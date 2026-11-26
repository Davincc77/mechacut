# -*- coding: utf-8 -*-
"""Bundle 119 — /money/prorate CONVENTIONS NOMMEES.

La guerre du prorata de loyer est publique, pas privee : six fils ont
ete lus AU SOURCE (26-11) et chacun publie une convention que les
calculateurs taisent :

  - r/personalfinance 9sqw2j : deux formules dans un seul fil —
    "1000/30 = 33.33 per day ... x 18 = 600" (le poseur arrondit SON
    resultat en silence : 33.33 x 18 = 599.94) et "[19/30]x[1229]"
    (autre borne, autre ordre).
  - r/Landlord 1hitzjq : "banker's month" — /30 "REGARDLESS of actual
    number of days" — l'office facture 566 pour 17 jours de janvier
    (mois de 31) ; le commentaire /31 rend 548.38 (arrondi humain —
    notre rendu nomme son mode : 548.39 half_up).
  - r/RealEstate 1idq3vr : la regle publiee "(annual rent / 365) x 22".
  - r/personalfinance cevz6l + r/legaladvice 66vwu9 : fin de bail a
    MIDI — 12 factures, 11,5 plaide, AUCUN fil ne calcule en demi-jours.
  - r/personalfinance 1b5p04y : "prorated" = deux OBJETS differents
    selon le bail (partiel du mois d'entree / delta fin-de-bail ->
    fin-de-mois), memes dates.

Attendus CALCULES A LA MAIN (ou oracle Fraction) ci-dessous — jamais
recopies du module. Les vecteurs legacy sont geles OCTET POUR OCTET
(contrat miroir de settle/b117).
"""

from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

from fastapi.testclient import TestClient

import money
import main

client = TestClient(main.app)

PATH = "/api/v1/money/prorate"

BASE = {"amount": "1000", "cycle_start": "2018-11-01",
        "cycle_end": "2018-11-30", "service_start": "2018-11-01",
        "service_end": "2018-11-18"}


def _deterministic(payload):
    r1 = client.post(PATH, json=payload)
    r2 = client.post(PATH, json=payload)
    assert r1.status_code == r2.status_code
    assert r1.content == r2.content
    return r1


def test_legacy_defaults_byte_identical():
    # GEL b118 (mesure AVANT edition, cycle b119) : les trois vecteurs
    # du corpus rendent le dictionnaire exact d'avant le bundle.
    v1 = money.money_prorate("1000", "2018-11-01", "2018-11-30",
                             "2018-11-01", "2018-11-18")
    assert v1 == {
        "amount": "1000", "covered_days": 18, "cycle_days": 30,
        "exact_decimal": "600.000000000000", "inclusive": True,
        "mode": "half_up", "places": 2, "prorated": "600.00",
        "ratio": {"denominator": 30, "numerator": 18},
    }, v1
    v2 = money.money_prorate("1229", "2018-11-01", "2018-11-30",
                             "2018-11-01", "2018-11-19")
    assert v2["prorated"] == "778.37"          # 23351/30 = 778.3666.. -> .37
    assert "basis" not in v2 and "order" not in v2
    assert "conventions" not in v2 and "daily_rounded" not in v2
    v3 = money.money_prorate("1200", "2026-01-01", "2026-01-31",
                             "2026-01-15", "2026-02-02", clamp=False)
    assert v3["covered_days"] == 19            # 17 janv + 2 fev
    assert v3["prorated"] == "735.48"          # 22800/31 = 735.4838.. -> .48
    assert v3["exact_decimal"] == "735.483870967742"


def test_landlord_quotient_9sqw2j():
    # Le fil publie la FORMULE du bailleur : daily = 1000/30 arrondi a
    # 33.33, x 18 = 599.94. Notre rendu nomme l'ordre et montre le
    # taux multiplie.
    r = _deterministic(dict(BASE, order="quotient"))
    b = r.json()
    assert r.status_code == 200, b
    assert b["prorated"] == "599.94"           # 33.33 x 18, exact a 2
    assert b["daily_rounded"] == "33.33"
    assert b["basis"] == "cycle" and b["order"] == "quotient"
    # product reste la loi de base : 1000 x 18/30 = 600.00 exactement.
    assert _deterministic(BASE).json()["prorated"] == "600.00"


def test_compare_pair_signed_delta_1229():
    # 9sqw2j autre formule : [19/30] x [1229].
    #   product  = 1229 x 19/30 = 23351/30 = 778.3666.. -> 778.37
    #   daily    = 1229/30 = 40.9666.. -> 40.97 ; x19 = 778.43
    #   delta (product - quotient) = 778.37 - 778.43 = -0.06
    r = _deterministic({"amount": "1229", "cycle_start": "2018-11-01",
                        "cycle_end": "2018-11-30",
                        "service_start": "2018-11-01",
                        "service_end": "2018-11-19", "compare": True})
    conv = r.json()["conventions"]
    assert conv["orders"] == {
        "product": "778.37", "quotient": "778.43",
        "delta_product_minus_quotient": "-0.06", "chosen": "product",
    }, conv["orders"]
    # 1b5p04y : les DEUX objets du meme mot, somme identique.
    assert conv["objects"] == {
        "occupied": "778.37",
        "unoccupied": "450.63",                # 1229 - 778.37
        "amount": "1229", "sum_equals_amount": True,
    }, conv["objects"]


def test_bankers_month_1hitzjq():
    # Janvier (31 reels), entree le 15 -> covered 15..31 = 17 jours.
    #   cycle   : 1000 x 17/31 = 548.387096.. -> 548.39 half_up
    #   month30 : 1000 x 17/30 = 566.6666..    -> 566.67
    #   month30 quotient : daily 33.33 x 17    -> 566.61
    #   year365 : 1000 x 204/365 = 558.9041..  -> 558.90
    jan = {"amount": "1000", "cycle_start": "2026-01-01",
           "cycle_end": "2026-01-31", "service_start": "2026-01-15",
           "service_end": "2026-01-31"}
    assert _deterministic(jan).json()["prorated"] == "548.39"
    m30 = _deterministic(dict(jan, basis="month30")).json()
    assert m30["prorated"] == "566.67"
    assert m30["ratio"] == {"numerator": 17, "denominator": 30}
    assert m30["cycle_days"] == 31             # les deux chiffres honnetes
    q30 = _deterministic(dict(jan, basis="month30",
                              order="quotient")).json()
    assert q30["prorated"] == "566.61" and q30["daily_rounded"] == "33.33"
    y = _deterministic(dict(jan, basis="year365")).json()
    assert y["prorated"] == "558.90"
    assert y["ratio"] == {"numerator": 204, "denominator": 365}  # 17x12


def test_year365_february_1idq3vr():
    # Fevrier 2026 (28), window 1..22 -> covered 22.
    #   cycle   : 1000 x 22/28 = 785.7142.. -> 785.71
    #   month30 : 1000 x 22/30 = 733.3333.. -> 733.33
    #   year365 : 1000 x 264/365 = 723.2876.. -> 723.29
    feb = {"amount": "1000", "cycle_start": "2026-02-01",
           "cycle_end": "2026-02-28", "service_start": "2026-02-01",
           "service_end": "2026-02-22"}
    assert _deterministic(feb).json()["prorated"] == "785.71"
    assert _deterministic(dict(feb, basis="month30")) \
        .json()["prorated"] == "733.33"
    y = _deterministic(dict(feb, basis="year365")).json()
    assert y["prorated"] == "723.29"
    assert y["ratio"] == {"numerator": 264, "denominator": 365}


def test_bound_moves_both_counts():
    # inclusive=False = "move-out day NOT counted" (1fep9e6) : borne
    # sur les DEUX comptes. 1229, Nov : cycle 30->29... non —
    # span 0 : cycle_days = 29, covered = 18.
    #   product : 1229 x 18/29 = 762.8275.. -> 762.83
    #   quotient: 1229/29 = 42.3793.. -> 42.38 ; x18 = 762.84
    body = {"amount": "1229", "cycle_start": "2018-11-01",
            "cycle_end": "2018-11-30", "service_start": "2018-11-01",
            "service_end": "2018-11-19", "inclusive": False,
            "compare": True}
    b = _deterministic(body).json()
    assert b["cycle_days"] == 29 and b["covered_days"] == 18
    assert b["conventions"]["orders"] == {
        "product": "762.83", "quotient": "762.84",
        "delta_product_minus_quotient": "-0.01", "chosen": "product",
    }, b["conventions"]["orders"]


def test_noon_lease_refused_with_two_readings():
    # cevz6l : 'ends at noon on the 12th' — 1500, Aout (31),
    # service 1..12. inclusive=True  : covered 12, 1500x12/31 =
    #   580.645161.. -> 580.65
    # inclusive=False : cycle 30, covered 11 -> 1500x11/30 = 550.00
    r = client.post(PATH, json={
        "amount": "1500", "cycle_start": "2018-08-01",
        "cycle_end": "2018-08-31", "service_start": "2018-08-01",
        "service_end": "2018-08-12T12:00"})
    assert r.status_code == 400
    e = r.json()["errors"][0] if "errors" in r.json() else r.json()[
        "detail"][0]
    assert e["field"] == "service_end"
    assert "REFUSED_DAY_GRAIN" in e["message"]
    assert e["readings"] == {"move_out_day_counted": "580.65",
                             "move_out_day_free": "550.00"}, e
    assert "11.5" in e["message"]  # la phrase publiee est citee


def test_epoch_and_rfc_refused_no_guessed_readings():
    # Un epoch n'a pas de PARTIE Date honnete sans deviner un fuseau :
    # refus, PAS de readings inventees.
    for bad in ("1795684593", "Mon, 12 Aug 2018 12:00:00 GMT"):
        r = client.post(PATH, json={
            "amount": "1500", "cycle_start": "2018-08-01",
            "cycle_end": "2018-08-31", "service_start": "2018-08-01",
            "service_end": bad})
        assert r.status_code == 400, bad
        j = r.json()
        e = (j["errors"] if "errors" in j else j["detail"])[0]
        assert "REFUSED_DAY_GRAIN" in e["message"], bad
        assert "readings" not in e, bad


def test_closed_sets_refused_by_name():
    # basis et order sont des ENSEMBLES FERMES publiés — le refus nomme
    # les membres. (La porte pydantic refuse avant ; le module refuse
    # aussi pour les appelants directs.)
    for body, field in ((dict(BASE, basis="monthly31"), "basis"),
                        (dict(BASE, order="first"), "order")):
        r = client.post(PATH, json=body)
        assert r.status_code == 400
        assert any(field in str(x.get("loc", x)) for x in
                   (r.json().get("errors") or r.json().get("detail"))), \
            (field, r.text)
    try:
        money.money_prorate("1000", "2018-11-01", "2018-11-30",
                            "2018-11-01", "2018-11-18", basis="real31")
        raise AssertionError("closed set must raise")
    except money.MoneyError as e:
        assert "month30" in str(e)


def test_objects_identity_decimal_amount():
    # amount a centimes : 1229.50 x 19/30 = 778.6833.. -> 778.68 ;
    # unoccupied = 1229.50 - 778.68 = 450.82 ; somme == amount.
    b = _deterministic({
        "amount": "1229.50", "cycle_start": "2018-11-01",
        "cycle_end": "2018-11-30", "service_start": "2018-11-01",
        "service_end": "2018-11-19", "compare": True}).json()
    o = b["conventions"]["objects"]
    assert o["occupied"] == "778.68" and o["unoccupied"] == "450.82"
    assert o["amount"] == "1229.50" and o["sum_equals_amount"] is True


def test_fraction_oracle_vs_module():
    # ORACLE INDEPENDANT (fractions entieres, jamais le chemin Decimal
    # du module) : 1234.56 fevrier, window 3..20 -> covered 18/28.
    # 1234.56 x 18 / 28 = 22222.08/28 = 793.645714285.. -> 793.65
    got = _deterministic({
        "amount": "1234.56", "cycle_start": "2026-02-01",
        "cycle_end": "2026-02-28", "service_start": "2026-02-03",
        "service_end": "2026-02-20"}).json()
    exact = Fraction(123456, 100) * 18 / 28
    want = (Decimal(exact.numerator) / Decimal(exact.denominator)
            ).quantize(Decimal("0.01"), ROUND_HALF_UP)
    assert got["prorated"] == format(want, "f") == "793.65", got
    # year365 oracle : 1234.56 x 216/365 = 266664.96/365 =
    # 730.5889315.. -> 730.59 (le 730.23 d'un premier calcul a la main
    # etait FAUX — verifie a deux fois, oracle Fraction independant).
    got2 = _deterministic({
        "amount": "1234.56", "cycle_start": "2026-02-01",
        "cycle_end": "2026-02-28", "service_start": "2026-02-03",
        "service_end": "2026-02-20", "basis": "year365"}).json()
    exact2 = Fraction(123456, 100) * (18 * 12) / 365
    want2 = (Decimal(exact2.numerator) / Decimal(exact2.denominator)
             ).quantize(Decimal("0.01"), ROUND_HALF_UP)
    assert got2["prorated"] == format(want2, "f") == "730.59", got2
