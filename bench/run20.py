# bench v20 — LE VERROU DE CIBLE : le garde promis par v17, mesuré.
#
# v17 a autopsié l'échec du 8B en relais : ZÉRO faute d'arithmétique,
# sept fois « juste mais à côté » — #00 : 160 (vendus l'après-midi)
# pour 240 (ce qui RESTE). Sa promesse, écrite avant de vendre :
# « la réponse exige {"answer": v, "target": nom} et le serveur
# refuse si le target ne correspond pas à la question déclarée ».
# Ce banc mesure cette phrase. Le garde n'est PAS encore dans le
# produit général (les fiches v0.82.0 l'ont, le protocole steps non) :
# ici le rôle du serveur est tenu par le harness, avec le dictionnaire
# des quantités nommées que gen16 possède (qte/cible, gate 22-11 :
# oracles séparés + 3 collisions de valeurs relevées, #07/#12).
#
# Bras (temp 0, seed 42, max 6 pas — le protocole v14 de part en part) :
#   S  skill-relay nu      : {"step": e} → serveur calcule → {"value"}
#                            → … → {"answer": v}. Base de ce banc,
#                            rejouée ici même (pas de cellule recyclée).
#   L  skill-relay + verrou: idem, mais le serveur enrichit chaque
#                            écho : {"value": v, "names": [quantités
#                            de sa chaîne qui valent v]} — et la
#                            réponse finale EXIGE {"answer": v,
#                            "target": nom}. Refus NOMMÉS (doctrine
#                            v14, réparation ×1) :
#                            VOCAB   — nom hors dictionnaire ;
#                            MISMATCH — la valeur n'est pas celle du
#                                     nom choisi (le refus nomme la
#                                     vraie quantité de cette valeur) ;
#                            CIBLE   — quantité valide mais pas celle
#                                     que la question demande.
#                            ok en L = valeur ORACLE et NOM DE LA
#                            CIBLE : un 300 « juste » nommé
#                            sold_afternoon (#12) est une faute.
# Modèles : 8b (la classe mesurée), 7b (témoin de non-dégât),
# 1.5b (le mur de lecture). 0.5b exclus : plafond 2/20 déjà publié
# six fois (v15, F5) — il n'est pas l'objet de ce garde.
#
# PRÉDICTIONS GELÉES AVANT LA PREMIÈRE CELLULE (le scoreur statue) :
#   P1 classe : dans S(8b), au moins 4 échecs sur 10 sont une valeur
#      qui égale une AUTRE quantité nommée de la chaîne (« à côté »,
#      re-mesure de l'autopsie v17 avec le dictionnaire du banc).
#   P2 le verrou convertit : L(8b) ≥ S(8b) + 3 /20.
#   P3 non-dégât : L(7b) ≥ S(7b) − 1 ; le garde ne casse pas celui
#      qui sait déjà viser.
#   P4 le mur reste : L(1.5b) ≤ 11/20 — nommer une cible ne répare
#      pas une lecture absente (v15/F5).
#   P5 coût honnête : tokens/juste L ≤ 1,5 × tokens/juste S (une
#      réparation par cellule au plus, pas un second protocole).
# Si une prédiction tombe, FINDINGS-V20 la nomme avec les lignes.
import json
import re
import sys
import time

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
from gen16 import problems
from run12 import MODELS
from run14 import SKILL, chat_msghist, calc_live, run_skill
from run16 import norm_num

OUT = "/Users/vincenzocirilli/Downloads/mechacut/bench/" \
      "results_v20_target_lock.jsonl"

_A1 = '  {"answer": "<value>"}                      — when the last '\
      'value IS\n                                               the ' \
      'answer'
_A2 = '  {"answer": "<value>", "target": "<name>"}  — name MUST be a\n'\
      '                                               quantity the '\
      'server echoed\n                                               ' \
      'in its "names"'
_C1 = "3. When a value equals what the question asked, send " \
      "{\"answer\": ...}."
_C2 = "3. When done, send {\"answer\": value, \"target\": NAME} where " \
      "NAME is one of the \"names\" the server echoed for that value " \
      "and is the quantity the question asks for."
assert _A1 in SKILL and _C1 in SKILL, ("SKILL v14 a dérivé — figer le "
                                       "diff avant de jouer quoi que ce "
                                       "soit")
SKILL_L = SKILL.replace(_A1, _A2).replace(_C1, _C2)

ERR_L = ('{"error": "protocol: reply EXACTLY {\\"step\\": \\"<expression'
         '\\"} or {\\"answer\\": \\"<value>\\", \\"target\\": \\"<name>'
         '\\"} — nothing else"}')


def names_for(qte, val):
    """Les quantités de la chaîne qui valent val (tolérance du banc,
    0,005). Ordre de génération = ordre du dictionnaire : la 1re
    collision nommée est #07/#12, relevées par le gate."""
    try:
        f = float(val)
    except (TypeError, ValueError):
        return []
    return [k for k, v in qte.items() if abs(float(v) - f) < 0.005]


def lock_verdict(qte, cible, val, name):
    """Le garde, pur et muet — (ok, refus, vrai_nom_si_connus)."""
    if not isinstance(name, str) or name not in qte:
        return False, "VOCAB", None
    try:
        f = float(val)
    except (TypeError, ValueError):
        return False, "VOCAB", None
    real = names_for(qte, f)
    if abs(float(qte[name]) - f) >= 0.005:
        return False, "MISMATCH", (real[0] if real else None)
    if name != cible:
        return False, "CIBLE", None
    return True, None, None


def refusal_text(kind, val, name, cible, qte, real):
    if kind == "VOCAB":
        return ('{"error": "target \\"%s\\" is not a quantity of this '
                'chain; choose a name the server echoed in \\"names\\"'
                ' — the question asks for \\"%s\\""}' % (name, cible))
    if kind == "MISMATCH":
        if real:
            return ('{"error": "you sent %s as \\"%s\\" but \\"%s\\" '
                    'equals %s here; what you sent is the quantity '
                    '\\"%s\\" — recompute \\"%s\\""}'
                    % (val, name, name, qte[name], real, cible))
        return ('{"error": "%s matches no quantity of the trace; the '
                'answer must be a value the server computed — '
                'recompute \\"%s\\""}' % (val, cible))
    return ('{"error": "\\"%s\\" is a real quantity but not the '
            'question\'s target; the question asks for \\"%s\\" — '
            'send its value under that name"}' % (name, cible))


def run_lock(model, q, qte, cible):
    """Le protocole v14 + verrou. Boucle calquée sur run14.run_skill
    (mêmes gabarits, même réparation unique, même budget de 6 pas)."""
    msgs = [{"role": "system", "content": SKILL_L},
            {"role": "user", "content": q}]
    steps, tokens, secs, repaired = [], 0, 0.0, 0
    last = None
    while len(steps) < 6:
        text, tok, sec = chat_msghist(model, msgs)
        tokens += tok
        secs += sec
        m = re.search(r"\{.*\}", text, re.S)
        obj = None
        if m:
            try:
                obj = json.loads(m.group(0))
            except Exception:
                obj = None
        if not isinstance(obj, dict):
            if repaired:
                return steps, "protocol_giveup", None, tokens, secs
            repaired += 1
            msgs.append({"role": "assistant", "content": text})
            msgs.append({"role": "user", "content": ERR_L})
            continue
        if "answer" in obj:
            if set(obj) != {"answer", "target"}:
                if repaired:
                    return steps, "protocol_giveup", None, tokens, secs
                repaired += 1
                msgs.append({"role": "assistant",
                             "content": json.dumps(obj)})
                msgs.append({"role": "user", "content": ERR_L})
                continue
            ok, kind, real = lock_verdict(qte, cible,
                                          obj.get("answer"),
                                          obj.get("target"))
            steps.append({"answer": str(obj.get("answer"))[:40],
                          "target": str(obj.get("target"))[:40],
                          "lock": kind or "OK"})
            last = (ok, kind, real, obj)
            if ok or repaired:
                break
            repaired += 1
            msgs.append({"role": "assistant",
                         "content": json.dumps(obj)})
            msgs.append({"role": "user", "content": refusal_text(
                kind, obj.get("answer"), obj.get("target"), cible,
                qte, real)})
            continue
        if "step" not in obj or len(obj) != 1:
            if repaired:
                return steps, "protocol_giveup", None, tokens, secs
            repaired += 1
            msgs.append({"role": "assistant",
                         "content": json.dumps(obj)})
            msgs.append({"role": "user", "content": ERR_L})
            continue
        expr = str(obj["step"])[:120]
        if not re.fullmatch(r"[0-9+\-*/().\s]+", expr):
            if repaired:
                return steps, "step_not_closed", None, tokens, secs
            repaired += 1
            msgs.append({"role": "assistant",
                         "content": json.dumps(obj)})
            msgs.append({"role": "user", "content":
                         '{"error": "step must contain only digits '
                         'and + - * / ( )"}'})
            continue
        val, err = calc_live(expr)
        if err:
            return steps, "calc_refused:" + expr[:30], last, tokens, secs
        steps.append({"step": expr, "value": val})
        nm = names_for(qte, val)
        msgs.append({"role": "assistant",
                     "content": json.dumps(obj)})
        msgs.append({"role": "user", "content":
                     '{"value": "%s", "names": %s}' % (val,
                                                       json.dumps(nm))})
    if last is None:
        return steps, "max_steps", None, tokens, secs
    ok, kind, real, obj = last
    err = None if ok else ("refus_final_" + str(kind))
    return steps, err, last, tokens, secs


def one(model_key, arm, t):
    mk = MODELS[model_key]
    t0 = time.time()
    if arm == "S":
        steps, err, tok, sec = run_skill(mk, t["text"])
        ans = steps[-1].get("answer") if steps else None
        got = norm_num(ans)
        ok = got is not None and abs(got - float(t["gold"])) < 0.005
        return ok, got, None, err, tok, sec, steps
    steps, err, last, tok, sec = run_lock(mk, t["text"], t["qte"],
                                          t["cible"])
    if last is None:
        return False, None, None, err, tok, sec, steps
    ok, kind, real, obj = last
    got = norm_num(obj.get("answer"))
    return ok, got, str(obj.get("target"))[:40], err, tok, sec, steps


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        q = {"total": 100, "sold": 40, "remaining": 60}
        c = "remaining"
        assert lock_verdict(q, c, "60", "remaining") == (True, None,
                                                          None)
        assert lock_verdict(q, c, "40", "remaining")[1] == "MISMATCH"
        assert lock_verdict(q, c, "40", "sold")[1] == "CIBLE"
        assert lock_verdict(q, c, "40", "extra")[1] == "VOCAB"
        assert lock_verdict(q, c, "99", "remaining")[1] == "MISMATCH"
        print("selftest verrou: PASS (VOCAB/MISMATCH/CIBLE/OK)")
        sys.exit(0)
    qs = problems()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = [a for a in args if a in MODELS] or ["8b", "7b", "1.5b"]
    cap = int(next((a for a in args if a not in MODELS), 0)) or None
    done = set()
    try:
        for l in open(OUT):
            r = json.loads(l)
            done.add((r["model"], r["i"], r["arm"]))
    except FileNotFoundError:
        pass
    print("déjà faites:", len(done), "/ 120 — matrice 3 modèles × 2 "
          "bras × 20", flush=True)
    n = 0
    with open(OUT, "a", encoding="utf-8") as fh:
        for mk in only:
            for t in qs:
                for arm in ("S", "L"):
                    if (mk, t["i"], arm) in done:
                        continue
                    if cap and n >= cap:
                        print("cap atteint (%d) — reprisable" % cap,
                              flush=True)
                        sys.exit(0)
                    ok, got, target, err, tok, sec, steps = \
                        one(mk, arm, t)
                    fh.write(json.dumps({
                        "harness": "v20-target-lock", "model": mk,
                        "i": t["i"], "family": t["family"],
                        "arm": arm, "ok": ok, "got": got,
                        "gold": float(t["gold"]), "target_used": target,
                        "cible": t["cible"], "err": err,
                        "tokens": tok, "secs": round(sec, 2),
                        "trace": json.dumps(steps,
                                            ensure_ascii=False)[:400]},
                        ensure_ascii=False) + "\n")
                    fh.flush()
                    n += 1
                    print("%-4s %s #%02d %s tok=%d %s" % (
                        mk, arm, t["i"], "✓" if ok else "✗", tok,
                        err or ""), flush=True)
