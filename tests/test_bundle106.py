# -*- coding: utf-8 -*-
"""Bundle 106 — /agent/tool-trim : QUOI DÉBRANCHER pour tenir le budget
de fenêtre, re-compte exact des survivants au canon des sœurs.

Golds tracés À LA MAIN sur l'oracle séparé g106 (scratch/
g106_tooltrim_oracle.py, json+Fraction+Decimal stdlib, écrit AVANT
tooltrimkit.py — jamais importé du module). Sens habituel : le test
suit l'oracle ; si la machine contredit, on vérifie DEUX FOIS qui a
raison.

Tracé principal (canons visibles, g106) :
  canon({"name":"a"})  = {"name":"a"}                    -> 12 chars, est 3
  canon(b desc "x")    = {"description":"x","name":"b"}   -> 30 chars, est 8
  canon(c desc "yy")   = {"description":"yy","name":"c"}  -> 31 chars, est 8
  total 73 -> est GLOBAL ceil(73/4) = 19 (jamais 3+8+8=19... ici égal,
  la divergence se TRAQUE ailleurs, vecteur ab/ac/ad : global 3, somme 4).
  usage {a:0, b:3} -> a IDLE_30J (coupé D'ABORD, chars desc),
  b RATIO 30/3 = 10.0, c UNKNOWN (jamais avant les mesurés).
  budget 8 : gouttes [a, b] ; survivants [c] est 8 (= borne close, FITS).
  budget 25 : FITS_AS_IS, zéro goutte, sauvegarde 0 nommée.
  keep [b] budget 5 : a puis c gouttes, b protégé, est 8 > 5 ->
  STILL_OVER, reste 3 CHIFFRÉ, jamais de conseil deviné.
  S (big 91 UNKNOWN, small 34 RATIO 34,0, mid 35 RATIO 0.35) budget 30 :
  on coupe small puis mid — les MESURÉS avant l'INCONNU, même gros,
  même bon ; budget 20 l'inconnu tombe aussi -> UNKNOWN_CUTS + ALL_DROPPED.
  budget_pct : window 200000 x 10 -> 20000 exact ; 1000 x 33 -> 330 ;
  window 50 x 1 -> floor 0 CLAMPÉ à 1 (un budget ne meurt pas d'arrondi).
  tie (ii,kk,mm chars 13, calls 2) -> ratio égaux, NOM ASCENDANT.
  dollars : turns 3, price "2" -> 11 x 3 x 2 / 1e6 = "0.000066".
"""
import hashlib
import json
import math

import pytest
from fastapi.testclient import TestClient

import contexttaxkit as ct
import main
import tooltrimkit as k

client = TestClient(main.app)
main.RATE_LIMIT = 10**9

T = [{"name": "a"}, {"name": "b", "description": "x"},
     {"name": "c", "description": "yy"}]
U = {"a": 0, "b": 3}


# ------------------------------------------------- mesure canon (g106)
def test_a1_canon_chars_golds():
    assert len(json.dumps({"name": "a"}, sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False)) == 12
    assert len(json.dumps({"name": "b", "description": "x"},
                          sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False)) == 30
    assert len(json.dumps({"name": "c", "description": "yy"},
                          sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False)) == 31


def test_a2_trimmed_fits_idle_first():
    r = k.tool_trim(T, budget=8, usage=U)
    assert r["verdict"] == "TRIMMED_FITS"
    assert r["before"] == {"tools": 3, "chars": 73, "token_estimate": 19,
                           "pct_of_window": 0.01}
    assert r["after"]["chars"] == 31 and r["after"]["token_estimate"] == 8
    assert [p["name"] for p in r["plan"]] == ["a", "b"]
    assert [p["class"] for p in r["plan"]] == ["IDLE_30J", "RATIO"]
    assert r["plan"][0]["calls_30d"] == 0
    assert r["plan"][1]["cost_per_call"] == 10.0
    assert sorted(s["name"] for s in r["survivors"]) == ["c"]
    assert r["saved"]["tokens_global"] == 11
    assert r["saved"]["tokens_sum_per_tool"] == 11
    assert r["saved"]["divergence"] == 0
    assert r["budget"]["tokens"] == 8 and r["budget"]["via"] == "tokens"
    assert r["budget"]["window"] == 200000


def test_a3_close_bound_fits_as_is():
    # est 19 == budget 19 : borne close de la fratrie, rien à débrancher
    r = k.tool_trim(T, budget=19, usage=U)
    assert r["verdict"] == "FITS_AS_IS" and r["plan"] == []
    assert r["saved"]["tokens_global"] == 0
    r = k.tool_trim(T, budget=25, usage=U)
    assert r["verdict"] == "FITS_AS_IS"


def test_a4_unknown_never_before_measured():
    # budget 6 : il faut tout couper — l'UNKNOWN tombe EN DERNIER
    r = k.tool_trim(T, budget=6, usage=U)
    assert [p["name"] for p in r["plan"]] == ["a", "b", "c"]
    assert [p["class"] for p in r["plan"]] == ["IDLE_30J", "RATIO",
                                               "UNKNOWN"]
    assert r["after"]["token_estimate"] == 0
    assert "ALL_DROPPED" in r["flags"] and "UNKNOWN_CUTS" in r["flags"]
    assert r["saved"]["tokens_global"] == 19


def test_a5_ratio_worst_first():
    # small 34/1 = 34.0 avant mid 35/100 = 0.35 ; big 91 UNKNOWN dernier
    S = [{"name": "big", "description": "x" * 60},
         {"name": "small", "description": "y"},
         {"name": "mid", "description": "zzzz"}]
    r = k.tool_trim(S, budget=30, usage={"small": 1, "mid": 100})
    assert [p["name"] for p in r["plan"]] == ["small", "mid"]
    assert [p["class"] for p in r["plan"]] == ["RATIO", "RATIO"]
    assert r["plan"][0]["cost_per_call"] == 34.0
    assert r["plan"][1]["cost_per_call"] == 0.35
    assert [s["name"] for s in r["survivors"]] == ["big"]
    assert r["saved"]["tokens_global"] == 17
    assert r["saved"]["tokens_sum_per_tool"] == 18   # ceil(34/4)=9, ceil(35/4)=9
    assert r["saved"]["divergence"] == 1
    assert "UNKNOWN_CUTS" not in r["flags"]


def test_a6_still_over_reste_chiffre():
    r = k.tool_trim(T, budget=5, usage=U, keep=["b"])
    assert r["verdict"] == "STILL_OVER"
    assert r["reste"] == 3                    # est(b) 8 - budget 5
    assert [p["name"] for p in r["plan"]] == ["a", "c"]
    assert [s["name"] for s in r["survivors"]] == ["b"]
    assert "KEEP_PROTECTED" in r["flags"]


def test_a7_budget_pct_floor_and_clamp():
    r = k.tool_trim(T, budget_pct=10, window=200000)
    assert r["budget"]["tokens"] == 20000 and r["budget"]["via"] == "budget_pct"
    assert r["verdict"] == "FITS_AS_IS"
    r = k.tool_trim(T, budget_pct=33, window=1000)
    assert r["budget"]["tokens"] == 330       # 1000*33//100 exact
    r = k.tool_trim(T, budget_pct=1, window=50)
    assert r["budget"]["tokens"] == 1         # floor 0 clampé à 1, déclaré


def test_a8_ties_name_ascending():
    Z = [{"name": "mm"}, {"name": "kk"}, {"name": "ii"}]   # 13 chars chacun
    r = k.tool_trim(Z, budget=3, usage={"mm": 2, "kk": 2, "ii": 2})
    assert [p["name"] for p in r["plan"]] == ["ii", "kk", "mm"]
    # ratio égaux (13/2), chars égaux -> NOM ASCENDANT, règle close


def test_a9_divergence_global_vs_sum():
    W = [{"name": "ab"}, {"name": "ac"}, {"name": "ad"}]  # 13 chars
    r = k.tool_trim(W, budget=7)
    # total 39 -> ceil = 10 ; survivants 26 -> ceil = 7 ; goutte 13 -> 4
    assert r["saved"]["tokens_global"] == 3    # 10 - 7
    assert r["saved"]["tokens_sum_per_tool"] == 4   # ceil(13/4)
    assert r["saved"]["divergence"] == 1       # les deux chiffres voyagent
    assert r["verdict"] == "TRIMMED_FITS"


def test_a10_no_usage_data_cost_only_order():
    # zéro usage : NO_USAGE_DATA, les UNKNOWN ordonnés chars desc, nom asc
    r = k.tool_trim(T, budget=8)
    assert "NO_USAGE_DATA" in r["flags"]
    assert [p["name"] for p in r["plan"]] == ["c", "b"]   # 31, 30
    assert r["verdict"] == "TRIMMED_FITS"
    assert r["after"]["token_estimate"] == 3    # ne reste que a (12)


def test_a11_per_turn_rule():
    r = k.tool_trim(T, budget=8, usage=U, turns=3)
    assert r["saved"]["per_turn"] == 33         # 11 x 3 (Irolla)
    assert "price" not in r


def test_a12_dollars_at_caller_price():
    r = k.tool_trim(T, budget=8, usage=U, turns=3, input_per_mtok="2")
    assert r["price"]["usd_saved_for_this_run"] == "0.000066"
    assert r["price"]["input_per_mtok"] == "2"


def test_a13_empty_listing_is_state():
    r = k.tool_trim([], budget=5)
    assert r["verdict"] == "FITS_AS_IS"
    assert "EMPTY_LISTING" in r["flags"]
    assert r["before"]["token_estimate"] == 0


# ------------------------------------------------------- refus nommés
def test_b1_budget_required():
    with pytest.raises(k.ToolTrimError) as e:
        k.tool_trim(T)
    assert e.value.field == "budget"
    assert e.value.expected == "budget >= 1 or budget_pct 1..100"


def test_b2_two_spellings_conflict():
    with pytest.raises(k.ToolTrimError) as e:
        k.tool_trim(T, budget=8, budget_pct=10)
    assert e.value.field == "budget"
    assert "never both" in e.value.expected


def test_b3_budget_floor():
    for bad in (0, -5, True, "8"):
        with pytest.raises(k.ToolTrimError) as e:
            k.tool_trim(T, budget=bad)
        assert e.value.field == "budget"


def test_b4_pct_bounds():
    for bad in (0, 101, 2.5):
        with pytest.raises(k.ToolTrimError) as e:
            k.tool_trim(T, budget_pct=bad)
        assert e.value.field == "budget_pct"


def test_b5_usage_ghost_name():
    with pytest.raises(k.ToolTrimError) as e:
        k.tool_trim(T, budget=8, usage={"zz": 5})
    assert e.value.field == "usage.zz"
    assert "must appear in tools" in e.value.expected


def test_b6_usage_negative():
    with pytest.raises(k.ToolTrimError) as e:
        k.tool_trim(T, budget=8, usage={"a": -1})
    assert e.value.field == "usage.a"


def test_b7_keep_ghost_and_dup():
    with pytest.raises(k.ToolTrimError) as e:
        k.tool_trim(T, budget=8, keep=["qq"])
    assert e.value.field == "keep"
    with pytest.raises(k.ToolTrimError) as e:
        k.tool_trim(T, budget=8, keep=["a", "a"])
    assert e.value.field == "keep"


def test_b8_duplicate_names_shadowing():
    with pytest.raises(k.ToolTrimError) as e:
        k.tool_trim([{"name": "a"}, {"name": "a"}], budget=5)
    assert "shadowing" in e.value.message


def test_b9_empty_name_and_non_object():
    with pytest.raises(k.ToolTrimError) as e:
        k.tool_trim([{"name": ""}], budget=5)
    assert e.value.field == "tools[0].name"
    with pytest.raises(k.ToolTrimError) as e:
        k.tool_trim(["x"], budget=5)
    assert e.value.field == "tools[0]"


def test_b10_ceiling_5000():
    tools = [{"name": "n%d" % i} for i in range(5001)]
    with pytest.raises(k.ToolTrimError) as e:
        k.tool_trim(tools, budget=5)
    assert e.value.field == "tools" and "5000" in e.value.message


def test_b11_price_argument_contract():
    for bad in ("x", "-1"):
        with pytest.raises(k.ToolTrimError) as e:
            k.tool_trim(T, budget=8, input_per_mtok=bad)
        assert e.value.field == "input_per_mtok"
    with pytest.raises(k.ToolTrimError) as e:
        k.tool_trim(T, budget=8, turns=0)
    assert e.value.field == "turns"


def test_b12_window_argument():
    with pytest.raises(k.ToolTrimError) as e:
        k.tool_trim(T, budget=8, window=0)
    assert e.value.field == "window"


# ------------------------------------------------------ contrat live
PIN = {"tools": [{"name": "mail", "description": "send email"},
                 {"name": "notes", "description": "x" * 48},
                 {"name": "drive", "description": "files"},
                 {"name": "maps", "description": "geo"}],
       "usage": {"mail": 2, "notes": 0, "drive": 40},
       "budget": 24, "turns": 10}


def test_c1_api_roundtrip_determinism():
    r1 = client.post("/api/v1/agent/tool-trim", json=PIN)
    r2 = client.post("/api/v1/agent/tool-trim", json=PIN)
    assert r1.status_code == 200, r1.text
    assert r1.content == r2.content
    b = r1.json()
    # g106 : chars 42, 81, 38, 35 -> total 196 -> est 49
    assert b["before"]["chars"] == 196 and b["before"]["token_estimate"] == 49
    # notes IDLE (0 appels) puis mail 42/2=21 ; après = 73 chars -> 19 <= 24
    assert [p["name"] for p in b["plan"]] == ["notes", "mail"]
    assert b["verdict"] == "TRIMMED_FITS"
    assert b["saved"]["tokens_global"] == 30
    assert b["saved"]["tokens_sum_per_tool"] == 32   # ceil(81/4)+ceil(42/4)
    assert b["saved"]["divergence"] == 2
    assert b["saved"]["per_turn"] == 300             # 30 x 10 tours
    assert sorted(s["name"] for s in b["survivors"]) == ["drive", "maps"]


def test_c2_api_refus_field_expected():
    r = client.post("/api/v1/agent/tool-trim",
                    json={"tools": T, "budget": 8, "usage": {"zz": 1}})
    assert r.status_code == 400
    err = r.json()["errors"][0]
    assert err["field"] == "usage.zz" and "expected" in err


def test_c3_soeur_recompte_identique():
    # thèse du lot : le re-compte EST la mesure de context-tax — collez
    # les survivants, le nombre doit être identique, octet à octet
    r = client.post("/api/v1/agent/tool-trim", json=PIN).json()
    keep = sorted(s["name"] for s in r["survivors"])
    survivors = [t for t in PIN["tools"] if t["name"] in keep]
    tax = ct.context_tax(survivors)
    assert tax["total_chars"] == r["after"]["chars"] == 73
    assert tax["token_estimate"] == r["after"]["token_estimate"] == 19


# ------------------------------------------------------------ routeur
def test_j1_aiguilles_trim_x3():
    for q in ("which MCP tools should I disconnect to fit my context budget",
              "trop d outils MCP branches lesquels couper pour tenir le "
              "budget",
              "quais ferramentas desligar para caber no orcamento",
              "115 tools 43000 tokens what to trim before disconnecting",
              "is my tool list over budget on a 60k local window"):
        r = client.get("/route", params={"q": q}).json()
        assert r["tools"], q
        assert r["tools"][0]["tool"] == "agent_tooltrim", q


def test_j2_fratrie_garde_ses_aiguilles():
    for q, want in (
            ("combien de tokens coûte la liste d'outils de ce serveur MCP "
             "à chaque tour", "agent_contexttax"),
            ("how much does this pasted tools/list cost my 200k window",
             "agent_contexttax"),
            ("what did the mcp update cost my tool list in extra tokens",
             "agent_costdiff"),
            ("quel surcoût de tokens la nouvelle version du serveur MCP "
             "m'apporte", "agent_costdiff"),
            ("what changed in my MCP tool list since the reading I pinned",
             "agent_mcpsurface"),
            ("is retrying this timeout a fourth time rational or am i stuck",
             "agent_retrybudget")):
        r = client.get("/route", params={"q": q}).json()
        assert r["tools"][0]["tool"] == want, q


def test_j3_blagues_meurent():
    for q in ("tell me a joke about trimming hedges",
              "blague sur les outils à débrancher",
              "piada sobre desligar ferramentas"):
        names = [t["tool"] for t in
                 client.get("/route", params={"q": q}).json()["tools"]]
        assert "agent_tooltrim" not in names, q


def test_j4_leurre_lave_vue():
    # débrancher un électroménager ne se prescrit pas ici : pas d'outils,
    # pas de budget, la phrase doit mourir avant l'aiguille
    names = [t["tool"] for t in client.get(
        "/route", params={"q": "je veux débrancher mon lave-vaisselle"}
    ).json()["tools"]]
    assert "agent_tooltrim" not in names


# ------------------------------------------------- vitrine & compteurs
def test_k1_landing_carte_exactement_une_x3():
    for lang in ("en", "fr", "pt"):
        html = main.LANDING[lang]
        assert html.count('data-tool="agent_tooltrim"') == 1, lang


def test_k2_manifest_porte_l_outil():
    body = client.get("/agent/manifest").text
    assert "agent_tooltrim" in body
