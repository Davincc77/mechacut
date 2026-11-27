# -*- coding: utf-8 -*-
"""doi_name_equivalence — la règle DOI qui manquait à la porte.

Contrat d'admission (registre L16, reçu proposeur a4ba4e61…ea62) : la
compilation des rapports de campagne, lignes 448-532 — « says whether
two DOI strings name the SAME DOI under DOI Handbook §4.3 (case-
insensitive over ASCII only, prefix/suffix split, doi:/doi.org/dx.doi.org
forms stripped) and validates DOI grammar ». Mesure du segment : les
4 formes écrites d'un même DOI rendent 4/3/4 distincts par
text_url_canonical + list_dedupe (gold 1, gate 95e20bec) ; §4.3.4 Ex.2
Á/á MERGÉ a tort par le mode texte, Ex.1 S/s SPLIT a tort par exact ;
/route q=doi NO_MATCH ; check_format refuse le format « doi » par son
nom. Outils corrects sous leurs contrats -> maillon absent, pas bogue.

Reference publiee nommee (version citee) :
  DOI Handbook, DOI Foundation, publication date September 2025
  https://www.doi.org/doi-handbook/DOIHandbook_2025.pdf
  sha256 1f6c73c12890a8bef8f30d06a7fe1de90723318e796bfff68d4a64759b4ddcf3
  — le PDF meme du refs/ de campagne (sha 1f6c73c1… consigne l.445),
  re-telé et sha-verifie au build du 27-11 ; version du record = PDF.
  Regles lues mot a mot :
  §4.3.1 name = sequence Graphic (lettres, marques, chiffres,
        ponctuation, symboles et ESPACES ; les code points de controle
        sont exclus), prefix + U+002F SOLIDUS + suffix, AUCUNE limite
        de longueur ;
  §4.3.2 prefix = directory indicator (chiffres, « usually equal to
        10 ») + U+002E + registrant code (sequences de chiffres
        separees par des points — « 10.500.100 » Ex.2) ; « If the
        directory indicator is equal to 10 then a registrant code is
        always present » ;
  §4.3.3 suffix = sequence de code points choisie par le registrant —
        Ex.1 « 10.1000/123456 », Ex.2 « 10.1038/issn.1476-4687 » ;
  §4.3.4 equivalence : NO normalization (ISO/IEC 10646), code points
        identiques SAUF U+0041..U+005A identiques a U+0061..U+007A —
        donc le cas n'est plie que pour l'ASCII. Ex.1 : S/s EQUIVALENTS
        (10.5594/SMPTE.ST2067-21.2020 = 10.5594/sMPTE.sT2067-21.2020) ;
        Ex.2 : Á/á NON équivalents (10.26321/Á.GUTIÉRREZ.ZARZA.02.
        2018.03 vs minuscule) ;
  §4.3.5 le DOI system n'utilise PAS de chiffre de controle (jamais
        de fausse somme de controle — mesure du batch 1 idx 19) ;
  §4.4.1 l'etiquette « doi: » PRECEDE le nom, n'en fait pas partie ;
  §4.7 percent-encoding : applique PREFIX et SUFFIX separement,
        exemple « 10.1000/456#789 » -> « 10.1000/456%23789 » ;
  §6.5 les shortDOI « 10/abcde » NE SONT PAS des DOI names.

Amont dit, pas devore : le parsing brut->champs cites est la sœur
admise NON construite refs_biblio_scan (registre L68). Ce contrat reçoit
DEUX CHAMPES CITES (identifiants) et rend l'equivalence — il ne parse
jamais un texte brut.
"""
import re

REFERENCE = {
    "spec": "DOI Handbook, DOI Foundation — publication date September "
            "2025 (ISO 26324; the PDF is the version of record)",
    "url": "https://www.doi.org/doi-handbook/DOIHandbook_2025.pdf",
    "pdf_sha256": ("1f6c73c12890a8bef8f30d06a7fe1de90723318e796bff"
                   "f68d4a64759b4ddcf3"),
    "sections": {
        "4.3.1": "Graphic code points (spaces included, controls "
                 "excluded); prefix + U+002F + suffix; no length limit",
        "4.3.2": "prefix = directory indicator + '.' + registrant code "
                 "(digit groups, dot-separated); '10' implies a "
                 "registrant code",
        "4.3.3": "suffix = any code-point sequence the registrant "
                 "chooses",
        "4.3.4": "equivalence: identical code points, NO normalization, "
                 "except U+0041..U+005A identical to U+0061..U+007A "
                 "(ASCII-only case fold)",
        "4.3.5": "the DOI System itself uses no check digits",
        "4.4.1": "the 'doi:' label precedes the name, is not part of "
                 "it",
        "4.7": "percent-encoding applies to prefix and suffix "
              "separately in the HTTP proxy form",
        "6.5": "shortDOIs of the form 10/abcde are NOT DOI names",
    },
}

PROXY_HOSTS = ("doi.org", "dx.doi.org")
_HEXDIGITS = "0123456789abcdefABCDEF"
_PREFIX_DIGITS = re.compile(r"\d+(?:\.\d+)*\Z")


class DoiKitError(Exception):
    """Structural refusal (a field that is not a string at all)."""

    def __init__(self, field, msg):
        self.field = field
        self.msg = msg
        super().__init__(msg)


def _has_control(s):
    for ch in s:
        o = ord(ch)
        if o < 32 or o == 127:
            return True
    return False


def _pct_decode(seg):
    """RFC 3986 §2.1 / Handbook §4.7 inverse. Returns (text, ok, err)."""
    if "%" not in seg:
        return seg, None
    out = bytearray()
    i = 0
    while i < len(seg):
        ch = seg[i]
        if ch == "%":
            if i + 2 >= len(seg) or seg[i + 1] not in _HEXDIGITS \
                    or seg[i + 2] not in _HEXDIGITS:
                return None, "percent_malformed"
            out.append(int(seg[i + 1:i + 3], 16))
            i += 3
        else:
            out.extend(ch.encode("utf-8"))
            i += 1
    try:
        return out.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, "percent_invalid_utf8"


def fold_key(name):
    """§4.3.4: the ONLY case folding is ASCII A-Z -> a-z. No
    normalization of any other kind (accented pairs stay distinct)."""
    return "".join(
        chr(ord(c) + 32) if 0x41 <= ord(c) <= 0x5A else c for c in name)


def parse_doi(given):
    """One cited field -> closed parse record. Grammar problems are
    NAMED verdicts (errors list), never HTTP 400: the tool's job is to
    judge strings as they were cited."""
    side = {"given": given, "form": None, "trimmed": False,
            "name": None, "prefix": None, "directory_indicator": None,
            "registrant_code": None, "suffix": None,
            "percent_decoded": False, "valid": False, "errors": []}
    errs = side["errors"]
    s = given.strip()
    side["trimmed"] = s != given
    if not s:
        errs.append("empty_input")
        return side
    low = s.lower()
    rest = s
    if low.startswith("https://") or low.startswith("http://"):
        after = s[8:] if low.startswith("https://") else s[7:]
        host, slash, path = after.partition("/")
        if host.lower() not in PROXY_HOSTS:
            errs.append("url_host_unsupported")
            return side
        if not slash:
            errs.append("missing_solidus")
            return side
        side["form"] = "proxy"
        rest = path
    elif low.startswith("doi:"):
        side["form"] = "label"
        rest = s[4:]
    else:
        side["form"] = "bare"
    prefix_raw, slash, suffix_raw = rest.partition("/")
    if not slash:
        errs.append("missing_solidus")
        return side
    prefix: str = prefix_raw
    suffix: str = suffix_raw
    if side["form"] == "proxy":
        # §4.7 encodes prefix and suffix SEPARATELY — decode the same way.
        dp, err = _pct_decode(prefix_raw)
        if err or dp is None:
            errs.append(err or "percent_malformed")
            return side
        ds, err2 = _pct_decode(suffix_raw)
        if err2 or ds is None:
            errs.append(err2 or "percent_malformed")
            return side
        prefix, suffix = dp, ds
        side["percent_decoded"] = "%" in prefix_raw or "%" in suffix_raw
    name = prefix + "/" + suffix
    side["name"] = name
    if _has_control(name):
        errs.append("control_char_not_graphic")   # §4.3.1
    if prefix == "":
        errs.append("prefix_missing")
    elif prefix == "10":
        # §6.5: 10/abcde is a shortDOI — not a DOI name; §4.3.2: a
        # registrant code is ALWAYS present for indicator 10.
        errs.append("shortdoi_not_a_doi_name")
    elif not _PREFIX_DIGITS.match(prefix):
        errs.append("prefix_grammar_not_digits")
    elif not prefix.startswith("10."):
        # §4.3.2: the indicator is "usually equal to 10"; other
        # indicators are future possibilities, none published-assigned.
        errs.append("directory_indicator_not_10")
    else:
        side["directory_indicator"] = "10"
        side["registrant_code"] = prefix[3:]
    if suffix == "":
        errs.append("empty_suffix")
    side["valid"] = not errs
    if side["valid"]:
        side["prefix"] = prefix
        side["suffix"] = suffix
    return side


def equivalence(a, b):
    if not isinstance(a, str):
        raise DoiKitError("a", "a: pass the cited DOI string (type string)")
    if not isinstance(b, str):
        raise DoiKitError("b", "b: pass the cited DOI string (type string)")
    pa, pb = parse_doi(a), parse_doi(b)
    if not pa["valid"] or not pb["valid"]:
        verdict, eq = "INVALID", None   # never guess over a broken cite
    else:
        same = fold_key(pa["name"]) == fold_key(pb["name"])
        verdict = "EQUIVALENT" if same else "NOT_EQUIVALENT"
        eq = same
    return {
        "a": pa,
        "b": pb,
        "verdict": verdict,
        "equivalent": eq,
        "rule": {
            "comparison": "code-point sequences identical, EXCEPT "
                          "U+0041..U+005A identical to U+0061..U+007A "
                          "(DOI Handbook §4.3.4) — ASCII-only case "
                          "fold, NO normalization (Á vs á, Å U+212B vs "
                          "Å U+00C5, composed vs combining: distinct "
                          "names)",
            "representations": "'doi:' label and the doi.org / "
                               "dx.doi.org proxy forms are stripped "
                               "(§4.4.1, §4.7); percent-encoding is "
                               "reversed for the proxy form only",
            "check_digit": "the DOI System uses no check digits — none "
                           "is computed, ever (§4.3.5)",
        },
        "reference": REFERENCE,
    }
