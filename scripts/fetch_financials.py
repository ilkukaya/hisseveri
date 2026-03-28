"""
Finansal tabloları isyatirimhisse kütüphanesi ile çeker.
"""

import json
import os
import time
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FINANCIALS_DIR = os.path.join(DATA_DIR, "financials")
COMPANIES_DIR = os.path.join(DATA_DIR, "companies")

CURRENT_YEAR = datetime.now().year


def fetch_financial_data(ticker):
    """Belirli bir hisse için mali tablo verilerini çeker."""
    try:
        from isyatirimhisse import fetch_financials

        df = fetch_financials(
            symbols=ticker,
            start_year=CURRENT_YEAR - 2,
            end_year=CURRENT_YEAR,
            exchange="TRY",
            financial_group="1",
        )

        if df is None or df.empty:
            return None

        return df

    except ImportError:
        print("isyatirimhisse kütüphanesi bulunamadı.")
        return None
    except Exception as e:
        print(f"  Hata ({ticker}): {e}")
        return None


def parse_to_json(df, ticker):
    """DataFrame'i site yapısına uygun JSON formatına dönüştürür."""
    if df is None or df.empty:
        return None

    # DataFrame sütunlarını analiz et
    columns = list(df.columns)
    print(f"    Sütunlar: {columns[:5]}...")

    # Dönemleri belirle (sütun adlarından)
    period_cols = [c for c in columns if "/" in str(c) or any(str(y) in str(c) for y in range(2020, 2030))]

    if not period_cols:
        print(f"    {ticker}: Dönem sütunları bulunamadı")
        return None

    # Son 8 dönemi al
    periods = period_cols[:8] if len(period_cols) >= 8 else period_cols

    # Mali kalemleri parse et
    result = {
        "ticker": ticker,
        "currency": "TRY",
        "periods": [str(p) for p in periods],
        "balanceSheet": {
            "currentAssets": [],
            "nonCurrentAssets": [],
            "totalAssets": [],
            "currentLiabilities": [],
            "nonCurrentLiabilities": [],
            "totalLiabilities": [],
            "equity": [],
        },
        "incomeStatement": {
            "revenue": [],
            "costOfRevenue": [],
            "grossProfit": [],
            "operatingIncome": [],
            "netIncome": [],
            "ebitda": [],
        },
        "cashFlow": {
            "operating": [],
            "investing": [],
            "financing": [],
        },
    }

    # Kalem eşleştirme
    item_map = {
        "Dönen Varlıklar": ("balanceSheet", "currentAssets"),
        "Duran Varlıklar": ("balanceSheet", "nonCurrentAssets"),
        "Toplam Varlıklar": ("balanceSheet", "totalAssets"),
        "Kısa Vadeli Yükümlülükler": ("balanceSheet", "currentLiabilities"),
        "Uzun Vadeli Yükümlülükler": ("balanceSheet", "nonCurrentLiabilities"),
        "Toplam Yükümlülükler": ("balanceSheet", "totalLiabilities"),
        "Özkaynaklar": ("balanceSheet", "equity"),
        "Ana Ortaklık Payları": ("balanceSheet", "equity"),
        "Hasılat": ("incomeStatement", "revenue"),
        "Satışların Maliyeti": ("incomeStatement", "costOfRevenue"),
        "Brüt Kar (Zarar)": ("incomeStatement", "grossProfit"),
        "Esas Faaliyet Karı (Zararı)": ("incomeStatement", "operatingIncome"),
        "Dönem Net Karı (Zararı)": ("incomeStatement", "netIncome"),
        "İşletme Faaliyetlerinden Nakit Akışları": ("cashFlow", "operating"),
        "Yatırım Faaliyetlerinden Nakit Akışları": ("cashFlow", "investing"),
        "Finansman Faaliyetlerinden Nakit Akışları": ("cashFlow", "financing"),
    }

    # DataFrame'den verileri çek
    name_col = None
    for col in ["itemDescTr", "FINANCIAL_ITEM_NAME_TR", "Kalem"]:
        if col in df.columns:
            name_col = col
            break

    if name_col is None:
        # İlk sütunu kalem adı olarak kullan
        name_col = columns[0]

    for _, row in df.iterrows():
        item_name = str(row.get(name_col, "")).strip()

        for key, (section, field) in item_map.items():
            if key.lower() in item_name.lower():
                values = []
                for p in periods:
                    val = row.get(p, 0)
                    try:
                        values.append(float(val) if val and str(val) != "nan" else 0)
                    except (ValueError, TypeError):
                        values.append(0)

                if not result[section][field]:  # İlk eşleşmeyi al
                    result[section][field] = values
                break

    # Eksik alanları doldur
    for section in result:
        if isinstance(result[section], dict):
            for field in result[section]:
                if not result[section][field]:
                    result[section][field] = [0] * len(periods)

    return result


def save_financial_data(ticker, data):
    """Finansal verileri JSON dosyasına kaydeder."""
    os.makedirs(FINANCIALS_DIR, exist_ok=True)
    output_path = os.path.join(FINANCIALS_DIR, f"{ticker}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
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
        df = fetch_financial_data(ticker)

        if df is not None:
            parsed = parse_to_json(df, ticker)
            if parsed:
                save_financial_data(ticker, parsed)
                print(f"    Mali tablo kaydedildi.")

        time.sleep(0.5)

    print("Finansal veriler tamamlandı.")
