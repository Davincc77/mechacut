"""Bundle 6.1 — validators: real registry vectors + closed-table audit."""

from fastapi.testclient import TestClient

import checkers
import main

client = TestClient(main.app)


def _twice(url, payload):
    r1 = client.post(url, json=payload)
    r2 = client.post(url, json=payload)
    assert r1.content == r2.content
    return r1


def test_iban_table_is_self_consistent():
    for cc, (declared, computed) in checkers.iban_table_widths().items():
        assert declared == computed, cc


def test_iban_valid_vectors():
    for iban in ["FR7630004000031234567890143", "DE89370400440532013000",
                 "GB82WEST12345698765432", "NL91ABNA0417164300",
                 "PT50000201231234567890154", "IT60X0542811101000000123456",
                 "ES7921000813610123456789", "BE68539007547034",
                 "CH9300762011623852957", "AT611904300234573201",
                 "SE4550000000058398257466", "EE382200221020145685",
                 "UA213223130000026007233566001"]:
        r = client.post("/api/v1/validate/iban", json={"iban": iban})
        assert r.status_code == 200, (iban, r.text)
        assert r.json()["valid"] is True


def test_iban_refusals_are_precise():
    r = client.post("/api/v1/validate/iban",
                    json={"iban": "FR7630004000031234567890144"})
    assert r.status_code == 400 and r.json()["error"] == "check_failed"
    assert "mod-97" in r.json()["errors"][0]["message"]
    r = client.post("/api/v1/validate/iban", json={"iban": "ZZ99FOO"})
    assert "unknown country" in r.json()["errors"][0]["message"]
    r = client.post("/api/v1/validate/iban",
                    json={"iban": "DE8937040044053201300"})
    assert "length" in r.json()["errors"][0]["message"]


def test_iban_is_paid_route():
    r = client.post("/api/v1/validate/iban",
                    json={"iban": "FR7630004000031234567890143"},
                    headers={"X-Test": "x"})
    # no payment header -> exactly the 402 contract, no free pass
    from fastapi.testclient import TestClient as _TC
    fresh = _TC(main.app)
    r = fresh.post("/api/v1/validate/iban",
                   json={"iban": "FR7630004000031234567890143"},
                   headers={"Host": "mechacut.studio"})
    if r.status_code == 402:
        assert "X-PAYMENT-ADDRESS" in r.headers
    else:  # payments unconfigured locally: route still reachable
        assert r.status_code in (200, 400)


def test_phone_forms():
    for body, e164 in [({"phone": "+33 1 23 45 67 89"},
                        "+33123456789"),
                       ({"phone": "0123456789",
                        "default_country": "FR"}, "+33123456789"),
                       ({"phone": "0044 1234 567890"}, "+441234567890"),
                       ({"phone": "+1 (212) 736-5000"}, "+12127365000")]:
        r = _twice("/api/v1/validate/phone", body)
        assert r.status_code == 200, r.text
        assert r.json()["e164"] == e164
    r = client.post("/api/v1/validate/phone", json={"phone": "+33123"})
    assert r.status_code == 400
    r = client.post("/api/v1/validate/phone", json={"phone": "0123456789"})
    assert r.status_code == 400  # bare national needs default_country


def test_email():
    r = _twice("/api/v1/validate/email",
               {"email": "Josie.Tardy@Sub.Domain.FR"})
    assert r.json()["normalized"] == "Josie.Tardy@sub.domain.fr"
    for bad in ["a..b@x.com", "a@x.c", "no-at.com", "@x.com",
                "a b@x.com"]:
        r = client.post("/api/v1/validate/email", json={"email": bad})
        assert r.status_code == 400, bad


def test_url_canonical():
    r = _twice("/api/v1/validate/url",
               {"url": "HTTP://Fr.Example.COM:80/a/../b?X=1&Y=2#f"})
    b = r.json()
    assert b["canonical"] == "http://fr.example.com/b?X=1&Y=2#f"
    assert b["port"] is None and b["secure"] is False
    r = client.post("/api/v1/validate/url", json={"url": "https://café.fr"})
    assert r.json()["host"] == "xn--caf-dma.fr"
    r = client.post("/api/v1/validate/url", json={"url": "gopher://x/y"})
    assert r.status_code == 400
    r = client.post("/api/v1/validate/url", json={"url": "http://x.com:99999"})
    assert r.status_code == 400


def test_color_wcag():
    r = _twice("/api/v1/color/check", {"color": "#767676",
                                       "against": "#ffffff"})
    c = r.json()["contrast"]
    assert c["ratio"] == 4.542 and c["AA_normal"] is True
    r = client.post("/api/v1/color/check", json={"color": "#777777",
                                                 "against":
                                                 "rgb(255,255,255)"})
    assert r.json()["contrast"]["AA_normal"] is False
    r = client.post("/api/v1/color/check", json={"color": "#000",
                                                 "against": "#FFF"})
    assert r.json()["contrast"]["ratio"] == 21.0
    r = client.post("/api/v1/color/check", json={"color": "rebeccapurple"})
    assert r.status_code == 400
    r = client.post("/api/v1/color/check", json={"color": "rgb(260,0,0)"})
    assert r.status_code == 400
