# FINDINGS-V24 — trente jours de LFM3 : le modèle qui sait lire ne sait pas se répéter

La réponse mesurée à l'objection qui tuait le produit après V23
(« garde ton serveur, mon modèle sait »). Mêmes fixtures que v19,
importées INTACTES : le même dirty.csv, la même SPEC six règles, le
même gold écrit à la main, le même validateur que le modèle ne voit
jamais. Seul changement : le modèle (liquid/lfm-3-1.7b via Nous) et
le régime temp 0,7 — le réel. 90 cellules, prédictions B1-B5 gelées
au commit `abfdd41`, joué depuis sans retouche.

| bras | jours justes | sorties distinctes | SILENCE | $ |
|---|---|---|---|---|
| N nu | **4/30** | 3 | **25/30** | 0,049 |
| R retry ≤3 | **14/30** | 4 | 14/30 | 0,115 |
| M machine | **30/30** | **1** (même sha `8f56011c…` que v19) | 0 | **0,00** |

Rappel des mêmes fixtures par les nains de v19 : qwen 1.5b nu 0/30,
21 sorties ; 7b nu 0/30, 4 sorties.

## La nouvelle classe : le SILENCE

LFM3 ne dérive pas comme Qwen — il ne dégage plus de mauvais octets,
il ne dégage RIEN : sur 25 jours sur 30, la réponse finale est VIDE
(finish_reason=length, 8192 tokens de completion bouclés en
reasoning, jamais de livraison). La machine, le même octet ; le
modèle, le silence — et le silence est FACTURÉ : ~$0,0016 par jour
muet, le champ `cost` du fournisseur le confirme, usage « never
sent » compris. Pour un agent qui écrit ce CSV dans un fichier : 25
jours sur 30, soit fichier vide, soit crash. v19 avait mesuré la
dérive avec confiance ; voici le silence avec facture.

## B1-B5, statues

- **B1 ✓ dérive** : 3 sorties distinctes en nu — mais le vrai
  résultat est pire que le seuil : la sortie MODE (25/30) est le
  vide. Le pitch « jamais deux fois pareil » survit ; la forme de sa
  mort (une sortie unique et juste ≥28/30) n'est pas arrivée.
- **B2 ✓** : 4/30 jours justes (seuil ≤27). Le champion du 7/7 en
  chaîne de V23 tombe à 13 % en job quotidien. L'examen d'un coup
  n'était pas le métier.
- **B3 ✓** : le retry monte à 14/30 (il répare le vide en
  ré-échantillonnant — 1 sur 3 jours muets se sauve au troisième
  tirage) mais rejoue le silence 14 fois, pour 2,3× la facture.
  Placebo, chiffré hors famille, troisième fois.
- **B4 ✓** : la machine 30/30 au même sha que v19 — l'instrument
  n'a pas bougé d'un octet, la gate l'a redit avant la course.
- **B5 ✓** : $0,1638 la course entière.

## Ce que les deux bancs disent ensemble (la ligne honnête)

V23 : un petit modèle bien entraîné LIT nos chaînes — 7/7, à nu,
pour moins de deux millièmes. C'est vrai, c'est publié, notre pitch
« ils ne savent pas » est mort ce jour-là.
V24 : le même modèle, sur le VRAI job — le même fichier, trente
jours de suite — ne produit un résultat exploitable que 4 jours sur
30. « Savoir lire une fois » et « répondre tous les jours » sont des
capacités différentes, et la seconde n'existe que du côté du serveur.
La valeur de mechacut n'a jamais été de prêter une compréhension ;
c'est de prêter une **continuité** : le sha, la cible, le refus
nommé, le $0, le même octet le trentième jour.

## Incidents consignés

1. Le harnais initial lisait `content` sans classe : 28 jours joués
   avant que le SILENCE soit NOMMÉ (finish_reason + longueur de
   reasoning + err="silence" ajoutés par l'amendement `405842b` du
   même soir — les 28 cellules déjà jouées reclassées par dérivation
   depuis leur sha de contenu vide, aucune re-pilotée).
2. M arm : 10 lignes écrites puis SIGPIPE (sortie tronquée par un
   `| head` — leçon : jamais tronquer une course, l'auto-troncature
   des outils suffit). Repreuve déterministe 10→29, même sha.
3. Le route LFM3 a flapé en vrais 404 par intermittence ; les
   retries du harnais les ont mangés (et un faux diagnostic « route
   instable » avait été publié à tort plus tôt — voir V23).
4. La carte landing de v24 comptait d'abord 26/30 silences : sa
   définition (« forme refusée ») mélangeait le vrai vide (25 jours,
   sha du newline) et l'UNIQUE jour de contenu non vide mais mal
   formé (d7f807). Le générateur ET son garde portaient la même
   erreur miroir — un test ne peut pas pêcher ce qu'il répète.
   Corrigé les deux à la définition stricte ; 25 vides + 4 justes
   + 1 malformé = 30, la phrase ne ment plus d'un jour.

## Ce que ça vend (ligne mesurée, mise à jour)

**« On vous a laissé le bénéfice du doute : votre 1,7B qui lit les
chaînes, mis trente jours à l'épreuve du job réel. Quatre jours
justes, vingt-cinq silences facturés, et le retry qui paie le
silence 2,3 fois. Le même code, chez nous : trente jours, un octet,
$0,00. Lire est une grâce ; répéter est une machine. »**

## Reproduction

    cd bench && ../.venv/bin/python run24.py M N R   # repreneable (arm,day)
    ../.venv/bin/python score24.py                   # B1-B5 statues
Brut : results_v24_lfm3_30days.jsonl (90 lignes : finish,
reasoning_chars, sha, $ par jour). Gate : l'import v19 vérifié
machine==gold avant la première cellule.
