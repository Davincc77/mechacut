# -*- coding: utf-8 -*-
"""modelidkit — /agent/modelid : l'audit STATIQUE d'une liste d'ids de
modèles contre un annuaire COLLÉ. La grammaire ne jure jamais
l'existence — c'est la leçon V23, érigée en champ GUARANTEE.

Douleurs documentées, pas conjecturées (preuves 20–23-nov-2026) :

  * openclaw #20522 : la config ACCEPTE un id inexistant
    (« amazon-bedrock/us.anthropic.claude-opus-4-6-v1:0 », le bon est
    « claude-opus-4-6 »), le gateway démarre, et l'agent meurt à
    l'appel. La correction DEMANDÉE dans l'issue : « validate model
    IDs against catalog before saving to config » — c'est cet outil.
  * openclaw #45294 : « google/gemini-3.0-flash » accepté au
    démarrage, « Unknown model » à l'inférence ; le correct est
    « google/gemini-3-flash-preview ». Le pattern Google est DOCUMENTÉ
    dans l'issue : gemini-<major>[-<minor>]-<tier>[-preview].
  * litellm #37271 : un id à slash est LISTÉ par GET /v1/models et
    404 en GET /v1/models/{id} — le mirage V23 reproduit chez le
    gateway lui-même. Notre verdict dit la forme, jamais l'invocabilité.
  * litellm #14807 : le mode custom-provider ÉLIME tout avant le
    premier slash — Groq reçoit « gpt-oss-120b » au lieu de
    « openai/gpt-oss-120b » et répond 404.
  * n8n #39227 : l'inverse — l'runtime coupe le préfixe provider avant
    d'appeler un gateway qui route sur la chaîne COMPLÈTE. Le suffixe
    nu arrive chez un annuaire qui n'a que des ids à org : NO_ORG.
  * LiteLLM v1.82.3 (guide everpod 21-nov-2026) : l'outil envoie son
    PROPRE nom « openrouter/google/gemini-2.5-flash » à OpenRouter —
    PREFIX_KEPT. Et le test live du 22-nov publié dans le même guide :
    « qwen/qwen3.6-27b » répond 200, « qwen/qwen-3.6-27b » répond 404
    — un seul tiret. PUNCT_DRIFT.
  * hermes-agent #110891 : le picker offre DEUX ids pour une config ;
    l'id raw-key part en « <key>:<model> » et le tour meurt en 503.
    Deux ids pour une entrée = la grammaire tranche, pas l'humeur.
  * superlinked/sie #939 : « make MODEL_NOT_FOUND actionable » — la
    correction demandée est SUGGEST THE CLOSEST model ids (« Did you
    mean …? »). La doc d'erreurs de Claude Code fait exactement ça
    (« Model "Sonnet5" is not a recognized model id. Did you mean
    'claude-sonnet-5' ? ») avec un seuil nommé en dur
    (« When nothing is close enough … »). Ici le seuil est
    LE NÔTRE, publié : distance de Levenshtein ≤ 3 sur la forme
    normalisée (minuscule + point/tiret/souligné retirés — continuumcode :
    les alias « résolvent en silence », un slug mal ponctué marche
    puis MEURT — le drift ponctuel est une bombe à retardement qu'on
    NOMME, pas qu'on tolère).
  * V23 nous-mêmes : l'annuaire listait
    « anthropic/claude-sonnet-5.5:batch » et le GET 404ait. Un audit
    statique qui dirait « OK, invocable » serait le MÊME mensonge.
    Le champ guarantee est le serment contraire : OK certifie la
    forme et l'appartenance à l'annuaire COLLÉ ; seul un ping le
    certifierait — le ping appartient au radar (--catalog), pas à
    cette grammaire. ZÉRO fetch ici, mêmes octets pour toujours.

Grammaire fermée : org/name[:variant|#variant]. Caractères permis :
A-Za-z0-9 . _ - et les séparateurs / : #. Jamais d'espace dans un id
d'API (everpod liste « spaces » et « display names » parmi les causes
directes — un nom d'affichage n'est pas un id, un alias non plus
tant que l'annuaire ne le nomme pas).

Échelle de décision FERMÉE, premier étage qui touche gagne :
EXACT → CASE_DRIFT → PUNCT_DRIFT → PREFIX_KEPT (retrait d'un segment
de tête, byte-exact) → NO_ORG (bare id dont la queue EST dans
l'annuaire) → VARIANT_DECOR (le « :free » fait PARTIE de l'identifiant
— continuumcode —, l'annuaire n'a que la base) → NOT_IN_CATALOG
(+ suggestion si distance ≤ 3, sinon RIEN : pas de near-miss inventé).
Les dérives COMPOSÉES (préfixe + casse, ex. « openrouter/Google/
Gemini-2.5-Flash ») tombent honnêtement en NOT_IN_CATALOG sans
suggestion si la distance dépasse le seuil nommé — le retrait n'est
byte-exact que dans un étage, et un audit qui commence à composer
les règles recommence à déviner.
"""
import string

GRAMMAR = "org/name[:variant|#variant]"
GUARANTEE = ("static form check only — OK certifies the shape and the "
             "pasted annuaire, never the GET (V23); invocability is a "
             "ping, this is a grammar")
ALLOWED = frozenset(string.ascii_letters + string.digits + "._-/:#")
MAX_IDS = 200
MAX_CATALOG = 4000
MAX_ID_LEN = 200
SUGGEST_MAX_DISTANCE = 3

# Variantes publiées — table FERMÉE, source : OpenRouter,
# docs/guides/routing/model-variants/overview (consultée le
# 23-nov-2026). Deux CLASSES au comportement catalogue OPPOSÉ :
# les catalog variants sont des ENTRÉES DU MODELE (elles existent
# dans GET /models et leur id complet doit être envoyé tel quel),
# les routing variants ne sont JAMAIS listées (elles s'appliquent à
# la requête ; les chercher au catalogue est un faux alarme).
# La découverte radar du 23-nov — deux mirages portant « :batch »,
# listés mais morts en appel direct — est exactement la phrase
# publiée : « The Batch API takes the base model slug and resolves
# the :batch entry itself »… « inference requests fail because
# there is no endpoint to route to » quand l'entrée est appelée en
# sync. Le TYPE est un CHAMP, pas un étage de plus dans l'échelle.
VARIANT_CATALOG = {
    "free": ("active",
             "catalog variant: free-tier entry with its own rate "
             "limits, endpoints and zero price — it is NOT the base "
             "entry; do not strip the suffix to compare, pricing and "
             "context differ"),
    "batch": ("active",
              "catalog variant served by the Batch API only: the "
              "Batch API takes the BASE slug and resolves :batch "
              "itself — a sync chat call on the suffixed id has no "
              "endpoint to route to (our own V23 mirage, published)"),
    "thinking": ("deprecated",
                 "catalog variant, deprecated: reasoning enabled by "
                 "default on models that shipped the endpoint — use "
                 "the reasoning parameter instead"),
    "extended": ("deprecated",
                 "catalog variant, deprecated: larger-context entry, "
                 "currently offered by no model"),
}
VARIANT_ROUTING = ("nitro", "floor", "exacto", "online")

VERDICTS = ("OK", "EMPTY", "HAS_SPACE", "BAD_CHAR", "BAD_VARIANT",
            "BAD_SLASH", "NO_ORG", "PREFIX_KEPT", "CASE_DRIFT",
            "PUNCT_DRIFT", "VARIANT_DECOR", "NOT_IN_CATALOG")


class ModelIdError(Exception):
    def __init__(self, field, message, expected):
        self.field = field
        self.message = message
        self.expected = expected
        super().__init__(f"{field}: {message}")


def _norm(s):
    """Forme normalisée : minuscule, point/tiret/souligné retirés.
    Le slash RESTE (il porte la structure org/name)."""
    return s.lower().translate(str.maketrans("", "", "._-"))


def _structural(raw):
    """Code structurel ou None si la forme est saine."""
    if raw.strip() == "":
        return "EMPTY"
    if any(c.isspace() for c in raw):
        return "HAS_SPACE"
    if any(c not in ALLOWED for c in raw):
        return "BAD_CHAR"
    ci, hi = raw.find(":"), raw.find("#")
    if raw.count(":") > 1 or raw.count("#") > 1:
        return "BAD_VARIANT"
    if ci == 0 or hi == 0:
        return "BAD_VARIANT"
    if ci != -1 and hi != -1 and hi < ci:
        return "BAD_VARIANT"
    mark = min((x for x in (ci, hi) if x != -1), default=-1)
    if mark != -1:
        if mark == len(raw) - 1 or raw[mark + 1] in ":#":
            return "BAD_VARIANT"
    base = raw if mark == -1 else raw[:mark]
    if base.startswith("/") or base.endswith("/") or "//" in base:
        return "BAD_SLASH"
    return None


# Serves du TYPE — publié dans chaque résultat portant un suffixe
# structurellement sain. Additif pur : le ladder, la grammaire et la
# guarantee ne bougent pas, un id sans suffixe ne gagne AUCUN champ
# (les pins existantes restent octet pour octet).
_ROUTING_SERVES = (
    "routing variant — never an entry in the models catalog; it only "
    "changes how the request is routed. Absent from the catalog is "
    "NORMAL, not an error to fix: the catalog holds the base id")
_UNKNOWN_SERVES = (
    "suffix not in the published closed table (catalog/routing) — "
    "refuse to guess: ping the full id nowhere trustingly, ask the "
    "gateway docs. The guarantee field still holds: this is a "
    "grammar, never invocability")


def _variant_info(raw):
    """TYPE de la variante pour un id structurellement sain. Renvoie
    None si aucun marqueur ; les empilés (:a:b) meurent déjà en
    BAD_VARIANT dans _structural et n'arrivent jamais ici."""
    marks = [i for i, c in enumerate(raw) if c in ":#"]
    if not marks or len(marks) > 1:
        # aucun suffixe, ou empilé (:a:b) — l'empilé est déjà mort en
        # BAD_VARIANT dans _structural ; pas de champ sur un cadavre.
        return None
    k = marks[0]
    marker, suffix = raw[k], raw[k + 1:]
    low = suffix.lower()
    if low in VARIANT_CATALOG:
        status, serves = VARIANT_CATALOG[low]
        cls = "catalog"
    elif low in VARIANT_ROUTING:
        status, serves, cls = "published", _ROUTING_SERVES, "routing"
    else:
        status, serves, cls = "unpublished", _UNKNOWN_SERVES, "unknown"
    return {"marker": marker, "suffix": suffix, "class": cls,
            "status": status, "serves": serves}


def _levenshtein(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _suggest(raw, cat_sorted):
    """Plus proche voisin sur les formes normalisées ; seuil nommé ;
    égalité -> première entrée lexicographique (déterminisme)."""
    n = _norm(raw)
    best = None
    for e in cat_sorted:
        d = _levenshtein(n, _norm(e))
        if d < SUGGEST_MAX_DISTANCE + 1 and (best is None or d < best[0]):
            best = (d, e)
    return best[1] if best else None


def _judge(raw, cat, cat_sorted):
    code = _structural(raw)
    if code:
        return code, None
    if not cat:
        # mode grammaire pure : sans annuaire collé, on ne peut
        # honnêtement affirmer que la structure — rien de plus.
        return "OK", None
    if raw in cat:
        return "OK", None
    lower = raw.lower()
    for e in cat_sorted:
        if e.lower() == lower:
            return "CASE_DRIFT", e
    n = _norm(raw)
    for e in cat_sorted:
        if _norm(e) == n:
            return "PUNCT_DRIFT", e
    parts = raw.split("/")
    if len(parts) >= 3:
        for k in range(1, len(parts) - 1):
            suffix = "/".join(parts[k:])
            if suffix in cat:
                return "PREFIX_KEPT", suffix
    if len(parts) == 2:
        tail = parts[1]
        for e in cat_sorted:
            if e == tail:
                return "PREFIX_KEPT", e
    if len(parts) == 1:
        mark = min((x for x in (raw.find(":"), raw.find("#")) if x != -1),
                   default=-1)
        base = raw if mark == -1 else raw[:mark]
        for e in cat_sorted:
            if "/" in e and e.split("/", 1)[1] == base:
                return "NO_ORG", e
        if mark != -1 and base in cat:
            return "VARIANT_DECOR", base
        return "NOT_IN_CATALOG", _suggest(raw, cat_sorted)
    mark = min((x for x in (raw.find(":"), raw.find("#")) if x != -1),
               default=-1)
    if mark != -1:
        base = raw[:mark]
        if base in cat:
            return "VARIANT_DECOR", base
    return "NOT_IN_CATALOG", _suggest(raw, cat_sorted)


def run_modelid(args):
    ids = args.get("ids")
    if ids is None:
        raise ModelIdError("ids", "absent — l'audit sans liste d'ids "
                                  "ne dit rien",
                           "list of model id strings, 1..%d" % MAX_IDS)
    if not isinstance(ids, list):
        raise ModelIdError("ids", "pas une liste",
                           "list of model id strings")
    if not ids:
        raise ModelIdError("ids", "0 id — un audit vide est une table "
                                  "de zéros qu'un script avalerait",
                           "at least 1 model id string")
    if len(ids) > MAX_IDS:
        raise ModelIdError("ids", "trop d'ids (%d)" % len(ids),
                           "at most %d" % MAX_IDS)
    for i, v in enumerate(ids):
        if not isinstance(v, str):
            raise ModelIdError("ids[%d]" % i, "non-string",
                               "the model id EXACTLY as your agent "
                               "sends it")
        if len(v) > MAX_ID_LEN:
            raise ModelIdError("ids[%d]" % i,
                               "trop long (%d)" % len(v),
                               "at most %d chars" % MAX_ID_LEN)
    catalog = args.get("catalog")
    cat = set()
    if catalog is not None:
        if not isinstance(catalog, list):
            raise ModelIdError("catalog", "pas une liste",
                               "list of annuaire id strings, or omit")
        if len(catalog) > MAX_CATALOG:
            raise ModelIdError("catalog", "trop d'entrées (%d)"
                               % len(catalog),
                               "at most %d" % MAX_CATALOG)
        if not catalog:
            raise ModelIdError("catalog", "0 entrée — un annuaire vide "
                                         "ne prouve rien",
                               "at least 1 annuaire entry, or omit "
                               "for grammar-only mode")
        for i, v in enumerate(catalog):
            if not isinstance(v, str):
                raise ModelIdError("catalog[%d]" % i, "non-string",
                                   "annuaire entry string")
        cat = set(catalog)
    cat_sorted = sorted(cat)
    results = []
    n_ok = 0
    for raw in ids:
        verdict, suggest = _judge(raw, cat, cat_sorted)
        if verdict == "OK":
            n_ok += 1
        entry = {"id": raw, "verdict": verdict, "suggest": suggest}
        info = _variant_info(raw)
        if info is not None:
            entry["variant"] = info
        results.append(entry)
    return {
        "grammar": GRAMMAR,
        "guarantee": GUARANTEE,
        "catalog_mode": bool(cat),
        "catalog_size": len(cat),
        "suggest_max_distance": SUGGEST_MAX_DISTANCE,
        "results": results,
        "counts": {"total": len(ids), "ok": n_ok,
                   "flagged": len(ids) - n_ok},
    }
