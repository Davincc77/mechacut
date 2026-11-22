# bench v17 — l'économie de tokens (thèse de l'opérateur, 22-11) :
# « le déterminisme empêche les répétitions et remet la puissance de
# calcul là où elle doit être : réfléchir, pas répéter — sans toucher
# au modèle ».
#
# Mêmes marqueurs que v16 : mêmes 20 problèmes seedés (gen16, graine
# 2026), mêmes modèles gratuits locaux. Ce qui change : on COMPTE les
# tokens comme objet d'étude, et on donne au bras nu son arme
# légitime — le self-consistency (n=5, temp 0.7), la réponse «
# réessaie encore » du monde réel.
#
# Bras :
#   A  retry×5   : temp 0.7, 5 échantillons, majorité sur l'arrondi
#                  centésimal (déterministe : égalité de comptes →
#                  premier apparu). Tokens = la facture COMPLÈTE.
#   B  relay     : le protocole steps v14 ({"step": expression
#                  fermée} → le serveur calcule → {"value"} → …→
#                  {"answer"}), temp 0, 6 étapes max. Tokens =
#                  ce que LE MODÈLE paie ; le serveur est gratuit,
#                  ~0,2 s, et c'est écrit dans le FINDINGS.
#   (C  nu@0 simple shot : déjà facturé par v16 — lu depuis
#    results_v16_calibration.jsonl, pas re-joué : mêmes cellules,
#    mêmes graines, zéro drive.)
#
# PRÉDICTIONS ENREGISTRÉES AVANT LA PREMIÈRE CELLULE :
#   P1 sur les familles à chaîne (mix/partage), retry×5 NE converge
#      pas : succès < 30 % malgré 5× le budget — la mémoire ne sait
#      pas ce qu'elle ne sait pas (v16), le bruit n'apprend rien.
#   P2 relay ≥ 70 % de succès sur ces mêmes familles.
#   P3 tokens/coûts-par-juste : relay < retry×5 sur TOUTES les
#      familles, y compris celles que le nu réussit — parce que le
#      retry paie 5 fois pour douter pareil.
#   P4 le 8B ne rattrape pas le serveur par la taille : l'écart est
#      une frontière de FORME (v16), pas de capacité.
# Si une prédiction tombe, le FINDINGS dit laquelle et montre les
# lignes brutes — le banc est le juge.
import json
import re
import statistics
import sys
import time
from collections import Counter

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
import httpx
from gen16 import problems
from run12 import MODELS, BASE
from run14 import run_skill
from run16 import norm_num

OUT = "/Users/vincenzocirilli/Downloads/mechacut/bench/" \
      "results_v17_tokens.jsonl"

ASK = ("Solve this problem. Reply with EXACTLY one JSON object, "
       "nothing else:\n{\"answer\": \"<number>\"}\n\nProblem: <Q>")


def chat(model, msgs, temp=0.7, n=120):
    t0 = time.time()
    r = httpx.post("http://127.0.0.1:11434/api/chat", json={
        "model": model, "messages": msgs, "stream": False,
        "options": {"temperature": temp, "seed": 42 + len(msgs),
                    "num_ctx": 4096, "num_predict": n}}, timeout=180)
    d = r.json()
    return (d.get("message", {}).get("content", ""),
            d.get("prompt_eval_count", 0) + d.get("eval_count", 0),
            round(time.time() - t0, 2))


def run_retry(model, q):
    """5 échantillons temp 0.7, majorité centésimal, tie → premier
    apparu. Retourne (gagnant, tokens, secondes, votes)."""
    answers, toks, secs = [], 0, 0.0
    for _ in range(5):
        text, tok, sec = chat(model, [{"role": "user",
                                       "content": ASK.replace("<Q>", q)}])
        toks += tok
        secs += sec
        m = re.search(r"\{.*\}", text, re.S)
        got = None
        if m:
            try:
                got = norm_num(json.loads(m.group(0)).get("answer"))
            except Exception:
                got = None
        answers.append(None if got is None else
                       str(round(got, 2)))
    votes = Counter(a for a in answers if a is not None)
    winner = None
    if votes:
        best = max(votes.values())
        for a in answers:                       # premier apparu
            if a and votes[a] == best:
                winner = a
                break
    return winner, toks, secs, dict(votes)


if __name__ == "__main__":
    qs = problems()
    only = sys.argv[1:] or ["7b", "8b"]
    done = set()
    try:
        for l in open(OUT):
            r = json.loads(l)
            done.add((r["model"], r["i"], r["arm"]))
    except FileNotFoundError:
        pass
    print("déjà au brut:", len(done), "cellules — reprise", flush=True)
    with open(OUT, "a", encoding="utf-8") as fh:
        for mk in only:
            for t in qs:
                gold = str(round(float(t["gold"]), 2))
                # — bras A : retry×5
                if (mk, t["i"], "retry5") not in done:
                    win, toks, secs, votes = run_retry(MODELS[mk],
                                                       t["text"])
                    okA = win == gold
                    fh.write(json.dumps({"harness": "v17-tokens",
                                         "arm": "retry5", "model": mk,
                                         "i": t["i"],
                                         "family": t["family"],
                                         "ok": okA, "answer": win,
                                         "gold": gold, "votes": votes,
                                         "tokens": toks,
                                         "secs": secs}) + "\n")
                    fh.flush()
                    print("%-3s #%02d retry5 %s got=%s gold=%s tok=%d"
                          % (mk, t["i"], "✓" if okA else "✗", win,
                             gold, toks), flush=True)
                # — bras B : relay steps (protocole v14, temp 0)
                if (mk, t["i"], "relay") not in done:
                    steps, err, tokB, secB = run_skill(MODELS[mk],
                                                       t["text"])
                    ansB = steps[-1].get("answer") if steps else None
                    okB = (norm_num(ansB) is not None
                           and abs(norm_num(ansB)
                                   - float(t["gold"])) < .005)
                    fh.write(json.dumps({"harness": "v17-tokens",
                                         "arm": "relay", "model": mk,
                                         "i": t["i"],
                                         "family": t["family"],
                                         "ok": okB, "answer": ansB,
                                         "gold": gold, "err": err,
                                         "steps": len(steps),
                                         "tokens": tokB, "secs": secB,
                                         "trace": json.dumps(steps)[:300]
                                         }) + "\n")
                    fh.flush()
                    print("%-3s #%02d relay  %s got=%s tok=%d %s"
                          % (mk, t["i"], "✓" if okB else "✗", ansB,
                             tokB, err or ""), flush=True)
