import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Borsa Analiz Pro", layout="wide")

# 11 Baboş Hisse Listesi
BABOS_HISSELER = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'AVGO', 'ORCL']

def get_tv_bulk_data(start_row, row_count):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]},
            {"left": "exchange", "operation": "in_range", "right": ["AMEX", "NASDAQ", "NYSE"]}
        ],
        "options": {"lang": "en"},
        "markets": ["america"],
        # Sütun isimlerini TradingView formatına göre netleştiriyoruz
        "columns": ["name", "close", "RSI", "VWAP", "volume", "description", "RSI7", "RSI14"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [start_row, start_row + row_count]
    }
    try:
        response = requests.post(url, json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            return [{"Hisse": item['s'].split(":")[1], "İsim": item['d'][5], "Fiyat": item['d'][1], 
                     "RSI": item['d'][2], "VWAP": item['d'][3], "Hacim": item['d'][4],
                     "RSI7": item['d'][6], "RSI14": item['d'][7]} 
                    for item in data['data']]
    except: return []
    return []

st.title("🏦 Dev Veri Deposu & Baboş Analiz")

# GÜNCELLEME BUTONU
if st.button("🚀 14.000 HİSSEYİ GÜNCELLE"):
    all_rows = []
    bar = st.progress(0)
    status = st.empty()
    for i in range(0, 14000, 1000):
        status.write(f"⏳ {i} - {i+1000} indiriliyor...")
        batch = get_tv_bulk_data(i, 1000)
        if batch: all_rows.extend(batch)
        bar.progress((i + 1000) / 14000)
        time.sleep(0.3)
    if all_rows:
        # Dosyayı sıfırdan temiz bir şekilde yazıyoruz
        df_new = pd.DataFrame(all_rows)
        df_new.to_csv("canli_veriler.csv", index=False)
        st.success("Veritabanı başarıyla yenilendi!")
        time.sleep(1)
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    
    # Sütun kontrolü (Hata almamak için)
    required_cols = ['RSI7', 'RSI14', 'Fiyat', 'VWAP', 'RSI']
    if all(col in df.columns for col in required_cols):
        
        c1, c2, c3 = st.columns(3)
        fiyat_limit = c1.number_input("Min Fiyat ($)", value=1.0)
        hacim_limit = c2.number_input("Min Hacim", value=500000)
        rsi_sinir = c3.slider("RSI Sınırı (Dipten Dönüş İçin)", 0, 100, 30)

        tab1, tab2 = st.tabs(["🎯 11 BABOŞ PUANLAMA", "📉 TEKNİK DİPTEN DÖNÜŞ"])
        
        with tab1:
            st.subheader("Seçilmiş 11 Hisse Puan Durumu")
            babo_df = df[df['Hisse'].isin(BABOS_HISSELER)].copy()
            
            def puanla(row):
                p = 0
                if row['Fiyat'] > row['VWAP']: p += 40
                if row['RSI'] > 50: p += 30
                if row['RSI7'] > row['RSI14']: p += 30
                return p

            if not babo_df.empty:
                babo_df['PUAN'] = babo_df.apply(puanla, axis=1)
                st.dataframe(babo_df[['Hisse', 'Fiyat', 'PUAN', 'RSI', 'RSI7', 'RSI14']].sort_values(by="PUAN", ascending=False))
            else:
                st.warning("Baboş hisseler listede bulunamadı.")

        with tab2:
            st.info(f"Koşul: RSI < {rsi_sinir} VE RSI(7) > RSI(14)")
            if st.button("Teknik Dip Tara"):
                sonuc = df[(df['RSI'] < rsi_sinir) & 
                           (df['RSI7'] > df['RSI14']) & 
                           (df['Fiyat'] >= fiyat_limit) & 
                           (df['Hacim'] >= hacim_limit)]
                st.dataframe(sonuc.sort_values(by="Hacim", ascending=False))
    else:
        st.error("CSV yapısı hatalı. Lütfen '14.000 HİSSEYİ GÜNCELLE' butonuna basarak verileri yenileyin.")
else:
    st.warning("Veritabanı yok. Önce güncelleyin.")
