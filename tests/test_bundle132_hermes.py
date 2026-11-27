# Bundle 132_hermes — AMAS DATES 1/2 : les parseurs (v1.53.0).
# Admissions d'arbitrage Vince 27-11 (« ouvres les amas un par un, tous ») :
#   date_edtf_interval  (Gate, reçu 848f1a94, RECOMMANDÉE) — 9 golds tracés
#     main par Gate, mois finaux recoupés sur la porte (batch 13).
#   date_interval_within (Gate, reçu a8ce4696, « plus faible » selon Gate
#     lui-même — une part de la douleur était le bug B8 de logic_rules,
#     TIGÉ au bundle 128). ADMISE QUAND MÊME, séparée : sa DISTINCTIN est
#     vraie (date_window ne compare JAMAIS deux intervalles donnés) et le
#     DIFFICILE « on ne reformate jamais » de batch 01/02/06 meurt ici.
#     Écart révisé devant la table : je devais fusionner within dans edtf —
#     le draft de Gate prouve deux contrats, pas un. La table a raison.
#   marc008_date_range  (Lineage, reçu 692467fa, SUSPECT-DUPLICATE rendu
#     au POST) — ADMIS : la correspondance date_window 14 est un score de
#     MOTS, pas de contrat ; l'objet parsé est un champ FIXE positionnel,
#     hors texte libre. Table fermée : LOC MARC21 bd008a (édition 2026-05-27,
#     sha256 b2a162cc5fa4674c532a04bf4d6ccba1084bbabb6d55afff08052241ab67f26d).
#   Les formes catalogue 260$c (c1996., [1987?], [198-], années nues) : PAS
#   d'extension date_parse — l'année nue EST le gold EDTF n°1 (précision
#   réduite). date_parse reste l'instant unique. Tranché ici, consigné.
import base64, json
import urllib.request  # noqa — style maison des bundles voisins

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def edtf(text):
    return client.post("/api/v1/date/edtf-interval", json={"text": text})


def within(outer, inner):
    return client.post("/api/v1/date/interval-within",
                       json={"outer": outer, "inner": inner})


def marc008(field):
    return client.post("/api/v1/date/marc008", json={"field008": field})


# ============ date_edtf_interval — les 9 golds de Gate ============

def test_g1_bare_year_precision_an():
    r = edtf("1985")
    assert r.status_code == 200
    d = r.json()
    assert d["earliest"] == "1985-01-01" and d["latest"] == "1985-12-31"
    assert d["precision"] == "year"


def test_g2_month_not_leap_century():
    # 1900 n'est PAS bissextile (divisible par 100, pas par 400) —
    # le gold de Gate dit 28 jours ; la recopie naïve dirait 29.
    d = edtf("1900-02").json()
    assert d["earliest"] == "1900-02-01" and d["latest"] == "1900-02-28"
    assert d["precision"] == "month"


def test_g2b_month_leap_400():
    d = edtf("2004-02").json()
    assert d["latest"] == "2004-02-29"


def test_g3_closed_interval():
    d = edtf("1757/1861").json()
    assert d["earliest"] == "1757-01-01" and d["latest"] == "1861-12-31"
    assert d["interval"] is True and d["open_end"] is False


def test_g4_open_end_nul_dit():
    # le 21001231 sentinelle de TNA (14 faux CONTRADICTED de Gate) meurt ici :
    # une fin ouverte est latest:null + open_end:true, JAMAIS une borne volée.
    d = edtf("2004/..").json()
    assert d["earliest"] == "2004-01-01" and d["latest"] is None
    assert d["open_end"] is True


def test_g5_approx_qualifie():
    d = edtf("1600~/1972").json()
    assert d["earliest"] == "1600-01-01"
    assert "approximate" in d["qualifiers"]


def test_g6_uncertain():
    d = edtf("1985?").json()
    assert d["earliest"] == "1985-01-01" and "uncertain" in d["qualifiers"]


def test_g7_unspecified_digits():
    d = edtf("198X").json()
    assert d["earliest"] == "1980-01-01" and d["latest"] == "1989-12-31"
    assert "unspecified" in d["qualifiers"]


def test_g8_inverted_refused_by_name():
    r = edtf("1972/1600")
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "text"


def test_g9_not_edtf_refused():
    # can-fail : « 1966 Jan. » EST une date lisible par un humain — la
    # grammaire fermée la refuse NOMMÉE, c'est le contrat, pas un goût.
    r = edtf("1966 Jan.")
    assert r.status_code == 400
    assert "edtf" in json.dumps(r.json()).lower()


def test_g10_day_precision():
    d = edtf("1945-05-08").json()
    assert d["earliest"] == d["latest"] == "1945-05-08"
    assert d["precision"] == "day"


def test_g11_scale_proleptic_said():
    # le pré-1582 est calculé proleptique-Gregorian — échelle DITE,
    # même loi que B16 (bundle 128).
    d = edtf("1500-03-01").json()
    assert d["scale"] == "proleptic-gregorian"


# ============ date_interval_within ============

def test_w_inside_inclusive_start():
    d = within("1992-12-29/1999-12-31", "1992-12-29/1999-06-30").json()
    assert d["verdict"] == "INSIDE"


def test_w_starts_before_gap_2922():
    # miroir exact du chiffre Gate (ADM 273) : 8 ans, deux 29 février.
    d = within("1992-12-29/2000-12-31", "1984-12-29/1990-01-01").json()
    assert d["verdict"] == "STARTS_BEFORE"
    assert d["gap_days"] == 2922


def test_w_ends_after_gap_named():
    d = within("1990-01-01/2000-01-01", "1995-01-01/2016-06-22").json()
    assert d["verdict"] == "ENDS_AFTER"
    assert d["gap_days"] == 6017


def test_w_child_open_end_ends_after_flagged():
    # ACT 4 de Gate : un enfant qui ne finit jamais ne tient pas dans une
    # borne fermée — ENDS_AFTER + l'enfant ouvert NOMMÉ, jamais 9999 volé.
    d = within("1990-01-01/2000-01-01", "1995-01-01/..").json()
    assert d["verdict"] == "ENDS_AFTER" and d["child_open_end"] is True


def test_w_undated_not_judged():
    d = within("1990-01-01/2000-01-01", "uuuu").json()
    assert d["verdict"] == "UNDATED" and d["gap_days"] is None


def test_w_inverted_child_refused():
    r = within("1990-01-01/2000-01-01", "2010-01-01/1990-01-01")
    assert r.status_code == 400


# ============ marc008_date_range — table fermée LOC bd008a ============

def _m(f06, d1, d2):
    # 00-05 = SIX positions (yymmdd) ; 06 + 07-10 + 11-14 = 9 ;
    # 15-39 = vingt-cinq restantes — total 40 exactement.
    return marc008("      %s%s%s" % (f06, d1, d2) + " " * 25)


def test_m_s_single_date_blanks():
    d = _m("s", "1977", "####").json()
    assert d["earliest"] == "1977-01-01" and d["latest"] == "1977-12-31"
    assert d["date_type_meaning"] == "single known/probable date"


def test_m_c_ongoing_9999():
    d = _m("c", "1984", "9999").json()
    assert d["ongoing"] is True and d["latest"] is None
    assert d["earliest"] == "1984-01-01"


def test_m_q_questionable_span():
    # le gold Lineage : 18uu/19uu q → 1800..1999 — « combien de tri
    # sélectif » se mesure ici, en décades, pas en opinion.
    d = _m("q", "18uu", "19uu").json()
    assert d["earliest"] == "1800-01-01" and d["latest"] == "1999-12-31"


def test_m_digit_u_decade():
    d = _m("q", "1963", "1966").json()
    assert d["earliest"] == "1963-01-01" and d["latest"] == "1966-12-31"


def test_m_e_detailed_mmdd():
    d = _m("e", "1983", "0615").json()
    assert d["earliest"] == "1983-06-15" and d["latest"] == "1983-06-15"


def test_m_e_month_only():
    d = _m("e", "1977", "05##").json()
    assert d["earliest"] == "1977-05-01" and d["latest"] == "1977-05-31"


def test_m_e_day_unknown():
    d = _m("e", "1976", "11uu").json()
    assert d["earliest"] == "1976-11-01" and d["latest"] == "1976-11-30"


def test_m_r_reprint_roles():
    # r : date1 = reprint, date2 = ORIGINAL. Le span ne trie pas au hasard :
    # earliest vient de date2, et le RÔLE est nommé.
    d = _m("r", "1983", "1857").json()
    assert d["earliest"] == "1857-01-01" and d["latest"] == "1983-12-31"
    assert d["roles"] == {"date1": "reprint", "date2": "original"}


def test_m_n_unknown():
    d = _m("n", "uuuu", "uuuu").json()
    assert d["earliest"] is None and d["latest"] is None
    assert "dates_unknown" in d["flags"]


def test_m_leading_zero():
    d = _m("s", "0946", "####").json()
    assert d["earliest"] == "0946-01-01" and d["latest"] == "0946-12-31"


def test_m_fill_mix_refused_by_name():
    # « un fill mélangé ne doit JAMAIS se produire » (LOC) — la porte
    # refuse et nomme, elle ne remplit pas les trous.
    r = _m("s", "19|6", "####")
    assert r.status_code == 400
    assert "fill" in json.dumps(r.json()).lower()


def test_m_wrong_length_refused():
    r = marc008("short")
    assert r.status_code == 400


def test_m_unknown_code_refused():
    r = _m("z", "1963", "####")
    assert r.status_code == 400
    assert "z" in json.dumps(r.json())  # le refus nomme le coupable
