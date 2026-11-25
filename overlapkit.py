# -*- coding: utf-8 -*-
"""overlapkit — /agent/tool-overlap : QUELS DEUX OUTILS N'EN FONT QU'UN,
dans QUEL CLIENT, et de COMBIEN il faut raccourcir pour que ça tienne.

LA DOULEUR, publiée et vécue (lentille DEV, rang 1 tenu trois cycles ;
six gates LUS À LA SOURCE primaire le 2026-11-25, verbatim) : un agent
colle son tools/list MCP chez un client et un outil DISPARAÎT SANS ERREUR
— deux ids distincts deviennent le MÊME id sous la grammaire de noms du
client. Sources nommées, chaque ligne de la table ci-dessous est une
citation, pas une mémoire :

1. microsoft/vscode#338895 (ouvert 30-sept-2026, code lu) :
   `id = (idPrefix + name).replaceAll('.','_').slice(0, 64)`.
   « The 64 chars length limit is correct, because model provider APIs
   cap function names at 64. But VS code doesn't keep the IDs unique
   after the cut. » La collision fait THROW dans _syncTools, le throw
   AVORTE la boucle de registration différée, et « all tools after it
   in alphabetical order are silently dropped ». Leur repro publié :
   5 outils → 2 listés ; les deux derniers, SHORTS, meurent par
   ABORT, pas par leur propre longueur.
2. google-gemini/gemini-cli, source main `generateValidName` (lue) :
   préfixe `mcp_` forcé, sanitizer `[^a-zA-Z0-9_\-.:] -> _`, tete
   invalide -> `_` préfixé, et si > 63 : `slice(0,30) + "..." +
   slice(-30)` — 30+3+30 = 63. « That transform is not injective »
   (issue #28970) : deux noms qui different SEULEMENT du milieu jeté
   deviennent identiques, et `ToolRegistry.registerTool` OVERWRITE —
   le dernier enregistré gagne, le premier EST MORT. Note de leur
   source : `MAX_FUNCTION_NAME_LENGTH=64`, safeLimit 63, « as some
   environments have off-by-one behaviors ».
3. openai/openai-openapi `openapi.yaml` (lu) : « Must be a-z, A-Z,
   0-9, or contain underscores and dashes, with a maximum length
   of 64. » — LOUD 400, le bon bruit.
4. Gemini REST OpenAPI officiel `generate-content.openapi.json` (lu) :
   FunctionDeclaration.name « Must be a-z, A-Z, 0-9, or contain
   underscores, colons, dots, and dashes, with a maximum length
   of 128. » — L'ASYMÉTRIE EST LA THÈSE : l'API accepte 128, leur CLI
   plie à 63. Un nom parfaitement légal chez l'API EST UN ANGE MORT
   chez le client, et chaque client est plus strict AUTREMENT.
5. microsoft/foundry-dev-tools#723 (lu) : la coupe naive est
   « collision-unsafe and can be worse than the 400 — trading a loud,
   correct error for a quiet, wrong one » ; leur vecteur publié :
   `mcp__<uuid>__get_deployment_logs_for_production` (77) et
   `..._for_preview` (74) partagent leurs 64 premiers chars →
   « a call meant for production logs now dispatches to preview ».
6. andrewyng/openworker#746 (lu) : le nom tronqué sert À LA FOIS de nom
   montré au modèle et de clé du registre ; le modèle rappelle le nom
   COMPLET → « unknown tool », l'outil ne s'exécute jamais.
7. router-for-me/CLIProxyAPI#6209 (lu) : la conversion Responses→Claude
   coupe à 64 sans contrôle de collisions → Anthropic répond 400
   « tools: Tool names must be unique » — bruyant, OUBLIÉ quand
   l'appel part vers un modèle sans ce contrôle.
8. CopilotKit#7495 (lu) : deux serveurs exposant le MÊME nom nu — le
   spread remplace l'outil du serveur précédent sans avertissement.
9. platform.claude.com Messages (réf. 2026-10-21, lue) : aucune limite
   de LONGUEUR publiée pour les noms d'outils, mais l'erreur
   NOMMÉE `tool_name_conflict` — « a tool of another kind, or of
   another MCP server, already holds » — la collision de noms est un
   400 annoncé CHEZ EUX. Le module ne jure donc JAMAIS une longueur
   anthropic : ce qui n'est pas publié ne se jure pas (leçon soldes-lu).
10. FacileStudio/nacelle `mcp/client/bridge.go` (lu) : l'école
    d'en face, « Nothing is truncated. A name cut to fit silently maps
    two distinct tools onto one, which is a reported production
    failure in awslabs/mcp and is worse than the refusal it was trying
    to avoid: the model calls what it thinks is the read tool and
    gets the write one. »

CE QUI N'EXISTAIT PAS (question 5, payée 13h00) : tool-trim (b106) dit
QUOI COUPER pour le budget, context-tax (b101) dit COMBIEN coûte la
liste, mcp-surface dit CE QUI A CHANGÉ entre deux relevés — AUCUN ne
COMPTE les collisions de NOMS, qui sont un mécanisme distinct : un
listing peut être sous budget, inchangé, et pourtant muet d'un outil.
Dehors : chaque projet du gate ne répare QUE SON chemin (VS Code sa
coupe, le CLI son fold, la passerelle sa conversion) ; aucun service
ne répond « ces deux ids n'en font qu'un DANS CE client ». Proie franche.

LOIS FERMÉES :
1. La table des grammaires est CLOSE : {vscode, gemini_cli, head64,
   openai, anthropic, gemini_api}. Chaque rangée porte SON builder,
   SON cap, SON comportement publié (SILENT vs LOUD). Aucun LM, aucun
   réseau, aucun nom de client inventé : hors table = refus nommé.
2. Les coupes JS sont des unités UTF-16, pas des code points — le
   module compte et tranche en unités UTF-16 comme `String.slice`, et
   le DIT (un emoji compte 2 pour un client JS).
3. Comportements rejoués, jamais déviés : vscode = tri ALPHABÉTIQUE des
   ids coupés, la première re-registration qui HEURTE un id déjà posé
   THROWS et ABORT la boucle — tout ce qui suit en ordre alphabétique
   est perdu (le vecteur publié 5→2 est un test). gemini_cli =
   OVERWRITE : le dernier gagné, les autres morts. head64 = pas de
   contrôle : COLLAPSE = WRONG_ROUTE (foundry) ou UNKNOWN_CALL
   (openworker), selon que le nom coupé sert de clé ou pas — les deux
   noms voyagent dans la réponse.
4. REPAIR = NOMBRE : pour les grammaires à clef serveur (vscode,
   head64), la plus COURTE longueur de clef (repli sur les L premiers
   chars de chaque clef, L minimal) qui rend toutes les têtes coupées
   UNIQUES — le workaround publié d'openworker (« Shorten the server
   key in mcp.json ») RENDU EN NOMBRE, pas en conseil. Si même la clef
   vide ne suffit pas : NO_PREFIX_FIX nommé — c'est le nom des OUTILS
   qu'il faut renommer, et le module le dit avec la position du
   premier caractère distinctif.
5. GATE_STRICTER_THAN_API est une classe NOMMÉE : nom légal chez
   gemini_api (≤128 charset autorisé) et coupé/plié par un client —
   la preuve vivante que « l'API l'accepte » ne promet RIEN.
6. Anthropic : conflit de nu NOMS uniquement (tool_name_conflict, cité) ;
   JAMAIS de drapeau longueur (non publié). OpenAI : charset ET 64.
   Gemini API : charset [a-zA-Z0-9_:.-] ET 128.
7. Le même nom nu chez DEUX serveurs = BARE_SHADOW signalée une fois
   (classe CopilotKit), jamais recomptée par client.
"""
import hashlib
import json
import re

class OverlapError(Exception):
    def __init__(self, field, message, expected):
        self.field = field
        self.message = message
        self.expected = expected
        super().__init__(message)


MAX_TOOLS = 5000
MAX_FIELD = 300
CUT = 64            # la coupe VS Code / head64, en UNITES UTF-16
FOLD_LIMIT = 63     # safeLimit gemini-cli
FOLD_EDGE = 30      # head/tail gemini-cli


# --------------------------------------------------------------- UTF-16
def _u16(s):
    return len(s.encode("utf-16-le")) // 2


def _head(s, k):
    return s.encode("utf-16-le")[:2 * k].decode("utf-16-le", "ignore")


def _tail(s, k):
    return s.encode("utf-16-le")[-2 * k:].decode("utf-16-le", "ignore")


# --------------------------------------------------------------- table
def _vscode_build(server, name):
    raw = ("mcp_" + server + "_" + name) if server else name
    return raw.replace(".", "_")


def _gcli_build(server, name):
    # formatMcpToolName + generateValidName, recopiés de la source lue.
    q = ("mcp_" + server + "_" + name) if server else name
    v = q if q.startswith("mcp_") else "mcp_" + q
    v = re.sub(r"[^a-zA-Z0-9_\-.:]", "_", v)
    if v and not re.match(r"[a-zA-Z_]", v[0]):
        v = "_" + v
    return v


def _head64_build(server, name):
    return ("mcp__" + server + "__" + name) if server else name


def _fold(v):
    if _u16(v) > FOLD_LIMIT:
        return _head(v, FOLD_EDGE) + "..." + _tail(v, FOLD_EDGE)
    return v


# (builder, cap ou None, comportement publié : SILENT / LOUD, source)
TARGETS = {
    "vscode": (_vscode_build, CUT, "SILENT", "microsoft/vscode#338895"),
    "gemini_cli": (None, FOLD_LIMIT, "SILENT", "gemini-cli mcp-tool.ts"),
    "head64": (_head64_build, CUT, "SILENT",
               "foundry-dev-tools#723 / openworker#746"),
    "openai": (None, CUT, "LOUD", "openai/openai-openapi openapi.yaml"),
    "anthropic": (None, None, "LOUD",
                  "platform.claude.com tool_name_conflict"),
    "gemini_api": (None, 128, "LOUD",
                   "generate-content.openapi.json FunctionDeclaration"),
}
PROVIDER_CHARSET = {
    "openai": r"^[a-zA-Z0-9_-]{1,%d}$",
    "gemini_api": r"^[a-zA-Z0-9_\-:.]{1,%d}$",
}

CLIENTS = ("vscode", "gemini_cli", "head64")


# --------------------------------------------------------------- noyau
def tool_overlap(tools, targets=None):
    if not isinstance(tools, list):
        raise OverlapError("tools", "must be an array of {name, server?}",
                           "array")
    if not tools:
        raise OverlapError("tools", "empty listing — nothing to check",
                           "at least one tool")
    if len(tools) > MAX_TOOLS:
        raise OverlapError("tools", "listing over ceiling",
                           "at most %d tools" % MAX_TOOLS)
    seen_exact = set()
    for i, t in enumerate(tools):
        if not isinstance(t, dict):
            raise OverlapError("tools[%d]" % i, "must be an object",
                               "{name, server?}")
        name = t.get("name")
        server = t.get("server")
        if not isinstance(name, str) or not name:
            raise OverlapError("tools[%d].name" % i,
                               "tool names are refused empty or non-string",
                               "non-empty string")
        if len(name) > MAX_FIELD:
            raise OverlapError("tools[%d].name" % i, "name over ceiling",
                               "at most %d chars" % MAX_FIELD)
        if server is not None and (not isinstance(server, str) or not server
                                   or len(server) > MAX_FIELD):
            raise OverlapError("tools[%d].server" % i,
                               "server key refused empty or over ceiling",
                               "string of at most %d chars" % MAX_FIELD)
        if t.keys() - {"name", "server"}:
            raise OverlapError("tools[%d]" % i,
                               "unknown keys — paste {name, server?} only",
                               "name, server")
        key = (server or "", name)
        if key in seen_exact:
            raise OverlapError("tools[%d]" % i,
                               "identical (server, name) pasted twice — "
                               "a listing bug, not a collision to report",
                               "distinct entries")
        seen_exact.add(key)

    if targets is None:
        targets = sorted(TARGETS)
    bad = [x for x in targets if x not in TARGETS]
    if bad:
        raise OverlapError(
            "targets", "unknown grammar — the table is closed",
            "one of " + ", ".join(sorted(TARGETS)))

    out = {"tools_in": len(tools), "targets": {}, "gates": {}}

    # --- noms nus partagés par plusieurs serveurs (CopilotKit spread)
    bare = {}
    for i, t in enumerate(tools):
        bare.setdefault(t["name"], set()).add(t.get("server"))
    shadows = [[n, sorted(s for s in ss if s)] for n, ss in
               sorted(bare.items()) if len(ss) > 1]
    out["bare_shadows"] = shadows

    def final_id(t, target):
        b = TARGETS[target][0]
        if target == "gemini_cli":
            return _fold(_gcli_build(t.get("server"), t["name"]))
        if b is None:                       # providers : ce qui est collé
            return t["name"]
        return _head(b(t.get("server"), t["name"]), TARGETS[target][1])

    for target in targets:
        builder, cap, loud, src = TARGETS[target]
        ids = [final_id(t, target) for t in tools]
        rows = {"source": src, "ids": ids}
        groups = []
        byid = {}
        for i, d in enumerate(ids):
            byid.setdefault(d, []).append(i)
        dup = {d: ix for d, ix in byid.items() if len(ix) > 1}

        if target in CLIENTS:
            b = TARGETS[target][0]
            for d, ix in sorted(dup.items()):
                if target == "gemini_cli":
                    raws = [("mcp_" + tools[j]["server"] + "_" + tools[j]["name"]
                             if tools[j].get("server") else tools[j]["name"])
                            for j in ix]
                    pres = [_gcli_build(tools[j].get("server"),
                                        tools[j]["name"]) for j in ix]
                else:
                    raws = [(("mcp_" + tools[j]["server"] + "_"
                              if b is _vscode_build else "mcp__" +
                              tools[j]["server"] + "__")
                             + tools[j]["name"]
                             if tools[j].get("server") else tools[j]["name"])
                            for j in ix]
                    pres = [b(tools[j].get("server"), tools[j]["name"])
                            for j in ix]
                if len(set(raws)) == 1:
                    cls = "EXACT_ID"
                elif len(set(pres)) == 1:
                    cls = "SANITIZE_COLLAPSE"
                elif target == "gemini_cli":
                    cls = "FOLD_COLLAPSE"
                else:
                    cls = "COLLAPSE_CUT"
                groups.append({
                    "class": cls, "id": d,
                    "members": [{"i": j, "name": tools[j]["name"],
                                 "server": tools[j].get("server")}
                                for j in ix]})

        if target == "vscode":
            # boucle de registration : tri alphabetique des ids coupes ;
            # la premiere re-registration qui heurte THROWS et ABORTE.
            order = sorted(range(len(ids)), key=lambda j: (ids[j], tools[j]["name"]))
            registered = set()
            abort_at = None
            for pos, j in enumerate(order):
                if ids[j] in registered:
                    abort_at = pos
                    break
                registered.add(ids[j])
            rows["registered"] = len(registered)
            # l'outil qui HEURTE n'est pas enregistre lui non plus —
            # le repro publie : 5 outils, 2 listes, 3 morts (le thrower
            # compris). tail_dropped voyage DONC de l'aborton inclus.
            rows["tail_dropped"] = ([tools[order[p]]["name"]
                                     for p in range(abort_at, len(order))]
                                    if abort_at is not None else [])
            if abort_at is not None:
                rows["behavior"] = "TAIL_ABORT"
        elif target == "gemini_cli":
            rows["behavior"] = "OVERWRITE_LAST"
            kept = {}
            for i, d in enumerate(ids):
                kept[d] = i
            rows["overwritten"] = [{"id": d, "kept": tools[i]["name"],
                                    "dead": [tools[j]["name"] for j in ix
                                             if j != i]}
                                   for d, ix in sorted(dup.items())]
        elif target == "head64":
            rows["behavior"] = "WRONG_ROUTE_or_UNKNOWN_CALL"

        if target not in CLIENTS:  # providers : verdicts sur le colle nu
            flags = []
            for i, d in enumerate(ids):
                charset = {"openai": r"^[a-zA-Z0-9_-]+$",
                           "gemini_api": r"^[a-zA-Z0-9_\-.:]+$"}.get(target)
                if charset and not re.match(charset, d):
                    flags.append({"class": "ILLEGAL_CHAR", "i": i, "name": d,
                                  "pattern": charset})
                elif cap is not None and _u16(d) > cap:
                    flags.append({"class": "TOO_LONG", "i": i, "name": d,
                                  "limit": cap})
            if target == "anthropic":
                for d, ix in sorted(dup.items()):
                    flags.append({"class": "NAME_CONFLICT", "id": d,
                                  "members": ix})
            rows["flags"] = flags

        groups.sort(key=lambda g: g["id"])
        rows["groups"] = groups[:100]
        rows["groups_folded"] = max(0, len(groups) - 100)
        out["targets"][target] = rows

    # --- repair en NOMBRE : la plus courte clef qui dé-colle les tetes
    for target in ("vscode", "head64"):
        if target not in out["targets"]:
            continue
        rows = out["targets"][target]
        servers = sorted({t["server"] for t in tools if t.get("server")})
        if servers and any(g["class"].endswith("_CUT") for g in rows["groups"]):
            best = None
            ceiling = max(len(s) for s in servers)
            for L in range(1, ceiling + 1):
                sh = set()
                ok = True
                for t in tools:
                    s = (t.get("server") or "")[:L]
                    nm = t["name"]
                    d = _head(TARGETS[target][0](s, nm), TARGETS[target][1])
                    if d in sh:
                        ok = False
                        break
                    sh.add(d)
                if ok:
                    best = L
                    break
            rows["repair"] = ({"min_server_key_len": best} if best
                              else {"verdict": "NO_PREFIX_FIX"})
        elif rows["groups"]:
            rows["repair"] = {"verdict": "NO_PREFIX_FIX"}

    # --- GATE_STRICTER_THAN_API : légal chez gemini_api, plié par un client
    if "gemini_api" in targets and "gemini_cli" in targets:
        strict = []
        for i, t in enumerate(tools):
            n = t["name"]
            legal_api = bool(re.match(r"^[a-zA-Z0-9_\-.:]{1,128}$", n))
            folded = _u16(_gcli_build(t.get("server"), n)) > FOLD_LIMIT
            if legal_api and folded:
                strict.append(n)
        out["gates"]["GATE_STRICTER_THAN_API"] = strict

    # --- verdict global
    silent = 0
    for target in CLIENTS:
        rows = out["targets"].get(target)
        if not rows:
            continue
        silent += len(rows.get("tail_dropped", [])) if target == "vscode" else 0
        if target == "gemini_cli":
            silent += sum(len(o["dead"]) for o in rows.get("overwritten", []))
        if target == "head64":
            silent += sum(len(g["members"]) - 1 for g in rows["groups"])
    loud = []
    for target in ("openai", "anthropic", "gemini_api"):
        rows = out["targets"].get(target)
        if rows:
            loud += rows.get("flags", [])
    verdict = ("SILENT_LOSS" if silent else
               "LOUD_ONLY" if loud else "CLEAN")
    out["silent_losses"] = silent
    out["loud_flags"] = len(loud)
    out["verdict"] = verdict
    return out


def overlap_sha(obj):
    return hashlib.sha256(json.dumps(
        obj, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode()).hexdigest()
