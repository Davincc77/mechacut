# -*- coding: utf-8 -*-
"""bundle120 — /money/payscale : SALAIRE↔HEURE, DENOMINATEURS NOMMÉS
(lentille HUMAIN rang 2, portée DEUX cycles — l'ancre rechargée AU
SOURCE 26-nov : 5 USC 5504(b) relu à Cornell au mot près « divide the
annual rate by 2,087 » + « nearest cent, counting one-half and over
as a whole cent » ; §5505 « one-twelfth » ; r/fednews 1fnk3cb la
dérivation 4×262/17×261/7×260 ; r/ATC 17sefrt les « 20 cents off » ;
r/AskHR 1y0ey31 l'ordre ARRÊTE-D'ABORD qui mange $8 ; r/IRS_Source
1qh5ouz les 27 pay periods des années à 53 vendredis ; 1de8205 le
trio 38.46/38.17/42.55 sur 80 000).

Tous les attendus sont POSÉS À LA MAIN avant exécution ; un oracle
Fraction INDÉPENDANT croise les divisions (b119, règle maison). Les
chaînes exactes du module ne sont JAMAIS recopiées dans un attendu.

MAIN (52 000, fed2087) : 52000/2087 = 24.91615… → cent 24.92.
rate_first biweekly = 24.92 × 80 = 1993.60 ; direct = 52000/26 =
2000.00 ; delta = −6.40 ; trous annuels : 1993.60×26 − 52000 =
−166.40 et 2000.00×26 − 52000 = 0.00.
MAIN (priv2080) : 52000/2080 = 25 EXACT → tout ferme à zéro écart.
OPM ARRONDIT : 18.845 → 18.85 (l'exemple PUBLIÉ d'OPM — un module
qui banker's-arrondit donnerait 18.84 : le vecteur le pèche).
TRIO 1de8205 : 80000/2080=38.4615→38.46 ; 80000/2096=38.1679→38.17 ;
80000/1880=42.5531→42.55.
2026 : 261 workdays (365 = 52×7 + 1 jeudi) ×8 = 2088 ; 2024 : 262
(leap, lundi) ×8 = 2096 ; 2023 : 260 ×8 = 2080.
27 PÉRIODES : 2027 commence VENDREDI → 53 vendredis → (53+1)//2=27
ancrée première, 53//2=26 ancrée seconde. 2016 pareil (leap starts
Friday). 2026 commence jeudi → 52 vendredis → 26/26.
"""
from decimal import Decimal
from fractions import Fraction

import payscalekit
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)

ROUTE = "/api/v1/money/payscale"


def _refuse(args, field):
    try:
        payscalekit.money_payscale(**args)
        assert False, "no refusal for %s" % field
    except payscalekit.PayScaleError as e:
        assert e.field == field, (e.field, field)
        assert e.expected


def _cent_half_up(f):
    """Oracle ÉCRIT À PART : cent half-up sur un Fraction, sans
    Decimal — floor(f*100 + 1/2) en entiers, rendu en Decimal."""
    scaled = f * 100
    cents = (2 * scaled.numerator + scaled.denominator) // (
        2 * scaled.denominator)
    return Decimal(cents) / Decimal(100)


# ------------------------------------------------- le vecteur central
def test_52000_federal_5504b_by_hand():
    out = payscalekit.money_payscale("52000", basis="fed2087",
                                     period="biweekly")
    h = out["hourly"]
    # 52000/2087 à la main : 24.9161… — cent HALF-UP : 24.92
    assert h["rounded_cent"] == "24.92"
    # Oracle Fraction : le décimal rendu EST 52000/2087 à la
    # précision Decimal près (borne 1e-24, jamais une égalité de
    # chaînes tronquées).
    assert abs(Decimal(h["exact"]) * 2087 -
               Decimal(52000)) < Decimal("1e-20")
    # Le CENT est re-joué par l'oracle indépendant, pas par Decimal :
    assert _cent_half_up(Fraction(52000, 2087)) == Decimal("24.92")
    assert "2,087" in h["citation"] or "2087" in h["citation"]
    p = out["periods"]["biweekly"]
    assert p["rate_first"] == "1993.60"   # 24.92 x 80, posés
    assert p["direct"] == "2000.00"       # 52000 / 26
    assert p["delta_rate_first_minus_direct"] == "-6.40"
    assert p["annual_hole_rate_first"] == "-166.40"
    assert p["annual_hole_direct"] == "0.00"
    # 5504(b) cite DIVISER par 2087 puis MULTIPLIER par 80 — la règle
    # de l'ARRONDI du statut voyage, jamais fondue.
    assert "5504" in p["rate_first_rule"]


def test_priv2080_closes_to_zero():
    out = payscalekit.money_payscale("52000", basis="priv2080",
                                     period="biweekly")
    assert out["hourly"]["rounded_cent"] == "25.00"
    p = out["periods"]["biweekly"]
    assert p["rate_first"] == "2000.00"
    assert p["delta_rate_first_minus_direct"] == "0.00"
    assert p["annual_hole_rate_first"] == "0.00"


def test_opm_rounding_example_half_up_not_bankers():
    # L'exemple PUBLIÉ d'OPM (18zjamp, cite OPM au mot près) :
    # $18.845 → $18.85. Denom 2000 = pto 80.
    out = payscalekit.money_payscale("37690", basis="pto",
                                     pto_hours="80")
    assert out["hourly"]["rounded_cent"] == "18.85"
    assert "one-half" in out["hourly"]["rounding"]


def test_1de8205_published_trio():
    # 80 000 : le fil publie 38.46 / 38.17 / 42.55 — les TROIS
    # dénominateurs, chacun nommé par sa base fermée.
    a = payscalekit.money_payscale("80000", basis="priv2080")
    b = payscalekit.money_payscale("80000", basis="workdays",
                                   year=2024)
    c = payscalekit.money_payscale("80000", basis="pto",
                                   pto_hours="200")
    assert a["hourly"]["rounded_cent"] == "38.46"
    assert b["hourly"]["rounded_cent"] == "38.17"
    assert c["hourly"]["rounded_cent"] == "42.55"
    assert b["hourly"]["label"] == "workdays 262 x 8 = 2096 h (2024)"


def test_workdays_derivation_years():
    # la dérivation de 1fnk3cb, calculée par le CALENDRIER :
    assert payscalekit.workdays_in_year(2026) == 261
    assert payscalekit.workdays_in_year(2024) == 262
    assert payscalekit.workdays_in_year(2023) == 260


def test_weekly_pair_and_semi_monthly_hole():
    out = payscalekit.money_payscale("52000", basis="fed2087",
                                     period="semimonthly")
    p = out["periods"]["semimonthly"]
    assert p["direct"] == "2166.67"        # 52000/24 = 2166.666…
    assert p["annual_hole_direct"] == "0.08"
    assert "NOT statute" in p["direct_rule"]  # /24 = convention,
    #   pas 5504 — la ligne le dit.
    m = payscalekit.money_payscale("52000", basis="fed2087",
                                   period="monthly")
    q = m["periods"]["monthly"]
    assert q["direct"] == "4333.33"
    assert q["annual_hole_direct"] == "-0.04"
    assert "5505" in q["direct_rule"]      # « one-twelfth » : LA LOI.


def test_weekly_rate_first_vs_exact():
    out = payscalekit.money_payscale("52000", basis="fed2087",
                                     period="weekly")
    p = out["periods"]["weekly"]
    assert p["rate_first"] == "996.80"     # 24.92 x 40
    assert p["exact_rounded_once"] == "996.65"  # 52000/2087x40 =
    #   996.6460… posé à la main
    assert p["delta_rate_first_minus_exact"] == "0.15"


def test_compare_never_averages():
    out = payscalekit.money_payscale("52000", compare=True,
                                     year=2026, pto_hours="200")
    c = out["compare"]
    assert c["fed2087"]["hourly_rounded"] == "24.92"
    assert c["priv2080"]["hourly_rounded"] == "25.00"
    assert c["workdays"]["hourly_rounded"] == "24.90"   # /2088
    assert c["pto"]["hourly_rounded"] == "27.66"        # /1880
    assert c["hours"]["skipped"] == "needs hours"
    assert c["_spread"]["max_minus_min"] == "2.76"
    assert "silent average" in c["_spread"]["note"]


def test_custom_hours_contract_denominator():
    # 35 h x 52 = 1 820 — l'entrée FR, ARGUMENT, jamais encodée :
    # 45 000/1 820 = 24.72527… → 24.73 (posé à la MAIN).
    out = payscalekit.money_payscale("45000", basis="hours",
                                     hours="1820")
    assert out["hourly"]["rounded_cent"] == "24.73"
    assert out["hourly"]["label"] == "custom 1820 h"
    _refuse({"annual": "45000", "basis": "hours"}, "hours")
    _refuse({"annual": "45000", "basis": "hours", "hours": "0"},
            "hours")


def test_27_payday_years_2016_and_2027():
    # 1qh5ouz : « every 11 years » — 2016 et 2027 COMMENCENT vendredi.
    a = payscalekit.money_payscale("52000", basis="priv2080",
                                   year=2027, payday_weekday="fri")
    assert a["paydays_in_year"]["occurrences"] == 53
    assert a["paydays_in_year"]["every_other_from_first"] == 27
    assert a["paydays_in_year"]["every_other_from_second"] == 26
    b = payscalekit.money_payscale("52000", basis="priv2080",
                                   year=2016, payday_weekday="friday")
    assert b["paydays_in_year"]["occurrences"] == 53
    c = payscalekit.money_payscale("52000", basis="priv2080",
                                   year=2026, payday_weekday="fri")
    assert c["paydays_in_year"]["occurrences"] == 52
    assert c["paydays_in_year"]["every_other_from_first"] == 26


# ---------------------------------------------------- refus nommés
def test_no_silent_denominator():
    _refuse({"annual": "52000"}, "basis")          # rien de nommé
    _refuse({"annual": "52000", "basis": "calendar365"}, "basis")
    _refuse({"annual": "52000", "period": "biweekly"}, "basis")
    _refuse({"annual": "52000", "basis": "workdays"}, "year")
    _refuse({"annual": "52000", "basis": "pto"}, "pto_hours")
    _refuse({"annual": "52000", "basis": "pto",
             "pto_hours": "2100"}, "pto_hours")
    _refuse({"annual": "52000", "basis": "priv2080",
             "period": "biweekly", "order": "bankers"}, "order")
    _refuse({"annual": "abc", "basis": "priv2080"}, "annual")
    _refuse({"annual": "-5", "basis": "priv2080"}, "annual")
    _refuse({"annual": "52000", "basis": "workdays", "year": 1899},
            "year")


def test_order_absent_renders_the_pair():
    # Sans ordre forcé, biweekly rend rate_first ET direct avec
    # l'écart : la PAIRE est LE produit (prorate b119, settle b117) —
    # jamais un choix silencieux, jamais un refus qui cache le pair.
    out = payscalekit.money_payscale("52000", basis="fed2087",
                                     period="biweekly")
    assert "rate_first" in out["periods"]["biweekly"]
    assert "direct" in out["periods"]["biweekly"]
    assert "order_chosen" not in out
    named = payscalekit.money_payscale("52000", basis="fed2087",
                                       period="biweekly",
                                       order="rate_first")
    assert named["order_chosen"] == "rate_first"
    assert named["periods"]["biweekly"] == out["periods"]["biweekly"]


# ------------------------------------------------------- endpoint
def test_endpoint_200_sha_and_400_by_name():
    r = client.post(ROUTE, json={"annual": "52000",
                                 "basis": "fed2087",
                                 "period": "biweekly"})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["periods"]["biweekly"]["rate_first"] == "1993.60"
    assert "sha256" in b
    r = client.post(ROUTE, json={"annual": "52000",
                                 "basis": "calendar365"})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "basis"
    assert "365" in e["message"]
