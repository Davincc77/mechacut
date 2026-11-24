# -*- coding: utf-8 -*-
"""guaranteekit — /shop/legal-guarantee : les HORLOGES LÉGALES de l'achat,
datées pour UNE date de délivrance, juridictions FR et UK, sources
officielles rejouées VERBATIM, conflits et refus NOMMÉS.

LA DOULEUR, mesurée par la lentille HUMAIN (cycle 24-nov-2026,
lendemain des fêtes en janvier) : le cadeau tombe en panne le 16
janvier, la fenêtre commerciale du magasin est MORTE depuis le 8 ou le
15 janvier — et là, plus rien n'est daté nulle part. Les pages
d'aide rendent des DURÉES (« 2 ans », « six months »), jamais des
ÉCHÉANCES ; les modèles, eux, fondent trois régimes distincts en une
seule manchette et répondent avec confiance :

  * FR — service-public.fr F11094 (Vérifié le 17 août 2026, rejouée
    ce cycle) : « Vous avez 2 ans à partir du jour de la délivrance
    du bien pour utiliser la garantie » ; la PRÉSUMPTION d'antériorité
    diffère : « 24 mois pour les biens neufs et reconditionnés,
    12 mois pour les biens d'occasion » — et la page se contredit
    ELLE-MÊME sur le reconditionné : le bandeau résumé dit 24 mois,
    l'onglet « Bien d'occasion ou bien reconditionné » écrit « La non
    conformité est d'office considérée comme existant pendant un délai
    d'un an », pendant que L217-7 (ordonnance 2021-1247) ne nomme que
    l'occasion à 12 mois. CONFLIT NOMMÉ, les DEUX dates voyagent,
    jamais de moyenne.
  * FR — les remèdes ont DES HORLOGES PROPRES, datables : « La
    réparation ou le remplacement du bien doit intervenir dans les
    30 jours qui suivent votre demande » ; réparation choisie →
    « extension de la garantie initiale de 12 mois » ; remplacement
    IMPOSÉ par le vendeur → garantie « renouvelée pour 2 ans à
    compter du remplacement » ; remboursement « au plus tard dans les
    14 jours calendaires », ET L'EXEMPLE OFFICIEL DE COMPUT donne la
    convention : « Vous demandez un remboursement le 3 janvier. Le
    délai de remboursement commence à courir le lendemain, soit le
    4 janvier. Le vendeur doit donc vous rembourser au plus tard le
    17 janvier à minuit » — échéance = déclencheur + N jours, anniversaire
    inclus, règle appliquée partout ici et nommée. Pénalités publiées
    après l'échéance : 10 % (14-30 j de retard), 20 % (30-60),
    50 % (au-delà).
  * FR — garantie des vices cachés, service-public F11007 (Vérifié
    le 25 novembre 2025) : « 2 ans à partir de la découverte du
    défaut » — DEUXIÈME point de départ — « dans la limite de 20 ans
    après l'achat (c'est-à-dire à compter du jour de la vente) » —
    TROISIÈME point de départ. Conformité court depuis la délivrance,
    vices depuis la découverte, la forclusion depuis la VENTE : trois
    ancres sous le même mot « garantie ».
  * UK — legislation.gov.uk (données SLD 2026-10-29, amendements
    DMCC Act 2024 déjà appliqués) : s.22(3) « the end of 30 days
    beginning with the first day after these have all happened »
    (propriété transférée ET livrée ET, si installation due, notifiée
    : trois conditions, une seule ancre légale) ; s.19(14) « goods
    which do not conform to the contract at any time within the
    period of six months beginning with the day on which the goods
    were delivered must be taken not to have conformed to it on that
    day » — la présomption est une RÈGLE DE PREUVE, pas une deadline,
    et Explanatory Notes ¶97 le dit : elle ne s'applique même pas au
    short-term right to reject ; forclusion : « six years from the
    date of the breach of contract, whereas in Scottish law the
    limitation period is five years » (¶105, Prescription and
    Limitation (Scotland) Act 1973 s.6). Trois régimes, et le tiers
    des fils Reddit qu'on lit (r/LegalAdviceUK, nov-2026) mélangent « statutory
    warranty », 30-day, 6 months et 6 years dans la même phrase.
  * La presse du Black Friday 2026 confirme la classe de douleur de
    l'autre bout du monde : ACCC (19 nov, bhg.com.au) — « Your rights
    can last longer than the warranty » — mais le régime australien
    compte en « reasonable time » : PAS COUNTABLE en table, donc
    REFUSÉ par nom, portant le fait.

CONTRAT : jurisdiction FR|UK + delivered_on (l'ancre FR « délivrance »
/ UK : le jour où s.22(3)(a)(b)(c) sont toutes arrivées — hypothèse
NOMMÉE) + condition new|used|refurbished (seule FR branche la
présomption ; UK : la loi ne branche rien, dit tel quel) + nation UK
(optionnelle : absente, les DEUX forclusions 6y/5y voyagent) +
discovered_on (ouvre les verdicts + le bloc vices FR) +
claim_requested_on (FR seulement : ouvre +30 j réparation/remplacement
et +14 j remboursement ; UK : refus nommé, le « waiting period »
s.22(6) ne se compute pas sans la date de retour) + sold_on (ancre
20 ans vices ; absent = delivered_on, hypothèse nommée) + as_of
optionnel — JAMAIS d'horloge murale.

RÈGLE DE CALCUL DES MONTHS : anniversaire du quantième, ARRONDI AU
DERNIER JOUR du mois cible quand le quantième n'existe pas
(2024-02-29 + 2 ans -> 2026-02-28) — règle ÉCRITE dans la réponse.
Bornes « beginning with » UK : le jour nommé EST le jour 1, donc la
dernière = anniversaire - 1 (s.19(14)); bornes FR « à compter du jour
de » : l'exemple officiel 3-janvier -> 17-janvier fixe anniversaire +
N. Les deux conventions voyagent dans `computations`.

ZÉRO réseau, zéro horloge, zéro conseil : l'outil rend des DATES et
les verbatims, jamais un avis d'achat — la ligne officielle « La
garantie légale de conformité est différente de la garantie
commerciale (qui est facultative) » et « obligatoire » sont portées,
le jugement de valeur sur une extension payante reste à l'humain.
"""

WARRANT_TABLE_VERSION = "2026-11-24"
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday")
_S = "published"  # texte officiel rejoué verbatim cette nuit

# ---------------- helpers de compute ----------------
import calendar as _cal
from datetime import date as _date, timedelta as _td


class WarrantError(Exception):
    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected


def _d(s, field):
    try:
        y, m, d = (int(x) for x in s.split("-"))
        return _date(y, m, d)
    except Exception:
        raise WarrantError(field, "not an ISO calendar date: %r" % (s,),
                           "YYYY-MM-DD, e.g. 2026-12-25")


def _iso(d):
    return d.isoformat()


def _wd(d):
    return WEEKDAYS[d.weekday()]


def _addm(d, n):
    """Anniversaire n mois plus tard ; quantième inexistant -> DERNIER
    jour du mois cible (règle écrite dans la réponse)."""
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return _date(y, m, min(d.day, _cal.monthrange(y, m)[1]))


_MONTH_RULE = ("month math = calendar anniversary; when the target "
               "month has no such day, the LAST day of that month is "
               "the anniversary (2024-02-29 + 2 years -> 2026-02-28)")

# ---------------- le vocabulaire fermé ----------------
JURISDICTIONS = ("FR", "UK")
CONDITIONS = ("new", "used", "refurbished")
UK_NATIONS = ("england", "wales", "scotland", "northern-ireland")

_REFUSAL = {
    "US": ("no federal statutory warranty for goods exists: implied "
           "merchantability is state UCC law and diverges state by "
           "state — there is NO single date to count. The seasonal "
           "COMMERCIAL windows (Amazon/Walmart/Target/Best Buy/Apple) "
           "are /shop/return-deadline's table."),
    "AU": ("the Australian Consumer Law guarantees are automatic and "
           "'can last longer than a warranty' (ACCC, 19 nov 2026, "
           "verbatim) — but the clock is a 'reasonable time', decided "
           "case by case: NOT countable, refused by name rather than "
           "invented as a date."),
    "BR": ("the CDC's 90-day countable window for durable goods is a "
           "KNOWN CANDIDATE but its pages were not replayed to the "
           "verbatim standard this cycle — a table entry needs its "
           "official text, not my memory. Queued, refused here by "
           "name."),
    "IE": ("S.I. 359/2022 / Consumer Rights Act 2022 (IE): CCPC and "
           "Citizens Information both print 30-day short-term right, "
           "12-month presumption, six-year actions — concordant and "
           "queued for replay; not admitted until the pages are "
           "replayed at source."),
}

# Les lignes qui ne sont PAS une échéance ne deviennent jamais une
# date : elles voyagent comme conditions, verbatim.
_FR_REMEDIES = [
    "repair or replacement must occur 'dans les 30 jours qui suivent "
    "votre demande' (F11094 verbatim) — the claim date is the anchor; "
    "pass claim_requested_on and both remedy clocks are computed",
    "chosen repair extends the guarantee: 'extension de la garantie "
    "initiale de 12 mois' (F11094 verbatim)",
    "seller-IMPOSED replacement (you asked repair) renews the whole "
    "guarantee: 'renouvelée pour 2 ans à compter du remplacement du "
    "bien' (F11094 verbatim)",
    "refund: 'sans retard injustifié et au plus tard dans les 14 "
    "jours calendaires à compter de la date à laquelle le vendeur "
    "est informé de votre décision' (F11094 verbatim); published "
    "late-payment surcharges 10% (14-30 days late), 20% (30-60), "
    "50% (beyond 60)",
    "weekend extension exists but is NOT computable: F11094 defers "
    "'jour ouvrable' to 'jours fériés habituellement non travaillés "
    "DANS L'ENTREPRISE' — the company's own calendar decides, and "
    "the page's own example still prints '17 janvier à minuit' for "
    "a Sunday. The weekday travels with every date here; no "
    "extension is applied by guess",
    "legal vs commercial: 'La garantie légale de conformité est "
    "différente de la garantie commerciale (qui est facultative)' "
    "and 'obligatoire' (F11094 verbatim) — the answer to the "
    "extended-warranty upsell is the DATES plus this line; the "
    "purchase decision stays human",
    "excluded by F11094 verbatim: used goods sold at public auction, "
    "goods sold by a PRIVATE seller or a commissaire de justice, "
    "domestic animals, and free digital content even on a physical "
    "carrier (USB, CD) — private-sale gifts go to vices cachés only",
    "digital with continuous updates: supply contracted for 2 years "
    "or less (or unspecified) -> the 2-year clock; contracted longer "
    "-> 'le vendeur répond des défauts qui apparaissent pendant "
    "toute la période prévue par le contrat' (F11094 verbatim)",
    "since 31 July 2026 a SEPARATE right: repair by the MANUFACTURER "
    "after the legal guarantee died, 'pendant une période de 5 à 10 "
    "ans après l'achat, selon le produit et la pièce de rechange' "
    "(F11094 verbatim) — the range is per-product, NOT countable "
    "from these inputs: named, never averaged",
    "the legal conformity guarantee does NOT apply to sales by "
    "private individuals (vices cachés does) — F11007/F11094",
]

_UK_REMEDIES = [
    "s.22(3) (legislation.gov.uk, verbatim): 'the end of 30 days "
    "beginning with the first day after these have all happened — "
    "a ownership ... b the goods have been delivered, and c where "
    "the contract requires the trader to install the goods ... the "
    "trader has notified the consumer that the action has been "
    "taken' — delivered_on is treated as the day ALL of a/b/c "
    "completed (named assumption if installation lagged)",
    "s.22(4): goods 'which can reasonably be expected to perish "
    "after a shorter period' get that shorter period — perishables "
    "are refused a 30-day count, condition named",
    "s.22(6)-(7): a requested repair/replacement STOPS the 30-day "
    "clock for the 'waiting period' (claim day -> day replacement/"
    "repair received), then it ends 7 days after or at the original "
    "limit extended by the waiting period, whichever later — NOT "
    "computable without the return date; named, never guessed",
    "s.19(14) is a BURDEN rule, not a deadline: faults appearing "
    "in the six months beginning with delivery are deemed to have "
    "existed at delivery; Explanatory Notes ¶97: 'This does not "
    "apply where the consumer exercises the short-term right to "
    "reject'; s.19(15) disapplies it when the goods DID conform "
    "that day or the presumption is incompatible",
    "after the presumption, the consumer's own proof is required — "
    "but the action itself lives to the limitation period (¶105)",
    "final right to reject beyond 6 months may be reduced for use "
    "(s.24 territory) — refunds are not re-promised here; only the "
    "clocks are dated",
]

_VERBATIM_FR = {
    "action": "Vous avez 2 ans à partir du jour de la délivrance du "
              "bien pour utiliser la garantie (F11094, Vérifié le 17 "
              "août 2026)",
    "presumption_new": "'24 mois pour les biens neufs et "
                       "reconditionnés' + L217-7 (24 months new) — "
                       "service-public F11094 bandeau résumé",
    "presumption_used": "'12 mois pour les biens d'occasion' — "
                        "F11094 résumé; l'onglet 'Bien d'occasion ou "
                        "bien reconditionné' écrit 'délai d'un an'; "
                        "L217-7 (ordonnance 2021-1247) nomme "
                        "l'occasion à 12 mois",
    "vices_action": "'Vous avez 2 ans à partir de la découverte du "
                    "défaut' — F11007, Vérifié le 25 novembre 2025",
    "vices_cap": "'Et ce, dans la limite de 20 ans après l'achat "
                 "(c'est-à-dire à compter du jour de la vente)' — "
                 "F11007 verbatim",
}

_VERBATIM_UK = {
    "reject": "s.22(3) CRA 2015: 'the end of 30 days beginning with "
              "the first day after these have all happened'",
    "presumption": "s.19(14) CRA 2015: 'within the period of six "
                   "months beginning with the day on which the goods "
                   "were delivered ... must be taken not to have "
                   "conformed to it on that day'",
    "limitation": "Explanatory Notes ¶105: 'six years from the date "
                  "of the breach of contract, whereas in Scottish "
                  "law the limitation period is five years' "
                  "(Prescription and Limitation (Scotland) Act 1973, "
                  "s.6)",
}

_SOURCES = {
    "FR": [
        "service-public.fr F11094 'Achat d'un produit : garantie "
        "légale de conformité' (Vérifié le 17 août 2026) — replayed "
        "verbatim 24 nov 2026",
        "service-public.fr F11007 'Achat d'un produit : garantie "
        "légale des vices cachés' (Vérifié le 25 novembre 2025) — "
        "replayed verbatim 24 nov 2026",
        "code de la consommation L217-4 / L217-7 (via "
        "economie.gouv.fr/cedef/garantie-legale-conformite: "
        "'ordonnance n° 2021-1247 du 29 septembre 2021', occasion "
        "'porté à 12 mois à compter du 1er janvier 2022')",
    ],
    "UK": [
        "legislation.gov.uk Consumer Rights Act 2015 s.19 and s.22 "
        "(SLD data 2026-10-29, DMCC Act 2024 amendments applied) — "
        "replayed verbatim 24 nov 2026",
        "CRA 2015 Explanatory Notes ¶97 and ¶105 (legislation.gov.uk)",
        "apple.com/uk/legal/statutory-warranty (retailer restating "
        "the same three clocks: 30 days, six months, six years / "
        "five in Scotland) — concordance source",
    ],
}


# ---------------- le moteur ----------------
def legal_guarantee(jurisdiction, delivered_on, condition=None,
                    nation=None, discovered_on=None,
                    claim_requested_on=None, sold_on=None, as_of=None):
    j = (jurisdiction or "").upper()
    if not j:
        raise WarrantError(
            "jurisdiction",
            "jurisdiction is the whole tool: every clock below is a "
            "country's statute — pass one",
            "one of: fr, uk (other countries: refused by name — US "
            "has no federal countable window, AU is 'reasonable "
            "time', BR/IE are queued candidates)")
    if j not in JURISDICTIONS:
        msg = _REFUSAL.get(j)
        if msg:
            raise WarrantError("jurisdiction", msg, "one of: fr, uk")
        raise WarrantError(
            "jurisdiction",
            "no table row for %r: only the jurisdictions replayed "
            "to verbatim source are admitted (never a borrowed "
            "neighbour's law)" % (j,),
            "one of: fr, uk")

    dl = _d(delivered_on, "delivered_on")
    a = _d(as_of, "as_of") if as_of else None
    disc = _d(discovered_on, "discovered_on") if discovered_on else None
    cond = (condition or "new").lower()
    if cond not in CONDITIONS:
        raise WarrantError(
            "condition",
            "unknown condition %r — the FR presumption branches on "
            "exactly these words; UK tables none (statute does not "
            "branch)" % (condition,),
            "one of: new, used, refurbished")

    out = {
        "jurisdiction": j,
        "delivered_on": _iso(dl),
        "delivered_weekday": _wd(dl),
        "condition": cond,
        "table_version": WARRANT_TABLE_VERSION,
        "provenance": _S,
        "computations": {
            "month_rule": _MONTH_RULE,
            "fr_rule": "FR 'à compter du jour de la délivrance': the "
                       "official worked example fixes it — refund "
                       "claimed 3 January, clock runs 'from the next "
                       "day', due 'no later than 17 January' = "
                       "trigger + N days (anniversary inclusive)",
            "uk_rule": "UK 'beginning with the day': that day IS "
                       "day one — s.19(14) six months therefore "
                       "ends the day BEFORE the anniversary; s.22(3) "
                       "starts 'the first day AFTER' delivery, so "
                       "the 30th day = delivered + 30",
        },
        "conditions": [],
        "verbatim": {},
        "sources": _SOURCES[j],
    }

    if nation is not None:
        n = str(nation).lower()
        if n not in UK_NATIONS:
            raise WarrantError(
                "nation",
                "unknown UK nation %r — limitation is 6 years for "
                "England/Wales/Northern Ireland and 5 for Scotland; "
                "no other spelling is tabled" % (nation,),
                "one of: england, wales, scotland, northern-ireland")
        if j == "FR":
            raise WarrantError(
                "nation",
                "nation is a UK field: France has ONE civil-code "
                "clock for all of its territory — the input belongs "
                "to the other jurisdiction",
                "omit it for FR")
        out["nation"] = n

    # ------- les fenêtres de l'appelant (refus informatifs) -------
    if a:
        out["as_of"] = _iso(a)

    def _due(d, key, label):
        out[key] = {"date": _iso(d), "weekday": _wd(d), "rule": label}
        if a:
            out[key]["days_left"] = (d - a).days

    if j == "FR":
        _fr(out, dl, cond, disc, a, claim_requested_on, sold_on, _due)
    else:
        _uk(out, dl, cond, disc, a, claim_requested_on, nation, _due)

    return out


def _fr(out, dl, cond, disc, a, claim, sold_on, _due):
    out["conditions"] = list(_FR_REMEDIES)
    out["verbatim"] = dict(_VERBATIM_FR)
    action_by = _addm(dl, 24)
    _due(action_by, "conformite_action_by",
         "'2 ans à partir du jour de la délivrance' — F11094")

    pres = {}
    pres["new"] = _addm(dl, 24)
    pres["refurbished"] = _addm(dl, 24)
    pres["used"] = _addm(dl, 12)
    if cond == "used":
        pres_by = _addm(dl, 12)
        _due(pres_by, "presumption_by",
             "'12 mois pour les biens d'occasion' — F11094 résumé, "
             "concordant L217-7; au-delà, la preuve du défaut à la "
             "délivrance vous revient (verbatims voyagent)")
    elif cond == "refurbished":
        _due(_addm(dl, 24), "presumption_by",
             "CONFLICT, both dates travel, never averaged — "
             "F11094 résumé: '24 mois pour les biens neufs et "
             "reconditionnés' (2028-style anniversary below) BUT the "
             "same page's tab 'Bien d'occasion ou bien reconditionné' "
             "writes 'un délai d'un an', and L217-7 names only "
             "'biens d'occasion' at 12 months")
        out["conflict"] = {
            "field": "presumption_by (refurbished)",
            "positions": {
                "24_months": {"date": _iso(_addm(dl, 24)),
                              "source": "F11094 bandeau résumé "
                                        "(Vérifié 17 août 2026)"},
                "12_months": {"date": _iso(_addm(dl, 12)),
                              "source": "F11094 onglet 'Bien "
                                        "d'occasion ou bien "
                                        "reconditionné' + L217-7 "
                                        "silence on reconditionné"},
            },
            "handling": "both shipped; the conservative (earlier) "
                        "date is what a seller can demand you prove "
                        "after — act by the EARLIER one, named",
        }
    else:  # new
        _due(_addm(dl, 24), "presumption_by",
             "neuf: présomption d'antériorité = la durée même de "
             "l'action (24 mois) — F11094; the burden is the "
             "seller's inside it")
    out["presumption_table_all_conditions"] = {
        k: _iso(v) for k, v in sorted(pres.items())}

    if disc:
        in_pres = disc <= _date.fromisoformat(
            out["presumption_by"]["date"])
        in_window = disc <= action_by
        if in_window and in_pres:
            v = "WITHIN_PRESUMPTION"
            why = ("defect appeared inside the presumption window: "
                   "'d'office considéré comme datant d'avant l'achat' "
                   "— proving is the SELLER's job (F11094)")
        elif in_window:
            v = "IN_WINDOW_BURDEN_YOURS"
            why = ("still inside the 2-year action window but past "
                   "the presumption: 'c'est à vous d'apporter la "
                   "preuve' (F11094 verbatim)")
        else:
            v = "CONFORMITE_CLOSED"
            why = ("action window closed — the conformity guarantee "
                   "cannot be re-opened by a late claim; vices "
                   "cachés below is the remaining clock")
        out["conformite_verdict"] = {"verdict": v,
                                     "discovered_on": _iso(disc),
                                     "why": why}
        # ---- vices cachés : la DEUXIÈME horloge ----
        sold = _d(sold_on, "sold_on") if sold_on else dl
        v_action = _addm(disc, 24)
        cap = _addm(sold, 240)
        out["vices"] = {
            "discovered_on": _iso(disc),
            "action_by": _iso(v_action),
            "action_by_weekday": _wd(v_action),
            "cap_by": _iso(cap),
            "cap_by_weekday": _wd(cap),
            "cap_anchor": ("sold_on (the 20-year limit runs from the "
                           "day of the SALE, F11007)" if sold_on else
                           "delivered_on used as proxy for the sale "
                           "day — a gift ordered before delivery "
                           "SHIFTS the cap earlier; pass sold_on"),
            "verdict": None,
        }
        if cap < disc:
            out["vices"]["verdict"] = "CAP_PASSED_BEFORE_DISCOVERY"
            out["vices"]["why"] = (
                "the 20-year cap fell on %s, BEFORE the defect was "
                "discovered on %s — the action is born closed"
                % (_iso(cap), _iso(disc)))
        else:
            eff = min(v_action, cap)
            out["vices"]["effective_by"] = _iso(eff)
            out["vices"]["effective_by_weekday"] = _wd(eff)
            out["vices"]["binding"] = ("cap (20y)" if eff == cap
                                       else "action (2y from "
                                            "discovery)")
            if a:
                out["vices"]["days_left"] = (eff - a).days
                out["vices"]["verdict"] = (
                    "VICES_OPEN" if eff >= a else "VICES_CLOSED")
            else:
                out["vices"]["verdict"] = "VICES_DATES_ONLY"
    if claim:
        cq = _d(claim, "claim_requested_on")
        _due(cq + _td(days=30), "remedy_due_by",
             "'dans les 30 jours qui suivent votre demande' — F11094")
        _due(cq + _td(days=14), "refund_due_by",
             "'au plus tard dans les 14 jours calendaires' — F11094; "
             "official example: claimed 3 January -> due 17 "
             "January at midnight; surcharges past due: 10/20/50%")
    out["levers"] = {
        "commercial_window": "/shop/return-deadline — the seasonal "
                             "GOODWILL windows (Fnac/Darty 15-jan, "
                             "Boulanger 31-jan, Apple 8-jan) are a "
                             "different animal than these statutory "
                             "clocks",
        "price_drop": "/shop/pricedrop-refund",
    }
    return out


def _uk(out, dl, cond, disc, a, claim, nation, _due):
    if claim:
        raise WarrantError(
            "claim_requested_on",
            "the UK statute has no dated remedy clock to compute: "
            "s.22(6) STOPS the 30-day clock for the 'waiting period' "
            "between the repair/replacement request and receiving "
            "the goods back — a range no input here closes. The FR "
            "30-day/14-day clocks ARE computable.",
            "omit it for uk, or pass jurisdiction=fr")
    if cond != "new":
        out["condition_note"] = (
            "UK statute does not branch on new/used: every clock "
            "below is identical for a second-hand good (the CRA "
            "silence is tabled as silence — France's 12-month "
            "occasion branch has no UK twin)")
    out["conditions"] = list(_UK_REMEDIES)
    out["verbatim"] = dict(_VERBATIM_UK)
    reject_by = dl + _td(days=30)
    _due(reject_by, "reject_by",
         "short-term right to reject: 'end of 30 days beginning "
         "with the first day after' delivery (s.22(3)) — delivered "
         "day is day zero")
    presum = _addm(dl, 6) - _td(days=1)
    _due(presum, "presumption_by",
         "'within the period of six months beginning with the day "
         "on which the goods were delivered' (s.19(14)) — the "
         "delivery day is day ONE, so the window closes the day "
         "BEFORE the anniversary; this is a BURDEN rule, not a "
         "deadline (¶97: it does not even apply to the 30-day "
         "reject)")
    lim = {}
    lim["england_wales_ni"] = _addm(dl, 72)
    lim["scotland"] = _addm(dl, 60)
    n = (nation or "").lower()
    if n == "scotland":
        _due(_addm(dl, 60), "limitation_by",
             "'in Scottish law the limitation period is five years' "
             "— ¶105 (Prescription and Limitation (Scotland) Act "
             "1973, s.6: prescription EXTINGUISHES the obligation)")
    elif n:
        _due(_addm(dl, 72), "limitation_by",
             "'a limitation period of six years from the date of "
             "the breach of contract' — ¶105 (Limitation Act 1980, "
             "s.5); the breach is deemed to be the delivery day")
    else:
        out["limitation_by"] = {
            "england_wales_northern_ireland": {
                "date": _iso(_addm(dl, 72)),
                "weekday": _wd(_addm(dl, 72))},
            "scotland": {
                "date": _iso(_addm(dl, 60)),
                "weekday": _wd(_addm(dl, 60))},
            "rule": "no nation passed — BOTH travel: six years "
                    "(England/Wales/NI, Limitation Act 1980 s.5) vs "
                    "five (Scotland, 1973 Act s.6), ¶105 verbatim",
        }
        if a:
            out["limitation_by"]["england_wales_northern_ireland"]["days_left"] = (_addm(dl, 72) - a).days
            out["limitation_by"]["scotland"]["days_left"] = (_addm(dl, 60) - a).days
    out["limitation_table_all_nations"] = {
        k: _iso(v) for k, v in sorted(lim.items())}
    if disc:
        lim_end = (_addm(dl, 60) if (nation or "") == "scotland"
                   else _addm(dl, 72))
        if disc <= reject_by:
            v, why = "REJECT_WINDOW_OPEN", (
                "fault within the 30 days: the short-term right to "
                "reject is alive — reject and claim the full refund "
                "(the s.19(14) presumption is NOT what you need, "
                "¶97)")
        elif disc <= presum:
            v, why = "PAST_REJECT_IN_PRESUMPTION", (
                "30-day window closed, but the fault appeared within "
                "six months of delivery: deemed non-conforming at "
                "delivery — repair/replacement track, reversed "
                "burden, seller proves otherwise (s.19(14)-(15))")
        elif disc <= lim_end:
            v, why = "PAST_BURDEN_YOURS_IN_LIMITATION", (
                "outside six months: the presumption is gone but "
                "the limitation period is open — you prove the "
                "defect existed at delivery")
        else:
            v, why = "LIMITATION_PASSED", (
                "outside the limitation period for the nation "
                "named: contract action closed (other claims may "
                "exist — out of table)")
        out["verdict"] = {"verdict": v, "discovered_on": _iso(disc),
                          "why": why}
        if v == "PAST_BURDEN_YOURS_IN_LIMITATION" and nation:
            out["verdict"]["limitation_left_days"] = (lim_end - disc).days
    out["misread_guard"] = (
        "three clocks, not one: 30 days = REFUND right; 6 months = "
        "PROOF burden; 5-6 years = how long you may still SUE — "
        "r/LegalAdviceUK threads fuse them weekly; the six months "
        "never extends the thirty days and the six years is not a "
        "quality promise")
    out["levers"] = {
        "commercial_window": "/shop/return-deadline — the voluntary "
                             "retailer windows (amazon.uk 'whichever "
                             "is later', seasonal Jan-31s) are "
                             "policy, not statute",
        "refund_method": "a statutory refund is money back to the "
                         "payer — store credit is a goodwill "
                         "instrument; never let a window answer "
                         "confuse the two (return-deadline carries "
                         "the fee rows)",
    }
    return out
