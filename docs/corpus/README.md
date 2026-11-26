# docs/corpus — ledgers behind the document-verification study

Machine-readable evidence for `docs/CASE-STUDY-TICKET.md` (and the
network write-ups that cite it). One JSON per collection wave, one row
per document analyzed: source URL, file sha256, issuer/airline,
extraction density, per-fingerprint and per-family counts, and — for
wave 2 — the bench verdict + sha256 of each `file_encoding` call.

What is **not** here, by rule:

- No passenger, deputy or account-holder names. The public-record
  document ids (Senate `ceaps/documento/<n>`, Chamber CEAP rows) are
  cited because the transparency portals publish them; individuals are
  never extracted into a ledger row.
- No personal identifiers. `banks.json` originally carried CPF numbers
  from CVM-mandated officer disclosures and from discarded client-side
  faturas — masked to `•••.•••.•••-••` before this archive existed.
  The count of masks (31) is stated here rather than hidden.
- No scans counted as clean: rows whose text layer was empty carry
  `status: scanned` and are excluded from both the dirty and clean
  tallies, exactly as the case-study method describes.

Files:

| file | wave | scope |
|---|---|---|
| `wave1-original-fingerprint-pass.json` | 1 | first fingerprint pass over the 69 downloaded Senate candidates (pre-correction; kept as history) |
| `wave1-fingerprints.json` | 1 | corrected matcher, the 26-hit base |
| `apple-xai.json` / `google-microsoft.json` / `banks.json` | 1b | institutional controls: 42 / 49 / 33 rows |
| `wave2-europe.json` | 2 | 30 docs, UK/Scotland/Germany FOI & Bundestag |
| `wave2-anzus.json` | 2 | 30 docs, US DOL/HHS/state audits, Australia, Canada |
| `wave2-brasil.json` | 2 | 58 docs, Câmara API + fresh Senado ids, fingerprint-evolution table |

Re-derivation contract: every row's URL was fetched and hashed as
received; re-running the detectors means `curl <url>` + the needle
families listed in the case study (or, once it ships, one
`text_mojibake` call). A ledger that cannot be re-curlied is prose.
