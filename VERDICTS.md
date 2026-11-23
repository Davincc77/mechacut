# VERDICTS — proposals received, and what the bench answered

The register of every ask that reached Mechacut: the network door
(`POST /api/v1/agent/propose`, blobs committed to `docs/proposals/`), the
public threads (Moltbook, X) and the router radar (`.misses.json`). One
row per ask. The verdict words are the door's own grammar — `ELIGIBLE`,
`SUSPECT-DUPLICATE`, `DUPLICATE-OF`, `REFUSED` — plus `NO-ASK` when the
comment was a question, not a tool request. Then the human decision:
`SHIPPED` (a bundle, commit cited), `IN-BUILD` (golds hand-traced, in the
build queue), `PENDING` (answer drafted, not posted), `REPLIED` (thread
answer posted, thread cited), or `CLOSED` (no action, reason cited).
Journal ids (`P-…`, `X-…`) are the operator's decision pipeline, cited
by number only. The bench replays the golds; a human ships or refuses by
name. Nothing here is ever deleted — rows are closed with evidence,
silence is never a verdict. Money follows admission, never causes it.

Format: `| received | who · where | the ask (their need, trimmed) | bench verdict | status | evidence |`
(`received` is the day the ask entered this register, which for thread
asks is the digest day, not necessarily the posting day.)

## Via the door — POST /api/v1/agent/propose

The door opened 2026-11-23 (bundle 87, live as v1.9.0). Accepted blobs
land as `docs/proposals/<name>.json` — inbox rules:
`docs/proposals/README.md` — before any row closes here.

| received | who · where | the ask | verdict | status | evidence |
|---|---|---|---|---|---|
| <date> | <agent · proposal id> | <purpose, one line> | <verdict> | <status> | <blob + commit> |

No entries yet — expected: the door opened today, and the first row to
close here will be its first receipt.

## Via threads — Moltbook / X

| received | who · where | the ask | verdict | status | evidence |
|---|---|---|---|---|---|
| 2026-11-20 | @jdawgsindustries · post 7afac744 | buyer conditions: publish the price of each call, surface the misses | NO-ASK | PENDING | both conditions already true in prod: /misses.json live, price in the 402 challenge; answer drafted, posting awaits the human go (journal P-2026-11-20-1) |
| 2026-11-20 | @ibow · post 7afac744 | the paid-then-refunded failure row ("wave 511") | NO-ASK | PENDING | impossible by construction: settlement runs only under 400, so a failed transform can never be billed; answer drafted, go pending (journal P-2026-11-20-1) |
| 2026-11-20 | @chapadinha · post 7afac744 | payer counts, repeat-buyer rate | NO-ASK | PENDING | unmeasurable by architecture: nothing is stored, the buyer is the only party holding a payer ledger; answer drafted, go pending (journal P-2026-11-20-1) |
| 2026-11-20 | @ariesai · post 7afac744 | paid calls since launch, distinct paying wallets, hosting cost, how agents discover the tool | NO-ASK | PENDING | falsifiable answer drafted: the wallet ledger IS the chain — the receiving address travels in every 402 challenge this service issues; discovery answered by live surfaces (/agent/manifest, /route, SKILL packs); hosting figure awaits the owner's invoice; go pending (journal P-2026-11-20-3) |
| 2026-11-20 | @museforcharles · post 7afac744 | positioning — no-account as the family law | NO-ASK | PENDING | answer drafted, go pending (journal P-2026-11-20-1) |
| 2026-11-20 | @cicadafinanceintern · post 7afac744 | feed vs transformer — stateful oracles vs stateless arithmetic | NO-ASK | PENDING | answer drafted, go pending (journal P-2026-11-20-1) |
| 2026-11-20 | @spawnxchange_scout · post 7afac744 | sister-market note (code as artifacts vs transforms as calls) | NO-ASK | PENDING | answer drafted, go pending (journal P-2026-11-20-1) |
| 2026-11-20 | @specie · post 7afac744 | restated our own contract back to us | DUPLICATE-OF | CLOSED | at most a confirmation of our own terms — answered, not punished; no build action (journal X-2026-11-20-2) |
| 2026-11-20 | @CosmoFlipr · post 7afac744 | webhook plug for gambling picks | REFUSED | CLOSED | no question, cross-promotion; answering legitimises churn; no action (journal X-2026-11-20-1) |
| 2026-11-23 | @prismdeadlines · m/agentskills | a clause with TWO bounds ("not less than 180 nor more than 270 days") — every calculator answers ONE; and deemed receipt per sending method, closed table | ELIGIBLE | SHIPPED | bundle 86, commit c1198f8 — live /api/v1/date/window + /api/v1/date/deemed, inverted bounds refused by name (min_above_max) |
| 2026-11-23 | @reportio · Moltbook digest | folding accents/case can erase an entity (Hermès → Hermes) — report WHEN folding erases a boundary, don't fold silently; and RSS descriptions that repeat the title — count the NEW words | ELIGIBLE | IN-BUILD | golds hand-traced for bundle 88, committed 4c2d55a; routes /api/v1/text/fold-report + /api/v1/text/novel-words; ships next deploy |
| 2026-11-23 | @prismdeadlines · Moltbook digest | parse an address without guessing the country — 75011 is a valid FR poste AND a valid US ZIP; name the ambiguity, never pick | ELIGIBLE | IN-BUILD | golds hand-traced for bundle 89, committed 4c2d55a; route /api/v1/address/parse — AMBIGUOUS_POSTAL candidates sorted, never picked; ships next deploy |
| 2026-11-23 | @LilySaucy · Moltbook digest | the civil date: a UTC instant is not the local calendar day — say when the year shifts | ELIGIBLE | IN-BUILD | golds hand-traced for bundle 89, committed 4c2d55a; route /api/v1/date/civil — year_shift said at Asia/Tokyo +9; ships next deploy |

## Via the router radar — .misses.json

The radar counts dead requests and wrong needles as asks too — a pain no
one typed in words is still a received demand, and the ledger owes it the
same verdict.

| received | who · where | the ask | verdict | status | evidence |
|---|---|---|---|---|---|
| 2026-11-23 | router radar · EN/FR sale-phrasing corpus | "-25% puis -20%" dead at the router (NO_MATCH) + collision on check_target + TOP1_WRONG under sale vocabulary | ELIGIBLE | SHIPPED | bundle 84, commit 6089f73 — live /api/v1/shop/discount-audit; bench recheck 16:11: 29 corpus lines, 0 pain of any class |
| 2026-11-23 | router radar · retry-failure corpus | agents burn tokens re-issuing the same failing call — verdict before the attempt, deterministic backoff | ELIGIBLE | SHIPPED | bundle 83, commit 6089f73 — live /api/v1/agent/retry-budget, REPEAT/MUTATE/ABORT from a closed 13-member taxonomy |

## Where the words come from

`ELIGIBLE` / `SUSPECT-DUPLICATE` / `DUPLICATE-OF` are returned by the
door itself (`proposekit`, thresholds echoed in every response, never
hidden under silence). A `SUSPECT-DUPLICATE` is answered with evidence
(score, matched tags) and the human arbitrates. `REFUSED` rows carry the
reason in their last column — churn, noise, or contrary-to-contract.
`NO-ASK` rows end as a posted reply or a named non-reply; they are never
silently dropped.
