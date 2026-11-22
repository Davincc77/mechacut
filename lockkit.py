"""lockkit — le verrou de cible, en grammaire FERMÉE sur le NOM.

Banc V20 : le verrou {answer, target} convertit pile la classe « juste
mais à côté » (3/3) et clôture le 7B à 20/20. Banc V23, hors famille :
le garde a REFUSÉ DEUX BONNES RÉPONSES — le modèle disait « prix
final » et « RESTE » (le mot de l'énoncé) au lieu des clés
`final`/`remaining`. Verdict publié : un verrou qui exige la clé
littérale facture 77 % de plus pour rejeter des justes. La correction
est ici, et elle est dogmatiquement maison :

  NORMALISER (cas, accents, ligatures œ/æ, ponctuation, articles) —
  puis TABLE DE SYNONYMES FERMÉE, par cible de la maison (les mots
  relevés dans les énoncés publiés et les incidents des bancs, ×3
  langues). JAMAIS de fuzzy, JAMAIS de similarité, JAMAIS de LM :
  un mot hors table = refus NOMMÉ avec le vocabulaire attendu,
  réparable en une repasse (doctrine v14).

La sémantique des verdicts reste celle mesurée en v20 (importable à
l'identique) : VOCAB → MISMATCH → CIBLE → OK, avec la valeur servie
en décimal exact — « 240 » == « 240.00 », « 160 » nommé remaining
alors que remaining vaut 240 pointe la quantité réelle de cette
valeur. La réponse est une cible, pas un nombre.
"""
import unicodedata
from decimal import Decimal, InvalidOperation

# cibles de la maison = clés rendues par nos fiches et tracées par nos
# bancs ; les synonymes sont les PHRASES RÉELLES observées (énoncés
# gen16, traces V17/V23, sayings ×3 langues), normalisées.
SYNONYMS = {
    "remaining": {"reste", "le reste", "rest", "remainder",
                  "what remains", "what is left", "remain",
                  "combien restent", "combien il reste", "il reste",
                  "quantos restam", "quanto resta", "restante",
                  "restantes"},
    "second_share": {"second share", "second part",
                     "part de la seconde", "la part du second",
                     "segunda parte", "parte da segunda",
                     "combien recoit la seconde",
                     "quanto recebe a segunda"},
    "leftover": {"leftover", "ce qui reste apres partage",
                 "reste apres partage", "rest after second",
                 "sobrante", "resto apos partilha"},
    "final": {"final", "final price", "the final price",
              "prix final", "le prix final", "preco final",
              "montant final", "prix apres remises",
              "price after discounts", "valor final"},
    "projected_litres": {"projected litres", "litres in q hours",
                         "combien de litres", "litres prevus",
                         "litres projetes", "quantos litros"},
    "distance_km": {"distance", "distance parcourue", "km parcourus",
                    "combien de kilometres", "how many kilometers",
                    "distance km", "distancia", "km percorridos",
                    "quilometros"},
    "eggs_needed": {"eggs", "eggs needed", "oeufs", "nombre doeufs",
                    "how many eggs", "ovos", "quantos ovos",
                    "quantite doeufs", "quantidade de ovos"},
}

_ARTICLES = {"le", "la", "les", "l", "un", "une", "the", "a", "an"}


def norm_word(s):
    """Bas-de-casse, accents fondus, ligatures œ/æ ouvertes,
    ponctuation -> espace, articles retirés, espaces repliés.
    Déterministe et sans jugement : c'est la seule magie autorisée."""
    s = str(s or "").lower().replace("œ", "oe").replace("æ", "ae")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = "".join(c if c.isalnum() else " " for c in s)
    words = [w for w in s.split() if w not in _ARTICLES]
    return " ".join(words)


def dec(v):
    try:
        return Decimal(str(v).strip().replace(",", "."))
    except (InvalidOperation, ValueError, AttributeError):
        return None


def resolve(name, vocabulary):
    """name -> clé du vocabulaire, via égalité normalisée OU table
    fermée. Sinon None (jamais deviné)."""
    n = norm_word(name)
    for key in vocabulary:
        if n == norm_word(key):
            return key
    for key, syns in SYNONYMS.items():
        if key in vocabulary and n in syns:
            return key
    return None


def verdict(target, known, name, value):
    """known = {clé: Decimal} — le vocabulaire du serveur (trace de
    pas-à-pas ou answer{} d'une fiche). Retourne (code, details).
    Ordre gelé par v20 : VOCAB, MISMATCH, CIBLE, OK."""
    vocabulary = set(known)
    tkey = resolve(target, vocabulary)
    if tkey is None:
        return "TARGET_UNKNOWN", {"expected_target": str(target),
                                  "vocabulary": sorted(vocabulary)}
    rkey = resolve(name, vocabulary)
    if rkey is None:
        return "VOCAB", {"expected_target": tkey,
                         "vocabulary": sorted(vocabulary)}
    v = dec(value)
    if v is None:
        return "NOT_COMPUTED", {"expected_target": tkey}
    if v != known[rkey]:
        real = [k for k in known if known[k] == v]
        return "MISMATCH", {"expected_target": tkey,
                            "named": rkey,
                            "value_is_actually": sorted(real) or None}
    if rkey != tkey:
        return "CIBLE", {"expected_target": tkey, "named": rkey}
    return "OK", {"target": tkey, "value": format(known[tkey], "f")}
