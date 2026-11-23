# -*- coding: utf-8 -*-
"""Bundle 90 — le registre public des propositions.

Demande humaine (24-11) : page SÉPARÉE des arrivées avec le résultat du
banc — approuvé / doublon / refusé et POURQUOI. Visibles : les dix
dernières arrivées (dès qu'il y en a dix), statut de chacune
interrogeable par bots et humains — même principe que le catalogue.
Monétisation : compte Base OBLIGATOIRE pour devenir payante ; format
vérifié (EIP-55), responsabilité au proposeur si mal renseigné — écrit
dans le contrat lui-même, pas en note de bas de page.

Semences du registre (docs/proposals/registry.jsonl, append-only, 10
entrées, toutes traçables à une origine nommée) :
  shipped  ×6 : http_ratelimit, number_words_pair, date_window,
             date_deemed, text_fold_report, text_novel_words
  accepted ×2 : address_parse, date_civil  (banc dit POURQUOI)
  en-banc  ×1 : money_tip                  (jugée ELIGIBLE, non codée)
  refuse   ×1 : money_split                (DUPLICATE-OF argent, sha dit)

Golds tracés main :
  L1 liste sans filtre : ordre d'arrivée du fichier, counts d'états
     exacts, arrival = date DITE par la ligne (jamais l'horloge).
  L2 latest=3 -> les 3 dernières lignes du fichier ; latest=10 -> 10 ;
     latest=12 -> TOUTES les 10, window "up to", pas une erreur.
  L3 name=date_window -> 1 entrée, bundle 86 nommé, handle source.
  L4 status=refuse -> 1 entrée = money_split, reason = sha DUPLICATE-OF ;
     status=en-banc -> money_tip. Un filtre vide n'est pas une erreur.
  L5 grammaires : latest=0 -> 400 latest_grammar ; status=bogus ->
     400 status_grammar avec les cinq valeurs énumérées.
  L6 gate : propose sans compte -> monetizable false + next_step nommé ;
     compte EIP-55 valide -> monetizable true + accountability dite ;
     checksum cassé -> 400 base_account_grammar. On ne juge pas un
     contrat avec une adresse qui enverrait l'argent nulle part.
"""
import json

from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

VALID = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
BROKEN = "0x5aaeb6053F3E94C9b9A09f33669435E7Ef1BeAed"  # casse fautive


def _q(params):
    r = client.get("/api/v1/agent/proposals", params=params)
    return r.status_code, r.json()


def _p(body):
    r = client.post("/api/v1/agent/propose", json=body)
    return r.status_code, r.json()


ORDER = ["http_ratelimit", "number_words_pair", "date_window",
         "date_deemed", "text_fold_report", "text_novel_words",
         "address_parse", "date_civil", "money_tip", "money_split"]


def test_l1_listed_in_file_order_with_said_dates():
    s, b = _q({})
    assert s == 200 and b["verdict"] == "LISTED"
    assert [e["name"] for e in b["entries"]] == ORDER
    assert b["counts"]["status"] == {"shipped": 6, "accepted": 2,
                                     "en-banc": 1, "refuse": 1,
                                     "proposed": 0}
    assert b["counts"]["total"] == 10
    for e in b["entries"]:
        assert len(e["arrival"]) == 10 and e["arrival"][4] == "-"
    assert b["registry"] == "docs/proposals/registry.jsonl"


def test_l2_latest_is_a_window_not_a_promise():
    s, b = _q({"latest": 3})
    assert [e["name"] for e in b["entries"]] == ["date_civil",
                                                 "money_tip",
                                                 "money_split"]
    assert b["counts"] == {"shown": 3, "total": 10}
    s, b = _q({"latest": 10})
    assert [e["name"] for e in b["entries"]] == ORDER  # ordre du fichier
    s, b = _q({"latest": 12})
    assert b["counts"]["shown"] == 10  # up to, never exactly


def test_l3_search_one_named_proposal():
    s, b = _q({"name": "date_window"})
    assert s == 200 and b["verdict"] == "FOUND"
    e = b["entries"][0]
    assert e["status"] == "shipped" and e["bundle"] == 86
    assert "@prismdeadlines" in e["source"]


def test_l4_refused_carries_the_why_and_the_empty_is_a_fact():
    s, b = _q({"status": "refuse"})
    assert s == 200 and b["verdict"] == "FILTERED"
    assert [e["name"] for e in b["entries"]] == ["money_split"]
    assert "sha256" in b["entries"][0]["reason"]
    s, b = _q({"status": "en-banc"})
    assert [e["name"] for e in b["entries"]] == ["money_tip"]
    s, b = _q({"status": "proposed"})
    assert s == 200 and b["entries"] == []
    assert b["counts"]["shown"] == 0  # vide dit, pas erreur


def test_l5_grammars_are_named():
    s, b = _q({"latest": 0})
    assert s == 400 and "latest_grammar" in str(b)
    s, b = _q({"status": "bogus"})
    assert s == 400 and "status_grammar" in str(b)
    for v in ("shipped", "accepted", "en-banc", "refuse", "proposed"):
        assert v in str(b)


def test_l6_monetization_gate_on_propose():
    base = {"name": "calendar_lunar",
            "purpose": "lunar phase for a named civil date and zone",
            "examples": [{"input": {"date": "2026-12-24"},
                          "expected": {"phase": "waning"}}],
            "why": "holidays drift, models guess"}
    s, b = _p(dict(base))
    assert s == 200
    assert b["monetizable"] is False
    assert "base_account" in json.dumps(b["next_steps"])
    s, b = _p(dict(base, base_account=VALID))
    assert s == 200 and b["monetizable"] is True
    assert "proposer" in b["accountability"]
    s, b = _p(dict(base, base_account=BROKEN))
    assert s == 400 and "base_account_grammar" in str(b)


def test_b90_surfaces():
    names = [x["name"] for x in client.post(
        "/mcp", json={"jsonrpc": "2.0", "id": 1,
                      "method": "tools/list"}).json()["result"]["tools"]]
    assert "proposals_registry" in names
    m = client.get("/agent/manifest").text
    assert "/api/v1/agent/proposals" in m
    page = client.get("/proposals", headers={
        "Accept": "text/html"}).text
    assert "money_tip" in page and "money_split" in page
    assert "Dernières arrivées" in page or "Latest arrivals" in page
