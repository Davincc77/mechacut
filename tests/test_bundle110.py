# -*- coding: utf-8 -*-
"""bundle110 — /shop/soldes-lu : les dates luxembourgeoises PAR ACTE.

Golds tracés À LA MAIN sur l'oracle séparé g110 (scratch/oracle_g110.py,
écrit AVANT le module) et les dix actes rejoués legilux le 25-11-2026
(09h55-10h05) — jamais recopiés du module. L'oracle a d'abord été
auto-vérifié : 48 dates d'actes confrontées au calendrier, chaque nom
de jour imprimé retrouvé, SAUF les deux coquilles d'État nommées —
2017 A-807 (« samedi, le 29 juin 2018 » : un VENDREDI) et 2022 A-511
(« samedi, le 23 juillet 2023 » : un DIMANCHE). La douleur est la
classe maison exacte : une borne du lendemain ratée, cette fois par le
Journal officiel lui-même — et le RECTIFICATIF (A-96, publié
24-02-2023) déplace la BORNE, pas le nom de jour. Deux rectificatifs,
deux natures, jouées distinctes dans la réponse.

La chaîne 2021, version LU : contrairement à la belge (report +
prolongation par LOI), l'ajournement du 30-déc-2020 (A-1107) ne
portait AUCUNE DATE (« reportée à une date ultérieure ») et a été
ABROGÉ par le RGD du 13-janv-2021 (A-24) qui recâble 20-janv →
17-févr. Trois actes voyagent, dont un mort ; jamais de date inventée.

La divergence structurelle est jouée, pas moyennee : la loi du
23-déc-2016 ne connaît AUCUNE période d'attente (le texte rejoué n'a
zéro occurrence d'« attente ») — le champ « waiting » de /shop/
soldes-be N'EXISTE PAS ici, et le test le vérifie par l'ABSENCE.

Le routeur : la douleur pêchée par la sonde du lot (« saldos
luxemburgo datas 2027 » routait chart_from_data — stem « datas » →
« data ») meurt guérie ; le veto CLASSE b110 ne prescrit la table LU
qu'aux requêtes la nommant.
"""
import datetime as _date

import pytest

import soldeslukit as SL

WEEK_FR = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi",
           "dimanche")


def wd(iso):
    return WEEK_FR[_date.date.fromisoformat(iso).weekday()]


# ---------------------------------------------------------- le gold main
# année -> saison -> (label, debut, fin, duree) — recopié des actes.
GOLD = {
    2018: {"hiver": ("hiver 2017/2018", "2017-12-29", "2018-01-27", 30),
           "ete": ("été 2018", "2018-06-29", "2018-07-28", 30)},
    2019: {"hiver": ("hiver 2018/2019", "2018-12-29", "2019-01-26", 29),
           "ete": ("été 2019", "2019-06-28", "2019-07-27", 30)},
    2020: {"hiver": ("hiver 2019/2020", "2020-01-02", "2020-01-25", 24),
           "ete": ("été 2020", "2020-06-26", "2020-07-25", 30)},
    2021: {"hiver": ("hiver 2020/2021", "2021-01-20", "2021-02-17", 29),
           "ete": ("été 2021", "2021-06-26", "2021-07-24", 29)},
    2022: {"hiver": ("hiver 2021/2022", "2022-01-03", "2022-01-29", 27),
           "ete": ("été 2022", "2022-06-24", "2022-07-23", 30)},
    2023: {"hiver": ("hiver 2022/2023", "2023-01-02", "2023-01-28", 27),
           "ete": ("été 2023", "2023-06-24", "2023-07-22", 29)},
    2024: {"hiver": ("hiver 2023/2024", "2024-01-02", "2024-01-27", 26),
           "ete": ("été 2024", "2024-06-24", "2024-07-20", 27)},
    2025: {"hiver": ("hiver 2024/2025", "2025-01-02", "2025-01-25", 24),
           "ete": ("été 2025", "2025-06-27", "2025-07-26", 30)},
    2026: {"hiver": ("hiver 2025/2026", "2026-01-02", "2026-01-31", 30),
           "ete": ("été 2026", "2026-06-24", "2026-07-19", 26)},
    2027: {"hiver": ("hiver 2026/2027", "2027-01-02", "2027-01-30", 29),
           "ete": ("été 2027", "2027-06-26", "2027-07-24", 29)},
}


def W(year, season, **kw):
    out = SL.soldes_lu(year, season=season, **kw)
    return out["windows"][0]


# ------------------------------------------------------------ les vecteurs
def test_table_complete_x20_fenetres():
    for year, seasons in GOLD.items():
        res = SL.soldes_lu(year)
        assert [w["season"] for w in res["windows"]] == ["hiver", "ete"]
        for s, (label, start, end, length) in seasons.items():
            w = W(year, s)
            assert w["label"] == label, (year, s)
            assert w["start"] == start and w["end"] == end, (year, s)
            assert w["length_days"] == length, (year, s)
            # le nom de jour est CALÉ sur le calendrier, pas sur la
            # mémoire de l'acte : chaque borne porte son vrai jour.
            assert w["start_weekday"] == wd(start)
            assert w["end_weekday"] == wd(end)


def test_invariant_un_mois_maximum():
    # la loi (art. 1er § 4) borne à un mois ; la table rejouée tient
    # ligne à ligne — max 30, min 24 (consigné dans cap_check).
    lengths = [W(y, s)["length_days"]
               for y in GOLD for s in ("hiver", "ete")]
    assert max(lengths) == 30 and min(lengths) == 24
    assert "max table : 30, min : 24" in SL.soldes_lu(2023)["cap_check"]


def test_hiver2027_acte_en_vigueur():
    w = W(2027, "hiver")
    assert w["act"]["memorial"] == "Mémorial A n° 330 de 2026"
    assert "samedi, le 2 janvier 2027" in w["act"]["verbatim"]
    assert w["basis"].startswith("ACTE")


def test_ete2026_borne_dimanche_dite():
    # LU n'a pas la pudeur du dimanche belge : l'acte A-327 clot
    # un DIMANCHE et le dit lui-même — print_matches : VRAI.
    w = W(2026, "ete")
    assert w["end"] == "2026-07-19" and w["end_weekday"] == "dimanche"
    assert w["print_matches_calendar"] is True
    assert "dimanche, le 19 juillet 2026" in w["act"]["verbatim"]


# ------------------------------------------------- les deux rectificatifs
def test_rect_2018_corige_le_nom_de_jour_seul():
    w = W(2018, "ete")
    rect = w["rectification"]
    assert rect["type"] == "nom_de_jour_seul"
    assert "A n° 928 de 2017" in rect["memorial"]
    assert rect["original_imprime"] == "samedi, le 29 juin 2018"
    assert rect["rectifie_en"] == "vendredi, le 29 juin 2018"
    # LA DATE NE BOUGE PAS : le 29-06-2018 était vendredi — la
    # calendrier tranche, l'acte original s'était trompé d'étiquette.
    assert w["start"] == "2018-06-29"
    assert w["start_weekday"] == "vendredi"
    assert wd("2018-06-29") == "vendredi"  # vérité calendar indépendante
    assert w["print_matches_calendar"] is False  # l'ACTE imprimait faux


def test_rect_2023_deplace_la_borne_elle_meme():
    w = W(2023, "ete")
    rect = w["rectification"]
    assert rect["type"] == "date_elle_meme"
    assert "A n° 96 de 2023" in rect["memorial"]
    assert "23 juillet 2023" in rect["original_imprime"]
    assert w["end"] == "2023-07-22"
    assert w["end_weekday"] == "samedi"
    # la coquille était double : le 23-07-2023 était un DIMANCHE —
    # l'acte publié contredisait son propre jour nommé.
    assert wd("2023-07-23") == "dimanche"
    assert "la presse" in rect["note"]  # la presse disait 22 depuis le début


def test_hiver2018_sans_rectification_voyage_propre():
    w = W(2018, "hiver")
    assert "rectification" not in w
    assert w["print_matches_calendar"] is True


# ------------------------------------------------------------ chaîne 2021
def test_chaine_2021_trois_actes_dont_un_mort():
    w = W(2021, "hiver")
    chain = w["acts_chain"]
    assert [c["role"] for c in chain] == ["fixe", "ajourne_sans_date",
                                          "recable"]
    assert chain[0]["memorial"] == "Mémorial A n° 819 de 2020"
    assert chain[0]["verbatim"].startswith("début : samedi, le 2 "
                                           "janvier 2021")
    # l'ajournement ne portait AUCUNE date : texte nu, jamais daté.
    assert "ultérieure" in chain[1]["verbatim"]
    assert "abrog" in chain[1]["status"].lower()
    assert "2021" not in chain[1]["verbatim"]
    assert chain[2]["memorial"] == "Mémorial A n° 24 de 2021"
    # la fenêtre FINALE est celle du recâblage :
    assert (w["start"], w["end"]) == ("2021-01-20", "2021-02-17")
    assert w["act"]["memorial"] == "Mémorial A n° 24 de 2021"
    assert "AJOURNEMENT" in w["divergence_be"] or "ajournement" in \
        w["divergence_be"]


def test_ete2021_vit_sous_l_acte_original():
    # seul l'hiver fut recâblé ; l'été 2021 reste à A-819 :
    w = W(2021, "ete")
    assert w["act"]["memorial"] == "Mémorial A n° 819 de 2020"
    assert "chain" not in SL.ACTES[2021]["ete"]


# ------------------------------------------------------------- les gates
def test_gate_2017_refuse_porte_les_faits_de_2002():
    with pytest.raises(SL.SoldesLuError) as e:
        SL.soldes_lu(2017)
    m = e.value.message
    assert "15-sept-2016" in m and "30-juil-2002" in m
    assert "A-199" in m
    assert e.value.field == "year"
    # les dates anciennes VOYAGENT dans le refus (rejouées), jamais
    # comme lignes de la table :
    assert "2016-12-30" not in m and "30-déc-2016" in m


def test_gate_2016_refuse_sans_pret_de_date():
    with pytest.raises(SL.SoldesLuError) as e:
        SL.soldes_lu(2016)
    assert "30-juil-2002" in e.value.message
    assert "zero date pretee a la memoire" in e.value.message


@pytest.mark.parametrize("y", [2028, 2029, 2099])
def test_avenir_refuse_pas_de_prophetie(y):
    with pytest.raises(SL.SoldesLuError) as e:
        SL.soldes_lu(y)
    m = e.value.message
    assert "chaque" in m.lower()
    assert "A-330" in m or "06-juil-2026" in m
    assert e.value.field == "year"
    # aucune date de l'année refusée n'est prêtée à la réponse :
    assert str(y) + "-" not in m


def test_annee_non_entiere_refusee():
    with pytest.raises(SL.SoldesLuError):
        SL.soldes_lu("deux-mille")


# ------------------------------------------------------- territoires nommés
def test_france_renvoie_chez_la_soeur_window():
    with pytest.raises(SL.SoldesLuError) as e:
        SL.soldes_lu(2027, territory="france")
    assert "/shop/soldes-window" in e.value.message


def test_belgique_renvoie_chez_la_soeur_be():
    with pytest.raises(SL.SoldesLuError) as e:
        SL.soldes_lu(2027, territory="Belgique")
    assert "/shop/soldes-be" in e.value.message
    assert e.value.field == "territory"


@pytest.mark.parametrize("t", ["suisse", "québec", "Canada", "brésil",
                               "Deutschland", "united kingdom",
                               "portugal", "états-unis", "maroc"])
def test_calendriers_etrangers_refuses(t):
    with pytest.raises(SL.SoldesLuError):
        SL.soldes_lu(2027, territory=t)


@pytest.mark.parametrize("t", ["luxembourg", "Luxembourg-Ville",
                               "esch-sur-alzette", "lëtzebuerg",
                               "groussherzogtum", "Diekirch", "lux"])
def test_aliases_luxembourgeois_passent(t):
    assert SL.soldes_lu(2027, territory=t)["year"] == 2027


def test_saison_inconnue_refusee():
    with pytest.raises(SL.SoldesLuError) as e:
        SL.soldes_lu(2027, season="printemps")
    assert e.value.field == "season"


def test_wanter_luxembourgeois_vote_hiver():
    # « Wanter-Solden » — verbatim du communiqué rejoué (rtl.lu) :
    w = SL.soldes_lu(2027, season="wanter")["windows"]
    assert w[0]["season"] == "hiver"


# --------------------------------------------------------- l'absence jouée
def test_zero_attente_partout():
    res = SL.soldes_lu(2027)
    for w in res["windows"]:
        assert "waiting" not in w
        assert "standstill" not in w
    assert "VI.29" in res["no_waiting_period"]  # la divergence est Nommée
    assert "AUCUNE période" in res["no_waiting_period"]


# ------------------------------------------------------------------ as_of
def test_statut_aujour():
    res = SL.soldes_lu(2027, as_of="2026-11-25")
    hiver, ete = res["windows"]
    assert hiver["status"] == "UPCOMING"
    assert hiver["days_to_start"] == 38
    assert ete["status"] == "UPCOMING" and ete["days_to_start"] == 213


def test_statut_en_cours_et_ended():
    w = W(2023, "hiver", as_of="2023-01-10")
    assert w["status"] == "IN_PROGRESS" and w["days_left"] == 18
    w = W(2026, "hiver", as_of="2026-11-25")
    assert w["status"] == "ENDED" and w["days_since_end"] == 298


def test_as_of_mal_forme_refuse():
    with pytest.raises(SL.SoldesLuError) as e:
        SL.soldes_lu(2027, as_of="2027-1-2")
    assert e.value.field == "as_of"


# ------------------------------------------------------------------ route
import routing  # noqa: E402


def top1(q):
    rows = routing.route(q)
    return rows[0]["tool"] if rows else None


def rows_tools(q):
    return [r["tool"] for r in routing.route(q)]


def test_aiguilles_top1_lu():
    for q in ("soldes luxembourg janvier 2027",
              "quand commencent les soldes au luxembourg",
              "luxembourg sale dates winter 2027",
              "saldos luxemburgo datas 2027",
              "reglement grand-ducal soldes 2027"):
        assert top1(q) == "shop_soldes_lu", q


def test_douleur_pt_guerie():
    # « datas » ne vole plus la requête à chart_from_data :
    tools = rows_tools("saldos luxemburgo datas 2027")
    assert tools[0] == "shop_soldes_lu"
    assert "chart_from_data" not in tools[:1]


def test_veto_soeurs_tenu():
    # nommer la Belgique ne prescrit PAS la table LU :
    assert top1("soldes belgique janvier 2027") == "shop_soldes_be"
    assert "shop_soldes_lu" not in rows_tools("soldes belgique 2027")
    # nommer un calendrier sans table ne prescrit AUCUNE des trois :
    tools = rows_tools("suisse soldes janvier 2027")
    assert "shop_soldes_lu" not in tools
    assert "shop_soldes_window" not in tools


def test_les_deux_soeurs_ignorent_lu_quand_lux_nomme():
    tools = rows_tools("soldes luxembourg janvier 2027")
    assert tools[0] == "shop_soldes_lu"
    assert "shop_soldes_be" not in tools
    assert "shop_soldes_window" not in tools


def test_leurre_blague_meurt():
    assert routing.route("blague sur les soldes luxembourg") == []


def test_sans_pays_trois_tables_vivent():
    # la demande sépare, le routeur ne devine pas : les trois vivent,
    # aucune promesse de juridiction.
    tools = rows_tools("quand commencent les soldes 2027")
    assert "shop_soldes_window" in tools


def test_mots_communs_ne_surclassent_aucune_table():
    # RADAR 11h17 — la RÉGRESSION pêchée par le scan de fermeture,
    # épinglée pour de bon : « les soldes d'été 2027 débutent-ils le
    # 23 ou le 30 juin » (ligne b103 du corpus, want window) était
    # devenue TOP1_WRONG parce que MES tags LU portaient « quand
    # commencent » + « juin » — 6 points volés à une phrase sans
    # pays. Les tags LU sont revenus aux noms propres ; la fenêtre
    # été reste jurée chez la sœur, comme son hiver.
    assert top1("les soldes d'été 2027 débutent-ils le 23 ou le "
                "30 juin") == "shop_soldes_window"
    assert top1("quand commencent les soldes d'hiver 2027") == \
        "shop_soldes_window"
    # et les aiguilles du lot vivent SANS les mois ni les verbes :
    for q in ("soldes luxembourg janvier 2027",
              "les soldes d'hiver au luxembourg 2027"):
        assert top1(q) == "shop_soldes_lu", q


# ------------------------------------------------------------- endpoint API
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

main.RATE_LIMIT = 10**9
client = TestClient(main.app)


def test_endpoint_200_sha():
    r = client.post("/api/v1/shop/soldes-lu",
                    json={"year": 2027, "season": "hiver"})
    assert r.status_code == 200
    b = r.json()
    assert b["windows"][0]["start"] == "2027-01-02"
    assert "sha256" in b


def test_endpoint_400_nomme_le_champ():
    r = client.post("/api/v1/shop/soldes-lu", json={"year": 2028})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "year" and e["expected"]


def test_endpoint_inattendu_refuse():
    r = client.post("/api/v1/shop/soldes-lu",
                    json={"year": 2027, "pays": "fr"})
    assert r.status_code == 400


# --------------------------------------------------------- manifest & sœurs
def test_manifest_182_et_ligne_lu():
    body = client.get("/agent/manifest").text
    # b112 elagage : « deterministic » est tombe de la tete a claim
    # constant (le tracteur sha256 + « POSTs carry sha256 » certifient
    # le meme nom) — le compteur lu reste le test : TABLE 193 -
    # recipes 9 = 184 transforms, compte a la main.
    # b113 relève : TABLE 194 - recipes 9 = 185 transforms, compte à la main.
    assert "187 transforms + 9 recipes" in body  # b115 : +money_settle, 196-9=187
    assert "shop_soldes_lu  /api/v1/shop/soldes-lu  free" in body
    assert len(body.encode("utf-8")) < 9000


def test_soeur_be_relais_vivant_plus_file():
    import soldesbekit as SB
    with pytest.raises(SB.SoldesBeError) as e:
        SB.soldes_be(2027, territory="luxembourg")
    m = e.value.message
    assert "/shop/soldes-lu" in m
    assert "en file" not in m.lower()
    # la citation corrigée par le gate vit dans le refus :
    assert "art. 1er" in m


def test_registry_et_spec_outils():
    r = client.get("/tools/shop_soldes_lu.json")
    assert r.status_code == 200
    b = r.json()
    assert b["tier"] == "free" and b["pack"] == "dates"
    assert "RECTIFICATIF" in b["purpose"] or "rectifications" in \
        b["purpose"].lower() or "act" in b["purpose"]


def test_onze_pins_soldeslu_adds_only():
    import json
    g = json.loads(open("golden.json", encoding="utf-8").read())
    lu = [k for k in g if k.startswith("shop_soldeslu_")]
    assert len(lu) == 11
    assert sum(1 for k in lu if k.endswith("refuse")) == 5
    # adds-only global : 344 + 11 = 355, la pin soeur REMPLACEE (pas
    # retiree) porte son contrat neuf sous le MÊME nom.
    # b111 relève à 364 : +9 agent_tooloverlap (adds-only, zero retirée,
    # vecteurs publics — le contrat des sœurs n'a pas bougé d'un octet).
    # b112 relève à 374 : +10 invoice_payment_due (adds-only).
    # b114 relève à 392 : +9 json_bigint (adds-only, vecteurs publics) ; b113 relève à 383 : +9 agent_mcplist (adds-only, vecteurs
    # PUBLICS — #6935, codex, claude-web, vercel).
    # b115 relève à 400 : +8 money_settle (adds-only, vecteurs du
    # fil r/askmath) ; b114 relève à 392 : +9 json_bigint
    assert len(g) == 400
    assert g["shop_soldesbe_luxembourg_refuse"].startswith("400:")


def test_sayings_parite_x3_langues():
    import sayings
    s = sayings.SAY["/api/v1/shop/soldes-lu"]
    for lang in ("en", "fr", "pt"):
        assert s[lang], lang
        assert "2026/2027" in s[lang] and "2023" in s[lang], lang
