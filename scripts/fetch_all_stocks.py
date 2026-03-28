"""
Tüm BIST hisselerinin günlük verilerini İş Yatırım API'sinden çeker.
"""

import json
import os
import requests
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.isyatirim.com.tr/",
}

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def fetch_stock_list():
    """Tüm BIST hisselerinin günlük özet verilerini çeker."""
    url = "https://www.isyatirim.com.tr/api/StockData"

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Hata: Hisse listesi çekilemedi - {e}")
        return None


def fetch_bist_endeks():
    """BIST endekslerini ve hisse-endeks eşleştirmelerini çeker."""
    # Endeks verileri şirket kartı sayfasından elde edilebilir
    # Basit bir başlangıç için BIST30/100 listelerini sabit tutabiliriz
    pass


def save_stocks_json(data):
    """Hisse verilerini stocks.json olarak kaydeder."""
    if not data:
        print("Kaydedilecek veri yok.")
        return

    output = {
        "updatedAt": datetime.now().isoformat(),
        "count": len(data),
        "stocks": data,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, "stocks.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"{len(data)} hisse kaydedildi: {output_path}")


if __name__ == "__main__":
    print("BIST hisse listesi çekiliyor...")
    raw_data = fetch_stock_list()

    if raw_data:
        # API yanıtını parse et ve normalize et
        stocks = []
        for item in raw_data:
            try:
                stock = {
                    "ticker": item.get("HESSION", item.get("hisse", "")),
                    "name": item.get("AD", item.get("ad", "")),
                    "sector": item.get("SEESSION", item.get("sektor", "")),
                    "subsector": item.get("ALTSEESSION", ""),
                    "indexes": [],
                    "price": float(item.get("KAESSION", item.get("kapanis", 0))),
                    "change": float(item.get("FARK", item.get("fark", 0))),
                    "changePercent": float(item.get("YUZDE", item.get("yuzde", 0))),
                    "volume": int(item.get("HACIM", item.get("hacim", 0))),
                    "marketCap": float(item.get("PIYASADEGERI", item.get("piyasaDegeri", 0))),
                    "pe": None,
                    "pb": None,
                    "roe": None,
                    "netMargin": None,
                    "dividendYield": None,
                }
                if stock["ticker"]:
                    stocks.append(stock)
            except (ValueError, TypeError) as e:
                print(f"Parse hatası: {e}")
                continue

        save_stocks_json(stocks)
    else:
        print("API'den veri alınamadı. Mevcut veriler korunuyor.")
