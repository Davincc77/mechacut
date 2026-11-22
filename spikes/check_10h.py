#!/usr/bin/env python3
# Verification live du cycle (10h) : manifest, 9 nouvelles pins rejouees
# contre golden, /route n°1 x3 langues x2 outils, MCP tools/call refus
# nomme, arete 180/181 min live, landing e10 x3 langues. curl : l'UA
# urllib est bloque par le bord du site (403), consigne ici pour les
# cycles suivants.
import hashlib
import json
import subprocess
import time
import urllib.parse

BASE = "https://mechacut.studio"


def curl(url, data=None, accept=None, status=False):
    cmd = ["curl", "-s", "-m", "30"]
    if status:
        cmd += ["-w", "\n%{http_code}"]
    if accept:
        cmd += ["-H", "Accept: " + accept]
    if data is not None:
        cmd += ["-H", "Content-Type: application/json", "-d",
                json.dumps(data), url]
    else:
        cmd.append(url)
    for attempt in range(4):
        out = subprocess.run(cmd, capture_output=True, text=True).stdout
        if status:
            body, _, code = out.rpartition("\n")
            if int(code) == 429:
                time.sleep(20)
                continue
            return int(code), json.loads(body) if body else None
        try:
            parsed = json.loads(out)
        except ValueError:
            time.sleep(20)
            continue
        if isinstance(parsed, dict) and parsed.get("error") == \
                "rate_limited":
            time.sleep(20)
            continue
        return parsed
    raise RuntimeError("429 persistant sur " + url)


def canon(o):
    return hashlib.sha256(json.dumps(
        o, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode()).hexdigest()


print("--- manifest (texte brut : /agent/manifest n'est PAS du JSON)")
man = subprocess.run(["curl", "-s", "-m", "30", BASE + "/agent/manifest"],
                     capture_output=True, text=True).stdout
print("0.80.0 header:", "0.80.0" in man and "134 deterministic" in man)

print("--- 9 nouvelles pins == golden")
golden = json.load(open("golden.json"))
integ = curl(BASE + "/integrity.json")
pins = {p["name"]: p for p in integ["pins"]}
names = [n for n in golden if n.startswith(("money_flight_comp_",
                                            "date_week_"))]
ok = 0
for name in names:
    p = pins[name]
    st, body = curl(BASE + p["path"], p["body"], status=True)
    h = "%d:%s" % (st, canon(body))
    same = h == golden[name]
    ok += same
    print("%-42s %s" % (name, "OK" if same else "DRIFT"))
print("pins OK: %d/%d" % (ok, len(names)))

print("--- /route n°1 x3 langues")
QUERIES = [
    ("money_flight_comp", ["flight compensation ec261 delayed",
                            "indemnite vol retard annulation ec261",
                            "compensacao voo atrasado direito europeu"]),
    ("date_week", ["iso week number of a date",
                   "numero de semaine iso 53 calendrier",
                   "numero da semana iso calendario"]),
]
for want, qs in QUERIES:
    for q in qs:
        top = curl(BASE + "/route?q=" + urllib.parse.quote(q)
                   )["tools"][0]["tool"]
        print("%-40s -> %-18s %s" % (
            q[:40], top, "OK" if top == want else "MISMATCH"))

print("--- arête stricte live + refus nommé (HTTP puis MCP)")
for dmin, exp in (("180", "€0"), ("181", "€600")):
    st, body = curl(BASE + "/api/v1/money/flight_comp",
                    {"regime": "EU", "flight_date": "2027-11-01",
                     "event": "delay", "distance_km": "5800",
                     "intra_eu": "no", "delay_min": dmin}, status=True)
    print("delay_min=%s -> %s %s" % (dmin, body["owed"]["display"],
                                     "OK" if body["owed"]["display"]
                                     == exp else "MISMATCH"))
st, body = curl(BASE + "/api/v1/date/week", {"iso": "2027-W53"},
                status=True)
print("HTTP 400 named:", st == 400 and
      "DOES NOT EXIST" in body["errors"][0]["message"])
r = curl(BASE + "/mcp", {"jsonrpc": "2.0", "id": 1,
                         "method": "tools/call",
                         "params": {"name": "date_week",
                                    "arguments": {"iso": "2026-W01-3"}}})
txt = json.dumps(r)
print("MCP tools/call inverse:", "2025-12-31" in txt)

print("--- landing e10 + catalogue x3 langues")
for lang in ("en", "fr", "pt"):
    page = subprocess.run(
        ["curl", "-s", "-m", "30", "-H", "Accept: text/html",
         BASE + "/?lang=" + lang],
        capture_output=True, text=True).stdout
    e10 = ("Delayed flight" if lang == "en" else
           "Vol retardé" if lang == "fr" else
           "Voo atrasado") in page
    chip = ("claim by 2028-08-01" if lang == "en" else
            "avant le 2028-08-01" if lang == "fr" else
            "até 2028-08-01") in page
    print(lang, "| e10:", e10,
          "| flight_comp card:", "money_flight_comp" in page,
          "| week card:", "date_week" in page,
          "| live chip:", chip, "| bytes:", len(page))
