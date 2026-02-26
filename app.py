import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Analiz Platformu", layout="wide")

# Seçilmiş Hisse Senetleri Listesi
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
        "columns": ["name", "close", "RSI", "VWAP", "volume", "description", "RSI[7]", "RSI[14]"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [start_row, start_row + row_count]
    }
    try:
        response = requests.post(url, json=payload, timeout=25)
        if response.status_code == 200:
            data = response.json()
            return [{"Hisse": item['s'].split(":")[1], 
                     "İsim": item['d'][5], 
                     "Fiyat": item['d'][1], 
                     "RSI": item['d'][2], 
                     "VWAP": item['d'][3], 
                     "Hacim": item['d'][4],
                     "RSI7": item['d'][6], 
                     "RSI14": item['d'][7]} 
                    for item in data['data']]
    except:
        return []
    return []

st.title("📈 Amerika Hisse Senedi Analiz Platformu")

# 1. VERİ GÜNCELLEME
if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE"):
    all_rows = []
    bar = st.progress(0)
    status_msg = st.empty()
    for i in range(0, 14000, 1000):
        status_msg.info(f"Veriler işleniyor... {i}")
        batch = get_tv_bulk_data(i, 1000)
        if batch: all_rows.extend(batch)
        bar.progress((i + 1000) / 14000)
        time.sleep(0.4)
    if all_rows:
        pd.DataFrame(all_rows).to_csv("canli_veriler.csv", index=False)
        st.rerun()

st.divider()

# 2. ANALİZ VE TABLOLAR
if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    
    tab1, tab2 = st.tabs(["🎯 SEÇİLMİŞ HİSSE SENETLERİ (100 ÜZERİNDEN)", "📉 TEKNİK DİPTEN DÖNÜŞ"])
    
    with tab1:
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        
        def hesapla_skor(row):
            score = 0
            try:
                if float(row['Fiyat']) > float(row['VWAP']): score += 40
                if float(row['RSI']) > 50: score += 30
                if float(row['RSI7']) > float(row['RSI14']): score += 30
            except: pass
            return score

        if not ana_df.empty:
            ana_df['SKOR'] = ana_df.apply(hesapla_skor, axis=1)
            st.dataframe(ana_df[['Hisse', 'Fiyat', 'SKOR', 'RSI', 'RSI7', 'RSI14']].sort_values(by="SKOR", ascending=False), use_container_width=True)
        else:
            st.warning("Veritabanı güncel değil, lütfen yükleme yapın.")

    with tab2:
        st.info("Kriter: RSI < 30 VE RSI(7) > RSI(14)")
        
        if st.button("Taramayı Başlat"):
            # Sabit kriterlerle tarama (Kullanıcı girişi kaldırıldı)
            sonuc = df[(df['RSI'] < 30) & (df['RSI7'] > df['RSI14']) & (df['Fiyat'] > 1)]
            st.write(f"Bulunan Hisse Sayısı: {len(sonuc)}")
            st.dataframe(sonuc.sort_values(by="Hacim", ascending=False), use_container_width=True)
else:
    st.info("Lütfen önce verileri yükleyin.")
