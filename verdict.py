"""Bundle 22 — VERDICT. The output side of the coin: intake checked the
INPUT (does the request make sense?); VERDICT checks the OUTPUT of agents
that believe they agree, believe they obeyed, or believe what they cited.
Closed rules, pure functions, zero storage. Same payloads -> same verdict.

/check/agreement : N payloads claim to describe the same deal. Do they?
Recursive pointer walk over the union of keys, canonical equality:
  - numbers (or numeric strings) compared as Decimal — "1255.00" == 1255
  - strings exact (case-sensitive) — no fuzzy nonsense
  - lists element-wise; same members different order is its own kind
  - a key present on one side only is a divergence, never a shrug
"""
import re
from decimal import Decimal, InvalidOperation

MAX_PAYLOADS = 8
MAX_DEPTH = 12

_NUM_RE = re.compile(r"^-?[\d,]*\.?\d+$")


def _dec(v):
    """Decimal if the value is numeric (int/float/numeric string)."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return Decimal(str(v))
    if isinstance(v, str):
        t = v.strip().replace("$", "").replace("%", "")
        if _NUM_RE.match(t):
            try:
                return Decimal(t.replace(",", ""))
            except InvalidOperation:
                return None
    return None


def _collect(payload, pointer, out, depth):
    """Flatten to {pointer: value}, preserving containers at depth limit."""
    if depth > MAX_DEPTH:
        out[pointer] = payload
        return
    if isinstance(payload, dict):
        if not payload:
            out[pointer] = payload
        for k in sorted(payload):
            _collect(payload[k], "%s/%s" % (pointer, k), out, depth + 1)
    elif isinstance(payload, list):
        out[pointer] = payload
    else:
        out[pointer] = payload


def _equal(a, b):
    da, db = _dec(a), _dec(b)
    if da is not None and db is not None:
        return da == db
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_equal(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def check_agreement(payloads):
    """payloads: list of 2..8 JSON values. Returns the verdict dict."""
    if not isinstance(payloads, list) or len(payloads) < 2:
        raise ValueError("payloads must be a list of at least 2 objects")
    if len(payloads) > MAX_PAYLOADS:
        raise ValueError("at most %d payloads per call" % MAX_PAYLOADS)

    flats = []
    for p in payloads:
        d = {}
        _collect(p, "", d, 0)
        flats.append(d)
    pointers = sorted(set().union(*[set(f) for f in flats]))

    divergences = []
    for ptr in pointers:
        vals = [f.get(ptr, "«absent»") for f in flats]
        base = vals[0]
        kind = None
        for i, v in enumerate(vals):
            if i == 0:
                continue
            if ptr in flats[0] and v == "«absent»":
                kind = kind or "presence"
            elif "«absent»" in (base,) and v != "«absent»":
                kind = kind or "presence"
            elif not _equal(base, v):
                if isinstance(base, list) and isinstance(v, list) \
                        and sorted(map(repr, base)) == \
                        sorted(map(repr, v)):
                    kind = kind or "order"
                else:
                    da, db = _dec(base), _dec(v)
                    if da is not None and db is not None:
                        kind = kind or "numeric"
                    elif isinstance(base, list) != isinstance(v, list):
                        kind = kind or "type"
                    else:
                        kind = kind or "value"
        if kind:
            shown = [str(v)[:120] for v in vals]
            divergences.append({"pointer": ptr or "/", "kind": kind,
                                 "values": shown})
    return {"agree": not divergences, "payloads": len(payloads),
            "compared_pointers": len(pointers),
            "divergences": divergences,
            "first_divergence": (divergences[0]["pointer"]
                                 if divergences else None)}
