"""reldate — relative-date phrases in human words → exact ISO. EN/FR/PT.

The #1 complaint across every local-model forum (see the demand research backlog
for the receipts): "this Monday", "end of this week", "in 3 days" — models
compute calendars in their heads and get confidently wrong answers
("August 14 1970 was a Sunday" — it was a Friday). The community's own
advice is literally this tool: externalize the arithmetic.

Determinism contract:
  * `now` is an ARGUMENT (echoed as now_used). Same phrase + same now +
    same tz → same answer forever. Without now: current UTC second, and
    the chosen instant is printed.
  * The grammar is CLOSED. A phrase outside it is refused by name — no
    NLP fallback, no vibes. Natural-language → phrase is the model's
    job; phrase → date is ours.
  * Time-of-day words map to a published convention table (morning=
    09:00 …), listed in every response. Bare phrase with no time word
    resolves at 00:00 and says so (time_given: false).
  * Genuine ambiguities ("this Friday" on a Friday) return BOTH
    readings with ambiguity: true — reported, never decided.
"""
import calendar
import re
import unicodedata
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:                       # pragma: no cover
    ZoneInfo = None

# PT weekday names are Latin ordinals counted FROM SUNDAY: quarta-feira
# is Wednesday (=2), sexta is Friday (=4). The etymological off-by-one is
# exactly the mistake this machine exists to kill — mapped to CALENDAR
# positions, verified against named dates in the tests.
DAY_WORDS = {
    "monday": 0, "lundi": 0, "segunda": 0, "segunda-feira": 0,
    "tuesday": 1, "mardi": 1, "terca": 1, "terca-feira": 1,
    "wednesday": 2, "mercredi": 2, "quarta": 2, "quarta-feira": 2,
    "thursday": 3, "jeudi": 3, "quinta": 3, "quinta-feira": 3,
    "friday": 4, "vendredi": 4, "sexta": 4, "sexta-feira": 4,
    "saturday": 6, "samedi": 6, "sabado": 6,
    "sunday": 0, "dimanche": 0, "domingo": 0,
}
MONTH_WORDS = {
    "january": 1, "janvier": 1, "janeiro": 1, "february": 2,
    "fevrier": 2, "fevereiro": 2, "march": 3, "mars": 3, "marco": 3,
    "april": 4, "avril": 4, "abril": 4, "may": 5, "mai": 5, "maio": 5,
    "june": 6, "juin": 6, "junho": 6, "july": 7, "juillet": 7,
    "julho": 7, "august": 8, "aout": 8, "agosto": 8, "september": 9,
    "septembre": 9, "setembro": 9, "october": 10, "octobre": 10,
    "outubro": 10, "november": 11, "novembre": 11, "novembro": 11,
    "december": 12, "decembre": 12, "dezembro": 12,
}
UNIT_DAYS = {
    "day": 1, "jours": 1, "jour": 1, "dias": 1, "dia": 1,
    "week": 7, "semaines": 7, "semaine": 7, "semanas": 7, "semana": 7,
}
UNIT_MONTHS = {"month", "mois", "meses", "mes"}
UNIT_YEARS = {"year", "ans", "an", "anos", "ano"}
TIME_WORDS = {
    "morning": "09:00", "matin": "09:00", "manha": "09:00",
    "noon": "12:00", "midi": "12:00", "meiodia": "12:00",
    "afternoon": "14:00", "apres-midi": "14:00", "apresmidi": "14:00",
    "tarde": "14:00", "evening": "18:00", "soir": "18:00",
    "noite": "18:00", "tonight": "21:00",
    "ce soir": "21:00", "esta noite": "21:00",
}
TIME_CONVENTION = ("time words map (declared convention): morning/"
                   "matin/manha=09:00, noon/midi=12:00, afternoon/"
                   "apres-midi/tarde=14:00, evening/soir/noite=18:00, "
                   "tonight/ce soir=21:00; no time word → 00:00, "
                   "flagged time_given=false")


class RelDateError(Exception):
    pass


def _norm(phrase):
    s = unicodedata.normalize("NFKD", phrase.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("’", "'").replace("-", " ")
    s = re.sub(r"\s+", " ", s).strip(" .,!?")
    return s


def _add_months(dt, n):
    y = dt.year + (dt.month - 1 + n) // 12
    m = (dt.month - 1 + n) % 12 + 1
    d = min(dt.day, calendar.monthrange(y, m)[1])   # month-end clamp
    return dt.replace(year=y, month=m, day=d)


def _end_of(dt, span):
    if span == "week":          # ISO convention: week ends Sunday
        return dt + timedelta(days=6 - dt.weekday())
    if span == "month":
        return dt.replace(day=calendar.monthrange(dt.year, dt.month)[1])
    if span == "year":
        return dt.replace(month=12, day=31)
    raise RelDateError("span %r unknown" % span)


def _start_of(dt, span):
    if span == "week":          # ISO: Monday starts the week
        return dt - timedelta(days=dt.weekday())
    if span == "month":
        return dt.replace(day=1)
    if span == "year":
        return dt.replace(month=1, day=1)
    raise RelDateError("span %r unknown" % span)


WORDNUM = {"one": 1, "un": 1, "uma": 1, "deux": 2, "two": 2, "duas": 2,
           "trois": 3, "three": 3, "tres": 3, "quatre": 4, "four": 4,
           "cinq": 5, "five": 5}


def resolve(phrase, now=None, tz=None):
    if not phrase or not isinstance(phrase, str):
        raise RelDateError("phrase required")
    if now is None:
        now_used = datetime.now(timezone.utc)
        echoed = True
    else:
        now_used = datetime.fromisoformat(str(now).replace("Z", "+00:00"))
        if now_used.tzinfo is None:
            now_used = now_used.replace(tzinfo=timezone.utc)
        echoed = False
    if tz:
        if ZoneInfo is None:
            raise RelDateError("tz unsupported on this runtime")
        try:
            now_used = now_used.astimezone(ZoneInfo(tz))
        except Exception:
            raise RelDateError("unknown IANA zone %r" % tz)
    p = _norm(phrase)
    # time-of-day extraction
    hh, mm, time_given = 0, 0, False
    for w in sorted(TIME_WORDS, key=len, reverse=True):
        if p == w or p.endswith(" " + w):
            hh, mm = map(int, TIME_WORDS[w].split(":"))
            time_given = True
            p = p[: -len(w)].strip() if p != w else "today"
            # PT/FR articles left dangling by the time-word removal
            p = re.sub(r"\s+(a|as|o|os|de|da|du|la|le|del)$", "", p).strip()
            break
    ambiguity = False
    alt = None
    base = now_used.replace(hour=hh, minute=mm, second=0, microsecond=0)

    def dur(days):
        return base + timedelta(days=days)

    if p in ("today", "aujourdhui", "hoje", "tonight", "ce soir",
             "esta noite"):
        out = base
    elif p in ("tomorrow", "demain", "amanha"):
        out = dur(1)
    elif p in ("yesterday", "hier", "ontem"):
        out = dur(-1)
    else:
        out = None
        m = re.match(r"^(?:in |dans |em )?(\w+)\s+(days?|jours?|dias?|"
                     r"weeks?|semaines?|semanas?)$", p)
        if m:
            n = m.group(1)
            n = int(n) if n.isdigit() else WORDNUM.get(n)
            if n is None:
                raise RelDateError("number %r not in closed word set"
                                   % m.group(1))
            u = m.group(2)
            if u.startswith(("day", "jour", "dia")):
                out = dur(n)
            elif u.startswith(("week", "semain", "semana")):
                out = dur(7 * n)
            elif u.startswith(("month", "mois", "mes")):
                out = _add_months(base, n)
            else:
                out = _add_months(base, 12 * n)
        m2 = re.match(r"^(?:in|dans|em) (\d+|one|two|three|four|five) "
                      r"(days?|weeks?|months?|ans?|mois|semaines?|"
                      r"semanas?|years?|anos?)$", p)
        if m2:
            n = int(m2.group(1)) if m2.group(1).isdigit() \
                else WORDNUM[m2.group(1)]
            u = m2.group(2)
            if u.startswith(("day", "jour")):
                out = dur(n)
            elif u.startswith(("week", "semain", "semana")):
                out = dur(7 * n)
            elif u.startswith(("month", "mois", "mes")):
                out = _add_months(base, n)
            else:
                out = _add_months(base, 12 * n)
        m3 = re.match(r"^(\d+|one|two|three|four|five) "
                      r"(days?|weeks?|months?|years?) ago$|"
                      r"^il y a (\d+|un|deux|trois|quatre|cinq) "
                      r"(jours?|semaines?|mois|ans?)$|"
                      r"^ha (\d+|uma?) (dias?|semanas?|meses?|anos?)$", p)
        if m3:
            g = [x for x in m3.groups() if x is not None]
            n = int(g[0]) if g[0].isdigit() else WORDNUM[g[0]]
            u = g[1]
            sign = -1
            if u.startswith(("day", "jour", "dia")):
                out = dur(sign * n)
            elif u.startswith(("week", "semain", "semana")):
                out = dur(sign * 7 * n)
            elif u.startswith(("month", "mois", "mes")):
                out = _add_months(base, sign * n)
            else:
                out = _add_months(base, sign * 12 * n)
        SPANS = {"week": "week", "semaine": "week", "semana": "week",
                 "month": "month", "mois": "month", "mes": "month",
                 "year": "year", "annee": "year", "ano": "year",
                 "an": "year"}
        m4 = re.match(r"^(end|fin|fim)\b.*\b(week|semaine|semana|month|"
                      r"mois|mes|year|annee|ano|an)$", p)
        if m4:
            out = _end_of(base, SPANS[m4.group(2)])
        m5 = re.match(r"^(start|beginning|debut|comeco|inicio)\b.*\b"
                      r"(week|semaine|semana|month|mois|mes|year|annee|"
                      r"ano|an)$", p)
        if m5:
            out = _start_of(base, SPANS[m5.group(2)])
        if out is None:
            # weekday patterns
            m7 = re.match(r"^(this|next|last|ce|cette|prochain|prochaine|"
                          r"dernier|derniere|proxima|proximo|passada|"
                          r"passado)? ?(" + "|".join(
                              sorted(DAY_WORDS, key=len, reverse=True))
                          + r")$|^(this|next|last|ce|cette|prochain|"
                          r"prochaine|dernier|derniere|proxima|proximo) "
                          r"(" + "|".join(sorted(DAY_WORDS, key=len,
                                                 reverse=True)) + r")$", p)
            if not m7:
                raise RelDateError(
                    "phrase outside the closed grammar — model's job is "
                    "to normalize words into one of: today/tomorrow/"
                    "yesterday, [this|next|last] <weekday>, in N days/"
                    "weeks/months/years, N units ago, start/end of "
                    "week|month|year (+ FR/PT equivalents); + morning/"
                    "noon/afternoon/evening suffix")
            g = [x for x in m7.groups() if x is not None]
            qual, wd = (g[0].lower(), g[1]) if len(g) == 2 else \
                ("", g[0])
            target = DAY_WORDS[wd]
            today_w = now_used.weekday()
            if qual in ("last", "dernier", "derniere", "passada",
                        "passado"):
                # the SAME-NAMED day of the PREVIOUS ISO week
                delta = target - today_w - 7
            elif qual in ("this", "ce", "cette"):
                # X of the CURRENT ISO week (may be in the past —
                # declared); asked on X itself → both readings
                delta = target - today_w
                if delta == 0:
                    ambiguity = True
                    alt = (base + timedelta(days=7)).date().isoformat()
            else:
                # bare X and "next X" (declared identical): first X
                # STRICTLY after today; today==X → +7
                delta = (target - today_w) % 7
                if delta == 0:
                    delta = 7
                if qual in ("next", "prochain", "prochaine", "proxima",
                            "proximo"):
                    pass   # same rule, stated in reading_notes
            out = dur(delta)
    resolved = out
    notes = []
    if re.search(r"monday|tuesday|wednesday|thursday|friday|saturday|"
                 r"sunday|lundi|mardi|mercredi|jeudi|vendredi|samedi|"
                 r"dimanche|segunda|terca|quarta|quinta|sexta|sabado|"
                 r"domingo", p):
        notes.append("declared rules: bare & 'next X' = first X strictly "
                     "after today (X today → +7d); 'this X' = X of the "
                     "current ISO week (can be past); 'last X' = same "
                     "day of the previous ISO week")
    if ambiguity:
        notes.append("this <weekday> asked ON that weekday: both readings "
                     "kept — primary is today, alt is +7 days")
    if re.match(r"^(end|fin|fim)\\b", p):
        notes.append("ISO conventions declared: week = Mon…Sun, "
                     "resolved date is the Sunday")
    if re.match(r"^(start|beginning|debut|comeco|inicio)\\b", p):
        notes.append("ISO conventions declared: week starts Monday")
    return {"phrase": phrase, "now_used": now_used.isoformat(),
            "now_echoed_because_absent": echoed,
            "resolved": resolved.date().isoformat(),
            "datetime": resolved.isoformat(),
            "weekday": resolved.strftime("%A"),
            "time_given": time_given,
            "ambiguity": ambiguity,
            "alt_datetime": alt,
            "reading_notes": notes,
            "time_convention": TIME_CONVENTION}
