# -*- coding: utf-8 -*-
"""bundle146_hermes — PACK VERIFICATION (doi_name_equivalence,
xbrl_decimals_calc_consistency, erc20_raw_units). Admissions 27-11
(registre L16/L17/L21 — recus proposeur a4ba4e61…ea62 / 980850a4…27d8 /
887dffa67cadaab476e8182e29513b290b07f31a6e8c40fb3d66a199311c311e ;
suite integrite, audits de campagne vague 1).

Matiere des golds : la compilation des rapports de campagne (vague 1),
sections publication (l. 448-532), ESEF/XBRL (l. 1359-1486),
Base ERC-20 (l. 1966-1988), recoupee au primaire publie NOMME :
  - DOI Handbook, DOI Foundation — publication date September 2025,
    https://www.doi.org/doi-handbook/DOIHandbook_2025.pdf, sha256
    1f6c73c12890a8bef8f30d06a7fe1de90723318e796bfff68d4a64759b4ddcf3
    (re-telé au build, sha identique au sha consigne refs/ du
    rapport ; version du record = PDF). §4.3.4 Ex.1 (SMPTE S/s,
    EQUIVALENTS) et Ex.2 (Á.GUTIÉRREZ.ZARZA.02.2018.03, NON
    équivalents) rejoues LITTERALEMENT ; §4.3.2 Ex.2 « 10.500.100 » ;
    §4.7 « 10.1000/456#789 » = « 10.1000/456%23789 » ; §6.5 le
    shortDOI « 10/abcde » n'est pas un DOI name ; §4.3.1 le Graphic
    inclut l'espace — deux suffixes qui different par un espace
    interne sont deux noms ;
  - XBRL Calculations 1.1, Recommendation 2023-02-22 (rounded fact
    value interval [v±0.5*10^-d], INF = point, consistent iff CT
    overlaps RT — §5.2.3/§5.2.5 ; arcrole
    https://xbrl.org/2023/arcrole/summation-item) contre XBRL 2.1
    §5.2.5.2 (somme arrondie aux decimals du total, tie half-up away
    from zero DIT) — intervalles traces main sur les filings reels
    (l. 1407-1412) : SCBSM [13832500,13833500] vs [13833000,
    13835000] recoupement ; 2.1 rend 13834000 != 13833000 ; le tag
    doublon 13834000 retourne le 2.1 seul ; Sodexo [302500000,
    303500000] vs [302000000,304000000] coherents des deux lois ;
    GB a INF rendu en POINTS — l'ecart 910782 - 540375 = 370407 est
    la jambe HeldForSale omise par l'extraction (claim du test,
    l. 1358 : artefact attribue, jamais fondu dans l'outil) ;
  - EIP-20 (decimals() uint8, scaling value/10**decimals) + uint256
    0..2**256-1 ; decimales par token CITEES du corpus (l. 1963) :
    USDC 6, cbBTC 8, AERO/DEGEN/BRETT/TOSHI/MOG 18 ; MOG totalSupply
    116162348802077343159857936548537 LITTERAL du rapport (l. 1969).

Contraste rejoue vivant : eth_units au tip echoit le MOG en
« 116162348802077343159857936549000 » — +463 wei FABRIQUES (mesure
B2 46ecf95f de la campagne), verifie dans test_e7 contre le voisin,
la ou erc20_raw_units rend …548537 exact.

Limite dite a l'admission (brief 27-11) : le parsing brut->champs est
la sœur admise NON construite refs_biblio_scan (L68) — ces trois
outils recoivent des champs cites, jamais un document.
"""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

URL_DOI = "/api/v1/id/doi-equivalence"
URL_XBRL = "/api/v1/xbrl/calc-consistency"
URL_RAW = "/api/v1/eth/raw-units"

MOG_RAW = "116162348802077343159857936548537"
UINT256_MAX = ("1157920892373161954235709850086879078532699846656"
               "40564039457584007913129639935")
UINT256_OVERFLOW = ("115792089237316195423570985008687907853269984"
                    "665640564039457584007913129639936")  # 2**256


def doi(a, b):
    return client.post(URL_DOI, json={"a": a, "b": b})


def xbrl(total, parts):
    return client.post(URL_XBRL, json={"total": total, "parts": parts})


def raw(r, d):
    return client.post(URL_RAW, json={"raw": r, "decimals": d})


# ============ doi_name_equivalence — Handbook §4.3 rejoué =============

def test_d1_handbook_ex1_s_s_equivalent():
    # §4.3.4 Ex.1 LITTERAL : 10.5594/SMPTE.ST2067-21.2020 vs
    # 10.5594/sMPTE.sT2067-21.2020 — U+0053 identique a U+0073, SEULS
    # ces 26 plis-la. La mesure du segment : list_dedupe exact les
    # SPLITTAIT a tort (gate 95e20bec).
    r = doi("10.5594/SMPTE.ST2067-21.2020", "10.5594/sMPTE.sT2067-21.2020")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["verdict"] == "EQUIVALENT"
    assert d["equivalent"] is True
    # §4.3.1 EXAMPLE : prefix 10.5594 = DI 10 + registrant 5594,
    # suffix SMPTE.ST2067-21.2020.
    a = d["a"]
    assert a["valid"] and a["errors"] == []
    assert a["prefix"] == "10.5594"
    assert a["directory_indicator"] == "10"
    assert a["registrant_code"] == "5594"
    assert a["suffix"] == "SMPTE.ST2067-21.2020"
    assert a["name"] == "10.5594/SMPTE.ST2067-21.2020"
    assert a["form"] == "bare"
    assert len(d["sha256"]) == 64


def test_d2_handbook_ex2_a_acute_NOT_equivalent():
    # §4.3.4 Ex.2 LITTERAL : 10.26321/Á.GUTIÉRREZ.ZARZA.02.2018.03 vs
    # la variante minuscule — U+00C1 et U+00E1 ne sont PAS consideres
    # identiques. La mesure du segment : le mode texte des outils
    # existants MERGEAIT ce couple (gold NOT equivalent).
    upper = "10.26321/\u00c1.GUTI\u00c9RREZ.ZARZA.02.2018.03"
    lower = "10.26321/\u00e1.guti\u00e9rrez.zarza.02.2018.03"
    d = doi(upper, lower).json()
    assert d["verdict"] == "NOT_EQUIVALENT"
    assert d["equivalent"] is False
    assert d["a"]["valid"] and d["b"]["valid"]
    assert d["reference"]["pdf_sha256"].startswith("1f6c73c1")


def test_d3_four_forms_of_one_doi_gold_one():
    # Le corpus du segment (batch 2 9d03a0f5, batch 3 8843c962,
    # batch 5 6f64c52b → gate 95e20bec) : quatre formes ecrites d'un
    # meme DOI (doi.org mixed / ELIFE / dx.doi.org / doi:) rendaient
    # 4 / 3 / 4 distincts — gold UN. Ici les deux paires croisees
    # disent EQUIVALENT.
    d1 = doi("https://doi.org/10.7554/eLife.12095",
             "doi:10.7554/ELIFE.12095").json()
    assert d1["verdict"] == "EQUIVALENT"
    assert d1["a"]["form"] == "proxy" and d1["b"]["form"] == "label"
    assert d1["a"]["name"] == "10.7554/eLife.12095"
    d2 = doi("http://dx.doi.org/10.7554/eLife.12095",
             "10.7554/eLife.12095").json()
    assert d2["verdict"] == "EQUIVALENT"


def test_d4_registrant_dot_groups():
    # §4.3.2 Ex.2 : prefix hypothetique 10.500.100 — registrant code
    # « 500.100 », groupes de chiffres separes par U+002E.
    d = doi("10.500.100/xyz", "10.500.100/xyz").json()
    assert d["verdict"] == "EQUIVALENT"
    assert d["a"]["registrant_code"] == "500.100"
    assert d["a"]["valid"]


def test_d5_percent_pair_handbook_47():
    # §4.7 EXAMPLE LITTERAL : « 10.1000/456#789 » est percent-encode
    # en « 10.1000/456%23789 ». Le nom nu garde le # ; la forme proxy
    # est decodee AVANT comparaison.
    d = doi("10.1000/456#789", "https://doi.org/10.1000/456%23789").json()
    assert d["verdict"] == "EQUIVALENT"
    assert d["a"]["percent_decoded"] is False   # bare = literal
    assert d["b"]["percent_decoded"] is True    # proxy = decoded


def test_d6_no_normalization_composed_vs_combining():
    # §4.3.4 : « no normalization, as defined in ISO/IEC 10646, is
    # performed » — Á precompose (U+00C1) vs A + combining acute
    # (U+0301) sont DEUX NOMS. Le pli NFC des voisins les fond —
    # c'est exactement la faute que cette porte refuse de commettre.
    composed = "10.1000/\u00c1ngel"
    decomposed = "10.1000/A\u0301ngel"
    d = doi(composed, decomposed).json()
    assert d["verdict"] == "NOT_EQUIVALENT"
    assert d["a"]["valid"] and d["b"]["valid"]


def test_d7_angstrom_sign_not_normalized():
    # §4.2 bullet 3 (litige publie) : le glyphe Å peut etre
    # ANGSTROM SIGN (U+212B) ou LATIN CAPITAL A WITH RING (U+00C5).
    # §4.3.4 dit NO normalization — noms DISTINCTS. text_normalize
    # (NFKC) les fondrait ; can-fail : cette porte ne le fait pas.
    d = doi("10.1000/\u212bngstrom", "10.1000/\u00c5ngstrom").json()
    assert d["verdict"] == "NOT_EQUIVALENT"


def test_d8_shortdoi_is_not_a_doi_name():
    # §6.5 LITTERAL : « shortDOIs are not themselves DOI names and
    # therefore do not conform to the ISO standard syntax ».
    # §4.3.2 : indicator 10 sans registrant = jamais un prefix.
    d = doi("10/abcde", "10/abcde").json()
    assert d["verdict"] == "INVALID"
    assert d["equivalent"] is None
    assert "shortdoi_not_a_doi_name" in d["a"]["errors"]


def test_d9_grammar_refusals_named():
    # Chaque refus par son NOM — le contrat de reparation du citeur.
    cases = (
        ("20.1000/x", "directory_indicator_not_10"),   # §4.3.2 : 10 seul
        ("10.abc/x", "prefix_grammar_not_digits"),     # registrant non chiffre
        ("10.1000/", "empty_suffix"),                  # §4.3.3 suffixe
        ("10.1000", "missing_solidus"),                # §4.3.1 U+002F
        ("https://example.org/10.1000/1",
         "url_host_unsupported"),                      # proxy ferme
        ("10.1000/a\tb", "control_char_not_graphic"),  # §4.3.1 controles exclus
        ("", "empty_input"),
    )
    for bad, want in cases:
        r = doi(bad, "10.1000/123456")
        assert r.status_code == 200, (bad, r.text)
        d = r.json()
        assert want in d["a"]["errors"], (bad, d["a"]["errors"])
        assert d["verdict"] == "INVALID"
    assert doi("10.1000/1", "").json()["b"]["errors"] == ["empty_input"]


def test_d10_spaces_are_graphic_and_case_folds_only_ascii():
    # §4.3.1 : le Graphic inclut les ESPACES — un suffixe avec espace
    # est un nom valide et « a b » != « ab ». Pli ASCII seulement :
    # ABC vs abd DIFFERENT par le d, pas par la casse ; le trim
    # exterieur est DIT (trimmed), pas silencieux.
    assert doi("10.1000/a b", "10.1000/a b").json()["verdict"] == \
        "EQUIVALENT"
    assert doi("10.1000/a b", "10.1000/ab").json()["verdict"] == \
        "NOT_EQUIVALENT"
    assert doi("10.1000/ABC", "10.1000/abd").json()["verdict"] == \
        "NOT_EQUIVALENT"
    d = doi("  10.1000/123456  ", "10.1000/123456").json()
    assert d["verdict"] == "EQUIVALENT" and d["a"]["trimmed"] is True
    assert doi("https://doi.org/10.1000/50%25off",
               "10.1000/50%off").json()["verdict"] == "EQUIVALENT"


def test_d11_no_check_digit_is_invented():
    # §4.3.5 : « The DOI System does not itself make use of check
    # digits ». La porte ne calcule JAMAIS une somme de controle —
    # mesure du batch 1 idx 19 (no candidates). Un suffixe court,
    # opaque, passe sans qu'un « expected char » soit invente.
    d = doi("10.1000/182", "10.1000/182").json()
    assert d["verdict"] == "EQUIVALENT" and d["a"]["valid"]
    assert "no check digit" in d["rule"]["check_digit"]
    blob = str(d)
    for word in ("check", "digit"):
        assert word in d["rule"]["check_digit"].lower()


def test_d12_structural_refusals():
    # Champs absents / de type inadequat = 400 NOMME, jamais un
    # verdict fabrique ; cle inconnue refusee par son nom.
    assert client.post(URL_DOI, json={"a": "10.1000/1"}).status_code \
        == 400
    assert client.post(URL_DOI, json={"a": 5, "b": "10.1/x"}). \
        status_code == 400
    r = client.post(URL_DOI, json={"a": "10.1000/1", "b": "10.1000/1",
                                   "mode": "fuzzy"})
    assert r.status_code == 400
    assert "mode" in str(r.json())


# ========== xbrl_decimals_calc_consistency — filings traces main =======

def test_x1_scbsm_double_verdict_the_measured_split():
    # Gold LITTERAL du rapport ESEF (l. 1359, 1408-1409) : SCBSM FY2026
    # ProfitLoss tague 13833000 (decimals -3) vs 13828000 + 6000.
    # Calc 1.1 : [13833000,13835000] recoupe [13832500,13833500] →
    # CONSISTENT. XBRL 2.1 §5.2.5.2 : somme 13834000 != 13833000 →
    # INCONSISTENT. La porte voisine rendait « CONTRADICTED
    # -1000.00 » sans pouvoir NOMMER la loi de l'ecart.
    r = xbrl({"value": "13833000", "decimals": "-3"},
             [{"value": "13828000", "decimals": "-3"},
              {"value": "6000", "decimals": "-3"}])
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["total"]["interval"] == ["13832500", "13833500"]
    assert d["sum_interval"] == ["13833000", "13835000"]
    assert d["verdicts"]["calc_1_1"] == "CONSISTENT"
    assert d["verdicts"]["xbrl_2_1"] == "INCONSISTENT"
    assert d["verdicts_differ"] is True
    assert d["sum_exact"] == "13834000"
    assert d["rounded_sum_2_1"] == "13834000"
    assert d["delta_2_1"] == "1000"
    assert d["parts"][0]["interval"] == ["13827500", "13828500"]
    assert "2023-02-22" in d["rules"]["calc_1_1"]
    assert "5.2.5.2" in d["rules"]["xbrl_2_1"]


def test_x2_scbsm_duplicate_tag_flips_only_21():
    # Second gold SCBSM (l. 1368 : « SCBSM 13833000 AND 13834000 ») :
    # le fait triplement tague (fact_495308 / 495522 / 495580). Avec
    # 13834000 pour total, les DEUX lois tombent d'accord — la
    # divergence du depot vit dans ce couple de verdicts, rendu tel
    # quel, jamais moyenne.
    d = xbrl({"value": "13834000", "decimals": "-3"},
             [{"value": "13828000", "decimals": "-3"},
              {"value": "6000", "decimals": "-3"}]).json()
    assert d["verdicts"] == {"calc_1_1": "CONSISTENT",
                             "xbrl_2_1": "CONSISTENT"}
    assert d["verdicts_differ"] is False
    assert d["total"]["interval"] == ["13833500", "13834500"]
    assert d["delta_2_1"] == "0"


def test_x3_sodexo_consistent_under_both_laws():
    # Gold du rapport ESEF (l. 1368, 1410-1411) : 303000000 = 304000000 +
    # (-1000000) a decimals -6. Intervalles main : total [302500000,
    # 303500000], somme [302000000, 304000000] — recoupement ET
    # somme exacte : controle positif, la porte rend verte la ou le
    # depot est coherent.
    d = xbrl({"value": "303000000", "decimals": "-6"},
             [{"value": "304000000", "decimals": "-6"},
              {"value": "-1000000", "decimals": "-6"}]).json()
    assert d["total"]["interval"] == ["302500000", "303500000"]
    assert d["sum_interval"] == ["302000000", "304000000"]
    assert d["verdicts"] == {"calc_1_1": "CONSISTENT",
                             "xbrl_2_1": "CONSISTENT"}
    assert d["sum_exact"] == "303000000"


def test_x4_gb_infinite_points_and_gap_claim():
    # Gold du rapport ESEF (l. 1368, 1412) : GB FY2024 A = CA + NCA a decimals
    # ABSENT (= INF) : 406950 + 133425 = 540375 contre 910782 —
    # INCONSISTENT des deux lois, intervalles ponctuels. Le gap
    # 370407 EST la ligne HeldForSale omise par l'extraction du
    # rapport (l. 1358) — joue ICI comme claim d'arithmetique, la
    # porte ne voit jamais la jambe absente.
    d = xbrl({"value": "910782", "decimals": "INF"},
             [{"value": "406950", "decimals": "INF"},
              {"value": "133425", "decimals": "INF"}]).json()
    assert d["verdicts"] == {"calc_1_1": "INCONSISTENT",
                             "xbrl_2_1": "INCONSISTENT"}
    assert d["total"]["interval"] == ["910782", "910782"]
    assert d["sum_exact"] == "540375"
    assert int(910782) - int(d["sum_exact"]) == 370407   # HFS leg
    assert d["delta_2_1"] == "-370407"


def test_x5_values_as_the_filing_writes_them():
    # xBRL-JSON ecrit « 296089.0 » — l'echo garde la chaine EXACTE
    # (decimale tail incluse), decimals en argument entier rendu par
    # sa chaine, INF passe partout. Contraste nomme :
    # invoice_validate_totals forcerait « 14849000000.00 » au cent.
    d = xbrl({"value": "303000000.0", "decimals": -6},
             [{"value": "304000000.0", "decimals": -6},
              {"value": "-1000000.0", "decimals": -6}]).json()
    assert d["total"]["value"] == "303000000.0"
    assert d["total"]["decimals"] == "-6"
    assert d["verdicts"] == {"calc_1_1": "CONSISTENT",
                             "xbrl_2_1": "CONSISTENT"}


def test_x6_refusals_named_as_repair_contracts():
    # Valeur plus fine que ses propres decimals = conflit NOMME
    # (regle §4.6.7, le scale check 66/66 de la campagne) ; float =
    # refuse par le nom (binaire64 pretendrait une precision que le
    # depot n'a pas dite) ; parts vide, decimals hors contrat, cle
    # inconnue — chaque 400 nomme son champ.
    r = xbrl({"value": "13833001", "decimals": "-3"},
             [{"value": "1", "decimals": "0"}])
    assert r.status_code == 400
    assert any("total.value" in str(e) for e in r.json()["errors"]), \
        r.text
    assert any("4.6.7" in str(e) for e in r.json()["errors"])
    r = xbrl({"value": 13833000.0, "decimals": "-3"},
             [{"value": "1", "decimals": "0"}])
    assert r.status_code == 400
    assert any("binary64" in str(e) or "string" in str(e)
               for e in r.json()["errors"]), r.text
    assert xbrl({"value": "1", "decimals": "0"}, []).status_code == 400
    assert xbrl({"value": "1", "decimals": "maybe"},
                [{"value": "1", "decimals": "0"}]).status_code == 400
    assert xbrl({"value": "1", "decimals": "200"},
                [{"value": "1", "decimals": "0"}]).status_code == 400
    r = client.post(URL_XBRL, json={
        "total": {"value": "1", "decimals": "0", "unit": "EUR"},
        "parts": [{"value": "1", "decimals": "0"}]})
    assert r.status_code == 400
    assert "unit" in str(r.json()), r.text
    r = client.post(URL_XBRL, json={
        "total": {"value": "1", "decimals": "0"},
        "parts": [{"value": "1", "decimals": "0", "concept": "x"}]})
    assert r.status_code == 400 and "concept" in str(r.json()), r.text


# ============ erc20_raw_units — l'echelle sans arrondi =================

def test_e1_mog_thirty_three_digits_exact():
    # Gold LITTERAL du rapport Base ERC-20 (l. 1969) : MOG-Base totalSupply
    # 116162348802077343159857936548537 — 33 chiffres, decimals 18
    # (CITEES l. 1963). La rendue au dernier chiffre, la ou la
    # mesure de campagne a peche eth_units en arrondi.
    r = raw(MOG_RAW, 18)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["human"] == "116162348802077.343159857936548537"
    assert d["integer_part"] == "116162348802077"
    assert d["fraction_part"] == "343159857936548537"
    assert d["raw_digits"] == 33
    assert d["applied_defaults"] == []


def test_e2_uint256_max_seventy_eight_digits():
    # « up to 78 digits » du contrat admis : 2**256-1 (18 decimals,
    # la classe des tokens ERC-20 a 18) rendu ENTIER — la mesure
    # B1/B2 montrait 2^256−1 tronque en « 1157920892373161954235709
    # 85009·10^48 ». Tracé main : pow(2,256)-1, 78 chiffres.
    d = raw(UINT256_MAX, 18).json()
    assert d["raw_digits"] == 78
    assert d["human"] == ("11579208923731619542357098500868790785326"
                          "9984665640564039457.584007913129639935")
    assert len(d["fraction_part"]) == 18


def test_e3_edge_scales_d0_and_d77():
    # decimals = argument, jamais devine : 0 = identite (classe des
    # tokens sans decimale), 77 = borne SUPERIEURE du contrat admis
    # (0..77 — le max uint256 fait 78 chiffres).
    d = raw("1000000", 0).json()
    assert d["human"] == "1000000" and d["fraction_part"] == ""
    d = raw("1", 77).json()
    assert d["human"] == "0." + "0" * 76 + "1"
    assert len(d["human"]) == 1 + 1 + 77


def test_e4_rungs_the_neighbor_lacks_d6_d8():
    # eth_units ne connait que wei/gwei/ether — aucun barreau 10^6 ni
    # 10^8 : USDC (decimals 6 CITEES) et cbBTC (8 CITEES) devaient
    # passer par math_calc /10**d. Ici l'echelle est l'argument.
    assert raw("1000000000000", 6).json()["human"] == "1000000.000000"
    d = raw("42069000000", 8).json()
    assert d["human"] == "420.69000000"
    assert len(d["fraction_part"]) == 8


def test_e5_overflow_and_out_of_domain_refused_by_name():
    # « 2^256 refused » (contrat litteral) : refuse, JAMAIS reduit
    # mod 2**256 (le wrap EVM est un autre contrat). decimals 78
    # hors domaine ferme ; hex et floats refuses par le nom.
    r = raw(UINT256_OVERFLOW, 18)
    assert r.status_code == 400, r.text
    errs = str(r.json())
    assert "uint256" in errs and "wrapped" in errs
    assert raw("1", 78).status_code == 400
    assert raw("1", -1).status_code == 400
    r = raw("0x4d2", 18)
    assert r.status_code == 400 and "hex" in str(r.json())
    assert raw("-5", 18).status_code == 400
    assert raw("12.5", 18).status_code == 400
    assert client.post(URL_RAW, json={"raw": "1", "decimals": 18,
                                      "token": "USDC"}).status_code == 400


def test_e6_leading_zeros_said_not_silent():
    # B8 : tout ce que l'outil applique se REND dans la reponse.
    d = raw("0007", 2).json()
    assert d["human"] == "0.07" and d["raw"] == "7"
    assert d["applied_defaults"] == ["raw_leading_zeros_stripped"]


def test_e7_eth_units_plus463_wei_replayed_live():
    # Le contraste de campagne (B2 46ecf95f), REJOUÉ vivant contre
    # le voisin au tip : eth_units echoit le MOG en …549000, soit
    # +463 wei FABRIQUES par l'arrondi a 30 chiffres significatifs.
    # erc20_raw_units rend …548537 — l'ecart est arithmetique, pas
    # rhetorique : (wei rendu) - raw == 463.
    n = client.post("/api/v1/eth/units",
                    json={"value": MOG_RAW, "unit": "wei"})
    assert n.status_code == 200, n.text
    assert n.json()["wei"] == "116162348802077343159857936549000"
    assert int(n.json()["wei"]) - int(MOG_RAW) == 463
    mine = raw(MOG_RAW, 18).json()
    assert mine["human"].endswith("548537")
    assert mine["human"].replace(".", "") == MOG_RAW   # rien ne bouge


def test_e8_no_rounding_anywhere_by_construction():
    # Can-fail de classe : l'output est un DEPLACEMENT de virgule —
    # chaque chiffre de raw survit, en ordre, sans qu'un seul soit
    # arrondi. (La faute des voisins : 30+ chiffres = troncature
    # silencieuse.)
    for s, dd in ((MOG_RAW, 18), (UINT256_MAX, 77), ("123456789" * 5, 4)):
        d = raw(s, dd).json()
        assert d["human"].replace(".", "").lstrip("0") == \
            s.lstrip("0"), (s, dd)
        assert len(d["fraction_part"]) == (dd if int(s) else 0)


# ============ determinisme, batch, routing ============================

def test_z1_same_request_same_bytes_each_sha():
    for url, body in ((URL_DOI, {"a": "10.5594/SMPTE.ST2067-21.2020",
                                 "b": "10.5594/sMPTE.sT2067-21.2020"}),
                      (URL_XBRL, {"total": {"value": "13833000",
                                            "decimals": "-3"},
                                  "parts": [{"value": "13828000",
                                             "decimals": "-3"},
                                            {"value": "6000",
                                             "decimals": "-3"}]}),
                      (URL_RAW, {"raw": MOG_RAW, "decimals": 18})):
        a = client.post(url, json=body)
        b = client.post(url, json=body)
        assert a.status_code == 200
        assert a.content == b.content          # memes bytes, pour toujours
        assert len(a.json()["sha256"]) == 64


def test_z2_batch_dispatches_by_name():
    r = client.post("/api/v1/batch", json={
        "tool": "erc20_raw_units",
        "payloads": [{"raw": MOG_RAW, "decimals": 18},
                     {"raw": UINT256_OVERFLOW, "decimals": 18}]})
    assert r.status_code == 200, r.text
    got = r.json()
    assert got["failed"] == 1
    results = got["results"]
    assert results[0]["result"]["human"].endswith("548537")
    assert "invalid_input" in str(results[1]["error"])
    assert "uint256" in str(results[1]["error"])
    r = client.post("/api/v1/batch", json={
        "tool": "doi_name_equivalence",
        "payloads": [{"a": "10.1000/456#789",
                      "b": "https://doi.org/10.1000/456%23789"}]})
    assert r.json()["results"][0]["result"]["verdict"] == "EQUIVALENT"


def test_z3_pain_routes_now_answer():
    # Douleurs FERMEES du lot (lues a l'admission) : /route q=doi
    # NO_MATCH (6c05721d) ; « xbrl fact check » / « decimals inferred
    # precision » sans l'outil ; « uint256 », « erc20 decimals »
    # silencieux. Chacune nomme desormais son outil.
    for q, want in (
            ("doi", "doi_name_equivalence"),
            ("doi syntax validate", "doi_name_equivalence"),
            ("doi normalize case insensitive", "doi_name_equivalence"),
            ("doi parse prefix suffix", "doi_name_equivalence"),
            ("xbrl fact check", "xbrl_decimals_calc_consistency"),
            ("xbrl decimals calculation consistency",
             "xbrl_decimals_calc_consistency"),
            ("esef filing decimals interval",
             "xbrl_decimals_calc_consistency"),
            ("uint256", "erc20_raw_units"),
            ("erc20 decimals", "erc20_raw_units"),
            ("raw token supply human exact", "erc20_raw_units")):
        r = client.get("/route", params={"q": q})
        assert r.status_code == 200
        names = [e["tool"] for e in r.json()["tools"]]
        assert want in names, (q, names)


def test_z4_tools_json_surface():
    for name in ("doi_name_equivalence", "xbrl_decimals_calc_consistency",
                 "erc20_raw_units"):
        r = client.get("/tools/%s.json" % name)
        assert r.status_code == 200, name
        spec = r.json()
        assert spec["tier"] == "free"
        assert "Free." in spec["schema"]["description"]
