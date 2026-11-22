"""formulakit — /api/v1/formula : le catalogue de formules (F4, palier 1).

La douleur (benchs v12-v14 + r/ChatGPT NYT Cooking) : les modèles
CONNASSENT les formules et les exécutent mal — mauvaise base de log,
sens inversé, arrondi d'humeur. Le catalogue retourne la formule PUBLIÉE,
sa SUBSTITUTION avec les nombres de l'appelant, et le résultat EXACT
(Fraction de bout en bout, rendu Decimal à chiffres déclarés).

Architecture verrouillée (l’opérateur 22-11) : UN moteur, des enregistrements
déclaratifs — jamais un endpoint par formule. Une formule = nom, source,
texte, args (unités EN ARGUMENTS), solve_for fermé, fn pure, arrondi
déclaré, scope_note si le domaine touche santé/finance.

Palier 1 = arithmétique pure par construction : AUCUNE constante
(π, CODATA viendront au palier STEM avec leurs chiffres publiés et
leur assertion de précision). Tout est fractionnaire : le résultat est
exact avant l'arrondi, et l'arrondi est dit.
"""
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from datetime import date, timedelta

F = Fraction


def _fr(x):
    return F(Decimal(str(x)))


def _q(fr, digits):
    d = Decimal(fr.numerator) / Decimal(fr.denominator)
    q = Decimal(1).scaleb(-digits) if digits > 0 else Decimal(1)
    return str(d.quantize(q, rounding=ROUND_HALF_UP))


def _subst(parts):
    return " ".join(parts)


def _need(args, names):
    missing = [n for n in names if n not in args or args[n] in (None, "")]
    if missing:
        raise KeyError(",".join(missing))
    return [args[n] for n in names]


def _solve_pick(args, names, solve_for):
    """names moins solve_for = les connus ; solve_for doit être dans
    l'enum fermée de l'enregistrement (vérifié à l'appel)."""
    if solve_for not in names:
        raise KeyError("solve_for:" + "|".join(names))
    known = [n for n in names if n != solve_for]
    vals = _need(args, known)
    return dict(zip(known, vals)), solve_for


def _f_percent(args):
    mode = args.get("mode", "apply")
    p = _fr(_need(args, ["percent"])[0])
    if mode == "apply":
        b = _fr(_need(args, ["base"])[0])
        final_up = b * (1 + p / 100)
        final_down = b * (1 - p / 100)
        back_up = (b * (1 + p / 100)) * (1 - p / 100)
        gap = (1 - back_up / b) * 100 if b != 0 else F(0)
        direction = args.get("direction", "up")
        result = final_up if direction == "up" else final_down
        return (_subst([direction, str(p), "% on", str(b), "=",
                        str(result)]),
                {"result": _q(result, 2), "units": args.get("units", ""),
                 "roundtrip_after_inverse_pct": _q(gap, 2),
                 "roundtrip_note": "the SAME percent back does not land "
                                   "on base — the gap is real and "
                                   "declared, not rounding"})
    if mode == "original":
        fin = _fr(_need(args, ["final"])[0])
        d2 = args.get("direction", "up")
        factor = 1 + p / 100 if d2 == "up" else 1 - p / 100
        orig = fin / factor
        return ("%s of %s%% leads to %s → original = %s"
                % (d2, str(p), str(fin), _q(orig, 6)),
                {"result": _q(orig, 2)})
    raise KeyError("mode:apply|original")


def _f_rule_of_three(args):
    a, b, c = _need(args, ["a", "b", "c"])
    x = _fr(b) * _fr(c) / _fr(a)
    return ("%s:%s = %s:? → ? = %s × %s ÷ %s = %s"
            % (a, b, c, b, c, a, _q(x, 8)),
            {"result": _q(x, 2)})


def _f_speed(args):
    known, target = _solve_pick(
        args, ["distance", "time_hours", "speed"],
        args.get("solve_for", "speed"))
    if "distance" not in known and "time_hours" in known:
        val = _fr(known["speed"]) * _fr(known["time_hours"])
        sub = "d = v × t"
    elif "speed" not in known:
        val = _fr(known["distance"]) / _fr(known["time_hours"])
        sub = "v = d ÷ t"
    else:
        val = _fr(known["distance"]) / _fr(known["speed"])
        sub = "t = d ÷ v"
    return (sub + " → %s" % target, {"result": _q(val, 2),
                                     "units": {"distance": "km",
                                               "speed": "km/h",
                                               "time_hours": "h"}[target]})


def _f_fuel(args):
    litres, km = _need(args, ["litres", "km"])
    l100 = _fr(litres) * 100 / _fr(km)
    kml = _fr(km) / _fr(litres)
    return ("L/100km = %s×100÷%s ; km/L = %s÷%s" % (litres, km, km, litres),
            {"result_l_per_100km": _q(l100, 2),
             "result_km_per_l": _q(kml, 2)})


def _f_pace(args):
    minutes, km = _need(args, ["total_minutes", "km"])
    pace = _fr(minutes) / _fr(km)
    whole = int(pace)
    secs = int((pace - whole) * 60)
    return ("pace = %s ÷ %s" % (minutes, km),
            {"result_min_per_km": _q(pace, 2),
             "result_mmss": "%d:%02d" % (whole, secs)})


def _f_dilution(args):
    names = ["c1", "v1", "c2", "v2"]
    target = args.get("solve_for", "v1")
    if target not in names:
        raise KeyError("solve_for:c1|v1|c2|v2")
    missing = [n for n in names if n != target and
               (n not in args or args[n] in (None, ""))]
    if missing:
        raise KeyError(",".join(missing))
    k = {n: _fr(args[n]) for n in names if n != target}
    if target == "c1":
        val = k["c2"] * k["v2"] / k["v1"]
    elif target == "v1":
        val = k["c2"] * k["v2"] / k["c1"]
    elif target == "v2":
        val = k["c1"] * k["v1"] / k["c2"]
    else:
        val = k["c1"] * k["v1"] / k["v2"]
    return ("C1×V1 = C2×V2 → solve %s" % target,
            {"result": _q(val, 4)})


def _f_dosage(args):
    mgkg, kg = _need(args, ["mg_per_kg", "weight_kg"])
    dose = _fr(mgkg) * _fr(kg)
    return ("dose = %s mg/kg × %s kg" % (mgkg, kg),
            {"result": _q(dose, 3), "units": "mg",
             "scope_note": "arithmetic only: the DOSE is prescribed by "
                           "a professional, this endpoint only "
                           "multiplies the two numbers you gave"})


def _f_bakers(args):
    mode = args.get("mode", "hydration")
    if mode == "hydration":
        water, flour = _need(args, ["water_g", "flour_g"])
        h = _fr(water) / _fr(flour) * 100
        return ("hydration = %s ÷ %s × 100" % (water, flour),
                {"result_pct": _q(h, 2)})
    if mode == "water_for":
        flour, h = _need(args, ["flour_g", "hydration_pct"])
        w = _fr(flour) * _fr(h) / 100
        return ("water = %s × %s%%" % (flour, h),
                {"result_g": _q(w, 2)})
    if mode == "flour_for":
        water, h = _need(args, ["water_g", "hydration_pct"])
        fl = _fr(water) / (_fr(h) / 100)
        return ("flour = %s ÷ (%s%%)" % (water, h),
                {"result_g": _q(fl, 2)})
    raise KeyError("mode:hydration|water_for|flour_for")


def _f_naegle(args):
    lmp = _need(args, ["lmp"])[0]
    d0 = date.fromisoformat(lmp)
    via280 = d0 + timedelta(days=280)
    # variante publiée d'ACOG : +7 jours, -3 mois, +1 an — DEUX chemins
    # de calcul indépendants ; la réponse n'est rendue que s'ils tombent
    # sur la MÊME date, sinon refus nommé (aucun arbitraire silencieux).
    y, m, dd = d0.year, d0.month - 3, d0.day
    if m <= 0:
        m += 12
        y -= 1
    try:
        via_rule = (date(y, m, min(dd, 28) if m == 2 else dd)
                    + timedelta(days=7)
                    + timedelta(days=(366 if (y % 4 == 0 and
                                             (y % 100 != 0 or
                                              y % 400 == 0)) else 365)))
    except ValueError:
        via_rule = None
    if via_rule is None or via_rule != via280:
        # les deux définitions divergent sur certains bords (fin de mois
        # de février) : on REND celle des 280 jours — la définition
        # primaire — et on DÉCLARE l'écart, jamais on ne la cache.
        return ("EDD = LMP + 280 days", {
            "result": via280.isoformat(),
            "scope_note": "obstetric dating is clinical; LMP+280 is the "
                          "published rule, ultrasound dating overrides "
                          "it",
            "note": "the alternative formulation (+7d −3m +1y) differs "
                    "for this date — both shown, never silently merged",
            "alternative_result": (via_rule.isoformat()
                                   if via_rule else "n/a")})
    return ("EDD = LMP + 280 days (= +7j −3m +1an vérifié)",
            {"result": via280.isoformat(),
             "scope_note": "obstetric dating is clinical; LMP+280 is the "
                           "published rule, ultrasound dating overrides "
                           "it"})


def _f_area(args):
    shape = args.get("shape", "rectangle")
    if shape == "rectangle":
        l, w = _need(args, ["length", "width"])
        return ("A = l × w", {"result": _q(_fr(l) * _fr(w), 4)})
    if shape == "triangle":
        b, h = _need(args, ["base", "height"])
        return ("A = b × h ÷ 2", {"result": _q(_fr(b) * _fr(h) / 2, 4)})
    if shape == "trapezoid":
        a1, a2, h = _need(args, ["parallel_a", "parallel_b", "height"])
        s = (_fr(a1) + _fr(a2)) / 2 * _fr(h)
        return ("A = (a+b)/2 × h", {"result": _q(s, 4)})
    raise KeyError("shape:rectangle|triangle|trapezoid "
                   "(circle needs π — palier STEM, constants with "
                   "published digits)")


def _f_box(args):
    l, w, h = _need(args, ["length", "width", "height"])
    return ("V = l × w × h", {"result": _q(_fr(l) * _fr(w) * _fr(h), 4)})


def _f_share(args):
    mode = args.get("mode", "share")
    if mode == "share":
        part, whole = _need(args, ["part", "whole"])
        s = _fr(part) / _fr(whole) * 100
        return ("share = %s ÷ %s × 100" % (part, whole),
                {"result_pct": _q(s, 2)})
    if mode == "part_of":
        whole, pct = _need(args, ["whole", "pct"])
        p = _fr(whole) * _fr(pct) / 100
        return ("part = %s × %s%%" % (whole, pct),
                {"result": _q(p, 2)})
    raise KeyError("mode:share|part_of")


CATALOG = {
    "percent_up_down": dict(
        fn=_f_percent,
        formula="final = base × (1 ± pct/100)",
        source="elementary percent arithmetic; round-trip gap is exact "
               "Fraction math",
        args="base, percent, direction up|down, mode apply|original, "
             "units?, final?",
        summary="augmenter/diminuer un pourcentage, trouver l'original, "
                "et le trou réel du aller-retour"),
    "rule_of_three": dict(
        fn=_f_rule_of_three,
        formula="a:b = c:x → x = b × c ÷ a",
        source="rule of three (Euclid VII.19; every primary-school "
               "textbook)",
        args="a, b, c",
        summary="proportionnalité directe exacte"),
    "speed": dict(
        fn=_f_speed,
        formula="v = d ÷ t ; d = v × t ; t = d ÷ v",
        source="constant-speed kinematics, definition of speed",
        args="solve_for speed|distance|time_hours + any two of them",
        summary="vitesse, distance ou durée — au choix la cible"),
    "fuel_l100": dict(
        fn=_f_fuel,
        formula="L/100km = litres × 100 ÷ km ; km/L = km ÷ litres",
        source="consumption definitions (EU label convention L/100 km)",
        args="litres, km",
        summary="consommation dans LES DEUX sens, même appel"),
    "average_pace": dict(
        fn=_f_pace,
        formula="pace = total_minutes ÷ km",
        source="running pace definition (World Athletics conventions)",
        args="total_minutes, km",
        summary="allure moyenne en min/km ET en mm:ss"),
    "dilution_c1v1": dict(
        fn=_f_dilution,
        formula="C1 × V1 = C2 × V2",
        source="dilution equation, standard laboratory arithmetic",
        args="solve_for c1|v1|c2|v2 + the three known",
        summary="dilutions : la bonne inconnue parmi quatre"),
    "dosage_mg_kg": dict(
        fn=_f_dosage,
        formula="dose = mg_per_kg × weight_kg",
        source="weight-based dose arithmetic (the PRESCRIPTION is "
               "clinical, the multiplication is not)",
        args="mg_per_kg, weight_kg",
        summary="mg/kg × kg, avec le scope_note qui renvoie à "
                "l'humain compétent"),
    "bakers_hydration": dict(
        fn=_f_bakers,
        formula="hydration% = water ÷ flour × 100 (baker's percentages)",
        source="baker's percentage convention (flour = 100%)",
        args="mode hydration|water_for|flour_for + water_g, flour_g, "
             "hydration_pct",
        summary="levain et pain : les trois questions, un enregistrement"),
    "naegle_due_date": dict(
        fn=_f_naegle,
        formula="EDD = LMP + 280 days",
        source="Naegele's rule, ACOG committee opinion 700 (2017)",
        args="lmp (YYYY-MM-DD)",
        summary="date prévue d'accouchement — les DEUX formulations "
                "calculées, l'écart déclaré"),
    "area_shapes": dict(
        fn=_f_area,
        formula="rectangle l×w · triangle b×h÷2 · trapèze (a+b)/2×h",
        source="Euclidean area formulas (elements, book II/VI)",
        args="shape + its dimensions (cercle = palier STEM, il faut π)",
        summary="surfaces rationnelles — peintre, jardin, parquet"),
    "share_pct": dict(
        fn=_f_share,
        formula="share% = part ÷ whole × 100 ; part = whole × pct/100",
        source="percentage of a total (elementary statistics)",
        args="mode share|part_of + part, whole | whole, pct",
        summary="184 sur 460, c'est combien % — et l'inverse "
                "(distinct de money/discount : ici une PART, pas un "
                "prix qui bouge)"),
    "volume_box": dict(
        fn=_f_box,
        formula="V = l × w × h",
        source="cuboid volume, definition",
        args="length, width, height",
        summary="le volume du carton, de la piscine, du terrarium"),
}

# La règle de trois du prix (12ᵉ) : le pourcentage sur prix EST déjà
# money/discount — le catalogue ne le duplique PAS, il y POINTE.
CROSS_REFS = {"money/discount": "chaînes de remises sur prix "
               "(money/discount fait le travail, avec l'impact d'ordre)"}


def formula_index():
    return {"formulas": sorted(
        [{"name": n, "formula": r["formula"], "source": r["source"],
          "args": r["args"], "summary": r["summary"]}
         for n, r in CATALOG.items()], key=lambda f: f["name"]),
        "cross_refs": CROSS_REFS,
        "doctrine": "one engine, declarative records — adding a formula "
                    "is a registry row + its hand-computed vectors, "
                    "never a new endpoint. Palier 1 carries NO "
                    "constants by construction (π and CODATA arrive in "
                    "the STEM palier with their published digits and a "
                    "precision assertion). Results are exact Fractions "
                    "rendered to DECLARED decimals."}


def run_formula(name, args):
    if name not in CATALOG:
        raise KeyError("name:" + "|".join(sorted(CATALOG)))
    rec = CATALOG[name]
    sub, out = rec["fn"](args or {})
    out.update({"formula": name, "substitution": sub,
                "source": rec["source"]})
    return out
