# -*- coding: utf-8 -*-
"""Bundle 76 — eval/compare : le juge du banc érigé en route.

Golds tracés à la main AVANT l'impl (doctrine ADJACENCES décision 1) :
  G1  {"a":1,"b":"2.50","c":[1,2]} vs {"c":[1,2],"a":1,"b":2.5}
      -> OK, matched 4 : ordre des clés irrelevant, "2.50" est la
      MÊME quantité que 2.5 (incident juge v2 « 3829/10 »).
  G2  /vat/pct 20 vs "20.5" -> WRONG, 1 divergence kind value.
  G3  [1,2,3] vs [1,2]      -> /2 only_expected (jamais de silence).
  G4  {"x":1} vs {"x":1,"y":2} -> /y only_got.
  G5  identiques sauf sha256, ignore_paths ["$.sha256"] -> OK.
  G6  "3/4" vs 0.75 -> OK (la fraction est une représentation
      légitime du décimal, pas un type différent).
  G7  strict_types: "1.50" vs 1.5 -> WRONG kind type — la FORME est
      alors partie de la réponse.
  G8  scalaires racine 5 vs "5" -> OK.
Refus nommés : JSON string non parsable (ligne+colonne), pointeur
hors grammaire $.a.b[0].
"""
from fastapi.testclient import TestClient

import main
import routing

client = TestClient(main.app)


def _p(**kw):
    r = client.post("/api/v1/eval/compare", json=kw)
    return r.status_code, r.json()


def test_g1_ok_ordre_et_representation():
    s, b = _p(expected={"a": 1, "b": "2.50", "c": [1, 2]},
              got={"c": [1, 2], "a": 1, "b": 2.5})
    assert s == 200 and b["verdict"] == "OK"
    assert b["counts"]["matched"] == 4
    assert b["divergences"] == []


def test_g2_value_divergence():
    s, b = _p(expected={"total": "81.90", "vat": {"pct": 20}},
              got={"total": "81.90", "vat": {"pct": "20.5"}})
    assert b["verdict"] == "WRONG"
    assert len(b["divergences"]) == 1
    d = b["divergences"][0]
    assert d["pointer"] == "/vat/pct" and d["kind"] == "value"
    assert d["expected"] == 20 and d["got"] == "20.5"


def test_g3_missing_row_is_named_not_silent():
    s, b = _p(expected=[1, 2, 3], got=[1, 2])
    assert b["verdict"] == "WRONG"
    assert b["divergences"][0] == {"pointer": "/2",
                                   "kind": "only_expected",
                                   "expected": 3, "got": None}


def test_g4_extra_row():
    s, b = _p(expected={"x": 1}, got={"x": 1, "y": 2})
    assert b["divergences"][0]["kind"] == "only_got"
    assert b["divergences"][0]["pointer"] == "/y"


def test_g5_ignore_paths_sha():
    e = {"v": "1.0", "sha256": "aaaa"}
    g = {"v": "1.0", "sha256": "bbbb"}
    s, b = _p(expected=e, got=g, ignore_paths=["$.sha256"])
    assert b["verdict"] == "OK"
    assert b["ignore_paths_applied"] == ["/sha256"]
    # sans ignore, c'est un désaccord réel : le juge ne devine pas
    s, b = _p(expected=e, got=g)
    assert b["verdict"] == "WRONG"


def test_g6_fraction_equivalence():
    s, b = _p(expected={"n": "3/4"}, got={"n": 0.75})
    assert b["verdict"] == "OK"


def test_g7_strict_types_form_counts():
    s, b = _p(expected={"n": "1.50"}, got={"n": 1.5},
              strict_types=True)
    assert b["verdict"] == "WRONG"
    assert b["divergences"][0]["kind"] == "type"


def test_g8_scalar_roots():
    s, b = _p(expected=5, got="5")
    assert s == 200 and b["verdict"] == "OK"


def test_refusals_named():
    s, b = _p(expected={"a": 1}, got="oops{")
    assert s == 400
    msg = " ".join(e["message"] for e in b["errors"])
    assert "not valid JSON at line" in msg
    s, b = _p(expected={"a": 1}, got={"a": 1}, ignore_paths=["$.["])
    assert s == 400
    msg = " ".join(e["message"] for e in b["errors"])
    assert "ignore_paths must look like" in msg


def test_report_sha_stable():
    _, a = _p(expected={"a": 1}, got={"a": "1.00"})
    _, b = _p(expected={"a": 1}, got={"a": "1.00"})
    assert a["sha256"] == b["sha256"] and a["verdict"] == "OK"


def test_wired_everywhere():
    names = [t["name"] for t in main.MCP_TOOLS]
    assert "eval_compare" in names
    assert "/api/v1/eval/compare" in [t[1] for t in routing.TABLE]
    src = open("Dockerfile").read()
    assert "evalkit.py" in src  # leçon unitpricekit : COPY ou 502
