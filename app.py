import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="RSI Crossover Analiz", layout="wide")

def get_tv_crossover_data(offset):
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
            "Relative.Strength.Index.7[1]",   # Dün RSI7 (Kesişim kontrolü için)
            "Relative.Strength.Index.14[1]",  # Dün RSI14 (Kesişim kontrolü için)
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

st.title("🏹 RSI(7) Yukarı Keser RSI(14) - Gerçek Sinyal")

if st.button("🔴 KESİŞİMLERİ TARA (14.212 HİSSE)"):
    all_results = []
    status = st.empty()
    
    for i in range(0, 16000, 1000):
        status.warning(f"📡 Veri Analiz Ediliyor: {i} - {i+1000}")
        batch = get_tv_crossover_data(i)
        
        if batch:
            for item in batch:
                d = item.get('d', [])
                # Sütun eşleşmeleri:
                # d[2]: RSI7(Bugün), d[3]: RSI14(Bugün), d[4]: RSI7(Dün), d[5]: RSI14(Dün)
                
                bugun_7 = d[2]
                bugun_14 = d[3]
                dun_7 = d[4]
                dun_14 = d[5]
                
                # --- YUKARI KESER ŞARTI ---
                # 1. Dün 7, 14'ün altındaydı (Veya eşitti)
                # 2. Bugün 7, 14'ün üstüne çıktı
                # 3. RSI14 hala dip bölgesinde ( < 30 )
                if (dun_7 <= dun_14) and (bugun_7 > bugun_14) and (bugun_14 < 30):
                    all_results.append({
                        "Hisse": item.get('s', '').split(":")[1],
                        "Fiyat": d[1],
                        "RSI7_Bugün": bugun_7,
                        "RSI14_Bugün": bugun_14,
                        "RSI7_Dün": dun_7,
                        "RSI14_Dün": dun_14,
                        "Hacim": d[6]
                    })
        elif batch == []:
            break
        time.sleep(0.5)
    
    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv("kesisim_verileri.csv", index=False)
        st.success(f"✅ Tam Kesişim Veren {len(df)} Hisse Bulundu!")
        st.rerun()
    else:
        st.error("Şu an tam kesişme anında olan hisse yok!")

st.divider()

if os.path.exists("kesisim_verileri.csv"):
    df = pd.read_csv("kesisim_verileri.csv")
    st.subheader("🎯 Taze Sinyaller (Bugün Kesişenler)")
    st.dataframe(df.sort_values(by="Hacim", ascending=False), use_container_width=True)
else:
    st.info("Butona basarak taramayı başlat aşko.")
