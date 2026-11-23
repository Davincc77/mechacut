# -*- coding: utf-8 -*-
"""ovenschedulekit — /api/v1/food/ovenschedule : le compte à rebours
d'UN four, plats donnés, horaires calculés À REBOURS de l'heure de
service. serve_at/earliest_start sont des ARGUMENTS ; le module ne lit
JAMAIS une horloge murale (parallèle strict de poultry, leftovers et
du grand livre d'aging — la dérive de minuit est publiée).

Douleur mesurée 23-nov-2026 (J-3 de Thanksgiving) : huit timelines
publiées cette semaine, TOUTES en désaccord sur les mêmes minutes.
Repos de la dinde : « rests up to an hour » (chefamazing) contre
« 25 minutes » (thekitchencalc) contre « 30 to 45 » (howsweeteats)
contre « 20-30 » (hypemenu) contre « 45 min » (tessiestable) contre
« 30 minutes » (rsvplinks) — 20 à 60 minutes selon la page. Tempéra-
ture : 350 °F chez l'une, 325 °F chez quatre, « 425 puis 350 » chez
une autre. Et le temps que PERSONNE ne compte : « preheating eats 45
of them » (thekitchencalc) — le four froid ne commence pas à midi.
C'est rsvplinks qui écrit notre contrat, mot pour mot : « List every
dish that needs theoven, its temperature and its time. » Les timelines
web sont statiques, muettes sur les conflits de température (le plat
sort à 15:45, le suivant ENTRE à 15:45 à 100 °F de plus — la physique
refuse), et périmées le 27 novembre.

Doctrine :
  * UN FOUR, UN PLAT À LA FOIS — publié dans la réponse (field
    model). Le coiffage multi-racks est le choix de l'appelant : qui
    veut deux plats ensemble en passe un seul. La séquence est
    l'ordre du tableau, jamais une optimisation inventée.
  * Calcul À REBOURS : chaque plat doit être prêt à l'heure de
    service (sortie + repos hors four) et le four est une ressource
    séquentielle. Un plat sort plus tôt si le suivant entre plus tôt ;
    le temps d'attente supplémentaire est NOMBRE (hold_minutes),
    jamais caché.
  * LE REPOS A UN PLAFOND DE SÉCURITÉ : > 120 minutes hors four =
    refus NOMMÉ — la règle des 2 heures de la zone de danger FSIS est
    la même que celle de /food/leftovers (« discard any turkey … left
    out at room temperature longer than 2 hours »). Un plat qui doit
    reposer plus longtemps entre au frigo, pas dans notre contrat.
  * LA TEMPÉRATURE PORTE SON UNITÉ : « 180 » sans unité est refusé —
    c'est un tossé entre 82 °C et 356 °F, soit le double raté soit le
    brûlé (loi des nombres nus, précédente aging/shop). Conversion
    C→F exacte par 9/5+32 (Fraction, jamais de float), arrondi
    affiché seulement quand le publié ne l'est pas.
  * LES TRANSITIONS DE T° SONT UN ARGUMENT : preheat = minutes que
    le four met à tenir une nouvelle consigne. Les pages se
    contredisent (12-15 min à 325, 20 à 425 — thekitchencalc) ; le
    module NE DEVINE PAS, il applique la valeur passée (0 = « mon
    four tient », assumé) et marque la CONFLIT physique : deux plats
    consécutifs à des t° différentes avec zéro minute entre les deux
    = impossible, nommé (c'est LE trou que les timelines muettes
    laissent dans les calendriers).
  * Faisabilité : earliest_start compare à l'allumage du four ; trop
    juste = verdict nommé short_by_minutes, le calendrier reste rendu
    (le calcul est le contrat, la fenêtre est au monde).
  * 325 °F = plancher FSIS des VOLAILLES (poultry), publié en champ
    informatif only — jamais un refus pour un gratin à 300 °F.

Sources citées : timelines listées ci-dessus (consultées 23-nov-2026)
; FSIS « Let's Talk Turkey » (2 h / 1 h au-dessus de 90 °F, four « no
lower than 325 °F »). Aucun temps de cuisson INVENTÉ : les minutes ne
viennent que de l'appelant — la table FSIS par poids vit chez
/food/poultry, ce module est l'AGENCEUR, pas le cuisinier.
"""
from datetime import datetime, timedelta
from fractions import Fraction

MAX_DISHES = 12
MAX_MINUTES = 1440
MAX_REST = 120          # FSIS danger zone, 2 heures — voir leftovers
MAX_PREHEAT = 60
FSIS_FLOOR_F = 325      # volailles uniquement — informatif
MODEL = ("one oven, one dish at a time, array order = load order; "
         "rests happen OUTSIDE the oven; times counted backwards "
         "from serve_at — no wall clock, no invented cook times")
SOURCE = ("FSIS 'Let's Talk Turkey' (2 h room-temperature rule, 325 F "
          "poultry floor); oven-timeline disagreement measured "
          "2026-11-23 across 8 published Thanksgiving schedules "
          "(rest 20-60 min, 325 vs 350 F, preheat 12-20 min)")


class OvenError(Exception):
    def __init__(self, field, message, expected):
        self.field = field
        self.message = str(message)
        self.expected = expected
        super().__init__("%s: %s" % (field, message))


def _serve_dt(args, field):
    raw = args.get(field)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    if not isinstance(raw, str):
        raise OvenError(field, "chaîne attendue",
                        "ISO string, no JSON date object")
    t = raw.strip()
    if "/" in t:
        raise OvenError(
            field, "date à slashes refusée — un jour ambigu déplace "
                   "tout le calendrier (précédent aging/leftovers)",
            "ISO 8601 like 2026-11-26T16:00")
    if " " in t or t.endswith("Z") or "+" in t[10:]:
        raise OvenError(
            field, "fuseau ou espace non parse — naïves, même fuseau "
                   "sur toute la requête (doctrine poultry)",
            "naive ISO local, e.g. 2026-11-26T16:00")
    try:
        return datetime.fromisoformat(t)
    except ValueError:
        raise OvenError(field, "ISO invalide", "2026-11-26T16:00")


def _int(raw, field, lo, hi, required=True):
    if raw is None or raw == "":
        if required:
            raise OvenError(field, "absent",
                            "integer %d..%d" % (lo, hi))
        return None
    if isinstance(raw, bool) or not isinstance(raw, (int, str)):
        raise OvenError(field, "entier attendu", "integer or "
                        "integer string")
    s = str(raw).strip()
    if "." in s or "e" in s.lower():
        raise OvenError(
            field, "fraction refusée — la minute du four est "
                   "entière, et un float recopie l'erreur", "integer")
    try:
        v = int(s)
    except ValueError:
        raise OvenError(field, "entier attendu", "integer")
    if v < lo:
        raise OvenError(field, "minimum %d — le module ne prolonge "
                        "pas une table par un nombre extraordinaire"
                        % lo, "≥ %d" % lo)
    if v > hi:
        raise OvenError(field, "maximum %d — le module ne prolonge "
                        "pas une table par un nombre extraordinaire"
                        % hi, "≤ %d" % hi)
    return v


def _c_to_f(c):
    """Conversion EXACTE 9/5+32 (Fraction, jamais de float). Rendu :
    entier quand elle tombe juste, sinon une décimale — la précision
    affichée est une affirmation."""
    f = Fraction(c) * Fraction(9, 5) + 32
    if f.denominator == 1:
        return int(f)
    return float(round(f, 1))


def run_ovenschedule(args):
    args = args or {}
    serve = _serve_dt(args, "serve_at")
    if serve is None:
        raise OvenError(
            "serve_at", "absent — le compte à rebours n'a pas de "
                        "fin ; le module ne lit aucune horloge "
                        "murale", "naive ISO like 2026-11-26T16:00")
    earliest = _serve_dt(args, "earliest_start")
    preheat = _int(args.get("preheat", 0), "preheat", 0, MAX_PREHEAT,
                   required=False) or 0

    dishes = args.get("dishes")
    if not isinstance(dishes, list) or not dishes:
        raise OvenError(
            "dishes", "liste vide ou absente — rsvplinks écrit le "
                      "contrat : « list every dish that needs the "
                      "oven, its temperature and its time »",
            "non-empty array, max %d" % MAX_DISHES)
    if len(dishes) > MAX_DISHES:
        raise OvenError(
            "dishes", "plus de %d plats — au-delà, ce n'est plus un "
                      "four mais une logistique ; découpez en deux "
                      "menus" % MAX_DISHES, "≤ %d dishes" % MAX_DISHES)

    parsed = []
    for i, d in enumerate(dishes):
        where = "dishes[%d]" % i
        if not isinstance(d, dict):
            raise OvenError(where, "objet attendu",
                            "{name, minutes, temp, temp_unit, rest}")
        extra = set(d) - {"name", "minutes", "temp", "temp_unit",
                          "rest"}
        if extra:
            raise OvenError(
                where, "champs inconnus %s — le four ne devine pas "
                       "ce que vous vouliez dire par là"
                       % sorted(extra),
                "only name, minutes, temp, temp_unit, rest")
        name = d.get("name")
        if not isinstance(name, str) or not name.strip():
            raise OvenError(where + ".name", "nom absent — un "
                            "conflit sans nom est un conflit sans "
                            "preuve", "non-empty string")
        if len(name) > 60:
            raise OvenError(where + ".name", "60 caractères max",
                            "short label")
        minutes = _int(d.get("minutes"), where + ".minutes", 1,
                       MAX_MINUTES)
        # — temp ET unit séparés, les deux obligatoires, messages
        # nommés (le refus du nombre nu est LA règle, pas un détail).
        temp_raw = d.get("temp")
        unit_raw = d.get("temp_unit")
        if temp_raw is None:
            raise OvenError(where + ".temp", "absent",
                            "integer degrees")
        ts = str(temp_raw).strip()
        if "." in ts.lower() or "e" in ts.lower():
            raise OvenError(where + ".temp",
                            "degré fractionnaire refusé", "integer")
        try:
            temp_val = int(ts)
        except ValueError:
            raise OvenError(where + ".temp", "entier attendu",
                            "integer degrees")
        if unit_raw is None:
            raise OvenError(
                where + ".temp_unit",
                "%s SANS UNITÉ refusé — c'est pile ou face entre "
                "%.1f °C et %.1f °F : la moitié des tables du monde "
                "brûle, l'autre sert cru" % (
                    ts, (temp_val - 32) * 5 / 9.0, temp_val * 9 / 5.0
                    + 32),
                "F or C, next to the number")
        unit = str(unit_raw).strip().upper()
        if unit not in ("F", "C"):
            raise OvenError(where + ".temp_unit",
                            "unités publiées : F et C", "F or C")
        temp_f = temp_val if unit == "F" else _c_to_f(temp_val)
        raw_rest = d.get("rest")
        rest = 0 if raw_rest is None else _int(
            raw_rest, where + ".rest", 0, 10**9)
        if rest > MAX_REST:
            raise OvenError(
                where + ".rest",
                "plus de 120 minutes de repos HORS four = zone de "
                "danger FSIS — « discard … left out longer than 2 "
                "hours » : la règle de /food/leftovers vaut ici, "
                "refroidir au frigo n'est pas reposer",
                "0..%d minutes" % MAX_REST)
        parsed.append({"name": name.strip(), "minutes": minutes,
                       "temp_f": temp_f, "temp_in": temp_val,
                       "unit_in": unit, "rest": rest})

    # — calcul À REBOURS : le dernier plat doit être prêt à serve ;
    # chaque plat sort au plus tard min(serve - son repos, entrée du
    # suivant moins l'ajustement de température s'il y en a un).
    cursor = serve
    schedule = [None] * len(parsed)  # rempli de la fin vers le début
    for i in range(len(parsed) - 1, -1, -1):
        d = parsed[i]
        # dernière borne de sortie : prêter attention AU PLAT D'APRÈS
        # (déjà calculé) — sortie du courant ≤ entrée du suivant moins
        # l'ajustement de température (preheat) si consigne différente.
        out = serve - timedelta(minutes=d["rest"])
        if i < len(parsed) - 1:
            nxt = schedule[i + 1]
            out = min(out, nxt["in"] - timedelta(
                minutes=(preheat if nxt["temp_f"] != d["temp_f"]
                         else 0)))
        inn = out - timedelta(minutes=d["minutes"])
        cursor = inn
        schedule[i] = {"out": out, "in": inn, "temp_f": d["temp_f"],
                       "rest": d["rest"], "minutes": d["minutes"],
                       "name": d["name"]}

    oven_on = (schedule[0]["in"] - timedelta(minutes=preheat)
               if preheat else schedule[0]["in"])

    out_dishes, transitions, conflicts = [], [], 0
    for i, s in enumerate(schedule):
        d = parsed[i]
        entry = {
            "name": s["name"],
            "in_at": s["in"].isoformat(),
            "out_at": s["out"].isoformat(),
            "ready_at": (s["out"] + timedelta(minutes=s["rest"]))
                        .isoformat(),
            "minutes": s["minutes"],
            "rest_minutes": s["rest"],
            "hold_minutes": max(
                0, int((serve - s["out"] - timedelta(
                    minutes=s["rest"])).total_seconds() // 60)),
            "temp": d["temp_in"],
            "temp_unit_in": d["unit_in"],
            "temp_f": d["temp_f"],
        }
        out_dishes.append(entry)
        if i + 1 < len(schedule):
            n = schedule[i + 1]
            if n["temp_f"] != s["temp_f"]:
                gap = int((n["in"] - s["out"]).total_seconds() // 60)
                t = {"after": s["name"], "from_f": s["temp_f"],
                     "to_f": n["temp_f"], "gap_minutes": gap,
                     "adjust_applied_minutes": preheat}
                if gap == 0:
                    t["conflict"] = ("no_gap_temp_change — le plat "
                                     "suivant ENTRE à l'instant où "
                                     "celui-ci SORT, à une autre "
                                     "consigne : la physique refuse,"
                                     " passe preheat ou réordonne")
                    conflicts += 1
                transitions.append(t)

    res = {
        "serve_at": serve.isoformat(),
        "oven_on_at": oven_on.isoformat(),
        "model": MODEL,
        "dishes": out_dishes,
        "oven_minutes": sum(d["minutes"] for d in out_dishes),
        "transitions": transitions,
        "temp_conflicts": conflicts,
        "preheat_minutes": preheat,
        "below_fsis_poultry_floor": sorted(
            {d["name"] for d in out_dishes
             if Fraction(str(d["temp_f"])) < FSIS_FLOOR_F}),
        "source": SOURCE,
    }
    if earliest is not None:
        short = int((earliest - oven_on).total_seconds() // 60)
        res["feasibility"] = {
            "earliest_start": earliest.isoformat(),
            "compared_to": "oven_on_at — l'allumage est la "
                           "contrainte murale, pas l'entrée du plat",
            "feasible": short <= 0,
            "short_by_minutes": max(0, short),
        }
    return res
