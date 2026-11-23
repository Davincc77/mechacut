"""loopkit — check du doom loop : la répétition aveugle, mesurée.

Douleur documentée par le marché lui-même (ZCode v2,
model-anomaly-fallbacks.md : « mêmes outils, mêmes input en boucle =
signal doom loop ») et mesurée chez nous (V22b : 0/14 programmes
identiques ; V17 : le retry ne converge pas, il répète). Ce module
transforme le signal qualitatif en verdict fermé.

Lois écrites AVANT l'impl (golds dans tests/test_bundle82.py) :
- « identique » se juge en BYTES CANONIQUES de (tool, args) — ordre
  de clés et formes JSON normalisées par le canon de la maison :
  deux dictionnaires écrits dans des ordres différents sont le MÊME
  appel (même loi que eval/compare).
- DOOM   : course de ≥ doom_min (3) appels identiques CONSÉCUTIFS.
- CYCLIC : une période p ∈ 2..6 répétée ≥ cycles_min (2) fois
           entières, détectée à toute position.
- STORM  : un même appel ≥ storm_min (4) fois au total.
- HEALTHY : rien sous les seuils. ratio = distinct/total en Decimal,
           4 décimales, un seul dénominateur.
- Verdict = le plus grave présent (DOOM > CYCLIC > STORM > HEALTHY),
  MAIS tous les signaux sont rapportés.
- ceiling 200, seuils entiers 2..50 nommés, tool manquant = refus.
"""

import hashlib
import json
from decimal import ROUND_HALF_UP

from numfmt import _dec

MAX_CALLS = 200
MAX_PERIOD = 6


class LoopError(Exception):
    pass


def _canon_call(c):
    blob = json.dumps(c.get("args"), sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)
    return c["tool"] + "\x00" + blob


def _sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def _tool_of(k):
    return k.split("\x00", 1)[0]


def _runlengths(keys):
    runs = []
    i = 0
    while i < len(keys):
        j = i
        while j + 1 < len(keys) and keys[j + 1] == keys[i]:
            j += 1
        runs.append((i, j))
        i = j + 1
    return runs


def loop_doom_check(calls, doom_min=3, cycles_min=2, storm_min=4):
    if not calls:
        raise LoopError("calls is empty — a doom check over nothing "
                        "would answer HEALTHY for nothing; refused, "
                        "same law as the empty ledger in aging")
    if len(calls) > MAX_CALLS:
        raise LoopError("calls has %d entries — ceiling %d named; "
                        "longer traces go through /batch over chunks"
                        % (len(calls), MAX_CALLS))
    for name, v in (("doom_min", doom_min), ("cycles_min", cycles_min),
                    ("storm_min", storm_min)):
        if not isinstance(v, int) or isinstance(v, bool) or not 2 <= v <= 50:
            raise LoopError("%s must be an integer 2-50 (got %r) — a "
                            "threshold outside the named band is a "
                            "mood, not a policy" % (name, v))
    keys = []
    for i, c in enumerate(calls):
        if not isinstance(c, dict) or not isinstance(c.get("tool"), str) \
                or not c["tool"]:
            raise LoopError("calls[%d] needs a non-empty 'tool' string — "
                            "an unattributed call cannot be judged for "
                            "loops, only refused" % i)
        keys.append(_canon_call(c))

    total = len(keys)
    distinct = len(set(keys))
    signals = []

    # --- DOOM : courses consécutives
    for start, end in _runlengths(keys):
        n = end - start + 1
        if n >= doom_min:
            k = keys[start]
            signals.append({"kind": "doom", "tool": _tool_of(k),
                            "args_sha256": _sha(k),
                            "positions": list(range(start, end + 1)),
                            "count": n})

    # --- CYCLIC : meilleure course de blocs de période p
    cyc = None
    for p in range(2, MAX_PERIOD + 1):
        i = 0
        while i + p <= total:
            block = tuple(keys[i:i + p])
            reps = 1
            j = i + p
            while j + p <= total and tuple(keys[j:j + p]) == block:
                reps += 1
                j += p
            if reps >= cycles_min:
                cand = (reps, p, i, j)
                # préférence : plus de répétitions, puis période plus
                # courte, puis position plus ancienne — déterministe
                if cyc is None or (reps, -p, i) < (cyc[0], -cyc[1], cyc[2]):
                    cyc = cand
            i = j if reps >= cycles_min else i + p
    if cyc:
        reps, p, i, j = cyc
        signals.append({"kind": "cyclic", "period": p, "repeats": reps,
                        "tools": sorted({_tool_of(k)
                                         for k in keys[i:i + p]}),
                        "positions": list(range(i, j))})

    # --- STORM : compte total dispersé
    counts, where = {}, {}
    for i, k in enumerate(keys):
        counts[k] = counts.get(k, 0) + 1
        where.setdefault(k, []).append(i)
    storms = [(n, where[k][0], k) for k, n in counts.items()
              if n >= storm_min]
    for n, _, k in sorted(storms, key=lambda t: (-t[0], t[1])):
        sig = {"kind": "storm", "tool": _tool_of(k),
               "args_sha256": _sha(k),
               "positions": where[k], "count": n}
        # un appel déjà couvert par une course DOOM n'est pas caché :
        # la liste garde les deux lectures, le verdict garde la loi
        signals.append(sig)

    verdict = ("DOOM" if any(s["kind"] == "doom" for s in signals) else
               "CYCLIC" if cyc else
               "STORM" if storms else "HEALTHY")
    ratio = _dec(distinct) / _dec(total)
    return {"verdict": verdict, "total_calls": total,
            "distinct_calls": distinct,
            "distinct_ratio": format(ratio.quantize(_dec("0.0001"),
                                                    rounding=ROUND_HALF_UP), "f"),
            "thresholds": {"doom_min": doom_min, "cycles_min": cycles_min,
                           "storm_min": storm_min},
            "signals": signals}
