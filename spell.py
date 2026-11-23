"""Amounts in words (FR/EN/PT) — the invoice legal mention, deterministic.

Closed grammar, integer + cent units. Same amount, same language, same
words, forever. Not a model task: no LLM gets French "quatre-vingts" vs
"quatre-vingt" twice the same way.
"""

import re
from decimal import Decimal

from numfmt import _dec, NumberError


class SpellError(Exception):
    pass


_COMMON_ONES_EN = ["zero", "one", "two", "three", "four", "five", "six",
                   "seven", "eight", "nine", "ten", "eleven", "twelve",
                   "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
                   "eighteen", "nineteen"]
_TENS_EN = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty", 6: "sixty",
            7: "seventy", 8: "eighty", 9: "ninety"}
_ONES_FR = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept",
            "huit", "neuf", "dix", "onze", "douze", "treize", "quatorze",
            "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
_TENS_FR = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante",
            6: "soixante", 8: "quatre-vingt"}
_ONES_PT = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete",
            "oito", "nove", "dez", "onze", "doze", "treze", "catorze",
            "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
_TENS_PT = {2: "vinte", 3: "trinta", 4: "quarenta", 5: "cinquenta",
            6: "sessenta", 7: "setenta", 8: "oitenta", 9: "noventa"}


def _fr_small(n):
    if n < 20:
        return _ONES_FR[n]
    t, o = divmod(n, 10)
    if t == 1:
        return _ONES_FR[n]
    if t in (7, 9):
        base = _TENS_FR[t - 1]
        unit = n - 10 * (t - 1)
        if unit == 11:
            return base + " et onze"          # soixante et onze
        return base + "-" + _ONES_FR[unit]
    word = _TENS_FR[t]
    if o == 0:
        return word + ("s" if t == 8 else "")  # quatre-vingts
    if o == 1 and t != 8:
        return word + " et un"
    return word + "-" + _ONES_FR[o]


def _en_small(n):
    if n < 20:
        return _COMMON_ONES_EN[n]
    t, o = divmod(n, 10)
    if o == 0:
        return _TENS_EN[t]
    return _TENS_EN[t] + "-" + _COMMON_ONES_EN[o]


def _pt_small(n):
    if n < 20:
        return _ONES_PT[n]
    t, o = divmod(n, 10)
    if o == 0:
        return _TENS_PT[t]
    return _TENS_PT[t] + " e " + _ONES_PT[o]


def _hundred_fr(n):
    c, r = divmod(n, 100)
    out = []
    if c:
        if c == 1:
            out.append("cent")
        else:
            out.append(_ONES_FR[c] + (" cents" if r == 0 else " cent"))
    if r:
        out.append(_fr_small(r))
    return " ".join(out)


def _hundred_en(n):
    c, r = divmod(n, 100)
    out = []
    if c:
        out.append(_COMMON_ONES_EN[c] + " hundred")
    if r:
        out.append(_en_small(r))
    return " ".join(out)


_PT_HUNDREDS = {1: ("cem", "cento"), 2: "duzentos", 3: "trezentos",
                4: "quatrocentos", 5: "quinhentos", 6: "seiscentos",
                7: "setecentos", 8: "oitocentos", 9: "novecentos"}


def _hundred_pt(n):
    c, r = divmod(n, 100)
    head = None
    if c:
        head = ("cem" if r == 0 else "cento") if c == 1 else _PT_HUNDREDS[c]
    if r:
        tail = _pt_small(r)
        return (head + " e " + tail) if head else tail
    return head or _pt_small(0)


_LANGS = {
    "fr": {
        "small": _fr_small, "hundred": _hundred_fr,
        "scales": [("mille", None), ("million", "millions"),
                   ("milliard", "milliards"), ("billion", "billions")],
        "minus": "moins", "point": "virgule",
    },
    "en": {
        "small": _en_small, "hundred": _hundred_en,
        # pluriel anglais : JAMAIS. "two thousands" est une faute — la
        # table était héritée du motif FR/PT. Constaté par number_words_pair
        # au premier jour de vie (24-11) ; corrigé ici, version bump déclaré.
        "scales": [("thousand", "thousand"), ("million", "million"),
                   ("billion", "billion"), ("trillion", "trillion")],
        "minus": "minus", "point": "point",
    },
    "pt": {
        "small": _pt_small, "hundred": _hundred_pt,
        "scales": [("mil", None), ("milhão", "milhões"),
                   ("bilhão", "bilhões"), ("trilhão", "trilhões")],
        "minus": "menos", "point": "vírgula",
    },
}


def _split_triples(n_str):
    parts = []
    while len(n_str) > 3:
        parts.insert(0, n_str[-3:])
        n_str = n_str[:-3]
    parts.insert(0, n_str)
    return [int(p) for p in parts]


def spell_number(n, lang="fr"):
    if lang not in _LANGS:
        raise SpellError("unknown language: %r (closed: fr, en, pt)" % lang)
    L = _LANGS[lang]
    if n == 0:
        return L["small"](0)
    if n < 0:
        return L["minus"] + " " + spell_number(-n, lang)
    import re as _re
    triples = _split_triples(str(n))
    top = len(triples) - 1
    groups = []                                # (t, text) pairs
    for i, t in enumerate(triples):
        if t == 0:
            continue
        power = top - i
        txt = L["hundred"](t)
        if power == 0:
            groups.append((t, txt))
            continue
        # "cent"/"vingts" lose their plural s when a scale word follows
        txt = _re.sub(r" cents$", " cent", txt)
        txt = _re.sub(r"vingts$", "vingt", txt)
        sing, plural = L["scales"][power - 1]
        if plural is None:                     # mille / mil
            if t == 1:
                txt = sing                     # "mille", "mil"
            elif lang == "fr":
                txt = txt + " mille"
            else:
                txt = txt + " mil"
        else:
            txt = txt + " " + (plural if t > 1 else sing)
        groups.append((t, txt))
    out = ""
    for idx, (t, txt) in enumerate(groups):
        if idx == 0:
            out = txt
        elif lang == "pt" and t < 100:
            out += " e " + txt                 # closed pt rule: e before tail
        else:
            out += " " + txt
    return out


# (lang, ISO) -> (main_sing, main_plural, sub_sing, sub_plural)
_CURRENCY_WORDS = {
    ("fr", "EUR"): ("euro", "euros", "centime", "centimes"),
    ("fr", "USD"): ("dollar", "dollars", "cent", "cents"),
    ("fr", "CHF"): ("franc", "francs", "centime", "centimes"),
    ("fr", "GBP"): ("livre sterling", "livres sterling", "penny", "pence"),
    ("fr", "JPY"): ("yen", "yens", "", ""),
    ("fr", "CAD"): ("dollar canadien", "dollars canadiens", "cent", "cents"),
    ("fr", "XOF"): ("franc CFA", "francs CFA", "centime", "centimes"),
    ("fr", "MAD"): ("dirham", "dirhams", "centime", "centimes"),
    ("fr", "TND"): ("dinar", "dinars", "centime", "centimes"),
    ("fr", "BRL"): ("réel", "réels", "centavo", "centavos"),
    ("en", "EUR"): ("euro", "euros", "cent", "cents"),
    ("en", "USD"): ("dollar", "dollars", "cent", "cents"),
    ("en", "GBP"): ("pound", "pounds", "penny", "pence"),
    ("en", "JPY"): ("yen", "yen", "", ""),
    ("en", "CHF"): ("franc", "francs", "centime", "centimes"),
    ("en", "CAD"): ("dollar", "dollars", "cent", "cents"),
    ("en", "AUD"): ("dollar", "dollars", "cent", "cents"),
    ("en", "BRL"): ("real", "reals", "centavo", "centavos"),
    ("pt", "EUR"): ("euro", "euros", "cêntimo", "cêntimos"),
    ("pt", "BRL"): ("real", "reais", "centavo", "centavos"),
    ("pt", "USD"): ("dólar", "dólares", "centavo", "centavos"),
}


def num_spell(value, lang="fr", currency=None, cents=True, capital=False):
    """Amount -> words. `value` is a decimal amount (max 2 places). With
    `currency` (closed table) units are named and pluralized; without it
    the number is spelled with the locale's decimal-point word."""
    if lang not in _LANGS:
        raise SpellError("unknown language: %r (closed: fr, en, pt)" % lang)
    try:
        d = _dec(value)
    except NumberError as e:
        raise SpellError(str(e))
    if d != d.quantize(Decimal("0.01")):
        raise SpellError("amount must have at most 2 decimal places "
                         "(cents): %r" % value)
    L = _LANGS[lang]
    neg = d < 0
    d = abs(d)
    whole = int(d)
    frac = int((d - whole) * 100)
    pair = None
    if currency:
        pair = _CURRENCY_WORDS.get((lang, currency.upper()))
        if pair is None:
            raise SpellError("no words for currency %r in %r (closed table)"
                             % (currency, lang))
    parts = []
    if pair:
        parts.append(spell_number(whole, lang) + " "
                     + (pair[1] if whole > 1 else pair[0]))
        if frac:
            if not pair[2]:
                raise SpellError("%s has no sub-unit; amount must be whole"
                                 % currency.upper())
            parts.append(spell_number(frac, lang) + " "
                         + (pair[3] if frac > 1 else pair[2]))
    elif frac:
        parts = [spell_number(whole, lang), L["point"],
                 spell_number(frac, lang)]
    else:
        parts = [spell_number(whole, lang)]
    out = " ".join(parts)
    if neg:
        out = L["minus"] + " " + out
    if capital:
        out = out[0].upper() + out[1:]
    return {"words": out, "lang": lang,
            "currency": (currency.upper() if currency else None),
            "amount": ("-" if neg else "") + format(d, "f")}


# --------------------------------------------------------------------------
# number_words_pair — bundle 85. « Thirty (30) days » : la suite lit les
# DEUX formes, refuse de choisir quand elles se contredisent. L'index
# inverse est construit en épelant 0..9999 par les tables déjà vivantes —
# zero grammaire neuve, l'inversion est exactement le contrat de spell.
# --------------------------------------------------------------------------
_PAIR_RE = re.compile(
    r"([A-Za-z\u00c0-\u017f][A-Za-z\u00c0-\u017f' \u2011-]*?)\s*\(\s*"
    r"([0-9][0-9 .,\u00a0 ]{0,20})\s*\)")
_DIGITS_ONLY_RE = re.compile(r"\b\d[\d .,\u00a0]{0,19}\d\b|\b\d+\b")
_PAIR_LANGS = ("fr", "en", "pt")
_INDEX = {}


def _index():
    if _INDEX:
        return _INDEX
    for lang in _PAIR_LANGS:
        table = {}
        for i in range(10000):
            w = spell_number(i, lang).strip().lower()
            table.setdefault(w, i)
            w2 = w.replace(" and ", " ")
            if w2 != w:
                table.setdefault(w2, i)
        _INDEX[lang] = table
    return _INDEX


def _run_value(run):
    """Plus longue suffixe épelable du groupe de mots ; None si aucune."""
    words = [w for w in run.replace("\u2011", "-").lower().split() if w]
    if not words:
        return None
    for k in range(len(words)):
        tail = " ".join(words[k:])
        vals = {}
        for lang in _PAIR_LANGS:
            v = _index()[lang].get(tail)
            if v is not None:
                vals.setdefault(v, []).append(lang)
        if len(vals) == 1:
            v = next(iter(vals))
            return tail, v, sorted({l for ls in vals.values() for l in ls}), None
        if len(vals) > 1:
            return tail, None, sorted({l for ls in vals.values() for l in ls}), \
                "same words, different values across languages"
    return None


def _parse_numeric(raw):
    s = raw.replace("\u00a0", " ").strip()
    if re.match(r"^\d{1,3}(?:[ ,]\d{3})+(?:\.\d+|,\d+)?$", s):
        s = re.sub(r"[ ,](?=\d{3}\b)", "", s)
        return Decimal(s.replace(",", ".")), None
    m = re.match(r"^(\d+)([.,])(\d+)$", s)
    if m:
        if m.group(2) == ".":
            return Decimal(m.group(1) + "." + m.group(3)), None
        if len(m.group(3)) != 3:
            return Decimal(m.group(1) + "." + m.group(3)), None
        return None, "ambiguous decimal separator: %r" % raw
    if re.match(r"^\d+$", s):
        return Decimal(s), None
    return None, "unparseable numeric form: %r" % raw


def words_pair(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text is required and must not be empty")
    idx = _index()
    pairs, digit_only, ambiguous, warns = [], [], [], []
    consumed = []
    for m in _PAIR_RE.finditer(text):
        run, raw = m.group(1), m.group(2)
        parsed, err = _parse_numeric(raw)
        if err:
            ambiguous.append({"numeric": raw, "why": err})
            consumed.append((m.start(), m.end()))
            continue
        rv = _run_value(run)
        if rv is None:
            digit_only.append(raw.strip())
            consumed.append((m.start(), m.end()))
            continue
        spelled, value, langs, amb = rv
        if amb:
            warns.append("%s: %s" % (spelled, amb))
            digit_only.append(raw.strip())
            continue
        agree = parsed == Decimal(value)
        pairs.append({"words": spelled, "word_value": str(value),
                      "numeric": raw.strip(), "lang": langs[0]
                      if len(langs) == 1 else "+".join(langs),
                      "agree": bool(agree)})
        consumed.append((m.start(), m.end()))
    for m in _DIGITS_ONLY_RE.finditer(text):
        if any(a <= m.start() < b for a, b in consumed):
            continue
        digit_only.append(m.group(0).strip())
    if pairs and all(p["agree"] for p in pairs):
        verdict = "AGREE"
    elif any(not p["agree"] for p in pairs):
        verdict = "MISMATCH"
    else:
        verdict = "NO_PAIR"
    return {"verdict": verdict, "pairs": pairs,
            "counts": {"pairs": len(pairs), "digit_only": len(digit_only),
                       "ambiguous": len(ambiguous)},
            "digit_only": digit_only, "ambiguous": ambiguous,
            "warnings": warns}
