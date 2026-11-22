"""pointskit — /api/v1/money/points : la valeur d'un point, RENDUE EXACTE.

La formule est publiée, mot à mot (cardcompass.app, nov-2026) :

    cpp = (cash price − cash still paid) ÷ points × 100

Six calculateurs web rejoués le 22-nov-2026 (cardcompass, card-savvy,
usecalcpro, rewardsmaxing, milesbuyer, calculator.academy) donnent la
MÊME formule et des ARITHMÉTIQUES contraires sur l'arrondi : cardcompass
écrit « 1.49 » là où l'exact est 1081/725 = 1,491034… ; milesbuyer
écrit « 13× » là où 8 ÷ 0,6 = 40/3 = 13,33. Ici la fraction EXACTE
sort avec la décimale — comme money/crossover sur les tarifs.

CE QUE LE LIVE NE DONNE PAS ET CE QUE NOUS N'EMBARQUONS PAS : la
valorisation d'un programme (floor / baseline / ceiling chez
rewardsmaxing) bouge « when programs make material changes » — c'est un
ARGUMENT du caller, jamais une table figée dans le module. Le verdict
contre le floor fourni est rendu NOMMÉ (card-savvy sur Bilt : « don't
redeem toward rent (0.55¢) unless there is no other option » — 0,55 =
11/20 exact).

La TRAPPE publiée est la soustraction AVANT la division : un award
« $450 cash ou 25 000 points + 35 $ de taxes » vaut (450−35)÷25 000×100
= 83/50 = 1,66 — pas 1,80 (le taux d'arrondi que rend « $450/25 000 »).
Les rewards FORGONÉS (les points qu'on aurait gagnés en payant cash,
forme publiée chez calculator.academy) sont le troisième terme, en
argument. Le « ×100 » est toujours 1/100 de l'UNITÉ MAJEURE de la
devise — convention NOMMÉE (le ¥ n'a pas de centimes : le nombre reste
des centièmes de yen, dit comme tel).

Le break-even points-vs-cashback (formulaire
(cashback_annuel + fee) ÷ points_annuels) n'est PAS ici : c'est
money/crossover (déjà livré), nommé dans la réponse.

Rang multi-voies (cash / gift card / portail / transfert — les cinq
voies classées chez SwitchWize) : tri sur la FRACTION, égalités
nommées, écart best÷worst rendu en fraction (le « 13× » arrondi en
dessous ailleurs). Zéro fetch, zéro conseil financier : vos nombres,
notre arithmétique.
"""

from decimal import Decimal, getcontext, ROUND_HALF_UP
from fractions import Fraction

from money import ISO_DECIMALS

getcontext().prec = 30


class PointsError(ValueError):
    def __init__(self, field, message, expected=None):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected or _EXPECTED.get(field, "")


_EXPECTED = {
    "currency": "ISO code from the closed table (USD, EUR, GBP, BRL…)",
    "routes": "non-empty array of {name, points, cash_price, "
              "cash_still_paid?, rewards_forgone?} — all values as "
              "decimal STRINGS",
    "name": "short route label, unique across routes (cash, portal, "
            "transfer, gift_card…)",
    "points": "positive integer decimal string, e.g. '29000'",
    "cash_price": "the CASH price of the same thing, major units, "
                  "e.g. '438'",
    "cash_still_paid": "taxes/fees you still pay on the award, e.g. "
                       "'5.60' (default '0')",
    "rewards_forgone": "value of the points/cashback you would have "
                       "EARNED paying cash, major units (default '0')",
    "floor": "cents-per-point you would NOT go below — YOUR supplied "
             "valuation, never a table we embed",
    "baseline": "optional supplied baseline cpp",
    "ceiling": "optional supplied ceiling cpp",
    "points_balance": "optional: your balance, integer string — needs "
                      "valued_at",
    "valued_at": "a route name from routes[] or an explicit cpp "
                 "decimal string — never guessed",
    "points_per_dollar": "optional earning rate (e.g. '3' points per "
                         "unit spent); effective return % then rendered "
                         "against each route's cpp",
}

_CPP_PLACES = Decimal("0.000000000001")  # 12 places for the decimal
_CPP_2DP = Decimal("0.01")               # the "press" rounding


def _num(value, field):
    if value is None or (isinstance(value, str) and not value.strip()):
        raise PointsError(field, "missing or empty (pass a decimal "
                                 "string)")
    if not isinstance(value, str):
        raise PointsError(field, "pass a decimal STRING — got %s; the "
                                 "string contract keeps every replay "
                                 "byte-exact" % type(value).__name__)
    t = value.strip().replace("\u00A0", " ").replace(" ", "").replace("_", "")
    t = t.replace(",", ".")
    import re
    if not re.match(r"^[+-]?(\d+(\.\d*)?|\.\d+)$", t):
        raise PointsError(field, "not a decimal number: %r" % value)
    return Decimal(t)


def _frac_of(value, field):
    return Fraction(_num(value, field))


def _dec(fr, places=_CPP_PLACES):
    d = Decimal(fr.numerator) / Decimal(fr.denominator)
    return format(d.quantize(places, rounding=ROUND_HALF_UP), "f")


def _exact(fr):
    return {"numerator": str(fr.numerator),
            "denominator": str(fr.denominator)}


def _money(d, dec):
    q = d.quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP) \
        if dec else d.to_integral_value(rounding=ROUND_HALF_UP)
    return format(q, "f")


def _route(name, raw, idx):
    if not isinstance(raw, dict):
        raise PointsError("routes",
                          "routes[%d] is %s, expected an object"
                          % (idx, type(raw).__name__))
    label = raw.get("name")
    if not isinstance(label, str) or not label.strip():
        raise PointsError("routes", "routes[%d].name: a short unique "
                                    "label is required" % idx)
    pts = _frac_of(raw.get("points"), "points")
    if pts <= 0:
        raise PointsError("points", "routes[%d] (%s): points must be > 0 "
                                    "— %r is not a redemption"
                          % (idx, label.strip(), raw.get("points")))
    if pts.denominator != 1:
        raise PointsError("points", "routes[%d] (%s): points must be a "
                                    "whole number — %r"
                          % (idx, label.strip(), raw.get("points")))
    cash = _frac_of(raw.get("cash_price"), "cash_price")
    still = _frac_of(raw.get("cash_still_paid") or "0", "cash_still_paid")
    forgone = _frac_of(raw.get("rewards_forgone") or "0", "rewards_forgone")
    net = cash - still - forgone
    if net < 0:
        raise PointsError("cash_price", "routes[%d] (%s): the award "
                                        "costs MORE in cash than paying "
                                        "cash (net %s) — that is not a "
                                        "valuation, that is 'pay with "
                                        "cash', say it in words"
                          % (idx, label.strip(), _dec(net,
                                                      Decimal("0.01"))))
    return {"name": label.strip(), "points": pts, "cash_price": cash,
            "cash_still_paid": still, "rewards_forgone": forgone,
            "net_cash_value": net, "cpp": net / pts * 100}


def run_points(args):
    currency = (args.get("currency") or "").strip().upper()
    if currency not in ISO_DECIMALS:
        raise PointsError("currency", "unknown ISO code %r (closed "
                                      "table of %d majors)"
                          % (args.get("currency"), len(ISO_DECIMALS)))
    dec = ISO_DECIMALS[currency]

    raw_routes = args.get("routes")
    if not isinstance(raw_routes, list) or not raw_routes:
        raise PointsError("routes", "an array of at least one "
                                    "redemption path is required")
    routes = [_route(r.get("name"), r, i) if isinstance(r, dict)
              else _route(None, r, i) for i, r in enumerate(raw_routes)]
    seen = {}
    for r in routes:
        if r["name"].lower() in seen:
            raise PointsError("routes", "duplicate route name %r — the "
                                        "ranking and valued_at both key "
                                        "on the name" % r["name"])
        seen[r["name"].lower()] = True

    supplied = {}
    for k in ("floor", "baseline", "ceiling"):
        if args.get(k) not in (None, ""):
            v = Fraction(_num(args[k], k))
            if v < 0:
                raise PointsError(k, "a cents-per-point valuation "
                                     "cannot be negative")
            supplied[k] = v

    out_routes = []
    for r in routes:
        row = {
            "name": r["name"],
            "points": _dec(r["points"], Decimal(1)),
            "cash_price": _dec(r["cash_price"], Decimal("0.01")),
            "cash_still_paid": _dec(r["cash_still_paid"], Decimal("0.01")),
            "rewards_forgone": _dec(r["rewards_forgone"], Decimal("0.01")),
            "net_cash_value": _dec(r["net_cash_value"], Decimal("0.01")),
            "cpp": _dec(r["cpp"]),
            "cpp_exact": _exact(r["cpp"]),
            "cpp_press_2dp": _dec(r["cpp"], _CPP_2DP),
        }
        if "floor" in supplied:
            f = supplied["floor"]
            row["vs_floor"] = {
                "floor": _dec(f, Decimal("0.01")),
                "verdict": ("at-or-above floor: the redemption is "
                            "worth taking" if r["cpp"] >= f else
                            "BELOW floor: 'pay with cash' is the named "
                            "answer (card-savvy's own rule)"),
                "below": r["cpp"] < f,
            }
        out_routes.append(row)

    # ranking on the EXACT fraction; ties named, never melted
    order = sorted(routes, key=lambda r: r["cpp"], reverse=True)
    ranking = []
    i = 0
    while i < len(order):
        j = i
        group = []
        while j < len(order) and order[j]["cpp"] == order[i]["cpp"]:
            group.append(order[j]["name"])
            j += 1
        ranking.append({"rank": len(ranking) + 1, "names": group,
                        "cpp": _dec(order[i]["cpp"]),
                        "tied": len(group) > 1})
        i = j
    best, worst = order[0]["cpp"], order[-1]["cpp"]
    spread = None
    if len(routes) >= 2 and best > 0 and worst > 0:
        ratio = best / worst
        spread = {
            "ratio": _dec(ratio, Decimal("0.01")),
            "ratio_exact": _exact(ratio),
            "rule": "best ÷ worst on the EXACT fractions — milesbuyer "
                    "prints '13×' where 8 ÷ 0.6 = 40/3 = 13.33…; the "
                    "floor-of-the-rounding is their call, the fraction "
                    "is ours",
        }

    out = {
        "currency": currency,
        "routes": out_routes,
        "ranking": ranking,
        "formula": "cpp = (cash_price − cash_still_paid − "
                   "rewards_forgone) ÷ points × 100",
        "cpp_unit": "cents per point = 1/100 of the MAJOR unit of %s, "
                    "whatever the currency has as official minor unit "
                    "(a JPY cpp is still hundredths of a yen — named, "
                    "never melted)" % currency,
        "exactness_note": "no intermediate rounding: published pages "
                          "print 1.49 where the exact value is "
                          "1081/725 = 1.491034… (cardcompass) and '13×' "
                          "where the exact ratio is 40/3 (milesbuyer); "
                          "subtract BEFORE dividing — '450/25000' = "
                          "1.80 is the rate you get by FORGETTING the "
                          "35 of taxes (the real answer is 83/50 = "
                          "1.66)",
        "not_here": "the break-even between a points card and a "
                    "cashback card ((cashback + fee) ÷ points) is "
                    "TWO-TARIFF arithmetic: POST /api/v1/money/crossover",
    }
    if spread:
        out["spread"] = spread
    if supplied:
        out["supplied_valuations"] = {k: _dec(v, Decimal("0.01"))
                                      for k, v in supplied.items()}
        out["valuation_provenance"] = (
            "floor/baseline/ceiling are YOUR arguments, quoted back: "
            "program valuations move when 'programs make material "
            "changes' (rewardsmaxing's own note) — a table baked in "
            "here would rot, so none is")

    if args.get("points_balance") not in (None, ""):
        bal = _frac_of(args["points_balance"], "points_balance")
        if bal <= 0 or bal.denominator != 1:
            raise PointsError("points_balance", "a positive whole "
                                                "number string")
        va = args.get("valued_at")
        if not isinstance(va, str) or not va.strip():
            raise PointsError("valued_at", "required with "
                                            "points_balance — a route "
                                            "name or an explicit cpp; "
                                            "never guessed")
        va = va.strip()
        by_name = {r["name"].lower(): r for r in routes}
        if va.lower() in by_name:
            cpp, source = by_name[va.lower()]["cpp"], "route %s" \
                % by_name[va.lower()]["name"]
        else:
            try:
                cpp, source = Fraction(_num(va, "valued_at")), \
                    "supplied cpp"
            except PointsError:
                raise PointsError(
                    "valued_at", "%r is neither a route name nor a "
                                 "decimal cpp — value = points × cpp ÷ "
                                 "100" % va)
        value = bal * cpp / 100
        out["balance"] = {
            "points": _dec(bal, Decimal(1)),
            "valued_at": source,
            "cpp": _dec(cpp),
            "cpp_exact": _exact(cpp),
            "value": _money(Decimal(value.numerator)
                            / Decimal(value.denominator), dec),
            "value_exact": _exact(value),
            "rule": "balance value = points × cpp ÷ 100 (milesbuyer's "
                    "own arithmetic: 100 000 Amex points × 0.6 ¢ = "
                    "600.00 in statement credit)",
        }

    if args.get("points_per_dollar") not in (None, ""):
        ppd = _frac_of(args["points_per_dollar"], "points_per_dollar")
        if ppd <= 0:
            raise PointsError("points_per_dollar", "must be > 0")
        out["effective_return"] = {
            "points_per_dollar": _dec(ppd, Decimal("0.01")),
            "per_route": [
                {"name": r["name"],
                 "return_pct": _dec(ppd * r["cpp"], Decimal("0.01")),
                 "return_pct_exact": _exact(ppd * r["cpp"])}
                for r in routes],
            "rule": "effective return % = points per unit spent × cpp "
                    "(usecalcpro: 3 × 1.5 = 4.5 % — the ×100 of cpp and "
                    "the ×100 of the percent cancel)",
        }

    out["scope_note"] = (
        "your numbers, our arithmetic: no fetched prices, no program "
        "valuations, no points advice — and cardcompass's own rule "
        "held: 'never compare programs on cents per point alone'; the "
        "cpp is a property of ONE redemption, rendered exactly")
    return out
