# -*- coding: utf-8 -*-
"""Bundle 70 — T6 : le routeur ne prescrit plus des mots de grammaire.

Loi née du radar (docs/RADAR, scans 22h42 -> 03h31 du 23-nov) : les
trois OVERMATCH persistants matchaient UNIQUEMENT sur la grammaire
FR (matched ["moi","sur","les","de"], ["ne","pas","que","en"],
["pui","la","le","les"]) et la requête PT morte se faisait prescrire
money_baggage sur ["de","40"]. Douleur de classe documentée ailleurs :
laya #1453, README llm-router-plugins, autonomous-dev
INTENT-CLASSIFICATION, 9router #317.

Les attentes ci-dessous sont CALCULEES A LA MAIN depuis la TABLE
(poids NOM 6 / TAG 3 / PURPOSE 2, plancher T6 = 6), jamais recopiées
de la sortie du module.
"""
import routing


def test_t6_floor_published_and_enforced():
    assert routing.CONF_FLOOR == 4
    # toute liste renvoyée est au-dessus du plancher, par construction
    for q in ("chart", "dirty csv", "json diff",
              "mon vol est arrive avec 3 h 20 de retard",
              "raconte-moi une blague sur les bases de donnees"):
        for hit in routing.route(q):
            assert hit["score"] >= routing.CONF_FLOOR


def test_fr_grammar_only_query_refuses_by_name():
    # matching des 3 lignes du radar 03:30 : chaque token contenu est
    # soit STOP_FR brut, soit absent de tout vocabulaire (blague, base,
    # vie, gens — vérifié par l'audit collisions du cycle) :
    assert routing.route(
        "raconte-moi une blague sur les bases de donnees") == []
    assert routing.route(
        "je ne sais pas encore ce que je veux calculer, "
        "parlons-en") == []
    assert routing.route(
        "435 articles et puis la vie, le temps, les gens") == []


def test_pt_dead_query_no_longer_prescribed():
    # avant T6 : money_baggage score 5 sur ["de","40"] — prescription
    # de bruit. Le trou PT (loja/vendeu/manha absents des tags) reste
    # OUVERT et honnête : liste vide, pas une fausse aiguille.
    assert routing.route("loja tinha 435, vendeu 35 de manha, "
                         "40% do resto a tarde, quantos restam") == []


def test_raw_stop_saves_mois_from_moi():
    # la collision mesurée : _stem("mois") == _stem("moi") == "moi".
    # STOP teste le token BRUT — le pronom meurt, le signal FR des
    # dates survit à la porte d'entrée.
    assert routing._stem("mois") == "moi"
    assert "moi" in routing.STOP and "mois" not in routing.STOP
    # et le STOP à 3 langues est bien un UNION sans trou :
    assert routing.STOP == (routing.STOP_EN | routing.STOP_FR
                            | routing.STOP_PT)
    for w in ("est", "temps", "combien", "retard"):
        assert w not in routing.STOP  # signaux, pas grammaire


def test_one_word_name_queries_survive_the_floor():
    # calcul main : "chart" -> tige "chart" dans nsegs de
    # chart_from_data {chart, from, data} -> poids NOM 4 = plancher
    # pile : nommer n'est pas glisser.
    hits = routing.route("chart")
    assert hits and hits[0]["tool"] == "chart_from_data"
    assert hits[0]["score"] == 4
    # "batch" : un seul mot, mais c'EST le nom de l'outil -> 4.
    hits = routing.route("batch")
    assert hits and hits[0]["tool"] == "batch"
    # "json diff" : deux noms {json, diff} -> 4 + 4 = 8.
    hits = routing.route("json diff")
    assert hits[0]["tool"] == "json_diff" and hits[0]["score"] == 8
    # "csv" : le mot NOMME une famille — chaque outil csv_* marque 4
    # (cinq dans la TABLE : fix, types, join, diff, money_columns),
    # le vide n'est jamais la réponse à un mot qui nomme un outil.
    fam = {h["tool"] for h in routing.route("csv")}
    assert {"csv_fix", "csv_types", "csv_join"} <= fam
    assert all(h["score"] == 4 for h in routing.route("csv"))
    assert all(n.startswith("csv_") for n in fam)
    # un seul mot TAG (poids 3) ne précrit pas : "kwh" seul = refus.
    assert routing.route("kwh") == []


def test_vocab_holes_surfaced_by_the_floor_are_filled():
    # T6 a pêché deux trous de vocabulaire que le bruit portait avant
    # (lignes dictées par tests/test_bundle53 + probe du cycle) :
    hits = routing.route("a partir de quantos kwh o plano b e mais "
                         "barato")
    assert hits and hits[0]["path"] == "/api/v1/money/crossover"
    # FR dates : « rappel » était absent des tags (mois y est depuis
    # v1.1.0, mais il ne portait que 3 seul sous T6).
    hits = routing.route("rappel tous les mois le 3")
    assert hits and hits[0]["tool"] == "date_recurrence"


def test_radar_dictation_lines_keep_their_needle():
    # les vraies douleurs ne glissent pas sous le plancher : chaque
    #want du corpus radar garde son outil dans le top 3.
    lines = [
        ("magasin 435 articles, 35 vendus le matin, 40 % du reste "
         "l'après-midi, combien restent", "recipe_shop_reste"),
        ("partage 3829 : le premier recoit 2/5, le second 1/6 du "
         "reste", "recipe_partage_reste"),
        ("mon vol est arrive avec 3 h 20 de retard le 1er nov. 2027, "
         "que me doit la table EU", "money_flight_comp"),
        ("my bag is 40x18x30, flight 2027-11-02 — free under the "
         "seat", "money_baggage"),
        ("avant d'ouvrir ce CSV dans Excel, quelles colonnes perdent "
         "leurs zeros", "csv_excel_damage"),
        ("openpyxl read 1000000 but the human saw $1,000",
         "csv_excel_display"),
        ("tarif A 0,25 €/kWh + 0,60 par jour, B 0,27 + 0,45 — à "
         "partir de combien de kWh A gagne", "money_crossover"),
    ]
    for text, needle in lines:
        names = [h["tool"] for h in routing.route(text, top=3)]
        assert needle in names, (text[:40], names)


def test_api_route_publishes_the_floor(client=None):
    from fastapi.testclient import TestClient
    import main as main_mod
    c = TestClient(main_mod.app)
    r = c.get("/route", params={"q": "raconte-moi une blague sur les "
                                     "bases de donnees"})
    assert r.status_code == 200
    b = r.json()
    assert b["tools"] == []
    assert b["confidence_floor"] == 4
    # l'ancien contrat survit intégralement (additif seulement) :
    for key in ("query", "tools", "note", "sha256"):
        assert key in b
    r2 = c.get("/route", params={"q": "chart"})
    assert r2.json()["tools"][0]["tool"] == "chart_from_data"
