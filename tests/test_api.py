import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)
ROOT = Path(__file__).resolve().parent.parent

ROWS = [
    {"month": "Jan", "revenue": 1200, "product": "moovicut"},
    {"month": "Feb", "revenue": 1810, "product": "moovicut"},
    {"month": "Jan", "revenue": 940, "product": "petrel"},
    {"month": "Feb", "revenue": 1310, "product": "petrel"},
]


def test_chart_determinism():
    payload = {"kind": "bar", "x": "month", "y": "revenue", "series": "product",
               "title": "Revenue by product", "data": ROWS}
    r1 = client.post("/api/v1/chart", json=payload)
    r2 = client.post("/api/v1/chart", json=payload)
    assert r1.status_code == 200, r1.text
    b1, b2 = r1.json(), r2.json()
    assert b1["sha256"] == b2["sha256"]
    assert b1["sha256_png"] == b2["sha256_png"]
    assert b1["png_base64"] == b2["png_base64"]


def test_chart_spec_shape():
    r = client.post("/api/v1/chart", json={"x": "month", "y": "revenue", "data": ROWS})
    assert r.status_code == 200
    vega = r.json()["vega"]
    assert vega["mark"] == "bar"
    assert vega["encoding"]["y"]["aggregate"] == "sum"
    assert vega["encoding"]["x"]["type"] == "nominal"
    # input order preserved
    assert [v["month"] for v in vega["data"]["values"]] == \
        ["Jan", "Feb", "Jan", "Feb"]


def test_chart_csv_coercion():
    csv = "month,revenue,product\nJan,1200,moovicut\nFeb,1810,moovicut\n"
    r = client.post("/api/v1/chart",
                    json={"kind": "line", "x": "month", "y": "revenue", "csv": csv})
    assert r.status_code == 200, r.text
    vals = r.json()["vega"]["data"]["values"]
    assert vals[0]["revenue"] == 1200  # coerced from "1200"


def test_all_kinds_render():
    for kind in ["bar", "line", "area", "point", "step", "histogram", "pie"]:
        payload = ({"kind": "histogram", "x": "revenue", "data": ROWS}
                   if kind == "histogram" else
                   {"kind": kind, "x": "month", "y": "revenue", "data": ROWS})
        r = client.post("/api/v1/chart", json=payload)
        assert r.status_code == 200, f"{kind}: {r.text}"
        assert r.json()["png_bytes"] > 0


def test_chart_errors():
    # unknown kind
    r = client.post("/api/v1/chart", json={"x": "month", "y": "revenue",
                                          "data": ROWS, "kind": "scatter"})
    assert r.status_code == 400
    assert r.json()["error"] == "invalid_input"
    # missing y
    r = client.post("/api/v1/chart", json={"x": "month", "data": ROWS})
    assert r.status_code == 400
    # no data
    r = client.post("/api/v1/chart", json={"x": "month", "y": "revenue"})
    assert r.status_code == 400
    # bad column
    r = client.post("/api/v1/chart", json={"x": "nope", "y": "revenue", "data": ROWS})
    assert r.status_code == 400
    assert "column not found" in r.text
    # series unsupported for pie
    r = client.post("/api/v1/chart", json={"x": "month", "y": "revenue",
                                           "series": "product", "kind": "pie",
                                           "data": ROWS})
    assert r.status_code == 400


def test_reshape_basic():
    payload = {
        "input": {"person": {"name": "Davincc", "age": "44",
                             "tags": [{"t": "a", "v": "1"}, {"t": "b", "v": "2"}]}},
        "mapping": {"fields": {
            "name": {"path": "person.name"},
            "age": {"path": "person.age", "cast": "int"},
            "upper": {"path": "person.name", "cast": "upper"},
            "nick": {"path": "person.nickname", "default": "anon"},
            "tags": {"path": "person.tags",
                     "each": {"fields": {"key": {"path": "t"},
                                          "val": {"path": "v", "cast": "int"}}}},
        }},
    }
    r = client.post("/api/v1/reshape", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["output"] == {"name": "Davincc", "age": 44, "upper": "DAVINCC",
                              "nick": "anon",
                              "tags": [{"key": "a", "val": 1},
                                       {"key": "b", "val": 2}]}
    assert body["defaults_used"] == [{"field": "nick", "path": "person.nickname"}]
    r2 = client.post("/api/v1/reshape", json=payload)
    assert r2.json()["sha256"] == body["sha256"]


def test_reshape_errors():
    payload = {"input": {"a": 1}, "mapping": {"fields": {
        "x": {"path": "b.c"},  # missing, required
        "y": {"path": "a", "cast": "int"},
        "z": {"path": "a", "each": {"fields": {"q": {"path": "w"}}}},  # non-array
    }}}
    r = client.post("/api/v1/reshape", json=payload)
    assert r.status_code == 400
    fields = [e["field"] for e in r.json()["errors"]]
    assert "x" in fields and "z" in fields


def test_reshape_output_schema_gate():
    payload = {
        "input": {"person": {"name": "Davincc", "age": "44"}},
        "mapping": {"fields": {"age": {"path": "person.age", "cast": "int"}}},
        "outputSchema": {"type": "object", "required": ["age", "name"],
                         "properties": {"age": {"type": "integer"}}},
    }
    r = client.post("/api/v1/reshape", json=payload)
    assert r.status_code == 400
    assert r.json()["error"] == "schema_violation"
    assert r.json()["output"] == {"age": 44}


def test_validate():
    ok = client.post("/api/v1/validate", json={
        "payload": {"age": 44},
        "schema": {"type": "object", "required": ["age"],
                   "properties": {"age": {"type": "integer"}}}})
    assert ok.status_code == 200 and ok.json() == {"valid": True}
    bad = client.post("/api/v1/validate", json={
        "payload": {"age": "young"},
        "schema": {"type": "object", "required": ["age"],
                   "properties": {"age": {"type": "integer"}}}})
    assert bad.status_code == 400
    assert bad.json()["error"] == "schema_violation"


def test_openapi_and_index():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "/api/v1/chart" in r.json()["paths"]
    assert client.get("/").status_code == 200
    assert client.get("/SKILL.md").status_code == 200


def test_mcp():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert r.status_code == 200
    assert r.json()["result"]["serverInfo"]["name"] == "mechacut"
    # version single-source (consigne 24-11 : un serverInfo fige mentait de
    # 34 bundles — 0.93.0 vs manifest live). L'oracle est le manifest lui-meme.
    si_ver = r.json()["result"]["serverInfo"]["version"]
    manifest_ver = client.get("/agent/manifest").text.split(" ")[1]
    assert si_ver == manifest_ver, (si_ver, manifest_ver)
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert names[:3] == ["chart_from_data", "reshape_json", "validate_json"]
    assert "json_repair" in names and "format_convert" in names
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                  "params": {"name": "chart_from_data",
                                             "arguments": {"x": "month", "y": "revenue",
                                                           "data": ROWS}}})
    assert r.status_code == 200
    assert "sha256" in r.json()["result"]["content"][0]["text"]
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                                  "params": {"name": "nope", "arguments": {}}})
    assert r.json()["error"]["code"] == -32602


def test_rate_limit():
    main.HITS.clear()
    old = main.RATE_LIMIT
    main.RATE_LIMIT = 2
    try:
        assert client.post("/api/v1/validate",
                           json={"payload": {}, "schema": {}}).status_code == 200
        assert client.post("/api/v1/validate",
                           json={"payload": {}, "schema": {}}).status_code == 200
        assert client.post("/api/v1/validate",
                           json={"payload": {}, "schema": {}}).status_code == 429
    finally:
        main.RATE_LIMIT = old
        main.HITS.clear()


def test_golden_continuity():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "golden.py"), "check"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK" in r.stdout
