"""Bundle 21 — INTAKE. The intent card: turn a human's ordinary sentence
into a tool choice + a pre-filled form, and turn what's missing into the
exact question to ask back. Closed rules only: no model, no guessing, no
storage. Same utterance -> same card.

status:
  ready      -> one tool clearly wins; card fields filled/defaulted/missing
  ambiguous  -> several tools compete (or top score too weak); ask which one
  no_match   -> nothing matched; say so instead of improvising

Field sources are mechanical:
  fact kinds found in the utterance (money/date/url/email/uuid/iban/number)
  enum values appearing as words
  defaults declared by the schema
  text-ish payload fields stay MISSING unless the utterance looks like a
  payload (multi-line or >= 120 chars) — an instruction is not a document.
"""
import re

from extract import extract_facts

MIN_SCORE = 3            # below this the top tool is a coin flip
MARGIN = 2               # top - second <= MARGIN -> ambiguous
PAYLOAD_MIN_CHARS = 120

# schema field name -> fact kind harvested from the utterance
FACT_FIELDS = {
    "amount": "money", "money": "money", "value": None,  # value: number|money
    "date": "date", "day": "date",
    "url": "url", "link": "url",
    "email": "email", "mail": "email",
    "iban": "iban", "uuid": "uuid", "id": None,
}
LIST_FIELDS = {"items", "urls", "emails", "rows", "payloads", "chunks",
               "line_items"}
TEXT_FIELDS = {"text", "csv", "html", "markdown", "md", "data", "document",
               "input", "doc", "body", "content", "pattern", "patch", "diff",
               "note", "query"}


def _words(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


def _looks_like_payload(utterance):
    return ("\n" in utterance.strip()
            or len(utterance.strip()) >= PAYLOAD_MIN_CHARS)


def _x_request(utterance):
    """Nothing is ever SENT from here: this builds a draft link the
    human opens in their own X client, where they see and edit the text
    before any posting. Long alphanumerics (possible keys/tokens) are
    scrubbed first — a gap report describes the task, never leaks its
    payload."""
    import re
    from urllib.parse import quote
    clean = re.sub(r"[A-Za-z0-9_+/=\-]{16,}", "…", str(utterance))
    clean = " ".join(clean.split())[:90]
    text = ("mechacut.studio has no tool for: \u201c%s\u201d — "
            "could you build it? @Davincc" % clean)
    return {"url": "https://x.com/intent/post?text=" + quote(text),
            "note": "Nothing was sent. The link opens YOUR draft on X "
                    "with this sentence; edit or delete as you like. "
                    "Secrets were scrubbed from the text."}


def build_card(utterance, schemas, route_fn, top_tools=3):
    """schemas: {tool_name: inputSchema}. route_fn: routing.route.
    Returns the card dict (no sha here — the caller adds it)."""
    if not isinstance(utterance, str) or not utterance.strip():
        raise ValueError("utterance must be a non-empty string")

    cands = route_fn(utterance, top=top_tools) or []
    if not cands or cands[0]["score"] < MIN_SCORE:
        return {"status": "no_match",
                "candidates": [{"tool": c["tool"], "purpose": c["purpose"],
                                "score": c["score"]} for c in cands],
                "question_human":
                    "I could not match this to a mechanical tool; rephrase "
                    "the operation (convert / count / format / hash / "
                    "extract …) or browse /agent/manifest.",
                "request_on_x": _x_request(utterance)}
    if (len(cands) > 1
            and cands[0]["score"] - cands[1]["score"] <= MARGIN):
        return {"status": "ambiguous",
                "candidates": [{"tool": c["tool"], "purpose": c["purpose"],
                                "score": c["score"]} for c in cands],
                "question_human": "Which one did you mean: " + " / ".join(
                    "%s (%s)" % (c["tool"], c["purpose"])
                    for c in cands) + "?"}

    tool = cands[0]["tool"]
    schema = schemas.get(tool) or {}
    props = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    facts = None  # harvested lazily

    card = {}
    for fname, spec in sorted(props.items()):
        spec = spec if isinstance(spec, dict) else {}
        stype = spec.get("type")
        if isinstance(stype, list):          # unions: ["number","string"]
            stype = "string" if "string" in stype else stype[0]
        default = spec.get("default")
        enum = spec.get("enum")
        filled = None
        how = None

        if enum:
            hit = [e for e in enum
                   if isinstance(e, str) and re.search(
                       r"\b%s\b" % re.escape(str(e).lower()),
                       utterance.lower())]
            if hit:
                filled, how = hit[0], "enum word in utterance"
        if filled is None and stype in ("array",):
            if fname in LIST_FIELDS:
                lines = [ln.strip() for ln in
                         re.split(r"[\n,]", utterance.strip()) if ln.strip()]
                if "\n" in utterance and len(lines) > 1:
                    filled, how = lines[:100], "lines of the utterance"
        if filled is None and stype in ("integer", "number"):
            if fname in ("count", "n", "places", "k", "max_words",
                         "max_bytes", "top", "due_days", "width", "height"):
                mnum = re.search(r"\b%s\s*=?\s*(\d+)\b" % re.escape(fname),
                                 utterance.lower())
                if not mnum:
                    mnum = re.search(r"(\d+)\s+%s\b" % re.escape(fname),
                                     utterance.lower())
                if mnum:
                    filled = int(mnum.group(1))
                    how = "number next to the field name"
        if filled is None and (stype == "string" or (stype is None and (
                fname in FACT_FIELDS or fname in TEXT_FIELDS))):
            kind = FACT_FIELDS.get(fname, "auto")
            if kind == "auto":
                for token, fk in FACT_FIELDS.items():
                    if token in fname.split("_") and fk:
                        kind = fk
                        break
                else:
                    kind = None
            if kind or fname == "value":
                if facts is None:
                    facts = extract_facts(utterance, context_chars=0)
                kinds = ("money", "number") if fname == "value" else (kind,)
                hits = [f["value"] for f in facts["facts"]
                        if f["kind"] in kinds]
                if hits:
                    filled, how = hits[0], "fact found in the utterance"
            if filled is None and fname in TEXT_FIELDS:
                if _looks_like_payload(utterance):
                    filled, how = utterance, "the utterance IS the payload"
        if filled is None and default is not None:
            filled, how = default, "schema default — confirm if unsure"

        if filled is None:
            card[fname] = {"state": "MISSING",
                           "required": fname in required,
                           "hint": (",".join(map(str, enum)) if enum
                                    else stype or "value")}
        else:
            card[fname] = {"state": "filled", "value": filled, "how": how}

    missing = [f for f, c in card.items()
               if c["state"] == "MISSING" and c["required"]]
    status = "ready" if not missing else "incomplete"
    question = None
    if missing:
        question = ("To run %s I still need: %s." % (
            tool, ", ".join("%s (%s)" % (m, card[m]["hint"])
                            for m in missing)))
    return {"status": status,
            "tool": tool, "path": cands[0]["path"],
            "tier": cands[0].get("tier", "free"),
            "score": cands[0]["score"],
            "card": card,
            "missing_required": missing,
            "question_human": question}


def check_filled(tool, args, schemas):
    """The gate before the pay: a filled card is validated against the
    tool's real schema with the same closed rules. Returns (ok, problems).
    problems are phrased for the human AND parseable by the agent."""
    schema = schemas.get(tool)
    if schema is None:
        return False, [{"field": "tool",
                        "message": "unknown tool — pick from /agent/manifest"}]
    props = schema.get("properties") or {}
    required = list(schema.get("required") or [])
    args = args if isinstance(args, dict) else {}
    problems = []
    for fname in required:
        if fname not in args or args[fname] in (None, "", []):
            spec = props.get(fname) or {}
            problems.append({
                "field": fname,
                "message": "missing required field",
                "expected": ",".join(map(str, spec.get("enum") or []))
                            or spec.get("type") or "value"})
    for fname, val in args.items():
        spec = props.get(fname) or {}
        if not spec:
            problems.append({"field": fname,
                             "message": "not a field of %s" % tool,
                             "expected": ",".join(sorted(props))})
            continue
        enum = spec.get("enum")
        if enum and val not in enum:
            problems.append({"field": fname,
                             "message": "value %r not allowed" % (val,),
                             "expected": ",".join(map(str, enum))})
    return (not problems), problems
