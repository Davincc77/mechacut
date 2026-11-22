"""Bundle 27 lot 1 — CAIP identifiers (Chain Agnostic Improvement
Pool 2 / 10): the exact strings our x402 payments speak
(`eip155:8453`, `0x…@eip155:8453`). Closed tables: published chain ids,
published EIP-55 vectors, base58/bech32 shapes. parse + format, never
a network call."""
import re

from eth import EthError, eth_address

EIP155_CHAINS = {
    "1": "Ethereum Mainnet", "10": "OP Mainnet", "56": "BNB Smart Chain",
    "100": "Gnosis Chain", "137": "Polygon PoS", "8453": "Base",
    "42161": "Arbitrum One", "43114": "Avalanche C-Chain",
    "59144": "Linea", "534": "Scroll", "250": "Fantom Opera",
    "84532": "Base Sepolia", "11155111": "Sepolia",
}
BIP122_CHAINS = {
    "000000000019d6689c085ae165831e934ff763ae46a2a6c17b7a91ef126d1c89":
        "Bitcoin",
    "000000000933ea01ad0ee984209779baaec3ced90fa3f408719526f8d77f4943":
        "Bitcoin Testnet",
}
SOLANA_REFS = {"mainnet-beta", "devnet", "testnet"}
COSMOS_REFS = {"cosmoshub-4", "osmosis-1", "injective-1", "celestia"}

_B58 = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


class CaipError(Exception):
    pass


def _check_eip155_address(addr):
    try:
        return eth_address(addr)["checksummed"]
    except EthError as e:
        raise CaipError(str(e))


def caip_parse(value):
    if not isinstance(value, str) or not value.strip():
        raise CaipError("value must be a non-empty CAIP-2 or CAIP-10 string")
    v = value.strip()
    kind = "caip2"
    addr = None
    if "@" in v:
        addr, chain = v.split("@", 1)
        kind = "caip10"
    else:
        chain = v
    if ":" not in chain:
        raise CaipError("missing namespace: CAIP-2 is namespace:reference")
    ns, ref = chain.split(":", 1)
    out = {"kind": kind, "namespace": ns, "reference": ref}
    if ns == "eip155":
        if not ref.isdigit():
            raise CaipError("eip155 reference must be a decimal chain id")
        out["chain"] = EIP155_CHAINS.get(str(int(ref)))
        out["chain_known"] = str(int(ref)) in EIP155_CHAINS
        if int(ref) not in [int(k) for k in EIP155_CHAINS]:
            out["verdict_edge"] = ("valid CAIP-2, chain id outside the "
                                   "published subset shipped here")
    elif ns == "bip122":
        if not re.match(r"^[0-9a-f]{64}$", ref.lower()):
            raise CaipError("bip122 reference is the genesis hash (64 hex)")
        out["chain"] = BIP122_CHAINS.get(ref.lower())
        out["chain_known"] = ref.lower() in BIP122_CHAINS
    elif ns == "solana":
        out["chain"] = ref if ref in SOLANA_REFS else None
        out["chain_known"] = ref in SOLANA_REFS
    elif ns == "cosmos":
        out["chain"] = ref if ref in COSMOS_REFS else None
        out["chain_known"] = ref in COSMOS_REFS
    else:
        raise CaipError("namespace %r outside the closed subset "
                        "(eip155, bip122, solana, cosmos)" % ns)
    if kind == "caip10":
        if ns == "eip155":
            out["address_checksummed"] = _check_eip155_address(addr)
        elif ns == "solana":
            if not (32 <= len(addr) <= 44
                    and all(c in _B58 for c in addr)):
                raise CaipError("solana address must be base58 32-44 chars"
                                " (no 0 O I l)")
            out["address_checksummed"] = addr
        else:
            if not re.match(r"^[0-9a-zA-Z]{1,84}$", addr):
                raise CaipError("address shape invalid for this namespace")
            out["address_checksummed"] = addr
        out["caip10"] = "%s@%s" % (
            out["address_checksummed"] if ns == "eip155" else addr, chain)
    return out


def caip_format(namespace, reference, address=None):
    if not namespace or not reference:
        raise CaipError("namespace and reference required")
    parsed = caip_parse(("%s@%s:%s" % (address, namespace, reference))
                        if address else "%s:%s" % (namespace, reference))
    if address:
        return {"caip10": parsed["caip10"]}
    return {"caip2": "%s:%s" % (namespace, reference),
            "chain": parsed.get("chain"),
            "chain_known": parsed["chain_known"]}
