# -*- coding: utf-8 -*-
"""bundle68 — /agent/modelid : l'audit statique des ids de modèles.
ORACLES = les vecteurs PUBLIÉS eux-mêmes, attentes tracées à la main
étage par étage de l'échelle fermée, JAMAIS recopiées du module.

Échelle gelée (premier étage qui touche gagne) :
  EXACT > CASE > PUNCT > PREFIX(byte-exact) > NO_ORG(tail byte-exact)
  > VARIANT_DECOR(base EXACT) > NOT_IN_CATALOG(+distance ≤ 3 sur la
  forme normalisée = minuscule sans . _ - ; le slash reste).

Traces main (écrites AVANT l'implémentation) :
  V2  "upstage/solar-pro-4" vs ["upstage/solar-pro4"] (hermes #97654) :
      exact ✗ ; case ✗ ; punct : norm="upstage/solarpro4" des deux
      côtés ✓ → PUNCT_DRIFT, suggest = l'entrée.
  V4  "openrouter/google/gemini-2.5-flash" vs
      ["google/gemini-2.5-flash"] (LiteLLM v1.82.3, everpod) :
      exact/case/punct ✗ ; parts=3 → k=1 suffixe
      "google/gemini-2.5-flash" EXACT dans le cat ✓ → PREFIX_KEPT.
  V6  "openai/gpt-oss-120b" vs ["gpt-oss-120b"] (litellm #14807 Groq) :
      punct ✗ ; parts=2 → tail "gpt-oss-120b" ∈ cat → PREFIX_KEPT.
  V9  "deepseek/deepseek-chat-v3:free" vs
      ["deepseek/deepseek-chat-v3"] (inferenceapis 20-nov) :
      mark=":", base EXACT ∈ cat, full ∉ → VARIANT_DECOR
      (continuumcode : le :free fait PARTIE de l'id).
  V14 "google/gemini-3.7-flsh" vs ["google/gemini-3.7-flash"] :
      norm "google/gemini37flsh" contre "google/gemini37flash" :
      Levenshtein = 1 (un a inséré) ≤ 3 → suggest l'entrée.
  V17 "openrouter/Google/gemini-2.5-Flash" vs
      ["google/gemini-2.5-flash"] (dérive COMPOSÉE) :
      case ✗ (le préfixe reste dans le lower), punct ✗, PREFIX exige
      byte-exact → NOT_IN_CATALOG ; distance des norm = 11
      (« openrouter/ » = 11 caractères) > 3 → suggest None. Le refus
      de composer les règles = le refus de déviner.
  V10 "myalias" vs ["x/y"] (hermes v0.23.1, jamais résolu par PR
      ouvert le 22-nov) : bare, aucune queue, norm "myalias" vs "xy"
      = 6 > 3 → NOT_IN_CATALOG sans suggestion — l'audit est honnête,
      il ne RÉSOUT pas les alias, il dit qu'ils ne sont pas dans
      l'annuaire collé.
  V7  "gpt-5-mini" vs ["openai/gpt-5-mini"] (n8n #39227 : le runtime
      COUPE le préfixe — miroir de #14807) : bare, queue
      "gpt-5-mini" == base → NO_ORG, suggest "openai/gpt-5-mini".
  V11 (mirage V23 chez nous) : catalog ["anthropic/claude-sonnet-
      5.5:batch"], même id → OK — et le champ guarantee EST présent :
      OK ne jure jamais le GET. C'est la promesse, écrite dans la
      réponse, pas dans le README.
"""
import json


def _client():
    from fastapi.testclient import TestClient
    import main
    main.RATE_LIMIT = 10**9
    return TestClient(main.app)


def _audit(ids, catalog=None):
    body = {"ids": ids}
    if catalog is not None:
        body["catalog"] = catalog
    c = _client()
    r = c.post("/api/v1/agent/modelid", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def _verdict(ids, catalog, i=0):
    out = _audit(ids, catalog)
    res = out["results"][i]
    return res["verdict"], res["suggest"]


# ------------------------------------------------------- published vectors

def test_v1_litellm_37271_listed_is_form_ok():
    # Le gateway liste l'id AVEC SLASH et le GET 404 : notre audit dit
    # la FORME — la liste des causes de #37271 inclut le PATH du
    # gateway, pas l'id. OK est le verdict honnête, guarantee le dit.
    assert _verdict(["mistralai/mistral-7b-instruct"],
                    ["mistralai/mistral-7b-instruct"]) == ("OK", None)


def test_v2_hermes_solar_punct_drift():
    assert _verdict(["upstage/solar-pro-4"],
                    ["upstage/solar-pro4"]) == (
        "PUNCT_DRIFT", "upstage/solar-pro4")


def test_v3_everpod_qwen_one_dash_404():
    # Test live publié 22-nov : qwen3.6-27b → 200, qwen-3.6-27b → 404.
    assert _verdict(["qwen/qwen-3.6-27b"], ["qwen/qwen3.6-27b"]) == (
        "PUNCT_DRIFT", "qwen/qwen3.6-27b")
    assert _verdict(["qwen/qwen3.6-27b"], ["qwen/qwen3.6-27b"]) == (
        "OK", None)


def test_v4_litellm_prefix_kept_openrouter():
    assert _verdict(["openrouter/google/gemini-2.5-flash"],
                    ["google/gemini-2.5-flash"]) == (
        "PREFIX_KEPT", "google/gemini-2.5-flash")


def test_v5_hf_patchmodels_double_prefix():
    assert _verdict(["openai/deepseek/deepseek-v4-flash"],
                    ["deepseek/deepseek-v4-flash"]) == (
        "PREFIX_KEPT", "deepseek/deepseek-v4-flash")


def test_v6_litellm_14807_groq_stripped_target():
    # Groq route sur « gpt-oss-120b » nu ; l'id LiteLLM arrive entier.
    assert _verdict(["openai/gpt-oss-120b"], ["gpt-oss-120b"]) == (
        "PREFIX_KEPT", "gpt-oss-120b")


def test_v7_n8n_39227_bare_suffix_no_org():
    # Miroir de V6 : le runtime a COUPÉ le préfixe, le gateway route
    # sur la chaîne complète. La correction demandée par continuumcode
    # « add the prefix » devient un verdict NOMMÉ avec la cible.
    assert _verdict(["gpt-5-mini"], ["openai/gpt-5-mini"]) == (
        "NO_ORG", "openai/gpt-5-mini")


def test_v8_hf_case_drift():
    assert _verdict(["deepseek-ai/DeepSeek-V4-Flash:deepinfra"],
                    ["deepseek-ai/deepseek-v4-flash:deepinfra"]) == (
        "CASE_DRIFT", "deepseek-ai/deepseek-v4-flash:deepinfra")


def test_v9_inferenceapis_retired_free_variant():
    # « deepseek-chat-v3:free » retiré, la base vit : le :free est
    # PARTIE de l'identifiant (continuumcode), pas un chapeau.
    assert _verdict(["deepseek/deepseek-chat-v3:free"],
                    ["deepseek/deepseek-chat-v3"]) == (
        "VARIANT_DECOR", "deepseek/deepseek-chat-v3")


def test_v10_hermes_alias_literal_not_in_catalog():
    # v0.23.1 : l'alias part LITTÉRAL, 400 « myalias is not a valid
    # model ID », le fix est un PR encore OUVERT le 22-nov. Notre
    # audit ne résout pas les alias : il dit qu'ils ne sont PAS dans
    # l'annuaire collé, sans near-miss inventé.
    assert _verdict(["myalias"], ["x/y"]) == ("NOT_IN_CATALOG", None)


def test_v11_v23_mirage_ok_is_form_only():
    # L'incident V23 CHEZ NOUS : l'annuaire listait
    # claude-sonnet-5.5:batch et le GET 404ait. L'audit statique dit
    # OK (forme + annuaire collé) — et la garantie est DANS la
    # réponse, pas dans la prose : jamais l'audit ne jure l'appel.
    out = _audit(["anthropic/claude-sonnet-5.5:batch"],
                 ["anthropic/claude-sonnet-5.5:batch"])
    assert out["results"][0]["verdict"] == "OK"
    assert "never the GET" in out["guarantee"]
    assert out["grammar"] == "org/name[:variant|#variant]"


def test_v12_display_name_has_space():
    # everpod : « spaces » et « display names » sont des causes
    # directes du 400. Jamais d'espace dans un id d'API.
    assert _verdict(["Claude Opus 4"], ["x/y"]) == ("HAS_SPACE", None)


def test_v13_structural_codes_closed():
    assert _verdict(["a//b"], ["x/y"]) == ("BAD_SLASH", None)
    assert _verdict(["/b"], ["x/y"]) == ("BAD_SLASH", None)
    assert _verdict(["b/"], ["x/y"]) == ("BAD_SLASH", None)
    assert _verdict(["a/b:"], ["x/y"]) == ("BAD_VARIANT", None)
    assert _verdict(["a/b#"], ["x/y"]) == ("BAD_VARIANT", None)
    assert _verdict(["a/b:free:nitro"], ["x/y"]) == ("BAD_VARIANT", None)
    assert _verdict(["a/b#x:y"], ["x/y"]) == ("BAD_VARIANT", None)
    assert _verdict(["a/b@c"], ["x/y"]) == ("BAD_CHAR", None)
    assert _verdict([""], ["x/y"]) == ("EMPTY", None)


def test_v14_suggest_named_distance_1():
    # sie #939 : « Did you mean …? » — ici avec le seuil NOMMÉ, pas
    # un heuristique muet. Claude Code fait pareil et l'écrit.
    assert _verdict(["google/gemini-3.7-flsh"],
                    ["google/gemini-3.7-flash"]) == (
        "NOT_IN_CATALOG", "google/gemini-3.7-flash")


def test_v15_grammar_only_without_catalog():
    out = _audit(["gpt-5.6-sol", "mistralai/mistral-7b-instruct"])
    assert out["catalog_mode"] is False
    assert [r["verdict"] for r in out["results"]] == ["OK", "OK"]
    assert out["catalog_size"] == 0


def test_v16_exact_beats_lecture():
    # Un id EXACT dans l'annuaire gagne toujours : le LiteLLM name
    # complet EST annuairé par certains gateways — pas de leçon.
    assert _verdict(["mistralai/mistral-7b-instruct"],
                    ["mistralai/mistral-7b-instruct",
                     "mistral-7b-instruct"]) == ("OK", None)


def test_v17_composite_drift_refuses_to_guess():
    # préfixe + casse : les étages sont byte-exacts chacun ; composer
    # serait déviner. NOT_IN_CATALOG, distance 11 > 3, pas de
    # suggestion — le nommage exact de la cible est le ping du radar,
    # pas la grammaire.
    assert _verdict(["openrouter/Google/gemini-2.5-Flash"],
                    ["google/gemini-2.5-flash"]) == (
        "NOT_IN_CATALOG", None)


# ------------------------------------------------------------- the wire

def test_counts_and_order_input_echoed():
    out = _audit(["mistralai/mistral-7b-instruct", "upstage/solar-pro-4",
                  "Claude Opus 4"],
                 ["mistralai/mistral-7b-instruct", "upstage/solar-pro4"])
    assert out["counts"] == {"total": 3, "ok": 1, "flagged": 2}
    assert [r["id"] for r in out["results"]] == [
        "mistralai/mistral-7b-instruct", "upstage/solar-pro-4",
        "Claude Opus 4"]


def test_determinism_same_bytes_twice():
    c = _client()
    body = {"ids": ["openrouter/google/gemini-2.5-flash"],
            "catalog": ["google/gemini-2.5-flash"]}
    r1 = c.post("/api/v1/agent/modelid", json=body)
    r2 = c.post("/api/v1/agent/modelid", json=body)
    assert r1.content == r2.content
    assert r1.json()["sha256"]


def test_openclaw_45294_runtime_only_failure_naming():
    # « google/gemini-3.0-flash » accepté au config, mort à
    # l'inférence ; le correct « google/gemini-3-flash-preview ».
    # norm : "google/gemini30flash" contre
    # "google/gemini3flashpreview" — distance ? trace main :
    # il faut remplacer «0» → position… le seuil 3 tranche : AUCUNE
    # suggestion si > 3, NOT_IN_CATALOG quand même — le verdict nomme
    # l'absence, la doc fournie par l'issue n'est pas dans notre
    # contrat (pas d'annuaire Google embarqué : doctrine V23).
    assert _verdict(["google/gemini-3.0-flash"],
                    ["google/gemini-3-flash-preview"])[0] == \
        "NOT_IN_CATALOG"


# -------------------------------------------------------- named refusals

def test_400_names_the_field():
    c = _client()
    r = c.post("/api/v1/agent/modelid", json={"catalog": ["x/y"]})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "ids"
    r = c.post("/api/v1/agent/modelid", json={"ids": []})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "ids"
    r = c.post("/api/v1/agent/modelid", json={"ids": ["x/y"],
                                              "catalog": []})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "catalog"
    r = c.post("/api/v1/agent/modelid", json={"ids": [42]})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "ids[0]"
    r = c.post("/api/v1/agent/modelid", json={"ids": ["x/y"],
                                              "catalog": [None]})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "catalog[0]"


def test_400_caps_are_named():
    c = _client()
    r = c.post("/api/v1/agent/modelid", json={"ids": ["a/b"] * 201})
    assert r.status_code == 400
    assert "200" in r.json()["errors"][0]["expected"]
    r = c.post("/api/v1/agent/modelid", json={"ids": ["x" * 201]})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "ids[0]"


# --------------------------------------------------------- route & MCP

def test_route_top1_three_languages():
    c = _client()
    qs = [
        "my agent fails with model not found 404 invalid model id, is "
        "this a litellm or openrouter prefix problem, what is the "
        "correct slug",
        "mon agent meurt en 404 model not found, l'id du model est "
        "sûrement pas dans l'annuaire, problème de préfixe litellm "
        "openrouter, c'est quoi le bon slug",
        "meu agente falha com 404 model not found, o id do modelo não "
        "está no catálogo, problema de prefixo litellm openrouter, "
        "qual é o slug certo",
    ]
    for q in qs:
        r = c.get("/route", params={"q": q})
        top = r.json()["tools"][0]["tool"]
        assert top == "agent_modelid", (q, top)


def test_mcp_tool_call_returns_the_ladder():
    c = _client()
    r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 2,
                             "method": "tools/call",
                             "params": {
                                 "name": "agent_modelid",
                                 "arguments": {
                                     "ids": ["openrouter/google/"
                                             "gemini-2.5-flash"],
                                     "catalog": ["google/gemini-2.5-"
                                                 "flash"]}}})
    text = r.json()["result"]["content"][0]["text"]
    out = json.loads(text)
    payload = out["output"] if "output" in out else out
    assert payload["results"][0]["verdict"] == "PREFIX_KEPT"
