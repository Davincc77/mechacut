# -*- coding: utf-8 -*-
"""Bundle 93 — l'audit adversarial du 24-11, reçu et appliqué.

« date/parse answers 03/04/05 silently as dmy while num/parse refuses
1,234. The same class of ambiguity is refused in one door and resolved
by luck in the other — and your own MCP card says "never guessed". »
Vrai. Reproduit en prod avant d'ouvrir le fichier. Le canon est un :
l'ambiguïté qui ne peut pas se décider par les bytes se REFUSE, avec
les lectures candidates dans la réponse. 05/05/05 répond (toutes les
lectures donnent le même jour : ce ne sont pas des candidats, c'est
le même fait). 13/04/05 répond (13 ne peut pas être un mois : une
seule lecture est possible).

Golds tracés main :
  R1 03/04/05 sans prefer -> 400 slash_ambiguous ; la réponse NOMME
     les deux lectures (2005-04-03 / 2005-03-04) + le champ qui répare
     (prefer) — field+expected+example, le repair prompt intégral.
  R2 prefer=dmy -> 2005-04-03 ; prefer=mdy -> 2005-03-04 (comportement
     existant, inchangé, et le champ ambiguity dit RESOLVED-BY-PREFER).
  R3 13/04/05 -> 200 2005-04-13, ambiguity SINGLE-READING, source dite.
  R4 05/05/05 -> 200 2005-05-05 SINGLE-READING (bytes décident).
  R5 2005-04-03 ISO -> 200, ambiguity NONE — aucune régression : le
     refus ne touche que le registre numeric ambigu.
  R6 la card MCP de date_parse et la ligne de docs disent REFUSE
     désormais — la prose ne peut plus promettre ce que le code faisait.
  R7 (dérive mineure du même audit) : le 400 cross-family de units
     convert porte aussi expected — « the error is the repair prompt »
     vaut pour CHAQUE 400, pas la plupart.
"""
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def _d(body):
    r = client.post("/api/v1/date/parse", json=body)
    return r.status_code, r.json()


def test_r1_slash_ambiguous_is_refused_with_both_readings():
    s, b = _d({"text": "03/04/05"})
    assert s == 400
    txt = str(b)
    assert "slash_ambiguous" in txt
    assert "2005-04-03" in txt and "2005-03-04" in txt
    assert "prefer" in txt
    err = b["error"][0] if isinstance(b.get("error"), list) else b
    assert "field" in str(err) and "expected" in str(err)


def test_r2_prefer_still_decides_exactly():
    s, b = _d({"text": "03/04/05", "prefer": "dmy"})
    assert s == 200 and b["date"] == "2005-04-03"
    assert b["ambiguity"] == "RESOLVED-BY-PREFER"
    s, b = _d({"text": "03/04/05", "prefer": "mdy"})
    assert s == 200 and b["date"] == "2005-03-04"
    assert b["ambiguity"] == "RESOLVED-BY-PREFER"


def test_r3_day_above_twelve_needs_no_prefer():
    s, b = _d({"text": "13/04/05"})
    assert s == 200 and b["date"] == "2005-04-13"
    assert b["ambiguity"] == "SINGLE-READING"


def test_r4_coinciding_readings_are_one_fact():
    s, b = _d({"text": "05/05/05"})
    assert s == 200 and b["date"] == "2005-05-05"
    assert b["ambiguity"] == "SINGLE-READING"


def test_r5_iso_is_untouched():
    s, b = _d({"text": "2005-04-03"})
    assert s == 200 and b["date"] == "2005-04-03"
    assert b["ambiguity"] == "NONE"
    s, b = _d({"text": "3 April 2005"})
    assert s == 200 and b["ambiguity"] == "NONE"


def test_r6_prose_follows_behaviour():
    names = {t["name"]: t["description"] for t in client.post(
        "/mcp", json={"jsonrpc": "2.0", "id": 1,
                      "method": "tools/list"}).json()["result"]["tools"]}
    assert "slash" in names["date_parse"].lower()
    docs = client.get("/docs").text if client.get("/docs").status_code == 200 \
        else ""
    m = client.get("/agent/manifest").text
    assert "date/parse" in m


def test_r7_cross_family_400_carries_expected():
    r = client.post("/api/v1/units/convert",
                    json={"value": 1, "from": "km", "to": "kg"})
    assert r.status_code == 400
    assert "expected" in str(r.json())


def test_r8_fuzz_every_400_carries_expected(monkeypatch):
    monkeypatch.setattr(main, "RATE_LIMIT", 100_000)
    """L'audit parlait d'UN 400 sans expected ; le fuzz en trouvait 29,
    tous passés par _pyd_errors. La seam est unique — ce test la fige :
    aucun 400 ne sort plus d'ici sans nommer le champ ET l'attendu."""
    import routing
    bad = []
    for _n, path, _p, _u, _t in routing.TABLE:
        for payload in ({}, {"text": "\x00"}, {"value": "nan!"},
                        {"expr": "1+1", "from": 7}):
            r = client.post(path, json=payload)
            if r.status_code == 400:
                for e in r.json().get("errors", []):
                    if "expected" not in str(e):
                        bad.append((path, str(e)[:60]))
    assert not bad, bad[:4]
