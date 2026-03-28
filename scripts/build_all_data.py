"""
Tüm BIST hisselerini GitHub'dan çeker ve data/ altında JSON dosyaları oluşturur.
Bu script sandbox ortamında çalışır (GitHub erişimi var, İş Yatırım yok).
GitHub Actions'da çalışınca isyatirimhisse ile gerçek fiyat/mali veriler de çekilir.
"""

import json
import os
import urllib.request
from datetime import datetime, timedelta
import random
import math

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
COMPANIES_DIR = os.path.join(DATA_DIR, "companies")
FINANCIALS_DIR = os.path.join(DATA_DIR, "financials")
PRICES_DIR = os.path.join(DATA_DIR, "prices")
PUBLIC_DATA_DIR = os.path.join(os.path.dirname(DATA_DIR), "public", "data")

GITHUB_STOCK_LIST_URL = "https://raw.githubusercontent.com/yasinkurhan/Hisse-Radar-main/main/backend/app/data/bist_stocks.json"


def fetch_stock_list_from_github():
    """GitHub'daki Hisse-Radar reposundan 613 BIST hisse listesini çeker."""
    print("GitHub'dan hisse listesi çekiliyor...")
    req = urllib.request.Request(GITHUB_STOCK_LIST_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read())

    stocks_raw = data.get("stocks", data) if isinstance(data, dict) else data
    print(f"  {len(stocks_raw)} hisse bulundu.")
    return stocks_raw


def try_fetch_prices_isyatirim(ticker):
    """isyatirimhisse ile fiyat verisi çekmeyi dene."""
    try:
        from isyatirimhisse import fetch_stock_data
        end = datetime.now().strftime("%d-%m-%Y")
        start = (datetime.now() - timedelta(days=5)).strftime("%d-%m-%Y")
        df = fetch_stock_data(symbols=ticker, start_date=start, end_date=end)
        if df is not None and not df.empty:
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            close = float(last.get("HGDG_KAPANIS", 0))
            prev_close = float(prev.get("HGDG_KAPANIS", 0))
            volume = int(last.get("HGDG_HACIM", 0))
            change = close - prev_close
            pct = (change / prev_close * 100) if prev_close > 0 else 0
            return {
                "price": round(close, 2),
                "change": round(change, 2),
                "changePercent": round(pct, 2),
                "volume": volume,
            }
    except Exception:
        pass
    return None


def try_fetch_full_prices(ticker, days=365):
    """isyatirimhisse ile tam fiyat geçmişi çek."""
    try:
        from isyatirimhisse import fetch_stock_data
        end = datetime.now().strftime("%d-%m-%Y")
        start = (datetime.now() - timedelta(days=days)).strftime("%d-%m-%Y")
        df = fetch_stock_data(symbols=ticker, start_date=start, end_date=end)
        if df is not None and not df.empty:
            prices = []
            for _, row in df.iterrows():
                date_val = row.get("HGDG_TARIH", "")
                if hasattr(date_val, "strftime"):
                    date_str = date_val.strftime("%Y-%m-%d")
                else:
                    date_str = str(date_val)[:10]
                close = float(row.get("HGDG_KAPANIS", 0))
                vol = int(row.get("HGDG_HACIM", 0))
                if close > 0:
                    prices.append({"date": date_str, "close": round(close, 2), "volume": vol})
            return sorted(prices, key=lambda x: x["date"])
    except Exception:
        pass
    return None


def try_fetch_financials(ticker):
    """isyatirimhisse ile mali tablo çek."""
    try:
        from isyatirimhisse import fetch_financials
        year = datetime.now().year
        df = fetch_financials(symbols=ticker, start_year=year - 2, end_year=year, exchange="TRY", financial_group="1")
        if df is not None and not df.empty:
            return df
    except Exception:
        pass
    return None


def build_stocks_json(stocks_raw):
    """stocks.json oluşturur. İsyatirim erişimi varsa fiyat çeker, yoksa mevcut verilerden okur."""
    existing = {}
    stocks_path = os.path.join(DATA_DIR, "stocks.json")
    if os.path.exists(stocks_path):
        with open(stocks_path, "r", encoding="utf-8") as f:
            old = json.load(f)
            for s in old.get("stocks", []):
                existing[s["ticker"]] = s

    stocks = []
    api_available = False

    # İlk hisseyle API test et
    test_result = try_fetch_prices_isyatirim("THYAO")
    if test_result:
        api_available = True
        print("  İş Yatırım API erişimi mevcut. Gerçek fiyatlar çekilecek.")
    else:
        print("  İş Yatırım API erişimi yok. Mevcut veriler korunacak.")

    for i, raw in enumerate(stocks_raw):
        ticker = raw["symbol"]
        name = raw["name"]
        sector = raw["sector"]
        indexes = raw.get("indexes", [])

        # Mevcut veri varsa koru
        ex = existing.get(ticker, {})

        stock = {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "subsector": sector,
            "indexes": indexes,
            "price": ex.get("price", 0),
            "change": ex.get("change", 0),
            "changePercent": ex.get("changePercent", 0),
            "volume": ex.get("volume", 0),
            "marketCap": ex.get("marketCap", 0),
            "pe": ex.get("pe"),
            "pb": ex.get("pb"),
            "roe": ex.get("roe"),
            "netMargin": ex.get("netMargin"),
            "dividendYield": ex.get("dividendYield"),
        }

        # API varsa fiyat çek
        if api_available:
            price_data = try_fetch_prices_isyatirim(ticker)
            if price_data:
                stock["price"] = price_data["price"]
                stock["change"] = price_data["change"]
                stock["changePercent"] = price_data["changePercent"]
                stock["volume"] = price_data["volume"]
            if (i + 1) % 50 == 0:
                print(f"    {i + 1}/{len(stocks_raw)} hisse işlendi...")

        stocks.append(stock)

    result = {
        "updatedAt": datetime.now().isoformat(),
        "count": len(stocks),
        "stocks": stocks,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(stocks_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    with open(os.path.join(PUBLIC_DATA_DIR, "stocks.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  {len(stocks)} hisse stocks.json'a kaydedildi.")
    return stocks


def build_sectors_json(stocks):
    """Sektör verilerini hesapla ve sectors.json oluştur."""
    sector_map = {}
    for s in stocks:
        sec = s["sector"]
        if sec not in sector_map:
            sector_map[sec] = {"pe": [], "pb": [], "roe": [], "changes": [], "count": 0}
        sector_map[sec]["count"] += 1
        if s.get("pe") and s["pe"] > 0:
            sector_map[sec]["pe"].append(s["pe"])
        if s.get("pb") and s["pb"] > 0:
            sector_map[sec]["pb"].append(s["pb"])
        if s.get("roe"):
            sector_map[sec]["roe"].append(s["roe"])
        if s.get("changePercent"):
            sector_map[sec]["changes"].append(s["changePercent"])

    sectors = []
    for name, data in sorted(sector_map.items(), key=lambda x: -x[1]["count"]):
        slug = name.lower().replace(" ", "-").replace("ı", "i").replace("ö", "o").replace("ü", "u").replace("ş", "s").replace("ç", "c").replace("ğ", "g").replace("İ", "i")
        sectors.append({
            "slug": slug,
            "name": name,
            "stockCount": data["count"],
            "avgPE": round(sum(data["pe"]) / len(data["pe"]), 2) if data["pe"] else None,
            "avgPB": round(sum(data["pb"]) / len(data["pb"]), 2) if data["pb"] else None,
            "avgROE": round(sum(data["roe"]) / len(data["roe"]), 2) if data["roe"] else None,
            "performance": round(sum(data["changes"]) / len(data["changes"]), 2) if data["changes"] else 0,
        })

    with open(os.path.join(DATA_DIR, "sectors.json"), "w", encoding="utf-8") as f:
        json.dump(sectors, f, ensure_ascii=False, indent=2)
    print(f"  {len(sectors)} sektör sectors.json'a kaydedildi.")
    return sectors


def build_company_files(stocks):
    """Her hisse için companies/{TICKER}.json oluştur."""
    os.makedirs(COMPANIES_DIR, exist_ok=True)
    created = 0

    for s in stocks:
        ticker = s["ticker"]
        filepath = os.path.join(COMPANIES_DIR, f"{ticker}.json")

        # Mevcut dosya varsa koru
        if os.path.exists(filepath):
            continue

        company = {
            "ticker": ticker,
            "name": s["name"],
            "sector": s["sector"],
            "subsector": s.get("subsector", s["sector"]),
            "indexes": s.get("indexes", []),
            "website": "",
            "capital": 0,
            "freeFloat": 0,
            "ipoDate": "",
            "price": {
                "last": s.get("price", 0),
                "change": s.get("change", 0),
                "changePercent": s.get("changePercent", 0),
                "open": 0,
                "high": 0,
                "low": 0,
                "volume": s.get("volume", 0),
                "marketCap": s.get("marketCap", 0),
                "updatedAt": datetime.now().strftime("%Y-%m-%d"),
            },
            "ratios": {
                "pe": s.get("pe"),
                "pb": s.get("pb"),
                "ps": None,
                "evEbitda": None,
                "roe": s.get("roe"),
                "roa": None,
                "netMargin": s.get("netMargin"),
                "grossMargin": None,
                "ebitdaMargin": None,
                "currentRatio": None,
                "quickRatio": None,
                "debtEquity": None,
                "netDebtEbitda": None,
                "revenueGrowthYoy": None,
                "netIncomeGrowthYoy": None,
                "equityGrowthYoy": None,
            },
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(company, f, ensure_ascii=False, indent=2)
        created += 1

    print(f"  {created} yeni şirket dosyası oluşturuldu. ({len(stocks) - created} mevcut korundu)")


def build_financial_files(stocks):
    """Her hisse için financials/{TICKER}.json oluştur (yoksa boş yapı)."""
    os.makedirs(FINANCIALS_DIR, exist_ok=True)
    created = 0
    periods = ["2025/12", "2025/9", "2025/6", "2025/3", "2024/12", "2024/9", "2024/6", "2024/3"]
    zeros = [0] * len(periods)

    for s in stocks:
        ticker = s["ticker"]
        filepath = os.path.join(FINANCIALS_DIR, f"{ticker}.json")

        if os.path.exists(filepath):
            continue

        fin = {
            "ticker": ticker,
            "currency": "TRY",
            "periods": periods,
            "balanceSheet": {
                "currentAssets": list(zeros),
                "nonCurrentAssets": list(zeros),
                "totalAssets": list(zeros),
                "currentLiabilities": list(zeros),
                "nonCurrentLiabilities": list(zeros),
                "totalLiabilities": list(zeros),
                "equity": list(zeros),
            },
            "incomeStatement": {
                "revenue": list(zeros),
                "costOfRevenue": list(zeros),
                "grossProfit": list(zeros),
                "operatingIncome": list(zeros),
                "netIncome": list(zeros),
                "ebitda": list(zeros),
            },
            "cashFlow": {
                "operating": list(zeros),
                "investing": list(zeros),
                "financing": list(zeros),
            },
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(fin, f, ensure_ascii=False, indent=2)
        created += 1

    print(f"  {created} yeni mali tablo dosyası oluşturuldu. ({len(stocks) - created} mevcut korundu)")


def build_price_files(stocks):
    """Her hisse için prices/{TICKER}.json oluştur (yoksa boş array)."""
    os.makedirs(PRICES_DIR, exist_ok=True)
    created = 0

    for s in stocks:
        ticker = s["ticker"]
        filepath = os.path.join(PRICES_DIR, f"{ticker}.json")

        if os.path.exists(filepath):
            continue

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([], f)
        created += 1

    print(f"  {created} yeni fiyat dosyası oluşturuldu. ({len(stocks) - created} mevcut korundu)")


def main():
    print("=" * 60)
    print("BIST Veri Oluşturucu")
    print("=" * 60)

    # 1. GitHub'dan hisse listesini çek
    stocks_raw = fetch_stock_list_from_github()

    # 2. stocks.json oluştur
    print("\nstocks.json oluşturuluyor...")
    stocks = build_stocks_json(stocks_raw)

    # 3. sectors.json oluştur
    print("\nsectors.json oluşturuluyor...")
    build_sectors_json(stocks)

    # 4. Şirket dosyalarını oluştur
    print("\nŞirket dosyaları oluşturuluyor...")
    build_company_files(stocks)

    # 5. Mali tablo dosyaları oluştur
    print("\nMali tablo dosyaları oluşturuluyor...")
    build_financial_files(stocks)

    # 6. Fiyat dosyaları oluştur
    print("\nFiyat dosyaları oluşturuluyor...")
    build_price_files(stocks)

    print("\n" + "=" * 60)
    print(f"Tamamlandı! {len(stocks)} hisse işlendi.")
    print("=" * 60)


if __name__ == "__main__":
    main()
