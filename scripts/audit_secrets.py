# -*- coding: utf-8 -*-
# Audit HISTORIQUE complet : chaque BLOB jamais commité, scanné contre
# les familles de secrets connus. Sort = hits avec commit+fichier, pour
# revue humaine — pas de self-grading du scanner : les hits sont listés
# bruts, je les affiche tous.
import re
import subprocess
import collections

BLOBS = subprocess.run(
    ["git", "cat-file", "--batch-all-objects", "--batch-check"],
    capture_output=True, text=True).stdout.splitlines()
blobs = [l.split()[0] for l in BLOBS
         if len(l.split()) >= 2 and l.split()[1] == "blob"]
print("blobs à scanner:", len(blobs))

PATTERNS = {
    "openai/anthropic sk-": re.compile(rb"sk-[A-Za-z0-9_\-]{20,}"),
    "github token": re.compile(rb"(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"),
    "slack": re.compile(rb"xox[bpars]-[A-Za-z0-9\-]{10,}"),
    "aws": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "private key block": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "bearer long": re.compile(rb"[Bb]earer\s+[A-Za-z0-9._\-]{30,}"),
    "resend re_": re.compile(rb"\bre_[A-Za-z0-9]{24,}"),
    "railway rt_": re.compile(rb"\brt_[A-Za-z0-9]{20,}"),
    "mnemonic 12 mots": re.compile(rb"\b(abandon|zoo|wizard|legit|lawn|giant|surprise|pigeon|romance|tobacco)\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w+\s+\w"),
    "64-hex brut (clé privée potentielle)": re.compile(rb"\b0x[0-9a-fA-F]{64}\b"),
    "base64 hautement sensible": re.compile(rb"(secret|passwd|password|api_?key|token)[\"']?\s*[:=]\s*[\"'][A-Za-z0-9+/=]{16,}[\"']"),
}

# où chaque blob apparaît (commit:path) — premier trouvé suffit pour
# le contexte humain
name_map = {}
log = subprocess.run(
    ["git", "log", "--all", "--raw", "--format=%H", "--diff-filter=ACM"],
    capture_output=True, text=True).stdout
cur = None
for line in log.splitlines():
    if re.fullmatch(r"[0-9a-f]{40}", line):
        cur = line
    elif line.strip() and cur and "\t" in line:
        parts = line.split("\t")
        path = parts[-1]
        m = re.search(r":[0-9a-f]{6,} ([0-9a-f]{6,}) [0-9a-f]{6,} [A-Z]",
                      parts[0])
        if m:
            name_map.setdefault(m.group(1), (cur, path))

hits = collections.defaultdict(list)
for sha in blobs:
    data = subprocess.run(["git", "cat-file", "blob", sha],
                          capture_output=True).stdout
    if len(data) > 3_000_000:
        continue
    for label, rx in PATTERNS.items():
        for mm in rx.finditer(data):
            frag = mm.group(0)[:90]
            where = name_map.get(sha[:len(sha)], ("?", "?"))
            hits[label].append((where[0][:8], where[1], frag))

if not hits:
    print("\n*** ZÉRO HIT sur toutes les familles ***")
for label, rows in sorted(hits.items()):
    uniq = {(c, p) for c, p, _ in rows}
    print("\n[%s] %d matches, %d fichiers distincts :" %
          (label, len(rows), len(uniq)))
    seen = set()
    for c, p, frag in rows:
        if (c, p) in seen:
            continue
        seen.add((c, p))
        print("  %s %s :: %r" % (c, p, frag))
        if len(seen) >= 12:
            print("  …")
            break
