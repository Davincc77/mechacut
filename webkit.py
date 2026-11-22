"""Bundle 30 lot 1 — WEB/RENDU: ssh/fingerprint + zip/verify.

Both anchored to vectors produced THIS repo session with the real
OpenSSH and Info-ZIP binaries (ssh-keygen -lf / -E md5 / -l / -t), not
recomputed by the product — the honesty rule holds even when the tool
and the test would share a bug by construction.

zip/verify reads the archive in memory and never extracts: names, sizes,
stored-vs-computed CRC verdict per entry. An archive that gets a green
verdict here was never written to disk.
"""
import base64
import binascii
import hashlib
import io
import re
import struct
import zipfile


class WebError(Exception):
    pass


# ---------------------------------------------------------- ssh fp
_B64_RE = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")


def ssh_fingerprint(line):
    if not isinstance(line, str) or not line.strip():
        raise WebError("line must be a public key line")
    parts = line.split()
    if len(parts) < 2:
        raise WebError("expected '<type> <base64> [comment]'")
    ktype, b64 = parts[0], parts[1]
    comment = " ".join(parts[2:]) or None
    if not _B64_RE.match(b64):
        raise WebError("key blob is not valid base64")
    try:
        blob = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError) as e:
        raise WebError("key blob: %s" % e)
    # read the length-prefixed type field and confirm it matches
    if len(blob) < 4:
        raise WebError("blob too short")
    (tl,) = struct.unpack(">I", blob[:4])
    if tl > len(blob) - 4:
        raise WebError("declared type length exceeds blob")
    declared = blob[4:4 + tl].decode("ascii", "replace")
    if declared != ktype:
        raise WebError("type field %r disagrees with blob (%r)"
                       % (ktype, declared))
    sha = "SHA256:" + base64.b64encode(
        hashlib.sha256(blob).digest()).decode().rstrip("=")
    md = hashlib.md5(blob).hexdigest()
    return {"type": ktype, "comment": comment,
            "fingerprint_sha256": sha,
            "fingerprint_md5": ":".join(md[i:i + 2]
                                        for i in range(0, 32, 2)),
            "md5_deprecated": True,
            "blob_bytes": len(blob)}


# ---------------------------------------------------------- zip
_MAX = 32 * 1024 * 1024


def zip_verify(blob_b64):
    if not isinstance(blob_b64, str) or not blob_b64.strip():
        raise WebError("blob_b64 required (archive bytes, base64)")
    clean = "".join(blob_b64.split())
    try:
        raw = base64.b64decode(clean, validate=True)
    except (binascii.Error, ValueError) as e:
        raise WebError("not valid base64: %s" % e)
    if len(raw) > _MAX:
        raise WebError("archive exceeds the 32 MB in-memory cap")
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as e:
        raise WebError("bad zip: %s" % e)
    entries = []
    for info in zf.infolist():
        crc_ok = None
        computed = None
        try:
            data = zf.read(info.filename)   # zipfile itself checks CRC
            computed = "%08x" % (binascii.crc32(data) & 0xFFFFFFFF)
            crc_ok = computed == "%08x" % info.CRC
        except (zipfile.BadZipFile, EOFError, NotImplementedError):
            crc_ok = False      # corrupt member, or unsupported method:
            computed = None     # a verdict, not a crash
        entries.append({"name": info.filename,
                        "size": info.file_size,
                        "compressed_size": info.compress_size,
                        "crc32_stored": "%08x" % info.CRC,
                        "crc32_computed": computed,
                        "crc_ok": crc_ok,
                        "date": "%04d-%02d-%02d" % info.date_time[:3],
                        "encrypted": bool(info.flag_bits & 0x1)})
    bad_names = [e["name"] for e in entries if not e["crc_ok"]]
    ok = not bad_names
    return {"entries": entries, "entry_count": len(entries),
            "total_size": sum(e["size"] for e in entries),
            "archive_sha256": hashlib.sha256(raw).hexdigest(),
            "extracted": False,
            "bad_entries": bad_names,
            "integrity_ok": ok}


# ---------------------------------------------------------- lot 4
_CACHE_DIR_RE = re.compile(
    r"^\s*(no-store|no-cache|must-revalidate|proxy-revalidate|"
    r"max-stale|min-fresh|only-if-cached|"
    r"(?:s-maxage|max-age|stale-while-revalidate|"
    r"stale-if-error)=\d+)\s*$", re.I)


def web_cache(header, method="GET", conditional=False):
    """HTTP cache verdict from the header TEXT alone (closed rules from
    RFC 9111 §3 and §4): parse Cache-Control, flag unknown directives
    (legal but inert), and say what a compliant cache must do."""
    if not isinstance(header, str):
        raise WebError("header must be the Cache-Control value text")
    known, unknown, age_s = [], [], None
    for part in header.split(","):
        p_ = part.strip()
        if not p_:
            continue
        if _CACHE_DIR_RE.match(p_):
            known.append(p_.lower())
            if "=" in p_:
                k, _, v = p_.partition("=")
                if k.strip().lower() == "max-age":
                    age_s = int(v)
        else:
            unknown.append(p_)
    low = " ".join(known)
    if "no-store" in low:
        action = "forbidden_to_store"
    elif method.upper() not in ("GET", "HEAD"):
        action = "not_cacheable_method"
    elif "no-cache" in low:
        action = "store_but_revalidate_every_use"
    elif age_s is not None and age_s == 0:
        action = "must_revalidate_before_use"
    elif "must-revalidate" in low:
        action = "use_until_stale_then_revalidate"
    elif age_s is None:
        action = "heuristic_freshness_allowed"
    else:
        action = "fresh_for_max_age_seconds"
    out = {"directives": known, "unknown_directives": unknown,
           "max_age_seconds": age_s, "action": action,
           "rfc": "9111 s3 (freshness), s4 (stored responses)"}
    if conditional:
        out["conditional_request"] = ("revalidate-with-origin: ETag/"
                                      "Last-Modified comparison is the "
                                      "server's call, not the header's")
    return out


def compress_gzip(payload_b64, mode="compress", level=9):
    """Deterministic gzip: RFC 1952 with MTIME forced to 0 and no FNAME
    — the same input bytes produce the same archive bytes on any machine,
    which the stdlib gzip module does NOT guarantee by default."""
    import base64 as _b64
    import gzip as _gzip
    import zlib as _zlib
    if not isinstance(payload_b64, str) or not payload_b64.strip():
        raise WebError("payload_b64 required")
    try:
        raw = _b64.b64decode("".join(payload_b64.split()), validate=True)
    except Exception as e:
        raise WebError("payload is not base64: %s" % e)
    if len(raw) > 8 * 1024 * 1024:
        raise WebError("payload exceeds the 8 MB cap")
    if mode == "compress":
        if not 1 <= int(level) <= 9:
            raise WebError("level must be 1-9")
        arc = _gzip.compress(raw, compresslevel=int(level), mtime=0)
        return {"mode": "compress",
                "gzip_b64": _b64.b64encode(arc).decode(),
                "input_bytes": len(raw), "archive_bytes": len(arc),
                "ratio": round(len(arc) / len(raw), 4) if raw else 1.0,
                "deterministic": "mtime=0, no FNAME (RFC 1952)"}
    if mode == "decompress":
        try:
            out = _gzip.decompress(raw)
        except (_zlib.error, OSError, EOFError) as e:
            raise WebError("not a valid gzip stream: %s" % e)
        return {"mode": "decompress",
                "payload_b64": _b64.b64encode(out).decode(),
                "archive_bytes": len(raw), "output_bytes": len(out)}
    raise WebError("mode is compress or decompress")
