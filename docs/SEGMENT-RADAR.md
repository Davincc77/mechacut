# SEGMENT-RADAR — prochains corpus publics, prochains case studies

Compiled 2026-11-27 from live sources (every URL fetched or verified via
search THIS session; probes dated: election.fr 301→data.gouv page 200,
tether.to/transparency 200 with attestation surface, EPREL public-API
request page confirmed by search). Same doctrine as waves 3-5:
door-first arithmetic, attribution before headlines, 0 PII, bare facts.
Ranked by (public corpus quality × deterministic test × deadline ×
institutional buyer). This is an internal program file — nothing here is
a publishable claim until its wave has run and its ledger exists.

## 1. Stablecoin reserve attestations (MiCA) — HOME TURF, do first

- **Corpus (public, dated):** monthly/quarterly attestation PDFs from
  issuers — Tether (BDO, quarterly), Circle (monthly), Paxos/PyUSD
  (KPMG), Ripple/RLUSD (Deloitte), Gemini/GUSD (BPM), StraitsX,
  World Liberty Financial (KPMG). Entry points: each issuer's
  transparency page; an independent tracker lists document dates vs
  as-of dates per issuer (stableradar.com/compliance/evidence —
  navigation surface only, the PDF is the artefact of record).
- **Deterministic tests (all shipped tools):** `pdf_provenance` (built
  tonight) — signature date vs period end vs PDF CreationDate: an
  attestation whose bytes were born before the period it certifies, or
  whose Producer reveals a template reused from last month, is a named
  finding. `doc_text` → line-table extraction → `invoice_validate_
  totals`/`batch` — reserves by asset must sum to the stated total;
  circulation ≤ reserves is arithmetic the PDF itself claims.
- **Why it sells:** MiCA makes periodic reserve disclosure a legal
  obligation for EU issuers; ESMA publishes registers; the comparison
  across quarters is a compliance buyer's daily pain. We already run
  on-chain rails (x402, splitter) — crypto institutions are the one
  segment where the bench's home language is the buyer's native one.
- **Candidates the wave will test at the door:** attestation
  date-order check (pdf_provenance covers); table-sum extraction from
  PDFs (doc_text + ledger); possibly `money_reserves_match` (3rd
  occurrence decides).
- **Honest boundary:** an attestation is not an audit (the documents
  say so); findings measure the documents' own arithmetic and dates,
  never solvency claims.

## 2. Elections — published tallies must add up

- **Corpus (public, licensed, probed 27-11):** election.fr (301→200,
  follows to data.gouv) aggregates the French interior ministry results
  for 26 scrutins, 1999-2026; canonical entry:
  `data.gouv.fr/fr/datasets/donnees-des-elections-agregees/` (page live,
  CSV+JSON resources, Licence Ouverte x10 mentions); raw commune files
  per scrutin also hosted (legislatives 2024, europeennes 2024,
  communales 2026 ministry XML).
- **Deterministic tests:** per bureau: inscrits − abstentions =
  votants; suffrages exprimés + blancs + nuls ≤ votants; Σ candidats =
  exprimés; commune roll-up = Σ bureaux (the ministry publishes BOTH —
  they must agree byte-for-byte on integers); seat allocation = named
  method only (majoritaire à deux tours / proportionnelle — never a
  silent formula). All of it is the banks' column inverted: here the
  equation is expected to hold; a mismatch is a publishable event.
- **Deadline/buyer:** présidentielle 2027; buyers = interior ministries
  (FR/BE/LU), candidates' accountants, media verification desks,
  observation missions. The LU commune scale means every result can be
  replayed in a day — same law as the banks study.
- **Candidates for the door:** `stats_apportionment` (named methods,
  exact fractions), roll-up checker recipe. Same shape as
  invoice_validate_totals over a different carrier.

## 3. EPREL — the energy label is generated arithmetic

- **Corpus (public, API):** EPREL public API (free key on request) over
  every registered model — the label and the product information sheet
  are GENERATED from supplier-entered numbers under delegated
  regulations whose class boundaries are closed intervals with exact
  values (kWh/annum, litres/cycle, g CO2/km, lm/W).
- **Deterministic tests:** fiche value → computed class must equal the
  printed class (boundary arithmetic — the `check_format`/intervals
  grammar, same law as BR-CO formulas); price-per-use cost (num_fx for
  energy price args, money tools); QR→model identity roundtrip.
- **Buyer:** market surveillance (each member state checks labels),
  green public procurement (EPREL is named a procurement tool by the
  Commission's own pages), webshops under display obligations.
- **Effort:** medium (API key signup is human time; data volume huge —
  start with one product group, e.g. domestic fridges, 2026 labels).

## 4. Education / EDC — le diplôme ne se certifie plus, il se vérifie

- **Corpus (public):** European Digital Credentials for Learning
  (Europass) — open-source issuer infrastructure, published sample
  credentials (JSON-LD, W3C VC 1.1), ELM data model public. National
  overlays: bac resultats (data.gouv), but EDC is the institutional
  target: 2025 Council recommendation, EUDIW wallets 2027.
- **Deterministic tests:** transcript arithmetic — weighted average =
  Σ(grade × ECTS)/Σ ECTS rendered as EXACT fractions alongside the
  rounded display (the house money law applied to grades); ECTS sums
  per year; seal/hash verification at viewing = anchorkit's purpose
  (already built): the issuer's hash at issuance makes silent edits
  provable — THIS is the honest answer to "détecter la fraude IA":
  probabilistic AI-detection is not a bench domain and degrades fast;
  issuance-time anchoring + use-time verification makes forgery
  irrelevant regardless of who (or what) authored the bytes.
- **Candidate for the door:** `stats_weighted_average` exact/fraction
  pair (3rd occurrence rule applies from payscale+payscale+grades).

## 5. Aid flows (IATI) — donors publish, nobody re-adds

- **Corpus (public, free):** IATI publisher data via d-portal API —
  activity budgets, transactions (expenditure), per currency.
- **Deterministic tests:** Σ transactions ≤ Σ budget lines per activity
  (same totals grammar); currency normalisation through num_fx;
  date-order (activity end vs last transaction). Money: OECD DAC
  reporting deadlines; buyers = donor ministries + audit boards.

## 6. Carbon (EUTL) and 7. academia (Crossref/ORCID) — second wave

- EUTL: verified-emissions annual tables, public downloads — sums and
  allocation arithmetic. Crossref: free API — ORCID mod-11 checksum
  on author lists (id_checkdigit already knows ORCID), DOI grammar,
  journal PDF template-freeze via pdf_provenance (predatory-journal
  angle). Both solid but lower urgency than 1-5.

## Cross-cutting: the AI question, answered once

Every surface that fears AI-generated fraud (diplomas, invoices,
attestations, logs) gets the same doctrine: **we do not detect
fabrication after the fact — we make it unnecessary to try**: the
issuer hashes at issuance, the verifier checks at use, the door's
arithmetic catches what the eye can't (0.40 forints, three years
of frozen bytes, −9.09e-15). Detection is a claim; verification is
bytes. This paragraph is the marketing answer for "détecter les
fraudes IA" until a wave proves a number on it.

## Program

Order (Vince 27-11): (1) stablecoin attestations → (2) elections →
(3) EPREL → **academia/scientific publishing (Crossref, ORCID,
template-freeze on journals — promoted from second wave, named by the
human)** → EDC education → IATI → EUTL. Each = one wave: collect →
batch at the door → attribute → ledger in docs/corpus/ → case study in
the house skeleton → copy-audit → commit. CourtListener/professions
remains parked pending the account token.
