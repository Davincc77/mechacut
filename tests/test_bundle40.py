"""Bundle 40 — money/discount (discountkit). Attendus calculés à la main :
19.99 ×0.70 =13.993 ×0.80 =11.1944 → 11.19 ; effectif 44 % ; l'ordre
-30|-5 sur 83.40 = 53.38 vs -5|-30 = 54.88 (écart 1.50) ; B2P1 3@19.99
paie 2 → 39.98."""
import sys
sys.path.insert(0, ".")
import discountkit as dk
import main
import pytest
from fastapi.testclient import TestClient

client = TestClient(main.app)
P30 = {"type": "percent", "value": "30"}
P20 = {"type": "percent", "value": "20"}


def test_le_mensonge_des_soldes():
    r = dk.discount_chain("19.99", [P30, P20])
    assert r["final_total"] == "11.19"
    assert r["effective_discount_pct"] == "44.00"
    assert r["naive_sum_pct"] == "50.00"
    assert r["percent_lie_delta"] == "6.00"
    assert r["order_matters"] is False      # que des % : l'ordre ne peut pas


def test_ordre_fixe_contre_percent():
    r = dk.discount_chain("83.40", [P30, {"type": "fixed", "value": "5"}])
    assert r["final_total"] == "53.38"
    assert r["order_matters"] is True
    assert r["order_spread"] == "1.50"      # 54.88 - 53.38, fait main
    assert r["best_step_order_for_you"] == [1, 2]


def test_buy_two_pay_one():
    r = dk.discount_chain("19.99", [{"type": "buy2pay1"}], qty=3)
    assert r["gross_total"] == "59.97"
    assert r["final_total"] == "39.98"
    assert r["effective_discount_pct"] == "33.33"
    with pytest.raises(dk.DiscountError):
        dk.discount_chain("19.99", [{"type": "buy2pay1"}], qty=1)


def test_sous_zero_refuse_pas_coupe():
    with pytest.raises(dk.DiscountError) as e:
        dk.discount_chain("4.00", [{"type": "fixed", "value": "5"}])
    assert "below zero" in str(e.value)


def test_per_unit_fixed():
    r = dk.discount_chain("10.00", [{"type": "fixed", "value": "2",
                                     "per_unit": True}], qty=4)
    assert r["gross_total"] == "40.00"
    assert r["final_total"] == "32.00"


def test_regles_fermees():
    for bad in ({"type": "vat"}, {"type": "percent", "value": "150"},
                {"type": "percent", "value": "0"}):
        with pytest.raises(dk.DiscountError):
            dk.discount_chain("10.00", [bad])


def test_endpoint_stable_et_canon():
    body = {"price": "89.90", "currency": "EUR",
            "steps": [P30, P20]}
    r1 = client.post("/api/v1/money/discount", json=body).json()
    r2 = client.post("/api/v1/money/discount", json=body).json()
    assert r1 == r2
    assert r1["final_total"] == "50.34"
    assert r1["sha256"] == main.canon(
        {k: v for k, v in r1.items() if k != "sha256"})
    bad = client.post("/api/v1/money/discount",
                      json={"price": "10", "steps": []})
    assert bad.status_code == 400 and "non-empty" in bad.text


def test_ledger_naque_pas_de_notation_exponentielle():
    """Decimal.normalize() rendait « 3E+1 » dans le ledger (22-11,
    pris en flag pendant le bench v10). Les champs affichés pour un
    HUMAIN sont en notation ordinaire, toujours."""
    r = dk.discount_chain("89.90", [P30, P20])
    for step in r["ledger"]:
        assert "E" not in step["how"], step["how"]
    r2 = dk.discount_chain("100", [{"type": "fixed", "value": "20"}])
    assert r2["ledger"][0]["how"] == "- 20"
