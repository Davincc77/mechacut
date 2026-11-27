# -*- coding: utf-8 -*-
"""Bundle 136_hermes — spdx_expression + cvss_base_score (registre 26-11,
ADMIS 27-11, GO construction maison).

GRAMMAIRE PORTE. extra=forbid : une cle inconnue est refusee PAR SON
NOM (precedent B8). Tout ce qui est applique sans demande se REND
(applied_defaults, precedent B12/applied_defaults). Chaines exactes
Decimal (jamais de float silencieux). Tables fermees : vintage NOMME +
sha DECLARE dans chaque reponse. Refus par le nom, designant le
contract voisin quand il existe.

AVEU DE SOURCE (ecart contrat/realite, declare au rapport) : le
brief nommait « les 30 vecteurs v4.0 du rapport de campagne » comme
golds litteraux ; la compilation COMPIL_RAPPORTS_VAGUE2 ne contient
AUCUNE section cvss (grep integral 27-11 : zero occurrence de « cvss »,
une mention incidente de « spdx » ligne 1659, sans payload). Les
vecteurs du blob proposeur ne sont pas sur machine (registre : « les
instances relisent LEUR ligne », stocke:false). Donc, comme la consigne
le prevoit pour spdx (« golds a tracer depuis la spec si le rapport est
pauvre, en le declarant »), les golds sont TRACES depuis les sources
PUBLIEES CLOSES, chaque gold cite sa source litterale :

  * cvss v4.0 : FIRST, « CVSS v4.0 Examples » (worked examples, colonnes
    « v4.0 Base » / « v3.1 »), https://www.first.org/cvss/v4.0/examples
    (fetch 27-11-2026, page sha plus bas) + tables de l'implementation
    de reference https://github.com/FIRSTdotorg/cvss-v4-calculator
    (BSD-2-Clause). Les vecteurs publies avec un metric optionnel sont
    rejoues EN RETRANCHANT le metric optionnel, avec la regale nommee
    (supplementaux absents de cvss_score.js ; E:A == defaut worst-case
    de E:X par m()). Comptes : 28 vecteurs v4.0 DISTINCTS publie
    rejoues — pas 30, l'ecart est declare, jamais fabrique.
  * cvss v3.1 : memes tables « v3.1 » (31 paires publiees, 25
    vecteurs DISTINCTS rejoues — doublons d-edites, compte dit), equations
    section 7.1 + Table 14/16 lues dans
    https://www.first.org/cvss/v3.1/specification-document.
  * spdx : grammaire SPDX Specification v2.3.1 Annex D (normative),
    https://spdx.github.io/spdx-spec/v2.3.1/SPDX-license-expressions/ ;
    ids contre SPDX License List 3.29.0 (release 2026-09-16, 740
    licenses / 86 exceptions, table embarquee + sha). Golds = exemples
    LITTERAUX de l'annexe D, cites clause par clause.

Can-fail : un mot hors table n'est PAS une erreur reseau, c'est un
verdict nomme (UNKNOWN_ID / CASE_MISMATCH) ; une expression LicenseRef
est valide sans etre sur la liste ; un E:P publie « Base+Threat » ne
se laisse pas rejouer comme base.
"""
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)

SPDX_URL = "/api/v1/license/spdx-expression"
CVSS_URL = "/api/v1/security/cvss-base"


def _p(url, body):
    r = client.post(url, json=body)
    return r.status_code, (r.json() if r.content else {})


# ---------------------------------------------------------------- SPDX
# Golds litteraux de SPDX spec v2.3.1 Annex D :

def test_spdx_or_and_precedence_gold_from_annex_d45():
    # Annex D.4.5 verbatim: "LGPL-2.1-only OR BSD-3-Clause AND MIT
    # represents a license choice between either LGPL-2.1-only and the
    # expression BSD-3-Clause AND MIT because the AND operator takes
    # precedence over (is applied before) the OR operator."
    s, b = _p(SPDX_URL, {"expression": "LGPL-2.1-only OR BSD-3-Clause AND MIT"})
    assert s == 200, b
    assert b["canonical"] == "LGPL-2.1-only OR BSD-3-Clause AND MIT"
    assert b["tree"]["op"] == "OR"          # OR est le noeud racine
    assert any(c.get("op") == "AND" for c in b["tree"]["children"])
    assert b["verdicts"] == ["OK"]
    assert b["verdict_set"] == ["BAD_EXCEPTION_SLOT", "CASE_MISMATCH",
                                "DEPRECATED_ID", "OK", "UNKNOWN_ID",
                                "USER_REF"]   # ensemble ferme nomme
    assert b["list_version"] == "3.29.0"
    assert b["table"]["licenses"] == 740
    assert b["table"]["exceptions"] == 86


def test_spdx_parenthesized_or_gold_from_annex_d45():
    # D.4.5: "MIT AND (LGPL-2.1-or-later OR BSD-3-Clause)"
    s, b = _p(SPDX_URL, {"expression":
                         "MIT AND (LGPL-2.1-or-later OR BSD-3-Clause)"})
    assert s == 200, b
    assert b["canonical"] == "MIT AND (LGPL-2.1-or-later OR BSD-3-Clause)"
    assert b["verdicts"] == ["OK"]


def test_spdx_with_gold_from_annex_d44():
    # D.4.4: "GPL-2.0-or-later WITH Bison-exception-2.2"
    s, b = _p(SPDX_URL, {"expression":
                         "GPL-2.0-or-later WITH Bison-exception-2.2"})
    assert s == 200, b
    exc = [t for t in b["terms"] if t["kind"] == "exception"]
    assert len(exc) == 1 and exc[0]["in_list"] and exc[0]["with_slot"]
    assert b["verdicts"] == ["OK"]


def test_spdx_plus_suffix_gold_from_annex_d3():
    # D.3: "An SPDX License List Short Form Identifier with a unary
    # '+' operator suffix... For example: CDDL-1.0+" — GPL-2.0+ est
    # lui-meme une entree de la liste 3.29.0.
    s, b = _p(SPDX_URL, {"expression": "GPL-2.0+"})
    assert s == 200, b
    assert b["terms"][0]["plus"] is True
    assert b["terms"][0]["canonical_id"] == "GPL-2.0+"
    assert b["verdicts"] == ["DEPRECATED_ID"]   # GPL-2.0 est deprecie


def test_spdx_user_ref_gold_from_annex_d3():
    # D.3 verbatim: "DocumentRef-spdx-tool-1.2:LicenseRef-MIT-Style-2"
    s, b = _p(SPDX_URL, {"expression":
                         "DocumentRef-spdx-tool-1.2:LicenseRef-MIT-Style-2"})
    assert s == 200, b
    assert b["verdicts"] == ["USER_REF"]        # can-fail : pas une erreur


def test_spdx_case_insensitive_id_gold_from_annex_d2():
    # D.2: "MIT, Mit and mIt should all be treated as the same
    # identifier" — le cas canonique est rendu, l'ecart est un VERDICT.
    s, b = _p(SPDX_URL, {"expression": "mit"})
    assert s == 200, b
    assert b["terms"][0]["canonical_id"] == "MIT"
    assert b["verdicts"] == ["CASE_MISMATCH"]


def test_spdx_table_vintage_declared():
    s, b = _p(SPDX_URL, {"expression": "MIT"})
    assert s == 200, b
    tab = b["table"]
    assert tab["sha256"] == main.spdxkit.TABLE_SHA256
    assert tab["licenses"] == 740 and tab["exceptions"] == 86
    assert tab["deprecated_licenses"] == 32
    assert b["list_release_date"] == "2026-09-16"
    assert b["applied_defaults"] == [
        "list_version=3.29.0 (the only embedded vintage; a closed table "
        "is named, never assumed)"]


def test_spdx_unknown_id_is_verdict_not_error():
    # can-fail : MITT n'est PAS renomme MIT en silence.
    s, b = _p(SPDX_URL, {"expression": "MIT AND MITT"})
    assert s == 200, b
    t = [x for x in b["terms"] if x["id"] == "MITT"][0]
    assert t["in_list"] is False
    assert "MIT" in t["nearest"]          # did-you-mean a distance <= 2
    assert "UNKNOWN_ID" in b["verdicts"]


def test_spdx_bad_exception_slot_is_verdict():
    s, b = _p(SPDX_URL, {"expression": "MIT WITH Apache-2.0"})
    assert s == 200, b
    assert "BAD_EXCEPTION_SLOT" in b["verdicts"]
    # D.4.4 : le second operand doit etre une exception, Apache-2.0 ne
    # l'est pas — verdict nomme, pas de re-ecriture silencieuse.


def test_spdx_refusals_by_name():
    # precedent B8 : cle inconnue refusee PAR SON NOM
    s, b = _p(SPDX_URL, {"expression": "MIT", "bogus": 1})
    assert s == 400 and "bogus" in str(b)
    cases = [
        ({"expression": "MIT and Apache-2.0"}, "operator_case"),   # D.2
        ({"expression": "(MIT OR Apache-2.0"}, "unbalanced_paren"),
        ({"expression": "MIT MIT"}, "missing_operator"),
        ({"expression": "GPL-2.0:"}, "colon_id_deprecated"),
        ({"expression": "NONE"}, "special_value_not_expression"),
        ({"expression": ""}, "empty_expression"),
        ({"expression": "MIT", "list_version": "2.5"}, "list_version"),
    ]
    for payload, reason in cases:
        s, b = _p(SPDX_URL, payload)
        assert s == 400, (payload, b)
        assert reason in str(b), (payload, reason, b)


def test_spdx_deterministic_sha():
    s1, b1 = _p(SPDX_URL, {"expression": "MIT OR Apache-2.0"})
    s2, b2 = _p(SPDX_URL, {"expression": "MIT OR Apache-2.0"})
    assert b1["sha256"] == b2["sha256"]
    assert "sha256" in b1


# ---------------------------------------------------------------- CVSS
# v3.1 : 25 vecteurs DISTINCTS (31 paires publiees FIRST « Examples »,
# colonne « v3.1 », doublons d-edites).
# Source : https://www.first.org/cvss/v4.0/examples (pages 26-11/27-11
# de 2026, memes worked examples cotes v3.1 | v4.0).

V31_GOLDS = [
    ("CVSS:3.1/AV:L/AC:H/PR:L/UI:N/S:U/C:H/I:H/A:H", "7.0"),
    ("CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:L/I:N/A:N", "3.3"),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", "6.1"),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:L/I:L/A:N", "7.2"),
    ("CVSS:3.1/AV:L/AC:L/PR:H/UI:N/S:C/C:H/I:N/A:N", "6.0"),
    ("CVSS:3.1/AV:L/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H", "9.3"),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N", "7.5"),
    ("CVSS:3.1/AV:A/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:H", "9.3"),
    ("CVSS:3.1/AV:P/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H", "7.6"),
    ("CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N", "6.5"),
    ("CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N", "5.9"),
    ("CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:L/I:L/A:N", "5.4"),
    ("CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:H/A:H", "9.0"),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N", "4.3"),
    ("CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H", "8.8"),
    ("CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H", "7.8"),
    ("CVSS:3.1/AV:P/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H", "6.4"),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", "7.5"),
    ("CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:H/I:N/A:N", "4.9"),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "9.8"),
    ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", "7.3"),
    ("CVSS:3.1/AV:P/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "6.8"),
    ("CVSS:3.1/AV:L/AC:L/PR:H/UI:N/S:C/C:H/I:H/A:H", "8.2"),
    ("CVSS:3.1/AV:L/AC:L/PR:H/UI:N/S:U/C:N/I:H/A:H", "6.0"),
    ("CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H", "8.1"),
]

# v4.0 : vecteurs DISTINCTS publies, colonne « v4.0 Base » (+2 lignes
# « v4.0 Base + Threat » dont le metric retire est E:A, egal au
# worst-case par defaut de l'impl de reference). 28 comptes — le brief
# disait 30 ; l'ecart est declare, non fabrique.

V40_GOLDS = [
    ("CVSS:4.0/AV:L/AC:L/AT:P/PR:L/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "7.3"),
    ("CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:A/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N", "4.6"),
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:A/VC:N/VI:N/VA:N/SC:L/SI:L/SA:N", "5.1"),
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:L/SI:L/SA:N", "6.9"),
    ("CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:N/VI:N/VA:N/SC:H/SI:N/SA:N", "5.9"),
    ("CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H", "9.4"),
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:H/VA:N/SC:H/SI:H/SA:H", "9.3"),
    ("CVSS:4.0/AV:A/AC:L/AT:N/PR:N/UI:N/VC:N/VI:L/VA:N/SC:H/SI:N/SA:H", "6.4"),
    ("CVSS:4.0/AV:P/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "7.0"),
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N", "7.1"),
    ("CVSS:4.0/AV:N/AC:L/AT:P/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N", "8.2"),
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:P/VC:N/VI:N/VA:N/SC:L/SI:L/SA:N", "5.1"),
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:A/VC:H/VI:H/VA:H/SC:L/SI:L/SA:N", "8.5"),
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:A/VC:N/VI:L/VA:N/SC:N/SI:N/SA:N", "5.1"),
    ("CVSS:4.0/AV:N/AC:L/AT:P/PR:L/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "7.7"),
    ("CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:P/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "8.5"),
    ("CVSS:4.0/AV:P/AC:L/AT:P/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "5.4"),
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N", "8.7"),
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N", "6.9"),
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "9.3"),
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:L/VA:N/SC:L/SI:L/SA:L", "6.9"),
    # publies avec supplementaux (absents des equations de scoring,
    # cvss_score.js ne les lit pas) — retranches, regale citee :
    ("CVSS:4.0/AV:P/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:H/SA:N", "8.3"),
    ("CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "8.4"),
    ("CVSS:4.0/AV:L/AC:L/AT:P/PR:H/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "7.1"),
    ("CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:P/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "8.5"),
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H", "9.4"),
    # publie sous forme « Base + Threat » avec E:A — E absent defaut
    # worst-case E:A (m() de l'impl de reference) :
    ("CVSS:4.0/AV:N/AC:L/AT:P/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "9.2"),
    # idem (duplicate retire) :
    ("CVSS:4.0/AV:N/AC:L/AT:N/PR:H/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N", "8.6"),
]


def test_cvss_v31_published_golds():
    for vec, want in V31_GOLDS:
        s, b = _p(CVSS_URL, {"vector": vec})
        assert s == 200, (vec, b)
        assert b["score"] == want, (vec, b["score"], want)
        assert b["version"] == "3.1"
        assert "Roundup" in b["rounding"]           # fonction NOMMEE
        assert b["table"]["vintage"].startswith("v3.1")
        assert b["table"]["sha256"] == main.cvsskit.V31_TABLE_SHA256


def test_cvss_v40_published_golds():
    for vec, want in V40_GOLDS:
        s, b = _p(CVSS_URL, {"vector": vec})
        assert s == 200, (vec, b)
        assert b["score"] == want, (vec, b["score"], want)
        assert b["version"] == "4.0"
        assert "half-up" in b["rounding"]           # NOT Roundup, dit
        assert len(V40_GOLDS) == 28 and len(V31_GOLDS) == 25
        for d in b["applied_defaults"]:
            assert "worst case" in d or "scored as H" in d
        assert b["table"]["sha256"] == main.cvsskit.V40_TABLE_SHA256


def test_cvss_bands_named_closed_set():
    # Tables 14 (v3.1) et 22 (v4.0), memes ranges : None 0.0,
    # Low 0.1-3.9, Medium 4.0-6.9, High 7.0-8.9, Critical 9.0-10.0.
    for vec, want, band in [
            ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "9.8",
             "CRITICAL"),
            ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L", "7.3", "HIGH"),
            ("CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N", "4.3",
             "MEDIUM"),   # publie (V31_GOLDS)
            ("CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:L/I:N/A:N", "3.3", "LOW"),
            ("CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:H/A:H", "9.0",
             "CRITICAL"),   # boundary 9.0 publie
            ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N", "0.0",
             "NONE"),
            ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N",
             "0.0", "NONE")]:
        s, b = _p(CVSS_URL, {"vector": vec})
        assert s == 200 and b["score"] == want, (vec, b)
        assert b["severity"] == band, (vec, b["severity"], band)


def test_cvss_v31_nonpreferred_order_is_valid_spec_says_so():
    # v3.1 spec, section 6, verbatim : "The same example ... with the
    # metrics in a non-preferred ordering would produce the following
    # vector: CVSS:3.1/S:U/AV:N/..." — ACCEPTE, rendu normalise.
    s, b = _p(CVSS_URL, {"vector":
                         "CVSS:3.1/S:U/AV:N/AC:L/PR:H/UI:N/C:L/I:L/A:N"})
    assert s == 200, b
    assert list(b["metrics"]) == ["AV", "AC", "PR", "UI", "S", "C", "I",
                                  "A"]
    # propriete, pas un chiffre invente : le MEME vecteur en ordre
    # canonique rend le MEME score (l'outil normalise, il ne rejudge pas)
    s2, c = _p(CVSS_URL, {"vector":
                          "CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:L/I:L/A:N"})
    assert s2 == 200 and c["score"] == b["score"]


def test_cvss_v40_strict_order_table23_verbatim():
    # Table 23 : "A vector string must contain metrics in the order
    # shown in Table 23, every other ordering is invalid."
    s, b = _p(CVSS_URL, {"vector":
                         "CVSS:4.0/AC:L/AV:N/AT:N/PR:N/UI:N/VC:H/VI:H/"
                         "VA:H/SC:N/SI:N/SA:N"})
    assert s == 400 and "metric_order" in str(b)


def test_cvss_refusals_name_the_neighbor_contract():
    cases = [
        # spec v4.0 section Vector : exemples OFFICIELS de vecteurs INVALIDES
        ("CVSS:4.0/AV:F/AC:L/AT:N/PR:N/UI:N/VC:N/VI:L/VA:N/SC:N/SI:N/SA:N",
         "bad_value"),                      # "F" n'est pas une valeur de AV
        ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/ui:N/VC:N/VI:L/VA:N/SC:N/SI:N/SA:N",
         "case_sensitive"),                 # "ui" n'est pas une abreviation
        ("AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:L/VA:N/SC:N/SI:N/SA:N",
         "vector_prefix"),                  # prefixe absent
        ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:L/SC:N/SI:N/SA:N",
         "missing_metric"),                 # VA obligatoire manque
        ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N"
         "/E:A/E:X", "duplicate_metric"),   # E defini deux fois
        # metrics hors groupe Base = AUTRE contract, nomme :
        ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H/E:F",
         "group_out_of_scope"),
        ("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"
         "/E:U", "group_out_of_scope"),
        ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H/AV:L",
         "duplicate_metric"),
        # X n'existe pas dans le groupe Base :
        ("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:X/I:H/A:H",
         "not_defined_in_base"),
        # v2.0 jamais silencieusement relu comme v3.1 :
        ("CVSS:2.0/AV:N/AC:L/Au:N/C:P/I:P/A:P", "vector_prefix"),
        # precedent B8 : cle inconnue refusee par son nom
        ({"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
          "extra": 1}, None),
    ]
    for item in cases:
        if isinstance(item[0], dict):
            s, b = _p(CVSS_URL, item[0])
            assert s == 400 and "extra" in str(b)
            continue
        vec, reason = item
        s, b = _p(CVSS_URL, {"vector": vec})
        assert s == 400, (vec, b)
        assert reason in str(b), (vec, reason, b)


def test_cvss_exact_decimal_strings_and_sha():
    s, b = _p(CVSS_URL, {"vector":
                         "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"})
    assert s == 200, b
    # chaines exactes : ISS = 1 - 0.44**3 = 0.914816 — fini, pas de
    # 0.9148159999... binaire
    assert b["computation"]["iss"] == "0.914816"
    assert b["score"] == "9.8"
    s2, b2 = _p(CVSS_URL, {"vector":
                           "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"})
    assert b["sha256"] == b2["sha256"]


def test_cvss_threat_scored_example_is_not_replayed_as_base():
    # can-fail : le BT publie 8.2 avec E:P N'EST PAS le score du vecteur
    # de base (9.2) — le refus nomme protege ce melange.
    s, b = _p(CVSS_URL, {"vector":
                         "CVSS:4.0/AV:N/AC:L/AT:P/PR:N/UI:N/VC:H/VI:H/"
                         "VA:H/SC:N/SI:N/SA:N/E:P"})
    assert s == 400 and "group_out_of_scope" in str(b)
    s2, b2 = _p(CVSS_URL, {"vector":
                           "CVSS:4.0/AV:N/AC:L/AT:P/PR:N/UI:N/VC:H/VI:H/"
                           "VA:H/SC:N/SI:N/SA:N"})
    assert b2["score"] == "9.2"      # le score de BASE, publie ailleurs


def test_cvss_batch_dispatch():
    r = client.post("/api/v1/batch", json={
        "tool": "cvss_base_score",
        "payloads": [
            {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"},
            {"vector": "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/"
                       "VA:H/SC:N/SI:N/SA:N"},
            {"vector": "CVSS:9.9/AV:N"},
        ]})
    assert r.status_code == 200, r.json()
    res = r.json()["results"]
    assert res[0]["result"]["score"] == "9.8"
    assert res[1]["result"]["score"] == "9.3"
    assert res[2]["ok"] is False and "vector_prefix" in str(res[2])
    r2 = client.post("/api/v1/batch", json={
        "tool": "spdx_expression",
        "payloads": [{"expression": "MIT OR Apache-2.0"},
                     {"expression": "MIT and Apache-2.0"}]})
    res2 = r2.json()["results"]
    assert res2[0]["result"]["verdicts"] == ["OK"]
    assert res2[1]["ok"] is False and "operator_case" in str(res2[1])


def test_route_names_tools_and_manifest():
    # /route nomme les deux contrats (douleur de campagne : vecteurs
    # recalcules 0/30 par la porte, expressions de licence non parsees)
    for q, tool in [("cvss vector score", "cvss_base_score"),
                    ("spdx license expression", "spdx_expression")]:
        r = client.get("/route", params={"q": q})
        assert r.status_code == 200
        assert tool in str(r.json()), (q, r.json())
    m = client.get("/agent/manifest").text
    assert "spdx_expression /api/v1/license/spdx-expression free" in m
    assert "cvss_base_score /api/v1/security/cvss-base free" in m
    t1 = client.get("/tools/spdx_expression.json")
    t2 = client.get("/tools/cvss_base_score.json")
    assert t1.status_code == 200 and t2.status_code == 200
