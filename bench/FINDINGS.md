# A/B benchmark — findings (2026-11-20, v0.18.0)

**Setup.** Frozen task (`task_data.py`, seed 20261120): dirty 40-line CSV +
broken JSON + 18 URLs → one YAML document, scored by canonical sha256
against the pinned gold (`expected.sha`). temp 0, seed 42, local Ollama on
the M4 Pro. Arm A = model alone in context. Arm B = manifest + tool(s).

## What is proven (by tests, not models)

- `POST /api/v1/pipeline` with the 6-step chain returns the pinned gold
  answer exactly, in one HTTP call (`tests/test_pipeline.py`, 167 green).
- The navigation substrate (manifest, packs, router, recipes) is
  byte-deterministic and self-certified.
- A scripted client — 30 lines of code — gets a perfect answer at ~0
  thinking tokens. That is the actual product promise, and it holds.

## What the models did (measured)

| model | arm | result |
|---|---|---|
| qwen2.5 0.5b / 1.5b / 7b-q4 | A | fails — hallucinated rows, wrong dedupe, padding kept |
| qwen2.5 0.5b / 1.5b / 7b-q4 | B (tools + skeleton, several prompt designs) | mostly **0 tool calls**: answers directly; when it does call, it transcribes or invents field names (`clean_csv`, `$fill` mangled) |
| llama3.1:8b | B | emits the chain as plain **text** instead of the tool channel, loops on it |

The repeated, honest finding: **qwen2.5-instruct is not a tool-use model.**
Ollama's function-calling wrapper cannot make a 0.5–8B instruct model drive
a multi-step chain reliably. Prompt coercion ("MUST call", recency nudges,
placeholders) shifts the failure mode, not the outcome.

## Consequences for launch copy

- Do NOT claim "a weak agent orchestrates mechacut by itself." The measured
  claim is: **"mechacut turns a weak agent's 4-step job into one scripted
  call — no orchestration skill required."** The pipeline IS the agent's
  missing planning: the plan lives server-side (recipe/pipeline), the
  model only supplies data.
- The manifest/router remain honest selling points (they cost ~4 KB once
  and remove tool-choice reasoning, B0.7/B0.8), but the showcase number
  for the launch post is **one call → gold sha**, demonstrated in tests
  with an exact, repeatable command — not an LLM looping.
- If a future bench wants the "agent drives it" story, the correct test
  models are Hermes-function-calling trained (llama-3.1-70B, qwen2.5-coder,
  or a fine-tuned 7B tool model) — not instruct.

## Repro

```
.venv/bin/python bench/expected.py check          # gold integrity
.venv/bin/python -m pytest tests/test_pipeline.py # pipeline = gold, 1 call
```

Harness history: v1 (too easy, B won without tools), v2 (B punished for
transcribing — the thing the product removes), v3/v3b/v3c (placeholders,
$fill; sibling session's iterations, kept in results.jsonl tagged). The
matrix rows above are the union of honest runs across designs.

## v7 — the qualitative-leap task (2026-11-21)

Task : note d'incident -> JSON {montants, pourcentages, dates, services,
checkouts}. Gelé seed 20261121, scoré clé par clé (Decimal equality),
armes A (nu) vs B (one-shot extract_facts group=kind + list_dedupe +
réparation JSON guidée). Temp 0, seed 42, qwen2.5 local.

| modèle | A seul | B équipé | lecture |
|---|---|---|---|
| 0.5b | 0/5 | 0/5 | plafond confirmé, publié |
| 1.5b | 0/5 (JSON illisible) | **3/5** | le saut est partiel : la boucle erreur→réparation rend la sortie parsable et vraie sur 3 clés ; l'agent perd 2 valeurs en recopiant les listes du serveur |
| 7b | 5/5 | 5/5 | sur specs strictes, le 7b n'a pas besoin des outils — le coût B (1164 tok) > A (477). Les outils servent sous 7B et au-delà de la note de 5 lignes |

Trois leçons produits (pas bench) :
1. UN DUMP BRUIT TOXE : le extract_facts détaillé (26 faits dont fragments
   d'heures) faisait échouer là où le dump groupé-dedupé (group=kind) fait
   réussir. → group=kind est devenu un paramètre du produit, pas du harness.
2. L'erreur-réparation fonctionne : +0/5→3/5 sur 1.5b juste en lui
   renvoyant « JSON invalide, corrige » une fois. C'est la thèse du
   produit, mesurée sur le taux de réponse.
3. LA COPIE EST LE PROCHAIN ENNEMI : 1.5b perd 12.5% et « payments » en
   transcrivant la réponse du serveur dans sa réponse. La réponse v8 est
   serveur : recettes/pipeline qui COMPOSENT le JSON final — le modèle
   choose, the suite assembles. (publié comme résultat, pas caché)

Verdict public : exactitude 1.5b 0/3 réponses valides hier ; aujourd'hui
3/5 clés justes avec deux appels gratuits. Ce n'est pas un match nul :
c'est la première fois que la machine porte le modèle sous 7B à mi-chemin,
et on sait exactement quelle brique manque (composer côté serveur).

## v7.1 — forensique brute (2026-11-21, après le déploiement des miroirs Bankr)

Même tâche v7, capture des octets sortis par le modèle (brut non scoré) :

0.5b, NU (A) : connaît la FORME (les 5 clés !) mais hallucine les VALEURS
  (4300.00 → une seule valeur, 0.062 inventé, dates en double) puis
  s'effondre en boucle de répétition (« services » ×5, 2 367 tokens).
0.5b, ÉQUIPÉ (B) : mode de rupture RÉVÉLATEUR — il PARROTE le protocole
  steps JSON (réémet l'ouverture forcée + le texte de la note) sans
  jamais CONSOMMER l'observation de l'outil. calls=0. Le 0.5b n'a pas de
  modèle « l'outil a répondu » : le paywall ne peut rien pour lui.
  Plafond publié, trois fois de suite : c'est un résultat, pas un bug.

1.5b, NU (A) : 455 tokens, JSON propre mais FAUX (5210.50 inexistant,
  12.5% et 3.1% oubliés, date inventée). L'extraction pure le dépasse.
1.5b, ÉQUIPÉ (B) : il RECOPIE les bonnes valeurs du serveur (4300.00,
  910.50, 12.5, 3.1, 6.2, dates, services) — mais casse le JSON en
  recopiant (6.2% et dates sans guillemets). Avec la passe de réparation
  du protocole v7 officiel : 3/5 clés justes. Les valeurs sont là ;
  c'est la TRANSCRIPTION qui fuit. → v8 confirmé : composition
  serveur (le modèle choisit, la suite assemble), zéro recopie.

Leçons : (1) la fenêtre Overton du bench est entre 1.5b et 7b ;
(2) 0.5b échoue AVANT le paywall — aucune API ne répare l'absence de
théorie de l'esprit sur l'observation précédente ; (3) chaque échec de
1.5b maintenant est un argument pour /pipeline, pas contre mechacut.

## v8 (2026-11-21) — multi-tâche riche, 6 champs, réponse canonique
Tâche : note d'incident → {money triés+2déc, percent triés, dates uniques
triées, url, email, total_money}. Attentes CALCULÉES À LA MAIN. Suite LIVE.
Bras B v8.2 : protocole joué UNE fois par le harness (extract_facts live,
vraie observation), le modèle reformule/choisit ensuite.

          | nu (A)        | équipé (B)      | B en chiffres
----------|---------------|-----------------|-----------------------------
0.5b      | 0/6           | 0/6             | récite les compteurs de
          | (paraphe)     | (plafond v7)    | l'observation, ne reformate pas
1.5b      | 3/6           | 6/6  ◀ LE SAUT  | 937 tok / 2.4 s
7b        | 5/6           | 5/6 (money en   | 917 tok — a raté "3200.00"→"3200"
          | (1 date perdue)| "3200" près)    | hors contrat 2 décimales

- 1.5b : 3/6 nu (oublie 2 des 3 dates, ne liste pas l'email, url en string
  seule) → 6/6 avec UNE observation serveur. Les 3 valeurs perdues par
  oubli reviennent par construction : le rappel est garanti serveur.
- run8 premier passage (7b, bras B strict 1-cast) : 6/6 answer_from_server
  (575 tok, 8.2 s) — le choix recipe_facts existe et paie 6/6 sans
  reformulation.
- 0.5b : plafond confirmé une 3e fois (v6, v7, v8). On le publie tel quel.

## v9 (2026-11-21) — INTAKE en circuit fermé : le 0.5b saute ENFIN
Phrase humaine (FR, volontairement floue) → /intent/card LIVE choisit
l'outil et pré-remplit la note comme payload → le modèle RELAIE
{"run": path, "args": {"text": "$utterance"}} → la réponse vient du
serveur (answer_from_server). Attentes = celles de v8 (calculées main).

          | nu   | intake (1 relais) | tok intake | notes
----------|------|-------------------|------------|-------------------
0.5b      | 0/6  | 6/6  ◀ LE SAUT    | 320        | reproduit pass 2
1.5b      | 5/6  | 6/6               | 462        | ratait 2 dates seul
7b        | 4/6  | 6/6               | 452        | ratait money+2 dates

Contrôles d'honnêteté (le « en écartant tous les doutes ») :
- 3 appels live de la même phrase → sha256 unique (669e008e…) : contrat
  d'octets vérifié pendant le bench, pas après.
- pass 2 indépendant sur 0.5b : 0/6 → 6/6 reproduit à l'identique (seed 42).
- le serveur est la PROD (mechacut.studio), pas un mock local.
- attendu calculé à la main, pas copié du produit.
- ÉCHECS PUBLIÉS AUSSI : le nu du 0.5b (paraphe), le money-format du 7b.
- LIMITE DÉCLARÉE : la fiche est servie par le harness ; le modèle n'ouvre
  pas lui-même le dialogue intake. Version autonome = bras B strict de v8
  (7b : 6/6 en 1 appel, answer_from_server, 575 tok) — même résultat,
  moins de reliance sur le harness.
- Le 0.5b n'est PAS devenu plus intelligent : il n'a plus rien à calculer.
  C'est exactement la thèse de la suite, mesurée.
