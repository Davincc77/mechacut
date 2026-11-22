# -*- coding: utf-8 -*-
"""bundle66 — /money/unitprice : le dénominateur nommé (shrinkflation,
2-for-$7, étiquette fausse, « 1 lb 4 oz »).

ORACLES (calculés MAIN/Fraction indépendante, jamais recopiés du module) :

1. Gatorade publié (smartdollarplace 4-nov-2026) : 32 → 28 fl oz au
   même prix. Perte de produit = 4/32 = 1/8 → « 12.5000 », exact 25/2
   (%). Hausse par once = 4/28 = 1/7 → « 14.2857 », exact 100/7.
   DEUX DÉNOMINATEURS : 12,5 divise par 32, 14,2857 divise par 28.
   L'affiche qui dit « -12,5 % » ment par moitié de chiffre.
2. Hershey (file précédente) : 29 → 23,9 oz : (29−23,9)/29 = 5,1/29 =
   51/290 → 17.5862 (510/29) ; (29/23,9)−1 = 51/239 → 21.3389
   (5100/239).
3. TheWhyWeProject 21-nov-2026 : 10 portions → 9 : perte 1/10 =
   10.0000 (10/1) ; hausse 1/9 → 11.1111 (100/9). Famille COUNT :
   la portion n'est pas un gramme.
4. Métrique FR/PT : 500 g → 400 g : 1/5 → 20.0000 (20/1) ; 500/400−1
   = 1/4 → 25.0000 (25/1). Le ratio est invariant d'unité : « +25 %
   par gramme » EST « +25 % au kilo ».
5. Upsizing 12 → 14 oz : produit GAGNE 1/6 (display -16.6667, exact
   -50/3 — le signe dit « pas une perte ») ; prix/unité tombe de 1/7 →
   -14.2857 (-100/7).
6. Taille + prix bougent (32→28 à 5.00→5.50) : (5,5/28)/(5/32)−1 =
   44/35−1 = 9/35 → 25.7143 (180/7).
7. Olive oil publié : 8.99/16.9 floz = 899/1690 → 0.531953 ;
   11.49/25.5 = 383/850 → 0.450588 ; A vs winner = (899×850)/(1690×383)
   −1 → 18.0574 (1168800/64727). Le winner a la PLUS GROSSE étiquette
   → note LOWEST STICKER.
8. 2-for-$7 publié : 7.00/(2×15)=7/30 → 0.233333 ; 3.99/24 = 133/800 →
   0.166250 ; vs winner 2300/57 → 40.3509. Le pack « promo » est le
   PLUS GROS et le PLUS CHER par once → note BIGGEST PACKAGE.
9. Coupon qui inverse (jamais déviner le coupon : l'appelant le passe
   en prix net) : 2.00/12 = 1/6 → 0.166667 bat 6.00/32 = 3/16 →
   0.187500 ; B vs winner = 12.5000 pile (25/2).
10. Le piège Celsius (r/aldi, r/changemyview) : même famille, unités
    différentes — 288 floz à 7.99 vs 8.5 qt à 6.99. 8.5 qt = 272 floz
    PILE (gal=128 floz, qt=gall/4). 799/28800 → 0.027743 vs 699/27200
    → 0.025699 ; A vs winner = 50050/6291 → 7.9558. LE 24-PACK GAGNE —
    la lecture oz-vs-quart à l'œil nu est exactement ce que le LM ne
    sait pas faire. CETTE table croisée est le test qui a PÊCHÉ le bug
    historique de units.py : floz_us était tablé à 2,957 L l'once (×100)
    et qt_us/pt_us/cup_us ×10 — NIST SP 811 : 1 floz = 29,5735295625 mL
    pile. Gardes de régression au bas du fichier.
11. « 1 lb 4 oz » (r/mildlyinfuriating) = 20 oz à la fraction près →
    TIE nommé avec « 20 oz » au même prix. L'employée qui refusait le
    coupon avait tort en arithmétique ; le serveur, lui, convertit.
12. Étiquette auditée (r/LifeProTips « Walmart got the math wrong ») :
    2.69/12 oz = 269/1200 → 0.224167. Le tag « 0.244 » (3 dp) est
    TAG_WRONG ; le tag « 0.224 » est TAG_HONEST — jugé à SA précision,
    jamais à la nôtre (leçon Consumer Reports : c'est l'arrondi qui
    change le gagnant).

Refus NOMMÉS testés : mode hors grammaire ; virgule « 19,99 » (vers
/num/parse) ; familles mélangées (oz vs each) ; qty_str + qty/unit
contradictoires ; unité inconnue ; count 1 / 1.5 / 1000 ; 7 offres ;
old_price sans new_price ; no-op ; basis hors famille ; qty_str mixte.

NR — ce fichier est né sous le numéro 65 ; la session bench a pris 65
(money/aging) et v0.92.0 en vol, exactement la leçon du bundle61/62/63
gravée au skill : `ls tests/` à la micro-seconde de l'ÉCRITURE, pas de
la conception.
"""
import pytest

import unitpricekit as uk
from unitpricekit import UnitPriceError, run_unitprice


def _x(fr):
    return {"numerator": fr.numerator, "denominator": fr.denominator}


# --------------------------------------------------------------- shrink
def test_gatorade_published_vector_two_denominators():
    out = run_unitprice({"mode": "shrink", "unit": "floz",
                         "old_size": "32", "new_size": "28"})
    pc = out["product_change"]
    assert pc["display"] == "12.5000"
    assert pc["exact_fraction"] == _x(__import__("fractions").Fraction(
        25, 2))
    assert pc["denominator"] == "old size 32 floz_us"
    up = out["unit_price_change"]
    assert up["display"] == "14.2857"
    assert up["exact_fraction"] == _x(__import__("fractions").Fraction(
        100, 7))
    assert up["denominator"] == "new size 28 floz_us"
    assert out["price"] == "unchanged"
    assert "NOT the same number" in out["note"]


def test_hershey_29_to_239():
    out = run_unitprice({"mode": "shrink", "unit": "oz",
                         "old_size": "29", "new_size": "23.9"})
    assert out["product_change"]["display"] == "17.5862"
    assert out["product_change"]["exact_fraction"] == {"numerator": 510,
                                                       "denominator": 29}
    assert out["unit_price_change"]["display"] == "21.3389"
    assert out["unit_price_change"]["exact_fraction"] == {
        "numerator": 5100, "denominator": 239}


def test_ten_portions_become_nine_count_family():
    """TheWhyWeProject publié : +1/9 par portion — famille COUNT."""
    out = run_unitprice({"mode": "shrink", "unit": "portions",
                         "old_size": "10", "new_size": "9"})
    assert out["product_change"]["display"] == "10.0000"
    assert out["product_change"]["exact_fraction"] == {"numerator": 10,
                                                       "denominator": 1}
    assert out["unit_price_change"]["display"] == "11.1111"
    assert out["unit_price_change"]["exact_fraction"] == {
        "numerator": 100, "denominator": 9}


def test_metric_500g_to_400g_round_ratios():
    out = run_unitprice({"mode": "shrink", "unit": "g",
                         "old_size": "500", "new_size": "400"})
    assert out["product_change"]["display"] == "20.0000"
    assert out["unit_price_change"]["display"] == "25.0000"
    assert "not a no-op" not in out["note"]


def test_upsizing_signs_say_gain_not_loss():
    out = run_unitprice({"mode": "shrink", "unit": "oz",
                         "old_size": "12", "new_size": "14"})
    pc = out["product_change"]
    assert pc["display"] == "-16.6667" and pc["exact_fraction"]["numerator"] == -50
    up = out["unit_price_change"]
    assert up["display"] == "-14.2857" and up["exact_fraction"]["denominator"] == 7
    assert "GAINED" in out["note"]


def test_shrink_with_price_change_both_move():
    out = run_unitprice({"mode": "shrink", "unit": "floz",
                         "old_size": "32", "new_size": "28",
                         "old_price": "5.00", "new_price": "5.50"})
    assert out["unit_price_change"]["display"] == "25.7143"
    assert out["unit_price_change"]["exact_fraction"] == {
        "numerator": 180, "denominator": 7}
    assert out["price"] == {"old": "5.00", "new": "5.50"}


# --------------------------------------------------------------- compare
def test_olive_oil_published_pair_lowest_sticker_loses():
    out = run_unitprice({"mode": "compare", "offers": [
        {"label": "small", "price": "8.99", "qty": "16.9", "unit": "floz"},
        {"label": "big", "price": "11.49", "qty": "25.5", "unit": "floz"}]})
    a, b = out["offers"]
    assert a["per_unit"]["display"] == "0.531953"
    assert a["per_unit"]["exact_fraction"] == {"numerator": 899,
                                               "denominator": 1690}
    assert b["per_unit"]["display"] == "0.450588"
    assert b["per_unit"]["exact_fraction"] == {"numerator": 383,
                                               "denominator": 850}
    assert out["winner"] == "big"
    assert a["vs_winner"]["display"] == "18.0574"
    assert a["vs_winner"]["exact_fraction"] == {"numerator": 1168800,
                                                "denominator": 64727}
    assert b["vs_winner"]["display"] == "0.0000"
    assert "LOWEST STICKER" in out["note"]


def test_two_for_seven_promo_is_the_worst_per_ounce():
    out = run_unitprice({"mode": "compare", "offers": [
        {"label": "promo", "price": "7.00", "qty": "15", "unit": "oz",
         "count": "2"},
        {"label": "single", "price": "3.99", "qty": "24", "unit": "oz"}]})
    promo, single = out["offers"]
    assert promo["per_unit"]["display"] == "0.233333"
    assert promo["per_unit"]["exact_fraction"] == {"numerator": 7,
                                                   "denominator": 30}
    assert single["per_unit"]["display"] == "0.166250"
    assert promo["vs_winner"]["display"] == "40.3509"
    assert promo["vs_winner"]["exact_fraction"] == {"numerator": 2300,
                                                    "denominator": 57}
    assert out["winner"] == "single"
    assert "BIGGEST package yet costs 40.3509" in out["note"]
    assert promo["expression"] == "7.00 / 30 oz = 0.233333 per oz"


def test_coupon_inverts_the_bulk_myth():
    """(3.00−1.00)/12 bat 6.00/32 — le coupon est passé en prix NET,
    le serveur ne dévine pas la promo d'autrui (pick, don't
    transcribe)."""
    out = run_unitprice({"mode": "compare", "offers": [
        {"label": "small+coupon", "price": "2.00", "qty": "12",
         "unit": "oz"},
        {"label": "bulk", "price": "6.00", "qty": "32", "unit": "oz"}]})
    assert out["winner"] == "small+coupon"
    assert out["offers"][0]["per_unit"]["display"] == "0.166667"
    assert out["offers"][1]["per_unit"]["display"] == "0.187500"
    assert out["offers"][1]["vs_winner"]["display"] == "12.5000"
    assert out["offers"][1]["vs_winner"]["exact_fraction"] == {
        "numerator": 25, "denominator": 2}
    assert "BIGGEST package yet costs 12.5000" in out["note"]


def test_quart_versus_ounce_celsius_trap():
    """Le piège r/aldi : 18-pack en floz contre 24-pack en qt. Le
    24-pack GAGNE (699/27200 < 799/28800) — lecture à l'œil nu
    impossible, table croisée exacte obligatoire."""
    out = run_unitprice({"mode": "compare", "basis": "floz", "offers": [
        {"label": "18-pack", "price": "7.99", "qty": "288", "unit": "floz"},
        {"label": "24-pack", "price": "6.99", "qty": "8.5", "unit": "qt"}]})
    assert out["basis_unit"] == "floz_us"
    a, b = out["offers"]
    assert a["per_unit"]["display"] == "0.027743"
    assert a["per_unit"]["exact_fraction"] == {"numerator": 799,
                                               "denominator": 28800}
    assert b["per_unit"]["display"] == "0.025699"
    assert b["per_unit"]["exact_fraction"] == {"numerator": 699,
                                               "denominator": 27200}
    assert out["winner"] == "24-pack"
    assert a["vs_winner"]["display"] == "7.9558"
    assert a["vs_winner"]["exact_fraction"] == {"numerator": 50050,
                                                "denominator": 6291}


def test_compound_notation_lb4oz_ties_twenty_ounce():
    """r/mildlyinfuriating : 1 lb 4 oz EST 20 oz. Égalité EXACTE —
    nommée TIE, jamais départagée par un arrondi."""
    out = run_unitprice({"mode": "compare", "offers": [
        {"label": "bread", "price": "3.00", "qty_str": "1 lb 4 oz"},
        {"label": "coupon", "price": "3.00", "qty": "20", "unit": "oz"}]})
    assert out["winner"] is None
    assert "TIE" in out["note"]
    assert out["offers"][0]["size"] == out["offers"][1]["size"]
    assert out["offers"][0]["size_said"] == {"value": "1.25",
                                             "unit": "lb"}


def test_metric_compound_two_l_500ml():
    out = run_unitprice({"mode": "compare", "offers": [
        {"label": "jumbo", "price": "4.00", "qty_str": "2 l 500 ml"},
        {"label": "plain", "price": "1.20", "qty": "1000", "unit": "ml"}]})
    assert out["basis_unit"] == "l"
    assert out["offers"][0]["size_said"] == {"value": "2.5", "unit": "l"}
    assert out["offers"][0]["per_unit"]["display"] == "1.600000"
    assert out["offers"][1]["per_unit"]["display"] == "1.200000"
    assert out["winner"] == "plain"
    # 1.6/1.2 - 1 = 1/3 -> 33.3333 (100/3)
    assert out["offers"][0]["vs_winner"]["display"] == "33.3333"
    assert out["offers"][0]["vs_winner"]["exact_fraction"] == {
        "numerator": 100, "denominator": 3}


def test_tag_allegation_wrong_and_honest():
    """r/LifeProTips Walmart : l'étiquette est une ALLÉGATION, jugée à
    SA précision. 2.69/12 oz = 269/1200 = 0.224167... : tag 0.244 →
    TAG_WRONG ; tag 0.224 (même arrondi 3 dp) → TAG_HONEST."""
    body = {"mode": "compare", "offers": [
        {"label": "A", "price": "2.69", "qty": "12", "unit": "oz"},
        {"label": "B", "price": "2.40", "qty": "11", "unit": "oz"}]}
    wrong = run_unitprice({**body, "offers": [
        {"label": "A", "price": "2.69", "qty": "12", "unit": "oz",
         "tag": {"value": "0.244", "unit": "oz"}},
        {"label": "B", "price": "2.40", "qty": "11", "unit": "oz"}]})
    aud = wrong["offers"][0]["tag_audit"]
    assert aud["verdict"] == "TAG_WRONG"
    assert aud["true_exact"]["display"] == "0.224167"
    assert aud["true_exact"]["exact_fraction"] == {"numerator": 269,
                                                   "denominator": 1200}
    assert "claims 0.244" in aud["note"]
    honest = run_unitprice({**body, "offers": [
        {"label": "A", "price": "2.69", "qty": "12", "unit": "oz",
         "tag": {"value": "0.224", "unit": "oz"}},
        {"label": "B", "price": "2.40", "qty": "11", "unit": "oz"}]})
    aud2 = honest["offers"][0]["tag_audit"]
    assert aud2["verdict"] == "TAG_HONEST"
    assert "quantized at 3 dp" in aud2["note"]


# ------------------------------------------------------------ refusals
def test_mode_closed_set_refused():
    with pytest.raises(UnitPriceError) as e:
        run_unitprice({"mode": "mystery"})
    assert e.value.field == "mode"
    assert "compare, shrink" in e.value.expected


def test_comma_price_refused_and_punned_to_num_parse():
    with pytest.raises(UnitPriceError) as e:
        run_unitprice({"mode": "compare", "offers": [
            {"price": "19,99", "qty": "1", "unit": "oz"},
            {"price": "2.00", "qty": "1", "unit": "oz"}]})
    assert e.value.field == "offers[0].price"
    assert "num/parse" in e.value.message


def test_cross_family_refusal_teaches_the_exit():
    with pytest.raises(UnitPriceError) as e:
        run_unitprice({"mode": "compare", "offers": [
            {"price": "1.00", "qty": "12", "unit": "oz"},
            {"price": "1.00", "qty": "6", "unit": "each"}]})
    assert e.value.field == "offers[1]"
    assert "cross-family" in e.value.message


def test_qty_str_and_qty_are_mutually_exclusive():
    with pytest.raises(UnitPriceError) as e:
        run_unitprice({"mode": "compare", "offers": [
            {"price": "1.00", "qty_str": "20 oz", "qty": "20",
             "unit": "oz"},
            {"price": "1.00", "qty": "1", "unit": "oz"}]})
    assert "mutually exclusive" in e.value.message


def test_unknown_unit_and_mixed_compound_refused():
    with pytest.raises(UnitPriceError) as e:
        run_unitprice({"mode": "compare", "offers": [
            {"price": "1.00", "qty": "5", "unit": "sticks"},
            {"price": "1.00", "qty": "5", "unit": "oz"}]})
    assert "sticks" in e.value.message
    with pytest.raises(UnitPriceError) as e:
        run_unitprice({"mode": "compare", "offers": [
            {"price": "1.00", "qty_str": "1 l 4 oz"},
            {"price": "1.00", "qty": "5", "unit": "ml"}]})
    assert e.value.field == "offers[0]"
    assert "mixes families" in e.value.message


def test_count_grammar_named():
    base = {"price": "1.00", "qty": "2", "unit": "oz"}
    for bad in ("1", "1.5", "1000"):
        with pytest.raises(UnitPriceError) as e:
            run_unitprice({"mode": "compare", "offers": [
                {**base, "count": bad}, base]})
        assert e.value.field == "offers[0].count"


def test_offer_cap_and_basis_family_named():
    offers = [{"price": "1.00", "qty": "2", "unit": "oz"}] * 7
    with pytest.raises(UnitPriceError) as e:
        run_unitprice({"mode": "compare", "offers": offers})
    assert e.value.field == "offers"
    with pytest.raises(UnitPriceError) as e:
        run_unitprice({"mode": "compare", "basis": "each", "offers": [
            {"price": "1.00", "qty": "2", "unit": "oz"},
            {"price": "1.00", "qty": "3", "unit": "oz"}]})
    assert e.value.field == "basis"


def test_shrink_refusals_paired_price_and_noop():
    with pytest.raises(UnitPriceError) as e:
        run_unitprice({"mode": "shrink", "unit": "oz", "old_size": "5",
                       "new_size": "4", "old_price": "3"})
    assert e.value.field == "new_price"
    with pytest.raises(UnitPriceError) as e:
        run_unitprice({"mode": "shrink", "unit": "oz", "old_size": "5",
                       "new_size": "5"})
    assert "nothing moved" in e.value.message


def test_zero_size_refused_not_division_by_zero():
    with pytest.raises(UnitPriceError) as e:
        run_unitprice({"mode": "shrink", "unit": "oz", "old_size": "16",
                       "new_size": "0"})
    assert e.value.field == "new_size"


# ------------------------------------------------ the caught bug (NR)
def test_us_volume_factors_are_nist_exact():
    """LA RÉGRESSION GARDE : jusqu'à ce bundle, floz_us était tablé à
    2,957 L l'once (×100) et qt_us/pt_us/cup_us ×10 dans units.py —
    péché par la table croisée qt<->floz du test Celsius ci-dessus.
    NIST SP 811 App. B : 1 floz = 29,5735295625 mL pile (gal = 231
    in³ = 3,785411784 L, floz = gal/128)."""
    import units
    got = units.units_convert("1", "floz_us", "ml", places=10)
    assert got["value"] == "29.5735295625"
    assert units.units_convert("1", "qt_us", "l", places=9)["value"] \
        == "0.946352946"
    assert units.units_convert("1", "pt_us", "ml", places=6)["value"] \
        == "473.176473"
    assert units.units_convert("1", "cup_us", "ml", places=7)["value"] \
        == "236.5882365"
    # identités internes exactes : 128 floz = 4 qt = 8 pt = 16 cup = 1 gal
    from fractions import Fraction
    fam = units.FAMILIES["volume"]["units"]
    def f(u):
        n, d = fam[u]
        return Fraction(n) / Fraction(d)
    assert f("floz_us") * 128 == f("gal_us")
    assert f("qt_us") * 4 == f("gal_us")
    assert f("pt_us") * 8 == f("gal_us")
    assert f("cup_us") * 16 == f("gal_us")


def test_count_family_is_pure_tally():
    """100 sheets à 4.80 = 200 sheets à 9.60 au centime près — TIE
    nommé par fractions exactes, pas par tolérance."""
    out = run_unitprice({"mode": "compare", "offers": [
        {"label": "roll-s", "price": "4.80", "qty": "100", "unit": "sheets"},
        {"label": "roll-xl", "price": "9.60", "qty": "200",
         "unit": "sheets"}]})
    assert out["winner"] is None and "TIE" in out["note"]
    # 4.80/100 = 0.048 = 6/125 ; 9.60/200 = 6/125 — égalité EXACTE
    assert out["offers"][0]["per_unit"]["exact_fraction"] == {
        "numerator": 6, "denominator": 125}
    assert out["offers"][1]["per_unit"]["exact_fraction"] == {
        "numerator": 6, "denominator": 125}


def test_determinism_same_bytes_twice():
    body = {"mode": "shrink", "unit": "g", "old_size": "500",
            "new_size": "400"}
    a = run_unitprice(dict(body))
    b = run_unitprice(dict(body))
    import json
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# --------------------------------------------------- money_unitprice wire
def _client():
    from fastapi.testclient import TestClient
    import main
    main.RATE_LIMIT = 10**9
    return TestClient(main.app)


def test_route_200_sha_and_determinism():
    """the wire promise: same bytes twice, sha256 self-cert travels."""
    c = _client()
    body = {"mode": "shrink", "unit": "floz", "old_size": "32",
            "new_size": "28"}
    r1 = c.post("/api/v1/money/unitprice", json=body)
    r2 = c.post("/api/v1/money/unitprice", json=body)
    assert r1.status_code == 200
    assert r1.content == r2.content
    out = r1.json()
    assert out["sha256"]
    assert out["product_change"]["display"] == "12.5000"
    assert out["unit_price_change"]["exact_fraction"] == {
        "numerator": 100, "denominator": 7}


def test_route_400_names_the_field():
    c = _client()
    r = c.post("/api/v1/money/unitprice", json={
        "mode": "compare", "offers": [
            {"price": "19,99", "qty": "1", "unit": "oz"},
            {"price": "2.00", "qty": "1", "unit": "oz"}]})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "offers[0].price"


def test_route_top1_three_languages():
    c = _client()
    qs = [
        "the 500 gram package became 400 grams at the same price — "
        "what is the real price per unit, this shrinkflation math",
        "le paquet de 500 g est passé à 400 g au même prix — combien "
        "au kilo en vrai, cette arnaque shrinkflation",
        "o pacote de 500 g virou 400 g pelo mesmo preço — quanto por "
        "quilo de verdade essa shrinkflation",
    ]
    for q in qs:
        r = c.get("/route", params={"q": q})
        top = r.json()["tools"][0]["tool"]
        assert top == "money_unitprice", (q, top)


def test_e16_landing_card_baked_three_languages():
    """Full-phrase guard (maison) : la puce e16 est RÉELLEMENT
    recalculée au build — oracles 500→400 g : −20.0000 produit,
    +25.0000 unité, virgule en FR/PT."""
    import json
    en = json.load(open("locales/en.json", encoding="utf-8"))
    fr = json.load(open("locales/fr.json", encoding="utf-8"))
    pt = json.load(open("locales/pt.json", encoding="utf-8"))
    assert "\u221220.0000% of product, +25.0000% per unit" \
        in en["everyday_grid"]
    assert "\u221220,0000% de produit, +25,0000% au kilo" \
        in fr["everyday_grid"]
    assert "\u221220,0000% de produto, +25,0000% por quilo" \
        in pt["everyday_grid"]
    assert "500 g pack became 400 g" in en["everyday_grid"]
    assert "500 g est devenu 400 g" in fr["everyday_grid"]
    assert "500 g viraram 400 g" in pt["everyday_grid"]
