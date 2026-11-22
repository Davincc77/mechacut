# -*- coding: utf-8 -*-
"""bench V24 — TRENTE JOURS DE LFM3 : le modèle qui sait lire sait-il
se répéter ? (22-11-2026)

V23 vient de publier : un 1,7 B entraîné pour les agents résout nos
chaînes À NU 7/7. L'objection qui tue alors le produit entier :
« garde ton serveur, mon modèle sait, il n'a pas besoin d'être
garanti ». Ce banc est la réponse mesurée — ou son tombeau, statué
avant la première cellule.

Instrument IMPORTÉ de v19, intact : le même dirty.csv, la même SPEC
gelée à six règles, le même gold ÉCRIT À LA MAIN
(fixtures_v19/gold.csv), le même validateur de FORME (le modèle ne
voit JAMAIS le gold), le même canon. Seuls changements : le modèle
(liquid/lfm-3-1.7b via Nous, transport v23) et le régime : temp 0,7 —
le régime RÉEL des agents, déjà publié comme tel en v19.

Bras :
  N nu     : 30 jours, un appel par jour.
  R retry  : ≤3 appels/jour, stop dès que FORMAT_CHECK passe.
  M machine: la spec gelée en code (importée) — doit rester 30/30
             au même sha : c'est le claim à battre, pas une promesse.

PRÉDICTIONS GELÉES AVANT LA PREMIÈRE CELLULE (le scoreur statue) :
  B1 dérive : N produit ≥2 sorties canoniques distinctes en 30 jours.
     Si EXACTEMENT UNE sortie distincte ET juste ≥28/30 : le pitch
     « jamais deux fois pareil » MEURT sur cette classe — publier.
  B2 justesse : jours justes(N) ≤ 27/30 (le seuil de v19, même
     instrument).
  B3 retry : jours justes(R) < 30/30 — le re-tirage à 0,7 ne
     converge pas en tâche de conformité (loi v15 G2, hors famille ?)
     ET tokens(R) ≥ 1,5 × tokens(N).
  B4 machine : 1 sha distinct, 30/30, $0 — par construction, revérifié.
  B5 facture : la course entière ≤ $0,50 aux prix gelés.
Zéro re-pilotage. Si B1 tombe, FINDINGS-V24 publie la réfutation.
"""
import hashlib
import json
import sys
import time

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")

import urllib.error
import urllib.request

from run19 import DIRTY, GOLD, SPEC, FORMAT_CHECK, canon, machine, \
    strip_fences
from run22 import key
from run23 import PRICE_IN, PRICE_OUT

API = "https://inference-api.nousresearch.com/v1/chat/completions"
MODEL = "liquid/lfm-3-1.7b"
OUT = "/Users/vincenzocirilli/Downloads/mechacut/bench/" \
      "results_v24_lfm3_30days.jsonl"
DAYS = 30
GOLD_C = canon(GOLD)
GOLD_SHA = hashlib.sha256(GOLD_C.encode()).hexdigest()


def api7(temp=0.7):
    """Transport v23 (retry transitoire), temperature 0,7 — régime
    réel gelé dans l'en-tête. Amendement 22-11 (après 28 jours N,
    publié dans le commit, sémantique des cellules déjà jouées
    inchangée) : le contenu seul est LA RÉPONSE — ce que l'agent de
    prod reçoit. finish_reason et la longueur du reasoning sont
    enregistrés : le SILENCE (content vide, thinking avalé par la
    limite 8192) devient une classe mesurée, pas un bug de lecture."""
    def call():
        body = {"model": MODEL,
                "messages": [{"role": "user", "content": SPEC}],
                "stream": False, "temperature": temp}
        req = urllib.request.Request(
            API, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + key()})
        return json.loads(urllib.request.urlopen(req, timeout=240).read())
    tries, wait = 0, 15
    while True:
        try:
            r = call()
            break
        except urllib.error.HTTPError as e:
            e.read()
            tries += 1
            if e.code not in (404, 429, 500, 502, 503) or tries > 8:
                raise
            time.sleep(wait)
            wait = min(wait * 2, 120)
    u = r.get("usage", {})
    m = r["choices"][0]["message"]
    return (m.get("content") or "",
            int(u.get("prompt_tokens", 0)),
            int(u.get("completion_tokens", 0)),
            r["choices"][0].get("finish_reason"),
            len(m.get("reasoning") or ""))


def judge(text):
    out = canon(strip_fences(text))
    ok = out == GOLD_C
    shape = bool(FORMAT_CHECK.match(out))
    sha = hashlib.sha256(out.encode()).hexdigest()[:16]
    return out, ok, shape, sha


def cell(arm, day, fh):
    t0 = time.time()
    if arm == "M":
        out = canon(machine(DIRTY))
        row = {"harness": "v24-lfm3-30days", "arm": "M", "model":
               "machine", "day": day, "ok": out == GOLD_C,
               "shape": True, "sha": hashlib.sha256(
                   out.encode()).hexdigest()[:16],
               "tok_in": 0, "tok_out": 0, "usd": 0.0, "err": None,
               "secs": round(time.time() - t0, 2)}
        fh.write(json.dumps(row) + "\n")
        fh.flush()
        return row
    calls = 1 if arm == "N" else 0
    toks_in = toks_out = 0
    out = ok = shape = False
    sha = ""
    text = ""
    fin = None
    rs_l = 0
    budget = 1 if arm == "N" else 3
    for _ in range(budget):
        text, ti, to, fin, rs_l = api7()
        calls += 1
        toks_in += ti
        toks_out += to
        out, ok, shape, sha = judge(text)
        if arm == "N":
            break
        if shape:
            break
    usd = (toks_in * PRICE_IN + toks_out * PRICE_OUT) / 1e6
    err = None
    if not ok:
        if not (text or "").strip():
            err = "silence"
        elif not shape:
            err = "forme"
        else:
            err = "FAUX"
    row = {"harness": "v24-lfm3-30days", "arm": arm, "model": "lfm3",
           "day": day, "ok": bool(ok), "shape": bool(shape),
           "sha": sha, "tok_in": toks_in, "tok_out": toks_out,
           "usd": round(usd, 6), "calls": calls,
           "finish": fin, "reasoning_chars": rs_l, "err": err,
           "secs": round(time.time() - t0, 2)}
    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    fh.flush()
    return row


if __name__ == "__main__":
    m_out = canon(machine(DIRTY))
    if m_out != GOLD_C:
        sys.exit("GATE v19 : machine != gold écrit à la main — "
                 "l'instrument a bougé, ne pas courir.")
    print("gate : machine == gold (instrument v19 intact) ✓",
          flush=True)
    arms = sys.argv[1:] or ["M", "N", "R"]
    done = set()
    try:
        for l in open(OUT):
            r = json.loads(l)
            done.add((r["arm"], r["day"]))
    except FileNotFoundError:
        pass
    print("déjà faites:", len(done), "/ 90", flush=True)
    with open(OUT, "a", encoding="utf-8") as fh:
        for arm in arms:
            for day in range(DAYS):
                if (arm, day) in done:
                    continue
                row = cell(arm, day, fh)
                print("%s j%02d %s sha=%s %s" % (
                    arm, day, "✓" if row["ok"] else "✗",
                    row["sha"], row["err"] or ""), flush=True)
                if arm != "M":
                    time.sleep(1.0)
