import streamlit as st
import pandas as pd
import os

st.header("📊 Mevcut Veritabanı Durumu")

# Dosya adını senin önceki kodlarda kullandığın isme göre kontrol ediyoruz
dosya_adi = "ana_veritabani.csv" if os.path.exists("ana_veritabani.csv") else "canli_veriler.csv"

if os.path.exists(dosya_adi):
    df_vt = pd.read_csv(dosya_adi)
    
    # Üst Bilgiler
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Hisse Sayısı", len(df_vt))
    col2.metric("Dolu Sütunlar", len(df_vt.columns))
    col3.info(f"Dosya Adı: {dosya_adi}")

    st.divider()

    # Arama ve Filtreleme Özelliği
    arama = st.text_input("🔍 Veritabanında Hisse Ara (Örn: TSLA, AAPL):").upper()
    
    if arama:
        filtreli_df = df_vt[df_vt['Hisse'].str.contains(arama, na=False)]
        st.subheader(f"'{arama}' İçin Sonuçlar")
        st.dataframe(filtreli_df, use_container_width=True)
    else:
        st.subheader("📋 Tüm Veritabanı (İlk 500 Satır)")
        # Performans için ilk 500 satırı gösteriyoruz, istersen hepsine bakabilirsin
        st.dataframe(df_vt.head(500), use_container_width=True)

    # İndirme Butonu (Lazım olursa diye)
    csv = df_vt.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Mevcut VT'yi CSV Olarak Bilgisayara İndir",
        data=csv,
        file_name="mevcut_borsa_vt.csv",
        mime="text/csv",
    )
else:
    st.error("⚠️ Şu an sistemde kayıtlı bir veritabanı bulunamadı!")
    st.info("Lütfen önce 'TÜM PİYASAYI İNDİR' butonuna basarak 14.212 hisseyi sisteme kaydet.")
