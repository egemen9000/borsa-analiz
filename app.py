import streamlit as st
from tradingview_ta import TA_Handler, Interval
import pandas as pd
import time
import random

st.set_page_config(page_title="E-Borsa Analiz", layout="wide")

# Önbelleği 10 dakikaya çıkardık ki sunucuyu yormayalım
@st.cache_data(ttl=600)
def veri_cek_gizli(hisse):
    # Rastgele bir bekleme ekleyerek sorguya başlıyoruz
    time.sleep(random.uniform(2.0, 4.0)) 
    try:
        handler = TA_Handler(
            symbol=hisse,
            screener="america",
            exchange="",
            interval=Interval.INTERVAL_1_DAY,
            timeout=20
        )
        return handler.get_analysis()
    except Exception as e:
        return None

st.title("🛡️ Borsa Analiz (Güvenli Mod)")

tab1, tab2 = st.tabs(["🚀 TREND ANALİZİ", "📈 DİPTEN DÖNÜŞ"])

with tab1:
    HISSELER = ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA']
    if st.button('Trendi Tara'):
        veriler = []
        bar1 = st.progress(0)
        for idx, h in enumerate(HISSELER):
            res = veri_cek_gizli(h)
            if res:
                ind = res.indicators
                veriler.append({"Hisse": h, "Fiyat": round(ind.get("close"), 2), "Skor": 100}) # Skorlama mantığını buraya ekleyebilirsin
            bar1.progress((idx + 1) / len(HISSELER))
        if veriler:
            st.dataframe(pd.DataFrame(veriler))

with tab2:
    st.subheader("🔍 Dipten Dönüş Analizi")
    user_input = st.text_area("Hisseler:", "AAPL, MSFT, NVDA, TSLA, AMZN")
    hisseler = [x.strip().upper() for x in user_input.replace("\n", ",").split(",") if x.strip()][:5] # Max 5 hisse sınırı
    
    if st.button("Dipten Dönüş Tara"):
        found = []
        bar2 = st.progress(0)
        for idx, symbol in enumerate(hisseler):
            st.write(f"⌛ {symbol} analiz ediliyor...")
            res = veri_cek_gizli(symbol)
            if res:
                ind = res.indicators
                rsi14 = ind.get("RSI")
                rsi7 = ind.get("RSI7") or ind.get("RSI[7]")
                if rsi14 and rsi14 < 35 and rsi7 and rsi7 > rsi14:
                    found.append({"Hisse": symbol, "RSI(14)": round(rsi14, 2), "Durum": "🔥 FIRSAT"})
            bar2.progress((idx + 1) / len(hisseler))
        
        if found:
            st.success(f"{len(found)} hisse kriterlere uygun!")
            st.dataframe(pd.DataFrame(found))
        else:
            st.warning("Şu an kriterlere uyan yok veya TradingView hala blokluyor. 10 dk bekleyin.")
