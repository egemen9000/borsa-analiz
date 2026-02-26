import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="ABD Borsası RSI Tarayıcı", layout="wide")

if 'ana_veri' not in st.session_state:
    st.session_state['ana_veri'] = None

def get_tv_data(offset):
    # TradingView'ın ana endpoint'i
    url = "https://scanner.tradingview.com/america/scan"
    
    # Gerçek bir tarayıcı gibi görünmek için genişletilmiş header
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.tradingview.com",
        "Referer": "https://www.tradingview.com/",
        "Content-Type": "application/json"
    }

    # API'nin beklediği tam format
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]},
            {"left": "subtype", "operation": "in_range", "right": ["common", "foreign-issuer", "", "etf", "etn", "reit", "dr", "unit"]},
            {"left": "exchange", "operation": "in_range", "right": ["AMEX", "NASDAQ", "NYSE"]}
        ],
        "options": {"lang": "en"},
        "markets": ["america"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name", "description", "close",
            "Relative.Strength.Index.7", "Relative.Strength.Index.14",
            "Relative.Strength.Index.7[1]", "Relative.Strength.Index.14[1]",
            "volume"
        ],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [offset, offset + 1000]
    }
    
    try:
        # Verify=False eklemek bazen SSL sertifika hatalarını aşar
        res = requests.post(url, json=payload, headers=headers, timeout=20)
        if res.status_code == 200:
            return res.json().get('data', [])
        else:
            # Hata kodunu göstererek teşhis koyalım
            st.error(f"Sunucu Yanıtı: {res.status_code} - İstek reddedildi.")
            return None
    except Exception as e:
        st.error(f"Bağlantı Hatası: {str(e)}")
        return None

# --- ARAYÜZ ---
st.title("🛡️ ABD Borsası RSI Tarayıcı")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔴 1. VERİLERİ ÇEK"):
        all_stocks = []
        bar = st.progress(0)
        status = st.empty()
        
        # Limit 14,000 civarı
        limit = 15000 
        for i in range(0, limit, 1000):
            status.info(f"📡 Veri alınıyor: {i} - {i+1000}")
            batch = get_tv_data(i)
            
            if batch:
                for item in batch:
                    d = item.get('d', [])
                    all_stocks.append({
                        "Hisse": item.get('s', '').split(":")[1] if ":" in item.get('s', '') else item.get('s', ''),
                        "Şirket": d[1], "Fiyat": d[2], "RSI7": d[3], "RSI14": d[4],
                        "RSI7_Dun": d[5], "RSI14_Dun": d[6], "Hacim": d[7]
                    })
                bar.progress(min((i + 1000) / limit, 1.0))
                time.sleep(1.2) # Engellenmemek için bekleme süresini artırdık
            else:
                break
        
        if all_stocks:
            df = pd.DataFrame(all_stocks).drop_duplicates(subset=['Hisse'])
            st.session_state['ana_veri'] = df
            st.success(f"✅ {len(df)} Hisse Hafızaya Alındı!")
            status.empty()

# ... (Geri kalan Buton 2 ve Buton 3 kodları aynı kalabilir)
