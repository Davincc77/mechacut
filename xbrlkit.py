# -*- coding: utf-8 -*-
"""xbrl_decimals_calc_consistency — la loi des decimals absente du
voisin (registre L17, reçu proposeur 980850a4…27d8).

Contrat d'admission, purpose VERBATIM de la compilation des rapports de
campagne (l. 1480) : « XBRL summation check under declared decimals:
fact intervals, Calc 1.1 overlap verdict and XBRL 2.1 rounded-sum
verdict, both named ». Douleur mesuree (l. 1359, 1367, 1373) :
invoice_validate_totals refuse le champ decimals (400 body.decimals),
force tout au centime (« 14849000000.00 » pour un fait a -6) et rend
SCBSM FY2026 ProfitLoss 13833000 vs 13828000 + 6000 CONTRADICTED
-1000,00 la ou l'intervalle Calc 1.1 dit coherent — la porte ne sait
pas distinguer les deux lectures. Cet outil rend les DEUX verdicts,
NOMMES, avec les intervalles des faits.

References publiees nommees :
  - XBRL Calculations 1.1, Recommendation 22 February 2023,
    https://www.xbrl.org/Specification/calculation-1.1/REC-2023-02-22/
    rounded fact value interval (§5.2.3) : pour {value} v et {decimals}
    fini d, [v - 0.5*10^(0-d), v + 0.5*10^(0-d)] ; decimals « infinity »
    -> intervalle ponctuel [v, v] ; cohérent ssi l'intervalle calcule
    du total CT RECOUPE l'intervalle rapporte RT (§5.2.5) ; arcrole
    1.1 = https://xbrl.org/2023/arcrole/summation-item ;
  - XBRL 2.1 §5.2.5.2 (lecture nommee par le contrat d'admission) :
    la SOMME des valeurs des items est ARRONDIE aux decimals du total
    puis comparee au total ; le mode de largeur d'un tie n'est pas
    fige par 2.1 — cette porte dit le sien (half-up, away from zero) ;
  - XBRL 2.1 §4.6.7 : la valeur d'un fait doit etre compatible avec
    ses decimals (v * 10^d entier — le scale check rejoue par la
    campagne, 66/66 OK).

Golds TRACES MAIN depuis les filings reels cites (l. 1359, 1407-1412) :
  SCBSM FY2026 ProfitLoss (triplement tague fact_495308/495522/
  fact_495580, decimals -3) : total 13833000 -> [13832500, 13833500],
  parties 13828000 + 6000 -> [13833000, 13835000] — RECOUPEMENT, donc
  Calc 1.1 COHERENT ; somme 13834000 != 13833000, donc XBRL 2.1
  INCOHERENT. Le second tag 13834000 rend les deux verdicts COHERENTS
  — le doublon du depot est exactement ce que la porte ne savait pas
  dire. Sodexo 303000000 = 304000000 + (-1000000) a -6 : intervalles
  [302500000, 303500000] vs [302000000, 304000000] — coherents des
  deux lois. GB FY2024 A = CA + NCA a INF : 406950 + 133425 = 540375
  != 910782 — incoherent des deux lois (la jambe manquante HeldForSale
  370407 est un artefact d'extraction du rapport, rendu comme CLAIM
  d'arithmetique dans le test, jamais fondu dans l'outil).

bornes du contrat (disent, jamais silencieuses) : decimals entier
-100..100 ou « INF » (les filings du corpus vivent a -6..0), 1..200
parties, valeurs <= 200 caracteres.
"""
import re
from fractions import Fraction as F

MAX_PARTS = 200
DEC_ABS_MAX = 100
VALUE_MAX_LEN = 200

REF_CALC11 = ("XBRL Calculations 1.1, Recommendation 2023-02-22 — "
              "rounded fact value interval [v-0.5*10^-d, v+0.5*10^-d] "
              "(INF -> [v,v]) and consistency iff CT overlaps RT; "
              "arcrole https://xbrl.org/2023/arcrole/summation-item")
REF_21 = ("XBRL 2.1 §5.2.5.2 reading named by the intake contract: the "
          "sum of item values rounded to the total's decimals (this "
          "door: half-up away from zero, said) then compared to the "
          "total's value")
REF_467 = ("XBRL 2.1 §4.6.7 — a fact's value must be compatible with "
           "its declared decimals (value * 10^decimals is an integer); "
           "the campaign's scale check (66 values) replays this rule")

_DEC_RE = re.compile(r"-?\d+\Z")
_VALUE_RE = re.compile(r"-?\d+(?:\.\d+)?\Z")
class XbrlKitError(Exception):
    def __init__(self, field, msg):
        self.field = field
        self.msg = msg
        super().__init__(msg)


def _decimals(raw, field):
    """-> None for INF, else int. Refus NOMMES hors contrat."""
    if isinstance(raw, bool):
        raise XbrlKitError(field,
                           "%s: decimals is an integer or the string "
                           "'INF' — booleans are not decimals" % field)
    if isinstance(raw, int):
        d = raw
    elif isinstance(raw, str) and _DEC_RE.match(raw.strip()):
        d = int(raw.strip())
    elif isinstance(raw, str) and raw.strip().upper() == "INF":
        return None
    else:
        raise XbrlKitError(field,
                           "%s: decimals is an integer -100..100 or "
                           "the string 'INF', as the filing writes it"
                           % field)
    if not -DEC_ABS_MAX <= d <= DEC_ABS_MAX:
        raise XbrlKitError(field,
                           "%s: decimals is -100..100 or 'INF' (the "
                           "corpus lives at -6..0; the bound is this "
                           "door's closed contract, said not silent)"
                           % field)
    return d


def _value(raw, field):
    if isinstance(raw, bool) or isinstance(raw, float):
        raise XbrlKitError(field,
                           "%s: pass the value STRING exactly as the "
                           "filing writes it (e.g. \"296089.0\") — "
                           "binary64 would claim a precision the "
                           "filing never stated" % field)
    if isinstance(raw, int):
        s = str(raw)
    elif isinstance(raw, str) and _VALUE_RE.match(raw.strip()):
        s = raw.strip()
    else:
        raise XbrlKitError(field,
                           "%s: value is a plain decimal string or "
                           "integer (no exponent, no thousands "
                           "separator) — xBRL-JSON writes facts "
                           "exactly like \"13828000\"" % field)
    if len(s) > VALUE_MAX_LEN:
        raise XbrlKitError(field,
                           "%s: value is at most %d characters"
                           % (field, VALUE_MAX_LEN))
    return F(s), s


def _interval(v, d):
    """Calc 1.1 §5.2.3 rounded fact value interval."""
    if d is None:                 # INF -> single point
        return v, v
    h = F(1, 2) * (F(10) ** (-d))
    return v - h, v + h


def _half_up_away(k):
    """Half-up, ties AWAY FROM ZERO (the tie rule 2.1 leaves open —
    this door says which one it applied)."""
    fl = k.numerator // k.denominator
    rem = k - fl
    if rem > F(1, 2):
        return fl + 1
    if rem == F(1, 2):
        return fl + 1 if k > 0 else fl
    return fl


def _dec_str(fr):
    if fr.denominator == 1:
        return str(fr.numerator)
    # denominator is a power of 10
    n, den = fr.numerator, fr.denominator
    digits = ""
    while den % 10 == 0:
        den //= 10
        digits += "0"
    sign = "-" if n < 0 else ""
    n = abs(n)
    s = str(n).rjust(len(digits) + 1, "0")
    return sign + s[:-len(digits)] + "." + s[-len(digits):]


def check(total, parts):
    """total: {"value":…, "decimals":…}; parts: list of the same shape.
    Returns the closed response; refusals raise XbrlKitError(field)."""
    if not isinstance(total, dict):
        raise XbrlKitError("total",
                           "total: an object with value and decimals — "
                           "the reported total fact")
    stray = sorted(set(total) - {"value", "decimals"})
    if stray:
        raise XbrlKitError(
            "total.%s" % stray[0],
            "total: a fact is {value, decimals} only — '%s' is not "
            "summed (unit/currency is an echo, never a term; the "
            "neighbor invoice_validate_totals only echoes it too)"
            % stray[0])
    if not isinstance(parts, list) or not parts:
        raise XbrlKitError("parts",
                           "parts: a non-empty list of summation-item "
                           "facts (each {value, decimals}) — 1..200 "
                           "items")
    if len(parts) > MAX_PARTS:
        raise XbrlKitError("parts",
                           "parts: at most %d summation items in one "
                           "call" % MAX_PARTS)
    td = _decimals(total.get("decimals"), "total.decimals")
    tv, tv_s = _value(total.get("value"), "total.value")
    if td is not None:
        sc = tv * (F(10) ** td)
        if sc.denominator != 1:
            raise XbrlKitError("total.value",
                               "total.value: %s is finer than its "
                               "declared decimals %s — a fact must "
                               "agree with its own decimals tag "
                               "(XBRL 2.1 §4.6.7); fix the value or "
                               "the tag" % (tv_s, td))
    tlo, thi = _interval(tv, td)
    p_records = []
    s_lo = s_hi = F(0)
    s_exact = F(0)
    for i, p in enumerate(parts):
        if not isinstance(p, dict):
            raise XbrlKitError("parts[%d]" % i,
                               "parts[%d]: an object with value and "
                               "decimals" % i)
        stray = sorted(set(p) - {"value", "decimals"})
        if stray:
            raise XbrlKitError("parts[%d].%s" % (i, stray[0]),
                               "parts[%d]: a fact is {value, decimals} "
                               "only — '%s' is not summed"
                               % (i, stray[0]))
        pd = _decimals(p.get("decimals"), "parts[%d].decimals" % i)
        pv, pv_s = _value(p.get("value"), "parts[%d].value" % i)
        if pd is not None:
            sc = pv * (F(10) ** pd)
            if sc.denominator != 1:
                raise XbrlKitError("parts[%d].value" % i,
                                   "parts[%d].value: %s is finer than "
                                   "its declared decimals %s — a fact "
                                   "must agree with its own decimals "
                                   "tag (XBRL 2.1 §4.6.7); fix the "
                                   "value or the tag" % (i, pv_s, pd))
        lo, hi = _interval(pv, pd)
        p_records.append({"value": pv_s,
                          "decimals": "INF" if pd is None else str(pd),
                          "interval": [_dec_str(lo), _dec_str(hi)]})
        s_lo += lo
        s_hi += hi
        s_exact += pv
    # Calc 1.1: consistency iff the calculated total interval CT
    # overlaps the reported total interval RT (§5.2.5).
    calc11 = s_lo <= thi and tlo <= s_hi
    # XBRL 2.1 §5.2.5.2 (intake reading): round the sum to the total's
    # decimals, compare to the total's value.
    if td is None:
        rounded = s_exact
    else:
        q = F(10) ** (-td)
        rounded = _half_up_away(s_exact / q) * q
    v21 = rounded == tv
    return {
        "total": {"value": tv_s,
                  "decimals": "INF" if td is None else str(td),
                  "interval": [_dec_str(tlo), _dec_str(thi)]},
        "parts": p_records,
        "sum_exact": _dec_str(s_exact),
        "sum_interval": [_dec_str(s_lo), _dec_str(s_hi)],
        "verdicts": {
            "calc_1_1": "CONSISTENT" if calc11 else "INCONSISTENT",
            "xbrl_2_1": "CONSISTENT" if v21 else "INCONSISTENT",
        },
        "verdicts_differ": calc11 != v21,
        "rounded_sum_2_1": _dec_str(rounded),
        "delta_2_1": _dec_str(rounded - tv) if td is not None \
            else _dec_str(s_exact - tv),
        "rules": {"calc_1_1": REF_CALC11, "xbrl_2_1": REF_21,
                  "decimals_law": REF_467},
        "neighborhood": ("invoice_validate_totals refuses the decimals "
                         "field (400 body.decimals) and forces cents — "
                         "it cannot answer this question; this tool "
                         "never touches currency labels"),
    }
