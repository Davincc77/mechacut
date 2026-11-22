"""Bundle 3 — dates & scheduling: DST, calendar math, cron, deterministic ICS."""

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _deterministic(url, payload):
    r1 = client.post(url, json=payload)
    r2 = client.post(url, json=payload)
    assert r1.status_code == r2.status_code
    assert r1.content == r2.content  # same request, same bytes
    return r1


# ------------------------------------------------------------- date/parse

def test_parse_all_sources():
    r = _deterministic("/api/v1/date/parse",
                       {"text": "2026-03-29T02:30:00+01:00"})
    b = r.json()
    assert b["utc"] == "2026-03-29T01:30:00+00:00"
    assert b["weekday"] == "Sun" and b["naive"] is False
    r = client.post("/api/v1/date/parse", json={"text": "12/03/2026"})
    assert r.json()["date"] == "2026-03-12"  # dmy default
    r = client.post("/api/v1/date/parse",
                    json={"text": "03/12/2026", "prefer": "mdy"})
    assert r.json()["date"] == "2026-03-12"
    r = client.post("/api/v1/date/parse", json={"text": "12 Mar 2026"})
    assert r.json()["source"] == "month_name"
    r = client.post("/api/v1/date/parse",
                    json={"text": "Sun, 29 Mar 2026 02:30:00 GMT"})
    assert r.json()["source"] == "rfc2822"
    r = client.post("/api/v1/date/parse", json={"text": "1774000000"})
    assert r.json()["epoch"] == 1774000000
    r = client.post("/api/v1/date/parse",
                    json={"text": "2026-07-01 08:00", "tz": "Europe/Paris"})
    assert r.json()["utc"] == "2026-07-01T06:00:00+00:00"


def test_parse_refuses_ambiguity_and_garbage():
    r = client.post("/api/v1/date/parse", json={"text": "hello {["})
    assert r.status_code == 400
    assert r.json()["error"] == "unparsable_date"
    assert "expected" in r.json()["errors"][0]
    r = client.post("/api/v1/date/parse", json={"text": "2026-02-30"})
    assert r.status_code == 400


# ---------------------------------------------------------------- date/tz

def test_tz_dst_correct():
    r = _deterministic("/api/v1/date/tz", {
        "datetime": "2026-03-29", "source": "UTC", "at": "02:30",
        "targets": ["Europe/Paris", "America/New_York"]})
    zones = {z["tz"]: z for z in r.json()["zones"]}
    assert zones["Europe/Paris"]["iso"] == "2026-03-29T04:30:00+02:00"
    assert zones["Europe/Paris"]["dst"] is True
    assert zones["America/New_York"]["iso"] == "2026-03-28T22:30:00-04:00"
    r = client.post("/api/v1/date/tz",
                    json={"datetime": "2026-01-15T12:00:00Z",
                          "targets": ["Asia/Tokyo"]})
    assert r.json()["zones"][0]["iso"] == "2026-01-15T21:00:00+09:00"


def test_tz_unknown_zone_400():
    r = client.post("/api/v1/date/tz",
                    json={"datetime": "2026-01-01", "targets": ["Mars/Olympus"]})
    assert r.status_code == 400
    assert "Olympus" in r.text


# -------------------------------------------------------------- date/calc

def test_calc_add_month_clamp():
    r = _deterministic("/api/v1/date/calc",
                       {"base": "2026-01-31", "op": "add",
                        "params": {"duration": "1m"}})
    assert r.json()["result"] == "2026-02-28T00:00:00"
    r = client.post("/api/v1/date/calc",
                    json={"base": "2024-01-31", "op": "add",
                          "params": {"duration": "1m"}})
    assert r.json()["result"] == "2024-02-29T00:00:00"  # leap


def test_calc_business_days():
    r = client.post("/api/v1/date/calc",
                    json={"base": "2026-12-23", "op": "business_days",
                          "params": {"n": 5}})
    assert r.json()["result"] == "2026-12-30T00:00:00"
    r = client.post("/api/v1/date/calc",
                    json={"base": "2026-12-23", "op": "business_days",
                          "params": {"n": 5, "holidays": ["2026-12-25"]}})
    assert r.json()["result"] == "2026-12-31T00:00:00"
    r = client.post("/api/v1/date/calc",
                    json={"base": "2026-12-23", "op": "diff",
                          "params": {"unit": "business_days",
                                     "until": "2027-01-04"}})
    assert r.json()["business_days"] == 8


def test_calc_diff_human_boundary_age():
    r = client.post("/api/v1/date/calc",
                    json={"base": "2026-01-01", "op": "diff",
                          "params": {"unit": "human",
                                     "until": "2026-01-03 04:05:06"}})
    assert r.json()["human"] == "2 days 4 hours 5 minutes 6 seconds"
    r = client.post("/api/v1/date/calc",
                    json={"base": "2026-05-17", "op": "boundary",
                          "params": {"unit": "quarter", "edge": "end"}})
    assert r.json()["result"] == "2026-06-30T23:59:59"
    r = client.post("/api/v1/date/calc",
                    json={"base": "1977-06-15", "op": "age",
                          "params": {"on": "2026-11-20"}})
    b = r.json()
    assert (b["years"], b["months_extra"], b["days_extra"]) == (49, 5, 5)


# ------------------------------------------------------------------- cron

def test_cron_next_wallclock_pinned():
    r = _deterministic("/api/v1/cron/next", {
        "expression": "0 9 * * 1-5", "count": 3,
        "after": "2026-11-20T12:00:00Z", "tz": "Europe/Paris"})
    runs = r.json()["runs"]
    assert runs[0]["iso"] == "2026-11-23T09:00:00+01:00"
    assert runs[0]["weekday"] == "Mon" and len(runs) == 3


def test_cron_vixie_or_rule():
    r = client.post("/api/v1/cron/next", json={
        "expression": "0 0 13 * fri", "count": 3,
        "after": "2026-01-01T00:00:00Z"})
    days = [(x["iso"], x["weekday"]) for x in r.json()["runs"]]
    assert ("2026-01-13T00:00:00+00:00", "Tue") in days  # 13th wins by OR
    assert any(w == "Fri" for _, w in days)              # Fridays too


def test_cron_macro_and_names():
    r = client.post("/api/v1/cron/next",
                    json={"expression": "@weekly", "count": 1,
                          "after": "2026-11-20T00:00:00Z"})
    assert r.json()["runs"][0]["weekday"] == "Sun"
    r = client.post("/api/v1/cron/next",
                    json={"expression": "0 9 * jan-mar mon-fri", "count": 1,
                          "after": "2026-04-01T00:00:00Z"})
    run = r.json()["runs"][0]
    assert run["iso"].startswith("2027-01-01")  # first Jan weekday after Apr
    assert run["weekday"] in ("Mon", "Tue", "Wed", "Thu", "Fri")


def test_cron_bad_expression_400():
    r = client.post("/api/v1/cron/next", json={"expression": "85 * * * *"})
    assert r.status_code == 400
    assert "out of range" in r.text


def test_cron_humanize():
    r = _deterministic("/api/v1/cron/humanize",
                       {"expression": "*/15 9-17 * * 1-5"})
    b = r.json()
    assert b["human"].startswith("Runs at minute 0,15,30,45; at hour 09")
    assert b["fields"]["day of week"] == [1, 2, 3, 4, 5]


# -------------------------------------------------------------------- ics

ICS_EVENTS = [
    {"summary": "Réunion; planning", "start": "2026-12-01T09:00:00Z",
     "duration": "PT1H30M"},
    {"summary": "Noël", "start": "2026-12-24", "end": "2026-12-26"},
]


def test_ics_generate_deterministic_and_folded():
    r = _deterministic("/api/v1/ics/generate", {"events": ICS_EVENTS})
    body = r.json()["output"]
    assert body.startswith("BEGIN:VCALENDAR") and "\r\n" in body
    assert all(len(l.encode("utf-8")) <= 75 for l in body.split("\r\n"))
    assert "DTSTAMP:20261224T000000Z" in body  # mirrors DTSTART, no drift


def test_ics_roundtrip():
    gen = client.post("/api/v1/ics/generate", json={"events": ICS_EVENTS})
    text = gen.json()["output"]
    par = client.post("/api/v1/ics/parse", json={"ics": text})
    assert par.status_code == 200, par.text
    b = par.json()
    assert b["count"] == 2
    e0 = b["events"][0]
    assert e0["summary"] == "Réunion; planning"  # unescaped round-trip
    assert e0["duration_seconds"] == 5400
    assert e0["start"] == "2026-12-01T09:00:00+00:00"
    assert e0["uid"].endswith("@mechacut")


def test_ics_long_text_folded_roundtrip():
    ev = [{"summary": "S", "description": "long word " * 20,
           "start": "2026-01-01T00:00:00Z"}]
    gen = client.post("/api/v1/ics/generate", json={"events": ev})
    text = gen.json()["output"]
    assert all(len(l.encode("utf-8")) <= 75 for l in text.split("\r\n"))
    par = client.post("/api/v1/ics/parse", json={"ics": text})
    assert par.json()["events"][0]["description"] == "long word " * 20


def test_ics_garbage_400():
    r = client.post("/api/v1/ics/parse", json={"ics": "not a calendar"})
    assert r.status_code == 400


# ---------------------------------------------------------------- surfaces

def test_mcp_dates_tools():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert len(names) == 144  # +money_bogo (22-11 bundle61)
    for t in ("date_parse", "date_tz", "date_calc", "cron_next",
              "cron_humanize", "ics_generate", "ics_parse"):
        assert t in names
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2,
                                  "method": "tools/call",
                                  "params": {"name": "date_parse",
                                             "arguments":
                                                 {"text": "2026-01-01"}}})
    assert "2026-01-01" in r.json()["result"]["content"][0]["text"]
