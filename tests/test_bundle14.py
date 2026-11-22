"""Bundle 14 — extraction (extract/facts capped, text/select free)."""
import json

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_facts_complete_inventory():
    text = ("Invoice 2026-11-21 total $1,200.50 plus 20% VAT; wire to "
            "FR76 1234 5678 9012 3456 7890 1234; contact a@b.io; details "
            "at https://acme.io/inv; ref "
            "123e4567-e89b-12d3-a456-426614174000; tx 0xdeadbeefcafe; "
            "45 days.")
    r = client.post("/api/v1/extract/facts",
                    json={"text": text, "context_chars": 5})
    assert r.status_code == 200
    j = r.json()
    kinds = {f["kind"] for f in j["facts"]}
    assert {"date", "money", "percent", "iban", "email", "url", "uuid",
            "hexid", "number"} <= kinds, kinds
    # offsets are real: value re-founds at `at`
    for f in j["facts"]:
        assert text[f["at"]:f["at"] + len(f["value"])] == f["value"]
    assert j["total"] == len(j["facts"])


def test_facts_deterministic_bytes():
    body = {"text": "3 items for 12.50 EUR on 2026-01-02"}
    r1 = client.post("/api/v1/extract/facts", json=body)
    r2 = client.post("/api/v1/extract/facts", json=body)
    assert r1.content == r2.content
    assert "sha256" in r1.json()


def test_facts_closed_context_bound():
    r = client.post("/api/v1/extract/facts",
                    json={"text": "x", "context_chars": 999})
    assert r.status_code == 400
    assert "0..200" in json.dumps(r.json())


def test_select_document_order_and_coverage():
    chunks = ["revenue grew by half", "unrelated", "revenue revenue growth"]
    r = client.post("/api/v1/text/select",
                    json={"chunks": chunks, "query": "revenue growth",
                          "k": 2})
    assert r.status_code == 200
    j = r.json()
    idx = [x["index"] for x in j["selected"]]
    assert idx == sorted(idx)          # document order preserved
    assert idx[0] == 0 and idx[-1] == 2
    assert j["coverage"] == 1.0


def test_select_rejects_empty():
    r = client.post("/api/v1/text/select",
                    json={"chunks": [], "query": "x"})
    assert r.status_code == 400


def test_select_free_keyless_but_facts_capped_under_32k():
    # both answer keyless here: select is free, facts is capped (32 KB)
    r1 = client.post("/api/v1/text/select",
                     json={"chunks": ["a b"], "query": "a"})
    r2 = client.post("/api/v1/extract/facts", json={"text": "7 items"})
    assert r1.status_code == 200 and r2.status_code == 200


def test_mcp_exposes_bundle14():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert "extract_facts" in names and "text_select" in names
    r2 = client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "extract_facts",
                   "arguments": {"text": "paid $10.00 on 2026-01-02",
                                 "context_chars": 0}}})
    payload = json.loads(r2.json()["result"]["content"][0]["text"])
    assert payload["by_kind"].get("money") == 1


def test_facts_group_kind():
    r = client.post("/api/v1/extract/facts", json={
        "text": "paid $10.00 on 2026-01-02 and $10.00 again; 3.5% and 3",
        "group": "kind"})
    assert r.status_code == 200
    j = r.json()
    assert "facts" not in j
    assert j["values"]["money"] == ["$10.00"]     # deduped
    assert j["values"]["date"] == ["2026-01-02"]
    assert j["values"]["percent"] == ["3.5%"]
    assert "3" in j["values"]["number"]


def test_facts_default_shape_unchanged():
    r = client.post("/api/v1/extract/facts",
                    json={"text": "on 2026-01-02 pay $5.00",
                          "context_chars": 0})
    j = r.json()
    assert "facts" in j and "values" not in j
