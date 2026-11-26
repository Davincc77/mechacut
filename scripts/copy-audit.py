#!/usr/bin/env python3
"""copy-audit — zero opinion sur la surface publique.

Deterministic scanner (closed word list, zero LM) for the phrases this house
has already had to kill by hand: self-praising adverbs, universal quantifiers
without a named corpus, dead counters. Runs in CI: any hit fails the suite.
Exempt lines: data-hay keyword blobs and quoted source material (<q>).
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = ["README.md", "docs/INST-CATALOG.md", "docs/CASE-STUDY-TICKET.md",
         "docs/CASE-STUDY-BANKS.md",
         "locales/en.json", "locales/fr.json", "locales/pt.json",
         "scripts/make_landing.py"]

MARKERS = [
    # adverbe d'auto-aveu devant un fait
    "honestly:", "honnêtement :", "honesto:", "stated honestly",
    "honestly-labelled",
    # quantifieur universel sans corpus nommé
    "everyone knows", "Nobody says", "Personne ne dit", "Ninguém diz",
    "personne ne compte", "ninguém conta",
    # garantie revendiquée hors mesure
    "the class the form can guarantee",
    "la seule classe que la forme garantit",
    "a única classe que a forma garante",
    "confidence honestly", "marquer honnêtement", "confiança com honestidade",
    # compteurs morts / placeholders retirés
    "{n_shipped}", "no paid clone", "clone payant enregistré",
    "clone pago registrado", "nothing splits", "rien ne se divise",
    "nada divide",
    # slot sur-cité
    "every regulator",
]

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
