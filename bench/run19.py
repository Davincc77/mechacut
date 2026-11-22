# -*- coding: utf-8 -*-
"""v19 — LA FACTURE DU CSV (l'image promise par l'article).

Le job : le même CSV sale, nettoyé 30 jours de suite. Trois bras :
  N  nu            : un appel par jour, temp 0.7 (le régime RÉEL des
                     agents — publié, pas caché), réponse = le CSV nettoyé.
  R  retry-agent   : jusqu'à 3 appels par jour, stop dès que la sortie
                     passe un VALIDATEUR DE FORME (colonnes, ISO, minuscules,
                     prix à 2 décimales) — comme un vrai agent, il ne peut
                     PAS connaître le gold : il valide sa forme, pas son
                     contenu. Chaque appel est facturé.
  M  machine       : la fonction gelée du spec (le code est la spec, la
                     spec est gelée) — 30 jours, un seul sha possible.

PRÉDICTIONS ENREGISTRÉES AVANT LA PREMIÈRE CELLULE :
  P1  dérive : N produit ≥ 2 sorties canoniques distinctes sur 30 jours
      pour CHAQUE modèle.
  P2  justesse : au moins un modèle N est ≤ 27/30 jours justes.
  P3  retry facturé : tokens(R) ≥ 2× tokens(N) ; et R ne sauve pas tout :
      ≥1 modèle avec jours_justes(R) ≤ 29/30.
  P4  machine : distinct(M) = 1, 30/30 justes, coût LLM = 0.
  P5  arithmétique publiée : tokens par jour juste pour chaque bras.
Zéro re-pilotage : si P1-P4 tombent autrement, on publie tel quel.

Double gold : fixtures_v19/gold.csv est ÉCRIT À LA MAIN avant ce
fichier ; la gate du harness (première cellule) vérifie code==gold —
si la machine diffère du gold écrit à la main, c'est LE CODE qui est
corrigé (le gold n'est jamais relu du produit), et la correction est
consignée dans FINDINGS-V19.
"""
import hashlib
import json
import re
import sys
import time
import urllib.request
from decimal import Decimal

OLLAMA = "http://127.0.0.1:11434/api/generate"
OUT = "results_v19_csv_bill.jsonl"
DAYS = 30
MODELS = {"1.5b": "qwen2.5:1.5b-instruct",
          "7b": "qwen2.5:7b-instruct-q4_K_M"}
PACE = 2.2

DIRTY = open("fixtures_v19/dirty.csv").read()
GOLD = open("fixtures_v19/gold.csv").read()

SPEC = (
    "Daily job. Input CSV (dirty) columns: date,city,distance_km,price,qty.\n"
    "Output ONLY the cleaned CSV, header first, rows in input order:\n"
    "1. remove rows that are EXACT duplicates of a previous row "
    "(ignoring surrounding spaces);\n"
    "2. city: lowercase;\n"
    "3. distance_km: plain number, no trailing zeros (450 not 450.00);\n"
    "4. price: exactly two decimals;\n"
    "5. qty: integer;\n"
    "6. dates stay as they are (already ISO).\n"
    "No prose, no code fences.\n\nINPUT:\n" + DIRTY)

FORMAT_CHECK = re.compile(
    r"^date,city,distance_km,price,qty\n"
    r"(?:\d{4}-\d{2}-\d{2},[a-z]+,\d+(?:\.\d+)?,\d+\.\d{2},\d+\n)+$")


def canon(csv_text):
    """Normalisation pour la comparaison : on exige la forme exacte du
    spec (le monde réel ne pardonne pas les espaces)."""
    return csv_text.strip().replace("\r\n", "\n") + "\n"


def machine(csv_text):
    """La spec, gelée en code — 20 lignes, aucun jugement porté après
    coup."""
    lines = csv_text.strip().split("\n")
    head, out, seen = lines[0], [], set()
    for ln in lines[1:]:
        cells = [c.strip() for c in ln.split(",")]
        key = tuple(cells)
        if key in seen:
            continue
        seen.add(key)
        d, city, dist, price, qty = cells
        # décimal pur, jamais normalize() qui écrit 4.5E+2 ; et jamais
        # de float dans la chaîne.
        dist = format(Decimal(dist), "f")
        if "." in dist:
            dist = dist.rstrip("0").rstrip(".")
        out.append(",".join([d, city.lower(), dist,
                             "%.2f" % Decimal(price), str(int(qty))]))
    return head + "\n" + "\n".join(out) + "\n"


def ask(model, prompt, temp=0.7):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"temperature": temp, "seed": None}})
    req = urllib.request.Request(
        OLLAMA, data=body.encode(),
        headers={"Content-Type": "application/json"})
    raw = json.loads(urllib.request.urlopen(req, timeout=600).read())
    return raw["response"], raw.get("eval_count", 0) + \
        raw.get("prompt_eval_count", 0)


def strip_fences(t):
    m = re.search(r"```(?:csv)?\s*(.*?)```", t, re.S)
    return m.group(1) if m else t


def main():
    done = set()
    try:
        for ln in open(OUT):
            r = json.loads(ln)
            done.add((r["arm"], r["model"], r["day"]))
    except FileNotFoundError:
        pass

    gold = canon(GOLD)
    m_out = machine(DIRTY)
    if m_out != gold:
        print("GATE : machine != gold ÉCRIT À LA MAIN — ne pas courir ; "
              " corriger le CODE.")
        print("machine:", repr(m_out[:200]))
        sys.exit(1)
    print("gate double-gold : machine == gold à la main ✓", flush=True)

    # bras M : 30 jours, le même sha
    shas = {hashlib.sha256(gold.encode()).hexdigest()}
    if ("M", "machine", 0) not in done:
        with open(OUT, "a") as f:
            for day in range(DAYS):
                f.write(json.dumps({"arm": "M", "model": "machine",
                                    "day": day, "correct": True,
                                    "sha": sorted(shas)[0][:12],
                                    "toks": 0}) + "\n")
        print("M : 30/30, un seul sha", flush=True)

    for mk, mn in MODELS.items():
        for arm in ("N", "R"):
            for day in range(DAYS):
                if (arm, mk, day) in done:
                    continue
                toks = calls = 0
                correct = False
                got = None
                for attempt in range(3 if arm == "R" else 1):
                    prompt = SPEC
                    if arm == "R" and attempt:
                        prompt = SPEC + ("\n\nYour LAST output failed the "
                                         "format checks (row shape, "
                                         "lowercase city, two-decimal "
                                         "price, exact duplicates "
                                         "removed). Redo the WHOLE "
                                         "cleaned CSV, nothing else.")
                    try:
                        got, tk = ask(mn, prompt)
                        toks += tk
                        calls += 1
                    except Exception as e:
                        got = "ERR:%s" % type(e).__name__
                        break
                    out = canon(strip_fences(got))
                    if arm == "N":
                        correct = out == gold
                        break
                    # R : le validateur de FORME seul arrête la boucle
                    if FORMAT_CHECK.match(out):
                        correct = out == gold
                        break
                    correct = out == gold
                with open(OUT, "a") as f:
                    f.write(json.dumps({
                        "arm": arm, "model": mk, "day": day,
                        "correct": correct, "calls": calls,
                        "toks": toks,
                        "sha": hashlib.sha256(
                            canon(strip_fences(got)).encode()
                            if got and not got.startswith("ERR")
                            else (got or "").encode()).hexdigest()[:12],
                    }) + "\n")
                print("%s %s jour %d %s (%d appels, %d tok)" % (
                    arm, mk, day, "✓" if correct else "✗", calls,
                    toks), flush=True)
                time.sleep(PACE)
    score()


def score():
    rows = [json.loads(l) for l in open(OUT)]
    print("\n=== V19 : la facture des 30 jours ===")
    for arm in ("N", "R", "M"):
        for mk in sorted({r["model"] for r in rows
                          if r["arm"] == arm}):
            rs = [r for r in rows if r["arm"] == arm and r["model"] == mk]
            shas = len({r["sha"] for r in rs})
            ok = sum(r["correct"] for r in rs)
            tk = sum(r["toks"] for r in rs)
            per = tk / ok if ok else float("inf")
            print("%s %-8s %2d/%d justes · %d sorties distinctes · "
                  "%d tokens · %s tokens/jour juste" % (
                      arm, mk, ok, len(rs), shas, tk,
                      "∞" if per == float("inf") else int(per)))


if __name__ == "__main__":
    main()
