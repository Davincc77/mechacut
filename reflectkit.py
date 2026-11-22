"""reflectkit — /intent/reflect : la machine rend au modèle SA lecture.

Thèse (l’opérateur, 22-11). Les bancs ont séparé deux classes d'échec :
  v14  la skill stricte SUPPRIME la classe protocole (7b 2/20 → 14/20,
       zéro rupture de forme) ;
  v13  ce qui reste est la COMPRÉHENSION — le modèle lit mal l'histoire,
       et aucune skill ne peut lire à sa place.
D'où le retournement : puisqu'on leur parle dans LEUR langue, qu'ils
parlent la nôtre AVANT de calculer. Le miroir ne devine rien et ne
prescrit rien : il prend la compréhension que le modèle a DE LUI-MÊME,
la rejoue dans l'arithmétique exacte du produit, et la lui rend écrite.
Un modèle qui croyait avoir compris « 7 moins 2 divisé par 2 » voit
s'afficher 2.5 là où l'histoire demandait 3 : l'écart est dans sa
lecture, plus dans ses maths — et il le lit sans nous.

Ce n'est PAS un correcteur sémantique. Un refus ici nomme toujours la
formule et ses args, jamais « tu t'es trompé de problème » : la machine
ne connaît pas l'histoire de l'humain, seulement ce que le modèle a
déclaré. C'est exactement ce qui la rend fiable comme miroir.

Tout passe par le CATALOGUE (formulakit) : une compréhension = une
formule nommée + des args typés. Aucune grammaire nouvelle inventée
ici — c'est la leçon v14 appliquée au produit.
"""
import formulakit as fk

# (Le readback est le champ `substitution` que CHAQUE enregistrement du
# catalogue rend déjà — le miroir n'invente aucune langue, c'est la
# règle. Pas de dictionnaire de phrases parallèles ici : ce qui est
# calculé et ce qui est raconté doivent venir du MÊME champ, sinon le
# miroir peut mentir pendant que la formule dit vrai.)


class Unreadable(Exception):
    """La déclaration du modèle ne forme pas une lecture calculable :
    on nomme le champ attendu, on ne devine pas à sa place."""

    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field, self.message, self.expected = field, message, expected


def _require(body, key, example):
    if not isinstance(body, dict) or key not in body or body[key] in (None, ""):
        raise Unreadable(key, "missing %r" % key, example)
    return body[key]


def run_reflect(body):
    """Entrée : {"formula": "<nom du catalogue>", "args": {...}}.
    Sortie : la MÊME réponse que /api/v1/formula, PLUS le readback —
    la phrase arithmétique que le modèle relit contre l'histoire."""
    name = _require(body, "formula",
                    '{"formula": "rule_of_three", "args": {"a": 3, '
                    '"b": 4.50, "c": 7}}')
    if name not in fk.CATALOG:
        raise Unreadable("formula", "unknown formula %r" % name,
                         "one of: " + "|".join(sorted(fk.CATALOG)))
    args = body.get("args") or {}
    if not isinstance(args, dict):
        raise Unreadable("args", "args must be an object",
                         '{"a": 3, "b": 4.50, "c": 7}')

    # Le miroir APPELLE le catalogue — il n'a pas de calculette à lui.
    # Si le calcul refuse, le refus traverse tel quel : un nom manquant
    # dans une lecture est la même erreur dans les deux produits.
    try:
        out = fk.run_formula(name, args)
    except KeyError as e:
        raise Unreadable("args", str(e), fk.CATALOG[name]["args"])

    out["formula_ref"] = fk.CATALOG[name]["formula"]
    out["source"] = fk.CATALOG[name]["source"]
    out["reading_check"] = (
        "relis cette ligne contre la phrase de l'humain : « %s ». "
        "Si les NOMBRES ne sont pas ceux de l'histoire, la lecture est "
        "fausse et le calcul juste ne sauvera rien — redéclare. Si les "
        "nombres sont les bons, le résultat ci-dessus est exact, tu n'as "
        "plus à le refaire de tête."
        % out["substitution"])
    out["not_claimed"] = (
        "la machine ne connaît pas l'histoire : elle ne dit pas si ta "
        "lecture est la bonne, elle l'écrit assez noir sur blanc pour "
        "que TU le voies")
    return out
