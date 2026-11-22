# -*- coding: utf-8 -*-
"""routeur — matcher de grammaire fermée de l'annuaire (S3,
docs/ROUTER-SPEC.md).

L'annuaire appelle et applique : quand le texte matche la grammaire
d'une fiche, le serveur extrait les créneaux (verbatim) et la chaîne
tourne — ZÉRO LM, le sha du serveur EST la réponse. Hors cadre :
refus NOMMÉ + prompt à remplir, jamais un nombre deviné (règle R3).

Grammaire gelée, une LISTE de motifs par créneau (alternatives
strictes, dictées par le radar 22-11 : FR v16 + EN + PT + la forme
compacte « -25 % puis -20 % sur 81,90 — prix final »). Les motifs
FR naissent des gabarits bench/gen16.py ; EN/PT de la vie réelle
sondée (docs/RADAR/latest.json 20h28, 22-11 — incident consigné :
« is 30% off plus another 20%… », « split 3829: first gets 2/5… »).
Pluriel des valeurs distinctes pour un créneau = AMBIGU (refus
nommé), pas de premier-venu. La virgule décimale du prix est
pliée au point parce que la fiche l'accepte aux DEUX formes : ce
n'est pas une interprétation, c'est une notation.
"""
import re

TRAD = {
    "shop-reste": {
        "total": [r"(\d+)\s+articles", r"(\d+)\s+items",
                  r"tinha\s+(\d+)"],
        "sold_morning": [r"(\d+)\s+sont vendus", r"(\d+)\s+(?:sold|vendeu)",
                         r"vendeu\s+(\d+)"],
        "pct_afternoon": [r"(\d+)\s*%\s*du\s+reste",
                          r"(\d+)\s*%\s+of\s+the\s+rest",
                          r"(\d+)\s*%\s+do\s+resto"],
    },
    "partage-reste": {
        "total": [r"partage\s+(\d+)", r"split\s+(\d+)"],
        "first_part": [r"reçoit\s+(\d+/\d+)", r"recebe\s+(\d+/\d+)",
                       r"gets\s+(\d+/\d+)"],
        "second_of_rest": [r"(\d+/\d+)\s+du\s+reste",
                           r"(\d+/\d+)\s+of\s+the\s+rest",
                           r"(\d+/\d+)\s+do\s+resto"],
    },
    "soldes2": {
        "price": [r"(\d+(?:[.,]\d+)?)\s*€",
                  r"sur\s+(\d+[.,]\d+)", r"on\s+(\d+(?:\.\d+)?)"],
        "pct1": [r"soldé\s+(\d+)\s*%", r"-\s*(\d+)\s*%\s+puis",
                 r"(\d+)\s*%\s+off", r"reduzido\s+(\d+)\s*%",
                 r"desconto\s+de\s+(\d+)\s*%"],
        "pct2": [r"réduit de\s+(\d+)\s*%", r"puis\s+-?\s*(\d+)\s*%",
                 r"another\s+(\d+)\s*%", r"(?:reduzido|descontado)\s+em\s+(\d+)\s*%"],
    },
}
_SUFFIXE_PCT = {"pct_afternoon", "pct1", "pct2"}


def normalise(texte):
    t = (texte or "").lower().replace("’", "'")
    return re.sub(r"\s+", " ", t)


def extraire(fiche, texte):
    """-> (slots, manquants, ambigus). Les trois vides = applicable.

    Ambigu par créneau : les motifs de ce créneau, appliqués au texte
    PLIÉ (les accents pliés — incident live 22-11 : la phrase
    officielle « réduite de 30 % » ne matchait pas le motif plié
    « réduit de »). La PLIURE des valeurs distinctes = AMBIGU."""
    regles = TRAD.get(fiche) or {}
    t = _fold(texte or "")
    slots, manques, ambigus = {}, [], []
    for slot, motifs in regles.items():
        vals = set()
        for rx in motifs:
            vals.update(re.findall(_fold_pat(rx), t))
        vals.discard("")
        if not vals:
            manques.append(slot)
            continue
        if len(vals) > 1:
            ambigus.append({"slot": slot, "vus": sorted(vals)})
            continue
        v = next(iter(vals))
        if slot == "price":
            v = v.replace(",", ".")
        slots[slot] = (v + "%") if slot in _SUFFIXE_PCT else v
    return slots, manques, ambigus


import unicodedata


def _fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def _fold_pat(rx):
    """Plier l'ACCENT des motifs, jamais leurs escapes : « réduit de »
    devient « reduit de », « \\d+ » reste « \\d+ ». Les classes [...]
    sont recopiées brutes (aucun accent dans les nôtres)."""
    out, i = [], 0
    while i < len(rx):
        c = rx[i]
        if c == "\\" and i + 1 < len(rx):
            out.append(rx[i:i + 2])
            i += 2
            continue
        if c == "[":
            j = rx.index("]", i)
            out.append(rx[i:j + 1])
            i = j + 1
            continue
        out.append(" " if c == "\xa0" else _fold(c))
        i += 1
    return "".join(out)


def prompt_routee(prescription, texte):
    """Le F5-B rejoué : le LM ne fait que recopier."""
    return ("Tu ne CALCULES RIEN. Recopie les nombres du problème dans "
            "ces créneaux : "
            + ", ".join('"%s"' % s for s in prescription["creneaux"])
            + '. Réponds UNIQUEMENT {"slots":{...}}\n\n' + texte)
