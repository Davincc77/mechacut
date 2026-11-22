"""i18n parity and routing tests.

Every catalog must have exactly the keys of en.json (source of truth), the
template must use only known keys, rendered pages must contain no leftover
{{...}} tokens, and language routing must work (?lang=, Accept-Language,
browser vs agent). A language without a trusted reviewer does not ship.
"""

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main

ROOT = Path(__file__).resolve().parent.parent
LANGS = ("en", "fr", "pt")


def _catalog(code):
    return json.loads((ROOT / "locales" / f"{code}.json").read_text(encoding="utf-8"))


def _template_tokens():
    tpl = (ROOT / "static" / "landing.html").read_text(encoding="utf-8")
    return set(re.findall(r"\{\{([A-Za-z0-9._]+)\}\}", tpl))


def test_lang_codes_match_loader():
    assert main._LANG_CODES == LANGS
    assert set(main.LANDING.keys()) == set(LANGS)


def test_all_catalogs_are_json_objects():
    for code in LANGS:
        assert isinstance(_catalog(code), dict)
        assert len(_catalog(code)) > 30


def test_key_parity_with_english():
    en = _catalog("en")
    for code in LANGS:
        other = _catalog(code)
        miss = set(en) - set(other)
        extra = set(other) - set(en)
        assert not miss, f"{code}: clés manquantes: {sorted(miss)}"
        assert not extra, f"{code}: clés inattendues: {sorted(extra)}"


def test_all_values_non_empty():
    for code in LANGS:
        for key, val in _catalog(code).items():
            assert val.strip(), f"{code}:{key} est vide"


def test_template_tokens_covered_by_english():
    en = set(_catalog("en"))
    # cur.* tokens are injected by the loader (language switcher highlight),
    # not stored in catalogs.
    toks = _template_tokens() - {"LANG"} - {t for t in _template_tokens() if t.startswith("cur.")}
    missing = toks - en
    assert not missing, f"tokens sans clé dans en.json: {sorted(missing)}"
    import sys as _sys
    from pathlib import Path as _P
    _sd = str(_P(__file__).resolve().parents[1] / "scripts")
    if _sd not in _sys.path:
        _sys.path.insert(0, _sd)
    import make_landing as _ml
    unused = en - toks - _ml.BUILDER_CONSUMED
    assert not unused, f"clés sans token dans le template: {sorted(unused)}"


def test_rendered_pages_have_no_leftover_tokens():
    client = TestClient(main.app)
    for code in LANGS:
        html = client.get("/", headers={"accept": "text/html", "accept-language": code}).text
        assert "{{" not in html, f"{code}: tokens non résolus"
        assert f'<html lang="{code}">' in html


def _hero(code):
    # single source: the marker is read from the locale file, never
    # duplicated here — retranslations can never rot this test
    import json
    from pathlib import Path
    p = Path(main.__file__).resolve().parent / "locales" / (code + ".json")
    return json.loads(p.read_text(encoding="utf-8"))["hero1"]


def test_lang_query_routing():
    client = TestClient(main.app)
    for code in ("en", "fr", "pt"):
        html = client.get("/", headers={"accept": "text/html"},
                          params={"lang": code}).text
        assert '<html lang="%s">' % code in html
        assert _hero(code) in html, "?lang=%s ne rend pas %s" % (code, code)
    # langue inconnue -> repli EN
    html = client.get("/", headers={"accept": "text/html"},
                      params={"lang": "zh"}).text
    assert _hero("en") in html


def test_accept_language_routing():
    client = TestClient(main.app)
    zh = client.get("/", headers={"accept": "text/html",
                                  "accept-language": "zh-CN,zh;q=0.9,en;q=0.8"}).text
    assert _hero("en") in zh  # zh pas livré -> EN
    fr = client.get("/", headers={"accept": "text/html",
                                  "accept-language": "fr-FR,fr;q=0.9"}).text
    assert _hero("fr") in fr
    pt_br = client.get("/", headers={"accept": "text/html",
                                     "accept-language": "pt-BR,pt;q=0.9"}).text
    assert _hero("pt") in pt_br
    de = client.get("/", headers={"accept": "text/html",
                                  "accept-language": "de-DE,de;q=0.9"}).text
    assert _hero("en") in de  # de non livré -> EN

def test_agent_still_gets_json():
    client = TestClient(main.app)
    for accept in ("*/*", "application/json"):
        r = client.get("/", headers={"accept": accept})
        assert r.headers["content-type"].startswith("application/json")
        assert r.json()["service"] == "mechacut"
