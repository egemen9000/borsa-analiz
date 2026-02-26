import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="RSI Kesin Çözüm", layout="wide")

# 1. SEKME İÇİN SEÇİLMİŞ HİSSELER
ANA_HISSELER = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'AVGO', 'ORCL']

def get_tv_bulk_data(start_row, row_count):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        # BURASI KRİTİK: TradingView'in RSI 7 ve 14 için beklediği gerçek teknik isimler
        "columns": [
            "name", 
            "close", 
            "Relative.Strength.Index.7",   # RSI(7) verisi
            "Relative.Strength.Index.14",  # RSI(14) verisi
            "VWAP", 
            "volume", 
            "description"
        ], 
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [start_row, start_row + row_count]
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return [{"Hisse": item['s'].split(":")[1], 
                     "İsim": item['d'][6], 
                     "Fiyat": item['d'][1], 
                     "RSI7": item['d'][2], 
                     "RSI14": item['d'][3], 
                     "VWAP": item['d'][4], 
                     "Hacim": item['d'][5]} 
                    for item in data['data']]
    except: return []
    return []

st.title("📈 RSI(7) ve RSI(14) Canlı Tarama")

if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE"):
    all_rows = []
    bar = st.progress(0)
    for i in range(0, 14000, 1000):
        batch = get_tv_bulk_data(i, 1000)
        if batch: all_rows.extend(batch)
        bar.progress((i + 1000) / 14000)
        time.sleep(0.4)
    if all_rows:
        df_save = pd.DataFrame(all_rows)
        # Sayısal olmayanları temizleyelim ki filtre çalışsın
        df_save.to_csv("canli_veriler.csv", index=False)
        st.success("Veritabanı RSI(7) ve RSI(14) gerçek verileriyle yüklendi!")
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    # Verileri sayıya çevir (Hata payını sıfırla)
    df['RSI7'] = pd.to_numeric(df['RSI7'], errors='coerce')
    df['RSI14'] = pd.to_numeric(df['RSI14'], errors='coerce')

    tab1, tab2 = st.tabs(["🎯 ANA HİSSELER", "📉 TEKNİK ANALİZ (7 > 14)"])
    
    with tab1:
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        st.dataframe(ana_df[['Hisse', 'Fiyat', 'RSI7', 'RSI14']], use_container_width=True)

    with tab2:
        st.subheader("Filtre: RSI(14) < 30 VE RSI(7) > RSI(14)")
        
        
        
        if st.button("Taramayı Başlat"):
            # O 4 hisseyi yakalayacak olan asıl filtre
            sonuc = df[(df['RSI14'] < 30) & (df['RSI7'] > df['RSI14'])].copy()
            
            if not sonuc.empty:
                st.write(f"🚀 Kriterlere uyan **{len(sonuc)}** hisse bulundu.")
                st.dataframe(sonuc[['Hisse', 'İsim', 'Fiyat', 'RSI14', 'RSI7', 'Hacim']].sort_values(by="Hacim", ascending=False))
            else:
                st.warning("Tam kurala uyan hisse şu an yok. RSI(7) ve RSI(14) değerlerinin dolu olduğunu aşağıdaki tablodan kontrol et:")
                st.write("Veritabanı Örneği (Dolu mu?):", df[['Hisse', 'RSI7', 'RSI14']].head(10))
else:
    st.info("Lütfen verileri yükleyin.")
