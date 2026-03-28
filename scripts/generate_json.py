"""
Ana orchestrator script. Tüm veri çekme ve hesaplama scriptlerini sırayla çalıştırır.
Ayrıca piyasa verilerini (BIST100, USD/TRY, EUR/TRY) günceller.
"""

import json
import os
import subprocess
import sys
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(SCRIPTS_DIR), "data")


def run_script(name):
    """Bir Python scriptini çalıştırır."""
    script_path = os.path.join(SCRIPTS_DIR, name)
    print(f"\n{'=' * 50}")
    print(f"Çalıştırılıyor: {name}")
    print(f"{'=' * 50}")

    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr}", file=sys.stderr)

    if result.returncode != 0:
        print(f"HATA: {name} başarısız oldu (exit code: {result.returncode})")
        return False

    return True


def update_market_data():
    """BIST100 endeks ve döviz kurlarını günceller."""
    try:
        from isyatirimhisse import fetch_index_data
        from datetime import timedelta

        end_date = datetime.now().strftime("%d-%m-%Y")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%d-%m-%Y")

        # BIST100 endeks verisi
        df = fetch_index_data(
            indices="XU100",
            start_date=start_date,
            end_date=end_date,
        )

        market = {
            "updatedAt": datetime.now().isoformat(),
            "bist100": {"value": 0, "change": 0, "changePercent": 0},
            "usdTry": {"value": 0, "change": 0, "changePercent": 0},
            "eurTry": {"value": 0, "change": 0, "changePercent": 0},
        }

        if df is not None and not df.empty:
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            val = float(last.iloc[-1]) if len(last) > 0 else 0
            prev_val = float(prev.iloc[-1]) if len(prev) > 0 else val
            change = val - prev_val
            change_pct = (change / prev_val * 100) if prev_val > 0 else 0
            market["bist100"] = {
                "value": round(val, 2),
                "change": round(change, 2),
                "changePercent": round(change_pct, 2),
            }

        market_path = os.path.join(DATA_DIR, "market.json")
        with open(market_path, "w", encoding="utf-8") as f:
            json.dump(market, f, ensure_ascii=False, indent=2)

        print(f"Piyasa verisi güncellendi: BIST100 = {market['bist100']['value']}")

    except Exception as e:
        print(f"Piyasa verisi güncellenemedi: {e}")


def main():
    print("BİST veri güncelleme başlıyor...")

    steps = [
        ("fetch_all_stocks.py", "Hisse listesi çekiliyor"),
        ("fetch_prices.py", "Fiyat verileri çekiliyor"),
        ("fetch_financials.py", "Finansal tablolar çekiliyor"),
        ("calculate_ratios.py", "Rasyolar hesaplanıyor"),
    ]

    for script, description in steps:
        print(f"\n>> {description}...")
        success = run_script(script)
        if not success:
            print(f"UYARI: {script} başarısız oldu, devam ediliyor...")

    # Piyasa verilerini güncelle
    print("\n>> Piyasa verileri güncelleniyor...")
    update_market_data()

    print("\n" + "=" * 50)
    print("Veri güncelleme tamamlandı!")
    print("=" * 50)


if __name__ == "__main__":
    main()
