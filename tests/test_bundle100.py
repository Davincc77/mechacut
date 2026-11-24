# -*- coding: utf-8 -*-
"""Bundle 100 — /money/keep-records-uk : la date de destruction, par
règle officielle ancrée, UK, conflits et blocages nommés.

Golds tracés À LA MAIN (oracle séparé écrit AVANT le module, scratch
g100_oracle.py), jamais recoupés depuis la sortie du module. Les deux
EXEMPLES OFFICIELLS de gov.uk sont rejoués comme vecteurs :

  SA 2022-23 (fin 2023-04-05) -> deadline 2024-01-31 -> « until at
    least the end of January 2029 » -> retain 2029-01-31, destruction
    dès 2029-02-01 (convention « until at least » = le jour dit est le
    DERNIER jour gardé, détruire = +1).
  SA 2026-27 (fin 2027-04-05, exemple MTD) -> deadline 2028-01-31 ->
    « until at least 31 January 2033 » -> 2033-01-31 / 2033-02-01.
  Very late : deadline 2024-01-31, seuil 4 ans = 2028-01-31, rendu
    2029-06-15 > seuil -> 15 mois après ENVOI = 2030-09-15 ; les DEUX
    règles voyagent, la plus longue gouverne (CH14100 verbatim).
  Late-not-very : rendu 2024-06-01 <= 2028-01-31 -> la règle 15 mois
    NE S'OUVRE PAS, la règle 5 ans reste seule (2029-01-31).
  VAT : invoice émise 2026-11-24 -> 6 ans depuis ÉMISSION ->
    2032-11-24 ; résumé préparé 2026-07-01 -> 2032-07-01 ; série
    dernière entrée 2026-01-31 -> 2032-01-31 ; OSS -> 10 ans ->
    2036-11-24 ; bad debt -> 4 ans depuis la RÉCLAMATION -> 2030-11-24.
  s.388(4) : privé 3 ans / public 6 ans depuis la date de CRÉATION
    (2026-11-24 -> 2029-11-24 / 2032-11-24) ; 2024-02-29 + 3 ->
    2027-02-28 (clamp dernier jour de février, NON bissextile).
  LTD + s388 max : FY end 2023-12-31 + made_on 2023-11-10, privé ->
    s.388 retient jusqu'à 2026-11-10, le fisc jusqu'à 2029-12-31 ;
    governing = ct_records_6y, destruction 2030-01-01 (l'exemple
    harrisons « keep until at least 31 December 2029 » recoupe).
  PAYE/CIS année closant 2026-04-05 -> 3 ans -> 2029-04-05 /
    destruction 2029-04-06 ; 2026-04-06 REFUSÉ : l'année fiscale est
    définie par la loi (ITA 2007 s.4(3), fin 5 avril).
  days_left PAYE à as_of 2026-11-24 : 2026-11-24 -> 2027-11-24 = 365,
    -> 2028-11-24 = 366 (févr. 2028 bissextile) = 731, -> 2029-04-05 =
    132 (6+31+31+28+31+5) ; TOTAL 863.
"""
import json
from datetime import date

import pytest

import retentionkit as rk

VAT_ISSUED = dict(record_kind="vat_invoice", issued_on="2026-11-24")


def _gov(out):
    return [r for r in out["rules"] if r["status"] == "applied"]


def test_vat_invoice_anchors_from_issue():
    out = rk.keep_records(**VAT_ISSUED)
    r = _gov(out)[0]
    assert r["retain_until"] == "2032-11-24"
    assert r["earliest_destroy_on"] == "2032-11-25"
    assert "6 years from the date of issue" in r["verbatim"]
    assert r["anchor_field"] == "issued_on"
    assert out["jurisdiction"] == "UK"
    assert out["status"] == "COMPUTED"
    assert out["safe_destroy_on"] == "2032-11-25"
    assert out["table_version"] == "2026-11-24"


def test_future_event_document_keeps_issue_anchor():
    out = rk.keep_records(**VAT_ISSUED)
    note = [n for n in out["notes"] if n["note"] == "future_event"][0]
    assert ("runs not from the date of the future event but from the "
            "date on which the document itself is issued") in note["verbatim"]


def test_vat_summary_prepared_anchor():
    out = rk.keep_records(record_kind="vat_summary", prepared_on="2026-07-01")
    r = _gov(out)[0]
    assert (r["retain_until"], r["earliest_destroy_on"]) == \
        ("2032-07-01", "2032-07-02")
    assert "6 years from the date they are prepared" in r["verbatim"]


def test_vat_series_last_entry_and_piecemeal():
    out = rk.keep_records(record_kind="vat_series", last_entry_on="2026-01-31")
    r = _gov(out)[0]
    assert (r["retain_until"], r["earliest_destroy_on"]) == \
        ("2032-01-31", "2032-02-01")
    assert any(n["note"] == "piecemeal" for n in out["notes"])
    tab = [n for n in out["notes"] if n["note"] == "ch15400_minimums"][0]
    assert tab["verbatim"][-1] == ("Any record containing the VAT account",
                                   "6 years (No reduction)")
    assert tab["arbitrage"] == ("If a record falls within more than one of "
                                "the categories above, apply the longer "
                                "retention period.")


def test_vat_oss_is_ten_years():
    out = rk.keep_records(record_kind="vat_invoice", issued_on="2026-11-24",
                          scheme="oss")
    r = _gov(out)[0]
    assert r["retain_until"] == "2036-11-24"
    assert "(or 10 years if you are using the VAT One Stop Shop (OSS) " \
        "scheme or used the VAT Mini One Stop Shop (MOSS) scheme)" in \
        r["scheme_verbatim"]
    out2 = rk.keep_records(record_kind="vat_summary", prepared_on="2026-07-01",
                           scheme="moss")
    assert _gov(out2)[0]["retain_until"] == "2036-07-01"


def test_scheme_grammar_closed():
    with pytest.raises(rk.RetentionError) as e:
        rk.keep_records(record_kind="vat_invoice", issued_on="2026-11-24",
                        scheme="css")
    assert e.value.field == "scheme"


def test_vat_leap_clamp():
    out = rk.keep_records(record_kind="vat_invoice", issued_on="2024-02-29")
    r = _gov(out)[0]
    assert (r["retain_until"], r["earliest_destroy_on"]) == \
        ("2030-02-28", "2030-03-01")


def test_bad_debt_claim_four_years_from_claim():
    out = rk.keep_records(record_kind="vat_bad_debt_claim",
                          claim_on="2026-11-24")
    r = _gov(out)[0]
    assert (r["retain_until"], r["earliest_destroy_on"]) == \
        ("2030-11-24", "2030-11-25")
    out2 = rk.keep_records(record_kind="vat_bad_debt_claim",
                           claim_on="2026-11-24", vatmoss_used=True)
    assert _gov(out2)[0]["retain_until"] == "2036-11-24"
    note = [n for n in out["notes"] if n["note"] == "claim_window"][0]
    assert "within 4 years and 6 months" in note["verbatim"]


def test_ltd_six_years_from_financial_year_end():
    out = rk.keep_records(record_kind="company_tax_records",
                          financial_year_end_on="2023-12-31")
    r = _gov(out)[0]
    assert (r["retain_until"], r["earliest_destroy_on"]) == \
        ("2029-12-31", "2030-01-01")
    assert "6 years from the end of the last company financial year" in \
        r["verbatim"]


def test_ltd_blocked_conditions_are_named_not_guessed():
    out = rk.keep_records(record_kind="company_tax_records",
                          financial_year_end_on="2023-12-31",
                          return_late=True, compliance_check_open=True,
                          spans_periods=True, asset_beyond_six_years=True)
    assert out["status"] == "BLOCKED_EXTENSION"
    assert out["safe_destroy_on"] is None
    assert out["lower_bound_retain_until"] == "2029-12-31"
    assert sorted(out["blocked_by"]) == ["ct_compliance_check",
                                         "ct_late_return", "ct_long_asset",
                                         "ct_spans_periods"]
    late = [r for r in out["rules"] if r["id"] == "ct_late_return"][0]
    assert "no fixed" in late["reason"]


def test_ltd_plus_s388_both_rows_the_longest_governs():
    out = rk.keep_records(record_kind="company_tax_records",
                          financial_year_end_on="2023-12-31",
                          entity="private", made_on="2023-11-10")
    rs = {(r["retain_until"]) for r in _gov(out)}
    assert rs == {"2026-11-10", "2029-12-31"}
    assert out["governing_rule"] == "ct_records_6y"
    assert out["safe_destroy_on"] == "2030-01-01"
    note = [n for n in out["notes"] if n["note"] == "longest_governs"][0]
    assert note["verbatim"] == ("Any record that serves more than one "
                                "purpose must be kept for the longest "
                                "period required by those purposes.")


def test_ltd_entity_without_made_on_carries_uncomputed_row():
    out = rk.keep_records(record_kind="company_tax_records",
                          financial_year_end_on="2023-12-31",
                          entity="public")
    assert [n["note"] for n in out["notes"]] == ["s388_uncomputed"]
    assert out["safe_destroy_on"] == "2030-01-01"


def test_s388_branches_on_the_form():
    p = rk.keep_records(record_kind="companies_act_accounting",
                        made_on="2026-11-24", entity="private")
    b = rk.keep_records(record_kind="companies_act_accounting",
                        made_on="2026-11-24", entity="public")
    assert _gov(p)[0]["retain_until"] == "2029-11-24"
    assert _gov(b)[0]["retain_until"] == "2032-11-24"
    leap = rk.keep_records(record_kind="companies_act_accounting",
                           made_on="2024-02-29", entity="private")
    assert _gov(leap)[0]["earliest_destroy_on"] == "2027-03-01"


def test_s388_entity_grammar():
    with pytest.raises(rk.RetentionError) as e:
        rk.keep_records(record_kind="companies_act_accounting",
                        made_on="2026-11-24")
    assert e.value.field == "entity"
    with pytest.raises(rk.RetentionError) as e2:
        rk.keep_records(record_kind="companies_act_accounting",
                        made_on="2026-11-24", entity="llp")
    assert "with modifications" in e2.value.message


def test_sa_official_example_replayed():
    out = rk.keep_records(record_kind="self_assessment",
                          tax_year_end_on="2023-04-05")
    r = _gov(out)[0]
    assert r["anchor_on"] == "2024-01-31"
    assert r["retain_until"] == "2029-01-31"
    assert r["earliest_destroy_on"] == "2029-02-01"
    assert ("sent your 2022 to 2023 tax return online by 31 January "
            "2024") in r["official_example"]


def test_sa_second_official_example_mtd():
    out = rk.keep_records(record_kind="self_assessment",
                          tax_year_end_on="2027-04-05")
    assert _gov(out)[0]["retain_until"] == "2033-01-31"


def test_sa_very_late_opens_second_clock_and_longest_rules():
    out = rk.keep_records(record_kind="self_assessment",
                          deadline_on="2024-01-31", filed_on="2029-06-15")
    rs = {(r["retain_until"], r["earliest_destroy_on"]) for r in _gov(out)}
    assert rs == {("2029-01-31", "2029-02-01"),
                  ("2030-09-15", "2030-09-16")}
    assert out["governing_rule"] == "sa_very_late_15m"
    assert out["safe_destroy_on"] == "2030-09-16"


def test_sa_late_but_not_very_late_keeps_one_clock():
    out = rk.keep_records(record_kind="self_assessment",
                          deadline_on="2024-01-31", filed_on="2024-06-01")
    assert len(_gov(out)) == 1
    assert out["retain_until"] == "2029-01-31"
    note = [n for n in out["notes"] if n["note"] == "late_not_very_late"][0]
    assert "does NOT open" in note["effect"]


def test_sa_anchors_conflict_and_grammar():
    with pytest.raises(rk.RetentionError) as e:
        rk.keep_records(record_kind="self_assessment",
                        deadline_on="2024-01-31", tax_year_end_on="2027-04-05")
    assert e.value.field == "deadline_on"
    with pytest.raises(rk.RetentionError) as e2:
        rk.keep_records(record_kind="self_assessment")
    assert e2.value.field == "tax_year_end_on"
    with pytest.raises(rk.RetentionError) as e3:
        rk.keep_records(record_kind="self_assessment",
                        deadline_on="2024-02-29")
    assert e3.value.field == "deadline_on"


def test_paye_cis_expenses_three_years_from_tax_year_end():
    for k in ("paye", "cis", "expenses_benefits"):
        out = rk.keep_records(record_kind=k, tax_year_end_on="2026-04-05")
        r = _gov(out)[0]
        assert (r["retain_until"], r["earliest_destroy_on"]) == \
            ("2029-04-05", "2029-04-06"), k
    with pytest.raises(rk.RetentionError) as e:
        rk.keep_records(record_kind="paye", tax_year_end_on="2026-04-06")
    assert "ITA 2007 s.4(3)" in e.value.message


def test_as_of_days_left_hand_traced():
    out = rk.keep_records(record_kind="paye", tax_year_end_on="2026-04-05",
                          as_of="2026-11-24")
    assert out["days_left_in_retention"] == (date(2029, 4, 5)
                                             - date(2026, 11, 24)).days
    assert out["days_left_in_retention"] == 863
    assert out["expired"] is False
    out2 = rk.keep_records(record_kind="paye", tax_year_end_on="2026-04-05",
                           as_of="2030-01-01")
    assert out2["days_left_in_retention"] == -271
    assert out2["expired"] is True


def test_refusals_carry_their_facts():
    for kind, fact in (
            ("personal_22_months", "archived Tax Help PDF"),
            ("national_minimum_wage", "pay reference period"),
            ("france", "not replayed this cycle"),
            ("gdpr", "duty to DELETE"),
            ("scotland", "Scots-law prescription"),
            ("employment_contract", "GUARANTEE kit's")):
        with pytest.raises(rk.RetentionError) as e:
            rk.keep_records(record_kind=kind)
        assert fact in e.value.message, kind


def test_unknown_kind_lists_the_closed_enum():
    with pytest.raises(rk.RetentionError) as e:
        rk.keep_records(record_kind="shoebox")
    assert "vat_invoice" in e.value.expected
    assert e.value.field == "record_kind"


def test_anchor_mismatch_named():
    with pytest.raises(rk.RetentionError) as e:
        rk.keep_records(record_kind="paye", tax_year_end_on="2026-04-05",
                        issued_on="2026-01-01")
    assert e.value.field == "issued_on"
    assert "not an anchor" in e.value.message


def test_conventions_and_sources_travel():
    out = rk.keep_records(**VAT_ISSUED)
    assert "retain_until + 1 day" in out["conventions"]["destroy"]
    assert "2024-02-29 + 3 years -> 2027-02-28" in \
        out["conventions"]["anniversary"]
    assert "rejoué verbatim 2026-11-24" in out["sources"]["s388"]["stamp"]
    assert "Updated: 23 November 2026" in out["sources"]["ch15400"]["stamp"]


def test_module_determinism_two_calls():
    a = rk.keep_records(record_kind="company_tax_records",
                        financial_year_end_on="2023-12-31", entity="private",
                        made_on="2023-11-10", as_of="2026-11-24")
    b = rk.keep_records(record_kind="company_tax_records",
                        financial_year_end_on="2023-12-31", entity="private",
                        made_on="2023-11-10", as_of="2026-11-24")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_jurisdiction_veto_closed_list():
    # classe b98 portée à l'outil qui se nomme (b100) : une requête
    # qui nomme une AUTRE juridiction ne doit jamais promettre le
    # UK-only ; le token UK (HMRC / limited company / Reino Unido)
    # reste la porte d'entrée honnête.
    from fastapi.testclient import TestClient

    import main
    cli = TestClient(main.app)
    for q in ("combien de temps garder mes factures en France",
              "as notas fiscais brasileiras quanto tempo guardar",
              "how long must I keep invoices in France"):
        tops = [x["tool"] for x in
                cli.get("/route", params={"q": q}).json()["tools"]]
        assert "money_keep_records_uk" not in tops, q
    for q in ("puis-je jeter mes factures HMRC de 2020",
              "when can I destroy my limited company accounting records",
              "por quanto tempo guardar documentos da HMRC"):
        tops = [x["tool"] for x in
                cli.get("/route", params={"q": q}).json()["tools"]]
        assert "money_keep_records_uk" in tops, q


def test_route_and_surfaces():
    from fastapi.testclient import TestClient

    import main
    cli = TestClient(main.app)
    r = cli.post("/api/v1/money/keep-records-uk",
                 json={"record_kind": "self_assessment",
                       "tax_year_end_on": "2023-04-05"})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["retain_until"] == "2029-01-31"
    assert b["safe_destroy_on"] == "2029-02-01"
    r2 = cli.post("/api/v1/money/keep-records-uk",
                  json={"record_kind": "self_assessment",
                        "tax_year_end_on": "2023-04-05"})
    assert r2.content == r.content  # même requête, mêmes octets
    bad = cli.post("/api/v1/money/keep-records-uk",
                   json={"record_kind": "paye",
                         "tax_year_end_on": "2026-04-06"})
    assert bad.status_code == 400
    err = bad.json()["errors"][0]
    assert err["field"] == "tax_year_end_on"
    assert "ITA 2007 s.4(3)" in err["message"]
