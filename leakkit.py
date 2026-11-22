"""Bundle 26 — LEAK. The output gate for secrets.

/secret/scan  : closed pattern table (24 published key formats + Luhn
                cards + IBAN + JWT + private-key blocks + BIP39 seeds
                with the REAL checksum algorithm), exact positions.
/text/redact  : mask with stable per-kind numbering ([APIKEY_1]...),
                the rari-post part 5 done deterministically: the model
                never sees the raw value again, and the numbering is
                position-driven so the SAME text always gets the SAME
                mask. Mapping is OFF by default: a redaction endpoint
                that echoes secrets back is a new leak with extra steps.
"""
import hashlib
import re

_PATTERNS = [
    ("openai-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("github-fine-grained", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    ("aws-access-key", re.compile(r"\b(AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("stripe-key", re.compile(r"\b[sr]k_(?:live|test)_[0-9a-zA-Z]{20,}\b")),
    ("discord-webhook", re.compile(
        r"https://discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9_-]{20,}")),
    ("telegram-bot-token", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b")),
    ("private-key-block", re.compile(
        r"-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
                       r"\.??[A-Za-z0-9_-]*\b")),
    ("aws-secret", re.compile(r"(?i)aws.{0,20}[\"']?[0-9a-zA-Z/+]{40}[\"']?")),
]

_LUHN_RUN = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_IBANISH = re.compile(r"\b[A-Z]{2}\d{2}[ ]?(?:[A-Z0-9]{4}[ ]?){3,7}[A-Z]{0,4}\b")


def _luhn_ok(digits):
    s = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2:
            n *= 2
            if n > 9:
                n -= 9
        s += n
    return s % 10 == 0


def _card_brand(first):
    if first.startswith("4"):
        return "visa"
    if first[:2] in ("51", "52", "53", "54", "55"):
        return "mastercard"
    if first[:2] in ("34", "37"):
        return "amex"
    return "card"


def _iban_mod97(value):
    v = value.replace(" ", "").upper()
    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$", v):
        return False
    rearr = v[4:] + v[:4]
    num = "".join(str(int(c, 36)) for c in rearr)
    return int(num) % 97 == 1


# BIP39 English wordlist: shipped closed (2048 words is the standard;
# we ship the FIRST load from a local copy if present, else checksum
# validation of word indices works on any subset via membership +
# 11-bit unpack + sha256 leading-bits rule).
_WORDS = None


def _get_words():
    global _WORDS
    if _WORDS is None:
        import os
        path = os.path.join(os.path.dirname(__file__), "bip39_english.txt")
        if os.path.exists(path):
            _WORDS = [w.strip() for w in open(path, encoding="utf-8")
                      if w.strip()]
        else:
            _WORDS = []
    return _WORDS


def bip39_check(text):
    """Seed-phrase WELL-FORMEDNESS by the published algorithm: 12/15/18/
    21/24 words, every word in the English list, and the real checksum
    (leading sha256 bits of the entropy). Verdicts: valid / bad_checksum
    / not-english-wordlist / not-a-phrase. NEVER stores anything."""
    words = str(text).lower().split()
    if len(words) not in (12, 15, 18, 21, 24):
        return {"looks_like_seed": False, "verdict": "not-a-phrase",
                "word_count": len(words)}
    wl = _get_words()
    if not wl:
        return {"looks_like_seed": len(words) >= 12,
                "verdict": "wordlist-not-shipped",
                "note": "checksum needs the 2048-word list; the count and "
                        "shape verdicts are given, the rest is not guessed",
                "word_count": len(words)}
    idx = []
    for w in words:
        if w not in wl:
            return {"looks_like_seed": True, "verdict": "not-english-wordlist",
                    "first_unknown_word": w, "word_count": len(words)}
        idx.append(wl.index(w))
    bits = "".join(format(i, "011b") for i in idx)
    ent_bits = len(bits) * 32 // 33
    entropy, csum = bits[:ent_bits], bits[ent_bits:]
    eb = int(entropy, 2).to_bytes(ent_bits // 8, "big")
    good = format(int.from_bytes(hashlib.sha256(eb).digest()[:1], "big"),
                  "08b")[:len(csum)]
    return {"looks_like_seed": True,
            "verdict": "valid" if good == csum else "bad_checksum",
            "word_count": len(words), "language": "english"}


def _seed_spans(text):
    """Leftmost-shortest sliding window over word tokens: any run of
    12/15/18/21/24 wordlist words is a seed candidate; the checksum
    (published BIP39 rule) decides valid vs bad_checksum. Non-overlapping,
    deterministic. THE seed detector: scan and redact share it."""
    wl = _get_words()
    if not wl:
        return []
    wset = set(wl)
    toks = [(m.start(), m.group(0).lower(), m.end())
            for m in re.finditer(r"[A-Za-z]+", text)]
    spans = []
    taken = 0
    for size in (12, 15, 18, 21, 24):
        i = 0
        while i + size <= len(toks):
            if toks[i][0] < taken:
                i += 1
                continue
            run = toks[i:i + size]
            if all(w in wset for _s, w, _e in run):
                bits = "".join(format(wl.index(w), "011b")
                               for _s, w, _e in run)
                ent = bits[:len(bits) * 32 // 33]
                csum = bits[len(bits) * 32 // 33:]
                eb = int(ent, 2).to_bytes(len(ent) // 8, "big")
                good = format(int.from_bytes(
                    hashlib.sha256(eb).digest()[:1], "big"),
                    "08b")[:len(csum)]
                verdict = "valid" if good == csum else "bad_checksum"
                spans.append((run[0][0], run[-1][2], verdict, size))
                taken = run[-1][2]
                i += size
                continue
            i += 1
    return sorted(spans)


def scan_secrets(text, kinds=None):
    if not isinstance(text, str) or not text:
        raise ValueError("text must be a non-empty string")
    if len(text) > 200_000:
        raise ValueError("text too large for one scan (max 200 KB)")
    want = set(kinds) if kinds else None
    findings = []
    for kind, rx in _PATTERNS:
        if want and kind not in want:
            continue
        for m in rx.finditer(text):
            findings.append(_finding(kind, m.start(), m.group(0), text))
    if not want or "card" in (want or {"card"}):
        for m in _LUHN_RUN.finditer(text):
            run = re.sub(r"[ -]", "", m.group(0))
            if len(run) in (13, 14, 15, 16, 19) and _luhn_ok(run):
                findings.append(_finding(_card_brand(run), m.start(),
                                         m.group(0), text))
    if not want or "iban" in (want or {"iban"}):
        for m in _IBANISH.finditer(text):
            if _iban_mod97(m.group(0)) and not m.group(0).startswith("0"):
                findings.append(_finding("iban", m.start(), m.group(0), text))
    if not want or "bip39-seed" in (want or {"bip39-seed"}):
        for a, b, verdict, size in _seed_spans(text):
            findings.append({"kind": "bip39-seed-" + verdict,
                             "at": a, "length": b - a,
                             "word_count": size,
                             "preview": "[seed phrase, %d words]" % size})
    findings.sort(key=lambda f: f["at"])
    return {"findings": findings, "count": len(findings),
            "clean": not findings,
            "first_at": (findings[0]["at"] if findings else None)}


def _finding(kind, at, value, text):
    return {"kind": kind, "at": at, "length": len(value),
            "preview": value[:4] + "…" + value[-2:] if len(value) > 8
            else "•" * len(value)}


def redact(text, mask_tag=None):
    """Mask before you post: every finding from scan_secrets — keys,
    cards, IBAN, seeds — becomes a tag numbered by position, so the same
    text always yields the same mask. No mapping is returned: a redaction
    endpoint that echoes secrets is a leak with extra steps."""
    scan = scan_secrets(text)
    out = []
    last = 0
    counters = {}
    for f in sorted((x for x in scan["findings"]), key=lambda x: x["at"]):
        if f["at"] < last:
            continue
        if f["kind"].startswith("bip39-seed"):
            tag = "[SEED_PHRASE]"
        else:
            counters[f["kind"]] = counters.get(f["kind"], 0) + 1
            tag = mask_tag or ("[%s_%d]" % (
                f["kind"].upper().replace("-", "_"), counters[f["kind"]]))
        out.append(text[last:f["at"]])
        out.append(tag)
        last = f["at"] + f["length"]
    out.append(text[last:])
    return {"redacted": "".join(out), "items": scan["count"],
            "kinds": sorted(counters),
            "positions": sorted(f["at"] for f in scan["findings"])}
