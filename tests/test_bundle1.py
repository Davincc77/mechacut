"""Bundle 1 — data repair & cleaning: behavior + determinism + hardening."""

import json

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _deterministic(url, payload):
    r1 = client.post(url, json=payload)
    r2 = client.post(url, json=payload)
    assert r1.status_code == r2.status_code, (r1.text, r2.text)
    assert r1.content == r2.content  # same request, same bytes
    return r1


# ---------------------------------------------------------------- repair

def test_repair_all_classes():
    broken = ('```json\n{ name: "René", \'age\': 44, tags: ["a", "b",], '
              '/* c */ ok: True, bad: None }\n```')
    r = _deterministic("/api/v1/json/repair", {"text": broken})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["output"] == {"name": "René", "age": 44, "tags": ["a", "b"],
                           "ok": True, "bad": None}
    for label in ("markdown_fence", "single_quotes", "comments", "bare_keys",
                  "trailing_commas", "python_literals"):
        assert label in b["repairs"], label


def test_repair_clean_and_jsonl():
    r = client.post("/api/v1/json/repair", json={"text": '{"a": 1}'})
    assert r.json()["repairs"] == []
    r = _deterministic("/api/v1/json/repair",
                       json := {"text": '{"a": 1}\n{"a": 2}'})
    assert r.json()["output"] == [{"a": 1}, {"a": 2}]
    assert r.json()["repairs"] == ["jsonl_wrapped"]


def test_repair_gives_up_cleanly():
    r = client.post("/api/v1/json/repair", json={"text": "hello {["})
    assert r.status_code == 400
    assert r.json()["error"] == "unrepairable"


# ------------------------------------------------------------------ diff

def test_diff_pointers():
    r = _deterministic("/api/v1/json/diff", {"a": {"x": 1, "y": {"z": [1, 2]},
                                                   "gone": True},
                                             "b": {"x": 2, "y": {"z": [1, 2, 3]},
                                                   "new": "n"}})
    ch = r.json()["changes"]
    pairs = [(c["op"], c["path"]) for c in ch]
    assert ("removed", "/gone") in pairs
    assert ("added", "/new") in pairs
    assert ("added", "/y/z/2") in pairs
    changed = next(c for c in ch if c["op"] == "changed")
    assert changed["path"] == "/x" and changed["before"] == 1
    paths = [c["path"] for c in ch]
    assert paths == sorted(paths)  # deterministic sort on the pointer


def test_diff_bool_int_not_equal():
    r = client.post("/api/v1/json/diff", json={"a": {"x": True}, "b": {"x": 1}})
    assert r.json()["count"] == 1


# ----------------------------------------------------------------- patch

def test_patch_success_path():
    r = _deterministic(
        "/api/v1/json/patch",
        {"document": {"a": {"b": [1, 2]}},
         "patch": [
             {"op": "add", "path": "/a/c", "value": "x"},
             {"op": "replace", "path": "/a/c", "value": "y"},
             {"op": "move", "from": "/a/c", "path": "/a/m"},
             {"op": "copy", "from": "/a/m", "path": "/a/m2"},
             {"op": "test", "path": "/a/m2", "value": "y"},
             {"op": "remove", "path": "/a/b/0"},
         ]})
    assert r.status_code == 200, r.text
    assert r.json()["output"] == {"a": {"b": [2], "m": "y", "m2": "y"}}
    assert r.json()["operations_applied"] == 6


def test_patch_failure_names_operation():
    r = client.post("/api/v1/json/patch",
                    json={"document": {"a": 1},
                          "patch": [{"op": "test", "path": "/a", "value": 2}]})
    assert r.status_code == 400
    b = r.json()
    assert b["error"] == "patch_failed"
    assert b["errors"][0]["field"] == "patch[0]"
    assert "expected" in b["errors"][0]


# ------------------------------------------------------------- canonical

def test_canonical():
    r = _deterministic("/api/v1/json/canonical",
                       {"input": {"b": 1, "a": {"d": [3, 2], "c": 1}}})
    assert r.json()["text"] == '{"a":{"c":1,"d":[3,2]},"b":1}'
    rp = client.post("/api/v1/json/canonical",
                     json={"input": {"b": 1}, "style": "pretty"})
    assert rp.json()["text"].startswith('{\n  "b": 1')


# ---------------------------------------------------------------- dedupe

def test_dedupe_modes():
    r = _deterministic("/api/v1/list/dedupe",
                       {"items": [" Foo ", "foo", "BAR", "bar"], "mode": "text"})
    assert r.json()["output"] == [" Foo ", "BAR"]
    assert r.json()["removed"] == 2
    r = client.post("/api/v1/list/dedupe", json={"mode": "url", "items": [
        "https://A.com/x/", "https://a.com/x", "http://B.com:80/",
        "https://a.com/x#frag"]})
    assert r.json()["output"] == ["https://A.com/x/", "http://B.com:80/"]
    r = client.post("/api/v1/list/dedupe",
                    json={"mode": "email", "items": ["A@B.com", "a@b.com", "x"]})
    assert r.json()["output"] == ["A@B.com", "x"]


# --------------------------------------------------------------- csv/fix

DIRTY = "\ufeffname;name;age\r\nBob;X;42\r\nAnn\r\n\r\n"


def test_csv_fix():
    r = _deterministic("/api/v1/csv/fix", {"csv": DIRTY})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["output"] == "name,name_2,age\nBob,X,42\nAnn,,\n"
    assert "delimiter_detected:;" in b["notes"]
    assert "bom_removed" in b["notes"]
    assert "duplicate_headers_renamed" in b["notes"]
    assert "short_rows_padded:1" in b["notes"]


def test_csv_fix_empty_is_400():
    r = client.post("/api/v1/csv/fix", json={"csv": "\n\n"})
    assert r.status_code == 400


# ------------------------------------------------------------- csv/types

def test_csv_types():
    csv = ("age,price,active,born,nick\n"
           "34,1.5,true,2020-02-29,\n"
           "7,10,false,2021-01-01,n/a")
    r = _deterministic("/api/v1/csv/types", {"csv": csv})
    b = r.json()
    assert b["output"][0] == {"age": 34, "price": 1.5, "active": True,
                              "born": "2020-02-29", "nick": None}
    types = {c["name"]: c["type"] for c in b["columns"]}
    assert types == {"age": "int", "price": "float", "active": "bool",
                     "born": "date", "nick": "null"}
    nick = next(c for c in b["columns"] if c["name"] == "nick")
    assert nick["nulls"] == 2


# -------------------------------------------------------------- csv/join

LEFT = [{"id": 1, "n": "a"}, {"id": 2, "n": "b"}]
RIGHT = [{"id": 1, "t": "x"}, {"id": 3, "t": "y"}]


def test_join_modes():
    r = _deterministic("/api/v1/csv/join",
                       {"left": LEFT, "right": RIGHT, "on": "id",
                        "how": "inner"})
    assert r.json()["output"] == [{"id": 1, "n": "a", "t": "x"}]
    r = client.post("/api/v1/csv/join", json={"left": LEFT, "right": RIGHT,
                                              "on": "id", "how": "left"})
    out = r.json()["output"]
    assert len(out) == 2 and out[1] == {"t": None, "id": 2, "n": "b"}
    r = client.post("/api/v1/csv/join", json={"left": LEFT, "right": RIGHT,
                                              "on": "id", "how": "outer"})
    out = r.json()["output"]
    assert len(out) == 3 and out[2] == {"n": None, "id": 3, "t": "y"}
    assert r.json()["counts"]["matched"] == 1


def test_join_missing_key_400():
    r = client.post("/api/v1/csv/join", json={"left": LEFT, "right": RIGHT,
                                              "on": "nope"})
    assert r.status_code == 400
    assert "column not found" in r.text


# ----------------------------------------------------------- table/pivot

ROWS = [{"month": "Jan", "region": "E", "units": "10"},
        {"month": "Jan", "region": "W", "units": "5"},
        {"month": "Feb", "region": "E", "units": "7"}]


def test_pivot():
    r = _deterministic("/api/v1/table/pivot",
                       {"data": ROWS, "index": "month", "columns": "region",
                        "values": "units", "agg": "sum"})
    assert r.json()["output"] == [{"month": "Jan", "E": 10, "W": 5},
                                  {"month": "Feb", "E": 7, "W": None}]
    r = client.post("/api/v1/table/pivot",
                    json={"data": ROWS, "index": ["month"], "columns": "region",
                          "values": "units", "agg": "mean"})
    assert r.json()["output"][1]["E"] == 7.0


def test_unpivot():
    r = client.post("/api/v1/table/pivot",
                    json={"data": [{"id": 1, "q1": 5, "q2": 6}],
                          "mode": "unpivot", "keep": ["id"]})
    assert r.json()["output"] == [
        {"id": 1, "variable": "q1", "value": 5},
        {"id": 1, "variable": "q2", "value": 6}]


def test_pivot_non_numeric_agg_400():
    r = client.post("/api/v1/table/pivot",
                    json={"data": [{"m": "a", "c": "x", "v": "text"}],
                          "index": "m", "columns": "c", "values": "v"})
    assert r.status_code == 400
    assert "numeric" in r.text


# ------------------------------------------------------- format/convert

def test_convert_round_trips():
    r = _deterministic("/api/v1/format/convert",
                       {"input": "a: 1\nb: [1, 2]\n", "from": "yaml",
                        "to": "json"})
    assert r.json()["output"] == '{"a":1,"b":[1,2]}'
    r = client.post("/api/v1/format/convert",
                    json={"input": '{"B": "2", "A": "x y"}', "from": "json",
                          "to": "env"})
    assert r.json()["output"] == "A='x y'\nB=2\n"
    r = client.post("/api/v1/format/convert",
                    json={"input": '[{"a":1,"b":2},{"a":3}]', "from": "json",
                          "to": "csv"})
    assert r.json()["output"] == "a,b\n1,2\n3,\n"
    r = client.post("/api/v1/format/convert",
                    json={"input": "a,b\n1,x\n", "from": "csv", "to": "json"})
    assert json.loads(r.json()["output"]) == [{"a": 1, "b": "x"}]
    r = client.post("/api/v1/format/convert",
                    json={"input": 'x = 1\n[s]\ny = "a"\n', "from": "toml",
                          "to": "json"})
    assert json.loads(r.json()["output"]) == {"s": {"y": "a"}, "x": 1}


def test_convert_structural_errors_400():
    r = client.post("/api/v1/format/convert",
                    json={"input": '"just a string"', "from": "json",
                          "to": "env"})
    assert r.status_code == 400
    assert r.json()["error"] == "convert_failed"
    r = client.post("/api/v1/format/convert",
                    json={"input": '{"a": {"nested": 1}}', "from": "json",
                          "to": "env"})
    assert r.status_code == 400
    r = client.post("/api/v1/format/convert",
                    json={"input": "{}", "from": "json", "to": "xml"})
    assert r.status_code == 400  # enum


# -------------------------------------------------------------- surfaces

def test_mcp_exposes_bundle1():
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert names == [ 'chart_from_data', 'reshape_json', 'validate_json',
                      'json_repair', 'json_diff', 'json_patch',
                      'json_canonical', 'csv_fix', 'csv_types', 'csv_join',
                      'table_pivot', 'list_dedupe', 'format_convert',
                      'text_patch', 'text_diff', 'text_apply_diff',
                      'path_normalize', 'glob_match', 'env_interpolate',
                      'date_parse', 'date_tz', 'date_calc', 'cron_next',
                      'cron_humanize', 'ics_generate', 'ics_parse',
                      'num_format', 'num_parse', 'num_round', 'units_convert',
                      'money_prorate', 'money_aging', 'money_split', 'number_spell',
                      'id_ulid', 'pkg_name', 'net_ip', 'net_cidr',
                      'file_encoding', 'schedule_overlap', 'cron_validate',
                      'integrity_verify', 'math_calc', 'money_discount',
                      'formula_catalog', 'intent_reflect', 'date_recurrence', 'units_shoe_size', 'net_sri', 'date_tz_ambiguity', 'money_flight_comp', 'date_week', 'money_baggage', 'csv_excel_damage', 'money_crossover', 'csv_excel_display', 'date_tz_anchor', 'money_points', 'table_sql_dump', 'table_scale', 'check_format',
                      'csv_money_columns', 'date_relative', 'text_url_canonical', 'xml_to_json',
                      'web_cert', 'id_checkdigit', 'image_rightsize',
                      'money_rates', 'doc_text', 'money_amortize',
                      'money_interest', 'ics_validate', 'schedule_holidays',
                      'web_cache', 'gzip_roundtrip', 'qr_generate',
                      'table_peek', 'csv_diff', 'ssh_fingerprint',
                      'zip_verify', 'crypto_address', 'validate_taxid', 'caip',
                      'secret_scan', 'text_redact', 'validate_country',
                      'validate_postal', 'geo_distance', 'geo_geohash',
                      'file_identify', 'text_punycode', 'semver_parse',
                      'semver_sort', 'text_sanitize', 'json_map', 'num_fx',
                      'hash_hmac', 'hash_digest', 'enc_base64', 'jwt_decode',
                      'id_uuid', 'id_slug', 'fingerprint', 'validate_iban',
                      'validate_phone', 'validate_email', 'validate_url',
                      'color_check', 'text_count', 'sort_natural', 'text_case',
                      'text_truncate', 'regex_test', 'text_chunk', 'md_render',
                      'html_text', 'color_palette', 'eth_abi_encode',
                      'eth_abi_decode', 'eth_eip712', 'eth_receipt',
                      'eth_address', 'eth_selector', 'eth_units',
                      'text_decode', 'num_human', 'text_escape',
                      'text_normalize', 'batch', 'logic_rules', 'sort_multi',
                      'json_query', 'check_redlines', 'check_target', 'check_agreement',
                      'intent_card', 'intent_check', 'extract_facts',
                      'text_select', 'check_constraints', 'check_refs',
                      'ship_dimweight', 'json_coerce',
                      'money_bogo',
                      'money_unitprice',
                      'agent_modelid',
                      'food_poultry', 'food_leftovers',
                      'food_ovenschedule', 'ledger_apply_payments',
                          'ledger_summary', 'eval_compare',
                          'shop_shipping_deadline',
                          'shop_return_deadline',
                          'shop_pricedrop_refund',
                          'shop_legal_guarantee',
                          'money_keep_records_uk',
                          'invoice_validate_totals', 'check_allowlist',
                          'loop_doom_check', 'agent_retrybudget',
                          'agent_mcpaudit', 'agent_mcpsurface', 'agent_contexttax', 'agent_costdiff', 'agent_tooltrim', 'agent_tooloverlap', 'agent_mcplist', 'shop_discount_audit', 'net_ratelimit', 'number_words_pair', 'date_window', 'date_deemed', 'agent_propose', 'text_fold_report', 'text_novel_words', 'address_parse', 'date_civil', 'proposals_registry',                              'shop_gift_voucher', 'shop_soldes_window',
                              'shop_soldes_be', 'shop_soldes_lu',
                              'shop_withdrawal', 'invoice_payment_due']  # b112 payment-due en queue ; b110 soldes-lu en queue des dates ; b107 withdrawal en queue (ordre MCP_TOOLS = fin de liste) ; b105 soldes-be en queue ; b104 cost-diff aprés context-tax dans MCP_TOOLS ; b103 soldes-window en queue ; b102 gift-voucher ; queue 23-11 bundles 82-84, 92 ; bundle97 mcpsurface ; bundle99 legal_guarantee ; bundle101 context-tax (ordre MCP_TOOLS = aprés pricedrop)
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2,
                                  "method": "tools/call",
                                  "params": {"name": "json_repair",
                                             "arguments":
                                                 {"text": "{a: 1,}"}}})
    text = r.json()["result"]["content"][0]["text"]
    assert json.loads(text)["output"] == {"a": 1}


def test_index_and_openapi_list_routes():
    body = client.get("/").json()
    for route in ("/api/v1/json/repair", "/api/v1/csv/join",
                  "/api/v1/format/convert", "/api/v1/table/pivot"):
        assert route in body["endpoints"]
    spec = client.get("/openapi.json").json()
    for route in ("/api/v1/json/diff", "/api/v1/list/dedupe",
                  "/api/v1/csv/types"):
        assert route in spec["paths"]


# ------------------------------------------------------------- hardening

def test_scanner_probes_get_neutral_404():
    for probe in ("/.env", "/.git/config", "/wp-login.php", "/phpmyadmin/"):
        r = client.get(probe)
        assert r.status_code == 404, probe
        assert r.json() == {"error": "not_found"}


def test_docs_disabled():
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404


def test_method_not_allowed_is_neutral():
    r = client.get("/api/v1/validate")
    assert r.status_code == 405
    assert r.json() == {"error": "method_not_allowed"}


def test_oversized_body_413():
    r = client.post("/api/v1/json/repair", json={"text": "x" * 6_000_000})
    assert r.status_code == 413
    assert r.json()["error"] == "payload_too_large"


def test_security_headers_on_api_json():
    r = client.post("/api/v1/validate", json={"payload": {}, "schema": {}})
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["referrer-policy"] == "no-referrer"
    assert r.headers["cache-control"] == "no-store"
