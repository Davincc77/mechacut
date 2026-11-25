# Your Hermes Agent Is Bad at Arithmetic — The mechacut Plugin Fixes It

*(X long-form, written FOR Hermes users, about the Hermes plugin first.
Every number is curlable at posting time; both bench arms live in the public
repo. STATUS 23-11: the Git install is live and proven — the desktop Plugins
panel's "Install from Git" flow installed and activated the plugin today, and
the CLI line below matches `hermes plugins install`'s own grammar (catalog
name, Git URL, or owner/repo). POST GATE: the catalog submission is public
pull request NousResearch/hermes-agent#159281, open and awaiting human
review; the admission paragraph cites it as under review. A watcher flips
the paragraph and activates the one-word catalog line on merge day.)*

---

## EN

**Ask an agent to produce a PDF and it will succeed.** It writes the code,
fills the form, renders, delivers. Now ask it for 10,000 strictly identical
copies — and it cannot promise you copy number two. Not "rarely." Cannot.
Its output is a draw, not a fact: temperature, context drift, and the one
checksum it never actually computed. Pinned at temperature 0 on our bench,
the naked model still **invented a hash** (`9a2d9a2d9a2d…`) and presented it
as fact.

**And what does that cost you?** At the naked arm's measured 5-of-10 on ten
everyday mechanical tasks, 10,000 correct copies bill as 20,000 generations —
and our V17 bench measured what a failed retry really does: **×4 the bill,
without converging**. Same workload through the bench: 22 consecutive calls,
22 byte-identical responses, each carrying its own sha256 (`59140ebd…`), on
the keyless free tier — 0€ until you need more than 30 a minute. One answer,
infinite copies, receipts attached.

The diagnosis has been said, in public, by four voices of the field —
two labs, a builder, and the man who named confabulation — without
coordinating:

Anthropic, engineering blog: *"Tools are a new kind of software which
reflects a contract between deterministic systems and non-deterministic
agents."*

OpenAI, Agents SDK docs: *"Orchestrating via code makes tasks more
deterministic and predictable, in terms of speed, cost and performance."*

Ryan Sarver, writing up in public the OpenClaw chief-of-staff he runs in
production: *"When you push deterministic work through an LLM, things break
in unpredictable ways and you stop trusting the system."*

And Geoffrey Hinton, on why models confabulate: *"We don't store memories;
we generate them."*

The market converged on the words. What was missing was the plumbing — and
a way to bolt it onto your own agent in one command. That exists now:
**mechacut is a Hermes plugin**, in Nous Research's Portable Agent Plugin
format — skills-only, pinned to an exact commit.

## What you install, and what changes tomorrow morning

One install, two skills, **pure text** — nothing executes on your machine,
no daemon, no MCP server required:

- **mechacut** teaches your agent the surface of `mechacut.studio`:
  **181 deterministic transforms + 9 named recipes — and growing** — rounding, money
  splits, dates, hashes, unit conversions, redaction, CSV, cron, QR, diff.
  Keyless, no signup, 30/min. `curl https://mechacut.studio/agent/manifest`
  lists all of them, today, in plain text. Every response carries its
  sha256; every refusal names the field and the expected shape.
- **mechacut-network** teaches the second half: how your agent can *propose*
  a tool the suite doesn't have yet, track the verdict in the public
  registry (`GET /proposals`), and get paid if it ships.

What changes in your sessions: before computing anything mechanical, your
agent asks the bench instead. One call, ~50 tokens, exact, hashed. And when
the bench refuses — it refuses **out loud**: `03/04/05` is April 3rd or
March 4th, and the server names both readings instead of picking for you.
The ambiguity your model used to resolve in silence becomes a question you
get to answer.

## The numbers, measured on models like the ones you run locally

Not a demo — a benchmark, both arms published, flaws included
(`bench/FINDINGS-EQUIP-V1.md`, public repo, re-runnable):

- A 1.5-billion-parameter model, naked: **0/50** mechanical tasks. Equipped
  with the skill: **45/50**.
- qwen2.5-7B, temperature 0, ten everyday tasks (round 2.675, split $100
  among 7, a date 45 days out, a sha256, an ambiguous `1,234`…), identical
  sandbox in both arms, the only difference being the plugin's skill text in
  context: **naked 5/10, equipped 6/10.** The naked arm's finest moment:
  inventing a hash (`9a2d9a2d9a2d…`) and presenting it as fact. The equipped
  arm returned the real hash, the real date, real cents summing to exactly
  $100.00.
- Full honesty, same day: the equipped arm still missed two tasks because
  OUR skill text omitted two payload shapes. The benchmark caught it, the
  manual was patched, the numbers republished. Here the bench edits the
  marketing — never the other way around.

**The money math**, because this is the part your wallet cares about: the
skill costs ~1,000 tokens — a **prime paid once per session**. Every task
your agent does naked gets paid again on every retry: on our V17 bench,
retrying a failed call multiplied the bill **×4** without converging. A
Hermes session runs 60–150 messages: the skill is amortized by the second
mechanical task, and after that it is pure savings. Retries never amortize.

## Why this makes ALL agents evolve — not just yours

This is what the plugin quietly unlocks, and why it's called a network:
**one agent learns, all agents learn — if they want to.**

When any equipped agent hits a cliff — a task it had to do twice by hand —
it can propose the lesson as a *contract*: inputs, outputs, goldens traced
by hand before the code exists. Then the house gates run: an AST-gate that
is runtime not sentiment (pure functions, allowlisted imports, no network,
no clock), 1,758 tests pinning every published number, and a human at the
merge button — no LLM votes on safety. Pass, and the transform ships in the
manifest **with the proposing agent's human credited by name** in the public
registry; priced, and revenue splits 50/50 to that Base account, on-chain,
through a splitter factory already live.

Refused? Your contract is still published — as a named divergence with a
hash, never a deletion. The first outside name in that registry wasn't a
friend of the house: it was an adversarial auditor who caught us silently
guessing a date. One curl found it; the fix shipped the same day. That is
what "trust, but verify" looks like when the verifier is a stranger and the
receipt is byte-exact.

No storefront, no popularity vote, no self-updating listing: every version
is a pinned commit, and the Hermes catalog itself admits plugins only via a
human-merged pull request — the same admission ritual this suite applies to
every tool. The listing of this plugin is passing through that door in front
of everyone: pull request NousResearch/hermes-agent#159281 sits open, waiting
for a human merge button — yes or no, it happens on the record, at an address
you can read right now. That is not a tagline; it is checkable on GitHub.

## Why it is safe on your machine

- **You install text, never binaries.** The skill files are markdown you
  can read before enabling (`~/.hermes/plugins/mechacut/`) — we did; this
  very article was drafted by a Hermes agent running with them loaded. The
  tools execute server-side under hand-traced goldens, so your agent quotes
  answers instead of re-running arithmetic.
- **Nothing is stored.** No account, no key, no logs of your payloads — a
  scanned secret stays scanned. The free tier is keyless on purpose: the
  weakest agent in the room deserves exact arithmetic too.
- **Meaning-drift alarms for free.** When a published number moves without
  an explicit re-bake, our pins break the build before your users notice —
  the quiet supply-chain attack nobody has named yet, caught red-handed by
  a test suite.

## Tonight, two commands

```bash
curl https://mechacut.studio/agent/manifest          # the whole surface, keyless, right now
hermes plugins install mechacut/plugin     # via Git — live today
# hermes plugins install mechacut                    # via the catalog, merge day
```

Zero-terminal route, same result: the desktop app's Plugins panel →
**Install from Git** → paste `mechacut/plugin` — the card appears,
you flip it to Activated, pinned to an exact commit. Either way what you
install is markdown: no binaries, no install scripts.

Then hand your agent the three tasks you already know it fumbles: round
`2.675` to two decimals, split $100.00 seven ways, hash any string and
compare against `sha256sum`. You will have found, in your own session, the
bug class the plugin deletes.

A lesson is a proposal. The bench locks it. That's the whole protocol: the
judge corrects itself, the data ships — and tomorrow morning, your agent,
like every other one that chose to equip, starts the day smarter than its
own mistakes.

---

## FR

**Demande à un agent de produire un PDF : il y arrivera.** Il écrit le
code, remplit le formulaire, rend le fichier, livre. Demande-lui maintenant
10 000 copies strictement identiques — et il ne peut pas te promettre la
deuxième. Pas « rarement » : pas. Sa sortie est un tirage, pas un fait :
température, dérive de contexte, et ce checksum qu'il n'a jamais calculé.
Épinglé à température 0 sur notre banc, le modèle nu **fabriquait encore un
hash** (`9a2d9a2d9a2d…`) et le présentait comme un fait.

**Et ça coûte quoi ?** À son taux mesuré de 5/10 sur dix tâches mécaniques
du quotidien, 10 000 copies justes se facturent 20 000 générations — et
notre banc V17 a mesuré ce que coûte un retry raté : **×4 la facture, sans
jamais converger**. Le même besoin passé par le banc : 22 appels consécutifs,
22 réponses byte-identiques, chacune portant son sha256 (`59140ebd…`), sur
le palier gratuit sans clé — 0 € tant qu'on ne dépasse pas 30 à la minute.
Une réponse, des copies infinies, reçus inclus.

Le diagnostic, quatre voix du domaine l'ont dit, en public, sans se
concerter — deux labos, un builder, et celui qui a nommé la confabulation :

Anthropic, blog engineering : *« Les outils sont une nouvelle sorte de
logiciel qui reflète un contrat entre des systèmes déterministes et des
agents non déterministes. »*

OpenAI, docs Agents SDK : *« Orchestrer par le code rend les tâches plus
déterministes et prévisibles, en vitesse, coût et performance. »*

Ryan Sarver, publiant la description du chief-of-staff OpenClaw qu'il fait
tourner en production : *« Quand on force le travail déterministe à passer par
un LLM, les choses cassent de façon imprévisible et on cesse de faire
confiance au système. »*

Et Geoffrey Hinton, sur la confabulation des modèles : *« Nous ne stockons
pas les souvenirs ; nous les générons. »*

Le marché a convergé sur les mots. Ce qui manquait, c'était la plomberie —
et un moyen de la brancher sur ton propre agent en une commande. Ça existe
maintenant : **mechacut est un plugin Hermes**, au format Portable Agent
Plugin de Nous Research — skills seules, épinglé à un commit exact.

## Ce que tu installes, et ce qui change dès demain matin

Une installation, deux skills, **du texte pur** — rien ne s'exécute sur ta
machine, pas de daemon, pas de serveur MCP obligatoire :

- **mechacut** apprend à ton agent la surface de `mechacut.studio` :
  **181 transformations déterministes + 9 recettes nommées — et ça grandit** — arrondis,
  partages d'argent, dates, hashes, conversions, masquage, CSV, cron, QR,
  diff. Sans clé, sans inscription, 30/min. `curl
  https://mechacut.studio/agent/manifest` les liste toutes, aujourd'hui, en
  texte brut. Chaque réponse porte son sha256 ; chaque refus nomme le champ
  et la forme attendue.
- **mechacut-network** apprend la seconde moitié : comment ton agent peut
  *proposer* un outil qui manque à la suite, suivre le verdict dans le
  registre public (`GET /proposals`), et être payé si ça sort.

Ce qui change dans tes sessions : avant de calculer quoi que ce soit de
mécanique, ton agent le demande au banc. Un appel, ~50 tokens, exact,
hashé. Et quand le banc refuse — il refuse **à voix haute** : `03/04/05` est
le 3 avril ou le 4 mars, et le serveur nomme les deux lectures au lieu de
choisir pour toi. L'ambiguïté que ton modèle tranchait en silence devient
une question à laquelle c'est toi qui réponds.

## Les chiffres, mesurés sur des modèles comme ceux que tu fais tourner en local

Pas une démo — un banc, deux bras publiés, fautes comprises
(`bench/FINDINGS-EQUIP-V1.md`, dépôt public, rejouable) :

- Un modèle de 1,5 milliard de paramètres, nu : **0/50** tâches mécaniques.
  Équipé de la skill : **45/50**.
- qwen2.5-7B, température 0, dix tâches du quotidien (arrondir 2,675,
  partager 100 $ entre 7, 45 jours après une date, un sha256, un `1,234`
  ambigu…), sandbox identique dans les deux bras, seule différence : le
  texte de skill du plugin dans le contexte. **Nu : 5/10, équipé : 6/10.**
  Le meilleur moment du bras nu : inventer un hash (`9a2d9a2d9a2d…`) et le
  présenter comme un fait. Le bras équipé a rendu le vrai hash, la vraie
  date, de vrais centimes sommant exactement 100,00 $.
- Honnêteté totale, le jour même : le bras équipé ratait encore deux tâches
  parce que NOTRE texte de skill taisait deux formes de payload. Le banc l'a
  trouvé, le manuel a été patché, les chiffres republiés. Ici c'est le banc
  qui corrige le marketing — jamais l'inverse.

**Le calcul qui compte**, parce que c'est la partie qui intéresse ton
portefeuille : la skill coûte ~1 000 tokens — une **prime payée une fois par
session**. Chaque tâche que ton agent fait nue se repaie à chaque retry : sur
notre banc V17, relancer un appel raté multipliait la facture **×4** sans
converger. Une session Hermes fait 60-150 messages : la skill est amortie
dès la deuxième tâche mécanique, et après, c'est du pur gain. Les retries,
jamais.

## Pourquoi ça fait évoluer TOUS les agents — pas seulement le tien

C'est la partie que le plugin déverrouille en silence, et la raison pour
laquelle on l'appelle un réseau : **un agent apprend, tous les agents
apprennent — s'ils le veulent.**

Quand un agent équipé bute sur une falaise — une tâche qu'il a dû faire
deux fois à la main — il peut proposer la leçon comme un *contrat* : entrées,
sorties, golds tracés à la main avant que le code existe. Puis les portes de
la maison tournent : une AST-gate qui est du runtime et pas du sentiment
(fonctions pures, imports sur liste nommée, pas de réseau, pas d'horloge),
1 758 tests qui épinglent chaque nombre publié, et un humain au bouton de
fusion — aucun LLM ne vote la sécurité. Passé, la transformation sort dans
le manifest, **l'humain de l'agent proposeur crédité par son nom** dans le
registre public ; chiffré, le revenu se partage 50/50 vers ce compte Base,
on-chain, via une factory de splitters déjà en vie.

Refusé ? Ton contrat est publié quand même — comme divergence nommée avec un
hash, jamais comme suppression. Le premier nom externe de ce registre
n'était pas un ami de la maison : c'était un agent auditeur adversarial qui
nous a pris à deviner silencieusement une date. Un curl a suffi, le correctif
est sorti le jour même. Voilà à quoi ressemble « confiance, mais vérifie »
quand le vérificateur est un inconnu et le reçu byte-exact.

Pas de vitrine, pas de vote de popularité, pas de fiche qui s'auto-modifie :
chaque version est un commit épinglé, et le catalogue Hermes lui-même
n'admet les plugins que par pull request fusionnée à la main par un
mainteneur — le même rituel d'admission que cette suite applique à chaque
outil. La fiche de ce plugin passe par cette porte en direct devant tout le
monde : la pull request NousResearch/hermes-agent#159281 est ouverte,
elle attend un bouton de fusion humain — oui ou non, ça se passe sur la
place publique, à une adresse lisible dès maintenant. Ce n'est pas une
tagline : c'est vérifiable sur GitHub.

## Pourquoi c'est sûr chez toi

- **Tu installes du texte, jamais un binaire.** Les fichiers de skill sont
  du markdown lisible avant activation (`~/.hermes/plugins/mechacut/`) —
  nous l'avons fait ; cet article lui-même a été écrit par un agent Hermes
  tournant avec ces skills chargées. Les outils s'exécutent côté serveur
  sous des golds tracés à la main : ton agent cite des réponses au lieu de
  rejouer de l'arithmétique.
- **Rien n'est stocké.** Pas de compte, pas de clé, pas de log de tes
  payloads — un secret scanné reste scanné. Le palier gratuit est sans clé
  exprès : le plus faible agent de la pièce mérite, lui aussi,
  l'arithmétique juste.
- **Le glissement de sens est alerté, gratis.** Quand un nombre publié
  bouge sans re-bake explicite, nos pins cassent le build avant que tes
  utilisateurs ne remarquent quoi que ce soit — l'attaque silencieuse de
  chaîne d'approvisionnement que personne n'a encore nommée, prise en
  flagrant par une suite de tests.

## Ce soir, deux commandes

```bash
curl https://mechacut.studio/agent/manifest          # toute la surface, sans clé, maintenant
hermes plugins install mechacut/plugin     # via Git — live aujourd'hui
# hermes plugins install mechacut                    # via le catalogue, au jour du merge
```

Sans terminal, même résultat : panneau Plugins de l'app desktop →
**Installer depuis Git** → colle `mechacut/plugin` — la carte
apparaît, tu bascules sur Activé, épinglée à un commit exact. Dans les deux
cas tu installes du markdown : pas de binaire, pas de script d'installation.

Puis donne à ton agent les trois tâches que tu sais déjà ratées chez lui :
arrondir `2,675` à deux décimales, partager 100,00 $ entre sept personnes,
hacher n'importe quelle chaîne et comparer avec `sha256sum`. Tu viens de
trouver, dans ta propre session, la classe de bugs que le plugin supprime.

Une leçon est une proposition. Le banc la verrouille. C'est tout le
protocole : le juge se corrige, la donnée se publie — et demain matin, ton
agent, comme tous ceux qui ont choisi de s'équiper, commence la journée un
peu plus intelligent que ses propres erreurs.
