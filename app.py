import streamlit as st
from tradingview_ta import TA_Handler, Interval
import pandas as pd
import time

# --- BULUT AYARLARI ---
st.set_page_config(page_title="ABD Borsaları Strateji Bulutu", layout="wide")

# Veri çekme işlemini önbelleğe alıyoruz (Hız ve Engel Aşmak İçin)
@st.cache_data(ttl=300) # 5 dakika boyunca aynı hisse için TV'ye gitmez, hafızadan okur
def veri_cek_bulut(hisse):
    try:
        handler = TA_Handler(
            symbol=hisse,
            screener="america",
            exchange="",
            interval=Interval.INTERVAL_1_DAY,
            timeout=15
        )
        return handler.get_analysis()
    except:
        return None

st.title("🛡️ ABD Borsaları Strateji Merkezi (Cloud Edition)")
st.markdown("---")

tab1, tab2 = st.tabs(["🚀 TREND ANALİZİ", "📈 DİPTEN DÖNÜŞ"])

with tab1:
    HISSELER = ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'MU', 'AVGO', 'WDC', 'PLTR']
    if st.button('Trendi Tara'):
        veriler = []
        with st.spinner('Bulut üzerinden analiz ediliyor...'):
            for h in HISSELER:
                analiz = veri_cek_bulut(h)
                if analiz:
                    ind = analiz.indicators
                    fiyat = ind.get("close")
                    # Senin meşhur skorlama mantığın
                    skor = 0
                    if ind.get("VWAP") and fiyat > ind.get("VWAP"): skor += 25
                    if ind.get("EMA5") and ind.get("EMA20") and ind.get("EMA5") > ind.get("EMA20"): skor += 20
                    rsi = ind.get("RSI")
                    if rsi and rsi > 50: skor += 10
                    if 30 < rsi < 45: skor += 10
                    if ind.get("MACD.macd") and ind.get("MACD.signal") and ind.get("MACD.macd") > ind.get("MACD.signal"): skor += 10
                    if ind.get("SMA20") and fiyat > ind.get("SMA20"): skor += 15
                    
                    veriler.append({
                        "Hisse": h, "Fiyat": round(fiyat, 2), "Skor": skor,
                        "RSI(14)": round(rsi, 2) if rsi else 0, "Sinyal": analiz.summary.get("RECOMMENDATION")
                    })
                time.sleep(1) # Bulutta çok beklemeye gerek yok ama güvenlik iyidir
            
            if veriler:
                st.dataframe(pd.DataFrame(veriler).sort_values(by="Skor", ascending=False), use_container_width=True)

with tab2:
    st.subheader("🔍 Dipten Dönüş: RSI(7) > RSI(14) & RSI(14) < 30")
    user_input = st.text_area("Hisseleri girin:", value="AAPL, MSFT, NVDA, TSLA, AMZN, INTU, WDAY, TEAM")
    raw_list = [x.strip().upper() for x in user_input.replace("\n", ",").split(",") if x.strip()]
    user_hisseler = sorted(list(set(raw_list)))
    
    if st.button("Dipten Dönüş Sinyali Tara"):
        found_stocks = []
        with st.spinner('Fırsatlar taranıyor...'):
            for symbol in user_hisseler:
                analiz = veri_cek_bulut(symbol)
                if analiz:
                    ind = analiz.indicators
                    rsi14 = ind.get("RSI")
                    rsi7 = ind.get("RSI7") or ind.get("RSI[7]")
                    if rsi14 and rsi14 < 30 and rsi7 and rsi7 > rsi14:
                        found_stocks.append({
                            "Hisse": symbol, "Fiyat": round(ind.get("close"), 2),
                            "RSI(7)": round(rsi7, 2), "RSI(14)": round(rsi14, 2), "Durum": "🚀 DİPTEN DÖNÜŞ"
                        })
                time.sleep(1)
            
            if found_stocks:
                st.dataframe(pd.DataFrame(found_stocks), use_container_width=True)
            else:
                st.warning("Kriterlere uyan hisse bulunamadı.")