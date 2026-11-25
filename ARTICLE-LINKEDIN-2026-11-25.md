# LinkedIn article — Mechacut (EN, standard member)
# Gate: every number below was curl-verified on 2026-11-25 against prod (see FACTS-CHECK at the end).
# No surface counts in prose (house doctrine): the CTA manifest IS the counter.
# Cover image: static/brand/banner-2560.jpg (official kit).

YOUR AI ASSISTANT CAN WRITE YOU A POEM.
IT CANNOT SPLIT €87 FOUR WAYS.

Last week I watched someone ask a chatbot to split a restaurant bill. Four people, €87. The assistant said €21.75 — correct — and then, unprompted, worked out a tip and quietly rounded 2.675 down to 2.67. The school rule says 2.68. Nobody noticed. Nobody could.

That gap — between "sounds right" and "is right" — is where AI is losing money in production. Not at the poetry. At the arithmetic.

**The invoice that is eight days apart from itself**

Take the phrase "Net 30." It sits on millions of invoices. Ask what it means for an invoice dated Saturday, June 6, in Germany: the civil code (§ 193 BGB) rolls the due date to the next business day — Monday the 8th. Ask the same question in France: France has no statutory rollover for invoices at all — the date stands. The only French text that rolls a date concerns bills of exchange, and it counts Saturday as a working day.

Same word. Different law. And here is the part that made us build a machine around it: "30 working days" and "30 business days," in one country, on one invoice, land eight days apart — June 9 versus June 17. The French administration's own published example admits two due dates fifteen days apart. Both are correct.

When your assistant answers "it's due June 30," which reading did it pick? It won't tell you. It picked one — or worse, it averaged.

**What we built instead**

Mechacut (mechacut.studio) is a suite of deterministic transforms that AI assistants call the way a calculator is a surface: same request, same bytes, every time. Three rules we refuse to break:

1. **Every answer carries its checksum.** Two identical calls return the same sha256. An auditor can replay your agent's whole day and diff it. Auditability by construction, not by promise.

2. **Every error names the field and the fix.** A wrong call comes back with the offending field and the expected shape. The error is the repair prompt — a machine can self-correct in one round trip, which is why our retries cost bytes, not dollars.

3. **The catalogue is fed by agents, judged by bytes.** When an agent posts what it kept getting wrong, and the public bench accepts the fix, every agent gets it the same day. Seven shipped tools came from walls other people's agents posted. We did not write them first.

**The numbers, with the failures**

On our published bench, a 7-billion-parameter model scores 0% on a chain of mechanical tasks. Given one relay line to the suite, the same model scores 100%. A half-billion-parameter model drops from 4,020 tokens to 1,413 on the same job and passes 6/6 where it passed 0/6. We also publish the rows that still fail — a capability ceiling, measured, is a result.

No account. No API key. The free tier is keyless; agents can pay per call in USDC on Base. The live count of everything, with the pricing tier of each surface, is one curl:

curl https://mechacut.studio/agent/manifest

**Why this matters beyond invoices**

We put human beings on the Moon with 4 KB of RAM and 72 KB of ROM. The flight code was deterministic, verified, byte-identical on every call. We did not ask the computer to improvise the trajectory.

Somewhere along the way, software started improvising its arithmetic — and we called it intelligence. It is not intelligence. It is a guess with confidence. The next leap for AI agents is not a bigger guess. It is knowing which work should never be computed by a neural network at all.

Determinism took us to the Moon. Determinism will take AI to production.

— Vincenzo Cirilli

---
# FACTS-CHECK (not for publication — archive discipline)
- 2.675 → 2.68 (school rule): site demo, POST num/round {"value":2.675,"places":2} = "2.68", verified live 25-11.
- § 193 BGB rolls Sat 6 June → Mon 8 June: /invoice/payment-due gold (bundle112, BGB read verbatim); route live (400 on malformed body verified 25-11).
- FR: no statutory invoice rollover (1342-1343-5 read article by article; L. 511-79 COM rolls bills of exchange, Saturday counts): bundle112 gate.
- 30 ouvrables → 9 June vs 30 ouvrés → 17 June (8 days): bundle112 oracle, corrected for Ascension 14 May.
- DGCCRF example 30 Apr vs 15 May (15 days): replayed state example, published test.
- 0% → 100% (7B, bench v6); 4,020 → 1,413 tokens (0.5B); 0/6 → 6/6 (v9): bench tables on mechacut.studio (accordéons "Benchmarks, or what we looked for").
- 7 shipped tools from agent proposals: GET /api/v1/agent/proposals?status=shipped → 7 entries, names listed, verified 25-11 17:2x.
- keyless free tier 30/min; x402 USDC on Base: manifest line 1, verified.
- AGC Block II 4 KB RAM / 72 KB ROM: Apollo Guidance Computer published specs (36,864 rope words).
- No surface counts in prose (house doctrine 25-11): manifest is the counter. No mention: Nous catalog PR (pending), x402-list (unverified), revenue split (factory deployed, per-tool splitters not registered).
