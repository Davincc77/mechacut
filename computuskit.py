"""computuskit — bundle 133 (admission 27-11, registre L63, reçu 30b0983b).

Pâques par les deux computus PUBLIÉS, chacun NOMMÉ dans l'entrée :
gregorian_meeus_butcher (l'algorithme anonyme publié dans Nature en
1876, repris par Butcher 1877 et Meeus, Astronomical Algorithms 1991
ch. 56) et julian_meeus (Meeus AA 1991 p. 69 — le computus pascal des
Églises orientales). Le computus anonyme ne se devine pas : la douleur
mesurée de la campagne (COMPIL_RAPPORTS_VAGUE2, section clic 133) est
« date_parse refuses 'Easter 2012' » et « /route?q=easter+computus
return no tool » ; ici l'année et l'algorithme sont deux arguments
obligatoires, jamais une prose à parser.

Algorithme public : les deux suites de formules sont celles publiées
(Nature 1876 / Meeus 1991), entiers uniquement, jamais de float. Les
golds sont tracés depuis les COLONNES D'EXEMPLE publiées (1961/2026/
2027 grégorien, 2008/2016/2026/2027 julien, table « Date of Easter »
récupérée 27-11) plus les assertions consignées du rapport de campagne
(Pâque 2012-04-08 / 2012-04-15 = julien 04-02 + 13, coïncidence 2014,
2038-04-25 et 1943-04-25 dimanches). Le visage civil de chaque jour
voyage par le pont JDN de juliankit (bundle 135) : la table centurielle
des décalages est la MÊME (nom + version + sha importés), un 2100 à
+14 jours se lit dans la table, jamais dans un colle de 13.

Fenêtres closes, nommées : le computus grégorien répond à partir de
1583 (« The Gregorian Easter has been used since 1583 », page publiée)
et le julien de l'an 1 de l'ère liturgique ; les deux s'arrêtent à
9999, la fenêtre civile du pont. Hors portée : refus par le nom
désignant le voisin (julian_meeus pour 1500, date_julian_gregorian
pour les jours astronomiques), jamais un 400 muet.
"""
import hashlib
import json

import juliankit

ALGO_GREG = "gregorian_meeus_butcher"
ALGO_JUL = "julian_meeus"
ALGORITHMS = (ALGO_GREG, ALGO_JUL)     # ensemble fermé, nommé

# bornes fermées, dites (ère liturgique ; fenêtre civile du pont 135)
Y_JUL_MIN, Y_MAX = 1, 9999
Y_GREG_MIN = 1583

_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday", "Sunday")

PROCEDURE_NAME = "meeus-butcher-computus"
PROCEDURE_VERSION = (
    "v1 (2026-11-27) — Gregorian: anonymous computus, Nature 1876 / "
    "Butcher 1877 / Meeus AA 1991 ch. 56; Julian: Meeus AA 1991 p. 69. "
    "Worked-example columns published and replayed: 1961, 2026, 2027 "
    "(Gregorian) and 2008, 2016, 2026, 2027 (Julian, with their civil "
    "Gregorian equivalents 27 Apr 2008, 1 May 2016, 12 Apr 2026, "
    "2 May 2027)")
PROCEDURE_STEPS = {
    "gregorian_meeus_butcher": [
        "a = Y mod 19", "b = Y // 100", "c = Y mod 100", "d = b // 4",
        "e = b mod 4", "f = (b + 8) // 25", "g = (b - f + 1) // 3",
        "h = (19a + b - d - g + 15) mod 30", "i = c // 4", "k = c mod 4",
        "l = (32 + 2e + 2i - h - k) mod 7", "m = (a + 11h + 22l) // 451",
        "n = (h + l - 7m + 114) // 31 (month)",
        "o = (h + l - 7m + 114) mod 31 (day = o + 1)"],
    "julian_meeus": [
        "a = Y mod 4", "b = Y mod 7", "c = Y mod 19",
        "d = (19c + 15) mod 30", "e = (2a + 4b - d + 34) mod 7",
        "month = (d + e + 114) // 31", "day = (d + e + 114) mod 31 + 1"],
}
PROCEDURE_SHA256 = hashlib.sha256(json.dumps(
    {"name": PROCEDURE_NAME, "version": PROCEDURE_VERSION,
     "steps": PROCEDURE_STEPS}, sort_keys=True,
    separators=(",", ":")).encode()).hexdigest()

GOLDEN_RULE = ("golden number = (Y mod 19) + 1 — the Metonic sequence "
               "number, published formula of the Date of Easter article")


class ComputusError(Exception):
    def __init__(self, msg, field):
        super().__init__(msg)
        self.msg, self.field = msg, field


def _fmt(y, m, d):
    return "%04d-%02d-%02d" % (y, m, d)


def _weekday(jdn):
    return {"name": _WEEKDAYS[jdn % 7], "iso": jdn % 7 + 1}


def easter_gregorian_computus(y):
    """Le computus grégorien publié (Nature 1876 / Butcher / Meeus),
    entiers uniquement ; le visage julien passe par le pont 135."""
    a = y % 19
    b = y // 100
    c = y % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    n = (h + l - 7 * m + 114) // 31
    o = (h + l - 7 * m + 114) % 31
    jdn = juliankit.jdn_gregorian(y, n, o + 1)
    jt = juliankit.julian_from_jdn(jdn)
    return {
        "algorithm": ALGO_GREG,
        "computus": "gregorian",
        "gregorian_tuple": (y, n, o + 1),
        "julian_tuple": jt,
        "easter_gregorian": _fmt(y, n, o + 1),
        "easter_julian": _fmt(*jt),
        "jdn": jdn,
        "weekday": _weekday(jdn),
        "golden_number": a + 1,
        "offset_days": juliankit.offset_days(y, n),
        "intermediates": {"a": a, "b": b, "c": c, "d": d, "e": e,
                          "f": f, "g": g, "h": h, "i": i, "k": k,
                          "l": l, "m": m, "n": n, "o": o},
    }


def easter_julian_computus(y):
    """Le computus julien de Meeus (AA 1991 p. 69) : la date est JULIENNE
    par construction ; le jour civil grégorien se lit dans le pont, et le
    décalage centuriel (13 jours 1900-2099, 14 à partir de 2100) vient de
    la table, jamais d'un colle."""
    a = y % 4
    b = y % 7
    c = y % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    s = d + e + 114
    month = s // 31
    day = s % 31 + 1
    jdn = juliankit.jdn_julian(y, month, day)
    gt = juliankit.gregorian_from_jdn(jdn)
    return {
        "algorithm": ALGO_JUL,
        "computus": "julian",
        "julian_tuple": (y, month, day),
        "gregorian_tuple": gt,
        "easter_julian": _fmt(y, month, day),
        "easter_gregorian": _fmt(*gt),
        "jdn": jdn,
        "weekday": _weekday(jdn),
        "golden_number": c + 1,
        "offset_days": juliankit.offset_days(gt[0], gt[1]),
        "intermediates": {"a": a, "b": b, "c": c, "d": d, "e": e,
                          "d_plus_e_plus_114": s},
    }


def easter(year=None, algorithm=None):
    if algorithm is None:
        raise ComputusError(
            "algorithm: gregorian_meeus_butcher or julian_meeus — "
            "REQUIRED, never guessed. Western and Orthodox dates are "
            "different algorithms, not synonyms (2012: 04-08 vs 04-15; "
            "they coincide in 2014) — which computus you mean is the "
            "algorithm you type", "algorithm")
    if algorithm not in ALGORITHMS:
        raise ComputusError(
            "algorithm=%r is not in the closed set {gregorian_meeus_"
            "butcher, julian_meeus} of this contract (the two published "
            "computus of the campaign material). The revised-Julian "
            "(1923) and Aleppo (1997) proposals named on the published "
            "page were never adopted by the churches that date Easter "
            "today: separate contracts, not modelled, not synonyms"
            % algorithm, "algorithm")
    if isinstance(year, bool) or not isinstance(year, int):
        raise ComputusError(
            "year: an integer civil year of the liturgical era (1961, "
            "not '1961' nor 1961.0) — the computus takes a year and "
            "returns a Sunday, dates-as-prose belong to date_parse",
            "year")
    if year > Y_MAX:
        raise ComputusError(
            "year %d is outside the closed range of this contract "
            "(through %d — the civil window of the JDN bridge it "
            "travels)" % (year, Y_MAX), "year")
    if algorithm == ALGO_GREG:
        if year < Y_GREG_MIN:
            raise ComputusError(
                "year %d predates the Gregorian reform: the Gregorian "
                "Easter has been in use since 1583 — before that the "
                "computus in effect was the Julian one, and "
                "algorithm=julian_meeus is that contract (with "
                "date_julian_gregorian to state the day in both "
                "calendars)" % year, "year")
        out = easter_gregorian_computus(year)
    else:
        if year < Y_JUL_MIN:
            raise ComputusError(
                "year %d is outside the liturgical era this contract "
                "computes (1..%d): astronomical year 0 and negative "
                "years are date_julian_gregorian's numbering for days "
                "— no computus is modelled before year 1" % (year,
                                                             Y_MAX),
                "year")
        out = easter_julian_computus(year)

    return {
        "year": year,
        "algorithm": out["algorithm"],
        "computus": out["computus"],
        "easter_gregorian": out["easter_gregorian"],
        "easter_julian": out["easter_julian"],
        "jdn": out["jdn"],
        "weekday": out["weekday"],
        "golden_number": out["golden_number"],
        "golden_number_rule": GOLDEN_RULE,
        "intermediates": out["intermediates"],
        "offset_days": out["offset_days"],
        "offset_meaning": "gregorian civil day = julian civil day + "
                          "offset_days, for the same day",
        "scale": juliankit.SCALE,
        "table": {"name": juliankit.TABLE_NAME,
                  "version": juliankit.TABLE_VERSION,
                  "rule": juliankit.TABLE_RULE,
                  "sha256": juliankit.TABLE_SHA256},
        "procedure": {"name": PROCEDURE_NAME,
                      "version": PROCEDURE_VERSION,
                      "sha256": PROCEDURE_SHA256},
        "flags": [],
        "applied_defaults": [],
    }
