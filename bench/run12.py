# bench v12 — « le zéro qui compte plus vite que les autres »
# Un petit modèle gratuit (0.5B/1.5B) ne SAIT PAS faire ces dix calculs.
# Trois bras : NU (il invente), CODE (il écrit du python qu'un sandbox
# exécute — le vrai rival des agents), RELAIS (il recopie l'expression,
# la machine calcule). Métrique : secondes + tokens PAR RÉPONSE JUSTE
# — une réponse fausse a une espérance de temps infinie, et c'est là
# que « plus vite » devient honnête.
# Golds = Fraction exacte (oracle indépendant de Decimal ET du produit).
import json
import re
import subprocess
import sys
import time
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
import httpx

BASE = "https://mechacut.studio"
OLLAMA = "http://127.0.0.1:11434/api/chat"
MODELS = {"0.5b": "qwen2.5:0.5b-instruct", "1.5b": "qwen2.5:1.5b-instruct",
          "7b": "qwen2.5:7b-instruct-q4_K_M", "8b": "llama3.1:8b"}


def rhu(frac, n):
    d = Decimal(frac.numerator) / Decimal(frac.denominator)
    return str(d.quantize(Decimal(1).scaleb(-n) if n > 0 else Decimal(1),
                          rounding=ROUND_HALF_UP))


def _p(expr, digits):
    """gold par Fraction sur la grammaire fermée (cas utilisés)."""
    e = expr
    e = re.sub(r"(\d+\.\d+|\d+)", lambda m: "F('%s')" % m.group(1), e)
    v = eval(e, {"F": F, "__builtins__": {}})  # literals → Fraction only
    return rhu(v, digits)


TASKS12 = [
 {"id": "mul", "expr": "7834*9217", "digits": 0},
 {"id": "div_round", "expr": "1000/17", "digits": 4},
 {"id": "chain_pct", "expr": "2349.77*1.07*1.04*0.89", "digits": 2},
 {"id": "inverse_pct", "expr": "248.40*100/15", "digits": 2},
 {"id": "rule_three", "expr": "34.2*8.75/7.5", "digits": 3},
 {"id": "speed", "expr": "217.8/(2+47/60)", "digits": 2},
 {"id": "modulo", "expr": "987654321-7919*((987654321//7919))",
  "digits": 0, "gold_override": None},
 {"id": "compound", "expr": "1234.56*1.00417**19", "digits": 2},
 {"id": "unit_price", "expr": "17.83/24", "digits": 3},
 {"id": "float_trap", "expr": "0.1+0.2", "digits": 1},
]
for t in TASKS12:
    if t["id"] == "modulo":  # Fraction n'a pas // ; gold par Python int
        t["gold"] = str(987654321 % 7919)
    elif t["id"] == "float_trap":
        t["gold"] = "0.3"
    else:
        t["gold"] = _p(t["expr"], t["digits"])

NAKED = ("Compute this by hand and answer with EXACTLY one line "
         "containing only the number, rounded to {d} decimal place(s)"
         "{ds}: {e}")
RELAY_PROMPT = (
    "You are an agent. Routes:\n"
    "- /api/v1/math/calc — exact Decimal calculator, args "
    "{{expr, digits}}\n\nCompute this and answer with EXACTLY one "
    'JSON line {{"run": "<path>", "args": {{"expr": "...", '
    '"digits": N}}}}: {e}\n'
    "Copy the expression exactly; do not evaluate it yourself.")
CODE_PROMPT = (
    "Write ONLY a one-line python3 expression (no markdown, no print, "
    "no float() calls) that computes {e} rounded to {d} decimals using "
    "round(..., {d}). Output ONLY the expression.")


def chat(model, prompt, n=400):
    t0 = time.time()
    r = httpx.post(OLLAMA, json={
        "model": model, "stream": False,
        "options": {"temperature": 0, "seed": 42, "num_ctx": 8192,
                    "num_predict": n},
        "messages": [{"role": "user", "content": prompt}]}, timeout=600)
    d = r.json()
    return (d.get("message", {}).get("content", ""),
            d.get("prompt_eval_count", 0) + d.get("eval_count", 0),
            round(time.time() - t0, 2))


def extract_num(text):
    cands = re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    return cands[-1] if cands else None


def norm_num(x, d):
    if x is None:
        return None
    try:
        dd = Decimal(x)
    except Exception:
        return None
    q = Decimal(1).scaleb(-d) if d > 0 else Decimal(1)
    return str(dd.quantize(q, rounding=ROUND_HALF_UP))


def run_arm(model, t, arm):
    e, d, gold = t["expr"], t["digits"], t["gold"]
    ds = "" if d else " (integer)"
    if arm == "naked":
        text, tok, sec = chat(model, NAKED.format(e=e, d=d, ds=ds))
        got = norm_num(extract_num(text), d)
        return {"ok": got == gold, "got": got, "gold": gold,
                "tokens": tok, "secs": sec, "head": text[:120].replace("\n", " ")}
    if arm == "code":
        text, tok1, sec1 = chat(model, CODE_PROMPT.format(e=e, d=d))
        expr = text.strip().strip("`").splitlines()[-1] if text.strip() else ""
        out, viol = "", None
        # PORTIQUE : on n'exécute le texte d'un modèle qu'if ne contient
        # QUE chiffres, opérateurs, parenthèses, virgules, points et le
        # mot round. Toute lettre hors round = hors contrat → ✗ mesuré,
        # rien n'est lancé.
        if not re.fullmatch(r"[0-9+\-*/%.,()\s]*"
                            r"(round[0-9+\-*/%.,()\s]*)*", expr):
            viol = "out_of_contract"
        elif "__" in expr or "'" in expr or '"' in expr:
            viol = "out_of_contract"
        else:
            try:
                cp = subprocess.run(
                    [sys.executable, "-I", "-S", "-c",
                     "import sys; print(eval(sys.argv[1], "
                     "{'__builtins__': {}}, {'round': round}))", expr],
                    capture_output=True, text=True, timeout=8)
                out = cp.stdout.strip()
            except Exception:
                out = ""
        got = norm_num(re.sub(r"[\[\]()\s]", "", out).split(",")[-1]
                       if out else None, d)
        return {"ok": got == gold, "got": got, "gold": gold,
                "tokens": tok1, "secs": sec1, "code": expr[:120],
                "viol": viol, "head": out[:60]}
    # relay
    text, tok, sec = chat(model, RELAY_PROMPT.format(e=e, d=d))
    m = re.search(r"\{.*\}", text, re.S)
    got, err = None, None
    if m:
        try:
            body = json.loads(m.group(0))
            r = httpx.post(BASE + body.get("run", "/nope"),
                           json={"expr": body["args"]["expr"],
                                 "digits": body["args"].get("digits", d)},
                           timeout=30)
            if r.status_code == 200:
                got = norm_num(r.json()["value"], d)
            else:
                err = "srv%d" % r.status_code
        except Exception as ex:
            err = str(ex)[:60]
    return {"ok": got == gold, "got": got, "gold": gold, "tokens": tok,
            "secs": sec, "err": err, "head": text[:120].replace("\n", " ")}


if __name__ == "__main__":
    out_path = ("/Users/vincenzocirilli/Downloads/mechacut/bench/"
                "results_v12.jsonl")
    only = sys.argv[1:] or list(MODELS)
    with open(out_path, "a", encoding="utf-8") as fh:
        for mk in only:
            for t in TASKS12:
                for arm in ("naked", "code", "relay"):
                    r = run_arm(MODELS[mk], t, arm)
                    row = {"harness": "v12", "suite": "0.74.0",
                           "model": mk, "task": t["id"], "arm": arm,
                           **r}
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    fh.flush()
                    print("%-4s %-11s %-6s %s got=%s gold=%s tok=%s "
                          "%.1fs" % (mk, t["id"], arm,
                                     "✓" if r["ok"] else "✗", r["got"],
                                     r["gold"], r["tokens"], r["secs"]),
                          flush=True)
