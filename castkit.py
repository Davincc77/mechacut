# -*- coding: utf-8 -*-
"""castkit — /api/v1/json/coerce : reparer les ARGUMENTS d'un appel
d'outil qu'un lecteur STRICT refuse, sans jamais rien deviner.

Douleur mesuree (docs/DEMAND-QUEUE, cycle 17h52, liens frais) :
 - yetone/magpie #3152 : les modèles écrivent les entiers avec une
   fraction nulle ("limit": 8.0, "yield_time_ms": 2500.0) ; serde lit
   u64 et refuse L'APPEL ENTIER — « invalid type: floating point
   2500.0, expected u64 » — mesuré 11/11 tours sur grok-4.6/4.7 via
   relay. Le fix publié (c272e55) énonce la grammaire : les entiers à
   fraction nulle deviennent notation entière ; fractions VRAIES,
   EXONENTS, chaînes et clés restent such as written. Ce module est
   cette grammaire, en HTTP, sans relay.
 - PraisonAI #6369 : le @tool saute le casting → "2"+"3" → "23" ;
   force="false" est truthy en Python → « wrong results with no
   error ». Nous ne fondons JAMAIS string→number en silence : c'est un
   argument explicite (cast_strings), et « 007 » refuse TOUJOURS
   (les zéros de tête sont du payload — téléphone, CNPJ, SIREN).

Notation preserve : json.loads perd la forme écrite (1.0e3 devient
1000.0). Les tokens littéraux sont capturés par parse_int/parse_float,
la sortie est RESERIALISEE à la main — « 1.0e3 » ressort « 1.0e3 »
(gauche as written, VERITE du scope note), « 8.0 » devient « 8 ».

Grammaire close : types = integer (non borné, l'entier JSON) |
u64|i64|32 (bornes nommées dans le refus) | number | string | boolean
| array<ces-scalaires>. Valeurs nulles hors grammaire : objet imbriqué
= laissee telle quelle, NOMMÉE (ce module cible des arguments plats,
ce que sont les tool-calls ; declared nested schemas = hors contrat).
"""
import json
import re

_TYPES = ("integer", "u64", "i64", "u32", "i32", "number", "string",
          "boolean")
_BOUNDS = {"u64": (0, 2**64 - 1), "i64": (-2**63, 2**63 - 1),
           "u32": (0, 2**32 - 1), "i32": (-2**31, 2**31 - 1)}
_INT_ARRAY_RE = re.compile(r"^-?(0|[1-9][0-9]*)$")
_NUM_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?$")
_LEADING_ZERO_RE = re.compile(r"^-?0[0-9]+$")


class CoerceError(Exception):
    def __init__(self, field, message, expected):
        Exception.__init__(self, message)
        self.field = field
        self.message = message
        self.expected = expected


# ---------- tokens litteraux (la notation est la donnee) ----------
class Tok(object):
    __slots__ = ("lit",)

    def __init__(self, lit):
        self.lit = lit

    @property
    def value(self):
        raise NotImplementedError


class IntTok(Tok):
    @property
    def value(self):
        return int(self.lit)


class FloatTok(Tok):
    @property
    def value(self):
        return float(self.lit)

    @property
    def has_exp(self):
        return "e" in self.lit or "E" in self.lit

    @property
    def whole(self):
        from fractions import Fraction
        return Fraction(self.lit).denominator == 1


class StrTok(Tok):
    @property
    def value(self):
        return self.lit


class BoolTok(Tok):
    @property
    def value(self):
        return self.lit


class NullTok(Tok):
    @property
    def value(self):
        return None


class ObjVal(object):
    """paires ordonnees, dupliquees detectees a la parse."""
    __slots__ = ("pairs",)

    def __init__(self, pairs):
        self.pairs = pairs


class ArrVal(object):
    __slots__ = ("items",)

    def __init__(self, items):
        self.items = items


def _pairs(p):
    seen = {}
    for k, v in p:
        seen[k] = True
    return ObjVal(p)


def _wrap(v):
    """Apres json.loads, seuls les NOMBRES sont des tokens (hooks
    parse_int/parse_float) ; les chaines, booleans, null et listes
    arrivent nus — l'arbre de travail doit etre 100 % tokens pour que
    la serialisation conserve la notation d'origine."""
    if isinstance(v, (IntTok, FloatTok, StrTok, BoolTok, NullTok,
                      ObjVal, ArrVal)):
        if isinstance(v, ObjVal):
            return ObjVal([(k, _wrap(x)) for k, x in v.pairs])
        return v
    if isinstance(v, list):
        return ArrVal([_wrap(x) for x in v])
    if v is None:
        return NullTok(v)
    if isinstance(v, bool):          # AVANT int : bool est un int en Python
        return BoolTok(v)
    if isinstance(v, int):
        return IntTok(str(v))
    if isinstance(v, float):          # inf/nan rejectes par json strict
        return FloatTok(repr(v))
    if isinstance(v, str):
        return StrTok(v)
    raise CoerceError("raw", "unhandled JSON value %r" % (v,),
                      "tool-call arguments object of scalars and "
                      "flat arrays")


def _parse_raw(raw):
    try:
        tree = json.loads(raw, parse_int=lambda s: IntTok(s),
                          parse_float=lambda s: FloatTok(s),
                          object_pairs_hook=_pairs)
    except ValueError as e:
        raise CoerceError("raw", "not valid JSON: %s" % (str(e)[:80],),
                          "the EXACT bytes of the tool-call arguments "
                          "object, e.g. '{\"limit\": 8.0}' — this "
                          "service repairs notation, it does not "
                          "repair syntax (that is json/repair)")
    tree = _wrap(tree)
    dup = _first_dup(tree)
    if dup:
        raise CoerceError(dup[0], "duplicate key %r in one object"
                          % (dup[0],),
                          "one value per key — which one wins is a "
                          "guess, and a deterministic product never "
                          "guesses (json/repair drops first by rule; "
                          "here the call is refused)")
    return tree


def _first_dup(node):
    if isinstance(node, ObjVal):
        keys = [k for k, _ in node.pairs]
        if len(keys) != len(set(keys)):
            for k in keys:
                if keys.count(k) > 1:
                    return (k,)
        for _, v in node.pairs:
            d = _first_dup(v)
            if d:
                return d
    elif isinstance(node, ArrVal):
        for it in node.items:
            d = _first_dup(it)
            if d:
                return d
    return None


# ---------- serialisation : litteraux conserves ----------
def _emit(node):
    if isinstance(node, ObjVal):
        return "{" + ", ".join("%s: %s" % (json.dumps(k), _emit(v))
                               for k, v in node.pairs) + "}"
    if isinstance(node, ArrVal):
        return "[" + ", ".join(_emit(x) for x in node.items) + "]"
    if isinstance(node, IntTok):
        return node.lit
    if isinstance(node, FloatTok):
        return node.lit
    if isinstance(node, StrTok):
        return json.dumps(node.value)
    if isinstance(node, BoolTok):
        return "true" if node.value else "false"
    if isinstance(node, NullTok):
        return "null"
    raise AssertionError("unreachable token %r" % (node,))


def _plain(node):
    if isinstance(node, ObjVal):
        return {k: _plain(v) for k, v in node.pairs}
    if isinstance(node, ArrVal):
        return [_plain(x) for x in node.items]
    return node.value if isinstance(node, Tok) else node


def _as_type(text):
    t = (text or "").strip().lower()
    if t.startswith("array<") and t.endswith(">"):
        inner = t[6:-1].strip()
        if inner in _TYPES:
            return ("array", inner)
        return ("array?", inner)
    if t in _TYPES:
        return ("scalar", t)
    return (None, None)


def _num_of(tok):
    return tok.value if isinstance(tok, (IntTok, FloatTok)) else None


def coerce_scalar(tok, t, path, cast_on, changes, kept, refused):
    """Retourne le token (coerce ou tel quel) apres application de la
    grammaire close. Les refus laissent la VALEUR TELLE QUELEE."""
    if t in ("integer", "u64", "i64", "u32", "i32"):
        if isinstance(tok, IntTok):
            b = _BOUNDS.get(t)
            if b and not (b[0] <= tok.value <= b[1]):
                refused.append({"path": path, "code": "BOUND",
                                "got": tok.lit,
                                "expected": "%s range %d..%d"
                                            % (t, b[0], b[1]),
                                "repair": "a value inside the "
                                          "declared bound, or declare "
                                          "'integer' (unbounded)"})
                return tok
            return tok
        if isinstance(tok, FloatTok):
            if tok.has_exp:
                kept.append({"path": path, "literal": tok.lit, "why":
                             "exponent notation LEFT AS WRITTEN — the "
                             "published fix scope (magpie #3152) does "
                             "not touch exponents, and strict readers "
                             "still reject this form; rewrite it at the "
                             "producer or drop the exponent yourself"})
                return tok
            from fractions import Fraction
            if tok.whole:
                iv = int(Fraction(tok.lit))
                b = _BOUNDS.get(t)
                if b and not (b[0] <= iv <= b[1]):
                    refused.append({"path": path, "code": "BOUND",
                                    "got": tok.lit,
                                    "expected": "%s range %d..%d"
                                                % (t, b[0], b[1]),
                                    "repair": "a value inside the "
                                              "declared bound"})
                    return tok
                changes.append({"path": path, "from": tok.lit,
                                "to": str(iv), "rule": "WHOLE_FLOAT"})
                return IntTok(str(iv))
            refused.append({"path": path, "code": "FRACTIONAL",
                            "got": tok.lit,
                            "expected": "%s — integer value required" % t,
                            "repair": "a whole number like 8 (a real "
                                      "fraction cannot reach an int "
                                      "slot without losing 0.5 — this "
                                      "service will NOT silently "
                                      "truncate it)"})
            return tok
        if isinstance(tok, StrTok):
            s = tok.value
            if _LEADING_ZERO_RE.match(s):
                refused.append({"path": path, "code": "LEADING_ZERO",
                                "got": s,
                                "expected": "declared %s, but the "
                                            "string carries payload "
                                            "zeros" % t,
                                "repair": "keep it a string — leading "
                                          "zeros are identifiers "
                                          "(phone, CNPJ, SIREN); "
                                          "casting '007' to 7 is the "
                                          "damage Excel does (see "
                                          "csv/excel_damage)"})
                return tok
            if _INT_ARRAY_RE.match(s):
                if cast_on:
                    iv = int(s)
                    b = _BOUNDS.get(t)
                    if b and not (b[0] <= iv <= b[1]):
                        refused.append({"path": path, "code": "BOUND",
                                        "got": s,
                                        "expected": "%s range %d..%d"
                                                    % (t, b[0], b[1]),
                                        "repair": "a value inside the "
                                                  "declared bound"})
                        return tok
                    changes.append({"path": path, "from": '"%s"' % s,
                                    "to": str(iv),
                                    "rule": "STRING_CAST"})
                    return IntTok(str(iv))
                kept.append({"path": path, "literal": '"%s"' % s,
                             "why": "numeric string in an int slot "
                                    "LEFT AS WRITTEN — '2'+'3' -> '23' "
                                    "is the PraisonAI #6369 bug this "
                                    "call exists to kill; pass "
                                    "cast_strings='on' to declare the "
                                    "cast"})
                return tok
            refused.append({"path": path, "code": "NOT_NUMBER",
                            "got": '"%s"' % s,
                            "expected": "%s literal" % t,
                            "repair": "an unquoted number, e.g. 8"})
            return tok
        refused.append({"path": path, "code": "NOT_NUMBER",
                        "got": _emit(tok), "expected": "%s literal" % t,
                        "repair": "an unquoted number, e.g. 8"})
        return tok

    if t == "number":
        if isinstance(tok, (IntTok, FloatTok)):
            return tok
        if isinstance(tok, StrTok) and _NUM_RE.match(tok.value):
            if cast_on:
                changes.append({"path": path, "from": '"%s"' % tok.value,
                                "to": tok.value,
                                "rule": "STRING_CAST_NOTATION_KEPT"})
                itok = IntTok(tok.value) if _INT_ARRAY_RE.match(
                    tok.value) else FloatTok(tok.value)
                return itok
            kept.append({"path": path, "literal": '"%s"' % tok.value,
                         "why": "numeric string kept — cast_strings="
                                "'on' declares the cast"})
            return tok
        refused.append({"path": path, "code": "NOT_NUMBER",
                        "got": _emit(tok), "expected": "number",
                        "repair": "an unquoted number"})
        return tok

    if t == "string":
        if isinstance(tok, StrTok):
            return tok
        if isinstance(tok, (IntTok, FloatTok)):
            if cast_on:
                changes.append({"path": path, "from": tok.lit,
                                "to": '"%s"' % tok.lit,
                                "rule": "NUMBER_CAST_NOTATION_KEPT"})
                return StrTok(tok.lit)
            kept.append({"path": path, "literal": tok.lit,
                         "why": "number in a string slot left as "
                                "written — quoting 8.0 as \"8.0\" "
                                "versus \"8\" is a decision, and "
                                "cast_strings='on' makes it explicit"})
            return tok
        refused.append({"path": path, "code": "NOT_STRING",
                        "got": _emit(tok), "expected": "string",
                        "repair": "a quoted string"})
        return tok

    if t == "boolean":
        if isinstance(tok, BoolTok):
            return tok
        if isinstance(tok, StrTok) and tok.value.strip().lower() in (
                "true", "false"):
            refused.append({"path": path, "code": "BOOL_TRUTHY",
                            "got": '"%s"' % tok.value,
                            "expected": "JSON literal true|false "
                                        "(unquoted)",
                            "repair": "write %s — the QUOTED 'false' "
                                      "is truthy in Python; that is "
                                      "force='false' from PraisonAI "
                                      "#6369"
                                      % tok.value.strip().lower()})
            return tok
        refused.append({"path": path, "code": "NOT_BOOLEAN",
                        "got": _emit(tok),
                        "expected": "JSON literal true|false",
                        "repair": "1 and 0 are NOT booleans here — a "
                                  "strict reader expects the literal"})
        return tok

    # unknown handled by caller
    return tok


def coerce_value(tok, kind, t, path, cast_on, changes, kept, refused):
    if kind == "array":
        if not isinstance(tok, ArrVal):
            refused.append({"path": path, "code": "NOT_ARRAY",
                            "got": _emit(tok),
                            "expected": "array<%s>" % t,
                            "repair": "wrap the value in [ ], or "
                                      "declare the scalar type"})
            return tok
        out = []
        for i, item in enumerate(tok.items):
            out.append(coerce_scalar(item, t, "%s[%d]" % (path, i),
                                     cast_on, changes, kept, refused))
        return ArrVal(out)
    if isinstance(tok, ObjVal):
        kept.append({"path": path, "literal": "{...}",
                     "why": "nested object outside the closed grammar "
                            "— this tool repairs FLAT tool-call "
                            "arguments; declare its inner keys at the "
                            "top level or leave it untouched"})
        return tok
    if tok is None or isinstance(tok, NullTok):
        refused.append({"path": path, "code": "NULL", "got": "null",
                        "expected": "%s" % t,
                        "repair": "pass a value or omit the key — "
                                  "this service never decides what "
                                  "null means for your slot"})
        return tok
    return coerce_scalar(tok, t, path, cast_on, changes, kept, refused)


def run_coerce(args):
    raw = args.get("raw")
    schema = args.get("schema")
    cast_on = _norm_flag(args.get("cast_strings"), "cast_strings")
    strict = _norm_flag(args.get("strict"), "strict")
    if not isinstance(raw, str) or not raw.strip():
        raise CoerceError("raw", "missing or empty",
                          "the exact JSON text of the tool-call "
                          "arguments, e.g. '{\"limit\": 8.0}'")
    if not isinstance(schema, dict) or not schema:
        raise CoerceError("schema", "missing or empty",
                          "{key: type} over the closed set "
                          "integer|u64|i64|u32|i32|number|string|"
                          "boolean|array<one of those>")
    tree = _parse_raw(raw)
    if not isinstance(tree, ObjVal):
        raise CoerceError("raw", "top level is not an object",
                          "'{...}' — tool-call arguments are an "
                          "object of parameters")

    # validation du schema AVANT de toucher aux valeurs : un schema
    # hors grammaire est refuse, pas ignore.
    kinds = {}
    for k, t in schema.items():
        kind, tt = _as_type(t if isinstance(t, str) else None)
        if kind is None:
            raise CoerceError("schema.%s" % k,
                              "unknown type %r" % (t,),
                              "closed set: integer|u64|i64|u32|i32|"
                              "number|string|boolean, or "
                              "array<integer> etc. — nothing else")
        kinds[k] = (kind, tt)

    changes, kept, refused = [], [], []
    declared = set(kinds)
    present = set(k for k, _ in tree.pairs)
    out_pairs = []
    for k, v in tree.pairs:
        if k in kinds:
            kind, tt = kinds[k]
            v2 = coerce_value(v, kind, tt, k, cast_on, changes, kept,
                              refused)
            out_pairs.append((k, v2))
        else:
            out_pairs.append((k, v))
    coerced_tree = ObjVal(out_pairs)
    out = {
        "coerced_text": _emit(coerced_tree),
        "coerced": _plain(coerced_tree),
        "changes": changes,
        "left_as_written": kept,
        "refused": refused,
        "undeclared_untouched": sorted(present - declared),
        "missing_keys": sorted(declared - present),
        "cast_strings": "on" if cast_on else "off",
        "strict": bool(strict),
        "rule": "magpie #3152 published grammar: whole floats in int "
                "slots become integer notation; exponents, real "
                "fractions, strings and keys stay EXACTLY as written; "
                "PraisonAI #6369 castings are opt-in (cast_strings), "
                "leading zeros never cast",
        "scope_note": "repairs notation against a declared schema — "
                      "it does not validate a business payload "
                      "(json/validate), does not fix syntax "
                      "(json/repair), and never guesses: every "
                      "refusal names field, expected and repair",
    }
    if strict and refused:
        raise _StrictRefused(refused)
    return out


def _norm_flag(v, field):
    if v is None:
        return False
    t = str(v).strip().lower()
    if t in ("on", "true", "yes"):
        return True
    if t in ("off", "false", "no"):
        return False
    raise CoerceError(field, "unknown flag value %r" % (v,),
                      "'on' or 'off' (also true/false) — booleans "
                      "here are strings with a closed grammar, "
                      "because quoted JSON bools are the very bug "
                      "this tool repairs")


class _StrictRefused(Exception):
    def __init__(self, refused):
        Exception.__init__(self, "strict mode: %d refusal(s)"
                           % len(refused))
        self.refused = refused
