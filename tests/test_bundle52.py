# -*- coding: utf-8 -*-
"""bundle52 — le hub de bancs repliables : la forme ET les nombres.
Le guard recalcule indépendamment depuis les jsonls ; si un banc est
re-couru et que le résumé du landing ne suit pas, ce test rouge
empêche le mensuel de sortir."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "static" / "landing.html").read_text(encoding="utf-8")
_EN = json.loads((ROOT / "locales" / "en.json").read_text(
    encoding="utf-8"))
# le landing.html servi est le TEMPLATE rendu avec la locale — le
# guard teste la page RENDUE, pas la coquille.
HTML = re.sub(r"{{([a-zA-Z0-9_.]+)}}",
              lambda m: str(_EN.get(m.group(1), m.group(0))), TEMPLATE)


def _rows(name):
    f = ROOT / "bench" / name
    return [json.loads(l) for l in f.read_text().splitlines() if l.strip()]


def test_collapsible_bench_cards_grouped_by_thesis():
    cards = re.findall(r'<details class="bcard"[^>]*>\s*'
                       r'<summary><span class="bv">([vF][0-9b]+)'
                       r'</span>', HTML)
    assert cards == ["v6", "v9", "v10", "v11", "v12",          # exécution
                     "v15", "v17", "F5", "F7", "v23",          # forme
                     "v16", "v20", "v22", "v22b",              # doute+forme payante
                     "v13", "v14",                              # lecture
                     "v19", "v24"], cards                       # régime réel
    groups = re.findall(r'<details class="bgroupd"><summary>([^<]+)</summary>', HTML)
    assert len(groups) == 5, groups


def test_v19_summary_matches_raw():
    rows = _rows("results_v19_csv_bill.jsonl")
    mr = [r for r in rows if r["arm"] in ("N", "R")]
    wins = sum(bool(r["correct"]) for r in mr)
    drift = max(len({r["sha"] for r in rows if r["arm"] == "N"
                     and r["model"] == m})
                for m in ("1.5b", "7b"))
    machine = [r for r in rows if r["arm"] == "M"]
    ok_m = sum(bool(r["correct"]) for r in machine)
    # phrase COMPLÈTE recalculée — une couture cassée ou un fragment
    # orphelin ne passe plus jamais.
    expected = ("%d/%d attempts right for the models — machine: "
                "%d/%d days on one identical hash; %d different "
                "outputs from one model in 30 days."
                % (wins, len(mr), ok_m, len(machine), drift))
    assert expected in HTML, expected


def test_v15_summary_matches_raw():
    rows = [r for r in _rows("results_v15_matrix.jsonl")
            if r.get("family") in ("mix", "partage")
            and r.get("arm") in ("N", "T", "S", "C", "R")]
    alone = sum(1 for r in rows if r["arm"] in ("N", "T") and r["ok"])
    cells = sum(1 for r in rows if r["arm"] in ("N", "T"))
    arms = {a: sum(1 for r in rows if r["arm"] == a and r["ok"])
            for a in ("S", "C", "R")}
    best = max(arms.values())
    tied = [a for a in arms if arms[a] == best]
    arm_cells = sum(1 for r in rows if r["arm"] in tied) // len(tied)
    assert "%d/%d chain attempts" % (alone, cells) in HTML
    assert "%d/%d by the best server arm" % (best, arm_cells) in HTML


def test_no_stale_scroll_structure():
    # le contrat « pas des heures de scroll » : la section bench doit
    # tenir dans les cartes, pas en tableaux dépliés par défaut.
    bench = HTML[HTML.index('id="bench"'):HTML.index('id="build"')]
    assert bench.count("<table>") == 8          # 8 bancs tabulaires
    assert bench.count('open>') == 1            # seule la v23 est ouverte
    assert re.search(r'<details class="bcard" open>\s*<summary>'
                     r'<span class="bv">v23</span>', HTML), \
        "la carte ouverte par défaut doit être le dernier banc rendu"


def test_v22_v22b_summaries_match_raw():
    rows = _rows("results_v22.jsonl")
    n = [r for r in rows if r["arm"] == "N"]
    f = [r for r in rows if r["arm"] == "F"]
    per = {m: sum(1 for r in n if r["model"] == m and r["ok"])
           for m in {r["model"] for r in n}}
    expected = ("Three frontier models answer %d/%d naked — one at "
                "%d/7, another at %d/7. Through the frozen fiche: "
                "%d/%d. Paying more doesn't change the shape."
                % (sum(1 for r in n if r["ok"]), len(n),
                   max(per.values()), min(per.values()),
                   sum(1 for r in f if r["ok"]), len(f)))
    assert expected in HTML, expected
    b = _rows("results_v22b.jsonl")
    pairs = {}
    msha = {}
    for r in b:
        pairs.setdefault((r["model"], str(r["i"])), set()).add(r["code_sha"])
        msha.setdefault(str(r["i"]), set()).add(r["m_sha"])
    expected_b = ("Five passes at agent temperature: %d/%d right — the "
                  "SAME program twice: %d/14. The server: %s sha per "
                  "problem."
                  % (sum(1 for r in b if r["c_ok"]), len(b),
                     sum(1 for v in pairs.values() if len(v) == 1),
                     max(len(v) for v in msha.values())))
    assert expected_b in HTML, expected_b


def test_v20_summary_matches_raw():
    rows = _rows("results_v20_target_lock.jsonl")

    def w(mk, arm):
        return sum(1 for r in rows if r["model"] == mk
                   and r["arm"] == arm and r["ok"])
    expected = ("The wall is AIM: llama 8B went %d\u2192%d/20 with a "
                "target lock; the 7B signed its first %d/20."
                % (w("8b", "S"), w("8b", "L"), w("7b", "L")))
    assert expected in HTML, expected


def test_v23_summary_matches_raw():
    rows = _rows("results_v23_lfm3.jsonl")
    ch = [r for r in rows if r["arm"] == "N"
          and r["family"] in ("mix", "partage")]
    wins = sum(1 for r in ch if r["ok"])
    cost = sum(r["usd"] for r in rows if r["arm"] == "N")
    refused = sum(1 for r in rows if r["arm"] == "L" and not r["ok"]
                  and r["got"] is not None
                  and abs(r["got"] - r["gold"]) < 0.005)
    expected = ("A 1.7B trained for agents solved %d/%d chains naked "
                "for $%.4f \u2014 our wall was TRAINING, not size; "
                "and the lock refused %d right answers over their "
                "names." % (wins, len(ch), cost, refused))
    assert expected in HTML, expected


def test_v11_f5_v24_summary_match_raw():
    r = _rows("results_v11.jsonl")
    def w(sub, arm):
        rs = [x for x in r if sub in x["model"] and x["arm"] == arm]
        return "%d/%d" % (sum(1 for x in rs if x["ok"]), len(rs))
    assert ("the 7B goes %s to %s relayed" % (w("7b", "naked"),
                                              w("7b", "relay"))
            in HTML)
    f5 = _rows("results_f5_accept.jsonl")
    wins = sum(1 for x in f5 if x["verdict"] == "OK")
    rep = sum(x["repairs"] for x in f5)
    assert ("%d/%d chain attempts with the fiche — criterion ≥19 "
            "PASSED; %d repaired" % (wins, len(f5), rep) in HTML)
    r24 = _rows("results_v24_lfm3_30days.jsonl")
    n24 = [x for x in r24 if x["arm"] == "N"]
    # silence = réponse VIDE (sha du newline), pas « refusé de forme »
    sil = sum(1 for x in n24 if x["sha"] == "01ba4719c80b6fe9")
    okc = sum(1 for x in n24 if x["ok"])
    usd = sum(x["usd"] for x in n24)
    assert ("%d/%d days of empty answers after 8,192 reasoning "
            "tokens, %d right, billed $%.4f"
            % (sil, len(n24), okc, usd) in HTML)


def test_f7_summary_matches_raw():
    r = _rows("results_f7_accept.jsonl")
    r = [x for x in r if x["harness"] == "f7-accept"]
    wins = sum(1 for x in r if x["verdict"] == "OK")
    rep = sum(1 for x in r if x["verdict"] == "OK" and x["repairs"] > 0)
    assert ("%d/%d — criterion ≥19 passed; %d of them won by the "
            "named refusal" % (wins, len(r), rep)) in HTML
