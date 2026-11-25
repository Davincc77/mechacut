# -*- coding: utf-8 -*-
"""Bundle 99 — /shop/legal-guarantee : les horloges légales datées FR/UK.

Golds tracés À LA MAIN (oracle séparé écrit AVANT le module, scratch
g99/oracle.py, règles « anniversary » FR et « beginning with » UK),
jamais recopiés du module. Ancres : 2026-12-25 vendredi ; 2027-01-01
vendredi (b98) ; +30 jours = 2027-01-24 dimanche ; +2 ans =
2028-12-25 lundi (731 jours = 104×7+3 : vendredi+3).

  FR neuf, délivré 2026-12-25, découvert 2027-01-16, as_of 2027-01-16
    -> action 2028-12-25 Monday, days_left 709 (365+344), verdict
       WITHIN_PRESUMPTION ; vices 2029-01-16 Tuesday (+2 ans depuis
       la DÉCOUVERTE — ancre différente, nommée), effective 731 jours.
  FR occasion : présomption +12 mois (2027-12-25 Saturday), action
    +2 ans (2028-12-25) — découvert 2028-06-10 -> IN_WINDOW_BURDEN_
    YOURS (« c'est à vous d'apporter la preuve »).
  FR reconditionné -> CONFLIT NOMMÉ : F11094 résumé dit 24 mois,
    l'onglet de la MÊME page dit « un délai d'un an » — les deux
    dates (2028-12-25 / 2027-12-25) voyagent, jamais de moyenne.
  FR cap vices : vente 2009-01-10, délivré 2026-12-25, découvert
    2028-11-30 -> action 2030-11-30 mais cap = vente+20 ans =
    2029-01-10 — LE CAP EST BINDANT ; vente 2008-11-20, découvert
    2028-11-30 -> cap 2028-11-20 ANTÉRIEUR à la découverte ->
    CAP_PASSED_BEFORE_DISCOVERY.
  FR remèdes datés (exemple officiel 3-janv -> 17-janv = +14) :
    demande 2027-01-20 -> réparation 2027-02-19 Friday (+30),
    remboursement 2027-02-03 Wednesday (+14).
  UK england, délivré 2026-12-25 : reject 2027-01-24 Sunday
    (« first day after » = jour 1 -> 30e jour = D+30) ; présomption
    2027-06-24 (anniversaire 25-jun moins un jour — « beginning with
    the day » inclut le jour même) ; forclusion 2032-12-25. nation
    absente -> LES DEUX dates (2032 EWG/NI, 2031 Scotland).
  UK bornes : découvert 2027-06-24 pile -> PAST_REJECT_IN_
    PRESUMPTION ; 2027-06-25 -> PAST_BURDEN_YOURS_IN_LIMITATION.
  Clamp fin de mois : délivré 2024-02-29 -> reject 2024-03-30
    Saturday ; présomption 2024-08-28 Wednesday (anniversaire
    29-août - 1) ; +6 ans = 2030-02-28 THURSDAY (jour 59 de 2030,
    1er janv mardi -> +58 -> mardi+2).
"""
from datetime import date, timedelta

from fastapi.testclient import TestClient

import main
import guaranteekit as gk

client = TestClient(main.app)


def LG(**kw):
    r = client.post("/api/v1/shop/legal-guarantee", json=kw)
    return r


def test_fr_gift_feb_window():
    # l'exact scénario « le cadeau tombe en panne le 16 janvier »
    r = LG(jurisdiction="FR", delivered_on="2026-12-25",
           discovered_on="2027-01-16", as_of="2027-01-16")
    assert r.status_code == 200
    b = r.json()
    a = b["conformite_action_by"]
    assert a["date"] == "2028-12-25" and a["weekday"] == "Monday"
    assert a["days_left"] == 709
    assert b["presumption_by"]["date"] == "2028-12-25"
    assert b["conformite_verdict"]["verdict"] == "WITHIN_PRESUMPTION"
    v = b["vices"]
    assert v["action_by"] == "2029-01-16"  # +2 ans depuis la DÉCOUVERTE
    assert v["cap_by"] == "2046-12-25"     # +20 ans depuis la vente
    assert v["binding"] == "action (2y from discovery)"
    assert v["days_left"] == 731
    assert b["table_version"] == "2026-11-24"


def test_fr_used_presumption_branch():
    b = LG(jurisdiction="FR", delivered_on="2026-12-25",
           condition="used", discovered_on="2028-06-10").json()
    assert b["presumption_by"]["date"] == "2027-12-25"
    assert b["presumption_by"]["weekday"] == "Saturday"
    assert b["conformite_action_by"]["date"] == "2028-12-25"
    assert b["conformite_verdict"]["verdict"] == "IN_WINDOW_BURDEN_YOURS"


def test_fr_refurbished_named_conflict():
    b = LG(jurisdiction="FR", delivered_on="2026-12-25",
           condition="refurbished").json()
    c = b["conflict"]
    assert c["positions"]["24_months"]["date"] == "2028-12-25"
    assert c["positions"]["12_months"]["date"] == "2027-12-25"
    # la table complète des conditions voyage aussi
    assert b["presumption_table_all_conditions"]["used"] == "2027-12-25"


def test_fr_vices_cap_binding():
    b = LG(jurisdiction="FR", delivered_on="2026-12-25",
           discovered_on="2028-11-30", sold_on="2009-01-10").json()
    v = b["vices"]
    assert v["action_by"] == "2030-11-30"
    assert v["cap_by"] == "2029-01-10"
    assert v["binding"] == "cap (20y)"
    assert v["effective_by"] == "2029-01-10"


def test_fr_cap_passed_before_discovery():
    b = LG(jurisdiction="FR", delivered_on="2008-11-25",
           discovered_on="2028-11-30", sold_on="2008-11-20").json()
    v = b["vices"]
    assert v["cap_by"] == "2028-11-20"
    assert v["verdict"] == "CAP_PASSED_BEFORE_DISCOVERY"
    assert "born closed" in v["why"]


def test_fr_remedy_clocks_official_example():
    # F11094 exemple officiel : demande 3 janvier -> remboursement
    # au plus tard 17 janvier : +14, pas +13, pas « lendemain+14 ».
    b = LG(jurisdiction="FR", delivered_on="2026-12-25",
           claim_requested_on="2027-01-03").json()
    assert b["refund_due_by"]["date"] == "2027-01-17"
    assert b["refund_due_by"]["weekday"] == "Sunday"
    # et le module dit pourquoi la règle « jour ouvrable » n'est
    # PAS appliquée : elle dépend du calendrier de l'ENTREPRISE.
    assert any("DANS L'ENTREPRISE" in c for c in b["conditions"])


def test_fr_remedy_clocks_jan20():
    b = LG(jurisdiction="FR", delivered_on="2026-12-25",
           claim_requested_on="2027-01-20").json()
    assert b["remedy_due_by"]["date"] == "2027-02-19"
    assert b["remedy_due_by"]["weekday"] == "Friday"
    assert b["refund_due_by"]["date"] == "2027-02-03"
    assert b["refund_due_by"]["weekday"] == "Wednesday"


def test_uk_three_clocks_no_nation():
    b = LG(jurisdiction="UK", delivered_on="2026-12-25",
           discovered_on="2027-01-16", as_of="2027-01-16").json()
    assert b["reject_by"]["date"] == "2027-01-24"
    assert b["reject_by"]["weekday"] == "Sunday"
    assert b["reject_by"]["days_left"] == 8
    assert b["presumption_by"]["date"] == "2027-06-24"
    assert b["presumption_by"]["weekday"] == "Thursday"
    lim = b["limitation_by"]
    assert lim["england_wales_northern_ireland"]["date"] == "2032-12-25"
    assert lim["scotland"]["date"] == "2031-12-25"
    assert b["verdict"]["verdict"] == "REJECT_WINDOW_OPEN"
    assert "not what you need" in b["verdict"]["why"] or \
        "NOT what you need" in b["verdict"]["why"]


def test_uk_nation_scotland_single():
    b = LG(jurisdiction="UK", delivered_on="2026-12-25",
           nation="scotland").json()
    assert b["limitation_by"]["date"] == "2031-12-25"
    assert b["limitation_by"]["weekday"] == "Thursday"
    assert "limitation_table_all_nations" in b


def test_uk_presumption_edges():
    b = LG(jurisdiction="UK", delivered_on="2026-12-25",
           discovered_on="2027-06-24").json()
    assert b["verdict"]["verdict"] == "PAST_REJECT_IN_PRESUMPTION"
    b = LG(jurisdiction="UK", delivered_on="2026-12-25",
           discovered_on="2027-06-25").json()
    assert b["verdict"]["verdict"] == "PAST_BURDEN_YOURS_IN_LIMITATION"
    b = LG(jurisdiction="UK", delivered_on="2026-12-25",
           nation="scotland", discovered_on="2031-12-26").json()
    assert b["verdict"]["verdict"] == "LIMITATION_PASSED"


def test_uk_condition_does_not_branch():
    # la branche occasion est un produit du DROIT FRANÇAIS ; l'importer
    # en UK serait la faute exacte que cette table existe pour refuser.
    b = LG(jurisdiction="UK", delivered_on="2026-12-25",
           condition="used").json()
    assert "does not branch" in b["condition_note"]
    assert b["reject_by"]["date"] == "2027-01-24"


def test_month_clamp():
    b = LG(jurisdiction="UK", delivered_on="2024-02-29").json()
    assert b["reject_by"]["date"] == "2024-03-30"
    assert b["reject_by"]["weekday"] == "Saturday"
    assert b["presumption_by"]["date"] == "2024-08-28"
    assert b["presumption_by"]["weekday"] == "Wednesday"
    assert b["limitation_by"]["england_wales_northern_ireland"][
        "date"] == "2030-02-28"
    assert b["limitation_by"]["england_wales_northern_ireland"][
        "weekday"] == "Thursday"


def test_refusals_carry_their_facts():
    r = LG(jurisdiction="US", delivered_on="2026-12-25")
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "jurisdiction"
    assert "state UCC" in e["message"]
    assert "/shop/return-deadline" in e["message"]
    e = LG(jurisdiction="AU", delivered_on="2026-12-25").json()["errors"][0]
    assert "reasonable time" in e["message"]
    e = LG(jurisdiction="BR", delivered_on="2026-12-25").json()["errors"][0]
    assert "90-day" in e["message"]
    e = LG(jurisdiction="DE", delivered_on="2026-12-25").json()["errors"][0]
    assert "never a borrowed" in e["message"]


def test_field_refusals():
    e = LG(jurisdiction="FR", delivered_on="2026-12-25",
           nation="scotland").json()["errors"][0]
    assert e["field"] == "nation"
    assert "ONE civil-code clock" in e["message"]
    e = LG(jurisdiction="UK", delivered_on="2026-12-25",
           claim_requested_on="2027-01-01").json()["errors"][0]
    assert e["field"] == "claim_requested_on"
    assert "waiting period" in e["message"]
    e = LG(jurisdiction="FR", delivered_on="2026-12-25",
           condition="dory").json()["errors"][0]
    assert e["field"] == "condition"
    e = LG(jurisdiction="FR", delivered_on="25/12/2026").json()["errors"][0]
    assert e["field"] == "delivered_on"
    # extra=forbid
    r = LG(jurisdiction="FR", delivered_on="2026-12-25",
           warranty="gold").json()
    assert r["error"] == "invalid_input"


def test_no_wall_clock_deterministic():
    kw = dict(jurisdiction="FR", delivered_on="2026-12-25",
              discovered_on="2027-01-16")
    b1 = LG(**kw).json()
    b2 = LG(**kw).json()
    assert b1["sha256"] == b2["sha256"]
    assert "days_left" not in b1["conformite_action_by"]  # as_of absent


def test_commercial_boundary_travels():
    # la frontière avec return-deadline est UNE CHAÎNE de la réponse,
    # pas seulement un tag du routeur.
    b = LG(jurisdiction="FR", delivered_on="2026-12-25").json()
    assert "/shop/return-deadline" in b["levers"]["commercial_window"]
    b = LG(jurisdiction="UK", delivered_on="2026-12-25").json()
    assert "policy, not statute" in b["levers"]["commercial_window"]
    assert "three clocks, not one" in b["misread_guard"]


def test_route_and_surfaces():
    r = client.get("/route", params={"q": "mon cadeau est en panne le "
                                          "16 janvier, la garantie "
                                          "légale jusqu'à quand"})
    assert r.status_code == 200
    names = [m["tool"] for m in r.json()["tools"][:3]]
    assert "shop_legal_guarantee" in names
    # la fenêtre COMMERCIALE ne doit pas voler l'horloge légale ni
    # l'inverse : « retourner le cadeau qui ne plaît pas » = retour.
    r = client.get("/route", params={"q": "je veux retourner le "
                                          "cadeau noël qui ne me "
                                          "plaît pas"})
    names = [m["tool"] for m in r.json()["tools"][:3]]
    assert "shop_return_deadline" in names
    assert "shop_legal_guarantee" not in names
    r = client.get("/tools/shop_legal_guarantee.json")
    assert r.status_code == 200
    assert r.json()["tier"] == "free"
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert "shop_legal_guarantee" in names and len(names) == 182  # +shop_withdrawal bundle107 ; +agent_tooltrim bundle106 ; +shop_soldes_be bundle105 ; +agent_costdiff bundle104 ; 178 avec shop_soldes_window bundle103 ; 177 avec shop_gift_voucher bundle102 (le compteur avait DÉRIVÉ ici, pêché par le pytest complet du cycle 103) ; 176 avec agent_contexttax bundle101
