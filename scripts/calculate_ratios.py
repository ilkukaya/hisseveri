"""
Finansal tablolardan rasyoları hesaplar ve şirket detay JSON'larını günceller.
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FINANCIALS_DIR = os.path.join(DATA_DIR, "financials")
COMPANIES_DIR = os.path.join(DATA_DIR, "companies")


def calculate_ratios(financials, market_cap):
    """Finansal tablolardan temel rasyoları hesaplar."""
    ratios = {}

    bs = financials.get("balanceSheet", {})
    inc = financials.get("incomeStatement", {})

    # En son dönem verilerini al (index 0)
    equity = bs.get("equity", [0])[0] if bs.get("equity") else 0
    total_assets = bs.get("totalAssets", [0])[0] if bs.get("totalAssets") else 0
    current_assets = bs.get("currentAssets", [0])[0] if bs.get("currentAssets") else 0
    current_liabilities = bs.get("currentLiabilities", [0])[0] if bs.get("currentLiabilities") else 0
    total_liabilities = bs.get("totalLiabilities", [0])[0] if bs.get("totalLiabilities") else 0

    revenue = inc.get("revenue", [0])[0] if inc.get("revenue") else 0
    net_income = inc.get("netIncome", [0])[0] if inc.get("netIncome") else 0
    gross_profit = inc.get("grossProfit", [0])[0] if inc.get("grossProfit") else 0
    ebitda = inc.get("ebitda", [0])[0] if inc.get("ebitda") else 0

    # Değerleme rasyoları
    ratios["pe"] = round(market_cap / net_income, 2) if net_income > 0 else None
    ratios["pb"] = round(market_cap / equity, 2) if equity > 0 else None
    ratios["ps"] = round(market_cap / revenue, 2) if revenue > 0 else None

    # FD/FAVÖK
    net_debt = total_liabilities - current_assets
    firm_value = market_cap + net_debt
    ratios["evEbitda"] = round(firm_value / ebitda, 2) if ebitda > 0 else None

    # Karlılık rasyoları
    ratios["roe"] = round((net_income / equity) * 100, 2) if equity > 0 else None
    ratios["roa"] = round((net_income / total_assets) * 100, 2) if total_assets > 0 else None
    ratios["netMargin"] = round((net_income / revenue) * 100, 2) if revenue > 0 else None
    ratios["grossMargin"] = round((gross_profit / revenue) * 100, 2) if revenue > 0 else None
    ratios["ebitdaMargin"] = round((ebitda / revenue) * 100, 2) if revenue > 0 else None

    # Finansal yapı rasyoları
    ratios["currentRatio"] = round(current_assets / current_liabilities, 2) if current_liabilities > 0 else None
    ratios["debtEquity"] = round(total_liabilities / equity, 2) if equity > 0 else None
    ratios["netDebtEbitda"] = round(net_debt / ebitda, 2) if ebitda > 0 else None

    # Büyüme rasyoları (YoY - yıldan yıla)
    rev_list = inc.get("revenue", [])
    ni_list = inc.get("netIncome", [])
    eq_list = bs.get("equity", [])

    ratios["revenueGrowthYoy"] = _yoy_growth(rev_list)
    ratios["netIncomeGrowthYoy"] = _yoy_growth(ni_list)
    ratios["equityGrowthYoy"] = _yoy_growth(eq_list)

    # Asit-test oranı (stok verisi olmadığı için cari oranla aynı bırakıyoruz)
    ratios["quickRatio"] = ratios["currentRatio"]

    return ratios


def _yoy_growth(values):
    """Yıldan yıla büyüme oranını hesaplar (index 0 = son dönem, index 4 = 1 yıl önce)."""
    if len(values) >= 5 and values[4] and values[4] != 0:
        return round(((values[0] - values[4]) / abs(values[4])) * 100, 2)
    return None


def calculate_sector_averages(stocks_data):
    """Sektör ortalamalarını hesaplar."""
    sector_map = {}

    for stock in stocks_data.get("stocks", []):
        sector = stock.get("sector", "Diğer")
        if sector not in sector_map:
            sector_map[sector] = {"pe": [], "pb": [], "roe": [], "changes": [], "count": 0}

        sector_map[sector]["count"] += 1
        if stock.get("pe"):
            sector_map[sector]["pe"].append(stock["pe"])
        if stock.get("pb"):
            sector_map[sector]["pb"].append(stock["pb"])
        if stock.get("roe"):
            sector_map[sector]["roe"].append(stock["roe"])
        sector_map[sector]["changes"].append(stock.get("changePercent", 0))

    sectors = []
    for name, data in sector_map.items():
        slug = name.lower().replace(" ", "-").replace("ı", "i").replace("ö", "o").replace("ü", "u").replace("ş", "s").replace("ç", "c").replace("ğ", "g")
        sectors.append({
            "slug": slug,
            "name": name,
            "stockCount": data["count"],
            "avgPE": round(sum(data["pe"]) / len(data["pe"]), 2) if data["pe"] else None,
            "avgPB": round(sum(data["pb"]) / len(data["pb"]), 2) if data["pb"] else None,
            "avgROE": round(sum(data["roe"]) / len(data["roe"]), 2) if data["roe"] else None,
            "performance": round(sum(data["changes"]) / len(data["changes"]), 2) if data["changes"] else 0,
        })

    return sorted(sectors, key=lambda x: x["stockCount"], reverse=True)


if __name__ == "__main__":
    stocks_path = os.path.join(DATA_DIR, "stocks.json")
    if not os.path.exists(stocks_path):
        print("stocks.json bulunamadı.")
        exit(1)

    with open(stocks_path, "r", encoding="utf-8") as f:
        stocks_data = json.load(f)

    print("Rasyolar hesaplanıyor...")

    for stock in stocks_data.get("stocks", []):
        ticker = stock["ticker"]
        fin_path = os.path.join(FINANCIALS_DIR, f"{ticker}.json")

        if os.path.exists(fin_path):
            with open(fin_path, "r", encoding="utf-8") as f:
                financials = json.load(f)

            ratios = calculate_ratios(financials, stock.get("marketCap", 0))

            # Stocks.json'daki hisse bilgilerini güncelle
            stock["pe"] = ratios.get("pe")
            stock["pb"] = ratios.get("pb")
            stock["roe"] = ratios.get("roe")
            stock["netMargin"] = ratios.get("netMargin")

            # Company JSON'ı güncelle/oluştur
            company_path = os.path.join(COMPANIES_DIR, f"{ticker}.json")
            if os.path.exists(company_path):
                with open(company_path, "r", encoding="utf-8") as f:
                    company = json.load(f)
                company["ratios"] = ratios
                with open(company_path, "w", encoding="utf-8") as f:
                    json.dump(company, f, ensure_ascii=False, indent=2)

    # stocks.json güncelle
    with open(stocks_path, "w", encoding="utf-8") as f:
        json.dump(stocks_data, f, ensure_ascii=False, indent=2)

    # Sektör ortalamalarını hesapla
    sectors = calculate_sector_averages(stocks_data)
    sectors_path = os.path.join(DATA_DIR, "sectors.json")
    with open(sectors_path, "w", encoding="utf-8") as f:
        json.dump(sectors, f, ensure_ascii=False, indent=2)

    print(f"Rasyolar hesaplandı. {len(sectors)} sektör güncellendi.")
