"""
Finansal tablolardan kapsamlı rasyoları hesaplar ve şirket detay JSON'larını günceller.

Hesaplanan rasyolar:
- Değerleme: F/K, PD/DD, F/S, FD/FAVÖK, PEG, HBK (TTM bazlı)
- Karlılık: ROE (TTM), ROA (TTM), Brüt Marj, FAVÖK Marjı, Esas Faaliyet Kar Marjı, Net Kar Marjı
- Likidite: Cari Oran, Likidite (Asit-Test) Oranı, Nakit Oran
- Kaldıraç: Borç/Özkaynak, Kaldıraç Oranı, Finansal Borç Oranı, Net Borç/FAVÖK
- Faaliyet Etkinlik: Aktif, Stok, Alacak, Borç, Özkaynak Devir Hızı
- Büyüme: Gelir, FAVÖK, Net Kar, Özkaynak (YoY ve QoQ)
- Karne: Karlılık (0-6), Büyüme (0-6), Borçluluk (0-6), Toplam (0-18)
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
FINANCIALS_DIR = os.path.join(DATA_DIR, "financials")
COMPANIES_DIR = os.path.join(DATA_DIR, "companies")


def _safe_div(a, b):
    """Güvenli bölme — sıfıra bölme ve None kontrolü."""
    if b is None or a is None or b == 0:
        return None
    return a / b


def _r(val, decimals=2):
    """Güvenli yuvarlama."""
    if val is None:
        return None
    return round(val, decimals)


def _get_detailed_values(detailed_list, code):
    """Detailed bilanço/gelir tablosundan belirli bir kodu çeker."""
    if not detailed_list:
        return None
    for item in detailed_list:
        if item.get("code") == code:
            return item.get("values")
    return None


def _extract_single_quarters(cumulative_values, periods):
    """
    Kümülatif gelir tablosu değerlerinden tek çeyrek değerleri çıkarır.

    Gelir tablosu verileri kümülatif (YTD):
    /3 = Q1, /6 = H1, /9 = 9M, /12 = Yıllık

    Tek çeyrek:
    Q1 (/3) = değer
    Q2 = /6 - /3
    Q3 = /9 - /6
    Q4 = /12 - /9
    """
    if not cumulative_values or not periods:
        return None

    n = len(cumulative_values)
    result = [None] * n

    for i in range(n):
        val = cumulative_values[i]
        if val is None:
            continue

        period = periods[i] if i < len(periods) else ""
        month = period.split("/")[-1] if "/" in period else ""

        if month == "3":
            # Q1: zaten tek çeyrek
            result[i] = val
        elif month in ("6", "9", "12") and i > 0 and cumulative_values[i - 1] is not None:
            # Önceki dönem aynı yılın önceki çeyreği mi kontrol et
            prev_period = periods[i - 1] if i - 1 < len(periods) else ""
            prev_year = prev_period.split("/")[0] if "/" in prev_period else ""
            curr_year = period.split("/")[0] if "/" in period else ""

            if prev_year == curr_year:
                result[i] = val - cumulative_values[i - 1]
            else:
                # Farklı yıl - kümülatif çıkarma güvenli değil
                if month == "3":
                    result[i] = val
                else:
                    result[i] = None
        elif month == "3":
            result[i] = val
        else:
            result[i] = None

    return result


def _calc_ttm(single_quarter_values, idx):
    """
    Son 4 çeyreğin toplamını hesaplar (Trailing Twelve Months).
    idx: en son çeyreğin indeksi.
    """
    if not single_quarter_values or idx < 3:
        return None

    vals = [single_quarter_values[idx - j] for j in range(4)]
    if any(v is None for v in vals):
        return None

    return sum(vals)


def calculate_quarterly_ratios(financials, market_cap):
    """
    Tüm dönemler için çeyreklik rasyoları hesaplar.
    Returns: dict with quarterlyRatios (list) and summary ratios.
    """
    periods = financials.get("periods", [])
    bs = financials.get("balanceSheet", {})
    inc = financials.get("incomeStatement", {})
    cf = financials.get("cashFlow", {})
    detailed = financials.get("detailed", {})
    detailed_bs = detailed.get("balanceSheet", [])
    detailed_inc = detailed.get("incomeStatement", [])

    n = len(periods)
    if n == 0:
        return None

    # --- Bilanço verileri (dönem sonu, kümülatif değil) ---
    equity = bs.get("equity", [])
    total_assets = bs.get("totalAssets", [])
    current_assets = bs.get("currentAssets", [])
    current_liabilities = bs.get("currentLiabilities", [])
    non_current_liabilities = bs.get("nonCurrentLiabilities", [])
    total_liabilities = bs.get("totalLiabilities", [])

    # Detailed bilanço kalemleri
    cash = _get_detailed_values(detailed_bs, "1AA") or [None] * n  # Nakit
    inventories = _get_detailed_values(detailed_bs, "1AF") or [None] * n  # Stoklar
    trade_receivables = _get_detailed_values(detailed_bs, "1AC") or [None] * n  # Ticari Alacaklar
    short_term_debt = _get_detailed_values(detailed_bs, "2AA") or [None] * n  # Kısa Vadeli Fin. Borç
    long_term_debt = _get_detailed_values(detailed_bs, "2BA") or [None] * n  # Uzun Vadeli Fin. Borç
    trade_payables = _get_detailed_values(detailed_bs, "2AAGAA") or [None] * n  # Ticari Borçlar
    paid_capital = _get_detailed_values(detailed_bs, "2OA") or [None] * n  # Ödenmiş Sermaye

    # --- Gelir tablosu verileri (KÜMÜLATİF - tek çeyreğe çevir) ---
    revenue_cum = inc.get("revenue", [])
    cost_of_revenue_cum = inc.get("costOfRevenue", [])
    gross_profit_cum = inc.get("grossProfit", [])
    operating_income_cum = inc.get("operatingIncome", [])
    net_income_cum = inc.get("netIncome", [])
    ebitda_cum = inc.get("ebitda", [])

    # Detailed gelir tablosu kalemleri (KÜMÜLATİF)
    financial_income_cum = _get_detailed_values(detailed_inc, "3HB") or [None] * n
    financial_expense_cum = _get_detailed_values(detailed_inc, "3HC") or [None] * n

    # Tek çeyreğe çevir
    revenue_q = _extract_single_quarters(revenue_cum, periods) or [None] * n
    gross_profit_q = _extract_single_quarters(gross_profit_cum, periods) or [None] * n
    operating_income_q = _extract_single_quarters(operating_income_cum, periods) or [None] * n
    net_income_q = _extract_single_quarters(net_income_cum, periods) or [None] * n
    ebitda_q = _extract_single_quarters(ebitda_cum, periods) or [None] * n
    financial_expense_q = _extract_single_quarters(financial_expense_cum, periods) or [None] * n

    # Nakit akış (zaten kümülatif - tek çeyreğe çevir)
    operating_cf_q = _extract_single_quarters(cf.get("operating", []), periods) or [None] * n
    investing_cf_q = _extract_single_quarters(cf.get("investing", []), periods) or [None] * n

    # --- Her dönem için rasyoları hesapla ---
    quarterly_ratios = []

    for i in range(n):
        period = periods[i] if i < len(periods) else ""
        q = {"period": period}

        # Bilanço değerleri (nokta değerleri)
        eq = equity[i] if i < len(equity) else None
        ta = total_assets[i] if i < len(total_assets) else None
        ca = current_assets[i] if i < len(current_assets) else None
        cl = current_liabilities[i] if i < len(current_liabilities) else None
        ncl = non_current_liabilities[i] if i < len(non_current_liabilities) else None
        tl = total_liabilities[i] if i < len(total_liabilities) else None

        ca_val = cash[i] if i < len(cash) else None
        inv = inventories[i] if i < len(inventories) else None
        tr = trade_receivables[i] if i < len(trade_receivables) else None
        std = short_term_debt[i] if i < len(short_term_debt) else None
        ltd = long_term_debt[i] if i < len(long_term_debt) else None
        tp = trade_payables[i] if i < len(trade_payables) else None
        pc = paid_capital[i] if i < len(paid_capital) else None

        # Tek çeyrek gelir tablosu
        rev = revenue_q[i]
        gp = gross_profit_q[i]
        oi = operating_income_q[i]
        ni = net_income_q[i]
        ebt = ebitda_q[i]
        fin_exp = financial_expense_q[i]

        # Nakit akış tek çeyrek
        ocf = operating_cf_q[i]
        icf = investing_cf_q[i]

        # TTM hesaplamaları (son 4 çeyrek toplamı)
        rev_ttm = _calc_ttm(revenue_q, i)  # TTM
        ni_ttm = _calc_ttm(net_income_q, i)  # TTM
        ebitda_ttm = _calc_ttm(ebitda_q, i)  # TTM
        gp_ttm = _calc_ttm(gross_profit_q, i)  # TTM
        oi_ttm = _calc_ttm(operating_income_q, i)  # TTM
        ocf_ttm = _calc_ttm(operating_cf_q, i)  # TTM
        icf_ttm = _calc_ttm(investing_cf_q, i)  # TTM

        # ========== KARLILIK (tek çeyrek marjlar) ==========
        q["brutKarMarji"] = _r(_safe_div(gp, rev) and (gp / rev * 100) if rev and rev != 0 and gp is not None else None)
        q["favokMarji"] = _r(_safe_div(ebt, rev) and (ebt / rev * 100) if rev and rev != 0 and ebt is not None else None)
        q["esasFaaliyetKarMarji"] = _r((oi / rev * 100) if rev and rev != 0 and oi is not None else None)
        q["netKarMarji"] = _r((ni / rev * 100) if rev and rev != 0 and ni is not None else None)

        # ROE, ROA — TTM bazlı
        q["roe"] = _r((ni_ttm / eq * 100) if ni_ttm is not None and eq and eq > 0 else None)  # TTM
        q["roa"] = _r((ni_ttm / ta * 100) if ni_ttm is not None and ta and ta > 0 else None)  # TTM

        # HBK (Hisse Başı Kar) — TTM bazlı
        q["hisseBasiKar"] = _r((ni_ttm / pc) if ni_ttm is not None and pc and pc > 0 else None, 4)  # TTM

        # ========== LİKİDİTE ==========
        q["cariOran"] = _r(_safe_div(ca, cl))
        # Likidite (Asit-Test) Oranı = (Dönen Varlıklar - Stoklar) / Kısa Vadeli Yükümlülükler
        if ca is not None and inv is not None and cl and cl > 0:
            q["likiditeOrani"] = _r((ca - inv) / cl)
        else:
            q["likiditeOrani"] = None
        # Nakit Oran = Nakit / Kısa Vadeli Yükümlülükler
        q["nakitOran"] = _r(_safe_div(ca_val, cl))

        # ========== KALDIRAC ==========
        q["borcOzkaynak"] = _r(_safe_div(tl, eq))
        # Kaldıraç Oranı = Toplam Borç / Toplam Aktif
        q["kaldiracOrani"] = _r(_safe_div(tl, ta))
        # Finansal Borç Oranı = (Kısa Vadeli + Uzun Vadeli Fin. Borç) / Toplam Aktif
        if std is not None and ltd is not None and ta and ta > 0:
            q["finansalBorcOrani"] = _r((std + ltd) / ta)
        else:
            q["finansalBorcOrani"] = None
        # Net Borç / FAVÖK (TTM)
        if std is not None and ltd is not None and ca_val is not None and ebitda_ttm and ebitda_ttm > 0:
            net_debt = std + ltd - ca_val
            q["netBorcFavok"] = _r(net_debt / ebitda_ttm)  # TTM
        else:
            q["netBorcFavok"] = None

        # ========== FAALİYET ETKİNLİK (TTM bazlı) ==========
        q["aktifDevirHizi"] = _r(_safe_div(rev_ttm, ta))  # TTM
        if inv is not None and inv > 0 and rev_ttm and rev_ttm > 0:
            q["stokDevirHizi"] = _r(rev_ttm / inv)  # TTM
        else:
            q["stokDevirHizi"] = None
        if tr is not None and tr > 0 and rev_ttm and rev_ttm > 0:
            q["alacakDevirHizi"] = _r(rev_ttm / tr)  # TTM
        else:
            q["alacakDevirHizi"] = None
        if tp is not None and tp > 0 and rev_ttm and rev_ttm > 0:
            q["borcDevirHizi"] = _r(rev_ttm / tp)  # TTM
        else:
            q["borcDevirHizi"] = None
        q["ozkaynakDevirHizi"] = _r(_safe_div(rev_ttm, eq))  # TTM

        # ========== BÜYÜME (YoY — 4 çeyrek öncesiyle kıyasla) ==========
        if i >= 4:
            prev_rev = revenue_q[i - 4]
            prev_ni = net_income_q[i - 4]
            prev_ebitda = ebitda_q[i - 4]
            prev_eq = equity[i - 4] if i - 4 < len(equity) else None

            q["gelirBuyumeYoy"] = _r(((rev - prev_rev) / abs(prev_rev) * 100) if rev is not None and prev_rev and prev_rev != 0 else None)
            q["netKarBuyumeYoy"] = _r(((ni - prev_ni) / abs(prev_ni) * 100) if ni is not None and prev_ni and prev_ni != 0 else None)
            q["favokBuyumeYoy"] = _r(((ebt - prev_ebitda) / abs(prev_ebitda) * 100) if ebt is not None and prev_ebitda and prev_ebitda != 0 else None)
            q["ozkaynakBuyumeYoy"] = _r(((eq - prev_eq) / abs(prev_eq) * 100) if eq is not None and prev_eq and prev_eq != 0 else None)
        else:
            q["gelirBuyumeYoy"] = None
            q["netKarBuyumeYoy"] = None
            q["favokBuyumeYoy"] = None
            q["ozkaynakBuyumeYoy"] = None

        # ========== BÜYÜME (QoQ — önceki çeyrekle kıyasla) ==========
        if i >= 1:
            prev_rev_q = revenue_q[i - 1]
            prev_ni_q = net_income_q[i - 1]
            prev_ebitda_q = ebitda_q[i - 1]

            q["gelirBuyumeQoq"] = _r(((rev - prev_rev_q) / abs(prev_rev_q) * 100) if rev is not None and prev_rev_q and prev_rev_q != 0 else None)
            q["netKarBuyumeQoq"] = _r(((ni - prev_ni_q) / abs(prev_ni_q) * 100) if ni is not None and prev_ni_q and prev_ni_q != 0 else None)
            q["favokBuyumeQoq"] = _r(((ebt - prev_ebitda_q) / abs(prev_ebitda_q) * 100) if ebt is not None and prev_ebitda_q and prev_ebitda_q != 0 else None)
        else:
            q["gelirBuyumeQoq"] = None
            q["netKarBuyumeQoq"] = None
            q["favokBuyumeQoq"] = None

        # ========== DEĞERLEME (sadece son dönem — market_cap gerekli) ==========
        # Bu değerler sadece son dönem için anlamlı, diğerlerinde None
        if i == n - 1 and market_cap and market_cap > 0:
            # F/K — TTM
            q["fk"] = _r(_safe_div(market_cap, ni_ttm)) if ni_ttm and ni_ttm > 0 else None  # TTM
            # PD/DD
            q["pddd"] = _r(_safe_div(market_cap, eq)) if eq and eq > 0 else None
            # F/S — TTM
            q["fs"] = _r(_safe_div(market_cap, rev_ttm)) if rev_ttm and rev_ttm > 0 else None  # TTM
            # FD/FAVÖK — TTM
            if std is not None and ltd is not None and ca_val is not None and ebitda_ttm and ebitda_ttm > 0:
                net_debt = (std + ltd) - ca_val
                firm_value = market_cap + net_debt
                q["fdFavok"] = _r(firm_value / ebitda_ttm)  # TTM
            else:
                q["fdFavok"] = None
            # Serbest Nakit Akış Verimi
            if ocf_ttm is not None and icf_ttm is not None:
                fcf = ocf_ttm + icf_ttm  # investing negatif gelir
                q["serbestNakitAkisVerimi"] = _r((fcf / market_cap * 100) if market_cap > 0 else None)
            else:
                q["serbestNakitAkisVerimi"] = None
        else:
            q["fk"] = None
            q["pddd"] = None
            q["fs"] = None
            q["fdFavok"] = None
            q["serbestNakitAkisVerimi"] = None

        # Tek çeyrek ham değerler (grafikler için)
        q["gelir"] = rev
        q["brutKar"] = gp
        q["favok"] = ebt
        q["esasFaaliyetKari"] = oi
        q["netKar"] = ni
        q["isletmeNakitAkisi"] = ocf
        q["yatirimNakitAkisi"] = icf
        q["serbestNakitAkis"] = (ocf + icf) if ocf is not None and icf is not None else None

        quarterly_ratios.append(q)

    return quarterly_ratios


def calculate_karne(quarterly_ratios):
    """
    Karne (scorecard) hesaplar — son dönem verilerine göre.
    Karlılık (0-6), Büyüme (0-6), Borçluluk (0-6), Toplam (0-18).
    """
    if not quarterly_ratios or len(quarterly_ratios) < 2:
        return None

    last = quarterly_ratios[-1]
    prev = quarterly_ratios[-2]

    # Daha eski dönem (4 çeyrek önce)
    prev_year = quarterly_ratios[-5] if len(quarterly_ratios) >= 5 else None

    # ====== KARLILIK (0-6) ======
    karlilik = 0

    # 1: Brüt kar marjı pozitif mi?
    if last.get("brutKarMarji") is not None and last["brutKarMarji"] > 0:
        karlilik += 1

    # 2: Net kar marjı pozitif mi?
    if last.get("netKarMarji") is not None and last["netKarMarji"] > 0:
        karlilik += 1

    # 3: ROE > 0? (TTM)
    if last.get("roe") is not None and last["roe"] > 0:
        karlilik += 1

    # 4: Brüt kar marjı QoQ artış (bps)
    if (last.get("brutKarMarji") is not None and prev.get("brutKarMarji") is not None
            and last["brutKarMarji"] > prev["brutKarMarji"]):
        karlilik += 1

    # 5: Net kar marjı QoQ artış (bps)
    if (last.get("netKarMarji") is not None and prev.get("netKarMarji") is not None
            and last["netKarMarji"] > prev["netKarMarji"]):
        karlilik += 1

    # 6: İşletme nakit akışı pozitif mi? (tek çeyrek)
    if last.get("isletmeNakitAkisi") is not None and last["isletmeNakitAkisi"] > 0:
        karlilik += 1

    # ====== BÜYÜME (0-6) ======
    buyume = 0

    # 1: Gelir YoY büyüme pozitif mi?
    if last.get("gelirBuyumeYoy") is not None and last["gelirBuyumeYoy"] > 0:
        buyume += 1

    # 2: Net kar YoY büyüme pozitif mi?
    if last.get("netKarBuyumeYoy") is not None and last["netKarBuyumeYoy"] > 0:
        buyume += 1

    # 3: FAVÖK YoY büyüme pozitif mi?
    if last.get("favokBuyumeYoy") is not None and last["favokBuyumeYoy"] > 0:
        buyume += 1

    # 4: Gelir QoQ büyüme pozitif mi?
    if last.get("gelirBuyumeQoq") is not None and last["gelirBuyumeQoq"] > 0:
        buyume += 1

    # 5: Özkaynak YoY büyüme pozitif mi?
    if last.get("ozkaynakBuyumeYoy") is not None and last["ozkaynakBuyumeYoy"] > 0:
        buyume += 1

    # 6: Net kar QoQ büyüme pozitif mi?
    if last.get("netKarBuyumeQoq") is not None and last["netKarBuyumeQoq"] > 0:
        buyume += 1

    # ====== BORÇLULUK (0-6) ======
    borcluluk = 0

    # 1: Cari oran > 1?
    if last.get("cariOran") is not None and last["cariOran"] > 1:
        borcluluk += 1

    # 2: Kaldıraç oranı < 0.6?
    if last.get("kaldiracOrani") is not None and last["kaldiracOrani"] < 0.6:
        borcluluk += 1

    # 3: Net borç/FAVÖK < 3? (TTM)
    if last.get("netBorcFavok") is not None and last["netBorcFavok"] < 3:
        borcluluk += 1

    # 4: Cari oran QoQ iyileşme
    if (last.get("cariOran") is not None and prev.get("cariOran") is not None
            and last["cariOran"] > prev["cariOran"]):
        borcluluk += 1

    # 5: Finansal borç oranı < 0.3?
    if last.get("finansalBorcOrani") is not None and last["finansalBorcOrani"] < 0.3:
        borcluluk += 1

    # 6: abs(net finansal gider) / gelir < %10?
    last_fin_exp = last.get("_netFinansalGider")  # dahili kullanım
    last_rev = last.get("gelir")
    if last_fin_exp is not None and last_rev and last_rev > 0:
        if abs(last_fin_exp) / last_rev < 0.10:
            borcluluk += 1

    toplam = karlilik + buyume + borcluluk

    return {
        "karlilik": karlilik,
        "buyume": buyume,
        "borcluluk": borcluluk,
        "toplam": toplam
    }


def calculate_ratios(financials, market_cap):
    """
    Ana rasyo hesaplama fonksiyonu.
    Hem çeyreklik rasyolar hem de özet (son dönem) rasyolar üretir.
    """
    periods = financials.get("periods", [])
    if not periods:
        return {"ratios": {}, "quarterlyRatios": [], "karne": None}

    # Çeyreklik rasyoları hesapla
    quarterly = calculate_quarterly_ratios(financials, market_cap)
    if not quarterly:
        return {"ratios": {}, "quarterlyRatios": [], "karne": None}

    # Net finansal gider bilgisi karne için (dahili, JSON'a yazılmaz)
    detailed_inc = financials.get("detailed", {}).get("incomeStatement", [])
    fin_exp_cum = _get_detailed_values(detailed_inc, "3HC") or []
    fin_exp_q = _extract_single_quarters(fin_exp_cum, periods) or []
    if quarterly and fin_exp_q:
        for i, q in enumerate(quarterly):
            q["_netFinansalGider"] = fin_exp_q[i] if i < len(fin_exp_q) else None

    # Karne hesapla
    karne = calculate_karne(quarterly)

    # Dahili alanları temizle
    for q in quarterly:
        q.pop("_netFinansalGider", None)

    # Son dönem rasyolarını özet olarak çıkar (mevcut yapıyla uyumluluk)
    last = quarterly[-1] if quarterly else {}

    ratios = {
        "pe": last.get("fk"),
        "pb": last.get("pddd"),
        "ps": last.get("fs"),
        "evEbitda": last.get("fdFavok"),
        "roe": last.get("roe"),
        "roa": last.get("roa"),
        "netMargin": last.get("netKarMarji"),
        "grossMargin": last.get("brutKarMarji"),
        "ebitdaMargin": last.get("favokMarji"),
        "currentRatio": last.get("cariOran"),
        "quickRatio": last.get("likiditeOrani"),
        "cashRatio": last.get("nakitOran"),
        "debtEquity": last.get("borcOzkaynak"),
        "leverageRatio": last.get("kaldiracOrani"),
        "financialDebtRatio": last.get("finansalBorcOrani"),
        "netDebtEbitda": last.get("netBorcFavok"),
        "revenueGrowthYoy": last.get("gelirBuyumeYoy"),
        "netIncomeGrowthYoy": last.get("netKarBuyumeYoy"),
        "ebitdaGrowthYoy": last.get("favokBuyumeYoy"),
        "equityGrowthYoy": last.get("ozkaynakBuyumeYoy"),
        "earningsPerShare": last.get("hisseBasiKar"),
        "freeCashFlowYield": last.get("serbestNakitAkisVerimi"),
    }

    return {
        "ratios": ratios,
        "quarterlyRatios": quarterly,
        "karne": karne
    }


def calculate_sector_averages(stocks_data):
    """Sektör ortalamalarını hesaplar."""
    sector_map = {}

    for stock in stocks_data.get("stocks", []):
        sector = stock.get("sector", "Diğer")
        if sector not in sector_map:
            sector_map[sector] = {
                "pe": [], "pb": [], "roe": [], "evEbitda": [],
                "currentRatio": [], "netMargin": [],
                "changes": [], "count": 0
            }

        sector_map[sector]["count"] += 1
        for key in ["pe", "pb", "roe", "evEbitda", "currentRatio", "netMargin"]:
            val = stock.get(key)
            if val is not None:
                sector_map[sector][key].append(val)
        sector_map[sector]["changes"].append(stock.get("changePercent", 0))

    sectors = []
    for name, data in sector_map.items():
        slug = name.lower()
        for tr_char, en_char in [("ı", "i"), ("ö", "o"), ("ü", "u"), ("ş", "s"), ("ç", "c"), ("ğ", "g")]:
            slug = slug.replace(tr_char, en_char)
        slug = slug.replace(" ", "-")

        sector = {
            "slug": slug,
            "name": name,
            "stockCount": data["count"],
            "performance": _r(sum(data["changes"]) / len(data["changes"])) if data["changes"] else 0,
        }

        for key in ["pe", "pb", "roe", "evEbitda", "currentRatio", "netMargin"]:
            avg_key = f"avg{key[0].upper()}{key[1:]}"
            vals = data[key]
            sector[avg_key] = _r(sum(vals) / len(vals)) if vals else None

        sectors.append(sector)

    return sorted(sectors, key=lambda x: x["stockCount"], reverse=True)


if __name__ == "__main__":
    stocks_path = os.path.join(DATA_DIR, "stocks.json")
    if not os.path.exists(stocks_path):
        print("stocks.json bulunamadı.")
        exit(1)

    with open(stocks_path, "r", encoding="utf-8") as f:
        stocks_data = json.load(f)

    print("Kapsamlı rasyolar hesaplanıyor...")

    success = 0
    errors = 0

    for stock in stocks_data.get("stocks", []):
        ticker = stock["ticker"]
        fin_path = os.path.join(FINANCIALS_DIR, f"{ticker}.json")

        if not os.path.exists(fin_path):
            continue

        try:
            with open(fin_path, "r", encoding="utf-8") as f:
                financials = json.load(f)

            result = calculate_ratios(financials, stock.get("marketCap", 0))
            ratios = result["ratios"]

            # Stocks.json'daki hisse bilgilerini güncelle (mevcut yapı uyumluluğu)
            stock["pe"] = ratios.get("pe")
            stock["pb"] = ratios.get("pb")
            stock["roe"] = ratios.get("roe")
            stock["netMargin"] = ratios.get("netMargin")
            stock["evEbitda"] = ratios.get("evEbitda")
            stock["currentRatio"] = ratios.get("currentRatio")

            # Company JSON'ı güncelle
            company_path = os.path.join(COMPANIES_DIR, f"{ticker}.json")
            if os.path.exists(company_path):
                with open(company_path, "r", encoding="utf-8") as f:
                    company = json.load(f)

                company["ratios"] = ratios
                company["quarterlyRatios"] = result["quarterlyRatios"]
                company["karne"] = result["karne"]

                with open(company_path, "w", encoding="utf-8") as f:
                    json.dump(company, f, ensure_ascii=False, indent=2)

            success += 1
        except Exception as e:
            print(f"  HATA {ticker}: {e}")
            errors += 1

    # stocks.json güncelle
    with open(stocks_path, "w", encoding="utf-8") as f:
        json.dump(stocks_data, f, ensure_ascii=False, indent=2)

    # Sektör ortalamalarını hesapla
    sectors = calculate_sector_averages(stocks_data)
    sectors_path = os.path.join(DATA_DIR, "sectors.json")
    with open(sectors_path, "w", encoding="utf-8") as f:
        json.dump(sectors, f, ensure_ascii=False, indent=2)

    print(f"Tamamlandı: {success} başarılı, {errors} hata, {len(sectors)} sektör güncellendi.")
