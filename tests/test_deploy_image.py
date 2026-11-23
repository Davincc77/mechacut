import re
from pathlib import Path


def test_dockerfile_ships_the_registry():
    """bundle 90 — le registre doit être dans l'image : vide embarqué =
    fausse page. Le 24-11 le COPY n'a pas été posé (ancre 'static/ ' vs
    './static/' divergente) et le test ne couvrait pas docs/."""
    df = open("Dockerfile").read()
    assert "COPY docs/proposals/ ./docs/proposals/" in df
    lines = [l for l in open("docs/proposals/registry.jsonl") if l.strip()]
    assert len(lines) >= 10
    import registry
    assert registry.query()["counts"]["total"] >= 10


def test_dockerfile_copies_every_local_module():
    """The image copies an allowlist of files. Every local module that
    main.py imports must be in that allowlist — or prod crash-loops
    (learned the hard way when check.py shipped without a COPY line)."""
    root = Path(__file__).resolve().parent.parent
    docker = (root / "Dockerfile").read_text(encoding="utf-8")
    copy_files = set()
    for line in docker.splitlines():
        if line.startswith("COPY ") and "./" in line:
            for tok in line.split():
                if tok.endswith(".py") or tok.endswith(".md"):
                    copy_files.add(tok)
    local = {f.name for f in root.glob("*.py")}
    imported = set()
    src = (root / "main.py").read_text(encoding="utf-8")
    for m in re.finditer(r"^import (\w+)$", src, re.M):
        if "%s.py" % m.group(1) in local:
            imported.add("%s.py" % m.group(1))
    missing = imported - copy_files
    assert not missing, "Dockerfile COPY misses: %s" % sorted(missing)
