# The Agent Stack of 2027 Says "Deterministic or Agentic." Nobody Ships the First Word.

*Draft — X long post / article. Suite de « Determinism Will Send AI Where 4KB Took Us »
(chiffres de l'époque : 53 transforms ; aujourd'hui : 180 + 9, vérifiés live 24-11 soir, prod 1.27.0).
FR version below. ~480 words EN. — passes 23-11 : (a) ripoint 143→170 et rectification
du claim v22b « 0 de 14 » après recomptage des jsonls bruts (incident consigné
dans FINDINGS-V22, même doctrine que la correction de prix V22) ;
(b) ripoint 170→171 et prod 1.16.0→1.17.0 après bundle96 ; (c) 24-11 : 171→179,
prod 1.26.0, suite 1 686 ; (d) 24-11 soir : 179→180 (agent/tool-trim, bundle106),
prod 1.27.0, suite 1 720, pins 322 (comptes lus sur l'en-tête du manifest live,
jamais de mémoire).

---

## English

If you have read an agent-platform blueprint this year, you have met the sentence:
agents should turn events into signals "deterministically or agentically." Workflows
"mix agentic and deterministic steps." Two words, one stack — and the whole industry
keeps building the second word.

I know what the first word costs, because we priced it.

[mechacut.studio](https://mechacut.studio) is a deterministic transform suite for
agents: **180 transforms + 9 named chain recipes, and growing**, stateless, keyless at
30 requests/minute. Every response carries its own `sha256`. Every 400 carries the
field, the expected format and an example — the error is the prompt that fixes the
next call. And a surface we shipped this week, `/api/v1/router/apply`, takes a
word problem as prose, matches it against a closed grammar, and runs the whole
chain on the server — **zero LLM calls** — returning the answer with its checksum.
Feed it anything outside the grammar and it says so, explicitly. It never guesses.
(That is the feature. The guessing is what you keep paying the second word for.)

This week we measured the frontier, because after a dozen benches on small local
models, the honest objection is: *that is a dwarf problem.* Seven chained word
problems ("40% of the rest…", "the second receives 1/4 of the rest…") × three
frontier models × three arms — golds frozen before the first cell, everything
published raw (`bench/results_v22.jsonl`, $0.0344):

- **Naked:** 10/21 — one model 7/7, another 0/7. There is no frontier class.
  There are families, temperaments, luck.
- **Let the model write Python:** 21/21 numerically right. We published that even
  though it cuts against us. The shell camp's promise is true — on a job that runs
  once.
- **Frozen recipe** (the model transcribes, the server computes): 19/21. Every
  failure was on the model side — no JSON at all, or a miscopied number — and the
  server answered correctly anyway on whatever it was handed.

Then the bench that matters to anyone who runs a job more than once. Five repeats
of the *winning* arm at agent temperature (0.7): 70/70 numerically right — and the
identical program came back twice in only **3 of 14** model-problem pairs, and never
as a stable artifact: the other 11 rewrote it every pass. Code new each time, one
decimal tail in the mix (`776.6000000000000000000000002`), each run right, the answer
changing shape in 8 of 14 pairs. The frozen server, same 70 controls: one sha per problem, every time.
A model that is right is not a model that is reproducible. Production is the second
one. Retry does not fix any of this — measured too: five samples on a systematic
miss, unanimous on the same wrong number, ×4 the bill. Repeating is not thinking,
and sampling is not evidence.

We put people on the Moon with 4 KB of RAM and 72 KB of ROM because the math was
never asked to improvise. Constants were computed once, on the ground, in cold
blood, and frozen into rope. The computer did not reason about trajectories at
30,000 feet per second — it looked up what determinism had already proven.

The 2027 stack says "deterministic or agentic." Both words will ship. We sell the
first one: priced, versioned, curlable right now.

`curl https://mechacut.studio/agent/manifest`

Answering right once is a demo. Being identical every day is infrastructure.

---

## Français (version X / LinkedIn FR)

Si vous avez lu un manifeste de « plateforme d'agents » cette année, vous êtes
tombés sur la phrase : les agents doivent traduire les événements en signaux
« déterministiquement ou agentiquement ». Les workflows « mélangent étapes
agentiques et déterministes ». Deux mots, une pile — et toute l'industrie
construit le deuxième mot.

Le premier mot, on sait ce qu'il coûte : on l'a chiffré.

[mechacut.studio](https://mechacut.studio) est une suite de transforms
déterministes pour agents : **180 transforms + 9 recettes-chaînes nommées, et ça grandit**,
sans état, 30 requêtes/minute sans clé. Chaque réponse porte son propre
`sha256`. Chaque 400 porte le champ, le format attendu et un exemple —
l'erreur est le prompt qui répare l'appel suivant. Et une surface sortie cette
semaine, `/api/v1/router/apply`, prend un problème d'énoncé en prose, le matche
contre une grammaire fermée, et fait tourner la chaîne entière côté serveur —
**zéro appel de LM** — et rend la réponse avec son empreinte. Hors grammaire,
elle le dit explicitement. Elle ne devine jamais. (C'est ça, la fonctionnalité.
Le devinage, c'est exactement ce que le deuxième mot vous facture.)

Cette semaine, on a mesuré la frontière, parce qu'après une douzaine de bancs
sur petits modèles locaux, l'objection honnête est : *c'est un problème de
nains.* Sept problèmes à chaîne (« 40 % du reste… », « la seconde reçoit 1/4
du reste… ») × trois modèles frontière × trois bras — golds gelés avant la
première cellule, brut publié (`bench/results_v22.jsonl`, 0,0344 $) :

- **Nu :** 10/21 — un modèle à 7/7, un autre à 0/7. Il n'existe pas de classe
  frontière. Il existe des familles, des tempéraments, de la chance.
- **Le modèle écrit son Python :** 21/21 justes numériquement. Publié contre
  nous. La promesse du camp shell est vraie — sur un job qui tourne une fois.
- **Fiche gelée** (le modèle recopie, le serveur calcule) : 19/21. Chaque
  échec était du côté modèle — pas de JSON du tout, ou un nombre mal recopié —
  et le serveur, lui, a répondu juste sur ce qu'on lui donnait.

Puis le banc qui compte pour quiconque exécute un job plus d'une fois. Cinq
repasses du *bras gagnant* en température d'agent (0,7) : 70/70 justes
numériquement — et le même programme n'est revenu deux fois que dans **3 paires
sur 14** modèle-problème, et jamais comme artefact stable : les 11 autres l'ont
réécrit à chaque passe. Code nouveau à chaque fois, une queue de float dans le lot
(`776.6000000000000000000000002`), chaque course juste, la réponse changeant de
forme dans 8 paires sur 14. Le serveur gelé, mêmes 70 contrôles : un sha par
problème, à chaque fois. Un modèle qui a raison n'est pas un modèle reproductible.
La production, c'est le second.
Le retry n'y change rien — mesuré aussi : cinq échantillons sur une erreur
systématique, unanimes sur le même faux nombre, ×4 la facture. Répéter n'est pas
penser, et échantillonner n'est pas prouver.

On a mis des humains sur la Lune avec 4 Ko de RAM et 72 Ko de ROM parce que le
calcul n'a jamais eu à improviser. Les constantes ont été calculées une fois, à
terre, à froid, puis gelées dans la corde. L'ordinateur ne raisonnait pas sur la
trajectoire à 9 000 m/s — il consultait ce que le déterminisme avait déjà prouvé.

La pile de 2027 dit « déterministe ou agentique ». Les deux mots seront livrés.
Nous, on vend le premier : chiffré, versionné, vérifiable d'un curl.

`curl https://mechacut.studio/agent/manifest`

Avoir raison une fois est une démo. Être identique tous les jours est une
infrastructure.
