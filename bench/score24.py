# -*- coding: utf-8 -*-
# score24 — statue B1-B5 (gelées dans run24.py) et donne le tableau
# comparisonné à v19 : 21 sorties/30 j au qwen 1,5b ; ici, un modèle
# qui SAIT lire. La question n'est pas la justesse, c'est la
# Répétabilité.
import json
from collections import Counter

ROWS = [json.loads(l) for l in open(
    "/Users/vincenzocirilli/Downloads/mechacut/bench/"
    "results_v24_lfm3_30days.jsonl")]
print("cellules:", len(ROWS), "(attendu 90)")


def arm_rows(a):
    return [r for r in ROWS if r["arm"] == a]


N, R, M = arm_rows("N"), arm_rows("R"), arm_rows("M")

EMPTY_SHA = "01ba4719c80b6fe9"  # sha256 de "\n" — la réponse vide


def silence(rows):
    return sum(1 for r in rows if r.get("err") == "silence"
               or (r["sha"] == EMPTY_SHA and not r["ok"]))


for name, rows in (("N", N), ("R", R), ("M", M)):
    okc = sum(1 for r in rows if r["ok"])
    shas = Counter(r["sha"] for r in rows)
    tok = sum(r["tok_in"] + r["tok_out"] for r in rows)
    usd = sum(r["usd"] for r in rows)
    sil = silence(rows)
    print("%s : %2d/%2d jours justes | sorties distinctes: %d | "
          "SILENCE: %d | tok=%d | $%.4f" %
          (name, okc, len(rows), len(shas), sil, tok, usd))
    if name == "N":
        top = shas.most_common(3)
        okshas = {r["sha"] for r in rows if r["ok"]}
        print("   répartition : " + " · ".join(
            "%s ×%d%s" % (s[:6], c, " (JUSTE)" if s in okshas
                          else "") for s, c in top))
    if name == "R":
        forme = sum(1 for r in rows if r["err"] == "forme")
        faux = sum(1 for r in rows if r["err"] == "FAUX")
        print("   échecs R : %d en FORME refusée, %d FAUX malgré "
              "forme ✓" % (forme, faux))

usd_total = sum(r["usd"] for r in ROWS)
okN = sum(1 for r in N if r["ok"])
okR = sum(1 for r in R if r["ok"])
dN = len({r["sha"] for r in N})
tokN = sum(r["tok_in"] + r["tok_out"] for r in N)
tokR = sum(r["tok_in"] + r["tok_out"] for r in R)
print("\n—— verdicts gelés ——")
b1 = dN >= 2 or not (dN == 1 and okN >= 28)
print("B1 dérive   :", "✓" if dN >= 2 else
      ("✗ RÉFUTÉ : une seule sortie en 30 jours et %d/30 juste — "
       "publier" % okN) if dN == 1 and okN >= 28 else
      "✗ une sortie unique mais %d/30 juste (instable autrement)"
      % okN)
print("B2 justesse :", "✓" if okN <= 27 else
      "✗ %d/30 jours justes à nu (seuil ≤27)" % okN, "— mesuré:",
      "%d/30" % okN)
print("B3 retry    :", "✓" if okR < 30 and tokR >= 1.5 * tokN else
      "✗ R=%d/30, tokens R/N=%.2f" % (okR, tokR / max(1, tokN)))
print("mécanisme : le retry rejoue le SILENCE — R silence = %d, "
      "N silence = %d (journées facturées ~8192 tokens de "
      "reasoning, réponse vide)" % (silence(R), silence(N)))
m_ok = sum(1 for r in M if r["ok"])
print("B4 machine  :", "✓" if m_ok == len(M) == 30 and
      len({r["sha"] for r in M}) == 1 else "✗")
print("B5 facture  :", "✓" if usd_total <= 0.50 else "✗",
      "$%.4f total" % usd_total)
print("\nrappel v19 (mêmes fixtures, qwen 1.5b nu) : 0/30 justes, "
      "21 sorties distinctes ; 7b nu : 0/30, 4 sorties.")
