import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="Hisse Analiz Terminali", layout="wide")

# Analiz Edilecek Ana Hisse Listesi (Puanlama için)
ANA_HISSELER = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'GOOGL', 'META', 'AMD', 'NFLX', 'AVGO', 'ORCL']

def get_tv_bulk_data(start_row, row_count):
    """TradingView'den teknik verileri paketler halinde çeker"""
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]},
            {"left": "exchange", "operation": "in_range", "right": ["AMEX", "NASDAQ", "NYSE"]}
        ],
        "options": {"lang": "en"},
        "markets": ["america"],
        # RSI[7] ve RSI[14] TradingView API'deki teknik isimleridir
        "columns": ["name", "close", "RSI", "VWAP", "volume", "description", "RSI[7]", "RSI[14]"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [start_row, start_row + row_count]
    }
    try:
        response = requests.post(url, json=payload, timeout=25)
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
    except Exception as e:
        return []
    return []

st.title("📈 Kurumsal Hisse Analiz Platformu")

# 1. VERİ GÜNCELLEME VE PROGRESS BAR
if st.button("🚀 14.000 HİSSEYİ SİSTEME YÜKLE"):
    all_rows = []
    bar = st.progress(0)
    status_msg = st.empty()
    
    total = 14000
    step = 1000
    
    for i in range(0, total, step):
        status_msg.info(f"İşleniyor: {i} - {i+step} arası veriler...")
        batch = get_tv_bulk_data(i, step)
        if batch: 
            all_rows.extend(batch)
        bar.progress((i + step) / total)
        time.sleep(0.4) # Sunucu güvenliği için kısa mola
        
    if all_rows:
        df_new = pd.DataFrame(all_rows)
        # Veriyi temizle ve kaydet
        df_new.to_csv("canli_veriler.csv", index=False)
        status_msg.success(f"✅ İşlem Tamamlandı: {len(all_rows)} hisse kaydedildi.")
        time.sleep(1)
        st.rerun()

st.divider()

# 2. VERİ ANALİZ VE FİLTRELEME
if os.path.exists("canli_veriler.csv") and os.path.getsize("canli_veriler.csv") > 0:
    df = pd.read_csv("canli_veriler.csv")
    
    # Teknik Sütunların Varlığını Kontrol Et
    required_cols = ['RSI7', 'RSI14', 'Fiyat', 'VWAP', 'RSI']
    if all(col in df.columns for col in required_cols):
        
        c1, c2, c3 = st.columns(3)
        fiyat_limit = c1.number_input("Minimum Fiyat ($)", value=1.0)
        hacim_limit = c2.number_input("Minimum Hacim (Günlük)", value=500000)
        rsi_esik = c3.slider("Dipten Dönüş RSI Sınırı", 0, 100, 30)

        tab1, tab2 = st.tabs(["🎯 LİSTE ANALİZİ VE PUANLAMA", "📉 TEKNİK DİPTEN DÖNÜŞ"])
        
        with tab1:
            st.subheader("Seçilmiş Hisse Senetleri Skor Tablosu (100 Üzerinden)")
            ana_df = df[df['Hisse'].isin(ANA_HISSELER)].copy()
            
            def hesapla_skor(row):
                score = 0
                try:
                    # Kriter 1: Fiyat VWAP üzerindeyse (+40 Puan)
                    if float(row['Fiyat']) > float(row['VWAP']): score += 40
                    # Kriter 2: RSI 50 üzerindeyse (+30 Puan)
                    if float(row['RSI']) > 50: score += 30
                    # Kriter 3: RSI7, RSI14'ten büyükse (Pozitif Momentum) (+30 Puan)
                    if float(row['RSI7']) > float(row['RSI14']): score += 30
                except: pass
                return score

            if not ana_df.empty:
                ana_df['SKOR'] = ana_df.apply(hesapla_skor, axis=1)
                st.dataframe(ana_df[['Hisse', 'Fiyat', 'SKOR', 'RSI', 'RSI7', 'RSI14']].sort_values(by="SKOR", ascending=False), use_container_width=True)
            else:
                st.warning("Seçili hisseler veritabanında bulunamadı. Lütfen 'Sisteme Yükle' butonu ile verileri güncelleyin.")

        with tab2:
            st.info(f"Tarama Kriteri: RSI < {rsi_esik} VE RSI(7) > RSI(14)")
            
            if st.button("Teknik Dip Taramasını Başlat"):
                # Teknik Koşul: RSI belirtilen sınırın altında olacak VE kısa RSI, uzun RSI'ı yukarıda tutacak
                sonuc = df[(df['RSI'] < rsi_esik) & 
                           (df['RSI7'] > df['RSI14']) & 
                           (df['Fiyat'] >= fiyat_limit) & 
                           (df['Hacim'] >= hacim_limit)]
                
                st.write(f"Kriterlere uyan {len(sonuc)} hisse bulundu.")
                st.dataframe(sonuc.sort_values(by="Hacim", ascending=False), use_container_width=True)
    else:
        st.error("Veritabanı yapısı eksik (RSI7/RSI14 sütunları bulunamadı). Lütfen yukarıdaki butona basarak verileri yeniden yükleyin.")
else:
    st.info("Sistemde analiz edilecek veri bulunamadı. Lütfen '14.000 HİSSEYİ SİSTEME YÜKLE' butonunu kullanın.")
