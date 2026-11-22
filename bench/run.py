"""A/B benchmark runner v3: what a weak agent gains from mechacut.

  python bench/run.py            # all models x both arms, appends results
  python bench/run.py 1.5b B     # one cell

Task (FROZEN, seed 20261120, never edit): clean a CSV, repair JSON, dedupe
URLs, emit one YAML. Expected answer pinned by sha in bench/expected.sha.

Harness v3 design decisions (v2 post-mortem: every cell failed):
- v2 made arm B TRANSCRIBE: inject 2 KB of raw data into JSON tool args,
  then re-emit a 600-token YAML out of a JSON-escaped string at a path
  the prompt stated WRONG (output.output.output vs the real
  output.output). Mechacut's thesis is that agents must NOT transcribe;
  v2 punished B for the exact thing the product removes. v3 measures the
  thesis:
  * the model decides the chain only — {$fill} placeholders are kept
    verbatim and substituted by the harness before the call, exactly
    like a real agent passing its own variables to a tool in code
  * tool results arrive as RAW YAML text, never JSON-escaped
  * success for B = the chain the model itself produced executed to the
    canonical answer; zero transcription in either direction
- num_predict raised to 3000 for both arms (v2's 1500 truncated honest
  arm-A attempts — a cap artifact, not a capability signal).
- Rows are tagged {"harness": "v3"}; v2 rows stay in results.jsonl as
  evidence of the design flaw.

Metrics: tokens in+out, tool calls, success, wall-clock. temp=0, seed 42.
"""
import hashlib
import json
import re
import sys
import time

import httpx
import yaml

sys.path.insert(0, ".")
sys.path.insert(0, "bench")
import task_data
import routing
from main import app
from fastapi.testclient import TestClient

OLLAMA = "http://127.0.0.1:11434/api/chat"
SEED = 42
MODELS = {"0.5b": "qwen2.5:0.5b-instruct",
          "1.5b": "qwen2.5:1.5b-instruct",
          "7b": "qwen2.5:7b-instruct-q4_K_M"}
RESULTS = "bench/results.jsonl"
HARNESS = "v6"
NUM_PREDICT = 3000

app_client = TestClient(app)

import routing as _routing
TOOL_RUN_SINGLE = {}  # name -> path (validated through the real server)
for _n, _p, _k, _u, _t in _routing.TABLE:
    TOOL_RUN_SINGLE[_n] = _p

FILLS = {"csv": task_data.DIRTY_CSV, "json": task_data.BROKEN_JSON,
         "urls": task_data.URLS}

SKELETON = {
    "steps": [
        {"tool": "csv_fix", "args": {"csv": {"$fill": "csv"}}},
        {"tool": "csv_types", "args": {"csv": {"$from": [0, "output"]}}},
        {"tool": "list_dedupe",
         "args": {"items": {"$from": [1, "output"]}, "mode": "exact"}},
        {"tool": "json_repair", "args": {"text": {"$fill": "json"}}},
        {"tool": "list_dedupe", "args": {"items": {"$fill": "urls"},
                                         "mode": "url"}},
        {"tool": "format_convert", "args": {
            "input": {"rows": {"$from": [2, "output"]},
                      "totals": {"$from": [3, "output"]},
                      "urls": {"$from": [4, "output"]}},
            "from": "json", "to": "yaml"}},
    ]}

TOOL_SPECS = [
    {"type": "function", "function": {
        "name": "mechacut_pipeline",
        "description": (
            "Run a chain of mechacut tools server-side. steps is a list "
            "of {tool, args}; later steps reference earlier results with "
            "{\"$from\": [step_index, \"key\"]}. Data placeholders "
            "{\"$fill\": \"csv|json|urls\"} carry the task data — keep "
            "them exactly as they are. Returns the final YAML document "
            "as plain text."),
        "parameters": {"type": "object", "properties": {
            "steps": {"type": "array"}}, "required": ["steps"]}}},
]


DATA_ARGS = {"recipe_data_trio": {"csv": "csv", "json_text": "json",
                                  "urls": "urls"},
             "recipe_clean_table": {"csv": "csv"},
             "csv_fix": {"csv": "csv"},
             "json_repair": {"text": "json"}}


def _bind_data_args(tool, args):
    """v6: a real agent framework passes its own variables — the LLM
    never types data. If the model NAMED a data arg, the caller
    substitutes the true task data for that key; the value the model
    wrote is ignored. Binding = naming. Non-data args (mode, from, to,
    refs) stay exactly as written — that part is still measured."""
    for key, fill in DATA_ARGS.get(tool, {}).items():
        if key in args:
            args[key] = FILLS[fill]
    return args


def _substitute_fills(node):
    def walk(x):
        if isinstance(x, dict):
            if set(x.keys()) == {"$fill"} and x["$fill"] in FILLS:
                return FILLS[x["$fill"]]
            return {k: walk(v) for k, v in x.items()}
        if isinstance(x, list):
            return [walk(v) for v in x]
        return x
    return walk(node)


def chat(model, messages, tools=None, n=NUM_PREDICT):
    body = {"model": model, "messages": messages, "stream": False,
            "options": {"temperature": 0, "seed": SEED, "num_predict": n,
                        "num_ctx": 16384}}
    if tools:
        body["tools"] = tools
    t0 = time.time()
    r = httpx.post(OLLAMA, json=body, timeout=600)
    r.raise_for_status()
    j = r.json()
    return j, time.time() - t0


def run_arm_a(model):
    msgs = [{"role": "user", "content": task_data.TASK_TEXT}]
    j, secs = chat(model, msgs)
    return {"content": j["message"].get("content", ""),
            "tok_in": j.get("prompt_eval_count", 0),
            "tok_out": j.get("eval_count", 0),
            "calls": 0, "secs": secs}


def run_arm_b(model):
    """v5 — the product-real flow. A real weak agent does not compose a
    6-step DAG from memory: it asks the router (GET /route — deterministic,
    closed vocabulary) and binds placeholders. The harness runs that
    router call for the model (it is one HTTP GET, what any agent framework
    does mechanically) and hands back the top candidates as the manifest
    line already documents. The model still has to: pick the right tool,
    bind the three $fill keys to the right args, and answer with the
    chain JSON. Then the pipeline runs. Success = the model's own
    binding executed to the canonical answer."""
    query = ("rag preprocess dirty csv broken json dedupe urls into yaml "
             "rows totals urls")
    hits = routing.route(query, top=5)
    shortlist = "\n".join("%s  %s" % (h["tool"], h["purpose"])
                           for h in hits[:4])
    system = (
        "You drive mechacut, a deterministic tool server. Your ONLY job: "
        "answer with ONLY a JSON object and nothing else.\n"
        "Shapes:\n"
        "  a single call: {\"tool\": \"NAME\", \"args\": {...}}\n"
        "  a chain: {\"steps\": [{\"tool\": ..., \"args\": ...}]} "
        "where a later step reads an earlier one via {\"$from\": [i, "
        "\"output\"]}\n"
        "Task data is NEVER copied or invented: just NAME the data "
        "arguments (csv, json_text, urls) and your calling code fills "
        "their values automatically \u2014 whatever value you write "
        "there is ignored. Non-data args (mode, from, to, types, "
        "$from refs) you must write correctly.\n\n"
        "The server router answered this task with the candidates below "
        "(best first):\n" + shortlist + "\n\n"
        "Arg shapes:\n"
        "  recipe_data_trio {csv, json_text, urls} - one call: dirty "
        "csv + broken json + url list -> final YAML {rows, totals, "
        "urls}\n"
        "  recipe_clean_table {csv} - dirty CSV -> typed unique rows "
        "only\n"
        "  format_convert {input, from, to}; json_repair {text}; "
        "csv_fix {csv}; csv_types {csv}; list_dedupe {items, mode}\n\n"
        "Correct shape: {\"tool\": \"recipe_data_trio\", "
        "\"args\": {\"csv\": ..., \"json_text\": ..., "
        "\"urls\": ...}} \u2014 the three data args, named.")
    override = ("\n\nIMPORTANT: do NOT compute or transcribe. Per the "
                "system rules, your reply is ONLY the JSON tool call; "
                "name the data args and the caller supplies values.")
    msgs = [{"role": "system", "content": system},
            {"role": "user", "content": task_data.TASK_TEXT + override}]
    tok_in = tok_out = calls = 0
    secs = 0.0
    final_yaml = ""
    for _step in range(6):
        jx, d = chat(model, msgs, n=1200)
        secs += d
        tok_in += jx.get("prompt_eval_count", 0)
        tok_out += jx.get("eval_count", 0)
        msg = jx["message"]
        raw = (msg.get("content") or "").strip()
        m = re.search(r"\{.*\}", raw, re.S)
        call = None
        if m:
            try:
                call = json.loads(m.group(0))
            except Exception:
                call = None
        if not call:
            msgs.append(msg)
            msgs.append({"role": "user", "content":
                         "INVALID: reply with ONLY the JSON object."})
            continue
        calls += 1
        if "steps" in call:
            steps = _substitute_fills(call["steps"])
            r = app_client.post("/api/v1/pipeline", json={"steps": steps})
            body = r.json()
        elif "tool" in call:
            args = _substitute_fills(call.get("args") or {})
            args = _bind_data_args(call["tool"], args)
            runner = TOOL_RUN_SINGLE.get(call["tool"])
            if runner is None:
                body = {"errors": [{"message": "unknown tool %r"
                                         % call["tool"]}]}
                r = None
            else:
                r = app_client.post("/api/v1/pipeline", json={"steps": [
                    {"tool": call["tool"], "args": args}]})
                body = r.json()
        else:
            body = {"errors": [{"message": "reply must be "
                                     '{"tool":..., "args":...} or '
                                     '{"steps": [...]}'}]}
            r = None
        if r is not None and r.status_code == 200:
            out = body.get("output")
            if isinstance(out, dict):
                final_yaml = out.get("output") or ""
            elif isinstance(out, str):
                final_yaml = out
            break
        msgs.append(msg)
        msgs.append({"role": "user", "content": "PIPELINE_ERROR: " +
                     json.dumps(body.get("errors", body),
                                ensure_ascii=False)[:1500] +
                     "\nFix ONLY what the error names and reply again "
                     "with ONLY the full JSON."})
    try:
        import os
        os.makedirs("bench/debug", exist_ok=True)
        with open("bench/debug/%s-B.json" % model.split(":")[1], "w",
                  encoding="utf-8") as f:
            json.dump(msgs, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return {"content": final_yaml, "tok_in": tok_in, "tok_out": tok_out,
            "calls": calls, "secs": secs}


def score(content):
    if not content:
        return False
    doc = content if not isinstance(content, str) else None
    if doc is None:
        m = re.search(r"```(?:ya?ml)?\n(.*?)```", content, re.S)
        text = m.group(1) if m else content
        try:
            doc = yaml.safe_load(text)
        except Exception:
            return False
    if isinstance(doc, str):
        try:
            doc = yaml.safe_load(doc)
        except Exception:
            return False
    try:
        raw = task_data.canonical_of(doc)
    except Exception:
        return False
    return hashlib.sha256(raw).hexdigest() == EXPECTED_SHA


EXPECTED_SHA = ""  # filled from bench/expected.sha (pinned, versioned)


def main():
    global EXPECTED_SHA
    EXPECTED_SHA = open("bench/expected.sha").read().strip()
    keys = list(MODELS)
    arms = ["A", "B"]
    if len(sys.argv) > 1 and sys.argv[1] in MODELS:
        keys = [sys.argv[1]]
    if len(sys.argv) > 2 and sys.argv[2] in ("A", "B"):
        arms = [sys.argv[2]]
    for key in keys:
        model = MODELS[key]
        for arm in arms:
            t = run_arm_b(model) if arm == "B" else run_arm_a(model)
            row = {"model": key, "arm": arm, "tokens_in": t["tok_in"],
                   "tokens_out": t["tok_out"], "tool_calls": t["calls"],
                   "success": score(t["content"]),
                   "seconds": round(t["secs"], 2), "seed": SEED,
                   "temp": 0, "harness": HARNESS}
            with open(RESULTS, "a") as f:
                f.write(json.dumps(row) + "\n")
            print(row, flush=True)


if __name__ == "__main__":
    main()
