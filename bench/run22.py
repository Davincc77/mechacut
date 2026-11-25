# -*- coding: utf-8 -*-
"""BENCH V22 — LA FRONTE A-T-ELLE LE MÊME MAL ? (2026-11-22)

L'objection qui tue la thèse après douze bancs locaux 0,5–8B :
« GPT-5/Claude ne font pas ces erreurs ». Ce banc la mesure en
DOLLARS par réponse juste. Personne ne l'a publié : la littérature
(Snell 2408.03314, 2511.00751, 2610.23213, τ-bench) prouve le MAL —
retry placebique, dérive pass^k — mais personne n'a prixé le REMÈDE
sur les mêmes golds.

Dénominateur, écrit AVANT la première cellule : 63 cellules =
7 problèmes à chaîne v16 (mix + partage, golds Fraction gelés par
gen16, double-gate 22-11) × 3 modèles frontière × 3 bras :
  N nu        : le problème, « réponds UNIQUEMENT par le nombre ».
  C code      : le modèle ÉCRIT du Python (le camp concurrent A —
                PoT/SymCode/CodeMem), exécuté ICI en sandbox -I,
                8 s, stdout = la réponse. Le modèle ne calcule pas,
                il décrète un programme — c'est exactement leur promesse.
  F fiche     : B_routée de F5 rejouée À L'IDENTIQUE (fiche nommée,
                créneaux verbatim, refus nommé, réparation ×1),
                serveur = PROD https://mechacut.studio (v0.82.0,
                free <32 Ko). Le modèle ne décompose plus RIEN.

Modèles (un par famille, prix GELÉS dans PRICING le 22-11, source
/v1/models de l'API Nous) : claude-haiku-latest, gpt-5-mini,
deepseek-v3.2. temp 0 demandé ; si l'API REJETTE temp, un seul
retry aux paramètres par défaut et la ligne porte
"temp":"provider-default" (règle gelée, pas une improvisation).

ok au juge : norm_num(run16) == gold, EXACT. Le bras C compte EN
OUTRE « sem » : valeur approchante (|x−gold| ≤ 1e-6 mais pas
égale en décimal exact — le 0.30000000000000004 de v12) = faute
SÉMANTIQUE, publiée comme telle même si l'arrondi humain pardonnerait.
Le bras F est juste si le SERVEUR rend la cible et que trace[-1]
égale le gold ; le coût F = tokens du modèle seul, serveur à $0.

PRÉDICTIONS GELÉES AVANT LA PREMIÈRE CELLULE (le scoreur statue) :
  P1 l'objention tient-elle : ≥1 modèle fait ≥5/7 au bras N.
     Si oui, publier : sur ces 7 problèmes, la taille ENTERRE le mal
     — le produit redescend sur les petits modèles + la stabilité v19.
  P2 leur promesse tient-elle : C ≥ 6/7 sur les TROIS modèles ET
     zéro faute sémantique sur ≥5/7 chacun. Sinon, la frontière
     code aussi à côté avec assurance — le mal n'est pas la taille.
  P3 F = 7/7 partout. La transcription verbatim est le travail qu'un
     LM sait faire ; si F < 7/7, c'est le mur de lecture qui suit
     la frontière aussi — à publier tel quel.
  P4 économie : $/juste(F) ≤ $/juste(C) et tokens/juste(F) ≤ 30 %
     de tokens/juste(C).
  P5 stabilité : le bras F rend le MÊME sha serveur sur les 3
     modèles pour chaque problème (la réponse est dans le serveur,
     pas dans l'échantillon).

Repreneable : (model, arm, i) déjà vu = sauté. Pace 1,5 s.
"""
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = "/Users/vincenzocirilli/Downloads/mechacut/bench"
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, HERE)
from gen16 import problems                      # noqa: E402


def norm_num(x):
    # juge maison, copié de run16 (son import traînait httpx)
    s = str(x if x is not None else "").strip().replace(",", ".")
    s = re.sub(r"[^\d.\-]", "", s)
    try:
        return float(s)
    except Exception:
        return None

API = "https://inference-api.nousresearch.com/v1/chat/completions"
APP = "https://mechacut.studio"
OUT = HERE + "/results_v22.jsonl"
KEY = ""  # gelée dans main() avant la première cellule

# prix $/M tokens, saisis sur /v1/models le 22-11-2026 (GELÉS)
PRICING = {
    "anthropic/claude-haiku-4.5": (1.00, 5.00),
    "openai/gpt-5-mini": (0.25, 2.00),
    "deepseek/deepseek-v3.2": (0.26, 0.38),
}
SHORT = {"anthropic/claude-haiku-4.5": "haiku45",
         "openai/gpt-5-mini": "gpt5m",
         "deepseek/deepseek-v3.2": "dsv32"}
ARMS = ("N", "C", "F")

FICHE_OF = {"mix": "shop-reste", "partage": "partage-reste"}
SLOTDOC = {"shop-reste": ["total", "sold_morning", "pct_afternoon"],
           "partage-reste": ["total", "first_part", "second_of_rest"]}

P_NUDE = ("Tu ne CALCULES RIEN toi-même si tu n'en es pas capable : "
          "résous ce problème et réponds UNIQUEMENT par le nombre "
          "final.\n\n%s")
P_CODE = ("Écris UNIQUEMENT un script Python autonome qui résout ce "
          "problème avec decimal ou fractions (pas de float pour le "
          "résultat final) et l'IMPRIME seul, sans arrondi. Pas de "
          "prose, pas de commentaires.\n\n%s")
P_ROUTED = ("Tu ne CALCULES RIEN. Recopie les nombres du problème "
            "dans ces créneaux : %s. Réponds UNIQUEMENT "
            '{"slots":{...}}\n\n%s')
P_FIX = ("\n\nLe serveur a REFUSÉ : %s (%s). Corrige uniquement ce "
         "créneau, même format de réponse.")
PYBLOCK = re.compile(r"```(?:python)?\s*(.+?)```", re.S)


def key():
    import os
    p = os.path.expanduser("~/.hermes/auth.json")
    try:
        d = json.load(open(p))["providers"]["nous"]
        return d.get("agent_key") or d["access_token"]
    except Exception:
        raise SystemExit("pas de clé Nous (auth.json providers/nous)")


def api(model, msgs):
    def call(temp):
        body = {"model": model, "messages": msgs, "stream": False}
        if temp:
            body["temperature"] = 0
        req = urllib.request.Request(
            API, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + key()})
        return json.loads(urllib.request.urlopen(req, timeout=180).read())
    tmark = "0"
    try:
        r = call(True)
    except urllib.error.HTTPError as e:
        txt = e.read().decode(errors="replace")
        if "temperature" in txt.lower():     # règle gelée P/temp
            tmark = "provider-default"
            r = call(False)
        else:
            raise
    u = r.get("usage", {})
    return (r["choices"][0]["message"]["content"] or "",
            int(u.get("prompt_tokens", 0)),
            int(u.get("completion_tokens", 0)), tmark)


def post(fiche, slots):
    req = urllib.request.Request(
        APP + "/api/v1/fiche/" + fiche,
        data=json.dumps({"slots": slots}).encode(),
        headers={"Content-Type": "application/json",
                 "User-Agent": "mechacut-bench/22.0 (research; contact: "
                               "github.com/mechacut/mechacut)"})
    try:
        out = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        try:
            out = json.loads(e.read().decode())
        except Exception:
            return {"error": "http"}
    except Exception:
        return {"error": "net"}
    return out if isinstance(out, dict) else {"error": "nonjson"}


def run_code(code):
    try:
        r = subprocess.run([sys.executable, "-I", "-c", code],
                           capture_output=True, text=True, timeout=8,
                           cwd="/tmp")
        return (r.stdout or "").strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", -1
    except Exception:
        return "", -2


def judge_row(row):
    """Juge séparé : ne lit QUE les champs de la ligne."""
    gold = norm_num(row["gold"])
    if row["arm"] == "F":
        return "OK" if row.get("server_ok") else row.get("verdict", "ERR")
    got = norm_num(row.get("answer", ""))
    if got is None or gold is None:
        return "PARSE"
    if got == gold:
        return "OK"
    try:                                     # faute sémantique (bras C)
        if row["arm"] == "C" and abs(float(got) - float(gold)) <= 1e-6:
            return "SEM"
    except Exception:
        pass
    return "FAUX"


def cell(model, arm, p, KEY):
    fiche = FICHE_OF[p["family"]]
    rec = {"harness": "v22", "model": SHORT[model], "arm": arm,
           "i": p["i"], "family": p["family"], "gold": str(p["gold"]),
           "tok_p": 0, "tok_c": 0, "repairs": 0}
    if arm == "N":
        txt, tp, tc, tm = api(model, [{"role": "user",
                                       "content": P_NUDE % p["text"]}])
        rec.update(answer=txt.strip()[:200], tok_p=tp, tok_c=tc, temp=tm)
    elif arm == "C":
        txt, tp, tc, tm = api(model, [{"role": "user",
                                       "content": P_CODE % p["text"]}])
        code = PYBLOCK.search(txt)
        code = code.group(1) if code else txt
        out, rc = run_code(code[:8000])
        last = re.findall(r"-?[\d.,/]+", out.replace(" ", ""))
        rec.update(answer=(last[-1] if last else ""), tok_p=tp, tok_c=tc,
                   temp=tm, rc=rc, code_sha=hashlib_sha(code))
    else:
        prompt = P_ROUTED % (", ".join('"%s"' % s for s in SLOTDOC[fiche]),
                             p["text"])
        txt, tp, tc, tm = api(model, [{"role": "user", "content": prompt}])
        rec.update(tok_p=tp, tok_c=tc, temp=tm)
        slots = jslot(txt)
        for _ in range(2):                   # 1 essai + 1 réparation
            if not isinstance(slots, dict):
                rec["verdict"] = "PARSE"
                return rec
            out = post(fiche, slots)
            if not isinstance(out, dict) or out.get("error"):
                err = (out.get("errors") or [{}])[0]
                if not isinstance(err, dict):
                    err = {}
                msg = (err.get("field", ""), err.get("expected", ""))
                rec["repairs"] += 1
                txt2, tp2, tc2, _ = api(
                    model, [{"role": "user",
                             "content": prompt + P_FIX % msg}])
                rec["tok_p"] += tp2
                rec["tok_c"] += tc2
                slots = jslot(txt2)
                continue
            trace = out.get("trace") or []
            ans = out.get("answer") or {}
            cible = p.get("cible") or {"mix": "remaining",
                                       "partage": "second_share"}[
                                           p["family"]]
            server_ans = ans.get(cible)
            if server_ans is None and trace and isinstance(trace[-1], dict):
                server_ans = trace[-1].get("value")
            rec["server_ok"] = (norm_num(str(server_ans))
                                == norm_num(str(p["gold"])))
            rec["server_sha"] = hashlib_sha(
                json.dumps(ans, sort_keys=True))
            rec["cible"] = cible
            rec["answer"] = str(server_ans)[:60]
            return rec
        rec["verdict"] = "REFUS-2"
    return rec


def jslot(txt):
    m = re.search(r"\{.*\}", txt or "", re.S)
    if not m:
        return None
    try:
        j = json.loads(m.group(0))
    except Exception:
        return None
    return j.get("slots", j)


def hashlib_sha(s):
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def main():
    global KEY
    KEY = key()
    done = set()
    try:
        for ln in open(OUT):
            r = json.loads(ln)
            done.add((r["model"], r["arm"], r["i"]))
    except FileNotFoundError:
        pass
    probs = [p for p in problems() if p["family"] in FICHE_OF]
    print("gels : %d problèmes × %d modèles × 3 bras = %d ; déjà %d"
          % (len(probs), len(PRICING), len(probs) * 3 * len(PRICING),
             len(done)), flush=True)
    for model in PRICING:
        for arm in ARMS:
            for p in probs:
                if (SHORT[model], arm, p["i"]) in done:
                    continue
                try:
                    rec = cell(model, arm, p, KEY)
                except Exception as e:
                    print("ERR %-9s %s #%s : %s" % (SHORT[model], arm,
                                                    p["i"], e), flush=True)
                    time.sleep(4)
                    continue
                rec["ok"] = judge_row(rec) == "OK"
                with open(OUT, "a") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print("%-9s %s #%s %s" % (SHORT[model], arm, p["i"],
                                          rec["ok"]), flush=True)
                time.sleep(1.5)


if __name__ == "__main__":
    main()
