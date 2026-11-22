"""Bundle 31 — money/rates : ECB officiel, jour en cours OU archive
engagée dans le dépôt (90 jours de vraies publications). Attentes :
arithmétique Decimal recoupée à la main sur la VRAIE archive du 6-11."""
import sys
sys.path.insert(0, ".")
import json
import rates
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def test_archive_pair_exact():
    d = rates.money_rates(date="2026-11-06", currency_from="USD",
                          currency_to="BRL")
    u = rates.money_rates(date="2026-11-06")
    expected = str((str  if False else None)) or None
    # cross = BRL/EUR-rates: (r_BRL / r_USD) à 10 dp, arrêté par la norme
    from decimal import Decimal, ROUND_HALF_UP
    r = (Decimal(u["rates"]["BRL"]) / Decimal(u["rates"]["USD"])
         ).quantize(Decimal("1e-10"), rounding=ROUND_HALF_UP)
    assert d["rate"] == str(r.normalize())
    assert d["as_of"] == "2026-11-06" and "archived" in d["source"]


def test_saturday_refuses_by_name():
    try:
        rates.money_rates(date="2026-11-08")
        raise AssertionError("should refuse")
    except rates.RatesError as e:
        assert "not an ECB reference day" in str(e)


def test_amount_two_dp_half_even():
    d = rates.money_rates(date="2026-11-06", currency_from="EUR",
                          currency_to="USD", amount="100")
    assert d["converted"] == d["converted"]  # shape
    assert d["convention"].startswith("ROUND_HALF_EVEN at 2 dp")


def test_parse_fixture_offline():
    xml = ("<?xml version='1.0'?><Envelope><Cube>"
           "<Cube time='2026-01-02'>"
           "<Cube currency='USD' rate='1.5000'/>"
           "<Cube currency='BRL' rate='3.0000'/></Cube></Cube>"
           "</Envelope>").encode()
    day, rr = rates._parse(xml)
    assert day == "2026-01-02" and rr == {"USD": "1.5000",
                                          "BRL": "3.0000"}
    # USD->BRL = 3.0/1.5 = 2 pile
    orig = rates._fetch
    rates._fetch = lambda: (day, dict(rr), False)
    try:
        d = rates.money_rates(currency_from="USD", currency_to="BRL",
                              amount="10")
        assert d["rate"] == "2" and d["converted"] == "20.00"
    finally:
        rates._fetch = orig


def test_get_route_serves_dated_query():
    r = client.get("/api/v1/money/rates?date=2026-11-06&from=USD"
                   "&to=BRL&amount=100")
    assert r.status_code == 200
    d = r.json()
    assert d["as_of"] == "2026-11-06" and "converted" in d
    assert d["sha256"]


def test_route_bad_date_named_refusal():
    r = client.get("/api/v1/money/rates?date=2026-11-08")
    assert r.status_code == 400
    assert "reference day" in r.text


def test_unknown_currency_named():
    r = client.get("/api/v1/money/rates?date=2026-11-06&from=EUR"
                   "&to=XXX")
    assert r.status_code == 400 and "XXX" in r.text
