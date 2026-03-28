"""
10 farklı hisse için UFRS mali tablo çekme testi.
GitHub Actions'da çalıştırılmak üzere tasarlanmıştır.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_financials import fetch_financial_data

# Farklı sektörlerden 10 hisse
TEST_TICKERS = [
    "FROTO",   # Otomotiv
    "THYAO",   # Havacılık
    "AKBNK",   # Bankacılık
    "TUPRS",   # Enerji / Petrol
    "BIMAS",   # Perakende
    "ASELS",   # Savunma / Teknoloji
    "EREGL",   # Demir Çelik
    "TCELL",   # Telekomünikasyon
    "SISE",    # Cam / Holding
    "KCHOL",   # Holding
]


def test_ticker(ticker):
    """Tek hisse için mali tablo testini çalıştır."""
    print(f"\n{'='*60}")
    print(f"  {ticker}")
    print(f"{'='*60}")

    # DEBUG modunu aç - ilk hisse için tüm item kodlarını göster
    if ticker == TEST_TICKERS[0]:
        os.environ["DEBUG_FINANCIALS"] = ticker

    data = fetch_financial_data(ticker)

    if not data:
        print(f"  HATA: Veri çekilemedi!")
        return False

    print(f"  Dönemler: {data['periods']}")
    print(f"  Dönem sayısı: {len(data['periods'])}")

    all_ok = True

    # Bilanço kontrolü
    print(f"\n  BILANÇO:")
    for key, label in [
        ("currentAssets", "Dönen Varlıklar"),
        ("nonCurrentAssets", "Duran Varlıklar"),
        ("totalAssets", "Toplam Varlıklar"),
        ("currentLiabilities", "Kısa Vadeli Yük."),
        ("nonCurrentLiabilities", "Uzun Vadeli Yük."),
        ("totalLiabilities", "Toplam Yükümlülükler"),
        ("equity", "Özkaynaklar"),
    ]:
        vals = data["balanceSheet"][key]
        non_zero = sum(1 for v in vals if v != 0)
        last_val = vals[-1] if vals else 0
        status = "✓" if non_zero > 0 else "✗"
        if non_zero == 0:
            all_ok = False
        # Milyon TL formatında göster
        last_m = f"{last_val/1_000_000:,.0f}M" if last_val != 0 else "0"
        print(f"    {status} {label:25s} {non_zero}/{len(vals)} dönem  Son: {last_m}")

    # Gelir Tablosu kontrolü
    print(f"\n  GELİR TABLOSU:")
    for key, label in [
        ("revenue", "Hasılat"),
        ("costOfRevenue", "Satışların Maliyeti"),
        ("grossProfit", "Brüt Kar"),
        ("operatingIncome", "Faaliyet Karı"),
        ("netIncome", "Net Kar"),
        ("ebitda", "FAVÖK"),
    ]:
        vals = data["incomeStatement"][key]
        non_zero = sum(1 for v in vals if v != 0)
        last_val = vals[-1] if vals else 0
        status = "✓" if non_zero > 0 else "✗"
        if key in ("revenue", "netIncome") and non_zero == 0:
            all_ok = False
        last_m = f"{last_val/1_000_000:,.0f}M" if last_val != 0 else "0"
        print(f"    {status} {label:25s} {non_zero}/{len(vals)} dönem  Son: {last_m}")

    # Nakit Akış kontrolü
    print(f"\n  NAKİT AKIŞ:")
    for key, label in [
        ("operating", "İşletme Faaliyetleri"),
        ("investing", "Yatırım Faaliyetleri"),
        ("financing", "Finansman Faaliyetleri"),
    ]:
        vals = data["cashFlow"][key]
        non_zero = sum(1 for v in vals if v != 0)
        last_val = vals[-1] if vals else 0
        status = "✓" if non_zero > 0 else "✗"
        last_m = f"{last_val/1_000_000:,.0f}M" if last_val != 0 else "0"
        print(f"    {status} {label:25s} {non_zero}/{len(vals)} dönem  Son: {last_m}")

    # Genel sonuç
    print(f"\n  Sonuç: {'BAŞARILI ✓' if all_ok else 'EKSİK VERİ ✗'}")

    # JSON dosyasına kaydet (test çıktısı olarak)
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "financials")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{ticker}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Kaydedildi: data/financials/{ticker}.json")

    return all_ok


def main():
    print("=" * 60)
    print("  UFRS MALİ TABLO ÇEKME TESTİ")
    print(f"  10 farklı sektörden hisse test ediliyor")
    print("=" * 60)

    results = {}
    for ticker in TEST_TICKERS:
        try:
            results[ticker] = test_ticker(ticker)
        except Exception as e:
            print(f"\n  {ticker}: EXCEPTION - {e}")
            results[ticker] = False

    # Özet
    print(f"\n\n{'='*60}")
    print(f"  ÖZET")
    print(f"{'='*60}")
    success = sum(1 for v in results.values() if v)
    fail = sum(1 for v in results.values() if not v)
    for ticker, ok in results.items():
        print(f"  {'✓' if ok else '✗'} {ticker}")
    print(f"\n  Başarılı: {success}/{len(results)}")
    print(f"  Başarısız: {fail}/{len(results)}")

    if fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
