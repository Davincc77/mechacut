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
