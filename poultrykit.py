# -*- coding: utf-8 -*-
"""poultrykit — /api/v1/food/poultry : la FENÊTRE de la dinde, sourcée
USDA/FSIS. L'heure du four est un ARGUMENT ; le module ne lit JAMAIS
une horloge murale (parallèle strict du grand livre d'aging — la
dérive de minuit est publiée).

Douleur mesurée 23-nov-2026 (J-3 de Thanksgiving, le 26) : ×8 pages
de calculateurs ont éclos le week-end (calcthis.co, roofandrouter,
cedarandledger, duneed.app, thawday.com, onlinelistmaker, foodsfork,
foodexpirytracker). TOUTES citent la MÊME table FSIS et se
contredisent pourtant sur le créneau : « 12 lb → into the fridge by
Mon Nov 23 11:00 » chez l'une (BAS du créneau, heure à l'air) contre
« the refrigerator date uses the long end » chez l'autre (HAUT du
créneau) pour le même poulet ; cuisson 14 lb : « 3 h to 3 h 45 » ici,
« 3¾ to 4¼ » là. Un seul chiffre affiché là où le publié est une
FENÊTRE : c'est le mensonge à dénominateur unique de unitprice, en
version calendrier. Les calculettes web sont du JS publicitaire sans
contrat, sans sha, sans rejouabilité.

Ancrage (Q3 — la table est citée, jamais réécrite de mémoire) :
  * FSIS « Let's Talk Turkey — A Consumer Guide to Safely Roasting a
    Turkey », fsis.usda.gov/…/lets-talk-turkey-roasting (consulté
    23-nov-2026) : « allow approximately 24 hours for every 4 to 5
    pounds » au frigo à 40 °F ou moins ; table 4–12 lb = 1–3 jours,
    12–16 = 3–4, 16–20 = 4–5, 20–24 = 5–6 ; « a thawed turkey can
    remain in the refrigerator for 1 to 2 days » ; eau froide ~30
    min/lb, eau changée toutes les 30 min, cuire IMMÉDIATEMENT après
    décongélation ; cuisson congelée « at least 50 percent longer » ;
    four « no lower than 325 °F » ; la sonde tranche : 165 °F à la
    partie la plus épaisse du blanc, la plus interne de la cuisse et
    de l'aile.
  * Tables de cuisson 325 °F (farcie/non) : FSIS « Turkey Basics:
    Safe Cooking » + « Turkey from Farm to Table », mêmes créneaux
    que le PDF Kitchen Companion (2020-12) et foodkeeping.gov /
    foodsafety.gov (vérification croisée 23-nov).
  * kg→lb : 1 lb = 453,59237 g pile (accord international 1959),
    même facteur que units.py — un seul dénominateur par nombre.

Doctrine :
  * HORS TABLE : < 4 lb ou > 24 lb whole-bird = refus NOMMÉ. La
    table publiée s'arrête là où elle s'arrête ; 165 °F est le seul
    juge du « cuit », jamais un chiffre extrapolé.
  * Bornes partagées : 14 est dans « 12 to 14 » ET « 14 to 18 » ; à
    une borne interne la fenêtre est l'UNION des créneaux voisins,
    boundary=True — jamais de premier-venu silencieux (plurivalence
    du routeur, appliquée à la table).
  * La fenêtre « au plus tard » prend le HAUT du créneau (conservatif,
    comme duneed) ; au plus tôt = au plus tard − jours de
    conservation (1–2 j FSIS).
"""
from datetime import datetime, timedelta
from fractions import Fraction

MODES = ("plan", "thaw", "cook")

# (lb_min, lb_max, val_min, val_max) — créneaux publiés, à l'identique
FRIDGE_DAYS = ((4, 12, Fraction(1), Fraction(3)),
               (12, 16, Fraction(3), Fraction(4)),
               (16, 20, Fraction(4), Fraction(5)),
               (20, 24, Fraction(5), Fraction(6)))
COLD_WATER_HOURS = ((4, 12, Fraction(2), Fraction(6)),
                    (12, 16, Fraction(6), Fraction(8)),
                    (16, 20, Fraction(8), Fraction(10)),
                    (20, 24, Fraction(10), Fraction(12)))
COOK_UNSTUFFED = ((4, 8, Fraction(3, 2), Fraction(13, 4)),
                  (8, 12, Fraction(11, 4), Fraction(3)),
                  (12, 14, Fraction(3), Fraction(15, 4)),
                  (14, 18, Fraction(15, 4), Fraction(17, 4)),
                  (18, 20, Fraction(17, 4), Fraction(9, 2)),
                  (20, 24, Fraction(9, 2), Fraction(5)))
COOK_STUFFED = ((6, 8, Fraction(5, 2), Fraction(7, 2)),
                (8, 12, Fraction(3), Fraction(7, 2)),
                (12, 14, Fraction(7, 2), Fraction(4)),
                (14, 18, Fraction(4), Fraction(17, 4)),
                (18, 20, Fraction(17, 4), Fraction(19, 4)),
                (20, 24, Fraction(19, 4), Fraction(21, 4)))
MIN_LB, MAX_LB = Fraction(4), Fraction(24)
HOLD_MAX_DAYS = 2  # « remain in the refrigerator for 1 to 2 days »
KG_TO_LB = Fraction(10**8, 45359237)   # 1959 : lb = 453,59237 g pile
G_TO_LB = KG_TO_LB / 1000

SOURCE = ("USDA FSIS: Let's Talk Turkey (roasting); Turkey Basics: "
          "Safe Cooking / Safe Thawing; Turkey from Farm to Table; "
          "Kitchen Companion PDF. Tables quoted verbatim, 2026-11-23.")
THERMOMETER = ("done is 165 F / 74 C at the thermometer, not the "
               "clock: thickest part of breast, innermost part of "
               "thigh, innermost part of wing (FSIS)")


class PoultryError(Exception):
    def __init__(self, field, message, expected):
        self.field = field
        self.message = message
        self.expected = expected
        super().__init__(f"{field}: {message}")


def _pounds(args):
    raw = args.get("weight")
    if not isinstance(raw, str) or not raw.strip():
        raise PoultryError("weight", "absent ou vide",
                           "STRING like '16' or '6.8'")
    t = raw.strip()
    if "," in t:
        raise PoultryError("weight", "virgule décimale refusée — "
                                     "ceci est une LOCALE, pas un "
                                     "nombre",
                           "decimal point; /api/v1/num/parse first")
    try:
        v = Fraction(t)
    except (ValueError, ZeroDivisionError):
        raise PoultryError("weight", "nombre invalide",
                           "decimal string like '16'")
    if v <= 0:
        raise PoultryError("weight", "poids nul ou négatif",
                           "a positive weight")
    unit = args.get("unit") or "lb"
    if unit == "lb":
        lb = v
    elif unit == "kg":
        lb = v * KG_TO_LB
    elif unit == "g":
        lb = v * G_TO_LB
    else:
        raise PoultryError("unit", "unité inconnue",
                           "lb|kg|g (1 lb = 453,59237 g pile, 1959)")
    if lb < MIN_LB or lb > MAX_LB:
        raise PoultryError("weight",
                           "hors table FSIS publiée : 4–24 lb "
                           "whole-bird, bornes incluses ; le module "
                           "n'extrapole pas",
                           "4 to 24 lb whole-bird (FSIS)")
    return lb


def _bracket(table, lb, unit_label):
    """Créneaux publiés : min des bas, max des hauts des lignes qui
    contiennent lb. Une valeur sur une borne interne touche DEUX
    lignes : boundary=True, la fenêtre est leur union — jamais un
    premier-venu silencieux (règle de plurivalence du routeur)."""
    vlo = vhi = None
    n = 0
    for lo, hi, a, b in table:
        if lo <= lb <= hi:
            n += 1
            vlo = a if vlo is None else min(vlo, a)
            vhi = b if vhi is None else max(vhi, b)
    if n == 0:
        raise PoultryError("weight",
                           "aucun créneau publié pour cette valeur "
                           "(%s)" % unit_label,
                           "inside the published brackets")
    return vlo, vhi, n > 1


def _fmt(v, unit):
    s = "%.4f" % float(v)  # float() = fonction déterministe du Fraction
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "%s %s" % (s, unit)


def _shift(oven, hours):
    """Heures exactes (multiples de 1/4 h dans les tables) -> ISO."""
    return oven + timedelta(seconds=int(hours * 3600))


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M")


def run_poultry(args):
    mode = args.get("mode") or "plan"
    if mode not in MODES:
        raise PoultryError("mode", "hors grammaire", "|".join(MODES))
    lb = _pounds(args)
    stuffed = args.get("stuffed")
    if stuffed is None:
        stuffed = False
    if not isinstance(stuffed, bool):
        raise PoultryError("stuffed", "booléen attendu", "true|false")

    f_lo, f_hi, f_b = _bracket(FRIDGE_DAYS, lb, "days")
    c_lo, c_hi, c_b = _bracket(COLD_WATER_HOURS, lb, "hours")
    table = COOK_STUFFED if stuffed else COOK_UNSTUFFED
    t_lo, t_hi, t_b = _bracket(table, lb, "hours")

    out = {
        "source": SOURCE,
        "weight_lb": _fmt(lb, "lb"),
        "thermometer": THERMOMETER,
        "refrigerator_days": {"min": _fmt(f_lo, "day" if f_lo == 1
                                          else "days"),
                              "max": _fmt(f_hi, "days"),
                              "boundary": f_b,
                              "rule": "approximately 24 hours for "
                                      "every 4 to 5 pounds, at 40 F "
                                      "or below (FSIS)"},
        "cold_water_hours": {"min": _fmt(c_lo, "hours"),
                             "max": _fmt(c_hi, "hours"),
                             "boundary": c_b,
                             "rule": "about 30 minutes per pound; "
                                     "change water every 30 minutes; "
                                     "cook IMMEDIATELY after "
                                     "thawing (FSIS)"},
        "cook_hours": {"min": _fmt(t_lo, "hours"),
                       "max": _fmt(t_hi, "hours"),
                       "boundary": t_b,
                       "stuffed": stuffed,
                       "oven": "no lower than 325 F (FSIS)",
                       "frozen_min": _fmt(t_lo * 3 / 2, "hours"),
                       "frozen_max": _fmt(t_hi * 3 / 2, "hours"),
                       "frozen_rule": "cook from frozen: at least "
                                      "50% longer (FSIS)"},
        "hold_after_thawing": "1 to 2 days, refrigerator only (FSIS)",
    }

    if mode == "thaw":
        out["mode"] = "thaw"
        return out
    if mode == "cook":
        out["mode"] = "cook"
        return out

    # mode plan : la FENÊTRE en ISO, calculée depuis l'heure DONNÉE
    oven = args.get("oven_at")
    if not isinstance(oven, str) or not oven.strip():
        raise PoultryError("oven_at", "absent — une fenêtre sans "
                                      "heure de four n'est pas une "
                                      "fenêtre ; le module ne lit "
                                      "aucune horloge murale",
                           "ISO like 2026-11-26T10:00")
    try:
        oven = datetime.fromisoformat(oven.strip())
    except ValueError:
        raise PoultryError("oven_at", "ISO invalide",
                           "2026-11-26T10:00 (naïve, même fuseau)")

    by = _shift(oven, -f_hi * 24)
    not_before = by - timedelta(hours=HOLD_MAX_DAYS * 24)
    cold_by = _shift(oven, -c_hi)
    out["mode"] = "plan"
    out["oven_at"] = _iso(oven)
    out["put_in_refrigerator"] = {
        "by": _iso(by),
        "not_before": _iso(not_before),
        "rule": "long end of the published days table; earlier than "
                "that the 1-to-2-day hold runs past the oven (FSIS)",
    }
    out["cold_water_fallback"] = {
        "by": _iso(cold_by),
        "rule": "high of the published hours table; cook IMMEDIATELY "
                "after thawing, so no window (FSIS)",
    }
    out["frozen_from_scratch"] = {
        "out_earliest": _iso(_shift(oven, t_lo * 3 / 2)),
        "out_latest": _iso(_shift(oven, t_hi * 3 / 2)),
        "rule": "at least 50% longer than the bracket (FSIS); the "
                "thermometer decides, never the clock",
    }
    out["done"] = {
        "earliest": _iso(_shift(oven, t_lo)),
        "latest": _iso(_shift(oven, t_hi)),
        "rule": "times are approximate; 165 F at the thermometer is "
                "the real judge (FSIS)",
    }

    as_of = args.get("as_of")
    if as_of is not None:
        try:
            now = datetime.fromisoformat(str(as_of).strip())
        except ValueError:
            raise PoultryError("as_of", "ISO invalide",
                               "2026-11-25T09:00")
        out["behind_schedule"] = {
            "fridge_still_possible": now <= by,
            "cold_water_still_possible": now <= cold_by,
            "frozen_still_possible": now <= oven,
            "rule": "all three doors come from the published tables; "
                    "if every one is false the bird is late, not the "
                    "grammar",
        }
    return out
