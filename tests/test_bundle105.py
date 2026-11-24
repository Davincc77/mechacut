# -*- coding: utf-8 -*-
"""bundle105 — /shop/soldes-be : la grammaire belge, clause du dimanche,
attente d'un mois, reports corona 2020-2021. Golds tracés À LA MAIN sur
l'oracle g105 (stdlib, écrit AVANT le module) et les verbatims SPF/
Moniteur rejoués le 24-11-2026 — jamais recopiés du module.

Les vecteurs historiques VÉCUS : clause d'hiver 2016 (3 janv = dimanche)
et clause d'été 2018 (1er juil = dimanche) ; la fiche de file affirmait
« été 2024 » — le calendrier l'a réfutée avant build (1er juillet 2024 :
lundi). Le cas double 2021 : la clause aurait donné le samedi 2 janvier,
l'AR du 10-12-2020 l'ÉCRASE au lundi 4 « pour limiter les mouvements de
foule d'un samedi », et la loi du 02-02-2021 prolonge jusqu'au 15
février inclus — 43 jours, le seul hiver de la table où clause fired ET
overruled voyagent ensemble : une clause écartée n'est pas effacée.
"""
import json

import pytest

import soldesbekit as SB


def W(year, season, as_of=None, **kw):
    out = SB.soldes_be(year, season=season, as_of=as_of, **kw)
    return out["windows"][0]


# ---------------------------------------------------------------- les vecteurs
def test_hiver2027_clause_tiree():
    w = W(2027, "hiver")
    assert w["start"] == "2027-01-02"
    assert w["start_weekday"] == "Saturday"
    assert w["end"] == "2027-01-31"
    assert w["length_days"] == 30
    assert w["start_basis"] == "CLAUSE_DIMANCHE"
    assert w["clause"]["anchor"] == "2027-01-03"
    assert w["clause"]["anchor_weekday"] == "Sunday"
    assert w["clause"]["fired"] is True
    assert w["clause"]["overruled_by_derogation"] is False
    assert w["waiting"] == {
        "start": "2026-12-02", "end": "2027-01-01", "length_days": 31,
        "basis": "SPF_ENUMEREE",
        "text": "du 2 décembre au 1er janvier"}
    assert w["derogations_applied"] == []


def test_attente2027_borne_sudinfo_en_flag():
    # la douleur pêchée : sudinfo (24-nov) écrivait l'attente « débutera
    # le 3 décembre » — le SPF la nomme « du 2 décembre au 1er janvier »
    # pour cause de 3 janvier dimanche. Le tool rend la borne du texte.
    w = W(2027, "hiver")
    assert w["waiting"]["start"] == "2026-12-02"
    assert w["waiting"]["start"] != "2026-12-03"


def test_hiver2016_clause_vecue():
    w = W(2016, "hiver")
    assert (w["start"], w["end"], w["length_days"]) == \
        ("2016-01-02", "2016-01-31", 30)
    assert w["waiting"] == {
        "start": "2015-12-02", "end": "2016-01-01", "length_days": 31,
        "basis": "SPF_ENUMEREE",
        "text": "du 2 décembre au 1er janvier"}


def test_ete2018_clause_vecue_divergence_nommee():
    w = W(2018, "ete")
    assert (w["start"], w["end"], w["length_days"]) == \
        ("2018-06-30", "2018-07-31", 32)
    assert w["clause"]["fired"] is True
    assert w["clause"]["anchor_weekday"] == "Sunday"
    wai = w["waiting"]
    assert wai["start"] == "2018-05-31"
    assert wai["end"] == "2018-06-29"
    assert wai["length_days"] == 30
    # LA divergence du jour : la formule générique (même quantième au
    # mois précédent) donnerait le 30 mai ; le texte SPF nomme le 31.
    d = wai["formula_divergence"]
    assert d["formula_generic_start"] == "2018-05-30"
    assert d["named_text_start"] == "2018-05-31"
    assert "gouverne" in d["rule"]


def test_ete2018_pas_de_divergence_normale():
    assert "formula_divergence" not in W(2026, "ete")["waiting"]


def test_ete2029_prochaine_clause():
    w = W(2029, "ete")
    assert (w["start"], w["end"], w["length_days"]) == \
        ("2029-06-30", "2029-07-31", 32)
    assert w["waiting"]["start"] == "2029-05-31"


def test_ete2024_la_fiche_corrigee_par_le_calendrier():
    # la mémoire disait « 1er juillet 2024 dimanche » — c'était LUNDI.
    w = W(2024, "ete")
    assert w["clause"]["anchor_weekday"] == "Monday"
    assert w["clause"]["fired"] is False
    assert w["start"] == "2024-07-01"


def test_hiver2021_double_derogation():
    w = W(2021, "hiver")
    assert w["start"] == "2021-01-04"
    assert w["start_weekday"] == "Monday"
    assert w["end"] == "2021-02-15"
    assert w["length_days"] == 43
    assert w["start_basis"] == "REPORT_AR_2020-12-10"
    assert w["end_basis"] == "PROLONGATION_LOI_2021-02-02"
    assert w["clause"]["fired"] is True
    assert w["clause"]["overruled_by_derogation"] is True
    assert w["waiting"] == {
        "start": "2020-12-04", "end": "2021-01-03", "length_days": 31,
        "basis": "DERIVEE_DU_REPORT_AR_2020-12-10",
        "text": "du 4 décembre au 3 janvier (suite du report au lundi : "
                "« le premier jour des soldes qui détermine le début de "
                "la période d'attente »)"}
    d = w["derogations_applied"]
    assert len(d) == 2
    assert "4 janvier 2021" in d[0]["verbatim"]
    assert "15 février 2021 inclus" in d[1]["verbatim"]
    assert "2020044416" in d[0]["ref"]
    assert "2021040390" in d[1]["ref"]


def test_ete2020_report_en_aout():
    w = W(2020, "ete")
    assert (w["start"], w["end"], w["length_days"]) == \
        ("2020-08-01", "2020-08-31", 31)
    assert w["start_basis"] == "REPORT_LOI_2020-05-27"
    assert w["clause"]["fired"] is False  # 1er juillet 2020 = mercredi
    assert w["clause"]["anchor_weekday"] == "Wednesday"
    assert w["waiting"] == {
        "start": "2020-07-01", "end": "2020-07-31", "length_days": 31,
        "basis": "DERIVEE_DU_REPORT_LOI_2020-05-27",
        "text": "durant le mois précédant les soldes, comme de coutume "
                "(lesoir, 13-05-2020) : du 1er au 31 juillet"}
    assert "1er août au 31 août" in w["derogations_applied"][0]["verbatim"]


def test_hiver2020_normal_malgre_lannee():
    # l'année 2020 ne dérobe QUE l'été ; l'hiver 2020 (3 janv = vendredi)
    # reste au droit commun — la dérogation voyage PAR SAISON, pas par an.
    w = W(2020, "hiver")
    assert (w["start"], w["end"], w["length_days"]) == \
        ("2020-01-03", "2020-01-31", 29)
    assert w["derogations_applied"] == []


def test_droit_commun_hiver_et_ete():
    w = W(2025, "hiver")
    assert (w["start"], w["end"]) == ("2025-01-03", "2025-01-31")
    assert w["waiting"]["start"] == "2024-12-03"
    assert w["waiting"]["text"] == "du 3 décembre au 2 janvier inclus"
    e = W(2026, "ete")
    assert (e["start"], e["end"], e["length_days"]) == \
        ("2026-07-01", "2026-07-31", 31)
    assert e["waiting"]["start"] == "2026-06-01"
    assert e["waiting"]["text"] == "du 1er juin au 30 juin inclus"


def test_both_deux_fenetres_ordonnees():
    out = SB.soldes_be(2027)
    assert [w["season"] for w in out["windows"]] == ["hiver", "ete"]
    assert out["windows"][1]["start"] == "2027-07-01"


# ---------------------------------------------------------------- les bornes
@pytest.mark.parametrize("as_of,status,field,value", [
    ("2026-12-01", "UPCOMING", "days_to_waiting", 1),
    ("2026-12-02", "IN_ATTENTE", "days_left_in_waiting", 31),
    ("2027-01-01", "IN_ATTENTE", "days_left_in_waiting", 1),
    ("2027-01-02", "IN_PROGRESS", "days_left", 29),
    ("2027-01-31", "IN_PROGRESS", "days_left", 0),
    ("2027-02-01", "ENDED", "days_since_end", 1),
])
def test_quatre_phases_bornées(as_of, status, field, value):
    w = W(2027, "hiver", as_of=as_of)
    assert w["status"] == status
    assert w[field] == value


def test_vecteur_du_jour_compte_les_jours_de_la_presse():
    w = W(2027, "hiver", as_of="2026-11-24")
    assert w["status"] == "UPCOMING"
    assert w["days_to_start"] == 39
    assert w["days_to_waiting"] == 8


def test_sans_as_of_aucun_statut():
    w = W(2027, "hiver")
    assert "status" not in w and "days_to_start" not in w


# ---------------------------------------------------------------- le gate
def test_hiver2014_refuse_ete2014_passe():
    with pytest.raises(SB.SoldesBeError) as e:
        SB.soldes_be(2014, season="hiver")
    assert e.value.field == "year"
    assert "31-05-2014" in e.value.message
    assert "14-07-1991" in e.value.message
    assert "15 novembre" in e.value.message  # l'ancien régime porte son fait
    w = W(2014, "ete")
    assert w["start"] == "2014-07-01"


def test_annees_avant_2014_refusees():
    for y in (1991, 2013):
        with pytest.raises(SB.SoldesBeError) as e:
            SB.soldes_be(y, season="ete")
        assert e.value.field == "year"
    with pytest.raises(SB.SoldesBeError):
        SB.soldes_be(2013)  # both, hiver en tete -> refus
    with pytest.raises(SB.SoldesBeError) as e:
        SB.soldes_be(10000, season="hiver")
    assert e.value.expected == "year <= 9999"


def test_year_non_entier():
    with pytest.raises(SB.SoldesBeError) as e:
        SB.soldes_be("2027x")
    assert e.value.field == "year"


# ------------------------------------------------- refus par nom portant fait
def test_france_refusee_renvoie_chez_la_soeur():
    with pytest.raises(SB.SoldesBeError) as e:
        SB.soldes_be(2027, territory="france")
    m = e.value.message
    assert "27-05-2019" in m and "/shop/soldes-window" in m
    assert e.value.field == "territory"


def test_luxembourg_refuse_porte_son_fait():
    with pytest.raises(SB.SoldesBeError) as e:
        SB.soldes_be(2027, territory="Luxembourg")
    m = e.value.message
    assert "chaque ann" in m.lower() or "CHAQUE ANNEE" in m
    assert "23-12-2016" in m
    assert "/shop/soldes-lu" in m


@pytest.mark.parametrize("t", ["suisse", "Suisse romande", "québec",
                               "Canada", "ontario", "england", "united "
                               "kingdom", "espagne", "portugal", "brasil",
                               "états-unis", "germany", "sénégal"])
def test_etrangers_generiques_refuses(t):
    with pytest.raises(SB.SoldesBeError) as e:
        SB.soldes_be(2027, territory=t)
    assert e.value.field == "territory"


@pytest.mark.parametrize("t", ["belgique", "Belgique", "belgië", "belgium",
                               "be", "bruxelles", "Bruxelles",
                               "royaume de belgique"])
def test_belgique_accepte_par_aliases(t):
    out = SB.soldes_be(2027, territory=t)
    assert out["territory"].startswith("Belgique")


def test_territoire_inconnu_refuse():
    with pytest.raises(SB.SoldesBeError) as e:
        SB.soldes_be(2027, territory="atlantide")
    assert "liste closee" in e.value.expected


# ---------------------------------------------------------------- saisons
@pytest.mark.parametrize("raw,want", [
    ("hiver", "hiver"), ("Hiver", "hiver"), ("winter", "hiver"),
    ("hivernale", "hiver"), ("inverno", "hiver"),
    ("ete", "ete"), ("été", "ete"), ("Été", "ete"), ("summer", "ete"),
    ("estival", "ete"), ("verao", "ete"), ("zomer", "ete"),
])
def test_saison_lexique_ferme(raw, want):
    assert W(2027, raw)["season"] == want


def test_saison_inconnue():
    with pytest.raises(SB.SoldesBeError) as e:
        SB.soldes_be(2027, season="printemps")
    assert e.value.field == "season"


def test_as_of_mal_forme():
    with pytest.raises(SB.SoldesBeError) as e:
        SB.soldes_be(2027, as_of="3 janvier 2027")
    assert e.value.field == "as_of"
    assert "YYYY-MM-DD" in e.value.expected


# ---------------------------------------------------------------- corpus légal
def test_verbatims_voyagent():
    out = SB.soldes_be(2027)
    assert "Schlussverkauf" in out["rule"]
    assert "prend cours le 2 janvier" in out["rule"]
    assert "supérieure à un mois" in out["roi_rule"]  # pourquoi une LOI
    assert "période d'un mois qui précède" in out["waiting_rule"]["statute"]
    assert "du 3 décembre au 2 janvier inclus" in \
        out["waiting_rule"]["hiver"]
    assert "du 31 mai au 29 juin" in out["waiting_rule"]["ete"]
    assert "30 jours" in out["eligibility"]
    assert "maroquinerie" in out["prohibitions_during_waiting"] \
        ["sectors_and_acts"]
    assert "quatre jours" in out["prohibitions_during_waiting"] \
        ["braderie_exception"]
    assert "liquidation" in out["prohibitions_during_waiting"]["liquidation"]
    assert "20-05-2026" in out["regime_conflict"]  # CE, le tool date
    assert out["table_version"] == \
        "cde-coordonne-2026-01-21 + spf-2026-07-27"
    assert "31 janvier inclus" in out["spf"]["hiver"]
    assert "le 30 juin" in out["spf"]["ete"]


def test_pas_dannexe_territoriale_est_la_promesse():
    # la différence structurale avec la sœur française, déclarée :
    assert "annexe" in SB.soldes_be(2027)["territory"]


def test_end_inclus_partout():
    for y, s in [(2027, "hiver"), (2018, "ete"), (2021, "hiver"),
                 (2020, "ete"), (2015, "hiver")]:
        assert W(y, s)["end_included"] is True


def test_determinisme_byte_a_byte():
    from main import canon
    a = SB.soldes_be(2021, season="hiver", as_of="2021-01-04")
    b = SB.soldes_be(2021, season="hiver", as_of="2021-01-04")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert canon(a) == canon(b)
    # le premier jour des soldes 2021 est IN_PROGRESS jours_left 42
    assert a["windows"][0]["status"] == "IN_PROGRESS"
    assert a["windows"][0]["days_left"] == 42


# ---------------------------------------------------------------- route
from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402

client = TestClient(main.app)
main.RATE_LIMIT = 10**9


def _top(q):
    return [t["tool"] for t in
            client.get("/route", params={"q": q}).json()["tools"]]


def test_j1_aiguilles_soldes_be_x3():
    for q in ("quand commencent les soldes en belgique",
              "soldes belgique 2027 samedi 2 ou dimanche 3 janvier",
              "période d'attente soldes belgique 2 décembre 1er janvier",
              "winter sales belgium 2027 january 2 sunday clause",
              "saldos na bélgica 2027 janeiro período de espera",
              "wanneer zijn de solden 2027 in belgië"):
        assert _top(q)[0] == "shop_soldes_be", q


def test_j2_frontiere_juree_sans_pays_rest_chez_la_soeur():
    # « soldes 2027 » sans pays : TIÈGE par ordre TABLE, la sœur
    # française passe AVANT — règle déclarée, pas un pile ou face.
    assert _top("quand commencent les soldes d'hiver 2027")[0] == \
        "shop_soldes_window"
    # « france » nominatif ne vole rien à la sœur, ne réveille pas BE
    assert _top("les soldes d'hiver 2027 en france c'est le 6 ou le 13")[0] \
        == "shop_soldes_window"


def test_j3_soeur_et_gardes_gardent_leurs_aiguilles():
    # le veto b103 de la sœur reste intact : nommer la Belgique tue la
    # FENETRE FR (c'est l''outil BE qui répond, plus jamais un 400
    # promis par le routeur).
    names = _top("quand commencent les soldes en belgique")
    assert "shop_soldes_window" not in names
    # luxembourg : RIEN des soldes ne doit être prescrit (range 2 en
    # file, spec par acte annuel non jouée)
    names = _top("les soldes d'hiver au luxembourg 2027")
    assert "shop_soldes_be" not in names and "shop_soldes_window" not in names


def test_j4_leurres_meurent():
    for q in ("blague sur le calendrier des soldes belges",
              "quanto começam os saldos em portugal",
              "tell me a joke about the french sales calendar"):
        names = _top(q)
        assert "shop_soldes_be" not in names and \
            "shop_soldes_window" not in names, q


# ------------------------------------------------------------ endpoints
def test_g1_endpoint_2027_sha_et_attente():
    r = client.post("/api/v1/shop/soldes-be", json={
        "year": 2027, "season": "hiver", "as_of": "2026-11-24"})
    assert r.status_code == 200
    d = r.json()
    w = d["windows"][0]
    assert w["start"] == "2027-01-02"
    assert w["waiting"]["start"] == "2026-12-02"
    assert w["waiting"]["end"] == "2027-01-01"
    assert w["days_to_start"] == 39
    assert d["sha256"]


def test_g2_france_refusee_sur_le_route():
    r = client.post("/api/v1/shop/soldes-be", json={
        "year": 2027, "territory": "france"})
    assert r.status_code == 400
    err = r.json()["errors"][0]
    assert err["field"] == "territory"
    assert "/shop/soldes-window" in err["message"]


def test_g3_hiver2021_double_derogation_vivante():
    r = client.post("/api/v1/shop/soldes-be", json={
        "year": 2021, "season": "hiver"})
    w = r.json()["windows"][0]
    assert w["start"] == "2021-01-04" and w["end"] == "2021-02-15"
    assert w["clause"]["fired"] is True
    assert w["clause"]["overruled_by_derogation"] is True
    assert len(w["derogations_applied"]) == 2


def test_g4_400_porte_field_et_expected():
    r = client.post("/api/v1/shop/soldes-be", json={
        "year": 2027, "season": "printemps"})
    assert r.status_code == 400
    err = r.json()["errors"][0]
    assert err["field"] == "season"
    assert "hiver | ete | both" in err["expected"]


def test_g5_extra_field_refuse_pyd():
    r = client.post("/api/v1/shop/soldes-be", json={
        "year": 2027, "joker": True})
    assert r.status_code == 400


def test_g6_mcp_outille_et_lance():
    names = [t["name"] for t in client.post(
        "/mcp", json={"jsonrpc": "2.0", "id": 1,
                      "method": "tools/list"}).json()["result"]["tools"]]
    assert "shop_soldes_be" in names
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2,
                                  "method": "tools/call",
                                  "params": {"name": "shop_soldes_be",
                                             "arguments": {"year": 2016,
                                                           "season":
                                                               "hiver"}}})
    import json as _j
    payload = _j.loads(
        r.json()["result"]["content"][0]["text"])
    assert payload["windows"][0]["start"] == "2016-01-02"


def test_golden_contient_onze_nouvelles_pin():
    import json
    g = json.load(open("golden.json", encoding="utf-8"))
    pins = list(g["pins"].keys()) if "pins" in g else list(g.keys())
    for name in ("shop_soldesbe_hiver2027_clause_pin",
                 "shop_soldesbe_attente2027_bornes_pin",
                 "shop_soldesbe_hiver2021_double_pin",
                 "shop_soldesbe_ete2020_report_pin",
                 "shop_soldesbe_ete2018_clause_pin",
                 "shop_soldesbe_hiver2016_pin",
                 "shop_soldesbe_gate2014_hiver_refuse",
                 "shop_soldesbe_france_refuse",
                 "shop_soldesbe_luxembourg_refuse",
                 "shop_soldesbe_badseason_refuse",
                 "shop_soldesbe_future2029_clause_pin"):
        assert name in pins, name
