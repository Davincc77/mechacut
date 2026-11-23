# -*- coding: utf-8 -*-
"""Bundle 84 — /shop/discount-audit : la règle des 30 jours en arithmétique.

Golds tracés MAIN avant l'impl, depuis les exemples PUBLICS :
  100 (1er-oct) → 80 (week-end 7-8 nov) → 100 → BF 70, barré 100,
    annoncé 30 % : référence légale 80.00 posée le 07-nov, vrai
    12.5000 % (10.00 économisés) — le 30 annoncé est une
    INFLATION de 17.5 pp : MISLEADING_INFLATION (exemple wpdesk
    verbatim, loi CJEU C-330/23 : la promo antérieure ABAISSE la
    référence même si le prix est remonté).
  Même history, rien d'annoncé (pas de barré, pas de %) : BASELINE.
  History plate 100, sale 70, barré 100, % 30 : COMPLIANT exact.
  sale 100 = reference : NO_REDUCTION (aucune réduction annoncable).
  barré 90 < référence 100 : WRONG_REFERENCE (en dessous non plus,
    ce n'est pas le chiffre exigé).
  claimed 25 < vrai 30 : WRONG_REFERENCE chiffré 5.0000 pp —
    aucune tolérance d'arrondi n'est PUBLIÉE, on ne l'invente pas.
  history ne couvrant pas le début de fenêtre, pas de
  on_market_since : refus nommé INSUFFICIENT (absence ≠ zéro).
  Palier progressif DE : campagne dès le 20-nov (100→80→70),
  référence = plus bas AVANT le premier palier → 100 : 30 % légaux,
  COMPLIANT (PAngV §11(2)) ; la même table en eu baseline =
  MISLEADING_INFLATION 12.5 — le désaccord de transposition est
  RENDU, jamais moyenné.
  future-dated history, doublon de jour, camp>as_of : refus par le
  NOM du champ.
Et la douleur radar 14h54 verrouillée : les tokens morphématiques
« prix final reste » ne votent plus pour check_target (test
statique TABLE + dictées live FR/EN soldes).
"""
import main
import pytest
import retrykit
import routing
import omnibuskit
from fastapi.testclient import TestClient

client = TestClient(main.app)

WEEKEND = [{"date": "2026-10-01", "price": "100.00"},
           {"date": "2026-11-07", "price": "80.00"},
           {"date": "2026-11-09", "price": "100.00"}]


def _a(**kw):
    r = client.post("/api/v1/shop/discount-audit", json=kw)
    return r.status_code, r.json()


def test_wpdesk_weekend_inflation():
    s, b = _a(history=WEEKEND, as_of="2026-11-27",
              sale_price="70.00", previous_price="100.00",
              claimed_percent="30")
    assert s == 200
    assert b["verdict"] == "MISLEADING_INFLATION"
    assert b["reference_price"] == "80.00"
    assert b["reference_date"] == "2026-11-07"
    assert b["true_percent"] == "12.5000"
    assert b["savings_vs_reference"] == "10.00"
    assert any("fiction" in f for f in b["flags"])
    assert any("overstates" in f and "17.5000" in f
               for f in b["flags"])
    assert "C-330/23" in b["note"]
    assert "2019/2161" in b["rule"]
    assert b["window"] == {"from": "2026-10-28",
                           "to": "2026-11-27"}


def test_baseline_no_claim():
    s, b = _a(history=WEEKEND, as_of="2026-11-27", sale_price="70.00")
    assert s == 200 and b["verdict"] == "BASELINE"
    assert b["reference_price"] == "80.00"
    assert "previous_price_announced" not in b


def test_compliant_clean():
    s, b = _a(history=[{"date": "2026-09-01", "price": "100.00"}],
              as_of="2026-11-27", sale_price="70.00",
              previous_price="100.00", claimed_percent="30")
    assert s == 200 and b["verdict"] == "COMPLIANT"
    assert b["true_percent"] == "30.0000"


def test_claimed_exact_at_lowered_reference():
    # le commerçant honnête AU PLUS BAS : barré 80, % 12.5 exact
    s, b = _a(history=WEEKEND, as_of="2026-11-27", sale_price="70.00",
              previous_price="80.00", claimed_percent="12.5000")
    assert s == 200 and b["verdict"] == "COMPLIANT"


def test_no_reduction():
    s, b = _a(history=[{"date": "2026-10-01", "price": "100.00"}],
              as_of="2026-11-27", sale_price="100.00",
              claimed_percent="5")
    assert s == 200 and b["verdict"] == "NO_REDUCTION"
    assert b["true_percent"] == "0.0000"
    assert b["savings_vs_reference"] == "0.00"


def test_strikethrough_below_reference():
    s, b = _a(history=[{"date": "2026-10-01", "price": "100.00"}],
              as_of="2026-11-27", sale_price="70.00",
              previous_price="90.00")
    assert s == 200 and b["verdict"] == "WRONG_REFERENCE"
    assert any("below legal reference" in f and "10.00" in f
               for f in b["flags"])


def test_understated_percent_no_invented_tolerance():
    s, b = _a(history=[{"date": "2026-10-01", "price": "100.00"}],
              as_of="2026-11-27", sale_price="70.00",
              claimed_percent="25")
    assert s == 200 and b["verdict"] == "WRONG_REFERENCE"
    assert any("5.0000" in f and "no rounding tolerance" in f
               for f in b["flags"])


def test_insufficient_history_named():
    s, b = _a(history=[{"date": "2026-11-17", "price": "88.00"}],
              as_of="2026-11-27", sale_price="70.00")
    assert s == 400
    err = b["errors"][0]
    assert err["field"] == "history"
    assert "2026-10-28" in err["expected"]


def test_recent_listing_clause():
    hist = [{"date": "2026-11-20", "price": "80.00"},
            {"date": "2026-11-24", "price": "70.00"}]
    s, b = _a(history=hist, as_of="2026-11-27", sale_price="60.00",
              previous_price="80.00", jurisdiction="fr",
              on_market_since="2026-11-20")
    assert s == 200
    assert b["reference_price"] == "70.00"
    assert "L112-1-3" in b["note_listing"]
    # en eu baseline la clause est une option des États : refus nommé
    s2, b2 = _a(history=hist, as_of="2026-11-27", sale_price="60.00",
                on_market_since="2026-11-20")
    assert s2 == 400 and "Member States" in \
        b2["errors"][0]["message"]


def test_progressive_de_vs_eu_baseline():
    hist = [{"date": "2026-09-15", "price": "100.00"},
            {"date": "2026-11-20", "price": "80.00"}]
    s, b = _a(history=hist, as_of="2026-11-27", sale_price="70.00",
              previous_price="100.00", claimed_percent="30",
              jurisdiction="de", campaign_start="2026-11-20")
    assert s == 200 and b["verdict"] == "COMPLIANT"
    assert b["reference_price"] == "100.00"
    assert b["window"] == {"from": "2026-10-21",
                           "to": "2026-11-20"}
    assert "§11(2)" in b["rule_progressive"]
    # même table, eu baseline : la campagne est une réduction dans
    # la fenêtre → référence 80, les 30 % annoncés sont une inflation
    s2, b2 = _a(history=hist, as_of="2026-11-27", sale_price="70.00",
                previous_price="100.00", claimed_percent="30")
    assert s2 == 200 and b2["verdict"] == "MISLEADING_INFLATION"
    assert b2["reference_price"] == "80.00"
    # campaign_start est une règle nationale : en eu, refus nommé
    s3, b3 = _a(history=hist, as_of="2026-11-27", sale_price="70.00",
                campaign_start="2026-11-20")
    assert s3 == 400 and "campaign_start" == \
        b3["errors"][0]["field"]


def test_refusals_by_name():
    s, b = _a(history=[{"date": "2026-11-27", "price": "100.00"}],
              as_of="2026-11-27", sale_price="70.00")
    assert s == 400 and "history[0].date" in \
        b["errors"][0]["field"]
    s, b = _a(history=[{"date": "2026-11-01", "price": "80.00"},
                       {"date": "2026-11-01", "price": "90.00"}],
              as_of="2026-11-27", sale_price="70.00")
    assert s == 400 and "duplicate day" in \
        b["errors"][0]["message"]
    s, b = _a(history=WEEKEND, as_of="2026-11-27",
              sale_price="70.00", jurisdiction="uk")
    assert s == 400 and "uk" in b["errors"][0]["message"]
    s, b = _a(history=[], as_of="2026-11-27", sale_price="70.00")
    assert s == 400  # vide refusé comme le grand livre


# ----------------------------------------------------------------
# lot 83 endpoint-level golds (retry-budget)
# ----------------------------------------------------------------

def test_retrybudget_endpoint_golds():
    r = client.post("/api/v1/agent/retry-budget",
                    json={"error_class": "rate_limited",
                          "attempt": 1})
    assert r.status_code == 200
    b = r.json()
    assert b["verdict"] == "REPEAT" and b["backoff_seconds"] == 1
    r = client.post("/api/v1/agent/retry-budget",
                    json={"error_class": "schema_validation",
                          "attempt": 1})
    assert r.json()["verdict"] == "MUTATE"
    r = client.post("/api/v1/agent/retry-budget",
                    json={"error_class": "quota_exhausted",
                          "attempt": 1})
    assert r.json()["verdict"] == "ABORT"
    r = client.post("/api/v1/agent/retry-budget",
                    json={"error_class": "no_such_class",
                          "attempt": 1})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "error_class"


# ----------------------------------------------------------------
# douleur radar 14h54 : les tokens morphématiques ne volent plus
# ----------------------------------------------------------------

def test_check_target_no_hollow_tags():
    for name, path, pack, purpose, tags in routing.TABLE:
        if name == "check_target":
            for hollow in ("prix", "final", "reste"):
                assert hollow not in tags.split(), (
                    "tag creux %r de retour dans check_target — "
                    "classe b81 étendue aux mots vides" % hollow)


def test_soldes_lines_not_stolen_top1():
    # dictées live du corpus radar : le bon outil doit être TOP-1
    r = client.get("/route", params={"q": "-25 % puis -20 % sur "
                                          "81,90 — prix final"})
    tools = r.json()["tools"]
    assert tools[0]["tool"] in ("recipe_soldes2", "money_discount")
    r = client.get("/route", params={
        "q": "is 30% off plus another 20% the same as 50% off "
             "on 89.90"})
    tools = r.json()["tools"]
    assert tools[0]["tool"] == "money_discount"
    # la garde retrybudget/audit tombe sur leurs propres lignes
    r = client.get("/route", params={
        "q": "is retrying this timeout a fourth time rational or "
             "am i stuck"})
    assert r.json()["tools"][0]["tool"] == "agent_retrybudget"
    r = client.get("/route", params={
        "q": "le prix barré annonce -30 pour cent — est-ce licite "
             "face à la règle des trente jours ?"})
    assert r.json()["tools"][0]["tool"] == "shop_discount_audit"
    r = client.get("/route", params={
        "q": "a loja anuncia 30% sobre o preço riscado — é ilegal "
             "pela regra dos 30 dias?"})
    assert r.json()["tools"][0]["tool"] == "shop_discount_audit"
