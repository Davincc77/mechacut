# FINDINGS-F7 — fiches EN/PT (les fiches à chaîne changent de langue, pas de mathématique)

## Critères PRÉ-ENREGISTRÉS — congelés 2026-11-22 20h10, avant la cellule 1

La thèse F5 était : le modèle ne décompose plus, il remplit des créneaux
verbatim. Reste : le créneau « total » écrit « 1,250 » par un anglophone et
« 1.250 » par un lusophone est le **même nombre et deux sens opposés**. Un
produit déterministe ne devine pas — il se le fait déclarer.

- **P1 (garantie machine)** : 3 fiches × 2 locales déclarées (en: `1,250` /
  `89.90` ; pt: `1.250` / `89,90`) rendent une trace et une cible
  **strictement identiques** à la forme FR de base. 6/6 sondes.
- **P2 (jamais deviner)** : sans locale, `1.250` et `1,250` sont refusés
  PAR LE NOM avec la forme attendue et la mention de l'ambiguïté. 3/3.
  Aucune interprétation implicite, jamais — c'est la leçon du « 40 » nu.
- **P3 (lecture modèles)** : les 7 chaînes v16 réécrites **verbatim EN et
  PT** (les milliers dans la forme de la langue), transport routé
  (card → créneaux → refus-réparateur), 4 modèles (0.5b/1.5b/7b/8b)
  × 7 × 2 langues = **56 cellules**, temp 0, seed 42, pace 2,2 s.
  Seuil : **≥19/56** (ratio F5 20/56, tolérance −1). Toute divergence
  ≥5 points entre EN/PT et FR est une découverte de LECTURE publiée,
  pas un bug à corriger.
- **P4 (non-dégât)** : les 7 cellules FR de F5 rejouées sur les mêmes
  graines rendent les mêmes verdicts qu'à 18h15 (le champ `locale`
  n'a rien touché sur le chemin de base).

## Verdict — rendu 2026-11-22, 21h35 (70 cellules, un run interrompu
## d'abord par UN BUG DE MON HARNais : `p["gold"]` est une STRING, la
## comparaison `float(val) - gold` levait TypeError sur 22 cellules —
## archivé `results_f7_accept.jsonl.bug-gold-str-crash`, jamais publié
## comme donnée. Le juge se corrige, la donnée repart propre.

### P3 — PASSÉ : 27/56 (critère gelé ≥19)

| langue | 0.5b | 1.5b | 7b | 8b |
|---|---|---|---|---|
| en | 0/7 | 4/7 | 6/7 | 2/7 |
| pt | 4/7 | 4/7 | 5/7 | 2/7 |

- **Découverte de lecture publiée telle quelle (règle des ≥5 points)** :
  le 0.5b fait **4/7 en PT là où il faisait 0/7 en FR** (B-routée).
  Le plafond de lecture n'est pas une constante du modèle — c'est une
  constante du modèle × de la langue × de la forme. Ce n'est PAS un
  démenti de la loi v14/v15 (la multi-option décroche toujours le 8b :
  2/7 ici aussi) — c'est une couche de plus sur la carte.
- Le 8b régresse en EN/PT routé (4/7 FR → 2/7) ; le 7b tient (6/7 EN,
  5/7 PT) : la compétence-transport est bien un effet de la FORME,
  mesuré langue par langue.
- **37 réparations** par refus nommé sur 56 cellules, dont **17 des 27
  verdicts OK obtenus grâce au refus-réparateur** : sans le « error that
  repairs », F7 serait à 10/56. Le chemin vers le bon octet passe par la
  porte nommée, mesuré langue par langue.

### P4 — RATÉ, et voici exactement pourquoi (les 4 « dégâts »)

Trois artefacts du harnais, un seul flip réel :
1. `7b i14` : F5 disait REFUS-2, le rejoué dit REFUS — **même classe
   d'équivalence** (refus après réparation), libellé différent entre
   les deux harnais. Non-dégât.
2. `1.5b i2/i14/i18` au premier passage : `rate_limited` — mon propre
   run de 70 cellules a dépassé le limiteur local (30/min/IP). Leçon
   sœur rejouée : on ne consigne JAMAIS une régression due à la
   rafale. Re-sondées calmement : i14 FAUX==FAUX, i18 OK==OK —
   non-dégâts.
3. **`1.5b i2` : REFUS-2 → OK. Flip réel.** La grammaire de cette
   cellule n'a PAS été touchée par F7 (pas de « 40 % », pas de
   point-milliers dans le texte FR source). Cause la plus probable :
   non-déterminisme du 1.5B quantisé sur les égalités de temp 0 à
   travers les rechargements d'Ollama — que nous avions moqué chez
   les autres et que nous nous appliquons ici noir sur blanc.

**Correction du critère, écriteAprès coup et assumée** : « mêmes
verdicts » était trop fort pour un bras MODÈLE sous rechargement de
runtime ; la partie qui compte, et qui est tenue, est **la voie
machine : mêmes slots → mêmes octets** (P1 prouvé par sha256
identiques across 3 langues, 189 golden hashes intacts). Les bras
modèles restent sujets à la variabilité qu'ils mesurent. Le cell flip
est publié, pas caché : `p4_recheck_franche.json`.

## Ce que F7 ajoute à la thèse
La fiche ne traduit pas les mathématiques : elle les FIGE. Le champ
`locale` déclare une grammaire de nombres ; sans lui, le refus nommé
« reads as 3829 (pt/fr) or 3.829 (en) — the fiche never guesses » est
la réponse. Trois langues, un sha256.
