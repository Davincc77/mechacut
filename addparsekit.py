"""addparsekit — bundle 89. Découpage d'adresse POSTALE, parseur fermé.

@prismdeadlines : « un parseur simple, rien de plus ». C'est exactement ce
qu'on livre — et rien d'autre : on ne nomme pas rue/ville (ce serait
deviner), on CLASSIE : le pays (argument > nom posé > scan grammatical),
le code postal (grammaire des 50 pays de validate_postal), le reste en
lines ordonnées. Plusieurs pays acceptant le même code, c'est une douleur
réelle (75011 est valide dans 22 grammars) : verdict AMBIGUOUS_POSTAL,
candidats triés, l'argument country tranche et le dit.
"""
import re

import units

MAX_PARTS = 6
MAX_CHARS = 500
_POSTALISH = re.compile(r"\d[0-9A-Za-z \-]{2,9}$")


def _name_country(part):
    p = part.strip().lower()
    for cc, v in units.COUNTRIES.items():
        if p == v[0].lower() or p == cc.lower() or p == v[1].lower():
            return cc
    return None


def _match_ccs(code):
    out = []
    for cc, rx in units.POSTAL.items():
        try:
            if re.compile(rx).fullmatch(code.strip().upper()):
                out.append(cc)
        except re.error:
            pass
    return sorted(out)


def parse(text, country=None):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text_grammar: one address, 1..500 characters")
    if len(text) > MAX_CHARS:
        raise ValueError("ceiling: %d characters max, got %d"
                         % (MAX_CHARS, len(text)))
    parts = [p.strip() for p in re.split(r"[,\n]+", text) if p.strip()]
    if len(parts) > MAX_PARTS:
        raise ValueError("ceiling: %d components max — an address with "
                         "more parts is a story, not an address"
                         % MAX_PARTS)

    warnings, c, csrc = [], None, None
    if country:
        cc = str(country).strip().upper()
        if cc not in units.POSTAL:
            raise ValueError("country_grammar: %r is outside the %d "
                             "shipped postal grammars" % (country,
                                                          len(units.POSTAL)))
        c, csrc = cc, "argument"

    cparts = [p for p in parts if _name_country(p)]
    if c is None and cparts:
        c, csrc = _name_country(cparts[0]), "name"

    postal, postcc, candidates = None, None, []
    resolved = []
    for p in parts:
        if p in cparts:
            continue
        token, rest = (p.split(" ", 1) + [""])[:2] if " " in p else (p, "")
        if not rest:
            token, rest = p, ""
        cand = token if _POSTALISH.fullmatch(token) else (
            p if _POSTALISH.fullmatch(p) else None)
        if cand and postal is None:
            postal = cand
            if c:
                if c in _match_ccs(cand):
                    postcc = c
                else:
                    warnings.append("postal_unmatched: %r does not fit "
                                    "%s's grammar — kept as said"
                                    % (cand, c))
                    postcc = None
            else:
                candidates = _match_ccs(cand)
                if len(candidates) == 1:
                    postcc = candidates[0]
                    c, csrc = postcc, "scan"
            rest_line = rest or ("" if cand == p else "")
            if rest_line:
                resolved.append(rest_line)
        elif cand:
            warnings.append("multiple_postal_forms: second candidate %r "
                            "left among lines" % p)
            resolved.append(p)
        else:
            resolved.append(p)

    if postal is not None and not c and len(candidates) > 1:
        verdict = "AMBIGUOUS_POSTAL"
    elif postal is None:
        verdict = "NO_POSTAL"
    else:
        verdict = "PARSED"

    out = {"verdict": verdict,
           "components": {"country": c, "postal": postal,
                          "postal_country": postcc, "lines": resolved},
           "country_source": csrc,
           "postal_candidates": candidates if verdict ==
           "AMBIGUOUS_POSTAL" else ([c] if postcc else []),
           "warnings": warnings,
           "grammar": {"max_parts": MAX_PARTS, "max_chars": MAX_CHARS,
                       "postal_grammars": len(units.POSTAL),
                       "named_countries": len(units.COUNTRIES)}}
    if verdict == "NO_POSTAL":
        out["why"] = "no component matches any shipped postal grammar " \
                     "shape — the address may be complete, our table " \
                     "just cannot say where it is"
    return out
