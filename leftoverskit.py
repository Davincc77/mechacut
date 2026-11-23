# -*- coding: utf-8 -*-
"""leftoverskit — /api/v1/food/leftovers : la FENÊTRE DES RESTES,
sourcée USDA/FSIS. cooked_at/stored_at/frozen_at/as_of sont des
ARGUMENTS ; le module ne lit JAMAIS une horloge murale (parallèle
strict de poultry et du grand livre d'aging — la dérive de minuit
est publiée).

Douleur mesurée 23-nov-2026 (J-3 avant Thanksgiving, fenêtre utile
J+1..J+5) : la presse publie la règle en DUR — NBC New York (19-nov)
« eat them by Monday, Nov. 30 », ky3 (19-nov) « probably no more
than three days… 72 heures optimal » pour la même dinde, cupindy
(17-nov) « 3 to 4 days, so eat or freeze by Monday », r/Cooking
« eating the same carcass since Thanksgiving », r/AskACanadian
« 4 to 5 days » contre « maximum four days ». Les dates en dur sont
périmerces le 1er décembre ; le 3-contre-4 jours est la borne que
nous rendons en UNION nommée, jamais en premier-venu.

Ancrage (Q3 — citations verbatim, consultées 23-nov-2026) :
  * FSIS « Let's Talk Turkey — A Consumer Guide to Safely Roasting a
    Turkey », section Storing Your Leftovers (page last updated
    2023-11-17) : « Discard any turkey, stuffing, and gravy left out
    at room temperature longer than 2 hours; 1 hour in temperatures
    above 90 °F » ; « Use refrigerated turkey, stuffing, and gravy
    within 3 to 4 days » ; « If freezing leftovers, use within 2 to
    6 months for best quality » ; réchauffe « 165 °F » au
    thermomètre, « cooked turkey may be eaten cold ».
  * FSIS « Leftovers and Food Safety » (page last updated 2020-07-31),
    sections Danger Zone / Store / Reheat : « Throw away all
    perishable foods that have been left in room temperature for
    more than 2 hours (1 hour if the temperature is over 90 °F) » ;
    « Leftovers can be kept in the refrigerator for 3 to 4 days or
    frozen for 3 to 4 months. Although safe indefinitely, frozen
    leftovers can lose moisture and flavor… » ; « Reheat sauces,
    soups and gravies by bringing them to a rolling boil » ; la
    danger zone 40–140 °F.
  * LES DEUX PAGES FSIS SE CONTREDISENT sur le congélateur :
    2–6 mois (turkey) contre 3–4 mois (leftovers). doctrine poultry
    appliquée à la source : la fenêtre rendue est l'UNION des deux
    créneaux publiés (2 à 6 mois), chaque source citée à côté,
    boundary=True — jamais un créneau choisi en silence.

Doctrine :
  * HORS LISTE : les catégories sont les aliments NOMMÉS par la page
    turkey (turkey, stuffing, gravy) plus « leftovers » pour la règle
    générale de la page Leftovers ; toute autre catégorie est un
    refus nommé (pas de table par aliment inventée depuis les
    extensions d'États qui se contredisent — mash « 2–4 weeks » chez
    Penn State contre le 2–6 mois général).
  * > 2 heures est STRICT : 2 h pile passe (« longer than 2 hours »),
    2 h 01 jette — même grammaire que le « EXCEEDING 3 h » de la
    table flight_comp. warm_room=true bascule le seuil à 1 h
    (« over 90 °F »).
  * Sûreté ≠ qualité : le congélateur est « safe indefinitely » à
    0 °F ; la fenêtre 2–6 mois est QUALITÉ et le dit.
  * Le décompte part du JOUR de cuisson (« use within 3 to 4 days »
    suit le jetage à 2 h dont l'horloge part de la sortie de
    cuisson) ; si stored_at tombe un autre jour calendaire, la
    lecture alternative (départ au stockage) est PUBLIÉE dans
    fridge.counting_note, jamais substituée en silence.
"""
import calendar
from datetime import date, datetime, timedelta

CATEGORIES = ("turkey", "stuffing", "gravy", "leftovers")
FRIDGE_DAYS_MIN, FRIDGE_DAYS_MAX = 3, 4
FREEZE_MONTHS_MIN, FREEZE_MONTHS_MAX = 2, 6
OUT_LIMIT_H = 2
OUT_LIMIT_WARM_H = 1

SOURCE = (
    "USDA FSIS: 'Let's Talk Turkey' — Storing Your Leftovers "
    "(2023-11-17) and 'Leftovers and Food Safety' (2020-07-31); "
    "quotes verbatim, consulted 2026-11-23.")
THAWING_RULE = ("discard if left out longer than 2 hours at room "
                "temperature; 1 hour above 90 F / 32 C (FSIS, both "
                "pages)")
DANGER_ZONE = ("bacteria grow fastest between 40 F and 140 F; hot "
               "food must be kept at 140 F or warmer, cold perishable "
               "at 40 F or below (FSIS)")
FREEZER_SAFETY = ("safe indefinitely at 0 F held frozen — the window "
                  "below is BEST QUALITY (moisture and flavor), not "
                  "safety (FSIS Leftovers page, verbatim)")


class LeftoversError(Exception):
    def __init__(self, field, message, expected):
        self.field = field
        self.message = str(message)
        self.expected = expected
        super().__init__("%s: %s" % (field, message))


def _dt(args, field, required=True):
    raw = args.get(field)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        if required:
            raise LeftoversError(
                field,
                "absent — le module ne lit aucune horloge murale : "
                "sans ce point de départ il ne devine pas",
                "ISO naive like 2026-11-26T17:00 (same timezone "
                "throughout)")
        return None
    if not isinstance(raw, str):
        raise LeftoversError(field, "chaîne attendue",
                             "ISO string, no JSON date object")
    t = raw.strip()
    if "/" in t:
        raise LeftoversError(
            field, "date à slashes refusée — un jour ambigu déplace "
                   "la borne (précédent aging)",
            "ISO 8601 like 2026-11-26T17:00")
    if " " in t or t.endswith("Z") or "+" in t[10:]:
        raise LeftoversError(
            field, "fuseau ou espace non parse — naïves, même fuseau "
                   "sur tous les arguments (doctrine poultry)",
            "naive ISO local, e.g. 2026-11-26T17:00")
    try:
        return datetime.fromisoformat(t)
    except ValueError:
        raise LeftoversError(field, "ISO invalide",
                             "2026-11-26T17:00")


def _date_only(args, field):
    raw = args.get(field)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    t = raw.strip()
    try:
        d = date.fromisoformat(t)
    except ValueError:
        try:
            d = datetime.fromisoformat(t).date()
        except ValueError:
            raise LeftoversError(field, "date invalide",
                                 "2026-11-30 (or a naive datetime)")
    return d


def _fmt_h(fr_hours):
    s = ("%.4f" % float(fr_hours)).rstrip("0").rstrip(".")
    return s


def _add_months(d, k):
    """Arithmétique de MOIS calendaire avec clamp de fin de mois :
    2028-01-31 +2 = 2028-03-31 ; 2027-08-31 +6 = 2028-02-29 (bissexte
    — le 31 n'existe pas, on borne au dernier jour du mois cible)."""
    y, m = divmod((d.month - 1) + k, 12)
    y += d.year
    m += 1
    last = calendar.monthrange(y, m)[1]
    return date(y, m, min(d.day, last))


def run_leftovers(args):
    cat = args.get("category")
    if not isinstance(cat, str) or cat.strip().lower() not in CATEGORIES:
        raise LeftoversError(
            "category",
            "hors table FSIS nommée — pas de table par aliment "
            "inventée depuis des extensions d'États qui se "
            "contredisent",
            "|".join(CATEGORIES))
    cat = cat.strip().lower()

    warm = args.get("warm_room")
    if warm is None:
        warm = False
    if not isinstance(warm, bool):
        raise LeftoversError("warm_room", "booléen attendu",
                             "true|false (> 90 F / 32 C ambient)")

    cooked = _dt(args, "cooked_at")
    stored = _dt(args, "stored_at")
    if stored < cooked:
        raise LeftoversError(
            "stored_at", "avant cooked_at — l'horloge du 2 heures "
                         "part de la sortie de cuisson",
            "stored_at >= cooked_at")
    out_h = (stored - cooked) / timedelta(hours=1)
    limit = OUT_LIMIT_WARM_H if warm else OUT_LIMIT_H
    discarded = out_h > limit

    out = {
        "source": SOURCE,
        "category": cat,
        "cooked_at": cooked.isoformat(timespec="minutes"),
        "stored_at": stored.isoformat(timespec="minutes"),
        "two_hour_rule": {
            "hours_out": _fmt_h(out_h),
            "limit_hours": limit,
            "verdict": "DISCARD" if discarded else "WITHIN",
            "rule": THAWING_RULE,
            "boundary": "strict: longer than the limit discards; "
                        "exactly the limit passes",
        },
        "danger_zone": DANGER_ZONE,
    }
    if discarded:
        out["verdict"] = ("DISCARD — left out more than %d hour%s "
                          "before refrigeration; the fridge window "
                          "is not computed on food FSIS says to "
                          "throw away" % (limit, "s" if limit > 1 else ""))
        return out

    cday = cooked.date()
    low_day = cday + timedelta(days=FRIDGE_DAYS_MIN)
    high_day = cday + timedelta(days=FRIDGE_DAYS_MAX)
    out["fridge"] = {
        "days_min": FRIDGE_DAYS_MIN,
        "days_max": FRIDGE_DAYS_MAX,
        "use_by_first_reading": low_day.isoformat(),
        "last_day": high_day.isoformat(),
        "counting": "from the DAY of cooked_at — the 2-hour clock "
                    "starts at cooking and the 3-to-4-day rule "
                    "follows it in the same FSIS section",
        "counting_note": None,
        "rule": "use refrigerated leftovers within 3 to 4 days "
                "(both FSIS pages agree on this one)",
    }
    if stored.date() != cday:
        out["fridge"]["counting_note"] = (
            "stored_at falls on %s, a different calendar day: the "
            "alternative reading (count from storage) would end "
            "%s..%s — both published, neither chosen silently "
            "(union doctrine, like the poultry brackets)"
            % (stored.date().isoformat(),
               (stored.date() + timedelta(days=FRIDGE_DAYS_MIN)
                ).isoformat(),
               (stored.date() + timedelta(days=FRIDGE_DAYS_MAX)
                ).isoformat()))

    frozen = _dt(args, "frozen_at", required=False)
    if frozen is not None:
        # frozen_at accepte DATE ou DATETIME : un jour nu se compare
        # au jour (2026-08-31 n'est pas « avant » 2026-08-31T12:00,
        # c'est le même jour) ; une date-heure se compare en entier.
        raw_f = str(args.get("frozen_at")).strip()
        day_only = "T" not in raw_f and ":" not in raw_f
        if day_only:
            if frozen.date() < cooked.date():
                raise LeftoversError(
                    "frozen_at", "avant le jour de cuisson",
                    "frozen_at >= day of cooked_at")
        elif frozen < cooked:
            raise LeftoversError(
                "frozen_at", "avant cooked_at",
                "frozen_at >= cooked_at")
        fday = frozen.date()
        q_min = _add_months(fday, FREEZE_MONTHS_MIN)
        q_max = _add_months(fday, FREEZE_MONTHS_MAX)
        out["freezer"] = {
            "frozen_at": fday.isoformat(),
            "quality_from": q_min.isoformat(),
            "quality_by": q_max.isoformat(),
            "months_low": FREEZE_MONTHS_MIN,
            "months_high": FREEZE_MONTHS_MAX,
            "anchors": {"lets_talk_turkey": "2 to 6 months for "
                                            "best quality",
                        "leftovers_page": "frozen for 3 to 4 "
                                          "months"},
            "union_note": "the two FSIS pages publish DIFFERENT "
                          "quality windows; the window rendered is "
                          "their UNION, both anchors cited — "
                          "boundary=true by construction",
            "safety": FREEZER_SAFETY,
            "frozen_after_window": fday > high_day,
        }
        if fday > high_day:
            out["freezer"]["after_window_note"] = (
                "frozen after the 4-day fridge window (last day %s)"
                " — the freezer window is computed, but safety at "
                "the moment of freezing is not certifiable by this "
                "module" % high_day.isoformat())

    asof = _date_only(args, "as_of")
    if asof is not None:
        d = (asof - cday).days
        if d < 0:
            raise LeftoversError(
                "as_of", "avant le jour de cuisson — le module "
                         "refuse le voyage dans le temps",
                "as_of >= date of cooked_at")
        if d <= FRIDGE_DAYS_MIN:
            band, act = "WITHIN", "eat (or freeze) within the " \
                                  "published window"
        elif d == FRIDGE_DAYS_MAX:
            band, act = "LAST_DAY", "last published day: eat today " \
                                    "or it goes to the freezer"
        else:
            band, act = "EXPIRED", "discard unless it was frozen " \
                                   "inside the window"
        out["as_of"] = {
            "date": asof.isoformat(),
            "days_elapsed": d,
            "band": band,
            "action": act,
        }

    if cat == "gravy":
        out["reheat"] = ("sauces, soups and gravies: bring to a "
                         "ROLLING BOIL (FSIS Leftovers page, "
                         "verbatim)")
    else:
        out["reheat"] = ("reheat to 165 F as measured with a food "
                         "thermometer; cover and rotate (FSIS); "
                         + ("cooked turkey may be eaten cold "
                            "(Let's Talk Turkey)" if cat == "turkey"
                            else "stuffing center must also reach "
                                 "165 F (Let's Talk Turkey)"
                                 if cat == "stuffing" else
                                 "165 F is the judge, never the "
                                 "clock"))
    return out
