"""bundle46 — /date/recurrence : le déploiement RRULE, sous-ensemble RFC 5545.
ORACLE double : (1) les listes « ==> » PUBLIÉES de la RFC 5545 §3.8.5.3
(exemples officiels, pages 123-129, recopiées À LA MAIN ici) ; (2)
python-dateutil 3.0.0 en cross-battery — avec une divergence ASSUMÉE :
« MO,2TU » rend [] chez dateutil (le bug des fixtures Duncan-Haywood,
14 nov. 2026, reproduit sur 3.0.0) alors que l'ABNF §3.3.10 permet
l'ordinal par valeur. Le calcul main (lundis 5,12,19,26 + 2e mardi 13
= 5,12,13,19,26) tranche, et le test asserte LES DEUX.
Aucune attente n'est lue de la sortie du module."""
import pytest

import recurrkit as rk


def r(dtstart, rrule, **kw):
    args = {"dtstart": dtstart, "rrule": rrule}
    args.update(kw)
    return rk.run_recurrence(args)


def iso(out):
    return [o["iso"] for o in out["occurrences"]]


# ————————————————————— exemples PUBLIÉS RFC 5545 §3.8.5.3

def test_daily_count10():
    # « Daily for 10 occurrences » p.123 : September 2-11
    out = r("1997-09-02T09:00:00", "FREQ=DAILY;COUNT=10")
    assert iso(out) == ["1997-09-%02dT09:00:00" % d for d in range(2, 12)]
    assert out["bound_by"] == "count"
    assert out["dtstart_synced"] is True


def test_weekly_until_oct7():
    # « Weekly on Tuesday and Thursday for five weeks » p.125 :
    # UNTIL 19971007T00:00 == COUNT=10 — main : sep 2,4,9,11,16,18,23,
    # 25,30 + oct 2 ; oct 7 00:00 < oct 7 09:00 donc borné avant
    out = r("1997-09-02T09:00:00",
           "FREQ=WEEKLY;UNTIL=19971007T000000;WKST=SU;BYDAY=TU,TH")
    assert out["returned"] == 10
    assert iso(out)[-1] == "1997-10-02T09:00:00"
    assert out["bound_by"] == "until"


def test_biweekly_count8():
    # « Every other week on Tuesday and Thursday, for 8 occurrences »
    # p.126 : September 2,4,16,18,30; October 2,14,16 — WKST=SU ancre
    # les semaines sur dimanche 31 août ; le LLM de la démo
    # temporal-cortex saute les semaines paires : 4/8 dates fausses
    out = r("1997-09-02T09:00:00",
           "FREQ=WEEKLY;INTERVAL=2;COUNT=8;WKST=SU;BYDAY=TU,TH")
    assert iso(out) == ["1997-09-02T09:00:00", "1997-09-04T09:00:00",
                        "1997-09-16T09:00:00", "1997-09-18T09:00:00",
                        "1997-09-30T09:00:00", "1997-10-02T09:00:00",
                        "1997-10-14T09:00:00", "1997-10-16T09:00:00"]


def test_first_friday_x10():
    # « Monthly on the first Friday for 10 occurrences » p.126 :
    # sep 5, oct 3, nov 7, déc 5, jan 2, fév 6, mar 6, avr 3, mai 1,
    # juin 5 (1998)
    out = r("1997-09-05T09:00:00", "FREQ=MONTHLY;COUNT=10;BYDAY=1FR")
    assert iso(out) == ["1997-09-05T09:00:00", "1997-10-03T09:00:00",
                        "1997-11-07T09:00:00", "1997-12-05T09:00:00",
                        "1998-01-02T09:00:00", "1998-02-06T09:00:00",
                        "1998-03-06T09:00:00", "1998-04-03T09:00:00",
                        "1998-05-01T09:00:00", "1998-06-05T09:00:00"]


def test_first_last_sunday_every_other_month():
    # « Every other month on the first and last Sunday ... 10 » p.126 :
    # sep 7,28 ; nov 2,30 ; jan 4,25 ; mar 1,29 ; mai 3,31 (1998)
    out = r("1997-09-07T09:00:00",
           "FREQ=MONTHLY;INTERVAL=2;COUNT=10;BYDAY=1SU,-1SU")
    assert iso(out) == ["1997-09-07T09:00:00", "1997-09-28T09:00:00",
                        "1997-11-02T09:00:00", "1997-11-30T09:00:00",
                        "1998-01-04T09:00:00", "1998-01-25T09:00:00",
                        "1998-03-01T09:00:00", "1998-03-29T09:00:00",
                        "1998-05-03T09:00:00", "1998-05-31T09:00:00"]


def test_second_to_last_monday():
    # « Monthly on the second-to-last Monday of the month for 6 »
    # p.126 : sep 22, oct 20, nov 17, déc 22, jan 19, fév 16 (1998)
    out = r("1997-09-22T09:00:00", "FREQ=MONTHLY;COUNT=6;BYDAY=-2MO")
    assert iso(out) == ["1997-09-22T09:00:00", "1997-10-20T09:00:00",
                        "1997-11-17T09:00:00", "1997-12-22T09:00:00",
                        "1998-01-19T09:00:00", "1998-02-16T09:00:00"]


def test_third_to_last_day():
    # « Monthly on the third-to-the-last day » p.127 : sep 28, oct 29,
    # nov 28, déc 29, jan 29, fév 26 — main : -3 = dim-31+3-1 ; février
    # 1998 a 28 jours → 26
    out = r("1997-09-28T09:00:00", "FREQ=MONTHLY;BYMONTHDAY=-3",
            max_count=6)
    assert iso(out) == ["1997-09-28T09:00:00", "1997-10-29T09:00:00",
                        "1997-11-28T09:00:00", "1997-12-29T09:00:00",
                        "1998-01-29T09:00:00", "1998-02-26T09:00:00"]


def test_first_and_last_day():
    # « Monthly on the first and last day of the month for 10 » p.127 :
    # sep 30 ; oct 1,31 ; nov 1,30 ; déc 1,31 ; jan 1,31 ; fév 1 (1998)
    out = r("1997-09-30T09:00:00", "FREQ=MONTHLY;COUNT=10;BYMONTHDAY=1,-1")
    assert iso(out) == ["1997-09-30T09:00:00", "1997-10-01T09:00:00",
                        "1997-10-31T09:00:00", "1997-11-01T09:00:00",
                        "1997-11-30T09:00:00", "1997-12-01T09:00:00",
                        "1997-12-31T09:00:00", "1998-01-01T09:00:00",
                        "1998-01-31T09:00:00", "1998-02-01T09:00:00"]


def test_every_18_months_six_days():
    # « Every 18 months on the 10th thru 15th for 10 » p.127 : sep 1997
    # 10-15 (6) puis mars 1999 10-13 (4)
    out = r("1997-09-10T09:00:00",
           "FREQ=MONTHLY;INTERVAL=18;COUNT=10;"
           "BYMONTHDAY=10,11,12,13,14,15")
    assert iso(out) == ["1997-09-10T09:00:00", "1997-09-11T09:00:00",
                        "1997-09-12T09:00:00", "1997-09-13T09:00:00",
                        "1997-09-14T09:00:00", "1997-09-15T09:00:00",
                        "1999-03-10T09:00:00", "1999-03-11T09:00:00",
                        "1999-03-12T09:00:00", "1999-03-13T09:00:00"]


def test_every_tuesday_other_month():
    # « Every Tuesday, every other month » p.127 : sep 2,9,16,23,30 ;
    # nov 4,11,18,25 ; jan 6,13,20 (coupe à 12)
    out = r("1997-09-02T09:00:00", "FREQ=MONTHLY;INTERVAL=2;BYDAY=TU",
            max_count=12)
    assert iso(out) == ["1997-09-02T09:00:00", "1997-09-09T09:00:00",
                        "1997-09-16T09:00:00", "1997-09-23T09:00:00",
                        "1997-09-30T09:00:00", "1997-11-04T09:00:00",
                        "1997-11-11T09:00:00", "1997-11-18T09:00:00",
                        "1997-11-25T09:00:00", "1998-01-06T09:00:00",
                        "1998-01-13T09:00:00", "1998-01-20T09:00:00"]


def test_friday_the_13th_intersection():
    # « Every Friday the 13th » p.129 (EXDATE retiré : cap 5 depuis
    # sep 1997) — BYDAY=FR ET BYMONTHDAY=13 s'INTERSECTENT (Note 1 :
    # BYDAY limite quand BYMONTHDAY présent). Attendu publié : fév 13,
    # mar 13, nov 13 (1998), août 13 (1999), oct 13 (2000).
    out = r("1997-09-02T09:00:00", "FREQ=MONTHLY;BYDAY=FR;BYMONTHDAY=13",
            max_count=5)
    assert iso(out) == ["1998-02-13T09:00:00", "1998-03-13T09:00:00",
                        "1998-11-13T09:00:00", "1999-08-13T09:00:00",
                        "2000-10-13T09:00:00"]
    # le mardi 2 septembre n'est pas une occurrence : le RFC lui-même
    # le signale par EXDATE — nous le DÉCLARONS, jamais ne l'incluons
    assert out["dtstart_synced"] is False
    assert "UNDEFINED" in out["sync_note"]


def test_yearly_june_july():
    # « Yearly in June and July for 10 occurrences » p.128 : le jour
    # vient du DTSTART (10), x5 années
    out = r("1997-06-10T09:00:00", "FREQ=YEARLY;COUNT=10;BYMONTH=6,7")
    assert iso(out)[0:2] == ["1997-06-10T09:00:00", "1997-07-10T09:00:00"]
    assert out["returned"] == 10
    assert iso(out)[-1] == "2001-07-10T09:00:00"


def test_yearly_every_other_jan_feb_mar():
    # « Every other year on January, February, March for 10 » p.128 :
    # mars 10 (1997) seul dans l'année ancre (janv/fév passés), puis
    # 1999 ×3, 2001 ×3, 2003 ×3 = 10
    out = r("1997-03-10T09:00:00",
           "FREQ=YEARLY;INTERVAL=2;COUNT=10;BYMONTH=1,2,3")
    assert iso(out)[1:4] == ["1999-01-10T09:00:00", "1999-02-10T09:00:00",
                             "1999-03-10T09:00:00"]
    assert out["returned"] == 10
    assert iso(out)[-1] == "2003-03-10T09:00:00"


def test_twentieth_monday_of_year():
    # « Every 20th Monday of the year » p.128 : mai 19 1997, mai 18
    # 1998, mai 17 1999 — l'ordinal compte DANS L'ANNÉE quand ni
    # BYMONTH ni BYMONTHDAY ne borne (main : 1er lundi 1997 = 6 janv.,
    # +19×7 = 133 j = 19 mai)
    out = r("1997-05-19T09:00:00", "FREQ=YEARLY;BYDAY=20MO", max_count=3)
    assert iso(out) == ["1997-05-19T09:00:00", "1998-05-18T09:00:00",
                        "1999-05-17T09:00:00"]


def test_every_thursday_in_march():
    # « Every Thursday in March » p.129 : 13,20,27 (1997 — 6 excluded,
    # before DTSTART) ; 5,12,19,26 (1998) ; 4,11,18,25 (1999)
    out = r("1997-03-13T09:00:00", "FREQ=YEARLY;BYMONTH=3;BYDAY=TH",
            max_count=11)
    assert iso(out) == ["1997-03-13T09:00:00", "1997-03-20T09:00:00",
                        "1997-03-27T09:00:00", "1998-03-05T09:00:00",
                        "1998-03-12T09:00:00", "1998-03-19T09:00:00",
                        "1998-03-26T09:00:00", "1999-03-04T09:00:00",
                        "1999-03-11T09:00:00", "1999-03-18T09:00:00",
                        "1999-03-25T09:00:00"]


def test_presidential_election():
    # « Every 4 years, first Tuesday after a Monday in November » p.129
    # : nov 5 1996, nov 7 2000, nov 2 2004 — BYMONTHDAY borne 2-8 ET
    # BYDAY limite : intersection
    out = r("1996-11-05T09:00:00",
           "FREQ=YEARLY;INTERVAL=4;BYMONTH=11;BYDAY=TU;"
           "BYMONTHDAY=2,3,4,5,6,7,8", max_count=3)
    assert iso(out) == ["1996-11-05T09:00:00", "2000-11-07T09:00:00",
                        "2004-11-02T09:00:00"]


def test_daily_utc_until():
    # « Daily until December 24, 1997 » p.124 : la borne est le 24 à
    # 00:00Z, l'instance du 24 est à 09:00 → dernière = déc 23.
    # Main : sep 2→déc 23 inclus = 113 jours (29+31+30+23)
    out = r("1997-09-02T09:00:00Z", "FREQ=DAILY;UNTIL=19971224T000000Z")
    assert out["returned"] == 113
    assert iso(out)[-1] == "1997-12-23T09:00:00Z"


# ————————————————————— les PIÈGES nommés (calculs main)

def test_month31_drops_never_moves():
    # Duncan-Haywood 14 nov. : FREQ=MONTHLY depuis le 31 ne tombe que
    # 7 mois sur 12 — le RFC §3.3.10 DROPPE l'invalid date. Main :
    # mois de 31 jours = 1,3,5,7,8,10,12 → COUNT=7 finit AU 31 déc.,
    # les mois SAUTÉS sont fév/avr/juin/sep/nov (5 sauts, PAS 0)
    out = r("2026-01-31", "FREQ=MONTHLY;COUNT=7")
    assert iso(out) == ["2026-01-31", "2026-03-31", "2026-05-31",
                        "2026-07-31", "2026-08-31", "2026-10-31",
                        "2026-12-31"]
    assert out["skipped_invalid_dates"] == ["2026-02", "2026-04",
                                            "2026-06", "2026-09",
                                            "2026-11"]
    assert "DROPS" in out["skipped_note"]
    assert out["dtstart_kind"] == "date"


def test_feb29_only_leap():
    # main : 2024, 2028, 2032 — sauts 2025-27, 2029-31 (6 ans, pas 4 :
    # 2028 est bissextil)
    out = r("2024-02-29", "FREQ=YEARLY;COUNT=3")
    assert iso(out) == ["2024-02-29", "2028-02-29", "2032-02-29"]
    assert out["skipped_invalid_dates"] == ["2025", "2026", "2027",
                                            "2029", "2030", "2031"]


def test_interval2_2026_demo():
    # la démo publiée temporal-cortex (frontier LLM : 4/8 dates fausses
    # — il ignore INTERVAL=2). Main : semaine ancre lundi 2 mars 2026
    # (WKST MO), TU/TH : 3,5 ; SAUT 9-15 ; 17,19 ; SAUT 23-29 ; 31,
    # 2 avril ; SAUT 6-12 ; 14,16
    out = r("2026-03-03T09:00:00",
           "FREQ=WEEKLY;INTERVAL=2;BYDAY=TU,TH;COUNT=8")
    assert iso(out) == ["2026-03-03T09:00:00", "2026-03-05T09:00:00",
                        "2026-03-17T09:00:00", "2026-03-19T09:00:00",
                        "2026-03-31T09:00:00", "2026-04-02T09:00:00",
                        "2026-04-14T09:00:00", "2026-04-16T09:00:00"]


def test_mixed_ordinals_abnf():
    # « MO,2TU » (fixtures 14 nov. : dateutil 4.0.0 lit AUCUNE date).
    # ABNF §3.3.10 : weekdaynum = [[sign] ord] weekday — l'ordinal est
    # PAR VALEUR, donc mixte = légal. Calcul main janv. 2026 : lundis
    # 5,12,19,26 + 2e mardi 13 → 5,12,13,19,26
    out = r("2026-01-01T09:00:00", "FREQ=MONTHLY;BYDAY=MO,2TU",
            max_count=5)
    assert iso(out) == ["2026-01-05T09:00:00", "2026-01-12T09:00:00",
                        "2026-01-13T09:00:00", "2026-01-19T09:00:00",
                        "2026-01-26T09:00:00"]


def test_unbounded_capped_and_declared():
    # « neither COUNT nor UNTIL = infinite series » (portage Go,
    # §3.3.10 « repeat forever ») : cap dur 500, déclaré
    out = r("2026-01-01T09:00:00", "FREQ=DAILY;INTERVAL=2")
    assert out["returned"] == 500
    assert out["bound_by"] == "cap"
    assert out["truncated_at_cap"] is True
    assert "INFINITE" in out["cap_note"]


def test_never_fire_declared():
    # BYMONTH=2;BYMONTHDAY=30 : février n'a jamais 30 — le set est
    # légitimement VIDE (§3.3.10 drop), et on le DIT au lieu de boucler
    out = r("2026-01-01", "FREQ=MONTHLY;BYMONTH=2;BYMONTHDAY=30")
    assert out["returned"] == 0
    assert out["bound_by"] == "never"
    assert "NEVER" in out["never_note"]


def test_until_below_start_is_empty_not_never():
    out = r("2026-03-01T09:00:00", "FREQ=DAILY;UNTIL=20260101T000000")
    assert out["returned"] == 0
    assert out["bound_by"] == "until"
    assert "never_note" not in out


# ————————————————————— refus NOMMÉS (MUST cités)

def refuse(rrule, field="rrule", word=None):
    with pytest.raises(rk.RecurrenceError) as e:
        r("1997-09-02T09:00:00", rrule)
    assert e.value.field == field
    if word:
        assert word in str(e.value.message)
    return e.value


def test_refusals():
    refuse("COUNT=10;UNTIL=19971007T000000;FREQ=DAILY",
           word="MUST NOT occur in the same")
    refuse("FREQ=SECONDLY", word="refused by name")
    refuse("FREQ=MINUTELY", word="refused by name")
    refuse("FREQ=HOURLY", word="refused by name")
    refuse("FREQ=WEEKLY;BYDAY=2TU",
           word="MUST NOT be specified with a numeric value")
    refuse("FREQ=WEEKLY;BYMONTHDAY=3", word="MUST NOT be specified")
    refuse("FREQ=MONTHLY;BYSETPOS=-1", word="refused by name")
    refuse("FREQ=MONTHLY;BYWEEKNO=3", word="refused by name")
    refuse("FREQ=MONTHLY;BYYEARDAY=1", word="refused by name")
    refuse("FREQ=MONTHLY;BYHOUR=9", word="refused by name")
    refuse("FREQ=MONTHLY;BYMINUTE=30", word="refused by name")
    refuse("FREQ=MONTHLY;BYSECOND=0", word="refused by name")
    refuse("FREQ=MONTHLY;FOO=1", word="unknown rule part")
    refuse("FREQ=DAILY;COUNT=501", word="cap")
    refuse("FREQ=DAILY;COUNT=0", word="out of range")
    refuse("FREQ=DAILY;INTERVAL=0", word="out of range")
    refuse("FREQ=DAILY;FREQ=WEEKLY", word="twice")
    refuse("FREQ=MONTHLY;UNTIL=19971224", word="same value type")
    refuse("FREQ=DAILY;BYMONTH=13", word="out of range")
    refuse("FREQ=MONTHLY;BYMONTHDAY=0", word="out of range")
    refuse("FREQ=WEEKLY;BYDAY=TU,2WE",
           word="MUST NOT be specified with a numeric value")


def test_bad_inputs():
    with pytest.raises(rk.RecurrenceError):
        r("", "FREQ=DAILY")
    with pytest.raises(rk.RecurrenceError):
        r("1997-02-30", "FREQ=DAILY")               # date inexistante
    with pytest.raises(rk.RecurrenceError):
        r("1997-09-02T09:00:00", "NONSENSE")
    with pytest.raises(rk.RecurrenceError):
        r("1997-09-02T09:00:00", "FREQ=DAILY;;COUNT=2")


def test_lenient_by_name():
    # « RRULE: » collé depuis un .ics : accepté PAR LE NOM, déclaré
    out = r("19970902T090000", "RRULE:FREQ=DAILY;COUNT=3")   # compact
    assert iso(out) == ["1997-09-02T09:00:00", "1997-09-03T09:00:00",
                        "1997-09-04T09:00:00"]
    assert out["rrule_normalized"] == "FREQ=DAILY;COUNT=3;WKST=MO"
    assert out["dtstart_kind"] == "datetime"


# ————————————————————— contrat de forme

def test_shape_contract():
    out = r("1997-09-02T09:00:00", "FREQ=DAILY;COUNT=10")
    for key in ("freq", "interval", "wkst", "dtstart", "dtstart_kind",
                "rrule_normalized", "count", "until", "reading",
                "occurrences", "returned", "bound_by", "cap",
                "truncated_at_cap", "dtstart_synced",
                "skipped_invalid_dates", "rules_applied",
                "closed_subset"):
        assert key in out, key
    assert out["cap"] == 500
    assert out["occurrences"][0] == {"n": 1,
                                     "iso": "1997-09-02T09:00:00",
                                     "weekday": "Tue"}
    assert out["reading"] == ("every day, starting 1997-09-02T09:00:00, "
                              "for 10 occurrences")
    assert out["rrule_normalized"] == "FREQ=DAILY;COUNT=10;WKST=MO"


def test_reading_trap31():
    out = r("2026-01-31", "FREQ=MONTHLY;COUNT=7")
    assert out["reading"] == ("every month, on the 31st of the month, "
                              "starting 2026-01-31, for 7 occurrences, "
                              "all-day")


def test_wall_clock_declared():
    out = r("2026-01-05T09:00:00", "FREQ=WEEKLY;COUNT=2")
    joined = " ".join(out["rules_applied"])
    assert "wall-clock" in joined and "date/tz" in joined


# ————————————————————— ORACLE dateutil (test-only)

def test_dateutil_cross_battery():
    pytest.importorskip("dateutil")
    from datetime import datetime, date as D
    from dateutil.rrule import rrulestr
    battery = [
        ("1997-09-02T09:00:00", "FREQ=DAILY;COUNT=10"),
        ("1997-09-02T09:00:00",
         "FREQ=WEEKLY;INTERVAL=2;COUNT=8;WKST=SU;BYDAY=TU,TH"),
        ("1997-09-02T09:00:00",
         "FREQ=WEEKLY;UNTIL=19971007T000000;WKST=SU;BYDAY=TU,TH"),
        ("1997-09-05T09:00:00", "FREQ=MONTHLY;COUNT=10;BYDAY=1FR"),
        ("1997-09-07T09:00:00",
         "FREQ=MONTHLY;INTERVAL=2;COUNT=10;BYDAY=1SU,-1SU"),
        ("1997-09-22T09:00:00", "FREQ=MONTHLY;COUNT=6;BYDAY=-2MO"),
        ("1997-09-30T09:00:00", "FREQ=MONTHLY;COUNT=10;BYMONTHDAY=1,-1"),
        ("1996-11-05T09:00:00",
         "FREQ=YEARLY;INTERVAL=4;BYMONTH=11;BYDAY=TU;"
         "BYMONTHDAY=2,3,4,5,6,7,8"),
        ("1997-06-10T09:00:00", "FREQ=YEARLY;COUNT=10;BYMONTH=6,7"),
        ("2026-03-03T09:00:00",
         "FREQ=WEEKLY;INTERVAL=2;BYDAY=TU,TH;COUNT=8"),
        ("1997-09-02T09:00:00", "FREQ=MONTHLY;BYDAY=FR;BYMONTHDAY=13"),
        ("1997-03-13T09:00:00", "FREQ=YEARLY;BYMONTH=3;BYDAY=TH"),
    ]
    for dtstart, rrule in battery:
        out = r(dtstart, rrule, max_count=60)
        mine = iso(out)[:60]
        du = list(rrulestr(rrule,
                           dtstart=datetime.strptime(dtstart,
                                                     "%Y-%m-%dT%H:%M:%S")))
        theirs = [x.strftime("%Y-%m-%dT%H:%M:%S") for x in du][:len(mine)]
        assert mine == theirs, rrule


def test_dateutil_divergence_is_theirs():
    # le bug Duncan-Haywood reproduit sur 3.0.0 : MO,2TU rend [] chez
    # la lib de référence alors que l'ABNF la permet. Nous rendons le
    # calcul main (5,12,13,19,26) ; le test asserte la DIVERGENCE,
    # pas notre conformité par notre propre sortie
    pytest.importorskip("dateutil")
    from datetime import datetime
    from dateutil.rrule import rrulestr
    du = list(rrulestr("FREQ=MONTHLY;BYDAY=MO,2TU",
                       dtstart=datetime(2026, 1, 1, 9, 0, 0)))
    assert du == []                          # la lib est muette
    out = r("2026-01-01T09:00:00", "FREQ=MONTHLY;BYDAY=MO,2TU",
            max_count=5)
    assert iso(out) == ["2026-01-05T09:00:00", "2026-01-12T09:00:00",
                        "2026-01-13T09:00:00", "2026-01-19T09:00:00",
                        "2026-01-26T09:00:00"]
