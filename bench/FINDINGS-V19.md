# FINDINGS-V19 — la facture du CSV (30 jours du même fichier sale)

Le banc que l'article promettait. Un job d'agent banal : nettoyer le
MÊME CSV chaque jour pendant 30 jours. Spéc fermée (6 règles, dans le
prompt), gold ÉCRIT À LA MAIN avant le harness (bench/fixtures_v19/),
gate machine==gold passée — et elle a d'abord pêché un
`Decimal.normalize()` qui écrivait 4.5E+2 : c'est le CODE qu'on a
corrigé, jamais le gold. Nu @0.7 (le régime réel des agents — publié),
retry-agent ≤3 avec validateur de FORME seulement (le modèle ne voit
jamais le gold : personne ne triche), machine = la spec gelée en code.

## Prédictions → mesures (P1-P5 gelées dans run19.py avant la cellule 1)

| bras | jours justes | sorties DISTINCTES /30 | tokens |
|---|---|---|---|
| M machine | **30/30** | **1** (même sha256 × 30) | 0 |
| N nu 1.5b | 0/30 | **21** | 21 044 |
| N nu 7b | 0/30 | 4 | 18 346 |
| R retry 1.5b | 0/30 | 21 | 65 498 (**×3,11**) |
| R retry 7b | 0/30 | 2 | 29 877 (×1,63) |

- **P1 ✓** (dérive ≥2) : 21 sorties en 30 jours au 1.5b. Le « dix
  sorties différentes » de l'article était une UNDER-claim : vingt-et-une.
- **P2 ✓** (≤27/30) : 0/30. Les deux modèles, les deux bras,
  soixante jours facturés, zéro jour juste.
- **P3 partiellement ✗ — publié** : ×3,11 au 1.5b (≥2 ✓) mais ×1,63
  au 7b (<2 ✗) : le retry du 7b se contente de rejouer la MÊME erreur
  (2 sorties sur 30 jours) — moins cher que prévu, et toujours 0/30.
  Le problème n'a jamais été le prix du retry : c'est qu'il ne
  converge pas.
- **P4 ✓** : machine 30/30, un sha, 0 tokens, pour toujours.
- **P5 ✓** : tokens par jour juste = ∞, ∞, ∞, ∞ et 0.

## Le diagnostic (une prise hors matrice, consignée comme telle)
Le 7b nu ne rate pas au hasard : sa sortie stable SUPPRIME 4 lignes
(01-07, 01-09, 01-13, 01-15) — il déduplique les lignes qui se
ressemblent alors qu'elles ne sont pas identiques. Il ne salit pas le
CSV : **il efface quatre transactions de ton historique, du même air
sûr, trente jours de suite.** C'est la définition de la dérive avec
confiance, et c'est exactement ce qu'aucun retry ne paie.

## En dollars (superposition arithmétique, tarifs publiés, datés)
Tokens mesés en local ; fourchette = tous tokens au tarif input (bas)
→ au tarif output (haut) du fournisseur, car l'harness a sommé les
deux (correction notée pour les prochains harnesss) :
DeepInfra Qwen2.5-7B $0,04/$0,10 ; Fireworks $0,20/$0,20 ; Novita
$0,07/$0,07 ; Together Qwen2.5-1.5B $0,10/$0,10 (sources LiteLLM /
pricepertoken / cloudprice, vérifiés les 20-21 nov. 2026).
- Le mois de ce banc : $0,0007-0,004 par bras modèle. Oui, des
  centièmes. La facture n'est PAS dans le taux API — elle est dans
  les 21 versions de ta comptabilité et dans les 4 lignes effacées.
- À l'échelle (arithmétique, pas mesurée : même comportement × export
  réel de 50 k tokens/jour) : nu ≈ $0,08-0,15/mois en open-weight,
  $0,9-2,3/mois à tarif frontière, ×1,6 à ×3,1 avec le retry — pour
  0 jour juste. La machine : $0,00, 🟢 par jour, même octet.

## Reproduction
    .venv/bin/python bench/run19.py     # repreneable par (arm,model,day)
Brut : bench/results_v19_csv_bill.jsonl (150 cellules). Spéc et golds
: bench/fixtures_v19/. Le prompt exact est dans run19.py ; température
0,7 semence aléatoire (régime réel), machine déterministe par
construction.
