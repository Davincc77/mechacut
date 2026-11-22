"""Bundle 29 lot 1 — TEMPS. Attendues calculées à la main ; le jour de
semaine de 2026-11-21 est ancré sur le contexte de la session (vendredi
20 nov), donc le 23 = lundi."""
import sys
sys.path.insert(0, ".")
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def ov(**kw):
    r = client.post("/api/v1/schedule/overlap", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def cr(**kw):
    r = client.post("/api/v1/cron/validate", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


A = [{"start": "2026-11-23T09:00", "end": "2026-11-23T11:00", "label": "A"},
     {"start": "2026-11-23T10:00", "end": "2026-11-23T12:00", "label": "B"}]


def test_merge_union_and_total():
    d = ov(intervals=A)
    assert d["merged"] == [{"start": "2026-11-23T09:00:00",
                            "end": "2026-11-23T12:00:00"}]
    assert d["total_seconds"] == 10800


def test_conflicts_pair_seconds():
    d = ov(intervals=A, mode="conflicts")
    assert d["count"] == 1
    c = d["conflicts"][0]
    assert (c["a"], c["b"], c["seconds"]) == ("A", "B", 3600)


def test_free_gaps_in_window():
    d = ov(intervals=[A[0]], mode="free",
           window={"start": "2026-11-23T08:00", "end": "2026-11-23T14:00"})
    assert d["free"] == [
        {"start": "2026-11-23T08:00:00", "end": "2026-11-23T09:00:00"},
        {"start": "2026-11-23T11:00:00", "end": "2026-11-23T14:00:00"}]
    # 1 h + 3 h = 4 h = 14 400 s (l'attente "10800" était mon erreur de
    # calcul, pas celle du produit — le gap du milieu ne compte pas)


def test_contains_point():
    d = ov(intervals=A, mode="contains", point="2026-11-23T09:30")
    assert d["count"] == 1 and d["inside"][0]["label"] == "A"
    d0 = ov(intervals=A, mode="contains", point="2026-11-23T13:00")
    assert d0["count"] == 0


def test_overlap_rejects_malformed():
    r = client.post("/api/v1/schedule/overlap", json={"intervals": [
        {"start": "2026-11-23T12:00", "end": "2026-11-23T09:00"}]})
    assert r.status_code == 400 and "ends before" in r.text


def test_cron_next_runs_weekdays():
    d = cr(expr="0 9 * * 1-5", at="2026-11-21T10:00", count=3)
    assert d["runs"] == ["2026-11-23T09:00:00", "2026-11-24T09:00:00",
                         "2026-11-25T09:00:00"]


def test_cron_step():
    d = cr(expr="*/15 * * * *", at="2026-11-21T10:07", count=2)
    assert d["runs"] == ["2026-11-21T10:15:00", "2026-11-21T10:30:00"]


def test_cron_never_feb30():
    d = cr(expr="0 0 30 2 *")
    assert d["never"] is True and "max possible day is 29" in d["reason"]


def test_cron_leap_horizon():
    d = cr(expr="0 0 29 2 *", at="2026-11-21T00:00", count=1)
    assert d["runs"] == ["2028-02-29T00:00:00"]


def test_cron_descending_range_refused():
    r = client.post("/api/v1/cron/validate", json={"expr": "0 0 * * 5-1"})
    assert r.status_code == 400 and "descending" in r.text


def test_cron_seven_is_sunday():
    a = cr(expr="0 0 * * 7")
    b = cr(expr="0 0 * * 0")
    assert a["fields"]["dow"] == b["fields"]["dow"] == [0]


def test_cron_or_semantics_documented():
    d = cr(expr="0 0 13 * fri")
    assert d["dom_dow_semantics"] == "both restricted => OR (Vixie)"
    runs = cr(expr="0 0 13 * fri", at="2026-11-01T00:00", count=2)
    # OR : vendredi 6 nov puis vendredi 13 (le 13 est aussi vendredi ->
    # next vendredi = 6). Attendu main: 2026-11-06, 2026-11-13
    assert runs["runs"] == ["2026-11-06T00:00:00", "2026-11-13T00:00:00"]
