# -*- coding: utf-8 -*-
# Bundle 137_hermes — LOT 137 : pack geodesie / trigonometrie.
# Admissions 27-11 (registre L56/L60/L61 — recus POST 6b592587,
# 4de2e8f2, 3e025c90). Les golds sont LITTERAUX de la compilation des
# rapports de campagne 26-11 : section « Terre plate / geodesie »
# (lignes 2318-2399, golds.py rendu main : tangente sqrt(2Rh+h^2), arc
# R acos(R/(R+h)), R_eff=R/(1-k), hauteur cachee exacte, Vincenty 1975
# recoupe Karney 0,1 mm) et section spatiale (lignes 1735-1962 : ombres
# ALSJ/Horizons 35.01 / 25.38 / 35.05, 2.00 a 45 degres, 0.00 a 90,
# refus a 0). Coordonnees des aeroports : OurAirports airports.csv,
# idents nommes ; la version 27-11 du CSV (sha256 b6ae8329...18aea8,
# relevee au fetch) rend les memes lignes que la version epinglee au
# rapport — les golds reproduisent au 0,001 km, verifie main.
# Consigne owner 27-11 : R et k de refraction DECLARES dans chaque
# reponse ; modele et constantes nommes ; table = version + sha.
# Le voisin sphere est DESIGNE PAR SON NOM (geo_distance) dans les cas
# de test, pas en prose.
from decimal import ROUND_HALF_UP, Decimal

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

URL_GEO = "/api/v1/geo/wgs84"
URL_HORIZON = "/api/v1/geo/horizon"
URL_SHADOW = "/api/v1/geo/shadow"

# Coordonnes OurAirports airports.csv (idents cites), lues au fetch 27-11.
FAOR = {"lat": "-26.140081", "lon": "28.246801"}   # Johannesburg
KATL = {"lat": "33.6367", "lon": "-84.428101"}     # Atlanta
SCEL = {"lat": "-33.390252", "lon": "-70.794697"}  # Santiago
YMML = {"lat": "-37.670732", "lon": "144.837898"}  # Melbourne
YSSY = {"lat": "-33.946098", "lon": "151.177002"}  # Sydney
YPPH = {"lat": "-31.94029998779297", "lon": "115.96700286865234"}
EGLL = {"lat": "51.470748", "lon": "-0.459909"}    # Londres Heathrow
KJFK = {"lat": "40.639447", "lon": "-73.779317"}
NZAA = {"lat": "-37.01199", "lon": "174.786331"}
LFPG = {"lat": "49.00896", "lon": "2.554117"}


def geo(a, b, **kw):
    body = {"from": a, "to": b}
    body.update(kw)
    return client.post(URL_GEO, json=body)


def horizon(**kw):
    return client.post(URL_HORIZON, json=kw)


def shadow(**kw):
    return client.post(URL_SHADOW, json=kw)


def km_of(distance_m):
    # le km est le decalage EXACT du metre quantifie — pas un 2e arrondi
    return Decimal(distance_m).scaleb(-3)


# ============ geodesic_wgs84_inverse — Vincenty 1975 sur WGS84 ============

def test_g1_jnb_atl_gold_literal_vs_published():
    # releve campagne G4 : JNB-ATL WGS84 = 13 581,915 km contre 13 983 publies —
    # l'ecart +401,085 km est le finding du rapport ; la porte rend le
    # gold, pas le claim.
    r = geo(FAOR, KATL, digits=0)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["distance_m"] == "13581915"
    assert str(km_of(d["distance_m"])) == "13581.915"
    assert d["ellipsoid"]["name"] == "WGS84"
    assert d["ellipsoid"]["a_m"] == "6378137"
    assert d["ellipsoid"]["f"] == "1/298.257223563"
    assert d["method"]["name"] == "Vincenty inverse"


def test_g2_sphere_neighbor_geo_distance_scl_mel_minus_23072():
    # Le contraste 0/9 du rapport : geo_distance (sphere, R rendu) est
    # faux de -23,072 km sur SCL-MEL. Les DEUX voisins jouent ici PAR
    # LEUR NOM, le meme couple de points, et l'ecat est le gold litteral.
    g = geo(SCEL, YMML, digits=0)
    sp = client.post("/api/v1/geo/distance",
                     json={"a": SCEL, "b": YMML})
    assert sp.status_code == 200, sp.text
    assert g.status_code == 200, g.text
    assert g.json()["distance_km"] == "11318.838"          # geodesique
    assert sp.json()["km"] == 11295.766                    # geo_distance
    assert str(Decimal(str(sp.json()["km"]))
               - Decimal(g.json()["distance_km"])) == "-23.072"


def test_g3_flight_golds_replayed():
    # les paires du tableau G4 (km au 0,001 — litteraux du rapport)
    for a, b, gold in ((SCEL, YSSY, "11362.395"),
                       (YPPH, EGLL, "14499.071"),
                       (FAOR, YPPH, "8324.909"),
                       (NZAA, {"lat": "25.273056", "lon": "51.608056"},
                        "14534.428"),
                       (KJFK, NZAA, "14207.516"),
                       (YPPH, LFPG, "14263.337")):
        d = geo(a, b, digits=0).json()
        assert d["distance_km"] == gold, (a, b, d["distance_km"])


def test_g4_sphere_minus_geodesic_deltas_named():
    # ecarts geo_distance - geodesic (signe du rapport) : -22,252
    # SCL-SYD, +9,121 PER-LHR, -15,379 JNB-PER.
    for a, b, delta in ((SCEL, YSSY, "-22.252"),
                        (YPPH, EGLL, "9.121"),
                        (FAOR, YPPH, "-15.379")):
        g = Decimal(geo(a, b, digits=0).json()["distance_km"])
        s = Decimal(str(client.post("/api/v1/geo/distance",
                                    json={"a": a, "b": b}).json()["km"]))
        assert str(s - g) == delta, (a, b, str(s - g))


def test_g5_equator_and_pole_anchors():
    # ancre publiee du rapport : 1 degre d'equateur = a*pi/180 =
    # 111 319,4908 m — Vincenty le rend pile (chemin equatorial = a).
    d = geo({"lat": "0", "lon": "0"}, {"lat": "0", "lon": "1"}).json()
    assert d["distance_m"] == "111319.4908"
    # pole a pole = 20 003 931,4586 m (l'ancre serie de la meme page).
    p = geo({"lat": "90", "lon": "0"}, {"lat": "-90", "lon": "0"}).json()
    assert p["distance_m"] == "20003931.4586"


def test_g6_model_block_versioned_and_hashed():
    # consigne 27-11 : modele et constantes NOMMES dans chaque reponse,
    # version + sha qui voyagent.
    d = geo(FAOR, KATL, digits=0).json()
    m = d["method"]
    assert m["name"] == "Vincenty inverse"
    assert "1975" in m["reference"]
    assert m["version"] and len(m["sha256"]) == 64
    assert d["sha256"]  # queue canonique de la porte


def test_g7_identical_points_zero():
    d = geo(SCEL, dict(SCEL)).json()
    assert d["distance_m"] == "0.0000"
    assert d["azimuth_initial_deg"] is None  # non definie, jamais devinee


def test_g8_refusals_named():
    # hors plage, PAR LE NOM ; l'ellipse refuse tout champ inconnu.
    r = client.post(URL_GEO, json={"from": {"lat": "91", "lon": "0"},
                                   "to": FAOR})
    assert r.status_code == 400
    assert any("latitude_range" in e["message"]
               for e in r.json()["errors"]), r.text
    r = client.post(URL_GEO, json={"from": FAOR, "to": KATL,
                                   "algorithm": "karney"})
    assert r.status_code == 400  # extra=forbid
    # quasi-antipodal : Vincenty ne converge pas — refus NOMME, pas un
    # silence ni un nombre fabrique.
    r = client.post(URL_GEO, json={"from": {"lat": "45", "lon": "0"},
                                   "to": {"lat": "-45", "lon": "180"}})
    assert r.status_code == 400
    assert any("vincenty_non_convergence" in e["message"]
               for e in r.json()["errors"]), r.text


# ============ horizon_hidden_height — tangente ET arc, R et k nommes ====

FT = Decimal("0.3048")   # definition 1959, exacte
MI = Decimal("1609.344")


def test_h1_hidden_height_6ft_20mi_k0_and_k13():
    # thescience360 : 6 ft observer, 20 mi — 193 ft cache (k=0),
    # 163 ft (k=0,13). Golds exacts du rapport : 58,747 m / 49,817 m.
    a = horizon(mode="hidden_height", observer_height_m="1.8288",
                distance_m="32186.88", digits=3)
    assert a.status_code == 200, a.text
    da = a.json()
    assert da["hidden_height_m"] == "58.747"
    b = horizon(mode="hidden_height", observer_height_m="1.8288",
                distance_m="32186.88", k="0.13", digits=3).json()
    assert b["hidden_height_m"] == "49.817"
    # rendu en pieds, a la precision de la page : 193 et 163.
    assert str((Decimal(da["hidden_height_m"]) / FT).quantize(
        Decimal(1), rounding=ROUND_HALF_UP)) == "193"
    assert str((Decimal(b["hidden_height_m"]) / FT).quantize(
        Decimal(1), rounding=ROUND_HALF_UP)) == "163"


def test_h2_rule_8in_per_mile_squared_is_not_hidden_height():
    # le finding viral (releve campagne G1) : la regle 8 in/mi^2 rend 267 ft a
    # 20 mi — contre 193 ft (k=0) / 163 ft (k=0,13) de hauteur cachee.
    # La regle ignore l'oeil de l'observateur ET la refraction.
    rule_ft = (Decimal(8) * Decimal(20) ** 2 / Decimal(12)).quantize(
        Decimal(1), rounding=ROUND_HALF_UP)
    assert str(rule_ft) == "267"
    hidden = Decimal(horizon(mode="hidden_height",
                             observer_height_m="1.8288",
                             distance_m="32186.88",
                             digits=3).json()["hidden_height_m"])
    hidden_ft = (hidden / FT).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    assert str(hidden_ft) == "193"
    assert rule_ft != hidden_ft  # can-fail : la regle n'est PAS cachee


def test_h3_tangent_and_arc_both_returned():
    # les DEUX definitions rendues (la faute 1 du rapport : la page
    # 517 vs la porte 518). h = 21 000 m : tangente 517,709 km -> 518,
    # arc 516,574 km — litteraux du gold.
    d = horizon(mode="horizon", observer_height_m="21000",
                digits=0).json()
    assert d["horizon"]["tangent_m"] == "517709"
    assert d["horizon"]["arc_m"] == "516574"
    assert str(km_of(d["horizon"]["arc_m"])) == "516.574"
    # faute 2 : 35 000 ft — la page dit « along the surface » (368),
    # sa propre tangente fait 369. Les deux vivent ici.
    h35 = str(Decimal(35000) * FT)
    d2 = horizon(mode="horizon", observer_height_m=h35,
                 digits=0).json()
    assert d2["horizon"]["tangent_m"] == "368843"   # -> 369 km
    assert d2["horizon"]["arc_m"] == "368432"       # -> 368,432 km


def test_h4_vanish_distance_40m_ship():
    # vaisseau de 40 m vu d'un oeil de 1,70 m, k=0,13 : evanouissement
    # a 29 193,9 m (29,2 km publie).
    d = horizon(mode="vanish_distance", observer_height_m="1.7",
                target_height_m="40", k="0.13", digits=1).json()
    assert d["vanish"]["arc_m"] == "29193.9"


def test_h5_chicago_5m_93km():
    # Gold cache : observateur 5 m a 93 km, k=0,13 -> 486,887 m (487).
    d = horizon(mode="hidden_height", observer_height_m="5",
                distance_m="93000", k="0.13", digits=3).json()
    assert d["hidden_height_m"] == "486.887"


def test_h6_r_and_k_declared_always():
    # consigne owner : R et k NOMMES dans chaque reponse — meme quand
    # ce sont les defauts, et alors applied_defaults le dit (B8).
    d = horizon(mode="horizon", observer_height_m="1.7",
                digits=3).json()
    m = d["model"]
    assert m["R_m"] == "6371000"
    assert m["k"] == "0"
    assert m["R_eff_m"] == "6371000.000000"
    assert m["refraction"] == "R_eff = R / (1 - k)"
    assert sorted(d["applied_defaults"]) == ["R_m", "k"]
    d2 = horizon(mode="horizon", observer_height_m="1.7",
                 k="0.13", R_m="6371000", digits=3).json()
    assert d2["model"]["R_eff_m"] == "7322988.505747"
    assert "applied_defaults" not in d2 or d2["applied_defaults"] == []


def test_h7_drop_definitions():
    # drop a 60 mi : parabolique 2401 ft (2R = 6371 km), exact
    # 731,736 m — le gold du rapport ; et la regle 8 in/mi^2 implique
    # R = 3960,0 mi (G4), nommee par le test, pas par la prose.
    d = horizon(mode="drop", distance_m="96560.64", digits=3).json()
    assert d["drop"]["exact_m"] == "731.736"
    parab = Decimal(d["drop"]["parabolic_m"]) / FT
    assert str(parab.quantize(Decimal(1), rounding=ROUND_HALF_UP)) == "2401"
    implied_R_mi = (Decimal(2640) * Decimal(12) / Decimal(8)).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP)  # s^2/2R = 8 in/mi^2
    assert str(implied_R_mi) == "3960.0"


def test_h8_refusals_named():
    # distance sous l'horizon : rien n'est cache — refus NOMME.
    r = horizon(mode="hidden_height", observer_height_m="1.7",
                distance_m="1000")
    assert r.status_code == 400
    assert any("distance_within_horizon" in e["message"]
               for e in r.json()["errors"]), r.text
    assert horizon(mode="teleport").status_code == 400
    assert horizon(mode="horizon", observer_height_m="-1").status_code == 400
    # k = 1 : R_eff infini — refuse PAR LE NOM
    r = horizon(mode="horizon", observer_height_m="1.7", k="1")
    assert r.status_code == 400
    assert any("refraction_k_range" in e["message"]
               for e in r.json()["errors"]), r.text
    # drop sans distance, et champ invente : 400
    assert horizon(mode="drop", observer_height_m="1.7").status_code == 400
    assert horizon(mode="horizon", observer_height_m="1.7",
                   weather="clear").status_code == 400


# ============ shadow_length_sun_elevation (campagne spatiale, recu 3e025c90) =========

def test_s1_alsj_shadow_3501():
    # ALSJ printed : LM 7,04 m a 11,37 degres -> 35 m publie,
    # gold porte : 35,01 (2 dp, HALF_UP nomme).
    d = shadow(height_m="7.04", elevation_deg="11.37",
               digits=2).json()
    assert d["shadow_length_m"] == "35.01"


def test_s2_horizons_elevations_2538_and_3505():
    # Horizons 15,502665 degres (05:43 UTC) -> 25,38 ; Horizons
    # 11,357187 (21:34:42) -> 35,05 — les deux golds ALSJ/Horizons.
    assert shadow(height_m="7.04", elevation_deg="15.502665",
                  digits=2).json()["shadow_length_m"] == "25.38"
    assert shadow(height_m="7.04", elevation_deg="11.357187",
                  digits=2).json()["shadow_length_m"] == "35.05"


def test_s3_45_degrees_is_identity():
    assert shadow(height_m="2", elevation_deg="45",
                  digits=2).json()["shadow_length_m"] == "2.00"


def test_s4_zenith_zero_and_declared():
    d = shadow(height_m="7.04", elevation_deg="90", digits=2).json()
    assert d["shadow_length_m"] == "0.00"
    assert d["model"]["formula"] == "shadow = height / tan(elevation)"
    assert d["model"]["ground"] == "level"


def test_s5_sun_below_horizon_refused_by_name():
    # le sixieme gold : refus a 0. e <= 0 ne projette rien — nomme.
    for e in ("0", "-3.5"):
        r = shadow(height_m="7.04", elevation_deg=e, digits=2)
        assert r.status_code == 400, r.text
        assert any("sun_at_or_below_horizon" in x["message"]
                   for x in r.json()["errors"]), r.text
    # zenith depasse : l'angle n'a pas de sens comme elevation
    r = shadow(height_m="7.04", elevation_deg="90.5", digits=2)
    assert r.status_code == 400
    assert any("elevation_beyond_zenith" in x["message"]
               for x in r.json()["errors"]), r.text
    assert shadow(height_m="0", elevation_deg="45").status_code == 400
    assert client.post(URL_SHADOW,
                       json={"height_m": "7.04", "elevation_deg": "45",
                             "azimuth_deg": "88"}).status_code == 400


def test_s6_digits_default_is_said():
    d = shadow(height_m="7.04", elevation_deg="11.37").json()
    assert d["shadow_length_m"] == "35.01"
    assert d["digits"]["mode"] == "HALF_UP"
    assert d["digits"]["value"] == 2
    assert "digits" in d["applied_defaults"]


# ============ fermeture des routes vides de campagne ==================

def test_r1_pain_routes_now_answer():
    # les requetes qui renvoyaient NO_MATCH (releve entree-tax : 6/9 ;
    # section spatiale §7) nomment desormais un outil du pack.
    for q, want in (("geodesic WGS84 ellipsoid", "geodesic_wgs84_inverse"),
                    ("haversine", "geodesic_wgs84_inverse"),
                    ("curvature drop", "horizon_hidden_height"),
                    ("refraction coefficient", "horizon_hidden_height"),
                    ("horizon hidden height", "horizon_hidden_height"),
                    ("shadow length from sun elevation angle tangent",
                     "shadow_length_sun_elevation"),
                    ("tangent sine cosine trigonometry degrees",
                     "shadow_length_sun_elevation")):
        r = client.get("/route", params={"q": q})
        assert r.status_code == 200
        names = [e["tool"] for e in r.json()["tools"]]
        assert want in names, (q, names)
