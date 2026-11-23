# -*- coding: utf-8 -*-
"""Bundle 67 — ledger/apply-payments (ROADMAP-FINANCE 1.2).

Le rapprochement que le refus d'aging promet mot pour mot
(« reconciliation is ledger/apply-payments ») — une promesse de
message d'erreur devient un outil, vérifié ici : le message pointe
une route qui EXISTE.

Numéro : 66 était pris par la boucle (untracked, intouchable) — 67
réclamé ici, re-vérifié au commit (leçon bundle61 : le numéro est un
nom contentieux).

Gold écrit à la main avant l'impl :
  F1 100.00 (dû 10-01), F2 200.00 (11-01), F3 300.00 (12-01)
  P1 250.00 -> F1 100 + F2 150 ; P2 400.00 -> F2 50 + F3 300 + 50 non appliqué
  totaux : payment 650.00, applied 600.00, unapplied 50.00, open 0.00
"""
from fastapi.testclient import TestClient

import main
import routing

client = TestClient(main.app)

INV = [{"id": "F1", "due": "2026-10-01", "amount": "100.00"},
       {"id": "F2", "due": "2026-11-01", "amount": "200.00"},
       {"id": "F3", "due": "2026-12-01", "amount": "300.00"}]
PAY = [{"id": "P1", "date": "2026-11-15", "amount": "250.00"},
       {"id": "P2", "date": "2026-11-20", "amount": "400.00"}]


def _post(invoices=INV, payments=PAY):
    r = client.post("/api/v1/ledger/apply-payments",
                    json={"invoices": invoices, "payments": payments})
    return r.status_code, r.json()


def test_gold_a_main():
    s, b = _post()
    assert s == 200
    inv = {x["id"]: x for x in b["invoices"]}
    pay = {x["id"]: x for x in b["payments"]}
    assert inv["F1"]["status"] == "paid" and inv["F1"]["applied"] == "100.00"
    assert inv["F2"]["applied"] == "200.00" and inv["F3"]["applied"] == "300.00"
    assert pay["P1"]["allocations"] == [
        {"invoice": "F1", "amount": "100.00"},
        {"invoice": "F2", "amount": "150.00"}]
    assert pay["P2"]["leftover"] == "50.00"
    assert b["payment_total"] == "650.00"
    assert b["applied_total"] == "600.00"
    assert b["unapplied_total"] == "50.00"
    assert b["open_total"] == "0.00"


def test_invoices_keep_input_order_ledger_is_not_resorted():
    _, b = _post()
    assert [x["id"] for x in b["invoices"]] == ["F1", "F2", "F3"]


def test_tie_on_due_keeps_input_order():
    s, b = _post(
        [{"id": "A", "due": "2026-10-01", "amount": "10.00"},
         {"id": "B", "due": "2026-10-01", "amount": "10.00"}],
        [{"id": "P", "date": "2026-11-01", "amount": "10.00"}])
    assert s == 200
    assert b["payments"][0]["allocations"] == [{"invoice": "A",
                                                "amount": "10.00"}]


def test_partial_and_previously_paid():
    s, b = _post([{"id": "F", "due": "2026-10-01", "amount": "100.00",
                   "paid": "40.00"}],
                 [{"id": "P", "date": "2026-11-01", "amount": "60.00"}])
    assert s == 200
    f = b["invoices"][0]
    assert f["status"] == "paid" and f["applied"] == "60.00" \
        and f["outstanding"] == "0.00"
    s, b = _post([{"id": "F", "due": "2026-10-01", "amount": "100.00"}],
                 [{"id": "P", "date": "2026-11-01", "amount": "30.00"}])
    f = b["invoices"][0]
    assert f["status"] == "partial" and f["outstanding"] == "70.00"


def _refuse(invoices, payments, needle):
    s, b = _post(invoices, payments)
    assert s == 400, b
    assert needle in " ".join(e["message"] for e in b["errors"])


def test_refusals_are_named():
    _refuse([{"id": "F", "due": "2026-10-01", "amount": "10.00"}],
            [{"id": "P", "date": "2026-11-01", "amount": "-5.00"}],
            "credit note")
    _refuse([{"id": "F", "due": "2026-10-01", "amount": "10.00"}],
            [{"id": "P", "date": "2026-11-01", "amount": "0.00"}],
            "zero")
    _refuse([{"id": "F", "due": "2026-10-01", "amount": "10.005"}],
            [{"id": "P", "date": "2026-11-01", "amount": "1.00"}],
            "sub-cent")
    _refuse([{"id": "F", "due": "2026-10-01", "amount": "10.00"},
             {"id": "F", "due": "2026-10-02", "amount": "10.00"}],
            [{"id": "P", "date": "2026-11-01", "amount": "1.00"}],
            "duplicate invoice id")
    _refuse([{"id": "F", "due": "01/10/2026", "amount": "10.00"}],
            [{"id": "P", "date": "2026-11-01", "amount": "1.00"}],
            "ISO calendar date")


def test_empty_sides_refused_not_zeros():
    s, b = _post([], PAY)
    assert s == 400 and "nothing to apply" in str(b)
    s, b = _post(INV, [])
    assert s == 400 and "table of zeros" in str(b)


def test_promised_route_exists():
    # le message de refus d'aging promet cette route — la promesse
    # est vérifiée, pas décorative
    r = client.post("/api/v1/money/aging", json={
        "as_of": "2026-11-22", "invoices": [
            {"id": "X", "due": "2026-10-01", "amount": "10.00",
             "paid": "12.00"}]})
    msg = " ".join(e["message"] for e in r.json()["errors"])
    assert "ledger/apply-payments" in msg
    s, _ = _post([{"id": "X", "due": "2026-10-01", "amount": "10.00",
                   "paid": "12.00"}], PAY)
    assert s == 400  # ici aussi le sur-paiement en face est refusé


def test_wired_and_deterministic():
    names = [t["name"] for t in main.MCP_TOOLS]
    assert "ledger_apply_payments" in names
    assert "/api/v1/ledger/apply-payments" in [t[1]
                                               for t in routing.TABLE]
    _, a = _post()
    _, b = _post()
    assert a["sha256"] == b["sha256"]
