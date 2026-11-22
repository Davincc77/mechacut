"""bundle48 — /date/tz_ambiguity.

ORACLE. Aucune attente n'est lue de la sortie du module : chaque vecteur
est calculé À LA MAIN ici depuis les instants de transition PUBLIÉS par
worldtimedata (table nov. 2026 : Londres 25-oct-2026 01:00Z, NY
1-nov-2026 06:00Z, NY 14-mars-2027 07:00Z, Londres 28-mars-2027
01:00Z, Sydney 4-avr-2027 « 16:00 on Apr 3 ») et cronradar (« in New
York, 30 1 * * * has two candidate instants on November 1 (05:30 and
06:30 UTC) and 30 2 * * * has none on March 14 ») ; Lord Howe (transitions
de 30 minutes, premier dimanche d'avril/octobre à 02:00 local, +10:30
vers +11) est dérivé main des règles IANA publiées. Les dates US/EU/AU
sont des règles écrites dans la loi depuis des années — stables en
tzdata ; les zones sous législation mouvante (Canada, nov. 2026) sont
absentes des pins À DESSEIN.
"""
from fastapi.testclient import TestClient

import main
import tzambkit as tk

client = TestClient(main.app)
main.RATE_LIMIT = 10**9


# ==================================================== doublons (fall back)

def test_ny_fold_two_instants_published():
    # cronradar verbatim : « 30 1 * * * has two candidate instants on
    # November 1 (05:30 and 06:30 UTC) » ; worldtimedata : « The first
    # 1:30 AM is 05:30 UTC on EDT. The second is 06:30 UTC on EST. »
    r = tk.classify("America/New_York", "2026-11-01 01:30")
    assert r["kind"] == "fold"
    a, b = r["instants"]
    assert a["utc"] == "2026-11-01T05:30:00+00:00" and a["fold"] == 0
    assert a["offset"] == "-04:00" and a["tz_abbrev"] == "EDT"
    assert b["utc"] == "2026-11-01T06:30:00+00:00" and b["fold"] == 1
    assert b["offset"] == "-05:00" and b["tz_abbrev"] == "EST"
    t = r["transition"]
    assert t["utc"] == "2026-11-01T06:00:00+00:00"   # 01:59:59 EDT -> 01:00 EST
    assert t["type"] == "repeat"
    assert t["window_start"] == "01:00" and t["window_end"] == "02:00"
    assert t["change_minutes"] == -60
    assert r["verdict"].endswith("happens TWICE in America/New_York")


def test_paris_fold():
    # worldtimedata : « Oct 25 2026 Europe/Berlin, Paris, Madrid —
    # 02:00-02:59 twice, transition instant 01:00 UTC ». Main :
    # 02:30 CEST(+2) = 00:30Z ; 02:30 CET(+1) = 01:30Z.
    r = tk.classify("Europe/Paris", "2026-10-25T02:30:00")
    assert r["kind"] == "fold"
    assert r["instants"][0]["utc"] == "2026-10-25T00:30:00+00:00"
    assert r["instants"][0]["tz_abbrev"] == "CEST"
    assert r["instants"][1]["utc"] == "2026-10-25T01:30:00+00:00"
    assert r["instants"][1]["tz_abbrev"] == "CET"
    assert r["transition"]["utc"] == "2026-10-25T01:00:00+00:00"


def test_sydney_fold_southern_hemisphere():
    # worldtimedata : « Apr 4 2027 Australia/Sydney — 02:00-02:59 twice,
    # 16:00 on Apr 3 (UTC) ». Main : 02:30 AEDT(+11) = 15:30Z du 3 ;
    # 02:30 AEST(+10) = 16:30Z du 3.
    r = tk.classify("Australia/Sydney", "2027-04-04 02:30")
    assert r["kind"] == "fold"
    assert r["instants"][0]["utc"] == "2027-04-03T15:30:00+00:00"
    assert r["instants"][0]["tz_abbrev"] == "AEDT"
    assert r["instants"][1]["utc"] == "2027-04-03T16:30:00+00:00"
    assert r["instants"][1]["tz_abbrev"] == "AEST"
    assert r["transition"]["utc"] == "2027-04-03T16:00:00+00:00"
    assert r["transition"]["window_start"] == "02:00"
    assert r["transition"]["window_end"] == "03:00"


def test_lord_howe_half_hour_fold():
    # Règle IANA publiée : premier dimanche d'avril, 02:00 +11 ->
    # 01:30 +10:30 = 2026-04-04T15:00:00Z (02:00+11 = 15:00Z). Le
    # doublement dure DONC 30 minutes : 01:30-01:59 deux fois.
    # Main : 01:45 +11 = 14:45Z ; 01:45 +10:30 = 15:15Z.
    r = tk.classify("Australia/Lord_Howe", "2026-04-05 01:45")
    assert r["kind"] == "fold"
    assert r["instants"][0]["utc"] == "2026-04-04T14:45:00+00:00"
    assert r["instants"][1]["utc"] == "2026-04-04T15:15:00+00:00"
    assert r["transition"]["utc"] == "2026-04-04T15:00:00+00:00"
    assert r["transition"]["window_start"] == "01:30"
    assert r["transition"]["window_end"] == "02:00"
    assert r["transition"]["change_minutes"] == -30   # la classe 30 min


# ==================================================== trous (spring forward)

def test_ny_gap_2027_published():
    # cronradar : « 30 2 * * * has none on March 14 » (2027, 07:00 UTC).
    # Main : trou 02:00-03:00 ; dernier cadran valide 01:59:59 EST =
    # 06:59:59Z ; premier valide 03:00 EDT = 07:00Z.
    r = tk.classify("America/New_York", "2027-03-14 02:30")
    assert r["kind"] == "gap"
    t = r["transition"]
    assert t["utc"] == "2027-03-14T07:00:00+00:00"
    assert t["type"] == "skip"
    assert t["window_start"] == "02:00" and t["window_end"] == "03:00"
    assert t["change_minutes"] == 60
    pre, post = r["nearest"]
    assert pre["utc"] == "2027-03-14T06:59:59+00:00"
    assert pre["local"] == "2027-03-14 01:59:59" and pre["tz_abbrev"] == "EST"
    assert post["utc"] == "2027-03-14T07:00:00+00:00"
    assert post["local"] == "2027-03-14 03:00:00" and post["tz_abbrev"] == "EDT"
    assert r["verdict"].endswith("NEVER happens in America/New_York")


def test_london_gap_2027():
    # worldtimedata : « Mar 28 2027 Europe/London — 01:00-01:59 never,
    # 01:00 UTC ». Main : dernier valide 00:59:59 GMT ; premier
    # 02:00 BST = 01:00Z.
    r = tk.classify("Europe/London", "2027-03-28 01:30")
    assert r["kind"] == "gap"
    assert r["transition"]["utc"] == "2027-03-28T01:00:00+00:00"
    assert r["nearest"][0]["local"] == "2027-03-28 00:59:59"
    assert r["nearest"][1]["local"] == "2027-03-28 02:00:00"
    assert r["nearest"][1]["tz_abbrev"] == "BST"


def test_lord_howe_half_hour_gap():
    # Règle IANA : premier dimanche d'octobre, 02:00 +10:30 -> 02:30 +11.
    # 02:00 +10:30 = 2026-10-03T15:30:00Z ; trou = 02:00-02:30.
    # 02:15 est DANS le trou.
    r = tk.classify("Australia/Lord_Howe", "2026-10-04 02:15")
    assert r["kind"] == "gap"
    assert r["transition"]["utc"] == "2026-10-03T15:30:00+00:00"
    assert r["transition"]["window_start"] == "02:00"
    assert r["transition"]["window_end"] == "02:30"
    assert r["transition"]["change_minutes"] == 30


# ==================================================== single + bords

def test_single_edge_right_after_repeat():
    # Le cadran 02:00 du 1-nov à NY n'est PAS doublé : 02:00 EST =
    # 07:00Z, unique (le doublon couvre 01:00-01:59).
    r = tk.classify("America/New_York", "2026-11-01 02:00")
    assert r["kind"] == "single"
    assert r["utc"] == "2026-11-01T07:00:00+00:00"
    assert r["offset"] == "-05:00" and r["tz_abbrev"] == "EST"


def test_single_normal_day():
    r = tk.classify("America/New_York", "2026-11-02 01:30")
    assert r["kind"] == "single"
    assert r["utc"] == "2026-11-02T06:30:00+00:00"
    assert r["dst_active"] is False


def test_berlin_3am_single_nestjs_class():
    # nestjs/schedule #2389 : le bug cron 4.4.0 fait tirer 03:00 Berlin
    # DEUX FOIS (01:00Z + 02:00Z) — or 03:00 CET le 25-oct est un cadran
    # UNIQUE (02:00Z). La route sépare le fait (unique) du bug
    # d'implémentation — d'où scheduler_note.
    r = tk.classify("Europe/Berlin", "2026-10-25 03:00")
    assert r["kind"] == "single"
    assert r["utc"] == "2026-10-25T02:00:00+00:00"
    assert "scheduler_note" not in r  # single = pas d'ambiguïté, pas de sermon
    assert r["tz_abbrev"] == "CET"


def test_no_dst_zone():
    # Brésil : DST abolie depuis 2019 (loi, publique) — le 1-nov-2026
    # n'existe pas en doute : 01:30 -03 = 04:30Z, unique.
    r = tk.classify("America/Sao_Paulo", "2026-11-01 01:30")
    assert r["kind"] == "single"
    assert r["utc"] == "2026-11-01T04:30:00+00:00"
    assert r["offset"] == "-03:00"


def test_utc_always_single():
    r = tk.classify("UTC", "2026-11-01 01:30")
    assert r["kind"] == "single"
    assert r["utc"] == "2026-11-01T01:30:00+00:00"
    assert r["tz_abbrev"] == "UTC"


def test_seconds_and_t_separator():
    r = tk.classify("America/New_York", "2026-11-01T01:30:45")
    assert r["kind"] == "fold"
    assert r["instants"][0]["utc"] == "2026-11-01T05:30:45+00:00"
    assert r["instants"][1]["utc"] == "2026-11-01T06:30:45+00:00"


# ==================================================== refus nommés

def test_refuse_offset_in_input():
    for bad in ("2026-11-01T01:30:00-04:00", "2026-11-01 01:30Z",
                "2026-11-01T01:30:00+0100"):
        try:
            tk.classify("America/New_York", bad)
            assert False, bad
        except tk.TzAmbError as e:
            assert e.field == "local"
            assert "offset" in e.message


def test_refuse_date_without_time():
    try:
        tk.classify("America/New_York", "2026-11-01")
        assert False
    except tk.TzAmbError as e:
        assert e.field == "local"


def test_refuse_impossible_clock_and_zone():
    try:
        tk.classify("America/New_York", "2026-13-45 01:30")
        assert False
    except tk.TzAmbError as e:
        assert e.field == "local"
    try:
        tk.classify("Mars/Olympus_Mons", "2026-11-01 01:30")
        assert False
    except tk.TzAmbError as e:
        assert e.field == "zone"
    try:
        tk.classify("", "2026-11-01 01:30")
        assert False
    except tk.TzAmbError as e:
        assert e.field == "zone"  # la zone n'est JAMAIS devinée (UTC)


# ==================================================== HTTP

def test_http_determinism_and_pins_payload():
    # contrat d'entrée = chaînes (ScaleRequest precedent)
    for body in ({"zone": "America/New_York", "local": "2026-11-01 01:30"},
                 {"zone": "Europe/Paris", "local": "2026-10-25 02:30"},
                 {"zone": "America/New_York",
                  "local": "2027-03-14 02:30"},
                 {"zone": "Europe/Luxembourg",
                  "local": "2026-11-22 09:00"}):
        r1 = client.post("/api/v1/date/tz_ambiguity", json=body)
        r2 = client.post("/api/v1/date/tz_ambiguity", json=body)
        assert r1.status_code == 200
        assert r1.content == r2.content
        assert "sha256" in r1.json()


def test_http_refusals_are_400_named():
    r = client.post("/api/v1/date/tz_ambiguity",
                    json={"zone": "America/New_York",
                          "local": "2026-11-01T01:30:00-04:00"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "local"
    r = client.post("/api/v1/date/tz_ambiguity",
                    json={"local": "2026-11-01 01:30"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "zone"
    # un JSON number, pas une chaîne -> 400 déclaré
    r = client.post("/api/v1/date/tz_ambiguity",
                    json={"zone": "UTC", "local": 2026110101})
    assert r.status_code == 400


def test_http_exact_values_over_the_wire():
    r = client.post("/api/v1/date/tz_ambiguity",
                    json={"zone": "America/New_York",
                          "local": "2026-11-01 01:30"})
    b = r.json()
    assert b["kind"] == "fold"
    assert b["instants"][0]["utc"] == "2026-11-01T05:30:00+00:00"
    assert b["transition"]["utc"] == "2026-11-01T06:00:00+00:00"
    assert "fold=0" in b["pep495"]
