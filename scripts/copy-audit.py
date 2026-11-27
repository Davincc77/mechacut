#!/usr/bin/env python3
"""copy-audit — zero opinion sur la surface publique.

Deterministic scanner (closed word list, zero LM) for the phrases this house
has already had to kill by hand: self-praising adverbs, universal quantifiers
without a named corpus, dead counters. Runs in CI: any hit fails the suite.
Exempt lines: data-hay keyword blobs and quoted source material (<q>).

Depuis bundle 127_hermes : la table vit dans claimsweep.py (la porte joue
la MEME liste que le CI — un texte, une regle, un seul endroit). L'import
est la loi ; la re/copie serait une trahison de doctrine.
"""
import re, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from claimsweep import MARKERS  # noqa: E402 — table unique, pas de copie

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = ["README.md", "docs/INST-CATALOG.md", "docs/CASE-STUDY-TICKET.md",
         "docs/CASE-STUDY-BANKS.md",
         "docs/CASE-STUDY-GOVERNMENTS.md",
         "docs/CASE-STUDY-GEIPAN.md",
         "docs/CASE-STUDY-ARTEMIS.md",
         "locales/en.json", "locales/fr.json", "locales/pt.json",
         "scripts/make_landing.py"]

def hits(path: pathlib.Path):
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if "data-hay=" in line or "<q>" in line:
            continue
        low = line.lower()
        for m in MARKERS:
            if m.lower() in low:
                out.append((i, m, line.strip()[:110]))
    return out

def main():
    bad = []
    for rel in FILES:
        p = ROOT / rel
        if not p.exists():
            continue
        for i, m, frag in hits(p):
            bad.append(f"{rel}:{i} [{m}] {frag}")
    if bad:
        print("COPY-AUDIT FAILED — opinion/unverified phrasing:")
        print("\n".join(bad))
        return 1
    print(f"copy-audit: {len(FILES)} surfaces, 0 hit")
    return 0

if __name__ == "__main__":
    sys.exit(main())
