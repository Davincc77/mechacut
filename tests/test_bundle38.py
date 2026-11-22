"""Bundle 38 — csv/money_columns (moneykit). Le cas ETL-D exact :
« Claude hallucinating decimal points in financial CSVs ». Attentes
calculées à la main : même chaîne « 1.234 » = 1.234 (preuve US) ET
1234 (preuve EU) selon la colonne — c'EST le produit."""
import sys
sys.path.insert(0, ".")
import main
import moneykit
import pytest
from fastapi.testclient import TestClient

client = TestClient(main.app)


def col0(csv_text, **kw):
    r = moneykit.analyze(csv_text, **kw)
    return r, r["columns"][0]


def test_same_string_opposite_values_by_proof():
    _, us = col0("amount\n1,234.56\n1.234\n2,000.00")
    assert us["style_convention"] == "us"
    assert us["resolved"][0]["value"] == "1.234"
    assert "proven by 2 unambiguous values" in us["resolved"][0]["why"]
    _, eu = col0("montant\n1.234,56\n2,50\n1.234")
    assert eu["style_convention"] == "eu"
    assert eu["resolved"][0]["value"] == "1234"
    # le piège chiffré : mille fois d'écart entre les deux lectures
    assert us["max_reading_gap_x"] == 999.0


def test_contradiction_refuses_instead_of_coinflip():
    r, c = col0("x\n1,234.56\n1.234,56\n1.234")
    assert c["style_convention"] == "CONTRADICTORY"
    assert c["ambiguous_refused"] == 1
    ref = c["refused"][0]
    assert ref["readings"] == {"decimal": "1.234", "group": "1234"}
    assert "BOTH" in ref["why"]
    assert r["summary"]["verdict"].startswith("needs_human")


def test_no_evidence_refuses_too():
    _, c = col0("x\n1.234\n2.345")
    assert c["ambiguous_refused"] == 2
    assert c["ambiguous_resolved"] == 0


def test_real_two_column_table_untouched():
    r, _ = col0("qty,price\n3,1.50\n2,4.25")
    assert len(r["columns"]) == 2 and r["shape_note"] is None
    by = {c["column"]: c for c in r["columns"]}
    assert by["qty"]["unambiguous"] == 2
    assert by["price"]["unambiguous"] == 2


def test_currency_symbols_and_explicit_columns():
    _, c = col0("nom;prix\nclou;$1,234.56\nvis;$1.234\nplan;$2,000.00",
                columns=["prix"], delimiter=";")
    assert c["looks_like_money"] is True
    assert c["style_convention"] == "us"
    assert c["resolved"][0]["value"] == "1.234"


def test_refus_nommés():
    # ragged rows : la cellule manquante est comptée vide, pas inventée
    # (délimiteur forcé — sans lui, un fichier 2 lignes sur 3 avec
    # virgule n'a pas de délimiteur RÉCURRENT, et le sniffer dit
    # « une colonne », honnêtement)
    r = moneykit.analyze("a,b\nx\n1,2", delimiter=",")
    by = {c["column"]: c for c in r["columns"]}
    assert by["a"]["rows_empty"] + by["b"]["rows_empty"] >= 1
    with pytest.raises(moneykit.MoneyError):
        moneykit.analyze("")
    with pytest.raises(moneykit.MoneyError):
        moneykit.analyze("ville\nparis\nlyon")   # aucune colonne numérique
    with pytest.raises(moneykit.MoneyError) as e:
        moneykit.analyze("a,b\n1,2", columns=["zz"])
    assert "available" in str(e.value)


def test_endpoint_et_canon():
    body = {"csv": "facture\n1,234.56\n1.234\n2,000.00\n42.50"}
    r1 = client.post("/api/v1/csv/money_columns", json=body).json()
    r2 = client.post("/api/v1/csv/money_columns", json=body).json()
    assert r1 == r2
    assert r1["columns"][0]["resolved"][0]["value"] == "1.234"
    assert r1["sha256"] == main.canon(
        {k: v for k, v in r1.items() if k != "sha256"})
    bad = client.post("/api/v1/csv/money_columns", json={"csv": "ville\nx"})
    assert bad.status_code == 400 and "numeric" in bad.text
