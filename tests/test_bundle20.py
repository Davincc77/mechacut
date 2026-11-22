"""Bundle 20 — recipe/facts : la composition serveur qui fait réussir un
modèle faible au multi-tâches. Le modèle ne fait que CHOISIR la recette ;
l'inventaire est normalisé, dédupliqué, trié et sommés ici, jamais recopié."""
import sys
sys.path.insert(0, ".")
import json
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def test_recipe_facts_canonical_inventory():
    case = json.load(open("corpus/recipe_facts_incident.json"))
    r = client.post(case["path"], json=case["body"])
    assert r.status_code == 200
    d = r.json()
    inv = d["inventory"]
    assert inv["money"] == ["910.50", "4300.00"]          # tri numérique
    assert inv["percent"] == ["3.1%", "6.2%", "12.5%"]  # gold B003 (fait à la main) — le produit avait tort
    assert inv["date"] == ["2026-11-18", "2026-11-19", "2026-11-25"]
    assert inv["url"] == ["https://api.pay.eu/v1/checkout"]
    assert inv["email"] == ["ops@pay.eu"]
    assert d["total_money"] == "5210.50"
    assert d["sha256"]


def test_recipe_facts_deterministic():
    case = json.load(open("corpus/recipe_facts_incident.json"))
    a = client.post(case["path"], json=case["body"]).json()
    b = client.post(case["path"], json=case["body"]).json()
    assert a["sha256"] == b["sha256"]


def test_recipe_facts_kinds_filter():
    r = client.post("/api/v1/recipe/facts",
                    json={"text": "pay $1.00 by 2026-01-02, 50% http://a.b",
                          "kinds": ["money", "url"]})
    d = r.json()
    assert set(d["inventory"]) == {"money", "url"}
    assert d["inventory"]["url"] == ["http://a.b"]


def test_recipe_facts_bad_input_free_400():
    r = client.post("/api/v1/recipe/facts", json={"text": "   "})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "text"


def test_recipe_facts_in_all_surfaces():
    assert any(t["name"] == "recipe_facts" for t in main.MCP_TOOLS
               + main.RECIPE_SPECS)
    rec = client.get("/api/v1/recipes").json()["recipes"]
    assert "facts" in rec
    man = client.get("/agent/manifest").text
    assert "recipe/facts" in man
    route = client.get("/route", params={"q": "extract all amounts and dates from this note"}).json()
    assert "recipe_facts" in [t["tool"] for t in route["tools"]]
