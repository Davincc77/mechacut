# FINDINGS-V23 — la loi tenait-elle hors de la famille ? Deux non, une réécriture.

Le banc d'un seul piège : douze bancs, tous nos plafonds mesurés sur
la famille Qwen (+ llama). LFM3-1.7B (Liquid AI, 6-nov-2026, tri-
hybride, vendu pour le tool calling et IFStruct 93,7, « not
recommended for complex reasoning » de l'aveu du fabricant) entre
dans le banc comme contre-exemple armé : un 1,7 B ENTRAÎNÉ POUR LA
FORME. 60 cellules = 20 gen16 intouchés × 3 bras (N nu, S relais
v14, L verrou importé de run20), temp 0, Nous, prix gelés.

| bras | total | chaîne (mix+partage) | tokens | $ |
|---|---|---|---|---|
| N nu | **20/20** | **7/7** | 9 848 | 0,0018 |
| S relais | 18/20 | 7/7 | 48 250 | 0,0089 |
| L verrou | 18/20 | 6/7 | 86 536 | 0,0157 |

## Verdicts gelés

- **P1 ✗ RÉÉCRITURE (la chute du banc)** : prédit ≤3/7 en chaîne,
  mesuré 7/7 NU, en un coup, à 261-595 tokens. Le pitch « tes modèles
  ne savent pas faire les chaînes » n'était pas une loi de la taille
  ni de la FORME : c'était une loi de l'**objectif d'entraînement**.
  Un petit modèle entraîné pour les traces agentiques lit nos
  énoncés à dépendances que les Qwen de taille comparable échouent
  0/28. Les golds (382,90 ; 1 469 ; 225…) sortent de la graine 2026
  jamais publiée : la mémorisation est impossible, c'est bien une
  lecture.
- **P2 ✗** : la délégation n'ajoute rien là où le nu sait — S = N en
  chaîne, pour 4,9× les tokens et DEUX ruptures de gabarit de plus
  que L. Le relais est un pont (loi v17) ; là où il n'y a pas de
  rivière, il ne paie que la traverse.
- **P3 ✓ mais VIDE** : la classe « à côté » de S est de 0 — rien à
  convertir. Et le verrou est nettement perdant ici : +77 % de
  tokens vs relais, −1 chaîne. Ses deux échecs sont instructifs
  (plus bas : le verrou rejette des réponses JUSTES faute d'être
  lettré).
- **P4 ✓ à demi** : en L, 0 rupture de protocole (leur IFStruct est
  réel : le gabarit n'est JAMAIS cassé). En S, 2 ruptures sur le
  PREMIER tour du relais multi-tours (#09, #15 : traces vides) — le
  décrochage multi-tours n'est PAS une loi llama seulement. Un
  modèle post-trained pour les harnesses décroche quand même en
  relais, 2/20 : la rivière, c'est le multi-tour, pas le modèle.
- **P5 ✓** : facture totale $0,0264. $ par juste : N 0,0001 — L
  0,0015. Quinze fois le prix pour le même nombre, quand le modèle
  sait déjà.

## Ce que le verrou a pêché SUR LUI-MÊME (le plus utile pour le produit)

L #09 : réponse **9,16 = l'oracle**, nommée « prix final », puis
« final_price » après réparation — refusée VOCAB, le dictionnaire
disait `final`. L #18 : **225, l'oracle**, nommé « RESTE » — le mot
DE L'ÉNONCÉ — refusé deux fois. Le garde mesuré est trop littéral :
il exige le nom du serveur alors qu'il vient de l'échoer dans
`names`. Le produit doit rendre la grammaire du nom aussi fermée que
celle des créneaux (noms proposés = seuls admis, ou table de
synonymes par fiche), sinon il facture 77 % de plus pour rejeter des
justes. C'est écrit AVANT de le corriger.

## Ce que le banc NE réfute pas

V19 est intact : LFM3 fait 7/7 en chaîne en un échantillon ; le banc
n'a pas testé trente jours du même CSV par ce modèle. Répondre juste
une fois n'est pas répondre le même octet tous les jours — et la
garantie (trace, refus nommé, sha, $0) ne meurt pas ici. Ce qui
meurt : l'idée que la FORME est le SEUL chemin vers les chaînes pour
les petits modèles.

## Incident de plomberie publié

Le harnais gelé épinglait « liquid/lfm3-1.7b » — un mirage 404 (la
sonde multi-ids l'avait pourtant montré). J'ai d'abord commité
« route instable, uptime ~50 % » : diagnostic FAUX, la route était
ouverte 6/6 sous le bon id. Zéro cellule souillée (0 ligne au
moment de la correction), id corrigé avec trace, retries conservés.
Le juge/porteur de carte a péché le banc, pas le modèle : c'est le
rôle des gates.

## Ce que ça vend maintenant (ligne réécrite, mesurée)

**« Certains petits modèles savent lire nos chaînes — un l'a fait
7/7 pour $0,0018. Aucun ne te garantit le même octet le mois
prochain : nous, si. Répéter n'est pas penser, et même savoir lire
une fois n'est pas répondre pour toujours. »**

## Reproduction

    .venv/bin/python bench/run23.py N S L    # repreneable par (arm,i)
    .venv/bin/python bench/score23.py        # P1-P5 statues
Brut : bench/results_v23_lfm3.jsonl (60 cellules, $ par ligne).
Modèle : liquid/lfm-3-1.7b, Nous, temp 0 respecté (0 retry
provider-default dans les traces). Verrou importé de run20 — le
garde mesuré est le garde vendu, littéralité comprise.
