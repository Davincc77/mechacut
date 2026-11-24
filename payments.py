"""x402 v1 per-call payments (EIP-3009 / USDC on Base) — three tiers:

  🟢 free    — unpriced routes keep the keyless rate limit (RATE_LIMIT
               req/min/IP, no account). A 402 never touches the daily loop.
  🟡 capped  — free while the request payload stays under CAP_BYTES (32 KB);
               above it, the route requires x402 per call. Small jobs stay
               frictionless, whales pay automatically.
  🔴 priced  — x402 required from the first request.

400s are always free; settlement runs only after a successful (<400)
response. Unpaid attempts on priced routes (and capped routes over the cap)
answer 402 BEFORE validation, so they are counted separately as
kind=payment_required in /misses.json.

Env (all optional; MECHACUT_PAY_TO unset = payments off, 429 behavior):
  MECHACUT_PAY_TO       receiving address on Base. Unset = payments off.
  MECHACUT_NETWORK      "base" (default, mainnet) or "base-sepolia" (testnet)
  MECHACUT_ASSET        ERC-20 contract override (default: USDC per network)
  MECHACUT_FACILITATOR  default https://facilitator.payai.network
                        (public facilitator supporting x402 v1 on Base
                        mainnet; the reference x402.org facilitator is
                        testnets-only and CDP requires an API key)

Prices (USDC atomic units, 6 decimals):
  /api/v1/chart          1000  ($0.001)                       🔴
  /api/v1/reshape         500  ($0.0005)                      🔴
  /api/v1/validate        500  ($0.0005) above 32 KB          🟡
  /api/v1/csv/join        500  ($0.0005)                      🔴
  /api/v1/table/pivot     500  ($0.0005)                      🔴
  /api/v1/json/patch      500  ($0.0005) above 32 KB          🟡
  /api/v1/csv/fix         500  ($0.0005) above 32 KB          🟡
  /api/v1/csv/types       500  ($0.0005) above 32 KB          🟡
  /api/v1/format/convert  500  ($0.0005) above 32 KB          🟡
  /api/v1/text/diff       500  ($0.0005) above 32 KB          🟡
  /api/v1/ics/generate    500  ($0.0005) above 32 KB          🟡
  /api/v1/ics/parse       500  ($0.0005) above 32 KB          🟡
  /api/v1/number/spell    500  ($0.0005) above 32 KB          🟡
  /api/v1/validate/iban   free (V21: rival gratuit même byte — 22-11)🟢
  /api/v1/text/chunk     1000  ($0.001)                       🔴
  /api/v1/html/text     1000  ($0.001)                       🔴
  /api/v1/md/render       500  ($0.0005) above 32 KB          🟡
  /api/v1/extract/facts   500  ($0.0005) above 32 KB          🟡
  /api/v1/batch           500  ($0.0005) above 32 KB          🟡
  /api/v1/eth/abi-encode  500  ($0.0005) above 32 KB          🟡
  /api/v1/eth/abi-decode  500  ($0.0005) above 32 KB          🟡
  /api/v1/text/patch      500  ($0.0005)                      🔴
  /api/v1/text/apply-diff 500  ($0.0005)                      🔴
  /api/v1/money/prorate   500  ($0.0005)                      🔴

The server holds only a one-minute-window replay-protection set of payment
nonces in memory. It never sees a private key: verification and on-chain
settlement are done by the facilitator.
"""

import base64
import json
import os
import threading

import httpx
from fastapi.responses import JSONResponse

USDC = {
    "base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "base-sepolia": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
}

CAP_BYTES = 32 * 1024
PRICES = {
    "/api/v1/chart": "1000",
    "/api/v1/reshape": "500",
    "/api/v1/csv/join": "500",
    "/api/v1/table/pivot": "500",
    "/api/v1/text/patch": "500",
    "/api/v1/text/apply-diff": "500",
    "/api/v1/money/prorate": "500",
    "/api/v1/text/chunk": "1000",
    "/api/v1/html/text": "1000",
    "/api/v1/integrity/verify": "1000",
}
# 🟡 capped routes: free under CAP_BYTES, then priced per call.
CAP_ROUTES = {
    "/api/v1/validate": "500",
    "/api/v1/agent/context-tax": "500",
    "/api/v1/json/patch": "500",
    "/api/v1/csv/fix": "500",
    "/api/v1/csv/types": "500",
    "/api/v1/format/convert": "500",
    "/api/v1/text/diff": "500",
    "/api/v1/ics/generate": "500",
    "/api/v1/image/rightsize": "500",
    "/api/v1/web/cert": "500",
    "/api/v1/xml/to_json": "500",
    "/api/v1/csv/money_columns": "500",
    "/api/v1/table/sql_dump": "500",
    "/api/v1/ics/parse": "500",
    "/api/v1/number/spell": "500",
    "/api/v1/md/render": "500",
    "/api/v1/extract/facts": "500",
    "/api/v1/batch": "500",
    "/api/v1/eth/abi-encode": "500",
    "/api/v1/eth/abi-decode": "500",
    "/api/v1/doc/text": "1000",
}
PRICE_LABELS = {
    "/api/v1/chart": "$0.001",
    "/api/v1/reshape": "$0.0005",
    "/api/v1/csv/join": "$0.0005",
    "/api/v1/table/pivot": "$0.0005",
    "/api/v1/text/patch": "$0.0005",
    "/api/v1/text/apply-diff": "$0.0005",
    "/api/v1/money/prorate": "$0.0005",
    "/api/v1/text/chunk": "$0.001",
    "/api/v1/html/text": "$0.001",
    "/api/v1/integrity/verify": "$0.001",
}


def pay_to():
    return os.environ.get("MECHACUT_PAY_TO", "").strip()


def _splitters_file():
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "docs", "proposals", "splitters.json")
    return os.environ.get("MECHACUT_SPLITTERS", default)


def pay_to_for(path):
    """payTo of the challenge: the tool's registered splitter when
    docs/proposals/splitters.json (git, human-committed) gives one with
    a VALID EIP-55 address; the env pay_to() otherwise. The file is
    never trusted before being served: a malformed address falls back
    to the global one — a wrong payTo silently burns every payment."""
    import json
    try:
        m = json.loads(open(_splitters_file(), encoding="utf-8").read())
    except (OSError, ValueError):
        return pay_to()
    cand = str(m.get(path, "")).strip()
    if not cand:
        return pay_to()
    if _valid_eip55(cand):
        return cand
    return pay_to()


def splitter_note(path):
    """What the server did, in words — for audits, never guessed."""
    import json
    try:
        m = json.loads(open(_splitters_file(), encoding="utf-8").read())
    except (OSError, ValueError):
        return "fallback_env"
    cand = str(m.get(path, "")).strip()
    if not cand:
        return "fallback_env"
    if _valid_eip55(cand):
        return "splitter_registered"
    return "ignored_grammar"


def _valid_eip55(addr):
    import eth
    try:
        return bool(eth.eth_address(addr)["valid_eip55"])
    except eth.EthError:
        return False


def network():
    return os.environ.get("MECHACUT_NETWORK", "base").strip()


def asset():
    return os.environ.get("MECHACUT_ASSET", "").strip() or USDC.get(network(), "")


def facilitator():
    return os.environ.get("MECHACUT_FACILITATOR",
                          "https://facilitator.payai.network").rstrip("/")


def price(path):
    return PRICES.get(path) or CAP_ROUTES.get(path)


def enabled(path, size=None):
    """Payments are live only when MECHACUT_PAY_TO is set, and:
    always on priced routes; on capped routes only when the payload
    exceeds CAP_BYTES (size=None = unknown = treated as under cap)."""
    if not pay_to():
        return False
    if path in PRICES:
        return True
    if path in CAP_ROUTES:
        return size is not None and size > CAP_BYTES
    return False


def _requirement(url, path):
    desc = f"MechaCut {path} per-call fee"
    if path in CAP_ROUTES:
        desc = (f"MechaCut {path} per-call fee "
                f"(payload over {CAP_BYTES} bytes; under it the call is free)")
    return {
        "scheme": "exact",
        "network": network(),
        "maxAmountRequired": price(path),
        "resource": url,
        "description": desc,
        "mimeType": "application/json",
        "payTo": pay_to_for(path),
        "maxTimeoutSeconds": 60,
        "asset": asset(),
        # EIP-712 domain of the token on THIS network: test USDC on
        # Base Sepolia is "USDC"/"2"; mainnet is "USD Coin"/"2".
        # The facilitator signs-against this extra — lying here kills
        # every payment with invalid_exact_evm_signature (caught by the
        # E2E probe, unit tests cannot see it)
        "extra": ({"name": "USDC", "version": "2"}
                  if network() == "base-sepolia"
                  else {"name": "USD Coin", "version": "2"}),
    }


def requirements(url, path):
    """The 402 body an x402 client parses to build a payment."""
    return {
        "x402Version": 1,
        "error": "X-PAYMENT header is required",
        "accepts": [_requirement(url, path)],
    }


def payment_required(url, path, reason=None):
    body = requirements(url, path)
    if reason:
        body["error"] = reason
    return JSONResponse(status_code=402, content=body)


def decode_payment(header_value):
    """X-PAYMENT is base64-encoded JSON (x402 v1 PaymentPayload).
    Strict: a JSON body sent raw (the obvious client mistake) is
    refused, not leniently digested into garbage."""
    raw = None
    h = header_value.strip()
    if h.startswith("{"):
        raise ValueError("X-PAYMENT must be base64 of the JSON payload, "
                         "not the JSON itself")
    # a header cannot smuggle raw +// through some proxies; accept both
    # alphabets, and if the base64 looks urlsafe, translate it
    cand = h
    if "-" in cand or "_" in cand:
        cand = cand.replace("-", "+").replace("_", "/")
    for dec in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            candidate = dec(cand + "=" * (-len(cand) % 4))
            json.loads(candidate)
            raw = candidate
            break
        except Exception:
            continue
    if not raw:
        raise ValueError("X-PAYMENT is not valid base64")
    return json.loads(raw)


_seen: set = set()
_seen_lock = threading.Lock()


def _nonce(payment_payload):
    auth = (payment_payload.get("payload") or {}).get("authorization") or {}
    # x402 v1 names this field `from`; some senders spell it `fromAddress`
    # mirroring EIP-681 — the replay guard must not be the reason a
    # legitimately-shaped payment 402s (found by the cache free-ride E2E)
    return (payment_payload.get("network"), auth.get("nonce"),
            auth.get("from") or auth.get("fromAddress"))


def _facilitator_call(endpoint, payment_payload, url, path):
    body = {
        "paymentPayload": payment_payload,
        "paymentRequirements": _requirement(url, path),
    }
    r = httpx.post(facilitator() + endpoint, json=body, timeout=15)
    return r.json()


def verify(payment_payload, path, url):
    """Return (ok, info). Checks replay, then asks the facilitator to verify."""
    n = _nonce(payment_payload)
    if not all(n):
        return False, "payment payload is missing network/nonce/from"
    with _seen_lock:
        if n in _seen:
            return False, "replayed payment"
    try:
        data = _facilitator_call("/verify", payment_payload, url, path)
    except Exception as e:
        return False, f"facilitator unreachable: {e}"
    # the reference facilitator answers {"isValid": bool, "invalidReason":
    # str|null, "payer": addr} — reading a "valid" key here silently
    # rejected EVERY payment, including valid ones, and our generic
    # "invalid payment" masked the real verdict for one whole evening
    if not data.get("isValid", data.get("valid", False)):
        return False, (data.get("invalidReason") or data.get("error")
                       or "invalid payment")
    with _seen_lock:
        _seen.add(n)
    return True, data


USAGE: dict = {"settled": 0, "failed": 0, "cache_hits": 0, "routes": {}}


def settle(payment_payload, path, url):
    """Settle after a successful response. Best-effort: a settle failure does
    not undo a served response, but it must be visible in X-PAYMENT-RESPONSE."""
    try:
        res = _facilitator_call("/settle", payment_payload, url, path)
    except Exception as e:
        USAGE["failed"] += 1
        return {"success": False, "error": f"settlement failed: {e}"}
    if res.get("success"):
        USAGE["settled"] += 1
        USAGE["routes"][path] = USAGE["routes"].get(path, 0) + 1
    else:
        USAGE["failed"] += 1
    return res


def pricing_info():
    if not pay_to():
        return None
    return {
        "mode": ("free routes: %d req/min/IP keyless; capped routes: free "
                 "under %d bytes then x402 per call; priced routes: x402 "
                 "from the first call (no free tier)"
                 % (30, CAP_BYTES)),
        "network": network(),
        "asset": asset(),
        "prices": PRICE_LABELS,
        "capped_routes": {p: "$0.0005 above %d bytes" % CAP_BYTES
                          for p in CAP_ROUTES},
    }
