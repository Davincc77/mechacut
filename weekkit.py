"""weekkit — /api/v1/date/week : la semaine ISO aller-retour, avec le
piège %Y-%W%V démontré sur la date DEMANDÉE.

La douleur mesurée (nov. 2026) : « le 1-janv.-2027, %Y donne 2027 mais
%V donne la semaine 53 — de 2026 ; le résultat "2027-W53" EST UNE
SEMAINE QUI N'EXISTE PAS. Ce bug remonte une fois l'an, début janvier,
dans du code qui a tourné onze mois sans broncher » (filecraftpro,
table strftime). redbison donne le vecteur publié : 3-janv.-2021 →
"2021-W53" faux, correct "2020-W53". forum SQLite : « sans %G, %V est
inutile » ; blog rebased : le THÉORÈME — une année a 53 semaines ISO
ssi elle contient 53 jeudis, soit 71 années sur chaque cycle de 400.

Ce module ne committe AUCUNE table de semaines : le compte de semaines
d'une année est DÉDUIT du théorème (jour de Jan-1 + bissextile), les
bornes de W01/W53 sont calculées par datetime.fromisocalendar/isocalendar
(implémentation de la spec ISO 8601), et les conventions concurrentes
(Excel WEEKNUM 1/2/21, %U, %W) sont rendues CÔTE À CÔTE — jamais un
seul nombre confiant. La semaine demandée qui n'existe pas est REFUSÉE
avec la raison du théorème nommée, pas un 500 muet.
"""

import re
from datetime import date, timedelta

_WEEKDAY = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday"]

_EXPECTED = {
    "date": "an ISO calendar date 'YYYY-MM-DD', e.g. '2027-01-03'",
    "iso": "an ISO week date 'YYYY-Www-d' (day optional), e.g. "
           "'2026-W01-3' or '2026-W53' — the week-numbering year is "
           "the ISO year, NOT the calendar year",
    "year": "an ISO week-numbering year, e.g. '2026' — answers: how "
            "many weeks, W01 bounds, does W53 exist, why",
}


class WeekError(ValueError):
    def __init__(self, field, message, expected=None):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected or _EXPECTED.get(field, "")


def _isleap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _weeks_in(iso_year):
    """THÉORÈME (forum SQLite / blog rebased) : 53 semaines ssi le nom
    contient 53 jeudis ⟺ Jan-1 jeudi, ou Jan-1 mercredi ET bissextile.
    Zéro table : deux nombres calendaires, une soustraction."""
    j1 = date(iso_year, 1, 1)
    if j1.weekday() == 3 or (j1.weekday() == 2 and _isleap(iso_year)):
        return 53
    return 52


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise WeekError(field, "missing or empty (a JSON number is "
                        "refused — pass the string)")
    return value.strip()


def _parse_cal(t, field):
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", t)
    if not m:
        raise WeekError(field, "strict ISO 'YYYY-MM-DD', got %r" % t)
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError as exc:
        raise WeekError(field, "impossible date %r (%s)" % (t, exc))


def _theorem_reason(iso_year):
    j1 = date(iso_year, 1, 1)
    wd = _WEEKDAY[j1.weekday()]
    leap = "leap" if _isleap(iso_year) else "common"
    if _weeks_in(iso_year) == 53:
        return ("%s is a %s year starting %s → it contains 53 Thursdays "
                "→ 53 ISO weeks" % (iso_year, leap, wd))
    return ("%s is a %s year starting %s (W53 needs Jan-1 Thursday, or "
            "Wednesday in a leap year) → 52 ISO weeks" %
            (iso_year, leap, wd))


# ---------------------------------------------------------------- modes

def _week_conventions(dt):
    """Concurrentes publiées, rendues côte à côte (table wcalendar).
    Implémentation VERBALE des définitions : « %U/%W : jours de l'année
    AVANT le premier dimanche/lundi = semaine 0 ; chaque semaine commence
    à ce jour » ; « Excel WEEKNUM : la semaine partielle tenant Jan-1
    est la semaine 1 ». Vecteur publié GNU date : 2001-01-01 (lundi) →
    %U=00, %W=01."""
    jan1 = date(dt.year, 1, 1)
    doy = dt.timetuple().tm_yday
    su0 = (jan1.weekday() + 1) % 7              # Sunday=0
    first_sun = 1 + (7 - su0) % 7
    first_mon = 1 + (7 - jan1.weekday()) % 7
    strftime_u = 0 if doy < first_sun else 1 + (doy - first_sun) // 7
    strftime_w = 0 if doy < first_mon else 1 + (doy - first_mon) // 7
    excel_weeknum_1 = 1 if doy < first_sun else 2 + (doy - first_sun) // 7
    excel_weeknum_2 = 1 if doy < first_mon else 2 + (doy - first_mon) // 7
    return {
        "excel_weeknum_1": excel_weeknum_1,
        "excel_weeknum_2_NOT_ISO": excel_weeknum_2,
        "strftime_%U_sunday0based": strftime_u,
        "strftime_%W_monday0based": strftime_w,
        "first_sunday_doy": first_sun,
        "first_monday_doy": first_mon,
        "note": "Excel counts the partial week holding Jan-1 as 1; "
                "strftime counts days BEFORE the first weekday as 0; "
                "both differ from ISO near January — WEEKNUM(d,2) is "
                "Monday-start, NOT ISO (use 21/ISOWEEKNUM)",
    }


def _trap(dt, iy, iw):
    """La chaîne fausse %Y-W%V vs la juste %G-W%V, sur CETTE date."""
    buggy = "%04d-W%02d" % (dt.year, iw)
    correct = "%04d-W%02d" % (iy, iw)
    if dt.year == iy:
        return {"buggy_y_w_v": buggy, "correct_g_w_v": correct,
               "buggy_week_exists_in_printed_year": True,
               "risky": False,
               "note": "calendar year == ISO year here — %Y-W%V "
                       "coincidentally prints right; the bug surfaces "
                       "only near January (filecraftpro)"}
    exists = iw <= _weeks_in(dt.year)
    why = _theorem_reason(dt.year)
    return {
        "buggy_y_w_v": buggy,
        "correct_g_w_v": correct,
        "buggy_week_exists_in_printed_year": exists,
        "risky": True,
        "note": ("concatenating the GREGORIAN year with the ISO week "
                 "prints %r: %s" % (
                     buggy,
                     "a week that DOES NOT EXIST in %d (%s)" %
                     (dt.year, why) if not exists else
                     "the WRONG week of %d — it sorts wrong, silently "
                     "(PostgreSQL #13845, Snowflake policy bug class)" %
                     dt.year)),
    }


def _from_date(t):
    dt = _parse_cal(t, "date")
    iy, iw, idd = dt.isocalendar()
    start = dt - timedelta(days=idd - 1)
    end = start + timedelta(days=6)
    return {
        "mode": "date",
        "date": dt.isoformat(),
        "weekday": _WEEKDAY[dt.weekday()],
        "iso": {
            "iso_year": iy,
            "iso_week": iw,
            "iso_day": idd,
            "week_date": "%04d-W%02d-%d" % (iy, iw, idd),
            "week_start": start.isoformat(),
            "week_end": end.isoformat(),
            "iso_year_matches_calendar_year": iy == dt.year,
            "weeks_in_iso_year": _weeks_in(iy),
            "why_weeks": _theorem_reason(iy),
        },
        "us_conventions": _week_conventions(dt),
        "y_vs_g_trap": _trap(dt, iy, iw),
        "verdict": "%s is %s" % (dt.isoformat(),
                                 "%04d-W%02d-%d" % (iy, iw, idd)),
    }


_ISO_RE = re.compile(r"^(\d{4})-W(\d{2})(?:-([1-7]))?$")


def _from_iso(t):
    t = _text(t, "iso")
    m = _ISO_RE.match(t.upper().replace("−", "-"))
    if not m:
        raise WeekError(
            "iso", "format is 'YYYY-Www-d' with day 1..7 optional, "
                   "got %r" % t,
            _EXPECTED["iso"])
    iy, iw = int(m.group(1)), int(m.group(2))
    if iw < 1 or iw > 53:
        raise WeekError("iso", "week number %d is outside 01..53 — "
                        "and no ISO year has more than 53 weeks" % iw)
    weeks = _weeks_in(iy)
    if iw > weeks:
        hint = ""
        if iw == 53 and _weeks_in(iy - 1) == 53:
            hint = (" — the week you probably mean is %d-W53 (the ISO "
                    "year of the late-Dec/early-Jan days is %d, not %d):"
                    " this exact token is the %%Y-%%V concatenation "
                    "artifact" % (iy - 1, iy - 1, iy))
        raise WeekError(
            "iso",
            "%s IS A WEEK THAT DOES NOT EXIST: %s%s. If a calendar "
            "date was meant, pass 'date' instead" % (
                t, _theorem_reason(iy), hint),
            _EXPECTED["iso"])
    day = int(m.group(3)) if m.group(3) else None
    out = {"mode": "iso", "input": t,
           "iso_year": iy, "iso_week": iw,
           "weeks_in_iso_year": weeks, "why_weeks": _theorem_reason(iy)}
    if day is None:
        monday = date.fromisocalendar(iy, iw, 1)
        sunday = date.fromisocalendar(iy, iw, 7)
        out.update({
            "week_start": monday.isoformat(),
            "week_end": sunday.isoformat(),
            "days": [(monday + timedelta(days=i)).isoformat()
                     for i in range(7)],
            "verdict": "%s = %s .. %s (%d-day week of ISO year %d)" % (
                t, monday.isoformat(), sunday.isoformat(), 7, iy),
        })
    else:
        dt = date.fromisocalendar(iy, iw, day)
        out.update({
            "iso_day": day,
            "date": dt.isoformat(),
            "weekday": _WEEKDAY[dt.weekday()],
            "us_conventions": _week_conventions(dt),
            "y_vs_g_trap": _trap(dt, iy, iw),
            "verdict": "%s = %s (%s)" % (t, dt.isoformat(),
                                         _WEEKDAY[dt.weekday()]),
        })
    return out


def _from_year(t):
    t = _text(t, "year")
    if not re.match(r"^\d{1,4}$", t):
        raise WeekError("year", "digits only, 1..9999, got %r" % t)
    y = int(t)
    if not 1 <= y <= 9999:
        raise WeekError("year", "year must be 1..9999, got %s" % y)
    weeks = _weeks_in(y)
    w01 = date.fromisocalendar(y, 1, 1)
    wlast_start = date.fromisocalendar(y, weeks, 1)
    wlast_end = wlast_start + timedelta(days=6)
    jan_in_prev = [(date(y, 1, i), date(y, 1, i).isocalendar()[0])
                   for i in range(1, 8)]
    jan_in_prev = [d.isoformat() for d, iy in jan_in_prev
                   if iy == y - 1]
    dec_in_next = [(date(y, 12, i), date(y, 12, i).isocalendar()[0])
                   for i in range(25, 32)]
    dec_in_next = [d.isoformat() for d, iy in dec_in_next
                   if iy == y + 1]
    prev53 = next53 = None
    for k in range(1, 8):
        if prev53 is None and _weeks_in(y - k) == 53:
            prev53 = y - k
        if next53 is None and _weeks_in(y + k) == 53:
            next53 = y + k
        if prev53 is not None and next53 is not None:
            break
    return {
        "mode": "year",
        "year": y,
        "weeks": weeks,
        "has_w53": weeks == 53,
        "why": _theorem_reason(y),
        "w01": {"start": w01.isoformat(),
                "end": (w01 + timedelta(days=6)).isoformat()},
        "w_last": {"week": weeks,
                   "start": wlast_start.isoformat(),
                   "end": wlast_end.isoformat()},
        "days_of_january_in_previous_iso_year": jan_in_prev,
        "days_of_december_in_next_iso_year": dec_in_next,
        "neighbouring_53_week_years": {"previous": prev53,
                                       "next": next53},
        "verdict": "ISO year %d has %d weeks — %s" % (y, weeks,
                                                      _theorem_reason(y)),
    }


PLATFORM_NOTES = {
    "postgresql": "to_char(d, 'IYYY-\"W\"IW') — pair IW with the ISO "
                  "year IYYY; combining YYYY with IW is the fatal "
                  "concatenation (PG list bug #13845)",
    "mysql_mariadb": "YEARWEEK(d, 3); bare WEEK(d) follows server "
                     "default_week_format (usually 0 → 0..53)",
    "bigquery": "EXTRACT(ISOWEEK) with EXTRACT(ISOYEAR)",
    "snowflake": "WEEKISO() — WEEK() answers to session parameter "
                 "WEEK_OF_YEAR_POLICY and drifts per session",
    "excel_sheets": "ISOWEEKNUM(d) or WEEKNUM(d, 21) — WEEKNUM(d, 2) "
                    "is Monday-start-Jan-1, NOT ISO",
    "python": "d.isocalendar() / strftime('%G-W%V') — '%Y-W%V' "
              "breaks every January (filecraftpro)",
    "javascript": "Temporal weekOfYear + weekOfWeekbasedYear; legacy "
                  "Date math must stay in UTC or a DST 23-hour day "
                  "rounds the week wrong (wcalendar)",
}


def run_week(args):
    given = [k for k in ("date", "iso", "year")
             if args.get(k) is not None and str(args.get(k)).strip()]
    if len(given) != 1:
        raise WeekError(
            given[0] if given else "date",
            "exactly one of 'date' | 'iso' | 'year' — never two, never "
            "zero (the mode is not guessed)",
            "pass 'date' (YYYY-MM-DD), 'iso' (YYYY-Www-d) or 'year' "
            "(YYYY) — one at a time")
    k = given[0]
    if k == "date":
        out = _from_date(args["date"])
    elif k == "iso":
        out = _from_iso(args["iso"])
    else:
        out = _from_year(args["year"])
    out["platform_notes"] = PLATFORM_NOTES
    out["scope_note"] = [
        "ISO 8601 only for the 'iso' path: the week-numbering year is "
        "not the calendar year; the week-1 rule is 'the week holding "
        "Jan-4 / the first Thursday'",
        "US/Excel conventions are REPORTED beside ISO, never chosen "
        "for the caller — a KW-53 from a German provider and a 'week "
        "2' from an American sheet can name the same seven days",
        "no embedded week tables: the 53-week answer is the theorem "
        "(Jan-1 weekday + leap rule), the bounds are ISO-8601 "
        "arithmetic",
    ]
    return out
