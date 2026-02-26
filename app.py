import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Analiz Platformu", layout="wide")

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
        # Harf uyuşmazlığı riskine karşı API'nin beklediği tam teknik isimleri kullanıyoruz
        "columns": [
            "name", 
            "close", 
            "RSI", 
            "VWAP", 
            "volume", 
            "description", 
            "RSI[7]",   # 7 Periyotluk RSI
            "RSI[20]"   # Senin istediğin 20 Periyotluk RSI
        ],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [start_row, start_row + row_count]
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            # d[6] -> RSI[7], d[7] -> RSI[20]
            return [{"Hisse": item['s'].split(":")[1], 
                     "İsim": item['d'][5], 
                     "Fiyat": item['d'][1], 
                     "RSI": item['d'][2], 
                     "VWAP": item['d'][3], 
                     "Hacim": item['d'][4],
                     "RSI7": item['d'][6], 
                     "RSI20": item['d'][7]} 
                    for item in data['data']]
    except: return []
    return []

st.title("📈 Kurumsal Hisse Analiz Platformu")

if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE"):
    all_rows = []
    bar = st.progress(0)
    for i in range(0, 14000, 1000):
        batch = get_tv_bulk_data(i, 1000)
        if batch: all_rows.extend(batch)
        bar.progress((i + 1000) / 14000)
        time.sleep(0.5)
    if all_rows:
        # CSV Sütun İsimlerini Sabitliyoruz
        df_new = pd.DataFrame(all_rows)
        df_new.to_csv("canli_veriler.csv", index=False)
        st.success("Veritabanı RSI[7] ve RSI[20] verileriyle güncellendi!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    # Sayısal veri dönüşümü
    for col in ['RSI', 'RSI7', 'RSI20', 'Fiyat']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    tab1, tab2 = st.tabs(["🎯 SEÇİLMİŞ HİSSELER", "📉 TEKNİK DİPTEN DÖNÜŞ"])
    
    with tab1:
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        if not ana_df.empty:
            st.dataframe(ana_df[['Hisse', 'Fiyat', 'RSI', 'RSI7', 'RSI20']], use_container_width=True)

    with tab2:
        st.subheader("Filtre: RSI < 30 ve RSI(7) > RSI(20)")
        
        if st.button("Taramayı Başlat"):
            # O 4 hisseyi yakalamak için yeni kural (20 periyot)
            mask = (df['RSI'] < 30) & (df['RSI7'] > df['RSI20']) & (df['RSI7'] > 0)
            sonuc = df[mask].copy()
            
            if not sonuc.empty:
                st.write(f"🚀 Bulunan Hisse Sayısı: **{len(sonuc)}**")
                st.dataframe(sonuc[['Hisse', 'İsim', 'Fiyat', 'RSI', 'RSI7', 'RSI20', 'Hacim']].sort_values(by="Hacim", ascending=False))
            else:
                st.warning("Bu kriterlere uyan hisse şu an yok. RSI7 veya RSI20 sütunlarının 0 olup olmadığını kontrol et.")
                # Teşhis için ilk 5 satırı göster
                st.write("Veritabanı Örneği (İlk 5):", df[['Hisse', 'RSI7', 'RSI20']].head())

else:
    st.info("Lütfen verileri güncelleyin.")
