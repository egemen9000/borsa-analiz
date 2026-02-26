import streamlit as st
import pandas as pd
import requests
import time
import os

st.set_page_config(page_title="ABD Veri Deposu Pro", layout="wide")

# --- YARDIMCI FONKSİONLAR ---
def get_tv_bulk_data(start_row, row_count):
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]},
            {"left": "exchange", "operation": "in_range", "right": ["AMEX", "NASDAQ", "NYSE"]}
        ],
        "options": {"lang": "en"},
        "markets": ["america"],
        "columns": ["name", "close", "RSI", "VWAP", "EMA20", "volume", "description"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [start_row, start_row + row_count]
    }
    try:
        response = requests.post(url, json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            return [{"Hisse": item['s'].split(":")[1], "İsim": item['d'][6], "Fiyat": item['d'][1], 
                     "RSI": item['d'][2], "VWAP": item['d'][3], "EMA20": item['d'][4], "Hacim": item['d'][5]} 
                    for item in data['data']]
    except:
        return []
    return []

# --- 1. BÖLÜM: VERİTABANI DURUMU (PROGRESS BAR BURADA) ---
st.title("🏦 ABD Borsası Dev Veri Deposu")

db_exists = os.path.exists("canli_veriler.csv") and os.path.getsize("canli_veriler.csv") > 0

# Veritabanı Bilgi Paneli
with st.expander("📊 Veritabanı Durumu ve Güncelleme", expanded=not db_exists):
    if db_exists:
        df_status = pd.read_csv("canli_veriler.csv")
        st.success(f"✅ Veritabanı Hazır: {len(df_status)} Hisse Kayıtlı.")
    else:
        st.warning("⚠️ Veritabanı henüz oluşturulmadı. Lütfen güncellemeyi başlatın.")

    if st.button("🚀 14.000 HİSSEYİ İNDİR / GÜNCELLE"):
        all_rows = []
        # Ana Progress Bar
        main_progress = st.progress(0)
        status_msg = st.empty()
        
        start_time = time.time()
        
        # 14.000 hisseyi 1000'erli paketlerle çek
        total_steps = 14
        for i in range(total_steps):
            current_row = i * 1000
            status_msg.info(f"⏳ Paket {i+1}/{total_steps} indiriliyor... ({current_row} - {current_row+1000})")
            
            batch = get_tv_bulk_data(current_row, 1000)
            if batch:
                all_rows.extend(batch)
            
            # Progress Bar Güncelleme
            main_progress.progress((i + 1) / total_steps)
            time.sleep(0.4) # Bot koruması için mikro mola
            
        if all_rows:
            df_total = pd.DataFrame(all_rows)
            df_total.to_csv("canli_veriler.csv", index=False)
            gecen_sure = round(time.time() - start_time, 2)
            status_msg.success(f"✅ İşlem Tamamlandı! {len(df_total)} hisse {gecen_sure} saniyede kaydedildi.")
            time.sleep(2)
            st.rerun()

st.divider()

# --- 2. BÖLÜM: FİLTRELEME VE ANALİZ ---
if db_exists:
    df = pd.read_csv("canli_veriler.csv")
    
    st.sidebar.header("🔍 Filtre Ayarları")
    min_fiyat = st.sidebar.number_input("Minimum Fiyat ($)", value=1.0, step=0.5)
    min_hacim = st.sidebar.number_input("Minimum Hacim", value=500000, step=100000)
    rsi_aralik = st.sidebar.slider("RSI Aralığı", 0, 100, (30, 70))

    tab1, tab2 = st.tabs(["🚀 TREND ANALİZİ", "📉 DİPTEN DÖNÜŞ"])
    
    with tab1:
        st.subheader("🎯 Güçlü Trend (Fiyat > VWAP & RSI > 50)")
        if st.button("Trend Filtresini Çalıştır"):
            # Hızlı Filtreleme
            res = df[(df['Fiyat'] > df['VWAP']) & 
                     (df['RSI'] > 50) & 
                     (df['Fiyat'] >= min_fiyat) & 
                     (df['Hacim'] >= min_hacim)]
            st.write(f"Kriterlere uyan **{len(res)}** hisse bulundu.")
            st.dataframe(res.sort_values(by="Hacim", ascending=False), use_container_width=True)
            
    with tab2:
        st.subheader("🔍 Dipten Dönüş (RSI < 30)")
        if st.button("Dip Filtresini Çalıştır"):
            res = df[(df['RSI'] < 30) & 
                     (df['Fiyat'] >= min_fiyat) & 
                     (df['Hacim'] >= min_hacim)]
            st.write(f"Kriterlere uyan **{len(res)}** hisse bulundu.")
            st.dataframe(res.sort_values(by="RSI"), use_container_width=True)
else:
    st.info("💡 Uygulamayı kullanmak için önce yukarıdaki menüden veritabanını güncellemelisin.")
