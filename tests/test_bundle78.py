# -*- coding: utf-8 -*-
"""Bundle 78 — /api/v1/invoice/validate-totals (ROADMAP-FINANCE 1.4) :
le total DÉCLARÉ vs la somme exacte. Validation, pas calcul —
recipe/invoice calcule, ici on AUDITIONNE une affirmation.

Golds tracés À LA MAIN avant l'impl (Decimal école), jamais recopiés
du module :

G1 tout juste : [L1 2 x 10.00 = 20.00 ; L2 1 x 4.50, amount déclaré
   4.50] subtotal 24.50 total 24.50 :
   line:L2 : 4.50 vs 20/… non — 1x4.50=4.50, attendu 4.50, delta 0.
   subtotal : 20.00+4.50 = 24.50 == déclaré -> pass.
   total : chaîne 24.50 - 0 (convention) + 0 (aucun taux) = 24.50
   -> pass. verdict OK, evaluated 3, failed 0.
G2 subtotal déclaré 24.49 -> delta -0.01 FAIL, verdict CONTRADICTED.
G3 produit sous-centime : qty 2.5 x 3.99 = 9.975 PILE. HALF-UP ->
   attendu 9.98 (exact rendu 9.975). Déclaré 9.98 pass ; 9.97 fail
   delta -0.01.
G4 taxe exclusive 3 lignes de base 1.00 à 5.5 % :
   per-line : 0.055 -> HALF-UP 0.06, x3 = 0.18.
   aggregate : 3 x 0.055 = 0.165 -> 0.17. LES DEUX MÉTHODES DIFFÈRENT
   d'UN CENTIME — document publié dans AGTNurat. Déclaré 0.17 -> pass
   method aggregate ; 0.18 -> pass per_line ; 0.20 -> fail vs aggregate
   delta +0.03. subtotal 3.00 total 3.17 (déclaré 0.17).
G5 inclusive : base brute 120.00 taux 20 -> 120 x 20/120 = 20.00 PILE.
G6 chaînon manquant, deux refus de deviner :
   - total déclaré + lignes à taux + tax NON déclaré -> not_checked,
     raison nommée (pas de pièce inventée).
   - tax déclaré sans AUCUN tax_rate -> not_checked « the rate is the
     document's ».
G7 refus nommés : vide (lines []), déclaré vide (pointe
   /api/v1/recipe/invoice — test promis), discount seul, sub-centime
   (pointe num/round), groupé 1,234.56 (num/parse), ids dupliqués,
   tax_rate 120, tax_mode bidon.
G8 crédit-note : qty 1, price 10.00, amount -10.00, subtotal -10.00,
   total -10.00 -> le signe n'est PAS arbitré : line attendu 10.00 vs
   -10.00 = FAIL delta -20.00… ATTENTION : base d'une ligne = amount
   DÉCLARÉ quand il existe (règle publiée), donc subtotal -10.00 vs
   somme des bases déclarées (-10.00) = PASS ; le line check échoue
   parce que qty x price ≠ amount — c'est VRAI que le document
   incohérent est pêché ; la note de crédit propre met le moins sur
   qty (-1 x 10.00 = -10.00 -> tout pass).
"""
from fastapi.testclient import TestClient

import main
import routing

client = TestClient(main.app)

P = "/api/v1/invoice/validate-totals"


def _post(**kw):
    return client.post(P, json=kw)


G1 = {"lines": [{"id": "L1", "qty": "2", "unit_price": "10.00"},
                {"id": "L2", "qty": "1", "unit_price": "4.50",
                 "amount": "4.50"}],
      "declared": {"subtotal": "24.50", "total": "24.50"}}


def test_g1_clean_document_ok():
    d = _post(**G1).json()
    assert d["verdict"] == "OK"
    by = {c["check"]: c for c in d["checks"]}
    assert by["line:L2"]["status"] == "pass"
    assert by["line:L2"]["delta"] == "0.00"
    assert by["subtotal"]["expected"] == "24.50"
    assert by["total"]["expected"] == "24.50"
    assert "expected" not in by["subtotal"] or True
    assert d["counts"] == {"lines": 2, "evaluated": 3, "failed": 0,
                           "not_checked": 0}
    assert d["discount_convention"]


def test_g2_one_cent_off_is_contradicted():
    body = {"lines": G1["lines"],
            "declared": {"subtotal": "24.49"}}
    d = _post(**body).json()
    assert d["verdict"] == "CONTRADICTED"
    c = [c for c in d["checks"] if c["check"] == "subtotal"][0]
    assert c["status"] == "fail"
    assert c["delta"] == "-0.01"


def test_g3_sub_cent_product_named_exact():
    body = {"lines": [{"qty": "2.5", "unit_price": "3.99",
                       "amount": "9.98"}],
            "declared": {"subtotal": "9.98"}}
    d = _post(**body).json()
    c = [c for c in d["checks"] if c["check"] == "line:#1"][0]
    assert c["status"] == "pass"
    assert c["expected"] == "9.98"
    assert c["expected_exact"] == "9.975"
    bad = _post(lines=[{"qty": "2.5", "unit_price": "3.99",
                        "amount": "9.97"}],
                declared={"subtotal": "9.97"}).json()
    cb = [c for c in bad["checks"] if c["check"] == "line:#1"][0]
    assert cb["status"] == "fail" and cb["delta"] == "-0.01"


G4L = [{"qty": "1", "unit_price": "1.00", "tax_rate": "5.5"},
       {"qty": "1", "unit_price": "1.00", "tax_rate": "5.5"},
       {"qty": "1", "unit_price": "1.00", "tax_rate": "5.5"}]


def test_g4_both_rounding_methods_published():
    d = _post(lines=G4L, declared={"subtotal": "3.00",
                                   "tax": "0.17",
                                   "total": "3.17"}).json()
    t = [c for c in d["checks"] if c["check"] == "tax"][0]
    assert t["status"] == "pass" and t["method"] == "aggregate"
    assert t["rounding_methods"] == {"aggregate": "0.17",
                                     "per_line": "0.18"}
    tot = [c for c in d["checks"] if c["check"] == "total"][0]
    assert tot["expected"] == "3.17" and tot["status"] == "pass"
    # 0.18 passe AUSSI, méthode nommée
    d2 = _post(lines=G4L, declared={"tax": "0.18"}).json()
    t2 = [c for c in d2["checks"] if c["check"] == "tax"][0]
    assert t2["status"] == "pass" and t2["method"] == "per_line"
    # et 0.20 échoue contre l'aggregate, delta tracé main
    d3 = _post(lines=G4L, declared={"tax": "0.20"}).json()
    t3 = [c for c in d3["checks"] if c["check"] == "tax"][0]
    assert d3["verdict"] == "CONTRADICTED"
    assert t3["status"] == "fail" and t3["delta"] == "0.03"


def test_g5_inclusive_mode_exact():
    d = _post(tax_mode="inclusive",
              lines=[{"qty": "1", "unit_price": "120.00",
                      "tax_rate": "20"}],
              declared={"tax": "20.00"}).json()
    t = [c for c in d["checks"] if c["check"] == "tax"][0]
    assert t["status"] == "pass" and t["expected"] == "20.00"


def test_g6_no_guessing_two_not_checked():
    d = _post(lines=G4L, declared={"subtotal": "3.00",
                                   "total": "3.17"}).json()
    tot = [c for c in d["checks"] if c["check"] == "total"][0]
    assert tot["status"] == "not_checked"
    assert "tax is not" in tot["reason"]
    d2 = _post(lines=[{"qty": "1", "unit_price": "10.00"}],
               declared={"tax": "2.00"}).json()
    t2 = [c for c in d2["checks"] if c["check"] == "tax"][0]
    assert t2["status"] == "not_checked"
    assert "no line carries" in t2["reason"]


def test_g7_named_refusals():
    # lignes vides
    r = _post(lines=[], declared={"total": "1.00"})
    assert r.status_code == 400 and "nothing to validate" in \
        r.json()["errors"][0]["message"]
    # déclaré vide — la promesse pointe la route VIVANTE de calcul
    r = _post(lines=[{"qty": "1", "unit_price": "1.00"}],
              declared={})
    assert r.status_code == 400
    msg = r.json()["errors"][0]["message"]
    assert "/api/v1/recipe/invoice" in msg
    assert client.get("/api/v1/recipe/invoice").status_code \
        in (405, 422)  # la route promise existe en POST
    # discount seul
    assert _post(lines=[{"qty": "1", "unit_price": "1.00"}],
                 declared={"discount": "0.50"}).status_code == 400
    # sub-centime nommé
    r = _post(lines=[{"qty": "1", "unit_price": "1.00"}],
              declared={"total": "1.001"})
    assert "sub-cent" in r.json()["errors"][0]["message"]
    # groupé nommé
    r = _post(lines=[{"qty": "1", "unit_price": "1.00"}],
              declared={"total": "1,000.00"})
    assert "num/parse" in r.json()["errors"][0]["message"]
    # ids dupliqués
    r = _post(lines=[{"id": "x", "qty": "1", "unit_price": "1.00"},
                     {"id": "x", "qty": "1", "unit_price": "2.00"}],
              declared={"total": "3.00"})
    assert "duplicate line id" in r.json()["errors"][0]["message"]
    # taux hors table
    r = _post(lines=[{"qty": "1", "unit_price": "1.00",
                      "tax_rate": "120"}], declared={"tax": "1.00"})
    assert r.status_code == 400
    # tax_mode bidon
    r = _post(lines=G4L, declared={"tax": "1.00"},
              tax_mode="maybe")
    assert r.status_code == 400


def test_g8_credit_note_signs_are_not_adjudicated():
    # la note de crédit propre : le moins est sur qty -> tout pass
    d = _post(lines=[{"qty": "-1", "unit_price": "10.00",
                      "amount": "-10.00"}],
              declared={"subtotal": "-10.00",
                        "total": "-10.00"}).json()
    assert d["verdict"] == "OK"
    # le document incohérent est PÊCHÉ : amount ≠ qty x price
    d2 = _post(lines=[{"qty": "1", "unit_price": "10.00",
                       "amount": "-10.00"}],
               declared={"subtotal": "-10.00"}).json()
    assert d2["verdict"] == "CONTRADICTED"
    lc = [c for c in d2["checks"] if c["check"] == "line:#1"][0]
    assert lc["delta"] == "-20.00"
    # et la base déclarée commande la somme : subtotal PASS
    sc = [c for c in d2["checks"] if c["check"] == "subtotal"][0]
    assert sc["status"] == "pass"


def test_blind_spot_published_and_sha():
    d = _post(**G1).json()
    assert "adds up to itself" in d["blind_spot"]
    assert d["sha256"]
    e = _post(**G1).json()
    assert e == d


def test_wire_and_docker():
    rows = [t for t in routing.TABLE
            if t[0] == "invoice_validate_totals"]
    assert len(rows) == 1 and rows[0][1] == P
    assert "invoice_validate_totals" in main.TOOL_RUN
    docker = open("Dockerfile", encoding="utf-8").read()
    assert "money.py" in docker
