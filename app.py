import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Hisse Pro: VT ve Kesişim", layout="wide")

# --- TRADINGVIEW VERİ ÇEKME FONKSİYONU ---
def get_tv_raw_data(offset):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": [
            "name", "close", 
            "Relative.Strength.Index.7", "Relative.Strength.Index.14",
            "Relative.Strength.Index.7[1]", "Relative.Strength.Index.14[1]",
            "volume", "description"
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

st.title("🛡️ Borsa Analiz Merkezi v2")

# --- 1. BÖLÜM: VERİTABANI YÖNETİMİ ---
st.header("📂 1. Veritabanı (VT) İşlemleri")
col1, col2 = st.columns(2)

with col1:
    if st.button("🔴 TÜM ABD PİYASASINI İNDİR (VT GÜNCELLE)"):
        all_data = []
        progress = st.progress(0)
        status = st.empty()
        
        for i in range(0, 16000, 1000):
            status.warning(f"📡 İndiriliyor: {i} - {i+1000}")
            batch = get_tv_raw_data(i)
            if batch:
                for item in batch:
                    d = item.get('d', [])
                    all_data.append({
                        "Hisse": item.get('s', '').split(":")[1],
                        "Fiyat": d[1], "RSI7": d[2], "RSI14": d[3],
                        "RSI7_Dun": d[4], "RSI14_Dun": d[5],
                        "Hacim": d[6], "Isim": d[7]
                    })
            elif batch == []: break
            progress.progress(min((i + 1000) / 15000, 1.0))
            time.sleep(0.6)
            
        if all_data:
            df_vt = pd.DataFrame(all_data).drop_duplicates(subset=['Hisse'])
            df_vt.to_csv("ana_veritabani.csv", index=False)
            st.success(f"✅ {len(df_vt)} hisse veritabanına kaydedildi!")

with col2:
    if os.path.exists("ana_veritabani.csv"):
        df_load = pd.read_csv("ana_veritabani.csv")
        st.info(f"💾 Mevcut VT: {len(df_load)} Hisse")
    else:
        st.error("⚠️ Veritabanı bulunamadı, lütfen indirin.")

st.divider()

# --- 2. BÖLÜM: KURAL TARAMASI ---
st.header("🏹 2. Kesişim Sinyal Taraması")

if st.button("🔍 VT ÜZERİNDEN KESİŞİMLERİ BUL"):
    if os.path.exists("ana_veritabani.csv"):
        df = pd.read_csv("ana_veritabani.csv")
        
        # --- KURAL: YUKARI KESER VE RSI14 < 30 ---
        # Mantık: (Dün 7 < 14) ve (Bugün 7 > 14) ve (Bugün 14 < 30)
        mask = (df['RSI7_Dun'] <= df['RSI14_Dun']) & \
               (df['RSI7'] > df['RSI14']) & \
               (df['RSI14'] < 30)
        
        sinyal_listesi = df[mask].copy()
        
        if not sinyal_listesi.empty:
            st.success(f"🎯 Kurala uyan {len(sinyal_listesi)} taze sinyal yakalandı!")
            st.dataframe(sinyal_listesi.sort_values(by="Hacim", ascending=False))
        else:
            st.warning("⚠️ Veritabanındaki hisseler arasında şu an tam kesişme anında olan yok.")
                else:
        st.error("Önce veritabanını indirmen lazım aşko!")

st.divider()

# --- 3. BÖLÜM: HAM VERİ ---
if os.path.exists("ana_veritabani.csv"):
    with st.expander("📂 Tüm Veritabanını Gör"):
        st.dataframe(pd.read_csv("ana_veritabani.csv"))
