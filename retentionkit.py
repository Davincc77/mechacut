# -*- coding: utf-8 -*-
"""retentionkit — /money/keep-records-uk : la date la plus PROCHE où
un document britannique peut être détruit, calculée par RÈGLE OFFICIELLE
rejouée VERBATIM, ancre par ancre, conflits et blocages NOMMÉS.

LA DOULEUR, mesurée par la lentille HUMAIN (cycle 24-nov-2026) : la
question de janvier est « puis-je jeter ce classeur ? ». Le mot
« six ans » est un SEUL mot pour QUATRE ANCRES DIFFÉRENTES que les
pages d'aide et les modèles écrasent l'une sur l'autre :

  * VAT (HMRC Compliance Handbook CH15200, rejoué ce cycle) : le même
    « 6 years » DÉMARRE SELON LA NATURE DU DOCUMENT — « Records such
    as invoices should be retained for 6 years from the date of issue »
    (et la phrase que personne ne cite : « the 6-year period runs not
    from the date of the future event but from the date on which the
    document itself is issued » — une facture décrivant un événement
    FUTUR compte dès son ÉMISSION) ; « 6 years from the date they are
    prepared » pour les RÉSUMÉS (balance sheet, trading account) ;
    « 6 years from the date of the last entry » pour les SÉRIES
    (daybooks, ledgers, stock books, relié ou électronique — CH15500).
    GOV.UK (charge-reclaim-record-vat) : « at least 6 years (or 10
    years if you are using the VAT One Stop Shop (OSS) scheme or used
    the VAT Mini One Stop Shop (MOSS) scheme) ». Bad debt : « keep
    this information for 4 years after the claim is made, or 10 years
    if you used the VAT MOSS ».
  * LIMITED COMPANY côté HMRC (running-a-limited-company) : « 6 years
    from the end of the last company financial year they relate to,
    or longer if » — QUATRE conditions nommées, dont DEUX ne donnent
    AUCUNE date fixe (retard de déclaration, compliance check
    ouverte) : portées BLOCKED, jamais devinées.
  * LA MÊME COMPTABILITÉ côté companies (Companies Act 2006 s.388(4),
    legislation.gov.uk, SLD 2026-07-24) : « in the case of a private
    company, for three years from the date on which they are made ...
    in the case of a public company, for six years » — deux durées,
    une TROISIÈME ancre (date de CRÉATION). Les deux règles voyagent
    ensemble et c'est la règle officielle qui arbitre : « If a record
    falls within more than one of the categories above, apply the
    longer retention period » / « must be kept for the longest period
    required by those purposes » (CH15400/CH14100).
  * SELF-EMPLOYED (gov.uk) : « at least 5 years after the 31 January
    submission deadline of the relevant tax year » — une deadline
    DÉRIVÉE, pas une date du document — EXEMPLE OFFICIEL inclus :
    « If you sent your 2022 to 2023 tax return online by 31 January
    2024, you must keep your records until at least the end of
    January 2029 » — la convention « until at least » EST écrite là.
    Et le deuxième régime : « If you send your tax return more than
    4 years after the deadline, you'll need to keep your records for
    15 months after you send your tax return » — ancre d'ENVOI.
  * PAYE/CIS : « keep them for 3 years from the end of the tax year
    they relate to » (gov.uk paye-for-employers ; CH14700 couvre
    PAYE ET Construction Industry Scheme). L'« année fiscale » est
    DÉFINIE PAR LA LOI : ITA 2007 s.4(3) « A tax year begins on
    6 April and ends on the following 5 April » — l'outil REFUSE
    toute autre date de fin que 5 avril, et le dit.
  * CH15400, table des minima par catégorie manuelle, ESTAMPILLÉE
    « Updated: 23 November 2026 » — rejouée la VEILLE de ce build :
    dockets « No minimum period », ordres/notes 1 an, import/export
    et daybooks 3 ans, factures d'achat 4 ans, relevés bancaires et
    accounts 5 ans, « Any record containing the VAT account: 6 years
    (No reduction) » ; caveat CH15100 : la période spécifiée « is not
    to exceed 6 years » et HMRC « can specify a shorter period ».

CE QUE L'OUTIL NE FAIT PAS : il ne conseille pas — il rend la date.
Les régimes non rejoués sont REFUSÉS PAR NOM, portant leur fait
candidate : le raccourci « 22 months » des dossiers personnels non
professionnels (définition dans un PDF d'aide archivé, plus de page
gov.uk courante), le National Minimum Wage (6 ans depuis la pay
reference period, rules 2015 — non rejoué), les contrats de travail,
le RGPD (régime de suppression, pas de rétention), la droit commercial
français (10 ans Clôture des comptes — hors de cette juridiction).

CONVENTION DE COMPUT (portée dans chaque réponse) : retain_until =
anniversaire de l'ancre + N années/mois, ARRONDI AU DERNIER JOUR du
mois cible quand le quantième n'existe pas (règle héritée du kit
garantie) ; la page officielle dit « until at least the end of
January 2029 » — le jour dit est le DERNIER jour de rétention, donc
earliest_destroy_on = retain_until + 1 jour. Zéro réseau, zéro
horloge murale : `as_of` est un argument, jamais un now().
"""

RETENTION_TABLE_VERSION = "2026-11-24"

import calendar as _cal
from datetime import date as _date, timedelta as _td

_S = "rejoué verbatim 2026-11-24"  # chaque source porte son empreinte


class RetentionError(Exception):
    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected


def _d(s, field):
    if not isinstance(s, str):
        raise RetentionError(field, "not a date string: %r" % (s,),
                             "YYYY-MM-DD, e.g. 2026-11-24")
    try:
        y, m, d = (int(x) for x in s.split("-"))
        return _date(y, m, d)
    except Exception:
        raise RetentionError(field, "not an ISO calendar date: %r" % (s,),
                             "YYYY-MM-DD, e.g. 2026-11-24")


def _anniv(d, years=0, months=0):
    """Anniversaire + N, clampé au dernier jour du mois cible."""
    if years:
        y, m = d.year + years, d.month
    else:
        total = d.year * 12 + d.month - 1 + months
        y, m = divmod(total, 12)
        m += 1
    return _date(y, m, min(d.day, _cal.monthrange(y, m)[1]))


def _iso(d):
    return "%04d-%02d-%02d" % (d.year, d.month, d.day)


# ---------------- sources (verbatim, cache complet ce cycle) -------
SOURCES = {
    "ch15200": {
        "url": "gov.uk/hmrc-internal-manuals/compliance-handbook/ch15200",
        "stamp": _S},
    "charge_reclaim": {
        "url": "gov.uk/charge-reclaim-record-vat/keeping-vat-records",
        "stamp": _S},
    "ch15100": {
        "url": "gov.uk/hmrc-internal-manuals/compliance-handbook/ch15100",
        "stamp": _S},
    "ch15400": {
        "url": "gov.uk/hmrc-internal-manuals/compliance-handbook/ch15400",
        "stamp": _S + " — page estampillée « Updated: 23 November 2026 »"},
    "running_ltd": {
        "url": "gov.uk/running-a-limited-company/company-and-accounting-records",
        "stamp": _S},
    "s388": {
        "url": "legislation.gov.uk/ukpga/2006/46/section/388 (SLD 2026-07-24)",
        "stamp": _S},
    "sa_how_long": {
        "url": "gov.uk/self-employed-records/how-long-to-keep-your-records",
        "stamp": _S},
    "mtd_example": {
        "url": "gov.uk/guidance/use-making-tax-digital-for-income-tax/if-your-circumstances-change",
        "stamp": _S},
    "paye": {
        "url": "gov.uk/paye-for-employers/keeping-records",
        "stamp": _S},
    "ch14700": {
        "url": "gov.uk/hmrc-internal-manuals/compliance-handbook/ch14700",
        "stamp": _S},
    "expenses": {
        "url": "gov.uk/employer-reporting-expenses-benefits/record-keeping",
        "stamp": _S},
    "ita_s4": {
        "url": "legislation.gov.uk/ukpga/2007/3/section/4",
        "stamp": _S},
}

# Table CH15400 — minima des records manuels, transportée VERBATIM,
# arbitrage inclus. Elle ne RACOURCIT rien sans spécification HMRC
# (caveat CH15100) : elle voyage comme data, le compute reste la
# période légale de chaque kind.
CH15400_MINIMUMS = [
    ("Sales or service dockets", "No minimum period. May be destroyed "
     "when no longer needed."),
    ("Copies of orders, delivery notes, dispatch notes, goods returned "
     "notes, invoices for expenses incurred by employees", "1 year"),
    ("Production records, stock records (except those for second hand "
     "schemes), job cards, appointment books, diaries, business letters",
     "1 year"),
    ("Import, export and delivery from warehouse documents", "3 years"),
    ("Daybooks, ledgers, cashbooks, second hand scheme stock books",
     "3 years"),
    ("Purchase invoices, copy sales invoices, credit notes, debit "
     "notes, authenticated receipts", "4 years"),
    ("Daily gross takings records, records related to retail scheme "
     "calculations, catering estimates", "4 years"),
    ("Electronic Cash Registers (ECR) and Electronic Point of Sale "
     "(EPOS) records", "4 years"),
    ("Bank statements and paying-in books, management accounts, "
     "annual accounts", "5 years"),
    ("Any record containing the VAT account", "6 years (No reduction)"),
]
CH15400_ARBITRAGE = ("If a record falls within more than one of the "
                     "categories above, apply the longer retention period.")
CH14100_ARBITRAGE = ("Any record that serves more than one purpose must "
                      "be kept for the longest period required by those "
                      "purposes.")
CH15100_CAVEAT = ("This specified period is not to exceed 6 years. ... "
                  "Although the maximum period is 6 years, we can specify "
                  "a shorter period.")

FUTURE_EVENT = ("This rule applies equally to documents that refer to "
                "events that are to take place in the future (possibly a "
                "future date of payment or future supply of goods). In "
                "such cases the 6-year period runs not from the date of "
                "the future event but from the date on which the "
                "document itself is issued.")

SCHEMES = ("none", "oss", "moss")


# ---------------- kinds (grammaire fermée) ----------------
def _rule(rule_id, source, verbatim, anchor_field, anchor_on,
          period, retain_until):
    return {
        "id": rule_id,
        "source": source,
        "verbatim": verbatim,
        "anchor_field": anchor_field,
        "anchor_on": anchor_on,
        "period": period,
        "retain_until": retain_until,
        "earliest_destroy_on": _iso(_date.fromisoformat(retain_until)
                                    + _td(days=1)),
        "status": "applied",
    }


def _blocked(rule_id, source, verbatim, reason):
    return {"id": rule_id, "source": source, "verbatim": verbatim,
            "status": "blocked", "reason": reason,
            "earliest_destroy_on": None}


REFUSALS = {
    "personal_22_months": ("22 months is HMRC's shorthand for non-business "
                           "personal records — the sentence lives in an "
                           "archived Tax Help PDF, no current GOV.UK page "
                           "restates it as the rule; refused until replayed "
                           "on a live official page."),
    "national_minimum_wage": ("NMW records: 6 years from the end of the pay "
                              "reference period — the working-time records "
                              "regulation was not replayed this cycle; "
                              "refused by name, candidate on file."),
    "employment_contract": ("contract/tort limitation (6 years from breach, "
                            "5 in Scotland) is the LEGAL GUARANTEE kit's "
                            "family, not a records-retention rule; refused "
                            "here and pointed there."),
    "gdpr": ("storage limitation is a duty to DELETE, the opposite clock; "
             "no retention date comes out of it; refused by name."),
    "france": ("French commercial-law retention (10 years from the "
               "clôture of accounts) was not replayed this cycle and is a "
               "different jurisdiction; refused by name, candidate on "
               "file — this tool plays UK only."),
    "scotland": ("retention periods here are UK-wide statutes, not "
                 "Scots-law prescription (which is the 5-year limitation "
                 "line of the legal-guarantee kit); not a separate "
                 "retention clock; refused by name."),
}

KINDS = ("vat_invoice", "vat_summary", "vat_series", "vat_bad_debt_claim",
         "company_tax_records", "companies_act_accounting",
         "self_assessment", "paye", "cis", "expenses_benefits")

_ANCHOR_FIELDS = {
    "vat_invoice": ("issued_on",),
    "vat_summary": ("prepared_on",),
    "vat_series": ("last_entry_on",),
    "vat_bad_debt_claim": ("claim_on",),
    "company_tax_records": ("financial_year_end_on", "made_on"),
    "companies_act_accounting": ("made_on",),
    "self_assessment": None,   # règle propre : tax_year_end_on OU deadline_on
    "paye": ("tax_year_end_on",),
    "cis": ("tax_year_end_on",),
    "expenses_benefits": ("tax_year_end_on",),
}


def _tax_year_end(d, field):
    """ITA 2007 s.4(3): une année fiscale finit le 5 avril. Point."""
    if d.month != 4 or d.day != 5:
        raise RetentionError(
            field,
            "a UK tax year ENDS on 5 April — got %s. ITA 2007 s.4(3): "
            "'A tax year begins on 6 April and ends on the following 5 "
            "April'. Pass the 5 April that closes the year the records "
            "relate to." % _iso(d),
            "the 5 April ending the tax year, e.g. 2026-04-05")
    return d


def _sa_deadline(tax_year_end_on=None, deadline_on=None):
    """Deadline de rendu en ligne : 31 janvier qui suit la fin d'année."""
    if deadline_on is not None:
        d = deadline_on
        if d.month != 1 or d.day != 31:
            raise RetentionError(
                "deadline_on",
                "the online Self Assessment deadline is 31 January — got "
                "%s (gov.uk: 'at least 5 years after the 31 January "
                "submission deadline')" % _iso(d),
                "31 January, e.g. 2024-01-31")
        return d
    if tax_year_end_on is None:
        raise RetentionError(
            "tax_year_end_on", "self_assessment counts from the 31 January "
            "submission deadline of a tax year — pass tax_year_end_on (the "
            "5 April closing it) or deadline_on (the 31 January itself)",
            "tax_year_end_on like 2023-04-05, or deadline_on like "
            "2024-01-31")
    t = _tax_year_end(tax_year_end_on, "tax_year_end_on")
    # année 2022-23 finit 2023-04-05 -> deadline 31 janvier 2024
    return _date(t.year + 1, 1, 31)


def keep_records(record_kind, issued_on=None, prepared_on=None,
                 last_entry_on=None, claim_on=None,
                 financial_year_end_on=None, made_on=None,
                 tax_year_end_on=None, deadline_on=None, filed_on=None,
                 entity=None, scheme=None, vatmoss_used=None,
                 return_late=None, compliance_check_open=None,
                 spans_periods=None, asset_beyond_six_years=None,
                 as_of=None):
    if not isinstance(record_kind, str):
        raise RetentionError("record_kind",
                             "not a record kind: %r" % (record_kind,),
                             "one of " + ", ".join(KINDS))
    k = record_kind.strip().lower()
    if k in REFUSALS:
        raise RetentionError("record_kind", "refused by name — %s"
                             % REFUSALS[k], "one of " + ", ".join(KINDS))
    if k not in KINDS:
        raise RetentionError("record_kind",
                             "unknown record_kind %r" % (record_kind,),
                             "one of " + ", ".join(KINDS))

    scheme = (scheme or "none").strip().lower()
    if scheme not in SCHEMES:
        raise RetentionError(
            "scheme", "unknown scheme %r" % (scheme,),
            "none | oss | moss — gov.uk: '10 years if you are using the "
            "VAT One Stop Shop (OSS) scheme or used the ... (MOSS) scheme'")

    dates = {}
    for field, val in (("issued_on", issued_on), ("prepared_on", prepared_on),
                       ("last_entry_on", last_entry_on), ("claim_on", claim_on),
                       ("financial_year_end_on", financial_year_end_on),
                       ("made_on", made_on), ("tax_year_end_on", tax_year_end_on),
                       ("deadline_on", deadline_on), ("filed_on", filed_on)):
        if val is not None:
            dates[field] = _d(val, field)

    rules = []
    notes = []
    anchor_field = _ANCHOR_FIELDS[k]
    if anchor_field is not None:
        f = anchor_field[0]
        if f not in dates:
            raise RetentionError(
                f, "record_kind %s counts from its %s — none was passed"
                   % (k, f), "ISO date, e.g. 2026-11-24")
        for extra in dates:
            if extra not in anchor_field:
                raise RetentionError(
                    extra, "%s is not an anchor for record_kind %s "
                           "(the rule counts from %s)" % (extra, k, f),
                            "only " + ", ".join(anchor_field))

    # ---------------- VAT : trois ancres, un seul « 6 years » --------
    if k in ("vat_invoice", "vat_summary", "vat_series"):
        f = {"vat_invoice": "issued_on", "vat_summary": "prepared_on",
             "vat_series": "last_entry_on"}[k]
        anchor = dates[f]
        years = 10 if scheme != "none" else 6
        verbatims = {
            "vat_invoice": "Records such as invoices should be retained for "
                           "6 years from the date of issue.",
            "vat_summary": "Records such as a balance sheet or trading "
                           "account should be retained for 6 years from the "
                           "date they are prepared.",
            "vat_series": "Records such as ledgers, daybooks or stock books "
                          "which are kept ... should normally be retained "
                          "for 6 years from the date of the last entry.",
        }[k]
        rules.append(_rule("vat_%s_6y" % k.split("_")[1], "ch15200",
                           verbatims, f, _iso(anchor),
                           "%d years" % years,
                           _iso(_anniv(anchor, years=years))))
        if scheme != "none":
            rules[-1]["source"] = "ch15200 + charge_reclaim"
            rules[-1]["scheme_verbatim"] = (
                "You must keep VAT records for at least 6 years (or 10 "
                "years if you are using the VAT One Stop Shop (OSS) "
                "scheme or used the VAT Mini One Stop Shop (MOSS) scheme).")
        if k == "vat_invoice":
            notes.append({"note": "future_event", "verbatim": FUTURE_EVENT,
                          "effect": "anchor stays %s — the future event "
                                    "does not restart or delay the clock"
                                    % f})
        notes.append({"note": "ch15400_minimums",
                      "verbatim": CH15400_MINIMUMS,
                      "arbitrage": CH15400_ARBITRAGE,
                      "caveat": CH15100_CAVEAT,
                      "effect": "the 4/5-year rows are MINIMA HMRC may "
                                "specify; the computed clock above stays "
                                "the legal one unless HMRC has specified "
                                "shorter for this person"})
        if k == "vat_series":
            notes.append({"note": "piecemeal",
                          "verbatim": "It is not a breach of the law if "
                                      "they destroy piecemeal the pages of "
                                      "a bound book, or parts of pages or "
                                      "cards, as soon as the information "
                                      "recorded on them has been kept for "
                                      "the statutory period.",
                          "effect": "per-entry destruction is legal once "
                                    "that entry is 6 years old; the date "
                                    "above is for the WHOLE series"})

    elif k == "vat_bad_debt_claim":
        anchor = dates["claim_on"]
        years = 10 if vatmoss_used else 4
        rules.append(_rule(
            "bad_debt_claim", "charge_reclaim",
            "You must keep this information for 4 years after the claim is "
            "made, or 10 years if you used the VAT MOSS.",
            "claim_on", _iso(anchor), "%d years" % years,
            _iso(_anniv(anchor, years=years))))
        if vatmoss_used is not None:
            rules[-1]["flag"] = "vatmoss_used=%s" % bool(vatmoss_used)
        notes.append({"note": "claim_window",
                      "verbatim": "You must claim a refund from HMRC within "
                                  "4 years and 6 months of the date the "
                                  "payment was due or the date of supply "
                                  "(whichever was later).",
                      "effect": "the WINDOW to claim is a different clock "
                                "from the duty to KEEP; only the keep "
                                "clock is computed above"})

    # ---------------- limited company : deux règles, pas une ----------
    elif k == "company_tax_records":
        anchor = dates["financial_year_end_on"]
        rules.append(_rule(
            "ct_records_6y", "running_ltd",
            "You must keep records for 6 years from the end of the last "
            "company financial year they relate to.",
            "financial_year_end_on", _iso(anchor), "6 years",
            _iso(_anniv(anchor, years=6))))
        blocked = []
        if return_late:
            blocked.append(_blocked(
                "ct_late_return", "running_ltd",
                "... or longer if: ... you sent your Company Tax Return "
                "late.",
                "the page states the EXTENSION but publishes no fixed "
                "date — the clock cannot be computed here and is not "
                "guessed"))
        if compliance_check_open:
            blocked.append(_blocked(
                "ct_compliance_check", "running_ltd",
                "... or longer if: ... HMRC has started a compliance "
                "check into your Company Tax Return.",
                "retention runs until the check becomes unconditional; "
                "that date is not on this page — carried blocked, never "
                "invented"))
        if spans_periods:
            blocked.append(_blocked(
                "ct_spans_periods", "running_ltd",
                "... or longer if: they show a transaction that covers "
                "more than one of the company's accounting periods.",
                "the anchor would move to the LAST period covered — "
                "which period end governs is an input the page does not "
                "compute for you"))
        if asset_beyond_six_years:
            blocked.append(_blocked(
                "ct_long_asset", "running_ltd",
                "... or longer if: the company has bought something that "
                "it expects to last more than 6 years, like equipment or "
                "machinery.",
                "the expected lifetime is the company's own figure — no "
                "official table to compute it; carried blocked"))
        rules.extend(blocked)
        # s.388 vit à CÔTÉ, ancre différente
        if entity is not None:
            e = entity.strip().lower()
            if e not in ("private", "public"):
                raise RetentionError(
                    "entity", "unknown entity %r" % (entity,),
                    "private | public — s.388(4) branches on the form; "
                    "LLPs apply s.388 'with modifications' (S.I. "
                    "2008/1911 reg. 6) — modifications not replayed, "
                    "refused as entity")
            if "made_on" in dates:
                m = dates["made_on"]
                yrs = 3 if e == "private" else 6
                rules.append(_rule(
                    "s388_%s" % e, "s388",
                    "Accounting records ... must be preserved by it — (a) "
                    "in the case of a private company, for three years "
                    "from the date on which they are made; (b) in the "
                    "case of a public company, for six years from the "
                    "date on which they are made.",
                    "made_on", _iso(m), "%d years" % yrs,
                    _iso(_anniv(m, years=yrs))))
                notes.append({"note": "longest_governs",
                              "verbatim": CH14100_ARBITRAGE,
                              "effect": "the two clocks above count from "
                                        "DIFFERENT dates; the later "
                                        "retain_until governs destruction"})
            else:
                notes.append({"note": "s388_uncomputed",
                              "verbatim": "in the case of a private "
                                          "company, for three years from "
                                          "the date on which they are "
                                          "made",
                              "effect": "companies-act retention counts "
                                        "from made_on — pass made_on to "
                                        "bring its row into the max"})
        else:
            notes.append({"note": "two_rules",
                          "verbatim": "Two separate retention rules "
                                      "apply to a company, and they are "
                                      "not the same rule: six years for "
                                      "tax from the financial year end; "
                                      "under Companies Act 2006 s.388, "
                                      "three years (private) or six "
                                      "(public) from the date the "
                                      "records are made.",
                          "effect": "carried as a NAMED conflict — this "
                                    "row is the GOV.UK guide plus the "
                                    "Act, no averaging"})

    elif k == "companies_act_accounting":
        m = dates["made_on"]
        if entity is None:
            raise RetentionError(
                "entity", "s.388(4) branches on the COMPANY FORM — an "
                          "untyped company has no computable period",
                "private (3 years) | public (6 years)")
        e = entity.strip().lower()
        if e not in ("private", "public"):
            raise RetentionError(
                "entity",
                "unknown entity %r — s.388(4) knows only private and "
                "public; LLPs apply s.388 'with modifications' (S.I. "
                "2008/1911 reg. 6), not replayed, refused as entity" %
                (entity,),
                "private (3 years) | public (6 years)")
        yrs = 3 if e == "private" else 6
        rules.append(_rule(
            "s388_%s" % e, "s388",
            "in the case of a %s company, for %s from the date on which "
            "they are made" % (e, "three years" if e == "private"
                               else "six years"),
            "made_on", _iso(m), "%d years" % yrs,
            _iso(_anniv(m, years=yrs))))

    # ---------------- self assessment : la deadline DÉRIVÉE ------------
    elif k == "self_assessment":
        for f in ("issued_on", "prepared_on", "last_entry_on", "claim_on",
                  "financial_year_end_on", "made_on", "tax_year_end_on",
                  "deadline_on"):
            if f in dates and f not in ("tax_year_end_on", "deadline_on",
                                        "filed_on"):
                raise RetentionError(
                    f, "%s is not an anchor for self_assessment — the "
                       "clock counts from the 31 January SUBMISSION "
                       "DEADLINE of the relevant tax year" % f,
                    "tax_year_end_on (5 April) or deadline_on (31 January)"
                    ", optionally filed_on")
        if tax_year_end_on is not None and deadline_on is not None:
            d_check = _d(deadline_on, "deadline_on")
            t = _tax_year_end(_d(tax_year_end_on, "tax_year_end_on"),
                              "tax_year_end_on")
            if d_check != _date(t.year + 1, 1, 31):
                raise RetentionError(
                    "deadline_on",
                    "deadline_on %s is not the online deadline of the tax "
                    "year ending %s (expected %s) — pass one anchor, or "
                    "consistent ones" % (_iso(d_check), _iso(t),
                                         _iso(_date(t.year + 1, 1, 31))),
                    "31 January following the 5 April that ends the year")
        deadline = _sa_deadline(
            tax_year_end_on=dates.get("tax_year_end_on"),
            deadline_on=dates.get("deadline_on"))
        retain_5y = _anniv(deadline, years=5)
        rules.append(_rule(
            "sa_5y_after_deadline", "sa_how_long",
            "You must keep your records for at least 5 years after the 31 "
            "January submission deadline of the relevant tax year.",
            "deadline_on", _iso(deadline), "5 years", _iso(retain_5y)))
        rules[-1]["official_example"] = (
            "If you sent your 2022 to 2023 tax return online by 31 "
            "January 2024, you must keep your records until at least the "
            "end of January 2029.")
        if "filed_on" in dates:
            filed = dates["filed_on"]
            threshold = _anniv(deadline, years=4)
            if filed > threshold:
                retain_15m = _anniv(filed, months=15)
                rules.append(_rule(
                    "sa_very_late_15m", "sa_how_long",
                    "If you send your tax return more than 4 years after "
                    "the deadline, you'll need to keep your records for "
                    "15 months after you send your tax return.",
                    "filed_on", _iso(filed), "15 months",
                    _iso(retain_15m)))
                notes.append({"note": "longest_governs",
                              "verbatim": CH14100_ARBITRAGE,
                              "effect": "both clocks above apply to the "
                                        "same file; the later "
                                        "retain_until governs"})
            else:
                notes.append({"note": "late_not_very_late",
                              "verbatim": "more than 4 years after the "
                                          "deadline",
                              "effect": "filed_on %s is late but not "
                                        "past the 4-year threshold (%s) — "
                                        "the 15-month rule does NOT open, "
                                        "the 5-year deadline rule stands "
                                        "alone" % (_iso(filed),
                                                   _iso(threshold))})

    # ---------------- PAYE / CIS / expenses : 3 ans, fin d'année -------
    elif k in ("paye", "cis", "expenses_benefits"):
        t = _tax_year_end(dates["tax_year_end_on"], "tax_year_end_on")
        if k in ("paye", "expenses_benefits"):
            src = "paye" if k == "paye" else "expenses"
            verb = ("Your records must show you've reported accurately, "
                    "and you need to keep them for 3 years from the end "
                    "of the tax year they relate to."
                    if k == "paye" else
                    "You must keep records for 3 years from the end of "
                    "the tax year they relate to.")
        else:
            src, verb = "ch14700", (
                "If the person is an employer or makes payments within "
                "the Construction Industry Scheme, they must retain "
                "their PAYE and/or Construction Industry Scheme records "
                "for 3 years after the end of the tax year to which "
                "they relate.")
        rules.append(_rule("%s_3y" % k, src, verb, "tax_year_end_on",
                           _iso(t), "3 years", _iso(_anniv(t, years=3))))
        if k == "cis":
            notes.append({"note": "ita_definition",
                          "verbatim": "A tax year begins on 6 April and "
                                      "ends on the following 5 April.",
                          "effect": "the 5-April validation of "
                                    "tax_year_end_on is statutory, not "
                                    "house style (ITA 2007 s.4(3))"})
        else:
            notes.append({"note": "ita_definition",
                          "verbatim": "A tax year begins on 6 April and "
                                      "ends on the following 5 April.",
                          "effect": "tax_year_end_on must be the 5 April "
                                    "closing the year (ITA 2007 s.4(3))"})

    # ---------------- agrégat ------------------------------------------
    applied = [r for r in rules if r["status"] == "applied"]
    blocked = [r for r in rules if r["status"] == "blocked"]
    governing = None
    if applied:
        governing = max(applied, key=lambda r: r["retain_until"])
    if blocked:
        safe = None
        status = ("BLOCKED_EXTENSION" if governing else "BLOCKED")
    else:
        safe = governing["earliest_destroy_on"] if governing else None
        status = "COMPUTED" if governing else "NO_RULE"

    out = {
        "record_kind": k,
        "jurisdiction": "UK",
        "status": status,
        "rules": rules,
        "governing_rule": governing["id"] if governing and not blocked else None,
        "retain_until": governing["retain_until"] if governing and not blocked else None,
        "safe_destroy_on": safe,
        "lower_bound_retain_until": (governing["retain_until"]
                                     if governing and blocked else None),
        "blocked_by": [b["id"] for b in blocked],
        "notes": notes,
        "conventions": {
            "from": "the named official ANCHOR of each rule (issue / "
                    "prepared / last entry / financial year end / made / "
                    "31 January deadline / filed), never a wall clock",
            "until": "official wording 'until at least' = the anniversary "
                     "day itself is the LAST day of retention",
            "anniversary": "anchor + N years/months, clamped to the last "
                           "day of the target month when the day-of-month "
                           "does not exist (2024-02-29 + 3 years -> "
                           "2027-02-28)",
            "destroy": "earliest_destroy_on = retain_until + 1 day",
            "longest": CH14100_ARBITRAGE,
        },
        "sources": SOURCES,
        "table_version": RETENTION_TABLE_VERSION,
    }
    if as_of is not None:
        a = _d(as_of, "as_of")
        out["as_of"] = _iso(a)
        if governing:
            days = (_date.fromisoformat(governing["retain_until"]) - a).days
            out["days_left_in_retention"] = days
            out["expired"] = days < 0
    return out
