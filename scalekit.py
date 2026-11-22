"""scalekit — /api/v1/table/scale : la recette réduite avec les RÈGLES DITES.

« 1/3 de la recette » : les modèles écrasent les fractions — 400 g × 1/3
ressort « 133 » ou « 130 » selon l'humeur, 5 œufs ÷ 2 devient « 3 œufs »
sans explication (l'affaire NYT Cooking AI, novembre 2026). Ici chaque
ligne rend TROIS choses : le produit EXACT (Fraction réduite, jamais de
flottant), le nombre MESURABLE (arrondi par la classe d'ingrédient, règle
nommée dans la réponse) et l'ÉCART entre les deux. Le multiplicateur est
dit UNE fois (ratio de portions réduit en fraction exacte). Un
silent-rounding est structurellement impossible : la règle est dans la
réponse, pas dans l'à-peu-près.

Fermé, ça veut dire :
  unités      g kg oz lb ml l tsp tbsp cup piece — les vagues « pinch »,
              « handful », « pincée » sont REFUSÉES PAR LE NOM (c'est LA
              douleur r/AskReddit « 500 couverts x 1 pincee = 12,5 lb
              de sel » : une mesure ouverte ne se scale pas)
  classes     base salt spice leavening yeast egg — chacune SA table
              d'arrondi, publiée dans la réponse (kitchen-steps-v1)
  factor      décimal exact ou fraction « 1/3 » ; OU servings_from/
              servings_to entiers — le ratio est calculé, réduit, REDIT.
              Les deux à la fois = refus nommé (dit une seule fois).
  power       option par ligne : le facteur appliqué devient
              factor**power — exact pour puissances entières et racines
              propres, sinon Decimal ln/exp 34 chiffres arrondi à 6.
              Sub-linéaire SUR DEMANDE et déclaré, jamais inventé.
  refus       factor ≤ 0, signe, flottant, vide, >200 lignes, nombres
              démesurés (12 chiffres), classe/unité hors table fermée

Les paliers mesurables viennent du matériel de mesure publié : jeux de
cuillères américains 1/4–1 tsp (les mini-jeux sel/épices descendent au
1/8, cf. Williams-Sonoma/King Arthur), tasses graduées 1/4 cup, balances
de cuisine 1 g puis 5 g puis 10 g, 0,1 g sous 10 g. Œuf : 50 g coquille
enlevée = poids publié King Arthur / USDA « large egg ». Aucune médecine,
aucune dose : le sub-linéaire culinaire n'est appliqué QUE si l'appelant
fournit power=, et la note le dit.

Aucun état module : tout est passé en paramètre (threads FastAPI).
"""
import re
from decimal import Decimal, ROUND_HALF_UP, getcontext
from fractions import Fraction

getcontext().prec = 34

MAX_ITEMS = 200
MAX_DIGITS = 12          # chiffres par nombre (entières ET décimales)
DECIMAL_PLACES = 4       # rendu décimal déclaré

UNITS = {"g": "grams", "kg": "kilograms", "oz": "ounces", "lb": "pounds",
         "ml": "millilitres", "l": "litres", "tsp": "teaspoons",
         "tbsp": "tablespoons", "cup": "cups", "piece": "pieces"}
VAGUE = {"pinch", "pincée", "pincee", "handful", "dash", "smidgen",
         "poignée", "poignee"}

CLASSES = {"base", "salt", "spice", "leavening", "yeast", "egg"}
NON_LINEAR = {"salt", "spice", "leavening", "yeast"}

EGG_GRAMS = Decimal(50)  # « large egg », coquille enlevée — King Arthur
                         # Baker's weight / USDA 50 g


class ScaleError(Exception):
    pass


def _fail(msg):
    raise ScaleError(msg)


def _parse_qty(text, field):
    """Texte source -> Fraction exacte. « 1/3 », « 2 1/2 », « 0.5 »,
    « 5 ». Le texte commande, jamais le binaire flottant."""
    if isinstance(text, bool) or isinstance(text, float):
        _fail("%s: flottant/booleen refuse — passez la valeur ECRITE en "
              "chaine (0.1 en binaire vaut 0.30000000000000004 apres x3)"
              % field)
    if isinstance(text, int):
        s = str(text)
    elif isinstance(text, str):
        s = text.strip()
    else:
        _fail("%s: ecrire un nombre (« 400 », « 1/3 », « 2 1/2 »)" % field)
    if not s:
        _fail("%s: vide" % field)
    if len(s) > 40:
        _fail("%s: trop long (40 caracteres max)" % field)
    if s[0] in "+-":
        _fail("%s: signe refuse — on scale des quantites, pas des dettes"
              % field)
    m = re.match(r"^(\d+)\s+(\d+)/(\d+)$", s)
    if m:
        _size(m.group(1), field)
        _size(m.group(2), field)
        _size(m.group(3), field)
        if int(m.group(3)) == 0:
            _fail("%s: denominator zero" % field)
        return Fraction(int(m.group(1)) * int(m.group(3)) + int(m.group(2)),
                        int(m.group(3)))
    m = re.match(r"^(\d+)/(\d+)$", s)
    if m:
        _size(m.group(1), field)
        _size(m.group(2), field)
        if int(m.group(2)) == 0:
            _fail("%s: denominator zero" % field)
        return Fraction(int(m.group(1)), int(m.group(2)))
    m = re.match(r"^(\d+)\.(\d+)$", s)
    if m:
        _size(m.group(1), field)
        _size(m.group(2), field)
        return Fraction(s)
    m = re.match(r"^\d+$", s)
    if m:
        _size(s, field)
        return Fraction(int(s))
    _fail("%s: « %s » n'est ni un nombre, ni une fraction « a/b », ni "
          "une mixte « a b/c »" % (field, s))


def _size(part, field):
    if len(part) > MAX_DIGITS:
        _fail("%s: %d chiffres max par nombre" % (field, MAX_DIGITS))


def _mixed(fr):
    """Fraction >= 0 -> « 133 1/3 » (mixte réduite ; Fraction réduit)."""
    if fr.denominator == 1:
        return str(fr.numerator)
    whole = fr.numerator // fr.denominator
    rest = fr - whole
    if whole and rest:
        return "%d %d/%d" % (whole, rest.numerator, rest.denominator)
    return "%d/%d" % (fr.numerator, fr.denominator)


def _fmt(fr):
    """Decimal de la Fraction, 4 places déclarees, zeros superflus coupes."""
    d = Decimal(fr.numerator) / Decimal(fr.denominator)
    d = d.quantize(Decimal(1).scaleb(-DECIMAL_PLACES),
                   rounding=ROUND_HALF_UP)
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


SPOONLIKE = ("tsp", "tbsp", "cup", "oz", "lb")


def _human(fr, unit):
    """La notation du public : fraction mixte pour cuilleres/tasses/onces
    (les jeux publies sont en fractions), decimale pour le metric."""
    return _mixed(fr) if unit in SPOONLIKE else _fmt(fr)


def _step(unit, cls, exact_abs):
    """Palier mesurable — kitchen-steps-v1 (source : docstring)."""
    if unit in ("g", "ml"):
        if exact_abs < 10:
            return Fraction(1, 10)
        if exact_abs < 100:
            return Fraction(1)
        if exact_abs < 1000:
            return Fraction(5)
        return Fraction(10)
    if unit == "kg":
        return Fraction(1, 100)
    if unit == "l":
        return Fraction(1, 20)
    if unit == "oz":
        return Fraction(1, 4)
    if unit == "lb":
        return Fraction(1, 8)
    if unit == "cup":
        return Fraction(1, 4)
    if unit == "tbsp":
        return Fraction(1, 2) if cls == "base" else Fraction(1, 4)
    if unit == "tsp":
        return Fraction(1, 4) if cls == "base" else Fraction(1, 8)
    return Fraction(1)  # piece / egg


def _round_to_step(fr, step):
    """Exact -> plus proche palier, demi vers le large. Un exact positif
    ne devient JAMAIS zero : on remonte au premier palier et on le DIT."""
    val = Decimal(fr.numerator) / Decimal(fr.denominator)
    q = (val / Decimal(step.numerator) * Decimal(step.denominator)) \
        .to_integral_value(rounding=ROUND_HALF_UP)
    meas = Fraction(q) * step
    floored = fr > 0 and meas == 0
    if floored:
        meas = step
    return meas, floored


def _pow_factor(f, p):
    """factor ** power : entiers exacts, racines propres exactes, sinon
    Decimal ln/exp 34 chiffres -> 6 declarees."""
    if p.denominator == 1:
        n = int(p)
        if n >= 0:
            return Fraction(f.numerator ** n, f.denominator ** n)
        if f.numerator == 0:
            _fail("power negative sur zero")
        return Fraction(f.denominator ** -n, f.numerator ** -n)
    if p == Fraction(1, 2) or p == Fraction(1, 3):
        k = int(p.denominator)
        rn, rd = _iroot(f.numerator, k), _iroot(f.denominator, k)
        if rn ** k == f.numerator and rd ** k == f.denominator:
            return Fraction(rn, rd)
    val = ((Decimal(f.numerator) / Decimal(f.denominator)).ln()
           * Decimal(p.numerator) / Decimal(p.denominator))
    got = val.exp().quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    return Fraction(str(got))


def _iroot(n, k):
    if n < 0:
        _fail("racine negative")
    x = int(round(n ** (1.0 / k)))  # SEED seulement, jamais le resultat
    while x > 0 and x ** k > n:
        x -= 1
    while (x + 1) ** k <= n:
        x += 1
    return x


def scale(items, factor=None, servings_from=None, servings_to=None,
          power_default=None):
    if not isinstance(items, list) or not items:
        _fail("items: liste non vide requise")
    if len(items) > MAX_ITEMS:
        _fail("items: %d lignes, max %d" % (len(items), MAX_ITEMS))
    if factor is not None and (servings_from is not None
                               or servings_to is not None):
        _fail("factor ET servings_* : le multiplicateur est dit UNE "
              "fois — choisissez")
    if factor is not None:
        f = _parse_qty(factor, "factor")
        source = "factor"
    elif servings_from is not None and servings_to is not None:
        a = _parse_qty(servings_from, "servings_from")
        b = _parse_qty(servings_to, "servings_to")
        if a.denominator != 1 or b.denominator != 1:
            _fail("servings_* : entiers de convives")
        if a == 0 or b == 0:
            _fail("servings_* : positif (0 convive = personne ne mange)")
        f = Fraction(b.numerator, a.numerator)
        source = "servings %d -> %d" % (a.numerator, b.numerator)
    else:
        _fail("factor ou (servings_from + servings_to) : requis")
    if f <= 0:
        _fail("factor: strictement positif")

    power_d = None
    if power_default is not None:
        power_d = _parse_qty(power_default, "power_default")
        if power_d <= 0:
            _fail("power_default: positif")

    out_items = []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            _fail("items[%d]: objet {name, qty, unit, class}" % i)
        name = str(it.get("name") or "").strip()
        if not name:
            _fail("items[%d]: name requis" % i)
        if len(name) > 120:
            _fail("items[%d]: name 120 caracteres max" % i)
        cls = str(it.get("class") or "base").strip().lower()
        if cls not in CLASSES:
            _fail("items[%d] «%s»: class inconnue «%s» — table fermee "
                  "base salt spice leavening yeast egg" % (i, name, cls))
        unit = str(it.get("unit") or "").strip().lower()
        if unit in VAGUE:
            _fail("items[%d] «%s»: «%s» n'est pas mesurable (500 "
                  "couverts x 1 pincee = 12,5 lb de sel). Declarez la "
                  "conversion de VOTRE source et passez tsp ou g"
                  % (i, name, unit))
        if unit not in UNITS:
            _fail("items[%d] «%s»: unite inconnue «%s» — table fermee %s"
                  % (i, name, unit, " ".join(sorted(UNITS))))
        q = _parse_qty(it.get("qty"), "items[%d].qty" % i)
        if q < 0:
            _fail("items[%d] «%s»: qty negatif refuse" % (i, name))

        applied = f
        power_note = None
        pw = it.get("power", power_d)
        if pw is not None:
            pp = pw if isinstance(pw, Fraction) else _parse_qty(
                pw, "items[%d].power" % i)
            if pp <= 0:
                _fail("items[%d] «%s»: power positif" % (i, name))
            applied = _pow_factor(f, pp)
            power_note = "factor %s ** power %s = %s" % (
                _mixed(f), _mixed(pp), _mixed(applied))

        exact = q * applied
        step = _step(unit, cls, abs(exact))
        meas, floored = _round_to_step(exact, step)

        row = {
            "name": name,
            "class": cls,
            "input": "%s %s" % (_mixed(q), unit),
            "exact": {"fraction": "%s %s" % (_mixed(exact), unit),
                      "decimal": "%s %s" % (_fmt(exact), unit)},
            "measurable": {"value": "%s %s" % (_human(meas, unit), unit),
                           "rule": "nearest %s %s, half-up"
                                   % (_human(step, unit), unit)},
        }
        if power_note:
            row["power"] = power_note
        if q == 0:
            row["rounding_delta"] = "0%"
        else:
            row["rounding_delta"] = "%s%%" % _fmt(
                (meas - exact) / exact * 100)
        if floored:
            row["flag"] = ("below smallest step — raised to %s %s; "
                           "double-batch-and-halve is the honest fix"
                           % (_human(step, unit), unit))
        if cls in NON_LINEAR:
            row["note"] = ("scaled LINEARLY; published kitchen guidance "
                           "has salt/spice/leavening sub-scale beyond "
                           "about x2 — pass power=0.75 if YOUR source "
                           "says so; this machine never invents it")
        if cls == "egg" and unit == "piece":
            row["weight_alternative"] = (
                "beat and weigh: %s g (large egg = 50 g shelled, "
                "published King Arthur/USDA weight)"
                % _fmt(exact * Fraction(EGG_GRAMS)))
        out_items.append(row)

    return {
        "multiplier": {"fraction": str(f), "mixed": _mixed(f),
                       "decimal": _fmt(f), "source": source},
        "items": out_items,
        "rules": {
            "table": "kitchen-steps-v1",
            "steps": {
                "g/ml": "under 10 -> 0.1 ; under 100 -> 1 ; "
                        "under 1000 -> 5 ; else 10",
                "kg": "0.01", "l": "0.05", "oz": "1/4", "lb": "1/8",
                "cup": "1/4",
                "tbsp": "base 1/2 / salt-spice 1/4",
                "tsp": "base 1/4 / salt-spice-leavening-yeast 1/8",
                "piece/egg": "1 whole",
            },
            "sourced_from": "published measuring sets (1/4 tsp min, "
                            "1/8 in mini sets; 1/4 cup min) and kitchen "
                            "scales (1/5/10 g graduations); egg 50 g = "
                            "King Arthur/USDA large-egg weight",
            "rounding": "nearest step, half-up; positive exact never "
                        "rounds to zero (raised + flagged)",
            "arithmetic": "source text -> Fraction, zero float; "
                          "decimals shown to 4 places, trailing zeros "
                          "trimmed",
        },
        "scope_notes": [
            "bake time and pan size do NOT scale with quantities — "
            "geometry and oven behaviour are separate questions",
            "prices, shopping and nutrition are out of contract: bring "
            "the numbers, get the math stated",
            "no medical/veterinary dosing: this scales flour, not "
            "prescriptions",
        ],
    }
