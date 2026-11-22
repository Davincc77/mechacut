"""Bundle 16 — batch + named recipes invoice/schedule."""
import json

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_batch_mixed_results_deterministic():
    body = {"tool": "num_round", "payloads": [
        {"value": "2.5", "mode": "half_even", "places": 0},
        {"value": "oops", "mode": "half_even", "places": 0}]}
    r1 = client.post("/api/v1/batch", json=body)
    r2 = client.post("/api/v1/batch", json=body)
    assert r1.content == r2.content
    j = r1.json()
    assert j["succeeded"] == 1 and j["failed"] == 1
    assert j["results"][0]["ok"] is True
    assert j["results"][1]["ok"] is False
    assert j["results"][1]["error"]["errors"][0]["field"] == "value"
    assert "sha256" in j


def test_batch_unknown_tool_names_alternatives():
    r = client.post("/api/v1/batch",
                    json={"tool": "nope", "payloads": [{}]})
    assert r.status_code == 400
    assert "date_calc" in json.dumps(r.json())  # closed list in the error


def test_batch_no_recursion():
    for t in ("batch",):
        r = client.post("/api/v1/batch",
                        json={"tool": t, "payloads": [{"tool": "x",
                                                       "payloads": []}]})
        assert r.status_code == 400


def test_batch_stop_on_error():
    r = client.post("/api/v1/batch", json={
        "tool": "num_round", "stop_on_error": True, "payloads": [
            {"value": "oops", "mode": "half_even", "places": 0},
            {"value": "1.5", "mode": "half_even", "places": 0}]})
    j = r.json()
    assert j["stopped_early"] is True and len(j["results"]) == 1


def test_recipe_invoice_exact_and_spelled():
    r = client.post("/api/v1/recipe/invoice", json={
        "line_items": [{"desc": "Dev", "qty": 12, "unit_price": "85.00"},
                       {"desc": "Host", "qty": 1, "unit_price": "4.90"}],
        "currency": "EUR", "vat_percent": "20",
        "date": "2026-11-21", "due_days": 30, "words_lang": "fr"})
    assert r.status_code == 200
    j = r.json()
    assert j["subtotal"] == "1024.90"
    assert j["vat"] == "204.98"
    assert j["total"] == "1229.88"
    assert j["due"].startswith("2026-12-21")
    assert "mille deux cent vingt-neuf" in j["total_words"]


def test_recipe_invoice_rejects_garbage():
    r = client.post("/api/v1/recipe/invoice",
                    json={"line_items": [{"qty": 1}]})
    assert r.status_code == 400
    assert "desc" in json.dumps(r.json())


def test_recipe_schedule_weekly_ics():
    r = client.post("/api/v1/recipe/schedule", json={
        "cron": "0 10 * * 1", "start": "2026-11-23T00:00:00",
        "count": 3, "timezone": "Europe/Paris", "duration_minutes": 45,
        "summary": "Standup"})
    j = r.json()
    assert r.status_code == 200
    assert len(j["occurrences"]) == 3
    assert j["occurrences"][0]["start"] == "2026-11-23T10:00:00+01:00"
    assert j["ics"].startswith("BEGIN:VCALENDAR")
    assert "Standup" in j["ics"]


def test_mcp_exposes_batch_and_recipes_visible():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert "batch" in names
