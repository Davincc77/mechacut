# -*- coding: utf-8 -*-
"""Bundle 64 — A1+A2 du soir 22-11, ordonnés par V21 et l'humain.

A1 : le compteur de jours ouvrés que ComputeFirst avait et pas nous
(date/calc op=diff unit=business_days) recoit include_base — ADDITIF
pur : le comportement historique (base exclue) reste épinglé, le
nouveau portail compte les DEUX bouts (leur convention, or 9 écrit à
la main dans ce test AVANT l'impl). Fenêtre nulle : le jour même
compte 1 s'il est ouvré — pas 0 par omission. Fenêtre arrière avec
include_base : REFUS nommé, la convention ne s'importe pas en miroir.

A2 : validate/iban devient gratuit — décision de l'humain après V21
(« TIER-DIVERGENCE : même byte, portefeuille chez nous »). Le sha de
la réponse n'a pas bougé (le middleware ne touche pas le corps) :
la pin FR garde son empreinte, elle change de rayon.
"""
from fastapi.testclient import TestClient

import main
import payments

client = TestClient(main.app)


def _days(base, until, holidays=None, include_base=None):
    params = {"until": until, "unit": "business_days",
              "holidays": holidays or []}
    if include_base is not None:
        params["include_base"] = include_base
    r = client.post("/api/v1/date/calc",
                    json={"base": base, "op": "diff", "params": params})
    assert r.status_code == 200, r.text
    return r.json()["business_days"]


# ------------------------------------------------------------- A1
def test_workdays_inclusive_counts_both_ends():
    # or du banc V21 G4, écrit à la main avant l'impl :
    # lun 05 → ven 16 janvier 2026, férié le 12 = 9
    assert _days("2026-01-05", "2026-01-16",
                 ["2026-01-12"], True) == 9


def test_workdays_default_unchanged_base_excluded():
    # la continuité d'abord : l'ancien comportement, épinglé, bouge pas
    assert _days("2026-01-05", "2026-01-16", ["2026-01-12"]) == 8
    assert _days("2026-01-05", "2026-01-16", ["2026-01-12"],
                 False) == 8


def test_workdays_same_day_is_one_when_open():
    assert _days("2026-01-05", "2026-01-05", [], True) == 1   # lundi
    assert _days("2026-01-05", "2026-01-05", ["2026-01-05"],
                 True) == 0                                   # férié
    assert _days("2026-01-10", "2026-01-10", [], True) == 0   # samedi


def test_workdays_backward_window_refused_not_mirrored():
    r = client.post("/api/v1/date/calc", json={
        "base": "2026-01-16", "op": "diff",
        "params": {"until": "2026-01-05", "unit": "business_days",
                   "include_base": True}})
    assert r.status_code == 400
    msgs = " ".join(e["message"] for e in r.json()["errors"])
    assert "include_base needs until >= base" in msgs
    # l'arrière SANS include_base garde sa signature figée par les
    # pins — et elle n'est PAS le miroir de l'avant : base exclue
    # en avant = (05..16] = 8 ouvrés ; en arrière = [05..16) compte
    # 15..05 = 9 ouvrés. C'est exactement pour cela qu'include_base
    # refuse l'arrière au lieu de le mirrored par conjecture.
    assert _days("2026-01-16", "2026-01-05") == -9


# ------------------------------------------------------------- A2
def test_iban_left_the_paid_table():
    assert "/api/v1/validate/iban" not in payments.PRICES
    assert "/api/v1/validate/iban" not in payments.PRICE_LABELS


def test_iban_free_still_the_same_answer():
    r = client.post("/api/v1/validate/iban",
                    json={"iban": "FR7630006000011234567890189"})
    assert r.status_code == 200
    b = r.json()
    assert b["valid"] is True and b["country"] == "FR" \
        and b["length"] == 27
    # le sha du corps ne dépend pas du tier — la pin garde son empreinte
    assert b["sha256"] == r.json()["sha256"]


def test_manifest_and_docstrings_say_free():
    src = open("main.py", encoding="utf-8").read()
    assert "mod-97 verdict (free)" in src
    assert "mod-97   (free)" in src
    assert '"$0.0005"' not in src.split("/api/v1/validate/iban\":"
                                        )[1][:120]
