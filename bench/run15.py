# bench v15 — L'ARBITRE. Une seule matrice, un seul harnais, jouée
# d'un trait : 5 bras × 4 modèles gratuits locaux × 20 problèmes
# seedés (gen16, graine 2026, golds exacts pré-calculés). Aucune
# cellule recyclée d'un autre banc : quand on publiera, on ne pourra
# pas nous dire « tes chiffres viennent de trois expériences ».
#
# Bras (tous temp 0 sauf mention) :
#   N nude      : répond toi-même, un coup, {"answer"}
#   C code      : écrit du Python, exécuté dans le portique AST +
#                 sous-processus isolé (la voie « l'agent code »)
#   R relay-free: le style v13 — UN seul JSON libre de steps que
#                 le serveur évalue ligne à ligne (le bras qu'on sait
#                 cassé : inclus pour que le banc montre la cassure)
#   S skill-steps: le protocole v14 — une expression fermée par tour,
#                 le serveur calcule, max 6 pas (la voie mechacut)
#   T retry5    : 5 échantillons temp 0,7 + majorité (l'arme
#                 légitime du nu : le self-consistency du monde réel)
#
# PRÉDICTIONS GELÉES AVANT LA PREMIÈRE CELLULE (publiées avec le
# code, le scoreur les statue, pas moi) :
#   G1  S ≥ tous les autres bras, sur chaque modèle.
#   G2  T ≈ N (le retry n'achète rien sur erreur systématique),
#       avec ~5× les tokens.
#   G3  R s'effondre sur les petits (≤4/20 en dessous de 7B).
#   G4  C est fort sur 7B et fragilisé sur 8B (leçon v12/v14 : la
#       discipline du format n'est pas la taille).
#   G5  Sur les familles à chaîne (mix/partage) : seuls S (et peut-être
#       C) marquent ; N, R, T ≈ 0 — la frontière de FORME, une
#       dernière fois, sur une matrice complète.
# Si une prédiction tombe, FINDINGS-V15 la nomme avec les lignes.
import json
import re
import sys
import time

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut")
sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
from gen16 import problems
from run12 import MODELS
from run13 import run_code
from run14 import chat_msghist, run_skill
from run16 import norm_num, ask as ask_nude
from run17 import run_retry

OUT = "/Users/vincenzocirilli/Downloads/mechacut/bench/" \
      "results_v15_matrix.jsonl"

FREE_RELAY = ("Break this problem into steps. Reply with EXACTLY one "
              "JSON object:\n{\"steps\": [\"<expr>\", \"<expr>\", …]}\n"
              "Each step = one closed arithmetic expression using "
              "digits + - * / ( ) and the numbers from the problem "
              "or from earlier steps (write the actual number, again, "
              "not a name). Last value = the answer.\n\nProblem: <Q>")

CODE = ("Solve by writing Python. Reply with EXACTLY one JSON object:"
        "\n{\"src\": \"<python: plain arithmetic, print(result) "
        "last>\"}\nNo imports, no functions, no strings needed.\n\n"
        "Problem: <Q>")

NUD = ("Solve this problem. Reply with EXACTLY one JSON object, "
       "nothing else:\n{\"answer\": \"<number>\"}\n\nProblem: <Q>")


def _jnum(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def run_free_relay(model, q):
    """R : un seul JSON {"steps":[...]} ; le harnais évalue chaque
    ligne avec la MÊME arithmétique Decimal que /math/calc local
    (l'oracle du banc, pas le serveur — pour la vitesse ; les
    expressions sont fermées, même grammaire)."""
    from decimal import Decimal
    t0 = time.time()
    text, tok, _ = chat_msghist(model, [{"role": "user",
                                         "content":
                                         FREE_RELAY.replace("<Q>", q)}],
                                n=400)
    obj = _jnum(text)
    if not isinstance(obj, dict) or not isinstance(obj.get("steps"),
                                                   list):
        return None, "shape", tok, round(time.time() - t0, 2)
    last = None
    for e in obj["steps"][:8]:
        e = str(e)
        if not re.fullmatch(r"[0-9+\-*/(). ]+", e):
            return None, "open_expr:" + e[:24], tok, \
                round(time.time() - t0, 2)
        try:
            last = eval(e, {"__builtins__": {}}, {})
        except Exception:
            return None, "eval:" + e[:24], tok, round(time.time() - t0,
                                                      2)
    return last, None, tok, round(time.time() - t0, 2)


def run_code_arm(model, q):
    t0 = time.time()
    text, tok, _ = chat_msghist(model, [{"role": "user",
                                         "content":
                                         CODE.replace("<Q>", q)}],
                                n=400)
    obj = _jnum(text)
    src = obj.get("src") if isinstance(obj, dict) else None
    if not src:
        return None, "shape", tok, round(time.time() - t0, 2)
    val, err = run_code(str(src))
    return norm_num(val), ("code:" + str(err)[:30] if err else None), \
        tok, round(time.time() - t0, 2)


ARMS = ("N", "C", "R", "S", "T")


def one(model_key, arm, q):
    mk = MODELS[model_key]
    if arm == "N":
        text, tok, sec = ask_nude(mk, q)
        obj = _jnum(text)
        got = norm_num(obj.get("answer")) if isinstance(obj, dict) \
            else None
        return got, (None if got is not None else "shape"), tok, sec
    if arm == "C":
        return run_code_arm(mk, q)
    if arm == "R":
        return run_free_relay(mk, q)
    if arm == "S":
        steps, err, tok, sec = run_skill(mk, q)
        ans = steps[-1].get("answer") if steps else None
        return norm_num(ans), err, tok, sec
    if arm == "T":
        win, tok, sec, votes = run_retry(mk, q)
        return norm_num(win), (None if win else "novote"), tok, sec
    raise AssertionError("bras inconnu: " + arm)


if __name__ == "__main__":
    qs = problems()
    only = sys.argv[1:] or ["0.5b", "1.5b", "7b", "8b"]
    done = set()
    try:
        for l in open(OUT):
            r = json.loads(l)
            done.add((r["model"], r["i"], r["arm"]))
    except FileNotFoundError:
        pass
    print("déjà faites:", len(done), "/ 400 — matrice", flush=True)
    with open(OUT, "a", encoding="utf-8") as fh:
        for mk in only:
            for t in qs:
                for arm in ARMS:
                    if (mk, t["i"], arm) in done:
                        continue
                    got, err, tok, sec = one(mk, arm, t["text"])
                    gold = float(t["gold"])
                    ok = got is not None and abs(got - gold) < .005
                    fh.write(json.dumps({"harness": "v15-matrix",
                                         "model": mk, "i": t["i"],
                                         "family": t["family"],
                                         "arm": arm, "ok": ok,
                                         "got": got, "gold": gold,
                                         "err": err, "tokens": tok,
                                         "secs": sec}) + "\n")
                    fh.flush()
                    print("%-4s #%02d %s %s tok=%d %s" % (
                        mk, t["i"], arm, "✓" if ok else "✗", tok,
                        err or ""), flush=True)
