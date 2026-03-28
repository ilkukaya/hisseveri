"""
Tüm BIST hisselerinin günlük verilerini çeker.
isyatirimhisse kütüphanesi kullanılarak İş Yatırım verilerine erişilir.
"""

import json
import os
import requests
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.isyatirim.com.tr/",
}


def fetch_stock_list():
    """BIST TÜM endeksindeki hisse listesini çeker."""
    try:
        from isyatirimhisse import fetch_stock_data

        # Son 5 iş günü verisini al - birden fazla hisse için
        end_date = datetime.now().strftime("%d-%m-%Y")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%d-%m-%Y")

        # Önce bilinen BIST30 + BIST100 hisselerini çek
        bist30 = [
            "AKBNK", "ARCLK", "ASELS", "BIMAS", "EKGYO", "EREGL",
            "FROTO", "GARAN", "GUBRF", "HEKTS", "ISCTR", "KCHOL",
            "KOZAA", "KOZAL", "KRDMD", "MGROS", "ODAS", "PETKM",
            "PGSUS", "SAHOL", "SASA", "SISE", "TAVHL", "TCELL",
            "THYAO", "TKFEN", "TOASO", "TTKOM", "TUPRS", "YKBNK",
        ]

        stocks = []
        for ticker in bist30:
            try:
                df = fetch_stock_data(
                    symbols=ticker,
                    start_date=start_date,
                    end_date=end_date,
                )
                if df is not None and not df.empty:
                    last_row = df.iloc[-1]
                    prev_row = df.iloc[-2] if len(df) > 1 else last_row
                    close = float(last_row.get("KAPANIS", last_row.get("Kapanış", 0)))
                    prev_close = float(prev_row.get("KAPANIS", prev_row.get("Kapanış", 0)))
                    change = close - prev_close
                    change_pct = (change / prev_close * 100) if prev_close > 0 else 0

                    stock = {
                        "ticker": ticker,
                        "name": "",
                        "sector": "",
                        "subsector": "",
                        "indexes": ["BIST30", "BIST100", "BISTTUM"],
                        "price": round(close, 2),
                        "change": round(change, 2),
                        "changePercent": round(change_pct, 2),
                        "volume": int(last_row.get("HACIM", last_row.get("Hacim", 0))),
                        "marketCap": 0,
                        "pe": None,
                        "pb": None,
                        "roe": None,
                        "netMargin": None,
                        "dividendYield": None,
                    }
                    stocks.append(stock)
                    print(f"  {ticker}: {close} TL")
            except Exception as e:
                print(f"  {ticker} hatası: {e}")
                continue

        return stocks

    except ImportError:
        print("isyatirimhisse kütüphanesi bulunamadı. pip install isyatirimhisse")
        return None
    except Exception as e:
        print(f"Hata: {e}")
        return None


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

    # Ayrıca public/data/ altına kopyala (SearchBar için)
    public_data_dir = os.path.join(DATA_DIR, "..", "public", "data")
    os.makedirs(public_data_dir, exist_ok=True)
    public_path = os.path.join(public_data_dir, "stocks.json")
    with open(public_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"{len(data)} hisse kaydedildi: {output_path}")


if __name__ == "__main__":
    print("BIST hisse listesi çekiliyor...")
    stocks = fetch_stock_list()
    if stocks:
        save_stocks_json(stocks)
    else:
        print("Veri alınamadı. Mevcut veriler korunuyor.")
