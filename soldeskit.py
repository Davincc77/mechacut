# -*- coding: utf-8 -*-
"""soldeskit — /shop/soldes-window : les dates LÉGALES des soldes
français, calculées depuis l'arrêté, derogations annuelles comprises.
Sources rejouées VERBATIM ce cycle (24-nov-2026) sur legifrance :

LA DOULEUR, mesurée par la lentille HUMAIN (24-nov-2026, à J-43 du
premier mercredi) : les sites de calendrier se contredisent DÉJÀ sur
2027 — dates-soldes.net, france.fr, voici, tpeactu, calendriergratuit
impriment « mercredi 6 janvier 8 h -> mardi 2 février inclus » ; un
autre site titre « jusqu'au mardi 9 février » — il a appliqué le
2e mercredi (13 janvier) SANS la clause d'avance. La règle tient en
une phrase et les modèles la ratent en confiance, surtout l'été : la
DEROGATION DE REPORT existe dans les deux sens (l'hiver AVANCE quand
le 2e mercredi est après le 12 ; l'été recule d'un cran en 2021 sous
un arrêté daté, puis AVANCE quand le dernier mercredi est après le
28). Et les tableaux de presse portent leurs propres fautes : moneyvox
2023 affirmait la Guyane soldée « du 5 octobre au 1er novembre » alors
que l'annexe consolidée ne liste plus la 973 depuis l'arrêté du
21 avril 2023 — Le Figaro 2024 écrit « alignée sur la date nationale ».
Enfin : QUATRE années ont été entièrement RECABLÉES par arrêté ad
hoc (été 2020 reporté au 15 juillet pour cause de Covid ; hiver 2021
reporté au 20 janvier puis PORTÉ À SIX SEMAINES par l'arrêté du
15 février 2021 ; été 2021 décalé au 30 juin — et au 26 JUIN pour la
Moselle seule ; Guadeloupe été 2021 au jeudi 7 octobre ; été 2023
puis été 2026 PORTÉS À CINQ SEMAINES pour cause de canicule). Aucun
moteur de calendrier ne publie ces arretés ; aucun modèle ne les a
de mémoire — les calculer mécaniquement depuis la grammaire 2019
RENDS DE FAUSSES DATES sur 2020-2021-2023-2026. La table les porte,
verbatim, avec leur JORF.

RÈGLE FERMÉE (arrêté du 27 mai 2019, NOR ECOI1911930A, JORF n°0124
du 29 mai 2019, en vigueur au 24/11/2026, consolidé legifrance) :
  art. 1er — hiver : « les soldes d'hiver débutent le deuxième
  mercredi du mois de janvier à 8 heures du matin. Cette date est
  avancée au premier mercredi du mois de janvier lorsque le deuxième
  mercredi intervient après le 12 du mois » — APRÈS LE 12 est STRICT :
  2e merc = 12 pile -> PAS d'avance (bornes vécues : 2028-01-12 garde,
  2027-01-13 avance).  été : « les soldes d'été débutent le dernier
  mercredi du mois de juin à 8 heures du matin. Cette date est avancée
  à l'avant-dernier mercredi du mois de juin lorsque le dernier
  mercredi intervient après le 28 du mois » — borne 2028-06-28 garde,
  2027-06-30 avance (lecalendrier et les modèles ratent CETTE
  moitié-là aussi).
  art. 2 + annexe — « par dérogation [...], les soldes sont fixés à
  des dates différentes dans certaines zones ». DEUX versions
  rejouées : INITIALE (JORF 29-05-2019 : 06 et 66 été = premier
  mercredi de juillet ; 973 hiver = premier mercredi de janvier, été =
  premier jeudi d'octobre ; 2A/2B = deuxième mercredi de juillet ;
  54/55/57/88 = premier jour OUVRÉ de janvier ; 971 hiver premier
  samedi / été dernier samedi de septembre ; 972 été premier jeudi
  d'octobre ; 974 hiver premier samedi de septembre / été premier
  samedi de février ; 975 « premier mercredi APRÈS le 14 juillet /
  APRÈS le 15 janvier » — après STRICT, borne vécue : le 15-01-2025
  EST mercredi -> 2025-01-22) et COURANTE (modifiée par arrêté du
  21 avril 2023, en vigueur 17 mai 2023 — 06, 66, 973 SORTIS :
  droit commun dès leurs fenêtres 2023).
  art. 3 — « La durée de chaque période de soldes est fixée à quatre
  semaines. » Fin INCLUSE = début + 27, le jour du début compté ;
  quatre confirmations indépendantes : officiel 2026 (7 janv ->
  3 févr, 24 juin -> 21 juil. avant prolongation), dgccrf Corse
  (8 juil -> 4 août), tpeactu SPM (20 janv -> 16 févr), Cher/Orne
  2021 (30 juin -> 27 juil.).
  art. 4 — « Le présent arrêté entre en vigueur le 1er janvier
  2020 » : les années < 2020 sont REFUSÉES, les dates relevaient
  d'arrêtés préfectoraux annuels non rejoués.

DÉROGATIONS ANNUELLES REJOUÉES (table fermée, chaque ligne voyage
avec son verbatim et sa source) :
  * arrêté du 10 juin 2020 (JORFTEXT000041987131) — été 2020 :
    « la date et l'heure de début des soldes d'été sont fixées au
    mercredi 15 juillet à 8 heures du matin », étendu NOMMÉMENT à
    « Alpes-Maritimes (06), Corse-du-Sud (2A), Haute-Corse (2B) et
    Pyrénées-Orientales (66) » ; « Les dates des autres zones listées
    en annexe sont inchangées. » Durée 4 semaines -> fin 11 août
    (lettre DGCCRF : « du mercredi 15 juillet à 8h00 au mardi 11 août
    inclus »).
  * arrêté du 23 décembre 2020 (JORFTEXT000042746859, JORF 29/12) —
    hiver 2021 : début « mercredi 20 janvier à 8 heures du matin »,
    également pour « Meurthe-et-Moselle, Meuse, Moselle, Vosges et
    Guadeloupe » nommées ; « autres départements et collectivités
    listés dans l'annexe [...] inchangées ».
  * arrêté du 15 février 2021 (JORF 16/02/2021 n°0040) — DURÉE hiver
    2021 : « six semaines [...] pour l'ensemble des départements,
    y compris la Meurthe-et-Moselle, la Meuse, la Moselle, les Vosges
    et la Guadeloupe. Toutefois, la durée applicable au département
    de La Réunion, ainsi qu'aux collectivités de Saint-Barthélemy et
    Saint-Martin, est inchangée : cette durée reste fixée à quatre
    semaines. » -> 20 janv. + 41 = 2 mars 2021 (confirmé : arrêté
    préfectoral Loire RAA 18-02-2021 « du 20 janvier au 2 mars 2021 »
    et réponse ministérielle AN n°437 du 20-09-2022). La 975 (COM non
    nommée) reste à quatre : le texte ne vise que « départements ».
  * arrêté du 15 juin 2021 (JORFTEXT000043684541, JORF 22/06) — été
    2021 : « fixées au 30 juin 2021 à 8 heures du matin » ; MOSSELLE
    seule nommée dans un article propre : « Pour la Moselle, [...]
    fixées au 26 juin 2021 » — un département arraché au droit commun
    par UNE ligne de texte que aucun calendrier grand public ne
    reproduit.
  * arrêté du 23 septembre 2021 (JORFTEXT000044091790) — Guadeloupe
    été 2021 : « la date et l'heure de début des soldes d'été en
    Guadeloupe (971) sont fixées au jeudi 7 octobre 2021 à 8 heures
    du matin ». Coincidence nommée : la 972, elle, tient son
    premier jeudi d'octobre par l'annexe — même date, deux sources.
  * arrêté du 6 juillet 2023 — été 2023 : « la durée des soldes d'été
    est de cinq semaines pour les départements dont la date de début
    des soldes est fixée au 28 juin 2023. La durée [...] listées dans
    l'annexe [...] est inchangée. » -> fin 1er août (moneyvox
    « nouvelle date de fin officielle ») ; la Corse garde 12 juil. ->
    8 août (moneyvox) : les dates ANNEXES ne suivent pas.
  * arrêté du 3 juillet 2026 (JORF n°0157 du 7 juillet 2026, NOR
    PMEI2617525A) — été 2026 : « pour l'année 2026, la durée de la
    période des soldes d'été est portée à cinq semaines pour les
    départements dont la date et l'heure de début des soldes sont
    déterminées en application de l'article 1er » (canicule,
    service-public A15000) -> 24 juin + 34 = 28 juillet, et la Corse,
    annexe, reste à 8 juil. -> 4 août (dgccrf fiche Soldes, rejouée).
    La clause vise l'ARTICLE 1ER : les départements d'Est soldent
    leur ETE sur la base de l'art. 1er (leur dérogation annexe ne
    porte que l'hiver) -> eux aussi à cinq semaines. ZÉRO devinette
    de scope : le scope est PREDIQUÉ depuis le texte.

L'AMBIGUITÉ DE L'EST, portée et nommée : « premier jour ouvré » —
l'annexe ne définit pas le mot. Lecture stricte (ouvré = travaillé,
lundi-vendredi hors férié du 1er) : 2027-01-04. Lecture « ouvrable »
(lundi-samedi) : 2027-01-02, celle qu'impriment tpeactu, france.fr,
voici. codespromoplus pose le conflit LUI-MÊME : « soit le samedi 2
janvier, jusqu'au 29, soit le lundi 4 janvier, jusqu'au 31, selon
que le samedi compte ou non ». Le mot de l'ARRÊTÉ est « ouvré » :
la lecture stricte est PRIMAIREE, l'autre voyage avec les deux
fenêtres, le verbatim et le nom du conflit. La divergence ne naît
que quand le 1er janvier tombe vendredi férié — 2027, 2038, 2049...
les autres années les deux lectures donnent la même date : le conflit
est daté, pas permanent.

CONTRAT : year (2020..9999, borne art. 4 nommée) + territory (liste
CLOSE des codes et noms de l'annexe, « metropole », « lorraine »,
« corse » ; pays étrangers REFUSÉS PAR NOM portant leur fait — la
table ne rejoue QUE l'arrêté français, et ne prête pas de mémoire
aux calendes belges ou luxembourgeoises) + season (hiver|ete|both)
+ as_of optionnel — JAMAIS d'horloge murale. Statut de fenêtre :
UPCOMING / IN_PROGRESS / ENDED + compte à rebours en jours (vecteur
vécu : as_of 2026-11-24 -> 43 jours avant le 6 janvier 2027, pile le
« Dans 43 jours » de la presse du jour).

ZÉRO réseau, zéro horloge, zéro conseil d'achat : l'outil rend des
DATES, la règle qui les nomme, les arrêtés qui les déplacent.
"""

from datetime import date as _date, timedelta as _td
import calendar as _cal

SOLDES_TABLE_VERSION = "2026-11-24"
_MON, _TUE, _WED, _THU, _FRI, _SAT, _SUN = range(7)
_DUR_SEM = 4  # art. 3

# ---------------------------------------------------------------- verbatims
ART1_HIVER = ("- les soldes d'hiver débutent le deuxième mercredi du "
              "mois de janvier à 8 heures du matin. Cette date est "
              "avancée au premier mercredi du mois de janvier lorsque "
              "le deuxième mercredi intervient après le 12 du mois")
ART1_ETE = ("- les soldes d'été débutent le dernier mercredi du mois "
            "de juin à 8 heures du matin. Cette date est avancée à "
            "l'avant-dernier mercredi du mois de juin lorsque le "
            "dernier mercredi intervient après le 28 du mois")
ART3 = ("La durée de chaque période de soldes est fixée à quatre "
        "semaines")
ART4 = "Le présent arrêté entre en vigueur le 1er janvier 2020"
_GATE = _date(2020, 1, 1)
# l'annexe initiale vit du 01/01/2020 au 16/05/2023 ; l'arrêté du
# 21 avril 2023 (Alpes-Maritimes) la remplace au 17 mai 2023 — la
# date de fenêtre est le test, pas la date de la demande.
_ANNEXE_SWITCH = _date(2023, 5, 17)

# ---------------------------------------------------------------- calendrier
def _nth_dow(y, m, n, dow):
    d = _date(y, m, 1)
    while d.weekday() != dow:
        d += _td(days=1)
    return d + _td(days=7 * (n - 1))


def _last_dow(y, m, dow):
    d = _date(y, m, _cal.monthrange(y, m)[1])
    while d.weekday() != dow:
        d -= _td(days=1)
    return d


def _first_dow_after(y, m, day_after, dow):
    """« premier mercredi APRÈS le 15 janvier » — après STRICT."""
    d = _date(y, m, day_after + 1)
    while d.weekday() != dow:
        d += _td(days=1)
    return d


def _premier_jour_ouvre(y):
    """Lecture stricte : jours travaillés lundi-vendredi, 1er janvier
    férié exclu. (Aucun autre férié en janvier.)"""
    d = _date(y, 1, 1)
    while d.weekday() > _FRI or d.day == 1:
        d += _td(days=1)
    return d


def _premier_jour_ouvrable(y):
    """Lecture « ouvrable » portée en conflit : lundi-samedi, 1er
    janvier férié exclu."""
    d = _date(y, 1, 1)
    while d.weekday() > _SAT or d.day == 1:
        d += _td(days=1)
    return d

# ---------------------------------------------------------------- art. 1er
def _art1_start(year, season):
    if season == "hiver":
        first = _nth_dow(year, 1, 1, _WED)
        second = first + _td(days=7)
        # « après le 12 » STRICT : le 12 lui-même NE déclenche rien.
        return (first if second.day > 12 else second), second, True
    last = _last_dow(year, 6, _WED)
    penult = last - _td(days=7)
    return (penult if last.day > 28 else last), last, False

# ---------------------------------------------------------------- annexes
# ligne = (callable(year)->date, verbatim de la colonne DATES, heure?)
def _sat(y, m, n):
    return _nth_dow(y, m, n, _SAT)


ANNEXE_EST = ("premier jour ouvré de janvier",
              lambda y: _premier_jour_ouvre(y),
              "Soldes d'hiver : premier jour ouvré du mois de janvier")
ANNEXE_ROWS = {
    # lignes INCHANGÉES par l'arrêté du 21 avril 2023 (identiques dans
    # les deux versions — colonne (label, callable, verbatim)) :
    "2A": {"ete": ("deuxieme mercredi de juillet",
                   lambda y: _nth_dow(y, 7, 2, _WED),
                   "Soldes d'été : deuxième mercredi du mois de juillet")},
    "2B": {"ete": ("deuxieme mercredi de juillet",
                   lambda y: _nth_dow(y, 7, 2, _WED),
                   "Soldes d'été : deuxième mercredi du mois de juillet")},
    "54": {"hiver": ANNEXE_EST}, "55": {"hiver": ANNEXE_EST},
    "57": {"hiver": ANNEXE_EST}, "88": {"hiver": ANNEXE_EST},
    "971": {"hiver": ("premier samedi de janvier",
                      lambda y: _sat(y, 1, 1),
                      "Soldes d'hiver : premier samedi de janvier"),
            "ete": ("dernier samedi de septembre",
                    lambda y: _last_dow(y, 9, _SAT),
                    "Soldes d'été : dernier samedi de septembre")},
    "972": {"ete": ("premier jeudi d'octobre",
                    lambda y: _nth_dow(y, 10, 1, _THU),
                    "Soldes d'été : premier jeudi d'octobre")},
    "974": {"hiver": ("premier samedi de septembre",
                      lambda y: _sat(y, 9, 1),
                      "Soldes d'hiver : premier samedi du mois de septembre"),
            "ete": ("premier samedi de février",
                    lambda y: _sat(y, 2, 1),
                    "Soldes d'été : premier samedi du mois de février")},
    "975": {"hiver": ("premier mercredi après le 15 janvier",
                      lambda y: _first_dow_after(y, 1, 15, _WED),
                      "Soldes d'hiver : premier mercredi après le 15 janvier"),
            "ete": ("premier mercredi après le 14 juillet",
                    lambda y: _first_dow_after(y, 7, 14, _WED),
                    "Soldes d'été : premier mercredi après le 14 juillet")},
    "977": {"hiver": ("premier samedi de mai", lambda y: _sat(y, 5, 1),
                      "Soldes d'hiver : premier samedi de mai"),
            "ete": ("deuxième samedi d'octobre", lambda y: _sat(y, 10, 2),
                    "Soldes d'été : deuxième samedi d'octobre")},
    "978": {"hiver": ("premier samedi de mai", lambda y: _sat(y, 5, 1),
                      "Soldes d'hiver : premier samedi de mai"),
            "ete": ("deuxième samedi d'octobre", lambda y: _sat(y, 10, 2),
                    "Soldes d'été : deuxième samedi d'octobre")},
}
# lignes ABROGÉES au 17 mai 2023 (arrêté du 21 avril 2023) — ne vivent
# que pour les fenêtres COMMENCÉES avant le switch :
ANNEXE_INITIALE = {
    "06": {"ete": ("premier mercredi de juillet",
                   lambda y: _nth_dow(y, 7, 1, _WED),
                   "Soldes d'été : premier mercredi du mois de juillet")},
    "66": {"ete": ("premier mercredi de juillet",
                   lambda y: _nth_dow(y, 7, 1, _WED),
                   "Soldes d'été : premier mercredi du mois de juillet")},
    "973": {"hiver": ("premier mercredi de janvier",
                      lambda y: _nth_dow(y, 1, 1, _WED),
                      "Soldes d'hiver : premier mercredi du mois de janvier"),
            "ete": ("premier jeudi d'octobre",
                    lambda y: _nth_dow(y, 10, 1, _THU),
                    "Soldes d'été : premier jeudi du mois d'octobre")},
}

# ---------------------------------------------------------------- derogations
# Chaque derogation porte son effet CALCULABLE + son verbatim. Les
# scopes sont des PREDICATS sur (code, base_start_is_art1, season).
DEROGATIONS = {
    "ete_2020": {
        "arrete": "arrêté du 10 juin 2020",
        "source": "legifrance JORFTEXT000041987131",
        "verbatim": ("la date et l'heure de début des soldes d'été "
                     "sont fixées au mercredi 15 juillet à 8 heures du "
                     "matin ; cette date s'applique également aux "
                     "départements des Alpes-Maritimes (06), de "
                     "Corse-du-Sud (2A), de Haute-Corse (2B) et des "
                     "Pyrénées-Orientales (66) ; les dates des autres "
                     "zones listées en annexe sont inchangées"),
        "year": 2020, "season": "ete", "effect": "START",
        "start": _date(2020, 7, 15), "time": "08:00",
        "in_scope": lambda code, art1, season: art1 or code in ("06", "2A", "2B", "66"),
    },
    "hiver_2021_date": {
        "arrete": "arrêté du 23 décembre 2020",
        "source": "legifrance JORFTEXT000042746859 (JORF 29/12/2020)",
        "verbatim": ("la date et l'heure de début des soldes d'hiver "
                     "sont fixées au mercredi 20 janvier à 8 heures du "
                     "matin ; également fixée au 20 janvier pour la "
                     "Meurthe-et-Moselle, la Meuse, la Moselle, les "
                     "Vosges et la Guadeloupe ; les dates applicables "
                     "aux autres départements et collectivités listés "
                     "dans l'annexe sont inchangées"),
        "year": 2021, "season": "hiver", "effect": "START",
        "start": _date(2021, 1, 20), "time": "08:00",
        "in_scope": lambda code, art1, season: art1 or code in ("54", "55", "57", "88", "971"),
    },
    "hiver_2021_duree": {
        "arrete": "arrêté du 15 février 2021",
        "source": "JORF n°0040 du 16/02/2021",
        "verbatim": ("à titre dérogatoire, la durée des soldes est "
                     "fixée à six semaines pour les soldes d'hiver "
                     "2021 ; cette durée s'applique pour l'ensemble "
                     "des départements, y compris la Meurthe-et-Moselle, "
                     "la Meuse, la Moselle, les Vosges et la Guadeloupe ; "
                     "toutefois, la durée applicable au département de "
                     "La Réunion, ainsi qu'aux collectivités de "
                     "Saint-Barthélemy et Saint-Martin, est inchangée : "
                     "cette durée reste fixée à quatre semaines"),
        "year": 2021, "season": "hiver", "effect": "DURATION",
        "weeks": 6,
        # « l'ensemble des départements » nommés + les exclus NOMMÉS
        # (974, 977, 978). La COM 975 n'est ni département ni nommée :
        # les six semaines ne l'atteignent pas — le verbatim voyage.
        "in_scope": lambda code, art1, season: code not in ("974", "975", "977", "978"),
    },
    "ete_2021_date": {
        "arrete": "arrêté du 15 juin 2021",
        "source": "legifrance JORFTEXT000043684541 (JORF 22/06/2021)",
        "verbatim": ("la date et l'heure de début des soldes d'été sont "
                     "fixées au 30 juin 2021 à 8 heures du matin ; pour "
                     "la Moselle, la date et l'heure de début des "
                     "soldes d'été sont fixées au 26 juin 2021 à 8 "
                     "heures du matin"),
        "year": 2021, "season": "ete", "effect": "START",
        "start": _date(2021, 6, 30), "time": "08:00",
        "moselle": {"start": _date(2021, 6, 26)},
        "in_scope": lambda code, art1, season: art1,
    },
    "ete_2021_guadeloupe": {
        "arrete": "arrêté du 23 septembre 2021",
        "source": "legifrance JORFTEXT000044091790",
        "verbatim": ("la date et l'heure de début des soldes d'été en "
                     "Guadeloupe (971) sont fixées au jeudi 7 octobre "
                     "2021 à 8 heures du matin"),
        "year": 2021, "season": "ete", "effect": "START",
        "start": _date(2021, 10, 7), "time": "08:00",
        "in_scope": lambda code, art1, season: code == "971",
    },
    "ete_2023_duree": {
        "arrete": "arrêté du 6 juillet 2023",
        "source": "legifrance (JORF 8 juillet 2023)",
        "verbatim": ("la durée des soldes d'été est de cinq semaines "
                     "pour les départements dont la date de début des "
                     "soldes est fixée au 28 juin 2023 ; la durée des "
                     "soldes d'été dont les dates dérogatoires sont "
                     "listées dans l'annexe de l'arrêté du 27 mai 2019 "
                     "est inchangée"),
        "year": 2023, "season": "ete", "effect": "DURATION",
        "weeks": 5,
        "in_scope": lambda code, art1, season: art1,
    },
    "ete_2026_duree": {
        "arrete": "arrêté du 3 juillet 2026",
        "source": "legifrance NOR PMEI2617525A (JORF n°0157 du "
                  "7 juillet 2026)",
        "verbatim": ("à titre exceptionnel et par dérogation à "
                     "l'article 3 de l'arrêté du 27 mai 2019, pour "
                     "l'année 2026, la durée de la période des soldes "
                     "d'été est portée à cinq semaines pour les "
                     "départements dont la date et l'heure de début "
                     "des soldes sont déterminées en application de "
                     "l'article 1er (canicule — service-public A15000)"),
        "year": 2026, "season": "ete", "effect": "DURATION",
        "weeks": 5,
        "in_scope": lambda code, art1, season: art1,
    },
}
# Le predicate art1 ci-dessus est évalué sur la SOURCE de la date de
# BASE (art. 1er vs annexe), donc 54/55/57/88 — dont l'été vient bien
# de l'art. 1er — entrent dans les cinq semaines 2023/2026 ; la Corse
# (annexe été) en sort, comme l'écrit la fiche dgccrf.

# ---------------------------------------------------------------- vocabulaires
_T_ERR = ("territory: liste CLOSE — metropole|france (droit commun), "
          "06|2A|2B|54|55|57|66|88|971|972|973|974|975|976|977|978, "
          "lorraine, corse — ou un pays refusé par nom")
_ALIASES = {
    "FR_METRO": ("metropole", "metropolitaine", "france", "fr",
                 "france metropolitaine", "hexagone", "droit commun",
                 "en ligne", "e commerce", "ecommerce", "internet",
                 "online"),
    "06": ("06", "alpes maritimes", "nice"),
    "2A": ("2a", "corse du sud", "ajaccio"),
    "2B": ("2b", "haute corse", "bastia"),
    "CORSE": ("corse",),
    "54": ("54", "meurthe et moselle", "nancy"),
    "55": ("55", "meuse"),
    "57": ("57", "moselle", "metz"),
    "88": ("88", "vosges", "epinal"),
    "LORRAINE": ("lorraine",),
    "66": ("66", "pyrenees orientales", "perpignan"),
    "971": ("971", "guadeloupe", "pointe a pitre"),
    "972": ("972", "martinique", "fort de france"),
    "973": ("973", "guyane", "cayenne"),
    "974": ("974", "reunion", "la reunion"),
    "975": ("975", "saint pierre", "saint et miquelon",
            "saint-pierre-et-miquelon"),
    "976": ("976", "mayotte"),
    "977": ("977", "saint barthelemy", "st barths"),
    "978": ("978", "saint martin", "st martin"),
}
# pays et territoires HORS table — refusés par nom portant LEUR fait
# d'ÊTRE hors table (aucune date de calendrier étranger n'est mémorisée
# ici, classe b100/b102).
FOREIGN = ("belg", "luxemb", "suiss", "quebe", "canad", "ontario",
           "royaume", "united", "kingdom", "great britain", "england",
           "scotland", "wales", "irlande", "irish", "espag", "italia",
           "portug", "brasil", "brazil", "bresil", "etats", "unis",
           "usa",
           "amerique", "maroc", "algerie", "tunisie", "senegal",
           "cote divoire", "deutschland", "germany", "niederlande",
           "holland", "suisse")
_SEASONS = {"hiver": "hiver", "winter": "hiver", "hivernale": "hiver",
            "ete": "ete", "été": "ete", "summer": "ete",
            "estival": "ete", "both": "both", "les deux": "both",
            "all": "both", "toutes": "both", "tous": "both"}
_WEEK = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
         "Saturday", "Sunday")


def _fold(s):
    out = []
    for ch in str(s).lower():
        if ch in "àâä":
            ch = "a"
        elif ch in "éèêë":
            ch = "e"
        elif ch in "îï":
            ch = "i"
        elif ch in "ôö":
            ch = "o"
        elif ch in "ùûü":
            ch = "u"
        elif ord(ch) > 127:
            ch = "?"
        out.append(ch)
    s = "".join(out)
    return " ".join(s.replace("-", " ").replace("/", " ").split())


class SoldesError(Exception):
    def __init__(self, field, message, expected):
        Exception.__init__(self, message)
        self.field = field
        self.message = message
        self.expected = expected


def _iso(d):
    return d.isoformat()


def _parse_as_of(s):
    try:
        return _date.fromisoformat(str(s))
    except Exception:
        raise SoldesError("as_of", "not an ISO calendar date: %r" % (s,),
                          "expected 'YYYY-MM-DD'")


def _territory(raw):
    t = _fold(raw if raw is not None else "metropole")
    for token in FOREIGN:
        if token in t:
            raise SoldesError(
                "territory",
                "%r refuse par nom portant son fait : la table ne "
                "rejoue QUE l'arrete francais du 27 mai 2019 ; le "
                "calendrier de ce territoire est fixe ailleurs et "
                "n'est PAS rejoue ici — aucune date n'est tiree de "
                "memoire" % (raw,), _T_ERR)
    multi = {"CORSE": ("2A", "2B"), "LORRAINE": ("54", "55", "57", "88")}
    for code, aliases in _ALIASES.items():
        if t in aliases or any(t == a or t.startswith(a + " ")
                               for a in aliases):
            if code in multi:
                return multi[code]
            return (code,)
    raise SoldesError("territory", "not in the closed table: %r" % (raw,),
                      _T_ERR)


def _season(raw):
    s = _fold(raw if raw is not None else "both")
    if s in _SEASONS:
        return _SEASONS[s]
    raise SoldesError(
        "season", "unknown season %r — attendu hiver|ete|both (liste "
        "closee)" % (raw,),
        "hiver | ete | both")


def _rule_for(code, year, season):
    """Règle de BASE : annexe (version datée) sinon art. 1er."""
    rows = {}
    if code in ANNEXE_ROWS:
        rows.update(ANNEXE_ROWS[code])
    if code in ANNEXE_INITIALE:
        init = ANNEXE_INITIALE[code]
        # la ligne initiale vit tant que la fenêtre commence avant le
        # switch 17 mai 2023 ; après, droit commun.
        probe = _date(year, 7, 1) if season == "ete" else _date(year, 1, 1)
        if probe < _ANNEXE_SWITCH and season in init:
            rows[season] = init[season]
    if season in rows:
        row = rows[season]
        fn, verbatim, hour = row[1], row[2], row[3] if len(row) > 3 else None
        return {"kind": "ANNEXE", "start": fn(year),
                "time": hour, "verbatim": verbatim,
                "art1": False}
    start, marker, _ = _art1_start(year, season)
    return {"kind": "ART1", "start": start, "time": "08:00",
            "verbatim": ART1_HIVER if season == "hiver" else ART1_ETE,
            "art1": True, "marker": marker}


def _window(code, year, season, as_of):
    base = _rule_for(code, year, season)
    start = base["start"]
    time = base["time"]
    weeks = _DUR_SEM
    applied = []
    rule = {"season": season,
            "source": "ART1" if base["art1"] else "ANNEXE",
            "verbatim": base["verbatim"]}
    if base["art1"]:
        if season == "hiver":
            rule["second_wednesday"] = _iso(base["marker"])
            rule["advanced"] = base["marker"].day > 12
        else:
            rule["last_wednesday"] = _iso(base["marker"])
            rule["advanced"] = base["marker"].day > 28
    conflict = None
    overridden = False
    # derogations annuelles
    for key, dg in sorted(DEROGATIONS.items()):
        if dg["year"] != year or dg["season"] != season:
            continue
        if not dg["in_scope"](code, base["art1"], season):
            continue
        if dg["effect"] == "START":
            overridden = True
            if code == "57" and "moselle" in dg:
                start = dg["moselle"]["start"]
                applied.append({
                    "arrete": dg["arrete"], "source": dg["source"],
                    "effect": ("Moselle seule — « Pour la Moselle, "
                               "la date et l'heure de début des soldes "
                               "d'été sont fixées au 26 juin 2021 à 8 "
                               "heures du matin »"),
                })
                time = "08:00"
                continue
            start = dg["start"]
            time = dg.get("time", time)
            applied.append({"arrete": dg["arrete"], "source": dg["source"],
                            "effect": dg["verbatim"]})
        elif dg["effect"] == "DURATION":
            weeks = dg["weeks"]
            applied.append({"arrete": dg["arrete"], "source": dg["source"],
                            "effect": dg["verbatim"]})
    # conflit date d'ouverture EST : premier jour ouvré, DEUX lectures —
    # jugé APRÈS derogations : quand un arrêté nomme la date (2021),
    # l'ambiguïté du mot ne joue plus, le conflit disparaît.
    if (not overridden and base["kind"] == "ANNEXE" and
            base["verbatim"].endswith("premier jour ouvré du mois de "
                                      "janvier")):
        alt = _premier_jour_ouvrable(year)
        if alt != start:
            conflict = {
                "class": "PREMIER_JOUR_OUVRE_AMBIGUOUS",
                "why": ("l'annexe dit « premier jour ouvré du mois de "
                        "janvier » sans definir le mot ; lecture "
                        "stricte OUVRÉ (lun-ven hors 1er férié) retient "
                        "le début ci-dessus ; lecture OUVRABLE "
                        "(lun-sam) donnerait le début alternatif"),
                "primary_start": _iso(start),
                "alternative_start": _iso(alt),
                "alternative_end": _iso(alt + _td(days=weeks * 7 - 1)),
                "press": ("tpeactu, france.fr, voici impriment le "
                          "samedi ; codespromoplus nomme le conflit « "
                          "selon que le samedi compte ou non » — les "
                          "deux fenêtres voyagent, le mot de l'arrêté "
                          "est ouvré : la lecture stricte est première"),
            }
    end = start + _td(days=weeks * 7 - 1)
    out = {
        "season": season,
        "start": _iso(start),
        "start_weekday": _WEEK[start.weekday()],
        "start_time": time,
        "end_inclusive": _iso(end),
        "duration_weeks": weeks,
        "rule": rule,
        "derogations_applied": applied,
        "conflict": conflict,
    }
    if as_of:
        if as_of < start:
            out["status"] = "UPCOMING"
            out["days_to_start"] = (start - as_of).days
        elif as_of > end:
            out["status"] = "ENDED"
            out["days_since_end"] = (as_of - end).days
        else:
            out["status"] = "IN_PROGRESS"
            out["days_left"] = (end - as_of).days
    return out


_TERR_LABEL = {
    "FR_METRO": "France métropolitaine / droit commun (art. 1er)",
    "06": "Alpes-Maritimes (06)",
    "2A": "Corse-du-Sud (2A)", "2B": "Haute-Corse (2B)",
    "54": "Meurthe-et-Moselle (54)", "55": "Meuse (55)",
    "57": "Moselle (57)", "66": "Pyrénées-Orientales (66)",
    "88": "Vosges (88)", "971": "Guadeloupe (971)",
    "972": "Martinique (972)", "973": "Guyane (973)",
    "974": "La Réunion (974)", "975": "Saint-Pierre-et-Miquelon (975)",
    "976": "Mayotte (976)", "977": "Saint-Barthélemy (977)",
    "978": "Saint-Martin (978)",
}


def soldes_window(year, territory="metropole", season=None, as_of=None):
    try:
        year = int(year)
    except (TypeError, ValueError):
        raise SoldesError("year", "not an integer year: %r" % (year,),
                          "expected integer >= 2020")
    if year < _GATE.year:
        raise SoldesError(
            "year",
            "%d refuse : l'arrete du 27 mai 2019 « entre en vigueur "
            "le 1er janvier 2020 » (art. 4) — avant 2020 les dates "
            "relevaient d'arretes prefectoraux annuels, non rejoues "
            "dans la table" % (year,),
            "year >= 2020")
    if year > 9999:
        raise SoldesError("year", "not an ISO-representable year: %d"
                          % (year,), "2020 <= year <= 9999")
    codes = _territory(territory)
    want = _season(season)
    seasons = ["hiver", "ete"] if want == "both" else [want]
    a = _parse_as_of(as_of) if as_of else None
    windows = []
    for code in codes:
        for s in seasons:
            w = _window(code, year, s, a)
            if len(codes) > 1:
                w["territory_code"] = code
            windows.append(w)
    return {
        "year": year,
        "territory": " + ".join(_TERR_LABEL.get(c, c) for c in codes),
        "windows": windows,
        "duration_rule": ART3,
        "table_version": SOLDES_TABLE_VERSION,
    }
