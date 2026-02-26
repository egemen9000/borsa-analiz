import streamlit as st
from tradingview_ta import TA_Handler, Interval
import pandas as pd
import time
import random

# Sayfa Ayarları
st.set_page_config(page_title="E-Borsa Strateji", layout="wide")

@st.cache_data(ttl=300)
def veri_cek_stabil(hisse):
    """Farklı screener ve exchange kombinasyonlarıyla veriyi zorlar"""
    denemeler = [
        {"scr": "america", "ex": ""},
        {"scr": "stock", "ex": ""},
        {"scr": "america", "ex": "NASDAQ"},
        {"scr": "america", "ex": "NYSE"}
    ]
    for d in denemeler:
        try:
            handler = TA_Handler(
                symbol=hisse,
                screener=d["scr"],
                exchange=d["ex"],
                interval=Interval.INTERVAL_1_DAY,
                timeout=15
            )
            # Bot korumasını aşmak için mikro bekleme
            time.sleep(random.uniform(0.1, 0.4))
            return handler.get_analysis()
        except:
            continue
    return None

st.title("🛡️ Borsa Strateji Bulutu")

tab1, tab2 = st.tabs(["🚀 TREND ANALİZİ", "📈 DİPTEN DÖNÜŞ"])

with tab1:
    HISSELER = ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'MU', 'AVGO', 'WDC', 'PLTR']
    if st.button('Trendi Tara'):
        veriler = []
        progress = st.progress(0)
        for idx, h in enumerate(HISSELER):
            res = veri_cek_stabil(h)
            if res:
                ind = res.indicators
                fiyat = ind.get("close")
                skor = 0
                if ind.get("VWAP") and fiyat > ind.get("VWAP"): skor += 25
                if ind.get("EMA5") and ind.get("EMA20") and ind.get("EMA5") > ind.get("EMA20"): skor += 20
                rsi = ind.get("RSI")
                if rsi and rsi > 50: skor += 10
                if 30 < rsi < 45: skor += 10
                if ind.get("MACD.macd") and ind.get("MACD.signal") and ind.get("MACD.macd") > ind.get("MACD.signal"): skor += 10
                if ind.get("SMA20") and fiyat > ind.get("SMA20"): skor += 15
                
                veriler.append({"Hisse": h, "Fiyat": round(fiyat, 2), "Skor": skor, "RSI": round(rsi, 2) if rsi else 0})
            time.sleep(random.uniform(1.2, 2.5)) # Blok yememek için kritik bekleme
            progress.progress((idx + 1) / len(HISSELER))
        if veriler:
            st.dataframe(pd.DataFrame(veriler).sort_values(by="Skor", ascending=False), use_container_width=True)

with tab2:
    st.subheader("🔍 Dipten Dönüş Analizi")
    user_input = st.text_area("Hisseler (Virgülle):", "AAPL, MSFT, NVDA, TSLA, AMZN, INTU, WDAY, TEAM")
    raw_list = [x.strip().upper() for x in user_input.replace("\n", ",").split(",") if x.strip()]
    
    if st.button("Dipten Dönüş Tara"):
        found = []
        bar = st.progress(0)
        for idx, symbol in enumerate(raw_list):
            res = veri_cek_stabil(symbol)
            if res:
                ind = res.indicators
                rsi14 = ind.get("RSI")
                rsi7 = ind.get("RSI7") or ind.get("RSI[7]")
                # Senin KRİTER: RSI14 < 30 ve RSI7 > RSI14
                if rsi14 and rsi14 < 30 and rsi7 and rsi7 > rsi14:
                    found.append({"Hisse": symbol, "Fiyat": round(ind.get("close"), 2), "RSI(7)": round(rsi7, 2), "RSI(14)": round(rsi14, 2), "Durum": "🔥 DİPTEN DÖNÜŞ"})
            time.sleep(random.uniform(1.2, 2.5))
            bar.progress((idx + 1) / len(raw_list))
        
        if found:
            st.dataframe(pd.DataFrame(found), use_container_width=True)
        else:
            st.warning("Bu hisseler arasında şu an kriterlere uyan yok veya bağlantı kısıtlandı. Listeyi azaltıp tekrar deneyin.")
