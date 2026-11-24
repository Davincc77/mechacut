# -*- coding: utf-8 -*-
"""Bundle 103 — /shop/soldes-window : les dates LÉGALES des soldes,
grammaire D-art.1er fermée, annexe versionnée, derogations annuelles
au verbatim. Golds tracés À LA MAIN sur l'oracle scratch g103
(calendar stdlib + tables de presse comme oracle indépendant :
calendriergratuit 2026-2029, tpeactu territoires 2027, dgccrf Corse
8 juil.->4 août 2026, Cher/Orne 30 juin->27 juil. 2021, AN n°437) —
sens habituel : le test suit la main ; si la machine contredit, on
vérifie DEUX FOIS qui a raison (la main a déjà été reprise une fois
par le calendrier sur ce bundle : 2021-07-13 -> 2021-07-14, l'oracle
suit le calendrier, pas la mémoire).

Golds principaux (oracle g103) :
  A. BORNES STRICTES de l'article 1er, vécues des DEUX côtés :
     hiver 2028 : 2e mercredi = 12 JANVIER PILE -> PAS d'avance
     (6 janv. serait la faute du modèle qui applique la clause sans
     lire « après ») ; hiver 2027 : 13 > 12 -> avance au 6 ;
     été 2028 : dernier mercredi = 28 JUIN PILE -> pas d'avance ;
     été 2027 : 30 > 28 -> avance au 23 — lecalendrier qui titre
     « jusqu'au 9 février » pour 2027 est la douleur pêchée en flag.
  B. fin INCLUSE = début + 27 (4 semaines), confirmé par quatre
     sources officielles ou de presse concordantes (2026 réel
     7 janv.->3 févr. ; Corse 8 juil.->4 août dgccrf ; SPM
     20 janv.->16 févr. tpeactu ; Moselle 30 juin->27 juil. 2021
     arrêtés préfectoraux).
  C. SIX derogations annuelles rejouées, chacune avec verbatim +
     source : été 2020 (15 juil., + 06/2A/2B/66 nommés), hiver 2021
     (20 janv. + 54/55/57/88/971 nommés ; DURÉE PORTÉE À SIX
     SEMAINES le 15 février 2021, 974/977/978 exceptées NOMMÉMENT,
     975 COM non nommée reste à quatre), été 2021 (30 juin — et la
     MOSSELLE SEULE au 26 juin, la ligne que la presse ne recopie
     jamais), Guadeloupe été 2021 (jeudi 7 octobre), été 2023
     (cinq semaines pour les départements du 28 juin), été 2026
     (cinq semaines article 1er, canicule).
  D. ANNEXE VERSIONNÉE : la ligne INITIALE de 06/66/973 vit pour les
     fenêtres COMMENCÉES avant le 17 mai 2023 (été 2020-2022, hiver
     2023 : 4 janvier) ; après, droit commun. La presse (moneyvox,
     juillet 2023) recyclait la ligne abrogée en Guyane (5 oct.->
     1 nov.) ; le texte consolidé dit 28 juin -> 1er août : la table
     suit le TEXTE et la divergence est nommée dans le module.
  E. AMBIGUÏTÉ « premier jour ouvré » : jugée APRÈS derogations —
     2027 : les DEUX fenêtres voyagent (lundi 4 primaire, samedi 2
     presse, le mot de l'arrêté est ouvré) ; 2021 : l'arrêté nomme
     le 20 janvier, le conflit ne joue plus ; 2022 : les deux
     lectures donnent la MÊME date, pas de conflit (le conflit est
     daté, pas permanent).
"""
import main
import pytest
import soldeskit as k
from fastapi.testclient import TestClient

client = TestClient(main.app)

M = "metropole"


# ---------------------------------------------------------------- art. 1er hiver
def test_a1_hiver_2027_avance_apres_le_12():
    r = k.soldes_window(2027, M, "hiver")
    w = r["windows"][0]
    assert w["start"] == "2027-01-06"
    assert w["start_weekday"] == "Wednesday"
    assert w["end_inclusive"] == "2027-02-02"
    assert w["start_time"] == "08:00"
    assert w["duration_weeks"] == 4
    assert w["rule"]["second_wednesday"] == "2027-01-13"
    assert w["rule"]["advanced"] is True


def test_a1b_hiver_2028_borne_12_pile_pas_avance():
    # « intervient APRÈS le 12 » est strict : le 12 lui-même ne
    # déclenche rien. 2028-01-12 est le 2e mercredi -> il RESTE.
    r = k.soldes_window(2028, M, "hiver")
    w = r["windows"][0]
    assert w["start"] == "2028-01-12"
    assert w["end_inclusive"] == "2028-02-08"
    assert w["rule"]["advanced"] is False


def test_a1c_hiver_2026_reel():
    # l'année VÉCUE : 14 > 12 -> avancé au 7 janvier, fin 3 février,
    # la presse officielle du jour le confirme.
    w = k.soldes_window(2026, M, "hiver")["windows"][0]
    assert (w["start"], w["end_inclusive"]) == ("2026-01-07",
                                                "2026-02-03")


def test_a1d_hiver_2020_2025_pas_davance():
    for year, start, end in ((2020, "2020-01-08", "2020-02-04"),
                             (2022, "2022-01-12", "2022-02-08"),
                             (2023, "2023-01-11", "2023-02-07"),
                             (2024, "2024-01-10", "2024-02-06"),
                             (2025, "2025-01-08", "2025-02-04")):
        w = k.soldes_window(year, M, "hiver")["windows"][0]
        assert (year, w["start"]) == (year, start)
        assert w["end_inclusive"] == end


def test_a1e_verbatim_voyage():
    w = k.soldes_window(2027, M, "hiver")["windows"][0]
    assert "deuxi\u00e8me mercredi" in w["rule"]["verbatim"]
    assert "apr\u00e8s le 12 du mois" in w["rule"]["verbatim"]
    assert "quatre semaines" in k.soldes_window(2027, M, "hiver")[
        "duration_rule"]


# ---------------------------------------------------------------- art. 1er été
def test_b1_ete_2027_avance_apres_le_28():
    w = k.soldes_window(2027, M, "ete")["windows"][0]
    assert w["start"] == "2027-06-23"
    assert w["end_inclusive"] == "2027-07-20"
    assert w["rule"]["last_wednesday"] == "2027-06-30"
    assert w["rule"]["advanced"] is True


def test_b1b_ete_2028_borne_28_pile():
    # le 28 juin 2028 EST le dernier mercredi -> pas d'avance ;
    # le 29 juin 2022 ne « pile » pas -> avancé au 22.
    w = k.soldes_window(2028, M, "ete")["windows"][0]
    assert w["start"] == "2028-06-28"
    assert w["rule"]["advanced"] is False
    w2 = k.soldes_window(2022, M, "ete")["windows"][0]
    assert w2["start"] == "2022-06-22"
    assert w2["end_inclusive"] == "2022-07-19"


def test_b1c_ete_reels_2024_2025_2026_2029():
    for year, start in ((2024, "2024-06-26"), (2025, "2025-06-25"),
                        (2026, "2026-06-24"), (2029, "2029-06-27")):
        w = k.soldes_window(year, M, "ete")["windows"][0]
        assert (year, w["start"]) == (year, start)


# ---------------------------------------------------------------- fins incluses
def test_c1_fin_incluse_bornes_status():
    # as_of LE JOUR de fin : IN_PROGRESS, 0 jour restant (la borne
    # est comptée, même idiome que gift-voucher 66A(1)).
    w = k.soldes_window(2026, M, "hiver", as_of="2026-02-03")[
        "windows"][0]
    assert w["status"] == "IN_PROGRESS"
    assert w["days_left"] == 0
    w = k.soldes_window(2026, M, "hiver", as_of="2026-02-04")[
        "windows"][0]
    # DEUX FOIS vérifié : days_since_end est la différence STRICTE de
    # dates (2026-02-04 - 2026-02-03 = 1), même idiom que days_left /
    # days_since de gift-voucher — la main avait posé 0, la machine a
    # raison sur l'arithmétique, le test suit la raison tracée.
    assert w["status"] == "ENDED"
    assert w["days_since_end"] == 1
    w = k.soldes_window(2026, M, "hiver", as_of="2026-01-07")[
        "windows"][0]
    assert w["status"] == "IN_PROGRESS"
    assert w["days_left"] == 27


def test_c2_compte_a_rebours_du_jour():
    # vecteur PRESSE du jour : « Dans 43 jours » (calendriergratuit,
    # 24-nov-2026) — l'arithmétique rend le même nombre, zéro horloge.
    w = k.soldes_window(2027, M, "hiver", as_of="2026-11-24")[
        "windows"][0]
    assert w["status"] == "UPCOMING"
    assert w["days_to_start"] == 43


# ---------------------------------------------------------------- derogations
def test_d1_hiver_2021_date_puis_duree_six():
    w = k.soldes_window(2021, M, "hiver")["windows"][0]
    assert w["start"] == "2021-01-20"
    assert w["duration_weeks"] == 6
    assert w["end_inclusive"] == "2021-03-02"
    srcs = [d["arrete"] for d in w["derogations_applied"]]
    assert srcs == ["arr\u00eat\u00e9 du 23 d\u00e9cembre 2020",
                    "arr\u00eat\u00e9 du 15 f\u00e9vrier 2021"]


def test_d1b_est_et_guadeloupe_nommés_par_la_date():
    for t in ("54", "55", "57", "88", "971"):
        w = k.soldes_window(2021, t, "hiver")["windows"][0]
        assert (t, w["start"]) == (t, "2021-01-20")
        assert w["duration_weeks"] == 6, t


def test_d1c_reunion_977_978_duree_inchangee_nomment():
    # l'arrêté du 15 février 2021 EXCLUT nommément 974/977/978 :
    # quatre semaines. La fenêtre hiver de la Réunion vit en
    # septembre (annexe), non dérogée par la date : 4 sept. -> 1 oct.
    w = k.soldes_window(2021, "974", "hiver")["windows"][0]
    assert w["start"] == "2021-09-04"
    assert w["duration_weeks"] == 4
    assert w["end_inclusive"] == "2021-10-01"
    for t in ("977", "978"):
        w = k.soldes_window(2021, t, "hiver")["windows"][0]
        assert (t, w["duration_weeks"]) == (t, 4)


def test_d1d_975_com_non_nommee_reste_quatre():
    # « six semaines pour l'ensemble des départements » — la COM
    # 975 n'est ni département ni nommée : la lecture voyage avec
    # le verbatim, pas avec la mémoire.
    w = k.soldes_window(2021, "975", "hiver")["windows"][0]
    assert w["duration_weeks"] == 4
    assert w["start"] == "2021-01-20"  # par l'ANNEXE (1er merc après
                                       # le 15), non par la dérogation
    assert w["derogations_applied"] == []


def test_d2_ete_2020_trente_juillet_tous_etendue():
    # l'arrêté du 10 juin 2020 étend NOMMÉMENT le 15 juillet à
    # 06/2A/2B/66 ; les autres zones d'annexe restent inchangées.
    for t in (M, "06", "2A", "2B", "66"):
        w = k.soldes_window(2020, t, "ete")["windows"][0]
        assert (t, w["start"]) == (t, "2020-07-15")
        assert w["start_time"] == "08:00"
        assert w["end_inclusive"] == "2020-08-11"
    w = k.soldes_window(2020, "974", "ete")["windows"][0]
    assert w["start"] == "2020-02-01"  # annexe inchangée : 1er sam. févr.
    w = k.soldes_window(2020, "971", "ete")["windows"][0]
    assert w["start"] == "2020-09-26"  # dernier sam. sept. inchangé


def test_d3_moselle_seule_2021():
    # la ligne que AUCUN calendrier grand public ne recopie :
    w = k.soldes_window(2021, "57", "ete")["windows"][0]
    assert w["start"] == "2021-06-26"
    assert w["end_inclusive"] == "2021-07-23"
    assert "26 juin 2021" in w["derogations_applied"][0]["effect"]
    # et le droit commun 2021 EST le 30 juin (le report d'une
    # semaine va CONTRE l'avance de la règle — l'arrêté déplace la
    # date, pas la grammaire) :
    w = k.soldes_window(2021, M, "ete")["windows"][0]
    assert w["start"] == "2021-06-30"
    assert w["end_inclusive"] == "2021-07-27"
    assert w["rule"]["last_wednesday"] == "2021-06-30"
    assert w["rule"]["advanced"] is True


def test_d3b_corse_ete_2021_non_derogee():
    w = k.soldes_window(2021, "2A", "ete")["windows"][0]
    assert w["start"] == "2021-07-14"  # main reprise par le calendrier :
    # 1er juillet 2021 JEUDI -> 1er merc 7, 2e merc 14. L'arrêté du
    # 15 juin 2021 ne nomme que l'article 1er et la Moselle.
    assert w["end_inclusive"] == "2021-08-10"
    assert w["derogations_applied"] == []


def test_d4_guadeloupe_2021_jeudi_sept():
    w = k.soldes_window(2021, "971", "ete")["windows"][0]
    assert w["start"] == "2021-10-07"
    assert w["end_inclusive"] == "2021-11-03"
    # coincidence NOMMÉE dans le module : la Martinique, elle, tient
    # la MÊME date par l'annexe — deux sources, une date.
    w = k.soldes_window(2021, "972", "ete")["windows"][0]
    assert w["start"] == "2021-10-07"
    assert w["derogations_applied"] == []


def test_d5_ete_2023_cinq_sem_pour_le_28_juin():
    w = k.soldes_window(2023, M, "ete")["windows"][0]
    assert w["start"] == "2023-06-28"
    assert w["duration_weeks"] == 5
    assert w["end_inclusive"] == "2023-08-01"
    # les dates ANNEXES restent à quatre (moneyvox : Corse 12 juil.
    # -> 8 août, et 8+27=… l'annexe dit deuxième mercredi : 12 juillet)
    w = k.soldes_window(2023, "2A", "ete")["windows"][0]
    assert w["start"] == "2023-07-12"
    assert w["duration_weeks"] == 4
    assert w["end_inclusive"] == "2023-08-08"


def test_d6_ete_2026_cinq_sem_canicule():
    # la presse du cycle (service-public A15000 + dgccrf) : « ont
    # débuté le mercredi 24 juin et devaient se terminer le 21
    # juillet ; en raison de la canicule [...] jusqu'au mardi 28
    # juillet au soir ». Le verbatim de l'arrêté du 3 juillet 2026
    # voyage avec la fenêtre.
    w = k.soldes_window(2026, M, "ete")["windows"][0]
    assert w["start"] == "2026-06-24"
    assert w["duration_weeks"] == 5
    assert w["end_inclusive"] == "2026-07-28"
    assert any("3 juillet" in d["arrete"]
               for d in w["derogations_applied"])
    # la CORSE, annexe, n'est PAS portée à cinq (dgccrf : 8 juil. ->
    # 4 août — quatre confirmations croisées du jour du début compté)
    w = k.soldes_window(2026, "2A", "ete")["windows"][0]
    assert w["duration_weeks"] == 4
    assert w["end_inclusive"] == "2026-08-04"
    # les départements d'EST soldent leur ÉTÉ sur l'article 1er (leur
    # annexe ne porte que l'hiver) -> eux aussi à cinq semaines :
    w = k.soldes_window(2026, "57", "ete")["windows"][0]
    assert w["duration_weeks"] == 5


# ---------------------------------------------------------------- annexe versionnée
def test_e1_lignes_abrogees_avant_switch():
    # 06 et 66 : été au PREMIER mercredi de juillet jusqu'au 16 mai
    # 2023 inclus (fenêtres 2020-2022) ; la Guyane aussi pour son
    # hiver (1er mercredi) et son été (1er jeudi).
    for year, start in ((2022, "2022-07-06"),):
        for t in ("06", "66"):
            w = k.soldes_window(year, t, "ete")["windows"][0]
            assert (t, w["start"]) == (t, start)
    w = k.soldes_window(2021, "973", "hiver")["windows"][0]
    assert w["start"] == "2021-01-06"   # 1er mercredi, ANNEXE non
                                        # dérogée par la date 2021
    w = k.soldes_window(2020, "973", "ete")["windows"][0]
    assert w["start"] == "2020-10-01"   # 1er jeudi d'octobre


def test_e1b_apres_switch_droit_commun():
    # l'arrêté du 21 avril 2023 (en vigueur 17 mai 2023) SORT 06/66/973
    # de l'annexe : les fenêtres COMMENCÉES après le switch tiennent
    # l'article 1er. L'été 2023 commence le 28 juin -> aligné (Le
    # Figaro le confirme). La presse moneyvox recyclait la ligne
    # guyanaise en octobre : le module suit le TEXTE, la divergence
    # est nommée dans le docstring, les dates du texte voyagent.
    for t in ("06", "66", "973"):
        w = k.soldes_window(2023, t, "ete")["windows"][0]
        assert (t, w["start"]) == (t, "2023-06-28")
        assert w["duration_weeks"] == 5  # art. 1er porté par l'arrêté
    w = k.soldes_window(2024, "973", "hiver")["windows"][0]
    assert w["start"] == "2024-01-10"    # plus de ligne : droit commun
    # MAIS l'hiver 2023 (fenêtre commencée le 4 janvier, avant le
    # switch) garde la ligne initiale :
    w = k.soldes_window(2023, "973", "hiver")["windows"][0]
    assert w["start"] == "2023-01-04"    # 1er mercredi


def test_e2_est_ouvr_annees_pacifiques():
    # les années où les DEUX lectures du mot donnent la même date
    # ne portent PAS de conflit : le conflit est daté, pas permanent.
    for year, start, end in ((2020, "2020-01-02", "2020-01-29"),
                             (2022, "2022-01-03", "2022-01-30"),
                             (2023, "2023-01-02", "2023-01-29"),
                             (2024, "2024-01-02", "2024-01-29"),
                             (2025, "2025-01-02", "2025-01-29"),
                             (2026, "2026-01-02", "2026-01-29")):
        w = k.soldes_window(year, "57", "hiver")["windows"][0]
        assert (year, w["start"]) == (year, start)
        assert w["end_inclusive"] == end
        assert w["conflict"] is None


def test_e3_est_2027_conflit_nomme():
    w = k.soldes_window(2027, "57", "hiver")["windows"][0]
    assert w["start"] == "2027-01-04"           # ouvré strict, premier
    assert w["end_inclusive"] == "2027-01-31"
    c = w["conflict"]
    assert c["class"] == "PREMIER_JOUR_OUVRE_AMBIGUOUS"
    assert c["alternative_start"] == "2027-01-02"  # ouvrable (presse)
    assert c["alternative_end"] == "2027-01-29"
    assert "samedi compte ou non" in c["press"]


def test_e3b_2021_pas_de_conflit_car_date_nommee():
    # le jugement vient APRÈS les dérogations : quand l'arrêté nomme
    # le 20 janvier, le mot « ouvré » ne joue plus, pas d'ambiguïté.
    w = k.soldes_window(2021, "88", "hiver")["windows"][0]
    assert w["conflict"] is None


def test_e4_territoires_inverses_2027():
    # table territoriale vivante (tpeactu + calendriers, rejouée au
    # main) — chaque territoire à son ancre :
    cases = {
        "971": ("hiver", "2027-01-02", "2027-01-29"),   # 1er sam janv
        "974": ("hiver", "2027-09-04", "2027-10-01"),   # 1er sam sept
        "974E": ("ete", "2027-02-06", "2027-03-05"),    # 1er sam févr
        "975": ("hiver", "2027-01-20", "2027-02-16"),   # 1er merc
                                                        # après le 15
        "975E": ("ete", "2027-07-21", "2027-08-17"),    # après le 14
        "977": ("hiver", "2027-05-01", "2027-05-28"),
        "978": ("ete", "2027-10-09", "2027-11-05"),     # 2e sam oct
    }
    for key, (season, start, end) in cases.items():
        t = key[:3]
        w = k.soldes_window(2027, t, season)["windows"][0]
        assert (key, w["start"]) == (key, start)
        assert w["end_inclusive"] == end


def test_e4b_spm_apres_strict_borne():
    # « premier mercredi APRÈS le 15 janvier » : après STRICT. Le
    # 15 janvier 2025 EST mercredi -> la fenêtre s'ouvre le 22, pas
    # le 15. Même grammaire pour « après le 12 » de l'article 1er.
    w = k.soldes_window(2025, "975", "hiver")["windows"][0]
    assert w["start"] == "2025-01-22"
    assert w["end_inclusive"] == "2025-02-18"


def test_e5_martinique_hiver_droit_commun():
    # l'annexe ne déroge pour la 972 que l'ÉTÉ : l'hiver martiniquais
    # suit l'article 1er — « aucune ligne pour cette saison » est dit,
    # pas inventé.
    w = k.soldes_window(2027, "972", "hiver")["windows"][0]
    assert w["start"] == "2027-01-06"
    assert w["rule"]["source"] == "ART1"
    w = k.soldes_window(2027, "972", "ete")["windows"][0]
    assert w["start"] == "2027-10-07"
    assert w["rule"]["source"] == "ANNEXE"


def test_e6_multi_territoires():
    r = k.soldes_window(2027, "lorraine", "hiver")
    assert [w["territory_code"] for w in r["windows"]] == ["54", "55",
                                                           "57", "88"]
    assert all(w["start"] == "2027-01-04" for w in r["windows"])
    assert "Moselle (57)" in r["territory"]
    r = k.soldes_window(2027, "corse", "ete")
    assert [w["territory_code"] for w in r["windows"]] == ["2A", "2B"]


def test_e7_heure_pas_inventee():
    # l'article 1er dit 8 h ; l'annexe ne dit AUCUNE heure pour ses
    # dates locales — le module rend None, jamais une heure prêtée.
    w = k.soldes_window(2027, "974", "hiver")["windows"][0]
    assert w["start_time"] is None
    w = k.soldes_window(2027, M, "hiver")["windows"][0]
    assert w["start_time"] == "08:00"
    w = k.soldes_window(2020, "971", "hiver")["windows"][0]
    assert w["start_time"] is None


# ---------------------------------------------------------------- refus nommés
def test_f1_gate_2020():
    with pytest.raises(k.SoldesError) as e:
        k.soldes_window(2019, M)
    assert e.value.field == "year"
    assert "entre en vigueur le 1er janvier 2020" in e.value.message


def test_f2_pays_refuses_par_nom():
    for t in ("belgique", "luxembourg", "suisse", "québec",
              "royaume-uni", "etats-unis", "portugal", "brésil"):
        with pytest.raises(k.SoldesError) as e:
            k.soldes_window(2027, t)
        assert e.value.field == "territory", t
        assert "QUE l'arrete francais" in e.value.message, t


def test_f3_vocables_clos():
    with pytest.raises(k.SoldesError) as e:
        k.soldes_window(2027, M, "printemps")
    assert "hiver | ete | both" in e.value.expected
    with pytest.raises(k.SoldesError) as e:
        k.soldes_window(2027, "atlantide")
    assert e.value.field == "territory"
    with pytest.raises(k.SoldesError):
        k.soldes_window(2027, M, "hiver", as_of="pas une date")
    with pytest.raises(k.SoldesError):
        k.soldes_window("vingt-sept", M)


def test_f4_accents_et_alias():
    # le pluriel des alias voyage : « été » accentué foldingué,
    # « Moselle » par son nom, « 57 » par son code, « Metz » par sa
    # ville, et l'orthographe sans accent acceptée aussi.
    a = k.soldes_window(2027, "Moselle", "hiver")
    b = k.soldes_window(2027, "metz", "hiver")
    c = k.soldes_window(2027, "57", "hiver")
    assert a == b == c
    w = k.soldes_window(2027, M, "été")
    assert w["windows"][0]["season"] == "ete"


# ---------------------------------------------------------------- route live
def test_g1_endpoint_pinning():
    r = client.post("/api/v1/shop/soldes-window", json={
        "year": 2027, "territory": "metropole", "season": "hiver",
        "as_of": "2026-11-24"})
    assert r.status_code == 200
    body = r.json()
    assert body["windows"][0]["start"] == "2027-01-06"
    assert body["windows"][0]["days_to_start"] == 43
    assert body["sha256"]


def test_g2_refus_sur_le_route():
    r = client.post("/api/v1/shop/soldes-window", json={
        "year": 2027, "territory": "belgique"})
    assert r.status_code == 400
    err = r.json()["errors"][0]
    assert err["field"] == "territory"
    assert "liste CLOSE" in err["expected"]


def test_g3_both_territories_windows():
    r = client.post("/api/v1/shop/soldes-window", json={
        "year": 2026})
    assert r.status_code == 200
    wins = r.json()["windows"]
    assert [(w["season"], w["duration_weeks"]) for w in wins] == [
        ("hiver", 4), ("ete", 5)]  # le live du jour : hiver fini,
                                   # été porté à cinq par la canicule
