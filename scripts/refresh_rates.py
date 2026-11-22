#!/usr/bin/env python3
"""Regenerate data/ecb_history.json from the ECB 90-day feed.
Run before a deploy to move the archive window forward; the endpoint
never rewrites this file itself (a GET does not mutate the repo)."""
import httpx
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

FEED = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
out = {}
r = httpx.get(FEED, timeout=30, headers={"User-Agent": "mechacut/1.0"})
r.raise_for_status()
root = ET.fromstring(r.content.decode("windows-1252"))
for cube in root.iter():
    if cube.tag.rsplit("}", 1)[-1] == "Cube" and "time" in cube.attrib:
        day = cube.attrib["time"]
        rates = {"EUR": "1"}
        for c2 in cube:
            if c2.tag.rsplit("}", 1)[-1] == "Cube":
                rates[c2.attrib["currency"]] = c2.attrib["rate"]
        if len(rates) > 5:
            out[day] = rates
dst = Path(__file__).resolve().parents[1] / "data" / "ecb_history.json"
dst.write_text(json.dumps(
    {"provenance": "ECB eurofxref-hist-90d.xml, fetched %s" % max(out),
     "days": out}, sort_keys=True, separators=(",", ":")))
print("refreshed:", len(out), "days,", min(out), "->", max(out))
