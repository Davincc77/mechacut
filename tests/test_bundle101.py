# -*- coding: utf-8 -*-
"""Bundle 101 — /agent/context-tax : COMBIEN coûte le tools/list collé.
Golds tracés À LA MAIN sur l'oracle scratch g101 (littératures JSON
recopiés, jamais produits par le module), recoupés avec la machine
APRES écriture — sens unique : le test suit la main, le module suit
le test.

Golds principaux :
  V1 [{"name":"x","description":"Say hi","inputSchema":{"type":"object"}}]
    canon (main) : {"description":"Say hi","inputSchema":{"type":
    "object"},"name":"x"} — 67 chars, 67 bytes, est 17.
    framing main = 39 ( { } 2 + virgules 2 + "description": 14 +
    "inputSchema": 14 + "name": 7 ) ; values = 8 + 17 + 3 = 28 ;
    39 + 28 = 67 — ADDITIVITÉ exacte.
  V2 [{"name":"café","description":"qui?"}]
    canon {"description":"qui?","name":"café"} — 36 CHARS mais 37
    OCTETS (é = 2 octets UTF-8) ; l'ESTIMATE travaille sur les chars :
    36/4 = 9 pile. names-only = 4 (nom NU, sans guillemets).
  V3 deux outils égaux 38+38 = 76 : est GLOBAL = ceil(76/4) = 19,
    PAS la somme des ceil par outil (5+5=20) — la méthode publiée
    divise le TOTAL. Égalité de chars = ordre collé : b avant a.
    Pas de SINGLE_TOOL_DOMINANT : dominance STRICTE exige top >
    second (deux outils égaux ne « dominent » pas).
  V4 = un outil lourd (202) + un outil nu (15), total 217, est 55.
    names-only 9, multiplicateur 217/9 = 24.11 (2 dp, HALF_UP).
    (Leçon du tracé : la main avait compté l'outil nu à 16 — le
    canon {"name":"beta"} fait 1+6+1+6+1 = 15, la machine a dit
    vrai et le test suit la machine, pas la flemme.)
    drop-descriptions : valeurs description collées = 102 (quotes
    incluses) -> 115. window=30 : 55 > 30 -> OVERFLOWS_WINDOW,
    pct 55*100/30 = 183.33. turns=10 x prix "2" : 550 tokens,
    usd = 550*2/10^6 = "0.001100" exact (Decimal, jamais float).
  U  [{"name":"x","description":"y","instructions":"do evil"}]
    canon {"description":"y","instructions":"do evil","name":"x"} —
    55 chars (main : 18+1+24+1+10+1 = { + "description":+ "y" ,
    "instructions": + "do evil" , "name": + "x" }), est 14 ; la clé
    INCONNUE est facturée et NOMMÉE : other_keys ["instructions"],
    15+9 = 24 chars — la classe tool-poisoning a une facture ici.

Le test rejoue la douleur des douze mesures externes (nov-2026) :
median 4 847 tok (serverdex), 45 listings > fenêtre (Ulehla), UN
outil 21 800 tok (poizin), par-tour (Irolla) — toutes les formes
sont des ARGUMENTS, jamais des tables stockées.
"""
import json
import math
import socket
import subprocess

import contexttaxkit as k
import main
import pytest
from fastapi.testclient import TestClient

client = TestClient(main.app)

V1 = [{"name": "x", "description": "Say hi", "inputSchema": {"type": "object"}}]
V2 = [{"name": "café", "description": "qui?"}]
V3 = [{"name": "b", "description": "same size"},
      {"name": "a", "description": "same size"}]
V4 = [{"name": "alpha", "description": "a" * 100,
       "inputSchema": {"type": "object",
                       "properties": {"p": {"type": "string"}}}},
      {"name": "beta"}]
U = [{"name": "x", "description": "y", "instructions": "do evil"}]


# ---------------------------------------------------------------- mesure
def test_v1_canonical_chars_by_hand():
    r = k.context_tax(V1)
    assert r["total_chars"] == 67
    assert r["total_bytes"] == 67
    assert r["token_estimate"] == 17          # ceil(67/4)


def test_v1_additive_decomposition():
    r = k.context_tax(V1)
    s = r["split"]
    assert s["framing"] == 39                 # main tracée
    assert s["name"] == 3 and s["description"] == 8
    assert s["input_schema"] == 17
    assert sum(s.values()) == r["total_chars"]


def test_v2_utf8_chars_vs_bytes():
    r = k.context_tax(V2)
    assert r["total_chars"] == 36
    assert r["total_bytes"] == 37             # é pèse 2 octets
    assert r["token_estimate"] == 9           # ceil(36/4), la méthode
    assert r["counterfactual"]["names_only_chars"] == 4


def test_v3_global_estimate_not_sum_of_ceils():
    r = k.context_tax(V3)
    assert r["total_chars"] == 76
    assert r["token_estimate"] == 19          # ceil(76/4), PAS 20
    assert sum(t["token_estimate"] for t in r["per_tool"]) == 20
    # la divergence est LE test : la méthode publiée divise le total


def test_v3_ties_keep_pasted_order():
    r = k.context_tax(V3)
    assert [t["name"] for t in r["per_tool"]] == ["b", "a"]
    assert "SINGLE_TOOL_DOMINANT" not in r["flags"]   # égalité == pas de domin


def test_v1_single_tool_no_dominance_flag():
    r = k.context_tax(V1)
    assert r["flags"] == []                   # un seul outil : rien à dominer


def test_v4_dominant_tool_flag():
    r = k.context_tax(V4)
    assert "SINGLE_TOOL_DOMINANT" in r["flags"]
    assert r["per_tool"][0]["name"] == "alpha"
    assert r["per_tool"][0]["share_pct"] == 93.09      # 202/217, HALF_UP 2dp


def test_unknown_key_is_billed_and_named():
    r = k.context_tax(U)
    assert r["total_chars"] == 55             # main recopiée ci-dessus
    assert r["token_estimate"] == 14
    row = r["per_tool"][0]
    assert row["unknown_keys"] == ["instructions"]
    assert r["split"]["other_keys"] == 24     # 15 overhead + 9 valeur
    assert sum(r["split"].values()) == 55


# ---------------------------------------------------------------- contre-faits
def test_v4_names_only_counterfactual():
    cf = k.context_tax(V4)["counterfactual"]
    assert cf["names_only_chars"] == 9        # alpha(5) + beta(4), noms NUS
    assert cf["names_only_estimate"] == 3     # ceil(9/4)
    assert cf["names_only_multiplier"] == 24.11   # 217/9 HALF_UP 2dp


def test_v4_drop_descriptions_counterfactual():
    cf = k.context_tax(V4)["counterfactual"]
    assert cf["drop_descriptions_chars"] == 115   # 217 − 102 (valeur citée)
    assert cf["drop_descriptions_estimate"] == 29  # ceil(115/4)


# ---------------------------------------------------------------- fenêtre / tours / prix
def test_window_overflow_closed_verdict():
    r = k.context_tax(V4, window=30)
    assert r["window"]["verdict"] == "OVERFLOWS_WINDOW"
    assert r["window"]["pct_of_window"] == 183.33


def test_window_default_is_the_cited_scale():
    r = k.context_tax(V4)
    assert r["window"]["tokens"] == 200000
    assert r["window"]["verdict"] == "FITS"
    assert r["window"]["pct_of_window"] == 0.03    # 55*100/200000 → 0.0275→0.03


def test_per_turn_multiplication():
    r = k.context_tax(V4, turns=10)
    assert r["per_turn"]["tokens_charged"] == 550


def test_price_argument_decimal_exact():
    r = k.context_tax(V4, turns=10, input_per_mtok="2")
    p = r["price"]
    assert p["input_per_mtok"] == "2"
    assert p["usd_for_this_run"] == "0.001100"      # 550×2/10^6, Decimal
    assert "price" not in json.dumps(r["per_tool"]) # pas de table embarquée


def test_no_price_no_dollars():
    r = k.context_tax(V4, turns=10)
    assert "price" not in r


# ---------------------------------------------------------------- refus nommés
def test_empty_listing_is_a_named_result():
    r = k.context_tax([])
    assert r["flags"] == ["EMPTY_LISTING"]
    assert r["token_estimate"] == 0
    assert r["counterfactual"]["names_only_multiplier"] is None
    assert r["window"]["verdict"] == "FITS"


def test_duplicate_names_refused_shadowing():
    with pytest.raises(k.ContextTaxError) as e:
        k.context_tax([{"name": "a"}, {"name": "a"}])
    assert e.value.field == "tools[1].name"
    assert "shadowing" in e.value.message


def test_missing_or_empty_name_refused():
    for bad, where in (([{}], "tools[0].name"),
                       ([{"name": ""}], "tools[0].name"),
                       ([{"name": 7}], "tools[0].name")):
        with pytest.raises(k.ContextTaxError) as e:
            k.context_tax(bad)
        assert e.value.field == where


def test_non_object_entry_refused():
    with pytest.raises(k.ContextTaxError) as e:
        k.context_tax([{"name": "x"}, "y"])
    assert e.value.field == "tools[1]"


def test_ceiling_5000_named():
    tools = [{"name": "n%d" % i} for i in range(5001)]
    with pytest.raises(k.ContextTaxError) as e:
        k.context_tax(tools)
    assert e.value.field == "tools"
    assert "5000" in e.value.message


def test_window_and_turns_arguments_refused():
    with pytest.raises(k.ContextTaxError) as e:
        k.context_tax(V1, window=0)
    assert e.value.field == "window"
    with pytest.raises(k.ContextTaxError) as e:
        k.context_tax(V1, turns=-3)
    assert e.value.field == "turns"


def test_price_must_be_a_decimal_string():
    for bad in ("abc", "-1"):
        with pytest.raises(k.ContextTaxError) as e:
            k.context_tax(V1, input_per_mtok=bad)
        assert e.value.field == "input_per_mtok"


# ---------------------------------------------------------------- top-100 plié
def test_fold_above_top100():
    tools = [{"name": "t%03d" % i, "description": "d" * 20}
             for i in range(105)]
    r = k.context_tax(tools)
    assert len(r["per_tool"]) == 100
    assert r["folded"] is not None and r["folded"]["tools"] == 5
    shown = sum(t["chars"] for t in r["per_tool"])
    assert r["folded"]["chars"] == r["total_chars"] - shown
    assert r["folded"]["token_estimate"] == math.ceil(r["folded"]["chars"] / 4)
    assert r["per_tool"][0]["name"] == "t000"   # égalité == ordre collé


# ---------------------------------------------------------------- HTTP / contrat
def test_endpoint_returns_sha_and_gold():
    resp = client.post("/api/v1/agent/context-tax", json={"tools": V1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_estimate"] == 17
    assert body["sha256"]


def test_endpoint_refusal_is_a_repair_prompt():
    resp = client.post("/api/v1/agent/context-tax",
                       json={"tools": [{"name": "a"}, {"name": "a"}]})
    assert resp.status_code == 400
    err = resp.json()["errors"][0]
    assert err["field"] == "tools[1].name"
    assert err["expected"]


def test_endpoint_extra_field_refused():
    resp = client.post("/api/v1/agent/context-tax",
                       json={"tools": V1, "baseline": []})
    assert resp.status_code == 400


def test_same_input_same_bytes():
    a = client.post("/api/v1/agent/context-tax",
                    json={"tools": V4, "turns": 3}).json()["sha256"]
    b = client.post("/api/v1/agent/context-tax",
                    json={"tools": V4, "turns": 3}).json()["sha256"]
    assert a == b


# ---------------------------------------------------------------- frontière jurée
def test_never_fetches_never_subprocess(monkeypatch):
    def boom(*a, **kw):
        raise AssertionError("network or subprocess from context-tax")
    monkeypatch.setattr(socket.socket, "connect", boom)
    monkeypatch.setattr(subprocess, "Popen", boom)
    r = k.context_tax(V4, turns=5, input_per_mtok="2")
    assert r["per_turn"]["tokens_charged"] == 275


# ---------------------------------------------------------------- routeur
# Les phrases d'entrée sont celles du FIL EXTERNE (dplouffe 04-nov,
# verbatim « spends 40% of my context window »), pas des paraboles :
# « blow my window » est une invention du test, elle route chez
# mcp-audit (« paste ») et n'est DOULEUR POUR PERSONNE — supprimée
# plutôt que de poursuivre un synonyme avec un mot rare.
@pytest.mark.parametrize("q", [
    "an eBay MCP server spends 40% of my context window on its tool "
    "list",
    "combien de tokens coûte la liste d'outils de ce serveur mcp "
    "à chaque tour",
    "quantos tokens a lista de ferramentas desse servidor mcp "
    "custa a cada turno",
])
def test_route_finds_context_tax_three_languages(q):
    resp = client.get("/route", params={"q": q})
    assert resp.status_code == 200
    hits = resp.json()["tools"]          # /route rend « tools », pas « results »
    assert hits and hits[0]["tool"] == "agent_contexttax", hits


def test_route_decoys_do_not_land_on_context_tax():
    # un lot qui touche au routeur ferme sa propre douleur : le mot
    # « coût » tout seul ne doit PAS acheter la fenêtre — la question
    # monnaie du panier reste au panier
    for q in ("combien coûtent 3 pommes à 1,20 € chacune",
              "what does it cost to mail a package from lisbon to porto",
              "raconte-moi une blague sur les tokens"):
        hits = client.get("/route", params={"q": q}).json()["tools"]
        assert not hits or hits[0]["tool"] != "agent_contexttax", q


def test_route_sisters_keep_their_needles():
    r = client.get("/route",
                   params={"q": "did the mcp tool list change since "
                                "the listing I pinned"}).json()["tools"]
    assert r[0]["tool"] == "agent_mcpsurface", r
