# -*- coding: utf-8 -*-
"""Bundle 79 — check/allowlist : la politique en grammaire fermée.

Golds tracés à la main avant l'impl (ADJACENCES décision 2) :
  alice/refund <= 100.00 : 99.99 ALLOW ; 100.01 DENY over_amount ;
  sans amount DENY missing_amount ; bob DENY no_rule (default_deny) ;
  {alice,* ALLOW} vs {alice,refund DENY} -> DENY (spécificité 2 > 1) ;
  {alice,refund ALLOW} vs {alice,refund DENY} -> AMBIGUOUS (tie) —
  la machine refuse le pile-ou-face de politique : R3 ailleurs.
"""
import pytest
from fastapi.testclient import TestClient

import allowkit
import main

client = TestClient(main.app)

RULES = [{"subject": "alice", "action": "refund", "max_amount": "100.00"}]


def _v(rules, reqs, dd=True):
    return allowkit.allow_check(rules, reqs, dd)["verdicts"]


def test_g1_allow_juste_et_over_deny():
    v = _v(RULES, [{"subject": "alice", "action": "refund",
                    "amount": "99.99"},
                   {"subject": "alice", "action": "refund",
                    "amount": "100.01"}])
    assert v[0]["verdict"] == "ALLOW" and v[0]["matched_rule"] == 0
    assert v[1]["verdict"] == "DENY" and v[1]["reason"] == "over_amount"


def test_g2_missing_amount_is_violation_not_zero():
    v = _v(RULES, [{"subject": "alice", "action": "refund"}])
    assert v[0]["verdict"] == "DENY" and v[0]["reason"] == "missing_amount"


def test_g3_no_rule_never_allows():
    v = _v(RULES, [{"subject": "bob", "action": "refund",
                    "amount": "1"}])
    assert v[0]["verdict"] == "DENY" and v[0]["reason"] == "no_rule"
    v = _v(RULES, [{"subject": "bob", "action": "refund",
                    "amount": "1"}], dd=False)
    assert v[0]["verdict"] == "ALLOW" and v[0]["reason"] == "no_rule"


def test_g4_specificity_wins_over_wildcard():
    rs = [{"subject": "alice", "action": "*", "allow": True},
          {"subject": "alice", "action": "refund", "allow": False}]
    v = _v(rs, [{"subject": "alice", "action": "refund",
                 "amount": "50"}])
    assert v[0]["verdict"] == "DENY" and v[0]["reason"] == "rule_deny"
    assert v[0]["matched_rule"] == 1


def test_g5_tie_is_ambiguous_never_resolved():
    rs = [{"subject": "alice", "action": "refund", "allow": True},
          {"subject": "alice", "action": "refund", "allow": False}]
    v = _v(rs, [{"subject": "alice", "action": "refund",
                 "amount": "10"}])
    assert v[0]["verdict"] == "AMBIGUOUS"
    assert v[0]["matched_rule"] == [0, 1]
    assert "coin" in v[0]["note"]


def test_g6_no_max_means_unlimited():
    v = _v([{"subject": "alice", "action": "x"}],
           [{"subject": "alice", "action": "x",
             "amount": "999999.99"}])
    assert v[0]["verdict"] == "ALLOW"


def test_g7_currency_closed():
    rs = [{"subject": "a", "action": "b", "currencies": ["EUR"]}]
    v = _v(rs, [{"subject": "a", "action": "b"},
                {"subject": "a", "action": "b", "currency": "USD"},
                {"subject": "a", "action": "b", "currency": "EUR"}])
    assert v[0]["reason"] == "missing_currency"
    assert v[1]["reason"] == "currency"
    assert v[2]["verdict"] == "ALLOW"


def test_g8_global_deny_beats_nothing_specific_wins():
    rs = [{"subject": "*", "action": "*", "allow": False},
          {"subject": "alice", "action": "refund", "allow": True}]
    v = _v(rs, [{"subject": "alice", "action": "refund"},
                {"subject": "bob", "action": "refund"}])
    assert v[0]["verdict"] == "ALLOW"
    assert v[1]["verdict"] == "DENY" and v[1]["matched_rule"] == 0


def test_regex_shaped_action_refused_not_evaluated():
    with pytest.raises(allowkit.AllowError) as e:
        allowkit.allow_check([{"subject": "a", "action": "refun.*"}], [])
    assert "grammar is closed" in str(e.value)


def test_grouped_amount_refused_with_pointing():
    with pytest.raises(allowkit.AllowError) as e:
        allowkit.allow_check([{"subject": "a", "action": "b",
                               "max_amount": "1,234.56"}], [])
    assert "num/parse" in str(e.value)


def test_truthy_string_allow_refused():
    with pytest.raises(allowkit.AllowError) as e:
        allowkit.allow_check([{"subject": "a", "action": "b",
                               "allow": "false"}], [])
    assert "truthy" in str(e.value)


def test_unknown_currency_refused():
    with pytest.raises(allowkit.AllowError) as e:
        allowkit.allow_check([{"subject": "a", "action": "b",
                               "currencies": ["XX"]}], [])
    assert "unknown ISO code" in str(e.value)


def test_ceiling_200_named():
    with pytest.raises(allowkit.AllowError) as e:
        allowkit.allow_check([{"subject": "a", "action": "b"}] * 201, [])
    assert "/batch" in str(e.value)


def test_route_and_prose():
    r = client.post("/api/v1/check/allowlist", json={
        "rules": RULES,
        "requests": [{"subject": "alice", "action": "refund",
                      "amount": "99.99", "id": "q1"}]})
    assert r.status_code == 200
    b = r.json()
    assert b["verdicts"][0]["verdict"] == "ALLOW"
    assert b["verdicts"][0]["id"] == "q1"
    assert b["counts"] == {"allowed": 1, "denied": 0, "ambiguous": 0}
    assert b["sha256"]
    names = [t["name"] for t in main.MCP_TOOLS]
    assert "check_allowlist" in names
    src = open("Dockerfile").read()
    assert "allowkit.py" in src
