# -*- coding: utf-8 -*-
# Bundle 145_hermes — LOT 145 : pack CELESTE (astro_precess_equatorial,
# units_freq_wavelength, bigear_snr_decode). Admissions 27-11 (registre
# L65/L66/L67 — payloads maison sha ed7e5fc9 / 423b030c / 813dcb95,
# campagne releveur celeste, segment Wow!/SETI). Les golds sont
# LITTERAUX de la compilation des rapports de campagne : la matiere du
# segment (ascension B1950->J2000, raie HI 1420 MHz <-> 21.1 cm,
# 6EQUJ5 / 72 s) rejouee contre les sources publiees NOMMEES :
#   - J. D. Ehman, « The Wow! Signal », Big Ear 30th anniversary report
#     (https://www.bigear.org/Wow30th/wow30th.htm) — formule et
#     constantes de precession au 1er ordre, corrections publiees
#     185.615 s / 352.62" / 185.463 s / 364.325", suite 6.5 14.5 26.5
#     30.5 19.5 5.5, echelle d'impression A-Z = 10..35, 6 x 12 = 72 s ;
#   - IAU 1976 (Lieske et al. 1977 / Explanatory Supplement) — systeme
#     des constantes m/n ;
#   - Wikipedia « Hydrogen line » — 21.106114054160(30) cm pour
#     1420.405751768(2) MHz ; c = 299792458 m/s EXACT (SI, 17e CGPM
#     1983) ; noms kHz/MHz/GHz : Reglement des radiocommunications ITU,
#     article 1.
# Le controle moderne recoupe : astropy 6.0.1 FK4(B1950)->ICRS rend
# 19h25m30.21s / -26d57'01" (positif) — cite par le rapport de campagne,
# dans les barres publiees +/- 10 s / +/- 20' ; rejoue ici comme CLAIM
# trace, pas comme oracle.
from decimal import Decimal

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

URL_PRECESS = "/api/v1/astro/precess"
URL_FREQ = "/api/v1/units/freq-wavelength"
URL_BIGEAR = "/api/v1/radio/bigear-snr"

# B1950 publie (Ehman 30th report, sections poshorn/neghorn) :
# 19h22m24.64s / 19h25m17.01s (precis), 19h22m25s / 19h25m17s (+/- 10s),
# dec -27d03m. J2000 publie : 19h25m31s (Ehman/Wikipedia/Gray-Marvel),
# 19h25m02s (Mendez 2025, arXiv 2508.10657, pointing recalibre),
# 19h25m26s (site PHL).


def precess(**kw):
    return client.post(URL_PRECESS, json=kw)


def freq(**kw):
    return client.post(URL_FREQ, json=kw)


def bigear(**kw):
    return client.post(URL_BIGEAR, json=kw)


# ========= astro_precess_equatorial — la formule d'Ehman rejouee =======

def test_p1_positive_horn_published_corrections():
    # Gold LITTERAL du rapport (Conversion of RA/Dec to Epoch 2000) :
    # entree 19h22m25s -27d03m, B1950->2000 : m = 3.073735,
    # n = 20.040425 ( = 1.3360283 s RA), Delta_RA = 185.615 s,
    # declination correction = 352.62". La porte rend les memes chiffres.
    r = precess(ra="19:22:25", dec="-27:03", from_epoch="1950",
                to_epoch="2000")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["rates"]["m_s_per_year"] == "3.073735"
    assert d["rates"]["n_arcsec_per_year"] == "20.040425"
    assert d["rates"]["n_ra_s_per_year"] == "1.3360283"
    assert d["delta"]["ra_s_of_time"] == "185.615"
    assert d["delta"]["dec_arcsec"] == "352.621"   # 2 dp publiees = 352.62
    assert d["output"]["ra_dms"] == "19:25:30.615"
    assert d["output"]["dec_dms"] == "-26:57:07.379"


def test_p2_digits_0_reproduces_published_j2000_19h25m31s():
    # LE gold titre : a la precision publiee (seconde), la porte rend
    # 19h25m31s — exactement le J2000 imprime par le rapport. Le refus
    # de fabriquer un chiffre plus faux que la source est le contrat.
    d = precess(ra="19:22:25", dec="-27:03", from_epoch="1950",
                to_epoch="2000", digits=0).json()
    assert d["output"]["ra_dms"] == "19:25:31"
    assert d["output"]["dec_dms"] == "-26:57:07"    # -26d57' publie


def test_p3_negative_horn_published_corrections():
    # 19h25m17s : Delta_RA = 185.463 s, declination correction =
    # 364.325" — les deux chiffres PUBLIES du rapport, au dernier
    # decimal print pret. J2000 arondi a la seconde = 19h28m22s publie.
    d = precess(ra="19:25:17", dec="-27:03", from_epoch="1950",
                to_epoch="2000").json()
    assert d["delta"]["ra_s_of_time"] == "185.463"
    assert d["delta"]["dec_arcsec"] == "364.325"
    d0 = precess(ra="19:25:17", dec="-27:03", from_epoch="1950",
                 to_epoch="2000", digits=0).json()
    assert d0["output"]["ra_dms"] == "19:28:22"


def test_p4_campaign_precise_inputs_replay_report_trace():
    # le rapport de campagne (controle positif) : avec 19h22m24.64s et
    # 19h25m17.01s, 185.616 s -> 19h25m30.256s et 185.463 s ->
    # 19h28m22.473s, 352.60" -> -26d57'07.4" (litteraux main du rapport)
    a = precess(ra="19h22m24.64s", dec="-27:03", from_epoch="1950",
                to_epoch="2000").json()
    assert a["delta"]["ra_s_of_time"] == "185.616"
    assert a["output"]["ra_dms"] == "19:25:30.256"
    assert a["output"]["dec_dms"] == "-26:57:07.404"
    b = precess(ra="19:25:17.01", dec="-27:03", from_epoch="1950",
                to_epoch="2000").json()
    assert b["delta"]["ra_s_of_time"] == "185.463"
    assert b["output"]["ra_dms"] == "19:28:22.473"
    # claim trace : a 1 dp la porte rend le chiffre du rapport
    assert Decimal(a["delta"]["dec_arcsec"]).quantize(
        Decimal("0.01")) == Decimal("352.60")


def test_p5_published_divergences_are_claims_not_answers():
    # la matiere du segment : TROIS J2000 publies pour la meme bande
    # d'ascension (Ehman/Wikipedia 31s ; Mendez 02s — pointing
    # recalibre, pas la meme entree ; site PHL 26s). La porte rend son
    # modele nomme ; l'ecart est joue ICI en arithmetique, jamais fondu.
    mine = Decimal(precess(ra="19:22:25", dec="-27:03",
                           from_epoch="1950", to_epoch="2000",
                           digits=3).json()["output"]["ra_dms"]
                   .split(":")[2])
    for who, pub in (("ehman", Decimal("31")),
                     ("mendez", Decimal("2")),
                     ("phl", Decimal("26"))):
        gap = pub - mine
        assert abs(gap) <= Decimal("30"), (who, str(gap))
    # ehman - mendez = 29 s d'ecart PUBLIE entre deux versions —
    # l'outil ne tranche pas, il nomme son modele (reference IAU 1976 +
    # rapport Ehman, version + sha dans chaque reponse).
    assert Decimal("31") - Decimal("2") == Decimal("29")


def test_p6_hms_forms_and_decimal_hours_round_trip():
    # 19h22m24.64s == 19:22:24.64 == 19.373511111h (heures decimales)
    a = precess(ra="19:22:24.64", dec="-27:03", from_epoch="1950",
                to_epoch="2000").json()
    b = precess(ra="19.373511111111", dec="-27.05", from_epoch="1950",
                to_epoch="2000").json()
    assert a["delta"] == b["delta"]


def test_p7_model_block_versioned_hashed_and_declared():
    d = precess(ra="19:22:25", dec="-27:03", from_epoch="1950",
                to_epoch="2000").json()
    m = d["model"]
    assert m["name"] == "iau1976-first-order-epoch-precession-145"
    assert "IAU 1976" in m["version"] and "1976" in m["reference"]
    assert "bigear.org/Wow30th" in m["reference"]
    assert m["neglected"].startswith("nutation")
    assert len(m["sha256"]) == 64 and d["sha256"]
    assert d["digits"]["mode"] == "HALF_UP"
    assert d["applied_defaults"] == ["digits"]


def test_p8_same_epoch_is_said_identity():
    # span 0 : identite arithmetique, dite — pas un nombre fabrique.
    d = precess(ra="19:22:25", dec="-27:03", from_epoch="1950",
                to_epoch="1950").json()
    assert d["delta"]["ra_s_of_time"] == "0.000"
    assert d["output"]["ra_dms"] == "19:22:25.000"
    assert d["note"].startswith("same_epoch_identity")


def test_p9_refusals_named():
    # pole : tan(Dec) diverge — refuse PAR LE NOM, designe dans le
    # message, jamais un 90 deg fabrique.
    r = precess(ra="19:22:25", dec="90", from_epoch="1950",
                to_epoch="2000")
    assert r.status_code == 400
    assert any("dec_polar_singularity" in e["message"]
               for e in r.json()["errors"]), r.text
    r = precess(ra="24:00:00", dec="-27:03", from_epoch="1950",
                to_epoch="2000")
    assert r.status_code == 400
    assert any("ra_hours_range" in e["message"]
               for e in r.json()["errors"]), r.text
    r = precess(ra="19:60:00", dec="-27:03", from_epoch="1950",
                to_epoch="2000")
    assert r.status_code == 400
    assert any("sexagesimal_field_range" in e["message"]
               for e in r.json()["errors"]), r.text
    r = precess(ra="19:22:25", dec="-27:+3", from_epoch="1950",
                to_epoch="2000")
    assert r.status_code == 400
    assert any("dec_field_sign" in e["message"]
               for e in r.json()["errors"]), r.text
    r = precess(ra="19:22:25", dec="-27:03", from_epoch="1700",
                to_epoch="2000")
    assert r.status_code == 400
    assert any("span_beyond_first_order" in e["message"]
               for e in r.json()["errors"]), r.text
    r = precess(ra="19:22:25", dec="-27:03", from_epoch="1200",
                to_epoch="1300")
    assert r.status_code == 400
    assert any("epoch_range" in e["message"]
               for e in r.json()["errors"]), r.text
    # extra=forbid ne negocie pas
    assert precess(ra="19:22:25", dec="-27:03", from_epoch="1950",
                   to_epoch="2000", nutation="on").status_code == 400
    assert precess(ra="19:22:25", dec="-27:03",
                   to_epoch="2000").status_code == 400  # from manque


# ============== units_freq_wavelength — lambda = c/f ==================

def test_u1_hi_line_published_last_digit():
    # LE gold du contrat (registre L66) : 1420.405751768 MHz ->
    # 21.106114054160 cm — la valeur publiee Wikipedia « Hydrogen line »
    # (21.106114054160(30) cm) reproduite au DERNIER CHIFFRE, c exact.
    r = freq(value="1420.405751768", unit="MHz", out="cm", digits=12)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["result"]["value"] == "21.106114054160"
    assert d["constants"]["c_m_per_s"] == "299792458"
    assert "17th CGPM" in d["constants"]["exactness"]
    assert "Hydrogen_line" in d["model"]["reference"]
    assert "21.106114054160" in d["model"]["reference"]


def test_u2_nominale_1420_mhz_is_not_21_cm():
    # le finding de campagne : « 21 cm » est un ARRONDI — a 1420 MHz
    # exact lambda fait 21.1121449296 cm (10 dp, litteral du rapport).
    d = freq(value="1420", unit="MHz", out="cm", digits=10).json()
    assert d["result"]["value"] == "21.1121449296"
    # l'expansion non tronquee du rapport, au chiffre pres (20 dp) :
    d2 = freq(value="1420.405751768", unit="MHz", out="m",
              digits=20).json()
    assert d2["result"]["value"] == "0.21106114054159799305"


def test_u3_round_trip_returns_the_published_frequency():
    # 21.106114054160 cm -> f : le repos HI 1420.405751768 MHz revient
    # au milli-hertz publie — la paire se joue dans les deux sens.
    d = freq(value="21.106114054160", unit="cm", out="MHz",
             digits=9).json()
    assert d["result"]["value"] == "1420.405751768"
    assert d["result"]["family"] == "frequency"


def test_u4_other_units_closed_dict():
    # la table fermee rendue entiere : l'autre famille, tous ses noms,
    # memes chiffres a travers la paire (input MHz -> famille longueur).
    d = freq(value="1420.405751768", unit="MHz", out="cm",
             digits=12).json()
    assert sorted(d["other_units"]) == ["cm", "km", "m", "mm", "nm",
                                        "um"]
    assert d["other_units"]["cm"] == "21.106114054160"
    assert d["other_units"]["m"] == "0.211061140542"
    w = freq(value="21.106114054160", unit="cm", out="MHz",
             digits=12).json()
    assert set(w["other_units"]) == {"Hz", "kHz", "MHz", "GHz", "THz"}
    assert w["other_units"]["MHz"].startswith("1420.405751767")
    assert w["other_units"]["GHz"] == "1.420405751768"


def test_u5_defaults_are_said():
    d = freq(value="1420", unit="MHz").json()
    assert d["result"]["unit"] == "m"          # defaut dit
    assert d["digits"]["value"] == 12
    assert sorted(d["applied_defaults"]) == ["digits", "out"]


def test_u6_refusals_named():
    # zero = DC, longueur d'onde infinie — refuse PAR LE NOM ;
    # unite hors table fermee refusee (le voisin units_convert est
    # designe : MHz n'y existe pas) ; meme famille refusee.
    r = freq(value="0", unit="MHz", out="cm")
    assert r.status_code == 400
    assert any("frequency_range" in e["message"]
               for e in r.json()["errors"]), r.text
    r = freq(value="5", unit="Mhz", out="cm")
    assert r.status_code == 400
    assert any("unit_unknown" in e["message"] and "units_convert"
               in e["message"] for e in r.json()["errors"]), r.text
    r = freq(value="5", unit="MHz", out="GHz")
    assert r.status_code == 400
    assert any("out_unit_same_family" in e["message"]
               for e in r.json()["errors"]), r.text
    r = freq(value="5", unit="MHz", out="furlong")
    assert r.status_code == 400
    assert any("out_unit_unknown" in e["message"]
               for e in r.json()["errors"]), r.text
    r = freq(value="1e30", unit="GHz", out="m")
    assert r.status_code == 400
    assert any("value_out_of_range" in e["message"]
               for e in r.json()["errors"]), r.text
    assert freq(value="-3", unit="m").status_code == 400
    assert freq(value="5", unit="MHz", out="cm",
                polarization="H").status_code == 400


def test_u7_exact_case_mu_spellings_share_one_scale():
    # um et µm sont la MEME unite publiee — les deux se lisent, la
    # reponse normalise, aucune devinette de famille.
    a = freq(value="21.106114054160", unit="µm", out="MHz",
             digits=6).json()
    b = freq(value="21.106114054160", unit="um", out="MHz",
             digits=6).json()
    assert a["result"] == b["result"]


# ============== bigear_snr_decode — l'echelle publiee =================

def test_b1_6equj5_intervals_published():
    # LE gold du contrat (registre L67) : 6EQUJ5 decompose en
    # intervalles — 6=[6,7) E=[14,15) Q=[26,27) U=[30,31) J=[19,20)
    # 5=[5,6) ; la suite 6.5 14.5 26.5 30.5 19.5 5.5 est celle du
    # rapport Ehman (regle de troncature + 0.5), pas une invention.
    r = bigear(string="6EQUJ5")
    assert r.status_code == 200, r.text
    d = r.json()
    forms = [x["interval"]["closed_form"] for x in d["digits"]]
    assert forms == ["[6,7)", "[14,15)", "[26,27)", "[30,31)",
                     "[19,20)", "[5,6)"]
    assert d["best_estimate_sequence"] == "6.5 14.5 26.5 30.5 19.5 5.5"
    assert d["peak"]["interval"] == "[30,31)"
    assert d["peak"]["best_estimate"] == "30.5"
    assert d["peak"]["chars"] == [{"index": 3, "char": "U"}]
    # la cle du code, litterale de la page : ord('U') - ord('A') + 10
    assert ord("U") - ord("A") + 10 == 30


def test_b2_duration_72s_published_and_span_said():
    # 72 s publie = 6 rangees x 12 s (l'integrale 10 s + ~2 s de
    # calcul) ; le span premier->dernier = 60 s est DIT a cote — deux
    # definitions rendues, precedent b137. La HPBW 37 s est nommee NON
    # duree (l'erreur que le rapport releve).
    d = bigear(string="6EQUJ5").json()
    assert d["cadence"]["duration_nominal_s"] == "72"
    assert d["cadence"]["first_to_last_s"] == "60"
    assert d["cadence"]["seconds_per_row"] == "12"
    assert d["cadence"]["integration_s"] == "10"
    assert "37 s HPBW" in d["cadence"]["note"]
    assert d["input"]["rows"] == 6


def test_b3_scale_closed_at_both_ends():
    # A = 10, Z = 35 — les bornes publiees « 10 through 35 » ;
    # l'espace est le code du zero (zero imprime = blanc).
    d = bigear(string="AZ").json()
    assert d["digits"][0]["snr_truncated"] == 10
    assert d["digits"][1]["snr_truncated"] == 35
    assert d["digits"][1]["interval"]["closed_form"] == "[35,36)"
    s = bigear(string=" 5").json()
    assert s["digits"][0]["char"] == "space"
    assert s["digits"][0]["interval"]["closed_form"] == "[0,1)"
    assert s["digits"][0]["best_estimate"] == "0.5"


def test_b4_published_divergences_and_unsourced_noise():
    # la matiere du registre L67 : divergences de PIC publiees
    # (30.5 Ehman / 30.1 Mendez / entre 30 et 31 Wikipedia / 30 sigma
    # Kraus, chaque variante avec sa source nommee) ; le « bruit 10 »
    # est ABSENT des sources — rendu comme tel, la confusion probable
    # (canal 10 kHz, integration 10 s) est DITE.
    d = bigear(string="6EQUJ5").json()
    pv = d["published_variants"]
    vals = [v["value"] for v in pv["peak_snr"]]
    assert vals == ["30.5 +/- 0.5", "30.1 +/- 0.4",
                    "between 30 and 31", "30 sigma"]
    assert all(v["source"].startswith("https://") for v in pv["peak_snr"])
    assert pv["ambient_noise_10"].startswith("ABSENT")
    assert "10 kHz" in pv["ambient_noise_10"]
    assert d["not_a_message"].startswith("the sequence is an intensity")


def test_b5_scale_block_versioned_hashed():
    d = bigear(string="6EQUJ5").json()
    m = d["scale"]
    assert m["name"] == "bigear-printout-scale-145"
    assert "bigear.org/Wow30th" in m["reference"]
    assert len(m["sha256"]) == 64 and d["sha256"]


def test_b6_refusals_named():
    # '0' n'existe pas dans le code publie (zero = blanc) ; les
    # minuscules sont hors alphabet majuscule ; caractere inconnu
    # refuse ; vide refuse ; fenetre 200 caracteres borde.
    for bad, want in (("0", "zero_code_absent"),
                      ("6equj5", "lowercase_code"),
                      ("6EQU!5", "unknown_code"),
                      ("", "empty_printout")):
        r = bigear(string=bad)
        assert r.status_code == 400, bad
        assert any(want in e["message"] for e in r.json()["errors"]), \
            (bad, r.text)
    assert bigear(string="A" * 201).status_code == 400
    assert bigear(string="6EQUJ5", channel=2).status_code == 400
    assert bigear().status_code == 400


# ============ determinisme et fermeture ===============================

def test_d1_same_request_same_bytes():
    for url, body in ((URL_PRECESS, {"ra": "19:22:25", "dec": "-27:03",
                                     "from_epoch": "1950",
                                     "to_epoch": "2000"}),
                      (URL_FREQ, {"value": "1420.405751768",
                                  "unit": "MHz", "out": "cm",
                                  "digits": 12}),
                      (URL_BIGEAR, {"string": "6EQUJ5"})):
        a = client.post(url, json=body)
        b = client.post(url, json=body)
        assert a.status_code == 200
        assert a.content == b.content
        j = a.json()
        assert j["sha256"] and len(j["sha256"]) == 64


def test_d2_batch_routes_the_three_by_name():
    # le dispatcher ne doit pas etre aveugle (registre, case 3).
    r = client.post("/api/v1/batch", json={
        "tool": "bigear_snr_decode",
        "payloads": [{"string": "6EQUJ5"}, {"string": "A"}]})
    assert r.status_code == 200, r.text
    got = r.json()
    assert got["failed"] == 0
    results = [x["result"] for x in got["results"]]
    assert results[0]["best_estimate_sequence"] == \
        "6.5 14.5 26.5 30.5 19.5 5.5"
    assert results[1]["peak"]["interval"] == "[10,11)"


def test_d3_pain_routes_now_answer():
    # douleurs FERMEES du segment (registres : route [] FR+EN, 0
    # occurrence epoch/precess au manifest) : ces requetes nomment
    # desormais un outil du lot.
    for q, want in (
            ("precess B1950 J2000 right ascension",
             "astro_precess_equatorial"),
            ("precession des equinoxes coordonnees",
             "astro_precess_equatorial"),
            ("convert epoch fk4 to j2000 coordinates",
             "astro_precess_equatorial"),
            ("1420 MHz wavelength in cm", "units_freq_wavelength"),
            ("longueur d onde frequence hertz", "units_freq_wavelength"),
            ("mhz to nm radio frequency", "units_freq_wavelength"),
            ("decode 6EQUJ5 big ear wow", "bigear_snr_decode"),
            ("wow signal snr printout letters", "bigear_snr_decode")):
        r = client.get("/route", params={"q": q})
        assert r.status_code == 200
        names = [e["tool"] for e in r.json()["tools"]]
        assert want in names, (q, names)


def test_d4_tools_json_surface_exists():
    for name in ("astro_precess_equatorial", "units_freq_wavelength",
                 "bigear_snr_decode"):
        r = client.get("/tools/%s.json" % name)
        assert r.status_code == 200, name
        spec = r.json()
        assert spec["tier"] == "free"
        assert "Free." in spec["schema"]["description"]
