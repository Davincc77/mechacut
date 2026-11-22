"""Bundle A1 — Determinism Auditor.

/integrity/verify takes a target's PUBLISHED pins (their integrity.json,
or an explicit list) and answers one question vendors cannot answer
from their own logs: do two identical calls return identical bytes?

Safety by construction — this endpoint fetches URLs, so the closed
guards are the product:
  * https only; the hostname must resolve to a public address
    (loopback, private, link-local incl. cloud metadata 169.254.169.254,
    and reserved ranges are refused by name, not silently skipped);
  * redirects are followed manually and re-checked at every hop;
  * caps: 20 pins, 2-5 attempts, 20 fetches per call, 1 MB per response,
    a hard 25-second global budget — the auditor cannot be turned into
    an amplifier against anyone, including its own host.

Modes: "bytes" (sha256 over the exact response bytes — the strictest
determinism claim) and "json-canonical" (sha256 over the canonical JSON
re-serialisation, matching mechacut-style pin files; tolerates key
order and whitespace, NOT value drift).

The audit itself is deterministic: same target state in, same report
out — except the elapsed fields, which are excluded from the report's
sha256 by design.
"""
import hashlib
import ipaddress
import json
import socket
import urllib.parse
import time
from urllib.parse import urlsplit

import httpx

MAX_FETCHES = 20
MAX_PINS = 20
MAX_BYTES = 1_000_000
BUDGET_S = 25.0
_UA = "mechacut-auditor/1 (+https://mechacut.studio/agent/manifest)"


class AuditError(Exception):
    pass


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def canon_json(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _resolve_guard(url):
    """https + hostname -> at least one PUBLIC IP; returns the checked
    host. Every failure is a named refusal."""
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise AuditError("scheme %r refused: the auditor speaks https "
                         "only" % parts.scheme)
    host = parts.hostname
    if not host:
        raise AuditError("url has no hostname")
    try:
        infos = socket.getaddrinfo(host, parts.port or 443,
                                   proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise AuditError("dns failure for %r: %s" % (host, e))
    addrs = set()
    for fam, _t, _p, _c, sa in infos:
        ip = ipaddress.ip_address(sa[0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified
                or (ip.version == 6 and getattr(ip, "is_site_local",
                                                False))):
            raise AuditError("%s resolves to a non-public address "
                             "(%s) — refused by the SSRF guard; audit "
                             "LAN/metadata targets by running the "
                             "code, not the endpoint" % (host, ip))
        addrs.add(str(ip))
    return host, sorted(addrs)


def _fetch(client, url, method, body, deadline):
    if time.monotonic() > deadline:
        raise AuditError("global budget (25s) exhausted — partial "
                         "verdict is honest, unlimited patience is "
                         "an amplifier")
    r = client.request(method, url,
                       json=body if method == "POST" and body is not None
                       else None,
                       timeout=max(0.5, min(5.0, deadline
                                            - time.monotonic())))
    if len(r.content) > MAX_BYTES:
        raise AuditError("response exceeds the 1 MB cap")
    return r


def _request_with_redirects(client, url, method, body, deadline,
                            max_hops=3):
    seen = 0
    cur = url
    while True:
        _host, addrs = _resolve_guard(cur)
        r = _fetch(client, cur, method, body, deadline)
        if r.status_code in (301, 302, 303, 307, 308) and "location" \
                in r.headers:
            seen += 1
            if seen > max_hops:
                raise AuditError("more than %d redirects — refused"
                                 % max_hops)
            nxt = r.headers["location"]
            if not nxt.startswith("http"):
                base = urlsplit(cur)
                nxt = "%s://%s%s" % (base.scheme, base.netloc,
                                     nxt if nxt.startswith("/")
                                     else "/" + nxt)
            cur = nxt
            continue
        return r


def verify_pin(client, base, pin, attempts, mode, deadline):
    path = pin.get("path") or ""
    if not path.startswith("/"):
        raise AuditError("pin path must start with /")
    method = (pin.get("method") or "POST").upper()
    query = pin.get("query")
    if query:
        # sorted: the pin's bytes are the contract, dict order is not
        url = base + path + "?" + urllib.parse.urlencode(sorted(
            (k, str(v)) for k, v in query.items()))
    else:
        url = base + path
    body = pin.get("body")
    claim = pin.get("sha256")
    observed = []
    status = None
    first_error = None
    saw_paywall = False
    for _ in range(attempts):
        try:
            r = _request_with_redirects(client, url, method, body,
                                        deadline)
        except httpx.HTTPError as e:
            first_error = "%s: %s" % (type(e).__name__, str(e)[:120])
            break
        except AuditError as e:
            first_error = str(e)
            break
        status = r.status_code
        if status == 402 and b"x402Version" in r.content:
            saw_paywall = True
        if mode == "json-canonical":
            try:
                payload = r.json()
            except (ValueError, json.JSONDecodeError):
                first_error = "response is not JSON — json-canonical " \
                              "mode cannot apply; use bytes mode"
                status_out = r.status_code
                return {"name": pin.get("name", path), "path": path,
                        "status": status_out, "stable": False,
                        "error": first_error, "observed": []}
            digest = _sha(canon_json(payload))
        else:
            digest = _sha(r.content)
        observed.append(digest)
    stable = len(observed) > 1 and len(set(observed)) == 1
    paywalled = bool(saw_paywall)
    matches = None
    if claim and stable and not paywalled:
        matches = observed[0] == claim
    out = {"name": pin.get("name", path), "path": path,
           "status": status, "calls": len(observed),
           "observed_sha256": sorted(set(observed)),
           "stable": stable}
    if paywalled:
        out["paywalled"] = True
    if first_error:
        out["error"] = first_error
    if claim:
        out["claim_sha256"] = claim
        out["matches_claim"] = matches
    return out


def integrity_verify(base_url, pins=None, integrity_url=None,
                     attempts=3, mode="bytes"):
    t0 = time.monotonic()
    deadline = t0 + BUDGET_S
    if not isinstance(base_url, str) or not base_url.strip():
        raise AuditError("base_url required (https://target)")
    base = base_url.strip().rstrip("/")
    _resolve_guard(base + "/")          # checked once up front too
    if mode not in ("bytes", "json-canonical"):
        raise AuditError("mode is bytes or json-canonical")
    if not isinstance(attempts, int) or not 2 <= attempts <= 5:
        raise AuditError("attempts must be an integer 2-5")
    if pins is None:
        if not integrity_url:
            raise AuditError("pins or integrity_url required")
        iurl = integrity_url if integrity_url.startswith("http") \
            else base + integrity_url
        with httpx.Client(headers={"User-Agent": _UA},
                          follow_redirects=False) as client:
            r = _request_with_redirects(client, iurl, "GET", None,
                                        deadline)
        try:
            doc = r.json()
        except ValueError:
            raise AuditError("integrity_url did not return JSON")
        if not isinstance(doc, dict) or not isinstance(
                doc.get("pins"), list):
            raise AuditError("integrity doc needs {\"pins\": [...]} — "
                             "unknown formats get a named refusal, not "
                             "a guess")
        pins = doc["pins"]
    if not isinstance(pins, list) or not pins:
        raise AuditError("pins: non-empty list required")
    if len(pins) > MAX_PINS:
        raise AuditError("max %d pins per audit (the endpoint cannot "
                         "become a load generator)" % MAX_PINS)
    if len(pins) * attempts > MAX_FETCHES:
        raise AuditError("%d pins x %d attempts exceeds the %d-fetch "
                         "cap — lower attempts or audit in batches"
                         % (len(pins), attempts, MAX_FETCHES))
    results = []
    with httpx.Client(headers={"User-Agent": _UA},
                      follow_redirects=False) as client:
        for pin in pins:
            if not isinstance(pin, dict) or "path" not in pin:
                raise AuditError("each pin needs at least {path}")
            results.append(verify_pin(client, base, pin, attempts, mode,
                                      deadline))
    stable = sum(1 for x in results if x["stable"])
    paywalled = [x["name"] for x in results if x.get("paywalled")]
    claimed = [x for x in results if x.get("matches_claim") is not None]
    lying = [x["name"] for x in claimed if x["matches_claim"] is False]
    unreachable = [x["name"] for x in results
                   if x.get("error") and not x["stable"]]
    if unreachable and stable == 0:
        verdict = "unreachable: %s" % "; ".join(
            "%s (%s)" % (x["name"], x["error"])[:160]
            for x in results if x.get("error"))[:300]
    elif lying:
        verdict = "DIVERGENT from published claims: %s" % ", ".join(
            lying[:8])
    elif stable == len(results) and not paywalled:
        verdict = "deterministic under %s comparison (%d/%d pins, %d " \
                  "attempts each)" % (mode, stable, len(results),
                                      attempts)
    elif stable == len(results):
        verdict = ("deterministic on %d/%d pins; %d pin(s) paywalled "
                   "(402 itself stable — the gate is deterministic, the "
                   "paid answer needs one x402 call to verify): %s"
                   % (stable - len(paywalled), len(results),
                      len(paywalled), ", ".join(paywalled[:6])))
    else:
        drift = [x["name"] for x in results if not x["stable"]
                 and not x.get("error")]
        verdict = "NON-DETERMINISTIC: bytes differ between identical " \
                  "calls for %s" % ", ".join(drift[:8])
    report = {"target": base, "mode": mode, "attempts": attempts,
              "pins_audited": len(results), "stable": stable,
              "paywalled": len(paywalled),
              "unstable_or_refused": len(results) - stable,
              "results": results, "verdict": verdict}
    # elapsed is excluded from the fingerprint on purpose: the audit's
    # truth is its content, not its timing
    report["sha256"] = _sha(canon_json(
        {k: v for k, v in report.items() if k != "elapsed_ms"}))
    report["elapsed_ms"] = int((time.monotonic() - t0) * 1000)
    return report
