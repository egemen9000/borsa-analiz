import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Hisse Analiz Platformu", layout="wide")

# 1. SEKME İÇİN SABİT LİSTE
ANA_HISSELER = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'AVGO', 'ORCL']

def get_tv_bulk_data(start_row, row_count):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]},
            {"left": "exchange", "operation": "in_range", "right": ["AMEX", "NASDAQ", "NYSE"]}
        ],
        "options": {"lang": "en"},
        "markets": ["america"],
        # Sütunları ham endeksleriyle istiyoruz
        "columns": ["name", "close", "RSI", "VWAP", "volume", "description", "RSI[7]", "RSI[14]"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [start_row, start_row + row_count]
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return [{"Hisse": item['s'].split(":")[1], 
                     "İsim": item['d'][5], 
                     "Fiyat": item['d'][1], 
                     "RSI": item['d'][2], 
                     "VWAP": item['d'][3], 
                     "Hacim": item['d'][4],
                     "RSI7": item['d'][6], 
                     "RSI14": item['d'][7]} 
                    for item in data['data']]
    except: return []
    return []

st.title("📈 Amerika Hisse Senedi Analiz Platformu")

if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE"):
    all_rows = []
    bar = st.progress(0)
    for i in range(0, 14000, 1000):
        batch = get_tv_bulk_data(i, 1000)
        if batch: all_rows.extend(batch)
        bar.progress((i + 1000) / 14000)
        time.sleep(0.4)
    if all_rows:
        df_new = pd.DataFrame(all_rows)
        df_new.to_csv("canli_veriler.csv", index=False)
        st.success("Veriler sıfırlandı ve 14.000 yeni kayıt yüklendi!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    
    # VERİ TİPİ ZORLAMA (O 4 hisseyi kaçırmamak için kritik)
    for col in ['RSI', 'RSI7', 'RSI14', 'Fiyat']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    tab1, tab2 = st.tabs(["🎯 SEÇİLMİŞ HİSSE SENETLERİ", "📉 TEKNİK DİPTEN DÖNÜŞ"])
    
    with tab1:
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        if not ana_df.empty:
            st.dataframe(ana_df[['Hisse', 'Fiyat', 'RSI', 'RSI7', 'RSI14']], use_container_width=True)

    with tab2:
        st.subheader("Filtre: RSI < 30 VE RSI7 > RSI14")
        
        if st.button("Taramayı Başlat"):
            # O 4 hisseyi bulmak için filtreyi en temiz haliyle çalıştırıyoruz
            # Fiyat limitini 0.1'e çektim ki ucuz hisseler de gelsin
            mask = (df['RSI'] < 30) & (df['RSI7'] > df['RSI14']) & (df['Fiyat'] > 0.1)
            sonuc = df[mask].dropna(subset=['RSI', 'RSI7', 'RSI14'])
            
            if not sonuc.empty:
                st.write(f"🚀 Bulunan Hisse Sayısı: **{len(sonuc)}**")
                st.dataframe(sonuc[['Hisse', 'İsim', 'Fiyat', 'RSI', 'RSI7', 'RSI14', 'Hacim']].sort_values(by="Hacim", ascending=False))
            else:
                # Hala gelmiyorsa hata ayıklama için veri tabanı özetini göster
                st.error("Kriterlere uygun hisse bulunamadı. Veri tabanındaki sütunları kontrol ediyorum...")
                st.write("Veri tabanı sütun isimlerin:", list(df.columns))
                st.write("RSI 30 altı toplam hisse sayısı:", len(df[df['RSI'] < 30]))
                st.info("Eğer 'RSI 30 altı' hisse varsa ama sonuç boşsa, RSI7 verisi o hisseler için boş (NaN) geliyor olabilir.")

else:
    st.info("Veri yok, lütfen yükleyin.")
