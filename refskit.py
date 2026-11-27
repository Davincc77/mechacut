# -*- coding: utf-8 -*-
"""refs_biblio_scan — le maillon absent : chaine de reference BRUTE ->
champs + ids extraits, chaque id rendu avec le controle qui LUI est
publie (registre L68, recu f4a7a9904e766db6, ADMIS 27-11 — audit
contrat-contre-contrat : id_checkdigit verifie un id DONNE, check_refs
est un autre service, doi_name_equivalence (L16, bundle 146 SHIPPED)
est l'etape SUIVANTE, pas la precedente).

Contrat d'admission : parsing de chaines de reference brutes -> champs
+ ids extraits avec check digits (ISBN, ISSN mod-11 avec X final, DOI
grammaire 10.PREFIX/SUFFIX, arXiv YYMM.NNNNN | arch-ive). PAS de
resolution reseau : la porte ne questionne ni Crossref, ni doi.org —
l'equivalence de noms DOI vit deja ailleurs, mariee ici sans etre
dupliquee : le dossier doi extrait est le RECORD de doikit.parse_doi,
le MEME objet que rend /api/v1/id/doi-equivalence (bundle 146).

References publiees nommees (aucune inventee) :
  - ISBN : ISO 2108 — ISBN-10 = somme ponderee 10..1 mod-11, X = 10 en
    finale ; ISBN-13 = mod-10, poids alternes 1,3 (EAN-13), prefices
    978/979. Exemples publies canoniques (article « International
    Standard Book Number », exemples de controle) : 978-0-306-40615-7
    et 0-306-40615-2 (MEME livre, deux formes) ; 0-8044-2957-X (X de
    controle).
  - ISSN : ISO 3297 — 8 chiffres, poids 8..2, mod-11, X final. Gold :
    1932-6203 = PLOS ONE (ISSN Portal, « ISSN Record 1932-6203 — PloS
    one », https://portal.issn.org/resource/ISSN/1932-6203, consulte
    27-11) ; 1932-6204 = cle mutilee, attendue 3.
  - DOI : DOI Handbook, DOI Foundation, publication date September 2025
    (sha256 1f6c73c12890a8bef8f30d06a7fe1de90723318e796bfff68d4a6475
    9b4ddcf3 — meme primaire que bundle 146) §4.3 : grammaire
    10.PREFIXE/SUFFIXE ; §4.3.5 : « the DOI System does not itself make
    use of check digits » — JAMAIS de somme de controle inventee ici.
  - arXiv : arXiv identifier help (https://arxiv.org/help/formats) —
    nouveau « YYMM.NNNNN » (arXiv commence avril 1991 : YY 91..99 ->
    19YY, 00..90 -> 20YY), ancien « arch-ive/YYMMNNN », archives
    publiques nommees (liste fermee).
  - Gold PLOS ONE reel : Catenacci DVT, Liao W-L, Thyparambil S,
    Henderson L, Xu P, et al. (2014) Absolute Quantitation of Met
    Using Mass Spectrometry for Clinical Application: Assay
    Precision, Stability, and Correlation with MET Gene Amplification
    in FFPE Tumor Tissue. PLoS ONE 9(7): e100586.
    doi:10.1371/journal.pone.0100586 — recopie LITTERALE du bloc
    « Citation: » du PDF publie (journals.plos.org, file
    ?type=printable&id=10.1371/journal.pone.0100586, consulte 27-11).

Grammaire des champs (MAISON, dite) : « Auteurs (YYYY) Titre. Revue
V(I): locator. » — le premier « . » apres (YYYY) coupe titre et venue ;
un titre contenant un point abbrevatif coupe mal : limite nommee du
grammaire, pas un defaut silencieur. Sans match : parse NO_MATCH nomme,
les ids restent extraits — la porte ne devore jamais un champ qu'elle
ne peut pas citer.
"""
import re

import doikit

REF_DOI = ("DOI Handbook (DOI Foundation, publication date September "
           "2025, PDF sha256 1f6c73c12890a8bef8f30d06a7fe1de9072331"
           "8e796bfff68d4a64759b4ddcf3) §4.3 — grammar 10.PREFIX/"
           "SUFFIX; §4.3.5 no check digit exists, none is invented")
REF_ISBN = ("ISO 2108 — ISBN-10 check = sum(d_i * (10-i)) mod 11 over "
            "the first 9 digits, 10 rendered X final; ISBN-13 check = "
            "mod-10 alternating weights 1,3 (EAN-13), prefixes 978/"
            "979. Published examples replayed: 978-0-306-40615-7 = "
            "0-306-40615-2 (same book, two forms); 0-8044-2957-X (X "
            "check digit)")
REF_ISSN = ("ISO 3297 — ISSN check = (11 - sum(d_i * (8-i)) mod 11) "
            "mod 11 over the first 7 digits, 10 rendered X final. "
            "Gold cited: 1932-6203 = PLOS ONE (ISSN Portal record "
            "1932-6203, consulted 27-11); 1932-6204 fails — expected "
            "check 3. Capture rule (house, said): 4-3+[dX] blocks are "
            "claimed as ISSN; ISBN digits are claimed only after an "
            "ISBN label or as bare 978/979 blocks — an unlabelled "
            "digit soup is never invented")
REF_ARXIV = ("arXiv identifier grammar (arxiv.org/help/formats): new "
             "YYMM.NNNNN — arXiv began 1991-04, so YY 91..99 = 19YY "
             "and YY 00..90 = 20YY, MM 01..12, 4 or 5 digits; old "
             "arch-ive/YYMMNNN over the CLOSED published archive list "
             "below; a trailing vN version marker is kept and named")
REF_FIELDS = ("house field grammar: 'Auteurs (YYYY) Titre. Venue "
              "Volume(Issue): Locator.' — the first sentence period "
              "after (YYYY) splits title from venue; no match is a "
              "NAMED parse status, never a guessed split; ids are "
              "extracted either way")

# Liste fermee des archives heritables publiees par arXiv (help/formats)
LEGACY_ARCHIVES = frozenset((
    "acc-diff", "acc-phys", "adalg", "adaporg", "adapo", "aihp", "alg-gag",
    "analysis-pf", "ao-sci", "aope", "arep", "astro-ph", "atom-ph",
    "chem-web", "chao-dyn", "cmp-gd", "cmp-gn", "cmp-lg", "cmp-met",
    "cnu-dyn", "cnu-th", "cond-mat", "difsys-dyn", "dyn-sys", "emp-arg",
    "funct-an", "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th",
    "iri-quad", "math", "math-ph", "mth-cd", "nlin", "nlin-ao", "nlin-cd",
    "nlin-ps", "nlin-si", "nucl-ex", "nucl-th", "patt-sol", "q-alg",
    "q-bio", "q-bio-bm", "q-bio-cb", "q-bio-gn", "q-bio-mn", "q-bio-nc",
    "q-bio-pe", "q-bio-pf", "q-bio-qm", "q-fin", "q-fin-cp", "q-fin-eq",
    "q-fin-gn", "q-fin-mc", "q-fin-pm", "q-fin-pr", "q-fin-rm", "q-fin-st",
    "q-fin-tr", "q-ph", "quant-ph", "solv-int", "sndy", "supr-con",
))
_MONTHS = frozenset(range(1, 13))
_XISBN_LABEL = re.compile(r"\bISBN\s*[:\-]?\s*([0-9Xx][0-9Xx \u2010-\u2015-]{8,16}[0-9Xx])",
                          re.IGNORECASE)
_BARE13 = re.compile(r"(?<![\dXx-])(97[89][\d -]{10,13}\d)(?![\dXx-])")
_ISSN_RE = re.compile(r"(?<![\dXx-])(\d{4})-(\d{3})([\dXx])(?![\dXx])")
_DOI_RE = re.compile(
    r"(?:(?P<label>doi\s*:\s*)|(?P<url>https?://(?:dx\.)?doi\.org/))?"
    r"(?P<name>10\.\d{2,9}/[^\s;,)\]]+)", re.IGNORECASE)
_ARX_NEW = re.compile(r"(?<![\d.])(\d{4})\.(\d{4,5})(v\d+)?(?!\d)")
_ARX_OLD = re.compile(r"(?<![\w./-])([a-z][a-z-]*(?:\.[A-Za-z][A-Za-z0-9-]*)?)"
                      r"/(\d{7})(v\d+)?(?!\d)")
_FIELD_RE = re.compile(
    r"^(?P<authors>.+?)\s*\((?P<year>\d{4})\)\s*"
    r"(?P<title>.+?)\.\s+"
    r"(?P<venue>[^\s][^.]*?)\s+(?P<volume>\d{1,3})(?:\((?P<issue>[^)]{1,12})\))?"
    r"\s*:\s*(?P<locator>e\d{3,}|[A-Za-z]?\d+(?:[\u2013-]\d+)?)[.,;]?"
    r"(?:\s.*|\Z)", re.S)


class RefsKitError(Exception):
    def __init__(self, field, msg):
        self.field = field
        self.msg = msg
        super().__init__(msg)


def _isbn10_ok(d):
    s = sum((10 - i) * (10 if c == "X" else int(c))
            for i, c in enumerate(d))
    return s % 11 == 0


def _isbn10_expected(d9):
    r = sum((10 - i) * int(c) for i, c in enumerate(d9)) % 11
    v = (11 - r) % 11
    return "X" if v == 10 else str(v)


def _isbn13_expected(d12):
    r = sum(int(c) * (1 if i % 2 == 0 else 3)
            for i, c in enumerate(d12)) % 10
    return str((10 - r) % 10)


def _issn_expected(d7):
    r = sum((8 - i) * int(c) for i, c in enumerate(d7)) % 11
    v = (11 - r) % 11
    return "X" if v == 10 else str(v)


def _check_arxiv_new(yymm, nn, version):
    yy, mm = int(yymm[:2]), int(yymm[2:])
    errs = []
    if 91 <= yy:
        full_year = 1900 + yy
    elif 0 <= yy <= 90:
        full_year = 2000 + yy
    else:  # unreachable, kept closed
        full_year = None
    if not (1 <= mm <= 12):
        errs.append("arxiv_month_out_of_range")
    if not (4 <= len(nn) <= 5):
        errs.append("arxiv_serial_length")
    return {"kind": "arxiv", "raw": yymm + "." + nn,
            "normalized": yymm + "." + nn,
            "form": "new", "year": full_year, "month": mm,
            "serial_digits": len(nn),
            "version": version,
            "has_check_digit": False,
            "errors": errs, "valid": not errs}


def _check_arxiv_old(archive, digits, version):
    errs = []
    base = archive
    if archive not in LEGACY_ARCHIVES and \
            archive.split(".")[0] not in LEGACY_ARCHIVES:
        errs.append("arxiv_archive_not_in_published_list")
    yy, mm = int(digits[:2]), int(digits[2:4])
    if not (1 <= mm <= 12):
        errs.append("arxiv_month_out_of_range")
    return {"kind": "arxiv", "raw": archive + "/" + digits,
            "normalized": archive + "/" + digits,
            "form": "legacy", "archive": base,
            "year": 1900 + yy if yy >= 91 else 2000 + yy,
            "month": mm, "serial": digits[4:],
            "version": version,
            "has_check_digit": False,
            "errors": errs, "valid": not errs}


def _scan_ids(text):
    ids, seen = [], set()

    def push(at, rec):
        key = (rec["kind"], rec["normalized"])
        if key in seen:
            return
        seen.add(key)
        rec["at"] = at
        ids.append(rec)

    for m in _DOI_RE.finditer(text):
        cand = m.group(0)
        tail_strip = ""
        while cand and cand[-1] in ".,;:)":
            tail_strip = cand[-1] + tail_strip
            cand = cand[:-1]
        if m.group("label"):
            # hand the label form to doikit in its canonical spelling —
            # "doi : " with spaces is the same label, said not silent;
            # the punctuation trim applies to the NAME, not the label
            cand = "doi:" + m.group("name").rstrip(".,;:)")
            tail_strip = m.group("name")[len(m.group("name").
                                           rstrip(".,;:)")):] or \
                tail_strip
        side = doikit.parse_doi(cand)
        rec = {"kind": "doi", "raw": m.group(0),
               "normalized": side["name"] or cand,
               "doi_form": side["form"], "prefix": side["prefix"],
               "registrant_code": side["registrant_code"],
               "suffix": side["suffix"], "valid": side["valid"],
               "errors": list(side["errors"]),
               "has_check_digit": False,
               "check_digit_rule": "DOI Handbook §4.3.5 — the DOI "
                                   "System makes no use of check "
                                   "digits; none is computed here",
               "next_door": "/api/v1/id/doi-equivalence (bundle 146) — "
                            "name equivalence is judged there, not "
                            "duplicated here"}
        if tail_strip:
            rec["trailing_punct_trimmed"] = tail_strip
        push(m.start(), rec)

    for m in _XISBN_LABEL.finditer(text):
        raw_digits = re.sub(r"[ \u2010-\u2015-]", "", m.group(1)).upper()
        push(m.start(), _isbn_record(m.group(0), raw_digits, "label"))
    for m in _BARE13.finditer(text):
        raw_digits = re.sub(r"[ \u2010-\u2015-]", "", m.group(1))
        if raw_digits.startswith(("978", "979")) and len(raw_digits) == 13:
            push(m.start(), _isbn_record(m.group(0), raw_digits,
                                         "bare-978/979"))

    for m in _ISSN_RE.finditer(text):
        d7 = m.group(1) + m.group(2)
        exp = _issn_expected(d7)
        got = m.group(3).upper()
        push(m.start(), {"kind": "issn", "raw": m.group(0),
                         "normalized": m.group(1) + "-" + m.group(2) + got,
                         "valid": got == exp,
                         "has_check_digit": True,
                         "check_algorithm": "mod-11 weights 8..2, X=10 (ISO 3297)",
                         "expected_check": exp,
                         "observed_check": got,
                         "errors": ([] if got == exp else
                                    ["issn_check_digit_mismatch"])})
    return ids


def _isbn_record(raw, digits, via):
    rec = {"kind": "isbn", "raw": raw, "normalized": digits,
           "digits": len(digits), "via": via, "has_check_digit": True}
    if len(digits) == 10:
        rec["variant"] = "isbn10"
        rec["check_algorithm"] = "mod-11 weights 10..1, X=10 (ISO 2108)"
        exp = _isbn10_expected(digits[:9])
        ok = _isbn10_ok(digits)
        rec["expected_check"] = exp
        rec["observed_check"] = digits[9]
        rec["valid"] = ok
        rec["errors"] = [] if ok else ["isbn10_check_digit_mismatch"]
    elif len(digits) == 13:
        rec["variant"] = "isbn13"
        rec["check_algorithm"] = "mod-10 alternating weights 1,3 (EAN-13)"
        if not digits.startswith(("978", "979")):
            rec["valid"] = False
            rec["errors"] = ["isbn13_prefix_not_978_979"]
            return rec
        exp = _isbn13_expected(digits[:12])
        rec["expected_check"] = exp
        rec["observed_check"] = digits[12]
        rec["valid"] = digits[12] == exp
        rec["errors"] = [] if rec["valid"] else ["isbn13_check_digit_mismatch"]
    else:
        rec["variant"] = None
        rec["valid"] = False
        rec["errors"] = ["isbn_digit_count_%d" % len(digits)]
    return rec


def _scan_arxiv(text, ids, seen):
    for m in _ARX_NEW.finditer(text):
        key = ("arxiv", m.group(1) + "." + m.group(2))
        if key in seen:
            continue
        seen.add(key)
        rec = _check_arxiv_new(m.group(1), m.group(2), m.group(3))
        rec["at"] = m.start()
        ids.append(rec)
    for m in _ARX_OLD.finditer(text):
        key = ("arxiv", m.group(1) + "/" + m.group(2))
        if key in seen:
            continue
        seen.add(key)
        rec = _check_arxiv_old(m.group(1), m.group(2), m.group(3))
        rec["at"] = m.start()
        ids.append(rec)


def _parse_fields(text):
    m = _FIELD_RE.match(text)
    if not m:
        return {"status": "NO_MATCH", "fields": None}, []
    f = m.groupdict()
    missing = [k for k in ("authors", "year", "title", "venue",
                           "volume", "issue", "locator")
               if f.get(k) in (None, "")]
    return {"status": "FIELD_GRAMMAR_MATCH", "fields": f}, missing


def scan_one(ref):
    raw = ref
    s = ref.strip()
    applied = []
    if s != raw:
        applied.append("outer_whitespace_trimmed")
    out = {"raw": raw, "trimmed": s != raw}
    parsed, missing = _parse_fields(s)
    out["parse"] = parsed
    out["fields"] = parsed["fields"]
    out["missing_fields"] = missing if parsed["fields"] else \
        ["authors", "year", "title", "venue", "volume", "issue",
         "locator"]
    ids = _scan_ids(s)
    seen = {(r["kind"], r["normalized"]) for r in ids}
    _scan_arxiv(s, ids, seen)
    ids.sort(key=lambda r: r["at"])
    out["ids"] = ids
    # accords interchamps NOMMES (jamais des corrections)
    obs = []
    f = parsed["fields"]
    if f and f.get("locator") and f["locator"].startswith("e") \
            and f["locator"][1:].isdigit():
        for r in ids:
            if r["kind"] == "doi" and r["suffix"] and \
                    r["suffix"].endswith(f["locator"][1:]):
                obs.append("elocator_appears_in_doi_suffix:" +
                           f["locator"])
    out["observations"] = obs
    out["applied_defaults"] = applied
    return out, applied


def scan(refs):
    if not isinstance(refs, list):
        raise RefsKitError(
            "refs", "refs: a list of raw reference strings (1..100) — "
            "this door parses cited text, it never fetches a document")
    if not (1 <= len(refs) <= 100):
        raise RefsKitError(
            "refs", "refs: 1..100 strings — beyond 100 the batch door "
            "(/api/v1/batch) is the contract, not a fatter request")
    for i, r in enumerate(refs):
        if not isinstance(r, str):
            raise RefsKitError(
                "refs[%d]" % i, "refs[%d]: a string — shapes are "
                "refused by name, never coerced" % i)
    results, defaults = [], []
    for r in refs:
        one, ap = scan_one(r)
        results.append(one)
        defaults += ap
    ids = [d for x in results for d in x["ids"]]
    return {
        "refs_in": len(refs),
        "results": results,
        "counts": {
            "ids_found": len(ids),
            "ids_by_kind": {k: sum(1 for d in ids if d["kind"] == k)
                            for k in sorted({d["kind"] for d in ids})},
            "ids_valid": sum(1 for d in ids if d["valid"]),
            "ids_invalid": sum(1 for d in ids if not d["valid"]),
        },
        "rules": {"fields": REF_FIELDS, "isbn": REF_ISBN,
                  "issn": REF_ISSN, "doi": REF_DOI, "arxiv": REF_ARXIV},
        "boundary": "no network: extraction + published check digits "
                    "only — DOI name equivalence is the shipped "
                    "sibling /api/v1/id/doi-equivalence (bundle 146), "
                    "resolution (Crossref) belongs to neither door; "
                    "an id whose grammar or check fails is NAMED with "
                    "the expected digit, never silently repaired",
        "applied_defaults": sorted(set(defaults)),
    }
