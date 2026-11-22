"""Bundle 2 — code editing: behavior, round-trips, determinism."""

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _deterministic(url, payload):
    r1 = client.post(url, json=payload)
    r2 = client.post(url, json=payload)
    assert r1.status_code == r2.status_code
    assert r1.content == r2.content  # same request, same bytes
    return r1


# ------------------------------------------------------------- text/patch

def test_patch_unique_gate():
    r = _deterministic("/api/v1/text/patch", {
        "text": "x = one()\ny = one()",
        "edits": [{"find": "one()", "replace": "two()"}]})
    assert r.status_code == 400
    b = r.json()
    assert b["error"] == "edit_failed"
    assert "found 2 occurrence" in b["errors"][0]["message"]
    assert "expected" in b["errors"][0]


def test_patch_all_and_exact_counts():
    r = client.post("/api/v1/text/patch", json={
        "text": "x = one()\ny = one()",
        "edits": [{"find": "one()", "replace": "two()",
                   "occurrences": "all"}]})
    assert r.json()["output"] == "x = two()\ny = two()"
    assert r.json()["changed"] is True
    r = client.post("/api/v1/text/patch", json={
        "text": "aa", "edits": [{"find": "a", "replace": "b",
                                 "occurrences": 2}]})
    assert r.json()["output"] == "bb"
    r = client.post("/api/v1/text/patch", json={
        "text": "aa", "edits": [{"find": "a", "replace": "b",
                                 "occurrences": 3}]})
    assert r.status_code == 400


def test_patch_sequential():
    r = client.post("/api/v1/text/patch", json={
        "text": "def f(): return 1",
        "edits": [{"find": "def f", "replace": "def g"},
                  {"find": "return 1", "replace": "return 2"}]})
    assert r.json()["output"] == "def g(): return 2"
    assert r.json()["edits_applied"] == 2


# -------------------------------------------------------------- text/diff

def test_diff_roundtrip_property():
    a = "l1\nl2\nl3\nl4\nl5\nl6\nl7\n"
    b = "l1\nl2\nX\nl4\nl5\nl6\nl7\nl8\n"
    r = _deterministic("/api/v1/text/diff", {"a": a, "b": b, "context": 1})
    d = r.json()
    assert d["identical"] is False
    assert d["hunks"] == 2
    assert d["added"] == 2 and d["removed"] == 1
    # what Mechacut diffs, Mechacut can re-apply:
    back = client.post("/api/v1/text/apply-diff",
                       json={"text": a, "diff": d["diff"]})
    assert back.status_code == 200, back.text
    assert back.json()["output"] == b


def test_diff_identical():
    r = client.post("/api/v1/text/diff", json={"a": "x\n", "b": "x\n"})
    b = r.json()
    assert b["identical"] is True and b["diff"] == ""


# --------------------------------------------------------- text/apply-diff

def test_apply_strict_rejects_drift():
    diff = "--- before\n+++ after\n@@ -1,2 +1,2 @@\n l1\n-l2\n+X\n"
    r = client.post("/api/v1/text/apply-diff",
                    json={"text": "l1\nTOTALLY DIFFERENT\n", "diff": diff})
    assert r.status_code == 400
    b = r.json()
    assert b["error"] == "apply_failed"
    assert "hunk 0" in b["errors"][0]["message"]


def test_apply_multi_hunk_delta():
    a = "\n".join("line%d" % i for i in range(1, 11)) + "\n"
    d1 = client.post("/api/v1/text/diff", json={
        "a": a,
        "b": a.replace("line2", "NEW2").replace("line9", "NEW9"),
        "context": 0})
    r = client.post("/api/v1/text/apply-diff",
                    json={"text": a, "diff": d1.json()["diff"]})
    assert r.json()["output"] == a.replace("line2", "NEW2").replace(
        "line9", "NEW9")
    assert r.json()["hunks_applied"] == 2


# --------------------------------------------------------- path/normalize

def test_path_lexical():
    r = _deterministic("/api/v1/path/normalize",
                       {"path": "src//a/../b/./c.py"})
    b = r.json()
    assert b["path"] == "src/b/c.py"
    assert b["absolute"] is False
    assert (b["name"], b["stem"], b["extension"]) == ("c.py", "c", "py")
    r = client.post("/api/v1/path/normalize",
                    json={"path": "C:\\Users\\Dev\\..\\src\\App.JS",
                          "os": "windows", "case": "lower"})
    b = r.json()
    assert b["path"] == "C:/Users/src/App.JS" or b["path"] == "c:/users/src/app.js"
    assert b["absolute"] is True


def test_path_never_crosses_root():
    r = client.post("/api/v1/path/normalize",
                    json={"path": "a/../../b"})
    assert r.json()["path"] == "../b"
    r = client.post("/api/v1/path/normalize", json={"path": "/../../etc"})
    assert r.json()["path"] == "/etc"  # lexical: root absorbs


# ------------------------------------------------------------- glob/match

def test_glob_semantics():
    paths = ["src/a/test_x.py", "src/test_y.py", "src/a/x.py",
             "src/a/b/test_z.py", "tests/test_w.py", "src/.hidden.py"]
    r = _deterministic("/api/v1/glob/match",
                       {"pattern": "src/**/test_*.py", "paths": paths})
    b = r.json()
    assert b["matched"] == ["src/a/test_x.py", "src/test_y.py",
                            "src/a/b/test_z.py"]
    assert b["count"] == 3
    r = client.post("/api/v1/glob/match",
                    json={"pattern": "src/*.py", "paths": paths})
    # dots are literal (no shell magic): * matches .hidden too
    assert r.json()["matched"] == ["src/test_y.py", "src/.hidden.py"]
    r = client.post("/api/v1/glob/match",
                    json={"pattern": "src/?ain*.py", "paths": ["src/main.py"]})
    assert r.json()["count"] == 1  # ? matches one char


# ------------------------------------------------------- env/interpolate

def test_env_modes():
    r = _deterministic("/api/v1/env/interpolate", {
        "template": "$APP on ${PORT:-8080} and ${HOME}",
        "vars": {"APP": "mechacut", "HOME": "/srv"}})
    b = r.json()
    assert b["output"] == "mechacut on 8080 and /srv"
    assert b["substituted"] == 3 and b["missing"] == []
    r = client.post("/api/v1/env/interpolate", json={
        "template": "${A} $B", "vars": {}})
    assert r.status_code == 400  # strict by default
    r = client.post("/api/v1/env/interpolate",
                    json={"template": "${A} $B", "vars": {},
                          "strict": False})
    b = r.json()
    assert b["output"] == "${A} $B"
    assert b["missing"] == ["A", "B"]
    # numeric values stringify deterministically
    r = client.post("/api/v1/env/interpolate",
                    json={"template": "$N", "vars": {"N": 44}})
    assert r.json()["output"] == "44"


def test_mcp_exposes_bundle2():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/call",
                                  "params": {"name": "text_patch",
                                             "arguments": {
                                                 "text": "aXXb",
                                                 "edits": [{"find": "XX",
                                                            "replace": "--"}]}}})
    assert '"output": "a--b"' in r.json()["result"]["content"][0]["text"]
