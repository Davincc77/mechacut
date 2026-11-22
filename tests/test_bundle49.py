"""bundle49 — /money/flight_comp + /date/week.

ORACLES. flight-comp : chaque attente est calculée À LA MAIN depuis les
textes rejoués EN MAJUSCULE — cache EUR-Lex 32026R2202 (Art. 5(5), 6(4)
« EXCEEDING three hours » STRICT, 7(1) 250/400/600, 7(2) 50 % point (c)
seul, 7(3) 50/25 %, 7(5) trajet global, 7(9) neuf mois + 30 jours, 15a
12 mois), legislation.gov.uk (Art. 6(3) F143, Art. 7 F15 £220/£350/£520)
et la table OFFICIELLE gov.uk Air-passenger-travel-guide avec SES
vecteurs nommés (Glasgow-Amsterdam £220 · East Midlands-Marrakech £350 ·
London-New York £520/£260 sous 4 h). Aucune attente n'est lue de la
sortie du module. week : théorème des 53 jeudis validé sur UN CYCLE
COMPLET DE 400 ANS contre datetime.isocalendar (oracle stdlib ; le
compte 71 est publié par le blog rebased), balayage jour par jour des
définitions %U/%W sur trois années, vecteurs publiés (filecraftpro
2027-W53 inexistant, redbison 2021, forum SQLite 1903-W53-5 → 1904-01-01,
kalkoro 29-déc-2025 = 2026-W01-1, GNU date 2001-01-01 → %U=00 %W=01).
DÉCOUVERTE consignée : le libc LOCAL (macOS/BSD) dévie de POSIX sur
%W/%U près de janvier — l'oracle est la DÉFINITION balayée, jamais
l'appel libc ; la déviation de plateforme EST la douleur mesurée.
"""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

import compkit
import main as m
import weekkit as wk

client = TestClient(m.app)
m.RATE_LIMIT = 10**9


# ============================================= flight-comp : table A/B

def _fc(**kw):
    return compkit.decide(kw)


def test_table_b_strict_threshold_edge():
    # Art. 6(4) amendé : « EXCEEDING three hours » — 180 min pile ne
    # paye PAS (table B), ≥ 181 paye.
    r = _fc(regime="EU", flight_date="2027-11-01", event="delay",
            distance_km="6000", intra_eu="no", delay_min="180")
    assert r["owed"]["display"] == "€0"
    assert r["table"]["id"] == "amended-2026/2202"
    r = _fc(regime="EU", flight_date="2027-11-01", event="delay",
            distance_km="6000", intra_eu="no", delay_min="181")
    assert r["owed"]["display"] == "€600"
    assert r["reductions_may"][0]["amount"] == "€300"      # 7(2) point c


def test_table_a_caselaw_threshold_at_least():
    # Table A : Sturgeon/Nelson — « at least 3 hours » : 180 paye, et
    # la fenêtre 3-4 h du point (c) donne l'OPTION €300 (Nelson).
    r = _fc(regime="EU", flight_date="2027-06-15", event="delay",
            distance_km="6000", intra_eu="no", delay_min="180")
    assert r["owed"]["display"] == "€600"
    assert r["reductions_may"][0]["cite"].startswith("Nelson")
    assert r["reductions_may"][0]["amount"] == "€300"
    assert r["deadlines"]["claim_by"] is None              # A : pas de
    # forclusion codifiée — lois des États membres nommées, jamais devinées


def test_intra_union_cap_400_even_above_3500():
    # Art. 7(1)(b) : tout trajet intra-UE >1500 km = €400, y compris
    # au-delà de 3500 km (la bande la plus mal rapportée).
    r = _fc(regime="EU", flight_date="2027-11-05", event="delay",
            distance_km="7000", intra_eu="yes", delay_min="250")
    assert r["owed"]["display"] == "€400"
    assert r["band"]["letter"] == "b"
    assert r["reductions_may"] == []          # 7(2) : point (c) seulement
    assert "INTRA-UNION CAP" in r["band"]["cite"]


def test_uk_table_gov_uk_vectors():
    # gov.uk Air passenger travel guide, table 2, vecteurs NOMMÉS de la
    # page. legislation.gov.uk Art. 7 F15 : £220/£350/£520.
    r = _fc(regime="UK", flight_date="2026-11-05", event="delay",
            distance_km="675", delay_min="195")             # Glasgow-Amsterdam
    assert r["owed"]["display"] == "£220"
    r = _fc(regime="UK", flight_date="2026-11-05", event="delay",
            distance_km="1900", delay_min="195")            # EM-Marrakesh
    assert r["owed"]["display"] == "£350"
    r = _fc(regime="UK", flight_date="2026-11-05", event="delay",
            distance_km="5550", delay_min="240")            # London-NY
    assert r["owed"]["display"] == "£520"                   # 4 h pile
    r = _fc(regime="UK", flight_date="2026-11-05", event="delay",
            distance_km="5550", delay_min="239")
    assert r["owed"]["display"] == "£260"                   # sous 4 h


def test_cancellation_divergence_same_facts_two_tables():
    # FAITS IDENTiques, deux vols de part et d'autre de l'application :
    # avis à 10 jours, reroute partant 100 min avant, arrivant 200 min
    # après — table A : exemption Art. 5(1)(c)(ii) (≤2 h avant, <4 h
    # après) ; table B : la branche est PARTIE (il faut ≤1 h avant ET
    # <2 h après) → dû, avec options 7(2) et 7(3).
    facts = dict(distance_km="5800", intra_eu="no", notice_days="10",
                 rerouted="yes", reroute_depart_early_min="100",
                 reroute_arrive_late_min="200")
    a = _fc(regime="EU", flight_date="2027-06-15",
            event="cancellation", **facts)
    assert a["owed"]["display"] == "€0"
    b = _fc(regime="EU", flight_date="2027-11-05",
            event="cancellation", **facts)
    assert b["owed"]["display"] == "€600"
    amts = [x["amount"] for x in b["reductions_may"]]
    assert amts == ["€300", "€300", "€450"]     # 7(2) 50 ; 7(3)(a) 50 ; 7(3)(b) 25
    cits = [x["cite"] for x in b["reductions_may"]]
    assert "Art. 7(2)" in cits[0] and "7(3)(a)" in cits[1] \
        and "7(3)(b)" in cits[2]


def test_exemption_14_days_and_second_limb():
    for fd in ("2027-06-15", "2027-11-05"):                  # A et B : ≥14 j
        r = _fc(regime="EU", flight_date=fd, event="cancellation",
                distance_km="900", notice_days="14")
        assert r["owed"]["display"] == "€0"
    # table B, seconde branche : part ≤60 min avant ET arrive <120 après
    r = _fc(regime="EU", flight_date="2027-11-05", event="cancellation",
            distance_km="5800", intra_eu="no", notice_days="13",
            rerouted="yes", reroute_depart_early_min="60",
            reroute_arrive_late_min="119")
    assert r["owed"]["display"] == "€0"
    r = _fc(regime="EU", flight_date="2027-11-05", event="cancellation",
            distance_km="5800", intra_eu="no", notice_days="13",
            rerouted="yes", reroute_depart_early_min="60",
            reroute_arrive_late_min="120")      # <120 STRICT
    assert r["owed"]["display"] == "€600"


def test_claim_deadline_nine_months_with_clamp():
    # Art. 7(9) : demande sous neuf mois depuis la date de départ
    # effective du billet. Main : 15 déc 2027 + 9 mois = 15 SEP 2028 ;
    # 31 déc 2027 + 9 mois → 31 septembre n'existe pas → CLAMP 30.
    r = _fc(regime="EU", flight_date="2027-12-15",
            event="denied_boarding", distance_km="900")
    assert r["deadlines"]["claim_by"] == "2028-09-15"
    assert r["deadlines"]["complaint_by"] == "2028-12-15"   # 15a : 12 mois
    assert r["deadlines"]["carrier_answer_days"] == 30
    r = _fc(regime="EU", flight_date="2027-12-31", event="cancellation",
            distance_km="900", notice_days="2")
    assert r["deadlines"]["claim_by"] == "2028-09-30"
    assert r["deadlines"]["claim_day_clamped"] is True


def test_denied_boarding_full_band_no_window():
    r = _fc(regime="EU", flight_date="2027-11-05",
            event="denied_boarding", distance_km="1400")
    assert r["owed"]["display"] == "€250"
    assert r["reductions_may"] == []
    assert "7 calendar days" in r["exemption_or_refusal"][0]["rule"]


def test_boundary_bands_and_refusals():
    r = _fc(regime="EU", flight_date="2027-11-05", event="delay",
            distance_km="1500", delay_min="200")
    assert r["band"]["letter"] == "a"                       # « or less »
    r = _fc(regime="EU", flight_date="2027-11-05", event="delay",
            distance_km="3500", intra_eu="no", delay_min="200")
    assert r["band"]["letter"] == "b"
    r = _fc(regime="EU", flight_date="2027-11-05", event="delay",
            distance_km="3501", intra_eu="no", delay_min="200")
    assert r["band"]["letter"] == "c"
    with pytest.raises(compkit.CompError) as e:
        _fc(flight_date="2027-11-05", event="delay",
            distance_km="900", delay_min="200")
    assert e.value.field == "regime"
    with pytest.raises(compkit.CompError) as e:            # UK antérieur
        _fc(regime="UK", flight_date="2020-12-31", event="delay",  # à 2021
            distance_km="900", delay_min="200")
    assert e.value.field == "flight_date"
    with pytest.raises(compkit.CompError) as e:            # intra deviné
        _fc(regime="EU", flight_date="2027-11-01", event="delay",  # refusé
            distance_km="6000", delay_min="200")
    assert e.value.field == "intra_eu"
    with pytest.raises(compkit.CompError) as e:            # UK : pas de
        _fc(regime="UK", flight_date="2026-11-05", event="delay",   # bande
            distance_km="6000", intra_eu="no", delay_min="200")     # intra
    assert e.value.field == "intra_eu"


def test_extraordinary_is_note_not_math():
    # Art. 6c(2) : l'exemption extraordinary circumstances exige preuve
    # de lien causal + toutes mesures raisonnables — évaluation des
    # FAITS, pas arithmétique. Le montant rendu reste avant exemption.
    r = _fc(regime="EU", flight_date="2027-11-05", event="delay",
            distance_km="900", delay_min="200", extraordinary="yes")
    assert r["owed"]["display"] == "€250"
    assert any("6c(2)" in n for n in r["info"])


# ================================================= week : le piège W53

def test_2027_w53_artifact_published():
    # filecraftpro : le 1-janv.-2027, %Y-W%V → « 2027-W53 », une SEMAINE
    # QUI N'EXISTE PAS (2027 : Jan-1 vendredi, commune → 52 semaines).
    r = wk._from_date("2027-01-01")
    assert r["iso"]["week_date"] == "2026-W53-5"   # vendredi = 5e jour
    t = r["y_vs_g_trap"]
    assert t["buggy_y_w_v"] == "2027-W53"
    assert t["correct_g_w_v"] == "2026-W53"
    assert t["buggy_week_exists_in_printed_year"] is False
    assert t["risky"] is True
    with pytest.raises(wk.WeekError) as e:
        wk._from_iso("2027-W53")
    assert "DOES NOT EXIST" in e.value.message
    assert "2026-W53" in e.value.message   # l'indice du vrai jeton


def test_redbison_2021_vector():
    r = wk._from_date("2021-01-03")            # 3-janv.-2021 → 2020-W53-7
    assert r["iso"]["week_date"] == "2020-W53-7"
    assert r["y_vs_g_trap"]["buggy_y_w_v"] == "2021-W53"
    assert r["y_vs_g_trap"]["buggy_week_exists_in_printed_year"] is False


def test_kalkoro_kw53_and_w01_bounds():
    # un fournisseur qui dit « KW 53 » parle du 28-déc → 3-janv ;
    # le 29-déc-2025 est 2026-W01-1, JAMAIS « 2025-W01 ».
    r = wk._from_iso("2026-W53")
    assert (r["week_start"], r["week_end"]) == ("2026-12-28", "2027-01-03")
    r = wk._from_iso("2026-W01-3")
    assert r["date"] == "2025-12-31"
    r = wk._from_date("2025-12-29")
    assert r["iso"]["week_date"] == "2026-W01-1"
    t = r["y_vs_g_trap"]
    assert t["buggy_y_w_v"] == "2025-W01"
    assert t["correct_g_w_v"] == "2026-W01"
    assert t["buggy_week_exists_in_printed_year"] is True  # mais autre semaine
    assert t["risky"] is True


def test_sqlite_forum_1904_vector():
    # forum SQLite : 1904-01-01 = vendredi de 1903-W53
    r = wk._from_iso("1903-W53-5")
    assert r["date"] == "1904-01-01"


def test_theorem_over_full_400_year_cycle():
    # blog rebased (publié) : une année a 53 semaines ssi 53 jeudis ;
    # EXACTEMENT 71 telles années par cycle grégorien de 400 ans.
    count = 0
    for y in range(1601, 2001):
        w = date(y, 12, 28).isocalendar()[1]     # oracle stdlib
        assert wk._weeks_in(y) == w, y
        count += w == 53
    assert count == 71


def _scan_weeks(year):
    """Oracle INDÉPENDANT : balayage jour par jour de la DÉFINITION
    POSIX (« jours avant le premier dimanche/lundi = semaine 0 »)."""
    out_u, out_w = {}, {}
    d = date(year, 1, 1)
    end = date(year, 12, 31)
    su = mo = None
    cu = cw = 0
    while d <= end:
        if d.weekday() == 6:
            if su is None:
                su = d
                cu = 1
            else:
                cu += 1
        if d.weekday() == 0:
            if mo is None:
                mo = d
                cw = 1
            else:
                cw += 1
        out_u[d] = 0 if su is None else cu
        out_w[d] = 0 if mo is None else cw
        d += timedelta(days=1)
    return out_u, out_w


def _us(dtstr):
    return wk._from_date(dtstr)["us_conventions"]


def test_us_conventions_vs_definition_scan():
    for year in (2025, 2026, 2027):
        su, sw = _scan_weeks(year)
        d = date(year, 1, 1)
        while d <= date(year, 12, 31):
            r = wk._from_date(d.isoformat())
            assert r["us_conventions"]["strftime_%U_sunday0based"] == su[d]
            assert r["us_conventions"]["strftime_%W_monday0based"] == sw[d]
            d += timedelta(days=1)


def test_excel_us_collision_wcalendar():
    # wcalendar : « 3 janv. 2027 = 2026-W53 ISO vs 2027 Week 2 US » ;
    # GNU date 2001-01-01 (lundi) → %U=00, %W=01.
    r = wk._from_date("2027-01-03")
    assert r["us_conventions"]["excel_weeknum_1"] == 2
    assert r["us_conventions"]["strftime_%U_sunday0based"] == 1
    assert r["us_conventions"]["strftime_%W_monday0based"] == 0
    assert _us("2001-01-01")["strftime_%U_sunday0based"] == 0
    assert _us("2001-01-01")["strftime_%W_monday0based"] == 1


def test_year_mode_theorem_reason_and_neighbours():
    r = wk._from_year("2026")
    assert r["weeks"] == 53 and r["has_w53"] is True
    assert "Thursday" in r["why"]                 # Jan-1 2026 jeudi
    assert r["w01"] == {"start": "2025-12-29", "end": "2026-01-04"}
    assert r["neighbouring_53_week_years"] == {"previous": 2020,
                                               "next": 2032}
    r = wk._from_year("2027")
    assert r["weeks"] == 52 and "Friday" in r["why"]
    r = wk._from_year("2025")
    assert r["weeks"] == 52
    assert r["days_of_december_in_next_iso_year"] == ["2025-12-29",
                                                      "2025-12-30",
                                                      "2025-12-31"]


def test_iso_refusals_named_and_mode_arbitration():
    with pytest.raises(wk.WeekError):
        wk._from_iso("2026-W54")
    with pytest.raises(wk.WeekError):
        wk._from_iso("2026-W00")
    with pytest.raises(wk.WeekError):
        wk._from_iso("2026-01-03")
    with pytest.raises(wk.WeekError) as e:
        wk.run_week({"date": "2026-01-01", "year": "2026"})
    assert "exactly one" in e.value.message
    with pytest.raises(wk.WeekError):
        wk.run_week({})


# ================================================================== HTTP

def test_http_determinism_both_routes():
    for path, body in (
            ("/api/v1/money/flight_comp",
             {"regime": "EU", "flight_date": "2027-11-05",
              "event": "delay", "distance_km": "5800",
              "intra_eu": "no", "delay_min": "210"}),
            ("/api/v1/date/week", {"date": "2027-01-03"}),
    ):
        r1 = client.post(path, json=body)
        r2 = client.post(path, json=body)
        assert r1.status_code == 200
        assert r1.content == r2.content
        assert "sha256" in r1.json()


def test_http_exact_values_over_the_wire():
    r = client.post("/api/v1/money/flight_comp",
                    json={"regime": "UK", "flight_date": "2026-11-05",
                          "event": "delay", "distance_km": "5550",
                          "delay_min": "239"})
    assert r.json()["owed"]["display"] == "£260"
    r = client.post("/api/v1/date/week", json={"iso": "2026-W01-3"})
    assert r.json()["date"] == "2025-12-31"
    r = client.post("/api/v1/date/week", json={"year": "2026"})
    assert r.json()["weeks"] == 53


def test_http_refusals_are_400_named():
    r = client.post("/api/v1/money/flight_comp",
                    json={"flight_date": "2027-11-05", "event": "delay",
                          "distance_km": "900", "delay_min": "200"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "regime"
    # contrat d'entrée = chaînes (ScaleRequest precedent)
    r = client.post("/api/v1/money/flight_comp",
                    json={"regime": "EU", "flight_date": "2027-11-05",
                          "event": "delay", "distance_km": 900,
                          "delay_min": "200"})
    assert r.status_code == 400
    r = client.post("/api/v1/date/week",
                    json={"iso": "2027-W53"})
    assert r.status_code == 400
    assert "DOES NOT EXIST" in r.json()["errors"][0]["message"]


def test_route_first_for_pain_phrases():
    import routing
    for q in ("flight compensation ec261", "indemnite vol retard",
              "compensacao voo atrasado", "my delayed flight rights"):
        hits = routing.route(q, 5)
        assert hits and hits[0]["path"] == "/api/v1/money/flight_comp", q
    for q in ("iso week number", "semaine iso 53",
              "numero da semana iso", "week-based year report"):
        hits = routing.route(q, 5)
        assert hits and hits[0]["path"] == "/api/v1/date/week", q
