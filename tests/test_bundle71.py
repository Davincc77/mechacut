# -*- coding: utf-8 -*-
"""Bundle 71 — /api/v1/food/leftovers : la fenêtre des restes, table
FSIS fermée, horloge murale interdite.

Toutes les attentes sont CALCULÉES À LA MAIN avant impl (calendrier
2026 vérifié : le 26-nov-2026 est un jeudi — Thanksgiving ; NBC
19-nov-2026 publie « eat them by Monday, Nov 30 » = cooked_day + 4).
"""
from datetime import date

import leftoverskit
from leftoverskit import _add_months, run_leftovers, LeftoversError

import json
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


# ---------- bornes de la règle des 2 heures (strictes, verbatim) ----

def test_exactly_two_hours_passes_two_oh_one_discards():
    # « longer than 2 hours » : 2 h pile n'est pas plus long.
    ok = run_leftovers(dict(category="turkey",
                            cooked_at="2026-11-26T17:00",
                            stored_at="2026-11-26T19:00"))
    assert ok["two_hour_rule"]["verdict"] == "WITHIN"
    assert ok["two_hour_rule"]["hours_out"] == "2"
    bad = run_leftovers(dict(category="turkey",
                             cooked_at="2026-11-26T17:00",
                             stored_at="2026-11-26T19:01"))
    assert bad["two_hour_rule"]["verdict"] == "DISCARD"
    # le DISCARD ne calcule PAS la fenêtre — pas de blanchiment :
    assert "fridge" not in bad
    assert "DISCARD" in bad["verdict"]


def test_warm_room_moves_the_gate_to_one_hour():
    ok = run_leftovers(dict(category="stuffing",
                            cooked_at="2026-11-26T15:00",
                            stored_at="2026-11-26T16:00",
                            warm_room=True))
    assert ok["two_hour_rule"]["verdict"] == "WITHIN"
    bad = run_leftovers(dict(category="stuffing",
                             cooked_at="2026-11-26T15:00",
                             stored_at="2026-11-26T16:01",
                             warm_room=True))
    assert bad["two_hour_rule"]["verdict"] == "DISCARD"
    assert bad["two_hour_rule"]["limit_hours"] == 1


# ---------- la fenêtre 3-4 jours, bandes nommées ---------------------

def test_thanksgiving_replay_matches_the_headlines():
    # calcul main : cuit jeu 26-nov + 4 jours = lun 30-nov = la date
    # que NBC/USA publient en dur pour 2026 ; ici c'est un ARGUMENT.
    out = run_leftovers(dict(category="turkey",
                             cooked_at="2026-11-26T17:00",
                             stored_at="2026-11-26T19:00",
                             as_of="2026-11-30"))
    assert out["fridge"]["last_day"] == "2026-11-30"
    assert out["fridge"]["use_by_first_reading"] == "2026-11-29"
    assert out["as_of"]["band"] == "LAST_DAY"
    assert out["as_of"]["days_elapsed"] == 4


def test_bands_across_the_boundary():
    base = dict(category="turkey", cooked_at="2026-11-26T17:00",
                stored_at="2026-11-26T19:00")
    d3 = run_leftovers(dict(base, as_of="2026-11-29"))
    assert d3["as_of"]["band"] == "WITHIN"
    d5 = run_leftovers(dict(base, as_of="2026-12-01"))
    assert d5["as_of"]["band"] == "EXPIRED"
    # r/Cooking rejoué : carcasse du 22-nov, question du 27-nov :
    exp = run_leftovers(dict(category="turkey",
                             cooked_at="2026-11-22T18:00",
                             stored_at="2026-11-22T19:30",
                             as_of="2026-11-27"))
    assert exp["as_of"]["band"] == "EXPIRED"
    assert exp["fridge"]["last_day"] == "2026-11-26"


def test_stored_on_the_far_side_of_midnight_publishes_both_readings():
    # cuit 23:30, rangé 00:30 : 1 h dehors ✓ mais changement de jour
    # calendaire — les DEUX lectures sont publiées, jamais un choix.
    out = run_leftovers(dict(category="gravy",
                             cooked_at="2026-11-26T23:30",
                             stored_at="2026-11-27T00:30"))
    assert out["two_hour_rule"]["verdict"] == "WITHIN"
    note = out["fridge"]["counting_note"]
    assert note and "2026-11-30..2026-12-01" in note


# ---------- congélateur : UNION des deux pages, clamp de fin de mois -

def test_freezer_union_of_contradicting_fsis_pages():
    out = run_leftovers(dict(category="turkey",
                             cooked_at="2026-11-26T17:00",
                             stored_at="2026-11-26T19:00",
                             frozen_at="2026-11-26"))
    f = out["freezer"]
    assert f["months_low"] == 2 and f["months_high"] == 6
    assert f["quality_from"] == "2027-01-26"
    assert f["quality_by"] == "2027-05-26"
    assert "2 to 6" in f["anchors"]["lets_talk_turkey"]
    assert "3 to 4" in f["anchors"]["leftovers_page"]
    assert f["frozen_after_window"] is False
    assert "quality" in f["safety"].lower()


def test_month_clamp_including_leap_february():
    # calcul main : février 2027 = 28 jours, février 2028 = 29.
    assert _add_months(date(2026, 8, 31), 6) == date(2027, 2, 28)
    assert _add_months(date(2027, 8, 31), 6) == date(2028, 2, 29)
    assert _add_months(date(2028, 1, 31), 1) == date(2028, 2, 29)
    assert _add_months(date(2026, 11, 26), 2) == date(2027, 1, 26)


def test_frozen_after_window_is_flagged_not_silenced():
    out = run_leftovers(dict(category="turkey",
                             cooked_at="2026-11-20T17:00",
                             stored_at="2026-11-20T18:00",
                             frozen_at="2026-11-27"))
    # last_day = 2026-11-24 ; congelé le 27 → hors fenêtre frigo :
    assert out["freezer"]["frozen_after_window"] is True
    assert "not certifiable" in out["freezer"]["after_window_note"]


# ---------- refus nommés ---------------------------------------------

def test_closed_category_refuses_invented_rows():
    # les tables d'extensions d'États se contredisent (mash « 2-4
    # weeks » Penn State contre le 2-6 mois général) : pas d'invention.
    for bad in ("mashed potatoes", "casserole", ""):
        try:
            run_leftovers(dict(category=bad,
                               cooked_at="2026-11-26T17:00",
                               stored_at="2026-11-26T19:00"))
            raise AssertionError("refus attendu: " + repr(bad))
        except LeftoversError as e:
            assert e.field == "category"
            assert "turkey|stuffing|gravy|leftovers" in e.expected


def test_time_travel_and_clockless_are_refused():
    try:
        run_leftovers(dict(category="turkey",
                           cooked_at="2026-11-26T17:00",
                           stored_at="2026-11-26T19:00",
                           as_of="2026-11-25"))
        raise AssertionError("as_of antérieur au jour de cuisson")
    except LeftoversError as e:
        assert e.field == "as_of"
    try:
        run_leftovers(dict(category="turkey",
                           cooked_at="2026-11-26T17:00"))
        raise AssertionError("stored_at absent = pas de devinette")
    except LeftoversError as e:
        assert e.field == "stored_at"


def test_slash_dates_and_offsets_refused():
    try:
        run_leftovers(dict(category="turkey",
                           cooked_at="26/11/2026",
                           stored_at="2026-11-26T19:00"))
        raise AssertionError("slash refusé (précédent aging)")
    except LeftoversError as e:
        assert e.field == "cooked_at" and "slash" in e.message
    try:
        run_leftovers(dict(category="turkey",
                           cooked_at="2026-11-26T17:00:00+01:00",
                           stored_at="2026-11-26T19:00"))
        raise AssertionError("offset refusé (naïves, même fuseau)")
    except LeftoversError as e:
        assert e.field == "cooked_at"


# ---------- réchauffe par catégorie ----------------------------------

def test_reheat_by_category():
    g = run_leftovers(dict(category="gravy",
                           cooked_at="2026-11-26T16:00",
                           stored_at="2026-11-26T17:00"))
    assert "ROLLING BOIL" in g["reheat"]
    t = run_leftovers(dict(category="turkey",
                           cooked_at="2026-11-26T16:00",
                           stored_at="2026-11-26T17:00"))
    assert "165 F" in t["reheat"] and "cold" in t["reheat"]
    s = run_leftovers(dict(category="stuffing",
                           cooked_at="2026-11-26T16:00",
                           stored_at="2026-11-26T17:00"))
    assert "165 F" in s["reheat"] and "stuffing center" in s["reheat"]


# ---------- contrat API & routeur ------------------------------------

def test_api_shape_and_sha():
    r = client.post("/api/v1/food/leftovers", json=dict(
        category="turkey", cooked_at="2026-11-26T17:00",
        stored_at="2026-11-26T19:00", as_of="2026-11-30"))
    assert r.status_code == 200
    b = r.json()
    assert "sha256" in b and b["source"]
    assert b["two_hour_rule"]["verdict"] == "WITHIN"
    r4 = client.post("/api/v1/food/leftovers", json=dict(
        category="giblet gravy boat"))
    assert r4.status_code == 400


def test_router_routes_leftovers_without_stealing_poultry():
    # "leftovers" est le NOM de l'outil : poids 4, survit seul (T6).
    import routing
    hits = routing.route("are my leftovers still safe")
    assert hits and hits[0]["tool"] == "food_leftovers"
    # la dinde crue à dégeler reste chez poultry — pas de vol :
    hits = routing.route("when do I take the turkey out of the "
                         "freezer to thaw")
    assert "food_poultry" in [h["tool"] for h in hits[:2]]
    # les lignes shop PT/FR ne dérivent pas vers les restes :
    hits = routing.route("loja tinha 435, vendeu 35 de manha, 40% "
                         "do resto a tarde, quantos restam")
    assert all(h["tool"] != "food_leftovers" for h in hits)
