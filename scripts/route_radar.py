#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""route_radar — la fonction de recherche de douleurs COTE ROUTEUR et
ADAPTATEUR, pour la boucle de croissance. Deterministe, lecture seule,
jamais de secret echoe.

Deux lentilles :
  1. RADAR (defaut) — sonde le routeur de PROD avec un corpus de
     formulations reelles (x3 langues, variantes d'accents et de
     casse, leurres « ne doit PAS matcher ») via GET /route et, si le
     manifest les declare, POST /api/v1/router/plan + /apply.
     Classes de douleur pechees : NO_MATCH (douleur = requete morte),
     WRONG (douleur = mauvaise aiguille, pire que le silence),
     OVERMATCH (douleur = le serveur s'invente une extraction sur une
     phrase sans donnees), REGRESSION (marchait hier, casse
     aujourd'hui).
  2. CATALOG (--catalog) — le piege d'ADAPTATEUR de l'incident V23 :
     un id MODELE liste n'est pas un id invocable. Liste /v1/models
     (Nous), sonde un echantillon en un appel 1-token, signale les
     MIRAGES (liste 200, appel 404). C'est la douleur des gens qui
     cablent des annuaires a l'aveugle — la notre pareil.

Sorties : docs/RADAR/scan-<ts>.json + latest.json + diff avec le scan
precedent (nouvelles douleurs / gueris / regresses) ; resume markdown
imprimé pour coller dans DEMAND-QUEUE.md. Le script ne decide rien :
il mesure, la boucle choisit.
"""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

APP = "https://mechacut.studio"
UA = ("mechacut-radar/1.0 (growth-loop; contact: "
      "github.com/Davincc77/mechacut)")
NOUS = "https://inference-api.nousresearch.com/v1"
RADAR_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "docs", "RADAR")

# ---------------- lentille 1 : le corpus. Chaque cas = (texte,
# attente). attente : nom de fiche/route cherche dans le top, ou
# None = « ne doit RIEN prescrire » (leurre). Les variantes
# accent/casse TESTENT l'incident consigne v0.84.0
# (accents+egalite=NO-MATCH).
CASES = [
    # chaîne, x3 langues + variantes — la zone 0/28 est le territory
    ("magasin 435 articles, 35 vendus le matin, 40 % du reste "
     "l'après-midi, combien restent", "shop"),
    ("magasin 435 articles, 35 vendus le matin, 40 % du RESTE "
     "l'après-midi, combien restent", "shop"),
    ("435 articles, 35 le matin, 40% Du Reste l'apres-midi combien "
     "restent", "shop"),
    ("shop had 435 items, 35 sold in the morning, 40% of the rest "
     "in the afternoon, how many remain", "shop"),
    ("loja tinha 435, vendeu 35 de manha, 40% do resto a tarde, "
     "quantos restam", "shop"),
    ("partage 3829 : le premier recoit 2/5, le second 1/6 du reste",
     "partage"),
    ("split 3829: first gets 2/5, second 1/6 of the rest",
     "partage"),
    ("-25 % puis -20 % sur 81,90 — prix final", "soldes"),
    ("is 30% off plus another 20% the same as 50% off on 89.90",
     "soldes"),
    # quotidien — le noyau qui compte
    ("mon vol est arrive avec 3 h 20 de retard le 1er nov. 2027, "
     "que me doit la table EU", "flight"),
    ("my bag is 40x18x30, flight 2027-11-02 — free under the seat",
     "baggage"),
    ("avant d'ouvrir ce CSV dans Excel, quelles colonnes perdent "
     "leurs zeros", "excel"),
    ("openpyxl read 1000000 but the human saw $1,000", "display"),
    ("tarif A 0,25 €/kWh + 0,60 par jour, B 0,27 + 0,45 — à partir "
     "de combien de kWh A gagne", "crossover"),
    # leurres : aucune extraction fermee n'est licite — le routeur
    # doit REFUSER par le nom, pas inventer.
    ("raconte-moi une blague sur les bases de donnees", None),
    ("je ne sais pas encore ce que je veux calculer, parlons-en",
     None),
    ("435 articles et puis la vie, le temps, les gens", None),
]


def get(url, params=None, data=None, headers=None):
    if params:
        url += "?" + "&".join(
            "%s=%s" % (k, urllib.parse.quote(str(v)))
            for k, v in params.items())
    req = urllib.request.Request(url, data=data, headers=headers or {})
    req.add_header("User-Agent", UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)[:120]}


import urllib.parse  # noqa: E402  (après get pour lisibilité)


def probe_router(manifest):
    st, info = get(APP + "/")
    has_plan = "/api/v1/router/plan" in (info.get("endpoints") or {})
    rows = []
    for text, want in CASES:
        rec = {"text": text[:80], "want": want}
        st, body = get(APP + "/route", {"q": text, "top": "5"})
        tools = body.get("tools") or []
        names = [t.get("tool", "") for t in tools]
        top_score = tools[0].get("score", 0) if tools else 0
        top1 = names[0] if names else ""
        rec["route_top"] = top1
        rec["score"] = top_score
        # un leurre est « bien traité » si RIEN ne franchit le seuil
        # de confiance (5) : le routeur ne doit pas inventer une
        # destination. En dessous, c'est un refus doux ; au-dessus,
        # OVERMATCH. Les scores des vraies douleurs (shop/prix) sont
        # >=9 sur ce corpus.
        if want is None:
            rec["verdict"] = ("leurre-ok" if top_score <= 5 or
                              body.get("elsewhere") else "OVERMATCH")
        else:
            hit = any(want.lower() in n.lower() for n in names[:3])
            rec["verdict"] = ("ok" if hit else
                              ("NO_MATCH" if top_score <= 5
                               else "WRONG"))
        rows.append(rec)
        time.sleep(0.3)
    if has_plan:
        for text, want in CASES[:8]:
            st, body = get(APP + "/api/v1/router/plan",
                           data=json.dumps({"texte": text}).encode(),
                           headers={"Content-Type":
                                    "application/json"})
            got = (body.get("fiche") or body.get("prescribed")
                   or body.get("route") or "")
            rec = {"text": text[:80], "want": want, "via": "plan",
                   "verdict": ("plan-http-%d" % st if st != 200
                               else "ok" if (want is None and
                                             not got) or (want and
                                             want.lower() in
                                             str(got).lower())
                               else "plan-WRONG")}
            rows.append(rec)
            time.sleep(0.3)
    return rows


# ---------------- lentille 2 : mirages de catalogue.
def probe_catalog(sample=12):
    def key():
        p = os.path.expanduser("~/.hermes/auth.json")
        try:
            d = json.load(open(p))["providers"]["nous"]
            return d.get("agent_key") or d["access_token"]
        except Exception:
            return None
    k = key()
    if not k:
        return [{"verdict": "catalog-skipped", "text": "pas de cle"}]
    req = urllib.request.Request(NOUS + "/models", headers={
        "Authorization": "Bearer " + k, "User-Agent": UA})
    try:
        ids = sorted(m["id"] for m in json.loads(
            urllib.request.urlopen(req, timeout=60).read())["data"])
    except Exception as e:
        return [{"verdict": "catalog-error", "text": str(e)[:80]}]
    step = max(1, len(ids) // sample)
    picked = ids[::step][:sample]
    out = []
    for mid in picked:
        body = json.dumps({"model": mid, "stream": False,
                           "max_tokens": 2, "messages": [{"role":
                           "user", "content": "OK"}]}).encode()
        st, _ = get(NOUS + "/chat/completions", data=body, headers={
            "Authorization": "Bearer " + k,
            "Content-Type": "application/json"})
        out.append({"text": mid, "want": None,
                    "verdict": "ok" if st == 200 else
                    ("MIRAGE" if st == 404 else "http-%d" % st)})
        time.sleep(1.0)
    return out


def main():
    argv = sys.argv[1:]
    os.makedirs(RADAR_DIR, exist_ok=True)
    rows = probe_router(None)
    if "--catalog" in argv:
        rows += probe_catalog()
    scan = {"ts": datetime.now().isoformat(timespec="seconds"),
            "n": len(rows),
            "counts": {v: sum(1 for r in rows if r["verdict"] == v)
                       for v in sorted({r["verdict"] for r in rows})},
            "rows": rows}
    latest = os.path.join(RADAR_DIR, "latest.json")
    prev = {}
    if os.path.exists(latest):
        prev = {r["text"]: r["verdict"]
                for r in json.load(open(latest))["rows"]}
    stamp = scan["ts"].replace(":", "-").replace(" ", "_")
    with open(os.path.join(RADAR_DIR, "scan-%s.json" % stamp),
              "w") as fh:
        json.dump(scan, fh, ensure_ascii=False, indent=1)
    with open(latest, "w") as fh:
        json.dump(scan, fh, ensure_ascii=False, indent=1)
    new_pain = [r for r in rows
                if r["verdict"] not in ("ok", "leurre-ok", "plan-skip")
                and prev.get(r["text"]) == "ok"]
    fresh = [r for r in rows
             if r["verdict"] not in ("ok", "leurre-ok", "plan-skip")
             and r["text"] not in prev]
    healed = [t for t, v in prev.items()
              if v not in ("ok", "leurre-ok", "plan-skip")
              and any(r["text"] == t and r["verdict"] in
                      ("ok", "leurre-ok") for r in rows)]
    print("# RADAR ROUTEUR — %s" % scan["ts"])
    print("douleurs actives : %s" % json.dumps(
        {k: v for k, v in scan["counts"].items()
         if k not in ("ok", "leurre-ok", "plan-skip")}))
    for label, items in (("REGRESSION", new_pain), ("NOUVELLE", fresh),
                         ("GUERIE", healed)):
        for it in items[:8]:
            if isinstance(it, dict):
                print("- %s : %r → %s" % (label, it["text"],
                                          it["verdict"]))
            else:
                print("- GUERIE : %r" % it[:70])
    print("(brut : docs/RADAR/scan-%s.json — local-only)" % stamp)


if __name__ == "__main__":
    main()
