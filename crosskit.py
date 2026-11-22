"""crosskit — /api/v1/money/crossover : le prix de reviens des tarifs à
DEUX COMPOSANTES (prix unitaire + fixe), rendu EXACT.

La formule est publiée (uktaxdrag, toolfoundry, rightsums, gasbill-
calculator, solaxyra, expatcalc, energysolutions — sept calculateurs
rejoués le 22-nov-2026) :

    coût annuel = conso × prix_unitaire + 365 × fixe_journalier
    bascule     = Δ fixe annualisé ÷ Δ prix_unitaire

ET CES SEPT PAGES SE CONTREDISENT SUR L'ARRONDI : gasbill arrondit le
Δ fixe à £19,42 puis divise → « about 4 623 kWh » ; le calcul exact
(0,0532×365)÷0,0042 = 4 623⅓ kWh. rightsums tronque −90,6295 en
« −£90,63 » avant de diviser. ICI, DECIMAL NE QANTIZE JAMAIS AVANT LA
DERNIÈRE OPÉRATION : la bascule est rendue en fraction EXACTE
(numerator/denominator) plus sa valeur décimale ; l'arrondi
intermédiaire de la presse est nommément ce qu'on ne fait pas.

Les CONVENTIONS DE JOURS sont un argument, jamais un choix muet :
« ×365 » (uktaxdrag, la règle) vs « ×30 jours par mois » (certains
calculateurs) ne sont PAS la même arithmétique — ici un fixe MENSUEL
est annualisé par ×12 EXACT (12 mois ≠ 360 jours), un fixe JOURNALIER
par ×days_per_year (défaut 365, override nommé 366 = année bissextile),
et « per week » est REFUSÉ par le nom : pas de conversion exacte
semaine→année. C'est LA divergence que deux calculateurs publiés
(myenergytoolkit ×30 vs uxtaxdrag ×365) se disputent sans la nommer.

La DOMINATION est une réponse, pas un vide : si un plan gagne sur les
DEUX composantes, aucune bascule positive n'existe — « never » est
rendu NOMMÉ. Branches voisines : prix unitaires égaux (aucun
arbitrage possible : le fixe gagne à toute conso), fixes égaux (bascule
à zéro : le prix unitaire gagne dès le premier kWh), tout égal
(identiques — seuls les frais one-off peuvent encore distinguer).

Unités : Wh/kWh/MWh normalisés sur kWh par facteurs EXACTS (SI) ;
toute AUTRE unité identique des deux côtés (GB, seat, item…) passe
telle quelle, la bascule est rendue dans cette unité. Les KM ne sont
calculés que si la consommation par unité est FOURNIE (normcalc) —
jamais devinée. Frais (exit/sign-up/credit) : une fois par scénario,
ils déplacent le PAYBACK en mois, pas la bascule structurelle — les
deux sont rendus séparément (uktaxdrag : « net first-year saving » est
une formule distincte du break-even kWh).

Zéro fetch, zéro prix du kWh inventé : tout est argument. Ce n'est pas
un conseil tarifaire — c'est l'arithmétique exacte de VOS nombres.
"""

from decimal import Decimal, getcontext, ROUND_HALF_UP
from fractions import Fraction

from money import ISO_DECIMALS

getcontext().prec = 30

# facteurs EXACTS vers kWh (SI : 10^3 et 10^6, pas de mémoire)
_UNIT_TO_KWH = {"Wh": Decimal("0.001"), "kWh": Decimal(1),
                "MWh": Decimal("1000")}
_FIXED_PER = {"day", "month", "year"}


class CrossError(ValueError):
    def __init__(self, field, message, expected=None):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected or _EXPECTED.get(field, "")


_EXPECTED = {
    "a_unit_rate": "decimal string in MAJOR currency units per unit, "
                   "e.g. '0.30' (24,5 p/kWh = '0.245' with currency GBP)",
    "a_unit_per": "'kWh', 'Wh' or 'MWh' — or ANY other unit string as "
                  "long as plan_b uses the SAME one (GB, seat, item…)",
    "a_fixed": "decimal string of the recurring fixed charge, e.g. '12'",
    "a_fixed_per": "'day', 'month' or 'year' — 'week' is REFUSED: no "
                   "exact weeks-per-year conversion exists",
    "b_unit_rate": "same contract as a_unit_rate",
    "b_unit_per": "must equal a_unit_per (a crossover between kWh and "
                  "MWh tariffs is undefined)",
    "b_fixed": "same contract as a_fixed",
    "b_fixed_per": "same contract as a_fixed_per",
    "currency": "ISO code from the closed table (EUR, GBP, USD, BRL…)",
    "days_per_year": "'365' (default) or '366' for a named leap year — "
                     "monthly fixeds always use ×12 exact, never 30-day "
                     "months",
    "usage_per_period": "your consumption as a decimal string, paired "
                        "with usage_period; costs compare AT that usage",
    "usage_period": "'month' or 'year' (default 'year')",
    "km_per_unit": "decimal km (or mi) per unit, e.g. '6' — the crossover "
                   "is converted to distance ONLY if supplied",
    "exit_fee_a": "one-off fee to leave plan A (first-year only; moves "
                  "the payback, never the structural crossover)",
    "exit_fee_b": "one-off fee to leave plan B",
    "sign_up_a": "one-off joining fee for plan A",
    "sign_up_b": "one-off joining fee for plan B",
}


def _num(value, field):
    if not isinstance(value, str) or not value.strip():
        raise CrossError(field, "missing or empty (pass a decimal string)")
    t = value.strip().replace("\u00A0", "").replace(" ", "").replace("_", "")
    t = t.replace(",", ".")
    import re
    if not re.match(r"^[+-]?(\d+(\.\d*)?|\.\d+)$", t):
        raise CrossError(field, "not a decimal number: %r" % value)
    return Decimal(t)


def _pos(value, field):
    d = _num(value, field)
    if d < 0:
        raise CrossError(field, "negative rates/fees are not tariffs — "
                                "pass credits as sign_up/exit fees")
    return d


def _q(value, places):
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def _money(d, dec):
    return format(_q(d, dec), "f")   # devise à décimales FIXES, jamais


def _dec_str(d):
    s = format(d.normalize(), "f")
    if s in ("-0", "-0.0", "-0.00"):
        s = s.lstrip("-")
    return s


def _frac(fr):
    return {"numerator": str(fr.numerator),
            "denominator": str(fr.denominator)}


def run_crossover(args):
    currency = (args.get("currency") or "").strip().upper()
    if currency not in ISO_DECIMALS:
        raise CrossError("currency", "unknown ISO code %r (closed table "
                         "of %d majors)" % (args.get("currency"),
                                            len(ISO_DECIMALS)))
    dec = ISO_DECIMALS[currency]

    a_per = (args.get("a_unit_per") or "").strip()
    b_per = (args.get("b_unit_per") or "").strip()
    if not a_per or not b_per:
        raise CrossError("a_unit_per", "both plans need an explicit unit "
                         "(kWh / Wh / MWh or any matching unit)")
    if a_per != b_per:
        raise CrossError("b_unit_per", "units differ (%r vs %r): no "
                         "crossover is defined between different units"
                         % (a_per, b_per))
    a_rate = _pos(args.get("a_unit_rate"), "a_unit_rate")
    b_rate = _pos(args.get("b_unit_rate"), "b_unit_rate")

    a_fp = (args.get("a_fixed_per") or "").strip().lower()
    b_fp = (args.get("b_fixed_per") or "").strip().lower()
    for fp, fld in ((a_fp, "a_fixed_per"), (b_fp, "b_fixed_per")):
        if fp == "week":
            raise CrossError(fld, "'week' is REFUSED: no exact weeks-per-"
                             "year conversion exists — pass the fixed as "
                             "day, month or year")
        if fp not in _FIXED_PER:
            raise CrossError(fld, "must be 'day', 'month' or 'year', "
                             "got %r" % args.get(fld))
    a_fixed = _pos(args.get("a_fixed"), "a_fixed")
    b_fixed = _pos(args.get("b_fixed"), "b_fixed")

    dpy = Decimal(365)
    if args.get("days_per_year"):
        raw = args["days_per_year"].strip()
        if raw not in ("365", "366"):
            raise CrossError("days_per_year", "must be '365' or '366' "
                             "(named leap year), got %r" % raw)
        dpy = Decimal(raw)

    def annualize(fixed, per):
        if per == "day":
            return fixed * dpy
        if per == "month":
            return fixed * Decimal(12)   # 12 mois EXACTS, jamais 30×12 j
        return fixed

    a_fix_y = annualize(a_fixed, a_fp)
    b_fix_y = annualize(b_fixed, b_fp)

    scale = _UNIT_TO_KWH.get(a_per, Decimal(1))
    out_units = "kWh" if a_per in _UNIT_TO_KWH else a_per

    # Algèbre figée : d_fix = fixe A − fixe B (annualisé) ;
    # d_unit = unitaire B − unitaire A (positif ⇒ A gagne au-delà).
    # Bascule u* = d_fix ÷ d_unit (coûts égaux en u*).
    d_fix = a_fix_y - b_fix_y
    d_unit = b_rate - a_rate

    crossover = None
    fraction = None
    per_month = None
    if d_unit == 0:
        if d_fix == 0:
            verdict = {"kind": "identical-structure",
                       "rule": "same unit rate AND same annualised fixed "
                               "— the two tariffs are arithmetically one; "
                               "only one-off fees can still differ "
                               "(compared below if supplied)"}
        else:
            winner = "plan_a" if d_fix < 0 else "plan_b"
            verdict = {"kind": "no-tradeoff",
                       "winner_always": winner,
                       "rule": "equal unit rates: no usage can reverse "
                               "the ranking — the cheaper annualised "
                               "fixed wins at every consumption "
                               "(structural saving %s per year)"
                               % _dec_str(abs(d_fix))}
    elif d_fix == 0:
        winner = "plan_a" if d_unit > 0 else "plan_b"
        crossover = Decimal(0)
        fraction = _frac(Fraction(0))
        verdict = {"kind": "immediate-crossover",
                   "winner_above_zero": winner,
                   "rule": "equal annualised fixed: the crossover is at "
                           "ZERO — the lower unit rate wins from the "
                           "first %s" % out_units}
        per_month = Decimal(0)
    elif (d_fix > 0) == (d_unit > 0):
        # u* > 0 : vrai point de bascule
        fr = (Fraction(d_fix) / Fraction(d_unit)) * Fraction(scale)
        crossover = Decimal(fr.numerator) / Decimal(fr.denominator)
        fraction = _frac(fr)
        lo = "plan_b" if d_fix > 0 else "plan_a"   # qui a le fixe bas
        hi = "plan_a" if d_unit > 0 else "plan_b"  # qui a l'unitaire bas
        verdict = {
            "kind": "crossover",
            "below_crossover": lo,
            "above_crossover": hi,
            "rule": "%s has the lower annualised fixed — it wins below "
                    "the point; %s has the lower unit rate — it wins "
                    "above" % (lo, hi),
        }
    else:
        # u* ≤ 0 : un plan gagne sur les DEUX composantes
        fr = Fraction(d_fix) / Fraction(d_unit)
        exact = Decimal(fr.numerator) / Decimal(fr.denominator)
        a_dom = a_fix_y <= b_fix_y and a_rate <= b_rate and \
            (a_fix_y < b_fix_y or a_rate < b_rate)
        who = "plan_a" if a_dom else "plan_b"
        verdict = {"kind": "domination",
                   "winner_always": who,
                   "signed_solution": _dec_str(exact.normalize()),
                   "rule": "the equation solves at a negative usage (%s "
                           "%s/year) — %s is cheaper on BOTH components, "
                           "so 'never' IS the answer"
                           % (_dec_str(exact.normalize()), out_units, who)}

    conv = {
        "days_per_year": _dec_str(dpy),
        "monthly_fixed_rule": "×12 exact months per year — a 30-day "
                              "month (×360) is a DIFFERENT published "
                              "convention, named here as rejected",
        "daily_fixed_rule": "×%s days per year (override "
                            "days_per_year='366' for a leap year)"
                            % _dec_str(dpy),
    }

    out = {
        "plans": {
            "a": {"unit_rate": _dec_str(a_rate), "unit_per": a_per,
                  "fixed": _dec_str(a_fixed), "fixed_per": a_fp,
                  "fixed_annualised": _dec_str(a_fix_y)},
            "b": {"unit_rate": _dec_str(b_rate), "unit_per": b_per,
                  "fixed": _dec_str(b_fixed), "fixed_per": b_fp,
                  "fixed_annualised": _dec_str(b_fix_y)},
            "currency": currency,
        },
        "verdict": verdict,
        "crossover": None,
        "exactness_note": "no intermediate rounding: published calculators "
                          "round the Δ fixed first (e.g. £19.42/0.0042 = "
                          "'about 4,623' where the exact answer is "
                          "4,623 1/3 kWh); the fraction rendered here is "
                          "the exact rule",
        "day_convention": conv,
    }

    if crossover is not None and verdict["kind"] == "crossover":
        out["crossover"] = {
            "per_year": _dec_str(crossover),
            "per_year_fraction": fraction,
            "per_month": _dec_str((crossover / Decimal(12)).normalize()),
            "unit": out_units,
        }
        if args.get("km_per_unit"):
            kpu = _pos(args["km_per_unit"], "km_per_unit")
            out["crossover"]["distance"] = {
                "per_unit_supplied": _dec_str(kpu),
                "distance_per_year": _dec_str((crossover * kpu).normalize()),
                "distance_per_month": _dec_str((crossover * kpu /
                                                Decimal(12)).normalize()),
                "rule": "distance = crossover × SUPPLIED km per unit — "
                        "never a guessed consumption",
            }

    if args.get("usage_per_period"):
        uper = (args.get("usage_period") or "year").strip().lower()
        if uper not in ("month", "year"):
            raise CrossError("usage_period", "must be 'month' or 'year', "
                             "got %r" % args.get("usage_period"))
        u = _pos(args["usage_per_period"], "usage_per_period")
        u_year = u * (Decimal(12) if uper == "month" else Decimal(1))

        def side(rate, fix_y):
            var = u_year * rate
            return {"variable": _dec_str(var.normalize()),
                    "fixed_annual": _money(fix_y, dec),
                    "total": _money(var + fix_y, dec)}
        ca, cb = side(a_rate, a_fix_y), side(b_rate, b_fix_y)
        diff = Decimal(ca["total"]) - Decimal(cb["total"])
        out["at_usage"] = {
            "usage": _dec_str(u), "usage_period": uper,
            "usage_annualised": _dec_str(u_year), "unit": out_units,
            "plan_a": ca, "plan_b": cb,
            "cheaper": "plan_a" if diff < 0 else ("plan_b" if diff > 0
                                                  else "tie"),
            "annual_difference": _money(abs(diff), dec),
            "currency": currency,
        }

        fees = {k: _pos(args[k], k) for k in
                ("exit_fee_a", "exit_fee_b", "sign_up_a", "sign_up_b")
                if args.get(k)}
        if fees:
            one_off_ab = fees.get("exit_fee_a", Decimal(0)) + \
                fees.get("sign_up_b", Decimal(0))
            one_off_ba = fees.get("exit_fee_b", Decimal(0)) + \
                fees.get("sign_up_a", Decimal(0))
            annual_diff = Decimal(ca["total"]) - Decimal(cb["total"])
            monthly = annual_diff / Decimal(12)

            def switch(one_off, saving):
                net = saving - one_off
                payback = None
                if one_off > 0 and monthly > 0:
                    payback = format(_q(one_off / monthly, 2), "f")
                elif one_off > 0 and monthly <= 0:
                    payback = "never"
                return {"one_off": _money(one_off, dec),
                        "net_first_year_saving": _money(net, dec),
                        "payback_months": payback}
            out["fees"] = {
                "a_to_b": switch(one_off_ab, annual_diff),
                "b_to_a": switch(one_off_ba, -annual_diff),
                "rule": "uktaxdrag distinction: net first-year saving = "
                        "annual diff − exit fee + credit — fees move the "
                        "PAYBACK, never the structural crossover; "
                        "both switches are rendered side by side",
            }

    out["scope_note"] = ("your numbers, our arithmetic: no fetched "
                         "prices, no invented rates, no tariff advice — "
                         "the crossover is exact Decimal with the day "
                         "convention named; VAT and scope assumptions "
                         "stay inside the inputs you supply")
    return out
