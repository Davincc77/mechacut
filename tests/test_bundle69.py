# -*- coding: utf-8 -*-
"""bundle69 — /api/v1/food/poultry : la FENÊTRE de la dinde,
tables USDA/FSIS, l'heure du four est un ARGUMENT.

ORACLES tracés à la MAIN sur les tables publiées (écrits avant le
module, jamais recopiés de sa sortie) :

1. décongélation frigo, 15 lb : créneau (12,16) = 3 à 4 jours ;
   eau froide (12,16) = 6 à 8 h ; cuisson (14,18) = 3¾ à 4¼ h,
   soit 3.7500 à 4.2500 heures.
2. plan 16 lb, oven_at 2026-11-26T10:00 : créneau (16,20) = 4 à 5 j,
   bout LONG = 5 j = 120 h → by = 2026-11-21T10:00.
   not_before = by − 48 h = 2026-11-19T10:00 (la règle des 1–2 jours
   FSIS : plus tôt que ça, la volaille a fini de décongeler et
   dort au-delà de la fenêtre).
   eau froide (16,20) = 8 à 10 h → by = 2026-11-26T00:00 ;
   done = oven + [17/4, 9/2) h = 2026-11-26T14:15 / 14:30 ? non :
   (14 lb) — 16 lb est (14,18) : earliest + 3¾ h = 13:45,
   latest + 4¼ h = 14:15.
3. 14 lb = BORNE PARTAGÉE, cuisson : « 12 to 14 » (3–3¾) ET
   « 14 to 18 » (3¾–4¼) → union 3 à 4.25, boundary=True.
4. 6,8 kg = 6.8 × 10⁸/45359237 lb = 680000000/45359237 =
   14.9918… (tracé : 45359237 × 14 = 635029318 ; reste
   44970682 ; 44970682/45359237 ≈ 0.99144 → 14.9914 lb) :
   cuisson (14,18) strict — boundary=False ; décongélation
   (12,16) = 3–4 j.
5. refus NOMMÉS : 3 lb et 30 lb hors table (4–24 bornes incluses) ;
   « 19,99 » virgule → /num/parse ; unit stone.
6. as_of 2026-11-23T12:00 pour le plan 16 lb : by = 21e 10:00 →
   fridge_still_possible False ; cold by = 26e 00:00 → True.
7. la table ne bouge pas : mêmes octets deux fois, sha256 voyage.
"""
import json


def _client():
    from fastapi.testclient import TestClient
    import main
    main.RATE_LIMIT = 10**9
    return TestClient(main.app)


def _post(body):
    r = _client().post("/api/v1/food/poultry", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_v1_thaw_15lb_brackets():
    out = _post({"mode": "thaw", "weight": "15"})
    assert out["refrigerator_days"]["min"] == "3 days"
    assert out["refrigerator_days"]["max"] == "4 days"
    assert out["cold_water_hours"]["min"] == "6 hours"
    assert out["cold_water_hours"]["max"] == "8 hours"
    assert out["cook_hours"]["min"] == "3.75 hours"
    assert out["cook_hours"]["max"] == "4.25 hours"
    assert "165 F" in out["thermometer"]


def test_v2_plan_16lb_window_iso():
    out = _post({"weight": "16", "oven_at": "2026-11-26T10:00"})
    assert out["mode"] == "plan"
    assert out["put_in_refrigerator"]["by"] == "2026-11-21T10:00"
    assert out["put_in_refrigerator"]["not_before"] == "2026-11-19T10:00"
    assert out["cold_water_fallback"]["by"] == "2026-11-26T00:00"
    # 16 lb : cuisson (14,18) 3¾–4¼
    assert out["done"]["earliest"] == "2026-11-26T13:45"
    assert out["done"]["latest"] == "2026-11-26T14:15"
    assert out["frozen_from_scratch"]["out_earliest"] == "2026-11-26T15:37"
    assert out["frozen_from_scratch"]["out_latest"] == "2026-11-26T16:22"


def test_v3_boundary_14lb_union():
    out = _post({"mode": "cook", "weight": "14"})
    assert out["cook_hours"]["min"] == "3 hours"
    assert out["cook_hours"]["max"] == "4.25 hours"
    assert out["cook_hours"]["boundary"] is True
    # 14 n'est pas borne de décongélation (12,16) seule
    assert out["refrigerator_days"]["boundary"] is False
    assert out["refrigerator_days"]["min"] == "3 days"


def test_v4_kg_6p8_exact_fraction():
    out = _post({"mode": "cook", "weight": "6.8", "unit": "kg"})
    # 6.8 * 10**8 / 45359237 = 680000000/45359237 lb = 14.9914…
    assert out["weight_lb"].startswith("14.9914")
    assert out["cook_hours"]["boundary"] is False
    assert out["cook_hours"]["min"] == "3.75 hours"


def test_v5_named_refusals():
    c = _client()
    for bad in [{"weight": "3"}, {"weight": "30"},
                {"weight": "19,99"}, {"weight": "10", "unit": "stone"}]:
        r = c.post("/api/v1/food/poultry", json=bad)
        assert r.status_code == 400, bad
        f = r.json()["errors"][0]["field"]
        assert f in ("weight", "unit"), (bad, f)


def test_v6_as_of_behind_schedule():
    out = _post({"weight": "16", "oven_at": "2026-11-26T10:00",
                 "as_of": "2026-11-23T12:00"})
    assert out["behind_schedule"]["fridge_still_possible"] is False
    assert out["behind_schedule"]["cold_water_still_possible"] is True
    assert out["behind_schedule"]["frozen_still_possible"] is True


def test_v7_determinism_same_bytes_twice():
    c = _client()
    body = {"weight": "16", "oven_at": "2026-11-26T10:00"}
    r1 = c.post("/api/v1/food/poultry", json=body)
    r2 = c.post("/api/v1/food/poultry", json=body)
    assert r1.content == r2.content
    assert r1.json()["sha256"]


def test_v8_mode_outside_grammar():
    c = _client()
    r = c.post("/api/v1/food/poultry",
               json={"mode": "grill", "weight": "16"})
    assert r.status_code == 400
    assert "plan|thaw|cook" in r.json()["errors"][0]["expected"]


def test_route_top1_three_languages():
    c = _client()
    qs = [
        "what time do I take the turkey out of the freezer to "
        "roast it in time for Thanksgiving dinner at 3",
        "a quelle heure sortir la dinde du congelateur pour la "
        "cuisson du four a Thanksgiving diner 15 heures",
        "a que horas tirar o peru do congelador para assar no "
        "forno a tempo do jantar de Thanksgiving",
    ]
    for q in qs:
        top = c.get("/route", params={"q": q}).json()["tools"][0]["tool"]
        assert top == "food_poultry", (q, top)


def test_mcp_tool_call_returns_window():
    c = _client()
    r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 2,
                             "method": "tools/call",
                             "params": {
                                 "name": "food_poultry",
                                 "arguments": {
                                     "weight": "16",
                                     "oven_at": "2026-11-26T10:00"}}})
    text = r.json()["result"]["content"][0]["text"]
    out = json.loads(text)
    payload = out["output"] if "output" in out else out
    assert payload["put_in_refrigerator"]["by"] == "2026-11-21T10:00"


def test_e17_landing_card_baked_three_languages():
    """Puce RÉELLEMENT recalculée au build (garde maison) : le
    everyday_grid des locales porte l'heure bue par le serveur."""
    en = json.load(open("locales/en.json", encoding="utf-8"))
    fr = json.load(open("locales/fr.json", encoding="utf-8"))
    pt = json.load(open("locales/pt.json", encoding="utf-8"))
    assert "into the fridge by 2026-11-21T10:00" in en["everyday_grid"]
    assert "not before 2026-11-19T10:00" in en["everyday_grid"]
    assert "cong\u00e9lateur avant 2026-11-21T10:00" in fr["everyday_grid"]
    assert "jamais avant 2026-11-19T10:00" in fr["everyday_grid"]
    assert "geladeira at\u00e9 2026-11-21T10:00" in pt["everyday_grid"]
    assert "nunca antes de 2026-11-19T10:00" in pt["everyday_grid"]
