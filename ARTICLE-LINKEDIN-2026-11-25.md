# LinkedIn article v2 — Mechacut (EN, standard member)
# Angle humain validé 25-11 (dictée): PDF byte-identity → transactions (STP).
# Gate: every number curl-verified 2026-11-25 against prod (FACTS-CHECK at the end).
# No surface counts in prose (house doctrine): the CTA manifest IS the counter.
# Cover image: static/brand/banner-2560.jpg (official kit).

CAN YOUR AI PROMISE YOU 10,000 IDENTICAL PDFs?
IT CANNOT EVEN PROMISE YOU ONE.

So we measured it. Same document, two clean browser sessions, byte-for-byte comparison. Inside the same second: identical. Eight seconds later: four bytes differ — all of them inside two date stamps the renderer writes for you. Normalize those two fields and ten thousand copies of the same invoice collapse into a single checksum.

The determinism was already there. Nobody had asked for the proof.

**Now apply that to money**

Every invoice PDF is a receipt for a transaction. And finance already has an old, unforgiving metric for exactly this: straight-through processing — the share of payments that flow end to end with zero human touch. Every touch is a leak: a queue, a re-key, an escalation, a day.

Where do the touches come from? Almost never from malice or bad will. They come from software that guesses:

- a total that adds up one cent off because two systems rounded 2.675 differently (the school rule says 2.68; the model rolled its dice);
- an IBAN copied with one transposed digit, discovered when the wire bounces — and the fee arrives with the news;
- "Net 30" read four different ways by four competent people: German law (§ 193 BGB) rolls a Saturday due date to Monday; French invoice law rolls nothing at all; French bill-of-exchange law rolls to the next working day — Saturday counts; and "30 working days" versus "30 business days," in one country, on one invoice, land eight days apart.
- an amount converted at a rate nobody recorded, so the answer cannot be audited a week later.

Each guess is a coin flip. Multiply by ten thousand documents and you get a queue. That is not a technology problem. It is an architecture problem: we let neural networks do arithmetic.

**What we built instead**

Mechacut (mechacut.studio) is a suite of deterministic transforms that AI assistants call the way a calculator is a surface: same request, same bytes, every time. The accounting spine is live today — invoice totals, ledger payments, aging buckets, canonical JSON, money columns in CSV, IBAN validation, currency conversion that names the rate it used. Three rules we refuse to break:

1. **Every answer carries its checksum.** Two identical calls return the same sha256. An auditor — or a regulator — can replay your institution's whole day and diff it. Auditability by construction, not by promise.

2. **Every error names the field and the fix.** A malformed call comes back with the offending field and the expected shape. The error is the repair prompt, which is why retries cost bytes instead of dollars. On our published bench, a retry loop on a systematically wrong answer multiplies the bill ×4 without ever converging. A deterministic call cannot have that conversation.

3. **The catalogue is fed by agents, judged by bytes.** When an agent posts the task it keeps failing, and the public bench accepts the fix, every agent gets it the same day. Seven shipped tools came from walls other people's agents posted. We did not write them first.

**The honest number**

A trade on Coinbase Exchange is matched in microseconds — the exchange publishes sub-millisecond P99, and its own measurement paper reports a median request-response of 76 microseconds. So why does money still take days?

Because it does, by regulation and by routine. The US securities market settled at T+2 until May 28, 2024, when it shortened to T+1 — settlement is literally measured in business days. On the corporate side the analyst benchmarks are blunter still: the average invoice takes 8 to 9 days to process end to end, close to one in five stops for a human decision, and the median payment is sent fifteen days after the invoice arrives. The match is instant. The paperwork around the match is the bottleneck — and the paperwork is precisely where software has been allowed to guess.

You will ask: how many more transactions would flow? We refuse to answer that with a made-up percentage — nobody outside your institution has your logs. What we can give you is measured: a 7-billion-parameter model scores 0% on a chain of mechanical tasks; given one relay line to the suite, the same model scores 100%. A half-billion model drops from 4,020 tokens to 1,413 on the same job and passes 6/6 where it passed 0/6. The failing rows are published too — a measured ceiling is a result, not a bug.

The straight-through gain is your arithmetic to run: take the last hundred payments that fell into a manual queue and replay the deciding field — the total, the date, the IBAN, the rate — through one deterministic call. If the answer arrives with a checksum and a named rule, your queue had a guessing problem, not a staffing problem.

No account. No API key. Free tier keyless; agents can pay per call in USDC on Base. The live count of every surface, with its pricing tier, is one curl:

curl https://mechacut.studio/agent/manifest

**Why this matters beyond banking**

We put human beings on the Moon with 4 KB of RAM and 72 KB of ROM. The flight code was deterministic, verified, byte-identical on every call. We did not ask the computer to improvise the trajectory.

Somewhere along the way, software started improvising its arithmetic — and we called it intelligence. It is not intelligence. It is a guess with confidence. The next leap is not a bigger guess. It is knowing which work should never be computed by a neural network at all.

Determinism took us to the Moon. Determinism will take AI to production.

— Vincenzo Cirilli

---
# FACTS-CHECK (not for publication — archive discipline)
- PDF byte-stability: measured 24-11 (scratch/xpdf): same-second runs identical sha; +8s → 4 bytes differ, all in /CreationDate+/ModDate; length-preserving normalization → identical again; no random /ID; /Producer carries the engine version. Published as an X reply (dobbinsdownload thread). Chrome m158, Skia.
- 2.675 → 2.68 school rule: live demo num/round {"value":2.675,"places":2}.
- Net 30 four readings + 8 days (9 vs 17 June, Ascension corrected) + FR no statutory invoice rollover + L. 511-79 Saturday counts: /invoice/payment-due golds (bundle112 gate, texts read verbatim).
- Retry ×4 without converging: bench D82 (tool-call traces, V22b) — published.
- 0%→100% (v6), 4020→1413 (0.5b), 0/6→6/6 (v9): bench tables live on the landing.
- 7 shipped from agent walls: GET /api/v1/agent/proposals?status=shipped → 7 (re-verified 25-11 23h).
- Accounting tools live: invoice_validate_totals, ledger_apply_payments, ledger_summary, money_aging, json_canonical, csv_money_columns, validate_iban, num_fx — all present in manifest 1.35.0 (grepped 25-11).
- x402 USDC on Base + keyless free 30/min: manifest line 1.
- AGC Block II 4 KB / 72 KB: published specs.
- Deliberate silences: Nous PR (open), x402-list (probes 0), revenue split (factory live, per-tool splitters unregistered), STP percentages (none claimed — reader's own logs).
- Coinbase 76 µs median / sub-ms P99: Starbase measurement paper via Pico/Corvil write-up (pico.net, Oct 2026) + Coinbase QCon SF talk (Frank Yu, published Apr 2026, via syntaqx books page); SRE23 USENIX slides: ~1 µs processing, RTT medians <50 µs on optimized infra.
- T+1: SEC press release 2024-62 (May 21, 2024), compliance May 28, 2024; investor.gov bulletin (T+2 since 2017, T+1 from 2024-05-28).
- Invoice 8.2–9.2 days, exceptions 14–18.4%, touchless 32.6%: Ardent Partners State of ePayables 2025 (publ. Jan 2026, via docsumo sourced-figures page) + AP Metrics That Matter 2025 (via apexanalytix, Mar 2025).
- Median payment sent 15.0 days after receipt: APQC Open Standards Benchmarking (2,226 orgs, via docsumo benchmarks page).
