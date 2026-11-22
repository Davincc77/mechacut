"""money/rates — today's official reference rates, ECB daily feed.

The contract, stated honestly:
  * /api/v1/num/fx stays PURE: the caller brings the rate, so the same
    request replays to the same bytes forever. This endpoint is the
    OTHER half of the truth: where a fresh, citable rate comes from.
  * One upstream fetch per reference day (the feed stamps its own date;
    we refetch only when that day turns or after a failure cooldown),
    cached in memory. A redeploy refetches — nothing is persisted.
  * If the ECB is unreachable and a cache exists, the answer is served
    STALE and SAYS SO ("stale": true + its as_of date). If there is
    nothing cached, the answer is a named refusal. A rate is never
    invented, never interpolated, never rounded toward optimism.
  * Crosses (USD->BRL) are computed through EUR, the feed's base, in
    Decimal at 10 dp — the arithmetic of the source, disclosed.
"""
import decimal
import json
import re
import threading
import time
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path

import httpx

FEED = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
UA = "mechacut/1.0 (+https://mechacut.studio/SKILL-MINI.md)"
_COOLDOWN_S = 900

_lock = threading.Lock()
_cache = {"time": None, "rates": {}}        # ECB reference day, ISO
_last_try = 0.0


class RatesError(Exception):
    pass


def _parse(xml_bytes):
    root = ET.fromstring(xml_bytes)
    day = None
    rates = {}
    for cube in root.iter():
        tag = cube.tag.rsplit("}", 1)[-1]
        if tag != "Cube":
            continue
        if "time" in cube.attrib:
            day = cube.attrib["time"]
        elif "currency" in cube.attrib:
            rates[cube.attrib["currency"]] = cube.attrib["rate"]
    if not day or not rates:
        raise RatesError("ECB feed shape unrecognised — refusing to guess")
    return day, rates


def _fetch():
    global _last_try
    with _lock:
        now = time.monotonic()
        if _cache["time"] and now - _last_try < _COOLDOWN_S and \
                _cache["rates"]:
            return _cache["time"], dict(_cache["rates"]), False
        _last_try = now
        try:
            r = httpx.get(FEED, timeout=10.0, headers={"User-Agent": UA})
            r.raise_for_status()
            day, rates = _parse(r.content)
        except (httpx.HTTPError, ET.ParseError, RatesError) as e:
            if _cache["time"]:
                return _cache["time"], dict(_cache["rates"]), True
            raise RatesError(
                "ECB unreachable and nothing cached (%s) — a rate is "
                "never invented here" % type(e).__name__) from e
        _cache["time"], _cache["rates"] = day, rates
        return day, dict(rates), False


_ARCHIVE_PATH = Path(__file__).resolve().parent / "data" \
    / "ecb_history.json"
_archive = None


def _load_archive():
    global _archive
    if _archive is None:
        try:
            _archive = json.loads(
                _ARCHIVE_PATH.read_text(encoding="utf-8"))["days"]
        except (OSError, ValueError, KeyError):
            _archive = {}
    return _archive


def money_rates(currency_from="EUR", currency_to=None, amount=None,
                date=None):
    """date=None -> today's live feed. date=YYYY-MM-DD inside the
    archived window -> that day's true published rates (weekend and
    holiday dates simply are not reference days: named refusal, no
    silent snapping)."""
    if date:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(date)):
            raise RatesError("date must be YYYY-MM-DD")
        arc = _load_archive()
        if date not in arc:
            days = sorted(arc)
            raise RatesError(
                "%r is not an ECB reference day (not every calendar day "
                "publishes). Archived window: %s to %s, %d days"
                % (date, days[0] if days else "-",
                   days[-1] if days else "-", len(days)))
        day, rates, stale = date, dict(arc[date]), False
    else:
        day, rates, stale = _fetch()
    f = str(currency_from or "EUR").upper()
    out = {"as_of": day,
           "source": "ECB daily reference rates"
                     + ("" if not date else " (archived publication)"),
           "base": "EUR", "currencies": len(rates)}
    if stale:
        out["stale"] = True
    if f != "EUR" and f not in rates:
        raise RatesError("currency %r not in today's ECB feed" % f)
    if currency_to:
        t = str(currency_to).upper()
        if t not in rates:
            raise RatesError("currency %r not in today's ECB feed" % t)
        one_f = Decimal("1") if f == "EUR" else Decimal(rates[f])
        one_t = Decimal("1") if t == "EUR" else Decimal(rates[t])
        with decimal.localcontext() as ctx:
            ctx.prec = 30
            rate = (one_t / one_f).quantize(Decimal("1e-10"))
        out["from"], out["to"] = f, t
        out["rate"] = str(rate.normalize())
        out["crossed_through"] = "EUR" if f != "EUR" and t != "EUR" else f
        if amount is not None:
            try:
                a = Decimal(str(amount))
            except decimal.InvalidOperation:
                raise RatesError("amount must be a number")
            with decimal.localcontext() as ctx:
                ctx.prec = 30
                conv = (a * rate).quantize(Decimal("0.01"),
                                           rounding=decimal.ROUND_HALF_EVEN)
            out["amount"] = str(a)
            out["converted"] = str(conv)
            out["convention"] = "ROUND_HALF_EVEN at 2 dp (cash rounding)"
    else:
        out["rates"] = rates
    return out
