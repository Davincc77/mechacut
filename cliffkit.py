# -*- coding: utf-8 -*-
"""cliffkit — /agent/result-cliff: does THIS result survive inline in
THIS harness, counted the way THAT harness counts?

Every agent harness buries tool results at its own frontier, in its
own unit, and the unit is rarely the word: Claude Code's docs and
error message say TOKENS while the cut measured across anthropics/
claude-code#97622 is 50,000 CHARACTERS, identical for latin and greek,
single- versus multi-line (measured boundary 50,000..50,500; the docs
now say it out loud: "once it's longer than 50,000 characters,
whatever its token count", "Setting MAX_MCP_OUTPUT_TOKENS doesn't
change this threshold" — code.claude.com/docs/en/mcp, re-grepped
2026-11-26). Codex counts UTF-8 bytes divided by four
(codex-rs/utils/string/src/truncate.rs, APPROX_BYTES_PER_TOKEN=4,
read 2026-11-26). Rakazo keeps a quarter of each leaf at each end
(packages/adapters/src/runtime/context/context-selection.ts, read
2026-11-26 — and the formula PUBLISHED in elie222/rakazo#2439 is
already dead code: cliffs mutate, which is why every row of this
table carries its source and its as_of).

The point is the crossing, computed in the harness's own unit —
never a token estimate the harness never used. Units that don't
convert exactly are REFUSED by name, and a harness whose threshold
is unpublished (microsoft/vscode#311068: cut observed from 14.4 KB
up, marked isTruncated=true, the resource:// hint broken — closed
2026-11-04 as work complete) answers UNPUBLISHED_THRESHOLD, not a
guessed number.

Sisters: /agent/context-tax PRICES a pasted tools/list; /agent/tool-
trim DECIDES what to disconnect under a budget; /agent/mcp-surface
FINGERPRINTS a listing; /agent/modelid AUDITS ids and their variant
suffixes. None of them predicts what a harness does to ONE result —
this kit is the crossing, the verdict, the marker text and the
survivors' shape. Never fetches; the table ships in code, sources
cited per row, as_of per row.

b121 — THE SURVIVOR SPEAKS: a JSON paste answers, per row, whether
THE HARNESS'S OWN CUT still parses. The demand is measured, not
pleaded: arXiv 2610.36114 (3,827 of 11,189 tool results cut before
the model — "every cut result became broken JSON"), and the November
2026 wave of frameworks EXECUTING cut-off JSON arguments because a
lenient repairer "fixed" them: run-llama/llama_index#24102 (2026-11-
09, parse_partial_json repairs a truncated write_file call at line 17
of 40 and FunctionAgent RUNS it), NVIDIA/NeMo-Agent-Toolkit#2550
(2026-11-03, 16 of 40 lines land on disk; the merged fix #2551
requires STRICT json.loads — "no partial parsing"), langchain4j#7169
(2026-11-18, JsonEOFException from a LENGTH reply), simonw/llm#1887
(2026-11-16), MervinPraison/PraisonAI#6369 (2026-11-14, index-
addressed stream assembly yields invalid JSON and drops
finish_reason). /json/repair and /json/bigint speak of the INTACT
document; nobody pronounced on the SURVIVANT. This field does, and
it refuses to fake it: only cuts the table can replay EXACTLY are
replayed (others answer NOT_REPLAYED with the named reason), and the
parse oracle is json.loads itself — never a guess about where JSON
breaks. A middle cut that falls wholly INSIDE one string value
produces a survivor that STILL PARSES with the marker buried in the
text — PARSEABLE_BUT_MUTATED is the dangerous class (a repaired
argument EXECUTES), and it is named as itself.
"""

import json as _json

TABLE_VERSION = "b121-1"
AS_OF = "2026-11-26"

UNITS = ("chars", "bytes", "lines", "tokens")
SURFACES = ("result", "description")

# goose law, read IN CODE (not in threads) at aaif-goose/goose — the
# repo MOVED from block/goose (API redirect confirmed 2026-11-26):
# platform_extensions/developer/shell.rs lines 161-164 (read at HEAD
# 2026-11-26): OUTPUT_LIMIT_LINES 2000, OUTPUT_LIMIT_BYTES 50_000,
# OUTPUT_PREVIEW_LINES 50, OUTPUT_PREVIEW_BYTES 10_000. The OR of
# two MIXED units is new grammar in this table; the reason cites
# LINES first when both exceed (`if exceeded_lines`). The global
# layer, agents/large_response_handler.rs (read the same day):
# DEFAULT_LARGE_TEXT_THRESHOLD = 200_000 CHARS (.chars().count()),
# knob GOOSE_MAX_TOOL_RESPONSE_SIZE (PR #9256 merged 2026-05-27,
# fixes #7027); an oversized block is REPLACED by a notice pointing
# at a KEPT file (tempfile keep(), prefix goose_mcp_response_,
# owner-only per its own test) — zero result characters survive
# inline. Write failure NAMED: the full text passes through.
GOOSE_SHELL_LINES = 2000
GOOSE_SHELL_BYTES = 50_000
GOOSE_PREVIEW_LINES = 50
GOOSE_PREVIEW_BYTES = 10_000
GOOSE_GLOBAL_CHARS = 200_000
GOOSE_TOOLS = ("shell", "extension")


class CliffError(Exception):
    """Named 400: field, message, expected — the error IS the prompt."""

    def __init__(self, field, message, expected):
        self.field = field
        self.message = message
        self.expected = expected
        super().__init__(message)


# ------------------------------------------------------------- helpers
def ceil_div(a, b):
    """Rust's (x + APPROX_BYTES_PER_TOKEN - 1) / APPROX_BYTES_PER_TOKEN
    pattern from codex-rs/utils/string/src/truncate.rs (read 2026-11-26)
    — positive integers here, floor division after the bump."""
    return (a + b - 1) // b


# ---------------------------------------------- codex own unit, in full
# plan_token_truncation (codex-rs/utils/string/src/truncate.rs, 2026-11-26):
#   max_bytes = token_limit * 4; if s.len() <= max_bytes: None (no cut)
#   split_budget: left = max_bytes / 2, right = max_bytes - left
#   marker "…{ceil_div(len - max_bytes, 4)} tokens truncated…"
CODEX_APPROX_BYTES_PER_TOKEN = 4


def codex_bytes_cliff(token_limit):
    return token_limit * CODEX_APPROX_BYTES_PER_TOKEN


def codex_removed_tokens(byte_len, max_bytes):
    return ceil_div(byte_len - max_bytes, CODEX_APPROX_BYTES_PER_TOKEN)


def codex_split_budget(max_bytes):
    left = max_bytes // 2
    return left, max_bytes - left


# ------------------------------------------- rakazo own estimator, in full
# estimateTextTokens (packages/adapters/src/runtime/context/
# context-selection.ts lines 122-148, read 2026-11-26): iterates UTF-16
# code units (text.charCodeAt), kinds: 1 lowercase, 2 uppercase,
# 3 digit, 0 else; weights: >=128 -> 0.6 if <0x0590 else 1.25; digit
# -> 1; other printable ASCII (>32,<127 non kind) -> 0.4; else 0.3;
# transition penalty +1 for lower->upper, digit->letter, letter->digit;
# total = min(ceil(sum), Buffer.byteLength(text,"utf8")).
def _utf16_units(text):
    for ch in text:
        cp = ord(ch)
        if cp >= 0x10000:
            cp -= 0x10000
            yield 0xD800 + (cp >> 10)
            yield 0xDC00 + (cp & 0x3FF)
        else:
            yield cp


def rakazo_estimate_tokens(text):
    total = 0.0
    previous = 0
    for code in _utf16_units(text):
        if 97 <= code <= 122:
            kind = 1
        elif 65 <= code <= 90:
            kind = 2
        elif 48 <= code <= 57:
            kind = 3
        else:
            kind = 0
        if code >= 128:
            total += 0.6 if code < 0x0590 else 1.25
        elif kind == 3:
            total += 1
        elif kind == 0 and 32 < code < 127:
            total += 0.4
        else:
            total += 0.3
        if ((previous == 1 and kind == 2)
                or (previous == 3 and kind in (1, 2))
                or (previous in (1, 2) and kind == 3)):
            total += 1
        previous = kind
    return min(int(total) + (1 if total > int(total) else 0),
               len(text.encode("utf-8")))


def rakazo_js_length(text):
    """JS string length: UTF-16 code units, rakazo's counting of chars."""
    return sum(1 for _ in _utf16_units(text))


# -------------------------------------------------------- hermes own cut
# truncate_head_tail (NousResearch/hermes-agent tools/
# tool_output_truncate.py, read 2026-11-26): head=int(max*0.4),
# tail=max-head, notice with thousands separators, label "MCP RESULT".
HERMES_HEAD_RATIO = 0.4
HERMES_RESULT_CAP_CHARS = 2_000_000  # mcp_tool_content.py 2026-11-26


def hermes_notice(omitted, total, label="MCP RESULT"):
    return ("\n\n... [%s TRUNCATED - %s chars omitted out of %s total] "
            "...\n\n" % (label, format(omitted, ","), format(total, ",")))


def hermes_split(max_chars):
    head = int(max_chars * HERMES_HEAD_RATIO)
    return head, max_chars - head


# --------------------------------------------------------------- table
# Each row: aliases; unit = the unit its cliff is COUNTED IN; verdicts
# are closed names; every number below was read at the cited source on
# AS_OF. A row with config=None takes its cliff as an ARGUMENT — never
# a remembered default.
def _rows():
    return {
        "claude-code": {
            "aliases": ("claude code", "claudecode", "claude",
                        "anthropic", "cc"),
            "surfaces": {
                "result": {
                    "unit": "chars", "cliff": 50000, "cmp": "gt",
                    "counted_as": ("unicode code points — measured "
                                   "identical latin/greek and single/"
                                   "multiline (#97622 replay 2026-11-25)"),
                    "verdict": "PERSIST_TO_FILE",
                    "marker": ('notice text says "exceeds maximum '
                               'allowed tokens" for a CHARACTERS cut'),
                    "message_lies": True,
                    "recoverable": ("full text saved to a file + ~2 KB "
                                    "inline preview (firecrawl-mcp-"
                                    "server#548, read 2026-11-26); the "
                                    "file is only a rescue IF the "
                                    "client can read it — sandbox-"
                                    "unreadable overflow named in the "
                                    "atlassian#17 thread"),
                    "repair": ('per-tool _meta["anthropic/'
                               'maxResultSizeChars"] in tools/list, '
                               "hard ceiling 500000 chars (v2.1.91+); "
                               "MAX_MCP_OUTPUT_TOKENS does NOT lift "
                               "the 50k chars cliff"),
                    "extra_cliffs": [
                        {"unit": "tokens", "cliff": 10000, "cmp": "gt",
                         "verdict": "INLINE_WITH_WARNING",
                         "kind": "doc"},
                        {"unit": "tokens", "cliff": 25000, "cmp": "gt",
                         "verdict": "REFUSED_BY_LIMIT",
                         "kind": "env",
                         "repair": "MAX_MCP_OUTPUT_TOKENS (default)"},
                    ],
                    "transport_guard": (
                        "BELOW the result cliffs, the TRANSPORT "
                        "decides first: an HTTP/SSE server response "
                        "over 16 MiB is STOPPED mid-read and the "
                        "request FAILS; a single WebSocket message "
                        "over 16 MiB CLOSES the connection — MAX_"
                        "MCP_OUTPUT_TOKENS moves neither guard "
                        "(code.claude.com/docs/en/mcp read "
                        "2026-11-26)"),
                    "source": ("code.claude.com/docs/en/mcp re-grepped "
                               "2026-11-26; anthropics/claude-code"
                               "#97622 open, #87650 lineage"),
                },
                "description": {
                    "unit": "chars", "cliff": 2048, "cmp": "gt",
                    "counted_as": "characters of the tool description",
                    "verdict": "HEAD_ONLY_SILENT",
                    "marker": "none — silent; /mcp UI shows the INTACT text",
                    "message_lies": True,
                    "recoverable": ("no — the LLM never sees the tail; "
                                    "the UI disagrees with the model"),
                    "repair": "none shipped — #87650 closed 2026-09-21 "
                              "as stale (locked 2026-11-21), re-read "
                              "2026-11-26: the cut lives",
                    "source": "anthropics/claude-code#87650",
                },
            },
        },
        "codex": {
            "aliases": ("codex cli", "codex-cli", "openai/codex",
                        "codex"),
            "surfaces": {
                "result": {
                    "unit": "bytes",
                    "cliff": None, "cliff_from": "token_limit",
                    "cliff_unit": "tokens",
                    "cmp": "gt",
                    "counted_as": ("UTF-8 bytes vs token_limit*4 — the "
                                   "harness's own APPROX_BYTES_PER_"
                                   "TOKEN=4, so bytes convert EXACTLY "
                                   "(never a guessed tokenizer)"),
                    "verdict": "MIDDLE_CUT_MARKED",
                    "marker": ('"…N tokens truncated…" inline; N = '
                               "ceil((bytes-4*limit)/4); kept head and "
                               "tail split at half the byte budget "
                               "each; marker OUTSIDE the budget"),
                    "message_lies": False,
                    "recoverable": ("no — #14206: 'no artifact ID, "
                                    "temp file path, or follow-up "
                                    "handle'; the cut is in place in "
                                    "the model-visible history"),
                    "repair": ("config key tool_output_token_limit "
                               "(step_settings.rs — default comes "
                               "from the PINNED MODEL and is not "
                               "published; pass it as an argument)"),
                    "ask": "token_limit",
                    "note": ("v0.56-era MCP responses cut at 10 KiB "
                             "OR 256 lines with head+tail surviving "
                             "(openai/codex#6544, closed 2026-03-08 — "
                             "historical footnote, not today's law)"),
                    "mcp_envelope": (
                        "today's MCP law lives in codex-rs/utils/"
                        "output-truncation/src/lib.rs (read "
                        "2026-11-26): a serialized CallToolResult "
                        "over max_bytes is RE-ENVELOPED — a plain "
                        "text result loses its JSON envelope and "
                        "starts with the literal \"Truncated tool "
                        "output:\"; structured_content is DROPPED; "
                        "the preview is middle-cut in BYTES (\"…N "
                        "chars truncated…\") and its own JSON "
                        "ESCAPING re-inflates it, so the budget is "
                        "SCALED DOWN and re-cut until the envelope "
                        "fits — the text inside the result is a cut "
                        "of a re-escape of a cut"),
                    "source": ("codex-rs/utils/string/src/truncate.rs "
                               "+ utils/output-truncation/src/lib.rs + "
                               "session/step_settings.rs read "
                               "2026-11-26; openai/codex#14206 open"),
                },
            },
        },
        "bionic": {
            "aliases": ("lm studio", "lmstudio", "lm-studio", "bionic"),
            "surfaces": {
                "result": {
                    "unit": "chars", "cliff": 50000, "cmp": "gt",
                    "counted_as": "characters of the text result",
                    "verdict": "HEAD_ONLY_MARKED",
                    "marker": '"... (truncated)" appended',
                    "message_lies": False,
                    "recoverable": ("no continuation mechanism — #2338 "
                                    "open; the surviving prefix is "
                                    "byte-identical to the original, "
                                    "so it is NOT the server cutting"),
                    "repair": "none named (ticket open 2026-11-26)",
                    "source": ("lmstudio-ai/lmstudio-bug-tracker#2338 "
                               "body re-read 2026-11-26"),
                },
            },
        },
        "vscode": {
            "aliases": ("vs code", "vscode", "copilot",
                        "github copilot", "vscode copilot"),
            "surfaces": {
                "result": {
                    "unit": "bytes",
                    "cliff": None, "cliff_kind": "unpublished",
                    "counted_as": ("bytes reported in the thread "
                                   "(50 KB-999 KB cut, community "
                                   "reports from 14.4 KB) — NO "
                                   "published threshold"),
                    "verdict": "UNPUBLISHED_THRESHOLD",
                    "marker": ("isTruncated=true flag on the result; "
                               "the vscode-chat-response-resource:// "
                               "hint did NOT resolve (#311068)"),
                    "message_lies": False,
                    "recoverable": ("flagged but the follow-up handle "
                                    "was broken; issue closed with "
                                    "the work reported done "
                                    "(updated 2026-10-26)"),
                    "repair": ("no size knob published — the honest "
                               "answer is: this harness cuts at an "
                               "UNPUBLISHED point and flags it"),
                    "band": (14400, 1_000_000),
                    "source": ("microsoft/vscode#311068 body re-read "
                               "2026-11-26"),
                },
            },
        },
        "rakazo": {
            "aliases": ("rakazo",),
            "surfaces": {
                "result": {
                    "unit": "chars",
                    "cliff": None, "cliff_from": "budget", "cmp": "gt",
                    "counted_as": ("JS string length (UTF-16 units) "
                                   "of the serialized result vs the "
                                   "session budget — no constant: "
                                   "the cut fits YOUR budget"),
                    "verdict": "LEAF_MIDDLE_CUT_FLAGGED",
                    "marker": ("longest leaf first, kept "
                               "max(8, floor(len/4)) at EACH end "
                               "(fallback floor((len-marker)/4)), "
                               "iterative; payload carries "
                               "contextTruncated=true — the flag "
                               "lives INSIDE the result"),
                    "message_lies": False,
                    "recoverable": "no — the middle is replaced in place",
                    "repair": ("the published #2439 formula max(128, "
                               "min(len/2, available/4)) is DEAD CODE "
                               "at HEAD (file moved to runtime/"
                               "context/, per-leaf rules above) — a "
                               "cliff read from memory one month old "
                               "is WRONG; this is why every row is "
                               "as_of dated"),
                    "ask": "budget",
                    "source": ("packages/adapters/src/runtime/context/"
                               "context-selection.ts read 2026-11-26; "
                               "elie222/rakazo#2439 closed 2026-11-01"),
                },
            },
        },
        "hermes-agent": {
            "aliases": ("hermes", "hermes-agent", "hermes agent"),
            "surfaces": {
                "result": {
                    "unit": "chars", "cliff": HERMES_RESULT_CAP_CHARS,
                    "cmp": "gt",
                    "counted_as": "python characters (code points)",
                    "verdict": "HEAD_TAIL_MARKED",
                    "marker": ('"\\n\\n... [MCP RESULT TRUNCATED - '
                               "N chars omitted out of M total] ...\\n"
                               '\\n" — head 40% tail 60%, counts in '
                               "the notice"),
                    "message_lies": False,
                    "recoverable": ("by design the cap sits AFTER the "
                                    "spillover layer (source comment: "
                                    "a 50K cap 'would truncate before "
                                    "spillover could preserve the "
                                    "data')"),
                    "repair": ("resource/media blocks: 50 MiB cap "
                               "rejected BEFORE decoding, named "
                               "'too large to cache'"),
                    "source": ("NousResearch/hermes-agent tools/"
                               "tool_output_truncate.py + tools/"
                               "mcp_tool_content.py read 2026-11-26; "
                               "#129369 closed 2026-10-24"),
                },
            },
        },
        "onyx": {
            "aliases": ("onyx", "onyx-dot-app", "onyx app"),
            "surfaces": {
                "result": {
                    "unit": "tokens",
                    "cliff": None, "cliff_from": "context_room",
                    "cmp": "gt",
                    "counted_as": ("the harness cuts NOTHING — "
                                   "run_llm_loop appends "
                                   "llm_facing_response VERBATIM; "
                                   "the cliff is YOUR model window "
                                   "and the provider's own token "
                                   "count (onyx-dot-app/onyx#11007, "
                                   "body re-read at source "
                                   "2026-11-26)"),
                    "verdict": "PROVIDER_REQUEST_REJECTED",
                    "marker": ("none — nothing is cut: the WHOLE "
                               "request dies with a provider error; "
                               "the '[TRUNCATED: ...]' notice lives "
                               "only in the PROPOSED fix"),
                    "message_lies": False,
                    "recoverable": ("no — dead request, dead turn; "
                                    "#16312 (marked dup 2026-11-20): "
                                    "'Required: 2032226, Available: "
                                    "843719' hit BEFORE any tool "
                                    "even ran — the tool DEFINITIONS "
                                    "alone ate the budget"),
                    "repair": ("MAX_TOOL_RESULT_TOKENS default "
                               "20 000 + notice is PROPOSED, NOT "
                               "DEPLOYED: issue #11007 open since "
                               "2026-05-12, PR #14586 still open "
                               "(unmerged, re-read 2026-11-26); "
                               "#15119 and #16312 were closed INTO "
                               "this issue 2026-11-20 — the pain "
                               "REPORTS, it does not repair; until "
                               "it ships the only real lever is your "
                               "own room: pass context_room"),
                    "ask": "context_room",
                    "source": ("onyx-dot-app/onyx#11007 body + "
                               "duplicate marks read at source "
                               "2026-11-26; #15119 (564-chunk merged "
                               "RAG sections), #16312, PR #14586"),
                },
            },
        },
        "goose": {
            "aliases": ("goose", "aaif-goose", "block/goose",
                        "goose cli", "goose-cli"),
            "surfaces": {
                "result": {
                    "unit": "chars", "cliff": GOOSE_GLOBAL_CHARS,
                    "cmp": "gt",
                    "counted_as": ("the GLOBAL handler counts Rust "
                                   ".chars() = Unicode scalars = "
                                   "python code points exactly "
                                   "(large_response_handler.rs read "
                                   "2026-11-26); the developer "
                                   "shell cuts EARLIER in LINES "
                                   "OR BYTES — see shell_law"),
                    "verdict": "REPLACE_WITH_NOTICE",
                    "marker": ('"The response returned from the '
                               "tool call was larger (N characters)"
                               " and is stored in the file which "
                               "you can use other tools to examine "
                               'or search in: {path}" — the block '
                               "is REPLACED: ZERO result "
                               "characters survive inline; the "
                               "shell notice instead: "
                               '"[Output exceeded 2000 line limit '
                               "(N lines total). Full output saved "
                               "to {path}. Read it with shell "
                               "commands like `head`, `tail`, or "
                               "`sed -n \'100,200p\'` up to 2000 "
                               'lines at a time.]"'),
                    "message_lies": False,
                    "recoverable": ("usually — the large-response "
                                    "file is KEPT (tempfile keep(), "
                                    "prefix goose_mcp_response_, "
                                    "owner-only per its own test); "
                                    "but a shell preview's file "
                                    "lives in ShellTool's PRIVATE "
                                    "TempDir (dies with the tool "
                                    "instance), and goose#13817 "
                                    "(open 2026-11-25) shows a "
                                    "session truncate can delete "
                                    "the compaction summary the "
                                    "notice rides in — the rescue "
                                    "path itself can be orphaned"),
                    "repair": ("GOOSE_MAX_TOOL_RESPONSE_SIZE (PR "
                               "#9256 merged 2026-05-27, fixes "
                               "#7027); the default 200000 chars "
                               "is PUBLISHED in code "
                               "(DEFAULT_LARGE_TEXT_THRESHOLD) — "
                               "declare max_response_size if YOUR "
                               "config sets another"),
                    "source": ("aaif-goose/goose (repo MOVED from "
                               "block/goose — API redirect read "
                               "2026-11-26) crates/goose/src/agents"
                               "/large_response_handler.rs + "
                               "agents/platform_extensions/"
                               "developer/shell.rs read at HEAD "
                               "2026-11-26; #7025 closed "
                               "2026-05-14, #9256 merged "
                               "2026-05-27, #13817 open 2026-11-25"),
                },
            },
        },
    }


HARNESSES = _rows()

FIRECRAWL_NOTE = ("firecrawl-mcp-server#548 (open 2026-10-16, read "
                  "2026-11-26) is NOT a separate cutter: the 2 KB "
                  "preview is Claude Code's own post-persist inline — "
                  "it rides the claude-code recoverable field.")

ALL_ORDER = ("claude-code", "codex", "bionic", "vscode", "rakazo",
             "hermes-agent", "onyx", "goose")


def resolve_harness(name):
    q = str(name).strip().lower()
    if q in HARNESSES:
        return q
    for h, row in HARNESSES.items():
        if q in row["aliases"]:
            return h
    raise CliffError(
        "harness",
        "unknown harness '%s' — the table is closed" % name,
        "one of %s (aliases %s)" % (
            "|".join(ALL_ORDER),
            "|".join(sorted({a for r in HARNESSES.values()
                             for a in r["aliases"]}))))


def _measure(text):
    return {"chars": len(text),
            "bytes": len(text.encode("utf-8")),
            "lines": text.count("\n") + 1,
            "utf16_chars": rakazo_js_length(text)}


def _declared_size(size, unit):
    try:
        n = int(size)
    except (TypeError, ValueError):
        raise CliffError("size", "size must be an integer", "int")
    if n < 0:
        raise CliffError("size", "size is a count, not a debt", ">= 0")
    if unit not in UNITS:
        raise CliffError("unit", "unknown unit '%s'" % unit,
                         "|".join(UNITS))
    return n


def _native_n(row, m, unit, size):
    """Return the size expressed in the row's native counting unit.
    None -> cannot convert (refuse). This is where 'computed in the
    harness's own unit, never a guess' lives."""
    if unit is not None:
        # declared mode: exact match, plus the two unit functions the
        # HARNESS ITSELF publishes (codex counts bytes; JS harnesses
        # count UTF-16 units).
        if row["unit"] == unit:
            return size
        if unit == "tokens" and row["unit"] == "bytes":
            # codex counts bytes = 4*token_limit — EXACT inversion
            # through its own function, not a guess.
            return size * CODEX_APPROX_BYTES_PER_TOKEN
        if unit == "chars" and row.get("counted_as", "").startswith(
                "JS string length"):
            return size  # JS chars ARE the unit for rakazo
        return None
    # paste mode: measure in the native unit
    if row["unit"] == "chars":
        if row.get("counted_as", "").startswith("JS string length"):
            return m["utf16_chars"]
        return m["chars"]
    return m[row["unit"]]


def _ask(row, key):
    raise CliffError(
        key,
        "the %s cliff is CONFIG-BOUNDED, not constant — refusing to "
        "guess it" % row.get("_harness", "harness"),
        "pass %s (the harness reads it from your config/model; "
        "nothing in this table pretends to know YOUR value)" % key)


def _goose_survivors(text):
    """Exact replay of shell.rs truncate_output + truncate_preview_bytes
    (read at HEAD 2026-11-26): last 50 lines joined by \\n, then a
    byte-tail of 10 000 snapped FORWARD to the next char boundary."""
    parts = text.split("\n")
    ps = max(0, len(parts) - GOOSE_PREVIEW_LINES)
    tail = parts[ps:]
    joined = "\n".join(tail)
    jb = joined.encode("utf-8")
    cut = len(jb) > GOOSE_PREVIEW_BYTES
    snap = False
    if cut:
        start = len(jb) - GOOSE_PREVIEW_BYTES
        while start < len(jb) and 0x80 <= jb[start] < 0xC0:
            start += 1
            snap = True
        keep = jb[start:]
    else:
        keep = jb
    ks = keep.decode("utf-8")
    return {"survivor_lines": ks.count("\n") + 1,
            "survivor_bytes": len(keep),
            "survivor_chars": len(ks),
            "dropped_head_lines": len(parts) - len(tail),
            "preview_line_cut_applied": cut,
            "boundary_snap_applied": snap}


def _goose_judge(out, surf, m, unit, size, args, text):
    # The goose row is TWO clauses in one harness: the developer
    # shell law (lines OR bytes, mixed units — new grammar in this
    # table) and the agent-wide char handler. tool=shell (default)
    # judges the clause that bites FIRST; tool=extension judges only
    # the global one. A declared mode NEVER guesses: the UTF-8
    # inequalities the harness itself relies on (bytes >= chars,
    # chars >= ceil(bytes/4)) DECIDE when they can, and the row
    # names INDETERMINATE_NEEDS_PASTE when they cannot.
    tq = args.get("tool")
    if tq is None:
        tq = "shell"
    else:
        raw = str(tq).strip().lower()
        if raw in ("shell", "developer", "developer-shell",
                   "dev-shell"):
            tq = "shell"
        elif raw in ("extension", "ext", "mcp"):
            tq = "extension"
        else:
            raise CliffError(
                "tool",
                "unknown goose tool '%s' — the law is two-layered, "
                "name the layer" % tq,
                "shell|extension (developer-shell and mcp alias)")
    gcliff = GOOSE_GLOBAL_CHARS
    gsize = args.get("max_response_size")
    if gsize is not None:
        gcliff = _declared_size(gsize, "chars")
    out["cliff"] = gcliff
    out["tool"] = tq

    g = {"unit": "chars", "cliff": gcliff, "crossed": None,
         "margin": None, "verdict": None, "by_bound": None}
    exact = m["chars"] if m is not None else (
        size if unit == "chars" else None)
    if exact is not None:
        g["margin"] = gcliff - exact
        g["crossed"] = exact > gcliff
    elif unit == "bytes":
        if size <= gcliff:
            g["crossed"] = False   # chars <= bytes: impossible to
            g["by_bound"] = "chars<=bytes"  # cross, PROVEN
        elif (size + 3) // 4 > gcliff:
            g["crossed"] = True
            g["by_bound"] = "chars>=bytes/4"
    elif unit == "lines":
        if size - 1 > gcliff:
            g["crossed"] = True
            g["by_bound"] = "chars>=lines-1"
    elif unit == "tokens":
        raise CliffError(
            "unit",
            "goose counts CHARS (global) and BYTES+LINES (shell) — "
            "'tokens' would need a tokenizer goose never published",
            "unit chars|bytes|lines, or paste the result and the "
            "kit counts it the way goose does")
    g["verdict"] = ("INDETERMINATE_NEEDS_PASTE" if g["crossed"] is
                    None else ("REPLACE_WITH_NOTICE" if g["crossed"]
                               else "INLINE"))
    out["global"] = g

    law = {"applies": tq == "shell", "verdict": None,
           "crossed": None, "triggered_by": None,
           "cliffs": {"lines": GOOSE_SHELL_LINES,
                      "bytes": GOOSE_SHELL_BYTES},
           "preview": {"lines": GOOSE_PREVIEW_LINES,
                       "bytes": GOOSE_PREVIEW_BYTES,
                       "shape": ("last 50 lines joined, then "
                                 "TAIL-capped at 10000 bytes "
                                 "snapped forward to a char "
                                 "boundary — the head is dropped "
                                 "TWICE (lines, then bytes)")},
           "temp_file": ("full output written to ShellTool's PRIVATE "
                         "TempDir — dies with the tool instance; "
                         "the global handler's goose_mcp_response_ "
                         "file is KEPT (owner-only) — different "
                         "rescues, read at source 2026-11-26")}
    if not law["applies"]:
        law["status"] = "NOT_APPLIED"
        law["verdict"] = "NOT_APPLIED"
    elif m is not None:
        over_l = m["lines"] > GOOSE_SHELL_LINES
        over_b = m["bytes"] > GOOSE_SHELL_BYTES
        law["crossed"] = over_l or over_b
        law["status"] = "EXACT_PASTE"
        if law["crossed"]:
            law["verdict"] = "TEMP_FILE_TAIL_ONLY"
            law["triggered_by"] = "lines" if over_l else "bytes"
            law["reason_rendered"] = (
                "Output exceeded %d line limit (%d lines total)."
                % (GOOSE_SHELL_LINES, m["lines"]) if over_l else
                "Output exceeded %d byte limit (%d bytes total)."
                % (GOOSE_SHELL_BYTES, m["bytes"]))
            law.update(_goose_survivors(text))
            law["dropped_bytes"] = m["bytes"] - law["survivor_bytes"]
        else:
            law["verdict"] = "INLINE"
            law.update(_goose_survivors(text))
    else:
        law["status"] = "DECLARED"
        if unit == "chars":
            if size > GOOSE_SHELL_BYTES:
                law["crossed"] = True   # bytes >= chars > 50000 —
                law["by_bound"] = "bytes>=chars"   # PROVEN blind
                law["verdict"] = "TEMP_FILE_TAIL_ONLY"
                law["triggered_by"] = "bytes"
            else:
                law["crossed"] = None
                law["status"] = ("INDETERMINATE_NEEDS_PASTE"
                                 if not (size > GOOSE_SHELL_BYTES)
                                 else "CROSSED")
                law["verdict"] = law["status"]
        elif unit == "bytes":
            law["crossed"] = (size > GOOSE_SHELL_BYTES
                              if size > GOOSE_SHELL_BYTES else None)
            if size > GOOSE_SHELL_BYTES:
                law["verdict"] = "TEMP_FILE_TAIL_ONLY"
                law["triggered_by"] = "bytes"
            else:
                law["crossed"] = None
                law["verdict"] = law["status"] = (
                    "INDETERMINATE_NEEDS_PASTE")
        elif unit == "lines":
            if size > GOOSE_SHELL_LINES:
                law["crossed"] = True
                law["verdict"] = "TEMP_FILE_TAIL_ONLY"
                law["triggered_by"] = "lines"
            else:
                law["crossed"] = None
                law["verdict"] = law["status"] = (
                    "INDETERMINATE_NEEDS_PASTE")
        law.setdefault("verdict", "INDETERMINATE_NEEDS_PASTE")
        law["crossed"] = bool(law["verdict"] == "TEMP_FILE_TAIL_ONLY") \
            if law["verdict"] == "TEMP_FILE_TAIL_ONLY" else \
            law.get("crossed")
    out["shell_law"] = law

    if law["applies"] and law["crossed"] is True:
        out["verdict"] = "TEMP_FILE_TAIL_ONLY"
        out["crossed"] = True
        out["operative"] = ("shell_law — the clause bites FIRST: a "
                            "developer-shell block never reaches the "
                            "200000-char handler inline")
    elif g["crossed"] is True:
        out["verdict"] = "REPLACE_WITH_NOTICE"
        out["crossed"] = True
        out["operative"] = "global_handler"
    elif ((law["applies"] and law["crossed"] is None)
          or g["crossed"] is None):
        out["verdict"] = "INDETERMINATE_NEEDS_PASTE"
        out["crossed"] = None
        out["operative"] = ("undecided — the declared count does not "
                            "cross any published bound; paste the "
                            "result or declare the other unit")
    else:
        out["verdict"] = "INLINE"
        out["crossed"] = False
        out["operative"] = ("none — both clauses hold at the "
                            "published numbers")
    out["margin"] = g["margin"]
    out["unit"] = surf["unit"]
    return out


def out_goose_stub(name, surface, surf):
    """Same base fields as _row_verdict builds for every row — the
    goose judge then fills verdict/crossed/margin from TWO clauses."""
    return {"harness": name, "surface": surface,
            "unit": surf["unit"],
            "counted_as": surf["counted_as"],
            "verdict": None, "crossed": None, "margin": None,
            "message_lies": surf["message_lies"],
            "marker": surf["marker"],
            "recoverable": surf["recoverable"],
            "repair": surf["repair"],
            "source": surf["source"], "as_of": AS_OF}


# ------------------------------------------- b121: the survivor PARSES?
_WS = " \t\n\r"


def _json_token_spans(text):
    """RFC 8259 closed grammar over a document that ALREADY passed
    _json.loads: returns [(lo, hi, kind, path)] for EVERY token, in
    order. kind: struct | key | string_value | number | literal.
    path is the member path the token sits at ('$' for structural
    tokens between members), keys RAW (display only). The document is
    valid by contract, so this walk never raises and never guesses."""
    spans = []
    pos = [0]
    n = len(text)

    def skip_ws():
        while pos[0] < n and text[pos[0]] in _WS:
            pos[0] += 1

    def scan_string():
        j = pos[0] + 1
        while True:
            ch = text[j]
            if ch == "\\":
                j += 2
                continue
            if ch == '"':
                return j + 1
            j += 1

    def scan_atom():
        j = pos[0]
        while j < n and text[j] not in " \t\n\r,}]":
            j += 1
        return j

    def parse_arr(path):
        lo = pos[0]
        spans.append((lo, lo + 1, "struct", path))
        pos[0] += 1
        skip_ws()
        if pos[0] < n and text[pos[0]] == "]":
            cl = pos[0]
            spans.append((cl, cl + 1, "struct", path))
            pos[0] += 1
            return
        idx = 0
        while True:
            parse_value(path + "[%d]" % idx)
            skip_ws()
            if pos[0] < n and text[pos[0]] == ",":
                cm = pos[0]
                spans.append((cm, cm + 1, "struct", path + "[%d]" % idx))
                pos[0] += 1
                skip_ws()
                idx += 1
                continue
            break
        cl = pos[0]
        spans.append((cl, cl + 1, "struct", path))
        pos[0] += 1

    def parse_obj(path):
        lo = pos[0]
        spans.append((lo, lo + 1, "struct", path))
        pos[0] += 1
        skip_ws()
        if pos[0] < n and text[pos[0]] == "}":
            cl = pos[0]
            spans.append((cl, cl + 1, "struct", path))
            pos[0] += 1
            return
        while True:
            key_lo = pos[0]
            key_hi = scan_string()
            key = text[key_lo + 1:key_hi - 1]
            member = path + "." + key
            spans.append((key_lo, key_hi, "key", member))
            pos[0] = key_hi
            skip_ws()
            col = pos[0]
            spans.append((col, col + 1, "struct", member))
            pos[0] += 1
            parse_value(member)
            skip_ws()
            if pos[0] < n and text[pos[0]] == ",":
                cm = pos[0]
                spans.append((cm, cm + 1, "struct", member))
                pos[0] += 1
                skip_ws()
                continue
            break
        cl = pos[0]
        spans.append((cl, cl + 1, "struct", path))
        pos[0] += 1

    def parse_value(path):
        skip_ws()
        lo = pos[0]
        c = text[lo]
        if c == "{":
            parse_obj(path)
            return
        if c == "[":
            parse_arr(path)
            return
        if c == '"':
            hi = scan_string()
            spans.append((lo, hi, "string_value", path))
            pos[0] = hi
            return
        hi = scan_atom()
        spans.append((lo, hi,
                      "number" if c in "-0123456789" else "literal",
                      path))
        pos[0] = hi

    skip_ws()
    parse_value("$")
    return spans


def _guilty_at(spans, lo, hi):
    """What the deleted span [lo, hi) touched: the node the cut BEGINS
    inside (token containing lo), the node it ENDS inside (token
    containing hi-1 — the last character that died), and whether both
    are the SAME string value (the PARSEABLE_BUT_MUTATED condition:
    the marker fell wholly inside one string, so the survivor still
    parses while the value lies)."""
    begin = None
    end = None
    last = max(hi - 1, lo)
    for s_lo, s_hi, kind, path in spans:
        if begin is None and s_lo <= lo < s_hi:
            begin = (kind, path)
        if s_lo <= last < s_hi:
            end = (kind, path)
    if begin is None:
        begin = ("structure", "$")
    if end is None:
        end = ("structure", "$")
    return {"begin": {"kind": begin[0], "path": begin[1]},
            "end": {"kind": end[0], "path": end[1]},
            "same_string": bool(begin == end and begin[0] ==
                                "string_value")}


def _goose_tail_text(text):
    """The shell-law survivor STRING, byte-exact with _goose_survivors
    (last 50 lines, tail-capped at 10 000 bytes snapped forward)."""
    parts = text.split("\n")
    ps = max(0, len(parts) - GOOSE_PREVIEW_LINES)
    joined = "\n".join(parts[ps:])
    jb = joined.encode("utf-8")
    if len(jb) > GOOSE_PREVIEW_BYTES:
        start = len(jb) - GOOSE_PREVIEW_BYTES
        while start < len(jb) and 0x80 <= jb[start] < 0xC0:
            start += 1
        return ps, jb[start:].decode("utf-8")
    return ps, joined


def _survivor_replay(name, out, text):
    """(survivor, lo, hi, marker) with EXACT replay of the row's own
    law, or None when this row's cut is not replayable honestly. lo/hi
    are the deleted span in CHARACTERS of the original paste."""
    v = out.get("verdict")
    if v == "INLINE":
        return None
    if name == "rakazo":
        return None  # LEAF_MIDDLE_CUT_FLAGGED — the fold is per-leaf,
        # longest leaf first: not a head/tail of the paste. Replaying
        # it would invent a survivor the harness may not produce.
    if name == "vscode":
        return None  # UNPUBLISHED_THRESHOLD — a band is not a cut.
    if name == "onyx":
        return None  # PROVIDER_REQUEST_REJECTED — nothing is cut.
    if name == "claude-code" and v == "PERSIST_TO_FILE":
        return None  # zero of the RESULT survives inline; a ~2 KB
    # preview clause is approximate ("~"), and this kit never replays
    # an approximation. The FILE holds the intact bytes.
    if name == "goose":
        if v == "REPLACE_WITH_NOTICE":
            return None  # global handler: the block is REPLACED.
        law = out.get("shell_law") or {}
        if law.get("verdict") == "TEMP_FILE_TAIL_ONLY":
            _ps, tail = _goose_tail_text(text)
            end = len(text) - len(tail)
            return tail, 0, end, ""  # the HEAD is what died
        return None
    if name == "codex" and v == "MIDDLE_CUT_MARKED":
        b = text.encode("utf-8")
        head = out.get("kept_head_bytes")
        tail = out.get("kept_tail_bytes")
        marker = out.get("marker_rendered") or ""
        if head is None or tail is None:
            return None
        h = min(head, len(b))
        while h > 0 and 0x80 <= b[h] < 0xC0:
            h -= 1  # floor_char_boundary (truncate.rs split_string)
        t = max(len(b) - tail, h)
        while t < len(b) and 0x80 <= b[t] < 0xC0:
            t += 1  # suffix starts at the first char AT/after target
        pre = b[:h].decode("utf-8")
        suf = b[t:].decode("utf-8")
        return (pre + marker + suf, len(pre), len(text) - len(suf),
                marker)
    if name == "bionic" and v == "HEAD_ONLY_MARKED":
        cliff = out.get("cliff")
        if cliff is None:
            return None
        marker = "... (truncated)"
        return text[:cliff] + marker, cliff, len(text), marker
    if name == "hermes-agent" and v == "HEAD_TAIL_MARKED":
        head, tail = hermes_split(out.get("cliff") or 0)
        marker = out.get("marker_rendered") or ""
        if tail > len(text) - head:
            return None
        return (text[:head] + marker + text[len(text) - tail:],
                head, len(text) - tail, marker)
    return None


_NOT_REPLAYED_WHY = {
    "rakazo": ("LEAF_MIDDLE_CUT_FLAGGED — rakazo folds the LONGEST "
               "leaf first (max(8, floor(len/4)) per end), not the "
               "document: a head/tail replay would invent a survivor. "
               "The fold replaces a string middle IN PLACE, so the "
               "document still PARSES while a string value is "
               "SILENTLY MUTATED — ask the kit for the rows it can "
               "replay exactly"),
    "vscode": ("UNPUBLISHED_THRESHOLD — the cut lives inside a band "
               "(14.4 KB–999 KB reported, #311068); replaying would "
               "invent the harness's number"),
    "onyx": ("PROVIDER_REQUEST_REJECTED — onyx cuts NOTHING: the "
             "paste survives VERBATIM, it is the whole PROVIDER "
             "request that dies; no local cut to replay"),
    "claude-code": ("PERSIST_TO_FILE — zero of the result survives "
                    "inline (the notice replaces it; the ~2 KB "
                    "preview clause is approximate and this kit "
                    "never replays '~'): the JSON is INTACT IN THE "
                    "NAMED FILE, unreadable inline"),
    "goose": ("the global handler REPLACES the block with a notice — "
              "zero result characters survive inline (shell.rs's "
              "tail-only clause answers separately under shell_law)"),
}


def _json_survival(name, out, text):
    """The b121 field: does THIS harness's OWN cut on THIS pasted
    document still PARSE? The oracle is _json.loads itself. Declared
    mode has no text and NO field — the kit never pronounces on bytes
    it has not seen."""
    try:
        _json.loads(text)
    except ValueError:
        return {"input": "NOT_JSON",
                "verdict": "NOT_REPLAYED",
                "why": "the paste is not a JSON document — nothing "
                       "about a cut's JSON survival can be judged "
                       "from bytes that never parsed"}
    v = out.get("verdict")
    if v == "INLINE":
        return {"input": "JSON", "verdict": "INTACT", "cut": False,
                "why": "no cut at this size in this harness — the "
                       "document reaches the model whole"}
    if v in ("REFUSED_IN_PASTE", "UNPUBLISHED_THRESHOLD",
             "REFUSED_NEEDS_ARGUMENT"):
        why = (_NOT_REPLAYED_WHY.get(name)
               or "the row refuses a paste-counted cut — no local "
                  "replay without the harness's own argument")
        if v == "REFUSED_NEEDS_ARGUMENT" and name not in \
                _NOT_REPLAYED_WHY:
            why = ("the row needs %s to place its cliff — declare it "
                   "and the kit replays" % out.get("ask"))
        if isinstance(why, tuple):
            why = why[0]
        return {"input": "JSON", "verdict": "NOT_REPLAYED", "why": why}
    if name == "goose" and v == "REPLACE_WITH_NOTICE":
        return {"input": "JSON", "verdict": "NO_CONTENT_SURVIVES",
                "rescue": "the notice points at a goose_mcp_response_ "
                          "file the harness KEEPS (owner-only, read "
                          "at source): the intact bytes live there, "
                          "inline NOTHING of the result survives",
                "why": _NOT_REPLAYED_WHY["goose"]}
    if name == "claude-code" and v == "PERSIST_TO_FILE":
        return {"input": "JSON", "verdict": "NO_CONTENT_SURVIVES",
                "rescue": "the full text is saved to the file the "
                          "notice NAMES — read it back and it "
                          "parses",
                "why": _NOT_REPLAYED_WHY["claude-code"]}
    replayed = _survivor_replay(name, out, text)
    if replayed is None:
        why = _NOT_REPLAYED_WHY.get(name) or (
            "no exact replay of this row's cut shape exists in the "
            "table — the kit says NOT_REPLAYED rather than invent a "
            "survivor")
        if isinstance(why, tuple):
            why = why[0]
        return {"input": "JSON", "verdict": "NOT_REPLAYED", "why": why}
    survivor, lo, hi, marker = replayed
    doc0 = _json.loads(text)
    try:
        got = _json.loads(survivor)
    except _json.JSONDecodeError as e:
        return {"input": "JSON", "verdict": "BROKEN",
                "cut": [lo, hi],
                "guilty": _guilty_at(_json_token_spans(text), lo, hi),
                "survivor_error": "%s: line %d column %d (char %d)"
                                  % (e.msg, e.lineno, e.colno,
                                     e.pos),
                "marker_rendered": marker}
    if got == doc0:
        return {"input": "JSON", "verdict": "INTACT",
                "cut": [lo, hi],
                "why": "the deleted span was empty — the survivor is "
                       "the document itself"}
    return {"input": "JSON", "verdict": "PARSEABLE_BUT_MUTATED",
            "cut": [lo, hi],
            "guilty": _guilty_at(_json_token_spans(text), lo, hi),
            "marker_rendered": marker,
            "why": "the survivor PARSES — and the marker sits INSIDE "
                   "the value: a repaired argument would EXECUTE the "
                   "lie (llama_index#24102 class)"}


def _row_verdict(name, row, surface, m, unit, size, args, text=None):
    surf = row["surfaces"][surface]
    if name == "goose":
        return _goose_judge(out_goose_stub(name, surface, surf),
                            surf, m, unit, size, args, text)
    out = {"harness": name, "surface": surface,
           "unit": surf["unit"],
           "counted_as": surf["counted_as"],
           "verdict": None, "crossed": None, "margin": None,
           "message_lies": surf["message_lies"],
           "marker": surf["marker"],
           "recoverable": surf["recoverable"],
           "repair": surf["repair"],
           "source": surf["source"], "as_of": AS_OF}
    for extra in ("transport_guard", "mcp_envelope"):
        if extra in surf:
            out[extra] = surf[extra]
    if m is not None and surf["unit"] == "tokens":
        # A PASTE cannot be counted in tokens without the provider's
        # OWN tokenizer — the kit refuses the guess, and it refuses
        # hardest for the harness that cuts nothing at all: there is
        # no local cut to replay here, only a budget to declare.
        out["verdict"] = "REFUSED_IN_PASTE"
        out["ask"] = surf["ask"]
        out["reason"] = ("onyx counts in the provider's tokens — no "
                         "paste can be counted without that "
                         "tokenizer, and nothing local was cut; "
                         "declare size+unit=tokens AND context_room "
                         "instead")
        return out
    cliff = surf["cliff"]
    if cliff is None:
        if surf.get("cliff_kind") == "unpublished":
            out["verdict"] = "UNPUBLISHED_THRESHOLD"
            out["cliff"] = None
            if "band" in surf:
                out["band_bytes"] = list(surf["band"])
            if m is not None:
                n = _native_n(surf, m, unit, size)
                out["measured"] = n
                out["indeterminate"] = ("no published threshold to "
                                        "cross — the flag "
                                        "isTruncated is the contract")
            return out
        ask = surf["ask"]
        given = args.get(ask)
        if given is None:
            row["_harness"] = name
            out["verdict"] = "REFUSED_NEEDS_ARGUMENT"
            out["ask"] = ask
            out["reason"] = surf["repair"]
            return out
        cu = surf.get("cliff_unit", surf["unit"])
        raw = _declared_size(given, cu)
        # the config key speaks tokens; the cut counts bytes — the
        # harness's OWN conversion (truncate.rs: max_bytes =
        # tokens * APPROX_BYTES_PER_TOKEN), not an estimate.
        cliff = (codex_bytes_cliff(raw)
                 if cu == "tokens" and surf["unit"] == "bytes"
                 else raw)
        out["cliff"] = cliff
    else:
        out["cliff"] = cliff

    n = _native_n(surf, m, unit, size)
    if n is None:
        raise CliffError(
            "unit",
            "%s counts in %s — declared '%s' would need a guessed "
            "conversion; REFUSED" % (name, surf["unit"], unit),
            "declare unit=%s (or paste the result and the kit counts "
            "it EXACTLY the way %s does)" % (surf["unit"], name))
    out["input_in_native_unit"] = n
    out["margin"] = cliff - n
    out["crossed"] = n > cliff
    if not out["crossed"]:
        out["verdict"] = "INLINE"
        # the doc cliffs under the persist cliff still bite the
        # WARNING surface — carry them as named extras:
        if "extra_cliffs" in surf and m is not None:
            out["also"] = _claude_token_notes(surf, m)
        return out
    out["verdict"] = surf["verdict"]
    if name == "codex":
        removed = codex_removed_tokens(n, cliff)
        head, tail = codex_split_budget(cliff)
        out["marker_rendered"] = "…%d tokens truncated…" % removed
        out["kept_head_bytes"], out["kept_tail_bytes"] = head, tail
        out["note"] = surf["note"]
    elif name == "rakazo":
        out["note"] = surf["repair"]
        out["kept_per_end_rule"] = "max(8, floor(len/4)) per leaf"
        out["inline_flag"] = "contextTruncated=true"
    elif name == "hermes-agent" and m is not None:
        head, tail = hermes_split(cliff)
        omitted = n - head - tail
        out["kept_head_chars"], out["kept_tail_chars"] = head, tail
        out["marker_rendered"] = hermes_notice(omitted, n)
    elif name == "bionic":
        out["kept_prefix_chars"] = cliff
    elif name == "claude-code" and surface == "result":
        out["note"] = FIRECRAWL_NOTE
    if "extra_cliffs" in surf:
        out["also"] = _claude_token_notes(surf, m)
    return out


def _claude_token_notes(surf, m):
    """Claude's token-unit cliffs: the tokenizer is Anthropic's and is
    NOT republished — an estimate never becomes a verdict here."""
    notes = []
    for c in surf.get("extra_cliffs", []):
        notes.append({"unit": c["unit"], "cliff": c["cliff"],
                      "verdict": c["verdict"], "kind": c["kind"],
                      "status": ("INDETERMINATE from chars — claude-"
                                 "code counts tokens with its own "
                                 "tokenizer; this kit refuses to "
                                 "convert, the chars cliff is the "
                                 "measured one (#97622)"),
                      "as_of": AS_OF})
    return notes


def run_cliff(args):
    harness = args.get("harness")
    result = args.get("result")
    size = args.get("size")
    unit = args.get("unit")
    surface = args.get("surface") or "result"
    if surface not in SURFACES:
        raise CliffError("surface", "unknown surface '%s'" % surface,
                         "|".join(SURFACES))
    if result is not None and (size is not None or unit is not None):
        raise CliffError(
            "size",
            "a paste and a declared size are two different claims — "
            "pick one",
            "result (paste, measured) OR size+unit (declared), never "
            "both")
    if result is None and size is None and unit is None:
        raise CliffError(
            "size", "nothing to judge — the table needs a size",
            "result (paste) or size+unit; unit ABSENT is a named "
            "refusal: the crossing is computed in the harness's own "
            "unit, never guessed")
    if unit is not None and size is None:
        raise CliffError("size", "a unit without a size decides nothing",
                         "size (int) alongside unit")
    if size is not None and unit is None:
        raise CliffError("unit", "size declared without unit",
                         "unit chars|bytes|lines|tokens — a count "
                         "without its unit is exactly how the 50k "
                         "tokens-for-chars lie happens")
    m = None
    n = None
    if result is not None:
        if not isinstance(result, str):
            raise CliffError("result", "result must be the pasted text",
                             "string")
        m = _measure(result)
    else:
        unit = str(unit).strip().lower()
        n = _declared_size(size, unit)
    args_rest = {k: args.get(k) for k in ("budget", "token_limit",
                                          "context_room", "tool",
                                          "max_response_size")}

    if harness is None:
        if m is None:
            raise CliffError(
                "harness",
                "all-rows mode needs a paste (a declared count cannot "
                "be faithful in eight units at once)",
                "paste result, or name one harness + size + unit")
        rows = []
        for name in ALL_ORDER:
            row = HARNESSES[name]
            if surface not in row["surfaces"]:
                continue
            r = _row_verdict(name, row, surface, m, None,
                             None, args_rest, result)
            if m is not None and surface == "result":
                r["json_survival"] = _json_survival(name, r, result)
            rows.append(r)
        return {"mode": "all-rows", "table_version": TABLE_VERSION,
                "as_of": AS_OF, "measured": m, "rows": rows,
                "firecrawl_548": FIRECRAWL_NOTE}

    name = resolve_harness(harness)
    row = HARNESSES[name]
    if surface not in row["surfaces"]:
        raise CliffError(
            "surface",
            "%s has no '%s' surface row — descriptions are cut only "
            "by claude-code in this table" % (name, surface),
            "surface result (or claude-code + description)")
    out = _row_verdict(name, row, surface, m,
                       unit if m is None else None, n, args_rest,
                       result)
    if m is not None and surface == "result":
        out["json_survival"] = _json_survival(name, out, result)
    out["mode"] = "paste" if m is not None else "declared"
    out["table_version"] = TABLE_VERSION
    if m is not None:
        out["measured"] = m
    return out
