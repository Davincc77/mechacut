"""Bundle 5.1 — hashes, encodings, identity: known vectors + strictness."""

import base64
import json

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _twice(url, payload):
    r1 = client.post(url, json=payload)
    r2 = client.post(url, json=payload)
    assert r1.content == r2.content
    return r1


def test_hash_known_vectors():
    assert client.post("/api/v1/hash/digest", json={"data": "abc"}).json(
    )["hex"] == ("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff"
                 "61f20015ad")
    r = client.post("/api/v1/hash/digest",
                    json={"data": "abc", "algo": "md5"})
    assert r.json()["hex"] == "900150983cd24fb0d6963f7d28e17f72"
    r = client.post("/api/v1/hash/digest",
                    json={"data": "abc", "algo": "sha1"})
    assert r.json()["hex"] == "a9993e364706816aba3e25717850c26c9cd0d89d"
    r = client.post("/api/v1/hash/digest",
                    json={"data": "aGVsbG8=", "input_kind": "base64"})
    assert r.json()["hex"] == ("2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c"
                               "1fa7425e73043362938b9824")  # sha256("hello")


def test_enc_roundtrip_and_strictness():
    r = _twice("/api/v1/enc/base64", {"text": "hello"})
    assert r.json()["result"] == "aGVsbG8="
    r = client.post("/api/v1/enc/base64", json={"text": "aGVsbG8=",
                                                "op": "decode"})
    assert r.json()["result"] == "hello"
    r = client.post("/api/v1/enc/base64",
                    json={"text": "hello", "variant": "hex"})
    assert r.json()["result"] == "68656c6c6f"
    r = client.post("/api/v1/enc/base64",
                    json={"text": "aGVsbG8=", "op": "decode",
                          "variant": "base64url"})
    assert r.json()["result"] == "hello"  # urlsafe accepted everywhere
    r = client.post("/api/v1/enc/base64", json={"text": "!!!!",
                                                "op": "decode"})
    assert r.status_code == 400  # strict: no lenient silent empty


def test_jwt_decode():
    tok = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." + base64.urlsafe_b64encode(
        json.dumps({"sub": "42", "iat": 1700000000,
                    "exp": 1700003600}).encode()).rstrip(b"=").decode() + ".sig"
    r = _twice("/api/v1/jwt/decode", {"token": tok})
    b = r.json()
    assert b["header"]["alg"] == "HS256"
    assert b["payload"]["sub"] == "42"
    assert b["verified"] is False
    assert b["iat_iso"] == "2023-11-14T22:13:20+00:00"
    assert client.post("/api/v1/jwt/decode",
                       json={"token": "nope"}).status_code == 400


def test_uuid_determinism():
    r = _twice("/api/v1/id/uuid", {"op": "v5",
                                   "name": "https://mechacut.studio"})
    assert r.json()["uuid"] == "7ad923e8-7764-502f-a105-e7cfc5f23674"
    assert r.json()["urn"].startswith("urn:uuid:")
    r = client.post("/api/v1/id/uuid", json={"op": "v4_seeded",
                                             "seed": "davincc"})
    u1 = r.json()["uuid"]
    r2 = client.post("/api/v1/id/uuid", json={"op": "v4_seeded",
                                              "seed": "davincc"})
    assert r2.json()["uuid"] == u1  # seeded, not random
    r = client.post("/api/v1/id/uuid", json={"op": "v7",
                                             "at": "2026-11-20T08:00:00Z"})
    b = r.json()
    # v7 layout: first 48 bits are the millisecond timestamp
    assert int(b["uuid"].replace("-", "")[:12], 16) == b["timestamp_ms"]
    assert b["version"] == 7
    r = client.post("/api/v1/id/uuid", json={"op": "v7"})
    assert r.status_code == 400  # wall clock refused


def test_slug():
    r = _twice("/api/v1/id/slug", {"text": "Café Crème — 2026 !"})
    assert r.json()["slug"] == "cafe-creme-2026"
    r = client.post("/api/v1/id/slug", json={"text": "the quick brown fox",
                                             "max_len": 10})
    b = r.json()
    assert b["slug"] == "the-quick" and b["truncated"] is True
    r = client.post("/api/v1/id/slug", json={"text": "A B", "sep": "_"})
    assert r.json()["slug"] == "a_b"


def test_fingerprint_order_invariant():
    r1 = client.post("/api/v1/fingerprint", json={"value": {"b": 1,
                                                            "a": [1, 2]}})
    r2 = client.post("/api/v1/fingerprint", json={"value": {"a": [1, 2],
                                                            "b": 1}})
    assert r1.json()["sha256"] == r2.json()["sha256"]
    assert r1.json()["canonical"] == '{"a":[1,2],"b":1}'
    r = client.post("/api/v1/fingerprint",
                    json={"value": "name,age\nBob,42\n", "kind": "csv"})
    assert r.json()["rows"] == 1
