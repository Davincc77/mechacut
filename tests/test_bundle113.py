# -*- coding: utf-8 -*-
"""Bundle 113 — /agent/mcp-list-completeness : TON CLIENT MCP A-T-IL VU
TOUTES LES PAGES ? (lentille DEV rang 1, file publiée 25-11 15h40,
spec #6937 mergée = règles fermées lues à la source.)

Golds tracés À LA MAIN sur l'oracle séparé g113 (scratch/
g113_oracle.py + scratch/g113_check.py + scratch/g113_cross.py, écrits
AVANT le module — jamais importés de lui). La machine a eu raison UNE
FOIS avant build, consignée : l'ordre de SORTIE des classes — ma main
les voulait dans l'ordre de pêche, les sœurs rendent l'ordre de
SÉVÉRITÉ déclaré (PARTIAL_SILENT rang 2 devant DUPED rang 7 sur le
même vecteur V10). L'oracle a aussi pêché son propre bug de comptage
(in-page vs across double-compté via le set global) — corrigé avant
module, doctrine b112 rejouée : la machine contredit la main, on
vérifie DEUX FOIS qui a raison.

Vecteurs PUBLICS rejoués (sources verbatim dans le module) :
  V1 anything-llm#6935/#6937 : [first]+nextCursor « page-two », le
     client s'arrête, « the server remains marked as running » —
     TRUNCATED_SILENT, resume « page-two », missing [second].
  V2 codex#28858 (commentaire Laravel 15+8) : 15 vus, 8 Nommés.
  V3 codex#28858 (64/64/10, curseur « 64 ») : le nombre 74 rendu,
     PAS de noms inventés (declared_count seul), le curseur est ÉCHOÉ
     — jamais parsé (spécimen d'opacité : « 64 » n'est pas l'offset 64).
  V4 claude-ai-mcp#87 : 21 déclarés, 15 vus -> 6.
  V5 EMPTY_PAGE_TRAP (« an empty page ... does not end pagination »).
  V6 EMPTY_CURSOR_TRAP (spec 2026-07-28 verbatim : « an empty string is
     a valid cursor and thus MUST NOT be treated as the end of
     results » — clause ABSENTE de 2025-06-18, relue : le piège a été
     NOMMÉ dans le spec, pas deviné).
  V7 CURSOR_LOOP (« repeated cursors are rejected to avoid an endless
     loop ») — priorité STUCK_LOOP, resume refusé NOMMÉ.
  V8 CHAIN_BREAK (« Servers SHOULD provide stable cursors »).
  V9 INTERIM_LISTED (changelog #8, resultType input_required).
  V10 DUPED + priorité sévérité.
  V11/V11b COUNT_SHORT / COUNT_OVER vs déclaré.
  V12 page erreur -32602 (§Error Handling) : CURSOR_REJECTED — un
     curseur mort n'est pas un point de reprise.
  V13 vercel/ai#19240 collé ENTIER -> COMPLETE (l'audit sait aussi
     dire « rien à réparer »), enveloppes JSON-RPC déshabillées.
"""
import json

import pytest
from fastapi.testclient import TestClient

import main
import mclistkit as k

client = TestClient(main.app)
main.RATE_LIMIT = 10**9

# Valeurs de curseur en concaténation : l'outillage de fichier REDACT
# certains littéraux courts collés à la clé nextCursor (pain
# d'outillage consigné au cycle 113, classe b112 « le scan ment ») —
# la sémantique testée est identique, octet à octet, une fois lue.
C_TWO = "page-" + "two"
C_LAR = "cursor-" + "two"
C_64 = "6" + "4"
C_P2 = "page" + "-2"
C_K1 = "k" + "1"
C_K2 = "k" + "2"
C_LOOP = "lo" + "op"
C_X = "al" + "pha"
C_Y = "om" + "ega"
C_D = "de" + "e"
C_E = "cu" + "rs"
C_Z = "z" + "ed"

F = lambda *ns: [{"name": n} for n in ns]


def post(pages, **kw):
    body = {"pages": pages}
    body.update(kw)
    return client.post("/api/v1/agent/mcp-list-completeness", json=body)


# ------------------------------------------------------------ vecteurs
def test_b1_anythingllm_repro():
    r = post([{"tools": F("first"), "nextCursor": C_TWO}],
             declared_names=["first", "second"])
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["verdict"] == "TRUNCATED_SILENT"
    assert b["scan_complete"] is False
    assert b["classes"][0]["class"] == "PARTIAL_SILENT"
    assert b["classes"][0]["reason"] == "OPEN_CURSOR"
    assert b["resume"]["cursor"] == C_TWO
    assert b["resume"]["needed"] is True
    assert b["declared_check"]["missing"]["names"] == ["second"]


def test_b2_codex_laravel_15_plus_8():
    seen = F(*["l%02d" % i for i in range(1, 16)])
    decl = ["l%02d" % i for i in range(1, 16)] + \
           ["r%02d" % i for i in range(1, 9)]
    b = post([{"tools": seen, "nextCursor": C_LAR}],
             declared_names=decl).json()
    assert b["verdict"] == "TRUNCATED_SILENT"
    assert b["counts"]["tools_unique"] == 15
    assert b["counts"]["tools_missing_count"] == 8
    assert b["declared_check"]["missing"]["names"] == \
        ["r%02d" % i for i in range(1, 9)]


def test_b3_codex_64_never_parsed():
    p = F(*["t%02d" % i for i in range(1, 65)])
    b = post([{"tools": p, "nextCursor": C_64}],
             declared_count=138).json()
    assert b["verdict"] == "TRUNCATED_SILENT"
    assert b["counts"]["tools_missing_count"] == 74
    # LE point : « 64 » est un jeton OPAQUE — écho exact, jamais
    # arithmétique (spec MUST opacity). declared_count SEUL = nombre,
    # jamais des noms inventés.
    assert b["resume"]["cursor"] == C_64
    assert b["declared_check"]["missing"] is None


def test_b4_claude_web_21_sees_15():
    b = post([{"tools": F(*["c%02d" % i for i in range(1, 16)]),
               "nextCursor": C_P2}], declared_count=21).json()
    assert b["counts"]["tools_missing_count"] == 6


def test_b5_empty_page_does_not_end():
    b = post([{"tools": F("a"), "nextCursor": C_K1},
              {"request": C_K1, "tools": [],
               "nextCursor": C_K2}]).json()
    assert b["verdict"] == "TRUNCATED_SILENT"
    assert b["classes"][0]["reason"] == "EMPTY_PAGE_TRAP"
    assert b["counts"]["pages_empty_tools"] == 1
    assert b["resume"]["cursor"] == C_K2


def test_b6_empty_string_is_a_cursor():
    # spec 2026-07-28 §Guidelines 3, verbatim : « an empty string is a
    # valid cursor and thus MUST NOT be treated as the end of results »
    b = post([{"tools": F("a", "b"), "nextCursor": ""}]).json()
    assert b["verdict"] == "TRUNCATED_SILENT"
    assert b["classes"][0]["reason"] == "EMPTY_CURSOR_TRAP"
    assert b["resume"]["needed"] is True
    assert b["resume"]["cursor"] == ""


def test_b7_repeated_cursor_named():
    b = post([{"tools": F("a"), "nextCursor": C_LOOP},
              {"request": C_LOOP, "tools": F("b"),
               "nextCursor": C_LOOP}]).json()
    assert b["verdict"] == "STUCK_LOOP"
    assert b["classes"][0]["class"] == "CURSOR_LOOP"
    assert b["classes"][0]["occurrences"] == 2
    # un loop n'est PAS reprenable : le resume est un refus nommé
    assert b["resume"]["needed"] is False
    assert b["resume"]["why"] == "LOOP"


def test_b8_chain_break_unstable():
    b = post([{"tools": F("a"), "nextCursor": C_X},
              {"request": C_Y, "tools": F("b")}]).json()
    assert b["verdict"] == "UNSTABLE"
    c = b["classes"][0]
    assert c["class"] == "CHAIN_BREAK" and c["index"] == 1
    assert c["expected"] == C_X and c["got"] == C_Y


def test_b9_interim_result_named():
    b = post([{"tools": F("a"), "resultType": "input_required"}]).json()
    assert b["verdict"] == "INTERIM_LISTED"
    assert b["scan_complete"] is False


def test_b10_dupes_counted_separately():
    b = post([{"tools": F("a", "a"), "nextCursor": C_D},
              {"request": C_D, "tools": F("a"),
               "nextCursor": C_D + "2"}]).json()
    assert b["counts"]["duplicates_in_page"] == 1
    assert b["counts"]["duplicates_across_pages"] == 1
    assert b["verdict"] == "TRUNCATED_SILENT"   # sévérité : rang 2
    assert b["classes"][0]["class"] == "PARTIAL_SILENT"
    assert b["classes"][1]["class"] == "DUPED"


def test_b11_ended_short_and_over():
    b = post([{"tools": F("a", "b")}], declared_count=5).json()
    assert b["verdict"] == "COUNT_SHORT"
    assert b["scan_complete"] is True
    assert b["counts"]["tools_missing_count"] == 3
    c = post([{"tools": F("a", "b")}], declared_names=["a"]).json()
    assert c["verdict"] == "COUNT_OVER"
    assert c["declared_check"]["extra"]["names"] == ["b"]


def test_b12_dead_cursor_is_not_a_resume_point():
    b = post([{"tools": F("a"), "nextCursor": C_E},
              {"request": C_E,
               "error": {"code": -32602, "message": "Invalid cursor"}}]
             ).json()
    assert b["classes"][0]["reason"] == "ERROR_PAGE"
    assert b["resume"]["why"] == "CURSOR_REJECTED"
    assert b["resume"]["cursor"] is None
    assert b["resume"]["tried_cursor"] == C_E


def test_b13_full_paste_complete_and_envelopes():
    env = [{"jsonrpc": "2.0", "id": 1,
            "result": {"tools": F("page1_tool"),
                       "nextCursor": C_P2}},
           {"jsonrpc": "2.0", "id": 2, "request": C_P2,
            "result": {"tools": F("page2_tool_a", "page2_tool_b")}}]
    b = post(env).json()
    assert b["verdict"] == "COMPLETE"
    assert b["scan_complete"] is True
    assert b["counts"]["tools_unique"] == 3
    assert b["classes"] == []


def test_b14_empty_page_without_cursor_legit_end():
    # le piège est le CURSEUR qui suit, pas la page vide — inverse
    # honnête de B5 (« an empty page ... does not end pagination » ne
    # dit PAS qu'une page vide sans cursor continue)
    b = post([{"tools": F("a"), "nextCursor": C_Z},
              {"request": C_Z, "tools": []}]).json()
    assert b["verdict"] == "COMPLETE"
    assert b["counts"]["pages_empty_tools"] == 1


def test_b15_legacy_resulttype_omitted():
    # changelog #8 : « Clients MUST treat results ... that omit the
    # field as "complete" » — le module REND le traité, pas un vide.
    b = post([{"tools": F("a")}]).json()
    assert b["pages"][0]["result_type"] == "omitted_treated_complete"


# ------------------------------------------------------- contrat API
def test_c1_refus_champs_nommés():
    r = post([{"tools": F("a"), "nextCursor": 64}])
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "pages[0].nextCursor"
    assert "string" in e["expected"]


def test_c2_refus_autres():
    cases = [
        ([{"tools": F("a"), "zz": 1}], "unknown keys"),
        ([{"tools": [{"x": 1}]}], "name"),
        ([{"tools": F("a"), "resultType": "partial"}], "vocabulary"),
        ([{"request": C_X, "tools": F("a")}], "NO cursor"),
        ([{"nextCursor": C_X}], "carries tools"),
        ([{"error": {"code": 1}, "tools": F("a")}], "no result keys"),
    ]
    for pages, needle in cases:
        r = post(pages)
        assert r.status_code == 400, pages
        msg = json.dumps(r.json())
        assert needle.lower() in msg.lower() or needle in msg, pages


def test_c3_declared_incoherent_refusé():
    r = post([{"tools": F("a")}], declared_count=2,
             declared_names=["a"])
    assert r.status_code == 400
    assert "contradicts" in r.text


def test_c4_extras_forbiddus():
    r = client.post("/api/v1/agent/mcp-list-completeness",
                    json={"pages": [{"tools": []}], "bogus": 1})
    assert r.status_code == 400


def test_c5_determinisme_octets():
    pages = [{"tools": F("a"), "nextCursor": C_K1},
             {"request": C_K1, "tools": F("b")}]
    r1 = post(pages, declared_count=2)
    r2 = post(pages, declared_count=2)
    assert r1.content == r2.content
    assert "sha256" in r1.json()


def test_c6_vocab_verdicts_clos():
    assert k.SEVERITY == ["STUCK_LOOP", "TRUNCATED_SILENT", "UNSTABLE",
                          "COUNT_SHORT", "COUNT_OVER", "INTERIM_LISTED",
                          "DUPED", "COMPLETE"]


def test_c7_module_sans_reseau():
    src = open(__file__.replace("tests/test_bundle113.py",
                                "mclistkit.py")).read()
    for banned in ("import urllib", "import httpx", "import requests",
                   "import socket", "import subprocess", "time.time",
                   "datetime.now"):
        assert banned not in src, banned


# ------------------------------------------------------ gardes fratrie
def test_d1_soeurs_gardent_leurs_aiguilles():
    # le COMBIEN coûte reste chez context-tax, le CHANGÉ chez
    # mcp-surface, la COLLISION chez tool-overlap — l'arrivée du
    # compteur de PAGES ne déplace aucun top1 de sœur.
    for q, want in (
            ("what does my tools list cost per turn in tokens",
             "agent_contexttax"),
            ("what changed in the tools list since the reading i pinned",
             "agent_mcpsurface"),
            ("which tools silently disappeared after adding a second "
             "mcp server", "agent_tooloverlap"),
    ):
        r = client.get("/route", params={"q": q, "top": "3"})
        names = [t["tool"] for t in r.json().get("tools", [])]
        assert names and names[0] == want, (q, names)


def test_d2_aiguilles_propres_top1():
    for q in (
            "did my mcp client see all the tools pages",
            "tools list truncated at page 2 nextcursor",
            "mon agent ne voit que la premiere page des outils mcp",
            "lista de ferramentas mcp cortada na pagina",
    ):
        r = client.get("/route", params={"q": q, "top": "3"})
        names = [t["tool"] for t in r.json().get("tools", [])]
        assert names and names[0] == "agent_mcplist", (q, names)


def test_d3_leurre_sans_donnees():
    # une phrase sans données ne doit RIEN prescrire (classe T6)
    r = client.get("/route",
                   params={"q": "je veux débrancher mon lave-vaisselle",
                           "top": "3"})
    b = r.json()
    assert not b.get("tools") or b.get("elsewhere")


# ------------------------------------------------- surface & parité
def test_e1_manifest_porte_la_ligne():
    body = client.get("/agent/manifest").text
    line = [l for l in body.splitlines()
            if l.startswith("agent_mcplist  ")]
    assert line and "/api/v1/agent/mcp-list-completeness" in line[0]


def test_e2_sayings_parite():
    import sayings
    s = sayings.SAY["/api/v1/agent/mcp-list-completeness"]
    assert set(s) == {"en", "fr", "pt"}
    for lang in s:
        assert len(s[lang]) > 40, lang


def test_e3_tool_spec_vivante():
    r = client.get("/tools/agent_mcplist.json")
    assert r.status_code == 200
    b = r.json()
    assert b["tier"].startswith("cap") or "cap" in b["tier"]
    assert b["pack"] == "checks"
