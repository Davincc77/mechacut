# bench v10 runner — NU vs RELAIS. 2 modèles gratuits « un peu plus
# forts » (7b-q4, 8b) × 18 tâches × 2 bras, temp 0, seed 42, même
# num_ctx/num_predict pour les deux bras (leçons llm-ab-bench).
# Bras B : l'humain-énoncé est REMPLACÉ par la question nue sans les
# données ; le modèle choisit la route dans SHORTLIST et nomme les args
# ($name) ; le harness BIND les vraies données, APPELLE le serveur LIVE
# et EXTRACT la réponse — answer_from_server=True.
import json
import re
import sys
import time

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
import httpx
import golden10
import task10
from match10 import match_naked

BASE = "https://mechacut.studio"
OLLAMA = "http://127.0.0.1:11434/api/chat"
MODELS = {"7b": "qwen2.5:7b-instruct-q4_K_M", "8b": "llama3.1:8b"}
NUM_CTX, NUM_PRED = 16384, 600
JSON_RX = re.compile(r"\{.*\}", re.S)


def chat(model, prompt):
    r = httpx.post(OLLAMA, json={
        "model": model, "stream": False,
        "options": {"temperature": 0, "seed": 42, "num_ctx": NUM_CTX,
                    "num_predict": NUM_PRED},
        "messages": [{"role": "user", "content": prompt}]}, timeout=600)
    d = r.json()
    return (d.get("message", {}).get("content", ""),
            d.get("prompt_eval_count", 0) + d.get("eval_count", 0))


def bind(t):
    """Le harness substitue les vraies données — le modèle ne les a
    jamais vues dans ses propres args (binding par nom, pas copie).
    Référence = nom exact d'une clé de data, avec ou sans $."""
    args = json.loads(json.dumps(t["b_args"]))
    data = t["data"]

    def sub(v):
        if isinstance(v, str) and v in data:
            return data[v]
        if isinstance(v, str) and v.startswith("$") and v[1:] in data:
            return data[v[1:]]
        return v

    for k, v in list(args.items()):
        args[k] = sub(v)
    for st in args.get("steps") or []:
        if isinstance(st, dict):
            for kk, vv in list(st.items()):
                st[kk] = sub(vv)
    return args


_last_call = [0.0]


def server_answer(t):
    """Appelle le live et renvoie la liste des champs-réponse.
    Pace plancher 2,2 s : la limite du service est 30 req/min/IP —
    un bench qui déclenche des 429 ne mesure rien."""
    wait = 2.2 - (time.time() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    _last_call[0] = time.time()
    r = httpx.post(BASE + t["run"], json=bind(t), timeout=60)
    if r.status_code == 429:
        time.sleep(45)
        r = httpx.post(BASE + t["run"], json=bind(t), timeout=60)
    d = r.json()
    e = t["extract"]
    if e == "dv":
        return [str(d["check_char"])]
    if e == "repair_set":
        return [",".join(sorted("%d:%s" % (c["edit"]["position"],
                                           c["edit"]["to"])
                                for c in d["candidates"]))]
    if e == "hex":
        return [d["hex"]]
    if e == "b64":
        return [d["base64"]]
    if e.startswith("two:"):
        keys = e[4:].split("|")
        alias = {"effective_pct": "effective_discount_pct"}
        return [str(d[alias.get(k, k)]) for k in keys]
    if e == "date_result":
        return [d.get("result", d.get("resolved", ""))[:10]]
    if e == "hm_result":
        return [d["result"][11:16]]
    if e == "canonical":
        return [d["canonical"]]
    if e == "resolved0":
        return [d["columns"][0]["resolved"][0]["value"]]
    if e == "json_min":
        return [json.dumps(d["json"], separators=(",", ":"))]
    raise ValueError("unknown extractor " + e)


def norm_field(x):
    return str(x).strip().strip("'\")")


def match(gold, got, cmp):
    if got is None:
        return False
    if cmp == "set":
        a = set(gold[0].split(","))
        b = set(str(got[0]).split(","))
        return a == b
    if cmp == "json":
        try:
            return (json.loads(gold[0]) == json.loads(got[0]))
        except Exception:
            return False
    g = [norm_field(x) for x in gold]
    o = [norm_field(x) for x in got]
    if len(o) == 1 and "|" in str(o[0]):
        o = [p.strip() for p in str(o[0]).split("|")]
    o = [x for x in o if x != ""]
    return g == o[:len(g)] or o == g


def naked_prompt(t):
    return (t["naked"] + "\n\nRules: no tools, no code — compute it "
            "yourself. Give ONLY the answer line(s) exactly as asked.")


def arm_b_prompt(t):
    routes = "\n".join("- %s — %s (args: %s)"
                       % (r["path"], r["one_liner"], r["args_hint"])
                       for r in task10.SHORTLIST)
    data_note = ("The task data lives ALREADY on your side under names "
                 + ", ".join("$" + k for k in t["data"]) +
                 ". NEVER copy data values: reference them as \"$name\"."
                 if t["data"] else "")
    return ("You are an agent with these deterministic routes:\n"
            + routes + "\n\nHUMAN TASK:\n" + t["naked"] + "\n"
            + data_note +
            "\n\nReply with EXACTLY one JSON object and nothing else:\n"
            '{"run": "<path>", "args": {<the chosen arguments>}}')


def run_matrix(out_path):
    rows = []
    with open(out_path, "a", encoding="utf-8") as fh:
        for mk, model in MODELS.items():
            for t in task10.TASKS:
                gold = golden10.GOLD[t["id"]]
                # bras A — NU
                t0 = time.time()
                textA, tokA = chat(model, naked_prompt(t))
                okA = match_naked(textA, gold, t["cmp"])
                rowA = {"harness": "v10", "suite": "0.72.0",
                        "model": mk, "task": t["id"], "arm": "naked",
                        "ok": bool(okA), "tokens": tokA,
                        "secs": round(time.time() - t0, 1),
                        "head": textA.strip()[:160].replace("\n", " ")}
                fh.write(json.dumps(rowA, ensure_ascii=False) + "\n")
                fh.flush()
                rows.append(rowA)
                print("%-4s %-20s naked %s  %s" % (
                    mk, t["id"], "✓" if okA else "✗",
                    rowA["head"][:70]), flush=True)
                # bras B — RELAIS (choix de route, le serveur répond)
                t0 = time.time()
                textB, tokB = chat(model, arm_b_prompt(t))
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
                    # binding : les args nommés par le modèle sont
                    # re-remplis depuis la tâche — la valeur du modèle
                    # est IGNORÉE pour la donnée (anti-transcription)
                    merged = bind(t)
                    for k, v in (sel.get("args") or {}).items():
                        if k not in merged and k not in (
                                "mode", "scheme", "algo", "phrase",
                                "op", "params", "tz", "currency", "qty",
                                "steps", "force_array", "sort_params",
                                "drop_fragment"):
                            err = "invented_arg:%s" % k
                    try:
                        got = server_answer(tt)
                    except Exception as e:
                        got, err = None, "server:%s" % e
                okB = match(gold, got, t["cmp"])
                rowB = {"harness": "v10", "suite": "0.72.0",
                        "model": mk, "task": t["id"], "arm": "relay",
                        "ok": bool(okB), "tokens": tokB,
                        "secs": round(time.time() - t0, 1),
                        "route": (sel or {}).get("run"),
                        "answer_from_server": True,
                        "err": err,
                        "head": textB.strip()[:160].replace("\n", " ")}
                fh.write(json.dumps(rowB, ensure_ascii=False) + "\n")
                fh.flush()
                rows.append(rowB)
                print("%-4s %-20s relay %s  %s" % (
                    mk, t["id"], "✓" if okB else "✗",
                    str(got or rowB["head"])[:70]), flush=True)
    return rows


if __name__ == "__main__":
    import payments
    # audit « le bench coûte $0 » : chaque route touchée doit être free
    paid_hits = [t["run"] for t in task10.TASKS
                 if t["run"] in payments.PRICES]
    assert not paid_hits, \
        "routes payantes dès le 1er appel: %s" % paid_hits
    # les routes CAP_ROUTES (🟡) ne sont gratuites QUE sous le cap :
    # le bench le prouve par la taille réelle du corps envoyé.
    for t in task10.TASKS:
        if t["run"] in payments.CAP_ROUTES:
            n = len(json.dumps(bind(t)).encode("utf-8"))
            assert n < 32 * 1024, "%s payload %d o >= cap" % (
                t["run"], n)
    print("free-audit OK: 0 route payante, payloads 🟡 sous le cap")
    if "--probe" in sys.argv:
        bad = 0
        for t in task10.TASKS:
            try:
                got = server_answer(t)
                ok = match(golden10.GOLD[t["id"]], got, t["cmp"])
            except Exception as e:
                got, ok = "EXC:%s" % e, False
            bad += 0 if ok else 1
            print("%-20s %s gold=%s server=%s" % (
                t["id"], "OK " if ok else "DÉSACCORD",
                golden10.GOLD[t["id"]], got))
        print("probe:", len(task10.TASKS) - bad, "/", len(task10.TASKS))
        sys.exit(1 if bad else 0)
    run_matrix("/Users/vincenzocirilli/Downloads/mechacut/bench/"
               "results_v10.jsonl")
