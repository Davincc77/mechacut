# -*- coding: utf-8 -*-
"""bench V23 — LA LOI TIEN-ELLE HORS DE LA FAMILLE ? (lfm3-1.7b)

Douze bancs, un seul plafond publié — « le 0.5B ne se sauve par
aucun bras » — mais TOUS nos nains sont de la famille Qwen (plus
llama pour la taille). LFM3-1.7B (Liquid AI, 6 nov. 2026) est le
contre-exemple venu d'ailleurs : architecture tri-hybride (convolu-
tions + attention fenêtrée), IFStruct 93,7 revendiqué, post-entraîné
pour le tool calling, et officiellement « not recommended for complex
reasoning ». Un modèle vendu pour la FORME, pas pour la lecture :
c'est NOUS, en poids plume. S'il obéit aux mêmes lois que nos Qwen,
la frontière de FORME cesse d'être une habitude de laboratoire.

Instrument figé : les MÊMES 20 problèmes gen16 (graine 2026, identité
38df94d7), les MÊMES bras que v20. Modèle via Nous (inference-api,
prix GELÉS depuis /v1/models le 22-11 : in $0,08/M, out $0,20/M).
Serveur = le code de PROD lui-même dans TestClient : même grammaire
fermée, même Decimal, zéro réseau, zéro rate-limit (précédent : les
tests bundle ; la limite 30/min avait foudroyé 4 cellules de v20).
Temp 0 demandé ; rejet temp → retry provider-default (règle v22).
Le verrou est IMPORTÉ de run20 (lock_verdict/names_for/refus) : pas
de copie, pas de dérive — le garde mesuré est le garde vendu.

Bras (20 cellules chacun) :
  N nu      : un coup, {"answer"}.
  S relais  : protocole v14 — {"step": expression fermée}, le serveur
              calcule et renvoie {"value"}, {"answer"} pour finir.
  L verrou  : S + écho "names" + réponse exigeant {"answer","target"}
              + refus nommés VOCAB/MISMATCH/CIBLE + réparation ×1.

PRÉDICTIONS GELÉES AVANT LA PREMIÈRE CELLULE (le scoreur statue) :
  P1 le mur suit la TAILLE, pas la famille : N ≤ 3/7 en chaîne
     (mix+partage). Si N ≥ 5/7 : le plafond « les petits ne lisent
     pas » est une habitude Qwen — publier la réécriture du pitch.
  P2 la délégation tient hors-famille : S ≥ N + 2 en chaîne.
  P3 le verrou tient hors-famille : L ≥ S au total ET au moins les
     2/3 des « à côté » de S convertis (s'il y en a ≥ 1).
  P4 leur promesse de FORME est vraie : ruptures de PROTOCOLE en
     L ≤ 1/20 — un modèle post-trained tool-calling ne décroche pas
     du gabarit. Sinon : le gabarit n'est pas leur terrain non plus.
  P5 coût : la facture totale du banc ≤ $0,50 ; le $ par réponse
     juste du bras L est publié (pas de prédiction, un chiffre).
Si une prédiction tombe, FINDINGS-V23 la nomme avec les lignes.
"""
import json
import re
import sys
import time

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")

from fastapi.testclient import TestClient

import main as prod_app                  # noqa: E402
from gen16 import problems               # noqa: E402
from run20 import SKILL_L, ERR_L, lock_verdict, names_for, refusal_text  # noqa: E402
from run14 import SKILL                  # noqa: E402
from run22 import key, norm_num          # noqa: E402

import urllib.error
import urllib.request

API = "https://inference-api.nousresearch.com/v1/chat/completions"
MODEL = "liquid/lfm3-1.7b"
PRICE_IN, PRICE_OUT = 0.08, 0.20          # $/M, gelés 22-11 (/v1/models)
OUT = "/Users/vincenzocirilli/Downloads/mechacut/bench/" \
      "results_v23_lfm3.jsonl"
CLIENT = TestClient(prod_app.app)

P_NUDE = ('Solve this. Reply with EXACTLY one JSON object:\n'
          '{"answer": "<number>"}\n\nProblem: ')


def api(msgs):
    """Même règle que v22 : temp 0 d'abord ; si l'API rejette temp,
    UN seul retry aux paramètres du fournisseur, marqué. Plus : la
    route LFM3 est instable (le scan lui-même dit « back on our
    list » — premier ping a fait un 404 froid). Retry transitoire
    404/429/5xx : 3 tentatives, 10 s puis 20 s — résilience infra,
    gelée avant la première cellule, pas une prédiction."""
    def call(temp):
        body = {"model": MODEL, "messages": msgs, "stream": False}
        if temp:
            body["temperature"] = 0
        req = urllib.request.Request(
            API, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + key()})
        return json.loads(urllib.request.urlopen(req, timeout=180).read())
    mark = "0"
    tries, wait = 0, 15
    while True:
        try:
            r = call(True)
            break
        except urllib.error.HTTPError as e:
            txt = e.read().decode(errors="replace")
            if "temperature" in txt.lower():
                mark = "provider-default"
                r = call(False)
                break
            tries += 1
            if e.code not in (404, 429, 500, 502, 503) or tries > 6:
                raise
            time.sleep(wait)
            wait = min(wait * 2, 75)
    u = r.get("usage", {})
    return (r["choices"][0]["message"]["content"] or "",
            int(u.get("prompt_tokens", 0)),
            int(u.get("completion_tokens", 0)), mark)


def jobj(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def calc(expr):
    """Le serveur de prod, en process — grammaire fermée, Decimal."""
    r = CLIENT.post("/api/v1/math/calc", json={"expr": expr})
    if r.status_code != 200:
        return None, r.json()
    return r.json()["value"], None


def run_nude(t):
    text, pin, pout, mark = api([{"role": "user",
                                  "content": P_NUDE + t["text"]}])
    o = jobj(text)
    got = norm_num(o.get("answer")) if isinstance(o, dict) else None
    ok = got is not None and abs(got - float(t["gold"])) < 0.005
    return ok, got, ("shape" if o is None else None), text, pin, pout


def _relay(t, lock):
    """Boucle v14 ; lock=False → S, lock=True → L (verrou importé)."""
    skill = SKILL_L if lock else SKILL
    msgs = [{"role": "system", "content": skill},
            {"role": "user", "content": t["text"]}]
    steps, pins, pouts, repaired = [], 0, 0, 0
    err_shape = None
    while len([s for s in steps if "step" in s]) < 6:
        text, pin, pout, mark = api(msgs)
        pins += pin
        pouts += pout
        o = jobj(text)
        if not isinstance(o, dict):
            if repaired:
                return steps, "protocol_giveup", None, pins, pouts
            repaired, err_shape = 1, "shape"
            msgs.append({"role": "assistant", "content": text})
            msgs.append({"role": "user",
                         "content": ERR_L if lock else
                         '{"error": "protocol: reply EXACTLY '
                         '{\\"step\\": \\"<expression>\\"} or '
                         '{\\"answer\\": \\"<value>\\"} — nothing else"}'})
            continue
        if "answer" in o:
            if not lock:
                if set(o) != {"answer"}:
                    if repaired:
                        return steps, "protocol_giveup", None, pins, pouts
                    repaired, err_shape = 1, "shape"
                    msgs.append({"role": "assistant",
                                 "content": json.dumps(o)})
                    msgs.append({"role": "user", "content": ERR_L})
                    continue
                steps.append({"answer": str(o["answer"])[:40]})
                got = norm_num(o["answer"])
                ok = got is not None and \
                    abs(got - float(t["gold"])) < 0.005
                return steps, (None if ok else "FAUX"), (ok, got, None,
                                                          o), pins, pouts
            if set(o) != {"answer", "target"}:
                if repaired:
                    return steps, "protocol_giveup", None, pins, pouts
                repaired += 1
                msgs.append({"role": "assistant",
                             "content": json.dumps(o)})
                msgs.append({"role": "user", "content": ERR_L})
                continue
            ok, kind, real = lock_verdict(t["qte"], t["cible"],
                                          o["answer"], o["target"])
            steps.append({"answer": str(o["answer"])[:40],
                          "target": str(o["target"])[:40],
                          "lock": kind or "OK"})
            last = (ok, kind, real, o)
            if ok or repaired:
                got = norm_num(o["answer"])
                last = (bool(ok), kind, real, o)
                return steps, (None if ok else "refus_final_" +
                               str(kind)), last, pins, pouts
            repaired += 1
            msgs.append({"role": "assistant", "content": json.dumps(o)})
            msgs.append({"role": "user",
                         "content": refusal_text(kind, o["answer"],
                                                 o["target"], t["cible"],
                                                 t["qte"], real)})
            continue
        if "step" not in o or len(o) != 1:
            if repaired:
                return steps, "protocol_giveup", None, pins, pouts
            repaired += 1
            msgs.append({"role": "assistant",
                         "content": json.dumps(o)})
            msgs.append({"role": "user",
                         "content": ERR_L if lock else
                         '{"error": "protocol: reply EXACTLY '
                         '{\\"step\\": \\"<expression>\\"} or '
                         '{\\"answer\\": \\"<value>\\"} — nothing else"}'})
            continue
        expr = str(o["step"])[:120]
        if not re.fullmatch(r"[0-9+\-*/().\s]+", expr):
            if repaired:
                return steps, "step_not_closed", None, pins, pouts
            repaired += 1
            msgs.append({"role": "assistant", "content": json.dumps(o)})
            msgs.append({"role": "user",
                         "content": '{"error": "step must contain '
                         'only digits and + - * / ( )"}'})
            continue
        val, cerr = calc(expr)
        if cerr:
            return steps, "calc_refused:" + expr[:30], None, pins, pouts
        steps.append({"step": expr, "value": val})
        msgs.append({"role": "assistant", "content": json.dumps(o)})
        echo = '{"value": "%s"}' % val
        if lock:
            echo = '{"value": "%s", "names": %s}' % (
                val, json.dumps(names_for(t["qte"], val)))
        msgs.append({"role": "user", "content": echo})
    return steps, "max_steps", None, pins, pouts


def one(arm, t):
    if arm == "N":
        ok, got, err, text, pin, pout = run_nude(t)
        return ok, got, None, err, pin, pout, [{"naked": text[:120]}]
    steps, err, last, pin, pout = _relay(t, lock=(arm == "L"))
    got = target = None
    ok = False
    if last:
        ok, kind, real, o = last
        got = norm_num(o.get("answer"))
        target = str(o.get("target", ""))[:40] or None
    return ok, got, target, err, pin, pout, steps


if __name__ == "__main__":
    qs = problems()
    arms = sys.argv[1:] or ["N", "S", "L"]
    done = set()
    try:
        for l in open(OUT):
            r = json.loads(l)
            done.add((r["arm"], r["i"]))
    except FileNotFoundError:
        pass
    print("déjà faites:", len(done), "/ 60 —", arms, flush=True)
    with open(OUT, "a", encoding="utf-8") as fh:
        for arm in arms:
            for t in qs:
                if (arm, t["i"]) in done:
                    continue
                ok, got, target, err, pin, pout, steps = one(arm, t)
                usd = (pin * PRICE_IN + pout * PRICE_OUT) / 1e6
                fh.write(json.dumps({
                    "harness": "v23-lfm3-crossfamily", "model": "lfm3",
                    "i": t["i"], "family": t["family"], "arm": arm,
                    "ok": bool(ok), "got": got, "gold": float(t["gold"]),
                    "target_used": target, "cible": t["cible"],
                    "err": err, "tok_in": pin, "tok_out": pout,
                    "usd": round(usd, 6),
                    "trace": json.dumps(steps, ensure_ascii=False)[:400]},
                    ensure_ascii=False) + "\n")
                fh.flush()
                print("%s #%02d %s tok=%d $%.4f %s" % (
                    arm, t["i"], "✓" if ok else "✗", pin + pout, usd,
                    err or ""), flush=True)
                time.sleep(1.0)
