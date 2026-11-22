# -*- coding: utf-8 -*-
"""bundle57 — /api/v1/check/target : le verrou de cible en service.

ORACLES CALCULÉS À LA MAIN, d'après les incidents publiés :
  V23 #09 : target « le prix final », réponse nommée « prix final »
     valeur 49.14 avec known final=49.14 → OK (le verrou littéral
     refusait ; le verrou à table de synonymes fermée passe).
  V23 #18 : cible remaining, mot de l'énoncé « RESTE » valeur 300,
     collision sold_afternoon==remaining==300 → OK (le NOM est la
     clé, la valeur est celle de la clé).
  V17 #00 : 160 nommé « remaining » alors que remaining=240 →
     MISMATCH, value_is_actually = [sold_afternoon] (160).
  Invention : « le resultat » hors table → VOCAB avec le
     vocabulary trié (jamais deviné).
  Décimal strict : « 240 » vs known 240.00 → égalité Decimal.
  CIBLE : 400 nommé « rest after morning » alors que la cible est
     remaining → CIBLE (quantité réelle, mauvaise visée).
  Réparations nommées : chaque refus porte `next` non vide, ok=false.
  Forme : value en prose, known vide, doublon de noms → 400 CHAMP
     par nom.
  Déterminisme : le même appel trois fois → même sha256.
"""
from fastapi.testclient import TestClient

import lockkit
import main as m

client = TestClient(m.app)

K9 = [{"name": "price", "value": "81.90"},
      {"name": "after_first", "value": "61.425"},
      {"name": "final", "value": "49.14"}]
K18 = [{"name": "total", "value": "435"},
       {"name": "sold_morning", "value": "35"},
       {"name": "rest_after_morning", "value": "400"},
       {"name": "sold_afternoon", "value": "300"},
       {"name": "remaining", "value": "300"}]
K00 = [{"name": "remaining", "value": "240"},
       {"name": "sold_afternoon", "value": "160"}]


def post(target, name, value, known):
    return client.post("/api/v1/check/target", json={
        "target": target, "answer": {"name": name, "value": value},
        "known": known})


def test_v23_synonym_passes():
    r = post("le prix final", "prix final", "49.14", K9).json()
    assert r["ok"] and r["verdict"] == "OK", r
    assert r["answer"] == {"target": "final", "value": "49.14"}


def test_v23_rest_collision_names_the_key():
    r = post("combien restent", "RESTE", "300", K18).json()
    assert r["ok"] and r["answer"]["target"] == "remaining", r


def test_v17_mismatch_names_the_real_quantity():
    r = post("remaining", "remaining", "160", K00).json()
    assert r["verdict"] == "MISMATCH", r
    assert r["value_is_actually"] == ["sold_afternoon"]
    assert r["ok"] is False and r["next"]


def test_invention_refused_with_vocab():
    r = post("final", "le resultat", "49.14", K9).json()
    assert r["verdict"] == "VOCAB" and r["ok"] is False
    assert r["vocabulary"] == ["after_first", "final", "price"]
    assert r["next"]


def test_decimal_equality_not_string():
    # « ce qui reste encore » n'est PAS en table : grammaire fermée,
    # on ne devine pas — le refus est nommé, réparable en une passe.
    r = post("remaining", "ce qui reste encore", "240",
             [{"name": "remaining", "value": "240.00"}]).json()
    assert r["verdict"] == "VOCAB", r
    r2 = post("remaining", "what is left", "240",
              [{"name": "remaining", "value": "240.00"}]).json()
    # la valeur SERVIE est celle du serveur, dans sa forme canonique
    # (240.00), pas la notation du candidat : c'est le principe même
    # de la fiche — la réponse est dans le serveur.
    assert r2["ok"] and r2["answer"]["value"] == "240.00", r2


def test_cible_wrong_named_quantity():
    r = post("combien restent", "rest after morning", "400",
             K18).json()
    assert r["verdict"] == "CIBLE", r
    assert r["expected_target"] == "remaining"
    assert r["named"] == "rest_after_morning"


def test_shape_refusals_are_named():
    r = client.post("/api/v1/check/target", json={
        "target": "final", "answer": {"name": "final",
                                      "value": "environ quarante-neuf"},
        "known": K9})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "answer.value"
    r = post("final", "final", "49.14", [])
    assert r.status_code == 400 and r.json()["errors"][0][
        "field"] == "known"
    r = post("final", "final", "49.14", K9 + K9[:1])
    assert r.status_code == 400 and r.json()["errors"][0][
        "field"] == "known"


def test_determinism_same_sha_three_times():
    seen = {post("le prix final", "prix final", "49.14", K9)
            .json()["sha256"] for _ in range(3)}
    assert len(seen) == 1


def test_lockkit_pure_table():
    voc = {"remaining"}
    assert lockkit.resolve("Quanto resta", voc) == "remaining"
    assert lockkit.resolve("restante", voc) == "remaining"
    assert lockkit.resolve("the remainder", voc) == "remaining"
    assert lockkit.resolve("resultat global", voc) is None
