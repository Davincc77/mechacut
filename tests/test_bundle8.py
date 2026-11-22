"""Bundle 8 — color/palette: closed harmonies, exact rotations, stable ramps."""

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)

P = "/api/v1/color/palette"


def _twice(payload):
    r1 = client.post(P, json=payload)
    r2 = client.post(P, json=payload)
    assert r1.content == r2.content  # same seed -> same bytes, forever
    return r1


def test_palette_exact_rotations():
    r = _twice({"color": "#ff0000", "scheme": "complementary"})
    assert r.status_code == 200
    assert r.json()["swatches"] == ["#ff0000", "#00ffff"]
    r = _twice({"color": "#ff0000", "scheme": "triad"})
    assert r.json()["swatches"] == ["#ff0000", "#00ff00", "#0000ff"]
    r = _twice({"color": "#6d28d9", "scheme": "triad"})
    assert r.json()["swatches"] == ["#6d28d9", "#d96d28", "#28d96d"]
    r = _twice({"color": "#3a7bd5", "scheme": "analogous"})
    assert r.json()["swatches"] == ["#3ac8d5", "#3a7bd5", "#463ad5"]
    r = _twice({"color": "#3a7bd5", "scheme": "split"})
    assert r.json()["swatches"][0] == "#3a7bd5"  # base is always first
    r = _twice({"color": "#767676", "scheme": "complementary"})
    assert r.json()["swatches"] == ["#767676", "#767676"]  # gray stays gray


def test_palette_ramps():
    r = _twice({"color": "#6d28d9", "steps": 5, "neutral": True})
    b = r.json()
    assert b["shades"] == ["#0b0416", "#3b1577", "#6c26d9", "#ae88ea",
                           "#f0e9fb"]
    assert len(b["neutral_ramp"]) == 5
    hexes = [int(x[1:], 16) for x in b["neutral_ramp"]]
    assert hexes == sorted(hexes)  # even lightness, monotone
    assert "sha256" in b


def test_palette_refusals():
    for body in ({"color": "#6d28d9", "steps": 0},
                 {"color": "#6d28d9", "steps": 22},
                 {"color": "#nope"},
                 {"color": "#6d28d9", "scheme": "golden-ratio"}):
        r = client.post(P, json=body)
        assert r.status_code == 400, body
    r = client.post(P, json={"color": "#6d28d9", "steps": 0})
    assert r.json()["error"] == "check_failed"


def test_dark_color_hsl_sane():
    # the palette work exposed a broken HSL conversion for dark colors
    # (scale mismatch could yield nonsense saturation) — regression guard.
    r = client.post("/api/v1/color/check", json={"color": "#0b0416"})
    assert r.status_code == 200
    h, sl, l = r.json()["hsl"]
    assert 0 <= sl <= 100 and 0 <= l <= 100
    r = client.post("/api/v1/color/check", json={"color": "#6d28d9"})
    assert r.json()["hsl"] == [263.39, 69.96, 50.39]


def test_palette_mcp():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/call",
                                  "params": {"name": "color_palette",
                                             "arguments": {
                                                 "color": "#6d28d9",
                                                 "scheme": "triad"}}})
    assert "#d96d28" in r.json()["result"]["content"][0]["text"]
