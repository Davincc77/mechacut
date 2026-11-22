"""Deterministic JSON repair, diff, patch, canonicalization and dedupe.

Pure functions, stdlib only. No LLM, no storage. Same input -> same output.

Repair scope (documented, closed set): markdown fences, BOM, smart quotes,
single-quoted strings, // and /* */ comments, Python literals (True/False/
None/NaN/Infinity), bare object keys, trailing commas, JSONL one-object-per-
line. Repairs are recorded by name in a stable order.
"""

import copy
import json
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit


class RepairError(Exception):
    pass


class PatchError(Exception):
    def __init__(self, index, message):
        super().__init__(f"patch[{index}]: {message}")
        self.index = index
        self.message = message


_FENCE = re.compile(r"^```[ \t]*(?:json|JSON)?[ \t]*\r?\n([\s\S]*?)\r?\n?```$")
_SMART = {
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
    "\u2018": "'", "\u2019": "'", "\u201a": "'",
    "\u00ab": '"', "\u00bb": '"',
}
_BARE_KEY = re.compile(r"([{,][ \t\r\n]*)([A-Za-z_$][A-Za-z0-9_$.\-]*)([ \t\r\n]*:)")
_TRAILING = re.compile(r",[ \t\r\n]*([}\]])")
_MINUS_INF = re.compile(r"-[ \t]*Infinity")
_PY_LIT = re.compile(r"(?<![\w.\"])(True|False|None|NaN|Infinity)(?![\w\"])")
_VALID_ESC = set('"\\/bfnrt')


def _add(seq, name):
    if name not in seq:
        seq.append(name)


def _read_sq(s, i):
    """Read a single-quoted string at s[i]; return (double_quoted, next_i) or None."""
    out = ['"']
    j, n = i + 1, len(s)
    while j < n:
        c = s[j]
        if c == "\\" and j + 1 < n:
            nx = s[j + 1]
            if nx == "'":
                out.append("'")
            elif nx == '"':
                out.append('\\"')
            elif nx in _VALID_ESC or nx == "u":
                out.append(c + nx)
            else:
                out.append("\\\\" + nx)
            j += 2
            continue
        if c == '"':
            out.append('\\"')
        elif c == "'":
            out.append('"')
            return "".join(out), j + 1
        elif c == "\n":
            return None
        else:
            out.append(c)
        j += 1
    return None


def _split(s, repairs):
    """Tokenize into ('code'|'str', text); single quotes become JSON strings."""
    parts, buf = [], []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == '"':
            j = i + 1
            closed = False
            while j < n:
                if s[j] == "\\":
                    j += 2
                    continue
                if s[j] == '"':
                    closed = True
                    break
                j += 1
            if closed:
                if buf:
                    parts.append(("code", "".join(buf)))
                    buf = []
                parts.append(("str", s[i:j + 1]))
                i = j + 1
                continue
        if c == "'":
            got = _read_sq(s, i)
            if got:
                if buf:
                    parts.append(("code", "".join(buf)))
                    buf = []
                parts.append(("str", got[0]))
                _add(repairs, "single_quotes")
                i = got[1]
                continue
        buf.append(c)
        i += 1
    if buf:
        parts.append(("code", "".join(buf)))
    return parts


def _fix_code(code, repairs):
    out = []
    i, n = 0, len(code)
    while i < n:
        c = code[i]
        if c == "/" and i + 1 < n and code[i + 1] == "/":
            _add(repairs, "comments")
            while i < n and code[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and code[i + 1] == "*":
            _add(repairs, "comments")
            end = code.find("*/", i + 2)
            i = n if end < 0 else end + 2
            out.append(" ")
            continue
        if c in _SMART:
            _add(repairs, "smart_quotes")
            out.append(_SMART[c])
            i += 1
            continue
        out.append(c)
        i += 1
    code = "".join(out)
    code = _MINUS_INF.sub(lambda m: (_add(repairs, "python_literals"), "null")[1], code)
    code = _PY_LIT.sub(
        lambda m: (_add(repairs, "python_literals"),
                   {"True": "true", "False": "false", "None": "null",
                    "NaN": "null", "Infinity": "null"}[m.group(1)])[1],
        code)

    def _key(m):
        _add(repairs, "bare_keys")
        return m.group(1) + '"' + m.group(2) + '"' + m.group(3)

    code = _BARE_KEY.sub(_key, code)

    def _tc(m):
        _add(repairs, "trailing_commas")
        return m.group(1)

    for _ in range(4):
        new = _TRAILING.sub(_tc, code)
        if new == code:
            break
        code = new
    return code


def json_repair(text):
    """Return (value, repairs). Raise RepairError when unrepairable."""
    if not isinstance(text, str) or not text.strip():
        raise RepairError("empty text")
    try:
        return json.loads(text), []
    except ValueError:
        pass
    repairs = []
    t = text
    if t.startswith("\ufeff"):
        t = t.lstrip("\ufeff")
        _add(repairs, "bom")
    t = t.strip()
    m = _FENCE.match(t)
    if m:
        t = m.group(1)
        _add(repairs, "markdown_fence")
    rebuilt = "".join(
        txt if kind == "str" else _fix_code(txt, repairs)
        for kind, txt in _split(t, repairs)
    )
    try:
        return json.loads(rebuilt), repairs
    except ValueError as e:
        first = next((c for c in rebuilt.splitlines() if c.strip()), None)
        if first and first.lstrip().startswith("{"):
            objs = []
            for ln in rebuilt.splitlines():
                s = ln.strip().rstrip(",")
                if not s:
                    continue
                try:
                    objs.append(json.loads(s))
                except ValueError:
                    objs = None
                    break
            if objs:
                _add(repairs, "jsonl_wrapped")
                return objs, repairs
        raise RepairError("unrepairable: %s" % (getattr(e, "msg", None) or e)) from None


# ------------------------------------------------------------------- diff

def _esc(seg):
    return str(seg).replace("~", "~0").replace("/", "~1")


def json_diff(a, b):
    """Structural diff: sorted list of {op, path, value|before/after}."""

    def eq(x, y):
        if isinstance(x, bool) != isinstance(y, bool):
            return False
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return x == y
        return type(x) is type(y) and x == y

    changes = []

    def walk(path, x, y):
        if isinstance(x, dict) and isinstance(y, dict):
            for k in x:
                p = path + "/" + _esc(k)
                if k not in y:
                    changes.append({"op": "removed", "path": p, "value": x[k]})
                else:
                    walk(p, x[k], y[k])
            for k in y:
                if k not in x:
                    changes.append({"op": "added", "path": path + "/" + _esc(k),
                                    "value": y[k]})
            return
        if isinstance(x, list) and isinstance(y, list):
            n = min(len(x), len(y))
            for i in range(n):
                walk(path + "/" + _esc(i), x[i], y[i])
            for i in range(n, len(y)):
                changes.append({"op": "added", "path": path + "/" + _esc(i), "value": y[i]})
            for i in range(n, len(x)):
                changes.append({"op": "removed", "path": path + "/" + _esc(i), "value": x[i]})
            return
        if not eq(x, y):
            changes.append({"op": "changed", "path": path, "before": x, "after": y})

    walk("", a, b)
    changes.sort(key=lambda c: (c["path"], c["op"]))
    return changes


# ------------------------------------------------------------------ patch

def _tokens(p, idx):
    if p == "":
        return []
    if not isinstance(p, str) or not p.startswith("/"):
        raise PatchError(idx, "invalid JSON pointer: %r" % (p,))
    return [s.replace("~1", "/").replace("~0", "~") for s in p[1:].split("/")]


def _get(doc, toks, idx, what):
    cur = doc
    for k in toks:
        if isinstance(cur, dict):
            if k not in cur:
                raise PatchError(idx, "%s: key not found: %s" % (what, k))
            cur = cur[k]
        elif isinstance(cur, list):
            if k == "-":
                raise PatchError(idx, "%s: cannot read '-'" % what)
            if not k.isdigit():
                raise PatchError(idx, "%s: invalid array index: %s" % (what, k))
            i = int(k)
            if i >= len(cur):
                raise PatchError(idx, "%s: index out of range: %d" % (what, i))
            cur = cur[i]
        else:
            raise PatchError(idx, "%s: parent is not a container" % what)
    return cur


def _parent(doc, toks, idx, what):
    return _get(doc, toks[:-1], idx, what)


def _insert(container, key, value, idx):
    if isinstance(container, dict):
        container[key] = value
        return
    if isinstance(container, list):
        if key == "-":
            container.append(value)
            return
        if not key.isdigit():
            raise PatchError(idx, "invalid array index: %s" % key)
        i = int(key)
        if i > len(container):
            raise PatchError(idx, "index out of range: %d" % i)
        container.insert(i, value)
        return
    raise PatchError(idx, "parent is not a container")


def _remove(container, key, idx):
    if isinstance(container, dict):
        if key not in container:
            raise PatchError(idx, "key not found: %s" % key)
        return container.pop(key)
    if isinstance(container, list):
        if not key.isdigit() or int(key) >= len(container):
            raise PatchError(idx, "invalid array index: %s" % key)
        return container.pop(int(key))
    raise PatchError(idx, "parent is not a container")


def _json_eq(x, y):
    if isinstance(x, bool) != isinstance(y, bool):
        return False
    return x == y


def json_patch(document, ops):
    """Apply an RFC 6902 patch; return the new document. Raise PatchError."""
    doc = copy.deepcopy(document)
    for idx, op in enumerate(ops):
        if not isinstance(op, dict) or "op" not in op:
            raise PatchError(idx, "each operation needs an 'op'")
        kind = op["op"]
        if kind not in ("add", "remove", "replace", "move", "copy", "test"):
            raise PatchError(idx, "unknown op: %r" % (kind,))
        path = op.get("path")
        if kind != "test" and not isinstance(path, str):
            raise PatchError(idx, "'path' must be a string")
        toks = _tokens(path if isinstance(path, str) else "", idx)
        if kind == "add":
            if "value" not in op:
                raise PatchError(idx, "add requires 'value'")
            if not toks:
                doc = copy.deepcopy(op["value"])
            else:
                _insert(_parent(doc, toks, idx, "add"), toks[-1],
                        copy.deepcopy(op["value"]), idx)
        elif kind == "remove":
            if not toks:
                raise PatchError(idx, "cannot remove the root")
            _remove(_parent(doc, toks, idx, "remove"), toks[-1], idx)
        elif kind == "replace":
            if "value" not in op:
                raise PatchError(idx, "replace requires 'value'")
            if not toks:
                doc = copy.deepcopy(op["value"])
            else:
                par = _parent(doc, toks, idx, "replace")
                key = toks[-1]
                if isinstance(par, dict):
                    if key not in par:
                        raise PatchError(idx, "key not found: %s" % key)
                    par[key] = copy.deepcopy(op["value"])
                elif isinstance(par, list):
                    if not key.isdigit() or int(key) >= len(par):
                        raise PatchError(idx, "invalid array index: %s" % key)
                    par[int(key)] = copy.deepcopy(op["value"])
                else:
                    raise PatchError(idx, "parent is not a container")
        elif kind in ("move", "copy"):
            src = op.get("from")
            if not isinstance(src, str):
                raise PatchError(idx, "%s requires a string 'from'" % kind)
            stoks = _tokens(src, idx)
            if not stoks:
                raise PatchError(idx, "cannot %s from the root" % kind)
            if kind == "move" and (path == src or path.startswith(src + "/")):
                raise PatchError(idx, "cannot move a location below itself")
            val = _get(doc, stoks, idx, kind)
            if kind == "copy":
                val = copy.deepcopy(val)
            else:
                val = _remove(_parent(doc, stoks, idx, kind), stoks[-1], idx)
            if not toks:
                doc = val
            else:
                _insert(_parent(doc, toks, idx, kind), toks[-1], val, idx)
        else:  # test
            cur = _get(doc, toks, idx, "test")
            if not _json_eq(cur, op.get("value")):
                raise PatchError(idx, "test failed at %s" % (path or "/root"))
    return doc


# -------------------------------------------------------------- canonical

def json_canonical(value, style="minified"):
    if style == "pretty":
        return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# ----------------------------------------------------------------- dedupe

def _norm_key(v, mode):
    if mode == "exact":
        return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    if not isinstance(v, str):
        v = json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    s = unicodedata.normalize("NFC", v)
    if mode == "text":
        return " ".join(s.split()).casefold()
    if mode == "email":
        local, sep, domain = s.partition("@")
        if not sep:
            return " ".join(s.split()).casefold()
        return "%s@%s" % (local.lower(), domain.lower().rstrip("."))
    if mode == "url":
        try:
            parts = urlsplit(s.strip())
            host = (parts.hostname or "").lower().rstrip(".")
            port = parts.port
        except ValueError:
            return " ".join(s.split()).casefold()
        scheme = parts.scheme.lower()
        netloc = host
        drop = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
        if port is not None and not drop:
            netloc = "%s:%d" % (host, port)
        path = parts.path
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")
        query = "&".join(sorted(p for p in parts.query.split("&") if p))
        return urlunsplit((scheme, netloc, path, query, ""))
    raise RepairError("unknown mode: %r" % (mode,))


def list_dedupe(items, mode="text"):
    """Dedupe keeping the first occurrence and the original item values."""
    if not isinstance(items, list):
        raise RepairError("items must be an array")
    seen = set()
    out = []
    for it in items:
        key = _norm_key(it, mode)
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out, len(items) - len(out)
