"""
İş Yatırım API'sinden finansal tabloları (bilanço, gelir tablosu, nakit akış) çeker.
"""

import json
import os
import time
import requests
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.isyatirim.com.tr/",
}

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FINANCIALS_DIR = os.path.join(DATA_DIR, "financials")
COMPANIES_DIR = os.path.join(DATA_DIR, "companies")

# Mali tablo API endpoint'i
MALI_TABLO_URL = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo"

# Son 2 yılın çeyreklik dönemleri
CURRENT_YEAR = datetime.now().year


def fetch_financial_table(ticker, exchange="TRY", financial_group="XI_29"):
    """Belirli bir hisse için mali tablo verilerini çeker."""
    years = [CURRENT_YEAR, CURRENT_YEAR - 1]
    periods = [12, 9, 6, 3]

    params = {
        "companyCode": ticker,
        "exchange": exchange,
        "financialGroup": financial_group,
    }

    # 4 dönem çekebiliyoruz her seferde
    for i, (year, period) in enumerate(
        [(y, p) for y in years for p in periods][:4]
    ):
        params[f"year{i + 1}"] = year
        params[f"period{i + 1}"] = period

    try:
        response = requests.get(MALI_TABLO_URL, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("value", [])
    except requests.RequestException as e:
        print(f"  Hata ({ticker}): {e}")
        return None


def parse_financial_data(raw_data, ticker):
    """Ham API verisini yapılandırılmış JSON formatına dönüştürür."""
    if not raw_data:
        return None

    # Mali tablo kalemlerini kategorize et
    balance_sheet = {}
    income_statement = {}
    cash_flow = {}

    for item in raw_data:
        code = item.get("itemCode", "")
        name_tr = item.get("itemDescTr", "")

        # Bilanço kalemleri
        if code.startswith("1"):
            balance_sheet[code] = item
        elif code.startswith("2"):
            income_statement[code] = item
        elif code.startswith("3"):
            cash_flow[code] = item

    return {
        "ticker": ticker,
        "currency": "TRY",
        "raw": raw_data,
    }


def save_financial_data(ticker, data):
    """Finansal verileri JSON dosyasına kaydeder."""
    os.makedirs(FINANCIALS_DIR, exist_ok=True)
    output_path = os.path.join(FINANCIALS_DIR, f"{ticker}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Hisse listesini yükle
    stocks_path = os.path.join(DATA_DIR, "stocks.json")
    if not os.path.exists(stocks_path):
        print("stocks.json bulunamadı. Önce fetch_all_stocks.py çalıştırın.")
        exit(1)

    with open(stocks_path, "r", encoding="utf-8") as f:
        stocks_data = json.load(f)

    tickers = [s["ticker"] for s in stocks_data.get("stocks", [])]
    print(f"{len(tickers)} hisse için finansal veriler çekiliyor...")

    for i, ticker in enumerate(tickers):
        print(f"  [{i + 1}/{len(tickers)}] {ticker}...")
        raw = fetch_financial_table(ticker)

        if raw:
            parsed = parse_financial_data(raw, ticker)
            if parsed:
                save_financial_data(ticker, parsed)

        # Rate limiting - API'ye saygılı olalım
        time.sleep(0.5)

    print("Finansal veriler tamamlandı.")
