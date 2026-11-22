# Agrégateur v16 — la table de calibration et le VERDICT, comptés
# exactement comme le docstring de run16.py les a gelés AVANT les
# données. Aucune marge de négociation ici : seuils importés nulle
# part, écrits deux fois exprès (si quelqu'un change l'un, l'autre
# ment).
import json

ROWS = [json.loads(l) for l in open(
    "/Users/vincenzocirilli/Downloads/mechacut/bench/"
    "results_v16_calibration.jsonl")]
print("cellules:", len(ROWS))
for mk in ("0.5b", "1.5b", "7b", "8b"):
    rs = [r for r in ROWS if r["model"] == mk]
    valid = [r for r in rs if r["err"] is None]
    ok = [r for r in valid if r["ok"]]
    wrong = [r for r in valid if not r["ok"]]
    p_nc_w = (sum(1 for r in wrong if r["confident"] is False)
              / len(wrong)) if wrong else float("nan")
    p_c_k = (sum(1 for r in ok if r["confident"] is True)
             / len(ok)) if ok else float("nan")
    if p_nc_w >= 0.40 and p_c_k >= 0.70:
        verdict = "DISCRIMINE"
    elif p_nc_w < 0.20:
        verdict = "DÉCORATIVE"
    else:
        verdict = "PARTIEL"
    conf_ = [r for r in valid if r.get("conf_explicit")]
    print("%-5s juste %2d/%2d | formes cassées %d | "
          "P(¬confiant|faute)=%.2f P(confiant|juste)=%.2f | "
          "champ explicite posé %d/%d → %s"
          % (mk, len(ok), len(rs), len(rs) - len(valid),
             p_nc_w, p_c_k, len(conf_), len(rs), verdict))
