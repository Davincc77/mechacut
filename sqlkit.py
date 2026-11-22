"""sqlkit — /table/sql_dump : du CSV/JSON en SQL exécutable, RÈGLES DITES.

La douleur (r/AI_Agents 1x6gmnk, mot pour mot) : « a common pitfall …
identifier quoting. PostgreSQL uses double quotes, MySQL backticks…
specify which database engine the model is generating SQL for at the
time of creation ». Et le fil CVE-2026-32628 (dev.to) : « Three
connectors. Three databases. Zero parameterization. » — l'agent qui
écrit du SQL à la main casse les quotes ET les types, en silence.

Ce module ne devine jamais rien sans le déclarer :
  * chaque colonne rend son TYPE INFERÉ avec la RAISON et un ÉCHANTILLON ;
  * les identifiants hors grammaire fermée sont REFUSÉS par le nom
    (surface d'injection = zéro, pas d'échappement « ingénieux ») ;
  * le quoting des littéraux et des identifiants suit la spec publiée
    de chaque dialecte (PG §4.1.1, MySQL §9.1, SQLite §3.1) ;
  * l'oracle est le round-trip : le dump sqlite se recharge dans
    sqlite3 (stdlib) et re-requir == les données d'entrée (test_bundle41).

Set fermé : types INTEGER | REAL | TEXT (+ NULL). Pas de BOOLEAN, pas
de DATE, pas de timestamp : les dialectes n'ont pas la MÊME grammaire
pour ça — le dire vaut mieux qu'inventer un type commun.
"""
import csv
import io
import re

SQL_TYPES = ("INTEGER", "REAL", "TEXT")
DIALECTS = ("sqlite", "postgres", "mysql")

INT64_MIN = -9223372036854775808
INT64_MAX = 9223372036854775807

# MySQL utf8mb4 : VARCHAR max = 65535 octets par ligne ; une seule
# colonne large plafonne à 65535//4 = 16383 caractères (docs MySQL,
# String Data Type Overview). Au-delà : TEXT.
MYSQL_VARCHAR_MAX = 16383

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_INT_RE = re.compile(r"^-?\d+$")
_REAL_RE = re.compile(r"^-?\d+\.\d+$")

MAX_TEXT_SAMPLE = 60


class SqlDumpError(Exception):
    pass


# --------------------------------------------------------------- inputs

def _rows_from_csv(text, delimiter):
    if not isinstance(text, str) or not text.strip():
        raise SqlDumpError("csv is empty — nothing to dump")
    delim = delimiter
    if delim is None:
        try:
            delim = csv.Sniffer().sniff(text[:8000],
                                        delimiters=",;\t|").delimiter
            delim_note = "delimiter detected: %r (csv.Sniffer)" % delim
        except csv.Error:
            delim = ","
            delim_note = "no consistent delimiter found — default ','"
    else:
        delim_note = "delimiter given: %r" % delim
    try:
        grid = [r for r in csv.reader(io.StringIO(text, newline=""),
                                      delimiter=delim)]
    except csv.Error as e:
        raise SqlDumpError("csv is unparseable: %s (a NUL byte or an "
                           "unterminated quote cannot be dumped; refuse, "
                           "never repair — repair is csv/fix's job)" % e)
    blank = sum(1 for r in grid if not r or all(c == "" for c in r))
    grid = [r for r in grid if r and any(c != "" for c in r)]
    if len(grid) < 2:
        raise SqlDumpError("need a header line and at least one data row")
    header = grid[0]
    if len(set(header)) != len(header):
        raise SqlDumpError("duplicate column names in header: %s — "
                           "fix them upstream (csv/fix renames, this "
                           "module refuses)" % header)
    rows = []
    padded = 0
    for i, r in enumerate(grid[1:], start=2):
        if len(r) > len(header):
            raise SqlDumpError("row %d has %d cells for %d columns — "
                               "ragged CSV refused, not truncated"
                               % (i, len(r), len(header)))
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))
            padded += 1
            # short row: trailing cells become empty, and empty is
            # decided by empty_as_null below — same rule as JSON null.
        rows.append(dict(zip(header, r)))
    return rows, delim_note, blank, padded


def _rows_from_json(rows):
    if not isinstance(rows, list) or not rows:
        raise SqlDumpError("rows must be a non-empty list of objects")
    if not all(isinstance(r, dict) for r in rows):
        raise SqlDumpError("every row must be a JSON object")
    cols = list(rows[0].keys())
    if not cols:
        raise SqlDumpError("row 1 has no keys — no schema to derive")
    for i, r in enumerate(rows[1:], start=2):
        extra = [k for k in r if k not in cols]
        if extra:
            raise SqlDumpError("row %d has unknown column(s) %s — the "
                               "schema is row 1's keys, never a union "
                               "guessed later" % (i, extra))
    return rows, cols


# ------------------------------------------------------------- literals

def _quote_ident(name, dialect):
    if not isinstance(name, str) or not _IDENT_RE.match(name):
        raise SqlDumpError(
            "identifier %r rejected: closed grammar ^[A-Za-z_]"
            "[A-Za-z0-9_]*$ (<= 64 chars). No quoting-around of spaces, "
            "quotes or control bytes — that is where injection lives."
            % (name,))
    if len(name) > 64:
        raise SqlDumpError("identifier %r longer than 64 chars "
                           "(MySQL's hard limit — same rule everywhere)"
                           % name)
    if dialect == "mysql":
        return "`%s`" % name
    return '"%s"' % name


def _quote_text(value, dialect):
    # SQL standard doubles the single quote (PG §4.1.1, SQLite §3.1,
    # MySQL §9.1.1.1 accepts '' too). MySQL additionally treats '\' as
    # an escape lead unless NO_BACKSLASH_ESCAPES is set (docs MySQL
    # String Literals) — we default NO and double backslashes, saying
    # so in rules_applied.
    s = value.replace("'", "''")
    if dialect == "mysql":
        s = s.replace("\\", "\\\\")
    return "'%s'" % s


# --------------------------------------------------------- inference

def _cell_token(v):
    """Return (kind, token): kind in text|num|null|bool."""
    if v is None:
        return "null", ""
    if isinstance(v, bool):
        return "bool", "true" if v else "false"
    if isinstance(v, (int, float)):
        # Python str() on int/float round-trips exactly; JSON numbers
        # arrive as int/float. Tokens keep the source spelling.
        return "num", repr(v) if isinstance(v, float) else str(v)
    if isinstance(v, str):
        if "\x00" in v:
            raise SqlDumpError("NUL byte inside a value — SQL string "
                               "literals cannot carry it; refusing "
                               "instead of silently dropping")
        return "text", v
    raise SqlDumpError("unsupported JSON value type %s" % type(v).__name__)


def _looks_int(token):
    if not _INT_RE.match(token):
        return False
    if token != "0" and token.lstrip("-").startswith("0"):
        return False  # leading zeros — identifier, not number
    if token == "-0":
        return False  # signed zero: dialects normalize it to 0; keep the token
    return INT64_MIN <= int(token) <= INT64_MAX


def _looks_real(token):
    return bool(_REAL_RE.match(token))


def _infer_column(rows, col, empty_as_null):
    saw_int = saw_real = saw_text = saw_bool = False
    nulls = 0
    sample = []
    offenders = []
    width = 0
    for r in rows:
        kind, token = _cell_token(r.get(col))
        if kind == "null" or (kind == "text" and token == ""
                              and empty_as_null):
            nulls += 1
            continue
        if kind == "bool":
            saw_bool = True
            continue
        if kind == "text" and token == "":
            saw_text = True
            width = max(width, 0)
            continue
        if _looks_int(token):
            saw_int = True
        elif _looks_real(token):
            saw_real = True
        else:
            saw_text = True
            width = max(width, len(token))
        if len(sample) < MAX_TEXT_SAMPLE and token not in sample:
            sample.append(token)
    parts = sum([saw_int, saw_real, saw_text, saw_bool])
    if parts == 0:
        return {"type": "NULL",
                "reason": "all values null/empty — column typed NULL "
                          "is impossible; it becomes TEXT with a note",
                "nulls": nulls}
    mixed = parts > 1
    if saw_text:
        t = "TEXT"
        why = ["text present"]
        if saw_int or saw_real or saw_bool:
            why.append("widened to TEXT (only type that expresses "
                       "everything — never a coin flip)")
    elif saw_bool:
        t = "INTEGER"
        why = ["JSON booleans render as 1/0 — the one form every "
               "dialect in the closed set accepts (no shared BOOLEAN "
               "literal between PG and MySQL)"]
    elif saw_real:
        t = "REAL"
        why = ["every value matches ^-?\\d+\\.\\d+$"]
        if saw_int:
            why.append("integers absorbed into REAL (widening)")
    else:
        t = "INTEGER"
        why = ["every value matches ^-?\\d+$, no leading zeros, "
               "within int64"]
    if empty_as_null is False and nulls:
        why.append("empty cells are '' literals (empty_as_null=false)")
    return {"type": t, "reason": "; ".join(why), "nulls": nulls,
            "mixed": mixed, "sample": sample[:5], "width": width,
            "empty_as_null": empty_as_null}


# ---------------------------------------------------------------- dump

def dump(csv_text=None, rows=None, table="data", dialect="sqlite",
         create=True, if_not_exists=True, rows_per_statement=100,
         empty_as_null=False, types=None, delimiter=None,
         max_rows=10000):
    if dialect not in DIALECTS:
        raise SqlDumpError("dialect must be one of %s, got %r"
                           % (list(DIALECTS), dialect))
    if (csv_text is None) == (rows is None):
        raise SqlDumpError("give EXACTLY one input: csv (text) or rows "
                           "(list of objects) — never both, never none")
    delim_note = None
    blank = 0
    padded = 0
    if csv_text is not None:
        rows, delim_note, blank, padded = _rows_from_csv(csv_text,
                                                         delimiter)
        cols = list(rows[0].keys())
    else:
        rows, cols = _rows_from_json(rows)
    if len(rows) > max_rows:
        raise SqlDumpError("row count %d over max_rows=%d — split the "
                           "dump, this is a CPU-bound free tool, not a "
                           "database" % (len(rows), max_rows))
    if not isinstance(rows_per_statement, int) or not (
            1 <= rows_per_statement <= 1000):
        raise SqlDumpError("rows_per_statement must be an integer "
                           "1..1000 (chunk size is part of the output "
                           "contract)")

    overrides = types or {}
    if not isinstance(overrides, dict):
        raise SqlDumpError("types must be an object column->type")
    for k, v in overrides.items():
        if k not in cols:
            raise SqlDumpError("types override for unknown column %r "
                               "(columns: %s)" % (k, cols))
        if str(v).upper() not in SQL_TYPES:
            raise SqlDumpError("type override %r for %r outside the "
                               "closed set INTEGER|REAL|TEXT" % (v, k))

    colspecs = []
    for c in cols:
        inf = _infer_column(rows, c, empty_as_null)
        if c in overrides:
            chosen = str(overrides[c]).upper()
            inf = dict(inf)
            inf["reason"] = "overridden to %s by caller (inferred was " \
                            "%s: %s)" % (chosen, inf["type"],
                                         inf["reason"])
            inf["type"] = chosen
        colspecs.append({"column": c, **inf})

    # final type for SQL (NULL-impossible columns fall back to TEXT)
    for s in colspecs:
        if s["type"] == "NULL":
            s["type"] = "TEXT"
            s["note"] = "no non-empty value at all — TEXT kept"

    qtable = _quote_ident(table, dialect)
    qcols = [_quote_ident(s["column"], dialect) for s in colspecs]

    statements = []
    if create:
        ddl_cols = []
        for s, qc in zip(colspecs, qcols):
            t = s["type"]
            if t == "TEXT" and dialect == "mysql":
                w = s.get("width", 0)
                t = ("VARCHAR(%d)" % w if 0 < w <= MYSQL_VARCHAR_MAX
                     else "TEXT")
            ddl_cols.append("  %s %s" % (qc, t))
        head = "CREATE TABLE "
        if if_not_exists:
            head += "IF NOT EXISTS "
        statements.append(head + qtable + " (\n"
                          + ",\n".join(ddl_cols) + "\n);")

    col_list = ", ".join(qcols)
    n = 0
    chunk = []
    for r in rows:
        vals = []
        for s in colspecs:
            kind, token = _cell_token(r.get(s["column"]))
            if kind == "null" or (kind == "text" and token == ""
                                  and empty_as_null):
                vals.append("NULL")
            elif kind == "bool":
                vals.append("1" if token == "true" else "0")
            elif s["type"] in ("INTEGER", "REAL") and (
                    kind == "num" or (kind == "text" and (
                        _looks_int(token) or _looks_real(token)))):
                vals.append(token)  # source token, no float round-trip
            else:
                vals.append(_quote_text(token, dialect))
        chunk.append("(%s)" % ", ".join(vals))
        n += 1
        if len(chunk) == rows_per_statement:
            statements.append("INSERT INTO %s (%s) VALUES\n%s;"
                              % (qtable, col_list, ",\n".join(chunk)))
            chunk = []
    if chunk:
        statements.append("INSERT INTO %s (%s) VALUES\n%s;"
                          % (qtable, col_list, ",\n".join(chunk)))

    rules = [
        "1 identifiers: closed grammar ^[A-Za-z_][A-Za-z0-9_]*$, <=64 "
        "chars — anything else refused BY NAME (no quoting-around)",
        "2 types: closed set INTEGER|REAL|TEXT (+NULL). No BOOLEAN/DATE "
        "literal is shared by the three dialects, so none is invented",
        "3 leading zeros stay TEXT ('007' is an identifier, not a "
        "number); '-0' stays TEXT (dialects normalize signed zero)",
        "4 no exponent: '1e5' is TEXT (grammar ^-?\\d+\\.\\d+$ only)",
        "5 int64 range enforced: out-of-range integers -> TEXT, never "
        "silently wrapped",
        "6 mixed columns WIDEN (INTEGER+REAL->REAL, anything+TEXT->"
        "TEXT) and report mixed:true with samples — never a coin flip",
        "7 JSON booleans render as 1/0 integers (declared), not TRUE/"
        "FALSE keywords",
        "8 empty cells: '' literals unless empty_as_null=true -> NULL "
        "(mode echoed per column)",
        "9 numeric literals print as the SOURCE token — no float "
        "round-trip",
        "10 text literals: quote doubling '' (SQL standard, all three "
        "dialects)" + (" + backslash doubling (MySQL default mode)"
                       if dialect == "mysql" else ""),
        "11 NUL byte in a value -> refused by name (cannot live in a "
        "string literal)",
        "12 widths: mysql VARCHAR(observed max chars), >16383 -> TEXT "
        "(utf8mb4 row ceiling); postgres/sqlite TEXT; observed width "
        "always reported per column",
        "13 chunked inserts: rows_per_statement=%d (1..1000)"
        % rows_per_statement,
        "14 %s" % ("CREATE TABLE IF NOT EXISTS by default"
                   if (create and if_not_exists) else
                   ("CREATE TABLE emitted" if create
                    else "create=false: INSERTs only")),
    ]
    if delim_note:
        rules.append("15 %s" % delim_note)
        if padded:
            rules.append("16 short rows padded with empty cells: %d "
                         "(empties then follow rule 8)" % padded)

    out = {
        "table": table,
        "dialect": dialect,
        "columns": [
            {"name": s["column"], "type": s["type"],
             "inferred_reason": s["reason"], "mixed": s.get("mixed"),
             "nulls": s["nulls"], "sample": s.get("sample"),
             "text_width_observed": s.get("width"),
             **({"note": s["note"]} if s.get("note") else {})}
            for s in colspecs],
        "row_count": n,
        "statements": statements,
        "sql": "\n".join(statements),
        "rules_applied": rules,
        "discarded": {"blank_csv_rows_skipped": blank,
                      "short_rows_padded": padded},
        "create": create,
        "if_not_exists": if_not_exists,
        "rows_per_statement": rows_per_statement,
        "empty_as_null": empty_as_null,
        "sql_bytes": sum(len(s) + 1 for s in statements),
    }
    return out
