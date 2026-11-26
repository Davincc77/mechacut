# -*- coding: utf-8 -*-
"""bundle116 — /agent/result-cliff : la traversée du cliff d'UN
RÉSULTAT, calculée DANS L'UNITÉ DU COMPTE du harnais nommé.

Attendus CALCULÉS À LA MAIN depuis les sources lues le 2026-11-26 —
jamais recopiés du module :
- claude-code : coupe « longer than 50,000 characters » (doc relue
  live) ; le matrice latin/grec de #97622 dit frontière IDENTIQUE en
  caractères — à 50 500 chars, marge −500 ; à 50 000, pas « longer »,
  marge 0.
- codex (truncate.rs relu) : survit si bytes <= 4×limit (max_bytes =
  limit*4, test s.len() <= max_bytes) ; removed_tokens = ceil((bytes −
  4×limit)/4) ; split_budget : left = max/2, right = max − left.
  Vecteur : limit 500 → 2 000 octets ; paste 2 049 « a » → dépassé de
  49 → ceil(49/4) = 12,25 → 13 tokens annoncés.
- rakazo (context-selection.ts relu) : keep = max(8, floor(len/4)) par
  bout, payload.contextTruncated=true ; estimateur 0,3/0,4/1/0,6/1,25
  avec pénalité lower->upper, digit->letter, letter->digit, planché au
  byteLength utf-8. Vecteurs à la main : « aB » = 0,3 + (0,3+1) =
  1,6 → ceil 2, bytes 2 → 2 ; « abc 123 » = 4×0,3 + 3×1 = 4,2 → 5,
  bytes 7 → 5 ; « 9 » = 1 → 1.
- hermes (tool_output_truncate.py relu) : head = int(max×0,4) =
  800 000, tail = 1 200 000 ; à 2 000 001 chars : omitted 1, notice à
  séparateurs de milliers.
- bionic #2338 : « exactly 50,000 characters » survivent, marqueur
  « ... (truncated) », aucune continuation.
- vscode #311068 : AUCUN seuil publié (14,4 KB rapporté, 50-999 KB
  coupé) → verdict nommé UNPUBLISHED_THRESHOLD, jamais un chiffre
  deviné.

Oracle INDÉPENDANT : re-implémentation naïve (math.ceil, tables dict)
d'écrire différente, jouée contre le module sur corpus de textes.
"""
import json
import math

import cliffkit
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)

ROUTE = "/api/v1/agent/result-cliff"


# ------------------------------------------------------- oracle indépendant
def oracle_codex(bytes_len, token_limit):
    """Écrit différemment (math.ceil, pas le ceil_div du module) —
    même loi, source codex-rs/utils/string/src/truncate.rs."""
    max_bytes = token_limit * 4
    if bytes_len <= max_bytes:
        return None
    removed = math.ceil((bytes_len - max_bytes) / 4)
    return {"cliff_bytes": max_bytes,
            "margin": max_bytes - bytes_len,
            "removed_tokens": removed,
            "head": max_bytes // 2,
            "tail": max_bytes - max_bytes // 2}


def oracle_rakazo_tokens(text):
    """Table dict, boucle séparée — relecture du TS ligne à ligne,
    écriture distincte du module."""
    weights = {"lower": 0.3, "upper": 0.3, "digit": 1.0,
               "punct": 0.4, "space": 0.3}
    total = 0.0
    prev = None
    units = []
    for ch in text:
        cp = ord(ch)
        if cp >= 0x10000:
            cp -= 0x10000
            units += [0xD800 + (cp >> 10), 0xDC00 + (cp & 0x3FF)]
        else:
            units.append(cp)
    for code in units:
        if 97 <= code <= 122:
            cls, w = "lower", weights["lower"]
        elif 65 <= code <= 90:
            cls, w = "upper", weights["upper"]
        elif 48 <= code <= 57:
            cls, w = "digit", weights["digit"]
        elif code >= 128:
            cls, w = "nonascii", (0.6 if code < 0x590 else 1.25)
        elif code == 32 or code < 32 or code == 127:
            cls, w = "space", weights["space"]
        else:
            cls, w = "punct", weights["punct"]
        total += w
        if prev == "lower" and cls == "upper":
            total += 1
        if prev == "digit" and cls in ("lower", "upper"):
            total += 1
        if prev in ("lower", "upper") and cls == "digit":
            total += 1
        prev = cls
    return min(math.ceil(total), len(text.encode("utf-8")))


def test_hand_vector_aB():
    # « aB » : a = 0,3 ; B = 0,3 + pénalité lower->upper 1 -> 1,6 ->
    # ceil 2 ; bytes utf-8 = 2 -> min = 2. À LA MAIN.
    assert cliffkit.rakazo_estimate_tokens("aB") == 2


def test_hand_vector_abc_space_123():
    # 4 × 0,3 (a,b,c,espace) + 3 × 1 (chiffres, sans pénalité digit->
    # digit) = 4,2 -> ceil 5 ; bytes 7 -> min = 5.
    assert cliffkit.rakazo_estimate_tokens("abc 123") == 5


def test_hand_vector_digit():
    assert cliffkit.rakazo_estimate_tokens("9") == 1


def test_oracle_agrees_on_corpus():
    for t in ("Hello, World 42!", "αβγ 123 xY", "a1B2c3",
              "\t\n  spaces", "emoji \U0001F600 tail",
              "Ünïcödé mix 9lives", "ABCdef123"):
        assert cliffkit.rakazo_estimate_tokens(t) == \
            oracle_rakazo_tokens(t), t


def test_codex_hand_vector():
    paste = "a" * 2049
    out = cliffkit.run_cliff({"harness": "codex", "result": paste,
                              "token_limit": 500})
    # 2049 > 2000 = 4×500 -> dépassé ; marge 2000−2049 = −49 ;
    # removed = ceil(49/4) = 13 ; head = 2000//2 = 1000, tail = 1000.
    assert out["verdict"] == "MIDDLE_CUT_MARKED"
    assert out["cliff"] == 2000
    assert out["margin"] == -49
    assert out["marker_rendered"] == "…13 tokens truncated…"
    assert out["kept_head_bytes"] == 1000
    assert out["kept_tail_bytes"] == 1000
    o = oracle_codex(2049, 500)
    assert o["margin"] == out["margin"]
    assert o["removed_tokens"] == 13


def test_codex_declared_tokens_exact_inverse():
    # tokens déclarés : l'INVERSION EXACTE par la fonction du harnais
    # lui-même (bytes = 4×tokens), pas un estimateur importé.
    out = cliffkit.run_cliff({"harness": "codex", "size": 600,
                              "unit": "tokens", "token_limit": 500})
    assert out["input_in_native_unit"] == 2400
    assert out["margin"] == 2000 - 2400
    assert out["verdict"] == "MIDDLE_CUT_MARKED"
    assert out["marker_rendered"] == "…100 tokens truncated…"


def test_codex_declared_chars_refused():
    # codex compte des OCTETS (÷4) : des chars déclarés ne traversent
    # pas — refus NOMMÉ, jamais une conversion devinée.
    try:
        cliffkit.run_cliff({"harness": "codex", "size": 100000,
                            "unit": "chars", "token_limit": 500})
        assert False, "refusal expected"
    except cliffkit.CliffError as e:
        assert e.field == "unit"
        assert "bytes" in e.expected


# ------------------------------------------------- claude-code (la loi)
def test_claude_matrix_replay():
    # #97622 rejoué : la frontière est en CARACTÈRES, identique
    # latin/grec. 49 999 survit (+1) ; 50 000 n'est pas « longer »
    # (marge 0) ; 50 500 est persisté (marge −500) et le message
    # MENT sur l'unité.
    for n, crossed in ((49999, False), (50000, False),
                       (50500, True)):
        out = cliffkit.run_cliff({"harness": "claude-code",
                                  "size": n, "unit": "chars"})
        assert out["crossed"] == crossed, n
        assert out["margin"] == 50000 - n
    lat = cliffkit.run_cliff({"harness": "claude-code",
                              "result": "x" * 50500})
    grk = cliffkit.run_cliff({"harness": "claude-code",
                              "result": "α" * 50500})
    assert lat["verdict"] == grk["verdict"] == "PERSIST_TO_FILE"
    assert lat["margin"] == grk["margin"] == -500
    # bytes différents (50 500 vs 101 000), traversée IDENTIQUE :
    # c'est exactement le mensonge que le champ porte.
    assert lat["measured"]["bytes"] == 50500
    assert grk["measured"]["bytes"] == 101000
    assert lat["message_lies"] is True


def test_claude_token_cliffs_never_guessed():
    # Les cliffs tokens de claude (warn 10 000, cap 25 000) sont
    # portés NOMMÉS mais INDETERMINABLES depuis les chars : le
    # tokenizer n'est pas publié, le kit refuse la conversion.
    out = cliffkit.run_cliff({"harness": "claude-code",
                              "result": "x" * 60000})
    also = out["also"]
    assert [c["cliff"] for c in also] == [10000, 25000]
    assert all("INDETERMINATE" in c["status"] for c in also)


def test_claude_description_surface():
    ok = cliffkit.run_cliff({"harness": "claude-code",
                             "surface": "description",
                             "size": 2048, "unit": "chars"})
    cut = cliffkit.run_cliff({"harness": "claude-code",
                              "surface": "description",
                              "size": 2049, "unit": "chars"})
    assert ok["verdict"] == "INLINE"
    assert cut["verdict"] == "HEAD_ONLY_SILENT"
    assert cut["message_lies"] is True
    assert "INTACT" in cut["marker"]


def test_bionic_exact():
    # #2338 : « exactly 50,000 » survivent, préfixe byte-identique,
    # marqueur sans compte, AUCUNE continuation.
    at = cliffkit.run_cliff({"harness": "bionic", "size": 50000,
                             "unit": "chars"})
    over = cliffkit.run_cliff({"harness": "lm studio", "size": 50001,
                               "unit": "chars"})
    assert at["verdict"] == "INLINE" and at["margin"] == 0
    assert over["verdict"] == "HEAD_ONLY_MARKED"
    assert over["margin"] == -1
    assert over["kept_prefix_chars"] == 50000
    assert over["marker"] == '"... (truncated)" appended'


def test_rakazo_argument_and_flag():
    # pas de budget -> pas de verdict inventé : refus NOMMÉ.
    nb = cliffkit.run_cliff({"harness": "rakazo",
                             "result": "z" * 500})
    assert nb["verdict"] == "REFUSED_NEEDS_ARGUMENT"
    assert nb["ask"] == "budget"
    ok = cliffkit.run_cliff({"harness": "rakazo", "size": 999,
                             "unit": "chars", "budget": 1000})
    cut = cliffkit.run_cliff({"harness": "rakazo", "size": 4001,
                              "unit": "chars", "budget": 1000})
    assert ok["verdict"] == "INLINE" and ok["margin"] == 1
    assert cut["crossed"] is True and cut["margin"] == -3001
    assert cut["inline_flag"] == "contextTruncated=true"
    assert cut["kept_per_end_rule"] == "max(8, floor(len/4)) per leaf"
    # la MUTATION est consignée : la formule #2439 est nommée morte.
    assert "DEAD CODE" in cut["repair"]


def test_vscode_unpublished_threshold():
    out = cliffkit.run_cliff({"harness": "vscode", "size": 120000,
                              "unit": "bytes"})
    assert out["verdict"] == "UNPUBLISHED_THRESHOLD"
    assert out["cliff"] is None and out["margin"] is None
    assert out["band_bytes"] == [14400, 1000000]


def test_hermes_own_row_exact():
    # notice à LA MAIN : head = int(2 000 000 × 0,4) = 800 000 ;
    # tail = 1 200 000 ; à 2 000 001 : omitted 1, total « 2,000,001 ».
    at = cliffkit.run_cliff({"harness": "hermes-agent", "size": 2000000,
                             "unit": "chars"})
    over = cliffkit.run_cliff({"harness": "hermes-agent",
                               "result": "q" * 2000001})
    assert at["verdict"] == "INLINE" and at["margin"] == 0
    assert over["crossed"] is True
    assert over["kept_head_chars"] == 800000
    assert over["kept_tail_chars"] == 1200000
    assert over["marker_rendered"] == (
        "\n\n... [MCP RESULT TRUNCATED - 1 chars omitted out of "
        "2,000,001 total] ...\n\n")


# ------------------------------------------------------------- refusals
def test_unknown_harness_names_the_closed_table():
    try:
        cliffkit.run_cliff({"harness": "gpt-shell", "size": 1,
                            "unit": "chars"})
        assert False
    except cliffkit.CliffError as e:
        assert e.field == "harness"
        for h in cliffkit.ALL_ORDER:
            assert h in e.expected


def test_unit_absent_is_the_named_refusal():
    # « unité absente = refus nommé » — la thèse du cycle en un test.
    try:
        cliffkit.run_cliff({"harness": "bionic", "size": 60000})
        assert False
    except cliffkit.CliffError as e:
        assert e.field == "unit"


def test_lines_declared_refused_everywhere():
    # AUCUNE ligne vivante de la table ne compte des lignes (le 256
    # lignes de codex est une note v0.56, pas la loi) : refus nommé.
    try:
        cliffkit.run_cliff({"harness": "claude-code", "size": 300,
                            "unit": "lines"})
        assert False
    except cliffkit.CliffError as e:
        assert e.field == "unit"


def test_paste_and_declared_are_two_claims():
    try:
        cliffkit.run_cliff({"harness": "bionic", "result": "abc",
                            "size": 1, "unit": "chars"})
        assert False
    except cliffkit.CliffError as e:
        assert e.field == "size"


# ---------------------------------------------------------------- all-rows
def test_all_rows_one_paste_eight_countings():
    out = cliffkit.run_cliff({"result": "hello", "token_limit": 500,
                              "budget": 100000})
    assert out["mode"] == "all-rows"
    by = {r["harness"]: r for r in out["rows"]}
    assert set(by) == set(cliffkit.ALL_ORDER)
    assert by["claude-code"]["margin"] == 49995
    assert by["bionic"]["margin"] == 49995
    assert by["hermes-agent"]["margin"] == 2000000 - 5
    assert by["codex"]["verdict"] == "INLINE"
    assert by["codex"]["margin"] == 2000 - 5  # bytes = 5, ASCII
    assert by["rakazo"]["verdict"] == "INLINE"
    assert by["vscode"]["verdict"] == "UNPUBLISHED_THRESHOLD"
    # firecrawl #548 vit dans la ligne claude (note de recouvrance),
    # pas comme harnais séparé :
    assert "firecrawl" not in by
    assert "firecrawl_548" in out


def test_all_rows_without_config_args_are_honest():
    out = cliffkit.run_cliff({"result": "hello"})
    by = {r["harness"]: r for r in out["rows"]}
    assert by["codex"]["verdict"] == "REFUSED_NEEDS_ARGUMENT"
    assert by["rakazo"]["verdict"] == "REFUSED_NEEDS_ARGUMENT"
    assert by["claude-code"]["verdict"] == "INLINE"


# ---------------------------------------------------------------- endpoint
def test_endpoint_200_with_sha_and_cold_table():
    r = client.post(ROUTE, json={"harness": "claude code",
                                 "size": 50500, "unit": "chars"})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["verdict"] == "PERSIST_TO_FILE"
    assert b["table_version"] == cliffkit.TABLE_VERSION
    assert "sha256" in b


def test_endpoint_refusals_are_400_named():
    r = client.post(ROUTE, json={"harness": "bionic", "size": 1})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "unit"
    r2 = client.post(ROUTE, json={"harness": "nope", "size": 1,
                                  "unit": "chars"})
    assert r2.status_code == 400


def test_endpoint_two_calls_byte_identical():
    body = {"harness": "rakazo", "size": 1001, "unit": "chars",
            "budget": 1000}
    a = client.post(ROUTE, json=body).content
    b = client.post(ROUTE, json=body).content
    assert a == b


def test_manifest_line_budget_holds():
    import routing
    txt = routing.manifest_text(main.app.version)
    assert "agent_resultcliff" in txt
    assert len(txt.encode("utf-8")) < 9000


# ------------------------------------------------- LOT 2 : modelid base
# TEMOIN DE BASE (lentille RADAR, miroir 25-11 23h47 — trois :batch
# listes, 404 a l'ecriture). Attendus a la MAIN : champ additif en
# mode catalogue seulement, jamais un 13e verdict.

def test_base_witness_listed_proves_the_door_exists():
    import modelidkit
    out = modelidkit.run_modelid({
        "ids": ["anthropic/claude-sonnet-5.5:batch"],
        "catalog": ["anthropic/claude-sonnet-5.5",
                    "anthropic/claude-sonnet-5.5:batch"]})
    e = out["results"][0]
    assert e["verdict"] == "OK"          # l'echelle n'a pas bouge
    assert e["base"]["slug"] == "anthropic/claude-sonnet-5.5"
    assert e["base"]["listed"] is True
    assert "proven listed" in e["base"]["note"]
    assert "ping" in e["base"]["note"]   # V23 : listee != invoquable


def test_base_witness_absent_names_the_mirage_risk():
    import modelidkit
    out = modelidkit.run_modelid({
        "ids": ["zeta/ghost:batch"],
        "catalog": ["zeta/ghost:batch"]})   # suffixe liste, base absente
    e = out["results"][0]
    assert e["base"]["listed"] is False
    assert "unproven HERE" in e["base"]["note"]
    assert "swears nothing" in e["base"]["note"]


def test_base_witness_silence_outside_catalog_and_plain_ids():
    import modelidkit
    gram = modelidkit.run_modelid({"ids": ["a/b:batch"]})
    assert "base" not in gram["results"][0]      # mode grammaire pure
    plain = modelidkit.run_modelid({"ids": ["a/b"], "catalog": ["a/b"]})
    assert "base" not in plain["results"][0]     # pas de suffixe, pas
    # de temoin : les pins sans suffixe restent octet pour octet.


def test_base_witness_free_variant_keeps_the_id_ladder():
    # :free EST l'id (VARIANT_DECOR b68) — le temoin s'ajoute SANS
    # toucher le verdict : base absente = note nommee.
    import modelidkit
    out = modelidkit.run_modelid({
        "ids": ["deepseek/deepseek-chat-v3:free"],
        "catalog": ["deepseek/deepseek-chat-v3:free", "x/y"]})
    e = out["results"][0]
    assert e["verdict"] == "OK"
    assert e["base"]["listed"] is False
