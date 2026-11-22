"""certkit — X.509 certificate lint from PEM text, pure stdlib,
deterministic.

Honest scope:
  * We PARSE: subject/issuer names, serial, validity window, signature
    algorithm (with deprecation flags), SANs, basic constraints, EKUs.
  * We do NOT verify cryptographic signatures — no issuer's public key
    check, no revocation. The response says exactly that. Chain output
    is SHAPE (subject == next issuer), not trust.
  * Time is an ARGUMENT: as_of (ISO date/datetime) fixes the verdict so
    the same bytes replay forever; without it the verdict is "as of now
    (UTC)" and the chosen instant is echoed in the response.
"""
import base64
import binascii
import re
from datetime import datetime, timezone

PEM_RE = re.compile(
    r"-----BEGIN CERTIFICATE-----(.+?)-----END CERTIFICATE-----", re.S)


class CertError(Exception):
    pass


# ── minimal DER ───────────────────────────────────────────────────────

def _tlv(buf, pos):
    if pos >= len(buf):
        raise CertError("DER truncated")
    tag = buf[pos]
    pos += 1
    ln = buf[pos]
    pos += 1
    if ln & 0x80:
        n = ln & 0x7F
        if n == 0 or n > 4:
            raise CertError("bad DER length form")
        ln = int.from_bytes(buf[pos:pos + n], "big")
        pos += n
    if pos + ln > len(buf):
        raise CertError("DER truncated inside value")
    return tag, buf[pos:pos + ln], pos + ln


def _children(data):
    out, pos = [], 0
    while pos < len(data):
        tag, val, pos = _tlv(data, pos)
        out.append((tag, val))
    return out


def _oid(bytes_val):
    parts = [str(bytes_val[0] // 40), str(bytes_val[0] % 40)]
    v = 0
    for b in bytes_val[1:]:
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            parts.append(str(v))
            v = 0
    return ".".join(parts)


ATTR_NAMES = {
    "2.5.4.3": "CN", "2.5.4.6": "C", "2.5.4.7": "L", "2.5.4.8": "ST",
    "2.5.4.10": "O", "2.5.4.11": "OU", "2.5.4.5": "serialNumber",
    "0.9.2342.19200300.100.1.25": "DC", "1.2.840.113549.1.9.1": "E",
}
SIG_ALGS = {
    "1.2.840.113549.1.1.11": ("sha256WithRSA", False),
    "1.2.840.113549.1.1.12": ("sha384WithRSA", False),
    "1.2.840.113549.1.1.13": ("sha512WithRSA", False),
    "1.2.840.113549.1.1.5": ("sha1WithRSA", True),
    "1.2.840.113549.1.1.4": ("md5WithRSA", True),
    "1.2.840.10045.4.3.2": ("ecdsa-with-SHA256", False),
    "1.2.840.10045.4.3.3": ("ecdsa-with-SHA384", False),
    "1.2.840.10045.4.3.4": ("ecdsa-with-SHA512", False),
    "1.3.101.112": ("Ed25519", False),
}
EXT_NAMES = {
    "2.5.29.17": "subjectAltName", "2.5.29.19": "basicConstraints",
    "2.5.29.15": "keyUsage", "2.5.29.37": "extendedKeyUsage",
    "2.5.29.14": "subjectKeyIdentifier",
    "2.5.29.35": "authorityKeyIdentifier",
    "2.5.29.31": "cRLDistributionPoints", "1.3.6.1.5.5.7.1.1": "AIA",
    "2.23.140.1.2.1": "organizationValidation? (dv)",
}
EKU = {"1.3.6.1.5.5.7.3.1": "serverAuth",
       "1.3.6.1.5.5.7.3.2": "clientAuth",
       "1.3.6.1.5.5.7.3.3": "codeSigning",
       "1.3.6.1.5.5.7.3.4": "emailProtection",
       "1.3.6.1.5.5.7.3.9": "ocspSigning"}


def _parse_name(data):
    """RDNSequence -> RFC4514-ish string and ordered list."""
    rdns = []
    for tag, rdn in _children(data):        # SETs
        parts = []
        for _, atv in _children(rdn):
            kids = _children(atv)
            oid = _oid(kids[0][1])
            val = kids[1][1].decode("utf-8", "replace")
            parts.append((ATTR_NAMES.get(oid, oid), val))
        rdns.append(parts)
    flat = [kv for r in rdns for kv in r]
    s = ", ".join("%s=%s" % kv for kv in flat)
    return s, [{"k": k, "v": v} for k, v in flat]


def _parse_time(tag, data):
    st = data.decode("ascii")
    if tag == 0x17:                          # UTCTime YYMMDDHHMM[SS]Z
        yy = int(st[0:2])
        yyyy = 2000 + yy if yy < 50 else 1900 + yy
        rest = st[2:]
    elif tag == 0x18:                        # GeneralizedTime YYYY...
        yyyy, rest = int(st[0:4]), st[4:]
    else:
        raise CertError("time tag %r unexpected" % tag)
    mo, d, hh, mm = int(rest[0:2]), int(rest[2:4]), int(rest[4:6]), \
        int(rest[6:8])
    ss = int(rest[8:10]) if len(rest) >= 10 else 0
    dt = datetime(yyyy, mo, d, hh, mm, ss, tzinfo=timezone.utc)
    if "Z" not in st and re.search(r"[-+]\d{4}$", st):
        off = st[-5:]
        sign = 1 if off[0] == "+" else -1
        oh, om = int(off[1:3]), int(off[3:5])
        from datetime import timedelta
        dt = dt - sign * timedelta(hours=oh, minutes=om)
    return dt


def parse_cert(der):
    tag, cert, end = _tlv(der, 0)
    if tag != 0x30:
        raise CertError("certificate is not a SEQUENCE")
    _ck = _children(cert)
    tbs, alg_id = _ck[0][1], _ck[1][1]
    kids = _children(tbs)
    pos = 0
    version = 1
    if kids[pos][0] == 0xA0:                 # [0] explicit
        _t, inner, _p = _tlv(kids[pos][1], 0)
        version = int.from_bytes(inner, "big") + 1
        pos += 1
    serial = int.from_bytes(kids[pos][1], "big")
    serial_hex = ("%x" % serial)
    if len(serial_hex) % 2:
        serial_hex = "0" + serial_hex
    pos += 1
    pos += 1                                  # signature alg inside TBS
    issuer, issuer_rdns = _parse_name(kids[pos][1])
    pos += 1
    vt = _children(kids[pos][1])
    nb = _parse_time(vt[0][0], vt[0][1])
    na = _parse_time(vt[1][0], vt[1][1])
    pos += 1
    subject, subject_rdns = _parse_name(kids[pos][1])
    pos += 1
    pos += 1                                  # SPKI (v2/v3 unique IDs
    #  are legacy relics; the while-loop below skips anything non-A3
    #  anyway, so miscounting here is impossible now)
    san = {"dns": [], "email": [], "ip": [], "uri": []}
    basic = None
    ekus = []
    crit_unknown = []
    exts_present = []
    while pos < len(kids):
        if kids[pos][0] != 0xA3:
            pos += 1
            continue
        for _, exts_content in _children(kids[pos][1]):
            for _, ext_val in _children(exts_content):
                fields = _children(ext_val)
                oid = _oid(fields[0][1])
                rest = fields[1:]
                critical = False
                if (rest and rest[0][0] == 0x01
                        and rest[0][1] == b"\xff"):
                    critical = True
                    rest = rest[1:]
                value = rest[0][1] if rest else b""
                exts_present.append({"oid": oid, "critical": critical,
                                     "known": oid in EXT_NAMES})
                if oid == "2.5.29.17":
                    # value = DER of GeneralNames SEQUENCE — descend
                    outer = _children(value)
                    names = _children(outer[0][1]) if outer else []
                    for t, v in names:
                        if t == 0x82:
                            san["dns"].append(v.decode("ascii"))
                        elif t == 0x81:
                            san["email"].append(v.decode("ascii"))
                        elif t == 0x86:
                            san["uri"].append(v.decode("ascii"))
                        elif t == 0x87 and len(v) in (4, 16):
                            if len(v) == 4:
                                san["ip"].append(".".join(
                                    str(bb) for bb in v))
                            else:
                                san["ip"].append(":".join(
                                    v[i:i + 2].hex()
                                    for i in range(0, 16, 2)))
                elif oid == "2.5.29.19":
                    # value = DER of SEQUENCE { cA BOOLEAN DEFAULT
                    # FALSE } — descend both levels
                    outer = _children(value)
                    inner = _children(outer[0][1]) if outer else []
                    basic = bool(inner and inner[0][0] == 0x01
                                 and inner[0][1] == b"\xff")
                elif oid == "2.5.29.37":
                    for t, v in _children(value):
                        ekus.append(EKU.get(_oid(v), _oid(v)))
                elif critical and oid not in EXT_NAMES:
                    crit_unknown.append(oid)
        pos += 1
    alg_oid = _oid(_children(alg_id)[0][1])
    alg_name, deprecated = SIG_ALGS.get(
        alg_oid, ("oid:" + alg_oid,
                  alg_oid in ("1.2.840.113549.1.1.5",
                              "1.2.840.113549.1.1.4")))
    return {"version": version, "serial_hex": serial_hex,
            "issuer": issuer, "subject": subject,
            "not_before": nb, "not_after": na,
            "sig_alg": alg_name, "sig_deprecated": deprecated,
            "san": san, "ca": basic, "eku": ekus,
            "critical_unknown": crit_unknown, "extensions": exts_present}


def _as_of(arg):
    if not arg:
        return datetime.now(timezone.utc)
    st = str(arg).strip()
    try:
        if re.match(r"^\d{4}-\d{2}-\d{2}$", st):
            return datetime.fromisoformat(st + "T00:00:00+00:00")
        if st.endswith("Z"):
            st = st[:-1] + "+00:00"
        dt = datetime.fromisoformat(st)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        raise CertError("as_of must be YYYY-MM-DD or ISO-8601")


def lint(pem_text, as_of=None):
    """-> dict with one entry per PEM block + chain shape."""
    blocks = PEM_RE.findall(pem_text or "")
    if not blocks:
        raise CertError("no PEM certificate block found — paste the text "
                        "between -----BEGIN CERTIFICATE----- markers")
    now = _as_of(as_of)
    certs = []
    for i, b in enumerate(blocks):
        try:
            der = base64.b64decode(re.sub(r"\s+", "", b), validate=True)
        except (binascii.Error, ValueError):
            raise CertError("block %d: not valid base64 inside the PEM "
                            "markers" % (i + 1))
        try:
            c = parse_cert(der)
        except CertError:
            raise
        except Exception as e:
            raise CertError("block %d: DER parse failed (%s) — file is "
                            "corrupt or uses an unsupported structure"
                            % (i + 1, type(e).__name__))
        nb, na = c["not_before"], c["not_after"]
        days = int((na - now).total_seconds() // 86400)
        if now < nb:
            status = "not_yet_valid"
        elif now > na:
            status = "expired"
        else:
            status = "valid"
        import hashlib
        entry = {
            "index": i,
            "subject": c["subject"], "issuer": c["issuer"],
            "serial_hex": c["serial_hex"],
            "not_before": nb.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "not_after": na.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": status, "days_to_expiry": days,
            "version": c["version"], "sig_alg": c["sig_alg"],
            "sig_deprecated": c["sig_deprecated"],
            "ca": c["ca"], "eku": c["eku"],
            "san": {k: v for k, v in c["san"].items() if v},
            "sha256_fingerprint": hashlib.sha256(der).hexdigest(),
            "self_signed": c["subject"] == c["issuer"],
            "critical_unknown_oids": c["critical_unknown"],
            "warnings": [],
        }
        if c["sig_deprecated"]:
            entry["warnings"].append(
                "signature algorithm %s is deprecated" % c["sig_alg"])
        if status == "valid" and days < 14:
            entry["warnings"].append(
                "expires within 14 days")
        if not c["san"]["dns"] and c["ca"] is False:
            entry["warnings"].append(
                "leaf without subjectAltName.dns — browsers refuse these")
        if c["version"] < 3:
            entry["warnings"].append(
                "X.509 v%d predates SAN — legacy only" % c["version"])
        if c["ca"]:
            entry["warnings"].append(
                "this is a CA certificate (basicConstraints ca=true)")
        certs.append(entry)
    chain = None
    if len(certs) > 1:
        links = []
        for child, parent in zip(certs, certs[1:]):
            links.append({"child_issuer": child["issuer"],
                          "parent_subject": parent["subject"],
                          "shape_matches":
                              child["issuer"] == parent["subject"]})
        chain = {"order": "leaf-first expected", "links": links,
                 "all_shapes_match": all(l["shape_matches"]
                                         for l in links)}
    out = {"certificates": certs, "count": len(certs),
           "evaluated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "as_of_was_supplied": bool(as_of),
           "scope_note": "parsed, NOT signature-verified; chain output "
                         "is name-shape only, not trust"}
    if chain:
        out["chain"] = chain
    return out
