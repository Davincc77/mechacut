"""Bundle 0.3 — pipeline: a whole chain in one call, refs stay server-side."""

import hashlib

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)

URL = "/api/v1/pipeline"

CHAIN = [
    {"tool": "csv_fix", "args": {"csv": "id,score\r\n1, 10\r\n1,10\r\n"}},
    {"tool": "csv_types", "args": {"csv": {"$from": [0, "output"]}}},
    {"tool": "list_dedupe", "args": {"items": {"$from": [1, "output"]},
                                     "mode": "exact"}},
]


def test_pipeline_chain_and_trace():
    r1 = client.post(URL, json={"steps": CHAIN})
    r2 = client.post(URL, json={"steps": CHAIN})
    assert r1.content == r2.content
    b = r1.json()
    assert b["steps"] == ["csv_fix", "csv_types", "list_dedupe"]
    assert b["output"]["output"] == [{"id": 1, "score": 10.0}]
    assert "sha256" in b


def test_pipeline_bench_task_matches_pinned_gold():
    import sys
    sys.path.insert(0, "bench")
    import task_data as td
    steps = [
        {"tool": "csv_fix", "args": {"csv": td.DIRTY_CSV}},
        {"tool": "csv_types", "args": {"csv": {"$from": [0, "output"]}}},
        {"tool": "list_dedupe", "args": {"items": {"$from": [1, "output"]},
                                         "mode": "exact"}},
        {"tool": "json_repair", "args": {"text": td.BROKEN_JSON}},
        {"tool": "list_dedupe", "args": {"items": td.URLS, "mode": "url"}},
        {"tool": "format_convert", "args": {
            "input": {"rows": {"$from": [2, "output"]},
                      "totals": {"$from": [3, "output"]},
                      "urls": {"$from": [4, "output"]}},
            "from": "json", "to": "yaml"}},
    ]
    b = client.post(URL, json={"steps": steps}).json()
    import yaml
    doc = yaml.safe_load(b["output"]["output"])
    h = hashlib.sha256(td.canonical_of(doc)).hexdigest()
    pinned = open("bench/expected.sha").read().strip()
    assert h == pinned  # one call = the whole gold answer


def test_pipeline_refs_are_backward_only():
    r = client.post(URL, json={"steps": [
        {"tool": "json_canonical",
         "args": {"input": {"$from": [1, "output"]}}}]})
    assert r.status_code == 400
    assert "cannot see" in r.json()["errors"][0]["message"]


def test_pipeline_guards():
    r = client.post(URL, json={"steps": [{"tool": "nope", "args": {}}]})
    assert r.status_code == 400 and "manifest" in r.text
    r = client.post(URL, json={"steps": []})
    assert r.status_code == 400
    r = client.post(URL, json={"steps": [
        {"tool": "json_canonical", "args": {"input": 1}}] * 9})
    assert r.status_code == 400  # 1..8 steps


def test_pipeline_never_smuggles_paid_work():
    r = client.post(URL, json={"steps": [
        {"tool": "chart_from_data", "args": {"kind": "bar"}}]})
    assert r.status_code == 402
    assert r.json()["error"] == "payment_required"
    big = "a,b\n" + "x,y\n" * 9000
    r = client.post(URL, json={"steps": [
        {"tool": "csv_fix", "args": {"csv": big}}]})
    assert r.status_code == 402  # above the 32 KB cap -> direct x402 route


def test_pipeline_step_error_names_its_step():
    r = client.post(URL, json={"steps": [
        {"tool": "json_repair", "args": {"text": '{"a": 1}'}},
        {"tool": "csv_fix", "args": {"csv": ""}}]})
    assert r.status_code == 400
    b = r.json()
    assert b["step"] == 1
    assert "header row" in r.text  # the step's own repair prompt survives
