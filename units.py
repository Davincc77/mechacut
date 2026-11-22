"""Deterministic unit conversion — closed families, exact rational factors.

Every factor is defined against the family's canonical unit as a Decimal
integer ratio (numerator, denominator), so conversions are exact fractions
resolved at the requested precision — never float chains.
"""

from decimal import Decimal, localcontext


class UnitError(Exception):
    pass


# canonical: family -> {unit: (factor_num, factor_den)}  relative to base
def _f(num, den=1):
    return (Decimal(num), Decimal(den))


FAMILIES = {
    "length": {
        "base": "m",
        "units": {"m": _f(1), "km": _f(1000), "cm": _f(1, 100),
                  "mm": _f(1, 1000), "um": _f(1, 10**6),
                  "in": _f(254, 10000), "ft": _f(3048, 10000),
                  "yd": _f(9144, 10000), "mi": _f(1609344, 1000),
                  "nmi": _f(1852), "league": _f(3 * 1609344, 1000)},
    },
    "mass": {
        "base": "kg",
        "units": {"kg": _f(1), "g": _f(1, 1000), "mg": _f(1, 10**6),
                  "t": _f(1000), "tonne": _f(1000),
                  "lb": _f(45359237, 10**8), "oz": _f(28349523125, 10**12),
                  "st": _f(14 * 45359237, 10**8)},
    },
    "volume": {
        "base": "l",
        "units": {"l": _f(1), "ml": _f(1, 1000), "cl": _f(1, 100),
                  "dl": _f(1, 10), "m3": _f(1000), "cm3": _f(1, 1000),
                  # NIST SP 811 App. B : gal_us = 231 in^3 =
                  # 3,785411784 L pile (inch = 2,54 cm pile, accord
                  # 1959) ; floz = gal/128, qt = gal/4, pt = gal/8,
                  # cup = gal/16. PUISSANCES DE 10 CORRIGEES 22-11
                  # (bundle66) : floz_us etait tablé a 2,957 L l'once
                  # (x100), qt_us/pt_us/cup_us x10 — peche par la
                  # table croisee qt<->floz de money/unitprice, faute
                  # de test sur ces unités (garde ajouté bundle66).
                  "gal_us": _f(3785411784, 10**9),
                  "qt_us": _f(946352946, 10**9),
                  "pt_us": _f(473176473, 10**9),
                  "cup_us": _f(2365882365, 10**10),
                  "floz_us": _f(295735295625, 10**13),
                  "gal_uk": _f(454609, 100000)},
    },
    "area": {
        "base": "m2",
        "units": {"m2": _f(1), "km2": _f(10**6), "ha": _f(10000),
                  "are": _f(100), "acre": _f(40468564224, 10**7),
                  "ft2": _f(9290304, 10**6), "in2": _f(64516, 10**8),
                  "yd2": _f(83612736, 10**7)},
    },
    "speed": {
        "base": "ms",
        "units": {"ms": _f(1), "kmh": _f(1000, 3600), "mph": _f(1609344,
                                                                3600 * 1000),
                  "knot": _f(1852, 3600), "min": _f(3600)},
        "note": "min is min/km as pace is NOT speed; kept out via family check",
    },
    "data": {
        "base": "B",
        "units": {"B": _f(1), "kB": _f(1000), "MB": _f(10**6),
                  "GB": _f(10**9), "TB": _f(10**12), "PB": _f(10**15),
                  "KiB": _f(1024), "MiB": _f(1024**2), "GiB": _f(1024**3),
                  "TiB": _f(1024**4), "PiB": _f(1024**5),
                  "bit": _f(1, 8), "kbit": _f(1000, 8),
                  "Mbit": _f(10**6, 8), "Gbit": _f(10**9, 8)},
    },
    "duration": {
        "base": "s",
        "units": {"s": _f(1), "ms_t": _f(1, 1000), "min": _f(60),
                  "h": _f(3600), "d": _f(86400), "wk": _f(604800)},
    },
}
# drop the accidental 'min' entry from speed (pace confusion)
FAMILIES["speed"]["units"].pop("min", None)
FAMILIES["speed"].pop("note", None)

# temperature: offset math, not a ratio
_TEMPS = {"C", "F", "K"}

# unit aliases accepted on input
ALIASES = {
    "kilometer": "km", "kilometre": "km", "kilometers": "km",
    "metre": "m", "metres": "m", "meters": "m",
    "centimeter": "cm", "millimeter": "mm",
    "inch": "in", "inches": "in", "feet": "ft", "foot": "ft",
    "yards": "yd", "mile": "mi", "miles": "mi",
    "kilogram": "kg", "kilograms": "kg", "gram": "g", "grams": "g",
    "pound": "lb", "pounds": "lb", "ounce": "oz", "ounces": "oz",
    "liter": "l", "litre": "l", "liters": "l", "litres": "l",
    "gallon": "gal_us", "cup": "cup_us",
    "hectare": "ha", "hectares": "ha", "acres": "acre",
    "kilobyte": "kB", "megabyte": "MB", "gigabyte": "GB",
    "terabyte": "TB", "byte": "B", "bytes": "B",
    "second": "s", "seconds": "s", "minute": "min", "minutes": "min",
    "hour": "h", "hours": "h", "day": "d", "days": "d", "week": "wk",
    "weeks": "wk", "km/h": "kmh", "kmph": "kmh", "mph": "mph",
    "knots": "knot", "m/s": "ms", "mps": "ms", "sqm": "m2",
    "sqft": "ft2", "tonne": "t", "tonnes": "t",
}


def _resolve(unit):
    u = unit.strip()
    key = ALIASES.get(u.lower(), ALIASES.get(u, u))
    fam = None
    for name, spec in FAMILIES.items():
        if key in spec["units"]:
            fam = name
            break
    if fam is None:
        if key in _TEMPS:
            return "temperature", key
        raise UnitError("unknown unit: %r — closed families: %s"
                        % (unit, ", ".join(sorted(FAMILIES))))
    return fam, key


def units_convert(value, from_unit, to_unit, places=10):
    fam_a, a = _resolve(from_unit)
    fam_b, b = _resolve(to_unit)
    if fam_a == "temperature" or fam_b == "temperature":
        if fam_a != fam_b:
            raise UnitError("cross-family conversion refused: %r is %s, "
                            "%r is %s" % (from_unit, fam_a, to_unit, fam_b))
        out = _from_c(_to_c(Decimal(str(a if isinstance(a, Decimal) else 0)),
                             a), b) if False else _from_c(
            _to_c(Decimal(str(value)), a), b)
        q = out.quantize(Decimal(1).scaleb(-places))
        return {"value": format(q.normalize(), "f"),
                "float": float(out),
                "from": (from_unit, a, fam_a), "to": (to_unit, b, fam_b),
                "base": "C", "places": places}
    if fam_a != fam_b:
        raise UnitError("cross-family conversion refused: %r is %s, %r is "
                        "%s" % (from_unit, fam_a, to_unit, fam_b))
    d = Decimal(str(value)) if not isinstance(value, Decimal) else value
    if fam_a == "temperature":
        c = _to_c(d, a)
        out = _from_c(c, b)
    else:
        na, da = FAMILIES[fam_a]["units"][a]
        nb, db = FAMILIES[fam_a]["units"][b]
        with localcontext() as ctx:
            ctx.prec = 50
            out = d * (na / da) * (db / nb)
    q = out.quantize(Decimal(1).scaleb(-places)) if places is not None \
        else out
    qs = q.normalize()
    return {"value": format(qs, "f") if "E" not in format(qs, "f").upper()
            else format(qs, "f"),
            "float": float(out),
            "from": (from_unit, a, fam_a), "to": (to_unit, b, fam_b),
            "base": FAMILIES[fam_a]["base"], "places": places}


def _to_c(d, unit):
    if unit == "C":
        return d
    if unit == "F":
        return (d - Decimal(32)) * Decimal(5) / Decimal(9)
    return d - Decimal(273.15)


def _from_c(c, unit):
    if unit == "C":
        return c
    if unit == "F":
        return c * Decimal(9) / Decimal(5) + Decimal(32)
    return c + Decimal(273.15)


def units_info():
    return {name: {"base": spec["base"],
                   "units": sorted(spec["units"])}
            for name, spec in FAMILIES.items()}


# ---- Bundle 28 lot 8: closed ISO lookups ----
# TABLE = subset publié de la norme; HORS-SUBSET = verdict explicite
# "outside the closed subset", JAMAIS un faux "invalide" (règle: chaque
# outil doit pouvoir dire "je ne sais pas" avec précision).
COUNTRIES = {
    "FR": ("France", "FRA", "250", "EUR", "33", 2), "DE": ("Germany", "DEU", "276", "EUR", "49", 2),
    "GB": ("United Kingdom", "GBR", "826", "GBP", "44", 2), "US": ("United States", "USA", "840", "USD", "1", 2),
    "CA": ("Canada", "CAN", "124", "CAD", "1", 2), "BR": ("Brazil", "BRA", "076", "BRL", "55", 2),
    "PT": ("Portugal", "PRT", "620", "EUR", "351", 2), "ES": ("Spain", "ESP", "724", "EUR", "34", 2),
    "IT": ("Italy", "ITA", "380", "EUR", "39", 2), "NL": ("Netherlands", "NLD", "528", "EUR", "31", 2),
    "BE": ("Belgium", "BEL", "056", "EUR", "32", 2), "LU": ("Luxembourg", "LUX", "442", "EUR", "352", 2),
    "IE": ("Ireland", "IRL", "372", "EUR", "353", 2), "AT": ("Austria", "AUT", "040", "EUR", "43", 2),
    "CH": ("Switzerland", "CHE", "756", "CHF", "41", 2), "SE": ("Sweden", "SWE", "752", "SEK", "46", 2),
    "NO": ("Norway", "NOR", "578", "NOK", "47", 2), "DK": ("Denmark", "DNK", "208", "DKK", "45", 2),
    "FI": ("Finland", "FIN", "246", "EUR", "358", 2), "PL": ("Poland", "POL", "616", "PLN", "48", 2),
    "CZ": ("Czechia", "CZE", "203", "CZK", "420", 2), "SK": ("Slovakia", "SVK", "703", "EUR", "421", 2),
    "HU": ("Hungary", "HUN", "348", "HUF", "36", 2), "RO": ("Romania", "ROU", "642", "RON", "40", 2),
    "BG": ("Bulgaria", "BGR", "100", "BGN", "359", 2), "HR": ("Croatia", "HRV", "191", "EUR", "385", 2),
    "SI": ("Slovenia", "SVN", "705", "EUR", "386", 2), "GR": ("Greece", "GRC", "300", "EUR", "30", 2),
    "JP": ("Japan", "JPN", "392", "JPY", "81", 0), "KR": ("Korea, Republic of", "KOR", "410", "KRW", "82", 0),
    "CN": ("China", "CHN", "156", "CNY", "86", 2), "IN": ("India", "IND", "356", "INR", "91", 2),
    "SG": ("Singapore", "SGP", "702", "SGD", "65", 2), "HK": ("Hong Kong", "HKG", "344", "HKD", "852", 2),
    "TW": ("Taiwan", "TWN", "158", "TWD", "886", 2), "TH": ("Thailand", "THA", "764", "THB", "66", 2),
    "VN": ("Viet Nam", "VNM", "704", "VND", "84", 0), "ID": ("Indonesia", "IDN", "360", "IDR", "62", 2),
    "MY": ("Malaysia", "MYS", "458", "MYR", "60", 2), "PH": ("Philippines", "PHL", "608", "PHP", "63", 2),
    "AU": ("Australia", "AUS", "036", "AUD", "61", 2), "NZ": ("New Zealand", "NZL", "554", "NZD", "64", 2),
    "MX": ("Mexico", "MEX", "484", "MXN", "52", 2), "AR": ("Argentina", "ARG", "032", "ARS", "54", 2),
    "CL": ("Chile", "CHL", "152", "CLP", "56", 0), "CO": ("Colombia", "COL", "170", "COP", "57", 2),
    "PE": ("Peru", "PER", "604", "PEN", "51", 2), "UY": ("Uruguay", "URY", "858", "UYU", "598", 2),
    "PY": ("Paraguay", "PRY", "600", "PYG", "595", 0), "BO": ("Bolivia", "BOL", "068", "BOB", "591", 2),
    "VE": ("Venezuela", "VEN", "862", "VES", "58", 2), "ZA": ("South Africa", "ZAF", "710", "ZAR", "27", 2),
    "NG": ("Nigeria", "NGA", "566", "NGN", "234", 2), "EG": ("Egypt", "EGY", "818", "EGP", "20", 2),
    "KE": ("Kenya", "KEN", "404", "KES", "254", 2), "MA": ("Morocco", "MAR", "504", "MAD", "212", 2),
    "AE": ("United Arab Emirates", "ARE", "784", "AED", "971", 2), "SA": ("Saudi Arabia", "SAU", "682", "SAR", "966", 2),
    "IL": ("Israel", "ISR", "376", "ILS", "972", 2), "TR": ("Türkiye", "TUR", "792", "TRY", "90", 2),
    "UA": ("Ukraine", "UKR", "804", "UAH", "380", 2), "RU": ("Russian Federation", "RUS", "643", "RUB", "7", 2),
}

POSTAL = {
    "FR": r"\d{5}", "DE": r"\d{5}", "ES": r"\d{5}", "IT": r"\d{5}",
    "PT": r"\d{4}-?\d{3}", "NL": r"\d{4} ?[A-Z]{2}", "BE": r"\d{4}",
    "AT": r"\d{4}", "CH": r"\d{4}", "LU": r"\d{4}", "IE": r"[\dA-Z]{6,9}",
    "GB": r"[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}", "US": r"\d{5}(-\d{4})?",
    "CA": r"[A-Z]\d[A-Z] ?\d[A-Z]\d", "BR": r"\d{5}-?\d{3}",
    "JP": r"\d{3}-?\d{4}", "AU": r"\d{4}", "IN": r"\d{6}",
    "MX": r"\d{5}", "AR": r"[A-Z]?\d{4}[A-Z]?", "ZA": r"\d{4}",
    "SE": r"\d{3} ?\d{2}", "NO": r"\d{4}", "DK": r"\d{4}",
    "PL": r"\d{2}-?\d{3}", "CZ": r"\d{3} ?\d{2}", "SK": r"\d{3} ?\d{2}",
    "HU": r"\d{4}", "RO": r"\d{6}", "BG": r"\d{4}", "HR": r"\d{5}",
    "GR": r"\d{3} ?\d{2}", "KR": r"\d{5}", "CN": r"\d{6}",
    "NZ": r"\d{4}", "CL": r"\d{7}", "CO": r"\d{6}", "PE": r"\d{5}",
    "UY": r"\d{5}", "PY": r"\d{4}", "BO": r"\d{4}", "VE": r"\d{4}",
    "TR": r"\d{5}", "IL": r"\d{5}(-?\d{2})?", "SA": r"\d{5}",
    "AE": r"[A-Z]?\d{5}", "MA": r"\d{5}", "EG": r"\d{5}",
    "NG": r"[A-Z]{2,3} ?\d{2,4}", "KE": r"\d{5}",
}

_CANON_POSTAL = {
    "US": lambda x: x[:5] + ("-" + x[6:] if len(x) > 5 else ""),
    "CA": lambda x: x if " " in x else x[:3] + " " + x[3:],
    "NL": lambda x: x if " " in x else x[:4] + " " + x[4:],
    "BR": lambda x: x if "-" in x else x[:5] + "-" + x[5:],
    "JP": lambda x: x if "-" in x else x[:3] + "-" + x[3:],
    "PT": lambda x: x if "-" in x else x[:4] + "-" + x[4:],
}


def validate_country(code):
    c = str(code).strip().upper()
    if not (len(c) == 2 and c.isalpha()):
        raise UnitError("code must be ISO 3166-1 alpha-2 (2 letters)")
    if c in COUNTRIES:
        name, iso3, num, cur, dial, dec = COUNTRIES[c]
        return {"alpha_2": c, "alpha_3": iso3, "numeric": num,
                "official_name": name, "currency": cur,
                "currency_decimal_places": dec,
                "calling_code": "+" + dial, "in_subset": True,
                "subset_size": len(COUNTRIES)}
    return {"alpha_2": c, "in_subset": False,
            "verdict": "well-formed alpha-2 but outside the closed subset"
                       " of %d countries shipped: this is NOT a claim of"
                       " invalidity — it is the honest edge of the table"
                       % len(COUNTRIES)}


def validate_postal(code, country):
    import re as _re
    c = str(country).strip().upper()
    if c not in POSTAL:
        raise UnitError("no postal grammar shipped for %r (subset of %d "
                        "countries)" % (c, len(POSTAL)))
    s = str(code).strip().upper()
    ok = bool(_re.compile(POSTAL[c]).fullmatch(s))
    out = {"country": c, "input": s, "valid": ok}
    if ok and c in _CANON_POSTAL:
        out["canonical"] = _CANON_POSTAL[c](s)
    if not ok:
        out["expected"] = POSTAL[c]
    return out
