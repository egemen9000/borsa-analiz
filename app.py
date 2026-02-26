import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Hisse Scanner Pro", layout="wide")

def get_tv_data(offset):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": ["name", "close", "Relative.Strength.Index.7", "Relative.Strength.Index.14", "VWAP", "volume"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [offset, offset + 1000]
    }
    try:
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            data = res.json()
            return data.get('data', [])
        else:
            st.error(f"⚠️ API Hatası! Kod: {res.status_code}")
            return None
    except Exception as e:
        st.error(f"⚠️ Bağlantı Hatası: {str(e)}")
        return None

st.title("🚀 Kesintisiz 14.212+ Hisse Tarayıcı")

# İŞLEM MERKEZİ
if st.button("🔴 TARAMAYI ŞİMDİ BAŞLAT (DURURSA TEKRAR BAS)"):
    all_results = []
    placeholder = st.empty()
    progress = st.progress(0)
    
    # 15 binlik döngü (Garanticiyiz)
    for i in range(0, 16000, 1000):
        with placeholder.container():
            st.warning(f"🔄 Şu an çekiliyor: {i} - {i+1000}...")
        
        batch = get_tv_data(i)
        
        if batch is None: # Hata varsa durma, bir daha dene
            time.sleep(2)
            batch = get_tv_data(i)
            
        if batch:
            parsed = [{"Hisse": x['s'].split(":")[1], "Fiyat": x['d'][1], "RSI7": x['d'][2], "RSI14": x['d'][3], "VWAP": x['d'][4], "Hacim": x['d'][5]} for x in batch]
            all_results.extend(parsed)
            st.info(f"✅ Toplam biriken: {len(all_results)} hisse")
        else:
            st.success("🏁 Veri akışı bitti (Son hisseye ulaşıldı).")
            break
            
        progress.progress(min((i + 1000) / 15000, 1.0))
        time.sleep(1) # API'yi küstürme
    
    if all_results:
        df = pd.DataFrame(all_results).drop_duplicates(subset=['Hisse'])
        df.to_csv("canli_veriler.csv", index=False)
        st.balloons()
        st.success(f"💾 {len(df)} hisse kaydedildi! Sayfa yenileniyor...")
        time.sleep(2)
        st.rerun()

st.divider()

# VERİ GÖRÜNTÜLEME
if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    df['RSI7'] = pd.to_numeric(df['RSI7'], errors='coerce')
    df['RSI14'] = pd.to_numeric(df['RSI14'], errors='coerce')

    t1, t2 = st.tabs(["📊 Sinyal Verenler", "📋 Tüm Liste (Ham)"])
    
    with t1:
        # ANA FİLTRE: RSI14 < 30 ve RSI7 > RSI14
        sinyal = df[(df['RSI14'] < 30) & (df['RSI7'] > df['RSI14'])].copy()
        st.subheader(f"🎯 Dipten Dönüş Sinyali: {len(sinyal)} Hisse")
        
        st.dataframe(sinyal.sort_values(by="Hacim", ascending=False), use_container_width=True)
        
    with t2:
        st.subheader(f"Toplam Veritabanı: {len(df)} Hisse")
        st.dataframe(df, use_container_width=True)
else:
    st.info("Henüz veri çekilmedi. Kırmızı butona basarak motoru çalıştır.")
