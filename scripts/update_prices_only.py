"""
Günlük kapanış fiyatı güncellemesi.
Sadece fiyat çeker, mali tablo ve fiyat geçmişi çekmez.
Fiyat değişince F/K, PD/DD gibi rasyolar da güncellenir.
GitHub Actions daily-deploy workflow'unda kullanılır.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
COMPANIES_DIR = os.path.join(DATA_DIR, "companies")
FINANCIALS_DIR = os.path.join(DATA_DIR, "financials")
PUBLIC_DATA_DIR = os.path.join(os.path.dirname(DATA_DIR), "public", "data")

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
    return False


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
    print("Günlük Fiyat Güncelleme")
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # API kontrolü
    print("\n>> İş Yatırım API kontrol ediliyor...")
    check_api()

    if not API_AVAILABLE:
        print("API erişimi yok, çıkılıyor.")
        sys.exit(1)

    # Mevcut stocks.json oku
    stocks_path = os.path.join(DATA_DIR, "stocks.json")
    with open(stocks_path, "r", encoding="utf-8") as f:
        stocks_data = json.load(f)

    stocks = stocks_data.get("stocks", [])
    print(f"\n>> {len(stocks)} hisse fiyatı güncelleniyor...")

    success_count = 0
    fail_count = 0

    for i, stock in enumerate(stocks):
        ticker = stock["ticker"]

        # Güncel fiyat çek
        price_data = fetch_current_price(ticker)
        if price_data:
            stock["price"] = price_data["price"]
            stock["change"] = price_data["change"]
            stock["changePercent"] = price_data["changePercent"]
            stock["volume"] = price_data["volume"]
            success_count += 1

            # Mali tablo varsa rasyoları yeniden hesapla
            fin_path = os.path.join(FINANCIALS_DIR, f"{ticker}.json")
            if os.path.exists(fin_path):
                with open(fin_path, "r", encoding="utf-8") as f:
                    fin_data = json.load(f)
                ratios = calculate_ratios(fin_data, stock.get("marketCap", 0))
                stock["pe"] = ratios.get("pe")
                stock["pb"] = ratios.get("pb")
                stock["roe"] = ratios.get("roe")
                stock["netMargin"] = ratios.get("netMargin")

            # Company JSON güncelle
            company_file = os.path.join(COMPANIES_DIR, f"{ticker}.json")
            if os.path.exists(company_file):
                with open(company_file, "r", encoding="utf-8") as f:
                    company = json.load(f)
                company["price"]["last"] = price_data["price"]
                company["price"]["change"] = price_data["change"]
                company["price"]["changePercent"] = price_data["changePercent"]
                company["price"]["volume"] = price_data["volume"]
                company["price"]["updatedAt"] = datetime.now().strftime("%Y-%m-%d")
                if os.path.exists(fin_path):
                    company["ratios"] = ratios
                with open(company_file, "w", encoding="utf-8") as f:
                    json.dump(company, f, ensure_ascii=False, indent=2)
        else:
            fail_count += 1

        time.sleep(0.2)

        if (i + 1) % 50 == 0:
            print(f"   [{i + 1}/{len(stocks)}] işlendi...")

    # stocks.json kaydet
    print(f"\n>> stocks.json kaydediliyor...")
    stocks_data["updatedAt"] = datetime.now().isoformat()
    with open(stocks_path, "w", encoding="utf-8") as f:
        json.dump(stocks_data, f, ensure_ascii=False, indent=2)
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    with open(os.path.join(PUBLIC_DATA_DIR, "stocks.json"), "w", encoding="utf-8") as f:
        json.dump(stocks_data, f, ensure_ascii=False, indent=2)

    # sectors.json güncelle
    print(">> sectors.json güncelleniyor...")
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

    # market.json güncelle (BIST100)
    print(">> market.json güncelleniyor...")
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
    print(f"  Fiyat güncellenen: {success_count}")
    print(f"  Başarısız: {fail_count}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
