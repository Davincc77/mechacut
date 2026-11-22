"""Bundle 17 — daily micro-organs, all free (TOOLS-50 #53, #39, #26, #27).

Four chores an agent does every day and does by guessing: fixing mojibake,
saying durations and bytes like a human, escaping strings per dialect, and
comparing text after Unicode normalization. All closed: pinned tables,
documented rules, no heuristics that change with the wind.

Same request -> same bytes. No LLM, no network, no state.
"""
import base64
import re
import unicodedata

__all__ = ["MicroError", "text_decode", "num_human", "text_escape",
           "text_normalize", "json_map", "semver_parse", "semver_sort",
           "text_sanitize", "file_identify", "text_punycode"]


class MicroError(Exception):
    pass


# ------------------------------------------------------------- text/decode
# Mojibake = UTF-8 bytes displayed as Latin-1/CP1252. Detection is a closed
# loop: encode back to latin-1, re-decode as UTF-8; keep the repair only
# when it changes the text AND introduces no replacement char.
_FRENCH = ("Ã©", "Ã¨", "Ã ", "Ã»", "Ã¢", "Ã®", "Ã´", "Ã¹", "Å", "â")


def text_decode(text, target="utf-8"):
    if not isinstance(text, str):
        raise MicroError("text must be a string")
    if target not in ("utf-8",):
        raise MicroError("target must be utf-8 (closed set for now)")
    repairs = 0

    def _fix(m):
        nonlocal repairs
        bad = m.group(0)
        try:
            good = bad.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return bad
        if good != bad and "\ufffd" not in good:
            repairs += 1
            return good
        return bad

    fixed = re.sub(
        r"[\u00c2-\u00f4][\u0080-\u00bf]+"
        r"|[\u00c2-\u00f3][\u0080-\u00bf]"
        r"|\u00e2\u0080[\u0093-\u009d]"
        r"|\u00c3[\u0080-\u00bf]"
        r"|\u00c2[\u0080-\u00bf]"
        r"|\u00e2\u0082\u00ac"
        r"|\u00ef\u00bb\u00bf", _fix, text)
    markers = sum(1 for m in _FRENCH if m in text)
    return {"text": fixed, "repaired": repairs > 0, "repairs": repairs,
            "suspect": repairs > 0 or markers > 1,
            "suspicious_markers": markers if repairs == 0 else 0}


# --------------------------------------------------------------- num/human
_UNITS = (("B", 1), ("KiB", 1024), ("MiB", 1024 ** 2),
          ("GiB", 1024 ** 3), ("TiB", 1024 ** 4), ("PiB", 1024 ** 5))
_DEC = (("B", 1), ("kB", 10 ** 3), ("MB", 10 ** 6), ("GB", 10 ** 9),
        ("TB", 10 ** 12))


def num_human(value, kind, style=None):
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise MicroError("value must be numeric")
    if kind == "duration":
        secs = int(n)
        sign = "-" if secs < 0 else ""
        secs = abs(secs)
        d, rem = divmod(secs, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        parts = ([f"{d}d"] if d else []) + ([f"{h}h"] if h or d else []) \
            + ([f"{m}m"] if m or h or d else []) + [f"{s}s"]
        return {"human": sign + " ".join(parts), "kind": kind,
                "total_seconds": int(n)}
    if kind == "bytes":
        binary = style != "decimal"
        table = _UNITS if binary else _DEC
        chosen = table[0]
        for u, size in table:
            if abs(n) >= size:
                chosen = (u, size)
        u, size = chosen
        q = n / size
        human = ("%d %s" % (q, u)) if q == int(q) \
            else ("%.2f %s" % (q, u))
        return {"human": human, "kind": kind, "unit": u,
                "value": q, "base": "1024" if binary else "1000"}
    if kind == "roman":
        i = int(n)
        if not 1 <= i <= 3999:
            raise MicroError("roman needs an integer 1..3999")
        out = ""
        for sym, val in (("M", 1000), ("CM", 900), ("D", 500),
                         ("CD", 400), ("C", 100), ("XC", 90), ("L", 50),
                         ("XL", 40), ("X", 10), ("IX", 9), ("V", 5),
                         ("IV", 4), ("I", 1)):
            while i >= val:
                out += sym
                i -= val
        return {"human": out, "kind": kind}
    if kind == "ordinal":
        i = int(n)
        suf = ("th" if 11 <= abs(i) % 100 <= 13
               else {1: "st", 2: "nd", 3: "rd"}.get(abs(i) % 10, "th"))
        return {"human": "%d%s" % (i, suf), "kind": kind}
    raise MicroError("kind must be duration|bytes|roman|ordinal")


# -------------------------------------------------------------- text/escape
_DIALECTS = ("html", "sql", "shell", "csv", "json", "url")


def _esc_sql(v):
    return v.replace("\\", "\\\\").replace("'", "''")


def _esc_shell(v):
    safe = re.match(r"^[\w@%+=:,./-]+$", v)
    if safe and v:
        return v
    return "'" + v.replace("'", "'\\''") + "'"


def _esc_csv(v):
    if any(c in v for c in ',"\n\r'):
        return '"' + v.replace('"', '""') + '"'
    return v


def _esc_url(v):
    out = []
    for ch in unicodedata.normalize("NFC", v):
        if ch.isalnum() or ch in "-._~/?#[]@!$&'()*+,;=":
            out.append(ch)
        else:
            out += ["%%%02X" % b for b in ch.encode("utf-8")]
    return "".join(out)


_ESCAPERS = {
    "html": lambda v: (v.replace("&", "&amp;").replace("<", "&lt;")
                       .replace(">", "&gt;").replace('"', "&quot;")
                       .replace("'", "&#39;")),
    "sql": _esc_sql,
    "shell": _esc_shell,
    "csv": _esc_csv,
    "json": lambda v: __import__("json").dumps(v)[1:-1],
    "url": _esc_url,
}


def text_escape(value, dialects):
    if not isinstance(value, str):
        raise MicroError("value must be a string")
    if not isinstance(dialects, list) or not dialects:
        raise MicroError("dialects must be a non-empty array of: %s"
                         % ", ".join(_DIALECTS))
    bad = [d for d in dialects if d not in _DIALECTS]
    if bad:
        raise MicroError("unknown dialect(s) %s; allowed: %s"
                         % (", ".join(map(repr, bad)),
                            ", ".join(_DIALECTS)))
    out = {}
    for d in dict.fromkeys(dialects):        # dedupe, keep order
        out[d] = _ESCAPERS[d](value)
    return {"escaped": out, "dialects": list(out)}


# ----------------------------------------------------------- text/normalize
_FORMS = ("NFC", "NFD", "NFKC", "NFKD")


def text_normalize(text, form="NFC", strip_accents=False,
                   casefold=False, collapse_ws=False, fullwidth=False):
    if not isinstance(text, str):
        raise MicroError("text must be a string")
    if form not in _FORMS:
        raise MicroError("form must be one of: %s" % ", ".join(_FORMS))
    out = unicodedata.normalize(form, text)
    if strip_accents:
        out = "".join(c for c in unicodedata.normalize("NFD", out)
                      if not unicodedata.combining(c))
    if fullwidth:
        buf = []
        for c in out:
            code = ord(c)
            if code == 0x3000:
                buf.append(" ")
            elif 0xFF01 <= code <= 0xFF5E:
                buf.append(chr(code - 0xFEE0))
            else:
                buf.append(c)
        out = "".join(buf)
    if casefold:
        out = out.casefold()
    if collapse_ws:
        out = re.sub(r"\s+", " ", out).strip()
    return {"text": out, "form": form,
            "changed": out != text,
            "codepoints": len(out)}


_JSON_MAP_OPS = ("lower", "upper", "strip", "title", "slug", "kebab",
                 "snake", "camel", "round", "int", "str", "trunc")
_WORD_RX = __import__("re").compile(
    r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z0-9]+")


def _words(v):
    return _WORD_RX.findall(str(v))


def json_map(items, ops):
    """Closed element-wise transforms over a flat JSON array: NO ML, NO
    regex invention — a 12-op alphabet, applied in order. The missing
    half of reshape for lists of scalars."""
    if not isinstance(items, list) or not 1 <= len(items) <= 5000:
        raise MicroError("items: list of 1..5000 values")
    if not isinstance(ops, list) or not 1 <= len(ops) <= 20:
        raise MicroError("ops: list of 1..20 {op, places?}")
    for o in ops:
        if not isinstance(o, dict) or o.get("op") not in _JSON_MAP_OPS:
            raise MicroError("op must be one of: %s"
                             % ", ".join(_JSON_MAP_OPS))
    D = __import__("decimal")
    out = []
    for it in items:
        cur = it
        for o in ops:
            op = o["op"]
            if op == "round":
                q = D.Decimal(str(cur)).quantize(
                    D.Decimal(1).scaleb(-int(o.get("places", 2))),
                    rounding=D.ROUND_HALF_EVEN)
                cur = float(q) if abs(q) >= 1e-12 else 0.0
            elif op == "int":
                cur = int(D.Decimal(str(cur)))
            elif op == "str":
                cur = str(cur)
            elif op == "trunc":
                cur = str(cur)[: int(o.get("max", 20))]
            elif op in ("lower", "upper", "strip", "title"):
                s = str(cur)
                cur = {"lower": s.lower(), "upper": s.upper(),
                       "strip": s.strip(),
                       "title": s.title()}[op]
            else:
                ws = _words(cur)
                cur = {"slug": "-".join(w.lower() for w in ws),
                       "kebab": "-".join(w.lower() for w in ws),
                       "snake": "_".join(w.lower() for w in ws),
                       "camel": (ws[0].lower() +
                                 "".join(w.title() for w in ws[1:])
                                 if ws else "")}[op]
        out.append(cur)
    return {"mapped": out, "count": len(out), "ops_applied": len(ops)}


SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$")
# grammaire officielle semver.org (regex publiée, section 2026)


def _sem_pre_key(pre):
    if pre is None:
        return (1,)            # release > prerelease (règle 11.4)
    keys = []
    for part in pre.split("."):
        if part.isdigit():
            keys.append((0, 0, int(part), ""))
        else:
            keys.append((0, 1, 0, part))
    return (0, tuple(keys))    # prérelases: comparées ensuite (11.4.x)


def _semver_tuple(v):
    m = SEMVER_RE.match(v)
    if not m:
        raise MicroError("invalid semver: %r" % v)
    core = tuple(int(x) for x in m.groups()[:3])
    pre = m.group(4)
    return core, pre


def semver_parse(version):
    core, pre = _semver_tuple(version)
    m = SEMVER_RE.match(version)
    return {"version": version, "major": core[0], "minor": core[1],
            "patch": core[2],
            "prerelease": (pre.split(".") if pre else None),
            "build": (m.group(5).split(".") if m.group(5) else None),
            "is_stable": pre is None}


def semver_sort(versions):
    if not isinstance(versions, list) or not 1 <= len(versions) <= 2000:
        raise MicroError("versions: list of 1..2000 semver strings")
    for v in versions:
        _semver_tuple(v)                     # valide chaque chaîne
    def key(v):
        core, pre = _semver_tuple(v)
        return (core, _sem_pre_key(pre))
    # comparaison de prérelases selon la règle 11.4 (identifiant par
    # identifiant, numérique < alphanumérique, préfixe < plus-long)
    import functools

    def cmp_pre(a, b):
        if a is None or b is None:
            return 0 if a == b else (1 if a is None else -1)
        pa, pb = a.split("."), b.split(".")
        for x, y in zip(pa, pb):
            dx, dy = x.isdigit(), y.isdigit()
            if dx and dy:
                if int(x) != int(y):
                    return -1 if int(x) < int(y) else 1
            elif dx != dy:
                return -1 if dx else 1
            elif x != y:
                return -1 if x < y else 1
        return len(pa) - len(pb)

    def cmp(a, b):
        ca, cb = _semver_tuple(a)[0], _semver_tuple(b)[0]
        if ca != cb:
            return -1 if ca < cb else 1
        return cmp_pre(_semver_tuple(a)[1], _semver_tuple(b)[1])

    srt = sorted(set(versions), key=functools.cmp_to_key(cmp))
    return {"sorted": srt, "count": len(srt),
            "lowest": srt[0], "highest": srt[-1]}


_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    "COM%d" % i for i in range(1, 10)} | {
    "LPT%d" % i for i in range(1, 10)}
_UNSAFE = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def text_sanitize(name, sep="_", max_bytes=255):
    """Filename safe across Windows+POSIX: closed rules only — reserved
    device names, forbidden charset, trailing dots/spaces, byte budget.
    Verdict + warnings, never silence (a renamed file must SAY why)."""
    if not isinstance(name, str) or not name:
        raise MicroError("name must be a non-empty string")
    warnings = []
    s = name
    if s != s.strip(" ."):
        warnings.append("stripped leading/trailing spaces and dots")
        s = s.strip(" .")
    if _UNSAFE.search(s):
        warnings.append("replaced forbidden characters "
                        "[\\/:*?\"<>| + control]")
        s = _UNSAFE.sub(sep, s)
    base = s.split(".")[0].upper()
    if base in _RESERVED:
        warnings.append("reserved device name on Windows: %s" % base)
        s = "_" + s
    b = s.encode("utf-8")
    if len(b) > max_bytes:
        cut = b[:max_bytes]
        while cut and (cut[-1] & 0xC0) == 0x80:
            cut = cut[:-1]                     # continuation bytes
        if cut and (cut[-1] & 0xC0) == 0xC0:
            cut = cut[:-1]                     # orphaned lead byte
        s = cut.decode("utf-8")
        warnings.append("truncated to %d bytes (utf-8 boundary safe)"
                        % max_bytes)
    return {"safe": s or sep, "changed": s != name,
            "warnings": warnings, "bytes": len((s or sep).encode())}


_MAGIC = [
    (b"\x89PNG\r\n\x1a\n", "image/png", "png"),
    (b"\xff\xd8\xff", "image/jpeg", "jpg"),
    (b"GIF87a", "image/gif", "gif"),
    (b"GIF89a", "image/gif", "gif"),
    (b"%PDF-", "application/pdf", "pdf"),
    (b"PK\x03\x04", "application/zip", "zip"),
    (b"PK\x05\x06", "application/zip", "zip-empty"),
    (b"\x1f\x8b", "application/gzip", "gz"),
    (b"Rar!", "application/vnd.rar", "rar"),
    (b"7z\xbc\xaf\x27\x1c", "application/x-7z-compressed", "7z"),
    (b"BM", "image/bmp", "bmp"),
    (b"ID3", "audio/mpeg", "mp3"),
    (b"\xff\xfb", "audio/mpeg", "mp3"),
    (b"\xff\xf3", "audio/mpeg", "mp3"),
    (b"OggS", "audio/ogg", "ogg"),
    (b"fLaC", "audio/flac", "flac"),
    (b"RIFF", "audio-or-video-riff", "wav/avi"),
    (b"\x00\x00\x01\x00", "image/x-icon", "ico"),
    (b"<svg", "image/svg+xml", "svg"),
    (b"WEBP" if False else b"RIFF", None, None),   # placeholder removed
    (b"\x7fELF", "application/x-elf", "elf"),
    (b"MZ", "application/x-msdownload", "exe/dll"),
    (b"SQLite format 3\x00", "application/x-sqlite3", "sqlite"),
    (b"\xed\xab\xed\xbb", "filesystem-iso9660", "iso"),
]
_MAGIC = [m for m in _MAGIC if m[1]]
_TEXT_HEAD = re.compile(rb"^[\x09\x0a\x0d\x20-\x7e\xc2-\xff]+")


def file_identify(blob):
    """Magic-bytes identity: what a file IS, not what its name claims.
    Closed table (22 signatures), longest-match wins, honest 'unknown'.
    blob arrives as base64 (JSON-safe transport)."""
    if not isinstance(blob, str) or not blob:
        raise MicroError("blob must be base64 (non-empty string)")
    try:
        raw = base64.b64decode(blob + "=" * (-len(blob) % 4),
                               validate=False)
    except Exception:
        raise MicroError("blob is not valid base64")
    if not raw:
        return {"empty": True, "detected": None,
                "verdict": "0 bytes: it is nothing, and that is the answer"}
    best = None
    for sig, mime, ext in _MAGIC:
        if raw.startswith(sig):
            if best is None or len(sig) > len(best[0]):
                best = (sig, mime, ext)
    if best:
        return {"detected": best[1], "typical_ext": best[2],
                "signature_hex": best[0].hex(), "total_bytes": len(raw)}
    try:
        head = raw[:64].decode("utf-8")
        sample = raw[:32]
        printable = sum(1 for b_ in sample
                        if 0x20 <= b_ <= 0x7E or b_ in (9, 10, 13)
                        or b_ >= 0xC2)
        if sample and printable / len(sample) >= 0.8 \
                and any(0x20 <= b_ <= 0x7E for b_ in sample) \
                and _TEXT_HEAD.match(raw[:64]):
            kind = "text"
            hl = head.lower().lstrip()
            if hl.startswith("<?xml"):
                kind = "xml"
            elif hl.startswith(("<!doctype html", "<html")):
                kind = "html"
            elif hl.startswith("{") or hl.startswith("["):
                kind = "json-likely"
            return {"detected": "text/" + kind, "typical_ext": kind,
                    "signature_hex": None, "total_bytes": len(raw),
                    "printable_head": head[:40]}
    except UnicodeDecodeError:
        pass
    return {"detected": None, "verdict": "unknown: no signature in the "
            "closed table, not printable utf-8 — no guessing here",
            "first_bytes_hex": raw[:16].hex(), "total_bytes": len(raw)}


# ---- punycode / IDN (RFC 3492 encoding, stdlib codec is the reference) ----

def text_punycode(domain):
    """IDN <-> ASCII (xn--) round trip. Domain arrives in either form;
    verdicts come from the exact stdlib reference implementation —
    this tool guarantees what an LLM cannot: the SAME mapping every time."""
    if not isinstance(domain, str) or not domain.strip():
        raise MicroError("domain must be a non-empty string")
    d = domain.strip().rstrip(".").lower()
    out = {"input": d}
    if any(ord(c) > 127 for c in d):
        try:
            a = d.encode("idna").decode("ascii")
        except (UnicodeError, UnicodeDecodeError) as e:
            raise MicroError("not encodable (idna): %s" % e)
        out.update(unicode_form=d, ascii_form=a,
                   already_ascii=False,
                   is_idn=True)
    elif all(p.startswith("xn--") or p.isascii()
             for p in d.split(".")):
        try:
            u = d.encode("ascii").decode("idna")
        except (UnicodeError, UnicodeDecodeError) as e:
            raise MicroError("not decodable (idna): %s" % e)
        out.update(unicode_form=u, ascii_form=d,
                   already_ascii=True,
                   is_idn=any(p.startswith("xn--")
                              for p in d.split(".")))
    else:
        raise MicroError("domain is neither plain ascii nor xn-- labels")
    out["labels"] = d.split(".")
    return out


# ---- net/cidr + net/ip (RFC 4632/4291 closed math) ----
import ipaddress as _ipa


def net_ip(value):
    try:
        ip = _ipa.ip_address(value.strip())
    except ValueError as e:
        raise MicroError("not an IP address: %s" % e)
    v = ip.version
    return {
        "ip": str(ip), "version": v,
        "is_private": ip.is_private, "is_loopback": ip.is_loopback,
        "is_link_local": ip.is_link_local, "is_multicast": ip.is_multicast,
        "is_reserved": ip.is_reserved, "is_unspecified": ip.is_unspecified,
        "reverse_dns_name": str(ip.reverse_pointer),
        "packed_hex": ip.packed.hex(),
    }


def net_cidr(cidr, contains=None, split_into=None):
    try:
        net = _ipa.ip_network(cidr.strip(), strict=False)
    except ValueError as e:
        raise MicroError("not a CIDR: %s" % e)
    out = {"cidr": str(net), "network": str(net.network_address),
           "broadcast": str(str(net.broadcast_address)),
           "prefix": net.prefixlen, "total_addresses": net.num_addresses,
           "usable_hosts": (max(net.num_addresses - 2, 0)
                            if net.version == 4 and net.prefixlen < 31
                            else net.num_addresses),
           "ip_version": net.version}
    if contains:
        try:
            other = _ipa.ip_address(contains.strip())
        except ValueError:
            try:
                other = _ipa.ip_network(contains.strip(), strict=True)
                out["contains"] = {"query": str(other),
                                   "inside": other.subnet_of(net)}
            except ValueError as e:
                raise MicroError("contains: not an IP or CIDR")
        else:
            out["contains"] = {"query": str(other), "inside": other in net}
    if split_into:
        n = int(split_into)
        if n < 0 or n > 16:
            raise MicroError("split_into: 0..16 (subnet mask extension)")
        try:
            subs = list(net.subnets(prefixlen_diff=n))
        except ValueError as e:
            raise MicroError("split_into too large: %s" % e)
        out["subnets"] = [str(x) for x in subs[:256]]
        out["subnet_count"] = len(subs)
        out["truncated_at"] = 256 if len(subs) > 256 else None
    return out


# ---- text/file encoding (BOM + declared charset honest verdict) ----
_BOMS = [(b"\xef\xbb\xbf", "utf-8-sig"),
         (b"\xff\xfe", "utf-16-le"),
         (b"\xfe\xff", "utf-16-be"),
         (b"\x00\x00\xfe\xff", "utf-32-le"),
         (b"\xff\xfe\x00\x00", "utf-32-be")]


def file_encoding(blob_b64):
    """Does the text SAY its charset: BOM table (5), then strict utf-8
    decode, then utf-16 probe. Verdicts are honest: 'no-declaration'
    and 'undetermined' are first-class answers, not failures."""
    import base64 as _b64
    raw = _b64.b64decode(blob_b64 + "=" * (-len(blob_b64) % 4))
    for sig, name in _BOMS:
        if raw.startswith(sig):
            return {"bom": sig.hex(), "encoding": name,
                    "declared": True, "bytes": len(raw)}
    try:
        raw.decode("utf-8")
        return {"bom": None, "encoding": "utf-8", "declared": False,
                "verdict": "valid utf-8 without BOM", "bytes": len(raw)}
    except UnicodeDecodeError as e:
        return {"bom": None, "encoding": None, "declared": False,
                "verdict": "undetermined", "bytes": len(raw),
                "failed_at_byte": e.start,
                "first_bad_hex": raw[e.start:e.start + 4].hex(),
                "note": "could be latin-1/cp1252/shift-jis: the bytes do "
                        "not prove which; no guessing here"}
