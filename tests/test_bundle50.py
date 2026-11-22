"""bundle50 — /money/baggage + /csv/excel_damage.

ORACLES. Baggage : chaque attente est CALCULÉE À LA MAIN sur les textes
rejoués CE cycle — The Age (40×30×15 « or less », sous réserve de
passer sous le siège ; PAS de limite légale pour le casier ; POIDS non
prescrit), newsandstar/money-tourism (applicable 23-oct-2027, signé
16-sept, JO 2-oct), bymetz (table mesurée 20 transporteurs : Ryanair
40×30×20, KLM 40×30×15), Standard (UK hors champ départ ; « pas deux
sacs gratuits »). ROTATION : 40×18×30 dans gabarit 40×30×20 — faces
triées, le test l'exige ; ordre brut échoue, la règle triée passe.
Arête de presse : 55+40+20=115 > le « cumul 100 cm » attribué au texte
par AOL/Independent — le module le rend comme AFFIRMATION testée.
Conversion pouces : facteur EXACT 2,54, attendus multipliés à la main
(21,5→54,61 ; 14→35,56 ; 9→22,86).

Dommage Excel : vecteurs PUBLICS rejoués — devholster (01234→1234,
4111111111111111→4111111111111110, 987654321098765432→9.87654E+17,
1E5→100000, SEPT2, 3/4, -5/+43), changethisfile (02134→2134, MARCH1→
1er mars), aiwebcenter (SÉRIAL 46113 = 1er avril 2026, époque 30-déc-
1899 — oracle stdlib timedelta, pas l'arrondi du module), dev.to/
thedaybreak (pleine chasse). Locale : même cellule « 1-2 » → DEUX
dates (2-ja en m/d ; 1-fév en d/m) — attendu nommé d'après la DÉFINITION
de locale, jamais la sortie du module. Année implicite = ARGUMENT as_of
(règle n°1 : jamais l'horloge).
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient

import bagkit
import damagekit
import main as m

client = TestClient(m.app)
m.RATE_LIMIT = 10**9

_AS_OF = date(2026, 11, 22)


def _serial(y, mo, d):
    """Oracle stdlib : l'époque sérial Excel 30-déc-1899, verbatim."""
    return (date(y, mo, d) - date(1899, 12, 30)).days


# ==================================================== baggage : la loi

def test_legal_edge_40x30x15_exact_on_application_day():
    r = bagkit.run_baggage({"flight_date": "2027-10-23", "regime": "EU",
                            "bag": "40x30x15"})
    assert r["law"]["stage"] == "amended-2026/2202"
    assert r["personal_law"]["within_legal_safe_harbour"] is True
    assert "FREE" in r["personal_law"]["verdict"]


def test_one_mm_over_breaks_the_harbour():
    r = bagkit.run_baggage({"flight_date": "2027-10-23", "regime": "EU",
                            "bag": "40x30x16"})
    assert r["personal_law"]["within_legal_safe_harbour"] is False
    assert "EXCEEDS" in r["personal_law"]["verdict"]


def test_day_before_application_no_law_at_all():
    r = bagkit.run_baggage({"flight_date": "2027-10-22", "regime": "EU",
                            "bag": "40x30x15"})
    assert r["law"]["stage"] == "before-application"
    assert r["law"]["personal_cap_cm"] is None
    assert r["personal_law"] is None


def test_rotation_rule():
    # 40x18x30 faces triées = (18,30,40) ⊆ (20,30,40) : PASSE.
    # Ordre BRUT (18≤30 ? 30≤20 ?) échouerait — c'EST la douleur.
    r = bagkit.run_baggage({"flight_date": "2027-11-02", "regime": "EU",
                            "bag": "40x18x30",
                            "personal_sizer": "40x30x20"})
    assert r["carrier"]["personal_vs_sizer"]["fits"] is True
    # et 40x30x20 dépasse l'arête LOI 40x30x15 (depth 20>15) même
    # si le gabarit Ryanair l'accepte : deux réponses, deux règles.
    assert r["personal_law"]["within_legal_safe_harbour"] is False


def test_no_rotation_alchemy_past_the_long_face():
    r = bagkit.run_baggage({"flight_date": "2027-11-02", "regime": "EU",
                            "bag": "60x10x10",
                            "cabin_sizer": "55x40x23"})
    assert r["carrier"]["cabin_vs_sizer"]["fits"] is False


def test_overhead_bag_has_no_legal_size():
    r = bagkit.run_baggage({"flight_date": "2027-11-02", "regime": "EU",
                            "bag": "55x40x20",
                            "cabin_sizer": "55x40x23"})
    assert r["law"]["overhead_cap_cm"] is None
    assert "does NOT set a size limit" in r["law"]["overhead_note"]
    assert r["carrier"]["cabin_vs_sizer"]["fits"] is True


def test_press_sum_claim_arithmetically_tested():
    # 55+40+20 = 115 cm cumulés : le « 100 cm » prêté au texte
    # (AOL/Independent) rendrait chaque trolley standard hors la loi —
    # arête mesurée, rendue comme affirmation de presse, jamais règle.
    r = bagkit.run_baggage({"flight_date": "2027-11-02", "regime": "EU",
                            "bag": "55x40x20", "cabin_sum_limit": "100"})
    assert r["bag_sum_cm"] == "115"
    v = r["carrier"]["cabin_vs_sum"]
    assert v["passes"] is False
    assert "NOT in the regulation" in v["rule"]
    claims = [c["claim"] for c in r["press_contradictions"]]
    assert any("100 cm" in c for c in claims)


def test_inches_convert_at_exact_254():
    r = bagkit.run_baggage({"flight_date": "2027-11-02", "regime": "EU",
                            "bag": "21.5x14x9", "bag_unit": "in",
                            "cabin_sizer": "55x40x23"})
    assert r["bag_cm"] == "54.61x35.56x22.86"   # multiplié À LA MAIN
    assert r["carrier"]["cabin_vs_sizer"]["fits"] is True


def test_uk_departure_named_out_of_scope():
    r = bagkit.run_baggage({"flight_date": "2027-11-02", "regime": "UK",
                            "bag": "40x30x15"})
    assert r["law"]["stage"] == "not-covered"
    assert "departure" in r["law"]["note"]
    assert r["personal_law"] is None


def test_weight_is_carrier_rule_law_silent():
    r = bagkit.run_baggage({"flight_date": "2027-11-02", "regime": "EU",
                            "bag": "55x40x20", "weight_kg": "11",
                            "cabin_sizer": "55x40x20",
                            "cabin_weight_max": "10"})
    assert r["carrier"]["weight_vs_cap"]["passes"] is False
    assert "no weight" in r["carrier"]["weight_vs_cap"]["rule"]
    limb = " ".join(r["legal_limbs"])
    assert "NOT prescribed by law" in limb


def test_baggage_refusals_named():
    for bad, field in (({"flight_date": "2027-11-02", "regime": "eu261",
                         "bag": "40x30x15"}, "regime"),
                       ({"flight_date": "2027-13-01", "regime": "EU",
                         "bag": "40x30x15"}, "flight_date"),
                       ({"flight_date": "2027-11-02", "regime": "EU",
                         "bag": "40x30"}, "bag")):
        with pytest.raises(bagkit.BagError) as e:
            bagkit.run_baggage(bad)
        assert e.value.field == field


# ==================================================== damage : les vecteurs

def test_devholster_vectors_rejoues():
    f = damagekit.classify_cell
    assert f("01234", "en", _AS_OF) == ("leading_zero_stripped",
                                        {"displayed": "1234"})
    assert f("02134", "en", _AS_OF)[1]["displayed"] == "2134"
    assert f("0043664123456", "en", _AS_OF)[1]["displayed"] == \
        "43664123456"
    r = f("4111111111111111", "en", _AS_OF)
    assert r[0] == "long_number_truncated"
    assert r[1]["stored_value"] == "4111111111111110"   # vector publié
    r = f("987654321098765432", "en", _AS_OF)
    assert r[1]["displayed"] == "9.87654E+17"           # vector publié
    assert f("1E5", "en", _AS_OF)[1]["displayed"] == "100000"
    assert f("-5", "en", _AS_OF)[0] == "formula_shaped"
    assert f("+43", "en", _AS_OF)[1]["displayed"] == "43"


def test_date_coercion_locale_is_the_fork():
    # MÊME CELLULE, DEUX DATES : l'argument locale décide, dit.
    r = damagekit.classify_cell("1-2", "en", _AS_OF)
    assert r[1]["displays"] == "2026-01-02"     # m-d → 2 janvier
    assert r[1]["stored_serial"] == _serial(2026, 1, 2)
    r = damagekit.classify_cell("1-2", "eu", _AS_OF)
    assert r[1]["displays"] == "2026-02-01"     # d-m → 1 février
    r = damagekit.classify_cell("3-4", "en", _AS_OF)
    assert r[1]["displays"] == "2026-03-04"     # devholster 3/4→04.03
    r = damagekit.classify_cell("3-4", "eu", _AS_OF)
    assert r[1]["displays"] == "2026-04-03"
    r = damagekit.classify_cell("SEPT2", "en", _AS_OF)
    assert r[1]["displays"] == "2026-09-02"     # SEPT alias publié
    r = damagekit.classify_cell("MARCH1", "en", _AS_OF)
    assert r[1]["displays"] == "2026-03-01"     # changethisfile gene name
    assert r[0] == "coerced_to_date"


def test_serial_epoch_public_vector():
    # aiwebcenter : 46113 EST le 1-avril-2026 — oracle stdlib timedelta.
    assert damagekit._serial(date(2026, 4, 1)) == 46113
    assert _serial(2026, 4, 1) == 46113         # deux fois, deux voies


def test_formula_execution_surface():
    r = damagekit.classify_cell("=HYPERLINK(\"x\")", "en", _AS_OF)
    assert r[0] == "formula_shaped"
    assert r[1]["note"] == "executes as a formula"


def test_fullwidth_and_safe():
    assert damagekit.classify_cell("１２３", "en", _AS_OF)[0] == \
        "fullwidth_digits"
    assert damagekit.classify_cell("hello", "en", _AS_OF)[0] == \
        "text_preserved"
    assert damagekit.classify_cell("5", "en", _AS_OF)[0] == \
        "text_preserved"          # un entier nu survit


def test_run_damage_column_verdicts():
    csv = ("id,code,qty\n"
           "02134,3-4,5\n"
           "987654321098765432,SEPT2,7\n")
    r = damagekit.run_damage({"csv": csv, "locale": "en",
                              "as_of": "2026-11-22"})
    cols = r["columns"]
    assert cols[0]["at_risk"] and cols[1]["at_risk"]
    assert not cols[2]["at_risk"]               # qty 5/7 : rien ne convertit
    assert cols[2]["import_mode"].startswith("any")
    assert "id" in r["at_risk_columns"]
    assert len(r["prescribed_import"]) == 4     # dont le toggle Microsoft
    assert "UNRECOVERABLE" in r["recovery_note"]


def test_damage_requires_as_of_and_locale():
    with pytest.raises(damagekit.DamageError) as e:
        damagekit.run_damage({"csv": "a\n01\n"})
    assert e.value.field == "as_of"
    with pytest.raises(damagekit.DamageError) as e:
        damagekit.run_damage({"csv": "a\n01\n", "locale": "fr",
                              "as_of": "2026-11-22"})
    assert e.value.field == "locale"
    with pytest.raises(damagekit.DamageError) as e:
        damagekit.run_damage({"csv": "x" * 20001,
                              "as_of": "2026-11-22"})
    assert e.value.field == "csv"


# ==================================================== HTTP + pins

def test_http_determinism_both_routes():
    for path, body in (
            ("/api/v1/money/baggage", {"flight_date": "2027-11-02",
                                       "regime": "EU",
                                       "bag": "40x18x30",
                                       "personal_sizer": "40x30x20"}),
            ("/api/v1/csv/excel_damage", {"csv": "a,b\n02134,3-4\n",
                                          "locale": "en",
                                          "as_of": "2026-11-22"})):
        r1 = client.post(path, json=body)
        r2 = client.post(path, json=body)
        assert r1.status_code == r2.status_code == 200
        assert r1.content == r2.content
        assert r1.json()["sha256"]


def test_http_refusals_are_400_named():
    r = client.post("/api/v1/money/baggage",
                    json={"flight_date": "2027-11-02",
                          "regime": "schengen", "bag": "40x30x15"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "regime"
    r = client.post("/api/v1/csv/excel_damage",
                    json={"csv": "a\n1\n"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "as_of"


def test_route_first_for_pain_phrases():
    for q, path in (
            ("will my cabin bag fit under the seat 40x18x30",
             "/api/v1/money/baggage"),
            ("does my carry-on suitcase pass the new 2027 eu rule",
             "/api/v1/money/baggage"),
            ("mon sac de cabine passe-t-il la nouvelle règle européenne",
             "/api/v1/money/baggage"),
            ("excel destroyed my csv leading zeros postcodes",
             "/api/v1/csv/excel_damage"),
            ("que va détruire excel dans ce csv avant ouverture",
             "/api/v1/csv/excel_damage"),
            ("o excel vai corromper meu csv zeros à esquerda",
             "/api/v1/csv/excel_damage")):
        r = client.get("/route", params={"q": q})
        assert r.status_code == 200, q
        assert r.json()["tools"][0]["path"] == path, q
