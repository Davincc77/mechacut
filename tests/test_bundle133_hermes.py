# Bundle 133_hermes — LOT 133 : easter_computus + maya_long_count (v1.57.0).
# Admissions 27-11 (registre L63 reçu 30b0983b, L64 reçu b3026c7c), amas
# P-D du triage. Les blobs de la synthèse n'ont pas été consignés sur
# disque (stored:false, trou connu — précédent 135) : les golds viennent
# des assertions CONSIGNÉES du rapport de campagne (COMPIL_RAPPORTS_VAGUE2,
# section clic 133) et des tables d'exemple PUBLIÉES des algorithmes
# eux-mêmes (Date of Easter : worked examples Nature 1876 / Butcher 1877 /
# Meeus 1991 pour le grégorien, Meeus AA 1991 p.69 pour le julien ;
# Mesoamerican Long Count calendar : table des corrélations 584283/584285
# et règle publiée « the second digit from the right rolls over to zero
# when it reaches 18 »), recopiées, jamais inventées. Le pont JDN est
# REJOUE depuis juliankit (bundle 135, même table centurielle, même
# corrélation 584283 déjà gold) — cohérence exigée entre les deux outils,
# testée en seam, pas citée en prose.
#
# ÉCART CONSIGNÉ : la ligne « uinal range 0..19 » de la matière de
# campagne contredit SA PROPRE gold 12.19.19.17.19 (uinal 17) et la règle
# publiée base-18 (18 uinal = 1 tun). La règle publiée fait foi : uinal
# est borné à 17 ici, refus NOMMÉ au-delà — le refus « uinal 20 » du blob
# est couvert, et la dérive 18/19 meurt aussi par son nom.
import json

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def easter(body):
    return client.post("/api/v1/date/easter-computus", json=body)


def julian(body):
    return client.post("/api/v1/date/julian-gregorian", json=body)


# ============ easter_computus — table publiée Nature/Butcher/Meeus ============

def test_e1_1961_published_intermediates():
    # La colonne Y=1961 de la table publiée, recopiée LITTÉRALEMENT :
    # a=4 b=19 c=61 d=4 e=3 f=1 g=6 h=10 i=15 k=1 l=1 m=0 n=4 o=1
    # -> 2 April 1961. L'or est la table, pas la datasheet.
    r = easter({"year": 1961, "algorithm": "gregorian_meeus_butcher"})
    assert r.status_code == 200
    d = r.json()
    assert d["easter_gregorian"] == "1961-04-02"
    assert d["intermediates"] == {
        "a": 4, "b": 19, "c": 61, "d": 4, "e": 3, "f": 1, "g": 6,
        "h": 10, "i": 15, "k": 1, "l": 1, "m": 0, "n": 4, "o": 1}
    assert d["golden_number"] == 5  # (1961 mod 19) + 1, formule publiée


def test_e2_2026_2027_published_columns():
    a = easter({"year": 2026, "algorithm": "gregorian_meeus_butcher"}).json()
    b = easter({"year": 2027, "algorithm": "gregorian_meeus_butcher"}).json()
    assert a["easter_gregorian"] == "2026-04-05"
    assert a["intermediates"]["h"] == 12 and a["intermediates"]["l"] == 2
    assert a["intermediates"]["n"] == 4 and a["intermediates"]["o"] == 4
    assert b["easter_gregorian"] == "2027-03-28"
    assert b["intermediates"]["h"] == 1 and b["intermediates"]["l"] == 5
    assert b["intermediates"]["n"] == 3 and b["intermediates"]["o"] == 27


def test_e3_2012_pair_consigned():
    # COMPIL section clic 133 (B3) : « Western Easter 2012-04-08 and
    # Orthodox Pascha 2012-04-15 (Julian 2012-04-02 + 13) are both
    # Sundays, 7 days apart ». Les deux algorithmes, les deux visages.
    w = easter({"year": 2012, "algorithm": "gregorian_meeus_butcher"}).json()
    o = easter({"year": 2012, "algorithm": "julian_meeus"}).json()
    assert w["easter_gregorian"] == "2012-04-08"
    assert w["easter_julian"] == "2012-03-26"   # même jour, visage julien
    assert w["jdn"] == 2456026
    assert o["easter_julian"] == "2012-04-02"
    assert o["easter_gregorian"] == "2012-04-15"
    assert o["jdn"] == 2456033
    assert o["offset_days"] == 13
    assert w["weekday"]["iso"] == 7 and o["weekday"]["iso"] == 7


def test_e4_2014_coincidence_consigned():
    # « they coincide in 2014 (both 2014-04-20) » (COMPIL §5.1).
    w = easter({"year": 2014, "algorithm": "gregorian_meeus_butcher"}).json()
    o = easter({"year": 2014, "algorithm": "julian_meeus"}).json()
    assert w["easter_gregorian"] == o["easter_gregorian"] == "2014-04-20"
    assert w["jdn"] == o["jdn"] == 2456768


def test_e5_2025_contraction():
    # Contrat du lot, vérifié sur sources closes : Paque 2025 = 2025-04-20
    # a l'OUEST (gregorien) ET a l'EST (julien 2025-04-07 + pont -> meme
    # jour civil). Comptes dits dans le rapport.
    w = easter({"year": 2025, "algorithm": "gregorian_meeus_butcher"}).json()
    o = easter({"year": 2025, "algorithm": "julian_meeus"}).json()
    assert w["easter_gregorian"] == "2025-04-20"
    assert o["easter_julian"] == "2025-04-07"
    assert o["easter_gregorian"] == "2025-04-20"
    assert w["golden_number"] == 12  # colonne 2025 de la table publiee


def test_e6_extremes_consigned():
    # « Latest Gregorian Easter 2038-04-25 and 1943-04-25 are Sundays »
    # (COMPIL §3) ; les bornes publiees du computus gregorien : 22 mars
    # (1818, 2285) — 25 avril (1943, 2038).
    for y, want in ((1943, "1943-04-25"), (2038, "2038-04-25"),
                    (1818, "1818-03-22"), (2285, "2285-03-22")):
        d = easter({"year": y,
                    "algorithm": "gregorian_meeus_butcher"}).json()
        assert d["easter_gregorian"] == want
        assert d["weekday"]["name"] == "Sunday"


def test_e7_meeus_julian_published_columns():
    # Table publiée « Meeus's Julian algorithm » (AA 1991 p.69) :
    # Y=2008 : a=0 b=6 c=13 d=22 e=1, d+e+114=137 -> 14 avril julien /
    # 27 avril grégorien ; Y=2027 : d+e+114=142 -> 19 avril / 2 mai.
    a = easter({"year": 2008, "algorithm": "julian_meeus"}).json()
    assert a["intermediates"] == {"a": 0, "b": 6, "c": 13, "d": 22, "e": 1,
                                  "d_plus_e_plus_114": 137}
    assert a["easter_julian"] == "2008-04-14"
    assert a["easter_gregorian"] == "2008-04-27"
    b = easter({"year": 2027, "algorithm": "julian_meeus"}).json()
    assert b["easter_julian"] == "2027-04-19"
    assert b["easter_gregorian"] == "2027-05-02"
    c = easter({"year": 2016, "algorithm": "julian_meeus"}).json()
    assert c["easter_julian"] == "2016-04-18"
    assert c["easter_gregorian"] == "2016-05-01"


def test_e8_century_shift_2100_by_table():
    # « In the year 2100, the difference will increase by another day »
    # (page publiée Date of Easter) : Paque julienne 2100 = 18 avril
    # julien, pont table = +14 -> 2 mai 2100. La table centurielle de
    # juliankit joue, pas un 13 colle.
    d = easter({"year": 2100, "algorithm": "julian_meeus"}).json()
    assert d["easter_julian"] == "2100-04-18"
    assert d["easter_gregorian"] == "2100-05-02"
    assert d["offset_days"] == 14


def test_e9_sunday_invariant_sweep():
    # B5 consigné : « Ten Easter golds are Sunday (iso_day=7) ». Balayage
    # complet des deux computus sur la portée closee : la fete EST
    # dimanche par construction, et le computus gregorien reste dans sa
    # fenetre publiee 22 mars..25 avril (avant le 26 avril, dit la page).
    import computuskit
    import juliankit
    for y in range(1583, 3000):
        g = computuskit.easter_gregorian_computus(y)
        assert g["jdn"] % 7 == 6, y                    # dimanche
        assert "03-22" <= g["easter_gregorian"][5:] <= "04-25", y
    for y in range(1, 3000):
        j = computuskit.easter_julian_computus(y)
        assert j["jdn"] % 7 == 6, y
        # coherence pont : le jour rendu EST le jour julien du computus
        assert juliankit.julian_from_jdn(j["jdn"]) == j["julian_tuple"], y


# ============ easter_computus — refus nommés ============

def test_e_r1_algorithm_closed_set():
    r = easter({"year": 2025, "algorithm": "orthodox"})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "algorithm"
    assert "gregorian_meeus_butcher" in e["message"]
    assert "julian_meeus" in e["message"]


def test_e_r2_algorithm_required_never_guessed():
    r = easter({"year": 2025})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "algorithm"


def test_e_r3_pre_reform_year_names_the_julian_window():
    r = easter({"year": 1500, "algorithm": "gregorian_meeus_butcher"})
    assert r.status_code == 400
    assert "julian_meeus" in r.json()["errors"][0]["message"]


def test_e_r4_year_zero_refused_era_said():
    r = easter({"year": 0, "algorithm": "julian_meeus"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "year"


def test_e_r5_year_out_of_closed_range():
    assert easter({"year": 10000,
                   "algorithm": "gregorian_meeus_butcher"}).status_code == 400
    assert easter({"year": -44, "algorithm": "julian_meeus"}).status_code == 400


def test_e_r6_unknown_key_refused_by_name():
    # précédent B8 : une clé inconnue meurt par son nom.
    r = easter({"year": 2025, "algorithm": "julian_meeus", "rite": "latin"})
    assert r.status_code == 400
    assert "rite" in json.dumps(r.json())


# ============ easter_computus — rendu ============

def test_e_d1_bridge_coherence_with_135():
    # Seam bundle 135 : le gold G2 de test_bundle135 (julien 2012-04-02
    # -> gregorien 2012-04-15, jdn 2456033) est le MEME pont. Les deux
    # outils doivent rendre les mêmes octets sur la même question.
    o = easter({"year": 2012, "algorithm": "julian_meeus"}).json()
    j = julian({"date": "2012-04-02", "calendar": "julian"}).json()
    assert o["jdn"] == j["jdn"] == 2456033
    assert o["easter_gregorian"] == j["gregorian"]
    assert o["offset_days"] == j["offset_days"] == 13
    assert o["table"]["sha256"] == j["table"]["sha256"]  # une seule table


def test_e_d2_procedure_and_table_vintage_declared():
    # doctrine 27-11 : table/algorithme = version + sha déclarés.
    d = easter({"year": 2025, "algorithm": "julian_meeus"}).json()
    p = d["procedure"]
    assert p["name"] == "meeus-butcher-computus"
    assert "Nature 1876" in p["version"] and len(p["sha256"]) == 64
    assert d["table"]["name"] == "julian-gregorian-century-offsets"
    d2 = easter({"year": 1961,
                 "algorithm": "gregorian_meeus_butcher"}).json()
    assert d2["procedure"]["sha256"] == p["sha256"]      # stable
    assert d2["table"]["sha256"] == d["table"]["sha256"]  # stable


def test_e_d3_exact_integers_no_float():
    d = easter({"year": 2025, "algorithm": "gregorian_meeus_butcher"}).json()
    assert isinstance(d["jdn"], int)
    for v in d["intermediates"].values():
        assert isinstance(v, int)


def test_e_d4_no_silent_default():
    # les deux outils exigent tout : applied_defaults reste RENDU (vide
    # honnête, précédent B8/B12 — rien n'est appliqué sans être dit).
    d = easter({"year": 2025, "algorithm": "julian_meeus"}).json()
    assert d["applied_defaults"] == []


# ============ porte : routes vides de campagne, batch, routeur ============

def test_door_empty_routes_now_answer():
    # Douleur mesurée §2/§4 : /route?q=easter+computus et « paschal »
    # ne nommaient AUCUN outil ; « maya long count » ne pointait que
    # text_count. Les routes se repondent elles-memes.
    r = client.get("/route?q=easter+computus").json()
    assert "easter_computus" in json.dumps(r)
    r2 = client.get("/route?q=paschal").json()
    assert "easter_computus" in json.dumps(r2)


def test_batch_easter_and_maya():
    r = client.post("/api/v1/batch", json={
        "tool": "easter_computus",
        "payloads": [{"year": 2025, "algorithm": "gregorian_meeus_butcher"},
                     {"year": 2025, "algorithm": "coptic"}]})
    assert r.status_code == 200
    rs = r.json()["results"]
    assert rs[0]["result"]["easter_gregorian"] == "2025-04-20"
    assert rs[1]["ok"] is False
def test_tool_specs_resolve():
    for name in ("easter_computus",):
        r = client.get("/tools/%s.json" % name)
        assert r.status_code == 200, name
        b = r.json()
        assert b["tier"] == "free" and b["pack"] == "dates"
        assert "enum" in json.dumps(b["schema"])


def test_no_internal_names_in_answers():
    # la porte ne nomme jamais une instance interne ; les golds citent
    # l'algorithme publie, pas un releveur.
    r = client.post("/api/v1/date/easter-computus",
                    json={"year": 2025, "algorithm": "julian_meeus"})
    assert "licky" not in r.text.lower()
    assert "grok" not in r.text.lower()
