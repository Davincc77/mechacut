import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)

KEY_PAGES = ["/", "/proposals", "/PAYOUTS", "/route", "/recipes",
             "/SKILL-KIT.md", "/SKILL-NETWORK.md", "/SKILL-MINI.md",
             "/SKILL.md", "/agent/manifest"]


def _generator():
    p = Path(__file__).resolve().parent.parent / "scripts" / "make_sitemap.py"
    spec = importlib.util.spec_from_file_location("make_sitemap", str(p))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_sitemap_serves_200_xml_with_every_page():
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    assert "application/xml" in r.headers["content-type"]
    for path in KEY_PAGES:
        assert f"https://mechacut.studio{path}" in r.text, path


def test_sitemap_is_byte_stable_and_matches_generator():
    ms = _generator()
    a = ms.build("2026-01-01")
    b = ms.build("2026-01-01")
    assert a == b, "sitemap must be byte-stable for a fixed day"
    assert a.count("<url>") == len(ms.PAGES)
    served = client.get("/sitemap.xml").text
    assert served.count("<url>") == len(ms.PAGES)
