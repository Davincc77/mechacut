# -*- coding: utf-8 -*-
"""costdiffkit — /agent/cost-diff : COMBIEN À COMBIEN passe la facture
d'un tools/list entre deux relevés collés, par outil et par champ.

LA DOULEUR, publiée et vécue (lendille DEV, rang 1 de la file du
cycle 2026-11-24) : les mesures externes disent COMBIEN coûte UNE
liste (context-tax, livré b101) ; elles ne disent jamais ce qu'a
COÛTÉ L'UPDATE — et c'est la facture que personne ne signe :
- testdino.com nov-2026 : Playwright MCP 0.0.41 -> 0.0.85, la facture
  par défaut a CRÛ DE 78 % (2 203 -> 3 919 tokens) sans qu'aucun
  changelog ne le annonce.
- dplouffe.ca 04-nov-2026 : le même serveur GitHub coûte « 5,896
  tokens filtré, 23,139 avec tous les toolsets » — le CHIFFRE qui
  décide est une DIFFÉRENCE entre deux listings, pas un total.
- community.benhalpern.com 21-nov-2026 (Vladimir Beskorovainyi) :
  « After any filter, list the tools again and count them » — la
  recette de vérification EST un cost-diff ; aucun outil sans compte
  ne la rend.
- r/mcp (poizin) : deux versions des MÊMES 27 outils, 8 497 -> 22k
  tokens — « la faute au détail du schema, pas au texte » : ce sont
  les CHAMPS qui bougent, ils doivent voyager signés.
- Preuve INTERNE, pêchée par la maison sur SES propres pages (b103) :
  le coût FR de la landing pour e27 s'est mesuré EN SIX VAGUES par
  diff programmatique entre HEAD et l'atelier — la recette
  cost-diff mord d'abord nos propres fichiers.

CE QUI N'EXISTAIT PAS (question 5 payée) : mcp-audit dit REJETÉ,
mcp-surface dit CHANGÉ, context-tax dit COMBIEN — LA PAIRE (delta
chiffré ENTRE DEUX versions, par outil, par champ, en % du côté
avant) n'existait nulle part, ni en API publique, ni en lib pip
(les runs publiés de serverdex/Ulehla comparent DES SERVEURS DIFFÉ-
RENTS à une date, jamais VOS deux relevés). NOTRE différenciation :
HTTP sans compte, les DEUX listings COLLÉS, canon maison unique,
zéro fetch, zéro LM.

LOIS FERMÉES (le canon, l'estimateur et les seuils sont CEUX DE
context-tax — le diff est la MÊME mesure aux deux moments, sinon la
soustraction ne veut rien dire) :
1. MESURE = chaîne JSON canonique de la définition (contexttaxkit,
   sort_keys, separators (",",":"), UTF-8 non échappé). Estimateur
   NOMMÉ et unique : ceil(chars ÷ 4), plancher publié cité verbatim
   chez le frère.
2. PAIRE PAR NOM : un nom absent du côté avant = ADDED, absent du
   côté après = REMOVED, présent et canon IDENTIQUE = SAME, présent
   et canon DIFFÉRENT = CHANGED. Les deux validations du frère
   voyagent par côté : plafond 5 000 entrées, noms non-vides et
   UNIQUES (doublon = classe shadowing, REFUSÉ).
3. LA SOUSTRACTION EST UN THÉORÈME : somme des delta_chars par outil
   == total après − total avant, ASSERTÉ dans le module (leçon
   b101 : l'additif interne PÊCHE lui-même une double facture).
4. GLOBAL vs SOMME : le delta GLOBAL est ceil(total_après/4) −
   ceil(total_avant/4), JAMAIS la somme des deltas par outil — la
   méthode publiée divise le total. La divergence est CHIFFRÉE dans
   la réponse (les deux nombres voyagent), pas cachée : vecteur
   tracé à la main, global +4 contre somme +5 (g104).
5. % DU CÔTÉ AVANT : delta_est × 100 ÷ est_before, HALF_UP 2
   décimales ; est_before = 0 (ADDED, ou listing avant vide) ->
   None, JAMAIS d'infini ni de 100 volé. REMOVED porte −100.00.
6. MOVERS : non-nuls uniquement (SAME ne facture rien), tri
   |delta_chars| décroissant, ÉGALITÉ = NOM ASCENDANT — règle close
   DECLARÉE : un diff n'a pas d'« ordre collé » commun des deux
   listes, le nom est le seul tie-break que les deux côtés partagent.
   TOP 100 détaillés (seuil famille b97), le reste PLIÉ en tiers
   nommé (count, delta_chars, token_estimate_delta).
7. CHAMPS SIGNÉS : un outil CHANGED porte ses moved_fields (valeur
   canonique après − avant par champ contractuel, autres clés
   NOMMÉES avec le signe) — la leçon poizen : 27 outils, +13k
   tokens, la faute au schema seul. Une clé qui APPARAÎT ou DIS-
   PARAÎT est facturée à son overhead complet, nommée (classe
   tool-poisoning : la facture, pas seulement le digest).
8. FENÊTRE : argument, défaut 200 000 (l'échelle citée) ; verdict
   FITS/OVERFLOWS_WINDOW PAR CÔTÉ (borne est == window -> FITS, la
   borne close du frère) ; transition CLOSE STABLE /
   FITS_TO_OVERFLOWS / OVERFLOWS_TO_FITS — le story de testdino est
   un nom de champ, pas une devinette.
9. PAR-TOUR ET DOLLARDS : tokens_charged_delta = delta global ×
   turns (Irolla : la liste se paie À CHAQUE TOUR) ; dollars
   SEULEMENT si le prix est un ARGUMENT décimal de l'appelant —
   zéro table de prix stockée. Le delta peut être NÉGATIF (un
   allègement est une économie chiffrée, même monnaie, signe en
   toutes).
10. DRAPEAUX CLOSES : EMPTY_BEFORE / EMPTY_AFTER / EMPTY_BOTH
    (réponnent, une liste vide est un état, pas une erreur),
    DISJOINT_LISTINGS (aucun nom partagé : le diff est un REMPLA-
    CEMENT de serveur, pas une version — les ADDED/REMOVED dominent,
    le % de croissance n'a plus de sens de « mise à jour »),
    NO_CHANGES (movers vide), WINDOW_TRANSITION portant son sens.

Doctrine : zéro fetch, zéro horloge, zéro LM, zéro tokenizer tiers.
Un diff entre deux listings est de l'arithmétique, la seule mémoire
autorisée est la vôtre — dans le corps de la requête.
"""
from decimal import Decimal, InvalidOperation

import contexttaxkit as _ct
from contexttaxkit import (ESTIMATOR, MAX_TOOLS, TOP_DETAIL,
                           DEFAULT_WINDOW)

MAX_TOOLS = _ct.MAX_TOOLS
TOP_DETAIL = _ct.TOP_DETAIL

PROVENANCE_DIFF = [
    "testdino.com nov-2026: Playwright MCP 0.0.41->0.0.85 default "
    "listing grew 78% (2203->3919 tokens) unannounced",
    "dplouffe.ca 04-nov-2026: same GitHub server, 5896 tokens "
    "filtered vs 23139 all toolsets — the decision number is a delta",
    "community.benhalpern.com 21-nov-2026: 'After any filter, list "
    "the tools again and count them' — the verification recipe IS "
    "a cost diff",
    "reddit r/mcp (poizin): same 27 tools, 8497->22k tokens, the "
    "schema detail alone — fields must travel signed",
    "mechacut internal b103 24-nov-2026: the FR landing cost of one "
    "tool measured in six waves of programmatic locale diff — the "
    "recipe bit us first",
]

ESTIMATE_RULE = (
    "token_estimate_delta GLOBAL = ceil(total_chars_after/4) - "
    "ceil(total_chars_before/4) — the published floor method divides "
    "the total (context-tax law 2, same canon), so it need NOT equal "
    "the sum of per-tool deltas; both numbers travel, the "
    "divergence is stated, never hidden")

PCT_RULE = (
    "percentage of the BEFORE-side estimate, HALF_UP 2 decimals; a "
    "tool absent before pays nothing before — None, never infinity; "
    "REMOVED carries -100.00")

TRANSITION_VALUES = ("STABLE", "FITS_TO_OVERFLOWS", "OVERFLOWS_TO_FITS")


class CostDiffError(Exception):
    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected


def _measure_side(tools, side_name):
    """Validation et mesure d'un côté : les lois 2/7 du frère,
    appliquées au relevé qu'il nomme (tools_before / tools_after)."""
    if len(tools) > MAX_TOOLS:
        raise CostDiffError(
            side_name,
            "listing too large: %d tools pasted, ceiling %d per "
            "side (same family threshold as /agent/context-tax)"
            % (len(tools), MAX_TOOLS),
            "at most 5000 tool entries per side")
    seen = set()
    measured = {}
    for i, tool in enumerate(tools):
        try:
            m = _ct._measure_tool(tool, "%s[%d]" % (side_name, i))
        except _ct.ContextTaxError as e:
            # le contrat du 400 du frère (field + expected), traduit
            # sans réécriture : SAME canon, SAME serment, SAME shape.
            raise CostDiffError(e.field, e.message, e.expected)
        if m["name"] in seen:
            raise CostDiffError(
                "%s[%d].name" % (side_name, i),
                "duplicate tool name '%s' — spec 2026-07-28 names "
                "are unique per server; a pasted duplicate is the "
                "shadowing class (same refusal as /agent/context-tax)"
                % m["name"],
                "unique tool names")
        seen.add(m["name"])
        measured[m["name"]] = m
    return measured


def _arg_window(window):
    if window is None:
        return DEFAULT_WINDOW
    if not isinstance(window, int) or isinstance(window, bool) \
            or window < 1:
        raise CostDiffError(
            "window",
            "window must be an integer >= 1 token (the scale you "
            "measure both sides against, e.g. 200000)",
            "integer >= 1")
    return window


def _arg_turns(turns):
    if turns is None:
        return 1
    if not isinstance(turns, int) or isinstance(turns, bool) or turns < 1:
        raise CostDiffError(
            "turns",
            "turns must be an integer >= 1 — the listing is charged "
            "per turn (Irolla 2026), and the DELTA rides every turn "
            "too", "integer >= 1")
    return turns


def _arg_price(input_per_mtok):
    if input_per_mtok is None:
        return None
    try:
        price = Decimal(str(input_per_mtok))
    except (InvalidOperation, ValueError):
        raise CostDiffError(
            "input_per_mtok",
            "input_per_mtok must be a decimal STRING — the price "
            "per million input tokens YOU pay; never a stored "
            "table, prices rot, arguments don't",
            "decimal string >= 0, e.g. \"2\"")
    if not price.is_finite() or price < 0:
        raise CostDiffError(
            "input_per_mtok",
            "input_per_mtok must be a finite non-negative decimal — "
            "a negative price is a refund nobody publishes",
            "decimal string >= 0")
    return price


def _side_totals(measured, window):
    total_chars = sum(m["chars"] for m in measured.values())
    estimate = _ct._est(total_chars)
    return {
        "tools": len(measured),
        "chars": total_chars,
        "token_estimate": estimate,
        "verdict": "FITS" if estimate <= window else "OVERFLOWS_WINDOW",
    }


def _moved_fields(b, a):
    """Champs signés d'un outil CHANGED : valeur canonique après −
    avant par champ contractuel ; autres clés NOMMÉES, apparues ou
    disparues incluses. Zéro ligne pour un champ immobile."""
    moved = {}
    for k in _ct.CONTRACT_FIELDS:
        vb = b["vals"].get(k, 0)
        va = a["vals"].get(k, 0)
        if vb != va:
            moved[k] = va - vb
    keys = set(b["other"]) | set(a["other"])
    for k in sorted(keys):
        vb = b["other"].get(k, 0)
        va = a["other"].get(k, 0)
        if vb != va:
            moved["other:" + k] = va - vb
    fr = a["framing"] - b["framing"]
    if fr:
        moved["framing"] = fr
    return moved


def cost_diff(tools_before, tools_after, window=None, turns=None,
              input_per_mtok=None):
    window = _arg_window(window)
    turns = _arg_turns(turns)
    price = _arg_price(input_per_mtok)
    before = _measure_side(tools_before, "tools_before")
    after = _measure_side(tools_after, "tools_after")

    rows = []
    classes = {"added": 0, "removed": 0, "changed": 0, "unchanged": 0}
    for name in set(before) | set(after):
        b = before.get(name)
        a = after.get(name)
        if b is None:
            assert a is not None   # name vient de before|after
            cls = "ADDED"
            delta_chars = a["chars"]
        elif a is None:
            cls = "REMOVED"
            delta_chars = -b["chars"]
        else:
            delta_chars = a["chars"] - b["chars"]
            cls = "SAME" if delta_chars == 0 else "CHANGED"
        classes["unchanged" if cls == "SAME" else cls.lower()] += 1
        if cls == "SAME":
            continue
        eb = _ct._est(b["chars"]) if b else 0
        ea = _ct._est(a["chars"]) if a else 0
        d_est = ea - eb
        pct = None if eb == 0 else _ct._q2(Decimal(d_est) * 100
                                           / Decimal(eb))
        row = {"name": name, "class": cls,
               "chars_before": b["chars"] if b else None,
               "chars_after": a["chars"] if a else None,
               "delta_chars": delta_chars,
               "token_estimate_delta": d_est,
               "pct_of_before": pct}
        if cls == "CHANGED":
            row["moved_fields"] = _moved_fields(b, a)
        rows.append(row)

    # loi 3 : la soustraction est un théorème — assert interne,
    # il pêche lui-même une double facture (leçon b101).
    tb = _side_totals(before, window)
    ta = _side_totals(after, window)
    assert sum(r["delta_chars"] for r in rows) == \
        ta["chars"] - tb["chars"], "delta_chars must add up"

    delta_est_total = ta["token_estimate"] - tb["token_estimate"]
    delta_est_sum = sum(r["token_estimate_delta"] for r in rows)
    rows.sort(key=lambda r: (-abs(r["delta_chars"]), r["name"]))
    movers = rows[:TOP_DETAIL]
    folded = None
    if len(rows) > TOP_DETAIL:
        rest = rows[TOP_DETAIL:]
        folded = {"tools": len(rest),
                  "delta_chars": sum(r["delta_chars"] for r in rest),
                  "token_estimate_delta":
                      sum(r["token_estimate_delta"] for r in rest)}

    if tb["verdict"] == ta["verdict"]:
        transition = "STABLE"
    elif tb["verdict"] == "FITS":
        transition = "FITS_TO_OVERFLOWS"
    else:
        transition = "OVERFLOWS_TO_FITS"

    flags = []
    if not before and not after:
        flags.append("EMPTY_BOTH")
    else:
        if not before:
            flags.append("EMPTY_BEFORE")
        if not after:
            flags.append("EMPTY_AFTER")
        if before and after and not (set(before) & set(after)):
            flags.append("DISJOINT_LISTINGS")
    if not rows:
        flags.append("NO_CHANGES")
    if transition != "STABLE":
        flags.append("WINDOW_TRANSITION")

    growth_pct = None if tb["token_estimate"] == 0 else \
        _ct._q2(Decimal(delta_est_total) * 100
                / Decimal(tb["token_estimate"]))

    out = {
        "model": "agent/cost-diff",
        "classes": classes,
        "totals": {
            "before": tb,
            "after": ta,
            "delta": {
                "tools": ta["tools"] - tb["tools"],
                "chars": ta["chars"] - tb["chars"],
                "token_estimate": delta_est_total,
                "pct_of_before": growth_pct,
            },
            "per_tool_delta_sum": delta_est_sum,
            "divergence_note": ESTIMATE_RULE,
        },
        "movers": movers,
        "folded": folded,
        "window": {
            "tokens": window,
            "verdict_before": tb["verdict"],
            "verdict_after": ta["verdict"],
            "transition": transition,
            "note": ("window is an ARGUMENT measured against both "
                     "sides — the 200k scale published by every "
                     "source cited, not a vendor ceiling"),
        },
        "per_turn": {
            "turns": turns,
            "tokens_charged_delta": delta_est_total * turns,
            "rule": ("definitions ride EVERY turn (Irolla 2026: the "
                     "tool list is not paid once) — this line is "
                     "the global delta x turns; the growth bill of "
                     "a session is here, not in a changelog"),
        },
        "pct_rule": PCT_RULE,
        "transition_values": list(TRANSITION_VALUES),
        "flags": flags,
        "estimator": ESTIMATOR,
        "provenance": PROVENANCE_DIFF,
    }
    if price is not None:
        usd = (Decimal(out["per_turn"]["tokens_charged_delta"]) * price
               / Decimal(1000000)).quantize(Decimal("0.000001"),
                                            rounding=_ct.ROUND_HALF_UP)
        out["price"] = {
            "input_per_mtok": str(price),
            "usd_delta_for_this_run": str(usd),
            "rule": ("tokens_charged_delta x your price / 10^6, "
                     "exact decimal, sign included — a listing that "
                     "shrank saves real money and the refund is "
                     "named, not smoothed"),
        }
    return out
