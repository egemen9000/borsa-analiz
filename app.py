import streamlit as st
from tradingview_ta import TA_Handler, Interval
import pandas as pd
import time
import os

st.set_page_config(page_title="ABD Büyük Veri Merkezi", layout="wide")

# Örnek listeyi genişletiyoruz
SEMBOLLER = ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'INTC', 'PLTR', 'MU']

def toplu_veri_indir():
    st.info("🔄 Veriler indiriliyor... Lütfen bekleyin.")
    tum_veriler = []
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
            if analiz and analiz.indicators:
                ind = analiz.indicators
                tum_veriler.append({
                    "Hisse": sembol,
                    "Fiyat": ind.get("close"),
                    "RSI": ind.get("RSI"),
                    "VWAP": ind.get("VWAP"),
                    "EMA20": ind.get("EMA20"),
                    "Zaman": time.strftime('%H:%M:%S')
                })
        except Exception as e:
            continue # Hata veren hisseyi atla, sistemi durdurma
        
        progress_bar.progress((idx + 1) / len(SEMBOLLER))
    
    if not tum_veriler:
        return pd.DataFrame() # Tamamen boşsa boş dataframe dön
        
    return pd.DataFrame(tum_veriler)

st.title("📊 ABD Borsası Veri Deposu")

# Buton Alanı
col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 TÜM VERİLERİ YENİLE (GÜNCELLE)"):
        yeni_df = toplu_veri_indir()
        if not yeni_df.empty:
            yeni_df.to_csv("canli_veriler.csv", index=False)
            st.success("✅ Veriler indirildi ve CSV olarak kaydedildi!")
            st.rerun() # Sayfayı yenile ki veriler yüklensin
        else:
            st.error("❌ Hiçbir veri çekilemedi. TradingView şu an kısıtlıyor olabilir.")

# Veri Yükleme Alanı
if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    
    st.write(f"📂 Son Güncelleme: {len(df)} hisse kayıtlı.")
    
    tab1, tab2 = st.tabs(["🎯 STRATEJİ FİLTRESİ", "📉 DİPTEN DÖNÜŞ"])
    
    with tab1:
        # Sütunların varlığını kontrol ederek filtreleme yapıyoruz (Hata almamak için)
        if 'Fiyat' in df.columns and 'VWAP' in df.columns:
            filtre = df[(df['Fiyat'] > df['VWAP']) & (df['RSI'] > 50)]
            st.subheader("Trendi Güçlü Hisseler")
            st.dataframe(filtre, use_container_width=True)
        else:
            st.warning("Veri setinde gerekli sütunlar eksik. Lütfen verileri yenileyin.")
            
    with tab2:
        if 'RSI' in df.columns:
            dip_filtre = df[df['RSI'] < 30]
            st.subheader("Aşırı Satım (Dip) Bölgesi")
            st.dataframe(dip_filtre, use_container_width=True)
else:
    st.warning("Henüz yerel veri dosyası (CSV) bulunamadı. Lütfen 'Tüm Verileri Yenile' butonuna basın.")
