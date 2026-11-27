# The Government Publishes Its Own Counts. We Subtracted.

**A byte-level audit of three FBI Vault collections — Epstein, the 2020 FOIA log, and what we could not read at all.**

*mechacut case study · 2026-11-27 · doctrine: check, never certify — every number below is reproducible from the appendix, and every number carries the method that produced it*

---

## Why this corpus

The FBI Vault is the Bureau's public FOIA library: redacted records, released as PDFs. Each redacted document carries something most people never look at — a **processing sheet that makes its own numerical claims**: a declared total of deleted pages, and a line-by-line enumeration with exemption codes. The government, in other words, publishes arithmetic. Arithmetic can be checked without being interpreted. That is the only kind of fact this house publishes.

Three collections were audited. Nothing here is a thesis about what the redactions hide; several claims about what the redactions *say* were tested against the bytes, and here is what held, what broke, and what could not be read at all.

## First fact: the primary is a scan

Epstein Part 01 was pulled from the Vault itself, byte-verified: `2,662,507` bytes, sha256 `7c292dfa6e…`, 44 pages. Its text layer, measured with pypdf: **zero bytes of text on every page.** A pure scan.

This is not a complaint — it is the load-bearing finding. Every widely quoted "reading" of the famous line **`Total Deleted Page(s) = 258`** necessarily comes from *someone else's rendering* of that page: an OCR pass on a mirror, a search index, a Scribd text layer. A claim read from a rendering is not a claim read from the document. So the audit was run on the renderings, labelled as such, against the hash of the primary they claim to represent.

## The 258, replayed on six renderings

Six independent text renderings of the Part 01 sheet were located (two archive.org mirrors — one ABBYY OCR, one tesseract — the Vault's own search-engine index, Scribd, Studocu, and one more). **All six agree on N = 258.** No copy diverges on the total.

The arithmetic replay on the best rendering (ABBYY, 98,367 bytes of text, md5 `923f0b8d…`):

- Declared total: **258**. Row markers counted: **258**. Gap: **0**. The enumeration length matches its own header.
- Maximum page number in the enumeration: **317**. Numbers absent from the sequence: **63**. Reading duplicates: pages **8** and **133**.
- **67 of the enumerated rows are `~ OTHER - Court Sealing Order`**, numbered 250–317: court-sealed pages are counted inside the deleted total, named as OTHER rather than as an FOIA exemption code.
- Exemption codes outside the naive set: **b7E** (five rows, P01; recurring across P01, 03, 08, 12, 14, 17, 18, 20, 21), plus notations `b6-5` and `b7C-5`.

Two honest notes on that last bullet. **Note one — a correction of ours, kept in the record:** this audit's first brief defined the "closed code set" from memory of search snippets (b3/b6/b7C/b7D/OTHER). b7E is a real, published FOIA exemption — 5 U.S.C. § 552(b)(7)(E), law-enforcement techniques. The house law now reads: **the set comes from the statute, never from the sheet** — and the tool contract proposed from this campaign (`foia_sheet_audit`) encodes the statutory list, not ours. **Note two:** all of this is OCR text. Duplicates and gaps of ±a few are exactly the signature of recognition noise. The verdict on the primary therefore stands where doctrine puts it: **the "258" is verified as a rendering result on six engines, NON_VERIFIED against the scan itself.** That is the finding, not a hedge.

## The 22 parts: one format shift

All 22 Vault parts have text renderings (full table of sizes and md5s in the campaign ledger). One material observation, not interpreted: **Part 22 changes sheet format.** It declares `Total Withheld Page(s) = 4` (not "Deleted"), carries a release date of **January 31, 2020**, and adds Bates-number columns — the closing part of the 2021-era collection is formatted like a 2020 answer. Different template, different vocabulary, same case. Consigned, not explained.

## The 2020 FOIA log: native text, no OCR, one surprise

The FOIA Log 2020 — 467 pages, 16,485 records — exists in a **native-text PDF** (archive.org `FBIFOIALogs`, 2,079,514 bytes, sha256 `ee60d3f8c3…`, md5 matching the rendering first pass: `670564898a…`). Native was proven, not assumed: embedded subset TrueType fonts from a report generator, typographic characters (’ ×6, … ×1, § ×1) that tesseract renderings lose, zero empty pages, zero malformed dates. A recorded parser (self-tested 5/5 on hand-traced verbatim golds) replays the window claim:

- Declared window: **"01/01/2020 to 12/31/2020."**
- Records with a date-opened outside it: **2,278** — 1,310 in 2019, 968 in ≤2018, **0** in 2021+. Inside: 14,207. Sum exact: 16,485. ✓
- The structurally important surprise: **the log has exactly one date field.** "DATE CLOSED", "DATE RECEIVED", "DATE RELEASED" appear **zero** times as columns. So the only fair reading is the definitional one: a FOIA log is a census of *requests*, not of *releases* — a request opened in 2019 lives in the 2020 log because it was still being worked. 2,278 rows predate the title's window the way a case filed in 2019 sits in a 2020 docket. **Said, not sentenced.**
- The sample claim that started this: FOIA `1478175` — "All Documents, Reports, and Findings Provided by CrowdStrike in Relation to the DNC Hack" — dated **13-Oct-2020**: inside the window, ×1 occurrence, subject verbatim. Present, as advertised.
- Every page footer of a log titled "2020" reads a generation date of **7/28/2023** — ×467. Consigning the number, not the story.

## The sheets disagreed with each other — and that is a deliverable

The first pass (tesseract OCR rendering) counted **2,269** out-of-window date tokens. The native-text replay counts **2,278**. Gap: **+9** (+4 in 2019, +5 in ≤2018; +36 tokens total, same direction). The OCR pass undercounted — mutilated tokens at column breaks are invisible to recognition. Both numbers remain in the record with the method that produced each. An audit that hides its own two answers does not exist in this house; **a measured divergence is the most valuable thing a corpus publishes.**

## What this study does not prove

It proves nothing about who was redacted, why, or what the withheld pages contain. It proves nothing about whether 258 is *true* — it proves that six renderings say 258, that the primary is a scan, and that the enumeration's own arithmetic (258 rows, max 317, 67 sealed-order lines) is replayable and noisy. It says the "2020" log contains 2,278 requests opened before 2020, and that the word *log* explains it without anyone being wrong. For the COVID collection ("Origins of COVID-19 (Final)", 19,473,566 bytes): **no text rendering was found anywhere — NON_VERIFIED, full stop.** Zero is a result.

## The mirror

As with every campaign, the door audited itself: this corpus produced a tool contract — `foia_sheet_audit` — proposed to mechacut's own public registry on 27-11, returned SUSPECT-DUPLICATE by the door's word-gate, and admitted after a contract-vs-contract audit (the gate scores words; services differ: `text_claimsweep` searches for markers, the sheet audit replays declared totals against enumerations against the statutory code set). The receipt hashes are in the public registry; the refusal and the admission are both on the record, in that order.

## Appendix — replay this yourself

```bash
# 1. the primary is a scan: 44 pages, 0 bytes of text
shasum -a 256 epstein-part01.pdf   # 7c292dfa6ecb24c2755b73382189aa9841d2819ec6d67e3fe437ef2b0459758e

# 2. the elections log, native text
curl -sL "https://archive.org/download/FBIFOIALogs/FOIA%20Log%202020.pdf" -o log2020.pdf
shasum -a 256 log2020.pdf          # ee60d3f8c33678a539950c568b409fd8b1e7dd67e319cd47e6d4072118979aea

# 3. the window claim (recorded parser, self-test 5/5 on verbatim golds)
python v2_parse_foia_log.py --text native_text.txt --golds VAULT_V2_GOLDS.json
# -> {"total_lignes": 16485, "hors_fenetre": 2278, "ok": true}

# 4. the tool contract this corpus proposed
curl -s "https://mechacut.studio/api/v1/agent/proposals" | grep -o "foia_sheet_audit"
```

Campaign ledgers: `vault-v1-triage.{md,json}` (six renderings, 22-part table, NON_VERIFIED list), `VAULT_V2_ELECTIONS.md` + `VAULT_V2_GOLDS.json` + `v2_parse_foia_log.py` (native replay, golds verbatim), registry rows `foia_sheet_audit` (receipt `bb06eabd`) and `refs_biblio_scan` (receipt `f4a7a990`).

*Same claims, same bytes, different renderings — and a hash for each.* That is all this study asserts, and it is enough: the documents publish arithmetic, and arithmetic answers to subtraction, not to opinions.
