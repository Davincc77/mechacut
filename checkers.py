"""Deterministic validators (Bundle 6, TOOLS-50 #37-41).

Closed country tables owned here; no network, no external lists.
Semantics mirror /validate: a payload that fails the CHECK answers 400
kind=check_failed with precise errors + valid:false — the value is never
"200, sorry it's wrong".
"""

import re


class CheckError(Exception):
    pass


# ------------------------------------------------------------------- IBAN

# cc -> (total length, bban regex applied on the full normalized string)
_IBAN = {
    "AL": (28, r"AL\d{2}\d{8}[A-Z0-9]{16}"),
    "AD": (24, r"AD\d{2}\d{4}\d{4}[A-Z0-9]{12}"),
    "AT": (20, r"AT\d{2}\d{5}\d{11}"),
    "AZ": (28, r"AZ\d{2}[A-Z]{4}[A-Z0-9]{20}"),
    "BE": (16, r"BE\d{2}\d{3}\d{7}\d{2}"),
    "BH": (22, r"BH\d{2}[A-Z]{4}[A-Z0-9]{14}"),
    "BR": (29, r"BR\d{2}\d{8}\d{5}\d{10}[A-Z][A-Z0-9]"),
    "BG": (22, r"BG\d{2}[A-Z]{4}\d{6}[A-Z0-9]{8}"),
    "CR": (22, r"CR\d{2}\d{18}"),
    "HR": (21, r"HR\d{2}\d{7}\d{10}"),
    "CY": (28, r"CY\d{2}\d{3}\d{5}[A-Z0-9]{16}"),
    "CZ": (24, r"CZ\d{2}\d{20}"),
    "DK": (18, r"DK\d{2}\d{14}"),
    "DO": (28, r"DO\d{2}[A-Z0-9]{4}\d{20}"),
    "EG": (29, r"EG\d{2}\d{4}\d{4}\d{17}"),
    "EE": (20, r"EE\d{2}\d{2}\d{2}\d{11}\d{1}"),
    "FI": (18, r"FI\d{2}\d{14}"),
    "FR": (27, r"FR\d{2}\d{10}[A-Z0-9]{11}\d{2}"),
    "DE": (22, r"DE\d{2}\d{18}"),
    "GR": (27, r"GR\d{2}\d{3}\d{4}[A-Z0-9]{16}"),
    "HU": (28, r"HU\d{2}\d{3}\d{4}\d{6}\d{1}\d{10}"),
    "IS": (26, r"IS\d{2}\d{22}"),
    "IE": (22, r"IE\d{2}[A-Z]{4}\d{14}"),
    "IL": (23, r"IL\d{2}\d{3}\d{3}\d{13}"),
    "IT": (27, r"IT\d{2}[A-Z]\d{10}\d{12}"),
    "JO": (30, r"JO\d{2}[A-Z]{4}\d{4}[A-Z0-9]{18}"),
    "KZ": (20, r"KZ\d{2}\d{3}[A-Z0-9]{13}"),
    "KW": (30, r"KW\d{2}[A-Z]{4}[A-Z0-9]{22}"),
    "LV": (21, r"LV\d{2}[A-Z]{4}[A-Z0-9]{13}"),
    "LB": (28, r"LB\d{2}\d{4}[A-Z0-9]{20}"),
    "LI": (21, r"LI\d{2}[A-Z0-9]{5}\d{12}"),
    "LT": (20, r"LT\d{2}\d{5}\d{11}"),
    "LU": (20, r"LU\d{2}\d{3}\d{13}"),
    "MT": (31, r"MT\d{2}[A-Z]{4}\d{5}[A-Z0-9]{18}"),
    "MR": (27, r"MR\d{2}\d{23}"),
    "MC": (27, r"MC\d{2}\d{10}[A-Z0-9]{11}\d{2}"),
    "MD": (24, r"MD\d{2}[A-Z0-9]{20}"),
    "ME": (22, r"ME\d{2}\d{3}\d{13}\d{2}"),
    "NL": (18, r"NL\d{2}[A-Z]{4}\d{10}"),
    "MK": (19, r"MK\d{2}\d{3}[A-Z0-9]{10}\d{2}"),
    "NO": (15, r"NO\d{2}\d{11}"),
    "PK": (24, r"PK\d{2}[A-Z]{4}[A-Z0-9]{16}"),
    "PS": (29, r"PS\d{2}[A-Z]{4}[A-Z0-9]{21}"),
    "PL": (28, r"PL\d{2}\d{8}\d{16}"),
    "PT": (25, r"PT\d{2}\d{4}\d{4}\d{11}\d{2}"),
    "QA": (29, r"QA\d{2}[A-Z]{4}[A-Z0-9]{21}"),
    "RO": (24, r"RO\d{2}[A-Z]{4}[A-Z0-9]{16}"),
    "SM": (27, r"SM\d{2}[A-Z]\d{10}[A-Z0-9]{12}"),
    "SA": (24, r"SA\d{2}\d{2}[A-Z0-9]{18}"),
    "RS": (22, r"RS\d{2}\d{3}\d{13}\d{2}"),
    "SK": (24, r"SK\d{2}\d{4}\d{6}\d{10}"),
    "SI": (19, r"SI\d{2}\d{5}\d{8}\d{2}"),
    "ES": (24, r"ES\d{2}\d{4}\d{4}\d{1}\d{1}\d{10}"),
    "SE": (24, r"SE\d{2}\d{20}"),
    "CH": (21, r"CH\d{2}\d{5}[A-Z0-9]{12}"),
    "TR": (26, r"TR\d{2}\d{5}[A-Z0-9]{17}"),
    "UA": (29, r"UA\d{2}\d{6}[A-Z0-9]{19}"),
    "AE": (23, r"AE\d{2}\d{3}\d{16}"),
    "GB": (22, r"GB\d{2}[A-Z]{4}\d{14}"),
    "VA": (22, r"VA\d{2}\d{18}"),
    "XK": (20, r"XK\d{2}\d{4}\d{10}\d{2}"),
}


def _mod97(s):
    moved = s[4:] + s[:4]
    total = 0
    for ch in moved:
        if ch.isdigit():
            total = total * 10 + int(ch)
        elif "A" <= ch <= "Z":
            total = total * 100 + (ord(ch) - 55)
        else:
            return -1
    return total % 97


def check_iban(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise CheckError("iban must be a non-empty string")
    s = re.sub(r"\s+", "", raw).upper()
    errors = []
    country = s[:2]
    if not re.match(r"^[A-Z]{2}$", country):
        raise CheckError("iban must start with a two-letter country code")
    if country not in _IBAN:
        raise CheckError("unknown country %r (closed table of %d countries)"
                         % (country, len(_IBAN)))
    length, pattern = _IBAN[country]
    if len(s) != length:
        errors.append("length is %d, expected %d for %s" % (len(s), length,
                                                            country))
    if not re.match("^" + pattern + "$", s):
        errors.append("structure does not match the %s BBAN pattern" % country)
    m = _mod97(s)
    valid = m == 1 and not errors
    if m != 1 and not errors:
        errors.append("mod-97 checksum is %d, expected 1" % m)
    if not valid:
        raise CheckError("; ".join(errors))
    return {"valid": True, "country": country, "length": length,
            "checksum": s[2:4], "bban": s[4:], "iban": s}


# ------------------------------------------------------------- phone/E164

# cc -> (dial code, (min national digits, max national digits))
_DIAL = {
    "FR": ("33", (9, 9)), "BE": ("32", (8, 9)), "CH": ("41", (9, 9)),
    "LU": ("352", (9, 9)), "DE": ("49", (6, 11)), "GB": ("44", (9, 10)),
    "IE": ("353", (7, 9)), "IT": ("39", (6, 11)), "ES": ("34", (9, 9)),
    "PT": ("351", (9, 9)), "NL": ("31", (9, 9)), "AT": ("43", (4, 13)),
    "PL": ("48", (9, 9)), "CZ": ("420", (8, 9)), "SK": ("421", (9, 9)),
    "HU": ("36", (6, 9)), "RO": ("40", (9, 9)), "BG": ("359", (9, 9)),
    "GR": ("30", (10, 10)), "SE": ("46", (6, 9)), "NO": ("47", (8, 8)),
    "DK": ("45", (8, 8)), "FI": ("358", (5, 12)), "EE": ("372", (7, 8)),
    "LV": ("371", (8, 8)), "LT": ("370", (8, 8)), "HR": ("385", (8, 9)),
    "SI": ("386", (8, 8)), "RS": ("381", (6, 12)), "UA": ("380", (9, 9)),
    "RU": ("7", (10, 10)), "TR": ("90", (10, 10)), "US": ("1", (10, 10)),
    "CA": ("1", (10, 10)), "MX": ("52", (10, 10)), "BR": ("55", (10, 11)),
    "AR": ("54", (6, 12)), "CL": ("56", (8, 9)), "CO": ("57", (9, 10)),
    "MA": ("212", (9, 9)), "DZ": ("213", (8, 9)), "TN": ("216", (8, 8)),
    "EG": ("20", (9, 10)), "AE": ("971", (8, 9)), "SA": ("966", (9, 9)),
    "QA": ("974", (8, 8)), "KW": ("965", (8, 8)), "IL": ("972", (9, 9)),
    "SN": ("221", (9, 9)), "CI": ("225", (8, 10)), "ML": ("223", (8, 8)),
    "BF": ("226", (8, 8)), "NG": ("234", (10, 11)), "KE": ("254", (9, 9)),
    "ZA": ("27", (9, 9)), "JP": ("81", (10, 10)), "CN": ("86", (11, 11)),
    "IN": ("91", (10, 10)), "KR": ("82", (9, 11)), "SG": ("65", (8, 9)),
    "HK": ("852", (8, 8)), "AU": ("61", (9, 10)), "NZ": ("64", (8, 10)),
}
_BY_CODE = sorted((c[0], k) for k, c in _DIAL.items())  # dial -> cc


def check_phone(raw, default_country=None):
    if not isinstance(raw, str) or not raw.strip():
        raise CheckError("phone must be a non-empty string")
    s = re.sub(r"[\s()./\-]", "", raw)
    if s.startswith("00"):
        s = "+" + s[2:]
    cc_hint = None
    if not s.startswith("+"):
        if not default_country:
            raise CheckError("phone has no country code; pass "
                             'default_country (e.g. "FR")')
        cc_hint = default_country.upper()
        if cc_hint not in _DIAL:
            raise CheckError("unknown default_country %r (closed table)"
                             % cc_hint)
        dial = _DIAL[cc_hint][0]
        if s.startswith("0"):
            s = s.lstrip("0")
        s = "+" + dial + s
    digits = s[1:]
    if not digits.isdigit() or len(digits) < 2:
        raise CheckError("not a phone number: %r" % raw)
    # longest-prefix dial code match
    cc = None
    national = ""
    for dial, country in sorted(_BY_CODE, key=lambda x: -len(x[0])):
        if digits.startswith(dial):
            cc = country
            national = digits[len(dial):]
            break
    if cc is None:
        raise CheckError("dial code not in closed table: +%s" % digits)
    lo, hi = _DIAL[cc][1]
    if not (lo <= len(national) <= hi):
        raise CheckError("national number has %d digits, expected %d-%d "
                         "for %s" % (len(national), lo, hi, cc))
    return {"valid": True, "e164": "+" + digits, "country": cc,
            "dial_code": _DIAL[cc][0], "national": national}


# ------------------------------------------------------------------ email

_EMAIL_ATOM = re.compile(r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+$")


def check_email(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise CheckError("email must be a non-empty string")
    s = raw.strip()
    if s.count("@") != 1:
        raise CheckError("exactly one @ required")
    local, _, domain = s.partition("@")
    errors = []
    if not local or len(local) > 64:
        errors.append("local-part must be 1-64 bytes")
    if local.startswith(".") or local.endswith(".") or ".." in local:
        errors.append("local-part dot rules violated")
    if not _EMAIL_ATOM.match(local) and not (local.startswith('"')
                                             and local.endswith('"')):
        errors.append("local-part has characters outside the closed atom set")
    if len(s) > 254:
        errors.append("total length over 254")
    if not re.match(r"^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
                    r"(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*"
                    r"\.[A-Za-z]{2,63}$", domain):
        errors.append("domain is not a valid ascii/punycode hostname with "
                      "an alphabetic TLD")
    if errors:
        raise CheckError("; ".join(errors))
    return {"valid": True, "local": local, "domain": domain.lower(),
            "normalized": "%s@%s" % (local, domain.lower())}


# -------------------------------------------------------------------- url

def check_url(raw):
    from urllib.parse import urlsplit, urlunsplit, unquote
    if not isinstance(raw, str) or not raw.strip():
        raise CheckError("url must be a non-empty string")
    s = raw.strip()
    parts = urlsplit(s)
    if not parts.scheme:
        raise CheckError("absolute url with scheme required")
    if parts.scheme not in ("http", "https", "ftp"):
        raise CheckError("scheme %r outside closed set http|https|ftp"
                         % parts.scheme)
    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        raise CheckError("no host")
    try:
        host_puny = (host.encode("idna").decode("ascii")
                     if any(ord(ch) > 127 for ch in host) else host)
    except UnicodeError:
        raise CheckError("invalid host: %r" % parts.netloc)
    try:
        port = parts.port
    except ValueError:
        raise CheckError("port out of range 0-65535")
    default = (parts.scheme == "http" and port == 80) or \
              (parts.scheme == "https" and port == 443) or \
              (parts.scheme == "ftp" and port == 21)
    netloc = host_puny
    if port is not None and not default:
        netloc = "%s:%d" % (host_puny, port)
    if parts.username:
        userinfo = parts.username
        if parts.password:
            userinfo += ":***"
        netloc = "%s@%s" % (userinfo, netloc)
    path = parts.path or "/"
    path = posix_normpath(path)
    canonical = urlunsplit((parts.scheme.lower(), netloc, path,
                            parts.query, parts.fragment))
    return {"valid": True, "canonical": canonical,
            "scheme": parts.scheme.lower(), "host": host_puny,
            "port": None if default else port,
            "path": path, "query": parts.query,
            "fragment": parts.fragment, "secure":
            parts.scheme.lower() == "https"}


def posix_normpath(path):
    """Pure-lexical POSIX path normalization for URL paths."""
    lead = "/" if path.startswith("/") else ""
    parts = []
    for seg in path.split("/"):
        if seg == "" or seg == ".":
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    out = lead + "/".join(parts)
    if path.endswith("/") and not out.endswith("/") and out != lead:
        out += "/"
    return out or lead or "/"


# ------------------------------------------------------------------ color

_HEX3 = re.compile(r"^#?([0-9a-fA-F]){3}$")
_HEX6 = re.compile(r"^#?([0-9a-fA-F]{6})$")
_RGB = re.compile(r"^rgba?\((\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})"
                  r"(?:\s*,\s*[\d.]+)?\)$")


class ColorError(CheckError):
    pass


def _parse_color(value):
    v = str(value).strip()
    m = _HEX6.match(v)
    if m:
        h = m.group(1).lower()
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = _HEX3.match(v)
    if m and len(v.lstrip("#")) == 3:
        h = v.lstrip("#").lower()
        return tuple(int(c * 2, 16) for c in h)
    m = _RGB.match(v)
    if m:
        rgb = tuple(int(g) for g in m.groups())
        if any(c > 255 for c in rgb):
            raise ColorError("rgb components must be 0-255: %r" % value)
        return rgb
    raise ColorError("unparsable color: %r (closed: #rgb, #rrggbb, "
                     "rgb(r,g,b))" % value)


def _channel_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lum(rgb):
    r, g, b = rgb
    return (0.2126 * _channel_lin(r) + 0.7152 * _channel_lin(g)
            + 0.0722 * _channel_lin(b))


def color_check(value, against=None):
    rgb = _parse_color(value)
    h, s, l = _rgb_to_hsl(rgb)
    out = {"hex": "#%02x%02x%02x" % rgb, "rgb": list(rgb),
           "hsl": [round(h * 360, 2), round(s * 100, 2),
                   round(l * 100, 2)],
           "luminance": round(_lum(rgb), 6)}
    if against is not None:
        c2 = _parse_color(against)
        l1, l2 = _lum(rgb), _lum(c2)
        hi, lo = max(l1, l2), min(l1, l2)
        ratio = round((hi + 0.05) / (lo + 0.05), 3)
        out["contrast"] = {"against": "#%02x%02x%02x" % c2, "ratio": ratio,
                           "AA_normal": ratio >= 4.5,
                           "AA_large": ratio >= 3.0,
                           "AAA_normal": ratio >= 7.0,
                           "AAA_large": ratio >= 4.5}
    return out


def iban_table_widths():
    """Audit each closed-table entry. Every pattern is: literal cc (2
    chars) + atoms that each carry either a {n} quantifier or are a bare
    single-char class. So width = 2 + sum(quantifiers) + bare classes."""
    out = {}
    for cc, (length, pattern) in _IBAN.items():
        width = 2
        for n in re.findall(r"\{(\d+)\}", pattern):
            width += int(n)
        width += len(re.findall(r"\[[^\]]+\](?!\{)", pattern))
        out[cc] = (length, width)
    return out


# ---------------------------------------------------------------- palette

SCHEMES = ("complementary", "analogous", "triad", "tetradic", "split")

def _rgb_to_hsl(rgb):
    r, g, b = [c / 255.0 for c in rgb]
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2.0
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    sl = d / (2.0 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = ((g - b) / d + (6 if g < b else 0)) / 6
    elif mx == g:
        h = ((b - r) / d + 2) / 6
    else:
        h = ((r - g) / d + 4) / 6
    return h, sl, l

def _hsl_to_rgb(h, sl, l):
    if sl == 0:
        v = round(l * 255)
        return (v, v, v)
    q = l * (1 + sl) if l < 0.5 else l + sl - l * sl
    p = 2 * l - q
    def f(t):
        t = t % 1.0
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p
    return tuple(round(f(h + off) * 255) for off in (1 / 3, 0, -1 / 3))

def _rot(h, deg):
    return (h + deg / 360.0) % 1.0

def color_palette(color, scheme="complementary", steps=5, neutral=False):
    base = _parse_color(color)
    if scheme not in SCHEMES:
        raise CheckError("unknown scheme %r (closed: %s)"
                         % (scheme, ", ".join(SCHEMES)))
    if not isinstance(steps, int) or isinstance(steps, bool) \
            or not 2 <= steps <= 21:
        raise CheckError("steps must be 2..21")
    h, sl, l = _rgb_to_hsl(base)
    angles = {"complementary": [0, 180], "analogous": [-30, 0, 30],
              "triad": [0, 120, 240], "tetradic": [0, 90, 180, 270],
              "split": [0, 150, 210]}[scheme]
    def hx(hh, ss, ll):
        return "#%02x%02x%02x" % _hsl_to_rgb(hh % 1.0, ss, ll)
    swatches = [hx(_rot(h, a), sl, l) for a in angles]
    shades = []
    if steps:
        for i in range(steps):
            ll = i / (steps - 1) * 0.9 + 0.05
            shades.append(hx(h, sl, ll))
    out = {"base": "#%02x%02x%02x" % base, "scheme": scheme,
           "swatches": swatches, "shades": shades}
    if neutral:
        n = []
        for i in range(steps):
            ll = i / (steps - 1) * 0.9 + 0.05
            n.append(hx(0.0, 0.0, ll))
        out["neutral_ramp"] = n
    return out


# ---- bundle 123: stats_rate_ci — Wilson 95 % for k of n -------------------
# Born from the LATAM census (wave 3): 720/1105 was computed by hand three
# times before it became a door tool. z = 1,96 is the committee constant of
# the 95 % level, named here, never inherited from a silent default.

from decimal import Decimal as _D, ROUND_HALF_EVEN as _RHE

_WILSON_Z = _D("1.96")


def wilson_ci(k, n):
    """Exact Decimal Wilson score interval, reported to 0,1 % half-even.

    Caps raw bounds into [0, 1] BEFORE rounding (the census lesson: a
    cap applied after rounding invents 0,1 points). Returns the OBSERVED
    rate and the WILSON CENTER as two named fields — the conflation of
    the two is the disease this tool kills."""
    if not isinstance(k, int) or not isinstance(n, int):
        raise CheckError("k and n must be integers: k counts successes, n counts trials")
    if n < 1:
        raise CheckError("n must be at least 1: an interval needs at least one trial")
    if k < 0:
        raise CheckError("k must be 0 or more: a count of successes cannot be negative")
    if k > n:
        raise CheckError("k must not exceed n: cannot observe more successes than trials")
    z = _WILSON_Z
    z2 = z * z
    N = _D(n)
    p = _D(k) / N
    denom = 1 + z2 / N
    center = (p + z2 / (2 * N)) / denom
    inner = p * (1 - p) / N + z2 / (4 * N * N)
    half = z * inner.sqrt() / denom
    lo = center - half
    hi = center + half
    if lo < 0:
        lo = _D(0)
    if hi > 1:
        hi = _D(1)

    def pct(x):
        return str((x * 100).quantize(_D("0.1"), rounding=_RHE))

    return {"k": k, "n": n, "observed_pct": pct(p),
            "wilson_center_pct": pct(center),
            "lower_pct": pct(lo), "upper_pct": pct(hi),
            "method": "wilson", "confidence_pct": "95.0", "z": str(z)}
