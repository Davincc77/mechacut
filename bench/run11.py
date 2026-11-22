# bench v11 — NU vs RELAIS, 15 tâches conçues pour le zéro nu.
# Réutilise les primitives v10 (chat temp0/seed42/16k, bind par nom,
# match_naked champ par champ, pace 2,2s + backoff 429), ajoute les
# extracteurs v11 et le relais PIPELINE (recette gelée, composition
# absorbée par le produit — disclosure dans le foot du landing).
import json
import re
import sys
import time

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
import httpx
from decimal import Decimal

import golden11
import task11
from match10 import match_naked
from run10 import (BASE, MODELS, OLLAMA, chat, JSON_RX, _last_call)
from task10 import SHORTLIST as SHORTLIST10

SHORTLIST = SHORTLIST10 + [
    {"path": "/api/v1/pipeline",
     "args_hint": 'steps:[{tool,args}] with {"$from":[i,"key"]} refs',
     "one_liner": "run 1..8 tools as one call, later steps read earlier "
                  "results"},
    {"path": "/api/v1/json/canonical",
     "args_hint": "input",
     "one_liner": "canonical JSON (keys sorted, minified) + exact "
                  "sha256 of the emitted text"},
]

DATA11 = {t["id"]: t.get("data", {}) for t in task11.TASKS11}


def bind11(t):
    args = json.loads(json.dumps(t["b_args"]))
    data = t.get("data", {})

    def sub(v):
        if isinstance(v, str) and v == "$recipe":
            return t.get("recipe")
        if isinstance(v, str) and v in data:
            return data[v]
        return v

    for k, v in list(args.items()):
        args[k] = sub(v)
    return args


EXTRACT11 = {
    "v11_sha512_64": "hex",
    "v11_biz_holidays": "date_result",
    "v11_diff_biz_hol": "int_result",
    "v11_canon_sha": "sha256",
    "v11_url_canon": "canonical",
    "v11_recurring": "date_result",
}


def server_answer11(t):
    wait = 2.2 - (time.time() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    _last_call[0] = time.time()
    r = httpx.post(BASE + t["run"], json=bind11(t), timeout=60)
    if r.status_code == 429:
        time.sleep(45)
        r = httpx.post(BASE + t["run"], json=bind11(t), timeout=60)
    d = r.json()
    e = EXTRACT11.get(t["id"], t.get("extract", "dv"))
    if e == "dv":
        return [str(d["check_char"])]
    if e == "hex":
        return [d["hex"]]
    if e == "tail12_last_hex":
        return [d["output"]["hex"][-12:]]
    if e == "max0":
        vals = [Decimal(x["value"]) for x in d["columns"][0]["resolved"]]
        return ["%.2f" % max(vals)]
    if e == "max_types":
        vals = [Decimal(str(row["montant"]).replace(",", ""))
                for row in d["output"]]
        return ["%.2f" % max(vals)]
    if e == "date_result":
        return [d.get("result", d.get("resolved", ""))[:10]]
    if e == "int_result":
        return [str(d["business_days"])]
    if e == "canonical":
        return [d["canonical"]]
    if e == "sha256":
        return [d["sha256"]]
    raise ValueError("extract " + e)


def arm_b_prompt11(t):
    routes = "\n".join("- %s — %s (args: %s)"
                       % (r["path"], r["one_liner"], r["args_hint"])
                       for r in SHORTLIST)
    dn = ("The task data is on your side under "
          + ", ".join("$" + k for k in t.get("data", {}))
          + ". NEVER copy data values; reference them as \"$name\"."
          if t.get("data") else "")
    recipe_note = ('For THIS task the steps array is already prepared '
                   'for you — reference it as "$recipe".\n'
                   if "recipe" in t else "")
    return ("You are an agent with these deterministic routes:\n"
            + routes + "\n\nHUMAN TASK:\n"
            + t["naked"][:600] + "\n" + dn + "\n" + recipe_note +
            "\nReply with EXACTLY one JSON and nothing else:\n"
            '{"run": "<path>", "args": {<arguments>}}')


def run11(out_path):
    with open(out_path, "a", encoding="utf-8") as fh:
        for mk, model in MODELS.items():
            for t in task11.TASKS11:
                gold = golden11.GOLD11[t["id"]]
                textA, tokA = chat(model, t["naked"] +
                                   "\n\nRules: no tools, no code — "
                                   "compute it yourself. Give ONLY the "
                                   "answer line exactly as asked.")
                okA = match_naked(textA, gold, t["cmp"])
                rowA = {"harness": "v11", "suite": "0.73.2", "model": mk,
                        "task": t["id"], "arm": "naked", "ok": okA,
                        "tokens": tokA,
                        "head": textA.strip()[:140].replace("\n", " ")}
                fh.write(json.dumps(rowA, ensure_ascii=False) + "\n")
                fh.flush()
                print("%-4s %-18s naked %s %s" % (mk, t["id"],
                      "✓" if okA else "✗", rowA["head"][:56]),
                      flush=True)
                textB, tokB = chat(model, arm_b_prompt11(t))
                m = JSON_RX.search(textB)
                sel = None
                if m:
                    try:
                        sel = json.loads(m.group(0))
                    except Exception:
                        sel = None
                got, err = None, None
                if isinstance(sel, dict) and sel.get("run"):
                    tt = dict(t)
                    tt["run"] = sel["run"]
                    if sel["run"] != t["run"]:
                        # le modèle a choisi une route hors contrat de la
                        # tâche — on exécute SA réponse, l'extractor de la
                        # tâche ne s'appliquera que si le chemin colle
                        pass
                    try:
                        got = server_answer11(tt)
                    except Exception as e:
                        got, err = None, "%s" % e
                okB = match_naked("\n".join(map(str, got or [])), gold,
                                  t["cmp"]) if got else False
                rowB = {"harness": "v11", "suite": "0.73.2", "model": mk,
                        "task": t["id"], "arm": "relay", "ok": okB,
                        "tokens": tokB, "route": (sel or {}).get("run"),
                        "answer_from_server": True, "err": err,
                        "head": textB.strip()[:140].replace("\n", " ")}
                fh.write(json.dumps(rowB, ensure_ascii=False) + "\n")
                fh.flush()
                print("%-4s %-18s relay %s %s" % (mk, t["id"],
                      "✓" if okB else "✗",
                      str(got or rowB["head"])[:56]), flush=True)


if __name__ == "__main__":
    if "--probe" in sys.argv:
        bad = 0
        for t in task11.TASKS11:
            try:
                got = server_answer11(t)
                ok = all(g == o for g, o in
                         zip(golden11.GOLD11[t["id"]], got)) and \
                    len(got) == len(golden11.GOLD11[t["id"]])
            except Exception as e:
                got, ok = "EXC %s" % e, False
            bad += 0 if ok else 1
            print("%-18s %s gold=%s srv=%s" % (
                t["id"], "OK " if ok else "DÉSACCORD",
                str(golden11.GOLD11[t["id"]])[:24], str(got)[:24]))
        print("probe v11:", len(task11.TASKS11) - bad, "/",
              len(task11.TASKS11))
        sys.exit(1 if bad else 0)
    run11("/Users/vincenzocirilli/Downloads/mechacut/bench/"
          "results_v11.jsonl")
