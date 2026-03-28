"""
Ana orchestrator script. Tüm veri çekme ve hesaplama scriptlerini sırayla çalıştırır.
"""

import subprocess
import sys
import os

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))


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

    print("\n" + "=" * 50)
    print("Veri güncelleme tamamlandı!")
    print("=" * 50)


if __name__ == "__main__":
    main()
