# -*- coding: utf-8 -*-
"""Bundle 87 — agent/propose : la porte du réseau, jugée sans rien stocker.

Golds tracés MAIN (thresholds suspect_min_score=8, suspect_min_matched=2,
sondés sur le routeur vivant 24-11) :

  G1 money_split                      -> DUPLICATE-OF money_split
  G2 expense_split_daily + « split a restaurant bill evenly among people »
                                      -> SUSPECT (score 10, 3 matched, nommé)
  G3 money_tip + « how much to leave as gratuity given party size and
     total » (top1 score 6, 2 matched) -> ELIGIBLE + blob prêt au commit
  G4 « Money-Tip! »                   -> 400 bad_name, grammaire dite
  G5 purpose « tip »                  -> 400 purpose_grammar (20..140)
  G6 examples vides                   -> 400
  G7 as_of fourni                     -> blob daté PAR ARGUMENT, sinon
                                         undated — pas d'horloge murale
"""
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def _p(body):
    r = client.post("/api/v1/agent/propose", json=body)
    return r.status_code, r.json()


EX = [{"input": {"bill": "57.30", "pct": 15}, "expected": {"tip": "8.60"}}]


def test_g1_exact_duplicate():
    s, b = _p({"name": "money_split", "purpose": "cent exact split of a "
               "shared bill with closed remainder rules", "examples": EX})
    assert s == 200
    assert b["verdict"] == "DUPLICATE-OF"
    assert b["matches"][0]["tool"] == "money_split"


def test_g2_suspect_names_evidence():
    s, b = _p({"name": "expense_split_daily", "purpose": "split a "
               "restaurant bill evenly among people", "examples": EX})
    assert s == 200
    assert b["verdict"] == "SUSPECT-DUPLICATE"
    top = b["matches"][0]
    assert top["tool"] == "money_split" and top["score"] >= 8
    assert len(top["matched"]) >= 2


def test_g3_eligible_gets_blob_and_no_storage():
    s, b = _p({"name": "money_tip", "purpose": "how much to leave as "
               "gratuity given party size and total", "examples": EX,
               "why": "waiters split by hand and models fumble 15%"})
    assert s == 200
    assert b["verdict"] == "ELIGIBLE"
    assert b["stored"] is False
    assert b["blob"]["name"] == "money_tip"
    assert b["blob"]["undated"] is True
    assert b["thresholds"] == {"suspect_min_score": 8,
                               "suspect_min_matched": 2}
    assert "sha256" in b


def test_g4_bad_name_grammar_said():
    s, b = _p({"name": "Money-Tip!", "purpose": "how much to leave as "
               "gratuity given party size and total", "examples": EX})
    assert s == 400
    assert "bad_name" in str(b)


def test_g5_purpose_too_short():
    s, b = _p({"name": "money_tip", "purpose": "tip", "examples": EX})
    assert s == 400
    assert "purpose_grammar" in str(b)


def test_g6_empty_examples_refused():
    s, b = _p({"name": "money_tip", "purpose": "how much to leave as "
               "gratuity given party size and total", "examples": []})
    assert s == 400
    assert "examples" in str(b)


def test_g7_as_of_is_an_argument():
    s, b = _p({"name": "money_tip", "purpose": "how much to leave as "
               "gratuity given party size and total", "examples": EX,
               "as_of": "2026-11-24"})
    assert s == 200
    assert b["blob"]["as_of"] == "2026-11-24"
    assert b["blob"]["undated"] is False


def test_b87_surfaces_live():
    r = client.get("/SKILL-KIT.md")
    assert r.status_code == 200
    t = r.text
    assert "/api/v1/agent/propose" in t and "golds" in t.lower()
    names = [x["name"] for x in client.post(
        "/mcp", json={"jsonrpc": "2.0", "id": 1,
                      "method": "tools/list"}).json()["result"]["tools"]]
    assert "agent_propose" in names
