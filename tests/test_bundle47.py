"""bundle47 — /units/shoe_size + /net/sri.

ORACLES. shoes : aucune attente lue de la sortie du module — toutes les
fractions sont calculées À LA MAIN ici depuis les échelles publiées
(barleycorn = 1/3 in = 127/15 mm ; Paris point = 2/3 cm = 20/3 mm ;
ISO/TS 19407 Table 2 rendue publique : foot = (UK+23) x 127/15, US men
= UK + 1, US women = UK + 2 ; EU = foot_cm x 1.5 + 2 ; « EU 42 is a
28 cm last » (saascity, 20 nov. 2026) = vecteur verbatim). sri :
l'oracle est le pipeline PUBLIÉ de MDN — `openssl dgst -<algo> -binary
| openssl base64 -A` — une implémentation indépendante de hashlib ;
les vecteurs d'audit (TAB, sha1, longueur) sont écrits main d'après la
grammaire W3C et le CVE-2026-120423.
"""
import base64
import json
import subprocess
from fractions import Fraction

import pytest
from fastapi.testclient import TestClient

import main
import shoeskit as sk
import srikit as sr

client = TestClient(main.app)
main.RATE_LIMIT = 10**9


# ============================================ shoeskit — échelles publiées

def test_published_step_constants():
    assert sk.BARLEY == Fraction(127, 15)      # 1/3 in, exact
    assert sk.PARIS == Fraction(20, 3)         # 2/3 cm, exact
    # la dérive que convertitive donne « ~1.8 mm per step » : chez nous
    # c'est un THEOREME d'echelle, pas une mesure
    assert sk.PER_STEP_GAP == Fraction(9, 5)   # = 1.8 mm exactement
    assert sk.CYCLE_EU4 == Fraction(80, 3)     # 4 pas EU
    assert sk.CYCLE_US3 == Fraction(127, 5)    # 3 pas US
    assert sk.CYCLE_EU4 - sk.CYCLE_US3 == Fraction(19, 15)
    # les grilles ne se recouvrent jamais : 80/3 != 127/5
    assert sk.CYCLE_EU4 != sk.CYCLE_US3


def test_foot_271_matches_published_row():
    # sizechartfinder 27.1 cm -> US M 10 / UK 9 (formules) ; main :
    # uk = 271 x 15/127 - 23 = 1144/127 = 9 + 1/127 ; eu = 271 x 3/20
    # + 2 = 853/20 = 42.65 -> leur chart arrondit 42.5, le nôtre DIT
    # la position et les candidats
    o = sk.run_shoe_size({"foot_mm": 271})
    assert o["systems"]["eu"]["position"]["fraction"] == "853/20"
    assert o["systems"]["uk"]["position"]["fraction"] == "1144/127"
    assert o["systems"]["us_men"]["position"]["fraction"] == "1271/127"
    assert o["systems"]["us_women"]["position"]["fraction"] == "1398/127"
    assert o["systems"]["eu"]["candidates"]["grid_1/2"] == ["42 1/2", "43"]
    assert o["systems"]["eu"]["candidates"]["grid_1/3"] == ["42 1/3",
                                                             "42 2/3"]
    assert o["systems"]["mondopoint"]["candidates"]["grid_5mm"] == ["270",
                                                                     "275"]


def test_eu42_is_a_28cm_last_saascity_verbatim():
    # « EU 42 is a 28 cm last » — 42 x 20/3 = 280 exactement
    assert Fraction(42) * sk.PARIS == 280
    o = sk.run_shoe_size({"size": "42", "system": "eu"})
    # ancre pied : foot = (42-2) x 20/3 = 800/3 = 266.667 mm
    assert o["foot_mm"]["fraction"] == "800/3"
    assert o["systems"]["uk"]["position"]["fraction"] == "1079/127"
    # l'aisance du +2 est DECLAREE : 2 Paris points = 40/3 mm
    assert o["last_anchor"]["foot_vs_last_allowance_mm"]["fraction"] == \
        "40/3"


def test_third_size_parse_and_us95_vector():
    # « 42 2/3 » (pratique adidas) : (128/3 - 2) x 20/3 = 2440/9
    o = sk.run_shoe_size({"size": "42 2/3", "system": "eu"})
    assert o["foot_mm"]["fraction"] == "2440/9"
    # US 9.5 (thefitville « EU 41 OU 42, les deux corrects ») :
    # foot = 31.5 x 127/15 = 2667/10 ; eu = 2667/10 x 3/20 + 2 = 8401/200
    o2 = sk.run_shoe_size({"size": "9.5", "system": "us_men"})
    assert o2["foot_mm"]["fraction"] == "2667/10"
    assert o2["systems"]["eu"]["position"]["fraction"] == "8401/200"
    # nos candidats autour de 42.005 : 42 (grille entière), 42 1/2,
    # 42 1/3 — la réponse rend le GROUPE, jamais un numéro unique
    assert o2["never_one_number"] is True
    assert o2["systems"]["eu"]["candidates"]["grid_1/2"] == ["42", "42 1/2"]


def test_mondopoint_exact_on_grid_and_width():
    o = sk.run_shoe_size({"size": 270, "system": "mondopoint"})
    assert o["systems"]["mondopoint"]["candidates"]["grid_5mm"] == ["270"]
    o = sk.run_shoe_size({"foot_mm": 271, "width_mm": 100})
    assert o["mondopoint_label"] == "271/100"


def test_shoe_refusals_named():
    for args, field in (
        ({"foot_mm": 271, "size": 42, "system": "eu"}, "foot_mm"),
        ({}, "foot_mm"),
        ({"size": 42, "system": "cn"}, "system"),
        ({"foot_mm": 50}, "foot_mm"),
        ({"size": 60, "system": "eu"}, "size"),
        ({"size": "42 4/3", "system": "eu"}, "size"),
    ):
        with pytest.raises(sk.ShoeSizeError) as e:
            sk.run_shoe_size(args)
        assert e.value.field == field


# ============================================ srikit — oracle openssl MDN

FIXTURE = b"mechacut sri fixture \x00\xff 2026\n"
FIXTURE_B64 = base64.b64encode(FIXTURE).decode()


def _openssl(data, algo):
    p1 = subprocess.run(["openssl", "dgst", "-" + algo, "-binary"],
                        input=data, capture_output=True, check=True)
    p2 = subprocess.run(["openssl", "base64", "-A"],
                        input=p1.stdout, capture_output=True, check=True)
    return p2.stdout.decode().strip()


@pytest.mark.parametrize("algo", ["sha256", "sha384", "sha512"])
def test_sri_matches_published_openssl_pipeline(algo):
    o = sr.run_sri({"bytes_b64": FIXTURE_B64, "algorithms": [algo]})
    assert o["integrity"] == "%s-%s" % (algo, _openssl(FIXTURE, algo))


def test_sri_multi_token_strongest_first_and_text_utf8():
    o = sr.run_sri({"bytes_b64": FIXTURE_B64,
                    "algorithms": ["sha256", "sha512"]})
    toks = o["integrity"].split(" ")
    assert toks[0].startswith("sha512-") and len(toks) == 2
    t = sr.run_sri({"text": "héllo"})
    assert t["integrity"] == "sha384-" + _openssl(
        "héllo".encode("utf-8"), "sha384")
    assert "never fetched" in t["scope_note"]


def test_sri_tab_class_cve_2026_120423():
    o = sr.run_sri({"integrity_attr": "\t" + sr.run_sri(
        {"bytes_b64": FIXTURE_B64})["integrity"]})
    assert any("non-space" in f["finding"] and
               "CVE-2026-120423" in f["why"] for f in o["attr_audit"])


def test_sri_verify_and_tamper():
    good = sr.run_sri({"bytes_b64": FIXTURE_B64})["integrity"]
    v = sr.run_sri({"bytes_b64": FIXTURE_B64, "integrity_attr": good})
    assert v["attr_comparison"][0]["match"] is True
    bad = good[:-4] + "AAAA"
    v2 = sr.run_sri({"bytes_b64": FIXTURE_B64, "integrity_attr": bad})
    assert v2["attr_comparison"][0]["match"] is False


def test_sri_audit_vectors_main_written():
    a = sr.run_sri({"integrity_attr": "sha1-QLdDLCKNV2dzTor5xv1IutPqfA="})
    assert any("refused outright" in f["finding"] for f in a["attr_audit"])
    b = sr.run_sri({"integrity_attr": "sha384-c2hvcnQ="})  # 5 octets
    assert any("must be 48" in f["finding"] for f in b["attr_audit"])
    c = sr.run_sri({"integrity_attr": "sha384-QQ== sha384-AA=="})
    assert any("Duplicate" in f["finding"] or "duplicate" in f["finding"]
               for f in c["attr_audit"])


def test_sri_url_styles():
    moved = sr.run_sri({"bytes_b64": FIXTURE_B64,
                        "url": "https://cdn.jsdelivr.net/npm/"
                               "bootstrap@latest/dist/b.min.js"})
    assert any(f["level"] == "danger" for f in moved["url_audit"])
    rng = sr.run_sri({"bytes_b64": FIXTURE_B64,
                      "url": "https://cdn.jsdelivr.net/npm/"
                             "bootstrap@5/dist/b.min.js"})
    assert any(f["level"] == "warn" for f in rng["url_audit"])
    pinned = sr.run_sri({"bytes_b64": FIXTURE_B64,
                         "url": "https://cdn.jsdelivr.net/npm/"
                                "bootstrap@5.3.3/dist/b.min.js"})
    assert pinned["url_audit"][0].get("status") == "pinnable"
    # jamais de fetch : une URL seule est refusée par le nom
    with pytest.raises(sr.SriError) as e:
        sr.run_sri({"url": "https://x.test/y.js"})
    assert e.value.field == "bytes_b64"


# ============================================ contrats HTTP

def test_http_determinism_and_pins_payload():
    # inputs are STRINGS by contract (ScaleRequest precedent): the
    # closed grammar is "a decimal or fraction as text", numbers get a
    # declared 400 — pins therefore pass strings too
    for body in ({"foot_mm": "271"},
                 {"bytes_b64": FIXTURE_B64,
                  "url": "https://cdn.jsdelivr.net/npm/"
                         "bootstrap@5.3.3/dist/b.min.js"}):
        path = ("/api/v1/units/shoe_size" if "foot_mm" in body
                else "/api/v1/net/sri")
        r1 = client.post(path, json=body)
        r2 = client.post(path, json=body)
        assert r1.status_code == 200
        assert r1.content == r2.content
        assert "sha256" in r1.json()


def test_http_refusals_are_400_named():
    r = client.post("/api/v1/units/shoe_size",
                    json={"size": "42", "system": "cn"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "system"
    r = client.post("/api/v1/net/sri",
                    json={"bytes_b64": "!!!", "algorithms": ["sha1"]})
    assert r.status_code == 400


def test_http_exact_values_over_the_wire():
    r = client.post("/api/v1/units/shoe_size", json={"foot_mm": "271"})
    b = r.json()
    assert b["systems"]["eu"]["position"]["decimal"] == "42.6500"
    assert b["drift"]["per_step_gap_mm"] == {"fraction": "9/5",
                                             "decimal": "1.800000"}
    assert "280.000" in b["last_anchor"]["eu_last_mm_formula"] or \
        "280.000 mm" in b["last_anchor"]["eu_last_mm_formula"]
    r2 = client.post("/api/v1/net/sri", json={"text": "x"})
    assert r2.json()["integrity"].startswith("sha384-")
