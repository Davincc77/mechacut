"""Bundle 33 — web/cert (certkit). L'oracle est openssl, appelé DANS le
test : rien de recopié de mémoire. Statuts pilotés par as_of (explicite
= rejouable), jamais par la date du jour."""
import subprocess
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, ".")
import certkit
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)
CERTS = Path(__file__).resolve().parent / "certs"


def pem(name):
    return (CERTS / name).read_text()


def ossl_field(name):
    txt = subprocess.run(
        ["openssl", "x509", "-in", str(CERTS / name), "-noout",
         "-serial", "-startdate", "-enddate", "-subject", "-issuer",
         "-fingerprint", "-sha256"],
        capture_output=True, text=True, check=True).stdout
    f = {}
    for line in txt.splitlines():
        k, _, v = line.partition("=")
        f[k.strip()] = v.strip()
    return f


def iso(ossl_date):
    return datetime.strptime(ossl_date,
                             "%b %d %H:%M:%S %Y %Z").strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def test_rsa_leaf_matches_openssl_field_by_field():
    r = certkit.lint(pem("leaf_rsa.pem"), as_of="2026-12-01")
    c = r["certificates"][0]
    f = ossl_field("leaf_rsa.pem")
    assert c["serial_hex"] == f["serial"].lower()
    assert c["not_before"] == iso(f["notBefore"])
    assert c["not_after"] == iso(f["notAfter"])
    assert c["subject"] == "C=LU, O=Mechacut, CN=mechacut.studio"
    assert c["sha256_fingerprint"] == \
        f["SHA256 Fingerprint"].lower().replace(":", "")
    assert c["sig_alg"] == "sha256WithRSA"
    assert sorted(c["san"]["dns"]) == sorted(
        ["mechacut.studio", "www.mechacut.studio"])
    assert c["san"]["ip"] == ["203.0.113.7"]
    assert c["status"] == "valid" and c["days_to_expiry"] == 20
    assert c["self_signed"] is True


def test_ecdsa_and_sha1_alg_names():
    e = certkit.lint(pem("leaf_ec.pem"))["certificates"][0]
    assert e["sig_alg"] == "ecdsa-with-SHA256"
    assert not e["sig_deprecated"]
    s = certkit.lint(pem("leaf_sha1.pem"))["certificates"][0]
    assert s["sig_alg"] == "sha1WithRSA" and s["sig_deprecated"]
    assert any("deprecated" in w for w in s["warnings"])


def test_statuses_via_as_of_only():
    r = certkit.lint(pem("leaf_rsa.pem"), as_of="2000-01-01")
    assert r["certificates"][0]["status"] == "not_yet_valid"
    r2 = certkit.lint(pem("leaf_rsa.pem"), as_of="2030-01-01")
    c = r2["certificates"][0]
    assert c["status"] == "expired" and c["days_to_expiry"] < 0


def test_ca_flag_and_chain_shape():
    r = certkit.lint(pem("chain2.pem"))
    assert r["count"] == 2
    leaf, ca = r["certificates"]
    assert ca["ca"] is True
    assert leaf["ca"] is None or leaf["ca"] is False
    assert any("CA certificate" in w for w in ca["warnings"])
    assert r["chain"]["all_shapes_match"] is True
    assert leaf["issuer"] == ca["subject"]
    assert ca["self_signed"] is True and leaf["self_signed"] is False


def test_garbage_refused_by_name():
    try:
        certkit.lint("juste du texte")
        raise AssertionError("accepte !")
    except certkit.CertError as e:
        assert "BEGIN CERTIFICATE" in str(e)
    bad = pem("leaf_rsa.pem").replace("MIID", "M#*D", 1)
    try:
        certkit.lint(bad)
        raise AssertionError("base64 invalide accepte !")
    except certkit.CertError as e:
        assert "base64" in str(e)
    t = pem("leaf_rsa.pem")
    cut = t[:len(t) // 2] + "-----END CERTIFICATE-----\n"
    try:
        certkit.lint(cut)
        raise AssertionError("DER tronque accepte !")
    except certkit.CertError as e:
        assert "corrupt" in str(e) or "truncated" in str(e)


def test_scope_note_always_present():
    r = certkit.lint(pem("leaf_rsa.pem"))
    assert "NOT signature-verified" in r["scope_note"]
    assert r["as_of_was_supplied"] is False
    assert "T" in r["evaluated_at"]


def test_endpoint_and_canon():
    r = client.post("/api/v1/web/cert", json={
        "pem": pem("leaf_rsa.pem"), "as_of": "2026-12-01"})
    assert r.status_code == 200
    d = r.json()
    assert d["certificates"][0]["days_to_expiry"] == 20
    assert sorted(d["certificates"][0]["san"]["dns"]) == [
        "mechacut.studio", "www.mechacut.studio"]
    body = {k: v for k, v in d.items() if k != "sha256"}
    assert d["sha256"] == main.canon(body)
    r2 = client.post("/api/v1/web/cert", json={"pem": "rien"})
    assert r2.status_code == 400 and "BEGIN CERTIFICATE" in r2.text
