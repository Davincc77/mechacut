"""Bundle 29 lot 2 — holidays. La table de Pâques 2000-2099 est celle
publiée par le U.S. Census Bureau (census.gov) ; les listes nationales
viennent des textes de loi cités (Légifrance, Planalto, Diário da
República, 5 U.S.C. 6103)."""
import sys
sys.path.insert(0, ".")
import main
from holidays import easter
from fastapi.testclient import TestClient

client = TestClient(main.app)

CENSUS_2000_2099 = (
    "2000-04-23 2001-04-15 2002-03-31 2003-04-20 2004-04-11 2005-03-27 "
    "2006-04-16 2007-04-08 2008-03-23 2009-04-12 2010-04-04 2011-04-24 "
    "2012-04-08 2013-03-31 2014-04-20 2015-04-05 2016-03-27 2017-04-16 "
    "2018-04-01 2019-04-21 2020-04-12 2021-04-04 2022-04-17 2023-04-09 "
    "2024-03-31 2025-04-20 2026-04-05 2027-03-28 2028-04-16 2029-04-01 "
    "2030-04-21 2031-04-13 2032-03-28 2033-04-17 2034-04-09 2035-03-25 "
    "2036-04-13 2037-04-05 2038-04-25 2039-04-10 2040-04-01 2041-04-21 "
    "2042-04-06 2043-03-29 2044-04-17 2045-04-09 2046-03-25 2047-04-14 "
    "2048-04-05 2049-04-18 2050-04-10 2051-04-02 2052-04-21 2053-04-06 "
    "2054-03-29 2055-04-18 2056-04-02 2057-04-22 2058-04-14 2059-03-30 "
    "2060-04-18 2061-04-10 2062-03-26 2063-04-15 2064-04-06 2065-03-29 "
    "2066-04-11 2067-04-03 2068-04-22 2069-04-14 2070-03-30 2071-04-19 "
    "2072-04-10 2073-03-26 2074-04-15 2075-04-07 2076-04-19 2077-04-11 "
    "2078-04-03 2079-04-23 2080-04-07 2081-03-30 2082-04-19 2083-04-04 "
    "2084-03-26 2085-04-15 2086-03-31 2087-04-20 2088-04-11 2089-04-03 "
    "2090-04-16 2091-04-08 2092-03-30 2093-04-12 2094-04-04 2095-04-24 "
    "2096-04-15 2097-03-31 2098-04-20 2099-04-12")


def hol(**kw):
    r = client.post("/api/v1/schedule/holidays", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def test_computus_matches_census_century():
    for tok in CENSUS_2000_2099.split():
        assert easter(int(tok[:4])).isoformat() == tok, tok


def test_fr_eleven_legal_holidays_2026():
    d = hol(country="FR", year=2026)
    dates = {x["date"]: x for x in d["holidays"]}
    assert d["count"] == 11
    assert dates["2026-04-06"]["name"] == "Lundi de Pâques"
    assert dates["2026-05-14"]["name"] == "Ascension"      # Pâques+39
    assert dates["2026-05-25"]["name"] == "Lundi de Pentecôte"
    assert dates["2026-11-11"]["law"].startswith("L3133-1")


def test_brazil_national_law_and_facultativo_honesty():
    d = hol(country="BR", year=2026)
    assert d["count"] == 9
    dates = {x["date"] for x in d["holidays"]}
    assert "2026-04-03" in dates          # Sexta-Feira Santa (Pâques-2)
    assert "2026-02-17" not in dates      # Carnaval = point facultatif
    assert "pontos facultativos" in d["note"]
    assert "2026-10-12" in dates          # Lei 6.802/1980


def test_portugal_thirteen_and_corpus_dei():
    d = hol(country="PT", year=2026)
    assert d["count"] == 13
    corpo = [x for x in d["holidays"] if x["name"] == "Corpo de Deus"]
    assert corpo[0]["date"] == "2026-06-04"        # Pâques 5 avr + 60


def test_germany_core_only_says_so():
    d = hol(country="DE", year=2026)
    assert d["count"] == 9
    assert "Länder" in d["note"]
    assert "2026-10-03" in {x["date"] for x in d["holidays"]}


def test_us_observance_shift_and_firsts():
    d = hol(country="US", year=2026)
    assert d["count"] == 11
    july = [x for x in d["holidays"] if x["date"].endswith("07-04")][0]
    assert july["observed"] == "2026-07-03"        # samedi -> vendredi
    # 1985 : 11 - MLK (1986) - Juneteenth (2021) = 9 holidays fédéraux
    assert hol(country="US", year=2020)["count"] == 10  # pas de Juneteenth
    assert hol(country="US", year=2021)["count"] == 11
    t = [x for x in d["holidays"] if "Thanksgiving" in x["name"]][0]
    assert t["date"] == "2026-11-26"               # 4e jeudi


def test_is_holiday_verdict():
    d = hol(country="FR", on="2026-07-14")
    assert d["is_holiday"] is True
    assert d["matched"]["name"] == "Fête nationale"
    d2 = hol(country="FR", on="2026-07-13")
    assert d2["is_holiday"] is False


def test_unknown_country_refused_not_invented():
    r = client.post("/api/v1/schedule/holidays",
                    json={"country": "JP", "year": 2026})
    assert r.status_code == 400 and "closed set" in r.text


# ------------------------------------------------------------- lot 3
ICS_OK = (
    "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//mechacut//test//FR\r\n"
    "BEGIN:VEVENT\r\nUID:20260101-a@mechacut.studio\r\n"
    "DTSTAMP:20251121T120000Z\r\n"
    "DTSTART;TZID=Europe/Paris:20260101T090000\r\n"
    "DTEND;TZID=Europe/Paris:20260101T100000\r\n"
    "SUMMARY:séquence pliée\r\n  avec reprise\r\n"
    "END:VEVENT\r\nEND:VCALENDAR\r\n")


def ics(text):
    r = client.post("/api/v1/ics/validate", json={"text": text})
    assert r.status_code == 200, r.text
    return r.json()


def test_ics_valid_with_folding():
    d = ics(ICS_OK)
    assert d["valid"] is True and d["errors"] == []
    assert d["components"] == {"VCALENDAR": 1, "VEVENT": 1}


def test_ics_must_violations_are_errors():
    for label, src, code in [
        ("prodid", ICS_OK.replace("PRODID:-//mechacut//test//FR\r\n", ""),
         "missing_required"),
        ("ordre", ICS_OK.replace("20260101T100000\r\nSUMMARY",
                                 "20251231T100000\r\nSUMMARY"),
         "dtend_before_start"),
        ("mixte", ICS_OK.replace(
            "DTSTART;TZID=Europe/Paris:20260101T090000",
            "DTSTART;VALUE=DATE:20260101"), "dtstart_dtend_mixed"),
        ("ouvert", ICS_OK.replace("END:VEVENT\r\n", ""),
         "unclosed_component"),
        ("orphelin", ICS_OK + "END:VTODO\r\n", "unmatched_end")]:
        d = ics(src)
        assert not d["valid"], (label, d)
        assert any(e["code"] == code for e in d["errors"]), (label, d)


def test_ics_should_violations_stay_warnings():
    d = ics(ICS_OK.replace("DTSTART;TZID=Europe/Paris:20260101T090000",
                           "DTSTART:20260101T090000"))
    assert d["valid"] is True
    assert any(w["code"] == "floating_time" for w in d["warnings"])


def test_ics_garbage_line_flagged():
    d = ics(ICS_OK.replace("SUMMARY:x", "ceci n'est pas une propriété")
            if "SUMMARY:x" in ICS_OK else
            ICS_OK.replace("SUMMARY:séquence pliée",
                           "propriété invalide"))
    assert not d["valid"]
    assert any(e["code"] == "invalid_content_line" for e in d["errors"])
