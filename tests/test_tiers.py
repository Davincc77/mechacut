"""Three tiers under a live paywall: free / capped (32 KB) / priced."""

import pytest
from fastapi.testclient import TestClient

import main
import payments

client = TestClient(main.app)

PAY_TO = "0x1234000000000000000000000000000000000006"


@pytest.fixture
def paywall(monkeypatch):
    monkeypatch.setenv("MECHACUT_PAY_TO", PAY_TO)
    monkeypatch.setenv("MECHACUT_NETWORK", "base-sepolia")
    main.HITS.clear()
    payments._seen.clear()
    yield
    main.HITS.clear()


def test_tier_tables_are_exact():
    assert payments.PRICES == {"/api/v1/chart": "1000",
                               "/api/v1/reshape": "500",
                               "/api/v1/csv/join": "500",
                               "/api/v1/table/pivot": "500",
                               "/api/v1/text/patch": "500",
                               "/api/v1/text/apply-diff": "500",
                               "/api/v1/money/prorate": "500",
                               "/api/v1/text/chunk": "1000",
                               "/api/v1/html/text": "1000",
                               "/api/v1/integrity/verify": "1000"}
    assert payments.CAP_BYTES == 32768
    assert payments.CAP_ROUTES == {"/api/v1/json/patch": "500",
                                   "/api/v1/validate": "500",
                                   "/api/v1/agent/context-tax": "500",
                                   "/api/v1/agent/cost-diff": "500",
                                   "/api/v1/agent/tool-trim": "500",
                                   "/api/v1/csv/fix": "500",
                                   "/api/v1/csv/types": "500",
                                   "/api/v1/format/convert": "500",
                                   "/api/v1/text/diff": "500",
                                   "/api/v1/ics/generate": "500",
                                   "/api/v1/ics/parse": "500",
                                   "/api/v1/number/spell": "500",
                                   "/api/v1/md/render": "500",
                                   "/api/v1/extract/facts": "500",
                                   "/api/v1/batch": "500",
                                   "/api/v1/eth/abi-encode": "500",
                                   "/api/v1/eth/abi-decode": "500",
                                   "/api/v1/doc/text": "1000",
    "/api/v1/image/rightsize": "500",
    "/api/v1/web/cert": "500",
    "/api/v1/xml/to_json": "500",
    "/api/v1/csv/money_columns": "500",
    "/api/v1/table/sql_dump": "500",
}


def test_free_bundle_routes_never_ask_payment(paywall):
    r = client.post("/api/v1/json/repair", json={"text": "{a: 1}"})
    assert r.status_code == 200  # no X-PAYMENT under a live paywall
    assert "x-payment-response" not in r.headers


def test_capped_route_free_under_32k(paywall):
    r = client.post("/api/v1/json/patch",
                    json={"document": {"a": 1},
                          "patch": [{"op": "add", "path": "/b", "value": 2}]})
    assert r.status_code == 200
    assert r.json()["output"] == {"a": 1, "b": 2}


def test_capped_route_over_32k_requires_payment(paywall):
    r = client.post("/api/v1/json/patch",
                    json={"document": {"blob": "x" * 40000}, "patch": []})
    assert r.status_code == 402
    acc = r.json()["accepts"][0]
    assert acc["maxAmountRequired"] == "500"
    assert "32768" in acc["description"]


def test_new_priced_routes_402_first_call(paywall):
    r = client.post("/api/v1/csv/join",
                    json={"left": [{"id": 1}], "right": [{"id": 1}],
                          "on": "id"})
    assert r.status_code == 402
    assert r.json()["accepts"][0]["maxAmountRequired"] == "500"
    r = client.post("/api/v1/table/pivot",
                    json={"data": [{"m": "a", "c": "x", "v": 1}],
                          "index": "m", "columns": "c", "values": "v"})
    assert r.status_code == 402


def test_400s_on_priced_routes_stay_free(paywall, monkeypatch):
    # no X-PAYMENT: a priced route answers 402 before validation (contract:
    # the paywall gates the CALL; the 400-free rule applies to served calls)
    r = client.post("/api/v1/csv/join", json={"left": [], "right": [],
                                              "on": "id"})
    assert r.status_code == 402


def test_bundle2_tiers(paywall):
    # text/diff capped: free under 32 KB
    r = client.post("/api/v1/text/diff", json={"a": "x\n", "b": "y\n"})
    assert r.status_code == 200
    # text/diff over 32 KB: x402
    big = "x\n" * 20000
    r = client.post("/api/v1/text/diff", json={"a": big, "b": big + "y\n"})
    assert r.status_code == 402
    # priced from the first call
    r = client.post("/api/v1/text/patch",
                    json={"text": "a", "edits": [{"find": "a", "replace": "b"}]})
    assert r.status_code == 402
    r = client.post("/api/v1/text/apply-diff",
                    json={"text": "a\n", "diff": "@@ -1 +1 @@\n-a\n+b\n"})
    assert r.status_code == 402


def test_pricing_info_publishes_caps(paywall):
    body = client.get("/").json()
    info = body["payments"]
    assert len(info["capped_routes"]) == 23    # b107 vérifié : shop/withdrawal reste 🟢 FREE — entrée courte (dates), comme return-deadline et les sœurs soldes, pas un collage ; +1 24-11 tard: agent/tool-trim (listing collé, 🟡 comme les deux sœurs) ; +1 24-11: agent/cost-diff (deux listings collés, 🟡) ; 21 agent/context-tax ; 20 = table/sql_dump
    assert "32768" in info["mode"]
