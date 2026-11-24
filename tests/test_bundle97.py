# -*- coding: utf-8 -*-
"""Bundle 97 — /agent/mcp-surface : l'empreinte de surface MCP, puis
la dérive. Golds tracés MAIN + recoupés DEUX ORACLES (openssl/shasum
et hashlib) AVANT l'implémentation, sur des objets canoniques
recopiables octet à octet.

Leçon du tracé : ma première main avait écrit l'oracle de surface
sans les guillemets JSON ([hex] au lieu de ["hex"]) — le module a
dit vrai, l'humain avait tort, la machine a été REVÉRIFIÉE (les deux
oracles d'accord sur les octets corrigés) et le test suit le
canon, jamais l'inverse.

Golds à la main :
  [{"name":"x"}]
    bytes  {"annotations":{"destructiveHint":true,"idempotentHint":
            false,"openWorldHint":true,"readOnlyHint":false,
            "title":null},"description":null,"execution":null,
            "inputSchema":null,"name":"x","outputSchema":null,
            "title":null}
    sha    eebd93db…c3be29
    surface ["eebd93db…"] -> 01167fdd…f855d4
  [{"name":"café","description":"qui ?"}]  -> a2844daa…60330
    (ensure_ascii=False : les octets UTF-8 de café sont HACHÉS,
    pas échappés — le nom est le contrat)
  annotations {"readOnlyHint":true} explicite -> 9019d869…3b01c7
  inconnue « extra » gardée + title/inputSchema -> 4f70b44e…163db
  liste vide : surface = sha256("[]") = 4f53cda1…b945 (le vide EST
  un résultat nommé, la spec dit « MAY be empty »)
  inconnue rug-pull « instructions » -> 2edf9120…a6de00 (CE que
    le client lit entre dans le digest — classe tool-poisoning)
  deux outils ordonnés : [V1,V2] = 98c22447…20dc5a et
    [V2,V1] = bbd2b63f…db4891 — l'ORDRE change le digest de
    surface (spec 2026-07-28 : deterministic order SHOULD, ttlMs/
    cacheScope contractuels) ; le contenu digéré, lui, ne change
    pas — c'est exactement la classe REORDERED.

Verdicts CLOSES : DRIFT > REORDERED > CLEAN ; absent == {} == null
pour annotations ; explicite-égal-défaut == absent (aucune dérive
sémantique à écrire le défaut noir sur blanc).

Le serment de frontière, testé comme chez le frère mcp-audit :
socket et subprocess bouchonnés — zéro fetch, zéro lancement.

Garde d'hygiène NEUVE (douleur trouvée en lisant la vitrine ce
cycle) : deux clés `agent_mcpaudit` collées dans le bloc fr des
PURPOSES de make_landing — la seconde, en PT, écrasait la FR en
silence. Un dict Python à clé dupliquée est un ÉCRASEMENT, pas une
erreur : la garde AST refuse désormais tout doublon de clé dans les
littéraux de make_landing.py.
"""
import ast
import hashlib
import json
import socket
import subprocess

import mcpsurfacekit as k
import main
import pytest
from fastapi.testclient import TestClient

client = TestClient(main.app)

# golds openssl-verified (recopiés AVANT l'impl, revérifiés hashlib)
V1 = ("eebd93db19aaf06ed6166cbf63c34a152da20c71e58af98b60c532"
      "3097c3be29")
V1_SURFACE = ("01167fdde75e7c27312a3317f0f71fbca7486f29c3382bfd2"
              "3dcb71910f855d4")
V2 = ("a2844daab32b84672784f87e68021cd1fa3177edeaa8c6a243b79d4"
      "8d8760330")
V3 = ("9019d869de7575fef9ca637d2a9d7f955b6881360952b5c3ed8cc4d"
      "f443b01c7")
V4 = ("4f70b44e6c80fb2797d08d2877295641e8ef625f0ae1b30345915f3"
      "21b8163db")
EMPTY_SURFACE = ("4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba"
                 "873c2f11161202b945")
INSTRUCTIONS = ("2edf9120ff5736152fd240d904c31208256418ec66d8e83"
                "787281e5c48a6de00")
PAIR_FWD = ("98c2244793594b3053bb9d8bc031f774ce6815d493006da91c"
            "7f9a4cad20dc5a")
PAIR_REV = ("bbd2b63fe4a21e41fddd759649853dfb65384f0a06e2f20a25"
            "7b32a89edb4891")


# ---------------------------------------------------------------- pins main
def test_v1_pin_bytes_are_the_published_object():
    # l'objet canonique est recopiable à la MAIN : le test le
    # réécrit littéralement et le hache par le stdlib, pas par kit
    literal = ('{"annotations":{"destructiveHint":true,"idempotentHi'
               'nt":false,"openWorldHint":true,"readOnlyHint":false,'
               '"title":null},"description":null,"execution":null,'
               '"inputSchema":null,"name":"x","outputSchema":null,'
               '"title":null}')
    assert hashlib.sha256(literal.encode()).hexdigest() == V1
    out = k.mcp_surface([{"name": "x"}])
    assert out["tools"] == [{"name": "x", "sha256": V1}]
    assert out["surface_sha256"] == V1_SURFACE


def test_v2_name_and_description_are_hashed_as_octets():
    out = k.mcp_surface([{"name": "café", "description": "qui ?"}])
    assert out["tools"][0]["sha256"] == V2


def test_v3_explicit_annotation_and_v4_unknown_key_survive():
    assert k.mcp_surface(
        [{"name": "x",
          "annotations": {"readOnlyHint": True}}]
    )["tools"][0]["sha256"] == V3
    assert k.mcp_surface(
        [{"name": "x", "title": "Xy",
          "inputSchema": {"type": "object"},
          "annotations": {"extra": "keep me"}}]
    )["tools"][0]["sha256"] == V4


def test_instructions_key_is_digest_ed_rug_pull_class():
    # un champ INCONNU qui apparaît est un champ lu par le client :
    # la classe « instructions » (tool poisoning) doit bouger le
    # digest — les exclusions sont Nommées, pas inventées
    out = k.mcp_surface([{"name": "x", "instructions": "obey"}])
    assert out["tools"][0]["sha256"] == INSTRUCTIONS
    d = k.mcp_surface([{"name": "x", "instructions": "obey"}],
                      baseline=[{"name": "x"}])
    assert d["verdict"] == "DRIFT"
    assert d["changed"][0]["fields"] == ["instructions"]


def test_empty_listing_is_a_named_result():
    out = k.mcp_surface([])
    assert out["count"] == 0 and out["tools"] == []
    assert out["surface_sha256"] == EMPTY_SURFACE  # sha256("[]")


def test_order_is_part_of_the_surface_digest():
    fwd = k.mcp_surface([{"name": "x"}, {"name": "café",
                          "description": "qui ?"}])
    assert fwd["surface_sha256"] == PAIR_FWD
    rev = k.mcp_surface([{"name": "café", "description": "qui ?"},
                         {"name": "x"}])
    assert rev["surface_sha256"] == PAIR_REV
    # le contenu par outil NE bouge pas : seule la surface porte
    # l'ordre — c'est la classe REORDERED, pas un faux DRIFT
    assert fwd["tools"][0] == rev["tools"][1]


# ---------------------------------------------------------------- normes
def test_annotations_absent_eq_empty_eq_null():
    s = lambda tools: k.mcp_surface(tools)["surface_sha256"]
    assert s([{"name": "x"}]) == s([{"name": "x",
                                     "annotations": {}}])
    assert s([{"name": "x"}]) == s([{"name": "x",
                                     "annotations": None}])


def test_explicit_default_value_is_not_drift():
    # écrire noir sur blanc le défaut public de la spec ne change
    # RIEN au comportement du client : pas de faux DRIFT
    d = k.mcp_surface([{"name": "x",
                        "annotations": {"readOnlyHint": False}}],
                      baseline=[{"name": "x"}])
    assert d["verdict"] == "CLEAN"


def test_hint_flip_is_named_with_from_and_to():
    d = k.mcp_surface([{"name": "x"}],
                      baseline=[{"name": "x",
                                 "annotations":
                                     {"readOnlyHint": True}}])
    assert d["verdict"] == "DRIFT"
    assert d["changed"] == [{
        "name": "x", "fields": ["annotations"],
        "hint_flips": [{"hint": "readOnlyHint",
                        "from": True, "to": False}]}]


def test_destructive_hint_default_is_true_and_visible():
    # le défaut PUBLIC est true : écrire false est un flip, retirer
    # l'annotation ne l'est pas
    d = k.mcp_surface([{"name": "x",
                        "annotations": {"destructiveHint": False}}],
                      baseline=[{"name": "x"}])
    assert d["changed"][0]["hint_flips"] == [
        {"hint": "destructiveHint", "from": True, "to": False}]


# ---------------------------------------------------------------- verdicts
def test_added_removed_counts_and_orders():
    b = [{"name": "z"}, {"name": "a"}, {"name": "m"}]
    t = [{"name": "m"}, {"name": "a"}, {"name": "new"}]
    d = k.mcp_surface(t, baseline=b)
    assert d["verdict"] == "DRIFT"
    assert d["removed"] == ["z"]           # ordre baseline
    assert d["added"] == ["new"]           # ordre listing
    assert d["counts"] == {"added": 1, "changed": 0, "removed": 1,
                           "reordered": 0, "unchanged": 2}


def test_reordered_when_content_is_identical():
    d = k.mcp_surface([{"name": "b"}, {"name": "a"}],
                      baseline=[{"name": "a"}, {"name": "b"}])
    assert d["verdict"] == "REORDERED"
    assert d["reordered"] == ["a", "b"]
    assert d["changed"] == [] and d["added"] == []


def test_drift_outranks_reordered():
    d = k.mcp_surface([{"name": "b"}, {"name": "a",
                                       "description": "x"}],
                      baseline=[{"name": "a"}, {"name": "b"}])
    assert d["verdict"] == "DRIFT"
    assert d["reordered"] == ["b"]
    assert d["changed"][0]["name"] == "a"


# ---------------------------------------------------------------- refus
def _refused(tools=None, baseline=None, field=None):
    kwargs = {}
    if tools is not None:
        kwargs["tools"] = tools
    if baseline is not None:
        kwargs["baseline"] = baseline
    with pytest.raises(k.SurfaceError) as ei:
        k.mcp_surface(**kwargs)
    if field:
        assert ei.value.field == field
    return ei.value


def test_refusals_are_named():
    assert _refused(tools=[{"name": "x"}, {"name": "x"}],
                    field="tools[1].name").message.count("x") >= 1
    assert _refused(tools=[{"nam": "x"}],
                    field="tools[0].name")
    assert _refused(tools=[{"name": ""}], field="tools[0].name")
    assert _refused(tools=[7], field="tools[0]")
    assert _refused(tools=[{"name": "x"}],
                    baseline=[{"name": "y"}, {"name": "y"}],
                    field="baseline[1].name")
    assert _refused(tools=[{"name": "x"}], baseline={"a": 1})


def test_tools_above_ceiling_refused_by_name():
    big = [{"name": "t%d" % i} for i in range(k.MAX_TOOLS + 1)]
    e = _refused(tools=big)
    assert "5000" in e.message and e.field == "tools"


def test_non_object_annotations_are_hashed_not_rejudged():
    # la FORME est le domaine du frère mcp-audit ; ici une
    # annotation string est une DONNÉE visible, elle se digère
    out = k.mcp_surface([{"name": "x", "annotations": "oops"}])
    assert len(out["tools"][0]["sha256"]) == 64


# ---------------------------------------------------------------- HTTP
def test_route_200_and_contract():
    r = client.post("/api/v1/agent/mcp-surface",
                    json={"tools": [{"name": "x"}]})
    assert r.status_code == 200
    body = r.json()
    assert body["surface_sha256"] == V1_SURFACE
    assert "sha256" in body and len(body["sha256"]) == 64
    # déterminisme OCTET : le même appel, deux fois, mêmes octets
    r2 = client.post("/api/v1/agent/mcp-surface",
                     json={"tools": [{"name": "x"}]})
    assert r2.text == r.text


def test_route_rejects_extra_field():
    r = client.post("/api/v1/agent/mcp-surface",
                    json={"tools": [], "soup": 1})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "body.soup"  #
    # la porte unique b93 étiquette body.<champ>


def test_route_400_carries_named_field():
    r = client.post("/api/v1/agent/mcp-surface",
                    json={"tools": [{"name": "a"},
                                    {"name": "a"}]})
    assert r.status_code == 400
    err = r.json()["errors"][0]
    assert err["field"] == "tools[1].name"
    assert "duplicate" in err["message"]


def test_mcp_lists_the_new_tool():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert "agent_mcpsurface" in names


# ---------------------------------------------------------------- serment
def test_no_fetch_no_subprocess(monkeypatch):
    def _boom(*a, **kw):
        raise AssertionError("mcpsurfacekit touched the network")
    monkeypatch.setattr(socket, "socket", _boom)
    monkeypatch.setattr(subprocess, "Popen", _boom)
    k.mcp_surface([{"name": "x"}], baseline=[{"name": "y"}])


# ---------------------------------------------------------------- hygiène
def test_make_landing_has_no_duplicate_dict_keys():
    # douleur trouvée CE cycle : bloc fr des PURPOSES avec DEUX
    # clés agent_mcpaudit — la PT écrasait la FR en silence.
    # ast lit le SOURCE, pas le dict exécuté : le doublon est
    # invisible à l'exécution, visible au parseur.
    src = open("scripts/make_landing.py").read()
    tree = ast.parse(src)
    dupes = []

    class V(ast.NodeVisitor):
        def visit_Dict(self, node):
            seen = set()
            for key in node.keys:
                if isinstance(key, ast.Constant) and \
                        isinstance(key.value, str):
                    if key.value in seen:
                        dupes.append((key.value,
                                      getattr(key, "lineno", "?")))
                    seen.add(key.value)
            self.generic_visit(node)

    V().visit(tree)
    assert dupes == [], "duplicate dict keys in make_landing: %r" % \
        dupes
