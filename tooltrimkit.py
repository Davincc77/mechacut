# -*- coding: utf-8 -*-
"""tooltrimkit — /agent/tool-trim : QUOI DÉBRANCHER pour tenir le
budget de fenêtre, et le RE-COMPTE exact après.

LA DOULEUR, publiée et vécue (lentille DEV, rang 1 de la file du
cycle 2026-11-24 22h40) : les mesures externes disent COMBIEN coûte
une liste (context-tax, b101) et ce qu'a COÛTÉ l'update (cost-diff,
b104) ; elles ne disent jamais QUOI ENLEVER pour un budget — et le
re-compte après débranchage est le pas que chacun saute :
- r/ClaudeCode xalpx (fil 1y0l373, nov-2026) : « deactivated or
  removed any that hadn't received calls in the past 30 days » — la
  règle IDLE-first publiée PAR LE PRATICIEN, faite à la main sur ses
  logs, sans re-compte : il finit par « Is this a sensible setup? ».
- r/mcp sandeepK1125 (fil 1y0a4a2, nov-2026) : la première réponse
  demandée du fil : « Could you share how many tokens your servers
  used before and after trimming? » — le before/after chiffré EST la
  douleur nommée dans le fil.
- r/vscode mingl0280 (fil 1xf187y, nov-2026) : 160 outils contre une
  fenêtre 60k locale, « By deactivating some tools, we can drop down
  to around 20k, which fits » — un plan fait à l'œil, aux chiffres
  approximatifs, sur un petit modèle qui n'a pas la fenêtre.
- r/mcp simplymanas (fil 1y4jbnb, nov-2026) : 28 serveurs mesurés,
  médiane ~1 900 tokens, 4 dépassent 10k ; et en commentaire la GATE :
  « a test for each module that fails if the tools or list exceed a
  certain budget » — le FITS/STILL_OVER demandé EN CI.
- altrouter.dev (22-nov-2026) : 9 serveurs = 38 900 tokens = 19,4 %
  d'une fenêtre 200k ; « disable three unnecessary servers → $0.3099
  vs $0.7806, 60 % cheaper » — l'économie en dollars que personne ne
  calcule AVANT de débrancher.
- dev.to furqan (24-nov-2026) : 115 outils = 43 000 tokens avant le
  premier mot ; Beskorovainyi (21-nov, édité 23-nov) : « run a first
  pass BEFORE you disconnect, so the 'before' numbers exist ».
- apidog.dev (16-nov-2026) : la RÈGLE DE BUDGET publiée par un client
  réel — « auto : up front while definitions total under 10 % of the
  window » — rendue ici en ARGUMENT (budget_pct), floor déclaré.

CE QUI N'EXISTAIT PAS (question 5, payée 19h35) : context-tax dit
COMBIEN, cost-diff dit L'ÉCART, mcp-surface dit CHANGÉ — aucun ne dit
QUOI ENLEVER pour un budget donné, ni ne re-compte APRÈS. Externes :
/context du client arrondit aux centaines (Beskorovainyi l'écrit
lui-même), les filtres de serveurs changent sans compter. NOTRE
différenciation : le PLAN ordonné à critères EXACTS + le re-compte
GLOBAL au MÊME canon que les sœurs — collez les survivants dans
/agent/context-tax, le nombre doit être identique, octet à octet.

LOIS FERMÉES (le canon et l'estimateur de la FRATRIE sont obligatoires,
sinon le re-compte ne veut rien dire — leçon b104) :
1. MESURE = chaîne JSON canonique de chaque définition collée
   (contexttaxkit, sort_keys, separators (",",":"), UTF-8 non
   échappé). Estimateur NOMMÉ et unique : ceil(chars ÷ 4), plancher
   publié cité verbatim. Le TOTAL est ceil(total_chars ÷ 4), JAMAIS
   la somme des ceil par outil — la divergence entre les deux visages
   du chiffre est CHIFFRÉE dans la réponse, pas cachée.
2. BUDGET : budget (entier ≥ 1 tokens) OU budget_pct (1..100, règle
   apidog). budget_pct → budget_tokens = window × pct ÷ 100 en FLOOR
   entier exact — le floor ne promet jamais plus que l'énoncé
   (« under 10 % » dit under). Les deux à la fois = refus nommé
   (jamais les deux, contract de la maison).
3. ORDRE DES GOUTTES (classes CLOSES, critères en fractions EXACTES
   — jamais de flottant au critère, l'ordre d'un plan ne doit rien à
   IEEE-754) :
   a. IDLE_30J d'ABORD — calls_30d == 0 : payé chaque tour, jamais
      rendu (la règle xalpx, publiée par le praticien).
   b. RATIO ensuite — calls > 0, le PIRE coût par appel tombe avant
      le bon : ratio = chars ÷ calls en Fraction exacte, descendant.
   c. UNKNOWN en dernier — usage absent du relevé : on ne coupe pas
      ce qu'on n'a pas mesuré avant ce qu'on a mesuré inutile ;
      chaque goutte UNKNOWN est signalée en flag UNKNOWN_CUTS.
   Tie-breaks DÉCLARÉS : chars descendant, puis NOM ASCENDANT (b104).
4. keep : noms protégés — jamais gouttes. Chaque nom doit exister
   dans le listing (refus nommé). Si les gardés dépassent le budget
   SEULS, le verdict est STILL_OVER avec le RESTE chiffré — le plan
   ne devine pas votre garde-robe, il la mesure.
5. GREEDY : on retire dans l'ordre tant que ceil(chars survivants ÷ 4)
   > budget. Verdicts CLOSES : FITS_AS_IS (rien à débrancher —
   l'argent économisé EST zéro, comme NO_CHANGES chez la sœur),
   TRIMMED_FITS, STILL_OVER.
6. SAUVEGARDE PAR TOUR (Irolla : the tool list is not paid once) :
   saved × turns ; dollars SEULEMENT au prix décimal ARGUMENT de
   l'appelant — aucune table de prix, les prix pourrissent, les
   arguments non.
7. PLAFONDS famille b97 : 5 000 outils, noms non-vides et UNIQUES
   (doublon = shadowing refusé), entrées non-objets refusées ; détail
   Top 100 par liste, le reste plié en tiers nommé — la réponse doit
   tenir dans la poche du petit modèle, c'est le sujet de l'outil.

Doctrine : jamais de fetch, jamais d'horloge, aucun tokenizer tiers
installable — À DESSIN. Zéro LM.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from fractions import Fraction

import contexttaxkit as _ct
from contexttaxkit import ESTIMATOR, MAX_TOOLS, TOP_DETAIL, DEFAULT_WINDOW

PROVENANCE = [
    "r/ClaudeCode xalpx (fil 1y0l373, nov-2026): trimmed subagent MCP "
    "servers from his own session logs — 'deactivated or removed any "
    "that hadn't received calls in the past 30 days' — by hand, no "
    "recount, ends 'Is this a sensible setup?'",
    "r/mcp sandeepK1125 (fil 1y0a4a2, nov-2026): asked in-thread 'how "
    "many tokens did your servers use before and after trimming?' — "
    "the before/after recount IS the pain, in the reply to the pain",
    "r/vscode mingl0280 (fil 1xf187y, nov-2026): 160 tools against a "
    "60k local window, 'deactivating some tools we can drop down to "
    "around 20k, which fits' — eyeballed trim arithmetic",
    "r/mcp simplymanas (fil 1y4jbnb, nov-2026): 28 servers measured, "
    "median ~1,900 tokens, 4 over 10k; in-comment CI gate: a test "
    "fails when a tool list exceeds a stated budget",
    "altrouter.dev 22-nov-2026: 9 servers = 38,900 tokens = 19.4% of "
    "200k; 'disable three unnecessary servers -> $0.3099 vs $0.7806, "
    "60% cheaper' — real dollars nobody computes BEFORE disconnecting",
    "dev.to furqan 24-nov-2026: 115 tools = 43,000 tokens before the "
    "first word; Beskorovainyi 21-nov (edited 23-nov): 'run a first "
    "pass BEFORE you disconnect, so the before numbers exist'",
    "apidog.dev 16-nov-2026: budget rule published by a real client — "
    "'auto: up front while definitions total under 10% of the window'",
]


class ToolTrimError(Exception):
    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected


def _raise(field, message, expected):  # type: ignore # NoReturn below
    raise ToolTrimError(field, message, expected)


_raise.__annotations__["return"] = "NoReturn"


def _q2r(frac):
    """q2 pour une FRACTION exacte — Decimal(Fraction) n'est pas
    supporté, la quantification passe par numerator/denominator;
    la division se fait en Decimal (28 chiffres, largement assez
    pour un affichage à 2 décimales HALF_UP)."""
    return float((Decimal(frac.numerator) / Decimal(frac.denominator))
                 .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _measure_tools(tools):
    """Validation et mesure au canon des sœurs : SAME canon, SAME
    serment, SAME shape (leçon b104 — le re-compte ne veut dire
    quelque chose que mesuré identique)."""
    if len(tools) > MAX_TOOLS:
        _raise("tools",
               "listing too large: %d tools pasted, ceiling %d per "
               "call (same family threshold as /agent/context-tax "
               "and /agent/cost-diff)" % (len(tools), MAX_TOOLS),
               "at most 5000 tool entries")
    seen = set()
    measured = []
    for i, tool in enumerate(tools):
        try:
            m = _ct._measure_tool(tool, "tools[%d]" % i)
        except _ct.ContextTaxError as e:
            raise ToolTrimError(e.field, e.message, e.expected)
        if m["name"] in seen:
            _raise("tools[%d].name" % i,
                   "duplicate tool name '%s' — spec 2026-07-28 names "
                   "are unique per server; a pasted duplicate is the "
                   "shadowing class (same refusal as the sisters)"
                   % m["name"],
                   "unique tool names")
        seen.add(m["name"])
        measured.append(m)
    return measured


def _arg_budget(budget, budget_pct):
    if budget is not None and budget_pct is not None:
        _raise("budget",
               "budget and budget_pct are two spellings of one "
               "constraint — pass exactly one (tokens, or a percent "
               "of window like the published 10%% auto-load rule)",
               "budget OR budget_pct, never both")
    if budget is not None:
        if not isinstance(budget, int) or isinstance(budget, bool) \
                or budget < 1:
            _raise("budget",
                   "budget must be an integer >= 1 token — a 0-token "
                   "budget is no agent at all",
                   "integer >= 1")
        return budget, "tokens"
    if budget_pct is not None:
        if not isinstance(budget_pct, int) or isinstance(budget_pct,
                                                         bool) \
                or not (1 <= budget_pct <= 100):
            _raise("budget_pct",
                   "budget_pct must be an integer 1..100 — the "
                   "budget you name as a percent of the window "
                   "(the published rule reads 'under 10 % of the "
                   "window')",
                   "integer 1..100")
        return budget_pct, "budget_pct"
    _raise("budget",
           "a trim plan needs a budget: budget (tokens) or budget_pct "
           "(percent of window) — the plan answers 'what to cut to "
           "FIT', so FIT must be defined",
           "budget >= 1 or budget_pct 1..100")


def _arg_window(window):
    if window is None:
        return DEFAULT_WINDOW
    if not isinstance(window, int) or isinstance(window, bool) \
            or window < 1:
        _raise("window",
               "window must be an integer >= 1 token (the scale you "
               "measure against, e.g. 200000; a 60000 local model is "
               "a real caller here)",
               "integer >= 1")
    return window


def _arg_turns(turns):
    if turns is None:
        return 1
    if not isinstance(turns, int) or isinstance(turns, bool) or turns < 1:
        _raise("turns",
               "turns must be an integer >= 1 — the saved listing "
               "would have come back on EVERY turn (Irolla 2026: the "
               "tool list is not paid once)",
               "integer >= 1")
    return turns


def _arg_price(input_per_mtok):
    if input_per_mtok is None:
        return None
    try:
        price = Decimal(str(input_per_mtok))
    except (InvalidOperation, ValueError):
        _raise("input_per_mtok",
               "input_per_mtok must be a decimal STRING — the price "
               "per million input tokens YOU pay; never a stored "
               "table, prices rot, arguments don't",
               "decimal string >= 0, e.g. \"2\"")
    if not price.is_finite() or price < 0:
        _raise("input_per_mtok",
               "input_per_mtok must be a finite non-negative decimal "
               "— a negative price is a refund nobody publishes",
               "decimal string >= 0")
    return price


def _arg_usage(usage, names):
    if usage is None:
        return {}
    if not isinstance(usage, dict):
        _raise("usage",
               "usage must be an object mapping tool name to calls "
               "over the last 30 days (e.g. {\"send_mail\": 12})",
               "object of tool name -> integer >= 0")
    out = {}
    for k, v in usage.items():
        if not isinstance(k, str) or k == "":
            _raise("usage",
                   "usage keys must be non-empty tool names",
                   "tool name strings")
        if k not in names:
            _raise("usage.%s" % k,
                   "usage lists a tool the pasted listing does not "
                   "carry: '%s' — an uncounted ghost would corrupt "
                   "the ratio arithmetic" % k,
                   "usage names must appear in tools")
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            _raise("usage.%s" % k,
                   "usage.%s must be an integer >= 0 — calls over 30 "
                   "days, from YOUR logs (never fetched here)" % k,
                   "integer >= 0")
        out[k] = v
    return out


def _arg_keep(keep, names):
    if keep is None:
        return set()
    if not isinstance(keep, list) or not all(isinstance(x, str)
                                             for x in keep):
        _raise("keep",
               "keep must be a list of tool-name strings — the tools "
               "you refuse to disconnect",
               "array of strings")
    seen = set()
    for k in keep:
        if k == "":
            _raise("keep", "keep entries must be non-empty names",
                   "non-empty strings")
        if k not in names:
            _raise("keep",
                   "keep lists a tool the pasted listing does not "
                   "carry: '%s' — protect what exists" % k,
                   "keep names must appear in tools")
        if k in seen:
            _raise("keep",
                   "duplicate keep name '%s' — protection is a "
                   "set, not a stack",
                   "unique keep names")
        seen.add(k)
    return seen


def tool_trim(tools, budget=None, budget_pct=None, window=None,
              keep=None, usage=None, turns=None, input_per_mtok=None):
    window = _arg_window(window)
    budget_tokens, via = _arg_budget(budget, budget_pct)
    if via == "budget_pct":
        budget_tokens = window * budget_pct // 100   # floor exact
        budget_tokens = max(budget_tokens, 1)        # 1..100 x >=1
    turns = _arg_turns(turns)
    price = _arg_price(input_per_mtok)

    measured = _measure_tools(tools)
    names = set(m["name"] for m in measured)
    usage_map = _arg_usage(usage, names)
    keep_set = _arg_keep(keep, names)

    total_chars = sum(m["chars"] for m in measured)
    before_est = _ct._est(total_chars)

    # — classes closes, critères EXACTS (fractions), tie-breaks déclarés
    idle, ratioed, unknown, protected = [], [], [], []
    for m in measured:
        if m["name"] in keep_set:
            protected.append(m)
            continue
        c = usage_map.get(m["name"])
        if c == 0:
            idle.append((m, None))
        elif c is None:
            unknown.append((m, None))
        else:
            ratioed.append((m, Fraction(m["chars"], c)))
    idle.sort(key=lambda r: (-r[0]["chars"], r[0]["name"]))
    ratioed.sort(key=lambda r: (-r[1], -r[0]["chars"], r[0]["name"]))
    unknown.sort(key=lambda r: (-r[0]["chars"], r[0]["name"]))
    queue = [(m, "IDLE_30J") for m, _ in idle] \
        + [(m, "RATIO") for m, _ in ratioed] \
        + [(m, "UNKNOWN") for m, _ in unknown]

    cur = total_chars
    dropped = []
    dropped_names = set()
    for m, klass in queue:
        if _ct._est(cur) <= budget_tokens:
            break
        cur -= m["chars"]
        dropped_names.add(m["name"])
        dropped.append((m, klass))

    survivors = [m for m in measured if m["name"] not in dropped_names]
    survivor_chars = sum(m["chars"] for m in survivors)
    after_est = _ct._est(survivor_chars)
    saved_global = before_est - after_est
    saved_sum = sum(_ct._est(m["chars"]) for m, _ in dropped)

    if before_est <= budget_tokens:
        verdict = "FITS_AS_IS"
    elif after_est <= budget_tokens:
        verdict = "TRIMMED_FITS"
    else:
        verdict = "STILL_OVER"

    flags = []
    if not measured:
        flags.append("EMPTY_LISTING")
    if not usage_map:
        flags.append("NO_USAGE_DATA")
    if keep_set:
        flags.append("KEEP_PROTECTED")
    if any(k == "UNKNOWN" for _, k in dropped):
        flags.append("UNKNOWN_CUTS")
    if measured and not survivors:
        flags.append("ALL_DROPPED")

    def _entry(m, klass, rank):
        c = usage_map.get(m["name"])
        return {
            "rank": rank,
            "name": m["name"],
            "class": klass,
            "chars": m["chars"],
            "token_estimate": _ct._est(m["chars"]),
            "calls_30d": c,
            "cost_per_call": (None if not c
                              else _q2r(Fraction(m["chars"], c))),
        }

    plan_rows = [_entry(m, k, i + 1) for i, (m, k) in enumerate(dropped)]
    plan_folded = None
    if len(dropped) > TOP_DETAIL:
        fold = dropped[TOP_DETAIL:]
        fc = sum(m["chars"] for m, _ in fold)
        plan_folded = {"tools": len(fold), "chars": fc,
                       "token_estimate": sum(_ct._est(m["chars"])
                                             for m, _ in fold)}
        plan_rows = plan_rows[:TOP_DETAIL]
    survivor_rows = [_entry(m, "KEEP" if m["name"] in keep_set
                            else "SURVIVOR", i + 1)
                     for i, m in enumerate(survivors)]
    survivor_folded = None
    if len(survivors) > TOP_DETAIL:
        fold = survivors[TOP_DETAIL:]
        fc = sum(m["chars"] for m in fold)
        survivor_folded = {"tools": len(fold), "chars": fc,
                           "token_estimate": sum(_ct._est(m["chars"])
                                                 for m in fold)}
        survivor_rows = survivor_rows[:TOP_DETAIL]

    out = {
        "model": "agent/tool-trim",
        "tools": len(measured),
        "budget": {
            "tokens": budget_tokens,
            "via": via,
            "window": window,
            "rule": ("budget_pct -> window x pct // 100, integer "
                     "floor — 'under 10 % of the window' (the "
                     "published auto-load rule, apidog 16-nov-2026) "
                     "reads as a floor, never as a promise"
                     if via == "budget_pct" else
                     "budget given in tokens, honoured as an "
                     "inclusive bound (est == budget FITS, the "
                     "sisters' close bound)"),
        },
        "before": {"tools": len(measured), "chars": total_chars,
                   "token_estimate": before_est,
                   "pct_of_window": _ct._share(before_est, window)},
        "after": {"tools": len(survivors), "chars": survivor_chars,
                  "token_estimate": after_est,
                  "pct_of_window": _ct._share(after_est, window)},
        "verdict": verdict,
        "plan": plan_rows,
        "plan_folded": plan_folded,
        "survivors": survivor_rows,
        "survivors_folded": survivor_folded,
        "saved": {
            "tokens_global": saved_global,
            "tokens_sum_per_tool": saved_sum,
            "divergence": saved_sum - saved_global,
            "chars": total_chars - survivor_chars,
            "per_turn": saved_global * turns,
            "turns": turns,
            "rule": ("the GLOBAL saved number is ceil(total/4) - "
                     "ceil(kept/4) — the published method divides "
                     "the total, never sums the ceilings; both "
                     "numbers travel and the divergence is stated "
                     "(sister law, b101/b104). The listing rides "
                     "EVERY turn, so the saving repeats every turn"),
        },
        "flags": flags,
        "rules": {
            "order": ("drops fall in closed classes: IDLE_30J first "
                      "(calls_30d == 0 — paying every turn, never "
                      "used), then RATIO worst cost-per-call first "
                      "(chars / calls in EXACT fractions, never "
                      "floats), then UNKNOWN last (usage absent — "
                      "one does not cut what was never measured "
                      "ahead of what was measured useless)"),
            "ties": ("chars descending, then tool name ascending — "
                     "declared, stable, replayable (sister rule b104)"),
            "estimator": ESTIMATOR,
            "recount": ("paste the survivor list into "
                        "/agent/context-tax: the same canonical "
                        "strings are measured there, so its "
                        "token_estimate MUST equal this after "
                        "number — byte for byte"),
        },
        "provenance": PROVENANCE,
    }
    if verdict == "STILL_OVER":
        out["reste"] = after_est - budget_tokens
        out["over_rule"] = ("the kept floor alone exceeds the budget "
                            "(or the empty listing still misses it) "
                            "— the plan is reported with the "
                            "remaining overage, the budget or the "
                            "keep list must move, not the arithmetic")
    if price is not None:
        usd = (Decimal(out["saved"]["per_turn"]) * price
               / Decimal(1000000)).quantize(Decimal("0.000001"),
                                            rounding=ROUND_HALF_UP)
        out["price"] = {
            "input_per_mtok": str(price),
            "usd_saved_for_this_run": str(usd),
            "rule": ("tokens saved per turn x your price / 10^6, "
                     "exact decimal — the price is YOUR argument; "
                     "we store no model price table (a table "
                     "would rot, an argument doesn't) — and the "
                     "savings are real dollars per the altrouter "
                     "measure: cutting three servers moved a cycle "
                     "from $0.7806 to $0.3099"),
        }
    return out
