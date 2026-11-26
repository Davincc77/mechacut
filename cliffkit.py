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
"""

TABLE_VERSION = "b116-1"
AS_OF = "2026-11-26"

UNITS = ("chars", "bytes", "lines", "tokens")
SURFACES = ("result", "description")


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
                    "source": ("codex-rs/utils/string/src/truncate.rs "
                               "+ session/step_settings.rs read "
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
    }


HARNESSES = _rows()

FIRECRAWL_NOTE = ("firecrawl-mcp-server#548 (open 2026-10-16, read "
                  "2026-11-26) is NOT a separate cutter: the 2 KB "
                  "preview is Claude Code's own post-persist inline — "
                  "it rides the claude-code recoverable field.")

ALL_ORDER = ("claude-code", "codex", "bionic", "vscode", "rakazo",
             "hermes-agent")


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


def _row_verdict(name, row, surface, m, unit, size, args):
    surf = row["surfaces"][surface]
    out = {"harness": name, "surface": surface,
           "unit": surf["unit"],
           "counted_as": surf["counted_as"],
           "verdict": None, "crossed": None, "margin": None,
           "message_lies": surf["message_lies"],
           "marker": surf["marker"],
           "recoverable": surf["recoverable"],
           "repair": surf["repair"],
           "source": surf["source"], "as_of": AS_OF}
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
    args_rest = {k: args.get(k) for k in ("budget", "token_limit")}

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
            rows.append(_row_verdict(name, row, surface, m, None, None,
                                     args_rest))
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
                       unit if m is None else None, n, args_rest)
    out["mode"] = "paste" if m is not None else "declared"
    out["table_version"] = TABLE_VERSION
    if m is not None:
        out["measured"] = m
    return out
