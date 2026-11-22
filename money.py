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


def _iso_day(text, field):
    """Strict ISO calendar day — aging windows never accept slashed
    dates: an ambiguous day would silently move a bucket."""
    import datetime as _dt
    import re as _re
    if not isinstance(text, str) or not _re.fullmatch(
            r"\d{4}-\d{2}-\d{2}", text.strip()):
        raise MoneyError("%s must be an ISO calendar date YYYY-MM-DD "
                         "(slashed forms are refused: an ambiguous "
                         "day moves a bucket)" % field)
    try:
        return _dt.date.fromisoformat(text.strip())
    except ValueError:
        raise MoneyError("%s is not a real calendar date" % field)


def _dec_plain(text, field):
    """Plain decimal strings only in the ledger family: '1,234.56' is
    a LOCALE, not a number — the suite refuses and points to num/parse
    instead of guessing which grouping the writer meant."""
    import re as _re
    if not isinstance(text, str) or not _re.fullmatch(
            r"[+-]?\d+(\.\d+)?", text.strip()):
        raise MoneyError("%s must be a plain decimal string ('1234.56'); "
                         "grouped or locale forms go through num/parse "
                         "first (got %r)" % (field, text))
    return _dec(text.strip())


def money_aging(invoices, as_of, buckets=None):
    """Due-date aging of receivables (ROADMAP-FINANCE 1.1, sucked from
    the Ponte relances/impayés work). Invoices: due ISO day, amount
    and optional paid as decimal STRINGS. as_of is mandatory — the
    suite never reads a wall clock into a ledger (the midnight
    drift is a published lesson). Buckets default [30, 60, 90] ->
    labels 1-30, 31-60, 61-90, 90+ ; a window is left-open right-
    closed on days_overdue (30 -> 1-30, 31 -> 31-60). Fully paid ->
    status paid, excluded from open totals. Overpayment is a
    REFUSAL, not a negative bucket: reconciliation is another tool
    (ledger/apply-payments, roadmap 1.2). Rounding: exact Decimal,
    emitted at 2 places, half_up on the final quantize only."""
    if buckets is None:
        buckets = [30, 60, 90]
    if not isinstance(buckets, list) or not buckets:
        raise MoneyError("buckets must be a non-empty list of integers")
    prev = 0
    for b in buckets:
        if not isinstance(b, int) or isinstance(b, bool) or b <= prev:
            raise MoneyError(
                "buckets must be strictly increasing positive ints "
                "(got %r after %r) — a window has to start where the "
                "previous closed" % (b, prev))
        prev = b
    base = _iso_day(as_of, "as_of")
    labels = ["1-%d" % buckets[0]]
    labels += ["%d-%d" % (buckets[i] + 1, buckets[i + 1])
               for i in range(len(buckets) - 1)]
    labels.append("%d+" % buckets[-1])
    seen_ids = set()
    rows = []
    totals = {lab: Decimal(0) for lab in labels}
    counts = {lab: 0 for lab in labels}
    current = Decimal(0)
    current_n = 0
    paid_total = Decimal(0)
    paid_n = 0
    max_od = 0
    for i, inv in enumerate(invoices):
        due = _iso_day(inv["due"], "invoices[%d].due" % i)
        amt = _dec_plain(inv["amount"], "invoices[%d].amount" % i)
        paid = (_dec_plain(inv["paid"], "invoices[%d].paid" % i)
                if inv.get("paid") is not None else Decimal(0))
        if amt < 0:
            raise MoneyError("invoices[%d].amount is negative — aging "
                             "of credits is a ledger, not an AR report"
                             % i)
        out = amt - paid
        if out < 0:
            raise MoneyError(
                "invoices[%d] is overpaid by %s — reconciliation is "
                "ledger/apply-payments (roadmap 1.2), aging refuses "
                "negatives instead of inventing a bucket"
                % (i, out.copy_abs()))
        inv_id = inv.get("id")
        if inv_id is None:
            inv_id = str(i + 1)
        if inv_id in seen_ids:
            raise MoneyError("duplicate invoice id %r — ids are the "
                             "join key of the relance, not a label"
                             % inv_id)
        seen_ids.add(inv_id)
        days_overdue = (base - due).days
        if out == 0:
            status = "paid"
            paid_total += out
            paid_n += 1
        elif days_overdue <= 0:
            status = "current"
            current += out
            current_n += 1
        else:
            status = labels[-1]
            for lab, edge in zip(labels, buckets):
                if days_overdue <= edge:
                    status = lab
                    break
            totals[status] += out
            counts[status] += 1
            if days_overdue > max_od:
                max_od = days_overdue
        rows.append({"id": inv_id, "due": due.isoformat(),
                     "status": status, "days_overdue": days_overdue,
                     "outstanding": format(out.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")})
    q2 = Decimal(1).scaleb(-2)
    out_buckets = [{"label": "current", "count": current_n,
                    "total": format(current.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")}]
    out_buckets += [{"label": lab, "count": counts[lab],
                     "total": format(totals[lab].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")} for lab in labels]
    res = {"as_of": base.isoformat(), "buckets": out_buckets,
           "invoices": rows,
           "open_total": format((current + sum(totals.values())).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f"),
           "paid_count": paid_n,
           "max_days_overdue": max_od,
           "count": len(rows)}
    return res
