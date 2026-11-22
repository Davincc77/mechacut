"""tzambkit — /date/tz_ambiguity : l'heure murale que le cron ne peut pas avoir.

Spring forward : une heure du cadran N'EXISTE PAS (trou). Fall back : une
heure existe DEUX FOIS (doublon). date/tz résout les deux EN SILENCE par
les règles PEP 495 de zoneinfo (dates.py:42) — cette route le DIT, en
nommant chaque instant UTC, son offset et son abréviation, plus la
transition et sa fenêtre.

ZÉRO table embarquée, zéro fetch : l'oracle est la base IANA tzdata
installée sur le serveur, interrogée par zoneinfo lui-même à la date
demandée (binaire search sur l'offset — quelques microsecondes). Les
preuves de demande (nov. 2026) : cron 4.4.0 mesuré tirant DEUX FOIS un
job réglé à l'heure qui SUIT le doublon (nestjs/schedule #2389) ; K8s
CronJob 1.37.2 créant deux Jobs pour « 30 1 * * * » (cybernative) ;
durable-workflow #882 publiant comme correctif exactement ce contrat :
« repeated → un tir nommé ; nonexistent → une règle NOMMÉE ».

Contrat d'entrée = chaînes (ScaleRequest precedent) : l'heure locale est
le cadran qu'on écrirait dans la crontab — un offset en entrée est
REFUSÉ par le nom, c'est précisément ce qui est ambigu ici.
"""

import re
from datetime import datetime, timedelta, timezone

from dates import DateError, _fmt_off, _zone

_ONE_SECOND = timedelta(seconds=1)
_UTC = timezone.utc


class TzAmbError(ValueError):
    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected


_LOCAL_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?$")
_OFFSET_TAIL_RE = re.compile(r"(Z|z|[+-]\d{2}:?\d{2})$")

_EXPECTED_LOCAL = ("a LOCAL wall clock with no offset, e.g. "
                   "'2026-11-01 01:30' or '2026-11-01T01:30:45'")


def _parse_local(value):
    if not isinstance(value, str) or not value.strip():
        raise TzAmbError("local", "missing or empty", _EXPECTED_LOCAL)
    t = value.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", t):
        raise TzAmbError("local",
                         "date without a time: the ambiguity lives in "
                         "the hour — give the wall clock you would put "
                         "in the crontab",
                         _EXPECTED_LOCAL)
    if _OFFSET_TAIL_RE.search(t):
        raise TzAmbError(
            "local",
            "offset refused: the offset is EXACTLY what is ambiguous on "
            "a transition day — pass the wall clock only",
            _EXPECTED_LOCAL)
    m = _LOCAL_RE.match(t)
    if not m:
        raise TzAmbError("local", "unparsable wall clock %r" % value,
                         _EXPECTED_LOCAL)
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                        int(m.group(4)), int(m.group(5)),
                        int(m.group(6) or 0))
    except ValueError as e:
        raise TzAmbError("local", "impossible wall clock %r (%s)"
                         % (value, e), _EXPECTED_LOCAL)


def _resolve_zone(name):
    if not isinstance(name, str) or not name.strip():
        raise TzAmbError("zone", "missing or empty: the zone is never "
                         "guessed (a model that 'defaults to UTC' books "
                         "meetings nobody attends)",
                         "an IANA name, e.g. America/New_York, or UTC")
    try:
        return _zone(name.strip()), name.strip()
    except DateError:
        raise TzAmbError("zone", "unknown timezone %r" % name,
                         "an IANA name, e.g. America/New_York, or UTC")


def _off_at(z, udt):
    """True UTC offset of the zone at an absolute instant (aware UTC)."""
    return udt.astimezone(z).utcoffset()


def _search_transition(z, lo, hi):
    """First instant T in (lo, hi] whose zone offset differs from
    offset(lo). lo/hi are aware UTC datetimes, hi > lo, one second apart
    at best. Binary search on whole seconds — tzdata transitions are
    second-granular."""
    base = _off_at(z, lo)
    a, b = lo, hi
    while (b - a) > _ONE_SECOND:
        mid = a + (b - a) / 2
        mid = mid.replace(microsecond=0)
        if _off_at(z, mid) == base:
            a = mid
        else:
            b = mid
    return b


def _iso(dt):
    return dt.isoformat()


def _wall(z, udt):
    return udt.astimezone(z)


def _instant_block(utc_dt, offset, abbrev):
    return {"utc": _iso(utc_dt),
            "offset": _fmt_off(offset),
            "tz_abbrev": abbrev}


def classify(zone_name, local_str):
    """One wall clock + one zone -> the named verdict."""
    z, zone = _resolve_zone(zone_name)
    naive = _parse_local(local_str)
    d0 = naive.replace(tzinfo=z)                 # fold=0 (default)
    d1 = naive.replace(fold=1, tzinfo=z)
    o0, o1 = d0.utcoffset(), d1.utcoffset()
    u0 = d0.astimezone(_UTC)
    u1 = d1.astimezone(_UTC)

    if o0 == o1:
        # The wall clock occurs exactly once (or the zone has no such
        # rule at this date). Round-trip guard: belt AND braces.
        if u0.astimezone(z).replace(tzinfo=None, fold=0) != naive:
            raise TzAmbError("local",
                             "round-trip mismatch on a single-offset "
                             "time — refuse to answer rather than lie",
                             _EXPECTED_LOCAL)
        dst = d0.dst() or timedelta(0)
        return {
            "zone": zone,
            "local": local_str.strip(),
            "kind": "single",
            "verdict": "%s occurs exactly once in %s" % (
                naive.strftime("%Y-%m-%d %H:%M:%S"), zone),
            "utc": _iso(u0),
            "offset": _fmt_off(o0),
            "tz_abbrev": d0.tzname(),
            "dst_active": dst != timedelta(0),
        }

    fold = u0 < u1           # two instants (repeat) vs none (gap)
    lo, hi = (u0, u1) if fold else (u1, u0)
    T = _search_transition(z, lo, hi)
    off_pre = _off_at(z, T - _ONE_SECOND)
    off_post = _off_at(z, T)
    pre_wall = _wall(z, T - _ONE_SECOND)   # last wall before the jump
    post_wall = _wall(z, T)                # first wall at/after the jump

    transition = {
        "utc": _iso(T),
        "from_offset": _fmt_off(off_pre),
        "from_abbrev": pre_wall.tzname(),
        "to_offset": _fmt_off(off_post),
        "to_abbrev": post_wall.tzname(),
        "change_minutes": int(
            ((off_post or timedelta(0))
             - (off_pre or timedelta(0))).total_seconds() // 60),
    }
    if fold:
        transition["type"] = "repeat"
        # the repeated wall-clock window: [start, end)
        transition["window_start"] = post_wall.strftime("%H:%M")
        transition["window_end"] = (pre_wall + _ONE_SECOND) \
            .strftime("%H:%M")
    else:
        transition["type"] = "skip"
        transition["window_start"] = (pre_wall + _ONE_SECOND) \
            .strftime("%H:%M")
        transition["window_end"] = post_wall.strftime("%H:%M")

    base = {
        "zone": zone,
        "local": local_str.strip(),
        "transition": transition,
    }
    if fold:
        base.update({
            "kind": "fold",
            "verdict": "%s happens TWICE in %s" % (
                naive.strftime("%Y-%m-%d %H:%M:%S"), zone),
            "instants": [
                dict(_instant_block(u0, o0, d0.tzname()),
                     fold=0, role="first occurrence (pre-transition)"),
                dict(_instant_block(u1, o1, d1.tzname()),
                     fold=1, role="second occurrence (post-transition)"),
            ],
            "pep495": "Python: fold=0 -> %s, fold=1 -> %s. zoneinfo "
                      "already applied this rule silently to every "
                      "conversion you ran near a transition; this "
                      "route says it out loud." % (_iso(u0), _iso(u1)),
        })
    else:
        base.update({
            "kind": "gap",
            "verdict": "%s NEVER happens in %s" % (
                naive.strftime("%Y-%m-%d %H:%M:%S"), zone),
            "nearest": [
                dict(_instant_block(
                    T - _ONE_SECOND,
                    pre_wall.utcoffset(), pre_wall.tzname()),
                    local=pre_wall.strftime("%Y-%m-%d %H:%M:%S"),
                    role="last valid wall clock before the jump"),
                dict(_instant_block(T, post_wall.utcoffset(),
                                    post_wall.tzname()),
                     local=post_wall.strftime("%Y-%m-%d %H:%M:%S"),
                     role="first valid wall clock after the jump"),
            ],
            "pep495": "No fold value makes this instant exist: fold=0 "
                      "yields %s, fold=1 yields %s — both land on "
                      "DIFFERENT real wall clocks when read back. A "
                      "scheduler must pick a named rule (run at the "
                      "first valid time shifted by the gap, or skip)."
                      % (_iso(u0), _iso(u1)),
        })
    base["scheduler_note"] = (
        "Schedulers disagree on transition days: man7 cron may run "
        "twice, cronie protects fixed-time jobs, K8s CronJob and cron "
        "4.4.0 were MEASURED double-running in Nov 2026 (cron 4.4.0 "
        "even re-fires the hour AFTER the repeat), and wildcard "
        "entries like '*/15 1 * * *' can fire once per wall pass. "
        "The instants above are the facts; the pick is yours — "
        "idempotency keyed on the logical period beats dedup on the "
        "fire moment.")
    base["scope_note"] = (
        "Computed from the IANA tz database installed on this server "
        "via zoneinfo — no embedded table, no fetch, results for past "
        "and future transition dates are the ones tzdata encodes. "
        "Zones under live legislation (several Canadian provinces "
        "moved in Nov 2026) change with tzdata releases; re-check "
        "those near the date in question.")
    return base


def run_tz_amb(args):
    return classify(args.get("zone"), args.get("local") or "")
