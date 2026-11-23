"""shipdeadkit — /shop/shipping-deadline : la dernière date d'envoi
pour Noël 2026, CROISÉE, et le conflit NOMMÉ quand une source d'autorité
dévie.

LA DOULEUR, mesurée par la lentille humaine (cross-audit ×6 publiés
entre le 13 et le 21-nov-2026 : thenewsherald, palmbeachpost,
sunherald, wpxi, providencejournal, pressconnects — tous consultés
23-nov-2026) :

  * les tableaux presse sont STATIQUES et muets sur leur propre
    divergence. L'audit croisé de CE cycle a pêché une source (USA
    Today/palmbeachpost) qui décale d'UN JOUR les trois lignes express
    FedEx — Express Saver Dec 22 (vs Dec 21 chez 5 sources), 2Day
    Dec 23 (vs Dec 22), Overnight Dec 24 (vs Dec 23) — parce que SA
    table est publiée contre une cible « delivery by December 25 »
    là où les autres publient « by Dec 24 ». La page ne le dit pas.
    Un agent qui lit UNE page perd un jour, ou promet un Noël manqué.
  * le piège FREEP, généralisé : la même famille d'articles publiait
    « First-Class Alaska/Hawaii: Thursday, Dec 27 » — lignes hors de la
    table des autres sources. Règle : une ligne n'entre qu'avec DEUX
    sources qui concordent ; la divergence est rendue NOMMÉE, pas
    moyennée.
  * l'écart sémantique dans un même tableau : USPS publie « delivery
    BEFORE Dec 25 », UPS/FedEx « by Dec 24 » — même soir d'arrivée
    (le 24, vendredi 25 étant férié chez tous), colonnes qui Semblent
    différentes. Ici `arrives_by` est la vérité unique (2026-12-24)
    et le publié-verbatim de chaque transporteur voyage à côté.
  * UPS Ground n'A PAS de date unique : « depends on your route, so
    check ups.com/ctc » (thenewsherald, verbatim). Une moyenne
    inventée serait une promesse fausse : c'est un refus NOMMÉ.
  * FedEx Ground/Home Delivery : la date dépend du TRANSIT (5 jours →
    Dec 17 … 1 jour → Dec 23, table palmbeachpost/wpxi/sunherald
    concordantes). Pas de transit en entrée = refus nommé, jamais un
    « en général ».

CONTRAT : year (défaut 2026, seule table publiée) + carrier + service
(+ transit_days pour fedex ground/home-delivery ; + as_of optionnel
pour le compte à rebours) → ship_by + jour de semaine DÉRIVÉ, arrives_by
commun, sources concordantes, conflit nommé s'il existe. Périmètre :
48 États contigus — Alaska/Hawaï et l'international sont HORS TABLE
(refus de promesse, la mention `scope` le dit).

ORACLE : chaque ship_by de la table a son jour de semaine PUBLIÉ en
dur par au moins une source (sunherald : « Thursday, Dec. 17 »,
« Monday, Dec. 21 », « Tuesday, Dec. 22 », « Wednesday, Dec. 23 »,
pressconnects : « Tuesday, Dec. 15 », providencejournal :
« Thursday, Dec. 24 ») ; les test rejouent ces jours publiés contre
le calendrier — la dérive du module EST testée contre la presse.

Doctrine : jamais de fetch, jamais d'horloge — la table est un FAIT
versionné par année (`table_version`), as_of est un ARGUMENT. Zéro LM.
"""
import datetime as _dt

class ShipDeadError(Exception):
    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected


TABLE_VERSION = "2026-11-23"
ARRIVES_BY = "2026-12-24"
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday")

# (ship_by, [sources concordantes], conflit éventuel
#  (ship_by_dissident, source, raison publiée))
_ROW = lambda d, s, c=None: {"ship_by": d, "sources": s, "conflict": c}
_MAJ = ["thenewsherald", "providencejournal", "wpxi", "sunherald",
        "pressconnects"]

YEARS = {
    2026: {
        "usps": {
            "phrasing": "delivery before Dec 25 (arrives by Dec 24)",
            "services": {
                "ground-advantage": _ROW(
                    "2026-12-17", ["thenewsherald", "palmbeachpost",
                                   "wpxi", "pressconnects"]),
                "first-class": _ROW(
                    "2026-12-17", ["thenewsherald", "palmbeachpost",
                                   "wpxi", "pressconnects"]),
                "priority": _ROW(
                    "2026-12-18", ["thenewsherald", "palmbeachpost",
                                   "wpxi", "pressconnects"]),
                "priority-express": _ROW(
                    "2026-12-19", ["thenewsherald", "palmbeachpost",
                                   "wpxi", "pressconnects"]),
            },
            "no_date": {},
        },
        "ups": {
            "phrasing": "delivery by Dec 24",
            "services": {
                "3-day-select": _ROW(
                    "2026-12-21", ["thenewsherald", "sunherald",
                                   "wpxi", "pressconnects"]),
                "2nd-day-air": _ROW(
                    "2026-12-22", ["thenewsherald", "sunherald",
                                   "wpxi", "pressconnects"]),
                "next-day-air": _ROW(
                    "2026-12-23", ["thenewsherald", "sunherald",
                                   "wpxi", "pressconnects"]),
            },
            "no_date": {
                "ground": (
                    "UPS Ground has NO single last ship day — it "
                    "depends on origin/destination zone: 'check "
                    "ups.com/ctc' (thenewsherald, verbatim). Any "
                    "average invented here would be a false promise."),
            },
        },
        "fedex": {
            "phrasing": "delivery by Dec 24",
            "services": {
                "ground-economy": _ROW(
                    "2026-12-15", ["palmbeachpost", "sunherald",
                                   "wpxi", "pressconnects"]),
                "express-saver": _ROW(
                    "2026-12-21", _MAJ,
                    ("2026-12-22", "palmbeachpost",
                     "its table is published against a 'delivery by "
                     "Dec 25' target where 5 sources publish 'by "
                     "Dec 24'")),
                "2day": _ROW(
                    "2026-12-22", _MAJ,
                    ("2026-12-23", "palmbeachpost",
                     "same shifted target as its Saver/overnight "
                     "rows (Dec 25 vs Dec 24)")),
                "overnight": _ROW(
                    "2026-12-23", ["wpxi", "sunherald",
                                   "pressconnects", "thenewsherald"],
                    ("2026-12-24", "palmbeachpost",
                     "same shifted target (Dec 25 vs Dec 24)")),
                "sameday": _ROW(
                    "2026-12-24", ["palmbeachpost", "sunherald",
                                   "wpxi", "pressconnects"]),
            },
            "transit": {
                "ground": _ROW("map", ["palmbeachpost", "wpxi",
                                       "sunherald"]),
                "home-delivery": _ROW("map", ["palmbeachpost", "wpxi",
                                              "sunherald"]),
            },
            "transit_map": {
                5: "2026-12-17", 4: "2026-12-18", 3: "2026-12-21",
                2: "2026-12-22", 1: "2026-12-23",
            },
            "no_date": {},
        },
    },
}

# aliases édités (grammaire fermée) : variante publiée -> clé canonique
ALIASES = {
    ("usps", "ground"): "ground-advantage",
    ("usps", "priority-mail"): "priority",
    ("usps", "priority-mail-express"): "priority-express",
    ("usps", "first-class-mail"): "first-class",
    ("ups", "3-day"): "3-day-select",
    ("ups", "3-day-select"): "3-day-select",
    ("ups", "2nd-day"): "2nd-day-air",
    ("ups", "2-day-air"): "2nd-day-air",
    ("ups", "next-day"): "next-day-air",
    ("fedex", "ground-economy"): "ground-economy",
    ("fedex", "economy"): "ground-economy",
    ("fedex", "saver"): "express-saver",
    ("fedex", "2-day"): "2day",
    ("fedex", "2day-am"): "2day",
    ("fedex", "2-day-am"): "2day",
    ("fedex", "first-overnight"): "overnight",
    ("fedex", "priority-overnight"): "overnight",
    ("fedex", "standard-overnight"): "overnight",
    ("fedex", "extra-hours"): "overnight",
    ("fedex", "same-day"): "sameday",
    ("fedex", "home"): "home-delivery",
}


def _norm(text, field):
    out = str(text).strip().lower().replace(" ", "-").replace("_", "-")
    if not out:
        raise ShipDeadError(field, "empty value",
                            "a carrier or service name")
    return out


def _wdays(iso):
    return WEEKDAYS[_dt.date.fromisoformat(iso).weekday()]


def ship_deadline(carrier, service, transit_days=None, year=2026,
                  as_of=None):
    carrier = _norm(carrier, "carrier")
    service = _norm(service, "service")
    if carrier not in ("usps", "ups", "fedex"):
        raise ShipDeadError(
            "carrier", f"unknown carrier '{carrier}'",
            "usps | ups | fedex — the table carries exactly these")
    ytab = YEARS.get(year)
    if ytab is None:
        raise ShipDeadError(
            "year", f"no published table for year {year}",
            "2026 — tables are versioned by year, never extrapolated")
    tab = ytab[carrier]
    service = ALIASES.get((carrier, service), service)
    svc = tab["services"].get(service)
    transit_tab = tab.get("transit", {})
    if svc is None and service not in transit_tab:
        if service in tab.get("no_date", {}):
            raise ShipDeadError(
                "service", f"{carrier} {service}: {tab['no_date'][service]}",
                "a service with a single published ship-by date: "
                + ", ".join(sorted(list(tab["services"])
                                   + list(transit_tab))))
        raise ShipDeadError(
            "service", f"unknown service '{service}' for {carrier}",
            "one of: " + ", ".join(sorted(list(tab["services"])
                                          + list(transit_tab)
                                          + list(tab.get("no_date",
                                                         {})))))
    is_transit = svc is None
    if is_transit:
        if transit_days is None:
            raise ShipDeadError(
                "transit_days",
                f"{carrier} {service} has no single date — its ship-by "
                f"depends on the transit days",
                "transit_days: one of 1, 2, 3, 4, 5")
        tmap = tab["transit_map"]
        if transit_days not in tmap:
            raise ShipDeadError(
                "transit_days",
                f"transit_days {transit_days} outside the published map",
                "one of: " + ", ".join(str(k) for k in sorted(tmap)))
        row = tmap[transit_days]
        ship_by = row
        sources = transit_tab[service]["sources"]
        conflict = None
        service_out = service
    else:
        if transit_days is not None:
            raise ShipDeadError(
                "transit_days",
                f"{carrier} {service} has ONE published ship-by date — "
                f"transit_days does not apply",
                "omit transit_days (it belongs to fedex ground and "
                "home-delivery)")
        ship_by = svc["ship_by"]
        sources = svc["sources"]
        conflict = svc["conflict"]
        service_out = service
    out = {
        "table_version": TABLE_VERSION,
        "year": year,
        "carrier": carrier,
        "service": service_out,
        "ship_by": ship_by,
        "ship_by_weekday": _wdays(ship_by),
        "arrives_by": ARRIVES_BY,
        "arrives_by_weekday": _wdays(ARRIVES_BY),
        "published_semantics": tab["phrasing"],
        "cross_check": {
            "agreeing_sources": list(sources),
            "conflict": None if conflict is None else {
                "ship_by": conflict[0], "source": conflict[1],
                "why": conflict[2]},
        },
        "scope": ("US lower 48 states only — Alaska/Hawaii and "
                  "international deadlines are EARLIER and not in this "
                  "table; a refusal here is honest, an average would "
                  "not be"),
    }
    if is_transit:
        out["transit_days"] = transit_days
    if as_of is not None:
        for bad, how in (("/", "slashes"), (".", "dots")):
            if bad in as_of:
                raise ShipDeadError(
                    "as_of", f"as_of '{as_of}' uses {how}",
                    "ISO YYYY-MM-DD (grouped or slashed forms are a "
                    "SHAPE problem: /num/parse first)")
        if len(as_of) != 10 or as_of[4] != "-" or as_of[7] != "-":
            raise ShipDeadError(
                "as_of", f"as_of '{as_of}' is not a plain ISO day",
                "ISO YYYY-MM-DD, no offset, no time")
        try:
            base = _dt.date.fromisoformat(as_of)
        except ValueError:
            raise ShipDeadError(
                "as_of", f"as_of '{as_of}' is not a real calendar day",
                "ISO YYYY-MM-DD")
        out["as_of"] = as_of
        out["days_left"] = (
            _dt.date.fromisoformat(ship_by) - base).days
        out["deadline_state"] = (
            "open" if out["days_left"] > 0
            else "last-day-today" if out["days_left"] == 0
            else "missed")
    return out
