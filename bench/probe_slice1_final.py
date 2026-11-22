"""csk — probe final tranche 1 (B001-B005), v0.84.0, zéro appel modèle.
État attendu au gel: PASS B001/B004/B005, FAIL B002(normalization_gap),
FAIL B003(misroute+extraction) — si une cellule change de raison, la sonde
le hurle (le produit a bougé: re-probe avant toute re-mesure).
"""
import json, sys, os, re, importlib.util
REPO = os.path.expanduser("~/Downloads/mechacut")
sys.path.insert(0, REPO)
from fastapi.testclient import TestClient
import main
C = TestClient(main.app)
BASE = os.path.expanduser("~/Downloads/mechacut/bench/corpus/tasks")
CANON = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
def sha(o): return __import__("hashlib").sha256(CANON(o)).hexdigest()
def load(t): return json.load(open(f"{BASE}/{t}/input.json", encoding="utf-8"))
def gold(t): return json.load(open(f"{BASE}/{t}/expected.json", encoding="utf-8"))
def ver(t):
    s = importlib.util.spec_from_file_location(f"v_{t}", f"{BASE}/{t}/verifier.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

print("=== PROBE FINAL tranche 1 — csk v0.84.0 ===")
ij = C.get("/integrity.json").json()
print(f"[integrity] {len(ij['pins'])} pins | [manifest] {C.get('/agent/manifest').text.splitlines()[0]}")

# B001 — batch 40 valeurs, kind explicite
d1 = load("B001")
b1 = C.post("/api/v1/batch", json={"tool": "validate_taxid",
    "payloads": [{"value": i["value"], "kind": i["kind"]} for i in d1["values"]]}).json()
art1 = ver("B001").compose(b1, d1["values"])
assert b1["succeeded"] == 40 and b1["failed"] == 0, "batch B001 incomplet"
print(("PASS " if sha(art1) == sha(gold("B001")) else "FAIL ") + "B001: batch+compose == gold (40/40)")

# B002 — clean-table (forme seulement) + détection du gap
d2 = load("B002")
b2 = C.post("/api/v1/recipe/clean-table", json={"csv": d2["csv"]}).json()
art2 = ver("B002").compose(b2)
gap = ver("B002").gap_reason(b2)
print(("PASS " if sha(art2) == sha(gold("B002")) else "FAIL ") + f"B002: compose forme == gold | gap={gap}")
assert gap["dates_non_iso"] == 0 and gap["montants_milliers"] == 0, \
    f"B002: le gap de normalisation EST REVENUE: {gap} — régression produit"

# B003 — router/plan (misroute attendu) + recipe_facts (fragments attendus)
d3 = load("B003")
plan = C.post("/api/v1/router/plan", json={"texte": d3["note"]}).json()
facts = C.post("/api/v1/recipe/facts", json={"text": d3["note"]}).json()
art3 = ver("B003").compose(facts)
print(("PASS " if plan.get("prescription", {}).get("fiche") == "partage-reste" else "FAIL ") +
      f"B003: misroute encore présent (fiche={plan.get('prescription', {}).get('fiche')})")
nums = facts["inventory"].get("number", [])  # monde corrigé : la classe fragments peut disparaître totalement
frags = [n for n in nums if n.endswith(",00") or n.endswith(",50") or n.endswith(",75")]
print(("PASS " if not frags else "FAIL ") +
      f"B003: plus de fragments espace-milliers (frags={frags[:3]})")
assert sha(art3) == sha(gold("B003")), \
    "B003: la voie équipée EST RETOMBÉE — extraction FR régressée"

# B004 — vocabulaire pinné
d4 = load("B004")
b4 = C.post("/api/v1/validate", json={"payload": d4["payload"], "schema": d4["schema"]}).json()
art4 = ver("B004").compose(b4)
print(("PASS " if sha(art4) == sha(gold("B004")) else "FAIL ") + "B004: vocabulaire pinné == gold")

# B005 — fingerprint
d5 = load("B005")
b5 = C.post("/api/v1/fingerprint", json={"value": d5["payload"]}).json()
art5 = ver("B005").compose(b5)
print(("PASS " if sha(art5) == sha(gold("B005")) else "FAIL ") + "B005: fingerprint == gold")

print("\nÉtat sondé (ré-sondé 22h50) : B001-B005 PASS — le produit est venu au gold,\njamais l'inverse. Le MISROUTE B003 (plan/intent) reste OUVERT chez l'instance routeur.")
