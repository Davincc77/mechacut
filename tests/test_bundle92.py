# -*- coding: utf-8 -*-
"""Bundle 92 — /agent/mcp-audit : le listing MCP jugé avant le client.

Golds tracés MAIN avant l'impl (les wire-shapes publiés rejoués
verbatim) :
  inputSchema {}                      -> EMPTY_INPUT_SCHEMA critical
                                          (gitlab-mcp #286 : TOUS les
                                          clients rejettent)
  allOf à la racine                   -> ROOT_NOT_OBJECT critical
                                          (langfuse #13804 : Claude
                                          Code droppe en silence)
  "items":[{...},{...}] (et même [])  -> TUPLE_ITEMS critical
                                          (strapi #27395, TS SDK #2084)
  deux fois le même nom               -> DUP_NAME
  « сep » avec с cyrillique           -> NAME_UNSAFE + U+0441 nommé
  required:["zz"] hors properties     -> REQUIRED_UNKNOWN
  protocolVersion "2026-12-31"        -> PROTO_UNKNOWN (révisions
                                          connues citées dans le détail)
  cle d'enveloppe 2026-07-28          -> PAS de finding protocole
  nom avec point "get.user"           -> NAME_DOT warning (le pattern
                                          fournisseur ^[a-zA-Z0-9_-]+$)
  nom avec slash seul                 -> SLASH_NAME info — le conflit
                                          SEP-986 vs spec est RENDU
  description == le nom               -> DESCRIPTION_ECHO
  0 desc sur toutes les propriétés    -> PARAMS_ALL_UNDESCRIBED
  initialize sans serverInfo.name     -> NO_SERVER_NAME
  initialize sans version             -> PROTO_MISSING
  pas d'initialize du tout            -> NO_INITIALIZE (info)
  tools: []                           -> EMPTY_TOOLS info
  get_user + getUser                  -> MIXED_NAMING info
  $schema draft-07 (sans tuples)      -> DIALECT_DRAFT07 warning
  enum de 51                          -> BIG_ENUM (bord nommé 50)
  properties 5 niveaux                -> DEEP_SCHEMA (bord nommé 4)
  chaine additionalProperties 1000    -> PAS de RecursionError (le
                                          hostile est borné, pas planté)
  5100 propriétés                       -> WALK_TRUNCATED — une sonde
                                          tronquée EST un résultat nommé
  257 tools / tools non-liste / init non-dict -> refus NOMMÉS
Échelle close : REJECTED > NEEDS_REVIEW > INFORMATIONAL > CLEAN.

Le serment de frontière est testé : le module n'ouvre NI socket NI
subprocess — test par bouchonnade (socket.socket et subprocess
leveraient si le module les appelait).
"""
import socket
import subprocess

import mcpauditkit as m
import main
import pytest
from fastapi.testclient import TestClient

client = TestClient(main.app)


def _clean_tool(name="get_user", desc="fetch one user record by its id"):
    return {"name": name, "description": desc,
            "inputSchema": {"type": "object",
                            "properties": {"id": {"type": "string",
                                                  "description": "id"}}}}


_INIT = {"protocolVersion": "2025-06-18",
         "serverInfo": {"name": "demo", "version": "1"}}


def _rules(r):
    return sorted(f["rule"] for f in r["findings"])


def test_empty_input_schema_is_critical():
    r = m.agent_mcp_audit([{"name": "x_tool",
                            "description": "does a thing worth naming",
                            "inputSchema": {}}], _INIT)
    assert r["verdict"] == "REJECTED"
    assert "EMPTY_INPUT_SCHEMA" in _rules(r)
    ev = [f for f in r["findings"] if f["rule"] == "EMPTY_INPUT_SCHEMA"][0]
    assert "gitlab-mcp" in ev["evidence"]


def test_root_composition_dropped_silently():
    r = m.agent_mcp_audit([{"name": "y_tool",
                            "description": "clean desc here",
                            "inputSchema": {"allOf": [{"type": "object"}]}}],
                          _INIT)
    assert r["verdict"] == "REJECTED"
    assert "ROOT_NOT_OBJECT" in _rules(r)


def test_tuple_items_fire_even_empty():
    for items in ([{"type": "string"}, {"type": "number"}], []):
        r = m.agent_mcp_audit([{"name": "z_tool",
                                "description": "ok description",
                                "inputSchema": {"type": "object", "properties":
                                                {"a": {"type": "array",
                                                       "description": "list",
                                                       "items": items}}}}], _INIT)
        assert "TUPLE_ITEMS" in _rules(r), items


def test_dup_and_name_classes():
    t = _clean_tool("a_one")
    r = m.agent_mcp_audit([t, _clean_tool("a_one")], _INIT)
    assert "DUP_NAME" in _rules(r)
    r = m.agent_mcp_audit([_clean_tool(u"\u0441ep")], _INIT)
    assert "NAME_UNSAFE" in _rules(r)
    ev = [f for f in r["findings"] if f["rule"] == "NAME_UNSAFE"][0]
    assert "U+0441" in ev["detail"]  # le cyrillique est NOMMÉ, pas deviné
    r = m.agent_mcp_audit([_clean_tool("get.user")], _INIT)
    assert "NAME_DOT" in _rules(r)
    r = m.agent_mcp_audit([_clean_tool("user-profile/update")], _INIT)
    assert "SLASH_NAME" in _rules(r)
    assert r["verdict"] != "REJECTED"  # le conflit est rendu, pas puni
    r = m.agent_mcp_audit([{"description": "no name at all here",
                            "inputSchema": {"type": "object",
                                            "properties": {}}}], _INIT)
    assert "NAME_UNSAFE" in _rules(r)
    assert any(f["tool"] == "tools[0]" for f in r["findings"]
               if f["rule"] == "NAME_UNSAFE")  # l'index est un nom


def test_required_contradicts_itself():
    r = m.agent_mcp_audit([{"name": "a_b", "description": "alpha beta tool",
                             "inputSchema": {"type": "object",
                                             "properties": {"q": {"type": "string",
                                                                   "description": "qq"}},
                                             "required": ["q", "zz"]}}], _INIT)
    assert "REQUIRED_UNKNOWN" in _rules(r)
    assert [f for f in r["findings"] if f["rule"] == "REQUIRED_UNKNOWN"
            ][0]["detail"].count("'zz'") == 1


def test_protocol_revisions_are_a_closed_known_set():
    r = m.agent_mcp_audit([_clean_tool()], {
        "protocolVersion": "2026-12-31", "serverInfo": {"name": "n", "version": "1"}})
    assert "PROTO_UNKNOWN" in _rules(r)
    r = m.agent_mcp_audit([_clean_tool()], {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "serverInfo": {"name": "n", "version": "1"}})
    assert "PROTO_UNKNOWN" not in _rules(r)  # l'enveloppe moderne est lue
    r = m.agent_mcp_audit([_clean_tool()], {"serverInfo": {"name": "n"}})
    assert "PROTO_MISSING" in _rules(r)
    r = m.agent_mcp_audit([_clean_tool()], {"protocolVersion": "2025-06-18"})
    assert "NO_SERVER_NAME" in _rules(r)


def test_description_family():
    r = m.agent_mcp_audit([{"name": "a_b",
                            "inputSchema": {"type": "object",
                                            "properties": {}}}], _INIT)
    assert "NO_DESCRIPTION" in _rules(r)
    r = m.agent_mcp_audit([_clean_tool("get_user", "get user")], _INIT)
    assert "DESCRIPTION_ECHO" in _rules(r)
    r = m.agent_mcp_audit([{"name": "a_b", "description": "ok enough text",
                            "inputSchema": {"type": "object",
                                            "properties": {"p": {"type": "string"}}}}],
                          _INIT)
    assert "PARAMS_ALL_UNDESCRIBED" in _rules(r)


def test_list_and_naming_edges():
    r = m.agent_mcp_audit([], _INIT)
    assert r["verdict"] == "INFORMATIONAL"
    assert "EMPTY_TOOLS" in _rules(r)
    r = m.agent_mcp_audit([_clean_tool("get_user"), _clean_tool("getUser")], _INIT)
    assert "MIXED_NAMING" in _rules(r)
    r = m.agent_mcp_audit([{"name": "a_b", "description": "alpha beta tool",
                            "inputSchema": {"$schema":
                                            "http://json-schema.org/draft-07/schema#",
                                            "type": "object",
                                            "properties": {"p": {"type": "string",
                                                                  "description": "d"}}}}],
                          _INIT)
    assert "DIALECT_DRAFT07" in _rules(r)


def test_numbered_bands_fire_and_are_named():
    r = m.agent_mcp_audit([{"name": "a_b", "description": "alpha beta tool",
                            "inputSchema": {"type": "object",
                                            "properties": {"p": {"type": "string",
                                                                  "description": "d",
                                                                  "enum": list(range(51))}}}}],
                          _INIT)
    assert "BIG_ENUM" in _rules(r)
    node = {"type": "string", "description": "leaf"}
    for lvl in range(4, 0, -1):
        node = {"type": "object", "description": "lvl%d" % lvl,
                "properties": {"k%d" % lvl: node}}
    r = m.agent_mcp_audit([{"name": "a_b", "description": "alpha beta tool",
                            "inputSchema": {"type": "object",
                                            "properties": {"top": node}}}])
    assert "DEEP_SCHEMA" in _rules(r)


def test_hostile_input_is_bounded_not_fatal():
    deep: dict = {"type": "object"}
    cur = deep
    for _ in range(1000):
        nxt: dict = {"type": "object"}
        cur["additionalProperties"] = nxt
        cur = nxt
    r = m.agent_mcp_audit([{"name": "a_b", "description": "alpha beta tool",
                            "inputSchema": deep}])  # pas de RecursionError
    assert r["verdict"] == "INFORMATIONAL"
    props = {"p%d" % i: {"type": "string"} for i in range(5100)}
    r = m.agent_mcp_audit([{"name": "a_b", "description": "alpha beta tool",
                            "inputSchema": {"type": "object",
                                            "properties": props}}])
    assert "WALK_TRUNCATED" in _rules(r)  # sonde tronquée = résultat NOMMÉ
    caps = r["caps"]
    assert caps["walk_nodes"] == m.WALK_BUDGET_NODES == 5000


def test_caps_refused_by_name():
    with pytest.raises(m.McpAuditError) as e:
        m.agent_mcp_audit([_clean_tool()] * (m.MAX_TOOLS + 1))
    assert e.value.field == "tools"
    with pytest.raises(m.McpAuditError):
        m.agent_mcp_audit("not a list")
    with pytest.raises(m.McpAuditError) as e:
        m.agent_mcp_audit([_clean_tool()], initialize="x")
    assert e.value.field == "initialize"


def test_scale_is_closed():
    assert m.agent_mcp_audit([_clean_tool()], _INIT)["verdict"] == "CLEAN"
    r = m.agent_mcp_audit([{"name": "a_b", "description": "alpha beta tool",
                            "inputSchema": {"type": "object",
                                            "properties": {"p": {"type": "string"}}}}],
                          _INIT)
    assert r["verdict"] == "NEEDS_REVIEW"
    assert r["counts"] == {"critical": 0, "warning": 1, "info": 0}


def test_boundary_no_fetch_no_subprocess(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("l'audit a ouvert le monde au lieu du listing")
    monkeypatch.setattr(socket, "socket", boom)
    monkeypatch.setattr(subprocess, "Popen", boom)
    r = m.agent_mcp_audit([_clean_tool()], _INIT)
    assert r["verdict"] == "CLEAN"
    assert "runtime never" in r["boundary"]


def test_we_pass_our_own_criticals():
    """Le juge juge sa maison : notre propre MCP_TOOLS passé dans NOTRE
    table ne rend AUCUN critical. Les warnings (params sans description,
    naming mixte) sont consignés à la file — honnête, pas puni."""
    r = m.agent_mcp_audit([t for t in main.MCP_TOOLS if isinstance(t, dict)],
                          {"protocolVersion": "2025-06-18",
                           "serverInfo": {"name": "mechacut.studio",
                                          "version": main.app.version}})
    assert r["counts"]["critical"] == 0, [(f["tool"], f["rule"])
                                          for f in r["findings"]
                                          if f["severity"] == "critical"]


def test_endpoint_shape_and_errors():
    r = client.post("/api/v1/agent/mcp-audit",
                    json={"tools": [_clean_tool()], "initialize": _INIT})
    assert r.status_code == 200
    j = r.json()
    assert j["verdict"] == "CLEAN" and j["sha256"]
    assert "runtime never" in j["boundary"]
    r = client.post("/api/v1/agent/mcp-audit",
                    json={"tools": [{"name": "x", "description":
                                     "does a thing worth naming",
                                     "inputSchema": {}}]})
    assert r.status_code == 200 and r.json()["verdict"] == "REJECTED"
    r = client.post("/api/v1/agent/mcp-audit", json={})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "body.tools"
    r = client.post("/api/v1/agent/mcp-audit", json={"tools": "nope"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "body.tools"
    r = client.post("/api/v1/agent/mcp-audit",
                    json={"tools": [_clean_tool("a_b", "alpha beta tool"),
                                    _clean_tool("c_d", "gamma delta tool")],
                          "initialize": {"protocolVersion": "2026-12-31",
                                         "serverInfo": {"name": "n",
                                                        "version": "1"}},
                          "x": 1})
    assert r.status_code == 400  # extra forbidden : le contrat est clos


def test_route_and_surfaces():
    """Le routeur doit AIGUILLER la douleur dans les trois langues —
    sans LM, table close, floor 4 : une phrase morte en PT reste un
    refus vide honnête, pas un bruit."""
    for q in ("my mcp server lists tools the client never loads",
              "le client ne charge que 3 outils sur 12 mcp",
              "a lista de ferramentas mcp nao aparece no cliente"):
        j = client.get("/route", params={"q": q}).json()
        tops = [x["tool"] for x in j["tools"]]
        assert "agent_mcpaudit" in tops[:3], q
        assert tops[0] == "agent_mcpaudit", q
    man = client.get("/agent/manifest").text
    assert "/api/v1/agent/mcp-audit" in man
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "tools/list"})
    names = [t["name"] for t in r.json()["result"]["tools"]]
    assert "agent_mcpaudit" in names and len(names) == 185  # +agent_tooloverlap bundle111 ; +shop_soldes_lu bundle110 ; +shop_withdrawal bundle107 ; +agent_tooltrim bundle106 ; +shop_soldes_be bundle105 ; +agent_costdiff bundle104 ; 178 avec shop_soldes_window bundle103 ; 177 avec shop_gift_voucher bundle102 (le compteur avait DÉRIVÉ ici, pêché par le pytest complet du cycle 103) ; 176 avec agent_contexttax bundle101 ; 175 avec money_keep_records_uk bundle100
    # 171→172 : bundle96 (+shop_pricedrop_refund)
