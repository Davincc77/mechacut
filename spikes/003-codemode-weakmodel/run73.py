# Spike 003 — un modèle FAIBLE écrit-il une chaîne code-mode mieux qu'il ne
# choisit des tool-calls ? Même tâche que bench v7 (note d'incident → JSON),
# bras B (protocole steps JSON, baseline mesurée) vs bras C (un seul programme
# JS exécuté par le pont spike-002 contre la prod mechacut).
import sys, json, time, os
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
import run7, task7

BASE = "https://mechacut.studio"

# ---- executor vm (réutilise le pattern spike 002) ----
import vm_probe  # noqa  (petit helper local, voir vm_probe.py)

SDK = """You may write ONE JavaScript program instead. Global available:
  await codemode.extract_facts({text: NOTE}) -> {facts: [{kind, value, at, context}]}
     kinds include "money" (e.g. "$4,300.00"), "percent" ("12.5%"),
     "date" ("2026-11-18"), "number".
  await codemode.list_dedupe({items}) -> {output: [...]}   // keeps first-seen order
  await codemode.sort_natural({items}) -> {sorted: [...]}  // human order: c-2 < c-10
The full incident note is ALREADY in the global string NOTE — do not retype it.
codemode and NOTE are already defined — no import statements.
extract_facts resolves to an object; its list is under .facts

Reply with EXACTLY one expression, no prose, no fences:
  async () => { ...your program... return THE_ANSWER }
where THE_ANSWER is the JSON object requested above. Lists must already be
sorted ascending as strings."""


def build_C_prompt():
    note = run7.TASK[run7.TASK.index("Note:\n") + 6:]
    spec = run7.TASK[:run7.TASK.index("Note:\n")]
    return spec + SDK + "\nNOTE = " + json.dumps(note) + "\n\nYour expression:"


def get_note():
    return run7.TASK[run7.TASK.index("Note:\n") + 6:]


def exec_C_answer(text, tok):
    """exécute le programme JS du modèle dans node:vm (le runner Node fait
    les vrais appels HTTP ; on les compte via la réponse extract_facts)."""
    import re
    note = get_note()
    m = re.search(r"async\s*\(\)\s*=>\s*\{.*\}", text, re.S)
    prog = m.group(0) if m else None
    if not prog:
        return {"__exec_error": "no async arrow found"}, 0
    result, err = vm_probe.run_vm(prog, None, extra_globals={"NOTE": note})
    if err:
        return {"__exec_error": err[:160]}, 0
    return result, 1


def score7_result(res):
    if res is None or "__exec_error" in (res if isinstance(res, dict) else {}):
        return None
    return task7.score7(json.dumps(res))


def run(model_key):
    model = run7.MODELS[model_key]
    row = {"model": model_key, "harness": "003"}
    # --- Bras B : protocole steps JSON (baseline v7) ---
    msgs = [{"role": "user", "content": run7.TASK + "\n\n" + run7.SHAPES}] \
        + run7.forced_opening()
    tok_in = 0; answer = ""
    for _ in range(2):
        out, t = run7.chat(model, msgs); tok_in += t
        ex = run7.exec_steps(out)
        if ex is None:
            answer = out; break
        msgs.append({"role": "assistant", "content": out})
        msgs.append({"role": "user", "content": ex})
        answer = out
    sb = task7.score7(answer)
    row["B"] = {"keys": (None if not sb else
               sum(1 for k in task7.REQUIRED_KEYS
                   if task7.norm(k, sb[2].get(k)) == task7.norm(k, task7.expected7()[k]))),
               "valid_json": bool(sb), "tokens": tok_in}
    # --- Bras C : programme unique (+1 passe réparation, symétrique de B) ---
    c_msgs = [{"role": "user", "content": build_C_prompt()}]
    c_raw, c_tok = run7.chat(model, c_msgs)
    res, net = exec_C_answer(c_raw, c_tok)
    MAXR = int(os.environ.get("REPAIRS", "2"))
    repairs = 0
    while isinstance(res, dict) and "__exec_error" in res and repairs < MAXR:
        err = res["__exec_error"]
        c_msgs.append({"role": "assistant", "content": c_raw})
        c_msgs.append({"role": "user", "content":
            "Execution error: " + err +
            "\nFix and reply with ONE corrected expression, no prose."})
        c_raw, t = run7.chat(model, c_msgs)
        c_tok += t
        res, net = exec_C_answer(c_raw, c_tok)
        repairs += 1
    sc = score7_result(res)
    row["C"] = {"keys": (None if not sc else
               sum(1 for k in task7.REQUIRED_KEYS
                   if task7.norm(k, sc[2].get(k)) == task7.norm(k, task7.expected7()[k]))),
               "parsed": sc is not None, "exec_ok": "__exec_error" not in res,
               "exec_err": res.get("__exec_error") if isinstance(res, dict) else None,
               "net_calls": net, "tokens": c_tok, "repairs": repairs,
               "raw_head": c_raw[:300]}
    return row, c_raw


rows = []
for mk in ("1.5b", "7b"):
    r, raw = run(mk)
    rows.append(r)
    print("=== %s ===" % mk)
    print(" B :", r["B"])
    print(" C :", {k: v for k, v in r["C"].items() if k != "raw_head"})
    print(" C brut:", repr(raw[:220]))
    print()
json.dump(rows, open("/Users/vincenzocirilli/Downloads/mechacut/spikes/003-codemode-weakmodel/results.json", "w"), indent=1)
