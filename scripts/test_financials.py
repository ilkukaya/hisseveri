"""
Mali tablo çekme testi - 10 hisse (bankalar dahil).
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_financials import fetch_financial_data

TEST_TICKERS = [
    "FROTO",   # Otomotiv (XI_29)
    "THYAO",   # Havacılık (XI_29)
    "AKBNK",   # Banka (UFRS)
    "TUPRS",   # Enerji (XI_29)
    "BIMAS",   # Perakende (XI_29)
    "ASELS",   # Savunma (XI_29)
    "EREGL",   # Demir Çelik (XI_29)
    "TCELL",   # Telekom (XI_29)
    "SISE",    # Holding (XI_29)
    "KCHOL",   # Holding (XI_29)
]


def test_ticker(ticker):
    """Tek hisse için test."""
    print(f"\n{'='*70}")
    print(f"  {ticker}")
    print(f"{'='*70}")

    data = fetch_financial_data(ticker)

    if not data:
        print(f"  HATA: Veri çekilemedi!")
        return False

    print(f"  Dönemler: {data['periods']}")
    all_ok = True

    for section_name, section_label, fields in [
        ("balanceSheet", "BİLANÇO", [
            ("currentAssets", "Dönen Varlıklar"),
            ("nonCurrentAssets", "Duran Varlıklar"),
            ("totalAssets", "Toplam Varlıklar"),
            ("currentLiabilities", "Kısa Vadeli Yük."),
            ("nonCurrentLiabilities", "Uzun Vadeli Yük."),
            ("totalLiabilities", "Toplam Yükümlülükler"),
            ("equity", "Özkaynaklar"),
        ]),
        ("incomeStatement", "GELİR TABLOSU", [
            ("revenue", "Hasılat/Satış Gelirleri"),
            ("costOfRevenue", "Satışların Maliyeti"),
            ("grossProfit", "Brüt Kar"),
            ("operatingIncome", "Faaliyet Karı"),
            ("netIncome", "Net Kar"),
            ("ebitda", "FAVÖK"),
        ]),
        ("cashFlow", "NAKİT AKIŞ", [
            ("operating", "İşletme Faaliyetleri"),
            ("investing", "Yatırım Faaliyetleri"),
            ("financing", "Finansman Faaliyetleri"),
        ]),
    ]:
        print(f"\n  {section_label}:")
        for key, label in fields:
            vals = data[section_name][key]
            non_zero = sum(1 for v in vals if v != 0)
            last_val = vals[-1] if vals else 0
            status = "✓" if non_zero > 0 else "✗"
            if key in ("totalAssets", "equity", "revenue", "netIncome") and non_zero == 0:
                all_ok = False
            val_str = f"{last_val/1_000_000:>12,.0f}M" if last_val != 0 else f"{'0':>13s}"
            print(f"    {status} {label:25s} {non_zero}/{len(vals)} dönem  Son: {val_str}")

    print(f"\n  => {'BAŞARILI ✓' if all_ok else 'EKSİK VERİ ✗'}")
    return all_ok


def main():
    print("=" * 70)
    print("  MALİ TABLO ÇEKME TESTİ (XI_29 + UFRS)")
    print("=" * 70)

    results = {}
    for ticker in TEST_TICKERS:
        try:
            results[ticker] = test_ticker(ticker)
        except Exception as e:
            print(f"\n  {ticker}: EXCEPTION - {e}")
            import traceback
            traceback.print_exc()
            results[ticker] = False

    print(f"\n\n{'='*70}")
    print(f"  ÖZET")
    print(f"{'='*70}")
    for ticker, ok in results.items():
        print(f"  {'✓' if ok else '✗'} {ticker}")
    success = sum(1 for v in results.values() if v)
    print(f"\n  Başarılı: {success}/{len(results)}")

    if success < len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
