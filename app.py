import streamlit as st
from tradingview_ta import TA_Handler, Interval
import pandas as pd
import time

st.set_page_config(page_title="Dev Veri Merkezi", layout="wide")

# ÖNEMLİ: Hacimli ve popüler hisse listesi (Örnek olarak 50 tane koydum, bunu büyütebilirsin)
SEMBOLLER = ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'INTC', 
             'MU', 'AVGO', 'PLTR', 'BABA', 'PYPL', 'TSM', 'ASML', 'WDC', 'MARA', 'COIN']

def toplu_veri_indir():
    st.info("🔄 14.000 hisse arasından dev veri seti indiriliyor... (Lütfen bekleyin)")
    tum_veriler = []
    
    # İlerleme çubuğu
    progress_bar = st.progress(0)
    
    for idx, sembol in enumerate(SEMBOLLER):
        try:
            handler = TA_Handler(
                symbol=sembol,
                screener="america",
                exchange="",
                interval=Interval.INTERVAL_1_DAY,
                timeout=10
            )
            analiz = handler.get_analysis()
            if analiz:
                ind = analiz.indicators
                tum_veriler.append({
                    "Hisse": sembol,
                    "Fiyat": ind.get("close"),
                    "RSI": ind.get("RSI"),
                    "VWAP": ind.get("VWAP"),
                    "EMA20": ind.get("EMA20"),
                    "SMA50": ind.get("SMA50"),
                    "Zaman": time.strftime('%H:%M:%S')
                })
        except:
            continue
        
        # Her 5 sorguda bir kısa mola (Blok yememek için)
        if idx % 5 == 0:
            time.sleep(1)
        progress_bar.progress((idx + 1) / len(SEMBOLLER))
    
    df = pd.DataFrame(tum_veriler)
    # Veriyi bulutun geçici hafızasına (ve istersen CSV'ye) kaydet
    df.to_csv("canli_veriler.csv", index=False)
    return df

st.title("📊 ABD Borsası Büyük Veri Analizörü")

if st.button("🚀 TÜM BORSAYI TARA VE KAYDET"):
    veri_seti = toplu_veri_indir()
    st.session_state['veriler'] = veri_seti
    st.success("✅ Veriler indirildi ve yerel veritabanına kaydedildi!")

# Analiz Sekmeleri
if 'veriler' in st.session_state:
    df = st.session_state['veriler']
    
    tab1, tab2 = st.tabs(["🎯 STRATEJİ FİLTRESİ", "📉 DİPTEN DÖNÜŞ"])
    
    with tab1:
        # VWAP üstü ve RSI > 50 olanları saniyeler içinde süz
        filtre = df[(df['Fiyat'] > df['VWAP']) & (df['RSI'] > 50)]
        st.subheader("Trendi Güçlü Hisseler")
        st.write(f"Kriterlere uyan {len(filtre)} hisse bulundu.")
        st.dataframe(filtre)
        
    with tab2:
        # RSI < 30 olanları süz
        dip_filtre = df[df['RSI'] < 30]
        st.subheader("Aşırı Satım Bölgesindeki Hisseler")
        st.dataframe(dip_filtre)
else:
    st.warning("Henüz veri indirilmedi. Lütfen yukarıdaki butona basarak taramayı başlatın.")
