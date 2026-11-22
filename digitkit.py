"""The check-digit family: the identifiers a small model gets wrong
CONFIDENTLY (veridigit bench, Nov 2025: a frontier model, tool-free,
missed the check digit 91 % of the time on non-memorised identifiers).

15 schemes, each cited to its published spec — no table here is written
from memory:
  isbn10   ISO 2108: weights 10..1, sum mod 11, 'X' = 10
  isbn13   ISO 2108 (Bookland 978/979) + GS1 mod-10
  ean8     GS1 GTIN-8  — mod-10, weights 3,1,3,... right-to-left of the
           payload ("Module 10 check digit calculation", GS1 General
           Specifications)
  ean13    GS1 GTIN-13 — same weights
  upca     GS1 GTIN-12 (UPC-A) — same weights
  gtin14   GS1 GTIN-14 (indicator digit) — same weights over 13 payload
           digits
  issn     ISO 3297: weights 8..2, sum mod 11, 'X' = 10
  isin     ISO 6166: expand letters A=10..Z=35 in the 11-char payload,
           then Luhn (ISO/IEC 7812) over the digits
  cusip    ANSI X9.6: alphabet 0-9 A-Z * @ # (values 0..38), double the
           even positions (digits of the product summed), mod-10
           complement
  sedol    LRO / London Stock Exchange: 6 chars of digits and
           consonants (the vowels are never issued), weights 1,3,1,7,3,9,
           mod-10 complement
  aba      US Federal Reserve routing (ABA/ABA number): 9 digits,
           weights 3,7,1,3,7,1,3,7,1, sum divisible by 10
  lei      ISO 17442: 18-char entity ID + two check digits, ISO 7064
           MOD 97-10 (valid iff letter-expanded value mod 97 == 1)
  orcid    ISO 27729: ISO 7064 MOD 11-2 over the first 15 digits,
           'X' = 10
  cas      CAS Registry Number: sum(digit x position-from-right of the
           body) mod 10 = last digit; the hyphenated form is required
  verhoeff Verhoeff 1969 (dihedral group D5). Tables d, p, inv are the
           published ones: en.wikipedia.org/wiki/Verhoeff_algorithm
  damm     Damm 2004 (totally anti-symmetric quasigroup, dissertation
           Philipps-Universitaet Marburg). The table is the published
           one: en.wikipedia.org/wiki/Damm_algorithm

Closed design decisions, said out loud (this is the product):
- check with no scheme returns EVERY scheme whose format matches, each
  with its own verdict. A valid Bookland number is both ean13 and
  isbn13; we report the ambiguity, we never guess.
- The generic variable-length schemes (verhoeff, damm) require an
  explicit scheme= argument: any digit string passes their check ~10 %
  of the time, and reporting that as detection would be exactly the
  confident wrong answer we exist to kill.
- CAS matches only the canonical hyphenated form: bare digit strings
  are indistinguishable from other 7-10 digit identifiers.
- ISBN hyphenation is NOT attempted: it needs the registration-group
  range tables, and getting them from memory is how wrong books get
  shelved. issn/orcid/cas have algorithmic hyphenation, we render it.
"""

import re

MODES = ("check", "generate", "repair", "scan")
SCANNABLE_MAX = 20000      # chars of text scan accepts (bounded CPU, 🟢)
REPAIR_CAP = 25            # candidates returned per repair call


class DigitError(ValueError):
    pass


# ------------------------------------------------------------- tables
# Verhoeff: multiplication d in D5, inverse inv, permutation p (mod 8).
# Transcribed verbatim from the published tables (see module docstring).
_D = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)
_INV = (0, 4, 3, 2, 1, 5, 6, 7, 8, 9)
_P = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
)
# Damm: the quasigroup table from the published article (row = interim,
# column = processed digit); main diagonal is all zeros.
_DAMM = (
    (0, 3, 1, 7, 5, 9, 8, 6, 4, 2),
    (7, 0, 9, 2, 1, 5, 4, 8, 6, 3),
    (4, 2, 0, 6, 8, 7, 1, 3, 5, 9),
    (1, 7, 5, 0, 9, 8, 3, 4, 2, 6),
    (6, 1, 2, 3, 0, 4, 5, 9, 7, 8),
    (3, 6, 7, 4, 2, 0, 9, 5, 8, 1),
    (5, 8, 6, 9, 7, 2, 0, 1, 3, 4),
    (8, 9, 4, 5, 3, 6, 2, 0, 1, 7),
    (9, 4, 3, 8, 6, 1, 7, 2, 0, 5),
    (2, 5, 8, 1, 4, 3, 6, 7, 9, 0),
)

# ------------------------------------------------------- shared engines
def _mod10(payload, from_right_weight3=True):
    """GS1 module 10: weights 3,1,3,... applied from the right of the
    payload; the check makes the total divisible by 10."""
    s = 0
    for i, ch in enumerate(reversed(payload)):
        s += int(ch) * (3 if i % 2 == 0 else 1)
    return str((10 - s % 10) % 10)


def _luhn(payload):
    """ISO/IEC 7812 Luhn over a digit payload whose check digit follows:
    the rightmost payload digit is doubled, products > 9 lose 9."""
    s = 0
    for i, ch in enumerate(reversed(payload)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        s += d
    return str((10 - s % 10) % 10)


def _expand_alnum(s):
    """Letters A=10 ... Z=35, digits themselves (ISO 6166 / ISO 17442
    expansion rule)."""
    return "".join(str(ord(c) - 55) if c.isalpha() else c for c in s)


def _charval(c):
    """CUSIP alphabet 0-9 A-Z * @ # -> 0..38 (ANSI X9.6)."""
    if c.isdigit():
        return int(c)
    if c in "*@#":
        return 36 + "*@#".index(c)
    return ord(c) - 55


def _verhoeff_run(digits):
    c = 0
    for i, ch in enumerate(reversed(digits)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c


def _damm_run(digits):
    c = 0
    for ch in digits:
        c = _DAMM[c][int(ch)]
    return c


# ------------------------------------------------------- scheme records
# regex applies to the normalized string (upper, spaces and hyphens
# stripped — except cas, which REQUIRES its canonical hyphens and is
# matched before stripping them). payload(n) / check(n) split a
# normalized value; check_fn(payload) -> check character.
_DIGITS = "0123456789"


def _last1(n):
    return n[:-1], n[-1]


def _last2(n):
    return n[:-2], n[-2:]


def _cusip_check(payload):
    """ANSI X9.6: even 1-based positions doubled, digits of the product
    summed; check = mod-10 complement."""
    total = 0
    for i, c in enumerate(payload):
        v = _charval(c)
        if i % 2:
            v = v * 2
            v = v // 10 + v % 10
        total += v
    return str((10 - total % 10) % 10)


_SCHEMES = {
    "isbn10": dict(
        spec="ISO 2108 (mod 11, weights 10..1, X=10)",
        rx=r"\d{9}[0-9X]", check_n=1, split=_last1,
        check_fn=lambda p: str((11 - sum(
            int(d) * (10 - i) for i, d in enumerate(p)) % 11) % 11)
        .replace("10", "X"),
        pos_charsets=lambda i, n: "0123456789X" if i == 9 else _DIGITS),
    "isbn13": dict(
        spec="ISO 2108 Bookland (978/979) + GS1 mod 10",
        rx=r"97[89]\d{10}", check_n=1, split=_last1,
        check_fn=_mod10,
        pos_charsets=lambda i, n: _DIGITS),
    "ean8": dict(
        spec="GS1 GTIN-8 (General Specifications, module 10)",
        rx=r"\d{8}", check_n=1, split=_last1,
        check_fn=_mod10,
        pos_charsets=lambda i, n: _DIGITS),
    "ean13": dict(
        spec="GS1 GTIN-13 (General Specifications, module 10)",
        rx=r"\d{13}", check_n=1, split=_last1,
        check_fn=_mod10,
        pos_charsets=lambda i, n: _DIGITS),
    "upca": dict(
        spec="GS1 GTIN-12 / UPC-A (General Specifications, module 10)",
        rx=r"\d{12}", check_n=1, split=_last1,
        check_fn=_mod10,
        pos_charsets=lambda i, n: _DIGITS),
    "gtin14": dict(
        spec="GS1 GTIN-14 (indicator digit; module 10)",
        rx=r"\d{14}", check_n=1, split=_last1,
        check_fn=_mod10,
        pos_charsets=lambda i, n: _DIGITS),
    "issn": dict(
        spec="ISO 3297 (mod 11, weights 8..2, X=10)",
        rx=r"\d{7}[0-9X]", check_n=1, split=_last1,
        check_fn=lambda p: str((11 - sum(
            int(d) * (8 - i) for i, d in enumerate(p)) % 11) % 11)
        .replace("10", "X"),
        pos_charsets=lambda i, n: "0123456789X" if i == 7 else _DIGITS,
        pretty=lambda v: v[:4] + "-" + v[4:]),
    "isin": dict(
        spec="ISO 6166 (letters A=10..Z=35, then Luhn)",
        rx=r"[A-Z]{2}[A-Z0-9]{9}\d", check_n=1, split=_last1,
        check_fn=lambda p: _luhn(_expand_alnum(p)),
        pos_charsets=lambda i, n: (_DIGITS if i == 11 else
                                   (_DIGITS + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                                    if i >= 2 else "ABCDEFGHIJKLMNOPQRSTUVWXYZ"))),
    "cusip": dict(
        spec="ANSI X9.6 (alphabet 0-9 A-Z * @ #; even positions doubled)",
        rx=r"[A-Z0-9*@#]{8}\d", check_n=1, split=_last1,
        check_fn=_cusip_check,
        pos_charsets=lambda i, n: _DIGITS
        + "ABCDEFGHIJKLMNOPQRSTUVWXYZ*@#" if i < 8 else _DIGITS),
    "sedol": dict(
        spec="LRO SEDOL (digits + consonants only, weights 1,3,1,7,3,9)",
        rx=r"[0-9BCDFGHJKLMNPQRSTVWXYZ]{6}\d", check_n=1, split=_last1,
        check_fn=lambda p: str((10 - sum(
            _charval(c) * w for c, w in zip(p, (1, 3, 1, 7, 3, 9))
            ) % 10) % 10),
        pos_charsets=lambda i, n: _DIGITS
        + "BCDFGHJKLMNPQRSTVWXYZ" if i < 6 else _DIGITS),
    "aba": dict(
        spec="US Federal Reserve / ABA routing (weights 3,7,1; sum %10=0)",
        rx=r"\d{9}", check_n=1, split=_last1,
        check_fn=lambda p: str((10 - sum(
            int(d) * w for d, w in zip(
                p, (3, 7, 1, 3, 7, 1, 3, 7))) % 10) % 10),
        pos_charsets=lambda i, n: _DIGITS),
    "lei": dict(
        spec="ISO 17442 (ISO 7064 MOD 97-10 over entity ID + '00')",
        rx=r"[A-Z0-9]{18}\d{2}", check_n=2, split=_last2,
        check_fn=lambda p: str(98 - int(_expand_alnum(p) + "00") % 97)
        .zfill(2),
        pos_charsets=lambda i, n: _DIGITS
        + "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if i < 18 else _DIGITS),
    "orcid": dict(
        spec="ISO 27729 (ISO 7064 MOD 11-2, X=10)",
        rx=r"\d{15}[0-9X]", check_n=1, split=_last1,
        check_fn=lambda p: (lambda r: "X" if r == 10 else str(r))(
            (12 - _orcid_p(p)) % 11),
        pos_charsets=lambda i, n: "0123456789X" if i == 15 else _DIGITS,
        pretty=lambda v: "-".join((v[0:4], v[4:8], v[8:12], v[12:16]))),
    "cas": dict(
        spec="CAS Registry Number (sum digit*position from right, mod 10)",
        rx=r"\d{1,7}-\d{2}-\d", check_n=1, raw=True,
        split=lambda n: (n.rsplit("-", 1)[0], n[-1]),
        check_fn=lambda p: str(sum(
            int(d) * (i + 1) for i, d in enumerate(reversed(
                p.replace("-", "")))) % 10),
        pos_charsets=lambda i, n: "" if n[i] == "-" else _DIGITS,
        pretty=lambda v: v),
    "verhoeff": dict(
        spec="Verhoeff 1969 (dihedral group D5; published tables)",
        rx=r"\d{2,}", check_n=1, split=_last1,
        check_fn=lambda p: str(_INV[_verhoeff_run(p + "0")]),
        auto=False,
        pos_charsets=lambda i, n: _DIGITS),
    "damm": dict(
        spec="Damm 2004 (totally anti-symmetric quasigroup; published "
             "table)",
        rx=r"\d{2,}", check_n=1, split=_last1,
        check_fn=lambda p: str(_damm_run(p)),
        auto=False,
        pos_charsets=lambda i, n: _DIGITS),
}


def _orcid_p(p15):
    p = 0
    for d in p15:
        p = (p + int(d)) * 2 % 11
    return p


_RX = {name: re.compile("^(?:" + s["rx"] + ")$")
       for name, s in _SCHEMES.items()}


def scheme_names():
    return list(_SCHEMES)


# ---------------------------------------------------------- normalization
def normalize(value):
    """Uppercase, spaces/NBSP stripped, hyphens stripped. CAS keeps its
    hyphens (canonical form required) — handled per-scheme, not here."""
    return ((value or "").strip().upper()
            .replace(" ", "").replace("\u00a0", "")
            .replace("-", ""))


# ------------------------------------------------------------ core modes
def _match_entry(scheme, value, norm):
    s = _SCHEMES[scheme]
    n = value.upper().replace(" ", "") if s.get("raw") else norm
    if not _RX[scheme].match(n):
        return None
    payload, given = s["split"](n)
    expected = s["check_fn"](payload)
    return {"scheme": scheme, "spec": s["spec"],
            "checksum_valid": given == expected,
            "given_check_char": given, "expected_check_char": expected,
            "normalized": n}


def _check(value, scheme=None):
    norm = normalize(value)
    schemes = [scheme] if scheme else [
        n for n, s in _SCHEMES.items() if s.get("auto", True)]
    cands = []
    for sc in schemes:
        e = _match_entry(sc, value, norm)
        if e:
            cands.append(e)
    if scheme:
        if not cands:
            raise DigitError(
                "not a %s shape (%s); expected format %s"
                % (scheme, value, _SCHEMES[scheme]["rx"]))
        e = cands[0]
        out = {"mode": "check", "input": value, "unique": True, **e}
        src, sc = e["normalized"], scheme
    else:
        valid = [e for e in cands if e["checksum_valid"]]
        out = {"mode": "check", "input": value, "normalized": norm,
               "candidates": cands, "detected": bool(valid),
               "unique": len(valid) == 1,
               "valid_candidates": [e["scheme"] for e in valid]}
        # pretty render only when the identity is unambiguous: an
        # 8-digit EAN is ISSN-shaped too, and we do not hyphenate a
        # guess.
        if len(valid) == 1:
            src, sc = valid[0]["normalized"], valid[0]["scheme"]
        else:
            src, sc = None, None
    if sc:
        p = _pretty(src, sc)
        if p:
            out["pretty"] = p
    return out


def _pretty(norm, scheme):
    """Canonical printed form where it is algorithmic (issn, orcid,
    cas). ISBN hyphenation needs the registration-group range tables —
    out of scope, said in the module docstring, never improvised."""
    f = _SCHEMES[scheme].get("pretty")
    if f and _RX[scheme].match(norm):
        return f(norm)
    return None


def _generate(scheme, value):
    s = _SCHEMES[scheme]
    n = value.strip().upper().replace(" ", "") if s.get("raw") \
        else normalize(value)
    if s.get("raw"):
        # cas payload arrives as the hyphenated body, e.g. 7732-18
        if not re.match(r"^\d{1,7}-\d{2}$", n):
            raise DigitError("cas generate needs body 'NNNNNNN-NN'")
    elif not re.match("^(?:" + s["rx"] + ")$", n + "0" * s["check_n"]):
        raise DigitError("payload %r is not a valid %s payload "
                         "(format %s)" % (value, scheme, s["rx"]))
    chk = s["check_fn"](n)
    value_out = n + ("-" if s.get("raw") else "") + chk
    out = {"mode": "generate", "scheme": scheme, "spec": s["spec"],
           "payload": n, "check_char": chk, "value": value_out,
           "normalized": normalize(value_out)}
    p = _pretty(value_out, scheme)
    if p:
        out["pretty"] = p
    return out


def _repair(value, scheme=None):
    norm = normalize(value)
    out = []
    schemes = [scheme] if scheme else [
        n for n, s in _SCHEMES.items() if s.get("auto", True)]
    for sc in schemes:
        s = _SCHEMES[sc]
        if s.get("raw"):
            continue  # CAS needs its exact hyphen layout; no guessing
        chars = list(norm)
        for pos in range(len(chars)):
            charset = s["pos_charsets"](pos, chars)
            orig = chars[pos]
            for alt in charset:
                if alt == orig:
                    continue
                chars[pos] = alt
                cand = "".join(chars)
                e = _match_entry(sc, cand, cand)
                if e and e["checksum_valid"]:
                    out.append({"scheme": sc, "spec": s["spec"],
                                "value": cand,
                                "edit": {"position": pos, "from": orig,
                                         "to": alt},
                                "pretty": _pretty(cand, sc)})
            chars[pos] = orig
    out.sort(key=lambda e: (e["value"], e["scheme"]))
    truncated = len(out) > REPAIR_CAP
    return {"mode": "repair", "input": value,
            "candidates": out[:REPAIR_CAP], "total_found": len(out),
            "truncated": truncated}


def _scan(text):
    if len(text) > SCANNABLE_MAX:
        raise DigitError("scan text exceeds %d chars (closed cap)"
                         % SCANNABLE_MAX)
    found = []
    for m in re.finditer(r"[A-Z0-9*@#][A-Z0-9*\-@#.]*", text.upper()):
        tok = m.group(0).rstrip("-.")
        if not tok or len(tok) < 6:
            continue
        cands = []
        for sc, s in _SCHEMES.items():
            if not s.get("auto", True):
                continue
            e = _match_entry(sc, tok, normalize(tok))
            if e:
                cands.append({"scheme": sc,
                              "checksum_valid": e["checksum_valid"],
                              "expected_check_char":
                                  e["expected_check_char"]})
        if cands:
            found.append({"token": tok, "start": m.start(),
                          "results": cands})
    truncated = len(found) > 100
    return {"mode": "scan", "text_length": len(text),
            "found": found[:100], "truncated": truncated}


# --------------------------------------------------------------- facade
def checkdigit(mode="check", value=None, scheme=None, text=None):
    if mode not in MODES:
        raise DigitError("mode must be one of %s" % ", ".join(MODES))
    if mode == "scan":
        if not text:
            raise DigitError("scan needs text")
        return _scan(text)
    if not value:
        raise DigitError("%s needs value" % mode)
    if mode == "check":
        # append-only courtesy: identifiers that live on their own
        # named route get pointed there instead of silent nothing
        if re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$",
                    normalize(value or "")):
            return {"mode": "check", "input": value,
                    "candidates": [], "detected": False,
                    "unique": False, "valid_candidates": [],
                    "pointer": "this looks like an IBAN — use "
                               "/api/v1/validate/iban (mod-97 + "
                               "per-country BBAN length)"}
        if scheme and scheme not in _SCHEMES:
            raise DigitError("unknown scheme %r — closed list: %s"
                             % (scheme, ", ".join(_SCHEMES)))
        return _check(value, scheme)
    if mode == "generate":
        if scheme not in _SCHEMES:
            raise DigitError("generate needs a scheme from the closed "
                             "list: %s" % ", ".join(_SCHEMES))
        return _generate(scheme, value)
    if mode == "repair":
        if scheme and scheme not in _SCHEMES:
            raise DigitError("unknown scheme %r — closed list: %s"
                             % (scheme, ", ".join(_SCHEMES)))
        return _repair(value, scheme)
    raise DigitError("mode %r not implemented" % mode)
