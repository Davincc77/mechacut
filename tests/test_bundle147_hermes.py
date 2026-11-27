# -*- coding: utf-8 -*-
"""bundle147_hermes — SUITE INTEGRITE (refs_biblio_scan, foia_sheet_audit).
Admissions 27-11, registre L68 (recu f4a7a9904e766db6) + L69 (recu
bb06eabd7aceefd3) ; suite integrite (Vince) / campagne Vault (Vince).

Matiere golds VRAIE et consignee :
  - refs_biblio_scan : la citation PLOS ONE REELLE recopiee LITTERALE
    du bloc « Citation: » du PDF publie (journals.plos.org,
    ?type=printable&id=10.1371/journal.pone.0100586, consulte 27-11) —
    e100586, doi:10.1371/journal.pone.0100586 ; la PAIRE ISSN du
    registre L68 : 1932-6203 = ISSN reel de PLOS ONE (ISSN Portal
    record 1932-6203, consulte 27-11) rendu VALIDE, et 1932-6204, sa
    variante, refusee avec le chiffre attendu NOMME (3) ; les exemples
    ISBN publies ISO 2108 (978-0-306-40615-7 = 0-306-40615-2, deux
    formes du MEME livre ; 0-8044-2957-X, X de controle) — traces de
    REGLE, marques comme tels ; arXiv 2611.05806 (cite dans la page
    MARKET du site) et hep-th/9901001 (forme heritee publiee).
  - foia_sheet_audit : feuille V1 consignee (Part 01 du Vault, rendu
    Abbyy archive.org jeffrey-epstein-part-22-of-22) : « Total Deleted
    Page(s) = 258 » vs 258 marqueurs, min 3 / max 317, 63 numeros
    absents, doublons de lecture Page 8 ×2 et Page 133 ×2, 67 lignes
    « Page N ~ OTHER - Court Sealing Order » (n° 250→317), b7E ×5
    (pages 13, 15, 73, 100 + 1 ligne mutilee), « b6 - 1, -2, -3, -4,
    -5 » (lignes 13-15). Le bloc OCR complet des 258 lignes N'EST PAS
    dans la matiere consignee — F15 joue les AGREGATS CONSIGNES comme
    CLAIMS d'arithmetique sur une feuille-equivalent construite dans
    le test a partir de ces seuls faits (construit = claim, dit tel
    quel, precedent b146 GB/370407) ; la ligne Page 3 est verbatim du
    rendu #1. Feuille V2 consigne : le gold elections 5 lignes
    verbatim (VAULT_V2_GOLDS.json, auto-test 5/5 du parseur consigne
    v2_parse_foia_log.py sur le texte NATIF du FOIA Log 2020, sha256
    ee60d3f8…979aea) passe ICI PAR LA PORTE, champ a champ ; les
    totaux du log natif (16 485 / 2 278 / 14 207) vivent hors depot et
    sont rejoues en CLAIM d'arithmetique, pas comme chiffres de l'appel.

Loi maison 27-11 (registre L69) : l'ensemble ferme des codes vient du
STATUTE 5 U.S.C. § 552(b) — jamais du sheet ; b7E EST DEDANS (l'erreur
initiale de la salle est consignee, pas reproduite) ; codes hors
statute NOMMES un par un, jamais fondus ; verdicts MATCH/MISMATCH/GAP
seulement — la porte ne juge pas l'honnetete, elle rend l'ecart.

Limite dite a l'admission (registre L68) : PAS de resolution reseau —
Crossref appartient a doi_name_equivalence... non : doi_name_equivalence
(SHIPPED b146) est l'etape SUIVANTE, mariee ici via le record
doikit.parse_doi, jamais dupliquee.
"""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

URL_REFS = "/api/v1/refs/biblio-scan"
URL_FOIA = "/api/v1/foia/sheet-audit"

# verbatim, bloc « Citation: » du PDF PLOS ONE publie (consulte 27-11)
PLOS_REF = ("Catenacci DVT, Liao W-L, Thyparambil S, Henderson L, "
            "Xu P, et al. (2014) Absolute Quantitation of Met Using "
            "Mass Spectrometry for Clinical Application: Assay "
            "Precision, Stability, and Correlation with MET Gene "
            "Amplification in FFPE Tumor Tissue. PLoS ONE 9(7): "
            "e100586. doi:10.1371/journal.pone.0100586")

# les 5 golds verbatim VAULT_V2_GOLDS.json (auto-test 5/5 consigne)
ELECTION_GOLDS = [
    ("000 All Documents, Reports, and Findings Provided by \nCrowdStrike "
     "in Relation to the DNC Hack\n13-Oct-20201478175",
     {"case_rev": "000",
      "subject": ("All Documents, Reports, and Findings Provided by "
                  "CrowdStrike in Relation to the DNC Hack"),
      "date_opened": "13-Oct-2020", "foia_number": "1478175"}),
    ("000 Kraken10-Dec-20191453952",
     {"case_rev": "000", "subject": "Kraken",
      "date_opened": "10-Dec-2019", "foia_number": "1453952"}),
    ("000 Braden, Anne03-Feb-20151321099",
     {"case_rev": "000", "subject": "Braden, Anne",
      "date_opened": "03-Feb-2015", "foia_number": "1321099"}),
    ("001 All Files Released to Gerald Posner Regarding the \nSackler "
     "Family\n03-Jan-20201453204",
     {"case_rev": "001",
      "subject": ("All Files Released to Gerald Posner Regarding the "
                  "Sackler Family"),
      "date_opened": "03-Jan-2020", "foia_number": "1453204"}),
    ("000 All Contracts and MOU Between the FBI and \nCrowdStrike, "
     "Inc.\n26-Jan-20171365700",
     {"case_rev": "000",
      "subject": "All Contracts and MOU Between the FBI and "
                 "CrowdStrike, Inc.",
      "date_opened": "26-Jan-2017", "foia_number": "1365700"}),
]

W2020 = {"from": "2020-01-01", "to": "2020-12-31"}


def refs(*lines):
    return client.post(URL_REFS, json={"refs": list(lines)})


def sheet(declared, lines):
    return client.post(URL_FOIA, json={"kind": "deleted_page_sheet",
                                       "declared_total": declared,
                                       "lines": lines})


def log(lines, window=W2020):
    body = {"kind": "foia_log", "lines": lines}
    if window is not None:
        body["window"] = window
    return client.post(URL_FOIA, json=body)


# ===== refs_biblio_scan — la citation reelle et les ids a controle ====

def test_r1_plos_one_verbatim_fields():
    # La ref PLOS ONE LITTERALE du registre L68 : les champs rendus
    # champ par champ, sans qu'aucun ne soit devine.
    r = refs(PLOS_REF)
    assert r.status_code == 200, r.text
    d = r.json()
    one = d["results"][0]
    assert one["parse"]["status"] == "FIELD_GRAMMAR_MATCH"
    f = one["fields"]
    assert f["authors"] == ("Catenacci DVT, Liao W-L, Thyparambil S, "
                            "Henderson L, Xu P, et al.")
    assert f["year"] == "2014"
    assert f["title"].endswith("in FFPE Tumor Tissue")
    assert f["venue"] == "PLoS ONE"
    assert f["volume"] == "9" and f["issue"] == "7"
    assert f["locator"] == "e100586"
    assert one["missing_fields"] == []
    assert len(d["sha256"]) == 64


def test_r2_plos_doi_no_check_digit_invented():
    # Le doi:10.1371/journal.pone.0100586 de la meme ref : grammaire
    # §4.3 jouee par le RECORD doikit (mariee a doi_name_equivalence,
    # pas dupliquee), et §4.3.5 : AUCUN check digit DOI n'existe —
    # la porte ne le dit pas en prose, elle le REND (has_check_digit
    # false) et nomme la next door.
    d = refs(PLOS_REF).json()
    doi = d["results"][0]["ids"][0]
    assert doi["kind"] == "doi" and doi["valid"]
    assert doi["prefix"] == "10.1371"
    assert doi["registrant_code"] == "1371"
    assert doi["suffix"] == "journal.pone.0100586"
    assert doi["doi_form"] == "label"
    assert doi["has_check_digit"] is False
    assert "4.3.5" in doi["check_digit_rule"]
    assert "doi-equivalence" in doi["next_door"]
    # l'observation inter-champs, nommee sans corriger : e100586 vit
    # dans le suffixe DOI.
    assert "elocator_appears_in_doi_suffix:e100586" in \
        d["results"][0]["observations"]


def test_r3_issn_pair_gold_named():
    # La paire du registre L68 : 1932-6203 (ISSN Portal, reel) passe ;
    # 1932-6204 est refusee avec le chiffre ATTENDU nomme — contrat de
    # reparation, jamais une reparation silencieuse.
    d = refs("PLOS ONE — ISSN 1932-6203 (ISSN Portal record 1932-6203, "
             "consulte 27-11) ; variante 1932-6204 citee.").json()
    ids = d["results"][0]["ids"]
    assert [i["normalized"] for i in ids] == ["1932-6203", "1932-6204"]
    a, b = ids
    assert a["valid"] and a["errors"] == []
    assert a["expected_check"] == "3" and a["observed_check"] == "3"
    assert not b["valid"]
    assert b["expected_check"] == "3" and b["observed_check"] == "4"
    assert b["errors"] == ["issn_check_digit_mismatch"]
    assert "8..2" in a["check_algorithm"]


def test_r4_isbn_mod10_and_mod11_same_book():
    # ISO 2108 : les deux formes publiees du MEME livre (l'exemple
    # canonique) — ISBN-13 mod-10 poids 1,3 ; ISBN-10 mod-11 poids
    # 10..1 avec X final. La mutation 978-0-306-40615-0 est refusee
    # avec le 7 attendu NOMME.
    d = refs("ISBN 978-0-306-40615-7 ; ISBN 0-306-40615-2 ; "
             "ISBN 0-8044-2957-X ; ISBN 978-0-306-40615-0").json()
    by = {i["raw"]: i for i in d["results"][0]["ids"]}
    a = by["ISBN 978-0-306-40615-7"]
    assert a["variant"] == "isbn13" and a["valid"]
    assert "mod-10" in a["check_algorithm"]
    b = by["ISBN 0-306-40615-2"]
    assert b["variant"] == "isbn10" and b["valid"]
    assert "mod-11" in b["check_algorithm"]
    x = by["ISBN 0-8044-2957-X"]
    assert x["valid"] and x["expected_check"] == "X"
    bad = by["ISBN 978-0-306-40615-0"]
    assert not bad["valid"] and bad["expected_check"] == "7"
    assert bad["errors"] == ["isbn13_check_digit_mismatch"]


def test_r5_arxiv_both_grammars_closed():
    # arXiv : nouveau YYMM.NNNNN (2611.05806 — le chiffre deja cite
    # sur la page MARKET du site ; 2103.00001v2 — version gardee et
    # NOMMEE) et herite arch-ive/YYMMNNN (hep-th/9901001). Le mois
    # hors gamme et l'archive HORS LISTE FERMEE sont refuses PAR NOM ;
    # arXiv n'a pas de check digit — rendu comme tel, pas invente.
    d = refs("arXiv:2103.00001v2 ; 2611.05806 ; hep-th/9901001 ; "
             "2113.00001 ; bogus-arch/9901001").json()
    ids = {i["raw"]: i for i in d["results"][0]["ids"]}
    a = ids["2103.00001"]
    assert a["valid"] and a["form"] == "new" and a["year"] == 2021
    assert a["month"] == 3 and a["version"] == "v2"
    assert a["has_check_digit"] is False
    assert ids["2611.05806"]["valid"]
    b = ids["hep-th/9901001"]
    assert b["valid"] and b["form"] == "legacy" and b["archive"] == "hep-th"
    m = ids["2113.00001"]
    assert not m["valid"] and m["errors"] == ["arxiv_month_out_of_range"]
    g = ids["bogus-arch/9901001"]
    assert not g["valid"]
    assert "arxiv_archive_not_in_published_list" in g["errors"]


def test_r6_proxy_forms_and_doi_in_url():
    # Le scan vit dans le texte brut : la forme proxy doi.org apparait
    # telle quelle dans une ref, le record sort en NOM nu — et la
    # ponctuation de fin de phrase est retiree DITE, jamais avalee.
    d = refs("See https://doi.org/10.1371/journal.pone.0100586.",
             "doi:10.1000/1.").json()
    i1 = d["results"][0]["ids"][0]
    assert i1["doi_form"] == "proxy" and i1["valid"]
    assert i1["normalized"] == "10.1371/journal.pone.0100586"
    i2 = d["results"][1]["ids"][0]
    assert i2["normalized"] == "10.1000/1"
    assert i2["trailing_punct_trimmed"] == "."


def test_r7_bare_soup_never_claimed():
    # Regle de capture DITE : un bloc de 10 chiffres nu n'est JAMAIS
    # claiming comme ISBN sans label ni forme 978/979 — l'outil ne
    # devore pas les numeros de telephone et de compte.
    d = refs("compte 0306406152 regle le 210310 à 10h").json()
    kinds = [i["kind"] for i in d["results"][0]["ids"]]
    assert "isbn" not in kinds
    # 210310 n'est PAS un arXiv (pas de point) ; rien n'est invente.
    assert kinds == []


def test_r8_no_match_status_ids_survive():
    # Sans grammaire de champs, parse rend NO_MATCH NOMME et les ids
    # passent quand meme — la porte ne devore pas ce qu'elle ne sait
    # pas citer.
    d = refs("random prose doi:10.1000/abc no grammar here").json()
    one = d["results"][0]
    assert one["parse"]["status"] == "NO_MATCH"
    assert one["fields"] is None
    assert [i["kind"] for i in one["ids"]] == ["doi"]
    assert one["missing_fields"] == ["authors", "year", "title", "venue",
                                     "volume", "issue", "locator"]


def test_r9_refusals_named_as_repair_contracts():
    r = client.post(URL_REFS, json={})
    assert r.status_code == 400 and "refs" in str(r.json())
    assert client.post(URL_REFS, json={"refs": "one string"}). \
        status_code == 400
    r = client.post(URL_REFS, json={"refs": ["ok", 5]})
    assert r.status_code == 400 and "refs[1]" in str(r.json())
    assert client.post(URL_REFS, json={"refs": []}).status_code == 400
    assert client.post(URL_REFS, json={"refs": ["x"] * 101}). \
        status_code == 400
    r = client.post(URL_REFS, json={"refs": ["x"], "mode": "fuzzy"})
    assert r.status_code == 400 and "mode" in str(r.json())


def test_r10_rules_cite_primaries():
    # Chaque regle est CITEE dans la reponse (Handbook 2025 + sha,
    # ISO 2108/3297, arXiv help) — pas de prose maison sans nom.
    d = refs(PLOS_REF).json()
    rules = d["rules"]
    assert "September 2025" in rules["doi"]
    assert "1f6c73c1" in rules["doi"]
    assert "ISO 3297" in rules["issn"] and "ISO 2108" in rules["isbn"]
    assert "arxiv" in rules["arxiv"].lower()
    assert "no network" in d["boundary"].lower()


# ================= foia_sheet_audit — le gold elections 5/5 ==========

def test_f1_elections_golds_verbatim_5_sur_5():
    # VAULT_V2_GOLDS.json, materialise TEL QUEL : chaque champ rendu
    # champ par champ sur les lignes SOUDEES du texte natif (le log
    # n'a pas de separateurs — la grammaire consolmee du parseur
    # consigne v2_parse_foia_log.py rejouee par la porte).
    d = log([g for g, _ in ELECTION_GOLDS]).json()
    assert d["window_verdict"] == "MISMATCH"
    recs = d["records"]
    assert len(recs) == 5
    ok = 0
    for rec, (_line, exp) in zip(recs, ELECTION_GOLDS):
        f = rec["fields"]
        ok += all(f[k] == exp[k] for k in exp)
        assert rec["parse"] == "OK" and rec["errors"] == []
    assert ok == 5
    # la subject multi-lignes est jointe, blancs replies en UN espace :
    assert " \n" not in recs[0]["fields"]["subject"]
    assert "  " not in recs[0]["fields"]["subject"]


def test_f2_window_counts_pilot_dnc():
    # Le pilote CrowdStrike 1478175 (13-Oct-2020) est DANS la fenetre
    # 01/01/2020-12/31/2020 imprimee ; sur les 5 lignes, 2 dedans,
    # 3 dehors — arithmetique rendue, definitions dites a cote.
    d = log([g for g, _ in ELECTION_GOLDS]).json()
    c = d["counts"]
    assert c["in_window"] == 2 and c["out_of_window"] == 3
    assert c["out_by_year"] == {"2019": 1, "2017": 1, "2015": 1}
    assert d["arithmetic"] == "in_window + out_of_window + date_errors " \
        "+ anomalies = 2 + 3 + 0 + 0 = 5 (lines_enumerees)"
    pilot = [r for r in d["records"]
             if r["fields"]["foia_number"] == "1478175"][0]
    assert pilot["in_window"] is True
    assert "DATE OPENED only" in d["definitions"]["date_column"]
    assert d["statute"]["citation"] == "5 U.S.C. § 552(b)"


def test_f3_v2_full_log_arithmetic_claim():
    # Le log natif complet (16 485 lignes) vit HORS DEPOT — ses
    # totaux consigns (feuille V2 §4) sont rejoues comme CLAIM
    # d'arithmetique, la porte ne voit que les lignes passees.
    # precedent b146 GB 370407 : le claim est joue, pas la source.
    total, kept, outside = 16485, 14207, 2278
    assert kept + outside == total
    assert 1310 + 968 + 0 == outside   # 2019 + <=2018 + >=2021 (V2)
    assert outside == 2278


def test_f4_sheet_page3_verbatim_doj_subcodes():
    # Ligne verbatim du rendu #1 (snippet index sur le primaire) :
    # « Page 3 ~ b3 - 1; b6 - 1, -2, -3, -4; b7C - 1, -2, -3, -4 ».
    # Les sous-codes DOJ b6-1..4 tombent DANS l'ensemble publie ; la
    # liste tiree de b3 et b7C est HORS statute, NOMMEE (l'ensemble
    # vient du statute, jamais du sheet — loi maison 27-11).
    d = sheet(1, ["Page 3 ~ b3 - 1; b6 - 1, -2, -3, -4; "
                  "b7C - 1, -2, -3, -4;"]).json()
    assert d["total_verdict"] == "MATCH" and d["delta_total"] == 0
    assert d["numbering"]["verdicts"] == {"duplicates": "MATCH",
                                          "gaps": "MATCH"}
    c = d["codes"]
    assert c["in_statute"] == {"b3": 1, "b6": 1, "b7C": 1}
    assert c["in_doj_subcodes"] == {"b6-1": 1, "b6-2": 1, "b6-3": 1,
                                    "b6-4": 1}
    assert sorted(c["hors_statute"]) == ["b3-1", "b7C-1", "b7C-2",
                                         "b7C-3", "b7C-4"]
    assert c["verdict"] == "MISMATCH"


def test_f5_statute_named_b7e_inside():
    # LOI MAISON : la reference statute est NOMMEE dans la reponse ;
    # b7E est DANS le statute — l'erreur initiale de la salle (b7E
    # place hors de l'ensemble observe) est consignee et ICI JOUEE
    # CONTRE : une feuille 100 % b7E rend codes MATCH.
    d = sheet(1, ["Page 13 ~ b7E - 1;"]).json()
    st = d["statute"]
    assert st["citation"] == "5 U.S.C. § 552(b)"
    assert st["statute_codes"] == ["b1", "b2", "b3", "b4", "b5", "b6",
                                   "b7A", "b7B", "b7C", "b7D", "b7E",
                                   "b8", "b9"]
    assert st["doj_published_subcodes"] == ["b6-1", "b6-2", "b6-3",
                                            "b6-4"]
    assert "b7E" in st["statute_codes"]
    assert "NOT reproduced" in st["b7e_note"]
    assert d["codes"]["in_statute"] == {"b7E": 1}
    assert d["codes"]["hors_statute"] == {"b7E-1": 1}  # sous-code
    # non publie — nomme, la base statute reste pleine


def test_f6_bare_b7_not_folded():
    # b7 nu N'EST PAS dans l'ensemble (le statute subdivise (b)(7) en
    # (A)-(E)) : rendu sous-specifie NOMME, jamais replie en b7A..E.
    d = sheet(1, ["Page 9 ~ b7 - 1;"]).json()
    assert d["codes"]["hors_statute"].get("b7") == 1
    assert "b7" not in d["codes"]["in_statute"]
    assert d["codes"]["in_statute"] == {}


def test_f7_other_token_verbatim_never_merged():
    # « OTHER - Court Sealing Order » : le mot du sheet, PAS un code
    # du statute — token et label rendus SEPARES, jamais fondus dans
    # hors_statute des b-code.
    d = sheet(1, ["Page 250 ~ OTHER - Court Sealing Order"]).json()
    c = d["codes"]
    assert c["sheet_tokens_non_statute"] == {"OTHER": 1}
    assert c["sheet_token_labels"] == {"OTHER": ["Court Sealing Order"]}
    assert "OTHER" not in c["hors_statute"]


def test_f8_verdicts_closed_and_no_honesty_words():
    # Le vocabulaire est FERME : MATCH/MISMATCH/GAP, pas un mot de
    # plus — et la reponse ne JUGE PAS l'honnetete (mots verite/
    # fraude/mensonge absents de la reponse serialisee).
    d = sheet(4, ["Page 1 ~ b6 - 1;", "Page 2 ~ b6 - 1;",
                  "Page 4 ~ b6 - 1;", "Page 8 ~ b6 - 1;"]).json()
    blob = d
    vals = [blob["total_verdict"], blob["codes"]["verdict"]] + \
        list(blob["numbering"]["verdicts"].values())
    assert set(vals) <= {"MATCH", "MISMATCH", "GAP"}, vals
    import re as _re
    s = str(d).lower()
    for w in ("verite", "fraude", "mensonge", "truth", "fraud"):
        assert w not in s, w
    assert not _re.search(r"\blie[sd]?\b", s)


def test_f9_numbers_dups_gaps_sample_said():
    # numeros : les doublons NOMMES avec leur nombre, le trou rendu
    # en liste d'echantillon CAPPEE ET DITE (le compte total reste
    # exact — la borne de l'echantillon est un contrat, pas un cache).
    d = sheet(6, ["Page 5 ~ b6 - 1;", "Page 5 ~ b6 - 1;",
                  "Page 7 ~ b6 - 1;", "Page 3 ~ b6 - 1;",
                  "Page 12 ~ b6 - 1;", "Page 3 ~ b6 - 1;"]).json()
    n = d["numbering"]
    assert n["verdicts"] == {"duplicates": "MISMATCH", "gaps": "GAP"}
    assert n["duplicates"] == [{"page": 3, "count": 2},
                               {"page": 5, "count": 2}]
    # 3,5,7,12 distinct -> absents 4,6,8,9,10,11 = 6
    assert n["gaps_count"] == 6
    assert n["gaps_sample"] == [4, 6, 8, 9, 10, 11]
    assert "capped" in n["gaps_sample_rule"]
    assert n["min"] == 3 and n["max"] == 12
    assert n["max_gt_declared"] is True


def test_f10_mutilated_markers_listed_not_reconstituted():
    # V1 consigne les lignes dont l'OCR a mange le numero (« Page
    # C/ /V », « Page l; », « Page - i • 219 ») : comptees apart,
    # listees, JAMAIS reconstituees — mais leur CODE survit (le scan
    # cherche le token statute dans le bruit).
    d = sheet(3, ["Page C/ /V ~ b6 - 1;", "Page l; ~ b7D - 1;",
                  "Page - i • 219 ~ b7E - 1;"]).json()
    n = d["numbering"]
    assert n["unnumbered_count"] == 3 and n["numbers_distinct"] == 0
    assert n["min"] is None
    assert "Page - i • 219 ~ b7E - 1;" in n["unnumbered_lines"]
    assert d["codes"]["in_statute"] == {"b6": 1, "b7D": 1, "b7E": 1}
    assert d["total_verdict"] == "MATCH"  # 3 marqueurs = declares 3


def test_f11_total_verdict_mismatch_delta():
    # Part 04 du rendu #2 (consigne) : declares 200 vs lignes 146 —
    # l'ecart est LIVRE TEL QUEL en delta nomme, jamais ramene.
    d = log([l for l, _ in ELECTION_GOLDS], window=W2020).json()
    assert "declared_total" not in d   # total non requis pour le log
    r = sheet(200, ["Page %d ~ b6 - 1;" % i for i in range(1, 147)])
    d2 = r.json()
    assert d2["total_verdict"] == "MISMATCH"
    assert d2["delta_total"] == -54
    assert d2["numbering"]["verdicts"]["gaps"] == "MATCH"  # 1..146 plein


def test_f12_log_anomalies_visible():
    # L'anomalie consignee (ligne sans CASE REV, « Bartik, Jeffrey »)
    # est MONTEE COMME DITE, non reconstituee ; une ligne sans tampon
    # date+7 chiffres est refusee PAR LE NOM du motif absent.
    d = log(["Bartik, Jeffrey07-Dec-20201482833",
             "page footer 7/28/2023Page 250 of 467",
             "000 Kraken10-Dec-20191453952"]).json()
    recs = d["records"]
    assert len(recs) == 2
    assert recs[0]["fields"]["case_rev"] is None
    assert "case_rev_absent_in_text" in recs[0]["observations"]
    assert recs[0]["in_window"] is True
    anom = d["anomalies"]
    assert len(anom) == 1 and anom[0]["parse"] == "NO_RECORD_TAIL"
    assert "no dd-Mmm-yyyy + 7-digit tail" in anom[0]["errors"][0]


def test_f13_log_date_validity_named():
    # 31-Fevrier n'existe pas : refuse PAR NOM avec la loi du mois,
    # le mois inexistant aussi — la porte ne clamp jamais une date.
    d = log(["000 X31-Feb-20201478175", "000 Y29-Feb-20191478176",
             "000 Z13-Fob-20201478177",
             "000 Kraken10-Dec-20191453952"]).json()
    recs = d["records"]
    assert len(recs) == 4
    errs = [r["errors"] for r in recs]
    assert errs[0] == ["day_invalid_for_month"]
    assert errs[1] == ["day_invalid_for_month"]   # 2019 non bissextile
    assert errs[2] == ["month_name_unknown"]
    assert errs[3] == []
    assert d["anomalies"] == []  # le tampon existe, le champ est dit
    assert d["counts"]["date_errors"] == 3
    assert d["counts"]["out_of_window"] == 1
    assert "3" in d["arithmetic"]


def test_f14_refusals_named_sheet_and_log():
    assert client.post(URL_FOIA, json={"lines": ["x"]}). \
        status_code == 400
    r = client.post(URL_FOIA, json={"kind": "bazar", "lines": ["x"],
                                    "declared_total": 1})
    assert r.status_code == 400 and "kind" in str(r.json())
    assert client.post(URL_FOIA, json={"kind": "deleted_page_sheet",
                                       "lines": ["Page 1 ~ b1;"]}
                       ).status_code == 400          # declared_total
    assert client.post(URL_FOIA, json={"kind": "deleted_page_sheet",
                                       "declared_total": "258",
                                       "lines": ["Page 1 ~ b1;"]}
                       ).status_code == 400          # int attendu
    assert client.post(URL_FOIA, json={"kind": "foia_log",
                                       "lines": ["x"]}).status_code == 400
    assert client.post(URL_FOIA, json={"kind": "foia_log", "lines": [],
                                       "window": W2020}).status_code == 400
    assert client.post(URL_FOIA, json={"kind": "foia_log", "lines": ["x"],
                                       "window": {"from": "2020-12-31",
                                                  "to": "2020-01-01"}
                                       }).status_code == 400
    assert client.post(URL_FOIA, json={"kind": "foia_log", "lines": ["x"],
                                       "window": {"from": "31/12/2020",
                                                  "to": "x"}
                                       }).status_code == 400
    r = client.post(URL_FOIA, json={"kind": "deleted_page_sheet",
                                    "declared_total": 1,
                                    "lines": ["x"], "window": W2020})
    assert r.status_code == 400 and "window" in str(r.json())
    r = client.post(URL_FOIA, json={"kind": "deleted_page_sheet",
                                    "declared_total": 1,
                                    "lines": [{"page": 3}], "mode": "x"})
    assert r.status_code == 400 and "mode" in str(r.json())


def test_f15_part01_aggregates_replayed_as_claim():
    # FEUILLE V1, Part 01 — les AGREGATS CONSIGNES : 258 declares =
    # 258 marqueurs, min 3, max 317 (317 > 258 dit), 63 numeros
    # absents, doublons de lecture 8 et 133, 4 lignes mutilees dont
    # une porte encore son b7E (b7E x5), 67 lignes OTHER 250→317,
    # « b6 - 1, -2, -3, -4, -5 » (lignes 13-15). Le bloc OCR complet
    # n'est pas dans la matiere : la feuille-equivalent est CONSTRUITE
    # dans ce test a partir de ces seuls faits — claim rejoue, source
    # hors depot dite, jamais un chiffre invente rendu par l'app.
    lines = ["Page 3 ~ b3 - 1; b6 - 1, -2, -3, -4; b7C - 1, -2, -3, -4;"]
    for n in [x for x in range(4, 250) if x not in range(140, 202)]:
        if n == 13:
            lines.append("Page 13 ~ b6 - 1, -2, -3, -4, -5; b7E - 1;")
        elif n == 15:
            lines.append("Page 15 ~ b7E - 1; b7C - 1, -2, -3, -4, -5;")
        elif n == 73:
            lines.append("Page 73 ~ b7E - 1; b6 - 1, -2;")
        elif n == 100:
            lines.append("Page 100 ~ b7E - 1;")
        else:
            lines.append("Page %d ~ b6 - 1, -2;" % n)
    for n in range(250, 318):
        if n == 271:      # le 63e absent
            continue
        lines.append("Page %d ~ OTHER - Court Sealing Order" % n)
    lines += ["Page 8 ~ b7C - 1;", "Page 133 ~ b3 - 1;",
              "Page C/ /V ~ b6 - 1;", "Page l; ~ b7D - 1;",
              "Page - i • 219 ~ b7E - 1;", "Page x; ~ b6 - 1;"]
    assert len(lines) == 258
    d = sheet(258, lines).json()
    assert d["total_verdict"] == "MATCH" and d["delta_total"] == 0
    n = d["numbering"]
    assert n["verdicts"] == {"duplicates": "MISMATCH", "gaps": "GAP"}
    assert n["min"] == 3 and n["max"] == 317 and n["max_gt_declared"]
    assert n["numbers_distinct"] == 252
    assert n["gaps_count"] == 63
    assert n["duplicates"] == [{"page": 8, "count": 2},
                               {"page": 133, "count": 2}]
    assert n["unnumbered_count"] == 4
    c = d["codes"]
    assert c["in_statute"]["b7E"] == 5        # salle : hors — NOLLE
    assert "b7E" in d["statute"]["statute_codes"]  # NOMMee, top-level
    assert c["hors_statute"]["b6-5"] == 1     # sous-code non publie
    assert c["hors_statute"]["b7C-5"] == 1
    assert c["sheet_tokens_non_statute"]["OTHER"] == 67
    assert c["sheet_token_labels"]["OTHER"] == ["Court Sealing Order"]
    assert c["verdict"] == "MISMATCH"
    assert d["non_page_lines"]["count"] == 0


# ==================== determinisme, batch, routing ===================

def test_z1_same_request_same_bytes_each_sha():
    body_r = {"refs": [PLOS_REF]}
    body_f = {"kind": "deleted_page_sheet", "declared_total": 1,
              "lines": ["Page 3 ~ b3 - 1; b6 - 1, -2, -3, -4; "
                        "b7C - 1, -2, -3, -4;"]}
    for url, body in ((URL_REFS, body_r), (URL_FOIA, body_f)):
        a = client.post(url, json=body)
        b = client.post(url, json=body)
        assert a.status_code == 200 and a.content == b.content
        assert len(a.json()["sha256"]) == 64


def test_z2_batch_dispatches_by_name():
    r = client.post("/api/v1/batch", json={
        "tool": "refs_biblio_scan",
        "payloads": [{"refs": [PLOS_REF]}, {"refs": []}]})
    assert r.status_code == 200, r.text
    got = r.json()
    assert got["failed"] == 1
    assert got["results"][0]["result"]["counts"]["ids_valid"] == 1
    assert "invalid_input" in str(got["results"][1]["error"])
    r = client.post("/api/v1/batch", json={
        "tool": "foia_sheet_audit",
        "payloads": [{"kind": "foia_log", "window": W2020,
                     "lines": [ELECTION_GOLDS[0][0]]}]})
    assert r.json()["results"][0]["result"]["counts"]["in_window"] == 1


def test_z3_pain_routes_now_answer():
    for q, want in (
            ("isbn check", "refs_biblio_scan"),
            ("issn validate", "refs_biblio_scan"),
            ("bibliography citation parse", "refs_biblio_scan"),
            ("arxiv id parse", "refs_biblio_scan"),
            ("doi extract from citation", "refs_biblio_scan"),
            ("foia exemption codes", "foia_sheet_audit"),
            ("deleted page sheet", "foia_sheet_audit"),
            ("552b withheld codes", "foia_sheet_audit"),
            ("foia log window entries", "foia_sheet_audit")):
        r = client.get("/route", params={"q": q})
        assert r.status_code == 200
        names = [e["tool"] for e in r.json()["tools"]]
        assert want in names, (q, names)


def test_z4_tools_json_surface():
    for name in ("refs_biblio_scan", "foia_sheet_audit"):
        r = client.get("/tools/%s.json" % name)
        assert r.status_code == 200, name
        spec = r.json()
        assert spec["tier"] == "free"
        assert "Free." in spec["schema"]["description"]
