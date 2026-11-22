"""Public misses ledger: recording, anonymization, windowing."""

import time

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _clear():
    with main._misses_lock:
        main._misses.clear()


def _force_400():
    """A guaranteed 400 on a transform route (schema mismatch)."""
    r = client.post("/api/v1/validate",
                    json={"payload": {"age": 44}, "schema": {"type": "string"}})
    assert r.status_code == 400
    return r


def test_400s_are_recorded():
    _clear()
    _force_400()
    m = client.get("/misses.json").json()
    assert m["total"] >= 1
    assert m["by_route"].get("/api/v1/validate", 0) >= 1
    assert m["by_kind"], "au moins une erreur étiquetée"
    assert m["recent"][0]["route"] == "/api/v1/validate"
    assert m["window_minutes"] == main._MISS_WINDOW // 60


def test_misses_are_anonymized():
    _clear()
    client.post("/api/v1/reshape",
                json={"input": {"SECRET_XYZ_MARKER": "keep-me-out"},
                      "mapping": {"fields": {}}})
    body = client.get("/misses.json").text
    assert "SECRET_XYZ_MARKER" not in body
    assert "keep-me-out" not in body


def test_successes_are_not_misses():
    _clear()
    r = client.post("/api/v1/validate", json={"payload": {"a": 1}, "schema": {}})
    assert r.status_code == 200
    assert client.get("/misses.json").json()["total"] == 0


def test_old_misses_are_pruned():
    _clear()
    with main._misses_lock:
        main._misses.append((int(time.time()) - main._MISS_WINDOW - 10,
                             "/api/v1/chart", "stale"))
        main._misses.append((int(time.time()), "/api/v1/chart", "fresh"))
    m = client.get("/misses.json").json()
    assert m["total"] == 1
    assert m["recent"][0]["kind"] == "fresh"


def test_402_refusals_are_recorded(monkeypatch):
    _clear()
    monkeypatch.setenv("MECHACUT_PAY_TO", "0x1234000000000000000000000000000000000006")
    monkeypatch.setenv("MECHACUT_NETWORK", "base-sepolia")
    # /validate is capped: a >32 KB body must settle before answering
    r = client.post("/api/v1/validate",
                    json={"payload": {"a": 1, "pad": "x" * 40000},
                          "schema": {}})
    assert r.status_code == 402
    m = client.get("/misses.json").json()
    assert m["refusals"] >= 1
    assert m["by_kind"].get("payment_required", 0) >= 1
    assert m["by_route"].get("/api/v1/validate", 0) >= 1


def test_429_is_not_a_miss():
    _clear()
    old = main.RATE_LIMIT
    main.RATE_LIMIT = 0  # tout est refusé côté rate-limit, mais payments off
    try:
        assert client.post("/api/v1/validate",
                           json={"payload": {"a": 1}, "schema": {}}).status_code == 429
    finally:
        main.RATE_LIMIT = old
        main.HITS.clear()
    m = client.get("/misses.json").json()
    assert m["total"] == 0


def test_misses_present_in_index_card():
    d = client.get("/").json()
    assert "/misses.json" in d["endpoints"]
