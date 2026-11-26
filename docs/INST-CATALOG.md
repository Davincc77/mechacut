# Institutional Verification Catalog

What a deterministic document bench checks for institutions, sector by sector: the legal
basis, the exact mechanical test, the documented money behind it. Existence proof first —
the LATAM case study (`docs/CASE-STUDY-TICKET.md`, ledgers in `docs/corpus/`) shows a
frozen template defect surviving eight years across 720 of 1,105 public-records tickets
because nobody hashes what an institution signs. This catalog is that check, generalized.

**The invariant law.** Every institutional document splits into three columns:
*computation* (arithmetic/grammar byte-in — a bench can own it forever), *registry*
(oracle lookups — the bench names the source and caches honestly), *human* (judgment —
the bench refuses it by name). We sell the first column at machine price, instrument the
second, and never pretend the third is ours.

Status legend: **[P]** = figure or artefact replayed by the parent from primary in this
session; **[L]** = ledger-sourced (subagent, source URL live, flagged in `gaps` below).

---

## 1 · Governments

| Domain | Legal basis (primary) | The deterministic test | The money |
|---|---|---|---|
| EU e-invoicing (B2G) | Directive 2014/55/EU; EN 16931 | **223 business rules** in the official Schematron (58 core BR, 23 BR-CO arithmetic: VAT = taxable×rate/100 rounded 2dp, gross = net+VAT) — counted by us from the EC artefact | EU VAT gap **€128.4 bn** (2023, EC) **[P]**; MTIC €12.5–32.8 bn/yr (EC study) **[L]** |
| France e-invoicing | Ordonnance 2021-1190; CGI art. 289 bis; Annex II art. 242 nonies A | ~16 mandatory mentions = presence/format; DGFiP `REJET` on HT/TVA/TTC incoherence; date×size predicate (receive 09/2026 all; issue 09/2026 GE/ETI, 09/2027 PME/TPE) | €50/fault per missing e-invoice, cap €15 k/yr (art. 1737 III, Legifrance) **[L]**; >10 M economic actors in scope **[L]** |
| Italy SdI | DM 55/2013; ADE Allegato A v1.7.1 | 32 enumerated 5-digit rejection codes; arithmetic coherence (imponibile×aliquota=IVA, quoted); hash stamped on every delivery receipt — the state already verifies by hash | IT VAT gap €25.0 bn (15.0 %) (EC) **[L]** |
| Poland KSeF | VAT act art. 106a; phased 02/2026– | the invoice IS a government XML artefact: schema FA, 36-char reference, signed UPO receipt; penalties from 01/2027 | PL VAT gap €10.5 bn, worsening +4.8 pp (EC) **[L]** |
| India IRN | CGST r.46/50; CBIC 10/2023 | IRN = **NIC-generated SHA-256 of the invoice identity tuple**, queryable by hash — a government doing our job's philosophy at national scale | — **[L]** (geo-blocked primary; mirrored, flagged) |
| Brazil NF-e | AJUSTE SINIEF 7/05; ENCAT NT CJ 2025.001 | chave = 44 fixed positions + mod-11 DV — offline-verifiable, billions/yr; rejection code 402 = encoding ⇒ fiscal nullity (verified end-to-end in the LATAM study) | ANAC R$725.76 M in unpaid aviation fines (replay **[P]**) |
| Customs | UCC + Reg 414/2009 Annex VII; Reg 2658/87 art. 3 | **MRN: 18 chars + check digit — verified verbatim** from the regulation **[P]**; CN 6/8/10-digit grammar; EUR.1 fixed 12-box form | OLAF 2024: €623 M impact; one e-bike scheme €120 M duties + €80 M VAT **[L]** |
| Public audit | ECA annual reports; TED eForms rules R2.0.9 | eForms pre-validated by 231+ machine rules before publication (the EU already runs a bench — the audit trail is the gap) | EU budget error rate **5.6 %** of €191.2 bn (ECA) **[L]** |
| Apostille / civil | HCCH 1961 art. 4/7 | model certificate = 10 fixed fields (French title mandated); art. 7 **requires an issuing register** — a legally mandated re-verification API run by hand today | — **[L]** |

## 2 · Financial institutions

| Domain | Basis | Test | Money |
|---|---|---|---|
| BEC / invoice redirection | FBI IC3 | **re-issued "same" invoice PDF, swapped IBAN** → hash-at-issue + byte-diff of payment blocks; payee identifiers (IBAN mod-97 shipped, BIC/CI/ABA formats) | BEC **$2,770,151,146** across 21,442 complaints (IC3 2024 — table read from the primary PDF **[P]**); three-year $8.46 bn **[P]**; cumulative $55.5 bn 2013-23 **[L]** |
| Recordkeeping | SEC/CFTC/FCA | hash-anchored audit trails, examiner-ready | SEC: **16 firms, $1.1 bn+ — verified verbatim on sec.gov [P]**; CFTC $710 M **[L]**; FCA/UBS £27.6 M, 135.8 M defective transaction reports **[L]** |
| KYC onboarding | internal, per-bank | per-document hash proof-of-existence at issuance; ID checksums (shipped family) | $1,501–3,500 per client review, two-thirds of banks (Fenergo) **[L]**; 95-day average review (Quantexa) **[L]** |
| Underwriting | Fannie Mae B3-3.2-01 | the guide's own hard field checklist (paystub ≤30 days, YTD math per frequency) as a rule pack — deterministic text already in the payslip bench | ~$11.6 k cost-to-originate per loan (Freddie Mac) **[L]** |
| AP / duplicates | trustmi/ARDD | **61 % of double-paid invoices had NON-identical numbers, 8/10 passed PO match** — exact-number matching is the flaw; deterministic fuzzy fingerprint (normalized text + arithmetic) fixes it | manual invoice $12.44 vs $5.13 automated (MineralTree) **[L]**; duplicates 0.8–2 % of disbursements (APQC) **[L]** |
| SEPA / ISO 20022 | EPC262-08 v11.0; SWIFT CBPR+ | Creditor Identifier country formats + DVs; pacs.00x field rules; MT→MX rejects are deterministic events | 44 % of banks off-track Nov-2026 (RedCompass) **[L]**; ~1,600 manual repairs/day (0.1 % of 1.6 M msgs) **[L]** |
| Brazil rails | Febraban layouts (Banrisul PDR 240) | boleto: 47-digit linha digitável ↔ barcode, mod-10/mod-11 DVs, duplo dígito variant — bank-published arithmetic, **not yet in mechacut** | — |
| Supervisory | EBA validation rules XLSX; ECB AnaCredit + sanction methodology (ECB/2022/31/32) | the regulator's own rule sheets ARE the product spec: thousands of executable IF-THEN checks, published free | AnaCredit defects tariffed since 30/04/2024, sanctions published **[L]** |

## 3 · Professions

| Domain | Basis | Test | Money |
|---|---|---|---|
| US federal courts | CM/ECF; CAFC gate | PDF flattened, text-searchable, no JS/encryption — a machine gate courts already enforce; CAFC ships its own checker | rejected filings = missed deadlines **[L]** |
| US evidence | **FRE 902(13)-(14)** (2017) | hash equality is *self-authenticating evidence* — the Advisory Committee note says identical hashes "reliably attest" exact duplicates. The US rules of evidence endorse the bench's core primitive **[P-adjacent: rule text read]** | per-exhibit forensic authentication cost removed |
| France avocats/admin | CPC 930-1 (RPVA); CJA R.414-1; cass. 20-10.522 | transmission receipts, per-page watermark arithmetic, inventaire↔pièces consistency — inadmissibility d'office for non-electronic acts | — |
| Germany | § 130a ZPO + ERVV | version whitelist (PDF/A-1/-2, PDF/UA), embedded fonts, no JS — format = admissibility | wrong format = deadline lost **[L]** |
| Late payment (FR) | C. com. L441-9/10/16 | field presence + due-date arithmetic vs 60/45-day caps + €40 indemnity + interest recompute + SIREN checksum | **217 amendes, €35,793,050, 42.3 % anomaly rate (737 controls); 92 % of 38 court decisions upheld** — all read from Banque de France ODP-2024 primary + senat.fr **[P]** |
| Sworn translation | FR decree 2004-1463 (CA lists H.1/H.2), DE GDT + Länder, NL Rbtv, BR Decreto 13.609 art. 19/32 | oath wording + matrícula/register number well-formedness + hash-at-issue; **registry column: the four public lists are lookup oracles** — fidelity stays human, named | mis-hired translator voids the exhibit (FR) **[L]** |
| Insurance | CA DOI / NAIC / FBI | duplicate claim by file hash, altered-form byte-diff, prompt-pay deadline arithmetic | CA DOI 2025: $527.8 M reviewed claims, $458.3 M suspected; FBI: non-health fraud >$40 bn/yr **[L]** |
| Notarial | FR décret 71-941 art. 16-17; RON US (47 states) | PAdES/QES chain + timestamp validation in-bytes; notarial-block field presence + commission-expiry arithmetic — **a seal's authority can never be a checksum; we say so** | an emailed "signed" PDF is not an acte authentique |

## The whitespace (market, stated honestly)

Rule-validation is already commoditized: **€0.0025–0.01 per invoice** at published API
prices (SUPER PDP) — the deterministic check is cheap and everyone knows it now. What
**no** surveyed vendor sells: per-document **hash anchoring at issuance + third-party
re-verification + published jurisdiction rule packs + examiner-ready export** as one
curlable contract. Generic anchoring exists (OpenTimestamps free, OriginStamp freemium)
with zero compliance framing; KYC vendors re-check via ML per event. The slot is the
column every regulator already made deterministic and nobody priced.

## Honest gaps (kept, not buried)

NIC endpoints geo-blocked (IRN formula via integrator mirror, flagged); no EU check-digit
for EORI (registry lookup only); no consolidated apostille-fraud or India-GST-fraud
totals exist publicly; Compodium/Sovos/Pagero price on request; legifrance/ic3/economie
answer 403/999 to bare curl (browser-reachable, primary tables quoted above);
"Qonding"/"Tricube" untraceable as vendors; 'BEAMA' false-invoice stat untraceable —
replaced by UK Finance/Home Office ECS 2024 figures. Counts of EN 16931 rule families
differ across subagent reports (201 vs 223): the parent's own count of the official
preprocessed artefact governs — 223 unique BR ids / 58 core / 23 CO.

## The loop, applied here

This research was itself a repetition of the LATAM protocol ×3 — which is the point.
Five new transform candidates came out of doing it (see `docs/TRANSFORM-CANDIDATES.md`
rows 1–12): boleto/DV family, MRN, creditor identifier, EN 16931 arithmetic subset,
pdf_provenance, stats_rate_ci, text_mojibake profile. Money follows admission — the
catalog ships before any of them is priced.
