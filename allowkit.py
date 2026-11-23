"""allowkit — check/allowlist : qui a le droit de faire quoi, jusqu'à
combien (ADJACENCES décision 2). La douleur « actions involontaires »
ne se traite pas par un LLM qui juge — elle se traite par une grammaire
fermée qui refuse.

Règles écrites AVANT l'impl, golds dans tests/test_bundle77.py :
- subject / action = chaînes exactes ou '*' littéral. Pas de regex :
  "^refun.*" est un refus nommé, pas une feature.
- La règle la plus SPÉCIFIQUE gagne. Spécificité = nombre de champs
  concrets (subject != '*', action != '*'), 0, 1 ou 2.
- Égalité de spécificité avec decisions contraires = AMBIGUOUS et
  CESS. Le produit ne résout pas un conflit de politique par l'ordre
  des lignes — c'est la règle R3 de l'annuaire, la même loi : une
  égalité n'est pas un tirage au sort, c'est une question pour
  l'humain.
- Aucune règle applicable -> default_deny (défaut TRUE). Le silence
  n'autorise jamais ; un allowlist dont rien ne sort est une
  fenêtre, pas un garde-fou.
- max_amount : décimaux exacts, comparés en Decimal ; un amount
  manquant quand la règle exige un plafond est une violation nommée
  (missing_amount), pas un 0 implicite.
- currencies : table ISO fermée (les mêmes codes que money),
  manquante quand la règle en exige une = missing_currency.
"""

from decimal import Decimal

from money import ISO_DECIMALS
from numfmt import _dec


class AllowError(Exception):
    pass


def _d(s, field):
    try:
        return _dec(s)
    except Exception:
        raise AllowError("%s must be a plain decimal string; grouped "
                         "or locale forms go through num/parse first "
                         "(got %r)" % (field, s))


def allow_check(rules, requests, default_deny=True):
    if len(rules) > 200:
        raise AllowError("rules has %d entries — the closed ceiling is "
                         "200; larger policies belong in /batch over "
                         "chunks, not in one silent list" % len(rules))
    if len(requests) > 200:
        raise AllowError("requests has %d entries — ceiling 200, "
                         "same reason as rules" % len(requests))
    compiled = []
    for i, r in enumerate(rules):
        subj = r.get("subject")
        act = r.get("action")
        if not isinstance(subj, str) or not subj:
            raise AllowError("rules[%d].subject missing or empty — "
                             "use \"*\" to mean anyone, silence is "
                             "not a wildcard" % i)
        if not isinstance(act, str) or not act:
            raise AllowError("rules[%d].action missing or empty — use "
                             "\"*\" to mean anything" % i)
        for v, field in ((subj, "subject"), (act, "action")):
            if any(c in v for c in "^$*+?[](){}|\\") and v != "*":
                raise AllowError("rules[%d].%s=%r — the grammar is "
                                 "closed: exact strings or '*' "
                                 "literally; regex-shaped patterns "
                                 "are refused, not evaluated" % (i, field, v))
        allow = r.get("allow", True)
        if not isinstance(allow, bool):
            raise AllowError("rules[%d].allow must be a real boolean, "
                             "not %r — a truthy string is not policy"
                             % (i, allow))
        mx = None
        if r.get("max_amount") is not None:
            mx = _d(r["max_amount"], "rules[%d].max_amount" % i)
        cur = r.get("currencies")
        if cur is not None:
            if not isinstance(cur, list) or not cur:
                raise AllowError("rules[%d].currencies must be a non-"
                                 "empty list of ISO codes" % i)
            for c in cur:
                if c not in ISO_DECIMALS:
                    raise AllowError("rules[%d].currencies: unknown "
                                     "ISO code %r (closed table)" % (i, c))
        spec = (subj != "*") + (act != "*")
        compiled.append((i, subj, act, bool(allow), mx,
                         set(cur) if cur else None, spec))
    out = []
    counts = {"allowed": 0, "denied": 0, "ambiguous": 0}
    for j, q in enumerate(requests):
        subj = q.get("subject")
        act = q.get("action")
        if not isinstance(subj, str) or not isinstance(act, str):
            raise AllowError("requests[%d]: subject and action must be "
                             "strings — '*' in a REQUEST matches nothing, "
                             "it is a rule grammar only" % j)
        amount = None
        if q.get("amount") is not None:
            amount = _d(q["amount"], "requests[%d].amount" % j)
        cur = q.get("currency")
        cands = [c for c in compiled
                 if (c[1] == "*" or c[1] == subj)
                 and (c[2] == "*" or c[2] == act)]
        row = {"index": j, "subject": subj, "action": act}
        if q.get("id") is not None:
            row["id"] = q["id"]
        if not cands:
            verdict = "ALLOW" if not default_deny else "DENY"
            row["verdict"] = verdict
            row["reason"] = "no_rule"
            row["matched_rule"] = None
        else:
            top = max(c[6] for c in cands)
            tied = [c for c in cands if c[6] == top]
            decisions = set(c[3] for c in tied)
            if len(decisions) > 1:
                row["verdict"] = "AMBIGUOUS"
                row["reason"] = "tie"
                row["matched_rule"] = sorted(c[0] for c in tied)
                row["note"] = ("equal specificity, opposite decisions — "
                               "the machine refuses to pick a policy "
                               "coin-flip; ask the human who owns the "
                               "allowlist")
            else:
                row["matched_rule"] = tied[0][0]
                rule = tied[0]
                if not rule[3]:
                    row["verdict"], row["reason"] = "DENY", "rule_deny"
                elif rule[4] is not None and amount is None:
                    row["verdict"], row["reason"] = "DENY", "missing_amount"
                elif rule[4] is not None and amount > rule[4]:
                    row["verdict"], row["reason"] = "DENY", "over_amount"
                elif rule[5] is not None and cur is None:
                    row["verdict"], row["reason"] = "DENY", "missing_currency"
                elif rule[5] is not None and cur not in rule[5]:
                    row["verdict"], row["reason"] = "DENY", "currency"
                else:
                    row["verdict"], row["reason"] = "ALLOW", "allowed"
        counts[{"ALLOW": "allowed", "DENY": "denied",
                "AMBIGUOUS": "ambiguous"}[row["verdict"]]] += 1
        out.append(row)
    return {"verdicts": out, "rules_evaluated": len(compiled),
            "default_deny": default_deny, "counts": counts}
