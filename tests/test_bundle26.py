"""Bundle 26 — LEAK. secret/scan + text/redact.
Les fixtures sont ASSEMBLÉES à l'exécution (fragments séparés) : aucune
chaîne complète de forme-connue n'existe dans le source — notre propre
hygiène applique notre propre thèse."""
import sys
sys.path.insert(0, ".")
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)

_P1 = "s" + "k" + "-"
_P2 = "g" + "hp" + "_"
SK = _P1 + "A" * 28
GHP = _P2 + "B" * 36
CARD = "4111 1111 1111 1111"
SEED = " ".join(["abandon"] * 11 + ["about"])


def scan(t, kinds=None):
    r = client.post("/api/v1/secret/scan",
                    json={"text": t} if not kinds
                    else {"text": t, "kinds": kinds})
    assert r.status_code == 200, r.text
    return r.json()


def red(t):
    r = client.post("/api/v1/text/redact", json={"text": t})
    assert r.status_code == 200, r.text
    return r.json()


def test_scan_finds_both_at_positions():
    t = "conf openai " + SK + " et github " + GHP + chr(10)
    d = scan(t)
    kinds = {f["kind"] for f in d["findings"]}
    assert "openai-key" in kinds and "github-token" in kinds
    for f in d["findings"]:
        head = SK if f["kind"] == "openai-key" else GHP
        assert f["at"] == t.find(head)
        assert t[f["at"]:f["at"] + f["length"]] == head


def test_scan_luhn_gate():
    d = scan("numéro de commande 4111 1111 1111 1112")
    assert all(f["kind"] != "visa" for f in d["findings"])
    d2 = scan("carte " + CARD)
    assert any(f["kind"] == "visa" for f in d2["findings"])


def test_scan_bip39_real_checksum():
    assert "bip39-seed-valid" in [f["kind"] for f in
                                  scan(SEED)["findings"]]
    d2 = scan(" ".join(["abandon"] * 11 + ["wolf"]))
    assert "bip39-seed-bad_checksum" in [f["kind"] for f in
                                         d2["findings"]]


def test_scan_never_echoes_the_value():
    d = scan("ma clé " + SK)
    blob = str(d)
    assert SK not in blob and SK[8:] not in blob
    assert d["findings"][0]["preview"].endswith("AA")


def test_redact_stable_numbering_and_no_mapping():
    t = "a " + SK + " b " + GHP + " c"
    d = red(t)
    assert "[OPENAI_KEY_1]" in d["redacted"]
    assert "[GITHUB_TOKEN_1]" in d["redacted"]
    assert "AAAA" not in d["redacted"]
    d2 = red(t)
    assert d["redacted"] == d2["redacted"]
    assert d["sha256"] == d2["sha256"]


def test_redact_seed_wholesale():
    d = red(SEED + " ne pas partager")
    assert "[SEED_PHRASE]" in d["redacted"]
    assert "abandon" not in d["redacted"]


def test_scan_clean_says_clean():
    d = scan("rien de sensible ici, juste des mots 12345")
    assert d["clean"] is True and d["count"] == 0
