# Bench v17 — l'économie de tokens : répéter n'est pas penser
# (2026-11-22. Mêmes 20 problèmes seedés que v16 (graine 2026, golds
# exacts pré-calculés), mêmes modèles locaux, temp 0 / 0.7. 80
# cellules. Prédictions P1-P4 gelées dans run17.py AVANT la première
# cellule ; ce document dit laquelle est tombée.)

| modèle | bras | succès | tokens | tokens/juste | médiane s |
|---|---|---|---|---|---|
| 7b | nu@0 (réf v16) | 10/20 | 2 540 | 254 | 0,5 |
| 7b | retry×5 (temp 0,7, majorité) | 9/20 | 10 000 | 1 111 | 2,1 |
| 7b | **relay (protocole steps v14)** | **19/20** | 21 325 | 1 122 | 2,8 |
| 8b | nu@0 (réf v16) | 3/20 | 2 135 | 712 | 0,5 |
| 8b | retry×5 | 4/20 | 8 180 | 2 045 | 2,3 |
| 8b | relay | 10/20 | 30 127 | 3 013 | 3,0 |
| 1.5b | nu@0 (réf v16) | 2/20 | 2 646 | 1 323 | 0,2 |

## P1 — VRAIE, et plus forte que prévu : l'erreur n'est pas du bruit
Familles à chaîne (mix + partage) : retry×5 = **0/14** (7b et 8b),
soit 70 appels et 6 875 tokens pour zéro convergence. Et le détail
qui tue l'argument « réessaie » : les 5 échantillons du 7b sur #00
étaient **unanimes sur la même erreur** (5× 266,0 pour gold 240).
L'erreur de lecture est SYSTÉMATIQUE — re-tirer, c'est re-échantillonner
le même malentendu. Le retry ne lutte pas contre le hasard ici, il le
déguise en consensus.

## P2 — VRAIE au 7b (7/7 en chaîne, 19/20 total : le meilleur score
jamais observé sur ces 20 problèmes), FAUSSE au 8b (0/7) — et la
autopsie des traces vaut de l'or :
- **le 8b n'a fait UNE SEULE ERREUR D'ARITHMÉTIQUE en 7 problèmes.**
  Chaque step évalué par le serveur était exact.
- Il a répondu **à côté de la question**, 7 fois : #00 → 160 (la
  quantité vendue l'après-midi) pour 240 (ce qui RESTE) ; #14 → 734,5
  pile la moitié du gold 1 469 (il s'est arrêté un facteur avant).
- C'est la classe d'échec que le miroir /intent/reflect a été conçu
  pour rendre lisible — et v17 en donne la preuve chiffrée : quand le
  calcul est délégué, l'échec restant est NOMMÉ dans la trace (la
  cible, pas le nombre). Prochaine itération du protocole (file v18) :
  la réponse exige `{"answer": v, "target": nom}` et le serveur refuse
  si le target ne correspond pas à la question déclarée. Le produit
  n'a pas encore ce garde : c'est écrit ici avant de le vendre.

## P3 — FAUSSE telle qu'écrite : le relais est plus CHER sur les
familles simples (rate : 1 557 t/juste en relay contre 464 en retry,
et 254 en nu@0). Le multi-tour repaie le contexte à chaque étape :
coût ≈ O(étapes²). Lecture honnête : **le relais n'est pas un
progrès, c'est un pont** — gratuit en efficacité là où le modèle
tombe (mur de la chaîne : ∞ → 1 285 t/juste ET 7/7), gaspilleur là
où il sait déjà faire. La règle de routage par FORME (SKILL-MINI :
un pas → tête ou /math/calc en un appel ; chaîne → steps relayés)
est désormais justifiée par la facture, pas par l'idéologie.

## P4 — VRAIE, troisième mesure indépendante : le 8B reste le pire
agent (10/20 vs 19/20 au 7B sur le même protocole ; ruptures de
protocole relay : 7b 1, 8b 2 dont un abandon pur). La taille du
modèle n'achète pas la discipline — v12, v14, v17 : trois bancs,
même verdict.

## Ce que ça vend (ligne mesurée)
**« 5 retries sur les 14 problèmes à chaîne : 70 appels, 6 875
tokens, ZÉRO — et unanimes dans l'erreur. Un relais : 1 285 tokens
par réponse juste, 7/7 là où la répétition ne converge jamais. Et
sur les 7 que le gros modèle rate même en relais, à zéro erreur de
calcul : il répond juste… à la mauvaise question. Répéter n'est pas
penser — on a facturé la différence. »**

## Reproduction
    .venv/bin/python bench/run17.py 7b 8b     # repreneable (saut par cellule)
    .venv/bin/python bench/score17.py         # verdicts gelés
Brut : results_v17_tokens.jsonl (80 lignes). Intégrité : les 57
premières lignes proviennent d'un snapshot git récupéré après
l'incident du branch de test (mêmes graines, même protocole, même
build — aucune cellule re-pilotée ; les 23 restantes rejouées par la
reprise).
