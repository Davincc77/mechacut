# -*- coding: utf-8 -*-
"""Bundle 95 — le routeur n'est plus sourd à l'orthographe de ses
propres mots. Douleur MESURÉE en prod le 23-nov-2026 (v1.16.0) :

  « c'est quoi un prix barré légal »  -> top-1 money_bogo (WRONG)
  « prix barré légal plus bas à 80 »  -> NO_MATCH (la question d'OCU)
  « le prix barré est-il vrai »       -> top-1 money_unitprice (WRONG)
  « recouvrement facture impayé »     -> le tag « impayé » du ledger
    était inatteignable par son propre spelling.

La cause est une classe, pas une phrase : route() tokenisait en
[^a-z0-9]+ — un é est un SÉPARATEUR, « barré » éclatait en « barr »,
« légal » en « l »+« gal ». 92 mots de tags portaient une écriture
(accent ou majuscule) que le tokenizer de la requête ne pouvait pas
produire. Scan du 23-nov : 74 mots accentés, 69 inatteignables sur
leur mot seul. Le radar ne voyait rien : ses variantes d'accents
étaient DÉACCENTUÉES — l'angle mort du corpus était le test lui-même.

Guérison : _nw() — NFKD + retrait des combining marks (stdlib, fermé)
+ les latins que NFKD ne décompose pas (œ æ ø đ ð ß et leurs doubles
de casse, table close) + minuscules — appliqué DES DEUX CÔTÉS
(requête, tags, purposes, noms). Un seul côté aurait décalé
l'autre : plier la requête sans plier la table aurait rendu « impayé »
orphelin de son propre tag.

Les golds sont calculés à la main (prix+barre+legal = 3×3 = 9), la
classe est rejouée par oracle structurel : chaque tag dont l'écriture
diffère de sa forme pliée, interrogé AVEC SA majuscule/son accent,
doit ramener son outil dans le top 5. Les leurre-restent-brefs sont
rejoués : un pli qui ferait prescrire une blague serait une douleur
de plus, pas de moins.
"""
import re

import pytest
from fastapi.testclient import TestClient

import main
import routing

client = TestClient(main.app)


# ---------------------------------------------------------------- pli pur
def test_pli_pureté():
    assert routing._nw("barré") == "barre"
    assert routing._nw("légal") == "legal"
    assert routing._nw("impayé") == "impaye"
    assert routing._nw("préçu") == "precu"
    assert routing._nw("preço") == "preco"
    assert routing._nw("œuvre") == "oeuvre"          # hors NFKD: table close
    assert routing._nw("straße") == "strasse"        # ß: table close
    assert routing._nw("CJEU") == "cjeu"
    assert routing._nw("kWh") == "kwh"


def test_pli_idempotence_et_stabilité():
    for w in ["barré", "ÆØÐ", "œuf", "ÜBER", "àêîõ"]:
        once = routing._nw(w)
        assert routing._nw(once) == once
    q = "le prix barré est-il vrai"
    assert routing.route(q) == routing.route(q)       # mêmes mots, mêmes octets


# ---------------------------------------------------------------- dictées
# Scores calculés à la main : chaque mot de tag plié vaut 3, un segment
# de nom 4, sous le plancher 4 le routeur refuse.
DICTEES = [
    ("c'est quoi un prix barré légal", "shop_discount_audit", 9),
    ("prix barré légal plus bas à 80", "shop_discount_audit", 9),
    ("le prix barré est-il vrai", "shop_discount_audit", 9),
    ("la promotion est-elle licite", "shop_discount_audit", 6),
    ("recouvrement facture impayé", "money_aging", 9),
    ("preço riscado é legal", "shop_discount_audit", 9),
    ("a promotion says 50% off the was price — is that legal "
     "under the omnibus rule", "shop_discount_audit", 14),
]


@pytest.mark.parametrize("q,want,score", DICTEES)
def test_dictées_accentuées(q, want, score):
    top = routing.route(q, top=3)
    assert top, "NO_MATCH sur une question humaine mesurée en prod"
    assert top[0]["tool"] == want, f"TOP1_WRONG: {top[0]['tool']} volé"
    assert top[0]["score"] >= score


# ---------------------------------------------------------------- classe
def test_classe_spelling_entière():
    """Oracle structurel : tout tag dont l'écriture diffère de sa
    forme normalisée (accent, majuscule) — et lui seul — est interrogé
    avec SA majuscule/son accent + un voisin de sa propre ligne. Son
    outil doit répondre. Le lot guérit la classe, pas sept phrases."""
    tested = 0
    for name, path, pack, purpose, tags in routing.TABLE:
        ws = tags.split()
        for w in ws:
            if w == routing._nw(w) and not any(c.isupper() for c in w):
                continue
            tested += 1
            sib = next((x for x in ws
                        if x.isascii() and x.islower() and len(x) >= 4), "")
            got = [t["tool"] for t in routing.route(w + " " + sib, top=5)]
            assert name in got, f"{name} muet sur son propre tag {w!r}"
    assert tested >= 90, ("la classe mesurée le 23-nov comptait 92 mots ; "
                          "un compte qui s'effondre cache un nettoyage "
                          "de TABLE non consign")


# ---------------------------------------------------------------- garde-fous
def test_leurres_ne_prescrivent_toujours_rien():
    for lk in ["raconte-moi une blague sur les soldes",
               "ne me prescris rien du tout aujourd'hui",
               "juste une question philosophique sans données"]:
        assert routing.route(lk) == [], f"OVERMATCH: {lk}"


def test_ailleurs_scène():
    # « scène » accenté devait éclater en « sc + ne » ; le rail
    # moovicut est plié comme le reste.
    assert routing.elsewhere("la scène de mon tournage")
    assert routing.elsewhere("storyboard")  # continuité historique


def test_table_propre():
    # Les blobs à virgules (formula_catalog, intent_reflect) étaient
    # des tokens morts — jamais atteignables par un split whitespace.
    # Un retour de virgule recrée la classe : garde statique. Le
    # mojibake (Ã, Â seuls) est de l'orthographe cassée, pas un mot —
    # SAUF chez text_decode : recopier la maladie (« cafÃ ») est le
    # spelling exact de l'humain qui cherche le remède, et le pli le
    # rend désormais joignable des deux côtés.
    for name, _p, _k, _pu, tags in routing.TABLE:
        for w in tags.split():
            assert "," not in w, f"tag à virgule morte chez {name}: {w!r}"
            if name == "text_decode":
                continue
            assert "Ã" not in w and "Â" not in w, \
                f"mojibake dans un tag chez {name}: {w!r}"


def test_route_endpoint_v17():
    r = client.get("/route", params={"q": "c'est quoi un prix barré légal",
                                     "top": "3"}).json()
    assert r["tools"] and r["tools"][0]["tool"] == "shop_discount_audit"
    assert r["query"] == "c'est quoi un prix barré légal"
    assert "sha256" in r
