"""bundle51 — F5 fiches-recettes à chaîne (ficheskit). ORACLE : chaque
attendu est calculé À LA MAIN ici ; les golds du bench v16 servent de
contre-épreuve INDÉPENDANTE : mêmes problèmes, chemin inverse — 382.90
et 1469.00 sont sortis d'un Fraction de génération revu par un second
oracle Decimal relu depuis le texte. Un modèle nu n'en a fait que
0/28 ; la fiche, elle, n'a pas eu à relire l'histoire."""
import pytest

import ficheskit as fk


# — shop_reste : le #00 de v16. Main : 435−35=400 ; 40 % de 400=160 ;
# 400−160=240.
def test_shop_reste_bench_gold():
    out = fk.run_fiche("shop_reste", {"total": "435",
                                      "sold_morning": "35",
                                      "pct_afternoon": "40%"})
    assert out["answer"]["remaining"] == "240"
    assert out["target"] == "remaining"
    assert len(out["trace"]) == 3
    assert "rest_after_morning" in out["trace"][0]["expr"]


def test_shop_reste_second_gold():
    # #06 du bench : 263−63=200 ; 40 % = 80 ; reste 120.
    out = fk.run_fiche("shop_reste", {"total": 263, "sold_morning": 63,
                                      "pct_afternoon": "0.4"})
    assert out["answer"]["remaining"] == "120"


# — partage_reste : #01 main : 3829 × 3/5 = 2297,4 ; × 1/6 = 382,90.
def test_partage_reste_bench_gold():
    out = fk.run_fiche("partage_reste", {"total": "3829",
                                         "first_part": "2/5",
                                         "second_of_rest": "1/6"})
    assert out["answer"]["second_share"] == "382.90"
    # leftover = 2297,40 − 382,90 = 1914,50
    assert out["answer"]["leftover"] == "1914.50"


def test_partage_reste_quarter_gold():
    # #14 : 8814 × 2/3 = 5876 ; ÷ 4 = 1469.
    out = fk.run_fiche("partage_reste", {"total": 8814,
                                         "first_part": "1/3",
                                         "second_of_rest": "1/4"})
    assert out["answer"]["second_share"] == "1469"


# — soldes2 : #03 : 81,90 × 0,75 = 61,425 ; × 0,8 = 49,14 ;
# somme naïve 45 % vs effectif 40 % : l'écart = 5 points de prix.
def test_soldes2_bench_gold():
    out = fk.run_fiche("soldes2", {"price": "81.90", "pct1": "25%",
                                   "pct2": "20%"})
    assert out["answer"]["final"] == "49.14"
    assert out["answer"]["naive_sum_pct"] == "45"
    assert out["answer"]["effective_pct"] == "40"
    assert "money/discount" in out["see_also"]      # anti-doublon écrit


def test_thirds_never_round_silently():
    # 1/3 de 400 : la fiche rend la fraction mixte, pas 133.33 nu.
    out = fk.run_fiche("partage_reste", {"total": "400",
                                         "first_part": "0",
                                         "second_of_rest": "1/3"})
    assert out["answer"]["second_share"].startswith("133 1/3")


def test_slot_grammar_closed_and_named():
    for bad in ("beaucoup", "40 per cent", "1,234", "$12"):
        with pytest.raises(fk.Slot) as e:
            fk.run_fiche("shop_reste", {"total": bad,
                                        "sold_morning": "1",
                                        "pct_afternoon": "10%"})
        assert e.value.field == "total"
        assert "closed number" in e.value.message


def test_negative_rest_refused_by_name():
    with pytest.raises(fk.Slot) as e:
        fk.run_fiche("shop_reste", {"total": "10", "sold_morning": "12",
                                    "pct_afternoon": "50%"})
    assert e.value.field == "sold_morning"


def test_unknown_fiche_refused():
    with pytest.raises(fk.Slot):
        fk.run_fiche("compound_interest", {})


def test_determinism_same_slots_same_bytes():
    a = fk.run_fiche("shop_reste", {"total": "435", "sold_morning": "35",
                                    "pct_afternoon": "40%"})
    b = fk.run_fiche("shop_reste", {"total": "435", "sold_morning": "35",
                                    "pct_afternoon": "40%"})
    assert a == b


# — le 0.5B du smoke 22-11 écrivait "40" pour 40 % (→ ×40 silencieux)
# et une quantité calculée dans un créneau de part. Les deux sont des
# REFUS nommés avec la forme attendue, jamais des devinettes.
def test_bare_number_in_pct_slot_refused_with_hint():
    with pytest.raises(fk.Slot) as e:
        fk.run_fiche("shop_reste", {"total": "100", "sold_morning": "5",
                                    "pct_afternoon": "40"})
    assert e.value.field == "pct_afternoon"
    assert "multiply by forty" in e.value.expected
    # 0.4 et "40%" passent — les deux formes honnêtes :
    assert fk.run_fiche("shop_reste", {"total": "100",
                                       "sold_morning": "5",
                                       "pct_afternoon": "0.4"})
    assert fk.run_fiche("shop_reste", {"total": "100",
                                       "sold_morning": "5",
                                       "pct_afternoon": "40%"})


def test_computed_quantity_in_share_slot_refused():
    with pytest.raises(fk.Slot) as e:
        fk.run_fiche("partage_reste", {"total": "3829",
                                       "first_part": "2857",
                                       "second_of_rest": "1/6"})
    assert "you" in e.value.expected.lower()
    assert e.value.field == "first_part"


def test_pct_100_legitimate_not_refused():
    # 100 % est un pourcentage licite : tout le reste est vendu, il
    # reste ZERO — et zéro doit être rendu, pas refusé comme ambigu.
    out = fk.run_fiche("shop_reste", {"total": "50", "sold_morning": "10",
                                      "pct_afternoon": "100%"})
    assert out["answer"]["remaining"] == "0"
