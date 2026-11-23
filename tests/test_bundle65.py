# -*- coding: utf-8 -*-
"""Bundle 65 — money/aging : la 1.1 de ROADMAP-FINANCE (l'impayé,
douleur n°1 de la facturation BR↔EU). Gold écrit à la main AVANT l'impl :
  F1 due 2026-10-01 100.00 -> 52 jours de retard -> 31-60
  F2 due 2026-11-01 200.00 -> 21                  -> 1-30
  F3 due 2026-12-01 300.00 -> courante (-9)
  F4 due 2026-09-01 50.00 payée 50.00 -> paid, hors ouvert
  ouvert 600.00, max 52.
Calendrier vérifié à la main : 10-01 -> 11-22 = 30 (reste d'octobre)
+ 22 = 52. La fenêtre est ouverte à gauche fermée à droite sur les
jours de retard (30 dans 1-30, 31 dans 31-60, 90 dans 61-90, 91 en
90+), échu aujourd'hui = courant, jamais « 0 jour de retard ».
"""
from fastapi.testclient import TestClient

import main
import routing

client = TestClient(main.app)

BASE = {"as_of": "2026-11-22", "invoices": [
    {"due": "2026-10-01", "amount": "100.00", "id": "F1"},
    {"due": "2026-11-01", "amount": "200.00", "id": "F2"},
    {"due": "2026-12-01", "amount": "300.00", "id": "F3"},
    {"due": "2026-09-01", "amount": "50.00", "paid": "50.00",
     "id": "F4"}]}


def _post(payload):
    r = client.post("/api/v1/money/aging", json=payload)
    return r.status_code, r.json()


# ------------------------------------------------------------ le gold
def test_gold_a_main():
    s, b = _post(BASE)
    assert s == 200
    st = {i["id"]: i for i in b["invoices"]}
    assert st["F1"]["status"] == "31-60" and st["F1"]["days_overdue"] == 52
    assert st["F2"]["status"] == "1-30" and st["F2"]["days_overdue"] == 21
    assert st["F3"]["status"] == "current" and st["F3"]["days_overdue"] == -9
    assert st["F4"]["status"] == "paid"
    assert b["open_total"] == "600.00"
    assert b["max_days_overdue"] == 52
    lab = {x["label"]: x for x in b["buckets"]}
    assert lab["current"]["total"] == "300.00"
    assert lab["1-30"]["total"] == "200.00"
    assert lab["31-60"]["total"] == "100.00"
    assert lab["61-90"]["total"] == "0.00"
    assert b["count"] == 4 and b["paid_count"] == 1


def test_boundaries_windows():
    # 30 -> 1-30 | 31 -> 31-60 | 90 -> 61-90 | 91 -> 90+ | due today = current
    for due, want, days in (("2026-10-23", "1-30", 30),
                            ("2026-10-22", "31-60", 31),
                            ("2026-08-24", "61-90", 90),
                            ("2026-08-23", "90+", 91),
                            ("2026-11-22", "current", 0)):
        s, b = _post({"as_of": "2026-11-22",
                      "invoices": [{"due": due, "amount": "10.00"}]})
        assert s == 200
        assert b["invoices"][0]["status"] == want, (due, want, b)
        assert b["invoices"][0]["days_overdue"] == days


def test_custom_buckets():
    s, b = _post({"as_of": "2026-11-22", "buckets": [15, 45],
                  "invoices": [{"due": "2026-11-01", "amount": "7.00"}]})
    assert s == 200
    labs = [x["label"] for x in b["buckets"]]
    assert labs == ["current", "1-15", "16-45", "45+"]
    assert b["invoices"][0]["status"] == "16-45"


# ------------------------------------------------------------ refus
def _refuse(payload, needle):
    s, b = _post(payload)
    assert s == 400, b
    msgs = " ".join(e["message"] for e in b["errors"])
    assert needle in msgs, msgs


def test_slashed_date_refused_not_guessed():
    _refuse({"as_of": "22/11/2026",
             "invoices": [{"due": "2026-10-01", "amount": "1.00"}]},
            "ISO calendar date")
    _refuse({"as_of": "2026-11-22",
             "invoices": [{"due": "01/10/2026", "amount": "1.00"}]},
            "ISO calendar date")


def test_grouped_amount_refused_with_pointing():
    _refuse({"as_of": "2026-11-22",
             "invoices": [{"due": "2026-10-01", "amount": "1,234.56"}]},
            "num/parse")


def test_overpaid_is_a_refusal_not_a_negative_bucket():
    _refuse({"as_of": "2026-11-22",
             "invoices": [{"due": "2026-10-01", "amount": "10.00",
                           "paid": "12.00"}]},
            "apply-payments")


def test_duplicate_ids_refused():
    _refuse({"as_of": "2026-11-22", "invoices": [
        {"due": "2026-10-01", "amount": "1.00", "id": "X"},
        {"due": "2026-10-02", "amount": "2.00", "id": "X"}]},
        "duplicate invoice id")


def test_buckets_not_increasing_refused():
    _refuse({"as_of": "2026-11-22", "buckets": [60, 30],
             "invoices": [{"due": "2026-10-01", "amount": "1.00"}]},
            "strictly increasing")


def test_empty_ledger_refused_not_zeros():
    _refuse({"as_of": "2026-11-22", "invoices": []},
            "empty ledger")


def test_negative_amount_refused():
    _refuse({"as_of": "2026-11-22",
             "invoices": [{"due": "2026-10-01", "amount": "-5.00"}]},
            "negative")


# ------------------------------------------------------- câblage complet
def test_same_input_same_sha():
    _, a = _post(BASE)
    _, b = _post(BASE)
    assert a["sha256"] == b["sha256"]


def test_wired_everywhere():
    names = [t["name"] for t in main.MCP_TOOLS]
    assert "money_aging" in names
    routes = [t[1] for t in routing.TABLE]
    assert "/api/v1/money/aging" in routes
    src = open("main.py", encoding="utf-8").read()
    assert "receivable buckets" in src          # en-tête docs
    assert "due-date buckets (free)" in src     # manifest
