#!/usr/bin/env python3
"""External continuity audit: corpus against LIVE mechacut.studio vs
golden.json. 0 drift = the deployed site replays the pinned bytes.

  python scripts/live_vs_golden.py

Politeness: paces < 30/min (our own rate limit), paid routes expected 402
(excluded), 429s retried, never retry-loops.
"""
import hashlib
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import payments  # noqa: E402


def canon(obj):
    return hashlib.sha256(json.dumps(
        obj, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode()).hexdigest()


def call(path, body):
    p = subprocess.run(
        ["curl", "-s", "-m", "20", "-w", "\n%{http_code}",
         "https://mechacut.studio" + path, "-X", "POST",
         "-H", "content-type: application/json",
         "-d", json.dumps(body, ensure_ascii=False)],
        capture_output=True, text=True)
    raw, _, code = p.stdout.rpartition("\n")
    status = int(code) if code.strip().isdigit() else -1
    return status, raw


def main():
    golden = json.loads((ROOT / "golden.json").read_text())
    checked = drift = paid = 0
    problems = []
    cases = {}
    for f in sorted((ROOT / "corpus").glob("*.json")):
        req = json.loads(f.read_text())
        cases[req.get("name", f.stem)] = req
    for name in sorted(golden):
        req = cases.get(name)
        if not req or name not in golden:
            continue
        if req["path"] in payments.PRICES:
            paid += 1
            continue
        if req.get("method", "POST").upper() == "GET":
            qs = "&".join("%s=%s" % (k, v) for k, v in
                          sorted((req.get("query") or {}).items()))
            p = subprocess.run(
                ["curl", "-s", "-m", "20", "-w", "\n%{http_code}",
                 "https://mechacut.studio" + req["path"] +
                 ("?" + qs if qs else "")],
                capture_output=True, text=True)
            raw, _, code = p.stdout.rpartition("\n")
            status = int(code) if code.strip().isdigit() else -1
        else:
            for attempt in range(3):
                status, raw = call(req["path"], req.get("body") or {})
                if status == 429:
                    time.sleep(2.5)
                    continue
                break
        if status == 429:
            problems.append((name, "still rate-limited"))
            drift += 1
            continue
        got = "%d:%s" % (status, canon(json.loads(raw)) if raw else "?")
        checked += 1
        if got != golden[name]:
            drift += 1
            problems.append((name, golden[name][:18], got[:18]))
        time.sleep(2.2)
    print("live-vs-golden: %d vérifiées, %d drift, %d payantes exclues"
          % (checked - drift, drift, paid))
    for x in problems:
        print("DRIFT:", x)
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
