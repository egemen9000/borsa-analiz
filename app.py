import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Hisse Scanner Pro", layout="wide")

def get_tv_data_safe(offset):
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

st.title("🚀 Kesintisiz 14.212+ Hisse Tarayıcı")

if st.button("🔴 MOTORU ÇALIŞTIR (TÜM PİYASAYI İNDİR)"):
    all_results = []
    status_area = st.empty()
    progress_bar = st.progress(0)
    
    for i in range(0, 16000, 1000):
        status_area.warning(f"📡 Veri paketleniyor: {i} - {i+1000}")
        batch = get_tv_data_safe(i)
        
        if batch:
            for item in batch:
                d = item.get('d', [])
                all_results.append({
                    "Hisse": item.get('s', '').split(":")[1] if ":" in item.get('s', '') else item.get('s', ''),
                    "Fiyat": d[1],
                    "RSI7": d[2],
                    "RSI14": d[3],
                    "VWAP": d[4],
                    "Hacim": d[5],
                    "İsim": d[6]
                })
            status_area.success(f"✅ Şu ana kadar {len(all_results)} hisse toplandı!")
        elif batch == []:
            break
        
        progress_bar.progress(min((i + 1000) / 15000, 1.0))
        time.sleep(0.7)
    
    if all_results:
        df = pd.DataFrame(all_results).drop_duplicates(subset=['Hisse'])
        df.to_csv("canli_veriler.csv", index=False)
        st.success(f"💾 Toplam {len(df)} hisse kaydedildi!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    for col in ['RSI7', 'RSI14', 'Fiyat', 'VWAP', 'Hacim']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    t1, t2 = st.tabs(["📊 Sinyal Avcısı", "📋 Ham Veri Ambarı"])
    
    with t1:
        mask = (df['RSI14'] < 30) & (df['RSI7'] > df['RSI14'])
        sinyal = df[mask].copy()
        st.subheader(f"🎯 Kurala Uyan: {len(sinyal)} Hisse")
        
        if not sinyal.empty:
            st.dataframe(sinyal.sort_values(by="Hacim", ascending=False), use_container_width=True)
        else:
            st.info("Kurala uyan hisse şu an yok.")
        
    with t2:
        st.subheader(f"Toplam Veritabanı: {len(df)} Hisse")
        st.dataframe(df, use_container_width=True)
else:
    st.info("Veri yok. Kırmızı butona bas.")
