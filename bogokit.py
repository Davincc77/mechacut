"""bogokit — /money/bogo : le pourcentage que la CAISSE applique vraiment.

Le panneau dit « BUY ONE GET ONE 50 % OFF ». Trois arnaques d'arithmétique
de comptoir, rendues impossibles, tout en Decimal exact :

  1. L'ASSIETTE. Le 50 % ne porte que sur le DEUXIEME article — et, règle
     de détail PUBLIÉE (« retailers almost always apply the 50%-off
     portion to the lower-priced of the two items », convertitive.com),
     sur le MOINCHER des deux. Deux prix égaux : la paire est à -25 %,
     pas -50 % (publié : dothecalculation.com, disco plugin 2026). Deux
     prix inégaux 60+40 : -20 % sur la paire — ni 25 % ni 50 %.
  2. LE RESTE. Trois articles = UNE paire + UN article payé PLEIN :
     3 × 25 $ sous BOGO 50 % = 62,50 $ payés, effectif 50/3 % = 16,6667 %.
     Le serveur ne devine PAS quel article apparie lequel : les paires
     sont DONNÉES en argument, l'article impair va dans `extras`.
     (Doctrine : pick, don't transcribe — la grammaire fermée ne décompose
     pas l'intention du client, elle la reçoit.)
  3. L'EMPILEMENT. Coupon -30 % sur un BOGO 50 % : les pourcentages se
     MULTIPLIENT, jamais s'additionnent. La vendeuse qui refuse le coupon
     « parce que 50 > 30 » (r/Millennials 1k072jr) a tort dans les deux
     sens : le BOGO ne vaut 25 % que si les prix sont égaux, et 25 % puis
     30 % = 47,5 %, pas 55 %.

Grammaire fermée : offers = {bogo_free, bogo_percent} ; hors grammaire =
refus NOMMÉ avec la forme attendue. Nombres au format maison
(Decimal(str), point décimal) — « 81,90 » est un refus nommé,
/api/v1/num/parse est l'outil d'avant. Plafonds : 12 paires, 12 extras.

La formule et la trace sont rendues dans la réponse — pas de boîte noire.
"""
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

Q4 = Decimal("0.0001")
OFFERS = ("bogo_free", "bogo_percent")
MAX_PAIRS = 12
MAX_EXTRAS = 12
RULE_SECOND = "cheapest_discounted"


class BogoError(Exception):
    def __init__(self, field, message, expected):
        self.field = field
        self.message = message
        self.expected = expected
        Exception.__init__(self, message)


def _d(x, what):
    try:
        v = Decimal(str(x))
    except Exception:
        raise BogoError(
            what,
            "%s: %r is not a number — dot decimal here ('40.00'); "
            "locale forms go through /api/v1/num/parse first" % (what, x),
            "decimal string, e.g. \"40.00\"")
    if not v.is_finite():
        raise BogoError(what, "%s must be finite, got %r" % (what, x),
                        "finite decimal")
    return v


def _money(v):
    return format(v, "f")


def _pct(numer, denom):
    """(numer/denom x 100) displayed at 4 dp HALF_UP + the EXACT fraction.

    The percent of a discount is a RATIO; the ratio is the product, so the
    exact fraction travels next to the rounded display — the display
    rounds, the claim does not.
    """
    frac = Fraction(numer) / Fraction(denom) * 100
    disp = (Decimal(numer) / Decimal(denom) * 100).quantize(
        Q4, rounding=ROUND_HALF_UP)
    return _money(disp), frac.numerator, frac.denominator


def run_bogo(args):
    offer = args.get("offer")
    if offer not in OFFERS:
        raise BogoError(
            "offer",
            "unknown offer %r — the BOGO family is closed" % (offer,),
            "one of: bogo_free, bogo_percent")

    pairs_raw = args.get("pairs")
    if not isinstance(pairs_raw, list) or not pairs_raw:
        raise BogoError("pairs", "pairs is required — each entry holds "
                        "EXACTLY two prices",
                        "[[\"40.00\",\"60.00\"], ...]")
    if len(pairs_raw) > MAX_PAIRS:
        raise BogoError("pairs", "too many pairs (%d) — this tool stops "
                        "at %d" % (len(pairs_raw), MAX_PAIRS),
                        "at most %d pairs" % MAX_PAIRS)
    parsed = []
    for i, p in enumerate(pairs_raw):
        if not isinstance(p, list) or len(p) != 2:
            raise BogoError(
                "pairs[%d]" % i,
                "a pair must hold EXACTLY two prices — an odd item "
                "belongs in extras (paid full), never in a pair",
                "[price_a, price_b]")
        a = _d(p[0], "pairs[%d][0]" % i)
        b = _d(p[1], "pairs[%d][1]" % i)
        if a <= 0 or b <= 0:
            raise BogoError("pairs[%d]" % i,
                            "prices must be > 0, got [%s, %s]"
                            % (_money(a), _money(b)),
                            "positive decimal")
        parsed.append((a, b))

    extras_raw = args.get("extras") or []
    if not isinstance(extras_raw, list):
        raise BogoError("extras", "extras must be a list of prices",
                        "[\"25.00\", ...]")
    if len(extras_raw) > MAX_EXTRAS:
        raise BogoError("extras", "too many extras (%d) — this tool stops "
                        "at %d" % (len(extras_raw), MAX_EXTRAS),
                        "at most %d items" % MAX_EXTRAS)
    extras = []
    for i, x in enumerate(extras_raw):
        v = _d(x, "extras[%d]" % i)
        if v <= 0:
            raise BogoError("extras[%d]" % i,
                            "prices must be > 0, got %s" % _money(v),
                            "positive decimal")
        extras.append(v)

    second = args.get("second_percent")
    sec = None
    if offer == "bogo_percent":
        if second is None:
            raise BogoError(
                "second_percent",
                "bogo_percent needs second_percent — the percent off "
                "the CHEAPER item, as printed on the sign",
                "\"50\"")
        sec = _d(second, "second_percent")
        if not (Decimal(0) < sec <= Decimal(100)):
            raise BogoError("second_percent",
                            "second_percent must be in (0,100], got %s"
                            % _money(sec),
                            "percent string, e.g. \"50\"")
    elif second is not None:
        raise BogoError(
            "second_percent",
            "bogo_free means the cheaper item is FREE — remove "
            "second_percent, or switch offer to bogo_percent",
            "absent for bogo_free")

    coupon = args.get("coupon_percent")
    cp = None
    if coupon is not None:
        cp = _d(coupon, "coupon_percent")
        if not (Decimal(0) < cp <= Decimal(100)):
            raise BogoError("coupon_percent",
                            "coupon_percent must be in (0,100], got %s"
                            % _money(cp),
                            "percent string, e.g. \"30\"")

    # ---- the maths, exact Decimal, each step named ------------------
    # bogo_free IS bogo_percent with the second item at 100 % off — one
    # closed branch, no duplicated arithmetic to drift apart.
    hundred = Decimal(100)
    sec_eff = hundred if sec is None else sec
    pair_rows = []
    full = Decimal(0)
    paid_before = Decimal(0)
    unequal = 0
    for a, b in parsed:
        hi, lo = (a, b) if a >= b else (b, a)
        full += a + b
        paid_lo = lo * (hundred - sec_eff) / hundred
        expr = "%s + %sx(1 - %s/100) = %s" % (
            _money(hi), _money(lo), _money(sec_eff),
            _money(hi + paid_lo))
        paid_pair = hi + paid_lo
        paid_before += paid_pair
        if hi != lo:
            unequal += 1
        pair_rows.append({
            "a": _money(a), "b": _money(b),
            "pricier": _money(hi), "cheaper": _money(lo),
            "paid": _money(paid_pair), "expression": expr,
            "same_price": hi == lo,
        })
    for v in extras:
        full += v
        paid_before += v

    paid = paid_before
    if cp is not None:
        paid = paid_before * (hundred - cp) / hundred
    saved = full - paid

    disp, num, den = _pct(saved, full)
    # the BOGO step alone (before any coupon), as a display percent:
    bogo_saved = full - paid_before
    bogo_disp, _, _ = _pct(bogo_saved, full)

    notes = []
    if offer == "bogo_percent":
        notes.append(
            "the %s%% off applies to the CHEAPER item of each pair only "
            "— published retail rule, not a guess" % _money(sec))
    else:
        notes.append("the cheaper item of each pair is FREE")
    if unequal:
        notes.append("%d of %d pairs are UNEQUAL-priced — the promo hits "
                     "the cheaper one, so the pair discount is smaller "
                     "than the equal-price case" % (unequal, len(parsed)))
    if extras:
        notes.append("%d item(s) paid FULL price — BOGO pairs, the odd "
                     "one out is not covered" % len(extras))
    if cp is not None:
        lie = (Decimal(bogo_disp) + cp).quantize(Q4, rounding=ROUND_HALF_UP)
        notes.append("the coupon stacks on the POST-BOGO total: %s%% then "
                     "%s%% -> %s%% off the bill, NOT %s%% — percentages "
                     "multiply, never add"
                     % (bogo_disp, _money(cp), disp, _money(lie)))

    out = {
        "offer": offer,
        "rule_second": RULE_SECOND,
        "pairs": pair_rows,
        "extras": [_money(v) for v in extras],
        "totals": {
            "full": _money(full),
            "paid_before_coupon": _money(paid_before),
            "paid": _money(paid),
            "saved": _money(saved),
        },
        "effective": {
            "percent": disp,
            "exact_fraction": {"numerator": num, "denominator": den},
            "rounded": "HALF_UP 4dp",
            "bogo_step_only": bogo_disp,
        },
        "bill": {
            "ad_says": ("buy one, get the second %s%% off" % _money(sec)
                        if offer == "bogo_percent"
                        else "buy one, get one free"),
            "bill_says": "%s%% off the whole purchase" % disp,
            "note": " ; ".join(notes),
        },
    }
    if sec is not None:
        out["second_percent"] = _money(sec)
    if cp is not None:
        out["coupon_percent"] = _money(cp)
    return out
