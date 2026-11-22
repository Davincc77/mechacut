"""Bundle 13 — self-check (check/constraints, check/refs)."""
import hashlib
import json

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _post(client, path, body):
    return client.post(path, json=body)


def test_constraints_pass_and_deterministic():
    body = {"text": "Vente closee le 2026-11-21 pour 45 euros.\n"
                    "1. alpha\n2. beta\n3. gamma",
            "constraints": {"points": 3, "max_words": 20,
                            "contains_date": True, "contains_number": True}}
    r1 = _post(client, "/api/v1/check/constraints", body)
    r2 = _post(client, "/api/v1/check/constraints", body)
    assert r1.status_code == 200
    j = r1.json()
    assert j["pass"] is True and j["checked"] == 4
    assert j["first_failure"] is None and j["errors"] == []
    assert r1.text == r2.text  # mêmes entrées, mêmes octets


def test_constraints_failure_names_the_repair():
    r = _post(client, "/api/v1/check/constraints", {
        "text": "- one point\n- two points",
        "constraints": {"points": 3, "must_contain": ["total", "2026"]}})
    assert r.status_code == 200
    j = r.json()
    assert j["pass"] is False
    fields = {e["field"] for e in j["errors"]}
    assert fields == {"points", "must_contain"}
    assert "points" in j["first_failure"]
    err = next(e for e in j["errors"] if e["field"] == "points")
    assert err["expected"] == 3 and err["observed"] == 2


def test_constraints_closed_vocabulary():
    r = _post(client, "/api/v1/check/constraints",
              {"text": "x", "constraints": {"max_wordz": 3}})
    assert r.status_code == 400
    body = json.dumps(r.json())
    assert "max_wordz" in body and "max_words" in body  # the error repairs


def test_constraints_case_fold_vs_exact():
    body = {"text": "TOTAL: 3", "constraints": {"must_contain": ["total"]}}
    assert _post(client, "/api/v1/check/constraints", body).json()["pass"]
    r = _post(client, "/api/v1/check/constraints", dict(body, case="exact"))
    assert r.json()["pass"] is False


def test_refs_unknown_citation_caught():
    r = _post(client, "/api/v1/check/refs", {
        "text": "According to https://acme.io/report, growth was 42% "
                "(see also https://evil.example/leak).",
        "sources": ["https://acme.io/report says growth was 42%",
                    "background note"]})
    assert r.status_code == 200
    j = r.json()
    assert j["pass"] is False
    assert [u["ref"] for u in j["unknown"]] == ["https://evil.example/leak"]
    assert j["unused_sources"] == ["background note"]
    assert j["refs_total"] == 3  # url, url, number 42


def test_refs_all_grounded():
    r = _post(client, "/api/v1/check/refs", {
        "text": "Done on 2026-11-21 at https://acme.io/x",
        "sources": ["2026-11-21 https://acme.io/x"],
        "kinds": ["urls"]})
    assert r.json()["pass"] is True


def test_mcp_exposes_bundle13():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert "check_constraints" in names and "check_refs" in names
    r2 = client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "check_constraints",
                   "arguments": {"text": "1. a\n2. b",
                                 "constraints": {"points": 2}}}})
    payload = json.loads(r2.json()["result"]["content"][0]["text"])
    assert payload["pass"] is True
    assert hashlib.sha256  # sha256 present in payload below
    assert "sha256" in payload


def test_free_tier_keyless():
    r = _post(client, "/api/v1/check/constraints",
              {"text": "hello", "constraints": {"max_words": 2}})
    assert r.status_code == 200  # no X-PAYMENT header required
