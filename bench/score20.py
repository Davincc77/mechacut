# score20 — rend le verdict de P1-P5 (gelées dans run20.py avant la
# cellule 1) et la facture par bras. Lit le brut + le dictionnaire
# généré : P1 reclasse les échecs de S en « à côté » (valeur = autre
# quantité nommée de la chaîne), ce que v17 avait vu à l'œil nu.
import json
import sys

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
from gen16 import problems

Q = {t["i"]: t for t in problems()}
V = [json.loads(l) for l in open(
    "/Users/vincenzocirilli/Downloads/mechacut/bench/"
    "results_v20_target_lock.jsonl")]
print("cellules:", len(V), "(attendu 120)")


def stats(model, arm):
    rs = [r for r in V if r["model"] == model and r["arm"] == arm]
    ok = sum(1 for r in rs if r["ok"])
    tok = sum(r["tokens"] for r in rs)
    return ok, len(rs), tok


print("\n%-5s %-3s %8s %9s %11s" %
      ("mod", "arm", "succès", "tokens", "t/juste"))
res = {}
for mk in ("8b", "7b", "1.5b"):
    for arm in ("S", "L"):
        o, n, t = stats(mk, arm)
        res[(mk, arm)] = (o, n, t)
        print("%-5s %-3s %5d/%-3d %9d %11s" %
              (mk, arm, o, n, t,
               ("%.0f" % (t / o)) if o else "∞"))


def a_cote(r):
    """Le got égale une AUTRE quantité nommée que la cible."""
    t = Q[r["i"]]
    if r["got"] is None:
        return False
    return any(abs(float(v) - r["got"]) < 0.005 and k != t["cible"]
               for k, v in t["qte"].items())


print("\n—— classes d'échec en S ——")
for mk in ("8b", "7b", "1.5b"):
    rs = [r for r in V if r["model"] == mk and r["arm"] == "S"
          and not r["ok"]]
    ac = sum(1 for r in rs if a_cote(r))
    print("%-5s %2d échecs dont %2d « à côté » (valeur = autre "
          "quantité nommée)" % (mk, len(rs), ac))

print("\n—— refus finaux en L ——")
for mk in ("8b", "7b", "1.5b"):
    rs = [r for r in V if r["model"] == mk and r["arm"] == "L"
          and not r["ok"]]
    by = {}
    for r in rs:
        by[r["err"]] = by.get(r["err"], 0) + 1
    print("%-5s %s" % (mk, sorted(by.items(), key=lambda kv: -kv[1])))

print("\n—— verdicts gelés ——")
o8s, _, _ = res[("8b", "S")]
o8l, _, _ = res[("8b", "L")]
o7s, _, _ = res[("7b", "S")]
o7l, _, _ = res[("7b", "L")]
o15l, _, _ = res[("1.5b", "L")]
rs8 = [r for r in V if r["model"] == "8b" and r["arm"] == "S"
       and not r["ok"]]
ac8 = sum(1 for r in rs8 if a_cote(r))
print("P1 classe   :", "✓" if ac8 >= 4 else "✗",
      "%d/10 échecs 8b en S sont « à côté » (seuil ≥4)" % ac8)
print("P2 convertit:", "✓" if o8l >= o8s + 3 else "✗",
      "8b %d → %d (seuil +%d)" % (o8s, o8l, o8l - o8s))
print("P3 non-dégât:", "✓" if o7l >= o7s - 1 else "✗",
      "7b S=%d L=%d (seuil L ≥ S−1)" % (o7s, o7l))
print("P4 le mur   :", "✓" if o15l <= 11 else "✗",
      "1.5b L=%d/20 (seuil ≤11)" % o15l)
for mk in ("8b", "7b", "1.5b"):
    o_s, _, t_s = res[(mk, "S")]
    o_l, _, t_l = res[(mk, "L")]
    if o_s and o_l:
        ratio = (t_l / o_l) / (t_s / o_s)
        print("P5 coût %-4s: %s t/juste L/S = %.2f (seuil ≤1,5)" %
              (mk, "✓" if ratio <= 1.5 else "✗", ratio))
    else:
        print("P5 coût %-4s: impossible (S ou L à 0 juste)" % mk)
