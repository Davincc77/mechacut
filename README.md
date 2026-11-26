# MechaCut

Deterministic mechanical tools for AI agents — the machine that answers
**the same bytes to the same request, forever**. One stateless API, an MCP
endpoint, x402 USDC micropayments on Base, and zero storage of what you send.

**Live catalog: [mechacut.studio/agent/manifest](https://mechacut.studio/agent/manifest)**
— 189 transforms + 9 named recipes as of v1.41.0, each with its tool card
(`/tools/<name>.json`: schema, price, a human sentence in EN/FR/PT, and the
server's real captured answer). Weak model? Start at
[`/SKILL-MINI.md`](https://mechacut.studio/SKILL-MINI.md) — a 2.6 KB manual
written to be followed literally by a 0.5B. Prove-the-determinism checklist:
[`/integrity.json`](https://mechacut.studio/integrity.json) — 431 replayable
golden pins.

The list below is the historical build log (bundle by bundle); the manifest
is the truth of today. Recent highlights: `money_payscale` SALARY↔HOUR,
EVERY published denominator NAMED (the paystub fight in law: 5 USC 5504(b)
"divide the annual rate by 2,087", "nearest cent, counting one-half and
over" — OPM's $18.845→$18.85 is a shipped test vector; 2,080 is the "typical"
that r/Payroll cites in every comment and no calculator names; basis
fed2087|priv2080|workdays(year)|pto|hours — 365 refused BY NAME; the
rate-first vs direct order pair renders the signed delta — −6.40 a pay,
−166.40 a year on 52,000, r/AskHR's "$8" family quantified; and the 27-payday
year of r/IRS_Source counted from the calendar, 2016 and 2027, 53 Fridays);
`agent_resultcliff` GOOSE row read AT CODE, not at thread (block/goose MOVED
to aaif-goose — redirect proven via API; developer shell: 2,000 lines OR
50,000 bytes → temp file + LAST-50 lines TAIL-capped at 10,000 bytes with a
char-boundary snap, the head dropped TWICE; the agent-wide handler REPLACES
past 200,000 chars — zero survival, knob #9256; #13817: even the rescue
notice can be orphaned — and the carried "CLI 20 lines" claim died at the
reading, removed; declared mode judged only by the harness's own UTF-8 bound
inequalities, INDETERMINATE_NEEDS_PASTE before any guess); then `money_prorate` RENT
CONVENTIONS NAMED (the same lease posts FOUR formulas: 1000/30=33.33×18
"= 600" rounds SILENTLY twice — the landlord's own way gives 599.94
(r/personalfinance 9sqw2j); the office splits "/30 days, REGARDLESS of
actual number of days" — 566.67 vs 548.39 on a 31-day January
(r/Landlord 1hitzjq); the annual/365 rule is published too (r/RealEstate
1idq3vr); and "prorated $127.55" vs the $1,354 billed is TWO OBJECTS
under one word (r/personalfinance 1b5p04y). basis cycle|month30|year365,
order product|quotient are ARGUMENTS; compare renders the pair with the
signed delta and occupied+unoccupied=amount; a date carrying a TIME is
refused by name WITH the two whole-day counts — nobody publishes 11.5 as
a unit, 12-or-11 is the `inclusive` bound (r/personalfinance cevz6l);
defaults replay the bundle-4 bytes exactly); then `money_settle`
NON-CASH MODE (THE 500
DOLLARS OF POINTS: the same trip publishes two answers — 40.50 counting the
instrument in FACE against its provider, 290.50 giving the credit and splitting
only the cash (r/askmath 1tuuael; the gap is exactly half the face — a graph
disagreement, not arithmetic). kind=noncash + counts face|cash|none are
ARGUMENTS; the cash cost of a point is yours to name, never fetched (CFPB
rewards spotlight 2024-05); no reading named = refused by name — silently
choosing the convention IS the wound; then `agent/result-cliff` (DOES THIS
RESULT SURVIVE INLINE IN THIS HARNESS — every harness buries tool results at its
own frontier in its own unit, and the unit in its error message often LIES:
Claude Code persists past 50,000 CHARACTERS while the notice says tokens,
MAX_MCP_OUTPUT_TOKENS lifts nothing, the latin/greek matrix proves the unit
(#97622; the doc now says it: "50,000 characters, whatever its token count",
hard ceiling 500,000 via the maxResultSizeChars annotation); codex counts UTF-8
bytes ÷ 4 — its published function, so the crossing is EXACT not estimated,
marker "…N tokens truncated…", mutated in place with no artifact and no handle
(#14206); bionic cuts at exactly 50,000 chars appending "... (truncated)", no
continuation (#2338); VS Code answers UNPUBLISHED_THRESHOLD because NO threshold
is published — the kit refuses to guess (#311068); and the table's own proof:
rakazo's PUBLISHED #2439 formula is ALREADY DEAD CODE — read at HEAD today the
cut is per-leaf, keep = max(8, floor(len/4)), payload.contextTruncated=true. A
cliff read from memory one month old is WRONG, so every row rides as_of dated
and source-cited. Unit absent or non-convertible = NAMED refusal; paste WITHOUT
a harness and all six rows answer in one call, each measured the way IT measures
(hermes-agent's own row included: 2,000,000 chars, head 40% tail 60%, counts
inside the notice); sisters: context-tax PRICES the listing, tool-trim CUTS it,
mcp-surface DIFFS it — none predicted the crossing of ONE result); `money/settle` (WHO PAYS WHOM
after a group fronted money — r/askmath 1ugli3y replayed verbatim: A
fronts 1375, C 865, B nothing; C tells B "keep the barbecue on me"; A
demands 628.33, B offers 458.33 — the thread never resolved because
BOTH answers are right, on different graphs. Net mode settles the
NETTED balances with the /money/split closed remainder rule (the
thread's own 746.67×3 = 2240.01 does not close; the orphan cents are
NAMED and closed here), transfers at the PROVEN minimum by zero-sum
subset-partition DP (n≤9; above, greedy declared, minimality NOT
proven), and the forgiveness — the thread's own rule, named by the
commenter who wrote that C can only forgive the debt owed to them — is
an executable ARGUMENT: capped at the forgiver's remaining claim, the
unreleased part still travels to the other creditors, never silently
erased. Itemized mode honours EACH RECEIPT: the waiver kills the B→C
receipt edge, B pays A 458.33 and C BEARS 288.33 — B's answer, with
who pays for it spelled out. mode=compare renders both graphs and
numbers the gap (118.34 net vs 288.33 per receipt). Rates are
ARGUMENTS, never fetched — the transaction-date rate is the caller's
law to name (2026-11-14 writing names booking-date and
settlement-date rates as the trap); 0- and 3-decimal settlement
currencies refuse by name because the family's remainder rule is in
cents; every answer replays each person's balance before it is
returned — identity failure is a REFUSAL, not a warning. Sisters:
money_split splits a KNOWN bill, money_aging ages invoices, pricedrop
answers who owes you the DIFFERENCE on a dropped price — no one was
clearing an advances graph; eleven prod needles x3 languages plus
decoys close the pain at the radar — and the verification caught a
pre-existing router hole now closed XS in the same build: the landing's
own e3 sentence, "did I copy this IBAN right? a bounced wire costs
45", routed text_diff because STOP_EN never carried the pronouns and
auxiliaries STOP_FR/STOP_PT have held since b70 — i, me, did, does,
was, were, are now die as grammar (Armenia's "am" deliberately spared,
class b81) and validate_iban carries the card's own surface words) —
the manifest counts them; `json/bigint` (THE INTEGER THAT LIES AT THE TOOL BOUNDARY — a well-formed JSON crosses an IEEE-754 parser, the value changes, NOTHING SAYS SO: Unity-MCP #754 EntityID arrives ...300 and the lookup dies with a LYING not-found; claude-code #11506 348555896224571969 displayed ...970; llm4s #1597 ...993 read as ...992 "whichever library reads the result"; ragflow PR #22064 snowflake ids widened by Go float64; x402 Go #4258 rounded a PAYMENT amount. The law is cited verbatim — RFC 8259 section 6: integers in [-(2**53)+1, (2**53)-1] are interoperable (and 1E400 named a hazard); the MCP draft MUST is quoted SCOPED to x-mcp-header parameters, never overclaimed. Every flagged integer comes back TWO ways: the exact binary64 value AND the shortest string JS re-emits (the emulation certified against the real reader: 240 values, zero divergence) — the tickets quote one without naming the other. Classes closed with declared severity: COLLISION (2^53 and 2^53+1 read IDENTICAL — the wrong-record symptom) > LOSSY > OVERFLOW > UNDERFLOW > EXACT_UNSAFE > SAFE; the scan follows the GRAMMAR, never a regex — digits inside strings are never findings (the regex inspectors admit it); mode=quote rewrites only flagged literals, every other byte intact; per finding the reader table JS/Go-float64/Python-int/nlohmann — conformance is not interoperability, the DIVERGENCE is the product; the hand oracle got caught twice by its own node table before the module (exponent re-anchor, and a golden cell carrying the value where the print belongs), doctrine b112 replayed; six needles x3 languages, two class decoys silent, siblings guarded: json_coerce keeps the rejected SHAPE (8.0 vs u64), num_round keeps asked-for ROUNDING, agent_mcplist keeps the PAGES) — the manifest counts them; `agent/mcp-list-completeness` (DID YOUR MCP CLIENT SEE EVERY PAGE — seven published 2026 bugs, one mechanism: the server paginates tools/list, the client calls once, everything past page one dies SILENT while the server stays green (anything-llm #6935 "the server remains marked as running"; Codex #28858 "the other 2,642 are uncallable"; Claude Code #23179/#48126/#66537; Claude.ai web #87 sees 15 of 21; vercel/ai #19240; openwiki #565); the rules are the spec read verbatim at BOTH versions: missing nextCursor = end, and — NEW in 2026-07-28, absent from 2025-06-18 — "an empty string is a valid cursor and thus MUST NOT be treated as the end of results", replayed as the EMPTY_CURSOR_TRAP class the merged anything-llm fix also names, with repeated cursors rejected (their merged text: "repeated cursors are rejected to avoid an endless loop") and a page 2 never silently swallowed; paste your declared number and the tail becomes a COUNT — with declared names, the missing tools are LISTED, never invented (74 vs the codex 138, 8 vs the Laravel 15, 6 vs Claude's 21-for-15); the resume point is the exact cursor echoed — never parsed (a cursor "64" is NOT offset 64: spec opacity MUST) — or a named refusal when following it would lie: loops are not resumable, a dead -32602 cursor is dead; JSON-RPC envelopes unwrap, unknown tool keys are ignored on purpose (shape lives at mcp-audit, pages live here); verdicts CLOSED with the severity order declared in the payload (STUCK_LOOP > TRUNCATED_SILENT > UNSTABLE > COUNT_SHORT > COUNT_OVER > INTERIM_LISTED > DUPED > COMPLETE) — the audit also says COMPLETE, eight pins replay from the public repros; sisters: mcp-audit REJECTED, mcp-surface CHANGED, tool-overlap COLLIDED, context-tax HOW MUCH — none counted PAGES, and a listing can pass all four and still die at page two; the hand oracle got caught once before build (class output order: severity, not discovery) and its own cross-page double-count bug died in the scratch, doctrine b112 replayed; six prod needles x3 languages + two page-decoys that must prescribe NOTHING close this pain at the radar); `invoice/payment-due` (THE FOUR READINGS OF NET 30 and who defers what, cited to the read text: § 193 BGB defers SATURDAY by law, BFDA 1971 s.1(4) defers bank holidays on the gov.uk PROCLAIMED tables 2026-2028 — years outside the table are refused, not predicted; France is the country of the EMPTY TABLE read as a verdict: civ. 1342-1343-5 replayed article by article carry NO statutory roll for an invoice term (old 1235-1244-1 repealed 2016, the 1925 bill rule repealed 2007), so the contract clause decides — while the lettre de change DOES roll (com_l511_79, read) to the next OUVRABLE day, Saturday counted per L. 3133-1, the same statute behind the eight-day gap between ouvrable and ouvré counts of one term; the DGCCRF ships 45-jours-fin-de-mois with TWO official methods and its own example, 30 April versus 15 May, fifteen days apart — the tool renders both, NEVER a mean (a thesis test: no average key CAN exist in the output); TARGET2 on top, six closings per year from the ECB page and the published computus: the rails close, the DEBT runs (directive 2011/7/EU art. 3, read — interest without reminder), a Saturday closing is named ABSORBED with zero phantom days, and the GBP rail carries NO settlement column because the CHAPS text was never read — what is not read is not sworn; L. 441-10 cap flagged, eom exempt BY LAW since the derogation passes sixty itself; day-0 pinned on four published examples; the oracle, traced by hand, got caught TWICE by the machine before the module (the 25-dec closing missed from the TARGET set; Ascension 14-May missed from the count — June 17 is the number); sisters: money_aging buckets KNOWN due dates, date_deemed gives the deemed receipt that starts this clock, schedule/holidays lists days without ever a term — none answered WHEN payment is legally due; the fratrie guard caught MY new tags stealing a counting phrase mid-build — fixed at the source, and the hole it exposed went to date_calc, which carried no French counting words at all: a dead query found by my own test, then owned; six prod needles x3 languages close the pain at the radar); `agent/tool-overlap` (WHICH TWO of your tools BECOME ONE id in WHICH client — the published name grammars replayed as a closed table: VS Code's (prefix+name) dot-to-underscore cut@64 with the registration-loop ABORT, where the public repro 5 tools -> 2 listed is now a test and the thrower dies with the whole alphabetical tail; gemini-cli's generateValidName read from their source (mcp_ prefix, sanitizer, head30+\"...\"+tail30 past 63 — non-injective, the registry keeps the LAST and the first is dead); the gateway family's plain cut with no collision check, where the foundry issue's production-vs-preview 64-byte head ships pinned byte for byte; caps read from the specs themselves — OpenAI 64 [a-z A-Z 0-9 _ -], Gemini REST 128 with dots and colons — and the asymmetry IS the thesis: GATE_STRICTER_THAN_API names ids legal in the API and folded by the client, because API-legal proves nothing at the caller; Anthropic publishes the conflict error and NO length, so length is never promised there (a source you did not read is a claim you do not ship — the soldes-lu lesson, replayed outside law); repair is a NUMBER — the shortest server-key length that uncollides the cut heads, or NO_PREFIX_FIX when the distinguisher lives past every window, rename the tools themselves; classes closed COLLAPSE_CUT/FOLD_COLLAPSE/SANITIZE_COLLAPSE/EXACT_ID/BARE_SHADOW/TOO_LONG/ILLEGAL_CHAR/NAME_CONFLICT, verdicts SILENT_LOSS/LOUD_ONLY/CLEAN — being LOUD is not being SILENT, that difference is the product; UTF-16 units exactly like String.slice; sisters: context-tax says HOW MUCH, tool-trim WHAT TO CUT, mcp-surface WHAT CHANGED, mcp-audit REJECTED — collisions were counted nowhere; closing its router pain at the source: «which tools silently disappeared after adding a second mcp server» prescribes this tool in prod while «combien coûte la liste» stays with context-tax and «je veux débrancher mon lave-vaisselle» still prescribes NOTHING); `agent/tool-trim` (WHICH tools to disconnect to fit a window budget, and the exact re-count after — the step every November 2026 post about tool-list cost stops before: paste one tools/list, optional calls_30d from YOUR logs and a budget in tokens or as a percent of the window (the published auto-load rule, 10%, rendered as a floor); drops fall in closed classes on EXACT fractions, never floats — IDLE_30J first (paying every turn, never used: the xalpx rule published from his session logs), then worst cost-per-call, and NEVER the unmeasured ahead of the measured idle — UNKNOWN tools are cut last and flagged; keep protects names and a keep floor that misses the budget alone returns STILL_OVER with the overage chiffré, not advice; the re-count is the sister's arithmetic: paste the survivors into /agent/context-tax and the number MUST be identical, the global ceil(chars/4) travels beside the sum-of-ceilings with the divergence stated (b101/b104 law); dollars only at YOUR decimal price — the altrouter measure, $0.7806→$0.3099 for cutting three servers, becomes arithmetic before the disconnect, not an anecdote after; ties chars desc then name asc, ceiling 5000, top-100 folded, verdicts FITS_AS_IS/TRIMMED_FITS/STILL_OVER closed; sisters: context-tax says HOW MUCH, cost-diff the price in between, mcp-surface CHANGED — this says WHAT TO CUT; closing its router pain at the source: «trop d'outils MCP, lesquels couper pour tenir le budget» prescribes the plan now, while «combien coûte la liste» stays with context-tax, «what changed since the reading I pinned» with mcp-surface, and «je veux débrancher mon lave-vaisselle» prescribes NOTHING); `shop/soldes-be` (the BELGIAN sale calendar as DATES computed from art. VI.25 BCEL with the SPF standstill enumeration replayed 24-Nov-2026: winter runs 3–31 January, OPENING THE 2ND when the 3rd is a Sunday — lived 2016, coming 2027; summer 1–31 July, the 30th of June when July 1 is a Sunday — lived 2018, and its standstill is the NAMED «du 31 mai au 29 juin», which beats the generic formula (30 May) and ships the divergence as a field; the one-month standstill computed at exactly the next-day boundary the press keeps missing — sudinfo on 24-Nov printed 3 December where the SPF names 2 December–1 January; the corona years verbatim with their Moniteur numacs: été 2020 moved to 1–31 August (loi 27-mai-2020), winter 2021 REPORTED to Monday 4 January (AR 10-déc-2020: the fired Sunday clause was OVERRULED — fired AND overruled travel together, an erased clause is a lie) and PROLONGED to 15 February by a LOI because §2 caps the King at one month (the press said 14, the adopted text says 15, the conflict is dated); eligibility (30 days on sale, still held), the sectoral ban, the braderie ≤4-day exception and the liquidation escape ride as verbatim; the Conseil d'État 20-May-2026 annulments come back as a NAMED conflict because the tool dates and does not plead; winters before 2015 refused with the 1991-law facts, France refused by name pointing at the sister's arrêté, Luxembourg refused by name carrying the truth that its dates are set EACH YEAR by grand-ducal decree — no formula, no invented date; and the honesty proof: the queue's own memory claimed the summer clause fired in 2024, the calendar corrected the FILE before the build — 1 July 2024 was a Monday; closing its router pain at the source: «quand commencent les soldes en belgique» used to prescribe NOTHING, now it prescribes this tool, and the no-country query still lands on the French window by declared TABLE order); `shop/soldes-lu` (the LUXEMBOURG sale calendar as DATES that come from the ACTES themselves — loi du 23-déc-2016 art. 1 § 4 hands both periods to a grand-ducal decree EVERY YEAR: no second-Wednesday rule, no Sunday clause, the grammar IS the act; ten replayed RGDs (Mém. A-807/2017 through A-330/2026, each with its verbatim) date 2018–2027, every one of the 48 bounds cross-checked against the real calendar, and the two state misprints the replay caught travel NAMED by kind: the 2017 RECTIFICATIF (A-928) fixed a weekday LABEL only — «samedi, le 29 juin 2018» was a Friday, same date — while the 2023 RECTIFICATIF (A-96) moved the BOUNDARY itself: A-511 printed «samedi, le 23 juillet 2023», a Sunday, and the corrected close is Saturday 22 July, which the press and the 30-Sep-2022 government communique had been saying all along, so quoting the Official Journal without its rectification contradicts the State; the 2021 corona chain is LU-shaped, not BE-shaped: RGD 08-Oct-2020 fixed 2–30 January, RGD 30-Dec-2020 POSTPONED it «to a later date» without naming one, and RGD 13-Jan-2021 ABROGATED that postponement and recabled Wednesday 20-January → Wednesday 17-February — three acts travel, one of them dead, no date invented; the structural divergence rides by ABSENCE: the 2016 law knows NO waiting period (zero «attente» in the replayed text — the 7-day advertising window lived in the repealed 2002 law, abrogated entire by art. 11), so Belgium's standstill field does not exist here and the module says so instead of averaging; the one-month statutory cap is a VERIFIED invariant line by line (max 30 days, min 24); gates: seasons ≤ 2017 refused carrying the 2002-law facts (the old-regime RGD 15-Sep-2016 is replayed via the official Chamber dossier because its legilux ELI 404s — the source is named, not hidden), 2028-and-after refused because the next decree is not signed — pas d'acte, pas de date, jamais de prophétie; and the sisters' pointer went LIVE: both refused Luxembourg «en file», now they refuse it pointing at this table (their pin replaced by contract change, recorded), while «saldos luxemburgo datas» — whose stem «datas»→«data» used to hand the query to the chart tool — now lands here, the PT probe-pain closed in prod); `agent/cost-diff` (the PRICE OF THE UPDATE: paste two tools/list readings and get the bill between them on the sister's canon and estimator so the subtraction means something — classes ADDED/REMOVED/CHANGED/SAME by name, per-tool delta in chars and tokens, percentage of the BEFORE side (None for an added tool: nothing was paid before; −100.00 for a removed one), a CHANGED tool shipping its moved_fields SIGNED per contract field (the r/mcp case: same 27 tools, 8497→22k tokens, the schema detail alone); the global delta is ceil(after/4)−ceil(before/4) and the per-tool sum travels beside it with the divergence CHIFFERED, never hidden (testdino told the Playwright story — 0.0.41→0.0.85, +78% unannounced; the verdict transition FITS_TO_OVERFLOWS turns it into a field); the delta rides EVERY turn (Irolla) and dollars only at YOUR decimal price, sign included — a listing that shrank saves real money and the refund is named; ties broken by name ascending because a diff has no shared pasted order and the rule is declared; sisters: mcp-audit says REJECTED, mcp-surface says CHANGED, context-tax says HOW MUCH — this says FROM HOW MUCH TO HOW MUCH); `shop/soldes-window` (the French sale calendar as DATES computed from the arrêté replayed 24-Nov-2026 — winter opens the second Wednesday of January at 8 h, ADVANCED to the first when the second falls after the 12th: 2027 is Wednesday 6 January, and the calendar site printing «until 9 February» dropped the clause; summer carries its own advance, penultimate Wednesday when the last falls after the 28th: 2027 opens 23 June; four weeks with the start day counted; and the part no press table copies — SEVEN annual derogations shipped with their verbatim and their JORF: été 2020 fixed to 15 July (Covid), winter 2021 fixed to 20 January then CARRIED TO SIX WEEKS by the 15-Feb-2021 arrête, Moselle opening été 2021 ALONE on 26 June, Guadeloupe moved to Thursday 7 October 2021, and the heatwaves carrying été 2023 and été 2026 to five weeks — scoped by predicate on the text, which is why Corsica keeps four; the annex itself VERSIONED, rows 06/66/973 living only for windows that began before 17 May 2023 — moneyvox's «Guyane 5 October 2023» recycled an abrogated line, the press artifact this table refuses; the four eastern départements open on the «premier jour ouvré», a word the arrête never defines: 2027 ships BOTH windows, Monday 4 first (the arrêté's word), Saturday 2 named (the press reading); Saint-Pierre counts «premier mercredi APRÈS le 15 janvier» strictly — 2025-01-15 IS a Wednesday, so the window opens the 22nd; years before 2020 refused with art. 4; Belgium, Luxembourg, Switzerland, Quebec refused BY NAME because this table replays only the French arrête and lends dates no memory; closing its own router pain at the source: the recipe's stray «sold» tag was stealing «soldes» queries at score 5 — a word too generic is an incident, and the veto list is closed, zero LM); `shop/gift-voucher` (the gift card that «expired» may be legally alive: Ireland's Consumer Protection (Gift Vouchers) Act 2019, replayed section by section — a printed expiry shorter than five years from the CONTRACT date is not voided but DEEMED REPLACED by five years, the deemed term overriding the paper (66B(1)(b)+(c)): the JD Sports shape, ~€250,000 refunded in July after the CCPC's 20-Nov-2026 call-in; the expiry day itself still redeems because 66A(1) says «the date AFTER which»; the 2-December-2019 commencement gate named; the €1 refund floor shipping WITH its conflict — the Act prints «€1 or more», the CCPC FAQ paraphrases «more than €1», at €1.00 the statute governs, both texts travel; four counter acts voided against numbered subsections (single-use, voucher caps, name-mismatch fees, earlier replacements) and the gift RECIPIENT holding all rights (66B(10)); France replayed NEGATIVE — no law fixes a validity minimum, the printed date is contractual, and the «30 years» rumour is real-property prescription (art. 2227), corrected by name; UK/BR/US refused by name, not replayed; a jurisdiction-named tool that also refuses cities: «expired in London» dies at the router before it can promise Dublin law); `agent/context-tax` (the question eleven November 2026 runs measured for THEIR servers and nobody answers for yours: paste the tools/list and get exact canonical chars/bytes per tool, a token estimate that is the published floor method — ceil(chars/4), quoted with its error declared, no third-party tokenizer installed on purpose — split by field: name, title, description, schemas, annotations, and the pasted unknown keys NAMED with their bill (an 'instructions' key is text the server makes you pay for; the tool-poisoning class now has a price line); counterfactuals computed not argued — names-only with its multiplier (the tool-search claim: 'seul le NOM est chargé') and drop-descriptions (r/mcp: the cost lives in descriptions, not counts); charged PER TURN (Irolla: 'the tool list is not paid once') and dollars ONLY at your own decimal-string price argument — no stored model-price table, prices rot, arguments don't; FITS/OVERFLOWS_WINDOW against your window (the run that counted 35,633 servers found 45 listings alone larger than 200k); top-100 detailed, the tail folded into a named aggregate so the answer fits the small model it is for; sisters: mcp-audit says REJECTED, mcp-surface says CHANGED — this says HOW MUCH); `money/keep-records-uk` (the UK retention clocks that HMRC states in four places and no page computes: "six years" is ONE phrase for different anchors — VAT counts from the date ON the document (even a paper describing a future event, CH15200 says so), the limited company from the END of the financial year, Companies Act s.388(4) counts the same records THREE years if private, SIX if plc — from the date MADE — and Self Assessment counts five years from a 31 January deadline that is on no document, with both official examples replayed (2022-23 → keep until end of January 2029) and a second clock when a return is filed more than four years late: fifteen months from sending; the four "or longer if" extensions come back BLOCKED with their published reason, never an invented date; CH15400's minimum table travels as replayed the day after its own update (23 November 2026) with the official arbitrage — two rules on one paper, the LONGER governs; a tax year is 5 April because ITA 2007 s.4(3) says so, and other year-ends are refused citing the Act; and a tool that NAMES its jurisdiction refuses queries that name another: the France/Brazil phrasings now die at the router instead of promising UK dates — the veto is a closed word list, zero LM); `shop/legal-guarantee` (the STATUTORY clocks, dated: FR conformity runs 2 years from the delivery day with the presumption at 24/12 months — and F11094 contradicts itself on refurbished goods, both dates shipped and NAMED, never averaged; vices cachés start at DISCOVERY (2 years) with a 20-year cap from the SALE; UK keeps three clocks apart the way Reddit threads fuse them: 30-day reject (s.22(3) 'first day after these have all happened'), the six-month burden that is not a deadline (s.19(14), EN ¶97), and limitation of six years in England/Wales/NI against FIVE in Scotland — nation absent, both dates travel; US/AU refused by name carrying their facts, the commercial holiday windows stay in return-deadline's table); `agent/mcp-surface` (pin a pasted tools/list and diff it against the previous one — per-tool SHA-256 over the spec's contract fields plus an order-sensitive surface digest (2026-07-28 makes deterministic order contractual: ttlMs, cacheScope); annotations canonicalized to their PUBLIC spec defaults so a readOnlyHint flip that rewrites no text still moves the digest — the AI-SDK fingerprint's blind class, counted at 524 flips on 189 servers in three weeks, while RugSnare counted 6.5% of top npm MCP packages drifting their listing in four; icons and _meta excluded BY NAME, unknown pasted keys hashed (a new 'instructions' key is a digest move — the tool-poisoning class); duplicate names refused, never silently shadowed; verdicts CLEAN/REORDERED/DRIFT closed; sister to mcp-audit: that one asks whether a client would REJECT the listing, this one asks whether it CHANGED — shape, never runtime, no fetch, no subprocess); `agent/mcp-audit` (paste the tools/list you are about to ship and it returns the named wire-shape reasons a real client would silently drop it — empty inputSchema (gitlab-mcp #286), root not object (langfuse #13804), draft-07 tuple items (strapi #27395), unknown protocolVersion, non-ASCII homoglyph names; the SEP-986-vs-spec slash conflict is RENDERED, not averaged; static listing only — no fetch, no subprocess, shape certified runtime never); `agent/retry-budget` (is re-attempting THIS failure rational? the closed taxonomy AWS AGENTREL07-BP02 demands — transient errors REPEAT with deterministic 1-2-4 backoff (capped at a named 64 s, no jitter: a verdict, not a draw), fixable errors MUTATE (a schema violation retried is a guaranteed failure bought twice — the 1,840-identical-retries story, counted BY payload hash, never guessed), terminal errors ABORT; per-call ceiling AND session token budget checked at two levels like AWS prescribes; provider Retry-After honored above the schedule; `retryable` travels as a machine field so the model reads it instead of parsing English; loop/doom-check judges the trace after the fact, this judges the next call before it — post-mortem vs ante-mortem); `shop/discount-audit` (is that crossed-out price LEGAL: the Omnibus 30-day rule as closed arithmetic — reference = the LOWEST price the shop applied in the previous 30 days (Directive (EU) 2019/2161 art. 6a), and a weekend sale LOWERS that reference even after the price went back up (CJEU C-330/23): 100→80→100→70 is a 12.5% cut, not 30%; verdict COMPLIANT / MISLEADING_INFLATION / WRONG_REFERENCE / NO_REDUCTION, every divergence counted in signed decimal points; the progressive-step clause rendered per transposition (de §11(2), fr L112-1-3) — and the eu-vs-de disagreement on the SAME history is RENDERED, never averaged; history and as_of are arguments — no price is ever fetched, and an uncovered 30-day window is refused by name because absence is never zero. The Commission's own March 2026 sweep: 30% of 314 traders got this wrong); `shop/return-deadline` (the published holiday RETURN table for 2026-2027: sellercentral and bestbuy.com verbatim, rows admitted only with >=2 concordant sources, provenance class carried on every answer; the shared 'until Jan 31' headline's omissions rendered as data — Target's window closes Dec 24, Best Buy's member rule splits at Dec 4 into a 60-day Day-1 rolling window, Amazon UK adds 'whichever is later' against the delivery date; single-source retailers are refused BY NAME carrying the candidate fact; a pattern table that publishes itself as fact is returned as a NAMED conflict, never averaged; since v1.19 France is IN — fnac.com and darty.com replayed VERBATIM ('prolongés jusqu'au 15 janvier 2027 … hors marketplace, gros électroménager et TV', the TV/GEM exclusion returned as a NAMED condition because 'electronics' routes to both sides of the published line), boulanger.com's own site printing its window end as 2026 in the legal note and 2027 in the cart module — the official typo carried as a NAMED conflict, Dec 27 never Dec 31 —, Dell France carrying the later-of rule in French ('la date la plus tardive des deux prévalant'), amazon.fr publishing its second Jan-15 regime NOT per category but per product in the Buy-button widget — the limit named, nothing invented —, and Apple direct joining with a grammar new to the table: the window keys on RECEIVED items ('received between November 6 and December 25, may be returned through January 8, 2027', apple.com verbatim, page FR concordant) so the delivery date is the gate and absent is not zero; cdiscount stays refused by name — a date without its purchase window is not a deadline); `shop/shipping-deadline` (the Christmas 2026 last-ship-by table, cross-checked: six press tables published Nov 13–21 disagree — one syndicate prints FedEx Saver/2Day/Overnight a full day later because its target is Dec 25, not Dec 24 — rows survive only with ≥2 agreeing sources and the dissenter is returned NAMED with its reason; UPS Ground has no single last day (zone-dependent) and is refused, not averaged; weekdays derived from the calendar the press itself cites; as_of is an argument, so days-left is arithmetic, not a clock; the window dies Dec 23); `invoice/validate-totals` (audits a DECLARED invoice total: amount==qty×unit_price per line, sum==subtotal, subtotal−discount+tax==total, and the tax claim checked against BOTH published rounding methods — aggregate or per-line, the match named — exact Decimal cent-level signed deltas, verdict OK or CONTRADICTED; numbers are never corrected, because a corrected claim destroys the evidence that was wrong; published blind spot: an internally consistent wrong number is invisible to identity checks); `food/ovenschedule` (one oven, every dish, times counted BACKWARDS from serve_at as an argument: eight published 2026 Thanksgiving timelines disagree on rests of 20 to 60 minutes, 325 or 350°F, and none counts the preheat that eats 45 — this one names the physically impossible handoff (next dish enters the instant the previous leaves at another setting), refuses a bare 180 without a unit (82°C or 356°F is a coin flip), and caps rests at the FSIS 2-hour danger zone — the leftovers rule, applied to the oven); `food/leftovers` (the leftovers window: 2-hour discard clock counted from cooked_at, STRICT like the flight table's EXCEEDING-3-h rule — exactly 2 h passes, 2 h 01 discards; 3-to-4 days from the DAY of cooking with the 4th day named LAST_DAY; the two FSIS pages contradict each other on the freezer, 2-6 vs 3-4 months, so the window rendered is their UNION with both anchors cited — and quality is labelled quality, safe indefinitely at 0F; closed category table, no per-food State-extension rows invented); `/route` T6 (bundle 70: FR/PT grammar words are stop-words now — tested on the RAW token because `stem(mois) == moi` would have killed the dates signal with the pronoun — and nothing under confidence floor 4 is listed: an incidental tag (3) or purpose word (2) never prescribes, a tool NAME (4) is not incidental; the radar's three standing OVERMATCH died at the source, dead PT queries get an honest empty list instead of a noise needle, and the two vocabulary holes the floor exposed got filled, not hidden); `food/poultry` (the Thanksgiving window, USDA/FSIS tables as ARGUMENTS — put the 16-lb bird in the fridge by 2026-11-21T10:00, not before 11-19; every web calculator contradicts the next; done is 165°F at the thermometer, never a guessed date); `agent/modelid` (static audit of
your agent's model-id strings against a pasted catalog: closed grammar
`org/name[:variant|#variant]`, named verdicts — PREFIX_KEPT, NO_ORG,
CASE_DRIFT, PUNCT_DRIFT, VARIANT_DECOR — did-you-mean at a NAMED
Levenshtein≤3 threshold, and the response itself swears that OK certifies
shape, never that the GET answers: the V23 incident, written as doctrine
into the bytes — and since v1.30 it NAMES THE DOOR: dialect tokens read
from the gateway docs replayed 25-Nov give {chat, embedding, image} ×
sync/batch doors, image+`:batch` is called a CLASH ("Batch returns text
and embeddings only"), embedding+`:batch` rides its two named
restrictions (provider refused, nested input 400), and every
dialect-carrying entry wears the badge "listed in the catalog, NOT
proven invocable" — the radar's standing batch mirages, named instead
of rediscovered); `money/unitprice` (unit price and shrinkflation with
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
