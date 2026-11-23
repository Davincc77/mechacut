"""Deterministic dates, timezones, cron and ICS (Bundle 3, TOOLS-50 #17-23).

Pure stdlib (datetime, zoneinfo, calendar, email.utils). No LLM, no
storage, no filesystem, no current-time reads by the transforms themselves:
every function takes its reference instants explicitly. Output timestamps
are ISO 8601 with explicit offsets; cron semantics are WALL CLOCK in the
requested zone (what crontab means), never absolute instants.
"""

import calendar
import re
from datetime import date, datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo


class DateError(Exception):
    pass


_MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}
_MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_name) if m})
_DOWS = {d.lower(): i for i, d in enumerate(
    ["mon", "tue", "wed", "thu", "fri", "sat", "sun", "monday", "tuesday",
     "wednesday", "thursday", "friday", "saturday", "sunday"], start=0)}
_DOW_CANON = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_WEEKEND_DEFAULT = [5, 6]  # Sat, Sun (Mon=0)


def _zone(name):
    if name in ("UTC", "utc", "Z", ""):
        return timezone.utc
    try:
        return ZoneInfo(name)
    except Exception:
        raise DateError("unknown timezone: %r (use an IANA name, e.g. "
                        "Europe/Paris, or UTC)" % name)


def _attach(dt, zname):
    """Interpret a naive datetime in a zone (wall clock). Non-existent
    wall times are resolved by zoneinfo's fold rules (documented)."""
    if dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=_zone(zname))


# ------------------------------------------------------------- date/parse

_ISO_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})"
    r"(?:[ T](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?"
    r"(Z|[+-]\d{2}:?\d{2})?)?$")
_EPOCH_RE = re.compile(r"^-?\d{9,11}(?:\.\d+)?$")
_DMY_RE = re.compile(r"^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})$")
_MDY_RE = re.compile(r"^(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})$")
_DMY_NAME_RE = re.compile(r"^(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})$")
_MONTH_FIRST_RE = re.compile(r"^([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(\d{4})$")


def parse_date(text, prefer=None, tz=None):
    """Parse one human/ISO instant. Never guesses day/month order —
    and since bundle 93 that word has teeth: when a slashed date has
    TWO live readings (03/04/05), parse_date REFUSES with both
    candidates named unless `prefer` is passed. When the bytes decide
    (13 can never be a month; 05/05/05 collapses to one day), the
    answer is given, single-reading. ISO and month-names are never
    touched by the refusal."""
    ambiguity = "NONE"
    if not isinstance(text, str) or not text.strip():
        raise DateError("date must be a non-empty string")
    s = text.strip()
    naive = None
    dt = None
    if _EPOCH_RE.match(s):
        dt = datetime.fromtimestamp(float(s), tz=timezone.utc)
        source = "epoch"
    elif re.match(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,\s", s, re.I):
        try:
            dt = parsedate_to_datetime(s)
        except Exception:
            raise DateError("unparsable RFC 2822 date: %r" % s)
        source = "rfc2822"
    elif "T" in s or re.match(r"^\d{4}-\d{2}-\d{2}", s):
        m = _ISO_RE.match(s)
        if not m:
            raise DateError("unparsable ISO-ish date: %r" % s)
        y, mo, d, h, mi, se, fr, off = m.groups()
        try:
            naive = datetime(int(y), int(mo), int(d),
                             int(h or 0), int(mi or 0), int(se or 0),
                             int((fr or "").ljust(6, "0") or 0))
        except ValueError as e:
            raise DateError("invalid ISO date: %s" % e)
        if off:
            if off in ("Z", "z"):
                dt = naive.replace(tzinfo=timezone.utc)
            else:
                o = off.replace(":", "")
                sign = 1 if o[0] == "+" else -1
                dt = naive.replace(tzinfo=timezone(timedelta(
                    hours=sign * int(o[1:3]), minutes=sign * int(o[3:5]))))
        source = "iso"
    else:
        m = _DMY_RE.match(s)
        if m:
            a, b, c = (int(m.group(1)), int(m.group(2)), m.group(3))
            year = int(c) + 2000 if len(c) == 2 else int(c)
            if prefer is not None and prefer not in ("dmy", "mdy"):
                raise DateError('prefer must be "dmy" or "mdy"')
            ambiguity = "NONE"
            if a > 12:
                d_, mo_ = a, b
            elif b > 12:
                d_, mo_ = b, a
            elif a == b:
                d_, mo_ = a, b  # both readings coincide: one fact
            elif prefer is None:
                # the audit of 24-11, applied: refusing here is the
                # whole difference between a parser and a coin
                y_ = int(c) + 2000 if len(c) == 2 else int(c)
                raise DateError(
                    "slash_ambiguous: %r reads as %04d-%02d-%02d (dmy) "
                    "OR %04d-%02d-%02d (mdy) — both are valid calendar "
                    "days; pass prefer=\"dmy\" or prefer=\"mdy\", we "
                    "refuse to pick" % (s, y_, b, a, y_, a, b))
            else:
                d_, mo_ = (a, b) if prefer == "dmy" else (b, a)
                ambiguity = "RESOLVED-BY-PREFER"
            if a == b or a > 12 or b > 12:
                ambiguity = "SINGLE-READING"
            try:
                naive = datetime(year, mo_, d_)
            except ValueError:
                raise DateError("invalid calendar date: %r" % s)
            source = "numeric"
        else:
            m = _MDY_RE.match(s) or _MONTH_FIRST_RE.match(s)
            if m:
                g1, g2, g3 = m.groups()
                if g1.isdigit():
                    d_, mon, year = int(g1), g2.lower(), int(g3)
                elif g2.isdigit():
                    mon, d_, year = g1.lower(), int(g2), int(g3)
                else:
                    raise DateError("unparsable date: %r" % s)
                mo_ = _MONTHS.get(mon)
                if not mo_:
                    raise DateError("unknown month name: %r" % g2 if not g1.isdigit() else "unknown month name: %r" % g1)
                try:
                    naive = datetime(year, mo_, d_)
                except ValueError:
                    raise DateError("invalid calendar date: %r" % s)
                source = "month_name"
            else:
                raise DateError("unparsable date: %r" % s)
    if dt is None:
        dt = _attach(naive, tz) if tz else naive
    out = {
        "iso": dt.isoformat(),
        "date": dt.date().isoformat(),
        "weekday": _DOW_CANON[dt.weekday()],
        "iso_week": list(dt.isocalendar()[:3]),
        "naive": dt.tzinfo is None,
        "source": source,
        "ambiguity": ambiguity,
    }
    if dt.tzinfo is not None:
        utc = dt.astimezone(timezone.utc)
        out["utc"] = utc.isoformat()
        out["epoch"] = int(utc.timestamp())
    else:
        out["utc"] = None
        out["epoch"] = None
    return out


def _parse_instant(value, tz=None):
    r = parse_date(value, tz=tz)
    return datetime.fromisoformat(r["iso"])


# ---------------------------------------------------------------- date/tz

def tz_convert(value, source="UTC", targets=("UTC",), date_at=None):
    """Convert an instant to one or more IANA zones. A naive date is read in
    `source`; a bare date (no time) gets date_at (HH:MM, default 00:00)."""
    if isinstance(targets, str):
        targets = [targets]
    base = value.strip()
    r = parse_date(base)
    dt = datetime.fromisoformat(r["iso"])
    if re.match(r"^\d{4}-\d{2}-\d{2}$", base):
        hh, mm = (date_at or "00:00").split(":")
        dt = dt.replace(hour=int(hh), minute=int(mm))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_zone(source))
    src = dt.astimezone()
    out = []
    for t in targets:
        z = _zone(t)
        conv = dt.astimezone(z)
        dst = conv.dst() or timedelta(0)
        out.append({
            "tz": t,
            "iso": conv.isoformat(),
            "weekday": _DOW_CANON[conv.weekday()],
            # P7 (sonde 22-11) : fraction de JOUR, pas heures —
            # l'agent lit offset_hhmm pour la forme humaine ;
            # le nombre brut reste pinné tel quel (doctrine).
            "utc_offset": conv.utcoffset().total_seconds() / 86400,
            "offset_hhmm": _fmt_off(conv.utcoffset()),
            "dst": dst != timedelta(0),
        })
    return {"input": dt.isoformat(), "source": source, "zones": out}


def _fmt_off(td):
    if td is None:
        return "+00:00"
    s = int(td.total_seconds())
    sign = "+" if s >= 0 else "-"
    s = abs(s)
    return "%s%02d:%02d" % (sign, s // 3600, (s % 3600) // 60)


# --------------------------------------------------------------- date/calc

_ADD_RE = re.compile(r"^(?:(\d+)y)?(?:(\d+)m)?(?:(\d+)w)?(?:(\d+)d)?"
                     r"(?:T(?:(\d+)h)?(?:(\d+)M)?(?:(\d+)s)?)?$")


def _add_calendar(dt, years=0, months=0, weeks=0, days=0,
                  hours=0, minutes=0, seconds=0):
    y, mo = dt.year + years, dt.month + months
    # normalize month overflow
    y += (mo - 1) // 12
    mo = (mo - 1) % 12 + 1
    d = min(dt.day, calendar.monthrange(y, mo)[1])  # clamp month ends
    naive_wall = dt.replace(year=y, month=mo, day=d)
    delta = timedelta(weeks=weeks, days=days, hours=hours,
                      minutes=minutes, seconds=seconds)
    if naive_wall.tzinfo is None or naive_wall.tzinfo == timezone.utc:
        return naive_wall + delta
    # wall-clock add for zoned datetimes: shift naive, re-attach, re-normalize
    wall = naive_wall.replace(tzinfo=None) + delta
    zi = naive_wall.tzinfo
    return wall.replace(tzinfo=zi)


def _duration_iso(td):
    total = int(td.total_seconds())
    sign = "-" if total < 0 else ""
    total = abs(total)
    d, rem = divmod(total, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    out = sign + "P"
    if d:
        out += "%dD" % d
    if h or m or s:
        out += "T" + ("%dH" % h if h else "") + ("%dM" % m if m else "") \
             + ("%dS" % s if s else "")
    return out if out.rstrip("PT-") != "" else "PT0S"


def _human_diff(td):
    total = int(td.total_seconds())
    sign = "-" if total < 0 else ""
    total = abs(total)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    for v, name in ((days, "day"), (hours, "hour"), (minutes, "minute"),
                    (seconds, "second")):
        if v:
            parts.append("%d %s%s" % (v, name, "s" if v != 1 else ""))
    return (sign + " ".join(parts)) if parts else "0 seconds"


def _business_shift(dt, n, holidays, weekend):
    hol = set()
    for h in holidays:
        hol.add(_parse_instant(h).date())
    step = 1 if n >= 0 else -1
    left = abs(n)
    cur = dt
    while left:
        cur = cur + timedelta(days=step)
        if cur.weekday() not in weekend and cur.date() not in hol:
            left -= 1
    return cur


def date_calc(base, op, params=None, tz=None):
    """One base date, one operation, deterministic result.
    ops: add | business_days | diff | boundary | age
    """
    params = params or {}
    dt = _parse_instant(base, tz=tz)
    if op == "add":
        m = _ADD_RE.match(params.get("duration", ""))
        if not m or not params.get("duration"):
            raise DateError('add needs params.duration ISO-8601-ish '
                            '(e.g. "1y2m3d", "P3D" accepted without P)')
        y, mo, w, d, h, mi, s = (int(g) if g else 0 for g in m.groups())
        out = _add_calendar(dt, y, mo, w, d, h, mi, s)
        return {"result": out.isoformat(),
                "weekday": _DOW_CANON[out.weekday()]}
    if op == "business_days":
        n = params.get("n")
        if not isinstance(n, int) or isinstance(n, bool):
            raise DateError("business_days needs integer params.n")
        weekend = params.get("weekend", _WEEKEND_DEFAULT)
        if not isinstance(weekend, list) or not all(
                isinstance(x, int) and 0 <= x <= 6 for x in weekend):
            raise DateError("params.weekend must be a list of ints 0 (Mon) "
                            "to 6 (Sun)")
        out = _business_shift(dt, n, params.get("holidays", []), weekend)
        return {"result": out.isoformat(),
                "weekday": _DOW_CANON[out.weekday()]}
    if op == "diff":
        unit = params.get("unit", "human")
        other = _parse_instant(params.get("until"), tz=tz)
        if (dt.tzinfo is None) != (other.tzinfo is None):
            raise DateError("diff needs both instants aware or both naive")
        td = other - dt
        if unit == "days":
            return {"days": td.days, "seconds_iso": _duration_iso(td)}
        if unit == "business_days":
            weekend = params.get("weekend", _WEEKEND_DEFAULT)
            hol = {str(_parse_instant(h).date())
                   for h in params.get("holidays", [])}
            sign = 1 if td.days >= 0 else -1
            step = timedelta(days=sign)
            cur = dt.date()
            end = other.date()
            count = 0
            include_base = params.get("include_base", False)
            if include_base:
                if sign < 0:
                    raise DateError("include_base needs until >= base "
                                    "(the counting window starts AT base; "
                                    "backward windows refuse, they are "
                                    "not mirrored by guesswork)")
                if cur == end:
                    if (cur.weekday() not in weekend
                            and str(cur) not in hol):
                        return {"business_days": 1}
                    return {"business_days": 0}
                if (cur.weekday() not in weekend
                        and str(cur) not in hol):
                    count = 1
            while cur != end:
                cur = cur + step
                if cur.weekday() not in weekend and str(cur) not in hol:
                    count += 1
            return {"business_days": sign * count}
        if unit == "human":
            return {"human": _human_diff(td), "total_seconds":
                    int(td.total_seconds())}
        if unit == "calendar":
            # calendar-aware: whole months + residual days (+ time if zoned)
            sign = 1 if other >= dt else -1
            a, b = (dt, other) if sign == 1 else (other, dt)
            months = (b.year - a.year) * 12 + (b.month - a.month)
            if b.day < a.day or (b.day == a.day and b.time() < a.time()):
                months -= 1
            y, mo = divmod(a.month - 1 + months, 12)
            anchor = a.replace(year=a.year + y, month=mo + 1,
                               day=min(a.day, calendar.monthrange(
                                   a.year + y, mo + 1)[1]))
            rem = (b - anchor).days
            return {"months": sign * months, "days": sign * rem}
        raise DateError('diff unit must be one of days|business_days|'
                        'human|calendar')
    if op == "boundary":
        unit = params.get("unit", "month")
        edge = params.get("edge", "start")
        if unit == "day":
            start, end = dt.replace(hour=0, minute=0, second=0), None
            end = dt.replace(hour=23, minute=59, second=59)
        elif unit == "week":
            monday = dt - timedelta(days=dt.weekday())
            start = monday.replace(hour=0, minute=0, second=0)
            end = (monday + timedelta(days=6)).replace(
                hour=23, minute=59, second=59)
        elif unit == "month":
            start = dt.replace(day=1, hour=0, minute=0, second=0)
            last = calendar.monthrange(dt.year, dt.month)[1]
            end = dt.replace(day=last, hour=23, minute=59, second=59)
        elif unit == "quarter":
            qm = (dt.month - 1) // 3 * 3 + 1
            start = dt.replace(month=qm, day=1, hour=0, minute=0, second=0)
            end = dt.replace(month=qm + 2,
                             day=calendar.monthrange(dt.year, qm + 2)[1],
                             hour=23, minute=59, second=59)
        elif unit == "year":
            start = dt.replace(month=1, day=1, hour=0, minute=0, second=0)
            end = dt.replace(month=12, day=31, hour=23, minute=59, second=59)
        else:
            raise DateError("boundary unit must be day|week|month|quarter|year")
        if edge not in ("start", "end"):
            raise DateError("boundary edge must be start or end")
        out = start if edge == "start" else end
        return {"result": out.isoformat(),
                "weekday": _DOW_CANON[out.weekday()]}
    if op == "age":
        other = _parse_instant(params.get("on"), tz=tz) if params.get("on") \
            else datetime.now(timezone.utc)
        if other < dt:
            raise DateError("age.on must not be before base")
        years = other.year - dt.year
        mdiff = (other.month - dt.month) * 100 + (other.day - dt.day)
        if other.time() < dt.time():
            mdiff -= 100
        if mdiff < 0:
            years -= 1
            mdiff += 1200
        return {"years": years, "months_extra": mdiff // 100,
                "days_extra": mdiff % 100,
                "total_days": (other.date() - dt.date()).days}
    raise DateError("unknown op: %r (add|business_days|diff|boundary|age)"
                    % op)


# ------------------------------------------------------------------- cron

_CRON_MACRO = {
    "@yearly": "0 0 1 1 *", "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *", "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *", "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *", "@minutely": "* * * * *",
}
_FIELD_RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]
_DOW_NAMES = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5,
              "sat": 6}
_MON_NAMES = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}


def _parse_field(item, lo, hi, names):
    vals = set()
    for part in item.split(","):
        step = 1
        base = part
        if "/" in part:
            base, s = part.split("/", 1)
            if not s.isdigit() or int(s) == 0:
                raise DateError("invalid step: %r" % part)
            step = int(s)
        if base == "*":
            a, b = lo, hi
        elif "-" in base[1:] or (base.startswith("-")):
            lo_s, hi_s = base.split("-", 1)
            def num(x):
                x = x.lower()
                return names[x] if x in names else int(x)
            try:
                a, b = num(lo_s), num(hi_s)
            except (ValueError, KeyError):
                raise DateError("invalid range: %r" % part)
            if a > b:
                raise DateError("inverted range: %r" % part)
        else:
            x = base.lower()
            try:
                v = names[x] if x in names else int(x)
            except (ValueError, KeyError):
                raise DateError("invalid value: %r" % base)
            a = b = v
        vals.update(range(a, b + 1, step))
    for v in vals:
        if not lo <= v <= hi:
            raise DateError("value out of range %d-%d: %d" % (lo, hi, v))
    return vals


def parse_cron(expression):
    if not isinstance(expression, str):
        raise DateError("expression must be a string")
    expr = expression.strip().lower()
    expr = _CRON_MACRO.get(expr, expr)
    fields = expr.split()
    if len(fields) != 5:
        raise DateError("cron must have 5 fields "
                        "(minute hour dom month dow): %r" % expression)
    sets = []
    for i, f in enumerate(fields):
        lo, hi = _FIELD_RANGES[i]
        names = _DOW_NAMES if i == 4 else (_MON_NAMES if i == 3 else {})
        sets.append(_parse_field(f, lo, hi, names))
    # 7 means Sunday in crontab
    if 7 in sets[4]:
        sets[4].discard(7)
        sets[4].add(0)
    return {"minute": sets[0], "hour": sets[1], "dom": sets[2],
            "month": sets[3], "dow": sets[4],
            "dom_restricted": fields[2] != "*",
            "dow_restricted": fields[4] != "*"}


def cron_next(expression, count=1, after=None, tz="UTC"):
    """Next `count` fire times. Wall-clock semantics in `tz` (crontab
    behavior). Vixie rule: if both dom and dow are restricted, a day
    matches if EITHER matches. `after`: ISO instant (default: current
    wall time in tz, second-precision) — pin it for byte-stable calls."""
    if not (1 <= count <= 1000):
        raise DateError("count must be 1-1000")
    f = parse_cron(expression)
    z = _zone(tz)
    # P-cron (sonde de contrat 22-11) : un runs: [] muet n'est pas une
    # réponse. Si le jour du mois est structurelement impossible pour
    # TOUS les mois de l'expression (31 fevrier), le verdict est nomme
    # dans le corps — meme runs, mais jamais silence. La projection du
    # gold (expression, tz, after, count, runs) ne change pas : les
    # cles sont des FRERES, pas des remplacements.
    never = None
    if f["dom_restricted"] and not f["dow_restricted"]:
        import calendar

        def _cap(m):
            return 29 if m == 2 else calendar.monthrange(2024, m)[1]
        bad = sorted(d for d in f["dom"]
                     if all(d > _cap(m) for m in f["month"]))
        if bad and len(bad) == len(f["dom"]):
            never = ("NEVER_FIRES: day-of-month %s cannot occur in "
                     "month(s) %s — February ends at 29. Widen the "
                     "month set; this expression is a silence, not a "
                     "schedule"
                     % (",".join(str(x) for x in bad),
                        ",".join(str(x) for x in sorted(f["month"]))))
    if after is None:
        base = datetime.now(z)
    else:
        r = parse_date(after)
        base = datetime.fromisoformat(r["iso"])
        base = base.astimezone(z) if base.tzinfo else base.replace(tzinfo=z)
    cur = base.replace(second=0, microsecond=0) + timedelta(minutes=1)
    results = []
    skipped = []
    horizon = cur + timedelta(days=366 * 5)
    dom_or_dow = f["dom_restricted"] and f["dow_restricted"]
    while len(results) < count and cur < horizon:
        if cur.month not in f["month"]:
            y, mo = cur.year + (cur.month == 12), cur.month % 12 + 1
            cur = datetime(y, mo, 1, tzinfo=z)
            continue
        dom_ok = cur.day in f["dom"]
        dow_ok = ((cur.weekday() + 1) % 7) in f["dow"]
        day_ok = (dom_ok or dow_ok) if dom_or_dow else (dom_ok and dow_ok)
        if not day_ok:
            cur = datetime.combine(cur.date() + timedelta(days=1),
                                   time(0, 0), tzinfo=z)
            continue
        if cur.hour not in f["hour"]:
            nxt = [h for h in f["hour"] if h > cur.hour]
            if nxt:
                cur = cur.replace(hour=min(nxt), minute=0)
            else:
                cur = datetime.combine(cur.date() + timedelta(days=1),
                                       time(0, 0), tzinfo=z)
            continue
        nxtm = [m for m in f["minute"] if m >= cur.minute]
        if not nxtm:
            cur = cur + timedelta(hours=1)
            cur = cur.replace(minute=0)
            continue
        cur = cur.replace(minute=min(nxtm))
        # Mur inexistant : l'engine de la maison (le MEME que
        # date/tz_ambiguity, import tardif — tzambkit importe dates)
        # est INTERROGE, jamais duplique. Un wall clock dans le trou
        # DST n'est pas mappe « comme s'il existait » : il est saute,
        # nomme, avec le premier instant valide apres le saut.
        if z is not timezone.utc:
            from tzambkit import TzAmbError, classify
            try:
                cl = classify(tz, cur.strftime("%Y-%m-%dT%H:%M:%S"))
            except TzAmbError:
                cl = {"kind": "gap",
                      "verdict": "%s refused: round-trip mismatch"
                                 % cur.strftime("%Y-%m-%d %H:%M:%S")}
            if cl["kind"] == "gap":
                near = (cl.get("nearest") or [{}, {}])[1]
                skipped.append({
                    "wall": cur.strftime("%Y-%m-%dT%H:%M"),
                    "zone": tz,
                    "verdict": cl["verdict"],
                    "first_valid_after_jump": near.get("local")})
                cur = cur + timedelta(minutes=1)
                continue
        results.append({
            "iso": cur.isoformat(),
            "epoch": int(cur.timestamp()),
            "weekday": _DOW_CANON[cur.weekday()],
        })
        cur = cur + timedelta(minutes=1)
    out = {"expression": expression, "tz": tz, "runs": results}
    if never is not None:
        out["never_fires"] = never
    if skipped:
        out["skipped"] = skipped
    return out


_CRON_LABELS = ("minute", "hour", "day of month", "month", "day of week")


def cron_humanize(expression):
    f = parse_cron(expression)
    parts = []

    def phrase(vals, lo, hi, names=None, label=""):
        if vals == set(range(lo, hi + 1)):
            return "every " + label
        inv = {}
        if names:
            inv = {v: k for k, v in names.items() if len(k) == 3}
        items = sorted(vals)
        s = ", ".join((inv.get(v, str(v))).upper() if names else str(v)
                      for v in items)
        return "%s at %s" % (label, s)

    minute = f["minute"]
    hour = f["hour"]
    if minute == set(range(0, 60)):
        mpart = "every minute"
    elif len(minute) <= 12:
        mpart = "at minute " + ",".join(str(v) for v in sorted(minute))
    else:
        mpart = "every minute (set of %d)" % len(minute)
    if hour == set(range(0, 24)):
        hpart = "every hour"
    else:
        hpart = "at hour " + ",".join("%02d" % v for v in sorted(hour))
    dpart = ("every day" if f["dom"] == set(range(1, 32))
             else "on day of month " + ",".join(str(v) for v in sorted(f["dom"])))
    mon_names = {v: k.upper() for v, k in
                 ((i, m) for i, m in enumerate(calendar.month_abbr) if m)}
    if f["month"] == set(range(1, 13)):
        mopart = "every month"
    else:
        mopart = "in " + ",".join(mon_names[v] for v in sorted(f["month"]))
    dow_names = {0: "SUN", 1: "MON", 2: "TUE", 3: "WED", 4: "THU",
                 5: "FRI", 6: "SAT"}
    if f["dow"] == set(range(0, 7)):
        dpart2 = "any day of week"
    else:
        dpart2 = ("on " if f["dom"] != set(range(1, 32)) and False
                  else "on day of week ") + \
                 ",".join(dow_names[v] for v in sorted(f["dow"]))
    if minute == {0}:
        mpart = "minute 0"
    clauses = [mpart, hpart, dpart, mopart, dpart2]
    human = "; ".join(clauses)
    return {"expression": expression, "human": "Runs %s" % human,
            "fields": {label: sorted(vals) for label, vals in zip(
                _CRON_LABELS, (minute, hour, f["dom"], f["month"], f["dow"]))}}



# -------------------------------------------------------------------- ics

_DUR_RE = re.compile(r"^P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?"
                     r"(?:(\d+)S)?)?$")


def _fold(line):
    """RFC 5545 line folding at 75 octets (UTF-8 aware)."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return [line]
    out = []
    cur = ""
    curb = 0
    budget = 75
    for ch in line:
        cb = len(ch.encode("utf-8"))
        if curb + cb > budget:
            out.append(cur)
            cur, curb = "", 0
            budget = 74  # continuation lines carry a leading space
        cur += ch
        curb += cb
    out.append(cur)
    return [out[0]] + [" " + c for c in out[1:]]


def _esc(text):
    return (str(text).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def ics_generate(events, prodid="-//mechacut.studio//ICS//EN",
                 calname="mechacut"):
    import hashlib
    if not isinstance(events, list) or not events:
        raise DateError("events must be a non-empty array")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:" + _esc(prodid), "CALSCALE:GREGORIAN",
             "X-WR-CALNAME:" + _esc(calname)]
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            raise DateError("event %d: must be an object" % i)
        start = ev.get("start")
        if not start:
            raise DateError("event %d: start is required" % i)
        dt = _parse_instant(start, tz=ev.get("tz", "UTC"))
        allday = bool(re.match(r"^\d{4}-\d{2}-\d{2}$", str(start).strip()))
        end = ev.get("end")
        dur = ev.get("duration")
        if end:
            dtend = _parse_instant(end, tz=ev.get("tz", "UTC"))
        elif dur:
            m = _DUR_RE.match(str(dur).upper())
            if not m:
                raise DateError("event %d: bad duration %r" % (i, dur))
            w, d, h, mi, s = (int(g) if g else 0 for g in m.groups())
            dtend = dt + timedelta(weeks=w, days=d, hours=h, minutes=mi,
                                   seconds=s)
        else:
            dtend = None
        uid = ev.get("uid") or (hashlib.sha256((
            str(ev.get("summary", "")) + dt.isoformat()).encode()).hexdigest()
            [:32] + "@mechacut")

        def fmt(x):
            if x.tzinfo is None:
                return x.strftime("%Y%m%dT%H%M%S")
            return x.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        lines.append("BEGIN:VEVENT")
        lines.append("UID:" + _esc(uid))
        # DTSTAMP is deterministic: explicit `stamp`, else DTSTART, else the
        # epoch sentinel — never wall-clock now(), or the bytes would drift.
        stamp = ev.get("stamp")
        if stamp is not None:
            st = _parse_instant(stamp, tz=ev.get("tz", "UTC"))
            lines.append("DTSTAMP:" + fmt(st if st.tzinfo else
                                          st.replace(tzinfo=timezone.utc)))
        elif dt.tzinfo is not None:
            lines.append("DTSTAMP:" + fmt(dt))
        else:
            lines.append("DTSTAMP:19700101T000000Z")
        if allday:
            lines.append("DTSTART;VALUE=DATE:" + dt.strftime("%Y%m%d"))
            if dtend is not None:
                lines.append("DTEND;VALUE=DATE:" + dtend.strftime("%Y%m%d"))
        else:
            lines.append("DTSTART:" + fmt(dt))
            if dtend is not None:
                lines.append("DTEND:" + fmt(dtend))
        if ev.get("summary") is not None:
            lines.append("SUMMARY:" + _esc(ev["summary"]))
        for key in ("description", "location", "organizer", "url",
                    "status", "rrule", "categories"):
            v = ev.get(key)
            if v is None:
                continue
            if key == "organizer" and not str(v).startswith("mailto:"):
                v = "mailto:" + str(v)
            if key == "categories" and isinstance(v, list):
                v = ",".join(str(x) for x in v)
            lines.append(key.upper() + ":" + _esc(v))
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    folded = []
    for l in lines:
        folded.extend(_fold(l))
    return "\r\n".join(folded) + "\r\n"


_UNFOLD = re.compile(r"\r?\n[ \t]")


def ics_parse(text):
    if not isinstance(text, str) or "BEGIN:VCALENDAR" not in text:
        raise DateError("not a VCALENDAR document")
    body = _UNFOLD.sub("", text.replace("\r\n", "\n").replace("\r", "\n"))
    meta = {"prodid": None, "version": None, "calscale": None,
            "calname": None}
    events = []
    cur = None
    for line in body.split("\n"):
        if not line.strip():
            continue
        if line == "BEGIN:VEVENT":
            cur = {}
            continue
        if line == "END:VEVENT":
            if cur is not None:
                events.append(_finalize_event(cur))
            cur = None
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        name, _, params = key.partition(";")
        name = name.upper()
        if cur is None:
            if name == "PRODID":
                meta["prodid"] = val
            elif name == "VERSION":
                meta["version"] = val
            elif name == "CALSCALE":
                meta["calscale"] = val
            elif name == "X-WR-CALNAME":
                meta["calname"] = val
            continue
        tzid = None
        for p in params.split(";"):
            if p.upper().startswith("TZID="):
                tzid = p[5:]
            if p.upper().startswith("VALUE=DATE"):
                tzid = tzid or "DATE"
        cur.setdefault("_p", {})[name] = (val, tzid)
    return {"calendar": meta, "events": events, "count": len(events)}


def _unescape(v):
    out = []
    i = 0
    while i < len(v):
        c = v[i]
        if c == "\\" and i + 1 < len(v):
            n = v[i + 1]
            if n in "nN":
                out.append("\n")
            elif n in ";,\\":
                out.append(n)
            else:
                out.append(n)
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _fmt_ics_dt(val, tzid):
    val = val.strip()
    if tzid == "DATE" or re.match(r"^\d{8}$", val):
        return date(int(val[0:4]), int(val[4:6]), int(val[6:8])).isoformat()
    if re.match(r"^\d{8}T\d{6}Z$", val):
        dt = datetime.strptime(val, "%Y%m%dT%H%M%SZ").replace(
            tzinfo=timezone.utc)
        return dt.isoformat()
    if re.match(r"^\d{8}T\d{6}$", val):
        dt = datetime.strptime(val, "%Y%m%dT%H%M%S")
        if tzid:
            dt = dt.replace(tzinfo=_zone(tzid))
        return dt.isoformat()
    return val


def _finalize_event(raw):
    p = raw.get("_p", {})

    def get(k, unescape=True):
        v = p.get(k, (None, None))[0]
        if v is None:
            return None
        return _unescape(v) if unescape else v

    start_v, start_tz = p.get("DTSTART", (None, None))
    end_v, end_tz = p.get("DTEND", (None, None))
    ev = {
        "uid": get("UID"),
        "summary": get("SUMMARY"),
        "description": get("DESCRIPTION"),
        "location": get("LOCATION"),
        "status": get("STATUS"),
        "url": get("URL"),
        "rrule": get("RRULE", unescape=False),
        "categories": [c for c in (get("CATEGORIES") or "").split(",")
                       if c] or None,
        "organizer": get("ORGANIZER"),
        "start": _fmt_ics_dt(start_v, start_tz) if start_v else None,
        "end": _fmt_ics_dt(end_v, end_tz) if end_v else None,
        "duration_seconds": None,
    }
    if ev["start"] and ev["end"]:
        try:
            a = datetime.fromisoformat(ev["start"])
            b = datetime.fromisoformat(ev["end"])
            if a.tzinfo is None and b.tzinfo is None or \
               (a.tzinfo is not None and b.tzinfo is not None):
                ev["duration_seconds"] = int((b - a).total_seconds())
        except ValueError:
            pass
    d = p.get("DURATION", (None, None))[0]
    if d and ev["duration_seconds"] is None:
        m = _DUR_RE.match(d.upper())
        if m:
            w, dd, h, mi, s = (int(g) if g else 0 for g in m.groups())
            ev["duration_seconds"] = ((w * 7 + dd) * 86400 + h * 3600 +
                                      mi * 60 + s)
    return {k: v for k, v in ev.items() if v is not None or k == "uid"}


# --------------------------------------------------------------------------
# date_window — bundle 86. « not less than 180 nor more than 270 days
# before X » : la borne seule ne rend pas la clause. Ici on rend la FENÊTRE
# entière, inclusive, avec son span et sa phrase. Bornes inversées = refus
# nommé (on ne trie pas à la place de l'humain), egales = un jour, pas un
# refus. @prismdeadlines, m/agentskills, 23-11.
# --------------------------------------------------------------------------
def _strict_day(value, field):
    if not isinstance(value, str) or not value.strip():
        raise DateError("%s: an ISO date is required (YYYY-MM-DD)" % field)
    v = value.strip()
    if len(v) != 10 or v[4] != "-" or v[7] != "-":
        raise DateError("%s must be strict ISO YYYY-MM-DD, got %r — "
                        "slashes and words are other tools' job"
                        % (field, value))
    try:
        y, m, dd = (int(x) for x in v.split("-"))
        return date(y, m, dd)
    except ValueError:
        raise DateError("%s: not a calendar date: %r" % (field, value))


def window(event, direction, min_days, max_days):
    d = _strict_day(event, "event")
    if direction not in ("before", "after"):
        raise DateError("direction must be 'before' or 'after': %r"
                        % direction)
    for v, w in ((min_days, "min_days"), (max_days, "max_days")):
        if isinstance(v, bool) or not isinstance(v, int):
            raise DateError("%s must be an integer number of days" % w)
        if v < 0:
            raise DateError("%s must be >= 0: %d" % (w, v))
    if min_days > max_days:
        raise DateError("min_above_max: min_days=%d exceeds max_days=%d — "
                        "a clause reads not less than X nor more than Y; "
                        "we do not silently sort a contract"
                        % (min_days, max_days))
    if direction == "before":
        earliest = d - timedelta(days=max_days)
        latest = d - timedelta(days=min_days)
    else:
        earliest = d + timedelta(days=min_days)
        latest = d + timedelta(days=max_days)
    span = (latest - earliest).days
    return {"event": d.isoformat(), "direction": direction,
            "earliest": earliest.isoformat(), "latest": latest.isoformat(),
            "span_days": span, "bounds": "inclusive",
            "meaning": "the act must fall between %s and %s (inclusive), "
                       "i.e. %d to %d days %s the event" % (
                           earliest.isoformat(), latest.isoformat(),
                           min_days, max_days, direction)}


# --------------------------------------------------------------------------
# date_deemed — bundle 86. Une date de réception RÉPUTÉE dépend du mode
# d'envoi ; sans mode connu, on ne donne PAS de date. Table fermée, nommée,
# dépassable par argument explicite (l'argument est dit comme argument).
# --------------------------------------------------------------------------
_DEEMED_TABLE = {"email": 0, "courier": 1, "registered": 2,
                 "standard_mail": 5}


def deemed(sent, method, deemed_days=None):
    if not isinstance(method, str) or not method.strip():
        raise DateError("method_required: no deemed receipt date is given "
                        "until the mode of sending is known — accepted: "
                        "email | courier | registered | standard_mail")
    if method not in _DEEMED_TABLE:
        raise DateError("unknown method: %r (closed table: email, courier, "
                        "registered, standard_mail)" % method)
    d = _strict_day(sent, "sent")
    table = _DEEMED_TABLE[method]
    if deemed_days is None:
        days, source = table, "table"
    else:
        if isinstance(deemed_days, bool) or not isinstance(deemed_days, int):
            raise DateError("deemed_days must be an integer")
        if not 0 <= deemed_days <= 90:
            raise DateError("deemed_days outside 0..90 (named ceiling): %d"
                            % deemed_days)
        days, source = deemed_days, "argument"
    return {"sent": d.isoformat(), "method": method, "days": days,
            "table_days": table, "source": source,
            "deemed_receipt": (d + timedelta(days=days)).isoformat()}


# --------------------------------------------------------------------------
# date_civil — bundle 89 (@LilySaucy). 212 factures de Tokyo datées au
# fuseau du serveur : le UTC était juste, l'exercice était faux. Ici le
# fuseau est un ARGUMENT OBLIGATOIRE et la réponse dit si la date civile
# CHANGE D'ANNÉE par rapport au UTC — le glissement fiscal est nommé,
# jamais silencé. L'horloge du serveur n'est jamais lue.
# --------------------------------------------------------------------------
def civil(instant, timezone):
    if not isinstance(timezone, str) or not timezone.strip():
        raise DateError("tz_required: the civil date belongs to a NAMED "
                        "zone — the server's own zone is never read "
                        "(212 invoices learned that the hard way)")
    try:
        z = _zone(timezone)
    except DateError:
        raise DateError("zone_unknown: %r — use an IANA name, e.g. "
                        "Asia/Tokyo" % timezone)
    if not isinstance(instant, str) or not instant.strip():
        raise DateError("instant: ISO timestamp with offset required")
    dt = _parse_instant(instant)
    if dt.tzinfo is None:
        raise DateError("instant must carry its offset (+00:00) — a naked "
                        "wall time has no civil date anywhere until a zone "
                        "is named")
    import datetime as _m
    loc = dt.astimezone(z)
    utc_d = dt.astimezone(_m.timezone.utc).date()
    off = loc.strftime("%z")
    off = off[:3] + ":" + off[3:] if off else "+00:00"
    return {"utc_date": utc_d.isoformat(),
            "civil_date": loc.date().isoformat(),
            "civil_weekday": loc.strftime("%A"),
            "offset": off, "zone": timezone.strip(),
            "day_shift": utc_d != loc.date(),
            "year_shift": utc_d.year != loc.date().year}
