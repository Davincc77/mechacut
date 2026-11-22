# -*- coding: utf-8 -*-
"""F5 ACCEPT — critère A3 (gelé dans FINDINGS-V15) : « la fiche
mono-appel doit faire ≥ ce que R+S font ensemble sur mix/partage
(19/56) ».

Lecture du dénominateur, écrite AVANT la première cellule : 56 = 7
problèmes à chaîne v16 × 4 modèles × 2 transports, les deux seuls
honnêtes pour une fiche :
  A_découverte : le problème nu + les 3 fiches (dont soldes2, leurre)
                 — le modèle CHOISIT la fiche et remplit les créneaux.
  B_routée     : la fiche nommée d'office + créneaux à remplir.
Réparation : sur refus nommé du serveur, UNE repasse avec le message
exact (doctrine v14). temp 0, seed 42, pace 2,2 s. Repreneable :
(menu, model, i) déjà vu = sauté.

Verdict figé : OK si ≥ 19/56. Les victoires par modèle, par famille
et le taux de réparation sont publiés tels quels, y compris le 0.5B
qu'on attend au plafond (c'est la borne, pas un échec caché).
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, ".")
import gen16  # noqa: E402

OLLAMA = "http://127.0.0.1:11434/api/generate"
APP = "http://127.0.0.1:8899"
OUT = "results_f5_accept.jsonl"

MODELS = {"0.5b": "qwen2.5:0.5b-instruct",
          "1.5b": "qwen2.5:1.5b-instruct",
          "7b": "qwen2.5:7b-instruct-q4_K_M",
          "8b": "llama3.1:8b"}
FICHE_OF = {"mix": "shop-reste", "partage": "partage-reste"}
TARGET_OF = {"mix": "remaining", "partage": "second_share"}
SLOTDOC = {
    "shop-reste": ["total", "sold_morning", "pct_afternoon"],
    "partage-reste": ["total", "first_part", "second_of_rest"],
    "soldes2": ["price", "pct1", "pct2"]}
MENU = "\n".join("- /api/v1/fiche/%s : créneaux %s"
                 % (f, ", ".join('"%s"' % s for s in sl))
                 for f, sl in SLOTDOC.items())

P_DISCOVER = ("Tu ne CALCULES RIEN. Choisis LA fiche qui correspond au "
              "problème et recopie les nombres, tels qu'écrits.\n" + MENU +
              '\nRéponds UNIQUEMENT: {"fiche":"...", "slots":{...}}\n\n%s')
P_ROUTED = ("Tu ne CALCULES RIEN. Recopie les nombres du problème dans "
            'ces créneaux : %s. Réponds UNIQUEMENT {"slots":{...}}\n\n%s')
P_FIX = ("\n\nLe serveur a REFUSÉ : %s (%s). Corrige uniquement ce "
         "créneau, même format de réponse.")


def ask(model, prompt):
    body = json.dumps({"model": model, "prompt": prompt,
                       "stream": False,
                       "options": {"temperature": 0, "seed": 42}})
    req = urllib.request.Request(
        OLLAMA, data=body.encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    raw = json.loads(urllib.request.urlopen(req, timeout=240).read())
    txt = raw["response"]
    toks = raw.get("eval_count", 0) + raw.get("prompt_eval_count", 0)
    return txt, toks, time.time() - t0


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
            done.add((r["menu"], r["model"], r["i"]))
    except FileNotFoundError:
        pass
    print("déjà rendu:", len(done), "— reprise", flush=True)

    probs = [p for p in gen16.problems() if p["family"] in FICHE_OF]
    for menu in ("A_découverte", "B_routée"):
        for mkey, mname in MODELS.items():
            for p in probs:
                if (menu, mkey, p["i"]) in done:
                    continue
                fiche = FICHE_OF[p["family"]]
                prompt = (P_DISCOVER % p["text"] if menu == "A_découverte"
                          else P_ROUTED % (", ".join(
                              '"%s"' % s for s in SLOTDOC[fiche]),
                              p["text"]))
                rec = {"harness": "f5-accept", "menu": menu,
                       "model": mkey, "i": p["i"],
                       "family": p["family"], "gold": p["gold"],
                       "repairs": 0, "toks": 0}
                got = None
                try:
                    txt, tk, secs = ask(mname, prompt)
                    rec["toks"] = tk
                    j = jslot(txt)
                    chosen = fiche
                    if menu == "A_découverte" and j and "fiche" in j:
                        chosen = j["fiche"].replace("/api/v1/fiche/", "")
                        got = j.get("slots")
                    else:
                        got = (j or {}).get("slots", j)
                    for _ in range(2):          # 1 essai + 1 réparation
                        if not chosen or chosen not in SLOTDOC:
                            rec["verdict"] = "FICHE-INCONNUE:%s" % chosen
                            break
                        if not isinstance(got, dict):
                            rec["verdict"] = "PARSE"
                            break
                        out = post(chosen, got)
                        if "errors" in out and rec["repairs"] == 0:
                            err = out["errors"][0]
                            rec["repairs"] = 1
                            txt2, tk2, _ = ask(
                                mname, prompt + P_FIX % (err.get("field"),
                                                         err.get("expected")))
                            rec["toks"] += tk2
                            j2 = jslot(txt2)
                            got = ((j2 or {}).get("slots")
                                   if menu == "B_routée" else
                                   (j2 or {}).get("slots", got))
                            continue
                        if "answer" not in out:
                            rec["verdict"] = "REFUS-2"
                            break
                        val = out["answer"][TARGET_OF[p["family"]]]
                        rec["got"] = val
                        from decimal import Decimal
                        rec["verdict"] = ("OK" if Decimal(val) ==
                                          Decimal(str(p["gold"]))
                                          else "FAUX")
                        break
                except Exception as e:
                    rec["verdict"] = "ERREUR:%s" % type(e).__name__
                with open(OUT, "a") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print("%s %s #%d → %s (rep%d)" % (
                    menu[:6], mkey, p["i"], rec.get("verdict"),
                    rec["repairs"]), flush=True)
                time.sleep(2.2)

    wins = tot = rep = 0
    per = {}
    for ln in open(OUT):
        r = json.loads(ln)
        tot += 1
        rep += r["repairs"]
        w = r["verdict"] == "OK"
        wins += w
        per.setdefault(r["model"], [0, 0])
        per[r["model"]][0] += w
        per[r["model"]][1] += 1
    print("=== F5 ACCEPT: %d/%d (critère ≥19) réparations=%d ===" % (
        wins, tot, rep))
    for m, (w, t) in sorted(per.items()):
        print("  %s: %d/%d" % (m, w, t))


if __name__ == "__main__":
    main()
