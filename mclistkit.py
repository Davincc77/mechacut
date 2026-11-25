# -*- coding: utf-8 -*-
"""mclistkit — /agent/mcp-list-completeness : TON CLIENT MCP A-T-IL VU
TOUTES LES PAGES ? Le listing est-il COMPLET, et que reste-t-il derrière
le curseur, EN NOMBRES.

LA DOULEUR, publiée et vécue (lentille DEV ; preuve lue à la source
primaire le 25-nov-2026, verbatim recopié ici, pas de mémoire).
Sept clients majeurs, SIX MOIS de reprod publiquées, le MÊME mécanisme —
le serveur paginate tools/list, le client appelle UNE fois, et tout ce
qui suit la page 1 meurt SANS ERREUR :

1. Mintplex-Labs/anything-llm#6935 (ouvert 1-nov-2026, CLOSED par PR
   #6937, merged 5b0cc9f 2-nov-2026, rendu v1.20.0) : « When an MCP
   server paginates tools/list, AnythingLLM silently omits every tool
   after the first page from both the settings list and the agent's
   plugins. The server remains marked as running, but the agent cannot
   use those omitted tools. » Leur repro : page1 [first] + curseur
   « page-two », le contrôle SDK explicite rend « second »,
   l'application ne voit QUE [ 'first' ]. Les trois règles fermées du
   fix MERGED, citées du corps du PR : « An empty page or empty-string
   cursor does not end pagination. ... repeated cursors are rejected to
   avoid an endless loop. ... Later-page errors use the existing error
   handling rather than exposing an incomplete tool list. »
2. openai/codex#28858 (ouvert 18-juin-2026, TOUJOURS OUVERT au scan) :
   corps lu — serveur page1 « 30 tools + nextCursor page-2 »,
   « Codex only exposed the first 30 tools. The tool from the second
   page was not callable. » ; code pointé : « the callable tool
   discovery path appears to call tools/list once with params = None ».
   Commentaires lus : un serveur 64/64/10 sur trois pages (curseurs
   « 64 », « 128 ») — Codex « registers exactly the first 64 » ; un
   serveur paginé à 1000 — « the other 2,642 are uncallable » ;
   workaround publié « codex features set mcp_2026_07_28 true » qui
   suit enfin les curseurs MAIS bascule la révision de protocole de
   CHAQUE serveur — casse les anciens. « tools/list is the only list
   endpoint missing that loop. »
3. anthropics/claude-code#23179 (ouvert 4-févr-2026, CLOSED) :
   « Claude Code only sees the first 100 tools, doesn't request
   page 2 » ; workaround : « MCP server authors can increase their
   page size (e.g., SetToolsPageSize(200)) ».
4. anthropics/claude-code#48126 (ouvert 14-avr-2026, CLOSED) :
   « All tools on subsequent pages are silently dropped with no
   warning. » — le 23179 bis, quatre mois plus tard.
5. anthropics/claude-code#66537 (ouvert 9-juin-2026, CLOSED) : Claude
   Desktop macOS ; passerelle AWS Bedrock AgentCore paginant « at 30
   tools/page » — « Tools on page 2+ are absent from the session and
   return "no such tool" if invoked. »
6. anthropics/claude-ai-mcp#87 (ouvert 9-mars-2026, TOUJOURS OUVERT) :
   web — « e.g., 21 tools with a page size of 15 » — « The remaining
   6 tools are silently missing. »
7. vercel/ai#19240 (ouvert 21-août-2026, CLOSED par fix : reproduction
   #19440, fix « Updated tools() to follow each nextCursor and combine
   all returned tool definitions ») : « Only the first page ever
   showed up, with no warning and no error. » — le package définit
   BIEN PaginatedResultSchema.nextCursor dans types.ts et ne l'utilise
   pas : le schema est là, la BOUCLE manque.
8. langchain-ai/openwiki#565 (ouvert 1-août-2026, CLOSED) : la coupure
   n'est même pas douce — « callMcpConnectorTool hard-rejects any tool
   name missing from the discovered set » : l'outil paginé d'après la
   page 1 existe côté serveur et meurt côté agent AVEC une erreur,
   sans que personne n'ait dit qu'il y avait une page 2.

LA LOI FERMÉE, relue 25-nov aux deux versions du spec (raw GitHub,
docs/specification/*/server/utilities/pagination.mdx) :
A. spec 2026-07-28 §Implementation Guidelines, verbatim :
   « Clients SHOULD: Treat a missing nextCursor as the end of
   results » ; « Clients MUST treat cursors as opaque tokens:
   Don't make assumptions about cursor format; Don't attempt to parse
   or modify cursors; Don't make any determination based on cursor
   value other than whether a non-null value was provided (e.g. an
   empty string is a valid cursor and thus MUST NOT be treated as the
   end of results) ». LA CLAUSE EMPTY-STRING EST NEUVE : la version
   2025-06-18 (lue aussi) porte le MUST d'opacité SANS cet exemple —
   le piège a été NOMMÉ dans le spec, pas deviné par nous.
B. spec §Pagination Flow : « List Request (no cursor) » — la première
   requête ne porte pas de curseur.
C. spec §Guidelines 1 : « Servers SHOULD: Provide stable cursors ».
D. spec §Error Handling : « Invalid cursors SHOULD result in an error
   with code -32602 (Invalid params) ».
E. spec 2026-07-28 changelog #8, verbatim : « All results now carry a
   required resultType field: "complete" for ordinary results and
   "input_required" for multi round-trip request interim results.
   Clients MUST treat results from earlier-protocol servers that omit
   the field as "complete" ».

CE QUI N'EXISTAIT PAS (question 5, payée au grep + aux sources) :
la fratrie — mcp-audit dit REJETÉ (forme), mcp-surface dit CHANGÉ
(deux relevés), tool-overlap dit FUSIONNÉ (collisions de noms),
context-tax dit COMBIEN COÛTE, tool-trim dit QUOI DÉBRANCHER,
cost-diff dit DE COMBIEN À COMBIEN. AUCUNE route ne COMPTE LES PAGES :
un listing peut être légal, inchangé, sans collision, sous budget —
et mourir quand même à la page 2. Dehors : le spec dit aux clients
comment faire, il ne dit à PERSONNE de vérifier ce qu'un client a vu ;
chaque repro ci-dessus a dû être pêché issue par issue, et six des
huit chemins ne sont toujours pas réparés au 25-nov-2026. Proie franche.

LOIS DU MODULE (vocabulaire clos, zéro LM, zéro réseau, zéro horloge) :
1. Les PAGES collées sont la vérité du client : chaque page = l'objet
   result tel que rendu ({tools, nextCursor?, resultType?}) ou l'objet
   error {-32602...} ; le champ trace « request » (curseur envoyé pour
   obtenir cette page) est FACULTATIF — sans lui les chaînons sont
   UNCHECKED, jamais devinés. Les enveloppes JSON-RPC {jsonrpc, id,
   result} sont déshabillées ; les clés d'outil inconnues (description,
   inputSchema) sont IGNORES : la forme vit chez mcp-audit, ICI on
   compte les PAGES.
2. Terminaison = cursor absent OU null (règle A). Un cursor PRÉSENT,
   fût-il la chaîne vide, dit « il y a une suite ». JAMAIS de
   détermination sur la VALEUR d'un curseur autre que null / non-null :
   les curseurs sont comparés OCTET À OCTET (légitime : le fix #6937
   rejeté les répétitions) et JAMAIS parsés — un curseur « 64 » n'est
   PAS l'offset 64, c'est une opaqueité.
3. Classes fermées, chacune avec sa source citée en sortie :
   PARTIAL_SILENT (raisons par priorité déclarée : ERROR_PAGE >
   EMPTY_PAGE_TRAP > EMPTY_CURSOR_TRAP > OPEN_CURSOR), CURSOR_LOOP,
   CHAIN_BREAK, SHORT_VS_DECLARED, OVER_VS_DECLARED, INTERIM_LISTED,
   DUPED (in-page + across-comptés séparément).
4. Verdict = la classe présente la plus SÉVÈRE, ordre DÉCLARÉ (il
   voyage dans la réponse) : STUCK_LOOP > TRUNCATED_SILENT > UNSTABLE >
   COUNT_SHORT > COUNT_OVER > INTERIM_LISTED > DUPED > COMPLETE.
   scan_complete n'est VRAI qu'au bout d'une chaîne intacte, terminée,
   sans page erreur ni page intérimaire.
5. Le déclaratif est un ARGUMENT, jamais une devinette :
   declared_count (entier) ou declared_names (liste) — les deux rendent
   le MANQUE en NOMBRE ; avec les noms, le manque est NOMMÉ (tri
   code-point, top-100 détaillé, queue pliée nommée). declared_names
   et declared_count incohérents = refus. Le manque court vs déclaré ne
   SE DIE (classe) que scan TERMINÉ : sinon c'est PARTIAL_SILENT qui
   porte la douleur, pas le serveur.
6. resultType : omis = « omitted_treated_complete » (règle E, mot pour
   mot) ; input_required = page INTÉRIMAIRE — les outils y sont comptés
   mais flaggés : un scan qui s'arrête là n'a JAMAIS vu le résultat.
7. réparer est un NOMBRE : resume.cursor = le curseur exact où
   reprendre (celui que le client n'a pas suivis), ou son refus nommé
   (LOOP — reprendre ne sert à rien ; REJECTED — le curseur est mort,
   re-tenter ne le ressuscite pas, redémarre le scan).
"""
import copy

class ListError(Exception):
    def __init__(self, field, message, expected):
        self.field = field
        self.message = message
        self.expected = expected
        super().__init__(message)


MAX_PAGES = 5000
MAX_TOOLS_TOTAL = 5000
MAX_FIELD = 300
NAME_FOLD = 100

PAGE_KEYS = {"tools", "nextCursor", "resultType", "request", "error"}
RESULT_TYPES = ("complete", "input_required")

SEVERITY = ["STUCK_LOOP", "TRUNCATED_SILENT", "UNSTABLE", "COUNT_SHORT",
            "COUNT_OVER", "INTERIM_LISTED", "DUPED", "COMPLETE"]
CLASS_VERDICT = {
    "CURSOR_LOOP": "STUCK_LOOP",
    "PARTIAL_SILENT": "TRUNCATED_SILENT",
    "CHAIN_BREAK": "UNSTABLE",
    "SHORT_VS_DECLARED": "COUNT_SHORT",
    "OVER_VS_DECLARED": "COUNT_OVER",
    "INTERIM_LISTED": "INTERIM_LISTED",
    "DUPED": "DUPED",
}

SOURCES = {
    "PARTIAL_SILENT":
        "anything-llm#6935 (merged #6937: 'silently omits every tool "
        "after the first page'); codex#28858; claude-code#23179/#48126/"
        "#66537; claude-ai-mcp#87; vercel/ai#19240; openwiki#565; "
        "spec 2026-07-28 pagination (missing nextCursor = end)",
    "CURSOR_LOOP":
        "anything-llm PR #6937 merged text: 'repeated cursors are "
        "rejected to avoid an endless loop'",
    "CHAIN_BREAK":
        "spec 2026-07-28 §Guidelines 1: 'Servers SHOULD provide stable "
        "cursors'",
    "EMPTY_PAGE_TRAP":
        "anything-llm PR #6937 merged text: 'An empty page or "
        "empty-string cursor does not end pagination'",
    "EMPTY_CURSOR_TRAP":
        "spec 2026-07-28 §Guidelines 3 verbatim: 'an empty string is a "
        "valid cursor and thus MUST NOT be treated as the end of "
        "results' (clause absent from 2025-06-18 — NAMED in the spec "
        "later, not guessed)",
    "ERROR_PAGE":
        "spec §Error Handling: 'Invalid cursors SHOULD result in an "
        "error with code -32602'; PR #6937: later-page errors must not "
        "expose an incomplete tool list",
    "INTERIM_LISTED":
        "spec 2026-07-28 changelog #8 (MRTR, SEP-2322): resultType "
        "'input_required' is an interim result",
    "SHORT_VS_DECLARED":
        "the declared count is an ARGUMENT (docs/registry/user-supplied)"
        " — never fetched, never invented",
    "OVER_VS_DECLARED":
        "more delivered than declared = the declaration lied or the "
        "catalog drifted mid-scan",
    "DUPED":
        "cross-page re-delivery: 'Servers SHOULD provide stable "
        "cursors' §Guidelines 1; counted, never deduped silently",
}

BOUNDARY = ("static page audit — pages pasted exactly as the client "
            "fetched them; no fetch, no subprocess, no clock; cursors "
            "compared byte-for-byte only and never parsed (spec MUST "
            "opacity); tool-entry keys beyond name are ignored — shape "
            "belongs to mcp-audit (sister)")


def _unwrap(p, i):
    if not isinstance(p, dict):
        raise ListError("pages[%d]" % i, "each page is a tools/list "
                        "result object (or its JSON-RPC envelope)",
                        "object")
    if "result" in p and ("jsonrpc" in p or "id" in p):
        inner = p["result"]
        if not isinstance(inner, dict):
            raise ListError("pages[%d].result" % i, "envelope result "
                            "must be an object", "object")
        extra = set(p) - {"jsonrpc", "id", "result", "request"}
        if extra:
            raise ListError("pages[%d]" % i, "envelope carries unknown "
                            "keys alongside result",
                            "jsonrpc, id, result, request?")
        out = dict(inner)
        for k in ("request",):
            if k in p:
                out[k] = p[k]
        return out
    if p.keys() - PAGE_KEYS:
        raise ListError("pages[%d]" % i, "unknown keys — paste "
                        "{tools, nextCursor?, resultType?, request?} "
                        "or {error, request?}",
                        ", ".join(sorted(PAGE_KEYS)))
    return p


def _folded(names):
    if len(names) > NAME_FOLD:
        return {"names": names[:NAME_FOLD], "folded": len(names) -
                NAME_FOLD, "fold_rule": "top %d detailed (names "
                "sorted by Unicode code point), tail folded and named"
                % NAME_FOLD}
    return {"names": names, "folded": 0}


def mcp_list_completeness(pages, declared_count=None,
                          declared_names=None):
    if not isinstance(pages, list) or not pages:
        raise ListError("pages", "empty audit — paste the pages the "
                        "client fetched", "non-empty array")
    if len(pages) > MAX_PAGES:
        raise ListError("pages", "over ceiling",
                        "at most %d pages" % MAX_PAGES)

    names = None
    if declared_names is not None:
        if not isinstance(declared_names, list) or \
                any(not isinstance(x, str) or not x or len(x) > MAX_FIELD
                    for x in declared_names):
            raise ListError("declared_names", "array of non-empty "
                            "strings, each at most %d chars" % MAX_FIELD,
                            "array")
        if len(set(declared_names)) != len(declared_names):
            raise ListError("declared_names", "names pasted twice — a "
                            "declaration is a SET", "distinct names")
        names = sorted(declared_names)
        if declared_count is not None and declared_count != len(names):
            raise ListError("declared", "declared_count contradicts "
                            "len(declared_names) — fix the claim",
                            "consistent numbers")
    if declared_count is not None and (isinstance(declared_count, bool)
                                       or not isinstance(declared_count,
                                                         int)
                                       or declared_count < 0):
        raise ListError("declared_count", "non-negative integer",
                        "integer")

    digests = []
    seen = set()
    dup_in = 0
    dup_across = 0
    dup_names = set()
    cursor_count = {}
    empty_pages = 0
    error_pages = 0
    chain_checked = 0
    chain_break = None
    interim_idx = None
    error_idx = None
    prev_cursor = None
    raw_total = 0

    for i, p0 in enumerate(pages):
        p = _unwrap(copy.deepcopy(p0), i)
        req = p.get("request")
        if i == 0 and req is not None:
            raise ListError("pages[0].request",
                            "the first list request carries NO cursor "
                            "(spec §Pagination Flow, verbatim: 'List "
                            "Request (no cursor)')",
                            "absent")
        if req is not None and (not isinstance(req, str) or
                                len(req) > MAX_FIELD):
            raise ListError("pages[%d].request" % i,
                            "string of at most %d chars" % MAX_FIELD,
                            "string")
        if req is not None:
            chain_checked += 1
            if req != prev_cursor:
                if chain_break is None:
                    chain_break = (i, prev_cursor, req)
        rt = p.get("resultType")
        if rt is not None and rt not in RESULT_TYPES:
            raise ListError("pages[%d].resultType" % i,
                            "vocabulary closed", "complete | "
                            "input_required")
        err = p.get("error")
        tools = []
        value = None
        if err is not None and rt is not None:
            raise ListError("pages[%d].resultType" % i,
                            "an error response is not a result — no "
                            "resultType either", "absent")
        if err is not None:
            if "tools" in p or "nextCursor" in p:
                raise ListError("pages[%d]" % i, "an error response "
                                "carries no result keys (JSON-RPC "
                                "either/or)", "error alone")
            if not isinstance(err, dict) or \
                    not isinstance(err.get("code"), int):
                raise ListError("pages[%d].error" % i, "error needs an "
                                "integer code", "{code, message?}")
            em = err.get("message")
            if em is not None and (not isinstance(em, str) or
                                   len(em) > MAX_FIELD):
                raise ListError("pages[%d].error.message" % i,
                                "string of at most %d chars" % MAX_FIELD,
                                "string")
            error_pages += 1
            if error_idx is None:
                error_idx = i
            state = "ABSENT"
        else:
            if "tools" not in p:
                raise ListError("pages[%d]" % i, "each result page "
                                "carries tools[] (or the page is an "
                                "error)", "tools array")
            tools = p["tools"]
            if not isinstance(tools, list):
                raise ListError("pages[%d].tools" % i, "array", "array")
            page_names = []
            for j, t in enumerate(tools):
                if not isinstance(t, dict):
                    raise ListError("pages[%d].tools[%d]" % (i, j),
                                    "tool entries are objects with a "
                                    "name", "{name, ...}")
                nm = t.get("name")
                if not isinstance(nm, str) or not nm or \
                        len(nm) > MAX_FIELD:
                    raise ListError("pages[%d].tools[%d].name" % (i, j),
                                    "non-empty string, at most %d chars"
                                    % MAX_FIELD, "string")
                page_names.append(nm)
            if raw_total + len(page_names) > MAX_TOOLS_TOTAL:
                raise ListError("pages", "pasted listings over "
                                "ceiling", "at most %d tool entries "
                                "total" % MAX_TOOLS_TOTAL)
            raw_total += len(page_names)
            if "nextCursor" in p:
                nc = p["nextCursor"]
                if nc is None:
                    state = "NULL"
                elif not isinstance(nc, str):
                    raise ListError("pages[%d].nextCursor" % i,
                                    "a cursor is a string, null, or "
                                    "absent (spec: opaque string token)",
                                    "string | null | absent")
                elif len(nc) > MAX_FIELD:
                    raise ListError("pages[%d].nextCursor" % i,
                                    "cursor over ceiling",
                                    "at most %d chars" % MAX_FIELD)
                elif nc == "":
                    state = "EMPTY"
                    value = ""
                else:
                    state = "VALUE"
                    value = nc
            else:
                state = "ABSENT"
            if not page_names:
                empty_pages += 1
            inpage = {}
            for nm in page_names:
                inpage[nm] = inpage.get(nm, 0) + 1
            for nm in sorted(inpage):
                if nm in seen:
                    dup_across += inpage[nm]
                    dup_names.add(nm)
                else:
                    seen.add(nm)
                c = inpage[nm]
                if c > 1:
                    dup_in += c - 1
                    dup_names.add(nm)
        if rt == "input_required" and interim_idx is None:
            interim_idx = i
        if err is None:
            if value is not None:
                cursor_count[value] = cursor_count.get(value, 0) + 1
            prev_cursor = value
        else:
            prev_cursor = None
        digests.append({"index": i, "tools": len(tools),
                        "cursor": state, "cursor_value": value,
                        "result_type": None if err is not None else
                        (rt if rt is not None else
                         "omitted_treated_complete"),
                        "request": req,
                        "error_code": err.get("code")
                        if isinstance(err, dict) else None,
                        "chain": "n/a" if i == 0 else
                                 ("checked" if req is not None
                                  else "unchecked")})

    lastpage = _unwrap(copy.deepcopy(pages[-1]), len(pages) - 1) \
        if _is_envelope(pages[-1]) else pages[-1]
    is_error_last = isinstance(lastpage, dict) and "error" in lastpage
    # Terminaison (règle A, verbatim : « Treat a missing nextCursor as
    # the end of results ») : ABSENT ou null = FIN ; présent, fût-il ""
    # = suite. Une page erreur n'est PAS une fin, c'est une mort du
    # scan (PARTIAL_SILENT raison ERROR_PAGE, règle 3).
    terminated = (not is_error_last) and lastpage.get("nextCursor") \
        is None
    open_cursor = None
    if not terminated and not is_error_last:
        open_cursor = lastpage.get("nextCursor")

    loop = None
    for cv in sorted(cursor_count):
        if cursor_count[cv] > 1:
            if loop is None or cursor_count[cv] > cursor_count[loop]:
                loop = cv

    classes = []
    if loop is not None:
        classes.append({"class": "CURSOR_LOOP", "cursor": loop,
                        "occurrences": cursor_count[loop],
                        "source": SOURCES["CURSOR_LOOP"]})
    if not terminated:
        if is_error_last:
            reason = "ERROR_PAGE"
            src = SOURCES["ERROR_PAGE"]
        elif lastpage.get("tools") == []:
            reason = "EMPTY_PAGE_TRAP"
            src = SOURCES["EMPTY_PAGE_TRAP"]
        elif open_cursor == "":
            reason = "EMPTY_CURSOR_TRAP"
            src = SOURCES["EMPTY_CURSOR_TRAP"]
        else:
            reason = "OPEN_CURSOR"
            src = SOURCES["PARTIAL_SILENT"]
        classes.append({"class": "PARTIAL_SILENT", "reason": reason,
                        "source": src})
    if chain_break is not None:
        classes.append({"class": "CHAIN_BREAK", "index": chain_break[0],
                        "expected": chain_break[1],
                        "got": chain_break[2],
                        "source": SOURCES["CHAIN_BREAK"]})

    unique = sorted(seen)
    declared_total = len(names) if names is not None else declared_count
    short = over = None
    missing_names = extra_names = None
    if declared_total is not None:
        if terminated:
            if len(unique) < declared_total:
                classes.append({"class": "SHORT_VS_DECLARED",
                                "gap": declared_total - len(unique),
                                "source":
                                SOURCES["SHORT_VS_DECLARED"]})
                short = declared_total - len(unique)
            elif len(unique) > declared_total:
                classes.append({"class": "OVER_VS_DECLARED",
                                "gap": len(unique) - declared_total,
                                "source": SOURCES["OVER_VS_DECLARED"]})
                over = len(unique) - declared_total
        elif len(unique) < declared_total:
            short = declared_total - len(unique)
    if names is not None:
        nset = set(names)
        missing_names = [n for n in names if n not in seen]
        extra_names = [n for n in unique if n not in nset]
    if interim_idx is not None:
        classes.append({"class": "INTERIM_LISTED", "index": interim_idx,
                        "source": SOURCES["INTERIM_LISTED"]})
    if dup_in or dup_across:
        classes.append({"class": "DUPED",
                        "in_page": dup_in,
                        "across_pages": dup_across,
                        "names": _folded(sorted(dup_names)),
                        "source": SOURCES["DUPED"]})

    sev_rank = {"CURSOR_LOOP": 0, "PARTIAL_SILENT": 1, "CHAIN_BREAK": 2,
                "SHORT_VS_DECLARED": 3, "OVER_VS_DECLARED": 4,
                "INTERIM_LISTED": 5, "DUPED": 6}
    triggered = sorted(classes, key=lambda c: sev_rank[c["class"]])
    classes.sort(key=lambda c: sev_rank[c["class"]])
    verdict = CLASS_VERDICT[triggered[0]["class"]] if triggered \
        else "COMPLETE"

    scan_complete = terminated and chain_break is None and \
        error_pages == 0 and interim_idx is None

    if loop is not None:
        resume = {"needed": False, "cursor": None, "why": "LOOP",
                  "rule": "repeated cursor rejected (PR #6937 merged "
                          "text) — following it walks the same page "
                          "forever; the fix is server-side"}
    elif scan_complete:
        resume = {"needed": False, "cursor": None,
                  "why": "SCAN_COMPLETE"}
    elif is_error_last:
        tried = None
        if len(digests) > 1:
            tried = digests[-2]["cursor_value"]
        resume = {"needed": True, "cursor": None,
                  "why": "CURSOR_REJECTED", "tried_cursor": tried,
                  "rule": "the continuation cursor DIED with -32602 "
                          "(spec §Error Handling) — restart the scan; "
                          "a rejected cursor is not resumable"}
    else:
        resume = {"needed": True, "cursor": open_cursor,
                  "why": "OPEN_CURSOR",
                  "rule": "pagination ends when nextCursor is ABSENT "
                          "(spec §Guidelines 2); an empty string is a "
                          "valid cursor and MUST NOT end results "
                          "(spec §Guidelines 3, verbatim)"}

    status = "NOT_GIVEN"
    if declared_total is not None:
        if short:
            status = "SHORT"
        elif over:
            status = "OVER"
        else:
            status = "MATCHES"

    def _dk(entry):
        return _folded(sorted(entry))

    if missing_names is not None:
        mm = _folded(missing_names) if missing_names else {"names": [],
                                                           "folded": 0}
    else:
        mm = None
    if extra_names is not None:
        xx = _folded(extra_names) if extra_names else {"names": [],
                                                       "folded": 0}
    else:
        xx = None

    return {
        "boundary": BOUNDARY,
        "classes": classes,
        "counts": {
            "chain_hops_checked": chain_checked,
            "cursors_repeated": sum(1 for c in cursor_count.values()
                                    if c > 1),
            "declared_total": declared_total,
            "duplicates_across_pages": dup_across,
            "duplicates_in_page": dup_in,
            "pages_empty_tools": empty_pages,
            "pages_error": error_pages,
            "pages_pasted": len(pages),
            "tools_missing_count": short,
            "tools_seen_raw": raw_total,
            "tools_unique": len(unique),
        },
        "declared_check": {"extra": xx, "missing": mm, "status": status},
        "pages": digests,
        "resume": resume,
        "scan_complete": scan_complete,
        "verdict": verdict,
        "verdict_rule": " > ".join(SEVERITY) +
        " (the FIRST triggered class names the verdict; all triggered "
        "classes still travel in 'classes', severity-sorted)",
    }


def _is_envelope(p):
    return isinstance(p, dict) and "result" in p and \
        ("jsonrpc" in p or "id" in p)
