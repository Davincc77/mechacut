# -*- coding: utf-8 -*-
"""Bundle 104 — /agent/cost-diff : le PRIX DE L'UPDATE, delta chiffré
entre deux listings collés, par outil et par champ.

Golds tracés À LA MAIN sur l'oracle séparé g104 (scratch/g104_oracle.py,
stdlib json+ceil, écrit AVANT costdiffkit.py — jamais importé du
module). Sens habituel : le test suit l'oracle ; si la machine
contredit, on vérifie DEUX FOIS qui a raison.

Tracé principal (arithmétique visible, g104) :
  canon({"name":"a"}) = {"name":"a"} -> 12 chars, est = ceil(12/4) = 3
  canon({"name":"a","description":"hi"})
      = {"description":"hi","name":"a"} -> 31 chars, est = 8
  delta_chars = 19, delta_est = 5, pct = 166.67 (2 chiffres, HALF_UP)
Autres golds :
  three : avant 138 chars/est 35, après 219/est 55 ; delta global 20,
  somme par outil 21 (DIVERGENCE chiffrée, pas cachée) ; movers
  gamma(+73 ADDED, pct None) puis alpha(+8, est 18->20, +11.11 %,
  moved_fields {"description": 8}) ; beta SAME reste aux classes.
  tie : aa et zz delta +19 pareil -> ordre NOM ascendant (règle close).
  div : [a] -> [ab, abc] : global +4 (3->7), somme +5 (0-3+4+4).
  window : est==window FITS (borne close du frère) ; 3->8 à window=3
  = FITS_TO_OVERFLOWS + drapeau WINDOW_TRANSITION.
  dollars : turns 10, price "2" -> 50 x 2 / 1e6 = "0.000100" ;
  shrink turns 2 price "3" -> -10 tokens, "-0.000030" SIGNE INCLUS.
  fold : 130 outils CHANGED +1 char -> 100 movers + folded 30/30/0.
"""
import main
import pytest
import costdiffkit as k
import contexttaxkit as ct
from fastapi.testclient import TestClient

client = TestClient(main.app)

A_MIN = [{"name": "a"}]
B_MIN = [{"name": "a", "description": "hi"}]
A_THREE = [
    {"name": "alpha", "description": "Say hi",
     "inputSchema": {"type": "object"}},
    {"name": "beta", "description": "Add",
     "inputSchema": {"type": "object"}},
]
B_THREE = [
    {"name": "alpha", "description": "Say hi, loudly",
     "inputSchema": {"type": "object"}},
    {"name": "beta", "description": "Add",
     "inputSchema": {"type": "object"}},
    {"name": "gamma", "description": "New tool",
     "inputSchema": {"type": "object"}},
]
A_TIE = [{"name": "aa"}, {"name": "zz"}]
B_TIE = [{"name": "aa", "description": "hi"},
         {"name": "zz", "description": "hi"}]


# --------------------------------------------------------------- main gold
def test_a1_main_trace_chars_and_estimates():
    r = k.cost_diff(A_MIN, B_MIN)
    assert r["totals"]["before"]["chars"] == 12
    assert r["totals"]["after"]["chars"] == 31
    assert r["totals"]["before"]["token_estimate"] == 3
    assert r["totals"]["after"]["token_estimate"] == 8
    assert r["totals"]["delta"]["token_estimate"] == 5
    assert r["totals"]["delta"]["chars"] == 19


def test_a2_main_trace_pct():
    r = k.cost_diff(A_MIN, B_MIN)
    assert r["totals"]["delta"]["pct_of_before"] == 166.67
    m = r["movers"][0]
    assert m["name"] == "a" and m["class"] == "CHANGED"
    assert m["delta_chars"] == 19
    assert m["token_estimate_delta"] == 5
    assert m["pct_of_before"] == 166.67


def test_a3_additivity_is_a_theorem():
    # loi 3 : somme des delta_chars == total après - total avant
    for a, b in ((A_MIN, B_MIN), (A_THREE, B_THREE),
                 (A_THREE, [B_THREE[0]]), (A_TIE, B_TIE)):
        r = k.cost_diff(a, b)
        assert sum(m["delta_chars"] for m in r["movers"]) == \
            r["totals"]["delta"]["chars"]


def test_a4_no_wall_clock_and_canon_shared_with_sister():
    # même canon que context-tax : le canon d'un outil se relit
    # identique chez les deux soeurs (test d'ADN de la famille)
    r = k.cost_diff(A_THREE, B_THREE)
    tax = ct.context_tax(B_THREE)
    assert r["totals"]["after"]["chars"] == tax["total_chars"] == 219
    tax_a = ct.context_tax(A_THREE)
    assert r["totals"]["before"]["chars"] == tax_a["total_chars"] == 138


# --------------------------------------------------------------- classes
def test_b1_classes_and_movers_three():
    r = k.cost_diff(A_THREE, B_THREE)
    assert r["classes"] == {"added": 1, "removed": 0, "changed": 1,
                            "unchanged": 1}
    assert [m["name"] for m in r["movers"]] == ["gamma", "alpha"]


def test_b2_added_pct_none_renamed_none_pas_infini():
    r = k.cost_diff(A_THREE, B_THREE)
    g = r["movers"][0]
    assert g["class"] == "ADDED"
    assert g["chars_before"] is None and g["chars_after"] == 73
    assert g["token_estimate_delta"] == 19      # ceil(73/4) = 19
    assert g["pct_of_before"] is None


def test_b3_changed_moved_fields_signes():
    r = k.cost_diff(A_THREE, B_THREE)
    alpha = r["movers"][1]
    assert alpha["class"] == "CHANGED"
    assert alpha["delta_chars"] == 8
    assert alpha["token_estimate_delta"] == 2   # 18 -> 20
    assert alpha["pct_of_before"] == 11.11
    assert alpha["moved_fields"] == {"description": 8}


def test_b4_removed_pct_exact_minus_cent():
    r = k.cost_diff(A_THREE, [B_THREE[0]])
    beta = next(m for m in r["movers"] if m["name"] == "beta")
    assert beta["class"] == "REMOVED"
    assert beta["pct_of_before"] == -100.00
    assert beta["chars_after"] is None
    assert r["totals"]["delta"]["token_estimate"] == -15


def test_b5_same_sort_folding_meme():
    r = k.cost_diff(A_MIN, A_MIN)
    assert r["classes"] == {"added": 0, "removed": 0, "changed": 0,
                            "unchanged": 1}
    assert r["movers"] == []
    assert "NO_CHANGES" in r["flags"]


def test_b6_key_order_is_not_a_bill():
    # canon = clés triées : réordonner un DICT ne facture pas.
    a = [{"name": "n", "description": "d"}]
    b = [{"description": "d", "name": "n"}]
    r = k.cost_diff(a, b)
    assert r["classes"]["unchanged"] == 1
    assert "NO_CHANGES" in r["flags"]


# --------------------------------------------------------------- divergence
def test_c1_global_minus_vs_sum_chiffree():
    r = k.cost_diff(A_THREE, B_THREE)
    assert r["totals"]["delta"]["token_estimate"] == 20
    assert r["totals"]["per_tool_delta_sum"] == 21
    assert "ceil" in r["totals"]["divergence_note"]


def test_c2_divergence_trace_hand():
    # g104 : [a] -> [ab, abc] : 12 -> 27 chars, est 3 -> 7.
    r = k.cost_diff([{"name": "a"}],
                    [{"name": "ab"}, {"name": "abc"}])
    assert r["totals"]["delta"]["token_estimate"] == 4
    assert r["totals"]["per_tool_delta_sum"] == 5
    assert [(m["name"], m["class"], m["delta_chars"])
            for m in r["movers"]] == [("abc", "ADDED", 14),
                                      ("ab", "ADDED", 13),
                                      ("a", "REMOVED", -12)]


def test_c3_growth_pct_reelle():
    # testdino-shape : +78 % — le % se LIT, il n'est pas raconté
    r = k.cost_diff(A_THREE, B_THREE)
    assert r["totals"]["delta"]["pct_of_before"] == 57.14


# --------------------------------------------------------------- ties/fold
def test_d1_tie_name_ascendant():
    r = k.cost_diff(A_TIE, B_TIE)
    assert [m["name"] for m in r["movers"]] == ["aa", "zz"]
    assert r["movers"][0]["delta_chars"] == r["movers"][1]["delta_chars"]


def test_d2_fold_top_100():
    b = [{"name": "t%03d" % i, "description": "x"} for i in range(130)]
    a = [{"name": "t%03d" % i, "description": "xx"} for i in range(130)]
    r = k.cost_diff(b, a)
    assert len(r["movers"]) == 100
    assert r["folded"] == {"tools": 30, "delta_chars": 30,
                           "token_estimate_delta": 0}
    assert sum(m["delta_chars"] for m in r["movers"]) + \
        r["folded"]["delta_chars"] == 130


# --------------------------------------------------------------- window
def test_e1_verdict_par_cote_borne_close():
    r = k.cost_diff(A_MIN, B_MIN, window=3)
    assert r["totals"]["before"]["verdict"] == "FITS"  # est 3 == 3
    assert r["totals"]["after"]["verdict"] == "OVERFLOWS_WINDOW"
    assert r["window"]["transition"] == "FITS_TO_OVERFLOWS"
    assert "WINDOW_TRANSITION" in r["flags"]


def test_e2_transition_shrink_retombe():
    r = k.cost_diff(B_MIN, A_MIN, window=8)
    assert r["window"]["transition"] == "STABLE"
    r2 = k.cost_diff(B_MIN, A_MIN, window=5)
    assert r2["window"]["transition"] == "OVERFLOWS_TO_FITS"


# --------------------------------------------------------------- turns/$
def test_f1_par_tour_et_dollars():
    r = k.cost_diff(A_MIN, B_MIN, turns=10, input_per_mtok="2")
    assert r["per_turn"]["tokens_charged_delta"] == 50
    assert r["price"]["usd_delta_for_this_run"] == "0.000100"


def test_f2_shrink_signe_meme_monnaie():
    r = k.cost_diff(B_MIN, A_MIN, turns=2, input_per_mtok="3")
    assert r["totals"]["delta"]["token_estimate"] == -5
    assert r["per_turn"]["tokens_charged_delta"] == -10
    assert r["price"]["usd_delta_for_this_run"] == "-0.000030"


def test_f3_pas_de_prix_pas_de_dollars():
    r = k.cost_diff(A_MIN, B_MIN)
    assert "price" not in r
    assert r["per_turn"]["turns"] == 1


# --------------------------------------------------------------- flags
def test_g1_disjoint_nomme():
    r = k.cost_diff([{"name": "solo_old"}], [{"name": "solo_new"}])
    assert "DISJOINT_LISTINGS" in r["flags"]
    assert r["classes"] == {"added": 1, "removed": 1, "changed": 0,
                            "unchanged": 0}


def test_g2_les_vides_sont_des_etats():
    r = k.cost_diff([], A_MIN)
    assert "EMPTY_BEFORE" in r["flags"]
    assert r["totals"]["before"]["token_estimate"] == 0
    assert r["totals"]["delta"]["pct_of_before"] is None
    r = k.cost_diff(A_MIN, [])
    assert "EMPTY_AFTER" in r["flags"]
    r = k.cost_diff([], [])
    assert "EMPTY_BOTH" in r["flags"]
    assert r["totals"]["delta"]["token_estimate"] == 0


# --------------------------------------------------------------- refusés
def test_h1_dup_shadowing_par_cote():
    with pytest.raises(k.CostDiffError) as e:
        k.cost_diff([{"name": "a"}, {"name": "a"}], [])
    assert e.value.field == "tools_before[1].name"
    with pytest.raises(k.CostDiffError) as e:
        k.cost_diff([], [{"name": "b"}, {"name": "b"}])
    assert e.value.field == "tools_after[1].name"


def test_h2_noms_vides_et_non_objets_traduits_du_frere():
    with pytest.raises(k.CostDiffError) as e:
        k.cost_diff([{"name": ""}], [])
    assert e.value.field == "tools_before[0].name"
    with pytest.raises(k.CostDiffError) as e:
        k.cost_diff([5], [])
    assert e.value.expected == "a JSON object"


def test_h3_plafond_par_cote():
    with pytest.raises(k.CostDiffError) as e:
        k.cost_diff([{"name": "n%d" % i} for i in range(5001)], [])
    assert e.value.field == "tools_before"


def test_h4_arguments_valides_comme_chez_le_frere():
    for field, kwargs in (("window", {"window": 0}),
                          ("turns", {"turns": 0}),
                          ("input_per_mtok", {"input_per_mtok": "-1"}),
                          ("input_per_mtok", {"input_per_mtok": "abc"})):
        with pytest.raises(k.CostDiffError) as e:
            k.cost_diff(A_MIN, B_MIN, **kwargs)
        assert e.value.field == field


# --------------------------------------------------------------- endpoint
def _post(b):
    return client.post("/api/v1/agent/cost-diff", json=b)


def test_i1_endpoint_shape():
    r = _post({"tools_before": A_THREE, "tools_after": B_THREE})
    assert r.status_code == 200
    j = r.json()
    assert j["model"] == "agent/cost-diff"
    assert j["totals"]["delta"]["token_estimate"] == 20
    assert "sha256" in j


def test_i2_extra_field_refuse():
    r = _post({"tools_before": [], "tools_after": [], "now": "x"})
    assert r.status_code == 400


def test_i3_refus_400_porte_field_expected():
    r = _post({"tools_before": [{"name": "a"}, {"name": "a"}],
               "tools_after": []})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "tools_before[1].name"
    assert "unique" in e["expected"] or "unique" in e["message"]


def test_i4_sayings_et_provenance_voyagent():
    r = _post({"tools_before": A_MIN, "tools_after": B_MIN})
    j = r.json()
    assert len(j["provenance"]) >= 5
    assert "ceil" in j["estimator"]
    assert set(j["transition_values"]) == {"STABLE", "FITS_TO_OVERFLOWS",
                                           "OVERFLOWS_TO_FITS"}


# --------------------------------------------------------------- routeur
def test_j1_aiguilles_costdiff_x3():
    for q in ("what did the mcp update cost my tool list in extra "
              "tokens",
              "quel surcoût de tokens la nouvelle version du serveur "
              "mcp a ajouté à ma liste d'outils",
              "quanto a nova versão do meu servidor mcp custou a mais "
              "em tokens na lista de ferramentas",
              "the update of my mcp server grew the tool list by 13k "
              "tokens — what is the delta per tool"):
        r = client.get("/route", params={"q": q})
        top = r.json()["tools"][0]["tool"]
        assert top == "agent_costdiff", (q, top)


def test_j2_la_soeur_single_listing_garde_son_aiguille():
    r = client.get("/route", params={"q": "combien de tokens coûte la "
                       "liste d'outils de ce serveur MCP à chaque tour"})
    assert r.json()["tools"][0]["tool"] == "agent_contexttax"


def test_j3_le_frere_digest_garde_le_sien():
    # "what changed" sans vocabulaire de PRIX reste chez mcp-surface
    r = client.get("/route", params={"q": "what changed in my MCP "
                       "tool list since the reading I pinned"})
    assert r.json()["tools"][0]["tool"] == "agent_mcpsurface"


def test_j4_leurres_meurent():
    for q in ("combien coûtent 3 pommes à -20 %",
              "blague sur le prix de la nouvelle version de la liste "
              "d'outils",
              "quanto custa enviar uma caixa pelos correios"):
        names = [t["tool"] for t in
                 client.get("/route", params={"q": q}).json()["tools"]]
        assert "agent_costdiff" not in names, q
