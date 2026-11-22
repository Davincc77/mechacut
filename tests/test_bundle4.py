"""Bundle 4.1 — numbers: closed-table formatting, refusal-not-guessing parse,
exact Decimal rounding."""

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _deterministic(url, payload):
    r1 = client.post(url, json=payload)
    r2 = client.post(url, json=payload)
    assert r1.status_code == r2.status_code
    assert r1.content == r2.content
    return r1


def test_format_table():
    cases = [
        ({"value": 1234.567}, "1,234.567"),
        ({"value": 1234.567, "style": "currency", "currency": "usd"},
         "$1,234.57"),
        ({"value": 1234.567, "locale": "fr-FR", "style": "currency",
          "currency": "EUR"}, "1\u00A0234,57\u00A0\u20AC"),
        ({"value": "1234567.891", "locale": "de-DE", "decimals": 2},
         "1.234.567,89"),
        ({"value": 1234.6, "locale": "ja-JP", "style": "currency",
          "currency": "JPY"}, "\u00A51,235"),
        ({"value": "0.1234", "style": "percent"}, "12.34%"),
        ({"value": -42.5, "style": "currency", "currency": "EUR"},
         "-\u20AC42.50"),
        ({"value": 1000000}, "1,000,000"),
    ]
    for body, expected in cases:
        r = _deterministic("/api/v1/num/format", body)
        assert r.status_code == 200, r.text
        assert r.json()["formatted"] == expected, (body, r.json())


def test_format_unknown_locale_400():
    r = client.post("/api/v1/num/format", json={"value": 1, "locale": "xx-XX"})
    assert r.status_code == 400
    assert "closed table" in r.text


def test_parse_canonical_forms():
    for text, expected in [
        ("1,234.56", "1234.56"), ("1.234,56", "1234.56"),
        ("1'234.56", "1234.56"), ("1.23e4", "12300"),
        ("-$12.30", "-12.3"),
    ]:
        r = _deterministic("/api/v1/num/parse", {"text": text})
        assert r.json()["decimal_string"] == expected, text


def test_parse_currency_and_percent():
    r = client.post("/api/v1/num/parse", json={"text": "€1 234,56"})
    b = r.json()
    assert b["currency"] == "EUR" and b["decimal_string"] == "1234.56"
    r = client.post("/api/v1/num/parse", json={"text": "12,34%"})
    assert r.json()["percent"] is True
    r = client.post("/api/v1/num/parse", json={"text": "USD 120"})
    assert r.json()["currency"] == "USD"


def test_parse_refuses_ambiguity():
    r = client.post("/api/v1/num/parse", json={"text": "1,234"})
    assert r.status_code == 400
    assert r.json()["error"] == "unparsable_number"
    assert "prefer" in r.text
    r = client.post("/api/v1/num/parse",
                    json={"text": "1,234", "prefer": "group"})
    assert r.json()["decimal_string"] == "1234"
    r = client.post("/api/v1/num/parse",
                    json={"text": "1,234", "prefer": "decimal"})
    assert r.json()["decimal_string"] == "1.234"


def test_round_modes():
    r = _deterministic("/api/v1/num/round", {"value": 2.5})
    assert r.json()["result"] == "2"          # banker's default
    r = client.post("/api/v1/num/round", json={"value": 2.5,
                                               "mode": "half_up"})
    assert r.json()["result"] == "3"
    r = client.post("/api/v1/num/round", json={"value": "0.145",
                                               "places": 2})
    assert r.json()["result"] == "0.14"
    r = client.post("/api/v1/num/round", json={"value": "0.145",
                                               "places": 2,
                                               "mode": "half_up"})
    assert r.json()["result"] == "0.15"
    r = client.post("/api/v1/num/round",
                    json={"value": "12345678901234567890.123", "places": 1,
                          "mode": "up"})
    assert r.json()["result"] == "12345678901234567890.2"  # beyond float
    r = client.post("/api/v1/num/round", json={"value": 12345,
                                               "places": 3,
                                               "significant": True})
    assert r.json()["result"] == "12300"
    r = client.post("/api/v1/num/round", json={"value": "1.1", "mode": "ceil"})
    assert r.json()["result"] == "2"


def test_mcp_num_tools():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/call",
                                  "params": {"name": "num_round",
                                             "arguments": {"value": "2.675",
                                                           "places": 2,
                                                           "mode": "half_up"}}})
    assert '"result": "2.68"' in r.json()["result"]["content"][0]["text"]


# ------------------------------------------------------- lot 4.2: units

def test_units_table():
    cases = [
        ({"value": 100, "from": "km", "to": "mi"}, "62.1371192237"),
        ({"value": 100, "from": "C", "to": "F"}, "212"),
        ({"value": 212, "from": "F", "to": "K"}, "373.15"),
        ({"value": 150, "from": "lb", "to": "kg"}, "68.0388555"),
        ({"value": 10**9, "from": "B", "to": "GiB"}, "0.9313225746"),
        ({"value": 1, "from": "gallon", "to": "l"}, "3.785411784"),
        ({"value": 10, "from": "acre", "to": "ha"}, "4.0468564224"),
        ({"value": 90, "from": "km/h", "to": "m/s"}, "25"),
    ]
    for body, expected in cases:
        r = _deterministic("/api/v1/units/convert", body)
        assert r.status_code == 200, r.text
        assert r.json()["value"] == expected, (body, r.json())


def test_units_refusals():
    r = client.post("/api/v1/units/convert",
                    json={"value": 1, "from": "kg", "to": "km"})
    assert r.status_code == 400
    assert "cross-family" in r.text
    r = client.post("/api/v1/units/convert",
                    json={"value": 1, "from": "hand", "to": "m"})
    assert r.status_code == 400
    assert "closed families" in r.text


# ------------------------------------------------------- lot 4.2: money

def test_prorate():
    r = _deterministic("/api/v1/money/prorate", {
        "amount": "100.00", "cycle_start": "2026-11-01",
        "cycle_end": "2026-11-30", "service_start": "2026-11-10",
        "service_end": "2026-11-19"})
    b = r.json()
    assert b["prorated"] == "33.33"
    assert b["ratio"] == {"numerator": 10, "denominator": 30}
    assert b["exact_decimal"] == "33.333333333333"
    r = client.post("/api/v1/money/prorate", json={
        "amount": "100.00", "cycle_start": "2026-11-01",
        "cycle_end": "2026-11-30", "service_start": "2026-12-01",
        "service_end": "2026-12-31"})
    assert r.json()["prorated"] == "0.00"
    r = client.post("/api/v1/money/prorate", json={
        "amount": "99.00", "cycle_start": "2026-01-01",
        "cycle_end": "2026-01-31", "service_start": "2025-12-01",
        "service_end": "2026-01-10"})
    assert r.json()["prorated"] == "31.94"  # clamped to cycle


def test_split():
    r = _deterministic("/api/v1/money/split",
                       {"total": "100.00", "participants": ["a", "b", "c"]})
    b = r.json()
    assert [x["share"] for x in b["shares"]] == ["33.34", "33.33", "33.33"]
    assert b["assigned"] == "100.00" and b["unassigned"] == "0.00"
    r = client.post("/api/v1/money/split", json={
        "total": "1000", "participants": [{"name": "x", "weight": 3},
                                          {"name": "y", "weight": 1}]})
    assert [x["share"] for x in r.json()["shares"]] == ["750.00", "250.00"]
    r = client.post("/api/v1/money/split",
                    json={"total": "0.01",
                          "participants": ["a", "b", "c", "d", "e"]})
    assert [x["share"] for x in r.json()["shares"]][0] == "0.01"
    r = client.post("/api/v1/money/split",
                    json={"total": "10", "participants": []})
    assert r.status_code == 400


def test_mcp_units_money():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/call",
                                  "params": {"name": "units_convert",
                                             "arguments": {"value": 1,
                                                           "from": "m2",
                                                           "to": "sqft",
                                                           "places": 6}}})
    assert '"value": "0.107639"' in r.json()["result"]["content"][0]["text"]


# ---------------------------------------------------- lot 4.3: spell-out

def test_spell_fr_rules():
    cases = [
        ({"value": "1234.56", "lang": "fr", "currency": "EUR"},
         "mille deux cent trente-quatre euros cinquante-six centimes"),
        ({"value": "80.00", "lang": "fr", "currency": "EUR"},
         "quatre-vingts euros"),
        ({"value": "80000", "lang": "fr", "currency": "EUR"},
         "quatre-vingt mille euros"),
        ({"value": "1.00", "lang": "fr", "currency": "EUR"}, "un euro"),
        ({"value": "401", "lang": "fr", "currency": "EUR"},
         "quatre cent un euros"),
        ({"value": "-42.10", "lang": "fr", "currency": "EUR"},
         "moins quarante-deux euros dix centimes"),
        ({"value": "999999.99", "lang": "fr", "currency": "EUR",
          "capital": True},
         "Neuf cent quatre-vingt-dix-neuf mille neuf cent quatre-vingt-"
         "dix-neuf euros quatre-vingt-dix-neuf centimes"),
    ]
    for body, expected in cases:
        r = _deterministic("/api/v1/number/spell", body)
        assert r.status_code == 200, r.text
        assert r.json()["words"] == expected, (body, r.json())


def test_spell_en_pt():
    r = client.post("/api/v1/number/spell",
                    json={"value": "-42.10", "lang": "en",
                          "currency": "USD"})
    assert r.json()["words"] == "minus forty-two dollars ten cents"
    r = client.post("/api/v1/number/spell",
                    json={"value": "5.05", "lang": "pt", "currency": "BRL"})
    assert r.json()["words"] == "cinco reais cinco centavos"
    r = client.post("/api/v1/number/spell",
                    json={"value": "250", "lang": "pt", "currency": "EUR"})
    assert r.json()["words"] == "duzentos e cinquenta euros"


def test_spell_without_currency():
    r = client.post("/api/v1/number/spell", json={"value": "3.46",
                                                  "lang": "fr"})
    assert r.json()["words"] == "trois virgule quarante-six"


def test_spell_refusals():
    r = client.post("/api/v1/number/spell", json={"value": "1.2345",
                                                  "lang": "fr"})
    assert r.status_code == 400
    assert r.json()["error"] == "spell_failed"
    r = client.post("/api/v1/number/spell", json={"value": "1",
                                                  "lang": "zh"})
    assert r.status_code == 400
    r = client.post("/api/v1/number/spell", json={"value": "1", "lang": "fr",
                                                  "currency": "XYZ"})
    assert r.status_code == 400
    r = client.post("/api/v1/number/spell", json={"value": "100.50",
                                                  "lang": "fr",
                                                  "currency": "JPY"})
    assert r.status_code == 400  # yen has no sub-unit


def test_spell_mcp():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/call",
                                  "params": {"name": "number_spell",
                                             "arguments": {
                                                 "value": "1.00",
                                                 "lang": "fr",
                                                 "currency": "EUR"}}})
    assert "un euro" in r.json()["result"]["content"][0]["text"]
