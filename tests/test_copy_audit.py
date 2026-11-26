import subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

def test_copy_audit_zero_hits():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "copy-audit.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, "opinion phrasing on public surfaces:\n" + r.stdout

def test_copy_audit_can_fail():
    # article 7 du protocole: un test qui ne peut pas echouer ne peut pas passer
    import tempfile, os
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "locales").mkdir()
    (d / "scripts").mkdir()
    shutil_marker = d / "locales" / "en.json"
    shutil_marker.write_text('{"k": "honestly: fine"}', encoding="utf-8")
    import shutil as sh
    sh.copy(ROOT / "scripts" / "copy-audit.py", d / "scripts" / "copy-audit.py")
    r = subprocess.run([sys.executable, str(d / "scripts" / "copy-audit.py")],
                       capture_output=True, text=True, cwd=d)
    assert r.returncode == 1 and "honestly:" in r.stdout
