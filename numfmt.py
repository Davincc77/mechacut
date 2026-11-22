"""Deterministic number formatting, parsing and rounding (Bundle 4).

decimal.Decimal throughout the rounding path — never float arithmetic.
Locale and currency tables are CLOSED and owned here (no platform locale
dependency): same input, same bytes, on any machine.

Parsing stance mirrors date/parse: ambiguity is REFUSED, not guessed —
a lone separator followed by exactly three digits requires an explicit
prefer="decimal" | "group".
"""

import re
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR, \
    ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_DOWN, ROUND_UP


class NumberError(Exception):
    pass


LOCALES = {
    "en-US": {"group": ",", "decimal": ".", "cur": "prefix"},
    "en-GB": {"group": ",", "decimal": ".", "cur": "prefix"},
    "fr-FR": {"group": "\u00A0", "decimal": ",", "cur": "suffix"},
    "de-DE": {"group": ".", "decimal": ",", "cur": "suffix"},
    "es-ES": {"group": ".", "decimal": ",", "cur": "suffix"},
    "it-IT": {"group": ".", "decimal": ",", "cur": "suffix"},
    "pt-BR": {"group": ".", "decimal": ",", "cur": "suffix"},
    "nl-NL": {"group": ".", "decimal": ",", "cur": "suffix"},
    "sv-SE": {"group": "\u00A0", "decimal": ",", "cur": "suffix"},
    "pl-PL": {"group": "\u00A0", "decimal": ",", "cur": "suffix"},
    "tr-TR": {"group": ".", "decimal": ",", "cur": "prefix"},
    "ja-JP": {"group": ",", "decimal": ".", "cur": "prefix"},
    "zh-CN": {"group": ",", "decimal": ".", "cur": "prefix"},
}

CURRENCIES = {
    "USD": "$", "EUR": "\u20AC", "GBP": "\u00A3", "JPY": "\u00A5",
    "CNY": "\u00A5", "CHF": "CHF", "CAD": "CA$", "AUD": "A$",
    "BRL": "R$", "MXN": "MX$", "ARS": "AR$", "COP": "COL$",
    "INR": "\u20B9", "XOF": "CFA", "MAD": "DH", "TND": "DT",
    "ZAR": "R", "SGD": "S$", "NZD": "NZ$", "KRW": "\u20A9",
}
# currencies whose minor unit is the whole unit (0 decimals by default)
ZERO_DECIMALS = {"JPY", "KRW", "VND", "ISK", "CLP"}

_MODES = {
    "half_even": ROUND_HALF_EVEN, "half_up": ROUND_HALF_UP,
    "half_down": ROUND_HALF_DOWN, "ceil": ROUND_CEILING,
    "floor": ROUND_FLOOR, "trunc": ROUND_DOWN, "up": ROUND_UP,
}


def _dec(value):
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise NumberError("value must be a number, not a boolean")
    if isinstance(value, (int, float)):
        # str() on floats is the shortest round-trip repr — deterministic
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value.strip())
        except InvalidOperation:
            raise NumberError("invalid numeric string: %r" % value)
    raise NumberError("value must be a number or numeric string")


def _plain(d):
    """Fixed-point string without exponent, trailing zeros kept as given."""
    s = format(d, "f")
    return s


def _group(intpart, sep):
    parts = []
    while len(intpart) > 3:
        parts.append(intpart[-3:])
        intpart = intpart[:-3]
    parts.append(intpart)
    return sep.join(reversed(parts))


def num_format(value, locale="en-US", style="number", currency=None,
               decimals=None, grouping=True):
    if locale not in LOCALES:
        raise NumberError("unknown locale: %r (closed table: %s)"
                          % (locale, ", ".join(sorted(LOCALES))))
    if style not in ("number", "currency", "percent"):
        raise NumberError('style must be "number", "currency" or "percent"')
    L = LOCALES[locale]
    d = _dec(value)
    sym = None
    if style == "currency":
        if not currency:
            raise NumberError("currency is required when style is currency")
        code = currency.upper()
        sym = CURRENCIES.get(code)
        if sym is None:
            raise NumberError("unknown currency: %r (closed table: %s)"
                              % (currency, ", ".join(sorted(CURRENCIES))))
    scale_dec = None
    if style == "percent":
        d = d * 100
    if decimals is None:
        if style == "currency":
            scale_dec = 0 if code in ZERO_DECIMALS else 2
        elif style == "percent":
            scale_dec = 2
    else:
        if not isinstance(decimals, int) or isinstance(decimals, bool) \
                or not (0 <= decimals <= 30):
            raise NumberError("decimals must be an integer 0-30")
        scale_dec = decimals
    shown = d.quantize(Decimal(1).scaleb(-scale_dec),
                       rounding=ROUND_HALF_EVEN) if scale_dec is not None \
        else d.normalize() if d == d.to_integral_value() else d
    text = _plain(shown)
    neg = text.startswith("-")
    text = text.lstrip("+-")
    if "." in text:
        intp, frac = text.split(".", 1)
    else:
        intp, frac = text, None
    if grouping:
        intp = _group(intp, L["group"])
    body = intp + (L["decimal"] + frac if frac is not None else "")
    if neg:
        body = "-" + body
    if style == "percent":
        out = body + "%"
    elif style == "currency":
        if L["cur"] == "prefix":
            if neg:
                out = "-" + sym + body.lstrip("-")
            else:
                out = sym + body
        else:
            out = body + "\u00A0" + sym
    else:
        out = body
    return {"formatted": out, "locale": locale, "style": style,
            "currency": (code if style == "currency" else None),
            "decimals": scale_dec}


def num_parse(text, prefer=None):
    if not isinstance(text, str) or not text.strip():
        raise NumberError("text must be a non-empty string")
    if prefer not in (None, "decimal", "group"):
        raise NumberError('prefer must be "decimal" or "group"')
    s = text.strip().replace("\u00A0", " ").replace("\u202F", " ")
    percent = False
    if s.endswith("%") or s.startswith("%"):
        percent = True
        s = s.strip("%").strip()
    sign0 = ""
    if s[:1] in ("+", "-") and s[1:2] not in "0123456789.,":
        sign0, s = s[0], s[1:].strip()
    currency = None
    up = s.upper()
    for code in sorted(CURRENCIES):          # ISO codes first, alphabetical
        if up.startswith(code) and (len(up) == len(code) or
                                    not up[len(code)].isalpha()):
            currency = code
            s = s[len(code):].strip()
            break
        if up.endswith(code) and (len(up) == len(code) or
                                  not up[-len(code) - 1].isalpha()):
            currency = code
            s = s[:-len(code)].strip()
            break
    if currency is None:
        first_sym = {}
        for code in sorted(CURRENCIES):
            first_sym.setdefault(CURRENCIES[code], code)
        for sym in sorted(first_sym, key=lambda x: (-len(x), x)):
            if s.startswith(sym) or s.endswith(sym):
                currency = first_sym[sym]
                s = (s[len(sym):] if s.startswith(sym)
                     else s[:-len(sym)]).strip()
                break

    m = re.match(r"^([+-]?)([\d\s.,']*)([eE][+-]?\d+)?$", s)
    if not m or not any(ch.isdigit() for ch in m.group(2)):
        raise NumberError("unparsable number: %r" % text)
    sign, digits, expo = m.groups()
    expo = expo or ""
    digits = digits.replace("'", "").replace(" ", "")
    dec_sep = None
    last_comma, last_dot = digits.rfind(","), digits.rfind(".")
    if last_comma >= 0 and last_dot >= 0:
        dec_sep = "," if last_comma > last_dot else "."
    elif last_comma >= 0 or last_dot >= 0:
        sep = "," if last_comma >= 0 else "."
        if digits.count(sep) > 1:
            dec_sep = None                      # grouping only: 1,234,567
        else:
            head, _, tail = digits.partition(sep)
            if len(tail) == 3 and len(head) <= 3:
                if prefer is None:
                    raise NumberError(
                        'ambiguous number: %r — "%s" could be a group or a '
                        'decimal separator; pass prefer="decimal" or '
                        'prefer="group"' % (text, sep))
                dec_sep = sep if prefer == "decimal" else None
            else:
                dec_sep = sep
    val = digits
    if dec_sep:
        other = "." if dec_sep == "," else ","
        val = val.replace(other, "")
        val = val.replace(dec_sep, ".")
    else:
        val = val.replace(",", "").replace(".", "")
    if not re.match(r"^\d*\.?\d*$", val) or val in ("", "."):
        raise NumberError("unparsable number: %r" % text)
    try:
        d = Decimal(sign0 + sign + val + expo)
    except InvalidOperation:
        raise NumberError("unparsable number: %r" % text)
    nd = d.normalize()
    return {
        "decimal_string": format(nd, "f"),
        "float": float(d),
        "is_integer": d == d.to_integral_value(),
        "currency": currency,
        "percent": percent,
    }


def num_round(value, places=0, mode="half_even", significant=False):
    d = _dec(value)
    if mode not in _MODES:
        raise NumberError("unknown mode: %r (one of %s)"
                          % (mode, ", ".join(sorted(_MODES))))
    if not isinstance(places, int) or isinstance(places, bool) \
            or not (0 <= places <= 30):
        raise NumberError("places must be an integer 0-30")
    if significant and places < 1:
        raise NumberError("significant digits must be >= 1")
    if significant:
        if d == 0:
            q = Decimal(0)
        else:
            exp = d.adjusted() - (places - 1)
            q = d.quantize(Decimal(1).scaleb(exp), rounding=_MODES[mode])
    else:
        q = d.quantize(Decimal(1).scaleb(-places), rounding=_MODES[mode])
    exact = format(q, "f")
    return {"result": exact, "float": float(q), "mode": mode,
            "places": places, "significant": significant,
            "changed": q != d}
