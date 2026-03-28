"""
Tarihsel fiyat verilerini isyatirimhisse kütüphanesi ile çeker.
"""

import json
import os
import time
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PRICES_DIR = os.path.join(DATA_DIR, "prices")


def fetch_price_data(ticker, days=365):
    """Belirli bir hisse için tarihsel fiyat verisi çeker."""
    try:
        from isyatirimhisse import fetch_stock_data

        end_date = datetime.now().strftime("%d-%m-%Y")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%d-%m-%Y")

        df = fetch_stock_data(
            symbols=ticker,
            start_date=start_date,
            end_date=end_date,
        )

        if df is None or df.empty:
            return []

        prices = []
        for _, row in df.iterrows():
            try:
                date_val = row.get("TARIH", row.get("Tarih", ""))
                if hasattr(date_val, "strftime"):
                    date_str = date_val.strftime("%Y-%m-%d")
                else:
                    date_str = str(date_val)

                close = float(row.get("KAPANIS", row.get("Kapanış", 0)))
                volume = int(row.get("HACIM", row.get("Hacim", 0)))

                if close > 0:
                    prices.append({
                        "date": date_str,
                        "close": round(close, 2),
                        "volume": volume,
                    })
            except (ValueError, TypeError):
                continue

        return sorted(prices, key=lambda x: x["date"])

    except ImportError:
        print("isyatirimhisse kütüphanesi bulunamadı.")
        return []
    except Exception as e:
        print(f"  Hata ({ticker}): {e}")
        return []


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
        prices = fetch_price_data(ticker)

        if prices:
            save_price_data(ticker, prices)
            print(f"    {len(prices)} gün kaydedildi.")

        time.sleep(0.3)

    print("Fiyat verileri tamamlandı.")
