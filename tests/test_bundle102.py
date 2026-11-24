# -*- coding: utf-8 -*-
"""Bundle 102 — /shop/gift-voucher : la carte cadeau « expirée »,
verdict daté, juridictions NOMMÉES. Golds tracés À LA MAIN sur
l'oracle scratch g102 (arithmétique date pure, écrite AVANT le
module) — sens habituel : le test suit la main, le module suit le
test, et si la machine contredit, on vérifie DEUX FOIS qui a raison.

Golds principaux (oracle g102) :
  A1 JD Sports shape : achat 2025-11-01, papier 2026-11-01,
     as_of 2026-11-24 -> deemed 2030-11-01 (anniversaire exact),
     ILLEGAL_SHORT_EXPIRY, PAPER_DEAD_LAW_ALIVE, days_left 1438
     (2030-11-01 - 2026-11-24 = 365+366+365+365 - 23 = 1438, main),
     papier vole (deemed - printed) = 1461 (2026-11-01->2030-11-01 :
     365(2027)+366(2028)+365(2029)+365(2030)-… main : 1461 — le
     saut bissextile est DANS la fenêtre, 4 ans = 1461).
  A4 borne commencement INCLUSE : achat 2019-12-02 (CCPC : « sold
     before 2 December 2019 do not have to comply » — le 2 est DEDANS),
     papier 2020-12-01, as_of 2026-01-01 -> deemed 2024-12-02,
     DEAD_EVEN_DEEMED, days_since 395, vol 1462 (2020-12-01->2024-12-02
     = 365+365+365+366+1 = 1462, main).
  A5 bissextile : achat 2024-02-29 -> deemed 2029-02-28 (règle
     écrite : quantième inexistant -> DERNIER jour du mois).
  B borne euro : remaining « 1.00 » -> REFUND_RIGHT avec CONFLIT
     NOMMÉ (statute « €1 or more » vs FAQ CCPC « more than €1 »),
     « 0.99 » -> SILENT_BELOW_EUR1 (le trou est la loi, pas un
     arrangements ; zéro date inventée).
"""
import json
import socket
import subprocess

import pytest
import voucherkit as k
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


# ---------------------------------------------------------------- IE : la forme JD Sports
def test_a1_illegal_short_paper_dead_law_alive():
    r = k.gift_voucher("ie", "2025-11-01",
                       printed_expiry_on="2026-11-01", as_of="2026-11-24")
    assert r["jurisdiction"] == "IE"
    assert r["verdict"] == "ILLEGAL_SHORT_EXPIRY"
    assert r["deemed_expiry_on"] == "2030-11-01"
    assert r["legal_expiry_on"] == "2030-11-01"
    assert r["status"] == "PAPER_DEAD_LAW_ALIVE"
    assert r["days_left"] == 1438
    assert r["paper_vs_law"]["days_the_printed_date_stole"] == 1461
    assert r["paper_vs_law"]["printed"] == "2026-11-01"
    assert r["paper_vs_law"]["deemed"] == "2030-11-01"


def test_a1b_same_case_paper_still_alive():
    # as_of AVANT le papier : vivant partout, mais l'illégalité est
    # déjà dite — la clause courte est l'offence, pas la date du jour.
    r = k.gift_voucher("ie", "2025-11-01",
                       printed_expiry_on="2026-11-01", as_of="2025-11-15")
    assert r["verdict"] == "ILLEGAL_SHORT_EXPIRY"
    assert r["status"] == "ALIVE"
    assert r["days_left"] == 1812


def test_a2_compliant_explicit():
    r = k.gift_voucher("IE", "2022-12-20",
                       printed_expiry_on="2028-12-31", as_of="2026-12-25")
    assert r["verdict"] == "COMPLIANT_EXPLICIT"
    assert r["legal_expiry_on"] == "2028-12-31"   # le papier est la loi
    assert r["status"] == "ALIVE"
    assert r["days_left"] == 737


def test_a2b_expiry_day_itself_still_redeems():
    # 66A(1) : « the date AFTER which … ceases » — le jour dit n'est
    # PAS encore le lendemain. Borne jurée, pas une faveur.
    r = k.gift_voucher("ie", "2022-12-20",
                       printed_expiry_on="2027-12-20", as_of="2027-12-20")
    assert r["verdict"] == "COMPLIANT_EXPLICIT"
    assert r["status"] == "ALIVE"
    assert r["days_left"] == 0


def test_a2c_one_day_past_compliant_dead_honest():
    r = k.gift_voucher("ie", "2022-12-20",
                       printed_expiry_on="2027-12-20", as_of="2027-12-21")
    assert r["status"] == "DEAD"
    assert r["days_since"] == 1


def test_a3_pre_commencement():
    r = k.gift_voucher("ie", "2019-12-01",
                       printed_expiry_on="2020-12-01")
    assert r["verdict"] == "PRE_COMMENCEMENT"
    assert "BEFORE" in r["commencement_gate"]["rule"]
    assert "legal_expiry_on" not in r  # l'Act n'atteint pas la date


def test_a4_commencement_boundary_inside_and_dead_even_deemed():
    r = k.gift_voucher("ie", "2019-12-02",
                       printed_expiry_on="2020-12-01", as_of="2026-01-01")
    assert r["verdict"] == "ILLEGAL_SHORT_EXPIRY"
    assert "INSIDE" in r["commencement_gate"]["rule"]
    assert r["deemed_expiry_on"] == "2024-12-02"
    assert r["status"] == "DEAD_EVEN_DEEMED"
    assert r["days_since"] == 395
    assert r["paper_vs_law"]["days_the_printed_date_stole"] == 1462


def test_a5_leap_day_anchor_last_day_rule():
    r = k.gift_voucher("ie", "2024-02-29")
    assert r["verdict"] == "DEEMED_FIVE_YEAR"
    assert r["deemed_expiry_on"] == "2029-02-28"  # 2029 non bissextile
    assert "2029-02-28" in r["computations"]["year_rule"]


def test_a6_silent_contract_deemed_five():
    r = k.gift_voucher("ie", "2023-06-15", as_of="2026-11-24")
    assert r["verdict"] == "DEEMED_FIVE_YEAR"
    assert r["legal_expiry_on"] == "2028-06-15"
    assert r["status"] == "ALIVE"
    assert r["days_left"] == 569
    assert any("66B(2)" in c for c in r["conditions"])


def test_a7_no_expiry_term_is_itself_legal():
    r = k.gift_voucher("ie", "2021-01-04", no_expiry_term=True)
    assert r["verdict"] == "COMPLIANT_NO_EXPIRY"
    assert r["legal_expiry_on"] is None
    assert r["status"] == "ALIVE" if "status" in r else True


def test_no_expiry_and_printed_contradict():
    with pytest.raises(k.VoucherError) as e:
        k.gift_voucher("ie", "2021-01-04", no_expiry_term=True,
                       printed_expiry_on="2026-01-04")
    assert e.value.field == "no_expiry_term"


# ---------------------------------------------------------------- la borne euro
def test_b1_exactly_one_euro_refund_and_conflict_named():
    r = k.gift_voucher("ie", "2023-06-15", remaining_eur="1.00")
    b = r["refund_block"]
    assert b["verdict"] == "REFUND_RIGHT"
    assert b["balance"] == "1.00"
    c = b["conflict"]
    assert "statute_eur1_or_more" in c["positions"]
    assert "ccpc_faq_more_than" in c["positions"]
    assert "€1 or more" in c["positions"]["statute_eur1_or_more"]


def test_b2_below_one_statute_silent():
    r = k.gift_voucher("ie", "2023-06-15", remaining_eur="0.99")
    assert r["refund_block"]["verdict"] == "SILENT_BELOW_EUR1"
    assert "conflict" not in r["refund_block"]


def test_b3_comma_decimal_is_string_money():
    r = k.gift_voucher("ie", "2023-06-15", remaining_eur="12,50")
    assert r["refund_block"]["balance"] == "12.50"


def test_b4_negative_balance_refused():
    with pytest.raises(k.VoucherError) as e:
        k.gift_voucher("ie", "2023-06-15", remaining_eur="-1.00")
    assert e.value.field == "remaining_eur"


# ---------------------------------------------------------------- les 8 exclusions closes
def test_c1_all_eight_exclusion_classes():
    assert len(k.EXCLUDED_CLASSES) == 8
    for cls in sorted(k.EXCLUDED_CLASSES):
        r = k.gift_voucher("ie", "2023-06-15", excluded_class=cls)
        assert r["verdict"] == "EXCLUDED_OUT_OF_SCOPE"
        assert r["excluded_class"] == cls
        assert "no_dates_computed" in r


def test_c2_unknown_exclusion_refused_with_list():
    with pytest.raises(k.VoucherError) as e:
        k.gift_voucher("ie", "2023-06-15", excluded_class="giftcard")
    assert e.value.field == "excluded_class"
    assert "loyalty" in e.value.expected


def test_c3_return_credit_is_the_return_deadline_frontier():
    # l'avoir né d'un RETOUR n'est pas un gift voucher — la frontière
    # avec /shop/return-deadline voyage dans la clause verbatim.
    r = k.gift_voucher("ie", "2023-06-15", excluded_class="return_refund")
    assert "return-deadline" in r["why"]


# ---------------------------------------------------------------- les 4 actes du comptoir
def test_d1_four_clashes_each_against_a_section():
    assert len(k.CLASHES) == 4
    for clash in sorted(k.CLASHES):
        r = k.gift_voucher("ie", "2023-06-15", clash=clash)
        tc = r["term_clash"]
        assert tc["clash"] == clash
        assert "66B" in tc["void_against"]
        assert "66B(9)" in tc["effect"]


def test_d2_unknown_clash_refused():
    with pytest.raises(k.VoucherError) as e:
        k.gift_voucher("ie", "2023-06-15", clash="no_cashback")
    assert e.value.field == "clash"


# ---------------------------------------------------------------- FR : l'absence rejouée
def test_e1_fr_no_statutory_minimum_no_invented_date():
    r = k.gift_voucher("fr", "2024-12-20",
                       printed_expiry_on="2025-12-20", as_of="2026-11-24")
    assert r["verdict"] == "NO_STATUTORY_MINIMUM"
    assert r["status"] == "DEAD_ON_PAPER"
    assert r["days_since"] == 339
    pb = r["prescription_block"]
    assert pb["period_years"] == 5
    assert pb["computable"] is False       # l'ancre est FLOTTANTE
    assert "2227" in pb["correction"]      # le 30 ans corrige ici
    assert "2224" in r["verbatim"]["prescription_cinq_ans"]


def test_e2_fr_without_printed_date():
    r = k.gift_voucher("fr", "2025-01-10")
    assert r["verdict"] == "NO_STATUTORY_MINIMUM"
    assert "NO_PRINTED_DATE" in r["date_status"]


def test_e3_fr_refuses_ie_only_fields():
    with pytest.raises(k.VoucherError) as e:
        k.gift_voucher("fr", "2025-01-10", clash="single_use_required")
    assert e.value.field == "clash"
    with pytest.raises(k.VoucherError) as e:
        k.gift_voucher("fr", "2025-01-10", excluded_class="loyalty")
    assert e.value.field == "excluded_class"


# ---------------------------------------------------------------- vet de juridiction
@pytest.mark.parametrize("j", ["uk", "gb", "united kingdom", "brasil",
                               "brazil", "usa", "united states"])
def test_f1_untabled_jurisdictions_refused_by_name(j):
    with pytest.raises(k.VoucherError) as e:
        k.gift_voucher(j, "2025-01-10")
    assert e.value.field == "jurisdiction"
    assert e.value.expected == "ie or fr"
    assert "repl" in e.value.message.lower()


def test_f2_unknown_jurisdiction_lists_the_table():
    with pytest.raises(k.VoucherError) as e:
        k.gift_voucher("espagne", "2025-01-10")
    assert "ireland" in e.value.expected
    assert "france" in e.value.expected


def test_f3_alias_casing_accents():
    assert k.gift_voucher(" ÉIRE ", "2025-01-10")["jurisdiction"] == "IE"
    assert k.gift_voucher("France", "2025-01-10")["jurisdiction"] == "FR"


# ---------------------------------------------------------------- incohérences data
def test_g1_expiry_before_purchase_refused():
    with pytest.raises(k.VoucherError) as e:
        k.gift_voucher("ie", "2025-01-01", printed_expiry_on="2024-01-01")
    assert e.value.field == "printed_expiry_on"


def test_g2_as_of_before_purchase_refused():
    with pytest.raises(k.VoucherError) as e:
        k.gift_voucher("ie", "2025-06-01", as_of="2024-06-01")
    assert e.value.field == "as_of"


def test_g3_bad_date_field_named():
    with pytest.raises(k.VoucherError) as e:
        k.gift_voucher("ie", "2025-13-01")
    assert e.value.field == "purchased_on"


# ---------------------------------------------------------------- HTTP / contrat
def test_h1_endpoint_200_sha():
    resp = client.post("/api/v1/shop/gift-voucher", json={
        "jurisdiction": "ie", "purchased_on": "2025-11-01",
        "printed_expiry_on": "2026-11-01", "as_of": "2026-11-24"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "PAPER_DEAD_LAW_ALIVE"
    assert body["sha256"]


def test_h2_endpoint_refusal_is_a_repair_prompt():
    resp = client.post("/api/v1/shop/gift-voucher", json={
        "jurisdiction": "uk", "purchased_on": "2025-01-01"})
    assert resp.status_code == 400
    err = resp.json()["errors"][0]
    assert err["field"] == "jurisdiction"
    assert err["expected"] == "ie or fr"


def test_h3_endpoint_extra_field_refused():
    resp = client.post("/api/v1/shop/gift-voucher", json={
        "jurisdiction": "ie", "purchased_on": "2025-01-01",
        "country": "IE"})
    assert resp.status_code == 400


def test_h4_same_input_same_bytes():
    a = client.post("/api/v1/shop/gift-voucher", json={
        "jurisdiction": "ie", "purchased_on": "2023-06-15",
        "remaining_eur": "1.00"}).json()["sha256"]
    b = client.post("/api/v1/shop/gift-voucher", json={
        "jurisdiction": "ie", "purchased_on": "2023-06-15",
        "remaining_eur": "1.00"}).json()["sha256"]
    assert a == b


def test_h5_never_fetches_never_subprocess(monkeypatch):
    def boom(*a, **kw):
        raise AssertionError("network or subprocess from voucherkit")
    monkeypatch.setattr(socket.socket, "connect", boom)
    monkeypatch.setattr(subprocess, "Popen", boom)
    r = k.gift_voucher("ie", "2025-01-01", remaining_eur="1.00",
                       as_of="2026-11-24")
    assert r["jurisdiction"] == "IE"


# ---------------------------------------------------------------- routeur (sa douleur propre)
@pytest.mark.parametrize("q, want", [
    ("the gift voucher I got for last Christmas expired, shop says too "
     "late, bought in Dublin 2024", "shop_gift_voucher"),
    ("gift card expired but I heard five years is the law",
     "shop_gift_voucher"),
    ("ma carte cadeau a expiré, le magasin dit que c'est mort — j'ai "
     "acheté à Dublin", "shop_gift_voucher"),
    ("bon cadeau périmé en France, y a-t-il une durée légale ?",
     "shop_gift_voucher"),
    ("meu cartão-presente irlandês venceu, a loja diz que acabou",
     "shop_gift_voucher"),
    ("vale-presente da JD Sports expirou, comprei em Dublin",
     "shop_gift_voucher"),
])
def test_i1_route_three_languages(q, want):
    r = client.get("/route", params={"q": q}).json()["tools"]
    assert r[0]["tool"] == want, [x["tool"] for x in r[:3]]


@pytest.mark.parametrize("q", [
    "meu vale-presente brasileiro expirou",          # BR hors table
    "gift voucher expired in London",  # UK nommé par sa capitale
    "mon voucher a expiré à Londres",                # même forme FR
    "mon bon d'achat a expiré en Irlande du Nord",   # UK encore (nord)
    "tell me a joke about expired gift vouchers",    # forme b98
    "raconte-moi une blague sur les cartes cadeaux",  # b98 x2
])
def test_i2_router_vetoes_hold(q):
    r = client.get("/route", params={"q": q}).json()["tools"]
    assert "shop_gift_voucher" not in [x["tool"] for x in r]


@pytest.mark.parametrize("q, want", [
    ("can I still return the Christmas gift I bought at fnac",
     "shop_return_deadline"),
    ("the price dropped after I paid, they offer a gift card refund, "
     "who owes me", "shop_pricedrop_refund"),
    ("my points are worth more as a gift card balance or cash back",
     "money_points"),
    ("combien de tokens coûte la liste d'outils de ce serveur mcp "
     "à chaque tour", "agent_contexttax"),
    ("garantie légale du cadeau défectueux livré à Noël",
     "shop_legal_guarantee"),
])
def test_i3_sibling_needles_untouched(q, want):
    r = client.get("/route", params={"q": q}).json()["tools"]
    assert r[0]["tool"] == want, [x["tool"] for x in r[:3]]
