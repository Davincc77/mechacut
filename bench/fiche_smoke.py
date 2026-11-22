# Smoke F5 : le 0.5B ne décompose plus, il recopie des créneaux.
# Critère pré-enregistré (docs/F5) : 4/4 sur 4 problèmes à chaîne —
# 2 shop_reste, 1 partage_reste, 1 soldes2 — sinon la fiche est morte.
import json
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "..")
OLLAMA = "http://127.0.0.1:11434/api/generate"
APP = "http://127.0.0.1:8899"

CASES = [
    # (fiche, texte du problème, créneaux attendus — golds v16/v15)
    ("shop-reste",
     "Un magasin a 435 articles. Il en vend 35 le matin, puis 40 % du "
     "reste l'après-midi. Combien lui reste-t-il d'articles ?",
     {"total": "435", "sold_morning": "35", "pct_afternoon": "40%"},
     "remaining", "240"),
    ("shop-reste",
     "Une bibliothèque prête 63 livres un lundi, puis 40 % du reste le "
     "mardi. Elle avait 263 livres. Combien lui en reste-t-il ?",
     {"total": "263", "sold_morning": "63", "pct_afternoon": "40%"},
     "remaining", "120"),
    ("partage-reste",
     "Trois héritiers se partagent 3829 euros. Le premier reçoit 2/5 "
     "de la somme, le second reçoit 1/6 du reste. Combien reçoit le "
     "second ?",
     {"total": "3829", "first_part": "2/5", "second_of_rest": "1/6"},
     "second_share", "382.90"),
    ("soldes2",
     "Un article à 81,90 euros est soldé de 25 %, puis d'une remise "
     "immédiate de 20 %. Quel est le prix final ?",
     {"price": "81.90", "pct1": "25%", "pct2": "20%"},
     "final", "49.14"),
]

CARD = ("Tu ne CALCULES RIEN. Tu recopies les nombres du problème, "
        "exactement écrits, dans ces créneaux : %s. Réponds UNIQUEMENT "
        "par un objet JSON des créneaux, rien d'autre.\n\n%s")


SLOTDOC = {
    "shop-reste": ["total", "sold_morning", "pct_afternoon"],
    "partage-reste": ["total", "first_part", "second_of_rest"],
    "soldes2": ["price", "pct1", "pct2"]}


def slot_fill(fiche, text):
    slots_doc = SLOTDOC[fiche]
    prompt = CARD % (", ".join('"%s"' % s for s in slots_doc), text)
    body = json.dumps({"model": "qwen2.5:0.5b-instruct",
                       "prompt": prompt, "stream": False,
                       "options": {"temperature": 0, "seed": 42}})
    req = urllib.request.Request(
        OLLAMA, data=body.encode(),
        headers={"Content-Type": "application/json"})
    raw = json.loads(urllib.request.urlopen(req, timeout=180).read()
                     )["response"]
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None, raw
    try:
        return json.loads(m.group(0)), raw
    except Exception:
        return None, raw


def call_fiche(fiche, slots):
    req = urllib.request.Request(
        APP + "/api/v1/fiche/" + fiche,
        data=json.dumps({"slots": slots}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        # 400 = refus nommé du serveur : c'est DONNÉE, pas accident.
        return json.loads(e.read().decode())


ok = 0
for fiche, text, expect_slots, target, gold in CASES:
    got, raw = slot_fill(fiche, text)
    verdict = "PARSE-ÉCHOUÉ"
    repairs = 0
    for _ in range(2):                  # 1re tentative + 1 réparation
        if not got:
            break
        out = call_fiche(fiche, got)
        if "errors" in out:             # l'erreur-qui-répare (v14)
            err = out["errors"][0]
            verdict = "RÉPARE"
            reprompt = (CARD % (", ".join('"%s"' % s
                                          for s in SLOTDOC[fiche]),
                                text)) + \
                "\n\nLe serveur a REFUSÉ : %s (%s). Corrige uniquement " \
                "ce créneau." % (err.get("field"), err.get("expected"))
            body = json.dumps(
                {"model": "qwen2.5:0.5b-instruct", "prompt": reprompt,
                 "stream": False,
                 "options": {"temperature": 0, "seed": 42}})
            req2 = urllib.request.Request(
                OLLAMA, data=body.encode(),
                headers={"Content-Type": "application/json"})
            raw2 = json.loads(
                urllib.request.urlopen(req2, timeout=180).read())
            m = re.search(r"\{.*\}", raw2["response"], re.S)
            repairs += 1
            try:
                got = json.loads(m.group(0)) if m else None
            except Exception:
                got = None
            continue
        val = out["answer"][target]
        verdict = "OK" if val == gold else "FAUX %s≠%s" % (val, gold)
        break
    ok += verdict == "OK"
    print("%-14s %-14s repaires=%d slots=%s" % (fiche, verdict,
                                                repairs, got), flush=True)
    time.sleep(1.0)

print("SMOKE F5 : %d/4" % ok)
sys.exit(0 if ok == 4 else 1)
