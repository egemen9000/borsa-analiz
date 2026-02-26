def get_tv_full_data(offset):
    url = "https://scanner.tradingview.com/america/scan"
    
    # Daha kapsamlı header (Tarayıcı gibi görünmek için)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.tradingview.com/",
        "Origin": "https://www.tradingview.com"
    }

    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "en"},
        "markets": ["america"],
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
        # Timeout süresini 30 saniyeye çıkardık
        res = requests.post(url, json=payload, headers=headers, timeout=30)
        if res.status_code == 200:
            data = res.json().get('data', [])
            return data
        else:
            st.error(f"Hata Kodu: {res.status_code}")
            return None
    except Exception as e:
        # Hatayı ekrana yazdır ki ne olduğunu görelim
        st.error(f"Bağlantı koptu: {str(e)}")
        return None
