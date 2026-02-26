import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Hisse Analiz Platformu", layout="wide")

# 1. SEKME İÇİN SABİT LİSTE
ANA_HISSELER = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'AVGO', 'ORCL']

def get_tv_bulk_data(start_row, row_count):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]},
            {"left": "exchange", "operation": "in_range", "right": ["AMEX", "NASDAQ", "NYSE"]}
        ],
        "options": {"lang": "en"},
        "markets": ["america"],
        # API'den RSI 7 ve 14 verilerini ham isimleriyle istiyoruz
        "columns": ["name", "close", "RSI", "VWAP", "volume", "description", "RSI[7]", "RSI[14]"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [start_row, start_row + row_count]
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return [{"Hisse": item['s'].split(":")[1], 
                     "İsim": item['d'][5], 
                     "Fiyat": item['d'][1], 
                     "RSI": item['d'][2], 
                     "VWAP": item['d'][3], 
                     "Hacim": item['d'][4],
                     "RSI7": item['d'][6], 
                     "RSI14": item['d'][7]} 
                    for item in data['data']]
    except: return []
    return []

st.title("📈 Amerika Hisse Senedi Analiz Platformu")

# VERİ YÜKLEME BUTONU (Eskiyi Siler, Yeniyi Yazar)
if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE"):
    all_rows = []
    bar = st.progress(0)
    status_msg = st.empty()
    for i in range(0, 14000, 1000):
        status_msg.info(f"Yükleniyor: {i} / 14000")
        batch = get_tv_bulk_data(i, 1000)
        if batch: all_rows.extend(batch)
        bar.progress((i + 1000) / 14000)
        time.sleep(0.4)
    if all_rows:
        df_new = pd.DataFrame(all_rows)
        df_new.to_csv("canli_veriler.csv", index=False)
        st.success("Tüm veriler sıfırlandı ve güncellendi!")
        time.sleep(1)
        st.rerun()

st.divider()

if os.path.exists("canli_veriler.csv"):
    df = pd.read_csv("canli_veriler.csv")
    # Sayısal analiz için zorunlu dönüşüm
    for col in ['RSI', 'RSI7', 'RSI14', 'Fiyat', 'VWAP']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    tab1, tab2 = st.tabs(["🎯 SEÇİLMİŞ HİSSE SENETLERİ (100 ÜZERİNDEN)", "📉 TEKNİK DİPTEN DÖNÜŞ"])
    
    # --- 1. SEKME (SKORLAMA) ---
    with tab1:
        ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
        def hesapla_puan(row):
            p = 0
            if row['Fiyat'] > row['VWAP']: p += 40
            if row['RSI'] > 50: p += 30
            if row['RSI7'] > row['RSI14']: p += 30
            return p
        if not ana_df.empty:
            ana_df['SKOR'] = ana_df.apply(hesapla_puan, axis=1)
            st.dataframe(ana_df[['Hisse', 'Fiyat', 'SKOR', 'RSI', 'RSI7', 'RSI14']].sort_values(by="SKOR", ascending=False), use_container_width=True)
        else: st.warning("Seçili hisse verisi bulunamadı. Lütfen sisteme yükleme yapın.")

    # --- 2. SEKME (BÜYÜK TARAMA) ---
    with tab2:
        st.subheader("Büyük Tarama: RSI < 30 ve RSI(7) > RSI(14)")
        if st.button("Taramayı Başlat"):
            # Teknik Filtre: RSI 30 altı ve 7 periyotluk RSI 14'ü yukarı kesmiş
            mask = (df['RSI'] < 30) & (df['RSI7'] > df['RSI14']) & (df['Fiyat'] > 0.5)
            sonuc = df[mask].dropna(subset=['RSI', 'RSI7', 'RSI14'])
            
            if not sonuc.empty:
                st.write(f"🚀 Kriterlere uyan **{len(sonuc)}** hisse senedi bulundu.")
                st.dataframe(sonuc[['Hisse', 'İsim', 'Fiyat', 'RSI', 'RSI7', 'RSI14', 'Hacim']].sort_values(by="Hacim", ascending=False), use_container_width=True)
            else:
                # Boş gelmemesi için koruma modu
                st.warning("Tam kurala (RSI < 30) uyan hisse şu an yok. RSI < 35 seviyesindeki dönüşler taranıyor...")
                yedek = df[(df['RSI'] < 35) & (df['RSI7'] > df['RSI14']) & (df['Fiyat'] > 0.5)].head(20)
                if not yedek.empty:
                    st.dataframe(yedek[['Hisse', 'Fiyat', 'RSI', 'RSI7', 'RSI14', 'Hacim']], use_container_width=True)
                else:
                    st.error("Borsada şu an dipten dönen hisse yok. Piyasanın biraz sakinleşmesini bekleyip tekrar güncelleyin.")
else:
    st.info("Sistemde veri yok. Lütfen 'Sisteme Yükle' butonu ile 14.000 hisseyi çekin.")
