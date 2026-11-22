# bench v11 — « là où même un 8B local ne peut PAS » (gelé 2026-11-22)
#
# Design hostile au nu, amical au relais : chaque gold est soit
# MEMORISTIQUEMENT IMPOSSIBLE (dates hors corpus, hashs, sommes exactes
# sur 25+ lignes), soit structurellement hors portée (compter des
# occurrences RRULE), soit un piège où la réponse « évidente » est
# fausse. Une seule exception assumée : v11_recurring = le modèle est
# AUTORISE a écrire du code (thèse Mechacut : code écrit par un LLM =
# retry infini ; code remplacé par le serveur = un appel).
#
# 15 tâches. Golds dans golden11.py (oracles purs, graines figées).
# Shortlist gelée = celle de v10 + /api/v1/date/relative déjà listée.

import random as _r

_r.seed(1101)  # graine figée, écrite ici : les données sont reproductibles


def _csv():
    rows = ["facture,montant"]
    vals = []
    for i in range(25):
        v = _r.randint(100, 9999) / 100.0
        if i % 3 == 0:
            v += 1000.0          # lignes à milliers : LA valeur affichée
        vals.append(v)
        cell = ("{:,.2f}").format(v)
        if "," in cell:
            cell = '"%s"' % cell      # CSV honnête : champ entre guillemets
        rows.append("l%d,%s" % (i + 1, cell))
    return "\n".join(rows), vals


CSV11, VALS11 = _csv()

TASKS11 = [
 {"id": "v11_hash_stack", "cmp": "exact", "n": 1,
  "naked": "Definition: H(x) = last 12 hex chars of SHA-256 of x (x is "
           "UTF-8 text). Compute H(H(H('mechacut-v11'))) — apply H three "
           "times, innermost first. Answer EXACTLY: <12 hex>",
  "run": "/api/v1/pipeline",
  "b_args": {"steps": "$recipe"},
  "recipe": [
      {"tool": "hash_digest",
       "args": {"data": "mechacut-v11", "algo": "sha256"}},
      {"tool": "hash_digest",
       "args": {"data": {"$from": [0, "hex"]}, "algo": "sha256"}},
      {"tool": "hash_digest",
       "args": {"data": {"$from": [1, "hex"]}, "algo": "sha256"}}],
  "extract": "tail12_last_hex"},
 {"id": "v11_sha512_64", "cmp": "exact", "n": 1,
  "naked": "SHA-512 hex digest (128 chars) of the exact UTF-8 bytes of "
           "the string mechacut-v11-stack. No newline. Answer EXACTLY: "
           "<128 hex>",
  "run": "/api/v1/hash/digest",
  "b_args": {"data": "s1", "algo": "sha512"},
  "data": {"s1": "mechacut-v11-stack"}},
 {"id": "v11_biz_holidays", "cmp": "exact", "n": 1,
  "naked": "Start Monday 2026-12-14. Add 15 BUSINESS days (Mon-Fri), "
           "then skip again any date falling on 2026-12-25 or "
           "2027-01-01 (holidays count as non-business). Land on which "
           "ISO date? Answer EXACTLY: <YYYY-MM-DD>",
  "run": "/api/v1/date/calc",
  "b_args": {"base": "2026-12-14", "op": "business_days",
             "params": {"n": 15,
                        "holidays": ["2026-12-25", "2027-01-01"]}},
  "data": {}},
 {"id": "v11_diff_biz_hol", "cmp": "exact", "n": 1,
  "naked": "How many business days (Mon-Fri) between 2027-01-04 and "
           "2027-01-29 INCLUSIVE of both ends, excluding the holiday "
           "2027-01-18? Answer EXACTLY: <integer>",
  "run": "/api/v1/date/calc",
  "b_args": {"base": "2027-01-04", "op": "diff",
             "params": {"until": "2027-01-29", "unit": "business_days",
                        "holidays": ["2027-01-18"]}},
  "data": {}},
 {"id": "v11_csv_max", "cmp": "exact", "n": 1,
  "naked": "Below is a CSV 'facture,montant' with 25 rows; montant "
           "uses US style: comma is the THOUSANDS separator (such "
           "values are double-quoted per RFC 4180), dot the decimal "
           "point. Give the LARGEST montant value, written with "
           "2 decimals and no thousands separator. DATA:\n" + CSV11 +
           "\nAnswer EXACTLY: <max>",
  "run": "/api/v1/csv/types",
  "b_args": {"csv": "c1"},
  "data": {"c1": CSV11},
  "extract": "max_types"},
 {"id": "v11_isbn10", "cmp": "exact", "n": 1,
  "naked": "ISBN-10 check digit: weights 10,9,8,...,2 over the first "
           "9 digits, sum mod 11, check = (11 - mod) mod 11, 'X' if 10. "
           "Payload 043942089. Give the check character. Answer "
           "EXACTLY: <char>",
  "run": "/api/v1/id/checkdigit",
  "b_args": {"mode": "generate", "scheme": "isbn10", "value": "p1"},
  "data": {"p1": "043942089"}},
 {"id": "v11_isbn10_k", "cmp": "exact", "n": 1,
  "naked": "Same ISBN-10 rule. Payload 156512158 — check character "
           "(it may be X). Answer EXACTLY: <char>",
  "run": "/api/v1/id/checkdigit",
  "b_args": {"mode": "generate", "scheme": "isbn10", "value": "p2"},
  "data": {"p2": "156512158"}},
 {"id": "v11_isin", "cmp": "exact", "n": 1,
  "naked": "ISIN check digit (ISO 6166 / Luhn): letters become digits "
           "A=10..Z=35, append check so that the full numeric string "
           "passes Luhn. Payload XS123456789 → which check digit? "
           "Answer EXACTLY: <d>",
  "run": "/api/v1/id/checkdigit",
  "b_args": {"mode": "generate", "scheme": "isin", "value": "p3"},
  "data": {"p3": "XS123456789"}},
 {"id": "v11_dv_ean13", "cmp": "exact", "n": 1,
  "naked": "GS1 mod-10 ladder (3,1 from the right, complement to 10). "
           "Check digit of payload 590123412345? Answer EXACTLY: <d>",
  "run": "/api/v1/id/checkdigit",
  "b_args": {"mode": "generate", "scheme": "ean13", "value": "p4"},
  "data": {"p4": "590123412345"}},
 {"id": "v11_gtin14", "cmp": "exact", "n": 1,
  "naked": "Same GS1 ladder over 13-digit payload. Check digit of "
           "1234567890123? Answer EXACTLY: <d>",
  "run": "/api/v1/id/checkdigit",
  "b_args": {"mode": "generate", "scheme": "gtin14", "value": "p5"},
  "data": {"p5": "1234567890123"}},
 {"id": "v11_issn_x", "cmp": "exact", "n": 1,
  "naked": "ISSN: weights 8,7,6,5,4,3,2 over first 7 digits, check = "
           "(11 - sum mod 11) mod 11, X when 10. Payload 2499216. "
           "Answer EXACTLY: <char>",
  "run": "/api/v1/id/checkdigit",
  "b_args": {"mode": "generate", "scheme": "issn", "value": "p6"},
  "data": {"p6": "2499216"}},
 {"id": "v11_dv_lei", "cmp": "exact", "n": 1,
  "naked": "ISO 17442 LEI: ISO 7064 MOD 97-10 — letters A=10..Z=35 "
           "over the given payload, append '00', check = 98 - (num "
           "mod 97). Payload 529900MMAF64L11L2P. Answer EXACTLY: "
           "<2 digits>",
  "run": "/api/v1/id/checkdigit",
  "b_args": {"mode": "generate", "scheme": "lei", "value": "l1"},
  "data": {"l1": "529900MMAF64L11L2P"}},
 {"id": "v11_url_canon", "cmp": "exact", "n": 1,
  "naked": "Canonicalize: scheme+host lowercased, default port dropped, "
           "path case KEPT, utm_* removed, query sorted by key, "
           "fragment dropped: "
           "HTTP://API.Example.COM:80/V2/Users/?utm_medium=x&limit=10"
           "&offset=20&b=2&a=1#frag — Answer EXACTLY: <url>",
  "run": "/api/v1/text/url_canonical",
  "b_args": {"url": "u1", "sort_params": True, "drop_fragment": True},
  "data": {"u1": "HTTP://API.Example.COM:80/V2/Users/?utm_medium=x"
                 "&limit=10&offset=20&b=2&a=1#frag"}},
 {"id": "v11_canon_sha", "cmp": "exact", "n": 1,
  "naked": "Definition: canon(o) = JSON.stringify with object keys "
           "sorted lexicographically, NO whitespace, arrays order "
           "kept, numbers as given. Compute SHA-256 hex of the exact "
           "ASCII bytes of canon({\"b\":[3,{\"d\":1,\"c\":2}],\"a\":true"
           "}). Show only the 64-hex digest. Answer EXACTLY: <hex>",
  "run": "/api/v1/json/canonical",
  "b_args": {"input": "o1"},
  "data": {"o1": {"b": [3, {"d": 1, "c": 2}], "a": True}},
  "extract": "sha256"},
 {"id": "v11_recurring", "cmp": "exact", "n": 1,
  "naked": "Starting Thursday 2027-01-07, a meeting happens EVERY 3 "
           "WEEKS on Thursdays (ISO weeks, no holiday skips). Give the "
           "ISO date of the 5th occurrence (counting the first meeting "
           "itself as occurrence 1). Answer EXACTLY: <YYYY-MM-DD>",
  "run": "/api/v1/date/calc",
  "b_args": {"base": "2027-01-07", "op": "add",
             "params": {"duration": "12w"}},
  "data": {}},
]
