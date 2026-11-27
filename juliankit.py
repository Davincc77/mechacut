"""juliankit — bundle 135 (admission 27-11, registre L24, reçu 56dc427d).

Conversion julian <-> gregorian par le nombre de jours julien (JDN),
le pont entier partagé par les deux calendriers. date_calc refuse
calendar=julian PAR SON NOM et désigne ce contrat (dates.py, B16 :
« a true julian<->gregorian conversion is a different contract ») —
ce foyer est celui qu'il nomme.

Algorithmes publiés, entiers uniquement (Meeus, Astronomical
Algorithms ch. 7 ; Wikipedia « Julian day number »). Échelle
proleptique des deux côtés de 1582, DITE ; numérotation astronomique
des années (année 0 = 1er 1 BCE), dite. Table fermée des décalages
centuriels : version + sha déclarées dans la réponse (doctrine 27-11).

Golds tracés depuis l'algorithme publié (triage interne 27-11 :
« golds depuis algo public »), recoupés avec les assertions consignées
du rapport de campagne (COMPIL_RAPPORTS_VAGUE2, section clic 133 :
JDN 0 = julian -4712-01-01 ; décalage 1900-2099 = 13 jours ;
JDN 584283 = grégorien -3113-08-11 = julien -3113-09-06 ;
julien 2012-04-02 + 13 = grégorien 2012-04-15).
"""
import hashlib
import json
import re

CAL_GREG = "gregorian"
CAL_JUL = "julian"
CALENDARS = (CAL_GREG, CAL_JUL)          # ensemble fermé, nommé
YEAR_STARTS = ("jan01", "march25")       # ensemble fermé, nommé
Y_MIN, Y_MAX = -9999, 9999               # bornes fermées, nommées

SCALE = ("proleptic-both-calendars "
         "(astronomical year numbering, year 0 = 1 BCE)")

_DATE_RE = re.compile(r"^(-?\d{1,4})-(\d{2})-(\d{2})$")
_HAS_TIME_RE = re.compile(r"[T/Z]|[ +]\d|\d:")

TABLE_NAME = "julian-gregorian-century-offsets"
TABLE_VERSION = ("v1 (2026-11-27) — dérivée des deux formules JDN "
                 "publiées (Meeus ch. 7 / Wikipedia Julian day number); "
                 "ancres consignées : JDN 0 = julien -4712-01-01, "
                 "JDN 2299161 = grégorien 1582-10-15, "
                 "1900-2099 = 13 jours, JDN 584283 pont maya GMT")
TABLE_RULE = ("offset(era_year) = era_year//100 - era_year//400 - 2, "
              "era_year = astronomical year at the March-to-March "
              "window, proleptic both sides of 1582")
TABLE_SHA256 = hashlib.sha256(json.dumps(
    {"name": TABLE_NAME, "version": TABLE_VERSION,
     "rule": TABLE_RULE}, sort_keys=True,
    separators=(",", ":")).encode()).hexdigest()


class DateKitError(Exception):
    def __init__(self, msg, field):
        super().__init__(msg)
        self.msg, self.field = msg, field


def _leap_greg(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _leap_jul(y):
    return y % 4 == 0


def _month_days(y, m, cal):
    if m == 2:
        return 29 if (_leap_greg(y) if cal == CAL_GREG
                      else _leap_jul(y)) else 28
    return 31 if m in (1, 3, 5, 7, 8, 10, 12) else 30


def jdn_gregorian(y, m, d):
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return (d + (153 * mm + 2) // 5 + 365 * yy + yy // 4
            - yy // 100 + yy // 400 - 32045)


def jdn_julian(y, m, d):
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - 32083


def _tdiv(a, b):
    # division tronquée vers zéro (l'arithmétique des algorithmes
    # publiés, écrite en C ; Python // plans vers -inf — 1 jour de
    # dérive avant l'an 1 sinon, trouvé au traçage)
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def gregorian_from_jdn(j):
    # Hinnant, « civil_from_days » (algorithme publié), JDN - 2440588
    z = j - 2440588 + 719468
    era = _tdiv(z, 146097) if z >= 0 else _tdiv(z - 146096, 146097)
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    d = doy - (153 * mp + 2) // 5 + 1
    m = mp + 3 if mp < 10 else mp - 9
    return y + (1 if m <= 2 else 0), m, d


def julian_from_jdn(j):
    c = j + 32082
    dd = (4 * c + 3) // 1461
    e = c - 1461 * dd // 4
    m = (5 * e + 2) // 153
    d = e - (153 * m + 2) // 5 + 1
    return dd - 4800 + (m + 2) // 12, m + 3 - 12 * ((m + 2) // 12), d


def offset_days(year, month):
    """Décalage grégorien = julien + offset, lu au 1er mars de l'ère
    astro (le pont des siècles : 1582->10, 1700->11, 1800->12,
    1900-2099->13, dit par la table, jamais deviné)."""
    era_year = year if month >= 3 else year - 1
    return era_year // 100 - era_year // 400 - 2


def _fmt(y, m, d):
    return "%04d-%02d-%02d" % (y, m, d)


def _parse_date(s):
    if not isinstance(s, str) or not s.strip():
        raise DateKitError(
            "date: a calendar day as YYYY-MM-DD (astronomical year "
            "numbering, negative years allowed: -0044-03-15)", "date")
    t = s.strip()
    if _HAS_TIME_RE.search(t):
        raise DateKitError(
            "%r is an instant, not a calendar day: this tool converts "
            "civil days between calendars; times and zones belong to "
            "date_parse / date_tz" % s, "date")
    m = _DATE_RE.match(t)
    if not m:
        raise DateKitError(
            "date %r is not YYYY-MM-DD: a bare year is date_edtf_"
            "interval's reduced precision, catalogue forms are "
            "marc008_date_range — here every day is exact in the "
            "calendar you name" % s, "date")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _check_day(y, mo, d, cal, field):
    if not Y_MIN <= y <= Y_MAX:
        raise DateKitError(
            "year %d is outside the closed range -9999..9999 "
            "(astronomical numbering)" % y, field)
    if not 1 <= mo <= 12:
        raise DateKitError("month %02d is not 01..12" % mo, field)
    lim = _month_days(y, mo, cal)
    if not 1 <= d <= lim:
        rule = ("leap years divisible by 4" if cal == CAL_JUL
                else "leap years divisible by 4, except centuries "
                     "not divisible by 400")
        raise DateKitError(
            "%s is not a civil day of the %s calendar: month %02d of "
            "year %d has %d days there (rule: %s)"
            % (_fmt(y, mo, d), cal, mo, y, lim, rule), field)


def _civil_from_jdn(j):
    jy, jm, jd = julian_from_jdn(j)
    gy, gm, gd = gregorian_from_jdn(j)
    return (jy, jm, jd), (gy, gm, gd)


def convert(date=None, calendar=None, year_start=None, jdn=None,
            to_date=None, to_calendar=None):
    applied = []
    if year_start is None:
        year_start = "jan01"
        applied.append("year_start=jan01 (default: year counted from "
                       "1 January)")
    if year_start not in YEAR_STARTS:
        raise DateKitError(
            "year_start=%r is not in the closed set {jan01, march25}: "
            "march25 is the Lady-Day style (English-speaking civil "
            "years to 1752), jan01 the modern one — no other year "
            "opening is modelled" % year_start, "year_start")
    if date is None and jdn is None:
        raise DateKitError(
            "give a calendar day (date + calendar) or a day count "
            "(jdn) — one of the two, never none", "date")
    if date is not None and jdn is not None:
        raise DateKitError(
            "date and jdn are two names for the same day: give one. "
            "jdn is calendar-neutral, so no calendar argument belongs "
            "beside it", "jdn")

    flags = []
    if jdn is not None:
        if isinstance(jdn, bool) or not isinstance(jdn, int):
            raise DateKitError(
                "jdn: an integer Julian Day Number (a day count, no "
                "fraction — Modified JD and instants are not this "
                "contract)", "jdn")
        (jy, jm, jd), (gy, gm, gd) = _civil_from_jdn(jdn)
        if not (Y_MIN <= gy <= Y_MAX and Y_MIN <= jy <= Y_MAX):
            raise DateKitError(
                "jdn %d falls outside the closed civil range "
                "-9999..9999 of this contract" % jdn, "jdn")
        if calendar is not None:
            raise DateKitError(
                "jdn already names the day in both calendars: drop "
                "calendar, or send date instead", "calendar")
        source = "jdn %d" % jdn
        cal_in = None
    else:
        if calendar is None:
            raise DateKitError(
                "calendar: gregorian or julian — REQUIRED, never "
                "guessed. The whole pain of this contract is date_calc "
                "silently ignoring calendar=julian; here the calendar "
                "you mean is the calendar you type", "calendar")
        if calendar not in CALENDARS:
            raise DateKitError(
                "calendar=%r is not in the closed set {gregorian, "
                "julian} (proleptic both sides of 1582, scale said). "
                "date_calc refuses this argument by name and points "
                "here; other calendars are separate contracts, not "
                "synonyms" % calendar, "calendar")
        y, mo, d = _parse_date(date)
        given = _fmt(y, mo, d)
        if year_start == "march25":
            if mo < 3 or (mo == 3 and d < 25):
                y += 1
                flags.append("march25_style: Jan 1 - Mar 24 belongs "
                             "to the NEXT numbered civil year (Lady-"
                             "Day opening, said by the style name)")
            if y >= 1752:
                flags.append("march25_after_1752: the Lady-Day style "
                             "lapsed with the British calendar act of "
                             "1752; the arithmetic still answers, the "
                             "historical usage does not")
        _check_day(y, mo, d, calendar, "date")
        if calendar == CAL_GREG:
            jdn = jdn_gregorian(y, mo, d)
            gy, gm, gd = y, mo, d
            jy, jm, jd = julian_from_jdn(jdn)
            if y == 1582 and mo == 10 and 5 <= d <= 14:
                flags.append(
                    "gregorian_skip_1582: 1582-10-05..14 were never "
                    "civil days where the reform landed — this date "
                    "exists PROLEPTICALLY only, scale said, not "
                    "refused")
        else:
            jdn = jdn_julian(y, mo, d)
            jy, jm, jd = y, mo, d
            gy, gm, gd = gregorian_from_jdn(jdn)
        source = {"date": given, "calendar": calendar}
        cal_in = calendar

    off = offset_days(gy, gm)
    diff_days = None
    if to_date is not None:
        if jdn is not None and date is None and to_calendar is None:
            raise DateKitError(
                "to_date beside a bare jdn needs to_calendar too (the "
                "other side has no calendar to inherit)",
                "to_calendar")
        if to_calendar is None:
            to_calendar = cal_in
            applied.append("to_calendar=%s (inherited from calendar)"
                           % cal_in)
        if to_calendar not in CALENDARS:
            raise DateKitError(
                "to_calendar=%r is not in the closed set {gregorian, "
                "julian}" % to_calendar, "to_calendar")
        ty, tmo, td = _parse_date(to_date)
        _check_day(ty, tmo, td, to_calendar, "to_date")
        tjdn = (jdn_gregorian(ty, tmo, td) if to_calendar == CAL_GREG
                else jdn_julian(ty, tmo, td))
        diff_days = tjdn - jdn

    return {
        "source": source,
        "jdn": jdn,
        "gregorian": _fmt(gy, gm, gd),
        "julian": _fmt(jy, jm, jd),
        "offset_days": off,
        "offset_meaning": "gregorian civil day = julian civil day + "
                          "offset_days, for the same day",
        "year_start": year_start,
        "scale": SCALE,
        "table": {"name": TABLE_NAME, "version": TABLE_VERSION,
                  "rule": TABLE_RULE, "sha256": TABLE_SHA256},
        "flags": flags,
        "diff_days": diff_days,
        "applied_defaults": applied,
    }
