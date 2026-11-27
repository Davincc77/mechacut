# BUNDLE-REGISTER — la taxe d'enregistrement d'un outil neuf, jouée complète

Écrite le 26-11 après bundle 123 (`stats_rate_ci`), où chaque case a été
payée en rouges successifs (11 → 6 → 0). Un bundle suivant part de cette
liste et paie zéro rouge surprise. Révisée à CHAQUE bundle : si une case
change, ce fichier ment — le corriger fait partie de la taxe.

## Ordre exact (17 fichiers, du rouge au vert)

1. `tests/test_bundleNNN[_agent].py` — golds tracés À LA MAIN, écrit
   AVANT l'implémentation. Le docstring porte les traces de calcul.
   **Convention de nommage (décision Vince 27-11)** : le fichier porte le
   nom de l'agent qui le construit — `test_bundle123_hermes.py` pour
   l'agent campagnes (Hermès interactif) ; **sans suffixe = un autre
   agent** (cron sœur, externe). Le numéro de bundle reste global et
   unique ; le suffixe dit QUI a payé la taxe, pas ce que le test prouve.
2. L'implémentation dans le kit de sa famille (`checkers.py` pour
   checks/numbers-logique, kit dédié sinon).
3. `main.py` — Request(BaseModel) + `run_x` + endpoint + **entrée dans
   la table dispatcher** (`"x": run_x,` — sinon /api/v1/batch aveugle) +
   **entrée dans MCP_TOOLS** (sinon `/tools/x.json` 404 → bundle0) +
   version `x.y.0` bump.
4. `routing.py` — tuple TABLE (name, path, famille, purpose ≤ ~34 car.,
   tags). Les tags passent les 3 pages landing : budget FR/PT (case 9).
5. `corpus/x_pin.json` — une requête épinglée (harness golden).
6. `sayings.py` — SAY[path] × en/fr/pt (instructions, pas slogans ;
   l'argent de chaque langue dans sa devise).
6b. `make_landing` touche AUSSI `static/landing.html`
    (artifact SUIVI, pas seulement locales/*.json — pêché au bundle
    125 : commit oubliait le template, verts locaux cachaient un arbre
    sale). Après régénération : `git status`, ajouter le fichier.
7. `scripts/golden.py write` — régénère `golden.json` +
   `static/agent_examples.json`. Vérifier : diff **adds-only**,
   zéro suppression (compter les ^- hors en-tête de fichier).
8. `scripts/make_landing.py` — régénère locales/{en,fr,pt}.json.
9. BUDGETS (mesurer, ne jamais deviner) :
   - manifeste `< 9000` octets — si dépassement : élage claim-constant
     dans la tête de `routing.manifest_text` (précédents b111/b112/b114 ;
     chaque coupe cite son précédent en commentaire) ;
   - landing `< 181000` − 367 × 3 langues — si dépassement : dédoublonner
     (précédent b123 : attribut `title` des chips tier = légende visible
     mot à mot, coupé) et resserrer les tags du tuple ;
   - 218 lignes de manifeste max.
10. PINS à monter (chercher l'ancien nombre, tout est épinglé) :
    - `== 198`→+1 : `tests/test_bundle0.py` (TABLE) ;
    - `== 190`→+1 : `tests/test_bundle1.py` (liste MCP littérale —
      INSÉRER le nom dans la liste, pas que le compteur),
      `tests/test_bundle3.py`, `tests/test_bundle92.py`,
      `tests/test_bundle99.py` ;
    - golden `== 443`→+N : `tests/test_bundle108.py` ET
      `tests/test_bundle110.py` (deux épingles, formats de commentaire
      différents) ;
    - « NNN transforms + 9 recipes » : `tests/test_bundle110.py`.
11. Suite COMPLÈTE, exit code NU (jamais via pipe — `| tail` masque le
    rouge). Attendre : `2169+tests_neufs passed, 2 skipped, exit 0`.
12. `git add` avec les **chemins énumérés** (jamais `-A` : le working
    tree peut porter les files non commitées d'un autre agent — sœur/
    cron). `git status` AVANT : si un fichier partagé est `M` sans être
    à toi, ne pas y toucher.
13. Commit → push (garde pre-push ADN doit passer) → `railway up` (nu) →
    vérifier le manifeste live (version + compteur) → rejouer les golds
    EN PROD + le batch dispatcher.
14. Flip `VERDICTS.md` : IN-BUILD → SHIPPED, citation du commit de
    construction (hash réel, jamais prédit) + sha live. `pytest
    tests/test_verdict_ledger.py` nu, commit séparé, push.
15. Si l'outil vient d'un dossier de la porte : la rangee reste vraie —
    ne jamais réécrire l'historique de la ligne, seulement son statut.

## Non-négociables

- Les golds précèdent l'impl ; un gold que l'impl « corrige » était un
  gold faux — le tracer de nouveau, à la main.
- `check_failed` vs `invalid_input` : suivre le VOISINAGE de la table
  (les validateurs refusent en `check_failed`), pas une préférence.
- Les compteurs ne se pétrissent pas dans les artefacts : manifeste =
  compteur du bench ; plugin = autre horloge (registre MCP).
- Ce fichier est dans le dépôt pour les DEUX agents (main + sœur cron) :
  périmé ici = faux rouge ailleurs.

- **127_hermes v1.50.0** (build 2967c19) : text_claimsweep — table fermée importée du CI copy-audit, golds du blob 77dcc80b rejoués, citation exemptée, extra=forbid né avec l'outil ; élague manifeste claim constant ; suite 2217.

- **128_hermes v1.51.0** : vague de CORRECTIFS des fautes de grammaire rendues par la compilation Grok vague 2 (B1 queue sha256 = canon maison, plus le digest vole ; B3 champs nommes lat/lon + rate + generate-full-id ; B8 grammaire rules fermee nom-when-require-forbid-set + fait inconnu refuse par son nom, op exists garde l'absence legitime ; B11 seconde intercalaire DITE des deux cotes (format la valide, parse la refuse en nommant POSIX + la porte utc_tt_offset) ; B12 echelle declaree rendue (round et places), muet = historique intact ; B16 calendar julian refuse, dit proleptic-Gregorian, la vraie conversion est date_julian_gregorian au registre ; B17 modele+rayon echoes ; 7e trouvee en relisant : age sans on lisait l'horloge murale du serveur — desormais params.on exige, nomme. Deux blessures auto-infligees pechees par la suite et reparees dans le meme commit (set oublie dans la liste fermee ; regex souple des schemes generiques). Suite 2235 + 3 re-epingles (2 pins golden/integrity), exit 0 NU.

- **129_hermes v1.52.0** : B9 ferme la vague Grok 2 — pdf_provenance conforme ISO 32000-1 : la valeur vient du dictionnaire /Info QUE LE TRAILER NOMME (§14.3.3) au lieu du dernier octet gagne du scan global (les 5 retournements de Probe par les Info embarquees) ; chaines HEX et UTF-16BE a BOM decodees (§7.9.2.2 — les 14+13 fausses/vides) ; corps ObjStm scies par /N /First (§7.5.7) ; date sans offset rendue NAIVE dite (racine : bug python '' in '+-' — la porte mentait sur sa propre grammaire) ; offset OHH seul accepte ; created==modified rend equal+False, plus jamais True (Scout) ; mixed naive/zoned = unknown dit, jamais devine ; le ciphertext n'est plus jamais rendu comme producteur ; source_sha256 lie le recu aux octets (Probe #3). Le COMPTE global survit (rangee 16 MiCA — la preuve des generations coexistantes ne disparait pas). 11 tests dont 2 can-fail ; un gold trace main corrige par la TABLE (Apche->Apatche, la table a raison, mon oeil avait tort). Suite 2246 + 1 re-epingle golden (pdf_provenance), exit 0 NU.
