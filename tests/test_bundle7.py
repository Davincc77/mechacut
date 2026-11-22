"""Bundle 7.1 — text tools: boundary-exact, permutation-exact."""

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _twice(url, payload):
    r1 = client.post(url, json=payload)
    r2 = client.post(url, json=payload)
    assert r1.content == r2.content
    return r1


def test_text_count():
    r = _twice("/api/v1/text/count",
               {"text": "Bonjour le monde. Ça va ?\n\nDeuxième ligne."})
    b = r.json()
    assert b["sentences"] == 3 and b["paragraphs"] == 2
    assert b["words"] == 7 and b["lines"] == 3
    assert b["chars"] == len("Bonjour le monde. Ça va ?\n\nDeuxième ligne.")
    assert b["bytes"] > b["chars"]  # UTF-8 accents counted right


def test_sort_natural():
    r = _twice("/api/v1/sort/natural",
               {"items": ["file10.txt", "file2.txt", "file1.txt",
                          "File20.txt"]})
    # 20 > 10: File20 lands LAST even case-folded — numbers compare as
    # numbers, letters case-fold; that is the closed total order here
    assert r.json()["sorted"] == ["file1.txt", "file2.txt", "file10.txt",
                                  "File20.txt"]
    assert sorted(r.json()["permutation"]) == list(range(4))
    r = client.post("/api/v1/sort/natural", json={"items": ["b", "a"],
                                                  "reverse": True})
    assert r.json()["sorted"] == ["b", "a"]
    r = client.post("/api/v1/sort/natural", json={"items": [1, 2]})
    assert r.status_code == 400


def test_text_case_roundtrip():
    for text, op, expected in [
            ("parseHTTPResponseCode", "snake", "parse_http_response_code"),
            ("hello_world-again", "pascal", "HelloWorldAgain"),
            ("Mechanically Inclined", "kebab", "mechanically-inclined"),
            ("some_title here", "camel", "someTitleHere"),
            ("x y", "sentence", "X y")]:
        r = client.post("/api/v1/text/case", json={"text": text, "op": op})
        assert r.json()["result"] == expected, (text, op, r.json())


def test_text_truncate_boundaries():
    r = _twice("/api/v1/text/truncate",
               {"text": "Un deux trois quatre cinq", "max": 3,
                "unit": "words"})
    assert r.json()["output"] == "Un deux trois…"
    r = client.post("/api/v1/text/truncate",
                    json={"text": "Aa bbbb ccccc d", "max": 7,
                          "unit": "chars", "strategy": "word"})
    assert r.json()["output"] == "Aa…"
    r = client.post("/api/v1/text/truncate",
                    json={"text": "Première phrase. Deuxième. Troisième.",
                          "max": 1, "unit": "sentences"})
    b = r.json()
    assert b["output"] == "Première phrase.…" and b["removed_units"] == 2
    r = client.post("/api/v1/text/truncate",
                    json={"text": "short", "max": 10, "unit": "chars"})
    assert r.json()["truncated"] is False
    r = client.post("/api/v1/text/truncate",
                    json={"text": "x", "max": 0, "unit": "chars"})
    assert r.status_code == 400


def test_regex_modes():
    r = _twice("/api/v1/regex/test",
               {"pattern": r"(?P<k>\w+)=(?P<v>\d+)", "text": "a=1 bb=22",
                "mode": "groups"})
    assert r.json()["named"] == {"k": "a", "v": "1"}
    r = client.post("/api/v1/regex/test",
                    json={"pattern": r"\d+", "text": "a1 bb22 c333",
                          "mode": "findall"})
    assert [m["text"] for m in r.json()["matches"]] == ["1", "22", "333"]
    r = client.post("/api/v1/regex/test",
                    json={"pattern": r"(\w)", "text": "abc",
                          "mode": "replace", "template": "[$1]"})
    assert r.json()["result"] == "[a][b][c]"
    r = client.post("/api/v1/regex/test",
                    json={"pattern": r"(\w)", "text": "abc",
                          "mode": "replace", "template": r"[\1]"})
    assert r.json()["result"] == "[a][b][c]"  # both dialects
    r = client.post("/api/v1/regex/test",
                    json={"pattern": r"(", "text": "abc"})
    assert r.status_code == 400 and r.json()["error"] == "regex_failed"
    r = client.post("/api/v1/regex/test",
                    json={"pattern": r"a", "text": "x" * 65537})
    assert r.status_code == 400  # ReDoS blast-radius cap
    r = client.post("/api/v1/regex/test",
                    json={"pattern": r"a", "text": "A", "flags": "iq"})
    assert r.status_code == 400  # closed flag set


# ------------------------------------------------------- lot 7.2: chunk

def test_chunk_deterministic_and_budgeted():
    txt = ("Le déterminisme est un contrat. Chaque requête identique "
           "produit des octets identiques. C'est ainsi que l'on a envoyé "
           "des hommes sur la lune avec 4 Ko de RAM. Mechacut répond une "
           "fois, pour toujours. Un modèle donne du sens ; Mechacut fait "
           "la mécanique. Pas de stockage, pas de réseau, pas d'excuses.")
    r = _twice("/api/v1/text/chunk", {"text": txt, "budget": 40,
                                      "overlap": 10})
    b = r.json()
    assert b["encoding"] == "cl100k_base" and b["count"] == len(b["chunks"])
    for c in b["chunks"]:
        assert c["tokens"] <= 40
    texts = [c["text"] for c in b["chunks"]]
    assert all(t in txt for t in texts)
    import re
    joined = re.sub(r"\s+", "", "".join(texts))
    assert set(re.sub(r"\s+", "", txt)) <= set(joined)  # coverage
    assert sorted({c["char_start"] for c in b["chunks"]}) == \
        sorted(c["char_start"] for c in b["chunks"])  # offsets ordered


def test_chunk_hard_cut():
    r = client.post("/api/v1/text/chunk",
                    json={"text": "mot " * 200, "budget": 12,
                          "unit": "paragraph"})
    b = r.json()
    assert b["count"] > 1
    assert all(c["tokens"] <= 12 for c in b["chunks"])


def test_chunk_refusals():
    r = client.post("/api/v1/text/chunk", json={"text": "x", "budget": 5,
                                                "overlap": 5})
    assert r.status_code == 400
    r = client.post("/api/v1/text/chunk", json={"text": "x", "budget": 0})
    assert r.status_code == 400
    r = client.post("/api/v1/text/chunk", json={"text": "x",
                                                "encoding": "bpe-9000"})
    assert r.status_code == 400


def test_md_render_closed_subset():
    md = ("# Titre — Méthode\n\nTexte **gras** *it* `c`.\n\n- un\n- deux\n\n"
          "| A | B |\n|---|---|\n| 1 | [x](https://e.org) |\n\n"
          "> cite\n\n```python\nprint(1)\n```\n")
    r = _twice("/api/v1/md/render", {"markdown": md, "heading_ids": True})
    h = r.json()["html"]
    assert '<h1 id="titre-methode">' in h
    assert "<strong>gras</strong>" in h and "<em>it</em>" in h
    assert "<thead><tr><th>A</th><th>B</th></tr></thead>" in h
    assert '<a href="https://e.org">x</a>' in h
    assert '<code class="language-python">' in h
    assert "<blockquote><p>cite</p></blockquote>" in h


def test_md_render_escapes_and_refuses():
    # a URL containing parentheses is outside the closed link syntax ->
    # it stays text (no refusal needed); without them, javascript: fires
    r = client.post("/api/v1/md/render",
                    json={"markdown": "[x](javascript:alert)"})
    assert r.status_code == 400
    r = client.post("/api/v1/md/render",
                    json={"markdown": "[x](javascript:alert(1))"})
    assert r.status_code == 200 and "javascript" in r.json()["html"]
    assert "<a" not in r.json()["html"]
    r = client.post("/api/v1/md/render",
                    json={"markdown": "<b>safe</b> & <i>"})
    h = r.json()["html"]
    assert "&lt;b&gt;safe&lt;/b&gt;" in h
    # unclosed fence closes at EOF, documented leniency
    r = client.post("/api/v1/md/render", json={"markdown": "```\ncode"})
    assert "<pre><code>code</code></pre>" in r.json()["html"]


# ------------------------------------------------------ lot 7.3: html

PAGE = '''<html><head><title>T</title><style>.a{}</style></head><body>
<h1>Bonjour</h1><script>var x="caché";</script>
<p>Un   paragraphe avec
des   espaces.</p><ul><li>item&nbsp;1</li><li>a &amp; b</li></ul>
<a href="https://mechacut.studio">le site</a>
<a href="javascript:evil()">piège</a></body></html>''' 


def test_html_text_canonical():
    r = _twice("/api/v1/html/text", {"html": PAGE})
    b = r.json()
    t = b["text"]
    assert "caché" not in t and ".a{}" not in t and "<" not in t
    assert t.splitlines()[:2] == ["Bonjour", "Un paragraphe avec"]
    assert "a & b" in t and "item\xa01" in t  # nbsp decoded once
    assert "(https" not in t and b["links_refused"] == 0
    assert b["truncated"] is False


def test_html_text_keep_links():
    r = client.post("/api/v1/html/text", json={"html": PAGE,
                                               "keep_links": True})
    b = r.json()
    assert "le site (https://mechacut.studio)" in b["text"]
    assert "piège" in b["text"] and "javascript" not in b["text"]
    assert b["links_refused"] == 1


def test_html_text_cap_and_leniency():
    r = client.post("/api/v1/html/text", json={"html": PAGE,
                                               "max_bytes": 20})
    assert r.json()["truncated"] is True
    r = client.post("/api/v1/html/text", json={"html": "<p>unclosed <b>x"})
    assert r.status_code == 200
    r = client.post("/api/v1/html/text",
                    json={"html": "x", "max_bytes": 0})
    assert r.status_code == 400
