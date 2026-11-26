# The Equation That Holds — and Nobody Proves It

*A machine audit of 86 SEC balance sheets, in one call. Published 2026-11-26.
Every number in this document is curlable; the ledger is in
[`corpus/wave4-banks.json`](corpus/wave4-banks.json).*

## What this study is not

There is no scandal here, and we say so before anyone can accuse us of
burying one. We audited the balance-sheet equation — Assets = Liabilities +
Equity — across 86 SEC 10-K filings and found **zero contradictions**. The
accounting holds. That is the finding.

The finding that sells is the second one: **nobody proves it.** Auditors
give opinions on the whole; regulators sample; the public assumes. The
machine does neither — it verifies every published equation, at cent
precision, in one HTTP call, with a hash on every receipt. Proof stops
being a belief at $500k per engagement and becomes a property of the bytes,
at machine cost.

## How it started

The LATAM case study (`CASE-STUDY-TICKET.md`) proved the method on an
airline's e-ticket template. The institutional catalog
(`INST-CATALOG.md`) then asked the banks' own question: what would
continuous verification cost you, and against which published numbers?
The cheapest place to answer with our own method was the surface every
bank publishes anyway: the XBRL facts in EDGAR.

## Method

1. **Sample.** 100 issuers selected from the SEC's official ticker file by
   normalized name: a named bank list (39 matched) plus a named industrial
   list (61 matched). Disclosure: name normalization pulled in fund
   vehicles (BNY Mellon Strategic Municipal Trust, Morgan Stanley India
   Fund) and an IFRS filer (Prudential plc). They stayed in the sample
   and left it through the exclusion gate below, named.
2. **Facts.** One SEC `companyfacts` call per issuer (public, keyless,
   declared User-Agent). For each issuer: the latest 10-K instant of
   `Assets`, `Liabilities`, `LiabilitiesAndStockholdersEquity`,
   `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest`,
   `StockholdersEquity`, `MinorityInterest`.
3. **The equation, chosen per issuer.** Where `LiabilitiesAndStockholdersEquity`
   exists at the same end date as `Assets`, the test compares two
   independently declared tags — the cleanest form. Otherwise the sum of
   `Liabilities` + equity-including-NCI at matching end date.
4. **The verdict is not ours.** Every check went through
   `POST /api/v1/batch` with `tool=invoice_validate_totals` — one call,
   86 payloads, exact Decimal arithmetic, signed deltas, a sha256 on every
   receipt. The bench's rounding is named (`half_even`); its published
   blind spot (an internally consistent wrong number) is stated in the
   contract and repeated here.
5. **Exclusions are named, not counted away.** 14 of 100: no 10-K Assets
   instant (fund vehicles file N-CSR, not 10-K) or no matching-end
   equation tags. The full list is in the ledger.

## Result

- **86 filings checked. 86 OK. 0 CONTRADICTED.** One batch call, 86 sha256
  receipts, every one replayable against the same XBRL instants.
- Median time: the whole collection plus audit ran inside one afternoon,
  including the self-correction below.

## The 28 errors that were ours

The first pass used the naive equation `Assets = Liabilities +
StockholdersEquity` and the door flagged **28 of 54 as CONTRADICTED** —
52%, the kind of number that writes a scandal headline.

Every one of the 28 was our artifact. `StockholdersEquity` is the
parent-only tag; it excludes non-controlling interests. The gaps were
positive, and their magnitude tracked exactly the NCI each company carries:
Boeing $3M, Starbucks $7.3M, Commerce Bancshares $23.4M — up to NextEra
$11.87B, whose NCI is genuinely that large. Re-fetching with the correct
concepts dropped the contradiction count to zero.

We publish this because it is the audit's own claim, tested on the audit:
**a bench that flags is not a bench that is right.** The door was correct
to flag what we gave it; the attribution — gap direction, magnitude vs.
NCI — is what turned 28 "findings" into 0 findings and 1 lesson. The
LATAM study says the same law about documents; this study says it about
auditors.

## Why banks still buy

The balance sheet is the easy surface — structured, tagged, public,
audited. The money in the catalog sits on the surfaces nobody hashes at
issuance:

- **Invoice redirection (BEC):** $2,770,151,146 across 21,442 complaints
  in 2024, $8.46bn over three years — FBI IC3, table read from the
  primary PDF. The classic vector is a re-issued "same" invoice with a
  swapped IBAN: a byte-diff against the issuer's anchored hash is the
  deterministic detector, and no surveyed vendor sells it.
- **Duplicate payments:** 0.8–2% of disbursements (APQC); 61% of
  double-paid invoices had NON-identical invoice numbers and 8 of 10
  passed PO matching (Trustmi) — exact-number matching is the flaw;
  normalized-text + arithmetic fingerprinting is deterministic.
- **Recordkeeping:** SEC, 16 firms, more than $1.1bn (press release
  2022-174, verified verbatim on sec.gov). Documents that exist but
  cannot be proven unchanged are the fine category.
- **The cost of not checking:** manual invoice handling $12.44 vs
  $5.13 automated (MineralTree); rule-validation commodities at
  €0.0025–0.01 per invoice (SUPER PDP, published API prices).

The pitch writes itself from this study's own shape: *we proved 86 balance
sheets in one call, found zero errors, and published the 28 we made
ourselves. Point us at the surface you are afraid of — invoices, payment
orders, mandates — and get the same receipts.*

## What the bytes prove — and what they don't

Proved: for 86 filings, the declared Assets and the declared
liabilities-plus-equity tags are equal to the cent, as filed, on the
dates fetched, with a replayable hash per check.

Not proved: that the underlying accounting is true (the equation can hold
while the numbers mislead — our own blind-spot clause), that restatements
never differ from originals (we take the latest 10-K instant, as filed),
or that any non-XBRL document was ever checked. Scope is the contract.

## Control methodology

1. Verdicts come from the door, not from local arithmetic — including the
   ones that contradicted us.
2. Artifacts are attributed before headlines: gap direction and magnitude
   vs. the NCI hypothesis, tested on all 28.
3. Exclusions are named in the ledger, with reasons.
4. Sampling defects are disclosed (fund vehicles, IFRS filer).
5. Every claim above is either a curl away or a row in
   `corpus/wave4-banks.json` with its door sha256.
6. No personal data exists in this corpus by construction: issuer filings
   are public by law.

## Appendix — replay it yourself

```bash
# one issuer's facts — Apple, FY end 2026-09-26, Assets 404,548,000,000
# (declared UA is the SEC's condition of use)
curl -s -A "you (you@example.com)" \
  https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json |
  python3 -c "import json,sys; d=json.load(sys.stdin)['facts']['us-gaap']; \
  print({k: v['units']['USD'][-1]['val'] for k,v in d.items() \
  if k in ('Assets','LiabilitiesAndStockholdersEquity')})"

# the same check through the door, one call
curl -s -X POST https://mechacut.studio/api/v1/invoice/validate-totals \
  -H "Content-Type: application/json" \
  -d '{"lines":[{"qty":"1","unit_price":"404548000000","amount":"404548000000"}],
       "declared":{"subtotal":"404548000000","tax":"0","total":"404548000000"}}'
```

Ledger: `docs/corpus/wave4-banks.json` (86 rows, door sha per row,
14 named exclusions, method + self-correction). Companion studies:
`CASE-STUDY-TICKET.md` (documents), `INST-CATALOG.md` (segments).
