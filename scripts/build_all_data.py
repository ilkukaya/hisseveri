"""
Tüm BIST hisseleri için veri çekme ve JSON dosyaları oluşturma.
GitHub Actions'da çalışır: isyatirimhisse ile gerçek fiyat + mali tablo çeker.
Sandbox'ta çalışır: GitHub'dan hisse listesi çeker, mevcut verileri korur.
"""

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta

# Scripts dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
COMPANIES_DIR = os.path.join(DATA_DIR, "companies")
FINANCIALS_DIR = os.path.join(DATA_DIR, "financials")
PRICES_DIR = os.path.join(DATA_DIR, "prices")
PUBLIC_DATA_DIR = os.path.join(os.path.dirname(DATA_DIR), "public", "data")

GITHUB_STOCK_LIST_URL = "https://raw.githubusercontent.com/yasinkurhan/Hisse-Radar-main/main/backend/app/data/bist_stocks.json"

CURRENT_YEAR = datetime.now().year

# isyatirimhisse erişimi varsa True
API_AVAILABLE = False


def check_api():
    """İş Yatırım API erişimini test et."""
    global API_AVAILABLE
    try:
        from isyatirimhisse import fetch_stock_data
        end = datetime.now().strftime("%d-%m-%Y")
        start = (datetime.now() - timedelta(days=7)).strftime("%d-%m-%Y")
        df = fetch_stock_data(symbols="THYAO", start_date=start, end_date=end)
        if df is not None and not df.empty:
            API_AVAILABLE = True
            print("  [OK] İş Yatırım API erişimi mevcut.")
            return True
    except Exception as e:
        print(f"  [!] İş Yatırım API erişimi yok: {str(e)[:100]}")

    # Direct API test as fallback
    if not API_AVAILABLE:
        try:
            import requests
            resp = requests.get(
                "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo",
                params={"companyCode": "THYAO", "exchange": "TRY", "financialGroup": "UFRS",
                        "year1": CURRENT_YEAR, "period1": 3, "year2": CURRENT_YEAR, "period2": 6,
                        "year3": CURRENT_YEAR, "period3": 9, "year4": CURRENT_YEAR, "period4": 12},
                timeout=10
            )
            if resp.status_code == 200 and resp.json().get("value"):
                API_AVAILABLE = True
                print("  [OK] İş Yatırım API (direct) erişimi mevcut.")
                return True
        except Exception as e:
            print(f"  [!] Direct API erişimi de yok: {str(e)[:100]}")

    return False


def fetch_stock_list_from_github():
    """GitHub'dan 613 BIST hisse listesini çeker."""
    print("\n>> GitHub'dan hisse listesi çekiliyor...")
    req = urllib.request.Request(GITHUB_STOCK_LIST_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read())
    stocks_raw = data.get("stocks", data) if isinstance(data, dict) else data
    print(f"   {len(stocks_raw)} hisse bulundu.")
    return stocks_raw


def fetch_current_price(ticker):
    """Tek hisse için güncel fiyat çek."""
    if not API_AVAILABLE:
        return None
    try:
        from isyatirimhisse import fetch_stock_data
        end = datetime.now().strftime("%d-%m-%Y")
        start = (datetime.now() - timedelta(days=7)).strftime("%d-%m-%Y")
        df = fetch_stock_data(symbols=ticker, start_date=start, end_date=end)
        if df is not None and not df.empty:
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            close = float(last.get("HGDG_KAPANIS", 0))
            prev_close = float(prev.get("HGDG_KAPANIS", 0))
            volume = int(last.get("HGDG_HACIM", 0))
            change = round(close - prev_close, 4)
            pct = round((change / prev_close * 100), 2) if prev_close > 0 else 0
            return {"price": round(close, 2), "change": change, "changePercent": pct, "volume": volume}
    except Exception:
        pass
    return None


def fetch_price_history(ticker, days=365):
    """Hisse için tarihsel fiyat verisi çek."""
    if not API_AVAILABLE:
        return None
    try:
        from isyatirimhisse import fetch_stock_data
        end = datetime.now().strftime("%d-%m-%Y")
        start = (datetime.now() - timedelta(days=days)).strftime("%d-%m-%Y")
        df = fetch_stock_data(symbols=ticker, start_date=start, end_date=end)
        if df is not None and not df.empty:
            prices = []
            for _, row in df.iterrows():
                d = row.get("HGDG_TARIH", "")
                date_str = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10]
                close = float(row.get("HGDG_KAPANIS", 0))
                vol = int(row.get("HGDG_HACIM", 0))
                if close > 0:
                    prices.append({"date": date_str, "close": round(close, 2), "volume": vol})
            return sorted(prices, key=lambda x: x["date"])
    except Exception:
        pass
    return None


def fetch_financial_data(ticker):
    """Hisse için mali tablo verisi çek ve JSON formatına dönüştür.
    Doğrudan İş Yatırım API'sini kullanarak UFRS formatında tüm tabloları çeker."""
    if not API_AVAILABLE:
        return None
    try:
        from fetch_financials import fetch_financial_data as _fetch
        return _fetch(ticker)
    except ImportError:
        # fetch_financials.py bulunamazsa inline fallback
        pass
    except Exception as e:
        print(f"     Mali tablo hatası ({ticker}): {str(e)[:80]}")
    return None


def calculate_ratios(financials, market_cap):
    """Finansal tablolardan rasyoları hesapla."""
    bs = financials.get("balanceSheet", {})
    inc = financials.get("incomeStatement", {})
    ratios = {}

    equity = (bs.get("equity") or [0])[0]
    total_assets = (bs.get("totalAssets") or [0])[0]
    current_assets = (bs.get("currentAssets") or [0])[0]
    current_liab = (bs.get("currentLiabilities") or [0])[0]
    total_liab = (bs.get("totalLiabilities") or [0])[0]
    revenue = (inc.get("revenue") or [0])[0]
    net_income = (inc.get("netIncome") or [0])[0]
    gross_profit = (inc.get("grossProfit") or [0])[0]
    ebitda = (inc.get("ebitda") or [0])[0]

    ratios["pe"] = round(market_cap / net_income, 2) if net_income > 0 and market_cap > 0 else None
    ratios["pb"] = round(market_cap / equity, 2) if equity > 0 and market_cap > 0 else None
    ratios["ps"] = round(market_cap / revenue, 2) if revenue > 0 and market_cap > 0 else None
    ratios["roe"] = round((net_income / equity) * 100, 2) if equity > 0 else None
    ratios["roa"] = round((net_income / total_assets) * 100, 2) if total_assets > 0 else None
    ratios["netMargin"] = round((net_income / revenue) * 100, 2) if revenue > 0 else None
    ratios["grossMargin"] = round((gross_profit / revenue) * 100, 2) if revenue > 0 else None
    ratios["currentRatio"] = round(current_assets / current_liab, 2) if current_liab > 0 else None
    ratios["debtEquity"] = round(total_liab / equity, 2) if equity > 0 else None

    # Büyüme (YoY)
    rev_list = inc.get("revenue", [])
    ni_list = inc.get("netIncome", [])
    ratios["revenueGrowthYoy"] = _yoy(rev_list)
    ratios["netIncomeGrowthYoy"] = _yoy(ni_list)

    # Boş alanlar
    for k in ["evEbitda", "ebitdaMargin", "quickRatio", "netDebtEbitda", "equityGrowthYoy"]:
        if k not in ratios:
            ratios[k] = None

    return ratios


def _yoy(values):
    if len(values) >= 5 and values[4] and values[4] != 0:
        return round(((values[0] - values[4]) / abs(values[4])) * 100, 2)
    return None


def main():
    print("=" * 60)
    print("BIST Veri Pipeline")
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # API kontrolü
    print("\n>> İş Yatırım API kontrol ediliyor...")
    check_api()

    # 1. Hisse listesi
    stocks_raw = fetch_stock_list_from_github()

    # Mevcut verileri yükle
    existing_stocks = {}
    stocks_path = os.path.join(DATA_DIR, "stocks.json")
    if os.path.exists(stocks_path):
        with open(stocks_path, "r", encoding="utf-8") as f:
            old = json.load(f)
            for s in old.get("stocks", []):
                existing_stocks[s["ticker"]] = s

    # 2. Her hisse için veri çek
    print(f"\n>> {len(stocks_raw)} hisse işleniyor...")
    os.makedirs(COMPANIES_DIR, exist_ok=True)
    os.makedirs(FINANCIALS_DIR, exist_ok=True)
    os.makedirs(PRICES_DIR, exist_ok=True)

    stocks = []
    success_count = 0
    fail_count = 0

    for i, raw in enumerate(stocks_raw):
        ticker = raw["symbol"]
        name = raw["name"]
        sector = raw["sector"]
        indexes = raw.get("indexes", [])

        ex = existing_stocks.get(ticker, {})

        stock = {
            "ticker": ticker, "name": name, "sector": sector,
            "subsector": sector, "indexes": indexes,
            "price": ex.get("price", 0), "change": ex.get("change", 0),
            "changePercent": ex.get("changePercent", 0),
            "volume": ex.get("volume", 0), "marketCap": ex.get("marketCap", 0),
            "pe": ex.get("pe"), "pb": ex.get("pb"), "roe": ex.get("roe"),
            "netMargin": ex.get("netMargin"), "dividendYield": ex.get("dividendYield"),
        }

        if API_AVAILABLE:
            # Güncel fiyat
            price_data = fetch_current_price(ticker)
            if price_data:
                stock["price"] = price_data["price"]
                stock["change"] = price_data["change"]
                stock["changePercent"] = price_data["changePercent"]
                stock["volume"] = price_data["volume"]
                success_count += 1
            else:
                fail_count += 1
            time.sleep(0.2)

            # Fiyat geçmişi
            prices_file = os.path.join(PRICES_DIR, f"{ticker}.json")
            history = fetch_price_history(ticker)
            if history:
                with open(prices_file, "w", encoding="utf-8") as f:
                    json.dump(history, f, ensure_ascii=False)
            elif not os.path.exists(prices_file):
                with open(prices_file, "w", encoding="utf-8") as f:
                    json.dump([], f)
            time.sleep(0.2)

            # Mali tablolar
            fin_file = os.path.join(FINANCIALS_DIR, f"{ticker}.json")
            fin_data = fetch_financial_data(ticker)
            if fin_data:
                with open(fin_file, "w", encoding="utf-8") as f:
                    json.dump(fin_data, f, ensure_ascii=False, indent=2)

                # Rasyoları hesapla
                ratios = calculate_ratios(fin_data, stock.get("marketCap", 0))
                stock["pe"] = ratios.get("pe")
                stock["pb"] = ratios.get("pb")
                stock["roe"] = ratios.get("roe")
                stock["netMargin"] = ratios.get("netMargin")
            elif not os.path.exists(fin_file):
                # Boş yapı oluştur
                periods = ["2025/12", "2025/9", "2025/6", "2025/3", "2024/12", "2024/9", "2024/6", "2024/3"]
                zeros = [0] * 8
                empty_fin = {
                    "ticker": ticker, "currency": "TRY", "periods": periods,
                    "balanceSheet": {k: list(zeros) for k in ["currentAssets", "nonCurrentAssets", "totalAssets", "currentLiabilities", "nonCurrentLiabilities", "totalLiabilities", "equity"]},
                    "incomeStatement": {k: list(zeros) for k in ["revenue", "costOfRevenue", "grossProfit", "operatingIncome", "netIncome", "ebitda"]},
                    "cashFlow": {k: list(zeros) for k in ["operating", "investing", "financing"]},
                }
                with open(fin_file, "w", encoding="utf-8") as f:
                    json.dump(empty_fin, f, ensure_ascii=False, indent=2)
            time.sleep(0.3)

            # Şirket dosyası güncelle
            company_file = os.path.join(COMPANIES_DIR, f"{ticker}.json")
            if os.path.exists(company_file):
                with open(company_file, "r", encoding="utf-8") as f:
                    company = json.load(f)
                company["price"]["last"] = stock["price"]
                company["price"]["change"] = stock["change"]
                company["price"]["changePercent"] = stock["changePercent"]
                company["price"]["volume"] = stock["volume"]
                company["price"]["updatedAt"] = datetime.now().strftime("%Y-%m-%d")
                if fin_data:
                    company["ratios"] = calculate_ratios(fin_data, stock.get("marketCap", 0))
                with open(company_file, "w", encoding="utf-8") as f:
                    json.dump(company, f, ensure_ascii=False, indent=2)
            else:
                company = {
                    "ticker": ticker, "name": name, "sector": sector,
                    "subsector": sector, "indexes": indexes,
                    "website": "", "capital": 0, "freeFloat": 0, "ipoDate": "",
                    "price": {
                        "last": stock["price"], "change": stock["change"],
                        "changePercent": stock["changePercent"],
                        "open": 0, "high": 0, "low": 0,
                        "volume": stock["volume"],
                        "marketCap": stock.get("marketCap", 0),
                        "updatedAt": datetime.now().strftime("%Y-%m-%d"),
                    },
                    "ratios": {k: None for k in ["pe", "pb", "ps", "evEbitda", "roe", "roa",
                        "netMargin", "grossMargin", "ebitdaMargin", "currentRatio", "quickRatio",
                        "debtEquity", "netDebtEbitda", "revenueGrowthYoy", "netIncomeGrowthYoy", "equityGrowthYoy"]},
                }
                if fin_data:
                    company["ratios"] = calculate_ratios(fin_data, stock.get("marketCap", 0))
                with open(company_file, "w", encoding="utf-8") as f:
                    json.dump(company, f, ensure_ascii=False, indent=2)
        else:
            # API yok - sadece dosya yoksa oluştur
            for subdir, default in [
                (PRICES_DIR, []),
                (FINANCIALS_DIR, {
                    "ticker": ticker, "currency": "TRY",
                    "periods": ["2025/12", "2025/9", "2025/6", "2025/3", "2024/12", "2024/9", "2024/6", "2024/3"],
                    "balanceSheet": {k: [0]*8 for k in ["currentAssets", "nonCurrentAssets", "totalAssets", "currentLiabilities", "nonCurrentLiabilities", "totalLiabilities", "equity"]},
                    "incomeStatement": {k: [0]*8 for k in ["revenue", "costOfRevenue", "grossProfit", "operatingIncome", "netIncome", "ebitda"]},
                    "cashFlow": {k: [0]*8 for k in ["operating", "investing", "financing"]},
                }),
            ]:
                fp = os.path.join(subdir, f"{ticker}.json")
                if not os.path.exists(fp):
                    with open(fp, "w", encoding="utf-8") as f:
                        json.dump(default, f, ensure_ascii=False, indent=2)

            company_file = os.path.join(COMPANIES_DIR, f"{ticker}.json")
            if not os.path.exists(company_file):
                company = {
                    "ticker": ticker, "name": name, "sector": sector,
                    "subsector": sector, "indexes": indexes,
                    "website": "", "capital": 0, "freeFloat": 0, "ipoDate": "",
                    "price": {"last": 0, "change": 0, "changePercent": 0, "open": 0, "high": 0, "low": 0, "volume": 0, "marketCap": 0, "updatedAt": datetime.now().strftime("%Y-%m-%d")},
                    "ratios": {k: None for k in ["pe", "pb", "ps", "evEbitda", "roe", "roa", "netMargin", "grossMargin", "ebitdaMargin", "currentRatio", "quickRatio", "debtEquity", "netDebtEbitda", "revenueGrowthYoy", "netIncomeGrowthYoy", "equityGrowthYoy"]},
                }
                with open(company_file, "w", encoding="utf-8") as f:
                    json.dump(company, f, ensure_ascii=False, indent=2)

        stocks.append(stock)

        if (i + 1) % 50 == 0:
            print(f"   [{i + 1}/{len(stocks_raw)}] işlendi...")

    # 3. stocks.json kaydet
    print(f"\n>> stocks.json kaydediliyor ({len(stocks)} hisse)...")
    result = {"updatedAt": datetime.now().isoformat(), "count": len(stocks), "stocks": stocks}
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(stocks_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    with open(os.path.join(PUBLIC_DATA_DIR, "stocks.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 4. sectors.json oluştur
    print(">> sectors.json oluşturuluyor...")
    sector_map = {}
    for s in stocks:
        sec = s["sector"]
        if sec not in sector_map:
            sector_map[sec] = {"pe": [], "pb": [], "roe": [], "changes": [], "count": 0}
        sector_map[sec]["count"] += 1
        if s.get("pe") and s["pe"] > 0: sector_map[sec]["pe"].append(s["pe"])
        if s.get("pb") and s["pb"] > 0: sector_map[sec]["pb"].append(s["pb"])
        if s.get("roe"): sector_map[sec]["roe"].append(s["roe"])
        if s.get("changePercent"): sector_map[sec]["changes"].append(s["changePercent"])

    sectors = []
    for name, data in sorted(sector_map.items(), key=lambda x: -x[1]["count"]):
        slug = name.lower()
        for old, new in [(" ", "-"), ("ı", "i"), ("ö", "o"), ("ü", "u"), ("ş", "s"), ("ç", "c"), ("ğ", "g"), ("İ", "i")]:
            slug = slug.replace(old, new)
        sectors.append({
            "slug": slug, "name": name, "stockCount": data["count"],
            "avgPE": round(sum(data["pe"]) / len(data["pe"]), 2) if data["pe"] else None,
            "avgPB": round(sum(data["pb"]) / len(data["pb"]), 2) if data["pb"] else None,
            "avgROE": round(sum(data["roe"]) / len(data["roe"]), 2) if data["roe"] else None,
            "performance": round(sum(data["changes"]) / len(data["changes"]), 2) if data["changes"] else 0,
        })
    with open(os.path.join(DATA_DIR, "sectors.json"), "w", encoding="utf-8") as f:
        json.dump(sectors, f, ensure_ascii=False, indent=2)

    # 5. Piyasa verisi güncelle
    if API_AVAILABLE:
        print(">> Piyasa verisi güncelleniyor...")
        try:
            from isyatirimhisse import fetch_index_data
            end = datetime.now().strftime("%d-%m-%Y")
            start = (datetime.now() - timedelta(days=7)).strftime("%d-%m-%Y")
            df = fetch_index_data(indices="XU100", start_date=start, end_date=end)
            if df is not None and not df.empty:
                last = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else last
                val = float(last.iloc[-1])
                prev_val = float(prev.iloc[-1])
                market = {
                    "updatedAt": datetime.now().isoformat(),
                    "bist100": {"value": round(val, 2), "change": round(val - prev_val, 2), "changePercent": round((val - prev_val) / prev_val * 100, 2)},
                    "usdTry": {"value": 0, "change": 0, "changePercent": 0},
                    "eurTry": {"value": 0, "change": 0, "changePercent": 0},
                }
                with open(os.path.join(DATA_DIR, "market.json"), "w", encoding="utf-8") as f:
                    json.dump(market, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"   Piyasa verisi hatası: {e}")

    # Özet
    print(f"\n{'=' * 60}")
    print(f"Tamamlandı!")
    print(f"  Toplam hisse: {len(stocks)}")
    print(f"  Sektör sayısı: {len(sectors)}")
    if API_AVAILABLE:
        print(f"  Fiyat çekilen: {success_count}")
        print(f"  Başarısız: {fail_count}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
