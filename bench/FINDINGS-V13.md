# Bench v13 — GSM8K RÉEL : le résultat NÉGATIF, publié en premier
# (2026-11-22, suite 0.75.0. 20 questions du test set MIT d'OpenAI,
# subset seedé 1301 publié, 240 cellules, harness v13-gsm8k.)

| modèle | nu | code | relais |
|---|---|---|---|
| qwen2.5:0.5b | 9/20 | 4/20 | **0/20** |
| qwen2.5:1.5b | 7/20 | 4/20 | **0/20** |
| qwen2.5:7b-q4 | 18/20 | 9/20 | 2/20 |
| llama3.1:8b | 16/20 | 14/20 | 6/20 |

## Les trois lectures honnêtes

1. **Un 0,5 milliard sort 9/20 à un benchmark censé être de
   l'arithmétique scolaire.** Qwen2.5 est affûté maths et le test set
   circule dans les corpus depuis 2021 : ce score mesure un mélange de
   modèles de solutions mémorisés et de templates vus, pas la
   justesse du calcul — le calcul, le v12 vient de le facturer : sur
   NOMBRES NEUFS, le même 0.5B tombe à 0/10 nu. C'est le phénomène
   que la littérature 2026 mesure ailleurs (SWE-bench Verified
   80,9 → Pro 45,9 à modèle constant) : le benchmark public mesure ce
   que le modèle a VU, pas ce qu'il sait faire.

2. **Le relais multi-étapes s'effondre (0–6/20) — et c'était écrit.**
   Mon bras relais demandait au modèle DE DÉCOMPOSER le problème en
   étapes JSON. Le mur de composition mesuré dès v6 (« free-form
   composition stays above a q4-quantized 7B ») recollapsé ici, chiffré
   sur données réelles : demander à un 0.5B de composer = 0/20. Le
   v12 (relais une étape, recopie) faisait 9–10/10 avec le MÊME
   0.5B. La leçon produit : la décomposition est le travail du
   serveur (fiche d'intention, recettes, pipeline) — jamais celui
   du modèle, encore moins du petit.

3. **Le bras code perd contre la réponse nue** (4–14/20 vs 7–18/20) :
   traduire un mot en programme est au-dessus de ces modèles AUSSI,
   et coûte plus de tokens que leur réponse directe.

## Ce que ça change au produit (file, pas déni)
- Le contrat mechacut n'a jamais prétendu à la COMPREHENSION — le
  v13 le prouve par l'absurde en échouant là où le produit ne vend
  rien : publié tel quel, sans re-pilotage, avec les 42 cellules
  « passait nu, rate relais » listées dans le brut.
- v14 (queue G-v13) : le « bench qui prouve » sera un **generateur
  seedé** (nombres nouveaux à chaque run, golds calculés à la
  génération → zéro contamination possible) avec relais en **fiche
  d'intention** (le serveur décompose, le modèle relit) — pas du
  GSM8K mémorisé, pas du JSON libre.
- La ligne température 0.7 de G-v13 attend son tour : ici tout est à
  temp 0, et même là la mémoire gagne — à chaud, elle vacillera.

## Reproduction
    .venv/bin/python bench/run13.py 0.5b 1.5b 7b 8b
Brut : bench/results_v13_gsm8k.jsonl (240 lignes).
Données : bench/data/gsm8k_test.jsonl (MIT © 2021 OpenAI, LICENSE
joint). Subset : random.Random(1301).sample(range(1319), 20), trié.
