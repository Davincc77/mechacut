# MechaCut

Deterministic mechanical tools for AI agents — the machine that answers
**the same bytes to the same request, forever**. One stateless API, an MCP
endpoint, x402 USDC micropayments on Base, and zero storage of what you send.

**Live catalog: [mechacut.studio/agent/manifest](https://mechacut.studio/agent/manifest)**
— 147 transforms + 9 named recipes as of v0.94.0, each with its tool card
(`/tools/<name>.json`: schema, price, a human sentence in EN/FR/PT, and the
server's real captured answer). Weak model? Start at
[`/SKILL-MINI.md`](https://mechacut.studio/SKILL-MINI.md) — a 2.6 KB manual
written to be followed literally by a 0.5B. Prove-the-determinism checklist:
[`/integrity.json`](https://mechacut.studio/integrity.json) — 209 replayable
golden pins.

The list below is the historical build log (bundle by bundle); the manifest
is the truth of today. Recent highlights: `agent/modelid` (static audit of
your agent's model-id strings against a pasted catalog: closed grammar
`org/name[:variant|#variant]`, named verdicts — PREFIX_KEPT, NO_ORG,
CASE_DRIFT, PUNCT_DRIFT, VARIANT_DECOR — did-you-mean at a NAMED
Levenshtein≤3 threshold, and the response itself swears that OK certifies
shape, never that the GET answers: the V23 incident, written as doctrine
into the bytes); `money/unitprice` (unit price and shrinkflation with
the DENOMINATOR NAMED: 32→28 fl oz at the same sticker is −12.5% of
product but +14.2857% per ounce — 1/7, never one headline number;
"two-for-$7" of 15 oz jars pays 40.3509% MORE per ounce than the big
single jar; "1 lb 4 oz" parses to exactly 20 oz; and the store's own
per-unit tag is AUDITED at its printed precision — r/LifeProTips
"Walmart got the math wrong" becomes a named TAG_WRONG. Building it
caught and fixed a ×10/×100 exponent bug in the site's own US volume
table, floz_us/qt_us/pt_us/cup_us, NIST SP 811 anchors, regression-
pinned); `money/bogo` (what a
"buy one get one 50% off" sign REALLY bills: the percent lands on the
CHEAPER item of each pair — published retail rule — so $60+$40 pays 80
of 100 = 20.0000%, neither 25 nor 50; equal prices give 25% on the pair,
never 50; the odd item pays FULL because pairs are GIVEN, never guessed;
a −30% coupon stacks as FACTORS — 25 then 30 = 47.5%, never 55 — with
the per-pair expression and the exact fraction beside the 4-dp display);
`ship/dimweight` (what a
parcel is actually BILLED, one step per rounding: two published
calculators print 35 and 34.5 on the SAME 20×20×12 inches — the exact
value 4800/139 = 34.5323741007 settles it; gates (>1 ft³), ceilings
(70 lb) and divisors are ARGUMENTS with as_of — carrier tables rot,
USPS moved 166→139 on 2026-07-12 — and the declared divisor unit makes
the published mm-into-139 trap structurally impossible);
`json/coerce` (the tool-call arguments a strict reader rejects:
models write `limit` 8.0, serde expects u64 and drops the WHOLE call;
the published magpie grammar repairs whole floats to integer
notation, leaves exponents and real fractions AS WRITTEN — and
re-emits them exactly, notation is data — refuses quoted `"false"` by
name, casts strings only on declaration, and never touches `007`);
`date/tz_anchor` (one wall
clock, two clocks reading it — six production bugs measured in November
2026 share the shape: a naive timestamp written against the job's zone,
anchored by a UTC box; every candidate instant, the drift SIGNED in
minutes, both wall clocks read back, the offset-wins arbitration Composio
published, and the PraisonAI "offset in force NOW" fix-bug replayed by
name); `money/points` (what a reward point is actually worth: cpp =
(cash − taxes − forgone) ÷ points × 100 in an EXACT fraction — the web
prints 1.49 where 1081/725 = 1.491034… lives, paths ranked side by side
against YOUR supplied floor, never an embedded valuation table);
`money/crossover` (two tariffs
with a unit rate and a recurring fixed: the web's seven published
calculators all ROUND THE FIXED DELTA FIRST and contradict each other —
4,623 where the exact answer is 4,623⅓ kWh; here the crossover ships as
an exact fraction, the day convention is NAMED (×12 for monthly, never
30-day months), and a plan that wins on both components gets the honest
verdict "never"); `csv/excel_display` (what Excel DISPLAYS from a stored
value under a numFmt code — arXiv 2611.05806 measured it: '$#,##0,'
turns 1,000,000 into $1,000 and six python extractors never said so);
`money/baggage` (cabin-baggage
verdict keyed by the FLIGHT DATE — Regulation (EU) 2026/2202 applies only
FROM 2027-10-23 and until then no EU size rule exists at all; from it,
exactly one legal edge: the 40×30×15 under-seat item must ride FREE, while
the regulation sets NO size for the overhead bag and NO weight for the
personal item — where law is silent the answer says silent. Carrier
gauges are supplied arguments, never fetched; fit is compared per
dimension WITH rotation, so 40×18×30 passes a 40×30×20 gauge that raw
order fails; the press "100 cm combined + 7 kg" reading is returned as a
tested claim — the standard 55×40×20 trolley sums to 115 cm — never as
law), `csv/excel_damage` (what Excel will SILENTLY DESTROY in your CSV
before you double-click it, per column, replaying published vectors:
02134→2134, 4111111111111111→4111111111111110, 987654321098765432→
9.87654E+17, 1E5→100000, SEPT2 and MARCH1 coerced to dates, "3-4" is
March 4 under en and April 3 under eu — same cell, two dates, so locale
is an argument and the implied year is frozen by as_of; rules named by
Microsoft's own three Automatic Data Conversion toggles, the import mode
prescribed, the unrecoverability stated), `money/flight_comp` (flight
compensation keyed by the FLIGHT DATE, because Regulation (EU) 2026/2202
applies only FROM 2027-10-23 and the press conflated the two dates —
identical facts either side of that line pay DIFFERENTLY: the new Art.
6(4) threshold is "EXCEEDING three hours", so exactly 180 min does not
pay, while the old case-law threshold "at least 3 hours" did; bands EUR
250/400/600 and GBP 220/350/520 from the official gov.uk rows (including
its under-4h £260 long-haul split), the intra-Union €400 cap named, the
50 %/25 % reductions rendered as what the text literally says — the
carrier MAY reduce, options never silence — and the nine-month claim
deadline returned as an exact date, zero flight fetches, zero legal
promises), `date/week` (ISO 8601 weeks both directions, the %Y-W%V
concatenation trap shown on the requested date — "2027-W53" IS A WEEK
THAT DOES NOT EXIST, proven live, 2027 has 52 weeks; W53 existence by
THEOREM: 53 Thursdays iff Jan-1 Thursday or Wednesday-in-leap-year,
validated against stdlib across a full 400-year cycle = exactly 71 such
years as published; Excel WEEKNUM/%U/%W beside ISO, never chosen for the
caller; and a platform discovery measured while building the oracle —
macOS BSD strftime deviates from POSIX on %U/%W/%V near January, so the
module implements the definition, never the libc call),
`date/tz_ambiguity` (the wall
clock the crontab can never have: one zone + one local time → verdict
`single | fold | gap` — every candidate UTC instant named with offset and
abbreviation, the transition minute and affected window computed live from
the installed IANA tzdata (no embedded table, no fetch), the PEP 495 fold
rule stated out loud, gap neighbours named — the fact that K8s CronJob and
cron 4.4.0 double-ran over in November 2026), `units/shoe_size` (shoe sizes
answered in exact millimetres: published steps as exact fractions —
barleycorn 127/15, Paris point 20/3 — half-size AND third-size grid
candidates printed side by side (Nike 42.5 and adidas 42⅔ for one foot are
both right and said so), cross-system drift as exact numbers (1.8 mm per
step; 4 EU steps never coincide with 3 US steps), the +2 allowance named
(40/3 mm), brand charts declared off-contract — never one confident
number), `net/sri` (W3C integrity attributes from LOCAL octets only, never
fetches: paste-ready tags, attribute style-audit including the
CVE-2026-120423 TAB-separator class, sha1/md5 refused by name,
wrong-length digests caught, @latest/range URLs flagged as planned
outages), `date/recurrence` (an RFC 5545
RRULE expanded into dated occurrences with every trap declared in the
answer — MONTHLY from the 31st DROPS short months and LISTS them, never
moves them; biweekly really skips weeks, the failure class a published
demo scored 4-of-8-wrong on; mixed `MO,2TU` parses per the ABNF where
python-dateutil 4.0.0 reads NO dates; COUNT xor UNTIL, ordinals only where
the RFC allows them, BYSETPOS and friends refused by name; DTSTART anchor
and sync status reported — the rrule.js off-by-one and the dateutil
silent-drop both live in the RFC's UNDEFINED zone, we declare it; wall-clock
expansion per spec, hard cap 500 with truncation named), `formula` +
`intent/reflect` (12 published formulas computed in exact Fractions, and the
comprehension mirror that writes your reading back before arithmetic
excuses it), `table/scale` (the recipe halved:
every line answers THREE times — exact reduced fraction, measurable amount at
its ingredient class's published measuring step, and the percent delta — so
silent rounding is structurally impossible; 5 eggs halved is 2½ = 3 whole or
125 g beaten, stated never guessed, and "pinch" is refused by name),
`table/sql_dump` (CSV/JSON rows
into CREATE TABLE + INSERT where every inferred type comes with its reason
and sample — `'007'` stays TEXT, identifiers outside the closed grammar are
refused by name, quoting is exact per dialect, and the oracle is loading the
sqlite dump back and re-querying the hand-computed rows), `id/checkdigit` (15 published
check-digit schemes — ISBN, EAN/UPC/GTIN, ISSN, ISIN, CUSIP, SEDOL, ABA, LEI,
ORCID, CAS, Verhoeff, Damm — with `generate`, `repair` and `scan`; the point:
a frontier model with no tool gets the check digit wrong ~91 % of the time on
non-memorised identifiers, and we report format ambiguity instead of guessing
it), `money/rates` (ECB official
reference rates + a committed 65-day archive of true published days),
`image/rightsize` (PNG resize in pure stdlib — integer resampling, no float
ever touches a sample), `web/cert` (X.509 lint from PEM, `as_of` argument
makes every verdict replayable), `id/checkdigit` (15 published schemes —
frontier models botch ~91% of unmemorised check digits; ours cites every
spec and reports Bookland ambiguity instead of guessing), `xml/to_json`
(the conversion rules PRINTED in the response; `force_array` kills the
one-item bug), the determinism auditor `/integrity/verify`
(replays any API's published pins), and the intake card (`intent/card`) that
turns vague human words into a gated tool call.

**Core**
- **chart_from_data** — records or CSV + column roles → Vega-Lite spec and PNG
- **reshape_json** — JSON + declarative mapping → reshaped JSON, gated by an
  optional JSON Schema
- **validate_json** — payload + JSON Schema → valid or precise errors

**Bundle 1 — data repair & cleaning**
- **json_repair** — broken JSON (fences, single quotes, comments, bare keys,
  trailing commas, Python literals, JSONL) → parsed + repairs applied
- **json_diff** — two JSON values → sorted changes with RFC 6901 pointers
- **json_patch** — RFC 6902 patch applied, per-operation errors
- **json_canonical** — sorted-keys canonical bytes + exact sha256
- **csv_fix** — dirty CSV → clean CSV + notes (BOM, CRLF, delimiter, ragged rows)
- **csv_types** — column type inference and coercion (int/float/bool/date/…)
- **csv_join** — inner/left/right/outer join of two record tables
- **table_pivot** — pivot (sum/count/mean/min/max/first) and unpivot
- **list_dedupe** — text/url/email-aware dedupe, first occurrence wins
- **format_convert** — json ⇄ yaml ⇄ toml ⇄ csv ⇄ env

**Bundle 2 — code editing**
- **text_patch** — find/replace with an exact-uniqueness gate per edit
- **text_diff** — unified line diff, fixed labels, stats, exact sha256
- **text_apply_diff** — strict unified-diff application (no fuzz)
- **path_normalize** — lexical POSIX normalization + parts (no filesystem)
- **glob_match** — deterministic `**`/`*`/`?` over a list of paths
- **env_interpolate** — `$VAR` / `${VAR:-default}` expansion, missing reported

**Bundle 3 — dates & scheduling**
- **date_parse** — ISO / RFC 2822 / epoch / month-name → canonical fields, order never guessed
- **date_tz** — DST-correct conversions across IANA zones
- **date_calc** — add (month-end clamped), business days, diff, boundaries, age
- **cron_next** — next N fire times, wall-clock semantics, Vixie OR rule
- **cron_humanize** — expression → plain reading + field sets
- **ics_generate** — deterministic RFC 5545 output (CRLF, folded, no clock drift)
- **ics_parse** — VCALENDAR → normalized events

**Bundle 4 — numbers & money**
- **num_format** — closed locale/currency tables, Decimal-based, deterministic bytes
- **num_parse** — human number → canonical decimal; ambiguity refused, not guessed
- **num_round** — banker's or explicit rounding, exact beyond float range
- **units_convert** — closed families, exact rational factors, refusals named
- **money_prorate** — exact fraction before the last rounding (paid)
- **money_split** — cent-exact with a closed remainder rule
- **number_spell** — amounts in words FR/EN/PT, the invoice mention

**Bundle 5 — hashes, encodings & identity**
- **hash_digest** — five algos, strict input kinds (a model cannot hash)
- **enc_base64** — base64/base64url/hex both ways, garbage refused
- **jwt_decode** — claims exposed, `verified: false` stated, never faked
- **id_uuid** — v5, seeded v4, v7 with explicit instant (no wall clock)
- **id_slug** — NFKD transliteration, collapsed separators, bounded cuts
- **fingerprint** — canonical JSON/CSV sha256: the agent's cache key

**Bundle 6 — validators & color**
- **validate_iban** — closed 61-country table, BBAN structure, mod-97 (paid)
- **validate_phone** — any national form in, E.164 + country out
- **validate_email** — structural check + normalized form, no DNS theater
- **validate_url** — components + canonical (IDN→punycode, ports, paths)
- **color_check** — hex/rgb/hsl + WCAG contrast verdicts (AA/AAA)

**Bundle 7 — context & text** (lot 7.1 shipped)
- **text_count** — chars/words/sentences/paragraphs/lines/bytes, exact
- **sort_natural** — file2 before file10 + the permutation itself
- **text_case** — every case convention, both directions
- **text_truncate** — to N units at a real boundary, never mid-word
- **regex_test** — match/spans/groups/replace without touching your own
  process (and a 64 KB ReDoS blast-radius cap)
- **text_chunk** — exact token-budget chunks, the real tokenizer (paid)
- **md_render** — closed-subset markdown to safe, stable HTML
- **html_text** — HTML to canonical readable text, links kept as
  label (href), `javascript:` refused (paid)

**Bundle 8 — palettes**
- **color_palette** — five closed harmony schemes + even-lightness ramps,
  same seed forever

**Agent navigation (bundle 0)** — `GET /agent/manifest`: one line per tool,
~4 KB for all 53, self-certified; `GET /tools/<name>.json` for a single
schema; `GET /SKILL-<pack>.md` to install one bundle's skill instead of the
whole suite. `GET /route?q="dirty csv to typed rows"` ranks the suite with
a closed vocabulary — no LLM, same words same answer. Named recipes chain
steps in one call: recipes (`clean-table`, `clean-json`) or the general
`POST /api/v1/pipeline` — up to 8 tools chained server-side with
`{"$from": [step, "key"]}` refs: intermediate results never enter the
caller's context, and the response is just the last step's body. The 400 response is
the repair prompt: `field` + `expected` + `example`, every time — including
from inside a recipe, where a failing step returns its own prompt untouched.

No API key, no account, nothing stored. Same request → same bytes: every
response carries a `sha256`.

## Why

The top AI uses (code gen, tests, docs, data handling, visualization) are mostly
mechanical transforms where people burn thousands of tokens to get formulaic
output. Moovicut proved the pattern for storyboards: encode the expert craft
once in a deterministic engine, expose it as an API + MCP tool, and agents call
it in one shot instead of reasoning. MechaCut is the same move for data.

The 50-tool suite roadmap and the free/capped/priced tiering live in
[`TOOLS-50.md`](TOOLS-50.md).

## Run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pip install pyyaml tomli-w   # format_convert
.venv/bin/uvicorn main:app --port 8898
```

- OpenAPI: http://127.0.0.1:8898/openapi.json
- MCP (stateless JSON-RPC): POST http://127.0.0.1:8898/mcp — one tool per
  transform, listed by `tools/list`
- Agent skill: http://127.0.0.1:8898/SKILL.md

## Determinism / continuity

- Tests: `.venv/bin/pytest`
- Golden harness: `python scripts/golden.py check` — replays `corpus/*.json`
  and compares response hashes against `golden.json`. `write` re-pins (bump the
  version when an intentional change drifts a hash — same discipline as
  Moovicut's continuity benchmark). New tools ship new corpus cases.
- Design choices that make outputs stable: data is never reordered
  (first-appearance order for aggregates, input order for lines), fixed
  palette assigned by sorted series name, PNG metadata stripped, numeric
  coercion is total (a column is quantitative only if every value parses),
  join overlaps resolve left-wins, dedupe keeps the first occurrence.

## Hardening

No file serving, no reflection: unmatched paths (`.env`, `.git`, wp-scans)
all answer the same neutral `404 {"error":"not_found"}`; `/docs` and `/redoc`
are disabled (the contract is public at `/openapi.json`); request bodies over
5 MB are refused (413) before any payment or route work; every response
carries `nosniff`, `DENY`, `no-referrer`; JSON surfaces are `no-store`.

## Rules

- Nothing is stored. Only IPs in a one-minute rate-limit window, the 60-minute
  miss ledger and payment nonces — all in memory.
- `/misses.json` — public anonymized rejection/refusal ledger: kind and route
  per 400, plus "payment_required" per 402 (unpaid attempt), rolling 60-minute
  window, in-memory only. No payloads, no IPs.

## Payments (x402) — three tiers

- **Free** (most of Bundle 1): keyless, 30 req/min/IP. A 402 never sits on an
  agent's core loop — the free tier is the product, not a trial.
- **Capped** (`json/patch`, `csv/fix`, `csv/types`, `format/convert`): free
  while the request is under 32 KB; above, x402 per call.
- **Priced** (`chart` $0.001; `reshape`, `validate`, `csv/join`, `table/pivot`
  $0.0005): when `MECHACUT_PAY_TO` is set, every call answers
  `402 Payment Required` until a valid x402 payment is attached (USDC on Base
  via EIP-3009, verified and settled by the facilitator).

400s are always free; settlement runs only after a successful response. A
valid `X-PAYMENT` header lets the call through — `x402-fetch` wraps fetch and
pays automatically. The server holds no private key (the facilitator settles
on-chain to `MECHACUT_PAY_TO`); it keeps only payment nonces in memory for
replay protection. Test the loop on `base-sepolia` with faucet USDC, switch
to mainnet (`base`) by changing one env var.

Server env: `MECHACUT_PAY_TO` (unset = payments off), `MECHACUT_NETWORK`,
`MECHACUT_ASSET`, `MECHACUT_FACILITATOR`.

## The industry question: what does a correct answer cost?

Not tokens generated — **tokens per shippable result**. Measured (bench v9:
one extraction task, 6 required fields, expectations hand-computed before
any run, production server, seed 42, temp 0):

| model | naked | card-equipped | the honest reading |
|---|---|---|---|
| 0.5b | 366 tok -> 0/6 | 320 tok -> 6/6 | cheaper AND correct |
| 1.5b | 346 tok -> 5/6 | 462 tok -> 6/6 | +116 tok, systematic miss gone |
| 7b   | 449 tok -> 4/6 | 452 tok -> 6/6 | +3 tok, two fields flipped |

Three taxes the token tables hide:

1. **Retry tax.** The naked misses are systematic — the same dropped date
   on every retry of the same request — so "just retry" does not converge.
   The real price of a miss is a human review or an extra model call,
   unbounded. Equipped: zero retries, measured.
2. **Parse tax.** A free-text answer must be re-parsed by more code or
   more model. A card answer arrives as fields.
3. **Verification tax.** A deterministic server answer carries a sha256 an
   auditor can re-check. Prose carries a vibe.

At 100k documents/month (a projection, labelled as one): you do not pay
83% of the bill when the pass rate is 83% — you pay the bill plus the blast
radius of the systematic 17%. The card turns the bill from probabilistic to
fixed: **+3 to +34% tokens, -100% retries, -100% parsers, 100% provable.**

## The intake loop (human words in, certainty out)

Weak models fail on vague sentences by improvising. Agents should not guess —
they should ask, with a form the server builds:

```
human: "round 1234.5678 to 2 places"
agent -> POST /api/v1/intent/card {"utterance": "<the words, as said>"}
server <- {status: ready, tool: num_round,
           card: {value: 1234.5678 (fact found in the utterance),
                  places: 2 (number next to the field name),
                  mode: half_even (schema default — confirm if unsure)}}
```

If required fields are missing the answer is not a guess but a question —
`question_human`: *"To run date_tz I still need: datetime (string),
targets (array)."* — the exact card the human fills. Multiple plausible tools
become `ambiguous` with the shortlist; nothing matches becomes `no_match`
instead of a hallucinated call. The filled card is gated free of charge
against the tool's real schema:

```
POST /api/v1/intent/check {"tool": "date_tz", "args": {...}}
-> {ok: true, next: "POST /api/v1/date/tz"}     # pay once, never twice
```

Same closed rules as everything here — schema facts, enum words, defaults,
payload detection — no model, no storage, no network. Deterministic:
same utterance -> same card -> same sha256.

## Roadmap

- Determinism auditor: shipped, including the paywall-vs-divergence
  distinction (a stable 402 is a deterministic gate, not a lie)
- An agent loop researches real agent pain, scores candidates
  (demand × determinism)/effort, and ships one small lot at a time —
  every item lands here with tests, tool cards in EN/FR/PT, a
  replayable corpus pin, and landing presence
- Shipped by that loop since 2026-11-20: RRULE recurrence subset (RFC
  5545), XML→JSON with conversion rules printed in the response, URL
  canonicalization (RFC 3986 §6.2.2), CSV→SQL dumps validated by a
  real sqlite roundtrip, EC261/UK261 flight compensation by flight
  date, ISO week arithmetic, cabin-baggage law-vs-gauge by flight
  date, Excel's silent CSV damage predicted per column, shoe sizes
  in millimetres, SRI
  generation from local bytes, a 12-formula catalog and a
  comprehension mirror (/intent/reflect)
- Still open from earlier plans: jq passthrough for power users,
  streamable MCP transport
