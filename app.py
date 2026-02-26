import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Hisse Analiz Platformu", layout="wide")

# 1. SEKME İÇİN SEÇİLMİŞ HİSSELER
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
        # İsteğin üzerine tam olarak RSI7 ve RSI14 isimlerini deniyoruz
        "columns": [
            "name", 
            "close", 
            "RSI", 
            "VWAP", 
            "volume", 
            "description", 
            "RSI7", 
            "RSI14"
        ],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [start_row, start_row + row_count]
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
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
    except: return []
    return []

st.title("📈 Amerika Hisse Senedi Analiz Platformu")

# VERİ GÜNCELLEME BUTONU
if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE"):
    all_rows = []
    bar = st.progress(0)
    for i in range(0, 14000, 1000):
        batch = get_tv_bulk_data(i, 1000)
        if batch: all_rows.extend(batch)
        bar.progress((i + 1000) / 14000)
        time.sleep(0.4)
    if all_rows:
        df_new = pd.DataFrame(all_rows)
        # Sütun isimlerini CSV'de netleştiriyoruz
        df_new.to_csv("canli_veriler.csv", index=False)
        st.success("Veritabanı RSI7 ve RSI14 formatıyla yenilendi!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    # Sayısal veri kontrolü
    for col in ['RSI', 'RSI7', 'RSI14', 'Fiyat']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    tab1, tab2 = st.tabs(["🎯 SEÇİLMİŞ HİSSELER", "📉 TEKNİK DİPTEN DÖNÜŞ"])
    
    with tab1:
        # 1. Sekme: Puanlama (Mevcut mantık korundu)
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        if not ana_df.empty:
            st.dataframe(ana_df[['Hisse', 'Fiyat', 'RSI', 'RSI7', 'RSI14']], use_container_width=True)

    with tab2:
        st.subheader("Filtre: RSI < 30 ve RSI7 > RSI14")
        
        if st.button("Taramayı Başlat"):
            # RSI7 ve RSI14 uyuşmazlığını çözmek için kural
            mask = (df['RSI'] < 30) & (df['RSI7'] > df['RSI14']) & (df['RSI7'] > 0)
            sonuc = df[mask].copy()
            
            if not sonuc.empty:
                st.write(f"🚀 Kriterlere uyan **{len(sonuc)}** hisse bulundu.")
                st.dataframe(sonuc[['Hisse', 'İsim', 'Fiyat', 'RSI', 'RSI7', 'RSI14', 'Hacim']].sort_values(by="Hacim", ascending=False))
            else:
                st.error("Kriterlere uygun hisse bulunamadı. Veritabanındaki RSI7/RSI14 değerlerini kontrol edin.")
                # Hata ayıklama için örnek tablo
                st.write("Veritabanı Kontrolü (İlk 5 Satır):", df[['Hisse', 'RSI7', 'RSI14']].head())
else:
    st.info("Sistemde veri bulunamadı. Lütfen '14.000 HİSSEYİ SİSTEME YÜKLE' butonuna basın.")
