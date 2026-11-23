# -*- coding: utf-8 -*-
"""Bundle 82 — loop/doom-check : la répétition aveugle mesurée.

Douleur documentée par le marché (ZCode v2 model-anomaly-fallbacks :
« mêmes outils, mêmes input en boucle = signal doom loop ») ET mesurée
chez nous (V22b 0/14, V17 retry non convergent). Golds tracés à la
main avant l'impl — mêmes cas que la validation du module :
  [R,R,R]         -> DOOM positions [0,1,2]
  [R,R]           -> HEALTHY (deux n'est pas une boucle ; seuil nommé)
  [A,B]x3         -> CYCLIC période 2, repeats 3
  x dispersé ×4   -> STORM [0,2,4,6]
  {"a":1,"b":2} vs {"b":2,"a":1} -> MÊME appel (canon) -> DOOM
  2 distincts/6   -> ratio "0.3333"
"""
import main
import pytest
from fastapi.testclient import TestClient

client = TestClient(main.app)


def _c(**kw):
    r = client.post("/api/v1/loop/doom-check", json=kw)
    return r.status_code, r.json()


def _calls(*specs):
    return [{"tool": t, "args": a} for t, a in specs]


def test_doom_three_consecutive():
    s, b = _c(calls=_calls(("bash", {"c": "ls"}), ("bash", {"c": "ls"}),
                            ("bash", {"c": "ls"})))
    assert s == 200 and b["verdict"] == "DOOM"
    assert b["signals"][0]["positions"] == [0, 1, 2]
    assert b["signals"][0]["count"] == 3


def test_two_is_not_a_loop():
    s, b = _c(calls=_calls(("bash", {"c": "ls"}), ("bash", {"c": "ls"})))
    assert b["verdict"] == "HEALTHY"
    assert b["signals"] == []


def test_cyclic_period_two():
    seq = _calls(("a", {}), ("b", {})) * 3
    s, b = _c(calls=seq)
    assert b["verdict"] == "CYCLIC"
    sig = [x for x in b["signals"] if x["kind"] == "cyclic"][0]
    assert sig["period"] == 2 and sig["repeats"] == 3


def test_storm_scattered():
    seq = _calls(("x", {"v": 1}), ("y", {}), ("x", {"v": 1}), ("z", {}),
                 ("x", {"v": 1}), ("w", {}), ("x", {"v": 1}))
    s, b = _c(calls=seq)
    assert b["verdict"] == "STORM"
    st = [x for x in b["signals"] if x["kind"] == "storm"][0]
    assert st["positions"] == [0, 2, 4, 6] and st["count"] == 4


def test_canonical_identity_key_order():
    s, b = _c(calls=[{"tool": "t", "args": {"a": 1, "b": 2}},
                     {"tool": "t", "args": {"b": 2, "a": 1}},
                     {"tool": "t", "args": {"a": 1, "b": 2}}])
    assert b["verdict"] == "DOOM"


def test_single_denominator_ratio():
    s, b = _c(calls=_calls(("a", {}), ("b", {})) * 3)
    assert b["distinct_ratio"] == "0.3333"
    assert b["total_calls"] == 6 and b["distinct_calls"] == 2


def test_thresholds_echoed_and_named_refusals():
    s, b = _c(calls=_calls(("x", {})), )
    assert s == 200 and b["thresholds"] == {"doom_min": 3,
                                            "cycles_min": 2,
                                            "storm_min": 4}
    s, b = _c(calls=[])
    assert s == 400 and "empty" in str(b)
    s, b = _c(calls=[{"args": {}}])
    assert s == 400 and "calls.0.tool" in str(b)  # le nom exact du champ — mieux que mon aiguillon
    s, b = _c(calls=_calls(("x", {})), doom_min=1)
    assert s == 400 and "2-50" in str(b)
    s, b = _c(calls=_calls(("x", {})) * 201)
    assert s == 400 and "/batch" in str(b)


def test_determinism_and_wiring():
    payload = {"calls": _calls(("a", {}), ("a", {}), ("a", {}))}
    _, x = _c(**payload)
    _, y = _c(**payload)
    assert x["sha256"] == y["sha256"]
    names = [t["name"] for t in main.MCP_TOOLS]
    assert "loop_doom_check" in names
    src = open("Dockerfile").read()
    assert "loopkit.py" in src
