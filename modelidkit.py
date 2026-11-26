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
import re
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

# --------------------------------------------------------------- DIALECTES
# bundle109 — le champ que la grammaire peut jurer SANS ping : QUELLE
# PORTE parle cet id. Douleur mesurée (miroir catalogue radar 05h04
# + 23-nov, incidents cités plus haut) : un id « listé » meurt en 404
# ou 400 quand l'appelant frappe la mauvaise porte — anthropic/
# claude-sonnet-5.5:batch pingé en chat sync, gemini-embedding-001:
# batch pingé comme un chat, sentence-transformers/all-minilm-l6-v2
# renvoyé http-400 en /chat (scan bundle 72). Le petit modèle relit
# le catalogue et ne voit pas le DIALECTE. Preuve fraîche du 25-nov :
# HN 49796140 (« all their API routes for non existing models return
# 404 and when there's a new model it returns 403 ») + HN 49554520
# (Cerebras : « Model does not exist… when the error is really about
# billing ») — la porte menteuse s'habille en id menteur.
#
# TABLE FERMÉE, sourcée, zéro extrapolation — chaque token vient d'un
# id REJOUÉ dans la doc publique OpenRouter ce cycle (25-11, gate
# batch-quickstart + guides/features/batch-api + multimodal/
# image-generation + api_reference/embeddings) ou d'un id MESURÉ par
# notre propre radar. Pas d'audio dans la table : sa doc n'a pas été
# rejouée ce cycle, et une table « de mémoire » est interdite
# (question 3). La table GRANDIT d'observations nommées, jamais
# d'indices d'indices.
DIALECT_EMBEDDING = frozenset(("embedding", "embed"))
DIALECT_IMAGE = frozenset(("image", "imagen", "flux", "seedream",
                           "diffusion", "dall", "ideogram", "recraft"))
DIALECT_TOKENS = ("embedding", "image")  # ordre de priorité nommé

# Les PHRASES de porte — verbatim des règles publiées, citées dans
# la réponse comme la guarantee l'y oblige. « The Batch API takes
# the base model slug and resolves the :batch entry itself » ;
# endpoints batch acceptés : /v1/chat/completions, /v1/responses,
# /v1/messages, /v1/embeddings ; « Batch returns text and embeddings
# only » → l'image n'a PAS de porte batch (le clash est la règle,
# pas une humeur). Embeddings batch : « Embeddings batches do not
# accept provider » + « Nested input through the Batch API → 400 ».
_SYNC_CHAT_BASE = (
    "no sync chat endpoint on the suffixed id — the sync door is the "
    "BASE slug; the Batch API takes the base model slug and resolves "
    "the :batch entry itself (published variants rule)")
_SYNC_EMBEDDING = (
    "this id speaks embeddings, not chat — its sync door is "
    "/v1/embeddings; a chat call on it answers 400 (measured, radar "
    "bundle 72: all-minilm-l6-v2) — the catalog mixes types without "
    "saying so in the id")
_SYNC_IMAGE = (
    "this id speaks image output — its door is the gateway's "
    "dedicated Image API (image-generation guide, 25-nov: flux, "
    "seedream, gpt-image listed there, not in chat); "
    "/v1/chat/completions is not it")
_BATCH_YES = (
    "the batch door exists: the Batch API takes the base slug and "
    "resolves :batch itself; one model and one endpoint per batch; "
    "24h window")
_BATCH_EMBEDDING_NOTES = (
    "embeddings batches are accepted (/v1/embeddings is a listed "
    "batch endpoint) but two named restrictions ride: provider is "
    "not accepted, and nested document-chunk input returns 400")
_BATCH_NONE = (
    "CLASH — Batch returns text and embeddings only (published "
    "limitation, 25-nov): an image-dialect id has NO batch door; a "
    ":batch listing on it is the V23 mirage trap, refuse to ping it "
    "trustingly")

# Le BADGE — la thèse V23 en une ligne, posée sur tout résultat qui
# porte un dialecte (et seulement ceux-là). « Listed » est un CRAYON
# de catalogue ; « invocable » est un PING ; entre les deux, la
# grammaire nomme la porte sans jamais jurer l'appel. Preuve fraîche
# 25-nov : HN 49796140 (404 pour tout id absent, 403 pour tout id
# NOUVEAU — le code HTTP ment par omission chez le fournisseur
# comme chez le gateway).
BADGE_LISTED_NOT_INVOCABLE = (
    "listed in the catalog, NOT proven invocable — the batch "
    "door is /api/v1/batch (24h window, base slug), never a "
    "sync chat call on the :batch id")


def _name_tokens(raw):
    """Tokens du SEGMENT DE NOM (dernier slash), minuscules, coupés
    sur tout ce qui n'est pas alphanumérique. L'org ne vote pas :
    « bytedance-seed/seedream-4.5 » parle image par son NOM."""
    base = raw
    mark = min((x for x in (base.find(":"), base.find("#")) if x != -1),
               default=-1)
    if mark != -1:
        base = base[:mark]
    seg = base.rsplit("/", 1)[-1]
    return set(re.split(r"[^a-z0-9]+", seg.lower()))


def _dialect_of(raw):
    """Dialecte de CONTENU par tokens du nom, priorité nommée :
    embedding avant image (« multimodal-embedding » est un
    embedding, pas une image)."""
    toks = _name_tokens(raw)
    if toks & DIALECT_EMBEDDING:
        return "embedding"
    if toks & DIALECT_IMAGE:
        return "image"
    return "chat"


def _dialect_info(raw, vinfo):
    """Champ DIALECTE — émis quand la grammaire a quelque chose à
    dire que le déaut masquerait : id de dialecte non-chat (la
    mauvaise porte est le pain, quel que soit le suffixe) OU porteur
    du suffixe :batch (la porte batch est une porte, pas un modèle).
    Un chat sans suffixe batch ne gagne AUCUN champ : les pins
    existantes restent octet pour octet (précédent b68)."""
    content = _dialect_of(raw)
    batch = vinfo is not None and vinfo["class"] == "catalog" \
        and vinfo["suffix"].lower() == "batch"
    if content == "chat" and not batch:
        return None
    out = {"content": content}  # type: dict
    if content == "embedding":
        out["sync"] = _SYNC_EMBEDDING
    elif content == "image":
        out["sync"] = _SYNC_IMAGE
    else:
        out["sync"] = _SYNC_CHAT_BASE
    if batch:
        if content == "image":
            out["batch"] = _BATCH_NONE
            out["clash"] = True
        elif content == "embedding":
            out["batch"] = _BATCH_YES + " — " + _BATCH_EMBEDDING_NOTES
            out["clash"] = False
        else:
            out["batch"] = _BATCH_YES
            out["clash"] = False
    else:
        out["batch"] = ("not batched: this id carries no batch "
                        "variant — sync door only")
        out["clash"] = False
    return out

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
        dinfo = _dialect_info(raw, info)
        if dinfo is not None:
            entry["dialect"] = dinfo
            entry["badge"] = BADGE_LISTED_NOT_INVOCABLE
        if info is not None and cat:
            # b116 TEMOIN DE BASE (miroir radar 25-11 23h47 : trois
            # :batch LISTES mais 404 en ecriture — la porte conseillee
            # est le slug de BASE ; un conseil de porte vers une porte
            # que le releve colle NE NOMME RIEN reste un mirage). Le
            # champ est additif, mode catalogue seulement, jamais un
            # verdict de plus : l'echelle de b68 reste gelee.
            k = raw.find(info["marker"])
            base = raw[:k]
            listed = base in cat
            entry["base"] = {
                "slug": base, "listed": listed,
                "note": ("base slug IS in the pasted annuaire — the "
                         "sync door this suffix's table names is "
                         "proven listed (invocability stays a ping, "
                         "V23)" if listed else
                         "base slug is NOT in the pasted annuaire — "
                         "the door the rules name is unproven HERE: "
                         "paste the fuller listing or ping it; this "
                         "audit swears nothing on an absent line")}
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
