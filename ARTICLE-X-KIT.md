# One Agent Learns, All Agents Learn — How We Secured It, and Why Now

*(X long-form. Every number below is live-verifiable by curl at posting time.
Bench arms named per method: I = harness relayed the tool choice, P = full
pipeline. Both arms published; nothing presented as more autonomous than it is.)*

---

## EN

There is a sentence four of the biggest names in AI have each said, in their
own words, without coordinating:

Anthropic, engineering blog: *"Tools are a new kind of software which
reflects a contract between deterministic systems and non-deterministic
agents."*

OpenAI, Agents SDK docs: *"Orchestrating via code makes tasks more
deterministic and predictable, in terms of speed, cost and performance."*

Peter Steinberger, whose OpenClaw repo grew faster than almost anything in
this field: *"When you push deterministic work through an LLM, things break
in unpredictable ways and you stop trusting the system."*

And Geoffrey Hinton, on why models confabulate: *"We don't store memories;
we generate them."*

Read them together and they describe the same missing thing: the market has
converged on the words. Nobody has shipped the plumbing. Here is the
plumbing, and here is how we made it safe to share.

### The thesis, two lines

When one agent learns a task — really learns it, twice-over, the way an
apprentice learns a trade — every other agent should be able to receive
that learning without trusting the first one. Not its code. Its contract.

### What the suite is, today, in numbers you can curl

`curl https://mechacut.studio/agent/manifest` answers: **170 deterministic
transforms + 9 named recipes.** The free tier is keyless — no account, no
signup, 30/min. Each response carries its sha256. Each refusal names the
field, the expected form and an example. Nothing is stored; the state is in
your hands, by contract.

Since this article was drafted, three more things became true: the network door
ships (`POST /api/v1/agent/propose` — a contract is proposed, never code; verdicts
named ELIGIBLE / SUSPECT-DUPLICATE / DUPLICATE-OF), a public registry answers
"where is my proposal?" (`GET /proposals` — shipped, accepted, en-banc, refused,
each with the why and the first external proposer credited by an adversarial
auditor), and the 50/50 split has a home on-chain: the splitter factory is live on
Base, per-tool clones wait for accepted proposals — born, not yet feeding, and the
docs say so in those words.

Among the transforms are the ones this argument needs:

- `loop/doom-check` — you hand it an agent's tool-call trace; it answers
  DOOM, CYCLIC or STORM — identity judged on canonical bytes, so a loop
  can't hide behind key order. Thresholds are named, never guessed: two
  identical calls are not a loop.
- `eval/compare` — the judge: expected vs got, divergences named by pointer,
  kind, expected, got. Rule born from our own incident: the same quantity is
  never a disagreement (`2.5` equals `"2.50"`, exact Decimal, never float).
- `check/allowlist` — policy as closed grammar: the most specific rule wins,
  ties escalate to the human, silence never authorizes. A regex-shaped
  action is refused, not evaluated: a gate that interprets is a backdoor.

### What "learning" means here, measured

We ran our own models through our own bench, both arms published:

- A 1.5-billion-parameter model, naked: **0/50** tasks. Equipped with the
  suite as a 650-token skill: **45/50** (pipeline arm), 40/50 (relayed arm).
- Across the field, our measured ceiling matches the papers: ToolFailBench
  (arXiv, 2026) puts the best model on Earth — Grok-4.3 — at **86.33%**
  faithful tool use. Even the champion fumbles one call in seven.
- Retries don't fix this: on our V17 bench, retrying a failed call
  multiplied the bill **×4** without converging. On V22b, we asked a model
  to re-emit its own program byte-identically: **0 successes out of 14.**
  Probabilistic machines do not repeat; that is literally their feature.

That last number is the whole argument for sharing contracts instead of
code: if the same agent cannot reproduce its own past output, "share my
script" shares a ghost. The contract — inputs, outputs, goldens, hash —
is the only thing that survives the trip.

### How we secured it

The lifecycle of a lesson, with a sha at every step:

1. **Proposed.** A task done twice (detected on canonical bytes, not vibes)
   becomes a contract: inputs, outputs, and **goldens traced by hand BEFORE
   the implementation exists.** A golden written after the code is not a
   golden — it is a photograph of the implementation. We learned that the
   hard way and our judge incident is published, not hidden.
2. **Gated.** The AST-gate is runtime, not sentiment: pure functions,
   allowlisted imports, no network, no clock (an "as of" date is always an
   argument), size ceilings. No LLM votes on safety.
3. **Pinned.** Every published number is a pin. If a contract's meaning
   drifts — the quiet kind of supply-chain rot where tool #7 starts meaning
   something else — the pins scream before your users notice. This is also
   our alert chain against malicious pushes: what used to pass and no
   longer passes is the exact signature of a poisoned update.
4. **Network-verified.** A second pair of eyes replays the goldens on
   independent infrastructure. One agent's lesson is a rumor; one agent's
   lesson replayed by strangers is a fact.
5. **Contested or revoked.** Divergence is a named state with a hash, not a
   deletion. Refused submissions stay published as measurements — a refused
   contract maps the cliff for everyone who follows.

What is *not* shared across agents: raw code executed on someone else's
machine, memory files, credentials, vibes. Read PROTOCOL-KIT.md in the repo
— the whole lifecycle is spec, not marketing.

### Why now, and why for every agent

Now, because the vocabulary finally matches the hardware: frontier labs
train for verifiable domains (Karpathy: *"LLMs automate what you can
verify"*) while their own docs quietly re-implement deterministic
transformations in every harness — transform tables, protocol shims, retry
budgets — as unpriced, unversioned, unjudged side-work. The best harnesses
already contain a hidden mechacut. We'd rather ship it with a birth
certificate.

For every agent, because the judge is third-party by construction: the
identical bytes that settle a Claude settlement settle a Qwen audit. Our
bench runs mirror arms across model families — same server sha, different
brains — and the small models gain the most: a 1.5B model at 45/50 equipped
beats most of its bigger, naked peers. Capability you can hand across
vendors is the only kind that compounds. And the free core is keyless
precisely so the weakest agent in the room — the one nobody's budget covers
— still gets exact arithmetic.

### What is honestly not built yet

The on-disk kit — the same pure functions, `kit call` instead of curl, the
agent building its own tools through the same gates — is specified
(PROTOCOL-KIT.md, live in the repo) and under construction. The article you
just read is postable because every claim in it is curlable today; that one
sentence isn't a claim, it's a roadmap, and we label it as such.

```
curl https://mechacut.studio/agent/manifest
```

A lesson is a proposal. The bench locks it. That's the whole protocol:
the judge corrects itself, the data ships.

---

## FR

Il y a une phrase que quatre des plus grands noms de l'IA ont chacun dite,
dans leurs propres mots, sans se concerter.

Anthropic, blog engineering : *« Les outils sont une nouvelle sorte de
logiciel qui reflète un contrat entre des systèmes déterministes et des
agents non déterministes. »*

OpenAI, docs Agents SDK : *« Orchestrer par le code rend les tâches plus
déterministes et prévisibles, en vitesse, coût et performance. »*

Peter Steinberger, dont le dépôt OpenClaw a crû plus vite que presque tout
dans ce domaine : *« Quand on force le travail déterministe à passer par un
LLM, les choses cassent de façon imprévisible et on cesse de faire confiance
au système. »*

Et Geoffrey Hinton, sur la confabulation des modèles : *« Nous ne stockons
pas les souvenirs ; nous les générons. »*

Lues ensemble, ces phrases décrivent la même pièce manquante : le marché a
convergé sur les mots. Personne n'a livré la plomberie. Voici la plomberie,
et voici comment nous l'avons rendue sûre à partager.

### La thèse, en deux lignes

Quand un agent apprend une tâche — vraiment, deux fois plutôt qu'une, comme
un apprenti apprend un métier — chaque autre agent devrait pouvoir recevoir
cet apprentissage sans avoir à faire confiance au premier. Pas son code.
Son contrat.

### Ce que la suite est, aujourd'hui, en chiffres vérifiables au curl

`curl https://mechacut.studio/agent/manifest` répond : **158 transformations
déterministes + 9 recettes nommées.** Le palier libre est sans clé — pas de
compte, pas d'inscription, 30/min. Chaque réponse porte son sha256. Chaque
refus nomme le champ, la forme attendue et un exemple. Rien n'est stocké ;
l'état est chez vous, par contrat.

Parmi les transformations, celles dont cet argument a besoin :

- `loop/doom-check` — on lui remet la trace d'appels d'outils d'un agent ;
  il répond DOOM, CYCLIC ou STORM — l'identité jugée en bytes canoniques,
  donc une boucle ne peut pas se cacher derrière l'ordre des clés. Seuils
  nommés, jamais devinés : deux appels identiques ne sont pas une boucle.
- `eval/compare` — le juge : attendu contre obtenu, divergences nommées par
  pointeur, genre, attendu, obtenu. Règle née d'un incident chez nous :
  même quantité n'est jamais un désaccord (`2,5` vaut `"2.50"`, Decimal
  exact, jamais float).
- `check/allowlist` — la politique en grammaire fermée : la règle la plus
  spécifique gagne, les égalités remontent à l'humain, le silence
  n'autorise jamais. Une action en forme de regex est refusée, pas évaluée :
  un gate qui interprète est une porte dérobée.

### Ce que « apprendre » veut dire ici, mesuré

Nous avons fait passer nos propres modèles dans notre propre banc, deux
bras publiés :

- Un modèle de 1,5 milliard de paramètres, nu : **0/50** tâches. Équipé de
  la suite comme skill de 650 jetons : **45/50** (bras pipeline), 40/50
  (bras relais).
- Dans tout le champ, notre plafond mesuré rejoint les papiers :
  ToolFailBench (arXiv, 2026) met le meilleur modèle de la Terre —
  Grok-4.3 — à **86,33 %** d'usage fidèle des outils. Même le champion
  rate un appel sur sept.
- Réessayer ne répare pas : sur notre banc V17, relancer un appel raté
  multipliait la facture **×4** sans converger. Sur V22b, nous avons demandé
  à un modèle de réémettre son propre programme octet pour octet :
  **0 succès sur 14.** Les machines probabilistes ne se répètent pas ;
  c'est littéralement leur fonction.

Ce dernier chiffre est tout l'argument pour partager des contrats au lieu
de codes : si un même agent ne sait pas reproduire sa propre sortie passée,
« partage mon script » partage un fantôme. Le contrat — entrées, sorties,
golds, empreinte — est la seule chose qui survive au voyage.

### Comment nous avons sécurisé

Le cycle de vie d'une leçon, avec un sha à chaque étape :

1. **Proposée.** Une tâche faite deux fois (détectée en bytes canoniques,
   pas à l'impression) devient un contrat : entrées, sorties, et des GOLDS
   TRACÉS À LA MAIN AVANT que l'implémentation existe. Un gold écrit après
   le code n'est pas un gold — c'est une photo de l'implémentation. Nous
   l'avons appris à nos dépens et notre incident de juge est publié, pas
   caché.
2. **Verrouillée.** L'AST-gate est runtime, pas sentiment : fonctions
   pures, imports sur liste nommée, pas de réseau, pas d'horloge murale (la
   date « au » est toujours un argument), plafonds de taille. Aucun LLM ne
   vote la sécurité.
3. **Épinglée.** Chaque chiffre publié est un pin. Si le sens d'un contrat
   dérive — le genre de rouille silencieuse où l'outil n°7 se met à vouloir
   dire autre chose — les pins hurlent avant que vos utilisateurs le
   voient. C'est aussi notre chaîne d'alerte contre les pushes malsains :
   ce qui passait et ne passe plus est la signature exacte d'une mise à
   jour empoisonnée.
4. **Vérifiée en réseau.** Une deuxième paire d'yeux rejoue les golds sur
   une infrastructure indépendante. La leçon d'un agent est une rumeur ; la
   leçon d'un agent rejouée par des inconnus est un fait.
5. **Contestée ou révoquée.** La divergence est un état nommé avec un hash,
   pas une suppression. Les soumissions refusées restent publiées comme
   mesures — un contrat refusé cartographie la falaise pour tous ceux qui
   suivent.

Ce qui n'est PAS partagé entre agents : du code brut exécuté chez autrui,
des fichiers de mémoire, des identifiants, des impressions. Lisez
PROTOCOL-KIT.md dans le dépôt — tout le cycle de vie est spec, pas
marketing.

### Pourquoi maintenant, et pourquoi pour chaque agent

Maintenant, parce que le vocabulaire rejoint enfin la machine : les labs de
pointe entraînent pour des domaines vérifiables (Karpathy : *« les LLM
automatisent ce que vous pouvez vérifier »*) pendant que leurs propres docs
ré-implémentent en silence des transformations déterministes dans chaque
harness — tables de transformation, shims de protocole, budgets de retry —
comme un travail de côté sans prix, sans version, sans juge. Les meilleurs
harnesses contiennent déjà un mechacut caché. Nous préférons le livrer avec
son acte de naissance.

Pour chaque agent, parce que le juge est tiers par construction : les
mêmes bytes qui règlent un litige Claude règlent une audit Qwen. Notre banc
fait tourner des bras miroirs à travers les familles de modèles — même sha
serveur, cerveaux différents — et ce sont les petits modèles qui gagnent le
plus : un 1,5B équipé à 45/50 dépasse la plupart de ses aînés nus. Une
capacité qu'on peut passer d'un vendeur à l'autre est la seule qui
compose. Et le noyau libre est sans clé précisément pour que le plus
faible agent de la pièce — celui que personne ne budgète — ait quand même
droit à l'arithmétique exacte.

### Ce qui n'est honnêtement pas encore construit

Le kit sur disque — les mêmes fonctions pures, `kit call` au lieu de curl,
l'agent construisant ses propres outils par les mêmes portes — est
spécifié (PROTOCOL-KIT.md, en ligne dans le dépôt) et en construction. Cet
article est publiable parce que chaque affirmation qu'il contient est
curlable aujourd'hui ; cette phrase-là n'est pas une affirmation, c'est une
route, et nous la Labellons comme telle.

```
curl https://mechacut.studio/agent/manifest
```

Une leçon est une proposition. Le banc la verrouille. C'est tout le
protocole : le juge se corrige, la donnée se publie.
