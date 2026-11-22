"""displaykit — /api/v1/csv/excel_display : ce que Excel AFFICHE d'une
valeur STOCKÉE sous un code numFmt — le RENDU, pas le dommage.

La preuve est un papier MESURÉ (arXiv 2611.05806, « Measuring and
Mitigating Divergences in Office Documents ») : la cellule B9 stocke
1 000 000 sous le format « $#,##0, » — la VIRGULE TRAILLANTE SCALE
par mille — et Excel affiche $1,000. Les SIX extracteurs python
(markitdown, openpyxl, pandas, unstructured, calamine, Docling)
rejettent la valeur STOCKÉE ; l'agent lit 1 000 000, l'humain voit
$1,000, et « le budget spreadsheet » est approuvé sur deux chiffres
DIFFÉRENTS. L'attaque numFmt leurres les quatre assistants de test et
trois des quatre coding agents dans au moins 9 essais sur 10. Le
second papier (arXiv 2608.25880) nomme la famille : « representation
divergence » — stored ≠ displayed ≠ cached ≠ recalculated.

LA SPEC DU RENDU est la table publiée des symboles Microsoft (« Control
settings in the Format Cells dialog box », learn.microsoft.com), avec
SES EXEMPLES RÉSOLUS, rejoués en tests :
  « #.0,, » + 12 200 000 → « 12.2 »    (deux virgules = ÷1 000 000)
  « (000)  » + 12         → « (012) »  (0 = remplit de zéros)
  « 0%     » + 0,5        → « 50% »    (% = ×100 ET signe)
  « 0.00 "dollars" » + 1,23 → « 1.23 dollars »
  « 1.2345 » sous « 0.00 » → « 1.23 »  (le STOCKÉ ne change pas)
  « #.##   » + 8,9        → « 8.9 »    (# = pas de zéro inutile)

GRAMMAIRE FERMÉE, refuser par le NOM est le contrat : General
(dépend de la LARGEUR de colonne — MS Q&A 12760109 le dit), E-notation,
codes de date/heure (m/d/y/h = sémantique des sériels, autre monde),
couleurs [Red], conditions [<100], placeholder texte @, sections de
texte (4 sections), remplissages * et _ (fonction de la largeur).
Ce qui reste : 0 # ? en parties entière et décimale, virgule de
groupement ENTRE les placeholders, virgules TRAILLANTES après le
dernier placeholder = mise à l'échelle ×1000ᵏ (« , » scale par mille,
« ,, » par million — table MS), %, littéraux $ + - ( ) / espace : et
"quoted" (\escape), sections positif;négatif;zero (max 3), arrondi de
DISPLAY demi-vers-le-large sur l'absolue (2,5 sous « 0 » → « 3 »,
l'inverse de banker's — déclaré dans la réponse), et la LOCALE en
argument : l'ingénieur Microsoft (MS Q&A 945311) déclare les
séparateurs du FICHIER invariant (« File content is always written in
English ») et l'AFFICHAGE suit les réglages de l'utilisateur — donc
« . » et « , » du code sont des SYMBOLES rendus avec la locale
fournie, jamais recopiés bruts quand locale ≠ en-US.

Sous-lot RENDU annoncé derrière /csv/excel_damage (v0.81.0, qui
PRÉDIT le dommage à l'import) : deux outils, deux questions —
« que va-t-il détruire » vs « que va-t-il montrer ». L'appelant donne
le STOCKÉ (que give openpyxl/pandas renvoient déjà) et le CODE
(styles.xml) ; la machine rend ce que l'ŒIL aurait vu. Zéro XLSX
ouvert, zéro fetch.
"""

import re
from decimal import Decimal, ROUND_HALF_UP

from numfmt import LOCALES

_SECTIONS_MAX = 3
_DIGIT_CHARS = "#0?%,."      # % et . restent « core » ; , traité à part


class DisplayError(ValueError):
    def __init__(self, field, message, expected=None):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected or _DISPLAY_EXPECTED.get(field, "")


_DISPLAY_EXPECTED = {
    "value": "the STORED number as a decimal string, exactly as "
             "openpyxl/pandas return it, e.g. '1000000' or "
             "'25604.880000000001'",
    "format": "the numFmt code string from styles.xml: 0 # ? digits, "
              ". separator, , grouping or trailing scaling, % percent, "
              "literals $ + - ( ) / space : \"quoted\" \\escapes; up "
              "to 3 sections pos;neg;zero",
    "locale": "display locale for separators (" +
              ", ".join(sorted(LOCALES)) + ") — file codes are "
              "locale-invariant per Microsoft; DISPLAY follows the "
              "user, so this is an argument",
}


def _strip_literals_edges(sec):
    """Sépare littéraux de tête/queue du PATTERN de chiffres.
    Respecte "quotes" et \\escapes. ',' est « core » : les virgules
    de mise à l'échelle TRAILLANTES (« #.0,, ») vivent dans le core."""
    chars = "#0?%.,"
    n = len(sec)
    i = 0
    while i < n and sec[i] not in chars:
        if sec[i] == "\\" and i + 1 < n:
            i += 2
        elif sec[i] == '"':
            j = sec.find('"', i + 1)
            if j < 0:
                raise DisplayError("format", "unbalanced quote in %r"
                                   % sec)
            i = j + 1
        else:
            i += 1
    prefix, core = sec[:i], sec[i:]
    j = len(core)
    while j > 0 and core[j - 1] not in chars:
        back = core[:j - 1]
        if core[j - 1] == ")" or core[j - 1] in "$+ -/ :%":
            j -= 1
            continue
        # queue commençant par une quote fermée : remonter à l'ouverte
        if '"' in back and back.count('"') % 2 == 1:
            j = back.rfind('"')
            continue
        if core[j - 1] == "\\" and j >= 3 and core[j - 2] != "\\":
            j -= 1
            continue
        j -= 1
    suffix = core[j:]
    core = core[:j]
    return prefix, core, suffix


def _split_sections(fmt):
    secs, cur, in_q, i = [], [], False, 0
    while i < len(fmt):
        ch = fmt[i]
        if ch == "\\":
            cur.append(ch)
            if i + 1 < len(fmt):
                cur.append(fmt[i + 1])
                i += 1
        elif ch == '"':
            in_q = not in_q
            cur.append(ch)
        elif ch == ";" and not in_q:
            secs.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    secs.append("".join(cur))
    while secs and secs[-1] == "":
        secs.pop()
    if len(secs) > _SECTIONS_MAX:
        raise DisplayError("format", "more than %d sections — 4-section "
                           "formats carry a TEXT section, outside the "
                           "numeric subset" % _SECTIONS_MAX)
    return secs


_DATE_RE = re.compile(r"[mdyhMDYH]")
_REFUSALS = [
    ("general", "General display depends on COLUMN WIDTH (MS Q&A "
                "12760109: narrow columns drop decimals silently) — "
                "not deterministic; pass the explicit code"),
    ("@", "@ text placeholder: the cell is text, not a number"),
    ("*", "* repeat-fill depends on column width (MS symbol table)"),
    ("_", "_ skip-width depends on column width (MS symbol table)"),
    ("[", "bracketed codes ([h]:mm elapsed time, [Red] colour, [<100] "
          "conditions) are date/colour/conditional semantics"),
    ("E-notation", None),
]


def _refuse(sec):
    if re.search(r"general", sec, re.I):
        raise DisplayError("format", _REFUSALS[0][1])
    naked = re.sub(r'"[^"]*"', "", sec)
    naked = re.sub(r"\\.", "", naked)
    if re.search(r"[eE]\s*[+-]", naked) or re.search(r"[eE]0", naked):
        raise DisplayError("format", "scientific E-notation is outside "
                           "the closed numeric subset")
    for ch, msg in _REFUSALS[1:]:
        if ch in naked and msg:
            raise DisplayError("format", msg)
    if _DATE_RE.search(naked):
        raise DisplayError("format", "date/time code (m, d, y, h) — "
                           "serial-date rendering is a different "
                           "semantic world, refused by name")
    return sec


def _unescape_lit(text):
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            out.append(text[i + 1])
            i += 2
        elif ch == '"':
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _parse_core(core):
    """→ (int_pattern, frac_pattern, scaling, pct_count)."""
    if not core:
        raise DisplayError("format", "empty numeric section")
    pct = len(core) - len(core.rstrip("%"))
    core = core[:-pct] if pct else core
    if "%" in core:
        raise DisplayError("format", "the % symbol must sit after the "
                           "digit placeholders, got %r" % core)
    scaling = 0
    # virgules TRAILLANTES après le dernier placeholder = scaling
    while core.endswith(","):
        scaling += 1
        core = core[:-1]
    if core.count(".") > 1:
        raise DisplayError("format", "more than one decimal separator — "
                           "not a closed numeric code")
    if "." in core:
        int_p, frac_p = core.split(".", 1)
    else:
        int_p, frac_p = core, ""
    if not re.search(r"[#0?]", int_p + frac_p):
        raise DisplayError("format", "no digit placeholder (0/#/?) — "
                           "%r carries no number" % core)
    if not re.match(r"^[#0?,]*$", int_p):
        raise DisplayError("format", "unsupported characters in integer "
                           "pattern %r" % int_p)
    if not re.match(r"^[#0?]*$", frac_p):
        raise DisplayError("format", "unsupported characters in decimal "
                           "pattern %r (no grouping or scaling comma "
                           "right of the separator)" % frac_p)
    if "," in int_p:
        if int_p.count(",") > 1:
            raise DisplayError("format", "more than one grouping comma — "
                               "lakh-style '##,##,###' grouping is "
                               "outside the closed subset")
        if not re.search(r"[#0?],[#0?]", int_p):
            raise DisplayError("format", "the grouping comma must sit "
                               "BETWEEN digit placeholders (e.g. #,##0), "
                               "got %r" % int_p)
    return int_p, frac_p, scaling, pct


def _render_int(int_p, digits, group_ch):
    pad0 = int_p.count("0")
    padq = pad0 + int_p.count("?")
    grouped = "," in int_p
    s = digits
    if len(s) < pad0:
        s = s.rjust(pad0, "0")
    elif len(s) < padq:
        s = s.rjust(padq, " ")
    if grouped:
        chunks = []
        while len(s) > 3:
            chunks.insert(0, s[-3:])
            s = s[:-3]
        chunks.insert(0, s)
        return group_ch.join(chunks)
    return s


def _render_frac(frac_p, fdigits):
    """fdigits : décimales du NOMBRE ARRONDI (longueur == len(frac_p))."""
    # dernière décimale SIGNIFICATIVE (non nulle)
    last_sig = -1
    for i, d in enumerate(fdigits):
        if d != "0":
            last_sig = i
    out = []
    for i, ph in enumerate(frac_p):
        d = fdigits[i]
        if ph == "0":
            out.append(d)
        elif ph == "?":
            out.append(" " if (d == "0" and i > last_sig) else d)
        else:  # '#'
            if i <= last_sig:
                out.append(d)
            elif d != "0":
                out.append(d)
            # sinon : rien (zéro insignificant non affiché)
    return "".join(out)


def _render_one(value, sec, dec_sep, group_ch):
    prefix, core, suffix = _strip_literals_edges(sec)
    int_p, frac_p, scaling, pct = _parse_core(core)
    rules = []
    v = value
    if pct:
        v = v * (Decimal(100) ** pct)
        rules.append("pct ×100 per symbol (%d symbol(s); MS table: "
                     "code '0%%' turns 0.5 into 50%%)" % pct)
    if scaling:
        v = v / (Decimal(1000) ** scaling)
        rules.append("trailing comma scaling ÷1000^%d — the MS table "
                     "example: '#.0,,' shows 12,200,000 as 12.2"
                     % scaling)
    places = len(frac_p)
    av = abs(v)
    if places:
        q = av.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    else:
        q = av.quantize(Decimal(1), rounding=ROUND_HALF_UP)
    rules.append("display rounding HALF-AWAY-FROM-ZERO to %d decimal(s) "
                 "(2.5 under '0' → 3) — the stored value NEVER changes, "
                 "only the display" % places)
    text = format(q, "f")
    ipd, _, fpd = text.partition(".")
    fpd = (fpd + "0" * places)[:places]
    body = _render_int(int_p, ipd, group_ch)
    if places:
        body += dec_sep + _render_frac(frac_p, fpd)
    body += "%" * pct   # % = ×100 ET signe affiché (table MS)
    rendered = _unescape_lit(prefix) + body + _unescape_lit(suffix)
    return rendered, rules


def run_display(args):
    raw = args.get("value")
    if not isinstance(raw, str) or not raw.strip():
        raise DisplayError("value", "missing or empty (decimal string, "
                           "exactly as stored)")
    try:
        value = Decimal(raw.strip())
    except Exception:
        raise DisplayError("value", "not a decimal number: %r" % raw)
    fmt = args.get("format")
    if not isinstance(fmt, str) or not fmt.strip():
        raise DisplayError("format", "missing or empty (the numFmt code "
                           "from styles.xml)")
    fmt = fmt.strip()
    locale = (args.get("locale") or "en-US").strip()
    if locale not in LOCALES:
        raise DisplayError("locale", "unknown locale %r (closed table)"
                           % locale)
    dec_sep = LOCALES[locale]["decimal"]
    group_ch = LOCALES[locale]["group"]

    secs = _split_sections(fmt)
    for s in secs:
        _refuse(s)
    neg, zero = value < 0, value == 0
    if len(secs) == 1:
        sec, used = secs[0], ("1 (single section: negatives get a "
                              "leading '-' because no second section "
                              "exists)")
        body, rules = _render_one(value, sec, dec_sep, group_ch)
        display = ("-" + body) if neg else body
    else:
        if zero and len(secs) >= 3:
            sec, used = secs[2], "3 (zero section)"
        elif neg and len(secs) >= 2:
            sec, used = secs[1], "2 (negative section)"
        elif zero:
            sec, used = secs[0], ("1 (two-section format: zero renders "
                                  "through the positive section)")
        else:
            sec, used = secs[0], "1 (positive section)"
        display, rules = _render_one(value, sec, dec_sep, group_ch)

    return {
        "stored": format(value, "f"),
        "format": fmt,
        "displayed": display,
        "locale": locale,
        "separators_note": "the code's '.' and ',' are SYMBOLS only — "
                           "Microsoft: file content is locale-invariant; "
                           "display follows the supplied locale (de-DE "
                           "renders 1.234,56 with the same code)",
        "section_used": used,
        "rules_applied": rules,
        "stored_unchanged": "sums and formulas still use the stored "
                            "value — only what the EYE sees is rendered",
        "refused_outside_subset": [
            "General (column-width dependent)",
            "scientific E-notation",
            "date/time codes (m d y h, [h]:mm)",
            "[Red] colour codes and [<] conditions",
            "* fill and _ skip (column-width dependent)",
            "@ text placeholder (4-section formats)",
        ],
        "scope_note": "stored value and numFmt code are SUPPLIED "
                      "(openpyxl/pandas give the stored value; "
                      "styles.xml gives the code) — nothing fetched, "
                      "no XLSX opened; answers 'what would the human "
                      "see', the divergence arXiv 2611.05806 measures",
    }
