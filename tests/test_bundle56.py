# -*- coding: utf-8 -*-
"""bundle56 — /date/tz_anchor + /money/points.

ORACLES. Anchor : chaque instant attendu est CALCULÉ À LA MAIN depuis
les offsets PUBLIÉS (EST −05:00, EDT −04:00, CET +01:00, CEST +02:00,
BST +01:00) aux dates vérifiées sur le calendrier (US DST : fin
01-nov-2026 = premier dimanche, début 08-mars-2026 ; EU : fin
25-oct-2026, début 29-mars-2026 — jours vérifiés « Sun » via date(2026,
...).strftime avant d'écrire un seul littéral). Dérive paris/UTC :
09:00 CET = 08:00Z ; l'ancre naïve UTC = 09:00Z → +60 min. Été : 09:00
CEST = 07:00Z → +120. Fold NY 01:30 : 05:30Z (EDT) et 06:30Z (EST) vs
01:30Z → −240/−300. Gap NY 02:30 : inexistante ; premier valide après =
03:00 EDT = 07:00Z vs 02:30Z → −270. Absolu 22:30Z relu murale à
Londres = 21:30Z → −60 (le « shifted earlier » de Composio #4148).
+05:30 : 09:00−05:30 = 03:30Z ; mal relu en UTC = 09:00Z → +330 (le
demi-écart qui prouve que la minute compte). Fix PraisonAI #4732 :
stamped −05:00 au lieu du −04:00 DE LA DATE → +60, nommé.

Points : cpp = (cash − reste − forvenus) ÷ points × 100 en Fraction
EXACTE (le module calcule, les golds viennent des pages publiées +
divisions longues) : cardcompass (438−5.60)/29000 → 432.40/29000×100 :
432,40×100 = 43 240 ; 43 240/29 000 = 4 324/2 900 = 1 081/725 (1 081 =
23·47, 725 = 5²·29, irréductible) = 1,491034… → presse « 1.49 ».
card-savvy (450−35)/25 000 = 415/25 000×100 = 83/50 = 1,66 PILE.
usecalcpro 750/50 000 = 3/2 = 1,5 ; 3 pts/$ × 1,5 = 9/2 = 4,5 %.
milesbuyer : statement 100 000 × 0.6/100 = 600.00 ; ratio 8÷0,6 = 40/3
= 13.33… (publié « 13× » — eux planchent, nous rendons la fraction).
SwitchWize : 600/900/480 sur 60 000 → 1,0 / 1,5 / 0,8 ; spread 15/8 =
1.88. Bilt : 55/10 000×100 = 11/20 = 0.55 sous floor 1.00 → « pay with
cash » nommé.
"""

import pytest
from fastapi.testclient import TestClient

import anchorkit
import main as m
import pointskit
import tzambkit

client = TestClient(m.app)
m.RATE_LIMIT = 10**9


# ================================================= points : la formule

CARD = {"currency": "USD", "routes": [{"name": "flight",
                                       "points": "29000",
                                       "cash_price": "438",
                                       "cash_still_paid": "5.60"}]}


def test_cardcompass_exact_1081_725():
    r = pointskit.run_points(CARD)
    row = r["routes"][0]
    # 438 − 5.60 = 432.40 ; ×100 ÷ 29 000 = 43 240/29 000 = 1 081/725
    assert row["cpp"] == "1.491034482759"   # 13e décimale 6 → ronde
    assert row["cpp_exact"] == {"numerator": "1081", "denominator": "725"}
    assert row["cpp_press_2dp"] == "1.49"   # leur arrondi, nommé
    assert row["net_cash_value"] == "432.40"
    assert "1/100" in r["cpp_unit"]


def test_card_savvy_166_exactly():
    r = pointskit.run_points({"currency": "USD", "routes": [{
        "name": "award", "points": "25000", "cash_price": "450",
        "cash_still_paid": "35"}]})
    # 415/25 000 × 100 = 41 500/25 000 = 83/50 = 1.66 PILE
    assert r["routes"][0]["cpp"] == "1.660000000000"
    assert r["routes"][0]["cpp_exact"] == {"numerator": "83",
                                           "denominator": "50"}


def test_subtract_before_divide_is_the_trap():
    # « 450/25000 » OUBLIE les 35 de taxes : 1.80 — le mauvais nombre
    r = pointskit.run_points({"currency": "USD", "routes": [{
        "name": "a", "points": "25000", "cash_price": "450",
        "cash_still_paid": "35"}]})
    assert r["routes"][0]["cpp"].startswith("1.66")
    assert not r["routes"][0]["cpp"].startswith("1.8")


def test_rewards_forgone_third_term():
    r = pointskit.run_points({"currency": "USD", "routes": [{
        "name": "a", "points": "25000", "cash_price": "450",
        "cash_still_paid": "35", "rewards_forgone": "10"}]})
    # (450 − 35 − 10) = 405 ; 40 500/25 000 = 81/50 = 1.62 pile
    assert r["routes"][0]["cpp"] == "1.620000000000"
    assert r["routes"][0]["net_cash_value"] == "405.00"


def test_bilt_below_floor_named():
    r = pointskit.run_points({"currency": "USD", "floor": "1.0",
                              "routes": [{"name": "rent", "points": "10000",
                                          "cash_price": "55"}]})
    # 5 500/10 000 = 11/20 = 0.55 < 1.00
    row = r["routes"][0]
    assert row["cpp"] == "0.550000000000"
    assert row["vs_floor"]["below"] is True
    assert "pay with cash" in row["vs_floor"]["verdict"]


def test_at_floor_is_not_below():
    r = pointskit.run_points({"currency": "USD", "floor": "1.0",
                              "routes": [{"name": "sc", "points": "60000",
                                          "cash_price": "600"}]})
    assert r["routes"][0]["vs_floor"]["below"] is False
    assert "at-or-above" in r["routes"][0]["vs_floor"]["verdict"]


def test_switchwize_ranking_and_spread():
    r = pointskit.run_points({"currency": "USD", "routes": [
        {"name": "cash", "points": "60000", "cash_price": "600"},
        {"name": "portal", "points": "60000", "cash_price": "900"},
        {"name": "gift", "points": "60000", "cash_price": "480"}]})
    order = [x["names"] for x in r["ranking"]]
    assert order == [["portal"], ["cash"], ["gift"]]
    # 900/60000 = 1.5 ; 600/480 sur 60 000 = 1.0 / 0.8 ; 1.5÷0.8 = 15/8
    assert r["spread"]["ratio"] == "1.88"
    assert r["spread"]["ratio_exact"] == {"numerator": "15",
                                          "denominator": "8"}


def test_milesbuyer_range_40_3():
    r = pointskit.run_points({"currency": "USD", "routes": [
        {"name": "statement", "points": "60000", "cash_price": "360"},
        {"name": "transfer", "points": "60000", "cash_price": "4800"}]})
    # 8.0 ÷ 0.6 = 80/6 = 40/3 = 13.33… (publié « 13× » — planché)
    assert r["spread"]["ratio_exact"] == {"numerator": "40",
                                          "denominator": "3"}
    assert r["spread"]["ratio"] == "13.33"


def test_balance_value_milesbuyer():
    r = pointskit.run_points({"currency": "USD", "routes": [
        {"name": "statement", "points": "100000", "cash_price": "600"}],
        "points_balance": "100000", "valued_at": "statement"})
    # 100 000 × 0.6 ¢ ÷ 100 = 600.00 $
    assert r["balance"]["value"] == "600.00"
    assert r["balance"]["cpp"] == "0.600000000000"


def test_balance_valued_at_explicit_cpp():
    r = pointskit.run_points({"currency": "EUR", "routes": [
        {"name": "x", "points": "1", "cash_price": "1"}],
        "points_balance": "60000", "valued_at": "1.0"})
    # 60 000 × 1.0/100 = 600.00 €
    assert r["balance"]["value"] == "600.00"
    assert r["balance"]["valued_at"] == "supplied cpp"


def test_balance_without_valued_at_refused():
    with pytest.raises(pointskit.PointsError) as e:
        pointskit.run_points({"currency": "EUR", "routes": [
            {"name": "x", "points": "1", "cash_price": "1"}],
            "points_balance": "60000"})
    assert e.value.field == "valued_at"


def test_effective_return_compound():
    r = pointskit.run_points({"currency": "USD", "points_per_dollar": "3",
                              "routes": [{"name": "portal",
                                          "points": "50000",
                                          "cash_price": "750"}]})
    # 750/50 000×100 = 1.5 ; 3 × 1.5 = 9/2 = 4.50 %
    er = r["effective_return"]["per_route"][0]
    assert er["return_pct"] == "4.50"
    assert er["return_pct_exact"] == {"numerator": "9", "denominator": "2"}


def test_tie_named_not_melted():
    r = pointskit.run_points({"currency": "USD", "routes": [
        {"name": "a", "points": "10000", "cash_price": "500"},
        {"name": "b", "points": "50000", "cash_price": "2500"}]})
    assert len(r["ranking"]) == 1 and r["ranking"][0]["tied"] is True
    assert r["ranking"][0]["names"] == ["a", "b"]


def test_jpy_minor_unit_convention():
    # ¥ sans centimes : cpp reste des 1/100 de yen, CONVENTION NOMMÉE
    r = pointskit.run_points({"currency": "JPY", "routes": [
        {"name": "x", "points": "1", "cash_price": "1"}],
        "points_balance": "10000", "valued_at": "0.5"})
    # 10 000 × 0.5/100 = 50 — zéro décimale rendue pour JPY
    assert r["balance"]["value"] == "50"


def test_points_refusals_named():
    for bad, field in (
        ({"currency": "USD", "routes": [{"name": "a", "points": "100",
                                         "cash_price": "30",
                                         "cash_still_paid": "35"}]},
         "cash_price"),
        ({"currency": "USD", "routes": [{"name": "a", "points": "1",
                                         "cash_price": "1"},
                                        {"name": "a", "points": "1",
                                         "cash_price": "1"}]}, "routes"),
        ({"currency": "USD", "routes": [{"name": "a", "points": "0",
                                         "cash_price": "1"}]}, "points"),
        ({"currency": "USD", "routes": [{"name": "a", "points": "10.5",
                                         "cash_price": "1"}]}, "points"),
        ({"currency": "EURO", "routes": [{"name": "a", "points": "1",
                                          "cash_price": "1"}]}, "currency"),
        ({"currency": "USD", "routes": []}, "routes"),
    ):
        with pytest.raises(pointskit.PointsError) as e:
            pointskit.run_points(bad)
        assert e.value.field == field, bad


def test_number_instead_of_string_refused():
    with pytest.raises(pointskit.PointsError) as e:
        pointskit.run_points({"currency": "USD", "routes": [
            {"name": "a", "points": 29000, "cash_price": "1"}]})
    assert e.value.field == "points"
    assert "STRING" in str(e.value)


def test_break_even_points_elsewhere():
    r = pointskit.run_points(CARD)
    assert "money/crossover" in r["not_here"]


# ================================================= anchor : deux horloges

def test_paris_written_utc_server_60_late():
    # 09:00 CET (+01:00) = 08:00Z ; l'UTC naïf = 09:00Z → +60 min
    r = anchorkit.run_anchor({"stamp": "2026-11-02 09:00",
                              "meant_in": "Europe/Paris",
                              "run_in": "UTC"})
    assert r["meant_in"]["kind"] == "single"
    assert r["meant_in"]["instants"] == ["2026-11-02T08:00:00+00:00"]
    assert r["run_in"]["server_anchor_utc"] == "2026-11-02T09:00:00+00:00"
    assert r["drift"]["minutes"] == 60 and r["drift"]["seconds"] == 3600
    assert "60 min LATE" in r["drift"]["verdict"]
    assert r["readback"]["intended_seen_in_run_wall"] == \
        "2026-11-02T08:00:00+00:00"
    assert r["readback"]["server_fire_seen_in_meant_wall"] == \
        "2026-11-02T10:00:00+01:00"


def test_summer_cest_120_late():
    # 09:00 CEST (+02:00) = 07:00Z vs 09:00Z → +120 min
    r = anchorkit.run_anchor({"stamp": "2026-07-15 09:00",
                              "meant_in": "Europe/Paris",
                              "run_in": "UTC"})
    assert r["drift"]["minutes"] == 120
    assert r["meant_in"]["instants"] == ["2026-07-15T07:00:00+00:00"]


def test_ny_fold_two_drifts():
    # 2026-11-01 = premier dimanche de novembre → doublon 01:30 :
    # pass 1 EDT(−04:00) = 05:30Z, pass 2 EST(−05:00) = 06:30Z ;
    # ancre UTC naïve = 01:30Z → −240 / −300 min (EARLY)
    r = anchorkit.run_anchor({"stamp": "2026-11-01 01:30",
                              "meant_in": "America/New_York",
                              "run_in": "UTC"})
    assert r["meant_in"]["kind"] == "fold"
    assert r["meant_in"]["instants"] == ["2026-11-01T05:30:00+00:00",
                                         "2026-11-01T06:30:00+00:00"]
    assert [d["minutes"] for d in r["drift"]] == [-240, -300]
    assert all("EARLY" in d["verdict"] for d in r["drift"])
    t = r["transition_meant"]
    assert t["type"] == "repeat" and t["change_minutes"] == -60
    assert (t["window_start"], t["window_end"]) == ("01:00", "02:00")


def test_ny_gap_never_happens():
    # 2026-03-08 = premier dimanche de mars → 02:30 N'EXISTE PAS ;
    # premier valide après saut = 03:00 EDT = 07:00Z vs 02:30Z → −270
    r = anchorkit.run_anchor({"stamp": "2026-03-08 02:30",
                              "meant_in": "America/New_York",
                              "run_in": "UTC"})
    assert r["meant_in"]["kind"] == "gap"
    assert r["drift"]["minutes"] == -270
    assert "NEVER occurs" in r["gap_note"]
    assert r["meant_in"]["instants"] == ["2026-03-08T06:59:59+00:00",
                                         "2026-03-08T07:00:00+00:00"]


def test_offset_wins_composio_4148():
    # 22:30Z est un INSTANT ; le lire comme murale de Londres (BST
    # +01:00) réserve 21:30Z → 60 min EARLY — le « shifted earlier »
    r = anchorkit.run_anchor({"stamp": "2026-09-02T22:30:00Z",
                              "meant_in": "Europe/London",
                              "run_in": "Europe/London"})
    assert r["stamp_kind"] == "absolute"
    assert r["instant_utc"] == "2026-09-02T22:30:00+00:00"
    assert r["wall_in_meant"] == "2026-09-02T23:30:00+01:00"
    mis = r["misparsed_if_offset_dropped"]
    assert mis["utc"] == "2026-09-02T21:30:00+00:00"
    assert mis["drift"]["minutes"] == -60
    assert "Composio #4148" in r["offset_wins"]


def test_half_hour_offset_exact_minutes():
    # 09:00+05:30 → 03:30Z ; mal ancré UTC naïf = 09:00Z → +330 min
    r = anchorkit.run_anchor({"stamp": "2026-03-15 09:00+05:30",
                              "meant_in": "UTC", "run_in": "UTC"})
    assert r["instant_utc"] == "2026-03-15T03:30:00+00:00"
    d = r["misparsed_if_offset_dropped"]["drift"]
    assert d["minutes"] == 330 and d["seconds"] == 19800


def test_same_zone_zero_drift():
    r = anchorkit.run_anchor({"stamp": "2026-11-02 09:00",
                              "meant_in": "Europe/Paris",
                              "run_in": "Europe/Paris"})
    assert r["drift"]["seconds"] == 0
    assert "no drift" in r["drift"]["verdict"]


def test_praisonai_4732_stamped_now_offset():
    # 15-mars = EDT (−04:00) ; coder « l'offset d'AUJOURD'HUI » −05:00
    # décale l'instant de +60 min — la faute du fix lui-même
    r = anchorkit.run_anchor({"stamp": "2026-03-15 09:00",
                              "meant_in": "America/New_York",
                              "run_in": "America/New_York",
                              "stamped_offset": "-05:00"})
    g = r["stamped_offset_guard"]
    assert g["offset_in_force_that_date"] == "-04:00"
    assert g["stamped_utc"] == "2026-03-15T14:00:00+00:00"
    assert g["drift"]["minutes"] == 60
    assert "PRAISONAI #4732" in g["verdict"]


def test_stamped_offset_that_matches_survives():
    r = anchorkit.run_anchor({"stamp": "2026-03-15 09:00",
                              "meant_in": "America/New_York",
                              "run_in": "America/New_York",
                              "stamped_offset": "-04:00"})
    assert r["stamped_offset_guard"]["drift"]["seconds"] == 0
    assert "survives" in r["stamped_offset_guard"]["verdict"]


def test_anchor_calls_the_ambiguity_engine():
    # règle du MIROIR : les instants rendus SONT ceux de classify()
    base = tzambkit.classify("Europe/Paris", "2026-11-02 09:00")
    r = anchorkit.run_anchor({"stamp": "2026-11-02 09:00",
                              "meant_in": "Europe/Paris",
                              "run_in": "UTC"})
    assert r["meant_in"]["instants"] == [base["utc"]]
    assert r["meant_in"]["verdict"] == base["verdict"]


def test_anchor_refusals_named():
    for bad, field in (
        ({"stamp": "2026-11-02 09:00", "run_in": "UTC"}, "meant_in"),
        ({"stamp": "2026-11-02 09:00", "meant_in": "Europe/Paris"},
         "run_in"),
        ({"stamp": "1730545200", "meant_in": "UTC", "run_in": "UTC"},
         "stamp"),
        ({"stamp": "9am paris", "meant_in": "Europe/Paris",
          "run_in": "UTC"}, "stamp"),
        ({"stamp": "2026-02-30 09:00", "meant_in": "UTC",
          "run_in": "UTC"}, "stamp"),
        ({"stamp": "2026-11-02 09:00", "meant_in": "Mars/Olympus",
          "run_in": "UTC"}, "meant_in"),
        ({"stamp": "2026-11-02 09:00", "meant_in": "UTC",
          "run_in": "Mars/Olympus"}, "run_in"),
        ({"stamp": "2026-09-02T22:30:00Z", "meant_in": "UTC",
          "run_in": "UTC", "stamped_offset": "+01:00"}, "stamped_offset"),
    ):
        with pytest.raises(anchorkit.AnchorError) as e:
            anchorkit.run_anchor(bad)
        assert e.value.field == field, bad


def test_pointer_when_one_zone_is_not_a_conflict():
    with pytest.raises(anchorkit.AnchorError) as e:
        anchorkit.run_anchor({"stamp": "2026-11-02 09:00",
                              "run_in": "Europe/Paris"})
    assert "tz_ambiguity" in str(e.value)


# ================================================= HTTP + pins

def test_http_determinism_both_routes():
    for path, body in (
            ("/api/v1/money/points", CARD),
            ("/api/v1/date/tz_anchor", {"stamp": "2026-11-02 09:00",
                                        "meant_in": "Europe/Paris",
                                        "run_in": "UTC"})):
        r1 = client.post(path, json=body)
        r2 = client.post(path, json=body)
        assert r1.status_code == r2.status_code == 200, path
        assert r1.content == r2.content
        assert r1.json()["sha256"]


def test_http_refusals_are_400_named():
    r = client.post("/api/v1/date/tz_anchor",
                    json={"stamp": "2026-11-02 09:00",
                          "meant_in": "Europe/Paris"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "run_in"
    r = client.post("/api/v1/money/points", json={
        "currency": "USD", "routes": [{"name": "a", "points": "1",
                                       "cash_price": "1"},
                                      {"name": "a", "points": "1",
                                       "cash_price": "2"}]})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "routes"


def test_http_number_input_refused_declared():
    r = client.post("/api/v1/date/tz_anchor",
                    json={"stamp": 1730545200, "meant_in": "UTC",
                          "run_in": "UTC"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "body.stamp"
    r = client.post("/api/v1/money/points", json={
        "currency": "USD",
        "routes": [{"name": "a", "points": 29000,
                    "cash_price": "438"}]})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "points"


def test_route_first_for_pain_phrases():
    for q, path in (
            ("naive timestamp server anchored utc job fires late wrong "
             "time config zone drift", "/api/v1/date/tz_anchor"),
            ("my scheduler stores utc but I wrote 9am Paris time how "
             "late does it fire", "/api/v1/date/tz_anchor"),
            ("le cron est ecrit en heure de paris mais le serveur est "
             "en utc avec quel decalage il part vraiment",
             "/api/v1/date/tz_anchor"),
            ("o servidor esta em utc mas meu horario foi escrito para "
             "sao paulo com quantos minutos de atraso dispara",
             "/api/v1/date/tz_anchor"),
            ("the server is utc but i wrote the time meant for paris "
             "so my job fires early by two hours",
             "/api/v1/date/tz_anchor"),
            ("how many cents per point is this redemption worth travel "
             "portal transfer statement", "/api/v1/money/points"),
            ("credit card points value redeem flight taxes cpp balance",
             "/api/v1/money/points"),
            ("combien vaut un point en centimes quand il faut payer les "
             "taxes du portail", "/api/v1/money/points"),
            ("quantos centavos vale cada ponto no resgate com taxas de "
             "transferencia", "/api/v1/money/points"),
            ("60000 points for a 900 dollar flight minus 5 60 taxes is "
             "that 1 5 cpp", "/api/v1/money/points")):
        r = client.get("/route", params={"q": q})
        assert r.status_code == 200, q
        assert r.json()["tools"][0]["path"] == path, (q, r.json()["tools"][0])


def test_sister_phrases_still_mine_their_own():
    # leçons du cycle 13h51 : les phrases des voisins ne changent PAS
    # de camp quand un nouveau tool arrive
    for q, tool in (
            ("date timezone conversion paris to new york", "date_tz"),
            ("dst fall back runs twice duplicate wall clock nonexistent",
             "date_tz_ambiguity"),
            ("which tariff is cheaper above how many kwh standing "
             "charge crossover", "money_crossover"),
            ("a partir de combien de kwh le tarif b gagne",
             "money_crossover")):
        r = client.get("/route", params={"q": q})
        assert r.json()["tools"][0]["tool"] == tool, q


def test_mcp_tools_replay_both():
    for name, args, keys in (
            ("money_points", CARD, ['"cpp"', "1.491034482759"]),
            ("date_tz_anchor", {"stamp": "2026-11-02 09:00",
                                "meant_in": "Europe/Paris",
                                "run_in": "UTC"},
             ['"drift"', "60 min LATE"])):
        body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": name, "arguments": args}}
        r = client.post("/mcp", json=body)
        assert r.status_code == 200, name
        txt = r.json()["result"]["content"][0]["text"]
        for k in keys:
            assert k in txt, (name, k)
