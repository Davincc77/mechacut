# Global airline document-audit — protocol (pre-registered)

Status: v1.0, registered 2026-11-26, BEFORE the global sweep waves begin.
This file is the pre-registration: the method is fixed here first so no
later result can retro-fit a metric. Amendments are appended, never
silent — each edit carries a dated note here.

The study began narrow (one issuer, LATAM; see
`docs/CASE-STUDY-TICKET.md`). This protocol widens the lens to the whole
population, with the same instrument, and it defines what "irreproachable"
means operationally: **a fixed population, an explicit sampling design, a
frozen detector, controls around every number, and a coverage table that
publishes its own holes.**

## 1. Population (the frame)

The audited universe = every passenger airline that appears in public
registries with an IATA code or ICAO designator, enumerated from cited
primary sources before sampling begins:

- IATA member + associate lists (public pages; cited with fetch date).
- National civil-aviation authority registries where reachable
  (ANAC BR, FAA, EASA, CAA UK, DOT T-100 carriers, DGAC/ANAC per country).
- A carrier enters the frame only through a cited registry row; a carrier
  known only from news is footnoted, not counted.

Every frame build is versioned (`population/airlines-YYYYMMDD.csv`) with
columns `carrier, iata, icao, country_of_registration, source_url,
source_class, fetched_at`. The frame is frozen per wave; later waves may
extend it in a new version, never edit a cited one.

## 2. Sampling design (per carrier)

Public ticket documents are sourced only from:

1. **Government transparency portals** — reimbursements/FOI releases that
   contain e-tickets or flight receipts (Brazil's Senate & Chamber, UK
   ministerial FOI, Canada travel & hospitality, Australia
   transparency.gov.au, Bundestag, regional parliaments, EU bodies, any
   national equivalent found).
2. **Issuers' own public document paths** (indexed PDF URLs, e.g.
   `latamairlines.com/documents-pdf/…`).
3. **Fingerprint-first search**: any frozen corrupted string found in one
   victim becomes the search key that independently finds the next
   (a template bug is a searchable string).

Sampling is **convenience-based on the public record, and says so**: the
unit is the document, not the passenger. A carrier is "audited" only when
≥1 readable ticket document was obtained; otherwise its row reads
`not-found` — and `not-found` is never, anywhere in this study, phrased or
summarized as `clean`. Absence of evidence is published as absence.

## 3. Instrument (frozen detector, two layers)

- Extraction: pypdf text layer; <200 chars = `scanned` (excluded from
  dirty AND clean, counted separately).
- Layer 1: `file_encoding` on the raw bytes — encoding of the layer.
- Layer 2: double-encoding patterns `Ã©|Ã£|Ãª|Ã¡|Ã­|Ã³|Ãº|Ã§|Â[ºª]|â€|Ã¼|Ã¶|Ã¤`
  — applied with the case/context traps pinned by the LATAM work
  (uppercase legitimate accents like `CONTRATAÇÃO` or `MANHÃ` are NOT
  hits; a needle that is a substring of a correct word must carry negative
  context; mojibake IS valid UTF-8, so Layer 1 alone never fires).
- Provenance: per file — URL, sha256, page count, char count, emission
  date read FROM the document, issuer as printed.
- Positive control (synthetic `Ã©` must fire) runs once per agent session
  before any verdict; a session whose control fails reports nothing.
- The bench itself is dogfooded: where a bench endpoint exists for a check
  (encoding, tax ids, hash), it is called and its answer recorded; manual
  code is the fallback and is marked as such in the ledger.

## 4. Reporting rules

- One coverage table, every carrier in the frame, one row: `audited |
  not-found | scanned-only | dirty | clean` with document counts.
- Dirty counts cite document ids; every number is re-derivable from
  committed ledgers (`docs/corpus/`), which are PII-swept before commit.
- Citations: every load-bearing claim in the final report carries an
  inline ledger id; the Sources block is mechanically rendered from the
  ledger (grounded-citations), never retyped.
- Limits stated with the finding, every time: a 0-row for a carrier with
  two documents is a signal, not a certificate. No carrier is declared
  globally safe on any sample size; the study can only ever say: *among
  observed public documents, X carriers showed corruption of class Y.*
- Wording of record: the bench VERIFIES. It never certifies.

## 5. Wave plan (≤3 parallel agents per wave, per standing rule)

| wave | scope | status |
|---|---|---|
| 1 / 1b | LATAM BR + institutions control arms | done (ledgers in `docs/corpus/`) |
| 2 | Europe, ANZUS, Brazil round-2 | done |
| 3 | LATAM border, money column, census | RUNNING |
| 4 | global sweep A/B/C (EMEA, Americas, APAC) — frame build + first audit pass | dispatched this registration |

## 6. Amendments

- 2026-11-26 — v1.0 registered at the user's request: "rapport
  scientifiquement irréprochable, toutes les compagnies aériennes." The
  LATAM case study's method is hereby generalized and frozen BEFORE any
  wider claim is collected.
