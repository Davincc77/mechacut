# -*- coding: utf-8 -*-
"""Bundle 77 — /api/v1/shop/shipping-deadline : la table des délais
d'envoi de Noël 2026, croisée ≥2 sources, conflit NOMMÉ.

Golds tracés À LA MAIN avant l'impl, depuis les tableaux PRESSE
(cross-audit ×6 du cycle, articles publiés 13→21-nov-2026), jamais
recopiés du module :

  fedex express-saver  -> ship_by 2026-12-21 (sunherald « Monday,
      Dec. 21 ») ; palmbeachpost publie Dec 22 → conflit nommé.
  fedex 2day           -> 2026-12-22 « Tuesday » (3 sources) ; pbp 23.
  fedex overnight      -> 2026-12-23 « Wednesday » ; pbp 24.
  fedex ground-economy -> 2026-12-15 « Tuesday » (pressconnects).
  fedex sameday        -> 2026-12-24 « Thursday » (unanime ×4).
  usps ground-advantage-> 2026-12-17 « Thursday » (sunherald, verbatim).
  usps priority        -> 2026-12-18 ; priority-express -> 2026-12-19.
  ups 3-day-select     -> 2026-12-21 ; 2nd-day-air -> 12-22 ;
      next-day-air -> 12-23. UPS GROUND : AUCUNE date (« check
      ups.com/ctc ») -> refus nommé.
  fedex ground transit : 5->12-17, 4->12-18, 3->12-21, 2->12-22,
      1->12-23 (palmbeachpost/wpxi/sunherald concordants).
  arrives_by COMMUN = 2026-12-24 (vendredi 25 férié : « before Dec 25 »
  chez USPS et « by Dec 24 » chez UPS/FedEx décrivent le MÊME soir).

  Compte à rebours tracé main : 2026-11-23 -> 2026-12-22 = 7 (nov.)
  + 22 = 29 jours ; 2026-12-22 -> 12-22 = 0 « last-day-today » ;
  2026-12-23 -> 12-21 = -2 « missed ».

  ORACLE DE CALENDIER (indépendant du module) : chaque ship_by porte
  le jour de semaine PUBLIÉ en dur par la presse : 12-15 Tuesday,
  12-17 Thursday, 12-18 Friday, 12-19 Saturday, 12-21 Monday,
  12-22 Tuesday, 12-23 Wednesday, 12-24 Thursday.
"""
import datetime as dt

from fastapi.testclient import TestClient

import main
import routing
import shipdeadkit

client = TestClient(main.app)


def _post(**kw):
    r = client.post("/api/v1/shop/shipping-deadline", json=kw)
    return r


# ---------- la table, gold presse ----------

def test_fedex_saver_majority_and_named_conflict():
    d = _post(carrier="fedex", service="express-saver").json()
    assert d["ship_by"] == "2026-12-21"
    assert d["ship_by_weekday"] == "Monday"
    assert d["arrives_by"] == "2026-12-24"
    assert d["arrives_by_weekday"] == "Thursday"
    c = d["cross_check"]["conflict"]
    assert c["ship_by"] == "2026-12-22"
    assert c["source"] == "palmbeachpost"
    assert "Dec 25" in c["why"]
    assert len(d["cross_check"]["agreeing_sources"]) == 5


def test_usps_semantics_kept_verbatim():
    d = _post(carrier="usps", service="ground-advantage").json()
    assert d["ship_by"] == "2026-12-17"
    assert d["ship_by_weekday"] == "Thursday"
    assert "before Dec 25" in d["published_semantics"]
    assert d["cross_check"]["conflict"] is None


def test_aliased_forms_land_on_same_row():
    a = _post(carrier="usps", service="Priority Mail Express").json()
    b = _post(carrier="usps", service="priority-express").json()
    assert a["ship_by"] == b["ship_by"] == "2026-12-19"
    assert a["sha256"] == b["sha256"]


def test_ups_ground_refused_no_single_date():
    r = _post(carrier="ups", service="ground")
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "service"
    assert "ups.com/ctc" in e["message"]
    # la promesse du refus doit pointer des services VIVANTS de la table
    assert "2nd-day-air" in e["expected"]


def test_fedex_transit_days_required_and_bounded():
    r = _post(carrier="fedex", service="ground")
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "transit_days"
    d5 = _post(carrier="fedex", service="ground",
               transit_days=5).json()
    assert d5["ship_by"] == "2026-12-17"
    d1 = _post(carrier="fedex", service="home-delivery",
               transit_days=1).json()
    assert d1["ship_by"] == "2026-12-23"
    assert d1["transit_days"] == 1
    r6 = _post(carrier="fedex", service="ground", transit_days=6)
    assert r6.status_code == 400
    assert "transit_days 6 outside" in r6.json()["errors"][0]["message"]


def test_transit_on_single_date_service_refused():
    r = _post(carrier="fedex", service="2day", transit_days=2)
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "transit_days"
    assert "ONE published ship-by" in e["message"]


# ---------- compte à rebours, arithmétique tracée main ----------

def test_days_left_hand_counted():
    d = _post(carrier="ups", service="2nd-day-air",
              as_of="2026-11-23").json()
    assert d["days_left"] == 29          # 7 (nov.) + 22 (dec.)
    assert d["deadline_state"] == "open"
    t = _post(carrier="ups", service="2nd-day-air",
              as_of="2026-12-22").json()
    assert t["days_left"] == 0
    assert t["deadline_state"] == "last-day-today"
    m = _post(carrier="ups", service="3-day-select",
              as_of="2026-12-23").json()
    assert m["days_left"] == -2
    assert m["deadline_state"] == "missed"


def test_as_of_grammar_refused_by_name():
    for bad in ("12/23/2026", "23.12.2026", "2026-13-01",
                "2026-12-23T10:00", "2026-12"):
        r = _post(carrier="ups", service="2nd-day-air", as_of=bad)
        assert r.status_code == 400, bad
        assert r.json()["errors"][0]["field"] == "as_of"


# ---------- hors table ----------

def test_unknown_carrier_lists_the_closed_three():
    r = _post(carrier="dhl", service="express")
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "carrier"
    assert "usps | ups | fedex" in e["expected"]


def test_year_outside_table_refused_not_extrapolated():
    r = _post(carrier="usps", service="priority", year=2027)
    assert r.status_code == 400
    assert "2026" in r.json()["errors"][0]["expected"]


def test_scope_honest_on_every_answer():
    d = _post(carrier="usps", service="priority").json()
    assert "Alaska/Hawaii" in d["scope"]


# ---------- ORACLE : jour publié en dur par la presse ----------

PUBLISHED_WEEKDAYS = [
    ("fedex", "ground-economy", None, "2026-12-15", "Tuesday"),
    ("usps", "ground-advantage", None, "2026-12-17", "Thursday"),
    ("ups", "3-day-select", None, "2026-12-21", "Monday"),
    ("ups", "2nd-day-air", None, "2026-12-22", "Tuesday"),
    ("ups", "next-day-air", None, "2026-12-23", "Wednesday"),
    ("fedex", "sameday", None, "2026-12-24", "Thursday"),
]


def test_weekday_derivation_matches_press_verbatim():
    for carrier, service, tr, date, day in PUBLISHED_WEEKDAYS:
        body = {"carrier": carrier, "service": service}
        if tr:
            body["transit_days"] = tr
        d = _post(**body).json()
        assert d["ship_by"] == date
        assert d["ship_by_weekday"] == day
        # oracle indépendant : le calendrier système dit le même mot
        assert dt.date.fromisoformat(date).strftime("%A") == day


def test_determinism_and_wire_registered():
    a = _post(carrier="ups", service="next-day-air").json()
    b = _post(carrier="ups", service="next-day-air").json()
    assert a == b and a["sha256"]
    rows = [t for t in routing.TABLE
            if t[0] == "shop_shipping_deadline"]
    assert len(rows) == 1
    assert rows[0][1] == "/api/v1/shop/shipping-deadline"
    assert "shop_shipping_deadline" in main.TOOL_RUN
    # le module DOIT voyager dans l'image docker
    docker = open("Dockerfile", encoding="utf-8").read()
    assert "shipdeadkit.py" in docker


def test_route_dictations_x3_langues():
    # les phrases live (sayings) doivent tomber sur l'outil — la
    # leçon bundle71 : le live parle AVANT le push
    for q in ("last day to ship UPS 2nd Day Air so it arrives by "
              "Christmas?",
              "dernier jour pour envoyer avec FedEx Express Saver "
              "avant Noël",
              "qual o último dia para enviar FedEx Ground 3 dias e "
              "chegar no Natal 2026"):
        d = client.get("/route", params={"q": q, "top": "5"}).json()
        tools = d.get("tools", [])
        assert tools and tools[0]["tool"] == "shop_shipping_deadline", q


def test_module_table_has_no_hand_derived_weekday():
    # garde-fou : les jours de semaine ne sont JAMAIS en table,
    # toujours dérivés du calendrier par _wdays
    for year, ctab in shipdeadkit.YEARS.items():
        for carrier, tab in ctab.items():
            if not isinstance(tab, dict) or carrier == "transit_map":
                continue
            for svc, row in (tab.get("services") or {}).items():
                if isinstance(row, dict) and "ship_by" in row:
                    assert not isinstance(row["ship_by"], tuple)
