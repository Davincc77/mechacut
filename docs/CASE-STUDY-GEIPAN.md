# The Date That Never Existed — and the Register That Printed It

*A deterministic audit of the official GEIPAN case export (CNES, France):
3,404 rows, judged through the mechacut door. Published 2026-11-27.
Evidence base: an internal survey run of 2026-11-26 (section report sha256
`df5b7d257328182b28ea1c505941ef52df1de96ed72924cf8f77de58f2011d99`, lines
674–806 of the wave-2 compilation, file sha256 `a3aa7a991ca621c0b820706739d2079242f1f036f3c70d33c017200bddf6284b`).
Companion studies: `CASE-STUDY-TICKET.md` (documents), `CASE-STUDY-BANKS.md`
(assumptions), `CASE-STUDY-GOVERNMENTS.md` (standards), and the wave-2
companion `CASE-STUDY-ARTEMIS.md` (space claims).*

## What this is

GEIPAN is the French space agency's official research group on unidentified
aerial phenomena. It publishes its case files — dates, coordinates,
classifications — as a downloadable table. This is not a study of what
people saw. It is a study of what an official register writes down, run
under one rule: verify, never certify.

The table holds 3,404 cases. Exactly one of them carries a date that never
existed: **September 31, 2000**, printed in a classified case, in the date
cell and again in the case title. Everything else the audit could judge,
it judged clean: 3,397 dates concordant with their own year column, zero
disagreements; every coordinate inside its declared range. And 98 date
cells are honest blanks — placeholders, not errors. The door refused what
was impossible; its own refusals then showed two measurable gaps, published
below with receipts.

## Method

1. **Corpus.** `https://www.cnes-geipan.fr/fr/cnes/export/cas` →
   `export_cas.xlsx`, 1,857,770 bytes, 3,404 data rows, 19 columns, HTTP
   Last-Modified 2026-11-19 14:15:34 GMT, sha256
   `d5aa80194c730d447ddb19bd5f74804d10a3ada031613ef42b659034b2386aa6`.
   Re-fetched 2026-11-27 for this study: same bytes, same sha, same
   Last-Modified header (appendix).
2. **Extraction, local and read-only.** openpyxl over the workbook.
   Used: case ID, title, year, observation date, classification, type,
   latitude, longitude, department, region. The “Détails” and testimony
   columns were not copied; only keyword *counts* were taken from
   Identification. The testimony export was not downloaded. No witness
   name, contact or quote enters this study by construction.
3. **Golds traced by hand before any batch.** September has 30 days;
   2000 is a Gregorian leap year, 1900 is not; latitude −90..90, longitude
   −180..180 (ISO 6709 / WGS84 bounds); the published `geo_geohash`
   example 42.6, −5.6, precision 5 → `ezs42`. Dates are arguments.
4. **Verdicts at the door.** `POST /api/v1/batch`: `date_parse` 15
   payloads (batch sha `1507d0ad1405d1c9fff301a4f3a0f7f398a87cccfa5ac74368c89148bee5dc4f`),
   `geo_geohash` 8 (sha `e9fd37127523fcd751a587db93fd110698f6b9428683131507b7287beab9f26b`),
   `date_civil` 3 (sha `1e7502f23a2970bde221762180ce3bbe8d717a1d980b876c413b540883690401`);
   plus `POST /api/v1/pdf/provenance` on the ODNI PDF (result sha
   `a8192fda53356d3c3e5d44981fa738b5c2d3e36a5c450234319560595df75784`).
   Local Python parsed the workbook; it never overruled a door answer.
5. **Named exclusions.** `aaro.mil` returned HTTP 403 from the survey box
   and `nuforc.org` returned 403 behind Cloudflare; no rows from either
   were collected. The adjacent official substitute used in their place,
   stated as such: the ODNI Preliminary Assessment on UAP, 2021-06-25,
   dni.gov PDF, 385,812 bytes, sha256
   `3b699a825c53aab7816b50ffe0c45d4f424ca43da5eaa421736e529f2ac00ac9`
   (the misspelled official filename ships as-is).

## Result

`date_parse`: **6 OK, 0 CONTRADICTED, 9 named refusals** — all fifteen
outcomes matching the hand-traced golds. The OK six include `29/02/2000`
(valid: 2000 is a leap year) and `27/04/2025` (case `2025-04-51643`).

**The impossible date.** Case `2000-09-01556`, classification B, year
field `2000`, Observation date cell `31/09/2000`. September has 30 days.
The case title repeats it: “BACOUEL (60) 31.09.2000”. Attribution: a real
invalid calendar date in the official export — not an extraction artifact
(the 2026-11-27 recount over the raw bytes found exactly one invalid full
date among 3,404 rows, this one), and not a door error: the door refused
it with `invalid calendar date` (batch sha above; refusal reproduced
2026-11-27, see appendix).

**Placeholders, listed by kind, not counted as errors.** 19 year-only
(`--/--/1937`), 72 month-year (`--/08/1947`), 7 partially malformed
(`--/--/198-`, `--/--/199-` ×2, `2-/05/1995`, `2-/10/1996`, `1-/05/2008`,
`0-/06/2008`). These are missing data in published shapes. The recount
reproduced all three counts from the raw bytes, same numbers.

**The clean control.** 3,397 dates carrying a year agree with the Année
column; 0 disagreements (the 7 malformed cells were excluded from parsing
in the survey). The 2026-11-27 recount is even wider — it also read the
four years embedded inside malformed cells: 3,401 comparisons, still 0
disagreements. A door that flags one row in 3,404 is credible because it
passed 3,397 of them.

**24 cases where the ID year is not the observation year** — e.g.
`1959-03-00042` observes on 20/03/1953, `1980-01-50559` on 30/05/1993.
Not cited as CONTRADICTED: no published GEIPAN rule saying the ID year
must equal the observation year was in hand. A contradiction needs a
declared rule; without one the honest row reads *looked for, found, not
judged*.

**Coordinates.** All 3,404 rows inside −90..90 / −180..180 — zero
out-of-range values. Three 2025 cases sit at (0, 0) (`2025-04-51643`,
`2025-11-51710`, `2025-11-51711`); two rows carry longitude 0 with a
non-zero latitude (44.55°N — a real point in western France — and
34.0°N). (0, 0) is in range and encodes (`s00000`); it is recorded as a
possible missing-value convention, not an out-of-range error.
`geo_geohash`: 5 OK (including GEIPAN `49.62, 2.39` → `u0cdq3`), 3 named
in-range-boundary refusals, 0 CONTRADICTED.

**The ODNI substitute file.** `pdf_provenance`: Producer `Aspose.PDF for
.NET 21.2`, `info_location=object_stream`, created = modified =
`2021-06-25T15:24:27-04:00`, unencrypted. `date_civil` renders that
instant as 2021-06-25 in `America/New_York`, UTC and Europe/Paris alike,
`day_shift=false` — matching the official document date. The 2026-11-27
replay returns the same fields (result sha
`2ba16acdbca73f550d8c4c83f13e2146e3bc7dbe69459c980ef23a9aedb9384c`);
the `created_before_modified` flag reads `false` there for equal
instants where the survey recorded `true` — what both readings agree on
is the equality itself, and that is what the check used.

## What the archive writes about the sky

GEIPAN's own Identification column carries ordinary explanations, counted
(not quoted): **vénus ×108, iss ×77, starlink ×34** — word-boundary counts
reproduced from the raw workbook on 2026-11-27. This study reports those
numbers and attaches no interpretation: they are cells in an official
table, and the table is the finding's only author.

## What was not judged, and why

- **Times and timezones.** The export has no time-of-day and no zone
  field. Sighting-hour, DST-fold and gap checks could not be run on this
  corpus — named, not guessed. The door's `date_tz` tools had no fact to
  judge.
- **Sky-body explanations** (Venus, ISS, Starlink, meteor showers as an
  angle/altitude claim): no named, versioned ephemeris table was loaded
  within the survey cap, and `/route` returned `tools: []` for the
  ephemeris query (sha `9cb30e3e614648c381534b8eff6a313f674c187bc5257f44b7ce1c602dc9d9d4`).
  Nothing was computed by hand. Not CONTRADICTED, not OK: not judged.

## What this does not prove

- Nothing about UAP. One invalid date cell is a data-entry fact about a
  spreadsheet column. It is evidence about registers, not about skies.
- The classification B of `2000-09-01556` is not re-judged here; only its
  date cell was measured.
- The 98 placeholder cells are incomplete data, not false data. A census
  of blanks is not a scandal list.
- The AARO and NUFORC silences are a 403 from one machine, not a verdict
  about those archives.
- September 31, 2000 does not appear in the Gregorian calendar. That is
  the whole of the finding, and it is enough.

## The door's own gaps, published

1. **A 400 naming the wrong field.** `geo_geohash` answered out-of-range
   latitude/longitude with `field: "precision"` (batch sha `e9fd3712…`,
   indices 5–7). Correct refusal, wrong name — a repair contract that
   misdirects the repair.
2. **A refusal that is right but silent.** `date_parse` refuses
   `--/--/1937` with a generic `unparsable date`: no completeness class
   (`year_only` / `month_year` / `malformed`), and the 1937 is not
   returned. Reproduced 2026-11-27 (batch sha
   `9539c080a7c3355fee423c94323f0b9a1ff526c67e766efc3ef55550ecaa2859`).
   That is the tool's published contract — full date or refuse — and a
   contract can still be measured as a gap.
3. **The gap went to the door as a proposal.** `date_partial` (payload
   sha `11dedc38c40acfc30bd41fbd3e325911447a0349a27d2db192465835ca324314`):
   first POST answered 400 naming `name/purpose/examples` when the
   offending field was `source` — the wrong-field class again, now on the
   proposal gate itself. The repaired POST returned **SUSPECT-DUPLICATE**
   vs `date_parse` (12), `date_window` (10), `ics_generate` (9); receipt
   `ec047397a383b469fde1824899b1f937b1f0ce09e5a61fcc50784eedf487bd1f`.
   The verdict was taken as rendered: no rewording, no re-post. Probed
   2026-11-27: `/tools/date_partial.json` → 404 — unbuilt, like its
   verdict, the record stands.

## Control methodology

1. Golds traced by hand from the calendar and the coordinate bounds
   before the door was ever asked.
2. Verdicts from the door, not from local arithmetic — including the
   refusals that landed on our own corpus.
3. The one real invalid date attributed to its source, then recounted
   from the raw bytes the next day by a second hand.
4. Missing data, out-of-range data and rule-less disagreement are three
   different classes; this study never collapses them.
5. A 403 is a named exclusion, never a zero.
6. No person appears anywhere: testimony columns unread, testimony
   export undownloaded, keyword counts only.
7. Every number here is a row of the hashed file or a receipt of the
   door.

## Appendix — replay it yourself

```bash
# the official export, and the sha that frames every count above
curl -sL -o export_cas.xlsx "https://www.cnes-geipan.fr/fr/cnes/export/cas"
shasum -a 256 export_cas.xlsx
# d5aa80194c730d447ddb19bd5f74804d10a3ada031613ef42b659034b2386aa6

# the door's refusal of the impossible date (replayed 2026-11-27,
# batch sha 9539c080a7c3355fee423c94323f0b9a1ff526c67e766efc3ef55550ecaa2859)
curl -s -X POST https://mechacut.studio/api/v1/batch \
  -H "Content-Type: application/json" \
  -d '{"tool":"date_parse","payloads":[
       {"text":"31/09/2000","prefer":"dmy"},
       {"text":"29/02/2000","prefer":"dmy"},
       {"text":"15/06/1951","prefer":"dmy"},
       {"text":"--/--/1937","prefer":"dmy"}]}'
# -> invalid calendar date · 2000-02-29 OK · 1951-06-15 OK · unparsable,
#    no class named, year 1937 not returned

# the ODNI substitute, whose sha closes the provenance chain
curl -sL -o uap2021.pdf \
  "https://www.dni.gov/files/ODNI/documents/assessments/Prelimary-Assessment-UAP-20210625.pdf"
shasum -a 256 uap2021.pdf
# 3b699a825c53aab7816b50ffe0c45d4f424ca43da5eaa421736e529f2ac00ac9
```

*The survey's working files (extracts, batch logs, hashes) stay with the
wave-2 reports outside this repository; the shas above identify them.
Evidence section: compilation lines 674–806, report sha256 `df5b7d25…`.*
