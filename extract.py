"""Bundle 14 — reliable extraction (TOOLS-50 #44, #45).

A weak model summarizing a document *loses* facts silently: the one number
that mattered, the date in paragraph four, the amount with the wrong comma.
Extraction by LLM is recall by chance. This module does recall by
construction: every number, date, money amount, email, URL and identifier
in the text, with its byte offset and context window — deterministic,
complete, and cheap because it never guesses.

Same request -> same bytes. No LLM, no network, no state.
"""
import re

__all__ = ["ExtractError", "extract_facts", "select_chunks"]


class ExtractError(Exception):
    pass


_ISO = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_DMY = re.compile(r"\b\d{1,2}[/.]\d{1,2}[/.]\d{2,4}\b")
_MONTHS = (r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
           r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
           r"Nov(?:ember)?|Dec(?:ember)?")
_M1 = re.compile(r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:%s)\.?(?:\s+\d{2,4})?\b"
                 % _MONTHS)
_M2 = re.compile(r"\b(?:%s)\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{2,4}\b"
                 % _MONTHS)
_URL = re.compile(r"(?:https?|ftp|mailto):[^\s<>\"'()\[\]]+")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_HEXID = re.compile(r"\b0x[0-9a-fA-F]{6,}\b")
_UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                   r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_IBANISH = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?\d[A-Z0-9]){10,30}\b")
_NUM_TAIL = r"(?:\d[\d.,]*\d|\d)"          # amounts must end on a digit
_MONEY = re.compile(
    r"(?<![\w.,$€£¥/])(?:[-+]?(?:[$€£¥R$]\s?" + _NUM_TAIL +
    r"|" + _NUM_TAIL + r"\s?(?:USD|EUR|BRL|GBP|JPY|XOF)))(?![\w])")
_NUM = re.compile(r"(?<![\w.,$€£¥/-])[-+]?\d+(?:[.,]\d+)*(?=%|\b)"
                  r"(?![-/]\d)")
_KIND_ORDER = ("money", "date", "number", "percent", "url", "email",
               "uuid", "hexid", "iban")
_PERCENT = re.compile(r"(?<![\w.])[-+]?\d+(?:[.,]\d+)?\s?%")


def _overlaps(spans, start, end):
    for _k, s, _e in spans:
        if start < _e and s < end:
            return True
    return False


def extract_facts(text, context_chars=30, group=None):
    if not isinstance(text, str):
        raise ExtractError("text must be a string")
    if (not isinstance(context_chars, int) or isinstance(context_chars, bool)
            or not 0 <= context_chars <= 200):
        raise ExtractError("context_chars must be an integer 0..200")
    spans = []

    def harvest(rx, kind):
        for m in rx.finditer(text):
            s, e = m.span()
            if kind in ("url", "email"):   # trailing prose punctuation
                while e > s + 1 and text[e - 1] in ".,;:!?)]":
                    e -= 1
            if not _overlaps(spans, s, e):
                spans.append((kind, s, e))

    harvest(_MONEY, "money")
    harvest(_M1, "date")
    harvest(_M2, "date")
    harvest(_ISO, "date")
    harvest(_DMY, "date")
    harvest(_PERCENT, "percent")
    harvest(_EMAIL, "email")      # before URL: mailto handled there
    harvest(_URL, "url")
    harvest(_UUID, "uuid")
    harvest(_HEXID, "hexid")
    harvest(_IBANISH, "iban")
    harvest(_NUM, "number")
    spans.sort(key=lambda t: (t[1], _KIND_ORDER.index(t[0])))
    out = []
    for kind, s, e in spans:
        if kind == "percent" and "%" not in text[s:e]:
            kind = "number"
        left = text[max(0, s - context_chars):s]
        right = text[e:e + context_chars]
        out.append({"kind": kind, "value": text[s:e], "at": s,
                    "context": "%s[%s]%s" % (left, text[s:e], right)
                    if context_chars else None})
    by_kind = {}
    for f in out:
        by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
    if group == "kind":
        vals = {}
        for f in out:
            v = f["value"]
            if v not in vals.setdefault(f["kind"], []):
                vals[f["kind"]].append(v)
        return {"total": len(out), "by_kind": by_kind,
                "values": {k: vals[k] for k in _KIND_ORDER if k in vals}}
    return {"total": len(out), "by_kind": by_kind, "facts": out}


# ------------------------------------------------------------- selection
def select_chunks(chunks, query, k=3, unit="word"):
    if not isinstance(chunks, list) or not chunks:
        raise ExtractError("chunks must be a non-empty array of strings")
    if not all(isinstance(c, str) for c in chunks):
        raise ExtractError("chunks must contain only strings")
    if not isinstance(query, str) or not query.strip():
        raise ExtractError("query must be a non-empty string")
    if (not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= 50):
        raise ExtractError("k must be an integer 1..50")
    if unit not in ("word", "char"):
        raise ExtractError("unit must be word or char")

    def toks(s):
        if unit == "word":
            return {t for t in re.split(r"[^\w]+", s.casefold()) if t}
        return set(c for c in s.casefold() if not c.isspace())

    q = toks(query)
    if not q:
        raise ExtractError("query has no selectable tokens")
    scored = []
    for i, c in enumerate(chunks):
        ct = toks(c)
        overlap = len(q & ct)
        score = (overlap / len(q), overlap, -i, len(c))
        scored.append((score, i, c, ct))
    scored.sort(key=lambda t: t[0], reverse=True)
    chosen = scored[:k]
    chosen.sort(key=lambda t: t[1])   # preserve document order in output
    return {
        "selected": [{"index": i, "score": round(sc[0], 6),
                      "matched_terms": sorted(q & ct), "text": c}
                     for sc, i, c, ct in chosen],
        "coverage": round(max(sc[0] for sc, _i, _c, _t in chosen), 6),
    }


# --------------------------------------------- composition (Bundle 20)
def _canon_money(v):
    from decimal import Decimal, InvalidOperation
    t = v.strip()
    for ch in ("$", "\u20ac", "\u00a3", "\u00a5", " "):
        t = t.replace(ch, "")
    neg = t.startswith("-")
    t = t.lstrip("-").replace(",", "")
    # trailing devise textuelle : 1 000 USD / 50 dollars
    for suf in ("USD", "usd", "dollars", "dollar", "EUR", "eur", "euros"):
        if t.endswith(suf):
            t = t[: -len(suf)]
    try:
        d = Decimal(t)
    except InvalidOperation:
        return None
    d = d.quantize(Decimal("0.01")) if d == d.to_integral_value() is False         else d.quantize(Decimal("0.01"))
    return ("-" if neg else "") + format(d, "f")


def _canon_percent(v):
    t = v.strip().rstrip("%").replace(" ", "")
    return t or None


def _canon_date(v):
    import re as _re
    m = _re.match(r"^(\d{4})-(\d{2})-(\d{2})", v.strip())
    if m:
        return m.group(0)
    try:
        import dates as _d
        return _d.parse_date(v)["iso"][:10]
    except Exception:
        return None


def _numkey(s):
    try:
        return (0, float(s.replace(",", "")))
    except ValueError:
        return (1, s)


def recipe_facts(text, kinds=None, total=True):
    """Server-side composition of the mechanical answer: extract -> canon-
    icalize -> dedupe -> sort -> sum. The model's whole job is to CHOOSE this
    recipe; nothing is retranscribed (bundle 20 / bench v8 lesson)."""
    base = extract_facts(text, context_chars=0, group="kind")
    vals = base.get("values", {})
    want = kinds or list(vals.keys())
    if isinstance(want, str):
        want = [want]
    inventory = {}
    for kind in want:
        raw = vals.get(kind, [])
        if kind == "money":
            c = [_canon_money(x) for x in raw]
        elif kind == "percent":
            c = [_canon_percent(x) for x in raw]
        elif kind == "date":
            c = [_canon_date(x) for x in raw]
        else:
            c = [x.strip().lower() if kind == "email" else x.strip()
                 for x in raw]
        uniq = []
        for x in c:
            if x and x not in uniq:
                uniq.append(x)
        if kind in ("money", "percent", "number"):
            uniq.sort(key=_numkey)
        else:
            uniq.sort()
        inventory[kind] = uniq
    out = {"inventory": inventory,
           "counts": {k: len(v) for k, v in inventory.items()},
           "total_facts": base["total"]}
    if total and inventory.get("money"):
        from decimal import Decimal
        ssum = Decimal(0)
        ok = True
        for m in inventory["money"]:
            try:
                ssum += Decimal(m)
            except Exception:
                ok = False
        if ok:
            out["total_money"] = format(ssum.quantize(Decimal("0.01")), "f")
    return out
