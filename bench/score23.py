# -*- coding: utf-8 -*-
# score23 — verdicts P1-P5 (gelées dans run23.py avant la cellule 1).
# La question d'un seul banc : la famille Qwen était-elle le sujet,
# ou le symptôme ?
import json
import sys

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
from gen16 import problems

Q = {t["i"]: t for t in problems()}
ROWS = [json.loads(l) for l in open(
    "/Users/vincenzocirilli/Downloads/mechacut/bench/"
    "results_v23_lfm3.jsonl")]
CHAINE = {"mix", "partage"}
print("cellules:", len(ROWS), "(attendu 60)")


def rows_of(arm, chain=False):
    return [r for r in ROWS if r["arm"] == arm and
            (not chain or r["family"] in CHAINE)]


def wins(arm, chain=False):
    rs = rows_of(arm, chain)
    return sum(1 for r in rs if r["ok"]), len(rs)


for arm in ("N", "S", "L"):
    o, n = wins(arm)
    oc, nc = wins(arm, chain=True)
    tok = sum(r["tok_in"] + r["tok_out"] for r in rows_of(arm))
    usd = sum(r["usd"] for r in rows_of(arm))
    print("%s : %2d/%2d total | %d/%d chaîne | tok=%d $%.4f" %
          (arm, o, n, oc, nc, tok, usd))


def a_cote(r):
    t = Q[r["i"]]
    if r["got"] is None:
        return False
    return any(abs(float(v) - r["got"]) < 0.005 and k != t["cible"]
               for k, v in t["qte"].items())


s_fail = [r for r in rows_of("S") if not r["ok"]]
s_acote = [r for r in s_fail if a_cote(r)]
conv = sum(1 for r in s_acote
           if any(x["i"] == r["i"] and x["ok"] for x in rows_of("L")))
print("S échecs: %d dont %d « à côté » ; L convertit %d/%d" %
      (len(s_fail), len(s_acote), conv, len(s_acote)))
prot = sum(1 for r in rows_of("L")
           if (r["err"] or "") in ("protocol_giveup", "shape"))
print("L ruptures de protocole:", prot)
usd_total = sum(r["usd"] for r in ROWS)
oL, _ = wins("L")
print("facture totale: $%.4f — $/juste L: %s" %
      (usd_total, ("%.4f" % (usd_total / oL)) if oL else "∞"))

print("\n—— verdicts gelés ——")
nN, _ = wins("N", chain=True)
sN, _ = wins("N", chain=False)
sS, _ = wins("S", chain=False)
nS, _ = wins("S", chain=True)
lS, _ = wins("L", chain=False)
print("P1 mur hors-famille :", "✓" if nN <= 3 else ("✗ RÉÉCRITURE : "
      "N=%d/7 en chaîne — le plafond n'était pas qu'un Qwen" % nN))
print("P2 délégation       :", "✓" if nS >= nN + 2 else
      "✗ S=%d vs N=%d en chaîne (attendu ≥N+2)" % (nS, nN))
p3 = lS >= sS and (len(s_acote) == 0 or conv >= -(-2 * len(s_acote) // 3))
print("P3 verrou           :", "✓" if p3 else
      "✗ L=%d vs S=%d ; à côté %d convertis %d" %
      (lS, sS, len(s_acote), conv))
print("P4 gabarit          :", "✓" if prot <= 1 else
      "✗ %d ruptures (attendu ≤1)" % prot)
print("P5 facture          :", "✓" if usd_total <= 0.50 else
      "✗ $%.4f" % usd_total)
