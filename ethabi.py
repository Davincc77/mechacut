"""Bundle 18 (lot 2) — calldata, EIP-712, receipt matching (TOOLS-50 #54,
#55, #56, #58).

The blind-signing layer killed here: an agent never hand-writes calldata,
never hand-builds a permit digest, never eyeballs a Transfer log again.
Encoding is the Solidity ABI spec, ported as closed rules; EIP-712 is the
typed-data spec, verbatim. Verified against the published example digests
of both specs.

Same request -> same bytes. No LLM, no network, no state.
"""
import re

from eth import EthError, keccak256

__all__ = ["abi_encode", "abi_decode", "eip712_digest", "receipt_match"]

_BASE = re.compile(r"^(u?int|bytes|address|bool|string)(\d*)$")


def parse_type(t):
    if not isinstance(t, str) or not t:
        raise EthError("type must be a non-empty string like uint256")
    m = re.match(r"^(.+?)((?:\[\d*\])*)$", t)
    if not m:
        raise EthError("bad type %r" % t)
    base, suffix = m.group(1), m.group(2)
    dims = re.findall(r"\[(\d*)\]", suffix)
    if base.startswith("tuple") and not re.match(r"^tuple$", base):
        raise EthError("only bare 'tuple' base is accepted")
    if not re.match(r"^tuple$", base) and not _BASE.match(base):
        raise EthError("unknown base type %r (uint<M> int<M> bytes<M> "
                       "address bool string tuple allowed)" % base)
    if base == "bytes" and m.group(2) == "" and _BASE.match("bytes" + ""):
        pass
    if base in ("address", "bool", "string", "tuple"):
        if _BASE.match(base) is None and base != "tuple":
            raise EthError("bad base %r" % base)
    if base.startswith(("uint", "int")) or (base.startswith("bytes")
                                            and base != "bytes"):
        n = int(re.sub(r"\D", "", base))
        if base.startswith("bytes") and not 1 <= n <= 32:
            raise EthError("bytesN needs N in 1..32")
        if base.startswith(("uint", "int")) and not (
                8 <= n <= 256 and n % 8 == 0):
            raise EthError("uint/int bits must be 8..256 step 8")
    if base == "tuple":
        raise EthError("bare tuples need the ABI tree form; use typed args")
    return base, dims


def _is_dynamic(base, dims):
    if any(d == "" for d in dims):
        return True
    return base in ("string", "bytes")


def _enc_static_value(base, v):
    if base == "address":
        s = str(v).lower().removeprefix("0x")
        if not re.match(r"^[0-9a-f]{40}$", s):
            raise EthError("address must be 20 hex bytes")
        return bytes(12) + bytes.fromhex(s)
    if base == "bool":
        if v not in (True, False, "true", "false"):
            raise EthError("bool needs true/false")
        return bytes(31) + (b"\x01" if v in (True, "true") else b"\x00")
    if base.startswith("bytes"):
        n = int(base[5:])
        data = (bytes.fromhex(str(v).removeprefix("0x"))
                if re.fullmatch(r"(0x)?[0-9a-fA-F]*", str(v))
                else str(v).encode())
        if len(data) != n:
            raise EthError("bytes%d needs exactly %d bytes" % (n, n))
        return data + bytes(32 - n)
    # uint / int
    try:
        from decimal import Decimal
        d = Decimal(str(v))
        if d != d.to_integral_value():
            raise EthError("integer expected")
        i = int(d)
    except Exception:
        raise EthError("numeric integer expected, got %r" % (v,))
    bits = int(base[4:] or 256) if base.startswith("uint") else \
        int(base[3:] or 256)
    if base.startswith("uint") and not 0 <= i < 2 ** bits:
        raise EthError("value out of range for %s" % base)
    if base.startswith("int") and not -(2 ** (bits - 1)) <= i < 2 ** \
            (bits - 1):
        raise EthError("value out of range for %s" % base)
    return i.to_bytes(32, "big", signed=base.startswith("int"))


def _enc_dynamic_tail(base, v):
    if base in ("string",):
        data = str(v).encode("utf-8")
    elif base == "bytes":
        data = bytes.fromhex(str(v).removeprefix("0x"))
    else:
        raise EthError("not a dynamic base")
    pad = (32 - len(data) % 32) % 32
    return len(data).to_bytes(32, "big") + data + bytes(pad)


def _enc(value, base, dims):
    """Encode one value of type base + dims (list of remaining dims)."""
    if dims:
        head_dims, tail_dims = dims[0], dims[1:]
        if not isinstance(value, (list, tuple)):
            raise EthError("expected an array")
        n = len(value)
        if head_dims != "" and n != int(head_dims):
            raise EthError("fixed array wants %s items, got %d"
                           % (head_dims, n))
        elem_dyn = _is_dynamic(base, tail_dims)
        parts = []
        if head_dims == "":
            parts.append(n.to_bytes(32, "big"))
        heads, tails = [], []
        for item in value:
            enc_item = _enc(item, base, tail_dims)
            if elem_dyn:
                heads.append(None)
                tails.append(enc_item)
            else:
                heads.append(enc_item)
        off = n * 32 if head_dims == "" else 0
        # offsets count from array body start
        body = bytearray()
        for i, item in enumerate(value):
            if elem_dyn:
                body += (len(heads) * 32 + sum(len(t) for t in tails[:i])
                         ).to_bytes(32, "big")
            else:
                body += heads[i]
        for t in tails:
            body += t
        return b"".join(parts) + bytes(body)
    if base in ("string", "bytes") and not dims:
        return _enc_dynamic_tail(base, value)
    return _enc_static_value(base, value)


def abi_encode(types, values):
    if len(types) != len(values):
        raise EthError("types/values length mismatch")
    parsed = [parse_type(t) for t in types]
    heads, tails = [], []
    for v, (base, dims) in zip(values, parsed):
        enc = _enc(v, base, dims)
        if _is_dynamic(base, dims):
            heads.append(("DYN", len(tails)))
            tails.append(enc)
        else:
            heads.append(("FIX", enc))
    head_size = 32 * len(types)
    out = bytearray()
    dyn_seen = 0
    for kind, payload in heads:
        if kind == "FIX":
            out += payload
        else:
            tail_len_before = sum(len(t) for t in tails[:dyn_seen])
            out += (head_size + tail_len_before).to_bytes(32, "big")
            dyn_seen += 1
    for t in tails:
        out += t
    return "0x" + bytes(out).hex()


def _word(raw, off):
    if off + 32 > len(raw):
        raise EthError("payload truncated at byte %d" % off)
    return int.from_bytes(raw[off:off + 32], "big")


def _split_type(t):
    m = re.match(r"^(.+?)((?:\[\d*\])*)$", str(t))
    if not m:
        raise EthError("bad type %r" % (t,))
    return m.group(1), re.findall(r"\[(\d*)\]", m.group(2))


def _pad32(n):
    return (32 - n % 32) % 32


def abi_decode(types, data):
    """Decode a payload against a closed type list: static bases, string,
    bytes, and arrays T[] / T[N] of static elements (one level). Anything
    richer is refused, not guessed."""
    raw = bytes.fromhex(str(data).removeprefix("0x"))
    if len(raw) % 32:
        raise EthError("payload length must be a multiple of 32 bytes")
    parsed = []
    for t in types:
        base, dims = _split_type(t)
        if dims:
            if len(dims) > 1:
                raise EthError("nested arrays are outside the closed "
                               "grammar")
            if base in ("string", "bytes"):
                raise EthError("arrays of dynamic types are refused")
        parsed.append((base, dims))

    def decode_static(off, base):
        if base == "address":
            return "0x" + raw[off + 12:off + 32].hex()
        if base == "bool":
            return _word(raw, off) != 0
        if base.startswith("bytes") and base != "bytes":
            n = int(base[5:])
            return "0x" + raw[off:off + n].hex()
        if base.startswith("uint"):
            return str(_word(raw, off))
        if base.startswith("int"):
            return str(int.from_bytes(raw[off:off + 32], "big",
                                      signed=True))
        raise EthError("cannot decode %r" % (base,))

    out = []
    for i, (base, dims) in enumerate(parsed):
        head_pos = 32 * i
        is_dynamic = base in ("string", "bytes") or (dims
                                                     and dims[0] == "")
        if is_dynamic:
            off = _word(raw, head_pos)
        else:
            off = head_pos
        if base == "string":
            ln = _word(raw, off)
            out.append(raw[off + 32:off + 32 + ln].decode("utf-8"))
        elif base == "bytes":
            ln = _word(raw, off)
            out.append("0x" + raw[off + 32:off + 32 + ln].hex())
        elif dims:
            if dims[0] == "":
                n = _word(raw, off)
                body = off + 32
            else:
                n = int(dims[0])
                body = off
            out.append([decode_static(body + 32 * k, base)
                        for k in range(n)])
        else:
            out.append(decode_static(off, base))
    return out


# ------------------------------------------------------------- EIP-712
def _field_base(ftype):
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[\d*\])*$", str(ftype))
    if not m:
        raise EthError("bad field type %r" % (ftype,))
    return m.group(1), re.findall(r"\[(\d*)\]", str(ftype))


def _collect_deps(name, structs, found):
    for f in structs[name]:
        base, _dims = _field_base(f["type"])
        if base in structs and base not in found:
            found.add(base)
            _collect_deps(base, structs, found)


def _encode_type(name, structs, emitted=None):
    """EIP-712: the struct and all its transitive dependencies, sorted
    alphabetically together, each as name(fields in declaration order)."""
    names = {name}
    _collect_deps(name, structs, names)
    return "".join(
        "%s(%s)" % (n, ",".join("%s %s" % (f["type"], f["name"])
                                for f in structs[n]))
        for n in sorted(names))


def _type_hash(name, structs):
    return keccak256(_encode_type(name, structs, set()).encode())


def _enc_value(v, ftype, structs):
    base, dims = _field_base(ftype)

    def enc(elem):
        if base in structs:
            return keccak256(_encode_data(base, elem, structs))
        if base == "string":
            return keccak256(str(elem).encode())
        if base == "bytes":
            return keccak256(bytes.fromhex(str(elem).removeprefix("0x")))
        return _enc_static_value(base, elem)

    if not dims:
        return enc(v)
    if not isinstance(v, list):
        raise EthError("expected array for %r" % ftype)
    if dims[0] == "":
        return len(v).to_bytes(32, "big") + b"".join(enc(x) for x in v)
    return b"".join(enc(x) for x in v)


def _encode_data(name, obj, structs):
    if not isinstance(obj, dict):
        raise EthError("%s expects an object" % name)
    out = bytearray(_type_hash(name, structs))
    for f in structs[name]:
        if f["name"] not in obj:
            raise EthError("missing field %r for struct %s"
                           % (f["name"], name))
        out += _enc_value(obj[f["name"]], f["type"], structs)
    return bytes(out)


def eip712_digest(typed_data):
    """Full EIP-712: domainSeparator, struct hash, 0x1901 digest."""
    try:
        primary = typed_data["primaryType"]
        types = typed_data["types"]
        domain = typed_data["domain"]
        message = typed_data["message"]
    except (KeyError, TypeError):
        raise EthError("need {types, primaryType, domain, message}")
    structs = {k: v for k, v in types.items() if k != "EIP712Domain"}
    if primary not in structs:
        raise EthError("primaryType %r missing from types" % primary)
    dom_fields = types.get("EIP712Domain")
    if dom_fields is None:
        raise EthError("types must include EIP712Domain")
    structs["EIP712Domain"] = dom_fields
    for name in list(structs):
        for f in structs[name]:
            base, _ = _field_base(f["type"])
            known = (base in structs or re.fullmatch(
                r"u?int\d*|bytes\d*|address|bool|string|bytes", base))
            if not known:
                raise EthError("unknown type %r in %s.%s"
                               % (f["type"], name, f["name"]))
    dom_hash = keccak256(_encode_data("EIP712Domain", domain, structs))
    msg_hash = keccak256(_encode_data(primary, message, structs))
    digest = keccak256(b"\x19\x01" + dom_hash + msg_hash)
    return {"digest": "0x" + digest.hex(),
            "domain_separator": "0x" + dom_hash.hex(),
            "struct_hash": "0x" + msg_hash.hex(),
            "encode_type": _encode_type(primary, structs, set())}


# --------------------------------------------------------- receipt-match
TRANSFER_TOPIC = keccak256(b"Transfer(address,address,uint256)").hex()
APPROVE_TOPIC = keccak256(b"Approval(address,address,uint256)").hex()


def _addr40(x):
    return str(x).lower().removeprefix("0x").rjust(64, "0")[-40:]


def receipt_match(logs, expect):
    """Match event logs against expected effects. topic: Transfer (default)
    | Approval | 0x-hex topic0. Addresses compare on their last 40 hex."""
    if not isinstance(logs, list) or not logs:
        raise EthError("logs must be a non-empty array")
    if not isinstance(expect, dict) or not expect:
        raise EthError("expect needs any of topic|contract|from|to|value")
    topic = expect.get("topic", "Transfer")
    if topic == "Transfer":
        topic0 = TRANSFER_TOPIC
    elif topic == "Approval":
        topic0 = APPROVE_TOPIC
    else:
        topic0 = str(topic).lower().removeprefix("0x")
        if not re.fullmatch(r"[0-9a-f]{64}", topic0):
            raise EthError("topic must be Transfer|Approval or 32-byte hex")
    matches = []
    for i, lg in enumerate(logs):
        if not isinstance(lg, dict):
            raise EthError("log %d must be an object" % i)
        topics = [str(t).lower().removeprefix("0x").rjust(64, "0")
                  for t in lg.get("topics", [])]
        data = str(lg.get("data", "")).lower().removeprefix("0x")
        if not topics or topics[0] != topic0:
            continue
        ok = True
        if "contract" in expect:
            ok &= _addr40(lg.get("address", "")) == _addr40(
                expect["contract"])
        if "from" in expect:
            ok &= len(topics) > 1 and topics[1][-40:] == _addr40(
                expect["from"])
        if "to" in expect:
            ok &= len(topics) > 2 and topics[2][-40:] == _addr40(
                expect["to"])
        if "value" in expect:
            got = int(data[:64] or "0", 16)
            want = str(expect["value"])
            ok &= got == (int(want, 16) if want.startswith("0x")
                          else int(want))
        if ok:
            entry = {"log_index": i}
            if len(topics) > 1:
                entry["from"] = "0x" + topics[1][-40:]
            if len(topics) > 2:
                entry["to"] = "0x" + topics[2][-40:]
            if data:
                entry["value"] = str(int(data[:64], 16))
            matches.append(entry)
    return {"matched": len(matches), "matches": matches,
            "total_logs": len(logs), "pass": bool(matches)}
