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
# Règle de cadence (bundle 72) : le scan 06:22 du 23-nov s'est
# auto-infligé un plan-http-429 — 0,3 s de sommeil = 33 req/min,
# au-dessus de NOTRE propre règle 25/min enseignée à l'instance qui
# consomme. La lentille ferme sa douleur : toute sonde de PROD attend
# APP_MIN_GAP.
APP_MIN_GAP = 2.6
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
    # RE-DÉCLARÉE 23-11 cycle 14h56 : la want « soldes » n'a jamais
    # désigné un outil du catalogue — l'artefact comparatif vit chez
    # money_discount ; la want dit maintenant le nom vrai.
    ("is 30% off plus another 20% the same as 50% off on 89.90",
     "discount"),
    # les deux outils du cycle — garde de leur propre douleur
    ("is retrying this timeout a fourth time rational or am i stuck",
     "retrybudget"),
    ("this strikethrough says minus 30 percent — is it legal under "
     "the omnibus rule", "discount_audit"),
    ("le prix barré annonce -30 pour cent — est-ce licite face à "
     "la règle des trente jours ?", "discount_audit"),
    ("a loja anuncia 30% sobre o preço riscado — é ilegal pela "
     "regra dos 30 dias?", "discount_audit"),
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
    # bundle 95 — l'ORTHGRAPHE ACCENTUÉE, variante que le corpus ne
    # testait JAMAIS (ses « variantes d'accents » étaient déaccentuées :
    # l'angle mort du test était le test). Sept dictées MESURÉES en
    # prod le 23-nov sous v1.16.0 (WRONG/NO_MATCH avant le pli T7).
    ("c'est quoi un prix barré légal", "discount_audit"),
    ("prix barré légal plus bas à 80", "discount_audit"),
    ("le prix barré est-il vrai", "discount_audit"),
    ("la promotion est-elle licite", "discount_audit"),
    ("recouvrement facture impayé", "aging"),
    ("preço riscado é legal", "discount_audit"),
    ("is the strikethrough was price legal under omnibus",
     "discount_audit"),
    # bundle 96 — le pilier 3 du trio boutique. Douleur : la
    # requête HUMaine « qui me rend la différence » était volée par
    # unitprice/discount-audit (les mots « prix » et « 80 » sont
    # déjà occupés) ; ces lignes ferment la découvrabilité du nouvel
    # outil ET gardent la frontière avec return-deadline.
    ("j'ai acheté 100 à la Fnac, passé à 80, qui me rembourse la "
     "différence", "pricedrop"),
    ("i paid 100 at best buy and the price dropped to 80 last week "
     "— who owes me the difference", "pricedrop"),
    ("comprei por 100 na fnac e caiu para 80, quem me devolve a "
     "diferenca", "pricedrop"),
    ("PRIX BAISSE APRES ACHAT REMBOURSEMENT DIFFÉRENCE fnac",
     "pricedrop"),
    ("can I still return the TV I bought at target, until when",
     "return_deadline"),
    # leurres : aucune extraction fermee n'est licite — le routeur
    # doit REFUSER par le nom, pas inventer.
    ("raconte-moi une blague sur les bases de donnees", None),
    ("je ne sais pas encore ce que je veux calculer, parlons-en",
     None),
    ("435 articles et puis la vie, le temps, les gens", None),
    ("raconte-moi une blague sur les soldes légaux", None),
    # bundle 97 — découvrabilité de l'agent-family NEUVE : la
    # question de SURFACE (« a-t-il changé ? ») et celle du JUGE
    # (« va-t-il rejeter ? ») ne doivent jamais se croiser ; le
    # leurre « empreintes digitales » protège le mot FR « empreinte »
    # — un leurre qui route = une fausse promesse (OVERMATCH).
    ("le listing d'outils MCP a changé depuis mon relevé épinglé",
     "mcpsurface"),
    ("did the MCP tools list change since I pinned it — fingerprints",
     "mcpsurface"),
    ("a lista de ferramentas MCP mudou desde a última leitura",
     "mcpsurface"),
    ("LISTING OUTILS MCP A CHANGÉ DÉRIVE EMPREINTE", "mcpsurface"),
    ("mon tools/list a un inputSchema vide — le client va-t-il le "
     "rejeter", "mcpaudit"),
    ("fais-moi une blague sur les empreintes digitales", None),
    # EN : « fingerprints » EST un mot du NOM ssh_fingerprint
    # (poids 4, pluriel plié) — la blague anglaise route, mesuré CE
    # cycle. Ce n'est PAS un leurre libre : douleur OVERMATCH de la
    # famille ssh, consignée à la file, non encodée ici comme « doit
    # mourir » tant que le routeur ne plie pas les formes
    # « tell/joke about » comme il plie « blague ».
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
        # Bundle 72 : le verdict s'appuie sur la LISTE RENVOYÉE, plus
        # sur un score-magasin (l'ancien « <= 5 » datait d'avant T6 :
        # sous le plancher 4 publié, un leurre à 4-5 franchissait la
        # porte comme « leurre-ok »). Un refus = liste vide (ou
        # elsewhere) ; c'est la garantie T6 elle-même, pas un seuil
        # dupliqué dans l'outillage.
        if want is None:
            rec["verdict"] = ("leurre-ok" if (not tools or
                                              body.get("elsewhere"))
                              else "OVERMATCH")
        else:
            hit = any(want.lower() in n.lower() for n in names[:3])
            # TOP1_WRONG (douleur pêchée 14h54) : le bon outil est
            # DANS la liste mais le mauvais est EN TÊTE — l'inversion
            # que la règle top-5 masquait (« -25 % puis -20 % »
            # volé top-1 par check_target via « prix final »).
            rec["verdict"] = ("TOP1_WRONG" if (
                hit and names and want.lower()
                not in names[0].lower()) else
                "ok" if hit else
                ("NO_MATCH" if not tools
                 else "WRONG"))
        rows.append(rec)
        time.sleep(APP_MIN_GAP)
    if has_plan:
        for text, want in CASES[:8]:
            st, body = get(APP + "/api/v1/router/plan",
                           data=json.dumps({"texte": text}).encode(),
                           headers={"Content-Type":
                                    "application/json"})
            presc = body.get("prescription")
            got = (presc.get("fiche") if isinstance(presc, dict)
                   else None) or body.get("fiche") or ""
            rec = {"text": text[:80], "want": want, "via": "plan",
                   "verdict": ("plan-http-%d" % st if st != 200
                               else "ok" if (want is None and
                                             not got) or (want and
                                             want.lower() in
                                             str(got).lower())
                               else "plan-WRONG")}
            rows.append(rec)
            time.sleep(APP_MIN_GAP)
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
    # Bundle 72 : la lecture passe par get() comme le reste — un seul
    # chemin réseau, et le test peut rejouer la sonde hors-ligne.
    st, listing = get(NOUS + "/models",
                      headers={"Authorization": "Bearer " + k})
    try:
        ids = sorted(m["id"] for m in listing["data"])
    except Exception:
        return [{"verdict": "catalog-error",
                 "text": "http-%d" % st}]
    step = max(1, len(ids) // sample)
    picked = ids[::step][:sample]
    out = []
    for mid in picked:
        # Bundle 72 — le verdict doit TYPER l'endpoint. Mesuré 06:22 :
        # google/gemini-embedding-001:batch, appelé en /chat par
        # l'ancienne sonde, renvoyait http-400 — le catalogue mélange
        # les TYPES (chat/embeddings) sans le dire dans l'id ; c'est
        # le piège V23 sous son second jour (listed ≠ invocable ICI).
        embed = "embed" in mid.lower()
        if embed:
            path, probe = "/embeddings", {"model": mid, "input": "OK"}
        else:
            path, probe = "/chat/completions", {
                "model": mid, "stream": False, "max_tokens": 2,
                "messages": [{"role": "user", "content": "OK"}]}
        st, _ = get(NOUS + path, data=json.dumps(probe).encode(),
                    headers={
                        "Authorization": "Bearer " + k,
                        "Content-Type": "application/json"})
        out.append({"text": mid, "want": "embed" if embed else None,
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
        # clé (texte, want) : le corpus contient des lignes au MEME
        # texte avec des volontés différentes — indexé sur le texte
        # seul, le last-write-wins faisait ressortir un NO_MATCH
        # ancien comme « REGRESSION » (artefact mesuré 22-11 21h57,
        # ligne PT loja).
        prev = {(r["text"], r.get("want"), r.get("via")): r["verdict"]
                for r in json.load(open(latest))["rows"]}
    stamp = scan["ts"].replace(":", "-").replace(" ", "_")
    with open(os.path.join(RADAR_DIR, "scan-%s.json" % stamp),
              "w") as fh:
        json.dump(scan, fh, ensure_ascii=False, indent=1)
    with open(latest, "w") as fh:
        json.dump(scan, fh, ensure_ascii=False, indent=1)
    new_pain = [r for r in rows
                if r["verdict"] not in ("ok", "leurre-ok", "plan-skip")
                and prev.get((r["text"], r.get("want"),
                              r.get("via"))) == "ok"]
    fresh = [r for r in rows
             if r["verdict"] not in ("ok", "leurre-ok", "plan-skip")
             and (r["text"], r.get("want"), r.get("via"))
             not in prev]
    healed = [k for k, v in prev.items()
              if v not in ("ok", "leurre-ok", "plan-skip")
              and any((r["text"], r.get("want"), r.get("via")) == k
                      and r["verdict"] in
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
                print("- GUERIE : %r (want %r)" % (it[0][:70], it[1]))

    print("(brut : docs/RADAR/scan-%s.json — local-only)" % stamp)


if __name__ == "__main__":
    main()
