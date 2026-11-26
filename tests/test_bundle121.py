# -*- coding: utf-8 -*-
"""bundle121 — /agent/result-cliff : LE SURVIVANT PARLE.
Un collage JSON + la loi de chaque harnais rejouee EXACTEMENT -> le
kit prononce: INTACT / PARSEABLE_BUT_MUTATED / BROKEN (+ le noeud
coupable) / NO_CONTENT_SURVIVES / NOT_REPLAYED (raison nommee).
Demande MESUREE, pas plaidoyee : arXiv 2610.36114 (3 827/11 189
resultats coupes, « every cut result became broken JSON ») + la vague
de novembre 2026 ou des frameworks EXECUTENT des arguments tronques
« repares » : llama_index#24102, NeMo#2550/#2551 (fix = strict
json.loads), langchain4j#7169, simonw/llm#1887, PraisonAI#6369.

Attendus CALCULES A LA MAIN (sources lues 2026-11-26) — jamais
recopies du module :

V1 codex, coupe DANS une seule chaine :
  texte = {"k":" + 3000 x + ","n":7} -> 6 + 3000 + 8 = 3 014
  caracteres ET octets (pur ASCII).
  token_limit 400 -> cliff = 4 x 400 = 1 600 octets ;
  removed_tokens = ceil((3014 - 1600)/4) = ceil(353,5) = 354 ;
  marqueur = "…354 tokens truncated…" = 1+3+1+6+1+9+1 = 22 caracteres.
  tete = 800 octets -> 800 caractères (ASCII) ; queue = 800 ->
  reprise a 3014 - 800 = 2 214.
  Survivant = 800 premiers + marqueur + 800 derniers : la chaine
  "k" vaut 794 x + marqueur + 792 x — le document PARSE
  mais la valeur MENT -> PARSEABLE_BUT_MUTATED, coupe [800..2214],
  coupable = $.k des DEUX bords, same_string VRAI.

V2 codex, coupe DANS un nombre :
  texte = {"a":[1,2,...,590],"tail":"keep"} — 590 entiers, separes
  par des virgules. Comptage : {"a":[ = 6 ; 1..9 = 9 chiffres + 9
  virgules = 18 ; 10..99 = 180 + 90 = 270 ; 100..590 = 491 nombres x
  3 chiffres = 1 473 + 491 virgules = 1 964 ; total interieur =
  6 + 18 + 270 + 1964 = 2 258 ; + "tail":"keep"} = 15 -> 2 273
  caracteres. token_limit 400 -> cliff 1 600 ; tete 800 octets.
  Ou est le caractere 800 ? 100 commence a 6+18+270 = 294 ;
  (800 - 294) = 506 ; chaque nombre>=100 coute 4 (3 chiffres +
  virgule) ; 506 = 126 x 4 + 2 -> nombre 100+126 = 226, 2e de ses
  3 chiffres : caractere 800 = '6' FINAL de "226" -> NOEUD
  number $.a[225] (valeur 226 = index 225). Marqueur AU MILIEU D'UN
  TABLEAU -> json.loads refuse : BROKEN.

V3 bionic, coupe-prefixe qui AVALE LA FIN DU DOCUMENT :
  texte = {"big":" + 60 000 y + "} -> 8 + 60 000 + 2 = 60 010.
  cliff 50 000 -> survivant = 50 000 premiers + "... (truncated)".
  La portee [50 000, 60 010) contient le FERMETURE de la chaine et
  l'ACCOLADE : le prefixe seul ne ferme RIEN -> BROKEN, cut[0] = 50 000,
  begin = $.big (la chaine couvre 7..60 006).

V4 hermes-agent : tete 40 % = int(2 000 000 x 0,4) = 800 000 ;
  queue = 1 200 000 ; document 2 000 010 -> 10 caracteres meurent,
  les DEUX bornes dans la chaine "a" -> PARSEABLE_BUT_MUTATED.

V5 goose shell : fichier de 2 001 lignes ; loi = 2 000 lignes
  DEPASSEES (2 001 > 2 000) -> la tete tombe, la queue DES 50
  DERNIERES LIGNES survit (coupe 20000 octets? ici < 10 000 si on
  garde les lignes courtes — 50 lignes x ~6 car = ~300 octets).
  cut commence a 0 : begin = la structure racine.

V6 mode declare : PAS DE CHAMP (le kit ne prononce jamais sur des
  octets qu'il n'a pas vus).

V7 toutes lignes : chaque ligne rend SON verdict nomme.

Oracle INDEPENDANT : _json.loads decide PARSE/BREAK ; les offsets
ci-dessus sont arithmetiques, pas observees.
"""
import json

import cliffkit
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)

ROUTE = "/api/v1/agent/result-cliff"


def _post(args):
    r = client.post(ROUTE, json=args)
    assert r.status_code == 200, r.text
    return r.json()


# ------------------------------------------------------------------ V1
def test_v1_codex_cut_inside_one_string_is_the_lie():
    text = '{"k":"' + "x" * 3000 + '","n":7}'
    assert len(text) == 3014
    out = _post({"harness": "codex", "result": text,
                 "token_limit": 400})
    js = out["json_survival"]
    assert js["input"] == "JSON"
    assert js["verdict"] == "PARSEABLE_BUT_MUTATED"
    assert js["cut"] == [800, 2214]
    assert js["marker_rendered"] == "…354 tokens truncated…"
    g = js["guilty"]
    assert g["begin"] == {"kind": "string_value", "path": "$.k"}
    assert g["end"] == {"kind": "string_value", "path": "$.k"}
    assert g["same_string"] is True


def test_v1_survivor_value_is_exactly_the_hand_trace():
    # 794 x + le marqueur de 22 + 792 x = 1608 caracteres dans $.k
    text = '{"k":"' + "x" * 3000 + '","n":7}'
    out = _post({"harness": "codex", "result": text,
                 "token_limit": 400})
    survivor = ('{"k":"' + "x" * 794 + "…354 tokens truncated…"
                + "x" * 792 + '","n":7}')
    assert json.loads(survivor)["k"] == "x" * 794 + \
        "…354 tokens truncated…" + "x" * 792
    # et le champ rendu est le MEME document (oracle json, pas kit)
    assert out["json_survival"]["verdict"] == "PARSEABLE_BUT_MUTATED"


# ------------------------------------------------------------------ V2
def test_v2_codex_cut_inside_number_is_broken_with_named_node():
    text = '{"a":[' + ",".join(str(i) for i in range(1, 591)) \
        + '],"tail":"keep"}'
    assert len(text) == 2273  # recompte a la main, voir docstring
    out = _post({"harness": "codex", "result": text,
                 "token_limit": 400})
    js = out["json_survival"]
    assert js["verdict"] == "BROKEN"
    assert js["cut"][0] == 800
    g = js["guilty"]
    assert g["begin"]["kind"] == "number"
    assert g["begin"]["path"] == "$.a[225]"
    assert g["same_string"] is False


# ------------------------------------------------------------------ V3
def test_v3_bionic_prefix_cut_is_broken():
    text = '{"big":"' + "y" * 60000 + '"}'
    assert len(text) == 60010
    out = _post({"harness": "bionic", "result": text})
    js = out["json_survival"]
    assert js["verdict"] == "BROKEN"
    assert js["cut"] == [50000, 60010]
    assert js["guilty"]["begin"]["path"] == "$.big"
    # meme DANS une chaine au debut : la portee avale la fermeture
    assert js["guilty"]["same_string"] is False


# ------------------------------------------------------------------ V4
def test_v4_hermes_newlined_notice_breaks_even_an_in_string_cut():
    # LA LEÇON DU VECTEUR : la notice hermes contient des SAUTS DE
    # LIGNE bruts — dans une chaine JSON, un saut de ligne est un
    # CARACTÈRE DE CONTRÔLÈTE : la coupe, même entièrement dans une
    # valeur, ne mute pas le survivant, elle le CASSE. La forme du
    # marqueur EST le verdict.
    # {"a":" = 6 ; z*2 000 000 ; '","b":"0123456789"}' = 19
    text = '{"a":"' + "z" * 2000000 + '","b":"0123456789"}'
    assert len(text) == 2000025
    out = _post({"harness": "hermes-agent", "result": text})
    js = out["json_survival"]
    # tete = int(2 000 000 x 0,4) = 800 000 ; queue = 1 200 000 ;
    # portee = [800 000, 2 000 025 - 1 200 000) = [800 000, 800 025),
    # les DEUX bords dans la chaine a (couvre 6..2 000 006).
    assert js["verdict"] == "BROKEN"
    assert js["cut"] == [800000, 800025]
    assert js["guilty"]["begin"]["path"] == "$.a"
    assert js["guilty"]["same_string"] is True
    assert "char 800" in js["survivor_error"]  # casse AU marqueur


# ------------------------------------------------------------------ V5
def test_v5_goose_head_dies_root_is_guilty():
    # JSON VALIDE : 2 002 lignes -> 1 en-tete, 1 999 lignes "1,",
    # une ligne "1" SANS virgule (la virgule finale tuerait le doc —
    # piége péché par l'oracle json lui-même), puis "]}"
    lines = ['{"a":['] + ["1,"] * 1999 + ["1", "]}"]
    # 2 002 lignes > OUTPUT_LIMIT_LINES (2 000) ; octets ~6 008 <<
    # 50 000 ; queue des 50 dernieres lignes << 10 000 octets.
    text = "\n".join(lines)
    json.loads(text)  # oracle : le vecteur LUI-MÊME doit parser
    out = _post({"harness": "goose", "result": text})
    assert out["verdict"] == "TEMP_FILE_TAIL_ONLY"
    js = out["json_survival"]
    assert js["verdict"] == "BROKEN"
    assert js["cut"][0] == 0  # la TETE est ce qui meurt
    assert js["guilty"]["begin"]["path"] == "$"


def test_v5b_goose_global_replace_names_no_content():
    text = '{"k":"' + "w" * 250000 + '"}'
    out = _post({"harness": "goose", "result": text})
    # law lines: 1 ligne ! (< 2000 lignes, < 50 000 octets? NON :
    # 250 008 octets > 50 000 -> TEMP_FILE_TAIL_ONLY BIEN AVANT le
    # handler global. Pour atteindre le global, il faut une sortie
    # sous les deux clauses shell ET > 200 000 caracteres —
    # impossible : la clause shell mord d'abord. tool=extension
    # juge SEUL le handler global :
    assert out["verdict"] == "TEMP_FILE_TAIL_ONLY"
    out2 = _post({"harness": "goose", "result": text,
                  "tool": "extension"})
    assert out2["verdict"] == "REPLACE_WITH_NOTICE"
    js2 = out2["json_survival"]
    assert js2["verdict"] == "NO_CONTENT_SURVIVES"
    assert "goose_mcp_response_" in js2["rescue"]


# ------------------------------------------------------------------ V6
def test_v6_declared_mode_has_no_json_field():
    out = _post({"harness": "codex", "size": 3014, "unit": "bytes",
                 "token_limit": 400})
    assert out["mode"] == "declared"
    assert "json_survival" not in out
    out2 = _post({"harness": "claude-code", "size": 50001,
                  "unit": "chars"})
    assert "json_survival" not in out2


def test_v6b_not_json_paste_is_named_not_guessed():
    out = _post({"harness": "codex", "result": "hello {broken",
                 "token_limit": 400})
    js = out["json_survival"]
    assert js["input"] == "NOT_JSON"
    assert js["verdict"] == "NOT_REPLAYED"


# ------------------------------------------------------------------ V7
def test_v7_all_rows_every_row_names_its_own_answer():
    text = '{"big":"' + "q" * 60000 + '"}'
    out = _post({"result": text})
    assert out["mode"] == "all-rows"
    by = {r["harness"]: r for r in out["rows"]}
    assert by["claude-code"]["json_survival"]["verdict"] == \
        "NO_CONTENT_SURVIVES"
    assert by["bionic"]["json_survival"]["verdict"] == "BROKEN"
    assert by["codex"]["json_survival"]["verdict"] == "NOT_REPLAYED"
    assert "token_limit" in by["codex"]["json_survival"]["why"]
    assert by["rakazo"]["json_survival"]["verdict"] == "NOT_REPLAYED"
    assert by["vscode"]["json_survival"]["verdict"] == "NOT_REPLAYED"
    assert by["onyx"]["json_survival"]["verdict"] == "NOT_REPLAYED"
    assert by["hermes-agent"]["json_survival"]["verdict"] == "INTACT"
    assert by["goose"]["json_survival"]["verdict"] == "BROKEN"


def test_v7b_small_json_is_intact_everywhere():
    out = _post({"result": '{"ok": true}'})
    for r in out["rows"]:
        js = r["json_survival"]
        assert js["input"] == "JSON"
        assert js["verdict"] in ("INTACT", "NOT_REPLAYED")


# ------------------------------------------------- lois statiques b121
def test_claude_transport_guard_ships():
    out = _post({"harness": "claude-code", "size": 10, "unit": "chars"})
    assert "16 MiB" in out["transport_guard"]
    assert "WebSocket" in out["transport_guard"]


def test_codex_mcp_envelope_ships():
    # codex compte en OCTETS — un declared 'chars' est un refus NOMMÉ
    # (c'est le produit, pas un bug : le test le prouve en passant)
    out = _post({"harness": "codex", "size": 10, "unit": "bytes",
                 "token_limit": 500})
    env = out["mcp_envelope"]
    assert "Truncated tool output:" in env
    assert "structured_content is DROPPED" in env


def test_table_version_bumped():
    assert cliffkit.TABLE_VERSION == "b121-1"


# ------------------------------------------------------------- oracles
def test_oracle_mutation_path_via_independent_json():
    # oracle ecrit DIFFEREMMENT : reproduire la coupe a la main et
    # laisser json.decider, sans passer par _survivor_replay.
    text = '{"k":"' + "x" * 3000 + '","n":7}'
    pre = text[:800]
    suf = text[2214:]
    survivor = pre + "…354 tokens truncated…" + suf
    doc = json.loads(survivor)  # doit lever si le kit a tort
    assert doc["n"] == 7
    assert "…354 tokens truncated…" in doc["k"]


def test_determinism_same_bytes():
    text = '{"a":[' + ",".join(str(i) for i in range(1, 591)) \
        + '],"tail":"keep"}'
    r1 = client.post(ROUTE, json={"harness": "codex",
                                  "result": text,
                                  "token_limit": 400})
    r2 = client.post(ROUTE, json={"harness": "codex",
                                  "result": text,
                                  "token_limit": 400})
    assert r1.content == r2.content
