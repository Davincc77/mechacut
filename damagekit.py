"""damagekit — /api/v1/csv/excel_damage : que Excel va-t-il DÉTRUIRE
dans ce CSV, AVANT le double-clic.

Le dommage frappe À L'OUVERTURE, pas à l'enregistrement (« Excel
converts CSV values on open, not on save, so the damage happens before
you notice it » — delimiter.live) ; sauvegarder après écrit l'endommagé
sur disque et le code postal sans son zéro est IRRÉCUPÉRABLE. Les règles
de conversion automatiques d'Excel sont NOMMÉES par Microsoft lui-même
depuis Excel 365 (version 2309 Windows / 16.77 Mac, File→Options→Data→
Automatic Data Conversion, trois interrupteurs : remove leading zeros /
convert to scientific notation / convert text to dates — aiwebcenter).
Ce module PRÉDIT cellule par cellule ce que chaque interrupteur ferait,
avec les VECTEURS PUBLIÉS rejoués (devholster : 01234→1234,
4111111111111111→4111111111111110, 987654321098765432→9.87654E+17,
1E5→100000, SEPT2→date, 3/4→date, -5/+43→nombre/formule ; changethisfile :
ZIP 02134→2134, MARCH1→1 mars ; aiwebcenter : le sérial 46113 =
1-avril-2026, époque 30-déc-1899 — le « 46113 » que les gens trouvent
dans leurs exports EST la date).

La date devinée dépend de la LOCALE : « 3-4 » devient 3 avril en
anglais (m/d) et 4 mars en français/allemand (d.m) — même cellule, DEUX
dates, et l'outil qui ne pose pas la question fond les deux. locale est
donc un ARGUMENT (en|eu), jamais deviné ; l'année implicite d'un jeton
sans année est figée par as_of (règle n°1 du playbook : le temps est un
argument).

CE LOT = la DÉTECTION (verdict par colonne + mode d'import prescrit).
Le RENDU du masque numFmt (stocké→affiché, les 88 % de misled de
l'étude ooxml-display-fidelity) est le sous-lot M resté en file.
"""

import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

_EPOCH = date(1899, 12, 30)   # la base des sérials Excel (1 = 1-01-1900,
                              # bug du siècle 1900 digéré : 60 = 29-févr
                              # 1900 fantôme ; époque effective 30-déc-
                              # 1899 pour les dates >= 1-mars-1900)

_MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
           "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
_ABBR = {m: i + 1 for i, m in enumerate(_MONTHS)}
# alias publiés : SEPT (devholster) et les noms complets (MARCH, changethisfile)
_ABBR.update({"SEPT": 9, "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3,
              "APRIL": 4, "JUNE": 6, "JULY": 7, "AUGUST": 8,
              "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11,
              "DECEMBER": 12})

_RE_ZEROS = re.compile(r"^0\d+$")
_RE_LONGINT = re.compile(r"^\d{16,}$")
_RE_SCI = re.compile(r"^\d+E-?\d+$", re.IGNORECASE)
_RE_MD = re.compile(r"^(\d{1,2})[./-](\d{1,2})$")
_RE_MDA = re.compile(r"^(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})$")
_RE_MONTHNAME = re.compile(r"^([A-Z]+)\.?(\d{1,2})$")
_RE_SIGN = re.compile(r"^[=+-@]\d")
_RE_FULLWIDTH = re.compile(r"[０-９]")

_IMPORT_PRESCRIPTION = [
    "NEVER double-click the file: open Excel blank first, then "
    "Data > From Text/CSV > Transform Data, and set every flagged "
    "column to TEXT before loading (Power Query)",
    "or switch the conversions off at the source: Excel 365 >= 2309 "
    "(Windows) / 16.77 (Mac), File > Options > Data > Automatic Data "
    "Conversion: 'remove leading zeros', 'scientific notation', "
    "'turn text into dates' — Microsoft's own three toggles",
    "or ship .xlsx (typed) instead of CSV when the recipient will "
    "open it in Excel (devholster)",
    "reformatting the cell AFTER the damage does NOT recover the "
    "value — the digits are gone from the model, only the original "
    "file is intact (dev.to/thedaybreak, delimiter.live)",
]

_RULES = {
    "leading_zero_stripped": "Microsoft toggle 'remove leading zeros': "
                             "02134 becomes 2134 — postcodes, SSNs, "
                             "phone numbers, internal codes",
    "long_number_truncated": "15 significant digits is the ceiling: "
                             "the 16th+ digits become 0 (4111...111 -> "
                             "...110) and display flips to scientific "
                             "notation (987654321098765432 -> "
                             "9.87654E+17), unrecoverable",
    "exponent_read_as_number": "1E5 is already a number to Excel: "
                               "displays as 100000 — product codes of "
                               "shape letter-E-digits die silently",
    "coerced_to_date": "anything date-shaped becomes a date SERIAL "
                       "(stored as days since 1899-12-30; 46113 IS "
                       "2026-04-01): part numbers, ratios, gene names "
                       "(MARCH1, SEPT2), and '1-2' or '3/4' ranges — "
                       "the interpretation depends on LOCALE: m/d for "
                       "en, d/m for eu",
    "formula_shaped": "a leading = + - @ with digits after is "
                      "formula-trigger territory: -5 and +43 become "
                      "numbers, '=...' executes, injection risk when "
                      "the file is downstream-shared (changethisfile)",
    "fullwidth_digits": "typed full-width digits (１２３) are NOT the "
                        "number 123 to tools that compare strings; "
                        "Excel may read the cell as text while your "
                        "pipeline sees two different IDs "
                        "(dev.to/thedaybreak)",
    "text_preserved": "no known automatic conversion fires; the cell "
                      "survives a double-click unchanged",
}


class DamageError(ValueError):
    def __init__(self, field, message, expected=None):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected or ""


def _serial(d):
    """Sérial Excel pour une date >= 1900-03-01 (base 1899-12-30)."""
    return (d - _EPOCH).days


def _year_of(as_of, yy):
    """Excel complète un jeton sans année avec l'ANNÉE COURANTE ; deux
    chiffres = 20yy (fenêtre 1930-2029). Ici le temps est figé par
    as_of — jamais lu de l'horloge."""
    if yy is None:
        return as_of.year
    if len(str(yy)) <= 2:
        y = int(str(yy))
        return 2000 + y if y < 30 else 1900 + y
    return int(yy)


def _as_date(text, locale, as_of):
    """Renvoie (date, explication) si Excel dateifierait ce jeton,
    sinon None."""
    t = text.strip()
    m = _RE_MD.match(t)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if locale == "en":          # m/d
            mo, dy = a, b
        else:                        # d/m (eu)
            mo, dy = b, a
        if not (1 <= mo <= 12 and 1 <= dy <= 31):
            return None
        try:
            d = date(_year_of(as_of, None), mo, dy)
        except ValueError:
            return None
        limb = "month/day (en)" if locale == "en" else "day/month (eu)"
        return d, "'%s' read as %s" % (t, limb)
    m = _RE_MDA.match(t)
    if m:
        a, b, c = m.group(1), m.group(2), m.group(3)
        a, b = int(a), int(b)
        if locale == "en":
            mo, dy = a, b
        else:
            mo, dy = b, a
        try:
            d = date(_year_of(as_of, c), mo, dy)
        except ValueError:
            return None
        return d, "year %r completed per window 1930-2029" % c
    m = _RE_MONTHNAME.match(t.upper())
    if m and m.group(1) in _ABBR:
        mo = _ABBR[m.group(1)]
        dy = int(m.group(2))
        if 1 <= dy <= 31:
            try:
                d = date(_year_of(as_of, None), mo, dy)
            except ValueError:
                return None
            return d, "month-name prefix '%s' + day" % m.group(1)
    return None


def classify_cell(raw, locale, as_of):
    """Règle principale -> ce qu'Excel STOCKERAIT/AFFICHERAIT, par les
    vecteurs publiés. Retourne (règle, prédiction dict ou None)."""
    v = raw.strip()
    if v == "":
        return "text_preserved", None
    if _RE_FULLWIDTH.search(v):
        return "fullwidth_digits", {"note": "compare strings, not "
                                    "numbers — two IDs for tools"}
    if _RE_SCI.match(v):
        d = Decimal(v)
        disp = str(int(d)) if d == d.to_integral_value() \
            else format(d.normalize(), "f")
        return "exponent_read_as_number", {"displayed": disp}
    if _RE_LONGINT.match(v):
        q = Decimal(v)
        # garde de 15 chiffres significatifs, arrondi du 16e (demi vers
        # le haut — vector publié 4111111111111111 -> 4111111111111110)
        exp = len(v) - 15
        factor = Decimal(10) ** exp
        rounded = (q / factor).quantize(Decimal("1"),
                                        rounding=ROUND_HALF_UP) * factor
        return "long_number_truncated", {
            "displayed": "%sE+%d" % (str(rounded)[0] + "." +
                                     str(rounded)[1:6].rstrip("0"),
                                     len(v) - 1),
            "stored_value": str(int(rounded)),
            "digits_kept": 15}
    if _RE_ZEROS.match(v):
        return "leading_zero_stripped", {"displayed": str(int(v))}
    if v.startswith("="):
        return "formula_shaped", {"note": "executes as a formula"}
    if _RE_SIGN.match(v):
        head = v[0]
        return "formula_shaped", {"displayed": str(int(v))}
    got = _as_date(v, locale, as_of)
    if got:
        d, why = got
        return "coerced_to_date", {
            "stored_serial": _serial(d), "displays": d.isoformat(),
            "why": why}
    return "text_preserved", None


def run_damage(args):
    text = args.get("csv")
    if not isinstance(text, str) or not text.strip():
        raise DamageError("csv", "missing or empty",
                          "the CSV text itself (string), max 20000 "
                          "chars")
    if len(text) > 20000:
        raise DamageError("csv", "too long (%d > 20000)" % len(text),
                          "keep the file under 20 KB — the point is "
                          "the shape of the columns, not the volume")
    locale = (args.get("locale") or "en").strip().lower()
    if locale not in ("en", "eu"):
        raise DamageError("locale", "must be 'en' (month/day) or "
                          "'eu' (day/month), got %r"
                          % args.get("locale"))
    at = args.get("as_of")
    if at is None:
        raise DamageError("as_of", "required",
                          "'YYYY-MM-DD' — the year Excel IMPLIES for "
                          "'3/4' is the CURRENT year, so the clock is "
                          "an argument here, never a fetch")
    try:
        as_of = date.fromisoformat(str(at).strip())
    except ValueError:
        raise DamageError("as_of", "not an ISO date: %r" % at)
    dialect = ";" if text.count(";") > text.count(",") else ","

    rows = [[c.strip() for c in line.split(dialect)]
            for line in text.splitlines() if line.strip()]
    if not rows:
        raise DamageError("csv", "no lines")
    ncols = max(len(r) for r in rows)
    columns = []
    for i in range(ncols):
        vals = [r[i] for r in rows[1:] if len(r) > i] or \
               [r[i] for r in rows if len(r) > i]
        header = rows[0][i] if (len(rows[0]) > i and ncols and
                                len(rows) > 1) else ""
        counts = {}
        flagged = []
        for v in vals:
            rule, pred = classify_cell(v, locale, as_of)
            counts[rule] = counts.get(rule, 0) + 1
            if rule != "text_preserved" and pred is not None \
                    and len(flagged) < 5:
                item = {"cell": v, "rule": rule}
                item.update(pred)
                flagged.append(item)
        endangered = sum(n for r, n in counts.items()
                         if r != "text_preserved")
        columns.append({
            "header": header, "values_scanned": len(vals),
            "at_risk": endangered > 0,
            "endangered_cells": endangered, "rule_counts": counts,
            "samples": flagged,
            "import_mode": "Text (typed) via Data>From Text/CSV"
                           if endangered > 0 else "any (nothing "
                           "converts)",
        })
    out = {
        "dialect_detected": dialect, "locale": locale,
        "as_of": as_of.isoformat(), "rows": len(rows),
        "columns": columns,
        "at_risk_columns": [c["header"] or "#%d" % (i + 1)
                           for i, c in enumerate(columns)
                           if c["at_risk"]],
        "rules_glossary": {k: _RULES[k] for k in sorted(_RULES)},
        "prescribed_import": _IMPORT_PRESCRIPTION,
        "recovery_note": "damage happens ON OPEN, saving writes it "
                         "back — a stripped zero is UNRECOVERABLE "
                         "from the xlsx; only the original CSV is "
                         "intact (delimiter.live)",
        "scope_note": "detection of the three Microsoft Automatic "
                      "Data Conversion classes + published vectors; "
                      "the displayed-vs-stored numFmt mask study "
                      "(88 % misled) is the separate rendering lot",
    }
    return out
