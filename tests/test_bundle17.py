"""Bundle 17 — micro-organs: decode, human, escape, normalize (free)."""
import json

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_decode_repairs_provable_mojibake():
    r = client.post("/api/v1/text/decode", json={"text": "CafÃ© au lait"})
    j = r.json()
    assert j["text"] == "Café au lait"
    assert j["repaired"] is True and j["repairs"] == 1


def test_decode_never_guesses_clean_text():
    body = {"text": "texte propre, sans souci d'encodage"}
    r1 = client.post("/api/v1/text/decode", json=body)
    r2 = client.post("/api/v1/text/decode", json=body)
    assert r1.status_code == 200
    assert r1.json()["repaired"] is False
    assert r1.json()["text"] == body["text"]
    assert r1.content == r2.content


def test_num_human_durations_bytes_romans_ordinals():
    for value, kind, want in [
        (3661, "duration", "1h 1m 1s"),
        (86475, "duration", "1d 0h 1m 15s"),
        (1536, "bytes", "1.50 KiB"),
        (1987, "roman", "MCMLXXXVII"),
        (22, "ordinal", "22nd"),
        (3, "ordinal", "3rd"),
    ]:
        j = client.post("/api/v1/num/human",
                        json={"value": value, "kind": kind}).json()
        assert j["human"] == want, (kind, value, j)
    j = client.post("/api/v1/num/human",
                    json={"value": 1536, "kind": "bytes",
                          "style": "decimal"}).json()
    assert j["human"] == "1.54 kB" and j["base"] == "1000"


def test_num_human_closed_kinds():
    r = client.post("/api/v1/num/human",
                    json={"value": 1, "kind": "fahrenheit"})
    assert r.status_code == 422 or r.status_code == 400


def test_escape_dialects_all_closed():
    r = client.post("/api/v1/text/escape", json={
        "value": "O'Brien <b>&amp;</b>",
        "dialects": ["html", "sql", "shell", "csv", "json", "url"]})
    j = r.json()
    e = j["escaped"]
    assert set(e) == {"html", "sql", "shell", "csv", "json", "url"}
    assert "&lt;b&gt;" in e["html"]
    assert "''" in e["sql"]                       # doubled quote
    assert e["shell"].startswith("'")             # forced single-quote
    assert e["json"] == "O'Brien <b>&amp;</b>"  # JSON needs no entities


def test_escape_unknown_dialect_named():
    r = client.post("/api/v1/text/escape",
                    json={"value": "x", "dialects": ["latex"]})
    assert r.status_code == 400
    assert "latex" in json.dumps(r.json()) and "html" in json.dumps(r.json())


def test_normalize_forms_ligature_and_accents():
    r = client.post("/api/v1/text/normalize", json={
        "text": "ﬁle  Ünïcödé", "form": "NFKC", "strip_accents": True,
        "collapse_ws": True})
    j = r.json()
    assert j["text"] == "file Unicode" and j["changed"] is True


def test_normalize_fullwidth():
    r = client.post("/api/v1/text/normalize",
                    json={"text": "ＴＥＳＴ １２３", "fullwidth": True,
                          "collapse_ws": True})
    assert r.json()["text"] == "TEST 123"


def test_mcp_exposes_bundle17():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    for n in ("text_decode", "num_human", "text_escape", "text_normalize"):
        assert n in names


def test_all_free_keyless():
    for path, body in [
        ("/api/v1/text/decode", {"text": "ok"}),
        ("/api/v1/num/human", {"value": 5, "kind": "ordinal"}),
        ("/api/v1/text/escape", {"value": "x", "dialects": ["csv"]}),
        ("/api/v1/text/normalize", {"text": "x"}),
    ]:
        assert client.post(path, json=body).status_code == 200, path
