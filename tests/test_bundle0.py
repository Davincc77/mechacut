"""Bundle 0 — agent navigation: manifest, on-demand schemas, skill packs."""

import hashlib

from fastapi.testclient import TestClient

import main
import routing

client = TestClient(main.app)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_manifest_complete_and_self_certified():
    r1 = client.get("/agent/manifest")
    r2 = client.get("/agent/manifest")
    assert r1.content == r2.content          # same bytes, forever
    assert r1.status_code == 200
    body = r1.text
    folded = "folded to dense mode" in body
    for name, path, _pack, purpose, _tags in routing.TABLE:
        line = [l for l in body.splitlines() if l.startswith(name + "  ")]
        assert line, name                     # every tool has its line
        assert path in line[0], name
        # prose mode carries the purpose; dense mode is legal ONLY when
        # the portability budget forces it, and then /tools/<name>.json
        # is declared as the purpose source in the NOTE line
        assert (purpose in line[0]) or folded, name
    ls = body.rstrip("\n").split("\n")
    assert ls[-1] == "# sha256=" + _sha("\n".join(ls[:-1]))


def test_manifest_token_budget():
    body = client.get("/agent/manifest").text
    # the promise: the whole catalogue is one fetch a weak model can carry.
    # Bounded absolutely AND amortized per line, so growth stays honest:
    # if a tool makes the manifest fat per line, this test says so.
    lines = body.splitlines()
    assert len(body) < 9000                   # absolute portability ceiling
    assert len(body) < 130 * len(lines)       # <= ~30 tokens per entry
    # fixed skeleton (header, tiers, notes, recipes, discovery) + one line
    # per tool; the real ceiling is the byte budget + dense fold in the
    # routing module — line count is only a proxy, resized here as the
    # catalogue grows past its original 95-tool shape
    assert len(lines) < 215   # resize 24-11 bundle97 (+agent_mcpsurface)
    # : 214 lignes MESUREES, 8 740 octets < 9 000 — le budget octets
    # est le vrai plafond et il serre (260 restants) : le prochain
    # lot border line débordera, le dense-fold routing le porte déjà.
    # Leçon du lot : les golds d'un test qui FIGE un plafond suivent
    # la mesure, jamais l'à-peu-près (précédent 197/214 bundle89).
    # shipping_deadline, +invoice_validate_totals) : 197 lignes, le
    # plafond OCTETS <9000 tient (mesuré 7 789) et la moyenne
    # <130/ligne aussi — la ligne reste un proxy, précédent 192/196
    # resize 23-11 bundle76 (+eval_compare;
    # 192 lignes, 7521 octets < 9000 et moyenne 39 < 130/ligne — les
    # plafonds RÉELS tiennent, la ligne est un proxy, précédent 190/192)
    # 190 lignes, budget octets <9000 tient — seul plafond réel)
    # (resize precedent 22-11 18h : <188, 186 lignes — bundle66
    # money_unitprice porte le catalogue a 188 lignes, le 189 ci-dessus
    # est le nouveau plafond ; le budget octets <9000 tient, seul
    # plafond reel)
    # resize 22-11 soir (+3 fiches F5 : 181 lignes, 6909 octets — le budget octets <9000 tient, seul plafond réel
    # resize 22-11 12h (136 routes: +baggage
    # +excel_damage) : le vrai plafond est le budget octets (<9000,
    # respecté : la ligne NOTE de
    # repli dense apparaît, preuve que le contrat portabilité tient)


def test_tool_spec_on_demand():
    r = client.get("/tools/color_palette.json")
    b = r.json()
    assert b["tier"] == "free" and b["pack"] == "design"
    assert "triad" in b["schema"]["inputSchema"]["properties"]["scheme"]["enum"]
    assert "sha256" in b
    for name, _p, _k, _u, _t in routing.TABLE:  # every TABLE name resolves
        assert client.get("/tools/%s.json" % name).status_code == 200


def test_tool_spec_unknown():
    r = client.get("/tools/csv_fx.json")
    assert r.status_code == 404
    b = r.json()
    assert b["error"] == "unknown_tool" and "csv_fix" in b["did_you_mean"]
    assert "manifest" in b["expected"]


def test_skill_packs_partition_the_suite():
    seen = 0
    for pack in routing.PACKS:
        r = client.get("/SKILL-%s.md" % pack)
        assert r.status_code == 200, pack
        body = r.text
        ls = body.rstrip("\n").split("\n")
        assert ls[-1] == "# sha256=" + _sha("\n".join(ls[:-1]))
        seen += body.count("\n## ")
    assert seen == len(routing.TABLE) == 181   # +agent_mcpsurface bundle97 ; 180 avec shop_pricedrop_refund
    # (23-11 bundle96) ; était 179 avec agent_mcpaudit (bundle92)


def test_pack_unknown():
    r = client.get("/SKILL-nope.md")
    assert r.status_code == 404
    assert r.json()["error"] == "unknown_pack"


def test_router_deterministic_and_relevant():
    r1 = c_route = client.get("/route", params={"q": "dirty csv to typed json"})
    r2 = client.get("/route", params={"q": "dirty csv to typed json"})
    assert r1.content == r2.content
    assert r1.status_code == 200
    b = r1.json()
    names = [t["tool"] for t in b["tools"][:5]]
    # recipe outranking its own units for a recipe-shaped query is
    # correct routing, not a regression; assert membership, not order
    # (bundle 71 note: nsegs are stemmed now — "typed" reaches
    # csv_types by NAME+TAG, 11 > csv_fix 9: a request for TYPED
    # json is type inference first; the old winner set stays valid)
    assert b["tools"][0]["tool"] in ("csv_fix", "csv_types",
                                     "recipe_clean_table",
                                     "recipe_data_trio")
    assert set(names) & {"csv_fix", "csv_types", "recipe_clean_table",
                         "recipe_data_trio"}
    assert all(t["score"] > 0 for t in b["tools"])
    scores = [t["score"] for t in b["tools"]]
    assert scores == sorted(scores, reverse=True)
    assert "sha256" in b
    # stop-words-only queries navigate to nothing, loudly and stably
    assert client.get("/route", params={"q": "the and to"}).json()["tools"] == []


def test_family_rail_points_storyboard_queries_at_moovicut():
    q = {"q": "storyboard my product launch"}
    r1 = client.get("/route", params=q)
    r2 = client.get("/route", params=q)
    assert r1.content == r2.content
    b = r1.json()
    assert b["elsewhere"][0]["url"] == "https://moovicut.studio"
    # data-shaped queries answer byte-identical to before: no rail key
    plain = client.get("/route",
                       params={"q": "dirty csv to typed json"}).json()
    assert "elsewhere" not in plain
    # the manifest carries the pointer for bots that never call /route
    assert "moovicut.studio" in client.get("/agent/manifest").text
    # both agent cards name the sister product
    assert "moovicut" in client.get("/").json()["family"]
    assert "moovicut" in client.get("/mcp").json()["family"]


def test_router_guards():
    r = client.get("/route", params={"q": "x" * 600})
    assert r.status_code == 400
    assert r.json()["error"] == "route_failed"
    r = client.get("/route", params={"q": "csv", "top": 0})
    assert r.status_code in (400, 422)
    assert "top" in r.text  # names the offending field, per B0.2


def test_recipe_clean_table_pipeline():
    dirty = "name,amount\r\nAlpha,1\r\nAlpha,1\r\nbeta, 2.5\r\nAlpha,1\r\n"
    r1 = client.post("/api/v1/recipe/clean-table", json={"csv": dirty})
    r2 = client.post("/api/v1/recipe/clean-table", json={"csv": dirty})
    assert r1.content == r2.content
    b = r1.json()
    assert b["steps"] == ["csv/fix", "values/normalize", "csv/types", "list/dedupe"]
    assert b["fix_notes"] == ["crlf_normalized"]
    assert b["removed_rows"] == 2
    # bundle 62 / gold B002 : les rows sont du TEXTE LITTÉRAL
    # normalisé — 2524.20 fondu en float perd la précision affirmée.
    assert b["rows"] == [{"name": "Alpha", "amount": "1"},
                         {"name": "beta", "amount": "2.5"}]
    assert b["columns"][1]["type"] == "float"
    assert "sha256" in b
    # a failing step returns its own repair prompt, untouched
    r = client.post("/api/v1/recipe/clean-table", json={"csv": ""})
    assert r.status_code == 400
    assert "CSV text with a header row" in r.text  # step 1's own prompt
    r = client.post("/api/v1/recipe/clean-table", json={"csv": "nobody"})
    assert r.status_code == 400
    assert "produced no rows" in r.text  # step 2 refuses, recipe passes it on


def test_recipe_clean_json_pipeline():
    r = client.post("/api/v1/recipe/clean-json",
                    json={"text": '{"a": 1}\n{"a": 2}'})
    b = r.json()
    assert b["repairs"] == ["jsonl_wrapped"]
    assert b["text"] == '[{"a":1},{"a":2}]'
    assert b["bytes"] == len(b["text"])
    r = client.post("/api/v1/recipe/clean-json",
                    json={"text": '{"a": 1}\n{"a": 2}', "style": "pretty"})
    assert "\n  {" in r.json()["text"]


def test_recipes_registry():
    r = client.get("/api/v1/recipes")
    b = r.json()
    assert sorted(b["recipes"]) == ["clean-json", "clean-table",
                                       "data-trio", "facts", "invoice",
                                       "partage-reste", "schedule",
                                       "shop-reste", "soldes2"]
    # le registre vendait 4 lignes alors que le manifest promet 9 recettes
    # depuis des bundles — la liste est désormais DÉRIVÉE de RECIPE_SPECS,
    # plus de main.py énuméré à la main (consigné bundle86, 24-11)
    assert "sha256" in b
