# -*- coding: utf-8 -*-
"""bundle109 — /agent/modelid Dialectes & Portes + veto DROIT-FENÊTRE.

ORACLE TRACÉ À LA MAIN (25-nov, avant l'implémentation), source des
règles : docs OpenRouter rejoués ce cycle —
  batch-quickstart : endpoints batch = /v1/chat/completions,
    /v1/responses, /v1/messages, /v1/embeddings ; « A model with no
    batch variant returns 400 » ; « Embeddings batches do not accept
    provider » ; nested input via Batch = 400.
  guides/features/batch-api (Limitations) : « Image or audio output
    — use the sync API. Batch returns text and embeddings only. »
  guides/routing/model-variants : « The Batch API takes the BASE
    model slug and resolves the :batch entry itself. »
  image-generation guide : flux, seedream, gpt-image vivent derrière
    l'Image API dédiée, pas derrière /v1/chat/completions.
  embeddings guide : example id « openai/text-embedding-3-small »,
    « google/gemini-embedding-2-preview » — le token EMBEDDING est
    dans le NOM, c'est de là que la grammaire peut le lire.

Traces main :
  D1 « anthropic/claude-sonnet-5.5:batch » (catalogue = même id) :
     EXACT → OK. Tokens du nom = {claude, sonnet, 5, 5} → contenu
     CHAT ; suffixe :batch → le champ dialect EST émis : porte sync
     = le SLUG DE BASE (règle publiée), porte batch existe (clash
     False). C'est le mirage V23 nommé enfin par la grammaire.
  D2 « google/gemini-embedding-001:batch » : OK ; tokens {gemini,
     embedding, 001} → contenu EMBEDDING ; batch existe (/v1/
     embeddings est un endpoint batch publié) MAIS restrictions
     nommées : provider refusé, nested input 400. clash False —
     contrairement à l'hypothèse initiale de la file, corrigée par
     le gate : un embedding n'EST PAS incompatible avec batch.
  D3 « black-forest-labs/flux.2-pro:batch » : OK ; tokens {flux, 2,
     pro} → contenu IMAGE ; « Batch returns text and embeddings
     only » → PORTE BATCH ABSENTE, clash TRUE. Le :batch sur du
     flux est le piège V23 sous sa seconde forme : une entrée de
     catalogue sans porte.
  D4 « openai/gpt-4o-mini » sans suffixe : OK et RIEN DE NEUF —
     pas de champ dialect (chat sans :batch = la vie d'avant, octet
     pour octet ; c'est la promesse adds-only du bundle).
  D5 « sentence-transformers/all-minilm-l6-v2 » sans suffixe :
     tokens {all, minilm, l6, v2} — minilm N'EST PAS dans la table
     fermée (seuls les ids rejoués y entrent) → contenu CHAT par
     défaut, dialect ABSENT. La grammaire ne dévin pas les familles
     qu'elle n'a pas lues : silence, pas mensonge. (Leçon b81 à
     l'envers : ajouter « minilm » pour faire plaisir à un scan
     serait coder de mémoire l'écosystème sentence-transformers.)
  D6 « deepseek/deepseek-chat-v3:free » : VARIANT_DECOR inchangé et
     AUCUN dialect — :free n'est pas :batch, deepseek est chat. La
     pin b68 de cet id reste octet pour octet.
  D7 « openai/gpt-5.2:nitro » : routing variant, pas de dialect
     (nitro ne déplace pas la porte du contenu). Pins intactes.
  D8 « openrouter/Google/gemini-2.5-Flash » dérive COMPOSÉE (b68
     gelait NOT_IN_CATALOG sans suggest) : verdict inchangé ET
     dialect absent (gemini/flash = chat). L'échelle ne recompose
     pas pour un champ de plus.
  D9 priorité Nommée embedding avant image : « google/multimodal-
     embedding-001 » — tokens contiennent les DEUX ; la priorité
     publiée dans la table tranche : EMBEDDING (c'est un embedding
     qui AVALE des images, pas une sortie image). sync = /v1/
     embeddings ; batch accepté avec les mêmes restrictions que D2.
  D10 badge : tout résultat porteur de dialect porte le badge
     listed_not_invocable (texte publié ci-dessous, verbatim de la
     these V23) — et SEULEMENT ceux-là (D4/D5/D6/D7/D8 sans badge).
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import modelidkit  # noqa: E402
import routing  # noqa: E402

BADGE = ("listed in the catalog, NOT proven invocable — the batch "
         "door is /api/v1/batch (24h window, base slug), never a "
         "sync chat call on the :batch id")


def audit(ids, catalog=None):
    args = {"ids": ids}
    if catalog is not None:
        args["catalog"] = catalog
    return modelidkit.run_modelid(args)


def entry(out, i=0):
    return out["results"][i]


class TestDialectDoors(unittest.TestCase):
    def test_d1_chat_batch_sync_door_is_base_slug(self):
        out = audit(["anthropic/claude-sonnet-5.5:batch"],
                    ["anthropic/claude-sonnet-5.5:batch"])
        e = entry(out)
        self.assertEqual(e["verdict"], "OK")
        d = e["dialect"]
        self.assertEqual(d["content"], "chat")
        self.assertIn("BASE slug", d["sync"])
        self.assertIn("24h", d["batch"])
        self.assertFalse(d["clash"])
        self.assertEqual(e["badge"], BADGE)

    def test_d2_embedding_batch_accepted_with_named_restrictions(self):
        out = audit(["google/gemini-embedding-001:batch"],
                    ["google/gemini-embedding-001:batch"])
        d = entry(out)["dialect"]
        self.assertEqual(d["content"], "embedding")
        self.assertIn("/v1/embeddings", d["sync"])
        self.assertFalse(d["clash"])  # la file disait True ; le gate dit non
        self.assertIn("/v1/embeddings", d["batch"])
        self.assertIn("provider", d["batch"])
        self.assertIn("nested", d["batch"].lower())
        self.assertIn("400", d["batch"])

    def test_d3_image_batch_clash(self):
        out = audit(["black-forest-labs/flux.2-pro:batch"],
                    ["black-forest-labs/flux.2-pro:batch"])
        d = entry(out)["dialect"]
        self.assertEqual(d["content"], "image")
        self.assertTrue(d["clash"])
        self.assertIn("CLASH", d["batch"])
        self.assertIn("text and embeddings only", d["batch"])

    def test_d4_chat_no_suffix_untouched(self):
        out = audit(["openai/gpt-4o-mini"], ["openai/gpt-4o-mini"])
        e = entry(out)
        self.assertEqual(e["verdict"], "OK")
        self.assertNotIn("dialect", e)
        self.assertNotIn("badge", e)

    def test_d5_minilm_family_not_claimed(self):
        out = audit(["sentence-transformers/all-minilm-l6-v2"],
                    ["sentence-transformers/all-minilm-l6-v2"])
        e = entry(out)
        self.assertNotIn("dialect", e)
        self.assertNotIn("badge", e)

    def test_d6_free_is_not_a_door(self):
        out = audit(["deepseek/deepseek-chat-v3:free"],
                    ["deepseek/deepseek-chat-v3"])
        e = entry(out)
        self.assertEqual(e["verdict"], "VARIANT_DECOR")
        self.assertNotIn("dialect", e)

    def test_d7_routing_variant_is_not_a_door(self):
        out = audit(["openai/gpt-5.2:nitro"], ["openai/gpt-5.2"])
        e = entry(out)
        self.assertNotIn("dialect", e)
        self.assertEqual(e["variant"]["class"], "routing")

    def test_d8_composed_drift_still_refuses(self):
        out = audit(["openrouter/Google/gemini-2.5-Flash"],
                    ["google/gemini-2.5-flash"])
        e = entry(out)
        self.assertEqual(e["verdict"], "NOT_IN_CATALOG")
        self.assertIsNone(e["suggest"])
        self.assertNotIn("dialect", e)

    def test_d9_embedding_beats_image_by_named_priority(self):
        out = audit(["google/multimodal-embedding-1"],
                    ["google/multimodal-embedding-1"])
        d = entry(out)["dialect"]
        self.assertEqual(d["content"], "embedding")

    def test_d10_badge_rides_only_with_dialect(self):
        out = audit(["openai/gpt-4o-mini",
                     "anthropic/claude-sonnet-5.5:batch"],
                    ["openai/gpt-4o-mini",
                     "anthropic/claude-sonnet-5.5:batch"])
        self.assertNotIn("badge", entry(out, 0))
        self.assertEqual(entry(out, 1)["badge"], BADGE)


class TestLadderUntouched(unittest.TestCase):
    """L'échelle b68 ne recompose pas pour le champ neuf."""

    def test_punct_drift_beats_dialect(self):
        out = audit(["upstage/solar-pro-4"], ["upstage/solar-pro4"])
        e = entry(out)
        self.assertEqual(e["verdict"], "PUNCT_DRIFT")
        self.assertEqual(e["suggest"], "upstage/solar-pro4")
        self.assertNotIn("dialect", e)

    def test_embedding_punct_drift_keeps_both(self):
        out = audit(["text-embedding-3-small"],
                    ["text-embedding-3-small"])
        e = entry(out)
        self.assertEqual(e["verdict"], "OK")
        self.assertEqual(e["dialect"]["content"], "embedding")


class TestGrammarInput(unittest.TestCase):
    def test_dialect_uses_name_segment_not_org(self):
        # « bytedance-seed » contient seed, pas seedream — le NOM
        # segment tranche : seedream-4.5 → image.
        out = audit(["bytedance-seed/seedream-4.5"],
                    ["bytedance-seed/seedream-4.5"])
        self.assertEqual(entry(out)["dialect"]["content"], "image")

    def test_uppercase_suffix_still_batch(self):
        out = audit(["x/y:BATCH"], ["x/y:BATCH"])
        d = entry(out)["dialect"]
        self.assertIn("24h", d["batch"])


class TestVetoDroitFenetre(unittest.TestCase):
    """Radar 06h13/07h44 : deux leurres routaient des tables
    étrangères. Un leurre qui route = une promesse fausse."""

    def test_bresil_tue_la_fenetre_us(self):
        for r in routing.route("retour brésil 7 jours "
                               "arrependimento prazo", top=5):
            self.assertNotIn(r["tool"], ("shop_return_deadline",
                                         "shop_withdrawal"))

    def test_allemagne_tue_shipping_us(self):
        for r in routing.route("withdrawal germany online order "
                               "deadline", top=5):
            self.assertNotIn(r["tool"],
                             ("shop_shipping_deadline", "shop_withdrawal"))

    def test_walmart_us_survit(self):
        tools = [r["tool"] for r in
                 routing.route("walmart return deadline january 31",
                               top=5)]
        self.assertIn("shop_return_deadline", tools)

    def test_indiana_ne_tue_rien(self):
        # Indiana est un État US : « india » ne vote que comme MOT
        # EXACT, jamais comme racine (le piège des toponymes).
        out = routing.route("walmart return indiana receipt", top=5)
        self.assertIn("shop_return_deadline", [r["tool"] for r in out])

    def test_batch_ne_vole_plus_json_map(self):
        tools = [r["tool"] for r in
                 routing.route("map every item of an array batch "
                               "style", top=5)]
        self.assertIn("json_map", tools)

    def test_dialect_aiguilles_x3_langues(self):
        for q, want in (
            ("model id not found 404 batch litellm", "agent_modelid"),
            ("embedding model returns error in chat gateway",
             "agent_modelid"),
            ("id modelo introuvable 404 batch openrouter",
             "agent_modelid"),
            ("modelo listado retorna erro no chat embeddings gateway",
             "agent_modelid"),
        ):
            tools = [r["tool"] for r in routing.route(q, top=3)]
            self.assertEqual(tools[0], want, (q, tools))


if __name__ == "__main__":
    unittest.main()
