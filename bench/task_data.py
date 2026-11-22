"""The fixed benchmark task (bench/task.md is its human spec).

One task, four pipeline steps, one canonical answer. Arm A: the model does
everything in its own context. Arm B: the model gets the mechacut manifest
and calls endpoints. Same prompt text, same data, temp=0, same seed.

Data is frozen (generated once, seed 20261120): 40 CSV lines (30 unique + 10
dupes in three padding styles), a 12-item single-quoted JSON blob, 18 URLs with 
case/slash variants. Sized so in-context doing is error-prone for sub-7B models.
"""

DIRTY_CSV = 'id,name,score\r\n3,Mia,29.78 \r\n34,Yara, 45.98\r\n20,Rene,40.34\r\n7,Omar,95.05 \r\n14,Yara, 65.42\r\n11,Kofi,46.77 \r\n5, Ivo , 14.63\r\n10,Lena, 22.32\r\n22,Luc, 68.6\r\n33, Sven , 82.24\r\n24,Zoe,77.05\r\n35,Tomas,97.66 \r\n36,Ines,27.73\r\n39,Dario,57.43 \r\n1, Ana , 44.46\r\n2,Luc, 51.88\r\n16,Ines,30.31\r\n9, Piotr , 13.37\r\n26,Nina, 35.61\r\n23,Mia,37.12 \r\n40,Rene,96.35\r\n6,Nina, 11.4\r\n32,Rita,52.36\r\n38,Freya, 1.34\r\n25, Ivo , 58.74\r\n15,Tomas,30.29 \r\n27,Omar,43.43 \r\n37, Milan , 63.6\r\n4,Zoe,21.87\r\n31,Kofi,86.04 \r\n5, Ivo,14.63 \r\n11, Kofi,46.77 \r\n9, Piotr,13.37 \r\n3, Mia,29.78 \r\n2, Luc,51.88 \r\n37, Milan,63.6 \r\n36, Ines,27.73 \r\n6, Nina,11.4 \r\n33, Sven,82.24 \r\n25, Ivo,58.74 \r\n'

BROKEN_JSON = "{'total': 2684.35, 'currency': 'EUR', 'vendor': 'ACME', 'items': [{'n': 'Rene', 'v': 46.74,}, {'n': 'Ana', 'v': 25.68,}, {'n': 'Luc', 'v': 28.39,}, {'n': 'Mia', 'v': 36.46,}, {'n': 'Zoe', 'v': 16.77,}, {'n': 'Ivo', 'v': 23.69,}, {'n': 'Nina', 'v': 6.11,}, {'n': 'Omar', 'v': 27.42,}, {'n': 'Vera', 'v': 48.79,}, {'n': 'Piotr', 'v': 19.02,}, {'n': 'Lena', 'v': 22.88,}, {'n': 'Kofi', 'v': 12.89,},],}"

URLS = ['https://a.io/x', 'https://b.io/', 'https://c.io/y', 'https://d.io/z', 'https://e.io/q', 'https://f.io/r', 'https://g.io/s', 'https://h.io/t', 'https://i.io/u', 'HTTP://A.IO/x', 'https://b.io', 'HTTPS://C.IO/y', 'https://d.io/z/', 'https://e.io/q', 'https://f.io/R', 'https://g.io/s/', 'https://H.IO/t', 'https://i.io/u/']


SCHEMA = {
    "type": "object",
    "required": ["rows", "totals", "urls"],
    "properties": {
        "rows": {"type": "array"},
        "totals": {"type": "object"},
        "urls": {"type": "array"},
    },
}

TASK_TEXT = (
    "You will get three pieces of raw data. Produce ONE final YAML document "
    "and nothing else.\n\nSteps:\n"
    "1. Clean this CSV (CRLF and padding noise), keep first occurrence of "
    "duplicate rows,\ntypes: id=int, name=string, score=float.\n"
    "CSV_START\n%s\nCSV_END\n"
    "2. Repair this broken JSON (single quotes, trailing commas):\n"
    "JSON_START\n%s\nJSON_END\n"
    "3. Deduplicate these URLs (scheme case ignored, host case-insensitive, "
    "a single\ntrailing slash does not change the URL), first occurrence "
    "order kept:\n%s\n\n"
    "The final YAML must have exactly the keys:\n"
    "  rows:   the cleaned, typed, deduplicated CSV rows (list of objects)\n"
    "  totals: the repaired JSON object\n"
    "  urls:   the deduplicated URL list\n"
    "Reply with the YAML document only, no prose, no fences.\n"
) % (DIRTY_CSV, BROKEN_JSON, "\n".join("- " + u for u in URLS))


def canonical_of(doc):
    """Canonical JSON bytes of a parsed final answer (scoring form)."""
    import json
    return json.dumps(doc, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
