import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Kesin Filtreleme", layout="wide")

st.title("🎯 Hedef Odaklı Hisse Filtreleme")

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    
    # Sayısal dönüşümü garantiye alalım
    df['RSI7'] = pd.to_numeric(df['RSI7'], errors='coerce')
    df['RSI14'] = pd.to_numeric(df['RSI14'], errors='coerce')
    df['Fiyat'] = pd.to_numeric(df['Fiyat'], errors='coerce')

    # --- ANA FİLTRELEME MANTIĞI ---
    # 1. RSI 14'ün 30'un altında (veya çok yakınında) olması
    # 2. Kısa periyodun (7), uzun periyodu (14) yukarı kesmiş veya yakalamış olması
    
    # Filtreyi senin için biraz esnettim (30 yerine 35 yaptım ki kaçmasın)
    sinyal_df = df[(df['RSI14'] <= 35) & (df['RSI7'] >= df['RSI14'])].copy()
    
    # Boş verileri (NaN) temizle
    sinyal_df = sinyal_df.dropna(subset=['RSI7', 'RSI14'])

    st.subheader(f"🔍 Filtre Sonucu: {len(sinyal_df)} Hisse Bulundu")

    if not sinyal_df.empty:
        # En yüksek hacimliler muhtemelen senin o 4 hissendir
        st.success("İşte kriterlerine uyan hisseler:")
        st.dataframe(
            sinyal_df[['Hisse', 'İsim', 'Fiyat', 'RSI7', 'RSI14', 'Hacim']]
            .sort_values(by="Hacim", ascending=False), 
            use_container_width=True
        )
    else:
        st.error("Kriterlere uyan hisse bulunamadı!")
        st.info("Neden gelmiyor olabilir? Ham veri sekmesine gidip o 4 hissenin RSI7 ve RSI14 değerlerine bak. Eğer RSI7 hala RSI14'ten küçükse (Örn: 22 < 25), teknik olarak 'Yukarı Kesişim' gerçekleşmemiş demektir.")

    # --- EKSTRA: SADECE DİPTE OLANLAR (Kesişim Şartı Olmadan) ---
    with st.expander("Sadece RSI < 30 olan tüm hisseleri gör (Kesişim şartı yok)"):
        dip_hisseler = df[df['RSI14'] < 30].sort_values(by="RSI14")
        st.dataframe(dip_hisseler[['Hisse', 'Fiyat', 'RSI14', 'RSI7']])

else:
    st.warning("Önce verileri yüklemen lazım reis!")
