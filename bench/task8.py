# bench v8 — le saut du 0.5b : multi-tâche impossible seul, 1 choix avec mechacut.
NOTE8 = """ALERT 2027-01-08 09:15 UTC: settlement lag on base-settlement. \
Exposure $12,450.75 (treasury) + $3,200.00 (market-making). 8.25% of batches \
stuck; 2.5% auto-retried; SLA report deadline 2027-01-11. Dashboard \
https://status.acme.dev/base-settlement, contact oncall@acme.dev. \
4213 delayed settlements. Recovery scheduled 2027-01-09."""


def expected8():
    # CALCULÉ À LA MAIN sur la note (pas copie-produit) — l'étalon d'honnêteté.
    # money: 12450.75 + 3200.00 → tri numérique asc ; total 15650.75
    # percent: 8.25, 2.5 → tri numérique asc ; date: 3 uniques (jours calendrier)
    # url: 1 ; email: 1
    return {
        "money": ["3200.00", "12450.75"],
        "percent": ["2.5", "8.25"],
        "date": ["2027-01-08", "2027-01-09", "2027-01-11"],
        "url": ["https://status.acme.dev/base-settlement"],
        "email": ["oncall@acme.dev"],
        "total_money": "15650.75",
    }


KEYS8 = list(expected8().keys())

ARM_A_TASK = """Read the incident note and answer with EXACTLY one JSON object \
and nothing else, with keys:
  {"money": [...], "percent": [...], "date": [...], "url": [...],
   "email": [...], "total_money": "..."}
money: each $ amount as a plain number string with 2 decimals, sorted \
ascending numerically. percent: number without % sorted ascending. date: the \
unique calendar dates YYYY-MM-DD sorted. url/email: the exact addresses found. \
total_money: the sum of the amounts, 2 decimals.
Note:

""" + NOTE8

ARM_B_TASK = ARM_A_TASK + """

You may instead use the mechacut suite: reply with EXACTLY one JSON object
{"steps": [{"tool": "...", "args": {...}}]} and nothing else.
Tools available (fill or reference values; $note is the incident note as-is):
  recipe_facts  args {"text": "<note or $note>"} -> the full answer: \
inventory {money,percent,date,url,email,...} sorted+canonical + total_money
  extract_facts args {"text": "...", "group": "kind"} -> raw values by kind \
(no totals, no canon)
  batch         args {"tool": "...", "payloads": [...]} -> run one tool N times
"""
