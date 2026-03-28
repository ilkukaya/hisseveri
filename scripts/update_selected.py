"""
Seçili hisseler için mali tablo + rasyo güncelleme.
Verileri çeker, JSON dosyalarını günceller.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_financials import fetch_financial_data, save_financial_data

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
COMPANIES_DIR = os.path.join(DATA_DIR, "companies")
STOCKS_PATH = os.path.join(DATA_DIR, "stocks.json")

TICKERS = sys.argv[1:] if len(sys.argv) > 1 else [
    "FROTO", "THYAO", "AKBNK", "TUPRS", "BIMAS",
    "ASELS", "EREGL", "TCELL", "SISE", "KCHOL",
]


def calculate_ratios(fin, market_cap):
    """Finansal tablolardan rasyoları hesapla."""
    bs = fin.get("balanceSheet", {})
    inc = fin.get("incomeStatement", {})

    equity = (bs.get("equity") or [0])[-1]
    total_assets = (bs.get("totalAssets") or [0])[-1]
    current_assets = (bs.get("currentAssets") or [0])[-1]
    current_liab = (bs.get("currentLiabilities") or [0])[-1]
    total_liab = (bs.get("totalLiabilities") or [0])[-1]
    revenue = (inc.get("revenue") or [0])[-1]
    net_income = (inc.get("netIncome") or [0])[-1]
    gross_profit = (inc.get("grossProfit") or [0])[-1]
    op_income = (inc.get("operatingIncome") or [0])[-1]
    ebitda = (inc.get("ebitda") or [0])[-1]

    r = {}
    r["pe"] = round(market_cap / net_income, 2) if net_income > 0 and market_cap > 0 else None
    r["pb"] = round(market_cap / equity, 2) if equity > 0 and market_cap > 0 else None
    r["ps"] = round(market_cap / revenue, 2) if revenue > 0 and market_cap > 0 else None
    r["evEbitda"] = round(market_cap / ebitda, 2) if ebitda > 0 and market_cap > 0 else None
    r["roe"] = round((net_income / equity) * 100, 2) if equity > 0 else None
    r["roa"] = round((net_income / total_assets) * 100, 2) if total_assets > 0 else None
    r["netMargin"] = round((net_income / revenue) * 100, 2) if revenue > 0 else None
    r["grossMargin"] = round((gross_profit / revenue) * 100, 2) if revenue > 0 else None
    r["ebitdaMargin"] = round((ebitda / revenue) * 100, 2) if revenue > 0 and ebitda > 0 else None
    r["currentRatio"] = round(current_assets / current_liab, 2) if current_liab > 0 else None
    r["quickRatio"] = None
    r["debtEquity"] = round(total_liab / equity, 2) if equity > 0 else None
    r["netDebtEbitda"] = None

    # YoY büyüme
    rev_list = inc.get("revenue", [])
    ni_list = inc.get("netIncome", [])
    eq_list = bs.get("equity", [])
    r["revenueGrowthYoy"] = _yoy(rev_list)
    r["netIncomeGrowthYoy"] = _yoy(ni_list)
    r["equityGrowthYoy"] = _yoy(eq_list)

    return r


def _yoy(values):
    """Yıldan yıla büyüme: son dönem vs 4 dönem öncesi."""
    if len(values) >= 5 and values[-5] and values[-5] != 0:
        return round(((values[-1] - values[-5]) / abs(values[-5])) * 100, 2)
    return None


def main():
    print(f"{len(TICKERS)} hisse güncelleniyor: {', '.join(TICKERS)}")

    # stocks.json'dan mevcut market cap bilgisini al
    stocks_map = {}
    if os.path.exists(STOCKS_PATH):
        with open(STOCKS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            for s in data.get("stocks", []):
                stocks_map[s["ticker"]] = s

    success = 0
    for ticker in TICKERS:
        print(f"\n  {ticker}...", end="")
        fin = fetch_financial_data(ticker)

        if not fin:
            print(" HATA: veri çekilemedi")
            continue

        # Finansal verileri kaydet
        save_financial_data(ticker, fin)

        # Rasyoları hesapla ve company JSON güncelle
        stock = stocks_map.get(ticker, {})
        market_cap = stock.get("marketCap", 0)
        ratios = calculate_ratios(fin, market_cap)

        company_path = os.path.join(COMPANIES_DIR, f"{ticker}.json")
        if os.path.exists(company_path):
            with open(company_path, "r", encoding="utf-8") as f:
                company = json.load(f)
            company["ratios"] = ratios
            with open(company_path, "w", encoding="utf-8") as f:
                json.dump(company, f, ensure_ascii=False, indent=2)

        # stocks.json'daki rasyoları da güncelle
        if ticker in stocks_map:
            stocks_map[ticker]["pe"] = ratios.get("pe")
            stocks_map[ticker]["pb"] = ratios.get("pb")
            stocks_map[ticker]["roe"] = ratios.get("roe")
            stocks_map[ticker]["netMargin"] = ratios.get("netMargin")

        rev = fin["incomeStatement"]["revenue"]
        ni = fin["incomeStatement"]["netIncome"]
        ebitda = fin["incomeStatement"]["ebitda"]
        print(f" OK | Gelir: {rev[-1]/1e6:,.0f}M | Kar: {ni[-1]/1e6:,.0f}M | FAVÖK: {ebitda[-1]/1e6:,.0f}M")
        if ratios.get("pe"):
            print(f"         F/K: {ratios['pe']} | PD/DD: {ratios.get('pb')} | ROE: {ratios.get('roe')}%")

        success += 1

    # stocks.json güncelle
    if os.path.exists(STOCKS_PATH) and stocks_map:
        with open(STOCKS_PATH, "r", encoding="utf-8") as f:
            full_data = json.load(f)
        for i, s in enumerate(full_data.get("stocks", [])):
            if s["ticker"] in stocks_map:
                full_data["stocks"][i] = stocks_map[s["ticker"]]
        with open(STOCKS_PATH, "w", encoding="utf-8") as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        # Public copy
        pub_path = os.path.join(os.path.dirname(DATA_DIR), "public", "data", "stocks.json")
        if os.path.exists(os.path.dirname(pub_path)):
            with open(pub_path, "w", encoding="utf-8") as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"Tamamlandı: {success}/{len(TICKERS)} başarılı")


if __name__ == "__main__":
    main()
