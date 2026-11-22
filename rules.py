"""Bundle 15 — rules, ordering, nested access (TOOLS-50 #48, #49, #51).

Multi-step logic is where small models diverge hardest: they forget a
condition three clauses deep, sort by the wrong key when a tie exists, or
grab the wrong value out of nested JSON "by feel". This module keeps the
model out of the mechanics: a closed rule grammar evaluates facts and
emits a per-rule trace; sort keys are explicit and stable; nested access
is a pinned path grammar. The model decides what to check — the bytes
decide what it means.

Same request -> same bytes. No LLM, no network, no state.
"""
import re

__all__ = ["RulesError", "logic_rules", "sort_multi", "json_query"]


class RulesError(Exception):
    pass


# ------------------------------------------------------------- path grammar
_SEG = re.compile(r"^(?:([a-zA-Z_][a-zA-Z0-9_]*)|\[(\d+)\])$")
_LEAF_OPS = ("eq", "ne", "gt", "gte", "lt", "lte", "in", "contains",
             "not_contains", "exists")


def resolve(container, path):
    """Dot/bracket path -> (found, value). Closed grammar:
    user.level, items[0].price, a.b[12]"""
    if not isinstance(path, str) or not path:
        raise RulesError("path must be a non-empty string like user.level "
                         "or items[0].price")
    cur = container
    for raw in path.split("."):
        if raw == "":
            raise RulesError("empty path segment in %r" % path)
        m = _SEG.match(raw)
        if not m:
            raise RulesError("bad path segment %r in %r" % (raw, path))
        key, idx = m.group(1), m.group(2)
        if idx is not None:
            if not isinstance(cur, list):
                return False, None
            i = int(idx)
            if i >= len(cur):
                return False, None
            cur = cur[i]
        else:
            if not isinstance(cur, dict) or key not in cur:
                return False, None
            cur = cur[key]
    return True, cur


def _rank(v):
    """Closed type ordering: null < bool < number < string < list < dict."""
    if v is None:
        return 0
    if isinstance(v, bool):
        return 1
    if isinstance(v, (int, float)):
        return 2
    if isinstance(v, str):
        return 3
    if isinstance(v, list):
        return 4
    return 5


def _cmp(a, b):
    ra, rb = _rank(a), _rank(b)
    if ra != rb:
        return (ra > rb) - (ra < rb)
    if ra in (4, 5):            # containers compare by canonical length+rank
        sa, sb = str(a), str(b)
        return (sa > sb) - (sa < sb)
    return (a > b) - (a < b)


# ---------------------------------------------------------- rule grammar
_MAX_DEPTH = 8
_MAX_RULES = 50


def _check_cond(cond, facts, depth):
    if depth > _MAX_DEPTH:
        raise RulesError("condition nesting deeper than %d" % _MAX_DEPTH)
    if not isinstance(cond, dict) or not cond:
        raise RulesError("each condition is an object: {fact,op,value} or "
                         "one of and/or/not")
    if "fact" in cond:
        op, arg = "leaf", cond
    else:
        if len(cond) != 1:
            raise RulesError("logical condition must carry exactly one "
                             "key (and/or/not), got: %s"
                             % ", ".join(sorted(cond)))
        (op, arg), = cond.items()
    if op == "and":
        if not isinstance(arg, list) or not arg:
            raise RulesError("and expects a non-empty array of conditions")
        return all(_check_cond(c, facts, depth + 1) for c in arg)
    if op == "or":
        if not isinstance(arg, list) or not arg:
            raise RulesError("or expects a non-empty array of conditions")
        return any(_check_cond(c, facts, depth + 1) for c in arg)
    if op == "not":
        return not _check_cond(arg, facts, depth + 1)
    if op == "leaf" and not isinstance(cond.get("op"), str):
        raise RulesError("leaf condition needs {fact, op, value}")
    if op != "leaf" and not isinstance(arg, dict):
        raise RulesError("leaf condition needs {fact, op, value}")
    leaf = cond if op == "leaf" else arg
    if "op" not in leaf or "fact" not in leaf:
        raise RulesError("leaf condition needs {fact, op, value}")
    found, value = resolve(facts, leaf["fact"])
    lop = leaf["op"]
    if lop not in _LEAF_OPS:
        raise RulesError("unknown op %r; allowed: %s"
                         % (lop, ", ".join(_LEAF_OPS)))
    want = leaf.get("value")
    if lop == "exists":
        return not found if want is False else found
    if not found:
        return False
    if lop == "eq":
        return value == want
    if lop == "ne":
        return value != want
    if lop == "gt":
        return _cmp(value, want) > 0
    if lop == "gte":
        return _cmp(value, want) >= 0
    if lop == "lt":
        return _cmp(value, want) < 0
    if lop == "lte":
        return _cmp(value, want) <= 0
    if lop == "in":
        return isinstance(want, list) and any(
            not _cmp(value, x) for x in want)
    if lop == "contains":
        if isinstance(value, str):
            return isinstance(want, str) and want in value
        if isinstance(value, list):
            return any(not _cmp(v, want) for v in value)
        return False
    if lop == "not_contains":
        return not _check_cond({"fact": leaf["fact"], "op": "contains",
                                "value": want}, facts, depth)
    raise RulesError("unreachable op")


def logic_rules(facts, rules):
    if not isinstance(facts, dict):
        raise RulesError("facts must be an object")
    if not isinstance(rules, list) or not rules:
        raise RulesError("rules must be a non-empty array")
    if len(rules) > _MAX_RULES:
        raise RulesError("at most %d rules" % _MAX_RULES)
    out_facts = dict(facts)
    trace = []
    violations = []
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise RulesError("rule %d must be an object" % i)
        name = rule.get("name", "rule_%d" % i)
        if not isinstance(name, str) or not name:
            raise RulesError("rule name must be a non-empty string")
        when = rule.get("when")
        try:
            fired = True if when is None else _check_cond(when, out_facts, 1)
        except RulesError as e:
            raise RulesError("rule %r: %s" % (name, e))
        entry = {"name": name, "fired": fired}
        if not fired:
            entry["outcome"] = "skipped"
            trace.append(entry)
            continue
        ok = True
        for kind in ("require", "forbid"):
            cond = rule.get(kind)
            if cond is None:
                continue
            try:
                holds = _check_cond(cond, out_facts, 1)
            except RulesError as e:
                raise RulesError("rule %r %s: %s" % (name, kind, e))
            good = holds if kind == "require" else not holds
            if not good:
                ok = False
                v = {"rule": name, "kind": kind}
                violations.append(v)
        assigns = rule.get("set")
        if isinstance(assigns, dict):
            for path, val in sorted(assigns.items()):
                segs = path.split(".")
                if any(not _SEG.match(x) for x in segs):
                    raise RulesError("rule %r: bad set path %r"
                                     % (name, path))
                cur = out_facts
                for raw in segs[:-1]:
                    m = _SEG.match(raw)
                    if not m or not m.group(1):
                        raise RulesError("rule %r: bad set path %r"
                                         % (name, path))
                    cur = cur.setdefault(m.group(1), {})
                mlast = _SEG.match(segs[-1])
                if not mlast or not mlast.group(1):
                    raise RulesError("rule %r: bad set path %r"
                                     % (name, path))
                cur[mlast.group(1)] = val
            entry["set"] = {k: assigns[k] for k in sorted(assigns)}
        entry["outcome"] = "passed" if ok else "violated"
        trace.append(entry)
    return {
        "pass": not violations,
        "rules": len(rules),
        "fired": sum(1 for t in trace if t["fired"]),
        "violations": violations,
        "trace": trace,
        "facts": out_facts,
        "errors": [{"field": v["rule"], "expected": v["kind"],
                    "observed": "condition not met"} for v in violations],
    }


# ------------------------------------------------------------- sort/multi
def sort_multi(rows, by):
    if not isinstance(rows, list) or not all(isinstance(r, dict)
                                             for r in rows):
        raise RulesError("rows must be an array of objects")
    if not isinstance(by, list) or not by:
        raise RulesError("by must be a non-empty array of "
                         "{key, dir: asc|desc}")
    keys = []
    for spec in by:
        if not isinstance(spec, dict) or "key" not in spec:
            raise RulesError("each by entry needs a key")
        d = spec.get("dir", "asc")
        if d not in ("asc", "desc"):
            raise RulesError("dir must be asc or desc")
        resolve({}, spec["key"])          # grammar check
        keys.append((spec["key"], d))

    class K:
        __slots__ = ("pair",)

        def __init__(self, pair):
            self.pair = pair

        def __lt__(self, other):
            for path, d in keys:
                _fa, va = resolve(self.pair[1], path)
                _fb, vb = resolve(other.pair[1], path)
                c = _cmp(va, vb)
                if c:
                    return c < 0 if d == "asc" else c > 0
            return self.pair[0] < other.pair[0]   # stable: original index

    ordered = [k.pair for k in sorted(K(p) for p in list(enumerate(rows)))]
    return {"sorted": [r for _i, r in ordered], "rows": len(rows)}


# -------------------------------------------------------------- json/query
_Q = re.compile(r"^\$(?:\.[a-zA-Z_][a-zA-Z0-9_]*"
                r"|\[(?:\d+|\*)\])*$")


def json_query(data, path):
    if not isinstance(path, str) or not _Q.match(path):
        raise RulesError("path must match $ .key [n] [*] grammar, e.g. "
                         "$.users[0].email or $.items[*].price")
    results = []
    tokens = _tokenize(path)

    def step(node, toks, built):
        if not toks:
            results.append({"path": built, "value": node})
            return
        tok, rest = toks[0], toks[1:]
        if tok in ("*", "[*]"):
            if isinstance(node, list):
                for i, v in enumerate(node):
                    step(v, rest, "%s[%d]" % (built, i))
        elif tok.startswith("["):
            i = int(tok[1:-1])
            if isinstance(node, list) and i < len(node):
                step(node[i], rest, "%s[%d]" % (built, i))
        else:
            if isinstance(node, dict) and tok in node:
                step(node[tok], rest,
                     "%s.%s" % (built, tok) if built != "$"
                     else "$.%s" % tok)

    step(data, tokens, "$")
    return {"matches": len(results), "results": results,
            "not_found": not results}


def _tokenize(path):
    toks = []
    i = 1
    while i < len(path):
        c = path[i]
        if c == ".":
            j = i + 1
            while j < len(path) and path[j] not in ".[":
                j += 1
            toks.append(path[i + 1:j])
            i = j
        elif c == "[":
            j = path.index("]", i)
            toks.append(path[i:j + 1])
            i = j + 1
        else:
            raise RulesError("bad path char %r" % c)
    return toks
