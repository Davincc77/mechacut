"""Deterministic HTML -> text (Bundle 7, TOOLS-50 #49).

Stdlib html.parser only: block structure becomes newlines, invisible
regions (script/style/noscript/template/head/svg/iframe) vanish, links
can optionally carry their href, entities are decoded once, whitespace
collapses per closed rule. The anti-hallucination tool for scraping
agents: they never "remember" a page, they read this canonical text.
"""

import re
import html
from html.parser import HTMLParser


class ExtractError(Exception):
    pass


_SKIP = {"script", "style", "noscript", "template", "head", "svg",
         "iframe", "canvas", "video", "audio", "object", "embed"}
_BLOCK = {"p", "div", "section", "article", "main", "header", "footer",
          "nav", "aside", "blockquote", "pre", "ul", "ol", "li", "table",
          "tr", "thead", "tbody", "tfoot", "td", "th", "h1", "h2", "h3",
          "h4", "h5", "h6", "br", "hr", "figure", "figcaption", "dt",
          "dd", "dl", "form", "fieldset", "details", "summary",
          "address", "dialog"}


class _Text(HTMLParser):
    def __init__(self, keep_links, max_bytes):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip_depth = 0
        self.keep_links = keep_links
        self.href = None
        self.total = 0
        self.max_bytes = max_bytes
        self.truncated = False
        self.links_refused = 0
        self._link_buf = None

    def handle_starttag(self, tag, attrs):
        if self.truncated:
            return
        if tag in _SKIP:
            self.skip_depth += 1
        if tag in _BLOCK:
            self.parts.append("\n")
        if tag == "a" and self.keep_links:
            self.href = dict(attrs).get("href")
            self._link_buf = [] if self.href else None
        if tag == "img":
            alt = dict(attrs).get("alt", "")
            if alt:
                self.parts.append("[%s]" % alt)

    def handle_endtag(self, tag):
        if self.truncated:
            return
        if tag in _SKIP and self.skip_depth:
            self.skip_depth -= 1
        if tag in _BLOCK:
            self.parts.append("\n")
        if tag == "a" and self._link_buf is not None:
            label = "".join(self._link_buf)
            href = self.href or ""
            low = href.strip().lower()
            if low.startswith(("javascript:", "data:", "vbscript:")):
                self.links_refused += 1
                href = ""
            if label or href:
                self.parts.append("%s (%s)" % (label, href) if href
                                  else label)
            self._link_buf = None
            self.href = None

    def handle_data(self, data):
        if self.truncated or not data:
            return
        if self.skip_depth:
            return
        if self._link_buf is not None:
            self._link_buf.append(data)
            return
        self.parts.append(data)
        self.total += len(data)
        if self._byte_len() > self.max_bytes:
            self.truncated = True

    def _byte_len(self):
        return sum(len(p.encode("utf-8")) for p in self.parts)


def html_text(raw, keep_links=False, max_bytes=1_048_576):
    if not isinstance(raw, str):
        raise ExtractError("html must be a string")
    if not 0 < max_bytes <= 8_388_608:
        raise ExtractError("max_bytes must be 1..8388608")
    p = _Text(keep_links, max_bytes)
    try:
        p.feed(raw)
        p.close()
    except Exception as e:                       # malformed input
        raise ExtractError("parse failed: %s" % e)
    text = "".join(p.parts)
    text = html.unescape(text)                  # one final pass, then stop
    lines = []
    for line in re.split(r"\n+", text):
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
    out = "\n".join(lines)
    truncated = p.truncated
    if len(out.encode("utf-8")) > max_bytes:
        cut = out.encode("utf-8")[:max_bytes].decode("utf-8", "ignore")
        out, truncated = cut, True
    return {"text": out, "chars": len(out),
            "lines": out.count("\n") + 1 if out else 0,
            "truncated": truncated,
            "links_refused": p.links_refused,
            "keep_links": bool(keep_links)}
