# ROADMAP-FINANCE — sucer l'app Ponte dans Mechacut (22-11, directive humain)

Directive : « tous les processus financiers déterministes et
répétitifs de la compta, aspirés et mis dans mechacut ». Le pont est
clair : Ponte garde l'état (base, factures, auth, PDF) ; Mechacut
aspire les **maths et le droit** — fonctions pures, entrées closes,
oracles par outil. Chaque outil = un contrat, un gold écrit à la main
avant l'impl, une ligne de doc, un commit. Les outils marqués
[INVENTÉ] sont des rapports que l'humain invente : la structure est
déterministe, le contenu fiscal reste sourcé loi ou signalé comme
proposition.

Source : `~/ponte/app.py` (208 k, lu via le skill ponte-dev) et ses
docs. Ce fichier vit à la racine du repo ; la boucle de croissance
le lit et peut prendre des lots, un seul propriétaire par fichier.

## F1 — ledger-core (douleur : l'impayé) — ordre d'attaque

| # | outil | aspire de Ponte | contrat |
|---|---|---|---|
| 1.1 | `money/aging` | relances + seuils | factures + as_of → buckets (0-30/31-60/61-90/90+), outstanding, max_days_overdue |
| 1.2 | `ledger/apply-payments` | rapprochement manuel | paiements → factures, FIFO par due-date, sur/ sous-payé nommé |
| 1.3 | `ledger/summary` | bilan annuel | écritures → totaux mensuels + report + solde |
| 1.4 | `invoice/validate-totals` | "la somme ne ment jamais" | lignes + totals DÉCLARÉS → écarts exacts (validation, pas calcul : recipe/invoice calcule déjà) |
| 1.5 | `invoice/number-check` | séquence sans trou | numéros → trous, doublons, continu |

## F2 — tax-eu (table fermée, sourcée)

| # | outil | aspire de Ponte | contrat |
|---|---|---|---|
| 2.1 | `tax/vat-category` | R3 EN16931 | pays vendeur/acheteur + biens/services → AE/E/TX + mention obligatoire + raison |
| 2.2 | `tax/einvoicing-deadline` | radar obligations C2/C3 | as_of + profil → dû/échéance/décalage, table sourcée (2026-09-01 / 2027-09-01) |

## F3 — tax-br (personne d'autre ne l'a ; marché ciblé)

| # | outil | aspire de Ponte | contrat |
|---|---|---|---|
| 3.1 | `tax/br-export-services` | notes d'export | lignes → ISS non dû (LC116 art. 2 II), PIS/COFINS zero (Lei 10.865), IOF 0 % export, note sourcée par ligne |
| 3.2 | `tax/pgdas-segregation` | Simples annex III vs 5.01/5.03 | lignes → revenue segregé/non, pourcentages |
| 3.3 | `tax/mei-cbe-limits` | seuils | revenus + date → Mei 81 k (prorata entrée), CBE 1 M USD (taux via money/rates as_of — composé, pas re-codé) |
| 3.4 | `tax/nfse-sheet` | Feuille "Emissão Completa" | facture → champs de la feuille déterminés ; JAMAIS l'envoi |

## F4 — reports [INVENTÉ structurellement, loi sourcée]

| # | outil | aspiration | contrat |
|---|---|---|---|
| 4.1 | `report/accountant-csv` | CSV comptable 17 colonnes | factures → colonnes exactes, clés figées |
| 4.2 | `report/annual-summary` | bilan | écritures + taux figés → écarts change resolved/unresolved, top clients, délai moyen paiement |
| 4.3 | `report/tax-scaffold-2047` | [INVENTÉ] | revenus étrangers → échelon 18,3 % crédit d'impôt (CGI art. sourced), structure prête, jamais remplie à la place de l'humain |
| 4.4 | `report/carnet-leao` | [INVENTÉ] | 20482 mensuel : table des seuils loi + calcul du dû |

## F5 — rates-forex : DÉJÀ FAIT (money/rates as_of, recipe/fx-legacy,
num/fx). Fermé, rien à sucer.

## F6 — radar-rules

| # | outil | aspire de Ponte | contrat |
|---|---|---|---|
| 6.1 | (existe) `logic/rules` | logic/rules | moteur déjà là |
| 6.2 | `legal/deadline-status` | LEGAL_RULES | table versionnée sourcée + as_of → dû/late/n-a + digest ; les règles 10-11 (e-invoicing) vivent ici |

## Doctrine appliquée à la famille

- Un outil = un contrat + un gold à la main + un oracle + un commit.
- Décimaux strings uniquement, refusaient les groupés (aiguillage
  num/parse). `as_of` obligatoire partout : une date manque = refus
  nommé, jamais "today" (le contrefossé de minuit est consigné).
- Tout ce qui vient d'une loi porte sa source dans le refus ou la
  note ; [INVENTÉ] = structure seulement, le contenu fiscal reste au
  humain.
- Versionnage : chaque tool nouveau bump 0.x + pin replayable.
