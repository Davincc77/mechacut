"""withdrawalkit — /shop/withdrawal : le délai de RÉTRACTATION légal
français rendu en DATES, pas en prose.

LA DOULEUR (lentille HUMAIN, cycle 25-11, J-2 avant Black Friday) :
trois organisations de consommateurs LU publient le 24-nov la même
phrase (BEE SECURE, CEC, ULC) — « 14 jours à compter de la RÉCEPTION,
s'applique ÉGALEMENT aux articles en promotion, en MAGASIN aucun
droit automatique » ; la presse BF 2026 répète le 14 sans JAMAIS le
dater ; service-public F10485 écrit l'horloge en clair (« le décompte
commence le LENDEMAIN ; si ce délai expire un samedi, un dimanche ou
un jour férié, il est prolongé jusqu'au premier jour ouvrable ») —
et un agent à qui l'on dit « reçu mardi, jusqu'à quand ? » répond
avec un nombre rond, jamais une date, jamais le week-end. La loi
FRANCE ne se contente pas de dire 14 : L221-19 DONNE LA GRAMMAIRE
DU CALENDRIER, ancrée au règlement (CEE) 1182/71 du Conseil du
3 juin 1971 — jour de départ non compté, fin à la dernière heure du
dernier jour, prorogation samedi/dimanche/férié. Grammaire fermée,
jouable.

LES SOURCES (rejouées, jamais de mémoire) : Code de la consommation,
section 6 « Droit de rétractation applicable aux contrats conclus à
distance et hors établissement (Articles L221-18 à L221-28) »,
LEGI-texte LEGITEXT000006069565 / LEGISCTA000032221365 — texte
REJOUÉ VERBATIM le 25-11-2026 via le snapshot web.archive
2025-03-09 (archive.org/web/20250309114853) de la page legifrance,
avec concordance confirmée le jour même sur les extraits indexés
des versions EN VIGUEUR (L221-18 « en vigueur depuis le 01 juillet
2016 », création ordonnance n°2016-301 du 14 mars 2016 ; L221-28
modifié par ordonnance n°2021-1734 du 22 décembre 2021, en vigueur
depuis le 28 mai 2022 — les dates de version voyagent). Fiches
officielles service-public F10485 (counting, soldes/occasion,
exceptions rendues en exemples) et F11094 (le délai de rétractation
INTERROMPU par la mise en jeu de la garantie de conformité, à rejouer
à la livraison du bien neuf) : REJOUÉES 25-11-2026.

LES RÈGLES, toutes datées :
  * point de départ selon le contrat (L221-18, verbatim) : biens →
    réception (DERNIER bien si livraisons séparées ; PREMIER si
    livraison régulière) ; services → conclusion ; hors établissement
    → conclusion, le droit s'exerce dès ce jour même pour les biens ;
  * horloge (L221-19) : lendemain compté jour 1 ; quatorzième jour
    à minuit ; samedi/dimanche/férié → premier jour ouvrable
    suivant. Fériés = NOTRE table L3133-1 (schedule/holidays) —
    théorème des sœurs, pas de seconde table ;
  * L221-20 : info rétractation manquante → douze mois de plus à
  compter de l'expiration initiale ; info fournie PENDANT cette
  prolongation → nouvelle période de quatorze jours ;
  * L221-23/L221-24 rendus comme secondes horloges : renvoi et
    remboursement = +14 jours calendaires depuis la communication,
    SANS prorogation publiée pour ces délais-là — la divergence est
    NOMMÉE, pas moyennée ;
  * L221-28 : treize exceptions fermées en classes nommées, chacune
    rendant son clause verbatim.

CE QUE L'OUTIL NE FAIT PAS : pas de fenêtre ENSEIGNE (sœur
return-deadline), pas d'horloge PANNE/DÉFAUT (sœur legal-guarantee),
pas de droit en MAGASIN (HORS L221-18, refusé par nom), pas de BE/
LU/BR/UK (non rejoués, refusés par nom — la directive harmonise le
14 jours, chaque pays a sa grammaire de comptage), aucun fetch,
aucune horloge murale : as_of est un ARGUMENT.
"""

import calendar
from datetime import date, timedelta

import holidays as holidays_kit

class WithdrawalError(Exception):
    def __init__(self, field, message, expected):
        self.field = field
        self.message = message
        self.expected = expected
        super().__init__(message)


PERIOD_DAYS = 14           # L221-18 : « un délai de quatorze jours »
EXT_MONTHS = 12            # L221-20 : « prolongé de douze mois »
YEAR_MIN, YEAR_MAX = 1900, 2099   # range de la table de computus (holidays)

KINDS = ("goods", "services", "off_premises", "subscriptions")

START_RULES = {
    "goods": ("L221-18 2°", "De la réception du bien par le "
              "consommateur ou un tiers, autre que le transporteur, "
              "désigné par lui, pour les contrats de vente de biens."
              " — plusieurs biens livrés séparément : réception du "
              "DERNIER bien ou lot ou pièce ; bien composé livré par "
              "étapes sur période définie : réception de la DERNIÈRE "
              "pièce (alinéa 3 verbatim)"),
    "services": ("L221-18 1°", "De la conclusion du contrat, pour "
                 "les contrats de prestation de services et ceux "
                 "mentionnés à l'article L. 221-4"),
    "off_premises": ("L221-18 2° (alinéa 2)", "Pour les contrats "
                     "conclus hors établissement, le consommateur "
                     "peut exercer son droit de rétractation à "
                     "compter de la conclusion du contrat"),
    "subscriptions": ("L221-18 alinéa 4", "Pour les contrats "
                      "prévoyant la livraison régulière de biens "
                      "pendant une période définie, le délai court "
                      "à compter de la réception du premier bien"),
}

CLOCK_L221_19 = (
    "Conformément au règlement n° 1182/71/CEE du Conseil du 3 juin "
    "1971 portant détermination des règles applicables aux délais, "
    "aux dates et aux termes : 1° Le jour où le contrat est conclu "
    "ou le jour de la réception du bien n'est pas compté dans le "
    "délai mentionné à l'article L. 221-18 ; 2° Le délai commence à "
    "courir au début de la première heure du premier jour et prend "
    "fin à l'expiration de la dernière heure du dernier jour du "
    "délai ; 3° Si ce délai expire un samedi, un dimanche ou un jour "
    "férié ou chômé, il est prorogé jusqu'au premier jour ouvrable "
    "suivant. (Code de la consommation, art. L221-19, création "
    "ordonnance n°2016-301 du 14 mars 2016)")

EXCEPTIONS = {  # L221-28, treize classes fermées, clause verbatim
    "service_executed": (1, "De fourniture de services pleinement "
        "exécutés avant la fin du délai de rétractation et, si le "
        "contrat soumet le consommateur à une obligation de payer, "
        "dont l'exécution a commencé avec son accord préalable et "
        "exprès et avec la reconnaissance par lui de la perte de son "
        "droit de rétractation, lorsque la prestation aura été "
        "pleinement exécutée par le professionnel",
        "les trois conditions voyagent ensemble : exécution + accord "
        "préalable exprès + reconnaissance de la perte"),
    "financial_market": (2, "De fourniture de biens ou de services "
        "dont le prix dépend de fluctuations sur le marché financier "
        "échappant au contrôle du professionnel et susceptibles de se "
        "produire pendant le délai de rétractation",
        "l'exemple rendu par F10485 : l'achat d'or"),
    "made_to_order": (3, "De fourniture de biens confectionnés selon "
        "les spécifications du consommateur ou nettement "
        "personnalisés",
        "F10485 nomme la frontière : choisir une couleur ou une "
        "finition dans une gamme standard ne personnalise pas "
        "assez pour exclure"),
    "perishable": (4, "De fourniture de biens susceptibles de se "
        "détériorer ou de se périmer rapidement",
        "F10485 excepte les aliments à DDM (date de durabilité "
        "minimale)"),
    "unsealed_hygiene": (5, "De fourniture de biens qui ont été "
        "descellés par le consommateur après la livraison et qui ne "
        "peuvent être renvoyés pour des raisons d'hygiène ou de "
        "protection de la santé",
        "exemples F10485 : cosmétiques operculés, sous-vêtements en "
        "sachets fermés"),
    "inseparable_mix": (6, "De fourniture de biens qui, après avoir "
        "été livrés et de par leur nature, sont mélangés de manière "
        "indissociable avec d'autres articles",
        "exemple F10485 : la télécommande d'un téléviseur"),
    "alcohol_delayed": (7, "De fourniture de boissons alcoolisées "
        "dont la livraison est différée au-delà de trente jours et "
        "dont la valeur convenue à la conclusion du contrat dépend "
        "de fluctuations sur le marché échappant au contrôle du "
        "professionnel",
        "les DEUX conditions : différé > 30 jours ET valeur liée au "
        "marché"),
    "urgent_home_repair": (8, "De travaux d'entretien ou de "
        "réparation à réaliser en urgence au domicile du "
        "consommateur et expressément sollicités par lui, dans la "
        "limite des pièces de rechange et travaux strictement "
        "nécessaires pour répondre à l'urgence",
        "la limite est dans la clause : l'urgence seulement"),
    "unsealed_media": (9, "De fourniture d'enregistrements audio ou "
        "vidéo ou de logiciels informatiques lorsqu'ils ont été "
        "descellés par le consommateur après la livraison",
        "descellé = l'opercle ; l'achat scellé reste rétractable"),
    "press_daily": (10, "De fourniture d'un journal, d'un périodique "
        "ou d'un magazine, sauf pour les contrats d'abonnement à ces "
        "publications",
        "le « sauf » est dans la clause : l'ABONNEMENT reste "
        "rétractable"),
    "public_auction": (11, "Conclus lors d'une enchère publique",
        "l'enchère publique seulement ; la vente en ligne à prix "
        "décroissant n'est pas couverte par ce 11°"),
    "dated_services": (12, "De prestations de services "
        "d'hébergement, autres que d'hébergement résidentiel, de "
        "services de transport de biens, de locations de voitures, "
        "de restauration ou d'activités de loisirs qui doivent être "
        "fournis à une date ou à une période déterminée",
        "héb. résidentiel excepté dans la clause elle-même"),
    "digital_started": (13, "De fourniture d'un contenu numérique "
        "sans support matériel dont l'exécution a commencé avant la "
        "fin du délai de rétractation et, si le contrat soumet le "
        "consommateur à une obligation de payer, lorsque : a) il a "
        "donné préalablement son consentement exprès ; b) il a "
        "reconnu qu'il perdra son droit ; c) le professionnel a "
        "fourni la confirmation de l'accord (L. 221-13 al. 2)",
        "l'exemple rendu par F10485 : le film téléchargé"),
}

_REFUSAL_OTHER_COUNTRY = (
    "be|lu|br|uk et les autres refused by name: directive 2011/83/EU "
    "harmonises the 14 days but NOT each state's counting grammar — "
    "this replay covers only the French articles. Belgium/Luxembourg "
    "carry their own sale-calendar sisters (shop/soldes-be, "
    "shop/soldes-window for France); Brazil runs a different "
    "arrependimento clock (CDC art. 49, not replayed here)")

_REFUSAL_IN_STORE = (
    "in_store refused by name carrying its statute: L221-18 opens "
    "the 14 days for contracts « conclus à distance, à la suite "
    "d'un démarchage téléphonique ou hors établissement » — a plain "
    "shop purchase is outside the article, so NO automatic legal "
    "right exists (BEE SECURE/CEC/ULC 24-Nov say the same words); "
    "the store's own window is a different clock: /shop/"
    "return-deadline")


def _iso(d, field):
    if not isinstance(d, str):
        raise WithdrawalError(field, "date must be an ISO YYYY-MM-DD "
                              "string", "ISO YYYY-MM-DD")
    try:
        dt = date.fromisoformat(d[:10])
    except ValueError:
        raise WithdrawalError(field, "not a valid calendar date: %r"
                              % d, "ISO YYYY-MM-DD")
    if not YEAR_MIN <= dt.year <= YEAR_MAX:
        raise WithdrawalError(field,
            "%s: outside %04d-%04d — the holiday calendar is the "
            "anchored computus, not vibes" % (d, YEAR_MIN, YEAR_MAX),
            "a date in %04d-%04d" % (YEAR_MIN, YEAR_MAX))
    return dt


def _wd(d):
    return calendar.day_name[d.weekday()]


def _holiday(d):
    """(name, law) if d is an FR legal holiday, else None. THE ONE
    TABLE — schedule/holidays, Code du travail L3133-1 cited per
    line. Reused, never re-typed."""
    res = holidays_kit.holidays("FR", d.year)
    iso = d.isoformat()
    for x in res["holidays"]:
        if x["date"] == iso:
            return x["name"], x["law"]
    return None


def _advance(dt):
    """L221-19 3°: Saturday, Sunday or a legal holiday pushes the
    expiry to the first business day after. Returns (final, chain)."""
    chain = []
    while True:
        w = dt.weekday()
        if w == 5:
            chain.append({"date": dt.isoformat(), "reason": "Saturday"})
        elif w == 6:
            chain.append({"date": dt.isoformat(), "reason": "Sunday"})
        else:
            h = _holiday(dt)
            if h:
                chain.append({"date": dt.isoformat(),
                              "reason": "holiday: %s (%s)" % h})
            else:
                break
        dt += timedelta(days=1)
    return dt, chain


def _plus_months(d, months):
    """+N calendar months, clamped to month end — the sister
    convention (dates.py _add_calendar). 2028-02-29 +12 -> 2029-02-28."""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def withdrawal(start_date, kind="goods", notified=None,
               info_missing=False, info_date=None,
               product_class=None, as_of=None, country="fr"):
    c = (country or "fr").strip().lower()
    if c != "fr":
        raise WithdrawalError("country", _REFUSAL_OTHER_COUNTRY,
                              "fr")
    k = (kind or "").strip().lower()
    if k == "in_store":
        raise WithdrawalError("kind", _REFUSAL_IN_STORE,
                              " | ".join(KINDS))
    if k not in KINDS:
        raise WithdrawalError("kind", "kind outside the closed set "
                              "— the four contract families L221-18 "
                              "names its own start for",
                              " | ".join(KINDS))
    s = _iso(start_date, "start_date")

    if product_class is not None:
        pc = str(product_class).strip().lower()
        if pc not in EXCEPTIONS:
            raise WithdrawalError("product_class",
                "product_class outside the thirteen closed classes "
                "of L221-28 — an exception is a named clause, never "
                "a guess", " | ".join(sorted(EXCEPTIONS)))
    else:
        pc = None

    day1 = s + timedelta(days=1)                    # L221-19 1°
    raw = s + timedelta(days=PERIOD_DAYS)           # 14e jour
    fin, chain = _advance(raw)

    out = {
        "country": "FR",
        "kind": k,
        "start_date": s.isoformat(),
        "start_weekday": _wd(s),
        "start_rule": {"article": START_RULES[k][0],
                       "text": START_RULES[k][1]},
        "clock": {"article": "L221-19",
                  "anchor": "règlement (CEE) n° 1182/71 du Conseil, "
                            "3 juin 1971 — cité par l'article",
                  "text": CLOCK_L221_19},
        "day1": day1.isoformat(),
        "deadline_initial": raw.isoformat(),
        "deadline_initial_weekday": _wd(raw),
        "deadline": fin.isoformat(),
        "deadline_weekday": _wd(fin),
        "extension_applied": bool(chain),
        "extension_chain": chain,
        "final_deadline": fin.isoformat(),
        "final_deadline_source": "L221-18 + L221-19",
        "notified": None,
        "return_by": None,
        "refund_by": None,
        "info_missing": bool(info_missing),
        "info_date": None,
        "extended_12m": None,
        "restarted_deadline": None,
        "exception": None,
    }

    if info_date is not None:
        i = _iso(info_date, "info_date")
        # L221-20 existe pour l'information QUI MANQUAIT : un
        # info_date l'implique — le champ repart true, jamais on ne
        # laisse « info fournie » contredire « info tardive ».
        out["info_missing"] = True
        out["info_date"] = i.isoformat()

    if out["info_missing"]:
        ext = _plus_months(fin, EXT_MONTHS)        # L221-20 al. 1
        out["extended_12m"] = ext.isoformat()
        if out["info_date"] is None:
            out["final_deadline"] = ext.isoformat()
            out["final_deadline_source"] = "L221-20 al. 1 (douze mois)"
        else:
            if i < s:
                raise WithdrawalError("info_date",
                    "info_date %s precedes the contract's clock — "
                    "dates inverted are refused" % i.isoformat(),
                    "a date on or after start_date")
            if i > ext:
                # l'information n'est pas arrivée « pendant cette
                # prolongation » : pas de seconde période due
                out["final_deadline"] = ext.isoformat()
                out["final_deadline_source"] = ("L221-20 al. 1 — "
                    "info_date %s falls AFTER the twelve-month "
                    "prolongation, no new fourteen-day period is "
                    "born under al. 2" % i.isoformat())
            else:
                i_raw = i + timedelta(days=PERIOD_DAYS)
                i_fin, i_chain = _advance(i_raw)
                out["restarted_deadline"] = i_fin.isoformat()
                out["restarted_extension"] = i_chain
                out["final_deadline"] = i_fin.isoformat()
                out["final_deadline_source"] = ("L221-20 al. 2 — "
                    "new fourteen-day period from the day the late "
                    "information arrived (%s)" % i.isoformat())

    if notified is not None:
        n = _iso(notified, "notified")
        fdl = date.fromisoformat(out["final_deadline"])
        if n < s:
            raise WithdrawalError("notified",
                "notified %s precedes the clock's start %s — dates "
                "inverted are refused, not sorted (the contract "
                "does not reorder itself)" % (n.isoformat(),
                                              s.isoformat()),
                "a date on or after start_date")
        if n > fdl:
            raise WithdrawalError("notified",
                "notified %s after the governing deadline %s — the "
                "right was already closing or closed on that date; "
                "the tool dates, it does not plead" % (n.isoformat(),
                                                       out["final_deadline"]),
                "a date on or before the final deadline")
        nb = n + timedelta(days=PERIOD_DAYS)
        out["notified"] = n.isoformat()
        # L221-23 et L221-24 rendent quatorze JOURS CALENDAIRES ; la
        # prorogation de L221-19 est écrite pour LE DÉLAI de l'article
        # L221-18 — ces deux secondes horloges voyagent sans chain,
        # DIVERGENCE NOMMÉE en conditions, jamais moyennée.
        out["return_by"] = nb.isoformat()
        out["refund_by"] = nb.isoformat()

    if pc is not None:
        num, clause, note = EXCEPTIONS[pc]
        out["exception"] = {"class": pc, "article": "L221-28 %d°" % num,
                            "clause": clause, "note": note}

    if as_of is not None:
        a = _iso(as_of, "as_of")
        fdl = date.fromisoformat(out["final_deadline"])
        out["as_of"] = a.isoformat()
        if pc is not None:
            out["days_left"] = None
            out["verdict"] = "NOT_WITHDRAWABLE"
        elif a > fdl:
            out["days_left"] = (fdl - a).days
            out["verdict"] = "EXPIRED"
        elif a == fdl:
            out["days_left"] = 0
            out["verdict"] = "FINAL_DAY"
        else:
            out["days_left"] = (fdl - a).days
            out["verdict"] = "OPEN"
    else:
        out["as_of"] = None
        out["days_left"] = None
        out["verdict"] = ("NOT_WITHDRAWABLE" if pc is not None
                          else "UNDATED — as_of is an argument, "
                               "the wall clock is never read")

    out["conditions"] = [
        "the fourteen days run from the start ABOVE, counted per "
        "L221-19: the start day is NOT counted, the period ends at "
        "the last hour of day 14, and a Saturday/Sunday/legal-holiday "
        "expiry advances day by day (rule verbatim in clock.text)",
        "return_by/refund_by are calendar fourteen-day clocks from "
        "the communication (L221-23, L221-24) — the advance rule of "
        "L221-19 is written for the L221-18 period, so these two "
        "travel WITHOUT weekend extension: divergence named, never "
        "averaged",
        "refund may be deferred until the goods are recovered or "
        "proof of shipping is given, whichever comes FIRST "
        "(L221-24 al. 2 verbatim); direct return costs fall on the "
        "consumer unless the seller waived or failed to disclose "
        "them (L221-23 al. 2)",
        "the right also runs on SALE, second-hand and clearance "
        "goods bought at distance — « le droit de rétractation "
        "s'applique aussi si le produit est soldé, d'occasion ou "
        "déstocké » (service-public F10485, replayed 25-Nov-2026); "
        "a shop window promo does not cancel it",
        "a legal-guarantee claim opened DURING the window interrupts "
        "it; the fourteen-day count RESTARTS at the delivery of the "
        "replaced or repaired conforming good (service-public "
        "F11094, replayed — /shop/legal-guarantee dates that clock)",
        "holidays used are the national L3133-1 table — Alsace-"
        "Moselle adds Good Friday and December 26 and is NOT folded "
        "in silently (named scope, same table as schedule/holidays)",
        "the store's voluntary holiday window is a DIFFERENT clock: "
        "/shop/return-deadline; broken-good windows: /shop/legal-"
        "guarantee; this tool answers CHANGED-MIND only",
    ]
    out["provenance"] = {
        "code": "Code de la consommation, section 6, L221-18 à "
                "L221-28 (LEGITEXT000006069565 / LEGISCTA000032221365)",
        "rejoue": "legifrance text replayed verbatim 25-Nov-2026 via "
                  "web.archive snapshot 2025-03-09 of the section "
                  "page; in-force versions confirmed same day "
                  "(L221-18 since 01-Jul-2016, ordonnance 2016-301; "
                  "L221-19 to L221-26 since 28-May-2022, ordonnance "
                  "2021-1734)",
        "official_fiches": "service-public.fr F10485 and F11094 "
                           "replayed 25-Nov-2026",
        "sister_table": "FR legal holidays: Code du travail "
                        "L3133-1 via /api/v1/schedule/holidays",
    }
    return out
