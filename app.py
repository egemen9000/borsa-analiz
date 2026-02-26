import streamlit as st
import pandas as pd
import requests
import time

# Sayfa Genişliği ve Başlık
st.set_page_config(page_title="ABD Borsası RSI Sinyal Paneli", layout="wide")

# --- HAFIZA KURULUMU ---
# Sayfa her yenilendiğinde verilerin silinmemesi için session_state kullanıyoruz
if 'ana_veri' not in st.session_state:
    st.session_state['ana_veri'] = None

def get_tv_full_data(offset):
    """TradingView Scanner API'den 1000'erli paketler halinde veri çeker."""
    url = "https://scanner.tradingview.com/america/scan"
    
    # GitHub/Cloud ortamında engellenmemek için User-Agent ekliyoruz
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": [
            "name",                          # 0
            "description",                   # 1
            "close",                         # 2
            "Relative.Strength.Index.7",     # 3
            "Relative.Strength.Index.14",    # 4
            "Relative.Strength.Index.7[1]",  # 5 (Dünkü RSI 7)
            "Relative.Strength.Index.14[1]", # 6 (Dünkü RSI 14)
            "volume"                         # 7
        ],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [offset, offset + 1000]
    }
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=30)
        if res.status_code == 200:
            return res.json().get('data', [])
        return None
    except Exception as e:
        st.error(f"Bağlantı Hatası (Sıra {offset}): {e}")
        return None

# --- ARAYÜZ ---
st.title("🛡️ ABD Borsası RSI Tarayıcı Pro")
st.markdown("""
**Strateji:** 1. **Aşırı Satım:** RSI(14) değeri 30'un altında olmalı.
2. **Kesişim (Golden Cross):** RSI(7), RSI(14)'ü yukarı kesmiş olmalı (Dün altta, bugün üstte).
""")

# --- BUTONLAR ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔴 1. TÜM ABD PİYASASINI İNDİR"):
        all_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Yaklaşık 15.000-16.000 hisse için döngü
        for i in range(0, 16000, 1000):
            status_text.info(f"📡 Veri çekiliyor: {i} - {i+1000} arası...")
            batch = get_tv_full_data(i)
            
            if batch:
                for item in batch:
                    d = item.get('d', [])
                    all_data.append({
                        "Hisse": item.get('s', '').split(":")[1] if ":" in item.get('s', '') else item.get('s', ''),
                        "Şirket": d[1],
                        "Fiyat": d[2],
                        "RSI7": d[3],
                        "RSI14": d[4],
                        "RSI7_Dun": d[5],
                        "RSI14_Dun": d[6],
                        "Hacim": d[7]
                    })
                # İlerleme çubuğunu güncelle
                progress_bar.progress(min((i + 1000) / 16000, 1.0))
                time.sleep(0.4) # API'yi yormamak için kısa bekleme
            else:
                break
        
        if all_data:
            df_raw = pd.DataFrame(all_data).drop_duplicates(subset=['Hisse'])
            # Sayısal verilere dönüştür (Hata verenleri NaN yapar)
            numeric_cols = ["Fiyat", "RSI7", "RSI14", "RSI7_Dun", "RSI14_Dun", "Hacim"]
            for col in numeric_cols:
                df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce')
            
            st.session_state['ana_veri'] = df_raw.dropna(subset=['RSI7', 'RSI14'])
            st.success(f"✅ {len(st.session_state['ana_veri'])} Hisse Hafızaya Alındı!")
            status_text.empty()

with col2:
    if st.button("📂 2. VERİTABANINI GÖR"):
        if st.session_state['ana_veri'] is not None:
            st.subheader("📋 Güncel Veritabanı")
            st.dataframe(st.session_state['ana_veri'], use_container_width=True)
        else:
            st.warning("⚠️ Önce 1. butona basarak verileri çekmelisin.")

with col3:
    find_cross = st.button("🏹 3. SİNYAL ÜRETENLERİ BUL")

st.divider()

# --- SİNYAL ANALİZİ ---
if find_cross:
    if st.session_state['ana_veri'] is not None:
        df = st.session_state['ana_veri'].copy()
        
        # FİLTRE MANTIĞI:
        # 1. RSI(14) < 30 olacak
        # 2. RSI(7) dün RSI(14)'ten küçük veya eşitti
        # 3. RSI(7) bugün RSI(14)'ten büyük (YUKARI KESTİ)
        
        mask = (
            (df['RSI14'] < 30) & 
            (df['RSI7_Dun'] <= df['RSI14_Dun']) & 
            (df['RSI7'] > df['RSI14'])
        )
        
        crossover_list = df[mask]
        
        if not crossover_list.empty:
            st.balloons()
            st.subheader(f"🎯 Kriterlere Uyan {len(crossover_list)} Hisse Yakalandı")
            
            # Tabloyu daha şık gösterelim
            st.dataframe(
                crossover_list.sort_values(by="Hacim", ascending=False).style.format({
                    "Fiyat": "{:.2f} $",
                    "RSI7": "{:.2f}",
                    "RSI14": "{:.2f}",
                    "Hacim": "{:,.0f}"
                }),
                use_container_width=True
            )
            
            # Excel İndirme Butonu (Bonus)
            csv = crossover_list.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Sonuçları CSV Olarak İndir",
                data=csv,
                file_name='rsi_sinyalleri.csv',
                mime='text/csv',
            )
        else:
            st.info("🔍 Şu an kriterlere uyan bir kesişim bulunamadı.")
    else:
        st.error("⚠️ Önce 1. butona basıp tüm piyasayı indirmen gerekiyor!")
