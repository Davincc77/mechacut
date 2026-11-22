"""Closed-subset Markdown -> HTML (Bundle 7, TOOLS-50 #48).

Deliberately NOT a full CommonMark implementation and not a third-party
parser: this is the contract the server states and keeps forever. A
model that needs more composes more calls; a model that needs exactly
this gets byte-stable HTML out of it. Unknown constructs are escaped
text, never surprises.
"""

import html as _html
import re
import unicodedata


class RenderError(Exception):
    pass


_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^()\s]+)(?:\s+\"([^\"]*)\")?\)")
_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^()\s]+)(?:\s+\"([^\"]*)\")?\)")


def _safe_url(url):
    u = url.strip()
    low = u.lower()
    if low.startswith(("javascript:", "vbscript:", "data:")) and \
            not low.startswith("data:image/"):
        raise RenderError("url scheme refused: %r" % u[:30])
    return _html.escape(u, quote=True)


def _inline(line):
    # escape FIRST: the closed subset never trusts raw HTML
    out = _html.escape(line, quote=False)
    # images before links (link syntax is a subset of image syntax)
    out = _IMG_RE.sub(
        lambda m: '<img alt="%s" src="%s"%s>' % (
            m.group(1), _safe_url(m.group(2)),
            ' title="%s"' % _html.escape(m.group(3), quote=True)
            if m.group(3) else ""), out)
    out = _LINK_RE.sub(
        lambda m: '<a href="%s"%s>%s</a>' % (
            _safe_url(m.group(2)),
            ' title="%s"' % _html.escape(m.group(3), quote=True)
            if m.group(3) else "", m.group(1)), out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", out)
    return out


_FENCE = "```"


def md_render(text, heading_ids=False):
    if not isinstance(text, str):
        raise RenderError("markdown must be a string")
    if len(text) > 262144:
        raise RenderError("markdown capped at 256 KB")
    lines = text.replace("\r\n", "\n").split("\n")
    out = []
    para = []
    fence = None
    fence_lang = ""
    fence_buf = []
    list_mode = None          # None | "ul" | "ol"

    def flush_para():
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_list():
        nonlocal list_mode
        if list_mode:
            out.append("</ul>" if list_mode == "ul" else "</ol>")
            list_mode = None

    def flush_fence():
        nonlocal fence, fence_buf, fence_lang
        if fence is not None:
            code = _html.escape("\n".join(fence_buf), quote=False)
            attr = ' class="language-%s"' % _html.escape(
                fence_lang, quote=True) if fence_lang else ""
            out.append("<pre><code%s>%s</code></pre>" % (attr, code))
            fence, fence_buf, fence_lang = None, [], ""

    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        if fence is not None:
            if stripped.startswith(_FENCE):
                flush_fence()
            else:
                fence_buf.append(raw)
            i += 1
            continue
        if stripped.startswith(_FENCE):
            flush_para()
            fence = True
            fence_lang = stripped[3:].strip().split(" ")[0]
            i += 1
            continue

        # tables: consecutive |...| lines, header + separator + rows
        if stripped.startswith("|") and stripped.endswith("|"):
            flush_para()
            flush_list()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|") and \
                    lines[i].strip().endswith("|"):
                cells = [c.strip() for c in
                         lines[i].strip()[1:-1].split("|")]
                rows.append(cells)
                i += 1
            body = rows
            sep = (len(rows) >= 2 and rows[1] and
                   all(re.match(r"^:?-{3,}:?$", c) for c in rows[1]))
            if sep:
                head, body = rows[0], rows[2:]
            else:
                head = None
            t = ["<table>"]
            if head:
                t.append("<thead><tr>" + "".join(
                    "<th>%s</th>" % _inline(c) for c in head)
                    + "</tr></thead>")
            t.append("<tbody>")
            for r in body:
                t.append("<tr>" + "".join("<td>%s</td>" % _inline(c)
                                          for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("\n".join(t))
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush_para()
            flush_list()
            lvl = len(m.group(1))
            content = _inline(m.group(2).strip())
            attr = ""
            if heading_ids:
                sid = unicodedata.normalize("NFKD", m.group(2))
                sid = "".join(ch for ch in sid
                              if not unicodedata.combining(ch))
                sid = re.sub(r"[^a-z0-9]+", "-", sid.lower()).strip("-")
                attr = ' id="%s"' % sid
            out.append("<h%d%s>%s</h%d>" % (lvl, attr, content, lvl))
            i += 1
            continue

        if stripped == "---" or stripped == "***" or stripped == "___":
            flush_para()
            flush_list()
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith("> "):
            flush_para()
            flush_list()
            out.append("<blockquote><p>%s</p></blockquote>"
                       % _inline(stripped[2:]))
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if m:
            flush_para()
            if list_mode != "ol":
                flush_list()
                out.append("<ol>")
                list_mode = "ol"
            out.append("<li>%s</li>" % _inline(m.group(2)))
            i += 1
            continue
        m = re.match(r"^[-*+]\s+(.*)$", stripped)
        if m:
            flush_para()
            if list_mode != "ul":
                flush_list()
                out.append("<ul>")
                list_mode = "ul"
            out.append("<li>%s</li>" % _inline(m.group(1)))
            i += 1
            continue

        if not stripped:
            flush_para()
            flush_list()
            i += 1
            continue

        flush_list()
        para.append(stripped)
        i += 1

    flush_para()
    flush_list()
    flush_fence()
    # lenient by documented contract: an unclosed fence just closes at EOF
    return "<div class=\"markdown\">" + "\n".join(out) + "</div>"


_DOC_CSS = (
    "body{margin:0;background:#faf9f7;color:#111;font:15px/1.65 "
    "Georgia,'Times New Roman',serif}"
    ".sheet{max-width:720px;margin:0 auto;padding:48px 40px;background:#fff;"
    "box-shadow:0 1px 4px rgba(0,0,0,.12)}"
    "h1,h2,h3{font-family:Helvetica,Arial,sans-serif;line-height:1.25}"
    "h1{font-size:26px;margin:0 0 18px}h2{font-size:20px;margin:26px 0 10px}"
    "h3{font-size:16px;margin:20px 0 8px}"
    "code,pre{font:13px/1.5 ui-monospace,Menlo,monospace;background:#f2f1ee;"
    "border-radius:6px}pre{padding:10px 12px;overflow-x:auto}"
    "table{border-collapse:collapse;margin:14px 0}td,th{border:1px solid #ccc;"
    "padding:5px 9px;font-size:14px}"
    "blockquote{margin:14px 0;padding:2px 16px;border-left:3px solid #c9b458;"
    "color:#333}"
    "@media print{body{background:#fff}.sheet{max-width:none;margin:0;"
    "padding:0;box-shadow:none}@page{margin:18mm 16mm}}"
)


def md_document(body_html, title=None):
    """Standalone printable page: A4-friendly CSS, print rules — Ctrl-P
    makes the PDF, the bytes stay deterministic."""
    import html as _h
    t = _h.escape(title or "Document", quote=True)
    return ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<title>%s</title><style>%s</style></head><body><div class=\"sheet\">"
            "%s</div></body></html>" % (t, _DOC_CSS, body_html))
