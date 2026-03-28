"""
Finansal tabloları İş Yatırım API'sinden doğrudan çeker.
UFRS formatında bilanço, gelir tablosu ve nakit akış tablosunu tek seferde alır.
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

# UFRS item code mapping - maps itemCode to our internal field names
# These codes are stable across all BIST companies
ITEM_CODE_MAP = {
    # Balance Sheet (Bilanço)
    "1A": ("balanceSheet", "currentAssets"),          # Dönen Varlıklar
    "2A": ("balanceSheet", "nonCurrentAssets"),        # Duran Varlıklar
    "AKT": ("balanceSheet", "totalAssets"),            # Toplam Varlıklar
    "1P": ("balanceSheet", "currentLiabilities"),      # Kısa Vadeli Yükümlülükler
    "2P": ("balanceSheet", "nonCurrentLiabilities"),   # Uzun Vadeli Yükümlülükler
    "BORC": ("balanceSheet", "totalLiabilities"),      # Toplam Yükümlülükler
    "3P": ("balanceSheet", "equity"),                  # Özkaynaklar
    # Income Statement (Gelir Tablosu)
    "HASILAT": ("incomeStatement", "revenue"),         # Hasılat
    "SMM": ("incomeStatement", "costOfRevenue"),       # Satışların Maliyeti
    "BK": ("incomeStatement", "grossProfit"),          # Brüt Kar (Zarar)
    "EFK": ("incomeStatement", "operatingIncome"),     # Esas Faaliyet Karı (Zararı)
    "FAVOK": ("incomeStatement", "ebitda"),            # FAVÖK
    "DNK": ("incomeStatement", "netIncome"),           # Dönem Net Karı (Zararı)
    # Cash Flow (Nakit Akış)
    "ISLETME_NAK": ("cashFlow", "operating"),          # İşletme Faaliyetlerinden Nakit Akışları
    "YATIRIM_NAK": ("cashFlow", "investing"),          # Yatırım Faaliyetlerinden Nakit Akışları
    "FINANSMAN_NAK": ("cashFlow", "financing"),        # Finansman Faaliyetlerinden Nakit Akışları
}

# Fallback: match by Turkish description if itemCode doesn't match
ITEM_DESC_MAP = {
    "Dönen Varlıklar": ("balanceSheet", "currentAssets"),
    "Duran Varlıklar": ("balanceSheet", "nonCurrentAssets"),
    "Toplam Varlıklar": ("balanceSheet", "totalAssets"),
    "TOPLAM VARLIKLAR": ("balanceSheet", "totalAssets"),
    "Kısa Vadeli Yükümlülükler": ("balanceSheet", "currentLiabilities"),
    "Uzun Vadeli Yükümlülükler": ("balanceSheet", "nonCurrentLiabilities"),
    "Toplam Yükümlülükler": ("balanceSheet", "totalLiabilities"),
    "TOPLAM YÜKÜMLÜLÜKLER": ("balanceSheet", "totalLiabilities"),
    "Özkaynaklar": ("balanceSheet", "equity"),
    "Ana Ortaklık Payları": ("balanceSheet", "equity"),
    "Hasılat": ("incomeStatement", "revenue"),
    "Satış Gelirleri": ("incomeStatement", "revenue"),
    "Satışların Maliyeti": ("incomeStatement", "costOfRevenue"),
    "Brüt Kar (Zarar)": ("incomeStatement", "grossProfit"),
    "Brüt Kar": ("incomeStatement", "grossProfit"),
    "BRÜT KAR (ZARAR)": ("incomeStatement", "grossProfit"),
    "Esas Faaliyet Karı (Zararı)": ("incomeStatement", "operatingIncome"),
    "Esas Faaliyet Karı": ("incomeStatement", "operatingIncome"),
    "FAALİYET KARI (ZARARI)": ("incomeStatement", "operatingIncome"),
    "Dönem Net Karı (Zararı)": ("incomeStatement", "netIncome"),
    "Dönem Net Karı": ("incomeStatement", "netIncome"),
    "Net Dönem Karı (Zararı)": ("incomeStatement", "netIncome"),
    "NET DÖNEM KARI (ZARARI)": ("incomeStatement", "netIncome"),
    "FAVÖK": ("incomeStatement", "ebitda"),
    "İşletme Faaliyetlerinden Nakit Akışları": ("cashFlow", "operating"),
    "İŞLETME FAALİYETLERİNDEN NAKİT AKIŞLARI": ("cashFlow", "operating"),
    "Yatırım Faaliyetlerinden Nakit Akışları": ("cashFlow", "investing"),
    "YATIRIM FAALİYETLERİNDEN NAKİT AKIŞLARI": ("cashFlow", "investing"),
    "Finansman Faaliyetlerinden Nakit Akışları": ("cashFlow", "financing"),
    "FİNANSMAN FAALİYETLERİNDEN NAKİT AKIŞLARI": ("cashFlow", "financing"),
}


def fetch_from_api(ticker, year, financial_group="UFRS"):
    """Tek bir yıl için 4 çeyrek mali tablo verisini API'den çeker.
    Returns list of dicts with keys: itemCode, itemDescTr, itemDescEng, and 4 value keys."""
    params = {
        "companyCode": ticker,
        "exchange": "TRY",
        "financialGroup": financial_group,
        "year1": year,
        "period1": 3,
        "year2": year,
        "period2": 6,
        "year3": year,
        "period3": 9,
        "year4": year,
        "period4": 12,
    }
    try:
        resp = requests.get(API_URL, params=params, timeout=15, verify=True)
        resp.raise_for_status()
        data = resp.json()
        raw_rows = data.get("value", [])
        if not raw_rows:
            return None

        # API yanıtını normalize et: ilk 3 key metadata, sonraki 4 key değerler
        normalized = []
        for row in raw_rows:
            keys = list(row.keys())
            if len(keys) < 4:
                continue

            # İlk 3 sütun: itemCode, itemDescTr, itemDescEng
            item_code = str(row[keys[0]]).strip() if len(keys) > 0 else ""
            desc_tr = str(row[keys[1]]).strip() if len(keys) > 1 else ""
            desc_eng = str(row[keys[2]]).strip() if len(keys) > 2 else ""

            # Sonraki 4 sütun: çeyrek değerler (Q1, Q2, Q3, Q4)
            values = []
            for k in keys[3:7]:
                v = row.get(k, 0)
                try:
                    values.append(float(v) if v is not None and str(v) not in ("nan", "None", "") else 0)
                except (ValueError, TypeError):
                    values.append(0)

            # 4'ten az değer varsa sıfırla tamamla
            while len(values) < 4:
                values.append(0)

            normalized.append({
                "itemCode": item_code,
                "itemDescTr": desc_tr,
                "itemDescEng": desc_eng,
                "values": values,  # [Q1, Q2, Q3, Q4]
            })

        return normalized
    except Exception as e:
        print(f"    API hatası ({ticker}, {year}, {financial_group}): {str(e)[:80]}")
        return None


def fetch_financial_data(ticker):
    """Bir hisse için tüm mali tablo verilerini çeker ve JSON formatına dönüştürür."""
    all_rows = {}  # itemCode -> {periods...}
    all_periods = []

    # Son 3 yılın verilerini çek (UFRS)
    for year in range(CURRENT_YEAR - 2, CURRENT_YEAR + 1):
        rows = fetch_from_api(ticker, year, "UFRS")

        # UFRS başarısız olursa UFRS_K dene
        if rows is None or len(rows) == 0:
            rows = fetch_from_api(ticker, year, "UFRS_K")

        if rows is None or len(rows) == 0:
            # Bu yıl için veri yok, boş dönemler ekle
            for q in [3, 6, 9, 12]:
                all_periods.append(f"{year}/{q}")
            continue

        year_periods = [f"{year}/{q}" for q in [3, 6, 9, 12]]
        all_periods.extend(year_periods)

        for row in rows:
            code = row["itemCode"]
            desc_tr = row["itemDescTr"]
            desc_eng = row["itemDescEng"]

            if code not in all_rows:
                all_rows[code] = {"descTr": desc_tr, "descEng": desc_eng, "values": {}}

            # Değerleri al (sıralı: Q1=3, Q2=6, Q3=9, Q4=12)
            for i, period in enumerate(year_periods):
                all_rows[code]["values"][period] = row["values"][i]

    if not all_rows:
        return None

    # Dönemleri sırala ve son 8 dönemi al
    all_periods = sorted(set(all_periods))
    # Sadece veri olan dönemleri tut
    valid_periods = []
    for p in all_periods:
        has_data = any(
            row["values"].get(p) is not None and row["values"].get(p) != 0
            for row in all_rows.values()
        )
        if has_data:
            valid_periods.append(p)
    periods = valid_periods[-8:] if len(valid_periods) > 8 else valid_periods

    if not periods:
        periods = all_periods[-8:] if len(all_periods) > 8 else all_periods

    # Sonuç yapısı
    result = {
        "ticker": ticker,
        "currency": "TRY",
        "periods": periods,
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

    found = {}  # field_name -> [values]

    # Debug: item kodlarını logla (sadece DEBUG_FINANCIALS=ticker veya "1" ise ilk çağrıda)
    debug_target = os.environ.get("DEBUG_FINANCIALS", "")
    if debug_target and (debug_target == ticker or debug_target == "1"):
        print(f"    [{ticker}] API'den gelen {len(all_rows)} kalem:")
        for code, rd in all_rows.items():
            print(f"      {code}: {rd['descTr']}")
        if debug_target == "1":
            os.environ["DEBUG_FINANCIALS"] = ""  # Sadece ilk hisse

    for code, row_data in all_rows.items():
        desc_tr = row_data["descTr"]

        # Önce itemCode ile eşleştir
        mapping = ITEM_CODE_MAP.get(code)

        # itemCode bulunamazsa açıklama ile eşleştir
        if not mapping:
            for pattern, m in ITEM_DESC_MAP.items():
                if pattern.lower() == desc_tr.lower():
                    mapping = m
                    break

        # Hala bulunamazsa kısmi eşleşme dene
        if not mapping:
            desc_lower = desc_tr.lower()
            for pattern, m in ITEM_DESC_MAP.items():
                if pattern.lower() in desc_lower:
                    field_key = f"{m[0]}.{m[1]}"
                    if field_key not in found:
                        mapping = m
                    break

        if not mapping:
            continue

        section, field = mapping
        field_key = f"{section}.{field}"

        # İlk eşleşmeyi al (daha spesifik kalemler önce gelir)
        if field_key in found:
            continue

        values = []
        for p in periods:
            val = row_data["values"].get(p, 0)
            try:
                values.append(float(val) if val is not None and str(val) not in ("nan", "None", "") else 0)
            except (ValueError, TypeError):
                values.append(0)

        found[field_key] = values
        result[section][field] = values

    # Eksik alanları sıfırlarla doldur
    for section in ["balanceSheet", "incomeStatement", "cashFlow"]:
        for field in result[section]:
            if not result[section][field]:
                result[section][field] = [0] * len(periods)

    # totalLiabilities hesapla eğer yoksa
    if all(v == 0 for v in result["balanceSheet"]["totalLiabilities"]):
        cl = result["balanceSheet"]["currentLiabilities"]
        ncl = result["balanceSheet"]["nonCurrentLiabilities"]
        if any(v != 0 for v in cl) or any(v != 0 for v in ncl):
            result["balanceSheet"]["totalLiabilities"] = [
                cl[i] + ncl[i] for i in range(len(periods))
            ]

    # totalAssets hesapla eğer yoksa
    if all(v == 0 for v in result["balanceSheet"]["totalAssets"]):
        ca = result["balanceSheet"]["currentAssets"]
        nca = result["balanceSheet"]["nonCurrentAssets"]
        if any(v != 0 for v in ca) or any(v != 0 for v in nca):
            result["balanceSheet"]["totalAssets"] = [
                ca[i] + nca[i] for i in range(len(periods))
            ]

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

    success = 0
    fail = 0

    for i, ticker in enumerate(tickers):
        print(f"  [{i + 1}/{len(tickers)}] {ticker}...", end="")
        data = fetch_financial_data(ticker)

        if data:
            # Veri kalitesini kontrol et
            rev = data["incomeStatement"]["revenue"]
            has_revenue = any(v != 0 for v in rev)
            ni = data["incomeStatement"]["netIncome"]
            has_income = any(v != 0 for v in ni)

            save_financial_data(ticker, data)
            success += 1
            status = "OK"
            if has_revenue:
                status += f" (gelir: {len([v for v in rev if v != 0])} dönem)"
            print(f" {status}")
        else:
            fail += 1
            print(" HATA")

        time.sleep(0.3)

    print(f"\nTamamlandı: {success} başarılı, {fail} başarısız")
