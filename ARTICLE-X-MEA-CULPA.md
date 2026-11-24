# We Wrote "Every Number Is Curlable." A Day Later, Our Own Numbers Weren't.

*(Post-MERGE article. HARD GATE: do not post until the plugin is officially in
the Hermes catalog — entry `mechacut` visible in
https://hermes-agent.nousresearch.com/docs/api/plugin-catalog.json AND the PR
merge visible on NousResearch/hermes-agent#159281. On merge day, the watcher
fills [MERGE-DATE] and flips the header; then it is ready to post, EN below,
FR after. Companion piece to "Your Hermes Agent Is Bad at Arithmetic" — that
one stands; this one is about what happened the day after.)*

---

## EN

**The article made one promise above all: every number in it is curlable at
posting time.** Numbers with dates, checks you can run yourself, a bench that
edits the marketing instead of the other way around. We stand behind all of
it.

Twenty-four hours later, three things were true — and we found them the
honest way, by being checked:

**1. Our own numbers went stale inside a day.** The article said 171
deterministic transforms. The live manifest said 178 that evening — because
the suite ships tools faster than prose can chase them. Nobody was harmed:
the missing transforms were real additions, not errors. But a post about
verifiable facts citing a verifiable-fact-count was three bundles out of
date. Fix: every published number now carries its reading date and the live
pointer (`GET /agent/manifest`), and the catalog entry's description was
stripped of datable counts entirely — the manifest is the count.

**2. We misattributed a quote.** The line *"When you push deterministic
work through an LLM, things break in unpredictable ways and you stop
trusting the system"* — we attributed it to Peter Steinberger, because a
wiki page said so. It's actually **Ryan Sarver's**, word for word, from the
post where he describes the OpenClaw chief-of-staff he runs in production.
The sentence was right. The name above it was wrong. Lesson logged as
doctrine: a quote is a number — it must be curlable to the person who said
it, not to whoever hosts the sentence now.

**3. A human reviewer at the gate found the one that actually mattered.**
Our own skill file taught agents to scan a log for leaked secrets by
uploading that log to our API — sending the very text you suspect holds
credentials to a third party, to protect it. Our server stores nothing, and
it was still the wrong instruction to put in a model's hand. This wasn't
caught by marketing feedback; it was caught by the catalog's human review —
the door this whole suite preaches — and it went into the article's own
safety section as a selling point while sitting as a flaw in the docs.
Fix, same day: the example is bounded to text the human *explicitly chose*
to send, with the line "the full text leaves the machine" printed above the
call, and the disclosure in the catalog entry says plainly that these are
ordinary HTTPS requests — the harness does not prompt you per call.

**And that's the actual thesis, not a spin.** Items 1 and 2 were mistakes
without consequences — a stale count, a wrong name — and fixing them cost an
evening. Item 3 was a mistake *with* consequences, and it died precisely
because the admission ritual for the catalog is a stranger reading your
text and a human holding the merge button. No LLM voted on any of this.
Nothing published was deleted: the corrections ship as dated fixes, visible
in the public repo, because that is what "the bench edits the marketing"
means when the bench turns on you.

[On MERGE-DATE, Nous Research merged this plugin into the official Hermes
catalog — after the review above.] You can check the catalog feed, the
manifest, the registry, the diff of every fix. We were not perfect in the
first post. The system we were pitching is the one that caught us — twice
over a number, once over a name, and once, crucially, over a safety claim
in our own instruction manual.

Same request, same bytes. Even when the request is: check us.

---

## FR

**L'article ne promettait qu'une chose par-dessus tout : chaque nombre est
vérifiable par curl à l'heure de publication.** Des chiffres datés, des
vérifications que vous pouvez faire vous-mêmes, un banc qui édite le
marketing et non l'inverse. On le maintient, mot pour mot.

Vingt-quatre heures plus tard, trois choses étaient vraies — et on les a
trouvées honnêtement, en se laissant vérifier :

**1. Nos propres chiffres ont séché dans la journée.** L'article disait 171
transformations déterministes. Le manifest live en affichait 178 le soir
même — parce que la suite livre des outils plus vite que la prose ne peut
les rattraper. Personne n'a été lésé : les transformations manquantes
étaient des ajouts réels, pas des erreurs. Mais un post sur les faits
vérifiables citait un nombre de faits vérifiables périmé de trois bundles.
Corrigé : chaque nombre publié porte désormais sa date de relevé et son
pointeur live (`GET /agent/manifest`), et la fiche du catalogue a été
vidée de tout nombre datable — le manifest EST le comptage.

**2. On a mal attribué une citation.** La phrase *« Quand on force le
travail déterministe à passer par un LLM, les choses cassent de façon
imprévisible et on cesse de faire confiance au système »* — on l'avait
créditée à Peter Steinberger, parce qu'un wiki le disait. Elle est de
**Ryan Sarver**, mot pour mot, dans le post où il décrit le chief-of-staff
OpenClaw qu'il fait tourner en production. La phrase était juste. Le nom
au-dessus était faux. Leçon inscrite comme doctrine : une citation est un
nombre — elle doit être vérifiable jusqu'à la bouche qui l'a dite, pas
jusqu'au site qui l'héberge.

**3. Un relecteur humain à la porte a trouvé celle qui comptait vraiment.**
Notre propre fichier de skill apprenait aux agents à scanner un log pour y
trouver des secrets en envoyant ce log à notre API — envoyer précisément le
texte qu'on soupçonne contenir des identifiants vers un tiers, pour le
protéger. Notre serveur ne stocke rien, et c'était quand même la mauvaise
instruction à mettre dans la main d'un modèle. Ça n'a pas été trouvé par un
retour marketing ; ça a été trouvé par la revue humaine du catalogue — la
porte que cette suite prêche depuis le début — et pendant que l'article en
faisait un argument de sécurité, le défaut vivait dans la doc. Corrigé le
jour même : l'exemple est borné au texte que l'humain a **explicitement
choisi** d'envoyer, la ligne « le texte complet quitte votre machine » est
imprimée au-dessus de l'appel, et la disclosure du catalogue dit
platement qu'il s'agit de requêtes HTTPS ordinaires — le harnais ne vous
demande pas confirmation à chaque appel.

**Et c'est ça, la thèse — pas une figure de style.** Les points 1 et 2
étaient des erreurs sans conséquence : un compteur périmé, un mauvais nom —
les corriger a coûté une soirée. Le point 3 était une erreur **avec**
conséquences, et elle est morte précisément parce que le rituel d'admission
du catalogue, c'est un inconnu qui lit votre texte et un humain qui tient
le bouton de fusion. Aucun LLM n'a voté pour rien de tout ça. Rien de publié
n'a été effacé : les corrections sortent comme des rustines datées,
visibles dans le dépôt public, parce que « le banc édite le marketing »
veut dire ça, y compris quand le banc se retourne contre vous.

[Le JOUR DE MERGE, Nous Research a fusionné ce plugin dans le catalogue
officiel Hermes — après la revue ci-dessus.] Vous pouvez vérifier le feed
du catalogue, le manifest, le registre, le diff de chaque correction. On
n'était pas parfaits dans le premier post. Le système qu'on vous pitchait
est celui qui nous a attrapés — deux fois sur un nombre, une fois sur un
nom, et une fois, surtout, sur un argument de sécurité dans notre propre
manuel d'instructions.

Même requête, mêmes octets. Même quand la requête est : vérifiez-nous.
