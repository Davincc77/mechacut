# -*- coding: utf-8 -*-
"""bundle58 — /ship/dimweight + /json/coerce.

ORACLES (calculs MAIN, jamais la sortie du module recopiée) :

dimweight — chaîne publiée (calculatorcollection : chaque dimension au
pouce supérieur AVANT volume, DIM = volume ÷ diviseur, puis livres AU
PALIER supérieur) :
  12x8x6 in : vol 576 in3 ; 576/139 : 139x4=556 reste 20 ;
  20/139 = 0.14388489208633... -> 4.1438848921 (11e chiffre 8, on monte).
  max(2, 4.14...) = 4.14... ; ceil au palier 1 -> 5 lb (leur exemple
  publié, rejoué).
  20x20x12 : vol 4800 ; 4800/139 : 139x34=4726 reste 74 ;
  74/139 = 0.53237410071... -> 34.5323741007 (11e chiffre 1, on reste).
  step 1 -> 35 (rollo publié) ; step none -> 34.5323741007 (amzprep
  publie 34,5 — TRONCATURE de la fraction exacte, rendue comme telle).
  mm 305x203x152 avec diviseur 139 in3_lb : conversion par le facteur
  DEFINI 1 in = 25.4 mm — 305/25.4 = 1525/127 = 12.0078740157 (11e 4),
  203/25.4 = 1015/127 = 7.9921259843 (11e 5 suivi de 196..., on monte),
  152/25.4 = 760/127 = 5.9842519685 (11e 0) ; ceil -> 13x8x6 = 624 ;
  624/139 = 4.4892086331 (11e 9) ; 624 < 1728 -> gate USPS : DIM ne
  s'applique PAS, facturé = actual 2 lb. SANS ceil : volume
  9 411 080 mm3 = 1 176 385 000/2 048 383 in3 ; DIM =
  1176385000/284725237 = 4.13161... -> ceil palier -> 5.
  cm 40x30x25 : 30 000 cm3 ; ÷5000 = 6 PILE (6/1) ; ÷6000 = 5 PILE ;
  plafond 70 : facturé 35 avec cap 30 -> 30, capped.
  actual 2.4 lb seul -> ceil palier 1 = 3 (règle du palier, pas des
  arrondis bancaires).
  Le piege publie « mm avec diviseur imperial = x16,4 » est rendu
  IMPOSSIBLE : le diviseur porte son unite, la conversion est etape
  nommee.

json/coerce — grammaire du fix publie magpie c272e55 (creee par
#3152 : « whole numbers with zero fractional digits become integer
spellings (8.0 -> 8, 2500.0 -> 2500) ; actual fractions, exponent
notation, strings and keys stay as written ») + PraisonAI #6369
(« 2 »+« 3 » -> « 23 », force="false" truthy). Vecteurs : 8.0 -> 8 ;
2500.0/17277.0 -> entiers u64 ; 2.5 en creneau entier -> refus
FRACTIONAL (JAMAIS de troncature silencieuse) ; 1.0e3 -> laisse TEL
QUEL et re-emit « 1.0e3 » (la notation est la donnee — json.loads
standard la perd, ce module la capture par parse_float) ; "false" ->
refus BOOL_TRUTHY nomme ; "007" -> refus LEADING_ZERO MEME avec cast
(actif = phone/CNPJ/SIREN, la lecon csv/excel_damage) ; chaine
numerique -> cast UNIQUEMENT avec cast_strings=on ; 2^63 en i64 ->
refus BOUND bornes nommees ; cles dupliquees -> refus ; nested object
-> laisse + nomme. 9223372036854775808 > 2^63-1 (oracle Python natif,
puissance de 2, pas memoire).

La re-emission : le test verifie que le texte SORTI porte la notation
d'entree pour ce qui est laisse (1.0e3) et la notation entiere pour ce
qui est coerce (8) — ce que traverse le bug #3152 (relais qui perd la
forme ecrite), ici capture par tokens litteraux.
"""
import json

import pytest
from fastapi.testclient import TestClient

import castkit
import dimkit
import main as m
import routing

client = TestClient(m.app)


# ---------------- dimweight : module pur, attentes MAIN ---------------

def _dim(l, w, h, unit, av, au, rules, as_of=None):
    a = {"dims": {"l": l, "w": w, "h": h, "unit": unit},
         "actual_weight": {"value": av, "unit": au},
         "rules": rules}
    if as_of is not None:
        a["as_of"] = as_of
    return dimkit.run_dimweight(a)

R139 = {"name": "r139", "divisor": "139", "divisor_unit": "in3_lb",
        "dim_round": "ceil", "weight_step": "1"}


def test_calculatorcollection_5lb():
    out = _dim("12", "8", "6", "in", "2", "lb", [R139])
    r = out["results"][0]
    # 576/139 = 4.14388489208633... palier 1 -> 5
    assert r["billed_weight"] == "5"
    assert r["billed_fraction"] == "5/1"
    assert r["governs"] == "dimensional"
    vol = [s for s in r["steps"] if s["step"] == "volume"][0]
    assert vol["value"] == "576" and vol["fraction"] == "576/1"
    dimw = [s for s in r["steps"]
            if s["step"] == "dimensional weight"][0]
    assert dimw["value"] == "4.1438848921"
    assert dimw["fraction"] == "576/139"


def test_rollo_vs_amzprep_diverge_on_same_inches():
    r2 = dict(R139)
    r2["name"] = "amzprep"
    r2["weight_step"] = "none"
    out = _dim("20", "20", "12", "in", "2", "lb", [R139, r2],
               as_of="2026-07-12")
    a, b = out["results"]
    assert a["billed_weight"] == "35"          # rollo publie
    assert b["billed_fraction"] == "4800/139"  # leur 34,5 = troncature
    assert b["billed_weight"] == "34.5323741007"
    assert "DISAGREE" in out["verdict"]
    assert out["as_of"] == "2026-07-12"


def test_mm_gate_below_one_cubic_foot():
    out = _dim("305", "203", "152", "mm", "2", "lb",
               [dict(R139, name="usps", min_volume="1728")])
    r = out["results"][0]
    # dims converties (305/25.4 = 12.0078740157...) puis ceil 13x8x6=624
    dims = [s for s in r["steps"] if s["step"].startswith("dimension ")]
    assert [d["exact"] for d in dims] == ["12.0078740157",
                                          "7.9921259843",
                                          "5.9842519685"]
    assert [d["rounded_up_to"] for d in dims] == ["13", "8", "6"]
    assert r["dim_applies"] is False  # 624 < 1728 : gate USPS strict
    assert r["billed_weight"] == "2"
    assert r["governs"] == "actual"
    assert r["gate_note"] and "out of contract" in r["gate_note"]


def test_mm_without_ceil_exact_fraction():
    out = _dim("305", "203", "152", "mm", "2", "lb",
               [dict(R139, dim_round="none")])
    r = out["results"][0]
    dimw = [s for s in r["steps"]
            if s["step"] == "dimensional weight"][0]
    # 9 411 080 mm3 / 16 387.064 = 1176385000/2048383 in3 ; ÷139 :
    assert dimw["fraction"] == "1176385000/284725237"
    assert r["billed_weight"] == "5"


def test_cm_two_divisors_same_box():
    ra = {"name": "a", "divisor": "5000", "divisor_unit": "cm3_kg",
          "dim_round": "ceil", "weight_step": "1"}
    rb = dict(ra, name="b", divisor="6000")
    out = _dim("40", "30", "25", "cm", "1.2", "kg", [ra, rb])
    a, b = out["results"]
    assert a["billed_weight"] == "6" and a["unit"] == "kg"
    assert b["billed_weight"] == "5"
    # ranking en grammes : 5000 g d'abord
    assert out["ranking"][0]["rule"] == "b"
    assert out["ranking"][0]["grams"] == "5000"
    assert out["results"][0]["grams_for_ranking"] == "6000"


def test_cap_named_and_actual_only_rounding():
    out = _dim("20", "20", "12", "in", "2", "lb",
               [dict(R139, cap="30")])
    r = out["results"][0]
    assert r["billed_weight"] == "30" and r["capped"] is True
    out2 = _dim("20", "20", "12", "in", "2.4", "lb",
                [dict(R139, divisor="1")])  # dim = 4800 -> cap pas cap
    assert out2["results"][0]["billed_weight"] == "4800"
    out3 = _dim("1", "1", "1", "in", "2.4", "lb",
                [dict(R139, divisor="139")])
    # max(2.4 ; 1/139) = 2.4 -> palier 1 -> 3 : LE PALIER s'applique
    # aussi au poids réel (règle publiée, pas un arrondi bancaire)
    assert out3["results"][0]["billed_weight"] == "3"
    assert out3["results"][0]["governs"] == "actual"


def test_dim_refusals_are_named():
    for kw, field in (
        (dict(R139, divisor_unit="mm3_g"), "rules[0].divisor_unit"),
        (dict(R139, weight_step="0.4"), "rules[0].weight_step"),
        (dict(R139, dim_round="round"), "rules[0].dim_round"),
    ):
        with pytest.raises(dimkit.DimError) as e:
            _dim("12", "8", "6", "in", "2", "lb", [kw])
        assert e.value.field == field
    with pytest.raises(dimkit.DimError) as e:
        _dim("12", "8", "6", "in", "2", "lb", [R139] * 7)
    assert "too many" in str(e.value.message)
    with pytest.raises(dimkit.DimError) as e:
        _dim("0", "8", "6", "in", "2", "lb", [R139])
    assert e.value.field == "dims.l"


# ---------------- coerce : grammaire publiée, attentes MAIN -----------

def _co(raw, schema, **kw):
    a = {"raw": raw, "schema": schema}
    a.update(kw)
    return castkit.run_coerce(a)


def test_magpie_whole_float_to_int():
    out = _co('{"limit": 8.0}', {"limit": "integer"})
    assert out["coerced_text"] == '{"limit": 8}'
    assert out["changes"][0]["rule"] == "WHOLE_FLOAT"
    assert out["coerced"] == {"limit": 8}


def test_serde_u64_replay_2500_and_17277():
    out = _co('{"yield_time_ms": 2500.0, "session_id": 17277.0}',
              {"yield_time_ms": "u64", "session_id": "u64"})
    assert out["coerced"] == {"yield_time_ms": 2500,
                              "session_id": 17277}
    assert len(out["changes"]) == 2


def test_negative_zero_fraction_still_int():
    out = _co('{"a": -3.00}', {"a": "i64"})
    assert out["coerced_text"] == '{"a": -3}'


def test_real_fraction_refused_never_truncated():
    out = _co('{"b": 2.5}', {"b": "integer"})
    ref = out["refused"][0]
    assert ref["code"] == "FRACTIONAL" and ref["path"] == "b"
    assert out["coerced_text"] == '{"b": 2.5}'   # tel quel, jamais 2
    with pytest.raises(castkit._StrictRefused):
        _co('{"b": 2.5}', {"b": "integer"}, strict="true")


def test_exponent_left_as_written_and_reemitted():
    # le fix publie laisse les exponents ; la notation survit a la
    # re-emission (json.loads l'aurait perdue : 1.0e3 -> 1000.0)
    out = _co('{"n": 1.0e3}', {"n": "integer"})
    assert out["coerced_text"] == '{"n": 1.0e3}'
    assert out["changes"] == []
    assert out["left_as_written"][0]["why"].startswith("exponent")


def test_praisonai_string_cast_is_optin():
    raw = '{"quantity": "2", "unit_price": "3"}'
    off = _co(raw, {"quantity": "integer", "unit_price": "integer"})
    assert off["changes"] == []
    assert {x["path"] for x in off["left_as_written"]} == \
        {"quantity", "unit_price"}
    on = _co(raw, {"quantity": "integer", "unit_price": "integer"},
             cast_strings="on")
    assert on["coerced"] == {"quantity": 2, "unit_price": 3}
    assert on["changes"][0]["rule"] == "STRING_CAST"


def test_bool_truthy_refused_by_name():
    out = _co('{"force": "false"}', {"force": "boolean"})
    ref = out["refused"][0]
    assert ref["code"] == "BOOL_TRUTHY"
    assert "write false" in ref["repair"]
    # 1/0 ne sont PAS des booleens ici :
    out2 = _co('{"force": 1}', {"force": "boolean"})
    assert out2["refused"][0]["code"] == "NOT_BOOLEAN"


def test_leading_zero_never_cast_even_optin():
    out = _co('{"code": "007", "qty": "2"}',
              {"code": "integer", "qty": "integer"},
              cast_strings="on")
    assert out["refused"][0]["code"] == "LEADING_ZERO"
    assert out["coerced_text"] == '{"code": "007", "qty": 2}'


def test_serde_bounds_named():
    # 2^63 = 9223372036854775808 depasse i64 max 9223372036854775807
    out = _co('{"id": 9223372036854775808}', {"id": "i64"})
    ref = out["refused"][0]
    assert ref["code"] == "BOUND"
    assert "9223372036854775807" in ref["expected"]
    # un float a fraction nulle hors borne = BOUND aussi
    out2 = _co('{"id": 2000000000.0}', {"id": "u32"})  # 2e9 <= u32 max
    assert out2["coerced"] == {"id": 2000000000}
    out3 = _co('{"id": 5000000000.0}', {"id": "u32"})
    assert out3["refused"][0]["code"] == "BOUND"


def test_arrays_indexed_paths():
    out = _co('{"ids": [1.0, 2.5, 3]}', {"ids": "array<integer>"})
    assert out["changes"][0]["path"] == "ids[0]"
    assert out["refused"][0]["path"] == "ids[1]"
    assert out["coerced_text"] == '{"ids": [1, 2.5, 3]}'
    out2 = _co('{"ids": 1.0}', {"ids": "array<integer>"})
    assert out2["refused"][0]["code"] == "NOT_ARRAY"


def test_undeclared_missing_nested_dup():
    out = _co('{"name": 8.0, "extra": "x"}', {"name": "string"},
              cast_strings="on")
    assert out["coerced_text"] == '{"name": "8.0", "extra": "x"}'
    assert out["undeclared_untouched"] == ["extra"]
    out2 = _co('{"a": {"b": 1}}', {"a": "integer"})
    assert out2["left_as_written"][0]["path"] == "a"  # nested, nomme
    with pytest.raises(castkit.CoerceError) as e:
        _co('{"a":1,"a":2}', {"a": "integer"})
    assert "duplicate" in str(e.value.message)
    with pytest.raises(castkit.CoerceError):
        _co('{"a":1,}', {"a": "integer"})


def test_schema_grammar_closed():
    with pytest.raises(castkit.CoerceError) as e:
        _co('{"a": 1}', {"a": "uint42"})
    assert "schema.a" == e.value.field
    with pytest.raises(castkit.CoerceError) as e:
        _co('{"a": "on"}', {"a": "integer"}, cast_strings="maybe")
    assert e.value.field == "cast_strings"


# ---------------- HTTP + MCP + pins de contrat ------------------------

def test_http_ship_dimweight_contract():
    r = client.post("/api/v1/ship/dimweight", json={
        "dims": {"l": "12", "w": "8", "h": "6", "unit": "in"},
        "actual_weight": {"value": "2", "unit": "lb"},
        "rules": [R139]})
    assert r.status_code == 200
    b = r.json()
    assert b["results"][0]["billed_weight"] == "5"
    assert "sha256" in b and b["scope_note"]


def test_http_dims_json_number_refused():
    r = client.post("/api/v1/ship/dimweight", json={
        "dims": {"l": 12, "w": 8, "h": 6, "unit": "in"},
        "actual_weight": {"value": "2", "unit": "lb"},
        "rules": [R139]})
    assert r.status_code == 400


def test_http_json_coerce_and_strict_400():
    r = client.post("/api/v1/json/coerce", json={
        "raw": '{"limit": 8.0}', "schema": {"limit": "integer"}})
    assert r.status_code == 200
    assert r.json()["coerced_text"] == '{"limit": 8}'
    r2 = client.post("/api/v1/json/coerce", json={
        "raw": '{"b": 2.5}', "schema": {"b": "integer"},
        "strict": "true"})
    assert r2.status_code == 400
    err = r2.json()["errors"][0]
    assert err["field"] == "b" and "FRACTIONAL" in err["message"]


def test_determinism_both_routes():
    for path, body in (
        ("/api/v1/ship/dimweight",
         {"dims": {"l": "20", "w": "20", "h": "12", "unit": "in"},
          "actual_weight": {"value": "2", "unit": "lb"},
          "rules": [R139, {"name": "amzprep", "divisor": "139",
                           "divisor_unit": "in3_lb",
                           "dim_round": "ceil", "weight_step": "none"}]}),
        ("/api/v1/json/coerce",
         {"raw": '{"n": 1.0e3, "limit": 8.0}',
          "schema": {"n": "integer", "limit": "integer"}})):
        r1 = client.post(path, json=body)
        r2 = client.post(path, json=body)
        assert r1.status_code == 200 and r1.content == r2.content


def test_mcp_replay_both_tools():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/call",
                                  "params": {"name": "json_coerce",
                                             "arguments": {
                                                 "raw": '{"limit": 8.0}',
                                                 "schema": {"limit":
                                                            "integer"}}}})
    assert r.status_code == 200
    text = json.dumps(r.json())
    assert '"limit": 8' in text.replace('\\"', '"')
    r2 = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2,
                                   "method": "tools/call",
                                   "params": {"name": "ship_dimweight",
                                              "arguments": {
                                                  "dims": {"l": "12",
                                                           "w": "8",
                                                           "h": "6",
                                                           "unit": "in"},
                                                  "actual_weight": {
                                                      "value": "2",
                                                      "unit": "lb"},
                                                  "rules": [
                                                      {"name": "x",
                                                       "divisor": "139",
                                                       "divisor_unit":
                                                       "in3_lb",
                                                       "dim_round":
                                                       "ceil",
                                                       "weight_step":
                                                       "1"}]}}})
    assert r2.status_code == 200


def test_route_top1_both_tools_six_phrases():
    qs = [
        ("carrier billed weight dimensional divisor parcel",
         "ship_dimweight"),
        ("poids facture du colis dimensions diviseur transporteur",
         "ship_dimweight"),
        ("peso cobrado da caixa cubagem divisor transportadora",
         "ship_dimweight"),
        ("tool call arguments rejected invalid type floating point "
         "expected u64", "json_coerce"),
        ("les arguments de l'appel outil refusés par le parseur "
         "strict", "json_coerce"),
        ("os argumentos da chamada da ferramenta recusados pelo "
         "parser estrito", "json_coerce"),
    ]
    for q, want in qs:
        r = client.get("/route", params={"q": q})
        top = r.json()["tools"][0]["tool"]
        assert top == want, (q, top)


def test_everyday_chip_baked_three_languages():
    # la puce e14 est la SORTIE REELLE rejouee (6 vs 5 kg, 30 000 ÷
    # 5 000 vs 6 000) — recalculée ici a la main, pas recopiee
    en = json.loads(open("locales/en.json", encoding="utf-8").read())
    fr = json.loads(open("locales/fr.json", encoding="utf-8").read())
    pt = json.loads(open("locales/pt.json", encoding="utf-8").read())
    assert "billed 6 kg vs 5 kg" in en["everyday_grid"]
    assert "facturé 6 kg" in fr["everyday_grid"]
    assert "cobrado 6 kg" in pt["everyday_grid"]
    # resize 22-11 bundle66: e16 (unitprice) rejoint la grille
    assert "Sixteen" in en["everyday.intro"]
    assert "Seize" in fr["everyday.intro"]
    assert "Dezesseis" in pt["everyday.intro"]


def test_golden_contains_eleven_new_pins():
    g = json.loads(open("golden.json", encoding="utf-8").read())
    import os
    names = [json.loads(open("corpus/%s" % f, encoding="utf-8").read())
             ["name"] for f in os.listdir("corpus")
             if f.startswith(("ship_dimweight_", "json_coerce_"))]
    assert len(names) == 11
    for n in names:
        assert n in g and g[n].startswith("200:"), n
