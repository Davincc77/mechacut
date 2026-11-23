"""proposekit — bundle 87. La porte du SKILL-NETWORK, en sept grammes fermés.

Un agent propose un CONTRAT (jamais du code) ; le juge le route contre
l'existant et rend un verdict nommé. Rien n'est stocké ici : le blob est
pour git, le banc décide, l'humain publie. Les seuils sont dans la réponse,
jamais cachés sous un silence.
"""
import hashlib
import json
import re

SUSPECT_MIN_SCORE = 8
SUSPECT_MIN_MATCHED = 2
NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,39}$")


class ProposeError(ValueError):
    pass


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def propose(name, purpose, why, examples, source, as_of):
    if not NAME_RE.match(name or ""):
        raise ProposeError(
            "bad_name: %r — grammar ^[a-z][a-z0-9]{2,39}$ "
            "(lowercase snake_case, 3..40)" % name)
    if not isinstance(purpose, str) or not 20 <= len(purpose) <= 140:
        raise ProposeError("purpose_grammar: purpose must be a single "
                           "factual sentence of 20..140 characters — it "
                           "becomes the catalogue card and the router's "
                           "prey")
    if not isinstance(examples, list) or not 1 <= len(examples) <= 10:
        raise ProposeError("examples_grammar: 1..10 traced examples, each "
                           "{input: object, expected: object} — golds "
                           "before code, always")
    for i, ex in enumerate(examples):
        if not isinstance(ex, dict) or not isinstance(ex.get("input"), dict) \
                or not isinstance(ex.get("expected"), dict):
            raise ProposeError("examples_grammar: example %d needs both "
                               "input and expected as objects" % i)
    if len(why or "") > 300:
        raise ProposeError("why_grammar: why is a pain quote, 300 "
                           "characters max")
    if len(source or "") > 200:
        raise ProposeError("source_grammar: source is one URL, 200 max")

    import routing
    exact = _norm(name)
    dupes = [n for n, p, pk, pu, tg in routing.TABLE if _norm(n) == exact]
    hits = routing.route((purpose + " " + (why or "")).strip(), top=5)
    suspects = [h for h in hits
                if h["score"] >= SUSPECT_MIN_SCORE
                and len(h["matched"]) >= SUSPECT_MIN_MATCHED]

    checks = {"name_grammar": True, "purpose_grammar": True,
              "examples_count": len(examples),
              "suspect_min_score": SUSPECT_MIN_SCORE,
              "suspect_min_matched": SUSPECT_MIN_MATCHED}
    matches = dupes + [h["tool"] for h in suspects]
    matches_detail = [{"tool": h["tool"], "score": h["score"],
                       "matched": h["matched"]} for h in suspects[:3]]

    if dupes:
        verdict = "DUPLICATE-OF"
    elif suspects:
        verdict = "SUSPECT-DUPLICATE"
    else:
        verdict = "ELIGIBLE"

    blob = {"name": name, "purpose": purpose,
            "examples": examples,
            "why": why or "", "source": source or "",
            "as_of": as_of or None,
            "undated": not as_of}
    out = {"verdict": verdict,
           "matches": matches_detail or
           [{"tool": d, "score": None, "matched": ["exact-name"]}
            for d in dupes],
           "checks": checks,
           "thresholds": {"suspect_min_score": SUSPECT_MIN_SCORE,
                          "suspect_min_matched": SUSPECT_MIN_MATCHED},
           "blob": blob,
           "next_steps": [
               "commit the blob verbatim as docs/proposals/%s.json in "
               "github.com/Davincc77/mechacut" % name,
               "the bench replays its examples against any existing "
               "candidate; golds stay hand-traced — an accepted proposal "
               "ships as a bundle or is refused by name",
               "money follows admission, never causes it"],
           "stored": False}
    if verdict == "DUPLICATE-OF":
        out["blob"] = None
        out["next_steps"] = ["live with the existing tool: %s — a "
                             "duplicate proposal is not punished, it is "
                             "answered; divergent duplicates, though, "
                             "publish their diff to the bench" % dupes[0]]
    return out
