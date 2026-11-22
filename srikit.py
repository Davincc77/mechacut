"""srikit — /api/v1/net/sri : l'attribut Subresource Integrity prêt à
coller, PLUS l'audit du style qui AVEUGLE un vérificateur. Jamais de
fetch : ce module ne télécharge RIEN — il opère sur des octets locaux
(fournis) ou sur la chaîne integrity qu'on lui montre.

Douleurs (veille forums & CVE, items 7+) :
  1. Le pipeline openssl à deux étages que chaque agent refait à la
     main (guides de remediation nov. 2026 : webshield.orygn, siteyvm,
     zoroseoaudit — tous citent `openssl dgst -sha384 -binary |
     openssl base64 -A`) : un appel, mêmes octets, même base64.
  2. CVE-2026-120423 (undici, 6 nov. 2026, patché 11 nov.) : le
     parseur de metadata ne scindait que sur ESPACE ; un préfixe TAB
     faisait sauter TOUS les tokens et le corps altéré était accepté
     INCONDITIONNELLEMENT. Notre audit d'attribut signale la classe
     (TAB/NL entre tokens, casse, séparateurs) AVANT qu'un
     vérificateur myope ne l'avale.
  3. Le piège du hash sur URL mouvante : socket.dev (« the file
     changed: a range or latest URL moved ») + Chrome Modern Web
     Guidance (« digest from the bytes you reviewed, never from the
     live response ») — nos audits d'URL signalent @latest / @majeur
     seul / non-versionné comme panne programmée.
  4. L'honnêteté de portée (jamilxt nov. 2026 + Optizely dev.to) :
     « SRI answers "are these the expected bytes?" — not "were these
     bytes safe?" » et « nobody pins a hash on a snippet whose whole
     purpose is to change » — le scope_note est dans la réponse.

Spec ancrée : W3C SRI (Subresource Integrity, https://www.w3.org/TR/SRI/) :
  integrity-values = 1#hash-source ; hash-source = hash-function-name
  "-" base64-value ; base64 = RFC 4648 ; noms supportés sha256/sha384/
  sha512 ; un user agent choisit LA fonction la plus forte qu'il
  supporte parmi les tokens (pas « toutes vérifiées ») ; le fetch doit
  être CORS (d'où crossorigin="anonymous" obligatoire cross-origin).
  RFC 9620 (digest unification) pour la forme des algos.
Refus nommés : sha1/md5 — « supported by no modern browser » (MDN) ;
algorithme inconnu ; base64 malformé ; taille > 4 Mo.

Aucun état module : tout en paramètre (threads FastAPI).
"""
import base64
import binascii
import hashlib
import re

MAX_BYTES = 4 * 1024 * 1024
SUPPORTED = ("sha256", "sha384", "sha512")
# force croissante pour la note « strongest wins »
_STRENGTH = {"sha256": 256, "sha384": 384, "sha512": 512}
_B64 = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")
_TOKEN = re.compile(r"^([A-Za-z0-9\-+.]+)-([^ ]*)$")

# URL mouvantes = panne programmée (socket.dev, zoroseoaudit, spec.website)
_CDN_HOSTS = re.compile(r"(jsdelivr|unpkg|cdnjs)\.", re.I)
_LATEST = re.compile(r"[@/]latest(?:[/?#]|$)", re.I)
_VER_FULL = re.compile(r"@(\d+)\.(\d+)\.(\d+)")
_VER_PARTIAL = re.compile(r"@(\d+)(?:\.(\d+))?(?=[/.]|$)")
_SEG_VER = re.compile(r"/\d+\.\d+\.\d+(?:\.\d+)?/")


class SriError(ValueError):
    def __init__(self, field, message, expected):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected


def _b64_digest(algo, data):
    return base64.b64encode(hashlib.new(algo, data).digest()).decode()


def run_sri(args):
    args = dict(args or {})
    raw_b64 = args.get("bytes_b64")
    text = args.get("text")
    algs = args.get("algorithms") or ["sha384"]
    url = args.get("url")
    attr = args.get("integrity_attr")

    if isinstance(algs, str):
        algs = [algs]
    if not isinstance(algs, list) or not algs:
        raise SriError("algorithms", "algorithms must be a non-empty list",
                       "subset of sha256/sha384/sha512")
    for a in algs:
        if a not in SUPPORTED:
            raise SriError(
                "algorithms",
                "algorithm %r is not usable in an integrity attribute"
                % (a,),
                "sha256|sha384|sha512 — sha1/md5 are refused by modern "
                "browsers outright")

    if raw_b64 is not None and text is not None:
        raise SriError("bytes_b64", "bytes_b64 and text are both given",
                       "exactly one: the octets b64-wrapped, or UTF-8 "
                       "text (declared)")
    if raw_b64 is None and text is None and attr is None:
        raise SriError(
            "bytes_b64", "nothing to do",
            "give bytes_b64/text of the exact local file, or an "
            "integrity_attr to audit. This tool NEVER fetches a URL.")
    if url and raw_b64 is None and text is None:
        raise SriError(
            "bytes_b64", "a url alone is not verifiable here",
            "we never fetch — pass the octets you actually reviewed "
            "(bytes_b64 or text). Passing the live response to be "
            "hashed defeats the whole point (digest from reviewed "
            "bytes, never from the wire).")

    data = None
    source = None
    if text is not None:
        data = str(text).encode("utf-8")
        source = "text re-encoded as UTF-8 octets (declared)"
    elif raw_b64 is not None:
        try:
            data = base64.b64decode(str(raw_b64), validate=True)
        except (binascii.Error, ValueError):
            raise SriError("bytes_b64", "bytes_b64 does not decode",
                           "strict base64 of the exact file bytes")
        source = "bytes_b64 decoded strictly"

    out = {"tool": "net_sri", "source": source if data is not None
           else "integrity_attr audit only — no octets were given"}

    if data is not None:
        if len(data) > MAX_BYTES:
            raise SriError("bytes_b64",
                           "payload %d bytes over 4 MiB cap" % len(data),
                           "assets are small by nature; hash the exact "
                           "file you ship, not a monolith")
        out["byte_count"] = len(data)
        hashes = {a: _b64_digest(a, data) for a in algs}
        out["hashes"] = hashes
        # ordre W3C : tokens séparés par ESPACE simple ; le plus fort
        # d'abord n'est pas requis — mais la sémantique est « strongest
        # supported wins », PAS « tous vérifiés » (déclaré).
        ordered = sorted(algs, key=lambda a: -_STRENGTH[a])
        integrity = " ".join("%s-%s" % (a, hashes[a]) for a in ordered)
        out["integrity"] = integrity
        out["attributes"] = {"integrity": integrity,
                             "crossorigin": "anonymous"}
        out["strongest_wins_note"] = (
            "with multiple tokens a user agent verifies against the "
            "STRONGEST hash it supports, not all of them (W3C SRI) — "
            "listing more is insurance, not double checking")
        if url:
            safe = url.replace('"', "&quot;")
            out["tags"] = {
                "script": '<script src="%s" integrity="%s" '
                          'crossorigin="anonymous"></script>'
                          % (safe, integrity),
                "stylesheet": '<link rel="stylesheet" href="%s" '
                              'integrity="%s" crossorigin="anonymous">'
                              % (safe, integrity),
            }
        if attr is not None:
            given = {a: t for a, t in _tokens(attr)}
            verdict = []
            for a in algs:
                if a in given:
                    verdict.append({"algorithm": a,
                                    "match": given[a] == hashes[a],
                                    "detail": None if given[a] == hashes[a]
                                    else "the attribute names a "
                                         "different digest than the "
                                         "LOCAL octets produce — the "
                                         "browser will refuse this file"})
            out["attr_comparison"] = verdict
            findings = _audit_style(attr, "integrity_attr")
            out["attr_audit"] = findings
    else:
        out["attr_audit"] = _audit_style(str(attr), "integrity_attr")
        out["verify_note"] = ("style audit only — no octets were given, "
                              "so nothing here proves the file itself "
                              "matches; pass bytes_b64 to verify")

    if url:
        out["url_audit"] = _audit_url(url)
    out["crossorigin_note"] = (
        "crossorigin=\"anonymous\" is not optional for cross-origin "
        "assets: without CORS the browser cannot read the response to "
        "hash it and refuses the resource (MDN/W3C)")
    out["scope_note"] = (
        "SRI answers 'are these the expected bytes?' — NOT 'were these "
        "bytes safe?' (jamilxt, nov. 2026). A snippet whose purpose is "
        "to change (A/B payloads, per-account vendor scripts) cannot "
        "be pinned honestly — nobody pins a moving file (Optimizely "
        "incident, 188 sites): that class needs CSP + blast-radius, "
        "not a hash workaround. This tool never fetched anything.")
    out["pipeline_note"] = ("equivalent published pipeline: "
                            "openssl dgst -sha384 -binary | "
                            "openssl base64 -A, run on the exact local "
                            "file (MDN)")
    return out


def _tokens(value):
    """Découpe façon W3C : 1#hash-source, séparateurs = ASCII whitespace
    (espace ET tab/NL en HTML). Rend (algo, base64) par token."""
    parts = re.split(r"[ \t\r\n\f]+", value.strip()) if value.strip() \
        else []
    out = []
    for p in parts:
        if not p:
            continue
        m = _TOKEN.match(p)
        if m:
            out.append((m.group(1), m.group(2)))
        else:
            out.append((None, p))
    return out


def _audit_style(value, field):
    findings = []
    # classe CVE-2026-120423 : TAB/NL entre tokens = un parseur qui ne
    # scinde QUE sur espace saute tout et accepte n'importe quel corps
    if re.search(r"[\t\r\n\f]", value):
        findings.append({
            "level": "danger",
            "finding": "non-space ASCII whitespace inside the integrity "
                       "value",
            "why": "HTML splits tokens on ALL ASCII whitespace, but a "
                   "space-only verifier (undici CVE-2026-120423, fixed "
                   "11 nov. 2026) silently skipped EVERY token behind a "
                   "TAB prefix and accepted tampered bodies "
                   "unconditionally",
            "fix": "rewrite the attribute with single SPACES between "
                   "tokens"})
    stripped = value.strip()
    if stripped != value:
        findings.append({"level": "style",
                         "finding": "leading/trailing whitespace around "
                                    "the attribute value",
                         "why": "parsers differ at the edges — the TAB-"
                                "skip class starts here",
                         "fix": "trim; tokens separated by single spaces"})
    tokens = _tokens(value)
    seen = set()
    for algo, b64 in tokens:
        if algo is None:
            findings.append({"level": "danger",
                             "finding": "malformed token %r" % b64,
                             "why": "not 'algo-base64' per W3C grammar",
                             "fix": "e.g. sha384-<base64>"})
            continue
        if algo not in SUPPORTED:
            hint = ("refused outright by modern browsers" if algo in
                    ("sha1", "md5", "sha224", "sha3-384", "blake2b")
                    else "unknown algorithm name")
            findings.append({"level": "danger",
                             "finding": "algorithm %r is %s"
                                        % (algo, hint),
                             "why": "the whole token is then unusable — "
                                    "browsers fall back to no SRI or "
                                    "refuse the resource",
                             "fix": "use one of sha256/sha384/sha512"})
            continue
        if algo != algo.lower():
            findings.append({"level": "style",
                             "finding": "algorithm name %r not lowercase"
                                        % algo,
                             "why": "MDN and every CDN publish the "
                                    "lowercase form; some verifiers "
                                    "compare case-sensitively",
                             "fix": "lowercase the name"})
        if not _B64.match(b64 or ""):
            findings.append({"level": "danger",
                             "finding": "invalid base64 for %s token"
                                        % algo,
                             "why": "a corrupt digest never matches — "
                                    "the file will be blocked in "
                                    "production at first load",
                             "fix": "regenerate from the reviewed bytes"})
            continue
        try:
            dec = base64.b64decode(b64, validate=True)
            want = int(algo[3:]) // 8
            if len(dec) != want:
                findings.append({
                    "level": "danger",
                    "finding": "%s digest is %d bytes, must be %d"
                               % (algo, len(dec), want),
                    "why": "wrong-length digest = truncated or copied "
                           "value — guaranteed mismatch",
                    "fix": "regenerate from the exact reviewed file"})
        except (binascii.Error, ValueError):
            findings.append({"level": "danger",
                             "finding": "base64 will not decode for %s"
                                        % algo,
                             "why": "strict decoders refuse padding/"
                                    "charset errors browsers tolerate",
                             "fix": "regenerate"})
        if algo in seen:
            findings.append({"level": "style",
                             "finding": "duplicate algorithm %r" % algo,
                             "why": "W3C picks the strongest SUPPORTED "
                                    "token, not each in turn — a "
                                    "duplicate adds ambiguity, not "
                                    "security",
                             "fix": "one token per algorithm"})
        seen.add(algo)
    if not tokens:
        findings.append({"level": "danger", "finding": "empty integrity "
                         "value", "why": "equivalent to no SRI at all",
                         "fix": "generate from the reviewed bytes"})
    return findings


def _audit_url(url):
    findings = []
    if url.startswith("http://"):
        findings.append({"level": "danger", "finding": "plain http url",
                         "why": "integrity over an unauthenticated "
                                "channel still lets a MITM swap both "
                                "file and page context; modern browsers "
                                "block mixed passive content anyway",
                         "fix": "https"})
    m = _LATEST.search(url)
    if m:
        findings.append({"level": "danger", "finding": m.group(0).lstrip("@/"),
                         "why": "'latest' is a MOVING alias — the CDN "
                                "serves new bytes under the same URL, so "
                                "the pinned hash fails at the next update "
                                "(planned outage)",
                         "fix": "pin the FULL immutable version, then "
                                "hash THAT url's bytes"})
    elif _CDN_HOSTS.search(url):
        full = _VER_FULL.search(url)
        seg = _SEG_VER.search(url)
        if full or seg:
            pass  # version complète quelque part dans le chemin
        else:
            part = _VER_PARTIAL.search(url)
            if part:
                findings.append({
                    "level": "warn", "finding": part.group(0),
                    "why": "major/minor RANGE tag (@5, @5.3) — the "
                           "patch stream keeps rewriting those bytes",
                    "fix": "pin the FULL immutable version, then hash "
                           "THAT url's bytes"})
            else:
                findings.append({
                    "level": "danger", "finding": "no version segment",
                    "why": "unversioned CDN path — every 'latest' build "
                           "overwrites it; a hash here is a time bomb",
                    "fix": "pin the FULL immutable version, then hash "
                           "THAT url's bytes"})
    if not findings:
        findings.append({"finding": "url carries an explicit full "
                         "version segment", "status": "pinnable"})
    return findings
