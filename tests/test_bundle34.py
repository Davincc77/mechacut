"""Bundle 34 — /id/checkdigit (digitkit). 15 published schemes.
Expected values are computed BY HAND (arithmetic in the comments) or
re-derived by oracle code transcribed from the spec definitions in this
file — never copied from digitkit. Published vector sources: the veridigit
benchmark README (github.com/qinisolabs/veridigit) and the dsh-checkdigit
scheme table (github.com/TYEclipse/dsh-checkdigit), plus canonical
examples published in the specs/articles themselves (2363 Verhoeff, 5724
Damm, 0306406152 ISBN, 7732-18-5 water CAS, 021000021 JPMorgan ABA).
"""
import json
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, ".")
import digitkit
import main
import payments

client = TestClient(main.app)


# ---------------------------------------------------------- the point
def _gs1(payload):
    """GS1 module-10, transcribed from the published definition:
    weights 3,1,3,... from the right of the payload."""
    s = sum(int(d) * (3 if i % 2 == 0 else 1)
            for i, d in enumerate(reversed(payload)))
    return str((10 - s % 10) % 10)


def _iso_expand(s):
    """ISO letter expansion A=10..Z=35 (definition, not digitkit)."""
    return "".join(str(ord(c) - 55) if "A" <= c <= "Z" else c for c in s)


def _luhn(payload_digits):
    """ISO/IEC 7812 check digit over the payload (published recursive
    form: double every second digit from the right of the payload)."""
    s = 0
    for i, ch in enumerate(reversed(payload_digits)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        s += d
    return str((10 - s % 10) % 10)


# ------------------------------------------------- published vectors
# Every one verified by hand against its definition:
PUBLISHED = [
    # isbn10 0306406152: 0*10+3*9+0*8+6*7+4*6+0*5+6*4+1*3+5*2+2*1 = 132
    # = 11*12 -> mod 11 == 0  (the published example ISBN)
    ("isbn10", "0306406152"),
    # isbn13 9780306406157: same body as above + 978 prefix (Bookland)
    ("isbn13", "9780306406157"),
    # ean8 96385074: 7*3+0+5*3+8+3*3+6+9*3 = 21+15+8+9+6+27 = 86;
    # (10-6)%10 = 4  (published GS1 example)
    ("ean8", "96385074"),
    # ean13 4006381333931: reversed payload 393331836004 weights
    # 3,1,..: 9+9+9+3+9+1+24+3+18+0+0+4 = 89 -> check 1
    ("ean13", "4006381333931"),
    ("upca", "036000291452"),
    # gtin14 09780306406157: 0*3+9+7*3+8+0+3+0+6+4*3+0+6*3+1+5*3
    # = 0+9+21+8+0+3+0+6+12+0+18+1+15 = 93 -> check 7
    ("gtin14", "09780306406157"),
    # issn 03785955: 0*8+3*7+7*6+8*5+5*4+9*3+5*2 = 160; 160%11=6;
    # (11-6) = 5
    ("issn", "03785955"),
    ("isin", "US0378331005"),   # Apple, published ISIN
    ("isin", "DE0005190003"),   # BMW, published ISIN
    ("cusip", "037833100"),     # Apple CUSIP, published
    # sedol B15KXQ8: B=11,K=20,X=33,Q=26 weights 1,3,1,7,3,9:
    # 11+3+5+140+99+234 = 492 -> (10-2)%10 = 8
    ("sedol", "B15KXQ8"),
    # aba 021000021: (0+1+0+0+0)*3 + (2+8+3+2)*7? no — weights by
    # position 3,7,1,3,7,1,3,7,1: 0+14+1+0+0+0+0+14+1 = 30, 30%10==0
    ("aba", "021000021"),       # JPMorgan Chase, published example
    ("lei", "529900T8BM49AURSDO55"),   # GLEIF-published example LEI
    ("lei", "5493001KJTIIGC8Y1R12"),   # JPMorgan LEI, published
    # orcid 0000-0002-1825-0097: MOD 11-2 recursive over 000000021825009
    # -> p=5, (12-5)%11 = 7  (the canonical Josiah Carberry iD)
    ("orcid", "0000-0002-1825-0097"),
    # cas 7732-18-5 (WATER): body 773218 from right:
    # 8*1+1*2+2*3+3*4+7*5+7*6 = 8+2+6+12+35+42 = 105, 105%10 = 5
    ("cas", "7732-18-5"),
    ("verhoeff", "2363"),       # the published worked example
    ("damm", "5724"),           # the published worked example
]


@pytest.mark.parametrize("scheme,value", PUBLISHED)
def test_published_vectors_pass(scheme, value):
    r = digitkit.checkdigit("check", value=value, scheme=scheme)
    assert r["checksum_valid"], (scheme, value)
    assert r["expected_check_char"] == r["given_check_char"]


@pytest.mark.parametrize("scheme,value", PUBLISHED)
def test_published_vectors_also_detected_by_auto(scheme, value):
    if scheme in ("verhoeff", "damm"):
        pytest.skip("generic schemes need an explicit scheme= — closed "
                    "design decision")
    r = digitkit.checkdigit("check", value=value)
    assert scheme in r["valid_candidates"], (scheme, value)


# ------------------------------------------- cross-oracles per family
def test_gs1_family_matches_definition_directly():
    # (scheme, payload, expected check) — all hand-computed above
    for scheme, p, c in [("ean8", "9638507", "4"),
                         ("ean13", "400638133393", "1"),
                         ("upca", "03600029145", "2"),
                         ("gtin14", "0978030640615", "7"),
                         ("isbn13", "978030640615", "7")]:
        assert _gs1(p) == c
        r = digitkit.checkdigit("generate", scheme=scheme, value=p)
        assert r["value"] == p + c


def test_isin_luhn_oracle():
    for isin in ("US0378331005", "DE0005190003"):
        expanded = _iso_expand(isin[:11])          # letters -> digits
        assert _luhn(expanded) == isin[11]         # independent Luhn
        r = digitkit.checkdigit("check", value=isin, scheme="isin")
        assert r["checksum_valid"]


def test_lei_mod97_oracle():
    for lei in ("529900T8BM49AURSDO55", "5493001KJTIIGC8Y1R12"):
        assert int(_iso_expand(lei)) % 97 == 1     # ISO 7064 definition
        assert digitkit.checkdigit(
            "check", value=lei, scheme="lei")["checksum_valid"]


def test_isbn10_to_isbn13_conversion_pair():
    # 978 + ISBN-10 body (9 digits) -> same item, mod-10 check
    assert digitkit.checkdigit(
        "check", value="0306406152", scheme="isbn10")["checksum_valid"]
    g = digitkit.checkdigit("generate", scheme="isbn13",
                            value="978030640615")
    assert g["value"] == "9780306406157"


# ------------------------------------------------------ table honesty
def test_verhoeff_tables_are_the_published_ones():
    d, p, inv = digitkit._D, digitkit._P, digitkit._INV
    for row in d:
        assert sorted(row) == list(range(10))      # Latin rows
    assert d[0] == tuple(range(10))                # identity row
    assert all(d[j][inv[j]] == 0 for j in range(10))  # inverse law
    for row in p:
        assert sorted(row) == list(range(10))
    assert p[0] == tuple(range(10))
    # Wikipedia's own worked trace for 2363 (right-to-left):
    # (0,p0(3))=3 -> (3,p1(6))=d[3][3]=1 -> (1,p2(3))=d[1][3]=4
    # -> (4,p3(2))=d[4][1]=0  => valid
    assert digitkit._verhoeff_run("2363") == 0
    assert digitkit.checkdigit(
        "generate", scheme="verhoeff", value="236")["value"] == "2363"


def test_damm_table_is_a_quasigroup_with_zero_diagonal():
    t = digitkit._DAMM
    assert len(t) == 10 and all(len(r) == 10 for r in t)
    for r in t:
        assert sorted(r) == list(range(10))        # Latin rows
    for c in range(10):
        assert sorted(r[c] for r in t) == list(range(10))  # Latin cols
    assert all(t[i][i] == 0 for i in range(10))    # weak total antisym
    # published worked example: 5 -> 9 -> 7 -> 4 -> 0
    assert digitkit._damm_run("5724") == 0
    assert digitkit.checkdigit(
        "generate", scheme="damm", value="572")["value"] == "5724"


def test_generic_schemes_detect_every_single_error_and_transposition():
    # exhaustive over payloads 0..999: flipping one digit, or swapping
    # two neighbours, must ALWAYS invalidate (the published claim)
    for scheme in ("verhoeff", "damm"):
        for base in range(1000):
            v = digitkit.checkdigit("generate", scheme=scheme,
                                    value=str(base))["value"]
            digits = list(v)
            for i in range(len(digits)):
                for alt in "0123456789":
                    if alt == digits[i]:
                        continue
                    m = digits[:]
                    m[i] = alt
                    bad = digitkit.checkdigit(
                        "check", value="".join(m), scheme=scheme)
                    assert not bad["checksum_valid"], (scheme, v, i, alt)
            for i in range(len(digits) - 1):
                if digits[i] == digits[i + 1]:
                    continue
                m = digits[:]
                m[i], m[i + 1] = m[i + 1], m[i]
                bad = digitkit.checkdigit("check", value="".join(m),
                                          scheme=scheme)
                assert not bad["checksum_valid"], (scheme, v, i)


# ------------------------------------------------------- honest modes
def test_bookland_ambiguity_is_reported_not_guessed():
    r = digitkit.checkdigit("check", value="978-0-306-40615-7")
    assert r["valid_candidates"] == ["isbn13", "ean13"]
    assert r["unique"] is False
    assert "pretty" not in r        # no hyphenation of a guess


def test_unique_match_gets_its_pretty_form():
    r = digitkit.checkdigit("check", value="03785955")
    # 96385074 is ISSN-shaped too; 03785955: ean8 check:
    # 5*3+9+3*3+8+5*3+3+0*3? reversed 555983730? -> compute: payload
    # 0378595: 5*3+9*1+5*3+8*1+7*3+3*1+0*3 = 15+9+15+8+21+3+0 = 71
    # check would be 9, not 5 -> ean8 INVALID, issn VALID -> unique
    assert r["unique"] is True and r["detected"] is True
    assert r["pretty"] == "0378-5955"


def test_wrong_digit_names_the_expected_one():
    # 4006381333939: same payload as the published EAN-13, check must
    # be 1 (hand-computed above)
    r = digitkit.checkdigit("check", value="4006381333939",
                            scheme="ean13")
    assert not r["checksum_valid"]
    assert r["expected_check_char"] == "1" and r["given_check_char"] == "9"


def test_repair_finds_the_original_and_no_impostors():
    # corrupt one digit (position 11: 9 -> 4): 4006381333941
    r = digitkit.checkdigit("repair", value="4006381333941",
                            scheme="ean13")
    vals = [c["value"] for c in r["candidates"]]
    assert "4006381333931" in vals
    # closed math: weights 1 and 3 are both invertible mod 10, so a
    # 13-char EAN-13 has EXACTLY one fixing character per position
    assert r["total_found"] == 13
    for c in r["candidates"]:
        assert _gs1(c["value"][:12]) == c["value"][12]


def test_generate_and_bad_payloads():
    g = digitkit.checkdigit("generate", scheme="cas", value="7732-18")
    assert g["value"] == "7732-18-5" and g["pretty"] == "7732-18-5"
    with pytest.raises(digitkit.DigitError):
        digitkit.checkdigit("generate", scheme="isbn10", value="12x456789")
    with pytest.raises(digitkit.DigitError):
        digitkit.checkdigit("check", value="12345678", scheme="ean13")


def test_generic_schemes_need_explicit_scheme():
    r = digitkit.checkdigit("check", value="2363")   # Verhoeff-valid
    assert r["candidates"] == [] and r["detected"] is False
    assert digitkit.checkdigit(
        "check", value="2363", scheme="verhoeff")["checksum_valid"]


def test_cas_requires_hyphens():
    with pytest.raises(digitkit.DigitError):
        digitkit.checkdigit("check", value="7732185", scheme="cas")
    assert digitkit.checkdigit(
        "check", value="7732-18-5", scheme="cas")["checksum_valid"]


def test_scan_finds_and_verdicts():
    text = ("Order: ISBN 978-0-306-40615-7, EAN 4006381333939 (bad), "
            "water CAS 7732-18-5, LEI 5493001KJTIIGC8Y1R12 today")
    r = digitkit.checkdigit("scan", text=text)
    toks = {f["token"]: f for f in r["found"]}
    assert "978-0-306-40615-7" in toks
    bad = toks["4006381333939"]["results"]
    ean = [x for x in bad if x["scheme"] == "ean13"][0]
    assert ean["checksum_valid"] is False and ean["expected_check_char"] \
        == "1"
    cas = [x for x in toks["7732-18-5"]["results"]
           if x["scheme"] == "cas"][0]
    assert cas["checksum_valid"] is True
    assert [x for x in toks["5493001KJTIIGC8Y1R12"]["results"]][0][
        "checksum_valid"] is True


def test_scan_cap_is_named():
    with pytest.raises(digitkit.DigitError):
        digitkit.checkdigit("scan", text="12345678 " * 2500)


# ------------------------------------------------------- API contract
def test_api_check_mode_and_sha():
    r = client.post("/api/v1/id/checkdigit",
                    json={"value": "9780306406157"})
    assert r.status_code == 200
    b = r.json()
    assert b["valid_candidates"] == ["isbn13", "ean13"]
    sha = b.pop("sha256")
    # independent canonical hash
    blob = json.dumps(b, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode()
    import hashlib
    assert hashlib.sha256(blob).hexdigest() == sha


def test_api_errors_name_fields():
    r = client.post("/api/v1/id/checkdigit",
                    json={"value": "x", "scheme": "nope"})
    assert r.status_code == 400
    assert "closed list" in r.text and "ean13" in r.text
    r = client.post("/api/v1/id/checkdigit", json={"mode": "merge",
                                                   "value": "1"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "mode"
    r = client.post("/api/v1/id/checkdigit", json={"mode": "scan"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "text"


def test_tier_is_free():
    assert "/api/v1/id/checkdigit" not in payments.PRICES
    assert "/api/v1/id/checkdigit" not in payments.CAP_ROUTES


def test_agent_surfaces():
    assert "id_checkdigit" in client.get("/agent/manifest").text
    assert "/api/v1/id/checkdigit" in client.get(
        "/tools/id_checkdigit.json").json()["path"]
    hits = [t["tool"] for t in client.get(
        "/route", params={"q": "is this ean check digit wrong"}).json()
        ["tools"]]
    assert "id_checkdigit" in hits[:3]
    assert "id_checkdigit" in client.get("/SKILL-checks.md").text
    # callable through MCP, same bytes as the direct route minus sha
    m = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/call",
                                  "params": {"name": "id_checkdigit",
                                             "arguments": {
                                                 "value": "03785955",
                                                 "scheme": "issn"}}})
    inner = json.loads(m.json()["result"]["content"][0]["text"])
    assert inner["checksum_valid"] is True
    assert inner["pretty"] == "0378-5955"
