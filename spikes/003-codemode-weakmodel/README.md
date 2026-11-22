# Spike 003 — un modèle FAIBLE écrit-il une chaîne code-mode mieux qu'il ne choisit des tools ?

## Question
Given qwen2.5 1.5b & 7b (local, temp 0), when on leur demande de REMPLIR un
programme JS pour le pont code-mode (spike 002) au lieu de CHOISIR un tool
(protocole steps JSON du bench v7) sur la MÊME tâche (note d'incident → JSON),
then le bras code gagne-t-il ? (hypothèse de départ : oui, Cloudflare le vend comme ça)

## Résultats (un-shot, REPAIRS=0, puis avec réparation)

| modèle | bras B (tool-calls) | bras C (code-mode, 1 shot) | bras C (+2 réparations) |
|---|---|---|---|
| 1.5b | 0/5 (hors-sujet, baseline v7) | **✗ 963 tok — `extract_facts is not defined`** (a perdu le préfixe `codemode.`) | ✗ ne converge pas, tokens ×4 |
| 7b  | **5/5 ✓ 1164 tok** (l'arme qui marche) | **✗ 793 tok — `undefined.filter`** : `await codemode.extract_facts(...).facts` — le `.facts` s'applique à la Promise, pas au résultat | ✗ 0/5, 2 réparations n'y changent rien |

## Verdict: **INVALIDATED — ne pas construire /eval comme interface pour modèles faibles**

Le pont code-mode est un échec MESURÉ sur les modèles faibles, pour une raison
structurelle, pas un bug de prompt :

1. **Le 7b passait 5/5 en tool-calls ; le code-mode le FAIT TOMBER à 0.** Le
   bug de précédence `await X().facts` est un piège JS réel (les humains y
   tombent). En demandant au modèle d'écrire le *flow de contrôle*, on
   réintroduit exactement la classe d'erreur que mechacut existe pour supprimer :
   le modèle doit de nouveau être *correct dans un formalisme*, cette fois du
   JavaScript et non du JSON.
2. **La tâche mechacut n'a pas de boucle à économiser.** Code Mode brille quand
   il y a 2500 endpoints et des loops longs (le domaine Cloudflare : DNS→Zero
   Trust→Workers en chaîne). Ici, "remplir extract_facts" est un appel isolé :
   le pont paie tout le risque JS pour ne sauver qu'un aller-retour.
3. **Les modèles faibles n'ont pas la discipline de namespace** (`codemode.`)
   ni la culture async/await : la boucle réparation (renvoyer l'erreur du
   sandbox) ne converge pas en 2 tries — les messages d'exécution VM sont trop
   cryptiques pour eux, contrairement au "errors[]" à la mechacut qui, lui, se
   répare.

## La vraie réponse, et elle est déjà livrée
Pour un modèle faible, le chaînage optimal n'est PAS du code écrit par le
modèle, c'est un **DAG déclaratif exécuté côté serveur** : `/api/v1/pipeline`
(`steps: [{tool, args, $from}]`), déjà en prod. Le modèle nomme des outils et
des refs ; le serveur orchestre ; aucune sémantique JS à rater. C'est
strictement supérieur au code-mode pour la cible AGENTS-CATALOG, et ça n'a pas
été mesuré au hasard : c'est le bras B qui fait 5/5 au 7b ici même.

## Ce que code-mode GARDE comme valeur (honnête, pas de jeter avec l'eau du bain)
Pour un **orchestrateur fort** (Claude/GPT-4o qui a déjà un execute_code et des
centaines d'outils hors mechacut), exposer mechacut comme un seul méta-outil
typé reste défendable — mais c'est un ACHETEUR DIFFÉRENT du "modèle gratuit
qui saute de catégorie". Le pitch faible-modèle ne doit PAS reposer dessus.

## Recommandation
- NE PAS builder `/api/v1/eval` (sandbox JS serveur). Coût d'archi élevé
  (workerd sidecar, sécurité, facturation "1 execute = N calls ?"), bénéfice
  nul sur la cible mesurée.
- Garder `/agent/manifest` (découverte compacte, prouvée) + `/api/v1/pipeline`
  (chaînage déclaratif server-side) comme l'interface officielle, celle qu'on
  met en avant pour les modèles faibles.
- Le finding devient du CONTENU : "on a testé le code-mode de Cloudflare sur
  nos modèles faibles — il leur fait PERDRE un test qu'ils passaient déjà.
  Voici pourquoi un agent faible doit remplir un schéma, pas écrire du JS."
  C'est un post qui se différencie de toute la vague code-mode.
