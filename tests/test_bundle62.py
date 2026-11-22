# -*- coding: utf-8 -*-
"""bundle62 — /money/bogo : l'arnaque du panneau BOGO, calculée à la main.

Ce fichier est né sous le numéro 61 (commit `c2a5015`) ; le numéro 61 a
été repris depuis par des tests de planification cron, donc les tests
money/bogo voyagent ici, inchangés octet pour octet, sous le numéro libre
suivant.

ORACLES (calculs MAIN, jamais la sortie du module recopiée) :

1. Prix ÉGAUX 40,00 + 40,00, « get the second 50% off » (tableau publié
   dothecalculation.com : 40+20 = 60 payés sur 80) :
   paid_lo = 40,00 × (100-50)/100 = 2 000,00/100 = 20,00 pile.
   paire payée 60,00 ; full 80,00 ; saved 20,00.
   20/80 = 1/4 → effectif 25 % PILE → display « 25.0000 », exact 25/1.
   Le panneau dit 50, la note dit 25 — c'est LE vecteur publié.

2. Prix INÉGAUX 60,00 + 40,00, même panneau (vecteur publié
   convertitive.com : « you pay 60 + 20 = 80 instead of 100, a 20%
   discount on the pair ») :
   le MOINCHER (40,00) porte la remise → paid_lo 20,00 ; paire 80,00 ;
   full 100,00 ; saved 20,00 ; 20/100 = 1/5 → « 20.0000 », exact 1/5.
   Ni 25 % ni 50 % : le prix inégal mange 5 points de promo.

3. BOGO FREE 40+40 : l'article moins cher gratuit → payé 40,00 sur
   80,00 ; saved 40,00 ; 40/80 = 1/2 → « 50.0000 », exact 1/2.

4. RESTE IMPAIR : une paire 25+25 + UN extra 25 :
   paid_lo = 25 × 50/100 = 1 250/100 = 12,5 ; paire 37,5 ;
   payé 37,5 + 25 = 62,5 ; full 75 ; saved 12,5.
   12,5/75 = 1/6 → ×100 = 50/3 = 16,666|666... → HALF_UP 4 dp =
   « 16.6667 », exact fraction 50/3 (la fraction est le produit,
   l'affichage n'est qu'un rendu).

5. EMPILEMENT : cas 1 + coupon 30 :
   payé_post_bogo 60,00 × (100-30)/100 = 4 200,00/100 = 42,00 ;
   saved 38,00 ; 38/80 = 19/40 → ×100 = 95/2 = 47,5 → « 47.5000 ».
   Le MENSONGE additif : 25,0000 + 30 = 55,0000 — la note doit nommer
   les deux et trancher : 47,5 est la note, 55 est le titre.

6. Refus NOMMÉS (grammaire fermée) : offre hors famille ; second_percent
   manquant sur bogo_percent ; second_percent PRÉSENT sur bogo_free (ne
   jamais dévorer silencieusement un argument contradictoire) ; prix à
   virgule « 81,90 » (c'est /num/parse qui fait ce travail) ; paire de
   3 prix ; treizième paire ; prix nul ; coupon 0.

Chaque test nomme l'erreur de comptoir qu'il empêche.
"""
import pytest

import bogokit
from bogokit import BogoError, run_bogo


def test_equal_price_pair_is_25_not_50():
    """Le vecteur publié : BOGO 50 % sur deux 40,00 = 25 % de la paire."""
    out = run_bogo({"offer": "bogo_percent", "second_percent": "50",
                    "pairs": [["40.00", "40.00"]]})
    assert out["totals"] == {"full": "80.00",
                             "paid_before_coupon": "60.00",
                             "paid": "60.00", "saved": "20.00"}
    eff = out["effective"]
    assert eff["percent"] == "25.0000"
    assert eff["exact_fraction"] == {"numerator": 25, "denominator": 1}
    assert out["bill"]["bill_says"] == "25.0000% off the whole purchase"
    assert out["pairs"][0]["expression"] == \
        "40.00 + 40.00x(1 - 50/100) = 60.00"


def test_unequal_pair_is_20_the_published_vector():
    """convertitive.com 60+40 -> on paie 80 sur 100 -> 20 %, ni 25 ni 50."""
    out = run_bogo({"offer": "bogo_percent", "second_percent": "50",
                    "pairs": [["60.00", "40.00"]]})
    assert out["totals"]["paid"] == "80.00"
    assert out["effective"]["percent"] == "20.0000"
    assert out["effective"]["exact_fraction"] == {"numerator": 20,
                                                  "denominator": 1}
    p = out["pairs"][0]
    assert p["pricier"] == "60.00" and p["cheaper"] == "40.00"
    assert p["same_price"] is False
    assert "UNEQUAL-priced" in out["bill"]["note"]
    assert "CHEAPER item" in out["bill"]["note"]


def test_bogo_free_is_a_real_50():
    """BOGOF 40+40 : le moins cher gratuit -> 40 payés sur 80 -> 50 %."""
    out = run_bogo({"offer": "bogo_free", "pairs": [["40.00", "40.00"]]})
    assert out["totals"]["paid"] == "40.00"
    assert out["effective"]["percent"] == "50.0000"
    assert out["effective"]["exact_fraction"] == {"numerator": 50,
                                                  "denominator": 1}
    assert out["bill"]["ad_says"] == "buy one, get one free"


def test_odd_remainder_pays_full_and_the_fraction_travels():
    """3 x 25 sous BOGO 50 = 62,5 payés sur 75 -> 50/3 % -> 16.6667."""
    out = run_bogo({"offer": "bogo_percent", "second_percent": "50",
                    "pairs": [["25", "25"]], "extras": ["25"]})
    assert out["totals"] == {"full": "75", "paid_before_coupon": "62.5",
                             "paid": "62.5", "saved": "12.5"}
    eff = out["effective"]
    assert eff["percent"] == "16.6667"
    assert eff["exact_fraction"] == {"numerator": 50, "denominator": 3}
    assert "paid FULL price" in out["bill"]["note"]


def test_stacked_coupon_multiplies_never_adds():
    """25 % (BOGO) puis 30 % (coupon) = 47.5000 %, PAS 55 — les deux
    chiffres doivent être DANS la note, sinon le client refait l'addition
    mentalement (c'est précisément l'erreur de comptoir pêchée)."""
    out = run_bogo({"offer": "bogo_percent", "second_percent": "50",
                    "pairs": [["40.00", "40.00"]],
                    "coupon_percent": "30"})
    assert out["totals"]["paid"] == "42.00"
    assert out["effective"]["percent"] == "47.5000"
    assert out["effective"]["bogo_step_only"] == "25.0000"
    assert out["effective"]["exact_fraction"] == {"numerator": 95,
                                                  "denominator": 2}
    note = out["bill"]["note"]
    assert "47.5000% off the bill, NOT 55.0000%" in note


def test_unknown_offer_refused_by_name():
    with pytest.raises(BogoError) as e:
        run_bogo({"offer": "2_for_15", "pairs": [["40.00", "40.00"]]})
    assert e.value.field == "offer"
    assert "closed" in e.value.message
    assert e.value.expected == "one of: bogo_free, bogo_percent"


def test_bogo_percent_without_second_percent_is_refused_not_guessed():
    """50 est CE que le panneau dit souvent — le serveur ne devine jamais
    le chiffre d'une affiche qu'il ne voit pas."""
    with pytest.raises(BogoError) as e:
        run_bogo({"offer": "bogo_percent", "pairs": [["40.00", "40.00"]]})
    assert e.value.field == "second_percent"


def test_second_percent_on_free_is_refused_not_swallowed():
    with pytest.raises(BogoError) as e:
        run_bogo({"offer": "bogo_free", "second_percent": "50",
                  "pairs": [["40.00", "40.00"]]})
    assert e.value.field == "second_percent"
    assert "remove" in e.value.message


def test_comma_price_refused_and_punned_to_num_parse():
    """« 81,90 » est une FORME, pas un nombre pour nous — refus nommé qui
    dit où est l'outil de la forme (/num/parse), même grammaire que
    money/discount."""
    with pytest.raises(BogoError) as e:
        run_bogo({"offer": "bogo_free", "pairs": [["81,90", "40"]]})
    assert e.value.field == "pairs[0][0]"
    assert "num/parse" in e.value.message


def test_triple_pair_refused_points_at_extras():
    with pytest.raises(BogoError) as e:
        run_bogo({"offer": "bogo_free",
                  "pairs": [["10.00", "10.00", "10.00"]]})
    assert e.value.field == "pairs[0]"
    assert "extras" in e.value.message


def test_pair_cap_named():
    pairs = [["1.00", "1.00"]] * 13
    with pytest.raises(BogoError) as e:
        run_bogo({"offer": "bogo_free", "pairs": pairs})
    assert e.value.field == "pairs"
    assert "12" in e.value.message


def test_zero_price_named_and_zero_coupon_named():
    with pytest.raises(BogoError) as e:
        run_bogo({"offer": "bogo_free", "pairs": [["0", "10.00"]]})
    assert e.value.field == "pairs[0]"
    with pytest.raises(BogoError) as e:
        run_bogo({"offer": "bogo_free", "pairs": [["10.00", "10.00"]],
                  "coupon_percent": "0"})
    assert e.value.field == "coupon_percent"


def test_multi_pair_sums_exact():
    """deux paires inégales : (60+40)->80 et (30+10)->35 — payé 115 sur
    140 ; saved 25 ; 25/140 = 5/28 = 17,857142... -> 17.8571, exact 5/28."""
    out = run_bogo({"offer": "bogo_percent", "second_percent": "50",
                    "pairs": [["60.00", "40.00"], ["30.00", "10.00"]]})
    assert out["totals"] == {"full": "140.00",
                             "paid_before_coupon": "115.00",
                             "paid": "115.00", "saved": "25.00"}
    assert out["effective"]["percent"] == "17.8571"
    assert out["effective"]["exact_fraction"] == {"numerator": 125,
                                                  "denominator": 7}


def test_no_scientific_notation_in_any_money_field():
    """leçon « 3E+1 » : format(d,'f') partout — ici 1000.00 ne doit
    JAMAIS sortir en exponentielle sous la pleine gratuité."""
    out = run_bogo({"offer": "bogo_free", "pairs": [["1000.00", "1000.00"]]})
    blob = repr(out)
    assert "E+" not in blob and "e-0" not in blob
    assert out["totals"]["paid"] == "1000.00"


# --------------------------------------------------- money_bogo route-level
def test_route_200_sha_and_determinism():
    """money_bogo route-level — the wire promise: same bytes twice, and
    the self-cert sha256 travels."""
    from fastapi.testclient import TestClient
    import main
    main.RATE_LIMIT = 10**9
    client = TestClient(main.app)
    body = {"offer": "bogo_percent", "second_percent": "50",
            "pairs": [["60.00", "40.00"]]}
    r1 = client.post("/api/v1/money/bogo", json=body)
    r2 = client.post("/api/v1/money/bogo", json=body)
    assert r1.status_code == 200
    assert r1.content == r2.content
    out = r1.json()
    assert out["sha256"] and out["bill"]["bill_says"] == \
        "20.0000% off the whole purchase"


def test_route_400_names_the_field():
    from fastapi.testclient import TestClient
    import main
    main.RATE_LIMIT = 10**9
    client = TestClient(main.app)
    r = client.post("/api/v1/money/bogo",
                    json={"offer": "bogo_galactique",
                          "pairs": [["40.00", "40.00"]]})
    assert r.status_code == 400
    err = r.json()["errors"][0]
    assert err["field"] == "offer"


def test_route_top1_three_languages():
    from fastapi.testclient import TestClient
    import main
    main.RATE_LIMIT = 10**9
    client = TestClient(main.app)
    qs = [
        "bogo buy one get one 50 percent off the second item what is "
        "the real discount",
        "achète le premier le deuxième à −50 % deux sweats 60 et 40 "
        "euros c'est combien sur la note",
        "compre um leve o segundo com 50% off duas camisetas de 60 e "
        "40 qual é o desconto real no caixa",
    ]
    for q in qs:
        r = client.get("/route", params={"q": q})
        top = r.json()["tools"][0]["tool"]
        assert top == "money_bogo", (q, top)


def test_e15_landing_card_baked_three_languages():
    """Full-phrase guard (maison) : les puces e15 sont RECALCULEES ici,
    jamais recopiees du module — 60+40 sous BOGO 50 = 20.0000/20,0000,
    paye 80.00/80,00 sur 100.00/100,00."""
    import json
    en = json.load(open("locales/en.json", encoding="utf-8"))
    fr = json.load(open("locales/fr.json", encoding="utf-8"))
    pt = json.load(open("locales/pt.json", encoding="utf-8"))
    assert "sign says 50%, the pair pays 20.0000 — you pay 80.00 of " \
        "100.00" in en["everyday_grid"]
    assert "l'affiche dit 50%, la paire paie 20,0000 — on règle 80,00 " \
        "sur 100,00" in fr["everyday_grid"]
    assert "a placa diz 50%, o par sai por 20,0000 — você paga 80,00 " \
        "de 100,00" in pt["everyday_grid"]
    # resize 22-11 bundle66: la grille passe a seize puces
    for doc, word in ((en, "Sixteen"), (fr, "Seize"), (pt, "Dezesseis")):
        assert word in doc["everyday.intro"]
