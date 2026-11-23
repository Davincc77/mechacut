# -*- coding: utf-8 -*-
"""Bundle 91 — le splitter on-chain : preuve EVM + mécanisme serveur.

Le contrat vit hors du dépôt pour ses tests : à la racine, notre eth.py
éclipse le package py-evm (contrainte d'espace de noms, écrite dans
scripts/splitter_proof.py). Le subprocess lance donc la preuve depuis
un cwd neutre et le test asserte CHAMP par champ ce qu'elle imprime —
la chaîne de confiance : git -> artefact compilé -> preuve -> nombres.

S7 : côté serveur, le payTo du challenge devient le splitter enregistré
pour CETTE route (docs/proposals/splitters.json, git), avec retombée
nommée sur l'adresse d'environnement si le fichier absente ou si son
adresse est mal formée. Un payTo faux ne se devine pas, il se refuse.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main
import payments

REPO = Path(__file__).resolve().parent.parent
ART = REPO / "contracts" / "build" / "artifacts.json"

GOOD = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
BAD = "0x5aaeb6053f3e94c9b9a09f33669435e7ef1beae"  # checksum brisé


@pytest.fixture(scope="module")
def proof():
    pytest.importorskip("web3")
    # eth_tester N'EST PAS importable depuis la racine du repo : notre
    # eth.py éclipse le package py-evm « eth ». La preuve tourne donc
    # en subprocess -I (isolé, pas de cwd sur sys.path) avec un
    # PYTHONPATH neutre — la contrainte est écrite, pas cachée.
    probe = subprocess.run(
        [sys.executable, "-I", "-c", "import eth_tester"],
        cwd="/tmp", capture_output=True, text=True)
    if probe.returncode != 0:
        pytest.skip("eth_tester absent de l'environnement isolé")
    env = dict(os.environ, PYTHONPATH="/tmp")
    out = subprocess.run(
        [sys.executable, "-I", str(REPO / "scripts" / "splitter_proof.py"),
         str(ART)],
        cwd="/tmp", capture_output=True, text=True, timeout=600, env=env)
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_s1_create2_respects_git(proof):
    assert proof["s1_predicted_eq_deployed"] is True


def test_s2_terms_are_bound_not_trusted(proof):
    assert proof["s2_idempotent"] is True
    assert proof["s2_mismatch_reverted"] is True


def test_s3_the_split_is_exact_money(proof):
    assert proof["s3_payout"] == 500_000
    assert proof["s3_treasury"] == 500_000
    assert proof["s3_splitter_empty"] == 0


def test_s4_odd_amounts_round_in_favour_of_neither_side(proof):
    # deux flush cumulés : $1 pile + 999_999 impair
    assert proof["s4_odd_payout_total"] == 999_999   # 500000 + 499999
    assert proof["s4_odd_treasury_total"] == 1_000_000  # 500000 + 500000
    assert proof["s4_odd_splitter_empty"] == 0


def test_s5_eth_cannot_enter(proof):
    assert proof["s5_eth_rejected"] is True


def test_s6_one_tool_one_identity(proof):
    assert proof["s6_distinct"] is True
    assert proof["s7_invariants"] is True


def test_s7_payto_follows_the_registry_file(tmp_path, monkeypatch):
    splitter = GOOD
    f = tmp_path / "splitters.json"
    monkeypatch.setenv("MECHACUT_PAY_TO", "0x" + "ab" * 20)
    monkeypatch.setenv("MECHACUT_SPLITTERS", str(f))
    # pas de fichier -> environnement, à l'identique d'hier
    assert payments.pay_to_for("/api/v1/chart") == "0x" + "ab" * 20
    assert payments.splitter_note("/api/v1/chart") == "fallback_env"
    f.write_text(json.dumps({"/api/v1/chart": splitter}))
    assert payments.pay_to_for("/api/v1/chart") == splitter
    assert payments.splitter_note("/api/v1/chart") == "splitter_registered"
    # adresse mal formée -> ignorée NOMMÉE, jamais servie
    f.write_text(json.dumps({"/api/v1/chart": BAD}))
    assert payments.pay_to_for("/api/v1/chart") == "0x" + "ab" * 20
    assert payments.splitter_note("/api/v1/chart") == "ignored_grammar"


def test_s7b_challenge_carries_the_splitter(tmp_path, monkeypatch):
    f = tmp_path / "splitters.json"
    f.write_text(json.dumps({"/api/v1/chart": GOOD}))
    monkeypatch.setenv("MECHACUT_PAY_TO", "0x" + "ab" * 20)
    monkeypatch.setenv("MECHACUT_SPLITTERS", str(f))
    c = TestClient(main.app)
    r = c.post("/api/v1/chart", json={"data": [{"x": 1}]})
    assert r.status_code == 402
    acc = r.json()["accepts"][0]
    assert acc["payTo"] == GOOD
    assert acc["network"] == "base" and acc["scheme"] == "exact"


def test_b91_files_ship():
    assert (REPO / "contracts" / "splitter.sol").exists()
    assert json.loads(ART.read_text())["USDCSplitter"]["bytecode"]
    art2 = json.loads(ART.read_text())
    assert "SplitterFactory" in art2 and "MockUSDC" in art2
    assert (REPO / "docs" / "proposals" / "splitters.json").exists()
    assert (REPO / "docs" / "proposals" / "PAYOUTS.md").exists()
    reg = (REPO / "docs" / "proposals" / "registry.jsonl")
    assert reg.exists()  # COPY dir embarqué, vérifié au deploy test
