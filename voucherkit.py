# -*- coding: utf-8 -*-
"""voucherkit — /shop/gift-voucher : la CARTE CADEAU qui « expire »,
verdict daté, juridictions NOMMÉES, sources officielles rejouées
VERBATIM ce cycle (24-nov-2026).

LA DOULEUR, mesurée par la lentille HUMAIN (20-nov-2026, à J-5 de
Black Friday, à 5 semaines de Noël) : la presse officielle irlandaise
sonne l'alarme — CCPC « Traders told to fix gift voucher faults »
(20-nov, communiqué) — lettres aux hôtels, restaurants, sport,
vêtements, salons de toute l'Irlande ; JD Sports a rendu ≈250 000 €
en juillet pour des bons valables UN AN là où la loi de 2019 dit
CINQ (RTÉ, Irish Times 20-nov). Et la douleur citée par la presse
est la plus quotidienne de toutes : « one of the most common issues
is consumers unable to locate vouchers they were given from last
Christmas ». La carte retrouvée dans un tiroir porte une date morte —
et personne ne dit que la date MORTE EST PEUT-ÊTRE LÉGALEMENT VIVANTE.
Les pages d'aide rendent des règles en prose ; les modèles, eux,
inventent des durées par pays : la file portait « France : 30 ans » —
FAUX, rejoué ce midi : les 30 ans sont ceux des actions RÉELLES
IMMOBILIÈRES (article 2227), pas des cartes cadeaux.

SOURCES REJOUÉES CE CYCLE, texte entier en cache :
  * IE — irishstatutebook.ie, CONSUMER PROTECTION (GIFT VOUCHERS)
    ACT 2019 (No. 38 of 2019), s.2 insère la Part 4A, sections 66A et
    66B, verbatim : expiry date means « the date AFTER WHICH … a gift
    voucher ceases to be redeemable » — le jour dit EST encore
    redeemable ; 66B(1)(a) « at least 5 years from the date on which
    the contract was entered into » ou PAS d'expiry ; 66B(1)(b) LA
    FICTION FERMÉE : « the contract shall be DEEMED to include a term
    … 5 years » ; 66B(1)(c) le deemed OVERRIDE l'express ; 66B(1)(d)
    contraire = offence. Liste close des exclusions 66A(2)(a)-(h) :
    deals datés ≤ 3 mois, LOYALTY, PROMO, AVOIR DE RETOUR (le bon né
    d'un retour n'est pas un gift voucher — frontière avec
    /shop/return-deadline), UTILITIES, chèque/draft/mandat,
    E-MONEY (S.I. 183/2011), non-destiné-à-être-offert. 66B(2)
    durable medium obligatoire ; 66B(3) pas de « tout dépenser d'un
    coup » ; 66B(4) solde « €1 OR MORE » -> dû (cash, electronic
    transfer ou voucher) ; 66B(5) voucher de remplacement : date non
    antérieure, valeur égale ; 66B(6) nom mal orthographié :
    rectification GRATUITE, redemption due ; 66B(7) AUCUNE limite
    nombre de vouchers par transaction ; 66B(8) remplacement volé/perdu
    : pas de date antérieure ; 66B(9) la clause contraire « shall not
    be binding » et le contrat survit sans elle ; 66B(10) LE
    TRANSFÉRÉ tient TOUS les droits — la carte reçue à Noël n'est pas
    un contrat où le porteur n'est pas partie, l'ancre reste la DATE
    D'ACHAT du contrat, jamais la date du cadeau.
  * IE — ccpc.ie pages « Gift vouchers requirements for businesses »
    et consumer, rejouées : borne de commencement NOMMÉE — « sold
    before 2 December 2019 do not have to comply » ; et LA
    CONTRADICTION pêchée : la FAQ d'application écrit « more than
    €1 », le statute écrit « €1 OR MORE » — borne à €1.00 pile : le
    texte de la loi gouverne, le conflit est NOMMÉ, la boundary case
    voyage dans `conflict`.
  * FR — la règle française est l'ABSENCE de règle, rejouée ce midi
    sur QUATRE sources concordantes : kohenavocats.fr (19-nov-2026,
    avocat en droit de la consommation) « aucune loi ne fixe une
    durée minimale ou maximale de validité pour les bons d'achat » ;
    Défense des Consommateurs « le Code de la consommation ne
    comporte pas d'article propre aux cartes cadeaux, aux bons
    d'achat ni aux avoirs » — encadrés L111-1 (information avant
    l'achat), L121-3 (pratique trompeuse), L212-1/L241-1 (clause
    abusive) ; L'Alsace « question conso » (carte expirée avril 2023)
    — « votre seule option est de négocier un geste commercial »,
    « une durée d'un an est parfaitement légale dès lors qu'elle est
    portée à la connaissance du consommateur » ; TF1 Info (Noël) —
    « chaque enseigne fait ce qu'elle veut, elle doit juste le
    préciser dans ses CGV » et le piège de l'ANCRE : « cela peut être
    dès l'émission de la carte ou à activation ».
  * FR — prescription, economie.gouv.fr DGCCRF « Délais de
    prescription » (écrit 16-10-2023, rejouée) : « les actions
    personnelles ou mobilières se prescrivent par CINQ ans à compter
    du jour où le titulaire d'un droit a connu ou aurait dû connaître
    les faits » (article 2224) — point de départ FLOTTANT, donc
    ANCRÉ NON COMPUTABLE : la page FR rend la règle et REFUSE la
    date, classe des « or longer if » de keep-records. Et la
    CORRECTION que cet outil existe pour rendre : les 30 ans (2227)
    sont les actions réelles immobilières — pas les cartes cadeaux.

CONTRAT : jurisdiction IE|FR + purchased_on (l'ancre du contrat — la
date du CADEAU n'ancre rien, 66B(10) le dit) + printed_expiry_on
optionnel + no_expiry_term + excluded_class (liste close a-h) +
remaining_eur (Decimal en chaîne, jamais float) + clash (liste close
des actes du marchand) + as_of optionnel — JAMAIS d'horloge murale.
UK, BR, US : REFUSÉS PAR NOM portant leur fait (non rejoués ce
cycle — la table ne se remplit pas de mémoire).

ZÉRO réseau, zéro horloge, zéro conseil d'achat : l'outil rend des
DATES, des VERDICTS CLOSES et les verbatims — le geste commercial
éventuel reste à l'humain.
"""

VOUCHER_TABLE_VERSION = "2026-11-24"
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday")
_S = "published"  # texte officiel rejoué verbatim ce cycle

import calendar as _cal
from datetime import date as _date, timedelta as _td
from decimal import Decimal, InvalidOperation

# Commencement borne NOMMÉE par la page CCPC d'application :
# « Gift vouchers sold before 2 December 2019 do not have to comply
# with the Act. » — 2 déc. INclus dans le champ.
_COMMENCEMENT = _date(2019, 12, 2)
_ONE_EUR = Decimal("1")

# vocabulaires fermés
_ALIASES_IE = ("ie", "irl", "ireland", "irlande", "irish", "eire",
               "dublin", "ccpc")
_ALIASES_FR = ("fr", "fra", "france", "francais", "francaise")
_ALIASES_UK = ("uk", "gb", "united kingdom", "great britain",
               "reyaume uni", "britain", "british", "england",
               "angleterre", "scotland", "ecosse", "wales", "gwynedd",
               "kingdom")
_ALIASES_BR = ("br", "brazil", "brasil", "brasileira", "brasileiro")
_ALIASES_US = ("us", "usa", "united states", "etats unis",
               "states", "amerique")

# 66A(2)(a)-(h) — liste CLOSE, chaque classe porte son verbatim.
EXCLUDED_CLASSES = {
    "discount_date_period":
        "66A(2)(a): redeemable only for the purchase, at a discounted "
        "price, of specified goods or specified services, from a "
        "specified trader or traders — 'on a specified date' or 'for "
        "a specified period of a limited duration not exceeding 3 "
        "months' — the deal-voucher shape sits OUTSIDE the Act",
    "loyalty": "66A(2)(b): 'supplied under a customer loyalty scheme'",
    "promotional":
        "66A(2)(c): 'supplied in connection with a promotional scheme "
        "that is connected to the purchase of specified goods or "
        "specified services'",
    "return_refund":
        "66A(2)(d): 'supplied by way of a refund for goods returned "
        "to a trader' — the credit BORN OF A RETURN is not a gift "
        "voucher: the return window itself is /shop/return-deadline",
    "utility":
        "66A(2)(e): 'redeemable only in exchange for goods or "
        "services relating to telephone services, internet services, "
        "fuel, electricity, heating or any other utility'",
    "payment_instrument":
        "66A(2)(f): 'a cheque, bank draft or postal money order'",
    "emoney":
        "66A(2)(g): 'constitutes electronic money, within the "
        "meaning of the European Communities (Electronic Money) "
        "Regulations 2011 (S.I. No. 183 of 2011)'",
    "not_a_gift":
        "66A(2)(h): 'not supplied, marketed, provided or otherwise "
        "made available to be given as a gift' — self-bought credit "
        "is outside the Act",
}

# Les actes du marchand que le porteur rencontre au comptoir —
# chacun meurt contre une SECTION nommée de 66B.
CLASHES = {
    "single_use_required":
        "66B(3): 'A gift voucher contract shall not contain a term "
        "requiring the full value of a gift voucher to be redeemed "
        "in a single transaction' — the term is void (66B(9)) and "
        "entering it is an offence (66B(3)(b))",
    "voucher_count_limited":
        "66B(7): 'shall not contain a term that places a limit on "
        "the number of gift vouchers that a person is permitted to "
        "redeem in a single transaction' — no stacking cap survives "
        "the Act (CCPC business page: 'There can be no restriction "
        "on the number of vouchers used in a single transaction')",
    "name_mismatch_fee":
        "66B(6): the named person 'may redeem the gift voucher "
        "notwithstanding a difference between that person's name … "
        "and as it appears on that person's passport, driving "
        "licence, or any other form of personal identification', and "
        "the name 'may be amended or changed without a fee being "
        "charged'",
    "replacement_earlier_expiry":
        "66B(8): a replacement for a lost or stolen voucher 'shall "
        "not be subject to an expiry date that is earlier than the "
        "expiry date of the gift voucher that it replaces'",
}

_VERBATIM_IE = {
    "five_year_floor":
        "66B(1)(a): 'a gift voucher contract shall contain a term "
        "that the gift voucher is — (i) subject to an expiry date "
        "that is at least 5 years from the date on which the "
        "contract was entered into, or (ii) not subject to an "
        "expiry date'",
    "deemed_term":
        "66B(1)(b): 'Where a gift voucher contract does not include "
        "a term satisfying paragraph (a), the contract shall be "
        "deemed to include a term that the gift voucher is subject "
        "to an expiry date that is 5 years from the date on which "
        "the contract was entered into'",
    "deemed_overrides":
        "66B(1)(c): the deemed term, where it conflicts with an "
        "express term, 'shall override the express term' — the "
        "printed date loses to the legal date",
    "expiry_definition":
        "66A(1): 'expiry date' means 'the date after which, by "
        "virtue of the passage of time, a gift voucher ceases to be "
        "redeemable' — ON the printed day the voucher has NOT yet "
        "ceased: the day named is still redeemable",
    "balance_one_euro":
        "66B(4): where part was redeemed 'such that the remaining "
        "balance of the gift voucher is \u20ac1 or more' and the "
        "contract prevents redeeming it in another transaction, the "
        "contract is deemed to require reimbursement 'in cash, by "
        "electronic transfer or by way of a gift voucher'",
    "replacement_equals":
        "66B(5): a replacement voucher must carry 'an expiry date "
        "not earlier than the expiry date' of the original and "
        "'a value equal to that of the remaining balance'",
    "transferee":
        "66B(10): a person who 'gives, sells or otherwise transfers' "
        "the voucher passes the contract rights — the third person "
        "'shall be entitled to exercise all rights under the gift "
        "voucher contract on the same terms'. The anchor stays the "
        "contract DATE: a gift received at Christmas does not move "
        "the five-year clock",
    "void_and_survives":
        "66B(9): a term contrary to 66B 'shall not be binding' on "
        "the non-trader party, and the contract 'shall continue to "
        "bind the parties … if it is capable of continuing in "
        "existence without the term'",
}

_SOURCES_IE = [
    "Consumer Protection (Gift Vouchers) Act 2019 (No. 38 of 2019), "
    "s.2 — Part 4A, sections 66A-66B, irishstatutebook.ie, replayed "
    "24-nov-2026 verbatim",
    "ccpc.ie 'Gift vouchers requirements for businesses' — 'A "
    "voucher with an expiry date of less than five years is deemed "
    "to have a five-year expiry'; 'sold before 2 December 2019 do "
    "not have to comply'",
    "ccpc.ie press release 20-nov-2026 'Traders told to fix gift "
    "voucher faults' + RT\u00c9 20-nov-2026 (JD Sports \u2248\u20ac250,000 "
    "refunds, July 2026, one-year vouchers)",
]

_VERBATIM_FR = {
    "aucune_duree_legale":
        "kohenavocats.fr (19-nov-2026, rejoué) : « aucune loi ne "
        "fixe une durée minimale ou maximale de validité pour les "
        "bons d'achat » — la liberté contractuelle a des bornes "
        "d'INFORMATION, pas de durée",
    "code_sans_article":
        "Défense des Consommateurs (fiche rejouée) : « le Code de "
        "la consommation ne comporte pas d'article propre aux "
        "cartes cadeaux, aux bons d'achat ni aux avoirs, de sorte "
        "que la durée de validité, l'usage du solde et le "
        "remboursement dépendent d'abord des conditions de "
        "l'émetteur » ; encadrés L111-1, L121-3, L212-1, L241-1",
    "information_avant_achat":
        "L111-1 (cité rejoué) : « Avant que le consommateur ne "
        "soit lié par un contrat à titre onéreux, le professionnel "
        "communique au consommateur, de manière lisible et "
        "compréhensible, les informations suivantes » ; TF1 Info "
        "(Noël, rejoué) : « chaque enseigne fait ce qu'elle veut, "
        "elle doit juste le préciser dans ses conditions générales "
        "de vente »",
    "ancre_emission_ou_activation":
        "TF1 (rejoué) : « Cela peut être dès l'émission de la "
        "carte ou à activation » ; usuel (avantagescarte, rejoué) : "
        "« douze mois à compter de l'achat ou de l'activation est "
        "la durée la plus fréquente » — l'ancre est un FAIT du "
        "contrat, jamais une moyenne",
    "seule_option_geste":
        "L'Alsace « question conso » (rejoué, carte périmée avril "
        "2023) : « Une durée de validité d'un an est parfaitement "
        "légale dès lors qu'elle est portée à la connaissance du "
        "consommateur » ; « Si votre carte cadeau est périmée "
        "aujourd'hui, votre seule option est de négocier un geste "
        "commercial de la part de l'enseigne »",
    "prescription_cinq_ans":
        "economie.gouv.fr DGCCRF « Délais de prescription » (écrit "
        "16-10-2023, rejouée) : « les actions personnelles ou "
        "mobilières se prescrivent par cinq ans à compter du jour "
        "où le titulaire d'un droit a connu ou aurait dû connaître "
        "les faits lui permettant de l'exercer » (article 2224)",
    "trente_ans_corrige":
        "CORRECTION que cet outil existe pour rendre : les 30 ans "
        "de la page DGCCRF sont ceux des « actions réelles "
        "immobilières » (article 2227) — pas celui des cartes "
        "cadeaux. La rumeur « solde prescrit par 30 ans en France » "
        "est un prêt entre régimes, refusé ici",
}

_SOURCES_FR = [
    "kohenavocats.fr 19-nov-2026 ; defense-des-consommateurs.fr "
    "(fiche carte cadeau) ; lalsace.fr 'question conso' 27-fev-2024 ; "
    "tf1info.fr (Noel, validite des cartes cadeaux) ; "
    "avantagescarte.com — toutes rejouees 24-nov-2026",
    "economie.gouv.fr DGCCRF 'Delais de prescription' (16-10-2023) — "
    "rejouee ce cycle : 5 ans (2224) droit commun consommateur ; "
    "30 ans = actions reelles immobilieres (2227)",
]

_REFUSAL = {
    "UK": ("the UK gift-card regime (contract terms + Consumer "
           "Rights Act 2015 unfair-terms screen + CMA guidance on "
           "unredeemed balances) was NOT replayed to the verbatim "
           "standard this cycle — a table entry needs its official "
           "text, not my memory. Queued; refused here by name."),
    "BR": ("the Brazilian vale-presente regime was NOT replayed "
           "this cycle — refused by name, queued. Coding it from "
           "memory is exactly the fault this house refuses: the "
           "Irish five-year floor does not travel to the Mercosul."),
    "US": ("US gift-card expiry is STATE law and diverges state by "
           "state — there is NO single national date to count, and "
           "no state page was replayed this cycle. Refused by name "
           "rather than invented as a date."),
}


class VoucherError(Exception):
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
        raise VoucherError(field, "not an ISO calendar date: %r" % (s,),
                           "YYYY-MM-DD, e.g. 2025-12-20")


def _iso(d):
    return d.isoformat()


def _wd(d):
    return WEEKDAYS[d.weekday()]


def _addy(d, n):
    """Anniversaire n annees plus tard ; quantieme inexistant ->
    DERNIER jour du mois cible (2024-02-29 + 5 -> 2029-02-28) —
    regle ECRITE dans la reponse, meme convention que la maison."""
    m = d.month
    target_year = d.year + n
    day = min(d.day, _cal.monthrange(target_year, m)[1])
    return _date(target_year, m, day)


_YEAR_RULE = ("year math = calendar anniversary; when the target "
              "year has no such day (29 February in a non-leap "
              "year), the LAST day of that month is the anniversary "
              "— 2024-02-29 + 5 years = 2029-02-28")
_DAY_RULE = ("expiry-day reading from 66A(1): 'the date after "
             "which … ceases to be redeemable' — on the expiry "
             "date itself the voucher is still redeemable "
             "(as_of <= expiry == alive)")


def _jur(s):
    t = str(s or "").strip().lower()
    # accents + separateurs : « ÉIRE », « États-Unis », « United-
    # Kingdom » — normalisation nominative, pas de LM.
    t = (t.replace("é", "e").replace("è", "e").replace("ê", "e")
         .replace("û", "u").replace("ô", "o").replace("ç", "c")
         .replace("à", "a").replace("á", "a").replace("ã", "a")
         .replace("õ", "o").replace("í", "i").replace("ñ", "n")
         .replace("-", " ").replace("_", " ").strip())
    words = set(t.split())
    if words & set(_ALIASES_IE):
        return "IE"
    if words & set(_ALIASES_FR):
        return "FR"
    if ("united states" in t or "etats unis" in t
            or words & set(_ALIASES_US)):
        raise VoucherError("jurisdiction", "US refused by name: " +
                           _REFUSAL["US"], "ie or fr")
    if ("united kingdom" in t or "great britain" in t
            or "royaume uni" in t or "reino unido" in t
            or words & set(_ALIASES_UK)):
        raise VoucherError("jurisdiction", "UK refused by name: " +
                           _REFUSAL["UK"], "ie or fr")
    if words & set(_ALIASES_BR):
        raise VoucherError("jurisdiction", "BR refused by name: " +
                           _REFUSAL["BR"], "ie or fr")
    raise VoucherError(
        "jurisdiction",
        "unknown jurisdiction %r — the replayed tabled regimes are "
        "exactly Ireland (five-year floor, Act 2019) and France "
        "(NO statutory minimum, replayed sources); UK/BR/US are "
        "refused by name carrying their fact" % (s,),
        "ie | ireland | irlande | fr | france (see refusal texts)")


def _dec(s, field):
    try:
        v = Decimal(str(s).replace(",", "."))
    except InvalidOperation:
        raise VoucherError(field, "not a decimal money string: %r" % (s,),
                           "'12.50' — string Decimal, never a float")
    if v < 0:
        raise VoucherError(field, "negative balance %r — the statute "
                           "reimburses a REMAINING balance, the "
                           "number cannot be under zero" % (s,),
                           ">= 0, e.g. '1.00'")
    return v


def gift_voucher(jurisdiction, purchased_on, printed_expiry_on=None,
                 no_expiry_term=False, excluded_class=None,
                 remaining_eur=None, clash=None, as_of=None):
    j = _jur(jurisdiction)
    p = _d(purchased_on, "purchased_on")
    pe = _d(printed_expiry_on, "printed_expiry_on") if printed_expiry_on \
        else None
    a = _d(as_of, "as_of") if as_of else None

    if pe and pe < p:
        raise VoucherError(
            "printed_expiry_on",
            "expiry %s before the contract date %s — a voucher "
            "cannot expire before it was bought; one of the two "
            "dates is misread (the Act counts FROM the contract "
            "date, 66B(1)(a))" % (_iso(pe), _iso(p)),
            "printed_expiry_on >= purchased_on, or omit it")
    if no_expiry_term and pe:
        raise VoucherError(
            "no_expiry_term",
            "no_expiry_term and printed_expiry_on contradict each "
            "other — the contract either names a date (66B(1)(a)(i)) "
            "or declares none (66B(1)(a)(ii)); both at once is a "
            "misread, not a term",
            "keep one: the printed date, or the no-expiry claim")
    if a and a < p:
        raise VoucherError(
            "as_of",
            "as_of %s is before purchased_on %s — the contract was "
            "not entered into at the day you ask about" %
            (_iso(a), _iso(p)),
            "as_of >= purchased_on")
    if excluded_class is not None and \
            str(excluded_class) not in EXCLUDED_CLASSES:
        raise VoucherError(
            "excluded_class",
            "unknown exclusion class %r — 66A(2) is a CLOSED list "
            "of eight letters, nothing else walks out of the Act"
            % (excluded_class,),
            "one of: " + ", ".join(sorted(EXCLUDED_CLASSES)))
    if clash is not None and str(clash) not in CLASHES:
        raise VoucherError(
            "clash",
            "unknown clash %r — the named counter acts are exactly "
            "these four, each void against a numbered subsection"
            % (clash,),
            "one of: " + ", ".join(sorted(CLASHES)))
    rem = _dec(remaining_eur, "remaining_eur") \
        if remaining_eur is not None else None

    out = {
        "jurisdiction": j,
        "purchased_on": _iso(p),
        "purchased_weekday": _wd(p),
        "table_version": VOUCHER_TABLE_VERSION,
        "provenance": _S,
        "computations": {
            "year_rule": _YEAR_RULE,
            "expiry_day_rule": _DAY_RULE,
        },
    }
    if pe:
        out["printed_expiry_on"] = _iso(pe)
        out["printed_weekday"] = _wd(pe)
    if a:
        out["as_of"] = _iso(a)

    if j == "IE":
        _ie(out, p, pe, bool(no_expiry_term), excluded_class, rem,
            clash, a)
    else:
        _fr(out, p, pe, excluded_class, clash, a)
    return out


def _ie(out, p, pe, no_expiry, excluded_class, rem, clash, a):
    out["act"] = ("Consumer Protection (Gift Vouchers) Act 2019 "
                  "(No. 38 of 2019), Part 4A s.66A-66B")
    out["sources"] = list(_SOURCES_IE)
    out["verbatim"] = dict(_VERBATIM_IE)
    deemed = _addy(p, 5)
    out["deemed_expiry_on"] = _iso(deemed)
    out["deemed_weekday"] = _wd(deemed)
    out["commencement_gate"] = {
        "date": _iso(_COMMENCEMENT),
        "rule": "CCPC business page verbatim: 'Gift vouchers sold "
                "before 2 December 2019 do not have to comply with "
                "the Act' — this contract date %s is %s the Act"
                % (_iso(p), "INSIDE" if p >= _COMMENCEMENT
                   else "BEFORE"),
    }

    # 1) la liste CLOSE des instruments hors Act (66A(2))
    if excluded_class is not None:
        out["verdict"] = "EXCLUDED_OUT_OF_SCOPE"
        out["excluded_class"] = str(excluded_class)
        out["why"] = EXCLUDED_CLASSES[str(excluded_class)]
        out["no_dates_computed"] = (
            "the Act never reaches this instrument — printing the "
            "five-year dates for it would be the false promise; the "
            "contract's own terms govern")
        return

    # 2) le gate de commencement
    if p < _COMMENCEMENT:
        out["verdict"] = "PRE_COMMENCEMENT"
        out["why"] = ("purchased %s is before 2 December 2019 — the "
                      "Act's own gate (CCPC: 'sold before 2 December "
                      "2019 do not have to comply'). The five-year "
                      "floor does not reach back; the printed "
                      "expiry, if any, is the contract's date. The "
                      "deemed block above shows what the date WOULD "
                      "have been — it travels as reference, never "
                      "as a claim" % (_iso(p),))
        return

    # 3) la branche des dates
    if no_expiry:
        out["verdict"] = "COMPLIANT_NO_EXPIRY"
        out["legal_expiry_on"] = None
        out["why"] = ("66B(1)(a)(ii) is a legal term on its own: "
                      "'not subject to an expiry date' — the voucher "
                      "carries no death day. If the printed sheet "
                      "says otherwise, the printed sheet lost (66B(9))")
        if a:
            out["status"] = "ALIVE"
            out["days_left"] = None
            out["status_rule"] = ("no expiry day exists; alive is "
                                  "forever, the day-count has no "
                                  "end to run toward")
    elif pe is None:
        out["verdict"] = "DEEMED_FIVE_YEAR"
        out["legal_expiry_on"] = _iso(deemed)
        out["why"] = ("the contract states no expiry term at all — "
                      "66B(1)(b) deems one: '5 years from the date "
                      "on which the contract was entered into'. "
                      "Silence is not openness: the deemed day "
                      "governs, and 66B(2) says the trader had to "
                      "put a date or a no-expiry statement on a "
                      "durable medium anyway")
        _alive(out, deemed, a)
    elif pe < deemed:
        out["verdict"] = "ILLEGAL_SHORT_EXPIRY"
        out["legal_expiry_on"] = _iso(deemed)
        out["paper_vs_law"] = {
            "printed": _iso(pe),
            "deemed": _iso(deemed),
            "days_the_printed_date_stole": (deemed - pe).days,
            "rule": "66B(1)(b)+(c): a term shorter than five years "
                    "is deemed replaced by the five-year term and "
                    "the deemed term OVERRIDES the express one — "
                    "exactly the JD Sports shape (one-year vouchers, "
                    "\u2248\u20ac250,000 refunded July 2026, CCPC/RT\u00c9)",
        }
        _alive(out, deemed, a, printed=pe)
    else:
        out["verdict"] = "COMPLIANT_EXPLICIT"
        out["legal_expiry_on"] = _iso(pe)
        out["why"] = ("the printed day is at least five years from "
                      "the contract day (66B(1)(a)(i)) — the paper "
                      "date IS the legal date; on or before it the "
                      "voucher redeems, after it the contract "
                      "expired lawfully and nothing here revives it")
        _alive(out, pe, a)

    # 4) le solde — la borne euro (66B(4)+(5)), NOMMÉE à €1.00 pile
    if rem is not None:
        rblock = {}
        if rem >= _ONE_EUR:
            rblock["verdict"] = "REFUND_RIGHT"
            rblock["balance"] = str(rem)
            rblock["rule"] = ("66B(4): remaining balance \u20ac1 or "
                              "more + a contract term blocking it "
                              "in another transaction -> the term "
                              "is deemed replaced: reimbursement is "
                              "owed 'in cash, by electronic "
                              "transfer or by way of a gift "
                              "voucher'; if by voucher, 66B(5): "
                              "'expiry date not earlier than' the "
                              "original and value equal to the "
                              "balance")
            if rem == _ONE_EUR:
                rblock["conflict"] = {
                    "field": "euro floor (balance exactly \u20ac1.00)",
                    "positions": {
                        "statute_eur1_or_more":
                            "66B(4)(a)(i) verbatim: 'such that the "
                            "remaining balance of the gift voucher "
                            "is \u20ac1 or more'",
                        "ccpc_faq_more_than":
                            "CCPC business FAQ paraphrase: 'If more "
                            "than \u20ac1 remains, the balance can be "
                            "refunded…'",
                    },
                    "handling": "the statute governs at exactly "
                                "\u20ac1.00: 'or more' includes the "
                                "boundary — the FAQ sentence is a "
                                "summary, not the section. Conflict "
                                "NAMED, both texts shipped",
                }
        else:
            rblock["verdict"] = "SILENT_BELOW_EUR1"
            rblock["balance"] = str(rem)
            rblock["rule"] = ("66B(4) deems a refund term only from "
                              "'\u20ac1 or more'; below that the "
                              "statute is SILENT — the contract "
                              "governs, and this tool refuses to "
                              "invent a right the section does not "
                              "print. (The same boundary, read "
                              "backwards, is the CCPC-FAQ wording — "
                              "see the conflict that ships at "
                              "\u20ac1.00)")
        out["refund_block"] = rblock

    # 5) l'acte du marchand — nul contre une section nommée
    if clash is not None:
        out["term_clash"] = {
            "clash": str(clash),
            "void_against": CLASHES[str(clash)],
            "effect": "66B(9): a contrary term 'shall not be "
                      "binding' on you and the contract continues "
                      "without it; entering it is an offence under "
                      "the quoted subsection",
        }

    out["conditions"] = [
        "durable medium (66B(2)): the expiry date, or the contract "
        "date + redemption period, or 'no expiry' — ON the voucher "
        "or on paper/email supplied with it; a date buried only in "
        "unreadable CGV is the trader's breach, not the holder's",
        "the clock anchors on the CONTRACT date — a gift handed "
        "over later moves nothing (66B(1)(a)(i) + 66B(10))",
        "the Act also covers business-to-business voucher sales "
        "(CCPC business page)",
        "lost voucher: a replacement may not carry an earlier "
        "expiry (66B(8)); ask for proof-of-purchase reissue with "
        "the ORIGINAL date",
    ]


def _alive(out, legal, a, printed=None):
    if a is None:
        return
    if a <= legal:
        if printed is not None and a > printed:
            # LA shape JD Sports : le papier dit mort, la loi dit vivant.
            out["status"] = "PAPER_DEAD_LAW_ALIVE"
            out["days_left"] = (legal - a).days
            out["status_rule"] = ("the printed day %s has passed but "
                                  "the deemed day has not — the "
                                  "printed date was overridden by "
                                  "66B(1)(c): on the counter the "
                                  "law, not the paper, governs; the "
                                  "days below run to the LEGAL day"
                                  % (_iso(printed),))
            return
        out["status"] = "ALIVE"
        out["days_left"] = (legal - a).days
        out["status_rule"] = ("as_of <= legal expiry: redeemable — "
                              "66A(1) makes the expiry 'the date "
                              "AFTER which' the voucher ceases, so "
                              "the day itself still redeems")
    else:
        out["status"] = "DEAD"
        out["days_since"] = (a - legal).days
        out["status_rule"] = ("as_of is past the LEGAL (deemed or "
                              "printed) expiry — dead lawfully; "
                              "nothing in the Act revives it")
        if out.get("verdict") == "ILLEGAL_SHORT_EXPIRY":
            out["status"] = "DEAD_EVEN_DEEMED"
            out["status_rule"] = ("the printed date was illegal AND "
                                  "the deemed five-year date has "
                                  "also passed — the paper was "
                                  "wrong, the clock has since run "
                                  "out anyway; report the sold "
                                  "short window to CCPC (the act "
                                  "itself is the offence, 66B(1)(d))")


def _fr(out, p, pe, excluded_class, clash, a):
    if excluded_class is not None or clash is not None:
        raise VoucherError(
            "excluded_class" if excluded_class is not None else "clash",
            "this field belongs to the Irish Act (66A(2) exclusions "
            "and 66B clashes) — France tables NO equivalent "
            "nullification: the French regime is 'the contract "
            "governs, framed by L111-1/L121-3/L212-1'. Ask IE with "
            "it, or FR without it",
            "omit for FR, use with jurisdiction=ie")
    out["sources"] = list(_SOURCES_FR)
    out["verbatim"] = dict(_VERBATIM_FR)
    out["verdict"] = "NO_STATUTORY_MINIMUM"
    out["rule"] = ("France has NO legal floor or ceiling for gift-"
                   "card validity: the printed date is CONTRACTUAL. "
                   "It binds only if it was brought to the buyer's "
                   "knowledge before purchase (L111-1) and it can "
                   "be attacked as unbalanced (L212-1) — but no "
                   "section voids a short expiry AS SUCH, unlike "
                   "Ireland's 66B(1). The five-year rule does NOT "
                   "travel across the Channel")
    if pe is None:
        out["date_status"] = ("NO_PRINTED_DATE — the contract's "
                              "CGV is the only source of the term; "
                              "find it (email, till receipt, issuer "
                              "site) before assuming anything")
    else:
        out["date_status"] = ("printed %s — contractual force only: "
                              "valid if disclosed before purchase, "
                              "contestable if hidden (L111-1) or "
                              "unbalanced (L212-1); NOT void by law "
                              "for being short" % (_iso(pe),))
        if a:
            if a <= pe:
                out["status"] = "ALIVE_ON_PAPER"
                out["days_left"] = (pe - a).days
            else:
                out["status"] = "DEAD_ON_PAPER"
                out["days_since"] = (a - pe).days
                out["paper_rule"] = (
                    "past the printed day the issuer may lawfully "
                    "refuse — L'Alsace 'question conso' verbatim: "
                    "'votre seule option est de negocier un geste "
                    "commercial'; no date here revives the card. "
                    "The contestable path is the DISCLOSURE of the "
                    "date (L111-1), not its length")
    out["prescription_block"] = {
        "period_years": 5,
        "anchor": "article 2224 civil code — 'a compter du jour ou "
                  "le titulaire d'un droit a connu ou aurait du "
                  "connaitre les faits'",
        "computable": False,
        "why_blocked": ("the start is FLOATING by statute: the day "
                        "you knew or ought to have known. Refusing "
                        "the date beats inventing it — pass the "
                        "knew-on day nowhere; this tool never "
                        "guesses it. Same house class as the 'or "
                        "longer if' conditions money_keep_records_uk "
                        "carries BLOCKED"),
        "correction": ("the '30 years' rumour about dormant gift-"
                       "card balances belongs to real-property "
                       "actions (article 2227, DGCCRF page "
                       "rejouée) — NOT to gift cards. Named and "
                       "refused here"),
    }
    out["conditions"] = [
        "anchor warning (rejoue) : la duree court des l'EMISSION ou "
        "de l'ACTIVATION selon l'emetteur — le point de depart est "
        "un FAIT du contrat, jamais une moyenne",
        "multi-enseignes vs mono-magasin et monnaie electronique "
        "(L315-1/L525-5 CMF) changent le regime (defense-des-"
        "consommateurs, rejoue) — la qualification de l'instrument "
        "precede tout calcul",
        "bought at distance: the 14-day withdrawal may still be "
        "open depending on qualification (the replayed fiche names "
        "L221-2, L221-18, L221-24, L221-28 with the financial-"
        "services carve-out) — a RETURN question, and this tool "
        "computes nothing there: named, bounded, refused",
    ]
