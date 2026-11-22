# FINDINGS-V22+V22b — LA FRONTIÈRE A-T-ELLE LE MÊME MAL ? (2026-11-22)

L'objection finale après douze bancs locaux 0,5–8B : « GPT-5/Claude
ne font pas ces erreurs ». Réponse mesurée en dollars, trois familles
frontière (claude-haiku-4.5, gpt-5-mini, deepseek-v3.2), trois bras
(NU / CODE écrit par le modèle exécuté en sandbox / FICHE prod
B_routée de F5 rejouée), 7 problèmes à chaîne gelés de v16, prix $/M
figés dans le harnais AVANT la première cellule. COÛT (corrigé le
22-11 au soir : la première ligne clamait « < 0,02 $ » sans avoir
été sommée — la somme recalculée ligne à ligne, tokens × tarifs
gelés : V22 = 0,0344 $, V22b = 0,0637 $, total 0,098 $ ; relevé
par ligne dans les jsonls — une publication de prix se prouve,
sinon c'est du slogan).

## La matrice (jugée v2 — voir l'incident du juge plus bas)

| modèle | N nu | C code | F fiche |
|---|---|---|---|
| gpt-5-mini | **7/7** | 7/7 (877 t/juste) | 7/7 (814 t/juste) |
| haiku-4.5 | 3/7 | 7/7 (199 t) | 6/7 |
| deepseek-v3.2 | **0/7** | 7/7 (190 t) | 6/7 |

## Verdicts des prédictions gelées

- **P1 VRAIE, mais c'est un transport-modèle, pas une loi de taille** :
  gpt-5-mini enterre les chaînes à mains nues (7/7) ; deepseek-v3.2,
  un modèle DEUX FOIS plus lourd et moins quantifié, fait 0/7 nu —
  exactement le score du 0.5B local. La frontière n'est pas une
  classe : l'objection « passe à un gros modèle » ne ferme pas le
  dossier, elle l'ouvre sur une autre variable (la famille, le
  réglage, pas la taille).
- **P2 VRAIE — publiée CONTRE NOUS** : le camp concurrent (le modèle
  écrit du Python) fait 7/7 sur les trois modèles frontière, zéro
  faute sémantique sur ces 7 job-unique. Le bras code marche. Sur
  job unique. C'est le résultat le plus important du banc, et c'est
  celui qui déplace le produit : notre valeur n'est PAS « la
  frontière échoue sans nous » sur l'arithmétique à un coup.
- **P3 FAUSSE** : la fiche rend 6/7 chez haiku et deepseek —
  #14 : un PARSE total (pas de JSON) et une transcription fausse
  (créneau recopié à côté → serveur compute juste sur input faux).
  Le mur de lecture suit la frontière jusque dans le geste le plus
  simple : recopier. 13 réparations nommées sur 21 cellules F :
  le refus-réparateur travaille à l'échelle frontière aussi.
- **P4 FAUSSE** : à l'échelle frontière la fiche n'économise pas les
  tokens (283–814 t/juste contre 190–877 au code). Sa valeur est
  ailleurs : trace pas-à-pas, verrou de cible, refus nommés, sha
  stable — et les classes où le NU et le CODE coûtent plus cher
  qu'eux-mêmes (V22b, ci-dessous).
- **P5 VRAIE après énoncé corrigé** : à créneaux identiques le
  serveur rend le même sha, 7/7 problèmes. Les deux sha distincts
  de #14 venaient d'inputs différents, pas du serveur.

## L'incident du juge (publié, doctrine F5)

`norm_num` amochait la fraction exacte : « 3829/10 » (= 382,90, le
gold) devenait 382910 → deux cellules C injustement FAUX au premier
décompté. Le jsonl brut reste intact ; le rejugement (norm_frac) est
dans score22.py avec sa raison écrite. Sans cette correction, P2
serait tombée FAUSSE sur un artefact de comptage — la gate machine
avait déjà pêché le piège miroir (lire trace[-1] au lieu de
answer[cible] rend le LEFTOVER, pas la cible) : les deux incidents
sont la même leçon, **nommer la quantité qu'on juge**.

## V22b — la répétabilité frontière (70 cellules : 2 modèles C 7/7
× 7 problèmes × 5 repasses à temp 0,7 — le régime réel des agents,
celui de v19 — + 70 POSTs de contrôle serveur)

- **B1 VRAIE, mais lue honnêtement** : 8 paires problème-modèle sur
  14 voient la RÉPONSE CHANGER DE FORME entre repasses (« 240 » vs
  « 240.0 », « 3829/10 » vs « 382.9 »), et gpt-5-mini a rendu une
  queue de float — 776.6000000000000000000000002 pour 776.6 — au
  milieu de ses 35/35 justes. **Zéro erreur numérique** (70/70 dans
  l'oracle) : contrairement aux nains de v19, la frontière ne rate
  pas le job — mais elle ne le rend jamais deux fois PAREIL.
- **B2 VRAIE, c'est le résultat qui porte le produit** : le
  programme est RÉÉCRIT à chaque passe — 4 shas de code distincts
  au moins sur 5 passes pour 7 problèmes/7 chez gpt-5-mini et 6/7
  chez deepseek.
  « 30 jours, même sha » est IMPOSSIBLE côté client frontière,
  même quand tout est juste : ce que tu déploies change de bytes
  chaque jour, et un déploiement qui change de bytes sans changer
  d'avis est un déploiement non auditable.
- **B3 VRAIE sans ombre** : 70/70 POSTs serveur, 1 sha par problème
  (10 repasses × 7 problèmes), 10/10 justes partout. La machine est
  la seule des trois à rendre le même artefact chaque jour.

## Incident d'intendance publié

Le fichier du harnais est arrivé sur disque avec l'en-tête
d'authentification REMPLACÉE par « *** » (masquage de secrets du
canal d'écriture) → deux 401 mystérieux, une fausse piste « clé
tournante ». Leçon outillage : après écriture d'un fichier touchant
un jeton, grep le contenu RÉEL avant de diagnostiquer l'API.

## Verdict global du banc — ce que la thèse devient

1. « Sans nous la frontière échoue » est RETIRÉ du vocabulaire :
   sur job unique, gpt-5-mini fait 7/7 nu et le code tient 7/7
   partout (P1/P2 VRAIES, publiées contre nous).
2. Ce qui survit et se trouve CHIFFRÉ à l'échelle frontière : la
   stabilité de l'artefact (B2 : jamais le même programme deux
   jours de suite ; B3 : nous, si), la garantie (trace, verrou de
   cible, refus nommés — 13 réparations F), les classes où nu et
   code coûtent plus cher qu'eux-mêmes (deepseek 0/7 nu, nains
   locaux 0/14 chaînes).
3. Le routeur (S1-S3 livrés ce lot : /router/plan, /router/apply)
   est la conséquence économique : sur la grammaire fermée, le
   serveur applique SANS AUCUN APPEL LM — le débat frontière est
   contourné, le sha est la réponse.
