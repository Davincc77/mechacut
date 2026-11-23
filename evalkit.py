"""evalkit — le juge du banc csk, érigé en route (ADJACENCES décision 1).

« Est-ce que c'est juste ? » est la douleur que le bras M paie à
15/50 : les agents comparent des artefacts à l'oeil nu et publient
des « OK » sur des désaccords réels (V21 G4 nous a pris en flagrant
nous-mêmes). eval/compare répond en octets : canonique, classes
nommées, divergences pointées, sha du rapport.

Règles fermées, écrites AVANT l'impl (golds dans tests/test_bundle76) :
- Même quantité n'est jamais un désaccord : 2.5 ≡ "2.50" ≡ "5/2"
  (Decimal exact ; la fraction est la représentation légitime du
  décimal, leçon de l'incident « 3829/10 » du juge v2).
- strict_types=true change la QUESTION, pas la réponse : alors la
  FORME compte et "1.50" vs 1.5 diverge en kind "type".
- Tableaux alignés position par position ; un manque = divergence
  nommée (kind missing/extra), jamais un silence.
- ignore_paths : grammaire des pointeurs de check/format ($.a.b[0])
  — racine $ ; ce qu'on ignore est IGNORE DES DEUX CÔTÉS, la liste
  est publiée dans le rapport (l'oubli d'un sha256 écho n'est pas
  un faux négatif).
- Racines scalaires comparées (5 vs "5" = OK) : le juge ne exige
  pas des objets, il répond sur ce qu'on lui donne.
"""

import re
from decimal import Decimal, InvalidOperation

_NUM = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+|\d+/\d+)$")
_POINTER = re.compile(r"^\$((\.[A-Za-z_][\w]*)*(\[\d+\])*)$")


class EvalError(Exception):
    pass


def _loads(v):
    """JSON string -> object ; parse failure raises with position."""
    if isinstance(v, str):
        import json
        try:
            return json.loads(v)
        except json.JSONDecodeError as e:
            raise EvalError("not valid JSON at line %d col %d: %s"
                            % (e.lineno, e.colno, e.msg))
    return v


def _num(x):
    """value -> canonical Decimal if it IS a number or a plain-decimal
    /fraction string ; None otherwise. Never float: 0.1 stays 1/10."""
    if isinstance(x, bool):
        return None
    if isinstance(x, int):
        return Decimal(x)
    if isinstance(x, float):
        return Decimal(repr(x))
    if isinstance(x, str) and _NUM.match(x.strip()):
        s = x.strip()
        if "/" in s:
            a, b = s.split("/")
            try:
                return Decimal(a) / Decimal(b)
            except (InvalidOperation, ZeroDivisionError):
                return None
        return Decimal(s)
    return None


def _eq(a, b, strict):
    return _eq_strict(a, b) if strict else _eq_loose(a, b)


def _eq_loose(a, b):
    na, nb = _num(a), _num(b)
    if na is not None and nb is not None:
        return na == nb
    if na is not None or nb is not None:
        return False  # number vs non-number-shape string is a divergence
    return a == b


def _eq_strict(a, b):
    """strict: forms must match; numbers equal AND both written the
    same way (number/number or string/string with identical text)."""
    if isinstance(a, str) != isinstance(b, str):
        return False
    if isinstance(a, str) and a != b:
        return False
    return _eq_loose(a, b)


def _to_pointer(p):
    """$.a.b[0] -> /a/b/0 ; raise EvalError on anything else."""
    s = p.strip()
    if not _POINTER.match(s):
        raise EvalError("ignore_paths must look like $.field or "
                        "$.a.b[0] (the check/format pointer grammar); "
                        "got %r" % p)
    out = []
    for tok in re.findall(r"\.([A-Za-z_]\w*)|\[(\d+)\]", s[1:]):
        out.append(tok[0] or tok[1])
    return "/" + "/".join(out) if out else ""


def _walk(a, b, path, ignore, strict, divs, counts):
    if path in ignore:
        counts["ignored"] += 1
        return
    na, nb = _num(a), _num(b)
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            sub = path + "/" + k
            if sub in ignore:
                counts["ignored"] += 1
                continue
            if k not in b:
                divs.append({"pointer": sub, "kind": "only_expected",
                             "expected": a[k], "got": None})
                counts["only_expected"] += 1
            elif k not in a:
                divs.append({"pointer": sub, "kind": "only_got",
                             "expected": None, "got": b[k]})
                counts["only_got"] += 1
            else:
                _walk(a[k], b[k], sub, ignore, strict, divs, counts)
        return
    if isinstance(a, list) and isinstance(b, list):
        for i in range(max(len(a), len(b))):
            sub = path + "/" + str(i)
            if sub in ignore:
                counts["ignored"] += 1
                continue
            if i >= len(b):
                divs.append({"pointer": sub, "kind": "only_expected",
                             "expected": a[i], "got": None})
                counts["only_expected"] += 1
            elif i >= len(a):
                divs.append({"pointer": sub, "kind": "only_got",
                             "expected": None, "got": b[i]})
                counts["only_got"] += 1
            else:
                _walk(a[i], b[i], sub, ignore, strict, divs, counts)
        return
    same = _eq(a, b, strict)
    if not same:
        if strict and na is not None and nb is not None:
            kind = "type"
        elif isinstance(a, (dict, list)) or isinstance(b, (dict, list)):
            kind = "shape"
        else:
            kind = "value"
        divs.append({"pointer": path or "/", "kind": kind,
                     "expected": a, "got": b})
        counts["diverged"] += 1
    else:
        counts["matched"] += 1


def eval_compare(expected, got, ignore_paths=None, strict_types=False):
    e = _loads(expected)
    g = _loads(got)
    ignore = set()
    for p in (ignore_paths or []):
        ignore.add(_to_pointer(p))
    divs = []
    counts = {"matched": 0, "diverged": 0, "only_expected": 0,
              "only_got": 0, "ignored": 0}
    _walk(e, g, "", ignore, strict_types, divs, counts)
    verdict = "OK" if not divs else "WRONG"
    out = {"verdict": verdict,
           "divergences": sorted(divs, key=lambda d: d["pointer"]),
           "counts": counts,
           "strict_types": strict_types,
           "ignore_paths_applied": sorted(ignore) if ignore else [],
           "note": ("equal quantity is never a disagreement: 2.5, "
                    "\"2.50\" and \"5/2\" match — unless strict_types"
                    if not strict_types else
                    "strict_types: form is part of the answer")}
    return out
