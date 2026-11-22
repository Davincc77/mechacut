# -*- coding: utf-8 -*-
"""routeur — matcher de grammaire fermée de l'annuaire (S3,
docs/ROUTER-SPEC.md).

L'annuaire appelle et applique : quand le texte matche la grammaire
d'une fiche, le serveur extrait les créneaux (verbatim) et la chaîne
tourne — ZÉRO LM, le sha du serveur EST la réponse. Hors cadre :
refus NOMMÉ + prompt à remplir, jamais un nombre deviné (règle R3).

Grammaire gelée : une regex par créneau, issue des gabarits v16
(bench/gen16.py, lignes citées dans router_annuaire.json). Plusieurs
valeurs distinctes pour un même créneau = AMBIGU (refus nommé), pas
de premier-venu.
"""
import re

TRAD = {
    "shop-reste": {
        "total": r"(\d+)\s+articles",
        "sold_morning": r"(\d+)\s+sont vendus",
        "pct_afternoon": r"(\d+)\s*%\s*du\s+reste"},
    "partage-reste": {
        "total": r"partage\s+(\d+)",
        "first_part": r"reçoit\s+(\d+/\d+)",
        "second_of_rest": r"(\d+/\d+)\s+du\s+reste"},
    "soldes2": {
        "price": r"(\d+(?:[.,]\d+)?)\s*€",
        "pct1": r"soldé\s+(\d+)\s*%",
        "pct2": r"réduit de\s+(\d+)\s*%"},
}
_SUFFIXE_PCT = {"pct_afternoon", "pct1", "pct2"}


def normalise(texte):
    t = (texte or "").lower().replace("’", "'")
    return re.sub(r"\s+", " ", t)


def extraire(fiche, texte):
    """-> (slots, manquants, ambigus). Les trois vides = applicable."""
    regles = TRAD.get(fiche) or {}
    t = normalise(texte)
    slots, manques, ambigus = {}, [], []
    for slot, rx in regles.items():
        vals = sorted(set(re.findall(rx, t)))
        if not vals:
            manques.append(slot)
        elif len(vals) > 1:
            ambigus.append({"slot": slot, "vus": vals})
        else:
            slots[slot] = (vals[0] + "%") if slot in _SUFFIXE_PCT else vals[0]
    return slots, manques, ambigus


def prompt_routee(prescription, texte):
    """Le F5-B rejoué : le LM ne fait que recopier."""
    return ("Tu ne CALCULES RIEN. Recopie les nombres du problème dans "
            "ces créneaux : "
            + ", ".join('"%s"' % s for s in prescription["creneaux"])
            + '. Réponds UNIQUEMENT {"slots":{...}}\n\n' + texte)
