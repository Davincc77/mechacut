# Bundle 135_hermes — LOT 135 : date_julian_gregorian + pep440_sort (v1.55.0).
# Admissions 27-11 (registre L24 reçu 56dc427d, L30 reçu 6aaf2824),
# arbitrage « TRI 27-11 » du cahier de triage interne : golds depuis l'algo public /
# grammaire publique close. Les blobs de la synthèse 22:55 n'ont pas
# été consignés sur disque (trou connu, cahier de triage interne) — les golds
# viennent donc des assertions CONSIGNÉES du rapport de campagne
# (COMPIL_RAPPORTS_VAGUE2, lignes 2611-2613, 2684-2685, B16) et des
# exemples publiés des spécitations elles-mêmes, recopiés, jamais
# inventés. Écart consigné au rapport : l'input exact du couple
# 28 452/28 442 (mesure Gate) n'est pas dans la matière consignée —
# sa CLASSE est couverte par le gold G7 (diff adjacent = 1) et le
# can-fail de la porte, pas par un gold inventé.
import json

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def julian(body):
    return client.post("/api/v1/date/julian-gregorian", json=body)


def p440(versions, **kw):
    body = {"versions": versions}
    body.update(kw)
    return client.post("/api/v1/version/pep440-sort", json=body)


# ============ date_julian_gregorian — golds tracés de l'algo public ============

def test_g1_reform_1582():
    # 1582-10-15 grégorien (premier jour de la réforme, ancre publiée
    # JDN 2299161) = 1582-10-05 julien ; décalage 10 jours nommé.
    r = julian({"date": "1582-10-15", "calendar": "gregorian"})
    assert r.status_code == 200
    d = r.json()
    assert d["julian"] == "1582-10-05"
    assert d["jdn"] == 2299161
    assert d["offset_days"] == 10


def test_g2_easter_pair_2012_consigned():
    # COMPIL_RAPPORTS_VAGUE2 (section clic 133, item B3) : « Julian
    # 2012-04-02 + 13 » = grégorien 2012-04-15 — Pâque orthodoxe.
    d = julian({"date": "2012-04-02", "calendar": "julian"}).json()
    assert d["gregorian"] == "2012-04-15"
    assert d["offset_days"] == 13
    assert d["jdn"] == 2456033


def test_g3_century_boundary_1700():
    # le registre nomme le décalage 10/11 j : il bascule quand
    # 1700, siècle non bissextile grégorien, garde un 29 février
    # julien : julien 1700-02-18 = grégorien 02-28 (10),
    # julien 1700-02-19 = grégorien 03-01 (11).
    a = julian({"date": "1700-02-18", "calendar": "julian"}).json()
    b = julian({"date": "1700-02-19", "calendar": "julian"}).json()
    assert a["gregorian"] == "1700-02-28" and a["offset_days"] == 10
    assert b["gregorian"] == "1700-03-01" and b["offset_days"] == 11


def test_g4_jdn0_epoch_consigned():
    # « JDN 0 = Julian −4712-01-01 » (COMPIL, règle julienne proleptique).
    d = julian({"jdn": 0}).json()
    assert d["julian"] == "-4712-01-01"
    assert d["gregorian"] == "-4713-11-24"


def test_g5_maya_bridge_consigned():
    # « 0.0.0.0.0 sous 584283 = JDN 584283 = −3113-08-11 (proleptic
    # Gregorian) = 6 September 3114 BCE Julian » (COMPIL, item maya).
    d = julian({"jdn": 584283}).json()
    assert d["gregorian"] == "-3113-08-11"
    assert d["julian"] == "-3113-09-06"


def test_g6_lady_day_style_named():
    # Washington : né « 11 February 1731 » style julien avec année
    # ouvrant le 25 mars = 22 February 1732 grégorien (exemple public
    # Old Style and New Style dates). Le style est NOMMÉ, pas deviné.
    d = julian({"date": "1731-02-11", "calendar": "julian",
                "year_start": "march25"}).json()
    assert d["gregorian"] == "1732-02-22"
    assert any(f.startswith("march25_style") for f in d["flags"])


def test_g6b_after_1752_said():
    d = julian({"date": "1800-01-01", "calendar": "gregorian",
                "year_start": "march25"}).json()
    assert any(f.startswith("march25_after_1752") for f in d["flags"])


def test_g7_historical_skip_one_day():
    # B16 consigné : date_calc compte 1582-10-15 moins 1582-10-04 en
    # 11 jours proleptiques. Ils étaient ADJACENTS : 1 jour. C'est le
    # écart exact (classe du 28 452 vs 28 442) rendu par le pont JDN.
    d = julian({"date": "1582-10-04", "calendar": "julian",
                "to_date": "1582-10-15",
                "to_calendar": "gregorian"}).json()
    assert d["diff_days"] == 1


def test_g7b_inherited_scale_is_said():
    # sans to_calendar, l'autre bord hérite du calendar DONNÉ — c'est
    # RENDU (applied_defaults), jamais un mélange silencieux.
    d = julian({"date": "1582-10-04", "calendar": "julian",
                "to_date": "1582-10-15"}).json()
    assert d["diff_days"] == 11
    assert any(a.startswith("to_calendar=julian")
               for a in d["applied_defaults"])


def test_g8_skip_window_flagged_not_refused():
    # 1582-10-10 « grégorien » n'a jamais été un jour civil : il existe
    # PROLEPTIQUEMENT — échelle DITE par le flag, jamais un refus muet.
    d = julian({"date": "1582-10-10", "calendar": "gregorian"}).json()
    assert d["jdn"] == 2299156
    assert any(f.startswith("gregorian_skip_1582") for f in d["flags"])


def test_g9_leap_rules_differ_by_calendar():
    # 1900 est bissextile en julien (tous les 4 ans, COMPIL:2611), pas
    # en grégorien (siècle non divisible par 400) : le même jour
    # existe dans l'un, meurt par son nom dans l'autre.
    ok = julian({"date": "1900-02-29", "calendar": "julian"})
    assert ok.status_code == 200
    assert ok.json()["gregorian"] == "1900-03-13"
    bad = julian({"date": "1900-02-29", "calendar": "gregorian"})
    assert bad.status_code == 400
    assert "gregorian" in json.dumps(bad.json()).lower()


def test_r1_unknown_calendar_refused_by_name():
    r = julian({"date": "2026-11-27", "calendar": "coptic"})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "calendar"
    assert "gregorian" in e["message"] and "julian" in e["message"]


def test_r2_instant_refused_names_neighbour():
    r = julian({"date": "2012-04-15T10:00", "calendar": "gregorian"})
    assert r.status_code == 400
    assert "date_parse" in r.json()["errors"][0]["message"]


def test_r3_bare_year_names_edtf_sister():
    r = julian({"date": "1985", "calendar": "gregorian"})
    assert r.status_code == 400
    assert "date_edtf_interval" in r.json()["errors"][0]["message"]


def test_r4_date_and_jdn_both_refused():
    r = julian({"date": "2000-01-01", "calendar": "gregorian",
                "jdn": 2451545})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "jdn"


def test_r5_no_input_refused():
    assert julian({}).status_code == 400


def test_r6_year_start_closed_set():
    r = julian({"date": "1700-01-01", "calendar": "julian",
                "year_start": "mar25"})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "year_start"
    assert "jan01" in e["message"] and "march25" in e["message"]


def test_r7_unknown_key_refused_by_name():
    # précédent B8 : une clé inconnue meurt par son nom.
    r = julian({"date": "2000-01-01", "calendar": "gregorian",
                "style": "old"})
    assert r.status_code == 400
    assert "style" in json.dumps(r.json())


def test_r8_range_closed():
    r = julian({"date": "-99999-01-01", "calendar": "gregorian"})
    assert r.status_code == 400


def test_d1_applied_defaults_rendered():
    # précédent B12 : tout défaut appliqué est RENDU.
    d = julian({"date": "2000-01-01", "calendar": "gregorian"}).json()
    assert d["year_start"] == "jan01"
    assert any("year_start" in a for a in d["applied_defaults"])


def test_d2_table_vintage_declared():
    # doctrine 27-11 : table fermée = version + sha déclarés dans la
    # réponse (pas une prose qui promet).
    d = julian({"date": "2026-11-27", "calendar": "gregorian"}).json()
    t = d["table"]
    assert t["name"] == "julian-gregorian-century-offsets"
    assert "v1" in t["version"] and len(t["sha256"]) == 64
    assert d["scale"].startswith("proleptic")
    d2 = julian({"date": "2000-01-01", "calendar": "gregorian"}).json()
    assert d2["table"]["sha256"] == t["sha256"]  # stable


def test_d3_exact_strings_no_float():
    d = julian({"jdn": 2451545}).json()
    assert isinstance(d["jdn"], int)
    assert d["gregorian"] == "2000-01-01"  # ancre publiée


def test_door_seam_date_calc_still_names_us():
    # can-fail sur la voisine : date_calc DOIT continuer à refuser
    # calendar=julian par son nom en désignant ce contrat — la porte
    # d'à côté est notre distinction prouvée (B16, dates.py).
    r = client.post("/api/v1/date/calc", json={
        "base": "2012-12-21", "op": "diff",
        "params": {"date2": "2012-12-08", "calendar": "julian"}})
    assert r.status_code == 400
    assert "date_julian_gregorian" in json.dumps(r.json())


def test_batch_dispatch():
    r = client.post("/api/v1/batch", json={"tool": "date_julian_gregorian",
                                           "payloads": [
        {"date": "1582-10-15", "calendar": "gregorian"},
        {"jdn": 584283}]})
    assert r.status_code == 200
    rs = r.json()["results"]
    assert rs[0]["result"]["julian"] == "1582-10-05"
    assert rs[1]["result"]["gregorian"] == "-3113-08-11"


# ============ pep440_sort — grammaire publique déclarée, golds publiés ============

# Liste publiée du PEP 440 (« Summary of permitted suffixes and
# relative ordering », « The following example covers many of the
# possible combinations ») — recopiée LITTÉRALEMENT, jamais inventée.
PEP_ORDER_PUBLISHED = [
    "1.dev0", "1.0.dev456", "1.0a1", "1.0a2.dev456", "1.0a12.dev456",
    "1.0a12", "1.0b1.dev456", "1.0b2", "1.0b2.post345.dev456",
    "1.0b2.post345", "1.0rc1.dev456", "1.0rc1", "1.0", "1.0+abc.5",
    "1.0+abc.7", "1.0+5", "1.0.post456.dev34", "1.0.post456",
    "1.0.15", "1.1.dev1",
]


def test_p1_pep_published_example_verbatim():
    r = p440(PEP_ORDER_PUBLISHED[::-1])
    assert r.status_code == 200
    assert r.json()["sorted_canonical"] == PEP_ORDER_PUBLISHED


def test_p2_epoch_published_example():
    # PEP 440 §Version epochs : « 2013.10 2014.04 1!1.0 1!1.1 1!2.0 »
    r = p440(["1!1.0", "1!2.0", "2014.04", "1!1.1", "2013.10"])
    assert r.json()["sorted"] == ["2013.10", "2014.04", "1!1.0",
                                  "1!1.1", "1!2.0"]


# Les 7/7 listes PyPI refusées par semver_sort (registre L30) : chaque
# liste porte au moins un token PEP hors grammaire semver (1!, a/b/rc,
# .post, .dev, dates). Le contraste est REJOUÉ ici, pas cité en prose.
PYPI_LIKE = [
    ["2.31.0", "1!2.0", "2.32.0.dev1"],
    ["1.0", "1.0rc1", "1.0b2", "1.0a1"],
    ["23.1", "23.2rc1", "23.2", "23.3.dev0"],
    ["1.0.post1", "1.0", "1.1.dev2"],
    ["2023.1", "1!2024.1", "2023.2"],
    ["0.9", "1.0.dev100", "1.0a0", "1.0"],
    ["3.0.0.post1", "3.0.0", "3.0.0rc1", "3.0.0b1"],
]


def test_p3_seven_pypi_lists_semver_refuses_pep440_sorts():
    for L in PYPI_LIKE:
        s = client.post("/api/v1/semver/sort", json={"versions": L})
        assert s.status_code == 400, L
        d = p440(L)
        assert d.status_code == 200, L
    # ordre tracé à la main sur la première : l'epoch 1! passe APRÈS
    # tout epoch 0 (règle publiée), dev1 avant le final absent — ici
    # 2.32.0.dev1 EST encore 2.32 (release (2,32) > (2,31)) :
    assert p440(PYPI_LIKE[0]).json()["sorted"] == \
        ["2.31.0", "2.32.0.dev1", "1!2.0"]


def test_p4_normalization_examples_published():
    cases = {  # chaque cas = un exemple publié du PEP (§Normalization)
        "1.1RC1": "1.1rc1",
        "1.1-a1": "1.1a1",
        "1.0alpha1": "1.0a1",
        "1.1beta2": "1.1b2",
        "1.1c3": "1.1rc3",
        "1.2a": "1.2a0",
        "1.2-post2": "1.2.post2",
        "1.2post2": "1.2.post2",
        "1.2.post-2": "1.2.post2",
        "1.0-r4": "1.0.post4",
        "1.0-1": "1.0.post1",
        "1.2-dev2": "1.2.dev2",
        "1.2dev2": "1.2.dev2",
        "1.2.dev": "1.2.dev0",
        "1.2.post": "1.2.post0",
        "1.0+ubuntu-1": "1.0+ubuntu.1",
        "v1.0": "1.0",
    }
    d = p440(sorted(cases)).json()
    got = {e["given"]: e["canonical"] for e in d["entries"]}
    for given, want in cases.items():
        assert got[given] == want, given
    # normalisation rendue, pas silencieuse :
    e = p440(["1.0-1"]).json()["entries"][0]
    assert any("implicit post" in n for n in e["normalizations"])


def test_p5_equivalences_rendered_not_deduped():
    # X.Y et X.Y.0 ne sont PAS distincts (règle de padding publiée) ;
    # le tri les garde, le verdict les GROUPE.
    d = p440(["1.0.0", "1.0", "v1.0.0"]).json()
    assert d["count"] == 3
    assert len(d["equivalences"]) == 1
    assert sorted(d["equivalences"][0]) == sorted(["1.0.0", "1.0",
                                                   "v1.0.0"])


def test_p6_local_ordering_published_positions():
    # dans la liste publiée : 1.0 < 1.0+abc.5 < 1.0+abc.7 < 1.0+5 <
    # 1.0.post456 — numérique > alphanumérique, plus de segments >
    # moins, local après le public sans local, le tout AVANT .post.
    o = p440(PEP_ORDER_PUBLISHED).json()["sorted_canonical"]
    pos = {v: o.index(v) for v in ("1.0", "1.0+abc.5", "1.0+abc.7",
                                   "1.0+5", "1.0.post456")}
    assert pos["1.0"] < pos["1.0+abc.5"] < pos["1.0+abc.7"] < \
        pos["1.0+5"] < pos["1.0.post456"]


def test_p7_dev_before_prerelease_final():
    # « The top level sort position of the .devN suffix » (diff de
    # PEP 386) : 1.0.devN AVANT 1.0a1, pas entre rc et final.
    d = p440(["1.0", "1.0a1", "1.0.dev456"]).json()
    assert d["sorted_canonical"] == ["1.0.dev456", "1.0a1", "1.0"]


def test_r9_pep440_refusals_named():
    # « 1.0- » : INVALIDE dit le PEP (§Implicit post releases) — refusé.
    assert p440(["1.0-"]).status_code == 400
    # semver-valide hors PEP (prerelease à points sémantiques) : refus
    # NOMMÉ désignant le contrat voisin semver_sort.
    r = p440(["1.0.0-alpha.beta"])
    assert r.status_code == 400
    assert "semver_sort" in json.dumps(r.json())
    # un specifier n'est pas une version.
    assert p440([">=1.0"]).status_code == 400
    # liste vide et plafond 2000 nommés (même plafond que semver_sort).
    assert p440([]).status_code == 400
    assert p440(["1.0"] * 2001).status_code == 400


def test_r10_non_string_refused_by_name():
    # 1.0 en JSON = float — le PEP parle en chaînes ; le 400 le dit.
    r = p440([1.0])
    assert r.status_code == 400
    assert "not a string" in json.dumps(r.json())


def test_r11_unknown_key_refused_by_name():
    r = client.post("/api/v1/version/pep440-sort",
                    json={"versions": ["1.0"], "order": "asc"})
    assert r.status_code == 400
    assert "order" in json.dumps(r.json())


def test_d4_descending_rendered():
    d = p440(["1.0", "1.0a1"], descending=True).json()
    assert d["descending"] is True
    assert d["sorted"] == ["1.0", "1.0a1"]
    d2 = p440(["1.0a1", "1.0"]).json()
    assert any("descending" in a for a in d2["applied_defaults"])
    assert d2["sorted"] == ["1.0a1", "1.0"]


def test_d5_grammar_vintage_declared():
    d = p440(["1.0"]).json()
    g = d["grammar"]
    assert g["name"] == "pep440-version-grammar"
    assert "PEP 440" in g["version"] and len(g["sha256"]) == 64


def test_d6_c_alias_said():
    d = p440(["1.0c1", "1.0rc1"]).json()
    assert d["sorted_canonical"] == ["1.0rc1", "1.0rc1"]
    assert any("c_alias" in f for f in d["flags"])
    assert d["equivalences"] == [["1.0c1", "1.0rc1"]]


def test_batch_pep440():
    r = client.post("/api/v1/batch", json={
        "tool": "pep440_sort",
        "payloads": [{"versions": ["1.0.post1", "1.0"]},
                     {"versions": ["nope!!"]}]})
    assert r.status_code == 200
    rs = r.json()["results"]
    assert rs[0]["result"]["sorted"] == ["1.0", "1.0.post1"]
    assert rs[1]["ok"] is False
