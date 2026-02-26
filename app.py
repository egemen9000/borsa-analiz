import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Hisse Scanner Pro", layout="wide")

def get_tv_data_safe(offset):
    url = "https://scanner.tradingview.com/america/scan"
    # Sütun isimlerini API'nin en ham/standart haliyle güncelledik
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": ["name", "close", "RSI7", "RSI", "VWAP", "volume", "description"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [offset, offset + 1000]
    }
    try:
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            return res.json().get('data', [])
        else:
            st.error(f"🔴 API Hatası (Offset {offset}): {res.status_code}")
            return None
    except Exception as e:
        st.error(f"🔴 Bağlantı Hatası: {str(e)}")
        return None

st.title("🚀 Kesintisiz 14.212+ Hisse Tarayıcı")

if st.button("🔴 MOTORU ÇALIŞTIR (TÜM PİYASAYI İNDİR)"):
    all_results = []
    status_area = st.empty()
    progress_bar = st.progress(0)
    
    # 15.000'e kadar zorluyoruz (14.212'de kendisi duracak)
    for i in range(0, 16000, 1000):
        status_area.warning(f"📡 Veri paketleniyor: {i} - {i+1000}")
        
        batch = get_tv_data_safe(i)
        
        if batch:
            # Gelen veriyi güvenli bir şekilde ayrıştır
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
        elif batch == []: # Veri bittiğinde boş liste döner
            status_area.info("🏁 Borsanın sonuna geldik. İşlem tamamlanıyor...")
            break
        
        progress_bar.progress(min((i + 1000) / 15000, 1.0))
        time.sleep(0.7) # API'yi şişirmemek için minik bir nefes
    
    if all_results:
        df = pd.DataFrame(all_results).drop_duplicates(subset=['Hisse'])
        df.to_csv("canli_veriler.csv", index=False)
        st.balloons()
        st.success(f"💾 Toplam {len(df)} hisse tertemiz kaydedildi!")
        time.sleep(2)
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    # Sayısal çevrimler
    for col in ['RSI7', 'RSI14', 'Fiyat', 'VWAP', 'Hacim']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    t1, t2 = st.tabs(["📊 Sinyal Avcısı", "📋 Ham Veri Ambarı"])
    
    with t1:
        # ANA FORMÜL: RSI14 dipte ama RSI7 kafayı kaldırmış
        mask = (df['RSI14'] < 30) & (df['RSI7'] > df['RSI14'])
        sinyal = df[mask].copy()
        st.subheader(f"🎯 Kurala Uyan: {len(sinyal)} Hisse")
                st.dataframe(sinyal.sort_values(by="Hacim", ascending=False), use_container_width=True)
        
    with t2:
        st.subheader(f"Toplam Veritabanı: {len(df)} Hisse")
        st.dataframe(df, use_container_width=True)
else:
    st.info("Sistemde yüklü veri yok. Kırmızı butona basarak indirmeyi başlat reis.")
