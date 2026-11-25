"""Bundle 112 — /invoice/payment-due : les QUATRE lectures d'un
« Net 30 », et QUI reporte QUOI. NOYAU QUI COMPTE (lentille HUMAIN) :
arithmétique de dates + tables de jours FERMÉES + règle de report
NOMMÉE par juridiction + couche de règlement TARGET2. Zéro réseau,
zéro horloge murale, zéro LM — la douleur publiée est que les gens
« calculent » une échéance en DEVINANT la convention de l'autre côté.

GATE PAYÉ À LA SOURCE (25-11 ~15h-15h35, voir docs/DEMAND-QUEUE.md) —
ce qui est publié est juré ici mot à mot ; ce qui ne l'est pas est
REFUSÉ NOMMÉ, jamais extrapolé :

  * § 193 BGB, lu verbatim (gesetze-im-internet.de/bgb/__193.html) :
    « …fällt der bestimmte Tag oder der letzte Tag der Frist auf einen
    Sonntag, einen am Erklärungs- oder Leistungsort staatlich
    anerkannten allgemeinen Feiertag oder einen Sonnabend, so tritt
    an die Stelle eines solchen Tages der nächste Werktag. »
    → ALLEMAGNE reporte le samedi par LOI, et le jour de report est
    Werktag au sens de §193 : ni samedi, ni dimanche, ni férié. Le
    Landage est déclaré : la table vit dans holidays.py, common core
    des Länder — même doctrine que le verdict de holidays.py : on ne
    devine pas le calendrier du Land, le décalage est NOMMÉ.
  * Code civil FR, sous-section 2 des obligations de sommes d'argent,
    LUE article par article (legifrance LEGISCTA000032035257) :
    1342 « Il doit être fait sitôt que la dette devient exigible »,
    1343 libération au nominal, 1343-4 lieu du paiement, 1343-5
    délai du juge — AUCUN texte ne reporte le TERME d'une facture
    tombé un samedi ou un dimanche. ET la recherche inverse est
    payée aussi : les anciens articles 1235-1244-1 (section « Du
    paiement ») sont ABROGÉS par l'ordonnance n° 2016-131 du 10
    février 2016 art. 2 (traces lues sur legifrance, versions
    abrogées), et la loi du 7 juillet 1925 qui reportait l'échéance
    des EFFETS DE COMMERCE au premier jour ouvrable est ABROGÉE à
    compter du 22 décembre 2007 (LOI 2007-1787 art. 27, lue). La
    France est le pays de la TABLE VIDE : pas de règle statutaire
    de roll en vigueur lue = pas de règle jurée ; le report FR est
    CONTRACTUEL (l'argument `clause` la calcule, nommée). Leçon
    soldes-lu/b110 rejouée contre la file elle-même : l'item de la
    file citait « L. 133-1 CMF ne reporte que… » — L. 133-1 est un
    texte de SERVICE DE PAIEMENT, pas de terme : lu, remis à sa
    place dans la couche SETTLEMENT, jamais dans la couche TERM.
  * Code monétaire et financier L. 133-1, lu (legifrance) : « Un
    jour ouvrable est un jour au cours duquel le prestataire de
    services de paiement du payeur ou celui du bénéficiaire exerce
    une activité permettant d'exécuter des opérations de paiement »
    → définition OPÉRATEUR du jour ouvrable ; il gouverne l'ordre,
    pas l'échéance.
  * L. 3133-1 code du travail (via la table holidays.py, relue) :
    jour OUVRABLE = tout jour sauf dimanche + férié légal — le
    SAMEDI compte. Face à l'usage « working days » des blogs et du
    client de r/Contractor : HUIT jours d'écart sur un Net 30
    d'oracle (V3b g112), dans le même pays, sur le même mot.
  * Banking and Financial Dealings Act 1971 s.1(4), lu verbatim
    (legislation.gov.uk/ukpga/1971/80) : « …deemed to be complied
    with if he makes or does it on the next following day on which
    he is compellable » sur BANK HOLIDAY — pas sur le samedi : la
    table UK n'est ni l'allemande ni la française. Dates lues LIVE
    sur gov.uk/bank-holidays.json (division england-and-wales,
    fetch 25-11-2026) : 2026, 2027, 2028 publiés — substitutions
    comprises (2027 : Christmas décalé 27, Boxing 28 — deux jours
    ouvrables POUR cause de week-end). Hors de ces trois années :
    NO_TABLE, refus nommé (« le calendrier des bank holidays se
    PROCLAME, il ne se prédit pas » — doctrine b110
    pas-d'acte-pas-de-date).
  * TARGET/T2, page BCE lue (ecb.europa.eu — working-hours) :
    ouvert lundi–vendredi, fermé samedis, dimanches et SIX jours
    par an — 1 janvier, Good Friday, Easter Monday, 1 mai,
    25 décembre, 26 décembre. Les mobiles viennent du computus
    publié (Meeus, holidays.py), cross-check live sur la page :
    2026 GF=3-avr EM=6-avr, 2027 GF=26-mar EM=29-mar, 2028
    GF=14-avr EM=17-avr — ZÉRO dérive. Une fermeture tombant un
    week-end est ABSORBÉE (2027-05-01 = samedi + closing : zéro
    jour de plus — l'absorption est NOMMÉE, pas devinée). Le
    règlement peut glisser ; la dette court quand même : directive
    2011/7/UE art. 3(1) et 3(3)(a), lus (eur-lex) : intérêt de
    retard SANS mise en demeure « from the day following the date
    or the end of the period for payment » — la raison pour
    laquelle échéance et règlement ne sont pas la même colonne.
  * Plafond FR L. 441-10, lu (economie.gouv.fr + entreprendre.
    service-public.gouv.fr) : 60 jours nets à compter de l'émission,
    ou 45 jours fin de mois EN DÉROGATION expresse du contrat. La
    DGCCRF publie que « 45 jours fin de mois » a DEUX méthodes
    officielles — 45-jours-PUIS-fin-de-mois et fin-de-mois-PUIS-45-
    jours — et l'exemple d'État (facture du 10 mars) sort 30 avril
    contre 15 mai : QUINZE jours d'écart admissibles par
    l'administration elle-même. Le module rend les DEUX, jamais la
    moyenne.
  * Conventions des places de marché, lues (invoice-generator,
    upflow, bluevine, resolvepay) : le jour d'émission est JOUR 0
    (« March 1 with Net 30 is due March 31 » ×4 exemples épinglés),
    « by convention Net 30 counts from the INVOICE date, not the
    receipt date » — la lecture réception existe (r/Contractor : le
    client qui compte ouvrés ; directive art. 3(3)(b)(i) : 30 jours
    dès RÉCEPTION quand le terme n'est pas fixé) mais elle est
    nommée comme LECTURE, jamais fondue.

Douleurs portées par ces lectures (liens dans la file) : r/
Contractor 1i24hj1 (Net30 calendaire vs ouvrés EN LITIGE — « they
claim the 30 days exclude weekends and holidays »), r/Accounting
xx5kik (60 days vs 60 business days), Bluevine vs ResolvePay qui se
CONTREDISENT sur le week-end — deux blogs, deux « vrais », parce
que la règle est JURIDICTIONNELLE et qu'eux vendent une moyenne.

Classes fermées rendues : readings (≤5 nommées), roll (règle ou
AUCUNE — le vide FR est un verdict LU, pas un trou), settlement
TARGET2 (open / shifts / absorbed / rail-not-read pour GB : la
livre ne se règle pas sur T2 et le texte CHAPS n'a pas été lu —
jamais de colonne sans texte), ceiling L. 441-10, eom DEUX méthodes,
clause contractuelle nommée. Les refus nomment field + expected.
"""
import re
from datetime import date, timedelta

import holidays as _hol


class DueError(Exception):
    def __init__(self, field, message, expected):
        Exception.__init__(self, message)
        self.field = field
        self.message = message
        self.expected = expected


# ------------------------------------------------------------------
# tables FERMÉES, chaque ligne avec son acte lu (docstring source)
# ------------------------------------------------------------------

# gov.uk /bank-holidays.json, division england-and-wales, relue LIVE
# 25-11-2026. Substitutions comprises — ce sont les dates PROCLAMÉES
# (pouvoirs s.1(2) BFDA 1971), pas la règle calculée. Hors 2026-2028
# : NO_TABLE, refus nommé.
GB_BANK_HOLIDAYS = {
    2026: ["2026-01-01", "2026-04-03", "2026-04-06", "2026-05-04",
           "2026-05-25", "2026-08-31", "2026-12-25", "2026-12-28"],
    2027: ["2027-01-01", "2027-03-26", "2027-03-29", "2027-05-03",
           "2027-05-31", "2027-08-30", "2027-12-27", "2027-12-28"],
    2028: ["2028-01-03", "2028-04-14", "2028-04-17", "2028-05-01",
           "2028-05-29", "2028-08-28", "2028-12-25", "2028-12-26"],
}

JURISDICTIONS = ("de", "fr", "gb")

CLAUSES = ("next_workday", "next_ouvrable", "previous_workday")

# L. 441-10 (lu, economie.gouv.fr) : 60 jours nets OU 45 jours fin de
# mois en dérogation expresse.
FR_NET_CAP_DAYS = 60


def _t2_closings(year):
    """Six TARGET fermetures/an, page BCE lue ; mobiles = computus
    publié (Meeus via holidays.py), cross-check 2026-2028 sur la page
    sans dérive."""
    e = _hol.easter(year)
    return {
        date(year, 1, 1).isoformat(): "New Year's Day",
        (e - timedelta(days=2)).isoformat(): "Good Friday",
        (e + timedelta(days=1)).isoformat(): "Easter Monday",
        date(year, 5, 1).isoformat(): "1 May (Labour Day)",
        date(year, 12, 25).isoformat(): "Christmas Day",
        date(year, 12, 26).isoformat(): "Christmas Holiday",
    }


def _gb_hset(year):
    if year not in GB_BANK_HOLIDAYS:
        raise DueError(
            "invoice_date",
            "GB bank-holiday dates are PROCLAIMED each year (BFDA "
            "1971 s.1(2)) — gov.uk publishes 2026-2028; no table for "
            "%d, no promise" % year,
            "year 2026-2028 for jurisdiction gb")
    return set(GB_BANK_HOLIDAYS[year])


def _gb_dates(year):
    """Union des DEUX couches lues : (1) les jours FIXES de Schedule 1
    de la BFDA 1971 — « Christmas Day, if it be not a Sunday or, if
    it be a Sunday, 26th December » et « 26th December, if it be not a
    Sunday » (verbatim, legislation.gov.uk) — donc un 25 ou 26 qui
    tombe SAMEDI est bank holiday ce jour-là, même si gov.uk ne liste
    que le substitut ouvrable ; (2) la table PROCLAMÉE gov.uk
    (substitutions et jours extra — les samedis de Noël des années
    pair n'y figurent pas, l'acte oui). La levée hors 2026-2028 est le
    refus NO_TABLE : la couche (2) ne se prédit pas."""
    hs = _gb_hset(year)
    d25 = date(year, 12, 25)
    d26 = date(year, 12, 26)
    hs = set(hs)
    hs.add((d25 if d25.weekday() != 6 else d26).isoformat())
    hs.add((d26 if d26.weekday() != 6
            else date(year, 12, 27)).isoformat())
    return hs


def _hset(jur, year):
    """Dates de jours fériés : FR/DE = loi (table holidays.py),
    GB = acte proclamé publié (None jamais — la levée fait le refus)."""
    if jur == "gb":
        return _gb_dates(year)
    return {e["date"] for e in _hol.holidays(jur.upper(), year)["holidays"]}


# ------------------------------------------------------------------
# grammaire des termes — FERMÉE ; chaque forme a sa source lue
# ------------------------------------------------------------------

_T_NET = re.compile(r"^(?:net\s*(\d{1,3})|(\d{1,3})\s*(?:days?|jours?)"
                    r"(?:\s+nets?)?|netto\s*(\d{1,3}))$")
_T_EOM = re.compile(r"^(?:(\d{1,3})\s*(?:jours?|days?)\s*fin\s*(?:de\s*)?"
                    r"mois|net\s*(\d{1,3})\s*(?:eom|fim de mes)|"
                    r"(\d{1,3})\s*(?:j|days?|jours?)\s*fm)$")
_T_WORKED = re.compile(r"^(?:(\d{1,3})\s*(?:business|working)\s*days?"
                       r"|(\d{1,3})\s*(?:jours?\s+)?ouvres|(\d{1,3})\s*"
                       r"(?:werk)?tage)$")
_T_OUVRABLES = re.compile(r"^(\d{1,3})\s*(?:jours?\s+)?ouvrables?$")
_T_RECEIPT = re.compile(r"^(?:due on receipt|a reception|à reception|"
                        r"faell ig)$")
_T_DISCOUNT = re.compile(r"^(\d{1,2})\s*/\s*(\d{1,3})\s*net\s*(\d{1,3})$")


def _pick(m):
    for g in m.groups():
        if g:
            return int(g)
    raise DueError("terms", "terms grammar matched but carried no day "
                   "count — impossible by construction, reported",
                   "net 30 | 30 jours fin de mois | 30 business days | "
                   "2/10 net 30")


def _parse_terms(terms):
    t = re.sub(r"\s+", " ", (terms or "").strip().lower())
    t = t.replace("ouvrés", "ouvres").replace("ouvrées", "ouvres")
    m = _T_NET.match(t)
    if m:
        return {"kind": "net", "days": _pick(m)}
    m = _T_EOM.match(t)
    if m:
        return {"kind": "eom", "days": _pick(m)}
    m = _T_WORKED.match(t)
    if m:
        return {"kind": "worked", "days": _pick(m)}
    m = _T_OUVRABLES.match(t)
    if m:
        return {"kind": "ouvrables", "days": _pick(m)}
    if _T_RECEIPT.match(t):
        return {"kind": "due_on_receipt", "days": 0}
    m = _T_DISCOUNT.match(t)
    if m:
        return {"kind": "discount", "pct": int(m.group(1)),
                "discount_days": int(m.group(2)),
                "days": int(m.group(3))}
    raise DueError(
        "terms",
        "unparsed terms — the grammar is CLOSED and every accepted "
        "form is a read text",
        "net 30 | 30 days | 30 jours fin de mois | net 30 eom | "
        "30 business days | 30 jours ouvrés | 30 jours ouvrables | "
        "due on receipt | 2/10 net 30")


# ------------------------------------------------------------------
# primitives — convention JOUR 0, épinglée sur les exemples publiés
# (invoice-generator : March 1 -> March 31, ×4 dans l'oracle g112)
# ------------------------------------------------------------------

def _eom(d):
    nxt = date(d.year + (d.month == 12), (d.month % 12) + 1, 1)
    return nxt - timedelta(days=1)


def _count_worked(start, n, jur, include_sat):
    """n jours comptés APRÈS start (start = jour 0). include_sat rend
    la LECTURE OUVRABLE (L. 3133-1, lu : tout jour sauf dimanche +
    férié — le SAMEDI compte) contre la lecture OUVRÉ/business day
    (lundi–vendredi). C'est la divergence française interne du mot —
    8 jours sur un Net 30 d'oracle, même pays, même statute."""
    if n == 0:
        return start
    d, c, yr_cache = start, 0, {}
    while c < n:
        d += timedelta(days=1)
        if d.year not in yr_cache:
            yr_cache[d.year] = _hset(jur, d.year) if jur else set()
        hs = yr_cache[d.year]
        weekday = d.weekday()
        if (weekday < 5 or (include_sat and weekday == 5)) \
                and d.isoformat() not in hs:
            c += 1
    return d


# ------------------------------------------------------------------
# RÈGLES DE ROLL — table close, chaque ligne avec son acte (ou son
# ABSENCE nommée : le vide FR est un VERDICT LU — abrogations 2016
# et 2007 vérifiées, voir docstring)
# ------------------------------------------------------------------

def _rolls(d, jur, document="invoice"):
    """Le texte de roll lui-même : DE §193 (dimanche, férié OU
    SAMBEDI — le samedi est reporté par la LOI) ; GB s.1(4) (bank
    holiday seulement) ; FR facture : ne reporte RIEN (table vide
    lue) ; FR LETTRE DE CHANGE : article L. 511-79 code de commerce,
    LU verbatim — « Le paiement d'une lettre de change dont
    l'échéance est à un jour férié légal ne peut être exigé que le
    premier jour ouvrable qui suit » : le report existe, mais il est
    par INSTRUMENT, pas par pays. La divergence est donc double :
    juridique ET notariée. Le « jour ouvrable » est celui de la
    table L. 3133-1 — le SAMEDI compte, le dimanche et les jours
    « où aucun paiement ne peut être exigé » (assimilés, lus) non."""
    if jur == "de":
        return (d.weekday() in (5, 6)
                or d.isoformat() in _hset("de", d.year))
    if jur == "gb":
        return d.isoformat() in _gb_dates(d.year)
    if jur == "fr" and document == "lettre_de_change":
        # L. 511-79 (lu) : férié légal OU dimanche (jour ouvrable
        # exigé pour tous les actes) -> premier jour ouvrable (le
        # SAMEDI compte, L. 3133-1). Les jours « assimilés » (aucun
        # paiement exigeable) vivent dans des lois de 1904-1909
        # NON ENUMEREES ici : gap nommé, jamais deviné.
        return (d.weekday() == 6
                or d.isoformat() in _hset("fr", d.year))
    return False


ROLL_LAW = {
    "de": "§ 193 BGB (lu verbatim) — Sonntag, anerkannter Feiertag "
          "ODER Sonnabend -> naechster Werktag ; le report est la LOI",
    "fr": "aucun texte en vigueur ne reporte le terme d'une FACTURE "
          "— 1342-1343-5 LUS, anciens 1235-1244-1 ABROGÉS (ord. "
          "2016-131), loi 1925 effets de commerce ABROGÉE (2007) ; "
          "le report FR est CONTRACTUEL",
    "fr_lc": "com_l511_79 (lu verbatim) — lettre de change à échéance "
             "fériée : « ne peut être exigé que le premier jour "
             "ouvrable qui suit » ; le report existe mais par "
             "INSTRUMENT, pas par pays",
    "gb": "BFDA 1971 s.1(4) (lu verbatim) — bank holiday -> next "
          "compellable day ; le SAMEDI n'est pas bank holiday : pas "
          "de report statutaire",
}


def _worked_day(d, jur):
    """lundi–vendredi hors fériés de la table"""
    return d.weekday() < 5 and d.isoformat() not in _hset(jur, d.year)


def _ouvrable_day(d, jur):
    """L. 3133-1 (lu) : tout jour SAUF dimanche + férié — le SAMEDI
    compte. Le mot du code du travail, pas l'usage bancaire."""
    return d.weekday() < 6 and d.isoformat() not in _hset(jur, d.year)


ROLL_RULE = {"de": "bgb_193", "fr": "no_statutory_roll",
             "fr_lc": "com_l511_79", "gb": "bfe_1971_s1_4"}


def _legal_due(raw, jur, clause=None, document="invoice"):
    """(date, shift_days) — roll de la règle si elle existe, clause
    contractuelle NOMMÉE si fournie. FR facture sans clause : la date
    RESTE (verdict lu, pas un repli silencieux). FR LETTRE DE CHANGE :
    roll L. 511-79, atterrissage JOUR OUVRABLE (le samedi compte,
    L. 3133-1) — pas_workday : la loi ne dit pas « working day »,
    elle dit « ouvrable ». shift_days en JOURS CALENDARAIRES bruts :
    samedi->lundi = 2, pas 1 — c'est l'écart que le client paie."""
    due, rolls = raw, 0
    lc = (jur == "fr" and document == "lettre_de_change")
    lands = (lambda d: _ouvrable_day(d, "fr")) if lc else \
            (lambda d: _worked_day(d, jur)) if jur != "fr" else \
            (lambda d: True)
    while _rolls(due, jur, document):
        due += timedelta(days=1)
        while not lands(due):
            due += timedelta(days=1)
        rolls += 1
    if clause == "previous_workday":
        back = raw - timedelta(days=1)
        while not _worked_day(back, jur):
            back -= timedelta(days=1)
        return back, abs((back - raw).days)
    if clause == "next_ouvrable":
        while not _ouvrable_day(due, jur):
            due += timedelta(days=1)
    elif clause == "next_workday":
        while not _worked_day(due, jur):
            due += timedelta(days=1)
    return due, abs((due - raw).days)


# ------------------------------------------------------------------
# couche SETTLEMENT — TARGET2 : l'argent bouge, la dette court.
# COLONNE EUR SEULEMENT : le rail GBP (CHAPS) n'a pas été lu — la
# ligne GB est refusée NOMMÉE, jamais approximée (leçon b111 : on ne
# jure pas ce qu'on n'a pas lu).
# ------------------------------------------------------------------

def _settlement(due):
    clos = _t2_closings(due.year)
    iso = due.isoformat()
    closing = clos.get(iso)
    weekend = due.weekday() >= 5
    d, steps = due, 0
    while d.weekday() >= 5 or d.isoformat() in _t2_closings(d.year):
        d += timedelta(days=1)
        steps += 1
    return {
        "layer": "TARGET2 — euro settlement only (page BCE lue)",
        "target2_open": steps == 0,
        "settle_on": d.isoformat(),
        "shift_days": steps,
        "due_day_target_closing": closing,
        "closing_absorbed_by_weekend": bool(closing) and weekend,
        "interest_runs_from": iso,
        "interest_law": "directive 2011/7/EU art. 3(1)+3(3)(a) (lus)"
                        " — interet de retard SANS mise en demeure"
                        " des le lendemain du terme ; le rail ferme,"
                        " la dette court",
    }


# ------------------------------------------------------------------
# entrée principale
# ------------------------------------------------------------------

WD = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
      "Saturday", "Sunday"]


def payment_due(invoice_date, terms, jurisdiction=None,
                receipt_date=None, count_from=None, clause=None,
                document=None):
    # --- dates : parsées ou refusées, jamais devinées ---
    try:
        iss = date.fromisoformat(str(invoice_date))
    except Exception:
        raise DueError("invoice_date", "invoice_date must be a real "
                       "YYYY-MM-DD calendar date", "YYYY-MM-DD")
    if not 1900 <= iss.year <= 2099:
        raise DueError("invoice_date", "date outside the anchored "
                       "computus range of the holiday tables",
                       "1900-2099")
    rcv = None
    if receipt_date is not None:
        try:
            rcv = date.fromisoformat(str(receipt_date))
        except Exception:
            raise DueError("receipt_date", "receipt_date must be a "
                           "real YYYY-MM-DD calendar date", "YYYY-MM-DD")
        if rcv < iss:
            raise DueError("receipt_date", "receipt_date precedes "
                           "invoice_date — the clock cannot start "
                           "before the ink",
                           "receipt_date >= invoice_date")
    if jurisdiction is not None:
        j = str(jurisdiction).lower()
        if j not in JURISDICTIONS:
            raise DueError("jurisdiction",
                           "jurisdiction outside the READ set — every "
                           "rule in the table cites its text; none "
                           "was read for other states",
                           "de | fr | gb")
        jurisdiction = j
    cf = (count_from or "issue").lower()
    if cf not in ("issue", "receipt"):
        raise DueError("count_from", "count_from outside the closed "
                       "pair", "issue | receipt")
    if cf == "receipt" and rcv is None:
        raise DueError("receipt_date", "count_from=receipt needs the "
                       "receipt date — the reading is named, the date "
                       "must be too", "receipt_date YYYY-MM-DD")
    if clause is not None:
        c = str(clause).lower()
        if c not in CLAUSES:
            raise DueError("clause", "clause outside the closed set",
                           "next_workday | next_ouvrable | "
                           "previous_workday")
        clause = c
    doc = (str(document) if document is not None
           else "invoice").lower().replace(" ", "_")
    if doc not in ("invoice", "lettre_de_change"):
        raise DueError("document", "instrument outside the READ pair — "
                       "the FR roll exists for the lettre de change "
                       "(L. 511-79, lu), not for the invoice ; other "
                       "instruments have no read text here",
                       "invoice | lettre_de_change")

    p = _parse_terms(terms)
    anchor = iss if cf == "issue" else rcv
    readings = []
    eom_methods = None
    discount = None

    def reading(name, d, note):
        return {"reading": name, "due": d.isoformat(),
                "weekday": WD[d.weekday()],
                "days_from_issue": (d - iss).days, "note": note}

    if p["kind"] == "net":
        primary = _add_days_checked(anchor, p["days"])
        readings.append(reading("calendar_issue", _add_days_checked(
            iss, p["days"]),
            "day 0 = invoice date — the published convention "
            "(March 1 -> March 31)"))
        if rcv is not None:
            readings.append(reading("calendar_receipt",
                                    _add_days_checked(rcv, p["days"]),
                                    "clock from RECEIPT — the "
                                    "r/Contractor reading; the "
                                    "directive itself starts at "
                                    "receipt when the term is not "
                                    "fixed (art. 3(3)(b)(i), read)"))
        if jurisdiction:
            readings.append(reading("worked_from_issue",
                                    _count_worked(iss, p["days"],
                                                  jurisdiction, False),
                                    "N counted as WORKED days "
                                    "(Mon-Fri minus %s holidays) — "
                                    "the count the client on Reddit "
                                    "swears by" % jurisdiction))
            if jurisdiction == "fr":
                readings.append(reading("ouvrables_from_issue",
                                        _count_worked(iss, p["days"],
                                                      "fr", True),
                                        "L. 3133-1 (lu) : jour "
                                        "ouvrable = tout jour sauf "
                                        "dimanche + ferie — le "
                                        "SAMEDI COMPTE ; meme mot, "
                                        "autre loi, autre date"))
    elif p["kind"] == "eom":
        m1 = _eom(_add_days_checked(anchor, p["days"]))
        m2 = _add_days_checked(_eom(anchor), p["days"])
        primary = m1
        eom_methods = {
            "days_then_end_of_month": m1.isoformat(),
            "end_of_month_then_days": m2.isoformat(),
            "gap_days": abs((m2 - m1).days),
            "law": "DGCCRF (lue) : DEUX methodes officielles, jamais "
                   "une moyenne — exemple d'Etat, facture du 10 "
                   "mars : 30 avril contre 15 mai",
        }
        readings.append(reading("days_then_end_of_month", m1,
                                "N days, then the end of that month"))
        readings.append(reading("end_of_month_then_days", m2,
                                "end of the CURRENT month, then N "
                                "days"))
    elif p["kind"] == "worked":
        if not jurisdiction:
            raise DueError("jurisdiction", "worked-day counting needs "
                           "a jurisdiction — the holiday tables are "
                           "law, not vibes", "de | fr | gb")
        primary = _count_worked(anchor, p["days"], jurisdiction, False)
        readings.append(reading("worked_from_" + cf, primary,
                                "Mon-Fri minus %s holidays"
                                % jurisdiction))
        readings.append(reading("plain_mon_fri", _count_worked(
            anchor, p["days"], None, False),
            "the NO-HOLIDAY count every public calculator ships — "
            "the delta IS the bank-holiday window"))
    elif p["kind"] == "ouvrables":
        if not jurisdiction:
            raise DueError("jurisdiction", "ouvrable counting needs "
                           "the jurisdiction whose statute defines "
                           "the word", "de | fr | gb")
        primary = _count_worked(anchor, p["days"], jurisdiction, True)
        readings.append(reading("ouvrables_from_" + cf, primary,
                                "L. 3133-1 (lu) : samedi COMPTE, "
                                "dimanche + feries non — the same "
                                "term counts differently from "
                                "'business days'"))
    elif p["kind"] == "due_on_receipt":
        if rcv is None:
            raise DueError("receipt_date", "'due on receipt' without "
                           "a receipt date is a slogan, not a term",
                           "receipt_date YYYY-MM-DD")
        primary = rcv
        readings.append(reading("due_on_receipt", rcv,
                                "due the day it arrives"))
    else:  # discount (2/10 net 30)
        primary = _add_days_checked(anchor, p["days"])
        dd = _add_days_checked(anchor, p["discount_days"])
        discount = {"pct": p["pct"],
                    "window": dd.isoformat(),
                    "window_weekday": WD[dd.weekday()]}
        readings.append(reading("discount_window", dd,
                                "%d%% early window = day %d"
                                % (p["pct"], p["discount_days"])))
        readings.append(reading("calendar_issue", _add_days_checked(
            iss, p["days"]), "net reading of the same clause"))

    if primary is None:
        raise DueError("terms", "no primary due date from the parsed "
                       "terms", "net 30 | 30 jours fin de mois | "
                       "30 business days | 2/10 net 30")

    # --- roll par juridiction LUE : la divergence EST la réponse ---
    per = {}
    for j in JURISDICTIONS:
        try:
            ld, shifts = _legal_due(primary, j,
                                    clause if jurisdiction == j
                                    else None, doc)
            key = "fr_lc" if (j == "fr" and doc == "lettre_de_change") \
                else j
            per[j] = {"legal_due": ld.isoformat(),
                      "weekday": WD[ld.weekday()],
                      "roll_rule": ROLL_RULE[key],
                      "statutory_roll": key != "fr",
                      "shift_days": shifts,
                      "law": ROLL_LAW[key]}
        except DueError as e:
            per[j] = {"refused": e.message, "expected": e.expected}
    present = [date.fromisoformat(v["legal_due"]) for v in per.values()
               if "legal_due" in v]
    divergence = abs((max(present) - min(present)).days) if \
        len(present) >= 2 else 0

    # settlement : sur l'échéance APPLIQUÉE (juridiction) sinon sur
    # la date primaire ; colonne EUR seulement (rail GBP non lu —
    # refus nommé, doctrine b111 « ce qui n'est pas lu ne se jure
    # pas »).
    applied = per.get(jurisdiction, {}) if jurisdiction else {}
    settle_target = date.fromisoformat(applied["legal_due"]) \
        if "legal_due" in applied else primary
    if jurisdiction == "gb":
        settle = {"layer": "GBP — not TARGET2; the CHAPS text was "
                "not read, so no settlement column is promised "
                "(never swear an unread rail)",
                "target2_open": None, "interest_runs_from":
                settle_target.isoformat()}
    else:
        settle = _settlement(settle_target)

    out = {
        "terms": p,
        "document": doc,
        "readings": readings,
        "spread_days": (max(r["days_from_issue"] for r in readings) -
                        min(r["days_from_issue"] for r in readings))
        if readings else 0,
        "conventions_said": {
            "day0": "invoice date is day 0 — pinned on the four "
                    "published examples (March 1 + 30 -> March 31)",
            "anchor": cf,
            "primary_reading": "%s from %s" % (p["kind"], cf),
        },
        "jurisdictions": per,
        "divergence_max_days": divergence,
        "settlement_target2": settle,
    }
    if eom_methods:
        out["eom_methods"] = eom_methods
    if discount:
        out["discount_window"] = discount
    if jurisdiction:
        if "refused" in applied:
            raise DueError("invoice_date", applied["refused"],
                           applied["expected"])
        out["applied"] = {"jurisdiction": jurisdiction,
                          "legal_due": applied["legal_due"],
                          "roll_rule": applied["roll_rule"],
                          "shift_days": applied["shift_days"]}
        if jurisdiction == "fr":
            span = (primary - iss).days
            over = span > FR_NET_CAP_DAYS and p["kind"] in (
                "net", "worked", "ouvrables", "discount")
            out["fr_ceiling"] = {
                "days_from_issue": span,
                "cap": "60 jours nets à compter de l'émission "
                       "(L. 441-10, lu) — 45 jours fin de mois en "
                       "dérogation expresse",
                "over": bool(over),
                "verdict": "OVER_L441_10" if over else "WITHIN",
            }
    return out


def _add_days_checked(d, n):
    if not 0 <= n <= 400:
        raise DueError("terms", "day count %d outside the ceiling — "
                       "this module dates terms, not perpetuities"
                       % n, "1-400")
    return d + timedelta(days=n)
