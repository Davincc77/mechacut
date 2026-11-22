# bench v8 — bras A (nu) vs bras B (1 choix de recette, LIVE mechacut.studio)
import sys, json, re, time
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
import task8
from decimal import Decimal, InvalidOperation
import httpx
import subprocess

BASE = "https://mechacut.studio"
MODELS = {"0.5b": "qwen2.5:0.5b-instruct",
          "1.5b": "qwen2.5:1.5b-instruct",
          "7b": "qwen2.5:7b-instruct"}
OLLAMA = "/usr/local/bin/ollama"  # sinon 'ollama' au PATH
import shutil
if not shutil.which(OLLAMA):
    OLLAMA = shutil.which("ollama") or "ollama"


def chat(model, messages, n=900):
    payload = {"model": model, "messages": messages, "stream": False,
               "options": {"temperature": 0, "seed": 42,
                           "num_predict": n}}
    out = subprocess.run([OLLAMA, "run", model, "-"],
                         input=json.dumps(messages[0]["content"]),
                         capture_output=True, text=True, timeout=300)
    # via API HTTP plutôt que CLI pour les compteurs :
    r = httpx.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=300)
    d = r.json()
    return d.get("message", {}).get("content", ""), \
        d.get("prompt_eval_count", 0) + d.get("eval_count", 0)


def _sortkey(x):
    try:
        return (0, Decimal(x))
    except (InvalidOperation, ValueError):
        return (1, str(x))


def norm_bucket(vals):
    out = []
    for v in (vals or []):
        t = str(v).strip().replace("$", "").replace(",", "").rstrip("%")
        try:
            d = Decimal(t)
            out.append(format(d, "f") if "." in t else t)
        except (InvalidOperation, ValueError):
            out.append(t.lower())
    return sorted(set(out), key=_sortkey)


def score8(doc):
    """doc = dict candidat ; renvoie (n_ok, total, détail)."""
    exp = task8.expected8()
    det = {}
    for k, want in exp.items():
        got = doc.get(k)
        if k == "total_money":
            ok = (got is not None and
                  str(got).replace("$", "").replace(",", "").strip() == want)
        else:
            ok = norm_bucket(got) == norm_bucket(want)
        det[k] = ok
    return sum(det.values()), len(det), det


JSON_RX = re.compile(r"\{.*\}", re.S)


def arm_a(model):
    t0 = time.time()
    text, tok = chat(model, [{"role": "user", "content": task8.ARM_A_TASK}])
    m = JSON_RX.search(text)
    ok = None
    if m:
        try:
            ok = score8(json.loads(m.group(0)))
        except Exception:
            ok = None
    return {"arm": "A", "parsed": ok is not None,
            "keys": (ok[0] if ok else 0), "of": (ok[1] if ok else 6),
            "detail": (ok[2] if ok else None), "tokens": tok,
            "seconds": round(time.time() - t0, 1), "head": text[:150]}


TOOL_PATH = {"recipe_facts": "/api/v1/recipe/facts",
             "extract_facts": "/api/v1/extract/facts",
             "batch": "/api/v1/batch",
             "json_query": "/api/v1/json/query"}


def gen_prefixed(model, prompt, prefix):
    """v8.1 : ouverture forcée (leçon v7) — le modèle complète, n'invente pas
    la structure du protocole."""
    payload = {"model": model, "prompt": prompt, "raw": True,
               "stream": False,
               "options": {"temperature": 0, "seed": 42,
                           "num_predict": 700}}
    r = httpx.post("http://127.0.0.1:11434/api/generate",
                   json=payload, timeout=300)
    d = r.json()
    text = prefix + d.get("response", "")
    tok = d.get("prompt_eval_count", 0) + d.get("eval_count", 0)
    return text, tok


def tolerant_steps(text):
    m = JSON_RX.search(text)
    if not m:
        return None
    for cand in (m.group(0), text + "]}"):
        try:
            doc = json.loads(cand)
            if isinstance(doc, dict) and "steps" in doc:
                steps = doc["steps"]
                if isinstance(steps, list) and steps:
                    return doc
        except Exception:
            continue
    return None


def arm_b(model):
    t0 = time.time()
    # v8.2 (leçon v7, méthode v6) : le protocole est JOUÉ une fois par le
    # harness sur un outil NEUTRE (extract_facts) avec VRAIE observation live.
    # Il reste au modèle de choisir l'outil final — la donnée ne le traverse
    # jamais. C'est exactement le contrat de la suite.
    demo = json.dumps({"steps": [{"tool": "extract_facts",
                                  "args": {"text": task8.NOTE8,
                                           "group": "kind",
                                           "context_chars": 0}}]},
                      ensure_ascii=False)
    obs = httpx.post(BASE + "/api/v1/extract/facts",
                     json={"text": task8.NOTE8, "group": "kind",
                           "context_chars": 0}, timeout=60).text
    messages = [{"role": "user", "content": task8.ARM_B_TASK},
                {"role": "assistant", "content": demo},
                {"role": "user", "content": obs}]
    text, tok = chat(model, messages)
    row = {"arm": "B", "harness": "v8.2", "steps": 0, "tool": None,
           "tokens": tok, "keys": 0, "of": 6, "detail": None,
           "answer_from_server": False, "head": text[:120]}
    doc = None
    m = JSON_RX.search(text)
    if m:
        try:
            doc = json.loads(m.group(0))
        except Exception:
            doc = None
    if isinstance(doc, dict) and doc.get("steps"):
        steps = doc["steps"]
        row["steps"] = len(steps)
        for st in steps[:3]:
            if not isinstance(st, dict):
                continue
            tool = st.get("tool")
            args = st.get("args") or {}
            if isinstance(args.get("text"), str):
                args["text"] = args["text"].replace("$note", task8.NOTE8)
            path = TOOL_PATH.get(tool)
            if not path:
                continue
            r = httpx.post(BASE + path, json=args, timeout=60)
            row["tool"] = tool
            if r.status_code != 200:
                continue
            d = r.json()
            inv = d.get("inventory")
            if isinstance(inv, dict):
                cand = dict(inv)
                cand["total_money"] = d.get("total_money")
                n_ok, of, det = score8(cand)
                row.update(keys=n_ok, of=of, detail=det,
                           answer_from_server=True)
    elif isinstance(doc, dict):
        # le modèle a répondu directement depuis l'observation —
        # on score quand même (honnête : c'est du rappel, pas du calcul)
        n_ok, of, det = score8(doc)
        row.update(keys=n_ok, of=of, detail=det)
    row["seconds"] = round(time.time() - t0, 1)
    return row


if __name__ == "__main__":
    which = sys.argv[1:] or list(MODELS)
    for mk in which:
        a = arm_a(MODELS[mk])
        b = arm_b(MODELS[mk])
        print(json.dumps({"model": mk, "harness": "v8", "A": a, "B": b},
                         ensure_ascii=False)[:900])
        sys.stdout.flush()
