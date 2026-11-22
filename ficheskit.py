"""ficheskit — F5 : les fiches-recettes à chaîne (bench v15, loi des 0/56).

Ce qu'une fiche change : le MODÈLE ne décompose plus jamais. La chaîne
de dépendances (« 40 % DU RESTE », « 1/4 du reste », « -25 % puis -20 % »)
est gelée ici, une fois, testée, épinglée ; l'appelant ne fournit que
des CRÉNEAUX — les nombres que l'humain a dits. C'est la forme exacte
des problèmes où nu et retry tombent à zéro sur 56 cellules : la
décomposition était le travail, pas l'arithmétique.

Chaque fiche rend sa TRACE d'étapes (expression + valeur exacte à
chaque pas) et sa CIBLE nommée : l'agent relit la chaîne au lieu de
l'avoir inventée. Arithmétique 100 % Fraction — aucun float n'entre
dans la chaîne.
"""
import re
from decimal import Decimal
from fractions import Fraction

F = Fraction

SLOT_RE = re.compile(r"^-?\d+(?:\.\d+)?$|^-?\d+/\d+$|^-?\d{1,4}%$")

# Sémantique par NOM de créneau (le smoke 0.5B du 22-11 a montré que la
# grammaire seule laissait passer "40" pour 40 % (×40 silencieux) et une
# quantité dans un créneau de part). Un produit déterministe ne devine
# JAMAIS le sens d'un nombre ambigu : il refuse, nomme le champ, dit la
# forme attendue — et l'appelant repart corriger (error-that-repairs).
_PCT = ("pct",)          # slots dont le nom contient "pct"
_SHARE = ("first_part", "second_of_rest")   # parts : valeur ≤ 1


class Slot(Exception):
    """Un créneau mal rempli : nommé, avec la forme attendue — jamais
    deviné. Grammaire fermée : décimal à point, fraction a/b, ou
    pourcentage n%."""

    def __init__(self, field, got, expected=None):
        self.field = field
        self.got = got
        self.message = "slot %r is not a closed number: %r" % (field, got)
        self.expected = expected or ("decimal \"435\" or \"81.90\", "
                                     "fraction \"2/5\", or percent "
                                     "\"40%\"")


def _loc(args):
    """F7 : la langue des NOMBRES se déclare, elle ne se devine pas.
    « 1.250 » vaut 1250 en pt/fr et 1.25 en en — deviner, c'est le
    « 40 » nu bis. Absent = grammaire fermée actuelle (aucune
    régression : ce qui passait passe, rien de nouveau ne passe)."""
    loc = (args or {}).get("locale")
    if loc is None:
        return ""
    if loc not in ("en", "fr", "pt"):
        raise Slot("locale", loc, 'one of "en", "fr", "pt" — or omit '
                   "the field and write plain closed numbers")
    return loc


def _slot(name, v, loc=""):
    s = str(v if v is not None else "").strip()
    s = re.sub(r"\s+%", "%", s)   # « 40 % » partout : l'espace n'est
                                  # pas un sens
    if loc == "en":
        m = re.fullmatch(r"(\d{1,3})(,\d{3})+(\.\d+)?", s)
        if m:
            s = s.replace(",", "")
    elif loc in ("fr", "pt"):
        m = re.fullmatch(r"(\d{1,3})([.\s ]\d{3})+(,\d+)?", s)
        if m:
            s = re.sub(r"[.\s ](?=\d{3})", "", s).replace(",", ".")
        elif re.fullmatch(r"\d+,\d+", s):
            s = s.replace(",", ".")   # « 89,90 » = 89.90
    if not loc and re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):
        # « 1.250 » vaut 1250 en pt/fr et 1.25 en en : la grammaire
        # fermée seule ne peut PAS trancher. C'est un refus nommé,
        # jamais une dévination silencieuse (P2, gelé 20h10).
        raise Slot(name, v, 'ambiguous thousands separator: '
                   '"%s" reads as %s (pt/fr) or %s (en) — declare '
                   '"locale": "en"|"fr"|"pt" in the slots — the fiche '
                   "never guesses"
                   % (s, s.replace(".", "").replace(",", ""),
                      s.replace(",", ".")))
    if not SLOT_RE.match(s):
        raise Slot(name, v)
    fr = (F(Decimal(s[:-1])) / 100 if s.endswith("%") else
          F(*(int(x) for x in s.split("/"))) if "/" in s
          else F(Decimal(s)))
    if any(t in name for t in _PCT) and fr > 1:
        raise Slot(name, v, "a percent: \"40%\", or the fraction "
                   "\"0.4\" — never the bare \"40\": it would "
                   "silently multiply by forty")
    if name in _SHARE and fr > 1:
        raise Slot(name, v, "a share of a whole (≤ 1): \"2/5\" or "
                   "\"0.4\" — a bare quantity like %r means you "
                   "computed the share; the fiche computes it, you "
                   "copy the human's words" % (v,))
    return fr


def _fmt(fr):
    """Fraction → texte exact : entier, centièmes si ça tombe, sinon
    fraction mixte LISIBLE + décimale bornée — jamais un arrondi muet."""
    scaled = fr * 100
    if fr.denominator == 1:
        return str(int(fr))
    if scaled.denominator == 1:
        c = int(scaled)
        if c < 0:
            return "-%d.%02d" % ((-c) // 100, (-c) % 100)
        return "%d.%02d" % (c // 100, c % 100)
    whole = int(fr)
    rest = fr - whole
    mixed = ("%d %d/%d" % (whole, rest.numerator, rest.denominator)
             if whole and rest.numerator else
             "%d/%d" % (fr.numerator, fr.denominator))
    dec = Decimal(fr.numerator) / Decimal(fr.denominator)
    return "%s (≈ %s)" % (mixed, str(dec.quantize(Decimal("0.01"))))


def _trace(pairs):
    return [{"step": i + 1, "expr": e, "value": _fmt(v)}
            for i, (e, v) in enumerate(pairs)]


def shop_reste(args):
    """total, sold_morning, pct_afternoon → remaining.
    (v15 famille « mix » : 0/28 nu+retry.)"""
    loc = _loc(args)
    total = _slot("total", args.get("total"), loc)
    morning = _slot("sold_morning", args.get("sold_morning"), loc)
    pct = _slot("pct_afternoon", args.get("pct_afternoon"), loc)
    rest1 = total - morning
    if rest1 < 0:
        raise Slot("sold_morning", args.get("sold_morning"))
    after = rest1 * pct
    remaining = rest1 - after
    return {
        "recipe": "shop_reste",
        "trace": _trace([
            ("rest_after_morning = total − sold_morning = %s − %s"
             % (_fmt(total), _fmt(morning)), rest1),
            ("sold_afternoon = rest_after_morning × pct_afternoon ="
             " %s × %s" % (_fmt(rest1), _fmt(pct)), after),
            ("remaining = rest_after_morning − sold_afternoon = %s − %s"
             % (_fmt(rest1), _fmt(after)), remaining)]),
        "answer": {"remaining": _fmt(remaining)},
        "target": "remaining",
        "note": "you filled three slots; the chain was ours. A naked "
                "model scored 0/28 on exactly this shape (bench v15)"}


def partage_reste(args):
    """total, first_part, second_of_rest → second_share (+ leftover).
    (v15 famille « partage » : 0/28 aussi.)"""
    loc = _loc(args)
    total = _slot("total", args.get("total"), loc)
    f1 = _slot("first_part", args.get("first_part"), loc)
    f2 = _slot("second_of_rest", args.get("second_of_rest"), loc)
    rest = total * (1 - f1)
    second = rest * f2
    left = rest - second
    return {
        "recipe": "partage_reste",
        "trace": _trace([
            ("rest = total × (1 − first_part) = %s × (1 − %s)"
             % (_fmt(total), _fmt(f1)), rest),
            ("second_share = rest × second_of_rest = %s × %s"
             % (_fmt(rest), _fmt(f2)), second),
            ("leftover = rest − second_share = %s − %s"
             % (_fmt(rest), _fmt(second)), left)]),
        "answer": {"second_share": _fmt(second), "leftover": _fmt(left)},
        "target": "second_share",
        "note": "the second share is OF THE REST, not of the total — "
                "the one word that zeroes every naked model"}


def soldes2(args):
    loc = _loc(args)
    """price, pct1, pct2 → final (+ le mensonge de la somme).
    Ne duplique PAS money/discount : deux remises, noyau minimal, la
    fiche POINTE discount pour les chaînes à N paliers."""
    price = _slot("price", args.get("price"), loc)
    p1 = _slot("pct1", args.get("pct1"), loc)
    p2 = _slot("pct2", args.get("pct2"), loc)
    after1 = price * (1 - p1)
    final = after1 * (1 - p2)
    naive = price * (1 - (p1 + p2))
    return {
        "recipe": "soldes2",
        "trace": _trace([
            ("after_first = price × (1 − pct1) = %s × (1 − %s)"
             % (_fmt(price), _fmt(p1)), after1),
            ("final = after_first × (1 − pct2) = %s × (1 − %s)"
             % (_fmt(after1), _fmt(p2)), final)]),
        "answer": {"final": _fmt(final),
                   "effective_pct": _fmt((price - final) / price * 100),
                   "naive_sum_pct": _fmt((p1 + p2) * 100),
                   "sum_understates_final_by": _fmt(
                       (naive - final) * -1 if price == 0 else
                       (final - naive) / price * 100)},
        "target": "final",
        "see_also": "/api/v1/money/discount for N-step chains "
                    "(order impact, buy2pay1)",
        "note": "two discounts, exact factors — the checkout will "
                "still add the percentages; it won't be exact"}


FICHES = {"shop_reste": shop_reste, "partage_reste": partage_reste,
          "soldes2": soldes2}


def run_fiche(name, args):
    if name not in FICHES:
        raise Slot("recipe", name)
    return FICHES[name](args or {})
