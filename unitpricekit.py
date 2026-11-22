"""unitpricekit — /money/unitprice : le prix à l'unité, exact, avec le
DÉNOMINATEUR NOMMÉ.

La douleur est documentée, pas conjecturée :

  * shrinkflation — TheWhyWeProject (21-nov-2026) : « un pack de 10
    portions devient 9, l'étiquette ne bouge pas, le prix par portion
    monte d'environ 1/9 » ; Janssen & Kasinger (Marketing Science 2025,
    comm. INFORMS 27-fév-2026) : +12 % par once l'année après un
    rétrécissement, et les shoppers n'ajustent presque pas la demande ;
    ShrinkRadar (édition 21-nov-2026) : +20,0 % médian au dénominateur
    caché contre +3,7 % d'inflation officielle ; Iowa State agpolicy
    review (automne 2026) : le thon coordonné 6 oz → 5 oz (DOJ 2016).
  * l'asymétrie des deux pourcentages — smartdollarplace (4-nov-2026) :
    Gatorade 32 → 28 fl oz = −12,5 % de produit mais +14,2857 % par
    once (32/28 = 8/7). CE NE SONT PAS LES MÊMES NOMBRES : la perte
    divise par l'ANCIENNE assiette, la hausse par la NOUVELLE. Un seul
    pourcentage pour les deux est exactement le mensonge que ce module
    rend impossible.
  * la notation composée — r/mildlyinfuriating (le coupon « 20 oz »
    refusé sur un pain marqué « 1 lb 4 oz ») : 1 lb 4 oz EST 20 oz, et
    « 2 l 500 ml » EST 2,5 l. La grammaire fermée le sait.
  * l'étiquette fausse — r/LifeProTips (« Walmart s'est trompé dans le
    calcul »), r/aldi (« les calculs des étiquettes sont inexacts ») :
    le prix/unité AFFICHÉ est une allégation. Ici il est REJOUE en
    Fraction exacte, à SA propre précision, et sa faute est nommée.
  * le mythe du gros format — smartdollarplace : (3,00 − 1,00 coupon)
    / 12 oz BAT 6,00 / 32 oz. Le serveur compare des fractions exactes,
    pas des impressions ; l'affichage 6 décimales n'est qu'un rendu
    (leçon Consumer Reports : arrondir 7,75 en 7,8 avait changé le
    gagnant de deux produits).

Ancrages : mass/volume viennent de units.py — livre avoirdupois =
453,59237 g pile (accord international 1959), galon US = 231 in³ =
3,785411784 L pile (NIST SP 811). La famille count est le dénombrement
pur : toute unité comptée vaut 1 objet, aucune table.

Doctrine : jamais de fetch, jamais d'horloge — mêmes octets pour
toujours. Virgule décimale = refus nommé vers /num/parse (c'est une
FORME, pas un nombre). Familles mélangées = refus nommé qui enseigne
la sortie. La fraction exacte voyage TOUJOURS à côté de l'affichage.
"""
import re
from decimal import Decimal, ROUND_HALF_UP, localcontext
from fractions import Fraction

import units

Q4 = Decimal("0.0001")
Q6 = Decimal("0.000001")
MODES = ("compare", "shrink")
MAX_OFFERS = 6
MAX_TOKENS = 4
MAX_COUNT = 999

# unités comptées (dénombrement pur), canonique -> famille "count"
COUNT_UNITS = {
    "each": "each", "ea": "each", "count": "each", "ct": "each",
    "piece": "piece", "pieces": "piece", "pc": "piece", "pcs": "piece",
    "sheet": "sheet", "sheets": "sheet", "load": "load", "loads": "load",
    "can": "can", "cans": "can", "tablet": "tablet", "tablets": "tablet",
    "capsule": "capsule", "capsules": "capsule", "wipe": "wipe",
    "wipes": "wipe", "portion": "portion", "portions": "portion",
}

# alias de présentation avant units._resolve (qui ne connaît que les
# formes canoniques du fichier units.py)
PRESENT = {
    "floz": "floz_us", "fl_oz": "floz_us", "fluidounce": "floz_us",
    "fluidounces": "floz_us",
    "qt": "qt_us", "qts": "qt_us", "quart": "qt_us", "quarts": "qt_us",
    "pt": "pt_us", "pint": "pt_us", "pints": "pt_us",
    "gal": "gal_us", "gallons": "gal_us",
    "cups": "cup_us", "mls": "ml", "liters": "l", "litres": "l",
}


class UnitPriceError(Exception):
    def __init__(self, field, message, expected):
        self.field = field
        self.message = message
        self.expected = expected
        Exception.__init__(self, message)


def _d(x, what):
    try:
        v = Decimal(str(x))
    except Exception:
        raise UnitPriceError(
            what,
            "%s: %r is not a number — dot decimal here ('19.99'); "
            "locale forms go through /api/v1/num/parse first" % (what, x),
            "decimal string, e.g. \"19.99\"")
    if not v.is_finite():
        raise UnitPriceError(what, "%s must be finite, got %r"
                             % (what, x), "finite decimal")
    return v


def _pos(x, what):
    v = _d(x, what)
    if v <= 0:
        raise UnitPriceError(what, "%s must be > 0, got %r — a zero-size "
                             "package is a refusal, not a price" % (what, x),
                             "positive decimal")
    return v


def _resolve_unit(token, field):
    """(family, canonical, Fraction base-per-one) — vocabulaire fermé."""
    if not isinstance(token, str) or not token.strip():
        raise UnitPriceError(
            field, "unit must be a non-empty string, got %r" % (token,),
            "one of: count (each sheet load can …), mass (g kg oz lb …), "
            "volume (ml l floz_us qt_us …)")
    raw = token.strip()
    low = re.sub(r"[\s.]+", "_", raw.lower()).strip("_")
    if low in COUNT_UNITS:
        return "count", COUNT_UNITS[low], Fraction(1)
    key = PRESENT.get(low, low)
    try:
        fam, canon = units._resolve(key)
    except units.UnitError:
        raise UnitPriceError(
            field,
            "unknown unit %r — closed vocabulary: count tokens (each, "
            "sheet, load, can, tablet, wipe, portion…) plus units/convert's "
            "mass and volume — compound forms like '1 lb 4 oz' parse, "
            "'sticks' does not" % (token,),
            "a unit of mass, volume, or count")
    if fam not in ("mass", "volume"):
        raise UnitPriceError(field,
                             "unit %r resolves to family %r — unitprice "
                             "compares mass, volume and count only"
                             % (token, fam),
                             "mass, volume or count unit")
    num, den = units.FAMILIES[fam]["units"][canon]
    return fam, canon, Fraction(num) / Fraction(den)


_PAIR = re.compile(r"^(\d+(?:\.\d+)?)([A-Za-z][A-Za-z0-9_]*)$")


def _parse_compact(s, field):
    """'1 lb 4 oz' / '1lb 4oz' / '2 l 500 ml' -> (fam, canon, Σ base).

    Grammaire fermée : 1..4 paires (nombre, unité) séparées par des
    espaces, TOUTES de la même famille. '20' seul = refus nommé (unit ?),
    jamais de devinette.
    """
    if not isinstance(s, str) or not s.strip():
        raise UnitPriceError(field, "qty_str must be non-empty",
                             "e.g. '1 lb 4 oz', '2 l 500 ml'")
    toks = s.split()
    if len(toks) > 2 * MAX_TOKENS:
        raise UnitPriceError(
            field, "qty_str %r: %d tokens beyond the cap of %d pairs"
            % (s, len(toks), MAX_TOKENS),
            "at most %d number+unit pairs" % MAX_TOKENS)
    total = Fraction(0)
    fam = canon = None
    i = 0
    while i < len(toks):
        num_s = unit_s = None
        m = _PAIR.match(toks[i])
        if m:
            num_s, unit_s = m.group(1), m.group(2)
        elif re.match(r"^\d+(\.\d+)?$", toks[i]) and i + 1 < len(toks):
            num_s, unit_s = toks[i], toks[i + 1]
            i += 1
        else:
            raise UnitPriceError(
                field,
                "qty_str %r: %r is not a number+unit pair — closed grammar "
                "is '<size><unit>' repeated, e.g. '1 lb 4 oz'"
                % (s, toks[i]),
                "number followed by a unit, 1..4 pairs")
        f, c, factor = _resolve_unit(unit_s, field)
        if fam is None:
            fam, canon = f, c
        elif f != fam:
            raise UnitPriceError(
                field,
                "qty_str %r mixes families: %r is %s but the earlier pair "
                "was %s — one family per quantity" % (s, unit_s, f, fam),
                "all pairs of the SAME family")
        total += Fraction(_pos(num_s, "%s token %r" % (field, toks[i]))
                          ) * factor
        i += 1
    return fam, canon, total


def _decimal_str(fr):
    """Fraction au dénominateur doux (2^a·5^b, le cas ici) -> décimal."""
    with localcontext() as ctx:
        ctx.prec = 60
        d = Decimal(fr.numerator) / Decimal(fr.denominator)
    return format(d.normalize(), "f")


def _quantity(o, field):
    """(family, canon, total_size_base: Fraction) d'une offre."""
    has_str = o.get("qty_str") not in (None, "")
    has_pair = o.get("qty") not in (None, "") or o.get("unit") not in (None,
                                                                       "")
    if has_str and has_pair:
        raise UnitPriceError(
            field,
            "%s: qty_str and qty/unit are mutually exclusive — the grammar "
            "will not guess which notation you meant" % field,
            "one of: qty_str, or qty + unit")
    if has_str:
        fam, canon, total = _parse_compact(o["qty_str"], field)
    elif has_pair:
        fam, canon, factor = _resolve_unit(o.get("unit"),
                                           "%s.unit" % field)
        total = Fraction(_pos(o.get("qty"), "%s.qty" % field)) * factor
    else:
        raise UnitPriceError(
            field,
            "%s: needs qty_str OR qty + unit — a price without a quantity "
            "is an advertisement, not an offer" % field,
            "qty_str like '1 lb 4 oz', or qty + unit")
    count_s = o.get("count")
    if count_s not in (None, ""):
        cs = str(count_s).strip()
        if not re.match(r"^\d+$", cs):
            raise UnitPriceError("%s.count" % field,
                                 "%s.count must be a whole number string "
                                 "('2' for two-for-$7), got %r"
                                 % (field, count_s), "integer string")
        c = int(cs)
        if c < 2:
            raise UnitPriceError(
                "%s.count" % field,
                "%s.count=%d — count multiplies a bundle; one item is just "
                "the item, drop the field" % (field, c), "integer >= 2")
        if c > MAX_COUNT:
            raise UnitPriceError(
                "%s.count" % field,
                "%s.count=%d beyond %d — this is a shopping cart, not a "
                "pallet" % (field, c, MAX_COUNT),
                "integer <= %d" % MAX_COUNT)
        total *= c
    if total <= 0:
        raise UnitPriceError(field, "%s: quantity sums to zero" % field,
                             "positive size")
    return fam, canon, total


def _money(v):
    return format(v, "f")


def _pct(fr):
    """(FRAC × 100) -> display 4 dp HALF_UP + exact reduced fraction."""
    p = Fraction(fr) * 100
    d = (Decimal(p.numerator) / Decimal(p.denominator)).quantize(
        Q4, ROUND_HALF_UP)
    return {"display": format(d, "f"),
            "exact_fraction": {"numerator": p.numerator,
                               "denominator": p.denominator}}


def _pu(fr):
    """prix/unité -> display 6 dp HALF_UP + exact."""
    d = (Decimal(fr.numerator) / Decimal(fr.denominator)).quantize(
        Q6, ROUND_HALF_UP)
    return {"display": format(d, "f"),
            "exact_fraction": {"numerator": fr.numerator,
                               "denominator": fr.denominator}}


def _audit_tag(tag, per_base, field, fam):
    """L'étiquette du magasin est une ALLÉGATION : rejouée en exact,
    jugée à SA propre précision (le mensonge de Consumer Reports
    7,75→7,8 est précisément un changement de précision)."""
    if not isinstance(tag, dict):
        raise UnitPriceError(
            "%s.tag" % field,
            "%s.tag must be an object {value, unit}, got %r" % (field, tag),
            "e.g. {\"value\": \"0.244\", \"unit\": \"oz\"}")
    claimed = _pos(tag.get("value"), "%s.tag.value" % field)
    fam_t, canon_t, tfac = _resolve_unit(tag.get("unit"), "%s.tag.unit"
                                         % field)
    if fam_t != fam:
        raise UnitPriceError("%s.tag.unit" % field,
                             "tag unit %r is family %r, offers are %r"
                             % (tag.get("unit"), fam_t, fam),
                             "a unit of %s" % fam)
    true = per_base * tfac  # prix par unité D'ÉTIQUETTE
    cs = str(claimed)
    dp = len(cs.split(".")[1]) if "." in cs else 0
    with localcontext() as ctx:
        ctx.prec = 60
        q = (Decimal(true.numerator) / Decimal(true.denominator)).quantize(
            Decimal(1).scaleb(-dp), ROUND_HALF_UP)
    honest = q == claimed
    out = {"claimed": cs, "claimed_unit": canon_t,
           "true_exact": _pu(true), "verdict":
           "TAG_HONEST" if honest else "TAG_WRONG"}
    out["note"] = (
        "the tag's rounding was stated: true %s per %s quantized at %d dp "
        "is %s, exactly the claim"
        % (_pu(true)["display"], canon_t, dp, cs) if honest else
        "the tag claims %s per %s but the exact share is %s — a tag is an "
        "allegation; here it is recomputed (r/LifeProTips 'Walmart got the "
        "math wrong' vector)" % (cs, canon_t, _pu(true)["display"]))
    return out


def _run_compare(args):
    offers = args.get("offers")
    if not isinstance(offers, list) or len(offers) < 2:
        raise UnitPriceError(
            "offers", "compare needs 2..%d offers, got %r"
            % (MAX_OFFERS, offers),
            "list of 2..%d {price, qty_str|qty+unit, count?, tag?}"
            % MAX_OFFERS)
    if len(offers) > MAX_OFFERS:
        raise UnitPriceError(
            "offers", "cap is %d offers, got %d — a shopping list is not "
            "a comparison" % (MAX_OFFERS, len(offers)),
            "at most %d offers" % MAX_OFFERS)
    fam = None
    parsed = []
    for i, o in enumerate(offers):
        if not isinstance(o, dict):
            raise UnitPriceError("offers[%d]" % i,
                                 "offer %d must be an object" % i,
                                 "{price, qty_str or qty+unit}")
        field = "offers[%d]" % i
        price = _pos(o.get("price"), "%s.price" % field)
        f, canon, total = _quantity(o, field)
        if fam is None:
            fam = f
        elif f != fam:
            raise UnitPriceError(
                field,
                "%s is family %r but offer 0 is family %r — cross-family "
                "comparison is a REFUSAL, not a number: to price per "
                "volume what is sold per can, give the can's volume as "
                "the size and compare on the volume side"
                % (field, f, fam),
                "all offers in ONE family")
        parsed.append((field, str(o.get("label") or "offer %d" % i),
                       price, canon, total, o))

    basis = args.get("basis")
    if basis not in (None, ""):
        bfam, bcanon, bfac = _resolve_unit(basis, "basis")
        if bfam != fam:
            raise UnitPriceError(
                "basis", "basis %r is family %r but the offers are %r"
                % (basis, bfam, fam), "a unit of %s" % fam)
    else:
        bcanon = parsed[0][3]
        bfac = _resolve_unit(bcanon, "basis")[2]

    rows = []
    pfs = []
    for field, label, price, canon, total, o in parsed:
        per_base = Fraction(price) / total          # prix par unité de base
        per_basis = per_base * bfac                 # prix par unité d'affichage
        pfs.append(per_basis)
        row = {"label": label,
               "sticker": _money(price),
               "size": {"numerator": total.numerator,
                        "denominator": total.denominator,
                        "unit": "base_of_%s" % fam},
               "size_said": {"value": _decimal_str(
                   total / _resolve_unit(canon, field)[2]),
                   "unit": canon},
               "per_unit": _pu(per_basis),
               "expression": "%s / %s %s = %s per %s"
                             % (_money(price),
                                _decimal_str(total /
                                             _resolve_unit(canon,
                                                           field)[2]),
                                canon, _pu(per_basis)["display"], bcanon)}
        tag = o.get("tag")
        if tag not in (None, ""):
            row["tag_audit"] = _audit_tag(tag, per_base, field, fam)
        rows.append(row)

    best = min(range(len(pfs)), key=lambda i: pfs[i])
    ties = [i for i in range(len(pfs)) if pfs[i] == pfs[best]]
    for r, pf in zip(rows, pfs):
        r["vs_winner"] = _pct(pf / pfs[best] - 1)
    cheapest_sticker = min(range(len(parsed)), key=lambda i: parsed[i][2])
    largest = max(range(len(parsed)), key=lambda i: parsed[i][4])
    notes = []
    if len(ties) > 1:
        winner = None
        notes.append(
            "TIE: %s cost EXACTLY the same per %s — the fractions are "
            "equal, no rounding was ever consulted"
            % (" and ".join(sorted(rows[i]["label"] for i in ties)),
               bcanon))
    else:
        winner = rows[best]["label"]
        if cheapest_sticker != best:
            notes.append(
                "%s has the LOWEST STICKER (%s) yet %s wins per %s (%s "
                "vs %s) — the bulk-size myth is broken by exact "
                "fractions, not by feeling"
                % (rows[cheapest_sticker]["label"],
                   rows[cheapest_sticker]["sticker"], winner, bcanon,
                   rows[best]["per_unit"]["display"],
                   rows[cheapest_sticker]["per_unit"]["display"]))
        elif parsed[largest][4] > parsed[best][4] and largest != best:
            notes.append(
                "%s is the BIGGEST package yet costs %s%% MORE per %s "
                "than %s — buying big is a habit, not a deal; the coupon "
                "or the mid-size can win on the exact fraction"
                % (rows[largest]["label"],
                   rows[largest]["vs_winner"]["display"], bcanon, winner))
    if not notes:
        notes.append(
            "%s is the cheapest per %s by exact fraction; every vs_winner "
            "percentage divides by the WINNER — one denominator per number"
            % (winner, bcanon))
    return {"mode": "compare", "family": fam, "basis_unit": bcanon,
            "winner": winner, "offers": rows, "note": " | ".join(notes)}


def _run_shrink(args):
    fam, canon, factor = _resolve_unit(args.get("unit"), "unit")
    old_s = Fraction(_pos(args.get("old_size"), "old_size")) * factor
    new_s = Fraction(_pos(args.get("new_size"), "new_size")) * factor
    op, np_ = args.get("old_price"), args.get("new_price")
    if (op is None) != (np_ is None):
        raise UnitPriceError(
            "new_price" if op is not None else "old_price",
            "old_price and new_price travel together — one without the "
            "other asks the server to invent a sticker",
            "both, or neither (price unchanged is the shrinkflation case)")
    same_price = op is None
    # le prix s'écho comme ÉCRIT (précédent money/bogo : le sticker est
    # une notation, pas une valeur à renormaliser) ; le calcul, lui,
    # marche en Fraction
    op_s, np_s = (None if same_price else str(args.get("old_price")).strip(),
                  None if same_price else str(args.get("new_price")).strip())
    op = Fraction(1) if same_price else Fraction(_pos(op, "old_price"))
    np_ = op if same_price else Fraction(_pos(np_, "new_price"))
    if old_s == new_s and op == np_:
        raise UnitPriceError(
            "new_size", "nothing moved: same size, same price — this tool "
            "measures a hidden raise, not a no-op",
            "a change in size or price")
    lost = (old_s - new_s) / old_s          # dénominateur : ANCIENNE taille
    rise = (np_ / new_s) / (op / old_s) - 1  # dénominateur : NOUVELLE
    # les tailles affichées sont celles DITES (32 floz_us), pas la base —
    # un dénominateur nommable est un dénominateur dans l'unité du client
    old_said = "%s %s" % (_decimal_str(old_s / factor), canon)
    new_said = "%s %s" % (_decimal_str(new_s / factor), canon)
    if lost > 0:
        direction = "lost %s%% of product" % _pct(lost)["display"]
    elif lost < 0:
        direction = ("GAINED %s%% of product (upsizing)"
                     % _pct(-lost)["display"])
    else:
        direction = "same size"
    if rise > 0:
        move = "the price per %s ROSE %s%%" % (canon, _pct(rise)["display"])
    elif rise < 0:
        move = "the price per %s fell %s%%" % (canon, _pct(-rise)["display"])
    else:
        move = "flat per %s" % canon
    if lost != 0:
        note = ("%s — and %s: these are NOT the same number. The product "
                "change divides by the OLD size (%s), the per-unit change "
                "divides by the NEW size (%s). Exact fractions travel "
                "beside every display." % (direction, move, old_said,
                                           new_said))
    else:
        note = ("same size, price moved %s -> %s: straight price change — "
                "per-unit rise divides by the SAME size both sides (%s)"
                % (op_s, np_s, canon))
    return {"mode": "shrink", "unit": canon,
            "old_size": {"numerator": old_s.numerator,
                         "denominator": old_s.denominator},
            "new_size": {"numerator": new_s.numerator,
                         "denominator": new_s.denominator},
            "price": ("unchanged" if same_price else
                      {"old": op_s, "new": np_s}),
            "product_change": dict(_pct(lost), denominator="old size %s"
                                                   % old_said),
            "unit_price_change": dict(_pct(rise), denominator="new size %s"
                                                      % new_said),
            "note": note}


def run_unitprice(args):
    mode = args.get("mode")
    if mode not in MODES:
        raise UnitPriceError(
            "mode",
            "mode %r is not in the closed set — compare two offers, or "
            "measure one shrink, never both in one call" % (mode,),
            "one of: %s" % ", ".join(MODES))
    if mode == "compare":
        return _run_compare(args)
    return _run_shrink(args)
