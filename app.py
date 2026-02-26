import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="14K Hisse Sinyal Avcısı", layout="wide")

def get_tv_data_full(offset):
    url = "https://scanner.tradingview.com/america/scan"
    # Sadece en gerekli kolonları istiyoruz (Hata almamak için)
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

st.title("🏹 Tüm ABD Hisseleri (14.212) - RSI Yukarı Keser")

if st.button("🚀 TÜM PİYASAYI TARA (14.212 HİSSE)"):
    found_signals = []
    status_text = st.empty()
    bar = st.progress(0)
    
    # 15.000'e kadar tüm piyasayı süpürüyoruz
    for i in range(0, 16000, 1000):
        status_text.warning(f"📡 Tarama Yapılıyor: {i} - {i+1000}...")
        batch = get_tv_data_full(i)
        
        if batch:
            for item in batch:
                d = item.get('d', [])
                # d[2]: Bugün RSI7, d[3]: Bugün RSI14, d[4]: Dün RSI7, d[5]: Dün RSI14
                
                # SIFIR HESAPLAMA - Sadece Karşılaştırma
                bugun7, bugun14 = d[2], d[3]
                dun7, dun14 = d[4], d[5]
                
                # --- YUKARI KESER ŞARTI (CROSSOVER) ---
                if (dun7 is not None and dun14 is not None and bugun7 is not None and bugun14 is not None):
                    if (dun7 <= dun14) and (bugun7 > bugun14) and (bugun14 < 30):
                        found_signals.append({
                            "Hisse": item.get('s', '').split(":")[1],
                            "Fiyat": d[1],
                            "RSI7_Bugun": round(bugun7, 2),
                            "RSI14_Bugun": round(bugun14, 2),
                            "RSI7_Dun": round(dun7, 2),
                            "RSI14_Dun": round(dun14, 2),
                            "Hacim": d[6]
                        })
        elif batch == []: 
            break
        
        bar.progress(min((i + 1000) / 15000, 1.0))
        time.sleep(0.4) # API'yi küstürme
        
    status_text.empty()
    
    if found_signals:
        df_final = pd.DataFrame(found_signals).drop_duplicates(subset=['Hisse'])
        st.success(f"🎯 14.212 Hisse tarandı! Tam bugün kesişen {len(df_final)} hisse bulundu.")
        st.dataframe(df_final.sort_values(by="Hacim", ascending=False), use_container_width=True)
        
        # Sonuçları kaydet
        df_final.to_csv("bulunan_sinyaller.csv", index=False)
    else:
        st.error("Şu an tam kesişim anında olan hisse yok baboş!")

st.divider()

if os.path.exists("bulunan_sinyaller.csv"):
    st.subheader("📂 Son Bulunan Sinyaller")
    st.dataframe(pd.read_csv("bulunan_sinyaller.csv"))
