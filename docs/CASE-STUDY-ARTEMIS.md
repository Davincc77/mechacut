# The Numbers That Landed — and the Claims That Didn't

*A deterministic audit of moon-landing and space “hoax” claims against JPL
Horizons (DE441) and the NASA/ALSJ printed numbers those claims attack,
every arithmetic step judged through the mechacut door. Published
2026-11-27. Evidence base: an internal survey run of 2026-11-26 (section
report sha256 `892e46fde6fa2a88f7988a9d599f016820bab1a0634d42ad81ca9d7793bafd06`,
lines 1735–1962 of the wave-2 compilation, file sha256
`a3aa7a991ca621c0b820706739d2079242f1f036f3c70d33c017200bddf6284b`).
Companion studies: `CASE-STUDY-GEIPAN.md` (the other half of the same
survey day), `CASE-STUDY-BANKS.md`, `CASE-STUDY-GOVERNMENTS.md`.*

## What this is

Space “the landing was faked” claims are almost all numbers: signal
delays, distances, shadow angles, mission clocks. Numbers can be checked.
42 checks ran against JPL Horizons (DE441 ephemeris, spacecraft kernels
Artemis-I_ASF and mar099) and the printed NASA / Apollo Lunar Surface
Journal values, with every computation judged at the door.

**31 OK, 11 CONTRADICTED.** None of the 11 supports a hoax: 2 are the
claims themselves proving false, 6 are printed artifacts (rounding,
conversions, undeclared reference points and models), and 3 are this
door's own limits — published here because the audit ran on three bodies
of numbers, not two. Verify, never certify, starting with our own
arithmetic.

## Method

1. **Claims quoted as printed.** Wikipedia *Moon landing conspiracy
   theories*, revision 1388029471 (2026-11-26T10:52:39Z — the revision
   id and timestamp re-confirmed live 2026-11-27): “more than a
   two-second delay … at a distance of 400 000 km”; “Typical delays in
   communication were about 0.5 seconds”; the 1977 *Back to Godhead*
   claim that the Moon sits 800,000 mi beyond the Sun (93e6 mi), a trip
   “in 91 hours” at “more than a million mph”. Printed counter-values:
   the NASA SP-4029 Apollo 11 summary, the ALSJ post-landing commentary
   and sun-angle tables, the Artemis FD13/FD6 blogs and press kit, the
   Mars 2020 pages, the 1969 Lunar Surface Operations Plan PDF.
2. **Reference physics, pinned.** JPL Horizons API queries with every
   response header saved (ephemeris source, center, time scale
   `TIME_TYPE=UT`, airless). Hand-typed constants: c = 299,792.458 km/s
   exact, 1 mi = 1.609344 km exact. Time scales from USNO `tai-utc.dat`
   and the IANA/IERS leap-seconds list (expiry 2027-06-28 — an argument,
   not a clock). The JPL Mars quick-facts page returned 403 to curl; its
   “205 million km” is cited from a search excerpt only, labeled there.
3. **Golds, with the disclosure up front.** All gold values were traced
   by hand in working notes before each batch; the study's golds file was
   written to disk after the batches it documents. That sequencing is a
   caveat, repeated here rather than footnoted away. Two hand-traced
   golds were wrong and the door caught them: 2.668 → **2.669** s, and
   242,024.6 → **242,026.6** mi. The gate was right both times; the
   corrections are on record with the golds.
4. **Verdicts at the door.** 12 `POST /api/v1/batch` calls: `math_calc`
   37 payloads, `units_convert` 8, `date_calc` 43, `date_tz` 6,
   `check_format` 3, `date_parse` 2, `logic_rules` 4 — **103 payloads**
   (the survey's own summary line says 101 while its per-tool table
   sums to 103; the breakdown is cited, the mismatch is named). Batch
   shas in the ledger table below. Local Python was a pocket calculator
   for golds and a response parser; no gate number was ever reformatted.
5. **Attribution before citation.** Every CONTRADICTED classified first:
   (a) the claim is false, (b) printed artifact, (c) gate limitation or
   bug, (d) extraction artifact. Class (d) found zero cases — and says
   so instead of hiding the class.

## Result: eleven contradictions, three columns

**Two claims are simply false.**

- “Typical delays about 0.5 seconds.” Horizons puts the Moon's one-way
  light-time at **1.2947 s** at the first step-off epoch — a 2.589 s
  round trip, **5.18×** the claim. A 0.5 s round trip would require the
  Moon at 74,948 km (b1 M05/M07/M08, rule b8 R2; batch shas `e822f5d2…`
  / `28931a70…`).
- “The Moon is about 93.8 million miles away” (the 1977 claim). Horizons:
  **242,026.6 mi** — the claim overshoots by a factor of **387.6**
  (b1 M09/M10). The claim's own division is fine: 93.8M mi ÷ 91 h =
  1,030,769 mph, arithmetically right on a false premise (b1 M11).

The best-known variant checked was *true as stated*: “more than a
two-second delay at 400,000 km” computes to 2.669 s at 400,000 km, and
2.589 s at the real 388,152 km (b1 M06/M05) — the genre survives by
quoting numbers that already hold.

**Six printed artifacts.**

- The NASA Artemis press kit prints “268,563 miles (432,194 km)”. The
  door converts 268,563 mi → **432,210.25 km**, and 432,194 km →
  **268,552.9 mi**: a 10-mile internal disagreement inside one
  parenthesis (b3 U1/U3, batch sha `14ef270a…`). The PDF was created
  2022-12-09 (local `pdfinfo` — the door's provenance pass declined the
  11.9 MB file at its 3.9 MB cap, named): after the flight, and not
  hoax evidence under any reading.
- Mars 2020: “127 million miles (204 million km)”. 127M mi is
  204.39M km; Horizons says 204.55M km, which rounds to **205** — the
  printed 204 is the miles rounded once, converted, rounded again
  (b1 M16/M17).
- Artemis maximum distance “268,563 mi” vs Horizons geocentric maximum
  **438,625.66 km**: Δ 6,415.4 km ≈ one Earth radius + 37 km — the
  reference point (geocenter or surface) is undeclared. Surface-
  referenced, NASA's number reproduces as 432,247.5 km (268,586 mi),
  and the evening reading “268,457 mi” carries the same offset within
  1.1 km (b1 M18/M19/M20): self-consistent, not declared.
- ALSJ sun angles run **0.01–0.12°** above Horizons: elevation printed
  11.37° at 21:34:42 UTC vs Horizons 11.357187° (azimuth 88.81 = 88.81
  exact); the EVA table's 14.0° / 15.4° vs Horizons 13.881° / 15.282° —
  the same +0.12° at both ends of a table quantized to quarter-hour GET
  with its model undeclared (b1 M29a–M29f). The ALSJ-vs-Horizons
  residual is published as unresolved: this study does not attribute
  error beyond what the sources declare.

**Three gate limits — ours.**

- `date_calc` counted **120 s** between 23:59:00Z and 00:01:00Z across
  the 2016 leap second: POSIX seconds, scale undeclared, gold 121
  (b4 D8, sha `2fd48aa4…`).
- `check_format` refused `2016-12-31T23:59:60Z`, a real inserted leap
  second, while its own contract said “leap second allowed” (b6 F1,
  sha `49f778eb…`).
- `date_parse` refused the same label; no leap-second table existed
  anywhere in the time family (b7 P1, sha `360468b3…`).

## What held up

Light-times to four decimals (1.2947 / 1.2992 s = Horizons); the whole
GET→UTC chain (landing 102:45:40 → 20:17:40 UTC, and the truncated
printed 20:17:39.9; splashdown 195:18:35 → 1969-07-24 16:50:35 — b4e,
sha `e72a3222…`); the zone-dependent date of the first step (22:56:15
EDT on 20 July and 03:56:15 Paris on 21 July — both correct, the zone
decides); shadows (7.04 m at 11.37° → 35.01 m; ~25 m at 05:43 UTC →
25.38 by the door's series workaround, b2 sha `e14d20c9…`); the Mars
OWLT chain (touchdown SCET + 682 s = ERT = NASA's own “11 minutes 22
seconds”); TT−UTC against Horizons TDB−UT for 1969/2021/2022 within
0.0013 s under the declared |TDB−TT| ≤ 0.0017 s bound (b1 M22–M25, b8
R3); and the provenance control on the 1969 plan PDF: created
1999-10-30, modified 2015-09-02 — scan dates, which is a neutral fact
against any “written later” claim about the document's contents.

## What this does not prove

- Whether anyone walked on the Moon. This is arithmetic on published
  numbers against a named model (DE441). The landing's own figures
  passed their own checks — that is the measurement, nothing more.
- That a printed rounding is a lie. 432,194 vs 432,210 km is a
  conversion artifact in a press kit; “204 vs 205 million km” is double
  rounding. Both are sloppy, neither is falsified: the underlying
  quantities hold.
- That ALSJ is wrong or Horizons is right: ALSJ's ephemeris and site
  model are undeclared, and the +0.12° residual stays open.
- Nothing about adjacent genres of claim: only numeric claims were in
  scope. No image, flag, tape or motive was analyzed.

## The next day (replayed 2026-11-27, door 1.48.1 → 1.56.0)

A case study is a dated measurement. Re-running the door's own failures
the next morning moved two of them:

- `units_convert` now keeps trailing zeros: `432194 km → "268552.90"`
  (batch sha `d0376e41…`) — the inconsistency measured on 11-26 against
  `math_calc` did not reproduce.
- `check_format` no longer refuses the leap label: it answers
  `valid=true` with a named `leap_second_paths` field and the note
  “POSIX/ISO civil time cannot render this instant — existence of the
  insertion is NOT judged here, never certified” (sha `2e8a98a4…`). It
  gives the identical answer for `2015-12-31T23:59:60Z`, which never
  occurred: the grammar question moved, the existence question is still
  a table nobody ships.
- `date_parse`'s refusal now names the missing table in its own message
  (`utc_tt_offset_named_table, at the door`). Probed the same hour:
  `/tools/utc_tt_offset_named_table.json` → **404**. An error pointing
  at a tool that is not there is its own bug class, recorded.
- `date_calc` no longer accepts `unit: seconds` in diffs (the enum is
  now named `days|business_days|human|calendar`), so the 120-vs-121
  POSIX result stays in the 11-26 ledger at its batch sha, not
  re-asserted today. Its mission-clock grammar still lands:
  1969-07-16T13:32Z + `T102h45M40s` → 1969-07-20T20:17:40+00:00 (sha
  `9d3261e3…`).
- The survey's two proposals — `utc_tt_offset_named_table` (request sha
  `486c7f55…`, gate sha `bc9e1f2e…`) and `shadow_length_sun_elevation`
  (`53cbdfc8…` / `3e025c90…`), both returned **SUSPECT-DUPLICATE** and
  accepted as rendered, no rewording, no re-post — were both still 404
  on `/tools/` at replay time.
- Horizons re-queried live: Moon geocentric delta at the landing instant
  = 0.00260367423959 AU = **389,504.1 km**, light-time **1.2992 s** —
  check #2 of the survey reproduced to four decimals from the primary
  source, a day later, from a different machine.

## Control methodology

1. Every arithmetic check at the door — including the two that proved
   hand-traced golds wrong, which were then corrected, not argued.
2. Every CONTRADICTED classified (claim false / printed artifact / gate
   limit) before publication; the extraction-artifact class searched and
   reported at zero.
3. Reference queries pinned with the headers that make them replayable
   (DE441, CENTER=500@399, TIME_TYPE=UT, airless).
4. Source failures travel named: a 403 page is an excerpt-only citation,
   a TLS-refused page is disclosed, an over-cap PDF stays `pdfinfo`-local.
5. Both gate verdicts stand as rendered; arbitration is a human lane and
   stayed there.
6. A next-day replay is part of the method: two published door bugs no
   longer reproduce, and that is in the document, not under it.
7. Numbers cited from the survey were re-derived where bytes allow
   (the 101-vs-103 payload-line mismatch is named; light-times,
   conversions and ratios re-computed live, appendix).

## Appendix — replay it yourself

```bash
# JPL Horizons, landing epoch (replayed 2026-11-27)
curl -s "https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND='301'&OBJ_DATA=NO&MAKE_EPHEM=YES&EPHEM_TYPE=OBSERVER&CENTER=500@399&START_TIME=1969-07-20%2020:17:40&STOP_TIME=1969-07-20%2020:17:41&STEP_SIZE=1%20m&QUANTITIES=20&TIME_TYPE=UT" | grep "1969-Jul-20 20:17:40"
# 0.00260367423959 AU x 149597870.7 = 389,504.1 km; /c = 1.2992 s one-way

# the two false claims, one door call (replayed 2026-11-27,
# batch sha fdfe3a97ef22b7b1173ae2c9a73e3822fe4e50284679447e8fe0a0a218964173)
curl -s -X POST https://mechacut.studio/api/v1/batch \
  -H "Content-Type: application/json" \
  -d '{"tool":"math_calc","payloads":[
       {"expr":"2*388152/299792.458","digits":3},
       {"expr":"round(2*400000/299792.458, 3)"},
       {"expr":"0.5*299792.458/2","digits":1},
       {"expr":"round(93800000/242026.6,1)"}]}'
# 2.589 s round trip · 2.669 s at the claimed distance ·
# a 0.5 s claim implies 74,948.1 km · the 1977 claim overshoots 387.6x

# NASA's own parenthetical, converted both ways (batch sha d0376e41…)
curl -s -X POST https://mechacut.studio/api/v1/batch \
  -H "Content-Type: application/json" \
  -d '{"tool":"units_convert","payloads":[
       {"value":"268563","from":"mi","to":"km","places":2},
       {"value":"432194","from":"km","to":"mi","places":2}]}'

# the leap second, as today's door answers it (batch sha 2e8a98a4…)
curl -s -X POST https://mechacut.studio/api/v1/batch \
  -H "Content-Type: application/json" \
  -d '{"tool":"check_format","payloads":[
       {"payload":{"x":"2016-12-31T23:59:60Z"},"formats":{"$.x":"datetime-iso"}}]}'

# survey batch shas (2026-11-26): b1 e822f5d2… b2 e14d20c9… b3 14ef270a…
# b4 2fd48aa4… b4e e72a3222… b5 c7a3a867… b6 49f778eb… b7 360468b3…
# b8 28931a70…  pdf p1 97a0f046…
```

*The survey's working files (Horizons outputs, sources, batch log,
SHA256SUMS) stay with the wave-2 reports outside this repository; the
shas above identify them. Evidence section: compilation lines
1735–1962, report sha256 `892e46fd…`.*
