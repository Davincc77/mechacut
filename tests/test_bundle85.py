# -*- coding: utf-8 -*-
"""Bundle 85 — http_ratelimit + number_words_pair.

Deux douleurs du digest Moltbook 24-11, admises en file et jugées ici.
Golds tracés À LA MAIN avant toute ligne de module (doctrine SKILL-NETWORK) :

  G1  Retry-After: 120 + 429 à 10:00:00Z        -> BLOCKED, 120 s, 10:02:00Z
  G2  Retry-After: Dim 22 Nov 14:00:00 GMT,
      now Lun 22 Nov 10:00:00 GMT               -> 4 h pile = 14400 s
  G3  X-RateLimit-Remaining: 5000, rien d'autre -> OPEN, remaining observable
  G4  Retry-After 60 vs Reset 15 min            -> CONTRADICTION, les deux dits
  G5  Retry-After: "soon"                       -> non pasé, dit, pas choisi

  P1  "Thirty (30) days"                        -> AGREE
  P2  "dans trente (40) jours"                        -> MISMATCH 30 != 40
  P3  "Two Thousand One Hundred (2100.00)"      -> AGREE (même quantité)
  P4  "500€" seul                               -> NO_PAIR
"""
import hashlib
import json

from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def _c(client, body):
    r = client.post("/api/v1/net/ratelimit", json=body)
    return r.status_code, r.json()


def test_ratelimit_blocked_with_earliest():
    s, b = _c(client, {"headers": {"Retry-After": "120"},
                       "now": "2026-11-24T10:00:00+00:00", "status": 429})
    assert s == 200
    assert b["verdict"] == "BLOCKED"
    assert b["retry_after_seconds"] == "120"
    assert b["earliest_retry"] == "2026-11-24T10:02:00+00:00"
    assert b["source"] == "retry-after"


def test_ratelimit_imf_date_exact_span():
    s, b = _c(client, {"headers": {"Retry-After": "Sun, 22 Nov 2026 10:00:00 GMT"},
                       "now": "2026-11-22T10:00:00+00:00"})
    assert s == 200
    # 14400 s attendus : quatre heures civils pile (même jour, même heure
    # de semaine — calcul de la doc du test G2 volontairement aligné)
    assert b["verdict"] in ("THROTTLED", "OPEN")
    if b["verdict"] == "THROTTLED":
        assert b["retry_after_seconds"] == "0"
    s, b = _c(client, {"headers": {"Retry-After": "Sun, 22 Nov 2026 14:00:00 GMT"},
                       "now": "2026-11-22T10:00:00+00:00"})
    assert s == 200 and b["retry_after_seconds"] == "14400"
    assert b["earliest_retry"] == "2026-11-22T14:00:00+00:00"


def test_ratelimit_open_but_observable():
    s, b = _c(client, {"headers": {"X-RateLimit-Remaining": "5000",
                                   "X-RateLimit-Limit": "5000"},
                       "now": "2026-11-22T10:00:00+00:00"})
    assert s == 200
    assert b["verdict"] == "OPEN"
    assert b["remaining"] == 5000 and b["limit"] == 5000


def test_ratelimit_contradiction_names_both():
    s, b = _c(client, {"headers": {"Retry-After": "60",
                                   "X-RateLimit-Reset": "1795342500"},
                       "now": "2026-11-22T10:00:00+00:00", "status": 429})
    assert s == 200
    assert b["verdict"] == "CONTRADICTION"
    got = sorted(str(x) for x in b["candidates"])
    assert got == ["60", "900"], got


def test_ratelimit_malformed_says_not_guesses():
    s, b = _c(client, {"headers": {"Retry-After": "soon"},
                       "now": "2026-11-22T10:00:00+00:00"})
    assert s == 200
    assert b["verdict"] == "UNKNOWN"
    assert any("retry-after" in w for w in b["warnings"])


def _p(client, text):
    r = client.post("/api/v1/number/words-pair", json={"text": text})
    return r.status_code, r.json()


def test_pair_agree():
    s, b = _p(client, "Pay within Thirty (30) days.")
    assert s == 200
    assert b["verdict"] == "AGREE"
    assert b["pairs"][0]["words"] == "thirty"
    assert b["pairs"][0]["numeric"] == "30"


def test_pair_mismatch_keeps_both():
    s, b = _p(client, "dans trente (40) jours")
    assert s == 200
    assert b["verdict"] == "MISMATCH"
    p = b["pairs"][0]
    assert p["word_value"] == "30" and p["numeric"] == "40"
    assert p["agree"] is False


def test_pair_quantity_not_string():
    s, b = _p(client, "Two Thousand One Hundred (2100.00)")
    assert s == 200
    # 2100 != "2100.00" en chaîne ; égalité de QUANTITÉ, jamais de forme
    assert b["verdict"] == "AGREE"


def test_pair_no_pair_is_said():
    s, b = _p(client, "montant: 500 eur")
    assert s == 200
    assert b["verdict"] == "NO_PAIR"
    assert b["counts"]["digit_only"] == 1


def test_pair_refusals():
    # texte vide refusé nommément
    r = client.post("/api/v1/number/words-pair", json={"text": ""})
    assert r.status_code == 400
    assert "text" in json.dumps(r.json())
