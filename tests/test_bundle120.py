# -*- coding: utf-8 -*-
"""bundle120 — CLIFFKIT ligne GOOSE (alternance DEV, rang 1 de la file
b119). La douleur, relevée AU CODE cet après-midi 2026-11-26 — la
fiche portée depuis b118 exigeait cette relecture, et la relecture a
CORRIGÉ la fiche :

0. L'identité : `gh api repos/block/goose` RENVOIE aaif-goose/goose —
   le projet a changé d'org, le redirect est prouvé par l'API le jour
   même. La « loi CLI 20 lignes » portée par b118 est RETIRÉE : elle
   n'existe pas dans le code.

1. COUCHE SHELL (developer extension, shell.rs lignes 161-164, code
   relu à HEAD 2026-11-26) : TRUNCATE = lines > 2000 OR bytes > 50000
   — des UNITÉS MIXTES, une grammaire que claude/codex ne portent
   pas. Le full output va dans le TempDir PRIVÉ de ShellTool (mort
   avec l'instance) ; l'inline = les 50 DERNIÈRES lignes, puis coupe
   à 10 000 octets PAR LA QUEUE (la tête est jetée deux fois) ; le
   reason cite les LIGNES d'abord quand les deux bornes dépassent
   (`if exceeded_lines`). Les constantes sont publiées dans le code —
   la ligne les PORTE, contrairement à onyx où le 20 000 n'était que
   PROPOSÉ.

2. COUCHE GLOBALE (large_response_handler.rs, relu à HEAD) : tout
   résultat de TOUT outil, threshold = GOOSE_MAX_TOOL_RESPONSE_SIZE
   (knob #9256 merged 2026-05-27), default 200_000 CHARS (le champ
   .chars().count() est LA loi — et le fichier est écrit dans une
   TempDir distincte). Deux verdicts séparés : INLINE (les deux
   couches tiennent), TEMP_FILE_TAIL_ONLY (shell seule),
   REPLACE_WITH_NOTICE (globale). La globale ne tranche JAMAIS le
   texte en place — elle LE REMPLACE par un avis ; le inline n'est
   pas un morceau du résultat, c'est 0 caractère du résultat.

Les attendus sont CALCULÉS À LA MAIN (bornes UTF-8, priorités de
raison, survivants exacts de la double coupe). La loi d'inégalité
bornée : bytes >= chars et chars >= bytes/4 (UTF-8, la fonction du
harness lui-même) — un MODE DÉCLARÉ ne devine pas : il DÉDUIT quand
la borne décide, et nomme INDETERMINATE sinon.
"""
import cliffkit
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)

ROUTE = "/api/v1/agent/result-cliff"

# constantes publiées, citées à la main depuis shell.rs:161-164
LINES_CLIFF = 2000      # > 2000 lignes déclenche
BYTES_CLIFF = 50_000    # > 50 000 octets déclenche
PREVIEW_LINES = 50      # les 50 DERNIÈRES survivent
PREVIEW_BYTES = 10_000  # puis queue-coupées à 10 000 octets
GLOBAL_CHARS = 200_000  # GOOSE_MAX_TOOL_RESPONSE_SIZE default


def _paste(text, **extra):
    args = {"result": text}
    args.update(extra)
    return cliffkit.run_cliff(args)


# ------------------------------------------------ couche globale
def test_global_boundary_equality_survives():
    # .count() > 200_000 : la loi du STRICTEMENT PLUS LONG — 200 000
    # caractères passent, calculé à la main.
    out = cliffkit.run_cliff({"harness": "goose", "size": GLOBAL_CHARS,
                              "unit": "chars", "tool": "extension"})
    assert out["verdict"] == "INLINE"
    assert out["margin"] == 0
    assert out["crossed"] is False


def test_global_replace_with_notice_named():
    out = cliffkit.run_cliff({"harness": "goose",
                              "size": GLOBAL_CHARS + 1,
                              "unit": "chars", "tool": "extension"})
    assert out["verdict"] == "REPLACE_WITH_NOTICE"
    assert out["crossed"] is True
    assert out["margin"] == -1
    # le inline ne survit PAS tronqué — il est REMPLACÉ : l'avis est
    # tout ce que le modèle voit.
    assert "stored in the file" in out["marker"]
    assert out["message_lies"] is False


def test_tool_extension_skips_shell_law():
    # 60 000 chars via un outil MCP NON-developer : la loi shell ne
    # s'applique PAS, la globale tient (60 000 <= 200 000) → INLINE.
    out = cliffkit.run_cliff({"harness": "goose", "size": 60_000,
                              "unit": "chars", "tool": "extension"})
    assert out["verdict"] == "INLINE"
    assert out["shell_law"]["applies"] is False


# ------------------------------------------------ couche shell : pâte
def test_shell_lines_trigger_survivors_hand_computed():
    # 2 001 lignes d'un 'x' : lignes = 2 001 > 2 000 → coupe ;
    # octets = 2 001 + 2 000 retours = 4 001 <= 50 000 (la borne des
    # lignes SEULE décide) ; survivants = les 50 dernières lignes
    # jointes par \\n = 50 + 49 = 99 octets, <= 10 000, pas de
    # seconde coupe. Calculés À LA MAIN.
    text = "\n".join(["x"] * 2001)
    out = _paste(text, harness="goose")
    assert out["verdict"] == "TEMP_FILE_TAIL_ONLY"
    law = out["shell_law"]
    assert law["triggered_by"] == "lines"
    assert law["survivor_lines"] == 50
    assert law["survivor_bytes"] == 99
    assert law["dropped_head_lines"] == 1951
    # la GLOBALE ne mord pas ici : la pâte fait 4 001 CARACTÈRES
    # (2 001 x + 2 000 retours), <= 200 000 — marge calculée à la
    # main :
    assert out["global"]["margin"] == GLOBAL_CHARS - 4001


def test_shell_bytes_trigger_reason_priority():
    # 1 000 lignes de 59 'y' : lignes = 1 000 <= 2000 ; octets =
    # 1 000*59 + 999 retours = 59 999 > 50 000 → la borne OCTETS
    # décide (seule dépassée).
    text = "\n".join(["y" * 59] * 1000)
    out = _paste(text, harness="goose")
    assert out["verdict"] == "TEMP_FILE_TAIL_ONLY"
    law = out["shell_law"]
    assert law["triggered_by"] == "bytes"
    # survivants : les 50 dernières lignes = 50*59 + 49 = 2 999
    # octets <= 10 000 — rendu tel quel.
    assert law["survivor_lines"] == 50
    assert law["survivor_bytes"] == 2999


def test_shell_both_exceeded_lines_reason_wins():
    # 2 500 lignes de 25 'z' : lignes 2 500 > 2000 ET octets
    # 2 500*25 + 2 499 = 64 999 > 50 000 — le code cite les LIGNES
    # en premier (`if exceeded_lines`). À LA MAIN.
    text = "\n".join(["z" * 25] * 2500)
    out = _paste(text, harness="goose")
    law = out["shell_law"]
    assert law["triggered_by"] == "lines"
    assert "2000 line limit" in law["reason_rendered"]
    assert "2500 lines total" in law["reason_rendered"]


def test_shell_preview_second_cut():
    # 2 lignes de 30 000 'w' : lignes = 2 <= 2000 ; octets =
    # 60 001 > 50 000 → coupe. Survivants = 50 dernières lignes =
    # TOUT (2 lignes), 60 001 octets > 10 000 → SECONDE coupe par la
    # QUEUE : les 10 000 derniers octets, ASCII → un seul 'w'-bloc
    # de 9 999 w + le \\n d'avant ? Non : queue pure de la chaîne
    # jointe "w"*30000 + "\n" + "w"*30000 = les 10 000 derniers
    # octets = 10 000 w, 0 retour à la ligne → 1 ligne, 10 000
    # octets. LA DOUBLE COUPE EST LE VERDICT TAIL-ONLY.
    text = "w" * 30000 + "\n" + "w" * 30000
    out = _paste(text, harness="goose")
    law = out["shell_law"]
    assert law["triggered_by"] == "bytes"
    assert law["survivor_bytes"] == PREVIEW_BYTES
    assert law["preview_line_cut_applied"] is True
    assert law["survivor_lines"] == 1


def test_shell_tail_snaps_to_char_boundary():
    # Vectorisé à la MAIN : "é"*20001 + "u"*9999 → octets =
    # 40 002 + 9 999 = 50 001 > 50 000 → coupe (borne OCTETS seule,
    # 1 ligne <= 2000). Preview = la ligne entière (50 001 o >
    # 10 000) → queue start = 50 001 - 10 000 = 40 001, ODD =
    # second byte du dernier é → SNAP à 40 002 : survivent les
    # 9 999 'u' — 9 999 octets, 9 999 caractères, PREVIEW_BYTES-1.
    text = "é" * 20001 + "u" * 9999
    out = cliffkit.run_cliff({"harness": "goose", "result": text})
    law = out["shell_law"]
    assert law["triggered_by"] == "bytes"
    assert law["survivor_bytes"] == PREVIEW_BYTES - 1  # 9 999
    assert law["survivor_chars"] == 9999
    assert law["boundary_snap_applied"] is True


# ------------------------------------------------ modes déclarés,
# bornes UTF-8 déduites, jamais devinées
def test_declared_chars_bound_decides_shell():
    # 60 000 CARACTÈRES déclarés : octets >= caractères (UTF-8 —
    # l'inégalité du harness lui-même) → 60 000 > 50 000 → la loi
    # shell est franchie CERTAIN, sans connaître le contenu.
    out = cliffkit.run_cliff({"harness": "goose", "size": 60_000,
                              "unit": "chars"})
    assert out["verdict"] == "TEMP_FILE_TAIL_ONLY"
    assert out["shell_law"]["by_bound"] == "bytes>=chars"
    assert out["global"]["crossed"] is False


def test_declared_small_chars_is_indeterminate_not_inline_lie():
    # 40 000 caractères : octets entre 40 000 et 160 000 — la borne
    # ne décide PAS ; répondre INLINE SERAIT un MENSONGE potentiel.
    out = cliffkit.run_cliff({"harness": "goose", "size": 40_000,
                              "unit": "chars"})
    assert out["shell_law"]["status"] == "INDETERMINATE_NEEDS_PASTE"
    assert out["global"]["crossed"] is False


def test_declared_bytes_bound_decides_global():
    # 900 001 OCTETS : chars >= bytes/4 = 225 000.25 → 225 001 >
    # 200 000 → la globale franchie PAR BORNAGE, à la main.
    out = cliffkit.run_cliff({"harness": "goose", "size": 900_001,
                              "unit": "bytes", "tool": "extension"})
    assert out["verdict"] == "REPLACE_WITH_NOTICE"
    assert out["global"]["by_bound"] == "chars>=bytes/4"


def test_declared_lines_over_cliff_definite():
    out = cliffkit.run_cliff({"harness": "goose", "size": 2001,
                              "unit": "lines"})
    assert out["verdict"] == "TEMP_FILE_TAIL_ONLY"
    assert out["shell_law"]["triggered_by"] == "lines"


def test_declared_lines_under_is_indeterminate():
    # 1 999 lignes : la borne des lignes ne mord pas ; octets et
    # caractères INCONNUS → INDETERMINATE, jamais un optimistic
    # INLINE.
    out = cliffkit.run_cliff({"harness": "goose", "size": 1999,
                              "unit": "lines"})
    assert out["shell_law"]["status"] == "INDETERMINATE_NEEDS_PASTE"


def test_tokens_refused_no_invented_tokenizer():
    try:
        cliffkit.run_cliff({"harness": "goose", "size": 70000,
                            "unit": "tokens"})
        assert False
    except cliffkit.CliffError as e:
        assert e.field == "unit"
        assert "goose" in e.message


# ------------------------------------------------ identité & additif
def test_org_move_redirect_is_known():
    # block/goose MOVED : l'API rend aaif-goose/goose (prouvé par
    # gh api 2026-11-26) — l'alias historique RÉSOUD, la source
    # cite les deux.
    out = cliffkit.run_cliff({"harness": "block/goose", "size": 300_000,
                              "unit": "chars"})
    assert out["harness"] == "goose"
    assert "aaif-goose" in out["source"]


def test_unknown_tool_value_refused_named():
    try:
        cliffkit.run_cliff({"harness": "goose", "size": 1,
                            "unit": "chars", "tool": "browser"})
        assert False
    except cliffkit.CliffError as e:
        assert e.field == "tool"
        assert "extension" in e.expected


def test_all_rows_now_eight_goose_rides():
    out = cliffkit.run_cliff({"result": "hello", "token_limit": 500,
                              "budget": 100000})
    by = {r["harness"]: r for r in out["rows"]}
    assert len(out["rows"]) == 8
    assert by["goose"]["verdict"] == "INLINE"  # 5 chars, 1 ligne
    assert by["goose"]["shell_law"]["survivor_chars"] == 5
    assert by["goose"]["global"]["margin"] == GLOBAL_CHARS - 5
    # le contrat additif : les six de b116 et l'onyx de b118 n'ont
    # PAS bougé (mêmes vecteurs que test_bundle118).
    assert by["claude-code"]["margin"] == 50000 - 5
    assert by["bionic"]["margin"] == 50000 - 5
    assert by["hermes-agent"]["margin"] == 2000000 - 5
    assert by["codex"]["margin"] == 2000 - 5
    assert by["onyx"]["verdict"] == "REFUSED_IN_PASTE"


def test_endpoint_goose_200_and_version():
    r = client.post(ROUTE, json={"harness": "goose", "size": 2500,
                                 "unit": "lines"})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["verdict"] == "TEMP_FILE_TAIL_ONLY"
    assert b["table_version"] == cliffkit.TABLE_VERSION
    assert b["table_version"] == "b120-1"
