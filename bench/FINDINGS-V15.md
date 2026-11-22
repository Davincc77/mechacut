# Bench v15 — L'ARBITRE : la matrice unique (5 bras × 4 modèles × 20
# problèmes seedés = 400 cellules, une seule tenue, 2026-11-22).
# Prédictions G1-G5 gelées dans run15.py, commitées AVANT la première
# cellule (072c898). Deux sont tombées ; le banc a jugé, pas nous.

| modèle | N nu | C code | R relais-libre | S pas-à-pas | T retry×5 |
|---|---|---|---|---|---|
| 0.5b | 2/20 | 0/20 | 0/20 | 2/20 | 1/20 |
| 1.5b | 2/20 | 0/20 | 6/20 | **11/20** | 3/20 |
| 7b-q4 | 10/20 | 8/20 | 10/20 | **19/20** | 9/20 |
| 8b | 3/20 | 6/20 | **11/20** | 10/20 | 4/20 |

(tokens/juste : N=254-1323 · C=321-686 · R=335-1088 · S=1122-3012 ·
T=1111-10035 ; "-" quand zéro succès = ∞)

## Verdicts des prédictions gelées
- **G2 ✓ LOI** : retry ≈ nu sur les quatre modèles (±1). Cinq
  échantillons à 0,7 n'achètent rien sur une erreur systématique —
  10 035 tokens pour 1/20 au 0.5B. Le self-consistency est un placebo
  sur ce terrain, chiffré cette fois sur toute la matrice.
- **G4 ✓** : le code marche mieux au 7B qu'au 8B (8 vs 6… mais le
  8B code > nu : 6 vs 3). La taille n'achète pas la discipline.
- **G5 ✓, plus fort que v17** : familles à chaîne (28 cellules) —
  **N = 0/28, T = 0/28** (le retry : littéralement jamais), et
  seuls les bras serveurs marquent : S 11, C 11, R 8. La frontière
  de FORME est une loi de la maison, répliquée sur matrice complète.
- **G1 ✗ — la chute intéressante** : le pas-à-pas ne domine PAS
  partout. Au 8B, le **relais-libre en un seul appel** (R) bat le
  protocole multi-tours (11 vs 10) à **8× moins cher** (394 vs
  3 012 t/juste) — llama décroche en multi-tours (leçon v14/v17
  confirmée) et brille quand on lui demande TOUT en une ligne.
- **G3 ✗ — la seconde** : R ne s'effondre pas au 1.5B (6/20) —
  l'effondrement de v13 venait du formulaire multi-champs, pas de
  l'idée. Un JSON à UN seul champ `{"steps": [...]}` est franchement
  plus robuste que ce que nous avions mesuré.

## Ce que la matrice dit que nous ne savions pas
1. **Il n'y a pas de meilleur bras universel — il y a une
   compatibilité modèle↔transport.** Le 7B est une bête de suivi
   (S 19/20, record de la maison), le 8B est un bon rédacteur d'un-shot
   (R) et un mauvais discuteur (S : 3 012 t/juste, ruptures max_steps),
   le 1.5B ne lit pas les histoires (tout <12) mais comble l'écart
   serveur vs nu de 9 points. Le produit doit donc exposer LES DEUX
   transports : le pipeline mono-appel (`{"steps":[…]}` — déjà là)
   et le protocole pas-à-pas — et la SKILL doit les router par modèle,
   pas par idéologie.
2. **Le 0.5B ne se sauve par aucun bras (max 2/20)** : là où le mur
   est la LECTURE, la délégation ne peut rien — c'est la borne
   honnête du produit, écrite dans le marbre de cette matrice :
   mechacut transforme des nombres, pas une compréhension qui n'existe
   pas. (Sur PUR calcul — v12 — le même 0.5B passait de 0 à 9/10.)
3. **La chaîne est le territoire du serveur** : 56 cellules
   nu+retry = 0/56. Toute conversation d'agent qui « révise son
   calcul » sur un problème à dépendances est du token brûlé à
   l'état pur. C'est le pitch, et il est irréfutable sur 400 cellules.

## Actions nées du banc (gravées en file)
- **A1 (S, skill)** : la SKILL recommande le pipeline mono-appel en
  transport PAR DÉFAUT pour les chaînes, le multi-tour en repli —
  hiérarchie inversée par les données, pas par goût.
- **A2 (v18)** : le verrou de cible reste le bon pari — le 8B en R a
  11/20 avec des réponses « justes mais à côté » (les 7 cibles
  manquées de v17 sont encore là) : viser juste est la dernière
  douleur non servie.
- **A3** : F5 fiches-recettes — critère d'acceptation issu du banc :
  la fiche mono-appel doit faire ≥ ce que R+S font ensemble sur
  mix/partage (19/56).

## Reproduction
    .venv/bin/python bench/run15.py [modèles]   # repreneable
    .venv/bin/python bench/score15.py           # G1-G5 statues
Brut : results_v15_matrix.jsonl (400 lignes, tokens et secondes par
cellule). Générateur : gen16.py (graine 2026, double oracle).
Ruptures de forme comptées à part au bas du scoreur — la confusion
protocole/connaissance est interdite depuis v14.
