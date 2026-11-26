# -*- coding: utf-8 -*-
"""bundle118 — CLIFFKIT ligne ONYX (alternance DEV, rang 1 de la file
b117). La douleur, relue AU SOURCE 2026-11-26 : onyx-dot-app/onyx
#11007 (open 2026-05-12) — run_llm_loop appends tool_response.llm_
facing_response VERBATIM, AUCUN budget ; le fix proposé nomme
MAX_TOOL_RESULT_TOKENS défaut 20 000 + notice [TRUNCATED: ...], il
vit dans PR #14586 TOUJOURS OUVERTE (non merged, re-vérifiée ce
matin). #15119 et #16312 marqués DOUBLES de #11007 le 20-nov par
justin-tahara — la douleur se REPORTE, pas se répare.

LA GRAMMAIRE DE CETTE LIGNE : onyx ne COUPE RIEN. Le cliff, c'est
la pièce restante de TON fenêtre, comptée en tokens par le PROVIDER.
D'où trois lois testées ici, attendues CALCULÉES À LA MAIN :

1. Le vecteur publié rejoué : #16312 dit « Required: 2032226,
   Available: 843719 » → marge = 843719 − 2032226 = −1 188 507
   (2 032 226 − 843 719 = 1 188 507, posés à la main) et le verdict
   n'est PAS une coupe : PROVIDER_REQUEST_REJECTED, la requête
   entière meurt, marker aucun (le [TRUNCATED] ne vit que dans la
   PROPOSITION).
2. Le 20 000 est un STATUT, jamais une loi : passer context_room
   = 20000 donne cliff = 20000 parce que C'EST TOI qui l'as dit ;
   retirer l'argument = REFUSED_NEEDS_ARGUMENT nommé. Le module
   n'a AUCUNE constante onyx.
3. Paste refusé : compter des tokens sans le tokenizer du provider
   EST la devinette que ce kit tue → REFUSED_IN_PASTE, et la
   déclinaison chars/bytes/lines = refus nommé field=unit.

Contrat : les SIX lignes de b116 ne bougent pas (verdicts rejoués à
la main ci-dessous) ; la table VERSIONNE (b118-1) et le mode
all-rows rend maintenant SEPT lignes dont une REFUSED_IN_PASTE —
additif, jamais réordonné.
"""
import cliffkit
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)

ROUTE = "/api/v1/agent/result-cliff"


# ------------------------------------------------------- vecteur publié
def test_16312_replay_named_refusal_vector():
    """Le nombre EXACT du fil : Required 2032226 / Available 843719.
    Marge calculée à la main : 843719 − 2032226 = −1 188 507."""
    out = cliffkit.run_cliff({"harness": "onyx", "size": 2032226,
                              "unit": "tokens",
                              "context_room": 843719})
    assert out["verdict"] == "PROVIDER_REQUEST_REJECTED"
    assert out["crossed"] is True
    assert out["margin"] == 843719 - 2032226
    assert out["margin"] == -1188507
    # rien n'a été coupé : pas de marqueur rendu, le message ne
    # ment pas — c'est le provider qui refuse la REQUÊTE.
    assert out["message_lies"] is False
    assert "TRUNCATED" in out["marker"] and "PROPOSED" in out["marker"]
    assert "cliff" in out and out["cliff"] == 843719


def test_20000_lives_as_status_never_as_law():
    """Le défaut PROPOSÉ n'est PAS la table : si l'appelant donne
    20 000 comme pièce, le cliff = 20 000 PAR CE QU'IL A DIT ;
    s'il ne donne rien, refus nommé. Aucune constante onyx dans le
    module (grep gardé ci-dessous)."""
    given = cliffkit.run_cliff({"harness": "onyx", "size": 25000,
                                "unit": "tokens",
                                "context_room": 20000})
    assert given["cliff"] == 20000
    assert given["crossed"] is True
    assert given["margin"] == 20000 - 25000  # −5 000, à la main
    missing = cliffkit.run_cliff({"harness": "onyx", "size": 25000,
                                  "unit": "tokens"})
    assert missing["verdict"] == "REFUSED_NEEDS_ARGUMENT"
    assert missing["ask"] == "context_room"
    assert "PROPOSED" in missing["reason"]
    # le repair porte la distinction qui compte : PROPOSÉ ≠ DÉPLOYÉ
    row = cliffkit.HARNESSES["onyx"]["surfaces"]["result"]
    for token in ("PROPOSED", "#14586", "#11007", "2026-11-20"):
        assert token in row["repair"], token


def test_boundary_equal_is_not_crossed():
    """cmp « gt » : exactement la pièce = ça passe (INLINE), marge 0
    — la loi du « longer than » déjà posée chez claude/bionic."""
    out = cliffkit.run_cliff({"harness": "onyx", "size": 128000,
                              "unit": "tokens",
                              "context_room": 128000})
    assert out["verdict"] == "INLINE"
    assert out["margin"] == 0
    assert out["crossed"] is False


# ------------------------------------------------------- refus nommés
def test_paste_is_refused_for_the_no_cut_row():
    """Pas de tokenizer provider ici, pas de coupe locale à rejouer :
    la pâte REFUSE PAR LE NOM, et dit quoi passer à la place."""
    out = cliffkit.run_cliff({"harness": "onyx",
                              "result": "abc", "context_room": 10})
    assert out["verdict"] == "REFUSED_IN_PASTE"
    assert out["ask"] == "context_room"
    assert "tokenizer" in out["reason"]


def test_declared_other_unit_refused_by_name():
    try:
        cliffkit.run_cliff({"harness": "onyx", "size": 5000,
                            "unit": "chars", "context_room": 10000})
        assert False
    except cliffkit.CliffError as e:
        assert e.field == "unit"
        assert "REFUSED" in e.message


def test_aliases_and_closed_table():
    assert cliffkit.resolve_harness("Onyx") == "onyx"
    assert cliffkit.resolve_harness("onyx-dot-app") == "onyx"
    try:
        cliffkit.run_cliff({"harness": "gpt-shell", "size": 1,
                            "unit": "chars"})
        assert False
    except cliffkit.CliffError as e:
        assert "onyx" in e.expected


# ------------------------------------------------------- contrat additif
def test_six_old_rows_unmoved():
    """La table a grandi, les SIX lignes de b116 n'ont PAS bougé
    (verdicts + marges recalculés à la main, mêmes vecteurs que
    bundle116) : additif ne veut rien dire d'autre."""
    out = cliffkit.run_cliff({"result": "hello", "token_limit": 500,
                              "budget": 100000, "surface": "result"})
    by = {r["harness"]: r for r in out["rows"]}
    assert by["claude-code"]["margin"] == 50000 - 5
    assert by["bionic"]["margin"] == 50000 - 5
    assert by["hermes-agent"]["margin"] == 2000000 - 5
    assert by["codex"]["verdict"] == "INLINE"
    assert by["codex"]["margin"] == 2000 - 5
    assert by["vscode"]["verdict"] == "UNPUBLISHED_THRESHOLD"
    assert by["rakazo"]["verdict"] == "INLINE"
    # la ligne neuve : refuse la pâte, ne devine JAMAIS un token
    assert by["onyx"]["verdict"] == "REFUSED_IN_PASTE"
    assert len(out["rows"]) == 8  # b120 : +goose, la table NE BIGARRE
    # PAS — additif, les sept de b118 rejouées à l'identique.


def test_no_constant_for_onyx_lives_in_the_module():
    """Garde : le nombre PROPOSÉ vit en PROSE de statut, jamais
    comme cliff appliqué sans l'argument de l'appelant."""
    import re
    row = open("cliffkit.py", encoding="utf-8").read()
    row = row[row.index('"onyx": {'):row.index("HARNESSES = _rows()")]
    assert '"cliff": None' in row
    assert re.search(r'"cliff":\s*[0-9]', row) is None
    assert re.search(r"\b20000\b", row) is None


# ------------------------------------------------------- endpoint
def test_endpoint_onyx_200_with_version_and_sha():
    r = client.post(ROUTE, json={"harness": "onyx", "size": 30000,
                                 "unit": "tokens",
                                 "context_room": 128000})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["verdict"] == "INLINE"
    assert b["crossed"] is False
    assert b["margin"] == 128000 - 30000  # 98 000, à la main
    assert b["table_version"] == cliffkit.TABLE_VERSION == "b120-1"
    assert b["as_of"] == "2026-11-26"
    assert "sha256" in b


def test_endpoint_byte_identical_twice():
    body = {"harness": "onyx", "size": 2032226, "unit": "tokens",
            "context_room": 843719}
    a = client.post(ROUTE, json=body).content
    b = client.post(ROUTE, json=body).content
    assert a == b


def test_endpoint_paste_onyx_names_the_refusal():
    r = client.post(ROUTE, json={"harness": "onyx",
                                 "result": "hello",
                                 "context_room": 10})
    assert r.status_code == 200
    assert r.json()["verdict"] == "REFUSED_IN_PASTE"


# ------------------------------------------------------- manifest
def test_manifest_unchanged_by_a_row():
    """Une LIGNE de table n'est pas un OUTIL : le manifest reste
    sous son budget et ne gagne aucune ligne neuve."""
    import routing
    txt = routing.manifest_text(main.app.version)
    assert "agent_resultcliff" in txt
    assert len(txt.encode("utf-8")) < 9000
    assert txt.count("result-cliff") == 1
