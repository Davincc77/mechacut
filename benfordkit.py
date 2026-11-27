"""benfordkit — bundle 134 (vague Grok 2, amas P-C, arbitrage Vince 27-11).

benford_digit_test : la table de conformite FERMEE BENFORD-NIGRINI2012-v1,
versionnee et hashee, nee des 49 statistiques mesurees via releveur
interne (blob de proposition sha256
f68fc7977cd586c429c9f7b9d5f96a0706d6933f36e4b9caa981e5612b40246e).

Entree : comptes de tests fermes (first_digit 9 bins / first_two 90 bins /
last_digit 10 bins / last_two 100 bins) + min/max. L'extraction des
chiffres est l'affaire de l'appelant (regles R-FT/R-POS/R-L2 dites hors
porte) ; ce que la porte gele, c'est l'attendu, le seuil, la bande, le
verdict.

Sortie : n, df, chi2 (2 dp), chi2_crit_05 (lu dans la table fermee
CHI2-CRIT-NISTEH-1.3.6.7.4-v1 de chi2kit — NommEE dans la reponse),
MAD (4 dp), bande Nigrini, verdict dans l'ensemble FERME a six noms :
CONFORMS / NONCONFORMITY / UNIFORM_REJECTED / UNIFORM_NOT_REJECTED /
SAMPLE_TOO_SMALL / SPAN_TOO_NARROW.

Lois closes, dites :
  EP = litteraux 16 decimales de log10(1+1/d) (la douleur n-1 de la
     campagne : la porte math_calc n'avait pas de log — ici la table
     EST l'attendu, versionnee et hashee).
  df : first_digit 8, first_two 89, last_digit 9, last_two 99.
  chi2 = somme (O - N.EP)^2 / (N.EP) en Decimal exact.
  MAD = somme |AP - EP| / K ; K = 9 / 90 / 10 / 100.
  Bandes MAD (Nigrini 2012 tabl. 7.1, v1 = borne SUPERIEURE INCLUSIVE,
  convention DECLAREE) :
    first_digit : CLOSE <= 0.006 < ACCEPTABLE <= 0.012 < MARGINAL
                  <= 0.015 < NONCONFORMITY
    first_two   : CLOSE <= 0.0012 < ACCEPTABLE <= 0.0018 < MARGINAL
                  <= 0.0022 < NONCONFORMITY
    last_digit / last_two : AUCUNE bande publiee — band=null dit,
                  mad rendu comme info ; verdict sur chi2 vs crit 0.05.
  Precedence du verdict (v1) : R-N1 -> R-SPAN -> statistique.
    R-N1   : n < 1000 -> SAMPLE_TOO_SMALL (statistiques quand meme rendues).
    R-SPAN : first_* exige max/min >= 10^4 -> SPAN_TOO_NARROW sinon.
    first_* : bande MAD NONCONFORMITY -> NONCONFORMITY, sinon CONFORMS.
    last_*  : chi2 > crit(0.05) -> UNIFORM_REJECTED sinon
              UNIFORM_NOT_REJECTED.
"""
import hashlib
import json
from decimal import Decimal as _D, ROUND_HALF_UP

from chi2kit import CRIT_TABLE_NAME, CRIT_TABLE_SHA, critical,     CRIT_SOURCE_SHA_PUBLISHED

TABLE_NAME = "BENFORD-NIGRINI2012-v1"
VERDICTS = ("CONFORMS", "NONCONFORMITY", "UNIFORM_REJECTED",
            "UNIFORM_NOT_REJECTED", "SAMPLE_TOO_SMALL", "SPAN_TOO_NARROW")
BANDS = ("CLOSE", "ACCEPTABLE", "MARGINAL", "NONCONFORMITY")
MIN_N = 1000
MIN_SPAN_RATIO = 10000


class BenfordKitError(Exception):
    def __init__(self, msg, field):
        super().__init__(msg)
        self.msg, self.field = msg, field


EP_FIRST_DIGIT = (
    "0.3010299956639812",
    "0.1760912590556812",
    "0.1249387366083000",
    "0.0969100130080564",
    "0.0791812460476248",
    "0.0669467896306132",
    "0.0579919469776868",
    "0.0511525224473813",
    "0.0457574905606751",
)

EP_FIRST_TWO = (
    "0.0413926851582250",
    "0.0377885608893998",
    "0.0347621062592119",
    "0.0321846833714013",
    "0.0299632233774432",
)

EP_FIRST_TWO = (
    "0.0280287236002435",
    "0.0263289387223491",
    "0.0248235837250321",
    "0.0234810958495229",
    "0.0222763947111522",
)

EP_FIRST_TWO = (
    "0.0211892990699381",
    "0.0202033860882870",
    "0.0193051551953866",
    "0.0184834056940131",
    "0.0177287669604316",
)

EP_FIRST_TWO = (
    "0.0170333392987804",
    "0.0163904161881693",
    "0.0157942671832319",
    "0.0152399665567369",
    "0.0147232568207063",
)

EP_FIRST_TWO = (
    "0.0142404391146102",
    "0.0137882844856333",
    "0.0133639615579815",
    "0.0129649771643676",
    "0.0125891273080205",
)

EP_FIRST_TWO = (
    "0.0122344564170116",
    "0.0118992232997077",
    "0.0115818725498152",
    "0.0112810104096890",
    "0.0109953843014632",
)

EP_FIRST_TWO = (
    "0.0107238653917731",
    "0.0104654336781650",
    "0.0102191651816861",
    "0.0099842209066009",
    "0.0097598372891562",
)

EP_FIRST_TWO = (
    "0.0095453179062304",
    "0.0093400262541434",
    "0.0091433794398698",
    "0.0089548426529264",
    "0.0087739243075051",
)

EP_FIRST_TWO = (
    "0.0086001717619176",
    "0.0084331675368628",
    "0.0082725259659899",
    "0.0081178902221795",
    "0.0079689296712753",
)

EP_FIRST_TWO = (
    "0.0078253375119566",
    "0.0076868286662910",
    "0.0075531378904459",
    "0.0074240180792069",
    "0.0072992387414994",
)

EP_FIRST_TWO = (
    "0.0071785846271234",
    "0.0070618544874868",
    "0.0069488599553278",
    "0.0068394245303055",
    "0.0067333826589684",
)

EP_FIRST_TWO = (
    "0.0066305788990131",
    "0.0065308671589578",
    "0.0064341100054099",
    "0.0063401780310190",
    "0.0062489492770015",
)

EP_FIRST_TWO = (
    "0.0061603087048185",
    "0.0060741477121932",
    "0.0059903636891874",
    "0.0059088596105203",
    "0.0058295436607239",
)

EP_FIRST_TWO = (
    "0.0057523288890913",
    "0.0056771328916905",
    "0.0056038775179985",
    "0.0055324885999610",
    "0.0054628957015022",
)

EP_FIRST_TWO = (
    "0.0053950318867062",
    "0.0053288335050669",
    "0.0052642399923572",
    "0.0052011936858078",
    "0.0051396396524111",
)

EP_FIRST_TWO = (
    "0.0050795255292750",
    "0.0050208013750508",
    "0.0049634195315501",
    "0.0049073344947442",
    "0.0048525027944121",
)

EP_FIRST_TWO = (
    "0.0047988828817687",
    "0.0047464350244617",
    "0.0046951212083798",
    "0.0046449050457635",
    "0.0045957516891491",
)

EP_FIRST_TWO = (
    "0.0045476277507206",
    "0.0045005012266764",
    "0.0044543414262500",
    "0.0044091189050551",
    "0.0043648054024501",
)


TESTS = {
    "first_digit": {"bins": 9, "df": 8, "ep": EP_FIRST_DIGIT,
                    "mad": True},
    "first_two": {"bins": 90, "df": 89, "ep": EP_FIRST_TWO,
                  "mad": True},
    "last_digit": {"bins": 10, "df": 9, "ep": tuple(["0.1"] * 10),
                   "mad": True},
    "last_two": {"bins": 100, "df": 99, "ep": tuple(["0.01"] * 100),
                 "mad": False},
}
MAD_EDGES = {"first_digit": (("CLOSE", "0.006"), ("ACCEPTABLE", "0.012"),
                             ("MARGINAL", "0.015")),
             "first_two": (("CLOSE", "0.0012"), ("ACCEPTABLE", "0.0018"),
                           ("MARGINAL", "0.0022"))}
TABLE_SHA = hashlib.sha256(json.dumps(
    {"name": TABLE_NAME,
     "first_digit": list(EP_FIRST_DIGIT),
     "first_two": list(EP_FIRST_TWO),
     "mad_edges": MAD_EDGES,
     "min_n": MIN_N, "min_span_ratio": MIN_SPAN_RATIO},
    sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _q(x, places):
    return str(x.quantize(_D(1).scaleb(-places), ROUND_HALF_UP))


def band_of(test, mad):
    """Bande Nigrini, borne superieure INCLUSIVE (convention v1, dite)."""
    if test not in MAD_EDGES:
        return None
    for name, edge in MAD_EDGES[test]:
        if mad <= _D(edge):
            return name
    return "NONCONFORMITY"


def test_run(test, counts, vmin, vmax):
    """Comptes de tests fermes + min/max -> n, df, chi2 (2 dp),
    chi2_crit_05, MAD (4 dp), bande, verdict (ensemble ferme)."""
    if test not in TESTS:
        raise BenfordKitError(
            "test %r is off the closed set: first_digit, first_two, "
            "last_digit, last_two — the expected table exists for "
            "these four only" % test, "test")
    spec = TESTS[test]
    if len(counts) != spec["bins"]:
        raise BenfordKitError(
            "%s takes exactly %d counts (%s bins); %d given — no bin "
            "is invented and none is dropped"
            % (test, spec["bins"],
               {"first_digit": "digits 1..9",
                "first_two": "values 10..99",
                "last_digit": "digits 0..9",
                "last_two": "values 00..99"}[test], len(counts)),
            "counts")
    if any(c < 0 for c in counts):
        raise BenfordKitError("counts must be >= 0: a frequency cannot "
                             "be negative", "counts")
    try:
        lo, hi = _D(str(vmin)), _D(str(vmax))
    except Exception:
        raise BenfordKitError("min and max must be plain numbers "
                              "(decimal strings or integers) — the "
                              "span ratio is exact or it is not made",
                              "min")
    if lo <= 0:
        raise BenfordKitError(
            "min must be > 0: the span rule R-SPAN divides by it — "
            "values <= 0 are excluded upstream (rule R-POS), never "
            "fed as span bounds", "min")
    if hi < lo:
        raise BenfordKitError(
            "max < min: the span bounds are inverted", "max")
    n = sum(counts)
    N = _D(n)
    df = spec["df"]
    eps = [_D(e) for e in spec["ep"]]
    chi2 = sum((_D(o) - N * e) ** 2 / (N * e)
               for o, e in zip(counts, eps)) if n else _D(0)
    k = _D(spec["bins"])
    mad = sum(abs(_D(o) / N - e) for o, e in zip(counts, eps)) / k \
        if n else None
    crit05 = critical(df, "0.05")["chi2_crit"]
    band = band_of(test, mad) if mad is not None else None
    if test == "last_two":
        band = None
    if n < MIN_N:
        verdict = "SAMPLE_TOO_SMALL"
    elif test in ("first_digit", "first_two") and hi / lo < MIN_SPAN_RATIO:
        verdict = "SPAN_TOO_NARROW"
    elif test in ("first_digit", "first_two"):
        verdict = ("NONCONFORMITY" if band == "NONCONFORMITY"
                   else "CONFORMS")
    else:
        verdict = ("UNIFORM_REJECTED" if chi2 > _D(crit05)
                   else "UNIFORM_NOT_REJECTED")
    out = {"test": test, "n": n, "df": df,
           "chi2": _q(chi2, 2),
           "chi2_crit_05": crit05,
           "chi2_crit_05_source": "%s (sha256 %s)"
                                  % (CRIT_TABLE_NAME, CRIT_TABLE_SHA),
           "verdict": verdict}
    if mad is not None:
        out["mad"] = _q(mad, 4)
        out["band"] = band
        if band is None:
            out["band_note"] = ("no Nigrini 2012 band is published for "
                                "this test — mad is info only")
    out["table"] = {"name": TABLE_NAME, "sha256": TABLE_SHA,
                    "rules": ["R-N1 n >= %d else SAMPLE_TOO_SMALL" % MIN_N,
                              "R-SPAN max/min >= 10^4 for first_* "
                              "else SPAN_TOO_NARROW",
                              "precedence: R-N1 > R-SPAN > statistic"],
                    "source": ("Benford expected proportions as "
                               "16-decimal log10(1+1/d) literals; MAD "
                               "bands from Nigrini 2012, ch. 7, "
                               "table 7.1 (upper-inclusive, v1 "
                               "convention declared); chi-square "
                               "critical values from %s" % CRIT_TABLE_NAME),
                    "critical_source_sha256_published":
                        CRIT_SOURCE_SHA_PUBLISHED}
    return out
