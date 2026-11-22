# -*- coding: utf-8 -*-
"""V22b — LA DÉRIVE FRONTIÈRE SUR JOB RÉPÉTÉ (2026-11-22).

V19 a facturé la dérive aux nains locaux (21 sorties/30 j, 0/30
justes). V22 a montré qu'un job frontière QUI ÉCRIT DU CODE rend la
bonne réponse 7/7 sur les 7 chaînes. Reste l'objection finale : « à
température-agent, mon GPT-5-mini qui code fera le MÊME job pareil
chaque jour ». Ce banc la mesure. C'est LE dernier trou de la thèse.

Protocole gelé : bras C de V22 rejoué (prompt P_CODE, exécution
locale sandbox -I), temp 0,7 — LE régime réel des agents, celui de
v19 — × 5 repasses × 7 problèmes × 2 modèles (gpt5m, dsv32 : les
deux C 7/7 de V22 — on teste la stabilité de ce qui sait déjà
répondre juste). Contrôle machine : chaque repasse POSTE aussi les
créneaux exacts de la fiche prod — le serveur doit rendre le même
sha 35/35.

PRÉDICTIONS GELÉES AVANT LA PREMIÈRE CELLULE :
  B1 dérive : ≥1 des deux modèles change AU MOINS UNE réponse entre
     deux repasses d'un même problème. S'il n'y a zéro dérive, la
     thèse v19 ne monte pas à l'échelle frontière — à publier aussi.
  B2 programme : chaque modèle réécrit un code de sha DIFFÉRENT sur
     ≥2 problèmes/7 entre repasses — le programme n'est jamais gelé,
     même quand la réponse l'est ; « 30 jours même sha » est
     impossible côté client.
  B3 contrôle serveur : 35/35 machine POSTs = même sha par problème.
"""
import json
import sys
import time

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
import run22  # noqa: E402
from gen16 import problems  # noqa: E402

OUT = run22.HERE + "/results_v22b.jsonl"
PASSES = 5
MODELS = ["openai/gpt-5-mini", "deepseek/deepseek-v3.2"]


def nf(x):
    """norm_frac local (la v2 du juge V22) : fraction admise."""
    import re
    s = str(x if x is not None else "").strip().replace(",", ".")
    m = re.fullmatch(r"(-?\d+)\s*/\s*(\d+)", s)
    if m:
        return int(m.group(1)) / int(m.group(2))
    return run22.norm_num(x)


def api_t07(model, prompt):
    body = {"model": model, "temperature": 0.7, "stream": False,
            "messages": [{"role": "user", "content": prompt}]}
    req = run22.urllib.request.Request(
        run22.API, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "***" + run22.key()})
    r = json.loads(run22.urllib.request.urlopen(req, timeout=180).read())
    u = r.get("usage", {})
    return (r["choices"][0]["message"]["content"] or "",
            int(u.get("prompt_tokens", 0)),
            int(u.get("completion_tokens", 0)))


def main():
    done = set()
    try:
        for ln in open(OUT):
            r = json.loads(ln)
            done.add((r["model"], r["pass"], r["i"]))
    except FileNotFoundError:
        pass
    probs = [p for p in problems() if p["family"] in run22.FICHE_OF]
    print("gels : 2 modèles × 5 passes × 7 = 70 cellules ; déjà %d"
          % len(done), flush=True)
    for model in MODELS:
        for ps in range(1, PASSES + 1):
            for p in probs:
                if (run22.SHORT[model], ps, p["i"]) in done:
                    continue
                rec = {"harness": "v22b", "model": run22.SHORT[model],
                       "pass": ps, "i": p["i"], "temp": "0.7",
                       "gold": str(p["gold"])}
                txt, tp, tc = api_t07(model, run22.P_CODE % p["text"])
                code = run22.PYBLOCK.search(txt)
                code = code.group(1) if code else txt
                outc, rc = run22.run_code(code[:8000])
                last = run22.re.findall(r"-?[\d.,/]+", outc.replace(" ", ""))
                rec.update(ans=(last[-1] if last else ""), rc=rc,
                           tok_p=tp, tok_c=tc,
                           code_sha=run22.hashlib_sha(code))
                # contrôle machine : mêmes créneaux exacts, fiche prod
                q, t = p["qte"], p["text"]
                if p["family"] == "mix":
                    pc = q["sold_afternoon"] / q["rest_after_morning"] * 100
                    pcs = int(pc) if pc == int(pc) else pc
                    fiche = "shop-reste"
                    slots = {"total": str(int(q["total"])),
                             "sold_morning": str(int(q["sold_morning"])),
                             "pct_afternoon": "%s%%" % pcs}
                else:
                    import re
                    fr = re.findall(r"(\d+/\d+)", t)
                    fiche = "partage-reste"
                    slots = {"total": re.search(r"partage (\d+)", t).group(1),
                             "first_part": fr[0], "second_of_rest": fr[1]}
                o = run22.post(fiche, slots)
                ans = (o.get("answer") or {}) if isinstance(o, dict) else {}
                rec["m_sha"] = run22.hashlib_sha(json.dumps(
                    ans, sort_keys=True))
                rec["m_ok"] = (nf(ans.get(p.get("cible"))) is not None
                               and abs(nf(ans.get(p.get("cible")))
                                       - nf(str(p["gold"]))) < 1e-9)
                rec["c_ok"] = (nf(rec["ans"]) is not None
                               and abs(nf(rec["ans"]) - nf(str(p["gold"])))
                               < 1e-9)
                with open(OUT, "a") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print("%s p%d #%s c_ok=%s code=%s m_ok=%s" % (
                    rec["model"], ps, p["i"], rec["c_ok"],
                    rec["code_sha"][:6], rec["m_ok"]), flush=True)
                time.sleep(1.2)


if __name__ == "__main__":
    main()
