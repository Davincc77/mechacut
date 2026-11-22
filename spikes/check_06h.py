#!/usr/bin/env python3
# Verification live : /route x3 langues x2 outils + recherche landing x3 langues
import json, subprocess, urllib.parse

QUERIES = [
    ("units_shoe_size", ["shoe size eu to us conversion millimetres",
                         "quelle pointure eu us chaussure en millimetres",
                         "conversao tamanho sapato eu us milimetros"]),
    ("net_sri", ["subresource integrity hash for cdn script",
                 "attribut integrity script cdn hachage",
                 "atributo integrity hash script externo cdn"]),
]
for want, qs in QUERIES:
    for q in qs:
        url = "https://mechacut.studio/route?q=" + urllib.parse.quote(q)
        out = subprocess.run(["curl", "-s", "-m", "20", url],
                             capture_output=True, text=True).stdout
        top = json.loads(out)["tools"][0]["tool"]
        print("%-40s -> %-18s %s" % (q[:40], top, "OK" if top == want else "MISMATCH"))

# recherche landing (octets servis, NEGOCIATION : Accept: text/html sinon
# le / rend l'index JSON — lecon deja consignee, appliquee ici)
for lang in ("en", "fr", "pt"):
    page = subprocess.run(
        ["curl", "-s", "-m", "30", "-H", "Accept: text/html",
         "https://mechacut.studio/?lang=" + lang],
        capture_output=True, text=True).stdout
    print(lang, "| units_shoe_size in grid:", "units_shoe_size" in page,
          "| net_sri in grid:", "net_sri" in page,
          "| bytes:", len(page),
          "| e9 card:", ("One foot" if lang == "en" else
                         "Un pied" if lang == "fr" else
                         "Um pé") in page)
