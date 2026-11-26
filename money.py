"""Deterministic money math (Bundle 4): prorate, split.

Decimal-only. Amounts enter as strings; every intermediate is exact.
The rounding step is the LAST operation and its mode is explicit.
"""

from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_CEILING, \
    ROUND_FLOOR, ROUND_DOWN
import re

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
                  clamp=True, basis="cycle", order="product",
                  compare=False):
    """Pro-rate `amount` (the full-cycle price) over the service window
    inside a billing cycle. Rule (documented, closed):

      prorated = amount * covered_days / cycle_days

    cycle_days counts days from cycle_start to cycle_end, inclusive of both
    ends when `inclusive` (the default); service window clamped to the cycle
    when `clamp` (else days outside simply don't count). covered_days uses
    the same inclusiveness. Exact fraction reported before rounding.

    CONVENTIONS (bundle 119) -- the rent-proration fight published in
    full: r/personalfinance 9sqw2j (two formulas in ONE thread:
    "1000/30 = 33.33 per day x 18 = 600" -- the poster rounds his own
    result silently -- and "[19/30]x[1229]" with the other bound),
    r/Landlord 1hitzjq (the banker's month as published rule: "divided
    by 30 days, REGARDLESS of actual number of days"), r/RealEstate
    1idq3vr (the annual-over-365 rule: "(annual rent / 365) x 22"),
    r/Landlord 1fep9e6 (the move-out-day bound named by the landlord
    himself) and r/legaladvice 66vwu9 (noon vs midnight: a DATE is not
    a MOMENT). Three closed sets, every member named by the people who
    use it -- we name them, we never pick one in silence:

      basis:  "cycle"   -- denominator = days in the cycle window (28,
                          29, 30 or 31). The default, legacy-stable.
              "month30" -- banker's / landlord month: daily rate always
                          = amount / 30, whatever the real month.
              "year365" -- amount is monthly; daily rate = amount*12/365.
      order:  "product"  -- multiply first, round LAST (one rounding).
              "quotient" -- the landlord's formula: round the DAILY rate
                          to `places` first, then multiply by days.
      compare -- adds the "conventions" block: both orders side by side
                          with the signed delta, and the two OBJECTS
                          (occupied vs unoccupied) with the sum identity
                          -- r/personalfinance 1b5p04y: the same word
                          "prorated" meant the partial month payment in
                          one lease and the end-of-lease-to-end-of-month
                          delta in the renewal, and the tenant fought a
                          phantom error with true numbers.

    Defaults (basis=cycle, order=product, compare=False) render the
    pre-119 output byte for byte -- the settle contract, mirrored.
    A date carrying a TIME (noon on the 12th, epoch, RFC header) is
    REFUSED BY NAME: no thread publishes a day fraction as a unit;
    the two published readings of a noon lease are day 12 counted or
    not -- that is the `inclusive` argument, never 11.5.
    """
    _refuse_time_grain(cycle_start, "cycle_start")
    _refuse_time_grain(cycle_end, "cycle_end")
    _refuse_time_grain(service_start, "service_start")
    _refuse_time_grain(service_end, "service_end")
    if basis not in ("cycle", "month30", "year365"):
        raise MoneyError("basis must be cycle|month30|year365 (closed set) "
                         "-- cycle = real days of the window, month30 = the "
                         "banker's month (r/Landlord 1hitzjq), year365 = "
                         "amount*12/365 daily (r/RealEstate 1idq3vr)")
    if order not in ("product", "quotient"):
        raise MoneyError("order must be product|quotient (closed set) "
                         "-- product rounds once at the end, quotient "
                         "rounds the daily rate first (the landlord's "
                         "formula in r/personalfinance 9sqw2j)")
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
    q = Decimal(1).scaleb(-places)
    # Daily rate before any rounding, per the named basis. cycle is the
    # legacy line; month30 is the banker's month (1hitzjq: "divided by
    # 30 days, REGARDLESS"); year365 treats the amount as monthly and
    # prices the day at amount*12/365 (1idq3vr top rule).
    if basis == "cycle":
        daily = amt / Decimal(cycle_days)
        num, den = covered, cycle_days
    elif basis == "month30":
        daily = amt / Decimal(30)
        num, den = covered, 30
    else:  # year365
        daily = amt * 12 / Decimal(365)
        num, den = covered * 12, 365
    # Legacy operation order preserved for basis=cycle (amt * covered
    # first, divide after) -- the 28-significant-digit rounding of the
    # two orders is not always identical, and the default render must
    # stay byte-identical to the pre-119 module.
    product_exact = amt * Decimal(num) / Decimal(den)
    ratio = {"numerator": num, "denominator": den}
    prod = product_exact.quantize(q, rounding=_MODES[mode])
    daily_r = daily.quantize(q, rounding=_MODES[mode])
    quot = daily_r * Decimal(covered)
    chosen = quot if order == "quotient" else prod
    out = {
        "prorated": format(chosen, "f"),
        "amount": format(amt, "f"),
        "covered_days": covered,
        "cycle_days": cycle_days,
        "ratio": ratio,
        "exact_decimal": format((quot if order == "quotient" else
                                 product_exact).quantize(
            Decimal(1).scaleb(-12), rounding=ROUND_HALF_EVEN), "f"),
        "places": places, "mode": mode, "inclusive": inclusive,
    }
    invoked = basis != "cycle" or order != "product" or compare
    if invoked:
        out["basis"] = basis
        out["order"] = order
    if order == "quotient":
        # The rounded daily IS the instrument: show the rate the whole
        # convention multiplies, so 33.33x18=599.94 is auditable at a
        # glance (9sqw2j's poster rounds his result instead).
        out["daily_rounded"] = format(daily_r, "f")
    if compare:
        # The pair render: both orders side by side with the signed
        # delta, and both OBJECTS of the same word (1b5p04y). Never a
        # silent average: the delta IS the negotiation.
        out["conventions"] = {
            "orders": {
                "product": format(prod, "f"),
                "quotient": format(quot, "f"),
                "delta_product_minus_quotient":
                    format(prod - quot, "f"),
                "chosen": order,
            },
            "objects": {
                "occupied": format(chosen, "f"),
                "unoccupied": format(amt - chosen, "f"),
                "amount": format(amt, "f"),
                "sum_equals_amount":
                    (chosen + (amt - chosen)) == amt,
            },
        }
    return out


_EPOCH_RE = re.compile(r"-?\d{8,}(?:\.\d+)?\Z")
_WEEKDAY_RE = re.compile(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,\s", re.I)
_MOMENT_RE = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d")


class GrainRefusal(MoneyError):
    """A date argument carrying a MOMENT on the prorate path (bundle
    119). Carries field+value so the route layer can show the two
    whole-day readings instead of only the refusal."""

    def __init__(self, field, value):
        self.field = field
        self.value = value
        MoneyError.__init__(
            self,
            "REFUSED_DAY_GRAIN: %s='%s' names a moment; prorate counts "
            "whole days. A lease ending 'at noon on the 12th' has "
            "exactly two published readings (r/personalfinance cevz6l, "
            "r/legaladvice 66vwu9): the move-out day counted "
            "(inclusive=true) or not (inclusive=false). Nobody "
            "publishes 11.5 as a unit -- pass the calendar date and "
            "name the bound." % (field, value))


def _refuse_time_grain(value, field):
    """Prorate counts WHOLE days. A value that carries a time (epoch,
    HH:MM, ISO with T, RFC weekday header) is refused by name -- the
    silent date-truncation of a noon lease was itself the convention
    pick this bundle exists to kill."""
    s = str(value).strip()
    if (_EPOCH_RE.fullmatch(s) or ":" in s or _WEEKDAY_RE.match(s)
            or _MOMENT_RE.search(s)):
        raise GrainRefusal(field, s)


def grain_date_part(value):
    """Best-effort calendar-date extraction from a moment string, for
    the refusal's two readings. Returns None when no honest date part
    exists (epoch) -- the readings are then omitted, never guessed."""
    s = str(value).strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    if m:
        return m.group(1)
    if _EPOCH_RE.fullmatch(s) or _WEEKDAY_RE.match(s):
        return None
    try:
        return parse_date(s)["date"][:10]
    except DateError:
        return None


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
    the relance/impayés ledger work of the invoicing suite). Invoices: due ISO day, amount
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


def _money2(text, field):
    """Ledger discipline for reconciliation: plain decimals AT MOST 2
    places. A sub-cent invoice amount is a currency problem or a
    missing num/round upstream — it must be named, never silently
    quantized here, because every allocation below must stay exact."""
    d = _dec_plain(text, field)
    exp = d.as_tuple().exponent
    if isinstance(exp, int) and exp < -2:
        raise MoneyError("%s has sub-cent precision (%r) — the "
                         "reconciliation is cent-level: round upstream "
                         "(num/round) or fix the currency, not this tool"
                         % (field, text))
    return d


def _fmt2(x):
    # exact: all inputs are <= 2 places and this tool only adds and
    # subtracts, so a quantize here never rounds.
    return format(x.quantize(Decimal("0.01")), "f")


def money_apply_payments(invoices, payments):
    """FIFO reconciliation of payments onto invoices (ROADMAP-FINANCE
    1.2, the refusal message of aging already promised this tool).
    Money is applied IN THE GIVEN PAYMENT ORDER — the engine never
    reorders the agent's cash. Invoices are charged by due date,
    oldest first; equal dues keep input order (a tie is a rule, not
    a coin). Amounts: plain decimal strings, exact Decimal, no
    rounding anywhere (allocation is subtraction). A payment larger
    than all open dues leaves a named LEFTOVER, it is never smeared
    onto the newest invoice. Refusals, not guesses: zero-amount
    invoice, zero payment, duplicate ids, negative, slashed dates.
    Output keeps invoices in INPUT order: the ledger you sent is the
    ledger you get back."""
    if not isinstance(invoices, list) or not isinstance(payments, list):
        raise MoneyError("invoices and payments must both be lists")
    seen = set()
    rows = []
    for i, inv in enumerate(invoices):
        due = _iso_day(inv["due"], "invoices[%d].due" % i)
        amt = _money2(inv["amount"], "invoices[%d].amount" % i)
        paid = (_money2(inv["paid"], "invoices[%d].paid" % i)
                if inv.get("paid") is not None else Decimal(0))
        inv_id = inv.get("id") or str(i + 1)
        if inv_id in seen:
            raise MoneyError("duplicate invoice id %r — ids are the "
                             "join key of the reconciliation" % inv_id)
        seen.add(inv_id)
        if amt == 0:
            raise MoneyError("invoices[%d].amount is zero — a zero "
                             "invoice is a typo or a stub, neither "
                             "belongs in a reconciliation" % i)
        if amt < 0 or paid < 0:
            raise MoneyError("invoices[%d] carries a negative amount — "
                             "credits are a different ledger operation"
                             % i)
        if paid > amt:
            raise MoneyError(
                "invoices[%d] is overpaid by %s on its face — aging "
                "refuses this too; here the fix is upstream data, "
                "not an invented bucket" % (i, (paid - amt)))
        rows.append({"id": inv_id, "due": due, "amount": amt,
                     "paid": paid, "applied": Decimal(0),
                     "allocations": []})
    seen_p = set()
    prows = []
    order = sorted(range(len(rows)), key=lambda k: (rows[k]["due"], k))
    queue = [rows[k] for k in order]
    qi = 0
    for j, p in enumerate(payments):
        pdate = _iso_day(p["date"], "payments[%d].date" % j)
        pamt = _money2(p["amount"], "payments[%d].amount" % j)
        pid = p.get("id") or "p%d" % (j + 1)
        if pid in seen_p:
            raise MoneyError("duplicate payment id %r" % pid)
        seen_p.add(pid)
        if pamt == 0:
            raise MoneyError("payments[%d].amount is zero — a zero "
                             "payment is a typo or a test, cash never "
                             "reconciles to nothing" % j)
        if pamt < 0:
            raise MoneyError("payments[%d] is negative — refunds are "
                             "a credit note, not a payment" % j)
        left = pamt
        allocs = []
        while left > 0 and qi < len(queue):
            row = queue[qi]
            open_amount = row["amount"] - row["paid"] - row["applied"]
            take = left if left < open_amount else open_amount
            row["applied"] += take
            left -= take
            allocs.append({"invoice": row["id"],
                           "amount": _fmt2(take)})
            if row["paid"] + row["applied"] == row["amount"]:
                qi += 1
        prows.append({"id": pid, "date": pdate.isoformat(),
                      "amount": _fmt2(pamt), "leftover": _fmt2(left),
                      "allocations": allocs})
    pay_total = sum((Decimal(r["amount"]) for r in prows), Decimal(0))
    applied_total = sum((p["applied"] for p in rows), Decimal(0))
    out_rows, open_total = [], Decimal(0)
    for row in rows:
        outstanding = row["amount"] - row["paid"] - row["applied"]
        open_total += outstanding
        status = ("paid" if outstanding == 0 else
                  "partial" if row["paid"] + row["applied"] > 0
                  else "unpaid")
        out_rows.append({"id": row["id"], "due": row["due"].isoformat(),
                         "amount": _fmt2(row["amount"]),
                         "paid_before": _fmt2(row["paid"]),
                         "applied": _fmt2(row["applied"]),
                         "outstanding": _fmt2(outstanding),
                         "status": status})
    return {"invoices": out_rows, "payments": prows,
            "payment_total": _fmt2(pay_total),
            "applied_total": _fmt2(applied_total),
            "unapplied_total": _fmt2(pay_total - applied_total),
            "open_total": _fmt2(open_total),
            "count": len(out_rows)}


MAX_SUMMARY_MONTHS = 1200


def money_ledger_summary(entries, opening_balance="0"):
    """Monthly rollup of a journal with a running balance (ROADMAP-FINANCE
    1.3, the annual-bilan arithmetic of the invoicing app — by_month sums — sucked
    and upgraded: the old app added floats and rounded each month; here every
    figure is exact Decimal, the chain is addition only, so a closed
    month's balance is a FACT, never a rounding survivor).

    Entries: {date ISO day, amount signed plain decimal STRING} —
    positive is inflow, negative is outflow; the sign IS the direction,
    there is no debit/credit flag to disagree with it. opening_balance
    (default "0") is the carryforward in; the same chain walks out.

    The report is CALENDAR-CONTINUOUS: every month between the first
    and the last entry is emitted, months with no entry render a
    zero-activity row that still carries the balance — a hole in a
    balance chain is how audits get lost. Beyond MAX_SUMMARY_MONTHS
    the calendar itself is refused by name (chunk by year upstream).

    Refusals, never guesses: empty ledger (parallel to aging and
    apply-payments — an empty table of zeros is not a summary), zero
    amount (typo or stub), sub-cent (num/round upstream), grouped
    locale forms (num/parse upstream), slashed or impossible dates
    (_iso_day). The suite never reads a wall clock here: months come
    from the entries, and only from the entries.
    """
    if not isinstance(entries, list) or not entries:
        raise MoneyError("entries must be a non-empty list — a summary "
                         "of nothing is a table of zeros, refused like "
                         "in aging and apply-payments")
    open_bal = _money2(opening_balance, "opening_balance")
    rows = []
    for i, e in enumerate(entries):
        d = _iso_day(e["date"], "entries[%d].date" % i)
        a = _money2(e["amount"], "entries[%d].amount" % i)
        if a == 0:
            raise MoneyError("entries[%d].amount is zero — a zero entry "
                             "is a typo or a stub, neither belongs in a "
                             "summary (apply-payments refuses it too)" % i)
        rows.append((d, a))
    first = min(d for d, _ in rows)
    last = max(d for d, _ in rows)
    span = (last.year - first.year) * 12 + (last.month - first.month) + 1
    if span > MAX_SUMMARY_MONTHS:
        raise MoneyError("%d months between the first and the last "
                         "entry (> %d) — the calendar chain is refused, "
                         "not truncated; summarize by year and add the "
                         "opening of each year" % (span,
                                                   MAX_SUMMARY_MONTHS))
    per = {}
    for d, a in rows:
        k = per.setdefault((d.year, d.month),
                           [Decimal(0), Decimal(0), 0])
        if a > 0:
            k[0] += a
        else:
            k[1] += -a
        k[2] += 1
    months = []
    bal = open_bal
    cur = (first.year, first.month)
    end = (last.year, last.month)
    while cur <= end:
        inflow, outflow, count = per.get(cur, (Decimal(0), Decimal(0), 0))
        net = inflow - outflow
        bal = bal + net
        months.append({"month": "%04d-%02d" % cur, "count": count,
                       "inflow": _fmt2(inflow), "outflow": _fmt2(outflow),
                       "net": _fmt2(net), "closing_balance": _fmt2(bal)})
        cur = (cur[0] + 1, 1) if cur[1] == 12 else (cur[0], cur[1] + 1)
    total_in = sum((Decimal(m["inflow"]) for m in months), Decimal(0))
    total_out = sum((Decimal(m["outflow"]) for m in months), Decimal(0))
    return {"opening_balance": _fmt2(open_bal), "months": months,
            "months_emitted": len(months),
            "totals": {"count": len(rows), "inflow": _fmt2(total_in),
                       "outflow": _fmt2(total_out),
                       "net": _fmt2(total_in - total_out)},
            "closing_balance": _fmt2(bal)}


# ---------------------------------------------------------------------
# invoice/validate-totals (ROADMAP-FINANCE 1.4) — claim-vs-claim.
# ---------------------------------------------------------------------

_Q2 = Decimal("0.01")


def _round2(x):
    return x.quantize(_Q2, rounding=ROUND_HALF_UP)


def money_validate_totals(lines, declared, tax_mode="exclusive",
                          currency=None):
    """Validate DECLARED invoice numbers against the arithmetic the
    document itself asserts (ROADMAP-FINANCE 1.4). This tool does NOT
    compute an invoice — /api/v1/recipe/invoice does. The published
    identities (AGTNurat/LLM-invoice-extraction README, checked
    23-nov-2026): amount == qty x unit_price per line, sum of line
    bases == subtotal, subtotal - discount + tax == total, and the
    tax claim against per-line tax_rate.

    Rules, all published in this docstring (determinisme d'admission) :
      * Comparison is cent-level HALF-UP. A document built with
        banker's rounding can show a named 0.01 delta — the delta is
        the product, never silently corrected: "a corrected number
        destroys the evidence that the receipt didn't add up"
        (antonau.tech, nov-2026). The raw sub-cent product travels as
        expected_exact whenever it differs.
      * A line base is its declared amount when present, else
        qty x unit_price. Signs are NOT adjudicated: a credit line is
        a negative in one of the factors and the identity holds —
        refusing it would reject legitimate documents.
      * The total chain uses declared parts only: subtotal declared or
        recomputed from lines (subtotal_source names which), discount
        omitted means 0 (convention published here), tax omitted means
        0 ONLY when no line carries a tax_rate — otherwise the check
        is not_checked rather than a guess (declaring a total while
        hiding the tax is exactly the ambiguous document).
      * The tax claim is checked against TWO published methods:
        aggregate rounding round2(sum of exact bases x rate) and
        per-line rounding sum of round2 per line. A declared tax that
        matches either passes, method named; matching neither fails
        with the delta against the aggregate.
      * Blind spot, published as a fact (the same README's
        coordinated_price experiment: 49/49): an internally
        consistent wrong number is INVISIBLE to identity checks.
        This tool validates that the document adds up to itself.
    Money inputs: plain decimal strings, at most 2 places (sub-cent
    claims are a num/round problem, grouped forms a num/parse one).
    tax_rate: plain 0..100 (percent of the exclusive base).
    """
    if tax_mode not in ("exclusive", "inclusive"):
        raise MoneyError("tax_mode must be 'exclusive' or 'inclusive' "
                         "(got %r) — the closed table offers nothing "
                         "else" % (tax_mode,))
    if not lines:
        raise MoneyError("no lines — there is nothing to validate a "
                         "claim against (an empty document is a "
                         "refusal, not a table of zeros: same law as "
                         "aging and apply-payments)")
    declared = declared or {}
    if not any(k in declared for k in ("subtotal", "discount", "tax",
                                       "total")):
        raise MoneyError("no declared totals to validate — computing "
                         "is another contract: /api/v1/recipe/invoice "
                         "builds an invoice, this tool auditions a "
                         "claim")
    checked_fields = [k for k in ("subtotal", "discount", "tax",
                                  "total") if k in declared]
    if checked_fields == ["discount"]:
        raise MoneyError("a lone discount forms no identity — declare "
                         "at least subtotal, tax or total alongside")

    bases = []
    checks = []
    seen_ids = set()
    has_rate = False
    for i, line in enumerate(lines):
        lid = line.get("id")
        if lid is not None:
            if lid in seen_ids:
                raise MoneyError("duplicate line id %r — ids are the "
                                 "join key of the audit, they must be "
                                 "unique (same law as apply-payments)"
                                 % (lid,))
            seen_ids.add(lid)
        name = lid if lid is not None else "#%d" % (i + 1,)
        qty = _dec_plain(line.get("qty"), "lines[%s].qty" % name)
        price = _money2(line.get("unit_price"),
                        "lines[%s].unit_price" % name)
        exact = qty * price
        declared_amount = line.get("amount")
        if declared_amount is not None:
            a = _money2(declared_amount, "lines[%s].amount" % name)
            exp = _round2(exact)
            checks.append({
                "check": "line:%s" % name,
                "declared": _fmt2(a), "expected": _fmt2(exp),
                "delta": _fmt2(a - exp),
                "status": "pass" if a == exp else "fail",
                **({"expected_exact": format(exact, "f")}
                   if _round2(exact) != exact else {}),
            })
            base = a
        else:
            base = exact
        rate = line.get("tax_rate")
        rate_d = None
        if rate is not None:
            has_rate = True
            rate_d = _dec_plain(rate, "lines[%s].tax_rate" % name)
            if rate_d < 0 or rate_d > 100:
                raise MoneyError(
                    "lines[%s].tax_rate %r outside 0..100 — percent of "
                    "the base; a compound surcharge is its own line, "
                    "not a rate above 100" % (name, rate))
        bases.append((base, rate_d))

    subtotal_source = "declared"
    sum_bases_exact = sum((b for b, _ in bases), Decimal(0))
    if "subtotal" in declared:
        s = _money2(declared["subtotal"], "declared.subtotal")
        exp_s = _round2(sum_bases_exact)
        checks.append({
            "check": "subtotal", "declared": _fmt2(s),
            "expected": _fmt2(exp_s), "delta": _fmt2(s - exp_s),
            "status": "pass" if s == exp_s else "fail",
            **({"expected_exact": format(sum_bases_exact, "f")}
               if exp_s != sum_bases_exact else {}),
        })
        chain_subtotal = s
    else:
        subtotal_source = "recomputed_from_lines"
        chain_subtotal = _round2(sum_bases_exact)

    # tax claim (needs at least one rate and a declared tax)
    expected_tax_agg = expected_tax_perline = None
    if has_rate:
        if tax_mode == "exclusive":
            agg = sum((b * r / Decimal(100) for b, r in bases
                       if r is not None), Decimal(0))
            per = sum((_round2(b * r / Decimal(100)) for b, r in bases
                       if r is not None), Decimal(0))
        else:
            agg = sum((b * r / (Decimal(100) + r) for b, r in bases
                       if r is not None), Decimal(0))
            per = sum((_round2(b * r / (Decimal(100) + r))
                       for b, r in bases if r is not None), Decimal(0))
        expected_tax_agg = _round2(agg)
        expected_tax_perline = _round2(per)
    if "tax" in declared:
        t = _money2(declared["tax"], "declared.tax")
        if not has_rate:
            checks.append({
                "check": "tax", "declared": _fmt2(t), "status":
                    "not_checked",
                "reason": "tax is declared but no line carries a "
                          "tax_rate — the rate is the document's, "
                          "inventing one here would invent the answer",
            })
            chain_tax = t
        else:
            if t == expected_tax_agg:
                status, method, exp = "pass", "aggregate", expected_tax_agg
            elif t == expected_tax_perline:
                status, method, exp = "pass", "per_line", expected_tax_perline
            else:
                status, method, exp = ("fail", "aggregate",
                                       expected_tax_agg)
            checks.append({
                "check": "tax", "declared": _fmt2(t),
                "expected": _fmt2(exp), "delta": _fmt2(t - exp),
                "status": status, "method": method,
                "rounding_methods": {
                    "aggregate": _fmt2(expected_tax_agg),
                    "per_line": _fmt2(expected_tax_perline)},
            })
            chain_tax = t
    else:
        if has_rate:
            chain_tax = None
        else:
            chain_tax = Decimal(0)

    discount = Decimal(0)
    discount_defaulted = True
    if "discount" in declared:
        discount = _money2(declared["discount"], "declared.discount")
        discount_defaulted = False

    if "total" in declared:
        tot = _money2(declared["total"], "declared.total")
        if chain_tax is None:
            checks.append({
                "check": "total", "declared": _fmt2(tot),
                "status": "not_checked",
                "reason": "lines carry tax_rate but tax is not "
                          "declared — filling your total with a "
                          "guessed tax (aggregate or per-line) would "
                          "make the audit a coin flip",
            })
        else:
            exp_t = chain_subtotal - discount + chain_tax
            checks.append({
                "check": "total", "declared": _fmt2(tot),
                "expected": _fmt2(exp_t), "delta": _fmt2(tot - exp_t),
                "status": "pass" if tot == exp_t else "fail",
            })

    evaluated = [c for c in checks if c["status"] in ("pass", "fail")]
    failed = [c for c in checks if c["status"] == "fail"]
    out = {
        "verdict": "CONTRADICTED" if failed else "OK",
        "rounding": ("half-up at cent; per-line vs aggregate tax "
                     "rounding is checked as BOTH published methods "
                     "(method named on the tax claim)"),
        "subtotal_source": subtotal_source,
        "tax_mode": tax_mode,
        "checks": checks,
        "counts": {
            "lines": len(lines),
            "evaluated": len(evaluated),
            "failed": len(failed),
            "not_checked": len(checks) - len(evaluated),
        },
        "blind_spot": ("an internally consistent wrong number is "
                       "invisible to identity checks — this tool "
                       "proves the document adds up to itself, never "
                       "that it matches reality"),
    }
    if discount_defaulted and any(c["check"] == "total"
                                  for c in checks):
        out["discount_convention"] = ("discount omitted means 0 in the "
                                      "total chain (published rule)")
    if currency is not None:
        out["currency"] = currency
    return out
