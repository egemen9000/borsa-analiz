import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Tüm ABD Hisseleri Analiz", layout="wide")

def get_tv_data(offset):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": ["name", "close", "Relative.Strength.Index.7", "Relative.Strength.Index.14", "VWAP", "volume", "description"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [offset, offset + 1000]
    }
    try:
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            return res.json().get('data', [])
        return None
    except:
        return None

st.title("🇺🇸 Tüm ABD Borsası: RSI Sinyal Takibi")

if st.button("🔴 TÜM PİYASAYI İNDİR VE FİLTRELE"):
    all_results = []
    status = st.empty()
    progress = st.progress(0)
    
    for i in range(0, 16000, 1000):
        status.warning(f"📡 Paket Çekiliyor: {i} - {i+1000}")
        batch = get_tv_data(i)
        
        if batch:
            for item in batch:
                d = item.get('d', [])
                all_results.append({
                    "Hisse": item.get('s', '').split(":")[1] if ":" in item.get('s', '') else item.get('s', ''),
                    "İsim": d[6],
                    "Fiyat": d[1],
                    "RSI7": d[2],
                    "RSI14": d[3],
                    "VWAP": d[4],
                    "Hacim": d[5]
                })
        elif batch == []:
            break
        
        progress.progress(min((i + 1000) / 15000, 1.0))
        time.sleep(0.5)
    
    if all_results:
        df = pd.DataFrame(all_results).drop_duplicates(subset=['Hisse'])
        df.to_csv("canli_veriler.csv", index=False)
        st.success(f"✅ {len(df)} Hisse Başarıyla Güncellendi!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    for col in ['RSI7', 'RSI14', 'Fiyat', 'VWAP', 'Hacim']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- KURAL: RSI14 < 30 VE RSI7 > RSI14 ---
    # Başka hiçbir kısıtlama (Hacim/Fiyat) yok!
    mask = (df['RSI14'] < 30) & (df['RSI7'] > df['RSI14'])
    sinyal_df = df[mask].copy()

    tab1, tab2 = st.tabs(["🔥 SİNYAL VERENLER", "📂 TÜM VERİTABANI"])

    with tab1:
        st.subheader(f"🎯 Kurala Uyan Toplam: {len(sinyal_df)} Hisse")
        
        if not sinyal_df.empty:
            # En yüksek hacimliler yine en üstte gelsin ki popüler olanları gör
            st.dataframe(sinyal_df.sort_values(by="Hacim", ascending=False), use_container_width=True)
        else:
            st.info("Şu an kurala uyan hisse bulunamadı.")

    with tab2:
        st.subheader(f"İndirilen 14.212+ Hisse Listesi")
        st.dataframe(df, use_container_width=True)
else:
    st.info("Butona bas, tüm Amerika'yı indirelim aşko.")
