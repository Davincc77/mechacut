# -*- coding: utf-8 -*-
"""bundle123 — /api/v1/stats/rate-ci : l'intervalle de Wilson, a la porte.

Ne vient pas de la theorie : vient du recensement LATAM (vague 3), ou
neuf agents ont calcule des taux « k of n » a la main — le 65,2 % a ete
rendu trois fois avant de devenir un outil. Le gold 1 EST le chiffre du
case study (720/1105 = 65,2 [62,3-67,9], docs/corpus/wave3-latam-census).

Attendus CALCULES A LA MAIN (z = 1,96 exact, Decimal) — jamais recopies
du module :

G1 k=720 n=1105 : p = 0,65158371 ; z2 = 3,8416 ; denom = 1 + z2/n
   = 1,00347656 ; centre = (p + z2/2n)/denom = (0,65158371 +
   0,00173802)/1,00347656 = 0,65094... -> 65,1 ;
   interieur = p(1-p)/n + z2/4n2 = 0,00020578 + 0,00000087 =
   0,00020665 ; racine = 0,014375 ; demi = 1,96 x 0,014375 /
   1,00347656 = 0,028078 ; bornes brutes [0,62287 ; 0,67902] ->
   [62,3 ; 67,9] ; observe = 720/1105 = 0,65158371 -> 65,2.

G2 k=0 n=600 : p=0 ; centre = (z2/2n)/(1 + z2/n) = 0,00320133/
   1,00640267 = 0,003181 -> 0,3 ; demi = 1,96 x sqrt(0 + 3,8416/
   1440000)/1,0064 = 1,96 x 0,001633/1,00640267 = 0,003181 ;
   borne basse brute = -0,00000017 -> PLAFONNEE A 0,0 (un taux ne
   descend pas sous 0) ; borne haute = 0,006362 -> 0,6.
   Le naive dirait « 0,00 % de risque » — la porte dit 0,3 [0,0-0,6].

G3 k=1 n=10 : p=0,1 ; centre = (0,1 + 0,19208)/1,38416 = 0,21101
   -> 21,1 ; interieur = 0,009 + 0,009604 = 0,018604 ; racine =
   0,136396 ; demi = 1,96 x 0,136396/1,38416 = 0,19315 ; bornes
   brutes [0,017862 ; 0,404165] -> [1,8 ; 40,4]. Observe -> 10,0.

G4 k=9 n=10 (symetrie de G3 verifiee a la main, pas au module) :
   p=0,9 ; centre = (0,9 + 0,19208)/1,38416 = 0,78899 -> 78,9 ;
   p(1-p) identique -> demi identique ; bornes brutes
   [0,595835 ; 0,982138] -> [59,6 ; 98,2]. Observe -> 90,0.
   Test d'invariant : centre(9/10) = 100 - centre(1/10) exactement
   a 0,1 pres, et borne_low(9/10) = 100 - borne_high(1/10).

Nommage : k = succes entiers >= 0 ; n = essais entiers >= 1 ; k <= n.
Bornes brutes plafonnees a [0, 1] AVANT arrondi (jamais apres :
G2 le prouve — arrondi apres plafond, pas plafond apres arrondi).
Pourcentages rendus a 0,1 pres, ROUND_HALF_EVEN — meme regle que
money. observed_pct = k/n brut, JAMAIS remplace par le centre :
l'outil rend les DEUX et les nomme — la confusion des deux est la
maladie que cet outil tue.
"""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def ci(k, n):
    r = client.post("/api/v1/stats/rate-ci", json={"k": k, "n": n})
    assert r.status_code == 200, r.text
    return r.json()


def test_g1_census_latam():
    out = ci(720, 1105)
    assert out["observed_pct"] == "65.2"
    assert out["wilson_center_pct"] == "65.1"
    assert out["lower_pct"] == "62.3"
    assert out["upper_pct"] == "67.9"


def test_g2_zero_k():
    out = ci(0, 600)
    assert out["observed_pct"] == "0.0"
    assert out["wilson_center_pct"] == "0.3"
    assert out["lower_pct"] == "0.0"
    assert out["upper_pct"] == "0.6"


def test_g3_one_of_ten():
    out = ci(1, 10)
    assert out["observed_pct"] == "10.0"
    assert out["wilson_center_pct"] == "21.1"
    assert out["lower_pct"] == "1.8"
    assert out["upper_pct"] == "40.4"


def test_g4_symmetry():
    a, b = ci(1, 10), ci(9, 10)
    assert b["observed_pct"] == "90.0"
    assert b["wilson_center_pct"] == "78.9"
    assert b["lower_pct"] == "59.6"
    assert b["upper_pct"] == "98.2"
    assert float(b["wilson_center_pct"]) == 100.0 - float(a["wilson_center_pct"])
    assert float(b["lower_pct"]) == round(100.0 - float(a["upper_pct"]), 1)


def test_can_fail_observed_never_equals_center_when_far():
    # 1/10 : un module qui confondrait observe et centre echoue ici
    out = ci(1, 10)
    assert out["observed_pct"] != out["wilson_center_pct"]


def test_rejects_bad_input():
    for payload in ({"k": -1, "n": 10}, {"k": 1, "n": 0}, {"k": 11, "n": 10}):
        r = client.post("/api/v1/stats/rate-ci", json=payload)
        assert r.status_code == 400, (payload, r.text)
        d = r.json()
        # grammaire du voisinage : la famille validateurs (4659-4788)
        # refuse en "check_failed" — le refus porte un message-reparation
        assert d["error"] == "check_failed", d
        assert d["errors"], d
        assert d["errors"][0].get("expected"), d
