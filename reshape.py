"""Deterministic JSON reshaping: a declarative mapping + optional JSON Schema gate.

Pure functions. No LLM, no storage.

Mapping shape:
  {"fields": {
      "out_key": {"path": "a.b[0].c", "cast": "int", "default": 0,
                  "required": false, "each": {"fields": {...}}}
      or {"const": "literal"}
  }}

Paths: dot-separated keys, [n] for array indices, optional leading "$.".
Casts: int (truncates), float, str, bool, upper, lower, strip.
A missing path uses "default" when given; otherwise it is an error when
required (the default) and simply omitted when required=false.
"""

import json
import re


class MissingError(Exception):
    pass


_TOKEN = re.compile(r"\[(\d+)\]|([^\.\[\]]+)")


def parse_path(path):
    if not isinstance(path, str) or not path:
        raise MissingError("path must be a non-empty string")
    p = path[2:] if path.startswith("$.") else path
    toks = []
    i, n = 0, len(p)
    while i < n:
        m = _TOKEN.match(p, i)
        if not m:
            raise MissingError(f"invalid path syntax: {path!r}")
        toks.append(int(m.group(1)) if m.group(1) is not None else m.group(2))
        i = m.end()
        if i < n:
            if p[i] != ".":
                raise MissingError(f"invalid path syntax: {path!r}")
            i += 1
            if i == n:
                raise MissingError(f"trailing dot in path: {path!r}")
    if not toks:
        raise MissingError(f"invalid path: {path!r}")
    return toks


def resolve(root, toks):
    cur = root
    for t in toks:
        if isinstance(t, int):
            if not isinstance(cur, list) or not -len(cur) <= t < len(cur):
                raise MissingError(f"index {t} out of range")
            cur = cur[t]
        else:
            if not isinstance(cur, dict) or t not in cur:
                raise MissingError(f"key not found: {t}")
            cur = cur[t]
    return cur


def _cast(v, cast):
    if cast == "int":
        s = str(v).strip()
        try:
            return int(s)
        except ValueError:
            return int(float(s))  # "3.0" -> 3; "3.5" truncates to 3
    if cast == "float":
        return float(str(v).strip())
    if cast == "str":
        if isinstance(v, str):
            return v
        return json.dumps(v) if isinstance(v, (dict, list)) else str(v)
    if cast == "bool":
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        if s in ("true", "1", "yes", "y"):
            return True
        if s in ("false", "0", "no", "n"):
            return False
        raise ValueError(f"not a bool: {v!r}")
    if cast == "upper":
        return str(v).upper()
    if cast == "lower":
        return str(v).lower()
    if cast == "strip":
        return str(v).strip()
    raise ValueError(f"unknown cast: {cast}")


def reshape(inp, mapping):
    """Return (output, errors, defaults_used)."""
    if not isinstance(mapping, dict) or not isinstance(mapping.get("fields"), dict):
        return {}, [{"field": "$", "message": "mapping must have a fields object"}], []
    return _apply(inp, mapping["fields"], "")


def _apply(cur, fields, prefix):
    out = {}
    errors = []
    defaults = []
    for key, spec in fields.items():
        fname = f"{prefix}{key}"
        if not isinstance(spec, dict):
            errors.append({"field": fname, "message": "field spec must be an object"})
            continue
        if "const" in spec:
            out[key] = spec["const"]
            continue
        path = spec.get("path")
        if not path:
            errors.append({"field": fname, "message": "field spec needs path or const"})
            continue
        try:
            toks = parse_path(path)
        except MissingError as e:
            errors.append({"field": fname, "path": path, "message": str(e)})
            continue
        try:
            val = resolve(cur, toks)
        except MissingError:
            if "default" in spec:
                out[key] = spec["default"]
                defaults.append({"field": fname, "path": path})
            elif spec.get("required", True):
                errors.append({"field": fname, "path": path, "message": "missing"})
            continue
        if "each" in spec:
            if not isinstance(val, list):
                errors.append({"field": fname, "path": path,
                               "message": "each requires an array"})
                continue
            sub = spec["each"]
            if not isinstance(sub, dict) or not isinstance(sub.get("fields"), dict):
                errors.append({"field": fname,
                               "message": "each must be a mapping with fields"})
                continue
            items = []
            for i, item in enumerate(val):
                s, es, ds = _apply(item, sub["fields"], f"{fname}[{i}].")
                errors.extend(es)
                defaults.extend(ds)
                items.append(s)
            out[key] = items
            continue
        cast = spec.get("cast")
        if cast:
            try:
                val = _cast(val, cast)
            except (ValueError, TypeError) as e:
                errors.append({"field": fname, "path": path, "message": str(e)})
                continue
        out[key] = val
    return out, errors, defaults
