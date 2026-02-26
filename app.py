import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Tam Kapasite Borsa Analizi", layout="wide")

# Takip listesi
ANA_HISSELER = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'AVGO', 'ORCL']

def get_tv_full_scan(start_row, row_count=1000):
    url = "https://scanner.tradingview.com/america/scan"
    # RSI7 ve RSI14 için en stabil teknik tanımlamalar
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": [
            "name", 
            "close", 
            "Relative.Strength.Index.7", 
            "Relative.Strength.Index.14", 
            "VWAP", 
            "volume", 
            "description"
        ], 
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [start_row, start_row + row_count]
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and len(data['data']) > 0:
                return [{"Hisse": item['s'].split(":")[1], 
                         "İsim": item['d'][6], 
                         "Fiyat": item['d'][1], 
                         "RSI7": item['d'][2], 
                         "RSI14": item['d'][3], 
                         "VWAP": item['d'][4], 
                         "Hacim": item['d'][5]} 
                        for item in data['data']]
        return []
    except:
        return None # Hata durumunda döngüyü kırmamak için None

st.title("🚀 Tam Kapasite (14.212+) Hisse Tarama Sistemi")

# ANA BUTON
if st.button("🔴 TÜM AMERİKA BORSASINI SIFIRDAN İNDİR"):
    all_data = []
    current_row = 0
    step = 1000
    
    progress_bar = st.progress(0)
    status_msg = st.empty()
    
    # Veri gelmeye devam ettiği sürece dön (Sınır koymadık, ne varsa çeker)
    while True:
        status_msg.info(f"⏳ {current_row}. satırdan sonrası taranıyor...")
        batch = get_tv_full_scan(current_row, step)
        
        if batch is None: # Geçici bağlantı hatası
            status_msg.warning("⚠️ Bağlantı hatası, 2 saniye sonra tekrar deneniyor...")
            time.sleep(2)
            continue
            
        if not batch: # Veri bitti (14.212. satıra ulaşıldı)
            status_msg.success(f"✅ Tarama bitti! Toplam {len(all_data)} hisse bulundu.")
            break
            
        all_data.extend(batch)
        current_row += step
        
        # 15.000 üzerinden tahmini ilerleme çubuğu
        progress_bar.progress(min(current_row / 15000, 1.0))
        time.sleep(0.5) # API ban yemesin diye küçük bir es
        
    if all_data:
        df_total = pd.DataFrame(all_data).drop_duplicates(subset=['Hisse'])
        df_total.to_csv("canli_veriler.csv", index=False)
        st.balloons()
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    
    # Sayısal veri zorunluluğu
    for col in ['RSI7', 'RSI14', 'Fiyat', 'VWAP']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    tab1, tab2, tab3 = st.tabs(["🎯 PUANLAMA", "📉 ÖZEL SİNYAL (7 > 14)", "📂 TAM LİSTE (HAM)"])
    
    with tab1:
        st.subheader("Büyük Hisseler Skor Tablosu")
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        if not ana_df.empty:
            # Basit Skor: Fiyat > VWAP (50p) + RSI7 > RSI14 (50p)
            ana_df['SKOR'] = ((ana_df['Fiyat'] > ana_df['VWAP']).astype(int) * 50 + 
                             (ana_df['RSI7'] > ana_df['RSI14']).astype(int) * 50)
            st.dataframe(ana_df[['Hisse', 'SKOR', 'Fiyat', 'RSI7', 'RSI14', 'VWAP']].sort_values(by="SKOR", ascending=False))

    with tab2:
        # Senin istediğin o meşhur filtre: RSI14 dipte (aşırı satım) ve RSI7 yukarı kırmış
        sinyal_df = df[(df['RSI14'] < 30) & (df['RSI7'] > df['RSI14'])].copy()
        st.subheader(f"Dipten Dönüş Sinyali Veren {len(sinyal_df)} Hisse")
        st.dataframe(sinyal_df.sort_values(by="Hacim", ascending=False))

    with tab3:
        st.subheader(f"Ham Veri Paneli (Toplam: {len(df)} Satır)")
        # Arama kutusu (O 212 farkı burada görebilirsin)
        ara = st.text_input("Hisse kodu ile ara:").upper()
        if ara:
            st.dataframe(df[df['Hisse'].str.contains(ara, na=False)])
        else:
            st.dataframe(df)
else:
    st.warning("Veritabanı henüz oluşturulmadı. Yukarıdaki kırmızı butona basarak tüm piyasayı indirin.")
