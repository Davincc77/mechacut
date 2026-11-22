# bench v10 — « pas seulement bien : JUSTE » (gelé 2026-11-22, suite
# v0.72.0, harness v10)
#
# Thèse mesurée : sur des réponses EXACTES (chiffres de contrôle,
# hashages, dates frontière, conventions prouvées), des modèles gratuits
# « un peu plus puissants » (qwen2.5:7b-q4, llama3.1:8b) échouent NU de
# façon SYSTÉMATIQUE à temp 0, et réussissent 100% avec le relais
# mechacut — le serveur renvoie la réponse juste. C'est une question de
# JUSTESSE, pas de style.
#
# Discipline (references/llm-ab-bench.md) : les golds viennent de
# golden10.py (oracles main : GS1 mod-10, ISO 7064 MOD 97-10, ISO 13616,
# hashlib, base64, calendrier/zoneinfo stdlib) — JAMAIS du produit.
# L'arm B voit la tâche sans les données (références $name), choisit une
# route de la SHORTLIST GELÉE, le harness BIND PAR NOM et relit la
# réponse serveur via EXTRACTORS. answer_from_server=True pour B.
# Comparateurs : exact / set (liste virgule triée) / json (parse->canon).

SHORTLIST = [
    {"path": "/api/v1/id/checkdigit",
     "args_hint": 'mode "generate"|"repair", scheme, value',
     "one_liner": "check digits EAN/ISBN/GTIN/LEI… + repair one-mutation"},
    {"path": "/api/v1/money/discount",
     "args_hint": "price, steps[], qty, currency",
     "one_liner": "chained discounts exact Decimal; order impact"},
    {"path": "/api/v1/hash/digest",
     "args_hint": "data, algo",
     "one_liner": "sha256/sha512/sha384/md5 over text: hex + base64"},
    {"path": "/api/v1/date/calc",
     "args_hint": "base, op, params, tz",
     "one_liner": "business days, boundaries, DST-aware arithmetic"},
    {"path": "/api/v1/date/relative",
     "args_hint": "phrase, now, tz",
     "one_liner": "relative phrases (EN/FR/PT) to exact ISO, now arg"},
    {"path": "/api/v1/text/url_canonical",
     "args_hint": "url, sort_params, drop_fragment, strip_tracking",
     "one_liner": "canonical URL per published RFC 3986 rules"},
    {"path": "/api/v1/web/cert",
     "args_hint": "pem, as_of",
     "one_liner": "X.509 PEM fields + status at as_of"},
    {"path": "/api/v1/csv/money_columns",
     "args_hint": "csv",
     "one_liner": "money columns: convention PROVEN by the column"},
    {"path": "/api/v1/xml/to_json",
     "args_hint": "xml, force_array[] (rooted paths, e.g. catalog/book)",
     "one_liner": "XML to JSON with the applied rules listed"},
]

TASKS = [
 {"id": "dv_ean13", "cmp": "exact",
  "naked": "GS1 EAN-13 check digit: weights 3,1 alternating starting "
           "at the RIGHT of the payload, DV = (10 - sum mod 10) mod 10. "
           "Compute the check digit of payload 400638133393. Answer "
           "with EXACTLY one line: <digit>",
  "run": "/api/v1/id/checkdigit",
  "b_args": {"mode": "generate", "scheme": "ean13", "value": "dv1"},
  "data": {"dv1": "400638133393"}, "extract": "dv"},
 {"id": "dv_gtin14", "cmp": "exact",
  "naked": "GTIN-14 uses the same GS1 mod-10 ladder (weights 3,1 from "
           "the right over the 13-digit payload). Check digit of "
           "payload 0978030640615? Answer EXACTLY one line: <digit>",
  "run": "/api/v1/id/checkdigit",
  "b_args": {"mode": "generate", "scheme": "gtin14", "value": "dv2"},
  "data": {"dv2": "0978030640615"}, "extract": "dv"},
 {"id": "dv_isbn13", "cmp": "exact",
  "naked": "ISBN-13 = EAN-13 weights on the 978-prefixed payload. "
           "Check digit of payload 978030640615? Answer EXACTLY one "
           "line: <digit>",
  "run": "/api/v1/id/checkdigit",
  "b_args": {"mode": "generate", "scheme": "isbn13", "value": "dv3"},
  "data": {"dv3": "978030640615"}, "extract": "dv"},
 {"id": "repair_isbn", "cmp": "set",
  "naked": "ISBN 9780306406158 fails its check digit; assume exactly "
           "ONE digit (any position, may be inside the 978 prefix, "
           "must stay 978/979-prefixed 13 digits) was mutated. List "
           "EVERY single-digit fix as pos:replaced_digit, comma-"
           "separated, positions 0-based, sorted. Answer EXACTLY one "
           "line.",
  "run": "/api/v1/id/checkdigit",
  "b_args": {"mode": "repair", "scheme": "isbn13", "value": "rv1"},
  "data": {"rv1": "9780306406158"}, "extract": "repair_set"},
 {"id": "lei_check", "cmp": "exact",
  "naked": "ISO 17442 LEI check digits use ISO 7064 MOD 97-10: map "
           "letters A=10..Z=35 over the 18-char payload, append '00', "
           "check = (98 - number mod 97) mod 97, written on two "
           "digits. Compute the two check digits for LEI payload "
           "529900T8BM49AURSDO. Answer EXACTLY one line: <2 digits>",
  "run": "/api/v1/id/checkdigit",
  "b_args": {"mode": "generate", "scheme": "lei", "value": "lv1"},
  "data": {"lv1": "529900T8BM49AURSDO"}, "extract": "dv"},
 {"id": "sha256_a", "cmp": "exact",
  "naked": "SHA-256 hex digest of the exact UTF-8 bytes of "
           "mechacut:v10:9780306406157 (no quotes, no newline). "
           "Answer EXACTLY one line: <64 hex lowercase>",
  "run": "/api/v1/hash/digest",
  "b_args": {"data": "h1", "algo": "sha256"},
  "data": {"h1": "mechacut:v10:9780306406157"}, "extract": "hex"},
 {"id": "sha256_b", "cmp": "exact",
  "naked": "SHA-256 hex of the exact UTF-8 bytes of the string "
           "v10-Δ-€-日本 (no newline). Answer EXACTLY one line: "
           "<64 hex lowercase>",
  "run": "/api/v1/hash/digest",
  "b_args": {"data": "h2", "algo": "sha256"},
  "data": {"h2": "v10-Δ-€-日本"}, "extract": "hex"},
 {"id": "b64_sha512", "cmp": "exact",
  "naked": "Standard base64 (padded, one line) of the RAW SHA-512 "
           "digest of the bytes of mechacut-v10. Answer EXACTLY one "
           "line: <base64>",
  "run": "/api/v1/hash/digest",
  "b_args": {"data": "h3", "algo": "sha512"},
  "data": {"h3": "mechacut-v10"}, "extract": "b64"},
 {"id": "disc_double", "cmp": "exact",
  "naked": "Item 89.90 EUR, two successive discounts: -30% then -20%. "
           "Final price (2 dp, half-up) and the REAL total discount "
           "percent (2 dp). Answer EXACTLY one line: <price>|<pct>",
  "run": "/api/v1/money/discount",
  "b_args": {"price": "p1", "currency": "EUR", "steps": [
      {"type": "percent", "value": "30"},
      {"type": "percent", "value": "20"}]},
  "data": {"p1": "89.90"}, "extract": "two:final_total|effective_pct"},
 {"id": "disc_order", "cmp": "exact",
  "naked": "Basket 83.40 EUR, steps in THIS order: -30% then a fixed "
           "-5 EUR. Fixed steps make the ORDER matter. Give the final "
           "price for the stated order (2 dp) and the spread in EUR "
           "between the best and worst ordering (2 dp). Answer "
           "EXACTLY: <final>|<spread>",
  "run": "/api/v1/money/discount",
  "b_args": {"price": "p2", "currency": "EUR", "steps": [
      {"type": "percent", "value": "30"},
      {"type": "fixed", "value": "5"}]},
  "data": {"p2": "83.40"}, "extract": "two:final_total|order_spread"},
 {"id": "disc_b2p1", "cmp": "exact",
  "naked": "3 identical items at 19.99 each, promo buy-2-pay-1 (pay "
           "ceil(qty/2)). Total paid and effective discount percent "
           "(2 dp each). Answer EXACTLY: <total>|<pct>",
  "run": "/api/v1/money/discount",
  "b_args": {"price": "p3", "qty": 3,
             "steps": [{"type": "buy2pay1"}]},
  "data": {"p3": "19.99"}, "extract": "two:final_total|effective_pct"},
 {"id": "biz_shift", "cmp": "exact",
  "naked": "Add exactly 10 BUSINESS days (Mon-Fri, weekends skipped, "
           "the base day not counted) to Monday 2026-11-23. Which ISO "
           "date do you land on? Answer EXACTLY one line: "
           "<YYYY-MM-DD>",
  "run": "/api/v1/date/calc",
  "b_args": {"base": "2026-11-23", "op": "business_days",
             "params": {"n": 10}},
  "data": {}, "extract": "date_result"},
 {"id": "feb_end", "cmp": "exact",
  "naked": "Last calendar day of February 2027 as ISO date. Answer "
           "EXACTLY one line: <YYYY-MM-DD>",
  "run": "/api/v1/date/calc",
  "b_args": {"base": "2027-02-01", "op": "boundary",
             "params": {"unit": "month", "edge": "end"}},
  "data": {}, "extract": "date_result"},
 {"id": "next_monday_sunday", "cmp": "exact",
  "naked": "Today is Sunday 2026-11-22 (ISO week 47 ends today). Give "
           "the ISO date of the day phrase 'next monday' resolves to "
           "under the convention: 'next X' = the first X strictly "
           "after today. Answer EXACTLY one line: <YYYY-MM-DD>",
  "run": "/api/v1/date/relative",
  "b_args": {"phrase": "next monday", "now": "2026-11-22"},
  "data": {}, "extract": "date_result"},
 {"id": "dst_gap", "cmp": "exact",
  "naked": "Europe/Luxembourg springs forward Sun 2027-03-28 at "
           "02:00 CET -> 03:00 CEST (02:30 does not exist). Add "
           "exactly 2 hours to local 2027-03-28 01:30: what LOCAL "
           "wall-clock time do you read? Answer EXACTLY: <HH:MM>",
  "run": "/api/v1/date/calc",
  "b_args": {"base": "2027-03-28T01:30", "op": "add",
             "params": {"duration": "T2h"}, "tz": "Europe/Luxembourg"},
  "data": {}, "extract": "hm_result"},
 {"id": "url_canon", "cmp": "exact",
  "naked": "Canonicalize this URL: scheme+host lowercased, path case "
           "KEPT, tracking utm_* params removed, remaining query "
           "params sorted by (key,value), fragment removed: "
           "HTTPS://Shop.Example.COM/Deals/?b=2&a=1&utm_source=x&b=1"
           "#top — Answer EXACTLY one line: <url>",
  "run": "/api/v1/text/url_canonical",
  "b_args": {"url": "u1", "sort_params": True, "drop_fragment": True},
  "data": {"u1": "HTTPS://Shop.Example.COM/Deals/?b=2&a=1"
                 "&utm_source=x&b=1#top"}, "extract": "canonical"},
 {"id": "csv_eu_meaning", "cmp": "exact",
  "naked": "Column 'montant' holds these values, one per line: "
           "1.234,56 then 2,50 then 1.234. A column PROVES its own "
           "decimal convention through its unambiguous cells. Which "
           "NUMBER does the lone 1.234 stand for, in that column? "
           "Answer EXACTLY one line: <integer-or-decimal>",
  "run": "/api/v1/csv/money_columns",
  "b_args": {"csv": "c1"},
  "data": {"c1": "montant\n1.234,56\n2,50\n1.234"},
  "extract": "resolved0"},
 {"id": "xml_force", "cmp": "json",
  "naked": "Convert <a><b><c x=\"1\"/></b></a> to JSON with rules: "
           "attributes become keys prefixed @, and path b/c is FORCED "
           "to an array. Give the MINIFIED JSON object. Answer "
           "EXACTLY one line.",
  "run": "/api/v1/xml/to_json",
  "b_args": {"xml": "x1", "force_array": ["a/b/c"]},
  "data": {"x1": '<a><b><c x="1"/></b></a>'}, "extract": "json_min"},
]
