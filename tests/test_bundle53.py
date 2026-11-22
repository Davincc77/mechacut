# -*- coding: utf-8 -*-
"""bundle53 — /money/crossover + /csv/excel_display.

ORACLES. Crossover : chaque attente est CALCULÉE À LA MAIN (divisions
longues commentées) sur les SEPT calculateurs publiés rejoués ce
cycle — uxtaxdrag (X 25p/60p vs Y 27p/45p : 0,15×365=54,75 ; ÷0,02 =
2 737,5 EXACT, leur « about 2 738 » est déjà un arrondi), numbivo
(12→144 vs 22→264 ; 120÷0,04 = 3 000/an = 250/mois), gasbillcalculator
(0,0532×365 = −19,418 ÷ −0,0042 : 97090/21 = 13870/3 = 4 623⅓ — eux
arrondissent 19,42 et trouvent 4 623,81 ; LA TRAPPE D'ARRONDI
INTERMÉDIAIRE est le vecteur), rightsums (0,2483×365 = 90,6295 ÷
0,0418 = 906295/418, irreductible : 418=2·11·19, 906295 impair, ÷11
et ÷19 non entiers), energysolutions (40p×365=146 ÷ 1p = 14 600),
expatcalc (36,50÷0,02=1 825). Convention mensuelle ×12 EXACT, jamais
30 jours ; jours 365/366 nommés (0,15×366=54,90÷0,02=2 745) ;
km = bascule × efficacité FOURNIE ; payback = frais one-off ÷ économie
mensuelle (60 ÷ 2 = 30 mois ; le sens inverse one_off=0 → None).

Display : exemples RÉ SOLUS de la table des symboles Microsoft
(« Format Cells dialog ») rejoués verbatim — « #.0,, »+12 200 000 →
« 12.2 » ; « (000) »+12 → « (012) » ; « 0% »+0,5 → « 50% » ; « 0.00
"dollars" »+1,23 ; 1,2345 sous « 0.00 » → 1,23 ; « #.## »+8,9 → 8,9 ;
« 0.0? »+8,9 → « 8.9 » + ESPACE (le ? padde, jamais ne tronque) ;
arrondi de display demi-vers-le-large (2,5→3, 3,5→4, −2,5→−3) ;
le B9 d'arXiv 2611.05806 : stocké 1 000 000 sous « $#,##0, » →
« $1,000 ». Locale FORK sur le MÊME code : « 1234567.891 » sous
« #,##0.00 » = « 1,234,567.89 » EN / « 1.234.567,89 » DE (l'ingénieur
Microsoft : les séparateurs du fichier sont des SYMBOLES). Refus NOMMÉS
: General (largeur), E-notation, dates (m/d/y/h), [Red], * et _, texte
@ (4 sections), lakh ##,##,###, deux points décimaux.
"""

import pytest
from fastapi.testclient import TestClient

import crosskit
import displaykit
import main as m

client = TestClient(m.app)
m.RATE_LIMIT = 10**9


# ==================================================== crossover : la bascule

def test_uxtaxdrag_exact_half():
    # 0,15×365 = 54,75 ; 54,75÷0,02 = 5475/2 = 2 737,5
    r = crosskit.run_crossover({
        "a_unit_rate": "0.25", "a_unit_per": "kWh",
        "a_fixed": "0.60", "a_fixed_per": "day",
        "b_unit_rate": "0.27", "b_unit_per": "kWh",
        "b_fixed": "0.45", "b_fixed_per": "day", "currency": "GBP"})
    assert r["crossover"]["per_year"] == "2737.5"
    assert r["crossover"]["per_year_fraction"] == {"numerator": "5475",
                                                   "denominator": "2"}
    # 2 737,5 ÷ 12 = 228,125 (division longue : 2737,5/12 = 228 + 1,5/12)
    assert r["crossover"]["per_month"] == "228.125"
    # Y a le fixe le plus bas (45<60) : gagne SOUS la bascule ; X a
    # l'unitaire le plus bas (25<27) : gagne AU-DESSUS — publié uxtaxdrag
    assert r["verdict"]["below_crossover"] == "plan_b"
    assert r["verdict"]["above_crossover"] == "plan_a"


def test_numbivo_monthly_times_twelve_not_360():
    # 12/mois → 144/an ; 22 → 264 ; d_fix = -120 ; d_unit = -0,04
    # -120/-0,04 = 3 000 ; /12 = 250/mois — le publié numbivo dit 250 ✓
    r = crosskit.run_crossover({
        "a_unit_rate": "0.30", "a_unit_per": "kWh",
        "a_fixed": "12", "a_fixed_per": "month",
        "b_unit_rate": "0.26", "b_unit_per": "kWh",
        "b_fixed": "22", "b_fixed_per": "month", "currency": "EUR"})
    assert r["crossover"]["per_year"] == "3000"
    assert r["crossover"]["per_month"] == "250"
    assert r["plans"]["a"]["fixed_annualised"] == "144"
    # la convention est DITE, pas fondue : 12 mois exacts
    assert "12" in r["day_convention"]["monthly_fixed_rule"]


def test_gasbill_intermediate_rounding_trap():
    # (0,2968−0,35)×365 = −19,418 EXACT ; ÷−0,0042 = 97090/21 = 13870/3
    # (gcd 7) — les publieurs arrondissent 19,42 → 4 623,81 : faux
    r = crosskit.run_crossover({
        "a_unit_rate": "0.0797", "a_unit_per": "kWh",
        "a_fixed": "0.2968", "a_fixed_per": "day",
        "b_unit_rate": "0.0755", "b_unit_per": "kWh",
        "b_fixed": "0.35", "b_fixed_per": "day", "currency": "GBP"})
    assert r["crossover"]["per_year_fraction"] == {"numerator": "13870",
                                                   "denominator": "3"}


def test_rightsums_irreducible_fraction():
    # 0,2483×365 = 90,6295 → 906295/10000 ; 0,0418 = 418/10000
    # 906295/418 : 418=2·11·19 ; 906295 impair ; /11=82390,45 ; /19=
    # 47699,74 — irreductible
    r = crosskit.run_crossover({
        "a_unit_rate": "0.2632", "a_unit_per": "kWh",
        "a_fixed": "0.5483", "a_fixed_per": "day",
        "b_unit_rate": "0.3050", "b_unit_per": "kWh",
        "b_fixed": "0.30", "b_fixed_per": "day", "currency": "GBP"})
    assert r["crossover"]["per_year_fraction"] == {"numerator": "906295",
                                                   "denominator": "418"}


def test_energysolutions_14600():
    # (0,90−0,50)×365 = 146 ; ÷0,01 = 14 600 — publié energysolutions ✓
    r = crosskit.run_crossover({
        "a_unit_rate": "0.24", "a_unit_per": "kWh",
        "a_fixed": "0.90", "a_fixed_per": "day",
        "b_unit_rate": "0.25", "b_unit_per": "kWh",
        "b_fixed": "0.50", "b_fixed_per": "day", "currency": "GBP"})
    assert r["crossover"]["per_year"] == "14600"


def test_domination_never_is_the_answer():
    # A gagne sur les DEUX (0,24<0,26 et 120<144) : aucun point positif
    r = crosskit.run_crossover({
        "a_unit_rate": "0.24", "a_unit_per": "kWh",
        "a_fixed": "10", "a_fixed_per": "month",
        "b_unit_rate": "0.26", "b_unit_per": "kWh",
        "b_fixed": "12", "b_fixed_per": "month", "currency": "EUR"})
    assert r["verdict"]["kind"] == "domination"
    assert r["verdict"]["winner_always"] == "plan_a"
    assert r["crossover"] is None
    # solution signée −1 200 (négative = jamais)
    assert r["verdict"]["signed_solution"] == "-1200"


def test_equal_rates_no_tradeoff_and_equal_fixed_immediate():
    r = crosskit.run_crossover({
        "a_unit_rate": "0.25", "a_unit_per": "kWh",
        "a_fixed": "10", "a_fixed_per": "month",
        "b_unit_rate": "0.25", "b_unit_per": "kWh",
        "b_fixed": "12", "b_fixed_per": "month", "currency": "EUR"})
    assert r["verdict"]["kind"] == "no-tradeoff"
    assert r["verdict"]["winner_always"] == "plan_a"
    r = crosskit.run_crossover({
        "a_unit_rate": "0.24", "a_unit_per": "kWh",
        "a_fixed": "10", "a_fixed_per": "month",
        "b_unit_rate": "0.26", "b_unit_per": "kWh",
        "b_fixed": "10", "b_fixed_per": "month", "currency": "EUR"})
    assert r["verdict"]["kind"] == "immediate-crossover"
    assert r["verdict"]["winner_above_zero"] == "plan_a"


def test_leap_year_named_shifts_the_answer():
    # cas uxtaxdrag avec 366 : 0,15×366 = 54,90 ÷ 0,02 = 2 745
    r = crosskit.run_crossover({
        "a_unit_rate": "0.25", "a_unit_per": "kWh",
        "a_fixed": "0.60", "a_fixed_per": "day",
        "b_unit_rate": "0.27", "b_unit_per": "kWh",
        "b_fixed": "0.45", "b_fixed_per": "day", "currency": "GBP",
        "days_per_year": "366"})
    assert r["crossover"]["per_year"] == "2745"


def test_mwh_normalized_to_kwh_exactly():
    # 250 vs 270 €/MWh : d_unit 20 ; 54,75/20 × 1000 = 2 737,5 kWh
    r = crosskit.run_crossover({
        "a_unit_rate": "250", "a_unit_per": "MWh",
        "a_fixed": "0.60", "a_fixed_per": "day",
        "b_unit_rate": "270", "b_unit_per": "MWh",
        "b_fixed": "0.45", "b_fixed_per": "day", "currency": "GBP"})
    assert r["crossover"]["per_year"] == "2737.5"
    assert r["crossover"]["unit"] == "kWh"


def test_generic_unit_passthrough():
    # fixes 60 vs 108 : d_fix = −48 ; d_unit = 0,008−0,01 = −0,002 ;
    # −48/−0,002 = 24 000 GB/an
    r = crosskit.run_crossover({
        "a_unit_rate": "0.01", "a_unit_per": "GB",
        "a_fixed": "5", "a_fixed_per": "month",
        "b_unit_rate": "0.008", "b_unit_per": "GB",
        "b_fixed": "9", "b_fixed_per": "month", "currency": "EUR"})
    assert r["crossover"]["per_year"] == "24000"
    assert r["crossover"]["unit"] == "GB"


def test_ev_distance_only_when_supplied():
    # 3 000 kWh × 6 km/kWh = 18 000 km/an ; ÷12 = 1 500
    r = crosskit.run_crossover({
        "a_unit_rate": "0.30", "a_unit_per": "kWh",
        "a_fixed": "12", "a_fixed_per": "month",
        "b_unit_rate": "0.26", "b_unit_per": "kWh",
        "b_fixed": "22", "b_fixed_per": "month", "currency": "EUR",
        "km_per_unit": "6"})
    assert r["crossover"]["distance"]["distance_per_year"] == "18000"
    assert r["crossover"]["distance"]["distance_per_month"] == "1500"


def test_costs_and_payback_side_by_side():
    # à 3 600 kWh/an : A = 1 080+144 = 1 224 ; B = 936+264 = 1 200 ;
    # économie a→b = 24/an = 2/mois ; one-off 60 → payback 30,00 mois ;
    # net première année 24−60 = −36 ; le sens b→a : one_off 0 → None
    r = crosskit.run_crossover({
        "a_unit_rate": "0.30", "a_unit_per": "kWh",
        "a_fixed": "12", "a_fixed_per": "month",
        "b_unit_rate": "0.26", "b_unit_per": "kWh",
        "b_fixed": "22", "b_fixed_per": "month", "currency": "EUR",
        "usage_per_period": "3600", "usage_period": "year",
        "exit_fee_a": "60"})
    assert r["at_usage"]["plan_a"]["total"] == "1224.00"
    assert r["at_usage"]["plan_b"]["total"] == "1200.00"
    assert r["fees"]["a_to_b"]["payback_months"] == "30.00"
    assert r["fees"]["a_to_b"]["net_first_year_saving"] == "-36.00"
    assert r["fees"]["b_to_a"]["payback_months"] is None


def test_usage_costs_above_crossover_flip_the_winner():
    # à 2 000 kWh/an (SOUS 3 000) : A = 600+144 = 744 ; B = 520+264 =
    # 784 ; A gagne de 40 ; à 4 000 (AU-DESSUS) : A = 1 344, B = 1 304,
    # B gagne de 40
    base = {"a_unit_rate": "0.30", "a_unit_per": "kWh",
            "a_fixed": "12", "a_fixed_per": "month",
            "b_unit_rate": "0.26", "b_unit_per": "kWh",
            "b_fixed": "22", "b_fixed_per": "month", "currency": "EUR"}
    r = crosskit.run_crossover(dict(base, usage_per_period="2000",
                                    usage_period="year"))
    assert r["at_usage"]["plan_a"]["total"] == "744.00"
    assert r["at_usage"]["plan_b"]["total"] == "784.00"
    assert r["at_usage"]["cheaper"] == "plan_a"
    r = crosskit.run_crossover(dict(base, usage_per_period="4000",
                                    usage_period="year"))
    assert r["at_usage"]["cheaper"] == "plan_b"


def test_crossover_refusals_named():
    base = {"a_unit_rate": "0.30", "a_unit_per": "kWh",
            "b_unit_rate": "0.26", "b_unit_per": "kWh",
            "a_fixed": "12", "b_fixed": "22", "currency": "EUR"}
    with pytest.raises(crosskit.CrossError) as e:
        crosskit.run_crossover(dict(base, a_fixed_per="week",
                                    b_fixed_per="month"))
    assert e.value.field == "a_fixed_per"
    with pytest.raises(crosskit.CrossError) as e:
        crosskit.run_crossover(dict(base, a_fixed_per="month",
                                    b_fixed_per="month",
                                    b_unit_per="MWh"))
    assert e.value.field == "b_unit_per"
    with pytest.raises(crosskit.CrossError) as e:
        crosskit.run_crossover(dict(base, a_fixed_per="month",
                                    b_fixed_per="month",
                                    currency="XXX"))
    assert e.value.field == "currency"
    with pytest.raises(crosskit.CrossError) as e:
        crosskit.run_crossover(dict(base, a_fixed_per="month",
                                    b_fixed_per="month",
                                    a_unit_rate="-0.30"))
    assert e.value.field == "a_unit_rate"
    with pytest.raises(crosskit.CrossError) as e:
        crosskit.run_crossover(dict(base, a_fixed_per="month",
                                    b_fixed_per="month",
                                    a_unit_rate="24p"))
    assert e.value.field == "a_unit_rate"
    with pytest.raises(crosskit.CrossError) as e:
        crosskit.run_crossover(dict(base, a_fixed_per="month",
                                    b_fixed_per="month",
                                    days_per_year="360"))
    assert e.value.field == "days_per_year"


# ==================================================== display : la table MS

def _d(v, f, locale=None):
    a = {"value": v, "format": f}
    if locale:
        a["locale"] = locale
    return displaykit.run_display(a)["displayed"]


def test_b9_thousand_scale_the_arxiv_attack():
    # arXiv 2611.05806 : stocké 1 000 000, « $#,##0, » → $1,000
    r = displaykit.run_display({"value": "1000000", "format": "$#,##0,"})
    assert r["displayed"] == "$1,000"
    # et le STOCKÉ reste 1000000 dans la réponse — la divergence DITE
    assert r["stored"] == "1000000"


def test_ms_table_examples_verbatim():
    assert _d("12200000", "#.0,,") == "12.2"      # ÷10^6, 1 décimale
    assert _d("12", "(000)") == "(012)"           # 0 = padding zéro
    assert _d("0.5", "0%") == "50%"               # ×100 ET signe
    assert _d("1.23", '0.00 "dollars"') == "1.23 dollars"
    assert _d("1.2345", "0.00") == "1.23"         # le stocké ne bouge pas
    assert _d("8.9", "#.##") == "8.9"             # # : pas de zéro nu
    assert _d("8.9", "0.0?") == "8.9 "            # ? : ESPACE signifiant
    # schneide.blog : le XML stocke 25604.880000000001
    assert _d("25604.880000000001", "0.00") == "25604.88"


def test_display_rounding_half_away_from_zero():
    assert _d("2.5", "0") == "3"
    assert _d("3.5", "0") == "4"
    assert _d("-2.5", "0") == "-3"    # sur l'absolue, puis signe


def test_sections_positive_negative_zero():
    assert _d("-2.34", "0.00;(0.00)") == "(2.34)"
    assert _d("-4.5", "0.00;-0.00") == "-4.50"
    assert _d("0", "0.0;-0.0;(0.0)") == "(0.0)"
    # deux sections : zéro passe par la positive
    assert _d("0", "0.00;(0.00)") == "0.00"
    # une section : le signe '-' est devant
    assert _d("-1500000", "$#,##0,") == "-$1,500"
    assert _d("0", "#,##0") == "0"


def test_locale_symbols_fork_same_code():
    # la MÊME cellule, deux affichages — l'ingénieur Microsoft :
    # séparateurs du fichier = symboles invariants
    assert _d("1234567.891", "#,##0.00") == "1,234,567.89"
    assert _d("1234567.891", "#,##0.00", "de-DE") == "1.234.567,89"
    assert _d("1234.5", "#,##0.00", "fr-FR") == "1\u00a0234,50"


def test_display_refusals_by_name():
    for fmt in ("General", "0.00E+00", "yyyy-mm-dd", "[Red]-0.00",
                "0*x", "_-0.00", "0.0;-0.0;0.0;@", "##,##,###.00",
                "0.0.0"):
        with pytest.raises(displaykit.DisplayError) as e:
            _d("1", fmt)
        assert e.value.field == "format", fmt
    with pytest.raises(displaykit.DisplayError) as e:
        displaykit.run_display({"value": "1", "format": "0.00",
                                "locale": "xx-YY"})
    assert e.value.field == "locale"
    with pytest.raises(displaykit.DisplayError) as e:
        displaykit.run_display({"value": "abc", "format": "0.00"})
    assert e.value.field == "value"
    with pytest.raises(displaykit.DisplayError) as e:
        displaykit.run_display({"value": "1", "format": ""})
    assert e.value.field == "format"


# ==================================================== HTTP + pins

def test_http_determinism_both_routes():
    for path, body in (
            ("/api/v1/money/crossover", {
                "a_unit_rate": "0.25", "a_unit_per": "kWh",
                "a_fixed": "0.60", "a_fixed_per": "day",
                "b_unit_rate": "0.27", "b_unit_per": "kWh",
                "b_fixed": "0.45", "b_fixed_per": "day",
                "currency": "GBP"}),
            ("/api/v1/csv/excel_display", {
                "value": "1000000", "format": "$#,##0,"})):
        r1 = client.post(path, json=body)
        r2 = client.post(path, json=body)
        assert r1.status_code == r2.status_code == 200
        assert r1.content == r2.content
        assert r1.json()["sha256"]


def test_http_refusals_are_400_named():
    r = client.post("/api/v1/money/crossover", json={
        "a_unit_rate": "0.30", "a_unit_per": "kWh",
        "a_fixed": "1", "a_fixed_per": "week",
        "b_unit_rate": "0.26", "b_unit_per": "kWh",
        "b_fixed": "2", "b_fixed_per": "month", "currency": "EUR"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "a_fixed_per"
    r = client.post("/api/v1/csv/excel_display",
                    json={"value": "1", "format": "General"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "format"


def test_http_number_input_refused_declared():
    # contrat d'entrée = CHAÎNES (leçon permanente, ScaleRequest) : un
    # JSON number est un 400 NOMMÉ sur les DEUX routes, jamais une
    # coercition silencieuse. Vérifié en prod-like avant d'écrire
    # l'attente : field 'body.<x>', message 'Input should be a valid
    # string' — c'est le TEST qui avait tort en visant le 422 FastAPI.
    r = client.post("/api/v1/csv/excel_display",
                    json={"value": 1000000, "format": "$#,##0,"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "body.value"
    r = client.post("/api/v1/money/crossover", json={
        "a_unit_rate": 0.30, "a_unit_per": "kWh",
        "a_fixed": "12", "a_fixed_per": "month",
        "b_unit_rate": "0.26", "b_unit_per": "kWh",
        "b_fixed": "22", "b_fixed_per": "month", "currency": "EUR"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "body.a_unit_rate"


def test_route_first_for_pain_phrases():
    for q, path in (
            ("which tariff is cheaper above how many kwh standing "
             "charge crossover", "/api/v1/money/crossover"),
            ("plan a lower unit rate plan b lower standing charge "
             "break even", "/api/v1/money/crossover"),
            ("à partir de combien de kwh le tarif b gagne",
             "/api/v1/money/crossover"),
            ("a partir de quantos kwh o plano b e mais barato",
             "/api/v1/money/crossover"),
            ("excel shows different value than stored numfmt budget",
             "/api/v1/csv/excel_display"),
            ("openpyxl reads the stored number not what excel displays",
             "/api/v1/csv/excel_display"),
            ("ce que excel affiche de la valeur stockée format nombre",
             "/api/v1/csv/excel_display")):
        r = client.get("/route", params={"q": q})
        assert r.status_code == 200, q
        assert r.json()["tools"][0]["path"] == path, q


def test_mcp_tools_replay_both():
    for name, args, key in (
            ("money_crossover", {
                "a_unit_rate": "0.25", "a_unit_per": "kWh",
                "a_fixed": "0.60", "a_fixed_per": "day",
                "b_unit_rate": "0.27", "b_unit_per": "kWh",
                "b_fixed": "0.45", "b_fixed_per": "day",
                "currency": "GBP"}, '"crossover"'),
            ("csv_excel_display", {"value": "12200000",
                                   "format": "#.0,,"}, '"displayed"')):
        body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": name, "arguments": args}}
        r = client.post("/mcp", json=body)
        assert r.status_code == 200, name
        txt = r.json()["result"]["content"][0]["text"]
        assert key in txt, name
        assert "2737.5" in txt or "12.2" in txt, name
