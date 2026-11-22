"""scalekit /table/scale — bundle43. Attentes CALCULEES MAIN (fractions
de poche), jamais recopiees du module. Verbatim de reference : r/ChatGPT
1sy9p5v (400 g -> 1/3), r/AskReddit 1wyx6ke (pincees), l'affaire NYT
Cooking AI (5 oeufs -> « 3 » sans explication).
Notations dues au public : cuilleres/tasses/onces en FRACTIONS (les jeux
publies sont en fractions), metric en decimales, multiplier en fraction
impropre + mixte + decimale."""
import json
import pytest
import scalekit
from scalekit import scale, ScaleError


def S(items, **kw):
    return scale(items, **kw)


FL = {"name": "flour", "qty": "400", "unit": "g"}

# ---- le multiplicateur est dit UNE fois -------------------------------


def test_multiplier_from_servings_is_reduced_and_named():
    # main: 15/6 = 5/2 = 2.5
    r = S([FL], servings_from=6, servings_to=15)
    assert r["multiplier"]["fraction"] == "5/2"
    assert r["multiplier"]["mixed"] == "2 1/2"
    assert r["multiplier"]["decimal"] == "2.5"
    assert r["multiplier"]["source"] == "servings 6 -> 15"


def test_factor_and_servings_together_refused():
    with pytest.raises(ScaleError, match="UNE"):
        S([FL], factor="2", servings_from=6, servings_to=15)


def test_factor_string_exact():
    r = S([FL], factor="1/3")
    assert r["multiplier"]["fraction"] == "1/3"
    assert r["multiplier"]["mixed"] == "1/3"


# ---- 1/3 de 400 g : l'exact N'EST PAS 133 ------------------------------


def test_third_of_400g_states_three_answers():
    # main: 400/3 = 133 1/3 ; 133.33 >= 100 -> palier 5 g ;
    #       133.333/5 = 26.666 -> half-up 27 -> 135 g
    #       ecart (135-400/3)/(400/3) = (5/3)/(400/3) = 5/400 -> 1.25 %
    r = S([FL], factor="1/3")
    it = r["items"][0]
    assert it["exact"]["fraction"] == "133 1/3 g"
    assert it["exact"]["decimal"] == "133.3333 g"
    assert it["measurable"]["value"] == "135 g"
    assert it["measurable"]["rule"] == "nearest 5 g, half-up"
    assert it["rounding_delta"] == "1.25%"


def test_01_times_3_is_03_not_float_mud():
    r = S([{"name": "saffron", "qty": "0.1", "unit": "g"}], factor="3")
    it = r["items"][0]
    assert it["exact"]["decimal"] == "0.3 g"       # main: 3/10
    assert it["measurable"]["value"] == "0.3 g"    # <10 g -> palier 0.1
    assert it["rounding_delta"] == "0%"


def test_whole_number_scaling_is_exact_and_zero_delta():
    r = S([FL], factor="2")
    it = r["items"][0]
    assert it["exact"]["fraction"] == "800 g"
    assert it["measurable"]["value"] == "800 g"
    assert it["rounding_delta"] == "0%"


# ---- l'affaire NYT : 5 oeufs / 2 --------------------------------------


def test_five_eggs_halved_is_stated_never_clipped():
    # main: 5 * 1/2 = 5/2 = 2.5 ; palier piece = 1 ; half-up -> 3 ;
    #       ecart (3-2.5)/2.5 = 20 % ; poids 2.5 * 50 g = 125 g
    r = S([{"name": "eggs", "qty": "5", "unit": "piece", "class": "egg"}],
          factor="1/2")
    it = r["items"][0]
    assert it["exact"]["fraction"] == "2 1/2 piece"
    assert it["measurable"]["value"] == "3 piece"
    assert it["rounding_delta"] == "20%"
    assert "125 g" in it["weight_alternative"]
    assert "50 g shelled" in it["weight_alternative"]


# ---- classes et paliers publies ----------------------------------------


def test_salt_uses_eighth_teaspoon_step():
    # main: 1/4 * 5/2 = 5/8 = 0.625 tsp ; palier salt = 1/8 ;
    #       5/8 pile multiple de 1/8 -> exact, delta 0
    r = S([{"name": "salt", "qty": "1/4", "unit": "tsp", "class": "salt"}],
          factor="2.5")
    it = r["items"][0]
    assert it["exact"]["fraction"] == "5/8 tsp"
    assert it["measurable"]["value"] == "5/8 tsp"
    assert it["measurable"]["rule"] == "nearest 1/8 tsp, half-up"
    assert it["rounding_delta"] == "0%"
    assert "never invents" in it["note"]


def test_base_tsp_step_is_quarter():
    # main: 1 tsp base x 0.3 = 0.3 ; palier 1/4 -> 0.3/0.25 = 1.2 ->
    #       half-up 1 -> 1/4 tsp ; ecart (1/4-3/10)/(3/10) =
    #       (-1/20)/(3/10) = -1/6 = -16.6667 %
    r = S([{"name": "vanilla", "qty": "1", "unit": "tsp"}], factor="0.3")
    it = r["items"][0]
    assert it["exact"]["fraction"] == "3/10 tsp"
    assert it["measurable"]["value"] == "1/4 tsp"
    assert it["measurable"]["rule"] == "nearest 1/4 tsp, half-up"
    assert it["rounding_delta"] == "-16.6667%"


def test_below_smallest_step_raises_and_flags_never_zero():
    # main: 1/8 x 1/3 = 1/24 ; palier 1/8 ; 1/24 < 1/16 -> down-0 ->
    #       REMONTE a 1/8, flag ; ecart (1/8-1/24)/(1/24) = 2 -> 200 %
    r = S([{"name": "paprika", "qty": "1/8", "unit": "tsp",
            "class": "spice"}], factor="1/3")
    it = r["items"][0]
    assert it["measurable"]["value"] == "1/8 tsp"
    assert "flag" in it and "raised" in it["flag"]
    assert "double-batch" in it["flag"]
    assert it["rounding_delta"] == "200%"


def test_cup_and_ml_steps():
    # main: 3/4 cup x 1/3 = 1/4 cup exact ; palier 1/4 -> 1/4
    #       250 ml x 2 = 500 ml ; >=100 -> palier 5 -> 500
    r = S([{"name": "rice", "qty": "3/4", "unit": "cup"}], factor="1/3")
    assert r["items"][0]["measurable"]["value"] == "1/4 cup"
    r2 = S([{"name": "milk", "qty": "250", "unit": "ml"}], factor="2")
    assert r2["items"][0]["measurable"]["value"] == "500 ml"
    assert r2["items"][0]["measurable"]["rule"] == "nearest 5 ml, half-up"


# ---- power : le sub-lineaire est DEMANDE, pas invente ------------------


def test_power_sqrt_is_exact_on_clean_numbers():
    # main: 9 ** 1/2 = 3 ; 2 tbsp x 3 = 6 tbsp ; palier 1/2 -> 6
    r = S([{"name": "butter", "qty": "2", "unit": "tbsp"}],
          factor="9", power_default="1/2")
    it = r["items"][0]
    assert it["power"] == "factor 9 ** power 1/2 = 3"
    assert it["exact"]["fraction"] == "6 tbsp"
    assert it["measurable"]["value"] == "6 tbsp"


def test_power_decimal_exponent_declared():
    # main (calculette): 4 ** 3/4 = sqrt(8) = 2.828427... ;
    # 1 tsp x 2.828427 ; palier leavening 1/8 : 2.828427/0.125 =
    # 22.6274 -> half-up 23 -> 23/8 = 2 7/8 tsp ; decimale declaree
    # 4 places -> 2.8284
    r = S([{"name": "baking powder", "qty": "1", "unit": "tsp",
            "class": "leavening"}], factor="4", power_default="0.75")
    it = r["items"][0]
    assert it["exact"]["decimal"] == "2.8284 tsp"
    assert it["measurable"]["value"] == "2 7/8 tsp"


def test_power_per_item_overrides():
    r = S([{"name": "salt", "qty": "1", "unit": "tsp", "class": "salt",
            "power": "1/2"}], factor="9")
    assert r["items"][0]["power"] == "factor 9 ** power 1/2 = 3"
    assert r["items"][0]["measurable"]["value"] == "3 tsp"


# ---- refus NOMMES ------------------------------------------------------


def test_pinch_refused_by_name_with_the_salt_story():
    with pytest.raises(ScaleError, match="12,5 lb"):
        S([{"name": "salt", "qty": "1", "unit": "pinch"}], factor="500")


def test_float_input_refused():
    with pytest.raises(ScaleError, match="flottant"):
        S([{"name": "x", "qty": 700.0, "unit": "g"}], factor="2")


def test_factor_zero_refused():
    with pytest.raises(ScaleError, match="positif"):
        S([FL], factor="0")


def test_negative_factor_refused_by_sign():
    with pytest.raises(ScaleError, match="signe"):
        S([FL], factor="-2")


def test_unknown_class_refused_with_closed_table():
    with pytest.raises(ScaleError, match="table fermee"):
        S([{"name": "sauce", "qty": "1", "unit": "cup",
            "class": "sauce"}], factor="2")


def test_unknown_unit_refused_with_closed_table():
    with pytest.raises(ScaleError, match="unite inconnue"):
        S([{"name": "mystery", "qty": "1", "unit": "hand"}], factor="2")


def test_servings_zero_refused():
    with pytest.raises(ScaleError, match="positif"):
        S([FL], servings_from=0, servings_to=4)


def test_giant_number_refused():
    with pytest.raises(ScaleError, match="chiffres"):
        S([{"name": "x", "qty": "1234567890123", "unit": "g"}], factor="2")


def test_too_many_items_refused():
    with pytest.raises(ScaleError, match="max 200"):
        S([FL] * 201, factor="2")


def test_garbage_qty_named():
    with pytest.raises(ScaleError, match="ni un nombre"):
        S([{"name": "flour", "qty": "a handful", "unit": "g"}], factor="2")


# ---- contrat global ----------------------------------------------------


def test_rules_block_is_shipped_in_the_response():
    r = S([FL], factor="2")
    assert r["rules"]["table"] == "kitchen-steps-v1"
    assert r["rules"]["steps"]["tsp"] == \
        "base 1/4 / salt-spice-leavening-yeast 1/8"
    assert len(r["scope_notes"]) == 3
    assert "pan size" in r["scope_notes"][0]


def test_determinism_same_bytes_twice():
    a = json.dumps(S([FL, {"name": "salt", "qty": "1/4", "unit": "tsp",
                           "class": "salt"}],
                     servings_from=6, servings_to=15), sort_keys=True)
    b = json.dumps(S([FL, {"name": "salt", "qty": "1/4", "unit": "tsp",
                           "class": "salt"}],
                     servings_from=6, servings_to=15), sort_keys=True)
    assert a == b


def test_reduced_input_fraction_is_echoed_reduced():
    # main: 2/6 = 1/3 ; 1/3 x 3 = 1 g pile
    r = S([{"name": "flour", "qty": "2/6", "unit": "g"}], factor="3")
    it = r["items"][0]
    assert it["input"] == "1/3 g"
    assert it["exact"]["fraction"] == "1 g"
