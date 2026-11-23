# -*- coding: utf-8 -*-
"""Bundle 83 — /agent/retry-budget : le verdict ante-mortem du retry.

Golds tracés MAIN avant l'impl (mêmes cas que la doc du module) :
  rate_limited a=1                 -> REPEAT backoff 1 (schedule 1-2-4)
  rate_limited a=2 same=2          -> REPEAT backoff 2
  network_timeout a=3 same=3       -> ABORT identical_retry_ceiling
  rate_limited a=3 same=1          -> ABORT attempt_ceiling
  rate_limited a=1 b=1000 est=40k  -> ABORT budget_exhausted
  rate_limited a=1 ra=30           -> REPEAT backoff 30 source provider
  rate_limited a=8 mx=10 same=1    -> REPEAT backoff 64 (plafond nommé)
  rate_limited a=1 idemp=False     -> ABORT side_effect_unverified
  schema_validation                -> MUTATE wasted 0 (jamais plafonné)
  invalid_argument a=4 same=4      -> MUTATE wasted 3 (le 1840-retry
                                      drame rendu : 3 appels IDENTIQUES
                                      déjà brûlés, et le verdict dit
                                      MUTATE, pas ABORT — réparer, pas
                                      abandonner)
  quota_exhausted / auth_expired   -> ABORT terminal_class
  same=5 attempt=2                 -> 400 (sous-ensemble)
  classe inconnue                  -> 400 (table fermée citée)
"""
import main
import pytest
import retrykit
from fastapi.testclient import TestClient

client = TestClient(main.app)


def _kb(**kw):
    r = client.post("/api/v1/agent/retry-budget", json=kw)
    return r.status_code, r.json()


def test_repeat_schedule_1_2_4():
    b = retrykit.agent_retrybudget("rate_limited", 1)
    assert b["verdict"] == "REPEAT"
    assert b["backoff_seconds"] == 1 and b["backoff_source"] == "schedule"
    assert b["remaining_identical"] == 2 and b["attempts_remaining"] == 2
    assert b["retryable"] is True
    b2 = retrykit.agent_retrybudget("rate_limited", 2, same_hash_count=2)
    assert b2["backoff_seconds"] == 2


def test_identical_ceiling_abort():
    b = retrykit.agent_retrybudget("network_timeout", 3,
                                   same_hash_count=3)
    assert b["verdict"] == "ABORT"
    assert b["reason"] == "identical_retry_ceiling"
    assert b["identical_retries_wasted"] == 2
    # retryable RESTE vrai : propriété de classe, pas copie du verdict
    assert b["retryable"] is True


def test_attempt_ceiling_when_payload_changed():
    b = retrykit.agent_retrybudget("rate_limited", 3, same_hash_count=1)
    assert b["verdict"] == "ABORT"
    assert b["reason"] == "attempt_ceiling"
    assert "identical_retry_ceiling" != b["reason"]


def test_backoff_capped_at_named_ceiling():
    b = retrykit.agent_retrybudget("network_timeout", 8,
                                   same_hash_count=1, retry_max=10)
    assert b["verdict"] == "REPEAT"
    assert b["backoff_seconds"] == 64


def test_provider_retry_after_respected():
    b = retrykit.agent_retrybudget("rate_limited", 1,
                                   retry_after_seconds=30)
    assert b["backoff_seconds"] == 30
    assert b["backoff_source"] == "provider"
    # un Retry-After PETIT ne écrase pas le schedule :
    b2 = retrykit.agent_retrybudget("rate_limited", 4, retry_max=10,
                                    same_hash_count=1,
                                    retry_after_seconds=2)
    assert b2["backoff_seconds"] == 8 and \
        b2["backoff_source"] == "schedule"


def test_budget_gate_two_levels():
    b = retrykit.agent_retrybudget("rate_limited", 1,
                                   budget_tokens=1000,
                                   est_cost_tokens=40000)
    assert b["verdict"] == "ABORT"
    assert b["reason"].startswith("budget_exhausted")
    # égalité = ça tient (est <= budget) : borne nommée, pas devinée
    ok = retrykit.agent_retrybudget("rate_limited", 1,
                                    budget_tokens=1000,
                                    est_cost_tokens=1000)
    assert ok["verdict"] == "REPEAT"


def test_side_effect_unverified_blocks_repeat():
    b = retrykit.agent_retrybudget("rate_limited", 1, idempotent=False)
    assert b["verdict"] == "ABORT"
    assert b["reason"] == "side_effect_unverified"


def test_fixable_mutate_never_ceilinged():
    b = retrykit.agent_retrybudget("schema_validation", 1)
    assert b["verdict"] == "MUTATE"
    assert b["reason"] == "fixable_class:schema_validation"
    assert b["identical_retries_wasted"] == 0
    assert b["retryable"] is False
    # le plafond de re-tentatives IDENTIQUES ne s'applique pas à
    # MUTATE — le drame 1840 retries : 4 essais dont 4 hachés
    # identiques d'un schéma cassé = réparer, pas abandonner
    d = retrykit.agent_retrybudget("invalid_argument", 4,
                                   same_hash_count=4)
    assert d["verdict"] == "MUTATE"
    assert d["identical_retries_wasted"] == 3


def test_terminal_classes_abort():
    for cls in ("quota_exhausted", "auth_expired"):
        b = retrykit.agent_retrybudget(cls, 1)
        assert b["verdict"] == "ABORT"
        assert b["reason"] == "terminal_class:" + cls
    # terminal passe AVANT les plafonds : auth expirée tentative 5
    b = retrykit.agent_retrybudget("auth_expired", 5, same_hash_count=2)
    assert b["reason"] == "terminal_class:auth_expired"


def test_all_transient_members_repeat():
    for cls in sorted(retrykit.TRANSIENT):
        b = retrykit.agent_retrybudget(cls, 1)
        assert b["verdict"] == "REPEAT", cls


def test_all_fixable_members_mutate():
    for cls in sorted(retrykit.FIXABLE):
        b = retrykit.agent_retrybudget(cls, 1)
        assert b["verdict"] == "MUTATE", cls
        assert b["guidance"]


def test_closed_set_rejects_unknown_class():
    with pytest.raises(retrykit.RetryBudgetError) as e:
        retrykit.agent_retrybudget("quantum_collapse", 1)
    msg = str(e.value)
    assert "quantum_collapse" in msg
    for member in ("rate_limited", "schema_validation",
                   "quota_exhausted"):
        assert member in msg


def test_same_count_subset_of_attempts():
    with pytest.raises(retrykit.RetryBudgetError) as e:
        retrykit.agent_retrybudget("rate_limited", 2,
                                   same_hash_count=5)
    assert "subset of attempts" in str(e.value)


def test_bands_named():
    with pytest.raises(retrykit.RetryBudgetError):
        retrykit.agent_retrybudget("rate_limited", 1, retry_max=1)
    with pytest.raises(retrykit.RetryBudgetError):
        retrykit.agent_retrybudget("rate_limited", 51)
    with pytest.raises(retrykit.RetryBudgetError):
        retrykit.agent_retrybudget("rate_limited", 1,
                                   retry_after_seconds=3601)
    with pytest.raises(retrykit.RetryBudgetError):
        retrykit.agent_retrybudget(
            "rate_limited", 1, payload_hash="x" * 129)


def test_endpoint_shape_and_errors():
    s, b = _kb(error_class="rate_limited", attempt=1)
    assert s == 200 and b["verdict"] == "REPEAT" and b["sha256"]
    s, b = _kb(error_class="nope", attempt=1)
    assert s == 400
    assert b["errors"][0]["field"] == "error_class"
    s, b = _kb(error_class="rate_limited")
    assert s == 400  # attempt requis : le 400 NOMME le champ manquant
    assert b["errors"][0]["field"] == "body.attempt"
    s, b = _kb(error_class="rate_limited", attempt=1, bogus=1)
    assert s == 400  # extra forbid


def test_mcp_and_manifest_present():
    s, b = _kb(error_class="schema_validation", attempt=2,
               same_hash_count=2)
    assert s == 200 and b["verdict"] == "MUTATE"
    m = client.get("/agent/manifest")
    assert m.status_code == 200
    names = [x for x in m.text.split("\n") if "retry-budget" in x]
