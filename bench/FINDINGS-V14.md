# Bench v14 — la SKILL stricte comme couche de compréhension
# (2026-11-22, 80 cellules, harness v14-skill, mêmes 20 questions
# GSM8K seedées 1301 que v13. Bras unique : le modèle ne calcule
# JAMAIS — il remplit le gabarit {"step": expression fermée}, le
# serveur évalue via math/calc, le modèle relit {"value"} et
# recommence, max 6 étapes, une réparation nommée par cellule.)

| modèle | nu (v13) | relais-libre (v13) | SKILL stricte (v14) | protocole cassé | max_steps |
|---|---|---|---|---|---|
| 0.5b | 9/20 | 0/20 | **2/20** | 1 | 0 |
| 1.5b | 7/20 | 0/20 | **2/20** | 2 | 3 |
| 7b-q4 | 18/20 | 2/20 | **14/20** | **0** | **0** |
| llama3.1:8b | 16/20 | 6/20 | 7/20 | **0** | 4 |

## Les trois enseignements, dans l'ordre de franchise

1. **La skill stricte RÉSOUS la classe d'échec protocole — c'était la
   thèse, elle est vraie.** V13 : le relais JSON libre s'effondrait en
   babil (0/20 aux petits). V14 : avec gabarits fermés + erreur qui
   nomme champ et forme + une seule réparation, le 7B tient 14/20 à
   **zéro rupture de protocole et zéro dépassement d'étapes** — chaque
   trace est lisible, chaque échec est nommé par la nature de son
   erreur, plus par sa forme. Un banc qui transforme l'échec opaque en
   échec diagnostiqué a déjà gagné, quel que soit le score.

2. **Mais le plafond restant est la COMPRÉHENSION, et aucune skill ne
   la donne.** 2/20 au 0.5B : il remplit parfaitement le gabarit avec
   les mauvais nombres (trace : « 40 », « 20 » inventés, 1.5b #35).
   La skill dit COMMENT remplir ; elle ne peut pas dire QUOI lire.

3. **Et sur GSM8K, la mémoire bat les deux.** Nu, le 7B fait 18/20
   — plus que 14/20 en skill-relay — parce que ces questions sont dans
   son entraînement. Comparer des bras sur données saturées mesure du
   recyclage. La hiérarchie vraie des bras ne peut être lue que sur
   NOMBRES NEUFS → c'est exactement ce que le banc v15 (générateur
   seedé) va trancher, avec la skill-relay comme quatrième bras
   officiel : nu / code / relais-libre / skill-stricte.

## Décision produit (conséquence directe, pas décorative)
- **Encoder le protocole math-steps dans les skills** : SKILL.md (pack
  numbers) en entier, SKILL-MINI en 4 lignes (gabarit + « tu ne
  calcules jamais » + max 6 pas). Preuve : 7B 0 rupture protocole.
- **Garder v12 comme titre marketing** (le calcul neuf relayé :
  9-10/10) — v14 prouve pourquoi : c'est LE cas où la décomposition
  tient en un pas, donc où la chaîne mémoire/compréhension ne pollue
  rien. Le one-shot est le cas d'usage honnête du produit ; le
  multi-pas est son extension mesurée, pas son pitch.
- **v15 devient l'arbitre** : seeds publiés, golds par Fraction,
  4 bras, + ligne temp 0.7. Si skill-stricte ≥ relais-libre avec
  écart net sur nombres neufs, la skill est un produit à télécharger
  au même titre que les endpoints — et on la linkera comme telle.

## Reproduction
    .venv/bin/python bench/run14.py [0.5b 1.5b 7b 8b]
Brut : bench/results_v14_skill.jsonl (80 lignes, traces complètes
inclinées dans le champ trace). Skill textuelle = SKILL constante du
harnais, mot pour mot identique à celle servie au modèle.
