# -*- coding: utf-8 -*-
"""soldeslukit — /shop/soldes-lu : les dates LÉGALES des soldes
luxembourgeoises, TABLE DATÉE PAR ACTE — la grammaire ici EST l'acte.

LA DOULEUR, mesurée par la lentille HUMAIN (rank 2 tenu deux cycles) :
le routeur de prod rendait tools:[] sur « soldes luxembourg janvier
2027 » — veto b103 (V_SOLD_OUT porte « luxemb ») + veto b105 : la
requête n'était pas bruyante, elle était MORTE. Nos deux sœurs
refusaient le Luxembourg PAR NOM en disant « en file » ; le relai
existait, la destination manquait.

LE DROIT, rejoué VERBATIM legilux le 25-11-2026 (oracle tracé main
avant le module, scratch/oracle_g110.py) : loi du 23 décembre 2016
sur les ventes en soldes et sur trottoir (Mém. A-267, publié
27-12-2016, EN VIGUEUR 31-12-2016), art. 1er, PARAGRAPHE 4 :
« Les ventes en solde ne peuvent avoir lieu que deux fois par an,
chaque période de soldes ne pouvant excéder la durée d'un mois au
maximum. Un règlement grand-ducal fixe CHAQUE ANNÉE les dates
d'ouverture et de clôture des deux périodes de vente en solde. »
— PAS DE FORMULE. Le Luxembourg n'a ni le mercredi français, ni la
clause du dimanche belge : chaque période vient d'un règlement
grand-ducal signé. Le calcul ne remplace jamais l'acte ; pas d'acte,
pas de date — l'extrapolation est le mensonge que ce module refuse
(précédent parcelmonitor). DIX actes rejoués (2017→2026) couvrent les
années 2018..2027 ; chaque date de la table est calée sur le
calendrier RÉEL par l'oracle — les deux seules dérogations sont des
COQUILLES D'ÉTAT NOMMÉES :

  * RGD 17-sept-2017 (Mém. A-807) imprimait l'ouverture des soldes de
    l'été 2018 « samedi, le 29 juin 2018 » — ce jour était un
    VENDREDI. RECTIFICATIF Mém. A n° 928 de 2017 : le point 2 est
    remplacé, « vendredi, le 29 juin 2018 » — MÊME DATE, le nom de
    jour seul corrige. Le module rend le vendredi (calendrier) et
    porte la rectification en RECTIFICATION, jamais gommée.
  * RGD 05-oct-2022 (Mém. A-511) imprimait « clôture : samedi, le 23
    juillet 2023 inclus » — le 23-07-2023 était un DIMANCHE. Le
    RECTIFICATIF Mém. A n° 96 de 2023 (publié 24-02-2023) remplace la
    BORNE ELLE-MÊME : « samedi, le 22 juillet 2023 inclus ». La
    douleur est inversée de la belge : la presse (rtl.lu, actu.fr,
    wort.lu) et le communiqué du gouvernement du 30-sept-2022 disaient
    22 depuis le début — c'est le Journal officiel qui s'était trompé
    en recopiant, et qui s'est rectifié quatre mois plus tard. Quiconque
    cite le Mémorial A-511 sans le A-96 contredit l'État.

LA CHAÎNE 2021 — version LU du recâblage corona, DIFFÉRENTE de la
belge, trois actes dont un mort : RGD 08-oct-2020 (Mém. A-819) fixait
l'hiver 2020/2021 du samedi 2-janv. au samedi 30-janv. ; RGD
30-déc-2020 (Mém. A-1107) l'AJOURNAIT « à une date ultérieure » —
sans date ; RGD 13-janv-2021 (Mém. A-24) ABROGE l'ajournement et
recâble : mercredi 20-janv.-2021 → mercredi 17-févr.-2021 inclus.
Les trois actes voyagent dans la réponse, chacun avec son rôle.

LA DIVERGENCE STRUCTURELLE contre la sœur belge, Nommée : la loi de
2016 ne connaît AUCUNE période d'attente (texte rejoué : zéro
occurrence de « attente » ; la fenêtre publicitaire du septième jour
vivait dans la loi du 30-juil-2002 abrogée — art. 11 de la loi de
2016 l'abroge en entier). Le champ « waiting » de /shop/soldes-be
n'existe PAS ici, et le module le DIT : pas de moyenne, pas d'import.

ANCIEN RÉGIME (gate) : l'hiver 2016/2017 et l'été 2017 furent datés
par le RGD 15-sept-2016 (Mém. A-199, « Acte plus en vigueur ») sous
l'art. 5 de la loi ABROGÉE du 30-juil-2002 — grammaire différente
(fenêtre publicitaire du 7e jour, annexion de fait à l'autre loi).
Dates recopiées du dossier officiel de la Chambre (l'ELI legilux de
cet acte est 404 — la source est Nommée, pas gommée) : hiver
30-déc-2016→28-janv-2017, été 24-juin→22-juil-2017. Refusés par nom
portant leur fait, jamais rendus comme lignes de la table — précédent
D310 (français) et 1991 (belge). Avant 2016 : actes non rejoués,
zéro date prêtée à la mémoire.

L'AVENIR : refusé. Le prochain règlement (hiver 2027/2028 + été 2028)
n'a pas encore de texte publié ; la loi dit « chaque année ». Aucun
précédent de datation ne devient prophétie : la table s'arrête au
RGD 06-juil-2026 (Mém. A-330).

LES RÈGLES QUI VOYAGENT (verbatim art. 1er) : interdiction d'annoncer
ou de vendre sous le terme « solde(s) » HORS des périodes (al. 2) ;
lieux habituels + prix « réellement inférieurs aux prix habituellement
demandés » (al. 3) ; deux fois par an, un mois au maximum (al. 4) —
invariant VÉRIFIÉ ligne à ligne sur les dix actes : aucune période
rejouée ne dépasse 30 jours.

CA EXISTE DEJA : guichet.lu rend la prose à jour, aucune API ; legilux
rend les actes, pas une date-au-demain ; la France et la Belgique ont
leurs outils, qui refusaient le Luxembourg par nom — ce module est la
destination que nos vetos promettaient. Diff : les actes en réponse
datée + les deux rectificatifs joués + la chaîne 2021 à trois actes +
refus daté de l'avenir. Zéro LM, zéro fetch runtime, free tier.
"""

import datetime as _date

WEEK = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday")
WEEK_FR = ("lundi", "mardi", "mercredi", "jeudi", "vendredi",
           "samedi", "dimanche")

SOLDES_LU_TABLE_VERSION = (
    "loi 23-12-2016 art. 1er § 4 + 10 actes legilux rejoués "
    "25-11-2026 (A-807+RECT A-928/2017, A-921/2018, A-728/2019, "
    "A-819+A-1107+A-24/2021, A-765/2021, A-511+RECT A-96/2023, "
    "A-625/2023, A-306/2024, A-327/2025, A-330/2026)")

FIRST_YEAR = 2018
LAST_YEAR = 2027

# ---------------------------------------------------------------- verbatims
ART_1_2 = ("art. 1er al. 2 (loi du 23-12-2016) : « Il est interdit "
           "d'annoncer ou de procéder à une vente en utilisant le terme "
           "«solde(s)» soit isolément, soit avec d'autres mots, ainsi "
           "que toute dénomination ou présentation suggérant une vente "
           "en solde en dehors des cas et conditions prévus au présent "
           "article. »")
ART_1_3 = ("art. 1er al. 3 : « La vente en solde doit avoir lieu dans "
           "les locaux où les biens en question sont habituellement "
           "vendus. Les prix des biens offerts en solde doivent être "
           "réellement inférieurs aux prix habituellement demandés par "
           "le vendeur pour les mêmes biens. »")
ART_1_4 = ("art. 1er al. 4 : « Les ventes en solde ne peuvent avoir "
           "lieu que deux fois par an, chaque période de soldes ne "
           "pouvant excéder la durée d'un mois au maximum. Un "
           "règlement grand-ducal fixe chaque année les dates "
           "d'ouverture et de clôture des deux périodes de vente en "
           "solde. »")
NO_WAITING = (
    "la loi luxembourgeoise du 23-12-2016 ne définit AUCUNE période "
    "d'attente (texte rejoué 25-11-2026 : zéro occurrence d'« attente » "
    "ni du septième jour) — divergence structurelle contre la Belgique "
    "(art. VI.29 CDE, attente d'un mois) ; l'ancienne fenêtre "
    "publicitaire du 7e jour vivait dans la loi du 30-juil-2002, "
    "ABROGÉE en entier par l'art. 11 de la loi de 2016. Le champ "
    "« waiting » de /shop/soldes-be n'existe pas ici : pas de "
    "moyenne, pas d'import.")
ANCIEN_REGIME = (
    "l'hiver 2016/2017 (vendredi 30-déc-2016 → samedi 28-janv-2017) et "
    "l'été 2017 (samedi 24-juin → samedi 22-juil-2017) furent fixés par "
    "le règlement grand-ducal du 15-sept-2016 (Mém. A-199 de 2016, "
    "« Acte plus en vigueur », publié 21-09-2016) sur base de l'art. 5 "
    "de la loi du 30-juil-2002 — abrogée par l'art. 11 de la loi du "
    "23-déc-2016. Grille différente (fenêtre publicitaire du 7e jour) : "
    "refusés par nom portant leur fait, pas des lignes de cette table. "
    "Dates recopiées du dossier officiel de la Chambre (Chambre des "
    "Députés, compilation du Mémorial A-199 — l'ELI legilux de cet "
    "acte renvoie 404, la source est nommée) ; avant 2016 : actes non "
    "rejoués, zéro date prêtée à la mémoire.")
FUTURE_NOTE = (
    "dernier acte rejoué : règlement grand-ducal du 06-juil-2026 "
    "(Mém. A-330 de 2026), qui couvre l'hiver 2026/2027 et l'été 2027. "
    "La loi du 23-déc-2016 art. 1er § 4 renvoie les dates à un "
    "règlement CHAQUE ANNÉE : l'acte suivant n'existe pas encore, et "
    "ici la grammaire EST l'acte — zéro extrapolation (précédent "
    "parcelmonitor). Surveiller le Mémorial A.")

# ---------------------------------------------------------------- la table
# année -> saisons ; chaque borne = (iso, label-imprimé-rectifié)
# source = ELI legilux ; rectification / chaîne portées à la ligne.
def _t(iso):
    return _date.date.fromisoformat(iso)


ACTES = {
    2018: {
        "hiver": {
            "label": "hiver 2017/2018",
            "start": "2017-12-29", "end": "2018-01-27",
            "act": {"date": "2017-09-17",
                    "memorial": "Mémorial A n° 807 de 2017",
                    "source": "legilux: eli/etat/leg/rgd/2017-09-17/a807",
                    "verbatim": "début : vendredi, le 29 décembre 2017, "
                                "clôture : samedi, le 27 janvier 2018 "
                                "inclus."},
            "print_matches": True},
        "ete": {
            "label": "été 2018",
            "start": "2018-06-29", "end": "2018-07-28",
            "act": {"date": "2017-09-17",
                    "memorial": "Mémorial A n° 807 de 2017",
                    "source": "legilux: eli/etat/leg/rgd/2017-09-17/a807",
                    "verbatim": "début : vendredi, le 29 juin 2018, "
                                "clôture : samedi, le 28 juillet 2018 "
                                "inclus. (texte RECTIFIÉ — voir "
                                "rectification)"},
            "print_matches": False,
            "rectification": {
                "type": "nom_de_jour_seul",
                "memorial": "Mémorial A n° 928 de 2017",
                "source": "legilux: eli/etat/leg/rect/2017-09-17/a928",
                "published_as": "Au Journal officiel N° 807 du 20 "
                                "septembre 2017, le texte de l'article "
                                "1er, point 2, est à remplacer",
                "original_imprime": "samedi, le 29 juin 2018",
                "rectifie_en": "vendredi, le 29 juin 2018",
                "note": "la date ne bouge pas : le 29-06-2018 était un "
                        "vendredi, l'acte imprimait « samedi ». Le "
                        "RECTIFICIF remplace le NOM DE JOUR. Le module "
                        "rend le vendredi (calendrier) et porte la "
                        "coquille nommée."}},
    },
    2019: {
        "hiver": {"label": "hiver 2018/2019",
                  "start": "2018-12-29", "end": "2019-01-26",
                  "act": {"date": "2018-10-04",
                          "memorial": "Mémorial A n° 921 de 2018",
                          "source": "legilux: eli/etat/leg/rgd/"
                                    "2018-10-04/a921",
                          "verbatim": "début : samedi, le 29 décembre "
                                      "2018, clôture : samedi, le 26 "
                                      "janvier 2019 inclus."},
                  "print_matches": True},
        "ete": {"label": "été 2019",
                "start": "2019-06-28", "end": "2019-07-27",
                "act": {"date": "2018-10-04",
                        "memorial": "Mémorial A n° 921 de 2018",
                        "source": "legilux: eli/etat/leg/rgd/"
                                  "2018-10-04/a921",
                        "verbatim": "début : vendredi, le 28 juin "
                                    "2019, clôture : samedi, le 27 "
                                    "juillet 2019 inclus."},
                "print_matches": True},
    },
    2020: {
        "hiver": {"label": "hiver 2019/2020",
                  "start": "2020-01-02", "end": "2020-01-25",
                  "act": {"date": "2019-10-26",
                          "memorial": "Mémorial A n° 728 de 2019",
                          "source": "legilux: eli/etat/leg/rgd/"
                                    "2019-10-26/a728",
                          "verbatim": "début : jeudi, le 2 janvier "
                                      "2020, clôture : samedi, le 25 "
                                      "janvier 2020 inclus."},
                  "print_matches": True},
        "ete": {"label": "été 2020",
                "start": "2020-06-26", "end": "2020-07-25",
                "act": {"date": "2019-10-26",
                        "memorial": "Mémorial A n° 728 de 2019",
                        "source": "legilux: eli/etat/leg/rgd/"
                                  "2019-10-26/a728",
                        "verbatim": "début : vendredi, le 26 juin "
                                    "2020, clôture : samedi, le 25 "
                                    "juillet 2020 inclus."},
                "print_matches": True},
    },
    2021: {
        "hiver": {"label": "hiver 2020/2021",
                  "start": "2021-01-20", "end": "2021-02-17",
                  "act": {"date": "2021-01-13",
                          "memorial": "Mémorial A n° 24 de 2021",
                          "source": "legilux: eli/etat/leg/rgd/"
                                    "2021-01-13/a24",
                          "verbatim": "les dates d'ouverture et de "
                                      "clôture de la période des "
                                      "soldes de l'hiver 2020/2021 "
                                      "sont remplacées comme suit : "
                                      "début : mercredi, le 20 janvier "
                                      "2021, clôture : mercredi, le 17 "
                                      "février 2021 inclus."},
                  "print_matches": True,
                  "chain": [
                      {"role": "fixe",
                       "date": "2020-10-08",
                       "memorial": "Mémorial A n° 819 de 2020",
                       "source": "legilux: eli/etat/leg/rgd/"
                                 "2020-10-08/a819",
                       "verbatim": "début : samedi, le 2 janvier "
                                   "2021, clôture : samedi, le 30 "
                                   "janvier 2021 inclus.",
                       "status": "modifié par le RGD 13-01-2021"},
                      {"role": "ajourne_sans_date",
                       "date": "2020-12-30",
                       "memorial": "Mémorial A n° 1107 de 2020",
                       "source": "legilux: eli/etat/leg/rgd/"
                                 "2020-12-30/a1107",
                       "verbatim": "est reportée à une date "
                                   "ultérieure.",
                       "status": "ABROGÉ par le RGD du 13-01-2021 "
                                 "(art. 2)",
                       "note": "l'ajournement ne portait AUCUNE date "
                               "— zéro date inventée ; l'acte vit "
                               "dans la chaîne comme acte mort, "
                               "nommé."},
                      {"role": "recable",
                       "date": "2021-01-13",
                       "memorial": "Mémorial A n° 24 de 2021",
                       "source": "legilux: eli/etat/leg/rgd/"
                                 "2021-01-13/a24",
                       "verbatim": "début : mercredi, le 20 janvier "
                                   "2021, clôture : mercredi, le 17 "
                                   "février 2021 inclus.",
                       "status": "en vigueur"}],
                  "divergence_be": "la chaîne belge 2021 fut "
                                   "report→prolongation par LOI "
                                   "(VI.25 § 2 borne le Roi) ; la "
                                   "chaîne LU est un AJOURNEMENT sans "
                                   "date PUIS ABROGÉ, remplacé par un "
                                   "second RGD — même famille, autres "
                                   "grammaires."},
        "ete": {"label": "été 2021",
                "start": "2021-06-26", "end": "2021-07-24",
                "act": {"date": "2020-10-08",
                        "memorial": "Mémorial A n° 819 de 2020",
                        "source": "legilux: eli/etat/leg/rgd/"
                                  "2020-10-08/a819",
                        "verbatim": "début : samedi, le 26 juin 2021, "
                                    "clôture : samedi, le 24 juillet "
                                    "2021 inclus."},
                "print_matches": True},
    },
    2022: {
        "hiver": {"label": "hiver 2021/2022",
                  "start": "2022-01-03", "end": "2022-01-29",
                  "act": {"date": "2021-11-02",
                          "memorial": "Mémorial A n° 765 de 2021",
                          "source": "legilux: eli/etat/leg/rgd/"
                                    "2021-11-02/a765",
                          "verbatim": "début : lundi, le 3 janvier "
                                      "2022, clôture : samedi, le 29 "
                                      "janvier 2022 inclus."},
                  # le 1er-02 était un samedi, le 2 un dimanche :
                  # l'acte a glissé au lundi 3 — sans clause écrite,
                  # par l'acte lui-même. Consigné.
                  "print_matches": True},
        "ete": {"label": "été 2022",
                "start": "2022-06-24", "end": "2022-07-23",
                "act": {"date": "2021-11-02",
                        "memorial": "Mémorial A n° 765 de 2021",
                        "source": "legilux: eli/etat/leg/rgd/"
                                  "2021-11-02/a765",
                        "verbatim": "début : vendredi, le 24 juin "
                                    "2022, clôture : samedi, le 23 "
                                    "juillet 2022 inclus."},
                "print_matches": True},
    },
    2023: {
        "hiver": {"label": "hiver 2022/2023",
                  "start": "2023-01-02", "end": "2023-01-28",
                  "act": {"date": "2022-10-05",
                          "memorial": "Mémorial A n° 511 de 2022",
                          "source": "legilux: eli/etat/leg/rgd/"
                                    "2022-10-05/a511",
                          "verbatim": "début : lundi, le 2 janvier "
                                      "2023, clôture : samedi, le 28 "
                                      "janvier 2023 inclus."},
                  "print_matches": True},
        "ete": {"label": "été 2023",
                "start": "2023-06-24", "end": "2023-07-22",
                "act": {"date": "2022-10-05",
                        "memorial": "Mémorial A n° 511 de 2022 "
                                    "(texte RECTIFIÉ — voir "
                                    "rectification)",
                        "source": "legilux: eli/etat/leg/rgd/"
                                  "2022-10-05/a511",
                        "verbatim": "début : samedi, le 24 juin 2023, "
                                    "clôture : samedi, le 22 juillet "
                                    "2023 inclus. (borne issue du "
                                    "RECTIFICATIF A-96)"},
                "print_matches": False,
                "rectification": {
                    "type": "date_elle_meme",
                    "memorial": "Mémorial A n° 96 de 2023 (publié "
                                "24-02-2023)",
                    "source": "legilux: eli/etat/leg/rect/"
                              "2022-10-05/a96",
                    "original_imprime": "clôture : samedi, le 23 "
                                        "juillet 2023 inclus",
                    "rectifie_en": "clôture : samedi, le 22 juillet "
                                   "2023 inclus",
                    "note": "le 23-07-2023 était un DIMANCHE : "
                            "l'acte publié s'était trompé, la presse "
                            "(rtl.lu, actu.fr, wort.lu) et le "
                            "communiqué du gouvernement du "
                            "30-09-2022 disaient 22 depuis le début. "
                            "Douleur INVERSÉE de la belge : ici "
                            "c'est le Journal officiel qui rendait "
                            "la fausse borne ; quiconque cite A-511 "
                            "sans A-96 contredit l'État. L'acte "
                            "rectifié gouverne ; l'original voyage "
                            "étiqueté."}},
    },
    2024: {
        "hiver": {"label": "hiver 2023/2024",
                  "start": "2024-01-02", "end": "2024-01-27",
                  "act": {"date": "2023-09-28",
                          "memorial": "Mémorial A n° 625 de 2023",
                          "source": "legilux: eli/etat/leg/rgd/"
                                    "2023-09-28/a625",
                          "verbatim": "début : mardi, le 2 janvier "
                                      "2024, clôture : samedi, le 27 "
                                      "janvier 2024 inclus."},
                  "print_matches": True},
        "ete": {"label": "été 2024",
                "start": "2024-06-24", "end": "2024-07-20",
                "act": {"date": "2023-09-28",
                        "memorial": "Mémorial A n° 625 de 2023",
                        "source": "legilux: eli/etat/leg/rgd/"
                                  "2023-09-28/a625",
                        "verbatim": "début : lundi, le 24 juin 2024, "
                                    "clôture : samedi, le 20 juillet "
                                    "2024 inclus."},
                # Fête nationale (24 juin, lundi en 2024) comme borne
                # d'ouverture — l'acte ne le dit pas, le module ne
                # le DEVINE pas : consigné dans le docstring du test,
                # absent de la réponse.
                "print_matches": True},
    },
    2025: {
        "hiver": {"label": "hiver 2024/2025",
                  "start": "2025-01-02", "end": "2025-01-25",
                  "act": {"date": "2024-07-23",
                          "memorial": "Mémorial A n° 306 de 2024",
                          "source": "legilux: eli/etat/leg/rgd/"
                                    "2024-07-23/a306",
                          "verbatim": "début : jeudi, le 2 janvier "
                                      "2025, clôture : samedi, le 25 "
                                      "janvier 2025 inclus."},
                  "print_matches": True},
        "ete": {"label": "été 2025",
                "start": "2025-06-27", "end": "2025-07-26",
                "act": {"date": "2024-07-23",
                        "memorial": "Mémorial A n° 306 de 2024",
                        "source": "legilux: eli/etat/leg/rgd/"
                                  "2024-07-23/a306",
                        "verbatim": "début : vendredi, le 27 juin "
                                    "2025, clôture : samedi, le 26 "
                                    "juillet 2025 inclus."},
                "print_matches": True},
    },
    2026: {
        "hiver": {"label": "hiver 2025/2026",
                  "start": "2026-01-02", "end": "2026-01-31",
                  "act": {"date": "2025-07-24",
                          "memorial": "Mémorial A n° 327 de 2025",
                          "source": "legilux: eli/etat/leg/rgd/"
                                    "2025-07-24/a327",
                          "verbatim": "début : vendredi, le 2 janvier "
                                      "2026, clôture : samedi, le 31 "
                                      "janvier 2026 inclus."},
                  "print_matches": True},
        "ete": {"label": "été 2026",
                "start": "2026-06-24", "end": "2026-07-19",
                "act": {"date": "2025-07-24",
                        "memorial": "Mémorial A n° 327 de 2025",
                        "source": "legilux: eli/etat/leg/rgd/"
                                  "2025-07-24/a327",
                        "verbatim": "début : mercredi, le 24 juin "
                                    "2026, clôture : dimanche, le 19 "
                                    "juillet 2026 inclus."},
                # la borne close tombe un DIMANCHE et l'acte le dit
                # lui-même — LU n'a pas la pudeur du dimanche belge,
                # elle a des actes. Consigné par le fait, pas par la
                # règle : print_matches est VRAI ici.
                "print_matches": True},
    },
    2027: {
        "hiver": {"label": "hiver 2026/2027",
                  "start": "2027-01-02", "end": "2027-01-30",
                  "act": {"date": "2026-07-06",
                          "memorial": "Mémorial A n° 330 de 2026",
                          "source": "legilux: eli/etat/leg/rgd/"
                                    "2026-07-06/a330",
                          "verbatim": "début : samedi, le 2 janvier "
                                      "2027, clôture : samedi, le 30 "
                                      "janvier 2027 inclus."},
                  "print_matches": True},
        "ete": {"label": "été 2027",
                "start": "2027-06-26", "end": "2027-07-24",
                "act": {"date": "2026-07-06",
                        "memorial": "Mémorial A n° 330 de 2026",
                        "source": "legilux: eli/etat/leg/rgd/"
                                  "2026-07-06/a330",
                        "verbatim": "début : samedi, le 26 juin 2027, "
                                    "clôture : samedi, le 24 juillet "
                                    "2027 inclus."},
                "print_matches": True},
    },
}


class SoldesLuError(Exception):
    def __init__(self, field, message, expected):
        Exception.__init__(self, message)
        self.field = field
        self.message = message
        self.expected = expected


# ------------------------------------------------------------------ fermetés
_LU = ("luxembourg", "luxembourg", "lux", "lëtzebuerg",
       "letzebuerg", "groussherzogtum", "grand-duche",
       "grand-duché", "esch", "esch-sur-alzette", "esch sur alzette",
       "wiltz", "diekirch", "grevenmacher", "vianden", "clervaux",
       "luxembourg-ville", "luxembourg ville")
_REFUSE_NOMMES = {
    "france": ("la France suit l'arrete francais du 27-05-2019 "
               "(deuxieme mercredi, quatre semaines, annexe de "
               "departements) — voir /shop/soldes-window"),
    "belgique": ("la Belgique suit le Livre VI belge (art. VI.25 CDE, "
                 "clause du dimanche, attente d'un mois) — voir "
                 "/shop/soldes-be"),
}
_REFUSE_GEN = (
    "suisse", "suiss", "quebe", "canad", "ontario", "montreal",
    "royaume", "united", "kingdom", "england", "scotland", "wales",
    "irlande", "irish", "dublin", "espag", "italia", "portug",
    "brasil", "brazil", "bresil", "etats", "unis", "usa", "amerique",
    "maroc", "algerie", "tunisie", "senegal", "cote divoire",
    "deutschland", "germany", "niederlande", "holland", "genev",
    "zurich", "amsterdam", "berlin", "madrid", "lisbon", "vienne",
)
_SEASONS = {"hiver": "hiver", "winter": "hiver", "wanter": "hiver",
            "hivernale": "hiver", "hyber": "hiver",
            "zomer": "ete", "ete": "ete", "été": "ete",
            "summer": "ete", "estival": "ete", "sommen": "ete",
            "inverno": "hiver", "verao": "ete",
            "both": "both", "les deux": "both", "all": "both",
            "toutes": "both", "tous": "both"}


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
        elif ch in "ùûüç":
            ch = {"ù": "u", "û": "u", "ü": "u", "ç": "c"}[ch]
        elif ord(ch) > 127:
            ch = "?"
        out.append(ch)
    s = "".join(out)
    return " ".join(s.replace("/", " ").split())


def _parse_as_of(s):
    try:
        return _date.date.fromisoformat(str(s))
    except Exception:
        raise SoldesLuError("as_of", "not an ISO calendar date: %r"
                            % (s,), "expected 'YYYY-MM-DD'")


def _territory(raw):
    t = _fold(raw if raw is not None else "luxembourg")
    if t in _LU or t.startswith("luxemb"):
        return
    for token, why in _REFUSE_NOMMES.items():
        if t == token or t.startswith(token):
            raise SoldesLuError(
                "territory",
                "%r refuse par nom portant son fait : %s ; la table ne "
                "rejoue QUE le reglement grand-ducal luxembourgeois"
                % (raw, why),
                "un territoire luxembourgeois (liste closee)")
    for token in _REFUSE_GEN:
        if token in t:
            raise SoldesLuError(
                "territory",
                "%r refuse par nom portant son fait : calendrier "
                "etranger non rejoue — la table ne dit AUCUNE date "
                "hors reglement grand-ducal luxembourgeois" % (raw,),
                "un territoire luxembourgeois (liste closee)")
    raise SoldesLuError("territory", "not in the closed table: %r"
                        % (raw,), "luxembourg (liste closee)")


def _season(raw):
    s = _fold(raw if raw is not None else "both")
    if s in _SEASONS:
        return _SEASONS[s]
    raise SoldesLuError(
        "season", "unknown season %r — attendu hiver|ete|both (liste "
        "closee)" % (raw,), "hiver | ete | both")


def _fr_wd(d):
    return WEEK_FR[d.weekday()]


def _window(year, season, as_of):
    w = ACTES[year][season]
    start, end = _t(w["start"]), _t(w["end"])
    length = (end - start).days + 1
    out = {"season": season, "label": w["label"],
           "start": w["start"], "start_weekday": _fr_wd(start),
           "end": w["end"], "end_weekday": _fr_wd(end),
           "end_included": True, "length_days": length,
           "basis": "ACTE — la date vient du reglement grand-ducal, "
                    "aucune formule ne l'a calculee",
           "act": dict(w["act"]),
           "print_matches_calendar": bool(w["print_matches"])}
    if "rectification" in w:
        out["rectification"] = dict(w["rectification"])
    if "chain" in w:
        out["acts_chain"] = [dict(c) for c in w["chain"]]
        out["divergence_be"] = w["divergence_be"]
    if as_of is not None:
        if as_of < start:
            out["status"] = "UPCOMING"
            out["days_to_start"] = (start - as_of).days
        elif as_of <= end:
            out["status"] = "IN_PROGRESS"
            out["days_left"] = (end - as_of).days
        else:
            out["status"] = "ENDED"
            out["days_since_end"] = (as_of - end).days
    return out


def soldes_lu(year, territory=None, season=None, as_of=None):
    try:
        year = int(year)
    except (TypeError, ValueError):
        raise SoldesLuError("year", "not an integer year: %r" % (year,),
                            "expected integer 2018..2027 (years "
                            "bracketed by replayed actes)")
    _territory(territory)
    want = _season(season)
    a = _parse_as_of(as_of) if as_of else None
    if year <= 2017:
        if year == 2017:
            raise SoldesLuError(
                "year",
                "2017 refuse : l'hiver 2016/2017 et l'ete 2017 furent "
                "fixes par le RGD du 15-sept-2016 sous la loi "
                "abrogee du 30-juil-2002 — ancien regime, grille "
                "differente (fenetre publicitaire du 7e jour), pas "
                "une ligne de cette table : %s ; premiere saison "
                "rejouee par un acte de la loi de 2016 : hiver "
                "2017/2018 (RGD 17-sept-2017)" % ANCIEN_REGIME,
                "year >= 2018 (10 actes RGD 2017-09-17 -> 2026-07-06)")
        raise SoldesLuError(
            "year",
            "%d refuse : avant le 31-12-2016 (entree en vigueur de la "
            "loi du 23-dec-2016), les dates se fixaient sous la loi "
            "du 30-juil-2002 art. 5, abrogee — actes non rejoues au-"
            "dela du 15-sept-2016, zero date pretee a la memoire ; "
            "premier acte de la table : RGD 17-sept-2017 (Mem. A-807) "
            "%s" % (year, ANCIEN_REGIME),
            "year >= 2018 (10 actes RGD 2017-09-17 -> 2026-07-06)")
    if year > LAST_YEAR:
        raise SoldesLuError(
            "year",
            "%d refuse : aucun reglement grand-ducal rejoue ne date "
            "les soldes de cette annee — la loi du 23-dec-2016 art. "
            "1er § 4 renvoie les dates a un reglement CHAQUE ANNEE : "
            "ici la grammaire EST l'acte, et l'acte n'existe pas "
            "encore. %s" % (year, FUTURE_NOTE),
            "year <= %d (dernier acte rejoue : %s)"
            % (LAST_YEAR, "RGD 06-juil-2026, Mem. A-330"))
    seasons = ["hiver", "ete"] if want == "both" else [want]
    return {
        "year": year,
        "territory": "Luxembourg — loi du 23-12-2016 art. 1er § 4 : un "
                     "reglement grand-ducal fixe CHAQUE ANNEE les "
                     "dates ; TABLE DATEE PAR ACTE, zero formule",
        "windows": [_window(year, s, a) for s in seasons],
        "no_waiting_period": NO_WAITING,
        "prohibition_hors_periode": ART_1_2,
        "conditions": ART_1_3,
        "rule": ART_1_4,
        "cap_check": "invariant « un mois au maximum » verifie ligne a "
                     "ligne sur les 10 actes rejoues : aucune periode "
                     "ne depasse 30 jours (max table : 30, min : 24)",
        "coverage": {"first_act": "RGD 17-sept-2017 (Mém. A-807) + "
                                  "RECTIFICATIF A-928",
                     "last_act": "RGD 06-juil-2026 (Mém. A-330)",
                     "years": "2018..2027",
                     "refused": {"ancien_regime": "≤ 2017 — saisons "
                                                  "datées sous la loi "
                                                  "du 30-07-2002 "
                                                  "(abrogée, art. 11 "
                                                  "de 2016) : refus "
                                                  "par nom portant "
                                                  "leur fait",
                                 "avenir": "≥ 2028 — pas d'acte, pas "
                                           "de date, jamais de "
                                           "prophétie"}},
        "table_version": SOLDES_LU_TABLE_VERSION,
    }
