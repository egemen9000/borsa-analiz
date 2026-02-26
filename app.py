import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Ham Veri Analiz", layout="wide")

def get_tv_raw_data(offset):
    url = "https://scanner.tradingview.com/america/scan"
    # TradingView'in orijinal teknik kolon isimleri (Değiştirme, hesaplama yapma!)
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": [
            "name", 
            "close", 
            "Relative.Strength.Index.7",      # Bugün RSI7
            "Relative.Strength.Index.14",     # Bugün RSI14
            "Relative.Strength.Index.7[1]",   # Dün RSI7
            "Relative.Strength.Index.14[1]",  # Dün RSI14
            "volume"
        ], 
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

st.title("🛡️ Ham Veri ile RSI Kesişim Taraması")

# --- 1. VERİTABANINI DOLDUR (VT) ---
if st.button("🔴 14.212 HİSSEYİ VT'YE İNDİR"):
    all_data = []
    status = st.empty()
    bar = st.progress(0)
    
    for i in range(0, 16000, 1000):
        status.warning(f"📡 Veri indiriliyor: {i} - {i+1000}")
        batch = get_tv_raw_data(i)
        if batch:
            for item in batch:
                d = item.get('d', [])
                all_data.append({
                    "Hisse": item.get('s', '').split(":")[1],
                    "Fiyat": d[1],
                    "RSI7_Bugun": d[2],
                    "RSI14_Bugun": d[3],
                    "RSI7_Dun": d[4],
                    "RSI14_Dun": d[5],
                    "Hacim": d[6]
                })
            status.success(f"✅ {len(all_data)} hisse alındı.")
        elif batch == []: break
        bar.progress(min((i + 1000) / 16000, 1.0))
        time.sleep(0.5)
        
    if all_data:
        pd.DataFrame(all_data).to_csv("ana_veritabani.csv", index=False)
        st.success("💾 Veritabanı kaydedildi! Artık kuralı çalıştırabilirsin.")

st.divider()

# --- 2. KURALI ÇALIŞTIR (VT ÜZERİNDEN) ---
if st.button("🔍 " "YUKARI KESER" " KURALINI UYGULA"):
    if os.path.exists("ana_veritabani.csv"):
        df = pd.read_csv("ana_veritabani.csv")
        
        # --- TAM SENİN İSTEDİĞİN KURAL (YUKARI KESER) ---
        # 1. Dün 7, 14'ün altındaydı (veya eşitti)
        # 2. Bugün 7, 14'ün üstüne çıktı
        # 3. RSI14 bugün 30'un altında (Aşırı satım bölgesi)
        
        mask = (df['RSI7_Dun'] <= df['RSI14_Dun']) & \
               (df['RSI7_Bugun'] > df['RSI14_Bugun']) & \
               (df['RSI14_Bugun'] < 30)
        
        sonuc = df[mask].copy()
        
        if not sonuc.empty:
            st.success(f"🎯 Tam o anı (kesişimi) yakaladığımız {len(sonuc)} hisse var!")
            
            st.dataframe(sonuc.sort_values(by="Hacim", ascending=False), use_container_width=True)
        else:
            st.warning("⚠️ Veritabanındaki 14.212 hisse içinde 'tam bugün' kesişen yok.")
    else:
        st.error("Önce VT'yi indir aşko, boş veritabanında neyi süzeyim?")

st.divider()

# Ham veriyi her zaman görebilmen için:
if os.path.exists("ana_veritabani.csv"):
    with st.expander("📂 Mevcut Veritabanı Ham Liste"):
        st.dataframe(pd.read_csv("ana_veritabani.csv"))
