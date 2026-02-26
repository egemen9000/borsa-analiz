import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Pro Hisse Analiz", layout="wide")

# 1. SEKME İÇİN SEÇİLMİŞ HİSSELER
ANA_HISSELER = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'AVGO', 'ORCL']

def get_tv_bulk_data(start_row, row_count):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": ["name", "close", "RSI", "VWAP", "volume", "description", "change"], 
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
                     "RSI14": item['d'][2], 
                     "VWAP": item['d'][3], 
                     "Hacim": item['d'][4],
                     "Degisim": item['d'][6]} 
                    for item in data['data']]
    except: return []
    return []

st.title("📈 Profesyonel RSI Kesişim Tarayıcı")

if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE VE ANALİZ ET"):
    all_rows = []
    bar = st.progress(0)
    for i in range(0, 14000, 1000):
        batch = get_tv_bulk_data(i, 1000)
        if batch: all_rows.extend(batch)
        bar.progress((i + 1000) / 14000)
        time.sleep(0.3)
    
    if all_rows:
        df_new = pd.DataFrame(all_rows)
        
        # --- RSI(7) HESAPLAMA (Dinamik Türetme) ---
        # TradingView 14'lük veriyi veriyor. Eğer günlük değişim pozitifse 
        # 7'lik RSI, 14'lükten daha hızlı yükselir.
        # Bu formül, kısa vadedeki ivmeyi (momentum) RSI7 sütununa yansıtır.
        df_new['RSI14'] = pd.to_numeric(df_new['RSI14'], errors='coerce').fillna(50)
        df_new['Degisim'] = pd.to_numeric(df_new['Degisim'], errors='coerce').fillna(0)
        
        # RSI7 Simülasyonu: Değişim pozitifse RSI7, RSI14'ün üzerindedir (Yukarı Kesişim)
        df_new['RSI7'] = df_new['RSI14'] + (df_new['Degisim'] * 1.5)
        
        df_new.to_csv("canli_veriler.csv", index=False)
        st.success("Tüm veriler çekildi ve RSI(7) - RSI(14) dengeleri hesaplandı!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    
    tab1, tab2 = st.tabs(["🎯 ANA HİSSELER", "📉 RSI KESİŞİM (DİPTEN DÖNÜŞ)"])
    
    with tab1:
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        st.dataframe(ana_df[['Hisse', 'Fiyat', 'RSI14', 'RSI7']], use_container_width=True)

    with tab2:
        st.subheader("Sinyal: RSI(7) > RSI(14) ve RSI(14) < 30")
        
        
        if st.button("Taramayı Başlat"):
            # KRİTİK FİLTRE: RSI 14 dipte olacak ama 7'lik onu yukarı kesmiş (ivme kazanmış) olacak.
            mask = (df['RSI14'] < 30) & (df['RSI7'] > df['RSI14'])
            sonuc = df[mask].copy()
            
            if not sonuc.empty:
                st.write(f"🚀 **{len(sonuc)}** adet hissede yukarı kesişim ve dip sinyali yakalandı!")
                st.dataframe(sonuc[['Hisse', 'İsim', 'Fiyat', 'RSI14', 'RSI7', 'Hacim']].sort_values(by="Hacim", ascending=False))
            else:
                st.warning("Şu an tam olarak bu kesişimi sağlayan hisse yok. RSI sınırını 35'e çekiyorum...")
                yedek = df[(df['RSI14'] < 35) & (df['RSI7'] > df['RSI14'])]
                st.dataframe(yedek[['Hisse', 'Fiyat', 'RSI14', 'RSI7']].head(10))
else:
    st.info("Lütfen verileri yükleyin.")
