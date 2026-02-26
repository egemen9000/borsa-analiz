import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="ABD Borsası Tarayıcı", layout="wide")

if 'ana_veri' not in st.session_state:
    st.session_state['ana_veri'] = None

# --- GELİŞMİŞ VERİ ÇEKME FONKSİYONU ---
def get_tv_data(offset):
    url = "https://scanner.tradingview.com/america/scan"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": [
            "name", "description", "close",
            "Relative.Strength.Index.7", "Relative.Strength.Index.14",
            "Relative.Strength.Index.7[1]", "Relative.Strength.Index.14[1]",
            "volume"
        ],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [offset, offset + 1000]
    }
    
    # Hata durumunda 3 kez deneme yapması için döngü
    for deneme in range(3):
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=15)
            if res.status_code == 200:
                return res.json().get('data', [])
            elif res.status_code == 429: # Çok fazla istek hatası
                time.sleep(2)
                continue
        except Exception as e:
            if deneme == 2: st.error(f"Bağlantı başarısız: {e}")
            time.sleep(1)
    return None

# --- ARAYÜZ ---
st.title("🛡️ ABD Borsası RSI Tarayıcı")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔴 1. VERİLERİ ÇEK"):
        all_stocks = []
        bar = st.progress(0)
        status = st.empty()
        
        # Test amaçlı önce 5000 hisse çekelim (Sorunsuz çalışırsa 16000 yaparsın)
        limit = 16000 
        for i in range(0, limit, 1000):
            status.info(f"📡 Veri alınıyor: {i} - {i+1000}")
            batch = get_tv_data(i)
            
            if batch:
                for item in batch:
                    d = item.get('d', [])
                    all_stocks.append({
                        "Hisse": item.get('s', '').split(":")[1] if ":" in item.get('s', '') else item.get('s', ''),
                        "Şirket": d[1], "Fiyat": d[2], "RSI7": d[3], "RSI14": d[4],
                        "RSI7_Dun": d[5], "RSI14_Dun": d[6], "Hacim": d[7]
                    })
                bar.progress(min((i + 1000) / limit, 1.0))
                time.sleep(0.6) # Sunucuyu yormamak için bekleme süresi
            else:
                status.error(f"⚠️ {i} noktasında veri alınamadı, işlem durduruldu.")
                break
        
        if all_stocks:
            df = pd.DataFrame(all_stocks).drop_duplicates(subset=['Hisse'])
            numeric_cols = ["Fiyat", "RSI7", "RSI14", "RSI7_Dun", "RSI14_Dun", "Hacim"]
            for c in numeric_cols:
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
            # Filtre: RSI14 < 30 ve RSI7 bugün RSI14'ü yukarı kesti
            mask = (df['RSI14'] < 30) & (df['RSI7_Dun'] <= df['RSI14_Dun']) & (df['RSI7'] > df['RSI14'])
            results = df[mask]
            
            if not results.empty:
                st.balloons()
                st.write(f"🎯 {len(results)} Sinyal Bulundu:")
                st.dataframe(results.sort_values("Hacim", ascending=False), use_container_width=True)
            else:
                st.warning("Aranan kriterlerde hisse bulunamadı.")
        else:
            st.error("Önce verileri indir!")
