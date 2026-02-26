import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Analiz Platformu", layout="wide")

# 1. SEKME İÇİN SABİT LİSTE (DEĞİŞMEDİ)
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
        # TradingView API'den RSI verilerini çekmek için en güvenli kolon isimleri
        "columns": ["name", "close", "RSI", "VWAP", "volume", "description", "RSI[7]", "RSI[14]"],
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

# VERİ YÜKLEME (ESKİYİ SİLER, YENİYİ YAZAR)
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
        df_new.to_csv("canli_veriler.csv", index=False)
        st.success("Veritabanı başarıyla tazelendi!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    
    # SAYISAL DÖNÜŞÜM (NaN Değerleri Temizlemek İçin Kritik)
    for col in ['RSI', 'RSI7', 'RSI14', 'Fiyat', 'VWAP']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    tab1, tab2 = st.tabs(["🎯 SEÇİLMİŞ HİSSE SENETLERİ (100 ÜZERİNDEN)", "📉 TEKNİK DİPTEN DÖNÜŞ"])
    
    with tab1:
        # 1. Sekme Mantığı (Aynen Korundu)
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        def hesapla_skor(row):
            s = 0
            try:
                if row['Fiyat'] > row['VWAP']: s += 40
                if row['RSI'] > 50: s += 30
                if row['RSI7'] > row['RSI14']: s += 30
            except: pass
            return s
        if not ana_df.empty:
            ana_df['SKOR'] = ana_df.apply(hesapla_skor, axis=1)
            st.dataframe(ana_df[['Hisse', 'Fiyat', 'SKOR', 'RSI', 'RSI7', 'RSI14']].sort_values(by="SKOR", ascending=False), use_container_width=True)

    with tab2:
        st.subheader("Büyük Tarama: RSI < 30 ve RSI(7) > RSI(14)")
        
        if st.button("Taramayı Başlat"):
            # Filtrele: RSI 30'dan küçük olan 364 hisseyi al
            # Ve RSI7 ile RSI14 verisi olanları süz (NaN olanları atma, 0 kabul et)
            df['RSI7'] = df['RSI7'].fillna(0)
            df['RSI14'] = df['RSI14'].fillna(0)
            
            # ANA KURAL:
            mask = (df['RSI'] < 30) & (df['RSI7'] > df['RSI14']) & (df['Fiyat'] > 0.1)
            sonuc = df[mask].copy()
            
            if not sonuc.empty:
                st.write(f"🚀 Kurala uyan **{len(sonuc)}** hisse bulundu.")
                st.dataframe(sonuc[['Hisse', 'İsim', 'Fiyat', 'RSI', 'RSI7', 'RSI14', 'Hacim']].sort_values(by="Hacim", ascending=False), use_container_width=True)
            else:
                # EĞER 4 HİSSE HALA GELMİYORSA: Kesişim çok taze olabilir (RSI7 >= RSI14 deniyoruz)
                st.warning("Tam kesişim (>) bulunamadı, sınırda olanlar (>=) taranıyor...")
                yedek = df[(df['RSI'] < 30) & (df['RSI7'] >= df['RSI14']) & (df['Fiyat'] > 0.1)]
                if not yedek.empty:
                    st.dataframe(yedek[['Hisse', 'Fiyat', 'RSI', 'RSI7', 'RSI14', 'Hacim']], use_container_width=True)
                else:
                    st.error("RSI 30 altında olan hisselerde şu an yukarı yönlü bir RSI7/14 kesişimi tespit edilemedi.")

else:
    st.info("Veri yok. Önce 'Sisteme Yükle' butonuna basın.")
