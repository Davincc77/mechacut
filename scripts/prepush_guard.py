#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prepush_guard — refuse tout push qui sortirait l'ADN ou un secret.

Lit les chemins interdits dans .git/info/exclude (fichier LOCAL, jamais
poussé : un cloneur tiers ne voit ni la liste, ni ce test — le garde
frappe là où le risque est, sur cette machine). Scanne les commits
sortants : (1) aucun ne touche un chemin interdit ; (2) aucun blob
nouveau ne porte un motif de secret (mêmes familles que
audit_secrets.py). Exit 0 = poussez ; exit 1 = noms, raisons, repos.

Usage : hook .git/hooks/pre-push (stdin = lignes de refs), ou manuel :
    .venv/bin/python scripts/prepush_guard.py [plage-git]
"""
import os
import re
import subprocess
import sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()
EXCLUDE = os.path.join(ROOT, ".git", "info", "exclude")

SECRET_PATTERNS = [
    # borne nommee bundle99 : le motif nu matchait « mu-sk-says-grok-... »
    # (URL d'article verbatim deja poussee) — une vraie cle sk- n'est
    # jamais collees a une lettre, le lookbehind ferme le faux positif
    # sans aveugler le garde.
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[bpars]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{30,}"),
    re.compile(r"\bre_[A-Za-z0-9]{24,}"),
    re.compile(r"(?i)(secret|passwd|password|api_?key|token)"
               r"[\"']?\s*[:=]\s*[\"'][^\"']{16,}[\"']"),
    # clé privée brute 64-hex : sur une LIGNE qui nomme une clé (les
    # sha256 de golden/integrity sont légion et légitimes — le motif
    # contextuel évite les faux positifs)
    re.compile(r"(?i)(private|secret)[^0-9a-f]{0,30}0x?[0-9a-f]{64}"),
]


def banned_paths():
    if not os.path.exists(EXCLUDE):
        return []
    out = []
    for line in open(EXCLUDE, encoding="utf-8"):
        line = line.strip()
        if line.startswith("/") and not line.startswith("//"):
            out.append(line.lstrip("/").rstrip("/"))
    return out


def outgoing_range():
    """plage argv > stdin du hook > origin/master..HEAD."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    data = ""
    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
    if data:
        parts = data.split()
        local, remote = parts[1], parts[3]
        if re.fullmatch(r"0+", remote):
            return local
        return "%s..%s" % (remote, local)
    return "origin/master..HEAD"


def touched(rng):
    """(path, status) ; status D = suppression — seule manière autorisée
    de toucher un chemin interdit : le sortir du dépôt."""
    if rng.count("..") == 1:
        cmd = ["git", "diff", "--name-status", rng]
    else:
        cmd = ["git", "show", "--name-status", "--format=", rng]
    out = []
    for l in subprocess.run(cmd, capture_output=True,
                            text=True).stdout.splitlines():
        if not l.strip():
            continue
        parts = l.split("\t")
        out.append((parts[-1], parts[0][0]))
    return out


def blobs(rng):
    files = touched(rng)
    rev = rng.split("..")[-1] if ".." in rng else rng
    out = []
    for f in {p for p, stt in files if stt != "D"}:
        r = subprocess.run(["git", "show", "%s:%s" % (rev, f)],
                           capture_output=True)
        if r.returncode == 0:
            out.append((f, r.stdout.decode("utf-8", "replace")))
    return out


def main():
    rng = outgoing_range()
    if not subprocess.run(["git", "rev-list", "--count", rng],
                          capture_output=True, text=True).stdout.strip() \
            .isdigit():
        return 0
    n = int(subprocess.run(["git", "rev-list", "--count", rng],
                           capture_output=True, text=True).stdout)
    if n == 0:
        return 0
    bad = []
    bans = banned_paths()
    for f, status in touched(rng):
        if status == "D":
            continue
        for b in bans:
            import fnmatch as _fm
            if f == b or f.startswith(b + "/") or _fm.fnmatch(f, b):
                bad.append("ADN : %s sort dans %s (interdit via "
                           ".git/info/exclude)" % (f, rng))
                break
    for f, content in blobs(rng):
        for rx in SECRET_PATTERNS:
            m = rx.search(content)
            if m:
                bad.append("SECRET : %s porte %r" %
                           (f, m.group(0)[:40]))
    if bad:
        print("prepush_guard : REFUS —")
        for b in bad:
            print("  - " + b)
        return 1
    print("prepush_guard : OK (%d commits sortants, %d chemins "
          "interdits surveillés, 0 secret)" % (n, len(bans)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
