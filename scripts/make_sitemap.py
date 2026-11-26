# -*- coding: utf-8 -*-
"""make_sitemap — the human-facing surface, as one byte-stable XML.

Deterministic: closed page list, fixed order, no crawl-time guessing. The
sitemap IS the promise: every URL a search engine should see, nothing it
should not. Re-running changes bytes only when the list changes.
"""
import datetime
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://mechacut.studio"

# HTML pages first (what a person lands on), then the agent-facing text
# surfaces a searcher may legitimately want (the registry, the payouts).
PAGES = [
    ("/", "daily"),
    ("/proposals", "daily"),
    ("/PAYOUTS", "monthly"),
    ("/route", "weekly"),
    ("/recipes", "weekly"),
    ("/SKILL-KIT.md", "weekly"),
    ("/SKILL-NETWORK.md", "weekly"),
    ("/SKILL-MINI.md", "weekly"),
    ("/SKILL.md", "weekly"),
    ("/agent/manifest", "daily"),
]


def build(today=None) -> str:
    day = today or datetime.date.today().isoformat()
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, freq in PAGES:
        out.append(f"  <url><loc>{BASE}{path}</loc>"
                   f"<lastmod>{day}</lastmod><changefreq>{freq}</changefreq>"
                   f"<priority>{'1.0' if path == '/' else '0.8'}</priority></url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    body = build()
    (ROOT / "static" / "sitemap.xml").write_text(body, encoding="utf-8")
    print(f"sitemap generated: {len(PAGES)} urls -> static/sitemap.xml")
