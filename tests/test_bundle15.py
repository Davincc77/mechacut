"""Bundle 15 — logic pack: logic/rules, sort/multi, json/query (all free)."""
import json

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_rules_pass_trace_and_set():
    r = client.post("/api/v1/logic/rules", json={
        "facts": {"amount": 1200, "country": "FR", "tags": ["eu"]},
        "rules": [
            {"name": "sepa", "when": {"fact": "country", "op": "eq",
                                      "value": "FR"},
             "require": {"and": [
                 {"fact": "amount", "op": "lte", "value": 10000},
                 {"fact": "tags", "op": "contains", "value": "eu"}]}},
            {"name": "never", "when": {"fact": "amount", "op": "gt",
                                       "value": 99999},
             "forbid": {"fact": "country", "op": "exists"}},
            {"name": "stamp", "set": {"checked": True}}]})
    assert r.status_code == 200
    j = r.json()
    assert j["pass"] is True and j["fired"] == 2
    outcomes = [t["outcome"] for t in j["trace"]]
    assert outcomes == ["passed", "skipped", "passed"]
    assert j["facts"]["checked"] is True


def test_rules_violation_names_the_rule():
    r = client.post("/api/v1/logic/rules", json={
        "facts": {"amount": 50000},
        "rules": [{"name": "limit", "require": {
            "fact": "amount", "op": "lte", "value": 10000}}]})
    j = r.json()
    assert j["pass"] is False
    assert j["violations"] == [{"rule": "limit", "kind": "require"}]
    assert j["errors"][0]["field"] == "limit"


def test_rules_closed_grammar_refunks_bad_ops():
    r = client.post("/api/v1/logic/rules", json={
        "facts": {"a": 1}, "rules": [{"name": "x", "require": {
            "fact": "a", "op": "regex", "value": ".*"}}]})
    assert r.status_code == 400
    assert "regex" in json.dumps(r.json()) and "eq" in json.dumps(r.json())


def test_rules_not_and_or_exist():
    r = client.post("/api/v1/logic/rules", json={
        "facts": {"role": "admin"},
        "rules": [{"name": "gate", "require": {"or": [
            {"fact": "role", "op": "eq", "value": "admin"},
            {"not": {"fact": "banned", "op": "exists"}}]}}]})
    assert r.json()["pass"] is True


def test_sort_multi_keys_dirs_ties():
    rows = [{"n": "b", "p": 2}, {"n": "a", "p": 2}, {"n": "c", "p": 1}]
    r = client.post("/api/v1/sort/multi",
                    json={"rows": rows, "by": [{"key": "p"},
                                               {"key": "n", "dir": "desc"}]})
    assert [x["n"] for x in r.json()["sorted"]] == ["c", "b", "a"]


def test_sort_multi_rejects_bad_dir():
    r = client.post("/api/v1/sort/multi",
                    json={"rows": [{"a": 1}], "by": [{"key": "a",
                                                      "dir": "sideways"}]})
    assert r.status_code == 400 and "asc" in json.dumps(r.json())


def test_json_query_wildcard_and_paths():
    r = client.post("/api/v1/json/query", json={
        "data": {"users": [{"email": "a@x.io"}, {"email": "b@x.io"}]},
        "path": "$.users[*].email"})
    j = r.json()
    assert j["matches"] == 2
    assert j["results"][1] == {"path": "$.users[1].email",
                               "value": "b@x.io"}


def test_json_query_grammar_closed():
    r = client.post("/api/v1/json/query",
                    json={"data": {}, "path": "$..users"})
    assert r.status_code == 400
    assert "$" in json.dumps(r.json())


def test_mcp_exposes_bundle15():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    for n in ("logic_rules", "sort_multi", "json_query"):
        assert n in names


def test_free_tier_keyless_all_three():
    for path, body in [
        ("/api/v1/logic/rules", {"facts": {}, "rules": [{"name": "n"}]}),
        ("/api/v1/sort/multi", {"rows": [{"a": 1}], "by": [{"key": "a"}]}),
        ("/api/v1/json/query", {"data": {"a": 1}, "path": "$.a"}),
    ]:
        assert client.post(path, json=body).status_code == 200, path
