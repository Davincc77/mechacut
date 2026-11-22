"""Bundle 61 — P-cron + P7 (douleurs de la sonde de contrat 22-11).

P-cron : le trou ne doit plus être un silence. Deux trous mesurés :
l'expression structurellement impossible (31 février) et le wall clock
inexistant (02:30 Paris le 29/03/2026). Les deux reçoivent un verdict
NOMMÉ en clés soeurs — la projection du gold (runs/tz/expression) ne
bouge pas : B009 reste PASS, les pins restent les pins.
"""
from fastapi.testclient import TestClient

import main

C = TestClient(main.app)


def _next(**kw):
    return C.post("/api/v1/cron/next", json=kw)


def test_never_fires_is_named_not_silent():
    r = _next(expression="0 9 31 2 *", after="2026-03-01T00:00:00Z")
    assert r.status_code == 200
    b = r.json()
    assert b["runs"] == []
    assert "NEVER_FIRES" in b["never_fires"]
    assert "February ends at 29" in b["never_fires"]


def test_feb29_is_silent_no_more_but_fires_in_leap():
    # dom 29 + month {2} EST possible (années bissextiles) : pas de
    # refus, jamais.
    r = _next(expression="0 9 29 2 *", after="2026-03-01T00:00:00Z",
              count=1)
    b = r.json()
    assert "never_fires" not in b
    assert b["runs"][0]["iso"].startswith("2028-02-29")


def test_dst_gap_wall_clock_is_skipped_and_named():
    r = _next(expression="30 2 * * *", after="2026-03-29T00:00:00Z",
              tz="Europe/Paris", count=2)
    b = r.json()
    isos = [x["iso"] for x in b["runs"]]
    assert not any("2026-03-29T02:30" in i for i in isos)
    sk = b["skipped"][0]
    assert sk["wall"] == "2026-03-29T02:30"
    assert "NEVER happens" in sk["verdict"]
    assert sk["first_valid_after_jump"] == "2026-03-29 03:00:00"


def test_fold_day_still_fires_once():
    # 25/10/2026 : 02:30 existe DEUX fois — ambigu mais RÉEL. Le cron
    # maison le sert une fois (première occurrence, comportement
    # crontab) et ne le marque PAS gap.
    r = _next(expression="30 2 * * *", after="2026-10-25T00:00:00Z",
              tz="Europe/Paris", count=1)
    b = r.json()
    assert "skipped" not in b
    assert b["runs"][0]["iso"].startswith("2026-10-25T02:30:00")


def test_utc_bytes_untouched():
    # non-régression stricte : l'appel UTC n'a pas de clés soeurs.
    r = _next(expression="0 12 * * *", after="2026-01-01T00:00:00Z",
              count=1)
    b = r.json()
    assert "never_fires" not in b and "skipped" not in b
    assert b["runs"][0]["iso"] == "2026-01-01T12:00:00+00:00"
