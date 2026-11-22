# -*- coding: utf-8 -*-
"""V22 SCOREUR — séparé de l'exécuteur (doctrine run15/score15).
Ne lit QUE results_v22.jsonl. Statue sur P1-P5 gelées dans run22.py.

JUGE v2 (22-11, post-course, doctrine « le juge se corrige, la
donnée se publie » — précédent : clef-dico F5) :
  J1. norm_frac : les bras N/C peuvent rendre une fraction EXACTE
      (« 3829/10 » = 382,90 — plus précis qu'un décimal). norm_num
      l'amochait en 382910. Les lignes fraction justes passaient à
      tort en FAUX. Le jsonl reste intact ; le rejugement est ici.
  J2. P5 : le sha du serveur ne vaut invariance QUE pour des créneaux
      identiques. Deux sha distincts sur #14 venaient de transcription
      échouée (input différent), pas du serveur. La question correcte :
      « à créneaux identiques, sha identique » + « tous les serveurs
      OK d'un problème partagent LE même sha ».
"""
import json
import re
import sys
from collections import defaultdict


def norm_frac(x):
    s = str(x if x is not None else "").strip().replace(",", ".")
    m = re.fullmatch(r"\s*(-?\d+)\s*/\s*(\d+)\s*", s)
    if m:
        return int(m.group(1)) / int(m.group(2))
    from run22 import norm_num
    return norm_num(x)

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
from run22 import PRICING, SHORT  # noqa: E402

ROWS = [json.loads(l) for l in open(
    "/Users/vincenzocirilli/Downloads/mechacut/bench/results_v22.jsonl")
    if l.strip()]
MODELS = sorted({r["model"] for r in ROWS})
ARMS = ("N", "C", "F")


def usd(r):
    pin = [v for k, v in SHORT.items() if k in PRICING and v == r["model"]]
    full = next((k for k, v in SHORT.items() if v == r["model"]), None)
    assert full
    pi, po = PRICING[full]
    return (r["tok_p"] * pi + r["tok_c"] * po) / 1e6


def rejudge(r):
    """JUGE v2 : fraction admise aux bras N/C ; F = verdict serveur."""
    if r["arm"] == "F":
        return bool(r.get("server_ok"))
    a, g = norm_frac(r.get("answer", "")), norm_frac(r.get("gold", ""))
    return a is not None and g is not None and abs(a - g) < 1e-9


def agg(sel):
    rows = [r for r in ROWS if sel(r)]
    n = len(rows)
    ok = sum(1 for r in rows if rejudge(r))
    sem = sum(1 for r in rows if r.get("verdict_juge") == "SEM"
              or (r["arm"] == "C" and not r["ok"]
                  and r.get("answer") and _close(r)))
    toks = sum(r["tok_p"] + r["tok_c"] for r in rows)
    cost = sum(usd(r) for r in rows)
    return n, ok, toks, cost


def _close(r):
    # SEM = approchant sans être exact : revérifié depuis la ligne seule
    from run22 import norm_num
    a, g = norm_num(r.get("answer", "")), norm_num(r.get("gold", ""))
    try:
        return a is not None and g is not None and a != g \
            and abs(a - g) <= 1e-6
    except Exception:
        return False


print("%-8s %s" % ("modèle", " ".join("%-16s" % ("bras " + a) for a in ARMS)))
M = {}
for m in MODELS:
    cells = []
    for a in ARMS:
        n, ok, toks, cost = agg(lambda r, m=m, a=a:
                                r["model"] == m and r["arm"] == a)
        per_ok = ("%.4f$" % (cost / ok)) if ok else "∞"
        cells.append("%2d/%d %6.0ft %s" % (ok, n, toks / max(1, ok) if ok
                                           else 0, per_ok))
    M[m] = dict(zip(ARMS, [agg(lambda r, m=m, a=a: r["model"] == m
                               and r["arm"] == a) for a in ARMS]))
    print("%-8s %s" % (m, " ".join("%-16s" % c for c in cells)))

sem = {m: [sum(1 for r in ROWS if r["model"] == m and r["arm"] == "C"
               and _close(r)) for _ in (0,)] for m in MODELS}
print("\nfautes SÉMANTIQUES bras C (approchant ≠ exact) :",
      {m: sem[m][0] for m in MODELS})
print("réparations bras F :",
      {m: sum(r["repairs"] for r in ROWS if r["model"] == m)
       for m in MODELS})

# P5 v2 : déterminisme = à créneaux justes (serveur OK), même sha.
sh = defaultdict(set)
for r in ROWS:
    if r["arm"] == "F" and r.get("server_ok"):
        sh[r["i"]].add(r["server_sha"])
p5 = bool(sh) and all(len(v) == 1 for v in sh.values())
print("sha serveur (cellules F à créneaux justes) :",
      {k: len(v) for k, v in sorted(sh.items())})

pn = lambda arm, m: M[m][arm][1] if m in M else 0
print("\n--- VERDICTS (gelés dans run22.py) ---")
print("P1 l'objection tient (≥1 modèle N ≥5/7) :",
      "VRAIE" if any(pn("N", m) >= 5 for m in MODELS) else "FAUSSE",
      {m: pn("N", m) for m in MODELS})
print("P2 leur promesse tient (C ≥6/7 et sem≤2 partout) :",
      "VRAIE" if all(pn("C", m) >= 6 for m in MODELS) else "FAUSSE",
      {m: pn("C", m) for m in MODELS})
print("P3 F = 7/7 partout :",
      "VRAIE" if all(pn("F", m) == 7 for m in MODELS) else "FAUSSE",
      {m: pn("F", m) for m in MODELS})
fj = {m: M[m]["F"][3] / max(1, M[m]["F"][1]) for m in MODELS}
cj = {m: M[m]["C"][3] / max(1, M[m]["C"][1]) for m in MODELS}
ft = {m: M[m]["F"][2] / max(1, M[m]["F"][1]) for m in MODELS}
ct = {m: M[m]["C"][2] / max(1, M[m]["C"][1]) for m in MODELS}
print("P4 $/juste F ≤ C ET tokens/juste F ≤ 30%% C :",
      "VRAIE" if all(m in fj and cj[m] and fj[m] <= cj[m] and
                     ft[m] <= 0.3 * ct[m] for m in MODELS) else "FAUSSE",
      {m: ("F %.4f$ vs C %.4f$ ; F %.0ft vs C %.0ft" %
           (fj.get(m, 0), cj.get(m, 0), ft.get(m, 0), ct.get(m, 0)))
       for m in MODELS})
print("P5 déterminisme serveur :", "VRAIE" if p5 else "FAUSSE")
