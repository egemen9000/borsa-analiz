import streamlit as st
import pandas as pd
import requests
import time

# Sayfa yapılandırması
st.set_page_config(page_title="ABD Borsası Tarayıcı", layout="wide")

# --- HAFIZA (SESSION STATE) ---
if 'ana_veri' not in st.session_state:
    st.session_state['ana_veri'] = None

def get_tv_data(offset):
    url = "https://scanner.tradingview.com/america/scan"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": [
            "name",                          # 0
            "description",                   # 1
            "close",                         # 2
            "Relative.Strength.Index.7",     # 3
            "Relative.Strength.Index.14",    # 4
            "Relative.Strength.Index.7[1]",  # 5
            "Relative.Strength.Index.14[1]", # 6
            "volume"                         # 7
        ],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [offset, offset + 1000]
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=30)
        if res.status_code == 200:
            return res.json().get('data', [])
        else:
            return None
    except Exception:
        return None

# --- ARAYÜZ ---
st.title("🛡️ ABD Borsası RSI Tarayıcı")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔴 1. VERİLERİ ÇEK"):
        all_stocks = []
        bar = st.progress(0)
        status = st.empty()
        
        # 16 bin hisseye kadar tara
        for i in range(0, 16000, 1000):
            status.info(f"📡 Veri alınıyor: {i} - {i+1000}")
            batch = get_tv_data(i)
            if batch:
                for item in batch:
                    d = item.get('d', [])
                    all_stocks.append({
                        "Hisse": item.get('s', '').split(":")[1] if ":" in item.get('s', '') else item.get('s', ''),
                        "Şirket": d[1],
                        "Fiyat": d[2],
                        "RSI7": d[3],
                        "RSI14": d[4],
                        "RSI7_Dun": d[5],
                        "RSI14_Dun": d[6],
                        "Hacim": d[7]
                    })
                bar.progress(min((i + 1000) / 16000, 1.0))
                time.sleep(0.5)
            else:
                break
        
        if all_stocks:
            df = pd.DataFrame(all_stocks).drop_duplicates(subset=['Hisse'])
            # Sayısal çevrim
            for c in ["Fiyat", "RSI7", "RSI14", "RSI7_Dun", "RSI14_Dun", "Hacim"]:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            st.session_state['ana_veri'] = df.dropna(subset=['RSI7', 'RSI14'])
            st.success(f"✅ {len(st.session_state['ana_veri'])} Hisse Hazır!")
            status.empty()

with col2:
    if st.button("📂 2. LİSTEYİ GÖSTER"):
        if st.session_state['ana_veri'] is not None:
            st.dataframe(st.session_state['ana_veri'], use_container_width=True)
        else:
            st.error("Veri yok!")

with col3:
    if st.button("🏹 3. KESİŞİMLERİ BUL"):
        if st.session_state['ana_veri'] is not None:
            df = st.session_state['ana_veri'].copy()
            # Filtre: RSI14 < 30 ve RSI7 yukarı keser RSI14
            mask = (df['RSI14'] < 30) & (df['RSI7_Dun'] <= df['RSI14_Dun']) & (df['RSI7'] > df['RSI14'])
            results = df[mask]
            
            if not results.empty:
                st.write(f"🎯 {len(results)} Sinyal Bulundu:")
                st.dataframe(results.sort_values("Hacim", ascending=False), use_container_width=True)
            else:
                st.warning("Uygun hisse bulunamadı.")
        else:
            st.error("Önce verileri indir!")
