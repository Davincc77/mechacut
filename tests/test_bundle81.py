# -*- coding: utf-8 -*-
"""Bundle 81 — l'audit des tags-CHIFFRES de la TABLE, guéri à la
SOURCE (règle de classe : un chiffre dans une requête est une
DONNÉE, jamais une intention).

DOULEUR (consignée au radar 11h14, pêchée par la BATTERIE live de
b78, pas par le corpus) : la dictée FR « la facture annonce
1 204,50 € de total… » partait chez csv_excel_display 8-7 sur les
tokens NUS « 1 » et « 50 » — les mêmes chiffres qui servaient de
tags. Le cycle précédent avait guéri LA PHRASE (re-dictée sans
monnaie morte) ; CE cycle guérit LE MOTEUR et LA TABLE :

  * route() DROPPE tout token entièrement numérique avant de
    scorer : les nombres de la requête ne votent plus pour
    aucune ligne, même quand une ligne les cite encore dans son
    purpose-documentaire (« + 1 000 000 → $1,000 »).
  * les tags nus numériques sont RENOMMÉS en composés ou retirés :
    rfc5545, eur400/eur600/gbp350/gbp520, semaine53, mod97,
    tweet (280 retiré), divisor/139 retiré, 404 retiré, 2027 retiré,
    15 retiré. Les trous de vocabulaire que le plancher a exposés
    sont BOUCHÉS AVEC DES MOTS (« under seat », « saw shown »),
    pas avec des chiffres — doctrine T6 rejouée.
  * la famille démonstrative FR « ce cet cette ces » rejoint
    STOP_FR (le trou : « es/etes » y étaient, « est » en reste
    VOLONTAIREMENT — fuseau EST ; « est-ce » matchait les pwords
    français du purpose de csv_excel_display).
  * garde STATIQUE : plus jamais un token purement numérique dans
    un champ tags de la TABLE.

Les deux échecs de dictée pêchés PENDANT ce lot (baggage 40x18x30
→ flight_comp ; openpyxl 1000000 → num_human) sont les trous de
vocabulaire que la guérison a exposés — ils sont VERROUILLÉS ici,
reproduits depuis les lignes du radar, pas inventés.
"""
import re

import routing


def test_no_bare_numeric_tags_anywhere_in_table():
    for row in routing.TABLE:
        for tok in row[4].split():
            assert not tok.isdigit(), (row[0], tok)

def test_numeric_query_tokens_never_vote():
    # la classe entière : des requêtes qui N'ÉTAIENT que des
    # chiffres pour un score ne sont plus que du silence honnête.
    assert routing.route("1") == []
    assert routing.route("50") == []
    assert routing.route("1 204 50") == []
    assert routing.route("400 600") == []

def test_old_broken_fr_dictation_is_healed_at_the_engine():
    # LA phrase d'avant la re-dictée de b78 — celle qui perdait
    # 8-7 chez csv_excel_display sur les tokens nus. Aujourd'hui
    # elle tombe sur le bon outil SANS retouche : le moteur a changé.
    hits = routing.route(
        "la facture annonce 1 204,50 € de total, est-ce que les "
        "lignes somment ?", top=2)
    assert hits and hits[0]["tool"] == "invoice_validate_totals", hits
    # et csv_excel_display ne doit plus rien devoir aux chiffres :
    for h in hits:
        assert not any(m.isdigit() for m in h["matched"])

def test_baggage_dictation_survives_numeric_drop():
    # trou de vocabulaire EXPOSÉ par la guérison (ligne du radar) :
    # « under the seat » ne vivait que sous le tag composé
    # « underseat » + le chiffre retiré. Bouché avec des mots.
    hits = routing.route("my bag is 40x18x30, flight 2027-11-02 "
                         "— free under the seat", top=3)
    assert hits[0]["tool"] == "money_baggage", hits

def test_excel_display_dictation_survives_numeric_drop():
    hits = routing.route("openpyxl read 1000000 but the human saw "
                         "$1,000", top=3)
    names = [h["tool"] for h in hits]
    assert "csv_excel_display" in names, names

def test_fr_demonstratives_stopped_est_kept_as_signal():
    assert routing._stem("ce") in routing.STOP_FR
    for w in ("ce", "cet", "cette", "ces"):
        assert w in routing.STOP_FR
    # « est » reste VOLONTAIREMENT hors stop-list (fuseau EST —
    # decision T6 documentée dans routing.py). Le verbe seul ne
    # route plus rien : 2 points de pword < plancher 4.
    assert "est" not in routing.STOP_FR
    assert routing.route("est") == []
    assert routing.route("ce") == []

def test_flight_comp_euro_pound_tiers_still_route():
    # les paliers de compensation sont des DONNÉES : le mot-tier
    # composé vote, pas le nombre nu.
    hits = routing.route("delayed flight 600 euro compensation")
    assert hits and hits[0]["tool"] == "money_flight_comp", hits

# le replay COMPLET du corpus radar contre la table neuve est déjà
# verrouillé par test_bundle72::test_radar_corpus_replays_locally —
# le lot qui touche le routeur n'a pas à doubler la garde, il doit
# la passer.
