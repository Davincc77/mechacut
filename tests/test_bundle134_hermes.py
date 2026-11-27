# Bundle 134_hermes — PAQUET CHI2 + BENFORD (amas P-C, arbitrage Vince 27-11).
# Admissions (registres 9ceddc83 / 265f6322 / e40332bc, contenu conserve
# chez le releveur interne ; blob benford sha256 f68fc7977cd586c429c9f7
# b9d5f96a0706d6933f36e4b9caa981e5612b40246e) :
#   stats_chi2_gof + stats_chi2_critical = UN SEUL OUTIL, DEUX SORTIES
#   NOMMEES (mode gof | critical), un seul contrat d'enregistrement ;
#   benford_digit_test = outil separate, relit la table critique fermee
#   et la NOMME dans la reponse.
# Golds : les 3 golds litteraux du contrat gof (reçu 9ceddc83, releveur
# interne — loteries) et les valeurs critiques tracees main sur le NIST
# (reçu 265f6322, releveur interne — Benford, METHODES). Les 5 golds
# benford tracés main vivent dans
# le GOLDS.md du releveur (stocke:false — jamais dans le depot) : leurs
# valeurs litterales disponibles dans la compilation (les seuils, les
# ratios 3281/855, l'erratum MAD 0.083804) sont rejoues ou consignes
# ici ; rien n'est invente.
import json

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def chi2(body):
    return client.post("/api/v1/stats/chi2", json=body)


def benford(body):
    return client.post("/api/v1/stats/benford", json=body)


# ============ mode gof — les 3 golds litteraux du contrat ============

def test_gof_gold1_even_df2():
    # [10,20,30] -> 10, df 2, p 0.006738 (e^-5) — litteral de campagne.
    r = chi2({"mode": "gof", "counts": [10, 20, 30]})
    assert r.status_code == 200
    d = r.json()
    assert d["chi2"] == "10.000000" and d["df"] == 2
    assert d["p_upper_tail"] == "0.006738"
    assert d["p_form"] == "p = e^(-x/2)"
    assert d["applied_defaults"] == ["expected=uniform n/k"]


def test_gof_gold2_even_df4():
    # [14,6,10,10,10] -> 3.2, df 4, p 0.524931 (e^-1.6 * 2.6).
    d = chi2({"mode": "gof", "counts": [14, 6, 10, 10, 10]}).json()
    assert d["chi2"] == "3.200000" and d["df"] == 4
    assert d["p_upper_tail"] == "0.524931"
    assert d["p_form"] == "p = e^(-x/2) * (1 + x/2)"


def test_gof_gold3_zero_count():
    # [0,10,20] -> 20, df 2, p 0.000045 (e^-10). Le 0.000045 est la
    # REGLE ferme qui fixe le cent-millieme, pas un rendu hasardeux :
    # e^-10 = 0.0000453999... — la troncature au 6e serait 0.000045
    # aussi, l'arrondi half-up pareil. Le gold est l'attendu.
    d = chi2({"mode": "gof", "counts": [0, 10, 20]}).json()
    assert d["chi2"] == "20.000000" and d["df"] == 2
    assert d["p_upper_tail"] == "0.000045"


def test_gof_expected_absent_said_back():
    # l'absence d'attendu est RENDUE, pas silencieuse. 3 bins -> df 2.
    d = chi2({"mode": "gof", "counts": [1, 1, 1]}).json()
    assert d["applied_defaults"] == ["expected=uniform n/k"]
    assert d["chi2"] == "0.000000" and d["p_upper_tail"] == "1.000000"


def test_gof_explicit_expected_exact():
    d = chi2({"mode": "gof", "counts": [10, 20, 30],
              "expected": ["20", "20", "20"]}).json()
    assert d["chi2"] == "10.000000" and d["p_upper_tail"] == "0.006738"
    assert "applied_defaults" not in d  # rien n'a ete default


def test_gof_df_odd_refused_naming_the_neighbour():
    # 4 bins -> df 3 impair : la forme fermee du contrat couvre les df
    # pairs. Refus PAR LE NOM, le voisin (mode=critical) est designe.
    r = chi2({"mode": "gof", "counts": [1, 2, 3, 4]})
    assert r.status_code == 400
    msg = json.dumps(r.json())
    assert "odd" in msg and "critical" in msg


def test_gof_bin_count_and_negative_and_length():
    assert chi2({"mode": "gof", "counts": [5]}).status_code == 400
    assert chi2({"mode": "gof", "counts": [-1, 2]}).status_code == 400
    r = chi2({"mode": "gof", "counts": [1, 2, 3], "expected": ["2"]})
    assert r.status_code == 400
    assert "expected" in json.dumps(r.json())


def test_gof_mode_cross_fields_refused():
    # un champ de l'autre sortie, sous ce mode, meurt nomme — pas ignore.
    r = chi2({"mode": "gof", "counts": [1, 1, 1, 1, 1], "df": 8})
    assert r.status_code == 400
    assert "mode=gof" in json.dumps(r.json())
    r = chi2({"mode": "critical", "df": 8, "alpha": "0.05",
              "counts": [1, 2]})
    assert r.status_code == 400
    assert "mode=critical" in json.dumps(r.json())


def test_unknown_key_refused_by_name():
    # extra=forbid porte : la cle inconnue est refusee PAR SON NOM.
    r = chi2({"mode": "critical", "df": 8, "alpha": "0.05", "dd": 4})
    assert r.status_code == 400
    assert "dd" in json.dumps(r.json())


def test_missing_mode_or_missing_fields():
    assert chi2({"df": 8, "alpha": "0.05"}).status_code == 400   # no mode
    r = chi2({"mode": "critical", "df": 8})
    assert r.status_code == 400
    assert "alpha" in json.dumps(r.json())


# ============ mode critical — les valeurs tracees main sur NIST ============
# Litteraux de campagne (METHODES : « df8 15.507 (20.090), df9 16.919
# (21.666), df89 112.022 (122.942), df99 123.225 (134.642) », alpha 0.05
# puis 0.01) — recopies LITTERALEMENT, table fermee recoupee au fetch.

CRIT_GOLDS = [
    (8, "0.05", "15.507"), (9, "0.05", "16.919"),
    (89, "0.05", "112.022"), (99, "0.05", "123.225"),
    (8, "0.01", "20.090"), (9, "0.01", "21.666"),
    (89, "0.01", "122.942"), (99, "0.01", "134.642"),
    # ancrages supplementaires de la MEME table (le seuil de 1%, la
    # derniere ligne, la file 0.10) — valeurs au format publie.
    (1, "0.05", "3.841"), (2, "0.05", "5.991"),
    (100, "0.05", "124.342"), (50, "0.001", "86.661"),
]


def test_critical_table_golds():
    for df, alpha, v in CRIT_GOLDS:
        r = chi2({"mode": "critical", "df": df, "alpha": alpha})
        assert r.status_code == 200, (df, alpha)
        d = r.json()
        assert d["chi2_crit"] == v, (df, alpha, d["chi2_crit"], v)
        assert d["tail"] == "upper"


def test_critical_table_declared_versioned_hashed():
    d = chi2({"mode": "critical", "df": 89, "alpha": "0.05"}).json()
    t = d["table"]
    assert t["name"] == "CHI2-CRIT-NISTEH-1.3.6.7.4-v1"
    assert len(t["sha256"]) == 64 and t["rows"] == "df 1..100"
    assert set(t["alphas"]) == {"0.10", "0.05", "0.025", "0.01", "0.001"}
    # la source de campagne (corpus T) est designee par son sha publie
    assert t["source_sha256_published"] == (
        "0272243b765df357a6ea272af1f84e7a0af59a16b5170298c802275106"
        "edd7e1")


def test_critical_off_table_refused_by_name():
    for df in (0, 101, 1000):
        r = chi2({"mode": "critical", "df": df, "alpha": "0.05"})
        assert r.status_code == 400
        assert "df" in json.dumps(r.json())
    for a in ("0.02", "0.5", "1", "0.050"):
        r = chi2({"mode": "critical", "df": 5, "alpha": a})
        assert r.status_code == 400
        assert "alpha" in json.dumps(r.json())


# ============ benford_digit_test — table BENFORD-NIGRINI2012-v1 ============

def test_benford_l1_null_exact():
    # Derive de la table (attendu trace main) : comptes uniformes sur
    # dernier chiffre -> chi2 0.00, MAD 0.0000, < 16.919 -> NOT_REJECTED.
    d = benford({"test": "last_digit", "counts": [100] * 10,
                 "min": 100, "max": 999}).json()
    assert d["n"] == 1000 and d["df"] == 9
    assert d["chi2"] == "0.00"
    assert d["chi2_crit_05"] == "16.919"   # litteral de campagne
    assert d["mad"] == "0.0000" and d["band"] is None
    assert d["verdict"] == "UNIFORM_NOT_REJECTED"


def test_benford_l1_skew_hand_exact():
    # Trace main : O=[900,100x9], N=1800, attendu 180.
    # chi2 = 720^2/180 + 9 * 80^2/180 = 2880 + 320 = 3200 -> REJECTED.
    # MAD = (|0.5-0.1| + 9*|1/18-0.1|)/10 = (0.4 + 9*0.04444444444)/10
    #     = 0.8/10 = 0.08 -> rendu 0.0800.
    d = benford({"test": "last_digit", "counts": [900] + [100] * 9,
                 "min": 100, "max": 999}).json()
    assert d["chi2"] == "3200.00" and d["mad"] == "0.0800"
    assert d["verdict"] == "UNIFORM_REJECTED"
    assert "no Nigrini 2012 band" in d["band_note"]  # info only, dit


def test_benford_span_literals_3281_and_855():
    # Ratios litteraux de la campagne (C1 = 3281, C2 = 855, « below
    # 10^4 »). n >= 1000 pour que R-N1 ne masque pas R-SPAN.
    counts = [301, 176, 125, 97, 79, 67, 58, 51, 46]  # n = 1000
    for hi in (3281, 855):
        d = benford({"test": "first_digit", "counts": counts,
                     "min": 1, "max": hi}).json()
        assert d["verdict"] == "SPAN_TOO_NARROW", hi
    # 10^4 pile passe (max/min >= 10^4 est la regle fermee)
    d = benford({"test": "first_digit", "counts": counts,
                 "min": 1, "max": 10000}).json()
    assert d["verdict"] in ("CONFORMS", "NONCONFORMITY")


def test_benford_rn1_precedence_over_everything():
    # R-N1 est la PREMIERE precedence : n < 1000, meme statistique
    # sous le seuil, meme bande CLOSE -> SAMPLE_TOO_SMALL.
    d = benford({"test": "first_digit", "counts": [300] * 3 + [1] * 6,
                 "min": 1, "max": 1000000}).json()
    assert d["n"] == 906
    assert d["verdict"] == "SAMPLE_TOO_SMALL"
    assert "chi2" in d and "mad" in d  # statistiques quand meme rendues


def test_benford_l2_hand_exact_and_band_absent():
    # Trace main : attendu uniforme 0.01, attendu attendu compte exact.
    # O = [110, 90, 100x98], N = 10000, attendu 100 chaque bin ->
    # chi2 = 10^2/100 + 10^2/100 = 2.00 < 123.225 (litteral campagne)
    # -> UNIFORM_NOT_REJECTED, MAD rendue, bande absente DITE.
    d = benford({"test": "last_two", "counts": [110, 90] + [100] * 98,
                 "min": 1, "max": 9999}).json()
    assert d["n"] == 10000 and d["df"] == 99
    assert d["chi2"] == "2.00" and d["chi2_crit_05"] == "123.225"
    assert d["verdict"] == "UNIFORM_NOT_REJECTED"
    assert d["band"] is None and "no Nigrini 2012 band" in d["band_note"]
    # et le rejet exact : O = [400, 200, 100x98], N = 10400, attendu 104.
    # chi2 = (296^2 + 96^2 + 98*4^2)/104 = 98400/104 = 946.1538.. -> 946.15
    d = benford({"test": "last_two", "counts": [400, 200] + [100] * 98,
                 "min": 1, "max": 9999}).json()
    assert d["chi2"] == "946.15"
    assert d["verdict"] == "UNIFORM_REJECTED"


def test_benford_band_edges_are_the_literals():
    # Les bordures fermees, litterales : 0.006/0.012/0.015 (F1) et
    # 0.0012/0.0018/0.0022 (F2), borne superieure INCLUSIVE (v1 dite).
    import benfordkit
    from decimal import Decimal as D
    edges = benfordkit.MAD_EDGES
    assert [e for _, e in edges["first_digit"]] == ["0.006", "0.012",
                                                    "0.015"]
    assert [e for _, e in edges["first_two"]] == ["0.0012", "0.0018",
                                                  "0.0022"]
    assert benfordkit.band_of("first_digit", D("0.006")) == "CLOSE"
    assert benfordkit.band_of("first_digit", D("0.0061")) == "ACCEPTABLE"
    assert benfordkit.band_of("first_digit", D("0.015")) == "MARGINAL"
    assert benfordkit.band_of("first_digit", D("0.0151")) == \
        "NONCONFORMITY"
    assert benfordkit.band_of("last_digit", D("0.5")) is None


def test_benford_first_two_nine_bins_lengths():
    # length refusals name the closed bin counts.
    for test, good in (("first_digit", 9), ("first_two", 90),
                       ("last_digit", 10), ("last_two", 100)):
        bad = good + 1
        r = benford({"test": test, "counts": [101] + [1] * (bad - 1),
                     "min": 1, "max": 99999})
        assert r.status_code == 400, test
        assert str(good) in json.dumps(r.json())


def test_benford_table_declared_and_crit_named():
    d = benford({"test": "first_digit",
                 "counts": [301, 176, 125, 97, 79, 67, 58, 51, 46],
                 "min": 1, "max": 10000}).json()
    assert d["chi2_crit_05"] == "15.507"  # litteral campagne, df 8
    assert "CHI2-CRIT-NISTEH-1.3.6.7.4-v1" in d["chi2_crit_05_source"]
    assert d["table"]["name"] == "BENFORD-NIGRINI2012-v1"
    assert len(d["table"]["sha256"]) == 64
    assert d["df"] == 8  # df fixes litteraux 8/89/9/99
    assert d["chi2_crit_05_source"]


def test_benford_verdict_closed_six():
    # L'ensemble est ferme a six noms — chaque reponse 200 y vit.
    import benfordkit
    seen = set()
    for body in ({"test": "last_digit", "counts": [100] * 10,
                  "min": 100, "max": 999},
                 {"test": "last_digit", "counts": [900] + [100] * 9,
                  "min": 100, "max": 999},
                 {"test": "first_digit", "counts": [100] * 9,
                  "min": 5, "max": 100},
                 {"test": "first_digit",
                  "counts": [301, 176, 125, 97, 79, 67, 58, 51, 46],
                  "min": 1, "max": 855}):
        d = benford(body).json()
        assert d["verdict"] in benfordkit.VERDICTS
        seen.add(d["verdict"])
    assert seen == {"UNIFORM_NOT_REJECTED", "UNIFORM_REJECTED",
                    "SAMPLE_TOO_SMALL", "SPAN_TOO_NARROW"}


def test_benford_grammar_refusals():
    # test hors table refuse par le nom ; min <= 0 refuse (R-POS dit) ;
    # max < min refuse ; cle inconnue refusee par son nom.
    assert benford({"test": "middle_digit", "counts": [1] * 9,
                    "min": 1, "max": 9}).status_code == 400
    r = benford({"test": "first_digit", "counts": [1] * 9,
                 "min": 0, "max": 9})
    assert r.status_code == 400
    assert "R-POS" in json.dumps(r.json())
    assert benford({"test": "first_digit", "counts": [1] * 9,
                    "min": 10, "max": 9}).status_code == 400
    r = benford({"test": "first_digit", "counts": [1] * 9,
                 "min": 1, "max": 9, "seed": 42})
    assert r.status_code == 400
    assert "seed" in json.dumps(r.json())


def test_benford_min_max_accept_decimal_strings():
    # min/max en chaines decimales exactes — le couple des comptes OFGL
    # B1 (litteraux 1.81 / 7045868.82, ratio > 10^4) passe sans float.
    d = benford({"test": "first_digit",
                 "counts": [301, 176, 125, 97, 79, 67, 58, 51, 46],
                 "min": "1.81", "max": "7045868.82"})
    assert d.status_code == 200
    assert d.json()["verdict"] in ("CONFORMS", "NONCONFORMITY")


def test_receipts_deterministic():
    # meme question, memes octets : le sha256 du recu se rejoue.
    b = {"mode": "gof", "counts": [14, 6, 10, 10, 10]}
    r1, r2 = chi2(b), chi2(b)
    assert r1.json()["sha256"] == r2.json()["sha256"]
    b = {"mode": "critical", "df": 89, "alpha": "0.05"}
    assert chi2(b).json()["sha256"] == chi2(b).json()["sha256"]
    b = {"test": "last_digit", "counts": [100] * 10, "min": 100,
         "max": 999}
    assert benford(b).json()["sha256"] == benford(b).json()["sha256"]


# ============ la porte elle-meme : surfaces ============

def test_route_answers_the_campaign_pains():
    # Douleurs mesurees de campagne : « chi square critical value »,
    # « chi square goodness of fit », « benford first digit » etaient
    # des routes VIDES. Elles repondent desormais.
    for q, want in (("chi square critical value", "stats_chi2"),
                    ("chi-square goodness of fit frequency", "stats_chi2"),
                    ("benford first digit", "benford_digit_test"),
                    ("mean absolute deviation digit distribution",
                     "benford_digit_test")):
        r = client.get("/route", params={"q": q})
        assert r.status_code == 200
        names = [t["tool"] for t in r.json()["tools"]]
        assert want in names, (q, names[:5])


def test_tool_specs_resolve():
    for name in ("stats_chi2", "benford_digit_test"):
        r = client.get("/tools/%s.json" % name)
        assert r.status_code == 200
        assert r.json()["tier"] == "free"


def test_mcp_exposes_the_pair():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert "stats_chi2" in names and "benford_digit_test" in names


def test_g1_erratum_value_recorded():
    # Consigne, pas rejouable depuis la compilation : l'erratum G1 dit
    # que le gold MAD (divise par N au lieu de K) a ete rattrape par la
    # porte sur la valeur 0.083804 (6 dp). Les comptes d'entree du gold
    # vivent dans le GOLDS.md du releveur (stocke:false) — ABSENTS de la
    # compilation. Ce test fixe la VALEUR comme attestation ; il refuse
    # qu'on lui invente un input. La regle K (diviser par le nombre de
    # bins) est celle du kit : mad = somme|AP-EP|/K, jamais /N.
    import benfordkit
    import inspect
    src = inspect.getsource(benfordkit.test_run)
    assert "/ k" in src  # la MAD division est /K (bins), pas /N
