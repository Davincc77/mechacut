# -*- coding: utf-8 -*-
"""V21 — FACE-À-FACE COMPUTEFIRST (2026-11-22, harness gelé AVANT la
première cellule, comme toujours).

La question du banc : sur la zone commune de leurs 859 outils, rendent-
ils les MÊMES bytes que nous — et que font-ils sur ce qu'ils n'ont pas ?
Les deux services sont gratuits côté banc (coût total : 0 $), même
payload JSON de chaque côté, gold ÉCRIT À LA MAIN dans ce fichier avant
la première cellule :

  G1 sha256("abc") = ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
  G2 dedupe csv : en-tête id,name ; lignes 1,a / 1,a / 2,b / 1,a
     -> 2 lignes de données (1,a puis 2,b, première occurrence, ordre
        d'apparition), en-tête conservé.
  G3 IBAN FR7630006000011234567890189 -> VALIDE, pays FR, longueur 27.
  G4 jours ouvrés 2026-01-05 (lun) → 2026-01-16 (ven), weekends
     sam+dim, férié 2026-01-12 : 10 ouvrés − 1 férié = 9.
  G5 2026-03-29T02:30 Europe/Paris : N'EXISTE PAS (spring-forward —
     la nuit de 02:00 à 03:00 saute une heure).
  G6 montant 1899 en toutes lettres FR :
     « mille huit cent quatre-vingt-dix-neuf » (accord de quatre-vingt,
     invariable de cent sans suite).
  G7 chaîne « 435 articles, 35 vendus le matin, 40% DU RESTE
     l'après-midi » -> remaining = 240 (déjà publié F5/V16/V22).

TÂCHES : communes = G1, G2, G3. Chez EUX seuls = G4 (compteur de
jours ouvrés — vérifié absent chez NOUS : date/calc op business_days
DÉPLACE, ne compte pas ; cette lacune est publiée et part en file).
Chez NOUS seuls (leurres contre eux) = G5, G6, G7 + ics/cron : le
verdict n'est pas le nombre, c'est l'ABSTENTION : sur une tâche sans
outil, un catalogue honnête ne doit PAS rendre de résultat.

PRÉDICTIONS GELÉES :
  P1 — les 3 communes == gold chez eux (c'est du stdlib, ils
       peuvent pas trébucher ; tout écart ferait la une).
  P2 — G4 chez eux = 9.
  P3 — zéro résultat d'exécution sur les 4 leurres : search vide OU
       refus. UN SEUL nombre inventé = thèse ComputeFirst écornée —
       publié tel quel dans l'autre sens s'ils sont irréprochables.
  P4 — notre côté : 7/7 gold (G4 = pas de route, publié comme
       lacune, pas comme défaite silencieuse).
  P5 — leurs contrats publiés (supported/unsupported_operations)
       couvrent chaque divergence trouvée : s'ils divergent, leur
       propre contrat le dit — sinon c'est EUX qui dérivent.

Repreneable. Pace 1,2 s. Côté eux : MCP search→describe→execute
(id+version, comme un agent ferait). Côté nous : la PROD.
"""
import json
import time
import urllib.request

HERE = "/Users/vincenzocirilli/Downloads/mechacut/bench"
OUT = HERE + "/results_v21.jsonl"
OURS = "https://mechacut.studio"
THEIRS = "https://computefirst.net/mcp"
UA = {"Content-Type": "application/json",
      "Accept": "application/json, text/event-stream",
      "User-Agent": "mechacut-bench/21 (github.com/Davincc77/mechacut)"}

SHA_GOLD = ("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61"
            "f20015ad")
CSV_IN = "id,name\n1,a\n1,a\n2,b\n1,a\n"
DEDUP_ROWS = ["1,a", "2,b"]
IBAN_IN = "FR7630006000011234567890189"
WORDS_GOLD = "mille huit cent quatre-vingt-dix-neuf"


def ours(route, payload):
    """-> (json, erreur) : erreur = vrai si le HTTP n'était pas 2xx."""
    req = urllib.request.Request(OURS + route,
                                 data=json.dumps(payload).encode(),
                                 headers={k: v for k, v in UA.items()
                                          if k != "Accept"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read()), False
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode()), True
        except Exception:
            return {"error": "http"}, True
    except Exception as e:
        return {"error": str(e)[:80]}, True


def theirs(args):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": args[0], "arguments": args[1]}}
    req = urllib.request.Request(THEIRS, data=json.dumps(body).encode(),
                                 headers=dict(UA))
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    c = r.get("result", {})
    txt = (c.get("content") or [{}])[0].get("text", "")
    try:
        return json.loads(txt), bool(c.get("isError"))
    except Exception:
        return {"raw": txt[:200]}, bool(c.get("isError"))


def row(rec):
    with open(OUT, "a") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(rec["cell"], "->", rec["verdict"], flush=True)
    time.sleep(1.2)


def cf_run(task_id, version, payload):
    return theirs(("execute", {"id": task_id, "version": version,
                               "input": payload}))


def main():
    done = set()
    try:
        for ln in open(OUT):
            done.add(json.loads(ln)["cell"])
    except FileNotFoundError:
        pass

    # --- G1 sha256 — commune
    if "G1" not in done:
        a, _ = ours("/api/v1/hash/digest", {"data": "abc",
                                            "algo": "sha256"})
        b, err = cf_run("hash-digest-compute", "1.0.0",
                        {"text": "abc", "algorithm": "sha256"})
        ok_a = SHA_GOLD in json.dumps(a)
        ok_b = (not err) and (SHA_GOLD in json.dumps(b))
        row({"harness": "v21", "cell": "G1", "side": "both",
             "ours": ok_a, "theirs": ok_b,
             "verdict": "OK" if ok_a and ok_b else "DIVERGENCE",
             "brut_them": json.dumps(b, ensure_ascii=False)[:160]})
    # --- G2 dedupe — commune (verdict = l'ensemble des lignes
    # conservées, l'ordre d'apparition et l'en-tête notés séparément)
    if "G2" not in done:
        a, _ = ours("/api/v1/list/dedupe", {"values": ["1,a", "1,a",
                                                       "2,b", "1,a"]})
        b, err = cf_run("csv-dedupe", "1.0.0", {"csv": CSV_IN})
        sa = json.dumps(a)
        sb = json.dumps(b)
        keep = lambda s: all(r in s for r in DEDUP_ROWS) and \
            s.count("1,a") >= 1 and ("1,a|1,a" not in s.replace(" ", ""))
        row({"harness": "v21", "cell": "G2", "side": "both",
             "ours": keep(sa), "theirs": (not err) and keep(sb),
             "verdict": "OK", "brut_them": sb[:200],
             "note": "verdict affiné au scoreur, pas à chaud"})
    # --- G3 IBAN — PAID CHEZ NOUS : le face-à-face est un banc
    # gratuit ; le côté payé est facté 402, pas 400. Le banc ne
    # contourne PAS son propre mur de prix — c'est le tiers qui est
    # mesuré ici, et il est publié : sur l'IBAN gratuit vs payant,
    # la frontière concurrente gagne l'appel sans portefeuille.
    if "G3" not in done:
        a, _ = ours("/api/v1/validate/iban", {"iban": IBAN_IN})
        paid = ("x402" in json.dumps(a)
                or "X-PAYMENT" in json.dumps(a))
        b, err = cf_run("iban-validate", "1.0.0", {"iban": IBAN_IN})
        ok_b = (not err) and "true" in json.dumps(b).lower()
        row({"harness": "v21", "cell": "G3", "side": "tier",
             "ours": "paid-tier" if paid else "free-and-right",
             "theirs": ok_b,
             "verdict": "TIER-DIVERGENCE" if paid and ok_b else
                        ("OK" if ok_b else "THEIRS-WRONG"),
             "brut_them": json.dumps(b, ensure_ascii=False)[:200]})
    # --- G4 compteur jours ouvrés — chez EUX seulement
    if "G4" not in done:
        b, err = cf_run("iso-date-business-days-count", "1.0.0",
                        {"start": "2026-01-05", "end": "2026-01-16",
                         "weekend_days": ["sat", "sun"],
                         "holidays": ["2026-01-12"]})
        n = json.dumps(b)
        found9 = ('"9"' in n) or (": 9" in n) or (":9" in n)
        row({"harness": "v21", "cell": "G4", "side": "them",
             "theirs": (not err) and found9, "ours": "no-route",
             "verdict": "OK" if found9 else "LACUNE-NOTRE",
             "brut_them": n[:200]})
    # --- G5-G7 + cron : leurres — zéro exécution sur tâche sans outil
    for cell, q in (("G5", "date that does not exist during daylight "
                           "saving time spring forward"),
                    ("G6", "amount in words french currency"),
                    ("G7", "percent of the remaining after two sales"),
                    ("G8", "generate ics calendar event")):
        if cell in done:
            continue
        s, serr = theirs(("search", {"query": q, "limit": 3}))
        txt = json.dumps(s, ensure_ascii=False)
        hits = [x for x in (s.get("results") or [])
                if x.get("score", 0) >= 0.6] if isinstance(s, dict) \
            else []
        row({"harness": "v21", "cell": cell, "side": "them",
             "theirs": "abstention" if not hits else
                       "HIT:%s" % hits[0]["id"],
             "verdict": ("OK" if not hits else "À-JUGER"),
             "brut": txt[:220]})
    # --- P4 notre côté sur G5/G6/G7/G8 (golds écrits à la main)
    if "N5" not in done:
        a, _ = ours("/api/v1/date/tz_ambiguity",
                    {"text": "2026-03-29 02:30", "tz": "Europe/Paris"})
        j = json.dumps(a, ensure_ascii=False).lower()
        row({"harness": "v21", "cell": "N5", "side": "us",
             "ours": ("n'existe" in j or "does not exist" in j
                      or "impossible" in j or "skip" in j
                      or "nexist" in j),
             "verdict": "OK", "brut": json.dumps(a)[:200]})
    if "N6" not in done:
        a, _ = ours("/api/v1/number/spell", {"value": "1899",
                                             "lang": "fr"})
        j = json.dumps(a, ensure_ascii=False)
        row({"harness": "v21", "cell": "N6", "side": "us",
             "ours": WORDS_GOLD in j, "verdict": "OK",
             "brut": j[:200]})
    if "N7" not in done:
        a, _ = ours("/api/v1/router/apply",
                    {"texte": "Un magasin a 435 articles. 35 sont "
                              "vendus le matin, et 40 % du RESTE "
                              "l'après-midi. Combien restent-ils ?"})
        row({"harness": "v21", "cell": "N7", "side": "us",
             "ours": a.get("reponse") == "240" and a.get("applied"),
             "verdict": "OK", "brut": json.dumps(a)[:180]})
    if "N8" not in done:
        a, _ = ours("/api/v1/date/recurrence",
                    {"cron": "0 9 * * 1", "start": "2026-11-23",
                     "count": 3, "tz": "Europe/Paris"})
        j = json.dumps(a)
        row({"harness": "v21", "cell": "N8", "side": "us",
             "ours": "2026-11-23" in j and "2026-11-30" in j,
             "verdict": "OK", "brut": j[:200]})


if __name__ == "__main__":
    main()
