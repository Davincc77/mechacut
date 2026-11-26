# -*- coding: utf-8 -*-
"""VERDICTS — le registre public des demandes reçues, jugé sur disque.

La page tient le verdict du banc pour chaque demande entrée par la
porte (agent/propose), les fils publics et le radar. Pas de réseau :
le test exige que la page se tienne sans croyance — vocabulaire fermé,
preuve par ligne, routes SHIPPED vivantes dans la TABLE, commits cités
résolvables dans le dépôt, toute promesse de chemin vérifiée contre
les fichiers suivis, et l'inbox décrite exactement comme la porte la
promet. Une citation pendante est la classe d'incident b87 : interdite
ici par construction.
"""
import re
import subprocess
from pathlib import Path

import routing

ROOT = Path(__file__).parent.parent
PAGE = (ROOT / "VERDICTS.md").read_text(encoding="utf-8")
INBOX = (ROOT / "docs" / "proposals" / "README.md").read_text(encoding="utf-8")

VERDICTS = {"ELIGIBLE", "SUSPECT-DUPLICATE", "DUPLICATE-OF", "REFUSED",
            "NO-ASK"}
STATUSES = {"SHIPPED", "IN-BUILD", "PENDING", "CLOSED", "REPLIED"}


def _data_rows():
    rows = []
    for line in PAGE.splitlines():
        line = line.strip()
        if line.startswith("| 2026-"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            assert len(cells) == 6, "row not 6-column: %r" % line[:60]
            rows.append(cells)
    assert rows, "VERDICTS.md lost its data rows"
    return rows


def test_verdict_vocabulary_is_the_doors_own():
    for cells in _data_rows():
        assert cells[3] in VERDICTS, "verdict outside grammar: %r" % cells[3]
        assert cells[4] in STATUSES, "status outside grammar: %r" % cells[4]


def test_every_row_carries_evidence():
    for who, cells in [(c[1], c) for c in _data_rows()]:
        ev = cells[5]
        assert len(ev) >= 20, "thin evidence for %s" % who
        assert re.search(r"commit(?:ted)? [0-9a-f]{7}|/api/v1/|"
                         r"[PX]-\d{4}-\d{2}-\d{2}-\d|live surfaces", ev), \
            "no citable proof for %s" % who


def test_cited_commits_resolve_in_this_repo():
    for cells in _data_rows() + [["", "", "", "", "", PAGE]]:
        for sha in re.findall(r"commit(?:ted)? ([0-9a-f]{7,40})", cells[5]):
            r = subprocess.run(["git", "cat-file", "-e", sha + "^{commit}"],
                               cwd=ROOT, capture_output=True)
            assert r.returncode == 0, "cited commit is not a commit: %s" % sha


def test_shipped_rows_name_a_commit_and_exist_in_the_table():
    table_paths = {t[1] for t in routing.TABLE}
    shipped = [c for c in _data_rows() if c[4] == "SHIPPED"]
    assert shipped, "register lost its shipped rows"
    for cells in shipped:
        assert re.search(r"commit [0-9a-f]{7}", cells[5]), \
            "SHIPPED without commit: %s" % cells[1]
        for p in re.findall(r"/api/v1/[a-z0-9/-]+", cells[5]):
            assert p in table_paths, \
                "row %s cites a route the build does not have: %s" % (
                    cells[1], p)


def test_in_build_rows_say_the_deploy_is_pending():
    for cells in _data_rows():
        if cells[4] != "IN-BUILD":
            continue
        assert "golds hand-traced" in cells[5] and "bundle" in cells[5], \
            "IN-BUILD must name the bundle and its golds: %s" % cells[1]
        assert "ships next deploy" in cells[5], \
            "IN-BUILD must say the deploy is pending: %s" % cells[1]
        assert "/api/v1/" in cells[5], "IN-BUILD must name its route: %s" % cells[1]


def test_no_ask_rows_owe_a_reply_state():
    for cells in _data_rows():
        if cells[3] != "NO-ASK":
            continue
        assert cells[4] in ("PENDING", "REPLIED"), \
            "NO-ASK row must be PENDING or REPLIED: %s" % cells[1]
        if cells[4] == "PENDING":
            assert re.search(r"[PX]-\d{4}-\d{2}-\d{2}-\d", cells[5]), \
                "PENDING without journal id: %s" % cells[1]


def test_non_build_verdicts_cite_their_journal_line():
    for cells in _data_rows():
        if cells[3] not in ("REFUSED", "DUPLICATE-OF"):
            continue
        assert re.search(r"X-\d{4}-\d{2}-\d{2}-\d", cells[5]), \
            "non-build verdict must cite its journal id: %s" % cells[1]


def test_door_section_keeps_the_empty_register_honest():
    # ÈRE 2 (26-11) : la porte a reçu ses premiers dossiers —
    # address_state, validate_cnpj, text_mojibake. L'invariance n'est
    # plus « vide mais honnête », c'est « rempli mais adossé » : chaque
    # ligne de la section porte cite un dossier blob suivi, et le
    # « No entries yet » n'a pas le droit de survivre à la première
    # ligne réelle (index qui nie ce qu'il contient = classe b87).
    door = PAGE.split("## Via threads")[0]
    assert "agent/propose" in door
    rows = [l for l in door.splitlines() if l.strip().startswith("| 2026-")]
    if "No entries yet" in door:
        assert not rows, "empty-register wording while door rows exist"
    import json
    tracked = set(subprocess.run(["git", "ls-files"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.split())
    for line in rows:
        blobs = re.findall(r"docs/proposals/([a-z0-9_]+)\.json", line)
        assert blobs, "door row without a docs/proposals/ blob citation"
        for b in blobs:
            p = "docs/proposals/%s.json" % b
            assert p in tracked, "door row cites an untracked blob: %s" % p
            d = json.loads((ROOT / p).read_text(encoding="utf-8"))
            name = d.get("name") or d.get("blob", {}).get("name")
            assert name, "blob dossier without a name: %s" % p


def test_every_blob_dossier_has_a_row():
    # sens inverse : docs/proposals/*.json de forme blob (name ou
    # examples) DOIT avoir sa ligne — l'index suit le dossier, jamais
    # l'inverse en silence. Les mappings (splitters.json) ne sont pas
    # des asks et n'ont pas de ligne à fermer.
    import json
    inbox = ROOT / "docs" / "proposals"
    for fn in sorted(inbox.glob("*.json")):
        d = json.loads(fn.read_text(encoding="utf-8"))
        if "name" not in d and "examples" not in d.get("blob", {}):
            continue
        key = d.get("name") or d["blob"]["name"]
        assert key in PAGE, ("docs/proposals/%s exists but VERDICTS.md "
                             "carries no row for '%s'" % (fn.name, key))


def test_inbox_readme_matches_the_doors_promise():
    assert "verbatim" in INBOX and "<name>.json" in INBOX
    assert "VERDICTS.md" in INBOX, "inbox must send verdicts to the register"
    # the door's next_steps names this exact path grammar
    import proposekit
    out = proposekit.propose(
        "verdict_probe_contract",
        "probe that keeps the inbox convention pinned to the door",
        None, [{"input": {"a": 1}, "expected": {"a": 1}}], None, None)
    assert out["verdict"] == "ELIGIBLE"
    assert "docs/proposals/verdict_probe_contract.json" in out["next_steps"][0]


def test_cited_paths_are_tracked_artifacts():
    # rule 22-11: the public repo shows product and proof only. Anything
    # this page cites as a file must actually be tracked — a dangling
    # citation is the b87 incident class, pinned closed here.
    tracked = set(subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True,
        text=True).stdout.split())
    for p in re.findall(r"(?<!/)\b(?:docs/|tests/)[A-Za-z0-9_./-]+\.[A-Za-z]+",
                        PAGE):
        assert p in tracked, "cited path not tracked: %s" % p
