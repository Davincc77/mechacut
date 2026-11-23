# -*- coding: utf-8 -*-
"""Bundle 88 — text_fold_report + text_novel_words (digest, @reportio).

Golds tracés MAIN :

  F1 ["Hermès","Hermes"] accents            -> COLLIDE hermes <- 2 raws
  F2 ["café","cafe","thé"] accents          -> 1 collision (cafe), thé seul
                                               ne compte pas ; folded_distinct 2
  F3 ["chat","chien"]                       -> SAFE
  F4 []                                     -> 400
  F5 201 valeurs                            -> 400 ceiling 200 nommé
  F6 ["Hermès","HERMES"] mode=cas           -> SAFE (accents gardés : hermès
                                               != hermes) ; mode=les_deux -> COLLIDE

  N1 title « Mechacut ships doom-check »,
     desc  « Mechacut ships doom-check today »      -> ECHO (novel {today}=1)
  N2 desc qui ajoute 4 mots distincts               -> NOVEL
  N3 items [N1, N2]                                 -> MIXED echo1 novel1
  N4 items []                                       -> 400
  N5 2 nouveaux <= 3 -> ECHO ; 3 == défaut -> ECHO ; 3 avec
     max_echo=2 -> NOVEL
"""
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def _f(body):
    r = client.post("/api/v1/text/fold-report", json=body)
    return r.status_code, r.json()


def test_f1_hermes_collision():
    s, b = _f({"values": ["Hermès", "Hermes"]})
    assert s == 200
    assert b["verdict"] == "COLLIDE"
    c = b["collisions"][0]
    assert c["folded"] == "Hermes"  # mode accents seul ne touche PAS la casse
    assert c["raws"] == ["Hermès", "Hermes"]


def test_f2_only_real_pairs_count():
    s, b = _f({"values": ["café", "cafe", "thé"]})
    assert s == 200
    assert len(b["collisions"]) == 1
    assert b["collisions"][0]["folded"] == "cafe"
    assert b["counts"]["values"] == 3
    assert b["counts"]["folded_distinct"] == 2


def test_f3_safe_when_distinct():
    s, b = _f({"values": ["chat", "chien"]})
    assert s == 200 and b["verdict"] == "SAFE"
    assert b["collisions"] == []


def test_f4_empty_refused():
    s, b = _f({"values": []})
    assert s == 400


def test_f5_ceiling_named():
    s, b = _f({"values": ["v%d" % i for i in range(201)]})
    assert s == 400
    assert "200" in str(b)


def test_f6_modes():
    s, b = _f({"values": ["Hermès", "HERMES"], "mode": "cas"})
    assert s == 200 and b["verdict"] == "SAFE"
    s, b = _f({"values": ["Hermès", "HERMES"], "mode": "les_deux"})
    assert s == 200 and b["verdict"] == "COLLIDE"


def _n(items, **kw):
    body = {"items": items}
    body.update(kw)
    r = client.post("/api/v1/text/novel-words", json=body)
    return r.status_code, r.json()


T = "Mechacut ships doom-check"
D_ECHO = "Mechacut ships doom-check today"
D_NOVEL = "Mechacut ships doom-check and the bench measures forty cells nightly"


def test_n1_echo():
    s, b = _n([{"title": T, "description": D_ECHO}])
    assert s == 200
    assert b["items"][0]["verdict"] == "ECHO"
    assert b["items"][0]["novel_count"] == 1
    assert b["verdict"] == "ALL-ECHO"


def test_n2_novel():
    s, b = _n([{"title": T, "description": D_NOVEL}])
    assert s == 200
    assert b["items"][0]["novel_count"] > 3
    assert b["verdict"] == "ALL-NOVEL"


def test_n3_mixed_counts():
    s, b = _n([{"title": T, "description": D_ECHO},
               {"title": T, "description": D_NOVEL}])
    assert s == 200 and b["verdict"] == "MIXED"
    assert b["counts"] == {"echo": 1, "novel": 1, "items": 2}


def test_n4_empty_refused():
    s, b = _n([])
    assert s == 400


def test_n5_boundary_three_is_echo_four_is_novel():
    s, b = _n([{"title": "alpha beta", "description": "alpha beta gamma delta"}])
    assert s == 200 and b["items"][0]["verdict"] == "ECHO"  # 2 nouveaux <= 3
    s, b = _n([{"title": "alpha beta",
                "description": "alpha beta gamma delta epsilon"}])
    assert s == 200 and b["items"][0]["verdict"] == "ECHO"  # 3 == plafond
    # max_echo=2 explicite : les mêmes 3 nouveaux deviennent NOVEL
    s, b = _n([{"title": "alpha beta",
                "description": "alpha beta gamma delta epsilon"}], max_echo=2)
    assert s == 200 and b["items"][0]["verdict"] == "NOVEL"


def test_b88_surfaces():
    names = [x["name"] for x in client.post(
        "/mcp", json={"jsonrpc": "2.0", "id": 1,
                      "method": "tools/list"}).json()["result"]["tools"]]
    assert "text_fold_report" in names and "text_novel_words" in names
    m = client.get("/agent/manifest").text
    assert "/api/v1/text/fold-report" in m and "/api/v1/text/novel-words" in m
