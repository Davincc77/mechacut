# FINDINGS-V21 — face-à-face ComputeFirst (2026-11-22, coût : 0 $ des deux côtés)

La question : sur la zone commune de leurs 859 outils, rendent-ils les
mêmes bytes que nous — et que font-ils sur ce qu'ils n'ont PAS ?
Harnais et golds gelés dans `bench/run21.py` AVANT la première cellule
(commit 0200acb, poussé.. Un incident de juge en cours de route,
archivé comme chez nous : notre première passe de G3 comptait un mur
de prix comme une erreur de calcul — la ligne boguée est dans
`results_v21.jsonl.bug-harness-tiers`, la cellule rejouée ci-dessous.

## La matrice (12 cellules)

| cellule | tâche | eux | nous | verdict |
|---|---|---|---|---|
| G1 | sha256("abc") | == gold | == gold | **accord byte à byte** |
| G2 | dedupe CSV (doublons, ordre) | == gold | == gold | **accord** |
| G3 | IBAN FR classique | `valid:true` **gratuit**, contrat versionné (`swift-iban-registry-103`) | `valid`… mais derrière x402 ($0,0005) | **TIER-DIVERGENCE : d'accord sur la valeur, division sur le prix** |
| G4 | compteur jours ouvrés avec fériés | 9 (correct) | **PAS DE ROUTE** | lacune nôtre, publiée |
| G5-G8 | DST sauté · toutes lettres FR · % du reste · ICS/cron | **4/4 ABSTENTION** (search < seuil, zéro exécution inventée) | 4/4 exact (N5-N8) | leur honnêteté vérifiée |

## Verdicts des prédictions gelées

- **P1 — confirmée à la valeur, réfutée au portefeuille** : là où nos
  deux suites ont l'outil gratuit, les bytes sont les mêmes (G1, G2).
  Sur G3, ils gagnent l'appel **sans clé ni portefeuille** — notre
  validateur IBAN est payé, le leur est libre. Ce n'est pas une
  erreur de calcul de notre part, c'est un **positionnement de tier** :
  publié tel quel. Le public qui compare verra un gratuit et un 402.
- **P2 — VRAIE** (9/9). Et P4 l'avait annoncé dans l'en-tête avant
  course : cette lacune était déjà écrite (notre `business_days`
  DÉPLACE, ne COMPTE pas) — la découverte du banc est donc
  méthodologique : le gold de l'absence était gelé.
- **P3 — VRAIE, et c'est la ligne la plus importante du banc** :
  ComputeFirst n'a **rien inventé sur les 4 leurres**. Un catalogue
  de 859 outils qui s'abstient 4/4 est un concurrent sérieux, pas
  une farce — le bench qui les aurait présentés comme des charlatans
  serait mort au premier run. À juger : ils sont dans le même camp
  que nous — le déterminisme avec contrats — et leur tablage
  gratuit sur certaines familles nous pique des appels.
- **P5 — VRAIE** : leurs réponses portent `data_version` (registre
  IBAN daté) — ils versionnent leurs tables. Nous pinsons nos
  goldens ; deux architectures de preuve, convergentes.

## Actions (dans l'ordre de douleur)

A1. **Compteur de jours ouvrés** chez nous (leur G4, notre trou) :
    op `diff {until, unit:workdays, holidays}` dans date/calc —
    payload à freezer, gold 9 écrit à la main, golden pin.
A2. **Décision de tier sur validate/iban** (et audit des autres
    payés à faible barrière) : le banc vient de montrer qu'un
    concurrent gratuit rend le même byte. C'est un choix de
    POSITIONNEMENT, pas de code — à trancher par l'humain.
A3. Publier la convergence : « sur les tâches où les deux suites
    ont l'outil gratuit, deux companies indépendantes rendent les
    MÊMES bytes » — c'est la meilleure preuve que le déterminisme
    n'est pas une secte mais une physique. Un post court, deux
    captures, pas de guerre de liens.
