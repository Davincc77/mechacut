"""Deterministic CSV repair/typing/join, pivot/unpivot and format conversion.

Pure functions (stdlib + PyYAML + tomli-w for conversion). No LLM, no storage.
Same input -> same bytes. Output CSV/JSON/YAML use \\n line endings.
"""

import csv as _csv
import io
import json
import re

import yaml
import tomli_w

try:  # production runs 3.13; local venv may be 3.9
    import tomllib as _toml_read
except ImportError:  # pragma: no cover
    import tomli as _toml_read

from chart import coerce, parse_records


class TransformError(Exception):
    pass


# ---------------------------------------------------------------- csv/fix

_DELIMS = [",", ";", "\t", "|"]
_DELIM_LABEL = {",": ",", ";": ";", "\t": "tab", "|": "|"}


def _blank(cells):
    return not any(c.strip() for c in cells)


def csv_fix(text, preserve_delimiter=False):
    """Dirty CSV text -> clean comma-CSV + list of applied notes."""
    notes = []
    t = text
    if t.startswith("\ufeff"):
        t = t[1:]
        notes.append("bom_removed")
    if "\r\n" in t:
        t = t.replace("\r\n", "\n")
        notes.append("crlf_normalized")
    if "\r" in t:
        t = t.replace("\r", "\n")
        notes.append("cr_normalized")
    first = next((ln for ln in t.split("\n") if ln.strip()), "")
    plain = re.sub(r'"[^"]*"', "", first)
    counts = [plain.count(d) for d in _DELIMS]
    best = max(range(len(_DELIMS)), key=lambda i: counts[i])
    delim = _DELIMS[best] if counts[best] > 0 else ","
    if delim != ",":
        notes.append("delimiter_detected:%s" % _DELIM_LABEL[delim])
    try:
        rows = list(_csv.reader(io.StringIO(t), delimiter=delim))
    except _csv.Error as e:
        raise TransformError("csv parse error: %s" % e)
    while rows and _blank(rows[-1]):
        rows.pop()
    n0 = len(rows)
    rows = [r for r in rows if not _blank(r)]
    if len(rows) < n0:
        notes.append("blank_rows_removed:%d" % (n0 - len(rows)))
    if not rows:
        raise TransformError("csv is empty (no header row)")
    header = [h.strip() for h in rows[0]]
    if any(not h for h in header):
        header = [h if h else "col_%d" % (i + 1) for i, h in enumerate(header)]
        notes.append("empty_headers_named")
    counts_ = {}
    dup = False
    for i, h in enumerate(header):
        counts_[h] = counts_.get(h, 0) + 1
        if counts_[h] > 1:
            header[i] = "%s_%d" % (h, counts_[h])
            dup = True
    if dup:
        notes.append("duplicate_headers_renamed")
    width = len(header)
    padded = truncated = 0
    body = []
    for r in rows[1:]:
        cells = [c.strip() for c in r]
        if len(cells) < width:
            padded += 1
            cells += [""] * (width - len(cells))
        elif len(cells) > width:
            truncated += 1
            cells = cells[:width]
        body.append(cells)
    if padded:
        notes.append("short_rows_padded:%d" % padded)
    if truncated:
        notes.append("long_rows_truncated:%d" % truncated)
    out = io.StringIO()
    w = _csv.writer(out, delimiter="," if not preserve_delimiter else delim,
                    lineterminator="\n")
    w.writerow(header)
    w.writerows(body)
    return out.getvalue(), notes


# -------------------------------------------------------------- csv/types

_INT = re.compile(r"^[+-]?\d+$")
_FLOAT = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$")
_NULLS = {"", "null", "none", "nan", "n/a", "na", "-"}
_BOOLS = {"true": True, "false": False}


def _is_null(v):
    return v is None or (isinstance(v, str) and v.strip().lower() in _NULLS)


def _valid_date(s):
    try:
        y, m, d = (int(x) for x in s.split("-"))
        import datetime
        datetime.date(y, m, d)
        return True
    except ValueError:
        return False


def _classify(real):
    if all(isinstance(v, bool) for v in real):
        return "bool"
    if all(isinstance(v, int) for v in real):
        return "int"
    if all(isinstance(v, (int, float)) for v in real):
        return "float"
    if all(isinstance(v, str) for v in real):
        s = [v.strip() for v in real]
        if all(x.lower() in _BOOLS for x in s):
            return "bool"
        if all(_INT.match(x) for x in s):
            return "int"
        if all(_FLOAT.match(x) for x in s):
            return "float"
        if all(_DATE.match(x) and _valid_date(x) for x in s):
            return "date"
        if all(_DATETIME.match(x) for x in s):
            return "datetime"
    return "string"


def _convert(v, typ):
    if _is_null(v):
        return None
    if isinstance(v, str):
        w = v.strip()
        if typ == "bool":
            return _BOOLS[w.lower()]
        if typ == "int":
            return int(w)
        if typ == "float":
            return float(w)
    return v


def csv_types(rows):
    """Infer and coerce column types. Return (rows, columns report)."""
    if not rows:
        raise TransformError("no rows")
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    types = {}
    for k in cols:
        real = [r.get(k) for r in rows if not _is_null(r.get(k))]
        types[k] = _classify(real) if real else "null"
    out = [{k: _convert(r.get(k), types[k]) for k in cols} for r in rows]
    report = [{"name": k, "type": types[k],
               "nulls": sum(1 for r in rows if _is_null(r.get(k)))} for k in cols]
    return out, report


# -------------------------------------------------------------- csv/join

def _keyf(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _pair(on):
    if isinstance(on, str):
        return on, on
    if isinstance(on, list) and len(on) == 2 and all(isinstance(x, str) for x in on):
        return on[0], on[1]
    if isinstance(on, dict) and "left" in on and "right" in on:
        return str(on["left"]), str(on["right"])
    raise TransformError('on must be "col", ["lcol", "rcol"] '
                         'or {"left": ..., "right": ...}')


def _columns(rows):
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    return cols


def csv_join(left, right, on, how="inner"):
    """Join record tables. Overlapping columns: left wins. Rows missing the
    key simply never match. Returns (rows, counts)."""
    lk, rk = _pair(on)
    if not left or lk not in left[0]:
        raise TransformError("column not found: %s" % lk)
    if not right or rk not in right[0]:
        raise TransformError("column not found: %s" % rk)
    right_cols = _columns(right)
    left_cols = _columns(left)
    index = {}
    for i, r in enumerate(right):
        index.setdefault(_keyf(r.get(rk)), []).append(i)
    used = set()
    out = []
    matched = 0
    for l in left:
        hits = index.get(_keyf(l.get(lk)), []) if lk in l else []
        for j in hits:
            matched += 1
            used.add(j)
            merged = dict(right[j])
            merged.update(l)
            out.append(merged)
        if not hits and how in ("left", "outer"):
            merged = {k: None for k in right_cols}
            merged.update(l)
            out.append(merged)
    if how in ("right", "outer"):
        for j, r in enumerate(right):
            if j in used:
                continue
            merged = {k: None for k in left_cols}
            merged.update(r)
            out.append(merged)
    counts = {"left_rows": len(left), "right_rows": len(right),
              "matched": matched, "output_rows": len(out)}
    return out, counts


# ----------------------------------------------------------- table/pivot

_AGGS = ("sum", "count", "mean", "min", "max", "first")


def _agg(kind, vals, col):
    if kind == "count":
        return len(vals)
    nums = []
    kinds = set()
    for v in vals:
        n = coerce(v)
        if isinstance(n, bool) or not isinstance(n, (int, float)):
            raise TransformError("aggregation %s needs numeric values "
                                 "in column %r, got %r" % (kind, col, v))
        nums.append(n)
        kinds.add("int" if isinstance(n, int) else "float")
    if kind in ("min", "max"):
        return (min if kind == "min" else max)(nums)
    # P5 (sonde de contrat 22-11) : sum() en float pourrissait visible-
    # ment — 118.71000000000001 dans une cellule d'argent. Et le gold
    # B010 dit plus : « 1,10 + 2,20 = 3.30 » — la ZÉRO finale est du
    # contrat, pas un ornement. Règle de la maison : un nombre entré en
    # string ressort en string (le JSON ne sait pas distinguer 3.3 de
    # 3.30 — le mot, si). Decimal additionne les LITÉRAUX, la somme
    # porte les décimales max des entrées, exactement. Entrées
    # numériques : comportement inchangé (int reste int, float rendu
    # au double le plus proche de la somme EXACTE — le pourri change,
    # le correct ne bouge pas ; doctrine pins).
    from decimal import Decimal
    dec = [Decimal(v) if isinstance(v, str)
           else (Decimal(n) if isinstance(n, int) else Decimal(repr(n)))
           for v, n in zip(vals, nums)]
    tot = sum(dec, Decimal(0))
    if kind == "sum":
        # C'est le POINT qui porte le contrat : « 10 » sans décimale
        # reste un entier (les pins et les agents le comparent comme
        # tel) ; dès qu'une entrée affiche « . », l'échelle est une
        # affirmation — « 22.00 » n'est pas « 22 » — et le mot le
        # rend, pas le nombre.
        if any(isinstance(v, str) and "." in v for v in vals):
            return str(tot)
        if any(isinstance(v, str) for v in vals) and kinds == {"int"}:
            return int(tot)
        if any(isinstance(v, str) for v, n in zip(vals, nums)
               if isinstance(n, float)):
            return float(tot)
        if kinds == {"int"}:
            return int(tot)
        if kinds == {"int"}:
            return int(tot)
        return float(tot)
    # mean : division exacte, rendu numérique (le contrat des chaînes
    # est celui de la SOMME ; la moyenne n'a pas de forme littérale).
    return float(tot / Decimal(len(dec)))


def table_pivot(rows, index, columns, values, agg="sum"):
    idxs = [index] if isinstance(index, str) else index
    if not idxs:
        raise TransformError("index is required (string or list of strings)")
    need = idxs + [columns, values]
    for r in rows:
        for c in need:
            if c not in r:
                raise TransformError("column not found: %s" % c)
    groups = {}
    col_set = []
    idx_order = []
    seen = set()
    for r in rows:
        ik = tuple(_keyf(r[c]) for c in idxs)
        if ik not in seen:
            seen.add(ik)
            idx_order.append((ik, tuple(r[c] for c in idxs)))
        cv = str(r[columns])
        if cv not in col_set:
            col_set.append(cv)
        if r[values] is not None and not _is_null(r[values]):
            groups.setdefault((ik, cv), []).append(r[values])
    out = []
    for ik, iv in idx_order:
        row = {}
        for name, val in zip(idxs, iv):
            row[name] = val
        for cv in sorted(col_set):
            vals = groups.get((ik, cv))
            if not vals:
                row[cv] = None
            elif agg == "first":
                row[cv] = vals[0]
            else:
                row[cv] = _agg(agg, vals, values)
        out.append(row)
    return out


def table_unpivot(rows, keep=None, var_cols=None,
                  var_name="variable", value_name="value"):
    if not rows:
        raise TransformError("no rows")
    allcols = _columns(rows)
    if var_cols:
        vs = list(var_cols)
        ks = keep or [c for c in allcols if c not in vs]
    elif keep:
        ks = list(keep)
        vs = var_cols or [c for c in allcols if c not in ks]
    else:
        raise TransformError("send keep (columns to retain) or vars "
                             "(columns to melt)")
    for c in ks + vs:
        if c not in allcols:
            raise TransformError("column not found: %s" % c)
    if not vs:
        raise TransformError("no columns to unpivot")
    out = []
    for r in rows:
        for v in vs:
            row = {k: r.get(k) for k in ks}
            row[var_name] = v
            row[value_name] = r.get(v)
            out.append(row)
    return out


# ------------------------------------------------------- format/convert

FORMATS = ("json", "yaml", "toml", "csv", "env")
_ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ENV_SAFE = re.compile(r"^[A-Za-z0-9_@%+=:,./-]+$")


def _jsonify(o):
    if isinstance(o, dict):
        return {str(k): _jsonify(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonify(v) for v in o]
    if isinstance(o, bool) or o is None or isinstance(o, (int, float, str)):
        return o
    if hasattr(o, "isoformat"):
        return o.isoformat()
    return str(o)


def _deep_sorted(x):
    if isinstance(x, dict):
        return {k: _deep_sorted(x[k]) for k in sorted(x)}
    if isinstance(x, list):
        return [_deep_sorted(v) for v in x]
    return x


def format_parse(text, fmt):
    if fmt == "json":
        try:
            return json.loads(text)
        except ValueError as e:
            raise TransformError("json: %s" % e)
    if fmt == "yaml":
        try:
            return _jsonify(yaml.safe_load(text))
        except yaml.YAMLError as e:
            raise TransformError("yaml: %s" % e)
    if fmt == "toml":
        try:
            return _jsonify(_toml_read.loads(text))
        except Exception as e:
            raise TransformError("toml: %s" % e)
    if fmt == "env":
        out = {}
        for n, ln in enumerate(text.splitlines(), 1):
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            k, sep, v = s.partition("=")
            if not sep:
                raise TransformError("env line %d: expected KEY=VALUE, got %r" % (n, ln))
            k = k.strip()
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            out[k] = v
        return out
    if fmt == "csv":
        try:
            rows = parse_records(csv_text=text)
        except Exception as e:
            raise TransformError("csv: %s" % e)
        typed, _ = csv_types(rows)
        return typed
    raise TransformError("unknown source format: %r" % (fmt,))


def format_dump(value, fmt):
    if fmt == "json":
        return json.dumps(_jsonify(value), sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False)
    if fmt == "yaml":
        try:
            return yaml.safe_dump(_jsonify(value), sort_keys=True,
                                  allow_unicode=True, default_flow_style=False)
        except yaml.YAMLError as e:
            raise TransformError("yaml: %s" % e)
    if fmt == "toml":
        v = _jsonify(value)
        if not isinstance(v, dict):
            raise TransformError("toml requires a top-level object")
        try:
            return tomli_w.dumps(_deep_sorted(v))
        except TypeError as e:
            raise TransformError("toml: %s" % e)
    if fmt == "env":
        if not isinstance(value, dict):
            raise TransformError("env requires an object")
        lines = []
        for k in sorted(value):
            v = value[k]
            if isinstance(v, bool):
                s = "true" if v else "false"
            elif isinstance(v, (int, float)):
                s = json.dumps(v)
            elif v is None:
                s = ""
            elif isinstance(v, str):
                s = v
            else:
                raise TransformError("env requires flat scalar values "
                                     "(key %r holds %s)" % (k, type(v).__name__))
            if not _ENV_KEY.match(k):
                raise TransformError("env invalid key: %r" % k)
            if s == "" or not _ENV_SAFE.match(s):
                s = "'" + s.replace("'", "'\\''") + "'"
            lines.append("%s=%s" % (k, s))
        return "\n".join(lines) + ("\n" if lines else "")
    if fmt == "csv":
        v = _jsonify(value)
        if not isinstance(v, list) or not v or not all(isinstance(r, dict) for r in v):
            raise TransformError("csv target requires a non-empty array of objects")
        cols = _columns(v)
        buf = io.StringIO()
        w = _csv.writer(buf, lineterminator="\n")
        w.writerow(cols)
        for r in v:
            buf_row = []
            for c in cols:
                cell = r.get(c)
                if cell is None:
                    cell = ""
                elif isinstance(cell, (dict, list)):
                    cell = json.dumps(cell, sort_keys=True,
                                      separators=(",", ":"), ensure_ascii=False)
                elif isinstance(cell, bool):
                    cell = "true" if cell else "false"
                buf_row.append(cell)
            w.writerow(buf_row)
        return buf.getvalue()
    raise TransformError("unknown target format: %r" % (fmt,))


def format_convert(text, source, target):
    return format_dump(format_parse(text, source), target)

# ------------------------------------------------ bundle 30 lot 2
_INT_RE = re.compile(r"^-?\d+$")
_DEC_RE = re.compile(r"^-?\d+\.\d+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BOOL_SET = {"true", "false", "yes", "no", "0", "1"}


def _cell_kind(v):
    if _INT_RE.match(v):
        return "integer"
    if _DEC_RE.match(v):
        return "decimal"
    if _DATE_RE.match(v):
        return "date-iso"
    if v.lower() in _BOOL_SET:
        return "boolean"
    return "string"


def table_peek(rows):
    """Column profile from a closed classifier — types, nulls, uniques,
    bounds for numerics. This is counting, not NLP: any column that
    mixes shapes comes back 'string' with mixed=True, never a guess."""
    if not isinstance(rows, list) or not rows:
        raise TransformError("rows: non-empty list of objects required")
    if not all(isinstance(r, dict) for r in rows):
        raise TransformError("every row must be an object")
    cols = []
    seen = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                cols.append(k)
    out = []
    for c in cols:
        vals = []
        nulls = 0
        for r in rows:
            v = r.get(c)
            if v is None or (isinstance(v, str) and v.strip() == ""):
                nulls += 1
            else:
                vals.append(v if isinstance(v, str) else str(v))
        kinds = {_cell_kind(v) for v in vals}
        if not vals:
            t = "empty"
        elif len(kinds) == 1:
            t = kinds.pop()
        else:
            t = "string"
        col = {"column": c, "n": len(rows), "nulls": nulls,
               "type": t}
        if len(kinds) > 1:
            col["mixed"] = True
        uniq = len(set(vals))
        col["uniques"] = uniq
        if t == "integer" or t == "decimal":
            num = sorted(float(v) for v in vals)
            col["min"] = num[0]
            col["max"] = num[-1]
        elif t == "date-iso":
            ds = sorted(vals)
            col["min"] = ds[0]
            col["max"] = ds[-1]
        out.append(col)
    return {"columns": out, "rows": len(rows)}


def csv_diff(left, right, key):
    """Row-level diff on a key: added / removed / changed (per-field
    pointers) + same_count. Keys are compared as strings; duplicate key
    rows are refused, not silently collapsed."""
    for name, rows in (("left", left), ("right", right)):
        if not isinstance(rows, list) or not all(
                isinstance(r, dict) for r in rows):
            raise TransformError("%s must be a list of objects" % name)
    keys = [key] if isinstance(key, str) else key
    if not keys:
        raise TransformError("key required (field name or list)")

    def kof(r, side):
        miss = [k for k in keys if k not in r]
        if miss:
            raise TransformError("%s row missing key field(s): %s"
                             % (side, ", ".join(miss)))
        return "\x1f".join(str(r[k]) for k in keys)

    def norm(v):
        if v is None:
            return None
        return v if isinstance(v, (int, float, bool)) else str(v)

    lmap, rmap, order_l, order_r = {}, {}, [], []
    for r in left:
        k = kof(r, "left")
        if k in lmap:
            raise TransformError("duplicate key in left: %s" % k.replace(
                "\x1f", "|"))
        lmap[k] = r
        order_l.append(k)
    for r in right:
        k = kof(r, "right")
        if k in rmap:
            raise TransformError("duplicate key in right: %s" % k.replace(
                "\x1f", "|"))
        rmap[k] = r
        order_r.append(k)
    removed = [k.replace("\x1f", "|") for k in order_l if k not in rmap]
    added = [k.replace("\x1f", "|") for k in order_r if k not in lmap]
    changed = []
    same = 0
    for k in order_l:
        if k not in rmap:
            continue
        a, bb = lmap[k], rmap[k]
        fields = []
        for f in sorted(set(a) | set(bb)):
            if f in keys:
                continue
            x, y = norm(a.get(f)), norm(bb.get(f))
            if isinstance(x, float) and isinstance(y, int):
                y = float(y)
            if isinstance(y, float) and isinstance(x, int):
                x = float(x)
            if x != y:
                fields.append({"field": f, "left": x, "right": y})
        if fields:
            changed.append({"key": k.replace("\x1f", "|"),
                            "fields": fields})
        else:
            same += 1
    return {"added": added, "removed": removed, "changed": changed,
            "same_count": same,
            "counts": {"added": len(added), "removed": len(removed),
                       "changed": len(changed)},
            "key_fields": keys}
