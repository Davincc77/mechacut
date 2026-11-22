"""Bundle FIN — amortize + interest. Ancres : petit cas calculé à la main
ligne à ligne + invariants qui DÉFINISSENT l'objet."""
import sys
from decimal import Decimal
sys.path.insert(0, ".")
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def am(**kw):
    r = client.post("/api/v1/money/amortize", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def it(**kw):
    r = client.post("/api/v1/money/interest", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def test_amortize_hand_computed_three_months():
    d = am(principal=1000, annual_rate_pct=12, months=3)
    assert d["payment"] == "340.02"
    s = d["schedule"]
    assert Decimal(s[0]["interest"]) == Decimal("10.00")
    assert Decimal(s[1]["balance"]) == Decimal("336.66")
    assert s[-1]["balance"] == "0.00"          # jamais -0.01


def test_amortize_invariants_rederive():
    d = am(principal=15000, annual_rate_pct=4.5, months=24)
    pays = [Decimal(x["payment"]) for x in d["schedule"]]
    ints = [Decimal(x["interest"]) for x in d["schedule"]]
    ams = [Decimal(x["amortization"]) for x in d["schedule"]]
    assert sum(ams) == Decimal("15000.00")
    assert sum(pays) == Decimal(d["total_paid"])
    assert sum(ints) == Decimal(d["total_interest"])
    assert Decimal(d["total_paid"]) - Decimal(d["total_interest"]) == \
        Decimal("15000.00")


def test_amortize_zero_rate_no_crash():
    d = am(principal=1200, annual_rate_pct=0, months=12)
    assert d["mode"] == "zero_rate"
    assert d["payment"] == "100.00" and d["total_interest"] == "0.00"


def test_amortize_refuses_negative_and_absurd():
    r = client.post("/api/v1/money/amortize", json={
        "principal": 1000, "annual_rate_pct": -1, "months": 12})
    assert r.status_code == 400 and "negative" in r.text
    r2 = client.post("/api/v1/money/amortize", json={
        "principal": 1000, "annual_rate_pct": 1, "months": 601})
    assert r2.status_code == 400


def test_interest_hand_case_semestriel():
    d = it(principal=100, annual_rate_pct=100, years=1,
           compounds_per_year=2)
    assert d["final_amount"] == "225.00"        # 100*1.5^2
    assert d["effective_annual_rate_pct"] == "125.00000000"
    assert "A = P(1 + r/m)^(mt)" in d["formula"]


def test_interest_daily_compounding_sanity():
    d = it(principal=100, annual_rate_pct=10, years=1,
           compounds_per_year=365)
    assert d["effective_annual_rate_pct"].startswith("10.515")


def test_interest_money_never_floats():
    d = it(principal=0.1 + 0.2, annual_rate_pct=0, years=3)
    assert d["interest_earned"] == "0.00"
    assert d["final_amount"] == "0.30"          # pas 0.30000000000000004
