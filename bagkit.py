"""bagkit — /api/v1/money/baggage : mon sac passe-t-il en cabine ? LOI
vs CONVENTION DE MARQUE, choisies par la DATE DU VOL.

Le règlement (UE) 2026/2202 s'applique DU 23 OCTOBRE 2027 (signé
16-sept-2026, JO 2-oct-2026 — newsandstar). Avant cette date, la loi ne
fixe AUCUNE taille : chaque compagnie décide. Après, la loi fixe UNE
seule arête chiffrée : l'article personnel doit être accepté SOUS LE
SIÈGE GRATUITEMENT, jusqu'à 40×30×15 cm (« or less », subject to fitting
under the seat — The Age rejoué 22-nov-2026). La loi NE fixe PAS la
taille du sac à main de casier overhead (« the regulation does NOT set a
size limit for the carry-on baggage in the overhead compartment » — The
Age) et NE fixe PAS le poids de l'article personnel.

La presse se contredit et nos règles le disent : The Age et le
Parlement rendent « second bag subject to cabin capacity, chargeable »
(Standard : « not two free bags »), alors qu'AOL/Independent prêtent au
texte « dimensions cumulées ≤ 100 cm + 7 kg ». ARITHMÉTIQUE PUBLICHÉE :
le trolley standard 55×40×20 fait 115 cm cumulés — sous la lecture AOL,
chaque casier conventionnel serait hors la loi, OR la loi ne fixe pas
d'arête overhead : la règle « 100 cm cumulés » est une AFFIRMATION DE
PRESSE, rendue comme telle, testée contre les faits, jamais mélangée
avec la règle légale. Comparaison PAR DIMENSION (règle de rotation : un
pavé 40×18×30 passe dans un gabarit 40×30×20 — mêmes faces triées),
jamais par somme.

Les sizers transporteur (Ryanair 40×30×20, KLM 40×30×15, easyJet
45×36×20/56×45×25… table bymetz mesurée) sont des ARGUMENTS — jamais
fetchus, jamais devinés. regime est un argument, pas une déduction :
la règle suit LE DÉPART (aéroports UE) et l'arrivée hors-UE opérée par
un transporteur UE ; le départ UK n'est PAS couvert (Standard : easyJet
retour seulement). Le verdict légal est vide quand le texte est muet —
c'est une réponse, pas un silence.
"""

import re
from datetime import date
from decimal import Decimal

_APPLIES = date(2027, 10, 23)   # Reg. (EU) 2026/2202, application date
_PERSONAL_CAP = (40, 30, 15)    # loi : article personnel sous le siège
_REGIMES = {"EU", "UK", "other"}

_EXPECTED = {
    "flight_date": "ISO date 'YYYY-MM-DD' of the flight — before "
                   "2027-10-23 no EU size rule exists; on/after it the "
                   "40x30x15 personal-item cap applies",
    "regime": "'EU' (departing an EU airport, or arriving in the EU "
              "from outside operated by an EU carrier), 'UK' or "
              "'other' — never guessed; the rules follow the DEPARTURE "
              "and the operator, not the passenger",
    "bag": "'LxWxH' dimensions of your bag as measured (length x width "
           "x height, any order — rotation is checked), e.g. '55x40x20'",
    "bag_unit": "'cm' (default) or 'in' — inches convert at exactly 2.54",
    "weight_kg": "whole or decimal kg of the bag — the law sets no "
                 "weight cap for the personal item; only a supplied "
                 "carrier cap can judge it",
    "personal_sizer": "'LxWxH' the carrier's CURRENT personal-item "
                      "gauge, supplied by you (e.g. '40x30x20' Ryanair) "
                      "— never fetched, never guessed",
    "cabin_sizer": "'LxWxH' the carrier's overhead-bag gauge, supplied "
                   "by you (e.g. '55x40x23') — the law sets no size "
                   "limit here, so without this argument the answer is "
                   "undetermined, not 'yes'",
    "cabin_sum_limit": "'158' style sum-in-cm limit if your carrier "
                       "publishes one — rendered as the CARRIER's rule; "
                       "the press 'EU 100 cm' figure is not law and "
                       "never keys a verdict",
    "cabin_weight_max": "kg limit your carrier publishes (e.g. '10') — "
                        "carrier rule, the law sets none for the "
                        "personal item",
}


class BagError(ValueError):
    def __init__(self, field, message, expected=None):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected or _EXPECTED.get(field, "")


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise BagError(field, "missing or empty (pass the string)")
    return value.strip()


def _date(value):
    t = _text(value, "flight_date")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", t):
        raise BagError("flight_date", "not an ISO date: %r" % value)
    try:
        return date.fromisoformat(t)
    except ValueError:
        raise BagError("flight_date", "not a real calendar day: %r"
                       % value)


def _dims(value, field):
    t = _text(value, field).lower().replace("×", "x").replace(" ", "")
    parts = t.split("x")
    if len(parts) != 3:
        raise BagError(field, "want 'LxWxH' three numbers, got %r"
                       % value)
    out = []
    for p in parts:
        if not re.match(r"^\d+(\.\d+)?$", p):
            raise BagError(field, "dimension not a positive number: %r"
                           % p)
        out.append(Decimal(p))
    return tuple(out)


def _num(value, field):
    t = _text(value, field)
    if not re.match(r"^\d+(\.\d+)?$", t):
        raise BagError(field, "not a positive number: %r" % value)
    return Decimal(t)


def _to_cm(dims, unit):
    if unit == "in":
        return tuple((d * Decimal("2.54")).quantize(Decimal("0.01"))
                     for d in dims)
    return dims


def _fits(bag_cm, sizer_cm):
    """Règle de rotation axis-aligned : faces triées, comparaison
    dimension à dimension. Un pavé 40x18x30 passe dans 40x30x20."""
    b = sorted(bag_cm)
    s = sorted(sizer_cm)
    per = [{"bag": str(b[i]), "gauge": str(s[i]), "fits": b[i] <= s[i]}
           for i in range(3)]
    return all(p["fits"] for p in per), per


_PERSONAL_LIMBS = [
    "the 40x30x15 cm cap is the SAFE HARBOUR for the under-seat item "
    "(The Age: 'maximum size of the underseat bag at 40x30x15, or "
    "less'); whether the bag physically fits under YOUR seat is an "
    "aircraft fact the law makes a condition — not decided here",
    "weight of the personal item: NOT prescribed by law (The Age); "
    "only a supplied carrier cap can judge it",
    "the second (overhead) bag: must be PERMITTED 'subject to the "
    "capacity of the aircraft cabin' (Art. as reported by The "
    "Independent) — the regulation sets NO size limit there (The "
    "Age); whether it is FREE is contested in the press (Evening "
    "Standard: 'not two free bags — airlines may still charge')",
    "fares INCLUDING a hand-baggage allowance must be DISPLAYED by "
    "default before booking starts (newsandstar, Regulation price-"
    "transparency article) — a display duty, not a size rule",
]

_PRESS_CONTRADICTIONS = [
    {"claim": "two free pieces of luggage guaranteed from 2027-10-23",
     "as_said_by": "The Age ('entitled to ... two pieces, free of "
                    "extra charge')",
     "against": "Evening Standard ('the new rules do NOT guarantee "
                 "two free bags — airlines may still charge for the "
                 "cabin bag') and the text's 'subject to cabin "
                 "capacity' limb"},
    {"claim": "EU caps overhead bags at 100 cm combined (and 7 kg)",
     "as_said_by": "AOL / Independent quoting Parliament",
     "against": "the regulation sets no overhead size (The Age) — "
                "and the standard 55x40x20 trolley sums to 115 cm, "
                "so the '100 cm' reading would outlaw every normal "
                "cabin case; arithmetically tested, never adopted"},
]


def run_baggage(args):
    fdate = _date(args.get("flight_date"))
    regime = _text(args.get("regime"), "regime").upper()
    if regime not in _REGIMES:
        raise BagError("regime", "must be 'EU', 'UK' or 'other', got %r"
                       % args.get("regime"))
    unit = (args.get("bag_unit") or "cm").strip().lower()
    if unit not in ("cm", "in"):
        raise BagError("bag_unit", "must be 'cm' or 'in', got %r"
                       % args.get("bag_unit"))
    bag = _to_cm(_dims(args.get("bag"), "bag"), unit)

    law_applies = (regime == "EU" and fdate >= _APPLIES)
    dims_cm = [{"face": ["length", "width", "height"][i],
                "cm": str(bag[i])} for i in range(3)]
    total_cm = sum(bag, Decimal(0)).normalize()

    # ---- la part LOI (article personnel sous le siège)
    if regime == "EU" and fdate < _APPLIES:
        law = {"stage": "before-application",
               "applies_from": _APPLIES.isoformat(),
               "personal_cap_cm": None,
               "note": "Until 2027-10-23 each airline decides the "
                       "free-bag rules (money-tourism); no EU size "
                       "limit exists yet for any cabin bag"}
        personal_law = None
    elif law_applies:
        cap = tuple(Decimal(c) for c in _PERSONAL_CAP)
        ok, per = _fits(bag, cap)
        law = {"stage": "amended-2026/2202",
               "applies_from": _APPLIES.isoformat(),
               "personal_cap_cm": "40x30x15",
               "overhead_cap_cm": None,
               "overhead_note": "the regulation does NOT set a size "
                                "limit for the overhead bag (The Age)"}
        personal_law = {"within_legal_safe_harbour": ok,
                        "per_dimension": per,
                        "verdict": ("FREE under the seat by law"
                                    if ok else
                                    "EXCEEDS the 40x30x15 safe "
                                    "harbour — whether it still fits "
                                    "under the seat is an aircraft "
                                    "fact; else carrier terms rule")}
    else:
        law = {"stage": "not-covered",
               "applies_from": _APPLIES.isoformat(),
               "personal_cap_cm": None,
               "note": ("UK departures are outside Reg. (EU) 2026/2202 "
                        "(Evening Standard: easyJet applies it on "
                        "return legs only — the rule follows the "
                        "departure airport and the operator); "
                        "carrier terms alone decide")
                       if regime == "UK" else
                       "regime 'other': no EU rule applies; carrier "
                       "terms alone decide"}
        personal_law = None

    # ---- la part CONVENTION (sizers fournis)
    carrier = {}
    if args.get("personal_sizer"):
        ps = _to_cm(_dims(args["personal_sizer"], "personal_sizer"),
                    _units_of(args, "personal_sizer", unit))
        ok, per = _fits(bag, ps)
        carrier["personal_vs_sizer"] = {
            "sizer_cm": "x".join(str(d) for d in ps),
            "fits": ok, "per_dimension": per,
            "rule": "carrier's published gauge, rotation allowed — "
                    "not law"}
    if args.get("cabin_sizer"):
        cs = _to_cm(_dims(args["cabin_sizer"], "cabin_sizer"),
                    _units_of(args, "cabin_sizer", unit))
        ok, per = _fits(bag, cs)
        carrier["cabin_vs_sizer"] = {
            "sizer_cm": "x".join(str(d) for d in cs),
            "fits": ok, "per_dimension": per,
            "rule": "carrier gauge; the law sets no overhead size"}
    if args.get("cabin_sum_limit"):
        lim = _num(args["cabin_sum_limit"], "cabin_sum_limit")
        carrier["cabin_vs_sum"] = {
            "bag_sum_cm": str(total_cm), "limit_cm": str(lim),
            "passes": total_cm <= lim,
            "rule": "sum-of-dimensions is a CARRIER convention style; "
                    "it is NOT in the regulation (the press 'EU 100 "
                    "cm' figure never keys this verdict)"}
    if args.get("cabin_weight_max") and args.get("weight_kg"):
        w = _num(args["weight_kg"], "weight_kg")
        m = _num(args["cabin_weight_max"], "cabin_weight_max")
        carrier["weight_vs_cap"] = {
            "bag_kg": str(w), "cap_kg": str(m), "passes": w <= m,
            "rule": "carrier cap; the law prescribes no weight for "
                    "the under-seat item (The Age)"}

    out = {
        "flight_date": fdate.isoformat(), "regime": regime,
        "bag_cm": "x".join(str(d) for d in bag),
        "bag_dims": dims_cm, "bag_sum_cm": str(total_cm),
        "law": law, "personal_law": personal_law, "carrier": carrier,
        "press_contradictions": _PRESS_CONTRADICTIONS,
        "legal_limbs": _PERSONAL_LIMBS,
        "scope_note": "carrier sizers are SUPPLIED, never fetched; "
                      "no gauge supplied + law silent = UNDETERMINED, "
                      "we do not guess an airline's current rule; "
                      "this is arithmetic against published texts, "
                      "not legal advice",
    }
    return out


def _units_of(args, field, default_unit):
    # les sizers sont toujours publiés en cm ; bag_unit ne convertit
    # que le sac de l'utilisateur. Retourne 'cm' systématiquement.
    return "cm"
