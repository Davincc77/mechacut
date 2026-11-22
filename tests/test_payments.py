import base64
import json

import pytest
from fastapi.testclient import TestClient

import main
import payments

client = TestClient(main.app)

PAY_TO = "0x1234000000000000000000000000000000000006"
# /validate is a capped route: stay over 32 KB to exercise the gate
VALID_BODY = {"payload": {"a": 1, "pad": "x" * 40000}, "schema": {}}


def _header(nonce="n-1"):
    return base64.b64encode(json.dumps({
        "x402Version": 1,
        "scheme": "exact",
        "network": "base-sepolia",
        "payload": {
            "signature": "0xdeadbeef",
            "authorization": {"from": "0xpayer", "to": PAY_TO, "value": "500",
                              "validAfter": "0", "validBefore": "9999999999",
                              "nonce": nonce},
        },
    }).encode()).decode()


@pytest.fixture
def paywall(monkeypatch):
    monkeypatch.setenv("MECHACUT_PAY_TO", PAY_TO)
    monkeypatch.setenv("MECHACUT_NETWORK", "base-sepolia")
    monkeypatch.setattr(main, "RATE_LIMIT", 1)
    main.HITS.clear()
    payments._seen.clear()
    yield
    main.HITS.clear()


def test_payments_off_still_429(monkeypatch):
    monkeypatch.delenv("MECHACUT_PAY_TO", raising=False)
    monkeypatch.setattr(main, "RATE_LIMIT", 1)
    main.HITS.clear()
    assert client.post("/api/v1/validate", json=VALID_BODY).status_code == 200
    r = client.post("/api/v1/validate", json=VALID_BODY)
    assert r.status_code == 429
    assert r.json()["error"] == "rate_limited"


def test_without_payment_returns_402_from_first_call(paywall):
    r = client.post("/api/v1/validate", json=VALID_BODY)
    assert r.status_code == 402
    b = r.json()
    assert b["x402Version"] == 1
    acc = b["accepts"][0]
    assert acc["scheme"] == "exact"
    assert acc["network"] == "base-sepolia"
    assert acc["maxAmountRequired"] == "500"
    assert acc["payTo"] == PAY_TO
    assert acc["asset"] == payments.USDC["base-sepolia"]
    assert acc["resource"].endswith("/api/v1/validate")


def test_chart_price_is_one_mill(paywall):
    r = client.post("/api/v1/chart", json={"x": "a", "y": "b", "data": [{"a": 1, "b": 2}]})
    assert r.status_code == 402
    assert r.json()["accepts"][0]["maxAmountRequired"] == "1000"


def test_valid_payment_passes(paywall, monkeypatch):
    monkeypatch.setattr(payments, "verify",
                        lambda p, path, url: (True, {"valid": True}))
    monkeypatch.setattr(payments, "settle",
                        lambda p, path, url: {"success": True, "transaction": "0xabc"})
    r = client.post("/api/v1/validate", json=VALID_BODY,
                    headers={"X-PAYMENT": _header()})
    assert r.status_code == 200
    assert r.json() == {"valid": True}
    assert r.headers["x-payment-response"] == \
        json.dumps({"success": True, "transaction": "0xabc"})


def test_invalid_payment_returns_402(paywall, monkeypatch):
    monkeypatch.setattr(payments, "verify",
                        lambda p, path, url: (False, "bad signature"))
    r = client.post("/api/v1/validate", json=VALID_BODY,
                    headers={"X-PAYMENT": _header()})
    assert r.status_code == 402


def test_garbage_header_returns_402(paywall):
    r = client.post("/api/v1/validate", json=VALID_BODY,
                    headers={"X-PAYMENT": "not-a-payment"})
    assert r.status_code == 402


def test_replay_rejected(paywall, monkeypatch):
    class FakeResp:
        def __init__(self, data):
            self._d = data

        def json(self):
            return self._d

    monkeypatch.setattr(payments.httpx, "post",
                        lambda url, json=None, timeout=None:
                        FakeResp({"isValid": True, "invalidReason": None, "payer": "0xpayer"}))
    r1 = client.post("/api/v1/validate", json=VALID_BODY,
                     headers={"X-PAYMENT": _header()})
    assert r1.status_code == 200  # first use of nonce n-1
    r2 = client.post("/api/v1/validate", json=VALID_BODY,
                     headers={"X-PAYMENT": _header()})
    assert r2.status_code == 402  # same nonce replayed


def test_prices_match_published_table():
    # the exact tables are owned by tests/test_tiers.py (single source);
    # this guards the label/unit consistency of the flagship price.
    assert payments.PRICES["/api/v1/chart"] == "1000"
    assert payments.PRICE_LABELS["/api/v1/chart"] == "$0.001"
    assert set(payments.PRICES) == set(payments.PRICE_LABELS)


def test_index_lists_pricing_only_when_configured(paywall):
    r = client.get("/")
    assert r.json()["payments"]["network"] == "base-sepolia"
    assert r.json()["payments"]["prices"]["/api/v1/chart"] == "$0.001"


def test_verify_reads_facilitator_shape(monkeypatch):
    # contract with the reference x402.org facilitator: isValid/
    # invalidReason — a made-up "valid" key must never reappear
    payload = {"x402Version": 1, "scheme": "exact",
               "network": "base-sepolia",
               "payload": {"signature": "0xdead", "authorization": {
                   "from": "0xabc", "to": payments.pay_to(),
                   "value": "500", "nonce": "0x01",
                   "validAfter": "1", "validBefore": "9" * 18}}}
    monkeypatch.setattr(payments, "pay_to",
                        lambda: "0x00f04a2a505116daf3b88eae17445d85bed4fbac")
    calls = {}
    def fake(endpoint, pl, url, path):
        calls["endpoint"] = endpoint
        return {"isValid": False,
                "invalidReason": "invalid_exact_evm_insufficient_balance",
                "payer": "0xabc"}
    monkeypatch.setattr(payments, "_facilitator_call", fake)
    ok, info = payments.verify(payload, "/api/v1/reshape",
                               "https://mechacut.studio/api/v1/reshape")
    assert ok is False
    assert "insufficient_balance" in info  # real reason propagates
    def fake_ok(endpoint, pl, url, path):
        return {"isValid": True, "invalidReason": None, "payer": "0xabc"}
    monkeypatch.setattr(payments, "_facilitator_call", fake_ok)
    ok, info = payments.verify(payload, "/api/v1/reshape",
                               "https://mechacut.studio/api/v1/reshape")
    assert ok is True  # ... and a valid one is finally ACCEPTED


def test_get_on_priced_route_is_405_not_402():
    """The paywall guards POST; GET must meet the router's 405, never a
    payment challenge (learned from a real agent that believed we
    advertised GET)."""
    assert client.get("/api/v1/reshape").status_code == 405
    assert client.get("/api/v1/chart").status_code == 405
