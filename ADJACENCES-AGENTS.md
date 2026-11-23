# ADJACENCES-AGENTS — croquis de positionnement (23-11, matin)

Source des idées : deux captures d'un chat « expert mode » (13 et 16
citations, chiffres NON vérifiés par nous — un chiffre non rejoué ne va
PAS sur la landing, jamais). La valeur de la carte n'est pas ses
pourcentages, c'est la nomenclature : six adjacences revendiquées par
le marché, huit douleurs nommées. Ce doc répond pour chacune :
**couvert (avec notre preuve) / candidat (avec le contrat) / refus
nommé (avec la raison)**. Le refus est une livrable comme les autres.

## Les six adjacences

| suggestion du marché | notre position | preuve ou contrat |
|---|---|---|
| automatisation de navigateur (Playwright/MCP) | **REFUSÉ nommé** | mechacut ne touchera pas le web réel : pas de session, pas de clic, pas de tiers de confiance implicite. Contrat du produit : « no account, nothing stored ». Une route navigateur serait un autre produit. |
| orchestration durable (Temporal-like) | **REFUSÉ nommé** | le sans-état est un choix, pas une limite : la chaîne vit dans `/pipeline` et sa réponse, pas dans une file. La durée appartient aux clients de la suite, pas à la suite. |
| évaluation déterministe (DeepEval-like) | **CANDIDAT n°1** | nous avons déjà le juge : `bench/harness/judge.py` (verdicts OK/WRONG/PARSE/REFUSAL sur golds canoniques, auto-testé). En faire une route `eval/compare` (prévu vs attendu + score par classe + sha), c'est du dogfooding pur — le banc devient l'API. Douleur adressée : « M » arm à 15/50 = les gens paient pour deviner si c'est juste. |
| mémoire persistante | **REFUSÉ nommé (pour cette suite)** | une suite qui répond « le même octet demain » ne peut pas stocker l'état du client. C'est le métier d'un autre projet de la maison — hors périmètre de ce repo. |
| sandbox de code avec timeout | **REFUSÉ, borne existante** | nous exécutons déjà du code modèle, mais sous AST-gate fermée (bras C du banc, opérateurs ET contextes, refus nommés). L'arbitraire non typé ne rentre pas : un serveur déterministe ne court pas le code des autres, il rend le sien. |
| gates de politique strictes | **CANDIDAT n°2** | `check/allowlist` : règles fermées (sujets × verbes × montants bornés) en entrée, verdict + raison nommée en sortie, sha compris. C'est `logic/rules` appliqué à l'autorisation. Douleur adressée : « actions involontaires » — notre réponse est exactement la leur : la grammaire fermée, comme pour le routeur (`/router/apply` refuse hors grammaire, publié). |

## Les huit douleurs marché × nos chiffres mesurés

| douleur (leurs mots, chiffrage non vérifié) | notre mesure (rejouable, ledger csk + FINDINGS) |
|---|---|
| fiabilité 70-95 % d'échec sur tâches réelles | **nos 0/202 nu à temp 0** (byte-exact, 4 modèles, R=5) — même famille d'ampleur, la nôtre a un denominator |
| gap prod ~25 % / 40 % abandonnés | non mesurables ici — terrain d'étude marché, pas de banc. À ne JAMAIS citer comme nôtre. |
| coût : explosion de tokens, « taxe de défiance » | mesuré en TTR : nu qui brûle 8 192 tokens vs équipé qui clôt à ~100 ; V22 : ×4 la facture pour le retry unanime |
| actions involontaires ~80 % | → candidat n°2 (allowlist) + refus du sandbox |
| observabilité | déjà couvert en nature : sha par réponse, `misses.json` anonymisé 60 min, transcripts vault par cellule de banc ; un `trace/replay` n'est pas nécessaire — le sha EST la trace |
| usage d'outils (mauvais route/mauvais outil) | le MISROUTE est notre métrique de tête (15/50 M sur 1.5b → 40-45/50 I/P) ; le routeur-annuaire est la réponse expédiée |
| état / durée | → refus nommé (sans-état) |
| données / specs (42 % d'échecs multi-agent) | notre réponse spec : chaque 400 porte champ + expected + exemple (publié depuis bundle 4) ; le multi-agent n'est pas notre terrain |

## Décisions — tranchées par l'humain (23-11, 10h)
1. `eval/compare` : **OUI** — contrat + gold à la main, à écrire en premier.
2. `check/allowlist` : **OUI** — dans la foulée.
3. Refus publics : **NON**. Rien sur la landing, rien sous forme
   d'anti-vitrine. La clarté sur ce qu'on fait rend les refus
   implicites : une suite qui dit précisément ses 152 transforms
   n'a pas à énumérer ce qu'elle ne sera jamais. Le refus reste
   interne (ce doc) comme boussole de roadmap : « pas de navigateur,
   pas de sandbox, pas de mémoire, pas de durée » = ce qu'on ne
   viendra PAS vendre un jour, pas ce qu'on ira crier.

## Provenance
Cartes reçues de l'humain le 23-11 (captures d'un tiers, 13+16
citations). Leurs chiffres sont traités comme des hypothèses de
nomenclature, jamais comme des données : chaque case « notre mesure »
au-dessus pointe un artefact du repo (ledger, FINDINGS, golden pins).
