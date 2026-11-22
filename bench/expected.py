"""Pin the canonical answer: run the gold pipeline through the endpoints.

  python bench/expected.py write  -> bench/expected.sha + prints the YAML
  python bench/expected.py check  -> fail if the pipeline drifts
"""
import hashlib
import json
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "bench")
import task_data
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def gold_doc():
    rows = client.post("/api/v1/recipe/clean-table",
                       json={"csv": task_data.DIRTY_CSV}).json()["rows"]
    totals = client.post("/api/v1/json/repair",
                         json={"text": task_data.BROKEN_JSON}).json()["output"]
    urls = client.post("/api/v1/list/dedupe",
                       json={"items": task_data.URLS,
                             "mode": "url"}).json()["output"]
    return {"rows": rows, "totals": totals, "urls": urls}


def gold_yaml():
    doc = gold_doc()
    text = client.post("/api/v1/format/convert",
                       json={"input": json.dumps(doc, ensure_ascii=False),
                             "from": "json", "to": "yaml"}).json()["output"]
    # the answer is the parsed doc, not the bytes: int/float/str are what
    # the task asked for, and the scorer parses YAML back to a doc anyway
    import yaml
    back = yaml.safe_load(text)
    assert json.dumps(back, sort_keys=True) == json.dumps(
        doc, sort_keys=True), "yaml round-trip must be lossless"
    return text


def sha():
    return hashlib.sha256(task_data.canonical_of(gold_doc())).hexdigest()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    s = sha()
    if mode == "write":
        open("bench/expected.sha", "w").write(s + "\n")
        print(gold_yaml())
        print("pinned:", s)
    else:
        pinned = open("bench/expected.sha").read().strip()
        assert s == pinned, "gold pipeline drifted: %s != %s" % (s, pinned)
        print("gold pipeline matches pinned sha:", s)
