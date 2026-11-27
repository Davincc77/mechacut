# Bundle 128_hermes — vague de CORRECTIFS des fautes de grammaire rendues
# par la compilation des 17 segments Grok (vague 2, 26-11 ~23:50), rejouees
# main sur v1.50.0 avant d'etre cru : B1 (le champ sha256 du digest MENT),
# B3 (les 400 nomment le mauvais champ — 3 sites confirmes), B8 (rele
# inconnu passe en silence — le pire, contraire de NOTRE doctrine), B11
# (seconde intercalaire refusee contre le contrat de format), B12 (round/
# places coupent les zeros que digits= garde), B16 (calendar julian avale
# en silence), B17 (geo_distance muet sur son modele). B14 etait deja tue
# (v1.49 — verifie live sur leur porte de 1.48.1 : fige depuis).
# Amas de propositions (dates/chi2/geodesie/digests) : arbitres a cote —
# cet arbre ne repare QUE les mensonges et les silences.
import json

from fastapi.testclient import TestClient

from main import app, canon

client = TestClient(app)


def call(path, body):
    return client.post("/api/v1/" + path, json=body)


# ---------------- B1 : le canon rendu, pas le digest vole ----------------

def test_b1_md5_ne_mentit_plus_sur_le_sha256():
    d = call("hash/digest", {"data": "abc", "algo": "md5"}).json()
    assert d["hex"] == "900150983cd24fb0d6963f7d28e17f72"  # md5 est la
    assert d["sha256"] != d["hex"]  # le champ sha256 n'EST plus le digest
    body = {k: v for k, v in d.items() if k != "sha256"}
    assert d["sha256"] == canon(body)  # queue canonique de la maison


def test_b1_sha256_meme_separation():
    # algo sha256 : l'hex du digest vit dans « hex » ; « sha256 » reste le
    # canon de la reponse — un seul sens par champ, quel que soit l'algo.
    d = call("hash/digest", {"data": "abc", "algo": "sha256"}).json()
    assert d["hex"] == ("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61"
                        "f20015ad")
    assert d["sha256"] != d["hex"]


# ---------------- B8 : plus de rele inconnu silencieux ----------------

def test_b8_cle_de_regle_inconnue_refusee_par_nom():
    r = call("logic/rules", {"facts": {"fact1": True},
                             "rules": [{"name": "r", "if": "fact1"}]})
    assert r.status_code == 400
    m = json.dumps(r.json())
    assert "if" in m  # la cle fautive nommee
    assert "when" in m  # la gramme fermee citee


def test_b8_fait_inconnu_dans_condition_refuse():
    r = call("logic/rules", {"facts": {"fact1": True}, "rules": [
        {"name": "r", "when": {"fact": "fact2", "op": "eq", "value": True}}]})
    assert r.status_code == 400
    m = json.dumps(r.json())
    assert "fact2" in m and "exists" in m  # l'absence a un op, pas un silence


def test_b8_absence_explicite_survit():
    # le chemin LEGITIME de l'absence doit continuer de jouer : op exists
    d = call("logic/rules", {"facts": {"fact1": True}, "rules": [
        {"name": "r", "when": {"fact": "fact2", "op": "exists"},
         "require": {"fact": "fact1", "op": "eq", "value": True}}]}).json()
    assert d["trace"][0]["fired"] is False and d["trace"][0]["outcome"] == "skipped"


def test_b8_require_inconnu_refuse_aussi():
    r = call("logic/rules", {"facts": {"fact1": True}, "rules": [
        {"name": "r", "require": {"fact": "fact9", "op": "gt", "value": 1}}]})
    assert r.status_code == 400
    assert "fact9" in json.dumps(r.json())


# ---------------- B11 : la seconde intercalaire, nommee des deux cotes ----

def test_b11_format_accepte_le_ap60_car_le_contrat_le_dit():
    # la carte du contrat dit « leap second ok » : le FORMAT est syntaxe
    # RFC 3339, pas capacite de la scale POSIX. :60 est un syntax-valid.
    d = call("check/format", {"payload": {"d": "2016-12-31T23:59:60Z"},
                              "formats": {"$.d": "datetime-iso"}}).json()
    assert d["valid"] is True
    assert "leap" in json.dumps(d)  # et le cas est NOMMEE, pas muet


def test_b11_date_parse_refuse_en_le_disant():
    # date_parse produit des instants civils : :60 n'en est pas un.
    # Refus legitime — mais le message doit NOMMER la seconde
    # intercalaire, pas un « 0..59 » nu.
    r = call("date/parse", {"text": "2016-12-31T23:59:60Z"})
    assert r.status_code == 400
    m = json.dumps(r.json()).lower()
    assert "leap" in m and "posix" in m


# ---------------- B12 : les zeros demandes sont rendus -------------------

def test_b12_round_garde_les_places_dites():
    d = call("math/calc", {"expr": "round(2.50, 2)"}).json()
    assert d["value"] == "2.50"


def test_b12_places_de_units_garde_les_zeros():
    d = call("units/convert", {"value": "268552.9", "from": "mi",
                               "to": "km", "places": 2}).json()
    v = d["value"]
    assert "." in v and len(v.split(".")[1]) == 2


# ---------------- B16/B7 : params avales = finis -------------------------

def test_b16_calendar_inconnu_refuse_par_nom():
    r = call("date/calc", {"base": "1582-10-04", "op": "diff",
                           "params": {"until": "1582-10-15",
                                      "calendar": "julian"}})
    assert r.status_code == 400
    m = json.dumps(r.json())
    assert "calendar" in m  # le cle fautive nommee
    assert "gregorian" in m.lower()  # la scale du outil dite


def test_b7_duration_grammaire_sans_ambiguite():
    r = call("date/calc", {"base": "2026-01-01", "op": "add",
                           "params": {"duration": "P3D"}})
    assert r.status_code == 400
    m = json.dumps(r.json())
    assert "without P" in m and '"3D"' in m or "3D" in m
    # la reparation doit donner la forme EXACTE, pas montrer le refus


def test_b7_signe_base_de_comptage_dite():
    d = call("date/calc", {"base": "2026-01-01T00:00:00Z", "op": "diff",
                           "params": {"until": "2025-12-31T23:57:37Z",
                                      "unit": "days"}}).json()
    assert d["days"] == -1  # floor (comportement conserve)
    assert "floor" in json.dumps(d)  # mais DESORMAIS DIT


# ---------------- B17 : le modele est echoe ------------------------------

def test_age_sans_on_horloge_murale_refusee():
    # la 7e faute, trouvee en relisant le code (non rapportee) : l'age
    # sans « on » lisait datetime.now() du serveur. Le claim maison dit
    # « the clock is always an argument ». Le refus nomme la cause et
    # rend la forme attendue — et le meme age doit etre rendu a deux
    # clients differents sur le meme « on ».
    r = call("date/calc", {"base": "1977-06-15", "op": "age",
                           "params": {}})
    assert r.status_code == 400
    m = json.dumps(r.json()).lower()
    assert "wall clock" in m and "params.on" in m
    d1 = call("date/calc", {"base": "1977-06-15", "op": "age",
                            "params": {"on": "2026-11-20"}}).json()
    d2 = call("date/calc", {"base": "1977-06-15", "op": "age",
                            "params": {"on": "2026-11-20"}}).json()
    assert (d1["years"], d1["months_extra"], d1["days_extra"]) == (49, 5, 5)
    assert d1["sha256"] == d2["sha256"]


def test_b17_geo_distance_dison_modele():
    import geo
    d = call("geo/distance", {"a": {"lat": 0, "lon": 0},
                              "b": {"lat": 1, "lon": 1}}).json()
    assert d["model"] == "sphere"
    assert d["radius_m"] == geo.EARTH_RADIUS_M  # le rayon REELLEMENT utilise


# ---------------- B3 : chaque 400 nomme le bon coupable ------------------

def test_b3_geohash_nomme_lat_pas_precision():
    r = call("geo/geohash", {"lat": 999, "lon": 0, "precision": 5})
    assert r.status_code == 400
    errs = r.json()["errors"]
    assert errs[0]["field"] == "lat"


def test_b3_num_fx_nomme_rate_pas_amount():
    r = call("num/fx", {"amount": "100", "rate": "abc", "to": "USD"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "rate"


def test_b3_checkdigit_generate_dit_le_body_sans_cle():
    # 9780306406150 SATISFAIT le regex 13 chiffres cite par le 400 : le
    # message doit donc dire la verite — generate veut le BODY sans la
    # derniere cle, et le regex cite est celui du FULL value.
    r = call("id/checkdigit", {"mode": "generate", "scheme": "isbn13",
                               "value": "9780306406150"})
    assert r.status_code == 400
    m = json.dumps(r.json()).lower()
    assert "without" in m and "check" in m
    r2 = call("id/checkdigit", {"mode": "generate", "scheme": "isbn13",
                                "value": "978030640615"})
    assert r2.status_code == 200  # le vrai chemin paie toujours
    assert r2.json()["check_char"] == "7"
