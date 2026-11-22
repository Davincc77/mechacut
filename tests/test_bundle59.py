"""Bundle 59 — P5 pêché par la sonde de contrat (22-11) : table_pivot
somme en Decimal exact. Le gold ne plie pas : c'est le produit qui
avait tort (118.71000000000001 dans une cellule d'argent)."""
from tables import table_pivot


def _rows(*vals):
    return [{"g": "a", "k": str(i), "v": v} for i, v in enumerate(vals)]


def test_sum_no_float_rot():
    rows = [{"g": "a", "k": "c", "v": v} for v in (0.1, 0.2, 118.41)]
    out = table_pivot(rows, "g", "k", "v")
    # somme exacte : 118.71 — la version float rendait 118.71000000000001
    assert out[0]["c"] == 118.71


def test_sum_ints_stay_int():
    rows = [{"g": "a", "k": "c", "v": v} for v in (1, 2, 3)]
    out = table_pivot(rows, "g", "k", "v")
    v = out[0]["c"]
    assert v == 6 and isinstance(v, int)


def test_sum_money_strings():
    rows = [{"g": "a", "k": "c", "v": x} for x in
            ("118.71", "0.30", "6.41", "-46.71")]
    out = table_pivot(rows, "g", "k", "v")
    assert out[0]["c"] == "78.71"


def test_trailing_zero_is_contract_B010():
    # Le gold de la sonde de contrat (csk B010) : 1.10 + 2.20 = "3.30".
    # La zéro finale est une AFFIRMATION de précision, pas un ornement —
    # un nombre entré en string ressort en string.
    rows = [{"g": "a", "k": "c", "v": v} for v in ("1.10", "2.20")]
    out = table_pivot(rows, "g", "k", "v")
    assert out[0]["c"] == "3.30"
    rows = [{"g": "a", "k": "c", "v": v} for v in ("0.1", "0.2")]
    assert table_pivot(rows, "g", "k", "v")[0]["c"] == "0.3"


def test_mean_exact_division():
    rows = [{"g": "a", "k": "x", "v": v} for v in (0.1, 0.2)]
    out = table_pivot(rows, "g", "k", "v", agg="mean")
    assert out[0]["x"] == 0.15
