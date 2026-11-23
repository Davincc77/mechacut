"""mcpauditkit — /agent/mcp-audit : le listing MCP qu'un client rejette
en silence, jugé SANS lancer le serveur.

Douleur publiée, adoubée trois jours avant ce bundle : Claude Code
2.1.330 (20-nov-2026) corrige en dur « turns failing with "JSON schema
is invalid" … when many MCP tools carry an input schema the API
refuses ». La table des shapes mortels est PUBLIÉE par mcp-schema-audit
(PyPI, 17-oct-2026), incident par incident :

- inputSchema absent ou {}  → TOUS les clients rejettent la fiche
  (gitlab-mcp #286) ; et un modèle face à un schema muet
  RE-CONSTRUIT les arguments un appel raté à la fois (prime-agent #1073).
- root sans type:"object", ou allOf/oneOf au RACINE → Claude Code
  DROPPE l'outil en silence (langfuse #13804).
- "items" en forme TUPLE (liste) — grammaire draft-07 → les clients
  stricts 2020-12 rejettent TOUT (strapi #27395 ; TS SDK #2084, P1
  ouvert trois mois).
- protocolVersion négocié hors des révisions connues, préversion codée
  en dur, echo moderne sur handshake legacy (mcpkit #12, go-sdk #1033,
  ferrum-edge #2168 ; initialize qui pend : stripe #290).

La classe NOUS a mordus ×3 cette semaine (bundle87 : guillemets
quadruplés dans 2 descriptions MCP ; bundle89 : un « cep » avec a
CYRILLIQUE dans les tags ; bundle85 : le tag « 429 » nu) — le garde
interne devient produit.

Grammaire des NOMS, l'état du droit publié (typescript-sdk #1512,
conformance #238) : la spec posée (2025-11-25 et draft) dit 1-128
caractères, [A-Za-z0-9_.-], JAMAIS le slash ; le SEP-986 (marqué
Final) dit 1-64 et AUTORISE le slash ; et les fournisseurs en
pattern OpenAI-compatible rejettent `^[a-zA-Z0-9_-]+$` — le POINT est
refusé en aval. Le conflit est RENDU, pas tranché en silence : c'est
la loi de la maison (comme le désaccord eu-vs-de chez discount-audit).

Révisions de protocole connues, vérifiées sur les releases du dépôt
modelcontextprotocol (état 2026-09, courant 2026-07-28, sans sessions) :
2024-10-07, 2024-11-05, 2025-03-26, 2025-06-18, 2025-11-25, 2026-07-28.

Frontière SECURITE, jurée : statique sur le LISTING collé — zéro
fetch, zéro subprocess. Les auditeurs externes LANCENT le serveur
(mcp-server-audit, CloudCorpRecords/mcpaudit) ou branchent un
observateur runtime (mcp-behave, interposition dynamique). Nous
certifions la FORME, jamais le RUNTIME — même serment que modelid
(« OK certifie la forme, jamais le GET »).

Lois fermées :
- SEUILS NOMMÉS : length utile description >= 10 ; longueur de nom
  1-128 (spec posée), 64 = bord Anthropic Directory ; propriétés
  enum > 50 = BIG_ENUM ; profondeur de schema > 4 = DEEP_SCHEMA ;
  outillage : budget de marche 5000 noeuds — épuisé, le finding
  WALK_TRUNCATED le DIT (une sonde tronquée est un résultat NOMMÉ,
  jamais un silence).
- verdicts d'échelle close : REJECTED (>=1 CRITICAL) > NEEDS_REVIEW
  (>=1 WARNING) > INFORMATIONAL (>=1 INFO) > CLEAN.
- ordre des findings : ordre de marche (tools dans l'ordre donné,
  règles dans l'ordre de la table, cross-tool ensuite, protocole
  en dernier) — première vue, comme chez text_fold_report.
- un nom absent ou non-string N'EST PAS un trou silencieux : le
  finding porte "tools[<index>]" — l'index est un nom qu'on ne peut
  pas inventer.
"""

import re

MAX_TOOLS = 256
WALK_BUDGET_NODES = 5000
DEEP_SCHEMA_MAX = 4
BIG_ENUM_MAX = 50
DESCRIPTION_MIN = 10
NAME_MAX_SPEC = 128
NAME_MAX_DIRECTORY = 64
NAME_ALLOWED = re.compile(r"^[A-Za-z0-9_.\-]+$")

PROTOCOL_REVISIONS = ("2024-10-07", "2024-11-05", "2025-03-26",
                      "2025-06-18", "2025-11-25", "2026-07-28")
PROTOCOL_CURRENT = "2026-07-28"
ENVELOPE_PROTOCOL_KEY = "io.modelcontextprotocol/protocolVersion"

DRAFT07_URLS = ("http://json-schema.org/draft-07/schema#",
                "http://json-schema.org/draft-07/schema")

SEVERITIES = ("critical", "warning", "info")

# règle -> (sévérité, pourquoi, réparation, preuve)
RULES = {
    "EMPTY_INPUT_SCHEMA": (
        "critical",
        "inputSchema absent, vide ou non-dict : les clients rejettent "
        "la fiche entiere (gitlab-mcp #286) et le modele re-construit "
        "les arguments un appel rate a la fois (prime-agent #1073)",
        "donne a l'outil un objet schema avec type:object et ses "
        "propriétés réelles",
        "gitlab-mcp #286; prime-agent #1073"),
    "ROOT_NOT_OBJECT": (
        "critical",
        "racine sans type:\"object\" (ou composition allOf/oneOf/anyOf "
        "à la racine) : Claude Code droppe l'outil en silence "
        "(langfuse #13804)",
        "promouvoir {\"type\":\"object\",\"properties\":{...}} à la "
        "racine ; composer a l'interieur des proprietes",
        "langfuse #13804"),
    "TUPLE_ITEMS": (
        "critical",
        "\"items\" en liste = grammaire draft-07 : les clients stricts "
        "2020-12 rejettent TOUT le listing (strapi #27395 ; TS SDK "
        "#2084 P1 trois mois)",
        "formes tuple -> {\"prefixItems\": [...], \"items\": {schema}}",
        "strapi #27395; TS SDK #2084"),
    "DUP_NAME": (
        "critical",
        "deux outils portent le meme nom : la resolution cote client "
        "est un tirage, pas une regle",
        "renommer — les noms sont uniques par serveur",
        "MCP tools spec (uniqueness within a server)"),
    "NAME_UNSAFE": (
        "critical",
        "nom hors classe [A-Za-z0-9_.-] (espace, emoji, accent, "
        "homoglyphe non-ASCII) ou > 128 : invisible, non adressable "
        "par les clients — la classe du « cep » a a cyrillique qui "
        "nous a mordus au bundle89",
        "noms ASCII de la classe publiee ; un nom non-ASCII est un "
        "bug invisible, jamais une fantaisie",
        "spec 2025-11-25 tool-names; incident interne b89"),
    "REQUIRED_UNKNOWN": (
        "critical",
        "required[] nomme un champ absent de properties{} : le schema "
        "se contredit lui-meme, les validateurs stricts et les "
        "agents plantent a l'appel",
        "aligner required sur les proprietes declarees",
        "CloudCorpRecords/mcpaudit (required fields that don't exist)"),
    "PROTO_UNKNOWN": (
        "critical",
        "protocolVersion declare hors des revisions connues : echo "
        "invente sur handshake legacy (go-sdk #1033), version codee "
        "en dur (mcpkit #12), refus de negocier (ferrum-edge #2168)",
        "utiliser une revision publisee, ou negocier vers elle",
        "go-sdk #1033; mcpkit #12; ferrum-edge #2168"),
    "NO_DESCRIPTION": (
        "warning",
        "description absente ou vide : les modeles n'appellent pas "
        "correctement ce qu'ils ne peuvent pas lire",
        "une phrase : quand l'appeler, avec quoi, ce qu'il rend",
        "CloudCorpRecords/mcpaudit (descriptions)"),
    "DESCRIPTION_ECHO": (
        "warning",
        "description = le nom repete ou sous 10 caracteres : un "
        "geste, pas une information — le modele devine la semantique",
        "decrire le CONTRAT, pas relire l'etiquette",
        "CloudCorpRecords/mcpaudit; glama mcp-schema-audit-mcp"),
    "PARAMS_ALL_UNDESCRIBED": (
        "warning",
        "toutes les proprietes sans description : chaque champ est "
        "une devinette, les args partent mal remplis",
        "une ligne par parametre — unite, format, bornes",
        "CloudCorpRecords/mcpaudit (parameter docs)"),
    "NO_SERVER_NAME": (
        "warning",
        "initialize sans serverInfo.name : rien a afficher, rien a "
        "dédupliquer cote client",
        "serverInfo{name,version} dans la reponse initialize",
        "mcp-schema-audit (initialize without serverInfo.name)"),
    "PROTO_MISSING": (
        "warning",
        "initialize sans champ de version de protocole : la "
        "negociation est unprouvable depuis la fiche",
        "rendre protocolVersion (ou la cle d'enveloppe "
        "io.modelcontextprotocol/protocolVersion)",
        "mcp-schema-audit (protocol version negotiation chaos)"),
    "NAME_DOT": (
        "warning",
        "point dans le nom : permis par la spec MCP, REFUSE en aval "
        "par les fournisseurs au pattern ^[a-zA-Z0-9_-]+$ — le "
        "listing passe, l'appel casse",
        "pour viser les fournisseurs compatible-OpenAI, remplacer . "
        "par _",
        "typescript-sdk #1512 (400 pattern)"),
    "EMPTY_TOOLS": (
        "info",
        "listing sans aucun outil : si le serveur n'expose que "
        "prompts/resources, c'est un etat legitime — sinon le "
        "serveur est invisible",
        "auditer comme ce que le serveur est (prompts/resources), "
        "ou lister les outils",
        "CloudCorpRecords/mcpaudit (no tools is not a failure)"),
    "NO_INITIALIZE": (
        "info",
        "pas de reponse initialize collée : version et serverInfo "
        "restent prononcables ni l'un ni l'autre",
        "coller le resultat initialize a cote des tools pour "
        "l'audit complet",
        "mcp-schema-audit (no initialize in recording)"),
    "NAME_LONG": (
        "info",
        "nom de 65 a 128 caracteres : dans la spec posee, hors du "
        "bord 64 de l'Anthropic Directory",
        " viser le Directory, descendre a <= 64",
        "mcpbundles naming guide; Anthropic tool design reference"),
    "SLASH_NAME": (
        "info",
        "slash dans le nom : etat du droit EN CONFLIT — SEP-986 "
        "(Final) l'autorise et borne a 64 ; la spec posee "
        "(2025-11-25, draft) l'omet et borne a 128. Rendu, pas tranche",
        "le conflit est dans la reponse — choisir son client cible",
        "SEP-986 vs spec 2025-11-25; typescript-sdk #1512"),
    "MIXED_NAMING": (
        "info",
        "conventions de nom melangees dans le listing (snake/camel/"
        "Pascal/kebab) : le modele hesite la ou la famille est reglee",
        "une seule convention par serveur",
        "glama mcp-schema-audit-mcp (cross-tool naming)"),
    "DEEP_SCHEMA": (
        "info",
        "properties imbriquees au-dela de 4 niveaux : les modeles "
        "remplissent mal le profond",
        "aplatir — les schemas plats se remplissent plat",
        "glama mcp-schema-audit-mcp (deeply nested schemas)"),
    "BIG_ENUM": (
        "info",
        "enum de plus de 50 choix : le contexte s'assèche et le "
        "modele invente des valeurs hors liste",
        "referencer l'enum ailleurs, ou la reduire",
        "glama mcp-schema-audit-mcp (oversized enums)"),
    "DIALECT_DRAFT07": (
        "warning",
        "$schema declare draft-07 : l'outillage MCP courant part de "
        "2020-12 — sans tuple ici, mais le melange des dialectes est "
        "la porte d'entree des rejets stricts",
        "publisher en 2020-12, ou assumer la matrice des clients",
        "strapi #27395; TS SDK #2084"),
    "WALK_TRUNCATED": (
        "info",
        "budget de marche de 5000 noeuds epuise : les findings "
        "profonds sont PARTIELS — le dire est la regle, se taire "
        "etait le bug du ledger du 23-11",
        "auditer en morceaux, ou reduire le listing",
        "loi interne : une sonde tronquee EST un resultat nomme"),
}

_SCALE = {"critical": 0, "warning": 1, "info": 2}


class McpAuditError(ValueError):
    def __init__(self, field, message, expected):
        super().__init__(f"{field} {message}")
        self.field = field
        self.message = message
        self.expected = expected


def _finding(findings, rule, tool, detail):
    sev, why, fix, evidence = RULES[rule]
    findings.append({"rule": rule, "severity": sev, "tool": tool,
                     "detail": detail, "why": why, "fix": fix,
                     "evidence": evidence})


def _label(tool, index):
    name = tool.get("name") if isinstance(tool, dict) else None
    if isinstance(name, str) and name:
        return name
    return "tools[%d]" % index


def _name_convention(name):
    if "_" in name:
        return "snake_case"
    if "-" in name:
        return "kebab-case"
    if name[:1].isupper():
        return "PascalCase"
    if any(c.isupper() for c in name):
        return "camelCase"
    return "lowercase"


def _norm_name(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _walk(node, path, state, on_node):
    """Parcours itératif déterministe (pile, clés triées), budget nommé.
    Itératif ET non récursif : un listing ennemi de 10 000 niveaux ne
    doit pas tuer le serveur avec un RecursionError — le budget le
    borde, la pile ne saute pas."""
    stack = [(node, path)]
    while stack:
        if state["truncated"] or state["nodes"] >= WALK_BUDGET_NODES:
            state["truncated"] = True
            return
        cur, cpath = stack.pop()
        on_node(cur, cpath, state)
        if isinstance(cur, dict):
            state["nodes"] += 1
            for k in sorted(cur.keys(), reverse=True):
                stack.append((cur[k], cpath + "." + k if cpath else k))
        elif isinstance(cur, list):
            state["nodes"] += 1
            for i in range(len(cur) - 1, -1, -1):
                stack.append((cur[i], "%s[%d]" % (cpath, i)))


def _check_schema(schema, label, findings, state):
    """Rules racine + marche complete (tuples, profondeur, enums)."""
    if not isinstance(schema, dict):
        return
    root_type = schema.get("type")
    composed = any(k in schema for k in ("allOf", "oneOf", "anyOf"))
    if root_type != "object":
        if root_type is None and composed:
            _finding(findings, "ROOT_NOT_OBJECT", label,
                     "racine composition %s, pas type:object"
                     % next(k for k in ("allOf", "oneOf", "anyOf")
                            if k in schema))
        elif root_type is None:
            _finding(findings, "ROOT_NOT_OBJECT", label,
                     "racine muette : ni type ni properties declarables")
        else:
            _finding(findings, "ROOT_NOT_OBJECT", label,
                     "type racine %r, attendu 'object'" % (root_type,))
    root_props = schema.get("properties")
    req = schema.get("required")
    if req is not None:
        if not isinstance(req, list) or not all(isinstance(x, str)
                                                for x in req):
            _finding(findings, "REQUIRED_UNKNOWN", label,
                     "required n'est pas une liste de chaines")
        else:
            known = set(root_props.keys()) if isinstance(root_props, dict) \
                else set()
            for field in sorted(set(req)):
                if field not in known:
                    _finding(findings, "REQUIRED_UNKNOWN", label,
                             "required nomme '%s' : absent de "
                             "properties{}" % field)
    dialect = schema.get("$schema")
    if isinstance(dialect, str) and dialect in DRAFT07_URLS:
        _finding(findings, "DIALECT_DRAFT07", label,
                 "$schema = draft-07 a la racine")

    hits = {"tuple": False, "enum": False}

    def visit(node, path, st):
        if not isinstance(node, dict):
            return
        items = node.get("items")
        if isinstance(items, list) and not hits["tuple"]:
            hits["tuple"] = True
            _finding(findings, "TUPLE_ITEMS", label,
                     "items en forme tuple (liste) a '%s'"
                     % (path or "racine",))
        enum = node.get("enum")
        if isinstance(enum, list) and len(enum) > BIG_ENUM_MAX \
                and not hits["enum"]:
            hits["enum"] = True
            _finding(findings, "BIG_ENUM", label,
                     "enum de %d choix a '%s' (bord nomme %d)"
                     % (len(enum), path or "racine", BIG_ENUM_MAX))

    props_depth_state = {"max_depth": 0}

    def depth_scan(node, level):
        # récursion BORNEE de force : level monte aussi pour items/
        # additionalProperties — un chainage ennemi ne descend jamais
        # plus bas que DEEP_SCHEMA_MAX + 1, la pile ne saute pas.
        if level > DEEP_SCHEMA_MAX + 1:
            return
        if isinstance(node, dict):
            props = node.get("properties")
            if isinstance(props, dict):
                props_depth_state["max_depth"] = max(
                    props_depth_state["max_depth"], level)
                for k in sorted(props.keys()):
                    depth_scan(props[k], level + 1)
            for k in ("items", "additionalProperties"):
                if k in node and isinstance(node[k], dict):
                    depth_scan(node[k], level + 1)

    depth_scan(schema, 1)
    if props_depth_state["max_depth"] > DEEP_SCHEMA_MAX:
        _finding(findings, "DEEP_SCHEMA", label,
                 "properties imbriquees a %d niveaux (bord nomme %d)"
                 % (props_depth_state["max_depth"], DEEP_SCHEMA_MAX))

    _walk(schema, "", state, visit)


def agent_mcp_audit(tools, initialize=None):
    if not isinstance(tools, list):
        raise McpAuditError(
            "tools", "must be a list of tool dicts, the tools/list "
            "result verbatim",
            "array 0..%d of objects — paste tools/list" % MAX_TOOLS)
    if len(tools) > MAX_TOOLS:
        raise McpAuditError(
            "tools", "%d entries over the named cap" % len(tools),
            "at most %d tools per audit call" % MAX_TOOLS)
    for i, t in enumerate(tools):
        if not isinstance(t, dict):
            raise McpAuditError(
                "tools[%d]" % i, "must be an object, the listing entry "
                "verbatim", "a tool dict as tools/list renders it")
    if initialize is not None and not isinstance(initialize, dict):
        raise McpAuditError(
            "initialize", "must be the initialize result object or "
            "absent", "the initialize response, verbatim, or omit it")

    findings = []
    state = {"nodes": 0, "truncated": False}

    if not tools:
        _finding(findings, "EMPTY_TOOLS", "-",
                 "aucun outil dans la fiche recue")

    conventions = {}
    seen_names = set()
    for i, tool in enumerate(tools):
        label = _label(tool, i)
        name = tool.get("name")
        if not isinstance(name, str) or not name:
            _finding(findings, "NAME_UNSAFE", label,
                     "nom absent ou non-string")
        else:
            if name in seen_names:
                _finding(findings, "DUP_NAME", name,
                         "le nom apparait plus d'une fois dans la fiche")
            seen_names.add(name)
            if len(name) > NAME_MAX_SPEC:
                _finding(findings, "NAME_UNSAFE", name,
                         "%d caracteres, au-dela du bord 128 de la spec"
                         % len(name))
            elif len(name) > NAME_MAX_DIRECTORY:
                _finding(findings, "NAME_LONG", name,
                         "%d caracteres : dans la spec, hors du bord 64 "
                         "du Directory" % len(name))
            bad = sorted(set(c for c in name if not NAME_ALLOWED.match(c)))
            if bad:
                if bad == ["/"]:
                    _finding(findings, "SLASH_NAME", name,
                             "le nom contient '/'")
                else:
                    nonascii = sorted(set(c for c in bad if ord(c) > 127))
                    detail = ("caracteres hors classe : %s"
                              % ", ".join(
                                  "%s(U+%04X)" % (repr(c)[1:-1], ord(c))
                                  for c in bad[:4]))
                    if nonascii:
                        detail += " — classe homoglyphe invisible"
                    _finding(findings, "NAME_UNSAFE", name, detail)
            # le POINT est dans la classe autorisée par la spec MCP —
            # mais HORS du pattern aval ^[a-zA-Z0-9_-]+$ des fournisseurs
            # compatible-OpenAI : le listing passe, l'appel casse.
            # typescript-sdk #1512 cite le 400 verbatim.
            if "." in name and (not bad or bad == ["/"]):
                _finding(findings, "NAME_DOT", name,
                         "point dans le nom : le pattern fournisseur "
                         "^[a-zA-Z0-9_-]+$ refusera l'appel")
            conv = _name_convention(name)
            conventions.setdefault(conv, [])
            if len(conventions[conv]) < 3:
                conventions[conv].append(name)

        desc = tool.get("description")
        if desc is None or (isinstance(desc, str) and not desc.strip()):
            _finding(findings, "NO_DESCRIPTION", label,
                     "pas de description")
        elif not isinstance(desc, str):
            _finding(findings, "NO_DESCRIPTION", label,
                     "description non-string")
        else:
            if _norm_name(desc) == _norm_name(label) and isinstance(
                    tool.get("name"), str):
                _finding(findings, "DESCRIPTION_ECHO", label,
                         "la description ne fait que relire le nom")
            elif len(desc.strip()) < DESCRIPTION_MIN:
                _finding(findings, "DESCRIPTION_ECHO", label,
                         "description de %d caracteres sous le seuil "
                         "nomme %d" % (len(desc.strip()), DESCRIPTION_MIN))

        schema = tool.get("inputSchema")
        if not isinstance(schema, dict) or schema == {}:
            _finding(findings, "EMPTY_INPUT_SCHEMA", label,
                     "inputSchema absent/vide/malforme"
                     if schema is None or schema == {} else
                     "inputSchema non-dict (%s)" % type(schema).__name__)
        else:
            props = schema.get("properties")
            if isinstance(props, dict) and props:
                described = 0
                for pname in sorted(props.keys()):
                    p = props[pname]
                    if isinstance(p, dict) and isinstance(p.get("description"),
                                                          str) \
                            and p["description"].strip():
                        described += 1
                if described == 0:
                    _finding(findings, "PARAMS_ALL_UNDESCRIBED", label,
                             "0 description sur %d proprietes"
                             % len(props))
            _check_schema(schema, label, findings, state)

    if len(conventions) > 1:
        _finding(findings, "MIXED_NAMING", "-",
                 "conventions melees : %s"
                 % "; ".join("%s(%s)" % (c, ", ".join(v))
                             for c, v in sorted(conventions.items())))

    if initialize is None:
        _finding(findings, "NO_INITIALIZE", "-",
                 "aucun initialize colle : version et serverInfo "
                 "introuvables depuis la seule liste d'outils")
    else:
        version = initialize.get("protocolVersion")
        if not isinstance(version, str) or not version:
            version = initialize.get(ENVELOPE_PROTOCOL_KEY)
        if not isinstance(version, str) or not version:
            _finding(findings, "PROTO_MISSING", "-",
                     "aucun champ protocolVersion (ni cle d'enveloppe "
                     "io.modelcontextprotocol/...)")
        elif version not in PROTOCOL_REVISIONS:
            _finding(findings, "PROTO_UNKNOWN", "-",
                     "protocolVersion %r hors des revisions connues %s"
                     % (version, ", ".join(PROTOCOL_REVISIONS)))
        info = initialize.get("serverInfo")
        if not isinstance(info, dict) or not isinstance(
                info.get("name"), str) or not info["name"].strip():
            _finding(findings, "NO_SERVER_NAME", "-",
                     "initialize sans serverInfo.name exploitable")

    if state["truncated"]:
        _finding(findings, "WALK_TRUNCATED", "-",
                 "budget de %d noeuds epuise apres %d — findings "
                 "profonds incomplets" % (WALK_BUDGET_NODES, state["nodes"]))

    counts = {"critical": 0, "warning": 0, "info": 0}
    for f in findings:
        counts[f["severity"]] += 1
    if counts["critical"]:
        verdict = "REJECTED"
    elif counts["warning"]:
        verdict = "NEEDS_REVIEW"
    elif counts["info"]:
        verdict = "INFORMATIONAL"
    else:
        verdict = "CLEAN"

    return {
        "verdict": verdict,
        "counts": counts,
        "tools_checked": len(tools),
        "findings": findings,
        "protocol": {"known_revisions": list(PROTOCOL_REVISIONS),
                     "current": PROTOCOL_CURRENT},
        "caps": {"tools_max": MAX_TOOLS, "walk_nodes": WALK_BUDGET_NODES,
                 "description_min": DESCRIPTION_MIN,
                 "name_max_spec": NAME_MAX_SPEC,
                 "name_max_directory": NAME_MAX_DIRECTORY,
                 "deep_schema_max": DEEP_SCHEMA_MAX,
                 "big_enum_max": BIG_ENUM_MAX},
        "boundary": "static listing verdict — shape is certified, "
                    "runtime never: no fetch, no subprocess, no call",
    }
