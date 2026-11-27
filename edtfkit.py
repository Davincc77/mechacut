"""edtfkit — bundle 132 (vague Grok 2, amas dates, arbitrage Vince 27-11).

Trois grammaires FERMEES, un seul foyer :
  parse_edtf      ISO 8601-2 niveau 0 + selecteurs niveau 1 nommes (~ ? X ..)
  interval_within containment de deux intervalles donnes ; une borne
                  ouverte est NOMMEE, jamais la sentinelle 21001231 des
                  finding aids (14 faux CONTRADICTED de Gate)
  marc008_range   LOC MARC21 008/06-14, table fermee de l'edition
                  2026-05-27 (source hashee dans les tests)

Loi de la maison : hors de la scope fermee, refus PAR SON NOM ; une
precision reduite est DITE (earliest/latest + precision), jamais forcee
en un instant ; l'echelle est proleptic-Gregorian, dite (B16, 1.51.0).
"""
import re
from calendar import monthrange
from datetime import date

SCOPE_EDTF = ("ISO 8601-2 level 0 plus the named level-1 selectors: "
              "~ ? X and the open side ..")
SCALE = "proleptic-gregorian"
_UNDATED = ("", "uuuu", "####", None)


class DateKitError(Exception):
    def __init__(self, msg, field):
        super().__init__(msg)
        self.msg, self.field = msg, field


_ELEM = re.compile(r"^(\d[\dX]{3}(?:-[0-1][\dX](?:-[0-3][\dX])?)?)"
                   r"(\?~|~\?|[?~])?$")


def _span(elem):
    """'198X' -> ('1980-01-01','1989-12-31','year'). X = chiffre non
    specifie : borne basse 0, haute 9, precision dite. Le mois suit la
    grammaire ISO stricte : 0X -> 01..09, 1X -> 10..12 (12 max)."""
    ys = elem[:4]
    y0 = int("".join("0" if c == "X" else c for c in ys))
    y1 = int("".join("9" if c == "X" else c for c in ys))
    unspecified = "X" in ys
    parts = elem.split("-")
    if len(parts) == 1:
        return ("%04d-01-01" % y0, "%04d-12-31" % y1, "year", unspecified)
    ms = parts[1]
    if ms[0] == "X":
        m0, m1 = 1, 12
        unspecified = True
    elif ms[1] == "X":
        m0, m1 = int(ms[0]) * 10 + 1, min(12, int(ms[0]) * 10 + 9)
        unspecified = True
    else:
        m0 = m1 = int(ms)
    if len(parts) == 2:
        return ("%04d-%02d-01" % (y0, m0),
                "%04d-%02d-%02d" % (y1, m1, monthrange(y1, m1)[1]),
                "month", unspecified)
    ds = parts[2]
    if ds[0] == "X":
        d0, d1 = 1, monthrange(y1, m1)[1] if m0 == m1 else 31
        unspecified = True
    elif ds[1] == "X":
        d0 = int(ds[0]) * 10 + 1
        d1 = min(monthrange(y1, m1)[1], int(ds[0]) * 10 + 9)
        unspecified = True
    else:
        d0 = d1 = int(ds)
    return ("%04d-%02d-%02d" % (y0, m0, d0),
            "%04d-%02d-%02d" % (y1, m1, d1), "day", unspecified)


def _side(p, label):
    if p == "..":
        return None, [], False
    if p.startswith("y") or p.startswith("-"):
        raise DateKitError(
            "the y-form (years before the common era) is out of the "
            "closed scope (%s)" % SCOPE_EDTF, label)
    m = _ELEM.match(p)
    if not m:
        raise DateKitError(
            "not EDTF under the closed grammar (%s): %r — seasons, "
            "quarters, time-of-day and choice-points are separate "
            "contracts, not synonyms" % (SCOPE_EDTF, p), label)
    quals = []
    suf = m.group(2) or ""
    if "?" in suf:
        quals.append("uncertain")
    if "~" in suf:
        quals.append("approximate")
    return m.group(1), quals, False


def parse_edtf(text, label="text"):
    t = str(text or "").strip()
    if not t:
        raise DateKitError("empty text: this tool parses; it never "
                           "invents", label)
    if t in ("uuuu", "####"):
        raise DateKitError("this is the MARC unknown, not EDTF — the "
                           "marc008 tool reads it", label)
    interval = "/" in t
    if interval:
        parts = t.split("/")
        if len(parts) != 2:
            raise DateKitError("an EDTF interval is exactly two sides",
                               label)
        if parts[0] == ".." and parts[1] == "..":
            raise DateKitError("an interval open on BOTH sides states "
                               "nothing", label)
    else:
        parts = [t]
        if parts[0] == "..":
            raise DateKitError("alone, .. is not a date", label)
    quals = []
    sides = []
    for p in parts:
        base, qs, _ = _side(p, label)
        sides.append(base)
        for q in qs:
            if q not in quals:
                quals.append(q)
    known = [s for s in sides if s]
    any_x = any("X" in s for s in known)
    if any_x and "unspecified" not in quals:
        quals.append("unspecified")
    if not interval:
        e, l, prec, _ = _span(known[0])
        return {"earliest": e, "latest": l, "precision": prec,
                "qualifiers": quals, "interval": False,
                "open_start": False, "open_end": False, "scale": SCALE}
    if sides[0] is None:
        e = None
        l, _, _, _ = _span(sides[1])
        l = _span(sides[1])[1]
    elif sides[1] is None:
        e = _span(sides[0])[0]
        l = None
    else:
        e = _span(sides[0])[0]
        l = _span(sides[1])[1]
    if e and l and e > l:
        raise DateKitError(
            "the interval is inverted (%s after %s) — fix the source; "
            "the gate will not silently reorder it"
            % (parts[1], parts[0]), label)
    return {"earliest": e, "latest": l, "precision": "interval",
            "qualifiers": quals, "interval": True,
            "open_start": sides[0] is None, "open_end": sides[1] is None,
            "scale": SCALE}


def _d(s):
    return date(int(s[:4]), int(s[5:7]), int(s[8:10])) if s else None


def interval_within(outer, inner):
    for side, label in ((outer, "outer"), (inner, "inner")):
        if str(side or "").strip() in _UNDATED:
            return {"verdict": "UNDATED", "gap_days": None,
                    "child_open_end": False, "parent_open_end": False,
                    "scale": SCALE}
    a = parse_edtf(outer, "outer")
    b = parse_edtf(inner, "inner")
    ae, al = _d(a["earliest"]), _d(a["latest"])
    be, bl = _d(b["earliest"]), _d(b["latest"])
    flags = {"child_open_end": bool(b["open_end"]),
             "parent_open_end": bool(a["open_end"])}
    starts_before_days = (ae - be).days if (ae and be and be < ae) else 0
    ends_after = bool(al) and (bl is None or bl > al)
    ends_after_days = None if (bl is None and al) else (
        (bl - al).days if (al and bl and bl > al) else 0)
    if ends_after and starts_before_days and ends_after_days:
        v, gap = "OUTSIDE_BOTH", max(starts_before_days, ends_after_days)
    elif ends_after:
        v, gap = "ENDS_AFTER", ends_after_days
    elif starts_before_days:
        v, gap = "STARTS_BEFORE", starts_before_days
    else:
        v, gap = "INSIDE", 0
    return {"verdict": v, "gap_days": gap, "scale": SCALE, **flags}


MARC_TYPES = {
    "b": "no dates given; B.C. date involved",
    "c": "continuing resource currently published",
    "d": "continuing resource ceased publication",
    "e": "detailed date",
    "i": "inclusive dates of collection",
    "k": "range of years of bulk of collection",
    "m": "multiple dates",
    "n": "dates unknown",
    "p": "distribution/production dates different",
    "q": "questionable date",
    "r": "reprint/reissue and original",
    "s": "single known/probable date",
    "t": "publication and copyright dates",
    "u": "continuing resource status unknown",
    "|": "no attempt to code",
}
_ROLES = {"r": {"date1": "reprint", "date2": "original"},
          "p": {"date1": "distribution", "date2": "production"},
          "t": {"date1": "publication", "date2": "copyright"}}
_DATE_CH = re.compile(r"^[\d#u|]{4}$")


def _year_span(s, label):
    """'19uu' -> (1900,1999) ; '197u' -> (1970,1979) ; '####' -> None.
    Le fill melange est ILLEGAL (LOC) — refuse, nomme, jamais rempli."""
    if s in ("####", "||||"):
        return None, None
    if "|" in s:
        raise DateKitError(
            "fill (|) must occupy all four positions when used — a mix "
            "of fill and other characters is never legal (LOC bd008a)",
            label)
    return (int("".join("0" if c == "u" else c for c in s)),
            int("".join("9" if c == "u" else c for c in s)))


def marc008_range(field):
    f = str(field or "")
    if len(f) not in (40, 9):
        raise DateKitError(
            "field008 must be the whole 40-character field or exactly "
            "positions 06-14 (9 characters); got %d characters" % len(f),
            "field008")
    block = f if len(f) == 9 else f[6:15]
    code, d1, d2 = block[0], block[1:5], block[5:9]
    if code not in MARC_TYPES:
        raise DateKitError("008/06 code %r is not in the closed MARC21 "
                           "set (bd008a, edition 2026-05-27)" % code,
                           "field008")
    for dd in (d1, d2):
        if not _DATE_CH.match(dd):
            raise DateKitError("date positions 07-14 accept digits, u, "
                               "# and fill only: %r" % dd, "field008")
    flags = []
    ongoing = code in ("c", "u")
    e = l = None
    if code == "e":
        # date2 porte mmdd, pas une annee (la table le dit — le lire)
        ylo, yhi = _year_span(d1, "field008")
        mm, dd = d2[:2], d2[2:]
        if ylo is None or yhi is None or \
                not (mm[0].isdigit() and mm[1].isdigit()):
            if ylo is not None and yhi is not None:
                e = "%04d-01-01" % ylo
                l = "%04d-12-31" % yhi
        else:
            m = int(mm)
            if dd == "##":
                e = "%04d-%02d-01" % (ylo, m)
                l = "%04d-%02d-%02d" % (yhi, m, monthrange(yhi, m)[1])
                flags.append("month_only")
            else:
                dlo = 1 if dd == "uu" else int(dd)
                dhi = monthrange(yhi, m)[1] if dd == "uu" else int(dd)
                e = "%04d-%02d-%02d" % (ylo, m, dlo)
                l = "%04d-%02d-%02d" % (yhi, m, dhi)
    elif code in ("s", "c", "d", "i", "k", "m", "n", "q", "r", "p", "t",
                  "u", "|", "b"):
        a1 = _year_span(d1, "field008")
        a2 = _year_span(d2, "field008")
        pair = [x for x in (a1, a2) if x[0] is not None]
        if pair:
            lo = min(x[0] for x in pair)
            hi = max(x[1] for x in pair)
            if code == "s":
                lo, hi = a1
            if code in ("c", "u") or d2 == "9999":
                if d2 == "9999":
                    hi = None
                    flags.append("9999_still_published")
            if lo is not None:
                e = "%04d-01-01" % lo
            l = "%04d-12-31" % hi if hi is not None else None
        if code == "n" and (d1, d2) == ("uuuu", "uuuu"):
            e = l = None
            flags.append("dates_unknown")
        if code == "|":
            e = l = None
            flags.append("no_attempt_to_code")
        if code == "b":
            e = l = None
            flags.append("bc_dates_live_in_046_out_of_scope")
        if code == "u":
            flags.append("status_unknown")
            if d2 == "uuuu":
                l = None
    return {"date_type": code,
            "date_type_meaning": MARC_TYPES[code],
            "earliest": e,
            "latest": l,
            "ongoing": ongoing,
            "roles": _ROLES.get(code),
            "flags": flags,
            "scale": SCALE,
            "source": "LOC MARC21 bd008a (edition 2026-05-27)"}
