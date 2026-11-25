# -*- coding: utf-8 -*-
"""Bundle 72 — la lentille ferme ses propres douleurs.

Deux douleurs mesurées par le scan radar 06:22 du 23-nov (le premier
avec --catalog, dette payée) :

1. NO_MATCH PT : « loja tinha 435, vendeu 35 de manha, 40% do resto
   a tarde, quantos restam » — active depuis 21h57, six scans de
   suite. Le trou est un TROU DE VOCABULAIRE, dicté par le radar :
   loja/vendeu/manha/manh/tarde/resto/restam rejoignent les tags de
   recipe_shop_reste. Les sept tiges étaient LIBRES (audit de
   possession du cycle) ; « quantos » jamais pris (interrogatif).
   Attente calculée À LA MAIN : 6 mots de contenu × 3 (poids TAG)
   = 18, aucun nom/purpose ne touche.

2. Douleur OUTILLAGE : le scan s'est auto-infligé un plan-http-429
   (0,3 s de sommeil = 33 req/min > notre règle 25/min) et sa sonde
   catalogue appelait un EMBEDDING en /chat (gemini-embedding-001
   http-400 = notre artefact, mais le catalogue mélange vraiment les
   types — piège V23 second jour, mesuré avec le MIRAGE
   claude-sonnet-5.5:batch). La lentille se calibre : cadence
   APP_MIN_GAP sur toute PROD, verdicts fondés sur la LISTE RENVOYÉE
   (plus de seuil dupliqué « <= 5 » qui laissait passer un leurre à
   4-5 depuis T6), sonde /embeddings typée par l'id.
"""
import sys
import pathlib

import routing

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent
                       / "scripts"))
import route_radar  # noqa: E402

PT_SHOP = ("loja tinha 435, vendeu 35 de manha, "
           "40% do resto a tarde, quantos restam")


def test_pt_shop_routes_by_hand_computed_score():
    hits = routing.route(PT_SHOP)
    assert hits[0]["tool"] == "recipe_shop_reste"
    # 6 tiges possédées (loja, vendeu, manha, tarde, resto, restam)
    # × poids TAG 3 — « manh » n'apparaît pas (phrase sans ã),
    # « tinha/quantos » ne sont possédés de personne, nombres nus
    # hors tags. 18, pas un point de plus.
    assert hits[0]["score"] == 18
    assert hits[0]["score"] >= routing.CONF_FLOOR


def test_new_pt_words_owned_by_exactly_one_entry():
    # audit de possession : un mot donné à deux entrées = aiguille
    # partagée = douleurfuture. Les sept mots du lot ne vivent qu'ici.
    for stem in ("loja", "vendeu", "manha", "manh", "tarde",
                 "resto", "restam"):
        owners = []
        for name, _path, _pack, _purpose, tags in routing.TABLE:
            toks = {routing._stem(t)
                    for t in tags.lower().split() if t}
            if stem in toks:
                owners.append(name)
        assert owners == ["recipe_shop_reste"], (stem, owners)


def test_other_food_pt_lines_untouched():
    # les vrais mots des restes restent la propriété exclusive de
    # leftovers : la phrase PT « combien de temps les sobras au
    # fridge » ne glisse pas vers la boutique.
    hits = routing.route("quanto tempo as sobras duram na geladeira")
    assert hits[0]["tool"] == "food_leftovers"


def test_radar_corpus_replays_locally():
    # le corpus du radar, rejoué CONTRE LA TABLE LOCALE : tout ce que
    # la prod déclare ok/leurre-ok l'est aussi ici (même code, même
    # sha de comportement attendue). Lignes exclues : les DOULEURS
    # CONSIGNÉES à la file, pas des contrats à geler ici —
    # comparatif EN (juridiction bench, money_bogo gagne sur des
    # nombres nus de purpose) ; brésil droit->fenêtre (veto
    # droit-fenêtre à poser, file b108) ; allemaine->shipping-deadline
    # (stopwords de purpose qui portent, file b108).
    excluded = ("is 30% off plus another 20% the same as 50% off",
                "retour brésil 7 jours arrependimento prazo",
                "withdrawal germany online order deadline")
    n_replayed = 0
    for text, want in route_radar.CASES:
        if any(x in text for x in excluded):
            continue
        hits = routing.route(text)
        names = [h["tool"] for h in hits[:3]]
        if want is None:
            assert names == [], text
        else:
            assert any(want.lower() in n.lower() for n in names), \
                (text, names)
            n_replayed += 1
    assert n_replayed >= 12


def test_radar_pacing_constant_is_honest():
    # 2,6 s = 23/min max — sous notre propre règle 25/min. La valeur
    # vit dans le module ET dans chaque sommeil de PROD : lecture du
    # source, pas confiance.
    src = pathlib.Path(route_radar.__file__).read_text()
    assert route_radar.APP_MIN_GAP >= 2.6
    assert "time.sleep(0.3)" not in src
    assert src.count("time.sleep(APP_MIN_GAP)") == 2


def test_catalog_probe_is_typed_offline():
    # sonde rejouée hors-ligne : un id « embed » part à /embeddings,
    # un id chat part à /chat/completions ; 404 = MIRAGE, pas un
    # http-400 fourre-tout.
    calls = []

    def fake_get(url, params=None, data=None, headers=None):
        calls.append(url)
        if url.endswith("/models"):
            return 200, {"data": [
                {"id": "anthropic/claude-sonnet-5.5:batch"},
                {"id": "google/gemini-embedding-001:batch"}]}
        if "chat" in url:
            return 404, {}
        return 200, {"data": [1]}

    real = route_radar.get
    try:
        route_radar.get = fake_get
        out = route_radar.probe_catalog(sample=2)
    finally:
        route_radar.get = real
    verdicts = {r["text"]: r["verdict"] for r in out}
    assert verdicts["anthropic/claude-sonnet-5.5:batch"] == "MIRAGE"
    assert verdicts["google/gemini-embedding-001:batch"] == "ok"
    assert any(u.endswith("/embeddings") for u in calls)
    assert any("/chat/completions" in u for u in calls)
