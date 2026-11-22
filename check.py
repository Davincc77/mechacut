"""Bundle 13 — self-check for weak agents (TOOLS-50 #42, #43).

A weak model cannot proofread its own output: it believes it wrote three
points when it wrote two, that it stayed under 100 words, that a date made
it through, that every URL came from the sources. This module replaces
that self-report with a measurement: closed constraint vocabulary, exact
verdicts, deterministic ordering. The model proposes; the byte gate
disposes.

Same request -> same bytes. No LLM, no network, no state.
"""
import hashlib
import json
import re

__all__ = ["CheckError", "check_constraints", "check_refs"]


class CheckError(Exception):
    """Closed-vocabulary refusal: message names the expected shape."""


# ------------------------------------------------------------ vocabulary
_CONSTRAINT_ORDER = (
    "min_chars", "max_chars", "min_bytes", "max_bytes", "min_words",
    "max_words", "max_lines", "points", "point_max_words", "must_contain",
    "must_not_contain", "contains_date", "contains_number", "starts_with",
    "ends_with", "no_markdown", "max_urls", "https_only",
)
_CASE = ("fold", "exact")

_URL_RE = re.compile(r"(?:(?:https?|ftp|mailto):)[^\s<>\"'()\[\]]+", re.I)
_ISO_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_SLASH_RE = re.compile(r"\b\d{1,2}[/.]\d{1,2}[/.]\d{2,4}\b")
_MONTHS = (r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?"
           r"|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
           r"nov(?:ember)?|dec(?:ember)?")
_MONTH_RE = re.compile(
    r"\b\d{1,2}(?:st|nd|rd|th)?\s+of?\s+(?:%s)\.?\s+\d{2,4}\b" % _MONTHS,
    re.I)
_MONTH_RE2 = re.compile(
    r"\b(?:%s)\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{2,4}\b" % _MONTHS, re.I)
_EPOCH_RE = re.compile(r"\b\d{10}\b")
_NUM_RE = re.compile(r"(?<![\w.])[-+]?\d+(?:[.,]\d+)*(?:%|e[-+]?\d+)?",
                     re.I)
_POINT_RE = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s+\S")
_MD_PATTERNS = ("**", "__", "`", "](")

_REF_KINDS = ("urls", "numbers", "hex", "uuid")
_HEX_RE = re.compile(r"\b0x[0-9a-fA-F]{6,}\b")
_UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")


def _norm(value, case):
    v = value.strip() if isinstance(value, str) else value
    if case == "fold" and isinstance(v, str):
        v = v.casefold()
    return v


def _words(text):
    return text.split()


def _fail(constraint, expected, observed):
    return {"constraint": constraint, "ok": False,
            "expected": expected, "observed": observed,
            "message": "%s: expected %s, observed %s"
                       % (constraint, expected, observed)}


def _ok(constraint, observed):
    return {"constraint": constraint, "ok": True, "observed": observed}


# ----------------------------------------------------------- constraints
def check_constraints(text, constraints, case="fold"):
    if not isinstance(text, str):
        raise CheckError("text must be a string")
    if not isinstance(constraints, dict) or not constraints:
        raise CheckError("constraints must be a non-empty object of "
                         "{name: value} from: %s"
                         % ", ".join(_CONSTRAINT_ORDER))
    if case not in _CASE:
        raise CheckError("case must be one of: %s" % ", ".join(_CASE))
    unknown = sorted(k for k in constraints if k not in _CONSTRAINT_ORDER)
    if unknown:
        raise CheckError("unknown constraint(s) %s; allowed: %s"
                         % (", ".join(unknown), ", ".join(_CONSTRAINT_ORDER)))

    def num(name):
        v = constraints[name]
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise CheckError("%s must be a non-negative integer" % name)
        return v

    results = []
    words = _words(text)
    lines = text.splitlines()
    lower = text.casefold() if case == "fold" else text

    def add(name, passed, expected, observed):
        results.append(_ok(name, observed) if passed
                       else _fail(name, expected, observed))

    if "min_chars" in constraints:
        v = num("min_chars")
        add("min_chars", len(text) >= v, v, len(text))
    if "max_chars" in constraints:
        v = num("max_chars")
        add("max_chars", len(text) <= v, v, len(text))
    if "min_bytes" in constraints:
        v = num("min_bytes")
        b = len(text.encode("utf-8"))
        add("min_bytes", b >= v, v, b)
    if "max_bytes" in constraints:
        v = num("max_bytes")
        b = len(text.encode("utf-8"))
        add("max_bytes", b <= v, v, b)
    if "min_words" in constraints:
        v = num("min_words")
        add("min_words", len(words) >= v, v, len(words))
    if "max_words" in constraints:
        v = num("max_words")
        add("max_words", len(words) <= v, v, len(words))
    if "max_lines" in constraints:
        v = num("max_lines")
        add("max_lines", len(lines) <= v, v, len(lines))

    point_lines = [ln for ln in lines if _POINT_RE.match(ln)]
    if "points" in constraints:
        v = num("points")
        add("points", len(point_lines) == v, v, len(point_lines))
    if "point_max_words" in constraints:
        v = num("point_max_words")
        over = sum(1 for ln in point_lines
                   if len(_words(_POINT_RE.sub("", ln, count=1))) > v)
        add("point_max_words", over == 0, "<=%d words each" % v,
            "%d point(s) over" % over if over else "all within")

    for key in ("must_contain", "must_not_contain"):
        if key in constraints:
            vals = constraints[key]
            if (not isinstance(vals, list) or not vals
                    or not all(isinstance(x, str) and x for x in vals)):
                raise CheckError("%s must be a non-empty array of "
                                 "non-empty strings" % key)
            missing = [x for x in vals
                       if _norm(x, case) not in lower]
            found = [x for x in vals if _norm(x, case) in lower]
            if key == "must_contain":
                add(key, not missing, "all present",
                    "missing: %s" % ", ".join(missing) if missing
                    else "all present")
            else:
                add(key, not found, "none present",
                    "found: %s" % ", ".join(found) if found
                    else "none present")

    if "contains_date" in constraints:
        want = bool(constraints["contains_date"])
        found = any(rx.search(text) for rx in
                    (_ISO_RE, _SLASH_RE, _MONTH_RE, _MONTH_RE2))
        add("contains_date", found == want, want, found)
    if "contains_number" in constraints:
        want = bool(constraints["contains_number"])
        found = bool(_NUM_RE.search(text))
        add("contains_number", found == want, want, found)
    for key in ("starts_with", "ends_with"):
        if key in constraints:
            v = constraints[key]
            if not isinstance(v, str) or not v:
                raise CheckError("%s must be a non-empty string" % key)
            edge = (text.lstrip().casefold() if case == "fold"
                    else text.lstrip())
            tail = (text.rstrip().casefold() if case == "fold"
                    else text.rstrip())
            needle = _norm(v, case)
            add(key, (edge.startswith(needle) if key == "starts_with"
                      else tail.endswith(needle)), v,
                "ok" if (edge.startswith(needle)
                         if key == "starts_with" else tail.endswith(needle))
                else "text %s: %s" % (
                    "begins" if key == "starts_with" else "ends",
                    (edge if key == "starts_with" else tail)[:40]))
    if "no_markdown" in constraints:
        want = bool(constraints["no_markdown"])
        hits = [p for p in _MD_PATTERNS if p in text] + [
            "h:" for ln in lines if re.match(r"^#{1,6}\s", ln)]
        add("no_markdown", (not hits) == want, want,
            "markdown found: %s" % ", ".join(hits) if hits else "clean")

    urls = _URL_RE.findall(text)
    if "max_urls" in constraints:
        v = num("max_urls")
        add("max_urls", len(urls) <= v, v, len(urls))
    if "https_only" in constraints:
        want = bool(constraints["https_only"])
        bad = [u for u in urls if not u.lower().startswith("https://")]
        add("https_only", (not bad) == want, want,
            "non-https: %s" % ", ".join(bad[:3]) if bad else "all https")

    failures = [r for r in results if not r["ok"]]
    return {
        "pass": not failures,
        "checked": len(results),
        "results": results,
        "first_failure": failures[0]["message"] if failures else None,
        "errors": [{"field": r["constraint"], "expected": r["expected"],
                    "observed": r["observed"]} for r in failures],
    }


# ------------------------------------------------------------------ refs
def check_refs(text, sources, kinds=None, case="fold"):
    if not isinstance(text, str):
        raise CheckError("text must be a string")
    if (not isinstance(sources, list) or not sources
            or not all(isinstance(x, str) and x.strip() for x in sources)):
        raise CheckError("sources must be a non-empty array of strings")
    if case not in _CASE:
        raise CheckError("case must be one of: %s" % ", ".join(_CASE))
    kinds = kinds or list(_REF_KINDS)
    if (not isinstance(kinds, list) or not kinds
            or any(k not in _REF_KINDS for k in kinds)):
        raise CheckError("kinds must be a subset of: %s"
                         % ", ".join(_REF_KINDS))

    found = []
    if "urls" in kinds:
        found += [("url", u.rstrip(".,;:!?)]\"'")) for u in _URL_RE.findall(text)]
    if "numbers" in kinds:
        found += [("number", n) for n in _NUM_RE.findall(text)]
    if "hex" in kinds:
        found += [("hex", h) for h in _HEX_RE.findall(text)]
    if "uuid" in kinds:
        found += [("uuid", u) for u in _UUID_RE.findall(text)]

    pool = []
    for s in sources:
        pool.append(_norm(s, case))
    # every reference found in the text must appear in some source string
    unknown = []
    seen = set()
    for kind, ref in found:
        nr = _norm(ref, case)
        if nr in seen:
            continue
        seen.add(nr)
        if not any(nr in p for p in pool):
            unknown.append({"kind": kind, "ref": ref})
    matched = len(seen) - len(unknown)
    used_idx = set()
    for i, p in enumerate(pool):
        if any(_norm(ref, case) in p for _kind, ref in found):
            used_idx.add(i)
    unused = [s for i, s in enumerate(sources) if i not in used_idx]
    return {
        "pass": not unknown,
        "refs_total": len(seen),
        "matched": matched,
        "unknown": unknown,
        "unused_sources": unused,
        "errors": [{"field": "ref", "expected": "present in sources",
                    "observed": u["ref"]} for u in unknown],
    }
