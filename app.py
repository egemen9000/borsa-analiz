import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Hisse Analiz Terminali", layout="wide")

# Analiz Edilecek Ana Hisse Listesi
ANA_HISSELER = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'AVGO', 'ORCL']

def get_tv_bulk_data(start_row, row_count):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]},
            {"left": "exchange", "operation": "in_range", "right": ["AMEX", "NASDAQ", "NYSE"]}
        ],
        "options": {"lang": "en"},
        "markets": ["america"],
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

st.title("📈 Kurumsal Hisse Analiz Platformu")

# VERİ GÜNCELLEME BÖLÜMÜ
if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE"):
    all_rows = []
    progress_bar = st.progress(0)
    status_msg = st.empty()
    
    for i in range(0, 14000, 1000):
        status_msg.info(f"İşleniyor: {i} - {i+1000} arası veriler...")
        batch = get_tv_bulk_data(i, 1000)
        if batch: all_rows.extend(batch)
        progress_bar.progress((i + 1000) / 14000)
        time.sleep(0.3)
        
    if all_rows:
        df_new = pd.DataFrame(all_rows)
        df_new.to_csv("canli_veriler.csv", index=False)
        st.success("Veritabanı başarıyla güncellendi.")
        time.sleep(1)
        st.rerun()

st.divider()

# VERİ ANALİZ BÖLÜMÜ
if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    
    # Sütun Doğrulama
    required_cols = ['RSI7', 'RSI14', 'Fiyat', 'VWAP', 'RSI']
    if all(col in df.columns for col in required_cols):
        
        c1, c2, c3 = st.columns(3)
        fiyat_limit = c1.number_input("Minimum Fiyat ($)", value=1.0)
        hacim_limit = c2.number_input("Minimum Hacim (Günlük)", value=500000)
        rsi_esik = c3.slider("Dipten Dönüş RSI Sınırı", 0, 100, 30)

        tab1, tab2 = st.tabs(["🎯 LİSTE ANALİZİ VE PUANLAMA", "📉 TEKNİK DİPTEN DÖNÜŞ"])
        
        with tab1:
            st.subheader("Seçilmiş 11 Hisse İçin Puanlama")
            ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
            
            def hesapla_puan(row):
                p = 0
                if row['Fiyat'] > row['VWAP']: p += 40
                if row['RSI'] > 50: p += 30
                if row['RSI7'] > row['RSI14']: p += 30
                return p

            if not ana_df.empty:
                ana_df['SKOR'] = ana_df.apply(hesapla_puan, axis=1)
                st.dataframe(ana_df[['Hisse', 'Fiyat', 'SKOR', 'RSI', 'RSI7', 'RSI14']].sort_values(by="SKOR", ascending=False))
            else:
                st.warning("Seçili hisseler veritabanında bulunamadı. Lütfen listeyi güncelleyin.")

        with tab2:
            st.info(f"Kriter: RSI < {rsi_esik} VE RSI(7) > RSI(14) (Yukarı Kesişim)")
            if st.button("Teknik Dip Taramasını Başlat"):
                sonuc = df[(df['RSI'] < rsi_esik) & 
                           (df['RSI7'] > df['RSI14']) & 
                           (df['Fiyat'] >= fiyat_limit) & 
                           (df['Hacim'] >= hacim_limit)]
                st.write(f"Kriterlere uyan {len(sonuc)} hisse bulundu.")
                st.dataframe(sonuc.sort_values(by="Hacim", ascending=False))
    else:
        st.error("Veritabanı yapısı uyumsuz. Lütfen yukarıdaki butona basarak verileri yeniden indirin.")
else:
    st.info("Sistemde kayıtlı veri bulunamadı. Lütfen taramayı başlatın.")
