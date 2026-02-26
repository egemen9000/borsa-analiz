import streamlit as st
import pandas as pd

st.set_page_config(page_title="RSI Sinyal Paneli", layout="wide")

SHEET_ID = "1cP9ve5qOEHA9yLuQ9n08STxVNXq5-Qu7-FAgY8J0WTg"
# Veriyi doğrudan CSV olarak çekme linki
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

st.title("🏹 RSI Kesişim Analizi")

if st.button("🔄 SHEETS'TEN VERİLERİ OKU VE ANALİZ ET"):
    with st.spinner("Analiz ediliyor..."):
        try:
            # Sheets'ten oku
            df = pd.read_csv(SHEET_URL)
            
            # Sayısal çevrim
            for col in ['RSI7', 'RSI14', 'RSI7_Dun', 'RSI14_Dun']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # ANALİZ: RSI(14) < 30 VE RSI(7) yukarı keser RSI(14)
            mask = (df['RSI14'] < 30) & (df['RSI7_Dun'] <= df['RSI14_Dun']) & (df['RSI7'] > df['RSI14'])
            sonuc = df[mask]
            
            if not sonuc.empty:
                st.balloons()
                st.success(f"🎯 {len(sonuc)} Sinyal Bulundu!")
                st.dataframe(sonuc.sort_values("Hacim", ascending=False))
            else:
                st.warning("Bugün kriterlere uyan bir kesişim yok.")
        except Exception as e:
            st.error(f"Hata: Sheets dosyası boş olabilir veya erişim kapalı. {e}")
