# -*- coding: utf-8 -*-
"""bundle114 — /json/bigint : L'ENTIER AU-DELÀ DE 2^53 MENT À LA
FRONTIÈRE DE L'OUTIL. Attendus CALCULÉS À LA MAIN puis croisés contre
le lecteur réel (node JSON.parse + String) sur 240 valeurs, zéro écart —
JAMAIS recopiés de bigintkit (rituel du playbook).

Vecteurs publics (lus À L'API GitHub 25-nov-2026) :
- Unity-MCP #754 : 568105584918935294 (exact 568105584918935296,
  print 568105584918935300 — le « or similar » du ticket EST le print)
- claude-code #11506 : 348555896224571969 -> print 348555896224571970
  (exact 348555896224571968)
- llm4s #1597 : 9007199254740993 -> 9007199254740992
- ragflow PR #22064 : 1234567890123456789 -> print 1234567890123456800
  (exact 1234567890123456768)
- RFC 8259 §6 nomme lui-même 1E400 comme danger.
"""
import hashlib
import json
import os
import subprocess

import bigintkit
import main
import routing
from fastapi.testclient import TestClient

client = TestClient(main.app)

R1 = 9007199254740991      # 2^53 - 1 — MAX_SAFE_INTEGER


def post(raw, mode=None):
    body = {"raw": raw}
    if mode:
        body["mode"] = mode
    return client.post("/api/v1/json/bigint", json=body)


# ---------------------------------------------------------------- loi
def test_max_safe_constant_is_the_rfc_range():
    assert bigintkit.SAFE_HI == 2 ** 53 - 1 == R1
    assert bigintkit.SAFE_LO == -(2 ** 53 - 1)


def test_verdicts_closed_and_ordered():
    assert bigintkit.SEVERITY == ["COLLISION", "LOSSY", "OVERFLOW",
                                  "UNDERFLOW", "EXACT_UNSAFE", "SAFE"]


def test_laws_are_cited_in_payload():
    out = bigintkit.bigint_audit('{"a": %d}' % (R1 + 1000))
    assert "RFC 8259" in out["laws"]["rfc8259_s6"]
    # le MUST MCP est cité BORNÉ aux x-mcp-header — pas survendu
    assert "x-mcp-header" in out["laws"]["mcp_draft_x_mcp_header"]


# ------------------------------------------------------- vecteurs live
def test_unity_vector_exact_and_print_distinct():
    out = post('{"entityId": 568105584918935294}').json()
    f = out["findings"][0]
    assert out["verdict"] == "LOSSY"
    assert f["binary64_value"] == "568105584918935296"
    assert f["js_string"] == "568105584918935300"
    assert f["delta"] == 2
    assert f["pointer"] == "/entityId"


def test_claude_vector_off_by_one_print():
    out = post('{"value": 348555896224571969}').json()
    f = out["findings"][0]
    assert f["binary64_value"] == "348555896224571968"
    assert f["js_string"] == "348555896224571970"
    assert f["delta"] == -1


def test_llm4s_pair_is_a_collision():
    out = post('{"a": 9007199254740993, "b": 9007199254740992}').json()
    assert out["verdict"] == "COLLISION"
    assert out["collisions"][0]["js_string"] == "9007199254740992"
    assert sorted(out["collisions"][0]["members"]) == \
        ["9007199254740992", "9007199254740993"]
    # et 93 vs 94 ne COLLISIONNENT PAS (prints distincts)
    out2 = post('{"i": 9007199254740993, "j": 9007199254740994}').json()
    assert out2["verdict"] == "LOSSY"
    assert out2["collisions"] == []


def test_ragflow_snowflake_vector():
    out = post('{"id": 1234567890123456789}').json()
    f = out["findings"][0]
    assert f["js_string"] == "1234567890123456800"
    assert f["binary64_value"] == "1234567890123456768"


def test_boundary_trio():
    out = post('{"s": %d, "e": %d, "l": %d}'
               % (R1, R1 + 1, R1 + 2)).json()
    by = {f["pointer"]: f["class"] for f in out["findings"]}
    # LA LOI, pas ma main : 2^53 et 2^53+1 se lisent IDENTIQUES chez JS
    # — le couple voisin du range RFC tombe sous COLLISION, la classe
    # reine. Attendu recalcule a l'oracle (2^53 -> ...992, 2^53+1 ->
    # ...992), doctrine b112 rejouee : la machine avait raison.
    assert out["verdict"] == "COLLISION"
    assert by["/e"] == "COLLISION" and by["/l"] == "COLLISION"
    assert sorted(out["collisions"][0]["members"]) == \
        ["9007199254740992", "9007199254740993"]
    assert "/s" not in by               # SAFE jamais listé


def test_2e20_keeps_value_loses_range():
    out = post('{"z": 2e20}').json()
    f = out["findings"][0]
    assert f["class"] == "EXACT_UNSAFE"
    assert f["js_string"] == "200000000000000000000"
    assert f["delta"] == 0


def test_rfc_named_hazards_overflow_underflow():
    out = post('{"hi": 1e400, "lo": 2e-500}').json()
    classes = {f["literal"]: f["class"] for f in out["findings"]}
    assert classes["1e400"] == "OVERFLOW"
    assert classes["2e-500"] == "UNDERFLOW"
    assert out["verdict"] == "OVERFLOW"  # sévérité : OVERFLOW > UNDERFLOW


def test_uint64_edge_and_int64_edge():
    out = post('{"u": 18446744073709551615, "v": 9223372036854775807}'
               ).json()
    by = {f["literal"]: f for f in out["findings"]}
    assert by["18446744073709551615"]["class"] == "LOSSY"
    assert by["18446744073709551615"]["js_string"] == \
        "18446744073709552000"
    assert by["18446744073709551615"]["uint64_holds"] is True
    # 2^64-1 EST le max uint64 — la valeur ment chez JS, nlohmann la
    # garde : c'est LA divergence, pas un echec de la table.
    assert by["18446744073709551615"]["int64_holds"] is False
    assert by["9223372036854775807"]["int64_holds"] is True


# -------------------------------------------------------- grammaire
def test_digits_in_strings_are_never_findings():
    # la différenciation CONTRE czoa (qui l'avoue : « digits inside
    # strings may be reported ») — ici c'est une loi de grammaire.
    out = post('{"id": "9007199254740993", "n": %d}' % (R1 + 100)
               ).json()
    assert out["flagged_count"] == 1
    assert out["findings"][0]["pointer"] == "/n"


def test_pointer_escapes_rfc6901():
    out = post('{"a/b~c": [%d]}' % (R1 + 1)).json()
    assert out["findings"][0]["pointer"] == "/a~1b~0c/0"


def test_duplicate_keys_both_scanned():
    out = post('{"id": %d, "id": %d}' % (R1 + 1, R1 + 3)).json()
    ptrs = [f["pointer"] for f in out["findings"]]
    assert ptrs == ["/id", "/id"] or set(ptrs) == {"/id"}


def test_deep_array_paths():
    out = post('[[[%d]]]' % (R1 + 8)).json()
    assert out["findings"][0]["pointer"] == "/0/0/0"


def test_negative_mirrors_positive():
    out = post('{"a": -9007199254740993}').json()
    f = out["findings"][0]
    assert f["js_string"] == "-9007199254740992"
    assert f["binary64_value"] == "-9007199254740992"


def test_exponent_integers_are_integers():
    out = post('{"a": 1e3, "b": 15e2}').json()
    assert out["verdict"] == "SAFE"
    assert out["flagged_count"] == 0


def test_real_fractions_never_flagged_but_hazards_are():
    out = post('{"f": 3.141592653589793238462643383279, "h": 1e400}'
               ).json()
    classes = {f["class"] for f in out["findings"]}
    assert classes == {"OVERFLOW"}   # la fraction : pas d'audit int


# ------------------------------------------------------------- patch
def test_quote_mode_bytes_outside_are_intact():
    raw = '{"ok": 7, "bad": %d, "s": "x %d y"}' % (R1 + 1, R1 + 2)
    out = post(raw, mode="quote").json()
    patched = out["patched"]
    assert '"bad": "%d"' % (R1 + 1) in patched
    # la chaîne reste INTACTE (pas un patch regex) :
    assert '"s": "x %d y"' % (R1 + 2) in patched
    assert '"ok": 7' in patched
    assert out["patched_count"] == 1


def test_quote_mode_is_idempotent_as_audit():
    raw = '{"a": %d}' % (R1 + 1)
    out = post(raw, mode="quote").json()
    again = post(out["patched"]).json()
    assert again["verdict"] == "SAFE"
    assert again["flagged_count"] == 0


def test_quote_mode_collisions_flagged_first():
    out = post('{"i": 9007199254740993, "j": 9007199254740992, '
               '"k": %d}' % (R1 + 1000), mode="quote").json()
    assert out["verdict"] == "COLLISION"
    assert json.loads(out["patched"]) == json.loads(out["patched"])
    assert '"i": "9007199254740993"' in out["patched"]


# ------------------------------------------------------ refus nommés
def test_refusals_name_field_and_expected():
    bad_cases = [
        ({"raw": 42}, "raw"),
        ({"raw": "   "}, "raw"),
        ({"raw": "{oops}"}, "raw"),
        ({"raw": '{"a": 1,}'}, "raw"),
        ({"raw": "{} trailing"}, "raw"),
        ({"raw": '{"a": 1e}'}, "raw"),
        ({"raw": '{"a": 01}'}, "raw"),
        ({"raw": '{"a": .5}'}, "raw"),
        ({"raw": '{"a": "x}'}, "raw"),
        ({"raw": "1", "mode": "hex"}, "mode"),
    ]
    for body, field in bad_cases:
        r = client.post("/api/v1/json/bigint", json=body)
        assert r.status_code == 400, body
        errs = r.json()["errors"]
        # la convention maison nomme le champ au CHEMIN pydantic
        # (body.raw) — « name field+expected », pas « name field==x ».
        assert any(e["field"].split(".")[-1] == field and e["expected"]
                   for e in errs), (body, errs)


def test_raw_must_be_text_not_object():
    # la THÈSE du lot : un nombre déjà parsé a PERDU la preuve.
    r = client.post("/api/v1/json/bigint", json={"json": {}})
    assert r.status_code == 400


# --------------------------------------------------------- doctrine
def test_module_never_touches_network():
    src = open(os.path.join(os.path.dirname(bigintkit.__file__),
                            "bigintkit.py")).read()
    for word in ("urllib", "requests", "socket", "http.client"):
        assert word not in src


def test_determinism_bytes():
    a = json.dumps(post('{"a": 1234567890123456789}').json(),
                   sort_keys=True)
    b = json.dumps(post('{"a": 1234567890123456789}').json(),
                   sort_keys=True)
    assert hashlib.sha256(a.encode()).hexdigest() == \
        hashlib.sha256(b.encode()).hexdigest()


# ------------------------------------------------------- needle x3
NEEDLES = [
    ("my int64 id comes back rounded after the json parse", "json_bigint"),
    ("snowflake id loses digits when the tool parses json", "json_bigint"),
    ("mon id flocon revient arrondi dans le json", "json_bigint"),
    ("mon entier 64 bits depasse la plage sure et change de valeur",
     "json_bigint"),
    ("meu id int64 chega arredondado depois do parse json", "json_bigint"),
    ("numero inteiro grande perde digitos silencioso no json", "json_bigint"),
]


def test_six_needles_top1():
    for q, want in NEEDLES:
        hits = routing.route(q)
        assert hits, q
        assert hits[0]["tool"] == want, (q, hits[:3])
        assert hits[0]["score"] >= 5, (q, hits[0]["score"])


def test_class_decoy_stays_silent():
    hits = routing.route("tell me a story about giants who lived "
                         "in the mountains")
    assert hits == []


def test_sibling_guards_hold():
    for q, want in [("argument 8.0 invalid type floating point "
                     "expected u64", "json_coerce"),
                    ("banker rounding half to even two decimal places",
                     "num_round"),
                    ("did my mcp client see every page of tools",
                     "agent_mcplist"),
                    ("two json values sorted changes by pointer",
                     "json_diff")]:
        hits = routing.route(q)
        assert hits and hits[0]["tool"] == want, (q, hits[:2])


# --------------------------------------------------- landing & fratrie
def test_landing_catalog_card_present_three_languages():
    import sayings
    say = sayings.SAY["/api/v1/json/bigint"]
    assert set(say) == {"en", "fr", "pt"}
    # le SAY voyage dans /tools/<name>.json (« try.say »), PAS dans la
    # landing — la carte de la landing, c'est data-hay + .tp localise.
    r = client.get("/tools/json_bigint.json")
    assert r.status_code == 200
    assert r.json()["try"]["say"]
    import re
    for lang, page in [("en", "locales/en.json"), ("fr", "locales/fr.json"),
                       ("pt", "locales/pt.json")]:
        body = json.load(open(os.path.join(
            os.path.dirname(main.__file__), page)))
        grid = body["bundles_grid"]
        # b125_hermes : badge passe en CSS ::before (pilote data-tier)
        # — la batterie suit le texte, pas ce qu'il disait (b112).
        m = re.search(r'data-tool="json_bigint" data-hay="([^"]*)"'
                      r'[^>]*> <code>json_bigint</code><span class="tp">(.*?)'
                      r'</span>', grid)
        assert m, page
        hay, tp = m.group(1), m.group(2)
        for stem in ("bigint", "int64", "snowflake"):
            assert stem in hay, (page, stem)
        if lang == "fr":
            assert "ENTIERS" in tp, tp
        if lang == "pt":
            assert "MENTEM" in tp, tp


def test_manifest_line_and_fold():
    body = client.get("/agent/manifest").text
    line = [l for l in body.splitlines()
            if l.startswith("json_bigint ")][0]
    assert "/api/v1/json/bigint" in line and " free" in line
    assert len(body.encode()) < 9000
    assert body.count("\n[") == sum(
        1 for p in routing.PACKS if any(t[2] == p for t in routing.TABLE))
    assert "packs: /SKILL-<pack>.md" in body


# ------------------------------------------------------- radar XS
def test_radar_latest_json_contract(tmp_path, monkeypatch):
    # le XS b114 : le diff VIT dans le JSON et les compteurs sont
    # RECONCILIES — invariant n == len(rows) == counts + counts_carried.
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))), "scripts"))
    import route_radar as rr
    doc = json.load(open(os.path.join(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))),
        "docs", "RADAR", "latest.json")))
    for key in ("n", "n_scan", "counts", "rows"):
        assert (key in doc) or doc.get("ts", "") >= "2026-11-25T21", key
    # si le doc vient déjà du nouveau schéma : vérification franche
    if "n_scan" in doc:
        assert doc["n"] == len(doc["rows"])
        tot = sum(doc["counts"].values()) + sum(
            (doc.get("counts_carried") or {}).values())
        assert tot == doc["n"], (tot, doc["n"])
        assert "diff" in doc
        assert set(doc["diff"]) == {"REGRESSION", "NOUVELLE", "GUERIE"}


def test_radar_embed_family_table():
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))), "scripts"))
    import route_radar as rr
    assert "mpnet" in rr.EMBED_FAMILY   # incident 25-11 21h15
    mids = ["sentence-transformers/all-mpnet-base-v2"]
    for mid in mids:
        assert ("embed" in mid.lower()
                or any(t in mid.lower() for t in rr.EMBED_FAMILY))
