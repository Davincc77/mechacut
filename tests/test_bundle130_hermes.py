"""Bundle 130 — mrn: the EU/UK customs Movement Reference Number joins
/id/checkdigit (rails installment 2a: MRN; creditor-id follows).
Expected values are traced BY HAND (weight products written out below,
each sum double-checked by a second, right-to-left modular pass) or
transcribed from the published TCP working-party example — never
copied from digitkit:

  - Reg 414/2009 Annex VII (export SAD, box MRN) — field table:
    YY n2 + country a2 + unique id an13 + check an1 = 18, printed
    Code 128 charset B. Re-read 27-11.
  - 2015/2447 Annex B — the an13 splits under the UCC into an12 +
    procedure a1 + check an1; procedure codes A B C D E J K L M R S T
    U V W (15 codes, closed table, read verbatim 27-11).
  - TCP working-party decision "Berekening controlecijfer MRN-GRN" —
    the ISO 6346 method with PUBLISHED sub-products for body
    99IT9876AB8890120: values x weights 2^0..2^16 =
    9 18 76 248 144 256 448 768 2560 6144 8192 16384 36864 0 16384
    65536 0; sum 154031; 154031/11 = 14002 remainder 9 -> DV 9;
    Table 2: remainder 10 renders '0'.

  Hand traces (independent of the module's left-to-right shift):
  26GB0000000000313 -> 2+12+68+96 + 0*16..0*32768 + 49152+32768+196608
    = 278706 = 11*25336 + 10 -> remainder 10 -> DV '0'  (Table 2 edge)
  06RO9876AB8890123 -> 12+116+208+144+256+448+768+2560+6144+8192+
    16384+36864+16384+65536+196608 = 350624 = 11*31874 + 10 -> '0'
    (the annex's own field example shows check 5 — illustration, not
    arithmetic: REFUSED as a gold, rendered as the finding it is)
  14DE9876AB889012X -> 1+8+56+120+144+256+448+768+2560+6144+8192+
    16384+36864+16384+65536+2359296 = 2513161 = 11*228469 + 2 -> '2'
    (the annex B worked text cites MRN 14DE9876AB889012X1 — same
    finding class, plus X is not an issued procedure character)
  24FR1234AB567890B -> 2+8+64+232+16+64+192+512+2560+6144+5120+12288+
    28672+65536+147456+0+786432 = 1055298 = 11*95936 + 2 -> '2'
  24FR1234AB567890X -> 1055298 - 786432 + 2359296 = 2628162 =
    11*238923 + 9 -> '9'
"""
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, ".")
import digitkit
import main

client = TestClient(main.app)
main.RATE_LIMIT = 10 ** 9


# --------------------------------------------------- independent oracle
# TCP published sub-products for body 99IT9876AB8890120 (transcribed
# from the decision, not from the module):
TCP_PRODUCTS = (9, 18, 76, 248, 144, 256, 448, 768, 2560, 6144, 8192,
                16384, 36864, 0, 16384, 65536, 0)
TCP_SUM = sum(TCP_PRODUCTS)   # 154031, the number the document prints

TCP_MRN = "99IT9876AB88901209"
UCC_MRN = "24FR1234AB567890B2"      # hand trace: sum 1055298, rem 2
REM10_MRN = "26GB00000000003130"    # hand trace: sum 278706, rem 10


def _iso6346_oracle(body17):
    """ISO 6346 check, written from the STANDARD definition (right-to-
    left iterative remainder, a different evaluation order than the
    module's left-to-right shifts): value*10+digit running mod 11 on
    the weighted table is NOT the same formula — here the textbook
    form: total = sum v_i * 2^i, then total % 11 with 10 -> '0'."""
    val = {}
    for d in range(10):
        val[str(d)] = d
    v = 10
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if v in (11, 22, 33):
            v += 1
        val[ch] = v
        v += 1
    total = 0
    w = 1
    for ch in body17:          # growing weight, applied right of the
        total += val[ch] * w   # previous — an independent loop shape
        w *= 2
    r = total % 11
    return "0" if r == 10 else str(r), total


def test_published_products_sum_is_the_printed_total():
    assert TCP_SUM == 154031           # the document's own figure
    assert TCP_SUM - 11 * 14002 == 9   # 154031/11 = 14002 r 9 (printed)


def test_tcp_worked_example_replays():
    r = digitkit.checkdigit(mode="check", value=TCP_MRN, scheme="mrn")
    assert r["checksum_valid"] is True
    assert _iso6346_oracle(TCP_MRN[:17]) == ("9", TCP_SUM)


def test_flip_is_named_not_hushed():
    bad = TCP_MRN[:17] + "8"
    r = digitkit.checkdigit(mode="check", value=bad, scheme="mrn")
    assert r["checksum_valid"] is False
    assert r["given_check_char"] == "8"
    assert r["expected_check_char"] == "9"


def test_remainder10_renders_zero():
    """TCP Table 2: remainder 10 -> check character '0'. The hand trace
    of 26GB0000000000313 gives remainder 10 (278706 = 11*25336 + 10)."""
    r = digitkit.checkdigit(mode="check", value=REM10_MRN,
                            scheme="mrn")
    assert r["checksum_valid"] is True
    assert r["expected_check_char"] == "0"
    assert _iso6346_oracle(REM10_MRN[:17]) == ("0", 278706)


def test_annex_field_example_is_a_refused_gold():
    """06RO9876AB88901235 pairs the annex's field EXAMPLES (06, RO,
    9876AB8890123, 5) — the check digit the algorithm gives is 0, not
    5. Rendered as the divergence it is; the vector must come back
    INVALID (the annexes' per-field illustrations are not arithmetic)."""
    r = digitkit.checkdigit(mode="check", value="06RO9876AB88901235",
                            scheme="mrn")
    assert r["checksum_valid"] is False
    assert r["given_check_char"] == "5"
    assert r["expected_check_char"] == "0"
    assert _iso6346_oracle("06RO9876AB8890123") == ("0", 350624)


def test_annexb_cited_mrn_fails_its_own_algorithm():
    """The 2015/2447 worked text cites MRN 14DE9876AB889012X1:
    expected '2' (hand trace 2513161 = 11*228469 + 2), and X is not an
    issued procedure character — both named."""
    r = digitkit.checkdigit(mode="check", value="14DE9876AB889012X1",
                            scheme="mrn")
    assert r["checksum_valid"] is False
    assert r["expected_check_char"] == "2"
    d = r["decoded"]
    assert d["procedure"] is None
    assert "NOT_IN_PUBLISHED_TABLE" in d["procedure_note"]


def test_ucc_procedure_char_decodes_from_the_closed_table():
    r = digitkit.checkdigit(mode="check", value=UCC_MRN, scheme="mrn")
    assert r["checksum_valid"] is True
    d = r["decoded"]
    assert d["year_pair"] == "24" and d["country"] == "FR"
    assert d["body_an13"] == "1234AB567890B"
    assert d["procedure_char"] == "B"
    assert d["procedure"] == "export and exit summary declaration"
    assert "UCC structure" in d["procedure_note"]
    assert "Code 128" in d["barcode_note"]


def test_procedure_slot_digit_names_the_2009_grammar():
    """TCP's own example body ends 120 at position 17 — a digit: no
    UCC procedure character. The verdict says which grammar it belongs
    to instead of inventing one."""
    r = digitkit.checkdigit(mode="check", value=TCP_MRN, scheme="mrn")
    d = r["decoded"]
    assert d["procedure"] is None
    assert d["procedure_char"] == "0"
    assert "2009 field-table grammar" in d["procedure_note"]


def test_off_table_letter_is_said_not_shelved():
    r = digitkit.checkdigit(mode="check", value="24FR1234AB567890X9",
                            scheme="mrn")
    assert r["checksum_valid"] is True  # hand trace 2628162 = 11*238923 + 9
    d = r["decoded"]
    assert d["procedure"] is None
    assert "NOT_IN_PUBLISHED_TABLE" in d["procedure_note"]


def test_generate_matches_hand_trace():
    r = digitkit.checkdigit(mode="generate", scheme="mrn",
                            value="24FR1234AB567890B")
    assert r["check_char"] == "2"
    assert r["value"] == UCC_MRN


def test_autodetect_unique_and_lowercase_survives():
    r = digitkit.checkdigit(mode="check", value=TCP_MRN)
    assert r["valid_candidates"] == ["mrn"]
    assert r["unique"] is True
    # no-scheme answers the AUTO-DETECT shape (candidates, not a flat
    # verdict) — the lowercase form must be normalized to the same id
    r2 = digitkit.checkdigit(mode="check", value=TCP_MRN.lower())
    assert r2["valid_candidates"] == ["mrn"]
    assert r2["normalized"] == TCP_MRN


def test_repair_finds_the_named_single_edit():
    r = digitkit.checkdigit(mode="repair", scheme="mrn",
                            value="24FR1234AB567890B5")
    hits = [c for c in r["candidates"]
            if c["value"] == UCC_MRN
            and c["edit"] == {"position": 17, "from": "5", "to": "2"}]
    assert hits, r["candidates"]


def test_scan_points_at_the_mrn_without_claiming_more():
    text = ("Suite a votre declaration, votre MRN 99IT9876AB88901209 "
            "a ete accepte.")
    r = digitkit.checkdigit(mode="scan", text=text)
    tok = [f for f in r["found"] if f["token"] == TCP_MRN]
    assert len(tok) == 1
    assert tok[0]["results"] == [
        {"scheme": "mrn", "checksum_valid": True,
         "expected_check_char": "9"}]


def test_shape_refused_by_name():
    with pytest.raises(digitkit.DigitError) as e:
        digitkit.checkdigit(mode="check", value="99IT9876AB889012",
                            scheme="mrn")
    assert "mrn" in str(e.value) and "expected format" in str(e.value)
    # year pair MUST be numeric digits — letters up front die too
    with pytest.raises(digitkit.DigitError):
        digitkit.checkdigit(mode="check", value="IT9IT9876AB8890120",
                            scheme="mrn")


def test_other_schemes_keep_their_exact_previous_shape():
    """Add-only contract: 'decoded' appears for mrn, nowhere else."""
    r = digitkit.checkdigit(mode="check", value="9780306406158")
    for cand in r["candidates"]:
        assert "decoded" not in cand, cand["scheme"]


def test_api_200_and_deterministic():
    body = {"mode": "check", "value": UCC_MRN, "scheme": "mrn"}
    r1 = client.post("/api/v1/id/checkdigit", json=body)
    r2 = client.post("/api/v1/id/checkdigit", json=body)
    assert r1.status_code == 200 and r1.json() == r2.json()
    assert r1.json()["decoded"]["procedure"].startswith("export and")


def test_scheme_closed_list_mentions_mrn():
    src = open("main.py", encoding="utf-8").read()
    assert "mrn verhoeff damm; omit to" in src
    assert "17 published schemes" in src
    names = digitkit.scheme_names()
    assert "mrn" in names and names.count("mrn") == 1
