# FINDINGS-F5 — les fiches-recettes à chaîne (acceptance du critère A3)

Critère PRÉ-ENREGISTRÉ (FINDINGS-V15, A3) : « la fiche mono-appel doit
faire ≥ ce que R+S font ensemble sur mix/partage (19/56) ».
Dénominateur, écrit avant la première cellule : 56 = 7 problèmes à
chaîne v16 × 4 modèles × 2 transports — A (découverte : le modèle
choisit parmi 3 fiches, dont soldes2 en leurre) et B (routée : fiche
imposée, créneaux seuls). Réparation serveur ×1 sur refus nommé
(doctrine v14), temp 0, seed 42.

## VERDICT : 20/56 — CRITÈRE PASSÉ. Lu honnêtement :

| modèle | A découverte | B routée |
|---|---|---|
| 7b | 6/7 | 6/7 |
| 8b | **0/7** | 4/7 |
| 1.5b | 0/7 | 4/7 |
| 0.5b | 0/7 | 0/7 |

- La fiche fait ce qu'elle promet : **quand le transport est bon, la
  chaîne devient solvable** — 7b : 12/14, y compris en choisissant sa
  fiche (une seule faute de leurre). Comparaison publiée : nu et retry
  faisaient 0/28 sur ces mêmes cellules.
- **Le 8B ne sait pas choisir** (0/7 découverte, 4/7 routée) : la
  multi-option le décroche — exactement la loi v14/v15/v17, re-mesurée.
  Le routeur (A1) n'est pas un confort, c'est une béquille mesurée.
- 1.5b et 8b routés à 4/7 : la fiche sauve la décomposition, pas la
  lecture. Le 0.5b : 0/14, sixième confirmation du plafond publié.
- Échecs non-OK : PARSE 22 (pas de JSON du tout — classe PROTOCOLE,
  le rôle de la skill stricte, pas de la fiche), REFUS-2 11 (deux
  refus sémantiques d'affilée), FAUX 1, et 2 KeyError du juge.
- Réparations : **34 des 56 cellules sont passées par le refus nommé**
  — l'erreur-qui-répare est le chemin principal, pas l'exception.

## L'incident du juge (publié parce que c'est nôtre)
La première passe affichait 0/56 avec 54 « FICHE-INCONNUE » : ma
vérification testait l'appartenance aux CLÉS d'un dictionnaire de
familles au lieu des noms de fiches. Les modèles avaient raison 54
fois sur 56 ; le juge était faux. Le jsonl contaminé est archivé
(`results_f5_accept.jsonl.bug-harness-clef-dico`), le correctif est
commité AVANT la seconde passe. Un banc sans l'historique de ses juges
ne vaut rien.

## Ce que ça change au produit
`/api/v1/fiche/shop-reste|partage-reste|soldes2` en prod (v0.82.0) :
refus sémantiques nommés inclus (le « 40 » nu dans un créneau de %
est devenu un 400 pédagogique — deux trous pêchés par le smoke 0.5B
avant le premier client). Routeur ×3 langues : « du reste » → fiche.
SKILL-MINI : la règle « les mots du reste = la zone 0/28, ne jamais
décomposer » tient en 5 lignes.

## Reproduction
    .venv/bin/python bench/fiche_accept.py   # repreneable par (menu,model,i)
Brut : bench/results_f5_accept.jsonl (56 lignes, tokens et réparations
par cellule). Fiches : ficheskit.py ; oracles à la main :
tests/test_bundle51.py ; golds croisés : gen16.py (double oracle).
