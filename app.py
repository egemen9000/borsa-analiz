import streamlit as st
import pandas as pd
import requests

# --- AYARLAR ---
st.set_page_config(page_title="ABD Borsa Analiz (Sheets)", layout="wide")

# Senin paylaştığın ID
SHEET_ID = "1cP9ve5qOEHA9yLuQ9n08STxVNXq5-Qu7-FAgY8J0WTg"
# CSV olarak okuma linki
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.title("🛡️ ABD Borsası RSI Paneli (Google Sheets)")

# --- FONKSİYONLAR ---
def tv_verisi_cek():
    """TradingView'dan tüm verileri çeker."""
    url = "https://scanner.tradingview.com/america/scan"
    headers = {"User-Agent": "Mozilla/5.0"}
    all_data = []
    
    # 14 bin veriyi 1000'erli paketlerle çekme
    for i in range(0, 15000, 1000):
        payload = {
            "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
            "options": {"lang": "en"}, "markets": ["america"],
            "columns": ["name", "close", "Relative.Strength.Index.7", "Relative.Strength.Index.14", 
                        "Relative.Strength.Index.7[1]", "Relative.Strength.Index.14[1]", "volume"],
            "sort": {"sortBy": "volume", "sortOrder": "desc"},
            "range": [i, i + 1000]
        }
        res = requests.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            batch = res.json().get('data', [])
            for item in batch:
                d = item.get('d', [])
                all_data.append({
                    "Hisse": item.get('s', '').split(":")[1] if ":" in item.get('s', '') else item.get('s', ''),
                    "Fiyat": d[1], "RSI7": d[2], "RSI14": d[3],
                    "RSI7_Dun": d[4], "RSI14_Dun": d[5], "Hacim": d[6]
                })
        else: break
    return pd.DataFrame(all_data)

# --- ARAYÜZ ---
col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 1. VERİLERİ ÇEK VE SHEETS'E KAYDET"):
        with st.spinner("TradingView'dan 14.212 hisse çekiliyor..."):
            df = tv_verisi_cek()
            if not df.empty:
                st.session_state['ana_veri'] = df
                st.success(f"✅ {len(df)} Hisse çekildi! Şimdi bu verileri manuel olarak Google Sheets'e kopyalaman veya bir otomasyon kurman önerilir.")
                st.dataframe(df.head(10))
                
                # CSV İndirme Butonu (Sheets'e yapıştırman için)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Sheets için CSV İndir", data=csv, file_name='borsa_veri.csv')

with col2:
    if st.button("🏹 2. ANALİZ ET (SHEETS'TEN OKU)"):
        try:
            df = pd.read_csv(SHEET_URL)
            # Sayısal çevrim
            for c in ['RSI7', 'RSI14', 'RSI7_Dun', 'RSI14_Dun']:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            
            # KRİTER: RSI14 < 30 VE RSI7 yukarı keser RSI14
            mask = (df['RSI14'] < 30) & (df['RSI7_Dun'] <= df['RSI14_Dun']) & (df['RSI7'] > df['RSI14'])
            sonuc = df[mask]
            
            if not sonuc.empty:
                st.balloons()
                st.subheader(f"🎯 {len(sonuc)} Sinyal Yakalandı")
                st.dataframe(sonuc.sort_values("Hacim", ascending=False))
            else:
                st.warning("Uygun hisse bulunamadı.")
        except:
            st.error("Sheets dosyası okunamadı! İçinin dolu olduğundan emin ol.")
