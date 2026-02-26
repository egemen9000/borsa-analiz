import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Zaman Makinesi VT", layout="wide")

def get_tv_full_data(offset):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": [
            "name", 
            "close", 
            "Relative.Strength.Index.7",      # Bugün RSI7
            "Relative.Strength.Index.14",     # Bugün RSI14
            "Relative.Strength.Index.7[1]",   # DÜN RSI7 (İşte bu eksikti!)
            "Relative.Strength.Index.14[1]",  # DÜN RSI14 (Bu da eksikti!)
            "volume"
        ], 
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [offset, offset + 1000]
    }
    try:
        res = requests.post(url, json=payload, timeout=20)
        return res.json().get('data', []) if res.status_code == 200 else None
    except: return None

st.title("🛡️ 14.212 Hisse: Dün + Bugün Veri Ambarı")

if st.button("🔴 TÜM PİYASAYI (DÜN+BUGÜN) VT'YE İNDİR"):
    all_data = []
    status = st.empty()
    bar = st.progress(0)
    
    for i in range(0, 16000, 1000):
        status.warning(f"📡 Veri kazınıyor: {i} - {i+1000}...")
        batch = get_tv_full_data(i)
        
        if batch:
            for item in batch:
                d = item.get('d', [])
                all_data.append({
                    "Hisse": item.get('s', '').split(":")[1] if ":" in item.get('s', '') else item.get('s', ''),
                    "Fiyat": d[1],
                    "RSI7_Bugun": d[2],
                    "RSI14_Bugun": d[3],
                    "RSI7_Dun": d[4],   # Dünkü veri artık burada!
                    "RSI14_Dun": d[5],  # Dünkü veri artık burada!
                    "Hacim": d[6]
                })
        elif batch == []: break
        bar.progress(min((i + 1000) / 16000, 1.0))
        time.sleep(0.5)
        
    if all_data:
        df_vt = pd.DataFrame(all_data).drop_duplicates(subset=['Hisse'])
        df_vt.to_csv("ana_veritabani.csv", index=False)
        st.success(f"✅ {len(df_vt)} Hisse Dün+Bugün verisiyle kaydedildi!")
        st.rerun()

st.divider()

# --- MEVCUT VT GÖSTERİCİ ---
if os.path.exists("ana_veritabani.csv"):
    df = pd.read_csv("ana_veritabani.csv")
    st.subheader(f"📋 Mevcut Veritabanı ({len(df)} Hisse)")
    
    # Sütunları kontrol et ki emin olalım
    st.write("Dolu Sütunlar:", list(df.columns))
    
    st.dataframe(df.head(100), use_container_width=True)
    
    # Kuralı burada hemen test edelim
    st.subheader("🚀 'Yukarı Keser' Testi")
    # Mantık: Dün (7 <= 14) ve Bugün (7 > 14)
    crossover = df[(df['RSI7_Dun'] <= df['RSI14_Dun']) & (df['RSI7_Bugun'] > df['RSI14_Bugun']) & (df['RSI14_Bugun'] < 30)]
    
    if not crossover.empty:
        st.success(f"🎯 Tam isabet! {len(crossover)} hisse bugün kurala uydu.")
        st.dataframe(crossover)
    else:
        st.info("VT dolu ama şu an tam kesişme anında olan hisse yok baboş.")
else:
    st.error("VT henüz oluşturulmadı. Kırmızı butona bas!")
