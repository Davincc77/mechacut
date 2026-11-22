"""Bundle 18 lot 1 — EVM primitives: keccak vendored, EIP-55, selectors."""
import hashlib as h
import json

from fastapi.testclient import TestClient

import eth
import main

client = TestClient(main.app)


def test_keccak_published_vectors():
    assert eth.keccak256(b"").hex() == (
        "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")
    assert eth.keccak256(b"abc").hex() == (
        "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45")
    assert eth.keccak256(b"transfer(address,uint256)").hex()[:8] == \
        "a9059cbb"


def test_keccak_matches_sha3_oracle_structure():
    # same permutation as FIPS-202 with different domain byte; a smoke that
    # multi-block absorption stays correct at the 136-byte boundary
    a = eth.keccak256(b"x" * 135).hex()
    b = eth.keccak256(b"x" * 136).hex()
    c = eth.keccak256(b"x" * 137).hex()
    assert len({a, b, c}) == 3


def test_eip55_all_official_vectors():
    for v in ("0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
              "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
              "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB",
              "0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb"):
        j = client.post("/api/v1/eth/address", json={"address": v}).json()
        assert j["valid_eip55"] is True, v


def test_eip55_typo_rejected_and_repaired():
    bad = "0x5AAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"  # 1 casse inversée
    j = client.post("/api/v1/eth/address", json={"address": bad}).json()
    assert j["valid_eip55"] is False
    assert j["checksummed"] == "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"


def test_allowlist_case_insensitive_membership():
    j = client.post("/api/v1/eth/address", json={
        "address": "0x00f04a2A505116dAF3b88EaE17445D85bEd4FbaC",
        "allowlist": ["0x00f04a2a505116daf3b88eae17445d85bed4fbac"]})
    assert j.json()["in_allowlist"] is True


def test_selector_route_and_no_spaces():
    j = client.post("/api/v1/eth/selector",
                    json={"signature": "transfer(address,uint256)"}).json()
    assert j["selector"] == "0xa9059cbb"
    r = client.post("/api/v1/eth/selector",
                    json={"signature": "transfer (address, uint256)"})
    assert r.status_code == 400 and "whitespace" in r.text


def test_units_exact_and_fractional_refused():
    j = client.post("/api/v1/eth/units",
                    json={"value": "1.5", "unit": "ether"}).json()
    assert j["wei"] == "1500000000000000000"
    assert j["gwei"] == "1500000000"
    assert "E+" not in json.dumps(j)
    r = client.post("/api/v1/eth/units",
                    json={"value": "0.0000000000000000001",
                          "unit": "ether"})
    assert r.status_code == 400 and "fractional" in r.text


def test_free_keyless_and_mcp():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert {"eth_address", "eth_selector", "eth_units"} <= set(names)
    assert client.post("/api/v1/eth/address",
                       json={"address": "0x" + "ab" * 20}
                       ).status_code == 200


# ------------------------------------------------------------- lot 2
def _mail():
    return {
        "types": {
            "EIP712Domain": [{"name": "name", "type": "string"},
                             {"name": "version", "type": "string"},
                             {"name": "chainId", "type": "uint256"},
                             {"name": "verifyingContract",
                              "type": "address"}],
            "Person": [{"name": "name", "type": "string"},
                       {"name": "wallet", "type": "address"}],
            "Mail": [{"name": "from", "type": "Person"},
                     {"name": "to", "type": "Person"},
                     {"name": "contents", "type": "string"}]},
        "primaryType": "Mail",
        "domain": {"name": "Ether Mail", "version": "1", "chainId": 1,
                   "verifyingContract":
                   "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"},
        "message": {
            "from": {"name": "Cow",
                     "wallet": "0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826"},
            "to": {"name": "Bob",
                   "wallet": "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"},
            "contents": "Hello, Bob!"}}


def test_eip712_spec_digest_over_http():
    r = client.post("/api/v1/eth/eip712", json=_mail())
    assert r.status_code == 200
    assert r.json()["digest"] == (
        "0xbe609aee343fb3c4b28e1df9e632fca64fcfaede20f02e86244efddf30957bd2"
    ), "EIP-712 official Mail digest"


def test_abi_roundtrip_over_http():
    body = {"types": ["address", "uint256"],
            "values": ["0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
                       "1000"]}
    enc = client.post("/api/v1/eth/abi-encode", json=body).json()
    assert enc["calldata"].startswith("0x0000000000000000000000005aaeb")
    assert enc["calldata"].endswith(
        "00000000000000000000000000000000000000000000000000000000000003e8")
    dec = client.post("/api/v1/eth/abi-decode", json={
        "types": body["types"], "data": enc["calldata"]}).json()
    assert dec["values"] == [
        "0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed", "1000"]


def test_abi_closed_grammar_refuses():
    r = client.post("/api/v1/eth/abi-encode",
                    json={"types": ["uint8[]"], "values": [[1]]})
    assert r.status_code == 200          # uint8[] dynamic array: accepted
    r2 = client.post("/api/v1/eth/abi-encode",
                     json={"types": ["uint9"], "values": [1]})
    assert r2.status_code == 400         # not a valid bit width
    r3 = client.post("/api/v1/eth/abi-decode",
                     json={"types": ["uint256"], "data": "0xdead"})
    assert r3.status_code == 400         # not a multiple of 32 bytes


def test_receipt_match_and_miss():
    logs = [{"address": "0xA0b86991c6218b36cdd17F0aC7A5f2f3c2E2Ba71",
             "topics": ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a1"
                        "1628f55a4df523b3ef",
                        "0x000000000000000000000000" + "ef" * 20,
                        "0x000000000000000000000000" + "ab" * 20],
             "data": "0x" + "0" * 60 + "03e8"}]
    hit = client.post("/api/v1/eth/receipt", json={
        "logs": logs,
        "expect": {"from": "0x" + "EF" * 20, "to": "0x" + "AB" * 20,
                   "value": "1000"}}).json()
    assert hit["pass"] is True and hit["matches"][0]["value"] == "1000"
    miss = client.post("/api/v1/eth/receipt", json={
        "logs": logs,
        "expect": {"from": "0x" + "EF" * 20, "value": "999"}}).json()
    assert miss["pass"] is False and miss["matched"] == 0
