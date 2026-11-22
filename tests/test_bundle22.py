"""Bundle 22 — VERDICT. Porte de sortie n°1 : /check/agreement."""
import sys
sys.path.insert(0, ".")
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def agree(payloads):
    r = client.post("/api/v1/check/agreement", json={"payloads": payloads})
    assert r.status_code == 200, r.text
    return r.json()


def test_identical_agree():
    d = agree([{"a": 1, "b": "x"}, {"b": "x", "a": 1}])
    assert d["agree"] is True and d["divergences"] == []


def test_numeric_string_tolerance():
    d = agree([{"total": "1255.00"}, {"total": 1255}])
    assert d["agree"] is True


def test_real_divergence_pointer_and_kind():
    d = agree([{"deal": {"usd": 100, "qty": 3}},
               {"deal": {"usd": 105, "qty": 3}}])
    assert d["agree"] is False
    div = d["divergences"][0]
    assert div["pointer"] == "/deal/usd" and div["kind"] == "numeric"
    assert d["first_divergence"] == "/deal/usd"


def test_presence_is_a_divergence():
    d = agree([{"x": 1, "y": 2}, {"x": 1}])
    assert d["agree"] is False
    assert d["divergences"][0]["pointer"] == "/y"
    assert d["divergences"][0]["kind"] == "presence"


def test_same_members_other_order_is_order_kind():
    d = agree([{"items": ["a", "b"]}, {"items": ["b", "a"]}])
    assert d["agree"] is False
    assert d["divergences"][0]["kind"] == "order"


def test_min_two_payloads_free_400():
    r = client.post("/api/v1/check/agreement", json={"payloads": [{"a": 1}]})
    assert r.status_code == 400
    assert "at least 2" in r.json()["errors"][0]["message"]


def test_deterministic_sha():
    a = agree([{"p": 1}, {"p": 2}])
    b = agree([{"p": 1}, {"p": 2}])
    assert a["sha256"] == b["sha256"]


def rl(text, rules):
    r = client.post("/api/v1/check/redlines",
                    json={"text": text, "rules": rules})
    assert r.status_code == 200, r.text
    return r.json()


def test_redline_pii_shape_caught():
    d = rl("Your card ends here, ref 4111 1111 1111 1111 thanks",
           {"forbid_shapes": ["card"]})
    assert d["clean"] is False
    assert d["first_violation"]["rule"] == "forbid_shapes:card"
    assert d["first_violation"]["at"] == 25


def test_redline_word_case_insensitive_word_boundary():
    d = rl("The PRICE is confidential", {"forbid_words": ["price"]})
    assert d["clean"] is False
    # 'pricetag' must NOT trip the word rule
    d2 = rl("a pricetag sticker", {"forbid_words": ["price"]})
    assert d2["clean"] is True


def test_redline_budget():
    d = rl("x" * 300, {"max_bytes": 280})
    assert d["clean"] is False and d["first_violation"]["kind"] == "budget"


def test_redline_email_shape_and_clean_pass():
    d = rl("contact jane@example.com", {"forbid_shapes": ["email"]})
    assert d["clean"] is False
    d2 = rl("all clear, nothing sensitive here",
            {"forbid_words": ["secret"], "forbid_shapes": ["email"]})
    assert d2["clean"] is True and d2["violations"] == 0


def test_redline_unknown_shape_400():
    r = client.post("/api/v1/check/redlines",
                    json={"text": "x", "rules": {"forbid_shapes": ["passport"]}})
    assert r.status_code == 400
    assert "card" in r.json()["errors"][0]["message"]


def test_redline_empty_rules_400():
    r = client.post("/api/v1/check/redlines",
                    json={"text": "x", "rules": {}})
    assert r.status_code == 400


def test_integrity_checklist_replays():
    import json, hashlib
    d = client.get("/integrity.json").json()
    assert len(d["pins"]) >= 78
    for pin in d["pins"]:
        assert {"name", "path", "status", "sha256"} <= set(pin)
        # POST : body ; GET : query + méthode explicites
        assert "body" in pin or (pin.get("method") == "GET"
                                 and "query" in pin)
    # replay 5 pins varies par tirage clos (5ᵉ, 25ᵉ, 50ᵉ, 70ᵉ, dernier)
    picks = [d["pins"][i] for i in (4, 24, 49, 69, -1)]
    picks.append(next(p for p in d["pins"] if p.get("method") == "GET"))
    for pin in picks:
        if pin.get("method") == "GET":
            r = client.get(pin["path"], params=pin["query"])
        else:
            r = client.post(pin["path"], json=pin["body"])
        assert r.status_code == pin["status"], pin["name"]
        got = hashlib.sha256(json.dumps(
            r.json(), sort_keys=True, separators=(",", ":"),
            ensure_ascii=False).encode()).hexdigest()
        assert got == pin["sha256"], pin["name"]


def test_agent_listing_generated_and_stable():
    r1 = client.get("/agent/listing.txt")
    r2 = client.get("/agent/listing.txt")
    assert r1.status_code == 200
    assert r1.headers["X-Listing-SHA"] == r2.headers["X-Listing-SHA"]
    t = r1.text
    assert "$0.0005" in t          # le floor réel, pas celui de Wade
    assert "transforms" in t and "recipes" in t
    assert "/integrity.json" in t and "/agent/manifest" in t
    assert "free  : " in t


def test_cache_miss_then_hit_same_bytes():
    import cache as _c
    _c.clear()
    body = {"text": "cache ritual 42 test", "group": "kind"}
    r1 = client.post("/api/v1/extract/facts", json=body)
    r2 = client.post("/api/v1/extract/facts", json=body)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.headers["x-cache"] == "MISS"
    assert r2.headers["x-cache"] == "HIT"
    assert r1.content == r2.content        # octets EXACTS, pas « similaires »
    _c.clear()


def test_cache_does_not_store_errors():
    import cache as _c
    _c.clear()
    client.post("/api/v1/check/agreement", json={"payloads": [{"a": 1}]})
    assert _c.stats()["entries"] == 0
    _c.clear()


def test_cache_bounded():
    import cache as _c
    _c.clear()
    for i in range(300):
        client.post("/api/v1/num/round",
                    json={"value": str(i), "places": 2})
    assert _c.stats()["entries"] <= _c.stats()["cap"]
    _c.clear()
