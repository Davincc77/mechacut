# Bench v10 — « pas seulement bien : JUSTE » (2026-11-22, suite 0.72/0.73)

## Question
Un modèle gratuit « un peu plus puissant » qu'un 1.5B — qwen2.5:7b
(q4, local) et llama3.1:8b (local) — est-il capable de réponses
EXACTES (chiffre de contrôle, hash, date, montant) SANS relais ?
Coût total du bench : $0 vérifié par le code (free-audit : 0 route
payante dès le 1er appel, payloads 🟡 prouvés < 32 Ko).

## Matrice mesurée (72 cellules, temp 0, seed 42, num_ctx 16k pareil
aux deux bras ; golds = oracles indépendants recoupés produit live
18/18 AVANT tout appel modèle)

| modèle | bras NU | bras RELAIS (answer_from_server) |
|---|---|---|
| qwen2.5:7b-q4 | **3/18 (17 %)** | **18/18 (100 %)** |
| llama3.1:8b | **3/18 (17 %)** | **18/18 (100 %)** |

Ce qui passe nu (3/18 ×2) : fin février non-bissextile, DST 03:30
(énoncé qui porte la réponse), LEI « 55 » par cœur (LLM entraîné
dessus — d'où les payloads NON mémorisés des autres tâches).
Tout le reste est raté CONF IAMMENT :

- sha256 : llama3.1 fabrique « 5f4b7f5d3f4c5f4b7f5d3f4c… » — un motif
  qui se répète, 128 hex de faux. Le hashage est biologiquement hors
  de portée ; la confiance, non.
- remises : « 24.54 » pour 50.34, « 50 % » pour 44 %, b2p1 « 23.98 »
  pour 39.98 — l'arithmétique bancaire des soldes, ratée en tous sens.
- colonne EU : « 1.234 » lu 1.234 là où la colonne PROUVE 1234 — le
  bug exact de r/ClaudeAI « decimal points in financial CSVs »,
  reproduit sur deux familles de modèles.
- repair ISBN : llama3.1 répond « 0:1, 1:1, 2:1, … 12:1 » — chaque
  position avec le CHIFFRE 1. Réponse parfaitement shaped, totalement
  fausse. Le pire genre d'échec : celui qui parse.
- xml force_array : tableau à l'envers (sur b au lieu de c).
- 'next monday' vu d'un dimanche : 2026-11-29 (attendu 23) — l'off-by-
  week classique qui casse les agendas.

## Reproductibilité (la clause qui ferme le doute)
Seconde passe INDÉPENDANTE du bras nu 7b, processus frais :
**18/18 verdicts reproduits à l'identique**. À temp 0 les échecs sont
systématiques — « juste réessaie » ne converge jamais. C'est le prix
réel d'un miss : un appel de plus, ou un humain qui relit.

## Déterminisme mesuré PENDANT le bench
3 appels identiques sur money/discount → **1 sha256** (200 seulement).
Fausse alerte utile : la première sonde criait « 2 shas » — c'était un
429 du rate-limiter (36 appels relais juste avant). Leçon de méthode :
un probe de déterminisme ne compte QUE les 200.

## Ce que le bench a PÊCHÉ (son vrai travail)
`Decimal.normalize()` publiait « ×(1 - 3E+1/100) » dans le ledger des
remises — notation exponentielle dans un champ destiné aux humains.
Corrigé en v0.72.1 (format f + garde anti-E), re-pin chirurgical
(1 golden), déployé en 0.73.1.

## Litige de session (honnêteté d'inventaire)
La sœur cron a déployé 0.73.0 (sql_dump) AVANT le re-pin du ledger ;
arbre fusionné en rebase, v0.73.1 = les deux. Pin money/discount vérifié
sur 0.73.1 ci-dessous.

## Publiable en une ligne
« Nus, un 7B gratuit et un 8B touchent 3 justesses sur 18 (17 %).
Branchés sur MechaCut : 18/18. Et leurs échecs nus se reproduisent
à l'identique — le retry ne converge jamais. »

## Reproduction
    .venv/bin/python bench/run10.py --probe   # golds × serveur (18/18)
    .venv/bin/python bench/run10.py           # matrice 72 cellules
Résultats bruts : bench/results_v10.jsonl (taggé harness v10,
suite 0.73.1).
