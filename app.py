import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Amerika Analiz Platformu", layout="wide")

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
        # API Kolonlarını En Garanti Halleriyle İstiyoruz
        "columns": ["name", "close", "RSI", "VWAP", "volume", "description", "RSI7", "RSI14"],
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

if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE"):
    all_rows = []
    bar = st.progress(0)
    for i in range(0, 14000, 1000):
        batch = get_tv_bulk_data(i, 1000)
        if batch: all_rows.extend(batch)
        bar.progress((i + 1000) / 14000)
        time.sleep(0.4)
    if all_rows:
        pd.DataFrame(all_rows).to_csv("canli_veriler.csv", index=False)
        st.success("Veritabanı sıfırlandı ve 14.000 yeni kayıt yüklendi!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    for col in ['RSI', 'RSI7', 'RSI14', 'Fiyat']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    tab1, tab2 = st.tabs(["🎯 SEÇİLMİŞ HİSSE SENETLERİ (100 ÜZERİNDEN)", "📉 TEKNİK DİPTEN DÖNÜŞ"])
    
    with tab1:
        # Seçilmiş Hisseler Paneli
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        st.write("### (100 Üzerinden) Puanlama")
        if not ana_df.empty:
            st.dataframe(ana_df[['Hisse', 'Fiyat', 'RSI', 'RSI7', 'RSI14']], use_container_width=True)

    with tab2:
        st.subheader("Filtre: RSI < 30 ve RSI(7) > RSI(14)")
        
        if st.button("Taramayı Başlat"):
            # Önce 0 veya None olan RSI7/14 değerlerini temizle (Hatalı sonuç vermesin)
            df_clean = df.dropna(subset=['RSI7', 'RSI14'])
            df_clean = df_clean[(df_clean['RSI7'] > 0) & (df_clean['RSI14'] > 0)]
            
            # ANA KURAL (Sadece RSI < 30)
            sonuc = df_clean[(df_clean['RSI'] < 30) & (df_clean['RSI7'] > df_clean['RSI14'])].copy()
            
            if not sonuc.empty:
                st.write(f"🚀 Kurala uyan **{len(sonuc)}** hisse bulundu.")
                st.dataframe(sonuc[['Hisse', 'İsim', 'Fiyat', 'RSI', 'RSI7', 'RSI14', 'Hacim']].sort_values(by="Hacim", ascending=False), use_container_width=True)
            else:
                # Eğer veri hala boş geliyorsa, sorun RSI7 verisinin çekilememesidir. 
                # Teşhis koymak için RSI 30 altı hisseleri ham verisiyle göster:
                st.warning("Tam kesişim (RSI7 > RSI14) şu an bulunamadı. RSI 30 altı tüm hisseler taranıyor...")
                ham_dip = df[df['RSI'] < 30].sort_values(by="RSI").head(20)
                st.dataframe(ham_dip[['Hisse', 'RSI', 'RSI7', 'RSI14']])

else:
    st.info("Veri yok. Lütfen sisteme yükleme yapın.")
