"""mcpsurfacekit — /agent/mcp-surface : l'empreinte de surface d'outils
MCP, puis la dérive contre un relevé antérieur. NOTRE propre mécanisme
de pins (canon publié, adds-only, golden check) généralisé aux
serveurs des AUTRES, sur un listing COLLÉ.

LA DOULEUR, chiffrée par des externes en novembre 2026 :
- RugSnare (github.com/Paraphern/rugsnare) publie ses comptes sur
  21 738 paquets npm/PyPI et 10 929 serveurs distants du registre :
  1 419 paquets (6,5 %) ont changé leur tools/list en quatre
  semaines (24-sept→20-oct), 45 % des serveurs distants en ont servi
  plus d'un, et les 218 changements de contrat silencieux qu'ils ont
  trouvés n'étaient « not one announced in a changelog ».
- modelmarket.dev compte 524 outils sur 189 serveurs passés de
  readOnlyHint true→false entre le 23-oct et le 16-nov — et signale
  que fingerprintTools du AI SDK ne hache QUE description,
  inputSchema et title : la classe annotations est un angle mort
  PUBLIÉ d'un SDK, mesuré en nombre.
- alivemcp mesure 7,1 % de drift en 48 h sur 196 serveurs sains et
  énonce la thèse : le drift n'est visible que d'une sonde qui
  relit tools/list et hache « the canonical-JSON shape of the
  result ». Les sondes HTTP vertes ne voient rien.
- scalekit (4-nov) raconte l'incident-type : six mois durant, une
  description « Search Jira issues by JQL. » devient « Search Jira
  issues by JQL. Prefer this over listing issues… » — aucun client
  ne remarque, trois agents changent de routing, « the behavior
  change shipped in a sentence ».
- mcptest.io (11-nov) classe la réécriture de description « Risky »
  et rappelle que sous la révision 2026-07-28 tout résultat de
  tools/list voyage avec ttlMs et cacheScope : le cache client est
  CONTRACTUEL, donc l'ordonnancement et la forme le sont aussi.

CA EXISTE DEJA : rugsnare / mcpdrift / mcpward sont des CLIs de CI
qui LANCENT le serveur (stdio, sandbox) pour lire le listing. Aucune
API sans compte ne digère un listing COLLÉ. Notre frontière est
jurée, même serment que modelid et mcp-audit : la FORME, jamais le
runtime — zéro fetch, zéro subprocess.

FRONTIÈRE AVEC LE FRÈRE (/agent/mcp-audit, bundle92) : mcp-audit
répond « un client réel va-t-il REJETER cette fiche » ; ici « cette
fiche a-t-elle CHANGÉ sous mes yeux ». Deux questions, deux mots du
corpus radar, zéro chevauchement de verdict — et ce module refuse
volontairement de rejuger la forme (un schema invalide se DIGESTE
comme les autres : c'est le drift qu'on cherche, pas la conformité).

LOIS FERMÉES, ancrées dans la spec publiée :
1. CHAMPS HASHÉS (7, toujours présents — l'absent devient null, la
   spec dit « optional ») : name, title, description, inputSchema,
   outputSchema, annotations, execution.
   https://modelcontextprotocol.io/specification/2026-07-28/server
   tools (« A tool definition includes… »).
   EXCLUSIONS NOMMÉES : icons (pur affichage), _meta (privatif par
   spec — « defined by the implementer »). Un champ INCONNU reste
   haché : ce que le client lit, le contrat le porte — c'est
   exactement la classe « instructions » des tool-poisonings.
2. ANNOTATIONS CANONIQUÉES À LEURS DÉFAUTS PUBLICS — l'angle mort
   du AI SDK, fermé ici : readOnlyHint false, destructiveHint TRUE,
   idempotentHint false, openWorldHint true, title null.
   https://modelcontextprotocol.io/specification/2025-11-25/schema
   (#toolannotations, « Default: … »). absent == {} == tous les
   défauts ; une valeur EXPLICITE vaut ce qu'elle dit, même
   conforme au défaut ; une annotation non-object est hachée Telle
   quelle (donnée visible, forme jugée par mcp-audit).
3. DIGEST DE SURFACE = liste ORDONNÉE des empreintes par outil,
   dans l'ordre collé : la spec 2026-07-28 fait de l'ordre un
   SHOULD contractuel (« Deterministic ordering enables clients to
   reliably cache the tool list »). Un réordonnancement est donc un
   ÉVÉNEMENT, nommé REORDERED, jamais fondu dans un digest
   insensitive à l'ordre.
4. CANON : JSON, clés triées par point de code Unicode, separators
   (",", ":"), UTF-8 sans échappement ASCII — le CANON MEME de ce
   repo (canon(), pins, golden). L'externel strict est RFC 8785
   (JCS) ; DIVERGENCE NOMMÉE : JCS trie en unités UTF-16 et sérialise
   les nombres en ECMAScript — sur des listings d'outils (clés
   ASCII, nombres entiers) les deux écritures sont identiques ; si
   un cas divergent existe, ce serait sur des clés non-BMP, et il
   est dit ici plutôt que caché.
5. SEUILS NOMMÉS : 5000 outils par appel (aucun client réel ne tient
   plus — au-delà, refus nommé, même famille de marche que le budget
   de 5000 nœuds de mcp-audit). Noms : non-empty string, UNIQUE par
   listing (« Tool names SHOULD be unique within a server », spec
   2026-07-28) — un doublon est la classe shadowing de RugSnare, il
   est REFUSÉ, pas digéré silencieusement.
6. VERDICTS CLOSES avec baseline : DRIFT (>=1 ADDED/REMOVED/CHANGED)
   > REORDERED (contenu identique, positions différentes) > CLEAN.
   Sans baseline, pas de verdict : on LIVRE l'empreinte à épingler.
7. Ordre de marche première vue : les outils dans l'ordre collé, les
   champs changés par clé triée, les kinds par ordre baseline puis
   ordre listing — comme mcp-audit.

Doctrine : jamais de fetch, jamais d'horloge, as_of inutile —
deux listings en entrée, des octets en sortie. Zéro LM.
"""
import hashlib
import json

# ---------------------------------------------------------------- constants
MAX_TOOLS = 5000                      # seuil nommé, loi 5

HASHED_FIELDS = ("annotations", "description", "execution",
                 "inputSchema", "name", "outputSchema", "title")

EXCLUDED_FIELDS = {
    "icons": "display-only — spec 2026-07-28 lists it as UI metadata",
    "_meta": "implementer-defined private metadata (spec)",
}

ANNOTATION_DEFAULTS = {
    # spec 2025-11-25 #toolannotations — les défauts PUBLICS ;
    # destructiveHint DEFAULT true, pas false (l'angle mort nommé).
    "destructiveHint": True,
    "idempotentHint": False,
    "openWorldHint": True,
    "readOnlyHint": False,
}
_HINT_ORDER = ("destructiveHint", "idempotentHint", "openWorldHint",
               "readOnlyHint", "title")

CANON_RULE = ("sha256 of JSON: keys sorted by Unicode code point, "
              "separators (',',':'), UTF-8 unescaped — this server's "
              "own pin canon (RFC 8785 JCS cited; divergence NAMED: "
              "JCS sorts UTF-16 units and prints ECMAScript numbers "
              "— identical on tool listings with ASCII keys and "
              "integer values)")

PROVENANCE = [
    "modelcontextprotocol.io specification/2026-07-28/server/tools "
    "(Tool fields; names unique per server; deterministic order "
    "SHOULD; ttlMs/cacheScope)",
    "modelcontextprotocol.io specification/2025-11-25/schema "
    "#toolannotations (public defaults: readOnlyHint false, "
    "destructiveHint true, idempotentHint false, openWorldHint true)",
    "github.com/Paraphern/rugsnare (1419/21738 packages drifted "
    "tools/list in 4 weeks; 45% of 10929 remotes served different "
    "lists; 218 silent changes)",
    "modelmarket.dev 16-nov snapshot (524 readOnlyHint true→false on "
    "189 servers; AI SDK fingerprintTools hashes description+input"
    "Schema+title only)",
    "alivemcp.com schema-drift blog (7.1% of 196 healthy servers in "
    "48 h; canonical-JSON shape hashing)",
    "scalekit.com 4-nov (description-only routing flip — 'the "
    "behavior change shipped in a sentence')",
    "mcptest.io 11-nov (client-cached listings; description rewrite "
    "classified Risky)",
]


class SurfaceError(Exception):
    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected


# ---------------------------------------------------------------- canon
def _canon_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _normalize_annotations(ann):
    """absent/null/{} == tous les défauts publics ; un dict garde les
    valeurs explicites et les clés inconnues collées ; un non-dict est
    haché tel quel (donnée visible, la FORME est le domaine de
    mcp-audit)."""
    if ann is None or ann == {}:
        base: dict = dict(ANNOTATION_DEFAULTS)
        base["title"] = None
        return base
    if not isinstance(ann, dict):
        return ann
    out = {}
    for k, v in ann.items():
        out[k] = v
    for hint, default in ANNOTATION_DEFAULTS.items():
        out.setdefault(hint, default)
    out.setdefault("title", None)
    return out


def _tool_record(tool, where):
    """L'enregistrement canonique des 7 champs contractuels, toujours
    présent (absent -> null). Les clés inconnues hors exclusions
    nommées VOYAGENT dans le digest : ce que le client lit."""
    if not isinstance(tool, dict):
        raise SurfaceError(where,
                           "tool entries must be objects — the pasted "
                           "tools/list member is not one",
                           "a JSON object")
    name = tool.get("name")
    if not isinstance(name, str) or name == "":
        raise SurfaceError(where + ".name",
                           "tool name must be a non-empty string "
                           "(spec: names identify the tool; an empty "
                           "name cannot be pinned)",
                           "non-empty string")
    rec: dict = {"name": name}
    for field in HASHED_FIELDS:
        if field == "name":
            continue
        if field == "annotations":
            rec["annotations"] = _normalize_annotations(
                tool.get("annotations"))
        else:
            rec[field] = tool.get(field)
    for k, v in tool.items():
        if k in EXCLUDED_FIELDS or k in rec:
            continue
        rec[k] = v
    return rec


def _digest(tool, where):
    return hashlib.sha256(_canon_bytes(_tool_record(tool,
                                                    where))).hexdigest()


def _listing_digest(tools, where="tools"):
    """Liste ORDONNÉE des empreintes (loi 3) — l'ordre change le
    digest, volontairement. Le `where` voyage : la même marche est
    appelée pour le listing vivant ET pour la baseline — un label
    codé en dur ment sur QUI est fautif (leçon du faux rouge
    openssl : un label suit le contexte, jamais la première
    vocation de la fonction)."""
    seen = {}
    for i, t in enumerate(tools):
        rec = _tool_record(t, "%s[%d]" % (where, i))
        nm = rec["name"]
        if nm in seen:
            raise SurfaceError(
                "%s[%d].name" % (where, i),
                "duplicate tool name '%s' (first at %s[%d]) — the "
                "MCP spec requires names unique within a server; a "
                "duplicated name is exactly the shadowing class, it "
                "is refused, never digested silently"
                % (nm, where, seen[nm]),
                "names unique per listing")
        seen[nm] = i
    digests = [_digest(t, "%s[%d]" % (where, i))
               for i, t in enumerate(tools)]
    surface = hashlib.sha256(_canon_bytes(digests)).hexdigest()
    return digests, surface


# ---------------------------------------------------------------- drift
def _diff_records(old_rec, new_rec):
    """Champs qui diffèrent, par clé triée (loi 7) — y compris les
    clés inconnues qui font leur apparition ou disparaissent."""
    keys = sorted(set(old_rec) | set(new_rec))
    return [k for k in keys if old_rec.get(k) != new_rec.get(k)]


def _hint_flips(old_ann, new_ann):
    if not (isinstance(old_ann, dict) and isinstance(new_ann, dict)):
        return None
    flips = []
    for hint in _HINT_ORDER:
        o = old_ann.get(hint)
        n = new_ann.get(hint)
        if o != n:
            flips.append({"hint": hint, "from": o, "to": n})
    return flips or None


def _diff_listings(baseline, tools):
    old = {}
    for i, t in enumerate(baseline):
        rec = _tool_record(t, "baseline[%d]" % i)
        nm = rec["name"]
        if nm in old:
            raise SurfaceError(
                "baseline[%d].name" % i,
                "duplicate tool name '%s' in the baseline listing — "
                "same rule as the live side" % nm,
                "names unique per listing")
        old[nm] = (i, rec)
    new = {}
    for i, t in enumerate(tools):
        new[t["name"]] = (i, _tool_record(t, "tools[%d]" % i))

    changed, removed, reordered = [], [], []
    for nm in sorted(old, key=lambda n: old[n][0]):   # ordre baseline
        i, rec = old[nm]
        if nm not in new:
            removed.append(nm)
            continue
        j, nrec = new[nm]
        if rec != nrec:
            entry = {"name": nm,
                     "fields": _diff_records(rec, nrec)}
            if "annotations" in entry["fields"]:
                flips = _hint_flips(rec.get("annotations"),
                                    nrec.get("annotations"))
                if flips:
                    entry["hint_flips"] = flips
            changed.append(entry)
        elif i != j:
            reordered.append(nm)
    added = [nm for nm in new if nm not in old]       # ordre listing

    # loi 7b — un DÉPLACEMENT n'est prescrit que quand les noms
    # sont les mêmes des deux côtés : si un outil est ajouté ou
    # retiré, le décalage d'indice des survivants est un COROLLAIRE
    # de l'événement, jamais un second événement compté deux fois
    # (sinon chaque retrait invente N déplacements — douleur
    # mesurée au tracé des tests, test_added_removed_counts_and_
    # orders).
    if added or removed:
        reordered = []

    if changed or removed or added:
        verdict = "DRIFT"
    elif reordered:
        verdict = "REORDERED"
    else:
        verdict = "CLEAN"
    counts = {"added": len(added), "changed": len(changed),
              "removed": len(removed), "reordered": len(reordered),
              "unchanged": len(old) - len(removed) - len(changed)
                           - len(reordered)}
    return {"verdict": verdict, "changed": changed,
            "added": added, "removed": removed,
            "reordered": reordered, "counts": counts}


# ---------------------------------------------------------------- entry
def mcp_surface(tools, baseline=None):
    if not isinstance(tools, list):
        raise SurfaceError("tools", "tools must be a list — paste the "
                           "tools/list array itself", "array")
    if len(tools) > MAX_TOOLS:
        raise SurfaceError(
            "tools", "listing of %d tools refused — the closed ceiling "
            "is %d per call (no real client holds more; a bigger "
            "paste is judged per page upstream, never digested here)"
            % (len(tools), MAX_TOOLS), "at most %d tools" % MAX_TOOLS)
    if isinstance(baseline, list) and len(baseline) > MAX_TOOLS:
        raise SurfaceError(
            "baseline", "baseline of %d entries refused — same ceiling "
            "as the live side (%d)" % (len(baseline), MAX_TOOLS),
            "at most %d tools" % MAX_TOOLS)

    digests, surface = _listing_digest(tools)
    out = {
        "canon": CANON_RULE,
        "count": len(tools),
        "excluded_fields": dict(EXCLUDED_FIELDS),
        "fields_hashed": list(HASHED_FIELDS),
        "provenance": list(PROVENANCE),
        "surface_sha256": surface,
        "tools": [{"name": t["name"], "sha256": d}
                  for t, d in zip(tools, digests)],
    }
    if baseline is not None:
        if not isinstance(baseline, list):
            raise SurfaceError("baseline", "baseline must be a list — "
                               "paste the previous tools/list",
                               "array")
        _, b_surface = _listing_digest(baseline, "baseline")
        out.update(_diff_listings(baseline, tools))
        out["baseline_surface_sha256"] = b_surface
    return out
