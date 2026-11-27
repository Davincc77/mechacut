# -*- coding: utf-8 -*-
"""foia_sheet_audit — l'arithmétique d'une feuille FOIA rejouée, pas un
verdict sur l'honnêteté du document (registre L69, reçu bb06eabd7aceefd3,
ADMIS 27-11 — audit : text_claimsweep cherche des marqueurs nommés, ne
rejoue AUCUNE arithmétique ; ici total déclaré vs lignes vs numéros vs
codes).

LOI MAISON 27-11 (consignée au registre et au brief du lot) :
  - l'ensemble FERMÉ des codes vient du STATUTE — 5 U.S.C. § 552(b) :
    b1, b2, b3, b4, b5, b6, b7A, b7B, b7C, b7D, b7E, b8, b9 — plus les
    sous-codes DOJ publiés b6-1..b6-4. La référence statute est NOMMÉE
    dans chaque réponse. L'ensemble vient du statute, JAMAIS du sheet.
  - b7E EST DANS LE STATUTE (5 U.S.C. § 552(b)(7)(E)). L'erreur
    initiale de la salle — qui plaçait b7E hors de l'ensemble observé
    {b3, b6-1..4, b7C, b7D, b3-1, OTHER} — est consignée (feuille V1
    §6, campagne Vault) ; cette porte ne la reproduit pas.
  - codes hors statute = NOMMÉS, un par un, avec leurs occurrences ;
    jamais fondus en un compteur flou. b7 nu (sans sous-clause) n'est
    PAS dans l'ensemble de la loi maison, qui énumère (b)(7)(A)-(E) :
    rendu comme token sous-spécifié, jamais replié en b7A..b7E.
  - verdicts MATCH/MISMATCH/GAP seulement. Le mot vérité/fraude
    n'existe pas ici : un écart est un écart, livre tel quel.

Matière des golds (campagne Vault, feuilles consignées) :
  - V1 (miroir archive.org jeffrey-epstein-part-22-of-22, rendu Abbyy
    du Deleted Page Information Sheet, Part 01, Civil Action
    # 17-cv-03956) : « Total Deleted Page(s) = 258 » ; 258 marqueurs
    « Page » énumérés ; n° min 3 / max 317 ; 63 numéros absents entre
    3 et 317 ; doublons de lecture Page 8 ×2 / Page 133 ×2 ; 67 lignes
    « Page N ~ OTHER - Court Sealing Order » (n° 250..317) ; b7E
    observé ×5 (pages 13, 15, 73, 100 + 1 ligne mutilée) ; sous-codes
    « b6 - 1, -2, -3, -4, -5 » observés (lignes 13-15).
  - V2 (FOIA Log 2020, archive.org FBIFOIALogs, « FOIA Log 2020.pdf »,
    sha256 ee60d3f8c33678a539950c568b409fd8b1e7dd67e319cd47e6d407211
    8979aea — couche texte NATIVE, aucune OCR) : fenêtre imprimée
    « 01/01/2020 to 12/31/2020 » ; 16 485 enregistrements ; 2 278
    date_opened hors fenêtre (2019: 1 310, ≤2018: 968, ≥2021: 0) ;
    14 207 conservées ; auto-test 5/5 sur les golds verbatim
    VAULT_V2_GOLDS.json (dont le pilote 1478175 CrowdStrike/DNC,
    13-Oct-2020, DANS la fenêtre).

Limite dite à l'admission : le bloc OCR complet des 258 lignes V1
n'existe pas dans la matière consignée (agrégats + lignes isolées
recopiées seulement) — les golds feuille rendent les lignes verbatim
citées et rejouent les agrégats consignés comme CLAIMS d'arithmétique,
jamais comme chiffres inventés. Le log natif V2 (16 485 lignes) vit
hors dépôt : ses totaux sont rejoués en claims, les 5 golds verbatim
passent PAR la porte.
"""
import calendar
import datetime
import re

REF_STATUTE = ("5 U.S.C. § 552(b) — Freedom of Information Act, "
               "exemptions (b)(1)-(b)(9), with (b)(7) subdivided "
               "(A)-(E); the closed code set of this door is read "
               "from the statute, never from the sheet; DOJ FOIA "
               "reporting publishes sub-codes b6-1..b6-4")
REF_SHEET_FORM = ("FBI/DOJ Deleted Page Information Sheet grammar "
                  "(rendered form cited from the Vault V1 triage, "
                  "archive.org jeffrey-epstein-part-22-of-22 Abbyy "
                  "layer): 'Page N ~ <code> - <markers>; <code> - "
                  "<markers>...' — each ';' segment names one "
                  "exemption token for the page; dash-list items "
                  "expand to BASE-k sub-code references, reported as "
                  "written, tested against the published sub-code "
                  "set, never merged")
REF_LOG_FORM = ("FOIA Log 2020 native-text record grammar (V2 parsed "
                "sheet v2_parse_foia_log.py, auto-test 5/5): case_rev "
                "= 3 digits, subject = free text folded to one space, "
                "date_opened = dd-Mmm-yyyy, foia_number = 7 digits — "
                "DATE OPENED is the only date column (0 occurrences "
                "of DATE CLOSED/RECEIVED/RELEASED labels); the "
                "printed window is an ARGUMENT here, never a wall "
                "clock")
REF_B7E = ("b7E is a statutory exemption — 5 U.S.C. § 552(b)(7)(E); "
           "the campaign's earlier observed-set error (placing b7E "
           "outside the closed set) is recorded and NOT reproduced "
           "here")
REF_NO_TRUTH = ("arithmetique rendue, pas un jugement d'honnetete : "
                "tout ecart est livre tel quel, verdicts limits a "
                "MATCH/MISMATCH/GAP par contrat")

# L'ensemble ferme, lu dans le statute (loi maison 27-11).
STATUTE_CODES = ("b1", "b2", "b3", "b4", "b5", "b6",
                 "b7A", "b7B", "b7C", "b7D", "b7E", "b8", "b9")
DOJ_SUBCODES = ("b6-1", "b6-2", "b6-3", "b6-4")
_IN_SET = frozenset(STATUTE_CODES) | frozenset(DOJ_SUBCODES)

_MONTHS = {m.lower(): i for i, m in enumerate(
    calendar.month_abbr[1:], 1) if m}
_PAGE_RE = re.compile(r"^\s*page\s+(?P<num>\d+|[^\s~]{1,8})\s*"
                      r"(?:[~=:.\u2013-]+\s*)?(?P<codes>.*)$",
                      re.IGNORECASE)
_MARK_RE = re.compile(r"-?\s*(\d+)")
_LOG_RE = re.compile(r"^\s*(?:(?P<rev>\d{3})\s+)?(?P<subject>.+?)\s*"
                     r"(?P<date>\d{2}-[A-Za-z]{3}-\d{4})(?P<num>\d{7})"
                     r"\s*$", re.S)


class FoiaKitError(Exception):
    def __init__(self, field, msg):
        self.field = field
        self.msg = msg
        super().__init__(msg)


def _iso(d):
    return datetime.date.fromisoformat(d)


def _statute_block():
    return {
        "citation": "5 U.S.C. § 552(b)",
        "statute_codes": list(STATUTE_CODES),
        "doj_published_subcodes": list(DOJ_SUBCODES),
        "rule": REF_STATUTE,
        "b7e_note": REF_B7E,
    }


def _audit_sheet(declared_total, lines):
    codes = {}          # base tokens as written
    subrefs = {}        # expanded BASE-k references
    other_tokens = {}   # non-b tokens (sheet vocabulary), verbatim base
    other_labels = {}   # token -> the trailing labels seen, verbatim
    unnumbered = []
    numbers = []
    non_page = []
    markers = 0
    for raw in lines:
        m = _PAGE_RE.match(raw)
        if not m:
            non_page.append(raw)
            continue
        markers += 1
        num = m.group("num")
        if num.isdigit():
            numbers.append(int(num))
        else:
            unnumbered.append(raw.strip())
        for seg in m.group("codes").split(";"):
            seg = seg.strip().strip(",")
            if not seg:
                continue
            bm = re.search(r"(?<![A-Za-z0-9])(b\d(?:[A-E]|-[1-9])?)(.*)$",
                           seg, re.IGNORECASE)
            if bm:
                # leading OR noise-prefixed exemption token — an OCR
                # line like 'Page — i • 219 ~ b7E - 1' keeps its code;
                # dash-list items after the token expand to BASE-k
                code = re.sub(r"\s+", "", bm.group(1))
                rest = bm.group(2)
                codes[code] = codes.get(code, 0) + 1
                if re.match(r"^\s*-", rest):
                    for k in _MARK_RE.findall(rest):
                        ref = "%s-%s" % (code, k)
                        subrefs[ref] = subrefs.get(ref, 0) + 1
            else:
                # sheet vocabulary: 'OTHER - Court Sealing Order' —
                # the token and its verbatim label are both kept,
                # never folded into the statute counters
                parts = re.split(r"\s+-\s+|\s+", seg.strip(), 1)
                token = parts[0]
                other_tokens[token] = other_tokens.get(token, 0) + 1
                if len(parts) > 1 and parts[1]:
                    other_labels.setdefault(token, set()).add(parts[1])

    total_verdict = "MATCH" if markers == declared_total \
        else "MISMATCH"
    dup = {}
    for n in numbers:
        dup[n] = dup.get(n, 0) + 1
    duplicates = [{"page": n, "count": c}
                  for n, c in sorted(dup.items()) if c > 1]
    distinct = sorted(set(numbers))
    gaps = []
    if distinct:
        lo, hi = distinct[0], distinct[-1]
        have = set(distinct)
        gaps = [n for n in range(lo, hi + 1) if n not in have]

    def split(obs):
        inside, outside = {}, {}
        for k, c in sorted(obs.items()):
            (inside if k.lower() in _IN_SET or k in _IN_SET
             else outside)[k] = c
        return inside, outside

    in_base, out_base = split(codes)
    in_sub, out_sub = split(subrefs)
    hors = {}
    for k, c in out_base.items():
        hors[k] = hors.get(k, 0) + c
    for k, c in out_sub.items():
        hors[k] = hors.get(k, 0) + c
    codes_verdict = ("MATCH" if not hors and not other_tokens
                     else "MISMATCH")
    return {
        "kind": "deleted_page_sheet",
        "declared_total": declared_total,
        "lines_passed": len(lines),
        "lines_enumerees": markers,
        "total_verdict": total_verdict,
        "delta_total": markers - declared_total,
        "numbering": {
            "verdicts": {
                "duplicates": "MISMATCH" if duplicates else "MATCH",
                "gaps": "GAP" if gaps else "MATCH",
            },
            "numbers_distinct": len(distinct),
            "min": distinct[0] if distinct else None,
            "max": distinct[-1] if distinct else None,
            "duplicates": duplicates,
            "gaps_count": len(gaps),
            "gaps_sample": gaps[:10],
            "gaps_sample_rule": "first 10 ascending; full count "
                                "given, the sample is capped and "
                                "said — never silent",
            "max_gt_declared": bool(distinct and
                                    distinct[-1] > declared_total),
            "unnumbered_lines": unnumbered[:10],
            "unnumbered_count": len(unnumbered),
            "unnumbered_rule": "markers whose OCR ate the number — "
                               "listed, never reconstituted",
        },
        "codes": {
            "statute": _statute_block(),
            "verdict": codes_verdict,
            "in_statute": in_base,
            "in_doj_subcodes": in_sub,
            "hors_statute": hors,
            "sheet_tokens_non_statute": other_tokens,
            "sheet_token_labels": {k: sorted(v)
                                   for k, v in sorted(other_labels.items())},
            "rule": "every observed token is named with its "
                    "occurrences; hors-statute tokens are never "
                    "merged into a counter, and b7E is inside the "
                    "statute (see b7e_note)",
        },
        "non_page_lines": {"count": len(non_page),
                           "sample": non_page[:5],
                           "rule": "lines without a 'Page N' marker "
                                   "are counted apart, never folded "
                                   "into lignes enumerees"},
    }


def _parse_log_line(line):
    m = _LOG_RE.match(line)
    if not m:
        return ({"raw": line, "parse": "NO_RECORD_TAIL",
                 "errors": ["no dd-Mmm-yyyy + 7-digit tail — the "
                            "native record buffer is absent, nothing "
                            "is guessed"]}, None)
    date = m.group("date")
    dd, mon, yyyy = date.split("-")
    errs = []
    mi = _MONTHS.get(mon.lower())
    d = None
    if mi is None:
        errs.append("month_name_unknown")
    else:
        day, year = int(dd), int(yyyy)
        if not (1 <= day <= calendar.monthrange(year, mi)[1]):
            errs.append("day_invalid_for_month")
        else:
            d = datetime.date(year, mi, day)
    rev = m.group("rev")
    out = {
        "raw": line,
        "parse": "OK" if not errs else "FIELD_ERRORS",
        "fields": {
            "case_rev": rev,
            "subject": re.sub(r"\s+", " ", m.group("subject")).strip(),
            "date_opened": date,
            "foia_number": m.group("num"),
        },
        "errors": errs,
    }
    if rev is None:
        out["observations"] = ["case_rev_absent_in_text"]
    else:
        out["observations"] = []
    return out, d


def _audit_log(window, lines, declared_total):
    wf, wt = window["from"], window["to"]
    lo, hi = _iso(wf), _iso(wt)
    records, anomalies = [], []
    inside, outside, bad_dates = 0, 0, 0
    by_year = {}
    for i, ln in enumerate(lines):
        rec, d = _parse_log_line(ln)
        rec["index"] = i
        if rec["parse"] == "NO_RECORD_TAIL":
            anomalies.append(rec)
            continue
        if d is None:
            bad_dates += 1
            records.append(rec)
            continue
        inw = lo <= d <= hi
        rec["in_window"] = inw
        if inw:
            inside += 1
        else:
            outside += 1
            by_year[d.year] = by_year.get(d.year, 0) + 1
        records.append(rec)
    dist = {"in_window": inside, "out_of_window": outside,
            "date_errors": bad_dates,
            "out_by_year": {str(y): n for y, n in
                            sorted(by_year.items())}}
    verdict = "MATCH" if (outside == 0 and not anomalies
                          and not bad_dates) else "MISMATCH"
    out = {
        "kind": "foia_log",
        "window": {"from": wf, "to": wt, "inclusive": True},
        "window_verdict": verdict,
        "lines_enumerees": len(lines),
        "counts": dist,
        "arithmetic": "in_window + out_of_window + date_errors + "
                      "anomalies = %d + %d + %d + %d = %d "
                      "(lines_enumerees)"
                      % (inside, outside, bad_dates, len(anomalies),
                         len(lines)),
        "records": records,
        "anomalies": anomalies,
        "definitions": {
            "date_column": "DATE OPENED only — the log carries no "
                           "DATE CLOSED/RECEIVED/RELEASED column "
                           "(V2 finding, labels counted 0); the "
                           "window is read against date_opened",
            "window": "the printed reporting period, passed as an "
                      "argument — never a wall clock",
            "boundary": REF_LOG_FORM,
            "reading": REF_NO_TRUTH,
        },
    }
    if declared_total is not None:
        out["declared_total"] = declared_total
        out["total_verdict"] = ("MATCH"
                                if declared_total == len(lines)
                                else "MISMATCH")
        out["delta_total"] = len(lines) - declared_total
    return out


def audit(req):
    kind = req.get("kind")
    if kind not in ("deleted_page_sheet", "foia_log"):
        raise FoiaKitError(
            "kind", "kind: deleted_page_sheet or foia_log — the two "
            "sheet grammars are named, never sniffed from the text")
    lines = req.get("lines")
    if not isinstance(lines, list) or not (1 <= len(lines) <= 2000):
        raise FoiaKitError(
            "lines", "lines: 1..2000 strings, the enumerated rows of "
            "the sheet or log exactly as rendered — beyond 2000 send "
            "the sheet in slices, this door keeps every line it saw")
    for i, l in enumerate(lines):
        if not isinstance(l, str):
            raise FoiaKitError("lines[%d]" % i,
                               "lines[%d]: a string, refused by "
                               "name" % i)
    if kind == "deleted_page_sheet":
        dt = req.get("declared_total")
        if not isinstance(dt, int) or isinstance(dt, bool):
            raise FoiaKitError(
                "declared_total", "declared_total: an integer — the "
                "sheet's own stated 'Total Deleted Page(s) = N' is "
                "the claim under audit; without it there is no total "
                "to compare, and inventing one is not this door's "
                "job")
        if req.get("window") is not None:
            raise FoiaKitError(
                "window", "window: deleted_page_sheet takes no "
                "window — date auditing is the foia_log kind")
        out = _audit_sheet(dt, lines)
        out["statute"] = out["codes"].pop("statute")
    else:
        w = req.get("window")
        if not isinstance(w, dict) or "from" not in w or "to" not in w:
            raise FoiaKitError(
                "window", "window: {from, to} ISO dates — the "
                "printed period is an argument, never guessed; the "
                "log kind audits lines against it")
        try:
            lo, hi = _iso(w["from"]), _iso(w["to"])
        except ValueError:
            raise FoiaKitError(
                "window", "window.from/window.to: valid ISO dates "
                "(YYYY-MM-DD) — malformed bounds are refused by "
                "name, not clamped")
        if lo > hi:
            raise FoiaKitError(
                "window", "window: inverted bounds refused by name "
                "(the sister date doors never default a window "
                "either)")
        out = _audit_log({"from": w["from"], "to": w["to"]},
                         lines, req.get("declared_total"))
        out["statute"] = _statute_block()
    out["boundary"] = REF_NO_TRUTH
    return out
