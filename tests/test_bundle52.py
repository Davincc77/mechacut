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


def test_eight_collapsible_bench_cards():
    cards = re.findall(r'<details class="bcard"[^>]*>\s*'
                       r'<summary><span class="bv">(v\d+)</span>', HTML)
    assert cards == ["v23", "v20", "v19", "v17", "v16", "v15",
                     "v12", "v10", "v9", "v6"], cards


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
