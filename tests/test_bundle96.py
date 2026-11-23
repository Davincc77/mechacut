"""Bundle 96 — /shop/pricedrop-refund : pilier 3 du trio boutique.

Golds TRACÉS À LA MAIN (calcul date + Decimal au brouillon, avant
implémentation), jamais recopiés du module ; dictées de routage à
scores recomptés à la main sous la règle publiée (tag=3, segment de
nom=4, purpose=2, plancher 4).
"""
import sys
sys.path.insert(0, ".")
import pricedroprefundkit as k
import routing
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)
E = "/api/v1/shop/pricedrop-refund"


# ---------------------------------------------------------------- goulots
def _refuse(**kw):
    try:
        k.pricedrop_refund(**kw)
        raise AssertionError("should have refused: %r" % (kw,))
    except k.PriceDropError as e:
        return e


def test_target_holiday_main_golden():
    # main: 20-11 -> 10-12, les deux avant le 24-12 ; écart 20,00 ;
    # butée publiée : 24 décembre.
    r = k.pricedrop_refund("target", "2026-11-20", "2026-12-10",
                           "100.00", "80.00", as_of="2026-11-25")
    assert r["eligible"] is True
    assert r["claim_by"] == "2026-12-24"
    assert r["claim_by_weekday"] == "Thursday"
    assert r["refund_amount"] == "20.00"
    assert r["rule_applied"] == "holiday-own-price-window"
    assert r["days_left"] == 29        # 25-11 -> 24-12 : 5+30+24-... :
    # nov: 5 jours restants (26..30), déc: 24 -> 29 — recalcul main.
    assert r["currency"] == "USD"
    assert "standard_fallback" in r


def test_target_standard_14_and_late_drop():
    r = k.pricedrop_refund("target", "2026-10-01", "2026-10-10",
                           "100.00", "95.00")
    assert (r["claim_by"], r["rule_applied"], r["refund_amount"]) == \
        ("2026-10-14", "standard-14-day", "5.00")
    # baisse trop tard : les DEUX fenêtres disent pourquoi.
    r2 = k.pricedrop_refund("target", "2026-11-20", "2026-12-26",
                            "100.00", "80.00")
    assert not r2["eligible"] and len(r2["reasons"]) == 2


def test_bestbuy_double_regime_and_day1():
    # main: réception 22-12 +15j -> 05-01 ; holiday claim -> 15-01 ;
    # le plus tardif des DEUX régimes publiés, jamais un mélange.
    r = k.pricedrop_refund("best buy", "2026-12-20", "2027-01-05",
                           "200.00", "160.00",
                           delivery_date="2026-12-22",
                           as_of="2026-12-28")
    assert r["claim_by"] == "2027-01-15" and r["refund_amount"] == \
        "40.00" and r["days_left"] == 18
    # membre 60 j depuis réception 22-12 : Day-1 publié -> +59 = 19-02.
    m = k.pricedrop_refund("bestbuy", "2026-12-20", "2027-01-05",
                           "200.00", "160.00", membership=True,
                           delivery_date="2026-12-22")
    assert m["claim_by"] == "2027-02-19"
    assert m["claim_by_weekday"] == "Friday"
    assert "Day-1" in m["counting_convention"]


def test_bestbuy_requires_delivery_event_and_marketplace():
    e = _refuse(retailer="bestbuy", purchase_date="2026-11-05",
                drop_date="2026-11-20", purchase_price="100.00",
                new_price="80.00")
    assert e.field == "delivery_date"
    ev = k.pricedrop_refund("bestbuy", "2026-11-05", "2026-11-30",
                            "100.00", "80.00", delivery_date="2026-11-07",
                            drop_is_event_pricing=True)
    assert not ev["eligible"]
    assert ev["rule_applied"] == "event-pricing-excluded"
    mp = k.pricedrop_refund("bestbuy", "2026-11-05", "2026-11-06",
                            "100.00", "80.00", delivery_date="2026-11-05",
                            channel="marketplace")
    assert not mp["eligible"]
    # le CONFLIT publié : match concurrent suspendu 19-30 nov,
    # ajustement propre prix courant toujours.
    assert any("SUSPENDED Nov 19" in c for c in mp["conflicts"])


def test_costco_double_window_verbatim():
    r = k.pricedrop_refund("costco", "2026-11-25", "2026-12-15",
                           "50.00", "40.00")
    assert r["claim_by"] == "2026-12-24"      # 25-11 + 29 jours
    assert r["rule_applied"] == "thirty-day-window"
    assert any("BOTH the promo dates" in c or
               "SALE-DATED" in c for c in r.get("needs_check", []))
    p = k.pricedrop_refund("costco", "2026-11-25", "2026-12-15",
                           "50.00", "40.00", promo_start="2026-11-26",
                           promo_end="2026-12-01")
    assert not p["eligible"] and p["claim_by"] == "2026-12-01"
    q = k.pricedrop_refund("costco", "2026-11-25", "2026-11-30",
                           "50.00", "40.00", promo_start="2026-11-26",
                           promo_end="2026-12-31")
    assert q["eligible"] and q["claim_by"] == "2026-12-24"
    # min(fenêtre 30 j = 24-12, promo fermée 31-12) : la double
    # fenêtre publiée est le MINIMUM des deux, jamais la plus large.


def test_apple_double_clock_is_the_earlier():
    # réception 28-11 -> +14 = 11-12 ; baisse 05-12 -> +14 = 18-12 ;
    # la butée publiée est la PLUS PROCHE des deux horloges.
    r = k.pricedrop_refund("apple", "2026-11-27", "2026-12-05",
                           "199.00", "149.00", delivery_date="2026-11-28")
    assert r["claim_by"] == "2026-12-11"
    assert r["refund_amount"] == "50.00"
    bf = k.pricedrop_refund("apple", "2026-11-27", "2026-12-05",
                            "199.00", "149.00", delivery_date="2026-11-28",
                            drop_is_event_pricing=True)
    assert not bf["eligible"]


def test_fnac_darty_campagne_et_deux_cartes():
    f = k.pricedrop_refund("fnac", "2026-11-05", "2026-11-28",
                           "100.00", "80.00", as_of="2026-11-25")
    assert f["eligible"] is True
    assert f["claim_by"] == "2026-11-30"
    assert f["refund_amount"] == "20.00"
    assert f["currency"] == "EUR"
    assert "carte cadeau Fnac" in f["mode"] and "NOT cash" in f["mode"]
    assert f["days_left"] == 5
    d = k.pricedrop_refund("darty", "2026-11-05", "2026-11-28",
                           "100.00", "80.00")
    assert "carte cadeau Darty" in d["mode"]
    hors = k.pricedrop_refund("darty", "2026-12-01", "2026-12-05",
                              "100.00", "80.00")
    assert not hors["eligible"] and hors["claim_by"] == "2026-11-30"
    e = _refuse(retailer="fnac", purchase_date="2026-11-05",
                drop_date="2026-11-28", purchase_price="100.00",
                new_price="80.00", channel="marketplace")
    assert e.field == "channel" and "hors marketplace" in e.message
    g = _refuse(retailer="fnac-darty", purchase_date="2026-11-05",
                drop_date="2026-11-28", purchase_price="100.00",
                new_price="80.00")
    assert g.field == "retailer"


def test_amazon_walmart_rien_publie_et_le_levier():
    a = k.pricedrop_refund("amazon", "2026-11-27", "2026-11-29",
                           "100.00", "70.00")
    assert not a["eligible"] and a["mode"] == "none"
    assert "/api/v1/shop/return-deadline" in a["lever"]
    w = k.pricedrop_refund("walmart", "2026-11-27", "2026-11-29",
                           "100.00", "70.00")
    assert not w["eligible"] and "CHECKOUT" in w["reasons"][1]


def test_homedepot_30j_et_event():
    r = k.pricedrop_refund("homedepot", "2026-11-20", "2026-12-10",
                           "100.00", "90.00")
    assert r["eligible"] and r["claim_by"] == "2026-12-19"
    ev = k.pricedrop_refund("homedepot", "2026-11-20", "2026-12-10",
                            "100.00", "90.00",
                            drop_is_event_pricing=True)
    assert not ev["eligible"]


def test_gates_transverses():
    z = k.pricedrop_refund("target", "2026-11-20", "2026-11-25",
                           "100.00", "100.00")
    assert not z["eligible"] and z["refund_amount"] == "0.00"
    assert z["rule_applied"] == "arithmetic-gate"
    e = _refuse(retailer="target", purchase_date="2026-11-20",
                drop_date="2026-11-10", purchase_price="100.00",
                new_price="80.00")
    assert e.field == "drop_date" and "discount-audit" in e.message
    s = _refuse(retailer="target", purchase_date="2025-11-20",
                drop_date="2025-12-01", purchase_price="100.00",
                new_price="80.00")
    assert s.field == "purchase_date"
    m = _refuse(retailer="target", purchase_date="2026-11-20",
                drop_date="2026-11-25", purchase_price="100.00",
                new_price="80.00", membership=True)
    assert m.field == "membership"
    p = _refuse(retailer="target", purchase_date="2026-11-20",
                drop_date="2026-11-25", purchase_price="100.00",
                new_price="80.00", promo_start="2026-11-01")
    assert p.field == "promo_start"
    # single-source : le refus PORTE le fait candidat.
    mc = _refuse(retailer="macy's", purchase_date="2026-11-20",
                 drop_date="2026-11-25", purchase_price="100.00",
                 new_price="80.00")
    assert "Nov 12" in mc.message and "ONE source" in mc.message
    cu = _refuse(retailer="currys", purchase_date="2026-11-20",
                 drop_date="2026-11-25", purchase_price="100.00",
                 new_price="80.00")
    assert "thinkmoney" in cu.message


# ---------------------------------------------------------------- wire
def test_endpoint_200_with_sha():
    r = client.post(E, json={"retailer": "target",
                             "purchase_date": "2026-11-20",
                             "drop_date": "2026-12-10",
                             "purchase_price": "100.00",
                             "new_price": "80.00"})
    assert r.status_code == 200
    j = r.json()
    assert j["eligible"] and j["refund_amount"] == "20.00"
    from main import canon
    body = dict(j)
    del body["sha256"]
    assert j["sha256"] == canon(body)


def test_endpoint_400_carries_field_and_expected():
    r = client.post(E, json={"retailer": "bestbuy",
                             "purchase_date": "2026-11-05",
                             "drop_date": "2026-11-20",
                             "purchase_price": "100.00",
                             "new_price": "80.00"})
    assert r.status_code == 400
    err = r.json()["errors"][0]
    assert err["field"] == "delivery_date"
    assert "expected" in err


def test_endpoint_extra_field_refused_and_free():
    r = client.post(E, json={"retailer": "target",
                             "purchase_date": "2026-11-20",
                             "drop_date": "2026-11-25",
                             "purchase_price": "100.00",
                             "new_price": "80.00",
                             "surprise": 1})
    assert r.status_code == 400
    import payments
    assert E not in payments.PRICES      # tier free


# ---------------------------------------------------------------- route
# scores recomptés à la main : tag=3, nom/path segment=4, purpose=2.
DICTEES = [
    # FR : fnac3 + prix3 + difference3 = 9
    ("j'ai acheté 100 € à la Fnac, le prix est passé à 80, qui me "
     "rembourse la différence", "shop_pricedrop_refund", 9),
    # EN : price3 + dropp3 + difference3 + who2 + owe2 = 13
    ("i paid 100 at best buy and the price dropped to 80 last week "
     "— who owes me the difference", "shop_pricedrop_refund", 13),
    # majuscules + accents mélangés : 6 mots tag = 18 (le pli b95
    # plie l'orthographe, la grammaire des nombres reste la mienne)
    ("PRIX BAISSE APRES ACHAT REMBOURSEMENT DIFFÉRENCE fnac",
     "shop_pricedrop_refund", 18),
    # PT : fnac3 + diferenca3 = 6
    ("comprei por 100 na fnac e caiu para 80, quem me devolve a "
     "diferenca", "shop_pricedrop_refund", 6),
]


def test_dictées_pilar3():
    for q, tool, score in DICTEES:
        top = routing.route(q, top=3)
        assert top and top[0]["tool"] == tool, q
        assert top[0]["score"] == score, (q, top)


def test_frontiere_avec_return_deadline_et_garde_b95():
    t = routing.route("can I still return the TV I bought at target, "
                      "until when", top=2)
    assert t[0]["tool"] == "shop_return_deadline"
    assert t[0]["score"] > next(x["score"] for x in t
                                if x["tool"] == "shop_pricedrop_refund")
    # garde b95 : la dictée du prix barré reste discount_audit top-1.
    d = routing.route("c'est quoi un prix barré légal", top=1)
    assert d[0]["tool"] == "shop_discount_audit" and d[0]["score"] == 9


def test_radar_corpus_rows_present():
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                    "..", "scripts"))
    import route_radar as rr
    wants = [w for _, w in rr.CASES if w == "pricedrop"]
    assert len(wants) == 4
    assert any(w == "return_deadline" for _, w in rr.CASES)
