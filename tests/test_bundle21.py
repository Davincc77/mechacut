"""Bundle 21 — INTAKE. La phrase humaine devient soit une fiche pré-remplie,
soit la question exacte à poser. Règles closes, déterministes, gratuites."""
import sys
sys.path.insert(0, ".")
import json
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def card(u):
    r = client.post("/api/v1/intent/card", json={"utterance": u})
    assert r.status_code == 200, r.text
    return r.json()


def test_ready_card_fills_from_words():
    d = card("round 1234.5678 to 2 places")
    assert d["status"] == "ready" and d["tool"] == "num_round"
    c = d["card"]
    assert c["value"]["state"] == "filled"
    assert str(c["value"]["value"]) == "1234.5678"
    assert c["places"]["value"] == 2
    assert c["mode"]["how"].startswith("schema default")
    assert d["missing_required"] == []


def test_enum_word_fills_algo():
    d = card("hash sha256 of the text: hello world mechacut and friends "
             "here to stay past the threshold for sure yes")
    assert d["tool"] == "hash_digest"
    assert d["card"]["algo"]["value"] == "sha256"


def test_short_utterance_does_not_become_a_document():
    d = card("slug this title please")
    assert d["status"] == "incomplete"
    assert "text" in d["missing_required"]
    assert "text" in d["question_human"]


def test_ambiguous_asks_which_one():
    d = card("format a number")
    assert d["status"] == "ambiguous"
    names = [c["tool"] for c in d["candidates"]]
    assert "num_format" in names
    assert d["question_human"].startswith("Which one did you mean")


def test_no_match_says_so():
    d = card("qwertyuiop zxcvbnmlkjh")
    assert d["status"] == "no_match"


def test_deterministic_and_pinned():
    a = card("round 1234.5678 to 2 places")
    b = card("round 1234.5678 to 2 places")
    assert a["sha256"] == b["sha256"]


def test_bad_input_free_400():
    r = client.post("/api/v1/intent/card", json={"utterance": "   "})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "utterance"


def test_surfaces():
    body = client.get("/api/v1/recipes").json()  # unaffected
    man = client.get("/agent/manifest").text
    assert "intent/card" in man
    tools = client.get("/mcp/tools").json() if False else None
    import main as m
    assert any(t["name"] == "intent_card" for t in m.MCP_TOOLS)


def test_intent_check_ok_before_you_pay():
    r = client.post("/api/v1/intent/check",
                    json={"tool": "num_round",
                          "args": {"value": "1234.5678", "places": 2}})
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True and d["problems"] == []
    assert d["next"] == "POST /api/v1/num/round"


def test_intent_check_missing_field():
    d = client.post("/api/v1/intent/check",
                    json={"tool": "hash_digest", "args": {}}).json()
    assert d["ok"] is False
    assert d["problems"][0]["field"] == "data"
    assert "data" in d["next"]


def test_intent_check_bad_enum():
    d = client.post("/api/v1/intent/check",
                    json={"tool": "hash_digest",
                          "args": {"data": "x", "algo": "crc999"}}).json()
    assert d["ok"] is False
    assert d["problems"][0]["field"] == "algo"
    assert "sha256" in d["problems"][0]["expected"]


def test_intent_check_unknown_tool():
    d = client.post("/api/v1/intent/check",
                    json={"tool": "does_not_exist", "args": {}}).json()
    assert d["ok"] is False
    assert d["problems"][0]["field"] == "tool"


def test_card_then_check_roundtrip():
    c = card("round 1234.5678 to 2 places")
    args = {f: v["value"] for f, v in c["card"].items()
            if v["state"] == "filled"}
    d = client.post("/api/v1/intent/check",
                    json={"tool": c["tool"], "args": args}).json()
    assert d["ok"] is True
