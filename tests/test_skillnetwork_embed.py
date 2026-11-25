"""SKILL-NETWORK.md est embarqué dans main.py parce que l'uploader
Railway l'a perdu deux fois (FileNotFoundError /app/SKILL-NETWORK.md,
25-11). Ce pin est la dette de cette décision : le texte embarqué DOIT
rester byte-identique au fichier suivi. Si tu changes l'un, change
l'autre — make_plugin régénère, la suite veille."""
from pathlib import Path
import main


def test_embedded_network_equals_tracked_file():
    disk = (Path(__file__).parent.parent / "SKILL-NETWORK.md").read_text()
    assert main.SKILL_NETWORK_TEXT == disk


def test_network_route_serves_the_doctrine():
    from fastapi.testclient import TestClient
    cli = TestClient(main.app)
    r = cli.get("/SKILL-NETWORK.md")
    assert r.status_code == 200
    assert "own language" in r.text
    assert "the gate judges bytes, not prose" in r.text.lower()
