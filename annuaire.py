# -*- coding: utf-8 -*-
"""annuaire — chargeur du routeur-douleurs (S1, docs/ROUTER-SPEC.md).

L'annuaire est de la DATA versionnée : ce module ne fait que la
charger et la valider à la forme. Une entrée sans preuve existante
sur disque est une opinion : elle crève le test, pas la prod.
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
ANNUAIRE = os.path.join(ROOT, "router_annuaire.json")

FICHES_CONNUES = {"shop-reste": "remaining",
                  "partage-reste": "second_share",
                  "soldes2": "final"}


def load(path=ANNUAIRE, strict=True):
    """strict=True (défaut, tests + dépôt) : chaque preuve doit exister
    sur disque — c'est la garde R4, une entrée sans ligne de bench
    commitée est une opinion. strict=False (runtime prod) : le Docker
    n'embarque pas bench/ ; à l'appel HTTP on sert l'entrée, la preuve
    restant CITÉE dans la réponse. La vérification d'existence est un
    garde de COMMIT, pas de REQUEST — sinon le prod plante sur un
    fichier que l'image ne contient pas (incident 0.84.0, consigné)."""
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    assert isinstance(d.get("version"), str) and d["version"]
    assert isinstance(d.get("regles_transport"), list) and \
        d["regles_transport"]
    for r in d["regles_transport"]:
        assert r.get("loi") and r.get("preuve"), "règle sans preuve"
        if strict:
            assert os.path.exists(os.path.join(ROOT, r["preuve"])), \
                "preuve de règle absente : %s" % r["preuve"]
    ids = set()
    for e in d.get("entrees", []):
        p = e["prescription"]
        fiche = p["fiche"]
        assert fiche in FICHES_CONNUES, "fiche inconnue : %s" % fiche
        assert p["cible"] == FICHES_CONNUES[fiche], \
            "%s : cible %s ≠ %s (verrou de cible, loi T4)" % (
                e["id"], p["cible"], FICHES_CONNUES[fiche])
        assert p["transport"] == "mono-appel-routé", \
            "la loi T1 ne se négocie pas : %s" % e["id"]
        proofs = e["preuve"] if isinstance(e["preuve"], list) \
            else [e["preuve"]]
        assert proofs, "entrée sans preuve : %s" % e["id"]
        if strict:
            for pf in proofs:
                assert os.path.exists(os.path.join(ROOT, pf)), \
                    "preuve absente du disque : %s (%s)" % (pf, e["id"])
        assert e["id"] not in ids, "id dupliqué : %s" % e["id"]
        ids.add(e["id"])
    return d


def trouver(texte, d=None):
    """Le mot le plus spécifique gagne ; pas de score flottant,
    pas d'approximation — ce qui ne matche pas reçoit une
    prescription vide (= on ne devine pas)."""
    d = d or load()
    meilleur, score = None, 0
    t = (texte or "").lower()
    for e in d["entrees"]:
        s = sum(1 for m in e["mots_cles"] if m in t)
        if s > score:
            meilleur, score = e, s
    return (meilleur, score) if score else (None, 0)


if __name__ == "__main__":
    dd = load()
    print("annuaire", dd["version"], ":", len(dd["entrees"]), "entrées,",
          len(dd["regles_transport"]), "règles de transport")
