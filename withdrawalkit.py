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
pas de droit en MAGASIN (HORS L221-18, refusé par nom), pas de BR/UK
(CDC art. 49 = sept jours, CCA 2015 — non rejoués, refusés par nom),
aucun fetch, aucune horloge murale : as_of est un ARGUMENT.

LA DEUXIEME VENUE (b108, cycle du 25-11 au matin) — LU ET BE. Le
rang 1 publié la veille nommait les mauvais articles (mémoire, pas
rejeu) : le gate a corrigé deux fois. La rétractation luxembourgeoise
est L. 221-3 + L. 222-9 (l'ancienne numérotation 1251-19 a été
abrogée par la loi du 2 avril 2014) ; la belge est VI.47 à VI.53
(VI.25 est l'article des SOLDES — notre sœur soldes-be le joue déjà).
Et la DIVERGENCE que la file promettait est réelle, textuelle, et
tracée sur oracle g108 : le Luxembourg proroge une échéance qui
tombe un jour NON OUVRABLE — or « jour ouvrable » = tous les jours
sauf dimanches et jours fériés légaux (glossaire officiel
guichet.lu ; FAQ ITM D9a3, COTRAV L. 232-6) — le SAMEDI reste donc
un samedi, contre l'exemple exact de la France qui le nomme. La
Belgique, Livre VI silencieux (« expire un samedi » : zéro occurrence
relue à ejustice au navigateur réel), c'est le NOUVEAU CODE CIVIL
art. I.7 (loi du 28 avril 2022, relue verbatim) : départ le LENDEMAIN
de l'événement (§1), ouvrable = ni férié, ni dimanche, ni SAMEDI
(§3), échéance non ouvrable reportée au jour ouvrable suivant (§4) —
et §7 : cet article joue faute de disposition contraire, ce que le
Livre VI ne contient pas. Le report belge s'étend aux secondes
horloges (VI.50/VI.51 = prestation ou communication), pas au report
français L221-19 — divergence nommée en conditions. VI.53 ajoute la
QUATORZIEME classe belge que ni la France ni le Luxembourg n'ont :
paris et loteries. Les tables LU (11 jours, COTRAV L. 232-6 + loi du
25 avril 2019) et BE (10 jours, liste SPF Emploi) entrent AUSSI ce
cycle dans /schedule/holidays — la file affirmait qu'elles « existaient
déjà » : le gate a pêché qu'elles n'existaient pas ; elles sont bâties
ligne par ligne avec leur loi, et le vecteur LU 9-mai-2028 (Journée
de l'Europe, seul pays UE à la fêter, source luxembourg.public.lu)
prouve qu'elles voyagent.
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
    "only fr|be|lu are dated here: each is a REPLAYED statute (FR "
    "L221-18/28, LU L. 221-3 + L. 222-9, BE VI.47/53 + C. civ. I.7); "
    "the directive harmonises the fourteen days but NOT each state's "
    "counting grammar — Saturday advances in FR and BE, survives in "
    "LU, and the holiday tables differ per state. br refused by name: "
    "CDC art. 49 runs SEVEN days, another clock entirely; uk refused: "
    "CCA 2015, post-Brexit statute not replayed; every other state "
    "ships when sourced — calendars are law, not vibes")

_REFUSAL_IN_STORE = (
    "in_store refused by name carrying its statute: L221-18 opens "
    "the 14 days for contracts « conclus à distance, à la suite "
    "d'un démarchage téléphonique ou hors établissement » — a plain "
    "shop purchase is outside the article, so NO automatic legal "
    "right exists (BEE SECURE/CEC/ULC 24-Nov say the same words); "
    "the store's own window is a different clock: /shop/"
    "return-deadline")

_REFUSAL_IN_STORE_LU = (
    "in_store refused by name: L. 221-3 and L. 222-9 open the right "
    "for contrats à distance et hors établissement only — a shop "
    "purchase carries NO automatic right, the same words BEE SECURE, "
    "CEC and ULC published 24-Nov; the store's voluntary window is a "
    "different clock: /shop/return-deadline")

_REFUSAL_IN_STORE_BE = (
    "in_store refused by name: VI.47 (vente à distance) and VI.67 "
    "(contrat hors établissement) close the circle — a plain shop "
    "sale enters neither, so NO automatic right (guide SPF Économie, "
    "rejoué 25-Nov); the store's own window: /shop/return-deadline")


# ------------------------------------------------ LU : L. 221-3 +
# L. 222-9 (legilux consolidé 20251125, rejoué verbatim 25-11-2026)
LU_START = {
    "goods": ("L. 222-9 (2) b)", "Du jour où le consommateur ou un "
        "tiers autre que le transporteur et désigné par le "
        "consommateur prend physiquement possession du bien — biens "
        "multiples d'une seule commande livrés séparément : possession "
        "du DERNIER bien ; bien composé de lots ou pièces : DERNIER "
        "lot ou pièce (b) i et ii verbatim)"),
    "services": ("L. 222-9 (2) a)", "En ce qui concerne les contrats "
        "de service, du jour de la conclusion du contrat (verbatim) ; "
        "eau, gaz, électricité non conditionnés, chauffage urbain et "
        "contenu numérique sans support : (2) c), conclusion aussi"),
    "off_premises": ("L. 222-9 (1) + (2)", "Le Luxembourg rend UN "
        "seul tableau pour le contrat à distance ET le contrat hors "
        "établissement (L. 222-9 (1) les nomme ensemble) — pas "
        "d'alinéa « à compter de la conclusion » séparé comme en "
        "France : le départ suit la nature, possession pour la vente"),
    "subscriptions": ("L. 222-9 (2) b) iii)", "Contrats portant sur "
        "la livraison régulière de biens pendant une période de "
        "temps définie : du jour où le consommateur prend "
        "physiquement possession du PREMIER bien (verbatim)"),
}

LU_CLOCK = (
    "« Pour tout contrat visé par les chapitres 2 à 4 du présent "
    "titre, le consommateur a le droit de se rétracter par écrit ou "
    "sur tout autre support durable, sans indication de motif et "
    "sans pénalité, dans un délai de quatorze jours calendrier. Si "
    "le dernier jour du délai n'est pas un jour ouvrable, le délai "
    "est prorogé jusqu'au premier jour ouvrable suivant. » (Code de "
    "la consommation, art. L. 221-3 (1), loi du 2 avril 2014) — "
    "« jour ouvrable » : le Code ne le définit PAS ; le glossaire "
    "OFFICIEL guichet.lu (« en règle générale, ce sont les jours du "
    "calendrier, sauf les dimanches et les jours fériés légaux ») "
    "et la FAQ ITM D9a3 (« du lundi au samedi ») le rendent : LE "
    "SAMEDI EST OUVRABLE, la prorogation ne joue que dimanche et "
    "jours fériés légaux (COTRAV L. 232-6, 11 jours)")

# les treize classes L. 222-9 (7), verbatim legilux — memes clés
# fermées que la France, lettres luxembourgeoises
LU_EXCEPTIONS = {
    "service_executed": ("a)", "de fourniture de services après que "
        "le service a été pleinement exécuté mais, si le contrat "
        "soumet le consommateur à une obligation de payer, seulement "
        "si l'exécution a commencé avec l'accord préalable exprès du "
        "consommateur, et à condition qu'il ait également reconnu "
        "qu'il perdra son droit de rétractation une fois que le "
        "contrat aura été pleinement exécuté par le professionnel",
        "les trois conditions voyagent ensemble : exécution + accord "
        "préalable exprès + reconnaissance de la perte (loi du "
        "30 novembre 2022)"),
    "financial_market": ("b)", "de fourniture de biens ou de services "
        "dont le prix est fonction des fluctuations sur le marché "
        "financier, échappant au contrôle du professionnel et "
        "susceptibles de se produire pendant le délai de rétractation",
        "la clause française dit « dépendent », la clause luxembourgeoise « est fonction » — meme classe, meme effet"),
    "made_to_order": ("c)", "de fourniture de biens confectionnés "
        "selon les spécifications du consommateur ou nettement "
        "personnalisés", "frontiere identique a la France : la couleur ou la finition dans une gamme standard ne suffisent pas"),
    "perishable": ("d)", "de fourniture de biens qui sont susceptibles "
        "de se détériorer ou de se périmer rapidement", ""),
    "unsealed_hygiene": ("e)", "de fourniture de biens scellés ne "
        "pouvant être renvoyés pour des raisons de protection de la "
        "santé ou d'hygiène et qui ont été descellés par le "
        "consommateur après la livraison", "scellé PUIS descellé — l'exception se lit dans l'ordre"),
    "inseparable_mix": ("f)", "de fourniture de biens qui, après "
        "avoir été livrés, et de par leur nature, sont mélangés de "
        "manière indissociable avec d'autres articles", ""),
    "alcohol_delayed": ("g)", "de fourniture de boissons alcoolisées "
        "dont le prix a été convenu au moment de la conclusion du "
        "contrat de vente, dont la livraison ne peut être effectuée "
        "qu'après trente jours et dont la valeur réelle dépend de "
        "fluctuations sur le marché échappant au contrôle du "
        "professionnel", "les DEUX conditions : différé > 30 jours ET valeur liée au marché"),
    "urgent_home_repair": ("h)", "dans lesquels le consommateur a "
        "expressément demandé au professionnel de lui rendre visite "
        "afin d'effectuer des travaux urgents d'entretien ou de "
        "réparation. Si, toutefois, à l'occasion de cette visite, le "
        "professionnel fournit des services venant s'ajouter à ceux "
        "spécifiquement requis par le consommateur ou des biens "
        "autres que les pièces de rechange indispensables aux "
        "travaux d'entretien ou de réparation, le droit de "
        "rétractation s'applique à ces services ou biens "
        "supplémentaires", "la limite est dans la clause : l'urgence seulement, et les ajouts restent rétractables"),
    "unsealed_media": ("i)", "de fourniture d'enregistrements audio "
        "ou vidéo scellés ou de logiciels informatiques scellés et "
        "qui ont été descellés par le consommateur après la "
        "livraison", ""),
    "press_daily": ("j)", "de fourniture de journaux, de périodiques "
        "et de magazines sauf pour les contrats d'abonnement à ces "
        "publications", "le « sauf » est dans la clause : l'ABONNEMENT reste rétractable"),
    "public_auction": ("k)", "de ventes conclus lors d'enchères "
        "publiques", "l'enchère publique seulement"),
    "dated_services": ("l)", "de fourniture de services d'hébergement "
        "(autres qu'à des fins résidentielles), de transport de "
        "biens, de location de voitures, de restauration, ou liés à "
        "des activités de loisirs, si le contrat prévoit une date ou "
        "une période d'exécution spécifique", ""),
    "digital_started": ("m)", "de fourniture d'un contenu numérique "
        "non fourni sur un support matériel si l'exécution a "
        "commencé avec l'accord préalable exprès du consommateur, et "
        "à condition que le contrat soumet le consommateur à une "
        "obligation de payer, si : (i) il a donné son consentement "
        "préalable exprès pour que l'exécution commence pendant le "
        "délai de rétractation ; (ii) il a reconnu qu'il perdra "
        "ainsi son droit de rétractation ; et (iii) le professionnel "
        "a fourni une confirmation conformément à l'article L. 222-7, "
        "paragraphe (2), ou à l'article L. 222-5",
        "les trois maillons, modifiés par la loi du 30 novembre 2022"),
}

# ------------------------------------------------ BE : VI.47-VI.53
# + VI.67 (ejustice, loi du 21 décembre 2013, insérés en vigueur
# 31-05-2014 ; VI.53 modifié par la loi du 8 mai 2022) + NOUVEAU
# CODE CIVIL art. I.7 (loi du 28 avril 2022, Moniteur belge 01-07-
# 2022) — tout rejoué VERBATIM le 25-11-2026.
BE_START = {
    "goods": ("VI.47 § 2 2°", "Du jour où le consommateur ou un "
        "tiers autre que le transporteur et désigné par le "
        "consommateur prend physiquement possession du bien — biens "
        "multiples d'une seule commande livrés séparément : DERNIER "
        "bien (a) ; lots ou pièces : DERNIER lot ou pièce (b) ; "
        "livraison régulière : PREMIER bien (c) (verbatim))"),
    "services": ("VI.47 § 2 1°", "En ce qui concerne les contrats "
        "de service, du jour de la conclusion du contrat (verbatim) ; "
        "eau, gaz, électricité non conditionnés, chauffage urbain : "
        "3°, conclusion"),
    "off_premises": ("VI.67 § 2", "Le contrat HORS ÉTABLISSEMENT a "
        "son propre article belge (VI.67, chapitre 3) qui rend la "
        "MEME table de départs que la vente à distance — possession "
        "du bien, conclusion du service (verbatim § 2 1° et 2°))"),
    "subscriptions": ("VI.47 § 2 2° c)", "Dans le cas des contrats "
        "portant sur la livraison régulière de biens pendant une "
        "période de temps définie, du jour où le consommateur prend "
        "physiquement possession du PREMIER bien (verbatim)"),
}

BE_CLOCK = (
    "« Un délai exprimé en jours... commence à courir le lendemain "
    "de l'événement ou de l'acte qui lui donne naissance » (art. I.7 "
    "§ 1er) ; « Les jours ouvrables sont tous les jours autres que "
    "les jours fériés légaux, dimanches et samedis » (§ 3) ; « Si le "
    "dernier jour d'un délai exprimé autrement qu'en heures pour "
    "l'accomplissement d'une prestation ou d'une communication est un "
    "jour férié, un dimanche ou un samedi, le délai prend fin à "
    "l'expiration de la dernière heure du jour ouvrable suivant » "
    "(§ 4) ; § 7 : l'article joue « en l'absence de disposition "
    "légale... contraire » — le Livre VI n'en donne aucune pour le "
    "délai de rétractation (relé 25-11-2026 : « expire un samedi » = "
    "zéro occurrence dans le Livre VI). Base du délai : « délai de "
    "14 jours » VI.47 § 1er, guide SPF Économie : « 14 jours "
    "calendrier... à compter du LENDEMAIN du jour où le consommateur "
    "prend physiquement possession » (relu 25-11-2026). Fériés "
    "reportés = la liste belge de 10 jours (SPF Emploi) : le 21 "
    "juillet et le 11 novembre existent, le 8 mai et le 14 juillet "
    "français N'EXISTENT PAS, le 26 décembre luxembourgeois NON PLUS")

BE_EXCEPTIONS = {
    "service_executed": ("1°", "les contrats de service après que le "
        "service a été pleinement exécuté mais, si le contrat soumet "
        "le consommateur à une obligation de payer, seulement si "
        "l'exécution a commencé avec l'accord préalable exprès du "
        "consommateur et qu'il a reconnu qu'il perdra son droit de "
        "rétractation une fois que le contrat aura été pleinement "
        "exécuté par l'entreprise",
        "l'entreprise, pas le professionnel — le CDE parle « entreprise »"),
    "financial_market": ("2°", "la fourniture de biens ou de services "
        "dont le prix dépend de fluctuations sur le marché financier "
        "échappant au contrôle de l'entreprise et susceptibles de se "
        "produire pendant le délai de rétractation", ""),
    "made_to_order": ("3°", "la fourniture de biens confectionnés "
        "selon les spécifications du consommateur ou nettement "
        "personnalisés", ""),
    "perishable": ("4°", "la fourniture de biens susceptibles de se "
        "détériorer ou de se périmer rapidement", ""),
    "unsealed_hygiene": ("5°", "la fourniture de biens scellés ne "
        "pouvant être renvoyés pour des raisons de protection de la "
        "santé ou d'hygiène et qui ont été descellés par le "
        "consommateur après la livraison", ""),
    "inseparable_mix": ("6°", "la fourniture de biens qui, après "
        "avoir été livrés, et de par leur nature, sont mélangés de "
        "manière indissociable avec d'autres articles", ""),
    "alcohol_delayed": ("7°", "la fourniture de boissons alcoolisées "
        "dont le prix a été convenu au moment de la conclusion du "
        "contrat de vente, dont la livraison ne peut être effectuée "
        "qu'après trente jours et dont la valeur réelle dépend de "
        "fluctuations sur le marché échappant au contrôle de "
        "l'entreprise", ""),
    "urgent_home_repair": ("8°", "les contrats dans lesquels le "
        "consommateur a expressément demandé à l'entreprise de lui "
        "rendre visite afin d'effectuer des travaux urgents "
        "d'entretien ou de réparation. Si, à l'occasion de cette "
        "visite, l'entreprise fournit des services venant s'ajouter à "
        "ceux spécifiquement requis par le consommateur ou des biens "
        "autres que les pièces de rechange indispensables aux "
        "travaux d'entretien ou de réparation, le droit de "
        "rétractation s'applique à ces services ou biens "
        "supplémentaires", ""),
    "unsealed_media": ("9°", "la fourniture d'enregistrements audio "
        "ou vidéo scellés ou de logiciels informatiques scellés et "
        "qui ont été descellés après livraison", ""),
    "press_daily": ("10°", "la fourniture d'un journal, d'un "
        "périodique ou d'un magazine sauf pour les contrats "
        "d'abonnement à ces publications", ""),
    "public_auction": ("11°", "les contrats conclus lors d'une "
        "enchère publique", ""),
    "dated_services": ("12°", "la prestation de services "
        "d'hébergement autres qu'à des fins résidentielles, de "
        "transport, de location de voitures, de restauration ou de "
        "services liés à des activités de loisirs si le contrat "
        "prévoit une date ou une période d'exécution spécifique", ""),
    "digital_started": ("13°", "les contrats de fourniture de "
        "contenus numériques non fournis sur un support matériel, si "
        "l'exécution a commencé et, si le contrat soumet le "
        "consommateur à une obligation de payer, lorsque : a) il a "
        "donné son consentement préalable exprès pour que l'exécution "
        "commence pendant le délai de rétractation ; b) il a reconnu "
        "qu'il perdra ainsi son droit de rétractation ; et c) "
        "l'entreprise a fourni une confirmation conformément à "
        "l'article VI.46, § 7", ""),
    "betting_lottery": ("14°", "les contrats de services de paris et "
        "de loteries", "LA QUATORZIEME — propre à la Belgique : ni "
        "les treize françaises (L221-28) ni les treize luxembourgeoises "
        "(L. 222-9 (7)) ne la contiennent (VI.53 modifié par la loi "
        "du 8 mai 2022, en vigueur 28-05-2022)"),
}

# grammaires closes par pays : depart, horloge, articles de chaque
# horloge, classements d'exceptions, regle d'avancement
COUNTRIES = {
    "fr": {
        "label": "FR", "holidays": "FR",
        "start": START_RULES, "clock_article": "L221-19",
        "clock_anchor": "règlement (CEE) n° 1182/71 du Conseil, "
            "3 juin 1971 — cité par l'article",
        "clock_text": CLOCK_L221_19,
        "deadline_source": "L221-18 + L221-19",
        "ext_article": "L221-20 al. 1 (douze mois)",
        "restart_article": "L221-20 al. 2",
        "exceptions": EXCEPTIONS,
        "exception_article": "L221-28 %d°",
        "advance": ("sat", "sun", "hol"),
        "second_advance": False,
        "second_clock": ("L221-23 (renvoi)", "L221-24 (remboursement)"),
        "in_store": _REFUSAL_IN_STORE,
        "law_code": "Code de la consommation (FR), section 6",
        "ext_short": "L221-20 al. 1", "restart_label": "L221-20 al. 2",
        "restart_short": "al. 2",
        "kind_message": "kind outside the closed set — the four "
            "contract families L221-18 names its own start for",
        "pc_count": "thirteen", "pc_name": "L221-28",
    },
    "lu": {
        "label": "LU", "holidays": "LU",
        "start": LU_START,
        "clock_article": "L. 221-3 (1) + L. 222-9",
        "clock_anchor": "directive 2011/83/UE art. 9 (2) — quatorze "
            "jours calendaires ; « jour ouvrable » rendu par le "
            "glossaire officiel guichet.lu et la FAQ ITM D9a3",
        "clock_text": LU_CLOCK,
        "deadline_source": "L. 221-3 (1) + L. 222-9 (2)",
        "ext_article": "L. 222-9 (3) (douze mois)",
        "restart_article": "L. 222-9 (4)",
        "exceptions": LU_EXCEPTIONS,
        "exception_article": "L. 222-9 (7) %s",
        "advance": ("sun", "hol"),
        "second_advance": False,
        "second_clock": ("L. 222-10 (4) (renvoi)",
                         "L. 222-10 (1) (remboursement)"),
        "in_store": _REFUSAL_IN_STORE_LU,
        "law_code": "Code de la consommation (LU), L. 221-3 et "
                    "L. 222-9 à L. 222-10",
        "ext_short": "L. 222-9 (3)", "restart_label": "L. 222-9 (4)",
        "restart_short": "(4)",
        "kind_message": "kind outside the closed set — the four "
            "contract families L. 222-9 (2) names its own start for",
        "pc_count": "thirteen", "pc_name": "L. 222-9 (7)",
    },
    "be": {
        "label": "BE", "holidays": "BE",
        "start": BE_START,
        "clock_article": "VI.47 § 2 + C. civ. art. I.7",
        "clock_anchor": "nouveau Code civil art. I.7 (loi du 28 "
            "avril 2022) — § 1er lendemain, § 3 samedi non ouvrable, "
            "§ 4 échéance reportée, § 7 application supplétive",
        "clock_text": BE_CLOCK,
        "deadline_source": "VI.47 § 2 + C. civ. I.7 § 4",
        "ext_article": "VI.48 al. 1 (douze mois)",
        "restart_article": "VI.48 al. 2",
        "exceptions": BE_EXCEPTIONS,
        "exception_article": "VI.53 %s",
        "advance": ("sat", "sun", "hol"),
        "second_advance": True,
        "second_clock": ("VI.51 § 1er (renvoi)",
                         "VI.50 § 1er (remboursement)"),
        "in_store": _REFUSAL_IN_STORE_BE,
        "law_code": "Code de droit économique (BE), Livre VI, "
                    "VI.47 à VI.53 et VI.67 + Code civil I.7",
        "ext_short": "VI.48 al. 1", "restart_label": "VI.48 al. 2",
        "restart_short": "al. 2",
        "kind_message": "kind outside the closed set — the four "
            "contract families VI.47 § 2 and VI.67 § 2 name their "
            "own start for",
        "pc_count": "fourteen", "pc_name": "VI.53",
    },
}



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


def _holiday(hol_country, d):
    """(name, law) if d is a legal holiday in THAT country, else
    None. THE ONE TABLE — schedule/holidays, cited per line (FR
    L3133-1, LU COTRAV L. 232-6, BE liste SPF Emploi) — théorème des
    sœurs, pas de seconde table, aucun jour inventé."""
    res = holidays_kit.holidays(hol_country, d.year)
    iso = d.isoformat()
    for x in res["holidays"]:
        if x["date"] == iso:
            return x["name"], x["law"]
    return None


def _advance(mode, hol_country, dt):
    """FR L221-19 3° / LU L. 221-3 (1) al. 2 / BE C. civ. I.7 § 4 :
    the expiry pushes day by day while the day is not ouvrable UNDER
    THAT STATE'S definition. mode = the tuple from COUNTRIES:
    FR and BE carry (« sat », « sun », « hol ») — the French article
    names the samedi, I.7 § 3 EXCLUDES the samedi from jours
    ouvrables; LU carries only (« sun », « hol ») — ouvrable = tous
    les jours sauf dimanches et fériés (glossaire guichet.lu, ITM
    D9a3), Saturday SURVIVES. Returns (final, chain)."""
    chain = []
    while True:
        w = dt.weekday()
        if w == 5 and "sat" in mode:
            chain.append({"date": dt.isoformat(), "reason": "Saturday"})
        elif w == 6:
            chain.append({"date": dt.isoformat(), "reason": "Sunday"})
        else:
            h = _holiday(hol_country, dt) if "hol" in mode else None
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
    if c not in COUNTRIES:
        raise WithdrawalError("country", _REFUSAL_OTHER_COUNTRY,
                              "fr | be | lu")
    g = COUNTRIES[c]
    k = (kind or "").strip().lower()
    if k == "in_store":
        raise WithdrawalError("kind", g["in_store"],
                              " | ".join(KINDS))
    if k not in KINDS:
        raise WithdrawalError("kind", g["kind_message"],
                              " | ".join(KINDS))
    s = _iso(start_date, "start_date")

    if product_class is not None:
        pc = str(product_class).strip().lower()
        if pc not in g["exceptions"]:
            raise WithdrawalError("product_class",
                "product_class outside the %s closed classes of %s — "
                "an exception is a named clause, never a guess"
                % (g["pc_count"], g["pc_name"]),
                " | ".join(sorted(g["exceptions"])))
    else:
        pc = None

    day1 = s + timedelta(days=1)                    # jour 1 (FR) /
    raw = s + timedelta(days=PERIOD_DAYS)           # lendemain + 14 (BE)
    fin, chain = _advance(g["advance"], g["holidays"], raw)

    out = {
        "country": g["label"],
        "kind": k,
        "start_date": s.isoformat(),
        "start_weekday": _wd(s),
        "start_rule": {"article": g["start"][k][0],
                       "text": g["start"][k][1]},
        "clock": {"article": g["clock_article"],
                  "anchor": g["clock_anchor"],
                  "text": g["clock_text"]},
        "day1": day1.isoformat(),
        "deadline_initial": raw.isoformat(),
        "deadline_initial_weekday": _wd(raw),
        "deadline": fin.isoformat(),
        "deadline_weekday": _wd(fin),
        "extension_applied": bool(chain),
        "extension_chain": chain,
        "final_deadline": fin.isoformat(),
        "final_deadline_source": g["deadline_source"],
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
        # l'article de la TRENTAINE (FR L221-20 / LU L. 222-9 (3) /
        # BE VI.48) existe pour l'information QUI MANQUAIT : un
        # info_date l'implique — le champ repart true, jamais on ne
        # laisse « info fournie » contredire « info tardive ».
        out["info_missing"] = True
        out["info_date"] = i.isoformat()

    if out["info_missing"]:
        ext = _plus_months(fin, EXT_MONTHS)        # al. 1
        out["extended_12m"] = ext.isoformat()
        if out["info_date"] is None:
            out["final_deadline"] = ext.isoformat()
            out["final_deadline_source"] = g["ext_article"]
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
                out["final_deadline_source"] = (
                    "%s — info_date %s falls AFTER the twelve-month "
                    "prolongation, no new fourteen-day period is "
                    "born under %s" % (g["ext_short"], i.isoformat(),
                                       g["restart_short"]))
            else:
                i_raw = i + timedelta(days=PERIOD_DAYS)
                i_fin, i_chain = _advance(g["advance"],
                                          g["holidays"], i_raw)
                out["restarted_deadline"] = i_fin.isoformat()
                out["restarted_extension"] = i_chain
                out["final_deadline"] = i_fin.isoformat()
                out["final_deadline_source"] = (
                    "%s — new fourteen-day period from the day the "
                    "late information arrived (%s)"
                    % (g["restart_label"], i.isoformat()))

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
        # FR L221-23/L221-24 et LU L. 222-10 rendent quatorze JOURS
        # CALENDAIRES SANS avance publiee pour ces horloges-la — la
        # prorogation est ecrite pour LE delai de retractation. BE,
        # art. I.7 § 4 : la regle vise TOUTE prestation ou
        # communication — la seconde horloge belge AVANCE donc.
        # Divergences NOMMEES en conditions, jamais moyennees.
        if g["second_advance"]:
            nb, _ = _advance(g["advance"], g["holidays"], nb)
        out["return_by"] = nb.isoformat()
        out["refund_by"] = nb.isoformat()

    if pc is not None:
        label, clause, note = g["exceptions"][pc]
        out["exception"] = {"class": pc,
                            "article": g["exception_article"] % label,
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

    if c == "fr":
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
    elif c == "lu":
        out["conditions"] = [
            "the fourteen CALENDAR days run from the start ABOVE "
            "(L. 222-9 (1)-(2)) and the expiry advances ONLY while "
            "the day is Sunday or a legal holiday (L. 221-3 (1) al. "
            "2) — SATURDAY IS A BUSINESS DAY in Luxembourg (official "
            "glossaire guichet.lu: « les jours du calendrier, sauf "
            "les dimanches et les jours fériés légaux »; ITM D9a3: "
            "« du lundi au samedi »), so a Saturday deadline STAYS a "
            "Saturday where French L221-19 names it and advances. "
            "One parcel, three grammars — France and Belgium move, "
            "Luxembourg does not",
            "L. 221-3 (1) requires the withdrawal BY WRITING or on "
            "another durable medium (oral allowed for the first "
            "section of chapter 2 — al. 3); the burden of proving "
            "the withdrawal is the consumer's (L. 222-9 (5) al. 3) — "
            "keep the timestamp",
            "return_by/refund_by are fourteen-day clocks from the "
            "communication (L. 222-10 (4) return, L. 222-10 (1) "
            "refund) traveling WITHOUT the L. 221-3 advance — the "
            "prorogation is written for le délai de rétractation "
            "itself; a refund paid late carries the LEGAL INTEREST "
            "rate by operation of law (L. 222-10 (1) al. 2): "
            "divergence named, never averaged",
            "info missing: the window closes twelve months after "
            "the initial expiry (L. 222-9 (3)); information supplied "
            "during that year restarts a fresh fourteen days from "
            "ITS receipt (L. 222-9 (4))",
            "the right also runs on soldes, occasion and déstockage "
            "buys at distance — the exact words BEE SECURE, CEC and "
            "ULC published 24-Nov-2026; a shop-window promo does not "
            "cancel it; in-store carries NO automatic right (same "
            "words, same statutes)",
            "holidays used are the 11 COTRAV L. 232-6 legal days — "
            "including 23 juin (anniversaire du Grand-Duc), 26 "
            "décembre (Saint-Étienne, absent FR et BE) and 9 mai "
            "(Journée de l'Europe, loi du 25 avril 2019 — le "
            "Luxembourg, seul pays de l'UE à en faire un jour férié)",
            "the store's voluntary window is a different clock: "
            "/shop/return-deadline; LU sale-window dates are NOT "
            "this tool and not yet in any table (/shop/soldes-window "
            "is France, /shop/soldes-be is Belgium) — refused by name",
        ]
        out["provenance"] = {
            "code": "Code de la consommation (Luxembourg), L. 221-3 "
                    "(1), L. 222-9 (1)-(4) et (7), L. 222-10 (1) et (4)",
            "rejoue": "legilux consolidated 20251125 read verbatim "
                      "25-Nov-2026 (full-code local archive) — the "
                      "pre-2014 numbering L. 1251-x was ABROGATED by "
                      "the loi du 2 avril 2014; the queue's stale "
                      "citation was corrected at the gate, lesson "
                      "filed at the playbook",
            "official_fiches": "guichet.lu rétractation page (last "
                               "update 17-06-2026 — same 14 jours "
                               "calendrier, same advance rule, same "
                               "twelve-month tail) + glossaire « Jour "
                               "ouvrable » + ITM D9a2/D9a3, all "
                               "replayed 25-Nov-2026",
            "sister_table": "LU legal holidays: COTRAV L. 232-6 + loi "
                            "du 25 avril 2019 via /api/v1/schedule/"
                            "holidays?country=lu (table entered this "
                            "cycle — the gate found it did NOT exist)",
        }
    else:
        out["conditions"] = [
            "the fourteen days START THE DAY AFTER the event (C. civ. "
            "art. I.7 § 1er — the SPF guide renders VI.47 § 2 the "
            "same way: « à compter du lendemain du jour de la "
            "livraison ») and an expiry falling on a Saturday, Sunday "
            "or legal holiday ends at the last hour of the NEXT "
            "business day (I.7 § 4; § 3 EXCLUDES Saturday from jours "
            "ouvrables) — the Belgian answer moves like the French "
            "one, BY A DIFFERENT TEXT: a Belgian CGV reciting the "
            "French L221-19 reaches the right date from the wrong "
            "statute (several replayed 25-Nov-2026)",
            "I.7 § 4 is written for ANY prestation or communication, "
            "so the Belgian second clocks (return VI.51 § 1er, refund "
            "VI.50 § 1er) CARRY the advance that French L221-23/24 "
            "and Luxembourg L. 222-10 travel RAW — same notification "
            "date, different refund day. Divergences named, never "
            "averaged",
            "Belgian exceptions number FOURTEEN (VI.53 1°-14°): paris "
            "et loteries (14°) has no French or Luxembourg twin",
            "info missing: twelve months from the initial expiry "
            "(VI.48 al. 1); information supplied during that year "
            "restarts fourteen days from its receipt (VI.48 al. 2)",
            "the right runs on soldes and occasion buys at distance "
            "(SPF guide replayed 25-Nov-2026); the BELGIAN SALE "
            "SEASONS are another article and another tool: VI.25 "
            "dates them at /shop/soldes-be — VI.47 is withdrawal",
            "holidays used are the 10 FEDERAL SPF Emploi days (21 "
            "juillet, 11 novembre — not the French 8 mai/14 juillet, "
            "not the Luxembourg 23 juin/26 décembre); community and "
            "regional days (28 septembre, 11 juillet) are NOT federal "
            "and never enter silently",
            "in-store: no automatic right — VI.47 (distance) and "
            "VI.67 (hors établissement) close the circle; store "
            "windows: /shop/return-deadline",
        ]
        out["provenance"] = {
            "code": "Code de droit économique (Belgique), Livre VI — "
                    "VI.47 § 2, VI.48, VI.50, VI.51, VI.53, VI.67 + "
                    "nouveau Code civil art. I.7 (loi du 28 avril 2022)",
            "rejoue": "ejustice consolidated text read 25-Nov-2026 in "
                      "a real browser: VI.47-VI.53/VI.67 verbatim "
                      "(inserted by the loi du 21 décembre 2013, "
                      "in force 31-05-2014; VI.53 modified by the "
                      "loi du 8 mai 2022, in force 28-05-2022); "
                      "« expire un samedi » = ZERO occurrences in "
                      "Livre VI — the advance lives in C. civ. I.7 "
                      "§§ 1, 3, 4, 7 read verbatim at ejustice; the "
                      "queue's « VI.25 » was the SALE article — "
                      "corrected at the gate, lesson filed",
            "official_fiches": "SPF Économie ventes-à-distance page + "
                               "guide « Le droit de rétractation dans "
                               "les contrats à distance » (lendemain "
                               "start, 14 jours calendrier, 12 mois, "
                               "remboursement 14 jours), replayed "
                               "25-Nov-2026; 10 jours fériés : liste "
                               "SPF Emploi",
            "sister_table": "BE legal holidays: liste SPF Emploi via "
                            "/api/v1/schedule/holidays?country=be "
                            "(table entered this cycle — the gate "
                            "found it did NOT exist)",
        }
    out["grammar_note"] = (
        "FR/BE/LU only — three REPLAYED statutes; each of the three "
        "answers the same parcel with its own counting grammar, and "
        "the tool names where they diverge instead of averaging them")
    if c == "fr":
        # b107 pins : la reponse FR voyage byte-a-byte — la note est
        # pour les pays ENTRES ce cycle, pas un champ neuf sur les
        # reponses epinglees.
        del out["grammar_note"]
    return out
