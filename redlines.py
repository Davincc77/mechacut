"""Bundle 22 lot 2 — /check/redlines. The negative-constraint gate.

"Never include customer identifiers", "max 280 chars", "do not mention
pricing" — research (2026) shows these degrade as context grows, and a
schema cannot catch them. Closed rules, pure scan, same text -> same
verdict. First violation only: the agent must not relearn to dump.

rules (all optional, at least one required):
  forbid_words  list of literal strings, case-insensitive word match
  forbid_regex  list of regex (<= 200 chars, run through the safety gate)
  forbid_shapes list of PII shapes: email | card | iban | phone | ssn
  max_bytes     integer
"""
import re

_SHAPES = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "card": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    "iban": re.compile(r"\b[A-Z]{2}\d{2}[ ]?(?:[A-Z0-9]{4}[ ]?){3,7}\b"),
    "phone": re.compile(r"\b\+?\d{1,3}[ .-]?(?:\((?:\d{2,4})\)[ .-]?)?"
                        r"(?:\d[ .-]?){7,12}\d\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}
MAX_RULES = 12


def check_redlines(text, rules):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    if not isinstance(rules, dict) or not rules:
        raise ValueError("rules object required (forbid_words, "
                         "forbid_regex, forbid_shapes, max_bytes)")
    hits = []

    mw = rules.get("max_bytes")
    if mw is not None:
        n = len(text.encode("utf-8"))
        if n > int(mw):
            hits.append({"rule": "max_bytes", "kind": "budget",
                         "why": "%d bytes > %d" % (n, int(mw)),
                         "at": n - int(mw)})

    for w in (rules.get("forbid_words") or [])[:MAX_RULES]:
        rx = re.compile(r"(?<![\w-])%s(?![\w-])" % re.escape(str(w)),
                        re.I)
        m = rx.search(text)
        if m:
            hits.append({"rule": "forbid_words:%s" % w, "kind": "word",
                         "why": "forbidden word present",
                         "at": m.start()})

    shapes = rules.get("forbid_shapes") or []
    unknown = [s for s in shapes if s not in _SHAPES]
    if unknown:
        raise ValueError("unknown shapes: %s; expected %s"
                         % (", ".join(map(str, unknown)),
                            ", ".join(sorted(_SHAPES))))
    for s in shapes[:MAX_RULES]:
        m = _SHAPES[s].search(text)
        if m:
            hits.append({"rule": "forbid_shapes:%s" % s, "kind": "shape",
                         "why": "%s-shaped token leaked" % s,
                         "at": m.start()})

    for r in (rules.get("forbid_regex") or [])[:MAX_RULES]:
        r = str(r)
        if len(r) > 200:
            raise ValueError("regex too long (max 200 chars)")
        try:
            rx = re.compile(r)
        except re.error as e:
            raise ValueError("bad regex %r: %s" % (r, e))
        m = rx.search(text)
        if m:
            hits.append({"rule": "forbid_regex", "kind": "regex",
                         "why": "matched %r" % m.group(0)[:60],
                         "at": m.start()})

    return {"clean": not hits, "violations": len(hits),
            "first_violation": (hits[0] if hits else None),
            "all_violations": hits[:8]}
