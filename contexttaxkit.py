"""contexttaxkit — /agent/context-tax : ce que VOTRE tools/list collé
coûte en fenêtre, par outil, et ce que rapporterait le contre-fait.

LA DOULEUR, mesurée huit fois en dix jours puis NOUVELLEMENT en
novembre 2026 — la colonne « combien » manquait chez nous :
- serverdex.io / dev.to 20-nov-2026 (run live du 20-nov sur
  13 716 serveurs répondants, 21 328 interrogés) : le MEDIAN coûte
  ≈4 847 tokens / 14 outils avant le premier mot ; le top 10 %
  ≈40 000 ; LE PLUS LOURD ≈241 000 — plus qu'une fenêtre 200k
  entière. Méthode publiée, citée verbatim : « characters of the raw
  definitions ÷ 4 (the floor — a real client frames each one with
  more) ».
- ondrej_ulehla, dev.to 14-nov-2026 : 35 633 serveurs comptés,
  median 2 518, et 45 dont le SEUL LISTING ne tient pas dans la
  fenêtre — « their tool list alone does not fit in the window they
  are supposed to work in ».
- r/mcp (poizin) top-50 npm, compteur Anthropic : un serveur de 16
  outils dépasse un serveur de 276 parce qu'UN SEUL outil pèse
  ≈21 800 tokens ; deux versions des MÊMES 27 outils : 8 497 → 22k
  tokens, la faute au détail du schema, pas au texte.
- besk.tech 21-nov : 19 serveurs, 738 définitions = ≈534 000 tokens
  (724/tool) ; un serveur de 21 outils charge 8 600 tokens par
  conversation et n'a pas été APPELÉ UNE fois en 30 jours.
- Reddit (myclaw) : « tool definitions alone ate 143,000 of
  200,000 tokens — 72 % of the context window vanished » ; (r/mcp)
  « 15+ servers burn 60,000 tokens before your agent reads a
  message ».
- Paul Irolla (Tokenade), correction de cadrage reprise chez minia2a
  11-nov : « the tool list is not paid once » — il est CHARGÉ PAR
  TOUR. La multiplication par les tours est donc LA réponse, pas un
  raffinement.
- apidog 16-nov : 4 serveurs stdio locaux = 11 923 tokens vs skill
  CLI 112 ; testdino nov-2026 : Playwright MCP 0.0.41→0.0.85, la
  facture par défaut a crû de 78 % (2 203→3 919 tokens) SANS QUE
  PERSONNE ne signe — la dérive de b97 a un prix, le prix nomme la
  dérive.

CA EXISTE DEJA : serverdex agrège les serveurs PUBLICS (classement,
pas le vôtre) ; Ulehla / besk / poizin publient LEURS runs ;
lap-score (pip) lint des serveurs mais exige install + serveur
vivant ; mcpaudit dit REJETÉ, mcp-surface dit CHANGÉ — aucun ne dit
COMBIEN. Nous : HTTP sans compte, listing COLLÉ, décomposition par
outil et par champ (name/description/schema), contre-fait names-only
chiffré, par-tour et $ si vous portez le prix. Zéro fetch, zéro
lancement, zéro LM.

LOIS FERMÉES :
1. MESURE = chaîne JSON CANONIQUE de la définition collée (clés
   triées par point de code, separators (",",":"), UTF-8 sans
   échappement ASCII — LE canon des pins de la maison, même serment
   que mcp-surface). chars = len(str), bytes = len(UTF-8) — les deux
   voyagent, l'ESTIMATE travaille sur les CHARS, méthode publiée.
2. ESTIMATEUR NOMMÉ, unique : ceil(chars ÷ 4), citée verbatim comme
   PLANCHER (« a real client frames each one with more »). Le GLOBAL
   est ceil(TOTAL_chars ÷ 4), JAMAIS la somme des ceil par outil —
   la méthode publiée divise le total ; divergence chiffrée dans les
   tests (vecteur à deux outils : 19 contre 20).
3. DÉCOMPOSITION ADDITIVE, testée à l'octet : chaque outil =
   framing (accolades + clés citées + deux-points + virgules) +
   valeurs des 7 champs contractuels (name, title, description,
   inputSchema, outputSchema, annotations, execution — spec
   2026-07-28) + autres clés COLLÉES, chacune NOMMÉE avec ses chars.
   Une clé « instructions » collée est du texte que le serveur fait
   payer — la classe tool-poisoning a une FACTURE ici, pas seulement
   un digest chez le frère.
4. CONTRE-FAITS NOMMÉS (la question que les runs publies ne rendent
   pas) : names-only = somme des chars de nom NU (le counterfait
   tool-search : « seul le NOM est chargé »), gain et multiplicateur
   ; drop-descriptions = total moins les valeurs description (la
   mesure r/mcp : « la consommation vient des descriptions, pas du
   nombre d'outils »).
5. PAR-TOUR : tokens_charges = estimate x turns (default 1), le
   correctif Irolla rendu ARITHMETIQUE. DOLLARS si — et seulement
   si — le PRIX est un ARGUMENT (string décimal, jamais une table :
   les prix des modèles bougent, nous ne les gardons pas en
   mémoire). usd = tokens_charges x prix / 10^6, Decimal, quantilé
   0.000001 HALF_UP.
6. FENÊTRE : defaut 200 000 (l'échelle publiée par TOUTES les
   sources, nommée comme échelle et non comme plafond d'un
   fournisseur) ; verdicts CLOSES FITS / OVERFLOWS_WINDOW (la classe
   « 45 serveurs qui ne tiennent pas »).
7. SEUILS NOMMÉS, famille b97 : 5 000 outils par appel ; noms
   non-vides et UNIQUES (doublon = classe shadowing, REFUSÉ, pas
   digesté) ; entrees non-objets REFUSÉES ; détail par outil : TOP
   100 (rang chars décroissant, égalité = ordre collé), le reste
   PLOYÉ en tiers agrégé nommé — la réponse doit tenir dans la
   poche d'un petit modèle, c'est le sujet même de l'outil.
8. FLAG CLOSED : SINGLE_TOOL_DOMINANT quand un outil porte >= la
   moitié des chars (la lecon poizin : 16 outils > 276 outils).

Doctrine : jamais de fetch, jamais d'horloge, aucun tokenizer
installable (un tokenizer TIERS rendrait le verdict dépendant d'une
version — la mesure est l'arithmétique des octets, l'estimateur est
NOMMÉ et son erreur est DECLARÉE). Zéro LM.
"""
import hashlib
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import ceil

MAX_TOOLS = 5000            # seuil nommé, famille mcp-surface
TOP_DETAIL = 100            # seuil nommé, loi 7
DEFAULT_WINDOW = 200000     # l'échelle publiée (Claude 200k, citée « used here only for scale »)

CONTRACT_FIELDS = ("name", "title", "description", "inputSchema",
                   "outputSchema", "annotations", "execution")

ESTIMATOR = ("ceil(chars / 4) on the canonical pasted definitions — "
             "the published floor estimator, quoted: 'characters of "
             "the raw definitions / 4 (the floor — a real client "
             "frames each one with more)' (serverdex.io, 20 Nov "
             "2026). Exact bytes travel beside it; no third-party "
             "tokenizer is installed here, on purpose.")

PROVENANCE = [
    "serverdex.io / dev.to 20-nov-2026: 21328 MCP servers asked, "
    "13716 answered; median ~4847 tokens / 14 tools; p90 ~40k; "
    "heaviest ~241k > a 200k window; method chars/4 quoted as floor",
    "dev.to ondrej_ulehla 14-nov-2026: 35633 servers counted, "
    "median 2518, 45 listings alone do not fit in 200k",
    "reddit r/mcp (poizin), top-50 npm via Anthropic counter: one "
    "tool ~21800 tokens makes 16 tools costlier than 276; same 27 "
    "tools 8497->22k tokens, schema detail alone",
    "besk.tech 21-nov-2026: 19 servers / 738 tools ~534k tokens "
    "(724/tool); a 21-tool server costs ~16500 per conversation, "
    "never called in 30 days",
    "reddit r/myclaw: definitions ate 143000 of 200000 tokens "
    "(72% of window); reddit r/mcp: 15+ servers burn 60000 tokens "
    "before the first message",
    "Paul Irolla (Tokenade) via minia2a 11-nov: 'the tool list is "
    "not paid once' — charged PER TURN",
    "apidog.com 16-nov-2026: four stdio servers = 11923 tokens vs "
    "CLI skill 112; testdino.com: Playwright MCP default listing "
    "grew 78% (2203->3919) between 0.0.41 and 0.0.85",
    "modelcontextprotocol.io spec 2026-07-28 server/tools (the "
    "seven contract fields; names unique per server)",
]


class ContextTaxError(Exception):
    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected


def _canon_str(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _measure_tool(tool, where):
    """L'arithmétique exacte de la définition canonique. Additif :
    framing + valeurs contractuelles + autres clés == len(canon)."""
    if not isinstance(tool, dict):
        raise ContextTaxError(where,
                              "tool entries must be objects — the "
                              "pasted tools/list member is not one",
                              "a JSON object")
    name = tool.get("name")
    if not isinstance(name, str) or name == "":
        raise ContextTaxError(where + ".name",
                              "tool name must be a non-empty string "
                              "(spec 2026-07-28: names identify the "
                              "tool; an unnamed tool cannot be "
                              "billed)",
                              "non-empty string")
    canon = _canon_str(tool)
    nkeys = len(tool)
    framing = 2 + (nkeys - 1 if nkeys > 0 else 0)   # accolades + virgules
    vals = {}
    other = {}
    for k, v in tool.items():
        if k in CONTRACT_FIELDS:
            framing += len(k) + 3                    # "key":
            vals[k] = len(_canon_str(v))
        else:
            # l'overhead de la clé INCONNUE voyage AVEC elle — sinon
            # il serait compté deux fois (assert additif ci-dessous,
            # qui a pêché exactement ce bug à l'écriture)
            other[k] = len(k) + 3 + len(_canon_str(v))
    total = len(canon)
    assert framing + sum(vals.values()) + sum(other.values()) == total, (
        "additivity broken on " + where)
    return {
        "name": name,
        "chars": total,
        "bytes": len(canon.encode("utf-8")),
        "framing": framing,
        "vals": vals,
        "other": other,
    }


def _est(chars):
    return ceil(chars / 4)


def _q2(x):
    return float(Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _share(part, whole):
    if whole <= 0:
        return 0.0
    return _q2(Decimal(part) * 100 / Decimal(whole))


def context_tax(tools, window=None, turns=None, input_per_mtok=None):
    # --- validations d'arguments, refus field+expected (contrat du 400)
    if window is None:
        window = DEFAULT_WINDOW
    if not isinstance(window, int) or isinstance(window, bool) or window < 1:
        raise ContextTaxError("window",
                              "window must be an integer >= 1 token "
                              "(the scale you measure against, e.g. "
                              "200000 — a 0 window would bill "
                              "everything as overflow)",
                              "integer >= 1")
    if turns is None:
        turns = 1
    if not isinstance(turns, int) or isinstance(turns, bool) or turns < 1:
        raise ContextTaxError("turns",
                              "turns must be an integer >= 1 — the "
                              "listing is charged per turn (Irolla "
                              "2026: 'the tool list is not paid "
                              "once'); zero turns is not a run",
                              "integer >= 1")
    price = None
    if input_per_mtok is not None:
        try:
            price = Decimal(str(input_per_mtok))
        except (InvalidOperation, ValueError):
            raise ContextTaxError(
                "input_per_mtok",
                "input_per_mtok must be a decimal STRING — the price "
                "per million input tokens YOU pay (e.g. \"2\" for "
                "$2/M). Never a stored table: model prices move",
                "decimal string >= 0, e.g. \"2\"")
        if not price.is_finite() or price < 0:
            raise ContextTaxError("input_per_mtok",
                                  "input_per_mtok must be a finite "
                                  "non-negative decimal — a negative "
                                  "price is a refund nobody publishes",
                                  "decimal string >= 0")

    if len(tools) > MAX_TOOLS:
        raise ContextTaxError("tools",
                              "listing too large: %d tools pasted, "
                              "ceiling %d per call (no real client "
                              "holds more — family threshold with "
                              "/agent/mcp-surface)" % (len(tools), MAX_TOOLS),
                              "at most 5000 tool entries")
    seen = set()
    measured = []
    for i, tool in enumerate(tools):
        m = _measure_tool(tool, "tools[%d]" % i)
        if m["name"] in seen:
            raise ContextTaxError(
                "tools[%d].name" % i,
                "duplicate tool name '%s' — spec 2026-07-28 names "
                "are unique per server; a pasted duplicate is the "
                "shadowing class, billed or measured nowhere honest"
                % m["name"],
                "unique tool names")
        seen.add(m["name"])
        measured.append(m)

    total_chars = sum(m["chars"] for m in measured)
    total_bytes = sum(m["bytes"] for m in measured)
    estimate = _est(total_chars)

    split = {
        "framing": sum(m["framing"] for m in measured),
        "name": sum(m["vals"].get("name", 0) for m in measured),
        "title": sum(m["vals"].get("title", 0) for m in measured),
        "description": sum(m["vals"].get("description", 0) for m in measured),
        "input_schema": sum(m["vals"].get("inputSchema", 0) for m in measured),
        "output_schema": sum(m["vals"].get("outputSchema", 0) for m in measured),
        "annotations": sum(m["vals"].get("annotations", 0) for m in measured),
        "execution": sum(m["vals"].get("execution", 0) for m in measured),
        "other_keys": sum(sum(m["other"].values()) for m in measured),
    }
    assert sum(split.values()) == total_chars, "split must add up"

    # --- rangs : chars décroissant, égalité = ordre collé (stable)
    ordered = sorted(range(len(measured)), key=lambda i: -measured[i]["chars"])
    per_tool = []
    shown_chars = 0
    for rank, idx in enumerate(ordered[:TOP_DETAIL], 1):
        m = measured[idx]
        shown_chars += m["chars"]
        other = m["other"]
        per_tool.append({
            "rank": rank,
            "name": m["name"],
            "chars": m["chars"],
            "bytes": m["bytes"],
            "token_estimate": _est(m["chars"]),
            "share_pct": _share(m["chars"], total_chars),
            "description_chars": m["vals"].get("description", 0),
            "schema_chars": (m["vals"].get("inputSchema", 0)
                             + m["vals"].get("outputSchema", 0)),
            "unknown_keys": sorted(other.keys()) if other else [],
        })
    folded = None
    if len(measured) > TOP_DETAIL:
        rest_chars = total_chars - shown_chars
        folded = {"tools": len(measured) - TOP_DETAIL,
                  "chars": rest_chars,
                  "token_estimate": _est(rest_chars)}

    # --- contre-faits nommés (loi 4)
    names_chars = sum(len(m["name"]) for m in measured)
    names_est = _est(names_chars)
    if names_chars > 0:
        mult = _q2(Decimal(total_chars) / Decimal(names_chars))
    else:
        mult = None
    drop_desc_chars = total_chars - split["description"]
    counterfactual = {
        "names_only_chars": names_chars,
        "names_only_estimate": names_est,
        "names_only_multiplier": mult,
        "names_only_rule": ("bare name characters only — the "
                            "tool-search counterfactual ('seul le NOM "
                            "est chargé'); client framing is NOT "
                            "counted, the same declared floor"),
        "drop_descriptions_chars": drop_desc_chars,
        "drop_descriptions_estimate": _est(drop_desc_chars),
        "drop_descriptions_rule": ("total minus every pasted "
                                   "description value — the r/mcp "
                                   "measurement: cost lives in "
                                   "descriptions, not tool counts"),
    }

    flags = []
    if not measured:
        flags.append("EMPTY_LISTING")
    elif len(measured) >= 2:
        # dominance STRICTE (rangs déjà triés) : un relevé de deux
        # outils EGAUX ne « domine » pas — la classe poizin, c'est
        # UN outil qui porte la facture des autres
        top, second = measured[ordered[0]]["chars"], measured[ordered[1]]["chars"]
        if top * 2 >= total_chars and top > second:
            flags.append("SINGLE_TOOL_DOMINANT")

    verdict = "FITS" if estimate <= window else "OVERFLOWS_WINDOW"
    out = {
        "model": "agent/context-tax",
        "tools": len(measured),
        "total_chars": total_chars,
        "total_bytes": total_bytes,
        "token_estimate": estimate,
        "estimator": ESTIMATOR,
        "split": split,
        "per_tool": per_tool,
        "folded": folded,
        "counterfactual": counterfactual,
        "window": {
            "tokens": window,
            "pct_of_window": _share(estimate, window),
            "verdict": verdict,
            "note": ("window is an ARGUMENT measured against, the "
                     "200k scale published by every source cited — "
                     "not a vendor ceiling"),
        },
        "per_turn": {
            "turns": turns,
            "tokens_charged": estimate * turns,
            "rule": ("definitions ride EVERY turn (Irolla 2026: the "
                     "tool list is not paid once) — this line is "
                     "estimate x turns"),
        },
        "flags": flags,
        "provenance": PROVENANCE,
    }
    if price is not None:
        usd = (Decimal(out["per_turn"]["tokens_charged"]) * price
               / Decimal(1000000)).quantize(Decimal("0.000001"),
                                            rounding=ROUND_HALF_UP)
        out["price"] = {
            "input_per_mtok": str(price),
            "usd_for_this_run": str(usd),
            "rule": ("tokens_charged x your price / 10^6, exact "
                     "decimal — the price is YOUR argument; we "
                     "store no model price table (0xadityaa 16-nov "
                     "copied Sonnet 5.5 $2/M input, $0.10 cache "
                     "hit — a table would rot, an argument doesn't)"),
        }
    return out


def sha256_of(obj):  # helper de test, le canon maison
    return hashlib.sha256(_canon_str(obj).encode("utf-8")).hexdigest()
