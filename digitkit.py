"""The check-digit family: the identifiers a small model gets wrong
CONFIDENTLY (veridigit bench, Nov 2025: a frontier model, tool-free,
missed the check digit 91 % of the time on non-memorised identifiers).

17 schemes, each cited to its published spec — no table here is written
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
  boleto   FEBRABAN linha digitavel (47 digits, Brazil): five fields,
           three module-10 field digits (weights 2,1 from the right,
           digit-summed products), one module-11 general digit
           (weights 2..9 from the right; result <2 or >9 -> 1), and
           campo 5 = fator de vencimento (4) + valor (10). The fator
           counts days since 1997-10-07 and MUST be >= 1000: cycle 1
           ran 1000..9999 up to 2025-02-21, cycle 2 restarted at 1000
           on 2025-02-22 (Linx table + BB Anexo + FEBRABAN concordant,
           read 26-11). Layout sources read 26-11: box4.dev/pt-br/
           brasil/validador-boleto (campo table + published DV
           example 001900000 -> 9), macoratti.net/boleto.htm (BB
           campo composition), github.com/micdog22/confere-boleto
           (barcode reassembly + weight statements).
  mrn      EU/UK customs Movement Reference Number (18 chars): Reg
           414/2009 Annex VII field table — YY (n2) + country (a2) +
           unique identifier (an13) + check (an1); under the UCC,
           2015/2447 Annex B splits field 3 as an12 + procedure (a1)
           + check (an1). The check digit is the ISO 6346 method read
           in the TCP working-party decision "Berekening controlecijfer
           MRN-GRN" (27-11): char values 0-9 own, letters A=10, B=12,
           C=13, D=14, E=15, F=16, G=17, H=18, I=19, J=20, K=21, L=23,
           M=24, N=25, O=26, P=27, Q=28, R=29, S=30, T=31, U=32, V=34,
           W=35, X=36, Y=37, Z=38 (multiples of 11 never issued: no
           11/22/33), weight 2^i on char i+1 from the LEFT, sum mod 11;
           TCP Table 2 renders remainder 10 as the character '0'.
           Printed as Code 128 character set B (cited in the annex).

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
- boleto: the verdict is PER DIGITO (dv1, dv2, dv3, dv_geral — each with
  its given and expected char), because the bank rejects the linha for
  ONE failing DV (ACBr forum vectors, read 26-11). A 48-digit linha is
  refused BY NAME: it is either a conta de consumo (8-prefixed layout)
  or the Banrisul duplo-dígito variant — neither grammar is asserted
  here, we do not guess what we have not sourced. The fator decodes to
  BOTH cycle candidates (1997-10-07 base, 9000-day restart, 2025-02-22
  discontinuity) — never to one date by reading the wall clock. scan
  finds a dot-separated linha inside one token; a space-separated
  printed linha arrives as separate fields by design and needs check.
- MRN: the regulation's own FIELD-TABLE examples (06RO9876AB8890123 /
  check 5 and 14DE9876AB889012X / check 1) are per-field illustrations
  and FAIL the published algorithm — traced by hand 27-11 (06RO…123
  gives '0', 14DE…12X gives '2'). They are refused as golds and the
  divergence is rendered in the verdict; the only vector carrying the
  full arithmetic is the TCP worked example (99IT9876AB8890120 ->
  154031 -> remainder 9 -> MRN 99IT9876AB88901209), replayed in the
  suite against the PUBLISHED sub-products, not against this module.
  A digit in UCC position 17 is rendered procedure=null with the
  pre-2016 grammar named — a letter outside the 2015/2447 table is
  said as NOT_IN_PUBLISHED_TABLE, never invented a meaning for.
- ISBN hyphenation is NOT attempted: it needs the registration-group
  range tables, and getting them from memory is how wrong books get
  shelved. issn/orcid/cas have algorithmic hyphenation, we render it.
"""

import re
from datetime import date, timedelta

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


# ------------------------------------------- MRN (EU/UK customs, 18)
# ISO 6346 char values transcribed verbatim from Table 1 of the TCP
# working-party decision (read 27-11) — note which values are NEVER
# issued (11, 22, 33): the letter series skips multiples of 11, so
# A=10, B=12, K=21, L=23, U=32, V=34, Z=38. A hand-computed value
# table written from memory is how containers used to mis-check.
_ISO6346_VALUES = {
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4,
    "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
    "A": 10, "B": 12, "C": 13, "D": 14, "E": 15, "F": 16, "G": 17,
    "H": 18, "I": 19, "J": 20, "K": 21, "L": 23, "M": 24, "N": 25,
    "O": 26, "P": 27, "Q": 28, "R": 29, "S": 30, "T": 31, "U": 32,
    "V": 34, "W": 35, "X": 36, "Y": 37, "Z": 38,
}


def _iso6346_check(payload):
    """TCP WP decision (MRN/GRN), ISO 6346 method: value x 2^position
    from the LEFT, sum, mod 11; remainder 10 renders as '0' (Table 2).
    Weights stop at 2^16: the check is over the first 17 characters."""
    s = sum(_ISO6346_VALUES[ch] << i for i, ch in enumerate(payload))
    r = s % 11
    return "0" if r == 10 else str(r)


# 2015/2447 Annex B (UCC), field 4 procedure identifier — closed table,
# read verbatim 27-11 (15 codes; F-H, N-Q, X-Z are NOT issued).
_MRN_PROC = {
    "A": "export only",
    "B": "export and exit summary declaration",
    "C": "exit summary declaration only",
    "D": "re-export notification",
    "E": "dispatch of goods in relation with special fiscal territories",
    "J": "transit declaration only",
    "K": "transit declaration and exit summary declaration",
    "L": "transit declaration and entry summary declaration",
    "M": "proof of the customs status of Union goods/customs manifest",
    "R": "import declaration only",
    "S": "import declaration and entry summary declaration",
    "T": "entry summary declaration only",
    "U": "temporary storage declaration",
    "V": "introduction of goods in relation with special fiscal territories",
    "W": "temporary storage declaration and entry summary declaration",
}


def _mrn_decoded(n):
    """Fields as the annexes name them; the procedure slot renders the
    grammar it belongs to instead of inventing a reading."""
    p = n[16]
    if p in _MRN_PROC:
        proc = _MRN_PROC[p]
        note = ("UCC structure (2015/2447 Annex B): n2 country-year, a2, "
                "an12, procedure a1, check an1")
    elif p.isdigit():
        proc = None
        note = ("position 17 is a digit: no UCC procedure character — "
                "2009 field-table grammar (an13 body, Reg 414/2009 "
                "Annex VII) or a non-UCC issuer; which one is not ours "
                "to guess")
    else:
        proc = None
        note = ("NOT_IN_PUBLISHED_TABLE: position 17 is a letter the "
                "2015/2447 procedure table does not issue — rendered "
                "as-is, no meaning invented")
    return {"year_pair": n[0:2], "country": n[2:4],
            "body_an13": n[4:17], "procedure_char": p,
            "procedure": proc, "procedure_note": note,
            "barcode_note": ("the annex requires Code 128 character "
                             "set B for printing the MRN (Reg 414/2009 "
                             "Annex VII, read 27-11)")}


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
    "boleto": dict(
        spec="FEBRABAN linha digitável (47 digits, 5 campos, per-DV "
             "verdicts — see module docstring for the cited layout)",
        rx=r"\d{47}", check_n=0, custom=True, dotless=True,
        pos_charsets=lambda i, n: _DIGITS),
    "mrn": dict(
        spec="EU/UK customs MRN (18 chars; Reg 414/2009 Annex VII "
             "field table + 2015/2447 Annex B; ISO 6346 check over "
             "chars 1-17, weights 2^0..2^16 from the left, mod 11, "
             "remainder 10 -> '0' — TCP WP decision, read 27-11)",
        rx=r"\d{2}[A-Z]{2}[A-Z0-9]{13}[0-9A-Z]", check_n=1,
        split=_last1, check_fn=_iso6346_check,
        decoded_fn=_mrn_decoded,
        pos_charsets=lambda i, n: (
            _DIGITS if i < 2 else
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if i < 4 else
            _DIGITS + "ABCDEFGHIJKLMNOPQRSTUVWXYZ")),
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


# ------------------------------------------------- boleto (FEBRABAN 47)
# Engines transcribed from the layout sources cited in the module
# docstring (read 26-11), NOT from any implementation: mod-10 with
# weights 2,1 from the right of the campo body (products digit-summed),
# general DV mod-11 with weights 2..9 cycling from the right over the
# 43 barcode digits without the DV slot (result <2 or >9 -> 1).
_BOLETO_EPOCH = date(1997, 10, 7)     # fator base date (BB Anexo: data
_BOLETO_RESTART = 9000                # base 07/10/1997; cycle 2 restart
                                      # +9000 days, fator 1000 = 2025-02-22


def _boleto_strip(value):
    """The linha is PRINTED in five fields with dots and spaces; those
    are separators, not data."""
    return re.sub(r"[.\s-]", "", value or "")


def _boleto_mod10(body):
    s = 0
    for i, ch in enumerate(reversed(body)):
        p = int(ch) * (2 if i % 2 == 0 else 1)
        s += p // 10 + p % 10
    return str((10 - s % 10) % 10)


def _boleto_geral(bar43):
    """General DV over the 43 barcode digits without the DV slot,
    weights 2,3,...,9,2,... from the right (micdog22/BB layout)."""
    s = sum(int(d) * (2 + i % 8) for i, d in enumerate(reversed(bar43)))
    res = 11 - s % 11
    return str(1 if res < 2 or res > 9 else res)


def _boleto_linha(bar43):
    """Build the 47-digit linha from the 43-digit barcode body
    (banco3 moeda1 fator4 valor10 livre25, general-DV slot omitted)."""
    banco, moeda, fator, valor, livre = (
        bar43[0:3], bar43[3], bar43[4:8], bar43[8:18], bar43[18:43])
    c1 = banco + moeda + livre[0:5]
    c2 = livre[5:15]
    c3 = livre[15:25]
    geral = _boleto_geral(bar43)
    return (c1 + _boleto_mod10(c1) + c2 + _boleto_mod10(c2)
            + c3 + _boleto_mod10(c3) + geral + fator + valor)


def _boleto_due(fator):
    """Cycle candidates for a fator — NEVER one date from the wall
    clock: fator f maps to base+f (cycle 1) and base+f+9000 (cycle 2)."""
    f = int(fator)
    if f < 1000:
        return [], ("fator %04d is below 1000: FEBRABAN rejects it (due "
                    "dates closer to the 1997-10-07 base than 1000 days "
                    "have no valid factor)" % f)
    d1 = _BOLETO_EPOCH + timedelta(days=f)
    d2 = _BOLETO_EPOCH + timedelta(days=f + _BOLETO_RESTART)
    out = [{"cycle": 1, "due": d1.isoformat()},
           {"cycle": 2, "due": d2.isoformat()}]
    note = ("cycle 1 ended 2025-02-21 (fator 9999); cycle 2 restarted at "
            "1000 on 2025-02-22 — both candidate dates are returned, "
            "which cycle applies is the bearer's fact, not ours")
    return out, note


def _boleto_verdict(digits):
    """Full per-DV verdict + decode of a 47-digit linha."""
    c1, c2, c3 = digits[0:10], digits[10:21], digits[21:32]
    dv_g, c5 = digits[32], digits[33:47]
    bar43 = (c1[0:3] + c1[3] + c5[0:4] + c5[4:14]
             + c1[4:9] + c2[0:10] + c3[0:10])
    dvs = {}
    for name, body, given in (("dv1", c1[0:9], c1[9]),
                              ("dv2", c2[0:10], c2[10]),
                              ("dv3", c3[0:10], c3[10])):
        exp = _boleto_mod10(body)
        dvs[name] = {"given": given, "expected": exp, "valid": given == exp}
    exp_g = _boleto_geral(bar43)
    dvs["dv_geral"] = {"given": dv_g, "expected": exp_g,
                       "valid": dv_g == exp_g}
    fator, valor = c5[0:4], c5[4:14]
    due, note = _boleto_due(fator)
    cents = int(valor)
    return {"scheme": "boleto",
            "spec": "FEBRABAN linha digitável (47 digits, 5 campos)",
            "checksum_valid": all(d["valid"] for d in dvs.values()),
            "normalized": digits, "dvs": dvs,
            "failing_fields": [k for k, d in dvs.items() if not d["valid"]],
            "decoded": {
                "banco": c1[0:3], "moeda": c1[3],
                "fator_vencimento": fator,
                "due_date_candidates": due, "fator_note": note,
                "valor_centavos": valor,
                "valor_decimal": "%d.%02d" % (cents // 100, cents % 100)},
            "barcode44": bar43[0:4] + dv_g + bar43[4:]}


def _boleto_generate(value):
    n = _boleto_strip(value)
    if len(n) == 44:
        raise DigitError(
            "44 digits is the full barcode — mode=check answers the "
            "47-digit linha; mode=generate needs the 43-digit body "
            "(banco3+moeda1+fator4+valor10+campo livre 25, the general "
            "DV slot omitted)")
    if len(n) != 43 or not n.isdigit():
        raise DigitError(
            "boleto generate needs 43 digits, got %r (%d)" % (value, len(n)))
    if int(n[4:8]) < 1000:
        raise DigitError(
            "fator %s below 1000: FEBRABAN rejects due dates closer than "
            "1000 days to the 1997-10-07 base — fix the body, not the DV"
            % n[4:8])
    linha = _boleto_linha(n)
    dv_g = linha[32]
    return {"mode": "generate", "scheme": "boleto",
            "spec": "FEBRABAN linha digitável (47 digits, 5 campos)",
            "payload": n, "value": linha,
            # the printed form on the ticket: five campos, dots inside
            # campos 1-3, campo 4 alone, campo 5 bare (sem edição)
            "value_printed": "%s.%s %s.%s %s.%s %s %s" % (
                linha[0:5], linha[5:10], linha[10:15], linha[15:21],
                linha[21:26], linha[26:32], dv_g, linha[33:47]),
            "barcode44": n[0:4] + dv_g + n[4:],
            "normalized": linha}


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
    if s.get("dotless"):
        n = _boleto_strip(n)
    if not _RX[scheme].match(n):
        return None
    if s.get("custom"):
        return _boleto_verdict(n)
    payload, given = s["split"](n)
    expected = s["check_fn"](payload)
    entry = {"scheme": scheme, "spec": s["spec"],
             "checksum_valid": given == expected,
             "given_check_char": given, "expected_check_char": expected,
             "normalized": n}
    # add-only: schemes that publish field semantics (mrn) return them;
    # every other entry keeps its exact previous shape.
    dfn = s.get("decoded_fn")
    if dfn:
        entry["decoded"] = dfn(n)
    return entry


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
            if scheme == "boleto" and len(_boleto_strip(value)) == 48:
                raise DigitError(
                    "48 digits is not the 47-position FEBRABAN "
                    "cobranca layout: either a consumo linha (8-"
                    "prefixed) or the Banrisul duplo-digito variant "
                    "— neither grammar is asserted here; refusing "
                    "to guess which")
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
    if s.get("custom"):
        return _boleto_generate(value)
    n = value.strip().upper().replace(" ", "") if s.get("raw") \
        else normalize(value)
    if s.get("raw"):
        # cas payload arrives as the hyphenated body, e.g. 7732-18
        if not re.match(r"^\d{1,7}-\d{2}$", n):
            raise DigitError("cas generate needs body 'NNNNNNN-NN'")
    elif re.match("^(?:" + s["rx"] + ")$", n + "0" * s["check_n"]):
        pass
    elif re.match("^(?:" + s["rx"] + ")$", n):
        # B3 (vague Grok 27-11) : « 9780306406150 » etait refuse en
        # generate en citant le regex 13 chiffres QU'IL SATISFAIT — le
        # message se contredisait lui-meme. Desormais la verite nommee :
        # le regex cite est celui du FULL value ; generate veut le BODY
        # sans le caractere de cle. Garde-fou paye a la suite :
        # l'ordre est inverse (payload valide D'ABORD, sinon le regex
        # souple des schemes generiques « \\d{2,} » reclamait un body
        # plus court que la duree du monde).
        raise DigitError("value %r is a FULL %s id — the cited format %s "
                         "matches it WITH its check char; generate wants "
                         "the payload WITHOUT it: send the first %d "
                         "characters" % (value, scheme, s["rx"],
                                         len(n) - s["check_n"]))
    else:
        raise DigitError("payload %r is not a valid %s payload "
                         "(format %s)" % (value, scheme, s["rx"]))
    chk = s["check_fn"](n)
    value_out = n + ("-" if s.get("raw") else "") + chk
    out = {"mode": "generate", "scheme": scheme, "spec": s["spec"],
           "payload": n, "check_char": chk, "value": value_out,
           "normalized": normalize(value_out)}
    dfn = s.get("decoded_fn")
    if dfn:
        out["decoded"] = dfn(value_out)
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
        if s.get("custom"):
            digits = _boleto_strip(norm)
            if len(digits) != 47 or not digits.isdigit():
                continue  # repair answers the 47-digit linha only
            chars = list(digits)
        else:
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
                cand = {"scheme": sc,
                        "checksum_valid": e["checksum_valid"],
                        "expected_check_char": e.get("expected_check_char")}
                if e.get("failing_fields"):
                    cand["failing_fields"] = e["failing_fields"]
                cands.append(cand)
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
