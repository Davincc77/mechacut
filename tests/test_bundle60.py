"""Bundle 60 — F7 : les fiches à chaîne parlent EN/PT. Le critère est
dans bench/FINDINGS-F7.md, congelé avant la cellule 1. Ici la moitié
MACHINE : P1 (le nombre déclaré dans sa langue rend la même trace) et
P2 (sans déclaration, l'ambigu est refusé par le nom — jamais deviné).
"""
from fastapi.testclient import TestClient

import main

C = TestClient(main.app)


def _p(fiche, slots):
    r = C.post("/api/v1/fiche/%s" % fiche, json={"slots": slots})
    return r.status_code, r.json()


def test_p1_shop_reste_identical_across_declared_locales():
    _code, base = _p("shop-reste", {"total": "1250", "sold_morning": "50",
                                    "pct_afternoon": "40%"})
    _c, en = _p("shop-reste", {"total": "1,250", "sold_morning": "50",
                               "pct_afternoon": "40%", "locale": "en"})
    _c, pt = _p("shop-reste", {"total": "1.250", "sold_morning": "50",
                               "pct_afternoon": "40 %", "locale": "pt"})
    assert base == en == pt
    assert base["answer"]["remaining"] == "720"


def test_p1_soldes2_comma_decimal_pt():
    _c, base = _p("soldes2", {"price": "81.90", "pct1": "25%",
                              "pct2": "20%"})
    _c, pt = _p("soldes2", {"price": "81,90", "pct1": "25 %",
                            "pct2": "20%", "locale": "pt"})
    assert base == pt
    assert base["answer"]["final"] == "49.14"


def test_p1_partage_reste_en_thousands_and_fractions():
    _c, base = _p("partage-reste", {"total": "1200", "first_part": "1/3",
                                    "second_of_rest": "40%"})
    _c, en = _p("partage-reste", {"total": "1,200", "first_part": "1/3",
                                  "second_of_rest": "40 %",
                                  "locale": "en"})
    assert base == en


def test_p2_ambiguous_never_guessed():
    code, body = _p("shop-reste", {"total": "1.250", "sold_morning": "50",
                                   "pct_afternoon": "40%"})
    assert code == 400
    msg = body["errors"][0]["expected"]
    assert "ambiguous thousands separator" in msg
    assert "never guesses" in msg


def test_p2_bad_locale_named():
    code, body = _p("shop-reste", {"total": "1250", "sold_morning": "50",
                                   "pct_afternoon": "40%",
                                   "locale": "de"})
    assert code == 400
    assert body["errors"][0]["field"] == "locale"


def test_p4_base_grammar_untouched():
    # le « 40 » nu est toujours refusé, locale déclaré ou non
    for slots in ({"total": "435", "sold_morning": "35",
                   "pct_afternoon": "40"},
                  {"total": "435", "sold_morning": "35",
                   "pct_afternoon": "40", "locale": "en"}):
        code, body = _p("shop-reste", slots)
        assert code == 400 and "forty" in body["errors"][0]["expected"]
