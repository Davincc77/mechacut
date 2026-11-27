"""Bundle 136 — cvsskit: CVSS vector -> base score + severity band.

Two CLOSED, NAMED vintages, both declared in every response with a
table sha (serialization is documented in the payload and re-derivable
from the embedded dicts):

  * CVSS v3.1 — specification document (FIRST, read verbatim
    27-11-2026, https://www.first.org/cvss/v3.1/specification-document):
    Table 16 metric values, section 7.1 Base equations, section 5
    Table 14 qualitative scale, and the ROUNDUP helper named in 7:
    "Roundup returns the smallest number, specified to 1 decimal place,
    that is equal to or higher than its input" — implemented exactly so
    (ceil to one decimal over EXACT Decimal arithmetic: every v3.1 base
    product here is a finite decimal, so the float error Appendix A
    warns about never enters). The eight Base metrics; X ("Not Defined")
    exists only in Temporal/Environmental (Tables 15/17) — refused by
    name in base. Order: the v3.1 spec shows a VALID vector with the
    base metrics "in a non-preferred ordering" (section 6) — so v3.1
    accepts any order and echoes it normalized; v4.0 does not (below).

  * CVSS v4.0 — spec (https://www.first.org/cvss/v4.0/) + REFERENCE
    IMPLEMENTATION tables, embedded by script, never by hand:
    cvss_lookup.js (270 MacroVector scores), max_severity.js,
    max_composed.js, and the interpolation of cvss_score.js, all
    BSD-2-Clause "(c) FIRST, Red Hat, and contributors",
    https://github.com/FIRSTdotorg/cvss-v4-calculator (fetched
    27-11-2026). Spec Table 23, verbatim: "A vector string must
    contain metrics in the order shown in Table 23, every other
    ordering is invalid. All Base metrics must be included" — the 11
    Base metrics in order, enforced by name. Threat (E), Environmental
    (CR IR AR M*) and Supplemental (S AU R V RE U) metrics are OUT of
    this contract: presence refused by the metric name, and the spec's
    own default for omitted optional metrics (Not Defined; E:X scored
    as worst case E:A by m() of the reference implementation) is
    RENDERED as applied_defaults, never silent.

Same input -> same bytes. v3.1 exact Decimal + Roundup named; v4.0
IEEE-754 doubles in the EXACT operation order of cvss_score.js (the
published example scores ARE float outputs of that order — reproducing
the order IS the contract), final step named as in the reference
(Math.round(value*10)/10 = half-up, NOT Roundup; the vintages round
differently and the response says which). No network, no LLM.
"""
import hashlib
import json
import math
from decimal import Decimal, ROUND_CEILING

__all__ = ["CvssError", "base_score", "SEVERITY_BANDS", "ROUNDING_SET",
           "V31_TABLE_SHA256", "V40_TABLE_SHA256"]

# severity bands: v3.1 Table 14 == v4.0 Table 22 (identical ranges)
SEVERITY_BANDS = [("CRITICAL", Decimal("9.0"), Decimal("10.0")),
                  ("HIGH", Decimal("7.0"), Decimal("8.9")),
                  ("MEDIUM", Decimal("4.0"), Decimal("6.9")),
                  ("LOW", Decimal("0.1"), Decimal("3.9")),
                  ("NONE", Decimal("0.0"), Decimal("0.0"))]

ROUNDING_SET = {"3.1": "Roundup (v3.1 spec 7: smallest 1-decimal value "
                       ">= input; exact-decimal arithmetic here)",
                "4.0": "round-to-1-decimal half-up (reference impl "
                       "Math.round(value*10)/10)"}


class CvssError(Exception):
    def __init__(self, field, reason, message, expected=None):
        self.field = field
        self.reason = reason
        self.message = message
        self.expected = expected
        super().__init__(message)


def _band(score):
    for name, lo, hi in SEVERITY_BANDS:
        if lo <= score <= hi:
            return name
    return "NONE"


def _d(x):
    return Decimal(x)


# --- v3.1 base weights: Table 16, read from the spec -------------------
V31_AV = {"N": _d("0.85"), "A": _d("0.62"), "L": _d("0.55"), "P": _d("0.2")}
V31_AC = {"L": _d("0.77"), "H": _d("0.44")}
V31_PR = {"N": {"U": _d("0.85"), "C": _d("0.85")},
          "L": {"U": _d("0.62"), "C": _d("0.68")},
          "H": {"U": _d("0.27"), "C": _d("0.5")}}
V31_UI = {"N": _d("0.85"), "R": _d("0.62")}
V31_CIA = {"H": _d("0.56"), "L": _d("0.22"), "N": _d("0")}
V31_ORDER = ["AV", "AC", "PR", "UI", "S", "C", "I", "A"]
V31_VALUES = {"AV": set(V31_AV), "AC": set(V31_AC), "PR": set(V31_PR),
              "UI": set(V31_UI), "S": {"U", "C"},
              "C": set(V31_CIA), "I": set(V31_CIA), "A": set(V31_CIA)}
V31_OTHER = {"E", "RL", "RC", "CR", "IR", "AR", "MAV", "MAC", "MPR",
             "MUI", "MS", "MC", "MI", "MA"}


def _roundup(x):
    """v3.1 spec 7 Roundup, exact."""
    if x <= 0:
        return Decimal("0.0")
    return (x * 10).to_integral_value(rounding=ROUND_CEILING) / 10


def _score31(m):
    iss = Decimal(1) - (
        (Decimal(1) - V31_CIA[m["C"]]) * (Decimal(1) - V31_CIA[m["I"]])
        * (Decimal(1) - V31_CIA[m["A"]]))
    scope = m["S"]
    if scope == "U":
        impact = _d("6.42") * iss
    else:
        impact = (_d("7.52") * (iss - _d("0.029"))
                  - _d("3.25") * (iss - _d("0.02")) ** 15)
    expl = (_d("8.22") * V31_AV[m["AV"]] * V31_AC[m["AC"]]
            * V31_PR[m["PR"]][scope] * V31_UI[m["UI"]])
    if impact <= 0:
        bs = Decimal("0.0")
    elif scope == "U":
        bs = _roundup(min(impact + expl, Decimal(10)))
    else:
        bs = _roundup(min(_d("1.08") * (impact + expl), Decimal(10)))
    return bs, {"iss": str(iss), "impact": str(impact),
                "exploitability": str(expl)}


def _canon31():
    return hashlib.sha256(json.dumps(
        {"AV": {k: str(x) for k, x in V31_AV.items()},
         "AC": {k: str(x) for k, x in V31_AC.items()},
         "PR": {k: {s: str(x) for s, x in v.items()}
                for k, v in V31_PR.items()},
         "UI": {k: str(x) for k, x in V31_UI.items()},
         "CIA": {k: str(x) for k, x in V31_CIA.items()},
         "constants": ["8.22", "6.42", "7.52", "0.029", "0.02", "1.08",
                       "exponent-15"]},
        sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


V31_TABLE_SHA256 = _canon31()

# --- v4.0 closed tables (generated from the reference repo) ------------
V40_LOOKUP = json.loads(
    '{"000000":10.0,"000001":9.9,"000010":9.8,"000011":9.5,"000020":9.5,"0000'
    '21":9.2,"000100":10.0,"000101":9.6,"000110":9.3,"000111":8.7,"000120":9.'
    '1,"000121":8.1,"000200":9.3,"000201":9.0,"000210":8.9,"000211":8.0,"0002'
    '20":8.1,"000221":6.8,"001000":9.8,"001001":9.5,"001010":9.5,"001011":9.2'
    ',"001020":9.0,"001021":8.4,"001100":9.3,"001101":9.2,"001110":8.9,"00111'
    '1":8.1,"001120":8.1,"001121":6.5,"001200":8.8,"001201":8.0,"001210":7.8,'
    '"001211":7.0,"001220":6.9,"001221":4.8,"002001":9.2,"002011":8.2,"002021'
    '":7.2,"002101":7.9,"002111":6.9,"002121":5.0,"002201":6.9,"002211":5.5,"'
    '002221":2.7,"010000":9.9,"010001":9.7,"010010":9.5,"010011":9.2,"010020"'
    ':9.2,"010021":8.5,"010100":9.5,"010101":9.1,"010110":9.0,"010111":8.3,"0'
    '10120":8.4,"010121":7.1,"010200":9.2,"010201":8.1,"010210":8.2,"010211":'
    '7.1,"010220":7.2,"010221":5.3,"011000":9.5,"011001":9.3,"011010":9.2,"01'
    '1011":8.5,"011020":8.5,"011021":7.3,"011100":9.2,"011101":8.2,"011110":8'
    '.0,"011111":7.2,"011120":7.0,"011121":5.9,"011200":8.4,"011201":7.0,"011'
    '210":7.1,"011211":5.2,"011220":5.0,"011221":3.0,"012001":8.6,"012011":7.'
    '5,"012021":5.2,"012101":7.1,"012111":5.2,"012121":2.9,"012201":6.3,"0122'
    '11":2.9,"012221":1.7,"100000":9.8,"100001":9.5,"100010":9.4,"100011":8.7'
    ',"100020":9.1,"100021":8.1,"100100":9.4,"100101":8.9,"100110":8.6,"10011'
    '1":7.4,"100120":7.7,"100121":6.4,"100200":8.7,"100201":7.5,"100210":7.4,'
    '"100211":6.3,"100220":6.3,"100221":4.9,"101000":9.4,"101001":8.9,"101010'
    '":8.8,"101011":7.7,"101020":7.6,"101021":6.7,"101100":8.6,"101101":7.6,"'
    '101110":7.4,"101111":5.8,"101120":5.9,"101121":5.0,"101200":7.2,"101201"'
    ':5.7,"101210":5.7,"101211":5.2,"101220":5.2,"101221":2.5,"102001":8.3,"1'
    '02011":7.0,"102021":5.4,"102101":6.5,"102111":5.8,"102121":2.6,"102201":'
    '5.3,"102211":2.1,"102221":1.3,"110000":9.5,"110001":9.0,"110010":8.8,"11'
    '0011":7.6,"110020":7.6,"110021":7.0,"110100":9.0,"110101":7.7,"110110":7'
    '.5,"110111":6.2,"110120":6.1,"110121":5.3,"110200":7.7,"110201":6.6,"110'
    '210":6.8,"110211":5.9,"110220":5.2,"110221":3.0,"111000":8.9,"111001":7.'
    '8,"111010":7.6,"111011":6.7,"111020":6.2,"111021":5.8,"111100":7.4,"1111'
    '01":5.9,"111110":5.7,"111111":5.7,"111120":4.7,"111121":2.3,"111200":6.1'
    ',"111201":5.2,"111210":5.7,"111211":2.9,"111220":2.4,"111221":1.6,"11200'
    '1":7.1,"112011":5.9,"112021":3.0,"112101":5.8,"112111":2.6,"112121":1.5,'
    '"112201":2.3,"112211":1.3,"112221":0.6,"200000":9.3,"200001":8.7,"200010'
    '":8.6,"200011":7.2,"200020":7.5,"200021":5.8,"200100":8.6,"200101":7.4,"'
    '200110":7.4,"200111":6.1,"200120":5.6,"200121":3.4,"200200":7.0,"200201"'
    ':5.4,"200210":5.2,"200211":4.0,"200220":4.0,"200221":2.2,"201000":8.5,"2'
    '01001":7.5,"201010":7.4,"201011":5.5,"201020":6.2,"201021":5.1,"201100":'
    '7.2,"201101":5.7,"201110":5.5,"201111":4.1,"201120":4.6,"201121":1.9,"20'
    '1200":5.3,"201201":3.6,"201210":3.4,"201211":1.9,"201220":1.9,"201221":0'
    '.8,"202001":6.4,"202011":5.1,"202021":2.0,"202101":4.7,"202111":2.1,"202'
    '121":1.1,"202201":2.4,"202211":0.9,"202221":0.4,"210000":8.8,"210001":7.'
    '5,"210010":7.3,"210011":5.3,"210020":6.0,"210021":5.0,"210100":7.3,"2101'
    '01":5.5,"210110":5.9,"210111":4.0,"210120":4.1,"210121":2.0,"210200":5.4'
    ',"210201":4.3,"210210":4.5,"210211":2.2,"210220":2.0,"210221":1.1,"21100'
    '0":7.5,"211001":5.5,"211010":5.8,"211011":4.5,"211020":4.0,"211021":2.1,'
    '"211100":6.1,"211101":5.1,"211110":4.8,"211111":1.8,"211120":2.0,"211121'
    '":0.9,"211200":4.6,"211201":1.8,"211210":1.7,"211211":0.7,"211220":0.8,"'
    '211221":0.2,"212001":5.3,"212011":2.4,"212021":1.4,"212101":2.4,"212111"'
    ':1.2,"212121":0.5,"212201":1.0,"212211":0.3,"212221":0.1}'
)

V40_MAXSEV = json.loads(
    '{"eq1":{"0":1,"1":4,"2":5},"eq2":{"0":1,"1":2},"eq3eq6":{"0":{"0":7,"1":'
    '6},"1":{"0":8,"1":8},"2":{"1":10}},"eq4":{"0":6,"1":5,"2":4},"eq5":{"0":'
    '1,"1":1,"2":1}}'
)

V40_MAXCOMPOSED = json.loads(
    '{"eq1":{"0":["AV:N/PR:N/UI:N/"],"1":["AV:A/PR:N/UI:N/","AV:N/PR:L/UI:N/"'
    ',"AV:N/PR:N/UI:P/"],"2":["AV:P/PR:N/UI:N/","AV:A/PR:L/UI:P/"]},"eq2":{"0'
    '":["AC:L/AT:N/"],"1":["AC:H/AT:N/","AC:L/AT:P/"]},"eq3":{"0":{"0":["VC:H'
    '/VI:H/VA:H/CR:H/IR:H/AR:H/"],"1":["VC:H/VI:H/VA:L/CR:M/IR:M/AR:H/","VC:H'
    '/VI:H/VA:H/CR:M/IR:M/AR:M/"]},"1":{"0":["VC:L/VI:H/VA:H/CR:H/IR:H/AR:H/"'
    ',"VC:H/VI:L/VA:H/CR:H/IR:H/AR:H/"],"1":["VC:L/VI:H/VA:L/CR:H/IR:M/AR:H/"'
    ',"VC:L/VI:H/VA:H/CR:H/IR:M/AR:M/","VC:H/VI:L/VA:H/CR:M/IR:H/AR:M/","VC:H'
    '/VI:L/VA:L/CR:M/IR:H/AR:H/","VC:L/VI:L/VA:H/CR:H/IR:H/AR:M/"]},"2":{"1":'
    '["VC:L/VI:L/VA:L/CR:H/IR:H/AR:H/"]}},"eq4":{"0":["SC:H/SI:S/SA:S/"],"1":'
    '["SC:H/SI:H/SA:H/"],"2":["SC:L/SI:L/SA:L/"]},"eq5":{"0":["E:A/"],"1":["E'
    ':P/"],"2":["E:U/"]}}'
)

def _canon40():
    return hashlib.sha256(
        ("\n".join("%s:%r" % (k, V40_LOOKUP[k]) for k in sorted(V40_LOOKUP))
         + "\n" + json.dumps(V40_MAXSEV, sort_keys=True,
                              separators=(",", ":"))
         + "\n" + json.dumps(V40_MAXCOMPOSED, sort_keys=True,
                              separators=(",", ":"))).encode("utf-8")
    ).hexdigest()


V40_TABLE_SHA256 = _canon40()
V40_TABLE_SERIAL = ("sha256 over UTF-8: lookup lines \"key:repr(score)\" "
                    "sorted by key joined by \n, then the max_severity.js "
                    "object text, then the max_composed.js object text, "
                    "\n-joined")

"""Tail of cvsskit.py: v4.0 port + shared vector parsing / base_score."""

V40_ORDER = ["AV", "AC", "AT", "PR", "UI", "VC", "VI", "VA",
             "SC", "SI", "SA"]
V40_BASE_VALUES = {"AV": ["N", "A", "L", "P"], "AC": ["L", "H"],
                   "AT": ["N", "P"], "PR": ["N", "L", "H"],
                   "UI": ["N", "P", "A"], "VC": ["H", "L", "N"],
                   "VI": ["H", "L", "N"], "VA": ["H", "L", "N"],
                   "SC": ["H", "L", "N"], "SI": ["H", "L", "N"],
                   "SA": ["H", "L", "N"]}
# metric names of the optional groups, refused by name (Table 23):
V40_THREAT = ["E"]
V40_ENV = ["CR", "IR", "AR", "MAV", "MAC", "MAT", "MPR", "MUI",
           "MVC", "MVI", "MVA", "MSC", "MSI", "MSA"]
V40_SUPP = ["S", "AU", "R", "V", "RE", "U"]

# value orderings of cvss_score.js (index = severity rank, tenths)
_LV = {"AV": {"N": 0.0, "A": 0.1, "L": 0.2, "P": 0.3},
       "PR": {"N": 0.0, "L": 0.1, "H": 0.2},
       "UI": {"N": 0.0, "P": 0.1, "A": 0.2},
       "AC": {"L": 0.0, "H": 0.1},
       "AT": {"N": 0.0, "P": 0.1},
       "VC": {"H": 0.0, "L": 0.1, "N": 0.2},
       "VI": {"H": 0.0, "L": 0.1, "N": 0.2},
       "VA": {"H": 0.0, "L": 0.1, "N": 0.2},
       "SC": {"H": 0.1, "L": 0.2, "N": 0.3},
       "SI": {"S": 0.0, "H": 0.1, "L": 0.2, "N": 0.3},
       "SA": {"S": 0.0, "H": 0.1, "L": 0.2, "N": 0.3},
       "CR": {"H": 0.0, "M": 0.1, "L": 0.2},
       "IR": {"H": 0.0, "M": 0.1, "L": 0.2},
       "AR": {"H": 0.0, "M": 0.1, "L": 0.2},
       "E": {"U": 0.2, "P": 0.1, "A": 0.0}}


def _m(v, metric):
    """cvss_score.js m(): E:X->A worst case, CR/IR/AR:X->H."""
    sel = v.get(metric, "X")
    if metric == "E" and sel == "X":
        return "A"
    if metric in ("CR", "IR", "AR") and sel == "X":
        return "H"
    return sel


def _macro_vector(v):
    """cvss_score.js macroVector(): the six EQ memberships."""
    if (_m(v, "AV") == "N" and _m(v, "PR") == "N" and _m(v, "UI") == "N"):
        eq1 = "0"
    elif (( _m(v, "AV") == "N" or _m(v, "PR") == "N"
            or _m(v, "UI") == "N")
          and not (_m(v, "AV") == "N" and _m(v, "PR") == "N"
                   and _m(v, "UI") == "N")
          and _m(v, "AV") != "P"):
        eq1 = "1"
    else:
        eq1 = "2"
    eq2 = "0" if (_m(v, "AC") == "L" and _m(v, "AT") == "N") else "1"
    if _m(v, "VC") == "H" and _m(v, "VI") == "H":
        eq3 = "0"
    elif (_m(v, "VC") == "H" or _m(v, "VI") == "H" or _m(v, "VA") == "H"):
        eq3 = "1"
    else:
        eq3 = "2"
    if _m(v, "SC") == "H" or _m(v, "SI") == "H" or _m(v, "SA") == "H":
        eq4 = "1"
    else:
        eq4 = "2"
    eq5 = {"A": "0", "P": "1", "U": "2"}[_m(v, "E")]
    if ((_m(v, "CR") == "H" and _m(v, "VC") == "H")
            or (_m(v, "IR") == "H" and _m(v, "VI") == "H")
            or (_m(v, "AR") == "H" and _m(v, "VA") == "H")):
        eq6 = "0"
    else:
        eq6 = "1"
    return eq1 + eq2 + eq3 + eq4 + eq5 + eq6


def _extract_value(metric, s):
    """cvss_score.js extractValueMetric()."""
    i = s.index(metric)
    rest = s[i + len(metric) + 1:]
    j = rest.find("/")
    return rest if j < 0 else rest[:j]


def _score40(v):
    """cvss_score.js, operation order preserved on IEEE-754 doubles."""
    if all(v.get(k) == "N" for k in
           ("VC", "VI", "VA", "SC", "SI", "SA")):
        return 0.0, {"macro": "no-impact-shortcut"}
    macro = _macro_vector(v)
    value = V40_LOOKUP[macro]
    eq = [int(c) for c in macro]
    e1, e2, e3, e4, e5, e6 = eq

    def key(a, b, c, d, e, f):
        return "%d%d%d%d%d%d" % (a, b, c, d, e, f)

    l1 = V40_LOOKUP.get(key(e1 + 1, e2, e3, e4, e5, e6))
    l2 = V40_LOOKUP.get(key(e1, e2 + 1, e3, e4, e5, e6))
    if e3 == 0 and e6 == 0:
        l3a = V40_LOOKUP.get(key(e1, e2, e3, e4, e5, e6 + 1))
        l3b = V40_LOOKUP.get(key(e1, e2, e3 + 1, e4, e5, e6))
        # JS: (left > right) ? left : right — an undefined right wins
        # the comparison as false, and undefined > any is false; an
        # undefined survivor means NaN-skipping downstream. Reproduce.
        if l3b is None:
            l3 = None
        elif l3a is not None and l3a > l3b:
            l3 = l3a
        else:
            l3 = l3b
    elif e3 == 1 and e6 == 1:
        l3 = V40_LOOKUP.get(key(e1, e2, e3 + 1, e4, e5, e6))
    elif e3 == 0 and e6 == 1:
        l3 = V40_LOOKUP.get(key(e1, e2, e3 + 1, e4, e5, e6))
    elif e3 == 1 and e6 == 0:
        l3 = V40_LOOKUP.get(key(e1, e2, e3, e4, e5, e6 + 1))
    else:
        l3 = V40_LOOKUP.get(key(e1, e2, e3 + 1, e4, e5, e6 + 1))
    l4 = V40_LOOKUP.get(key(e1, e2, e3, e4 + 1, e5, e6))
    l5 = V40_LOOKUP.get(key(e1, e2, e3, e4, e5 + 1, e6))

    # highest-severity vectors of the MacroVector, composed per EQ
    eq1_maxes = V40_MAXCOMPOSED["eq1"][str(e1)]
    eq2_maxes = V40_MAXCOMPOSED["eq2"][str(e2)]
    eq36 = V40_MAXCOMPOSED["eq3"][str(e3)]
    eq3eq6_maxes = eq36.get(str(e6)) or eq36.get(e6)
    eq4_maxes = V40_MAXCOMPOSED["eq4"][str(e4)]
    eq5_maxes = V40_MAXCOMPOSED["eq5"][str(e5)]
    if eq3eq6_maxes is None:
        raise CvssError("vector", "macro_unsupported",
                        "MacroVector %s: the reference table has no "
                        "highest vectors for eq3=%d,eq6=%d"
                        % (macro, e3, e6))
    max_vectors = [a + b + c + d + e
                   for a in eq1_maxes for b in eq2_maxes
                   for c in eq3eq6_maxes for d in eq4_maxes
                   for e in eq5_maxes]
    dists = None
    for mv in max_vectors:
        d = {}
        ok = True
        for met in ("AV", "PR", "UI", "AC", "AT", "VC", "VI", "VA",
                    "SC", "SI", "SA", "CR", "IR", "AR"):
            dd = _LV[met][_m(v, met)] - _LV[met][_extract_value(met, mv)]
            if dd < 0:
                ok = False
                break
            d[met] = dd
        if ok:
            dists = d
            break
    if dists is None:  # reference falls through on the last candidate
        raise CvssError("vector", "macro_unsupported",
                        "no highest-severity vector dominates %s"
                        % macro)

    cur1 = dists["AV"] + dists["PR"] + dists["UI"]
    cur2 = dists["AC"] + dists["AT"]
    cur3 = (dists["VC"] + dists["VI"] + dists["VA"] + dists["CR"]
            + dists["IR"] + dists["AR"])
    cur4 = dists["SC"] + dists["SI"] + dists["SA"]

    step = 0.1
    ms1 = V40_MAXSEV["eq1"][str(e1)] * step
    ms2 = V40_MAXSEV["eq2"][str(e2)] * step
    ms3 = V40_MAXSEV["eq3eq6"][str(e3)][str(e6)] * step
    ms4 = V40_MAXSEV["eq4"][str(e4)] * step

    macro_score = repr(value)
    n = 0
    norm = 0.0
    for lower, cur, msv in ((l1, cur1, ms1), (l2, cur2, ms2),
                            (l3, cur3, ms3), (l4, cur4, ms4)):
        if lower is None:
            continue
        n += 1
        norm += (value - lower) * (cur / msv)
    if l5 is not None:      # eq5: percentage is always 0, but counted
        n += 1

    mean = 0.0 if n == 0 else norm / n
    value -= mean
    if value < 0:
        value = 0.0
    if value > 10:
        value = 10.0
    final = math.floor(value * 10 + 0.5) / 10
    return final, {"macro": macro, "macro_score": macro_score,
                   "mean_distance": repr(mean)}


# --- shared front -------------------------------------------------------
def base_score(vector):
    """CVSS vector -> base score + named severity band + named rounding
    function + closed-table vintage. Grammar breaks are refused BY NAME."""
    if not isinstance(vector, str) or not vector.strip():
        raise CvssError("vector", "empty_vector",
                        "the vector string is empty")
    if len(vector) > 512:
        raise CvssError("vector", "vector_too_long",
                        "vector is %d characters; the named cap is 512"
                        % len(vector))
    if "  " in vector or vector != vector.strip():
        raise CvssError("vector", "whitespace",
                        "double spaces and surrounding space are "
                        "refused by name")
    parts = vector.split("/")
    prefix, rest = parts[0], parts[1:]
    if prefix not in ("CVSS:3.1", "CVSS:4.0"):
        raise CvssError("vector", "vector_prefix",
                        "'%s' is not a supported vintage: this build "
                        "carries the CLOSED tables for CVSS v3.1 and "
                        "v4.0 only (v2.0 and v3.0 vectors are NOT "
                        "re-scored here — silently reinterpreting a "
                        "v2 vector as v3.1 is how wrong bands get "
                        "published)" % prefix,
                        expected="CVSS:3.1/... or CVSS:4.0/...")
    version = "3.1" if prefix == "CVSS:3.1" else "4.0"

    m, seen = {}, []
    for p in rest:
        if p.count(":") != 1:
            raise CvssError("vector", "component_grammar",
                            "'%s' is not a NAME:VALUE component "
                            "(expected e.g. AV:N)" % p)
        k, val = p.split(":")
        if k != k.upper() or val != val.upper():
            raise CvssError("vector", "case_sensitive",
                            "'%s' at position %d: metric names and "
                            "values are CASE-SENSITIVE (spec vector "
                            "section: 'case sensitive')" % (p, len(seen) + 1),
                            expected="%s:%s" % (k.upper(), val.upper()))
        if k in seen:
            raise CvssError("vector", "duplicate_metric",
                            "'%s' appears twice (a vector must not "
                            "include the same metric more than once)"
                            % k)
        seen.append(k)
        m[k] = val

    if version == "3.1":
        _parse31(m, seen)
        bs, trace = _score31(m)
        score_s = "%.1f" % bs
        ordered = {k: m[k] for k in V31_ORDER}
        out = {"version": "3.1",
               "source": "https://www.first.org/cvss/v3.1/"
                         "specification-document",
               "table": {"name": "CVSS-V31-BASE-WEIGHTS",
                         "vintage": "v3.1 (FIRST spec, Table 16 read "
                                    "27-11-2026)",
                         "serialization": ("sha256 over UTF-8 of the "
                                           "sorted-keys JSON of the "
                                           "weight dicts + constants"),
                         "sha256": V31_TABLE_SHA256},
               "metrics": ordered,
               "order_note": ("the v3.1 spec shows a VALID vector in "
                              "non-preferred order (section 6: 'with the "
                              "metrics in a non-preferred ordering') — "
                              "order is echoed normalized, never refused"),
               "score": score_s,
               "severity": _band(Decimal(score_s)),
               "rounding": ROUNDING_SET["3.1"],
               "computation": {"formulas": "sec.7.1: ISS=1-[(1-C)(1-I)(1-A)];"
                               " S:U Impact=6.42*ISS; S:C Impact=7.52*"
                               "(ISS-0.029)-3.25*(ISS-0.02)^15; Expl=8.22*"
                               "AV*AC*PR*UI; S:U BaseScore=Roundup(min("
                               "Impact+Expl,10)); S:C =Roundup(min(1.08*"
                               "(Impact+Expl),10))",
                            "arithmetic": "exact Decimal (finite products),"
                            " never binary64",
                            **trace}}
        return out

    _parse40(m, seen)
    final, trace = _score40(m)
    score_s = "%.1f" % final
    out = {"version": "4.0",
           "source": "https://github.com/FIRSTdotorg/cvss-v4-calculator"
                     " (BSD-2-Clause, (c) FIRST, Red Hat, and "
                     "contributors)",
           "table": {"name": "CVSS-V40-MACROVECTOR",
                     "vintage": "v4.0 (reference tables fetched "
                                "27-11-2026)",
                     "macros": len(V40_LOOKUP),
                     "sha256": V40_TABLE_SHA256},
           "metrics": {k: m[k] for k in V40_ORDER},
           "score": score_s,
           "severity": _band(Decimal(score_s)),
           "rounding": ROUNDING_SET["4.0"],
           "computation": {"algorithm": "macrovector interpolation, "
                           "cvss_score.js operation order (IEEE-754 "
                           "doubles), named",
                           **trace},
           "applied_defaults": [
               "E:X (absent) is SCORED AS E:A worst case — m() of the "
               "reference implementation; a vector WITH E is refused by "
               "name (that is the base+threat contract, not built here)",
               "CR/IR/AR:X (absent) are scored as H — same m()"]}
    return out


def _parse31(m, seen):
    for k in seen:
        if k in V31_OTHER:
            raise CvssError("vector", "group_out_of_scope",
                            "'%s' is a Temporal/Environmental metric — "
                            "cvss_base_score computes the BASE group "
                            "only (v3.1 sec.7.2/7.3 are other contracts, "
                            "not built here)" % k,
                            expected="AV AC PR UI S C I A (8, base)")
        if k not in V31_VALUES:
            raise CvssError("vector", "unknown_metric",
                            "'%s' is not a v3.1 metric (closed set: AV "
                            "AC PR UI S C I A; temporal E RL RC and "
                            "environmental M* are refused by name)" % k)
    missing = [k for k in V31_ORDER if k not in m]
    if missing:
        raise CvssError("vector", "missing_metric",
                        "base metrics missing: %s — all 8 are required "
                        "(no Not-Defined for base metrics in v3.1 "
                        "tables)" % ", ".join(missing))
    for k, val in m.items():
        if val == "X":
            raise CvssError("vector", "not_defined_in_base",
                            "'%s:X' — Not Defined is not a BASE value "
                            "(X exists only in temporal/environmental "
                            "groups)" % k)
        if val not in V31_VALUES[k]:
            raise CvssError("vector", "bad_value",
                            "'%s:%s' is not a closed value of %s"
                            % (k, val, "v3.1"))


def _parse40(m, seen):
    for k in seen:
        grp = None
        if k in V40_ORDER:
            continue
        if k in V40_THREAT:
            grp = "Threat"
        elif k in V40_ENV:
            grp = "Environmental"
        elif k in V40_SUPP:
            grp = "Supplemental"
        if grp is not None:
            raise CvssError("vector", "group_out_of_scope",
                            "'%s' is a %s metric — cvss_base_score is "
                            "the BASE group only (Table 23: all Base "
                            "metrics mandatory, the other groups are "
                            "other contracts, not built here). Omit %s "
                            "for the base reading" % (k, grp, k),
                            expected="AV AC AT PR UI VC VI VA SC SI SA "
                                     "(11, base, in Table-23 order)")
        else:
            raise CvssError("vector", "unknown_metric",
                            "'%s' is not a v4.0 metric name" % k)
    # spec order of judgment, worked the wrong-way: completeness BEFORE
    # order (the spec's own invalid-vector example for a missing VA is
    # NAMED "Mandatory metric 'VA' is missing", not mis-ordered)
    missing = [k for k in V40_ORDER if k not in m]
    if missing:
        raise CvssError("vector", "missing_metric",
                        "Base metrics missing: %s (all 11 are mandatory "
                        "in v4.0 — spec Table 23)" % ", ".join(missing))
    base_in = [k for k in seen if k in V40_ORDER]
    if base_in != V40_ORDER:
        raise CvssError("vector", "metric_order",
                        "Base metrics out of Table-23 order: got %s, "
                        "expected %s — 'every other ordering is invalid'"
                        % ("/".join(base_in), "/".join(V40_ORDER)),
                        expected="/".join(V40_ORDER))
    for k in V40_ORDER:
        val = m[k]
        if val == "X":
            raise CvssError("vector", "not_defined_in_base",
                            "'%s:X' — the Base group has no Not-Defined "
                            "value (X belongs to the optional groups)"
                            % k,
                            expected=" | ".join(V40_BASE_VALUES[k]))
        if val not in V40_BASE_VALUES[k]:
            raise CvssError("vector", "bad_value",
                            "'%s:%s' is not a closed value of %s"
                            % (k, val, "v4.0"))
