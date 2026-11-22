# bench v9 — l'INTAKE en circuit fermé.
# Phrase vague du humain -> /intent/card (le serveur choisit l'outil et
# pré-remplit) -> le modèle ne fait que RELAYER {run, args}. Le total et
# l'inventaire viennent du serveur. La donnée ne traverse jamais le modèle.
import sys, json, re, time
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
import httpx
from run8 import MODELS, chat, score8, JSON_RX
import task8

BASE = "https://mechacut.studio"
HUMAN = ("Donne-moi une liste propre de tous les montants, pourcentages, "
         "dates, urls et emails du rapport d'incident ci-dessous, avec le "
         "total des montants. " + task8.NOTE8)


def card():
    r = httpx.post(BASE + "/api/v1/intent/card",
                   json={"utterance": HUMAN}, timeout=60)
    r.raise_for_status()
    return r.json()


def arm_intake(model):
    t0 = time.time()
    c = card()
    # ce que le modèle voit : la fiche + une seule consigne de relais
    prompt = (
        "You are an agent. A tool card was built FOR you.\n"
        "CARD: " + json.dumps({
            "status": c["status"], "tool": c.get("tool"),
            "path": c.get("path"),
            "card": {k: v.get("value") for k, v in
                     (c.get("card") or {}).items()
                     if v["state"] == "filled"}},
            ensure_ascii=False)[:900] + "\n"
        "Reply with EXACTLY one JSON: {\"run\": \"<path from CARD>\", "
        "\"args\": {\"text\": \"$utterance\"}} and nothing else. "
        "$utterance is the human message; it is substituted for you.")
    text, tok = chat(model, [{"role": "user", "content": prompt}], n=300)
    row = {"arm": "intake", "model": model, "card_status": c["status"],
           "card_tool": c.get("tool"), "steps": 0, "tool": None,
           "tokens": tok, "keys": 0, "of": 6, "detail": None,
           "answer_from_server": False, "head": text[:160]}
    m = JSON_RX.search(text)
    if m:
        try:
            doc = json.loads(m.group(0))
        except Exception:
            doc = None
        if isinstance(doc, dict) and doc.get("run"):
            row["steps"] = 1
            row["tool"] = doc["run"]
            args = doc.get("args") or {}
            if isinstance(args.get("text"), str):
                args["text"] = HUMAN if "$utterance" in args["text"] \
                    else args["text"]
            r = httpx.post(BASE + doc["run"], json=args, timeout=60)
            if r.status_code == 200:
                d = r.json()
                inv = d.get("inventory")
                if isinstance(inv, dict):
                    cand = dict(inv)
                    cand["total_money"] = d.get("total_money")
                    n_ok, of, det = score8(cand)
                    row.update(keys=n_ok, of=of, detail=det,
                               answer_from_server=True)
    row["seconds"] = round(time.time() - t0, 1)
    return row


def arm_naked(model):
    # même humain, aucun serveur : le modèle doit tout faire (attendu 0.x)
    text, tok = chat(model, [{"role": "user", "content":
        "Donne-moi une liste propre de tous les montants, pourcentages, "
        "dates, urls et emails du rapport, avec le total des montants, "
        "en un seul JSON: {\"money\":[...],\"percent\":[...],\"date\":[...],"
        "\"url\":[...],\"email\":[...],\"total_money\":\"..\"}\n\n"
        + task8.NOTE8}], n=600)
    m = JSON_RX.search(text)
    ok = None
    if m:
        try:
            ok = score8(json.loads(m.group(0)))
        except Exception:
            ok = None
    return {"arm": "naked", "model": model, "tokens": tok,
            "keys": (ok[0] if ok else 0), "of": (ok[1] if ok else 6),
            "detail": (ok[2] if ok else None), "head": text[:120]}


if __name__ == "__main__":
    print("CARD:", json.dumps({k: card()[k] for k in
          ("status", "tool", "missing_required")}, ensure_ascii=False))
    sys.stdout.flush()
    for mk in (sys.argv[1:] or list(MODELS)):
        n = arm_naked(MODELS[mk])
        i = arm_intake(MODELS[mk])
        print(json.dumps({"model": mk, "naked": n, "intake": i},
                         ensure_ascii=False)[:700])
        sys.stdout.flush()
