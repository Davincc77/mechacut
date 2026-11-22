# Bench v11 — conçu pour le zéro nu (2026-11-22, suite 0.73.2)

15 tâches hostiles : triple-hash itéré, sha512 intégral, business days
AVEC jours fériés, diff borné férié, max d'une colonne CSV à milliers
guillemetés (25 lignes), ISBN-10/ISSN/ISIN/LEI sur payloads non
mémorisés, URL canonique avec port par défaut, sha du JSON canonique,
récurrence +12 semaines.

| modèle | nu | relais |
|---|---|---|
| qwen2.5:7b-q4 | 3/15 | 13/15 |
| llama3.1:8b   | **0/15** | 13/15 |

- **8b nu = 0/15** : l'objectif « rater complètement » est atteint.
- Les 3 passes du 7b sont des fuites de MÉMOIRE, pas du calcul :
  043942089-X (ISBN HP publié dans ses poids), ISSN 2499-216X, et
  csv_max par chance de format. Ce sont exactement les cas que le
  bench doit publier — la mémoire n'est pas la justesse, elle ne
  couvre que les vecteurs connus (les variantes non publiées ratent).
- **Les 2 échecs RELAIS sont la thèse, pas un bug** :
  1. v11_hash_stack : les deux modèles aplatissent le stack 3-étapes
     en UN seul hash/digest — le mur de composition mesuré en direct,
     la raison d'être des recipes/pipeline (v9 le disait déjà à 1.5B ;
     le voilà chiffré à 7-8B sur un cas réel).
  2. v11_csv_max : choix de money_columns au lieu de csv/types —
     l'outil voisin « conceptuellement vrai » mais qui ne renvoie pas
     la colonne typée. La réponse du serveur ne peut pas être juste
     si la ROUTE choisie est à côté : le routage est la moitié du
     produit (d'où la refonte /route taguée F4 dans la file).
- Déterminisme : golds oracles purs, probe 15/15 avant modèles ;
  l'assert « ean13=3 de mémoire » est mort en construction — l'oracle
  s'est autocorrigé (7, ladder double-vérifié).

## Publiable
« 8 milliards de paramètres, 0/15 sur des formules de CM2 exactes.
Branchés sur 124 transformations déterministes : 13/15 — et les 2
ratés sont encore des échecs de COMPOSITION que le produit absorbe
par recettes. »

Reproduction : bench/run11.py --probe puis run11.py ;
brut : bench/results_v11.jsonl (60 cellules, tag harness v11).
