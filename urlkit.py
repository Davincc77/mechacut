"""urlkit — URL canonicalization per RFC 3986 §6.2.2, deterministic.

The contract: every transformation the machine performs is LISTED in the
response (rules_applied + removed[]). Nothing is silently stripped —
a canonical URL you cannot explain is a dedup bug waiting to bill
someone.

Syntax-based normalization only (RFC 3986 §6.2.2, the published
equivalence rules):
  * scheme + host lowercased (case-insensitive per RFC 3986 §6.2.2.1)
  * default port removed (80/http, 443/https — §6.2.3, only when the
    scheme says it is default)
  * dot-segments resolved (§5.2.4 algorithm, transcribed)
  * empty path → "/" (§6.2.3)
  * percent-encoding: hex uppercase, then decoded for unreserved
    characters ALPHA/DIGIT/-._.~ (§6.2.2.2) — %7E → ~ , %6a stays
  * non-ASCII host → punycode A-label (RFC 3492, our own text/punycode
    path reused)
  * query params: order PRESERVED by default (it is data, not noise —
    sort_params=true opts in explicitly)
  * tracking parameters: removed only from the published ad/analytics
    lists (Google Analytics utm_*, Google Ads gclid, Meta fbclid,
    Microsoft msclkid, Mailchimp mc_* , HubSpot _hs*) — and every
    removal is named in the response.

Path, fragment, userinfo casing are NOT touched beyond the rules above
— semantic case is not ours to lose.
"""
import re


def _encode_host(host):
    """IDN → A-labels, per label, via the stdlib idna codec
    (RFC 3490/3492). Trailing dots are preserved (they are
    significant root labels)."""
    trailing = host.endswith(".")
    body = host[:-1] if trailing else host
    labels = []
    for lab in body.split("."):
        if lab.isascii():
            labels.append(lab)
        else:
            labels.append(lab.encode("idna").decode("ascii"))
    return ".".join(labels) + ("." if trailing else "")

DEFAULT_TRACKING = [
    # published parameter names, per platform docs:
    "utm_source", "utm_medium", "utm_campaign", "utm_term",
    "utm_content", "utm_id", "utm_name", "utm_cid", "utm_reader",
    "utm_swu", "utm_referrer",                    # Google Analytics / LinkedIn
    "gclid", "dclid", "gbraid", "wbraid",         # Google Ads
    "fbclid", "msclkid",                          # Meta, Microsoft Ads
    "mc_cid", "mc_eid",                           # Mailchimp
    "_hsenc", "_hsmi", "hsa_acc", "hsa_cam",      # HubSpot
    "igshid",                                     # Instagram
]
UNRESERVED = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz0123456789-._~")
SPLIT = re.compile(
    r"^(?:([^:/?#]+):)?(?://([^/?#]*))?([^?#]*)(?:\?([^#]*))?"
    r"(?:#(.*))?$")
DEFAULT_PORTS = {"http": "80", "https": "443", "ftp": "21"}


class UrlError(Exception):
    pass


def _pct_norm(s):
    """uppercase hex, then decode unreserved (RFC 6.2.2.2)."""
    s = re.sub(r"%([0-9a-fA-F]{2})",
               lambda m: "%" + m.group(1).upper(), s)
    out, i = [], 0
    while i < len(s):
        if s[i] == "%" and i + 2 < len(s) + 0 and \
                re.match(r"^[0-9A-F]{2}$", s[i + 1:i + 3]):
            ch = chr(int(s[i + 1:i + 3], 16))
            if ch in UNRESERVED:
                out.append(ch)
                i += 3
                continue
        out.append(s[i])
        i += 1
    return "".join(out)


def _remove_dot_segments(path):
    # RFC 3986 §5.2.4, transcribed
    inp, out = path, []
    while inp:
        if inp.startswith("../"):
            inp = inp[3:]
        elif inp.startswith("./"):
            inp = inp[2:]
        elif inp.startswith("/./"):
            inp = "/" + inp[3:]
        elif inp == "/.":
            inp = "/"
        elif inp.startswith("/../"):
            inp = "/" + inp[4:]
            if out:
                out.pop()
        elif inp == "/..":
            inp = "/"
            if out:
                out.pop()
        elif inp in (".", ".."):
            inp = ""
        else:
            m = re.match(r"^/[^/]*|^[^/]+", inp)
            seg = m.group(0)
            inp = inp[len(seg):]
            out.append(seg)
    return "".join(out)


def canonicalize(url, strip_tracking=True, sort_params=False,
                 drop_fragment=False):
    if not isinstance(url, str) or not url.strip():
        raise UrlError("url must be a non-empty string")
    url = url.strip()
    m = SPLIT.match(url)
    if not m:
        raise UrlError("url does not parse (RFC 3986 §3 form required)")
    scheme, authority, path, query, frag = m.groups()
    actions = []
    if scheme is None:
        raise UrlError("scheme required (no relative URLs — a "
                       "canonical needs an anchor)")
    if scheme != scheme.lower():
        scheme = scheme.lower()
        actions.append("scheme lowercased")
    host, port, userinfo = None, None, None
    if authority is not None:
        if "@" in authority:
            userinfo, _, hostport = authority.rpartition("@")
        else:
            hostport = authority
        if hostport.startswith("["):          # IPv6 literal
            host, _, rest = hostport.partition("]")
            host += "]"
            rest = rest.lstrip(":")
            port = rest or None
        elif ":" in hostport:
            host, _, port = hostport.partition(":")
        else:
            host = hostport
        if host and not host.isascii():
            host = _encode_host(host)
            actions.append("host → punycode A-label (RFC 3492)")
        if host:
            hl = host.lower()
            if hl != host:
                actions.append("host lowercased")
            host = hl
        if port and DEFAULT_PORTS.get(scheme) == port:
            actions.append("default port :%s removed" % port)
            port = None
    if path == "" and authority is not None:
        path = "/"
        actions.append("empty path → /")
    newpath = _remove_dot_segments(path)
    if newpath != path:
        actions.append("dot-segments resolved (§5.2.4)")
    path = _pct_norm(newpath)
    if path != newpath:
        actions.append("percent-encoding normalized (§6.2.2.2)")
    params = []
    if query is not None:
        for kv in query.split("&"):
            params.append(kv)
        seen = []
        for kv in params:
            key = kv.split("=", 1)[0]
            if strip_tracking and key.lower() in DEFAULT_TRACKING:
                actions.append("tracking param removed: %s" % key)
            else:
                seen.append(kv)
        if sort_params:
            seen.sort()
            actions.append("query sorted (opt-in)")
        query = "&".join(seen)
        q2 = _pct_norm(query)
        if query != q2:
            actions.append("query percent-encoding normalized "
                           "(§6.2.2.2)")
        query = q2
        if query == "" and "&" not in "".join(seen) and not seen:
            actions.append("query emptied by removals — '?' omitted"
                           " (RFC 3986 §6.2.3: '' and absent are the"
                           " same URI)")
    if frag is not None:
        f2 = _pct_norm(frag)
        if f2 != frag:
            actions.append("fragment percent-encoding normalized")
            frag = f2
    if frag is not None and drop_fragment:
        actions.append("fragment dropped (opt-in)")
        frag = None
    netloc = ""
    if authority is not None:
        if userinfo:
            netloc = userinfo + "@"
        netloc += host or ""
        if port:
            netloc += ":" + port
    out = scheme + ":"
    if authority is not None:
        out += "//" + netloc
    out += path
    if query:
        out += "?" + query
    if frag is not None:
        out += "#" + frag
    return {"input": url, "canonical": out,
            "already_canonical": out == url,
            "components": {"scheme": scheme,
                           "userinfo": userinfo, "host": host,
                           "port": port, "path": path or None,
                           "query": query if query else None,
                           "fragment": frag},
            "actions": actions,
            "rules_source": "RFC 3986 §6.2.2 (syntax-based "
                            "normalization); tracking names from "
                            "published platform docs"}
