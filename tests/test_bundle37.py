"""Bundle 37 — date/relative (reldate). Tous les attendus sont calculés
à la main depuis l'ancre samedi 2026-11-21 (ou 1970-08-14 = vendredi,
fait publié cité sur r/selfhosted)."""
import sys
sys.path.insert(0, ".")
import main
import reldate
import pytest
from fastapi.testclient import TestClient

client = TestClient(main.app)
SAT = "2026-11-21T10:00:00+00:00"      # samedi, vérifié


def r(phrase, now=SAT, tz=None):
    d = reldate.resolve(phrase, now=now, tz=tz)
    return (d["resolved"], d["weekday"], d["datetime"][11:16],
            d["ambiguity"])


def test_english_core():
    assert r("today") == ("2026-11-21", "Saturday", "00:00", False)
    assert r("tomorrow") == ("2026-11-22", "Sunday", "00:00", False)
    assert r("yesterday") == ("2026-11-20", "Friday", "00:00", False)
    assert r("friday") == ("2026-11-27", "Friday", "00:00", False)
    assert r("next monday") == ("2026-11-23", "Monday", "00:00", False)
    # règle ISO déclarée : le samedi appartient à la semaine de lundi 16
    assert r("this monday") == ("2026-11-16", "Monday", "00:00", False)
    assert r("in 3 days") == ("2026-11-24", "Tuesday", "00:00", False)
    assert r("2 weeks ago") == ("2026-11-07", "Saturday", "00:00", False)
    assert r("in 2 months") == ("2027-01-21", "Thursday", "00:00", False)


def test_spans_and_leap_month():
    assert r("end of this month") == ("2026-11-30", "Monday",
                                      "00:00", False)
    assert r("start of the week") == ("2026-11-16", "Monday",
                                      "00:00", False)
    # février 2028 = 29 jours (année bissextile publiée)
    assert r("end of month", now="2028-02-10T00:00:00+00:00") == \
        ("2028-02-29", "Tuesday", "00:00", False)


def test_french_portuguese():
    assert r("demain") == ("2026-11-22", "Sunday", "00:00", False)
    assert r("vendredi soir") == ("2026-11-27", "Friday", "18:00",
                                  False)
    assert r("fin de l'annee") == ("2026-12-31", "Thursday", "00:00",
                                   False)
    assert r("debut du mois") == ("2026-11-01", "Sunday", "00:00",
                                  False)
    assert r("amanha") == ("2026-11-22", "Sunday", "00:00", False)
    assert r("proxima sexta da manha") == ("2026-11-27", "Friday",
                                           "09:00", False)
    assert r("fim da semana") == ("2026-11-22", "Sunday", "00:00",
                                  False)


def test_time_map_declared_and_tonight():
    d = reldate.resolve("tonight", now=SAT)
    assert d["datetime"][11:16] == "21:00"
    assert d["time_given"] is True
    assert "09:00" in d["time_convention"]
    plain = reldate.resolve("tomorrow", now=SAT)
    assert plain["time_given"] is False   # 00:00 déclaré, pas caché


def test_ambiguity_reported_not_decided():
    # vendredi 27 nov, on dit "this friday" un vendredi → les deux
    d = reldate.resolve("this friday", now="2026-11-27T09:00:00+00:00")
    assert d["ambiguity"] is True
    assert d["resolved"] == "2026-11-27"
    assert d["alt_datetime"] == "2026-12-04"
    assert any("both readings" in n for n in d["reading_notes"])


def test_1970_published_fact():
    # r/selfhosted : « August 14 1970 was a Sunday » — c'était VENDREDI
    d = reldate.resolve("today", now="1970-08-14T12:00:00+00:00")
    assert d["weekday"] == "Friday"
    # le mardi suivant = le 18
    d2 = reldate.resolve("tuesday", now="1970-08-14T12:00:00+00:00")
    assert (d2["resolved"], d2["weekday"]) == ("1970-08-18", "Tuesday")


def test_hors_grammaire_refuse_par_le_nom():
    with pytest.raises(reldate.RelDateError) as e:
        reldate.resolve("dans trois semaines environ vers midi",
                        now=SAT)
    msg = str(e.value)
    assert "closed grammar" in msg and "model's job" in msg
    with pytest.raises(reldate.RelDateError):
        reldate.resolve("today", tz="Mars/Extra")


def test_now_echo_and_tz():
    d = reldate.resolve("today")           # now absent → écho obligatoire
    assert d["now_echoed_because_absent"] is True
    assert "T" in d["now_used"]
    # même phrase, ancre Paris vs UTC à minuit approchant = dates possibles
    d1 = reldate.resolve("tomorrow", now="2026-11-21T23:30:00+00:00",
                         tz="Europe/Paris")     # 21/11 déjà 00:30 lundi ?
    # 2026-11-21T23:30Z = 2026-11-22T00:30+01 → demain = 22/11→23/11
    assert d1["resolved"] == "2026-11-23", d1


def test_endpoint_determinisme():
    body = {"phrase": "prochima sexta da manha".replace("prochima",
            "proxima"), "now": SAT}
    r1 = client.post("/api/v1/date/relative", json=body).json()
    r2 = client.post("/api/v1/date/relative", json=body).json()
    assert r1 == r2 and r1["sha256"]
    assert r1["resolved"] == "2026-11-27"
    bad = client.post("/api/v1/date/relative",
                      json={"phrase": "bientôt", "now": SAT})
    assert bad.status_code == 400 and "grammar" in bad.text
