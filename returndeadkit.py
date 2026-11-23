"""returndeadkit — /shop/return-deadline : la date limite de RETOUR
publiée pour un achat donné, CROISÉE ≥2 sources, provenance,
conventions et conflits NOMMÉS.

LA DOULEUR, mesurée par la lentille humaine (cycle 23-nov-2026,
Black Friday 27-nov) : les pages presse publient des manchettes
« you have until January 31 » et se TAISENT sur ce que leurs propres
tables contredisent :

  * SIX fins de fenêtres d'achat différentes dans la même saison :
    Amazon US déc-31, Amazon UK déc-25, Walmart déc-31, Target
    déc-24, Best Buy déc-31 (sellercentral, star-telegram/sacbee,
    thinkmoney, aol). Un achat Target du 26 décembre n'est PAS dans
    l'extension — la manchette « until Jan 31 » le laisse croire,
    la page publiée ne le dit pas.
  * le pattern publié comme un fait : parcelmonitor (nov-2026) écrit
    « every 2026 date in this article is last season's rule shifted
    forward by one year... treat each entry as the likely pattern,
    not the published fact », et dans la même page « Amazon has not
    yet published its 2026 holiday return policy » — alors que
    Seller Central publie le texte 2026 VERBATIM : « items purchased
    between November 1, 2026 and December 31, 2026 can be returned
    until January 31, 2027, except for Apple brand products, which
    can be returned until January 15, 2027 », appliqué à FBA comme
    FBM sans action du vendeur. Le conflit est un CHAMP de la
    réponse, jamais moyenné.
  * les discontinuités publiées que personne ne calcule : Best Buy
    membre Plus/Total — achats Oct 30→Dec 3 : date dure Jan 31 ;
    achats à partir de Dec 4 : FENÊTRE GLISSANTE de 60 jours. Deux
    règles selon le jour, sous une seule manchette. Et la note
    publiée « Day 1 is the date the customer acquires the product »
    est la CONVENTION de comptage : ici elle voyage dans la réponse
    et n'est jamais laissée à un off-by-one implicite.
  * le sens de la date : « last day to START the return, not the day
    the parcel must arrive » (parcelmonitor, verbatim) — le portail
    ferme à minuit.
  * le régime APRÈS la date : Amazon — late charge 20% du prix pendant
    les 30 premiers jours après la deadline, jusqu'à 100% au-delà
    (star-telegram) ; Best Buy — 45 $ d'activatable, 15% cameras/
    drones/projectors selon l'État ; Target — jusqu'à 35 $ sur un
    téléphone ouvert. Ces faits voyagent dans `fees`.

CONTRAT : retailer + purchase_date (ISO, saison 2026 seule jouée)
+ pays US|UK (même marque, deux contrats : la fenêtre Amazon ferme
Dec 31 aux US, Dec 25 au UK avec un « whichever is later » qui EXIGE
delivery_date) + category dans un vocabulaire FERMÉ + delivery_date
quand la règle court depuis la LIVRAISON (absent ≠ zéro : refus
nommé) + membership (bestbuy seulement — ailleurs il n'existe pas de
ligne datée publiée) + channel + as_of optionnel pour days_left.

RÈGLE D'ADMISSION : une ligne n'entre qu'avec DEUX sources qui
concordent, et sa classe de provenance voyage — published (texte
officiel rejoué) ou press2 (deux presses concordantes). Les lignes
single-source (Next, John Lewis, Argos, Boots — thinkmoney seul ;
Kohl's, Macy's, JCPenney — aol seul) sont REFUSÉES par nom, avec la
mention de ce que la source unique dit : un refus qui informe. Une
date en « pattern » (parcelmonitor se déclare lui-même pattern) ne
devient jamais une deadline chez nous.

ORACLE : les deadlines sont des dates PUBLIÉES en dur, jamais
dérivées ; les fenêtres glissantes utilisent le calendrier stdlib
sous la convention Day-1 publiée par Best Buy ; les tests rejouent
des golds tracés À LA MAIN avant l'implémentation.

Doctrine : jamais de fetch, jamais d'horloge — table versionnée
(`table_version`), as_of est un ARGUMENT. Zéro LM.
"""
import datetime as _dt

class ReturnDeadError(Exception):
    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected

TABLE_VERSION = "2026-11-23"
SEASON = "2026-2027"
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday")

_MEANING = ("last day to START the return, not the day the parcel "
            "must arrive — portals stop offering the option at "
            "midnight (published semantics, parcelmonitor verbatim)")

_P = "published"   # texte officiel rejoué verbatim
_J = "press2"      # deux presses concordantes

RETAILERS = {
    ("US", "amazon"): {
        "window": ("2026-11-01", "2026-12-31"),
        "extension": "2027-01-31",
        "extension_for": "most products",
        "exceptions": {"apple": ("2027-01-15",
                                 "Apple-branded products — Seller "
                                 "Central 2026 text, verbatim")},
        "standard": {"days": 30, "basis": "delivery",
                     "note": "standard 30 days from delivery"},
        "marketplace": "auto",
        "provenance": [_P],
        "sources": ["sellercentral.amazon.com 2026 extended holiday "
                    "returns policy (verbatim, FBA+FBM)",
                    "star-telegram/sacbee article318204164",
                    "miamiherald, aol (concordant)"],
        "conflicts": ["parcelmonitor (nov-2026) presents 'last "
                      "season's rule shifted by one year' as its "
                      "table and states 'Amazon has not yet published "
                      "its 2026 holiday return policy' — Seller "
                      "Central had published the 2026 text verbatim. "
                      "NAMED, never averaged"],
        "fees": ["after the deadline: 20% of the item's price for "
                 "the first 30 days, up to 100% beyond "
                 "(star-telegram, verbatim)",
                 "damaged/incomplete: up to 50% of the item's price "
                 "(aol table)"],
        "conditions": ["gift recipients return with the 17-digit "
                       "order number on the gift receipt/packing "
                       "slip (miamiherald)",
                       "non-returnable year-round: customized "
                       "products, perishables, final sale, certain "
                       "digital (Amazon policy, via miamiherald)"],
    },
    ("UK", "amazon"): {
        "window": ("2026-11-01", "2026-12-25"),
        "extension": "2027-01-31",
        "extension_later_of": {"days": 30, "basis": "delivery"},
        "exceptions": {},
        "standard": {"days": 30, "basis": "delivery",
                     "note": "30 days from receipt (voluntary "
                             "policy)"},
        "marketplace": "auto",
        "provenance": [_J],
        "sources": ["thinkmoney.co.uk (extended policies announced, "
                    "as of 16-nov-2026)",
                    "policyreturn.com (same window end and rule)"],
        "conflicts": ["same brand, two contracts: Amazon US closes "
                      "the purchase window Dec 31, Amazon UK closes "
                      "it Dec 25 AND adds 'or within 30 days of "
                      "delivery, whichever is later'. Country is a "
                      "required input; the rows never share"],
        "fees": [],
        "conditions": ["statutory 14-day cancellation right from "
                       "receipt runs INDEPENDENTLY of the voluntary "
                       "window (policyreturn, UK)",
                       "fashion (clothes, shoes, bags, jewellery, "
                       "watches): free returns within the 30 days "
                       "(policyreturn)"],
    },
    ("US", "walmart"): {
        "window": ("2026-10-01", "2026-12-31"),
        "extension": "2027-01-31",
        "extension_for": "most eligible purchases",
        "exceptions": {},
        "standard": {"days": 90, "basis": "purchase",
                     "note": "typical 90-day window (wreg); the "
                             "basis day (purchase vs delivery) is "
                             "not published — named, see "
                             "counting_convention"},
        "marketplace": "optin",
        "provenance": [_J],
        "sources": ["star-telegram/sacbee (Oct 1–Dec 31 → Jan 31, "
                    "marketplace caveat)", "aol 2026 table",
                    "wreg (typical 90 days)"],
        "conflicts": [],
        "fees": ["major appliances: 20% restocking (aol table)"],
        "conditions": ["excluded from the extension, shorter "
                       "standard rules: phones, protection plans, "
                       "major appliances, Dyson, food, some seasonal "
                       "and luxury items (sacbee; parcelmonitor "
                       "concordant)",
                       "marketplace sellers MAY opt in but are not "
                       "automatic (sacbee, parcelmonitor, cbs 2025) "
                       "— channel=marketplace returns a CONDITIONAL "
                       "row, never a promise"],
    },
    ("US", "target"): {
        "window": ("2026-11-01", "2026-12-24"),
        "extension": "2027-01-24",
        "extension_for": ["electronics", "entertainment",
                          "target_plus"],
        "exceptions": {"apple": ("2027-01-08",
                                 "Apple, Beats and mobile phones "
                                 "(sacbee, aol)"),
                       "beats": ("2027-01-08", "same line"),
                       "phone": ("2027-01-08", "same line")},
        "standard": {"days": 90, "basis": "purchase",
                     "note": "typical 90 days for new, unopened "
                             "general items (cbs, parcelmonitor)"},
        "standard_without_date": ("Target's per-category STANDARD "
                                  "window outside the extension "
                                  "dates is not in our >=2-source "
                                  "table — named refusal, not a "
                                  "borrowed deadline"),
        "marketplace": "auto-if-plus",
        "provenance": [_J],
        "sources": ["star-telegram/sacbee (Nov 1–Dec 24 → Jan 24; "
                    "Jan 8 Apple/Beats/phones)",
                    "parcelmonitor (pattern CONCORDANT, marked "
                    "pattern) + wreg"],
        "conflicts": ["the purchase window ends Dec 24, SEVEN days "
                      "before Amazon's: a Target electronics "
                      "purchase of Dec 26 is not in the extension "
                      "at all — the shared headline 'until January "
                      "31' does not say so",
                      "general purchases NEVER join the extension: "
                      "Target's own rule keeps them on the typical "
                      "90-day clock (cbs)"],
        "fees": ["opened mobile phones: restocking up to $35, "
                 "waived if sealed (parcelmonitor)"],
        "conditions": ["Target Circle Card holders: +30 days on the "
                       "standard 90 for general items (cbs) — a "
                       "membership this tool does NOT model: it "
                       "changes the standard clock, not the holiday "
                       "rows"],
    },
    ("US", "bestbuy"): {
        "window": ("2026-10-30", "2026-12-31"),
        "extension": "2027-01-15",
        "extension_for": "most purchases",
        "exceptions": {},
        "member_rule": {
            "hard_until": ("2026-12-03", "2027-01-31"),
            "rolling_from": "2026-12-04", "rolling_days": 60,
            "note": "Plus/Total: purchases Oct 30–Dec 3 → Jan 31 "
                    "2027; purchases on/after Dec 4 → 60-day window "
                    "(bestbuy.com, verbatim table)"},
        "short_windows": {"activatable": 14, "phone": 14,
                          "verizon": 30, "decoration": 15},
        "excluded_from_extension": ["applecare"],
        "standard": {"days": 15, "basis": "delivery",
                     "note": "standard period begins the day you "
                             "RECEIVE (bestbuy.com, verbatim)"},
        "member_standard_days": 60,
        "marketplace": "standard_only",
        "provenance": [_P],
        "sources": ["bestbuy.com Return & Exchange Promise (holiday "
                    "table + Day-1 footnote, verbatim)",
                    "corporate.bestbuy.com 2026 holiday calendar",
                    "aol + al.com (concordant)"],
        "conflicts": ["the member rule is TWO rules under one "
                      "headline: a Dec 3 member purchase gets Jan 31 "
                      "(hard date), a Dec 4 member purchase gets the "
                      "60-day rolling window — adjacent days, "
                      "different rule names, never a blend",
                      "short windows SURVIVE the extension: "
                      "decorations 15 days, activatables 14 (Verizon "
                      "30) even inside Oct 30–Dec 31 (bestbuy.com)"],
        "fees": ["activatable devices: $45 restocking; drones, "
                 "digital cameras, camera lenses, projectors: 15% "
                 "(state and condition dependent) (aol, "
                 "bestbuy.com)"],
        "conditions": ["Plus/Total extended timeframes do NOT apply "
                       "to Marketplace purchases (bestbuy.com)",
                       "Verizon activatable devices: 30-day return "
                       "period for ALL customers (bestbuy.com)"],
    },
    ("US", "costco"): {
        "window": None,
        "extension": None,
        "exceptions": {},
        "standard": {"days": 90, "basis": "delivery",
                     "only_for": ["electronics"],
                     "note": "90 days after delivery: TVs, laptops, "
                             "tablets, certain appliances (sacbee, "
                             "parcelmonitor)"},
        "general_no_date": ("Costco general merchandise: membership "
                            "return guarantee WITHOUT a dated window "
                            "— a date cannot be computed and this "
                            "tool refuses to invent one"),
        "marketplace": "n/a",
        "provenance": [_J],
        "sources": ["star-telegram/sacbee (90 days after delivery, "
                    "specified devices)", "parcelmonitor (standing "
                    "policy, no holiday deadline)"],
        "conflicts": ["Costco publishes NO holiday extension: the "
                      "January-31 headlines across the press say "
                      "nothing about it — its only dated clock is "
                      "the 90-day electronics rule from DELIVERY"],
        "fees": [],
        "conditions": ["no action needed at the holidays: the 90-day "
                       "clock is the same all season"],
    },
}

# grammaire FERMÉE : un synonyme inventé routerait vers la mauvaise
# deadline — les alias ci-dessous sont édités depuis les pages sources.
CATEGORY_ALIASES = {
    "general": "general", "most": "general", "other": "general",
    "toy": "general", "toys": "general", "clothing": "general",
    "furniture": "general",
    "electronics": "electronics", "tv": "electronics",
    "laptop": "electronics", "laptops": "electronics",
    "tablet": "electronics", "computer": "electronics",
    "console": "electronics", "camera": "electronics",
    "entertainment": "entertainment", "movie": "entertainment",
    "video-game": "entertainment", "games": "entertainment",
    "apple": "apple", "ipad": "apple", "mac": "apple",
    "macbook": "apple", "airpods": "apple",
    "iphone": "phone", "phone": "phone", "mobile": "phone",
    "smartphone": "phone", "cell phone": "phone",
    "beats": "beats", "beats-by-dr-dre": "beats",
    "activatable": "activatable", "cellular": "activatable",
    "hotspot": "activatable", "mobile-hotspot": "activatable",
    "verizon": "verizon",
    "decoration": "decoration", "decorations": "decoration",
    "holiday-decorations": "decoration",
    "artificial-tree": "decoration", "christmas-lights":
    "decoration",
    "applecare": "applecare", "applecare+": "applecare",
    "protection-plan": "protection_plan",
    "protection_plan": "protection_plan",
    "target-plus": "target_plus", "target_plus": "target_plus",
    "targetplus": "target_plus",
}

COUNTRIES = ("US", "UK")

_SINGLE_SOURCE_UK = {
    "next": "thinkmoney: eligible purchases 23-oct→25-dec 2026 → "
            "5-jan-2027 (ONE source, 16-nov-2026)",
    "john-lewis": "thinkmoney: 1-oct→24-dec 2026 → 23-jan-2027; "
                  "parcelmonitor repeats it but declares itself "
                  "pattern-only",
    "argos": "thinkmoney: 23-sep→25-dec 2026 → 31-jan-2027",
    "boots": "thinkmoney: online orders from 1-oct 2026 → "
             "31-jan-2027",
}

_KNOWN_REFUSAL_EXTRA = (
    " Kohl's (Oct 4–Dec 30 → Jan 31), Macy's (Oct 5–Dec 31 → Jan 31),"
    " JCPenney (→ Jan 31), Marshalls/TJ Maxx, ShopDisney, Nordstrom"
    " Rack: each known from a SINGLE press table (aol/wyff4) —"
    " refused by the >=2 concordant rule until a second source lands")

RETAILER_ALIASES = {
    "amazon": "amazon", "amazon.com": "amazon",
    "amazon.co.uk": "amazon", "amazon uk": "amazon",
    "amazonus": "amazon", "amazonusa": "amazon",
    "walmart": "walmart", "walmart.com": "walmart",
    "target": "target", "target.com": "target",
    "best buy": "bestbuy", "bestbuy": "bestbuy", "best_buy":
    "bestbuy", "best buy official": "bestbuy",
    "costco": "costco", "costco.com": "costco",
}

def _d(s, field="purchase_date"):
    try:
        return _dt.date.fromisoformat(s)
    except Exception:
        raise ReturnDeadError(field, "not an ISO calendar date: %r"
                              % (s,), "YYYY-MM-DD, e.g. 2026-12-20")

def _iso(d):
    return d.isoformat()

def _wd(d):
    return WEEKDAYS[d.weekday()]

def _last_day(start, days):
    """Convention publiée par Best Buy : 'Day 1 is the date the
    customer acquires the product' → dernier jour = start + days-1."""
    return start + _dt.timedelta(days=days - 1)

def return_deadline(retailer, purchase_date, country="US",
                    category=None, delivery_date=None,
                    membership=None, channel="first_party",
                    as_of=None):
    key_country = (country or "US").upper()
    if key_country not in COUNTRIES:
        raise ReturnDeadError(
            "country", "no crossed table for %r — this table is US "
            "and UK only; a promise on a market without >=2 "
            "concordant published sources would be a false one"
            % (key_country,), "US | UK")
    rn = RETAILER_ALIASES.get(retailer.strip().lower())
    if rn is None:
        slug = retailer.strip().lower().replace(" ", "-")
        if key_country == "UK" and slug in _SINGLE_SOURCE_UK:
            raise ReturnDeadError(
                "retailer", "%s: %s — ONE source, and our admission "
                "rule is >=2 concordant: named refusal carrying the "
                "candidate fact instead of a silent hole" % (
                    retailer, _SINGLE_SOURCE_UK[slug]),
                "amazon (UK); US: amazon | walmart | target | "
                "bestbuy | costco")
        raise ReturnDeadError(
            "retailer", "not in the 2026-2027 table: %r.%s" % (
                retailer, _KNOWN_REFUSAL_EXTRA),
            "amazon | walmart | target | bestbuy | costco (US), "
            "amazon (UK)")
    row = RETAILERS[(key_country, rn)]
    p = _d(purchase_date)
    if p.year != 2026:
        raise ReturnDeadError(
            "purchase_date", "outside the table season: this table "
            "is versioned for purchases made in 2026 (%s) — 2025 "
            "rules are not replayed, 2027 rules are not published "
            "yet" % SEASON, "2026-01-01 .. 2026-12-31")
    if membership and rn != "bestbuy":
        raise ReturnDeadError(
            "membership", "no dated membership return line is "
            "published for %s (Amazon Prime, Walmart+ and Circle "
            "Card change fees and standard-clock terms, not the "
            "holiday deadline row)" % rn,
            "omit membership, or retailer=bestbuy")
    cat = "general"
    if category is not None:
        c = category.strip().lower()
        if c not in CATEGORY_ALIASES:
            raise ReturnDeadError(
                "category", "unknown category %r — the grammar is "
                "closed; an invented synonym routes to the wrong "
                "deadline" % (category,),
                "general | electronics | entertainment | apple | "
                "beats | phone | activatable | verizon | decoration "
                "| applecare | protection_plan | target_plus")
        cat = CATEGORY_ALIASES[c]
    if channel not in ("first_party", "marketplace"):
        raise ReturnDeadError("channel", "unknown channel %r" % (
            channel,), "first_party | marketplace")
    dd = _d(delivery_date, "delivery_date") \
        if delivery_date else None

    out = {
        "table_version": TABLE_VERSION, "season": SEASON,
        "country": key_country, "retailer": rn,
        "purchase_date": _iso(p), "category": cat,
        "return_meaning": _MEANING,
        "provenance": row["provenance"], "sources": row["sources"],
    }
    if row["conflicts"]:
        out["conflicts"] = row["conflicts"]
    if row["fees"]:
        out["fees"] = row["fees"]
    if row["conditions"]:
        out["conditions"] = row["conditions"]

    if rn == "costco":
        out["purchase_window"] = None
        if cat not in ("electronics",):
            raise ReturnDeadError(
                "category", row["general_no_date"],
                "category=electronics (90 days from delivery)")
        if dd is None:
            raise ReturnDeadError(
                "delivery_date", "Costco's 90-day electronics clock "
                "counts from DELIVERY (sacbee, verbatim); without "
                "it any date would be invented — absent is not zero",
                "ISO delivery date")
        deadline = _last_day(dd, 90)
        rule = "standing-90-day-electronics"
        out["counting_convention"] = _convention(rn, 90, published=
                                                 False)
    else:
        out["purchase_window"] = list(row["window"])

        # ---- 1. fenêtres courtes Best Buy : elles SURVIVENT à
        #         l'extension (publié : decorations 15 j, activatables
        #          14 j, Verizon 30 j, y compris Oct 30→Dec 31)
        if rn == "bestbuy" and cat in row["short_windows"]:
            days = row["short_windows"][cat]
            deadline = _last_day(p, days)
            rule = "short-window-exception"
            out["window_days"] = days
            out["exception_note"] = ("this window is NOT replaced by "
                                     "the holiday extension "
                                     "(bestbuy.com table)")
            out["counting_convention"] = _convention(rn, days,
                                                     published=True)
        # ---- 2. exclusions d'extension (applecare : contrat tiers)
        elif rn == "bestbuy" and cat in \
                row["excluded_from_extension"]:
            if dd is None:
                raise ReturnDeadError(
                    "delivery_date", "this item is excluded from the "
                    "holiday table (third-party contract); its "
                    "standard 15-day window counts from delivery",
                    "ISO delivery date")
            deadline = _last_day(dd, 15)
            rule = "standard-window-excluded-item"
            out["counting_convention"] = _convention(rn, 15,
                                                     published=True)
        elif cat in ("protection_plan",) and rn in ("walmart",
                                                    "bestbuy"):
            std = row["standard"]
            basis = dd if std["basis"] == "delivery" else p
            if dd is None and std["basis"] == "delivery":
                raise ReturnDeadError(
                    "delivery_date", "%s lists protection plans as "
                    "excluded from the extension, on their shorter "
                    "standard rule — which counts from %s; absent "
                    "is not zero" % (rn, std["basis"]),
                    "ISO delivery date")
            deadline = _last_day(basis, std["days"])
            rule = "standard-window-excluded-category"
            out["counting_convention"] = _convention(rn, std["days"],
                     published=(rn == "bestbuy"))
        # ---- 3. exceptions à date dure (apple/beats/phone)
        elif cat in row["exceptions"]:
            exc = row["exceptions"][cat]
            if not (row["window"][0] <= _iso(p) <= row["window"][1]):
                # hors fenêtre d'extension : la ligne d'exception ne
                # s'applique pas ; standard si daté, sinon refus.
                if rn == "target":
                    raise ReturnDeadError(
                        "purchase_date",
                        "the %s holiday line only covers purchases "
                        "inside %s..%s; outside it, %s" % (
                            cat, row["window"][0], row["window"][1],
                            row["standard_without_date"]),
                        "purchase_date on or before %s"
                        % (row["window"][1],))
                if row["standard"]["basis"] == "delivery":
                    if dd is None:
                        raise ReturnDeadError(
                            "delivery_date",
                            "purchase is outside the extension "
                            "window; the standard rule counts from "
                            "delivery — missing_delivery_date",
                            "ISO delivery date")
                    deadline = _last_day(dd, row["standard"]["days"])
                    rule = "standard-window"
                    out["counting_convention"] = _convention(
                        rn, row["standard"]["days"], published=
                        (rn == "bestbuy"))
                else:
                    deadline = _last_day(p, row["standard"]["days"])
                    rule = "standard-window"
                    out["counting_convention"] = _convention(
                        rn, row["standard"]["days"],
                        published=False)
            else:
                deadline = _d(exc[0], "purchase_date")
                rule = "holiday-exception"
                out["exception_line"] = exc[1]
        # ---- 4. l'extension de saison elle-même
        else:
            win = row["window"]
            in_window = win[0] <= _iso(p) <= win[1]
            ext_for = row.get("extension_for")
            target_cat_gate = (rn == "target" and
                               isinstance(ext_for, list) and
                               cat in ext_for)
            if rn == "target" and cat in ("electronics",
                                          "entertainment",
                                          "target_plus") \
                    and not in_window:
                raise ReturnDeadError(
                    "purchase_date",
                    "Target's extension closed %s: a %s purchase of "
                    "%s is not in it, and %s. The shared press "
                    "headline 'until January 31' covers OTHER "
                    "retailers — named refusal beats a borrowed "
                    "deadline." % (win[1], cat, _iso(p),
                                   row["standard_without_date"]),
                    "purchase on or before %s, or category=general"
                    % (win[1],))
            if in_window and (rn != "target" or target_cat_gate):
                if rn == "bestbuy" and channel == "marketplace":
                    std = row["standard"]
                    if dd is None:
                        raise ReturnDeadError(
                            "delivery_date", "Marketplace purchases "
                            "keep the STANDARD policy (bestbuy.com, "
                            "verbatim): extended timeframes do not "
                            "apply; the standard 15 days counts from "
                            "delivery", "ISO delivery date")
                    deadline = _last_day(dd, std["days"])
                    rule = "marketplace-standard-policy"
                    out["counting_convention"] = _convention(
                        rn, std["days"], published=True)
                elif rn == "bestbuy" and membership:
                    mr = row["member_rule"]
                    if _iso(p) <= mr["hard_until"][0]:
                        deadline = _d(mr["hard_until"][1],
                                      "purchase_date")
                        rule = "holiday-extension-member-hard"
                    else:
                        deadline = _last_day(p, mr["rolling_days"])
                        rule = "holiday-extension-member-rolling"
                        out["counting_convention"] = _convention(
                            rn, mr["rolling_days"], published=True)
                    out["member_rule"] = mr["note"]
                else:
                    deadline = _d(row["extension"], "purchase_date")
                    rule = "holiday-extension"
                    if key_country == "UK":
                        lat = row["extension_later_of"]
                        if dd is None:
                            raise ReturnDeadError(
                                "delivery_date", "Amazon UK: 'until "
                                "31 January 2027 OR within 30 days "
                                "of delivery, whichever is later' — "
                                "the comparison needs the delivery "
                                "date; absent is not zero",
                                "ISO delivery date")
                        alt = _last_day(dd, lat["days"])
                        if alt > deadline:
                            deadline = alt
                            rule = "holiday-extension-later-of"
                            out["later_of"] = {
                                "fixed": row["extension"],
                                "delivery_plus_30": _iso(alt)}
                    if row["marketplace"] == "auto":
                        out["extension_applies"] = (
                            "auto — FBA and FBM alike (Seller "
                            "Central, verbatim)")
                    elif row["marketplace"] == "optin" and \
                            channel == "marketplace":
                        out["extension_applies"] = \
                            "unknown-for-seller"
                        out["named_condition"] = (
                            "marketplace sellers MAY opt in but are "
                            "not automatic (sacbee/parcelmonitor/cbs "
                            "concordant): the deadline above is the "
                            "first-party promise, the seller's "
                            "opt-in is outside this table")
            else:
                std = row["standard"]
                days = std["days"]
                if rn == "bestbuy" and membership:
                    days = row["member_standard_days"]
                basis_date = dd if std["basis"] == "delivery" else p
                if dd is None and std["basis"] == "delivery":
                    raise ReturnDeadError(
                        "delivery_date", "purchase is outside the "
                        "extension window; the standard %s rule for "
                        "%s counts from DELIVERY (published) — "
                        "missing_delivery_date" % (days, rn),
                        "ISO delivery date")
                deadline = _last_day(basis_date, days)
                rule = "standard-window"
                out["counting_convention"] = _convention(
                    rn, days, published=False)
                out["standard_basis"] = std["note"]
                if rn == "target":
                    out["extension_note"] = (
                        "general purchases never join Target's "
                        "extension — the typical 90-day clock is the "
                        "published rule for them (cbs)")

    out["rule_applied"] = rule
    out["return_by"] = _iso(deadline)
    out["return_by_weekday"] = _wd(deadline)
    if as_of is not None:
        a = _d(as_of, "as_of")
        out["as_of"] = _iso(a)
        out["days_left"] = (deadline - a).days
    return out

def _convention(rn, days, published):
    base = ("Day-1 convention: last day = basis + %d days"
            % (days - 1))
    if published:
        return base + " — PUBLISHED by bestbuy.com ('Day 1 is the " \
            "date the customer acquires the product')"
    return base + " — the convention is applied uniformly; only " \
        "Best Buy publishes it, %s does not — named, never hidden " \
        "in an off-by-one" % rn
