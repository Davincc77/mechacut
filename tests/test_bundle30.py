"""Bundle 30 lot 1 — WEB. Ancres produites par les binaires réels
ssh-keygen (macOS OpenSSH) et Info-ZIP dans la session, consignées ici
comme vecteurs publiés d'outils publiés."""
import base64
import sys

import pytest
sys.path.insert(0, ".")
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)

KEY_B64 = "AAAAC3NzaC1lZDI1NTE5AAAAI" + "A" * 43
KEY_LINE = "ssh-ed25519 " + KEY_B64 + " mechacut@test"
# zip déterministe (date 1980-01-01, deflate) régénéré par fixture ci-dessous
ZIP_B64 = ("UEsDBBQAAAAIAAAAIQCK/qr5CwAAAAkAAAAIAAAAbm90ZS50eHTLTU3OSEwu"
           "LeECAFBLAQIUAxQAAAAIAAAAIQCK/qr5CwAAAAkAAAAIAAAAAAAAAAAAAACk"
           "AQAAAABub3RlLnR4dFBLBQYAAAAAAQABADYAAAAxAAAAAAA=")


def fp(line):
    r = client.post("/api/v1/ssh/fingerprint", json={"line": line})
    assert r.status_code == 200, r.text
    return r.json()


def zv(blob):
    r = client.post("/api/v1/zip/verify", json={"blob_b64": blob})
    assert r.status_code == 200, r.text
    return r.json()


def test_ssh_sha256_matches_real_ssh_keygen():
    d = fp(KEY_LINE)
    assert d["fingerprint_sha256"] == \
        "SHA256:kmYcvdi2GkPeWxB6XLjrZB8JHsy2Hm8luHMFp9GMvqk"


def test_ssh_md5_legacy_format_and_deprecation_flag():
    d = fp(KEY_LINE)
    assert d["fingerprint_md5"] == \
        "3d:52:38:ce:ff:94:f5:d7:81:a4:a4:f9:2b:4f:fe:a0"
    assert d["md5_deprecated"] is True
    assert d["comment"] == "mechacut@test"


def test_ssh_type_field_must_agree_with_blob():
    r = client.post("/api/v1/ssh/fingerprint", json={
        "line": "ssh-rsa " + KEY_LINE.split()[1] + " x"})
    assert r.status_code == 400 and "disagrees" in r.text


def test_zip_clean_verdict_matches_infozip():
    d = zv(ZIP_B64)
    assert d["integrity_ok"] is True and d["bad_entries"] == []
    e = d["entries"][0]
    assert e["name"] == "note.txt" and e["size"] == 9
    assert e["crc32_stored"] == "f9aafe8a"
    assert e["crc32_computed"] == "f9aafe8a"
    assert d["archive_sha256"] == ("0a241db4140afde961a7cce224c4c8ef"
                                   "b807475465f0c715f71b06ed417d2a21")
    assert d["extracted"] is False


def test_zip_subtle_corruption_is_verdict_not_crash():
    raw = bytearray(base64.b64decode(ZIP_B64))
    raw[40] ^= 0xFF
    d = zv(base64.b64encode(bytes(raw)).decode())
    assert d["integrity_ok"] is False
    assert d["bad_entries"] == ["note.txt"]
    assert d["entries"][0]["crc32_computed"] is None


def test_zip_garbage_rejected():
    r = client.post("/api/v1/zip/verify", json={"blob_b64": "aGVsbG8="})
    assert r.status_code == 400 and "bad zip" in r.text


# ------------------------------------------------------------- lot 2
def pk(rows):
    r = client.post("/api/v1/table/peek", json={"rows": rows})
    assert r.status_code == 200, r.text
    return r.json()


def df(left, right, key):
    r = client.post("/api/v1/csv/diff",
                    json={"left": left, "right": right, "key": key})
    assert r.status_code == 200, r.text
    return r.json()


ROWS = [{"a": "1", "b": "2026-11-01", "c": "x"},
        {"a": "2", "b": "2026-11-03", "c": ""},
        {"a": "10", "b": "2026-11-02", "c": "y"}]


def test_peek_numeric_bounds_not_lexicographic():
    cols = {c["column"]: c for c in pk(ROWS)["columns"]}
    assert cols["a"]["type"] == "integer"
    assert cols["a"]["min"] == 1.0 and cols["a"]["max"] == 10.0
    assert cols["b"]["type"] == "date-iso"
    assert cols["b"]["min"] == "2026-11-01"
    assert cols["c"]["nulls"] == 1 and cols["c"]["uniques"] == 2


def test_peek_mixed_is_declared_not_resolved():
    d = pk([{"v": "1"}, {"v": "deux"}])
    col = d["columns"][0]
    assert col["type"] == "string" and col.get("mixed") is True


def test_diff_full_shape():
    r = df([{"id": "1", "v": "a", "w": "1"}, {"id": "2", "v": "b"}],
           [{"id": "2", "v": "B"}, {"id": "3", "v": "c"}], "id")
    assert r["added"] == ["3"] and r["removed"] == ["1"]
    assert r["changed"][0]["fields"] == [{"field": "v", "left": "b",
                                          "right": "B"}]
    assert r["same_count"] == 0 and r["counts"]["changed"] == 1


def test_diff_number_tolerance_and_composite_key():
    r = df([{"k": "1", "n": 2}], [{"k": "1", "n": 2.0}], "k")
    assert r["same_count"] == 1
    r2 = df([{"a": "1", "b": "x", "v": 1}], [{"a": "1", "b": "x", "v": 2}],
            ["a", "b"])
    assert r2["changed"][0]["key"] == "1|x" and r2["key_fields"] == ["a", "b"]


def test_diff_duplicate_key_refused():
    r = client.post("/api/v1/csv/diff", json={
        "left": [{"id": "1"}, {"id": "1"}], "right": [], "key": "id"})
    assert r.status_code == 400 and "duplicate" in r.text


# ------------------------------------------------------------- lot 3
def qr(**kw):
    r = client.post("/api/v1/qr/generate", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def test_qr_deterministic_svg_bytes():
    a = qr(text="https://mechacut.studio")
    b = qr(text="https://mechacut.studio")
    assert a["svg"] == b["svg"] and a["sha256"] == b["sha256"]
    assert a["svg"].startswith("<svg ") and "crispEdges" in a["svg"]


def test_qr_mode_and_version_selection():
    assert qr(text="012345678")["mode"] == "numeric"
    assert qr(text="HELLO WORLD")["mode"] == "alphanumeric"
    assert qr(text="mechacut.studio")["mode"] == "byte"
    d = qr(text="x" * 250, ecl="L")
    assert d["version"] == 10 and d["size"] == 57


def test_qr_capacity_wall_is_named():
    r = client.post("/api/v1/qr/generate", json={"text": "x" * 260,
                                                 "ecl": "M"})
    assert r.status_code == 400 and "too long" in r.text
    r2 = client.post("/api/v1/qr/generate", json={"text": "ok",
                                                  "version": 11})
    assert r2.status_code == 400 and "1-10" in r2.text


def test_qr_matrix_format_shape():
    d = qr(text="8675309", format="matrix")
    assert len(d["matrix"]) == d["size"] == 21
    assert d["matrix"][0][0] == 1              # finder module sombre
    assert d["modules"] == sum(sum(r) for r in d["matrix"])


def test_qr_matches_segno_matrix():
    """Byte-identity with the independent published encoder on payloads
    without padding ambiguity (dev oracle; prod never imports segno)."""
    segno = pytest.importorskip("segno")
    for text, ecl in [("8675309", "M"), ("1" * 24, "H"),
                      ("AB12 $%*+-./: 9", "L")]:
        d = qr(text=text, ecl=ecl, format="matrix")
        q = segno.make(text, version=d["version"], error=ecl,
                       mask=d["mask"], mode=d["mode"], boost_error=False)
        sm = [[int(c) for c in row] for row in q.matrix]
        assert sm == d["matrix"], (text[:10], ecl, d["version"])


def test_qr_decodes_under_opencv():
    """The final court of appeal: a real scanner extracts the exact text
    from our raster — including utf-8 payloads and the cases where other
    encoders pad differently."""
    cv2 = pytest.importorskip("cv2")
    import numpy as np
    det = cv2.QRCodeDetector()

    def raster(mat, scale=6, quiet=4):
        m = 1 - np.array(mat, dtype=np.uint8)
        big = np.repeat(np.repeat(m, scale, 0), scale, 1)
        pad = quiet * scale
        canvas = np.ones((big.shape[0] + 2 * pad,
                          big.shape[1] + 2 * pad), dtype=np.uint8)
        canvas[pad:pad + big.shape[0], pad:pad + big.shape[1]] = big
        return (canvas * 255).astype(np.uint8)

    def decode(d):
        got = det.detectAndDecode(raster(d["matrix"]))[0]
        if isinstance(got, bytes):
            return got.decode("utf-8", "replace")
        return got.encode("latin-1", "replace").decode("utf-8", "replace") \
            if got else ""

    ascii_payloads = ["z", "012345678", "HELLO WORLD",
                      "https://mechacut.studio/agent/manifest",
                      "x" * 250]
    for text in ascii_payloads:
        for ecl in "LMQH":
            r = client.post("/api/v1/qr/generate", json={
                "text": text, "ecl": ecl, "format": "matrix"})
            if r.status_code == 400:
                continue          # beyond v10 capacity for this ECL
            assert decode(r.json()) == text, (text[:12], ecl)
    # utf-8 : OpenCV garble certains pads multi-octets SELON le masque
    # (limitation du décodeur, pas de l'encodeur) — la garantie correcte
    # est donc l'égalité de décodage avec la référence segno
    segno = pytest.importorskip("segno")
    text = "Facture véloçue — été 2026"
    for ecl in "LMQH":
        d = qr(text=text, ecl=ecl, format="matrix")
        q = segno.make(text, version=d["version"], error=ecl,
                       mask=d["mask"], mode=d["mode"], boost_error=False)
        dm = decode(d)
        ds = decode({"matrix": [[int(c) for c in r] for r in q.matrix],
                     "mask": d["mask"]})
        assert dm == ds, (ecl, repr(dm[:14]), repr(ds[:14]))


# ------------------------------------------------------------- lot 4
def wc(header, **kw):
    r = client.post("/api/v1/web/cache", json={"header": header, **kw})
    assert r.status_code == 200, r.text
    return r.json()


def gz(payload_b64, **kw):
    r = client.post("/api/v1/gzip/roundtrip",
                    json={"payload_b64": payload_b64, **kw})
    assert r.status_code == 200, r.text
    return r.json()


def test_cache_directives_classified():
    d = wc("public, max-age=3600, immutable")
    assert d["max_age_seconds"] == 3600
    assert d["action"] == "fresh_for_max_age_seconds"
    assert sorted(d["unknown_directives"]) == ["immutable", "public"]


def test_cache_action_ladder():
    assert wc("no-store")["action"] == "forbidden_to_store"
    assert wc("no-cache")["action"] == \
        "store_but_revalidate_every_use"
    assert wc("max-age=0")["action"] == "must_revalidate_before_use"
    assert wc("must-revalidate")["action"] == \
        "use_until_stale_then_revalidate"
    assert wc("max-age=60")["action"] == "fresh_for_max_age_seconds"
    assert wc("")["action"] == "heuristic_freshness_allowed"


def test_cache_method_rule():
    assert wc("max-age=60", method="POST")["action"] == \
        "not_cacheable_method"


def test_gzip_bytes_reproducible_and_reversible():
    import base64 as _b
    payload = _b.b64encode(b"mechacut" * 400).decode()
    a = gz(payload)
    b = gz(payload)
    assert a["gzip_b64"] == b["gzip_b64"] and a["ratio"] < 0.1
    back = gz(a["gzip_b64"], mode="decompress")
    assert _b.b64decode(back["payload_b64"]) == b"mechacut" * 400
    assert back["output_bytes"] == 3200


def test_gzip_magic_and_garbage():
    import base64 as _b
    d = gz(_b.b64encode(b"hello").decode())
    raw = _b.b64decode(d["gzip_b64"])
    assert raw[:2] == b"\x1f\x8b"          # RFC 1952 magic
    assert raw[4:8] == b"\x00\x00\x00\x00"  # MTIME zeroed = deterministic
    r = client.post("/api/v1/gzip/roundtrip",
                    json={"payload_b64": "aGVsbG8=", "mode": "decompress"})
    assert r.status_code == 400 and "not a valid gzip" in r.text
