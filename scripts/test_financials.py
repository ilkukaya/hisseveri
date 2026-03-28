"""
Mali tablo API debug testi.
Her hisse için tüm financialGroup değerlerini dener ve ham API yanıtını gösterir.
"""

import json
import sys
import requests

API_URL = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo"

TEST_TICKERS = ["FROTO", "THYAO", "AKBNK", "TUPRS", "BIMAS"]

FINANCIAL_GROUPS = ["XI_29", "UFRS", "UFRS_K"]


def test_api_call(ticker, group, year):
    """Tek bir API çağrısı yap ve sonucu göster."""
    params = {
        "companyCode": ticker,
        "exchange": "TRY",
        "financialGroup": group,
        "year1": year, "period1": 3,
        "year2": year, "period2": 6,
        "year3": year, "period3": 9,
        "year4": year, "period4": 12,
    }
    try:
        resp = requests.get(API_URL, params=params, timeout=15)
        print(f"    HTTP {resp.status_code}", end="")

        if resp.status_code != 200:
            print(f" - {resp.text[:200]}")
            return None

        data = resp.json()
        rows = data.get("value", [])
        print(f" - {len(rows)} satır", end="")

        if not rows:
            print()
            return None

        # İlk satırın yapısını göster
        first = rows[0]
        keys = list(first.keys())
        print(f" - Sütunlar: {keys}")

        return rows

    except Exception as e:
        print(f" - HATA: {e}")
        return None


def show_items(rows):
    """API'den gelen kalemleri listele."""
    if not rows:
        return

    keys = list(rows[0].keys())
    # İlk 3 sütun meta, sonraki 4 sütun değerler
    meta_keys = keys[:3]
    val_keys = keys[3:7]

    for row in rows:
        code = str(row.get(meta_keys[0], "")).strip()
        desc_tr = str(row.get(meta_keys[1], "")).strip()
        # Son dönem değeri
        last_val = row.get(val_keys[-1], 0) if val_keys else 0
        try:
            last_val = float(last_val) if last_val else 0
        except (ValueError, TypeError):
            last_val = 0

        val_str = f"{last_val/1_000_000:>12,.0f}M" if last_val != 0 else f"{'0':>13s}"
        print(f"      {code:20s} {desc_tr:45s} {val_str}")


def main():
    print("=" * 100)
    print("  İŞ YATIRIM API - MALİ TABLO DEBUG TESTİ")
    print("=" * 100)

    for ticker in TEST_TICKERS:
        print(f"\n{'='*100}")
        print(f"  {ticker}")
        print(f"{'='*100}")

        for group in FINANCIAL_GROUPS:
            print(f"\n  >> financialGroup = {group}")

            # 2024 ve 2025 dene
            for year in [2024, 2025]:
                print(f"    {year}: ", end="")
                rows = test_api_call(ticker, group, year)

            # İlk veri bulunan grup için kalemleri göster
            rows = test_api_call(ticker, group, 2024)
            if rows:
                print(f"\n    Kalemler ({group}, 2024):")
                show_items(rows)
                break  # İlk çalışan grubu bulduk
        else:
            print(f"\n  UYARI: Hiçbir financialGroup {ticker} için veri döndürmedi!")

    # Özel test: FROTO için tüm olası grup değerlerini dene
    print(f"\n\n{'='*100}")
    print(f"  FROTO - TÜM GRUP DEĞERLERİ TESTİ")
    print(f"{'='*100}")
    extra_groups = ["XI_29", "XI_30", "UFRS", "UFRS_K",
                    "SOLO", "KONSOL", "1", "2", "3"]
    for group in extra_groups:
        print(f"\n  financialGroup={group}: ", end="")
        test_api_call("FROTO", group, 2024)


if __name__ == "__main__":
    main()
