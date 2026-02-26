import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta # Teknik analiz için en standart kütüphane

st.set_page_config(page_title="yfinance RSI Crossover", layout="wide")

st.title("🛡️ yfinance ile " "Yukarı Keser" " Analizi")

# Örnek: Takip ettiğin 350 hisseyi buraya liste olarak verebiliriz.
# Şimdilik örnek birkaç tane koyuyorum:
symbols = ["AAPL", "TSLA", "NVDA", "AMD", "MSFT", "GOOGL", "AMZN", "META", "NFLX"] 

if st.button("🔍 yfinance ile Kesişimleri Tara"):
    results = []
    status = st.empty()
    
    for ticker in symbols:
        status.info(f"Checking: {ticker}")
        try:
            # Son 30 günlük veriyi çek (RSI hesaplaması için yeterli)
            data = yf.download(ticker, period="1mo", interval="1d", progress=False)
            
            if len(data) > 15:
                # pandas_ta kullanarak RSI hesapla (Standart RSI)
                data['RSI14'] = ta.rsi(data['Close'], length=14)
                data['RSI7'] = ta.rsi(data['Close'], length=7)
                
                # Son iki günün verileri
                bugun = data.iloc[-1]
                dun = data.iloc[-2]
                
                # --- SENİN KURALIN (YUKARI KESER) ---
                # 1. Dün RSI7 <= RSI14
                # 2. Bugün RSI7 > RSI14
                # 3. RSI14 < 30 (Aşırı satım)
                
                if (dun['RSI7'] <= dun['RSI14']) and (bugun['RSI7'] > bugun['RSI14']) and (bugun['RSI14'] < 30):
                    results.append({
                        "Hisse": ticker,
                        "Fiyat": round(bugun['Close'], 2),
                        "RSI7 (Bugün)": round(bugun['RSI7'], 2),
                        "RSI14 (Bugün)": round(bugun['RSI14'], 2),
                        "RSI7 (Dün)": round(dun['RSI7'], 2)
                    })
        except:
            continue

    status.empty()
    
    if results:
        st.success(f"🎯 Kesişim Veren {len(results)} Hisse Bulundu!")
        st.dataframe(pd.DataFrame(results))
    else:
        st.warning("⚠️ Seçili hisseler arasında şu an 'yukarı keser' sinyali veren yok.")

st.info("💡 Not: yfinance ile 14.000 hisseyi aynı anda taramak uzun sürebilir. Genelde kendi 'watchlist' listeniz için en güvenli yoldur.")
