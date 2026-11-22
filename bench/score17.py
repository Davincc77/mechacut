# score17 — lit results_v17 + les cellules nues de v16 (bras C de
# référence, mêmes problèmes/mêmes graines — pas re-joués) et rend la
# facture : succès, tokens totaux, tokens PAR JUSTE (∞ si 0 juste),
# médiane de secondes. Puis statue sur P1-P4, pré-enregistrés dans
# run17.py avant la première cellule.
import json
import collections
import statistics as st

V17 = [json.loads(l) for l in open(
    "bench/results_v17_tokens.jsonl")]
V16 = [json.loads(l) for l in open(
    "bench/results_v16_calibration.jsonl")]
CHAINE = {"mix", "partage"}

print("cellules v17:", len(V17), "(attendu 80)")


def arm_stats(model, arm, rows=None, fam=None):
    rows = rows if rows is not None else V17
    rs = [r for r in rows if r["model"] == model and r["arm"] == arm
          and (fam is None or r["family"] in fam)]
    ok = sum(1 for r in rs if r["ok"])
    tok = sum(r["tokens"] for r in rs)
    secs = [r["secs"] for r in rs]
    tpw = tok / ok if ok else float("inf")
    return ok, len(rs), tok, tpw, (st.median(secs) if secs else 0)


print("\n%-4s %-8s %6s %8s %10s %8s" %
      ("mod", "bras", "succès", "tokens", "t/juste", "méd.s"))
for mk in ("1.5b", "7b", "8b"):
    if mk == "1.5b":
        rs = [r for r in V16 if r["model"] == mk]
        ok = sum(r["ok"] for r in rs)
        tok = sum(r["tokens"] for r in rs)
        print("%-4s %-8s %4d/%2d %8d %10s %8.1f" % (
            mk, "nude@0(ref)", ok, len(rs), tok,
            ("%.0f" % (tok / ok)) if ok else "∞",
            st.median([r["secs"] for r in rs])))
        continue
    for arm in ("retry5", "relay"):
        o, n, t, w, s = arm_stats(mk, arm)
        print("%-4s %-8s %4d/%2d %8d %10s %8.1f" % (
            mk, arm, o, n, t, ("%.0f" % w) if w != float("inf")
            else "∞", s))
    rs = [r for r in V16 if r["model"] == mk]
    o = sum(r["ok"] for r in rs)
    t = sum(r["tokens"] for r in rs)
    print("%-4s %-8s %4d/%2d %8d %10s %8.1f" % (
        mk, "nude@0(ref)", o, len(rs), t,
        ("%.0f" % (t / o)) if o else "∞",
        st.median([r["secs"] for r in rs])))

print("\n—— familles à chaîne seules (mix+partage) ——")
for mk in ("7b", "8b"):
    for arm in ("retry5", "relay"):
        o, n, t, w, s = arm_stats(mk, arm, fam=CHAINE)
        print("%-4s %-6s %2d/%2d  t/juste %s" % (
            mk, arm, o, n, ("%.0f" % w) if w != float("inf") else "∞"))

print("\n—— verdicts pré-enregistrés ——")
for mk in ("7b", "8b"):
    och, nch, _, _, _ = arm_stats(mk, "retry5", fam=CHAINE)
    rch, rn, _, _, _ = arm_stats(mk, "relay", fam=CHAINE)
    p1 = "TIÈDE (retry≥30 % en chaîne!)" if och / max(nch, 1) >= .3 \
        else "P1 ✓ retry ne converge pas"
    p2 = "P2 ✓ relay ≥70 %" if rn and rch / rn >= .7 else \
        "P2 ✗ relay " + str(rch) + "/" + str(rn)
    print("%-4s %s | %s" % (mk, p1, p2))
# P3 : par famille, relay t/juste < retry t/juste (si les deux nonzero)
inv = []
for fam in ("rate", "recette", "distance", "soldes", "mix", "partage"):
    for mk in ("7b", "8b"):
        _, _, _, wR, _ = arm_stats(mk, "retry5", fam={fam})
        _, _, _, wL, _ = arm_stats(mk, "relay", fam={fam})
        if wR != float("inf") and wL != float("inf") and wL >= wR:
            inv.append((mk, fam, round(wL), round(wR)))
print("P3 exceptions (relay plus cher/juste que retry):", inv or "aucune")
tot7 = arm_stats("7b", "relay", fam=CHAINE)
tot8 = arm_stats("8b", "relay", fam=CHAINE)
print("P4 (le gros ne rattrape pas) : relay chaîne 7b %d/%d, 8b %d/%d"
      % (tot7[0], tot7[1], tot8[0], tot8[1]))
