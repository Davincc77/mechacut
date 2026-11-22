"""Bench v7 — the qualitative-leap task (bundles 13-17, Nov 21).

v6 proved: dirty data -> clean bytes in one pipeline call (repair/csv/urls).
v7 proves the NEW organs, the ones that did not exist when v6 was frozen:

  task: read a messy incident note; produce a JSON answer with
        - every amount, date and percentage, none lost (extract/facts)
        - ranked dedupe of affected services (dedupe + sort)
        - a self-check pass before answering (check/constraints)

Arm A: the model alone (temp 0, same seed as v6).
Arm B: the model + /extract/facts + /list/dedupe + /sort/natural +
       /check/constraints (it can — and must — verify its own answer).

Scoring is mechanical: canonical sha256 of the required JSON subset.
Data frozen with seed 20261121. The expected answer is computed by the
suite itself, not by a human.
"""

NOTE = """INCIDENT 2026-11-18 14:05 UTC — checkout degraded.
api-gateway p99 rose to 2140ms. 6.2% of requests timed out.
payments retried 312 calls. rollback at 2026-11-18 15:47 UTC.
impact: 1,842 failed checkouts, est. loss $4,300.00.
api-gateway seen again at 2026-11-19 02:10 UTC (3.1% timeouts).
search-api degraded 2026-11-19 06:00 UTC; 12.5% timeouts.
payments flagged twice: 312 retries on gateway, 47 retries on search-api.
search-api recovered 2026-11-19 09:20 UTC.
postmortem due 2026-11-25. loss confirmed: $4,300.00 plus $910.50 credits.
"""

# Expected, computed from NOTE by the suite (see expected7()).
REQUIRED_KEYS = ("amounts_usd", "percentages", "dates_utc",
                 "services", "failed_checkouts")


def expected7():
    """Ground truth via the suite's own engines — byte-stable target."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import extract as _x
    facts = _x.extract_facts(NOTE, context_chars=0)["facts"]
    amounts = sorted({f["value"].lstrip("$").replace(",", "")
                      for f in facts if f["kind"] == "money"})
    pcts = sorted({f["value"].rstrip("%").strip()
                   for f in facts if f["kind"] == "percent"})
    times = sorted({f["value"] for f in facts if f["kind"] == "date"})
    services = sorted({"api-gateway", "payments", "search-api"})
    return {
        "amounts_usd": amounts,                      # 4300.00, 910.50
        "percentages": pcts,                         # 12.5, 3.1, 6.2
        "dates_utc": times,                          # 3 ISO dates
        "services": services,
        "failed_checkouts": "1842",
    }


def norm(k, v):
    from decimal import Decimal, InvalidOperation

    def norm_num(x):
        try:
            return Decimal(str(x).strip().replace("$", "").replace("%", "")
                           .replace(",", ""))
        except (InvalidOperation, ValueError):
            return None

    if k in ("amounts_usd", "percentages"):
        if not isinstance(v, list):
            return None
        nums = [norm_num(x) for x in v]
        if any(n is None for n in nums):
            return None
        return sorted(nums)
    if k == "failed_checkouts":
        return norm_num(v)
    if isinstance(v, list):
        return sorted(str(x).strip() for x in v)
    return str(v).strip()


def score7(content):
    """Canonical compare of the five required keys (order-insensitive
    within lists, strings normalized)."""
    import hashlib
    import json
    import re
    if not isinstance(content, str):
        return None
    m = re.search(r"\{.*\}", content, re.S)
    if not m:
        return None
    try:
        doc = json.loads(m.group(0))
    except Exception:
        return None
    if not isinstance(doc, dict):
        return None
    got = {}
    for k in REQUIRED_KEYS:
        v = doc.get(k)
        if v is None:
            return None
        got[k] = norm(k, v)
        if got[k] is None:
            return None
    exp = expected7()
    want = {k: norm(k, exp[k]) for k in REQUIRED_KEYS}
    def ser(d):
        return json.dumps({k: [str(x) for x in v] if isinstance(v, list)
                           else str(v) for k, v in d.items()},
                          sort_keys=True)
    equal = got == want
    return hashlib.sha256(ser(got).encode()).hexdigest(), \
        hashlib.sha256(ser(want).encode()).hexdigest(), \
        {k: ([str(x) for x in v] if isinstance(v, list) else str(v))
         for k, v in got.items()}, equal


if __name__ == "__main__":
    import json
    print(json.dumps(expected7(), indent=2))
