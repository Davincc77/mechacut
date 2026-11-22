# bench v14 — la SKILL comme couche de compréhension.
# Thèse de l’opérateur (22-11) : si le document à télécharger est assez
# STRICT (gabarits fermés, jamais de phrase libre, une expression par
# tour, le serveur calcule), la décomposition que le modèle ratait à
# l'état pur (v13 relais 0-6/20) devient-elle remplissable ?
#
# Protocole skill-relay : message système = la skill ci-dessous, mot
# pour mot telle qu'elle serait téléchargée. Puis boucle : le modèle
# répond STRICTEMENT {"step": "<expression fermée>"} — le harness
# évalue via math/calc LIVE et renvoie {"value": "…"} ; quand il croit
# avoir fini : {"answer": "<valeur>"}. Violation du gabarit →
# l'erreur NOMME le champ et la forme (error-that-repairs), UNE seule
# fois. Max 6 étapes. Comparaison : mêmes 20 questions, mêmes 4
# modèles que v13 (nu/code/relais déjà mesurés).
import json
import re
import sys
import time

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
import httpx
from run12 import MODELS, BASE
from run13 import load_subset, norm_int

OUT = "/Users/vincenzocirilli/Downloads/mechacut/bench/" \
      "results_v14_skill.jsonl"

SKILL = """You solve math word problems ONLY by filling this protocol.
You never compute. You never write sentences. You never explain.

Each turn, reply with EXACTLY one JSON object, nothing else:
  {"step": "<plain arithmetic expression>"}   — to compute something
  {"answer": "<value>"}                      — when the last value IS
                                               the answer

Rules for "step" expressions:
- digits, . + - * / ( ) and previously named values ONLY
- reference earlier results by writing them again as numbers, from
  the latest {"value": ...} you received
- ONE operation pair per step: "16-3" not the whole problem

Steps:
1. Read one number the problem gives you.
2. One step = the next quantity you need.
3. When a value equals what the question asked, send {"answer": ...}.

If your line is not exactly one of the two JSON forms, the server
replies {"error": ...} telling you the field and the shape. Fix it,
send one line again."""

ERR = ('{"error": "protocol: reply EXACTLY {\\"step\\": \\"<expression>'
       '\\"} or {\\"answer\\": \\"<value>\\"} — nothing else"}')


def chat_msghist(model, msgs, n=160):
    t0 = time.time()
    r = httpx.post("http://127.0.0.1:11434/api/chat", json={
        "model": model, "messages": msgs, "stream": False,
        "options": {"temperature": 0, "seed": 42, "num_ctx": 8192,
                    "num_predict": n}}, timeout=300)
    d = r.json()
    return (d.get("message", {}).get("content", ""),
            d.get("prompt_eval_count", 0) + d.get("eval_count", 0),
            round(time.time() - t0, 2))


def calc_live(expr):
    time.sleep(2.1)   # le service limite 30/min/IP — ce bench le respecte
    r = httpx.post(BASE + "/api/v1/math/calc", json={"expr": expr},
                   timeout=30)
    if r.status_code != 200:
        return None, r.json()
    return r.json()["value"], None


def run_skill(model, q):
    msgs = [{"role": "system", "content": SKILL},
            {"role": "user", "content": q}]
    steps, tokens, secs, repaired = [], 0, 0.0, 0
    while len(steps) < 6:
        text, tok, sec = chat_msghist(model, msgs)
        tokens += tok
        secs += sec
        m = re.search(r"\{.*\}", text, re.S)
        obj = None
        if m:
            try:
                obj = json.loads(m.group(0))
            except Exception:
                obj = None
        if not isinstance(obj, dict) or \
                set(obj) not in ({"step"}, {"answer"}):
            if repaired:
                return steps, "protocol_giveup", tokens, secs
            repaired += 1
            msgs.append({"role": "user", "content": text})
            msgs.append({"role": "assistant", "content": ERR})
            continue
        if "answer" in obj:
            steps.append({"answer": str(obj["answer"])[:40]})
            return steps, None, tokens, secs
        expr = str(obj["step"])[:120]
        if not re.fullmatch(r"[0-9+\-*/().\s]+", expr):
            if repaired:
                return steps, "step_not_closed", tokens, secs
            repaired += 1
            msgs.append({"role": "assistant", "content":
                         json.dumps(obj)})
            msgs.append({"role": "user", "content":
                         '{"error": "step must contain only digits '
                         'and + - * / ( )"}'})
            continue
        val, err = calc_live(expr)
        if err:
            return steps, "calc_refused:" + expr[:30], tokens, secs
        steps.append({"step": expr, "value": val})
        msgs.append({"role": "assistant", "content": json.dumps(obj)})
        msgs.append({"role": "user",
                     "content": '{"value": "%s"}' % val})
    return steps, "max_steps", tokens, secs


if __name__ == "__main__":
    subset = load_subset()
    only = sys.argv[1:] or list(MODELS)
    with open(OUT, "a", encoding="utf-8") as fh:
        for mk in only:
            for t in subset:
                steps, err, tok, sec = run_skill(MODELS[mk], t["q"])
                ans = steps[-1].get("answer") if steps else None
                ok = norm_int(ans) == norm_int(t["gold"])
                row = {"harness": "v14-skill", "seed": 1301,
                       "idx": t["i"], "model": mk, "arm": "skill",
                       "ok": ok, "answer": ans, "gold": t["gold"],
                       "steps": len(steps), "err": err,
                       "tokens": tok, "secs": round(sec, 2),
                       "trace": json.dumps(steps)[:400]}
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                fh.flush()
                print("%-4s #%4d %s ans=%s gold=%s steps=%d %s"
                      % (mk, t["i"], "✓" if ok else "✗", ans,
                         t["gold"], len(steps), err or ""),
                      flush=True)
