# -*- coding: utf-8 -*-
"""Bundle 75 — /agent/modelid gagne le TYPE de variante (XS, lentille
radar). Le radar 06h40 du 23-nov a péché deux MIRAGES portant
« :batch » ; la doc OpenRouter publiée (model-variants/overview,
consultée 23-11) ferme la grammaire : deux CLASSES de suffixes au
comportement catalogue OPPOSÉ —

  catalog  :free (active), :batch (active, Batch API uniquement —
           « the Batch API takes the base slug and resolves the
           :batch entry itself » ; en appel sync direct : « no
           endpoint to route to » = notre mirage V23 expliqué),
           :thinking + :extended (deprecated) ;
  routing  :nitro :floor :exacto :online — « accepted on every
           model ID and NEVER an entry in the models API ».

Un agent qui audite sa config contre GET /models tombe dans le
piège dans les deux sens : « :nitro absent du catalogue » est un
FAUX ALARME, « :batch présent mais mort en sync » est le VRAI.
La table est FERMÉE, sourced, zéro réseau, zéro LM.

Oracles écrits à la MAIN avant l'impl — le champ variant est
ADDITIF : il n'apparaît QUE quand l'id porte un suffixe structurel
unique valide ; échelle de verdicts, ladder, grammar et guarantee
intacts (pins sans suffixe octet pour octet).
"""
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _audit(ids, catalog=None):
    body = {"ids": ids}
    if catalog is not None:
        body["catalog"] = catalog
    r = client.post("/api/v1/agent/modelid", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def _variant(ids, catalog):
    return _audit(ids, catalog)["results"][0].get("variant")


# ---------- la classe catalog ----------

def test_batch_is_catalog_class_batch_api_only():
    v = _variant(["anthropic/claude-sonnet-5.5:batch"],
                 ["anthropic/claude-sonnet-5.5:batch"])
    assert v is not None
    assert v["suffix"] == "batch"
    assert v["class"] == "catalog"
    assert v["status"] == "active"
    # la phrase exacte est du contrat — le V23 mirage y est nommé.
    assert "Batch API" in v["serves"]
    assert "BASE" in v["serves"]


def test_free_is_catalog_class_with_own_entry_warning():
    v = _variant(["deepseek/deepseek-chat-v3:free"],
                 ["deepseek/deepseek-chat-v3"])
    assert v["suffix"] == "free"
    assert v["class"] == "catalog"
    assert v["status"] == "active"
    # la doc interdit le stripping silencieux : « do not strip » est
    # dans le message, verdict VARIANT_DECOR intact à côté.
    assert "strip" in v["serves"]
    r = _audit(["deepseek/deepseek-chat-v3:free"],
               ["deepseek/deepseek-chat-v3"])["results"][0]
    assert r["verdict"] == "VARIANT_DECOR"
    assert r["suggest"] == "deepseek/deepseek-chat-v3"


def test_deprecated_variants_are_named_deprecated():
    for suf in ("thinking", "extended"):
        v = _variant(["meta/llama-4:%s" % suf], ["meta/llama-4"])
        assert v["class"] == "catalog", suf
        assert v["status"] == "deprecated", suf


# ---------- la classe routing ----------

def test_routing_suffix_is_never_a_catalog_entry():
    # :nitro est ABSENT du catalogue — et c'est NORMAL. Sans le TYPE,
    # l'agent corrige un id sain ; avec, la réponse dit lequel des
    # deux pièges il regarde.
    v = _variant(["openai/gpt-5.2:nitro"], ["openai/gpt-5.2"])
    assert v["class"] == "routing"
    assert "never" in v["serves"]
    # le ladder reste VARIANT_DECOR (la base EST au catalogue) :
    r = _audit(["openai/gpt-5.2:nitro"], ["openai/gpt-5.2"])["results"][0]
    assert r["verdict"] == "VARIANT_DECOR"


def test_routing_family_all_four_suffixes():
    for suf in ("nitro", "floor", "exacto", "online"):
        v = _variant(["x/y:%s" % suf], ["x/y"])
        assert v["class"] == "routing", suf


# ---------- la classe unknown ----------

def test_unknown_suffix_refuses_to_guess():
    v = _variant(["x/y:banana"], ["x/y"])
    assert v["class"] == "unknown"
    assert v["suffix"] == "banana"
    assert "guess" in v["serves"]


# ---------- additive : le reste du monde ne bouge pas ----------

def test_no_variant_no_field():
    r = _audit(["openai/gpt-5-mini"], ["openai/gpt-5-mini"])["results"][0]
    assert "variant" not in r
    assert set(r) == {"id", "verdict", "suggest"}


def test_bad_variant_ladder_untouched_and_fieldless():
    # pile (test_bundle68) : deux marqueurs = BAD_VARIANT, pas de
    # champ variant — la structure refuse AVANT de classer.
    r = _audit(["a/b:free:nitro"], ["x/y"])["results"][0]
    assert r["verdict"] == "BAD_VARIANT"
    assert "variant" not in r


def test_hash_marker_classifies_like_colon():
    v = _variant(["meta/llama-3.2#free"], ["meta/llama-3.2"])
    assert v["class"] == "catalog"
    assert v["suffix"] == "free"
    assert v["marker"] == "#"


def test_suffix_case_is_reported_raw_classified_lower():
    v = _variant(["openai/gpt-5.2:NITRO"], ["openai/gpt-5.2"])
    assert v["suffix"] == "NITRO"      # ce que l'appelant a écrit
    assert v["class"] == "routing"     # classé sur la forme publiée


def test_grammar_and_guarantee_strings_unchanged():
    out = _audit(["a/b"], ["a/b"])
    assert out["grammar"] == "org/name[:variant|#variant]"
    assert out["guarantee"].startswith("static form check only")


def test_verdict_scale_closed_list():
    # l'échelle n'a pas gagné d'étage — le TYPE est un champ, pas un
    # verdict. Les VERDICTS publiés du module restent la vérité.
    import modelidkit
    assert "BATCH_ONLY" not in modelidkit.VERDICTS
    assert len(modelidkit.VERDICTS) == 12
