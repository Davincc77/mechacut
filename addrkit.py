"""Bundle 27 lot 3 — crypto address validation, pure Python stdlib only.

Why pure Python for RIPEMD-160: hashlib's ripemd160 lives behind OpenSSL's
legacy provider, so it exists on one runtime and not the next. A validation
endpoint that changes verdicts with the container image would break the one
promise this service makes. So the published spec is implemented here and
checked against the official vectors.

Validation only: never custody, never storage, never a network call.
"""
import hashlib
import struct

M32 = 0xFFFFFFFF
_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


class AddressError(Exception):
    pass


# ------------------------------------------------ RIPEMD-160 (published spec)
_R = (
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    [7, 4, 13, 1, 10, 6, 15, 3, 12, 0, 9, 5, 2, 14, 11, 8],
    [3, 10, 14, 4, 9, 15, 8, 1, 2, 7, 0, 6, 13, 11, 5, 12],
    [1, 9, 11, 10, 0, 8, 12, 4, 13, 3, 7, 15, 14, 5, 6, 2],
    [4, 0, 5, 9, 7, 12, 2, 10, 14, 1, 3, 8, 11, 6, 15, 13],
)
_R_PRIME = (
    [5, 14, 7, 0, 9, 2, 11, 4, 13, 6, 15, 8, 1, 10, 3, 12],
    [6, 11, 3, 7, 0, 13, 5, 10, 14, 15, 8, 12, 4, 9, 1, 2],
    [15, 5, 1, 3, 7, 14, 6, 9, 11, 8, 12, 2, 10, 0, 4, 13],
    [8, 6, 4, 1, 3, 11, 15, 0, 5, 12, 2, 13, 9, 7, 10, 14],
    [12, 15, 10, 4, 1, 5, 8, 7, 6, 2, 13, 14, 0, 3, 9, 11],
)
_S = (
    [11, 14, 15, 12, 5, 8, 7, 9, 11, 13, 14, 15, 6, 7, 9, 8],
    [7, 6, 8, 13, 11, 9, 7, 15, 7, 12, 15, 9, 11, 7, 13, 12],
    [11, 13, 6, 7, 14, 9, 13, 15, 14, 8, 13, 6, 5, 12, 7, 5],
    [11, 12, 14, 15, 14, 15, 9, 8, 9, 14, 5, 6, 8, 6, 5, 12],
    [9, 15, 5, 11, 6, 8, 13, 12, 5, 12, 13, 14, 11, 8, 5, 6],
)
_S_PRIME = (
    [8, 9, 9, 11, 13, 15, 15, 5, 7, 7, 8, 11, 14, 14, 12, 6],
    [9, 13, 15, 7, 12, 8, 9, 11, 7, 7, 12, 7, 6, 15, 13, 11],
    [9, 7, 15, 11, 8, 6, 6, 14, 12, 13, 5, 14, 13, 13, 7, 5],
    [15, 5, 8, 11, 14, 14, 6, 14, 6, 9, 12, 9, 12, 5, 15, 8],
    [8, 5, 12, 9, 12, 5, 14, 6, 8, 13, 6, 5, 15, 13, 11, 11],
)
_K = (0x00000000, 0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC, 0xA953FD4E)
_K_PRIME = (0x50A28BE6, 0x5C4DD124, 0x6D703EF3, 0x7A6D76E9, 0x00000000)


def _rol(x, n):
    return ((x << n) | (x >> (32 - n))) & M32


def _f(j, x, y, z):
    if j < 16:
        return x ^ y ^ z
    if j < 32:
        return (x & y) | (~x & M32 & z)
    if j < 48:
        return (x | (~y & M32)) ^ z
    if j < 64:
        return (x & z) | (y & (~z & M32))
    return x ^ (y | (~z & M32))


def ripemd160(data):
    """Official RIPEMD-160. Verified against the published test vectors."""
    msg = bytes(data)
    ln = len(msg)
    padded = msg + b"\x80"
    while len(padded) % 64 != 56:
        padded += b"\x00"
    padded += struct.pack("<Q", ln * 8)
    h = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]
    for off in range(0, len(padded), 64):
        x = list(struct.unpack("<16I", padded[off:off + 64]))
        a2, b2, c2, d2, e2 = h
        ap2, bp2, cp2, dp2, ep2 = h
        for j in range(80):
            rnd = j // 16
            t = (a2 + _f(j, b2, c2, d2) + x[_R[rnd][j % 16]]
                 + _K[rnd]) & M32
            t = (_rol(t, _S[rnd][j % 16]) + e2) & M32
            a2, e2, d2, c2, b2 = e2, d2, _rol(c2, 10), b2, t
            t = (ap2 + _f(79 - j, bp2, cp2, dp2) + x[_R_PRIME[rnd][j % 16]]
                 + _K_PRIME[rnd]) & M32
            t = (_rol(t, _S_PRIME[rnd][j % 16]) + ep2) & M32
            ap2, ep2, dp2, cp2, bp2 = ep2, dp2, _rol(cp2, 10), bp2, t
        new = [(h[1] + c2 + dp2) & M32,
               (h[2] + d2 + ep2) & M32,
               (h[3] + e2 + ap2) & M32,
               (h[4] + a2 + bp2) & M32,
               (h[0] + b2 + cp2) & M32]
        h = new
    return b"".join(struct.pack("<I", v) for v in h)


# ------------------------------------------------------------- base58check
def b58_decode(s):
    n = 0
    for ch in s:
        if ch not in _B58_ALPHABET:
            raise AddressError("base58: illegal character %r" % ch)
        n = n * 58 + _B58_ALPHABET.index(ch)
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    pad = 0
    for ch in s:
        if ch == "1":
            pad += 1
        else:
            break
    return b"\x00" * pad + body


def b58check_decode(addr):
    raw = b58_decode(addr)
    if len(raw) < 5:
        raise AddressError("base58check: too short")
    body, checksum = raw[:-4], raw[-4:]
    if hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4] != checksum:
        raise AddressError("base58check: checksum mismatch")
    return body[0], body[1:]


_BTC_VERSIONS = {0x00: ("p2pkh", "bitcoin"), 0x05: ("p2sh", "bitcoin"),
                 0x6F: ("p2pkh", "bitcoin-testnet"),
                 0xC4: ("p2sh", "bitcoin-testnet")}


# ---------------------------------------------------------------- bech32
def _bech32_poly(values):
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ v
        for i in range(5):
            if (b >> i) & 1:
                chk ^= [0x3B6A57B2, 0x26508E6D, 0x1EA119FA,
                        0x3D4233DD, 0x2A1462B3][i]
    return chk


def _bech32_hrp_expand(hrp):
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def bech32_decode(addr):
    if addr.lower() != addr and addr.upper() != addr:
        raise AddressError("bech32: mixed case is forbidden")
    s = addr.lower()
    if "1" not in s:
        raise AddressError("bech32: no separator")
    hrp, data_part = s.rsplit("1", 1)
    if not data_part or len(data_part) < 6:
        raise AddressError("bech32: data part too short")
    if any(c not in _BECH32_CHARSET for c in data_part):
        raise AddressError("bech32: invalid character in data part")
    data = [_BECH32_CHARSET.index(c) for c in data_part]
    spec = _bech32_poly(_bech32_hrp_expand(hrp) + data)
    if spec == 1:
        encoding = "bech32"
    elif spec == 0x2BC830A3:
        encoding = "bech32m"
    else:
        raise AddressError("bech32: checksum verification failed")
    return hrp, data[:-6], encoding


def convertbits(data, frombits, tobits, pad=True):
    acc = 0
    bits = 0
    out = []
    maxv = (1 << tobits) - 1
    for v in data:
        if v < 0 or v >> frombits:
            raise AddressError("bech32: value out of range")
        acc = (acc << frombits) | v
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            out.append((acc >> bits) & maxv)
    if pad:
        if bits:
            out.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        raise AddressError("bech32: invalid padding")
    return out


_HRP_NET = {"bc": "bitcoin", "tb": "bitcoin-testnet",
            "bcrt": "bitcoin-regtest", "ltc": "litecoin"}


def segwit_decode(addr):
    hrp, data, encoding = bech32_decode(addr)
    if hrp not in _HRP_NET:
        raise AddressError("bech32: hrp %r outside the closed table "
                           "(bc, tb, bcrt, ltc)" % hrp)
    if not data:
        raise AddressError("bech32: empty witness program")
    ver = data[0]
    program = convertbits(data[1:], 5, 8, False)
    if ver > 16:
        raise AddressError("bech32: witness version %d too high" % ver)
    if len(program) < 2 or len(program) > 40:
        raise AddressError("bech32: witness program length %d invalid"
                           % len(program))
    if ver == 0 and len(program) not in (20, 32):
        raise AddressError("bech32: v0 program must be 20 or 32 bytes "
                           "(got %d)" % len(program))
    if ver == 0 and encoding != "bech32":
        raise AddressError("bech32: v0 must use bech32, not bech32m")
    if ver != 0 and encoding != "bech32m":
        raise AddressError("bech32: v1+ must use bech32m")
    return {"scheme": "bech32" + ("m" if encoding == "bech32m" else ""),
            "witness_version": ver,
            "program_hex": bytes(program).hex(),
            "network": _HRP_NET[hrp],
            "kind": ("p2wpkh" if (ver, len(program)) == (0, 20) else
                     "p2wsh" if (ver, len(program)) == (0, 32) else
                     "taproot" if ver == 1 and len(program) == 32 else
                     "witness-v%d" % ver)}


# --------------------------------------------------------------- endpoint
def crypto_address(address, chain="auto"):
    if not isinstance(address, str) or not address.strip():
        raise AddressError("address must be a non-empty string")
    a = address.strip()
    problems = []
    chain = (chain or "auto").lower()
    # per-branch problem lists: a non-matching branch is a trial, not an
    # error; only the branch that OWNS the shape may report problems
    if chain in ("auto", "bitcoin", "litecoin") and a[:2].lower() in (
            "bc", "tb", "bc", "lt"):
        try:
            out = segwit_decode(a)
            if chain != "auto" and out["network"].split("-")[0] != chain:
                problems.append("network mismatch for chain=%s" % chain)
            out["valid"] = not problems
            if problems:
                out["problems"] = problems
            return out
        except AddressError as e:
            if chain != "auto":
                problems.append(str(e))
    if chain in ("auto", "bitcoin"):
        try:
            ver, payload = b58check_decode(a)
            if len(payload) != 20:
                problems.append("payload must be 20 bytes, got %d"
                                % len(payload))
            kind_net = _BTC_VERSIONS.get(ver)
            if kind_net is None:
                problems.append("version byte 0x%02x outside the closed "
                                "table (P2PKH/P2SH mainnet+testnet)" % ver)
            return {"scheme": "base58check",
                    "kind": kind_net[0] if kind_net else None,
                    "network": kind_net[1] if kind_net else None,
                    "version_byte": "0x%02x" % ver,
                    "hash160_hex": payload.hex(),
                    "valid": not problems,
                    "problems": problems or None}
        except AddressError as e:
            if chain != "auto":
                problems.append(str(e))
    if chain in ("auto", "eth", "evm", "base", "polygon"):
        from eth import EthError, eth_address
        try:
            d = eth_address(a)
            d["scheme"] = "evm"
            d["valid"] = d["valid_eip55"] and not problems
            if problems:
                d["problems"] = problems
            return d
        except EthError as e:
            problems.append(str(e))
    raise AddressError("no closed algorithm matched: " + " | ".join(problems))


