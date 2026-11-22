"""Bundle 18 (lot 1) — deterministic EVM primitives: keccak256, EIP-55,
selectors (TOOLS-50 #57 + core of #54/#56).

Pure-Python Keccak-f[1600], vendored and auditable — no wheels, no
dependency drift, same bytes forever. Everything that must be true for an
agent signing with its wallet (address shape, checksum, function selector,
EIP-712 domain digest) becomes a measured call instead of model memory.

Same request -> same bytes. No LLM, no network, no state.
"""
import re

__all__ = ["EthError", "keccak256", "eth_address", "eth_selector",
           "eth_units"]


class EthError(Exception):
    pass


# ---------------------------------------------------------- keccak-f[1600]
_RC = (
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
)
_ROT = (
    (0, 36, 3, 41, 18), (1, 44, 10, 45, 2), (62, 6, 43, 15, 61),
    (28, 55, 25, 21, 56), (27, 20, 39, 8, 14),
)
_M = (1 << 64) - 1


def _rol(v, n):
    n %= 64
    return ((v << n) | (v >> (64 - n))) & _M if n else v


def _f1600(A_in):
    """Keccak-f[1600] in flat lane indexing (lane[x + 5y]) — FIPS-202."""
    A = list(A_in)
    for rc in _RC:
        # theta
        C = [A[x] ^ A[x + 5] ^ A[x + 10] ^ A[x + 15] ^ A[x + 20]
             for x in range(5)]
        D = [C[(x + 4) % 5] ^ _rol(C[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                A[x + 5 * y] ^= D[x]
        # rho + pi
        B = [0] * 25
        for x in range(5):
            for y in range(5):
                B[y + 5 * ((2 * x + 3 * y) % 5)] = _rol(
                    A[x + 5 * y], _ROT[x][y])
        # chi
        for x in range(5):
            for y in range(5):
                A[x + 5 * y] = B[x + 5 * y] ^ (
                    (~B[(x + 1) % 5 + 5 * y] & _M)
                    & B[(x + 2) % 5 + 5 * y])
        # iota
        A[0] ^= rc
    return A


def keccak256(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    rate = 136                                   # 1088 bits for 256-out
    padded = bytearray(data)
    padded.append(0x01)                          # Keccak pad, not SHA3's 06
    while len(padded) % rate:
        padded.append(0x00)
    padded[-1] ^= 0x80
    lanes = [0] * 25
    for off in range(0, len(padded), rate):
        block = padded[off:off + rate]
        for i in range(rate // 8):
            lanes[i] ^= int.from_bytes(block[i * 8:i * 8 + 8], "little")
        lanes = _f1600(lanes)
    out = bytearray()
    for i in range(4):                           # 32 bytes out
        out += lanes[i].to_bytes(8, "little")
    return bytes(out)


# -------------------------------------------------------------- EIP-55/56
_HEXADDR = re.compile(r"^(0x)?[0-9a-fA-F]{40}$")


def _checksum(addr40):
    h = keccak256(addr40.lower().encode("ascii")).hex()
    return "0x" + "".join(
        c.upper() if c.isalpha() and int(h[i], 16) >= 8 else c
        for i, c in enumerate(addr40.lower()))


def eth_address(address, allowlist=None):
    if not isinstance(address, str) or not _HEXADDR.match(address.strip()):
        raise EthError('address must be 40 hex chars, e.g. '
                       '0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed')
    raw = address.strip()
    body = raw[2:]
    canonical = _checksum(body)
    lowered = raw.lower()
    is_lower = body == body.lower()
    is_upper = body == body.upper()
    valid = is_lower or is_upper or canonical == (
        raw if raw.startswith("0x") else "0x" + raw)
    out = {"input": raw, "checksummed": canonical,
           "lowercase": "0x" + body.lower(),
           "valid_eip55": valid,
           "all_lowercase": is_lower, "all_uppercase": is_upper}
    if allowlist is not None:
        if not isinstance(allowlist, list) or not all(
                _HEXADDR.match(str(a)) for a in allowlist):
            raise EthError("allowlist must be an array of 0x-hex addresses")
        norm = {("0x" + str(a)[2:].lower()) if str(a).lower().startswith(
            "0x") else "0x" + str(a).lower() for a in allowlist}
        out["in_allowlist"] = ("0x" + body.lower()) in norm
        out["allowlist_invalid"] = [
            a for a in allowlist
            if not _HEXADDR.match(str(a))]
    return out


def eth_selector(signature):
    if not isinstance(signature, str) or "(" not in signature \
            or not signature.endswith(")"):
        raise EthError("signature must look like "
                       '"transfer(address,uint256)" — canonical types, '
                       "no spaces")
    bad = [c for c in signature if c.isspace()]
    if bad:
        raise EthError("signature must contain no whitespace")
    digest = keccak256(signature.encode("ascii"))
    return {"signature": signature,
            "selector": "0x" + digest[:4].hex(),
            "full_hash": "0x" + digest.hex()}


# ------------------------------------------------------------- wei ladder
_WEI = {"wei": 1, "kwei": 10 ** 3, "mwei": 10 ** 6, "gwei": 10 ** 9,
        "szabo": 10 ** 12, "finney": 10 ** 15, "ether": 10 ** 18}


def eth_units(value, unit):
    from decimal import Decimal
    if unit not in _WEI:
        raise EthError("unit must be one of: %s"
                       % ", ".join(sorted(_WEI)))
    try:
        d = Decimal(str(value))
    except Exception:
        raise EthError("value must be a numeric string or number")
    wei = d * _WEI[unit]
    if wei != wei.to_integral_value():
        raise EthError("result is fractional wei — pick a coarser unit")
    w = int(wei)
    sign = "-" if w < 0 else ""
    a = abs(w)
    ether = Decimal(a) / Decimal(10 ** 18)
    gwei = Decimal(a) / Decimal(10 ** 9)
    def plain(d):
        t = format(d.normalize(), "f")     # no scientific notation
        return t
    return {"wei": "%s%d" % (sign, a),
            "gwei": sign + plain(gwei),
            "ether": sign + plain(ether)}
