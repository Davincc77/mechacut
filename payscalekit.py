# -*- coding: utf-8 -*-
"""payscalekit — /money/payscale: SALAIRE↔HEURE avec le dénominateur
NOMMÉ. La loi publie ses constantes ; les gens divisent de mémoire.

THE WOUND (threads lus AU SOURCE 2026-11-26, ancrage rechargé depuis
b118): r/ATC 17sefrt — l'employé est « 20 cents off » de son bulletin
de paie et le fil nomme la cause : « you're dividing your salary by
2080… a common mistake. Our hourly rate is based on 2087 ». r/fednews
1bpysai — « gross × 26 ne tombe pas sur le salaire annuel ; payroll
-directed to OPM : salary divided by 2087 then multiplied by 80 ».
1fnk3cb publie LA DÉRIVATION (quatre années à 262 jours = 2 096 h,
dix-sept à 261 = 2 088, sept à 260 = 2 080 — la moyenne du cycle).
18zjamp cite OPM au mot près sur l'ARRONDI : « nearest cent, counting
one-half cent and over as the next higher cent — $18.845 → $18.85 ».
r/AskHR 1y0ey31 : l'employeur arrondit LE TAUX (xx.37) puis ×80 —
« $8 de moins par an » : le JUMEAU exact de la guerre du prorata
b119, deux ordres, même mot. r/IRS_Source 1qh5ouz : « every 11 years
a calendar year contains 27 pay periods » — le piège du bihebdo.
r/personalfinance 1de8205 publié : 80 000 ÷ 2 080 = 38,46 ÷ 2 096 =
38,17 ÷ 1 880 = 42,55 — 20 % d'écart, « les avis divergent au
bureau ». 3r0eti : l'employeur divisait par 365 — 13,35 $/h au lieu
de 24,03 $, préjudice chiffré dans un fil.

CLOSED SETS, each member cited — the machine NAMES, never picks in
silence (5 USC 5504(b)/5505 read at Cornell 2026-11-26, exact words
of the rounding rule included):

  basis: "fed2087"     5 U.S.C. §5504(b): « divide the annual rate
                       by 2,087 » — hourly = annual/2087.
        "priv2080"     40h × 52 weeks — the private-sector « typical »
                       (r/Payroll 1pp94j9: every comment says it,
                       none says it in the tool).
        "workdays"     REAL weekdays of YOUR year argument × 8 —
                       2026 → 261 → 2 088; 2024 → 262 → 2 096; 2023 →
                       260 → 2 080 (the 1fnk3cb derivation, calendar
                       arithmetic, zero fetch).
        "pto"          2 080 MINUS an hours argument (the 1 880
                       reading of 1de8205) — holidays/PTO are an
                       ARGUMENT, local law is never encoded.
  order: "rate_first"  round the HOURLY to cents first, then ×40/×80
                       — the statute's own sequence AND the r/AskHR
                       employer; OPM rounding = ROUND_HALF_UP, its
                       $18.845 → $18.85 example is a test vector.
        "direct"       annual / period-count, rounded at the END —
                       the employee's check (« ×26 should match »).
  compare=true         all published bases side by side with signed
                       deltas. NO silent average, ever.

Biweekly "direct" = annual/26 and semimonthly = annual/24 are
PUBLISHED CONVENTIONS (1qh5ouz, the queue anchor 2000.00 vs
2166.67 on 52 000) — only §5504(b) and §5505 are cited as law.
The paydays block answers the 11-year trap: occurrences of the
payday weekday in the year → 26 or 27 every-other-week paydays,
§5504(a) « covers two administrative workweeks ».

Amounts are STRINGS, arithmetic Decimal, rounding NAMED. Every
response passes its identities inside the module (rate_first ×40×52
reconciles to the annual within the rounding hole the tool itself
renders — the hole is the PRODUCT, never hidden).
"""
from decimal import Decimal, ROUND_HALF_UP
import calendar as _cal

CENT = Decimal("0.01")

FED_HOURS = 2087          # 5 USC 5504(b)
PRIV_HOURS = 2080         # 40 x 52, the published "typical"
BASES = ("fed2087", "priv2080", "workdays", "pto", "hours")
ORDERS = ("rate_first", "direct")
PERIODS = ("weekly", "biweekly", "semimonthly", "monthly")
WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4,
            "sat": 5, "sun": 6}


class PayScaleError(Exception):
    """Named 400: field, message, expected — the error IS the prompt."""

    def __init__(self, field, message, expected):
        self.field = field
        self.message = message
        self.expected = expected
        super().__init__(message)


def _d(value, field):
    if isinstance(value, bool):
        raise PayScaleError(field, "not a number", "decimal string")
    try:
        v = Decimal(str(value).replace(",", "").strip())
    except Exception:
        raise PayScaleError(field, "not a decimal amount",
                            "decimal string")
    if v < 0:
        raise PayScaleError(field, "a salary is not a debt",
                            ">= 0")
    return v


def workdays_in_year(year):
    """MON-FRI occurrences of a Gregorian year — the derivation of
    2087 published in r/fednews 1fnk3cb (4x262, 17x261, 7x260 over
    the 28-year cycle). Pure calendar, zero fetch."""
    if not isinstance(year, int) or year < 1900 or year > 2099:
        raise PayScaleError("year", "the calendar window here is "
                            "1900-2099 (weekday arithmetic is exact; "
                            "outside it the tool refuses rather "
                            "than trust a library edge)",
                            "int year 1900..2099")
    return sum(1 for month in range(1, 13)
               for day in range(1, _cal.monthrange(year, month)[1] + 1)
               if _cal.weekday(year, month, day) < 5)


def _cent(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def _s(x):
    return str(x)


def _basis_hours(basis, year=None, pto_hours=None, hours=None):
    """Return (denominator_int, label, citation) or raise by name."""
    if basis == "fed2087":
        return (FED_HOURS, "federal 2,087",
                "5 U.S.C. 5504(b): 'divide the annual rate by 2,087'"
                " (Pub. L. 98-117)")
    if basis == "priv2080":
        return (PRIV_HOURS, "typical 2,080 = 40 x 52",
                "r/Payroll 1pp94j9: 'typically 2080' — published, "
                "never named by the calculators")
    if basis == "workdays":
        if year is None:
            raise PayScaleError(
                "year", "basis=workdays is the REAL calendar of "
                "YOUR year — refusing to invent one",
                "year (int 1900..2099)")
        wd = workdays_in_year(year)
        return (wd * 8, "workdays %d x 8 = %d h (%d)" % (wd, wd * 8,
                year),
                "r/fednews 1fnk3cb derivation (4x262/17x261/7x260) "
                "— weekday count, holidays NOT encoded")
    if basis == "hours":
        if hours is None:
            raise PayScaleError(
                "hours", "basis=hours IS a denominator argument — "
                "the contract's own count (1,820 for 35 h x 52, "
                "2,400 for 200 h x 12, the regular-rate hours of "
                "29 CFR 778.113) — never invented here",
                "hours (decimal string, > 0)")
        h = _d(hours, "hours")
        if h <= 0:
            raise PayScaleError("hours", "a denominator counts "
                                "hours, not debts", "> 0")
        return (h, "custom %s h" % _s(h),
                "YOUR contract's hours — an argument; local law "
                "never encoded, the divisor belongs to the letter")
    if basis == "pto":
        if pto_hours is None:
            raise PayScaleError(
                "pto_hours", "basis=pto subtracts PAID TIME OFF "
                "hours from 2,080 — an argument, never a guess",
                "pto_hours (decimal, < 2080)")
        p = _d(pto_hours, "pto_hours")
        if p >= PRIV_HOURS:
            raise PayScaleError("pto_hours",
                                "PTO >= 2,080 leaves no denominator",
                                "< 2080")
        h = Decimal(PRIV_HOURS) - p
        return (h, "2,080 - %s PTO = %s h" % (_s(p), _s(h)),
                "1de8205's 1,880 reading (200 h of PTO/holidays)")
    raise PayScaleError(
        "basis", "unknown basis '%s' — the closed published set is "
        "listed; 365 is NOT in it (3r0eti: dividing by calendar "
        "DAYS produced 13.35/h instead of 24.03/h — a harm, not a "
        "convention)" % basis,
        "fed2087|priv2080|workdays|pto")


def money_payscale(annual, basis=None, period=None, order=None,
                   compare=False, year=None, pto_hours=None,
                   hours=None, payday_weekday=None, currency=None):
    if basis is None and not compare:
        raise PayScaleError(
            "basis", "no silent denominator — name it (or set "
            "compare=true to see the whole published table)",
            "|".join(BASES))
    if period is not None and period not in PERIODS:
        raise PayScaleError("period", "unknown period '%s'" % period,
                            "|".join(PERIODS))
    if order is not None and order not in ORDERS:
        raise PayScaleError("order", "unknown order '%s'" % order,
                            "|".join(ORDERS))
    amt = _d(annual, "annual")
    out = {"annual": _s(amt)}
    if currency:
        out["currency"] = str(currency)

    hourly = None
    if basis is not None:
        hours_n, label, cite = _basis_hours(basis, year, pto_hours,
                                            hours)
        exact = amt / Decimal(str(hours_n))
        rounded = _cent(exact)
        hourly = {"basis": basis, "label": label, "citation": cite,
                  "exact": _s(exact), "rounded_cent": _s(rounded),
                  "rounding": "nearest cent, one-half and over UP — "
                              "5 USC 5504(b) verbatim + OPM's "
                              "$18.845 -> $18.85 example"}
        out["hourly"] = hourly

    if period is not None or order is not None:
        if hourly is None:
            raise PayScaleError(
                "basis", "a period without a denominator is the "
                "17sefrt mistake (20 cents off) in machine form — "
                "name the basis",
                "|".join(BASES))
        if order is not None:
            out["order_chosen"] = order
        # NO forced choice by default: the PAIR of readings is the
        # product (prorate b119's grammar, settle b117). An order
        # argument only NAMES the caller's pick; both travel.
        periods = [period] if period else list(PERIODS)
        block = {}
        for p in periods:
            block[p] = _period(amt, hourly, p)
        out["periods"] = block

    if compare:
        rows = {}
        for b in BASES:
            try:
                hn, label, cite = _basis_hours(
                    b, year if b == "workdays" else None,
                    pto_hours if b == "pto" else None,
                    hours if b == "hours" else None)
            except PayScaleError:
                rows[b] = {"skipped": (
                    "needs year" if b == "workdays" else
                    "needs pto_hours" if b == "pto" else
                    "needs hours" if b == "hours" else "skipped")}
                continue
            ex = amt / Decimal(str(hn))
            rows[b] = {"hours": _s(hn),
                       "label": label,
                       "hourly_rounded": _s(_cent(ex)),
                       "citation": cite}
        named = [Decimal(r["hourly_rounded"]) for r in rows.values()
                 if "hourly_rounded" in r]
        if len(named) >= 2:
            rows["_spread"] = {"max_minus_min":
                               _s(max(named) - min(named)),
                               "note": "never a silent average — "
                                       "the payroll letter chooses; "
                                       "the machine names the room"}
        out["compare"] = rows

    if payday_weekday is not None:
        if year is None:
            raise PayScaleError("year", "the 27-period trap is a "
                                "CALENDAR question — give the year",
                                "int 1900..2099")
        wd = WEEKDAYS.get(str(payday_weekday).lower()[:3])
        if wd is None:
            raise PayScaleError("payday_weekday",
                                "unknown weekday '%s'" %
                                payday_weekday, "|".join(WEEKDAYS))
        n = 0
        d0 = _cal.weekday(year, 1, 1)
        ydays = 366 if _cal.isleap(year) else 365
        # occurrences of weekday wd in the year
        first_off = (wd - d0) % 7
        n = 1 + (ydays - 1 - first_off) // 7
        out["paydays_in_year"] = {
            "weekday": payday_weekday, "occurrences": n,
            "every_other_from_first": (n + 1) // 2,
            "every_other_from_second": n // 2,
            "note": "5 USC 5504(a): a pay period covers two "
                    "administrative workweeks — a 53rd payday makes "
                    "the 27-period year of r/IRS_Source 1qh5ouz "
                    "(2016 and 2027 for Friday anchors)"}
    return out


def _period(amt, hourly, p):
    """Both published readings side by side when order isn't forced;
    each carries its own citation. The annual hole is rendered, never
    smoothed — it IS the fednews complaint, quantified."""
    h_exact = Decimal(hourly["exact"])
    h_cent = Decimal(hourly["rounded_cent"])
    res = {}
    rf = None
    if p in ("weekly", "biweekly"):
        mult = 40 if p == "weekly" else 80
        rf = _cent(h_cent * mult)
        res["rate_first"] = _s(rf)
        res["rate_first_rule"] = ("rounded hourly x %d — 5 USC "
                                  "5504(b)(3)" % mult)
    if p == "biweekly":
        dg = _cent(amt / 26)
        res["direct"] = _s(dg)
        res["direct_rule"] = "annual / 26 (the employee's check, " \
                             "1bpysai)"
        if rf is not None:
            res["delta_rate_first_minus_direct"] = _s(rf - dg)
        if rf is not None:
            res["annual_hole_rate_first"] = _s(rf * 26 - amt)
            res["annual_hole_direct"] = _s(dg * 26 - amt)
    elif p == "semimonthly":
        dg = _cent(amt / 24)
        res["direct"] = _s(dg)
        res["direct_rule"] = "annual / 24 — published convention " \
                             "(the queue's 2166.67 vs 2000.00), " \
                             "NOT statute"
        res["annual_hole_direct"] = _s(dg * 24 - amt)
    elif p == "monthly":
        dg = _cent(amt / 12)
        res["direct"] = _s(dg)
        res["direct_rule"] = "annual / 12 — 5 USC 5505(1) verbatim " \
                             "('one-twelfth of a year's pay')"
        res["annual_hole_direct"] = _s(dg * 12 - amt)
    elif p == "weekly":
        ex = _cent(h_exact * 40)
        res["exact_rounded_once"] = _s(ex)
        res["exact_rule"] = "hourly unrounded x40, rounded once at " \
                            "the end"
        res["delta_rate_first_minus_exact"] = _s(
            Decimal(res["rate_first"]) - ex)
    return res
