# -*- coding: utf-8 -*-
"""Bundle 74 — ledger/summary (ROADMAP-FINANCE 1.3, le troisième
souffle de la ligne F1 : aging → apply-payments → SUMMARY).

Aspire le bilan mensuel de Ponte (app.py _annual, by_month) : la
même agrégation calendrier, mais en Decimal exact — Ponte somme des
floats et round(…, 2) ; ici la chaîne de soldes est une soustraction
après soustraction, jamais un arrondi.

Gold écrit à la MAIN avant l'impl (23-11 ~09h50), additions tracées :
  opening_balance par défaut 0.00
  2026-09-05  +1000.00
  2026-09-20    -40.50   -> sept : in 1000.00, out 40.50,
                             net 959.50 (1000.00-40.50), closing 959.50, n=2
  (octobre sans écriture — le report de chaîne EST un mois rendu)
                             oct  : 0.00/0.00/0.00, closing 959.50, n=0
  2026-11-02  -600.25
  2026-11-30   +12.55   -> nov  : in 12.55, out 600.25,
                             net -587.70, closing 371.80
                             (959.50 + 12.55 = 972.05 ; 972.05-600.25=371.80), n=2
  2026-12-15    -0.05   -> déc  : in 0.00, out 0.05, net -0.05,
                             closing 371.75 (371.80-0.05), n=1
  totals : count 5, in 1012.55 (1000.00+12.55),
           out 640.80 (40.50+600.25+0.05), net 371.75 (1012.55-640.80)
  closing_balance final 371.75 == opening 0.00 + net 371.75
Variantes tracées main :
  opening "-3.50" : sept closing 956.00 ; final 368.25 (371.75-3.50)
  année : {+10.00 au 2026-12-31, -10.00 au 2027-01-01}
          -> mois ["2026-12","2027-01"], soldes ["10.00","0.00"]
Plafond tracé main : 2000-01..2099-12 = 12*100 = 1200 mois -> passe ;
2000-01..2100-01 = 1201 mois -> refus nommé.
"""
from decimal import Decimal

from fastapi.testclient import TestClient

import main
import routing

client = TestClient(main.app)

ENTRIES = [
    {"date": "2026-09-05", "amount": "1000.00"},
    {"date": "2026-09-20", "amount": "-40.50"},
    {"date": "2026-11-02", "amount": "-600.25"},
    {"date": "2026-11-30", "amount": "12.55"},
    {"date": "2026-12-15", "amount": "-0.05"},
]


def _post(entries=ENTRIES, opening=None):
    body = {"entries": entries}
    if opening is not None:
        body["opening_balance"] = opening
    r = client.post("/api/v1/ledger/summary", json=body)
    return r.status_code, r.json()


def test_route_and_table_wired():
    names = [row[0] for row in routing.TABLE]
    assert "ledger_summary" in names
    assert "/agent/manifest" not in names


def test_gold_main_chain():
    s, b = _post()
    assert s == 200
    assert b["opening_balance"] == "0.00"
    assert b["months_emitted"] == 4
    sept, oct_, nov, dec = b["months"]
    assert sept == {"month": "2026-09", "count": 2, "inflow": "1000.00",
                    "outflow": "40.50", "net": "959.50",
                    "closing_balance": "959.50"}
    assert oct_ == {"month": "2026-10", "count": 0, "inflow": "0.00",
                    "outflow": "0.00", "net": "0.00",
                    "closing_balance": "959.50"}
    assert nov == {"month": "2026-11", "count": 2, "inflow": "12.55",
                   "outflow": "600.25", "net": "-587.70",
                   "closing_balance": "371.80"}
    assert dec == {"month": "2026-12", "count": 1, "inflow": "0.00",
                   "outflow": "0.05", "net": "-0.05",
                   "closing_balance": "371.75"}
    assert b["totals"] == {"count": 5, "inflow": "1012.55",
                           "outflow": "640.80", "net": "371.75"}
    assert b["closing_balance"] == "371.75"


def test_empty_month_is_a_month():
    # « report » : la chaîne de soldes traverse le trou du calendrier ;
    # un mois sans écriture est rendu, jamais inventé ailleurs.
    _, b = _post()
    assert [m["month"] for m in b["months"]] == [
        "2026-09", "2026-10", "2026-11", "2026-12"]


def test_unsorted_entries_return_calendar_order():
    shuffled = [ENTRIES[4], ENTRIES[1], ENTRIES[3], ENTRIES[0], ENTRIES[2]]
    _, b = _post(entries=shuffled)
    assert [m["month"] for m in b["months"]] == [
        "2026-09", "2026-10", "2026-11", "2026-12"]
    assert b["closing_balance"] == "371.75"


def test_running_balance_invariant_every_month():
    # invariant rendu public par le test : closing_i == closing_{i-1} +
    # net_i (le premier part de opening), et solde final == opening + Σ.
    _, b = _post()
    bal = Decimal(b["opening_balance"])
    for m in b["months"]:
        bal += Decimal(m["net"])
        assert Decimal(m["closing_balance"]) == bal
    assert Decimal(b["closing_balance"]) == bal
    assert bal == Decimal(b["opening_balance"]) + Decimal(b["totals"]["net"])


def test_opening_balance_negative_shifts_chain():
    _, b = _post(opening="-3.50")
    assert b["months"][0]["closing_balance"] == "956.00"
    assert b["closing_balance"] == "368.25"


def test_year_boundary_chain():
    _, b = _post(entries=[{"date": "2026-12-31", "amount": "10.00"},
                          {"date": "2027-01-01", "amount": "-10.00"}])
    assert [m["month"] for m in b["months"]] == ["2026-12", "2027-01"]
    assert [m["closing_balance"] for m in b["months"]] == ["10.00", "0.00"]


def test_span_cap_1200_months_passes_1201_refused():
    ok = [{"date": "2000-01-15", "amount": "1.00"},
          {"date": "2099-12-15", "amount": "-1.00"}]
    s, b = _post(entries=ok)
    assert s == 200 and b["months_emitted"] == 1200
    over = [{"date": "2000-01-15", "amount": "1.00"},
            {"date": "2100-01-15", "amount": "-1.00"}]
    s2, b2 = _post(entries=over)
    assert s2 == 400
    assert "months" in b2["errors"][0]["message"]


def test_empty_entries_refused_not_a_zero_table():
    s, b = _post(entries=[])
    assert s == 400
    msg = b["errors"][0]["message"]
    assert "entries" in msg or "summar" in msg


def test_zero_entry_refused_by_name():
    s, b = _post(entries=[{"date": "2026-09-05", "amount": "0.00"}])
    assert s == 400
    assert "zero" in b["errors"][0]["message"]


def test_grouped_amount_refused_with_pointer():
    s, b = _post(entries=[{"date": "2026-09-05", "amount": "1,234.56"}])
    assert s == 400
    assert "num/parse" in b["errors"][0]["message"]


def test_sub_cent_amount_refused():
    s, b = _post(entries=[{"date": "2026-09-05", "amount": "10.001"}])
    assert s == 400
    assert "sub-cent" in b["errors"][0]["message"] or "cent" in b["errors"][0]["message"]


def test_slashed_date_refused():
    s, b = _post(entries=[{"date": "2026/09/05", "amount": "10.00"}])
    assert s == 400
    assert "YYYY-MM-DD" in b["errors"][0]["message"]


def test_impossible_calendar_date_refused():
    s, b = _post(entries=[{"date": "2026-02-30", "amount": "10.00"}])
    assert s == 400


def test_opening_balance_sub_cent_refused():
    s, b = _post(opening="0.001")
    assert s == 400


def test_determinism_same_bytes_same_sha():
    _, a = _post()
    _, b = _post()
    assert a["sha256"] == b["sha256"]


def test_route_finds_the_summary():
    # mot du NOM : « summary » (poids 4) survit seul ; la phrase
    # running balance doit atterrir ici, pas chez aging.
    for phrase, want in [
        ("ledger summary", "ledger_summary"),
        ("monthly summary of my journal with running balance",
         "ledger_summary"),
    ]:
        r = client.get("/route", params={"q": phrase}).json()
        top = r["tools"][0]["tool"] if r["tools"] else None
        assert top == want, (phrase, top)
