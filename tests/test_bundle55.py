# -*- coding: utf-8 -*-
"""bundle55 — les trois sentences signées : phrase COMPLÈTE × trois
langues, chacune une seule fois, dans son créneau. Le hero porte la
signature ; le catalogue et le hub de bancs portent leur thèse. Une
locale qui dérive, une phrase qui se duplique ou un créneau qui bouge
— ce test est rouge avant que le mensuel sorte."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "static" / "landing.html").read_text(encoding="utf-8")
LOCALES = {lang: json.loads((ROOT / "locales" / ("%s.json" % lang))
                            .read_text(encoding="utf-8"))
           for lang in ("en", "fr", "pt")}
HTML = {lang: re.sub(
    r"{{([a-zA-Z0-9_.]+)}}",
    lambda m, d=LOCALES[lang]: str(d.get(m.group(1), m.group(0))),
    TEMPLATE) for lang in LOCALES}

CREEDS = ("hero3", "bundles.creed", "bench.creed")


def test_three_creed_slots_in_template():
    assert ('<p class="creed">{{hero3}}<span class="sig"> — V. Cirilli'
            '</span></p>') in TEMPLATE
    assert ('<h2>{{bundles.h2}}</h2>\n      <p class="quote">'
            '{{bundles.creed}}</p>') in TEMPLATE
    assert ('<h2>{{bench.h2}}</h2>\n      <p class="quote">'
            '{{bench.creed}}</p>') in TEMPLATE


def test_creed_sentences_verbatim_each_language():
    for lang, html in HTML.items():
        for key in CREEDS:
            s = LOCALES[lang].get(key)
            assert s, (lang, key)
            assert html.count(s) == 1, (lang, key, html.count(s))


def test_hero3_carries_the_signature_once():
    for lang, html in HTML.items():
        s = LOCALES[lang]["hero3"]
        assert html.count(s + '<span class="sig"> — V. Cirilli</span>'
                         ) == 1, lang


def test_creeds_land_in_their_sections():
    # la devise du hero avant le catalogue ; chaque créneau sous son
    # propre h2 — un quiproquo de section est un mensonge de mise en
    # page, pas une cosmétique.
    for lang, html in HTML.items():
        assert (html.index(LOCALES[lang]["hero3"])
                < html.index(LOCALES[lang]["bundles.h2"]))
        assert (html.index(LOCALES[lang]["bundles.h2"])
                < html.index(LOCALES[lang]["bundles.creed"])
                < html.index(LOCALES[lang]["bench.h2"]))
        assert (html.index(LOCALES[lang]["bench.h2"])
                < html.index(LOCALES[lang]["bench.creed"]))


def test_sentences_are_ours_not_borrowed():
    # trace de la décision (22-11) : la phrase d'@explainx_ai a inspiré
    # le CRÉNEAU, pas le TEXTE — le landing ne quote pas un tiers et
    # ne signe pas un tiers. Si un texte d'emprunt entrait ici, ce
    # test n'est pas le rempart : la revue humaine l'est — d'où sa
    # présence comme artifact de décision.
    for html in HTML.values():
        assert "explainx" not in html.lower()
        assert "form you give it" not in html.lower()
