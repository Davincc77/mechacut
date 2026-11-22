"""bundle44 — F4 palier 1 : le catalogue de formules.
ORACLE : chaque attendu est CALCULÉ À LA MAIN ici, jamais lu du
registre (règle des deux golds). 12 enregistrements, zéro constante."""
import pytest

import formulakit as fk


def r(name, **args):
    return fk.run_formula(name, args)


# —percent_up_down : 240 +15 % = 276 ; le trou du aller-retour est
#  p²/100 = 2,25 % EXACT (main : 276×0,85 = 234,6 ; (240−234,6)/240).
def test_percent():
    out = r("percent_up_down", base=240, percent=15, direction="up")
    assert out["result"] == "276.00"
    assert out["roundtrip_after_inverse_pct"] == "2.25"
    orig = r("percent_up_down", mode="original", final=276, percent=15,
             direction="up")
    assert orig["result"] == "240.00"          # 276 ÷ 1,15 = 240


def test_rule_of_three():
    # main : 4,50 × 7 ÷ 3 = 31,5 ÷ 3 = 10,50
    assert r("rule_of_three", a=3, b="4.50", c=7)["result"] == "10.50"


# —speed : main : 120÷2,5=48 ; 48×2,5=120 ; 120÷48=2,5.
def test_speed_three_targets():
    assert r("speed", solve_for="speed", distance=120,
             time_hours=2.5)["result"] == "48.00"
    assert r("speed", solve_for="distance", speed=48,
             time_hours=2.5)["result"] == "120.00"
    out = r("speed", solve_for="time_hours", distance=120, speed=48)
    assert out["result"] == "2.50" and out["units"] == "h"


def test_fuel_both_senses():
    # main : 5×100÷60 = 8,333… → 8,33 ; 60÷5 = 12.
    out = r("fuel_l100", litres=5, km=60)
    assert out["result_l_per_100km"] == "8.33"
    assert out["result_km_per_l"] == "12.00"


def test_pace():
    # main : 52,5 ÷ 10 = 5,25 min ; 0,25 min = 15 s → 5:15.
    out = r("average_pace", total_minutes=52.5, km=10)
    assert out["result_min_per_km"] == "5.25"
    assert out["result_mmss"] == "5:15"


# —dilution : le bug que le vecteur-main a péché : solving c1 doit
# DIVISER par v1 (C1 = C2V2÷V1), pas se réutiliser. main :
# v1 = 20×50÷100 = 10 ; c1 = 20×50÷10 = 100 ; v2 = 100×10÷20 = 50.
def test_dilution_all_targets():
    assert r("dilution_c1v1", solve_for="v1", c1=100, c2=20,
             v2=50)["result"] == "10.0000"
    assert r("dilution_c1v1", solve_for="c1", c2=20, v1=10,
             v2=50)["result"] == "100.0000"
    assert r("dilution_c1v1", solve_for="v2", c1=100, v1=10,
             c2=20)["result"] == "50.0000"
    assert r("dilution_c1v1", solve_for="c2", c1=100, v1=10,
             v2=50)["result"] == "20.0000"


def test_dosage_carries_scope_note():
    out = r("dosage_mg_kg", mg_per_kg="2.5", weight_kg=8)
    assert out["result"] == "20.000"           # main : 8 × 2,5 = 20
    assert "professional" in out["scope_note"]


# —baker : main : 700÷1000×100 = 70 ; 500×0,70 = 350 ; 350÷0,70 = 500.
def test_bakers_three_modes():
    assert r("bakers_hydration", water_g=700,
             flour_g=1000)["result_pct"] == "70.00"
    assert r("bakers_hydration", mode="water_for", flour_g=500,
             hydration_pct=70)["result_g"] == "350.00"
    assert r("bakers_hydration", mode="flour_for", water_g=350,
             hydration_pct=70)["result_g"] == "500.00"


def test_naegle_two_paths_agree():
    # main : 2026-01-01 + 280 j : janv. reste 30, +28+31+30+31+30+31+31
    # +30 = 272 → 8 oct. ; +7j = 8 janv. −3m = 8 oct. 2025 +1a =
    # 8 oct. 2026. Les DEUX chemins concordent → pas de note d'écart.
    out = r("naegle_due_date", lmp="2026-01-01")
    assert out["result"] == "2026-10-08"
    assert "alternative_result" not in out
    assert "clinical" in out["scope_note"]


def test_area_rational_shapes_and_circle_refused():
    assert r("area_shapes", shape="rectangle", length=5,
             width=3.5)["result"] == "17.5000"
    assert r("area_shapes", shape="triangle", base=8,
             height=5)["result"] == "20.0000"
    assert r("area_shapes", shape="trapezoid", parallel_a=4,
             parallel_b=6, height=3)["result"] == "15.0000"
    with pytest.raises(KeyError) as e:
        r("area_shapes", shape="circle", radius=7)
    assert "π" in str(e.value)                  # nommé, pas ignoré


def test_volume_box():
    assert r("volume_box", length=2, width=3, height=4)["result"] \
        == "24.0000"


def test_unknown_formula_names_the_closed_set():
    with pytest.raises(KeyError) as e:
        r("quadratic_formula", a=1)
    assert "rule_of_three" in str(e.value)      # l'enum fermée entière


def test_missing_arg_is_named():
    with pytest.raises(KeyError) as e:
        r("rule_of_three", a=3, b=4.50)         # c manque
    assert str(e.value) == "'c'"


def test_no_duplicate_of_money_discount():
    # question 5 anti-doublon, écrite dans le code : les remises en
    # chaîne SUR PRIX appartiennent à money/discount — le catalogue
    # pointe, il ne reimplemente pas.
    assert any("money/discount" in k for k in fk.CROSS_REFS)
    idx = fk.formula_index()
    assert not any("discount" in f["name"] for f in idx["formulas"])


def test_catalog_is_twelve_and_pure_rational():
    assert len(fk.CATALOG) == 12
    # palier 1 : AUCUNE constante dans les sources rendues
    for f in fk.formula_index()["formulas"]:
        assert "π" not in f["formula"] or "Euclid" in f["source"]


def test_determinism_same_in_same_out():
    a = r("rule_of_three", a=3, b="4.50", c=7)
    b = r("rule_of_three", a=3, b="4.50", c=7)
    assert a == b
