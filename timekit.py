"""Bundle 29 lot 1 — TEMPS. Interval arithmetic and cron semantics.

No wall clock anywhere: `at` is a caller argument (same contract as
/id/ulid), so two calls at the same input return the same bytes. Cron
follows Vixie-cron semantics as documented: five fields, dow 0 and 7
both Sunday, day-of-month AND day-of-week restricted combine with OR
(the classic footnote), descending ranges are invalid input, and
impossible dates (Feb 30) get a `never` verdict with the reason —
never a silently empty schedule.
"""
import re
from datetime import datetime, timedelta


class TimeError(Exception):
    pass


_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?$")


def _parse_dt(value, field):
    if not isinstance(value, str):
        raise TimeError("%s must be an ISO datetime string" % field)
    v = value.strip()
    if not _DT_RE.match(v):
        raise TimeError("%s %r: expected YYYY-MM-DDTHH:MM[:SS] "
                        "(no zone — pass UTC if you mean UTC)" % (field, v))
    try:
        return datetime.fromisoformat(v.replace(" ", "T"))
    except ValueError as e:
        raise TimeError("%s: %s" % (field, e))


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _norm_intervals(raw):
    if not isinstance(raw, list) or not raw:
        raise TimeError("intervals must be a non-empty list")
    if len(raw) > 5000:
        raise TimeError("intervals: 5000 max (this is a scheduler, not a "
                        "database)")
    out = []
    for i, it in enumerate(raw):
        if not isinstance(it, dict):
            raise TimeError("interval %d must be an object" % i)
        a = _parse_dt(it.get("start"), "interval %d start" % i)
        b = _parse_dt(it.get("end"), "interval %d end" % i)
        if b < a:
            raise TimeError("interval %d ends before it starts" % i)
        out.append((a, b, it.get("label")))
    return out


def schedule_overlap(intervals, mode="merge", window=None, point=None):
    iv = sorted(_norm_intervals(intervals))
    if mode == "merge":
        merged = []
        for a, b, _lbl in iv:
            if merged and a <= merged[-1][1]:
                if b > merged[-1][1]:
                    merged[-1][1] = b
            else:
                merged.append([a, b])
        return {"mode": "merge",
                "merged": [{"start": _iso(a), "end": _iso(b)}
                           for a, b in merged],
                "total_seconds": int(sum((b - a).total_seconds()
                                         for a, b in merged))}
    if mode == "conflicts":
        found = []
        for i in range(len(iv)):
            for j in range(i + 1, len(iv)):
                a = max(iv[i][0], iv[j][0])
                b = min(iv[i][1], iv[j][1])
                if b > a:
                    found.append({"a": iv[i][2], "b": iv[j][2],
                                  "overlap_start": _iso(a),
                                  "overlap_end": _iso(b),
                                  "seconds": int((b - a).total_seconds())})
        return {"mode": "conflicts", "count": len(found),
                "conflicts": found,
                "pairwise": True}
    if mode == "free":
        if not window:
            raise TimeError("mode=free needs window {start,end}")
        wa = _parse_dt(window.get("start"), "window start")
        wb = _parse_dt(window.get("end"), "window end")
        merged = schedule_overlap(intervals, mode="merge")["merged"]
        gaps = []
        cur = wa
        for m in merged:
            a = _parse_dt(m["start"], "m")
            b = _parse_dt(m["end"], "m")
            if a > cur:
                gaps.append({"start": _iso(cur), "end": _iso(min(a, wb))})
            cur = max(cur, b)
            if cur >= wb:
                break
        if cur < wb:
            gaps.append({"start": _iso(cur), "end": _iso(wb)})
        return {"mode": "free", "window": {"start": _iso(wa),
                                           "end": _iso(wb)},
                "free": gaps,
                "free_seconds": int(sum(
                    (_parse_dt(g["end"], "e") - _parse_dt(g["start"], "s"))
                    .total_seconds() for g in gaps))}
    if mode == "contains":
        if not point:
            raise TimeError("mode=contains needs point (ISO datetime)")
        p = _parse_dt(point, "point")
        hits = [{"label": lbl, "start": _iso(a), "end": _iso(b)}
                for a, b, lbl in iv if a <= p < b]
        return {"mode": "contains", "point": _iso(p), "count": len(hits),
                "inside": hits}
    raise TimeError("mode %r outside closed set (merge conflicts free "
                    "contains)" % mode)


# ------------------------------------------------------------- cron
_NAMES = {"month": {1: "jan", 2: "feb", 3: "mar", 4: "apr", 5: "may",
                    6: "jun", 7: "jul", 8: "aug", 9: "sep", 10: "oct",
                    11: "nov", 12: "dec"},
          "dow": {0: "sun", 1: "mon", 2: "tue", 3: "wed", 4: "thu",
                  5: "fri", 6: "sat"}}
_ALIAS = {v: k for f in _NAMES for k, v in _NAMES[f].items()}

_FIELD_SPEC = [  # (name, min, max)
    ("minute", 0, 59), ("hour", 0, 23), ("dom", 1, 31),
    ("month", 1, 12), ("dow", 0, 7)]


def _parse_field(token, name, lo, hi):
    values = set()
    if not token:
        raise TimeError("empty %s field" % name)
    for part in token.split(","):
        step = 1
        body = part
        if "/" in part:
            body, _, step_s = part.partition("/")
            if not re.match(r"^\d+$", step_s) or int(step_s) < 1:
                raise TimeError("%s: bad step %r" % (name, part))
            step = int(step_s)
        if body == "*":
            a, b = lo, hi
        elif "-" in body:
            x, _, y = body.partition("-")
            try:
                a = _one(x, name, lo, hi)
                b = _one(y, name, lo, hi)
            except TimeError:
                raise TimeError("%s: bad range %r" % (name, part))
            if a > b:
                raise TimeError("%s: descending range %r is invalid input "
                                "(no wrap in Vixie cron)" % (name, part))
        else:
            try:
                a = b = _one(body, name, lo, hi)
            except TimeError:
                raise TimeError("%s: bad value %r" % (name, part))
        v = a
        while v <= b:
            values.add(v)
            v += step
    return values


def _one(text, name, lo, hi):
    if name in ("month", "dow") and text.lower() in _ALIAS:
        v = _ALIAS[text.lower()]
        if name == "dow" and v == 7:
            v = 0
        return v
    if not re.match(r"^\d+$", text):
        raise TimeError("bad %s value %r" % (name, text))
    v = int(text)
    if name == "dow" and v == 7:
        v = 0
    if not lo <= v <= (6 if name == "dow" else hi):
        raise TimeError("%s value %d outside %d-%d" % (
            name, v, lo, 6 if name == "dow" else hi))
    return v


def cron_parse(expr):
    if not isinstance(expr, str):
        raise TimeError("cron must be a string")
    fields = expr.split()
    if len(fields) != 5:
        raise TimeError("expected 5 fields (minute hour dom month dow), "
                        "got %d" % len(fields))
    parsed = {}
    for token, (name, lo, hi) in zip(fields, _FIELD_SPEC):
        parsed[name] = _parse_field(token, name, lo, hi)
    dom_star = fields[2] == "*"
    dow_star = fields[4] == "*"
    return parsed, dom_star, dow_star


def _dom_ok(dt, dom):
    days = [dt.replace(day=1),
            (dt.replace(day=1) + timedelta(days=32)).replace(day=1)]
    first = days[0]
    if dt.day > (days[1] - timedelta(days=1)).day:
        return False
    return dt.day in dom


_30_DAY = {4, 6, 9, 11}


def _never_reason(parsed, dom_star, dow_star):
    """Calendar-impossible combinations, checked before any scan:
    the max possible day of the selected months only. Feb is 29 at best
    (leap), 30-day months cap at 30. dow can never make a date
    impossible — it ORs with dom when both are restricted (Vixie)."""
    month = parsed["month"]
    dom = parsed["dom"]
    if dom_star or not dom:
        return None
    hi = {}
    for m in range(1, 13):
        hi[m] = 29 if m == 2 else (30 if m in _30_DAY else 31)
    cap = max(hi[m] for m in month)
    if min(dom) > cap:
        return ("day(s) %s can never occur in month(s) %s (max possible "
                "day is %d)" % (sorted(dom), sorted(month), cap))
    if not dow_star and dom and min(dom) > 31:
        return "day-of-month beyond 31"
    return None


def cron_next(expr, at, count=5):
    if not isinstance(count, int) or not 1 <= count <= 100:
        raise TimeError("count must be 1-100")
    parsed, dom_star, dow_star = cron_parse(expr)
    t0 = _parse_dt(at, "at")
    reason = _never_reason(parsed, dom_star, dow_star)
    if reason:
        return {"expr": expr, "never": True, "reason": reason}
    runs = []
    # walk minute-by-minute only over candidate days: cheap and exact
    minute = parsed["minute"]
    hour = parsed["hour"]
    month = parsed["month"]
    dom = parsed["dom"]
    dow = parsed["dow"]
    cur = t0.replace(second=0, microsecond=0) + timedelta(minutes=1)
    day_limit = t0 + timedelta(days=1500)
    while len(runs) < count:
        if cur > day_limit:
            return {"expr": expr, "runs": [_iso(x) for x in runs],
                    "exhausted": "no further run within 1500 days "
                                 "(leap-year-safe horizon)"}
        day_match = cur.month in month and (
            dom_star or _dom_ok(cur, dom)) and (
            dow_star or ((cur.weekday() + 1) % 7) in dow)
        if not dom_star and not dow_star:
            # Vixie: both restricted => OR, not AND (documented footnote)
            day_match = cur.month in month and (
                _dom_ok(cur, dom) or ((cur.weekday() + 1) % 7) in dow)
        if not day_match:
            cur = (cur + timedelta(days=1)).replace(hour=0, minute=0)
            continue
        if cur.hour in hour and cur.minute in minute:
            runs.append(cur)
        cur += timedelta(minutes=1)
    return {"expr": expr, "runs": [_iso(x) for x in runs], "never": False}
