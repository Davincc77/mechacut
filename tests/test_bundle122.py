"""Bundle 122 — boleto: the FEBRABAN linha digitavel joins /id/checkdigit
(id_checkdigit REVISION, grouped rails installment 1: boleto; MRN +
creditor-id follow as installment 2). Expected values are traced BY
HAND below (weight sums printed) or transcribed independently from the
layout sources read 26-11 — never copied from digitkit:

  - box4.dev/pt-br/brasil/validador-boleto — campo table (10+11+11+1+14
    = 47) and the published example: campo 1 body 001900000 -> DV 9,
    printed "00190.00009".
  - macoratti.net/boleto.htm — BB campo composition: campo 1 = banco
    (bar 1-3) + moeda (4) + livre positions; campo 5 = fator (bar 6-9)
    + valor (bar 10-19), 14 positions, sem edicao.
  - github.com/micdog22/confere-boleto — barcode 44 = 1-3 banco, 4
    moeda, 5 DV geral, 6-9 fator, 10-19 valor, 20-44 livre; mod-10
    weights 2,1 right-to-left digit-summed; DV geral mod-11 weights
    2..9, results 0/10/11 -> DV 1; fator = days since 1997-10-07.
  - b121 census (Linx fator table + BB Anexo + FEBRABAN): fator 1000
    floor, cycle 1 9999 = 2025-02-21, cycle 2 restarts 1000 = 2025-02-22.
"""
import hashlib
import json
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, ".")
import digitkit
import main

client = TestClient(main.app)
main.RATE_LIMIT = 10 ** 9


# --------------------------------------------------- independent oracle
def _b10(body):
    """FEBRABAN mod-10 (definition, transcribed from the sources above,
    not from digitkit): weights 2,1,2,1 from the right of the campo
    body, each product replaced by the sum of its digits."""
    s = 0
    for i, d in enumerate(reversed(body)):
        p = int(d) * (2 if i % 2 == 0 else 1)
        s += p // 10 + p % 10
    return str((10 - s % 10) % 10)


def _bgeral(bar43):
    """mod-11 over the 43 digits without the DV slot, weights
    2,3,4,5,6,7,8,9,2,... from the right; result = 11 - sum%11, and
    result <2 or >9 gives DV 1 (published edge rule)."""
    s = sum(int(d) * (2 + i % 8) for i, d in enumerate(reversed(bar43)))
    r = 11 - s % 11
    return str(1 if r < 2 or r > 9 else r)


def _linha(banco, moeda, fator, valor, livre):
    c1 = banco + moeda + livre[0:5]
    c2 = livre[5:15]
    c3 = livre[15:25]
    bar43 = banco + moeda + fator + valor + livre
    return (c1 + _b10(c1) + c2 + _b10(c2) + c3 + _b10(c3)
            + _bgeral(bar43) + fator + valor)


# ------------------------------------------------------------ the golds
# VEC A — hand-traced 26-11 (scratch/trace_boleto_b122.py, written
# before digitkit existed for boleto):
#   banco 001, moeda 9, fator 1000, valor 150.00, livre 12345...001
#   DV1 payload 001912345: from right 5x2=10->1, 4x1=4, 3x2=6, 2x1=2,
#     1x2=2, 9x1=9, 1x2=2, 0, 0 -> sum 26 -> DV (10-6)=4
#   DV2 0000000000: sum 0 -> 0;  DV3 0000000001: 1x2=2 -> sum 2 -> 8
#   geral bar43 sum 232, 232%11=1, 11-1=10 -> edge -> DV 1
VEC_A = ("00191234540000000000000000000018110000000015000")
BAR_A = "00191100000000150001234500000000000000000001"

# VEC B — banco 341 zero livre, fator 4321, valor 0.00 (all-zero livre):
#   DV1 341900000: 9x1=9, 1x2=2, 4x1=4, 3x2=6 -> sum 21 -> 9
#   DV2/DV3 zero -> 0;  geral sum 177, 177%11=1, 11-1=10 -> edge -> 1
VEC_B = ("34190000090000000000000000000000143210000000000")

# VEC C — mod-11 rest 0 edge: geral sum 110, 110%11=0, 11-0=11 -> 1
VEC_C = ("00190000090000000000000000000042120000000000001")

# ANCHOR — the published box4 example, whole linha built by hand:
#   banco 001 moeda 9, zero livre -> c1 body 001900000 -> DV 9
#   (exactly the published campo 1 "00190.00009");
#   DV2=DV3=0; geral: digits 1(idx2) 9(idx3) 1(idx4), weights from the
#   right of the 43-body (42-k)%8+2: idx2->2x1=2, idx3->9x9=81,
#   idx4->1x8=8 -> sum 91, 91%11=3, 11-3=8 -> DV geral 8; fator 1000,
#   valor zero.
ANCHOR = ("00190000090000000000000000000000810000000000000")


# ---------------------------------------------------------------- check
def test_vec_a_all_dvs_pass():
    r = digitkit.checkdigit(mode="check", value=VEC_A, scheme="boleto")
    assert r["checksum_valid"] is True
    assert r["failing_fields"] == []
    for dv in r["dvs"].values():
        assert dv["valid"] and dv["given"] == dv["expected"]
    assert r["dvs"]["dv1"] == {"given": "4", "expected": "4", "valid": True}
    assert r["dvs"]["dv_geral"] == {"given": "1", "expected": "1",
                                    "valid": True}  # the 11-r=10 edge
    assert r["barcode44"] == BAR_A
    d = r["decoded"]
    assert d["banco"] == "001" and d["moeda"] == "9"
    assert d["valor_centavos"] == "0000015000"
    assert d["valor_decimal"] == "150.00"


def test_published_anchor_campo1():
    """The box4.dev published campo 1 example 00190.00009 must come out
    of a full valid linha built by hand."""
    r = digitkit.checkdigit(mode="check", value=ANCHOR, scheme="boleto")
    assert r["checksum_valid"] is True
    assert r["normalized"][0:10] == "0019000009"  # 00190.00009
    assert r["dvs"]["dv_geral"]["expected"] == "8"  # traced sum 91


def test_zero_valor_is_legal():
    r = digitkit.checkdigit(mode="check", value=VEC_B, scheme="boleto")
    assert r["checksum_valid"] is True
    assert r["decoded"]["valor_decimal"] == "0.00"
    assert r["decoded"]["fator_vencimento"] == "4321"


def test_dotted_and_spaced_forms_agree():
    spaced = (VEC_A[0:5] + "." + VEC_A[5:10] + " " +
              VEC_A[10:15] + "." + VEC_A[15:21] + " " +
              VEC_A[21:26] + "." + VEC_A[26:32] + " " +
              VEC_A[32] + " " + VEC_A[33:47])
    a = digitkit.checkdigit(mode="check", value=VEC_A, scheme="boleto")
    b = digitkit.checkdigit(mode="check", value=spaced, scheme="boleto")
    assert a["normalized"] == b["normalized"] == VEC_A
    assert a["checksum_valid"] == b["checksum_valid"]


def test_named_failure_per_dv():
    """The ACBr forum vector class: the bank rejects for ONE campo DV;
    the verdict names which one, given vs expected."""
    bad = VEC_A[:9] + "9" + VEC_A[10:]      # corrupt dv1 (4 -> 9)
    r = digitkit.checkdigit(mode="check", value=bad, scheme="boleto")
    assert r["checksum_valid"] is False
    assert r["failing_fields"] == ["dv1"]
    assert r["dvs"]["dv1"] == {"given": "9", "expected": "4",
                               "valid": False}
    assert all(r["dvs"][k]["valid"] for k in
               ("dv2", "dv3", "dv_geral"))


# ------------------------------------------------------------ the fator
def test_fator_discontinuity_dates():
    """fator 1000 maps to TWO candidates: cycle 1 2000-07-03 (base
    1997-10-07 + 1000) and cycle 2 2025-02-22 (the restart day). The
    tool never picks one with a wall clock."""
    r = digitkit.checkdigit(mode="check", value=VEC_A, scheme="boleto")
    due = r["decoded"]["due_date_candidates"]
    assert due == [{"cycle": 1, "due": "2000-07-03"},
                   {"cycle": 2, "due": "2025-02-22"}]


def test_fator_below_1000_refused_by_name():
    bad = VEC_A[:33] + "0999" + VEC_A[37:]
    r = digitkit.checkdigit(mode="check", value=bad, scheme="boleto")
    assert r["decoded"]["due_date_candidates"] == []
    assert "below 1000" in r["decoded"]["fator_note"]


def test_nine_nine_nine_cycle_boundary():
    """fator 9999 = 2025-02-21 (cycle 1 end) and +9000 = 2049-10-13."""
    body = "001" + "9" + "9999" + "0000000000" + "0" * 25
    linha = _linha("001", "9", "9999", "0000000000", "0" * 25)
    r = digitkit.checkdigit(mode="check", value=linha, scheme="boleto")
    assert [c["due"] for c in r["decoded"]["due_date_candidates"]] == \
        ["2025-02-21", "2049-10-13"]


# ------------------------------------------------------------ generate
def test_generate_matches_hand_trace():
    body = "001" + "9" + "1000" + "0000015000" + \
        "1234500000000000000000001"
    g = digitkit.checkdigit(mode="generate", value=body, scheme="boleto")
    assert g["value"] == VEC_A
    assert g["barcode44"] == BAR_A
    assert g["value_printed"].startswith("00191.23454 00000.000000 "
                                         "00000.000018 1 ")


def test_generate_44_digit_barcode_refused_by_name():
    with pytest.raises(digitkit.DigitError) as e:
        digitkit.checkdigit(mode="generate", value=BAR_A, scheme="boleto")
    assert "full barcode" in str(e.value)


def test_generate_fator_floor_refused():
    body = "001" + "9" + "0999" + "0000000100" + "0" * 25
    with pytest.raises(digitkit.DigitError) as e:
        digitkit.checkdigit(mode="generate", value=body, scheme="boleto")
    assert "below 1000" in str(e.value)


def test_48_digit_refused_by_name():
    with pytest.raises(digitkit.DigitError) as e:
        digitkit.checkdigit(mode="check", value="0" + VEC_A,
                            scheme="boleto")
    msg = str(e.value)
    assert "consumo" in msg and "Banrisul" in msg


# ----------------------------------------------------- auto / repair / scan
def test_autodetect_no_scheme():
    r = digitkit.checkdigit(mode="check", value=VEC_A)
    assert r["detected"] is True and r["unique"] is True
    assert r["valid_candidates"] == ["boleto"]


def test_repair_single_edit_finds_original():
    bad = VEC_A[:31] + "9" + VEC_A[32:]     # dv3 corrupted 8 -> 9
    r = digitkit.checkdigit(mode="repair", value=bad, scheme="boleto")
    assert any(c["value"] == VEC_A for c in r["candidates"])


def test_scan_finds_fully_dot_separated_line():
    """A linha printed dots-only inside ONE token is found; the ticket
    form with spaces arrives as separate fields and needs check (a
    named limit, said in the module docstring)."""
    dotted = ".".join((VEC_A[0:5], VEC_A[5:10], VEC_A[10:15],
                       VEC_A[15:21], VEC_A[21:26], VEC_A[26:32],
                       VEC_A[32], VEC_A[33:47]))
    r = digitkit.checkdigit(mode="scan", text="pague ja: " + dotted +
                            " obrigado")
    hits = [x for x in r["found"] if any(
        c["scheme"] == "boleto" for c in x["results"])]
    assert len(hits) == 1
    assert hits[0]["results"][0]["checksum_valid"] is True


# -------------------------------------------------------------- API + laws
def test_api_200_and_deterministic():
    body = {"mode": "check", "value": VEC_A, "scheme": "boleto"}
    r1 = client.post("/api/v1/id/checkdigit", json=body)
    r2 = client.post("/api/v1/id/checkdigit", json=body)
    assert r1.status_code == 200
    assert r1.json()["decoded"]["valor_decimal"] == "150.00"
    assert r1.json()["sha256"] == r2.json()["sha256"]


def test_api_bad_400_names_field():
    r = client.post("/api/v1/id/checkdigit",
                    json={"mode": "check", "value": "0" * 48,
                          "scheme": "boleto"})
    assert r.status_code == 400
    detail = json.dumps(r.json())
    assert "consumo" in detail


def test_scheme_list_closed_mentions_boleto():
    with pytest.raises(digitkit.DigitError) as e:
        digitkit.checkdigit(mode="check", value=VEC_A, scheme="boletoo")
    assert "boleto" in str(e.value)
