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

## ADDENDUM — même nuit, après A1 + A2 (0.91.0 en prod)

L'humain a tranché, le banc rejoue. Deux lignes de l'original
étaient en avance sur leurs preuves — c'est ici que ça se publie :

1. **G4, la confession du juge** : la matrice ci-dessus écrivait
   « eux : 9 (correct) » alors que la première passe ne l'avait
   JAMAIS vérifié — le payload du harnais disait
   `weekend_days:["sat","sun"]` et leur grammaire fermée (entiers
   1-7, Monday=1) avait répondu un REFUS NOMMÉ, consigné dans le
   brut (`results_v21.jsonl.avant-a1-a2`). La cellule était une
   ATTENTE recopiée en fait. Rejoué avec le payload conforme :
   **eux 9, nous 9 — accord exact**, et leur refus était
   l'énoncé même de notre doctrine. Deux conventions notées :
   weekend 1-7 chez eux, 0-6 chez nous ; le même monde, deux
   grammaires, chacune nommée dans ses contrats.
2. **G3, la tier-divergence a cessé par décision** : validate/iban
   est devenu gratuit (0.91.0 — « même byte chez le voisin gratuit,
   portefeuille chez nous » n'était pas tenable). Rejoué :
   `ours: free-and-right`, même sha, plus de 402. La pin FR garde
   son empreinte d'origine — le middleware ne touche jamais le corps.
3. **A1 livré** : `diff unit=business_days` reçoit `include_base`
   (fenêtre [base..until], les deux bouts comptés ; fenêtre nulle =
   le jour compte 1 s'il est ouvré ; fenêtre arrière = refus nommé).
   La convention historique reste épinglée, intacte, sha d'origine.
   Découverte consignée par le propre test : l'arrière historique
   n'est PAS le miroir de l'avant (base exclue → [05..16) = 9
   ouvrés contre (05..16] = 8) — première version du test clamait
   -8 par symétrie conjecturée ; le pin figeait -9 ; le produit
   avait raison, le test s'incline et documente. C'est précisément
   ce pourquoi `include_base` refuse l'arrière au lieu de le
   deviner.

Matrice corrigée des deux branches :

| cellule | eux | nous | verdict final |
|---|---|---|---|
| G1 sha256 | == gold | == gold | accord byte à byte |
| G2 dedupe | == gold | == gold | accord |
| G3 IBAN | valide, gratuit | valide, **gratuit (0.91.0)** | **accord intégral** |
| G4 ouvrés [05→16, férié 12] | 9 | 9 (`include_base`) | **accord** |
| G5-G8 leurres | 4/4 abstention | 4/4 exacts | leur honnêteté vérifiée |

P2 amendée : VRAIE, mais seulement à partir du rejouement — le
banc d'hier soir affirmait le 9 d'eux sans l'avoir jamais reçu.
P4 amendée : la lacune est close (A1), épinglée à 196 pins.
Le reste de l'original tient.

