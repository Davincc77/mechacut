"""Bundle 0 — agent navigation substrate (TOOLS-50 B0.7 + B0.9).

When the suite grows, routing is the real token cost for a weak agent, so
the entry point is one fetch: GET /agent/manifest, one line per tool
(~500 tokens for all 53 — portable even on a 0.5B model). Detail is
pulled on demand: GET /tools/<name>.json returns one schema, not 53.
Skill packs (/SKILL-<pack>.md) let an agent install only its bundle:
Mechacut's growth costs nothing in prompt to those who skip the rest.

Closed tables, stdlib only, no LLM: same words, same bytes, sha256 on it.
"""

import hashlib
import json
import re
import unicodedata

import payments

PACKS = ("core", "repair", "code", "dates", "numbers", "identity",
         "checks", "text", "design", "extract", "logic", "time", "web")

# name, path, pack, purpose (agent-facing, closed), tags (for /route)
TABLE = (
    ("chart_from_data", "/api/v1/chart", "core",
     "records/CSV -> Vega-Lite spec + PNG",
     "chart graph plot visualize data spec png graphic histogram bars line "
     "pie viz graphique visualiser svg"),
    ("reshape_json", "/api/v1/reshape", "core",
     "schema-gated JSON reshaping",
     "reshape restructure transform json fields schema flatten rename "
     "contract api response mappage aplatir"),
    ("validate_json", "/api/v1/validate", "core",
     "JSON against schema, error pointers",
     "validate schema json check conform where does fail invalid against "
     "contract pointer field conformite"),
    ("json_repair", "/api/v1/json/repair", "repair",
     "broken JSON -> valid",
     "repair fix broken json malformed truncate quotes truncated extra "
     "data invalid unterminated fence markdown llm output unexpected end "
     "cassee corrompu quebrado"),
    ("json_diff", "/api/v1/json/diff", "repair",
     "structural diff, JSON pointers",
     "diff compare json versions changes pointer what changed drift moved "
     "added removed key entre"),
    ("json_patch", "/api/v1/json/patch", "repair",
     "apply JSON Patch operations",
     "patch json modify edit operations rfc6902 update one field without "
     "resending partial op rfc add remove replace"),
    ("json_canonical", "/api/v1/json/canonical", "repair",
     "canonical form + stable key",
     "canonical normalize json sort keys compare cache stable hash key "
     "identical unequal sorted two"),
    ("csv_fix", "/api/v1/csv/fix", "repair",
     "dirty CSV -> clean, refusals named",
     "csv clean fix dirty delimiter quote ragged semicolon stray excel "
     "export rows mixed encoding sep sujo"),
    ("csv_types", "/api/v1/csv/types", "repair",
     "infer column types, closed rules",
     "csv types infer column date number boolean cast typed dtype guess"),
    ("csv_join", "/api/v1/csv/join", "repair",
     "two tables joined, keys checked",
     "csv join merge tables keys sql lookup vlookup unmatched misses "
     "combine two files fusionner"),
    ("table_pivot", "/api/v1/table/pivot", "repair",
     "pivot and aggregate tables",
     "pivot table aggregate sum group analyze report groupby rollup "
     "crosstab region month croise"),
    ("list_dedupe", "/api/v1/list/dedupe", "repair",
     "order-preserving exact dedupe",
     "dedupe duplicate unique list urls entries repeats dupes already seen "
     "uniques liens"),
    ("format_convert", "/api/v1/format/convert", "repair",
     "json/csv/yaml round-trips",
     "convert format json csv yaml xml toml ini dump roundtrip config "
     "excel"),
    ("text_patch", "/api/v1/text/patch", "code",
     "search/replace edits on text",
     "patch edit text replace find string code paragraph change file "
     "without line numbers"),
    ("text_diff", "/api/v1/text/diff", "code",
     "unified diff between texts",
     "diff compare text changes unified patch side by what did i change "
     "edits tracking"),
    ("text_apply_diff", "/api/v1/text/apply-diff", "code",
     "apply unified diff exactly",
     "diff apply patch text update hunk cleanly git style file exact"),
    ("path_normalize", "/api/v1/path/normalize", "code",
     "file paths canonical, any OS",
     "path normalize file windows posix windows slash backslash separators "
     "absolute traversal dotdot emplacement"),
    ("glob_match", "/api/v1/glob/match", "code",
     "does this path match this glob",
     "glob match pattern path file test wildcard ignore star question "
     "bracket fnmatch"),
    ("env_interpolate", "/api/v1/env/interpolate", "code",
     "${VAR} expansion, defaults, refusals",
     "env variable interpolate template config expand dot dollar braces "
     "undefined defaults missing secrets"),
    ("date_parse", "/api/v1/date/parse", "dates",
     "any sane date string -> ISO",
     "date parse calendar iso format string rfc epoch unix timestamp "
     "friday ambiguity month name"),
    ("date_tz", "/api/v1/date/tz", "dates",
     "timezone conversion, DST-exact",
     "date timezone tz utc dst convert zone city conversion offset "
     "daylight saving beijing sao paulo fuso horario"),
    ("date_calc", "/api/v1/date/calc", "dates",
     "business days, add/sub, deltas",
     "date calculate business days add subtract duration delta weeks "
     "holidays deadline months clamp age later echeance "
     "jours ouvrables ouvrable interval range between counting"),
    ("cron_next", "/api/v1/cron/next", "dates",
     "next N cron runs, tz pinned",
     "cron schedule next run time job fires expression five field star"),
    ("cron_humanize", "/api/v1/cron/humanize", "dates",
     "cron expression -> plain words",
     "cron humanize explain words schedule expression meaning plain read "
     "crontab expliquer"),
    ("ics_generate", "/api/v1/ics/generate", "dates",
     "events -> valid ICS calendar",
     "ics calendar events generate export agenda all day recurring invite"),
    ("ics_parse", "/api/v1/ics/parse", "dates",
     "ICS -> structured events",
     "ics calendar parse import events vevent lines folded dtstart dtend "
     "read"),
    ("num_format", "/api/v1/num/format", "numbers",
     "locale-exact number formatting",
     "number format locale currency display decimal digits grouping en_us "
     "pt_br formato"),
    ("num_parse", "/api/v1/num/parse", "numbers",
     "ambiguous strings -> exact decimal",
     "number parse decimal amount extract string symbol thousand separator "
     "comma dot nombre"),
    ("num_round", "/api/v1/num/round", "numbers",
     "banker's or explicit, beyond float",
     "round rounding bankers decimal number half precision places down "
     "even float 0.1 0.2 arrondi"),
    ("units_convert", "/api/v1/units/convert", "numbers",
     "closed families, exact factors",
     "units convert measure length weight temperature volume area speed "
     "fahrenheit celsius miles km ounces grams acres nautical unidades"),
    ("money_prorate", "/api/v1/money/prorate", "numbers",
     "exact proration before last rounding",
     "money prorate split invoice tax period days fraction refund "
     "subscription cancel unused prorata"),
    ("money_aging", "/api/v1/money/aging", "numbers",
     "due-date aging of receivables into buckets",
     "aging overdue unpaid receivable invoice due dunning relance "
     "impayé retard facture echeance echéance balance aged ar "
     "comptable recouvrement"),
    ("money_unitprice", "/api/v1/money/unitprice", "numbers",
     "price per unit + shrinkflation, denominator NAMED (−12.5 % of "
     "pack ≠ +12.5 % per unit)",
     "unit price price per ounce per pound cheaper bulk shrinkflation "
     "smaller package same price cost per kilo compare grocery two for "
     "seven tag math wrong lb oz quart "
     "prix au kilo prix a l'once moins cher comparaison course "
     "paquet paquet grammage arnaque vrai vraiment etiquette "
     "erreur calcul meme prix moins cher au kilo denominateur "
     "deux pour sept "
     "preco por quilo preco por litro mais barato comparacao mercado "
     "reducao embalagem etiqueta conta errada mesmo preco dois por"),
    ("eval_compare", "/api/v1/eval/compare", "checks",
     "judge two JSON artifacts: OK/WRONG, divergences named",
     "eval evaluate compare judge diff expected got verdict wrong "
     "divergence pointer artifact score evaluer comparer juger "
     "verification ecart"),
    ("check_allowlist", "/api/v1/check/allowlist", "checks",
     "policy verdicts by closed grammar, most specific wins",
     "allowlist policy allow deny gate approve refuse subject action "
     "permission rule specific ambiguous autorisation politique "
     "permisso recusa regra deixar fazer"),
    ("loop_doom_check", "/api/v1/loop/doom-check", "checks",
     "doom/cyclic/storm verdicts over a tool-call trace",
     "loop doom cyclic storm repeat repetition trace agent calls "
     "retry stuck boucle repetition relance agentique trace "
     "repetitif boucler"),
    ("net_ratelimit", "/api/v1/net/ratelimit", "web",
     "Retry-After / X-RateLimit-* headers -> OPEN | THROTTLED | BLOCKED | "
     "UNKNOWN | CONTRADICTION, both waits named",
     "rate limit retry-after ratelimit throttle headers quota reset "
     "remaining backoff debit en-tete limite temporisation "
     "limitacao cabecalho tetos espera"),
    ("number_words_pair", "/api/v1/number/words-pair", "numbers",
     "spelled and digit amounts checked against each other — thirty (40) "
     "refuses, both values kept, no side chosen",
     "words pair amount cheque montant lettre chiffres contrat trinta "
     "trente thirty mismatch spelled numeral extenso por letras cifra "
     "contrato valor duplicado"),
    ("date_window", "/api/v1/date/window", "dates",
     "clause bounds (min..max days before/after an event) -> the full "
     "inclusive window, span, meaning; inverted bounds refused named",
     "window interval bounds clause deadline not less nor more "
     "range days before after event fenetre intervalle clause "
     "prazo janela limite intervalo clausula"),
    ("date_deemed", "/api/v1/date/deemed", "dates",
     "dispatch date + method -> deemed receipt date; no method, no "
     "date (closed table named, argument overrides are said)",
     "deemed receipt dispatch sending method registered courier "
     "standard mail email delivery date reception reputee envoi "
     "recomendado correio Entrega empfang"),
    ("agent_propose", "/api/v1/agent/propose", "checks",
     "network door: contract proposal judged against the live catalogue — "
     "DUPLICATE-OF, SUSPECT with evidence, ELIGIBLE with commit-ready blob",
     "propose proposal contract network submit tool new duplicate "
     "eligible suspect blob inbox proposition contrat soumettre "
     "propuesta contrato submissão"),
    ("text_fold_report", "/api/v1/text/fold-report", "text",
     "which case or accent foldings erase a distinct entity — reported, "
     "the fold itself left to the caller",
     "fold accents casefolding entity hermes identity collision "
     "nfd normalisation accents entite collision repli"),
    ("text_novel_words", "/api/v1/text/novel-words", "text",
     "description vs title: new words counted per item, echo feeds "
     "named, bound stated",
     "rss novelty echo description title words filler contenu titre "
     "novedad recheio"),
    ("address_parse", "/api/v1/address/parse", "extract",
     "postal address -> country, postal code validated against 50 "
     "grammars, remaining lines; ambiguity named, never resolved by luck",
     "address postal parse components country city street adresse "
     "cep endereço código postal componentes"),
    ("date_civil", "/api/v1/date/civil", "dates",
     "instant + named IANA zone -> the civil date that zone lives in; "
     "fiscal year shift flagged; server zone never consulted",
     "civil date invoice date timezone fuso fiscal year exercice "
     "date civile zona orologio locale date civile"),
    ("agent_retrybudget", "/api/v1/agent/retry-budget", "checks",
     "is re-attempting this failure rational? closed taxonomy, "
     "hash ceiling, session budget, deterministic backoff",
     "retry budget verdict transient fixable terminal repeat "
     "mutate abort identical hash backoff ceiling quota throttled "
     "limiter stuck exhausted attempt rational relance decision "
     "re tenter hachage identique plafonne budget tokens "
     "rationnel re-tentative reexperimentar veredito transcidente "
     "identico orcamento"),
    ("agent_mcpaudit", "/api/v1/agent/mcp-audit", "checks",
     "pasted MCP tools/list judged against named wire-shape "
     "rejection rules, before any client can silently drop it",
     "mcp listing tools descriptor handshake initialize "
     "serverinfo protocolversion inputschema empty silent "
     "invisible wire paste claude mcpaudit outils absents "
     "chargement vide protocole auditoria ferramentas "
     "silenciosa descricao ausente vazia"),
    ("agent_mcpsurface", "/api/v1/agent/mcp-surface", "checks",
     "pasted MCP tools/list fingerprinted per tool and as an ordered "
     "surface; baseline diff names ADDED/REMOVED/CHANGED plus "
     "REORDERED, annotation flips visible without any text change",
     "mcp tools list listing surface fingerprint fingerprints digest "
     "sha drift changed change pin pinned rug pull annotations "
     "readonly hint flipped order toolslist "
     "empreinte surface liste listing outils mcp change modifie "
     "derive releve epingle silencieuse annotations defauts "
     "destructive changed "
     "impressao digital superficie ferramentas mudou mcp "
     "deriva anotacoes padroes leitura anterior"),
    ("agent_contexttax", "/api/v1/agent/context-tax", "checks",
     "what the pasted MCP tools/list COSTS the window: chars/4 floor "
     "estimate per tool, name/description/schema split, names-only "
     "counterfactual, per-turn bill, $ at YOUR price argument",
     "context tax token cost charge bill burn waste window overflow "
     "fits turn definition description instruction "
     "coute couter taxe fenetre tour quanto custa taxa janela turno"),
    ("agent_costdiff", "/api/v1/agent/cost-diff", "checks",
     "the PRICE OF THE UPDATE: two pasted tools/list readings, token "
     "delta per tool, % of the before side, signed moved fields, "
     "FITS->OVERFLOWS transition named, delta per turn, $ at YOUR price",
     "cost diff delta grew increase update version upgrade price of "
     "the update more expensive extra since between two listings "
     "surcout plus addition added ajout nouvelle version mis a jour "
     "quanto a mais custo nova versao cobrou acrrescimo"),
    ("agent_tooltrim", "/api/v1/agent/tool-trim", "checks",
     "WHICH tools to cut for a budget: idle-first ranking in exact "
     "fractions, re-count at the sister's canon, FITS/STILL_OVER",
     "trim cut remove disable disconnect idle unused tools fit "
     "budget which to drop plan "
     "debrancher retirer couper desactiver outils tenir "
     "remover desligar ferramentas ociosas caber orcamento"),
    ("agent_tooloverlap", "/api/v1/agent/tool-overlap", "checks",
     "which two tools become ONE id in which client: 64-char cut, "
     "tail abort, middle fold, bare shadows, min key rename",
     "overlap collision collide collisions same name names tools "
     "disappear vanish truncated truncation silently dropped wrong "
     "tool routed prefix 64-char characters overlong shadow "
     "collision noms outils disparaissent tronque silencieusement "
     "mauvais outil nomme "
     "colisao nomes ferramentas somem truncadas silencioso "
     "ferramenta errada atalho"),
    ("agent_mcplist", "/api/v1/agent/mcp-list-completeness",
     "checks",
     "did your MCP client see every page: cursor rules replayed, the "
     "tail counted vs your declared number",
     "pagination paginate pages page cursor nextcursor truncated "
     "incomplete uncallable undiscoverable missing saw every loop "
     "repeated toolslist "
     "pagination pages curseur liste outils tronquee incomplete "
     "manquantes boucle "
     "paginacao paginas cursor ferramentas ausentes truncada "
     "incompleta laco"),
    ("invoice_payment_due", "/api/v1/invoice/payment-due", "dates",
     "the real invoice due date: four readings, roll rule named per "
     "law, TARGET2 settle layer",
     "payment due deadline invoice terms net net30 eom "
     "businessday workdays worked roll target2 settlement interest "
     "late penalty fin de mois quote letter change "
     "echeance facture paiement report "
     "retard frais penite prazo vencimento fatura "
     "uteis feriado zahlungsziel rechnung faelligkeit werktag "
     "verzug"),
    ("shop_discount_audit", "/api/v1/shop/discount-audit", "checks",
     "Omnibus thirty-day rule: is the crossed-out price legal? "
     "reference, true percent, verdict named",
     "discount audit strikethrough crossed price legal omnibus "
     "thirty lowest reference reduction misleading compliant fake "
     "sale advertised CJEU article fake-bargain solde prix barre "
     "legal licite trompeuse annonce annoncee regle des trente "
     "jours remise exageree desconto preco riscado ilegal "
     "promocao verdadeira falsa trinta dias menor regra enganosa "
     "vrai promotion"),
    ("ledger_apply_payments", "/api/v1/ledger/apply-payments",
     "numbers",
     "FIFO reconciliation of payments onto invoices",
     "reconcile reconciliation payment apply fifo invoice outstanding "
     "rapprochement paiement facture lettrage relance impayé "
     "comptable ledger cash clearing unapplied leftover"),
    ("ledger_summary", "/api/v1/ledger/summary", "numbers",
     "monthly ledger summary with running balance chain",
     "summary monthly running closing carryforward totals journal "
     "grand livre report "
     "resume mensuel solde cloture clôture "
     "balancete mensal razao livro encerramento resumo conta razão"),
    ("shop_shipping_deadline", "/api/v1/shop/shipping-deadline",
     "dates",
     "last ship-by day for Christmas by carrier and service",
     "shipping ship-by christmas day arrives ground saver air "
     "noel fetes dernier jour envoi avant usps ups fedex "
     "natal ultima data envie chegan ata fedex ups"),
     ("shop_return_deadline", "/api/v1/shop/return-deadline",
     "dates",
     "published holiday return deadline for a purchase date, "
     "provenance and conflicts named",
     "return deadline returns exchange last day gift christmas "
     "holiday purchase window seller retailer walmart target "
     "bestbuy amazon costco apple "
     "retour delai date limite retourner echange cadeau apres "
     "noel achat magasin delai de retour "
     "troca devolucao prazo ultimo dia devolver presente depois "
     "do natal comprar "
     "fnac darty boulanger dell cdiscount renvoyer renvoi livraison reception"),
    ("shop_pricedrop_refund", "/api/v1/shop/pricedrop-refund",
     "dates",
     "price drop after purchase: who owes you the difference, by "
     "when, in which money — closed 2026 BF table",
     "price drop dropped lowered after purchase difference refund "
     "adjustment guarantee owed lower price claim window bestbuy "
     "target costco fnac darty apple "
     "prix baisse baisse apres achat remboursement difference "
     "garantie meilleur prix qui me doit ecart carte cadeau "
     "queda de preco depois comprar diferenca reembolso garantia "
     "melhor preco"),
    ("shop_legal_guarantee", "/api/v1/shop/legal-guarantee",
     "dates",
     "statutory warranty clocks FR/UK from one delivery day: "
     "24m/12m, vices 2y+20y, UK 30-day/6m/6y-5y, conflicts named",
     "statutory warranty legal guarantee clocks conformity "
     "defect faulty broken gift burden limitation reject "
     "consumer rights act scotland six years "
     "garantie legale vice cache vices caches caché défectueux "
     "defenseux conforme delai panne cadeau presomption forclusion "
     "deux ans reparation remboursement garantie l\u00e9gale loi "
     "constructeur fabricant "
     "garantia legal defeito prazo fran\u00e7a reino unido "
     "conformidade vicio"),
    ("money_keep_records_uk", "/api/v1/money/keep-records-uk",
     "numbers",
     "UK retention clocks from official anchors -> earliest lawful "
     "destroy date, VAT three anchors, s388 by form, extensions "
     "BLOCKED not guessed",
     "keep records retention destroy shred dispose paperwork how long "
     "vat invoice paye cis self assessment companies act six years "
     "hmrc oss moss bad debt deadline filed throw away shoebox archive "
     "conservation jeter garder archives facture paperasse delai "
     "destruction combien de temps classeur royaume uni "
     "guardar documentos descartar tempo de guarda reino unido "
     "destruicao"),
    ("invoice_validate_totals", "/api/v1/invoice/validate-totals",
     "checks",
     "declared invoice totals vs exact arithmetic, signed deltas",
     "validate totals declared sum arithmetic contradiction audit "
     "receipt ocr claim "
     "verifier totaux declare somme calcul ecart facture recu "
     "validar totais declarados soma conferenca nota divergencia"),
    ("money_split", "/api/v1/money/split", "numbers",
     "cent-exact split, closed remainder rule",
     "money split bill participants cents remainder share friends evenly "
     "tip partage centavos"),
    ("number_spell", "/api/v1/number/spell", "numbers",
     "amount -> words FR/EN/PT",
     "spell words amount currency invoice mention french english "
     "portuguese euros dollars cents todas letras"),
    ("net_ip", "/api/v1/net/ip", "code",
     "is this IP private loopback link-local multicast reserved: anatomy",
     "ip address private public localhost link local multicast reserved "
     "ipv4 ipv6 adresse ip privee reservee address ip reservado"),
    ("net_cidr", "/api/v1/net/cidr", "code",
     "cidr range: network broadcast hosts contains subnet split",
     "cidr subnet ip range mask hosts network broadcast split "
     "sous reseau plage adresses diviser subrede cidr maquina"),
    ("file_encoding", "/api/v1/file/encoding", "extract",
     "charset forensics: bom table utf-8 strict or undetermined with proof",
     "encoding charset bom utf-8 latin-1 detect file encoding "
     "encodage caractere detecter codificacao caracteres"),
    ("integrity_verify", "/api/v1/integrity/verify", "checks",
     "auditor: replay ANY api's published pins N times, determinism "
     "verdict per pin, guarded egress",
     "audit determinism verify integrity third-party replay pin "
     "certificate auditer certitude"),
    ("math_calc", "/api/v1/math/calc", "numbers",
     "closed exact-Decimal calculator — the model writes the expression, "
     "the machine computes it; 0.1+0.2 is 0.3",
     "calc calcul math arithmetic multiply divide percentage fraction "
     "exact decimal virgule calculer multiplier calculadora conta "
     "regra de trois pourcentage"),
    ("money_discount", "/api/v1/money/discount", "numbers",
     "chained discounts as exact factors — 30%+20% is 44% not 50%, order "
     "of steps compared, formula returned",
     "discount solde promo pourcentage remise chained black friday "
     "same another versus combined equal stacked trick "
     "desconto promoção desconto em cascata equivalencia "
     "somado enganoso"),
    ("table_sql_dump", "/api/v1/table/sql_dump", "repair",
     "csv to sql: CREATE TABLE + INSERT from rows, types DEDUCED but "
     "SAID, quoting exact per dialect",
     "sql dump insert create table rows to sql export db loader "
     "generer sql inserer creer table requete banco inserir sql "
     "criar tabela postgres mysql sqlite column types statement "
     "schema ddl csv vers"),
    ("table_scale", "/api/v1/table/scale", "numbers",
     "recipe scaling with the rounding STATED: exact fraction + "
     "measurable step per ingredient class + delta, multiplier said once",
     "recipe scale cooking halve double third fraction grams eggs "
     "cups spoons portions servings kitchen baking ingredient convert "
     "recette cuisiner diviser doubler tiers oeufs cuilleres portions "
     "receita cozinhar dobrar reduzir terco colheres gramas ovos"),
    ("check_format", "/api/v1/check/format", "checks",
     "closed-set format validation for the rules JSON Schema cannot "
     "express (dates, semver, uuid, decimal-string…) — violations come "
     "with why + expected",
     "format validate date iso semver uuid decimal string hidden schema "
     "leap second pointer format vérification date calendrier"),
    ("csv_money_columns", "/api/v1/csv/money_columns", "repair",
     "financial CSV columns read by PROVEN convention — the column's own "
     "unambiguous values decide, contradictions are refused not guessed",
     "csv money decimal comma locale thousand separator montant "
     "devise virgule decimal milhar separador"),
    ("date_relative", "/api/v1/date/relative", "dates",
     "relative-date phrases (EN/FR/PT) to exact ISO — closed grammar, "
     "now as argument, ambiguities reported never decided",
     "relative date tomorrow next monday end of week demain lundi "
     "prochain fim de semana date relative amanha"),
    ("date_recurrence", "/api/v1/date/recurrence", "dates",
     "RRULE déroulé en dates — sous-ensemble RFC 5545 fermé, mois "
     "invalides sautés LISTÉS, ancrage du DTSTART déclaré, COUNT ou "
     "UNTIL jamais les deux, refus nommés, cap 500",
     "rrule recurrence recurring biweekly every other week monthly "
     "occupancy occurrences calendar series expand rfc rfc5545 dtstart "
     "until count byday wkst recurrente qui se repete un mardi sur "
     "deux tous les quinze jours derouler recurrence dates de serie "
     "recorrencia se repete a cada duas semanas quinzenal expandir "
     "rappel lembrete"),
    ("date_tz_ambiguity", "/api/v1/date/tz_ambiguity", "dates",
     "Heure murale + zone -> single | fold | gap : les heures qui "
     "n'existent pas (spring forward) ou qui existent DEUX FOIS (fall "
     "back), chaque instant UTC nomme avec offset et abréviation, la "
     "regle PEP 495 dite, les voisins du trou rendus — le verdict que "
     "date/tz applique en silence, cron_next ne signale pas",
     "dst daylight saving fall back spring forward ambiguous "
     "nonexistent wall clock runs twice duplicate cron job time zone "
     "transition pep495 fold heure changement d heure doublon heure "
     "inexistante deux fois fuseau crontab horario de verao hora "
     "inexistente duplo fuso horario duas ocorrencias transicao"),
    ("date_tz_anchor", "/api/v1/date/tz_anchor", "dates",
     "Une heure murale ECRITE dans la zone du job, ANCREE par la "
     "machine dans sa zone : chaque instant UTC candidat, la derive "
     "SIGNEE en minutes (positif = en retard), les deux horloges "
     "relues ; l'offset gagne (resolution Composio #4148) ; single/"
     "fold/gap rendus par l'engine date/tz_ambiguity APPELE, jamais "
     "duplique",
     "naive timestamp scheduler server anchored utc drift late early "
     "wrong fire time hour hours config machine clock mismatch "
     "stripped misread wrote write force offset assumed anchor reminder "
     "meant off murale decalage serveur ecrit relue dispara atraso "
     "adiantado servidor escrito hora clocks vraiment"),
    ("money_flight_comp", "/api/v1/money/flight_comp", "numbers",
     "Date de vol = TABLE de compensation : 261/2004 + Sturgeon/Nelson "
     "avant 2027-10-23, (UE) 2026/2202 codifié APRÈS (seuil « EXCEEDING "
     "3 h » STRICT, 180 min pile ne paye pas), UK261 £220/350/520 avec la "
     "ligne officielle £260 sous 4 h, plafond intra-UE €400 nommé, "
     "réductions = options « le transporteur PEUT », forclusion 9 mois "
     "en date exacte, zéro fetch",
     "flight compensation ec261 uk261 delayed cancelled denied boarding "
     "eur250 eur400 eur600 gbp220 gbp350 gbp520 claim deadline refund air passenger "
     "rights indemnite vol retard annulation suppression billet "
     "forclusion recours compensacao voo atrasado cancelamento "
     "direitos do passageiro aeronautico"),
    ("date_week", "/api/v1/date/week", "dates",
     "Semaine ISO aller-retour — année ISO SEPARÉE du %Y, W53 par LE "
     "THÉORÈME (53 jeudis ⟺ Jan-1 jeudi, ou mercredi + bissextile ; "
     "zéro table), semaine inexistante refusée avec l'artefact %Y-W%V "
     "nommé, conventions Excel/US (%U %W WEEKNUM) côte à côte, notes "
     "PostgreSQL/Snowflake",
     "iso week week number isoweek isocalendar w53 kw53 week-based-year "
     "excel weeknum isoweeknum date boundary reporting semana numero "
     "semaine iso semaine semaine53 calendrier kw kalenderwoche woche wochenzahl "
     "numero da semana semana iso contagem de semanas ano semanal"),
    ("units_shoe_size", "/api/v1/units/shoe_size", "numbers",
     "Pointures en millimetres exacts — pas publiés en fractions "
     "(barleycorn 127/15, Paris point 20/3), demi ET tiers comme "
     "candidats de grille, derive entre systemes DITE, jamais un "
     "seul numero confiant, charts marques hors contrat",
     "shoe size eu us uk conversion pointure taille chaussure "
     "mondopoint barleycorn paris point sneaker trainer foot length "
     "mm largeur taille de chaussure pointilles numero sapato "
     "conversao tamanho de sapato mezinha palmilha"),
    ("net_sri", "/api/v1/net/sri", "web",
     "Attribut Subresource Integrity depuis des OCTETS LOCAUX — "
     "jamais de fetch : integrity pret a coller, crossorigin, audit "
     "du style d'attribut (classe CVE-2026-120423 TAB), URL @latest "
     "ou range signalees comme panne programmee",
     "sri subresource integrity hash cdn script crossorigin sha384 "
     "tampering pin version attribut integrity empreinte CDN "
     "detournement verrouiller assinatura integridade sri script "
     "externo hash verificacao"),
    ("text_url_canonical", "/api/v1/text/url_canonical", "text",
     "RFC 3986 §6.2.2 URL canonicalization — every transformation listed, "
     "tracking params removed by named opt-in, IDN to punycode",
     "url canonical normalize dedupe tracking utm gclid fbclid punycode "
     "normaliser url doublons rastrear enlace"),
    ("xml_to_json", "/api/v1/xml/to_json", "repair",
     "XML to JSON with the conversion rules printed in the response; "
     "force_array pins cardinality, DTD refused by name",
     "xml to json conversion parsing feed soap atom rss "
     "conversion xml vers json parsing fluxo"),
    ("web_cert", "/api/v1/web/cert", "web",
     "X.509 certificate lint from PEM: SANs, validity, deprecation flags, "
     "chain shape; as_of makes the verdict replayable",
     "certificate tls ssl x509 pem cert expiry expiration validity "
     "chain expire certificat cert expire"),
    ("id_checkdigit", "/api/v1/id/checkdigit", "checks",
     "check digits: ISBN/EAN/GTIN/ISIN/LEI… verify, repair, scan",
     "check digit isbn ean upc gtin issn isin cusip sedol aba lei orcid "
     "cas verhoeff damm checksum barcode identifier typo transposed "
     "wrong digit chiffre de controle verificador dígito"),
    ("image_rightsize", "/api/v1/image/rightsize", "web",
     "deterministic PNG resize: exact box / bilinear / nearest, integer "
     "resampling, same bytes forever",
     "image png resize rightsize thumbnail avatar redimensionner image "
     "miniature图标 图标 redimensionar ícone avatar"),
    ("money_rates", "/api/v1/money/rates", "numbers",
     "official ECB reference rates: latest day or 90-day archive, crosses "
     "in Decimal, never an invented rate",
     "currency exchange forex taux devises cambio câmbio dollar euro "
     "real conversion historique"),
    ("doc_text", "/api/v1/doc/text", "extract",
     "PDF to text per page: CMaps, Flate, honest no-text-layer verdicts",
     "pdf extract text document facture invoice documento extrair "
     "texte extraer"),
    ("money_amortize", "/api/v1/money/amortize", "numbers",
     "loan schedule: annuity payments, interest per month, balance to 0.00",
     "loan amortization mortgage financiamento empréstimo pret crédito "
     "mensualité tableau"),
    ("money_interest", "/api/v1/money/interest", "numbers",
     "compound interest + effective annual rate, formula included",
     "compound interest savings juros compostos intérêts composés EAR "
     "capitalisation épargne"),
    ("ics_validate", "/api/v1/ics/validate", "time",
     "VCALENDAR lint: RFC 5545 MUSTs as errors, SHOULDs as warnings",
     "ics calendar validate lint vevent dtstart dtend RFC rfc5545 "
     "calendrier agenda verificação"),
    ("schedule_holidays", "/api/v1/schedule/holidays", "time",
     "statutory holidays FR BR PT DE US with the law cited on every line",
     "holiday feriados férias jours fériés feiertage feriado nacional "
     "calendar calendrier business days jour ouvrable"),
    ("web_cache", "/api/v1/web/cache", "web",
     "Cache-Control text -> RFC 9111 action, freshness, inert directives",
     "cache cache-control http max-age etag freshness revalidate "
     "cache-cache revalidation"),
    ("gzip_roundtrip", "/api/v1/gzip/roundtrip", "web",
     "deterministic gzip compress/decompress, mtime zeroed, base64",
     "gzip compress decompress deflate archive payload zlib "
     "comprimer décompresser"),
    ("qr_generate", "/api/v1/qr/generate", "web",
     "text -> QR code: deterministic SVG or module matrix, ISO 18004",
     "qr qrcode barcode svg matrix link share code paiement facture "
     "lien flash código"),
    ("table_peek", "/api/v1/table/peek", "repair",
     "table profile: column types, nulls, uniques, min-max — closed rules",
     "profile columns preview schema infer peek table data types nulls "
     "uniques minimum maximum profil colonnes aperçu perfis colunas"),
    ("csv_diff", "/api/v1/csv/diff", "repair",
     "row diff by key: added, removed, changed fields, same count",
     "diff compare changes delta versions export lignes changements "
     "comparar diff alterações"),
    ("ssh_fingerprint", "/api/v1/ssh/fingerprint", "web",
     "ssh key line -> SHA256/MD5 fingerprints exactly as ssh-keygen prints",
     "ssh key fingerprint host authorized_keys empreinte clé serveur "
     "huella clave impressão digital"),
    ("zip_verify", "/api/v1/zip/verify", "web",
     "zip archive listed and CRC-verified in memory, never extracted",
     "zip archive crc checksum verify integrity compressed bundle "
     "archive验证压缩包 verificar arquivo"),
    ("schedule_overlap", "/api/v1/schedule/overlap", "time",
     "schedule: merged busy blocks, overlapping pairs, free gaps, point verdict",
     "schedule agenda calendar availability overlap creneau emploi du temps "
     "agenda disponibilidade horário conflito calendário"),
    ("cron_validate", "/api/v1/cron/validate", "time",
     "cron: parse, impossible-date verdict, next runs from a given time",
     "cron schedule recurring timer expressao scheduler agendador "
     "rappel périodique recorrente"),
    ("crypto_address", "/api/v1/crypto/address", "identity",
     "crypto address: base58check, bech32 segwit, EIP-55 — checksum verdict",
     "address wallet bitcoin btc litecoin ltc eth ethereum base bech32 "
     "segwit taproot p2pkh adresse wallet cartera endereco endereço"),
    ("validate_taxid", "/api/v1/validate/taxid", "identity",
     "tax id: check-digit verdict for CNPJ, CPF, SIREN, SIRET, NIF, VAT EU",
     "tax id cnpj cpf siren siret vat nif numero fiscal identifiant "
     "fiscal impuesto Steuer número fiscal contribuição"),
    ("caip", "/api/v1/caip/parse", "identity",
     "chain identifier caip-2 caip-10: namespace, chain name, checksummed address",
     "caip chain id eip155 base arbitrum polygon solana bitcoin network "
     "identifier chaine identifiant reseau cadena identificação"),
    ("secret_scan", "/api/v1/secret/scan", "checks",
     "does this text leak api keys tokens cards seeds: positions, no echo",
     "secret leak api key token password credential scan detect redact "
     "before post fuiter cle secre clé token mot de passe détecter "
     "vazar segredo chave token detectar"),
    ("text_redact", "/api/v1/text/redact", "checks",
     "mask secrets with stable numbered tags before sharing anything",
     "redact mask anonymize scrub pii secrets remove hide before share "
     "masquer effacer anonymiser cachar mascarar"),
    ("validate_country", "/api/v1/validate/country", "checks",
     "iso country code: alpha3 numeric currency decimals calling code",
     "country code iso alpha currency calling lookup pays land país "
     "moeda indicativo"),
    ("validate_postal", "/api/v1/validate/postal", "checks",
     "postal code grammar per country with canonical spacing",
     "postal zip code cep postcode codigo postal código valid format "
     "plaque cepture"),
    ("geo_distance", "/api/v1/geo/distance", "extract",
     "great-circle distance between points or along an ordered route",
     "distance between coordinates miles km drive route trip "
     "distance coordonnees km trajet rota distancia coordenadas"),
    ("geo_geohash", "/api/v1/geo/geohash", "extract",
     "geohash encode decode with bounding box, published alphabet",
     "geohash location grid cell lat lon box nearby "
     "geohash localisation cellule geolocalizacion"),
    ("file_identify", "/api/v1/file/identify", "extract",
     "what is this blob really: magic bytes, not the file extension",
     "file type magic identify binary what is this blob extension mime "
     "detect fichier type identifier blob mime deviner tipo de arquivo "
     "identificar"),
    ("text_punycode", "/api/v1/text/punycode", "text",
     "unicode domain <-> xn-- idn round trip and homoglyph check",
     "punycode idn domain unicode xn-- internationalized homoglyph "
     "phishing dns域名域名 verificação domínio"),
    ("semver_parse", "/api/v1/semver/parse", "code",
     "official semver grammar: parts, prerelease, build, stability",
     "version parse major minor patch prerelease release semver check "
     "versie analyse versioning tag stable"),
    ("semver_sort", "/api/v1/semver/sort", "code",
     "sort versions by precedence not alphabet: 10 > 2, pre < release",
     "sort versions latest newest release semver order changelog "
     "trier versions dernier order release"),
    ("text_sanitize", "/api/v1/text/sanitize", "text",
     "cross-OS filename safe: reserved names, charset, byte budget, why",
     "filename sanitize safe file name reserved windows illegal chars "
     "nom de fichier sur sanitize nome arquivo invalido"),
    ("json_map", "/api/v1/json/map", "repair",
     "apply closed case-and-number ops to every item of an array",
     "map array list each element transform over items bulk shape list of"
     "parcourir liste chaque transformer elemente mapear lista cada"
     " array of objects style"),
    ("num_fx", "/api/v1/num/fx", "numbers",
     "convert currency with YOUR explicit rate: exact Decimal, ISO minor units",
     "currency convert fx exchange usd eur brl jpy money transfer price "
     "devise convertir taux change moeda conversao taxa cambiorate"),
    ("id_ulid", "/api/v1/id/ulid", "identity",
     "deterministic ULID make/parse/sort: same seed, same id — retry-safe",
     "ulid sortable id idempotency key generate order time prefix "
     "créer identifiant graine tri ulid crear identificador ordenacao semente"),
    ("pkg_name", "/api/v1/pkg/name", "code",
     "npm, PyPI or Docker package name valid? normalized and exactly why not",
     "package name npm pypi docker pip registry invalid normalize "
     "module publish wheel tag repo nome pacote invalido normalizar"),
    ("hash_hmac", "/api/v1/hash/hmac", "identity",
     "sign and verify a payload with a shared key: constant-time match",
     "hmac sign verify webhook authenticity shared secret signature "
     "inter-agent trust signer vérifier signature secret partagé "
     "hmac assinar verificar assinatura segredo compartilhado"),
    ("hash_digest", "/api/v1/hash/digest", "identity",
     "md5/sha/blake2b, hex + base64",
     "hash digest sha256 md5 sha1 blake2b checksum integrity b64 hex "
     "verify blake empreinte"),
    ("enc_base64", "/api/v1/enc/base64", "identity",
     "base64/hex encode/decode, urlsafe",
     "base64 encode decode hex urlsafe padding binary data uri hexdump "
     "encoding b64"),
    ("jwt_decode", "/api/v1/jwt/decode", "identity",
     "JWT segments, never fake-verified",
     "jwt token decode header payload signature base64url claims segment "
     "who issued"),
    ("id_uuid", "/api/v1/id/uuid", "identity",
     "v5/v7/seeded-v4, deterministic",
     "uuid generate id namespace seeded version v5 v7 identifier "
     "deterministic seed urn"),
    ("id_slug", "/api/v1/id/slug", "identity",
     "text -> clean URL slug",
     "slug url text normalize transliterate seo permalink friendly "
     "filename accents titre"),
    ("fingerprint", "/api/v1/fingerprint", "identity",
     "canonical hash of JSON/CSV",
     "fingerprint hash dedupe compare json csv canonical same config "
     "detect drift clusters content identical files empreinte"),
    ("validate_iban", "/api/v1/validate/iban", "checks",
     "61 countries, BBAN + mod-97",
     "iban bank validate payment account sepa country bban transfer payout "
     "mod97 bancaire"),
    ("validate_phone", "/api/v1/validate/phone", "checks",
     "E.164 + country rules",
     "phone validate number e164 mobile country ddi plus dial whatsapp "
     "numero"),
    ("validate_email", "/api/v1/validate/email", "checks",
     "email syntax + domain policy",
     "email validate address smtp syntax domain mx disposable typo plus "
     "addressing endereco"),
    ("validate_url", "/api/v1/validate/url", "checks",
     "URL structure + scheme rules",
     "url validate link scheme href uri http https malformed param anchor "
     "idn punycode lien"),
    ("color_check", "/api/v1/color/check", "checks",
     "hex/rgb/hsl + WCAG contrast",
     "color contrast wcag accessibility hex rgb hsl check aa aaa readable "
     "background foreground lighthouse contraste"),
    ("text_count", "/api/v1/text/count", "text",
     "words/sentences/lines/bytes exact",
     "count words characters lines sentences bytes text measure how long "
     "medida compte"),
    ("sort_natural", "/api/v1/sort/natural", "text",
     "file2 sorts before file10",
     "sort natural order filenames list version numeric human alphabetical "
     "tri"),
    ("text_case", "/api/v1/text/case", "text",
     "camel/snake/kebab/pascal exact",
     "case camel snake kebab pascal convert naming identifier screaming "
     "style variable conversion"),
    ("text_truncate", "/api/v1/text/truncate", "text",
     "boundary-exact truncation",
     "truncate cut limit text length boundary ellipsis words tweet shorten "
     "fit whole mid coupure"),
    ("regex_test", "/api/v1/regex/test", "text",
     "match/spans/groups/replace, sandboxed",
     "regex pattern match test replace find findall groups hang "
     "catastrophic backreference named grep sanitize"),
    ("text_chunk", "/api/v1/text/chunk", "text",
     "exact token-budget RAG chunks",
     "chunk rag tokens budget embedding split document tiktoken embeddings "
     "context window cl100k ingestion decoupe"),
    ("md_render", "/api/v1/md/render", "text",
     "markdown -> safe closed HTML",
     "markdown html render convert table headings sanitize readme email "
     "escape safe rendu"),
    ("html_text", "/api/v1/html/text", "text",
     "HTML -> canonical readable text",
     "html text extract scrape strip readable label boilerplate script "
     "style page actually says lisible"),
    ("recipe_shop_reste", "/api/v1/fiche/shop-reste", "numbers",
     "la chaîne « du RESTE » en un appel : total, vendus du matin, "
     "% de l'après-midi -> la trace des trois pas et le reste exact ; "
     "0/28 nu et retry sur cette forme (bench v15) — la décomposition "
     "est le travail, il est déjà fait ici",
     # Bundle 72 (23-11) — trou PT dicté par le radar, ligne « loja
     # tinha 435… » NO_MATCH active depuis 21h57 (scans 21h57→06:22).
     # Les 7 mots sont LIBRES (audit de possession du cycle : aucun
     # voisin ne les porte — sobras/geladeira/frigo restent chez
     # leftovers, restante chez partage). « quantos » JAMAIS pris
     # (interrogatif, loi c129b4d). Un seul de ces mots = 3 < plancher
     # T6 : la loi anti-mot-incidentel tient, la phrase complète = 18.
     "remaining stock shop inventory of the rest du reste "
     "afternoon pourcentage apres-midi combien restent il reste "
     "quantite restante vendas restantes restando depois "
     "loja vendeu manha manh tarde resto restam"),
    ("recipe_partage_reste", "/api/v1/fiche/partage-reste", "numbers",
     "part de la PART : total, première part, seconde « du reste » -> "
     "la seconde part + le reliquat, fractions exactes tracées",
     "share of the rest inheritance budget split fraction premier "
     "partage heritage budget repartition du reste parte do restante "
     "heranca divisao"),
    ("recipe_soldes2", "/api/v1/fiche/soldes2", "numbers",
     "deux remises, un prix final exact + le mensonge de la somme "
     "chiffré ; les chaînes à N paliers restent chez money/discount",
     "two discounts sale price final remise solde successive "
     "desconto duplo deux pourcentages cascade simple"),
    ("recipe_clean_table", "/api/v1/recipe/clean-table", "repair",
     "one call: dirty CSV -> typed unique rows",
     "recipe pipeline csv clean typed rows rag table trio shortcut sales "
     "quick start one call"),
    ("recipe_clean_json", "/api/v1/recipe/clean-json", "repair",
     "one call: broken JSON -> repaired canonical text",
     "recipe pipeline json repair broken canonical shortcut printed give "
     "one call"),
    ("recipe_data_trio", "/api/v1/recipe/data-trio", "repair",
     "one call: dirty csv + broken json + url list -> final YAML {rows, totals, urls}",
     "recipe trio rag ingestion preprocess csv json urls yaml rows totals "
     "pipeline shortcut one call"),
    ("color_palette", "/api/v1/color/palette", "design",
     "closed harmonies + lightness ramps",
     "palette color design harmony scheme swatch triad complementary brand "
     "shades tints"),
    ("check_constraints", "/api/v1/check/constraints", "checks",
     "draft + closed constraints -> pass/fail per rule",
     "check verify constraints self review did i follow word limit points "
     "numbered list proofread before sending verifier reponse controle "
     "conta pontos limite"),
    ("check_refs", "/api/v1/check/refs", "checks",
     "cited urls numbers hex uuid vs provided sources",
     "hallucinated link citation source match refs invented quote verify "
     "references unknown url citation check liens inventes "
     "verificacao citacoes"),
    ("extract_facts", "/api/v1/extract/facts", "extract",
     "every money date number url email uuid iban, none lost",
     "extract facts invoice numbers dates amounts urls emails inventory "
     "what figures summarize document extraction extraire faits montants "
     "extrair valores"),
    ("text_select", "/api/v1/text/select", "extract",
     "top-k chunks by closed coverage rules",
     "select relevant passages chunks query coverage retrieve without "
     "embedding search extractive choisir passages selection"),
    ("logic_rules", "/api/v1/logic/rules", "logic",
     "facts + closed rules -> per-rule trace",
     "logic rules if then else policy conditions gate validate decision "
     "constraints business multi step reasoning si alors politique "
     "regras decisao"),
    ("sort_multi", "/api/v1/sort/multi", "logic",
     "multi-key stable sort with explicit tie order",
     "sort multiple keys criteria rank order tiebreaker tri classement "
     "multi-criteres ordenar prioridade"),
    ("json_query", "/api/v1/json/query", "logic",
     "$-path nested access, [*] wildcards, canonical paths",
     "jsonpath nested deep extract path wildcard query reach array "
     "imbrique profonds chemin abfrage"),
    ("check_redlines", "/api/v1/check/redlines", "checks",
     "forbidden words/regex/PII shapes/budget in your draft: clean or first violation",
     "never include pii leak identifier forbidden privacy redline "
     "ban mention interdit fuite confidential never say confidential "
     "nunca incluir vazio proibido privacidade vazamento"),
    ("check_target", "/api/v1/check/target", "checks",
     "is the answer for the RIGHT quantity? target lock: named target, named refusal, closed synonym grammar",
     "target lock cible verrou answer name quantity refuse "
     "alvo cadeado resposta nome quantidade mauvaise question a cote "
     "the wrong question right number wrong naming answered beside"),
    ("check_agreement", "/api/v1/check/agreement", "checks",
     "do these payloads describe the same deal? every divergence by pointer",
     "same deal agree divergence mismatch two agents claim signed "
     "consentement identique different divergent meme accord deux agents "
     "mesmo acordo divergente dois agentes mesmo negocio"),
    ("intent_check", "/api/v1/intent/check", "core",
     "the filled form checked before you pay: ok, or exactly what to ask",
     "check validate form filled fields missing ready submit card "
     "verifier formulaire champs manquer demander avant payer"),
    ("formula_catalog", "/api/v1/formula", "numbers",
     "règle de trois, dilution C1V1, dosage mg/kg, EDD Naegele, "
     "hydratation du boulanger, part en pourcentage — la formule "
     "publiée, vos nombres substitués, le calcul exact",
     "formula rule of three dilution dosage naegle due date "
     "hydration bakers percentage percentage of total vitesse "
     "temps distance vitesse consommation carburant règle de trois "
     "date de naissance prévue hydratation levain pourcentage"),
    ("intent_reflect", "/api/v1/intent/reflect", "core",
     "le miroir de compréhension : tu déclares ta lecture (formule + "
     "args), la machine te la rend écrite et exacte avant que tu la "
     "prennes pour la vérité",
     "comprehension reading check word problem énoncé comprendre "
     "vérifier ma lecture j'ai mal compris misread"),
    ("intent_card", "/api/v1/intent/card", "core",
     "plain sentence -> the right tool + a pre-filled form, or the exact question to ask",
     "what can you do help intent unclear ambiguous ask human which tool "
     "fiche remplir question que peux tu faire aide quelle outil "
     "nao entendi qual ferramenta pedir humano preencher formulario"),
    ("batch", "/api/v1/batch", "core",
     "one tool over N payloads in a single call",
     "batch bulk many items loop iterate whole file all rows at once "
     "process repeatedly par lots plusieurs tous en une fois"),
    ("recipe_invoice", "/api/v1/recipe/invoice", "numbers",
     "one call: line items + VAT -> exact invoice + amount words + due",
     "invoice bill facture prepare totals vat amount words due date "
     "préparer facture client note de frais nota fiscal"),
    ("recipe_facts", "/api/v1/recipe/facts", "extract",
     "one call: messy text -> sorted money/percent/date/url inventory + total",
     "extract all numbers dates amounts urls emails from text inventory "
     "sum total summarize document report figures facts multi steps "
     "extraire tous les montants dates chiffres rapport inventaire "
     "extrair valores datas resumo documento"),
    ("recipe_schedule", "/api/v1/recipe/schedule", "dates",
     "one call: cron + start -> occurrences + ready ICS",
     "appointment calendar schedule meeting slots planifier rendez-vous "
     "agenda programação agendar"),
    ("text_decode", "/api/v1/text/decode", "text",
     "mojibake -> utf-8, only provable fixes",
     "encoding garbled mojibake cafÃ utf8 latin1 broken accents "
     "illisible encodage caracteres embaralhado"),
    ("num_human", "/api/v1/num/human", "numbers",
     "duration bytes roman ordinal shaped for humans",
     "how long humanize bytes size kb mb duration seconds format "
     "roman number ordinal duree taille octets tempo tamanho"),
    ("text_escape", "/api/v1/text/escape", "text",
     "one value escaped for html sql shell csv json url",
     "escape injection sanitize quote sql shell html csv url "
     "échapper echapper injection protege requete"),
    ("text_normalize", "/api/v1/text/normalize", "text",
     "unicode forms, accents, fullwidth, whitespace rules",
     "unicode normalize nfc nfd accents fullwidth match names dedupe "
     "equal look same acentos normalizar"),
    ("eth_address", "/api/v1/eth/address", "checks",
     "EIP-55 checksum + allowlist verdicts",
     "wallet address typo checksum ens send safe verify recipient "
     "allowlist adresse portefeuille destinataire"),
    ("eth_selector", "/api/v1/eth/selector", "identity",
     "signature -> 4-byte calldata selector",
     "calldata function selector abi signature encode four bytes "
     "selecteur fonction contrat"),
    ("eth_units", "/api/v1/eth/units", "numbers",
     "exact wei gwei ether conversions",
     "wei gwei ether decimals token amount units approve swap "
     "montant decimales"),
    ("eth_abi_encode", "/api/v1/eth/abi-encode", "identity",
     "types+values -> exact calldata",
     "calldata encode function contract call arguments solidity abi "
     "encoder appel contrat"),
    ("eth_abi_decode", "/api/v1/eth/abi-decode", "identity",
     "calldata -> readable values",
     "decode calldata inspect transaction signing blind review payload "
     "décoder transaction signature"),
    ("eth_eip712", "/api/v1/eth/eip712", "identity",
     "typed data -> EIP-712 0x1901 digest",
     "permit eip712 typed domain separator digest sign signature meta "
     "signature déléguée"),
    ("eth_receipt", "/api/v1/eth/receipt", "checks",
     "logs + expected effects -> match verdict",
     "receipt verify transfer log topic confirm amount sent worked "
     "reçu confirmation transfert"),
    ("money_baggage", "/api/v1/money/baggage", "numbers",
     "Date du vol = palier LOI (40×30×15 sous le siège GRATUIT depuis "
     "2027-10-23, RIEN avant — chaque compagnie décide) ; casier : la "
     "loi ne fixe AUCUNE taille ; gabarits transporteur EN ARGUMENTS, "
     "jamais fetchus ; ajustement PAR DIMENSION avec ROTATION (40×18×30 "
     "passe dans 40×30×20) ; le « cumul 100 cm / 7 kg » de la presse "
     "rendu comme affirmation TESTÉE (55+40+20=115), jamais comme règle",
     "cabin baggage carry on size 40x30x15 under seat underseat personal item "
     "hand luggage allowance does my bag fit suitcase sizer gauge "
     "rotation overhead new eu rule air passenger voyage sac "
     "bagage cabine dimensions franchie main valise sous le siège "
     "règle ue bagagem de mão malas de mão dimensões cabine "
     "regulamento eu bagagem franquia tamanho permitido"),
    ("csv_excel_damage", "/api/v1/csv/excel_damage", "repair",
     "Ce qu'Excel DÉTRUIT au double-clic, PRÉDIT avant : zéros de tête "
     "(02134→2134), mur des 15 chiffres (…1111→…1110), notation "
     "scientifique (1E5→100000), dates forcées (SEPT2, MARCH1, « 3-4 » "
     "= 4 mars EN / 3 avril EU — locale ARGUMENT, année figée par "
     "as_of), formes de formule (=-+@), pleine chasse ; règles = les "
     "trois interrupteurs Microsoft nommés ; import colonne-Texte "
     "PRESCRIT ; csv/fix répare, ici on PRÉDIT",
     "excel csv damage leading zeros scientific notation date "
     "conversion corrupted on open double click spreadsheet gene "
     "names postcode truncation digits import text columns "
     "dtype forecast predict before opening excel détruit zéros "
     "conversion date mise en forme import texte colonnes planilha "
     "csv excel zeros à esquerda notação científica corrupção ao "
     "abrir datas forçadas"),
    ("money_crossover", "/api/v1/money/crossover", "numbers",
     "Prix de reviens de DEUX tarifs à composantes (unitaire + fixe) : "
     "la bascule en FRACTION EXACTE — les sept calculateurs publiés "
     "arrondissent le Δ fixe avant de diviser et se contredisent ; "
     "conventions de jours NOMMÉES (mensuel ×12 exact, jamais 30 "
     "jours ; journalier ×365 ou 366 bissextile fourni ; « semaine » "
     "refusée) ; DOMINATION rendue « never » nommée ; km si "
     "consommation FOURNIE ; frais one-off en mois de payback, "
     "séparés de la bascule structurelle",
     "energy tariff comparison break-even kWh standing charge unit "
     "rate which is cheaper crossover fixed plus variable saas seats "
     "per user monthly annual leap year ev charging cost per km domi "
     "nation breakeven tarif comparaison prix de reviens bascule kwh "
     "abonnement fixe mensuel journalier quelle consommation "
     "compensação tarifa qual mais barata ponto de equivalência kwh "
     "assinatura mensalidade taxa de adesão plano barato"),
    ("money_points", "/api/v1/money/points", "numbers",
     "Combien vaut un POINT : cpp = (prix cash - reste cash - "
     "rewards forgoes) / points x 100 en FRACTION EXACTE (1081/725 "
     "la ou la presse dit 1.49) ; voies cote a cote triees, egalites "
     "nommees, verdict contre FLOOR fourni, solde x cpp, retour "
     "effectif pts/$ x cpp ; jamais de table de valorisation "
     "embarquee",
     "points worth redeem redemption cents cpp award travel portal "
     "statement credit gift card balance value taxes earning rate "
     "return dollar vale resgate ponto saldo centimes vaut fracao "
     "voies"),
    ("csv_excel_display", "/api/v1/csv/excel_display", "repair",
     "Ce qu'Excel AFFICHE d'une valeur STOCKÉE sous un code numFmt : "
     "la virgule trailing SCALE par mille (« $#,##0, » + 1 000 000 → "
     "$1,000 — l'attaque mesurée arXiv 2611.05806, six extracteurs "
     "python aveugles) ; exemples de la table Microsoft rejoués "
     "(« #.0,, »→12.2, « (000) »→(012), « 0% »→50%) ; arrondi de "
     "display demi-vers-le-large dit ; locale en ARGUMENT (les "
     "séparateurs du fichier sont des symboles — ingénieur Micro"
     "soft) ; General/dates/couleurs refusés PAR LE NOM ; rendu de "
     "style, la prédiction d'import est une autre route",
     "excel numfmt styles xlsx stored rendered diverge scale "
     "thousands trailing comma markitdown openpyxl pandas wrong "
     "budget cell shows saw shown extractor misled mise en forme affichée "
     "valeur stockée rendu format nombre affichage cellule styles "
     "xml visual formato número exibido célula render estilo de "
     "número valor estocado"),
    ("ship_dimweight", "/api/v1/ship/dimweight", "numbers",
     "Le poids VRAIMENT facture du colis : dimensions arrondies AU "
     "POUCE SUPERIEUR avant volume, volume ÷ diviseur (son unite est "
     "DECLAREE — le piege mm÷139 x16,4 devient impossible), max(actual, "
     "dimensionnel), ceil au palier, plafond. rollo 35 lb vs amzprep "
     "34,5 sur les MEMES pouces : la fraction exacte 4800/139 tranche "
     "et chaque etape est nommee ; tables transporteurs en ARGUMENTS "
     "(USPS 166→139 le 12-juil-2026 = elles pourrissent)",
     "dimensional weight dim billed parcel box carrier divisor "
     "pound volumetric shipping cost surprise max fee girth "
     "poids facture colis dimensions volumetrique transporteur "
     "expedition livre pale palier plafond poids volumetrique colis "
     "cobrado cubagem caixa envio transportadora divisor faturamento"),
    ("json_coerce", "/api/v1/json/coerce", "repair",
     "Repare les ARGUMENTS d'un appel d'outil qu'un lecteur STRICT "
     "refuse : 8.0→8 (classe serde « invalid type: floating point "
     "2500.0, expected u64 », 11/11 tours mesurés), exponents et "
     "fractions vraies laisses TELS QUELS, 'false' en chaine refuse PAR "
     "LE NOM (piege truthy), string→number seulement si cast_strings=on, "
     "'007' JAMAIS (les zeros de tete sont du payload), cles dupliquees "
     "refusees ; la notation d'origine est CONSERVEE a la sortie",
     "tool call arguments coerce cast serde u64 i64 whole float "
     "invalid type floating point expected strict parse call args "
     "truthy quoted false leading zeros notation "
     "arguments appel outil coercion arguments refuses "
     "argumentos chamada ferramenta coerção tipos estritos"),    ("money_bogo", "/api/v1/money/bogo", "numbers",
     "Le pourcentage que la CAISSE applique vraiment sous un panneau "
     "« BUY ONE GET ONE 50 % » : la remise porte sur le MOINCHER des "
     "deux (règle de détail publiée — 60+40 rend 80 sur 100, soit 20 %, "
     "ni 25 ni 50), prix égaux = 25 % de la paire JAMAIS 50, l'article "
     "impair se paie PLEIN (les paires sont DONNÉES, jamais devinées), "
     "le coupon s'EMPILE en produit de facteurs (25 puis 30 = 47,5, "
     "jamais 55) ; trace par paire, fraction exacte à côté de "
     "l'affichage",
     "bogo buy one get one second item cheaper pair effective checkout "
     "half off percent promo hoodies fine print real discount stack "
     "coupon bogo achète un obtiens le deuxième gratuit moins cher "
     "paire pourcentage réel caisse promo moitié prix empiler coupon "
     "note bogo compre um leve segundo grátis mais barato par "
     "porcentagem real caixa promoção metade preço cupom desconto "
     "verdadeiro"),
    ("agent_modelid", "/api/v1/agent/modelid", "code",
     "audit model ids against a pasted catalog — named verdicts, "
     "did-you-mean at a named distance, never swears the GET (V23)",
     "model id modelid litellm openrouter gateway prefix prefixe "
     "prefixo not found invalid identifier alias catalog annuaire "
     "catalogo erreur config agent nome modelo catalogo "
     "identificador inexistente errado vierge tiret underscore "
     "batch embedding"),
    ("food_poultry", "/api/v1/food/poultry", "dates",
     "turkey thaw & roast window, USDA FSIS tables, ISO clock as "
     "argument — never wall clock, never invented numbers",
     "turkey poultry thaw defrost freezer fridge roast cook time "
     "window dinner bird when take out frozen thanksgiving dinde "
     "volaille congélateur congelateur cuisson four sortir heur "
     "decongelar assar peru janela hora congelado"),
    ("food_leftovers", "/api/v1/food/leftovers", "dates",
     "leftovers window, USDA FSIS: 2h gate, 3-4 days fridge, 2-6 "
     "months freezer (UNION of the two contradicting FSIS pages) — "
     "all times ARGUMENTS, never wall clock, never invented tables",
     "leftovers leftover reheating reheat gravy stuffing discard "
     "bin danger conservation rechauffer sobras geladeira "
     "esquentar keep garder rester consommer validade durar "
     "safe frigo"),
    # Bundle 73 (23-11) — le compte à rebours d'UN four. Tags neufs
    # passés à l'audit de possession : oven / countdown / preheat /
    # conflict / serve / minuterie / forno / assado / sequencia /
    # cronograma / temperatura étaient LIBRES ; « schedule » (7
    # possesseurs), « roast » (poultry), « timing » (leftovers) et
    # « rest » (les deux recettes) ne sont PAS pris — pas de
    # co-quille, loi des voisins.
    ("food_ovenschedule", "/api/v1/food/ovenschedule", "dates",
     "un four, des plats, une heure de service : compte à rebours à "
     "l'envers, conflits de température nommés, jamais d'horloge "
     "murale — les timelines web ne vérifient rien de tout ça",
     "oven countdown preheat conflict serve four plan du four "
     "minuterie forno assado sequencia cronograma temperatura "
     "température"),
    ("shop_gift_voucher", "/api/v1/shop/gift-voucher", "dates",
     "gift voucher clocks: IE five-year floor, deemed override, "
     "EUR1 refund floor, conflicts named; FR no statutory minimum",
     "gift voucher expired expiry expires validity dead card "
     "deemed five years refund balance one euro single use stack "
     "limit name lost stolen replacement durable irish ireland "
     "jd ccpc "
     "carte cadeau expire expiree perime perimee valide validite "
     "duree solde irlande geste commercial remboursee bon "
     "cartao presente vale venceu expirou validade duracao "
     "irlanda saldo"),
    ("shop_soldes_window", "/api/v1/shop/soldes-window", "dates",
     "sale windows dated from the 2019 arr\u00eate: advance clauses "
     "both seasons, seven annual derogations 2020-2026 verbatim, "
     "versioned annex, ouvr\u00e9 ambiguity named, foreign calendars "
     "refused",
     "soldes window arrete dates legal hiver ete debut fin "
     "ouverture cloture quand commencent prolongation derogation "
     "report semaines canicule mercredi premier deuxieme dernier "
     "france lorraine corse guadeloupe martinique guyane reunion "
     "mayotte saint pierre barthelemy moselle nice metz perpignan "
     "saldos epoca verao inverno franca sales sale france winter "
     "summer start january june official"),
    ("shop_soldes_be", "/api/v1/shop/soldes-be", "dates",
     "belgian sale windows dated from art. VI.25 CDE: the sunday "
     "clause both seasons, the one-month standstill enumerated not "
     "guessed, corona reports 2020-2021 carried verbatim, an "
     "overruled clause kept visible, france and luxembourg pointed "
     "to their own tables",
     "soldes belgique belgie solden opruiming schlussverkauf periode "
     "attente pre-soldes presoldes sperperiode hiver ete janvier "
     "juillet aout debut cloture clause dimanche report prolongation "
     "bruxelles brussel antwerpen belgium sales sale dates winter "
     "summer january august royal decree livre vi "
     "saldos belgica verao inverno epoca espera janeiro agosto"),
    ("shop_withdrawal", "/api/v1/shop/withdrawal", "dates",
     "withdrawal dated FR BE LU: one parcel, three grammars — "
     "Saturday advances FR/BE, SURVIVES LU, twelve months when info "
     "missing, exceptions as named classes",
     "withdrawal retraction retract withdraw withdraws revocation "
     "revoke change my mind online order cooling off "
     "fourteen days received parcel expiry advance holiday "
     "solded occasion distance online "
     "retractation retracter retracte retractes delai changer avis "
     "quatorze jours reception recu colis distance internet solde "
     "ligne commande change avis decision retracter "
     "occasion prorogation feries date limite loi "
     "retractation france "
     "retratacao retratacoes desistencia desisto desiste arrependimento "
     "francia prazo quatorze dias desistir "
     "lei francesa feriado fim de semana contagem "
     "encomenda recebida compra desistencia posso terça terca"),
    ("shop_soldes_lu", "/api/v1/shop/soldes-lu", "dates",
     "luxembourg sale windows dated BY ACT: the loi du 23-12-2016 "
     "hands both periods to a grand-ducal decree EVERY YEAR "
     "— zero formule; ten replayed acts 2018..2027, two "
     "rectifications of two kinds (weekday label 2018, the bound "
     "itself 2023), the 2021 chain of three acts with its dead "
     "postponement, no waiting period unlike Belgium, never "
     "extrapolated past the last act",
     "soldes luxembourg lëtzebuerg winter summer sale sales "
     "date legale ouverture cloture "
     "reglement grand-ducal memorial "
     "hiver ete wanter "
     "saldos luxemburgo datas verao inverno "
     "luxemburger luxembourgish "
     "esch diekirch wiltz vianden groussherzogtum"),
)

TOOL_NAMES = tuple(t[0] for t in TABLE)
PATHS = {t[0]: t[1] for t in TABLE}
PACK_OF = {t[0]: t[2] for t in TABLE}


def tier(path):
    if path in payments.PRICES:
        return "paid " + payments.PRICE_LABELS[path]
    if path in payments.CAP_ROUTES:
        return "cap"
    return "free"


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canon(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode("utf-8")).hexdigest()


def manifest_text(version):
    """One line per tool, sections per pack. The 8.8 KB fold-budget is a
    portability CONTRACT for weak models (test-pinned): dense prose while
    it fits, dense table when it does not — names+paths+tiers always,
    purposes on demand via /route and /tools/<name>.json."""
    head = [
        # b104 elagage MESURE (consigne b103 « elague des l'annonce ») :
        # la ligne de TITRE et la ligne TIERS sont FUSIONNEES en une
        # seule, tout le contenu voyage — 217 lignes <218 avec
        # +agent_costdiff, octets <9 000 avec la NOTE dense resseree
        # a claim constant (les deux pointeurs de purpose vivent).
        # b111 elagage MESURE (+agent_tooloverlap, 52 octets a payer) :
        # tete « — » -> « - » (-2) ; « every POST carries » -> « POSTs
        # carry » (-7) ; « every 400 names » -> « 400s name » (-6) ;
        # « error IS the repair prompt » -> « error IS repair prompt »
        # (-4) ; « — » milieu -> « ; » (-4) ; « from one » -> « from 1 »
        # (-3) ; label « detail: » COUPE — le chemin /tools/<name>.json
        # se nomme lui-meme (-8) ; « POST /api/v1/pipeline » ->
        # « /api/v1/pipeline » (-5, convention b107 : le verbe vit dans
        # le schema, le pointeur porte le chemin) ; « "task words" » ->
        # « "words" » (-5, la place est payee par le chemin lui-meme) ;
        # « -> sister moovicut.studio » -> « -> moovicut.studio » (-7,
        # « sister » se lit sur la landing et dans SKILL.md, le manifeste
        # porte le chemin). Mesure b111 : 207 lignes / 8 995 octets.
        "mechacut.studio %s - %d transforms "
        "+ %d recipes. " %
        (version,
         sum(1 for e in TABLE if not e[0].startswith("recipe_")),
         sum(1 for e in TABLE if e[0].startswith("recipe_")))
        + "free=keyless 30/min; cap=free<32KB/x402; paid=x402 from 1. "
          "POSTs carry "
          "sha256; 400s name field+expected; "
          "error IS repair prompt; refusals name "
          "readings. "
          # b105 elagage MESURE (consigne b104 « FR a 23 octets du
          # plafond : le lot suivant HUMAIN paie prose + elagage ») :
          # la ligne de POINTEURS « detail: » est FUSIONNEE dans la
          # ligne de tete — tout le contenu voyage, 217 lignes, le
          # +shop_soldes_be ne debranche rien.
          # b107 elagage MESURE (consigne 23h50 « CE LOT PAIE UN VRAI
          # ELAGUAGE ») : articles et qualificatifs de tete coupes a
          # claim constant (« free under 32KB » -> « free<32KB »,
          # « from call one » -> « from one », « the error » ->
          # « error », « ambiguous refusals » -> « refusals »),
          # « GET » retire de la ligne recipes (le find /route est
          # deja nu — convention maison), « pack install: » ->
          # « packs: », « (HTML) » coupe (le format n'a jamais routé
          # personne), ET LES LIGNES VIDES entre blocs de pack sont
          # SUPPRIMEES — 16 octets et 16 lignes rendus au budget,
          # chaque pack garde son en-tete. Mesure : 205 lignes /
          # 8 988 octets avec la ligne shop_withdrawal incluse.
          # b110 elagage MESURE (la ligne shop_soldes_lu paie ses
          # 46 octets) : le POINTEUR « packs: » est SUPPRIME — chaque
          # en-tete de pack rend son propre /SKILL-<pack>.md, le
          # contenu voyage ; « named » coupe de la tete (adjectif,
          # les recettes sont nommees PAR LEUR LIGNE) ; « scene »
          # tombe de la classe not-here (« breakdowns » reste, classe
          # identique). Mesure LIVE 25-11 10h55 : 206 lignes /
          # 8 995 octets (splitlines — la méthode des cycles
          # précédents).
          # b112 elagage MESURE (+invoice_payment_due, 55 octets a
          # payer) : « deterministic » COUPE de la tete — adjectif,
          # consigne b107, la certification du meme nom est le
          # tracteur sha256 de fin + « POSTs carry sha256 » qui
          # vivent ; le POINTEUR DU MILIEU « /tools/<name>.json | »
          # SUPPRIME — le chemin vit DEJA dans le tail dense-fold
          # (dédoublonnage, claim constant) ; « find: » coupe du
          # pointeur route (le /route?q= nu est la convention
          # maison depuis b107) et ses guillemets « "words" »
          # tombent ; « folded to dense mode » devient « dense fold »
          # (le drapeau se nomme lui-meme, test_bundle0 synchronise)
          # ; « storyboards, shot lists, breakdowns » en SLASHES.
          # Mesure b112 : 208 lignes / 8 99x octets — marge relevee
          # a l'annonce, jamais de memoire.
          "pipelines: /api/v1/recipes|pipeline; "
        "proposals: /proposals|/api/v1/agent/proposals; "
        "not here: storyboards/shotlists/breakdowns "
        "-> moovicut.studio",
        # b102 elagage MESURE (consigne b101 « le prochain outil
        # debranche le dense-fold ou elague une ligne de tete ») :
        # la ligne soeur est FUSIONNEE dans discovery, pas coupee —
        # 217 lignes <218, contenu preserve, budget octets suit.
    ]
    by_pack = {}
    for name, path, pack, purpose, _tags in TABLE:
        by_pack.setdefault(pack, []).append((name, path, purpose))

    def render(with_purpose, note):
        ls = list(head)
        if note:
            ls.append(note)
        for pack in PACKS:
            if pack not in by_pack:
                continue
            ls.append("[%s] /SKILL-%s.md" % (pack, pack))
            for name, path, purpose in by_pack[pack]:
                t = tier(path).split()[0]
                ls.append("%s  %s  %s  %s" % (name, path, t, purpose)
                          if with_purpose else "%s  %s  %s"
                          % (name, path, t))
        return "\n".join(ls) + "\n"

    body = render(True, None)
    if len(body.encode()) > 8800:
        # b106 elagage MESURE (consigne b105 « le manifest a encore
        # 3 octets — la prochaine fusion de tete est a prevoir ») :
        # la ligne NOTE du dense-fold est FUSIONNEE dans la tete —
        # le drapeau « folded to dense mode » vit (test_bundle0 le
        # lit), les deux pointeurs de purpose vivent, 217 lignes.
        body = render(False, None)
        ls = body.split("\n")
        ls[0] += (" | dense fold (<8.8KB): /route?q= or "
                  "/tools/<name>.json")
        body = "\n".join(ls)
    return body + "# sha256=" + _sha(body.rstrip("\n")) + "\n"


def tool_spec(name, mcp_schema):
    row = next(t for t in TABLE if t[0] == name)
    out = {"tool": name, "path": row[1], "tier": tier(row[1]),
           "pack": row[2], "purpose": row[3], "schema": mcp_schema,
           "manifest": "GET /agent/manifest"}
    out["sha256"] = _canon(out)
    return out


PACK_NOTES = {
    "core": "the trio that came early: charts, reshaping, schema validation",
    "repair": "dirty data in, contract-clean data out",
    "code": "edits, diffs, paths, globs, env — the agent's workbench",
    "dates": "parse, timezones with DST, cron, ICS — no model math",
    "numbers": "exact numbers, units, money, amounts in words — for "
               "multi-step math never solve in one shot: POST "
               "{\"expr\": \"<op>\"} to /api/v1/math/calc one "
               "operation at a time and quote the value it returns",
    "web": "artifacts of the wire: keys and archives verified in memory, "
           "nothing extracted, nothing written",
    "time": "calendars of work: interval algebra and cron semantics — "
            "the clock is always an argument, never a surprise",
    "identity": "hashes, encodings, JWT, UUID, slugs, fingerprints",
    "checks": "closed-rule gates, named refusals — and the verdict trio: "
               "do payloads agree, does the draft cross a redline, do the "
               "cited refs exist in the source",
    "text": "counts, sorting, case, regex, chunking, markdown, scraping",
    "design": "deterministic palettes: one seed, forever",
    "extract": "Recall by construction: the scan cannot lose a fact, "
               "and selection is coverage arithmetic, not vibes.",
    "logic": "The model decides what to check; the grammar decides what it "
             "means — every rule emits a trace.",
}


def pack_markdown(pack, mcp_tools):
    if pack not in PACKS:
        return None
    by_name = {t["name"]: t for t in mcp_tools}
    lines = [
        "# Mechacut skill pack: %s" % pack,
        "",
        "%s. Stateless POST at mechacut.studio, no key, no account."
        % PACK_NOTES[pack],
        "Responses carry sha256; 400s carry field+expected.",
        "Tiers: free=keyless; cap=free under 32 KB then x402; "
        "paid=x402 per call.",
        "",
    ]
    for name, path, pk, purpose, _tags in TABLE:
        if pk != pack:
            continue
        sch = by_name.get(name, {})
        props = list(sch.get("inputSchema", {}).get("properties", {}))
        req = sch.get("inputSchema", {}).get("required", [])
        params = ", ".join(p + ("*" if p in req else "") for p in props)
        lines.append("## %s — POST %s  (%s)" % (name, path, tier(path)))
        lines.append("`{%s}` -> %s" % (params, purpose))
        lines.append("")
    lines.append("# sha256=%s" % _sha("\n".join(lines)))
    return "\n".join(lines) + "\n"


# ------------------------------------------------------- B0.8 task router
#
# Bundle 70 (2026-11-23) — T6, né du radar comme T5 est né de B003.
# La loi T5 (« un leurreur peut glisser UN mot, pas deux familles »)
# protégeait la grammaire fermée de /router/apply ; /route restait
# monolingue EN alors que les mots FR/PT entraient dans PURPOSES et
# TAGS par v1.1.0. Résultat mesuré (docs/RADAR, scans 22h42→03h31,
# 3 OVERMATCH persistants) : le routeur prescrivait sur des mots de
# GRAMMAIRE seuls — matched ["moi","sur","les","de"],
# ["ne","pas","que","en"], ["pui","la","le","les"] — et une requête
# PT morte se voyait prescrire money_baggage sur ["de","40"].
# Mêmes classes de douleur documentées ailleurs : laya #1453
# (stopwords pt/es/fr/it partagés déplacent le routage), README
# llm-router-plugins (« a big model chosen for a one-word greeting
# because none is never reached »), autonomous-dev (« update the
# README » → IMPLEMENT), 9router #317 (keyword lists monolingues =
# faux positifs).
#
# DEUX règles fermées, aucune n'invente quoi que ce soit :
#  1. STOP × 3 langues, testée sur le token BRUT avant _stem — la
#     raison est une collision mesurée : _stem("mois") == "moi",
#     donc stopper la tige tuerait le vrai signal FR des dates avec
#     le pronom. Stopper la forme brute ne tue que la grammaire.
#     (Le token arrive déjà plié par le splitter : "après" -> "apr",
#     "très" -> "tr", "où" -> "o" — les variantes accentuées sont
#     couvertes sous leur forme réelle.)
#  2. CONF_FLOOR = 4, le plancher publié dans la réponse /route :
#     sous 4, AUCUN outil n'est listé — le serveur refuse par le nom
#     au lieu de prescrire du bruit. Le 4 n'est pas un nombre réglé
#     à la main sur le corpus : c'est le POIDS DU NOM. Un mot incidentel
#     vaut au plus 3 (tag) ou 2 (purpose) — jamais le plancher ; un mot
#     qui EST le nom de l'outil (« chart », « csv », « batch ») vaut 4
#     et survit seul, parce que nommer n'est pas glisser. Les poids
#     4/3/2 restent INTACTS : ils portent la marge d'égalité de T5 dans
#     les intent cards (test_bundle21) et le golden intent_card_round —
#     les changer a été essayé et rejeté par le banc lui-même.

STOP_EN = frozenset("a an and do for from in into is it make my of on or "
                    "please that the this to turn with".split())

# Grammaire française fermée — pronoms, articles, prépositions,
# conjonctions, modaux. Volontairement ABSENTS (ce sont des signaux) :
# "est" (fuseau EST), "temps" (dates), "combien" (quantité),
# "mois" dérivé, "avant/apres" de crossover restent testés bruts.
STOP_FR = frozenset(
    "le la les un une des du de l au aux en dans sur sous chez vers "
    "avec sans pour par depuis avant apr apres et ou ni mais donc car "
    "si que qui quoi dont o quand comment ne pas rien personne jamais "
    "jusqu plus moins tres tr tout tous toute toutes autre autres "
    "mon ma mes ton ta tes son sa ses notre nos votre vos leur leurs "
    "je tu il elle on nous vous ils elles me te moi toi se soi y "
    "ce cet cette ces "
    "peut peux peuvent veux veut vouloir voulais "
    "fais fait faire dis dit dire suis es etes etre avoir ont eu "
    "dois doivent ici".split())

# Grammaire portugaise fermée — mêmes familles de mots.
STOP_PT = frozenset(
    "o os as um uma uns umas de do da das dos dum em no na nos nas "
    "num numa por para sem sob sobre e ou mas porque quando como que "
    "quem qual quais nao sim tambem tamb ja meu minha meus minhas "
    "teu tua teus suas seu sua nossos nossas voce voces ele ela elas "
    "isto isso aquilo aqui ali se me te lhe vos muito "
    "esta estao estava foram ser sao tem tenho queria fazer faz ao".split())

STOP = STOP_EN | STOP_FR | STOP_PT

# T6 — le plancher de confiance publié dans la réponse /route.
CONF_FLOOR = 4

# T7 — le pli d'écriture (bundle 95, douleur mesurée en prod le
# 23-nov-2026) : la requête est tokenisée en minuscules ASCII ; sans
# pli, « barré » éclate en « barr » (le é est un séparateur), « légal »
# en « l »+« gal », et 84 mots de tags accentés + les tags à majuscules
# (RFC, CJEU, kWh…) ne répondent JAMAIS à leur propre spelling. Le pli
# est des deux côtés — requête ET table — sinon « impayé » plié ne
# matche plus le tag brut « impayé » : NFKD + retrait des combining
# marks (stdlib, fermé, idempotent) + les caractères latins que NFKD
# ne décompose PAS (œ æ ø đ ð ß et leurs doubles de casse — table
# close ci-dessous, testée) + minuscules. Mêmes octets d'entrée,
# mêmes octets de sortie, pour toujours.
_TRIT = str.maketrans({"œ": "oe", "æ": "ae", "ß": "ss", "ø": "o",
                       "đ": "d", "ð": "d",
                       "Œ": "oe", "Æ": "ae", "ẞ": "ss", "Ø": "o",
                       "Đ": "d", "Ð": "d"})


def _nw(w):
    """Normalized word: fold accents, transliterate the five NFKD
    holdouts, lowercase. Deterministic; idempotent by construction."""
    w = w.translate(_TRIT)
    return "".join(c for c in unicodedata.normalize("NFKD", w)
                   if not unicodedata.combining(c)).lower()


def _stem(w):
    """Tiny closed suffix-stripper: deterministic, no tables, no ML."""
    if len(w) > 5 and w.endswith("ing"):
        return w[:-3]
    if len(w) > 4 and w.endswith("ed"):
        return w[:-2]
    if len(w) > 4 and w.endswith("es"):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def route(query, top=5):
    toks, seen = [], set()
    # FORME FERMÉE b98 — « blague / joke / piada » est un NOM de
    # requête méta : mechacut ne produit AUCUNE blague, donc toute
    # requête qui le contient est un NO_MATCH juré, quels que soient
    # ses mots de contenu. Douleur pêchée CE cycle par mon propre
    # leurre de corpus : « blague sur les retours de Noël » ROUTAIT
    # (poids retour+noël > plancher T6 depuis l'extension FR b98) —
    # un leurre qui route = promesse fausse. La classe EN « tell me
    # a joke about X » (file n°7, ssh_fingerprint OVERMATCH) meurt
    # par la MÊME règle, en trois langues, sans verbes ni LM.
    joke = False
    # CLASSE b100 — veto de JURIDICTION NOMMÉE : un outil dont le NOM
    # déclare une juridiction (« _uk ») ne doit JAMAIS être routé par
    # une requête qui en nomme une AUTRE. Douleur OVERMATCH pêchée
    # AVANT push par mes propres leurres : « combien de temps garder
    # mes factures en France » et « as notas fiscais brasileiras
    # quanto tempo guardar » routaient money_keep_records_uk — une
    # promesse fausse (le module refuse la France et le Brésil PAR
    # NOM, mais le routeur, lui, avait déjà promis). Liste fermée,
    # zéro LM ; la requête honnête passe par le token UK (« HMRC »,
    # « Royaume-Uni », « limited company ») et reste admise ; sans
    # lui, elle meurt en NO_MATCH CONSIGNÉ à la file (la douleur
    # réelle FR est un futur outil, pas un prêt).
    FOREIGN = ("france", "francais", "francaise", "frances", "french",
               "brasil", "brasileira", "brasileiro", "alemanha",
               "germany", "deutschland", "espana", "espanha",
               "italia", "italy", "quebec")
    foreign = False
    # CLASSE b102 — veto IN-TABLE : /shop/gift-voucher answerne
    # IRLANDE et FRANCE (seules rejouées) — un pays HORS table nommé
    # SANS ancre de la table ne doit pas prescrire l'outil : le
    # module répondrait par un refus et le routeur aurait déjà promis
    # (la leçon b100 rejouée à l'envers). Irlande DU NORD = UK, pas
    # la République — l'ancre « irland* » voisine de « nord » est
    # annulée NOMMÉE, liste fermée, zéro LM. Le pronom anglais « us »
    # n'est PAS dans le vocabulaire : un mot trop courant tuerait
    # des requêtes honnêtes (faute b81 des tags-« 1 »). RACINES, pas
    # mots entiers — « irlandês », « française », « brasileria »
    # passent tous les filets (« brit* » attrape britain/british).
    V_OUT = ("brasil", "brazil", "usa", "united", "state", "etats",
             "unis", "america", "amerique", "england", "angleterre",
             "scotland", "ecoss", "australia", "australie", "japan",
             "japon", "china", "chine", "canada", "espan", "portug",
             "angola", "mozambic", "mexic", "russie", "russia",
             "brit", "german", "deutsch",
             # b108 — l'Allemagne nommée dans nos trois langues de
             # surface manquait au veto : la classe « ville nomme la
             # juridiction » (b102) avait son trou pays. Une RACINE
             # rend l'adjectif et le pays : « allemande », « Alemania »,
             # « Alemanha » — le trou « rétractation allemande » datait
             # la France sur une question d'Allemagne. « allemagne »
             # (le nom FR) ne partage pas la racine : il voyage avec —
             # comme l'adjectif français à deux L, « allemande » — il
             # ne partage AUCUNE racine avec « aleman » (a-l-l-e contre
             # a-l-e) : chaque graphie voyage par son nom.
             "aleman", "allemagne", "allemand",
             # villes ANGLAISES — « it expired in London » nomme la
             # juridiction sans le mot « UK » (pêché par mon propre
             # leurre b102 : London routait l'outil)
             "london", "londres", "belfast", "manchester", "york",
             "glasgow", "edinburgh", "cardiff")
    V_OUT_EXACT = {"uk", "gb", "wales"}
    V_IN_P = ("irland", "franc")  # france/francais/irish-irlandaise
    V_IN = {"ie", "fr", "irl", "eire", "dublin", "ccpc", "paris",
            "cork", "galway"}
    # CLASSE b103 — veto IN-TABLE pour /shop/soldes-window : la table
    # ne rejoue que l'arrêté FRANÇAIS du 27 mai 2019. Une requête qui
    # nomme un autre calendrier (Belgique, Luxembourg, Suisse,
    # Québec, UK, US, Portugal, Brésil…) ne doit PAS prescrire cet
    # outil : le module répondrait un refus 400 et le routeur aurait
    # déjà promis (leçon b100/b102 rejouée). RACINES + villes des
    # juridictions étrangères, liste close, zéro LM. « france » et
    # les territoires d'outre-mer N'ENTRENT PAS ici : ils sont la
    # table.
    V_SOLD_OUT = ("belg", "luxemb", "suiss", "quebe", "canad",
                  "ontario", "royaume", "united", "etats",
                  "angleterre", "england", "brit", "irlande",
                  "irlandais", "espag", "portug", "brasil",
                  "brazil", "bresil", "italia", "deutsch",
                  "german", "mexique", "maroc", "algerie",
                  "tunisie", "senegal", "montreal", "bruxell",
                  "genev", "zurich", "amsterdam", "berlin",
                  "madrid", "lisbon", "dublin")
    V_SOLD_EXACT = {"uk", "gb", "usa", "ie"}
    # CLASSE b109 — veto DROIT-FENÊTRE. Deux OVERMATCH pêchés par mon
    # propre radar (scans 06h13 et 07h44, suivis, jamais niés) :
    # « retour brésil 7 jours arrependimento prazo » routait
    # shop_return_deadline (score 6, retour+prazo) — la table ne
    # joue QUE les marchés publiés US/UK/FR ; nommer le Brésil (ou
    # son droit : « arrependimento » = CDC art. 49, sept jours,
    # AUTRE horloge) ne doit rien prescrire. « withdrawal germany
    # online order deadline » routait shop_shipping_deadline (score
    # 4, le « deadline » de purpose) — sa table est USPS/UPS/FEDEX,
    # nommer l'Allemagne (ou tout territoire hors table) la tue.
    # Le module sait refuser par nom ; c'est le ROUTEUR qu'on
    # dresse (leçon b100/b102/b103, même classe, deux tables neuves).
    # RACINES fermées ; les pays DÉJÀ dans la table n'y entrent pas
    # (US/UK/FR vivent pour return-deadline, US seul pour shipping).
    V_RTN_OUT = ("brasil", "brazil", "brasileir", "arrepend",
                 "german", "deutsch", "aleman", "allemagne",
                 "allemand", "italia", "italie", "espag", "portug",
                 "angola", "mozambic", "japan", "japon", "china",
                 "chine", "korea", "coree", "bresil", "australie",
                 "australia", "mexic", "canad", "quebe", "ontario",
                 "russie", "russia", "maroc", "algerie", "tunisie",
                 "senegal", "suede", "norve", "belg", "luxemb",
                 "suiss", "irlande", "irlandais", "dublin",
                 "amsterdam", "berlin", "tokyo", "madrid", "lisbon",
                 "sydney", "montreal")
    # EXACTS : « india » ne peut pas être une RACINE — Indiana est
    # un État US et la table retour le joue ( Walmart retourne en
    # Indiana comme partout US ). Idem pour aucun mot de la liste
    # ci-dessus qui ne coupe un toponyme américain.
    V_RTN_EXACT = {"india"}
    # V_SHIP_OUT : la table shipping est US SEULE — les mots US n'y
    # entrent évidemment pas (tuer « ship to the United States by
    # Christmas » serait une régression d'honnête, leçon b81 des
    # mots trop courants rejouée à l'envers). Entrent : UK, FR et
    # tout le reste de V_RTN_OUT. PAS de villes FR/UK : « paris »
    # est aussi une ville du Texas, « london » aussi une ville de
    # l'Ontario — les mots ANGLAIS/FR « brit/england/france »
    # portent la juridiction sans ces pièges (leçon V_RTN_EXACT).
    V_SHIP_OUT = V_RTN_OUT + ("royaume", "england", "angleterre",
                              "scotland", "ecoss", "wales", "brit",
                              "uk", "france", "francais", "francaise",
                              "frances", "french")
    vrtout = vshipout = False
    # CLASSE b105 — la Belgique a SON outil (/shop/soldes-be) : les
    # mots belges tuent toujours la fenetre FR (vsoldes_out, rien ne
    # change pour elle) mais ne tuent plus l'outil BE ; a l'envers,
    # nommer la France (vtabled) ou tout autre calendrier (vsoldes_out)
    # sans mot belge ne doit JAMAIS prescrire l'outil BE — le module
    # repondrait un 400 et le routeur aurait promis (lecon b100/102/103).
    # RACINES fermees, zero LM. « be » seul n'y entre pas : c'est un
    # verbe anglais, la lecon des stopwords b98.
    V_BE = ("belg", "bruxel", "brussel", "solden", "opruiming",
            "schlus")
    vforeign = vtabled = vnord = vsoldes_out = vbename = False
    viirish = vfr = False
    vlux = vbelg = False
    for t in re.split(r"[^a-z0-9]+", _nw(query or "")):
        if t in ("blague", "blagues", "joke", "jokes", "piada",
                 "piadas"):
            joke = True
        if not t or t in STOP:
            continue
        # CLASSE b81 : un chiffre dans une requête est une DONNÉE,
        # jamais une intention — il ne vote pour aucune ligne. La
        # maladie des tags-« 1 »/« 50 » (dictée FR b78, 8-7 chez
        # csv_excel_display) est guérie à la SOURCE, pas phrase par
        # phrase. test_bundle81 la verrouille statiquement.
        if t.isdigit():
            continue
        if t in FOREIGN or _stem(t) in FOREIGN:
            foreign = True
        if t.startswith(V_OUT) or t in V_OUT_EXACT:
            vforeign = True
        # b109 — deux orthographes du Brésil manquaient aux deux
        # filets : « bresil » (FR) et « brazil » (EN) n'étaient pas
        # dans FOREIGN, « arrependimento » (le DROIT nommé, CDC 49)
        # ne tuait pas la ligne withdrawal. Racines fermées, chaque
        # graphie voyage par son nom (leçon b108 rejouée).
        if t.startswith(("bresil", "arrepend")) or t in ("brazil",):
            vforeign = True
        if t.startswith(V_RTN_OUT) or t in V_RTN_EXACT:
            vrtout = True
        if t.startswith(V_SHIP_OUT):
            vshipout = True
        if t.startswith(V_IN_P) or t in V_IN:
            vtabled = True
        if t.startswith(V_SOLD_OUT) or t in V_SOLD_EXACT:
            vsoldes_out = True
        if t.startswith(V_BE):
            vbename = True
        if t == "nord":
            vnord = True
        # b107 — la rétractation était la loi française seule : toute
        # juridiction NOMMÉE autre tuait la ligne. b108 — LU (L. 221-3/
        # L. 222-9) et BE (VI.47-VI.53 + C. civ. I.7) sont rejouées
        # AUSSI : un Luxembourg ou une Belgique nommés laissent vivre
        # la ligne (c'est LEURS grammaires qu'ils demandent) ; tout
        # autre pays nommé la tue toujours avant qu'elle ne promette.
        # Irlande entre par V_IN (gift-voucher) : elle a ICI son drapeau.
        if t.startswith(("irland",)) or t in ("ie", "irl", "eire",
                                              "dublin", "cork",
                                              "galway", "ccpc"):
            viirish = True
        if t.startswith("franc") or t in ("fr", "paris"):
            vfr = True
        if t.startswith(("luxemb", "lëtzebuerg")) or t in (
                "lux", "esch", "wiltz", "diekirch", "grevenmacher",
                "vianden", "clervaux", "grand-duche", "groussherzogtum"):
            vlux = True
        if t.startswith(("belg",)) or t in (
                "brussel", "bruxelles", "antwerpen", "antwerp", "gent",
                "ghent", "liege", "liège", "namur", "bruges", "brugge",
                "leuven", "louvain", "charleroi", "wallonie", "brabant"):
            vbelg = True
        st = _stem(t)
        if st not in seen:
            seen.add(st)
            toks.append(st)
    if joke:
        return []
    voucher_ok = vtabled and not vnord
    scored = []
    for idx, (name, path, pack, purpose, tags) in enumerate(TABLE):
        if foreign and name.endswith("_uk"):
            continue
        if name == "shop_gift_voucher" and (vforeign or vnord) \
                and not voucher_ok:
            continue
        if name == "shop_soldes_window" and vsoldes_out:
            continue
        # CLASSE b109 — veto DROIT-FENÊTRE sur les deux tables
        # américaines (radar 06h13/07h44, pêchés, suivis, réparés).
        if name == "shop_return_deadline" and vrtout:
            continue
        if name == "shop_shipping_deadline" and vshipout:
            continue
        if name == "shop_soldes_be" and (vsoldes_out or vtabled) \
                and not vbename:
            continue
        # CLASSE b110 — le Luxembourg a SON outil : destination des
        # refus NOMMÉS des deux sœurs (vetos b103/b105 tenus — le
        # relai promettait, voici la table). Un calendrier nommé SANS
        # mot luxembourgeois tue la ligne LU (le module répondrait un
        # 400 et le routeur aurait promis — leçon b100/b102) ;
        # « luxemburgo » vote par la MÊME racine « luxemb » du
        # drapeau vlux — la douleur PT pêchée par la sonde du lot
        # (« saldos luxemburgo datas » routait chart_from_data, le
        # stem « datas »→« data ») meurt guérie : la table LU score
        # saldos+luxemburgo+datas et repasse devant. Les mots belges
        # tuent LU, les mots LU tuent BE et window — chaque table ne
        # joue que chez elle, et « soldes 2027 » sans pays continue de
        # vivre pour les trois : c'est la demande qui les sépare, pas
        # le routeur qui devine.
        if name == "shop_soldes_lu" and (vsoldes_out or vtabled
                or vbename) and not vlux:
            continue
        # b110 LEÇON PÊCHÉE PAR MON PROPRE RADAR À LA FERMETURE : la
        # première table des tags portait « quand commencent » et les
        # mois (janvier|juin|juillet|x) — 6 points volés sur une
        # phrase SANS PAYS : « les soldes d'été 2027 débutent-ils le
        # 23 ou le 30 juin » (ligne b103 du radar, want window)
        # tombait TOP1_WRONG vers LU. La frontière jurée b105 ne vit
        # que si les mots COMMUNS ne surclasse aucune table : les
        # mois et les verbes d'ouverture restent chez window et be
        # (leurs tags n'ont jamais porté « quand commencent ») ; la
        # ligne LU ne garde que ses noms propres. Radar de fermeture
        # rejoué APRES la correction — c'est lui qui l'a trouvée,
        # jamais la batterie : l'outillage ment le moins sur son
        # propre travail (playbook §outillage).
        # b108 — LU et BE sont rejouées : nommées, elles laissent la
        # ligne VIVRE (le veto ne survit que pour les pays SANS table).
        # Un pays de V_SOLD_OUT qui n'est NI LU NI BE (Suisse, Québec,
        # Canada…) continue de tuer — pas de grammaire, pas de promesse.
        if name == "shop_withdrawal" and (
                vforeign or viirish or
                (vsoldes_out and not (vlux or vbelg))) \
                and not (vfr or vlux or vbelg):
            continue
        tail = path[len("/api/v1/"):]
        # nsegs STEMÉS comme les tags et le query — sinon un nom au
        # pluriel ne matche jamais JAMAIS son propre mot (bug pêché
        # par food_leftovers, bundle 71 : stem("leftovers") =
        # "leftover" != "leftovers").
        nsegs = set(filter(None, (_stem(_nw(x)) for x in name.split("_"))))
        nsegs |= set(filter(None, (_stem(_nw(x)) for x in
                                   re.split(r"[/_-]+", tail))))
        tagset = set(filter(None, (_stem(_nw(x)) for x in tags.split())))
        pwords = set(filter(None, (_stem(_nw(x)) for x in
                                   re.split(r"[^a-z0-9]+",
                                            purpose.lower()))))
        score, matched = 0, []
        for st in toks:
            if st in nsegs:
                w = 4
            elif st in tagset:
                w = 3
            elif st in pwords:
                w = 2
            else:
                w = 0
            if w:
                score += w
                matched.append(st)
        if score >= CONF_FLOOR:
            scored.append((-score, idx, name, path, pack, purpose,
                           score, matched))
    scored.sort()
    return [{"tool": n, "path": pth, "pack": k, "purpose": u,
             "tier": tier(pth), "score": s, "matched": m}
            for _n, _i, n, pth, k, u, s, m in scored[:top]]


# -------------------------------------------------------- B0.9 family rail
# Mechacut does data mechanics. Storyboards are the sister product's job:
# a bot that asks here for shots gets pointed at moovicut.studio, politely
# and deterministically — the tools array is untouched, the rail is added.
_STORY_WORDS = "storyboard storyboarding shot shots shotlist shotlists " \
               "scene scenes previz"
STORY_TERMS = frozenset(_stem(w) for w in _STORY_WORDS.split())


def elsewhere(query):
    """Sister-product pointer for media-shaped tasks: [] or one entry."""
    toks = set()
    for t in re.split(r"[^a-z0-9]+", _nw(query or "")):
        if t:
            toks.add(_stem(t))
    if toks & STORY_TERMS:
        return [{"product": "moovicut",
                 "url": "https://moovicut.studio",
                 "why": "storyboards, shot lists, scene breakdowns: "
                        "deterministic storyboarding lives next door"}]
    return []
