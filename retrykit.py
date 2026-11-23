"""retrykit — /agent/retry-budget : re-tenter EST-CE RATIONNEL ?

loop/doom-check (b82) juge la TRACE après coup — « es-tu en boucle ? ».
Ce module prononce le verdict ANTE-MORTEM sur UN échec classé —
« re-tenter cet appel, maintenant, avec ce budget : oui, en changeant,
ou non ». Mêmes données, questions distinctes, les deux réponses se
chaînent dans un harness.

Douleurs publiées que cette table interdit :
- dev.to/4sapi : boucle sans plafond, l'appel IDENTIQUE répété
  jusqu'à la session tuée à la main (1 840 retries, ₹18 400 brûlés) ;
  la classification seule fait tomber les appels redondants 27 → 3.
- openlayer : « sending the same malformed call three more times
  burns tokens while guaranteeing the same result » — classer AVANT.
- aident.ai : retryable = transient + safe repetition + observable
  result ; un side effect incertain interdit le re-tentatif
  IDENTIQUE tant que la première tentative n'est pas vérifiée.
- AWS AGENTREL07-BP02 : budgets à DEUX niveaux — par appel ET
  session (tokens) — et escalade quand le budget est épuisé.
- mer.vin : le compte à rebours doit VOYAGER dans la réponse.

Golds tracés main dans tests/test_bundle83.py, avant l'impl.

Lois fermées :
- TAXONOMIE 3 classes × 13 membres (jamais de LM, jamais de chaîne
  libre) : TRANSIENT {rate_limited, network_timeout, connection_reset,
  unavailable, lock_contention} → REPEAT ; FIXABLE {schema_validation,
  invalid_argument, type_mismatch, unknown_field, malformed_payload,
  permission_denied} → MUTATE ; TERMINAL {auth_expired,
  quota_exhausted} → ABORT.
- Échelle de priorité (nommée, déterministe) : classe inconnue =
  refus ; same_hash_count > attempt = refus (un compte de hachés
  identiques est un SOUS-ensemble des tentatives) ; TRANSIENT +
  idempotent=false = ABORT side_effect_unverified ; TERMINAL =
  ABORT terminal_class ; budget (est_cost > budget_tokens) = ABORT
  budget_exhausted ; FIXABLE = MUTATE (le plafond ne s'applique PAS :
  MUTATE n'est pas un re-tentatif) ; same_hash_count >= retry_max =
  ABORT identical_retry_ceiling ; attempt >= retry_max = ABORT
  attempt_ceiling ; sinon REPEAT. SANS preuve de haché fourni,
  same_hash_count vaut 1 : on n'AFFIRME pas des tentatives
  identiques qu'on n'a pas comptées — le plafond d'attempt borne
  quand même la session.
- backoff DÉTERMINISTE : schedule publié 1-2-4 (2^(attempt-1)),
  plafond nommé 64 s, JAMAIS de jitter (la machine est un verdict,
  pas un tirage) ; Retry-After du fournisseur est RESPECTÉ si
  supérieur (backoff_source = provider).
- retry_max bande 2-10 (défaut 3 — le cap publié des frameworks),
  attempt/same_hash_count bande 1-50, budgets 0-10 000 000,
  retry_after 0-3600.
- retryable est une PROPRIÉTÉ DE CLASSE (transient = true), pas une
  copie du verdict : le harness LIT le champ, la machine garde le
  verdict.
"""

MAX_BACKOFF_S = 64

TRANSIENT = {"rate_limited", "network_timeout", "connection_reset",
             "unavailable", "lock_contention"}
FIXABLE = {"schema_validation", "invalid_argument", "type_mismatch",
           "unknown_field", "malformed_payload", "permission_denied"}
TERMINAL = {"auth_expired", "quota_exhausted"}

GUIDANCE = {
    "schema_validation": "repair the payload against the schema, "
                         "then send the corrected call — a schema "
                         "violation fails identically forever",
    "invalid_argument": "fix the argument before the next call — the "
                        "same payload reproduces this failure",
    "type_mismatch": "coerce the field type (see /api/v1/json/coerce), "
                     "then send the corrected call",
    "unknown_field": "align field names with the contract (camelCase "
                     "vs snake_case is a named failure class), then "
                     "send the corrected call",
    "malformed_payload": "repair the bytes (see /api/v1/json/repair), "
                         "then send the corrected call",
    "permission_denied": "request the missing scope or reconnect — a "
                         "permission error does not heal with an "
                         "identical call",
    "auth_expired": "refresh credentials and re-plan — expired auth "
                    "is fatal to this attempt chain",
    "quota_exhausted": "restore budget or escalate — quota does not "
                       "reset between identical calls",
}

SOURCE = ("closed retry taxonomy: transient->REPEAT, fixable->MUTATE, "
          "terminal->ABORT; per-call ceiling AND session budget "
          "checked (AWS AGENTREL07-BP02, aident.ai retry matrix, "
          "dev.to/4sapi, openlayer)")


class RetryBudgetError(Exception):
    pass


def _cls(e):
    return str(e)


def _band(v, lo, hi, what):
    if not isinstance(v, int) or isinstance(v, bool):
        raise RetryBudgetError("%s must be an integer, got %r"
                               % (what, v))
    if not (lo <= v <= hi):
        raise RetryBudgetError("%s must be in %d..%d, got %d"
                               % (what, lo, hi, v))
    return v


def agent_retrybudget(error_class, attempt, payload_hash=None,
                      same_hash_count=None, retry_max=3,
                      budget_tokens=None, est_cost_tokens=None,
                      retry_after_seconds=None, idempotent=None):
    if error_class not in TRANSIENT | FIXABLE | TERMINAL:
        raise RetryBudgetError(
            "error_class %r not in the closed taxonomy (transient: %s; "
            "fixable: %s; terminal: %s)"
            % (error_class, ", ".join(sorted(TRANSIENT)),
               ", ".join(sorted(FIXABLE)), ", ".join(sorted(TERMINAL))))
    _band(attempt, 1, 50, "attempt")
    _band(retry_max, 2, 10, "retry_max")
    same = 1 if same_hash_count is None else same_hash_count
    _band(same, 1, 50, "same_hash_count")
    if same > attempt:
        raise RetryBudgetError(
            "same_hash_count %d exceeds attempt %d — identical calls "
            "are a subset of attempts" % (same, attempt))
    for v, what in ((budget_tokens, "budget_tokens"),
                    (est_cost_tokens, "est_cost_tokens")):
        if v is not None:
            _band(v, 0, 10_000_000, what)
    if retry_after_seconds is not None:
        _band(retry_after_seconds, 0, 3600, "retry_after_seconds")
    if payload_hash is not None:
        if not isinstance(payload_hash, str) or not (
                1 <= len(payload_hash) <= 128):
            raise RetryBudgetError(
                "payload_hash must be a string of 1..128 chars")

    move = ("transient" if error_class in TRANSIENT else
            "fixable" if error_class in FIXABLE else "terminal")
    out = {"verdict": None, "reason": None, "error_class": error_class,
           "move_class": move, "retryable": move == "transient",
           "attempt": attempt, "same_hash_count": same,
           "retry_max": retry_max, "source": SOURCE}

    def abort(reason, guidance):
        out["verdict"], out["reason"], out["guidance"] = \
            "ABORT", reason, guidance

    if move == "transient" and idempotent is False:
        abort("side_effect_unverified",
              "verify the first attempt (idempotency key or stable "
              "reference) BEFORE any second send — an identical call "
              "risks duplicating an irreversible effect")
    elif move == "terminal":
        abort("terminal_class:" + error_class, GUIDANCE[error_class])
    elif (budget_tokens is not None and est_cost_tokens is not None
            and est_cost_tokens > budget_tokens):
        out["verdict"] = "ABORT"
        out["reason"] = ("budget_exhausted (est_cost_tokens %d > "
                         "budget_tokens %d)"
                         % (est_cost_tokens, budget_tokens))
        out["guidance"] = ("session token ceiling reached — stop "
                           "retrying whatever the error class "
                           "(AWS AGENTREL07: budgets at two levels)")
    elif move == "fixable":
        out["verdict"] = "MUTATE"
        out["reason"] = "fixable_class:" + error_class
        out["guidance"] = GUIDANCE[error_class]
        out["identical_retries_wasted"] = same - 1
        out["attempts_remaining"] = max(0, retry_max - attempt)
    elif same >= retry_max:
        abort("identical_retry_ceiling",
              "attempt %d with the same payload hash — the next "
              "IDENTICAL call will not return a different answer; "
              "change the payload or the tool, or escalate"
              % (same + 1))
        out["identical_retries_wasted"] = same - 1
    elif attempt >= retry_max:
        abort("attempt_ceiling",
              "this step has hit the %d-attempt ceiling even with "
              "changed payloads — return an explicit failure so the "
              "model switches strategy" % retry_max)
    else:
        sched = min(2 ** (attempt - 1), MAX_BACKOFF_S)
        if retry_after_seconds is not None and \
                retry_after_seconds > sched:
            backoff, bsource = retry_after_seconds, "provider"
        else:
            backoff, bsource = sched, "schedule"
        out["verdict"] = "REPEAT"
        out["reason"] = "transient_class:" + error_class
        out["backoff_seconds"] = backoff
        out["backoff_source"] = bsource
        out["remaining_identical"] = retry_max - same
        out["attempts_remaining"] = retry_max - attempt
        out["guidance"] = ("re-send the identical call after "
                           "%ds — transient failures may resolve "
                           "without changing the request" % backoff)
    return out
