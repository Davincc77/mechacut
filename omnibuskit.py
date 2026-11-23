"""omnibuskit — /shop/discount-audit : le prix barré est-il LÉGAL ?

La règle des 30 jours, rendue en arithmétique close. Specs publiées,
citées avec chaque verdict :
- Directive (UE) 2019/2161 art. 6a (modifiant 98/6/CE) : « previous
  price » = le prix le plus BAS appliqué par le commerçant durant une
  période d'au moins 30 jours avant la réduction.
- CJEU C-330/23 (Aldi Süd) : le pourcentage ET le prix barré doivent
  se référer à ce plus bas — une promo antérieure dans la fenêtre
  ABAISSE la référence, même si le prix est remonté depuis.
- PAngV §11(1)(2) DE : paliers progressifs sans interruption →
  référence = plus bas AVANT le premier palier de la campagne ;
  clause « moins de 30 jours de mise en vente » §11(3) DE.
- L112-1-3 conso FR : transposition, même clause de première remise
  et même clause de mise en vente récente.
- Preuves de la douleur : sweep Commission 26-mars-2026, 314
  commerçants contrôlés, 30 % de références mal posées ; UOKiK
  29-mai-2026 (H&M, P&C — jusqu'à 10 % du CA) ; OCU/Consumo
  23-nov-2026 (11 plateformes signalées, amendes jusqu'à 350 000 €).

Modèle de la history (publié dans la réponse) : une entrée = le
jour où le prix est POSÉ ; il court jusqu'à l'entrée suivante. La
fenêtre [anchor−30j, anchor) est auditée par les prix EN VIGUEUR :
le prix porté au début (dernière entrée ≤ start) plus toute entrée
dans la fenêtre. anchor = as_of, ou campaign_start pour la clause
progressive (de|fr).

Golds tracés main dans tests/test_bundle84.py — exemples PUBLICS
rejoués verbatim : 100→80 (week-end)→100→70 = 12,5 % pas 30 %
(wpdesk) ; casque 100, 80 dans le mois, BF 70 → 10 € économisés
(firstonline) ; palier progressif 100→80 (campagne dès le 20)→70 :
de dit 30 % légaux (fenêtre avant le premier palier), eu baseline
dit 12,5 % — le DÉSACCORD de transposition est RENDU nommé, jamais
moyenné.

Verdicts fermés, priorité nommée : NO_REDUCTION >
MISLEADING_INFLATION > WRONG_REFERENCE > COMPLIANT | BASELINE (pas
de claim audité : la réponse donne SEULEMENT la référence légale).
TOUS les flags sont rendus (la hiérarchie guide, ne censure pas).
Clause récente mise en vente : appliquée en fr|de (citations
nationales), refusée en eu baseline — la directive RENVOIE aux
États, on n'invente pas le droit commun. INSUFFICIENT_HISTORY :
absence n'est jamais zéro (leçon b79) — la couverture du début de
fenêtre est exigée par le NOM de ce qui manque.
Égalité des % stricte : aucune tolérance d'arrondi n'étant publiée,
un écart est rendu CHIFFRÉ (pp, 4 décimales), jamais gracié.
"""

import datetime as _dt
from decimal import Decimal, ROUND_HALF_UP

TWO = Decimal("0.01")
FOUR = Decimal("0.0001")
WINDOW_DAYS = 30
MAX_HISTORY = 400
_JURIS = {"eu", "fr", "de"}

CLAUSE_PROGRESSIVE = {
    "de": "PAngV §11(2): progressive reduction — the reference is "
          "the lowest price before the FIRST step",
    "fr": "L112-1-3 conso: successive reductions without "
          "interruption — the reference is taken before the "
          "first one",
}
CLAUSE_RECENT = {
    "de": "PAngV §11(3): goods on the market less than 30 days — "
          "reference among the prices since listing",
    "fr": "L112-1-3 conso: goods on sale for less than 30 days — "
          "the lowest price of the actual period applies",
}


class DiscountAuditError(Exception):
    def __init__(self, field, message, expected):
        Exception.__init__(self, message)
        self.field, self.message, self.expected = field, message, expected


def _date(s, field):
    try:
        return _dt.date.fromisoformat(s)
    except Exception:
        raise DiscountAuditError(
            field, "not an ISO calendar date: %r" % (s,),
            "YYYY-MM-DD, e.g. 2026-11-27")


def _money(v, field):
    try:
        d = Decimal(str(v))
    except Exception:
        raise DiscountAuditError(
            field, "not a number: %r" % (v,), "exact decimal string")
    if d <= 0:
        raise DiscountAuditError(
            field, "must be > 0, got %s" % format(d, "f"),
            "the law audits prices, not zeros or negatives")
    return d


def shop_discount_audit(history, as_of, sale_price,
                        previous_price=None, claimed_percent=None,
                        jurisdiction="eu", campaign_start=None,
                        on_market_since=None):
    if jurisdiction not in _JURIS:
        raise DiscountAuditError(
            "jurisdiction", "unknown jurisdiction %r" % (jurisdiction,),
            "closed set: eu (art. 6a baseline), fr, de")
    if not history or len(history) > MAX_HISTORY:
        raise DiscountAuditError(
            "history", "history must hold 1..%d entries, got %d"
            % (MAX_HISTORY, len(history) if history else 0),
            "the shop's own applied prices — an empty history is "
            "an empty verdict, refused like the empty ledger")
    anchor = _date(as_of, "as_of")
    camp = _date(campaign_start, "campaign_start") \
        if campaign_start else None
    listed = _date(on_market_since, "on_market_since") \
        if on_market_since else None
    if camp and camp > anchor:
        raise DiscountAuditError(
            "campaign_start", "campaign starts after as_of — the "
            "reduction it anchors is in the future",
            "campaign_start <= as_of")
    pts = {}
    for i, h in enumerate(history):
        d = _date(h.get("date") or "", "history[%d].date" % i)
        if d >= anchor:
            raise DiscountAuditError(
                "history[%d].date" % i,
                "price dated %s is on/after as_of %s — the future "
                "cannot justify a reduction; the announced price "
                "itself belongs in sale_price"
                % (d.isoformat(), anchor.isoformat()),
                "strictly before as_of")
        if d in pts:
            raise DiscountAuditError(
                "history[%d].date" % i,
                "duplicate day %s with two prices — an ambiguous "
                "history has no deterministic minimum"
                % d.isoformat(), "one applied price per day")
        pts[d] = _money(h.get("price"), "history[%d].price" % i)
    sale = _money(sale_price, "sale_price")
    prev = _money(previous_price, "previous_price") \
        if previous_price is not None else None
    claim = None
    if claimed_percent is not None:
        claim = _money(claimed_percent, "claimed_percent")
        if claim > 100:
            raise DiscountAuditError(
                "claimed_percent",
                "more than 100: %s — a reduction is at most the "
                "whole price" % format(claim, "f"),
                "0 < claimed_percent <= 100")
    # clause progressive : transpositions nationales seulement
    if camp and jurisdiction == "eu":
        raise DiscountAuditError(
            "campaign_start", "the progressive-step rule is a "
            "national transposition (de/fr) — the eu baseline of "
            "art. 6a audits each reduction on its own 30-day "
            "window; pass jurisdiction=de or fr, or drop "
            "campaign_start",
            "campaign_start only with jurisdiction fr|de")
    eff_anchor = camp or anchor
    window_start = eff_anchor - _dt.timedelta(days=WINDOW_DAYS)
    carried = None
    for d in sorted(pts):
        if d <= window_start:
            carried = (d, pts[d])
    inside = {d: pts[d] for d in pts if window_start <= d
              < eff_anchor}
    win = dict(inside)
    if carried:
        win[carried[0]] = carried[1]
    coverage = {}
    if carried is None:
        first = min(pts)
        if first > window_start:
            if listed and listed > window_start and listed <= first \
                    and jurisdiction in ("de", "fr"):
                coverage["clause"] = CLAUSE_RECENT[jurisdiction]
                coverage["from"] = listed.isoformat()
            elif listed and listed > window_start and \
                    jurisdiction == "eu":
                raise DiscountAuditError(
                    "history", "window starts %s, first price %s — "
                    "the 'less than 30 days on the market' clause "
                    "is left to Member States by art. 6a and is "
                    "not the eu baseline; audit under "
                    "jurisdiction=de|fr with a citation, or supply "
                    "a price at or before %s"
                    % (window_start.isoformat(), first.isoformat(),
                       window_start.isoformat()),
                    "a price on/before %s, or jurisdiction fr|de "
                    "with on_market_since >= %s"
                    % (window_start.isoformat(),
                       window_start.isoformat()))
            else:
                raise DiscountAuditError(
                    "history", "no price at or before %s: the "
                    "30-day window (%s..%s) has an unpriced start "
                    "— INSUFFICIENT_HISTORY refuses to guess a "
                    "minimum over a blind zone (absence is never "
                    "zero)" % (window_start.isoformat(),
                               window_start.isoformat(),
                               eff_anchor.isoformat()),
                    "one applied price on/before %s (carried into "
                    "the window), or on_market_since proving the "
                    "goods are younger than the window"
                    % window_start.isoformat())
    reference = min(win.values())
    ref_date = min(d for d, p in win.items() if p == reference)
    true_pct = ((reference - sale) / reference * 100).quantize(
        FOUR, rounding=ROUND_HALF_UP)
    rule = ("Directive (EU) 2019/2161 art. 6a: previous price = "
            "lowest price applied in at least the 30 days before "
            "the reduction")
    out = {
        "as_of": anchor.isoformat(),
        "jurisdiction": jurisdiction,
        "window": {"from": window_start.isoformat(),
                   "to": eff_anchor.isoformat()},
        "reference_price": format(reference.quantize(
            TWO, rounding=ROUND_HALF_UP), "f"),
        "reference_date": ref_date.isoformat(),
        "sale_price": format(sale.quantize(TWO,
                                           rounding=ROUND_HALF_UP),
                             "f"),
        "true_percent": format(true_pct, "f"),
        "savings_vs_reference": format(
            (reference - sale).quantize(TWO, rounding=ROUND_HALF_UP),
            "f"),
        "rule": rule,
        "flags": [],
    }
    if win and reference < max(win.values()):
        out["note"] = ("an earlier price inside the window LOWERED "
                       "the reference — CJEU C-330/23: the "
                       "percentage and the strikethrough must "
                       "refer to the lowest figure, even after a "
                       "price went back up")
    if coverage.get("clause"):
        out["note_listing"] = coverage["clause"]
    if camp:
        out["rule_progressive"] = CLAUSE_PROGRESSIVE[jurisdiction]
        out["progressive_campaign_start"] = camp.isoformat()
    inflated = False
    wrongref = False
    if sale >= reference:
        out["verdict"] = "NO_REDUCTION"
        out["flags"].append(
            "sale %s >= reference %s — no reduction may be "
            "announced at all (art. 6a speaks of a price "
            "REDUCTION)" % (format(sale, "f"),
                            format(reference, "f")))
    else:
        if prev is not None:
            if prev > reference:
                inflated = True
                out["flags"].append(
                    "strikethrough %s above legal reference %s by "
                    "%s — the crossed-out number is fiction"
                    % (format(prev, "f"), format(reference, "f"),
                       format((prev - reference).quantize(
                           TWO, rounding=ROUND_HALF_UP), "f")))
            elif prev < reference:
                wrongref = True
                out["flags"].append(
                    "strikethrough %s below legal reference %s by "
                    "%s — not the required figure either way"
                    % (format(prev, "f"), format(reference, "f"),
                       format((reference - prev).quantize(
                           TWO, rounding=ROUND_HALF_UP), "f")))
        if claim is not None:
            if claim > true_pct:
                inflated = True
                out["flags"].append(
                    "announced %s%% overstates the legal %s%% by "
                    "%s pp" % (format(claim, "f"),
                               format(true_pct, "f"),
                               format((claim - true_pct).quantize(
                                   FOUR, rounding=ROUND_HALF_UP),
                                   "f")))
            elif claim < true_pct:
                wrongref = True
                out["flags"].append(
                    "announced %s%% does not equal the legal %s%% "
                    "(understated by %s pp) — no rounding "
                    "tolerance is published; the percentage must "
                    "be computed on the same figure as the law"
                    % (format(claim, "f"), format(true_pct, "f"),
                       format((true_pct - claim).quantize(
                           FOUR, rounding=ROUND_HALF_UP), "f")))
        if inflated:
            out["verdict"] = "MISLEADING_INFLATION"
        elif wrongref:
            out["verdict"] = "WRONG_REFERENCE"
        elif prev is None and claim is None:
            out["verdict"] = "BASELINE"
        else:
            out["verdict"] = "COMPLIANT"
    if prev is not None:
        out["previous_price_announced"] = format(
            prev.quantize(TWO, rounding=ROUND_HALF_UP), "f")
    if claim is not None:
        out["claimed_percent_announced"] = format(claim, "f")
    return out
