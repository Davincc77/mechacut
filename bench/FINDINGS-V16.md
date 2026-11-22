# Bench v16 — « le petit modèle sait-il QUAND il ne sait pas ? »
# Verdict pré-enregistré (a13ec1f) rendu par les données (86e727f) :
# confiance DÉCORATIVE, unanime, sans appel.
# (2026-11-22. 20 problèmes FR générés par graine 2026, golds exacts,
# nombres jamais vus par personne — la mémoire ne peut plus expliquer
# ni le mérite ni la faute. 4 modèles × 20 = 80 cellules, une seule
# exécution, zéro re-pilotage.)

| modèle | juste | P(¬confiant \| faute) | P(confiant \| juste) | verdict |
|---|---|---|---|---|
| 0.5b | 2/20 | **0.00** | 1.00 | DÉCORATIVE |
| 1.5b | 2/20 | **0.00** | 1.00 | DÉCORATIVE |
| 7b-q4 | 10/20 | **0.00** | 1.00 | DÉCORATIVE |
| llama3.1:8b | 3/20 | **0.00** | 1.00 | DÉCORATIVE |

**63 fautes. Zéro doute exprimé. Le mot « false » n'apparaît dans
aucun des 80 bruts.** Le 7B, qui ne répond juste que la moitié du
temps, est sûr de lui dans 100 % de ses erreurs. Le 8b a rendu
« 2331.3333333333335 » (gold 1469.00) avec conf=true — il a même
divisé en décimale périodique et l'a assumée.

## La découverte que le verdict cachait : le mur est UNE FAMILLE
justesse par famille, tous modèles :
- `rate` (une étape : débit × temps) → 9/16
- `recette` (proportion simple) → 5/12
- `distance` (deux étapes) → 2/12
- `soldes` (deux % successifs) → 1/12
- **`mix` (« % du RESTE », trois dépendances) → 0/16**
- **`partage` (« la seconde reçoit 1/4 DU RESTE ») → 0/12**

Le 7B est PARFAIT sur chaque famille à un pas (rate 4/4, recette 3/3)
et **zéro partout où la réponse dépend du résultat d'un calcul
précédent**. 0/28 cumulé sur les deux familles à reste. Ce n'est plus
une gradation de capacité : c'est une frontière. La chaîne
valeur→valeur est le point où le langage seul s'effondre — et
exactement la forme que le /api/v1/pipeline (refs `$from`) exécute
sans broncher, comme le bench v11 l'avait déjà montré sur le hash
stack à 3 étages.

## Ce que ça répond, à la question de l’opérateur
« Model-first, appeler la suite pour combler ce qu'on ne sait pas » :
**impossible à écrire comme règle, car la variable de contrôle
(« sait que ne sait pas ») n'existe pas dans ces modèles.** Sur
n=80 : la confiance déclarée n'a JAMAIS signalé une faute. Une skill
« appelle quand tu doutes » équivaut à une skill « appelle quand un
dé à faces inconnues le dit ». Le déclencheur honnête reste PAR
CLASSE (la règle actuelle de SKILL-MINI), et le miroir
/intent/reflect reste le seul geste qui aide à la compréhension :
il ne demande pas au modèle ce qu'il sait, il lui rend ce qu'il a
dit. Caveat tenu : la confiance VERBALE n'est pas la calibration
statistique (Kadavath et al. 2022 montrent du signal dans les LOGITS
de grands modèles fermés) — ce qu'on mesure ici est le seul canal
accessible à un agent gratuit : ce que le modèle DIT de son doute.
Et ce canal est vide.

## Ce que ça vend
Le pitch se résume désormais en une ligne mesurée :
**« ton modèle gratuit échoue sur TOUTES les questions à chaîne de
dépendance — et ne se corrige jamais tout seul, jamais, 0/63. La
machine qui déroule ces chaînes est déterministe : un pipeline, six
recettes, 132 tools. »** — chaque mot de cette phrase a son jsonl.

## Reproduction
    .venv/bin/python bench/gen16.py      # les 20 énoncés + golds
    .venv/bin/python bench/run16.py [modèles]
    .venv/bin/python bench/score16.py    # verdicts gelés, reclassement impossible
Brut : bench/results_v16_calibration.jsonl (80 lignes, conf_explicit
flaggé : le 1.5b n'a même pas posé le champ 7 fois sur 20 — répondre
sans répondre = confiance implicite, amendement pré-enregistré 86e727f).
