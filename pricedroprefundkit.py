"""pricedroprefundkit — /shop/pricedrop-refund : la baisse de prix
APRES l'achat, jugée par la table close des garanties PUBLIEES.

LA DOULEUR, mesurée par la lentille humaine (cycle 23-nov-2026,
fenêtre Black Friday ouverte — la date-butoir FNAC/DARTY tombe le
30-nov) : « j'ai acheté 100, c'est passé à 80, qui me rend la
différence ? » obtient aujourd'hui une prose, jamais un verdict :

  * les pages officielles FR publient la clause EN DUR — fnac.com et
    darty.com, verbatim concordant : « Meilleur prix garanti du 02
    novembre 10h00 au 30 novembre 23h59 2026 inclus… sur les
    produits des campagnes Black Friday, Avant-premières incluses…
    produit identique (même EAN)… non porteur d'autres promotions…
    dont le prix aurait varié pendant la période… remboursement en
    carte cadeau ». Deux enseignes, même contrat, MONNAIE DE
    REMBOURSEMENT DISTINCTE — un détail que la prose noie.
  * le droit français ne donne RIEN par lui-même (kohenavocats,
    15-nov-2026 : « aucun texte n'oblige le vendeur à reverser
    spontanément la différence ») ; la garantie promise devient
    contrat (1103 Code civil). La réponse porte donc la PROVENANCE
    de chaque fenêtre : clause officielle ou >=2 presses concordantes.
  * côté US, six presses concordantes (dipper, promomagpie,
    smartcentsclub, heresnext, bitcritiq, freshcalendars, via les
    pages officielles qu'elles citent) publient des règles que
    PERSONNE ne calcule avec vos dates : Target = deux fenêtres selon
    la date d'achat (1-nov→24-déc : baisse jugée au 24-déc ; sinon
    14 jours) ; Best Buy = deux régimes (retour depuis RÉCEPTION
    +15 j, et claims holiday jusqu'au 15-jan-2027, membres 60 j) ;
    Costco = 30 jours MAIS les promos datées exigent la DOUBLE
    fenêtre (« within BOTH the active promotional dates and 30 days ») ;
    Apple = 14 j depuis la réception ET demande dans les 14 j de la
    baisse, Black Friday EXCLU ; Amazon et Walmart = aucune ligne —
    le « rien » publié est un fait, pas un vide.
  * la distinction que les modèles ratent en confiance : ajustement
    de SOI-MÊME (own-price) vs match CONCURRENT — Best Buy suspend
    son match concurrent du 19 au 30-nov, son ajustement propre prix
    court toujours ; une manchette « price match excluded » lue comme
    « plus rien ne s'applique » est une FAUSSE clôture.

CONTRAT : retailer + purchase_date + drop_date + purchase_price +
new_price (decimal strings ; on ne fetche JAMAIS un prix — les deux
prix viennent d'HUMAN, le calcul est tout) + delivery_date quand la
règle court depuis la réception (absent ≠ zéro : refus nommé) +
membership (bestbuy seul) + promo_start/promo_end (costco seul) +
channel + drop_is_event_pricing (bool quand la baisse EST un prix
BF/vente flash — plusieurs clauses l'excluent nommément) + as_of
pour days_left. Vocabulaire des enseignes FERMÉ ; une ligne n'entre
qu'avec sa clause officielle (published) ou DEUX presses concordantes
(press2) ; Macy's/Newegg/Currys/Argos/John Lewis (single-source)
sont REFUSÉS PAR NOM avec le fait candidat à l'intérieur du refus.

ORACLE : dates = calendrier stdlib sous la convention Day-1 publiée
par Best Buy ; argent = Decimal, HALF_UP 2 décimales (la caisse, pas
la banque) ; golds tracés À LA MAIN dans test_bundle96 avant
l'implémentation.

Doctrine : jamais de fetch, jamais d'horloge — `table_version`,
as_of est un ARGUMENT. Zéro LM. Pilier 3 du trio boutique :
discount-audit (le prix barré est-il légal), return-deadline
(puis-je encore renvoyer), pricedrop-refund (qui me doit l'écart,
jusqu'à quand, et en quelle monnaie).
"""
import datetime as _dt
from decimal import Decimal, ROUND_HALF_UP

TWO = Decimal("0.01")


class PriceDropError(Exception):
    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected


TABLE_VERSION = "2026-11-23"
SEASON = "2026-2027"
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday")

_P = "published"   # clause officielle rejouée verbatim
_J = "press2"      # deux presses concordantes citant la page

# grammaire fermée des enseignes : un synonyme inventé routerait vers
# la mauvaise fenêtre. Les alias viennent des pages sources elles-mêmes.
RETAILER_ALIASES = {
    "target": "target", "target.com": "target",
    "best buy": "bestbuy", "bestbuy": "bestbuy", "best_buy": "bestbuy",
    "costco": "costco", "costco.com": "costco",
    "apple": "apple", "apple.com": "apple", "store.apple.com": "apple",
    "home depot": "homedepot", "homedepot": "homedepot",
    "the home depot": "homedepot",
    "amazon": "amazon", "amazon.com": "amazon",
    "walmart": "walmart", "walmart.com": "walmart",
    "fnac": "fnac", "fnac.com": "fnac",
    "darty": "darty", "darty.com": "darty",
    "fnac-darty": None,  # le groupe signe DEUX clauses distinctes
}

# lignes connues mais single-source : refus instruits (règle
# d'admission >=2 concordantes, même doctrine que returndeadkit).
_SINGLE_SOURCE = {
    "macys": "bunnycoupon: purchases Nov 12–Dec 24 2026 adjusted "
             "if Macy's own price drops by Dec 24 (ONE source, "
             "23-nov-2026)",
    "newegg": "thrifle: 7 days, store credit only (ONE table)",
    "currys": "thinkmoney: refunds qualifying drops (ONE source, "
              "16-nov-2026)",
    "argos": "thinkmoney: e-gift-card refunds (ONE source)",
    "john-lewis": "thinkmoney: 7 days + 25 competitors (ONE source)",
}

_KNOWN_REFUSAL_EXTRA = (
    " Nordstrom (shipping date basis) and IKEA Family 14/90 are known"
    " from thrifle's single table; Kohl's and JCPenney publish no"
    " own-price-drop line in our sources — named refusals carry the"
    " candidate facts until a second concordant source lands")


def _d(s, field="purchase_date"):
    try:
        return _dt.date.fromisoformat(s)
    except Exception:
        raise PriceDropError(field, "not an ISO calendar date: %r"
                             % (s,), "YYYY-MM-DD, e.g. 2026-11-27")


def _iso(d):
    return d.isoformat()


def _wd(d):
    return WEEKDAYS[d.weekday()]


def _money(s, field):
    try:
        v = Decimal(str(s))
    except Exception:
        raise PriceDropError(field, "not a decimal amount: %r"
                             % (s,), "e.g. \"100.00\"")
    if v < 0:
        raise PriceDropError(field, "a negative price is not a fact "
                             "about the world: %r" % (s,),
                             "amount >= 0")
    return v.quantize(TWO, rounding=ROUND_HALF_UP)


def _last_day(start, days):
    """Convention publiée par Best Buy : 'Day 1 is the date the
    customer acquires the product' → dernier jour = start + days-1."""
    return start + _dt.timedelta(days=days - 1)


def _convention(days, published):
    base = ("Day-1 convention: last day = basis + %d days" % (days - 1))
    if published:
        return base + (" — PUBLISHED by bestbuy.com ('Day 1 is the "
                       "date the customer acquires the product')")
    return base + (" — applied uniformly; only Best Buy publishes "
                   "the convention, %d-day rows elsewhere do not — "
                   "named, never hidden in an off-by-one" % days)


def pricedrop_refund(retailer, purchase_date, drop_date,
                     purchase_price, new_price, country=None,
                     delivery_date=None, membership=None,
                     promo_start=None, promo_end=None,
                     channel="first_party",
                     drop_is_event_pricing=None, currency=None,
                     as_of=None):
    rn = RETAILER_ALIASES.get((retailer or "").strip().lower(),
                              "__missing__")
    if rn is None:
        raise PriceDropError(
            "retailer", "'fnac-darty' is a GROUP, not a contract: "
            "Fnac and Darty sign separate gift-card clauses — name "
            "the store that sold the item", "fnac | darty")
    if rn == "__missing__":
        slug = (retailer or "").strip().lower().replace(" ",
                                                        "-").replace(
                                                            "'", "")
        if slug in _SINGLE_SOURCE:
            raise PriceDropError(
                "retailer", "%s: %s — ONE source, and our admission "
                "rule is >=2 concordant: named refusal carrying the "
                "candidate fact instead of a silent hole" % (
                    retailer, _SINGLE_SOURCE[slug]),
                "target | bestbuy | costco | apple | homedepot | "
                "amazon | walmart (US), fnac | darty (FR)")
        raise PriceDropError(
            "retailer", "not in the 2026-2027 own-price table: %r.%s"
            % (retailer, _KNOWN_REFUSAL_EXTRA),
            "target | bestbuy | costco | apple | homedepot | amazon "
            "| walmart | fnac | darty")

    ROW_COUNTRY = {"fnac": "FR", "darty": "FR"}
    rc = ROW_COUNTRY.get(rn, "US")
    if country and country.strip().upper() != rc:
        raise PriceDropError(
            "country", "%s publishes its own-price window for %s "
            "only in our >=2-source table — a borrowed country would "
            "be a borrowed promise" % (rn, rc), rc)
    if channel not in ("first_party", "marketplace"):
        raise PriceDropError("channel", "unknown channel %r"
                             % (channel,), "first_party | marketplace")

    cur = (currency or ("EUR" if rc == "FR" else "USD")).upper()
    if len(cur) != 3 or not cur.isalpha():
        raise PriceDropError("currency", "not an ISO-4217 code: %r"
                             % (currency,), "EUR | USD | 3 letters")

    p = _d(purchase_date)
    q = _d(drop_date, "drop_date")
    if q < p:
        raise PriceDropError(
            "drop_date", "the price drop cannot precede the purchase "
            "(%s < %s) — if you meant the price BEFORE the event, "
            "that is /shop/discount-audit" % (_iso(q), _iso(p)),
            "drop_date >= purchase_date")
    if p.year != 2026:
        raise PriceDropError(
            "purchase_date", "outside the table season: this table "
            "is versioned for purchases made in 2026 (%s) — 2025 "
            "rules are not replayed, 2027 rules are not published "
            "yet" % SEASON, "2026-01-01 .. 2026-12-31")

    a_p = _money(purchase_price, "purchase_price")
    a_n = _money(new_price, "new_price")
    diff = (a_p - a_n).quantize(TWO, rounding=ROUND_HALF_UP)

    # refus croisés : un argument sans ligne publiée pour cet
    # enseigne est un refus nommé, pas un ignoré silencieux.
    if membership and rn != "bestbuy":
        raise PriceDropError(
            "membership", "no dated membership price-adjustment line "
            "is published for %s (Prime and Circle Card change fees "
            "and return clocks, not the own-price window)" % rn,
            "omit membership, or retailer=bestbuy")
    if (promo_start or promo_end) and rn != "costco":
        raise PriceDropError(
            "promo_start", "the double-window rule (claim within "
            "BOTH the promo dates and the day count) is published "
            "for costco only; for %s a dated promo would be an "
            "invented exception" % rn,
            "omit promo_start/promo_end, or retailer=costco")
    if promo_start and promo_end and \
            _d(promo_end, "promo_end") < _d(promo_start, "promo_start"):
        raise PriceDropError("promo_end", "promotion cannot end "
                             "before it starts",
                             "promo_end >= promo_start")

    out = {
        "table_version": TABLE_VERSION, "season": SEASON,
        "country": rc, "retailer": rn, "channel": channel,
        "purchase_date": _iso(p), "drop_date": _iso(q),
        "purchase_price": str(a_p), "new_price": str(a_n),
        "currency": cur, "drop_is_event_pricing":
            bool(drop_is_event_pricing),
        "kinds_of_gap": "own-price adjustment (not competitor "
                        "matching, not the crossed-out-price "
                        "legality — see rule_applied)",
    }

    # levers communs aux verdicts négatifs
    def refuse(reasons, rule, claim_by=None, extra=None):
        out["eligible"] = False
        out["refund_amount"] = "0.00"
        out["reasons"] = reasons
        out["rule_applied"] = rule
        if claim_by is not None:
            out["claim_by"] = _iso(claim_by)
            out["claim_by_weekday"] = _wd(claim_by)
        if extra:
            out.update(extra)

    if diff <= 0:
        refuse(["no drop: %s >= %s — a refund needs the new price "
                "BELOW what you paid" % (str(a_n), str(a_p))],
               "arithmetic-gate")
        return _finish(out, as_of)

    if rn in ("amazon", "walmart"):
        refuse(["this retailer publishes NO own-price adjustment "
                "(dipper, promomagpie, bitcritiq concordant)"]
               + (["Walmart stores may match Walmart.com AT CHECKOUT "
                   "only — an after-the-fact drop is not matched "
                   "(heresnext, promomagpie)"] if rn == "walmart"
                  else []),
               "none-published",
               extra={
            "mode": "none",
            "lever": ("the published lever is buy-again-and-return-"
                      "the-original: compute that clock at "
                      "/api/v1/shop/return-deadline — it is the "
                      "neighbouring pillar, never averaged with "
                      "this one"),
            "provenance": [_J],
            "sources": (["dipperapp price-drop-after-Black-Friday "
                         "(2026 table)", "promomagpie (same rows)",
                         "bitcritiq (same rows)"] if rn == "amazon"
                        else ["dipperapp table (Walmart.com: no "
                              "adjustment)", "bunnycoupon (BF/CM "
                              "deals not matched in store)",
                              "heresnext (checkout-only match)"]),
        })
        return _finish(out, as_of)

    # ---------------- FR : campagne en dur 2-nov 10h → 30-nov ------
    if rn in ("fnac", "darty"):
        camp_start = _dt.date(2026, 11, 2)
        camp_end = _dt.date(2026, 11, 30)
        out["provenance"] = [_P]
        out["sources"] = [
            "%s.com (black-friday / cyber-monday page, clause "
            "\"Meilleur prix garanti du 02 novembre 10h00 au 30 "
            "novembre 23h59 2026 inclus\", verbatim)" % rn,
            "labomaison + bonplangeek (concordant, FR windows)",
        ]
        out["conditions"] = [
            "same EAN, product of the Black Friday campaigns "
            "(avant-premières included) — verbatim",
            "no other promotion on the lower price (codes, vente "
            "liée, prix à condition) — verbatim",
            "the price must have VARIATED inside the campaign window "
            "— verbatim",
            "campaign opens 2026-11-02 at 10:00 — a same-morning "
            "earlier timestamp is outside; we carry dates, the hour "
            "is yours to check",
            "marketplace sales are excluded — channel=first_party "
            "only",
        ]
        out["mode"] = ("gift card (carte cadeau %s) — verbatim; the "
                       "money comes back as %s store credit, NOT "
                       "cash" % (rn.capitalize(), rn.capitalize()))
        out["conflicts"] = [
            "the two sister brands refund in TWO different gift "
            "cards (carte cadeau Fnac vs Darty) under one identical "
            "clause — the mode field names the card that can pay "
            "you"]
        if channel == "marketplace":
            raise PriceDropError(
                "channel", "%s's best-price clause is verbatim "
                "'hors marketplace' — a third-party sale has no "
                "guarantee to run" % rn, "first_party")
        if p < camp_start or q > camp_end:
            refuse(["outside the published campaign window "
                    "2026-11-02..2026-11-30: purchase %s, drop %s"
                    % (_iso(p), _iso(q))], "campaign-window",
                   claim_by=camp_end)
            return _finish(out, as_of)
        out["eligible"] = True
        out["claim_by"] = _iso(camp_end)
        out["claim_by_weekday"] = _wd(camp_end)
        out["refund_amount"] = str(diff)
        out["rule_applied"] = "campaign-giftcard-clause"
        out["conflicts"] = [
            "the two sister brands refund in TWO different gift "
            "cards (carte cadeau Fnac vs Darty) under one identical "
            "clause — the mode field names the card that can pay "
            "you"]
        return _finish(out, as_of)

    # ---------------- US : quatre régimes datés ---------------------
    event = bool(drop_is_event_pricing)

    if rn == "target":
        hol = _dt.date(2026, 11, 1) <= p <= _dt.date(2026, 12, 24)
        std_end = _last_day(p, 14)
        if hol and q <= _dt.date(2026, 12, 24):
            out["eligible"] = True
            out["claim_by"] = "2026-12-24"
            out["claim_by_weekday"] = _wd(_dt.date(2026, 12, 24))
            out["refund_amount"] = str(diff)
            out["rule_applied"] = "holiday-own-price-window"
            out["counting_convention"] = _convention(14, False)
            out["standard_fallback"] = {
                "claim_by": _iso(std_end),
                "note": "purchases outside Nov 1–Dec 24 keep the "
                        "14-day window; both clocks are shown, "
                        "never blended"}
        elif q <= std_end:
            out["eligible"] = True
            out["claim_by"] = _iso(std_end)
            out["claim_by_weekday"] = _wd(std_end)
            out["refund_amount"] = str(diff)
            out["rule_applied"] = "standard-14-day"
            out["counting_convention"] = _convention(14, False)
        else:
            refuse(["holiday window: purchase %s %s / drop %s %s"
                    % (_iso(p), "in" if hol else "outside",
                       _iso(q),
                       "before" if q <= _dt.date(2026, 12, 24)
                       else "after") + " 2026-12-24",
                    "standard window closed %s (14 days from "
                    "purchase)" % _iso(std_end)], "both-windows",
                   claim_by=std_end)
        out["provenance"] = [_J]
        out["sources"] = ["Target price-match page via heresnext + "
                          "bitcritiq ('within 14 days after "
                          "purchase', holiday 'on or before Dec 24')",
                          "smartcentsclub + freshcalendars + "
                          "printerval + dipper (concordant tables)"]
        out["conditions"] = [
            "clearance/closeout and ANOTHER store's price are not "
            "matched (heresnext)",
            "a promotional Target GiftCard attached to the purchase "
            "voids the adjustment (bitcritiq)",
            "competitor matching: never — Target adjusts its OWN "
            "price only (all six tables)"]
        return _finish(out, as_of)

    if rn == "bestbuy":
        dd = _d(delivery_date, "delivery_date")
        period_days = 60 if membership else 15
        std_end = _last_day(dd, period_days)
        in_hol = _dt.date(2026, 10, 30) <= p <= _dt.date(2026, 12, 31)
        hol_claim = _dt.date(2027, 1, 15)
        out["provenance"] = [_P, _J]
        out["sources"] = ["bestbuy.com Price Match Guarantee "
                          "(effective 2026-10-30 / 2-sept-2026 per "
                          "bitcritiq/freshcalendars): 'If we lower "
                          "our in-store, online or app price during "
                          "the return and exchange period, we will "
                          "match our lower price, upon request.'",
                          "dipper + promomagpie + heresnext + "
                          "bitcritiq + freshcalendars (concordant)"]
        out["conflicts"] = [
            "competitor matching is SUSPENDED Nov 19–30 (bunnycoupon"
            ", heresnext) while OWN-price adjustment keeps running —"
            " 'price match excluded' is not 'nothing applies'; this "
            "tool answers the own-price question only"]
        out["conditions"] = [
            "standard period begins the day you RECEIVE (bestbuy."
            "com, verbatim) — hence the required delivery_date",
            "Plus/Total members: 60-day standard period (bitcritiq)"
            ", Marketplace purchases keep the standard 15 days even"
            " in the holiday window (bestbuy.com)"]
        if channel == "marketplace":
            refuse(["Marketplace items are excluded from price "
                    "adjustments (dipper, promomagpie)"],
                   "marketplace-excluded")
            return _finish(out, as_of)
        if event:
            refuse(["the lower price is event pricing: 'items "
                    "advertised as Black Friday pricing' and daily/"
                    "hourly sales are EXCLUDED from the guarantee "
                    "(bestbuy.com via freshcalendars, heresnext)"],
                   "event-pricing-excluded")
            return _finish(out, as_of)
        if in_hol and q <= hol_claim:
            out["eligible"] = True
            out["claim_by"] = _iso(max(hol_claim, std_end))
            out["claim_by_weekday"] = _wd(max(hol_claim, std_end))
            out["refund_amount"] = str(diff)
            out["rule_applied"] = ("holiday-claims-through-2027-01-15"
                                   + ("-member-60-day" if membership
                                      else ""))
            out["counting_convention"] = _convention(period_days,
                                                    True)
            out["both_rules"] = {
                "standard_period_ends": _iso(std_end),
                "holiday_claims_end": _iso(hol_claim),
                "note": "TWO published regimes under one headline; "
                        "the claim window is the LATER, never a "
                        "blend; a drop inside either counts"}
        elif q <= std_end:
            out["eligible"] = True
            out["claim_by"] = _iso(std_end)
            out["claim_by_weekday"] = _wd(std_end)
            out["refund_amount"] = str(diff)
            out["rule_applied"] = "standard-return-period"
            out["counting_convention"] = _convention(period_days,
                                                     True)
        else:
            refuse(["purchase %s %s the holiday window; the "
                    "standard period ran from delivery %s for %d "
                    "days and closed %s"
                    % (_iso(p), "inside" if in_hol else "outside",
                       _iso(dd), period_days, _iso(std_end))],
                   "both-windows", claim_by=std_end)
        return _finish(out, as_of)

    if rn == "costco":
        claim30 = _last_day(p, 30)
        out["provenance"] = [_J]
        out["sources"] = ["costco.com via bitcritiq + heresnext: "
                          "'within 30 days of purchase'; sale-dated "
                          "promos: 'within BOTH the active "
                          "promotional dates and 30 days', verbatim",
                          "dipper + promomagpie + bunnycoupon + "
                          "smartcentsclub (30 days, concordant)"]
        if promo_start or promo_end:
            ps, pe = _d(promo_start, "promo_start"), \
                _d(promo_end, "promo_end")
            gate = min(claim30, pe)
            if not (ps <= q <= pe):
                refuse(["the drop %s falls outside the published "
                        "promotion dates %s..%s" % (_iso(q),
                                                    _iso(ps),
                                                    _iso(pe))],
                       "double-window-promo-dates", claim_by=gate)
            elif p > pe:
                refuse(["the purchase %s came AFTER the promotion "
                        "closed %s — a dated-sale adjustment must "
                        "ride inside the promo (bitcritiq verbatim)"
                        % (_iso(p), _iso(pe))],
                       "double-window-promo-dates", claim_by=gate)
            else:
                out["eligible"] = True
                out["claim_by"] = _iso(gate)
                out["claim_by_weekday"] = _wd(gate)
                out["refund_amount"] = str(diff)
                out["rule_applied"] = "double-window"
                out["double_window"] = {"promo": [_iso(ps),
                                                  _iso(pe)],
                                       "thirty_days": _iso(claim30),
                                       "claim_by": "min of the two, "
                                                   "verbatim rule"}
            out["counting_convention"] = _convention(30, False)
            return _finish(out, as_of)
        out["eligible"] = True if q <= claim30 else False
        if not out["eligible"]:
            refuse(["the drop %s is beyond 30 days from purchase "
                    "(closed %s)" % (_iso(q), _iso(claim30))],
                   "thirty-day-window", claim_by=claim30)
        else:
            out["claim_by"] = _iso(claim30)
            out["claim_by_weekday"] = _wd(claim30)
            out["refund_amount"] = str(diff)
            out["rule_applied"] = "thirty-day-window"
            out["counting_convention"] = _convention(30, False)
            out["needs_check"] = [
                "if this item is a SALE-DATED promotion, the "
                "published rule closes the claim EARLIER — inside "
                "both the promo dates and the 30 days; pass "
                "promo_start/promo_end and this verdict recomputes"]
        out["conditions"] = [
            "members only, not resellers (heresnext)",
            "Costco.com does not match warehouse prices and neither "
            "matches competitors (bitcritiq, promomagpie)"]
        out["mode"] = "cash — adjustment to the original payment " \
                      "method (dipper)"
        return _finish(out, as_of)

    if rn == "apple":
        dd = _d(delivery_date, "delivery_date")
        receipt_end = _last_day(dd, 14)
        claim_after_drop = _last_day(q, 14)
        gate = min(receipt_end, claim_after_drop)
        out["provenance"] = [_J]
        out["sources"] = ["apple.com via heresnext + bitcritiq: "
                          "14 days of receipt, request within 14 "
                          "days of the drop",
                          "dipper + smartcentsclub (concordant "
                          "exclusions)"]
        if event:
            refuse(["Apple's own line EXCLUDES 'limited-time "
                    "reductions and special sales events such as "
                    "Black Friday' (heresnext, bitcritiq verbatim)"],
                   "event-pricing-excluded", claim_by=gate)
            return _finish(out, as_of)
        if q > receipt_end:
            refuse(["the drop came after the 14-day window from "
                    "receipt %s closed %s" % (_iso(dd),
                                              _iso(receipt_end))],
                   "receipt-14-day-window", claim_by=receipt_end)
            return _finish(out, as_of)
        out["eligible"] = True
        out["claim_by"] = _iso(gate)
        out["claim_by_weekday"] = _wd(gate)
        out["refund_amount"] = str(diff)
        out["rule_applied"] = "receipt-14-and-drop-14-minimum"
        out["counting_convention"] = _convention(14, False)
        out["both_clocks"] = {"from_receipt": _iso(receipt_end),
                              "from_drop": _iso(claim_after_drop),
                              "claim_by": "the EARLIER of the two —"
                                          " a published double clock"}
        out["conditions"] = [
            "Apple-branded products only (heresnext, bitcritiq)",
            "counts from RECEIPT — hence the required delivery_date"]
        out["mode"] = "cash — refund to original payment method"
        return _finish(out, as_of)

    # homedepot
    claim30 = _last_day(p, 30)
    out["provenance"] = [_J]
    out["sources"] = ["homedepot.com policy via dipper ('adjusts "
                      "if its own price drops, 30 days') + "
                      "bitcritiq ('Black Friday and other "
                      "limited-time promotions excluded')",
                      "promomagpie + heresnext (concordant)"]
    if channel == "marketplace":
        refuse(["third-party sellers are excluded (dipper)"],
               "marketplace-excluded")
        return _finish(out, as_of)
    if event:
        refuse(["the lower price is a Black Friday / limited-time "
                "promotion — excluded by Home Depot's own line "
                "(bitcritiq)"], "event-pricing-excluded",
               claim_by=claim30)
        return _finish(out, as_of)
    if q <= claim30:
        out["eligible"] = True
        out["claim_by"] = _iso(claim30)
        out["claim_by_weekday"] = _wd(claim30)
        out["refund_amount"] = str(diff)
        out["rule_applied"] = "thirty-day-window"
        out["counting_convention"] = _convention(30, False)
    else:
        refuse(["the drop %s is beyond 30 days from purchase (closed"
                " %s)" % (_iso(q), _iso(claim30))],
               "thirty-day-window", claim_by=claim30)
    out["mode"] = "cash — adjustment to original payment method"
    return _finish(out, as_of)


def _finish(out, as_of):
    if as_of is not None:
        a = _d(as_of, "as_of")
        out["as_of"] = _iso(a)
        if out.get("claim_by"):
            out["days_left"] = (_dt.date.fromisoformat(
                out["claim_by"]) - a).days
    if out.get("eligible"):
        out.setdefault("mode",
                       "cash — adjustment to the original payment "
                       "method (the mode each retailer publishes is "
                       "in the row's sources)")
    return out
