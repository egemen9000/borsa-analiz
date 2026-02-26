import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Tam Kapasite Analiz", layout="wide")

# 1. SEKME İÇİN SEÇİLMİŞ HİSSELER
ANA_HISSELER = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'AVGO', 'ORCL']

def get_tv_bulk_data(start_row, row_count):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": [
            "name", "close", "Relative.Strength.Index.7", "Relative.Strength.Index.14", 
            "VWAP", "volume", "description"
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
    except: return []
    return []

st.title("📈 Tam Kapasite Hisse Analiz Platformu")

# LİMİT 15.000 OLARAK GÜNCELLENDİ
if st.button("🚀 TÜM HİSSELERİ ÇEK (15.000 LİMİT)"):
    all_rows = []
    bar = st.progress(0)
    status = st.empty()
    # 14.000 yerine 15.000 yaparak o son 212 hisseyi de içeri alıyoruz
    for i in range(0, 15000, 1000):
        status.text(f"Taranıyor: {i} / 15000")
        batch = get_tv_bulk_data(i, 1000)
        if batch:
            all_rows.extend(batch)
        else:
            break # Eğer veri biterse zorlamaya gerek yok, döngüden çık
        bar.progress((i + 1000) / 15000)
        time.sleep(0.3)
    
    if all_rows:
        df_save = pd.DataFrame(all_rows)
        # Mükerrer (tekrar eden) kayıt varsa temizle
        df_save = df_save.drop_duplicates(subset=['Hisse'])
        df_save.to_csv("canli_veriler.csv", index=False)
        st.success(f"Toplam {len(df_save)} hisse başarıyla kaydedildi!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    for col in ['RSI7', 'RSI14', 'Fiyat', 'VWAP', 'Hacim']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    tab1, tab2, tab3 = st.tabs(["🎯 PUANLAMA", "📉 SİNYALLER", "📂 TÜM LİSTE"])
    
    with tab1:
        st.subheader("Büyüklerin Skoru")
        def hesapla_skor(row):
            skor = 0
            if row['Fiyat'] > row['VWAP']: skor += 40
            if row['RSI14'] > 50: skor += 30
            if row['RSI7'] > row['RSI14']: skor += 30
            return skor
        
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        if not ana_df.empty:
            ana_df['SKOR'] = ana_df.apply(hesapla_skor, axis=1)
            st.dataframe(ana_df[['Hisse', 'SKOR', 'Fiyat', 'RSI7', 'RSI14']].sort_values(by="SKOR", ascending=False))

    with tab2:
        # Senin o meşhur kuralın
        sinyal = df[(df['RSI14'] < 30) & (df['RSI7'] > df['RSI14'])].copy()
        st.subheader(f"Sinyal Verenler ({len(sinyal)} Hisse)")
        st.dataframe(sinyal.sort_values(by="Hacim", ascending=False))

    with tab3:
        st.subheader(f"Ham Veri Paneli (Toplam: {len(df)})")
        st.dataframe(df)
