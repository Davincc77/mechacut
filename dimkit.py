# -*- coding: utf-8 -*-
"""dimkit — /api/v1/ship/dimweight : le POIDS FACTURE d'un colis.

La douleur mesuree (docs/DEMAND-QUEUE, cycle 15h50 + 17h52) : deux
calculateurs publies (rollo vs amzprep) donnent 35 lb et 34,5 lb des
MEMES pouces 20x20x12 — la divergence n'est pas l'arithmetique, c'est
L'ORDRE des arrondis : chaque dimension au pouce superieur AVANT le
volume, volume ÷ diviseur, puis livres AU PALIER superieur. Et le
diviseur lui-meme POURRIT : USPS est passe de 166 a 139 le 12 juillet
2026 (table rollo publiee). Donc :

  - AUCUNE table de transporteur embarquee — divisor, seuils, paliers,
    plafond sont des ARGUMENTS (doctrine « les tables pourrissent »,
    money/points et flight_comp font pareil) ;
  - la CHAINE est rendue etape par etape, chaque valeur en Fraction
    exacte a cote du decimal (le 34,5 d'amzprep est une TRONCATURE de
    4800/139 = 34.53237... — nous rendons la fraction et le palier) ;
  - le piege publie « dimensions en mm avec diviseur imperial = DIM
    x16,4 trop gros » est rendu IMPOSSIBLE par contrat : le diviseur
    porte son unite (in3_lb | cm3_kg) et chaque cote est converti par
    les facteurs DEFINIS EXACTS (1 in = 25.4 mm pile, 1 lb =
    453.59237 g pile), conversions NOMMEES dans les etapes.

Specs citees : US Publication 526 / tarifs USPS dim weight (>1 pi3 =
1728 in3, division 139, poids arondi au palier superieur, max 70 lb) ;
UPS/FedEx dim divisor 139 in3/lb — les VALEURS restent des arguments,
la GRAMMAIRE de la chaine est la regle publique que les modeles fondent
(ils divisent avant d'arrondir les dimensions, ou n'arrondissent pas
les livres).

Tout est Fraction ; les decimales sont rendues a 10 chiffres avec
ROUND_HALF_EVEN sous localcontext ferme — memes octets pour toujours.
"""
from fractions import Fraction

DIM_UNITS = ("in", "cm", "mm")
MASS_UNITS = ("lb", "kg", "g", "oz")
DIV_UNITS = ("in3_lb", "cm3_kg")
DIM_ROUNDS = ("ceil", "none")
STEPS = ("1", "0.5", "0.25", "none")
MAX_RULES = 6

# facteurs DEFINIS EXACTS (par definition legale, pas de memoire)
IN_PER = {"in": Fraction(1), "cm": Fraction(100, 254), "mm": Fraction(10, 254)}
# masse -> grammes
G_PER = {"lb": Fraction("453.59237"), "kg": Fraction(1000), "g": Fraction(1),
         "oz": Fraction("28.349523125")}
VOL_UNIT_PER_DIV = {"in3_lb": "in3", "cm3_kg": "cm3"}
MASS_OF_RULE = {"in3_lb": "lb", "cm3_kg": "kg"}

_DEC_PLACES = 10


class DimError(Exception):
    def __init__(self, field, message, expected):
        Exception.__init__(self, message)
        self.field = field
        self.message = message
        self.expected = expected


def _frac(text, field):
    try:
        return Fraction(str(text))
    except (ValueError, ZeroDivisionError):
        raise DimError(field, "not a number: %r" % (text,),
                       "a decimal string like '20.5' — all values are "
                       "strings, never JSON numbers")


def _dec(value):
    """Fraction -> rendu ferme : un entier en notation entiere (jamais
    5.0000000000 pour un poids facture), sinon 10 chiffres HALF_EVEN
    sous localcontext ferme — memes octets pour toujours, jamais de E
    en affichage (lecon num/round)."""
    if value.denominator == 1:
        return str(value.numerator)
    import decimal
    with decimal.localcontext() as ctx:
        ctx.prec = 40
        ctx.rounding = decimal.ROUND_HALF_EVEN
        d = decimal.Decimal(value.numerator) / decimal.Decimal(
            value.denominator)
        return str(d.quantize(decimal.Decimal("1." + "0" * _DEC_PLACES),
                              rounding=decimal.ROUND_HALF_EVEN))


def _ceil_to(value, step):
    """Plafond de value au palier step (Fraction exactes)."""
    if step == 0:
        raise DimError("rules.weight_step", "step zero", "one of 1|0.5|0.25|none")
    return ((value / step).__ceil__()) * step


def _norm(text):
    import unicodedata
    return unicodedata.normalize("NFKC", str(text))


def run_dimweight(args):
    """Coeur pur : args (dict, pydantic deja passe) -> dict de reponse.
    Erreurs = DimError(field, message, expected), la reponse 400 les
    rend comme reparation (champ + attendu + exemple)."""
    dims = args.get("dims")
    actual = args.get("actual_weight")
    rules = args.get("rules")
    as_of = args.get("as_of")
    if not isinstance(dims, dict):
        raise DimError("dims", "missing", "{l, w, h, unit} — unit one of "
                                          "in|cm|mm")
    if not isinstance(actual, dict):
        raise DimError("actual_weight", "missing", "{value, unit} — unit "
                                                  "one of lb|kg|g|oz")
    if not isinstance(rules, list) or not rules:
        raise DimError("rules", "missing", "a list of 1..%d carrier rules"
                                           % MAX_RULES)
    if len(rules) > MAX_RULES:
        raise DimError("rules", "too many rules (%d > %d)"
                       % (len(rules), MAX_RULES),
                       "at most %d rules per call — compare a few "
                       "carriers, then call again" % MAX_RULES)

    try:
        unit = _norm(dims.get("unit", "")).lower()
    except Exception:
        unit = ""
    if unit not in DIM_UNITS:
        raise DimError("dims.unit", "unknown unit %r" % (dims.get("unit"),),
                       "one of in|cm|mm — closed set, nothing guessed")
    dl = _frac(_norm(dims.get("l")), "dims.l")
    dw = _frac(_norm(dims.get("w")), "dims.w")
    dh = _frac(_norm(dims.get("h")), "dims.h")
    for name, d in (("dims.l", dl), ("dims.w", dw), ("dims.h", dh)):
        if d <= 0:
            raise DimError(name, "dimension not positive: %s" % d,
                           "a positive number string — a box of zero "
                           "does not ship")
    mval = _frac(_norm(actual.get("value")), "actual_weight.value")
    munit = _norm(actual.get("unit", "")).lower()
    if munit not in MASS_UNITS:
        raise DimError("actual_weight.unit",
                       "unknown unit %r" % (actual.get("unit"),),
                       "one of lb|kg|g|oz")
    if mval < 0:
        raise DimError("actual_weight.value", "negative weight",
                       "a non-negative number string")
    if as_of is not None:
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", _norm(as_of) or ""):
            raise DimError("as_of", "not a date: %r" % (as_of,),
                           "YYYY-MM-DD — the date the carrier table was "
                           "read; the tables themselves stay arguments "
                           "(USPS 166->139 changed ON 2026-07-12)")

    results = []
    for i, r in enumerate(rules):
        if not isinstance(r, dict):
            raise DimError("rules[%d]" % i, "not an object",
                           "{name, divisor, divisor_unit, dim_round, "
                           "weight_step, min_volume?, cap?}")
        rname = _norm(r.get("name", "") or ("rule-%d" % (i + 1)))
        dunit = _norm(r.get("divisor_unit", "")).lower()
        if dunit not in DIV_UNITS:
            raise DimError("rules[%d].divisor_unit" % i,
                           "unknown divisor unit %r"
                           % (r.get("divisor_unit"),),
                           "one of in3_lb (cubic inches per pound) | "
                           "cm3_kg (cubic centimetres per kilogram) — "
                           "the divisor carries its OWN unit, that is "
                           "what kills the mm-into-139 trap (x16.4)")
        divisor = _frac(_norm(r.get("divisor")), "rules[%d].divisor" % i)
        if divisor <= 0:
            raise DimError("rules[%d].divisor" % i, "divisor not positive",
                           "e.g. '139' with divisor_unit in3_lb — the "
                           "VALUE is yours, we embed no carrier table "
                           "(they rot)")
        dr = _norm(r.get("dim_round", "")).lower()
        if dr not in DIM_ROUNDS:
            raise DimError("rules[%d].dim_round" % i,
                           "unknown dim_round %r" % (r.get("dim_round"),),
                           "'ceil' (each dimension to the next whole "
                           "unit BEFORE the volume — the published "
                           "rule) or 'none'")
        step = _norm(r.get("weight_step", "")).lower()
        if step not in STEPS:
            raise DimError("rules[%d].weight_step" % i,
                           "unknown weight_step %r"
                           % (r.get("weight_step"),),
                           "one of 1|0.5|0.25|none — ceiling of the "
                           "billable weight to that palier; 'none' is "
                           "amzprep's shape (prints 34.5 where the "
                           "carrier contract says 35)")
        vunit = VOL_UNIT_PER_DIV[dunit]
        mass_of_rule = MASS_OF_RULE[dunit]

        steps = []
        # 1. dimensions normalisees dans le systeme de la REGLE, par les
        #    facteurs DEFINIS exacts (1 in = 25.4 mm pile) — c'est la
        #    garde structurelle du piege publie « mm ÷ 139 » : l'unite du
        #    diviseur est DECLAREE, la conversion est NOMMEE, le melange
        #    est impossible.
        if vunit == "in3":
            f_long = IN_PER[unit]
        elif unit == "cm":
            f_long = Fraction(1)
        elif unit == "mm":
            f_long = Fraction(1, 10)
        else:  # in -> cm3 : facteur defini 2.54 cm/in
            f_long = Fraction("2.54")
        dims_r = []
        for label, d in (("L", dl), ("W", dw), ("H", dh)):
            conv_d = d * f_long
            if dr == "ceil":
                rounded = conv_d.__ceil__()
                dims_r.append(Fraction(rounded))
                steps.append({"step": "dimension %s" % label,
                              "exact": _dec(conv_d),
                              "rounded_up_to": str(rounded),
                              "rule": "ceil to next whole %s BEFORE "
                                      "volume" % vunit[:2]})
            else:
                dims_r.append(conv_d)
                steps.append({"step": "dimension %s" % label,
                              "exact": _dec(conv_d),
                              "rule": "no rounding (weight_step/dim_round "
                                      "= none)"})
        vol = dims_r[0] * dims_r[1] * dims_r[2]
        steps.append({"step": "volume", "value": _dec(vol),
                      "fraction": "%d/%d" % (vol.numerator, vol.denominator),
                      "unit": vunit,
                      "rule": "L x W x H after any dimension ceil"})

        # gate min_volume (USPS : dim weight ne s'applique que >1 ft3)
        applies = True
        if r.get("min_volume") is not None:
            mv = _frac(_norm(r.get("min_volume")),
                       "rules[%d].min_volume" % i)
            if mv < 0:
                raise DimError("rules[%d].min_volume" % i, "negative",
                               "a non-negative volume in %s" % vunit)
            applies = vol > mv
            steps.append({"step": "min_volume gate",
                          "threshold": _dec(mv), "unit": vunit,
                          "applies": applies,
                          "rule": "strictly greater than the threshold — "
                                  "USPS published rule: dim weight only "
                                  "over 1 cubic foot (1728 in3)"})
        dim_w = vol / divisor
        steps.append({"step": "dimensional weight",
                      "value": _dec(dim_w),
                      "fraction": "%d/%d" % (dim_w.numerator,
                                             dim_w.denominator),
                      "unit": mass_of_rule,
                      "rule": "volume ÷ divisor %s per %s — the divisor "
                              "you supplied, never a table we embed"
                              % (_dec(divisor), mass_of_rule)})
        actual_in_rule = mval * G_PER[munit] / G_PER[mass_of_rule]
        gate_note = None
        if applies:
            billable_raw = max(actual_in_rule, dim_w)
            which = ("dimensional" if dim_w >= actual_in_rule else "actual")
        else:
            billable_raw = actual_in_rule
            which = "actual"
            gate_note = ("below the min_volume threshold — this carrier "
                         "bills by actual weight; what it then CHARGES "
                         "(zone, flat rate) is LIVE and out of contract")
        steps.append({"step": "billable pre-round",
                      "value": _dec(billable_raw),
                      "fraction": "%d/%d" % (billable_raw.numerator,
                                             billable_raw.denominator),
                      "unit": mass_of_rule, "governs": which,
                      "actual_converted": _dec(actual_in_rule),
                      "rule": "max(actual, dimensional) — exact compare"})
        if step == "none":
            billable = billable_raw
            steps.append({"step": "palier", "rule": "none — printed raw "
                                                    "(the amzprep shape: "
                                                    "34.5 where the "
                                                    "contract rounds to "
                                                    "35)",
                          "value": _dec(billable)})
        else:
            billable = _ceil_to(billable_raw, Fraction(step))
            steps.append({"step": "palier",
                          "value": _dec(billable),
                          "rule": "ceil to the next %s %s — the rounding "
                                  "publishers SKIP between their 34.5 "
                                  "and the carrier's 35"
                                  % (step, mass_of_rule)})
        capped = False
        if r.get("cap") is not None:
            cp = _frac(_norm(r.get("cap")), "rules[%d].cap" % i)
            if cp <= 0:
                raise DimError("rules[%d].cap" % i, "cap not positive",
                               "e.g. '70' (lb) — the published parcel "
                               "ceiling")
            if billable > cp:
                capped = True
                billable = cp
            steps.append({"step": "cap", "limit": _dec(cp),
                          "capped": capped, "unit": mass_of_rule,
                          "rule": "billed weight never exceeds the "
                                  "published ceiling"})
        results.append({
            "rule": rname,
            "billed_weight": _dec(billable),
            "unit": mass_of_rule,
            "billed_fraction": "%d/%d" % (billable.numerator,
                                          billable.denominator),
            "governs": which,
            "dim_applies": applies,
            "capped": capped,
            "grams_for_ranking": _dec(billable * G_PER[mass_of_rule]),
            "steps": steps,
            "gate_note": gate_note,
        })

    order = sorted(results, key=lambda r: (Fraction(r["grams_for_ranking"]),
                                           _norm(r["rule"])))
    lightest = order[0] if order else None
    heaviest = order[-1] if order else None
    diverge = (lightest and heaviest and
               Fraction(lightest["grams_for_ranking"])
               != Fraction(heaviest["grams_for_ranking"]))
    out = {
        "dims": {"l": _norm(dims.get("l")), "w": _norm(dims.get("w")),
                 "h": _norm(dims.get("h")), "unit": unit},
        "actual_weight": {"value": _norm(actual.get("value")),
                          "unit": munit},
        "results": results,
        "ranking": [{"rule": r["rule"], "billed_weight": r["billed_weight"],
                     "unit": r["unit"],
                     "grams": r["grams_for_ranking"]} for r in order],
        "verdict": ("rules DISAGREE on this box — the divergence is the "
                    "ROUNDING ORDER, both chains are printed above"
                    if diverge else
                    "all rules bill the same weight for this box"),
        "as_of": _norm(as_of) if as_of is not None else None,
        "scope_note": ("no carrier table is embedded: divisors, gates and "
                       "ceilings rot (USPS moved 166 -> 139 ON 2026-07-12) "
                       "— they are ARGUMENTS; and what a kg of billed "
                       "weight COSTS is the carrier's live price sheet, "
                       "out of contract here"),
    }
    return out
