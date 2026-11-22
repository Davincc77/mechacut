"""discountkit — /money/discount : le compte que la caisse ne fera pas.

Deux arnaques d'arithmétique quotidienne, rendues impossibles :
  1. « -30 % PUIS -20 % » n'est PAS -50 %. Les remises s'enchaînent en
     facteurs multiplicatifs successifs : 0,70 × 0,80 = 0,56 → 44 %.
  2. L'ORDRE des paliers change le total quand un palier est en montant
     fixe. -30 % puis -5 EUR ≠ -5 EUR puis -30 %. La machine calcule
     les deux et LE DIT, au lieu de propager l'ordre saisi au clavier.

Tout en Decimal, borne par borne ; la FORMULE est rendue dans la réponse
(pas de boîte noire) ; le pourcentage effectif est calculé sur les
facteurs bruts avant tout arrondi monétaire, et l'arrondi final est
déclaré (HALF_UP à 2 décimales — la caisse, pas la banque).

Règles fermées du palier :
  percent  {"type":"percent","value":"30"}      → × (1 - 30/100)
  fixed    {"type":"fixed","value":"5"}         → - 5 (devise)
  buy2pay1 {"type":"buy2pay1"} + qty            → on paie ceil(qty/2)
"""
import itertools
import math
from decimal import Decimal, ROUND_HALF_UP

TWO = Decimal("0.01")


class DiscountError(Exception):
    pass


def _d(x, what):
    try:
        return Decimal(str(x))
    except Exception:
        raise DiscountError("%s must be a number, got %r" % (what, x))


def _step(step, price, qty):
    t = (step or {}).get("type")
    if t == "percent":
        v = _d(step.get("value"), "percent value")
        if not (Decimal(0) < v <= Decimal(100)):
            raise DiscountError("percent must be in (0,100]")
        return price * (Decimal(100) - v) / Decimal(100), \
            "×(1 - %s/100)" % format(v, "f")
    if t == "fixed":
        v = _d(step.get("value"), "fixed value")
        if v < 0:
            raise DiscountError("fixed must be >= 0")
        out = price - v * qty if step.get("per_unit") else price - v
        return out, "- %s%s" % (format(v, "f"), " per unit"
                                if step.get("per_unit") else "")
    if t == "buy2pay1":
        if not isinstance(qty, int) or qty < 2:
            raise DiscountError("buy2pay1 needs qty >= 2")
        paid = math.ceil(qty / 2)
        return (price / qty) * paid, "paie %d sur %d (ceil(qty/2))" % (
            paid, qty)
    raise DiscountError("unknown step type %r — closed set: "
                        "percent, fixed, buy2pay1" % t)


def discount_chain(price, steps, qty=1, currency=None):
    p0 = _d(price, "price")
    if p0 <= 0:
        raise DiscountError("price must be > 0")
    if not steps or not isinstance(steps, list):
        raise DiscountError("steps: non-empty list of "
                            "{type:percent|fixed|buy2pay1, value}")
    if qty < 1:
        raise DiscountError("qty must be >= 1")
    gross = p0 * qty
    ledger = []
    running = gross
    for i, st in enumerate(steps):
        running, how = _step(st, running, qty)
        if running < 0:
            raise DiscountError("step %d (%s) drives the total below "
                                "zero — refused, not clipped in silence"
                                % (i + 1, how))
        ledger.append({"step": i + 1, "rule": st.get("type"),
                       "how": how, "running_total": str(
                           running.quantize(TWO, rounding=ROUND_HALF_UP))})
    after = running.quantize(TWO, rounding=ROUND_HALF_UP)
    saved = gross - running
    eff = (Decimal(1) - running / gross) * 100
    out = {"currency": currency, "unit_price": str(p0), "qty": qty,
           "gross_total": str(gross.quantize(TWO)),
           "final_total": str(after),
           "saved": str(saved.quantize(TWO, rounding=ROUND_HALF_UP)),
           "effective_discount_pct": str(eff.quantize(
               Decimal("0.01"), rounding=ROUND_HALF_UP)),
           "naive_sum_pct": None, "ledger": ledger,
           "formula": "chain = successive multiplicative factors; "
                      "effective % computed on raw factors before any "
                      "money rounding; final HALF_UP to 2 dp"}
    # l'addition naïve des pourcentages — pour dénoncer l'écart
    out["order_matters"] = False   # que des facteurs : commutatif
    percents = [Decimal(str(s.get("value", "0"))) for s in steps
                if s.get("type") == "percent"]
    if len(percents) >= 2:
        naive = sum(percents, Decimal(0))
        out["naive_sum_pct"] = str(naive.quantize(TWO))
        out["percent_lie_delta"] = str((naive - eff).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP))
    # ordre : si des paliers fixed existent, tester les permutations
    if len(steps) > 1 and any(s.get("type") == "fixed" for s in steps):
        best, worst = None, None
        variants = []
        for perm in itertools.permutations(range(len(steps))):
            run = gross
            ok = True
            for idx in perm:
                try:
                    run, _ = _step(steps[idx], run, qty)
                except DiscountError:
                    ok = False
                    break
            if not ok or run < 0:
                continue
            variants.append((run, list(perm)))
        if variants:
            vals = sorted(v[0] for v in variants)
            spread = (vals[-1] - vals[0]).quantize(TWO)
            out["order_matters"] = spread != 0
            if spread != 0:
                lo = min(variants, key=lambda v: v[0])
                out["best_step_order_for_you"] = [i + 1 for i in lo[1]]
                out["order_spread"] = str(spread)
    return out
