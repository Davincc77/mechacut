"""Bundle 42 — math/calc (calckit). Le socle du bench v12 et du futur
catalogue F4. Attendus calculés à la main OU par Fraction (oracle
indépendant de Decimal) : 7834×9217 = 7834×9000+7834×217 =
70 506 000+1 699 978 = 72 205 978."""
import sys
sys.path.insert(0, ".")
import calckit
import main
import pytest
from fastapi.testclient import TestClient
from fractions import Fraction as F

client = TestClient(main.app)


def val(expr, digits=None):
    return calckit.calc(expr, digits)["value"]


def test_calculs_publics_calculés_main():
    assert val("7834*9217") == "72205978"
    assert val("1000/17", 4) == "58.8235"
    assert val("248.40*100/15", 2) == "1656.00"   # les zéros TIENTENT
    assert val("34.2*8.75/7.5", 3) == "39.900"
    assert val("217.8/(2+47/60)", 2) == "78.25"
    assert val("987654321%7919") == "4560"


def test_le_piège_float_est_mort():
    assert val("0.1+0.2") == "0.3"
    # 1.005 en binaire float, c'est 1.00499999… → round float = 1.0 ;
    # en Decimal source-tel-quelle, HALF_UP honnête = 1.01
    assert val("round(1.005, 2)") == "1.01"


def test_oracle_fraction_sur_la_chaîne():
    # compound : oracle Fraction indépendant, recalculé dans le test
    v = F("1234.56") * F(100417, 100000) ** 19
    from decimal import Decimal, ROUND_HALF_UP
    exp = str((Decimal(v.numerator) / Decimal(v.denominator))
              .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    assert val("1234.56*1.00417**19", 2) == exp == "1336.13"
    assert val("sqrt(2)").startswith("1.41421356237309504880")


def test_refus_nommés_la_langue_est_fermée():
    for bad, needle in [("__import__('os')", "closed language"),
                        ("len(2)", "closed language"),
                        ("x*2", "closed language"),
                        ("1/0", "division by zero"),
                        ("sqrt(-4)", "negative"),
                        ("2**999", "exponent"),
                        ("(1,2)", "closed"),
                        ("0x10", "closed language")]:
        with pytest.raises(calckit.CalcError) as e:
            calckit.calc(bad)
        assert needle in str(e.value), (bad, str(e.value))


def test_digitsbornes_et_expr_vide():
    with pytest.raises(calckit.CalcError):
        calckit.calc("1+1", digits=99)
    with pytest.raises(calckit.CalcError):
        calckit.calc("")
    with pytest.raises(calckit.CalcError):
        calckit.calc("9" * 1200)


def test_endpoint_stable_deux_appels_mêmes_octets():
    body = {"expr": "2349.77*1.07*1.04*0.89", "digits": 2}
    r1 = client.post("/api/v1/math/calc", json=body)
    r2 = client.post("/api/v1/math/calc", json=body)
    assert r1.status_code == r2.status_code == 200
    assert r1.content == r2.content
    d = r1.json()
    assert d["value"] == "2327.19" and d["rounded_to"] == 2
    assert d["sha256"] == main.canon(
        {k: v for k, v in d.items() if k != "sha256"})
    bad = client.post("/api/v1/math/calc", json={"expr": "open('x')"})
    assert bad.status_code == 400 and "closed" in bad.text


def test_math_calc_est_dans_le_catalogue():
    names = [t["name"] for t in client.post(
        "/mcp", json={"jsonrpc": "2.0", "id": 1,
                      "method": "tools/list"}).json()["result"]["tools"]]
    assert "math_calc" in names
