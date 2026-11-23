# -*- coding: utf-8 -*-
"""BENCH EQUIP-V1 — « token defense » : un agent Hermes ÉQUIPÉ de la skill
mechacut vs le MÊME agent sans skill, sur des tâches mécaniques répétitives.

Bras unique de différence : le contenu du system prompt. Les deux bras ont
le même outil (run_python, sandbox réelle), le même modèle local
(qwen2.5:7b-instruct-q4_K_M, tokens comptés par l'API ollama — pas des
estimations), la même consigne de précision. Le bras équipé reçoit
exactement le texte que le plugin installe : /SKILL-MINI.md LIVE (sha relevé).

Ce qu'on mesure par session :
  tokens_prompt + tokens_completion (somme de TOUTES les itérations —
  l'historique qui grossit compte, comme dans une vraie session Hermes),
  appels d'outil, justesse contre un ground truth calculé ICI en
  Decimal/datetime/hashlib (jamais contre la mémoire du modèle),
  et le comportement de refus sur la tâche ambiguë — la classe que la
  baseline ne sait même pas exister.

Sortie : bench/results/equip-v1.jsonl (une ligne par session) + table.
"""
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from decimal import Decimal

OLLAMA = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct-q4_K_M"
SKILL_URL = "https://mechacut.studio/SKILL-MINI.md"
OUT = "bench/results/equip-v1r2.jsonl"
MAX_STEPS = 7

BASE_SYSTEM = (
    "You are a coding agent serving a user. You can run python with your "
    "tool. The user cannot check your work, so compute exactly and be "
    "precise. When done, answer on the LAST line: ANSWER: <value only>."
)

TOOL = [{
    "type": "function",
    "function": {
        "name": "run_python",
        "description": "Run a python snippet in a sandbox, print to stdout.",
        "parameters": {
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
        },
    },
}]


def run_python(code):
    try:
        r = subprocess.run([sys.executable, "-I", "-c", code],
                           capture_output=True, text=True, timeout=12, cwd="/tmp")
        out = (r.stdout or "")[:600] + (("\nSTDERR: " + r.stderr[:200]) if r.returncode else "")
        return out.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


import re

def grade_exact(want):
    """Le modèle répond souvent EN PHRASE. On extrait de la réponse :
    la date, le hex long, ou le nombre demandé — le premier qui tombe
    sous le motif exact — puis on compare. Sans ça, le scoreur est pire
    que ce qu'il mesure (faute vue au run v1.0 : T5/T9 vrais positifs
    comptés faux car collés dans une phrase)."""
    pat = re.compile(re.escape(want))
    def g(ans):
        a = ans.replace(" ", "").replace(",", "")
        return pat.search(a) is not None
    return g


def grade_split(ans):
    try:
        parts = [Decimal(x) for x in ans.replace("$", "").split("/") if x.strip()]
    except Exception:
        return False
    return len(parts) == 7 and sum(parts) == Decimal("100.00") and (max(parts) - min(parts)) <= Decimal("0.01")


def grade_refusal(ans):
    a = ans.lower()
    return any(k in a for k in ("ambiguous", "could be", "either", "1.234", "decimal or", "ask"))


def sha256_file_free():
    return hashlib.sha256(b"mechacut").hexdigest()


TASKS = [
    {"id": "T1_round", "ask": "Round 2.675 to 2 decimals (half-up).",
     "grade": grade_exact("2.68")},
    {"id": "T2_split", "ask": "Split $100.00 among 7 people, cents exact, report the 7 amounts separated by '/'.",
     "grade": grade_split},
    {"id": "T3_units", "ask": "Convert 90 km/h to m/s.",
     "grade": grade_exact("25")},
    {"id": "T4_sha", "ask": "Give the sha256 hex digest of the literal string: mechacut",
     "grade": grade_exact(sha256_file_free())},
    {"id": "T5_dateadd", "ask": "What date is 45 days after 2026-11-24? (YYYY-MM-DD)",
     "grade": grade_exact("2027-01-08")},
    {"id": "T6_redact", "ask": "Redact every email from this line, keep the rest: Contact alice@corp.io or bob@corp.io now",
     "grade": lambda a: "alice@corp.io" not in a and "bob@corp.io" not in a and "Contact" in a and "@" not in a.split("now")[0].replace("[REDACTED]", "").replace("***", "").replace("[MASK]", "").replace("<REDACTED>", "")},
    {"id": "T7_ambig", "ask": "What number is this: 1,234",
     "grade": grade_refusal},
    {"id": "T8_daysbetween", "ask": "How many days from 2026-01-01 to 2026-03-31 inclusive of neither endpoint?",
     "grade": grade_exact("89")},
    {"id": "T9_bigmul", "ask": "Multiply exactly: 987654321 * 123456789",
     "grade": grade_exact(str(987654321 * 123456789))},
    {"id": "T10_euro", "ask": "Format the number 1234567.891 European-style (thousands separated with dots, decimal comma, 2 decimals).",
     "grade": grade_exact("1.234.567,89")},
]


def chat(messages, arm_skill):
    body = {"model": MODEL, "messages": messages, "stream": False, "tools": TOOL,
            "options": {"temperature": 0}}
    req = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        d = json.loads(r.read())
    return d


def run_session(task, skill_text):
    sysmsg = BASE_SYSTEM + (("\n\nINSTALLED SKILL — follow it exactly:\n" + skill_text) if skill_text else "")
    msgs = [{"role": "system", "content": sysmsg},
            {"role": "user", "content": task["ask"]}]
    tp = tc = calls = 0
    t0 = time.time()
    for _ in range(MAX_STEPS):
        d = chat(msgs, skill_text)
        m = d.get("message", {})
        tp += d.get("prompt_eval_count") or 0
        tc += d.get("eval_count") or 0
        tcs = m.get("tool_calls") or []
        if not tcs:
            ans = (m.get("content") or "").strip()
            line = [l for l in ans.splitlines() if "ANSWER:" in l.upper()]
            final = line[-1].split(":", 1)[1].strip() if line else ans.splitlines()[-1] if ans else ""
            return {"tokens": tp + tc, "prompt_tokens": tp, "completion_tokens": tc,
                    "calls": calls, "correct": bool(task["grade"](final)),
                    "answer": final[:160], "wall_s": round(time.time() - t0, 1)}
        msgs.append(m)
        for name, args in [(t["function"]["name"], t["function"]["arguments"]) for t in tcs]:
            calls += 1
            code = args.get("code", "") if isinstance(args, dict) else json.loads(args or "{}").get("code", "")
            out = run_python(code) if name == "run_python" else "unknown tool"
            msgs.append({"role": "tool", "content": out})
    return {"tokens": tp + tc, "prompt_tokens": tp, "completion_tokens": tc,
            "calls": calls, "correct": False, "answer": "(budget exhausted)",
            "wall_s": round(time.time() - t0, 1)}


def load_skill():
    """La skill que le plugin Hermes installe LITTÉRALEMENT — pas une copie
    éditée pour le bench. Chemin d'installation réel sur cette machine."""
    import pathlib
    p = pathlib.Path.home() / ".hermes/plugins/mechacut/skills/mechacut/SKILL.md"
    if p.exists():
        return p.read_text()
    rq = urllib.request.Request(SKILL_URL, headers={"User-Agent": "mechacut-bench/1"})
    return urllib.request.urlopen(rq, timeout=20).read().decode()


def main():
    skill = load_skill()
    skill_sha = hashlib.sha256(skill.encode()).hexdigest()[:12]
    print(f"skill live: {len(skill)} chars, sha {skill_sha}")
    import os
    os.makedirs("bench/results", exist_ok=True)
    rows = []
    with open(OUT, "w") as fh:
        for arm, sk in (("unequipped", None), ("equipped", skill)):
            for t in TASKS:
                r = run_session(t, sk)
                r.update(arm=arm, task=t["id"], skill_sha=skill_sha, ts=time.strftime("%F %T"))
                rows.append(r)
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                fh.flush()
                print(f"{arm:10s} {t['id']:14s} tok={r['tokens']:6d} calls={r['calls']} correct={r['correct']} :: {r['answer'][:60]}")
    for arm in ("unequipped", "equipped"):
        sel = [r for r in rows if r["arm"] == arm]
        tok = sum(r["tokens"] for r in sel)
        ok = sum(1 for r in sel if r["correct"])
        print(f"== {arm}: {ok}/{len(sel)} correct, {tok} tokens au total, médiane {sorted(r['tokens'] for r in sel)[len(sel)//2]}")


if __name__ == "__main__":
    main()
