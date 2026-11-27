# LinkedIn article v3 — Mechacut (EN, standard member)
# Angle validé 27-11 (Vince): annonce du listing officiel Hermes + fusion avec la case study LATAM.
# Gate: every number curl-verified 2026-11-27 (FACTS-CHECK at the end).
# No surface counts in prose (house doctrine): the CTA manifest IS the counter.
# Deck: 5 pages landscape 16:9, same backgrounds as v2 (official kit bg-hero).

ONE COMMAND FROM THE CATALOG.
EIGHT YEARS OF FROZEN BYTES AS THE PROOF.

**A plugin that ships no code — and the audit that shows why that matters.**

Yesterday the Hermes plugin catalog listed mechacut. Not a demo, not a wrapper: the contract itself, one line away — `hermes plugins install mechacut/plugin`. Two skills, zero code, zero daemon. An agent that installs it knows exactly three things. Same request, same bytes — every response carries its sha256. Errors name the offending field and the expected shape, so a retry costs bytes instead of dollars. And when the agent meets a computation the door does not have, it proposes a *contract* to a public registry — where verdicts, bench results and named refusals are readable by anyone, including the people who disagree with us.

We think a listing is worth an article only if you can check what it installs. So here is the check, in the form of a story.

**720 boarding passes that board no one**

It started with one passenger's PDF. A LATAM Airlines Brasil e-ticket that looked wrong: `tÃªm`, `serã`, a Spanish label where Portuguese is owed (`Nª de orden`), fused words inside the fare rules the passenger is asked to obey (`dadata`, `nãorealize`) — and a city that does not exist: **Rio do janeiro**.

We did not argue about it. We counted. Brazil's Federal Senate and Chamber of Deputies publish their travel reimbursements — ticket PDFs included — as public records. That portal is an unintentional time capsule: 8,221 ticket rows in the 2019–2026 dumps, 6,350 attachments fetched, 1,105 readable LATAM e-tickets. **720 of them — 65.2% [62.3–67.9, Wilson 95%] — carry the same frozen strings.** Not similar strings. The same broken bytes, across every census year, across years, passengers and orders. A 2018 ticket already carries them: the freeze is at least eight years old, and a new corrupted branch was still shipping in May 2026.

A corrupted string is a fingerprint. Random damage makes random victims. Frozen bytes make a template.

**The contrast is the thesis**

Same census, same readers, same period: **GOL 0/600. Azul 0/345.** Travel-agency printouts of *the same LATAM flights* carry none of the strings. 237 public documents from Apple, Google, Microsoft, xAI and five banks — including a 712-page prospectus with 47,082 correctly encoded accented characters — zero hits. Sixty-odd international tickets from twelve countries: zero. And the sharpest cut: LATAM e-tickets **issued outside Brazil** — 22 machine-readable, from Quito to Santiago — are **all clean**, and their Spanish template prints the *correct* `Nº de orden` where the Brazilian one prints `Nª de orden`. Same generator, same skeleton. The defect is not Brazilian paperwork, not the reimbursement pipeline, not the flights. It is one template layer, inside one airline, faithfully reproduced eight years running.

This is not a typo story. It is a liability story, and the numbers are published: Brazil's STJ holds a binding thesis (Tema 164) that inadequate information is itself a service defect with moral damages uncapped by the Montreal tariffs; Spain's Ministry of Consumer sanctioned five airlines **€178,933,631.99** in 2024 for unclear price presentation, under the article number that does the same work as Brazil's art. 47; and Brazilian fiscal law already rejects a mis-encoded tax document outright (official code 402) — fiscally, it does not exist. The document layer is a regulated object. Nobody proves the clean version, either.

**The mirror: our own door refused us**

Believing LATAM's company number (a valid CNPJ, mod-11) showed a gap in our suite, we proposed `validate_cnpj` to our own public door. The door returned **SUSPECT-DUPLICATE** — and the replay proved it right: the endpoint had existed all along (`validate_taxid`, `kind=cnpj`). Worse, our hand-traced gold was wrong; the endpoint's answer was right. The refusal was committed to the public registry. The real defect was discoverability — a bare word found nothing — and it was fixed the same day, test-pinned. An audit that accuses by bytes must be able to be accused back. Ours answers the same way to us as to strangers.

**The fix was never intelligence**

No one at LATAM needs a smarter model to print a ticket. The ticket needs a pipeline that cannot lie about what it printed: generate once, hash, diff the static strings, fail *named*. Every check in this audit — encoding detection, checksums, date normalization, the eight-year frozen-string comparison — is one deterministic call, and the same call returns the same bytes for everyone, forever.

That is now one command from the catalog. And the full audit, with every ledger, URL and sha256, is in the open repository: `docs/CASE-STUDY-TICKET.md`. A reader with the same bytes must reach the same verdict — otherwise it is not evidence, it is an anecdote.

`hermes plugins install mechacut/plugin`

The live count of every surface, with its pricing tier, is one curl:

`curl https://mechacut.studio/agent/manifest`

— Vincenzo Cirilli

---
# FACTS-CHECK (not for publication — archive discipline)
- Marketplace listing: hermes-agent.nousresearch.com/marketplace/mechacut — badge COMMUNITY, category Tools, v1.1.2, "Updated 12 hours ago", install line `hermes plugins install mechacut/plugin` — all read verbatim from the live page 27-11 ~13:20 CET. NOT claimed: "built by Nous Research" (official NousResearch plugins are a separate list; ours is a community listing IN their official catalog — the article says exactly this).
- Two skills, zero code, zero daemon: package description on the same page (Portable Agent Plugins v1, plugin.json + skills/).
- LATAM census numbers (8,221 rows; 6,350 fetched; 1,105 readable; 720 dirty = 65.2% [62.3–67.9]; 2018 ticket 2018-05-20; branches 2021-03-29 and 2026-05-17; same-day pair 303857/303863): docs/CASE-STUDY-TICKET.md, ledgers docs/corpus/, reproducible per the appendix curls. Verified against the case study published 26-11.
- GOL 0/600, Azul 0/345, agency printouts 0, institutions 237 docs 0 hits (712-page BB prospectus, 47,082 accented chars), international ~60 docs 0, foreign LATAM 22/22 clean + correct `Nº de orden`: same case study (Corpora B/C/D/E), same ledgers.
- Legal numbers: STJ Tema 164 (2018, binding); Spain €178,933,631.99 (2024-11-22, five low-cost carriers, art. 47.1(m)); NF-e rejection code 402; Senacon/Procon R$ 4,881,796.75 (2021–2023): case study §"Why a typo is a contract problem", anchors re-curl-verified at publication 26-11.
- validate_cnpj refusal: docs/proposals/validate_cnpj.json (committed); registry shows the line; the endpoint live today: POST /api/v1/validate/taxid {"value":"02.012.862/0001-60","kind":"cnpj"} → valid=true, mod-11 double DV, sha256.
- "28 shipped proposals" deliberately NOT in prose (house doctrine: no surface counts; the manifest curl IS the counter). Live registry total as of 27-11: 28 shipped / 20 accepted / 17 refused / 1 proposed / 1 en-banc — for the record only.
- Deliberate silences: who wrote the LATAM template (unknown, not claimed); LLM involvement (speculation, excluded); no percentage of "AI tickets" asserted anywhere.
