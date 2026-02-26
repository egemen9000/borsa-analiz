import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Analiz Platformu", layout="wide")

# 1. SEKME İÇİN SABİT LİSTE
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
        # Sütunları netleştiriyoruz: 6->RSI7, 7->RSI14
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
    except: return []
    return []

st.title("📈 Amerika Hisse Senedi Analiz Platformu")

# VERİ YÜKLEME
if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE"):
    all_rows = []
    bar = st.progress(0)
    status_msg = st.empty()
    for i in range(0, 14000, 1000):
        status_msg.info(f"Tarama yapılıyor: {i} / 14000")
        batch = get_tv_bulk_data(i, 1000)
        if batch: all_rows.extend(batch)
        bar.progress((i + 1000) / 14000)
        time.sleep(0.5)
    if all_rows:
        pd.DataFrame(all_rows).to_csv("canli_veriler.csv", index=False)
        st.success("Veritabanı başarıyla tazelendi!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    # Sayısal dönüşüm (Hata önleyici)
    for c in ['RSI', 'RSI7', 'RSI14', 'Fiyat', 'VWAP']:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    tab1, tab2 = st.tabs(["🎯 SEÇİLMİŞ HİSSE SENETLERİ (100 ÜZERİNDEN)", "📉 TEKNİK DİPTEN DÖNÜŞ"])
    
    # --- 1. SEKME (BOZULMADI) ---
    with tab1:
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        def hesapla_skor(row):
            s = 0
            if row['Fiyat'] > row['VWAP']: s += 40
            if row['RSI'] > 50: s += 30
            if row['RSI7'] > row['RSI14']: s += 30
            return s
        if not ana_df.empty:
            ana_df['SKOR'] = ana_df.apply(hesapla_skor, axis=1)
            st.dataframe(ana_df[['Hisse', 'Fiyat', 'SKOR', 'RSI', 'RSI7', 'RSI14']].sort_values(by="SKOR", ascending=False))
        else: st.warning("Veritabanını güncelleyin.")

    # --- 2. SEKME (BOŞ LİSTE SORUNU ÇÖZÜLDÜ) ---
    with tab2:
        st.subheader("Büyük Tarama: RSI < 30 ve RSI(7) > RSI(14)")
        if st.button("Taramayı Başlat"):
            # Sert kural: RSI < 30
            sonuc = df[(df['RSI'] < 30) & (df['RSI7'] > df['RSI14']) & (df['Fiyat'] > 0.5)].copy()
            
            if not sonuc.empty:
                st.write(f"🚀 Tam kurala uyan **{len(sonuc)}** hisse bulundu.")
                st.dataframe(sonuc[['Hisse', 'Fiyat', 'RSI', 'RSI7', 'RSI14', 'Hacim']].sort_values(by="Hacim", ascending=False))
            else:
                # EĞER BOŞSA: Kuralı biraz esnetip potansiyelleri getir (RSI < 40)
                st.warning("Tam kurala (RSI < 30) uyan hisse şu an yok. RSI < 40 olan potansiyel dönüşler listeleniyor...")
                esnek = df[(df['RSI'] < 40) & (df['RSI7'] > df['RSI14']) & (df['Fiyat'] > 0.5)].copy()
                if not esnek.empty:
                    st.dataframe(esnek[['Hisse', 'Fiyat', 'RSI', 'RSI7', 'RSI14', 'Hacim']].sort_values(by="RSI"))
                else:
                    st.error("Borsada şu an dipten dönen hisse yok. Lütfen piyasanın biraz soğumasını bekleyin.")
else:
    st.info("Veri yok. Önce 'Sisteme Yükle' butonuna basın.")
