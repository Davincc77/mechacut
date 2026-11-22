# bench v16 — le petit modèle sait-il QUAND il ne sait pas ?
# Hypothèse PRÉ-ENREGISTRÉE (file 1a078d5, écrite avant toute donnée) :
# confiance DÉCORATIVE.
#
# Méthodologie gelée avant le premier appel modèle :
#   - 20 problèmes à mots générés par graine (bench/gen16.py) : mêmes
#     familles que l'école, NOMBRES NEUFS, gold = Fraction calculée à la
#     génération. Aucune contamination possible, aucun oracle humain
#     partial : le papier tient la note AVANT que le modèle parle.
#   - bras unique NU : l'énoncé + une contrainte de forme minuscule :
#     répondre EXACTEMENT {"answer": "<nombre>", "confident": true|false}
#   - temp 0, seed 42 — la question est l'auto-connaissance, pas la
#     chance d'échantillonnage.
#   - Verdicts prédéfinis (pas de re-pilotage après coup) :
#       DISCRIMINE   si P(non-confiant | faute) ≥ 0,40
#                    ET P(confiant | juste) ≥ 0,70
#       DÉCORATIVE   si P(non-confiant | faute) < 0,20
#       PARTIEL      sinon (règle de l’opérateur applicable classe par classe)
#   - Les ruptures de forme sont comptées À PART (v14 a enseigné :
#     jamais confondre protocole et connaissance).
import json
import re
import sys
import time

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
import httpx
from gen16 import problems
from run12 import MODELS

OUT = "/Users/vincenzocirilli/Downloads/mechacut/bench/" \
      "results_v16_calibration.jsonl"

PROMPT = ("Solve this problem. Reply with EXACTLY one JSON object, "
          "nothing else:\n{\"answer\": \"<your number>\", "
          "\"confident\": true|false}\n"
          "confident=true only if you are sure your answer is correct.\n\n"
          "Problem: <Q>")


def ask(model, q):
    t0 = time.time()
    r = httpx.post("http://127.0.0.1:11434/api/chat", json={
        "model": model,
        "messages": [{"role": "user",
                      "content": PROMPT.replace("<Q>", q)}],
        "stream": False,
        "options": {"temperature": 0, "seed": 42, "num_ctx": 4096,
                    "num_predict": 120}}, timeout=180)
    d = r.json()
    return (d.get("message", {}).get("content", ""),
            d.get("prompt_eval_count", 0) + d.get("eval_count", 0),
            round(time.time() - t0, 2))


def norm_num(x):
    s = str(x if x is not None else "").strip().replace(",", ".")
    s = re.sub(r"[^\d.\-]", "", s)
    try:
        return float(s)
    except Exception:
        return None


if __name__ == "__main__":
    qs = problems()
    print("problèmes générés:", len(qs),
          "| premier:", qs[0]["text"][:70])
    only = sys.argv[1:] or list(MODELS)
    with open(OUT, "a", encoding="utf-8") as fh:
        for mk in only:
            for t in qs:
                text, tok, sec = ask(MODELS[mk], t["text"])
                err = None
                obj = None
                m = re.search(r"\{.*\}", text, re.S)
                if m:
                    try:
                        obj = json.loads(m.group(0))
                    except Exception:
                        err = "parse"
                else:
                    err = "no_json"
                got = conf = None
                if isinstance(obj, dict) and "answer" in obj:
                    got = norm_num(obj.get("answer"))
                    conf = obj.get("confident")
                    if conf not in (True, False):
                        # AMENDEMENT de lecture, pré-enregistré avant
                        # la première cellule (le smoke test 1.5b a
                        # OMIS le champ en répondant 145 pour 240) :
                        # pas de champ = pas de doute exprimé =
                        # CONFIANCE IMPLICITE. Répondre sans hésiter
                        # est exactement le sur-plomb mesuré ; le
                        # compter « sans avis » l'effacerait des
                        # statistiques — ce serait mentir en notre
                        # faveur. Le flag « implicit » garde la trace.
                        conf = True
                        err = None if "confident" not in obj \
                            else "confident_field"
                else:
                    err = err or "shape"
                gold = float(t["gold"])
                ok = got is not None and abs(got - gold) < 0.005
                row = {"harness": "v16-calibration", "seed": 2026,
                       "i": t["i"], "family": t["family"],
                       "model": mk, "arm": "naked_confident",
                       "ok": ok, "confident": conf,
                       "conf_explicit": isinstance(obj, dict)
                       and "confident" in obj,
                       "answer": got, "gold": gold,
                       "err": err, "tokens": tok, "secs": sec,
                       "raw": text[:160]}
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                fh.flush()
                print("%-4s #%02d %s conf=%s got=%s gold=%s %s"
                      % (mk, t["i"], "✓" if ok else "✗", conf, got,
                         gold, err or ""), flush=True)
