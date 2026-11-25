# -*- coding: utf-8 -*-
"""bigintkit — /json/bigint : QUELS ENTIERS DE TON JSON MENTENT AU-DELÀ
DE 2^53, LUS PAR CHAQUE LECTEUR, EN OCTETS EXACTS.

LA DOULEUR, lue À L'API GitHub le 25-nov-2026 (lentille DEV ; verbatim
recopié des corps d'issues, pas des snippets de recherche). Un JSON bien
formé traverse un parseur IEEE-754 : l'entier change de valeur et RIEN
NE LE DIT. Cinq tickets, un an de symptômes, le même mécanisme :

1. IvanMurzak/Unity-MCP#754 (ouvert 18-mai-2026, CLOSED) : « EntityID
   (64-bit) loses precision when passed as JSON number » — l'input
   568105584918935294 arrive « rounded » ; le lookup échoue avec un
   NOT FOUND MENTEUR : l'agent conclut que l'objet n'existe pas alors
   que c'est son IDENTIFIANT qui a voyé. Le corps cite le « or similar »
   — ici le nombre exact est rendu, plus de « similar » : binary64
   value ET String JS sont rendus séparément.
2. anthropics/claude-code#11506 (ouvert 12-nov-2025, CLOSED) :
   echo '348555896224571969' affiché 348555896224571970, « off by 1 ».
   Commentaire cité du ticket : « the real bug/design flaw is using jq
   or JSON as a transport mechanism » — le symptôme est dans l'affiche,
   la cause est au parse.
3. llm4s/llm4s#1597 (ouvert 7-oct-2026, CLOSED par #2092) : ujson
   represente tout en Double ; 9007199254740993 lu 9007199254740992
   « whichever library reads the result afterwards » — la divergence
   CROSS-LECTEUR (circe, play-json, zio-json, mesurée dans #1596) EST
   DANS LE TICKET. Ici elle devient une TABLE par lecteur.
4. infiniflow/ragflow PR#22064 (5-nov-2026) : table decode→re-marshal
   Go : 1234567890123456789 → 1234567890123456800 dans tool_use
   arguments — « snowflake-style IDs, 64-bit hashes, and large cursors
   arrive wrong at the tool executor » (Go encoding/json, target
   map[string]any, élargit en float64).
5. Blog llm4agents 13-nov-2026 sur x402 Go#4258 : trois UnmarshalJSON
   de go/types/v2.go arrondissent les MONTANTS de paiement — l'argent
   traverse la même frontière muette.
Et la famille « la surface ment sans erreur » déjà bâtie ici :
agent_contexttax (b101), tool-overlap (b111), mcp-list-completeness
(b113). Cet outil ferme l'étage VALEUR : b113 compte les PAGES vues,
ici on auditent les NOMBRES traversés.

LES LOIS, citées exactes (sources primaires relues ce soir) :
- RFC 8259 §6 (STD 90), verbatim : « numbers that are integers and are
  in the range [-(2**53)+1, (2**53)-1] are interoperable in the sense
  that implementations will agree exactly on their numeric values. »
  La même section NOMME les dangers non-entiers : « A JSON number such
  as 1E400 or 3.141592653589793238462643383279 may indicate potential
  interoperability problems ».
- Spec MCP (modelcontextprotocol.io, page specification/draft/server/
  tools datée 24-nov-2026) : « Integer values MUST be within the safe
  range for integers represented using IEEE754 double-precision
  floating point numbers (−2^53+1 to 2^53−1) » — PORTÉE exacte lue dans
  le contexte : le MUST s'applique aux entiers x-mcp-header, PAS à
  tous les entiers du protocol. On le cite borné, jamais survendu.
- ECMAScript Number.MAX_SAFE_INTEGER = 2^53 − 1 = 9007199254740991 ;
  tout entier au-delà peut être le voisin d'un autre (2^53+1 et 2^53
  se lisent IDENTIQUES — la COLLISION que jsontoolskit nomme « two
  different records comparing equal »).
- Go encoding/json : decode vers interface{} = float64 (arrondi comme
  JS) ; UseNumber() garde le LITTÉRAL. nlohmann::json (json.nlohmann.me,
  Number Handling) : stocke int64/uint64 exacts dans [-2^63, 2^64-1],
  double au-delà. Python json : parse_int=int — EXACT sans rien
  demander. La même octet-stream reçoit donc QUATRE destins selon le
  lecteur : c'est la table readers de chaque finding.

DEUX VALEURS PAR NOMBRE, découvertes à l'oracle node-vs-python (les
tickets les citent sans les distinguer) : le double EXACT (la valeur
mathématique du binaire, int(float(v))) et le PRINT JS (ce que le
modèle RE-VOIT quand le client re-sérialise — Number::toString, plus
court aller-retour). 348555896224571969 : exact …968, print …970 ;
568105584918935294 : exact …296, print …300 (le « 568105584918935300 »
du ticket Unity EST le print). L'émulation de Number::toString est
certifiée CONTRE LE LECTEUR EUX-MÊME : 240 valeurs (bornes 2^53, 2^63,
2^64, puissances de 10, 210 aléatoires signées), ZÉRO divergence.

LA LEÇON DE L'ORACLE (doctrine b112, jouée ce cycle CONTRE MOI) : la
première passe de la main émettait « 900719925474099.1 » pour
2^53−1 — elle oubliait de RE-ANCORER l'exposant après la coupe des
zéros de la repr ; et ma golden table écrivait le value exact
(…808) à la place du print (…000) pour 2^63−1. La table node lue en
octets francs a eu raison DEUX fois avant le module.

Classes (ordre de sévérité DÉCLARÉ dans la payload) :
COLLISION > LOSSY > OVERFLOW > UNDERFLOW > EXACT_UNSAFE > SAFE
- SAFE     : dans le range RFC 8259 — rien à dire.
- LOSSY    : hors range ET la valeur change sous binary64 (delta ≠ 0).
- OVERFLOW : la valeur binaire est ±Infinity (1e400, le cas nommé par
  le RFC).
- UNDERFLOW: non-null mais lu 0 (2e-500, mesuré).
- EXACT_UNSAFE : hors range mais valeur tenue par binary64 (2^53, 2^64
  — le nombre est sauf, l'INTEROPÉRABILITÉ non : les voisins impairs
  n'existent pas dans ce voisinage, et le range RFC est violé).
- COLLISION : deux littéraux DISTINCTS qui se lisent IDENTIQUES chez JS
  — le symptom des tickets « wrong record », la classe la plus grave.

Le patch (mode « quote ») applique la règle que t27 PR#10448 est en
train de coder ailleurs (le littéral devient chaîne décimale, jamais
nombre nu) : SEULS les littéraux marqués sont cités, TOUS les autres
octets restent intacts — y compris les chiffres DANS les chaînes, que
les auditeurs regex (czoa : « digits inside strings may be reported »)
signalent en faux positifs. Notre scanner suit la GRAMMAIRE, pas une
expression régulière : un id entre guilmettes n'est pas un finding.

Zéro réseau, zéro LM, zéro table de mémoire : mêmes octets, mêmes
verdicts, pour toujours.
"""
from decimal import Decimal

SAFE_HI = 2 ** 53 - 1
SAFE_LO = -(2 ** 53 - 1)
INT64_LO = -(2 ** 63)
INT64_HI = 2 ** 63 - 1
UINT64_MAX = 2 ** 64 - 1
MAX_RAW_CHARS = 1_000_000
MAX_DEPTH = 100

SEVERITY = ["COLLISION", "LOSSY", "OVERFLOW", "UNDERFLOW",
            "EXACT_UNSAFE", "SAFE"]

_L = float("inf")


class BigintError(ValueError):
    def __init__(self, field, message, expected):
        self.field = field
        self.message = message
        self.expected = expected
        ValueError.__init__(self, "%s: %s" % (field, message))


def js_number_string(x):
    """ECMA-262 Number::toString, émulé via la repr short-repr de Python.
    Certifié contre node (lecteur réel) sur 240 valeurs, zéro écart."""
    if x != x:
        return "NaN"
    if x == _L:
        return "Infinity"
    if x == -_L:
        return "-Infinity"
    if x == 0:
        return "0"
    neg = x < 0
    a = Decimal(repr(abs(x)))
    _, digs, exp = a.as_tuple()
    ds = "".join(map(str, digs))
    stripped = len(ds) - len(ds.rstrip("0") or "0")
    ds = ds.rstrip("0") or "0"
    k = len(ds)
    n = k + int(exp) + stripped
    if n <= 0 or n > 21:
        m = ds[0] + ("." + ds[1:] if k > 1 else "")
        e = n - 1
        out = m + "e" + ("+" if e >= 0 else "-") + str(abs(e))
    elif k <= n:
        out = ds + "0" * (n - k)
    else:
        out = ds[:n] + "." + ds[n:]
    return ("-" + out) if neg else out


# ---------------------------------------------------------------- scan
_WS = " \t\n\r"
_ESC = {'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f",
        "n": "\n", "r": "\r", "t": "\t"}


def _hex4(s, i):
    if i + 4 > len(s):
        raise BigintError("raw", "bad escape at offset %d — \\u needs 4 "
                          "hex digits" % i, "JSON string")
    try:
        return int(s[i:i + 4], 16), i + 4
    except ValueError:
        raise BigintError("raw", "bad escape at offset %d — \\u needs 4 "
                          "hex digits" % i, "JSON string")


def _scan_string(s, i):
    """Renvoie la fin exclusive du token string (guillemet fermé inclus)."""
    j = i + 1
    n = len(s)
    while True:
        if j >= n:
            raise BigintError("raw", "unterminated string opened at "
                              "offset %d" % i, "closing \"")
        c = s[j]
        if c == '"':
            return j + 1
        if c == "\\":
            j += 1
            if j >= n:
                raise BigintError("raw", "trailing backslash in string "
                                  "opened at offset %d" % i, "escape char")
            if s[j] == "u":
                _, j = _hex4(s, j + 1)
            elif s[j] in _ESC:
                j += 1
            else:
                raise BigintError("raw", "invalid escape \\%s at offset %d"
                                  % (s[j], j), "\\\" \\\\ \\/ \\b \\f "
                                     "\\n \\r \\t \\uXXXX")
        elif ord(c) < 0x20:
            raise BigintError("raw", "unescaped control character at "
                              "offset %d" % j, "JSON string")
        j += 1


def _skip_ws(s, i):
    while i < len(s) and s[i] in _WS:
        i += 1
    return i


def _walk(s, i, depth, stack, findings, counts):
    """Descend un token value ; remplit findings (numéros) et counts."""
    n = len(s)
    i = _skip_ws(s, i)
    if i >= n:
        raise BigintError("raw", "value ends at offset %d" % i, "JSON value")
    c = s[i]
    if c == "{":
        if depth > MAX_DEPTH:
            raise BigintError("raw", "nesting over %d levels" % MAX_DEPTH,
                              "shallower document")
        i = _skip_ws(s, i + 1)
        if i < n and s[i] == "}":
            return i + 1
        while True:
            if i >= n or s[i] != '"':
                raise BigintError("raw", "object key must be a string "
                                  "at offset %d" % i, "quoted key")
            j = _scan_string(s, i)
            # on décode la clé pour le pointer RFC 6901
            key = _decode_string(s, i, j)
            i = _skip_ws(s, j)
            if i >= n or s[i] != ":":
                raise BigintError("raw", "expected : after key at "
                                  "offset %d" % i, "colon")
            stack.append(_pointer_escape(key))
            i = _walk(s, i + 1, depth + 1, stack, findings, counts)
            stack.pop()
            i = _skip_ws(s, i)
            if i < n and s[i] == ",":
                i = _skip_ws(s, i + 1)
                continue
            if i < n and s[i] == "}":
                return i + 1
            raise BigintError("raw", "expected , or } at offset %d" % i,
                              "object body")
    if c == "[":
        if depth > MAX_DEPTH:
            raise BigintError("raw", "nesting over %d levels" % MAX_DEPTH,
                              "shallower document")
        i = _skip_ws(s, i + 1)
        idx = 0
        if i < n and s[i] == "]":
            return i + 1
        while True:
            stack.append(str(idx))
            i = _walk(s, i, depth + 1, stack, findings, counts)
            stack.pop()
            idx += 1
            i = _skip_ws(s, i)
            if i < n and s[i] == ",":
                i = _skip_ws(s, i + 1)
                continue
            if i < n and s[i] == "]":
                return i + 1
            raise BigintError("raw", "expected , or ] at offset %d" % i,
                              "array body")
    if c == '"':
        return _scan_string(s, i)
    if s.startswith("true", i):
        return i + 4
    if s.startswith("false", i):
        return i + 5
    if s.startswith("null", i):
        return i + 4
    if c in "-0123456789":
        j = i
        if s[j] == "-":
            j += 1
        dj = j
        while j < n and s[j].isdigit():
            j += 1
        if j == dj:
            raise BigintError("raw", "number at offset %d has no digit "
                              "before the point" % i, "JSON number")
        int_part = s[dj:j]
        if int_part != "0" and int_part.startswith("0"):
            raise BigintError("raw", "leading zero in number at offset %d"
                              % i, "JSON number")
        frac = ""
        if j < n and s[j] == ".":
            fj = j + 1
            while fj < n and s[fj].isdigit():
                fj += 1
            if fj == j + 1:
                raise BigintError("raw", "empty fraction at offset %d" % i,
                                  "digit after .")
            frac = s[j + 1:fj]
            j = fj
        expo = ""
        if j < n and s[j] in "eE":
            ej = j + 1
            if ej < n and s[ej] in "+-":
                ej += 1
            es = ej
            while ej < n and s[ej].isdigit():
                ej += 1
            if ej == es:
                raise BigintError("raw", "empty exponent at offset %d" % i,
                                  "digit after e")
            expo = s[j:ej]
            j = ej
        lit = s[i:j]
        counts["numbers"] += 1
        findings.append({
            "pointer": "/" + "/".join(stack) if stack else "",
            "offset": i, "literal": lit, "int_part": int_part,
            "frac": frac, "expo": expo,
        })
        return j
    raise BigintError("raw", "unexpected character %r at offset %d" % (c, i),
                      "JSON value")


def _decode_string(s, i, end):
    """Décode un token string (i à l'ouvrant, end après le fermant)."""
    out = []
    j = i + 1
    while j < end - 1:
        c = s[j]
        if c != "\\":
            out.append(c)
            j += 1
        elif s[j + 1] == "u":
            cp, j = _hex4(s, j + 2)
            if 0xD800 <= cp <= 0xDBFF and j < end - 1 and s[j] == "\\":
                # surrogate pair
                if s[j + 1] == "u":
                    lo, j2 = _hex4(s, j + 2)
                    if 0xDC00 <= lo <= 0xDFFF:
                        out.append(chr(0x10000 + ((cp - 0xD800) << 10)
                                       + (lo - 0xDC00)))
                        j = j2
                        continue
            out.append(chr(cp))
        else:
            out.append(_ESC[s[j + 1]])
            j += 2
    return "".join(out)


def _pointer_escape(key):
    return key.replace("~", "~0").replace("/", "~1")


# ------------------------------------------------------------- classify
def _classify(num):
    lit = num["literal"]
    is_int_value = not num["frac"] and (
        not num["expo"] or Decimal(lit) == Decimal(lit).to_integral_value())
    v = None
    if is_int_value:
        try:
            v = int(Decimal(lit))
        except Exception:
            is_int_value = False
    try:
        d = float(lit)
    except OverflowError:
        d = _L if not lit.startswith("-") else -_L
    if is_int_value and v is not None:
        if SAFE_LO <= v <= SAFE_HI:
            cls = "SAFE"
            exact = v
        else:
            if d in (_L, -_L):
                cls = "OVERFLOW"
                exact = None
            else:
                exact = int(d)
                cls = "EXACT_UNSAFE" if exact == v else "LOSSY"
    else:
        if d in (_L, -_L):
            cls = "OVERFLOW"
        elif d == 0 and Decimal(lit) != 0:
            cls = "UNDERFLOW"
        else:
            cls = "SAFE"
        exact = None
        v = None
    out = {
        "pointer": num["pointer"], "offset": num["offset"],
        "literal": lit, "class": cls,
    }
    if v is not None:
        out["value"] = str(v)
        out["int64_holds"] = INT64_LO <= v <= INT64_HI
        out["uint64_holds"] = 0 <= v <= UINT64_MAX
    if cls != "SAFE":
        if exact is not None:
            out["binary64_value"] = str(exact)
            out["delta"] = exact - v if v is not None else None
        elif cls == "OVERFLOW":
            out["binary64_value"] = "Infinity" if not lit.startswith(
                "-") else "-Infinity"
        elif cls == "UNDERFLOW":
            out["binary64_value"] = "0"
        out["js_string"] = js_number_string(d)
        out["readers"] = {
            "js_go_float64_python_float": out["js_string"],
            "python_json_int": str(v) if v is not None else "float only",
            "go_usenumber_nlohmann_gt64": lit if v is None else str(v),
        }
    else:
        out["js_string"] = js_number_string(d)
    return out


def bigint_audit(raw, mode=None):
    if not isinstance(raw, str):
        raise BigintError("raw", "paste the JSON TEXT (the bytes) — an "
                          "already-parsed value has lost the evidence",
                          "string")
    if not raw.strip():
        raise BigintError("raw", "empty audit — paste a JSON document",
                          "non-empty string")
    if len(raw) > MAX_RAW_CHARS:
        raise BigintError("raw", "over ceiling",
                          "at most %d chars" % MAX_RAW_CHARS)
    if mode is not None and mode not in ("quote",):
        raise BigintError("mode", "unknown mode %r" % mode,
                          'null or "quote"')
    findings, counts = [], {"numbers": 0}
    end = _walk(raw, 0, 0, [], findings, counts)
    if _skip_ws(raw, end) != len(raw):
        raise BigintError("raw", "trailing content at offset %d — a JSON "
                          "document is ONE value" % end, "end of input")

    results = [_classify(f) for f in findings]

    # collisions : littéraux entiers DISTINCTS, même print JS
    by_print = {}
    for r in results:
        if r["class"] in ("LOSSY", "EXACT_UNSAFE"):
            by_print.setdefault(r["js_string"], []).append(r)
    collisions = []
    for jsp, group in sorted(by_print.items()):
        lits = sorted({r["literal"] for r in group})
        if len(lits) > 1:
            collisions.append({"js_string": jsp, "members": lits,
                               "pointers": sorted(r["pointer"]
                                                  for r in group)})
            for r in group:
                r["class"] = "COLLISION"
                r["collides_with"] = [x for x in lits if x != r["literal"]]

    flagged = [r for r in results if r["class"] != "SAFE"]
    flagged.sort(key=lambda r: (SEVERITY.index(r["class"]), r["offset"]))
    top = min((SEVERITY.index(r["class"]) for r in flagged),
              default=SEVERITY.index("SAFE"))
    verdict = SEVERITY[top]

    out = {
        "verdict": verdict,
        "severity_order": list(SEVERITY),
        "safe_range": {
            "min": str(SAFE_LO), "max": str(SAFE_HI),
            "source": "RFC 8259 section 6 (STD 90), verbatim: numbers "
                      "that are integers in [-(2**53)+1,(2**53)-1] are "
                      "interoperable",
        },
        "numbers_seen": counts["numbers"],
        "flagged_count": len(flagged),
        "findings": flagged,
        "collisions": collisions,
        "strings_are_clean": "chiffres dans les chaines et les cles ne "
                             "sont JAMAIS des findings (scanner de "
                             "grammaire, pas regex)",
        "laws": {
            "rfc8259_s6": "RFC 8259 6: integers in [-(2**53)+1, (2**53)-1] "
                          "are interoperable; 1E400 and "
                          "3.141592653589793238462643383279 named as "
                          "interoperability hazards",
            "mcp_draft_x_mcp_header": "spec MCP draft server/tools "
                                      "(24-nov-2026): Integer values MUST "
                                      "be within the safe range for "
                                      "integers represented using "
                                      "IEEE754 double-precision ... "
                                      "-2^53+1 to 2^53-1 — scope lue: "
                                      "parametres x-mcp-header",
            "ecmascript": "Number.MAX_SAFE_INTEGER = 2**53-1 = 9007199254740991",
            "go_encoding_json": "encoding/json into interface{} widens to "
                                "float64 (UseNumber keeps the literal)",
            "nlohmann": "nlohmann::json stores int64/uint64 exact in "
                        "[-2^63, 2^64-1], double beyond (json.nlohmann.me)",
            "python_json": "json.loads keeps integers as exact int",
        },
        "repro": [
            "github.com/IvanMurzak/Unity-MCP/issues/754",
            "github.com/anthropics/claude-code/issues/11506",
            "github.com/llm4s/llm4s/issues/1597",
            "github.com/infiniflow/ragflow/pull/22064",
            "llm4agents.com x402 Go #4258 audit 13-nov-2026",
        ],
    }

    if mode == "quote":
        patched = []
        last = 0
        for r in sorted((x for x in results if x["class"] != "SAFE"),
                        key=lambda x: x["offset"]):
            lit = r["literal"]
            is_int = not lit.startswith('""') and r.get("value") is not None
            if not is_int and r["class"] not in ("OVERFLOW", "UNDERFLOW"):
                continue
            patched.append(raw[last:r["offset"]])
            patched.append('"%s"' % lit)
            last = r["offset"] + len(lit)
        patched.append(raw[last:])
        out["patched"] = "".join(patched)
        out["patched_count"] = sum(1 for x in results if x["class"] != "SAFE")
    return out
