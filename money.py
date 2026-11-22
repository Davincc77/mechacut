"""Deterministic money math (Bundle 4): prorate, split.

Decimal-only. Amounts enter as strings; every intermediate is exact.
The rounding step is the LAST operation and its mode is explicit.
"""

from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_CEILING, \
    ROUND_FLOOR, ROUND_DOWN

from numfmt import _dec  # shared value -> Decimal coercion (raises NumberError)
from dates import parse_date, DateError

_MODES = {
    "half_even": ROUND_HALF_EVEN, "half_up": ROUND_HALF_UP,
    "ceil": ROUND_CEILING, "floor": ROUND_FLOOR, "trunc": ROUND_DOWN,
}


class MoneyError(Exception):
    pass


def _d(s):
    return _dec(s)


def money_prorate(amount, cycle_start, cycle_end, service_start, service_end,
                  places=2, mode="half_up", inclusive=True,
                  clamp=True):
    """Pro-rate `amount` (the full-cycle price) over the service window
    inside a billing cycle. Rule (documented, closed):

      prorated = amount * covered_days / cycle_days

    cycle_days counts days from cycle_start to cycle_end, inclusive of both
    ends when `inclusive` (the default); service window clamped to the cycle
    when `clamp` (else days outside simply don't count). covered_days uses
    the same inclusiveness. Exact fraction reported before rounding.
    """
    try:
        cs = parse_date(cycle_start)["date"]
        ce = parse_date(cycle_end)["date"]
        ss = parse_date(service_start)["date"]
        se = parse_date(service_end)["date"]
    except DateError as e:
        raise MoneyError(str(e))
    from datetime import date
    def dd(x):
        y, m, d = (int(p) for p in x.split("-"))
        return date(y, m, d)
    cs_d, ce_d, ss_d, se_d = dd(cs), dd(ce), dd(ss), dd(se)
    if ce_d < cs_d or se_d < ss_d:
        raise MoneyError("cycle_end must be >= cycle_start and "
                         "service_end >= service_start")
    span = 1 if inclusive else 0
    cycle_days = (ce_d - cs_d).days + span
    if cycle_days <= 0:
        raise MoneyError("cycle spans zero days")
    lo, hi = (ss_d, se_d)
    if clamp:
        lo = max(lo, cs_d)
        hi = min(hi, ce_d)
    covered = (hi - lo).days + span
    if covered < 0:
        covered = 0
    amt = _d(amount)
    if places < 0 or places > 12 or mode not in _MODES:
        raise MoneyError("places must be 0-12 and mode one of "
                         + ", ".join(sorted(_MODES)))
    exact = amt * Decimal(covered) / Decimal(cycle_days)
    rounded = exact.quantize(Decimal(1).scaleb(-places),
                             rounding=_MODES[mode])
    return {
        "prorated": format(rounded, "f"),
        "amount": format(amt, "f"),
        "covered_days": covered,
        "cycle_days": cycle_days,
        "ratio": {"numerator": covered, "denominator": cycle_days},
        "exact_decimal": format(exact.quantize(
            Decimal(1).scaleb(-12), rounding=ROUND_HALF_EVEN), "f"),
        "places": places, "mode": mode, "inclusive": inclusive,
    }


def money_split(total, participants, mode="remainder_order"):
    """Split `total` among participants deterministically to the cent:
    equal share floor + the leftover cents handed out by the closed rule.

    mode "remainder_order": leftover cents go to the first participants in
    list order (stable, auditable — who got the extra cent is a function of
    position, not of hashing luck).
    participants: list of names, OR list of {name, weight?} — weights split
    proportionally, floor to places, remainder by order.
    """
    amt = _d(total)
    if not isinstance(participants, list) or not participants:
        raise MoneyError("participants must be a non-empty list")
    names, weights = [], []
    for p in participants:
        if isinstance(p, str):
            names.append(p)
            weights.append(Decimal(1))
        elif isinstance(p, dict) and "name" in p:
            names.append(str(p["name"]))
            w = p.get("weight", 1)
            try:
                wd = _dec(w)
            except Exception:
                raise MoneyError("weight must be numeric for %r" % p["name"])
            if wd < 0:
                raise MoneyError("weights must be >= 0")
            weights.append(wd)
        else:
            raise MoneyError("participant must be a name or {name, weight?}")
    if mode not in ("remainder_order",):
        raise MoneyError("mode must be \"remainder_order\"")
    total_w = sum(weights)
    if total_w == 0:
        raise MoneyError("total weight is zero")
    cents = amt * 100
    raw = [cents * w / total_w for w in weights]
    floors = [r.quantize(Decimal(1), rounding=ROUND_FLOOR) for r in raw]
    leftover = int(cents.quantize(Decimal("0.01"),
                                  rounding=ROUND_HALF_EVEN)
                   - sum(floors))
    if leftover < 0:
        leftover = 0
    # hand out leftover cents by fractional part desc, ties by order
    order = sorted(range(len(raw)),
                   key=lambda i: (-(raw[i] - floors[i]), i))
    shares = list(floors)
    for k in range(leftover):
        shares[order[k % len(order)]] += 1
    out = []
    for name, s in zip(names, shares):
        d = (s / Decimal(100)).quantize(Decimal("0.01"))
        out.append({"participant": name, "share": format(d, "f")})
    assigned = sum(Decimal(x["share"]) for x in out)
    return {"shares": out, "total": format(amt, "f"),
            "assigned": format(assigned, "f"),
            "remainder_cents": leftover,
            "unassigned": format(amt - assigned, "f"),
            "mode": mode}


ISO_DECIMALS = {
    "USD": 2, "EUR": 2, "GBP": 2, "BRL": 2, "INR": 2, "CAD": 2, "AUD": 2,
    "CHF": 2, "CNY": 2, "MXN": 2, "ARS": 2, "ZAR": 2, "TRY": 2, "SAR": 2,
    "NGN": 2, "EGP": 2, "RUB": 2, "PLN": 2, "COP": 2, "PEN": 2, "IDR": 2,
    "THB": 2, "AED": 2, "ILS": 2, "SEK": 2, "NOK": 2, "DKK": 2, "KWD": 3,
    "JPY": 0, "KRW": 0, "CLP": 0, "VND": 0, "ISK": 0,
}


def num_fx(amount, rate, to, precision=None):
    """Explicit-rate FX: the CALLER supplies the rate; this suite does the
    exact Decimal multiplication and the ISO-4217 rounding. Never a
    network call — a model guessing today's EUR/USD is the bug we refuse
    to serve; applying YOUR rate with banker's rounding is the fact."""
    if to not in ISO_DECIMALS:
        raise MoneyError("unknown currency %r (closed table of %d)"
                         % (to, len(ISO_DECIMALS)))
    try:
        v = Decimal(str(amount)) * Decimal(str(rate))
    except Exception:
        raise MoneyError("amount and rate must be numeric strings")
    dec = ISO_DECIMALS[to] if precision is None else int(precision)
    q = v.quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_EVEN)
    return {"result": format(q, "f"), "currency_to": to,
            "decimals": dec, "method": "half_even",
            "minor_units": int(q.scaleb(dec)),
            "rate_used": format(Decimal(str(rate)), "f"), "exact_before_rounding":
            format(v, "f")[:30]}
