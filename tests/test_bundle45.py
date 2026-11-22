"""bundle45 — /intent/reflect : le miroir de compréhension.
Garde suprême : le mirour ne peut PAS diverger du catalogue — le
résultat rendu est LITTÉRALEMENT celui de run_formula, testé à
l'égalité stricte sur plusieurs formules."""
import pytest

import formulakit as fk
import reflectkit as rk


def test_mirror_result_is_the_catalog_result():
    for name, args in [
            ("rule_of_three", {"a": 3, "b": "4.50", "c": 7}),
            ("share_pct", {"part": 184, "whole": 460}),
            ("fuel_l100", {"litres": 5, "km": 60}),
            ("naegle_due_date", {"lmp": "2026-01-01"})]:
        direct = fk.run_formula(name, args)
        mirror = rk.run_reflect({"formula": name, "args": args})
        for k, v in direct.items():
            assert mirror[k] == v, (name, k)


def test_reading_check_quotes_the_substitution():
    out = rk.run_reflect({"formula": "rule_of_three",
                          "args": {"a": 3, "b": "4.50", "c": 7}})
    assert out["substitution"] in out["reading_check"]
    assert "10.50" in out["result"]           # main : 4,5×7÷3 = 10,50


def test_unknown_formula_gets_the_closed_list():
    with pytest.raises(rk.Unreadable) as e:
        rk.run_reflect({"formula": "black_scholes", "args": {}})
    assert e.value.field == "formula"
    assert "rule_of_three" in e.value.expected   # palier STEM en file,
    # pas encore dans le set fermé — nommé comme inconnu, pas deviné


def test_missing_args_refuse_by_name_with_record_args():
    with pytest.raises(rk.Unreadable) as e:
        rk.run_reflect({"formula": "rule_of_three",
                        "args": {"a": 3, "b": 4.5}})
    assert e.value.field == "args"
    assert "c" in e.value.message
    assert e.value.expected == fk.CATALOG["rule_of_three"]["args"]


def test_honesty_fields_always_present():
    out = rk.run_reflect({"formula": "speed",
                          "args": {"solve_for": "speed", "distance": 120,
                                   "time_hours": 2.5}})
    assert "ne connaît pas l'histoire" in out["not_claimed"]
    assert out["source"] == fk.CATALOG["speed"]["source"]
    assert out["formula_ref"] == fk.CATALOG["speed"]["formula"]


def test_reflect_requires_a_formula_name():
    with pytest.raises(rk.Unreadable) as e:
        rk.run_reflect({"args": {"a": 1}})
    assert e.value.field == "formula"
