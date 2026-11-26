# -*- coding: utf-8 -*-
"""AUTO-AUDIT corpus LATAM (26-11-2026) — la decouvrabilite des SCHEMAS
NUS. Peche du bench sur lui-meme : la proposition validate_cnpj a ete
jugee SUSPECT-DUPLICATE par la porte (verdict JUSTE — validate_taxid
connait le CNPJ depuis toujours), mais l'enquete a revele le vrai trou
: /route?q=cnpj repondait VIDE. Le mot vivait aux TAGS (poids 3) sous
le plancher 4 ; « iban » passait lui seul parce qu'il est dans le NOM.
Le patch n'a pas touche les poids (T5 — tries, rejetes par le banc) :
il etend la SURFACE DU NOM (SCHEME_NAMES -> nsegs) pour les outils
dont le domaine EST la liste fermee des schemas qu'ils valident.

Golds traces a la main AVANT le patch, rejoues en prod :
  q=cnpj  -> validate_taxid  (cnpj, cpf, siren, siret, nif, vat)
  q=isbn  -> id_checkdigit   (liste fermee du message 400 en prod)
  collision gardees hors chemin : « ca » (pli de « ça ») ne doit
  JAMAIS atteindre id_checkdigit seul — le stem de « cas » est « cas »,
  verifie avant patch, pas apres.
"""
from fastapi.testclient import TestClient

import main

ORIGIN = {"Origin": "https://mechacut.studio"}
client = TestClient(main.app)


def _top(q):
    tools = client.get("/route?q=" + q, headers=ORIGIN).json()["tools"]
    return tools[0]["tool"] if tools else None


def test_bare_scheme_words_now_route():
    # un mot-schema seul = l'equivalent d'un mot-NOM : il nomme, il
    # ne glisse pas. Chaque couple est la demande exacte ; un nom de
    # schema n'a pas a demander de l'aide.
    assert _top("cnpj") == "validate_taxid"
    assert _top("cpf") == "validate_taxid"
    assert _top("siren") == "validate_taxid"
    assert _top("isbn") == "id_checkdigit"
    assert _top("issn") == "id_checkdigit"


def test_iban_still_routes_untouched():
    # regression : la voie historique (mot dans le NOM) reste vraie,
    # le patch ne deplace rien d'existant.
    assert _top("iban") == "validate_iban"


def test_ca_ne_rameute_pas_id_checkdigit():
    # collision Gardee : « ca » est le pli de « ça » (FR) — si un
    # jour un schema se met a plier dessus, cet echec est le signal,
    # pas une corvée. « cas » plie « cas » : distinct.
    assert _top("ca") != "id_checkdigit"


def test_taxid_gold_replay_closes_the_proposal():
    # le dossier : la porte a refuse validate_cnpj comme doublon de
    # validate_taxid — le replay ci-dessous est la PREUVE nommee.
    # Gold 1 (CNPJ public LATAM) valide ; gold 2 invalide avec raison
    # ; gold 3 etait FAUX dans notre brouillon (ors traces a la main
    # par le banc : 60, pas 23) — l'endpoint avait raison.
    ok = client.post("/api/v1/validate/taxid",
                     json={"value": "02.012.862/0001-60", "kind": "cnpj"},
                     headers=ORIGIN).json()
    bad = client.post("/api/v1/validate/taxid",
                      json={"value": "02.012.862/0001-61", "kind": "cnpj"},
                      headers=ORIGIN).json()
    ours = client.post("/api/v1/validate/taxid",
                       json={"value": "52.502.963/1000-23", "kind": "cnpj"},
                       headers=ORIGIN).json()
    assert ok["valid"] is True and "mod-11" in ok["algorithm"]
    assert bad["valid"] is False
    assert ours["valid"] is False  # le gold du banc etait faux
