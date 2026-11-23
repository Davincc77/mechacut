# -*- coding: utf-8 -*-
"""Bundle 89 — address_parse + date_civil (digest, @prismdeadlines, @LilySaucy).

Golds tracés MAIN :

  A1 «Hauptstraße 12, 10827 Berlin, Germany»
     -> components : Germany = DE ; 10827 postal DE ; reste lines ;
     verdict PARSED
  A2 «12 rue des Lilas, 75011 Paris»
     -> poste 75011 : grammaire FR unique ? 75011 passe FR ; d'autres
     pays 5 chiffres ? US ZIP 5 chiffres -> 75011 est un ZIP US valide
     AUSSI -> AMBIGUOUS_POSTAL, candidats triés [FR, US], on ne devine pas
  A3 même texte avec country="FR" -> PARSED, pays dit, plus d'ambiguïté
  A4 « » -> 400
  A5 7 lignes -> 400 ceiling nommé
  A6 sans poste du tout « Nowhere town » -> NO_POSTAL dit, components vides

  C1 2026-12-31T23:30:00+00:00 @ Asia/Tokyo (+9)
     -> civil 2027-01-01 jeudi, year_shift TRUE (l'exercice a bougé),
     utc_date 2026-12-31
  C2 même instant @ America/Sao_Paulo (-3) -> 2026-12-31, shift false
  C3 sans timezone -> 400 tz_required (le fuseau du serveur ne sera
     JAMAIS lu — c'est exactement la douleur des 212 factures de Tokyo)
  C4 zone inconnue -> 400 zone_unknown
"""
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def _a(body):
    r = client.post("/api/v1/address/parse", json=body)
    return r.status_code, r.json()


DE = "Hauptstraße 12, 10827 Berlin, Germany"
FR_AMB = "12 rue des Lilas, 75011 Paris"


def test_a1_country_named_parses():
    s, b = _a({"text": DE})
    assert s == 200 and b["verdict"] == "PARSED"
    comp = b["components"]
    assert comp["country"] == "DE"
    assert comp["postal"] == "10827"
    assert comp["postal_country"] == "DE"
    assert "Hauptstraße 12" in comp["lines"]
    assert "Berlin" in comp["lines"]


def test_a2_ambiguous_is_said_not_resolved():
    s, b = _a({"text": FR_AMB})
    assert s == 200
    assert b["verdict"] == "AMBIGUOUS_POSTAL"
    import re, units
    cand = sorted(cc for cc in units.POSTAL
                  if re.compile(units.POSTAL[cc]).fullmatch("75011"))
    assert b["postal_candidates"] == cand
    assert len(cand) == 22 and "FR" in cand and "US" in cand


def test_a3_country_argument_decides():
    s, b = _a({"text": FR_AMB, "country": "FR"})
    assert s == 200 and b["verdict"] == "PARSED"
    assert b["components"]["postal_country"] == "FR"
    assert b["country_source"] == "argument"


def test_a4_empty_refused():
    s, b = _a({"text": ""})
    assert s == 400


def test_a5_line_ceiling():
    s, b = _a({"text": "\n".join("line %d" % i for i in range(8))})
    assert s == 400
    assert "6" in str(b)


def test_a6_no_postal_is_said():
    s, b = _a({"text": "Nowhere town"})
    assert s == 200
    assert b["verdict"] == "NO_POSTAL"
    assert b["components"]["postal"] is None


def _c(body):
    r = client.post("/api/v1/date/civil", json=body)
    return r.status_code, r.json()


INST = "2026-12-31T23:30:00+00:00"


def test_c1_tokyo_shifts_the_fiscal_year():
    s, b = _c({"instant": INST, "timezone": "Asia/Tokyo"})
    assert s == 200
    assert b["civil_date"] == "2027-01-01"
    assert b["civil_weekday"] == "Friday"  # 2027-01-01 est vendredi — tracé recalé au calendrier
    assert b["year_shift"] is True
    assert b["utc_date"] == "2026-12-31"
    assert b["offset"] == "+09:00"


def test_c2_sao_paulo_no_shift():
    s, b = _c({"instant": INST, "timezone": "America/Sao_Paulo"})
    assert s == 200
    assert b["civil_date"] == "2026-12-31"
    assert b["year_shift"] is False


def test_c3_missing_tz_refused_server_never_read():
    s, b = _c({"instant": INST})
    assert s == 400
    assert "tz_required" in str(b)


def test_c4_unknown_zone_named():
    s, b = _c({"instant": INST, "timezone": "Mars/Olympus"})
    assert s == 400
    assert "zone_unknown" in str(b)


def test_b89_surfaces():
    names = [x["name"] for x in client.post(
        "/mcp", json={"jsonrpc": "2.0", "id": 1,
                      "method": "tools/list"}).json()["result"]["tools"]]
    assert "address_parse" in names and "date_civil" in names
    m = client.get("/agent/manifest").text
    assert "/api/v1/address/parse" in m and "/api/v1/date/civil" in m
