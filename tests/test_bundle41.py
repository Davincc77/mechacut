"""Bundle 41 — /table/sql_dump : le dump SQL qui DIT ses règles.

Toutes les attentes sont CALCULÉES : à la main depuis les specs
publiées (PG §4.1.1 / §4.1.3, MySQL §9.1.1.1 littéraux + §9.1.1.4
identifiants + String Data Types VARCHAR 65535/4, SQLite §3.1), ou
par l'ORACLE sqlite3 (stdlib) en round-trip — jamais recopiées de la
sortie du module. mysql/postgres n'ont pas d'oracle local : leurs
vecteurs sont écrits à la main, c'est déclaré dans chaque test.
"""
import sqlite3

import pytest
from fastapi.testclient import TestClient

import main
import sqlkit
from sqlkit import SqlDumpError, dump

client = TestClient(main.app)
URL = "/api/v1/table/sql_dump"

INT64_MAX = 9223372036854775807
INT64_MIN = -9223372036854775808


def _exec_sqlite(out):
    db = sqlite3.connect(":memory:")
    for s in out["statements"]:
        db.execute(s)
    return db


# ---------------------------------------------------------------- oracle

def test_sqlite_roundtrip_hand_computed():
    # CSV input, expected tuples computed BY HAND:
    #   id    all ^-?\d+$ no leading zero -> INTEGER -> sqlite ints
    #   name  text -> TEXT; sqlite has NO backslash escapes: verbatim
    #   qty   '007' forces the column TEXT -> every value quoted
    #   price int+real mix -> REAL; 10 stored bare -> REAL affinity 10.0
    #   note  empty_as_null=false -> '' literal
    out = dump(csv_text="id,name,qty,price,note\n"
                        "1,O'Brien,3,1.50,hello\n"
                        "2,Back\\slash,007,10,\n"
                        "3,caf\u00e9,12,2.5,\n",
               table="orders", dialect="sqlite", rows_per_statement=2)
    got = _exec_sqlite(out).execute(
        "SELECT id,name,qty,price,note FROM orders ORDER BY id"
    ).fetchall()
    assert got == [
        (1, "O'Brien", "3", 1.5, "hello"),
        (2, "Back\\slash", "007", 10.0, ""),
        (3, "caf\u00e9", "12", 2.5, ""),
    ]


def test_roundtrip_nulls_and_booleans():
    # JSON null -> NULL keyword; bool -> INTEGER 1/0 (rule 7); empty_as_null
    # turns '' into NULL too. Expected values written by hand.
    out = dump(rows=[{"a": 1, "v": True, "e": ""},
                     {"a": 2, "v": False, "e": None}],
               table="t", empty_as_null=True)
    got = _exec_sqlite(out).execute("SELECT a,v,e FROM t ORDER BY a"
                                    ).fetchall()
    assert got == [(1, 1, None), (2, 0, None)]


def test_roundtrip_date_stays_text_no_invented_type():
    # No shared DATE literal grammar across the three dialects -> TEXT.
    out = dump(rows=[{"d": "2026-11-22"}, {"d": "2026-01-01"}], table="t")
    assert out["columns"][0]["type"] == "TEXT"
    got = _exec_sqlite(out).execute("SELECT d FROM t ORDER BY d").fetchall()
    assert got == [("2026-01-01",), ("2026-11-22",)]


# ------------------------------------------------------------- vectors

def test_quote_doubling_sql_standard():
    # PG §4.1.1 / MySQL §9.1.1.1 / SQLite §3.1: '' escapes the quote.
    out = dump(rows=[{"s": "it's"}], table="t")
    assert "'it''s'" in out["statements"][-1]


def test_mysql_doubles_backslash_hand_vector():
    # MySQL default mode (NO_BACKSLASH_ESCAPES off, docs String Literals):
    # one backslash in data -> two in the literal. Hand-written:
    # value  a\b  -> literal 'a\\b'  (two backslash chars in the SQL text)
    out = dump(rows=[{"s": "a\\b"}], table="t", dialect="mysql")
    assert "('a\\\\b')" in out["statements"][-1]  # Python: \\\\ == two chars
    # postgres and sqlite must NOT double it:
    out2 = dump(rows=[{"s": "a\\b"}], table="t", dialect="postgres")
    assert "('a\\b')" in out2["statements"][-1]


def test_identifier_quoting_per_dialect_hand_vectors():
    # PG/SQLite: "double" (identifiers folded to lowercase unless quoted —
    # we ALWAYS quote, declared); MySQL: backticks (docs §9.1.1.4).
    r = dump(rows=[{"Order": 1}], table="data", dialect="postgres")
    assert '"Order"' in r["statements"][0]
    m = dump(rows=[{"Order": 1}], table="data", dialect="mysql")
    assert "`Order`" in m["statements"][0]
    # quoting keeps case: "Order" != order — the reason we quote always
    assert r["rules_applied"][0].startswith("1 identifiers")


@pytest.mark.parametrize("bad", ["or ders", "1table", "a-b", "a\"b",
                                 "a`b", "a'b", "", "x" * 65])
def test_identifiers_outside_closed_grammar_refused_by_name(bad):
    with pytest.raises(SqlDumpError) as e:
        dump(rows=[{"a": 1}], table=bad)
    assert "refused" not in str(e.value) or "rejected" in str(e.value)
    assert "closed grammar" in str(e.value) or "64 chars" in str(e.value)


@pytest.mark.parametrize("bad", ["a b", "a;b", "drop table", "a\x01"])
def test_column_names_refused_by_name(bad):
    with pytest.raises(SqlDumpError) as e:
        dump(rows=[{bad: 1}], table="t")
    assert "rejected" in str(e.value)


def test_nul_refused_csv_and_json():
    # SQL string literals cannot carry NUL -> refuse, never drop silently.
    with pytest.raises(SqlDumpError) as e:
        dump(csv_text="a,b\n1,x\x00y\n", table="t")
    assert "NUL" in str(e.value) or "unparseable" in str(e.value)
    with pytest.raises(SqlDumpError) as e:
        dump(rows=[{"a": "x\x00y"}], table="t")
    assert "NUL" in str(e.value)


# ------------------------------------------------------------- typing

def test_leading_zeros_and_signed_zero_stay_text():
    out = dump(rows=[{"a": "007", "b": "-0", "c": "0", "d": "-42"}],
               table="t")
    types = {c["name"]: c["type"] for c in out["columns"]}
    assert types == {"a": "TEXT", "b": "TEXT", "c": "INTEGER",
                     "d": "INTEGER"}
    # '007' and '-0' come back quoted, 0 and -42 bare:
    assert out["statements"][-1].endswith(
        "VALUES\n('007', '-0', 0, -42);")


def test_exponent_not_in_real_grammar():
    # REAL grammar is ^-?\d+\.\d+$ only (docs of the closed set): '1e5'
    # would need scientific literals — stays TEXT, declared.
    out = dump(rows=[{"a": "1e5", "b": "1.5", "c": ".5", "d": "5."}],
               table="t")
    types = {c["name"]: c["type"] for c in out["columns"]}
    assert types == {"a": "TEXT", "b": "REAL", "c": "TEXT", "d": "TEXT"}


def test_int64_bounds_never_wrapped():
    out = dump(rows=[{"lo": INT64_MIN, "hi": INT64_MAX,
                      "over": INT64_MAX + 1, "under": INT64_MIN - 1}],
               table="t")
    types = {c["name"]: c["type"] for c in out["columns"]}
    assert types == {"lo": "INTEGER", "hi": "INTEGER", "over": "TEXT",
                     "under": "TEXT"}


def test_mixed_widens_and_reports():
    # int + real -> REAL (widening); anything + text -> TEXT, mixed:true
    out = dump(rows=[{"a": "1", "b": "1"}, {"a": "2.5", "b": "x"}],
               table="t")
    by = {c["name"]: c for c in out["columns"]}
    assert by["a"]["type"] == "REAL" and by["a"]["mixed"] is True
    assert by["b"]["type"] == "TEXT" and by["b"]["mixed"] is True
    assert by["b"]["inferred_reason"].startswith("text present")


def test_types_override_echoes_the_inference():
    out = dump(rows=[{"n": "42"}], table="t", types={"n": "TEXT"})
    col = out["columns"][0]
    assert col["type"] == "TEXT"
    assert "overridden to TEXT by caller" in col["inferred_reason"]
    assert "inferred was INTEGER" in col["inferred_reason"]
    assert "'42'" in out["statements"][-1]
    with pytest.raises(SqlDumpError):
        dump(rows=[{"n": "42"}], table="t", types={"n": "BOOLEAN"})
    with pytest.raises(SqlDumpError):
        dump(rows=[{"n": "42"}], table="t", types={"zz": "TEXT"})


def test_mysql_varchar_widths_hand_computed():
    # longest text cell 'hello' = 5 chars -> VARCHAR(5); a 16384-char
    # value passes the utf8mb4 ceiling 16383 (65535/4) -> TEXT.
    out = dump(csv_text="a,b\nhello,x\n" + "y" * 16384 + ",z\n",
               table="t", dialect="mysql")
    ddl = out["statements"][0]
    assert '"a"'.replace('"', "`") in ddl  # mysql backticks
    assert "`a` TEXT" in ddl               # >16383 -> TEXT
    assert "`b` VARCHAR(1)" in ddl


def test_postgres_and_sqlite_stay_text():
    out = dump(csv_text="a\nhello\n", table="t", dialect="postgres")
    assert '"a" TEXT' in out["statements"][0]
    assert out["columns"][0]["text_width_observed"] == 5  # still reported


# ------------------------------------------------------------- input

def test_exactly_one_input():
    with pytest.raises(SqlDumpError) as e:
        dump(table="t")
    assert "EXACTLY one input" in str(e.value)
    with pytest.raises(SqlDumpError):
        dump(csv_text="a\n1\n", rows=[{"a": 1}], table="t")


def test_ragged_csv_refused_not_truncated():
    with pytest.raises(SqlDumpError) as e:
        dump(csv_text="a,b\n1,2,3\n", table="t")
    assert "ragged CSV refused" in str(e.value)


def test_short_rows_padded_and_said():
    out = dump(csv_text="a,b,c\n1,2\n", table="t")
    assert out["discarded"]["short_rows_padded"] == 1
    assert any("padded" in r for r in out["rules_applied"])
    assert out["statements"][-1].rstrip(";").endswith(", '')")


def test_blank_rows_skipped_and_counted():
    out = dump(csv_text="a,b\n1,2\n\n3,4\n", table="t")
    assert out["discarded"]["blank_csv_rows_skipped"] == 1
    assert out["row_count"] == 2


def test_duplicate_headers_refused():
    with pytest.raises(SqlDumpError) as e:
        dump(csv_text="a,a\n1,2\n", table="t")
    assert "duplicate column names" in str(e.value)


def test_json_schema_is_row1_never_a_union():
    with pytest.raises(SqlDumpError) as e:
        dump(rows=[{"a": 1}, {"a": 2, "b": 3}], table="t")
    assert "row 2 has unknown column(s)" in str(e.value)


def test_empty_inputs_refused():
    with pytest.raises(SqlDumpError):
        dump(csv_text="", table="t")
    with pytest.raises(SqlDumpError):
        dump(csv_text="only,header\n", table="t")
    with pytest.raises(SqlDumpError):
        dump(rows=[], table="t")


def test_max_rows_cpu_bound():
    with pytest.raises(SqlDumpError) as e:
        dump(rows=[{"a": i} for i in range(10001)], table="t")
    assert "max_rows" in str(e.value)


def test_chunking_100_100_50():
    out = dump(rows=[{"n": i} for i in range(250)], table="t")
    ins = [s for s in out["statements"] if s.startswith("INSERT")]
    assert len(ins) == 3
    counts = [len([l for l in s.splitlines() if l.startswith("(")])
              for s in ins]
    assert counts == [100, 100, 50]


def test_chunk_bounds_refused():
    for bad in (0, 1001, "x"):
        with pytest.raises((SqlDumpError, ValueError)):
            dump(rows=[{"a": 1}], table="t", rows_per_statement=bad)


def test_dialect_closed_set():
    with pytest.raises(SqlDumpError) as e:
        dump(rows=[{"a": 1}], table="t", dialect="oracle")
    assert "sqlite" in str(e.value)


def test_create_and_if_not_exists_switches_said():
    a = dump(rows=[{"a": 1}], table="t", create=False)
    assert not any(s.startswith("CREATE") for s in a["statements"])
    assert "INSERTs only" in a["rules_applied"][13]
    b = dump(rows=[{"a": 1}], table="t", if_not_exists=False)
    assert b["statements"][0].startswith("CREATE TABLE \"t\"")
    c = dump(rows=[{"a": 1}], table="t")
    assert c["statements"][0].startswith("CREATE TABLE IF NOT EXISTS")


def test_delimiter_note_declared():
    out = dump(csv_text="a;b\n1;2\n", table="t")
    assert any("delimiter" in r for r in out["rules_applied"])
    assert out["columns"][0]["name"] == "a"  # ';' sniffed, not ','


# ---------------------------------------------------------------- api

def test_api_determinism_and_fields():
    body = {"csv": "id,name\n1,O'Brien\n2,café\n", "table": "orders"}
    r1 = client.post(URL, json=body)
    r2 = client.post(URL, json=body)
    assert r1.status_code == 200
    assert r1.content == r2.content  # same request, same bytes, forever
    b = r1.json()
    assert set(["table", "dialect", "columns", "row_count", "statements",
                "sql", "rules_applied", "sha256"]) <= set(b)


def test_api_error_is_named_400():
    r = client.post(URL, json={"table": "or ders",
                               "rows": [{"a": 1}]})
    assert r.status_code == 400
    assert "closed grammar" in r.json()["errors"][0]["message"]


def test_mcp_tool_registered():
    names = [t["name"] for t in main.MCP_TOOLS]
    assert "table_sql_dump" in names
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/call",
                                  "params": {"name": "table_sql_dump",
                                             "arguments":
                                                 {"rows": [{"a": "1"}],
                                                  "table": "t"}}})
    assert r.status_code == 200
