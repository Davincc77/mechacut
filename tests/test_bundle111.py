# -*- coding: utf-8 -*-
"""Bundle 111 — /agent/tool-overlap : QUELS DEUX OUTILS N'EN FONT QU'UN,
dans QUEL CLIENT, et la correction en NOMBRE.

Golds tracés À LA MAIN sur l'oracle séparé g111 (scratch/g111_oracle.py,
stdlib pure, écrit AVANT overlapkit.py — jamais importé du module).
Sens habituel : le test suit l'oracle ; si la machine contredit, on
vérifie DEUX FOIS qui a raison. DEUX révisions de main-calcul ont eu
lieu CE CYCLE et sont consignées : 1) la borne min_server_key est 1 sur
le repro publié (raccourcir la clef REND de la place au nom — j'avais
écrit 11 en confondant sens de la coupe ; le workaround publié
d'openworker dit exactement cela) ; 2) le marqueur de fold est au
MILIEU (head30+'...'+tail30), pas en fin (source gemini-cli relue).

Vecteurs PUBLICS rejoués (sources verbatim dans le module) :
  V1 microsoft/vscode#338895 : clef 13, gateway 29, cinq outils ->
     registered 2, tail_dropped 3 (le thrower COMPRIS : « 5 outils,
     2 listés »), behavior TAIL_ABORT, repair min_server_key_len 1.
  V2 foundry-dev-tools#723 : 77 vs 74 chars -> tete 64 IDENTIQUE
     (V2_HEAD épinglé octet à octet), COLLAPSE_CUT, WRONG_ROUTE ;
     noms collés nus -> NO_PREFIX_FIX (aucune clef à raccourcir).
  V3 gemini-cli generateValidName : deux noms ne différant QUE du
     milieu jeté -> fold 63 chars IDENTIQUE, FOLD_COLLAPSE,
     OVERWRITE_LAST : le dernier gagne, l'autre EST MORT.
  V4 sanitizer : "user.getData" vs "user_getData" -> un chez VS Code
     (SANITIZE_COLLAPSE, registered 1), PAS un chez gemini-cli (le
     point est légal), ILLEGAL_CHAR chez openai.
  V5 asymétrie : 112 chars légaux chez gemini_api (≤128), TOO_LONG
     chez openai, PLIÉS par gemini-cli -> GATE_STRICTER_THAN_API nommé.
  V6 CopilotKit : même nom nu sur deux serveurs -> BARE_SHADOW +
     NAME_CONFLICT anthropic (tool_name_conflict cité) ; verdict
     LOUD_ONLY — bruyant n'est pas muet. Anthropic ne jure AUCUNE
     longueur (non publiée) — test d'honnêteté : 200 chars -> zéro
     drapeau anthropic.
  V7 repair : NO_PREFIX_FIX quand le distinctif vit au-delà de toute
     chambre (têtes communes 60 chars) ; borne 6 pour deux clefs
     sharing prefix N'EXISTE PAS comme cas — la chambre à L=1 (58)
     dé-colle tout ce qui diffère en 58 premiers ; consigné.
  EXACT_ID : "a"+"b_c" vs "a_b"+"c" -> même id qualifié (ambiguïté
     de namespace, distinct du bug de listing refusé à l'entrée).
"""
import hashlib
import json

import pytest
from fastapi.testclient import TestClient

import main
import overlapkit as k

client = TestClient(main.app)
main.RATE_LIMIT = 10**9

GW = "Long_server_Name_For_Gateway-"
V1 = [GW + t for t in ("get_resource_details", "get_resource_stats",
                       "get_resource_status", "list_resources",
                       "list_zones")]
V2_A = ("mcp__4e9e25f1-b480-40f3-ba8d-a792f8f6ff07__"
        "get_deployment_logs_for_production")
V2_B = ("mcp__4e9e25f1-b480-40f3-ba8d-a792f8f6ff07__"
        "get_deployment_logs_for_preview")
V2_HEAD = ("mcp__4e9e25f1-b480-40f3-ba8d-a792f8f6ff07__"
           "get_deployment_logs_f")
H30 = "mcp_report_" + "x" * 21
T30 = "tail_shared_0123456789abcdefghij"
V3_A = H30 + "MIDDLEone" + T30
V3_B = H30 + "MIDDLEtwo" + T30
V5 = "mcp_gateway_" + "t" * 100


# ------------------------------------------------------- grammaires seules
def test_a1_vscode_cut_64_verbatim():
    # (prefix + name).replaceAll('.','_').slice(0,64)
    got = k._head(k._vscode_build("srv.key", "a.b" + "c" * 70), 64)
    assert len(got) == 64 and "_" in got[:11] and "." not in got


def test_a2_gemini_fold_marker_is_middle():
    # head(30) + "..." + tail(30) : le marqueur EST au milieu, 63 chars.
    folded = k._fold("mcp_" + "q" * 70)
    assert folded[30:33] == "..." and len(folded) == 63


def test_a3_utf16_units():
    # un emoji = 2 unités UTF-16, exactement comme String.slice (JS).
    assert k._u16("a😀b") == 4          # 3 code points, 4 unités
    assert k._head("😀abcd", 2) == "😀"  # une coupe au milieu d'une
    # surrogate pair produit du texte INVALIDE chez JS aussi ; ici la
    # pair tombe pile — et à 1 unité on ne casse pas un caractère :
    assert k._head("😀abcd", 1) == "\ufffd" or k._head("😀abcd", 1) == ""


def test_a4_head64_no_sanitize():
    # la famille gateway ne sanitize PAS : les points SURVIVENT à la coupe.
    raw = "mcp__a.b__" + "z" * 60
    assert "." in k._head(raw, 64)


# ---------------------------------------------------------------- V1 VS Code
def test_b1_vscode_repro_public():
    r = k.tool_overlap([{"name": t, "server": "litellm-gw-01"} for t in V1])
    vs = r["targets"]["vscode"]
    assert vs["registered"] == 2                     # « only 2 are listed »
    assert vs["tail_dropped"] == [V1[2], V1[3], V1[4]]  # thrower + suite
    assert vs["behavior"] == "TAIL_ABORT"
    assert r["verdict"] == "SILENT_LOSS"


def test_b2_vscode_repair_is_one():
    # main-calcul REVISÉ (consigné) : à L=1 l'id complet tient sous 64 —
    # aucune coupe, têtes = noms complets, uniques. Le workaround publié.
    r = k.tool_overlap([{"name": t, "server": "litellm-gw-01"} for t in V1])
    assert r["targets"]["vscode"]["repair"] == {"min_server_key_len": 1}


def test_b3_vscode_sixty_five():
    # 65 chars -> coupe exactement à 64.
    name = "n" * 61
    r = k.tool_overlap([{"name": name, "server": "abc"}])
    assert len(r["targets"]["vscode"]["ids"][0]) == 64


# ------------------------------------------------------------------- V2
def test_c1_head64_collapse_verbatim():
    r = k.tool_overlap([{"name": V2_A}, {"name": V2_B}])
    h = r["targets"]["head64"]
    assert h["groups"][0]["class"] == "COLLAPSE_CUT"
    assert h["groups"][0]["id"] == V2_HEAD and len(V2_HEAD) == 64
    assert r["verdict"] == "SILENT_LOSS"


def test_c2_head64_noprefix_fix():
    # noms collés nus : aucune clef serveur à raccourcir -> NO_PREFIX_FIX.
    r = k.tool_overlap([{"name": V2_A}, {"name": V2_B}])
    assert r["targets"]["head64"]["repair"] == {"verdict": "NO_PREFIX_FIX"}


def test_c3_deep_head_is_no_prefix_fix():
    # têtes communes 60+ : même L=1 (chambre 58) ne dé-colle pas.
    h = "a" * 60
    r = k.tool_overlap([{"name": h + "1", "server": "gw"},
                        {"name": h + "2", "server": "gw"}])
    assert r["targets"]["vscode"]["repair"] == {"verdict": "NO_PREFIX_FIX"}


# ------------------------------------------------------------------- V3
def test_d1_gemini_fold_collapse_overwrite():
    r = k.tool_overlap([{"name": V3_A}, {"name": V3_B}])
    g = r["targets"]["gemini_cli"]
    assert g["groups"][0]["class"] == "FOLD_COLLAPSE"
    assert g["behavior"] == "OVERWRITE_LAST"
    assert g["overwritten"][0]["kept"] == V3_B
    assert g["overwritten"][0]["dead"] == [V3_A]


def test_d2_gemini_prefixes_bare_names():
    r = k.tool_overlap([{"name": "solo"}])
    assert r["targets"]["gemini_cli"]["ids"][0] == "mcp_solo"


def test_d3_gemini_sanitizer_keeps_dot_colon():
    # leur classe de caractères [a-zA-Z0-9_\-.:] LUE dans leur source.
    assert k._gcli_build(None, "user.getData:2") == "mcp_user.getData:2"
    assert k._gcli_build(None, "a b!c") == "mcp_a_b_c"
    assert k._gcli_build(None, "9tail") == "_9tail" or \
        k._gcli_build(None, "9tail").startswith("mcp_")
    # "9tail" -> préfixé mcp_ D'ABORD (leur ordre exact), donc tete 'm'
    assert k._gcli_build(None, "9tail") == "mcp_9tail"


def test_d4_exact_id_namespace():
    # ("a","b_c") et ("a_b","c") qualifient au MÊME id : EXACT_ID —
    # distinct du doublon strict (server,name), refusé à l'entrée.
    r = k.tool_overlap([{"name": "b_c", "server": "a"},
                        {"name": "c", "server": "a_b"}])
    assert r["targets"]["gemini_cli"]["groups"][0]["class"] == "EXACT_ID"


# ------------------------------------------------------------------- V4
def test_e1_sanitize_divergence():
    r = k.tool_overlap([{"name": "user.getData"}, {"name": "user_getData"}])
    assert r["targets"]["vscode"]["groups"][0]["class"] == "SANITIZE_COLLAPSE"
    assert r["targets"]["vscode"]["registered"] == 1
    assert not r["targets"]["gemini_cli"]["groups"]      # point légal là
    assert r["targets"]["openai"]["flags"][0]["class"] == "ILLEGAL_CHAR"
    assert r["verdict"] == "SILENT_LOSS"


# ------------------------------------------------------------------- V5
def test_f1_gate_stricter_than_api():
    r = k.tool_overlap([{"name": V5}])
    assert not r["targets"]["gemini_api"]["flags"]       # légal <=128
    assert r["targets"]["openai"]["flags"][0]["class"] == "TOO_LONG"
    assert V5 in r["gates"]["GATE_STRICTER_THAN_API"]


def test_f2_anthropic_never_promises_length():
    # ce qui n'est pas publié ne se jure pas (leçon soldes-lu rejouée).
    r = k.tool_overlap([{"name": "x" * 200}])
    assert r["targets"]["anthropic"]["flags"] == []
    assert r["targets"]["gemini_api"]["flags"][0]["class"] == "TOO_LONG"


def test_f3_anthropic_names_the_conflict():
    r = k.tool_overlap([{"name": "get_file", "server": "drive"},
                        {"name": "get_file", "server": "mail"}])
    assert r["bare_shadows"] == [["get_file", ["drive", "mail"]]]
    assert r["targets"]["anthropic"]["flags"][0]["class"] == "NAME_CONFLICT"
    assert r["verdict"] == "LOUD_ONLY"   # bruyant != muet : classe close
    # sous qualification, les clients de la table ne perdent RIEN :
    for c in ("vscode", "gemini_cli", "head64"):
        assert not r["targets"][c]["groups"]


# ------------------------------------------------------------------ contrat
def test_g1_caps_refusals_field_expected():
    for body, fld in (
            ({"tools": []}, "tools"),
            ({"tools": [{"name": ""}]}, "tools[0].name"),
            ({"tools": [{"name": "a"}, {"name": "a"}]}, "tools[1]"),
            ({"tools": [{"name": "a", "zz": 1}]}, "tools[0]"),
            ({"tools": [{"name": "a" * 301}]}, "tools[0].name"),
            ({"tools": [{"name": "a", "server": ""}]}, "tools[0].server"),
            ({"tools": [{"name": "a"}], "targets": ["cursor"]}, "targets"),
    ):
        r = client.post("/api/v1/agent/tool-overlap", json=body)
        assert r.status_code == 400, body
        e = r.json()["errors"][0]
        assert e["field"] == fld and "expected" in e, e


def test_g2_targets_subset_closed():
    r = client.post("/api/v1/agent/tool-overlap",
                    json={"tools": [{"name": V2_A}, {"name": V2_B}],
                          "targets": ["head64"]}).json()
    assert set(r["targets"]) == {"head64"}


def test_g3_roundtrip_determinism_octet():
    body = {"tools": [{"name": t, "server": "litellm-gw-01"} for t in V1]}
    r1 = client.post("/api/v1/agent/tool-overlap", json=body)
    r2 = client.post("/api/v1/agent/tool-overlap", json=body)
    assert r1.status_code == 200 and r1.content == r2.content
    assert r1.json()["sha256"] == hashlib.sha256(json.dumps(
        {kk: vv for kk, vv in r1.json().items() if kk != "sha256"},
        sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode()).hexdigest()


def test_g4_ceiling_5000():
    r = client.post("/api/v1/agent/tool-overlap",
                    json={"tools": [{"name": "t%d" % i} for i in range(5001)]})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "tools"


def test_g5_folded_groups_cap():
    # >100 groupes : top 100, le reste plié et CHIFFRÉ (convention soeurs).
    # 110 tetes de 64 chars distinctes, chacune portee par DEUX noms qui
    # ne different qu'au 65e caractere : 110 groupes, 10 pliés.
    tools = []
    for i in range(110):
        head = ("h%03d" % i) + "0" * 60          # 4+60 = 64 chars
        assert len(head) == 64
        tools.append({"name": head + "A"})
        tools.append({"name": head + "B"})
    r = k.tool_overlap(tools)
    h = r["targets"]["head64"]
    assert len(h["groups"]) == 100 and h["groups_folded"] == 10


# ------------------------------------------------------------- routeur
def test_j1_aiguilles_overlap_x3():
    for q in ("which of my tools silently disappeared after adding a "
              "second mcp server",
              "deux serveurs meme nom d outil quel outil a disparu "
              "silencieusement vscode",
              "quais ferramentas sumiram sem erro colisao de nomes mcp",
              "tool names collide after truncation 64 characters",
              "mcp tool prefix same first 64 characters wrong tool"):
        r = client.get("/route", params={"q": q}).json()
        assert r["tools"], q
        assert r["tools"][0]["tool"] == "agent_tooloverlap", q


def test_j2_fratrie_garde_ses_aiguilles():
    for q, want in (
            ("how many tokens does my mcp tool list cost every turn",
             "agent_contexttax"),
            ("which mcp tools should I disconnect to fit the budget",
             "agent_tooltrim"),
            ("what changed in my mcp tool surface since last week",
             "agent_mcpsurface"),
            ("is this mcp tool listing going to be rejected by clients",
             "agent_mcpaudit"),
    ):
        r = client.get("/route", params={"q": q}).json()
        assert r["tools"][0]["tool"] == want, (q, r["tools"][0])


def test_j3_leurre_ne_prescrit_rien():
    # une phrase sans donnee de noms ne doit pas inventer de collision.
    r = client.get("/route", params={"q": "tell me about my day"}).json()
    assert "agent_tooloverlap" not in [t["tool"] for t in r["tools"][:3]]


# ---------------------------------------------------------------- pins
PIN = {"tools": [{"name": t, "server": "litellm-gw-01"} for t in V1]}


def test_k1_pin_vscode_repro():
    r = client.post("/api/v1/agent/tool-overlap", json=PIN).json()
    assert r["verdict"] == "SILENT_LOSS" and r["targets"]["vscode"]["registered"] == 2
    assert r["targets"]["vscode"]["repair"] == {"min_server_key_len": 1}
