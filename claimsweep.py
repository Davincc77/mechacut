#!/usr/bin/env python3
"""claimsweep — la table fermee des marqueurs d'opinion, UN seul endroit.

Ne du CI de copie (scripts/copy-audit.py, ef168c3) monte a la porte sous
text_claimsweep (bundle 127_hermes, v1.50.0). Loi d'arbitrage du 26-11
(Vince, sur le SUSPECT-DUPLICATE 77dcc80b rendu par la porte) : la liste
est VERROUILLEE dans le contrat — une liste reglee par celui qu'elle juge
n'est plus une regle. Elle ne s'etend donc que par commit humain, jamais
par appelant, jamais par argument.

Semantique (golds G1-G6 traces main dans docs/proposals/
text_claimsweep.json) :
  - frappe insensible a la casse, sous-chaine litterale de la table ;
  - rend la forme canonique MINUSCULEE du marqueur, dans l'ordre de la
    premiere occurrence HORS citation, dedupliquee ;
  - exception citation : un marqueur PORTE par une voix citee
    ("...", "...", «...») n'est pas l'affirmation de l'auteur ;
    le meme marqueur ailleurs dans le texte frappe neanmoins ;
  - une phrase integralement subjective mais HORS table rend clean=true :
    le sweep ne devine pas l'opinion, il constate la table. C'est la
    these — le juge est verrouille, pas libre.
"""
import re

# ——— la table. Une seule. Copier ici = trahir copy-audit ; s'y tromper =
# deux regles pour un meme texte. Les familles sont documentees, pas codees
# (le rapport ne rend pas de famille : le contrat dit {clean, hits}).
MARKERS = [
    # adverbe d'auto-aveu devant un fait
    "honestly:", "honnêtement :", "honesto:", "stated honestly",
    "honestly-labelled",
    # quantifieur universel sans corpus nommé
    "everyone knows", "Nobody says", "Personne ne dit", "Ninguém diz",
    "personne ne compte", "ninguém conta",
    # garantie revendiquée hors mesure
    "the class the form can guarantee",
    "la seule classe que la forme garantit",
    "a única classe que a forma garante",
    "confidence honestly", "marquer honnêtement", "confiança com honestidade",
    # compteurs morts / placeholders retirés
    "{n_shipped}", "no paid clone", "clone payant enregistré",
    "clone pago registrado", "nothing splits", "rien ne se divise",
    "nada divide",
    # slot sur-cité
    "every regulator",
]

# Citations exemptees : trois graphies, couplees, non imbriquees. Rien
# d'autre — la grammaire est fermee, une apostrophe typographique n'ouvre
# pas une citation.
_CITE_RX = re.compile(
    r'"[^"\n]*"|"[^"\n]*"|«[^»\n]*»')


def _quote_spans(text):
    return [(m.start(), m.end()) for m in _CITE_RX.finditer(text)]


def sweep(text):
    """{text} -> {clean, hits} — la forme fermee du contrat porte."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    spans = _quote_spans(text)
    low = text.lower()
    firsts = {}
    for marker in MARKERS:
        m = marker.lower()
        start = 0
        while True:
            i = low.find(m, start)
            if i < 0:
                break
            inside = any(a <= i and i + len(m) <= b for a, b in spans)
            if not inside:
                firsts.setdefault(marker.lower(), i)
                break
            start = i + 1
    hits = [mk for mk, _ in sorted(firsts.items(), key=lambda kv: kv[1])]
    return {"clean": not hits, "hits": hits}
