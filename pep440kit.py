"""pep440kit — bundle 135 (admission 27-11, registre L30, reçu 6aaf2824).

Tri de versions selon la grammaire PEP 440 : epochs (N!), releases
multi-segments, préreleases a/b/rc (alias alpha/beta/c/pre/preview),
.postN (alias rev/r et la forme implicite -N), .devN, versions locales
+label. La grammaire publiée (PEP 440 Appendix B) est RECOPIEE, pas
réinventée ; l'ordre suit la « Summary of permitted suffixes and
relative ordering » du même document.

Voisin nommé : semver_sort (micro.py) valide la grammaire semver.org —
il refuse les tokens PEP 440 par leur nom (mesure registre : « 7/7
listes PyPI »). Ici c'est l'inverse : un « 1.0.0-rc.1 » semver-valide
mais hors PEP 440 meurt NOMMÉ, en désignant semver_sort.

Exemple d'ordre publié (la liste du PEP lui-même, recopiée mot pour
mot dans les tests) — golds : pypi.org/en/latest/specifications/version-specifiers
et PEP 440, « The following example covers many of the possible
combinations ».
"""
import hashlib
import json
import re

GRAMMAR_NAME = "pep440-version-grammar"
GRAMMAR_VERSION = ("PEP 440 (Final, created 2013-03-18) — Appendix B "
                   "VERSION_PATTERN + ordering summary, transcrits "
                   "2026-11-27")
N_MIN, N_MAX = 1, 2000  # même plafond que semver_sort, nommé

VERSION_PATTERN = r"""
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>alpha|a|beta|b|preview|pre|c|rc)
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
"""

_regex = re.compile(r"^\s*" + VERSION_PATTERN + r"\s*$",
                    re.VERBOSE | re.IGNORECASE)

_PRE_ALIAS = {"alpha": "a", "a": "a", "beta": "b", "b": "b",
              "preview": "rc", "pre": "rc", "c": "rc", "rc": "rc"}
_PRE_RANK = {"a": 0, "b": 1, "rc": 2}


class PepError(Exception):
    def __init__(self, msg, field="versions"):
        super().__init__(msg)
        self.msg, self.field = msg, field


GRAMMAR_SHA256 = hashlib.sha256(json.dumps(
    {"name": GRAMMAR_NAME, "version": GRAMMAR_VERSION,
     "pattern": VERSION_PATTERN}, sort_keys=True,
    separators=(",", ":")).encode()).hexdigest()


def _local_key(local):
    if local is None:
        return (0,)
    segs = []
    for part in re.split(r"[-_.]", local.lower()):
        if part.isdigit():
            segs.append((1, "", int(part)))
        else:
            segs.append((0, part, 0))
    return (1, tuple(segs))


def _local_canon(local):
    if local is None:
        return None
    out = []
    for part in re.split(r"[-_.]", local.lower()):
        out.append(str(int(part)) if part.isdigit() else part)
    return ".".join(out)


def _parse(v, idx):
    if not isinstance(v, str):
        raise PepError(
            "versions[%d] is %s, not a string — PEP 440 versions are "
            "text, never numbers (1.0 as a float silently renames "
            "1.00; send the string)" % (idx, type(v).__name__),
            "versions")
    m = _regex.match(v)
    if not m:
        raise PepError(
            "not a PEP 440 version: %r — the closed grammar is "
            "[N!]N(.N)*[{a|b|rc}N][.postN][.devN][+<local>]; a valid "
            "semver string outside it (1.0.0-rc.1, build metadata) is "
            "semver_sort's contract, not this one; version specifiers "
            "(~=, ==) are requirements, not versions"
            % v, "versions[%d]" % idx)
    norm = []
    s = v
    if s != s.strip():
        norm.append("whitespace stripped")
    core = s.strip()
    if core[:1] in "vV":
        core = core[1:]
        norm.append("v prefix ignored")
    epoch = m.group("epoch")
    epoch = int(epoch) if epoch is not None else None
    if epoch == 0:
        norm.append("epoch 0! is the implicit epoch, dropped")
    release = [int(x) for x in m.group("release").split(".")]
    if re.search(r"0\d", m.group("release")):
        norm.append("leading zeros dropped (int())")
    pre_l = m.group("pre_l")
    pre = None
    rc_alias = False
    if pre_l is not None:
        phase = _PRE_ALIAS[pre_l.lower()]
        rc_alias = pre_l.lower() in ("c", "pre", "preview")
        pn = m.group("pre_n")
        pn = 0 if pn is None else int(pn)
        if pre_l.lower() != phase:
            norm.append("%s -> %s (spelling alias)"
                        % (pre_l.lower(), phase))
        if m.group("pre_n") is None:
            norm.append("implicit pre number 0 made explicit")
        pre = (phase, pn)
    post = None
    if m.group("post_n1") is not None:
        post = int(m.group("post_n1"))
        norm.append("-N is the implicit post form -> .postN")
    elif m.group("post_l") is not None:
        pn = m.group("post_n2")
        post = 0 if pn is None else int(pn)
        if m.group("post_l").lower() in ("rev", "r"):
            norm.append("%s -> post (spelling alias)"
                        % m.group("post_l").lower())
        if pn is None:
            norm.append("implicit post number 0 made explicit")
    dev = None
    if m.group("dev_l") is not None:
        dn = m.group("dev_n")
        dev = 0 if dn is None else int(dn)
        if dn is None:
            norm.append("implicit dev number 0 made explicit")
    local = m.group("local")
    if local is not None and local != local.lower():
        norm.append("local label lowercased")
    if local is not None and re.search(r"[-_]", local):
        norm.append("local separators -> '.'")

    canon = []
    if epoch not in (None, 0):
        canon.append("%d!" % epoch)
    canon.append(".".join(str(x) for x in release))
    if pre:
        canon.append("%s%d" % pre)
    if post is not None:
        canon.append(".post%d" % post)
    if dev is not None:
        canon.append(".dev%d" % dev)
    lc = _local_canon(local)
    if lc is not None:
        canon.append("+%s" % lc)
    canonical = "".join(canon)

    dev_only_trick = (pre is None and post is None and dev is not None)
    _pre = ((0,) if dev_only_trick else
            (2,) if pre is None else (1, _PRE_RANK[pre[0]], pre[1]))
    _post = (0,) if post is None else (1, post)
    _dev = (2,) if dev is None else (1, dev)
    relkey = tuple(release)
    while len(relkey) > 1 and relkey[-1] == 0:
        relkey = relkey[:-1]   # « X.Y and X.Y.0 are not considered
                               # distinct » (règle de padding publiée)
    key = (0 if epoch is None else epoch, relkey, _pre,
           _post, _dev, _local_key(local))
    parts = {"epoch": epoch if epoch not in (None, 0) else None,
             "release": release, "pre": ({"phase": pre[0],
                                         "number": pre[1]} if pre
                                        else None),
             "post": post, "dev": dev, "local": lc}
    return {"given": v, "canonical": canonical, "parts": parts,
            "normalizations": norm, "_rc_alias": rc_alias, "_key": key}


def sort_versions(versions, descending=None):
    applied = []
    if descending is None:
        descending = False
        applied.append("descending=false (PEP 440 ascending release "
                       "order)")
    if not isinstance(versions, list) or \
            not N_MIN <= len(versions) <= N_MAX:
        raise PepError(
            "versions: a list of %d..%d PEP 440 strings (same closed "
            "cap as semver_sort) — empty lists and 2001-item inventories "
            "are refused, never guessed at" % (N_MIN, N_MAX))
    parsed = [_parse(v, i) for i, v in enumerate(versions)]
    order = sorted(range(len(parsed)), key=lambda i: parsed[i]["_key"],
                   reverse=descending)
    sorted_g = [parsed[i]["given"] for i in order]
    sorted_c = [parsed[i]["canonical"] for i in order]
    equivalences = []
    by_key = {}
    for i in order:
        by_key.setdefault(parsed[i]["_key"], []).append(i)
    for grp in by_key.values():
        givens = {parsed[i]["given"] for i in grp}
        if len(givens) > 1:
            equivalences.append([parsed[i]["given"] for i in grp])
    flags = []
    if any(p["parts"]["pre"] and p["_rc_alias"] for p in parsed):
        flags.append("c_alias: 'c'/'pre'/'preview' spellings sort as "
                     "'rc' (PEP 440) — index tools MAY refuse two "
                     "spellings for one release segment; sorting "
                     "keeps them equal, never rewrites history")
    entries = [{k: p[k] for k in ("given", "canonical", "parts",
                                  "normalizations")} for p in parsed]
    return {"sorted": sorted_g,
            "sorted_canonical": sorted_c,
            "count": len(parsed),
            "descending": bool(descending),
            "entries": entries,
            "equivalences": equivalences,
            "flags": flags,
            "grammar": {"name": GRAMMAR_NAME,
                        "version": GRAMMAR_VERSION,
                        "sha256": GRAMMAR_SHA256},
            "applied_defaults": applied}
