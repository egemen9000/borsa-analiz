import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Hisse Analiz Terminali", layout="wide")

# Analiz Edilecek Ana Hisse Listesi (Puanlama için)
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

# 1. VERİ GÜNCELLEME VE PROGRESS BAR
if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE"):
    all_rows = []
    bar = st.progress(0)
    status_msg = st.empty()
    
    total = 14000
    step = 1000
    
    for i in range(0, total, step):
        status_msg.info(f"İşleniyor: {i} - {i+step} arası veriler...")
        batch = get_tv_bulk_data(i, step)
        if batch: all_rows.extend(batch)
        bar.progress((i + step) / total)
        time.sleep(0.3)
        
    if all_rows:
        df_new = pd.DataFrame(all_rows)
        df_new.to_csv("canli_veriler.csv", index=False)
        status_msg.success("Veritabanı başarıyla güncellendi.")
        time.sleep(1)
        st.rerun()

st.divider()

# 2. VERİ ANALİZ VE FİLTRELEME
if os.path.exists("canli_veriler.csv") and os.path.getsize("canli_veriler.csv") > 0:
    df = pd.read_csv("canli_veriler.csv")
    
    # Teknik Sütun Kontrolü
    if 'RSI7' in df.columns and 'RSI14' in df.columns:
        
        c1, c2, c3 = st.columns(3)
        fiyat_limit = c1.number_input("Minimum Fiyat ($)", value=1.0)
        hacim_limit = c2.number_input("Minimum Hacim (Günlük)", value=500000)
        rsi_esik = c3.slider("Dipten Dönüş RSI Sınırı", 0, 100, 30)

        tab1, tab2 = st.tabs(["🎯 LİSTE ANALİZİ VE PUANLAMA", "📉 TEKNİK DİPTEN DÖNÜŞ"])
        
        with tab1:
            st.subheader("Seçilmiş Hisse Senetleri Skor Tablosu")
            ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
            
            def hesapla_skor(row):
                score = 0
                if row['Fiyat'] > row['VWAP']: score += 40
                if row['RSI'] > 50: score += 30
                if row['RSI7'] > row['RSI14']: score += 30
                return score

            if not ana_df.empty:
                ana_df['SKOR'] = ana_df.apply(hesapla_skor, axis=1)
                st.dataframe(ana_df[['Hisse', 'Fiyat', 'SKOR', 'RSI', 'RSI7', 'RSI14']].sort_values(by="SKOR", ascending=False), use_container_width=True)
            else:
                st.warning("Seçili hisseler veritabanında bulunamadı. Lütfen verileri güncelleyin.")

        with tab2:
            st.info(f"Kriter: RSI < {rsi_esik} VE RSI(7) > RSI(14) (Pozitif Kesişim)")
            if st.button("Teknik Dip Taramasını Başlat"):
                sonuc = df[(df['RSI'] < rsi_esik) & 
                           (df['RSI7'] > df['RSI14']) & 
                           (df['Fiyat'] >= fiyat_limit) & 
                           (df['Hacim'] >= hacim_limit)]
                st.write(f"Kriterlere uyan {len(sonuc)} hisse bulundu.")
                st.dataframe(sonuc.sort_values(by="Hacim", ascending=False), use_container_width=True)
    else:
        st.error("Veritabanı yapısı mevcut analiz kriterlerini desteklemiyor. Lütfen yukarıdaki butona basarak verileri yeniden indirin.")
else:
    st.info("Sistemde analiz edilecek veri bulunamadı. Lütfen 'Sisteme Yükle' butonunu kullanın.")
