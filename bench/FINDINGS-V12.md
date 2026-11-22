# Bench v12 — « du zéro à héros » (2026-11-22, suite 0.74.0, 120 cellules)

Dix calculs exacts × 4 modèles gratuits locaux (0.5B → 8B) × 3 bras :
NU / CODE (le modèle écrit du Python, portique, exécution) / RELAIS
(le modèle recopie l'expression, `math/calc` compte).

| modèle | nu | code | relais |
|---|---|---|---|
| qwen2.5:0.5b | **0/10** | 8/10 | 9/10 |
| qwen2.5:1.5b | 2/10 | 10/10 | 10/10 |
| qwen2.5:7b-q4 | 4/10 | 10/10 | 9/10 |
| llama3.1:8b | 1/10 | 9/10 | **5/10** |

## Ce que la matrice dit VRAIMENT (les trois surprises)

1. **Le zéro devient héros** : le 0.5B qui invente `89000098` à la
   place de `72205978` sort 9/10 en relais — à 0,2 s médian et
   ~169 tokens par réponse juste. Le calcul n'était pas son problème ;
   personne ne le lui avait enlevé.

2. **Le bras code égale le score — et perd la justesse en silence.**
   Le Python du modèle rend `round(0.1+0.2, 1)` arrondi parce que MON énoncé exigeait l'arrondi. Sans
   cette béquille, `print(0.1+0.2)` sort `0.30000000000000004` — la
   valeur exacte qu'un paiement avalerait. Le RELAIS rend `0.3` :
   même score affiché, deux mondes de sémantique. (Ligne de preuve :
   `python3 -c "print(0.1+0.2)"` vs `math/calc expr=0.1+0.2`.)

3. **Le plus fort est le pire agent** : llama3.1:8b ne rate AUCUN
   calcul — il rate la PROTOCOLE : « To answer your request, I'll
   provide... » babil avant le JSON, 4 parses cassés + 1 limiteur,
   5/10. Le relais nud-brut est lui-même une compétence. C'est
   exactement ce que la fiche d'intention (`/intent/card`, bras
   card-relay du bench v9 où ce même 8B tenait 100 %) vient retirer :
   le serveur écrit la ligne, le modèle la rejoue.

## Méthode et bornes
- Golds : Fraction exacte, indépendante de Decimal ET du produit ;
  portique d'exécution du code modèle (whitelist AST, évasions refusées
  par le nom, auto-prouvées) ; temp 0, seed 42, même num_ctx/num_predict
  aux trois bras ; $0 audité (routes gratuites seules).
- Un srv429 dans les traces = ma propre rafale (limite 30/min du
  service) — publié tel quel, pas re-piloté.
- Le 0.5B code 8/10 : ses 2 ratés sont des ratés d'ÉCRITURE
  d'expression (parenthèses), pas de calcul — la nature exacte du
  délégué.

## Reproduction
    .venv/bin/python bench/run12.py 0.5b 1.5b 7b 8b
Brut : bench/results_v12.jsonl (120 lignes, harness v12, suite 0.74.0).
