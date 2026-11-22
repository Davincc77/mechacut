# -*- coding: utf-8 -*-
"""F7 ACCEPT — les 7 chaînes v16 en EN et PT, transport routé.

Critère GELÉ 2026-11-22 20h10 dans bench/FINDINGS-F7.md, avant la
cellule 1 : P3 ≥ 19/56 (ratio F5 − 1) ; P4 : les verdicts FR de F5
rejoués à l'identique. Le modèle ne calcule rien : il COPIE les nombres
dans la langue déclarée. Le serveur ne devine jamais.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen16  # noqa: E402

OLLAMA = "http://127.0.0.1:11434/api/generate"
APP = "http://127.0.0.1:8899"
OUT = os.path.join(HERE, "results_f7_accept.jsonl")
F5 = os.path.join(HERE, "results_f5_accept.jsonl")

MODELS = {"0.5b": "qwen2.5:0.5b-instruct",
          "1.5b": "qwen2.5:1.5b-instruct",
          "7b": "qwen2.5:7b-instruct-q4_K_M",
          "8b": "llama3.1:8b"}
FICHE_OF = {"mix": "shop-reste", "partage": "partage-reste"}
SLOTDOC = {
    "shop-reste": ["total", "sold_morning", "pct_afternoon"],
    "partage-reste": ["total", "first_part", "second_of_rest"],
    "soldes2": ["price", "pct1", "pct2"]}

TEXT = {
    "en": {
        0: "A shop has 435 items. 35 are sold in the morning, and 40% "
           "of the REST in the afternoon. How many remain?",
        2: "We split 3,829 EUR: the first person gets 2/5, the second "
           "1/6 OF THE REST. How much does the second get?",
        6: "A shop has 263 items. 63 are sold in the morning, and 40% "
           "of the REST in the afternoon. How many remain?",
        8: "We split 7,766 EUR: the first person gets 2/5, the second "
           "1/6 OF THE REST. How much does the second get?",
        12: "A shop has 690 items. 90 are sold in the morning, and 50% "
            "of the REST in the afternoon. How many remain?",
        14: "We split 8,814 EUR: the first person gets 1/3, the second "
            "1/4 OF THE REST. How much does the second get?",
        18: "A shop has 377 items. 77 are sold in the morning, and 25% "
            "of the REST in the afternoon. How many remain?",
    },
    "pt": {
        0: "Uma loja tem 435 artigos. 35 sao vendidos de manha e 40% DO "
           "RESTO a tarde. Quantos restam?",
        2: "Dividimos 3.829 EUR: a primeira pessoa recebe 2/5, a segunda "
           "1/6 DO RESTO. Quanto recebe a segunda?",
        6: "Uma loja tem 263 artigos. 63 sao vendidos de manha e 40% DO "
           "RESTO a tarde. Quantos restam?",
        8: "Dividimos 7.766 EUR: a primeira pessoa recebe 2/5, a segunda "
           "1/6 DO RESTO. Quanto recebe a segunda?",
        12: "Uma loja tem 690 artigos. 90 sao vendidos de manha e 50% DO "
            "RESTO a tarde. Quantos restam?",
        14: "Dividimos 8.814 EUR: a primeira pessoa recebe 1/3, a segunda "
            "1/4 DO RESTO. Quanto recebe a segunda?",
        18: "Uma loja tem 377 artigos. 77 sao vendidos de manha e 25% DO "
            "RESTO a tarde. Quantos restam?",
    },
}
PROMPT = {
    "en": ("You do NOT compute anything. Copy the numbers from the "
           "problem into these slots: %s. Copy each number EXACTLY as "
           "written and add \"locale\": \"en\". Answer ONLY "
           "{\"slots\":{...}}\n\n%s"),
    "pt": ("Voce NAO calcula nada. Copie os numeros do problema para "
           "estes campos: %s. Copie cada numero EXATAMENTE como escrito "
           "e acrescente \"locale\": \"pt\". Responda SOMENTE "
           "{\"slots\":{...}}\n\n%s"),
}
P_FIX = ("\n\nThe server REFUSED: slot %s (%s). Fix only that slot, "
         "same answer format.")


def ask(model, prompt):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0, "seed": 42}})
    req = urllib.request.Request(
        OLLAMA, data=body.encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    raw = json.loads(urllib.request.urlopen(req, timeout=240).read())
    toks = raw.get("eval_count", 0) + raw.get("prompt_eval_count", 0)
    return raw["response"], toks, time.time() - t0


def jslot(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def post(fiche, slots):
    req = urllib.request.Request(
        APP + "/api/v1/fiche/" + fiche,
        data=json.dumps({"slots": slots}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"error": "http"}
    except Exception:
        return {"error": "net"}


def main():
    done = set()
    try:
        for ln in open(OUT):
            r = json.loads(ln)
            done.add((r["harness"], r.get("lang"), r["model"], r["i"]))
    except FileNotFoundError:
        pass
    print("déjà rendu:", len(done), "— reprise", flush=True)

    probs = {p["i"]: p for p in gen16.problems()
             if p["family"] in FICHE_OF and p["i"] in TEXT["en"]}

    f = open(OUT, "a")
    # ---------- P3 : 7 chaînes × 4 modèles × 2 langues ----------
    for lang in ("en", "pt"):
        for mkey, mname in MODELS.items():
            for i in sorted(probs):
                if ("f7-accept", lang, mkey, i) in done:
                    continue
                p = probs[i]
                fiche = FICHE_OF[p["family"]]
                prompt = PROMPT[lang] % (", ".join(
                    '"%s"' % s for s in SLOTDOC[fiche]), TEXT[lang][i])
                rec = {"harness": "f7-accept", "lang": lang, "model": mkey,
                       "i": i, "family": p["family"], "gold": p["gold"],
                       "repairs": 0, "toks": 0}
                try:
                    txt, tk, secs = ask(mname, prompt)
                    rec["toks"] = tk
                    got = (jslot(txt) or {}).get("slots")
                    verdict = "PARSE"
                    for _ in range(2):
                        if not isinstance(got, dict):
                            break
                        out = post(fiche, got)
                        if "errors" in out and rec["repairs"] == 0:
                            err = out["errors"][0]
                            rec["repairs"] = 1
                            txt2, tk2, _ = ask(
                                mname, prompt + P_FIX % (err.get("field"),
                                                         err.get("expected")))
                            rec["toks"] += tk2
                            got = (jslot(txt2) or {}).get("slots")
                            continue
                        if "answer" in out:
                            key = ("remaining" if p["family"] == "mix"
                                   else "second_share")
                            ans = out["answer"]
                            val = ans.get(key) if isinstance(ans, dict) else ans
                            gold = float(str(p["gold"]).replace(
                                ",", "."))
                            ok = (val is not None and abs(
                                float(str(val).split(" ")[0]
                                          .replace(",", "."))
                                - gold) < 0.005)
                            verdict = "OK" if ok else "FAUX"
                            rec["got"] = val
                        else:
                            verdict = "ERREUR:%s" % out.get("error")
                        break
                    rec["verdict"] = verdict
                except Exception as e:
                    rec["verdict"] = "CRASH:%s" % type(e).__name__
                f.write(json.dumps(rec) + "\n")
                f.flush()
                print(lang, mkey, "i%d" % i, rec["verdict"], flush=True)
                time.sleep(2.2)

    # ---------- P4 : non-dégât FR (rejoue B_routée 7b + 1.5b) ----------
    f5_verdicts = {}
    for ln in open(F5):
        r = json.loads(ln)
        if r["menu"] == "B_routée":
            f5_verdicts[(r["model"], r["i"])] = r["verdict"]
    for mkey in ("7b", "1.5b"):
        for i in sorted(probs):
            if ("f7-p4", None, mkey, i) in done:
                continue
            p = probs[i]
            fiche = FICHE_OF[p["family"]]
            prompt = ("Tu ne CALCULES RIEN. Recopie les nombres du "
                      "problème dans ces créneaux : %s. Réponds "
                      'UNIQUEMENT {"slots":{...}}\n\n%s') % (
                          ", ".join('"%s"' % s for s in SLOTDOC[fiche]),
                          p["text"])
            rec = {"harness": "f7-p4", "model": mkey, "i": i,
                   "repairs": 0, "toks": 0}
            try:
                txt, tk, _ = ask(MODELS[mkey], prompt)
                rec["toks"] = tk
                got = (jslot(txt) or {}).get("slots")
                verdict = "PARSE"
                for _ in range(2):
                    if not isinstance(got, dict):
                        break
                    out = post(fiche, got)
                    if "errors" in out and rec["repairs"] == 0:
                        err = out["errors"][0]
                        rec["repairs"] = 1
                        txt2, tk2, _ = ask(
                            MODELS[mkey], prompt + "\n\nLe serveur a "
                            "REFUSÉ : %s (%s). Corrige uniquement ce "
                            "créneau." % (err.get("field"),
                                          err.get("expected")))
                        rec["toks"] += tk2
                        got = (jslot(txt2) or {}).get("slots")
                        continue
                    if "answer" in out:
                        key = ("remaining" if p["family"] == "mix"
                               else "second_share")
                        ans = out["answer"]
                        val = ans.get(key) if isinstance(ans, dict) else ans
                        gold = float(str(p["gold"]).replace(",", "."))
                        ok = (val is not None and abs(
                            float(str(val).split(" ")[0]
                                      .replace(",", "."))
                            - gold) < 0.005)
                        verdict = "OK" if ok else "FAUX"
                    else:
                        verdict = "ERREUR:%s" % out.get("error")
                    break
                rec["verdict"] = verdict
            except Exception as e:
                rec["verdict"] = "CRASH:%s" % type(e).__name__
            rec["f5_verdict"] = f5_verdicts.get((mkey, i))
            rec["degage"] = rec["verdict"] != rec["f5_verdict"]
            f.write(json.dumps(rec) + "\n")
            f.flush()
            print("P4", mkey, "i%d" % i, rec["verdict"],
                  "(F5:", rec["f5_verdict"], ")", flush=True)
            time.sleep(2.2)
    f.close()

    # ---------- verdicts ----------
    rows = [json.loads(l) for l in open(OUT)]
    p3 = [r for r in rows if r["harness"] == "f7-accept"]
    wins = sum(1 for r in p3 if r["verdict"] == "OK")
    print("\nP3 : %d/%d — critère gelé ≥19/56 : %s"
          % (wins, len(p3), "PASSÉ" if wins >= 19 else "RATÉ"))
    for lg in ("en", "pt"):
        for mk in MODELS:
            sub = [r for r in p3 if r["lang"] == lg and r["model"] == mk]
            print("  %s/%s : %d/%d (repairs %d)"
                  % (lg, mk, sum(1 for r in sub if r["verdict"] == "OK"),
                     len(sub), sum(r["repairs"] for r in sub)))
    p4 = [r for r in rows if r["harness"] == "f7-p4"]
    bad = [r for r in p4 if r["degage"]]
    print("P4 : %d rejouées, %d dégâts — critère 0 dégât : %s"
          % (len(p4), len(bad), "PASSÉ" if not bad and len(p4) == 14
             else "EN COURTS" if len(p4) < 14 else "RATÉ"))


if __name__ == "__main__":
    main()
