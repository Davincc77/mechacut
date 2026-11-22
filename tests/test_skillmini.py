"""La mini-skill : une page, n'importe quel modèle. Budget, route,
panneau Try-it branché sur les réponses RÉELLES du build, et le lien
X de demande d'outil — pré-rempli, jamais envoyé."""
import json
import sys
sys.path.insert(0, ".")
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def test_skill_mini_served_and_budgeted():
    r = client.get("/SKILL-MINI.md")
    assert r.status_code == 200
    body = r.text
    assert len(body.encode("utf-8")) < 3500   # ~700 tokens : un 0.5B porte
    # resize 22-11 soir : +la règle F5/A1 — contenu issu du bench, pas
    # décoratif ; le vrai plafond portabilité reste <4000.
    for needle in ("/agent/manifest", "/api/v1/intent/card",
                   "request_on_x", "402", "Never reformat"):
        assert needle in body, needle
    # byte-stable : deux appels, mêmes octets
    assert client.get("/SKILL-MINI.md").content == r.content


def test_examples_json_is_the_build_stdout():
    r = client.get("/agent/examples.json")
    assert r.status_code == 200
    doc = r.json()
    assert doc["examples"], "corpus ran at build => non-empty"
    ex = doc["examples"]["/api/v1/num/round"]
    assert ex["status"] == 200
    assert "1234.57" in ex["response"]        # ce que le serveur a VRAIMENT dit


def test_tool_spec_carry_try():
    r = client.get("/tools/num_round.json")
    spec = r.json()
    say = spec["try"]["say"]
    assert isinstance(say, dict) and set(say) == {"en", "fr", "pt"}
    assert say["fr"] == "arrondis 1234.5678 à 2 décimales"
    assert spec["try"]["request"]["path"] == "/api/v1/num/round"
    assert "1234.57" in spec["try"]["response"]


def test_tool_spec_try_optional_not_fabricated():
    # un tool SANS pin corpus : say retombe sur le purpose, response None
    r = client.get("/tools/text_sanitize.json")
    spec = r.json()
    t = spec.get("try", {})
    if "/api/v1/text/sanitize" not in client.get(
            "/agent/examples.json").json()["examples"]:
        assert t.get("response") is None or "try" not in spec


def test_no_match_offers_the_x_draft_scrubbed():
    utter = ("extrais les numéros de carte de sk-" + "A" * 40 +
             " et parle-moi de météo marine")
    r = client.post("/api/v1/intent/card", json={"utterance": utter})
    assert r.status_code == 200
    d = r.json()
    if d["status"] != "no_match":
        # la météo marine ne matche pas non plus → peut être ambiguous ;
        # le champ n'existe que sur no_match, test ciblé direct sinon :
        import intake
        card = intake.build_card("peins-moi un mur en briques roses",
                                 {}, lambda q, top=3: [], top_tools=3)
        assert card["status"] == "no_match"
        d = card
    x = d["request_on_x"]
    assert x["url"].startswith("https://x.com/intent/post?text=")
    assert "Davincc" in x["url"]
    assert "Nothing was sent" in x["note"]
    # la clé de 40+ caractères doit être purgée du brouillon
    assert ("A" * 16) not in x["url"]


def test_landing_bakes_the_connect_block():
    html = open("static/landing.html", encoding="utf-8").read()
    assert 'id="connectcmd"' in html
    assert "/SKILL-MINI.md" in html


def test_everyday_section_is_built_from_real_answers():
    import json
    fr = json.loads(open("locales/fr.json", encoding="utf-8").read())
    grid = fr["everyday_grid"]
    assert 'id="everyday"' in grid
    import re as _re
    assert not _re.search(r">\?<", grid)  # aucune chip "échec"
    assert "jours" in grid                     # réponse en français réel
    en = json.loads(open("locales/en.json", encoding="utf-8").read())
    assert "days to go" in en["everyday_grid"]
    # devise locale dans les sayings : € en FR, $ en EN, R$ en PT
    import sayings
    am = sayings.SAY["/api/v1/money/amortize"]
    assert "€" in am["fr"] and "$" in am["en"] and "R$" in am["pt"]


def test_md_render_document_mode_deterministic():
    body = {"markdown": "# Test\n\ncorps", "document": True,
            "title": "Test"}
    a = client.post("/api/v1/md/render", json=body).json()
    b = client.post("/api/v1/md/render", json=body).json()
    assert a["html"].startswith("<!DOCTYPE html>")
    assert "@media print" in a["html"]
    assert a["sha256"] == b["sha256"]
    assert "printable" in a
    plain = client.post("/api/v1/md/render",
                        json={"markdown": "# Test"}).json()
    assert not plain["html"].startswith("<!DOCTYPE")
