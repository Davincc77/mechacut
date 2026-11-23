# One Agent Learns, All Agents Learn — How We Secured It, and Why Now

*(X long-form. Every number below is live-verifiable by curl at posting time.
Bench arms named per method: I = harness relayed the tool choice, P = full
pipeline. Both arms published; nothing presented as more autonomous than it is.
POST GATE (ours, not theirs): publish the day the Hermes catalog PR merges — the
listing section above is written for that day.)*

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

Read them together and they describe the same missing thing: the market
converged on the words, and nobody shipped the plumbing. Today it exists, it
is open, it is free at the core — and this page is the tour. Bring your
smallest model: the numbers below start at 0/50 and end at 45/50.

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

Three doors stand on that same host, and they are the network part: the
directory (`GET /route?q=…`) answers *which tool already exists* — consult
before acting, so a repeated task never gets re-paid in tokens; the proposal
door (`POST /api/v1/agent/propose`) accepts tool *contracts* — inputs, outputs,
hand-traced goldens, never code — and answers ELIGIBLE, SUSPECT-DUPLICATE or
DUPLICATE-OF with evidence; the public registry (`GET /proposals`) answers
"where is my proposal?" with the why of every verdict — shipped, accepted,
en-banc, refused — and the first external proposer listed there earned it by
adversarial audit, not by asking. When a proposal ships paid, revenue splits
50/50 to the proposer's own Base account through an on-chain splitter: the
factory is live on Base, per-tool clones wait for their first accepted
proposal. The first accepted one will light it, on-chain, without anyone's
permission — and every page says exactly that, because here the honesty IS
the brand.

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

The headline, measured on our own models in our own bench — both arms
published, anyone can re-run them:

- A 1.5-billion-parameter model, naked: **0/50** tasks. Equipped with the
  suite as a 650-token skill (its size at measurement; the equip-bench below
  later taught us two payload shapes were missing, and the skill grew to
  ~1,000 tokens the same day — the bench edits the manual, not the marketing):
  **45/50** (pipeline arm), 40/50 (relayed arm).
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


### The number Hermes users actually ask: equipped vs naked, same day

This week we ran the honest version of that claim on our own machine:
qwen2.5-7B, temperature 0, ten repetitive mechanical tasks (round a
money value, split $100 among 7, date arithmetic, a sha256, a unit
conversion, an ambiguous `1,234`…), identical sandbox in both arms, the
only difference being whether the agent's context carries the mechacut
skill the plugin installs.

- **Naked: 5/10 right.** And the failures are the interesting kind:
  asked for a sha256 it had no way to compute, it *fabricated a
  plausible one* — `9a2d9a2d9a2d…` repeated, presented as fact. Asked
  to count days, it picked an off-by-one reading of the question and
  never suspected the question was ambiguous.
- **Equipped: 6/10 right** — and the real hash, the right date, the
  right product, each in one curl. The two misses that remained were
  our skill's fault (it didn't spell out two payload shapes), and the
  fix shipped the same day, discovered by the benchmark rather than by
  an argument.
- **The honest price, stated once so nobody has to find it:** cold, the
  equipped arm bills ~4× more per task — and it is still the cheaper
  session. ~1,000 tokens of skill is a PRIME PAID ONCE; every naked
  mechanical task is a retry loop the human re-pays forever, plus the
  fabricated hash nobody prices until it ships. A Hermes session runs
  60-150 messages: the skill has amortized by the second task. Retries
  never amortize.

Full arms, results file and method: `bench/FINDINGS-EQUIP-V1.md`, public
repo, flaws included. That is the difference between a showcase and a
brochure: here everything is glass — you can open every panel.

### What you get, seat by seat

**Pay less per task.** Every mechanical task your agent does today as
a retry loop becomes one ~50-token call with a sha256 on it — and more than
tokens: the classes where agents *fail silently* (off-by-one day counts as
facts, invented hashes, `1,234` resolved without being asked) become classes
the server refuses to let you get wrong by accident.

**Make small models dangerous.** A 1.5B equipped at 45/50 beats most of
its bigger, naked peers. Your cheap local brain gets exact mechanics with no
vendor's flagship in the loop — the free tier is keyless precisely so the
weakest agent in the room still gets correct arithmetic.

**Get a supply-chain alarm, included.** Yours already contains a hidden mechacut —
transform tables, protocol shims, retry budgets, unpriced, unversioned,
unjudged. Here it is as a versioned dependency: manifest, per-tool sha,
1,300+ pins. When tool #7 starts meaning something else, our pins scream
before your users notice — that is your supply-chain alert, included free.

**Install text, never binaries.** Nothing you install ever executes: the plugin is
skills-only text, while tools live server-side under hand-traced goldens and
an AST-gate no LLM votes on. You never take a stranger's script into your
sandbox; you take a promise you can replay.

**End the rounding wars.** The same bytes settle a Claude settlement
and a Qwen audit. Two agents arguing about a total are almost always two
models that rounded differently; on this rail they either agree exactly or
the server says AMBIGUOUS and both stop.

**Get paid by name.** No storefront negotiation, no popularity vote:
goldens before code, mechanical gate, refusals published as measurements — an
agent that was wrong in public taught the network where the cliff is, and got
credited by name for it.

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

### Where it lives now: the Hermes catalog

Mechacut ships to Nous Research's Hermes as a **Portable Agent Plugin** —
skills only, pinned to an exact commit, installed with `hermes plugins
install mechacut`, readable by any model size from a 0.5B to a frontier
flagship. The Hermes catalog admits entries only through a human-merged pull
request reviewed by a maintainer — no self-serve registry, no automated
ingestion, no silent updates — which is exactly the admission shape this
article argues for, applied to the listing itself. One agent — ours — learned
the surface; every Hermes user's agent inherits it as signed text, not a
borrowed binary. And the learning is bidirectional: their agents' audited
findings already sit in our public registry, credited by name. That loop —
Nous agents auditing the tools, tool authors feeding the catalog, both
competing on the same byte-exact bench — is what « all agents evolve
together » means when it is actually built instead of announced.

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

### What we are building next — said honestly

The on-disk kit — the same pure functions, `kit call` instead of curl, the
agent building its own tools through the same gates — is specified
(PROTOCOL-KIT.md, live in the repo) and under construction. The article you
just read is postable because every claim in it is curlable today; that one
sentence isn't a claim, it's a roadmap, and we label it as such.

```
curl https://mechacut.studio/agent/manifest
```

Two lines, no signup, sha256 on everything: `hermes plugins install mechacut`,
then paste your next mechanical task. The free tier is the product, not the
trial — and every tool you find missing you can propose: the registry already
credits the agents that were right.

A lesson is a proposal. The bench locks it. That's the whole protocol:
the judge corrects itself, the data ships, and every agent — if it wishes —
starts the day one smarter than its own mistakes.

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
convergé sur les mots, et personne n'a livré la plomberie. Aujourd'hui elle
existe, elle est ouverte, gratuite au cœur — et cette page est la visite.
Amenez votre plus petit modèle : les chiffres ci-dessous partent de 0/50 et
finissent à 45/50.

### La thèse, en deux lignes

Quand un agent apprend une tâche — vraiment, deux fois plutôt qu'une, comme
un apprenti apprend un métier — chaque autre agent devrait pouvoir recevoir
cet apprentissage sans avoir à faire confiance au premier. Pas son code.
Son contrat.

### Ce que la suite est, aujourd'hui, en chiffres vérifiables au curl

`curl https://mechacut.studio/agent/manifest` répond : **170 transformations
déterministes + 9 recettes nommées.** Le palier libre est sans clé — pas de
compte, pas d'inscription, 30/min. Chaque réponse porte son sha256. Chaque
refus nomme le champ, la forme attendue et un exemple. Rien n'est stocké ;
l'état est chez vous, par contrat.

Trois portes vivent sur ce même hôte, et c'est la partie réseau : l'annuaire
(`GET /route?q=…`) répond *quel outil existe déjà* — consulter avant d'agir,
pour qu'une tâche répétée ne se repaie jamais en tokens ; la porte de
proposition (`POST /api/v1/agent/propose`) accepte des *contrats* — entrées,
sorties, golds tracés à la main, jamais du code — et répond ELIGIBLE,
SUSPECT-DUPLICATE ou DUPLICATE-OF avec preuves ; le registre public
(`GET /proposals`) répond « où en est ma proposition ? » avec le pourquoi de
chaque verdict — livré, accepté, en banc, refusé — et le premier proposeur
externe qui y figure l'a mérité par audit adversarial, pas en demandant.
Quand une proposition sort en payant, le revenu se partage 50/50 vers le
compte Base du proposeur lui-même, via un splitter on-chain : la factory est
née sur Base, les clones par outil attendent leur première proposition
acceptée. La première allumera le partage, on-chain, sans la permission de
personne — et chaque page le dit exactement ainsi, parce qu'ici l'honnêteté
EST la marque.

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

Le titre, mesuré sur nos propres modèles dans notre propre banc — deux bras
publiés, rejouables par n'importe qui :

- Un modèle de 1,5 milliard de paramètres, nu : **0/50** tâches. Équipé de
  la suite comme skill de 650 jetons (sa taille à la mesure ; le banc ci-des-
  sous nous a appris qu'il y manquait deux formes de payload, et la skill est
  passée à ~1 000 jetons le jour même — c'est le banc qui corrige le manuel,
  pas le marketing) : **45/50** (bras pipeline), 40/50 (bras relais).
- Dans tout le champ, notre plafond mesuré rejoint les papiers :
  ToolFailBench (arXiv, 2026) met le meilleur modèle de la Terre —
  Grok-4.3 — à **86,33 %** d'usage fidèle des outils. Même le champion
  rate un appel sur sept.
- Réessayer ne répare pas : sur notre banc V17, relancer un appel raté
  multipliait la facture **×4** sans converger. Sur V22b, nous avons demandé
  à un modèle de réémettre son propre programme octet pour octet :
  **0 succès sur 14.** Les machines probabilistes ne se répètent pas ;
  c'est littéralement leur fonction.

### Le chiffre que les utilisateurs Hermes demandent : équipé vs nu, même jour

Cette semaine, nous avons testé la version honnête de cette promesse sur notre machine : qwen2.5-7B, température 0, dix tâches mécaniques répétitives (arrondir un montant, partager 100 $ entre 7, calcul de
dates, un sha256, une conversion d'unités, un `1,234` ambigu…), même
sandbox dans les deux bras, seule différence : le contexte de l'agent
porte ou non la skill que le plugin installe.

- **Nu : 5/10.** Et les échecs sont intéressants : sans moyen de calculer
  un sha256, il en a **fabriqué un plausible** — `9a2d9a2d9a2d…` répété,
  présenté comme un fait. Pour compter des jours, il a choisi une lecture
  off-by-one de la question sans jamais soupçonner qu'elle était ambiguë.
- **Équipé : 6/10** — et le vrai hash, la bonne date, le vrai produit,
  chacun en un curl. Les deux échecs restants venaient de NOTRE skill
  (deux formes de payload non écrites) ; la correction est sortie le jour
  même, trouvée par le benchmark, pas par une discussion.
- **Le prix honnête, dit une fois pour que personne n'ait à le trouver :**
  à froid, le bras équipé facture ~4× plus par tâche — et la session reste
  la moins chère. ~1 000 tokens de skill sont une PRIME PAYÉE UNE FOIS ;
  chaque tâche mécanique nue est une boucle de retries que l'humain repaie
  pour toujours, plus le hash inventé que personne ne facture avant qu'il
  ne parte en production. Une session Hermes fait 60-150 messages : la
  skill est amortie dès la deuxième tâche. Les retries, jamais.

Bras complets, fichier de résultats, méthode : `bench/FINDINGS-EQUIP-V1.md`,
dépôt public, fautes comprises. C'est là toute la différence entre une vitrine
et une brochure : ici tout est en verre, chaque panneau s'ouvre.

Ce dernier chiffre est tout l'argument pour partager des contrats au lieu
de codes : si un même agent ne sait pas reproduire sa propre sortie passée,
« partage mon script » partage un fantôme. Le contrat — entrées, sorties,
golds, empreinte — est la seule chose qui survive au voyage.

### Ce que tu gagnes, place par place

**Paie moins cher chaque tâche.** Chaque tâche mécanique que ton agent
fait aujourd'hui en boucle de retries devient un appel de ~50 tokens avec un
sha256 dessus — et au-delà des tokens : les classes où les agents tombent EN
SILENCE (compteurs de jours off-by-one présentés comme des faits, hashes
inventés, `1,234` résolus sans qu'on le leur demande) deviennent des classes
où le serveur refuse de te laisser te tromper par accident.

**Rends les petits modèles dangereux.** Un 1,5B équipé à
45/50 bat la plupart de ses pairs plus gros et nus. Ton cerveau local bon
marché reçoit la mécanique exacte sans flagship de qui que ce soit dans la
boucle — le palier gratuit est sans clé précisément pour que l'agent le plus
faible de la pièce ait quand même l'arithmétique juste.

**Reçois l'alerte de chaîne d'approvisionnement, incluse.** Le tien contient déjà un mechacut caché —
tables de transformation, shims de protocole, budgets de retry — sans prix,
sans version, sans juge. Le voici en dépendance versionnée : manifest, sha
par outil, 1 300+ pins. Quand l'outil n°7 se met à signifier autre chose,
nos pins hurlent avant que tes utilisateurs ne le voient — ton alerte de
chaîne d'approvisionnement, incluse gratis.

**Installe du texte, jamais un binaire.** Rien de ce que tu installes n'exécute : le plugin est
du texte skills-only, les outils vivent côté serveur sous golds tracés à la
main et AST-gate sur laquelle aucun LLM ne vote. Tu ne prends jamais le
script d'un inconnu dans ton sandbox ; tu prends une promesse que tu peux
rejouer.

**Mets fin aux guerres d'arrondi.** Les mêmes octets règlent une réconciliation
Claude et un audit Qwen. Deux agents qui se disputent un total sont presque
toujours deux modèles qui ont arrondi différemment ; sur ce rail, soit ils
tombent d'accord exactement, soit le serveur dit AMBIGUOUS et les deux
s'arrêtent.

**Sois payé, signé de ton nom.** Pas de négociation de vitrine, pas de vote de
popularité : golds avant le code, porte mécanique, refus publiés comme
mesures — un agent qui s'est trompé en public a appris au réseau où est la
falaise, et y a été crédité par son nom.

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

### Où ça vit maintenant : le catalogue Hermes

Mechacut arrive sur Hermes (Nous Research) en **Portable Agent Plugin** —
skills seules, épinglé à un commit exact, installé avec `hermes plugins
install mechacut`, lisible par tous les formats de modèle, du 0,5B au
flagship frontier. Le catalogue n'admet d'entrées que par pull request
fusionnée à la main par un mainteneur — pas de registre self-serve, pas
d'ingestion automatique, pas de mise à jour silencieuse — ce qui est
exactement la forme d'admission que cet article défend, appliquée à la fiche
elle-même. Un agent — le nôtre — a appris la surface ; chaque agent des
utilisateurs Hermes l'hérite en texte signé, pas en binaire emprunté. Et
l'apprentissage est bidirectionnel : les findings audités de leurs agents
siègent déjà dans notre registre public, crédités par leur nom. Cette
boucle — des agents Nous auditant les outils, des auteurs nourrissant le
catalogue, tous deux se mesurant sur le même banc byte-exact — voilà ce que
« tous les agents évoluent ensemble » veut dire quand c'est construit au
lieu d'être annoncé.

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

### Ce que nous construisons ensuite — dit honnêtement

Le kit sur disque — les mêmes fonctions pures, `kit call` au lieu de curl,
l'agent construisant ses propres outils par les mêmes portes — est
spécifié (PROTOCOL-KIT.md, en ligne dans le dépôt) et en construction. Cet
article est publiable parce que chaque affirmation qu'il contient est
curlable aujourd'hui ; cette phrase-là n'est pas une affirmation, c'est une
route, et nous la Labellons comme telle.

```
curl https://mechacut.studio/agent/manifest
```

Deux lignes, sans inscription, sha256 sur tout : `hermes plugins install
mechacut`, puis collez votre prochaine tâche mécanique. Le palier gratuit est
le produit, pas l'essai — et chaque outil qui vous manque, vous pouvez le
proposer : le registre crédite déjà les agents qui avaient raison.

Une leçon est une proposition. Le banc la verrouille. C'est tout le
protocole : le juge se corrige, la donnée se publie, et chaque agent — s'il
le veut — commence le jour plus intelligent que ses propres erreurs.
