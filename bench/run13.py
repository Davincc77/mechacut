# bench v13 — GSM8K RÉEL (questions humaines publiées, MIT, golds
# "####" des auteurs — personne ne peut nous accuser de tâche sur
# mesure). Subset seedé et publié : reproductible par n'importe qui.
# Même thèse que v12, sur le banc d'essai de l'industrie : le calcul
# n'est PAS le modèle — délégué, il devient juste.
#
# Trois bras :
#   naked — le modèle répond, on extrait le dernier nombre
#   code  — le modèle écrit du python ; AST-portique LOCAL (aucun
#           import/attribut/ouverture ; seuls print/range/int/float/
#           round/abs/enums) puis exécution subprocess isolée
#   relay — le modèle ÉNUMÈRE les étapes de calcul en expressions
#           fermées ; math/calc les evaluate ; la dernière valeur est
#           la réponse. Comprendre reste du modèle ; compter est du
#           serveur — la séparation est le résultat publié.
import ast
import json
import random
import re
import subprocess
import sys
import time
from decimal import Decimal

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
import httpx
from run12 import MODELS, chat, BASE

SEED = 1301
N = 20
OUT = "/Users/vincenzocirilli/Downloads/mechacut/bench/" \
      "results_v13_gsm8k.jsonl"


def load_subset():
    rows = [json.loads(l) for l in open(
        "/Users/vincenzocirilli/Downloads/mechacut/bench/data/"
        "gsm8k_test.jsonl")]
    idx = sorted(random.Random(SEED).sample(range(len(rows)), N))
    out = []
    for i in idx:
        q = rows[i]
        gold = q["answer"].split("####")[-1].strip().replace(",", "")
        out.append({"i": i, "q": q["question"], "gold": gold})
    return out


def norm_int(x):
    if x is None:
        return None
    try:
        d = Decimal(str(x).replace(",", "").strip())
    except Exception:
        return None
    return str(int(d)) if d == d.to_integral_value() else str(d)


ALLOWED_CALLS = {"print", "range", "int", "float", "round", "abs",
                 "len", "sum", "max", "min", "enumerate"}
ALLOWED_NODES = (ast.Module, ast.Expr, ast.Assign, ast.AugAssign,
                 ast.For, ast.While, ast.If, ast.BinOp, ast.UnaryOp,
                 ast.Compare, ast.Call, ast.Name, ast.Load, ast.Store,
                 ast.Constant, ast.List, ast.Tuple, ast.Subscript,
                 ast.Slice, ast.arguments, ast.arg,
                 # opérateurs et contexte — ce sont des NOEUDS aussi
                 ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
                 ast.Mod, ast.Pow, ast.USub, ast.UAdd, ast.UAdd,
                 ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
                 ast.And, ast.Or, ast.Not, ast.Break, ast.Continue,
                 ast.Pass)


def code_gate(src):
    """Refus NOMMÉ de tout ce qui sort du contrat arithmétique."""
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return "syntax:%s" % e.msg
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            return "node:%s" % type(node).__name__
        if isinstance(node, ast.Attribute):
            return "attribute_access"
        if isinstance(node, ast.Call) and isinstance(node.func,
                                                     ast.Name):
            if node.func.id not in ALLOWED_CALLS:
                return "call:%s" % node.func.id
    return None


def run_code(src):
    g = code_gate(src)
    if g:
        return None, g
    try:
        cp = subprocess.run(
            [sys.executable, "-I", "-S", "-c",
             "import sys\n" + src],
             capture_output=True, text=True, timeout=8)
        return cp.stdout.strip().splitlines()[-1] if \
            cp.stdout.strip() else None, None
    except Exception as e:
        return None, "exec:%s" % type(e).__name__


def last_num(text):
    c = re.findall(r"-?\d[\d,]*(?:\.\d+)?", text.replace("\n", " "))
    return c[-1] if c else None


def arm_naked(m, t):
    p = ("Solve this grade-school math problem. Reason briefly, then "
         "end with EXACTLY one line: Answer: <number>\n\n" + t["q"])
    text, tok, sec = chat(m, p, n=700)
    got = norm_int(last_num(re.sub(r"^.*Answer:\s*", "",
                                   text.strip().splitlines()[-1]
                                   if "Answer" in text else text)
                            .strip() if "Answer" in text else
                            text))
    return got, {"tokens": tok, "secs": sec, "head":
                 text[-90:].replace("\n", " ")}


def arm_code(m, t):
    p = ("Write ONLY a python3 program (no markdown) that prints the "
         "numeric answer to this problem. Plain arithmetic and loops "
         "only — no imports, no strings printing the answer.\n\n"
         + t["q"])
    text, tok, sec = chat(m, p, n=700)
    src = re.sub(r"^```[a-z]*|```$", "", text.strip(),
                 flags=re.M).strip()
    out, viol = run_code(src)
    return norm_int(out), {"tokens": tok, "secs": sec, "viol": viol,
                           "head": src[:90].replace("\n", " ")}


def arm_relay(m, t):
    p = ("Do NOT compute. List the arithmetic steps as a JSON array "
         'of plain expression strings (digits, + - * / ( ) only), '
         "in order; the last expression yields the answer.\n"
         'Reply ONLY: {"steps": ["...", "..."]}\n\n' + t["q"])
    text, tok, sec = chat(m, p, n=500)
    mm = re.search(r"\{.*\}", text, re.S)
    vals, err = [], None
    if mm:
        try:
            steps = json.loads(mm.group(0)).get("steps", [])
            for e in steps[:12]:
                if not re.fullmatch(r"[0-9+\-*/().\s]+", str(e)):
                    err = "step_not_closed:%s" % str(e)[:30]
                    break
                r = httpx.post(BASE + "/api/v1/math/calc",
                               json={"expr": str(e)}, timeout=30)
                if r.status_code != 200:
                    err = "srv%s" % r.status_code
                    break
                vals.append(r.json()["value"])
        except Exception as ex:
            err = "parse:%s" % str(ex)[:40]
    else:
        err = "no_json"
    return norm_int(vals[-1] if vals else None), {
        "tokens": tok, "secs": sec, "steps": len(vals), "err": err,
        "head": text[:90].replace("\n", " ")}


if __name__ == "__main__":
    subset = load_subset()
    only = sys.argv[1:] or list(MODELS)
    with open(OUT, "a", encoding="utf-8") as fh:
        for mk in only:
            for t in subset:
                for name, fn in (("naked", arm_naked),
                                 ("code", arm_code),
                                 ("relay", arm_relay)):
                    got, meta = fn(MODELS[mk], t)
                    ok = got == norm_int(t["gold"])
                    row = {"harness": "v13-gsm8k", "seed": SEED,
                           "idx": t["i"], "model": mk, "arm": name,
                           "ok": ok, "got": got, "gold": t["gold"],
                           "license": "GSM8K MIT (c) 2021 OpenAI",
                           **meta}
                    fh.write(json.dumps(row, ensure_ascii=False)
                             + "\n")
                    fh.flush()
                    print("%-4s #%4d %-6s %s got=%s gold=%s"
                          % (mk, t["i"], name, "✓" if ok else "✗",
                             got, t["gold"]), flush=True)
