import streamlit as st
from tradingview_ta import TA_Handler, Interval
import pandas as pd
import time
import random
import os

st.set_page_config(page_title="ABD Borsa Veri Havuzu", layout="wide")

# Daha küçük, seçkin bir liste ile başlayalım (Blok riskini azaltmak için)
SEMBOLLER = ['NVDA', 'AAPL', 'TSLA', 'AMD', 'MSFT', 'AMZN', 'GOOGL', 'META']

def veri_cek_hayalet(sembol):
    """TradingView'i uyutarak veri çeker"""
    try:
        # Gerçek bir insan gibi rastgele bekle (2 ile 5 saniye arası)
        time.sleep(random.uniform(2.5, 5.2))
        
        handler = TA_Handler(
            symbol=sembol,
            screener="america",
            exchange="",
            interval=Interval.INTERVAL_1_DAY,
            timeout=25
        )
        analiz = handler.get_analysis()
        if analiz and analiz.indicators:
            ind = analiz.indicators
            return {
                "Hisse": sembol,
                "Fiyat": ind.get("close"),
                "RSI": ind.get("RSI"),
                "VWAP": ind.get("VWAP"),
                "Zaman": time.strftime('%H:%M:%S')
            }
    except:
        return None
    return None

st.title("🛡️ Hayalet Modu Veri Merkezi")

if st.button("🚀 VERİLERİ SESSİZCE ÇEK VE KAYDET"):
    tum_veriler = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, s in enumerate(SEMBOLLER):
        status_text.text(f"🔍 {s} taranıyor... (İnsansı bekleme devrede)")
        veri = veri_cek_hayalet(s)
        if veri:
            tum_veriler.append(veri)
        progress_bar.progress((idx + 1) / len(SEMBOLLER))
    
    if tum_veriler:
        df_yeni = pd.DataFrame(tum_veriler)
        df_yeni.to_csv("canli_veriler.csv", index=False)
        st.success(f"✅ {len(tum_veriler)} hisse başarıyla kaydedildi!")
        st.rerun()
    else:
        st.error("❌ TradingView hala bizi blokluyor. IP'nin soğuması için 15 dakika beklemelisin.")

st.divider()

# Dosya kontrolü ve Hata yönetimi
if os.path.exists("canli_veriler.csv") and os.path.getsize("canli_veriler.csv") > 0:
    try:
        df = pd.read_csv("canli_veriler.csv")
        st.subheader(f"📂 Kayıtlı Veriler ({len(df)} Hisse)")
        st.dataframe(df, use_container_width=True)
        
        # Analiz Sekmeleri
        t1, t2 = st.tabs(["🎯 STRATEJİ", "📉 DİP"])
        with t1:
            if 'Fiyat' in df.columns and 'VWAP' in df.columns:
                f = df[(df['Fiyat'] > df['VWAP']) & (df['RSI'] > 50)]
                st.dataframe(f)
        with t2:
            if 'RSI' in df.columns:
                st.dataframe(df[df['RSI'] < 30])
    except pd.errors.EmptyDataError:
        st.warning("⚠️ Veri dosyası oluşturuldu ama içi boş. Lütfen tekrar tarama yapın.")
else:
    st.info("💡 Henüz veri yok. Yukarıdaki butona basarak taramayı başlatın.")
