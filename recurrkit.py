"""recurrkit — /api/v1/date/recurrence : déploie un RRULE en dates, sans deviner.

Un RRULE est une grammaire PUBLIÉE (RFC 5545 §3.3.10 + §3.8.5.3), pas une
intention. Les modèles, eux, le traitent comme une suggestion : la démo
publiée de temporal-cortex (nov. 2026) montre un frontier model qui IGNORE
INTERVAL=2 sur « every other week, TU+TH, 8 occurrences » — « 4 out of 8
dates wrong ». truto (table de signatures d'échec, MAJ 15 juil.) liste la
classe entière : DTSTART non traité comme première occurrence (LE DÉFAUT
de rrule.js), WKST ignoré (biweekly sur les mauvais jours), BYSETPOS
manquant (le 2e jeudi rendu comme le 1er). python-dateutil 4.0.0 lit
« MO,2TU » comme AUCUNE date (fixtures Duncan-Haywood, 14 nov.). Ici on
déploie le texte de la RFC et chaque piège est DIT DANS LA RÉPONSE.

Sous-ensemble FERMÉ annoncé (le reste est REFUSÉ PAR LE NOM, jamais
ignoré en doux) :
    FREQ      DAILY | WEEKLY | MONTHLY | YEARLY
              SECONDLY/MINUTELY/HOURLY refusés : hors contrat, déclaré
    INTERVAL  entier ≥ 1 (défaut 1)
    COUNT xor UNTIL — « they MUST NOT occur in the same 'recur' » (§3.3.10)
    BYDAY     [±n] MO..SU ; ordinal permis uniquement pour MONTHLY/YEARLY
              (« MUST NOT be specified with a numeric value when the FREQ
              rule part is not set to MONTHLY or YEARLY »)
    BYMONTH   1..12 ; BYMONTHDAY ±1..±31 (« MUST NOT be specified when
              the FREQ rule part is set to WEEKLY »)
    WKST      MO..SU, défaut MO — significatif dès INTERVAL>1 en WEEKLY
    refusés   BYSETPOS, BYWEEKNO, BYYEARDAY, BYHOUR, BYMINUTE, BYSECOND
              (nommés dans l'erreur avec la raison)

Sémantique ancrée (§ = RFC 5545) :
  • « The DTSTART property defines the first instance in the recurrence
    set » et « The DTSTART property value always counts as the first
    occurrence » (§3.8.5.3, §3.3.10). Le RFC réserve la zone non
    synchronisée : « generated with a DTSTART value not synchronized with
    the recurrence rule is UNDEFINED ». rrule.js y INCLUT le dtstart
    (off-by-one), dateutil l'EXCLUT silencieusement ; le propre exemple
    Friday-the-13th du RFC part d'un mardi non synchronisé. Nous : le
    dtstart ANCRE la grille, n'est occurrence que s'il en est une, et la
    désynchronisation est SIGNALÉE (dtstart_synced=false + note), jamais
    tranchée en silence.
  • §3.3.10 : « instances with an invalid date (e.g., February 30) ...
    MUST be ignored » — le RFC DROPPE, il ne DÉPLACE pas. MONTHLY parti
    du 31 ne tombe que dans les mois de 31 jours ; les fenêtres sautées
    sont ÉNUMÉRÉES (la douleur fixture : 7 mois sur 12).
  • Ordre d'application §3.3.10 : BYMONTH, puis BYMONTHDAY, puis BYDAY
    (Note 1 : avec BYMONTHDAY présent, BYDAY LIMITE — l'exemple
    Friday-the-13th), puis COUNT/UNTIL. Respecté tel quel.
  • UNTIL borne INCLUSIVE, « MUST have the same value type as DTSTART »
    — mélange DATE/DATE-TIME = refus nommé.
  • Une série sans COUNT ni UNTIL est INFINIE (notée par le portage Go
    Malcolmston/rrule) : CAP dur de 500 occurrences, truncature déclarée.

Modèle horaire : WALL-CLOCK pur — « the same local time regardless of
time zone changes » (§3.8.5.3). L'expansion en UTC recréée EST la
signature « duplicate instances at DST transition » de la table truto.
Les instants par jour se prennent avec /api/v1/date/tz ; c'est dans
rules_applied. Runtime sans dépendance : datetime+calendar only ;
python-dateutil n'est qu'un oracle de TEST.
"""
import calendar
import re
from datetime import date, datetime, timedelta

CAP = 500                          # borne dure, déclarée dans chaque réponse
WD = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]      # index = date.weekday()
WD_NAMES = {"MO": "Mon", "TU": "Tue", "WE": "Wed", "TH": "Thu",
            "FR": "Fri", "SA": "Sat", "SU": "Sun"}
FREQS = ("DAILY", "WEEKLY", "MONTHLY", "YEARLY")
SUB_SEC_FREQS = ("SECONDLY", "MINUTELY", "HOURLY")
SUPPORTED = ("FREQ", "INTERVAL", "COUNT", "UNTIL", "BYDAY", "BYMONTH",
             "BYMONTHDAY", "WKST")
REFUSED_BY_NAME = ("BYSETPOS", "BYWEEKNO", "BYYEARDAY", "BYHOUR",
                   "BYMINUTE", "BYSECOND")

# budgets de scan : borne d'ARRÊT du calcul, jamais du résultat — après
# N fenêtres d'intervalle sans instance, une série sans borne est
# déclarée « never » (le filtre n'admet aucune date, p. ex.
# BYMONTH=2;BYMONTHDAY=30) ; au-delà du budget global on déclare
# « exhausted » plutôt que de tourner.
_EMPTY_DECLARE = {"DAILY": 400, "WEEKLY": 100, "MONTHLY": 60, "YEARLY": 40}
_SCAN_LIMIT = {"DAILY": 20000, "WEEKLY": 2000, "MONTHLY": 600, "YEARLY": 240}

_CLOSED_SUBSET = ("closed subset: FREQ DAILY|WEEKLY|MONTHLY|YEARLY; "
                  "INTERVAL; COUNT xor UNTIL; BYDAY ordinals only for "
                  "MONTHLY/YEARLY; BYMONTH; BYMONTHDAY signed; WKST. "
                  "BYSETPOS BYWEEKNO BYYEARDAY BYHOUR BYMINUTE BYSECOND "
                  "and FREQ SECONDLY/MINUTELY/HOURLY are refused by "
                  "name, never softly ignored. Hard cap: 500 "
                  "occurrences.")
_DROP_NOTE = ("RFC 5545 §3.3.10: recurrence instances with an invalid "
              "date MUST be ignored — the RFC DROPS them, it never MOVES "
              "them. A MONTHLY series anchored on the 31st lands only in "
              "31-day months; a YEARLY anchor on Feb 29 only in leap "
              "years")
_UNSYNC_NOTE = ("RFC 5545 §3.8.5.3: a recurrence set generated with a "
                "DTSTART not synchronized with the rule is UNDEFINED. "
                "This engine anchors the grid at DTSTART and returns the "
                "instances it admits; DTSTART is never force-included. "
                "rrule.js includes it (off-by-one), dateutil drops it "
                "silently — here it is declared, not guessed")
_WALL_NOTE = ("wall-clock expansion: every instance keeps DTSTART's time "
              "of day (§3.8.5.3 « the same local time regardless of time "
              "zone changes »); across a DST shift the UTC instant moves "
              "but the local time does not. Per-day instants: "
              "/api/v1/date/tz")
_ORDER_NOTE = ("application order per §3.3.10: BYMONTH, then BYMONTHDAY, "
               "then BYDAY (with BYMONTHDAY present, BYDAY LIMITS — the "
               "RFC's own Friday-the-13th example), then COUNT/UNTIL; "
               "UNTIL bounds inclusively and MUST share DTSTART's value "
               "type")


class RecurrenceError(Exception):
    def __init__(self, field, message, expected):
        Exception.__init__(self, message)
        self.field = field
        self.message = message
        self.expected = expected


# ---------------------------------------------------------------- parsing

_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_DT_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})"
                    r"[ T](\d{2}):(\d{2})(?::(\d{2}))?(Z)?$")
_COMPACT_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2})(Z)?)?$")
_PART_RE = re.compile(r"^([A-Za-z]+)=(.+)$")
_BYDAY_RE = re.compile(r"^([+-]?)(\d{0,2})([A-Za-z]{2})$")
_MONTHDAY_RE = re.compile(r"^([+-]?)(\d{1,2})$")


def _parse_instant(value):
    """Return (dt, kind) with dt a date (kind='date') or naive datetime,
    kind in ('date', 'datetime', 'datetime-utc'). Both spellings of the
    RFC are accepted (dashed + compact); the choice is DECLARED."""
    if not isinstance(value, str) or not value.strip():
        raise RecurrenceError("dtstart", "date/recurrence: dtstart is required",
                              "YYYY-MM-DD, YYYY-MM-DDTHH:MM[:SS][Z], or the "
                              "RFC compact form 19970902T090000Z")
    s = value.strip()
    m = _DATE_RE.match(s)
    if m:
        y, mo, d = (int(x) for x in m.groups())
        _check_ymd(y, mo, d, s, "dtstart")
        return date(y, mo, d), "date"
    m = _DT_RE.match(s) or _COMPACT_RE.match(s)
    if not m:
        raise RecurrenceError("dtstart",
                              "date/recurrence: unparseable dtstart %r" % value,
                              "DATE, floating DATE-TIME, or UTC DATE-TIME (Z)")
    y, mo, d, hh, mm, ss, zulu = m.groups()
    y, mo, d = int(y), int(mo), int(d)
    _check_ymd(y, mo, d, s, "dtstart")
    if hh is None:
        # compact DATE with no time part: 19970902 → all-day
        return date(y, mo, d), "date"
    hh, mm, ss = int(hh), int(mm), int(ss or 0)
    if hh > 23 or mm > 59 or ss > 59:
        raise RecurrenceError("dtstart",
                              "date/recurrence: dtstart %r time out of range"
                              % value, "HH 00-23, MM/SS 00-59")
    return datetime(y, mo, d, hh, mm, ss), ("datetime-utc" if zulu
                                            else "datetime")


def _check_ymd(y, mo, d, s, field):
    if not (1 <= mo <= 12):
        raise RecurrenceError(field, "date/recurrence: month out of range "
                              "in %r" % s, "01..12")
    if not (1 <= d <= calendar.monthrange(y, mo)[1]):
        raise RecurrenceError(field, "date/recurrence: %r is not a real "
                              "calendar date" % s, "a valid date")


def _parse_until(raw, kind):
    """UNTIL must share DTSTART's value type (§3.3.10 MUST)."""
    s = raw.strip()
    m = _DATE_RE.match(s)
    got_date = bool(m)
    m = m or _DT_RE.match(s) or _COMPACT_RE.match(s)
    if not m:
        raise RecurrenceError("rrule",
                              "date/recurrence: unparseable UNTIL %r" % raw,
                              "same value type as DTSTART")
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    _check_ymd(y, mo, d, s, "rrule")
    if got_date or m.group(4) is None:
        # DATE value type (dashed or compact-without-T); a trailing Z on
        # a DATE is the RFC's UTC-time form of DATE-TIME, already routed
        # through the datetime branch above by _DT_RE
        val, u_kind = date(y, mo, d), "date"
    else:
        hh, mm, ss = int(m.group(4)), int(m.group(5)), int(m.group(6) or 0)
        zulu = m.group(7)
        if hh > 23 or mm > 59 or ss > 59:
            raise RecurrenceError("rrule", "date/recurrence: UNTIL %r time "
                                  "out of range" % raw, "HH 00-23, MM/SS 00-59")
        val = datetime(y, mo, d, hh, mm, ss)
        u_kind = "datetime-utc" if zulu else "datetime"
    if u_kind != kind:
        raise RecurrenceError(
            "rrule",
            "date/recurrence: UNTIL type %s vs DTSTART type %s — ‘The value "
            "of the UNTIL rule part MUST have the same value type as the "
            "DTSTART property’ (§3.3.10)" % (u_kind, kind),
            "both DATE, both floating DATE-TIME, or both UTC DATE-TIME (Z)")
    return val


def _norm_rrule(value):
    if not isinstance(value, str) or not value.strip():
        raise RecurrenceError("rrule", "date/recurrence: rrule is required",
                              "an RFC 5545 RRULE value, e.g. FREQ=WEEKLY;"
                              "INTERVAL=2;BYDAY=TU,TH;COUNT=8")
    s = value.strip()
    if s.upper().startswith("RRULE:"):
        s = s[6:]                       # lenient BY NAME, declared below
    parts = {}
    first = True
    for raw in s.split(";"):
        if raw == "":
            raise RecurrenceError("rrule",
                                  "date/recurrence: empty rule part (a bare "
                                  "‘;’ in %r)" % value, "NAME=value pairs "
                                  "separated by ‘;’")
        m = _PART_RE.match(raw.strip())
        if not m:
            raise RecurrenceError("rrule",
                                  "date/recurrence: malformed rule part %r"
                                  % raw, "NAME=value")
        name, val = m.group(1).upper(), m.group(2).strip()
        if name in parts:
            raise RecurrenceError(
                "rrule",
                "date/recurrence: %s specified twice — ‘Individual rule "
                "parts MUST only be specified once’ (§3.3.10)" % name,
                "%s once" % name)
        parts[name] = val
        first = False
    return parts


def _pos_int(raw, name, lo, hi):
    if not re.match(r"^\d+$", raw) or not (lo <= int(raw) <= hi):
        raise RecurrenceError("rrule",
                              "date/recurrence: %s=%r out of range" % (name, raw),
                              "%s=%d..%d" % (name, lo, hi))
    return int(raw)


def _parse_rule(parts, kind):
    for name in parts:
        if name in REFUSED_BY_NAME:
            raise RecurrenceError(
                "rrule",
                "date/recurrence: %s is refused by name — outside the closed "
                "RFC 5545 subset, never silently ignored (§3.3.10 lists it; "
                "we declined it)" % name, _CLOSED_SUBSET)
        if name not in SUPPORTED:
            raise RecurrenceError("rrule",
                                  "date/recurrence: unknown rule part %s"
                                  % name, "only " + "|".join(SUPPORTED))
    if "FREQ" not in parts:
        raise RecurrenceError("rrule",
                              "date/recurrence: FREQ is required (§3.3.10)",
                              "FREQ=DAILY|WEEKLY|MONTHLY|YEARLY first")
    freq = parts["FREQ"].upper()
    if freq in SUB_SEC_FREQS:
        raise RecurrenceError("rrule",
                              "date/recurrence: FREQ=%s is refused by name — "
                              "sub-daily series are outside the contract"
                              % freq, "FREQ=DAILY|WEEKLY|MONTHLY|YEARLY")
    if freq not in FREQS:
        raise RecurrenceError("rrule", "date/recurrence: unknown FREQ %r"
                              % parts["FREQ"], "DAILY|WEEKLY|MONTHLY|YEARLY")

    rule = {"freq": freq, "normalized_had_rrule_prefix": False}
    rule["interval"] = _pos_int(parts["INTERVAL"], "INTERVAL", 1, 100000) \
        if "INTERVAL" in parts else 1

    if "COUNT" in parts and "UNTIL" in parts:
        raise RecurrenceError(
            "rrule",
            "date/recurrence: COUNT and UNTIL in one rule — ‘The UNTIL or "
            "COUNT rule parts are OPTIONAL, but they MUST NOT occur in the "
            "same recur’ (§3.3.10)", "COUNT or UNTIL, never both")
    rule["count"] = None
    if "COUNT" in parts:
        n = _pos_int(parts["COUNT"], "COUNT", 1, 10 ** 9)
        if n > CAP:
            raise RecurrenceError(
                "rrule",
                "date/recurrence: COUNT=%d exceeds the hard cap of %d — "
                "this engine answers bounded expansions; page the series "
                "with UNTIL windows" % (n, CAP), "COUNT ≤ %d" % CAP)
        rule["count"] = n
    rule["until"] = _parse_until(parts["UNTIL"], kind) if "UNTIL" in parts \
        else None
    rule["until_raw"] = parts.get("UNTIL")

    rule["bymonth"] = []
    if "BYMONTH" in parts:
        rule["bymonth"] = sorted({_pos_int(t, "BYMONTH", 1, 12)
                                  for t in _tokens(parts["BYMONTH"])})

    rule["bymonthday"] = []
    if "BYMONTHDAY" in parts:
        if freq == "WEEKLY":
            raise RecurrenceError(
                "rrule",
                "date/recurrence: BYMONTHDAY with FREQ=WEEKLY — ‘The "
                "BYMONTHDAY rule part MUST NOT be specified when the FREQ "
                "rule part is set to WEEKLY’ (§3.3.10)", _CLOSED_SUBSET)
        seen = []
        for t in _tokens(parts["BYMONTHDAY"]):
            m = _MONTHDAY_RE.match(t)
            if not m:
                raise RecurrenceError("rrule", "date/recurrence: malformed "
                                      "BYMONTHDAY %r" % t, "1..31 or -31..-1")
            n = int(m.group(2))
            if m.group(1) == "-":
                n = -n
            if n == 0 or abs(n) > 31:
                raise RecurrenceError("rrule", "date/recurrence: BYMONTHDAY "
                                      "%r out of range" % t,
                                      "1..31 or -31..-1, no 0")
            if n not in seen:
                seen.append(n)
        rule["bymonthday"] = seen

    rule["byday"] = []
    if "BYDAY" in parts:
        seen = []
        for t in _tokens(parts["BYDAY"]):
            m = _BYDAY_RE.match(t)
            if not m:
                raise RecurrenceError(
                    "rrule", "date/recurrence: malformed BYDAY value %r" % t,
                    "[±][1-53]MO..SU, e.g. 2TU, -1MO, FR")
            sign, ordn, wd = m.group(1), m.group(2), m.group(3).upper()
            if wd not in WD:
                raise RecurrenceError("rrule", "date/recurrence: unknown "
                                      "weekday %r in BYDAY" % wd,
                                      "|".join(WD))
            n = 0
            if ordn:
                n = int(ordn)
                if sign == "-":
                    n = -n
                if n == 0 or abs(n) > 53:
                    raise RecurrenceError("rrule", "date/recurrence: BYDAY "
                                          "ordinal %r out of range" % t,
                                          "±1..±53")
                if freq not in ("MONTHLY", "YEARLY"):
                    raise RecurrenceError(
                        "rrule",
                        "date/recurrence: BYDAY=%s with FREQ=%s — ‘The BYDAY "
                        "rule part MUST NOT be specified with a numeric "
                        "value when the FREQ rule part is not set to MONTHLY "
                        "or YEARLY’ (§3.3.10). Mixed forms like MO,2TU are "
                        "parsed per the ABNF when FREQ allows them — "
                        "python-dateutil 4.0.0 read them as NO dates at all "
                        "(Duncan-Haywood fixtures, 14 nov. 2026)" % (t, freq),
                        "bare MO..SU for DAILY/WEEKLY; ordinals only for "
                        "MONTHLY/YEARLY")
            if (n, wd) not in seen:
                seen.append((n, wd))
        rule["byday"] = seen

    rule["wkst"] = "MO"
    if "WKST" in parts:
        toks = _tokens(parts["WKST"])
        if len(toks) != 1 or toks[0].upper() not in WD:
            raise RecurrenceError("rrule", "date/recurrence: WKST must be a "
                                  "single weekday", "WKST=MO..SU")
        rule["wkst"] = toks[0].upper()
    return rule


def _tokens(val):
    return [t.strip() for t in val.split(",") if t.strip()]


# ---------------------------------------------------------------- engine

def _dim(y, m):
    return calendar.monthrange(y, m)[1]


def _shift_month(y, m, delta):
    tot = y * 12 + (m - 1) + delta
    return tot // 12, tot % 12 + 1


def _nth_weekday(y, m, wdi, n):
    """nth weekday of a month (n>0 from start, n<0 from end); None if absent."""
    if n > 0:
        first = date(y, m, 1)
        d = first + timedelta(days=(wdi - first.weekday()) % 7 + 7 * (n - 1))
    else:
        last = date(y, m, _dim(y, m))
        d = last - timedelta(days=(last.weekday() - wdi) % 7 + 7 * (-n - 1))
    return d if (d.year, d.month) == (y, m) else None


def _month_days(y, m, rule, anchor, skipped, skipped_key):
    """Admitted days for one month window, RFC order BYMONTHDAY→BYDAY;
    invalid dates are DROPPED into `skipped` (§3.3.10 MUST)."""
    dim = _dim(y, m)
    bymod = rule["bymonthday"]
    byday = rule["byday"]
    days = None
    if bymod:
        want = set()
        for n in bymod:
            d = n if n > 0 else dim + 1 + n
            if 1 <= d <= dim:
                want.add(d)
            else:
                skipped.add(skipped_key(y, m))
        days = want
    if byday:
        sel = set()
        for (n, wd) in byday:
            wdi = WD.index(wd)
            if n == 0:
                first = date(y, m, 1)
                d = first + timedelta(days=(wdi - first.weekday()) % 7)
                while d.month == m:
                    sel.add(d.day)
                    d += timedelta(days=7)
            else:
                dd = _nth_weekday(y, m, wdi, n)
                if dd:
                    sel.add(dd.day)
        days = sel if days is None else (days & sel)   # Note 1: BYDAY limits
    if days is None:
        a = anchor
        if a <= dim:
            days = {a}
        else:
            skipped.add(skipped_key(y, m))
            days = set()
    return sorted(days)


def _week_start(d, wkst):
    return d - timedelta(days=(d.weekday() - WD.index(wkst)) % 7)


def _stream(dt, kind, rule):
    """Yield admitted instances in window order (RFC grid), each typed
    like dt (date stays date, datetime stays naive datetime at the
    DTSTART wall time). Invalid calendar dates are DROPPED and recorded
    in rule['skipped'] (§3.3.10 MUST) — MONTHLY/YEARLY only."""
    freq = rule["freq"]
    iv = rule["interval"]
    base = dt.date() if isinstance(dt, datetime) else dt
    anchor_time = dt.time() if isinstance(dt, datetime) else None
    anchor_day = base.day

    def make(d):
        return datetime.combine(d, anchor_time) if anchor_time else d

    if freq == "DAILY":
        wd_sel = {wd for (_n, wd) in rule["byday"]}
        for k in range(_SCAN_LIMIT["DAILY"] + 1):
            cur = base + timedelta(days=iv * k)
            if rule["bymonth"] and cur.month not in rule["bymonth"]:
                continue
            if rule["bymonthday"]:
                dim = _dim(cur.year, cur.month)
                want = {(n if n > 0 else dim + 1 + n)
                        for n in rule["bymonthday"]
                        if 1 <= (n if n > 0 else dim + 1 + n) <= dim}
                if cur.day not in want:
                    continue
            if wd_sel and WD[cur.weekday()] not in wd_sel:
                continue
            yield make(cur)
        return

    if freq == "WEEKLY":
        ws = _week_start(base, rule["wkst"])
        wd_sel = ({wd for (_n, wd) in rule["byday"]} if rule["byday"]
                  else {WD[base.weekday()]})
        for k in range(_SCAN_LIMIT["WEEKLY"] + 1):
            wstart = ws + timedelta(days=7 * iv * k)
            for j in range(7):
                cur = wstart + timedelta(days=j)
                if cur < base:
                    continue
                if WD[cur.weekday()] not in wd_sel:
                    continue
                if rule["bymonth"] and cur.month not in rule["bymonth"]:
                    continue
                yield make(cur)
        return

    skipped = rule.setdefault("skipped", set())
    if freq == "MONTHLY":
        key = lambda yy, mm: "%04d-%02d" % (yy, mm)  # noqa: E731
        for k in range(_SCAN_LIMIT["MONTHLY"] + 1):
            y, m = _shift_month(base.year, base.month, iv * k)
            if rule["bymonth"] and m not in rule["bymonth"]:
                continue
            for day in _month_days(y, m, rule, anchor_day, skipped, key):
                cur = date(y, m, day)
                if cur >= base:
                    yield make(cur)
        return

    # YEARLY
    months = rule["bymonth"] or [base.month]
    ordinals = [(n, wd) for (n, wd) in rule["byday"] if n != 0]
    key = lambda yy, mm: "%04d" % yy                # noqa: E731
    for k in range(_SCAN_LIMIT["YEARLY"] + 1):
        y = base.year + iv * k
        out = []
        if ordinals and not rule["bymonth"] and not rule["bymonthday"]:
            # §3.3.10: an ordinal counts within the YEAR when neither
            # BYMONTH nor BYMONTHDAY narrows the window — the published
            # example FREQ=YEARLY;BYDAY=20MO gives the 20th Monday OF THE
            # YEAR (1997-05-19), not of January. Bare weekdays alongside
            # mean every such weekday in the whole year.
            for (n, wd) in rule["byday"]:
                wdi = WD.index(wd)
                if n == 0:
                    d = date(y, 1, 1)
                    d += timedelta(days=(wdi - d.weekday()) % 7)
                    while d.year == y:
                        out.append(d)
                        d += timedelta(days=7)
                    continue
                jan = date(y, 1, 1)
                if n > 0:
                    d = jan + timedelta(days=(wdi - jan.weekday()) % 7
                                        + 7 * (n - 1))
                else:
                    dec = date(y, 12, 31)
                    d = dec - timedelta(days=(dec.weekday() - wdi) % 7
                                        + 7 * (-n - 1))
                if d.year == y:
                    out.append(d)
        else:
            for m in months:
                for day in _month_days(y, m, rule, anchor_day, skipped, key):
                    out.append(date(y, m, day))
        for d in sorted(out):
            if d >= base:
                yield make(d)
    return


# ---------------------------------------------------------------- public

def run_recurrence(args):
    dt, kind = _parse_instant(args.get("dtstart"))
    parts = _norm_rrule(args.get("rrule"))
    rule = _parse_rule(parts, kind)
    skipped = rule.setdefault("skipped", set())

    max_count = args.get("max_count")
    if max_count is None:
        max_count = CAP
    else:
        if isinstance(max_count, bool) or not isinstance(max_count, int) \
                or max_count < 1:
            raise RecurrenceError("max_count",
                                  "date/recurrence: max_count must be an "
                                  "integer ≥ 1", "1..%d" % CAP)
        max_count = min(max_count, CAP)

    until = rule["until"]
    occ = []
    hard_cap_hit = False
    for cand in _stream(dt, kind, rule):
        if until is not None and cand > until:
            break
        occ.append(cand)
        if rule["count"] is not None and len(occ) >= rule["count"]:
            break
        if len(occ) >= CAP:
            hard_cap_hit = True
            break
        if len(occ) >= max_count:
            break

    if hard_cap_hit:
        bound_by = "cap"
    elif rule["count"] is not None and len(occ) < rule["count"]:
        bound_by = "exhausted"      # scan budget ended short of COUNT
    elif occ and max_count < CAP and rule["count"] is None and \
            until is None and len(occ) == max_count:
        bound_by = "max_count"
    elif rule["count"] is not None:
        bound_by = "count"
    elif until is not None:
        bound_by = "until"
    else:
        bound_by = "cap"

    suffix = "Z" if kind == "datetime-utc" else ""
    occurrences = []
    for i, d in enumerate(occ):
        dd = d.date() if isinstance(d, datetime) else d
        occurrences.append({"n": i + 1, "iso": _iso(d) + suffix,
                            "weekday": WD_NAMES[WD[dd.weekday()]]})

    dtstart_synced = bool(occurrences) and occurrences[0]["iso"] == \
        _iso(dt) + suffix
    never = (not occ) and _admissible(rule) is False

    skipped_out = sorted(skipped)
    out = {
        "freq": rule["freq"],
        "interval": rule["interval"],
        "wkst": rule["wkst"],
        "dtstart": _iso(dt) + suffix,
        "dtstart_kind": kind,
        "rrule_normalized": _canon(rule),
        "count": rule["count"],
        "until": rule["until_raw"],
        "reading": _reading(rule, dt, kind),
        "occurrences": occurrences,
        "returned": len(occurrences),
        "bound_by": "never" if never else bound_by,
        "cap": CAP,
        "truncated_at_cap": hard_cap_hit,
        "dtstart_synced": dtstart_synced,
        "skipped_invalid_dates": skipped_out[:CAP],
        "skipped_truncated": len(skipped_out) > CAP,
        "rules_applied": [
            "DTSTART anchors the grid and is the FIRST occurrence when it "
            "matches the rule — « the DTSTART property value always counts "
            "as the first occurrence » (§3.3.10); the rrule.js off-by-one "
            "class is closed here",
            _ORDER_NOTE,
            _WALL_NOTE,
            "dropped invalid dates never consume a COUNT — the bound "
            "applies to admitted instances only (§3.3.10: they “MUST be "
            "ignored and MUST NOT be counted as part of the recurrence "
            "set”)",
        ],
        "closed_subset": _CLOSED_SUBSET,
    }
    if skipped_out:
        out["skipped_note"] = _DROP_NOTE
    if not dtstart_synced:
        out["sync_note"] = _UNSYNC_NOTE
    if bound_by == "cap" and not never:
        out["cap_note"] = ("the series is INFINITE without COUNT/UNTIL "
                           "(§3.3.10); the engine stops at %d and says so "
                           "— page with UNTIL windows" % CAP)
    if bound_by == "max_count":
        out["cap_note"] = "stopped at the caller's max_count=%d; the " \
                          "series continues (engine cap %d)" % (max_count, CAP)
    if bound_by == "exhausted":
        out["cap_note"] = ("the scan budget (%d windows) ended before "
                           "COUNT was reached — widen with UNTIL windows"
                           % _SCAN_LIMIT[rule["freq"]])
    if never:
        out["never_note"] = ("the rule can NEVER fire: its filters admit "
                             "no instance (e.g. BYMONTH=2;BYMONTHDAY=30, "
                             "or BYDAY=31MO in MONTHLY). The RFC set is "
                             "legitimately empty — we declare it instead "
                             "of hanging or guessing")
    return out


def _admissible(rule):
    """Static never-fire detectors for the closed subset. True = surely
    fires somewhere, False = surely never, None = needs the scan."""
    if rule["byday"]:
        for (n, _wd) in rule["byday"]:
            if rule["freq"] == "MONTHLY" and abs(n) > 5:
                return False
    if rule["bymonthday"]:
        if rule["bymonth"] and all(m == 2 for m in rule["bymonth"]) \
                and all(abs(d) > 29 for d in rule["bymonthday"]):
            return False
    return None


def _iso(d):
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%dT%H:%M:%S")
    return d.isoformat()


def _canon(rule):
    chunks = ["FREQ=" + rule["freq"]]
    if rule["interval"] != 1:
        chunks.append("INTERVAL=%d" % rule["interval"])
    if rule["count"] is not None:
        chunks.append("COUNT=%d" % rule["count"])
    if rule["until_raw"] is not None:
        chunks.append("UNTIL=" + rule["until_raw"])
    if rule["byday"]:
        chunks.append("BYDAY=" + ",".join(
            (("%d" % n) if n else "") + wd for (n, wd) in rule["byday"]))
    if rule["bymonth"]:
        chunks.append("BYMONTH=" + ",".join(str(m) for m in rule["bymonth"]))
    if rule["bymonthday"]:
        chunks.append("BYMONTHDAY=" + ",".join(str(d) for d in
                                               rule["bymonthday"]))
    chunks.append("WKST=" + rule["wkst"])
    return ";".join(chunks)


_FREQ_WORDS = {"DAILY": "day", "WEEKLY": "week", "MONTHLY": "month",
               "YEARLY": "year"}
_MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November",
                "December"]


def _dayth(n):
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return "%d%s" % (n, suf)


def _reading(rule, dt, kind):
    iv = rule["interval"]
    unit = _FREQ_WORDS[rule["freq"]]
    if iv == 1:
        head = "every day" if rule["freq"] == "DAILY" else "every " + unit
    else:
        head = "every %d %ss" % (iv, unit)
    bits = [head]
    if rule["byday"]:
        bits.append("on " + ", ".join(
            (_ord(n) + " " + WD_NAMES[wd]) if n else WD_NAMES[wd]
            for (n, wd) in rule["byday"]))
    if rule["bymonthday"]:
        bits.append("on day(s) " + ", ".join(
            ("%d from month end" % -d) if d < 0 else str(d)
            for d in rule["bymonthday"]))
    if rule["bymonth"]:
        bits.append("in " + ", ".join(_MONTH_NAMES[m - 1]
                                      for m in rule["bymonth"]))
    if not rule["byday"] and not rule["bymonthday"]:
        if rule["freq"] == "WEEKLY":
            bits.append("on " + WD_NAMES[WD[dt.weekday()]])
        elif rule["freq"] == "MONTHLY":
            bits.append("on the %s of the month" % _dayth(dt.day))
        elif rule["freq"] == "YEARLY":
            bits.append("on the %s of %s" % (_dayth(dt.day),
                                             _MONTH_NAMES[dt.month - 1]))
    bits.append("starting " + _iso(dt))
    if rule["count"]:
        bits.append("for %d occurrences" % rule["count"])
    elif rule["until_raw"]:
        bits.append("until %s inclusive" % rule["until_raw"])
    else:
        bits.append("forever (capped at %d)" % CAP)
    if kind == "date":
        bits.append("all-day")
    return ", ".join(bits)


def _ord(n):
    if n == -1:
        return "last"
    if n < 0:
        return "%dth-from-end" % (-n)
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, "%dth" % n)
