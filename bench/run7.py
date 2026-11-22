"""Bench v7 — the narrow-lane protocol (Nov 21).

Lesson from the v6 re-run after the suite grew 56 -> 77 entries: giving a
weak model the manifest shortlist computed live degraded arm B (1.5b wrote
7200 prose tokens, 0 tool calls). More product, same navigation = worse
for the weakest. v7 tests the actual product answer: a TASK-SPECIFIC skill
pack (three tool shapes, nothing else) — navigation as a product, not an
afterthought.

  arm A : task text only.
  arm B : task text + 3 closed tool shapes + the steps protocol.

Models: qwen2.5 0.5b / 1.5b / 7b, temp 0, seed 42. Scoring: canonical sha
over the five required keys (bench/task7.py), computed by the suite.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "bench"))

import task7  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402

CLIENT = TestClient(app)
OLLAMA = "http://127.0.0.1:11434/api/chat"
SEED = 42
MODELS = {"0.5b": "qwen2.5:0.5b-instruct",
          "1.5b": "qwen2.5:1.5b-instruct",
          "7b": "qwen2.5:7b-instruct-q4_K_M"}
RESULTS = ROOT / "bench" / "results.jsonl"
HARNESS = "v7"

TASK = (
    "Read the incident note below. Answer with EXACTLY one JSON object and "
    "nothing else, with keys:\n"
    '  {"amounts_usd": [...], "percentages": [...], "dates_utc": [...], '
    '"services": [...], "failed_checkouts": "..."}\n'
    "Lists sorted ascending as strings; strip $ and %; dates_utc = the "
    "unique calendar dates in YYYY-MM-DD form, WITHOUT times; services = "
    "the unique lowercase API/service names mentioned. Note:\n\n"
    + task7.NOTE)

SHAPES = (
    "A FIRST TOOL CALL was already made for you (extract_facts with "
    'group="kind" returns DEDUPED values per kind — use it, do not '
    "re-derive). You may call more tools, each reply one JSON steps "
    "object:\n"
    '  {"steps":[{"tool":"list_dedupe","args":{"items":["a","b"]}}]}\n'
    '  {"steps":[{"tool":"check_constraints","args":{"text":"<your '
    'json>","constraints":{"max_words":120}}}]}\n'
    "When you are done with tools, reply with the FINAL JSON object "
    "only — never repeat a call you already made.")


def finalize(msgs, model):
    msgs.append({"role": "user",
                 "content": "No more tool calls. Reply with the final "
                            "JSON object only."})
    out, tok = chat(model, msgs)
    return out, tok


def chat(model, messages, n=2000):
    r = httpx.post(OLLAMA, json={
        "model": model, "messages": messages, "stream": False,
        "options": {"temperature": 0, "seed": SEED, "num_predict": n}},
        timeout=600)
    d = r.json()
    return (d.get("message") or {}).get("content") or "", \
        d.get("prompt_eval_count", 0) + d.get("eval_count", 0)


def exec_steps(content):
    """Execute a {"steps":[...]} reply against the real app; return a
    tool-output message or None if not a steps reply."""
    import re
    m = re.search(r"\{.*\}", content, re.S)
    if not m:
        return None
    try:
        doc = json.loads(m.group(0))
    except Exception:
        return None
    steps = doc.get("steps")
    if not isinstance(steps, list) or not steps:
        return None
    outs = []
    for st in steps[:4]:
        tool = st.get("tool")
        args = st.get("args") or {}
        if not isinstance(tool, str):
            outs.append({"error": "step needs tool"})
            continue
        rr = CLIENT.post("/api/v1/" + {
            "extract_facts": "extract/facts",
            "list_dedupe": "list/dedupe",
            "check_constraints": "check/constraints"}.get(tool, ""),
            json=args) if tool in ("extract_facts", "list_dedupe",
                                   "check_constraints") else None
        outs.append({"tool": tool, "status": rr.status_code if rr else 404,
                     "body": rr.json() if rr else "unknown tool"})
    return json.dumps({"results": outs})


def forced_opening():
    """One-shot: the harness plays the first tool call itself (like v6's
    pinned example) so the model sees real tool results before answering.
    Deterministic: same note, same call, same bytes."""
    step = json.dumps({"steps": [{"tool": "extract_facts",
                                  "args": {"text": task7.NOTE,
                                           "context_chars": 0,
                                           "group": "kind"}}]})
    obs = exec_steps(step)
    return [{"role": "assistant", "content": step},
            {"role": "user", "content": obs}]


def run(model_key):
    model = MODELS[model_key]
    for arm in ("A", "B"):
        t0 = time.time()
        tin = tout = calls = 0
        answer = ""
        if arm == "A":
            out, tok = chat(model, [{"role": "user", "content": TASK}])
            tin, tout = tok, 0
            answer = out
        else:
            msgs = ([{"role": "user", "content": TASK + "\n\n" + SHAPES}]
                    + forced_opening())
            calls += 1   # the pinned extract_facts step IS a tool call
            for _round in range(3):
                out, tok = chat(model, msgs)
                tin += tok
                obs = exec_steps(out)
                if obs is None:
                    answer = out
                    break
                calls += 1
                msgs.append({"role": "assistant", "content": out})
                msgs.append({"role": "user", "content": obs})
            answer = out
            if exec_steps(answer) is not None:   # model stuck calling
                answer, tok = finalize(msgs, model)
                tin += tok
            # erreurs-réparent : une passe de réparation JSON guidée
            import re as _re
            _m = _re.search(r"\{.*\}", answer or "", _re.S)
            _okj = False
            if _m:
                try:
                    json.loads(_m.group(0))
                    _okj = True
                except Exception:
                    pass
            if arm == "B" and not _okj:
                msgs.append({"role": "assistant", "content": answer})
                msgs.append({"role": "user", "content":
                             'invalid JSON: your reply must parse as one '
                             "JSON object, all values quoted as strings. "
                             "Fix and reply with JSON only."})
                answer, tok = chat(model, msgs)
                tin += tok
                calls += 1
        scored = task7.score7(answer)
        success = bool(scored) and scored[3] is True
        keys_ok = {}
        if scored:
            want_doc = task7.expected7()
            for k in task7.REQUIRED_KEYS:
                keys_ok[k] = (task7.norm(k, scored[2].get(k))
                              == task7.norm(k, want_doc[k]))
        rec = {"model": model_key, "arm": arm, "keys_ok": keys_ok,
               "tokens": tin,
               "tool_calls": calls, "success": success,
               "seconds": round(time.time() - t0, 2),
               "seed": SEED, "temp": 0, "harness": HARNESS}
        with RESULTS.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(rec, flush=True)


if __name__ == "__main__":
    keys = [a for a in sys.argv[1:] if a in MODELS] or list(MODELS)
    for k in keys:
        run(k)
