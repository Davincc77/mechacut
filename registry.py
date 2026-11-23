"""registry — bundle 90. Le registre public des propositions d'outils.

Doctrine : le registre vit dans GIT (docs/proposals/registry.jsonl,
append-only), pas dans une base. Le serveur LE LIT, ne l'écrit jamais :
« nothing stored » reste vrai au centime près — une arrivée passe par
/api/v1/agent/propose (verdict nommé, blob prêt-à-commit, rien stocké
côté serveur) et le banc humain la commite dans le fichier. Les états
sont une vocabulaire fermé : proposed | en-banc | accepted | shipped |
refuse. Les dates sont DITES par les lignes (arrival), jamais l'horloge.
"""
import json
import re
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent / \
    "docs" / "proposals" / "registry.jsonl"
STATUSES = ("proposed", "en-banc", "accepted", "shipped", "refuse")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,39}$")


def load():
    if not REGISTRY_PATH.exists():
        return []
    out = []
    for line in REGISTRY_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        if not _NAME_RE.match(e.get("name", "")):
            raise ValueError("registry_corrupt: bad name %r" % e.get("name"))
        if e.get("status") not in STATUSES:
            raise ValueError("registry_corrupt: status %r outside %s"
                             % (e.get("status"), "|".join(STATUSES)))
        if not _DATE_RE.match(str(e.get("arrival", ""))):
            raise ValueError("registry_corrupt: arrival must be YYYY-MM-DD")
        out.append(e)
    return out


def query(name=None, status=None, latest=None):
    if latest is not None:
        if isinstance(latest, bool) or not isinstance(latest, int) \
                or not 1 <= latest <= 100:
            raise ValueError("latest_grammar: integer 1..100 (window of "
                             "ARRIVALS, newest last)")
    if status is not None and status not in STATUSES:
        raise ValueError("status_grammar: %r outside proposed|en-banc|"
                         "accepted|shipped|refuse" % status)
    if name is not None and not _NAME_RE.match(name):
        raise ValueError("name_grammar: %r is not a tool name" % name)
    all_ = load()
    total = len(all_)
    entries = all_
    if name:
        entries = [e for e in entries if e["name"] == name]
        verdict = "FOUND" if entries else "NOT-IN-REGISTRY"
    elif status:
        entries = [e for e in entries if e["status"] == status]
        verdict = "FILTERED"
    elif latest is not None:
        entries = entries[-latest:]
        verdict = "LATEST"
    else:
        verdict = "LISTED"
    counts = {"shown": len(entries), "total": total}
    if not (name or status or latest):
        st = {s: 0 for s in STATUSES}
        for e in entries:
            st[e["status"]] += 1
        counts["status"] = st
    return {"verdict": verdict, "entries": entries, "counts": counts,
            "registry": "docs/proposals/registry.jsonl",
            "statuses": list(STATUSES)}
