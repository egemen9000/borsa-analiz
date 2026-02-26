import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="RSI Kesin Sonuç", layout="wide")

st.title("🎯 RSI Kesişim Sinyalleri")

# Veri tabanını oku
if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    
    # Sayısal veri tipini garantiye al (Hata çıkmasın)
    df['RSI7'] = pd.to_numeric(df['RSI7'], errors='coerce')
    df['RSI14'] = pd.to_numeric(df['RSI14'], errors='coerce')
    
    # --- ASIL FİLTRE BURADA ---
    # Şart 1: RSI14 kesinlikle 30'un altında olacak (Aşırı satım bölgesi)
    # Şart 2: RSI7, RSI14'ün üstünde olacak (Yukarı kesişim/ivme)
    mask = (df['RSI14'] < 30) & (df['RSI7'] > df['RSI14'])
    sonuc = df[mask].copy()

    if not sonuc.empty:
        st.success(f"🚀 Kriterlere uyan tam **{len(sonuc)}** hisse bulundu!")
        
        # Sonucu Hacim sırasına göre göster (En büyükler en üstte)
        st.dataframe(
            sonuc[['Hisse', 'İsim', 'Fiyat', 'RSI14', 'RSI7', 'Hacim']]
            .sort_values(by="Hacim", ascending=False),
            use_container_width=True
        )
    else:
        st.warning("Şu an her iki kuralı aynı anda sağlayan hisse bulunmuyor.")
        st.info("İstersen aşağıdan ham verileri tekrar kontrol edebilirsin.")
        
    # Kontrol için en düşük RSI14'lü 10 hisseyi göster
    with st.expander("Gözetim: En Düşük RSI(14) Değerine Sahip Hisseler"):
        st.dataframe(df.sort_values(by="RSI14").head(10)[['Hisse', 'RSI14', 'RSI7']])

else:
    st.error("Veritabanı (canli_veriler.csv) bulunamadı. Lütfen önce ana sayfadan verileri yükleyin!")
