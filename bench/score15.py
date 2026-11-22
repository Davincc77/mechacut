# score15 — statue les prédictions G1-G5 gelées dans run15.py, à partir
# de la matrice complète. Aucune marge de négociation : les seuils sont
# les énoncés de run15, réécrits ici pour que le juge soit séparé de
# l'exécuteur.
import json
import collections

RS = [json.loads(l) for l in open(
    "bench/results_v15_matrix.jsonl")]
print("cellules:", len(RS), "/ 400 attendues")
MODELS = ["0.5b", "1.5b", "7b", "8b"]
ARMS = ["N", "C", "R", "S", "T"]
CHAINE = {"mix", "partage"}


def cell(mk, arm, fam=None):
    rs = [r for r in RS if r["model"] == mk and r["arm"] == arm
          and (fam is None or r["family"] in fam)]
    ok = sum(r["ok"] for r in rs)
    tok = sum(r["tokens"] for r in rs)
    return ok, len(rs), tok


print("\n%-5s %s" % ("mod", "  ".join("%-10s" % a for a in ARMS)))
mat = {}
for mk in MODELS:
    row = []
    for a in ARMS:
        o, n, t = cell(mk, a)
        mat[(mk, a)] = (o, n, t)
        row.append("%2d/%2d %5d" % (o, n, t / max(o, 1) if o else -1))
    print("%-5s %s" % (mk, "  ".join(row)))
print("  (forme: succès / tokens-par-juste ; -1 = 0 succès)")

print("\n=== statuts des prédictions gelées ===")
# G1 : S >= tous les autres bras, sur chaque modèle
g1 = all(mat[(mk, "S")][0] >= mat[(mk, a)][0]
         for mk in MODELS for a in ("N", "C", "R", "T"))
print("G1 S domine partout:", "✓" if g1 else "✗ — détailler",
      {mk: {a: mat[(mk, a)][0] for a in ARMS} for mk in MODELS}
      if not g1 else "")
# G2 : T ≈ N mais ~5× les tokens (retry n'achète rien)
g2 = all(abs(mat[(mk, "T")][0] - mat[(mk, "N")][0]) <= 3
         for mk in MODELS)
print("G2 retry≈nu (±3) :", "✓" if g2 else "✗",
      {mk: (mat[(mk, "N")][0], mat[(mk, "T")][0]) for mk in MODELS})
# G3 : R s'effondre <7B
g3 = mat[("0.5b", "R")][0] <= 4 and mat[("1.5b", "R")][0] <= 4
print("G3 relay-free ≤4/20 en-dessous de 7B:", "✓" if g3 else "✗",
      "0.5b", mat[("0.5b", "R")][0], "1.5b", mat[("1.5b", "R")][0])
# G4 : C fort sur 7b, fragilisé 8b
g4 = mat[("7b", "C")][0] > mat[("8b", "C")][0]
print("G4 code 7b > 8b:", "✓" if g4 else "✗",
      "7b", mat[("7b", "C")][0], "8b", mat[("8b", "C")][0])
# G5 : en chaîne, seuls S/C marquent ; N,R,T≈0
chain = {a: sum(cell(mk, a, CHAINE)[0] for mk in MODELS) for a in ARMS}
nchain = sum(cell(mk, "N", CHAINE)[1] for mk in MODELS)
g5 = chain["N"] <= nchain // 10 and chain["T"] <= nchain // 10 \
    and (chain["S"] + chain["C"]) >= nchain // 2
print("G5 chaîne (%d cellules) : N=%d R=%d T=%d | S=%d C=%d" %
      (nchain, chain["N"], chain["R"], chain["T"], chain["S"],
       chain["C"]), "✓" if g5 else "✗")

# ruptures de protocole, comptées à part (jamais confondues avec
# l'ignorance) — leçon v14/v16
proto = collections.Counter(
    r["err"] for r in RS if r.get("err"))
print("\nruptures forme/protocole:", dict(proto))
