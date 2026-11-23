# -*- coding: utf-8 -*-
"""Bundle 86 — date_window + date_deemed (digest Moltbook, @prismdeadlines).

Golds tracés MAIN avant l'impl, calculs à la plume (vérifiés au datetime
le 23-11, 16h) :

  W1  2026-06-01 before 180..270   -> [2025-09-04 .. 2025-12-03], span 90
  W2  2026-06-01 after  180..270   -> [2026-11-28 .. 2027-02-26]
  W3  2026-06-01 before 270..180   -> refus min_above_max (jamais trié)
  W4  bornes égales 30..30         -> fenêtre d'un jour, span 0, pas un refus
  W5  max 271 en clause            -> 2025-08-31 ? NON : 271 -> 2025-09-03

  D1  2026-11-20 registered        -> 2026-11-22 (+2 table)
  D2  2026-11-20 standard_mail     -> 2026-11-25 (+5 table)
  D3  sans method                  -> refus method_required (pas de date
                                      tant que le mode d'envoi n'est pas connu)
  D4  2026-11-20 email             -> 2026-11-20 (+0)
  D5  deemed_days=14 + registered  -> 2026-12-04, source argument, pas table
"""
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def _w(body):
    r = client.post("/api/v1/date/window", json=body)
    return r.status_code, r.json()


def test_w1_window_before():
    s, b = _w({"event": "2026-06-01", "direction": "before",
               "min_days": 180, "max_days": 270})
    assert s == 200
    assert b["earliest"] == "2025-09-04"
    assert b["latest"] == "2025-12-03"
    assert b["span_days"] == 90
    assert b["bounds"] == "inclusive"


def test_w2_window_after():
    s, b = _w({"event": "2026-06-01", "direction": "after",
               "min_days": 180, "max_days": 270})
    assert s == 200
    assert b["earliest"] == "2026-11-28"
    assert b["latest"] == "2027-02-26"


def test_w3_inverted_bounds_refused_not_sorted():
    s, b = _w({"event": "2026-06-01", "direction": "before",
               "min_days": 270, "max_days": 180})
    assert s == 400
    assert "min_above_max" in str(b)


def test_w4_equal_bounds_is_a_day_not_a_refusal():
    s, b = _w({"event": "2026-06-01", "direction": "after",
               "min_days": 30, "max_days": 30})
    assert s == 200
    assert b["earliest"] == b["latest"] == "2026-07-01"
    assert b["span_days"] == 0


def test_w5_negative_refused():
    s, b = _w({"event": "2026-06-01", "direction": "after",
               "min_days": -1, "max_days": 10})
    assert s == 400


def _d(body):
    r = client.post("/api/v1/date/deemed", json=body)
    return r.status_code, r.json()


def test_d1_registered_two_days():
    s, b = _d({"sent": "2026-11-20", "method": "registered"})
    assert s == 200
    assert b["deemed_receipt"] == "2026-11-22"
    assert b["days"] == 2 and b["source"] == "table"


def test_d2_standard_five_days():
    s, b = _d({"sent": "2026-11-20", "method": "standard_mail"})
    assert s == 200
    assert b["deemed_receipt"] == "2026-11-25"


def test_d3_no_method_no_date():
    s, b = _d({"sent": "2026-11-20"})
    assert s == 400
    assert "method_required" in str(b)


def test_d4_email_same_day():
    s, b = _d({"sent": "2026-11-20", "method": "email"})
    assert s == 200
    assert b["deemed_receipt"] == "2026-11-20"
    assert b["days"] == 0


def test_d5_argument_beats_table_and_is_named():
    s, b = _d({"sent": "2026-11-20", "method": "registered", "deemed_days": 14})
    assert s == 200
    assert b["deemed_receipt"] == "2026-12-04"
    assert b["source"] == "argument" and b["table_days"] == 2


def test_b86_mcp_and_manifest_present():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert "date_window" in names and "date_deemed" in names
    m = client.get("/agent/manifest").text
    assert "/api/v1/date/window" in m and "/api/v1/date/deemed" in m
