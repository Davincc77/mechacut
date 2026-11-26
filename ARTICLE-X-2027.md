# The Agent Stack of 2027 Says "Deterministic or Agentic." Nobody Ships the First Word.

*Draft — X long post / article. Suite de « Determinism Will Send AI Where 4KB Took Us »
(chiffres de l'époque : 53 transforms ; aujourd'hui : 187 + 9, vérifiés live 26-11 00h50, prod 1.36.0).
FR version below. ~480 words EN. — passes 23-11 : (a) ripoint 143→170 et rectification
du claim v22b « 0 de 14 » après recomptage des jsonls bruts (incident consigné
dans FINDINGS-V22, même doctrine que la correction de prix V22) ;
(b) ripoint 170→171 et prod 1.16.0→1.17.0 après bundle96 ; (c) 24-11 : 171→179,
prod 1.26.0, suite 1 686 ; (d) 24-11 soir : 179→180 (agent/tool-trim, bundle106),
prod 1.27.0, suite 1 720, pins 322 ; (e) 25-11 01h : 180→181 (shop/withdrawal,
bundle107), prod 1.28.0, suite 1 758, pins 331, manifest 205 lignes / 8 988
octets (comptes lus sur l'en-tête du manifest live, jamais de mémoire) ;
(f) 25-11 06h : 181 INCHANGÉS — bundle108 fait entrer la Belgique et le
Luxembourg sur l'entrée /shop/withdrawal existante (pays en argument,
zéro ligne manifeste neuve), prod 1.29.0, suite 1 784, pins 341, manifest
205 lignes / 8 988 octets vérifiés live ; table des jours fériés
FR/BE/LU/BR/PT/DE/US — le compte des pins lu sur /integrity.json live.
(g) 25-11 08h30 : 181 INCHANGÉS BIS — bundle109 pose les DIALECTES ET
PORTES sur l'entrée /agent/modelid existante (champ additif, zéro ligne
manifeste neuve), prod 1.30.0, suite 1 804, pins 344 (UN pin remplacé par
contrat changé : la V23 gagne son badge « listed ≠ invocable »), manifest
205 lignes / 8 988 octets vérifiés live, pins lues sur /integrity.json live.
(h) 25-11 10h55 : 181→182 (/shop/soldes-lu, bundle110 — la table luxembourgeoise
DATEE PAR ACTE : dix règlements grand-ducaux rejoués, deux rectificatifs de deux
natures — dont celui qui déplace la BORNE de l'été 2023, le Journal officiel
imprimait un « samedi 23 juillet » qui était un dimanche), prod 1.31.0,
suite 1 858, pins 355 (+11 adds-only ; UN pin remplacé par contrat changé :
le pointeur de la sœur belge passe de « en file » à « vivent sous »), manifest
206 lignes / 8 995 octets vérifiés live, pins lues sur /integrity.json live ;
et le plafond landing redevient un contrat POUR LES TROIS LANGUES
(FR 177 028 / EN 179 517 / PT 180 996, lus build-vs-prod identiques — levier
structurel : haystack de recherche dédoublonné, plus ratissage à claim constant).
(i) 25-11 13h35 : 182→183 (/agent/tool-overlap, bundle111 — QUELS DEUX OUTILS
N'EN FONT QU'UN, DANS QUEL CLIENT : table fermée de grammars publiées, grammaires
LUES À LA SOURCE — vscode (coupe 64 + ABORT de la suite alphabétique, le repro
publié 5 outils → 2 listés rejoué en test), gemini-cli (fold head30+tail30,
OVERWRITE dernier gagne), gateway head64 (coupe sans contrôle, production↔preview
épinglé octet à octet), caps OpenAI 64 / Gemini API 128 lus dans leurs specs —
l'asymétrie API-vs-client nommée GATE_STRICTER_THAN_API ; la correction en NOMBRE :
min_server_key_len ou NO_PREFIX_FIX ; prod 1.34.0, suite 1 885, pins 364 (+9
adds-only, vecteurs publics), manifest 207 lignes / 8 997 octets vérifiés live —
la ligne neuve payée par élagage mesuré à claims constants (note b111 dans
routing.py) ; Anthropic : conflit de nom publié, AUCUNE longueur publiée — le
module ne jure pas ce que la source ne publie pas (test d'honnêteté). Les
tranches vitrine de la soeur (brand 1.31.1, network 1.32.0, hero 1.33.0-1) ont
rebaissé les pages : FR 171 187 / EN 174 601 / PT 175 306 build, marge revenue.
(i-bis) 25-11 après-midi : la soeur pose le logo disque (1.34.1), la thèse en tête
et le bench en accordéons (1.34.2), la grille quotidienne VINGT-SEPT cartes câblée
et la coupure « For developers & agents » (1.34.2 bis), puis rétracte son intro
« douze » — compter à la source, pas au screenshot ; suite 1 885 tenue, merge
tenu dans les deux sens (re-génération depuis LEUR make_landing — additif,
jamais merge à la main).)
(j) 25-11 16h25 : 183→184 (/invoice/payment-due, bundle112 — LES QUATRE
LECTURES D'UN NET 30, LE REPORT NOMMÉ PAR ACTE : le gate A CORRIGÉ LA FILE,
deuxième fois classe b110 — civ. 1343 lu à la source est la libération au
NOMINAL, la France FACTURE n'a aucun texte de report en vigueur (1342-1343-5
lus, anciens 1235-1244-1 abrogés ord. 2016-131, loi 1925 abrogée 2007) : le
vide est un VERDICT, la clause tranche — et le report FR existe par INSTRUMENT :
com_l511_79 roule la lettre de change au prochain OUVRABLE, le samedi compte
(L. 3133-1) ; face, § 193 BGB roule le samedi par LA LOI (verbatim lu),
BFDA 1971 s.1(4) roule les bank holidays (table gov.uk lue LIVE, 2026-2028,
hors table NO_TABLE refusé — proclamé jamais prédit) ; couche TARGET2 page BCE
lue : le rail ferme, la dette court (directive 2011/7 art. 3 lus), fermeture
samedi ABSORBÉE nommée (2027-05-01) ; rail GBP : texte CHAPS non lu = aucune
colonne promise. L'oracle tracé main a été PÊCHÉ DEUX FOIS par la machine
(25-déc oublié du jeu TARGET ; ASCENSION 14-mai oubliée du count — 17-juin
est le nombre) et corrigé avant build ; les DIVergences deviennent nombres :
2 jours sur le samedi 6-juin, 8 jours ouvrable-vs-ouvré dans le même pays,
15 jours l'exemple d'État DGCCRF lui-même, 0 jour la fermeture absorbée ;
aucune moyenne rendue — test de thèse. prod 1.34.4, suite 1 924, pins 374
(+10 adds-only), manifest 208 lignes / 8 994 octets lus live — ligne neuve
payée par élagage mesuré à claims constants (« deterministic » tombe de la
tête, le certificateur est le tracteur sha256 ; note b112 routing.py) ;
garde de fratrie pêchée PENDANT le build : mon tag « jours ouvrables »
volait une phrase de comptage — retirée, et le trou rendu à date_calc qui
n'avait AUCUN mot français de comptage (douleur NO_MATCH pêchée par mon
propre test). Aiguilles x3 langues fermées EN PROD par le scan du cycle.)
(k) 25-11 19h45 : 184→185 (/agent/mcp-list-completeness, bundle113 — TON
CLIENT MCP A-T-IL VU TOUTES LES PAGES : SEPT CLIENTS, SIX MOIS, LE MÊME
SILENCE — anything-llm #6935 (« the server remains marked as running »,
fix mergé #6937 dont les trois règles fermées sont la spec du module :
page vide et cursor vide ne finissent pas, cursor répété rejeté), Codex
#28858 ouvert (« the other 2,642 are uncallable », pages 64/64/10), Claude
Code #23179/#48126/#66537, Claude.ai web #87 (21 déclarés, 15 vus),
vercel/ai #19240, openwiki #565 — toutes issues LUES À L'API GitHub, pas
aux snippets ; LA LOI relue verbatim AUX DEUX VERSIONS DU SPEC (raw
GitHub) : la clause « an empty string is a valid cursor and thus MUST NOT
be treated as the end of results » existe en 2026-07-28, PAS en
2025-06-18 — le piège a été NOMMÉ dans le spec, pas deviné ; les curseurs
voyagent comparés octet à octet, JAMAIS parsés (opacité MUST : « 64 »
n'est pas l'offset 64) ; le manque vs ton nombre déclaré devient NOMBRE
(74 / 8 / 6 selon les trois repros), NOMS si tu déclares les tiens,
jamais inventés ; l'oracle main a PÊCHÉ DEUX BÊTES avant module (ordre de
sortie = sévérité déclarée, et son propre double-comptage in-page/across)
— doctrine b112 rejouée. prod 1.34.5, suite 1 952, pins 383 (+9
adds-only, vecteurs PUBLICS), manifest 209 lignes / 8 990 octets lus live
— ligne payée par élagage mesuré à claims constants (label « tiers: »
coupé, « /route?q=words » du milieu coupé — il vit dans le tail, précédent
b112) ; landing x3 re-bakée dans le commit, PT élagué à l'annonce comme
promis (FR 177 271 / EN 179 356 / PT 180 927).)

(l) 25-11 22h35 : 185→186 (/json/bigint, bundle114 — L'ENTIER QUI MENT À LA FRONTIÈRE DE L'OUTIL : RFC 8259 §6 relu à l'RFC Editor (les entiers de [-(2**53)+1, (2**53)-1] sont INTEROPÉRABLES — verbatim ; 1E400 nommé danger), le MUST de la spec MCP draft relu EN CONTEXTE — il porte les entiers x-mcp-header, pas tous les entiers : cité borné, jamais survendu ; cinq issues lues à l'API GitHub (Unity #754, claude-code #11506, llm4s #1597, ragflow PR #22064, audit x402 Go #4258) — deux nombres par finding, le double EXACT et le PRINT JS, que les tickets citent sans les distinguer ; l'émulation Number::toString CERTIFIÉE CONTRE NODE : 240 valeurs, zéro écart ; l'oracle tracé main PÊCHÉ DEUX FOIS par la table node avant module — re-anchor d'exposant après coupe des zéros, et une case de golden où la valeur exacte tenait la place du print (doctrine b112 jouée contre moi, 3e cycle de suite) ; la COLLISION nommée : 2^53 et 2^53+1 se lisent IDENTIQUES — le symptôme du mauvais enregistrement ; scanner de GRAMMAIRE : les chiffres dans les chaînes ne sont jamais des findings, contrairement aux inspectors regex qui l'avouent ; XS radar — l'artifact muet depuis trois cycles rend ENFIN son diff dans le JSON, compteurs réconciliés, invariant vérifié à l'écriture, et la sonde catalogue ne devine plus le TYPE des embeddings par substring (incident mpnet 21h15 : le 400 punissait mon essai, pas le serveur) ; et la mesure LIVE a pêché que Cloudflare injecte 367 octets dans la page SERVIE — le budget landing certifie depuis l'octet du NAVIGATEUR (PT était à 181 294 servis pendant que le test local restait vert ; en chemin : shop_soldes_lu rendait de l'anglais sur la page PT — parité pêchée par le budget). prod 1.35.0, suite 1 984, pins 392 (+9 adds-only, vecteurs PUBLICS), manifest 210 lignes / 8 842 octets lus live — ligne payée par élagage mesuré (les 13 en-têtes de pack cèdent leur chemin à un template de tête, claims constants) ; landing x3 : en 179 984 / fr 178 080 / pt 180 624 app, 180 991 servi — sous plafond réel.)
(m) 26-11 00h50 : 186→187 (/money/settle, bundle115 — QUI PAYE QUI : le graphe
des avances fermé au cent ; r/askmath 1ugli3y rejoué EN ENTIER — A avance 1375,
C 865, C remet la dette de B ; A exige 628,33, B propose 458,33 : le désaccord
EST l'architecture, les DEUX réponses sont justes sur deux graphes et compare
les rend chiffrées côte à côte ; la remise est un ARGUMENT plafonné à la propre
créance du remettant en net — la règle du commentateur rendue exécutable — et à
l'ARÊTE par reçu en itemized, avec l'écart Nommé (118,34 net vs 288,33 par reçu) ;
virements minimaux par partition DP à somme nulle, borne nommée n≤9, greedy
déclaré au-delà ; les cents ferment là où le 746,67×3 du fil ne fermait pas ;
taux en ARGUMENTS, jamais de fetch — la loi du jour de TRANSACTION (tryzedger
14-nov) dans le contrat ; 33 tests dont un ORACLE indépendant (énumération
exhaustive des partitions, écriture différente du DP du module) ; le budget
NAVIGATEUR payé DANS CE commit : vague d'élagage à claims constants sur
12 purposes PT + prose EN, EN 180 625 / FR 179 790 / PT 180 451 app —
servis 180 992 / 180 157 / 180 818, sous 181 000 ; et le contrat que b114
avait écrit dans
un COMMENTAIRE devient une ASSERTION sur les trois langues (itération 15 de la
classe « l'outillage ment » : un commentaire ne rougit jamais). prod 1.36.0,
suite 2 017 passed 2 skipped, pins 400 (+8 adds-only, vecteurs du fil), manifest
211 lignes / 8 883 octets lus live.)

---

## English

If you have read an agent-platform blueprint this year, you have met the sentence:
agents should turn events into signals "deterministically or agentically." Workflows
"mix agentic and deterministic steps." Two words, one stack — and the whole industry
keeps building the second word.

I know what the first word costs, because we priced it.

[mechacut.studio](https://mechacut.studio) is a deterministic transform suite for
agents: **187 transforms + 9 named chain recipes, and growing**, stateless, keyless at
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
déterministes pour agents : **187 transforms + 9 recettes-chaînes nommées, et ça grandit**,
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
