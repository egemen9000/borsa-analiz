import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Borsa Analiz Pro", layout="wide")

# --- HAFIZA KURULUMU ---
if 'ana_veri' not in st.session_state:
    st.session_state['ana_veri'] = None

def get_tv_full_data(offset):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": [
            "name", "close", 
            "Relative.Strength.Index.7", "Relative.Strength.Index.14",
            "Relative.Strength.Index.7[1]", "Relative.Strength.Index.14[1]",
            "volume"
        ], 
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [offset, offset + 1000]
    }
    try:
        res = requests.post(url, json=payload, timeout=20)
        return res.json().get('data', []) if res.status_code == 200 else None
    except: return None

st.title("🛡️ Borsa VT ve Sinyal Paneli")

# --- BUTONLAR ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔴 1. TÜM PİYASAYI İNDİR"):
        all_data = []
        bar = st.progress(0)
        status = st.empty()
        for i in range(0, 16000, 1000):
            status.warning(f"📡 İndiriliyor: {i} - {i+1000}")
            batch = get_tv_full_data(i)
            if batch:
                for item in batch:
                    d = item.get('d', [])
                    all_data.append({
                        "Hisse": item.get('s', '').split(":")[1] if ":" in item.get('s', '') else item.get('s', ''),
                        "Fiyat": d[1], "RSI7": d[2], "RSI14": d[3],
                        "RSI7_Dun": d[4], "RSI14_Dun": d[5], "Hacim": d[6]
                    })
            elif batch == []: break
            bar.progress(min((i + 1000) / 16000, 1.0))
            time.sleep(0.3)
        
        if all_data:
            st.session_state['ana_veri'] = pd.DataFrame(all_data).drop_duplicates(subset=['Hisse'])
            st.success(f"✅ {len(st.session_state['ana_veri'])} Hisse Hafızaya Alındı!")

with col2:
    view_vt = st.button("📂 2. MEVCUT VERİTABANINI GÖRÜNTÜLE")

with col3:
    find_cross = st.button("🏹 3. YUKARI KESENLERİ BUL")

st.divider()

# --- AKSİYONLAR ---

if view_vt:
    if st.session_state['ana_veri'] is not None:
        st.subheader("📋 Aktif Veritabanı (Hafızadaki)")
        st.dataframe(st.session_state['ana_veri'], use_container_width=True)
    else:
        st.error("⚠️ Hafıza boş baboş! Önce 1. butona basıp verileri çekmelisin.")

if find_cross:
    if st.session_state['ana_veri'] is not None:
        df = st.session_state['ana_veri'].copy()
        for c in ['RSI7','RSI14','RSI7_Dun','RSI14_Dun']:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        
        # KURAL: Dün (7 <= 14) ve Bugün (7 > 14) ve Bugün (14 < 30)
        mask = (df['RSI7_Dun'] <= df['RSI14_Dun']) & (df['RSI7'] > df['RSI14']) & (df['RSI14'] < 30)
        crossover = df[mask]
        
        if not crossover.empty:
            st.success(f"🎯 Tam bugün kesişen {len(crossover)} hisse yakalandı!")
            st.dataframe(crossover.sort_values(by="Hacim", ascending=False), use_container_width=True)
        else:
            st.warning("⚠️ Şu an tam kesişme anında (cross) olan hisse yok.")
    else:
        st.error("⚠️ Önce verileri indirmen lazım!")
