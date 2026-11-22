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
     "holidays deadline months clamp age later echeance"),
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
     "desconto promoção desconto em cascata"),
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
     "occupancy occurrences calendar series expand rfc 5545 dtstart "
     "until count byday wkst recurrente qui se repete un mardi sur "
     "deux tous les quinze jours derouler recurrence dates de serie "
     "recorrencia se repete a cada duas semanas quinzenal expandir"),
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
     "eur250 400 600 gbp220 350 520 claim deadline refund air passenger "
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
     "semaine iso semaine 53 calendrier kw kalenderwoche woche wochenzahl "
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
     "ics calendar validate lint vevent dtstart dtend RFC 5545 "
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
     "cron schedule recurring timer expressaoScheduler agendador "
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
     " array of objects batch style"),
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
     "97 bancaire"),
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
     "truncate cut limit text length boundary ellipsis words 280 shorten "
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
     "remaining stock shop inventory sold of the rest du reste "
     "afternoon pourcentage apres-midi combien restent il reste "
     "quantite restante vendas restantes restando depois"),
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
     "formula,rule of three,dilution,dosage,naegle,due date,"
     "hydration,bakers percentage,percentage of total,vitesse,"
     "temps distance vitesse,consommation carburant,règle de trois,"
     "date de naissance prévue,hydratation levain,pourcentage"),
    ("intent_reflect", "/api/v1/intent/reflect", "core",
     "le miroir de compréhension : tu déclares ta lecture (formule + "
     "args), la machine te la rend écrite et exacte avant que tu la "
     "prennes pour la vérité",
     "comprehension,reading check,word problem,énoncé,comprendre,"
     "vérifier ma lecture,j'ai mal compris,misread"),
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
     "Ã©chapper echapper injection protege requete"),
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
     "cabin baggage carry on size 40x30x15 underseat personal item "
     "hand luggage allowance does my bag fit suitcase sizer gauge "
     "rotation overhead new eu rule 2027 air passenger voyage sac "
     "bagage cabine dimensions franchie main valise sous le siège "
     "règle ue 2027 bagagem de mão malas de mão dimensões cabine "
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
     "names postcode truncation 15 digits import text columns "
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
     "assinatura mensalidade taxa de adesão"),
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
     "budget cell shows extractor misled mise en forme affichée "
     "valeur stockée rendu format nombre affichage cellule styles "
     "xml visual formato número exibido célula render estilo de "
     "número valor estocado"),
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
        "mechacut.studio %s — %d deterministic transforms "
        "+ %d named recipes." %
        (version,
         sum(1 for e in TABLE if not e[0].startswith("recipe_")),
         sum(1 for e in TABLE if e[0].startswith("recipe_"))),
        "tiers: free=keyless 30/min; cap=free under 32KB then x402; "
        "paid=x402 from call one.",
        "every POST response carries sha256; every 400 carries "
        "field+expected+example — the error is the repair prompt.",
        "detail on demand: GET /tools/<name>.json | "
        "install one pack: GET /SKILL-<pack>.md | "
        "one-call pipelines: GET /api/v1/recipes or POST /api/v1/pipeline | "
        'find tools: GET /route?q="your task words"',
        "not here: storyboards, shot lists, scene breakdowns "
        "-> sister product moovicut.studio",
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
            ls.append("")
            ls.append("[%s]  /SKILL-%s.md" % (pack, pack))
            for name, path, purpose in by_pack[pack]:
                t = tier(path).split()[0]
                ls.append("%s  %s  %s  %s" % (name, path, t, purpose)
                          if with_purpose else "%s  %s  %s"
                          % (name, path, t))
        return "\n".join(ls) + "\n"

    body = render(True, None)
    if len(body.encode()) > 8800:
        body = render(False, "NOTE: folded to dense mode (portability "
                             "budget <8.8KB); purpose: /route?q= or "
                             "/tools/<name>.json")
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
               "{\"step\": \"<expr>\"} to /api/v1/math/calc one "
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
        "Responses carry sha256; 400s carry field+expected+example.",
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

STOP = frozenset("a an and do for from in into is it make my of on or "
                 "please that the this to turn with".split())


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
    for t in re.split(r"[^a-z0-9]+", (query or "").lower()):
        if not t or t in STOP:
            continue
        st = _stem(t)
        if st not in seen:
            seen.add(st)
            toks.append(st)
    scored = []
    for idx, (name, path, pack, purpose, tags) in enumerate(TABLE):
        tail = path[len("/api/v1/"):]
        nsegs = set(name.split("_")) | set(re.split(r"[/_-]+", tail))
        tagset = set(filter(None, (_stem(x) for x in tags.split())))
        pwords = set(filter(None, (_stem(x) for x in
                                   re.split(r"[^a-z0-9]+", purpose.lower()))))
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
        if score:
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
    for t in re.split(r"[^a-z0-9]+", (query or "").lower()):
        if t:
            toks.add(_stem(t))
    if toks & STORY_TERMS:
        return [{"product": "moovicut",
                 "url": "https://moovicut.studio",
                 "why": "storyboards, shot lists, scene breakdowns: "
                        "deterministic storyboarding lives next door"}]
    return []
