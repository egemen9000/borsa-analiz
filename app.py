import streamlit as st
import pandas as pd
import requests
import json

st.set_page_config(page_title="Borsa Veri Bankası", layout="wide")

def get_tradingview_data():
    """TradingView Screener API kullanarak toplu veri çeker (Tek sorguda 100+ hisse)"""
    url = "https://scanner.tradingview.com/america/scan"
    
    # 14.000 hisse içinden en hacimli ve önemli olanları süzmek için filtre
    payload = {
        "filter": [
            {"left": "change", "operation": "nempty"},
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]},
            {"left": "subtype", "operation": "in_range", "right": ["common", "foreign-issuer", ""]},
            {"left": "exchange", "operation": "in_range", "right": ["AMEX", "NASDAQ", "NYSE"]}
        ],
        "options": {"lang": "en"},
        "markets": ["america"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": ["logoid", "name", "close", "change", "RSI", "VWAP", "EMA20", "volume", "description", "type", "subtype", "update_mode"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"}, # En yüksek hacimliler gelsin
        "range": [0, 1000] # Tek seferde ilk 1000 hisseyi alıyoruz
    }
    
    try:
        response = requests.post(url, json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            rows = []
            for item in data['data']:
                d = item['d']
                rows.append({
                    "Hisse": item['s'].split(":")[1],
                    "İsim": d[8],
                    "Fiyat": d[2],
                    "Hacim": d[7],
                    "RSI": d[4],
                    "VWAP": d[5],
                    "EMA20": d[6]
                })
            return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Screener hatası: {e}")
    return pd.DataFrame()

st.title("🏦 ABD Borsası Dev Veri Bankası")

if st.button("🚀 1000 HİSSEYİ TEK SEFERDE ÇEK"):
    df_scan = get_tradingview_data()
    if not df_scan.empty:
        # Veriyi kalıcı olarak kaydet
        df_scan.to_csv("canli_veriler.csv", index=False)
        st.success(f"✅ {len(df_scan)} dev hisse verisi başarıyla indirildi!")
        st.rerun()
    else:
        st.error("⚠️ Toplu çekim bile şu an engelleniyor. Lütfen 30 dk bekleyip tekrar deneyin.")

st.divider()

# Kayıtlı veri varsa göster ve analiz et
import os
if os.path.exists("canli_veriler.csv") and os.path.getsize("canli_veriler.csv") > 0:
    df = pd.read_csv("canli_veriler.csv")
    st.write(f"📂 Veritabanında {len(df)} hisse hazır bekliyor.")
    
    t1, t2 = st.tabs(["🚀 TREND ANALİZİ", "📉 DİPTEN DÖNÜŞ"])
    
    with t1:
        # VWAP üstü ve RSI > 50 olanları filtrele
        trend = df[(df['Fiyat'] > df['VWAP']) & (df['RSI'] > 50)].sort_values(by="Hacim", ascending=False)
        st.subheader("Güçlü Trend Hisseleri")
        st.dataframe(trend, use_container_width=True)
        
    with t2:
        # RSI < 30 olanları filtrele
        dip = df[df['RSI'] < 30].sort_values(by="RSI")
        st.subheader("Dipten Dönüş Sinyalleri")
        st.dataframe(dip, use_container_width=True)
else:
    st.info("Henüz veri indirilmemiş. Yukarıdaki butona basarak 1000 hisselik dev veri setini çekin.")
