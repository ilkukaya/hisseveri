"""
Finansal tabloları İş Yatırım API'sinden doğrudan çeker.
XI_29 formatında bilanço, gelir tablosu ve nakit akış tablosunu tek seferde alır.
Bankalar için UFRS formatına düşer.
"""

import json
import os
import time
from datetime import datetime

import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FINANCIALS_DIR = os.path.join(DATA_DIR, "financials")

CURRENT_YEAR = datetime.now().year

API_URL = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo"

# XI_29 item code mapping (çoğu BIST şirketi)
# Test sonucunda doğrulanmış gerçek kodlar
XI29_CODE_MAP = {
    # Bilanço
    "1A": ("balanceSheet", "currentAssets"),           # Dönen Varlıklar
    "1AK": ("balanceSheet", "nonCurrentAssets"),        # Duran Varlıklar
    "1BL": ("balanceSheet", "totalAssets"),             # TOPLAM VARLIKLAR
    "2A": ("balanceSheet", "currentLiabilities"),       # Kısa Vadeli Yükümlülükler
    "2B": ("balanceSheet", "nonCurrentLiabilities"),    # Uzun Vadeli Yükümlülükler
    "2N": ("balanceSheet", "equity"),                   # Özkaynaklar
    # Gelir Tablosu
    "3C": ("incomeStatement", "revenue"),               # Satış Gelirleri
    "3CA": ("incomeStatement", "costOfRevenue"),        # Satışların Maliyeti (-)
    "3D": ("incomeStatement", "grossProfit"),           # BRÜT KAR (ZARAR)
    "3DF": ("incomeStatement", "operatingIncome"),      # FAALİYET KARI (ZARARI)
    "3L": ("incomeStatement", "netIncome"),             # DÖNEM KARI (ZARARI)
    # Nakit Akış
    "4C": ("cashFlow", "operating"),                    # İşletme Faaliyetlerinden Kaynaklanan Net Nakit
    "4CAK": ("cashFlow", "investing"),                  # Yatırım Faaliyetlerinden Kaynaklanan Nakit
    "4CBE": ("cashFlow", "financing"),                  # Finansman Faaliyetlerden Kaynaklanan Nakit
    # Ek kalemler (FAVÖK hesabı için)
    "4B": ("_extra", "depreciation"),                   # Amortisman Giderleri
}

# UFRS item code mapping (bankalar)
UFRS_CODE_MAP = {
    # Bilanço
    "1Z": ("balanceSheet", "totalAssets"),              # AKTİF TOPLAMI
    "2O": ("balanceSheet", "equity"),                   # XVI. ÖZKAYNAKLAR
    # Gelir Tablosu
    "3CE": ("incomeStatement", "revenue"),              # VIII. FAALİYET GELİRLERİ/GİDERLERİ TOPLAMI
    "3CH": ("incomeStatement", "operatingIncome"),      # XI. NET FAALİYET KARI/ZARARI
    "3Z": ("incomeStatement", "netIncome"),             # XXIII. NET DÖNEM KARI/ZARARI
}


def fetch_from_api(ticker, year, financial_group="XI_29"):
    """Tek bir yıl için 4 çeyrek mali tablo verisini API'den çeker."""
    params = {
        "companyCode": ticker,
        "exchange": "TRY",
        "financialGroup": financial_group,
        "year1": year, "period1": 3,
        "year2": year, "period2": 6,
        "year3": year, "period3": 9,
        "year4": year, "period4": 12,
    }
    try:
        resp = requests.get(API_URL, params=params, timeout=15, verify=True)
        resp.raise_for_status()
        data = resp.json()
        raw_rows = data.get("value", [])
        if not raw_rows:
            return None

        # API: ilk 3 key = itemCode, itemDescTr, itemDescEng; sonraki 4 = value1-4
        normalized = []
        for row in raw_rows:
            keys = list(row.keys())
            if len(keys) < 4:
                continue

            item_code = str(row[keys[0]]).strip()
            desc_tr = str(row[keys[1]]).strip()

            values = []
            for k in keys[3:7]:
                v = row.get(k, 0)
                try:
                    values.append(float(v) if v is not None and str(v) not in ("nan", "None", "") else 0)
                except (ValueError, TypeError):
                    values.append(0)
            while len(values) < 4:
                values.append(0)

            normalized.append({
                "itemCode": item_code,
                "itemDescTr": desc_tr,
                "values": values,
            })

        return normalized
    except Exception as e:
        print(f"    API hatası ({ticker}, {year}, {financial_group}): {str(e)[:80]}")
        return None


def fetch_financial_data(ticker):
    """Bir hisse için tüm mali tablo verilerini çeker ve JSON formatına dönüştürür."""

    # Önce XI_29 dene (çoğu şirket), sonra UFRS (bankalar)
    groups_to_try = [("XI_29", XI29_CODE_MAP), ("UFRS", UFRS_CODE_MAP)]

    for financial_group, code_map in groups_to_try:
        all_rows = {}
        all_periods = []
        has_data = False

        for year in range(CURRENT_YEAR - 2, CURRENT_YEAR + 1):
            rows = fetch_from_api(ticker, year, financial_group)

            year_periods = [f"{year}/{q}" for q in [3, 6, 9, 12]]
            all_periods.extend(year_periods)

            if not rows:
                continue

            has_data = True
            for row in rows:
                code = row["itemCode"]
                if code not in all_rows:
                    all_rows[code] = {"descTr": row["itemDescTr"], "values": {}}
                for i, period in enumerate(year_periods):
                    all_rows[code]["values"][period] = row["values"][i]

        if not has_data:
            continue  # Bu grup çalışmadı, sonraki grubu dene

        # Veri olan dönemleri bul (kronolojik sırala: yıl, çeyrek)
        def period_sort_key(p):
            parts = p.split("/")
            return (int(parts[0]), int(parts[1]))

        valid_periods = []
        for p in sorted(set(all_periods), key=period_sort_key):
            if any(row["values"].get(p, 0) != 0 for row in all_rows.values()):
                valid_periods.append(p)
        periods = valid_periods[-8:] if len(valid_periods) > 8 else valid_periods

        if not periods:
            continue

        # Sonuç yapısı
        result = {
            "ticker": ticker,
            "currency": "TRY",
            "periods": periods,
            "balanceSheet": {
                "currentAssets": [], "nonCurrentAssets": [], "totalAssets": [],
                "currentLiabilities": [], "nonCurrentLiabilities": [],
                "totalLiabilities": [], "equity": [],
            },
            "incomeStatement": {
                "revenue": [], "costOfRevenue": [], "grossProfit": [],
                "operatingIncome": [], "netIncome": [], "ebitda": [],
            },
            "cashFlow": {
                "operating": [], "investing": [], "financing": [],
            },
        }

        found = set()
        extra = {}  # Ek kalemler (FAVÖK hesabı için amortisman vs.)

        for code, row_data in all_rows.items():
            mapping = code_map.get(code)
            if not mapping:
                continue

            section, field = mapping

            values = []
            for p in periods:
                val = row_data["values"].get(p, 0)
                try:
                    values.append(float(val) if val is not None and str(val) not in ("nan", "None", "") else 0)
                except (ValueError, TypeError):
                    values.append(0)

            # _extra kalemleri ayrı tut
            if section == "_extra":
                extra[field] = values
                continue

            field_key = f"{section}.{field}"
            if field_key in found:
                continue

            found.add(field_key)
            result[section][field] = values

        # Eksik alanları sıfırla doldur
        for section in ["balanceSheet", "incomeStatement", "cashFlow"]:
            for field in result[section]:
                if not result[section][field]:
                    result[section][field] = [0] * len(periods)

        # totalLiabilities = currentLiabilities + nonCurrentLiabilities
        if all(v == 0 for v in result["balanceSheet"]["totalLiabilities"]):
            cl = result["balanceSheet"]["currentLiabilities"]
            ncl = result["balanceSheet"]["nonCurrentLiabilities"]
            if any(v != 0 for v in cl) or any(v != 0 for v in ncl):
                result["balanceSheet"]["totalLiabilities"] = [
                    cl[i] + ncl[i] for i in range(len(periods))
                ]

        # totalAssets = currentAssets + nonCurrentAssets (yoksa)
        if all(v == 0 for v in result["balanceSheet"]["totalAssets"]):
            ca = result["balanceSheet"]["currentAssets"]
            nca = result["balanceSheet"]["nonCurrentAssets"]
            if any(v != 0 for v in ca) or any(v != 0 for v in nca):
                result["balanceSheet"]["totalAssets"] = [
                    ca[i] + nca[i] for i in range(len(periods))
                ]

        # FAVÖK = Faaliyet Karı + Amortisman
        if all(v == 0 for v in result["incomeStatement"]["ebitda"]):
            op_inc = result["incomeStatement"]["operatingIncome"]
            depreciation = extra.get("depreciation", [0] * len(periods))
            if any(v != 0 for v in op_inc) and any(v != 0 for v in depreciation):
                result["incomeStatement"]["ebitda"] = [
                    op_inc[i] + depreciation[i] for i in range(len(periods))
                ]

        # Detaylı tablo verileri - tüm API kalemlerini kaydet
        detailed = {
            "balanceSheet": [],
            "incomeStatement": [],
            "cashFlow": [],
        }

        for code, row_data in all_rows.items():
            values_list = []
            for p in periods:
                val = row_data["values"].get(p, 0)
                try:
                    values_list.append(float(val) if val is not None and str(val) not in ("nan", "None", "") else 0)
                except (ValueError, TypeError):
                    values_list.append(0)

            # Tüm değerler 0 olan satırları atla
            if all(v == 0 for v in values_list):
                continue

            item = {
                "code": code,
                "name": row_data["descTr"],
                "values": values_list,
            }

            # Kod prefixine göre kategorize et
            if code.startswith("1") or code.startswith("2"):
                detailed["balanceSheet"].append(item)
            elif code.startswith("3"):
                detailed["incomeStatement"].append(item)
            elif code.startswith("4"):
                detailed["cashFlow"].append(item)

        # Kodlara göre sırala (API sırası korunur ama güvenlik için)
        for section in detailed:
            detailed[section].sort(key=lambda x: x["code"])

        result["detailed"] = detailed

        # Veri kalitesi kontrolü - en az bilanço veya gelir tablosu olmalı
        has_balance = any(v != 0 for v in result["balanceSheet"]["totalAssets"])
        has_equity = any(v != 0 for v in result["balanceSheet"]["equity"])
        if has_balance or has_equity:
            return result

    return None


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

    success = 0
    fail = 0

    for i, ticker in enumerate(tickers):
        print(f"  [{i + 1}/{len(tickers)}] {ticker}...", end="")
        data = fetch_financial_data(ticker)

        if data:
            rev = data["incomeStatement"]["revenue"]
            ni = data["incomeStatement"]["netIncome"]
            save_financial_data(ticker, data)
            success += 1
            parts = []
            if any(v != 0 for v in rev):
                parts.append(f"gelir:{sum(1 for v in rev if v != 0)}")
            if any(v != 0 for v in ni):
                parts.append(f"kar:{sum(1 for v in ni if v != 0)}")
            print(f" OK ({', '.join(parts) if parts else 'bilanço'})")
        else:
            fail += 1
            print(" HATA")

        time.sleep(0.3)

    print(f"\nTamamlandı: {success} başarılı, {fail} başarısız")
