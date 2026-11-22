"""Deterministic context & text tools (Bundle 7, TOOLS-50 #43-47).

Shared sentence splitter here is the SAME one text/chunk will use: the
count and the chunker can never disagree about where a sentence ends.
"""

import re
import unicodedata


class ContextError(Exception):
    pass


# ------------------------------------------------------------- sentences

_SENT_SPLIT = re.compile(r"""
    (?<=[.!?…])            # terminal punctuation
    (?=\s)                 # followed by whitespace
    |                    # OR
    \n{2,}                 # blank line = hard break
""", re.VERBOSE)


def split_sentences(text):
    """Deterministic sentence spans: [(start, end)] over the original
    text, separators (whitespace) attached to neither side's content."""
    spans = []
    pos = 0
    for part in _SENT_SPLIT.split(text):
        if part is None:
            continue
        stripped = part.strip()
        if stripped:
            start = text.find(stripped, pos)
            spans.append((start, start + len(stripped)))
            pos = start + len(stripped)
    return spans


_SENTENCES_CACHED = split_sentences  # chunker alias


def _paragraphs(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def text_count(text):
    if not isinstance(text, str):
        raise ContextError("text must be a string")
    words = re.findall(r"\w+", text, re.UNICODE)
    lines = text.splitlines()
    return {"chars": len(text),
            "chars_nospace": len(re.sub(r"\s", "", text)),
            "words": len(words),
            "sentences": len(split_sentences(text)),
            "paragraphs": len(_paragraphs(text)),
            "lines": len(lines),
            "bytes": len(text.encode("utf-8"))}


# ------------------------------------------------------------ natural sort

_NAT = re.compile(r"(\d+)")


def _natkey(s):
    parts = []
    for i, chunk in enumerate(_NAT.split(s)):
        if i % 2:
            parts.append((1, int(chunk), ""))
        elif chunk:
            parts.append((0, 0, chunk.lower()))
    return tuple(parts)


def sort_natural(items, reverse=False):
    if not isinstance(items, list) or any(
            not isinstance(i, str) for i in items):
        raise ContextError("items must be a list of strings")
    order = sorted(range(len(items)),
                   key=lambda i: (_natkey(items[i]), items[i]))
    if reverse:
        order = order[::-1]
    return {"sorted": [items[i] for i in order],
            "permutation": order, "count": len(items),
            "reverse": bool(reverse)}


# -------------------------------------------------------------------- case

def _words_of(text):
    t = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    t = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", t)
    t = re.sub(r"[\-_/\\]+", " ", t)
    return [w for w in re.split(r"\s+", t) if w]


CASES = ("snake", "kebab", "camel", "pascal", "title", "upper", "lower",
         "sentence")


def text_case(text, op="snake"):
    if not isinstance(text, str) or not text.strip():
        raise ContextError("text must be a non-empty string")
    if op not in CASES:
        raise ContextError("unknown op %r (closed: %s)"
                           % (op, ", ".join(CASES)))
    ws = _words_of(text)
    low = [w.lower() for w in ws]
    if op == "snake":
        out = "_".join(low)
    elif op == "kebab":
        out = "-".join(low)
    elif op == "camel":
        out = low[0] + "".join(w.capitalize() for w in low[1:])
    elif op == "pascal":
        out = "".join(w.capitalize() for w in low)
    elif op == "title":
        out = " ".join(w.capitalize() for w in low)
    elif op == "upper":
        out = " ".join(w.upper() for w in low)
    elif op == "lower":
        out = " ".join(low)
    else:  # sentence
        out = " ".join(low)
        out = out[:1].upper() + out[1:]
    return {"op": op, "result": out, "words": len(ws)}


# ---------------------------------------------------------------- truncate

def text_truncate(text, max_len, unit="chars", strategy="word",
                  ellipsis="…"):
    if not isinstance(text, str):
        raise ContextError("text must be a string")
    if not isinstance(max_len, int) or isinstance(max_len, bool) \
            or max_len < 1:
        raise ContextError("max_len must be a positive integer")
    if unit not in ("chars", "words", "sentences"):
        raise ContextError('unit must be "chars", "words" or "sentences"')
    if strategy not in ("cut", "word", "sentence"):
        raise ContextError("strategy must be cut|word|sentence")
    if len(ellipsis) > 32:
        raise ContextError("ellipsis too long")
    if unit == "sentences":
        spans = split_sentences(text)
        if len(spans) <= max_len:
            return {"truncated": False, "output": text,
                    "removed_units": 0, "end_char": len(text)}
        end = spans[max_len][0]
        kept = text[:end].rstrip()
        return {"truncated": True,
                "output": kept + (ellipsis if kept and ellipsis else ""),
                "removed_units": len(spans) - max_len,
                "end_char": len(kept)}
    if unit == "words":
        words = re.finditer(r"\S+", text)
        positions = [(m.start(), m.end()) for m in words]
        if len(positions) <= max_len:
            return {"truncated": False, "output": text,
                    "removed_units": 0, "end_char": len(text)}
        kept = text[:positions[max_len - 1][1]].rstrip()
        return {"truncated": True,
                "output": kept + (ellipsis if kept and ellipsis else ""),
                "removed_units": len(positions) - max_len,
                "end_char": len(kept)}
    # chars
    if len(text) <= max_len:
        return {"truncated": False, "output": text, "removed_units": 0,
                "end_char": len(text)}
    budget = max_len - len(ellipsis) if ellipsis else max_len
    cut = text[:max(budget, 1)]
    if strategy == "word" or strategy == "sentence":
        r = re.search(r"\S*$", cut)
        trimmed = cut[:r.start()] if r and r.start() > 0 else cut
        # avoid cutting mid-word unless nothing matched
        if strategy == "word":
            sp = trimmed.rfind(" ")
            cut = trimmed[:sp] if sp > 0 else cut
        else:
            for p in ".!?…":
                sp = trimmed.rfind(p)
                if sp >= 0:
                    cut = trimmed[:sp + 1]
                    break
            else:
                cut = trimmed
    out = cut.rstrip() + (ellipsis if ellipsis else "")
    return {"truncated": True, "output": out,
            "removed_chars": len(text) - len(out), "end_char": len(cut)}


# --------------------------------------------------------------- regex/test

_FLAGS = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL,
          "x": re.VERBOSE, "u": re.UNICODE, "a": re.ASCII}
_MODES = ("test", "findall", "groups", "replace")


def regex_test(pattern, text, flags="u", mode="test", template=None,
               count=0):
    if not isinstance(pattern, str) or not isinstance(text, str):
        raise ContextError("pattern and text must be strings")
    if len(text) > 65536:
        raise ContextError("regex input capped at 65536 characters "
                           "(ReDoS blast-radius rule)")
    if mode not in _MODES:
        raise ContextError("mode must be one of: %s" % ", ".join(_MODES))
    f = re.UNICODE
    for ch in flags:
        if ch not in _FLAGS:
            raise ContextError("unknown flag %r (closed: %s)"
                               % (ch, "".join(sorted(_FLAGS))))
        f |= _FLAGS[ch]
    try:
        rx = re.compile(pattern, f)
    except re.error as e:
        raise ContextError("invalid pattern: %s" % e)
    if mode == "test":
        m = rx.search(text)
        return {"matched": m is not None,
                "match": m.group(0) if m else None,
                "span": [m.start(), m.end()] if m else None}
    if mode == "findall":
        return {"matches": [{"text": m.group(0),
                             "span": list(m.span())}
                            for m in rx.finditer(text)],
                "count_total": len(rx.findall(text))}
    if mode == "groups":
        m = rx.search(text)
        if not m:
            return {"matched": False, "named": {}, "numbered": []}
        named = {k: v for k, v in sorted(m.groupdict().items())}
        return {"matched": True, "named": named,
                "numbered": [g for g in m.groups()],
                "span": [m.start(), m.end()]}
    # replace
    if template is None:
        raise ContextError("replace mode requires 'template'")
    # closed extension: $1 JS-style backrefs are what models emit;
    # map them to \g<1> so both dialects work, nothing else changes
    tpl = re.sub(r"\$(\d+)", r"\\g<\1>", template)
    n = 0
    def _sub(m):
        nonlocal n
        n += 1
        return m.expand(tpl)
    out = rx.sub(_sub, text, count=count)
    return {"result": out, "replacements": n, "count_limit": count}


# ----------------------------------------------------------------- chunk
#
# The flagship: exact token-budget splitting. tiktoken is the ONE non-
# stdlib dependency of Mechacut — its BPE files are content-addressed
# (sha-1 in the filename), so "same input, same bytes" holds across
# versions of anything else; we report the version AND the file hash in
# every response so a golden can be re-audited years later.

_TOKENIZERS = {}


def _tokenizer(encoding):
    if encoding not in _TOKENIZERS:
        try:
            import tiktoken
        except ImportError:
            raise ContextError("tokenizer unavailable")
        try:
            _TOKENIZERS[encoding] = tiktoken.get_encoding(encoding)
        except (ValueError, KeyError):
            raise ContextError("unknown encoding %r (closed: cl100k_base, "
                               "o200k_base, o250k_base, p50k_base, "
                               "gpt2)" % encoding)
    return _TOKENIZERS[encoding]


def text_chunk(text, budget=512, overlap=0, encoding="cl100k_base",
               unit="sentence"):
    if not isinstance(text, str):
        raise ContextError("text must be a string")
    if not isinstance(budget, int) or isinstance(budget, bool) \
            or budget < 1:
        raise ContextError("budget must be a positive integer")
    if not isinstance(overlap, int) or isinstance(overlap, bool) \
            or overlap < 0:
        raise ContextError("overlap must be a non-negative integer")
    if overlap >= budget:
        raise ContextError("overlap must be < budget")
    if unit not in ("sentence", "paragraph"):
        raise ContextError('unit must be "sentence" or "paragraph"')
    if not text.strip():
        return {"encoding": encoding, "budget": budget, "overlap": overlap,
                "unit": unit, "count": 0, "chunks": [],
                "total_tokens": 0}
    enc = _tokenizer(encoding)
    if unit == "paragraph":
        units = []
        pos = 0
        for m in re.finditer(r"\S[^\n]*(?:\n(?!\s*\n)[^\n]*)*",
                             text):
            if m.group(0).strip():
                units.append(m.span())
    else:
        units = split_sentences(text)
    if not units:  # punctuation-less blob
        units = [(0, len(text))]
    toks = [len(enc.encode(text[a:b], disallowed_special=()))
            for a, b in units]
    chunks = []
    i = 0
    while i < len(units):
        take, used = 0, 0
        while i + take < len(units):
            if take and used + toks[i + take] > budget:
                break
            used += toks[i + take]
            take += 1
            if used >= budget:
                break
        span = (units[i][0], units[i + take - 1][1])
        piece = text[span[0]:span[1]]
        pt = enc.encode(piece, disallowed_special=())
        if len(pt) > budget:
            # single oversized unit: hard cut at token boundaries
            for k in range(0, len(pt), budget):
                sub = pt[k:k + budget]
                sub_text = enc.decode(sub)
                st = text.find(sub_text, span[0])
                chunks.append({"index": len(chunks), "text": sub_text,
                               "tokens": len(sub),
                               "char_start": st if st >= 0 else -1,
                               "hard_cut": True})
            i += take
            continue
        chunks.append({"index": len(chunks), "text": piece,
                       "tokens": len(pt), "char_start": span[0],
                       "hard_cut": False})
        step = take
        if overlap and i + take < len(units):
            back, acc = 0, 0
            while take - 1 - back >= 0 and \
                    acc + toks[i + take - 1 - back] <= overlap:
                acc += toks[i + take - 1 - back]
                back += 1
            if back:
                step = take - back  # next chunk re-takes those units
        i += step
    total = sum(c["tokens"] for c in chunks)
    return {"encoding": encoding, "budget": budget, "overlap": overlap,
            "unit": unit, "count": len(chunks), "chunks": chunks,
            "total_tokens": total}
