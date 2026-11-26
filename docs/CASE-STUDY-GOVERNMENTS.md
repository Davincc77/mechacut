# The Standard That Fails Its Own Example

*A deterministic audit of the official EN 16931 e-invoicing instances, run
through the mechacut door. Published 2026-11-26. Ledger:
[`corpus/wave5-en16931.json`](corpus/wave5-en16931.json). Companion studies:
`CASE-STUDY-TICKET.md` (documents), `CASE-STUDY-BANKS.md` (assumptions).*

## What this is

Europe is switching its invoices to bytes. Poland's KSeF makes the
government-issued XML artefact mandatory from February 2026; France's
mandate opens reception for every company on 1 September 2026; Germany's
B2B receiving obligation is already in force. All of it stands on
EN 16931 — 223 business rules (counted by us from the official
preprocessed Schematron: 58 core, 23 coherence) whose arithmetic is
machine-checkable by design.

We did the obvious thing nobody appears to have done: take the standard's
own example instances — 40 official files, the UBL and CII examples in the
ConnectingEurope repository — and replay their declared totals against
their own arithmetic, through a deterministic door with a hash on every
verdict.

113 of 126 checks pass. One does not, and the failure is between two
official artefacts.

## Method

1. **Corpus.** 40 `.xml` instances from `ubl/examples` and `cii/examples`
   of ConnectingEurope/eInvoicing-EN16931, fetched from
   raw.githubusercontent (public, versioned, re-downloadable).
2. **Extraction.** Python stdlib ElementTree, paths read from the files —
   not guessed (two guessed paths produced fake contradictions and were
   attributed to the extractor before any headline; see Self-corrections).
   Amounts summed as `Decimal` strings, never floats.
3. **Verdicts.** Not ours. Every check was POSTed to
   `https://mechacut.studio/api/v1/batch` with
   `tool=invoice_validate_totals` — exact Decimal arithmetic, named
   rounding (`half_even`), signed deltas, sha256 per receipt. Two batch
   calls, 126 payloads.
4. **Rules replayed.** BR-CO-10 (Σ line amounts = declared line total),
   BR-CO-13 (net = lines + charges − allowances), BR-CO-14 (Σ category VAT
   = declared VAT total), BR-CO-15 (gross = net + VAT), BR-CO-17
   (VAT amount = basis × rate / 100, committee rounding).

## Result

- **113 OK** — the standard's own examples mostly do satisfy the
  standard's own arithmetic.
- **12 not assessable, named**: CII examples carry category RATES but not
  per-category tax amounts — BR-CO-14 cannot be evaluated on them. We
  say so instead of guessing a basis.
- **7 set aside, named**: multi-rate files where per-category bases are
  absent from the example — same reason.
- **1 genuine divergence.** It is the reason this document exists.

## The divergence: 18 679,00 ≠ 18 678,60

File: `cii_examples_huf_example_cii.xml`. Declared facts, straight from
the XML:

```
TaxBasisTotalAmount   69 180,00 HUF
RateApplicablePercent     27,00 %
TaxTotalAmount       18 679,00 HUF   (declared)
```

The official Schematron's own formula — `round(x × 10 × 10) div 100`
(BR-CO-17) — computes **18 678,60**. The example declares **18 679,00**.
The two official artefacts disagree by 0,40 HUF, and the door's receipt
(sha in the ledger) records the signed delta.

Attribution, not accusation: **ISO-4217 assigns zero minor units to the
Hungarian forint.** The example rounds to whole forints — correct in
Hungarian practice. The Schematron's rounding formula hardcodes two
decimals for every currency — correct for EUR, blind for HUF. Neither
artefact is wrong in its own frame; the frames are incompatible, and the
standard ships both.

## What this does not prove

- We did not run the committee's full Schematron (that needs an XSLT
  engine); we replayed the totals chain arithmetically — the subset that
  is pure computation, which is exactly the subset this finding lives in.
- We do not know what the Hungarian tax authority's validator does with
  this file. If it rounds by currency (as practice does), the example
  passes there and fails the formula. If it follows the formula, the
  official example fails the official rule. Either way the divergence is
  in the published artefacts, not in our reading of them.
- One file is not a verdict on 27 member states. It is a measured,
  replayable class-of-bug with a named instance: currency-blind rounding
  in a standard that is about to become mandatory across a currency union
  that contains non-2-decimal currencies.

## Self-corrections, published before the headline

The campaign produced fake findings first, and they are in the ledger:

1. UBL BT-109: my extractor summed invoice lines **and** the declared
   `LegalMonetaryTotal/LineExtensionAmount` — every net check doubled.
   Fixed by reading paths, not tag names.
2. UBL BT-110: header `TaxTotal/TaxAmount` **and** the category
   subtotals were both counted — the same amount twice. Fixed by summing
   subtotals only.
3. Float garbage: the CII rounding-issue example summed to −9,09×10⁻¹⁵
   in floats. In Decimal it is exactly 0,00 — which is the file's own
   lesson, and the reason the file exists.

A bench that flags is not a bench that is right. The door was correct to
flag what we gave it; attribution is what turned 26 contradictions into
1 finding.

## Our own blind spot

`invoice_validate_totals` rounds in a named 2-decimal invoice domain and
refuses a currency parameter (`additionalProperties: false`). That is
right for its domain and wrong for HUF — the same class of blindness we
just measured in the standard. The money family already carries a closed
ISO-4217 table of 33 currencies; the fix is a named optional `currency`
field selecting minor units from it. It is logged as candidate #14
(revision, not new tool) and will go through the door like everything
else. A campaign that finds only other people's bugs has not audited
anything.

## Why governments buy

The catalog numbers, all curlable: EU VAT gap **€128,4 bn** (2023,
Commission); MTIC fraud €12,5–32,8 bn/yr; Poland's gap alone €10,5 bn
and worsening (+4,8 pp); Italy's SdI already stamps a file-integrity
hash on every delivery receipt and rejects on 32 enumerated codes —
the state has accepted that deterministic checks are the control; the
mandates arrive February/September 2026 whether or not anyone verifies
the arithmetic between them.

What this study adds is the pitch no consultant can make: *the standard
itself fails one of its own examples — deterministically, with a hash —
and the same machinery that found it runs against your production
invoices every day, at machine cost, refusing to correct the numbers
because a corrected claim destroys the evidence it was wrong.*

## Control methodology

1. Verdicts rendered by the door, not by local arithmetic — including
   the 25 that were our own artifacts.
2. Every divergence attributed to a named cause before publication
   (ISO-4217 minor units vs the formula's hardcoded 2 decimals).
3. Non-assessable cases named with their reason (12 + 7), never guessed.
4. Extraction bugs published in the same document as the finding.
5. Our own tool's mirror-bug logged as a revision candidate (#14).
6. Every number here is a row in `corpus/wave5-en16931.json` or a curl
   away.

## Appendix — replay it yourself

```bash
# the file, straight from the standard's repo
curl -s https://raw.githubusercontent.com/ConnectingEurope/eInvoicing-EN16931/master/cii/examples/huf_example_cii.xml | grep -E "BasisAmount|TaxTotalAmount|RateApplicablePercent" | head -5

# the committee's own formula, applied to its own numbers
python3 -c "x=69180.00*27/100; print(round(x*10*10)/100)"   # 18678.6

# the door's verdict, with receipt
curl -s -X POST https://mechacut.studio/api/v1/invoice/validate-totals \
  -H "Content-Type: application/json" \
  -d '{"lines":[{"qty":"1","unit_price":"18678.6","amount":"18678.6"}],
       "declared":{"subtotal":"18679.00","tax":"0","total":"18679.00"}}'
```
