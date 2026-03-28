"""
İş Yatırım API'sinden tarihsel fiyat verilerini çeker.
"""

import json
import os
import time
import requests
from datetime import datetime, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.isyatirim.com.tr/",
}

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PRICES_DIR = os.path.join(DATA_DIR, "prices")

PRICE_URL = "https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/HisseTekil"


def fetch_price_data(ticker, days=365 * 5):
    """Belirli bir hisse için tarihsel fiyat verisi çeker."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    params = {
        "hisse": ticker,
        "startdate": start_date.strftime("%d-%m-%Y"),
        "enddate": end_date.strftime("%d-%m-%Y"),
    }

    try:
        response = requests.get(PRICE_URL, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("value", [])
    except requests.RequestException as e:
        print(f"  Hata ({ticker}): {e}")
        return None


def parse_price_data(raw_data):
    """Ham fiyat verisini yapılandırılmış formata dönüştürür."""
    if not raw_data:
        return []

    prices = []
    for item in raw_data:
        try:
            date_str = item.get("HGDG_TARIH", "")
            # Tarih formatı: "DD-MM-YYYY" veya ISO format
            if "-" in date_str and len(date_str) == 10:
                parts = date_str.split("-")
                if len(parts[0]) == 2:  # DD-MM-YYYY
                    date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"

            close = float(item.get("HGDG_KAPANIS", 0))
            volume = int(item.get("HGDG_HACIM", 0))

            if close > 0:
                prices.append({
                    "date": date_str,
                    "close": round(close, 2),
                    "volume": volume,
                })
        except (ValueError, TypeError):
            continue

    return sorted(prices, key=lambda x: x["date"])


def save_price_data(ticker, prices):
    """Fiyat verilerini JSON dosyasına kaydeder."""
    os.makedirs(PRICES_DIR, exist_ok=True)
    output_path = os.path.join(PRICES_DIR, f"{ticker}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    stocks_path = os.path.join(DATA_DIR, "stocks.json")
    if not os.path.exists(stocks_path):
        print("stocks.json bulunamadı. Önce fetch_all_stocks.py çalıştırın.")
        exit(1)

    with open(stocks_path, "r", encoding="utf-8") as f:
        stocks_data = json.load(f)

    tickers = [s["ticker"] for s in stocks_data.get("stocks", [])]
    print(f"{len(tickers)} hisse için fiyat verileri çekiliyor...")

    for i, ticker in enumerate(tickers):
        print(f"  [{i + 1}/{len(tickers)}] {ticker}...")
        raw = fetch_price_data(ticker)

        if raw:
            prices = parse_price_data(raw)
            if prices:
                save_price_data(ticker, prices)
                print(f"    {len(prices)} gün kaydedildi.")

        # Rate limiting
        time.sleep(0.3)

    print("Fiyat verileri tamamlandı.")
