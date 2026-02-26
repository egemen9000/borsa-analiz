import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Tam Kapasite Analiz", layout="wide")

# 1. SEKME İÇİN SEÇİLMİŞ HİSSELER
ANA_HISSELER = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'AVGO', 'ORCL']

def get_tv_bulk_data(start_row, row_count):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": [
            "name", "close", "Relative.Strength.Index.7", "Relative.Strength.Index.14", 
            "VWAP", "volume", "description"
        ], 
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [start_row, start_row + row_count]
    }
    try:
        # Timeout süresini artırdık ve hata fırlatmasını sağladık
        response = requests.post(url, json=payload, timeout=45)
        response.raise_for_status() 
        data = response.json()
        if "data" in data:
            return [{"Hisse": item['s'].split(":")[1], 
                     "İsim": item['d'][6], 
                     "Fiyat": item['d'][1], 
                     "RSI7": item['d'][2], 
                     "RSI14": item['d'][3], 
                     "VWAP": item['d'][4], 
                     "Hacim": item['d'][5]} 
                    for item in data['data']]
    except Exception as e:
        st.error(f"Paket çekilirken hata oluştu ({start_row}): {e}")
        return None # Boş liste değil None döndür ki hata olduğunu anlayalım
    return []

st.title("📈 Tam Kapasite Hisse Analiz Platformu")

if st.button("🚀 TÜM HİSSELERİ ÇEK (15.000 LİMİT)"):
    all_rows = []
    bar = st.progress(0)
    status_text = st.empty()
    
    # 15.000 hisse için döngü
    for i in range(0, 15000, 1000):
        status_text.warning(f"⏳ Şu an çekilen aralık: {i} - {i+1000}...")
        batch = get_tv_bulk_data(i, 1000)
        
        if batch is not None:
            if len(batch) > 0:
                all_rows.extend(batch)
                status_text.success(f"✅ {len(all_rows)} hisse toplandı.")
            else:
                status_text.info("🏁 Daha fazla hisse kalmadı, işlem bitiriliyor.")
                break
        else:
            status_text.error(f"❌ {i} konumunda veri çekilemedi. Tekrar deneniyor...")
            time.sleep(2) # Hata alınca biraz daha fazla bekle
            
        bar.progress(min((i + 1000) / 15000, 1.0))
        time.sleep(1) # API'yi yormamak için bekleme süresini biraz artırdık

    if all_rows:
        df_save = pd.DataFrame(all_rows)
        df_save = df_save.drop_duplicates(subset=['Hisse'])
        df_save.to_csv("canli_veriler.csv", index=False)
        st.balloons()
        st.success(f"İşlem Tamam! Toplam {len(df_save)} hisse kaydedildi.")
        time.sleep(1)
        st.rerun()

st.divider()

# Görsellerde gördüğümüz tabloların düzgün çalışması için alt kısım
if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    for col in ['RSI7', 'RSI14', 'Fiyat', 'VWAP', 'Hacim']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    tab1, tab2, tab3 = st.tabs(["🎯 PUANLAMA", "📉 SİNYALLER", "📂 TÜM LİSTE"])
    
    with tab1:
        st.subheader("Büyüklerin Skoru")
        # Puanlama mantığını buraya ekleyebilirsin
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        st.dataframe(ana_df)

    with tab2:
        # Sinyal Filtresi
        sinyal = df[(df['RSI14'] < 30) & (df['RSI7'] > df['RSI14'])].copy()
        st.subheader(f"Sinyal Verenler ({len(sinyal)} Hisse)")
        st.dataframe(sinyal)

    with tab3:
        st.subheader(f"Ham Veri Paneli (Toplam: {len(df)})")
        st.dataframe(df)
else:
    st.info("Lütfen yukarıdaki butona basarak taramayı başlatın.")
