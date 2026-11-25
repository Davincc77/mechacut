# -*- coding: utf-8 -*-
"""bundle115 — /money/settle : QUI PAYE QUI. Le graphe d'avances se
nettoie au cent, la remise est un ARGUMENT plafonné et Nommé, et les
DEUX lectures du fil r/askmath 1ugli3y (628.33 pour A, 458.33 pour B)
sont rendues CHIFFRÉES avec l'écart entre elles.

Attendus CALCULÉS À LA MAIN (parts du fil : 1375+0+865=2240 ; règle des
restes /money/split : A 746.67 B 746.67 C 746.66 ; soldes A +628.33,
B −746.67, C +118.34 ; remise de C plafonnée à sa propre créance nette
118.34 — la règle du commentateur ; itemized : centime orphelin de
chaque reçu -> A 458.34/288.34, d'où B->A 458.33, C->A 458.33,
A->C 288.34, B->C 288.33) puis croisés contre un ORACLE INDÉPENDANT
(énumération exhaustive de partitions, ecriture différente du DP du
module) pour le compte minimal de virements — JAMAIS recopiés du
module (rituel du playbook).
"""
import itertools
import json
from decimal import Decimal

import main
import settlementkit as sk
from fastapi.testclient import TestClient

client = TestClient(main.app)

ADV = [{"who": "A", "paid": "1375.00"},
       {"who": "B", "paid": "0.00"},
       {"who": "C", "paid": "865.00"}]
NAMES = ["A", "B", "C"]


def oracle_min_transfers(bal):
    """Indépendant : énumère TOUTES les partitions en sous-ensembles à
    somme nulle (récursion première-élément, aucune DP masquée)."""
    nz = [n for n, b in bal.items() if b]

    def best(rem):
        if not rem:
            return 0
        out = -1
        head = rem[0]
        for r in range(1, len(rem) + 1):
            for combo in itertools.combinations(rem[1:], r - 1):
                grp = (head,) + combo
                if sum(bal[x] for x in grp) == 0:
                    rest = [x for x in rem if x not in grp]
                    v = 1 + best(rest)
                    if v > out:
                        out = v
        return out
    return len(nz) - best(nz)


def replay_ok(res):
    """les virements reproduisent-ils les soldes ? (oracle de test)"""
    acc = {}
    for t in res["transfers"]:
        c = int(Decimal(t["amount"]).scaleb(2))
        acc[t["from"]] = acc.get(t["from"], 0) - c
        acc[t["to"]] = acc.get(t["to"], 0) + c
    for b in res["balances"]:
        sign = -1 if b["position"].startswith("owed") else 1
        val = 0 if b["position"] == "settled" else \
            int(Decimal(b["position"].split()[-1]).scaleb(2))
        if acc.get(b["who"], 0) != sign * val:
            return False
    return True


# ------------------------------------------------ the thread itself
def test_net_with_forgiveness_pays_a_628_33():
    r = sk.money_settle(ADV, NAMES, waivers=[{"from": "C", "to": "B"}],
                        mode="net")
    assert r["transfers"] == [{"from": "B", "to": "A",
                               "amount": "628.33"}]
    assert r["transfer_count"] == 1 and r["minimal"] is True
    assert r["balances"] == [
        {"who": "A", "position": "due 628.33"},
        {"who": "B", "position": "owed 628.33"},
        {"who": "C", "position": "settled"}]
    assert replay_ok(r)


def test_forgiveness_is_capped_at_the_forgivers_own_claim():
    r = sk.money_settle(ADV, NAMES, waivers=[{"from": "C", "to": "B"}],
                        mode="net")
    w = r["waivers"][0]
    assert w["applied"] == "118.34"           # la créance nette de C
    assert w["forgiver_claim_after"] == "0.00"
    assert w["debtor_debt_after"] == "628.33"  # le reste voyage vers A
    assert w.get("cap") is None               # full-all = plafonné exact


def test_forgiveness_over_claim_names_the_cap():
    r = sk.money_settle(ADV, NAMES,
                        waivers=[{"from": "C", "to": "B",
                                  "amount": "999.00"}], mode="net")
    w = r["waivers"][0]
    assert w["applied"] == "118.34"
    assert w["cap"] == "WAIVER_CAPPED_AT_OWN_CLAIM"
    assert "GROUP" in w["why"]


def test_forgiveness_by_a_non_creditor_is_refused_not_silent():
    r = sk.money_settle(ADV, NAMES, waivers=[{"from": "B", "to": "C"}],
                        mode="net")
    w = r["waivers"][0]
    assert w["applied"] == "0.00"
    assert w["cap"] == "REFUSED_NOT_A_CREDITOR"
    assert r["transfers"] == [{"from": "B", "to": "A", "amount": "628.33"},
                              {"from": "B", "to": "C",
                               "amount": "118.34"}]


def test_partial_forgiveness_leaves_the_named_remainder():
    r = sk.money_settle(ADV, NAMES,
                        waivers=[{"from": "C", "to": "B",
                                  "amount": "50.00"}], mode="net")
    w = r["waivers"][0]
    assert w["applied"] == "50.00"
    assert w["debtor_debt_after"] == "696.67"   # 746.67 − 50.00
    assert r["transfers"] == [{"from": "B", "to": "A", "amount": "628.33"},
                              {"from": "B", "to": "C", "amount": "68.34"}]


def test_net_without_forgiveness_is_the_splitwise_answer():
    r = sk.money_settle(ADV, NAMES, mode="net")
    assert r["transfers"] == [{"from": "B", "to": "A", "amount": "628.33"},
                              {"from": "B", "to": "C", "amount": "118.34"}]
    assert r["minimal"] is True and replay_ok(r)


def test_itemized_honours_each_receipt_with_orphan_cents():
    r = sk.money_settle(ADV, NAMES, mode="itemized")
    # parts par reçu : 1375/3 -> A 458.34 (centime orphelin par ordre),
    # B 458.33, C 458.33 ; 865/3 -> A 288.34, B 288.33, C 288.33
    assert r["transfers"] == [
        {"from": "B", "to": "A", "amount": "458.33",
         "via": "advance by A"},
        {"from": "C", "to": "A", "amount": "458.33",
         "via": "advance by A"},
        {"from": "A", "to": "C", "amount": "288.34",
         "via": "advance by C"},
        {"from": "B", "to": "C", "amount": "288.33",
         "via": "advance by C"}]
    assert r["positions"] == [
        {"who": "A", "out_of_pocket": "746.68"},
        {"who": "B", "out_of_pocket": "746.66"},
        {"who": "C", "out_of_pocket": "746.66"}]
    assert sum(Decimal(p["out_of_pocket"]) for p in r["positions"]) \
        == Decimal(r["total"]) == Decimal("2240.00")


def test_itemized_forgiveness_kills_the_edge_and_C_bears_it():
    r = sk.money_settle(ADV, NAMES, waivers=[{"from": "C", "to": "B"}],
                        mode="itemized")
    assert {"from": "B", "to": "A", "amount": "458.33",
            "via": "advance by A"} in r["transfers"]
    assert all(t["from"] != "B" or t["to"] != "C" for t in r["transfers"])
    w = r["waivers"][0]
    assert w["applied"] == "288.33" and w["edge_total"] == "288.33"
    pos = {p["who"]: p["out_of_pocket"] for p in r["positions"]}
    assert pos == {"A": "746.68", "B": "458.33", "C": "1034.99"}
    assert sum(Decimal(v) for v in pos.values()) == Decimal("2240.00")


def test_compare_numbers_the_disagreement():
    r = sk.money_settle(ADV, NAMES, waivers=[{"from": "C", "to": "B"}],
                        mode="compare")
    d = r["divergence"]
    assert d["pays_net"] == {"B->A": "628.33"}
    assert d["pays_itemized"] == {"B->A": "458.33", "C->A": "458.33",
                                  "A->C": "288.34"}
    assert d["forgiveness_applied_net"] == {"C->B": "118.34"}
    assert d["forgiveness_applied_itemized"] == {"C->B": "288.33"}
    assert "graph" in d["note"]
    assert r["identity_check"].startswith("both graphs")


def test_cents_close_where_the_thread_did_not():
    # le fil écrit 746.67 × 3 = 2240.01 ≠ 2240 : la règle des restes
    # ferme au cent, dans l'ORDRE des participants
    r = sk.money_settle(ADV, NAMES, mode="net")
    assert [(s["participant"], s["share"]) for s in r["shares"]] == \
        [("A", "746.67"), ("B", "746.67"), ("C", "746.66")]
    assert sum(Decimal(s["share"]) for s in r["shares"]) == \
        Decimal("2240.00")
    assert r["total"] == "2240.00"


# ------------------------------------------------ graphs & modes
def test_two_disjoint_groups_cost_two_transfers_not_n_minus_one():
    adv = [{"who": "A", "paid": "100.00", "split_between": ["A", "B"]},
           {"who": "C", "paid": "100.00", "split_between": ["C", "D"]}]
    r = sk.money_settle(adv, ["A", "B", "C", "D"], mode="net")
    assert r["transfer_count"] == 2
    assert {tuple(sorted((t["from"], t["to"]))) for t in r["transfers"]} \
        == {("A", "B"), ("C", "D")}
    assert r["minimal"] is True and replay_ok(r)


def test_weights_are_the_split_family_grammar():
    adv = [{"who": "A", "paid": "1000.00"}]
    r = sk.money_settle(adv, [{"name": "A", "weight": 1},
                              {"name": "B", "weight": 1},
                              {"name": "C", "weight": 2}], mode="net")
    assert r["share_mode"] == "weights"
    # plus gros d'abord : C (500) avant B (250), égalités par ordre
    assert r["transfers"] == [
        {"from": "C", "to": "A", "amount": "500.00"},
        {"from": "B", "to": "A", "amount": "250.00"}]
    assert replay_ok(r)


def test_itemized_partial_split_never_touches_the_outsider():
    adv = [{"who": "A", "paid": "90.00", "split_between": ["A", "B"]}]
    r = sk.money_settle(adv, ["A", "B", "C"], mode="itemized")
    assert r["transfers"] == [{"from": "B", "to": "A", "amount": "45.00",
                               "via": "advance by A"}]
    pos = {p["who"]: p["out_of_pocket"] for p in r["positions"]}
    assert pos == {"A": "45.00", "B": "45.00", "C": "0.00"}


def test_zero_advance_never_appears_as_a_transfer():
    r = sk.money_settle([{"who": "A", "paid": "30.00"},
                         {"who": "B", "paid": "0.00"}], ["A", "B"])
    assert r["transfers"] == [{"from": "B", "to": "A", "amount": "15.00"}]


# -------------------------------------------------- oracle du minimum
def test_minimal_count_matches_independent_oracle():
    cases = [
        ([("A", "100.00"), ("B", "100.00")],
         ["A", "B", "C", "D", "E"], None),
        ([("A", "1375.00"), ("C", "865.00")], ["A", "B", "C"], None),
        ([("X", "60.00"), ("Y", "60.00"), ("Z", "60.00")],
         ["X", "Y", "Z", "U", "V", "W"], None),
        ([("A", "100.00", ["A", "B"]), ("C", "100.00", ["C", "D"])],
         ["A", "B", "C", "D"], None),
        ([("a", "7.77"), ("b", "13.13"), ("c", "90.90"),
          ("d", "7.07")], ["a", "b", "c", "d", "e", "f"], None),
    ]
    for spec, names, _ in cases:
        adv = []
        for row in spec:
            adv.append({"who": row[0], "paid": row[1],
                        **({"split_between": row[2]} if len(row) > 2
                           else {})})
        r = sk.money_settle(adv, names, mode="net")
        bal = {}
        for b in r["balances"]:
            sign = -1 if b["position"].startswith("owed") else 1
            bal[b["who"]] = 0 if b["position"] == "settled" else \
                sign * int(Decimal(b["position"].split()[-1]).scaleb(2))
        assert sum(bal.values()) == 0
        assert r["transfer_count"] == oracle_min_transfers(bal), names
        assert replay_ok(r)


def test_above_the_bound_greedy_stays_valid_but_admits_it():
    adv = []
    names = []
    for i in range(5):
        names += ["p%d" % i, "q%d" % i]
        adv.append({"who": "p%d" % i, "paid": "%d.00" % (10 + i)})
    # 10 personnes, 5 reçus disjoint de 2 -> minimum 5, greedy borne > 9
    r = sk.money_settle(adv, names, mode="net")
    assert len([n for n in names]) == 10
    assert r["minimal"] is False
    assert "NOT proven" in r["minimum_rule"]
    assert replay_ok(r)
    assert r["transfer_count"] <= len(names) - 1


# --------------------------------------------------- devises fermées
def test_rates_are_arguments_and_travel_on_the_line():
    adv = [{"who": "A", "paid": "100.00", "currency": "EUR"}]
    r = sk.money_settle(adv, ["A", "B"], currency="USD",
                        rates={"EUR": "1.10"})
    a = r["advances"][0]
    assert a["rate_used"] == "1.10"
    assert a["exact_before_rounding"] == "110.0000"
    assert a["settled"] == "110.00"
    assert r["transfers"] == [{"from": "B", "to": "A", "amount": "55.00"}]


def test_mixed_currencies_without_settlement_currency_refuse():
    adv = [{"who": "A", "paid": "10.00", "currency": "EUR"},
           {"who": "B", "paid": "10.00", "currency": "USD"}]
    try:
        sk.money_settle(adv, ["A", "B"])
        assert False
    except sk.MoneyError as e:
        assert "currency=" in str(e)


def test_foreign_without_rates_refuse_by_naming_the_date_rule():
    adv = [{"who": "A", "paid": "10.00", "currency": "EUR"}]
    try:
        sk.money_settle(adv, ["A", "B"], currency="USD")
        assert False
    except sk.MoneyError as e:
        assert "transaction-date" in str(e) and "never fetches" in str(e)


def test_jpy_settlement_refused_by_name():
    try:
        sk.money_settle(ADV, NAMES, currency="JPY")
        assert False
    except sk.MoneyError as e:
        assert "refused by name" in str(e) and "2-decimal" in str(e)


def test_unknown_currency_code_refused():
    try:
        sk.money_settle(ADV, NAMES, currency="XX")
        assert False
    except sk.MoneyError:
        pass


# ------------------------------------------------------ refus structuraux
def test_closed_sets_refuse_invented_words():
    for kw in ({"mode": "netting"}, {"share_mode": "proportional"}):
        try:
            sk.money_settle(ADV, NAMES, **kw)
            assert False
        except sk.MoneyError as e:
            assert "closed set" in str(e) or "equal|weights" in str(e)


def test_duplicate_participant_refused():
    try:
        sk.money_settle(ADV, ["A", "B", "A"])
        assert False
    except sk.MoneyError as e:
        assert "duplicate" in str(e)


def test_negative_advance_refused_as_refund_shape():
    try:
        sk.money_settle([{"who": "A", "paid": "-10.00"}], ["A", "B"])
        assert False
    except sk.MoneyError as e:
        assert "negative" in str(e)


def test_forgiving_a_stranger_refused():
    try:
        sk.money_settle(ADV, NAMES,
                        waivers=[{"from": "Z", "to": "B"}])
        assert False
    except sk.MoneyError as e:
        assert "stranger" in str(e)


def test_self_forgiveness_is_noise():
    try:
        sk.money_settle(ADV, NAMES, waivers=[{"from": "A", "to": "A"}])
        assert False
    except sk.MoneyError as e:
        assert "noise" in str(e)


def test_split_between_inventing_people_refused():
    # GHOST entre dans all_names dès split_between : soit le check des
    # participants NOMME l'omission (tous modes — chemin réel), soit la
    # garde itemized « invent a person » (défense en profondeur). Les
    # deux refusent par nom ; le test épingle le premier, vivant.
    adv = [{"who": "A", "paid": "90.00", "split_between": ["A", "GHOST"]}]
    for m in ("net", "itemized", "compare"):
        try:
            sk.money_settle(adv, ["A", "B"], mode=m)
            assert False
        except sk.MoneyError as e:
            assert "GHOST" in str(e)


def test_participants_omitting_an_advancer_refused():
    try:
        sk.money_settle(ADV, ["A", "B"])
        assert False
    except sk.MoneyError as e:
        assert "omit" in str(e)


def test_paid_must_be_a_decimal_string_shape():
    try:
        sk.money_settle([{"who": "A", "paid": "abc"}], ["A"])
        assert False
    except sk.MoneyError as e:
        assert "STRING" in str(e)


# ------------------------------------------------------------- surface
def test_api_smoke_and_sha():
    r = client.post("/api/v1/money/settle",
                    json={"advances": ADV, "participants": NAMES,
                          "waivers": [{"from": "C", "to": "B"}],
                          "mode": "compare"})
    assert r.status_code == 200
    body = r.json()
    assert body["sha256"]
    assert body["divergence"]["pays_net"] == {"B->A": "628.33"}


def test_api_refuses_bad_mode_with_named_field():
    r = client.post("/api/v1/money/settle",
                    json={"advances": ADV, "mode": "auto"})
    assert r.status_code == 400
    # le pydantic Literal parle AVANT le module et nomme le champ
    # fautif (body.mode — le patron maison de tous les money_* avec
    # enum) ; les erreurs SÉMANTIQUES du module sortent field=settle
    e = r.json()["errors"][0]
    assert e["field"] == "body.mode"
    assert "net" in e["expected"]


def test_api_semantic_error_names_the_settle_field():
    r = client.post("/api/v1/money/settle",
                    json={"advances": [{"who": "A", "paid": "-10.00"},
                                       {"who": "B", "paid": "10.00"}],
                          "participants": ["A", "B"]})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "settle" and "negative" in e["message"]


def test_determinism_same_bytes():
    a = sk.money_settle(ADV, NAMES,
                        waivers=[{"from": "C", "to": "B"}],
                        mode="compare")
    b = sk.money_settle(ADV, NAMES,
                        waivers=[{"from": "C", "to": "B"}],
                        mode="compare")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
