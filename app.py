import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Analiz Platformu", layout="wide")

# Seçilmiş Hisse Senetleri Listesi (Bozulmayacak Kısım)
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
        # RSI[7] ve RSI[14] teknik isimlerini TradingView formatında istiyoruz
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

# 1. VERİ GÜNCELLEME (Hataları çözen temizleme mekanizması eklendi)
if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE"):
    all_rows = []
    bar = st.progress(0)
    status_msg = st.empty()
    for i in range(0, 14000, 1000):
        status_msg.info(f"Dev tarama yapılıyor: {i} / 14000")
        batch = get_tv_bulk_data(i, 1000)
        if batch: all_rows.extend(batch)
        bar.progress((i + 1000) / 14000)
        time.sleep(0.4)
    if all_rows:
        df_new = pd.DataFrame(all_rows)
        # Hatalı/boş verileri sayısal analize hazırlıyoruz
        df_new.to_csv("canli_veriler.csv", index=False)
        st.success("Veritabanı 14.000 hisse için güncellendi!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    # Veriyi okurken sayısal sütunları zorla
    df = pd.read_csv("canli_veriler.csv")
    for col in ['RSI', 'RSI7', 'RSI14', 'Fiyat', 'VWAP']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    tab1, tab2 = st.tabs(["🎯 SEÇİLMİŞ HİSSE SENETLERİ (100 ÜZERİNDEN)", "📉 TEKNİK DİPTEN DÖNÜŞ"])
    
    # --- 1. SEKME (AYNEN KORUNDU) ---
    with tab1:
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        def hesapla_skor(row):
            score = 0
            try:
                if row['Fiyat'] > row['VWAP']: score += 40
                if row['RSI'] > 50: score += 30
                if row['RSI7'] > row['RSI14']: score += 30
            except: pass
            return score
        if not ana_df.empty:
            ana_df['SKOR'] = ana_df.apply(hesapla_skor, axis=1)
            st.dataframe(ana_df[['Hisse', 'Fiyat', 'SKOR', 'RSI', 'RSI7', 'RSI14']].sort_values(by="SKOR", ascending=False), use_container_width=True)
        else:
            st.warning("Puanlama için veri bulunamadı, güncelleyin.")

    # --- 2. SEKME (ONARILAN VE TARAMA YAPAN KISIM) ---
    with tab2:
        st.subheader("Büyük Tarama: RSI < 30 ve RSI(7) > RSI(14)")
        st.info("Bu işlem 14.000 hisseyi kuralına göre süzerek getirir.")
        
                
        if st.button("Taramayı Başlat"):
            # Filtreleme: Boş olmayanları al ve kuralı uygula
            mask = (df['RSI'] < 30) & (df['RSI7'] > df['RSI14']) & (df['Fiyat'] > 0.5)
            sonuc = df[mask].dropna(subset=['RSI', 'RSI7', 'RSI14']).copy()
            
            if not sonuc.empty:
                st.write(f"🚀 Kriterlere uyan **{len(sonuc)}** hisse bulundu.")
                st.dataframe(sonuc[['Hisse', 'İsim', 'Fiyat', 'RSI', 'RSI7', 'RSI14', 'Hacim']].sort_values(by="Hacim", ascending=False), use_container_width=True)
            else:
                # Eğer hiç yoksa, piyasada o an bu kurala uyan hisse yoktur. 
                # Yine de boş dönmemesi için en yakın hisseleri (RSI < 35) gösteren bir alternatif sunuyoruz.
                st.warning("Şu an RSI < 30 kuralına tam uyan hisse yok. RSI < 35 olan potansiyeller taranıyor...")
                potansiyel = df[(df['RSI'] < 35) & (df['RSI7'] > df['RSI14'])].head(10)
                if not potansiyel.empty:
                    st.dataframe(potansiyel[['Hisse', 'Fiyat', 'RSI', 'RSI7', 'RSI14']])
else:
    st.info("Lütfen önce verileri yükleyin.")
