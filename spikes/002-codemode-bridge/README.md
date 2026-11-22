# Spike 002 — pont Code Mode au-dessus de Mechacut (local, zéro compte Cloudflare)

## Question
Given @cloudflare/codemode (npm, MIT), when on exécute du code écrit
« comme le ferait un agent » contre les VRAIS endpoints mechacut, then
plusieurs tool-calls deviennent un seul exchange — et le tout tourne en
local sans compte Cloudflare ?

## Ce qui a été construit (jetable, volontairement)
- `gen_types.mjs` — le `generateTypesFromJsonSchema` RÉEL du package,
  nourri par `/tools/<name>.json` de la prod → SDK TypeScript typé.
- `bridge.mjs` — le `runCode` RÉEL du package + un executor local maison
  (~20 lignes, `node:vm`) branché sur mechacut.studio en HTTPS réel.

## Résultats mesurés
1. **Le package s'utilise vraiment en local** : le cœur (`runCode`,
   `normalizeCode`, `generateTypesFromJsonSchema`) vit dans des chunks
   SANS `cloudflare:workers`. Seuls `DynamicWorkerExecutor` et le runtime
   durable exigent workerd. Le README officiel confirme : « you can build
   your own for Node VM, QuickJS, containers, or anything else ».
2. **Chaîne exécutée en un seul exchange** : 7 entrées → dédup (1 appel)
   → boucle for → 5 hashes (5 appels) → tri naturel (1 appel) = **7 appels
   réseau, 1 seul tour de modèle**. Résultat : `a.tex b.tex c-2 c-10 d.tex`
   (ordre naturel, c-2 AVANT c-10 — la classe d'erreur que les LLM font).
3. **Sandbox vérifié** : `typeof process === "undefined"`,
   `typeof require === "undefined"`. (node:vm = cloison pédagogique, PAS
   une frontière de sécurité — en prod : workerd local via `wrangler dev`,
   ou QuickJS-WASM. C'est LE chantier du vrai build.)
4. **LE FINDING CONTRE-INTUITIF** : le SDK typé Code Mode (≈818 tokens
   pour 8 tools) n'est PAS plus petit que nos schémas bruts (≈764) —
   générer des types ajoute des commentaires et des noms. L'économie de
   Code Mode n'est pas là où le pitch dit qu'elle est. Elle est :
   (a) les définitions ne sont pas renvoyées à CHAQUE tour de conversation ;
   (b) les N appels en boucle = 1 exchange, pas N ;
   (c) les intermédiaires restent dans la variable du script, jamais dans
       la fenêtre du modèle → exactement notre leçon v7 « la recopie est
       l'ennemi » ET notre bug v6 « le catalogue qui grossit noie le 1.5b ».

## Head-to-head avec ce qu'on a déjà
| | /agent/manifest (existant) | pipeline $from (existant) | Code Mode (spike) |
|---|---|---|---|
| découverte | 500 tok | — | SDK ~2.8k tok/72 |
| chaînage | N exchanges | 1 exchange, JSON steps | 1 exchange, JS libre |
| boucles/conditions | non | limité ($from) | oui, gratuits |
| sandbox | n/a (serveur) | n/a (serveur) | à nous (workerd/quickjs) |
| facturation x402 | par appel | 1 call = 1 prix | 1 execute = … ? |

## Verdict: **PARTIAL → POURSUIVRE, mais pas comme prévu**
Le pont fonctionne et résout NOS deux problèmes mesurés cette semaine
(catalogue qui croît vs modèles faibles ; recopie qui perd des valeurs).
Mais : (1) le gain n'est pas la taille du SDK, c'est le nombre d'changes
et l'absence de recopie ; (2) le vrai build = un endpoint mechacut
`POST /api/v1/eval` qui sandbox du JS côté SERVEUR (pas notre processus
FastAPI/Python — un sidecar workerd, ou QuickJS via PyExecJS/quickjs-emscripten),
avec la facturation : **1 execute = 1 appel facturé** quel que soit N
(approfondit le batch, exactement le « un seul appel facturé au lieu de N ») ;
(3) le test qui décide vraiment reste 003 : un 1.5b écrit-il une chaîne
JS qui marche mieux qu'il ne choisit des tools ? À bencher avant de
promettre le pont aux cibles AGENTS-CATALOG.

## Prochaine itération (si go)
- spike 003 : Ollama 1.5b/7b, tâche de bench v7 rejouée via le pont vs tool-calls.
- choix sandbox sidecar (workerd local vs quickjs) — décision d'archi n°1.
- si 003 > tool-calls : bundle « /eval » = 3e brique du produit,
  la plus différenciante (Cloudflare ne SANDBOXE pas, il vend le pattern ;
  nous on vend le calcul déjà sandboxé derrière un prix).
