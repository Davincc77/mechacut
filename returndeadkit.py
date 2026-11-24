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

EXTENSION FRANCE (24-nov-2026, bundle98) — les pages OFFICIELLES
FR ont été REJOUÉES verbatim, pas la presse : fnac.com et darty.com
publient la même clause « prolongés jusqu'au 15 janvier 2027… hors
marketplace, gros électroménager et TV » ; boulanger.com publie sa
fenêtre OCT 30→DÉC 27 et le module panier du MÊME site écrit « 27
décembre 2027 » — coquille officielle, CONFLIT NOMMÉ ; dell.com/fr-fr
publie la grammaire later-of en français (« 15 janvier 2027 OU 30
jours à compter de la date de livraison, la date la plus tardive des
deux prévalant ») ; amazon.fr publie fenêtre déc-25 + later-of
janv-31/livr+30 ET un deuxième régime « 15 janv/livr+14 pour CERTAINS
produits » attaché PAR PRODUIT au widget de la fiche — non
énumérable en table, condition NOMMÉE. Apple direct entre avec sa
grammaire nouvelle : la fenêtre se joue sur les articles REÇUS
(« received between November 6 and December 25 » — verbatim
apple.com ; la page FR dit « reçus entre le 6 novembre et le 25
décembre », jusqu'au 8 janvier INCLUS). Cdiscount reste REFUSÉ par
nom : la date du 8 janvier est presse-concordante, la FENÊTRE d'achat
n'est connue que d'un agrégateur de coupons — une date sans sa
fenêtre n'est pas une deadline.

CONTRAT : retailer + purchase_date (ISO, saison 2026 seule jouée)
+ pays US|UK|FR (même marque, trois contrats : la fenêtre Amazon
ferme Dec 31 aux US, Dec 25 au UK et en FR avec un « whichever is
later » qui EXIGE delivery_date) + category dans un vocabulaire
FERMÉ + delivery_date quand la règle court depuis la LIVRAISON ou
de la RÉCEPTION (absent ≠ zéro : refus nommé) + membership (bestbuy
seulement — ailleurs il n'existe pas de ligne datée publiée) +
channel + as_of optionnel pour days_left.

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

TABLE_VERSION = "2026-11-24"
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
        "later_of_label": "Amazon UK",
        "later_of_quote": ("'until 31 January 2027 OR within 30 "
                           "days of delivery, whichever is later'"),
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
    # ---------------------------------------------------------- FR
    # bundle98 — pages officielles FR REJOUÉES verbatim 24-nov-2026.
    ("FR", "fnac"): {
        "window": ("2026-11-01", "2026-12-31"),
        "extension": "2027-01-15",
        "extension_for": "most products",
        "exceptions": {},
        "standard": {"days": 15, "basis": "dual",
                     "note": "« 15 jours à partir de la date d'achat "
                             "ou de réception » — la DOUBLE BASE est "
                             "publiée en verbatim (fnac.com) : le "
                             "choix de la base appliquée voyage dans "
                             "basis_note, jamais implicite"},
        "marketplace": "refused",
        "marketplace_note": ("la clause publiée exclut NOMMEMENT "
                             "« produits achetés sur la marketplace » "
                             "(fnac.com verbatim) — la politique du "
                             "vendeur tiers n'est pas dans cette "
                             "table : aucun délai prêté"),
        "extension_caveat": ("la prolongation exclut « gros "
                             "électroménager et TV » (verbatim) : si "
                             "l'article est un téléviseur ou un "
                             "gros électroménager, la date au-dessus "
                             "NE s'applique PAS — 'electronics' route "
                             "des deux côtés de la ligne publiée"),
        "provenance": [_P],
        "sources": ["fnac.com/retour-produit — « Les retours sont "
                    "prolongés jusqu'au 15 janvier 2027 — tout achat "
                    "effectué à la Fnac entre le 1er novembre et le "
                    "31 décembre 2026, hors produits achetés sur la "
                    "marketplace, gros électroménager et TV » "
                    "(verbatim, relu 24-nov-2026)",
                    "fnac.com/livraison-pour-noel + article "
                    "reassurance API — même clause verbatim",
                    "dealotronic.com 17-nov-2026 (« conditions "
                    "relevées sur les pages officielles », "
                    "concordant)"],
        "conflicts": [],
        "fees": ["en magasin, produit déballé non utilisé : décote "
                 "10 % ; déballé et utilisé : 20 % (fnac.com, "
                 "verbatim)"],
        "conditions": ["après la déclaration, 15 jours SUPPLÉMENTAIRES "
                       "pour renvoyer le colis ou déposer en magasin "
                       "(fnac.com verbatim)",
                       "retour en magasin gratuit, renvoi postal à "
                       "vos frais (fnac.com)"],
    },
    ("FR", "darty"): {
        "window": ("2026-11-01", "2026-12-31"),
        "extension": "2027-01-15",
        "extension_for": "most products",
        "exceptions": {},
        "standard": {"days": 15, "basis": "dual",
                     "note": "« 15 jours après réception » publié ; "
                             "double base achat/réception alignée "
                             "sur le groupe Fnac-Darty — la base "
                             "appliquée est NOMMÉE dans basis_note"},
        "marketplace": "refused",
        "marketplace_note": ("« à l'exception des produits gros "
                             "électroménager, téléviseurs et "
                             "Marketplace » (darty.com FAQ, "
                             "verbatim) — la procédure « ne "
                             "s'applique pas aux commandes "
                             "effectuées auprès de nos vendeurs "
                             "partenaires » (verbatim)"),
        "extension_caveat": ("exclus published : gros électroménager "
                             "et téléviseurs — darty.com définit le "
                             "volumineux VERBATIM : « les TV d'une "
                             "taille strictement supérieure à 43\" "
                             "(109 cm) sont considérées comme des "
                             "produits volumineux » + liste "
                             "lave-linge/sèche-linge/lave-vaisselle/"
                             "four/réfrigérateur… ; si l'article est "
                             "l'un d'eux, la date au-dessus NE "
                             "s'applique PAS"),
        "provenance": [_P],
        "sources": ["darty.com/services/aide/retour-retractation — "
                    "« Les retours sont prolongés jusqu'au 15 "
                    "janvier 2027 Pour tout achat effectué chez "
                    "Darty entre le 1er novembre et le 31 décembre "
                    "2026 Hors produits achetés sur la marketplace, "
                    "gros électroménager et TV » (verbatim)",
                    "darty.com foire aux questions — « achats "
                    "réalisés en magasin et sur notre site (y "
                    "compris Seconde vie) » (verbatim)",
                    "lefigaro 22-nov + dealotronic 17-nov "
                    "(concordants)"],
        "conflicts": [],
        "fees": ["changement d'avis par voie postale : retour à vos "
                 "frais (darty.com, verbatim)"],
        "conditions": ["la clause couvre magasin + site + Seconde "
                       "vie (FAQ verbatim)",
                       "produits hygiène/dermato descellés non "
                       "repris (liste verbatim darty.com)"],
    },
    ("FR", "boulanger"): {
        "window": ("2026-10-30", "2026-12-27"),
        "extension": "2027-01-31",
        "extension_for": "most products",
        "exceptions": {},
        "standard": None,
        "standard_without_date": ("hors de la fenêtre publiée "
                                  "30-octobre→27-décembre, l'horloge "
                                  "standard Boulanger n'est PAS "
                                  "datée en base commune dans nos "
                                  "≥2 sources (le titre « Retour "
                                  "sous 15 jours » ne dit ni depuis "
                                  "quoi) — refus nommé, pas de "
                                  "délai prêté"),
        "marketplace": "refused",
        "marketplace_note": ("« Hors produits vendus sur la "
                             "marketplace » (boulanger.com, "
                             "verbatim) — la politique du vendeur "
                             "tiers n'est pas dans cette table"),
        "provenance": [_P],
        "sources": ["boulanger.com/evenement/retourner-produit — "
                    "note officielle : « Le délai de retour est "
                    "prolongé jusqu'au 31 janvier 2027 pour vos "
                    "achats effectués entre le 30 octobre 2026 et "
                    "le 27 décembre 2026 sur boulanger.com et en "
                    "magasin. Hors produits vendus sur la "
                    "marketplace. » (verbatim)",
                    "boulanger.com modules panier/connexion + "
                    "avant-première Black Friday (même clause)"],
        "conflicts": ["le MÊME site publie deux fins de fenêtre : "
                      "la note légale de la page retour dit « 27 "
                      "décembre 2026 », le module panier/connexion "
                      "écrit « le 27 décembre 2027 » — coquille "
                      "officielle NOMMÉE ; c'est la note de la "
                      "clause elle-même (2026) qui fait foi, et "
                      "c'est la SEULE fenêtre compatible avec une "
                      "deadline du 31 janvier : jamais moyenné"],
        "fees": [],
        "conditions": ["« nous nous engageons à vous rembourser tout "
                       "produit non déballé, ou à vous échanger tout "
                       "produit ouvert et retourné complet dans son "
                       "emballage d'origine » (verbatim) — l'état du "
                       "produit décide remboursement vs échange",
                       "fenêtre d'achat DIFFÉRENTE des autres FR : "
                       "oct 30→déc 27, pas nov 1→déc 31 — un achat "
                       "du 28 décembre n'est PAS dans l'extension"],
    },
    ("FR", "dell"): {
        "window": ("2026-11-01", "2026-12-29"),
        "extension": "2027-01-15",
        "extension_later_of": {"days": 30, "basis": "delivery"},
        "later_of_label": "Dell France",
        "later_of_quote": ("« jusqu'au 15 janvier 2027 ou 30 jours à "
                           "compter de la date de livraison, la date "
                           "la plus tardive des deux prévalant »"),
        "extension_for": "PC, écrans d'ordinateur, accessoires PC",
        "exceptions": {},
        "standard": None,
        "standard_without_date": ("hors de la fenêtre publiée "
                                  "1er-novembre→29-décembre, "
                                  "l'horloge standard de retour "
                                  "dell.fr n'a pas été rejouée en "
                                  "≥2 sources ce cycle — refus "
                                  "nommé, pas de délai prêté"),
        "marketplace": "refused",
        "marketplace_note": ("la clause vise « les achats effectués "
                              "par les clients consommateurs entre "
                              "le 1 novembre 2026 et le 29 décembre "
                              "2026 SUR Dell.fr » (verbatim) — ni "
                              "marketplace tiers ni achat pro ne "
                              "sont dans la clause"),
        "extension_caveat": ("« Seuls les consommateurs sont "
                             "éligibles […] pour les PC, écrans "
                             "d'ordinateur et accessoires pour PC » "
                             "(verbatim) — un produit hors de cette "
                             "liste n'est PAS couvert par la ligne "
                             "des fêtes"),
        "caveat_always": True,
        "provenance": [_P],
        "sources": ["dell.com/fr-fr/learn/lp/holiday-shipping-and-"
                    "extended-returns (verbatim)",
                    "dell.com/fr-fr/shop/lp/return-policy (même "
                    "clause verbatim)",
                    "dell.com/fr-fr contact + terms-of-sale "
                    "(clause répétée verbatim — 4 pages officielles)"],
        "conflicts": ["la grammaire « la date la plus tardive des "
                      "deux prévalant » existe déjà côté Amazon UK — "
                      "même mécanisme, clause FR rejouée ; Dell ferme "
                      "sa fenêtre d'achat le 29-déc, deux jours avant "
                      "Fnac/Darty"],
        "fees": [],
        "conditions": ["« pour que vous ayez droit à un remboursement, "
                       "les produits doivent être dans un état « "
                       "neuf » ou « comme neuf » » (verbatim)",
                       "clients consommateurs seulement (pro = hors "
                       "ligne)"],
    },
    ("FR", "amazon"): {
        "window": ("2026-11-01", "2026-12-25"),
        "extension": "2027-01-31",
        "extension_later_of": {"days": 30, "basis": "delivery"},
        "later_of_label": "Amazon.fr",
        "later_of_quote": ("« jusqu'au 31 janvier 2027 ou dans les "
                           "30 jours suivant la réception (la date "
                           "la plus tardive prévalant) »"),
        "extension_for": "most products",
        "exceptions": {},
        "standard": {"days": 30, "basis": "delivery",
                     "note": "politique « retour sous 30 jours » des "
                             "produits éligibles vendus/expédiés par "
                             "Amazon, depuis la réception (cdn."
                             "amazon.fr, verbatim, en vigueur au "
                             "1er-octobre-2026)"},
        "marketplace": "auto",
        "extension_caveat": ("régime PAIR publié par amazon.fr : pour "
                             "« certains produits » des sites "
                             "DE/IT/FR le retour est limité au 15 "
                             "janvier 2027 ou 14 jours après "
                             "livraison (later-of) — la liste des "
                             "catégories n'existe PAS en table, elle "
                             "voyage PAR PRODUIT dans le widget « "
                             "Retours sous 30 jours et garanties "
                             "légales » sous le bouton Acheter ; si "
                             "la fiche de VOTRE article dit « "
                             "Retournable jusqu'au 15 janvier 2027 », "
                             "cette date prévaut sur celle calculée "
                             "au-dessus"),
        "caveat_always": True,
        "provenance": [_P],
        "sources": ["sellercentral.amazon.fr forum annonce officielle "
                    "(verbatim, FBA+FBM, 10 sites EU)",
                    "cdn.amazon.fr aide « À propos de nos politiques "
                    "de retour » (verbatim, saison 2026)",
                    "sellercentral-europe forum EN (même clause "
                    "verbatim)"],
        "conflicts": ["même marque TROIS contrats : Amazon US ferme "
                      "la fenêtre d'achat déc-31, Amazon UK et "
                      "Amazon.fr la ferment déc-25 ; seul l'US nomme "
                      "Apple en exception datée — la liste FR des "
                      "« certains produits » est publiée par fiche, "
                      "pas par catégorie : rien prêté d'un pays à "
                      "l'autre"],
        "fees": [],
        "conditions": ["la clause fêtes couvre FBA et FBM (verbatim "
                      "Seller Central) ; hors fêtes, les articles "
                      "expédiés par vendeur tiers relèvent de la "
                      "page Marketplace (verbatim page d'aide FR)",
                      "droit légal de rétractation 14 jours depuis "
                      "la réception, indépendant et antérieur à la "
                      "clause commerciale"],
    },
    # ------------------------------------------------- Apple direct
    ("US", "apple"): {
        "window": ("2026-11-06", "2026-12-25"),
        "window_basis": "delivery",
        "delivery_basis_refusal": ("Apple's holiday line keys on "
                                   "RECEIVED products — 'eligible "
                                   "products at the Apple Store "
                                   "Online that are received between "
                                   "November 6, 2026 and December "
                                   "25, 2026, may be returned "
                                   "through January 8, 2027' "
                                   "(apple.com, verbatim); the "
                                   "delivery date is the gate — "
                                   "absent is not zero"),
        "extension": "2027-01-08",
        "extension_for": "most eligible products",
        "exceptions": {},
        "standard": {"days": 14, "basis": "delivery",
                     "note": "14 calendar days from receipt "
                             "(apple.com, verbatim) — 'all purchases "
                             "made after December 25, 2026 are "
                             "subject to the Standard Return Policy'"},
        "eligibility_basis": ("fenêtre jouée sur la date de "
                              "RÉCEPTION (« received between… », "
                              "verbatim apple.com), pas sur la date "
                              "d'achat — grammaire unique dans "
                              "cette table"),
        "marketplace": "n/a",
        "provenance": [_P],
        "sources": ["apple.com/shop/help/returns_refund (verbatim "
                    "holiday clause, relu 24-nov-2026)",
                    "macrumors 6-nov-2026 « Apple's Extended Return "
                    "Policy Now in Effect » (concordant, multi-"
                    "pays)",
                    "newsobserver article318204164 — the 'hide a "
                    "catch' headline names the direct-Apple Jan 8 "
                    "deadline as the trap"],
        "conflicts": ["la presse publie une manchette « until "
                      "January 31 » pour la saison ; le RETOUR "
                      "APPLE DIRECT ferme 8 JANVIER et la fenêtre "
                      "se compte sur les articles REÇUS — deux "
                      "pièges séparés, nommés l'un et l'autre"],
        "fees": [],
        "conditions": ["carrier-financed iPhones (T-Mobile/Verizon) "
                       "and iPads (Verizon) are NOT eligible — "
                       "standard policy applies (apple.com, "
                       "verbatim)",
                       "policy applies to Apple Store online, "
                       "stores and the app (macrumors, concordant)"],
    },
    ("FR", "apple"): {
        "window": ("2026-11-06", "2026-12-25"),
        "window_basis": "delivery",
        "delivery_basis_refusal": ("la clause française joue sur les "
                                   "articles REÇUS : « reçus entre "
                                   "le 6 novembre 2026 et le 25 "
                                   "décembre 2026 » "
                                   "(apple.com/fr, verbatim) — la "
                                   "date de livraison est la porte, "
                                   "absente ≠ zéro"),
        "extension": "2027-01-08",
        "extension_for": "most eligible products",
        "exceptions": {},
        "standard": {"days": 14, "basis": "delivery",
                     "note": "« 14 jours à compter de la date de "
                             "livraison » (apple.com/fr, verbatim)"},
        "eligibility_basis": ("fenêtre jouée sur la date de "
                              "RÉCEPTION (« reçus entre le 6 "
                              "novembre et le 25 décembre », "
                              "verbatim) — grammaire unique dans "
                              "cette table"),
        "marketplace": "n/a",
        "provenance": [_P],
        "sources": ["apple.com/fr/shop/help/returns_refund — « Vous "
                    "avez jusqu'au 8 janvier 2027 inclus pour "
                    "retourner les articles éligibles achetés sur "
                    "l'Apple Store en ligne et reçus entre le 6 "
                    "novembre 2026 et le 25 décembre 2026 » "
                    "(verbatim, relu 24-nov-2026)",
                    "macrumors 6-nov-2026 (table multi-pays, "
                    "concordante)"],
        "conflicts": ["le verbatim français dit « achetés… et "
                      "reçus entre le 6 novembre et le 25 décembre » "
                      "— la clause nomme DEUX dates ; c'est la "
                      "RÉCEPTION qui ouvre la fenêtre (même lecture "
                      "que la page EN), l'achat hors fenêtre ne "
                      "l'ouvre pas : NOMMÉ, jamais moyenné"],
        "fees": [],
        "conditions": ["« les achats effectués à l'aide de l'option "
                       "de financement pour les particuliers ne "
                       "sont pas éligibles » (verbatim)",
                       "logiciels : reprise seulement si "
                       "non-descellés (apple.com/fr, verbatim)"],
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

COUNTRIES = ("US", "UK", "FR")

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

_UK_NOT_REPLAYED = {
    "apple": "the macrumors 6-nov multi-country table DOES list the "
             "UK store in the January 8 bucket, but the apple.com/uk "
             "page has not been replayed this cycle — borrowing a "
             "deadline across countries is exactly the mistake the "
             "FR/UK/US Amazon rows exist to name",
}

_PRESS_ONLY_FR = {
    "cdiscount": "la date du 8 janvier 2027 est porte PAR DEUX "
                 "presses concordantes (leconseilmalin, labomaison) "
                 "— MAIS la FENÊTRE d'achat (1er-nov→24-dec) n'est "
                 "connue que d'un agrégateur de coupons (bon-reduc) "
                 "et aucune page officielle cdiscount.com n'a été "
                 "rejouée : une date sans sa fenêtre n'est pas une "
                 "deadline — fait candidat porté ici, refus NOMMÉ",
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
    "amazon.fr": "amazon", "amazon fr": "amazon",
    "walmart": "walmart", "walmart.com": "walmart",
    "target": "target", "target.com": "target",
    "best buy": "bestbuy", "bestbuy": "bestbuy", "best_buy":
    "bestbuy", "best buy official": "bestbuy",
    "costco": "costco", "costco.com": "costco",
    "fnac": "fnac", "fnac.com": "fnac",
    "darty": "darty", "darty.com": "darty",
    "boulanger": "boulanger", "boulanger.com": "boulanger",
    "dell": "dell", "dell.fr": "dell", "dell.com": "dell",
    "apple": "apple", "apple.com": "apple",
    "apple store": "apple", "applestore": "apple",
    "the apple store": "apple",
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
            "country", "no crossed table for %r — this table is US, "
            "UK and FR only; a promise on a market without >=2 "
            "concordant published sources would be a false one"
            % (key_country,), "US | UK | FR")
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
        if key_country == "FR" and slug in _PRESS_ONLY_FR:
            raise ReturnDeadError(
                "retailer", "%s: %s" % (retailer,
                                        _PRESS_ONLY_FR[slug]),
                "fnac | darty | boulanger | dell | amazon | apple "
                "(FR)")
        raise ReturnDeadError(
            "retailer", "not in the 2026-2027 table: %r.%s" % (
                retailer, _KNOWN_REFUSAL_EXTRA),
            "amazon | walmart | target | bestbuy | costco (US), "
            "amazon (UK), fnac | darty | boulanger | dell | "
            "amazon | apple (FR)")
    if (key_country, rn) not in RETAILERS:
        if rn in _UK_NOT_REPLAYED and key_country == "UK":
            raise ReturnDeadError(
                "retailer", "%s: %s" % (retailer,
                                        _UK_NOT_REPLAYED[rn]),
                "amazon (UK); apple: US and FR only this season")
        raise ReturnDeadError(
            "retailer", "not in the 2026-2027 table for %s: %r" % (
                key_country, retailer),
                "see /agent/manifest — shop_return_deadline")
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

        # ---- 0. FR (bundle98) : la clause publie l'exclusion
        #         MARKETPLACE EN DUR (« hors marketplace ») — un
        #         achat vendeur tiers ne reçoit AUCUNE date prêtée.
        if row.get("marketplace") == "refused" and \
                channel == "marketplace":
            raise ReturnDeadError("channel",
                                  row["marketplace_note"],
                                  "first_party")

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
            wb = row.get("window_basis", "purchase")
            if wb == "delivery":
                if dd is None:
                    raise ReturnDeadError(
                        "delivery_date",
                        row["delivery_basis_refusal"],
                        "ISO delivery date")
                gate = dd
            else:
                gate = p
            in_window = win[0] <= _iso(gate) <= win[1]
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
                    lat = row.get("extension_later_of")
                    if lat:
                        if dd is None:
                            raise ReturnDeadError(
                                "delivery_date",
                                "%s: %s — the comparison needs "
                                "the delivery date; absent is not "
                                "zero" % (row["later_of_label"],
                                          row["later_of_quote"]),
                                "ISO delivery date")
                        alt = _last_day(dd, lat["days"])
                        if alt > deadline:
                            deadline = alt
                            rule = "holiday-extension-later-of"
                            out["later_of"] = {
                                "fixed": row["extension"],
                                "delivery_plus_%d" % lat["days"]:
                                    _iso(alt)}
                    if wb == "delivery":
                        out["eligibility_basis"] = row[
                            "eligibility_basis"]
                    cav = row.get("extension_caveat")
                    if cav and (row.get("caveat_always") or
                                cat == "electronics"):
                        out["named_condition"] = cav
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
                std = row.get("standard")
                if std is None:
                    raise ReturnDeadError(
                        "purchase_date",
                        row["standard_without_date"],
                        "purchase_date inside %s..%s for the "
                        "holiday date" % (win[0], win[1]))
                days = std["days"]
                if rn == "bestbuy" and membership:
                    days = row["member_standard_days"]
                if std["basis"] == "dual":
                    basis_date = dd if dd is not None else p
                    out["basis_note"] = (
                        std["note"] + " — APPLIED: " + (
                            "réception/livraison (delivery_date "
                            "given)" if dd is not None else
                            "date d'achat (no delivery_date "
                            "given)"))
                else:
                    basis_date = dd if std["basis"] == "delivery" \
                        else p
                    if dd is None and std["basis"] == "delivery":
                        raise ReturnDeadError(
                            "delivery_date", "purchase is outside "
                            "the extension window; the standard "
                            "%s rule for %s counts from DELIVERY "
                            "(published) — missing_delivery_date" %
                            (days, rn),
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
