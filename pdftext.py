"""doc/text — PDF text extraction, pure stdlib (zlib), no dependency
ever joins the image for this.

Honest scope, declared in every answer:
  SUPPORTED  uncompressed & FlateDecode content streams, the text
             operators Tj/TJ/'/", simple encoding diffs via /Differences,
             Type0/composite fonts via embedded ToUnicode CMaps (begin
             bfchar + beginbfrange), page order via the /Pages tree.
  REFUSED    image-only pages -> verdict "no text layer (ocr is not
             this endpoint)"; encrypted PDFs -> verdict, not garbage;
             unknown filters -> named, not guessed.

The value promise: the same PDF bytes in, the same text out, on any
machine, forever — verifiable by the sha256 in every response.
"""
import re
import zlib

_MAGIC_RE = re.compile(rb"^%PDF-(\d\.\d)")
_OBJ_RE = re.compile(rb"(\d+)\s+(\d+)\s+obj\b")
_REF_RE = re.compile(rb"(\d+)\s+0\s+R")


class PdfError(Exception):
    pass


def _objects(raw):
    """Map object number -> body bytes (between obj and endobj).
    Linear scan; PDFs are append-mostly and this is a reader, not an
    index — no xref parsing needed because we never trust offsets
    (stressed-file rule: rebuild, don't trust)."""
    objs = {}
    for m in _OBJ_RE.finditer(raw):
        num = int(m.group(1))
        start = m.end()
        end = raw.find(b"endobj", start)
        if end != -1:
            objs[num] = raw[start:end]
    return objs


def _value(objs, thing, depth=0):
    """Resolve indirect references one level deep, bounded."""
    if depth > 8:
        raise PdfError("reference cycle")
    m = _REF_RE.fullmatch(thing.strip()) if isinstance(thing, bytes) \
        else None
    if m:
        return _value(objs, objs.get(int(m.group(1)), b""), depth + 1)
    return thing


def _streams(objs, body):
    """Extract and decode every stream in an object body."""
    out = []
    i = 0
    while True:
        s = body.find(b"stream", i)
        if s == -1:
            break
        e = body.find(b"endstream", s)
        if e == -1:
            break
        head = body[max(0, s - 400):s]
        data = body[s + 6:e]
        data = data.lstrip(b"\r\n")
        filt = b""
        fm = re.search(rb"/Filter\s*/([A-Za-z0-9]+)", head)
        if fm:
            filt = fm.group(1)
        if filt == b"FlateDecode":
            try:
                data = zlib.decompress(data)
            except zlib.error:
                # some producers use raw deflate without zlib header
                try:
                    data = zlib.decompress(data, -15)
                except zlib.error:
                    raise PdfError("FlateDecode stream corrupt — "
                                   "refusing to invent bytes")
        elif filt not in (b"",):
            raise PdfError("filter %s outside the closed set "
                           "(none, FlateDecode) — named, not guessed"
                           % filt.decode())
        out.append(data)
        i = e + 9
    return out


_HEX4 = re.compile(rb"<[0-9A-Fa-f]{4,}>")


class _CMap:
    """ToUnicode CMap: bfchar + beginbfrange, the two that carry text."""

    def __init__(self):
        self.code2uni = {}

    def feed(self, stream):
        for m in re.finditer(rb"beginbfchar(.*?)endbfchar", stream, re.S):
            for pair in re.finditer(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>",
                                    m.group(1)):
                src, dst = pair.group(1), pair.group(2)
                self.code2uni[int(src, 16)] = _decode_hex4(dst)
        for m in re.finditer(rb"beginbfrange(.*?)endbfrange", stream, re.S):
            for row in re.finditer(
                    rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*"
                    rb"(<([0-9A-Fa-f]+)>|\[(.*?)\])", m.group(1), re.S):
                lo = int(row.group(1), 16)
                hi = int(row.group(2), 16)
                if row.group(4):
                    base = int(row.group(4), 16)
                    for i in range(lo, hi + 1):
                        self.code2uni[i] = _u16(base + (i - lo))
                else:
                    arr = row.group(5) or b""
                    vals = re.findall(rb"<([0-9A-Fa-f]+)>", arr)
                    for i, v in enumerate(vals[:hi - lo + 1]):
                        self.code2uni[lo + i] = _decode_hex4(v)


def _u16(x):
    try:
        return chr(x)
    except ValueError:
        return "\ufffd"


def _decode_hex4(h):
    h = h.decode()
    if len(h) == 2:
        return chr(int(h, 16))
    return "".join(_u16(int(h[i:i + 4], 16))
                   for i in range(0, len(h) - 3, 4))


def _pdf_string(body, start):
    """Read a literal (...) string, handling \\( \\) and nested parens
    and octal escapes, per PDF spec §7.3.4-5."""
    i = start + 1
    depth = 1
    out = bytearray()
    while i < len(body):
        c = body[i:i + 1]
        if c == b"\\":
            n = body[i + 1:i + 2]
            if n == b"n":
                out += b"\n"
            elif n == b"r":
                out += b"\r"
            elif n == b"t":
                out += b"\t"
            elif n == b"b":
                out += b"\b"
            elif n == b"f":
                out += b"\f"
            elif n and n in b"01234567":
                oct_ = body[i + 1:i + 4]
                k = 0
                while k < 3 and chr(oct_[k]).isdigit() \
                        and int(oct_[:k + 1], 8) <= 255:
                    k += 1
                out.append(int(oct_[:k], 8))
                i += k
            else:
                out += n
            i += 2
            continue
        if c == b"(":
            depth += 1
        elif c == b")":
            depth -= 1
            if depth == 0:
                return bytes(out), i + 1
        out += c
        i += 1
    raise PdfError("unterminated string in content stream")


# ------------------------------------------------------------------ text
_TOK_RE = re.compile(
    rb"/(?P<font>\w+)\s+[\d.]+\s+Tf"
    rb"|(?P<lit>\((?:[^()\\]|\\.)*\)|<[0-9A-Fa-f\s]+>)"
    rb"\s*(?P<op>Tj|'|\x22)"
    rb"|\[(?P<arr>[^\[\]]*)\]\s*TJ"
    rb"|(?P<nl>T\*|Td|TD)", re.S)


def _pdf_doc_string(body, use_cmap):
    """Decode one operand string per the active font: composite -> 2-byte
    codes via ToUnicode; simple -> bytes via /Differences map when set,
    latin-1 fallback (PDFDocEncoding ≈ latin-1 for text we meet)."""
    if use_cmap:
        hexs = b"".join(re.findall(rb"<([0-9A-Fa-f]+)>", body)) \
            if body.strip().startswith(b"<") else None
        if hexs is not None and len(hexs) % 4 == 0:
            return "".join(_u16(int(hexs[i:i + 4], 16))
                           for i in range(0, len(hexs), 4)) if all(
                int(hexs[i:i + 4], 16) in use_cmap for i in
                range(0, len(hexs), 4)) else "".join(
                use_cmap.get(int(hexs[i:i + 4], 16), "")
                for i in range(0, len(hexs), 4))
        raw, _ = _pdf_string(body, body.find(b"(")) \
            if b"(" in body[:2] else (b"", 0)
        data = raw or b""
        codes = [int.from_bytes(data[i:i + 2], "big")
                 for i in range(0, len(data) - 1, 2)]
        return "".join(use_cmap.get(c, _u16(c)) for c in codes)
    if body.strip().startswith(b"<"):
        h = re.findall(rb"<([0-9A-Fa-f]+)>", body)
        s = h[0] if h else b""
        data = bytes.fromhex(s.decode() + "0" * (len(s) % 2))
    else:
        data, _ = _pdf_string(body, body.find(b"("))
    return data.decode("latin-1", "replace")


def _font_cmap_for(objs, page_fonts_body):
    """{res-name: cmap-or-diff} for one page's /Font dict."""
    out = {}
    if not page_fonts_body:
        return out
    m = re.match(rb"\s*(\d+)\s+0\s+R", page_fonts_body)
    if m:
        page_fonts_body = objs.get(int(m.group(1)), b"")
    for fm in re.finditer(rb"/(\w+)\s+(\d+)\s+0\s+R", page_fonts_body):
        name, num = fm.group(1), int(fm.group(2))
        fbody = objs.get(num, b"")
        # ToUnicode?
        tu = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", fbody)
        cm = _CMap()
        if tu:
            tobj = objs.get(int(tu.group(1)), b"")
            try:
                for st in _streams(objs, tobj):
                    cm.feed(st)
            except PdfError:
                pass
        subtype = b"Type0" if b"/Type0" in fbody else b"simple"
        out[name.decode()] = cm.code2uni if subtype == b"Type0" \
            and cm.code2uni else None
    return out


def _pages_in_order(objs):
    root = None
    for num, body in objs.items():
        if b"/Type" in body and b"/Catalog" in body:
            root = num
            break
    if root is None:
        raise PdfError("no /Catalog — not a readable PDF")
    cat = objs[root]
    m = re.search(rb"/Pages\s+(\d+)\s+0\s+R", cat)
    if not m:
        raise PdfError("no /Pages in catalog")

    def walk(num, acc):
        body = objs.get(num, b"")
        kids = re.search(rb"/Kids\s*\[(.*?)\]", body, re.S)
        if kids:
            for km in re.finditer(rb"(\d+)\s+0\s+R", kids.group(1)):
                walk(int(km.group(1)), acc)
        elif b"/Type" in body and b"/Page" in body.replace(b"/Pages", b""):
            acc.append(num)
    acc = []
    walk(int(m.group(1)), acc)
    return acc


def extract_text(pdf_b64):
    import base64 as _b64
    if not isinstance(pdf_b64, str) or not pdf_b64.strip():
        raise PdfError("pdf_b64 required")
    raw = _b64.b64decode("".join(pdf_b64.split()), validate=True)
    if len(raw) > 16 * 1024 * 1024:
        raise PdfError("PDF exceeds the 16 MB cap")
    mm = _MAGIC_RE.match(raw.lstrip()[:32].lstrip(b"\xef\xbb\xbf")
                        if raw[:1] != b"%" else raw[:8])
    if not raw.lstrip().startswith(b"%PDF-"):
        raise PdfError("missing %PDF header — not a PDF, refusing to guess")
    if re.search(rb"/Encrypt\s+\d+\s+0\s+R", raw):
        raise PdfError("encrypted PDF: decryption is out of scope — "
                       "verdict, not garbage")
    objs = _objects(raw)
    if not objs:
        raise PdfError("no readable objects (linearized or damaged?)")
    pages = _pages_in_order(objs)
    out_pages = []
    no_text = 0
    for idx, num in enumerate(pages, 1):
        body = objs[num]
        contents = []
        cm = re.search(rb"/Contents\s*(\[[^\]]*\]|\d+\s+0\s+R)", body)
        if cm:
            spec = cm.group(1)
            refs = re.findall(rb"(\d+)\s+0\s+R", spec)
            for r in refs:
                try:
                    contents.extend(_streams(objs, objs.get(int(r), b"")))
                except PdfError:
                    raise
        # fonts for this page (page resources, else inherited search)
        res = re.search(rb"/Resources\s*<<(.*?)>>\s", body, re.S)
        fbody = re.search(rb"/Font\s*<<(.*?)>>",
                          res.group(1) if res else body, re.S)
        cmaps = _font_cmap_for(objs, fbody.group(1) if fbody else b"")
        text = []
        for stream in contents:
            cur_font = None
            for tok in _TOK_RE.finditer(stream):
                if tok.group("font") is not None:
                    cur_font = cmaps.get(tok.group("font").decode())
                elif tok.group("op") is not None:
                    lit, op = tok.group("lit"), tok.group("op")
                    dec = _pdf_doc_string(lit, cur_font)
                    text.append(dec)
                    if op in (b"'", b'"'):
                        text.append("\n")
                elif tok.group("arr") is not None:
                    parts = re.findall(
                        rb"\((?:[^()\\]|\\.)*\)|<[0-9A-Fa-f\s]+>",
                        tok.group("arr"))
                    text.append("".join(_pdf_doc_string(x, cur_font)
                                        for x in parts))
                else:
                    text.append("\n" if tok.group("nl") == b"T*"
                                else " ")
        joined = "".join(text)
        joined = re.sub(r"[ \t]+\n", "\n", joined)
        joined = re.sub(r"\n{3,}", "\n\n", joined).strip()
        if not joined:
            no_text += 1
        out_pages.append({"page": idx, "chars": len(joined),
                          "text": joined})
    return {
        "pages": out_pages,
        "page_count": len(out_pages),
        "text_pages": len(out_pages) - no_text,
        "empty_pages": no_text,
        "verdict": ("no text layer (image-only PDF — OCR is not this "
                    "endpoint)") if out_pages and no_text == len(out_pages)
                   else "ok",
        "total_chars": sum(p["chars"] for p in out_pages),
        "supported": "text operators Tj/TJ/'/\" , FlateDecode, "
                     "ToUnicode CMaps (bfchar/bfrange), /Differences",
    }
