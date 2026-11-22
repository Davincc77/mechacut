"""Continuity harness: run the corpus against the app and compare SHA-256s.

Usage:
  python scripts/golden.py write   # (re)pin golden.json
  python scripts/golden.py check    # exit 1 on any drift
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

main.RATE_LIMIT = 10**9  # the harness itself must never be rate-limited
client = TestClient(main.app)
CORPUS = ROOT / "corpus"
GOLDEN = ROOT / "golden.json"


def canon(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode()
    ).hexdigest()


EXAMPLES = {}


def run_corpus():
    results = {}
    for f in sorted(CORPUS.glob("*.json")):
        req = json.loads(f.read_text())
        name = req.get("name", f.stem)
        if req.get("method", "POST").upper() == "GET":
            r = client.get(req["path"], params=req.get("query"))
        else:
            r = client.post(req["path"], json=req["body"])
        results[name] = f"{r.status_code}:{canon(r.json())}"
        try:
            payload = r.json()
            if isinstance(payload, dict):
                payload = {k: v for k, v in payload.items()
                           if k != "sha256"}
            blob = json.dumps(payload, sort_keys=True,
                              separators=(",", ":"), ensure_ascii=False)
        except ValueError:
            blob = (r.text or "")[:200]
        EXAMPLES[name] = {"path": req["path"],
                          "body": req.get("body"),
                          "query": req.get("query"),
                          "status": r.status_code,
                          "response": blob[:260] + ("…"
                                                    if len(blob) > 260
                                                    else "")}
    return results


def main_cli():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    current = run_corpus()
    if mode == "write":
        GOLDEN.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(f"wrote {len(current)} golden hashes")
        # integrity.json: the public replay checklist — anyone, from any
        # language, can re-derive every golden from production alone.
        # canon(response) == sha256 over the response JSON with sorted
        # keys, separators (",",":"), utf-8, ensure_ascii false.
        pins = []
        for f in sorted(CORPUS.glob("*.json")):
            req = json.loads(f.read_text())
            name = req.get("name", f.stem)
            status, _, sha = current[name].partition(":")
            pin = {"name": name, "path": req["path"],
                   "status": int(status), "sha256": sha}
            if req.get("method", "POST").upper() == "GET":
                pin["method"] = "GET"
                pin["query"] = req.get("query") or {}
            else:
                pin["body"] = req["body"]
            import payments as _pay
            if req["path"] in _pay.PRICES:
                pin["requires_payment"] = True
                pin["price_atomic"] = _pay.PRICES[req["path"]]
            pins.append(pin)
        (ROOT / "integrity.json").write_text(json.dumps({
            "canonicalization": "sha256(json.dumps(response, sort_keys=True,"
                                " separators=(',',':'), ensure_ascii=False)"
                                ".encode())",
            "how_to_verify": "POST path+body to mechacut.studio (free pins"
                             " as-is; paid pins need one x402 call), canon"
                             " the response, compare sha256. Additions-"
                             "only history: every pin ever written stays.",
            "pins": pins}, indent=1, sort_keys=True) + "\n")
        print(f"wrote integrity.json with {len(pins)} replayable pins")
        # landing lazy-file: per-tool real request + response, captured
        # by RUNNING the corpus — the site's examples cannot lie because
        # they are the build's own stdout.
        by_tool = {}
        for f in sorted(CORPUS.glob("*.json")):
            req = json.loads(f.read_text())
            name = req.get("name", f.stem)
            by_tool[req["path"]] = EXAMPLES.get(name)
        (ROOT / "static" / "agent_examples.json").write_text(
            json.dumps({"generated_from": "corpus @ golden write",
                        "examples": by_tool},
                       separators=(",", ":"), sort_keys=True,
                       ensure_ascii=False), encoding="utf-8")
        print("wrote static/agent_examples.json (%d paths)"
              % len(by_tool))
        return 0
    if not GOLDEN.exists():
        print("no golden.json yet; run: python scripts/golden.py write")
        return 1
    golden = json.loads(GOLDEN.read_text())
    drift = [k for k in golden if golden.get(k) != current.get(k)]
    new = [k for k in current if k not in golden]
    if drift or new:
        if drift:
            print("DRIFT:", ", ".join(drift))
        if new:
            print("UNPINNED:", ", ".join(new))
        return 1
    print(f"OK: {len(golden)} golden hashes match")
    return 0


if __name__ == "__main__":
    sys.exit(main_cli())
