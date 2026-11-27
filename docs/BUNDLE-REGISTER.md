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

- **130_hermes v1.53.0** : rails installment 2a — le MRN douanier (18 caracteres) entre en REVISION de id_checkdigit, 17e scheme. Loi lue AU VENTRE 27-11 : Reg 414/2009 Annex VII (n2+a2+an13+an1, Code 128 charset B) + 2015/2447 Annex B (an12 + caractere de PROCEDURE a1 — table fermee 15 codes A-W mot pour mot) + decision TCP « Berekening controlecijfer MRN-GRN » (ISO 6346 : valeurs lettres en sautant 11/22/33, poids 2^0..2^16 de la GAUCHE, mod 11, reste 10 -> caractere '0' — Table 2). L'exemple travaille PUBLIE rejoue au produit pres : 99IT9876AB8890120 -> somme 154031 -> reste 9 -> MRN 99IT9876AB88901209. FINDING consignee : les exemples de champs des annexes EUX-MEMES (06RO…123/5, 14DE…X1/1) ECHOUENT leur propre algorithme (traces main : '0' et '2') — refuses comme golds, rendus NOMMES dans le verdict (le gold can-test 24FR1234AB567890X9 prouve qu'une procedure hors table est dite NOT_IN_PUBLISHED_TABLE, jamais inventee). 17 tests a attendus traces main double-passe + oracle transcrit du document (produits publies), 6 pins adds-only (golden diff 0 suppression), TABLE hay sans vol de mot (« reference » rendu a money_rates), saying FR rendu douane, re-bake x3 langues dans le meme commit, 4 aiguilles radar locales vertes (13/7/7/16) + leurres silencieux. Suite 2263 passed 2 skipped exit 0 NU.

- **132_hermes v1.54.0** : AMAS DATES 1/2 (arbitrage Vince 27-11 « ouvres les amas un apres l'autre, tous »). Trois parseurs ADMIS des recus Grok : date_edtf_interval (Gate 848f1a94, RECOMMANDEE — 9 golds de Gate rejoues, borne ouverte = null+flag, la sentinelle 2100 des finding aids meurt), date_interval_within (Gate a8ce4696, ADMISE SEPAREREMENT malgre son flag « plus faible » : sa DISTINCTIN est vraie — date_window ne compare jamais deux intervalles DONNES ; l'ecart 2922 j reproduit au jour pres), marc008_date_range (Lineage 692467fa : la correspondance date_window 14 etait un score de MOTS pas de contrat — le 008 est un champ POSITIONNEL ; table fermee LOC bd008a edition 2026-05-27 hashee b2a162cc, roles reprint/original dits, fill mele refuse). Les formes catalogue 260$c : PAS date_parse — l'annee nue EST le gold EDTF n°1 (precision reduite), date_parse reste l'instant unique, tranche consigne. REVISION d'apercu maison : je devais fusionner within dans edtf — le draft Gate prouvait deux contrats, la table a raison devant mon plan. Taxes : pins 197/205/196, elagage MESURE du manifest (marge 6 octets -> gouttiere double->simple, precedent b107 lignes vides, claim constant), 3 corpus, saying via landing x3, edtfkit.py a l'image. 31 tests dont can-fail (1966 Jan. refuse par son nom). Suite verte hors morsures des soeurs (verifiee en worktree propre), flip registre au commit suivant.

- **134_hermes v1.55.0** : PAQUET CHI2 (amas P-C, arbitrage Vince 27-11 — « un outil, deux sorties nommees, credite aux deux »). stats_chi2 : mode ferme gof | critical sous UN SEUL contrat d'enregistrement — gof rend chi2 (6 dp), ddl et la p de queue SUPERIEURE en forme fermee declaree (df pairs ; df impair refuse PAR LE NOM, le voisin critical est designe ; attendu absent = uniforme n/k RENDU en applied_defaults, arithmetique Fraction exacte) ; critical lit la table FERMEE CHI2-CRIT-NISTEH-1.3.6.7.4-v1 (NIST e-Handbook 1.3.6.7.4, df 1..100 x 0.10/0.05/0.025/0.01/0.001, version+sha declares, hors table refuse par le nom, jamais extrapole). Golds de campagne REJOUES LITTERALEMENT : les 3 du contrat gof ([10,20,30] -> 10,000000 / 0,006738 ; [14,6,10,10,10] -> 3,2 / 0,524931 ; [0,10,20] -> 20 / 0,000045) et les 8 seuils traces main sur NIST (df 8/9/89/99 aux alpha 0,05 et 0,01), table recoupee au fetch contre le calcul serie. benford_digit_test : outil SEPARATE (reçu e40332bc, blob f68fc797, contenu via releveur interne) sur la table BENFORD-NIGRINI2012-v1 — comptes fermes 9/90/10/100 + min/max -> n, df (8/89/9/99), chi2 2 dp, chi2_crit_05 LU dans la table chi2 et NOMME, MAD 4 dp, bande Nigrini (borne superieure inclusive, convention v1 DITE), verdict ferme a six noms, precedence R-N1 > R-SPAN > statistite dite ; last_* sans bande publiee = info DITE. Les 5 golds du GOLDS.md du releveur sont ABSENTS de la compilation (stocke:false) — non rejoues, non inventes ; l'erratum 0.083804 est consigne comme attestation, la loi MAD est /K jamais /N (l'erreur meme du gold). Distinction dite : stats_rate_ci = une proportion (z=1,96), math_calc = arithmetique fermee sans log/exp/gamma — aucun ne fait ni forme fermee ni table. Routes vides de campagne (« chi square critical value », « benford first digit ») repondent desormais, testees. Taxes : pins TABLE 207 / mcp 199 / manifest 198 transforms ; manifest 222 lignes / 8 819 octets — budget octets TENU sans elagage (la gouttiere b132 n'a pas servi) ; 3 corpus pins adds-only (golden 456 -> 459, 0 suppression), agent_examples 179 chemins, landing re-bakee x3 langues dans le commit, Dockerfile COPY. 29 tests dont can-fail (df impair refuse nomme, ratio 855 SPAN_TOO_NARROW, cle inconnue par son nom). Flip registre (proposed->SHIPPED des recus 9ceddc83/265f6322/e40332bc) : HORS de ce lot — le registre est gele au tri 27-11, au proprietaire d'y toucher.

- **135_hermes v1.56.0** : LOT 135 (admissions 27-11, registre L24 reçu 56dc427d + L30 reçu 6aaf2824). Deux outils, deux grammaires publiées closes. date_julian_gregorian = le contrat que date_calc DESIGNAIT par son nom (B16) : calendar argument OBLIGATOIRE {gregorian, julian}, pont JDN, table centurielle des décalages 10/11/12/13/14 versionnée+hashée dans chaque réponse, style année-25-mars NOMMÉ (Washington 1731-02-11 OS = 1732-02-22 — gold publié), golds rejoués depuis les assertions consignées du rapport de campagne (JDN 0, 584283 pont maya, Pâque 2012 +13, frontière 1700 au jour près). Écart CONSIGNÉ : l'input exact du couple 28 452/28 442 (mesure Gate) n'est pas dans la matière — sa classe est rendue par le gold adjacent 1582-10-04 julien → 1582-10-15 grégorien = 1 jour (date_calc : 11 proleptiques). pep440_sort = grammaire PEP 440 recopiée (Appendix B, epochs, a/b/rc alias, .post/.rev/-N, .dev, labels locaux) ; la liste d'ordre PUBLIÉE du PEP est rejouée littéralement sous mélanges ; les 7/7 listes que semver_sort refuse (registre) sont triées ici, le contraste est rejoué en test, pas cité en prose ; normalisations RENDUES par chaîne, équivalences groupées jamais fondues, grammaire version+sha déclarée. Taxes : pins TABLE 209 / mcp 201 / manifest 200 transforms, manifest MESURÉ 224 lignes / 8 921 octets (marge 79 — la prochaine ligne se paie en élagage ou en dense-fold), 2 corpus golds adds-only (golden 459->461, integrity, agent_examples 181 chemins), landing re-bakée x3 langues dans le commit, Dockerfile COPY des deux kits. 38 tests du fichier lot dont can-fail et le seam date_calc rejoué. Blob synthèse 22:55 toujours absent du disque (cahier de triage interne, trou connu) — les golds viennent des assertions consignées et des spécifications publiées, rien d'inventé.

- **136_hermes v1.57.0** : LOT 136 (admissions 27-11, registre L27 reçu 8162da28 + L31 reçu c69633d5). Deux outils, deux grammaires publiques CLOSES, tables versionnees+hashees. spdx_expression = /api/v1/license/spdx-expression : SPDX spec v2.3.1 Annexe D lue mot a mot (AND OR WITH sensibles a la casse, precedence + > WITH > AND > OR, parenthesage, LicenseRef/DocumentRef, NONE/NOASSERTION refuses comme valeurs de tags nommees) ; ids juges contre la SPDX License List 3.29.0 (release 2026-09-16, 740 licenses + 86 exceptions, table regeneree PAR SCRIPT depuis licenses.json/exceptions.json du tag, jamais recopiee a la main ; version + sha declares dans CHAQUE reponse) ; id inconnu = VERDICT (UNKNOWN_ID + did-you-mean a distance <=2, precedent agent_modelid) ; grammaire cassee = 400 PAR LE NOM (operator_case, unbalanced_paren, missing_operator, colon_id_deprecated, empty_expression, list_version designant la seule vintage embarquee). cvss_base_score = /api/v1/security/cvss-base : v3.1 (equations 7.1 + Table 16 de la spec, ROUNDUP ecrite litteralement et jouee en Decimal EXACT — jamais binaire64) ; v4.0 (tables de l'implementation de reference FIRST : cvss_lookup.js 270 macrovecteurs, max_severity, max_composed, BSD-2-Clause ; interpolation portee a l'ordre d'operations pres ; arrondi final half-up) — les deux vintages arrondissent DIFFEMMENT et la reponse le dit ; metrics Threat/Environmental/Supplemental refuses PAR LE NOM du metric en designant l'autre contract ; vecteur v3.1 en ordre non-preferé ACCEPTE, normalise et rendu (exemple valide de la spec). Golds : 25 vecteurs DISTINCTS v3.1 (31 paires publiees, dedup dit) + 28 v4.0 publies par FIRST rejoues au bit pres, plus 30 paires du document d'exemples comme golds de test. AVEU DE SOURCE consigne au rapport de build : le brief promettait « les 30 vecteurs v4.0 du rapport de campagne » ; la compilation ne contient AUCUNE section cvss — les golds shippe sont TRACES depuis les sources publiques closees nommees, NON INVENTES, l'ecart 28/30 est declare, pas fabrique. Peche closee au build : cvsskit touchait getcontext().prec globalement — contamination silencieuse de math_calc, reparee par localcontext() par appel (la legon vit dans le kit). Taxes RE-ANCREES MESUREES sur le tip courant (le lot etait construit sur ed1dbf0 et repose ici apres que 135 a occupe 200/209/201/461) : TABLE 211 / mcp 203 / manifest 202 transforms + 9 recipes, manifest MESURE 226 lignes / 8 991 octets (marge 9 — trois coupes a claim constant dans la tete : label « proposals: », « <32KB; », « storyboards-> » ; la POINTEUSE soeur moovicut.studio RESTE, pin b0:154 ; le nombre se dit dans la reponse du gate, le trio dans le rail elsewhere de /route — precedents b111/b127, gouttiere b132 non utilisee), 4 corpus pins adds-only (golden 461->465, zero suppression, zero drift des 461 existants verifie diff-a-diff, integrity 465, agent_examples 181->183 chemins), landing re-bakee x3 langues avec fr+pt dans PURPOSES — le budget landing a FRANCHI 181 k comme l'annoncait b114 : PROSE SERRÉE, pas de re-resize (tierlegend rendu — ses trois regles vivent dans tiers.intro, doctrine b123 ; e26 FR/PT ratismee — les clauses duplicant les cartes soldes de la MEME page tombent, chaque fait survit), mesure finale en 180 022 / fr 180 525 / pt 180 583 APP, 180 389 / 180 892 / 180 950 SERVIS, Dockerfile COPY des deux kits. 21 tests du fichier lot dont can-fail. Artifact connu NOMME non possede : test_bundle114::test_radar_latest_json_contract (docs/RADAR vit hors git). Flip registre (recus 8162da28 + c69633d5, accepted->SHIPPED) : HORS de ce lot — prerogative du proprietaire.
