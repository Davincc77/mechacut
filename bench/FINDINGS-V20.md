# FINDINGS-V20 — le verrou de cible : le garde promis par v17, mesuré

Promesse rejouée à la lettre : « la réponse exige `{"answer": v,
"target": nom}` et le serveur refuse si le target ne correspond pas à
la question déclarée » (FINDINGS-V17). Le rôle du serveur est tenu
par le harness, avec le dictionnaire de quantités que gen16 possède
(`qte`/`cible`, patch adds-only — identité des 20 problèmes vérifiée
par hash avant/après : `38df94d7…`). Refus nommés VOCAB / MISMATCH /
CIBLE, réparation ×1 (doctrine v14). PRÉDICTIONS P1-P5 gelées dans
run20.py, commitées AVANT la première cellule (8e0f81a).

## La table (120 cellules = 3 modèles × 2 bras × 20, temp 0, seed 42)

| modèle | S (protocole v14) | L (+ verrou) | t/juste S | t/juste L |
|---|---|---|---|---|
| 8b | 10/20 | **13/20** | 3 008 | **1 832 (×0,61)** |
| 7b | 19/20 | **20/20** | 1 120 | 1 174 (×1,05) |
| 1.5b | 11/20 | 12/20 | 1 883 | 2 136 (×1,13) |

Intégrité d'abord : le bras S REJOUÉ ici redonne exactement 10 / 19 /
11 — les trois scores S de la matrice v15. L'instrument est stable,
les deltas sont imputables au seul verrou.

## Verdicts gelés — deux tombent, le banc a jugé, pas nous

- **P1 ✗ (la classe est plus petite que l'autopsie)** : sur les 10
  échecs de S(8b), **3 seulement** portent une valeur qui égale une
  AUTRE quantité nommée de la chaîne (« à côté » au sens strict).
  L'autopsie de v17 (« 7 fois à côté ») était un œil nu sans
  dictionnaire : 7 des 10 nouveaux échecs sont des valeurs qui
  n'appartiennent à AUCUNE quantité — des fautes de LECTURE, pas de
  visée. Le verrou ne peut rien là où la chaîne elle-même est faux.
- **P2 ✓, pile au seuil** : 8b 10 → 13 (+3). Et le détail qui compte
  plus que le score : les 3 cellules « à côté » de S sont converties
  **3/3** par le verrou. Le garde prend exactement la classe qu'il
  vise, ni plus ni moins.
- **P3 ✓ — et surprise** : le 7b passe de 19/20 à **20/20 — premier
  sans-faute de la maison sur ces 20 problèmes**. Son échec S était
  un `max_steps` (dérive après 6 pas sur #07 rate) ; nommé dès le
  premier pas, le même modèle s'arrête d'errer. Le verrou n'est pas
  seulement un rattrapage : c'est une CLÔTURE de chaîne.
- **P4 ✗ (le mur bouge, mais ne tombe pas)** : 1.5b L = **12/20**,
  soit un de plus que le plafond 11 posé avant la course. Le verrou
  répare même une faute de lecture au 1.5B (+1) — mais 8 échecs
  restent, et leurs refus finaux sont les mêmes classes qu'en S.
  Dire « ≤11 » était trop strict ; dire « le verrou remplace la
  compréhension » reste faux. La borne honnête tient, ajustée.
- **P5 ✓ partout** : au 8b le verrou rend le travail moins CHER
  (×0,61) — parce que S errait 4-6 pas APRÈS avoir calculé le bon
  nombre. Preuve de la maison : S #00, trace publiée — `400−160 =
  240` dès le 3e pas (l'ORACLE), puis deux pas d'errance et réponse
  160. Le verrou L sur le même énoncé rend 240 nommé `remaining`.

## Ce que la collision a enseignée (relevée AVANT la course)

#12 : `sold_afternoon == remaining == 300.0`. Un « juste » à la
valeur ne suffit pas : le verrou exige le NOM de la cible. C'est le
produit qui parle — une fiche rend `target: remaining`, pas un
nombre nu.

## Incident publié

4 cellules 1.5b foudroyées par la limite 30/min du `math/calc` de
prod (erreurs infra, pas modèle) : retirées du brut, re-jouées à
froid, verdict P4 changé par la reprise (11 → 12). Les re-jous sont
déterministes (temp 0, seed 42) ; le brut final ne contient que des
cellules jouées.

## Ce que ça vend (ligne mesurée)

**« Le calcul était juste depuis le début — c'est la VISÉE que le
modèle ratait. Nommer la cible dans la réponse et refuser les
mismatches nommément : le 8B passe de 10 à 13/20, le 7B fait 20/20
pour la première fois, et là où il convertit, il convertit 3/3 —
tandis que le 1,5B, lui, prouve qu'aucun garde ne lit à sa place. »**

## Prochain mouvement naturel (non joué, écrit ici avant de le vendre)

Le garde vit déjà dans les fiches (v0.82.0, cible nommée) — pas dans
le protocole steps général. Si un lot produit embarque le verrou
(grammaire fermée du nom, refus nommés, réparation ×1) dans le
serveur, la promesse de v17 est enfin tenue sur TOUT le transport,
et ce banc devient son critère d'acceptation : L(8b) ≥ S+3,
7b non-dégât, t/juste ≤ 1,5×.

## Reproduction

    .venv/bin/python bench/run20.py 8b 7b 1.5b   # repreneable par (model,i,arm)
    .venv/bin/python bench/run20.py --selftest  # verrou pur : VOCAB/MISMATCH/CIBLE
    .venv/bin/python bench/score20.py           # P1-P5 statues
Brut : bench/results_v20_target_lock.jsonl (120 lignes, traces et
refus par cellule). Dictionnaire : bench/gen16.py (qte/cible par
famille ; gate identité dans le commit 8e0f81a).
