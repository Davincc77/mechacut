"""Bundle 19 — chart readability guard (2026-11-21, born from the Bankr
BANKR-hourly chart whose 25 x-labels collided). The fix is server-side and
versioned: same request -> same bytes, but those bytes are now readable."""
import sys
sys.path.insert(0, ".")
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def _hourly(n=25, price=0.0002):
    return {"kind": "line", "x": "hour", "y": "priceusd",
            "title": "t", "data": [
                {"hour": "%02d:00" % (i % 24), "priceusd": price + i * 1e-7}
                for i in range(n)]}


def test_dense_line_gets_vega_labelangle():
    r = client.post("/api/v1/chart", json=_hourly())
    assert r.status_code == 200
    d = r.json()
    assert d["vega"]["encoding"]["x"]["axis"]["labelAngle"] == -45


def test_sparse_line_untouched():
    r = client.post("/api/v1/chart", json=_hourly(6))
    assert r.status_code == 200
    assert "axis" not in r.json()["vega"]["encoding"]["x"]


def test_dense_bar_also_guarded():
    body = {"kind": "bar", "x": "h", "y": "v", "data": [
        {"h": "h%02d" % i, "v": i} for i in range(24)]}
    r = client.post("/api/v1/chart", json=body)
    assert r.status_code == 200
    assert r.json()["vega"]["encoding"]["x"]["axis"]["labelAngle"] == -45


def test_readability_is_still_deterministic():
    a = client.post("/api/v1/chart", json=_hourly()).json()
    b = client.post("/api/v1/chart", json=_hourly()).json()
    assert a["sha256"] == b["sha256"] and a["sha256_png"] == b["sha256_png"]


def test_tiny_magnitudes_render_scientific_without_error():
    # the guard path for 0.0002-style axes must not raise and must stay stable
    r = client.post("/api/v1/chart", json=_hourly(10))
    assert r.status_code == 200 and r.json()["png_bytes"] > 0
