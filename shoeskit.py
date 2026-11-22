"""shoeskit — /api/v1/units/shoe_size : les pointures en millimètres,
les PAS publiés en fractions exactes, la DÉRIVE rendue comme déclaration.

La douleur (veille forums, item pointures) : les convertisseurs
publiés rendent UN numéro confiant — « EU 42 → US 9 » — pendant que
leur propre prose concède que Nike imprime 42,5 et adidas 42⅔ pour le
MÊME US 9 (forkshoes, saascity 20 nov. 2026), et que « US 9.5 = EU 41
OU 42, les deux techniquement corrects » (thefitville, footwisdom).
Le petit modèle, lui, invente des moyennes : r/mildlyinfuriating —
« 7.5 − 1.5 = 9.5 » et un « average 1.75 » FABRIQUÉ pour coller aux
charts. Ici : aucune moyenne inventée, aucun numéro unique — la base
est le millimètre (seule échelle qui MESURE), les paliers sont les
échelles publiées, et chaque système rend sa POSITION exacte plus ses
CANDIDATS de grille (entiers / demi / tiers selon les pratiques
publiées des marques).

Specs ancrées (citées, jamais de mémoire) :
  PAS (sizechartfinder, convertitive, saascity) :
    Paris point  = 2/3 cm  = Fraction(20, 3)  mm = 6.666…
    barleycorn   = 1/3 in  = 25.4/3 mm        = 127/15   = 8.466…
    demi US/UK   = 127/30  = 4.233… ; demi EU = 10/3 = 3.333…
    mondopoint   = pas de 5 mm (ISO 9407:2019, Japan/Korea/ski)
    écart par pas : 127/15 − 20/3 = 9/5 = 1,8 mm EXACTEMENT
      (convertitive dit « ~1.8 mm per step » — chez nous c'est exact,
      en fractions, jamais 8.47 − 6.67 en flottant)
    4 pas EU = 80/3 ≈ 26.667 mm vs 3 pas US = 127/5 = 25.4 mm :
      les grilles ne se recouvrent JAMAIS (saascity/sizechartfinder),
      écart du cycle = 19/15 mm
  Tables de conversion (calibr.pro, restitution publiée d'ISO/TS
  19407:2023 Table 2 ; sizechartfinder) :
    foot_mm = (UK + 23) × 127/15 ; US men = UK + 1 ; US women = UK + 2
    EU = foot_cm × 3/2 + 2   (soit foot_mm × 3/20 + 2 — le « +2 » est
      l'aisance, exactement 2 Paris points = 40/3 ≈ 13.33 mm, DÉCLARÉE)
  Ancre last (saascity, verbatim : « EU 42 is a 28 cm last ») :
    last_mm = label × 20/3   (42 × 20/3 = 280,000 mm exact)
    UK      : last_in = (UK + 25)/3 (échelle publiée « 3×last − 25 »)

Zone hors contrat, DITE : les charts MARQUES (Nike 42.5 vs adidas 42⅔
vs « EU 44 » pour le même pied sur le chart Nike de sizechartfinder)
sont du live — aucune marque n'est encodée ici ; la réponse nomme la
dérive et rend les candidats de grille, jamais un achat.

Fermé, ça veut dire :
  systèmes    eu | uk | us_men | us_women | mondopoint (refus Nommé)
  entrée      foot_mm OU (size + system) — les deux = refus nommé ;
              width_mm optionnel (format ISO 9407 « 271/100 »)
  size        entier, décimal, fraction simple ou mixte (« 42 2/3 »,
              « 85/2 ») — tout devient Fraction exacte ou refus
  bornes      foot 80–400 mm, width 50–150 mm, labels dans les
              fourchettes publiées par système — hors bornes = refus
  rendu       fractions exactes en base ; décimales = arrondi déclaré
              ROUND_HALF_EVEN 4 dp (jamais la source de vérité)
  state       aucun : tout en paramètre (threads FastAPI)
"""
import re
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from fractions import Fraction

getcontext().prec = 34

IN_MM = Fraction(127, 5)            # 25.4 mm
BARLEY = IN_MM / 3                  # 1/3 in = 127/15 mm (8.466…)
PARIS = Fraction(20, 3)             # 2/3 cm = 6.666… mm
MONDO_STEP = 5                      # ISO 9407:2019 pas courant
PER_STEP_GAP = BARLEY - PARIS       # = 9/5 = 1.8 mm exactement
CYCLE_EU4 = PARIS * 4               # 80/3 mm
CYCLE_US3 = BARLEY * 3              # 127/5 mm
ALLOWANCE = 2 * PARIS               # le « +2 » = 40/3 mm = 13.333…

SYSTEMS = ("eu", "uk", "us_men", "us_women", "mondopoint")

# bornes publiées des étiquettes (fourchettes commerciales usuelles)
LABEL_BOUNDS = {
    "eu": (Fraction(15), Fraction(55)),
    "uk": (Fraction(0), Fraction(18)),
    "us_men": (Fraction(1), Fraction(20)),
    "us_women": (Fraction(1), Fraction(20)),
    "mondopoint": (Fraction(100), Fraction(350)),
}
# pas de grille par système : les demi-tailles existent en UK/US/EU,
# les TIERS sont imprimés par certaines marques EU (saascity, forkshoes)
GRIDS = {
    "eu": ("1/2", Fraction(1, 2), "1/3", Fraction(1, 3)),
    "uk": ("1/2", Fraction(1, 2)),
    "us_men": ("1/2", Fraction(1, 2)),
    "us_women": ("1/2", Fraction(1, 2)),
    "mondopoint": ("5mm", Fraction(5)),
}


class ShoeSizeError(ValueError):
    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected


def _dec(f, dp=4):
    """Rendu décimal déclaré — la fraction reste la valeur exacte."""
    q = Decimal(1).scaleb(-dp)
    return str((Decimal(f.numerator) / Decimal(f.denominator))
               .quantize(q, rounding=ROUND_HALF_EVEN))


def _fr(f):
    return "%d/%d" % (f.numerator, f.denominator)


def _label(f):
    """Étiquette lisible d'une position de grille : 42, 42 1/2, 42 2/3."""
    whole = f.numerator // f.denominator
    rem = f - whole
    if rem == 0:
        return str(whole)
    return "%d %s" % (whole, _fr(rem))


def _bracket(position, step):
    """Les deux points de grille qui encadrent la position (dédup)."""
    units = position / step
    fl = units.numerator // units.denominator          # floor exact
    lower = fl * step
    upper = lower if units == fl else (fl + 1) * step
    out = []
    for v in (lower, upper):
        lab = _label(v)
        if lab not in out:
            out.append(lab)
    return out


_MIX = re.compile(r"^(\d+)(?:[.](\d+)|[ +](\d+)/(\d+))$")
_PLAIN = re.compile(r"^\d+(?:[.]\d+)?$")
_FRAC = re.compile(r"^(\d+)/(\d+)$")


def _parse_size(raw, field):
    if isinstance(raw, bool):
        raise ShoeSizeError(field, "size must be a number", "e.g. 42.5")
    if isinstance(raw, (int, float)):
        if isinstance(raw, float):
            raw = repr(raw)
        else:
            return Fraction(raw)
    s = str(raw).strip().replace(",", ".")
    m = _PLAIN.match(s)
    if m:
        return Fraction(s)
    m = _FRAC.match(s)
    if m:
        den = int(m.group(2))
        if den == 0:
            raise ShoeSizeError(field, "zero denominator", "e.g. '85/2'")
        return Fraction(int(m.group(1)), den)
    m = _MIX.match(s)
    if m:
        whole = int(m.group(1))
        if m.group(2) is not None:
            return Fraction(str(whole) + "." + m.group(2))
        num, den = int(m.group(3)), int(m.group(4))
        if den == 0 or num >= den:
            raise ShoeSizeError(
                field, "fraction part must be < 1 (proper)",
                "e.g. '42 2/3' — a full size belongs in the integer part")
        return Fraction(whole) + Fraction(num, den)
    raise ShoeSizeError(
        field, "size not parseable: %r" % raw,
        "integer, decimal ('42.5'), fraction ('85/2') or mixed ('42 2/3')")


def _foot_from_label(system, size):
    """Position d'étiquette -> foot_mm (ancre pied des tables publiées)."""
    if system == "eu":
        return (size - 2) * PARIS
    if system == "uk":
        return (size + 23) * BARLEY
    if system == "us_men":
        return (size - 1 + 23) * BARLEY
    if system == "us_women":
        return (size - 2 + 23) * BARLEY
    return size  # mondopoint : l'étiquette EST le mm


def run_shoe_size(args):
    args = dict(args or {})
    foot_raw = args.get("foot_mm")
    size_raw = args.get("size")
    width_raw = args.get("width_mm")
    system = args.get("system")

    if foot_raw is not None and size_raw is not None:
        raise ShoeSizeError(
            "foot_mm", "foot_mm and size are both given",
            "exactly one: a measured foot in mm, or a labelled size "
            "with system=")
    if foot_raw is None and size_raw is None:
        raise ShoeSizeError(
            "foot_mm", "nothing to convert",
            "foot_mm (e.g. 271) or size+system (e.g. size '42 2/3', "
            "system 'eu')")

    if foot_raw is not None:
        foot = Fraction(str(foot_raw))
        basis = "foot_mm given directly"
        system = None
    else:
        if system not in SYSTEMS:
            raise ShoeSizeError(
                "system", "unknown system: %r" % (system,),
                "one of %s (closed list)" % ", ".join(SYSTEMS))
        size = _parse_size(size_raw, "size")
        lo, hi = LABEL_BOUNDS[system]
        if not lo <= size <= hi:
            raise ShoeSizeError(
                "size", "size %s outside published bounds for %s"
                % (_label(size), system),
                "%s..%s" % (lo, hi))
        foot = _foot_from_label(system, size)
        basis = "label %s in %s -> foot by the published %s formula" % (
            _label(size), system,
            "Paris-point" if system == "eu" else
            "mondopoint mm" if system == "mondopoint" else "barleycorn")
        if system == "eu":
            basis += " (the +2 = allowance, exactly 2 Paris points " \
                     "= %s mm = %s mm, is declared)" % (_fr(ALLOWANCE),
                                                        _dec(ALLOWANCE))

    if not Fraction(80) <= foot <= Fraction(400):
        raise ShoeSizeError(
            "foot_mm" if foot_raw is not None else "size",
            "foot length %s mm outside 80..400" % _dec(foot),
            "80..400 mm (adult+child range of the published charts)")

    width = None
    if width_raw is not None:
        width = Fraction(str(width_raw))
        if not Fraction(50) <= width <= Fraction(150):
            raise ShoeSizeError("width_mm", "width outside 50..150 mm",
                                "50..150 mm")

    # — positions par système (fractions exactes, jamais de moyenne)
    uk = foot / BARLEY - 23
    labels = {
        "eu": foot / PARIS + 2,
        "uk": uk,
        "us_men": uk + 1,
        "us_women": uk + 2,
    }
    out = {
        "tool": "units_shoe_size",
        "basis": basis,
        "foot_mm": {"fraction": _fr(foot), "decimal_mm": _dec(foot)},
        "systems": {},
    }
    for name, pos in labels.items():
        g = GRIDS[name]
        cand = {}
        for i in range(0, len(g), 2):
            cand["grid_" + g[i]] = _bracket(pos, g[i + 1])
        out["systems"][name] = {
            "position": {"fraction": _fr(pos), "decimal": _dec(pos)},
            "candidates": cand,
            "step_mm": {"fraction": _fr(PARIS if name == "eu" else BARLEY),
                        "decimal": _dec(PARIS if name == "eu" else BARLEY)},
        }
    out["systems"]["mondopoint"] = {
        "position": {"fraction": _fr(foot), "decimal_mm": _dec(foot)},
        "candidates": {"grid_5mm": _bracket(foot, MONDO_STEP)},
        "step_mm": {"fraction": "5/1", "decimal": "5.0000"},
    }
    if width is not None:
        out["mondopoint_label"] = "%s/%s" % (
            _label(foot), _label(width))
        out["width_note"] = ("ISO 9407 sizes length/width in mm "
                             "(e.g. '271/100'); fit here stays on "
                             "length — width classes of the shoe "
                             "itself are brand territory")

    # — la dérive, rendue comme déclaration (valeurs exactes)
    out["scale_steps_mm"] = {
        "paris_point": {"fraction": _fr(PARIS), "decimal": _dec(PARIS)},
        "barleycorn": {"fraction": _fr(BARLEY), "decimal": _dec(BARLEY)},
        "half_paris": {"fraction": _fr(PARIS / 2), "decimal": _dec(PARIS / 2)},
        "half_barleycorn": {"fraction": _fr(BARLEY / 2),
                            "decimal": _dec(BARLEY / 2)},
    }
    out["drift"] = {
        "per_step_gap_mm": {"fraction": _fr(PER_STEP_GAP),
                            "decimal": _dec(PER_STEP_GAP, 6)},
        "four_eu_steps_mm": {"fraction": _fr(CYCLE_EU4),
                             "decimal": _dec(CYCLE_EU4)},
        "three_us_steps_mm": {"fraction": _fr(CYCLE_US3),
                              "decimal": _dec(CYCLE_US3)},
        "cycle_gap_mm": {"fraction": _fr(CYCLE_EU4 - CYCLE_US3),
                         "decimal": _dec(CYCLE_EU4 - CYCLE_US3)},
        "note": "the grids never coincide: 4 EU steps = 80/3 mm but "
                "3 US/UK steps = 127/5 mm — every chart rounds",
    }
    out["last_anchor"] = {
        "eu_last_mm_formula": "label x 20/3 (Paris scale measures the "
                              "LAST: EU 42 -> 280.000 mm exactly)",
        "foot_vs_last_allowance_mm": {
            "fraction": _fr(ALLOWANCE), "decimal": _dec(ALLOWANCE)},
    }
    out["never_one_number"] = True
    out["scope_note"] = (
        "Brand size charts (Nike 42.5 vs adidas 42 2/3 vs whole-size "
        "Birkenstock for the same foot) are LIVE and OFF this contract "
        "— no brand is encoded here; this returns the exact positions "
        "and the published grid candidates, plus the drift as stated "
        "numbers. Nothing here says which shoe to buy; lasts differ "
        "in width, instep and toe box, not just length.")
    out["source"] = (
        "ISO/TS 19407:2023 Table 2 conventions as published "
        "(US men = UK + 1, US women = UK + 2, foot = (UK+23) x 127/15 "
        "mm); Paris point = 2/3 cm; barleycorn = 1/3 in; EU foot "
        "conversion = foot_cm x 1.5 + 2; ISO 9407:2019 mondopoint, "
        "5 mm steps.")
    out["rounding_note"] = ("all values exact as fractions; decimals "
                            "are ROUND_HALF_EVEN to 4 dp, never the "
                            "source of truth")
    return out
