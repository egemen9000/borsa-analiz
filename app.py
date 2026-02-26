import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Şeffaf Hisse Analiz", layout="wide")

# 1. SEKME İÇİN SEÇİLMİŞ HİSSELER
ANA_HISSELER = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'AVGO', 'ORCL']

def get_tv_bulk_data(start_row, row_count):
    url = "https://scanner.tradingview.com/america/scan"
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
            return [{"Hisse": item['s'].split(":")[1], 
                     "İsim": item['d'][6], 
                     "Fiyat": item['d'][1], 
                     "RSI7": item['d'][2], 
                     "RSI14": item['d'][3], 
                     "VWAP": item['d'][4], 
                     "Hacim": item['d'][5]} 
                    for item in data['data']]
    except:
        return []
    return []

st.title("📈 Şeffaf Hisse Analiz Platformu")

# VERİ YÜKLEME BÖLÜMÜ
if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE (VT SIFIRLA)"):
    all_rows = []
    bar = st.progress(0)
    status = st.empty()
    for i in range(0, 14000, 1000):
        status.text(f"İndiriliyor: {i} / 14000")
        batch = get_tv_bulk_data(i, 1000)
        if batch:
            all_rows.extend(batch)
        bar.progress((i + 1000) / 14000)
        time.sleep(0.3)
    if all_rows:
        df_save = pd.DataFrame(all_rows)
        df_save.to_csv("canli_veriler.csv", index=False)
        st.success("Tüm veriler CSV dosyasına yazıldı!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")

    # Sayısal dönüşümler
    for col in ['RSI7', 'RSI14', 'Fiyat', 'VWAP', 'Hacim']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # NaN temizleme
    df = df.dropna(subset=['RSI7', 'RSI14', 'Fiyat', 'VWAP', 'Hacim'])

    # Ortalama hacim hesaplama
    ortalama_hacim = df['Hacim'].mean()

    # SEKME OLUŞTURMA
    tab1, tab2, tab3 = st.tabs(["🎯 ANA HİSSELER", "📉 AKILLI DİP DÖNÜŞ SİNYALİ", "📂 TÜM VERİTABANI (HAM VERİ)"])
    
    with tab1:
        st.subheader("Seçilmiş Dev Şirketler")
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        st.dataframe(ana_df, use_container_width=True)

    with tab2:
        st.subheader("RSI7 > RSI14 • RSI14 < 30 • Fiyat > VWAP • Hacim > 2x Ortalama")

        sinyal = df[
            (df['RSI7'] > df['RSI14']) &
            (df['RSI14'] < 30) &
            (df['Fiyat'] > df['VWAP']) &
            (df['Hacim'] > 2 * ortalama_hacim)
        ].copy()

        if not sinyal.empty:
            st.success(f"🔥 Güçlü Sinyal Veren {len(sinyal)} Hisse Bulundu!")
            st.dataframe(
                sinyal.sort_values(by="Hacim", ascending=False),
                use_container_width=True
            )
        else:
            st.warning("Bu kriterlere uyan hisse şu an yok.")

    with tab3:
        st.subheader("Veritabanındaki Tüm Satırlar")
        st.info(f"Toplam {len(df)} hisse kayıtlı.")

        ara = st.text_input("Hisse kodu ile ara (Örn: NVDA):").upper()
        if ara:
            st.dataframe(df[df['Hisse'].str.contains(ara, na=False)], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

else:
    st.warning("Veritabanı boş. Lütfen yukarıdaki butona basarak verileri çekin.")



