"""Bundle 27 — IDENTITÉ. Vecteurs publiés : EIP-55 spec, chain IDs
registred, genesis Bitcoin publiés."""
import sys
sys.path.insert(0, ".")
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def caip(**kw):
    r = client.post("/api/v1/caip/parse", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def test_parse_our_own_payment_chain():
    d = caip(value="eip155:8453")
    assert d["namespace"] == "eip155" and d["chain"] == "Base"
    assert d["chain_known"] is True


def test_eip55_published_vector_roundtrip():
    d = caip(value="0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed@eip155:1")
    assert d["caip10"] == \
        "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed@eip155:1"
    low = caip(value="0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed@eip155:1")
    assert low["caip10"] == d["caip10"]      # casse normalisée par le spec


def test_format_mode():
    d = caip(mode="format", namespace="eip155", reference="8453")
    assert d["caip2"] == "eip155:8453" and d["chain"] == "Base"


def test_bitcoin_genesis_published():
    d = caip(value="bip122:000000000019d6689c085ae165831e93"
                  "4ff763ae46a2a6c17b7a91ef126d1c89")
    assert d["chain"] == "Bitcoin"


def test_unknown_chain_is_edge_verdict_not_error():
    d = caip(value="eip155:999999")
    assert d["chain_known"] is False
    assert "outside" in d["verdict_edge"]


def test_solana_base58_rejects_0OIl():
    r = client.post("/api/v1/caip/parse", json={
        "value": "0OIl" + "1" * 32 + "@solana:mainnet-beta"})
    assert r.status_code == 400
    assert "base58" in r.json()["errors"][0]["message"]


def test_namespace_subset_honest():
    r = client.post("/api/v1/caip/parse", json={"value": "tron:1"})
    assert r.status_code == 400
    assert "closed subset" in r.json()["errors"][0]["message"]


# ------------------------------------------------ lot 2 : validate/taxid
def tx(value, kind="auto"):
    r = client.post("/api/v1/validate/taxid", json={"value": value,
                                                    "kind": kind})
    assert r.status_code == 200, r.text
    return r.json()


def test_cnpj_receita_published_vector():
    assert tx("11.222.333/0001-81", "cnpj")["valid"] is True  # doc Receita
    assert tx("11.222.333/0001-80", "cnpj")["valid"] is False


def test_cpf_vector_and_repeated_digits_rule():
    assert tx("529.982.247-25")["valid"] is True          # exemple canonique
    assert tx("111.111.111-11")["valid"] is False         # règle publiée


def test_siren_insee_lettre_vectors():
    d = tx("120 027 016")                                 # SIREN de l'INSEE
    assert d["valid"] is True and d["kind"] == "siren"
    assert tx("123 456 789")["valid"] is False            # somme 47 publiée


def test_siret_published_examples_and_laposte_branch():
    assert tx("422 260 208 00026", kind="siret")["valid"] is True
    assert tx("812 345 676 00017", kind="siret")["valid"] is True
    assert tx("812 345 676 00018", kind="siret")["valid"] is False
    # branche La Poste documentée (validinsee) : somme brute % 5
    assert tx("35600000000010", kind="siret")["valid"] is True


def test_vat_fr_official_example_and_de():
    assert tx("FR40303265045")["valid"] is True   # exemple douane.gouv.fr
    assert tx("FR41303265045")["valid"] is False  # clé faussée


def test_ambiguous_14_digits_reported_not_guessed():
    d = tx("44306184100012")
    assert d["detected"] is None
    assert set(d["ambiguous_kinds"]) == {"cnpj", "siret"}


def test_unknown_country_raises_with_closed_list():
    r = client.post("/api/v1/validate/taxid",
                    json={"value": "XX123", "kind": "vat_xx"})
    assert r.status_code == 400
    assert "closed subset" in r.json()["errors"][0]["message"]


def test_algorithm_is_named_in_every_verdict():
    d = tx("11.222.333/0001-81", "cnpj")
    assert "Receita" in d["algorithm"]


# --------------------------------------------- lot 3 : crypto/address
import hashlib


def addr(a, chain="auto"):
    r = client.post("/api/v1/crypto/address",
                    json={"address": a} if chain == "auto"
                    else {"address": a, "chain": chain})
    assert r.status_code == 200, r.text
    return r.json()


def test_ripemd160_pure_python_official_vectors():
    # les 7 messages de la suite de Dobbertin et al., digests publiés ;
    # chaque vecteur est AUSSI recoupé avec l'oracle openssl local quand
    # le runtime le fournit — deux sources, jamais la mémoire du test
    import addrkit
    vectors = [
        (b"", "9c1185a5c5e9fc54612808977ee8f548b2258d31"),
        (b"abc", "8eb208f7e05d987a9b044a8e98c6b087f15a0bfc"),
        (b"message digest", "5d0689ef49d2fae572b881b123a85ffa21595f36"),
        (b"abcdefghijklmnopqrstuvwxyz",
         "f71c27109c692c1b56bbdceb5b9d2865b3708dbc"),
        (b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
         "12a053384a9c0c88e405a06c27dcf49ada62eb2b"),
        (b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
         "b0e20b6e3116640286ed3a87a5713079b21f5189"),
        (b"1234567890" * 8, "9b752e45573d4b39f4dbd3323cab82bf63326bfb"),
    ]
    for msg, want in vectors:
        assert addrkit.ripemd160(msg).hex() == want
    try:
        hashlib.new("ripemd160")
        have = True
    except ValueError:
        have = False
    if have:
        for msg, _ in vectors:
            o = hashlib.new("ripemd160")
            o.update(msg)
            assert o.digest() == addrkit.ripemd160(msg)


def test_base58check_genesis_address_published():
    d = addr("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    assert d["valid"] is True and d["kind"] == "p2pkh"
    assert d["network"] == "bitcoin"
    assert d["hash160_hex"] == "62e907b15cbf27d5425399ebf6f0fb50ebb88f18"


def test_bech32_bip173_vector():
    d = addr("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4")
    assert d["kind"] == "p2wpkh" and d["witness_version"] == 0
    assert d["scheme"] == "bech32" and d["valid"] is True


def test_bech32m_taproot_bip350_vector():
    d = addr("bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0")
    assert d["kind"] == "taproot" and d["scheme"] == "bech32m"


def test_bip173_invalid_vectors_rejected():
    # dernière lettre changée : checksum mort (vecteur BIP-173 détourné)
    r = client.post("/api/v1/crypto/address", json={
        "address": "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5"})
    assert r.status_code == 400
    # v0 en bech32m = interdit par BIP-350
    r2 = client.post("/api/v1/crypto/address", json={
        "address": "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"})
    assert r2.status_code == 400


def test_evm_branch_eip55_case():
    d = addr("0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed")
    assert d["scheme"] == "evm" and d["valid"] is True
    d2 = addr("0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAeD")   # e->E
    assert d2["valid"] is False


def test_base58_broken_checksum_rejected():
    r = client.post("/api/v1/crypto/address", json={
        "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfaA"})
    assert r.status_code == 400
    assert "no closed algorithm" in r.json()["errors"][0]["message"]
