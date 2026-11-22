"""Deterministic hashes, encodings and identity (Bundle 5, TOOLS-50 #31-36).

Pure stdlib. No LLM, no storage, no clock: a model cannot hash, will not
agree with itself on what a digest looks like, and will happily invent one
— this is the tool that replaces that whole failure class.
"""

import base64
import binascii
import hashlib
import json
import re
import unicodedata
import uuid as _uuid
from datetime import datetime, timezone


class IdentityError(Exception):
    pass


ALGOS = {"md5": "16", "sha1": "20", "sha256": "32", "sha512": "64",
         "blake2b": "64"}


def _digest(data, algo):
    raw = _as_bytes(data)
    return hashlib.new(algo, raw).hexdigest()


def _as_bytes(data):
    if not isinstance(data, str):
        raise IdentityError("data must be a string")
    return data.encode("utf-8")


def _b64_auto(text):
    """Strict decode with auto-padding; accepts standard and urlsafe."""
    t = text.strip().rstrip("=")
    pad = "=" * (-len(t) % 4)
    for alt in (None, b"-_"):
        try:
            return base64.b64decode(t + pad, altchars=alt, validate=True)
        except (binascii.Error, ValueError):
            continue
    raise IdentityError("not valid base64 (standard or urlsafe)")


def hash_digest(data, algo="sha256", input_kind="text"):
    if algo not in ALGOS:
        raise IdentityError("unknown algo: %r (closed: %s)"
                            % (algo, ", ".join(sorted(ALGOS))))
    if input_kind == "text":
        raw = _as_bytes(data)
    elif input_kind == "base64":
        raw = _b64_auto(data)
    elif input_kind == "hex":
        try:
            raw = bytes.fromhex(data.strip())
        except ValueError:
            raise IdentityError("not valid hex")
    else:
        raise IdentityError('input_kind must be "text", "base64" or "hex"')
    h = hashlib.new(algo, raw).hexdigest()
    return {"algo": algo, "hex": h,
            "base64": base64.b64encode(bytes.fromhex(h)).decode("ascii"),
            "input_bytes": len(raw)}


def enc_convert(text, op="encode", variant="base64", padding=True):
    if op not in ("encode", "decode"):
        raise IdentityError('op must be "encode" or "decode"')
    if variant not in ("base64", "base64url", "hex"):
        raise IdentityError("unknown variant: %r (closed: base64, "
                            "base64url, hex)" % variant)
    if op == "encode":
        raw = _as_bytes(text)
        if variant == "base64":
            out = base64.b64encode(raw).decode("ascii")
        elif variant == "base64url":
            out = base64.urlsafe_b64encode(raw).decode("ascii")
        else:
            out = raw.hex()
        if variant != "hex" and not padding:
            out = out.rstrip("=")
        return {"op": op, "variant": variant, "result": out,
                "input_bytes": len(raw), "output_bytes": len(out)}
    if variant == "hex":
        try:
            raw = bytes.fromhex(text.strip())
        except ValueError:
            raise IdentityError("not valid hex")
        out = raw.decode("utf-8", errors="strict") \
            if _valid_utf8(raw) else None
        if out is None:
            raise IdentityError("hex decodes to invalid UTF-8")
        return {"op": op, "variant": variant, "result": out,
                "input_bytes": len(text), "output_bytes": len(raw)}
    raw = _b64_auto(text.strip())
    try:
        out = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise IdentityError("bytes do not decode as UTF-8 text")
    return {"op": op, "variant": variant, "result": out,
            "input_bytes": len(text), "output_bytes": len(raw)}


def _valid_utf8(raw):
    try:
        raw.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def jwt_decode(token):
    """Decode — never verify. The signature is exposed, not trusted; an
    agent that needs verification already has the key, and pretending to
    check without one is exactly the theater this product refuses."""
    if not isinstance(token, str):
        raise IdentityError("token must be a string")
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise IdentityError("not a JWS compact token (3 dot-separated parts)")
    try:
        header = json.loads(_b64_auto(parts[0]))
        payload = json.loads(_b64_auto(parts[1]))
    except (IdentityError, ValueError):
        raise IdentityError("JWT segment is not valid base64url JSON")
    if not isinstance(header, dict) or not isinstance(payload, dict):
        raise IdentityError("JWT header/payload must be JSON objects")
    out = {"header": header, "payload": payload, "signature": parts[2],
           "verified": False, "note": "decoded, NOT cryptographically "
                                      "verified — no key material seen"}
    for claim in ("iat", "exp", "nbf"):
        v = payload.get(claim)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            try:
                out[claim + "_iso"] = datetime.fromtimestamp(
                    v, tz=timezone.utc).isoformat()
            except (OverflowError, OSError, ValueError):
                pass
    return out


_NS = {"url": _uuid.NAMESPACE_URL, "dns": _uuid.NAMESPACE_DNS,
       "oid": _uuid.NAMESPACE_OID, "x500": _uuid.NAMESPACE_X500}


def id_uuid(op="v5", name=None, namespace="url", seed=None, at=None):
    if op == "v5":
        if not name:
            raise IdentityError("v5 requires 'name'")
        if namespace in _NS:
            ns = _NS[namespace]
        else:
            try:
                ns = _uuid.UUID(str(namespace))
            except ValueError:
                raise IdentityError("namespace must be url|dns|oid|x500 or "
                                    "a UUID string")
        u = _uuid.uuid5(ns, str(name))
        return {"uuid": str(u), "urn": u.urn, "version": 5,
                "namespace": namespace, "name": name}
    if op == "v4_seeded":
        source = seed if seed is not None else name
        if source is None:
            raise IdentityError("v4_seeded requires 'seed' (or name)")
        digest = hashlib.sha256(str(source).encode("utf-8")).digest()
        u = _uuid.UUID(bytes=digest[:16], version=4)
        return {"uuid": str(u), "urn": u.urn, "version": 4,
                "seeded_from": str(source)}
    if op == "v7":
        if at is None:
            raise IdentityError("v7 here requires 'at' (ms epoch or ISO) — "
                                "the wall clock would break same-bytes")
        if isinstance(at, str):
            if re.match(r"^\d+$", at.strip()):
                ms = int(at)
            else:
                dt = datetime.fromisoformat(at.replace("Z", "+00:00"))
                ms = int(dt.timestamp() * 1000)
        else:
            ms = int(at)
        rnd = hashlib.sha256(("v7:" + str(seed or "") + ":" +
                              str(ms)).encode()).digest()
        b = bytearray(ms.to_bytes(6, "big") + rnd[:10])
        b[6] = (7 << 4) | (b[6] & 0x0F)              # version 7
        b[8] = (0b10 << 6) | (b[8] & 0b00111111)     # variant
        u = _uuid.UUID(hex=b.hex())   # version bits set above; the stdlib
                                       # constructor only speaks 1/3/4/5
        return {"uuid": str(u), "urn": u.urn, "version": 7,
                "timestamp_ms": ms,
                "timestamp_iso": datetime.fromtimestamp(
                    ms / 1000, tz=timezone.utc).isoformat()}
    raise IdentityError("unknown op: %r (v5 | v4_seeded | v7)" % op)


_SLUG_SEP = re.compile(r"[^a-z0-9]+")


def id_slug(text, sep="-", lower=True, max_len=0):
    if not isinstance(text, str) or not text.strip():
        raise IdentityError("text must be a non-empty string")
    if sep not in ("-", "_"):
        raise IdentityError('sep must be "-" or "_"')
    s = unicodedata.normalize("NFKD", text)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    if lower:
        s = s.lower()
    s = _SLUG_SEP.sub(sep, s).strip(sep)
    truncated = False
    if max_len:
        if not isinstance(max_len, int) or isinstance(max_len, bool) \
                or max_len < 1:
            raise IdentityError("max_len must be a positive integer")
        if len(s) > max_len:
            cut = s[:max_len]
            if sep in cut:
                cut = cut.rsplit(sep, 1)[0] or cut
            s, truncated = cut, True
    return {"slug": s, "sep": sep, "truncated": truncated,
            "input": text}


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def fingerprint(value, kind="json"):
    if kind == "json":
        text = canonical_json(value)
        return {"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "canonical": text, "kind": kind}
    if kind == "csv":
        import csv as _csv
        import io as _io
        if not isinstance(value, str):
            raise IdentityError("csv fingerprint expects CSV text")
        rows = list(_csv.reader(_io.StringIO(value)))
        if not rows:
            raise IdentityError("empty csv")
        header = [h.strip() for h in rows[0]]
        recs = []
        for r in rows[1:]:
            if not any(c.strip() for c in r):
                continue
            recs.append({header[i] if i < len(header) else "":
                         r[i].strip() for i in range(len(r))})
        text = canonical_json(recs)
        return {"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "rows": len(recs), "kind": kind}
    raise IdentityError('kind must be "json" or "csv"')


HMAC_ALGOS = ("md5", "sha1", "sha224", "sha256", "sha384", "sha512")


def hmac_op(message, key, algo="sha256", key_kind="text",
            message_kind="text", signature=None):
    """RFC 2104 HMAC over stdlib hmac — constant-time verify. Ground truth
    in tests: RFC 4231 published vectors, not this code."""
    import hmac as _hmac
    if algo not in HMAC_ALGOS:
        raise IdentityError("unknown algo: %r (closed: %s)"
                            % (algo, ", ".join(HMAC_ALGOS)))
    kb = _b64_auto(key) if key_kind == "base64" else (
        bytes.fromhex(key.strip()) if key_kind == "hex"
        else _as_bytes(key))
    mb = _b64_auto(message) if message_kind == "base64" else (
        bytes.fromhex(message.strip()) if message_kind == "hex"
        else _as_bytes(message))
    out = {"algo": "hmac-" + algo}
    h = _hmac.new(kb, mb, algo).hexdigest()
    out["hex"] = h
    out["base64"] = base64.b64encode(bytes.fromhex(h)).decode("ascii")
    if signature is not None:
        sig = str(signature).strip().lower()
        if sig.startswith("0x"):
            sig = sig[2:]
        try:
            sig_b = bytes.fromhex(sig)
        except ValueError:
            sig_b = base64.b64decode(sig + "=" * (-len(sig) % 4))
        out["match"] = _hmac.compare_digest(sig_b, bytes.fromhex(h))
    return out


CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _b32_encode(n, length):
    out = ""
    for _ in range(length):
        out = CROCKFORD[n & 31] + out
        n >>= 5
    if n:
        raise IdentityError("value too large")
    return out


def _b32_decode(s, what):
    n = 0
    for ch in s.upper():
        d = CROCKFORD.find(ch)
        if d < 0:
            raise IdentityError("invalid %s char %r (Crockford base32)"
                               % (what, ch))
        n = (n << 5) | d
    return n


def ulid_op(mode="make", timestamp_ms=None, entropy=None, seed=None,
            ulid=None, ids=None):
    """ULID (48-bit ms + 80-bit entropy), Crockford base32, uppercase 26.
    No wall clock inside the suite: make REQUIRES timestamp_ms and either
    entropy-hex or seed (entropy = sha256('mechacut-ulid:'+seed)[:10]) —
    same inputs -> same id, which is what makes it an idempotency key."""
    if mode == "make":
        if not isinstance(timestamp_ms, int) or not (0 <= timestamp_ms
                                                     < 2**48):
            raise IdentityError("timestamp_ms (int, 0..2^48-1) required — "
                                "no hidden clock: deterministic ids only")
        if entropy:
            try:
                eb = bytes.fromhex(entropy.strip())
            except ValueError:
                raise IdentityError("entropy must be 20 hex chars")
            if len(eb) != 10:
                raise IdentityError("entropy must be 10 bytes (20 hex)")
        elif seed:
            eb = hashlib.sha256(("mechacut-ulid:" + str(seed)).encode()
                                ).digest()[:10]
        else:
            raise IdentityError("entropy or seed required")
        u = (_b32_encode(timestamp_ms, 10)
             + _b32_encode(int.from_bytes(eb, "big"), 16))
        return {"ulid": u, "timestamp_ms": timestamp_ms,
                "entropy_hex": eb.hex()}
    if mode == "parse":
        if not isinstance(ulid, str) or len(ulid) != 26:
            raise IdentityError("ulid must be 26 chars")
        ts = _b32_decode(ulid[:10], "timestamp")
        ent = _b32_decode(ulid[10:], "entropy")
        return {"ulid": ulid.upper(), "timestamp_ms": ts,
                "entropy_hex": format(ent, "020x")}
    if mode == "sort":
        if not isinstance(ids, list) or not ids:
            raise IdentityError("ids must be a non-empty list")
        bad = [i for i in ids if not (isinstance(i, str) and len(i) == 26
                                      and all(c.upper() in CROCKFORD
                                              for c in i))]
        if bad:
            raise IdentityError("invalid ulid(s): %s"
                               % ", ".join(map(str, bad[:3])))
        srt = sorted(map(str.upper, set(ids)))
        return {"sorted": srt, "count": len(srt),
                "oldest": srt[0], "newest": srt[-1]}
    raise IdentityError('mode must be "make", "parse" or "sort"')
