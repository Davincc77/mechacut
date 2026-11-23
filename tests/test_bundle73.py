# -*- coding: utf-8 -*-
"""Bundle 73 — /api/v1/food/ovenschedule : le compte à rebours d'UN
four, J-3 de Thanksgiving (la fenêtre meurt jeudi 26-nov).

Douleur mesurée par la lentille HUMAINE du cycle 06h40 : huit timelines
2026 publiées cette semaine (chefamazing, thekitchencalc, howsweeteats,
hypemenu, sipsavormix, tessiestable, rsvplinks, saltnotes) décrivent le
MÊME dîner avec des repos de 20, 25, 30, 45 ou 60 minutes, 325 contre
350 °F, et PERSONNE ne compte le préchauffage qui « mange 45 minutes »
(thekitchencalc, verbatim). rsvplinks écrit le contrat mot pour mot :
« List every dish that needs the oven, its temperature and its time. »

ORACLES — horaires calculés À LA MAIN sur la règle publiée (calcul à
rebours : sortie du courant = min(serve − repos, entrée du suivant −
ajustement si consigne différente)), JAMAIS recopiés du module :

G1 serve 16:00, preheat 20, [turkey 195/325F/25, stuffing 45/325F/15,
   rolls 15/425F/0] :
   rolls : out = 16:00 − 0 = 16:00 ; in = 15:45.
   stuffing : min(16:00−15=15:45 ; 15:45−20=15:25) → out 15:25 ; in
   14:40. turkey : min(15:35 ; 14:40−0) → out 14:40 ; in = 14:40 −
   195 min = 11:25. oven_on = 11:25 − 20 = 11:05. Holds : 16:00−14:40
   −25 = 55 ; 16:00−15:25−15 = 20 ; 0. Four total = 195+45+15 = 255.
   1 transition (325→425, gap 20) SANS conflit.
G1b même menu, preheat 0 : stuffing out 15:45 in 15:00 ; turkey out
   15:00 in 11:45 hold 35 ; rolls in = out stuffing = 15:45 à 100 °F
   d'écart → CONFLIT no_gap_temp_change ×1. oven_on 11:45.
G2 gratin 40 min à 200 °C repos 10, serve 12:00 : out 11:50 in 11:10 ;
   200 °C × 9/5 + 32 = 360 + 32 = 392 °F pile (Fraction exacte).
G3 G1 + earliest_start 13:00 : allumage 11:05 → court de 115 minutes
   (13:00 − 11:05), feasible False — le calendrier reste rendu.
"""
from fastapi.testclient import TestClient

import main as m
import routing

client = TestClient(m.app)

G1 = {"serve_at": "2026-11-26T16:00", "preheat": 20,
      "dishes": [
          {"name": "turkey", "minutes": 195, "temp": 325,
           "temp_unit": "F", "rest": 25},
          {"name": "stuffing", "minutes": 45, "temp": 325,
           "temp_unit": "F", "rest": 15},
          {"name": "rolls", "minutes": 15, "temp": 425,
           "temp_unit": "F"}]}


def _body(req):
    r = client.post("/api/v1/food/ovenschedule", json=req)
    assert r.status_code == 200, r.text
    return r.json()


def test_thanksgiving_countdown_matches_hand_gold():
    d = _body(G1)
    dk = d["dishes"]
    assert [(x["in_at"][11:16], x["out_at"][11:16]) for x in dk] == \
        [("11:25", "14:40"), ("14:40", "15:25"), ("15:45", "16:00")]
    assert [x["hold_minutes"] for x in dk] == [55, 20, 0]
    assert d["oven_on_at"][11:16] == "11:05"
    assert d["oven_minutes"] == 255
    assert d["temp_conflicts"] == 0
    assert len(d["transitions"]) == 1
    t = d["transitions"][0]
    assert (t["after"], t["from_f"], t["to_f"], t["gap_minutes"],
            t["adjust_applied_minutes"]) == \
        ("stuffing", 325, 425, 20, 20)
    assert d["below_fsis_poultry_floor"] == []


def test_zero_gap_temperature_change_is_a_named_conflict():
    req = {k: v for k, v in G1.items() if k != "preheat"}
    d = _body(req)
    dk = d["dishes"]
    assert [(x["in_at"][11:16], x["out_at"][11:16]) for x in dk] == \
        [("11:45", "15:00"), ("15:00", "15:45"), ("15:45", "16:00")]
    assert dk[0]["hold_minutes"] == 35
    assert d["temp_conflicts"] == 1
    t = d["transitions"][0]
    assert t["gap_minutes"] == 0
    assert t["conflict"].startswith("no_gap_temp_change")


def test_celsius_is_exact_not_approximated():
    d = _body({"serve_at": "2026-11-28T12:00",
               "dishes": [{"name": "gratin", "minutes": 40,
                           "temp": 200, "temp_unit": "C",
                           "rest": 10}]})
    g = d["dishes"][0]
    assert g["temp_f"] == 392          # main : 200*9/5+32
    assert (g["in_at"][11:16], g["out_at"][11:16],
            g["ready_at"][11:16]) == ("11:10", "11:50", "12:00")


def test_short_window_is_feasibility_not_refusal():
    req = dict(G1, earliest_start="2026-11-26T13:00")
    d = _body(req)
    f = d["feasibility"]
    assert f["feasible"] is False
    assert f["short_by_minutes"] == 115   # main : 13:00 - 11:05
    assert d["dishes"][0]["in_at"][11:16] == "11:25"  # calendrier rendu


def test_bare_temperature_without_unit_refused_by_name():
    r = client.post("/api/v1/food/ovenschedule", json={
        "serve_at": "2026-11-26T16:00",
        "dishes": [{"name": "pie", "minutes": 55, "temp": 180}]})
    assert r.status_code == 400      # convention bad_request, épinglée
    e = r.json()["errors"][0]
    assert e["field"] == "dishes[0].temp_unit"
    assert "SANS UNITÉ" in e["message"]


def test_rest_beyond_danger_zone_refused_by_name():
    r = client.post("/api/v1/food/ovenschedule", json={
        "serve_at": "2026-11-26T16:00",
        "dishes": [{"name": "brisket", "minutes": 300, "temp": 275,
                    "temp_unit": "F", "rest": 180}]})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "dishes[0].rest"
    assert "FSIS" in e["message"] and "leftovers" in e["message"]


def test_slash_date_and_oversize_menu_refused():
    r = client.post("/api/v1/food/ovenschedule", json={
        "serve_at": "26/11/2026 16:00",
        "dishes": [{"name": "x", "minutes": 10, "temp": 350,
                    "temp_unit": "F"}]})
    assert r.status_code == 400
    assert "slash" in r.json()["errors"][0]["message"]
    r = client.post("/api/v1/food/ovenschedule", json={
        "serve_at": "2026-11-26T16:00",
        "dishes": [{"name": "d%d" % i, "minutes": 10, "temp": 350,
                    "temp_unit": "F"} for i in range(13)]})
    assert r.status_code == 400
    assert "12" in r.json()["errors"][0]["message"]


def test_routes_x3_languages():
    # « when do I take the turkey out » est HONNÊTEMENT à poultry
    # (quand sortir la dinde = fenêtre de décongélation — ses mots
    # when/take/out, vérifié au banc 12 > 9). La phrase du four ne
    # nomme QUE le four : oven+preheat+countdown+serve+four = 15.
    hits = routing.route("oven countdown preheat to serve at four")
    assert hits[0]["tool"] == "food_ovenschedule"
    assert hits[0]["score"] == 15
    # temp+rature (splitter coupe à l'accent, loi v1.1.0) + four = 6
    hits = routing.route("à quelle température allumer le four")
    assert hits[0]["tool"] == "food_ovenschedule"
    hits = routing.route("sequencia do forno para o assado")
    assert hits[0]["tool"] == "food_ovenschedule"
    assert hits[0]["score"] >= routing.CONF_FLOOR
    # poultry garde sa phrase, intacts (aucun vol de mot) :
    hits = routing.route("when do I take the turkey out")
    assert hits[0]["tool"] == "food_poultry"


def test_golden_contains_six_new_pins():
    import json
    import os
    g = json.loads(open("golden.json", encoding="utf-8").read())
    names = [json.loads(open("corpus/%s" % f, encoding="utf-8").read())
             ["name"] for f in os.listdir("corpus")
             if f.startswith("food_ovenschedule_")]
    assert len(names) == 6
    for n in names:
        assert n in g, n


def test_sayings_and_manifest_carry_the_tool():
    import sayings
    s = sayings.SAY["/api/v1/food/ovenschedule"]
    for L in ("en", "fr", "pt"):
        assert L in s and len(s[L]) > 40
    body = routing.manifest_text(m.app.version)
    assert "/api/v1/food/ovenschedule" in body
    assert len(body) < 9000
