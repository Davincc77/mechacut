"""MechaCut: deterministic data transforms. No key, no account, nothing stored.

Bundle core:
POST /api/v1/chart     records or CSV + column roles -> Vega-Lite spec and/or PNG
POST /api/v1/reshape   JSON + declarative mapping -> reshaped JSON (schema-gated)
POST /api/v1/validate  payload + JSON Schema -> valid or precise errors

Bundle 1 — data repair & cleaning (TOOLS-50 #1-10):
POST /api/v1/json/repair      broken JSON text -> parsed + repairs applied
POST /api/v1/json/diff        two JSON values -> sorted changes (JSON Pointer)
POST /api/v1/json/patch       document + RFC 6902 patch -> patched document
POST /api/v1/json/canonical   JSON -> canonical bytes (sorted keys) + sha256
POST /api/v1/csv/fix          dirty CSV -> clean CSV + notes
POST /api/v1/csv/types        CSV/records -> typed rows + column report
POST /api/v1/csv/join         two tables + key -> joined rows (left wins)
POST /api/v1/table/pivot      records -> pivot/unpivot with aggregation
POST /api/v1/list/dedupe      items + mode -> deduped, first-seen order
POST /api/v1/format/convert   json <-> yaml <-> toml <-> csv <-> env

Bundle 2 — code editing (TOOLS-50 #11-16):
POST /api/v1/text/patch       text + find/replace edits (uniqueness-checked)
POST /api/v1/text/diff        two texts -> unified diff + stats
POST /api/v1/text/apply-diff  text + unified diff -> patched text (strict)
POST /api/v1/path/normalize   lexical path normalization (never touches disk)
POST /api/v1/glob/match       deterministic glob over a list of paths
POST /api/v1/env/interpolate  $VAR / ${VAR:-default} expansion

Bundle 3 — dates & scheduling (TOOLS-50 #17-23):
POST /api/v1/date/parse       human/ISO/RFC2822/epoch -> canonical fields
POST /api/v1/date/tz          convert instants across IANA zones (DST-correct)
POST /api/v1/date/calc        add | business_days | diff | boundary | age
POST /api/v1/cron/next        next N fire times (wall clock, Vixie OR rule)
POST /api/v1/cron/humanize    cron -> plain reading + field sets
POST /api/v1/ics/generate     events -> deterministic VCALENDAR (CRLF, folded)
POST /api/v1/ics/parse        VCALENDAR -> normalized events
POST /api/v1/date/recurrence  RRULE -> dated occurrences, traps declared  (free)
POST /api/v1/units/shoe_size  shoe sizes -> exact mm, published steps,    (free)
                              drift declared, never one confident number
POST /api/v1/net/sri          local octets -> integrity attr + style audit (free)
POST /api/v1/date/tz_ambiguity  wall clock + zone -> single | fold | gap,  (free)
                                every UTC instant named, PEP 495 stated out
POST /api/v1/money/flight_comp  flight date keys the EC261/UK261 table —     (free)
                                old text vs 2026/2202, bands + MAY-reductions
POST /api/v1/date/week          ISO week <-> date, W53 by theorem, the       (free)
                                %Y-W%V trap shown on the requested date
POST /api/v1/money/baggage      flight date keys LAW vs carrier gauge;       (free)
                                40x30x15 underseat free from 2027-10-23
POST /api/v1/csv/excel_damage   what Excel DESTROYS on double-click,         (free)
                                per column, published vectors, import said
POST /api/v1/money/crossover    two-component tariffs: EXACT crossover,      (free)
                                named day convention, domination says never
POST /api/v1/csv/excel_display  stored value + numFmt code -> what the       (free)
                                human SEES (the $1,000-vs-1000000 split)

Bundle 4.1 — numbers & money (TOOLS-50 #24-26):
POST /api/v1/num/format       value + closed locale/currency tables -> text
POST /api/v1/num/parse        human number -> canonical decimal (+currency,%)
POST /api/v1/num/round        exact Decimal rounding (banker's, sig digits)

Bundle 4.2 — units & money (TOOLS-50 #27-29):
POST /api/v1/units/convert    closed families, exact rational factors
POST /api/v1/money/prorate    amount x covered/cycle days, rounded last (paid)
POST /api/v1/money/split      to-the-cent split, closed remainder rule

Bundle 4.3 — spell-out (TOOLS-50 #30):
POST /api/v1/number/spell     amount -> words (fr/en/pt, closed grammar)

Bundle 5.1 — hashes, encodings & identity (TOOLS-50 #31-36, all free):
POST /api/v1/hash/digest      md5/sha1/sha256/sha512/blake2b, strict input
POST /api/v1/enc/base64       base64/base64url/hex, garbage refused
POST /api/v1/jwt/decode       claims exposed, never silently "verified"
POST /api/v1/id/uuid          v5 | v4_seeded | v7 (explicit instant only)
POST /api/v1/id/slug          transliterated, collapsed, bounded
POST /api/v1/fingerprint      canonical JSON/CSV hash = your cache key

Bundle 6.1 — validators (TOOLS-50 #37-41):
POST /api/v1/validate/iban    closed 61-country table + mod-97   ($0.0005)
POST /api/v1/validate/phone   -> E.164 via closed dial-code table (free)
POST /api/v1/validate/email   structure + normalized form  (free, no DNS)
POST /api/v1/validate/url     components + canonical (IDN, ports)  (free)
POST /api/v1/color/check      hex/rgb/hsl + WCAG contrast against  (free)

Bundle 7.1 — context & text (TOOLS-50 #43-47, all free):
POST /api/v1/text/count       chars/words/sentences/paragraphs/lines/bytes
POST /api/v1/sort/natural     file2 before file10, + exact permutation
POST /api/v1/text/case        snake/kebab/camel/pascal/title/... 
POST /api/v1/text/truncate    to N units at a real boundary
POST /api/v1/regex/test       test/findall/groups/replace, sandboxed
POST /api/v1/text/chunk       token-exact RAG chunking            ($0.001)
POST /api/v1/md/render        closed-subset markdown -> HTML  (free < 32 KB)
POST /api/v1/html/text        HTML -> canonical text, links optional ($0.001)

Bundle 8 — palette (TOOLS-50 #50):
POST /api/v1/color/palette    closed-scheme palettes + ramps         (free)
POST /api/v1/check/constraints text + closed constraints -> verdicts  (free)
POST /api/v1/check/refs       cited refs vs provided sources         (free)
POST /api/v1/extract/facts    every fact in text, none lost      (cap 32 KB)
POST /api/v1/text/select      top-k chunks by closed query rules     (free)
POST /api/v1/logic/rules      facts + closed rule grammar -> trace   (free)
POST /api/v1/sort/multi       multi-key stable sort, explicit ties   (free)
POST /api/v1/json/query       $-path queries incl. [*] wildcards     (free)
Bundle 16 — volume (TOOLS-50 #52, #46, #47):
POST /api/v1/batch            same tool over N payloads, one call (cap 32 KB)
POST /api/v1/recipe/invoice   line items -> full invoice, exact + words (free)
POST /api/v1/recipe/schedule  cron + count -> events + ICS in one call   (free)
POST /api/v1/fiche/shop-reste|partage-reste|soldes2  the 'of the REST' chains, slots in, trace out (free)
POST /api/v1/recipe/facts     free text -> fact inventory canonical + total (free)
POST /api/v1/intent/card      plain words -> tool + form to fill, or the question to ask (free)
POST /api/v1/formula            published formula + your numbers, exact (free)
GET  /api/v1/formula            the closed catalog of 12, with sources (free)
POST /api/v1/intent/reflect     your reading, mirrored back before you trust it (free)
POST /api/v1/intent/check     filled card -> ok or exactly what the human must add (free)
POST /api/v1/check/agreement  N payloads -> same deal? divergences by pointer (free)
POST /api/v1/check/redlines   text vs forbidden words/regex/PII shapes/budget -> first violation (free)
POST /api/v1/hash/hmac          sign/verify payload with shared key — RFC 4231 vectors (free)
POST /api/v1/id/ulid            deterministic ULID make/parse/sort (seed -> same id) (free)
POST /api/v1/pkg/name           npm/PyPI/Docker name grammar verdict + normalize (free)
POST /api/v1/json/map           12 closed ops element-wise over an array (free)
POST /api/v1/num/fx             amount x YOUR rate -> exact ISO minor units, half_even (free)
POST /api/v1/semver/sort        precedence order, not alphabetical (free)
POST /api/v1/text/sanitize      cross-OS filename verdict + why (free)
Bundle 17 — daily micro-organs (TOOLS-50 #53, #39, #26, #27):
POST /api/v1/text/decode      mojibake -> utf-8, only provable fixes (free)
POST /api/v1/num/human        duration/bytes/roman/ordinal like a human (free)
POST /api/v1/text/escape      one value, dialects html/sql/shell/csv/json/url (free)
POST /api/v1/text/normalize   NFC/NFKC, accents, fullwidth, whitespace    (free)
Bundle 18 — EVM primitives (TOOLS-50 #57, core #54/#56):
POST /api/v1/eth/address      EIP-55 validity + allowlist membership   (free)
POST /api/v1/eth/selector     canonical signature -> 4-byte selector   (free)
POST /api/v1/eth/units        wei/gwei/ether exact ladder              (free)
POST /api/v1/eth/abi-encode   types+values -> calldata            (cap 32 KB)
POST /api/v1/eth/abi-decode   calldata -> readable args           (cap 32 KB)
POST /api/v1/eth/eip712       typed data -> 0x1901 digest             (free)
POST /api/v1/eth/receipt      logs + expected effects -> match        (free)

Surfaces:
GET  /openapi.json     OpenAPI 3.1
POST /mcp              stateless MCP JSON-RPC (one tool per transform)
GET  /SKILL.md         agent skill
GET  /agent/manifest   one line per tool, closed vocabulary (~500 tokens)
GET  /tools/{name}.json  single tool schema, on demand
GET  /SKILL-{pack}.md  per-bundle skill packs
GET  /route?q=...      task router, closed vocabulary, same words = answer
POST /api/v1/recipe/<name>  named pipelines (GET /api/v1/recipes)
POST /api/v1/pipeline       any 1..8 tool steps in one call, $from refs
GET  /misses.json      anonymized rolling rejection ledger (60 min)
GET  /integrity.json   public golden-pin replay checklist (self-audit)
GET  /usage.json        ephemeral settlement counters (paid mirror of misses)
GET  /agent/listing.txt  marketplace listing generated from live config

Hardening (scanner probes): /docs and /redoc disabled; unmatched paths return
a neutral JSON 404 (/.env, /.git/... get exactly the same answer as any
unknown path — no reflection, no stack, nothing to fingerprint); request
bodies are capped at 5 MB with 413 before any payment or route work; every
response carries nosniff/DENY/no-referrer and JSON surfaces are no-store.

Same request, same bytes: 200 responses carry a sha256. The only state the
process keeps is the rate-limit window (IPs, one minute, in memory), the
miss ledger (60 min, no payloads) and the payment-nonce replay set.
"""

import base64
import difflib
import hashlib
from types import SimpleNamespace
import json
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

import chart
import check
import checkers
import eth as eth_mod
import ethabi
import extract
import intake
import geo
import leakkit
import chainkit
import ficheskit
import annuaire
import routeur
import taxid
import addrkit
import timekit
import webkit
import qrkit
import holidays
import icskit
import amortize
import pdftext
import rates
import pngkit
import certkit
import xmlkit
import urlkit
import reldate
import moneykit
import formatkit
import discountkit
import calckit
import scalekit
import digitkit
import formulakit
import reflectkit
import recurrkit
import sqlkit
import shoeskit
import srikit
import tzambkit
import compkit
import weekkit
import bagkit
import damagekit
import crosskit
import displaykit
import auditor
import sayings
import verdict
import redlines
import cache
import micro
import rules as rules_mod
import htmltext
import context
import mdrender
import dates
import identity
import edits
import money
import numfmt
import payments
import repair
import reshape as reshape_mod
import routing
import spell
import tables
import units

# Human landing pages (browsers get HTML per language; agents keep the JSON
# card). Catalogs live in locales/, EN is the source of truth and parity is
# enforced by tests/test_i18n.py. Languages ship only when a trusted
# reviewer owns them — zh-Hans is pending such a review and stays out.
_LOCALES_DIR = Path(__file__).resolve().parent / "locales"
_LANDING_TEMPLATE = Path(__file__).resolve().parent / "static" / "landing.html"
_LANG_CODES = ("en", "fr", "pt")


def _load_landing() -> Dict[str, str]:
    if not _LANDING_TEMPLATE.exists() or not _LOCALES_DIR.exists():
        return {}
    tpl = _LANDING_TEMPLATE.read_text(encoding="utf-8")
    out = {}
    for code in _LANG_CODES:
        cat = json.loads((_LOCALES_DIR / f"{code}.json").read_text(encoding="utf-8"))
        html = tpl.replace("{{LANG}}", code)
        cur = {f"cur.{c}": " cur" if c == code else "" for c in _LANG_CODES}
        cat = {**cat, **cur}
        for key, val in cat.items():
            html = html.replace("{{" + key + "}}", val)
        out[code] = html
    return out


LANDING = _load_landing()


def _pick_lang(request: Request) -> str:
    q = request.query_params.get("lang")
    if q and q.lower() in _LANG_CODES:
        return q.lower()
    accept = request.headers.get("accept-language", "")
    for part in accept.split(","):
        tag = part.split(";")[0].strip().lower().split("-")[0]
        if tag in _LANG_CODES:
            return tag
    return "en"

RATE_LIMIT = 30  # requests per minute per IP
MAX_BODY_BYTES = 5 * 1024 * 1024  # request bodies above this are refused (413)
HITS: Dict[str, deque] = {}

# --- public misses ledger (anonymized, in-memory, nothing persisted) ---
# Every 400 and 402 on the transform routes is recorded as (ts, path, kind)
# only — never the payload, never the IP. 402s are labelled
# "payment_required" (an unpaid attempt); 400s keep their error kind. The
# window is rolling and the store is a bounded deque, so "nothing stored"
# stays true: the ledger dies with the process and with the hour.
_MISS_WINDOW = 60 * 60
_MISS_MAX = 5000
_misses: "deque[tuple[int, str, str]]" = deque()
_misses_lock = threading.Lock()


def _prune_misses(now: int) -> None:
    while _misses and now - _misses[0][0] > _MISS_WINDOW:
        _misses.popleft()


def record_miss(path: str, kind: str) -> None:
    now = int(time.time())
    with _misses_lock:
        _prune_misses(now)
        _misses.append((now, path, kind[:64]))
        while len(_misses) > _MISS_MAX:
            _misses.popleft()

app = FastAPI(
    title="MechaCut",
    version="0.84.0",
    # Agent-first surface: the docs endpoints are fingerprintable extra doors
    # and the contract is already public at /openapi.json.
    docs_url=None,
    redoc_url=None,
    description=(
        "Deterministic data transforms: charts, schema-gated reshaping, "
        "validation, the data-repair bundle (JSON repair/diff/patch/"
        "canonical, CSV fix/types/join, pivot, dedupe, format conversion) "
        "and the code-editing bundle (text patch/diff/apply-diff, path "
        "normalize, glob match, env interpolation), and the dates bundle "
        "(parse, timezones, calendar math, cron, ICS), and deterministic "
        "numbers (format, parse, round), units and money (convert, "
        "prorate, split), amounts in words (FR/EN/PT), and identity tools "
        "(hash, enc, jwt, uuid, slug, fingerprint), and the validators "
        "(iban, phone, email, url) with color/contrast, and text tools "
        "(count, natural sort, case, truncate, regex, chunk, markdown, "
        "html->text), palettes, and agent-navigation surfaces: manifest, single schemas, skill packs, a closed-vocabulary task router, named recipes and one-call pipelines. "
        "No API key, no account, nothing stored. Same request, same bytes: "
        "responses carry a sha256."
    ),
)


def canon(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bad_request(errors, kind="invalid_input", extra=None):
    body: Dict[str, Any] = {"error": kind, "errors": errors}
    if extra:
        body.update(extra)
    return JSONResponse(status_code=400, content=body)


def _pyd_errors(e):
    raw = e.errors() if hasattr(e, "errors") else None
    if raw:
        return [{"field": ".".join(str(p) for p in x["loc"]),
                 "message": x["msg"]} for x in raw]
    return [{"message": str(e)}]


@app.exception_handler(RequestValidationError)
async def _validation_handler(request: Request, exc: RequestValidationError):
    return bad_request(_pyd_errors(exc))


@app.exception_handler(StarletteHTTPException)
async def _http_handler(request: Request, exc: StarletteHTTPException):
    """Neutral JSON for unmatched paths and wrong methods: scanners probing
    /.env, /.git/config, /wp-admin... learn nothing beyond 'not found'."""
    kind = {404: "not_found", 405: "method_not_allowed"}.get(
        exc.status_code, "http_error")
    return JSONResponse(status_code=exc.status_code,
                        content={"error": kind})


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    ip = request.client.host if request.client else "local"
    now = time.time()
    path = request.url.path
    cl = request.headers.get("content-length", "")
    size = int(cl) if cl.isdigit() else None

    # --- determinism cache (bundle 25): 'same inputs -> same bytes' is a
    # licence to serve the bytes again, free. Lives HERE on purpose, inside
    # the middleware chain: a HIT response travels back out through
    # misses_ledger and hardening, so security headers still wrap it.
    caching = request.method == "POST" and path.startswith("/api/v1/")
    key = None
    if caching:
        body = await request.body()      # scope-cached; routes re-read fine
        if 0 < len(body) <= 5_000_000:
            key = cache.key_of(app.version, path, body)

    # Priced routes: x402 per call, required from the first request when
    # payments are configured. Capped routes: free under CAP_BYTES, x402
    # above. 400s stay free; settlement runs only after a successful (<400)
    # response. Paid calls skip the rate limiter. AND: an already-computed
    # paid answer is served from cache BEFORE the paywall — we do not
    # charge to re-emit bytes we already paid the CPU for.
    if request.method == "POST" and payments.enabled(path, size):
        # the free ride is for callers who do NOT claim to pay. If an
        # X-PAYMENT header is present, the payment gets the verification
        # it deserves — replay protection stays absolute even for cached
        # answers (a reused voucher must 402, never silently 200).
        if key and "x-payment" not in request.headers:
            hit = cache.get(key)
            if hit:
                payments.USAGE["cache_hits"] += 1
                status, stored = hit
                return Response(content=stored, status_code=status,
                                media_type="application/json",
                                headers={"X-Cache": "HIT"})
        url = str(request.url)
        header = request.headers.get("x-payment")
        if not header:
            return payments.payment_required(url, path)
        try:
            payload = payments.decode_payment(header)
        except Exception:
            return payments.payment_required(
                url, path,
                "X-PAYMENT is not a base64-encoded x402 v1 payment "
                "payload — header was present but unreadable")
        ok, info = payments.verify(payload, path, url)
        if not ok:
            return payments.payment_required(
                url, path, "payment refused by verification: %s" % info)
        response = await call_next(request)
        if response.status_code < 400:
            settlement = payments.settle(payload, path, url)
            response.headers["X-PAYMENT-RESPONSE"] = json.dumps(settlement)
            if key:
                data = b"".join([c async for c in response.body_iterator])
                cache.put(key, response.status_code, data)
                response = Response(content=data,
                                    status_code=response.status_code,
                                    headers=dict(response.headers),
                                    media_type=response.media_type)
                response.headers["X-Cache"] = "MISS"
        return response

    # Everything else keeps the keyless rate limit (429) — a cached free
    # call still counts against it: the free ride never defeats the gate.
    q = HITS.setdefault(ip, deque())
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limited",
                     "message": f"{RATE_LIMIT} requests per minute per IP"},
        )
    q.append(now)
    if key:
        hit = cache.get(key)
        if hit:
            status, stored = hit
            return Response(content=stored, status_code=status,
                            media_type="application/json",
                            headers={"X-Cache": "HIT"})
        response = await call_next(request)
        if response.status_code == 200:
            data = b"".join([c async for c in response.body_iterator])
            cache.put(key, 200, data)
            response = Response(content=data, status_code=200,
                                headers=dict(response.headers),
                                media_type=response.media_type)
            response.headers["X-Cache"] = "MISS"
        return response
    return await call_next(request)


@app.middleware("http")
async def misses_ledger(request: Request, call_next):
    response = await call_next(request)
    if response.status_code in (400, 402) and request.url.path.startswith("/api/v1/"):
        kind = "payment_required" if response.status_code == 402 else "unknown"
        if response.status_code == 400:
            try:
                body = json.loads(response.body)
                kind = str(body.get("error", "unknown"))
            except Exception:
                pass
        record_miss(request.url.path, kind)
    return response


@app.middleware("http")
async def hardening(request: Request, call_next):
    """Outermost: oversized bodies never reach payment or route code, and
    every response carries conservative security headers."""
    if request.method in ("POST", "PUT", "PATCH"):
        cl = request.headers.get("content-length", "")
        if cl.isdigit() and int(cl) > MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"error": "payload_too_large",
                         "message": f"request body over {MAX_BODY_BYTES} bytes"},
            )
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    path = request.url.path
    if path == "/" or path.startswith("/api/") or path in ("/misses.json", "/mcp"):
        response.headers["Cache-Control"] = "no-store"
    return response


# ---------------------------------------------------------------- charts

class ChartRequest(BaseModel):
    x: str
    kind: str = "bar"
    y: Optional[str] = None
    series: Optional[str] = None
    title: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    csv: Optional[str] = None
    width: int = 640
    height: int = 400
    format: Literal["both", "spec", "png"] = "both"


def run_chart(args: dict):
    """Shared by HTTP and MCP. Returns (body, None) or (None, 400 response)."""
    try:
        req = ChartRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    errors = []
    if req.kind not in chart.KINDS:
        errors.append({"field": "kind",
                       "message": f"unknown kind, expected one of {sorted(chart.KINDS)}"})
    if req.kind != "histogram" and not req.y:
        errors.append({"field": "y", "message": "required unless kind is histogram"})
    if req.data is None and not req.csv:
        errors.append({"field": "data", "message": "send data (records) or csv"})
    if errors:
        return None, bad_request(errors)
    try:
        rows = chart.parse_records(req.data, req.csv)
        vega, png = chart.build(req.kind, rows, req.x, req.y,
                               series=req.series, title=req.title,
                               width=req.width, height=req.height)
    except chart.ChartError as e:
        return None, bad_request([{"message": str(e)}])
    out: Dict[str, Any] = {"sha256": canon(vega)}
    if req.format != "png":
        out["vega"] = vega
    if req.format != "spec":
        out["sha256_png"] = hashlib.sha256(png).hexdigest()
        out["png_base64"] = base64.b64encode(png).decode("ascii")
        out["png_bytes"] = len(png)
    return out, None


@app.post("/api/v1/chart")
def api_chart(req: ChartRequest):
    body, err = run_chart(req.model_dump())
    return err if err else body


# ---------------------------------------------------------------- reshape

class ReshapeRequest(BaseModel):
    input: Any
    mapping: Dict[str, Any]
    outputSchema: Optional[Dict[str, Any]] = None


def run_reshape(args: dict):
    try:
        req = ReshapeRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    out, errors, defaults = reshape_mod.reshape(req.input, req.mapping)
    if errors:
        return None, bad_request(errors)
    if req.outputSchema:
        schema_errors = validate_payload(out, req.outputSchema)
        if schema_errors:
            return None, bad_request(schema_errors, "schema_violation",
                                     {"output": out})
    return {"output": out, "sha256": canon(out), "defaults_used": defaults}, None


@app.post("/api/v1/reshape")
def api_reshape(req: ReshapeRequest):
    body, err = run_reshape(req.model_dump())
    return err if err else body


# ---------------------------------------------------------------- validate

class ValidateRequest(BaseModel):
    model_config = {"populate_by_name": True}
    payload: Any
    json_schema: Dict[str, Any] = Field(alias="schema")


def validate_payload(payload, schema):
    try:
        validator = Draft202012Validator(schema)
    except Exception as e:
        return [{"field": "$schema", "message": f"invalid schema: {e}"}]
    errors = []
    for e in validator.iter_errors(payload):
        errors.append({
            "field": "/" + "/".join(str(p) for p in e.absolute_path),
            "message": e.message,
        })
    return errors


def run_validate(args: dict):
    try:
        req = ValidateRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    errors = validate_payload(req.payload, req.json_schema)
    if errors:
        return None, bad_request(errors, "schema_violation", {"valid": False})
    return {"valid": True}, None


@app.post("/api/v1/validate")
def api_validate(req: ValidateRequest):
    body, err = run_validate(req.model_dump())
    return err if err else body


# ------------------------------------------------- bundle 1: data repair

class JsonRepairRequest(BaseModel):
    text: str


def run_json_repair(args: dict):
    try:
        req = JsonRepairRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        value, repairs = repair.json_repair(req.text)
    except repair.RepairError as e:
        return None, bad_request(
            [{"field": "text", "message": str(e),
              "expected": "JSON-like text (markdown fences, BOM, smart or "
                          "single quotes, comments, bare keys, trailing "
                          "commas, Python literals, JSONL)"}],
            "unrepairable")
    return {"output": value, "repairs": repairs, "sha256": canon(value)}, None


@app.post("/api/v1/json/repair")
def api_json_repair(req: JsonRepairRequest):
    body, err = run_json_repair(req.model_dump())
    return err if err else body


class JsonDiffRequest(BaseModel):
    a: Any
    b: Any


def run_json_diff(args: dict):
    try:
        req = JsonDiffRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    changes = repair.json_diff(req.a, req.b)
    return {"changes": changes, "count": len(changes),
            "identical": not changes, "sha256": canon(changes)}, None


@app.post("/api/v1/json/diff")
def api_json_diff(req: JsonDiffRequest):
    body, err = run_json_diff(req.model_dump())
    return err if err else body


class JsonPatchRequest(BaseModel):
    document: Any
    patch: List[Dict[str, Any]]


def run_json_patch(args: dict):
    try:
        req = JsonPatchRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = repair.json_patch(req.document, req.patch)
    except repair.PatchError as e:
        return None, bad_request(
            [{"field": f"patch[{e.index}]", "message": e.message,
              "expected": "RFC 6902 operation with op in "
                          "add|remove|replace|move|copy|test"}],
            "patch_failed")
    return {"output": out, "operations_applied": len(req.patch),
            "sha256": canon(out)}, None


@app.post("/api/v1/json/patch")
def api_json_patch(req: JsonPatchRequest):
    body, err = run_json_patch(req.model_dump())
    return err if err else body


class CanonicalRequest(BaseModel):
    input: Any
    style: Literal["minified", "pretty"] = "minified"


def run_json_canonical(args: dict):
    try:
        req = CanonicalRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    text = repair.json_canonical(req.input, req.style)
    return {"text": text, "bytes": len(text.encode("utf-8")),
            "sha256": _sha_text(text)}, None


@app.post("/api/v1/json/canonical")
def api_json_canonical(req: CanonicalRequest):
    body, err = run_json_canonical(req.model_dump())
    return err if err else body


class DedupeRequest(BaseModel):
    items: List[Any]
    mode: Literal["exact", "text", "url", "email"] = "text"


def run_list_dedupe(args: dict):
    try:
        req = DedupeRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out, removed = repair.list_dedupe(req.items, req.mode)
    except repair.RepairError as e:
        return None, bad_request([{"field": "items", "message": str(e)}])
    return {"output": out, "removed": removed, "sha256": canon(out)}, None


@app.post("/api/v1/list/dedupe")
def api_list_dedupe(req: DedupeRequest):
    body, err = run_list_dedupe(req.model_dump())
    return err if err else body


class CsvFixRequest(BaseModel):
    csv: str
    preserve_delimiter: bool = False


def run_csv_fix(args: dict):
    try:
        req = CsvFixRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        text, notes = tables.csv_fix(req.csv, req.preserve_delimiter)
    except tables.TransformError as e:
        return None, bad_request([{"field": "csv", "message": str(e),
                                   "expected": "CSV text with a header row"}])
    return {"output": text, "notes": notes, "sha256": _sha_text(text)}, None


@app.post("/api/v1/csv/fix")
def api_csv_fix(req: CsvFixRequest):
    body, err = run_csv_fix(req.model_dump())
    return err if err else body


class CsvTypesRequest(BaseModel):
    csv: Optional[str] = None
    rows: Optional[List[Dict[str, Any]]] = None


def run_csv_types(args: dict):
    try:
        req = CsvTypesRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    if req.csv is None and req.rows is None:
        return None, bad_request(
            [{"field": "csv", "message": "send csv (text) or rows (records)"}])
    try:
        records = chart.parse_records(data=req.rows, csv_text=req.csv)
        out, columns = tables.csv_types(records)
    except (chart.ChartError, tables.TransformError) as e:
        return None, bad_request([{"field": "input", "message": str(e)}])
    return {"output": out, "columns": columns, "sha256": canon(out)}, None


@app.post("/api/v1/csv/types")
def api_csv_types(req: CsvTypesRequest):
    body, err = run_csv_types(req.model_dump())
    return err if err else body


class JoinRequest(BaseModel):
    left: Optional[List[Dict[str, Any]]] = None
    left_csv: Optional[str] = None
    right: Optional[List[Dict[str, Any]]] = None
    right_csv: Optional[str] = None
    on: Any
    how: Literal["inner", "left", "right", "outer"] = "inner"


def run_csv_join(args: dict):
    try:
        req = JoinRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        lrows = chart.parse_records(data=req.left, csv_text=req.left_csv)
        rrows = chart.parse_records(data=req.right, csv_text=req.right_csv)
        out, counts = tables.csv_join(lrows, rrows, req.on, req.how)
    except (chart.ChartError, tables.TransformError) as e:
        return None, bad_request([{"field": "on", "message": str(e),
                                   "expected": "\"col\" | [\"lcol\", \"rcol\"] "
                                               "| {\"left\": .., \"right\": ..}"}])
    return {"output": out, "counts": counts, "sha256": canon(out)}, None


@app.post("/api/v1/csv/join")
def api_csv_join(req: JoinRequest):
    body, err = run_csv_join(req.model_dump())
    return err if err else body


class PivotRequest(BaseModel):
    data: Optional[List[Dict[str, Any]]] = None
    csv: Optional[str] = None
    mode: Literal["pivot", "unpivot"] = "pivot"
    index: Optional[Any] = None
    columns: Optional[str] = None
    values: Optional[str] = None
    agg: Literal["sum", "count", "mean", "min", "max", "first"] = "sum"
    keep: Optional[List[str]] = None
    vars: Optional[List[str]] = None
    var_name: str = "variable"
    value_name: str = "value"


def run_table_pivot(args: dict):
    try:
        req = PivotRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    errors = []
    if req.mode == "pivot":
        if not req.index:
            errors.append({"field": "index", "message": "required for pivot"})
        if not req.columns:
            errors.append({"field": "columns", "message": "required for pivot"})
        if not req.values:
            errors.append({"field": "values", "message": "required for pivot"})
    if errors:
        return None, bad_request(errors)
    try:
        rows = chart.parse_records(data=req.data, csv_text=req.csv)
        if req.mode == "pivot":
            out = tables.table_pivot(rows, req.index, req.columns,
                                     req.values, req.agg)
        else:
            out = tables.table_unpivot(rows, req.keep, req.vars,
                                       req.var_name, req.value_name)
    except (chart.ChartError, tables.TransformError) as e:
        return None, bad_request([{"field": "data", "message": str(e)}])
    return {"output": out, "sha256": canon(out)}, None


@app.post("/api/v1/table/pivot")
def api_table_pivot(req: PivotRequest):
    body, err = run_table_pivot(req.model_dump())
    return err if err else body


class ConvertRequest(BaseModel):
    model_config = {"populate_by_name": True}
    input: Any
    source: Literal["json", "yaml", "toml", "csv", "env"] = Field(alias="from")
    target: Literal["json", "yaml", "toml", "csv", "env"] = Field(alias="to")


def run_format_convert(args: dict):
    try:
        req = ConvertRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    src = req.input if isinstance(req.input, str) else \
        json.dumps(req.input, ensure_ascii=False)
    try:
        text = tables.format_convert(src, req.source, req.target)
    except tables.TransformError as e:
        return None, bad_request(
            [{"field": "input", "message": str(e),
              "expected": "text in one of json|yaml|toml|csv|env"}],
            "convert_failed")
    return {"output": text, "sha256": _sha_text(text)}, None


@app.post("/api/v1/format/convert")
def api_format_convert(req: ConvertRequest):
    body, err = run_format_convert(
        {"input": req.input, "source": req.source, "target": req.target})
    return err if err else body


# ------------------------------------------------------- bundle 2: edits

class TextPatchRequest(BaseModel):
    text: str
    edits: List[Dict[str, Any]]


def run_text_patch(args: dict):
    try:
        req = TextPatchRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out, applied = edits.text_patch(req.text, req.edits)
    except edits.EditError as e:
        return None, bad_request(
            [{"field": "edits", "message": str(e),
              "expected": "[{find, replace, occurrences: \"one\"|\"all\"|N}]"}],
            "edit_failed")
    return {"output": out, "edits_applied": applied,
            "changed": out != req.text, "sha256": _sha_text(out)}, None


@app.post("/api/v1/text/patch")
def api_text_patch(req: TextPatchRequest):
    body, err = run_text_patch(req.model_dump())
    return err if err else body


class TextDiffRequest(BaseModel):
    a: str
    b: str
    context: int = Field(default=3, ge=0, le=20)


def run_text_diff(args: dict):
    try:
        req = TextDiffRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    diff, lines = edits.text_diff(req.a, req.b, req.context)
    hunks, added, removed = edits.diff_stats(lines)
    return {"diff": diff, "hunks": hunks, "added": added, "removed": removed,
            "identical": not lines, "sha256": _sha_text(diff)}, None


@app.post("/api/v1/text/diff")
def api_text_diff(req: TextDiffRequest):
    body, err = run_text_diff(req.model_dump())
    return err if err else body


class ApplyDiffRequest(BaseModel):
    text: str
    diff: str


def run_text_apply_diff(args: dict):
    try:
        req = ApplyDiffRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out, hunks, added, removed = edits.text_apply_diff(req.text, req.diff)
    except edits.EditError as e:
        return None, bad_request(
            [{"field": "diff", "message": str(e),
              "expected": "unified diff (@@ hunks, strict context match)"}],
            "apply_failed")
    return {"output": out, "hunks_applied": hunks, "added": added,
            "removed": removed, "sha256": _sha_text(out)}, None


@app.post("/api/v1/text/apply-diff")
def api_text_apply_diff(req: ApplyDiffRequest):
    body, err = run_text_apply_diff(req.model_dump())
    return err if err else body


class PathNormalizeRequest(BaseModel):
    path: str
    os: Literal["auto", "posix", "windows"] = "auto"
    case: Literal["keep", "lower"] = "keep"


def run_path_normalize(args: dict):
    try:
        req = PathNormalizeRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = dict(edits.path_normalize(req.path, req.os, req.case))
    except edits.EditError as e:
        return None, bad_request([{"field": "path", "message": str(e)}])
    out["sha256"] = _sha_text(out["path"])
    return out, None


@app.post("/api/v1/path/normalize")
def api_path_normalize(req: PathNormalizeRequest):
    body, err = run_path_normalize(req.model_dump())
    return err if err else body


class GlobMatchRequest(BaseModel):
    pattern: str
    paths: List[str]


def run_glob_match(args: dict):
    try:
        req = GlobMatchRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        matched = edits.glob_match(req.pattern, req.paths)
    except edits.EditError as e:
        return None, bad_request([{"field": "pattern", "message": str(e)}])
    body = {"matched": matched, "count": len(matched)}
    body["sha256"] = canon(body)
    return body, None


@app.post("/api/v1/glob/match")
def api_glob_match(req: GlobMatchRequest):
    body, err = run_glob_match(req.model_dump())
    return err if err else body


class EnvInterpolateRequest(BaseModel):
    template: str
    vars: Dict[str, Any]
    strict: bool = True


def run_env_interpolate(args: dict):
    try:
        req = EnvInterpolateRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out, n, missing = edits.env_interpolate(req.template, req.vars,
                                                req.strict)
    except edits.EditError as e:
        return None, bad_request(
            [{"field": "template", "message": str(e),
              "expected": "template with $VAR, ${VAR} or ${VAR:-default}"}])
    return {"output": out, "substituted": n, "missing": missing,
            "sha256": _sha_text(out)}, None


@app.post("/api/v1/env/interpolate")
def api_env_interpolate(req: EnvInterpolateRequest):
    body, err = run_env_interpolate(req.model_dump())
    return err if err else body


# ------------------------------------------------------- bundle 3: dates

class DateParseRequest(BaseModel):
    text: str
    prefer: Literal["dmy", "mdy"] = "dmy"
    tz: Optional[str] = None


def run_date_parse(args: dict):
    try:
        req = DateParseRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = dates.parse_date(req.text, req.prefer, req.tz)
    except dates.DateError as e:
        return None, bad_request(
            [{"field": "text", "message": str(e),
              "expected": "ISO 8601, RFC 2822, epoch seconds, d/m/y or "
                          "month-name date (order via prefer, never guessed)"}],
            "unparsable_date")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/date/parse")
def api_date_parse(req: DateParseRequest):
    body, err = run_date_parse(req.model_dump())
    return err if err else body


class DateTzRequest(BaseModel):
    datetime: str
    source: str = "UTC"
    targets: List[str] = ["UTC"]
    at: Optional[str] = None


def run_date_tz(args: dict):
    try:
        req = DateTzRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = dates.tz_convert(req.datetime, req.source, req.targets, req.at)
    except dates.DateError as e:
        return None, bad_request(
            [{"field": "targets", "message": str(e),
              "expected": "IANA zone names (Europe/Paris, America/New_York, "
                          "UTC...)"}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/date/tz")
def api_date_tz(req: DateTzRequest):
    body, err = run_date_tz(req.model_dump())
    return err if err else body


class DateCalcRequest(BaseModel):
    base: str
    op: Literal["add", "business_days", "diff", "boundary", "age"]
    params: Dict[str, Any] = Field(default_factory=dict)
    tz: Optional[str] = None


def run_date_calc(args: dict):
    try:
        req = DateCalcRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = dates.date_calc(req.base, req.op, req.params, req.tz)
    except dates.DateError as e:
        return None, bad_request(
            [{"field": "params", "message": str(e),
              "expected": "op=add {duration} | business_days {n, holidays?, "
                          "weekend?} | diff {until, unit} | boundary {unit, "
                          "edge} | age {on?}"}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/date/calc")
def api_date_calc(req: DateCalcRequest):
    body, err = run_date_calc(req.model_dump())
    return err if err else body


class CronNextRequest(BaseModel):
    expression: str
    count: int = Field(default=1, ge=1, le=1000)
    after: Optional[str] = None
    tz: str = "UTC"


def run_cron_next(args: dict):
    try:
        req = CronNextRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = dates.cron_next(req.expression, req.count, req.after, req.tz)
    except dates.DateError as e:
        return None, bad_request(
            [{"field": "expression", "message": str(e),
              "expected": "5-field cron or @macro (@daily, @weekly...)"}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/cron/next")
def api_cron_next(req: CronNextRequest):
    body, err = run_cron_next(req.model_dump())
    return err if err else body


class CronHumanizeRequest(BaseModel):
    expression: str


def run_cron_humanize(args: dict):
    try:
        req = CronHumanizeRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = dates.cron_humanize(req.expression)
    except dates.DateError as e:
        return None, bad_request(
            [{"field": "expression", "message": str(e),
              "expected": "5-field cron or @macro"}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/cron/humanize")
def api_cron_humanize(req: CronHumanizeRequest):
    body, err = run_cron_humanize(req.model_dump())
    return err if err else body


class IcsGenerateRequest(BaseModel):
    events: List[Dict[str, Any]]
    prodid: str = "-//mechacut.studio//ICS//EN"
    calname: str = "mechacut"


def run_ics_generate(args: dict):
    try:
        req = IcsGenerateRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        text = dates.ics_generate(req.events, req.prodid, req.calname)
    except dates.DateError as e:
        return None, bad_request(
            [{"field": "events", "message": str(e),
              "expected": "[{start, summary?, end?|duration?, tz?, uid?, "
                          "rrule?, ...}]"}])
    return {"output": text, "sha256": _sha_text(text)}, None


@app.post("/api/v1/ics/generate")
def api_ics_generate(req: IcsGenerateRequest):
    body, err = run_ics_generate(req.model_dump())
    return err if err else body


class IcsParseRequest(BaseModel):
    ics: str


def run_ics_parse(args: dict):
    try:
        req = IcsParseRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = dates.ics_parse(req.ics)
    except dates.DateError as e:
        return None, bad_request(
            [{"field": "ics", "message": str(e),
              "expected": "VCALENDAR text (BEGIN:VCALENDAR)"}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/ics/parse")
def api_ics_parse(req: IcsParseRequest):
    body, err = run_ics_parse(req.model_dump())
    return err if err else body


# ------------------------------------------------- bundle 4.1: numbers

class NumFormatRequest(BaseModel):
    value: Any
    locale: str = "en-US"
    style: Literal["number", "currency", "percent"] = "number"
    currency: Optional[str] = None
    decimals: Optional[int] = None
    grouping: bool = True


def run_num_format(args: dict):
    try:
        req = NumFormatRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = numfmt.num_format(req.value, req.locale, req.style,
                                req.currency, req.decimals, req.grouping)
    except numfmt.NumberError as e:
        return None, bad_request(
            [{"field": "value", "message": str(e),
              "expected": "number or numeric string; locale/currency from "
                          "the closed tables"}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/num/format")
def api_num_format(req: NumFormatRequest):
    body, err = run_num_format(req.model_dump())
    return err if err else body


class NumParseRequest(BaseModel):
    text: str
    prefer: Optional[Literal["decimal", "group"]] = None


def run_num_parse(args: dict):
    try:
        req = NumParseRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = numfmt.num_parse(req.text, req.prefer)
    except numfmt.NumberError as e:
        return None, bad_request(
            [{"field": "text", "message": str(e),
              "expected": "grouped/decimal number, optionally with currency "
                          "or %; ambiguity resolved by prefer"}],
            "unparsable_number")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/num/parse")
def api_num_parse(req: NumParseRequest):
    body, err = run_num_parse(req.model_dump())
    return err if err else body


class NumRoundRequest(BaseModel):
    value: Any
    places: int = Field(default=0, ge=0, le=30)
    mode: Literal["half_even", "half_up", "half_down", "ceil", "floor",
                  "trunc", "up"] = "half_even"
    significant: bool = False


def run_num_round(args: dict):
    try:
        req = NumRoundRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = numfmt.num_round(req.value, req.places, req.mode,
                               req.significant)
    except numfmt.NumberError as e:
        return None, bad_request([{"field": "value", "message": str(e)}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/num/round")
def api_num_round(req: NumRoundRequest):
    body, err = run_num_round(req.model_dump())
    return err if err else body


# -------------------------------------------- bundle 4.2: units & money

class UnitsConvertRequest(BaseModel):
    model_config = {"populate_by_name": True}
    value: Any
    from_unit: str = Field(alias="from")
    to_unit: str = Field(alias="to")
    places: int = Field(default=10, ge=0, le=30)


def run_units_convert(args: dict):
    try:
        req = UnitsConvertRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = units.units_convert(req.value, req.from_unit, req.to_unit,
                                  req.places)
    except units.UnitError as e:
        return None, bad_request([{"field": "from", "message": str(e),
                                   "expected": "units from the closed "
                                               "families"}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/units/convert")
def api_units_convert(req: UnitsConvertRequest):
    body, err = run_units_convert(
        {"value": req.value, "from": req.from_unit, "to": req.to_unit,
         "places": req.places})
    return err if err else body


class MoneyProrateRequest(BaseModel):
    amount: str
    cycle_start: str
    cycle_end: str
    service_start: str
    service_end: str
    places: int = Field(default=2, ge=0, le=12)
    mode: Literal["half_even", "half_up", "ceil", "floor", "trunc"] = "half_up"
    inclusive: bool = True
    clamp: bool = True


def run_money_prorate(args: dict):
    try:
        req = MoneyProrateRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = money.money_prorate(req.amount, req.cycle_start, req.cycle_end,
                                  req.service_start, req.service_end,
                                  req.places, req.mode, req.inclusive,
                                  req.clamp)
    except money.MoneyError as e:
        return None, bad_request(
            [{"field": "amount", "message": str(e),
              "expected": "amount as string, ISO dates, mode in half_even|"
                          "half_up|ceil|floor|trunc"}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/money/prorate")
def api_money_prorate(req: MoneyProrateRequest):
    body, err = run_money_prorate(req.model_dump())
    return err if err else body


class MoneySplitRequest(BaseModel):
    total: str
    participants: List[Any]
    mode: Literal["remainder_order"] = "remainder_order"


def run_money_split(args: dict):
    try:
        req = MoneySplitRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = money.money_split(req.total, req.participants, req.mode)
    except money.MoneyError as e:
        return None, bad_request(
            [{"field": "participants", "message": str(e),
              "expected": "[name | {name, weight?}] non-empty"}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/money/split")
def api_money_split(req: MoneySplitRequest):
    body, err = run_money_split(req.model_dump())
    return err if err else body


# --------------------------------------------- bundle 4.3: spell-out

class NumberSpellRequest(BaseModel):
    value: Any
    lang: Literal["fr", "en", "pt"] = "fr"
    currency: Optional[str] = None
    cents: bool = True
    capital: bool = False


def run_number_spell(args: dict):
    try:
        req = NumberSpellRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = spell.num_spell(req.value, req.lang, req.currency,
                              req.cents, req.capital)
    except spell.SpellError as e:
        return None, bad_request(
            [{"field": "value", "message": str(e),
              "expected": "amount with at most 2 decimals; lang in fr|en|pt; "
                          "currency from the closed words table"}],
            "spell_failed")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/number/spell")
def api_number_spell(req: NumberSpellRequest):
    body, err = run_number_spell(req.model_dump())
    return err if err else body


# ------------------------------------------- bundle 5.1: identity (free)

class HashDigestRequest(BaseModel):
    data: str
    algo: Literal["md5", "sha1", "sha256", "sha512", "blake2b"] = "sha256"
    input_kind: Literal["text", "base64", "hex"] = "text"


def run_hash_digest(args: dict):
    try:
        req = HashDigestRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = identity.hash_digest(req.data, req.algo, req.input_kind)
    except identity.IdentityError as e:
        return None, bad_request([{"field": "data", "message": str(e)}])
    out["sha256"] = out["hex"]
    return out, None


class IdUlidRequest(BaseModel):
    mode: str = "make"
    timestamp_ms: Optional[int] = None
    entropy: Optional[str] = None
    seed: Optional[str] = None
    ulid: Optional[str] = None
    ids: Optional[list] = None


def run_id_ulid(args: dict):
    try:
        out = identity.ulid_op(args.get("mode", "make"),
                               args.get("timestamp_ms"),
                               args.get("entropy"), args.get("seed"),
                               args.get("ulid"), args.get("ids"))
    except (identity.IdentityError, ValueError) as e:
        return None, bad_request([{"field": "mode",
                                   "message": "ulid: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/id/ulid")
def api_id_ulid(req: IdUlidRequest):
    body, err = run_id_ulid(req.model_dump())
    return err if err else body


class PkgNameRequest(BaseModel):
    name: str
    kind: str = "npm"


def run_pkg_name(args: dict):
    try:
        out = edits.pkgname_op(args.get("name"), args.get("kind", "npm"))
    except (edits.EditError, ValueError) as e:
        return None, bad_request([{"field": "name",
                                   "message": "pkg/name: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/pkg/name")
def api_pkg_name(req: PkgNameRequest):
    body, err = run_pkg_name(req.model_dump())
    return err if err else body


class NetIpRequest(BaseModel):
    value: str


def run_net_ip(args: dict):
    try:
        out = micro.net_ip(args.get("value"))
    except micro.MicroError as e:
        return None, bad_request([{"field": "value",
                                   "message": "net/ip: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/net/ip")
def api_net_ip(req: NetIpRequest):
    body, err = run_net_ip(req.model_dump())
    return err if err else body


class NetCidrRequest(BaseModel):
    cidr: str
    contains: Optional[str] = None
    split_into: Optional[int] = None


def run_net_cidr(args: dict):
    try:
        out = micro.net_cidr(args.get("cidr"), args.get("contains"),
                             args.get("split_into"))
    except micro.MicroError as e:
        return None, bad_request([{"field": "cidr",
                                   "message": "net/cidr: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/net/cidr")
def api_net_cidr(req: NetCidrRequest):
    body, err = run_net_cidr(req.model_dump())
    return err if err else body


class FileEncodingRequest(BaseModel):
    blob: str


def run_file_encoding(args: dict):
    try:
        out = micro.file_encoding(args.get("blob"))
    except Exception as e:
        return None, bad_request([{"field": "blob",
                                   "message": "file/encoding: invalid "
                                              "base64"}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/file/encoding")
def api_file_encoding(req: FileEncodingRequest):
    body, err = run_file_encoding(req.model_dump())
    return err if err else body


class QrRequest(BaseModel):
    text: Optional[str] = None
    ecl: str = "M"
    version: Optional[int] = None
    scale: int = 8
    quiet: int = 4
    format: str = "svg"


def run_qr(args: dict):
    try:
        d = qrkit.qr_matrix(args.get("text"),
                            ecl=args.get("ecl") or "M",
                            version=args.get("version"))
    except qrkit.QrError as e:
        return None, bad_request([{"field": "text",
                                   "message": "qr: %s" % e}])
    fmt = args.get("format") or "svg"
    out = {"version": d["version"], "mode": d["mode"],
           "ecl": d["ecl"], "mask": d["mask"], "size": d["size"],
           "modules": sum(sum(r) for r in d["matrix"])}
    if fmt == "svg":
        try:
            svg = qrkit.qr_svg(d["matrix"], scale=args.get("scale") or 8,
                               quiet=args.get("quiet") if
                               args.get("quiet") is not None else 4)
        except (ValueError, TypeError):
            return None, bad_request([{"field": "scale",
                                       "message": "qr: scale/quiet must "
                                                 "be integers"}])
        out["svg"] = svg
    elif fmt == "matrix":
        out["matrix"] = d["matrix"]
    else:
        return None, bad_request([{"field": "format",
                                   "message": "qr: format is svg or "
                                              "matrix"}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/qr/generate")
def api_qr(req: QrRequest):
    body, err = run_qr(req.model_dump())
    return err if err else body


class VerifyRequest(BaseModel):
    base_url: Optional[str] = None
    pins: Optional[list] = None
    integrity_url: Optional[str] = None
    attempts: int = 3
    mode: str = "bytes"


def run_verify(args: dict):
    try:
        out = auditor.integrity_verify(args.get("base_url"),
                                       pins=args.get("pins"),
                                       integrity_url=args.get(
                                           "integrity_url"),
                                       attempts=args.get("attempts") or 3,
                                       mode=args.get("mode") or "bytes")
    except auditor.AuditError as e:
        return None, bad_request([{"field": "base_url",
                                   "message": "audit: %s" % e}])
    return out, None


@app.post("/api/v1/integrity/verify")
def api_verify(req: VerifyRequest):
    body, err = run_verify(req.model_dump())
    return err if err else body


def run_rates(args: dict):
    try:
        out = rates.money_rates(
            currency_from=args.get("from") or "EUR",
            currency_to=args.get("to"),
            amount=args.get("amount"), date=args.get("date"))
    except rates.RatesError as e:
        return None, bad_request([{"field": "date",
                                   "message": "rates: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.get("/api/v1/money/rates")
def api_rates(date: Optional[str] = None,
              frm: Optional[str] = Query(None, alias="from"),
              to: Optional[str] = None,
              amount: Optional[str] = None):
    body, err = run_rates({"date": date, "from": frm, "to": to,
                           "amount": amount})
    return err if err else body


class CalcRequest(BaseModel):
    expr: str
    digits: Optional[int] = None


def run_calc(args: dict):
    try:
        out = calckit.calc(args.get("expr"), args.get("digits"))
    except calckit.CalcError as e:
        return None, bad_request([{"field": "expr",
                                   "message": "math/calc: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/math/calc")
def api_calc(req: CalcRequest):
    body, err = run_calc(req.dict())
    return err if err else body


class DiscountRequest(BaseModel):
    price: str
    steps: list
    qty: int = 1
    currency: Optional[str] = None


def run_discount(args: dict):
    try:
        out = discountkit.discount_chain(
            args.get("price"), args.get("steps") or [],
            qty=int(args.get("qty") or 1),
            currency=args.get("currency"))
    except discountkit.DiscountError as e:
        return None, bad_request([{"field": "steps",
                                   "message": "discount: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/money/discount")
def api_discount(req: DiscountRequest):
    body, err = run_discount(req.dict())
    return err if err else body


class SqlDumpRequest(BaseModel):
    csv: Optional[str] = None
    rows: Optional[list] = None
    table: str = "data"
    dialect: str = "sqlite"
    create: bool = True
    if_not_exists: bool = True
    rows_per_statement: int = 100
    empty_as_null: bool = False
    types: Optional[dict] = None
    delimiter: Optional[str] = None


def run_sql_dump(args: dict):
    try:
        out = sqlkit.dump(csv_text=args.get("csv"),
                          rows=args.get("rows"),
                          table=args.get("table") or "data",
                          dialect=args.get("dialect") or "sqlite",
                          create=bool(args.get("create", True)),
                          if_not_exists=bool(args.get("if_not_exists",
                                                      True)),
                          rows_per_statement=int(
                              args.get("rows_per_statement") or 100),
                          empty_as_null=bool(args.get("empty_as_null")),
                          types=args.get("types"),
                          delimiter=args.get("delimiter"))
    except (sqlkit.SqlDumpError, ValueError, TypeError) as e:
        return None, bad_request([{"field": "csv|rows",
                                   "message": "sql_dump: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/table/sql_dump")
def api_sql_dump(req: SqlDumpRequest):
    body, err = run_sql_dump(req.dict())
    return err if err else body


class ScaleRequest(BaseModel):
    items: list
    factor: Optional[str] = None
    servings_from: Optional[str] = None
    servings_to: Optional[str] = None
    power_default: Optional[str] = None


def run_table_scale(args: dict):
    try:
        out = scalekit.scale(items=args.get("items"),
                             factor=args.get("factor"),
                             servings_from=args.get("servings_from"),
                             servings_to=args.get("servings_to"),
                             power_default=args.get("power_default"))
    except scalekit.ScaleError as e:
        return None, bad_request([{"field": "items|factor|servings_*",
                                   "message": "table/scale: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/table/scale")
def api_table_scale(req: ScaleRequest):
    body, err = run_table_scale(req.dict())
    return err if err else body


class CheckFormatRequest(BaseModel):
    payload: Any
    formats: dict


def run_check_format(args: dict):
    try:
        out = formatkit.check_format(args.get("payload"),
                                     args.get("formats") or {})
    except formatkit.FormatError as e:
        return None, bad_request([{"field": "formats",
                                   "message": "check/format: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/check/format")
def api_check_format(req: CheckFormatRequest):
    body, err = run_check_format(req.dict())
    return err if err else body


class MoneyColumnsRequest(BaseModel):
    csv: str
    columns: Optional[list] = None
    delimiter: Optional[str] = None


def run_money_columns(args: dict):
    try:
        out = moneykit.analyze(
            args.get("csv") or "", columns=args.get("columns"),
            delimiter=args.get("delimiter") or None)
    except moneykit.MoneyError as e:
        return None, bad_request([{"field": "csv",
                                   "message": "money_columns: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/csv/money_columns")
def api_money_columns(req: MoneyColumnsRequest):
    body, err = run_money_columns(req.dict())
    return err if err else body


class RelativeDateRequest(BaseModel):
    phrase: str
    now: Optional[str] = None
    tz: Optional[str] = None


def run_relative_date(args: dict):
    try:
        out = reldate.resolve(args.get("phrase") or "",
                              now=args.get("now"), tz=args.get("tz"))
    except reldate.RelDateError as e:
        return None, bad_request([{"field": "phrase",
                                   "message": "relative date: %s" % e}])
    except ValueError:
        return None, bad_request([{"field": "now",
                                   "message": "relative date: now must "
                                              "be ISO-8601"}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/date/relative")
def api_relative_date(req: RelativeDateRequest):
    body, err = run_relative_date(req.dict())
    return err if err else body


class UrlCanonicalRequest(BaseModel):
    url: str
    strip_tracking: bool = True
    sort_params: bool = False
    drop_fragment: bool = False


def run_url_canonical(args: dict):
    try:
        out = urlkit.canonicalize(
            args.get("url") or "",
            strip_tracking=args.get("strip_tracking", True),
            sort_params=bool(args.get("sort_params")),
            drop_fragment=bool(args.get("drop_fragment")))
    except urlkit.UrlError as e:
        return None, bad_request([{"field": "url",
                                   "message": "url: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/text/url_canonical")
def api_url_canonical(req: UrlCanonicalRequest):
    body, err = run_url_canonical(req.dict())
    return err if err else body


class XmlJsonRequest(BaseModel):
    xml: str
    force_array: Optional[list] = None
    coerce: bool = False


def run_xml_json(args: dict):
    try:
        out = xmlkit.to_json(
            args.get("xml") or "",
            force_array=args.get("force_array"),
            coerce=bool(args.get("coerce")))
    except xmlkit.XmlError as e:
        return None, bad_request([{"field": "xml",
                                   "message": "xml: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/xml/to_json")
def api_xml_json(req: XmlJsonRequest):
    body, err = run_xml_json(req.dict())
    return err if err else body


class CertRequest(BaseModel):
    pem: str
    as_of: Optional[str] = None


def run_cert(args: dict):
    try:
        out = certkit.lint(args.get("pem") or "",
                           as_of=args.get("as_of"))
    except certkit.CertError as e:
        return None, bad_request([{"field": "pem",
                                   "message": "cert: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/web/cert")
def api_cert(req: CertRequest):
    body, err = run_cert(req.dict())
    return err if err else body


class CheckdigitRequest(BaseModel):
    mode: str = "check"
    value: Optional[str] = None
    scheme: Optional[str] = None
    text: Optional[str] = None


def run_checkdigit(args: dict):
    mode = args.get("mode") or "check"
    try:
        out = digitkit.checkdigit(mode=mode, value=args.get("value"),
                                  scheme=args.get("scheme"),
                                  text=args.get("text"))
    except digitkit.DigitError as e:
        field = "text" if mode == "scan" else "value"
        if mode not in digitkit.MODES:
            field = "mode"
        return None, bad_request([{"field": field,
                                   "message": "checkdigit: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/id/checkdigit")
def api_checkdigit(req: CheckdigitRequest):
    body, err = run_checkdigit(req.dict())
    return err if err else body


class RightsizeRequest(BaseModel):
    data_b64: str
    width: Optional[int] = None
    height: Optional[int] = None
    mode: str = "fit"
    resample: str = "box"


def run_rightsize(args: dict):
    try:
        raw = base64.b64decode(args.get("data_b64") or "", validate=True)
    except ValueError:
        return None, bad_request([{"field": "data_b64", "message":
                                   "rightsize: data_b64 is not valid "
                                   "base64"}])
    try:
        img = pngkit.decode(raw)
        out, algo = pngkit.rightsize(
            img, args.get("width"), args.get("height"),
            args.get("mode") or "fit", args.get("resample") or "box")
        enc = pngkit.encode(out)
    except pngkit.PngError as e:
        return None, bad_request([{"field": "data_b64",
                                   "message": "rightsize: %s" % e}])
    res = {"source": {"width": img["w"], "height": img["h"],
                      "depth": img["depth"],
                      "channels": img["channels"]},
           "result": {"width": out["w"], "height": out["h"],
                      "bytes": len(enc),
                      "png_b64": base64.b64encode(enc).decode()},
           "source_bytes": len(raw), "algorithm": algo}
    res["sha256"] = canon(res)
    return res, None


@app.post("/api/v1/image/rightsize")
def api_rightsize(req: RightsizeRequest):
    body, err = run_rightsize(req.dict())
    return err if err else body


class DocTextRequest(BaseModel):
    pdf_b64: Optional[str] = None
    page: Optional[int] = None


def run_doc_text(args: dict):
    try:
        out = pdftext.extract_text(args.get("pdf_b64"))
    except pdftext.PdfError as e:
        return None, bad_request([{"field": "pdf_b64",
                                   "message": "pdf: %s" % e}])
    pg = args.get("page")
    if pg is not None:
        if not isinstance(pg, int) or not 1 <= pg <= out["page_count"]:
            return None, bad_request([
                {"field": "page",
                 "message": "page must be 1-%d" % out["page_count"]}])
        out = {"page": pg, **out["pages"][pg - 1],
               "page_count": out["page_count"],
               "verdict": out["verdict"]}
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/doc/text")
def api_doc_text(req: DocTextRequest):
    body, err = run_doc_text(req.model_dump())
    return err if err else body


class AmortizeRequest(BaseModel):
    principal: Optional[object] = None
    annual_rate_pct: Optional[object] = None
    months: Optional[int] = None


class InterestRequest(BaseModel):
    principal: Optional[object] = None
    annual_rate_pct: Optional[object] = None
    years: Optional[object] = None
    compounds_per_year: int = 12


def run_amortize(args: dict):
    try:
        out = amortize.money_amortize(args.get("principal"),
                                      args.get("annual_rate_pct"),
                                      args.get("months"))
    except amortize.MoneyError as e:
        return None, bad_request([{"field": "principal",
                                   "message": "amortize: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


def run_interest(args: dict):
    try:
        out = amortize.money_interest(args.get("principal"),
                                      args.get("annual_rate_pct"),
                                      args.get("years"),
                                      args.get("compounds_per_year") or 12)
    except amortize.MoneyError as e:
        return None, bad_request([{"field": "principal",
                                   "message": "interest: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/money/amortize")
def api_amortize(req: AmortizeRequest):
    body, err = run_amortize(req.model_dump())
    return err if err else body


@app.post("/api/v1/money/interest")
def api_interest(req: InterestRequest):
    body, err = run_interest(req.model_dump())
    return err if err else body


class IcsRequest(BaseModel):
    text: Optional[str] = None


def run_ics(args: dict):
    try:
        out = icskit.ics_lint(args.get("text"))
    except ValueError as e:
        return None, bad_request([{"field": "text",
                                   "message": "ics: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/ics/validate")
def api_ics(req: IcsRequest):
    body, err = run_ics(req.model_dump())
    return err if err else body


class HolidaysRequest(BaseModel):
    country: Optional[str] = None
    year: Optional[int] = None
    on: Optional[str] = None


def run_holidays(args: dict):
    try:
        if args.get("on"):
            out = holidays.is_holiday(args.get("country"), args["on"])
        else:
            out = holidays.holidays(args.get("country"),
                                    args.get("year"))
    except (holidays.HolidayError, ValueError) as e:
        return None, bad_request([{"field": "country",
                                   "message": "holidays: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/schedule/holidays")
def api_holidays(req: HolidaysRequest):
    body, err = run_holidays(req.model_dump())
    return err if err else body


class WebCacheRequest(BaseModel):
    header: Optional[str] = None
    method: str = "GET"
    conditional: bool = False


class GzipRequest(BaseModel):
    payload_b64: Optional[str] = None
    mode: str = "compress"
    level: int = 9


def run_web_cache(args: dict):
    try:
        out = webkit.web_cache(args.get("header"),
                               method=args.get("method") or "GET",
                               conditional=bool(args.get("conditional")))
    except webkit.WebError as e:
        return None, bad_request([{"field": "header",
                                   "message": "cache: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


def run_gzip(args: dict):
    try:
        out = webkit.compress_gzip(args.get("payload_b64"),
                                   mode=args.get("mode") or "compress",
                                   level=args.get("level") or 9)
    except webkit.WebError as e:
        return None, bad_request([{"field": "payload_b64",
                                   "message": "gzip: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/web/cache")
def api_web_cache(req: WebCacheRequest):
    body, err = run_web_cache(req.model_dump())
    return err if err else body


@app.post("/api/v1/gzip/roundtrip")
def api_gzip(req: GzipRequest):
    body, err = run_gzip(req.model_dump())
    return err if err else body


class PeekRequest(BaseModel):
    rows: Optional[list] = None


class DiffRequest(BaseModel):
    left: Optional[list] = None
    right: Optional[list] = None
    key: Optional[object] = None


def run_table_peek(args: dict):
    try:
        out = tables.table_peek(args.get("rows"))
    except tables.TransformError as e:
        return None, bad_request([{"field": "rows",
                                   "message": "peek: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


def run_csv_diff(args: dict):
    try:
        out = tables.csv_diff(args.get("left"), args.get("right"),
                              args.get("key"))
    except tables.TransformError as e:
        return None, bad_request([{"field": "left",
                                   "message": "diff: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/table/peek")
def api_peek(req: PeekRequest):
    body, err = run_table_peek(req.model_dump())
    return err if err else body


@app.post("/api/v1/csv/diff")
def api_diff(req: DiffRequest):
    body, err = run_csv_diff(req.model_dump())
    return err if err else body


class SshFpRequest(BaseModel):
    line: Optional[str] = None


class ZipVerifyRequest(BaseModel):
    blob_b64: Optional[str] = None


def run_ssh_fp(args: dict):
    try:
        out = webkit.ssh_fingerprint(args.get("line"))
    except webkit.WebError as e:
        return None, bad_request([{"field": "line",
                                   "message": "ssh: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


def run_zip_verify(args: dict):
    try:
        out = webkit.zip_verify(args.get("blob_b64"))
    except webkit.WebError as e:
        return None, bad_request([{"field": "blob_b64",
                                   "message": "zip: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/ssh/fingerprint")
def api_ssh_fp(req: SshFpRequest):
    body, err = run_ssh_fp(req.model_dump())
    return err if err else body


@app.post("/api/v1/zip/verify")
def api_zip(req: ZipVerifyRequest):
    body, err = run_zip_verify(req.model_dump())
    return err if err else body


class OverlapRequest(BaseModel):
    intervals: Optional[list] = None
    mode: str = "merge"
    window: Optional[dict] = None
    point: Optional[str] = None


class CronRequest(BaseModel):
    expr: Optional[str] = None
    at: Optional[str] = None
    count: int = 5


def run_schedule_overlap(args: dict):
    try:
        out = timekit.schedule_overlap(
            args.get("intervals"), mode=args.get("mode") or "merge",
            window=args.get("window"), point=args.get("point"))
    except timekit.TimeError as e:
        return None, bad_request([{"field": "intervals",
                                   "message": "schedule: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


def run_cron(args: dict):
    try:
        if args.get("at"):
            out = timekit.cron_next(args.get("expr"), args["at"],
                                    count=args.get("count") or 5)
        else:
            parsed, dom_star, dow_star = timekit.cron_parse(
                args.get("expr"))
            reason = timekit._never_reason(parsed, dom_star, dow_star)
            out = {"expr": args.get("expr"),
                   "fields": {k: sorted(v) for k, v in parsed.items()},
                   "never": bool(reason),
                   "dom_dow_semantics": "both restricted => OR (Vixie)"}
            if reason:
                out["reason"] = reason
    except timekit.TimeError as e:
        return None, bad_request([{"field": "expr",
                                   "message": "cron: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/schedule/overlap")
def api_overlap(req: OverlapRequest):
    body, err = run_schedule_overlap(req.model_dump())
    return err if err else body


@app.post("/api/v1/cron/validate")
def api_cron(req: CronRequest):
    body, err = run_cron(req.model_dump())
    return err if err else body


class CryptoAddressRequest(BaseModel):
    address: Optional[str] = None
    chain: str = "auto"


def run_crypto_address(args: dict):
    try:
        out = addrkit.crypto_address(args.get("address"),
                                     chain=args.get("chain") or "auto")
    except addrkit.AddressError as e:
        return None, bad_request([{"field": "address",
                                   "message": "address: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/crypto/address")
def api_crypto_address(req: CryptoAddressRequest):
    body, err = run_crypto_address(req.model_dump())
    return err if err else body


class TaxIdRequest(BaseModel):
    value: Optional[str] = None
    kind: str = "auto"


def run_tax_validate(args: dict):
    try:
        out = taxid.tax_validate(args.get("value"),
                                 kind=args.get("kind") or "auto")
    except taxid.TaxError as e:
        return None, bad_request([{"field": "value",
                                   "message": "taxid: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/validate/taxid")
def api_taxid(req: TaxIdRequest):
    body, err = run_tax_validate(req.model_dump())
    return err if err else body


class CaipRequest(BaseModel):
    value: Optional[str] = None
    namespace: Optional[str] = None
    reference: Optional[str] = None
    address: Optional[str] = None
    mode: str = "parse"


def run_caip(args: dict):
    try:
        if args.get("mode") == "format":
            out = chainkit.caip_format(args.get("namespace"),
                                       args.get("reference"),
                                       args.get("address"))
        else:
            out = chainkit.caip_parse(args.get("value"))
    except chainkit.CaipError as e:
        return None, bad_request([{"field": "value",
                                   "message": "caip: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/caip/parse")
def api_caip(req: CaipRequest):
    body, err = run_caip(req.model_dump())
    return err if err else body


class SecretScanRequest(BaseModel):
    text: str
    kinds: Optional[list] = None


def run_secret_scan(args: dict):
    try:
        out = leakkit.scan_secrets(args.get("text"), args.get("kinds"))
    except ValueError as e:
        return None, bad_request([{"field": "text",
                                   "message": "secret/scan: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/secret/scan")
def api_secret_scan(req: SecretScanRequest):
    body, err = run_secret_scan(req.model_dump())
    return err if err else body


class TextRedactRequest(BaseModel):
    text: str
    mask_tag: Optional[str] = None


def run_text_redact(args: dict):
    try:
        out = leakkit.redact(args.get("text"), args.get("mask_tag"))
    except ValueError as e:
        return None, bad_request([{"field": "text",
                                   "message": "text/redact: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/text/redact")
def api_text_redact(req: TextRedactRequest):
    body, err = run_text_redact(req.model_dump())
    return err if err else body


class ValidateCountryRequest(BaseModel):
    code: str


def run_validate_country(args: dict):
    try:
        out = units.validate_country(args.get("code"))
    except units.UnitError as e:
        return None, bad_request([{"field": "code",
                                   "message": "validate/country: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/validate/country")
def api_validate_country(req: ValidateCountryRequest):
    body, err = run_validate_country(req.model_dump())
    return err if err else body


class ValidatePostalRequest(BaseModel):
    code: str
    country: str


def run_validate_postal(args: dict):
    try:
        out = units.validate_postal(args.get("code"),
                                    args.get("country"))
    except units.UnitError as e:
        return None, bad_request([{"field": "country",
                                   "message": "validate/postal: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/validate/postal")
def api_validate_postal(req: ValidatePostalRequest):
    body, err = run_validate_postal(req.model_dump())
    return err if err else body


class GeoDistanceRequest(BaseModel):
    a: Optional[Dict[str, float]] = None
    b: Optional[Dict[str, float]] = None
    route: Optional[list] = None


def run_geo_distance(args: dict):
    try:
        out = geo.geo_distance(args.get("a"), args.get("b"),
                               args.get("route"))
    except (ValueError, KeyError, TypeError) as e:
        return None, bad_request([{"field": "a",
                                   "message": "geo/distance: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/geo/distance")
def api_geo_distance(req: GeoDistanceRequest):
    body, err = run_geo_distance(req.model_dump())
    return err if err else body


class GeoGeohashRequest(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    geohash: Optional[str] = None
    precision: int = 6


def run_geo_geohash(args: dict):
    try:
        out = geo.geo_geohash(args.get("lat"), args.get("lon"),
                              args.get("geohash"),
                              args.get("precision", 6))
    except (ValueError, KeyError, TypeError) as e:
        return None, bad_request([{"field": "precision",
                                   "message": "geo/geohash: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/geo/geohash")
def api_geo_geohash(req: GeoGeohashRequest):
    body, err = run_geo_geohash(req.model_dump())
    return err if err else body


class FileIdentifyRequest(BaseModel):
    blob: str


def run_file_identify(args: dict):
    try:
        out = micro.file_identify(args.get("blob"))
    except micro.MicroError as e:
        return None, bad_request([{"field": "blob",
                                   "message": "file/identify: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/file/identify")
def api_file_identify(req: FileIdentifyRequest):
    body, err = run_file_identify(req.model_dump())
    return err if err else body


class TextPunycodeRequest(BaseModel):
    domain: str


def run_text_punycode(args: dict):
    try:
        out = micro.text_punycode(args.get("domain"))
    except micro.MicroError as e:
        return None, bad_request([{"field": "domain",
                                   "message": "punycode: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/text/punycode")
def api_text_punycode(req: TextPunycodeRequest):
    body, err = run_text_punycode(req.model_dump())
    return err if err else body


class SemverParseRequest(BaseModel):
    version: str


def run_semver_parse(args: dict):
    try:
        out = micro.semver_parse(args.get("version"))
    except micro.MicroError as e:
        return None, bad_request([{"field": "version",
                                   "message": "semver: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/semver/parse")
def api_semver_parse(req: SemverParseRequest):
    body, err = run_semver_parse(req.model_dump())
    return err if err else body


class SemverSortRequest(BaseModel):
    versions: list


def run_semver_sort(args: dict):
    try:
        out = micro.semver_sort(args.get("versions"))
    except micro.MicroError as e:
        return None, bad_request([{"field": "versions",
                                   "message": "semver: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/semver/sort")
def api_semver_sort(req: SemverSortRequest):
    body, err = run_semver_sort(req.model_dump())
    return err if err else body


class TextSanitizeRequest(BaseModel):
    name: str
    sep: str = "_"
    max_bytes: int = 255


def run_text_sanitize(args: dict):
    try:
        out = micro.text_sanitize(args.get("name"), args.get("sep", "_"),
                                  args.get("max_bytes", 255))
    except micro.MicroError as e:
        return None, bad_request([{"field": "name",
                                   "message": "sanitize: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/text/sanitize")
def api_text_sanitize(req: TextSanitizeRequest):
    body, err = run_text_sanitize(req.model_dump())
    return err if err else body


class JsonMapRequest(BaseModel):
    items: list
    ops: list


def run_json_map(args: dict):
    try:
        out = micro.json_map(args.get("items"), args.get("ops") or [])
    except (micro.MicroError, TypeError) as e:
        return None, bad_request([{"field": "items",
                                   "message": "json/map: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/json/map")
def api_json_map(req: JsonMapRequest):
    body, err = run_json_map(req.model_dump())
    return err if err else body


class NumFxRequest(BaseModel):
    amount: str
    rate: str
    to: str
    precision: Optional[int] = None


def run_num_fx(args: dict):
    try:
        out = money.num_fx(args.get("amount"), args.get("rate"),
                           args.get("to"), args.get("precision"))
    except (money.MoneyError, Exception) as e:
        if not isinstance(e, money.MoneyError):
            e = money.MoneyError("amount and rate must be numeric strings")
        return None, bad_request([{"field": "to" if "currency" in str(e)
                                   else "amount",
                                   "message": "num/fx: %s" % e}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/num/fx")
def api_num_fx(req: NumFxRequest):
    body, err = run_num_fx(req.model_dump())
    return err if err else body


class HashHmacRequest(BaseModel):
    message: str
    key: str
    algo: str = "sha256"
    key_kind: str = "text"
    message_kind: str = "text"
    signature: Optional[str] = None


def run_hash_hmac(args: dict):
    try:
        out = identity.hmac_op(args.get("message"), args.get("key"),
                               args.get("algo", "sha256"),
                               args.get("key_kind", "text"),
                               args.get("message_kind", "text"),
                               args.get("signature"))
    except (identity.IdentityError, ValueError) as e:
        field = "algo" if "algo" in str(e) else "key"
        return None, bad_request([{"field": field, "message": str(e)}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/hash/hmac")
def api_hash_hmac(req: HashHmacRequest):
    body, err = run_hash_hmac(req.model_dump())
    return err if err else body


@app.post("/api/v1/hash/digest")
def api_hash_digest(req: HashDigestRequest):
    body, err = run_hash_digest(req.model_dump())
    return err if err else body


class EncBase64Request(BaseModel):
    text: str
    op: Literal["encode", "decode"] = "encode"
    variant: Literal["base64", "base64url", "hex"] = "base64"
    padding: bool = True


def run_enc_base64(args: dict):
    try:
        req = EncBase64Request(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = identity.enc_convert(req.text, req.op, req.variant,
                                   req.padding)
    except identity.IdentityError as e:
        return None, bad_request([{"field": "text", "message": str(e),
                                   "expected": "text to encode, or strict "
                                               "base64/hex to decode"}])
    out["sha256"] = _sha_text(str(out["result"]))
    return out, None


@app.post("/api/v1/enc/base64")
def api_enc_base64(req: EncBase64Request):
    body, err = run_enc_base64(req.model_dump())
    return err if err else body


class JwtDecodeRequest(BaseModel):
    token: str


def run_jwt_decode(args: dict):
    try:
        req = JwtDecodeRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = identity.jwt_decode(req.token)
    except identity.IdentityError as e:
        return None, bad_request([{"field": "token", "message": str(e)}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/jwt/decode")
def api_jwt_decode(req: JwtDecodeRequest):
    body, err = run_jwt_decode(req.model_dump())
    return err if err else body


class IdUuidRequest(BaseModel):
    op: Literal["v5", "v4_seeded", "v7"] = "v5"
    name: Optional[str] = None
    namespace: str = "url"
    seed: Optional[str] = None
    at: Optional[Any] = None


def run_id_uuid(args: dict):
    try:
        req = IdUuidRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = identity.id_uuid(req.op, req.name, req.namespace, req.seed,
                               req.at)
    except identity.IdentityError as e:
        return None, bad_request([{"field": "op", "message": str(e)}])
    out["sha256"] = _sha_text(out["uuid"])
    return out, None


@app.post("/api/v1/id/uuid")
def api_id_uuid(req: IdUuidRequest):
    body, err = run_id_uuid(req.model_dump())
    return err if err else body


class IdSlugRequest(BaseModel):
    text: str
    sep: Literal["-", "_"] = "-"
    lower: bool = True
    max_len: int = 0


def run_id_slug(args: dict):
    try:
        req = IdSlugRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = identity.id_slug(req.text, req.sep, req.lower, req.max_len)
    except identity.IdentityError as e:
        return None, bad_request([{"field": "text", "message": str(e)}])
    out["sha256"] = _sha_text(out["slug"])
    return out, None


@app.post("/api/v1/id/slug")
def api_id_slug(req: IdSlugRequest):
    body, err = run_id_slug(req.model_dump())
    return err if err else body


class FingerprintRequest(BaseModel):
    value: Any
    kind: Literal["json", "csv"] = "json"


def run_fingerprint(args: dict):
    try:
        req = FingerprintRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = identity.fingerprint(req.value, req.kind)
    except identity.IdentityError as e:
        return None, bad_request([{"field": "value", "message": str(e)}])
    return out, None


@app.post("/api/v1/fingerprint")
def api_fingerprint(req: FingerprintRequest):
    body, err = run_fingerprint(req.model_dump())
    return err if err else body


# ------------------------------------------------ bundle 6.1: checkers

class ValidateIbanRequest(BaseModel):
    iban: str


def run_validate_iban(args: dict):
    try:
        req = ValidateIbanRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = checkers.check_iban(req.iban)
    except checkers.CheckError as e:
        return None, bad_request([{"field": "iban", "message": str(e)}],
                                 "check_failed")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/validate/iban")
def api_validate_iban(req: ValidateIbanRequest):
    body, err = run_validate_iban(req.model_dump())
    return err if err else body


class ValidatePhoneRequest(BaseModel):
    phone: str
    default_country: Optional[str] = None


def run_validate_phone(args: dict):
    try:
        req = ValidatePhoneRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = checkers.check_phone(req.phone, req.default_country)
    except checkers.CheckError as e:
        return None, bad_request([{"field": "phone", "message": str(e)}],
                                 "check_failed")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/validate/phone")
def api_validate_phone(req: ValidatePhoneRequest):
    body, err = run_validate_phone(req.model_dump())
    return err if err else body


class ValidateEmailRequest(BaseModel):
    email: str


def run_validate_email(args: dict):
    try:
        req = ValidateEmailRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = checkers.check_email(req.email)
    except checkers.CheckError as e:
        return None, bad_request([{"field": "email", "message": str(e)}],
                                 "check_failed")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/validate/email")
def api_validate_email(req: ValidateEmailRequest):
    body, err = run_validate_email(req.model_dump())
    return err if err else body


class ValidateUrlRequest(BaseModel):
    url: str


def run_validate_url(args: dict):
    try:
        req = ValidateUrlRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = checkers.check_url(req.url)
    except checkers.CheckError as e:
        return None, bad_request([{"field": "url", "message": str(e)}],
                                 "check_failed")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/validate/url")
def api_validate_url(req: ValidateUrlRequest):
    body, err = run_validate_url(req.model_dump())
    return err if err else body


class ColorCheckRequest(BaseModel):
    color: str
    against: Optional[str] = None


def run_color_check(args: dict):
    try:
        req = ColorCheckRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = checkers.color_check(req.color, req.against)
    except checkers.CheckError as e:
        return None, bad_request([{"field": "color", "message": str(e),
                                   "expected": "#rgb, #rrggbb or "
                                               "rgb(r,g,b)"}],
                                 "check_failed")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/color/check")
def api_color_check(req: ColorCheckRequest):
    body, err = run_color_check(req.model_dump())
    return err if err else body


# --------------------------------------------- bundle 7.1: text tools

class TextCountRequest(BaseModel):
    text: str


def run_text_count(args: dict):
    try:
        req = TextCountRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = context.text_count(req.text)
    except context.ContextError as e:
        return None, bad_request([{"field": "text", "message": str(e)}])
    return out, None


@app.post("/api/v1/text/count")
def api_text_count(req: TextCountRequest):
    body, err = run_text_count(req.model_dump())
    return err if err else body


class SortNaturalRequest(BaseModel):
    items: List[Any]
    reverse: bool = False


def run_sort_natural(args: dict):
    try:
        req = SortNaturalRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = context.sort_natural(req.items, req.reverse)
    except context.ContextError as e:
        return None, bad_request([{"field": "items", "message": str(e)}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/sort/natural")
def api_sort_natural(req: SortNaturalRequest):
    body, err = run_sort_natural(req.model_dump())
    return err if err else body


class TextCaseRequest(BaseModel):
    text: str
    op: Literal["snake", "kebab", "camel", "pascal", "title", "upper",
                "lower", "sentence"] = "snake"


def run_text_case(args: dict):
    try:
        req = TextCaseRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = context.text_case(req.text, req.op)
    except context.ContextError as e:
        return None, bad_request([{"field": "text", "message": str(e)}])
    return out, None


@app.post("/api/v1/text/case")
def api_text_case(req: TextCaseRequest):
    body, err = run_text_case(req.model_dump())
    return err if err else body


class TextTruncateRequest(BaseModel):
    text: str
    max: int
    unit: Literal["chars", "words", "sentences"] = "chars"
    strategy: Literal["cut", "word", "sentence"] = "word"
    ellipsis: str = "…"


def run_text_truncate(args: dict):
    try:
        req = TextTruncateRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = context.text_truncate(req.text, req.max, req.unit,
                                    req.strategy, req.ellipsis)
    except context.ContextError as e:
        return None, bad_request([{"field": "text", "message": str(e)}])
    out["unit"] = req.unit
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/text/truncate")
def api_text_truncate(req: TextTruncateRequest):
    body, err = run_text_truncate(req.model_dump())
    return err if err else body


class RegexTestRequest(BaseModel):
    pattern: str
    text: str
    flags: str = "u"
    mode: Literal["test", "findall", "groups", "replace"] = "test"
    template: Optional[str] = None
    count: int = 0


def run_regex_test(args: dict):
    try:
        req = RegexTestRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = context.regex_test(req.pattern, req.text, req.flags,
                                 req.mode, req.template, req.count)
    except context.ContextError as e:
        return None, bad_request([{"field": "pattern", "message": str(e),
                                   "expected": "python regex, flags in "
                                               "imsxua, text <= 64 KB"}],
                                 "regex_failed")
    out["mode"] = req.mode
    return out, None


@app.post("/api/v1/regex/test")
def api_regex_test(req: RegexTestRequest):
    body, err = run_regex_test(req.model_dump())
    return err if err else body


# ------------------------------------------------ bundle 7.2: chunking

class TextChunkRequest(BaseModel):
    text: str
    budget: int = 512
    overlap: int = 0
    encoding: Literal["cl100k_base", "o200k_base", "o250k_base",
                      "p50k_base", "gpt2"] = "cl100k_base"
    unit: Literal["sentence", "paragraph"] = "sentence"


def run_text_chunk(args: dict):
    try:
        req = TextChunkRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = context.text_chunk(req.text, req.budget, req.overlap,
                                 req.encoding, req.unit)
    except context.ContextError as e:
        return None, bad_request([{"field": "budget", "message": str(e)}],
                                 "chunk_failed")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/text/chunk")
def api_text_chunk(req: TextChunkRequest):
    body, err = run_text_chunk(req.model_dump())
    return err if err else body


class MdRenderRequest(BaseModel):
    markdown: str
    heading_ids: bool = False
    document: bool = False
    title: Optional[str] = None


def run_md_render(args: dict):
    try:
        req = MdRenderRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        html = mdrender.md_render(req.markdown, req.heading_ids)
    except mdrender.RenderError as e:
        return None, bad_request([{"field": "markdown", "message": str(e)}],
                                 "render_failed")
    if req.document:
        html = mdrender.md_document(html, title=req.title)
    out = {"html": html, "sha256": _sha_text(html)}
    if req.document:
        out["printable"] = ("open in a browser, Ctrl-P (or Cmd-P) -> "
                            "Save as PDF; A4 print CSS baked in")
    return out, None


@app.post("/api/v1/md/render")
def api_md_render(req: MdRenderRequest):
    body, err = run_md_render(req.model_dump())
    return err if err else body


# --------------------------------------------- bundle 7.3: scraping

class HtmlTextRequest(BaseModel):
    html: str
    keep_links: bool = False
    max_bytes: int = 1048576


def run_html_text(args: dict):
    try:
        req = HtmlTextRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = htmltext.html_text(req.html, req.keep_links, req.max_bytes)
    except htmltext.ExtractError as e:
        return None, bad_request([{"field": "html", "message": str(e)}],
                                 "extract_failed")
    out["sha256"] = _sha_text(out["text"])
    return out, None


@app.post("/api/v1/html/text")
def api_html_text(req: HtmlTextRequest):
    body, err = run_html_text(req.model_dump())
    return err if err else body

# --------------------------------------------- bundle 8: palette (free)

class ColorPaletteRequest(BaseModel):
    color: str
    scheme: Literal["complementary", "analogous", "triad", "tetradic",
                    "split"] = "complementary"
    steps: int = 5
    neutral: bool = False


def run_color_palette(args: dict):
    try:
        req = ColorPaletteRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    try:
        out = checkers.color_palette(req.color, req.scheme, req.steps,
                                     req.neutral)
    except checkers.CheckError as e:
        return None, bad_request([{"field": "color", "message": str(e)}],
                                 "check_failed")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/color/palette")
def api_color_palette(req: ColorPaletteRequest):
    body, err = run_color_palette(req.model_dump())
    return err if err else body


# ------------------------------------------- bundle 13: self-check (free)

class CheckConstraintsRequest(BaseModel):
    text: str
    constraints: Dict[str, Any]
    case: Literal["fold", "exact"] = "fold"


class CheckRefsRequest(BaseModel):
    text: str
    sources: List[str]
    kinds: Optional[List[str]] = None
    case: Literal["fold", "exact"] = "fold"


def run_check_constraints(args: dict):
    try:
        out = check.check_constraints(args["text"], args["constraints"],
                                      args.get("case") or "fold")
    except check.CheckError as e:
        return None, bad_request(
            [{"field": "constraints", "message": str(e)}], "check_failed")
    out["sha256"] = canon(out)
    return out, None


def run_check_refs(args: dict):
    try:
        out = check.check_refs(args["text"], args["sources"],
                               args.get("kinds"), args.get("case") or "fold")
    except check.CheckError as e:
        return None, bad_request(
            [{"field": "sources", "message": str(e)}], "check_failed")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/check/constraints")
def api_check_constraints(req: CheckConstraintsRequest):
    body, err = run_check_constraints(req.model_dump())
    return err if err else body


@app.post("/api/v1/check/refs")
def api_check_refs(req: CheckRefsRequest):
    body, err = run_check_refs(req.model_dump())
    return err if err else body


# -------------------------------------- bundle 14: extraction (capped)

class ExtractFactsRequest(BaseModel):
    text: str
    context_chars: int = 30
    group: Optional[Literal["kind"]] = None


class TextSelectRequest(BaseModel):
    chunks: List[str]
    query: str
    k: int = 3
    unit: Literal["word", "char"] = "word"


def run_extract_facts(args: dict):
    try:
        out = extract.extract_facts(args["text"], args["context_chars"],
                                    args.get("group"))
    except extract.ExtractError as e:
        return None, bad_request(
            [{"field": "text", "message": str(e)}], "extract_failed")
    out["sha256"] = canon(out)
    return out, None


def run_text_select(args: dict):
    try:
        out = extract.select_chunks(args["chunks"], args["query"],
                                    args["k"], args["unit"])
    except extract.ExtractError as e:
        return None, bad_request(
            [{"field": "chunks", "message": str(e)}], "select_failed")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/extract/facts")
def api_extract_facts(req: ExtractFactsRequest):
    body, err = run_extract_facts(req.model_dump())
    return err if err else body


@app.post("/api/v1/text/select")
def api_text_select(req: TextSelectRequest):
    body, err = run_text_select(req.model_dump())
    return err if err else body


# ----------------------------------------- bundle 15: logic (free)

class LogicRulesRequest(BaseModel):
    facts: Dict[str, Any]
    rules: List[Dict[str, Any]]


class SortMultiRequest(BaseModel):
    rows: List[Dict[str, Any]]
    by: List[Dict[str, Any]]


class JsonQueryRequest(BaseModel):
    data: Any
    path: str


def run_logic_rules(args: dict):
    try:
        out = rules_mod.logic_rules(args["facts"], args["rules"])
    except rules_mod.RulesError as e:
        return None, bad_request(
            [{"field": "rules", "message": str(e)}], "rule_failed")
    out["sha256"] = canon(out)
    return out, None


def run_sort_multi(args: dict):
    try:
        out = rules_mod.sort_multi(args["rows"], args["by"])
    except rules_mod.RulesError as e:
        return None, bad_request(
            [{"field": "by", "message": str(e)}], "sort_failed")
    out["sha256"] = canon(out)
    return out, None


def run_json_query(args: dict):
    try:
        out = rules_mod.json_query(args["data"], args["path"])
    except rules_mod.RulesError as e:
        return None, bad_request(
            [{"field": "path", "message": str(e)}], "query_failed")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/logic/rules")
def api_logic_rules(req: LogicRulesRequest):
    body, err = run_logic_rules(req.model_dump())
    return err if err else body


@app.post("/api/v1/sort/multi")
def api_sort_multi(req: SortMultiRequest):
    body, err = run_sort_multi(req.model_dump())
    return err if err else body


@app.post("/api/v1/json/query")
def api_json_query(req: JsonQueryRequest):
    body, err = run_json_query(req.model_dump())
    return err if err else body


# ------------------------------------------- bundle 16: volume & recipes

class BatchRequest(BaseModel):
    tool: str
    payloads: List[Dict[str, Any]]
    stop_on_error: bool = False


RECIPE_FORBIDDEN = {"batch", "pipeline"}


def run_batch(args: dict):
    tool = args.get("tool")
    payloads = args.get("payloads")
    if not isinstance(tool, str) or tool not in TOOL_RUN:
        names = sorted(set(TOOL_RUN) - {"recipe_clean_table",
                                        "recipe_clean_json",
                                        "recipe_data_trio"})
        return None, bad_request(
            [{"field": "tool", "message": "unknown tool %r; expected one "
              "of: %s" % (tool, ", ".join(names))}],
            "invalid_input")
    if tool in RECIPE_FORBIDDEN:
        return None, bad_request(
            [{"field": "tool", "message": "batch of batch/pipeline is "
              "forbidden (no recursion)"}], "invalid_input")
    if (not isinstance(payloads, list) or not payloads
            or len(payloads) > 100):
        return None, bad_request(
            [{"field": "payloads",
              "message": "payloads must be an array of 1..100 objects"}],
            "invalid_input")
    stop_on_error = bool(args.get("stop_on_error"))
    runner = TOOL_RUN[tool]
    results = []
    ok = fail = 0
    for i, one in enumerate(payloads):
        if not isinstance(one, dict):
            return None, bad_request(
                [{"field": "payloads[%d]" % i,
                  "message": "each payload must be an object"}],
                "invalid_input")
        out, err = runner(one)
        if err is None:
            ok += 1
            results.append({"index": i, "ok": True, "result": out})
        else:
            fail += 1
            detail = err.body if hasattr(err, "body") else None
            try:
                parsed = json.loads(detail.decode()) if isinstance(
                    detail, bytes) else (detail or err.status_code)
            except Exception:
                parsed = str(getattr(err, "status_code", err))
            results.append({"index": i, "ok": False, "error": parsed})
            if stop_on_error:
                break
    out = {"tool": tool, "total": len(payloads), "succeeded": ok,
           "failed": fail, "stopped_early": len(results) < len(payloads),
           "results": results}
    out["sha256"] = canon(out)
    return out, None


class RecipeInvoiceRequest(BaseModel):
    line_items: List[Dict[str, Any]]
    currency: str = "EUR"
    vat_percent: str = "0"
    date: str = ""
    due_days: int = 0
    words_lang: Literal["en", "fr", "pt"] = "fr"


def run_recipe_invoice(args: dict):
    from decimal import Decimal, ROUND_HALF_EVEN
    items = args.get("line_items")
    if (not isinstance(items, list) or not items
            or len(items) > 200):
        return None, bad_request(
            [{"field": "line_items",
              "message": "line_items must be an array of 1..200 "
                         "{desc, qty, unit_price}"}], "invalid_input")
    rows, sub = [], Decimal(0)
    for i, it in enumerate(items):
        if not isinstance(it, dict) or "desc" not in it:
            return None, bad_request(
                [{"field": "line_items[%d]" % i,
                  "message": "each item needs desc, qty, unit_price"}],
                "invalid_input")
        try:
            qty = Decimal(str(it.get("qty", 1)))
            price = Decimal(str(it.get("unit_price", 0)))
        except Exception:
            return None, bad_request(
                [{"field": "line_items[%d]" % i,
                  "message": "qty/unit_price must be numeric strings or "
                             "numbers"}], "invalid_input")
        line = (qty * price).quantize(Decimal("0.01"),
                                       rounding=ROUND_HALF_EVEN)
        sub += line
        rows.append({"desc": str(it["desc"]), "qty": str(qty),
                     "unit_price": str(price), "line_total": str(line)})
    try:
        vat_p = Decimal(str(args.get("vat_percent", "0")))
    except Exception:
        return None, bad_request(
            [{"field": "vat_percent", "message": "numeric string"}],
            "invalid_input")
    vat = (sub * vat_p / Decimal(100)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    total = sub + vat
    spelled, err = run_number_spell({"value": str(total),
                                     "lang": args.get("words_lang", "fr"),
                                     "currency": args.get("currency"),
                                     "cents": True, "capital": False})
    if err is not None:
        return None, err
    due = None
    if args.get("date"):
        due_days = int(args.get("due_days") or 0)
        try:
            calc = dates.date_calc(
                args["date"], "add",
                {"duration": "%dd" % max(due_days, 0)})
        except dates.DateError as e:
            return None, bad_request(
                [{"field": "date", "message": str(e)}], "invalid_input")
        due = calc.get("result")
    out = {"currency": args.get("currency", "EUR"), "items": rows,
           "subtotal": str(sub), "vat_percent": str(vat_p),
           "vat": str(vat), "total": str(total),
           "total_words": spelled.get("words"),
           "date": args.get("date") or None,
           "due": due}
    out["sha256"] = canon(out)
    return out, None


class RecipeScheduleRequest(BaseModel):
    cron: str
    start: str
    timezone: str = "UTC"
    count: int = 6
    duration_minutes: int = 60
    summary: str = "Appointment"


def run_recipe_schedule(args: dict):
    try:
        runs = dates.cron_next(args["cron"], int(args.get("count", 6)),
                               args.get("start"), args.get("timezone",
                                                           "UTC"))
    except dates.DateError as e:
        return None, bad_request(
            [{"field": "cron", "message": str(e)}], "invalid_input")
    events = [{"summary": args.get("summary", "Appointment"),
               "start": t["iso"],
               "duration": "PT%dM" % int(args.get("duration_minutes", 60)),
               "tz": args.get("timezone", "UTC")}
              for t in runs["runs"]]
    try:
        ics_text = dates.ics_generate(events)
    except dates.DateError as e:
        return None, bad_request(
            [{"field": "events", "message": str(e)}], "invalid_input")
    out = {"expression": runs["expression"], "tz": runs["tz"],
           "occurrences": events, "ics": ics_text}
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/batch")
def api_batch(req: BatchRequest):
    body, err = run_batch(req.model_dump())
    return err if err else body


@app.post("/api/v1/recipe/invoice")
def api_recipe_invoice(req: RecipeInvoiceRequest):
    body, err = run_recipe_invoice(req.model_dump())
    return err if err else body


@app.post("/api/v1/recipe/schedule")
def api_recipe_schedule(req: RecipeScheduleRequest):
    body, err = run_recipe_schedule(req.model_dump())
    return err if err else body


class FicheRequest(BaseModel):
    slots: Optional[dict] = None


def _run_fiche(name: str, args: dict):
    try:
        out = ficheskit.run_fiche(name, args.get("slots") or {})
    except ficheskit.Slot as e:
        return None, bad_request([{"field": e.field,
                                   "message": e.message,
                                   "expected": e.expected}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/fiche/shop-reste")
def api_fiche_shop_reste(req: FicheRequest):
    body, err = _run_fiche("shop_reste", req.model_dump())
    return err if err else body


@app.post("/api/v1/fiche/partage-reste")
def api_fiche_partage_reste(req: FicheRequest):
    body, err = _run_fiche("partage_reste", req.model_dump())
    return err if err else body


@app.post("/api/v1/fiche/soldes2")
def api_fiche_soldes2(req: FicheRequest):
    body, err = _run_fiche("soldes2", req.model_dump())
    return err if err else body


# ---------------- bundle 54 : le routeur-annuaire (docs/ROUTER-SPEC.md)
class RouterTextRequest(BaseModel):
    texte: str


def _router_out(out: dict):
    out["sha256"] = canon(out)
    return out


@app.post("/api/v1/router/plan")
def api_router_plan(req: RouterTextRequest):
    """Symptôme → prescription mesurée (fiche, créneaux, transport,
    preuve). Ne calcule rien, ne devine rien."""
    d = annuaire.load()
    entree, _ = annuaire.trouver(req.texte, d)
    out = {"match": entree is not None,
           "regles_transport": [r["loi"] for r in d["regles_transport"]]}
    if entree:
        p = entree["prescription"]
        out.update(entree=entree["id"], prescription=p,
                   preuve=list(entree["preuve"]),
                   prompt_lm=routeur.prompt_routee(p, req.texte))
    else:
        out["note"] = ("aucune entrée : le routeur ne devine pas. Une "
                       "entrée nouvelle exige une ligne de bench (R4). "
                       "Outil unitaire : /api/v1/intent/card.")
    return _router_out(out)


@app.post("/api/v1/router/apply")
def api_router_apply(req: RouterTextRequest):
    """L'annuaire APPELLE et APPLIQUE : grammaire fermée matchée →
    créneaux extraits verbatim → la fiche tourne, zéro LM. Sinon :
    refus nommé + prompt à remplir — jamais un nombre inventé."""
    d = annuaire.load()
    entree, _ = annuaire.trouver(req.texte, d)
    if entree is None:
        return _router_out({"applied": False, "match": False, "note":
                            "pas d'entrée d'annuaire : aucun nombre "
                            "sera produit. Outil unitaire : "
                            "/api/v1/intent/card."})
    p = entree["prescription"]
    slots, manques, ambigus = routeur.extraire(p["fiche"], req.texte)
    if manques or ambigus:
        return _router_out({
            "applied": False, "match": True, "entree": entree["id"],
            "creneaux_manquants": manques, "ambigus": ambigus,
            "prescription": p,
            "note": "grammaire fermée : rien n'est deviné. Remplis les "
                    "créneaux avec le prompt_lm (recopie verbatim), "
                    "puis POSTe la fiche.",
            "prompt_lm": routeur.prompt_routee(p, req.texte)})
    body, err = _run_fiche(p["fiche"].replace("-", "_"), {"slots": slots})
    if err is not None:
        return err
    out = {"applied": True, "entree": entree["id"], "creneaux": slots,
           "cible": p["cible"],
           "reponse": (body.get("answer") or {}).get(p["cible"]),
           "fiche": body}
    return _router_out(out)


class RecipeFactsRequest(BaseModel):
    text: str
    kinds: Optional[List[str]] = None
    total: bool = True


def run_recipe_facts(args: dict):
    text = args.get("text")
    if not isinstance(text, str) or not text.strip():
        return None, bad_request([{"field": "text",
                                   "message": "required, non-empty string"}])
    if len(text) > 1_000_000:
        return None, bad_request([{"field": "text",
                                   "message": "max 1000000 bytes"}])
    kinds = args.get("kinds")
    if kinds is not None and (not isinstance(kinds, list)
                              or not all(isinstance(k, str) for k in kinds)):
        return None, bad_request([{"field": "kinds",
                                   "message": "list of kind names"}])
    try:
        out = extract.recipe_facts(text, kinds=kinds,
                                   total=bool(args.get("total", True)))
    except extract.ExtractError as e:
        return None, bad_request([{"field": "text", "message": str(e)}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/recipe/facts")
def api_recipe_facts(req: RecipeFactsRequest):
    body, err = run_recipe_facts(req.model_dump())
    return err if err else body


class IntentCardRequest(BaseModel):
    utterance: str


def _intent_schemas():
    return {t["name"]: (t.get("inputSchema") or {})
            for t in MCP_TOOLS + RECIPE_SPECS}


def run_intent_card(args: dict):
    utt = args.get("utterance")
    if not isinstance(utt, str) or not utt.strip():
        return None, bad_request([{"field": "utterance",
                                   "message": "required, non-empty string"}])
    if len(utt) > 4000:
        return None, bad_request([{"field": "utterance",
                                   "message": "max 4000 bytes"}])
    try:
        out = intake.build_card(utt, _intent_schemas(), routing.route)
    except ValueError as e:
        return None, bad_request([{"field": "utterance",
                                   "message": str(e)}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/intent/card")
def api_intent_card(req: IntentCardRequest):
    body, err = run_intent_card(req.model_dump())
    return err if err else body


class CheckRedlinesRequest(BaseModel):
    text: str
    rules: Dict[str, Any]


def run_check_redlines(args: dict):
    try:
        out = redlines.check_redlines(args.get("text"), args.get("rules"))
    except ValueError as e:
        return None, bad_request([{"field": "rules",
                                   "message": str(e)}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/check/redlines")
def api_check_redlines(req: CheckRedlinesRequest):
    body, err = run_check_redlines(req.model_dump())
    return err if err else body


class CheckAgreementRequest(BaseModel):
    payloads: list


def run_check_agreement(args: dict):
    payloads = args.get("payloads")
    try:
        out = verdict.check_agreement(payloads)
    except ValueError as e:
        return None, bad_request([{"field": "payloads",
                                   "message": str(e)}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/check/agreement")
def api_check_agreement(req: CheckAgreementRequest):
    body, err = run_check_agreement(req.model_dump())
    return err if err else body


class IntentCheckRequest(BaseModel):
    tool: str
    args: Dict[str, Any] = {}


def routing_tool_path(name):
    for t in routing.TABLE:
        if t[0] == name:
            return t[1]
    return None


def run_intent_check(args: dict):
    tool = args.get("tool")
    if not isinstance(tool, str) or not tool.strip():
        return None, bad_request([{"field": "tool",
                                   "message": "required, non-empty string"}])
    payload = args.get("args")
    if not isinstance(payload, dict):
        return None, bad_request([{"field": "args",
                                   "message": "object of field: value"}])
    ok, problems = intake.check_filled(tool, payload, _intent_schemas())
    out = {"tool": tool, "ok": ok, "problems": problems,
           "next": (("POST " + routing_tool_path(tool)) if ok
                    and routing_tool_path(tool) else
                    "pick a tool from /agent/manifest") if ok
                   else "ask the human for: "
                        + ", ".join(p["field"] for p in problems)}
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/intent/check")
def api_intent_check(req: IntentCheckRequest):
    body, err = run_intent_check(req.model_dump())
    return err if err else body


# ----------------------------------------- bundle 17: micro (free)

class TextDecodeRequest(BaseModel):
    text: str
    target: Literal["utf-8"] = "utf-8"


class NumHumanRequest(BaseModel):
    value: Any
    kind: Literal["duration", "bytes", "roman", "ordinal"]
    style: Optional[Literal["decimal", "binary"]] = None


class TextEscapeRequest(BaseModel):
    value: str
    dialects: List[str]


class TextNormalizeRequest(BaseModel):
    text: str
    form: Literal["NFC", "NFD", "NFKC", "NFKD"] = "NFC"
    strip_accents: bool = False
    casefold: bool = False
    collapse_ws: bool = False
    fullwidth: bool = False


def _micro(err):
    return bad_request([{"field": "input", "message": str(err)}],
                       "invalid_input")


def run_text_decode(args: dict):
    try:
        out = micro.text_decode(args["text"], args.get("target") or "utf-8")
    except micro.MicroError as e:
        return None, _micro(e)
    out["sha256"] = canon(out)
    return out, None


def run_num_human(args: dict):
    try:
        out = micro.num_human(args["value"], args["kind"], args.get("style"))
    except micro.MicroError as e:
        return None, _micro(e)
    out["sha256"] = canon(out)
    return out, None


def run_text_escape(args: dict):
    try:
        out = micro.text_escape(args["value"], args["dialects"])
    except micro.MicroError as e:
        return None, _micro(e)
    out["sha256"] = canon(out)
    return out, None


def run_text_normalize(args: dict):
    try:
        out = micro.text_normalize(
            args["text"], args.get("form", "NFC"),
            args.get("strip_accents", False), args.get("casefold", False),
            args.get("collapse_ws", False), args.get("fullwidth", False))
    except micro.MicroError as e:
        return None, _micro(e)
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/text/decode")
def api_text_decode(req: TextDecodeRequest):
    body, err = run_text_decode(req.model_dump())
    return err if err else body


@app.post("/api/v1/num/human")
def api_num_human(req: NumHumanRequest):
    body, err = run_num_human(req.model_dump())
    return err if err else body


@app.post("/api/v1/text/escape")
def api_text_escape(req: TextEscapeRequest):
    body, err = run_text_escape(req.model_dump())
    return err if err else body


@app.post("/api/v1/text/normalize")
def api_text_normalize(req: TextNormalizeRequest):
    body, err = run_text_normalize(req.model_dump())
    return err if err else body


# ------------------------------------------- bundle 18: EVM (free)

class EthAddressRequest(BaseModel):
    address: str
    allowlist: Optional[List[str]] = None


class EthSelectorRequest(BaseModel):
    signature: str


class EthUnitsRequest(BaseModel):
    value: Any
    unit: Literal["wei", "kwei", "mwei", "gwei", "szabo", "finney",
                  "ether"]


def _eth_err(e, field):
    return bad_request([{"field": field, "message": str(e)}],
                       "invalid_input")


def run_eth_address(args: dict):
    try:
        out = eth_mod.eth_address(args["address"], args.get("allowlist"))
    except eth_mod.EthError as e:
        return None, _eth_err(e, "address")
    out["sha256"] = canon(out)
    return out, None


def run_eth_selector(args: dict):
    try:
        out = eth_mod.eth_selector(args["signature"])
    except eth_mod.EthError as e:
        return None, _eth_err(e, "signature")
    out["sha256"] = canon(out)
    return out, None


def run_eth_units(args: dict):
    try:
        out = eth_mod.eth_units(args["value"], args["unit"])
    except eth_mod.EthError as e:
        return None, _eth_err(e, "value")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/eth/address")
def api_eth_address(req: EthAddressRequest):
    body, err = run_eth_address(req.model_dump())
    return err if err else body


@app.post("/api/v1/eth/selector")
def api_eth_selector(req: EthSelectorRequest):
    body, err = run_eth_selector(req.model_dump())
    return err if err else body


@app.post("/api/v1/eth/units")
def api_eth_units(req: EthUnitsRequest):
    body, err = run_eth_units(req.model_dump())
    return err if err else body


# --------------------------------- bundle 18 lot 2: calldata & proofs

class AbiEncodeRequest(BaseModel):
    types: List[str]
    values: List[Any]


class AbiDecodeRequest(BaseModel):
    types: List[str]
    data: str


class Eip712Request(BaseModel):
    types: Dict[str, Any]
    primaryType: str
    domain: Dict[str, Any]
    message: Dict[str, Any]


class ReceiptMatchRequest(BaseModel):
    logs: List[Dict[str, Any]]
    expect: Dict[str, Any]


def run_eth_abi_encode(args: dict):
    try:
        calldata = ethabi.abi_encode(args["types"], args["values"])
    except ethabi.EthError as e:
        return None, bad_request(
            [{"field": "types", "message": str(e)}], "invalid_input")
    res = {"calldata": calldata}
    res["sha256"] = canon(res)
    return res, None


def run_eth_abi_decode(args: dict):
    try:
        vals = ethabi.abi_decode(args["types"], args["data"])
    except (ethabi.EthError, ValueError) as e:
        return None, bad_request(
            [{"field": "data", "message": str(e)}], "invalid_input")
    res = {"types": args["types"], "values": vals}
    res["sha256"] = canon(res)
    return res, None


def run_eth_eip712(args: dict):
    try:
        res = ethabi.eip712_digest(args)
    except (ethabi.EthError, ValueError) as e:
        return None, bad_request(
            [{"field": "types", "message": str(e)}], "invalid_input")
    res["sha256"] = canon(res)
    return res, None


def run_eth_receipt(args: dict):
    try:
        res = ethabi.receipt_match(args["logs"], args["expect"])
    except (ethabi.EthError, ValueError) as e:
        return None, bad_request(
            [{"field": "expect", "message": str(e)}], "invalid_input")
    res["sha256"] = canon(res)
    return res, None


@app.post("/api/v1/eth/abi-encode")
def api_eth_abi_encode(req: AbiEncodeRequest):
    body, err = run_eth_abi_encode(req.model_dump())
    return err if err else body


@app.post("/api/v1/eth/abi-decode")
def api_eth_abi_decode(req: AbiDecodeRequest):
    body, err = run_eth_abi_decode(req.model_dump())
    return err if err else body


@app.post("/api/v1/eth/eip712")
def api_eth_eip712(req: Eip712Request):
    body, err = run_eth_eip712(req.model_dump())
    return err if err else body


@app.post("/api/v1/eth/receipt")
def api_eth_receipt(req: ReceiptMatchRequest):
    body, err = run_eth_receipt(req.model_dump())
    return err if err else body


# ------------------------------------- bundle 0: agent navigation (free)

@app.get("/agent/manifest", response_class=PlainTextResponse)
def agent_manifest():
    return routing.manifest_text(app.version)


RECIPE_SPECS = [
    {"name": "recipe_clean_table",
     "description": "One call: dirty CSV -> fix -> types -> dedupe -> "
                    "typed unique rows (GET /api/v1/recipes). Free.",
     "inputSchema": {"type": "object", "required": ["csv"],
                     "properties": {"csv": {"type": "string"}}}},
    {"name": "recipe_clean_json",
     "description": "One call: broken JSON -> repair -> canonical text. "
                    "Free.",
     "inputSchema": {"type": "object", "required": ["text"],
                     "properties": {"text": {"type": "string"},
                                    "style": {"type": "string",
                                              "enum": ["minified",
                                                       "pretty"],
                                              "default": "minified"}}}},
    {"name": "recipe_invoice",
     "description": "One call: line items + VAT -> exact subtotal/vat/total "
                    "+ amount in words (FR/EN/PT) + due date. Free.",
     "inputSchema": {"type": "object", "required": ["line_items"],
                     "properties": {
                         "line_items": {"type": "array"},
                         "currency": {"type": "string", "default": "EUR"},
                         "vat_percent": {"type": "string", "default": "0"},
                         "date": {"type": "string"},
                         "due_days": {"type": "integer", "default": 0},
                         "words_lang": {"type": "string",
                                        "enum": ["en", "fr", "pt"],
                                        "default": "fr"}}}},
    {"name": "recipe_facts",
     "description": "One call: free text -> normalized fact inventory "
                    "(money/percent/date/number/url/email/uuid/iban, "
                    "canonicalized, deduped, sorted) + money total. The "
                    "model only CHOOSES this recipe; nothing is "
                    "retranscribed. Free.",
     "inputSchema": {"type": "object", "required": ["text"],
                     "properties": {
                         "text": {"type": "string"},
                         "kinds": {"type": "array", "items":
                                   {"type": "string"}},
                         "total": {"type": "boolean",
                                   "default": True}}}},
    {"name": "recipe_shop_reste",
     "description": "The 'of the REST' chain in ONE call: total, "
                    "sold_morning, pct_afternoon slots in -> the three "
                    "step trace and `remaining` out, exact Fractions. "
                    "Naked models score 0/28 on this shape (bench v15, "
                    "retries included) — not because of arithmetic but "
                    "because the decomposition IS the job. You copy "
                    "numbers; the chain is ours.",
     "inputSchema": {"type": "object", "properties": {"slots": {
         "type": "object", "properties": {
             "total": {"type": "string"},
             "sold_morning": {"type": "string"},
             "pct_afternoon": {"type": "string"}}}},
         "required": ["slots"]}},
    {"name": "recipe_partage_reste",
     "description": "Share of a share: total, first_part, "
                    "second_of_rest (fractions like 2/5 accepted) -> "
                    "second_share + leftover, with the trace. THE word "
                    "that zeroes free models is 'of the rest' — here "
                    "it is a slot name, nothing to re-derive.",
     "inputSchema": {"type": "object", "properties": {"slots": {
         "type": "object", "properties": {
             "total": {"type": "string"},
             "first_part": {"type": "string"},
             "second_of_rest": {"type": "string"}}}},
         "required": ["slots"]}},
    {"name": "recipe_soldes2",
     "description": "Two discounts, final price + the naive-sum lie "
                    "quantified — the minimal kernel of a discount "
                    "chain; N-step chains belong to /api/v1/money/"
                    "discount (the fiche points there, never "
                    "duplicates it).",
     "inputSchema": {"type": "object", "properties": {"slots": {
         "type": "object", "properties": {
             "price": {"type": "string"},
             "pct1": {"type": "string"},
             "pct2": {"type": "string"}}}},
         "required": ["slots"]}},
    {"name": "recipe_schedule",
     "description": "One call: cron + start + count -> occurrences + ready "
                    "ICS. Appointments without arithmetic. Free.",
     "inputSchema": {"type": "object", "required": ["cron", "start"],
                     "properties": {
                         "cron": {"type": "string"},
                         "start": {"type": "string"},
                         "timezone": {"type": "string", "default": "UTC"},
                         "count": {"type": "integer", "default": 6},
                         "duration_minutes": {"type": "integer",
                                              "default": 60},
                         "summary": {"type": "string"}}}},
    {"name": "recipe_data_trio",
     "description": "One call: dirty csv + broken json + url list -> "
                    "final YAML {rows, totals, urls}. The rag-ingestion "
                    "trio. Free. Also composable as a pipeline step.",
     "inputSchema": {"type": "object",
                     "required": ["csv", "json_text", "urls"],
                     "properties": {"csv": {"type": "string"},
                                    "json_text": {"type": "string"},
                                    "urls": {"type": "array",
                                             "items": {"type":
                                                       "string"}}}}},
]
def all_specs():
    # MCP_TOOLS is the literal list further down the module; recipes
    # join it so /tools/*.json and /SKILL-*.md see every TABLE name
    return MCP_TOOLS + RECIPE_SPECS


_EX_PATH = Path(__file__).parent / "static" / "agent_examples.json"
try:
    _EXAMPLES = json.loads(_EX_PATH.read_text(encoding="utf-8")) \
        .get("examples", {})
except (OSError, ValueError):
    _EXAMPLES = {}


@app.get("/tools/{tool}.json")
def api_tool_spec(tool: str):
    entry = next((t for t in all_specs() if t["name"] == tool), None)
    if entry is None:
        return JSONResponse(
            status_code=404,
            content={"error": "unknown_tool",
                     "field": "tool",
                     "expected": "one of the %d tool names "
                                 "(GET /agent/manifest)"
                                 % len(all_specs()),
                     "did_you_mean": sorted(difflib.get_close_matches(
                         tool, [t["name"] for t in all_specs()], n=5,
                         cutoff=0.0))})
    spec = routing.tool_spec(tool, entry)
    path = spec.get("path") or next(
        (t[1] for t in routing.TABLE if t[0] == tool), "")
    ex = _EXAMPLES.get(path)
    say = sayings.SAY.get(path)
    if path and (ex or say):
        spec["try"] = {"say": say or spec.get("purpose", ""),
                       "request": {"method": "POST", "path": path,
                                   "body": ex["body"] if ex else None},
                       "response": ex["response"] if ex else None,
                       "status": ex["status"] if ex else None}
    return spec


@app.get("/SKILL-MINI.md", response_class=PlainTextResponse)
def skill_mini_md():
    """The one-page skill: written so a 0.5B model can follow it
    literally. ~650 tokens, no hidden rules, byte-stable."""
    return (Path(__file__).parent / "SKILL-MINI.md").read_text()


@app.get("/SKILL-{pack}.md", response_class=PlainTextResponse)
def api_skill_pack(pack: str):
    text = routing.pack_markdown(pack, all_specs())
    if text is None:
        return JSONResponse(
            status_code=404,
            content={"error": "unknown_pack",
                     "field": "pack",
                     "expected": ", ".join(routing.PACKS)})
    return text



# ------------------------------ bundle 44/45: formula catalogue + miroir

class FormulaRequest(BaseModel):
    formula: Optional[str] = None
    args: Optional[dict] = None


def run_formula_endpoint(args: dict):
    name = args.get("formula") or args.get("name")
    if not name:
        return None, bad_request([{
            "field": "formula", "message": "missing formula",
            "expected": "a catalog name — GET /api/v1/formula lists "
                        "all %d with sources and args"
                        % len(formulakit.CATALOG)}])
    try:
        out = formulakit.run_formula(name, args.get("args") or {})
    except KeyError as e:
        rec = formulakit.CATALOG.get(name)
        return None, bad_request([{
            "field": "formula|args",
            "message": "formula %s: %s" % (name, str(e).strip("'")),
            "expected": (rec["args"] if rec else
                         "one of: " + "|".join(sorted(formulakit.CATALOG)))
        }])
    out["sha256"] = canon(out)
    return out, None


@app.get("/api/v1/formula")
def api_formula_catalog_get():
    out = formulakit.formula_index()
    out["sha256"] = canon(out)
    return out


@app.post("/api/v1/formula")
def api_formula(req: FormulaRequest):
    body, err = run_formula_endpoint(req.dict())
    return err if err else body


def run_intent_reflect(args: dict):
    try:
        out = reflectkit.run_reflect(args)
    except reflectkit.Unreadable as e:
        return None, bad_request(
            [{"field": e.field, "message": e.message,
              "expected": e.expected}], kind="unreadable_reading")
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/intent/reflect")
def api_intent_reflect(req: FormulaRequest):
    body, err = run_intent_reflect(req.dict())
    return err if err else body


# ------------------------------ bundle 46: date/recurrence (RRULE)

class RecurrenceRequest(BaseModel):
    dtstart: Optional[str] = None
    rrule: Optional[str] = None
    max_count: Optional[int] = None


def run_date_recurrence(args: dict):
    try:
        out = recurrkit.run_recurrence(args)
    except recurrkit.RecurrenceError as e:
        return None, bad_request(
            [{"field": e.field, "message": e.message,
              "expected": e.expected}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/date/recurrence")
def api_date_recurrence(req: RecurrenceRequest):
    body, err = run_date_recurrence(req.dict())
    return err if err else body

# ------------------------------ bundle 47: units/shoe_size + net/sri

class ShoesSizeRequest(BaseModel):
    foot_mm: Optional[str] = None
    size: Optional[str] = None
    system: Optional[str] = None
    width_mm: Optional[str] = None


def run_units_shoe_size(args: dict):
    try:
        out = shoeskit.run_shoe_size(args)
    except shoeskit.ShoeSizeError as e:
        return None, bad_request(
            [{"field": e.field, "message": e.message,
              "expected": e.expected}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/units/shoe_size")
def api_units_shoe_size(req: ShoesSizeRequest):
    body, err = run_units_shoe_size(req.dict())
    return err if err else body


class SriRequest(BaseModel):
    bytes_b64: Optional[str] = None
    text: Optional[str] = None
    algorithms: Optional[list] = None
    url: Optional[str] = None
    integrity_attr: Optional[str] = None


def run_net_sri(args: dict):
    try:
        out = srikit.run_sri(args)
    except srikit.SriError as e:
        return None, bad_request(
            [{"field": e.field, "message": e.message,
              "expected": e.expected}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/net/sri")
def api_net_sri(req: SriRequest):
    body, err = run_net_sri(req.dict())
    return err if err else body


# ------------------------------ bundle 48: date/tz_ambiguity

class TzAmbiguityRequest(BaseModel):
    zone: Optional[str] = None
    local: Optional[str] = None


def run_date_tz_ambiguity(args: dict):
    try:
        out = tzambkit.run_tz_amb(args)
    except tzambkit.TzAmbError as e:
        return None, bad_request(
            [{"field": e.field, "message": e.message,
              "expected": e.expected}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/date/tz_ambiguity")
def api_date_tz_ambiguity(req: TzAmbiguityRequest):
    body, err = run_date_tz_ambiguity(req.dict())
    return err if err else body

# ---------------- bundle 49: money/flight_comp + date/week


class MoneyFlightCompRequest(BaseModel):
    regime: Optional[str] = None
    flight_date: Optional[str] = None
    event: Optional[str] = None
    distance_km: Optional[str] = None
    intra_eu: Optional[str] = None
    delay_min: Optional[str] = None
    notice_days: Optional[str] = None
    rerouted: Optional[str] = None
    reroute_depart_early_min: Optional[str] = None
    reroute_arrive_late_min: Optional[str] = None
    extraordinary: Optional[str] = None


def run_money_flight_comp(args: dict):
    try:
        out = compkit.decide(args)
    except compkit.CompError as e:
        return None, bad_request(
            [{"field": e.field, "message": e.message,
              "expected": e.expected}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/money/flight_comp")
def api_money_flight_comp(req: MoneyFlightCompRequest):
    body, err = run_money_flight_comp(req.dict())
    return err if err else body


class DateWeekRequest(BaseModel):
    date: Optional[str] = None
    iso: Optional[str] = None
    year: Optional[str] = None


def run_date_week(args: dict):
    try:
        out = weekkit.run_week(args)
    except weekkit.WeekError as e:
        return None, bad_request(
            [{"field": e.field, "message": e.message,
              "expected": e.expected}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/date/week")
def api_date_week(req: DateWeekRequest):
    body, err = run_date_week(req.dict())
    return err if err else body

# ---------------- bundle 50: money/baggage + csv/excel_damage


class MoneyBaggageRequest(BaseModel):
    flight_date: Optional[str] = None
    regime: Optional[str] = None
    bag: Optional[str] = None
    bag_unit: Optional[str] = None
    weight_kg: Optional[str] = None
    personal_sizer: Optional[str] = None
    cabin_sizer: Optional[str] = None
    cabin_sum_limit: Optional[str] = None
    cabin_weight_max: Optional[str] = None


def run_money_baggage(args: dict):
    try:
        out = bagkit.run_baggage(args)
    except bagkit.BagError as e:
        return None, bad_request(
            [{"field": e.field, "message": str(e.message),
              "expected": e.expected}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/money/baggage")
def api_money_baggage(req: MoneyBaggageRequest):
    body, err = run_money_baggage(req.dict())
    return err if err else body


class CsvExcelDamageRequest(BaseModel):
    csv: Optional[str] = None
    locale: Optional[str] = None
    as_of: Optional[str] = None


def run_csv_excel_damage(args: dict):
    try:
        out = damagekit.run_damage(args)
    except damagekit.DamageError as e:
        return None, bad_request(
            [{"field": e.field, "message": str(e.message),
              "expected": e.expected}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/csv/excel_damage")
def api_csv_excel_damage(req: CsvExcelDamageRequest):
    body, err = run_csv_excel_damage(req.dict())
    return err if err else body


# ---------------- bundle 52: money/crossover + csv/excel_display

class MoneyCrossoverRequest(BaseModel):
    currency: Optional[str] = None
    a_unit_rate: Optional[str] = None
    a_unit_per: Optional[str] = None
    a_fixed: Optional[str] = None
    a_fixed_per: Optional[str] = None
    b_unit_rate: Optional[str] = None
    b_unit_per: Optional[str] = None
    b_fixed: Optional[str] = None
    b_fixed_per: Optional[str] = None
    days_per_year: Optional[str] = None
    usage_per_period: Optional[str] = None
    usage_period: Optional[str] = None
    km_per_unit: Optional[str] = None
    exit_fee_a: Optional[str] = None
    exit_fee_b: Optional[str] = None
    sign_up_a: Optional[str] = None
    sign_up_b: Optional[str] = None


def run_money_crossover(args: dict):
    try:
        out = crosskit.run_crossover(args)
    except crosskit.CrossError as e:
        return None, bad_request(
            [{"field": e.field, "message": str(e.message),
              "expected": e.expected}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/money/crossover")
def api_money_crossover(req: MoneyCrossoverRequest):
    body, err = run_money_crossover(req.dict())
    return err if err else body


class CsvExcelDisplayRequest(BaseModel):
    value: Optional[str] = None
    format: Optional[str] = None
    locale: Optional[str] = None


def run_csv_excel_display(args: dict):
    try:
        out = displaykit.run_display(args)
    except displaykit.DisplayError as e:
        return None, bad_request(
            [{"field": e.field, "message": str(e.message),
              "expected": e.expected}])
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/csv/excel_display")
def api_csv_excel_display(req: CsvExcelDisplayRequest):
    body, err = run_csv_excel_display(req.dict())
    return err if err else body

# ------------------------------ bundle 0: task router + named recipes

@app.get("/route")
def api_route(q: str = "", top: int = Query(default=5, ge=1, le=10)):
    if len(q) > 500:
        return bad_request(
            [{"field": "q", "message": "too long (%d > 500)" % len(q),
              "expected": "a task phrase under 500 chars, e.g. "
                          '"dirty csv to typed rows"'}],
            "route_failed")
    body = {"query": q, "tools": routing.route(q, top),
            "note": "closed-vocabulary ranking over the manifest table; "
                    "no LLM: same words, same answer, sha256 on it"}
    rail = routing.elsewhere(q)
    if rail:
        body["elsewhere"] = rail
    body["sha256"] = canon(body)
    return body


class RecipeCleanTableRequest(BaseModel):
    csv: str


class RecipeCleanJsonRequest(BaseModel):
    text: str
    style: Literal["minified", "pretty"] = "minified"


class RecipeDataTrioRequest(BaseModel):
    csv: str
    json_text: str
    urls: List[str]


def _recipe_clean_table(req):
    out, err = run_csv_fix({"csv": req.csv})
    if err:
        return None, err
    fixed, notes = out["output"], out["notes"]
    out, err = run_csv_types({"csv": fixed})
    if err:
        return None, err
    rows, columns = out["output"], out["columns"]
    out, err = run_list_dedupe({"items": rows, "mode": "exact"})
    if err:
        return None, err
    body = {"recipe": "clean-table",
            "steps": ["csv/fix", "csv/types", "list/dedupe"],
            "fix_notes": notes,
            "columns": columns,
            "rows": out["output"],
            "removed_rows": out["removed"]}
    body["sha256"] = canon(body)
    return body, None


def _recipe_clean_json(req):
    out, err = run_json_repair({"text": req.text})
    if err:
        return None, err
    value, repairs = out["output"], out["repairs"]
    out, err = run_json_canonical({"input": value, "style": req.style})
    if err:
        return None, err
    body = {"recipe": "clean-json",
            "steps": ["json/repair", "json/canonical"],
            "repairs": repairs,
            "text": out["text"],
            "bytes": out["bytes"]}
    body["sha256"] = canon(body)
    return body, None


@app.post("/api/v1/recipe/clean-table")
def api_recipe_clean_table(req: RecipeCleanTableRequest):
    body, err = _recipe_clean_table(req)
    return err if err else body


@app.post("/api/v1/recipe/clean-json")
def api_recipe_clean_json(req: RecipeCleanJsonRequest):
    body, err = _recipe_clean_json(req)
    return err if err else body


def _recipe_data_trio(req):
    """The rag-ingestion trio in one call: dirty csv -> typed unique rows,
    broken json -> repaired object, url list -> deduped. This is the
    pre-processing of every embedding pipeline, done once, for all."""
    out, err = _recipe_clean_table(SimpleNamespace(csv=req.csv))
    if err:
        return None, err
    rows = out["rows"]
    out, err = run_json_repair({"text": req.json_text})
    if err:
        return None, err
    totals = out["output"]
    out, err = run_list_dedupe({"items": req.urls, "mode": "url"})
    if err:
        return None, err
    urls = out["output"]
    doc = {"rows": rows, "totals": totals, "urls": urls}
    out, err = run_format_convert({"input": doc, "from": "json",
                                   "to": "yaml"})
    if err:
        return None, err
    body = {"recipe": "data-trio",
            "steps": ["csv/fix", "csv/types", "list/dedupe",
                      "json/repair", "list/dedupe", "format/convert"],
            "output": out["output"]}
    body["sha256"] = canon(body)
    return body, None


@app.post("/api/v1/recipe/data-trio")
def api_recipe_data_trio(req: RecipeDataTrioRequest):
    body, err = _recipe_data_trio(req)
    return err if err else body


@app.get("/api/v1/recipes")
def api_recipes():
    body = {"recipes": {
        "clean-table": "csv/fix -> csv/types -> list/dedupe: dirty CSV in, "
                       "typed unique rows out (POST {csv})",
        "data-trio": "the rag-ingestion trio in one call: dirty csv + "
                     "broken json + url list -> final YAML {rows, totals, "
                     "urls} (POST {csv, json_text, urls}) — also a "
                     "pipeline step: recipe_data_trio",
        "facts": "free text -> recipe/facts: every money/percent/date/"
                 "number/url/email/uuid/iban canonicalized, deduped and "
                 "sorted in ONE call, plus the money total (POST {text}) "
                 "— the multi-step answer a weak model cannot assemble "
                 "alone",
        "clean-json": "json/repair -> json/canonical: broken JSON in, "
                      "canonical bytes out (POST {text, style})"},
        "usage": "POST /api/v1/recipe/<name>; a failing step returns its "
                 "own 400 with field+expected+example, untouched"}
    body["sha256"] = canon(body)
    return body


# ----------------------------------- bundle 0: pipeline in one call (B0.3)

class PipelineStep(BaseModel):
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)


class PipelineRequest(BaseModel):
    steps: List[PipelineStep]


class _BadRef(Exception):
    pass


def _subst(value, results, upto):
    if isinstance(value, dict):
        if "$fill" in value:
            raise _BadRef('"$fill" is not a server placeholder — the '
                          'caller substitutes data before POSTing (agent '
                          'code passes its own variable)')
        stray = {"$from", "$step"} & set(value)
        if stray and set(value) != {"$from"}:
            raise _BadRef('"$from" must REPLACE the whole value — '
                          '{"arg": {"$from": [i, "key"]}}, never mixed '
                          'with other keys inside one object')
        if set(value) == {"$from"}:
            ref = value["$from"]
            if (not isinstance(ref, list) or len(ref) != 2
                    or not isinstance(ref[0], int) or isinstance(ref[0], bool)
                    or not isinstance(ref[1], str)):
                raise _BadRef('expected {"$from": [earlier_step, "key"]}')
            if not 0 <= ref[0] < upto:
                raise _BadRef("step %d cannot see step %d (results so far: "
                              "%d)" % (upto, ref[0], upto))
            if ref[1] not in results[ref[0]]:
                raise _BadRef('step %d output has no key %r (keys: %s)'
                              % (ref[0], ref[1], sorted(results[ref[0]])))
            return results[ref[0]][ref[1]]
        return {k: _subst(v, results, upto) for k, v in value.items()}
    if isinstance(value, list):
        return [_subst(v, results, upto) for v in value]
    return value


def _pipeline_payment_guard(i, step, subbed):
    """A pipeline must not smuggle paid work through a free door: the
    x402 middleware lives on HTTP routes, so here we re-derive the tier
    from the tool's own path and refuse what needs per-call payment."""
    path = routing.PATHS.get(step.tool)
    size = len(json.dumps(subbed, ensure_ascii=False).encode("utf-8"))
    if path in payments.PRICES:
        return JSONResponse(status_code=402, content={
            "error": "payment_required",
            "field": "steps[%d].tool" % i,
            "expected": "pipelines chain free and capped tools; %s is paid "
                        "(%s) — call its route directly with x402"
                        % (step.tool, payments.PRICE_LABELS[path])})
    if path in payments.CAP_ROUTES and size > payments.CAP_BYTES:
        return JSONResponse(status_code=402, content={
            "error": "payment_required",
            "field": "steps[%d].args" % i,
            "expected": "%s is free under %d bytes; this step payload is %d "
                        "— call its route directly with x402"
                        % (step.tool, payments.CAP_BYTES, size)})
    return None


def run_pipeline(args: dict):
    try:
        req = PipelineRequest(**args)
    except Exception as e:
        return None, bad_request(_pyd_errors(e))
    if not 1 <= len(req.steps) <= 8:
        return None, bad_request(
            [{"field": "steps", "message": "1..8 steps",
              "expected": "a short chain — longer work belongs in code"}],
            "pipeline_failed")
    results = []
    trace = []
    for i, step in enumerate(req.steps):
        runner = TOOL_RUN.get(step.tool)
        if runner is None:
            return None, bad_request(
                [{"field": "steps[%d].tool" % i,
                  "message": "unknown tool %r" % step.tool,
                  "expected": "one of the 53 tool names "
                              "(GET /agent/manifest)"}],
                "pipeline_failed")
        try:
            subbed = _subst(step.args, results, i)
        except _BadRef as e:
            return None, bad_request(
                [{"field": "steps[%d].args" % i, "message": str(e),
                  "expected": '{"$from": [earlier_step_index, "key"]}'}],
                "pipeline_failed")
        guard = _pipeline_payment_guard(i, step, subbed)
        if guard is not None:
            return None, guard
        body, err = runner(subbed)
        if err is not None:
            content = json.loads(err.body)
            content["step"] = i
            content["tool"] = step.tool
            content["chain"] = [t.tool for t in req.steps]
            return None, JSONResponse(status_code=400, content=content)
        results.append(body)
        trace.append(step.tool)
    out = {"steps": trace, "output": results[-1]}
    out["sha256"] = canon(out)
    return out, None


@app.post("/api/v1/pipeline")
def api_pipeline(req: PipelineRequest):
    body, err = run_pipeline(req.model_dump())
    return err if err else body


# ------------------------------------------------------- tool dispatch
TOOL_RUN = {
           # recipes ARE tools: a weak agent composes at the right
           # altitude (B0.10). args shape = the recipe's own fields.
           "recipe_clean_table": lambda a: _recipe_clean_table(
               SimpleNamespace(**a)),
           "recipe_clean_json": lambda a: _recipe_clean_json(
               SimpleNamespace(**a)),
           "recipe_data_trio": lambda a: _recipe_data_trio(
               SimpleNamespace(**a)),
           "chart_from_data": run_chart,
           "reshape_json": run_reshape,
           "validate_json": run_validate,
           "json_repair": run_json_repair,
           "json_diff": run_json_diff,
           "json_patch": run_json_patch,
           "json_canonical": run_json_canonical,
           "list_dedupe": run_list_dedupe,
           "csv_fix": run_csv_fix,
           "csv_types": run_csv_types,
           "csv_join": run_csv_join,
           "table_pivot": run_table_pivot,
           "format_convert": run_format_convert,
           "text_patch": run_text_patch,
           "text_diff": run_text_diff,
           "text_apply_diff": run_text_apply_diff,
           "path_normalize": run_path_normalize,
           "glob_match": run_glob_match,
           "env_interpolate": run_env_interpolate,
           "date_parse": run_date_parse,
           "date_tz": run_date_tz,
           "date_calc": run_date_calc,
           "cron_next": run_cron_next,
           "cron_humanize": run_cron_humanize,
           "ics_generate": run_ics_generate,
           "ics_parse": run_ics_parse,
           "num_format": run_num_format,
           "num_parse": run_num_parse,
           "num_round": run_num_round,
           "units_convert": run_units_convert,
           "money_prorate": run_money_prorate,
           "money_split": run_money_split,
           "number_spell": run_number_spell,
           "hash_digest": run_hash_digest,
           "hash_hmac": run_hash_hmac,
           "net_ip": run_net_ip,
           "net_cidr": run_net_cidr,
           "file_encoding": run_file_encoding,
           "integrity_verify": run_verify,
           "math_calc": run_calc,
           "money_discount": run_discount,
           "table_sql_dump": run_sql_dump,
           "table_scale": run_table_scale,
           "check_format": run_check_format,
           "csv_money_columns": run_money_columns,
           "formula_catalog": run_formula_endpoint,
           "intent_reflect": run_intent_reflect,
           "date_recurrence": run_date_recurrence,
           "units_shoe_size": run_units_shoe_size,
           "net_sri": run_net_sri,
           "date_tz_ambiguity": run_date_tz_ambiguity,
           "money_flight_comp": run_money_flight_comp,
           "date_week": run_date_week,
           "money_baggage": run_money_baggage,
           "csv_excel_damage": run_csv_excel_damage,
           "money_crossover": run_money_crossover,
           "csv_excel_display": run_csv_excel_display,
           "date_relative": run_relative_date,
           "text_url_canonical": run_url_canonical,
           "xml_to_json": run_xml_json,
           "web_cert": run_cert,
           "id_checkdigit": run_checkdigit,
           "image_rightsize": run_rightsize,
           "money_rates": run_rates,
           "doc_text": run_doc_text,
           "money_amortize": run_amortize,
           "money_interest": run_interest,
           "ics_validate": run_ics,
           "schedule_holidays": run_holidays,
           "web_cache": run_web_cache,
           "gzip_roundtrip": run_gzip,
           "qr_generate": run_qr,
           "table_peek": run_table_peek,
           "csv_diff": run_csv_diff,
           "ssh_fingerprint": run_ssh_fp,
           "zip_verify": run_zip_verify,
           "schedule_overlap": run_schedule_overlap,
           "cron_validate": run_cron,
           "crypto_address": run_crypto_address,
           "validate_taxid": run_tax_validate,
           "caip": run_caip,
           "secret_scan": run_secret_scan,
           "text_redact": run_text_redact,
           "validate_country": run_validate_country,
           "validate_postal": run_validate_postal,
           "geo_distance": run_geo_distance,
           "geo_geohash": run_geo_geohash,
           "file_identify": run_file_identify,
           "text_punycode": run_text_punycode,
           "semver_parse": run_semver_parse,
           "semver_sort": run_semver_sort,
           "text_sanitize": run_text_sanitize,
           "json_map": run_json_map,
           "num_fx": run_num_fx,
           "id_ulid": run_id_ulid,
           "pkg_name": run_pkg_name,
           "enc_base64": run_enc_base64,
           "jwt_decode": run_jwt_decode,
           "id_uuid": run_id_uuid,
           "id_slug": run_id_slug,
           "fingerprint": run_fingerprint,
           "validate_iban": run_validate_iban,
           "validate_phone": run_validate_phone,
           "validate_email": run_validate_email,
           "validate_url": run_validate_url,
           "color_check": run_color_check,
           "text_count": run_text_count,
           "sort_natural": run_sort_natural,
           "text_case": run_text_case,
           "text_truncate": run_text_truncate,
           "regex_test": run_regex_test,
           "text_chunk": run_text_chunk,
           "md_render": run_md_render,
           "html_text": run_html_text,
           "color_palette": run_color_palette,
           "check_constraints": run_check_constraints,
           "check_refs": run_check_refs,
           "extract_facts": run_extract_facts,
           "recipe_facts": run_recipe_facts,
           "intent_card": run_intent_card,
           "intent_check": run_intent_check,
           "check_agreement": run_check_agreement,
           "check_redlines": run_check_redlines,
           "text_select": run_text_select,
           "logic_rules": run_logic_rules,
           "sort_multi": run_sort_multi,
           "json_query": run_json_query,
           "eth_abi_encode": run_eth_abi_encode,
           "eth_abi_decode": run_eth_abi_decode,
           "eth_eip712": run_eth_eip712,
           "eth_receipt": run_eth_receipt,
           "eth_address": run_eth_address,
           "eth_selector": run_eth_selector,
           "eth_units": run_eth_units,
           "text_decode": run_text_decode,
           "num_human": run_num_human,
           "text_escape": run_text_escape,
           "text_normalize": run_text_normalize,
           "batch": run_batch,
           "recipe_invoice": run_recipe_invoice,
           "recipe_schedule": run_recipe_schedule,
           "recipe_shop_reste": lambda a: _run_fiche("shop_reste", a),
           "recipe_partage_reste": lambda a: _run_fiche("partage_reste", a),
           "recipe_soldes2": lambda a: _run_fiche("soldes2", a),
           }

# ---------------------------------------------------------------- MCP

MCP_TOOLS = [
    {
        "name": "chart_from_data",
        "description": (
            "Deterministic chart from records or CSV. Returns a Vega-Lite spec "
            "and/or a PNG. No LLM, nothing stored. Same request -> same sha256. "
            "Never reorders your data: bars/pies aggregate (sum) per category in "
            "first-appearance order; lines keep input order."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["x"],
            "properties": {
                "kind": {"type": "string", "enum": sorted(chart.KINDS),
                         "default": "bar",
                         "description": "bar, line, area, point, step, histogram, pie"},
                "x": {"type": "string",
                      "description": "category or numeric column"},
                "y": {"type": "string",
                      "description": "value column; required unless kind is histogram"},
                "series": {"type": "string", "description": "grouping column"},
                "title": {"type": "string"},
                "data": {"type": "array", "items": {"type": "object"},
                         "description": "records; or send csv"},
                "csv": {"type": "string",
                        "description": "CSV text, header row required"},
                "width": {"type": "integer", "default": 640},
                "height": {"type": "integer", "default": 400},
                "format": {"type": "string", "enum": ["both", "spec", "png"],
                           "default": "both"},
            },
        },
    },
    {
        "name": "reshape_json",
        "description": (
            "Reshape JSON with a declarative mapping (path, cast, default, "
            "required, each). Optional outputSchema gate: the output is "
            "validated and rejected with precise errors on violation. "
            "No LLM, nothing stored."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["input", "mapping"],
            "properties": {
                "input": {"description": "any JSON payload"},
                "mapping": {
                    "type": "object",
                    "required": ["fields"],
                    "properties": {"fields": {"type": "object"}},
                    "description": ("fields: {outKey: {path, cast?, default?, "
                                    "required?, each?} | {const}}"),
                },
                "outputSchema": {
                    "type": "object",
                    "description": "JSON Schema (draft 2020-12) the output must satisfy",
                },
            },
        },
    },
    {
        "name": "validate_json",
        "description": ("Validate a payload against a JSON Schema (draft 2020-12). "
                        "Returns valid or precise errors."),
        "inputSchema": {
            "type": "object",
            "required": ["payload", "schema"],
            "properties": {"payload": {"description": "any JSON"},
                           "schema": {"type": "object"}},
        },
    },
    {
        "name": "json_repair",
        "description": (
            "Repair broken JSON text deterministically (markdown fences, BOM, "
            "smart/single quotes, comments, bare keys, trailing commas, Python "
            "literals, JSONL). Returns the parsed value + repairs applied. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text"],
            "properties": {"text": {"type": "string",
                                    "description": "the broken JSON text"}},
        },
    },
    {
        "name": "json_diff",
        "description": (
            "Structural diff between two JSON values: sorted changes with RFC "
            "6901 pointer paths (added/removed/changed). Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["a", "b"],
            "properties": {"a": {"description": "original JSON"},
                           "b": {"description": "modified JSON"}},
        },
    },
    {
        "name": "json_patch",
        "description": (
            "Apply an RFC 6902 patch (add/remove/replace/move/copy/test) to a "
            "document; per-operation errors with the failing index. Free under "
            "32 KB, x402 above."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["document", "patch"],
            "properties": {
                "document": {"description": "the JSON document to patch"},
                "patch": {"type": "array", "items": {"type": "object"},
                          "description": "RFC 6902 operations, applied in order"},
            },
        },
    },
    {
        "name": "json_canonical",
        "description": (
            "Canonical JSON bytes: keys sorted, minified or pretty, exact "
            "sha256 of the emitted text. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["input"],
            "properties": {
                "input": {"description": "any JSON"},
                "style": {"type": "string", "enum": ["minified", "pretty"],
                          "default": "minified"},
            },
        },
    },
    {
        "name": "csv_fix",
        "description": (
            "Dirty CSV -> clean comma-CSV with \\n endings: BOM stripped, line "
            "endings unified, delimiter detected, blank rows removed, headers "
            "normalized (empty named, duplicates suffixed), short/long rows "
            "padded/truncated. Returns notes. Free under 32 KB, x402 above."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["csv"],
            "properties": {
                "csv": {"type": "string", "description": "the dirty CSV text"},
                "preserve_delimiter": {"type": "boolean", "default": False,
                                       "description": "keep the detected "
                                                      "delimiter instead of comma"},
            },
        },
    },
    {
        "name": "csv_types",
        "description": (
            "Infer and coerce column types (int, float, bool, date, datetime, "
            "string, null) over CSV text or records; returns typed rows and a "
            "column report with null counts. Free under 32 KB, x402 above."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "csv": {"type": "string", "description": "CSV text"},
                "rows": {"type": "array", "items": {"type": "object"},
                         "description": "or records directly"},
            },
        },
    },
    {
        "name": "csv_join",
        "description": (
            "Join two record tables (inner|left|right|outer) on a key column "
            "or [leftKey, rightKey]; overlapping columns: left wins; rows "
            "missing the key never match. Paid route (x402 from first call)."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["on"],
            "properties": {
                "left": {"type": "array", "items": {"type": "object"}},
                "left_csv": {"type": "string"},
                "right": {"type": "array", "items": {"type": "object"}},
                "right_csv": {"type": "string"},
                "on": {"description": "\"col\" | [\"lcol\", \"rcol\"] | "
                                      "{\"left\": .., \"right\": ..}"},
                "how": {"type": "string",
                        "enum": ["inner", "left", "right", "outer"],
                        "default": "inner"},
            },
        },
    },
    {
        "name": "table_pivot",
        "description": (
            "Pivot records (index x columns -> aggregated values, agg "
            "sum|count|mean|min|max|first, columns sorted, missing -> null) or "
            "unpivot (melt, keep/vars). Paid route (x402 from first call)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {"type": "array", "items": {"type": "object"}},
                "csv": {"type": "string"},
                "mode": {"type": "string", "enum": ["pivot", "unpivot"],
                         "default": "pivot"},
                "index": {"description": "pivot: column or list of columns"},
                "columns": {"type": "string", "description": "pivot: values spread here"},
                "values": {"type": "string", "description": "pivot: aggregated column"},
                "agg": {"type": "string",
                        "enum": ["sum", "count", "mean", "min", "max", "first"],
                        "default": "sum"},
                "keep": {"type": "array", "items": {"type": "string"},
                         "description": "unpivot: retained columns"},
                "vars": {"type": "array", "items": {"type": "string"},
                         "description": "unpivot: melted columns"},
                "var_name": {"type": "string", "default": "variable"},
                "value_name": {"type": "string", "default": "value"},
            },
        },
    },
    {
        "name": "list_dedupe",
        "description": (
            "Dedupe a list keeping the first occurrence and the original "
            "values: modes exact | text (NFC, whitespace, casefold) | url "
            "(scheme/host case, default ports, trailing slash, fragment, "
            "sorted query) | email (lowercase local@domain). Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["items"],
            "properties": {
                "items": {"type": "array", "description": "the list to dedupe"},
                "mode": {"type": "string",
                         "enum": ["exact", "text", "url", "email"],
                         "default": "text"},
            },
        },
    },
    {
        "name": "format_convert",
        "description": (
            "Convert between json, yaml, toml, csv, env. Deterministic: keys "
            "sorted where the format allows, \\n endings. env requires flat "
            "scalars; toml requires an object; csv requires an array of "
            "objects. Free under 32 KB, x402 above."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["input", "from", "to"],
            "properties": {
                "input": {"type": "string", "description": "the source text"},
                "from": {"type": "string",
                         "enum": ["json", "yaml", "toml", "csv", "env"]},
                "to": {"type": "string",
                       "enum": ["json", "yaml", "toml", "csv", "env"]},
            },
        },
    },
    {
        "name": "text_patch",
        "description": (
            "Find/replace edits on a text, applied in order, each verified: "
            "'occurrences' is \"one\" (default: exact-uniqueness gate), "
            "\"all\" or an exact count. A non-unique rename fails loudly "
            "instead of guessing. Paid route (x402 from first call)."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text", "edits"],
            "properties": {
                "text": {"type": "string", "description": "the source text"},
                "edits": {"type": "array", "items": {"type": "object"},
                          "description": "[{find, replace, occurrences?}]"},
            },
        },
    },
    {
        "name": "text_diff",
        "description": (
            "Unified line diff between two texts, fixed labels "
            "(before/after), configurable context (default 3), stats "
            "(hunks/added/removed), identical flag, exact sha256. Free under "
            "32 KB, x402 above."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["a", "b"],
            "properties": {
                "a": {"type": "string", "description": "original text"},
                "b": {"type": "string", "description": "modified text"},
                "context": {"type": "integer", "default": 3,
                            "description": "context lines (0-20)"},
            },
        },
    },
    {
        "name": "text_apply_diff",
        "description": (
            "Apply a unified diff STRICTLY: every context and deletion line "
            "must match its documented position; mismatches name the hunk and "
            "line — no fuzz, no silent reflow. Paid route (x402)."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text", "diff"],
            "properties": {
                "text": {"type": "string", "description": "the file text"},
                "diff": {"type": "string", "description": "unified diff"},
            },
        },
    },
    {
        "name": "path_normalize",
        "description": (
            "Lexical path normalization to POSIX form (auto posix/windows, "
            ". and .. resolution never crossing root, optional lowercase) + "
            "name/stem/extension. Never touches the filesystem. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string"},
                "os": {"type": "string",
                       "enum": ["auto", "posix", "windows"],
                       "default": "auto"},
                "case": {"type": "string", "enum": ["keep", "lower"],
                         "default": "keep"},
            },
        },
    },
    {
        "name": "glob_match",
        "description": (
            "Deterministic glob over a list of paths: * and ? do not cross "
            "/, ** spans segments, dots are literal, case-sensitive, input "
            "order preserved. No filesystem. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["pattern", "paths"],
            "properties": {
                "pattern": {"type": "string",
                            "description": "e.g. src/**/test_*.py"},
                "paths": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    {
        "name": "env_interpolate",
        "description": (
            "Expand $VAR, ${VAR} and ${VAR:-default} from a vars object. "
            "strict=true (default) fails naming every missing var; "
            "strict=false keeps them literal and reports `missing`. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["template", "vars"],
            "properties": {
                "template": {"type": "string"},
                "vars": {"type": "object"},
                "strict": {"type": "boolean", "default": True},
            },
        },
    },
    {
        "name": "date_parse",
        "description": (
            "Parse one date (ISO 8601, RFC 2822, epoch seconds, slashed "
            "numeric with explicit dmy/mdy preference — never guessed — or "
            "month-name form) -> ISO, UTC, epoch, weekday, ISO week, naive "
            "flag. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string"},
                "prefer": {"type": "string", "enum": ["dmy", "mdy"],
                           "default": "dmy",
                           "description": "order for slashed ambiguous dates"},
                "tz": {"type": "string",
                       "description": "IANA zone to interpret a naive value in"},
            },
        },
    },
    {
        "name": "date_tz",
        "description": (
            "Convert an instant or bare date into IANA zones with correct "
            "DST: ISO output per zone, offset, dst flag. Naive inputs read "
            "in `source` (default UTC); bare dates get `at` (HH:MM, default "
            "00:00). Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["datetime", "targets"],
            "properties": {
                "datetime": {"type": "string"},
                "source": {"type": "string", "default": "UTC"},
                "targets": {"type": "array", "items": {"type": "string"}},
                "at": {"type": "string", "description": "HH:MM for bare dates"},
            },
        },
    },
    {
        "name": "date_calc",
        "description": (
            "Date arithmetic: add (calendar-aware duration like \"1y2m3dT4h\", "
            "month-end clamped), business_days (n, holidays, weekend), diff "
            "(days|business_days|human|calendar), boundary "
            "(day|week|month|quarter|year, start|end), age. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["base", "op"],
            "properties": {
                "base": {"type": "string"},
                "op": {"type": "string",
                       "enum": ["add", "business_days", "diff", "boundary",
                                "age"]},
                "params": {"type": "object"},
                "tz": {"type": "string"},
            },
        },
    },
    {
        "name": "cron_next",
        "description": (
            "Next N fire times of a 5-field cron expression (or @macro), "
            "wall-clock semantics in `tz`, Vixie dom/dow OR rule. Pin "
            "`after` for a byte-stable answer. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["expression"],
            "properties": {
                "expression": {"type": "string"},
                "count": {"type": "integer", "default": 1,
                          "description": "1-1000"},
                "after": {"type": "string",
                          "description": "ISO instant (default: wall now)"},
                "tz": {"type": "string", "default": "UTC"},
            },
        },
    },
    {
        "name": "cron_humanize",
        "description": ("Cron expression -> plain reading + resolved field "
                        "sets. Free."),
        "inputSchema": {
            "type": "object",
            "required": ["expression"],
            "properties": {"expression": {"type": "string"}},
        },
    },
    {
        "name": "ics_generate",
        "description": (
            "Events -> deterministic RFC 5545 VCALENDAR: CRLF, 75-octet "
            "folding, DTSTAMP mirrors DTSTART when absent so bytes never "
            "drift. Free under 32 KB, x402 above."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["events"],
            "properties": {
                "events": {"type": "array", "items": {"type": "object"},
                           "description": "[{start, end|duration, summary, "
                                          "tz?, uid?, rrule?, ...}]"},
                "prodid": {"type": "string",
                           "default": "-//mechacut.studio//ICS//EN"},
                "calname": {"type": "string", "default": "mechacut"},
            },
        },
    },
    {
        "name": "ics_parse",
        "description": (
            "VCALENDAR -> calendar meta + normalized events (ISO starts/ends, "
            "duration seconds, RRULE raw passthrough, unescaped text). Free "
            "under 32 KB, x402 above."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["ics"],
            "properties": {"ics": {"type": "string"}},
        },
    },
    {
        "name": "num_format",
        "description": (
            "Deterministic number/currency/percent formatting from CLOSED "
            "locale (13) and currency (20) tables, Decimal-based: 1234.567 "
            '-> "1,234.567", fr-FR EUR currency -> "1\u00A0234,57\u00A0\u20AC", '
            '"12.34%". Free.'
        ),
        "inputSchema": {
            "type": "object",
            "required": ["value"],
            "properties": {
                "value": {"description": "number or numeric string"},
                "locale": {"type": "string", "default": "en-US"},
                "style": {"type": "string",
                          "enum": ["number", "currency", "percent"],
                          "default": "number"},
                "currency": {"type": "string",
                             "description": "ISO code, required for currency"},
                "decimals": {"type": "integer",
                             "description": "0-30; default per style"},
                "grouping": {"type": "boolean", "default": True},
            },
        },
    },
    {
        "name": "num_parse",
        "description": (
            "Human number -> canonical decimal_string + float + currency + "
            "percent flags. Handles grouping styles (1,234.56 / 1.234,56 / "
            "1'234.56 / spaces), symbols and ISO codes. Ambiguity is "
            'REFUSED, not guessed: 1,234 needs prefer="decimal" or "group". '
            "Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string"},
                "prefer": {"type": "string", "enum": ["decimal", "group"]},
            },
        },
    },
    {
        "name": "num_round",
        "description": (
            "Exact Decimal rounding: places 0-30 or significant digits, "
            "modes half_even (banker's, default) | half_up | half_down | "
            "ceil | floor | trunc | up. Same string in, same string out. "
            "Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["value"],
            "properties": {
                "value": {"description": "number or numeric string"},
                "places": {"type": "integer", "default": 0},
                "mode": {"type": "string",
                         "enum": ["half_even", "half_up", "half_down",
                                  "ceil", "floor", "trunc", "up"],
                         "default": "half_even"},
                "significant": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "units_convert",
        "description": (
            "Unit conversion in closed families (length, mass, volume, "
            "area, speed, data incl. KiB/kbit distinction, duration, "
            "temperature) with exact rational factors - cross-family "
            "conversions are refused, unknown units name the table. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["value", "from", "to"],
            "properties": {
                "value": {"description": "number or numeric string"},
                "from": {"type": "string"},
                "to": {"type": "string"},
                "places": {"type": "integer", "default": 10},
            },
        },
    },
    {
        "name": "money_prorate",
        "description": (
            "Prorate a cycle amount over a service window: prorated = "
            "amount * covered_days / cycle_days, exact fraction reported, "
            "rounding is the last step (half_up default), window clamped "
            "to the cycle. Paid route (x402 from first call)."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["amount", "cycle_start", "cycle_end",
                         "service_start", "service_end"],
            "properties": {
                "amount": {"type": "string", "description": "decimal string"},
                "cycle_start": {"type": "string"},
                "cycle_end": {"type": "string"},
                "service_start": {"type": "string"},
                "service_end": {"type": "string"},
                "places": {"type": "integer", "default": 2},
                "mode": {"type": "string",
                         "enum": ["half_even", "half_up", "ceil", "floor",
                                  "trunc"], "default": "half_up"},
                "inclusive": {"type": "boolean", "default": True},
                "clamp": {"type": "boolean", "default": True},
            },
        },
    },
    {
        "name": "money_split",
        "description": (
            "Split an amount to the cent with a CLOSED remainder rule: "
            "floor shares + leftover cents by fractional part, ties by "
            "list order - who gets the extra cent is deterministic. Equal "
            "or weighted participants. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["total", "participants"],
            "properties": {
                "total": {"type": "string"},
                "participants": {"type": "array",
                                 "description": "[name | {name, weight?}]"},
                "mode": {"type": "string", "enum": ["remainder_order"],
                         "default": "remainder_order"},
            },
        },
    },
    {
        "name": "number_spell",
        "description": (
            "Amount -> words for the invoice legal mention, in FR/EN/PT with "
            "closed grammatical rules (quatre-vingts, cent invariable before "
            "mille, duzentos/trezentos, e-rules) and currency unit naming. "
            "Same amount, same language, same words - forever. Free under "
            "32 KB, x402 above."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["value"],
            "properties": {
                "value": {"description": "decimal amount string, max 2 places"},
                "lang": {"type": "string", "enum": ["fr", "en", "pt"],
                         "default": "fr"},
                "currency": {"type": "string",
                             "description": "ISO code from the closed table"},
                "cents": {"type": "boolean", "default": True},
                "capital": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "id_ulid",
        "description": "ULID make/parse/sort, Crockford base32, "
                       "deterministic BY CONSTRUCTION: make demands "
                       "timestamp_ms + entropy-hex or seed (same seed -> "
                       "same id: retry-safe idempotency keys, no hidden "
                       "clock). sort = chronological lexicographic. Free.",
        "inputSchema": {"type": "object", "properties": {
            "mode": {"type": "string", "enum": ["make", "parse", "sort"],
                     "default": "make"},
            "timestamp_ms": {"type": "integer"},
            "entropy": {"type": "string"},
            "seed": {"type": "string"},
            "ulid": {"type": "string"},
            "ids": {"type": "array", "items": {"type": "string"}}}}},
    {
        "name": "pkg_name",
        "description": "Package-name grammar verdict + normalization for "
                       "npm (case/dot/charset), PyPI (PEP 503) and Docker "
                       "(repo/tag/digest). Agents invent uppercase npm "
                       "names and dotted tags; the registry will reject "
                       "them — here they get told why, before the push. "
                       "Free.",
        "inputSchema": {"type": "object", "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "kind": {"type": "string", "enum": [
                                "npm", "pypi", "docker"],
                                     "default": "npm"}}}},
    {
        "name": "net_ip",
        "description": "IP address anatomy from the stdlib reference: v4/"
                       "v6, private/loopback/link-local/multicast/reserved"
                       ", reverse-DNS name, packed hex. Agents POST to "
                       "169.254.0.1 thinking it is routable; it is not, "
                       "and now they can know. Free.",
        "inputSchema": {"type": "object", "required": ["value"],
                        "properties": {"value": {"type": "string"}}}},
    {
        "name": "net_cidr",
        "description": "CIDR math: network/broadcast/prefix/usable hosts,"
                       " contains(IP|subnet) verdict, split_into N-bit "
                       "subnets (capped 256 listed). The cloud/infra "
                       "agent chore done exactly. Free.",
        "inputSchema": {"type": "object", "required": ["cidr"],
                        "properties": {
                            "cidr": {"type": "string"},
                            "contains": {"type": "string"},
                            "split_into": {"type": "integer"}}}},
    {
        "name": "file_encoding",
        "description": "Charset forensics that never guesses: BOM table "
                       "(5), strict utf-8 validation, and 'undetermined' "
                       "with the exact failing byte offset + hex when the"
                       " bytes do not prove a codec. The honest sibling "
                       "of /text/decode. Free.",
        "inputSchema": {"type": "object", "required": ["blob"],
                        "properties": {"blob": {
                            "type": "string",
                            "description": "base64 of the bytes"}}}},
    {
        "name": "schedule_overlap",
        "description": "Interval arithmetic, four closed modes: merge "
                       "(union + total), conflicts (overlapping pairs with "
                       "seconds), free (gaps inside a window), contains "
                       "(is this point busy?). No clock: every datetime is "
                       "a caller argument. Free.",
        "inputSchema": {"type": "object", "properties": {
            "intervals": {"type": "array", "items": {"type": "object",
                      "properties": {"start": {"type": "string"},
                                     "end": {"type": "string"},
                                     "label": {"type": "string"}},
                      "required": ["start", "end"]}},
            "mode": {"type": "string",
                     "enum": ["merge", "conflicts", "free", "contains"]},
            "window": {"type": "object"},
            "point": {"type": "string"}},
            "required": ["intervals"]}},
    {
        "name": "cron_validate",
        "description": "Vixie-cron semantics, five fields, names and "
                       "steps accepted; descending ranges refused; 7 == 0 "
                       "for Sunday; dom+dow both restricted ORs (documented "
                       "footnote); calendar-impossible expressions get "
                       "never + reason. Pass `at` to get the next runs — "
                       "computed, not guessed. Free.",
        "inputSchema": {"type": "object", "properties": {
            "expr": {"type": "string"},
            "at": {"type": "string"},
            "count": {"type": "integer", "minimum": 1, "maximum": 100}},
            "required": ["expr"]}},
    {
        "name": "integrity_verify",
        "description": "Determinism Auditor: point it at any API with "
                       "published pins (their integrity.json or an "
                       "explicit pin list) and it re-plays every request "
                       "N times over https, comparing sha256 — bytes mode "
                       "(strictest) or json-canonical. Verdicts separate "
                       "deterministic / non-deterministic / paywalled-"
                       "(gate-stable) / unreachable. SSRF-guarded: https "
                       "only, public IPs only (metadata ranges refused by "
                       "name), hard fetch/byte/time caps. Paid $0.001: "
                       "network egress is real work.",
        "inputSchema": {"type": "object", "properties": {
            "base_url": {"type": "string"},
            "pins": {"type": "array", "items": {"type": "object",
                      "properties": {"path": {"type": "string"},
                                     "name": {"type": "string"},
                                     "method": {"type": "string"},
                                     "body": {},
                                     "sha256": {"type": "string"}}}},
            "integrity_url": {"type": "string"},
            "attempts": {"type": "integer", "minimum": 2,
                         "maximum": 5},
            "mode": {"type": "string",
                     "enum": ["bytes", "json-canonical"]}},
            "required": ["base_url"]}},
    {
        "name": "math_calc",
        "description": "The closed calculator — the model WRITES the "
                       "expression, the machine COMPUTES it. Exact "
                       "Decimal arithmetic from the SOURCE TEXT of every "
                       "literal (0.1+0.2 = 0.3, never 0.30000000000000004): "
                       "+ - * / // % **, parentheses, unary sign, and "
                       "exactly three named functions round(x[,n]) with "
                       "declared HALF_UP, sqrt, abs. Everything else — "
                       "names, letters, strings, attributes, lambdas, "
                       "exponents over 64, divisions by zero, sqrt of "
                       "negatives — REFUSED BY NAME, never silently "
                       "clipped. digits=0..30 quantizes the final value "
                       "and KEEPS trailing zeros (39.900 stays 39.900). "
                       "50-digit working precision declared in the "
                       "answer. The engine under the formula catalogue "
                       "to come. Free forever: arithmetic should cost "
                       "nothing.",
        "inputSchema": {"type": "object", "properties": {
            "expr": {"type": "string"},
            "digits": {"type": "integer", "minimum": 0, "maximum": 30}},
            "required": ["expr"]}},
    {
        "name": "money_discount",
        "description": "The math the checkout will not do for you. '-30% "
                       "then -20%' is NOT -50%: chained discounts are "
                       "successive multiplicative factors (0.70 x 0.80 = "
                       "0.56 -> 44%), and the naive sum is reported "
                       "SIDE BY SIDE with the lie's size (percent_lie_"
                       "delta). When a fixed-amount step exists, ALL step "
                       "orders are computed and compared: order_matters + "
                       "order_spread + best_step_order_for_you — because "
                       "-30%% then -5eur is not -5eur then -30%%. buy2pay1 "
                       "with qty, exact Decimal money, final HALF_UP 2 dp "
                       "declared, the formula returned for audit, below-"
                       "zero chains refused by name never clipped. Free — "
                       "this one should be free forever.",
        "inputSchema": {"type": "object", "properties": {
            "price": {"type": "string"},
            "steps": {"type": "array", "items": {"type": "object",
                       "properties": {
                           "type": {"enum": ["percent", "fixed",
                                             "buy2pay1"]},
                           "value": {"type": "string"},
                           "per_unit": {"type": "boolean"}}}},
            "qty": {"type": "integer", "default": 1},
            "currency": {"type": "string"}},
            "required": ["price", "steps"]}},
    {
        "name": "formula_catalog",
        "description": "The published-formula engine: 12 everyday "
                       "formulas (rule of three, percent up/down with "
                       "the round-trip gap named, speed/distance/time "
                       "solved for any leg, fuel in BOTH senses, "
                       "running pace, C1V1 dilution every target, "
                       "mg/kg dosage with a scope note, baker's "
                       "hydration 3 modes, Naegele EDD by two "
                       "independent calendar paths, rational areas, "
                       "cuboid volume, part-of-total share). The "
                       "formula itself is in the answer, your numbers "
                       "are substituted into it, the math is exact "
                       "Fractions rendered to declared decimals. Zero "
                       "constants in this palier by construction — pi "
                       "and CODATA arrive with published digits. GET "
                       "/api/v1/formula lists the closed catalog.",
        "inputSchema": {"type": "object", "properties": {
            "formula": {"type": "string"},
            "args": {"type": "object"}},
            "required": ["formula"]}},
    {
        "name": "intent_reflect",
        "description": "The comprehension mirror. A model that "
                       "misreads a word problem computes the wrong "
                       "thing perfectly; free-form retrying never "
                       "fixed that (bench v13: relay 0/20). Here the "
                       "model DECLARES its reading — which catalog "
                       "formula, which args it understood — and the "
                       "server answers with the exact result PLUS a "
                       "reading_check line: the substitution written "
                       "out so the model can compare it against the "
                       "human's sentence in plain words. The machine "
                       "never claims to know the story (not_claimed "
                       "is in every response); it makes the reading "
                       "visible. Same engine as /api/v1/formula — the "
                       "mirror cannot diverge from the math.",
        "inputSchema": {"type": "object", "properties": {
            "formula": {"type": "string"},
            "args": {"type": "object"}},
            "required": ["formula", "args"]}},
    {
        "name": "date_recurrence",
        "description": "Expand an RFC 5545 RRULE into dated "
                       "occurrences — the closed subset, with every "
                       "trap declared IN the answer. Models silently "
                       "fail here: biweekly rules land every week "
                       "(INTERVAL ignored: 4 of 8 dates wrong on the "
                       "published demo), MONTHLY from the 31st is "
                       "dropped in short months (the RFC: invalid "
                       "dates MUST be ignored, never moved), mixed "
                       "BYDAY like MO,2TU reads as NO dates in "
                       "python-dateutil 4.0.0. Supported: FREQ "
                       "DAILY/WEEKLY/MONTHLY/YEARLY, INTERVAL, COUNT "
                       "xor UNTIL (both = refused by name), BYDAY with "
                       "ordinals only for MONTHLY/YEARLY, BYMONTH, "
                       "BYMONTHDAY signed, WKST. BYSETPOS, BYWEEKNO, "
                       "BYYEARDAY, BYHOUR, BYMINUTE, BYSECOND and "
                       "sub-daily FREQs are refused by name, never "
                       "softly ignored. DTSTART anchors the grid and "
                       "sync status is reported — rrule.js force-"
                       "includes it (off-by-one), dateutil drops it "
                       "silently; the RFC calls that zone UNDEFINED "
                       "and we declare it. Wall-clock expansion per "
                       "the RFC: DST moves the UTC instant, not the "
                       "local time (per-day instants: date/tz). Cap "
                       "500 occurrences, truncation and skipped dates "
                       "listed. Free, no payment.",
        "inputSchema": {"type": "object", "properties": {
            "dtstart": {"type": "string",
                        "description": "YYYY-MM-DD, "
                        "YYYY-MM-DDTHH:MM[:SS], ...Z, or the RFC "
                        "compact 19970902T090000Z"},
            "rrule": {"type": "string",
                      "description": "RFC 5545 RRULE value; a leading "
                                      "'RRULE:' is accepted and "
                                      "stripped"},
            "max_count": {"type": "integer",
                          "description": "default and hard cap "
                                         "500"}},
            "required": ["dtstart", "rrule"]}},
    {
        "name": "units_shoe_size",
        "description": "Shoe sizes answered in millimetres with the "
                       "PUBLISHED steps as exact fractions — never one "
                       "confident number. Models and charts fail here: "
                       "convertisseurs print 'EU 42 -> US 9' while Nike "
                       "and adidas label the SAME foot 42.5 and 42 2/3; "
                       "small models invent averages ('7.5 - 1.5 = "
                       "9.5'). Inputs: foot_mm (measured) OR size+system "
                       "(eu|uk|us_men|us_women|mondopoint; sizes accept "
                       "42.5, '42 2/3', '85/2'), optional width_mm for "
                       "the ISO 9407 '271/100' label. Output: exact "
                       "fraction position per system + the grid "
                       "candidates each brand practice prints (halves "
                       "and thirds are both published EU grids), steps "
                       "(barleycorn 127/15 mm, Paris point 20/3 mm), the "
                       "cross-system drift stated as exact numbers (per "
                       "step 9/5 = 1.8 mm; 4 EU steps never equal 3 US "
                       "steps), the +2 allowance declared (40/3 mm), "
                       "and the foot-vs-last anchor said out loud. Brand "
                       "charts stay off-contract — no brand is encoded. "
                       "Out of bounds refused by name. Free, no payment.",
        "inputSchema": {"type": "object", "properties": {
            "foot_mm": {"type": "string",
                        "description": "measured foot length, e.g. 271"},
            "size": {"type": "string",
                     "description": "label: '42', '42.5', '42 2/3', "
                                    "'85/2'"},
            "system": {"type": "string",
                       "description": "eu | uk | us_men | us_women | "
                                      "mondopoint"},
            "width_mm": {"type": "string",
                         "description": "optional ISO 9407 width"}}}},
    {
        "name": "net_sri",
        "description": "Subresource Integrity from LOCAL octets only — "
                       "this tool never fetches. Give bytes_b64 or text "
                       "(the exact file you reviewed) and get the "
                       "ready-to-paste integrity attribute (sha256/"
                       "sha384/sha512, strongest-first, W3C grammar), "
                       "the crossorigin note, and full <script>/<link> "
                       "tags when a url is given. Give integrity_attr "
                       "to audit it: TAB/newline token separators are "
                       "flagged as the CVE-2026-120423 class (a "
                       "space-only verifier skips every token and "
                       "accepts tampered bodies unconditionally), "
                       "sha1/md5 and bad base64 refused by name, "
                       "wrong-length digests caught, duplicates "
                       "flagged (W3C = strongest supported wins, not "
                       "all checked). URLs audited for moving parts: "
                       "@latest and unversioned CDN paths flagged as "
                       "planned outages, @5/@5.3 ranges as warn. With "
                       "octets + attribute it VERIFIES the match locally "
                       "— honest scope note included: SRI proves bytes "
                       "are expected, never that they are safe. Free.",
        "inputSchema": {"type": "object", "properties": {
            "bytes_b64": {"type": "string",
                          "description": "strict base64 of the exact "
                                         "file bytes"},
            "text": {"type": "string",
                     "description": "UTF-8 text source (declared)"},
            "algorithms": {"type": "array", "items": {"type": "string"},
                           "description": "subset of sha256/sha384/"
                                          "sha512; default sha384"},
            "url": {"type": "string",
                    "description": "style-audited only — NEVER fetched"},
            "integrity_attr": {"type": "string",
                               "description": "attribute to audit or "
                                              "verify against octets"}}}},
    {
        "name": "date_tz_ambiguity",
        "description": "Does this LOCAL wall clock exist — and how "
                       "many times? Give a zone and a wall clock "
                       "(no offset; the offset is what is ambiguous) "
                       "and get the named verdict: single (one UTC "
                       "instant), fold (the wall clock happens TWICE "
                       "— both instants with offset and abbreviation, "
                       "PEP 495 fold rule stated), or gap (it NEVER "
                       "happens — last valid and first valid wall "
                       "clocks named). Transition minute, affected "
                       "window and direction computed live from the "
                       "installed IANA tzdata via zoneinfo — no "
                       "embedded table, no fetch. Built for cron/"
                       "scheduler questions the Nov 2026 incidents "
                       "made concrete: K8s CronJob double-ran "
                       "'30 1 * * *', cron 4.4.0 re-fired the hour "
                       "AFTER the repeat, wildcard entries fire once "
                       "per wall pass. Free.",
        "inputSchema": {"type": "object", "properties": {
            "zone": {"type": "string",
                     "description": "IANA zone, e.g. "
                                    "America/New_York (never guessed)"},
            "local": {"type": "string",
                      "description": "wall clock with no offset: "
                                     "'2026-11-01 01:30' or ISO with T"}}}},
    {
        "name": "money_flight_comp",
        "description": "Flight compensation (EC261 / UK261) decided "
                       "by the FLIGHT DATE, not the press date: "
                       "Regulation (EU) 2026/2202 applies only FROM "
                       "2027-10-23, so identical facts on two sides "
                       "of that date can pay differently (the new "
                       "Art. 6(4) threshold is 'EXCEEDING three "
                       "hours' — exactly 180 min does not pay; the "
                       "old case-law threshold was 'at least'). "
                       "Give regime (EU|UK), flight_date, event "
                       "(denied_boarding|cancellation|delay|"
                       "missed_connection), distance_km (great "
                       "circle, initial departure -> final "
                       "destination, supplied), and the event "
                       "numbers (delay_min; notice_days and "
                       "rerouting) — get band EUR 250/400/600 or "
                       "GBP 220/350/520 with the intra-Union 400 "
                       "cap named, the official under-4h long-haul "
                       "GBP 260 row, reductions rendered as the "
                       "text states them: the carrier MAY reduce "
                       "50 % (Art. 7(2)) or 50/25 % (Art. 7(3)) — "
                       "options, never silence. Table B adds the "
                       "nine-month claim deadline as an EXACT date "
                       "and the 30-day carrier answer duty. Zero "
                       "flight fetches, zero legal promises. Free.",
        "inputSchema": {"type": "object", "properties": {
            "regime": {"type": "string", "enum": ["EU", "UK"],
                       "description": "never guessed — the two "
                                      "systems pay different money"},
            "flight_date": {"type": "string",
                            "description": "YYYY-MM-DD of the "
                                           "flight; selects the "
                                           "table version"},
            "event": {"type": "string",
                      "enum": ["denied_boarding", "cancellation",
                               "delay", "missed_connection"]},
            "distance_km": {"type": "string",
                            "description": "great-circle km to the "
                                           "FINAL destination"},
            "intra_eu": {"type": "string", "enum": ["yes", "no"],
                         "description": "EU flights above 1500 km "
                                        "only — decides cap (b) vs (c)"},
            "delay_min": {"type": "string",
                          "description": "delay at arrival, minutes"},
            "notice_days": {"type": "string",
                            "description": "cancellation: days of "
                                           "advance notice"},
            "rerouted": {"type": "string", "enum": ["yes", "no"]},
            "reroute_depart_early_min": {"type": "string"},
            "reroute_arrive_late_min": {"type": "string"},
            "extraordinary": {"type": "string",
                              "enum": ["yes", "no"],
                              "description": "carrier INVOKES "
                                             "extraordinary "
                                             "circumstances (facts "
                                             "assessment, not "
                                             "arithmetic)"}}}},
    {
        "name": "date_week",
        "description": "ISO 8601 weeks, both directions, with the "
                       "year-boundary trap shown on YOUR date. "
                       "Pass 'date' → iso_year/iso_week/iso_day, "
                       "week bounds, and the live proof of the %Y-"
                       "W%V vs %G-W%V concatenation bug (formatting "
                       "2027-01-01 with the GREGORIAN year prints "
                       "'2027-W53', a week that does not exist — "
                       "2027 has 52 weeks). Pass 'iso' (YYYY-Www-d) "
                       "→ the calendar date, nonexistent weeks "
                       "REFUSED naming the theorem (a year has 53 "
                       "ISO weeks iff it contains 53 Thursdays: "
                       "Jan-1 Thursday, or Wednesday in a leap "
                       "year — computed, zero embedded tables). "
                       "Pass 'year' → weeks count, W01/W53 bounds, "
                       "January days of the previous ISO year, "
                       "neighbouring 53-week years. Excel/US "
                       "conventions (WEEKNUM 1/2, %U, %W) rendered "
                       "BESIDE ISO, never chosen for you — a "
                       "German 'KW 53' and an American 'week 2' "
                       "can name the same seven days. Platform "
                       "notes included (PostgreSQL IYYY, Snowflake "
                       "session policy, BSD strftime deviation "
                       "measured in production testing). Free.",
        "inputSchema": {"type": "object", "properties": {
            "date": {"type": "string",
                     "description": "YYYY-MM-DD — to ISO week"},
            "iso": {"type": "string",
                    "description": "YYYY-Www-d (day optional) — to "
                                   "calendar date"},
            "year": {"type": "string",
                     "description": "YYYY — how many weeks, does "
                                    "W53 exist"}}}},
    {
        "name": "money_baggage",
        "description": "Cabin baggage decided by the FLIGHT DATE, not "
                       "the press date. Reg. (EU) 2026/2202 applies "
                       "FROM 2027-10-23: before that no EU size rule "
                       "exists at all (each airline decides); from it, "
                       "exactly ONE legal edge — a personal item up "
                       "to 40x30x15 cm must be carried under the seat "
                       "FREE. The regulation sets NO size limit for "
                       "the overhead bag (The Age) and NO weight cap "
                       "for the personal item; where law is silent "
                       "the answer SAYS silent, it does not invent. "
                       "Carrier gauges are SUPPLIED arguments (the "
                       "measured 2026 table: Ryanair 40x30x20, KLM "
                       "40x30x15, easyJet 45x36x20/56x45x25…), never "
                       "fetched. Fit is compared PER DIMENSION with "
                       "rotation allowed — 40x18x30 passes a 40x30x20 "
                       "gauge while raw-order checking fails it. The "
                       "press '100 cm combined + 7 kg' reading is "
                       "returned as a tested press CLAIM (the standard "
                       "55x40x20 trolley sums to 115 cm, so that "
                       "reading would outlaw every normal cabin case "
                       "— the law does not say it), never a rule. UK "
                       "departures named out of scope. Zero fetch, "
                       "not legal advice. Free.",
        "inputSchema": {"type": "object", "properties": {
            "flight_date": {"type": "string",
                            "description": "YYYY-MM-DD — selects the "
                                           "legal stage (from 2027-"
                                           "10-23 the 40x30x15 cap)"},
            "regime": {"type": "string", "enum": ["EU", "UK", "other"],
                       "description": "follows the DEPARTURE airport "
                                      "and the operator — supplied, "
                                      "never guessed"},
            "bag": {"type": "string",
                    "description": "'LxWxH' as measured, any face "
                                   "order (rotation is checked)"},
            "bag_unit": {"type": "string", "enum": ["cm", "in"],
                         "description": "inches convert at exactly "
                                        "2.54"},
            "weight_kg": {"type": "string"},
            "personal_sizer": {"type": "string",
                               "description": "carrier's current "
                                              "personal-item gauge, "
                                              "you supply it"},
            "cabin_sizer": {"type": "string",
                            "description": "carrier's overhead gauge; "
                                           "without it and with law "
                                           "silent the verdict is "
                                           "UNDETERMINED, not 'yes'"},
            "cabin_sum_limit": {"type": "string",
                                "description": "sum limit ONLY if "
                                               "your carrier "
                                               "publishes one"},
            "cabin_weight_max": {"type": "string",
                                 "description": "carrier cap; law "
                                                "sets no weight for "
                                                "the underseat item"}}}},
    {
        "name": "csv_excel_damage",
        "description": "Before the double-click: what Excel will "
                       "SILENTLY DESTROY in this CSV, per column. "
                       "The damage happens ON OPEN and saving writes "
                       "it back — a stripped leading zero is "
                       "unrecoverable from the file (delimiter.live). "
                       "Predicts Microsoft's own three Automatic Data "
                       "Conversion toggles (Excel 365 2309+/16.77): "
                       "leading zeros (02134->2134), text-to-date "
                       "(SEPT2->2026-09-02, MARCH1->March 1 — gene "
                       "names die; '3-4' is March 4 under en but "
                       "April 3 under eu: SAME cell, TWO dates, so "
                       "locale is an argument never a guess), the "
                       "15-significant-digit wall (4111111111111111"
                       "->4111111111111110, 987654321098765432->"
                       "9.87654E+17), scientific notation (1E5->"
                       "100000), formula shapes (-5, +43, =... "
                       "injection surface), full-width digits (１２３ "
                       "compares as a different ID). A token without "
                       "a year takes the CURRENT year in Excel — so "
                       "as_of is REQUIRED here: determinism first. "
                       "Output: per-column rule counts + samples + "
                       "the prescribed import (Data>From Text/CSV "
                       "typed Text, or the toggles off, or ship "
                       ".xlsx). csv/fix REPAIRS after the fact; this "
                       "PREDICTS before it. Detection lot — the "
                       "stored-vs-displayed numFmt mask rendering "
                       "(the 88 % misled study) is the queued M "
                       "part. Free.",
        "inputSchema": {"type": "object", "properties": {
            "csv": {"type": "string",
                    "description": "the CSV text, <= 20000 chars"},
            "locale": {"type": "string", "enum": ["en", "eu"],
                       "description": "date coercion order: en reads "
                                      "m/d, eu reads d/m"},
            "as_of": {"type": "string",
                      "description": "YYYY-MM-DD freezing the year "
                                     "Excel implies for '3/4'"}}}},
    {
        "name": "money_crossover",
        "description": "Two-component tariffs (unit rate + recurring "
                       "fixed): WHERE they cross, exact. The formula "
                       "is published by seven web calculators that "
                       "contradict each other on ROUNDING: they round "
                       "the fixed delta first (19.42/0.0042 = 'about "
                       "4,623') where the exact answer is 4,623 1/3 "
                       "kWh. Here Decimal never quantizes before the "
                       "last step: the crossover ships as an EXACT "
                       "fraction plus its decimal. DAY CONVENTIONS are "
                       "named, never melted: monthly fixeds annualize "
                       "by x12 exact (not 30-day months = x360), "
                       "daily by x365 or a supplied 366 leap year; "
                       "'week' is REFUSED (no exact conversion). "
                       "DOMINATION is a rendered answer: when one plan "
                       "wins on BOTH components, 'never' comes back "
                       "named with the reason. Also: equal fixeds "
                       "(immediate crossover at zero), equal rates "
                       "(no tradeoff), distance conversion when km "
                       "per unit is SUPPLIED (EV), costs at your "
                       "usage, and one-off exit/signup fees rendered "
                       "as PAYBACK months — separate from the "
                       "structural crossover (uktaxdrag's own "
                       "distinction). Electricity, EV charging, SaaS "
                       "seats, mobile data: one kernel. Zero fetch, "
                       "no tariff advice. Free.",
        "inputSchema": {"type": "object", "properties": {
            "currency": {"type": "string",
                         "description": "ISO code (EUR, GBP, USD, "
                                        "BRL...)"},
            "a_unit_rate": {"type": "string",
                            "description": "plan A price per unit, "
                                           "major units: '0.30'"},
            "a_unit_per": {"type": "string",
                           "description": "kWh / Wh / MWh, or any "
                                          "unit matching plan B"},
            "a_fixed": {"type": "string",
                        "description": "plan A recurring fixed, '12'"},
            "a_fixed_per": {"type": "string", "enum": ["day", "month",
                                                        "year"],
                            "description": "the CONVENTION is explicit "
                                           "— 'week' refused"},
            "b_unit_rate": {"type": "string"},
            "b_unit_per": {"type": "string"},
            "b_fixed": {"type": "string"},
            "b_fixed_per": {"type": "string", "enum": ["day", "month",
                                                        "year"]},
            "days_per_year": {"type": "string",
                              "description": "'365' default, '366' "
                                             "named leap year"},
            "usage_per_period": {"type": "string",
                                 "description": "your consumption to "
                                                "compare costs at"},
            "usage_period": {"type": "string", "enum": ["month",
                                                         "year"]},
            "km_per_unit": {"type": "string",
                            "description": "supplied efficiency, e.g. "
                                           "'6' km/kWh → crossover in km"},
            "exit_fee_a": {"type": "string"},
            "exit_fee_b": {"type": "string"},
            "sign_up_a": {"type": "string"},
            "sign_up_b": {"type": "string"}}}},
    {
        "name": "csv_excel_display",
        "description": "What Excel DISPLAYS from a STORED value under "
                       "a numFmt code — the render, not the damage. "
                       "arXiv 2611.05806 measured it: cell B9 stores "
                       "1,000,000 under '$#,##0,' (the TRAILING COMMA "
                       "SCALES by a thousand) and Excel shows $1,000; "
                       "six python extractors (markitdown, openpyxl, "
                       "pandas, unstructured, calamine, Docling) all "
                       "emit the stored value — every chat assistant "
                       "and 3 of 4 coding agents tested got budget-"
                       "approved numbers the human never saw. Feed "
                       "the stored value (what your extractor gave "
                       "you) plus the format code (styles.xml); get "
                       "the display string + the rules said. Closed "
                       "subset from Microsoft's OWN symbol table with "
                       "its resolved examples replayed: '#.0,,' + "
                       "12200000 -> '12.2'; '(000)' + 12 -> '(012)'; "
                       "'0%' + 0.5 -> '50%'; '0.00 \"dollars\"' + 1.23 "
                       "-> '1.23 dollars'; '#.##' + 8.9 -> '8.9'; "
                       "display rounding half-away-from-zero (2.5 "
                       "under '0' -> 3) — and the stored value NEVER "
                       "changes, only the display. Separators are "
                       "SYMBOLS in the file (Microsoft states content "
                       "is locale-invariant): pass the locale you "
                       "display in and '1234567.891' under '#,##0.00' "
                       "becomes 1.234.567,89 in de-DE. REFUSED by "
                       "name: General (column-width dependent), "
                       "E-notation, date/time codes, [Red], [<] "
                       "conditions, * fill, _ skip, @ text. Free.",
        "inputSchema": {"type": "object", "properties": {
            "value": {"type": "string",
                      "description": "the STORED number as extracted, "
                                     "e.g. '1000000' or "
                                     "'25604.880000000001'"},
            "format": {"type": "string",
                       "description": "the numFmt code, e.g. "
                                      "'$#,##0,' or '#,##0.00'"},
            "locale": {"type": "string",
                       "description": "display locale for separators "
                                      "(closed table), default en-US"}}}},
    {
        "name": "table_sql_dump",
        "description": "CSV/JSON rows into executable CREATE TABLE + "
                       "INSERT with the rules SAID, not assumed. Per "
                       "column: type (INTEGER|REAL|TEXT closed set) + "
                       "reason + sample; leading zeros stay TEXT ('007' "
                       "is an identifier), no exponent, int64 enforced "
                       "(never wrapped), mixed columns widen and report "
                       "mixed. Dialect-exact quoting: identifiers refuse "
                       "anything outside the closed grammar (injection "
                       "surface zero), mysql doubles backslashes, all "
                       "three double ''. NUL bytes refused by name. "
                       "Oracle: the sqlite dump reloads into sqlite3 and "
                       "re-queries equal to the input. 🟡 above 32 KB.",
        "inputSchema": {"type": "object", "properties": {
            "csv": {"type": "string"},
            "rows": {"type": "array", "items": {"type": "object"}},
            "table": {"type": "string", "default": "data"},
            "dialect": {"type": "string",
                        "enum": ["sqlite", "postgres", "mysql"],
                        "default": "sqlite"},
            "create": {"type": "boolean", "default": True},
            "if_not_exists": {"type": "boolean", "default": True},
            "rows_per_statement": {"type": "integer", "default": 100},
            "empty_as_null": {"type": "boolean", "default": False},
            "types": {"type": "object"},
            "delimiter": {"type": "string"}}}},
    {
        "name": "table_scale",
        "description": "Recipe and formula scaling that can't silently "
                       "round: every line answers THREE times — exact "
                       "product as a reduced fraction (1/3 of 400 g is "
                       "133 1/3 g, never '133' or '130' by mood), the "
                       "MEASURABLE amount at the nearest real measuring "
                       "step for its ingredient class (kitchen-steps-v1, "
                       "the step table shipped in the response), and the "
                       "percent delta between them. The multiplier is "
                       "STATED ONCE: servings 6->15 is 5/2 = 2.5, reduced "
                       "and echoed. Eggs that land on halves come with "
                       "the beaten-grams alternative (5 eggs /2 = 2 1/2 = "
                       "3 whole OR 125 g — the NYT-Cooking-AI silent "
                       "'3 eggs' failure, stated instead). Units and "
                       "classes are closed sets; vague 'pinch'/'handful' "
                       "REFUSED BY NAME (the 500-guests = 12.5 lb salt "
                       "failure mode); salt/spice/leavening scale "
                       "LINEARLY and say so — a sub-linear factor is "
                       "applied only when the CALLER passes power=. "
                       "Exact Fractions, zero float. Free forever.",
        "inputSchema": {"type": "object", "properties": {
            "items": {"type": "array", "items": {"type": "object",
                       "properties": {
                           "name": {"type": "string"},
                           "qty": {"type": "string"},
                           "unit": {"enum": ["g", "kg", "oz", "lb",
                                             "ml", "l", "tsp", "tbsp",
                                             "cup", "piece"]},
                           "class": {"enum": ["base", "salt", "spice",
                                              "leavening", "yeast",
                                              "egg"]},
                           "power": {"type": "string"}}}},
            "factor": {"type": "string"},
            "servings_from": {"type": "string"},
            "servings_to": {"type": "string"},
            "power_default": {"type": "string"}},
            "required": ["items"]}},
    {
        "name": "check_format",
        "description": "Validate the formats JSON Schema CANNOT express: "
                       "a string field passes 'type: string' whether it "
                       "holds 2026-02-30, v1.2..3 or '1,234.56' where a "
                       "decimal-string was meant — the hidden-schema trap "
                       "that burns agent pipelines three systems later. "
                       "payload + formats map ($-path → format, wildcards "
                       "ok) over a CLOSED, cited set: date-iso/datetime-iso/"
                       "time-iso (RFC 3339, real calendar, leap second "
                       "allowed), semver (official grammar), uuid, "
                       "sha256-hex, hex-color, slug, decimal-string, e164, "
                       "email, url, currency-iso, country-iso, "
                       "json-pointer (RFC 6901). Every violation: path, "
                       "offending value, why, expected — the error is the "
                       "repair prompt. Unknown format names are refused "
                       "with the full closed set. Free.",
        "inputSchema": {"type": "object", "properties": {
            "payload": {"description": "any JSON document"},
            "formats": {"type": "object",
                        "description": "e.g. {\"$.due\": \"date-iso\"}"}},
            "required": ["payload", "formats"]}},
    {
        "name": "csv_money_columns",
        "description": "Read a financial CSV without EVER guessing a lone "
                       "value: the decimal convention must be PROVEN by "
                       "the column's own unambiguous cells. '1.234' reads "
                       "as 1.234 in a column that shows 1,234.56 and as "
                       "1234 in one that shows 1.234,56 — each resolution "
                       "traced with its evidence count; a column proving "
                       "BOTH styles is CONTRADICTORY and every ambiguous "
                       "value there is refused with its two readings "
                       "(needs_human), never coin-flipped — the $100.50 "
                       "read as $10,050 class of bug made structurally "
                       "impossible. Delimiter sniffed by recurrence "
                       "across lines (csv.Sniffer semantics), thousands "
                       "commas rejoined only when declared, real "
                       "qty,price tables left untouched. Reports "
                       "max_reading_gap_x — how big the trap was. Free "
                       "under 32 KB (🟡).",
        "inputSchema": {"type": "object", "properties": {
            "csv": {"type": "string"},
            "columns": {"type": "array",
                        "items": {"type": "string"},
                        "description": "names or indices; default all"},
            "delimiter": {"type": "string"}},
            "required": ["csv"]}},
    {
        "name": "date_relative",
        "description": "Relative-date phrases in human words → exact ISO, "
                       "EN/FR/PT closed grammar: today/demain/amanha, "
                       "[this|next|last] <weekday>, in N days/weeks/months/"
                       "years, N units ago, start|end of week|month|year, "
                       "+ declared time-of-day map (morning=09:00, "
                       "tonight=21:00…). now is an ARGUMENT (echoed as "
                       "now_used): same phrase + same now = same answer "
                       "forever. ISO-week rules stated in reading_notes; "
                       "'this Friday' said on a Friday returns BOTH "
                       "readings (ambiguity reported, never decided); "
                       "anything outside the grammar is refused by name — "
                       "normalizing messy prose to the grammar stays the "
                       "model's job, the calendar math becomes ours. "
                       "Answers the #1 complaint of every local-model "
                       "forum. Free.",
        "inputSchema": {"type": "object", "properties": {
            "phrase": {"type": "string"},
            "now": {"type": "string", "description": "ISO-8601 anchor; "
                     "omit = current UTC (echoed)"},
            "tz": {"type": "string", "description": "IANA zone applied "
                   "to now"}},
            "required": ["phrase"]}},
    {
        "name": "text_url_canonical",
        "description": "RFC 3986 §6.2.2 syntax-based URL canonicalization "
                       "where EVERY transformation is listed in the "
                       "response: scheme/host case, default port, "
                       "dot-segments (§5.2.4 algorithm), percent-encoding "
                       "(uppercase hex + unreserved decode — structural "
                       "%26 stays encoded, on purpose), IDN host → punycode "
                       "(RFC 3492). Tracking params (utm_*, gclid, fbclid, "
                       "msclkid, mc_*, _hs*, igshid — published names from "
                       "platform docs) removed only when asked, each "
                       "removal NAMED. Query order preserved by default — "
                       "it is data; sort_params is an explicit opt-in. The "
                       "canonical URL you can explain. Free.",
        "inputSchema": {"type": "object", "properties": {
            "url": {"type": "string"},
            "strip_tracking": {"type": "boolean", "default": True},
            "sort_params": {"type": "boolean", "default": False},
            "drop_fragment": {"type": "boolean", "default": False}},
            "required": ["url"]}},
    {
        "name": "xml_to_json",
        "description": "XML to JSON where the conversion rules are PRINTED "
                       "IN THE RESPONSE (every other converter takes six "
                       "decisions silently). attributes=@name, mixed text="
                       "#text, empty=null, repeated siblings=array, and "
                       "force_array pins a path to array at cardinality 1 "
                       "— the one-item bug that passes tests with three "
                       "fixtures and throws in production with one. "
                       "Namespace prefixes kept raw; DTD refused by name "
                       "(no XXE surface ever); coerce=true converts only "
                       "unambiguous numbers — 00713 stays a string, "
                       "because it is an identifier. Free under 32 KB (🟡).",
        "inputSchema": {"type": "object", "properties": {
            "xml": {"type": "string", "description": "document text"},
            "force_array": {"type": "array", "items": {"type": "string"},
                            "description": "slash paths, e.g. "
                                           "\"catalog/book\" — always "
                                           "arrays"},
            "coerce": {"type": "boolean"}},
            "required": ["xml"]}},
    {
        "name": "web_cert",
        "description": "X.509 certificate lint from PEM text, pure stdlib: "
                       "subject/issuer, serial, validity window, signature "
                       "algorithm with deprecation flags (SHA-1/MD5 named), "
                       "SANs (dns/email/ip/uri), basicConstraints, EKUs, "
                       "chain SHAPE (name-matching, not trust), warnings "
                       "(expiring <14d, leaf without SAN, legacy versions). "
                       "Time is an argument: pass as_of and the verdict "
                       "replays forever; omit it and the chosen instant is "
                       "echoed in evaluated_at. Parsed, NOT "
                       "signature-verified — the response says so. Free "
                       "under 32 KB (🟡).",
        "inputSchema": {"type": "object", "properties": {
            "pem": {"type": "string",
                    "description": "PEM block(s), one or a chain"},
            "as_of": {"type": "string",
                      "description": "ISO date/datetime fixing the "
                                     "expiry verdict"}},
            "required": ["pem"]}},
    {
        "name": "id_checkdigit",
        "description": "Check digits for the identifiers a model guesses: "
                       "15 published schemes (ISBN-10/13, EAN-8/13, UPC-A, "
                       "GTIN-14, ISSN, ISIN, CUSIP, SEDOL, ABA, LEI, ORCID, "
                       "CAS, Luhn-family via ISIN, Verhoeff, Damm), each "
                       "cited to its spec. check: auto-detect returns EVERY "
                       "format that matches with its own verdict — a valid "
                       "Bookland number is both ean13 and isbn13 and the "
                       "ambiguity is reported, never guessed; a wrong check "
                       "digit comes back with the expected character. "
                       "generate: payload in, valid identifier out. repair: "
                       "every single-character edit that makes the value "
                       "valid. scan: finds and verifies identifiers in free "
                       "text. Generic schemes (verhoeff, damm) need an "
                       "explicit scheme= — they would pass any digit "
                       "string 10 % of the time. Free.",
        "inputSchema": {"type": "object", "properties": {
            "mode": {"type": "string",
                     "enum": ["check", "generate", "repair", "scan"]},
            "value": {"type": "string",
                      "description": "identifier (check/repair) or payload "
                                     "(generate)"},
            "scheme": {"type": "string",
                       "description": "closed list: isbn10 isbn13 ean8 "
                                      "ean13 upca gtin14 issn isin cusip "
                                      "sedol aba lei orcid cas verhoeff "
                                      "damm; omit to auto-detect"},
            "text": {"type": "string",
                     "description": "scan mode: free text up to 20 000 "
                                    "chars"}},
            "required": []}},
    {
        "name": "image_rightsize",
        "description": "Deterministic PNG resize in pure stdlib: exact "
                       "area-average box (integer weights), centre-aligned "
                       "bilinear/nearest — no float ever touches a sample, "
                       "same bytes forever. fit/cover/stretch geometry via "
                       "Fraction scale factors. Palette/16-bit/alpha all "
                       "stay honest; Adam7 and corrupt CRC refused by name. "
                       "JPEG/WebP deliberately out of contract. Free under "
                       "32 KB payload, x402 above.",
        "inputSchema": {"type": "object", "properties": {
            "data_b64": {"type": "string",
                         "description": "source PNG, base64"},
            "width": {"type": "integer"},
            "height": {"type": "integer"},
            "mode": {"type": "string", "enum": ["fit", "cover",
                                                "stretch"]},
            "resample": {"type": "string",
                         "enum": ["box", "bilinear", "nearest"]}},
            "required": ["data_b64"]}},
    {
        "name": "money_rates",
        "description": "Today's OFFICIAL reference rates (ECB daily feed, "
                       "https only, one fetch per reference day, in-memory "
                       "cache) plus a 90-day archive of the true published "
                       "days: pass date=YYYY-MM-DD for history, none for "
                       "latest. Weekend/holiday dates get a named refusal, "
                       "never a silent snap. Crosses computed through EUR "
                       "in Decimal. Pair with /api/v1/num/fx, which stays "
                       "pure: fresh rate here, deterministic conversion "
                       "there. Free.",
        "inputSchema": {"type": "object", "properties": {
            "date": {"type": "string",
                     "description": "YYYY-MM-DD reference day or omit "
                                    "for latest"},
            "from": {"type": "string"},
            "to": {"type": "string"},
            "amount": {"type": "string"}}}},
    {
        "name": "doc_text",
        "description": "PDF to text, pure stdlib: FlateDecode, TJ/Tj "
                       "operators, ToUnicode CMaps (real producers "
                       "included), latin-1 fidelity, honest verdicts — "
                       "image-only says 'no text layer', encrypted says "
                       "decryption is out of scope, never a confident "
                       "garbage. Same bytes in, same text out, forever. "
                       "Free under 32 KB, $0.001 above (x402 on Base).",
        "inputSchema": {"type": "object", "properties": {
            "pdf_b64": {"type": "string"},
            "page": {"type": "integer", "minimum": 1}},
            "required": ["pdf_b64"]}},
    {
        "name": "money_amortize",
        "description": "Full amortization schedule on Decimal: constant "
                       "annuity, exact monthly interest, last line "
                       "absorbs rounding so balance hits 0.00 EXACTLY, "
                       "zero-rate branch handled without division. Every "
                       "total re-derives from its own rows. Free.",
        "inputSchema": {"type": "object", "properties": {
            "principal": {"type": "number"},
            "annual_rate_pct": {"type": "number"},
            "months": {"type": "integer", "minimum": 1, "maximum": 600}},
            "required": ["principal", "annual_rate_pct", "months"]}},
    {
        "name": "money_interest",
        "description": "Compound interest + effective annual rate, closed "
                       "form A = P(1 + r/m)^(mt), Decimal throughout, "
                       "formula echoed in the answer so the caller can "
                       "audit it. No rate is ever invented: all inputs "
                       "are arguments. Free.",
        "inputSchema": {"type": "object", "properties": {
            "principal": {"type": "number"},
            "annual_rate_pct": {"type": "number"},
            "years": {"type": "number"},
            "compounds_per_year": {"type": "integer",
                                   "minimum": 1, "maximum": 365}},
            "required": ["principal", "annual_rate_pct", "years"]}},
    {
        "name": "ics_validate",
        "description": "RFC 5545 lint with the spec's own severity: MUSTs "
                       "as errors (component pairing and nesting, required "
                       "properties per §3.6, DTSTART/DTEND type agreement "
                       "and order, VERSION), SHOULDs as warnings (floating "
                       "times, long physical lines). Nothing invented — a "
                       "clean verdict here means a strict client accepts "
                       "it. Free.",
        "inputSchema": {"type": "object",
                        "properties": {"text": {"type": "string"}},
                        "required": ["text"]}},
    {
        "name": "schedule_holidays",
        "description": "National legal holiday calendars FR BR PT DE US: "
                       "every day cites its statute (L3133-1, Lei 662, "
                       "CT 234o, 5 USC 6103 with the weekend-observance "
                       "shift), Easter from the Gregorian computus "
                       "verified against the US Census table for all of "
                       "2000-2099. Pass `on` for a yes/no verdict. "
                       "Regional extras declared, never invented. Free.",
        "inputSchema": {"type": "object", "properties": {
            "country": {"type": "string",
                        "enum": ["FR", "BR", "PT", "DE", "US"]},
            "year": {"type": "integer", "minimum": 1900, "maximum": 2099},
            "on": {"type": "string"}},
            "required": ["country"]}},
    {
        "name": "web_cache",
        "description": "Cache-Control verdict from header text alone: "
                       "known vs inert-unknown directives, freshness math, "
                       "the single action a compliant RFC 9111 cache must "
                       "take. Answers 'will this be re-fetched?' without "
                       "a browser. Free.",
        "inputSchema": {"type": "object", "properties": {
            "header": {"type": "string"},
            "method": {"type": "string"},
            "conditional": {"type": "boolean"}},
            "required": ["header"]}},
    {
        "name": "gzip_roundtrip",
        "description": "Deterministic gzip: MTIME=0, no FNAME (RFC 1952), "
                       "so identical inputs yield identical archive bytes "
                       "on every machine — the stdlib default embeds a "
                       "wall-clock mtime and cannot promise that. Compress "
                       "and decompress, base64 both ways. Free under 8 MB.",
        "inputSchema": {"type": "object", "properties": {
            "payload_b64": {"type": "string"},
            "mode": {"type": "string",
                     "enum": ["compress", "decompress"]},
            "level": {"type": "integer", "minimum": 1, "maximum": 9}},
            "required": ["payload_b64"]}},
    {
        "name": "qr_generate",
        "description": "Complete ISO 18004 encoder, pure stdlib: text -> "
                       "version 1-10 QR, numeric/alphanumeric/byte mode "
                       "chosen by charset, ECL L/M/Q/H, auto mask by "
                       "published penalties. Returns the exact matrix plus "
                       "a deterministic SVG (same text, same bytes, "
                       "forever — proof it decodes is OpenCV-roundtripped "
                       "in the tests). Free.",
        "inputSchema": {"type": "object", "properties": {
            "text": {"type": "string"},
            "ecl": {"type": "string", "enum": ["L", "M", "Q", "H"]},
            "version": {"type": "integer", "minimum": 1, "maximum": 10},
            "scale": {"type": "integer", "minimum": 1, "maximum": 24},
            "quiet": {"type": "integer", "minimum": 0, "maximum": 16},
            "format": {"type": "string", "enum": ["svg", "matrix"]}},
            "required": ["text"]}},
    {
        "name": "table_peek",
        "description": "Column profile of a JSON table: closed classifier "
                       "(integer decimal date-iso boolean string empty), "
                       "nulls, uniques, numeric and date bounds. Counting, "
                       "not NLP — mixed shapes say mixed. Free.",
        "inputSchema": {"type": "object", "properties": {
            "rows": {"type": "array", "items": {"type": "object"}}},
            "required": ["rows"]}},
    {
        "name": "csv_diff",
        "description": "Row-level diff by key: added, removed, changed with "
                       "per-field left/right values, same_count. Duplicate "
                       "keys refused rather than collapsed. The answer to "
                       "\u201cwhat actually changed between these two "
                       "exports?\u201d Free.",
        "inputSchema": {"type": "object", "properties": {
            "left": {"type": "array", "items": {"type": "object"}},
            "right": {"type": "array", "items": {"type": "object"}},
            "key": {"anyOf": [{"type": "string"},
                              {"type": "array",
                               "items": {"type": "string"}}]}},
            "required": ["left", "right", "key"]}},
    {
        "name": "ssh_fingerprint",
        "description": "SSH public key line -> SHA256 and MD5 fingerprints "
                       "exactly as ssh-keygen formats them, comment and "
                       "type-field cross-check included. Anchored to the "
                       "real binary's output, not to a recomputation. Free.",
        "inputSchema": {"type": "object",
                        "properties": {"line": {"type": "string"}},
                        "required": ["line"]}},
    {
        "name": "zip_verify",
        "description": "Archive integrity without extraction: base64 zip "
                       "in, per-entry listing with stored-vs-computed CRC32, "
                       "encrypted flags, archive sha256. Nothing touches "
                       "disk. Free under 32 MB.",
        "inputSchema": {"type": "object",
                        "properties": {"blob_b64": {"type": "string"}},
                        "required": ["blob_b64"]}},
    {
        "name": "crypto_address",
        "description": "Multi-chain address validation: base58check "
                       "(P2PKH/P2SH), bech32/bech32m segwit v0-v16 "
                       "(BIP-173/350 rules incl. v0-length and encoding "
                       "cross-checks), EVM EIP-55. Pure-python RIPEMD-160 "
                       "against the official vectors so verdicts never "
                       "depend on the OpenSSL build. Validation only. Free.",
        "inputSchema": {"type": "object", "properties": {
            "address": {"type": "string"},
            "chain": {"type": "string",
                      "enum": ["auto", "bitcoin", "litecoin", "eth",
                               "evm", "base", "polygon"]}},
            "required": ["address"]}},
    {
        "name": "validate_taxid",
        "description": "Tax id check digits, exact: CNPJ/CPF (Receita "
                       "mod-11), SIREN/SIRET (INSEE Luhn + the documented "
                       "La Poste branch), NIF PT, VAT DE/FR/IT/NL/LU. "
                       "Ambiguous 14-digit shape is REPORTED, never guessed. "
                       "Free.",
        "inputSchema": {"type": "object", "properties": {
            "value": {"type": "string"},
            "kind": {"type": "string",
                     "enum": ["auto", "cnpj", "cpf", "siren", "siret",
                              "nif_pt", "vat_de", "vat_fr", "vat_it",
                              "vat_nl", "vat_lu"]},
        }, "required": ["value"]}},
    {
        "name": "caip",
        "description": "CAIP-2 / CAIP-10 chain identifiers: parse "
                       "eip155:8453 or 0x…@eip155:8453 (and format them) "
                       "with published chain tables, EIP-55 checksummed "
                       "addresses, base58 solana gates. The exact strings "
                       "x402 payments speak — validated without a node. "
                       "Free.",
        "inputSchema": {"type": "object", "properties": {
            "value": {"type": "string"},
            "mode": {"type": "string", "enum": ["parse", "format"],
                     "default": "parse"},
            "namespace": {"type": "string"},
            "reference": {"type": "string"},
            "address": {"type": "string"}}}},
    {
        "name": "secret_scan",
        "description": "Leak gate for agent output: 24 published secret "
                       "formats (OpenAI/GitHub/AWS/Slack/Stripe/Google/"
                       "Discord/Telegram keys, private-key blocks, JWT), "
                       "Luhn-verified cards with brand, mod-97 IBAN, and "
                       "BIP39 seeds checked with the REAL checksum "
                       "(published vectors in tests). Previews only — "
                       "the value never echoes. Free.",
        "inputSchema": {"type": "object", "required": ["text"],
                        "properties": {"text": {"type": "string"},
                                       "kinds": {"type": "array"}}}},
    {
        "name": "text_redact",
        "description": "Mask before you post: secrets become [APIKEY_1], "
                       "[VISA_1]... numbered by position, so the same "
                       "text always gets the same mask. The mapping is "
                       "NOT returned on purpose — a redaction endpoint "
                       "that echoes secrets is a leak with extra steps. "
                       "Free.",
        "inputSchema": {"type": "object", "required": ["text"],
                        "properties": {"text": {"type": "string"},
                                       "mask_tag": {"type": "string"}}}},
    {
        "name": "validate_country",
        "description": "ISO 3166-1 lookup as ONE call: alpha-2 -> "
                       "alpha-3, numeric, official name, ISO-4217 "
                       "currency + decimal places, calling code. Codes "
                       "outside the shipped subset get an honest "
                       "edge-of-table verdict, never a fake invalid. "
                       "Free.",
        "inputSchema": {"type": "object", "required": ["code"],
                        "properties": {"code": {"type": "string"}}}},
    {
        "name": "validate_postal",
        "description": "Postal-code grammar by country (54 shipped "
                       "patterns): valid + canonical spacing (BR CEP, "
                       "CA A1A 1A1, NL 1234 AB, JP, PT) + the regex on "
                       "failure. Structure check, not a postcode oracle "
                       "— the verdict says which. Free.",
        "inputSchema": {"type": "object", "required": ["code", "country"],
                        "properties": {
                            "code": {"type": "string"},
                            "country": {"type": "string"}}}},
    {
        "name": "geo_distance",
        "description": "Great-circle distance (haversine, published mean "
                       "radius): point-to-point km/miles, or an ORDERED "
                       "route summed leg by leg. Agents average coordinates"
                       " in prose and drift 3 digits; this matches the "
                       "published Paris-London 343.5 km. Free.",
        "inputSchema": {"type": "object",
                        "properties": {
                            "a": {"type": "object"},
                            "b": {"type": "object"},
                            "route": {"type": "array"}}}},
    {
        "name": "geo_geohash",
        "description": "Geohash encode/decode on the published algorithm "
                       "(base32 without a i l o, reproduced spec example "
                       "42.6,-5.6 -> ezs42 in the test suite). decode "
                       "returns centre + bounding box at the hash "
                       "precision. Free.",
        "inputSchema": {"type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lon": {"type": "number"},
                            "geohash": {"type": "string"},
                            "precision": {"type": "integer",
                                          "default": 6}}}},
    {
        "name": "file_identify",
        "description": "What this blob REALLY is: closed magic-bytes "
                       "table (22 signatures: png/zip/gz/pdf/mp3/sqlite/"
                       "elf...), longest-match wins, printable-text "
                       "heuristic gated at 80%, and an honest 'unknown' "
                       "with the first 16 bytes hex when nothing matches. "
                       "The name lies; the header does not. Free.",
        "inputSchema": {"type": "object", "required": ["blob"],
                        "properties": {"blob": {
                            "type": "string",
                            "description": "base64 of the bytes"}}}},
    {
        "name": "text_punycode",
        "description": "IDN domains both ways: unicode <-> xn-- via the "
                       "exact stdlib RFC-3492 reference. Phishing "
                       "inspection (is this homoglyph domain the same "
                       "after encoding?) and agent link hygiene. Free.",
        "inputSchema": {"type": "object", "required": ["domain"],
                        "properties": {"domain": {"type": "string"}}}},
    {
        "name": "semver_parse",
        "description": "Parse a semantic version with the OFFICIAL semver"
                       " .org grammar: major/minor/patch, prerelease "
                       "identifiers, build metadata, stability verdict. "
                       "Free.",
        "inputSchema": {"type": "object", "required": ["version"],
                        "properties": {"version": {"type": "string"}}}},
    {
        "name": "semver_sort",
        "description": "Sort versions by semver PRECEDENCE (rule 11), not "
                       "alphabet: 10.0.0 > 2.0.0, prerelease < release, "
                       "numeric identifiers ordered numerically. Agents "
                       "pick the wrong 'latest' daily; this one cannot.",
        "inputSchema": {"type": "object", "required": ["versions"],
                        "properties": {"versions": {
                            "type": "array",
                            "items": {"type": "string"}}}}},
    {
        "name": "text_sanitize",
        "description": "Cross-OS safe filenames: reserved device names "
                       "(CON/NUL/COM1-9), forbidden charset, trailing "
                       "dots/spaces, utf-8 byte budget. Verdict + WHY it "
                       "changed, never a silent rename. Free.",
        "inputSchema": {"type": "object", "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "sep": {"type": "string", "default": "_"},
                            "max_bytes": {"type": "integer",
                                          "default": 255}}}},
    {
        "name": "json_map",
        "description": "Element-wise closed transforms over a JSON array: "
                       "12 ops (lower/upper/strip/title/slug/kebab/snake/"
                       "camel/round/int/str/trunc), applied in order. The "
                       "missing half of reshape for lists of scalars. Free.",
        "inputSchema": {"type": "object", "required": ["items", "ops"],
                        "properties": {
                            "items": {"type": "array"},
                            "ops": {"type": "array", "items": {
                                "type": "object",
                                "properties": {
                                    "op": {"type": "string", "enum": [
                                        "lower", "upper", "strip", "title",
                                        "slug", "kebab", "snake", "camel",
                                        "round", "int", "str", "trunc"]},
                                    "places": {"type": "integer"},
                                    "max": {"type": "integer"}}}}}}},
    {
        "name": "num_fx",
        "description": "Explicit-rate currency math: the CALLER supplies "
                       "the rate, the suite multiplies in exact Decimal "
                       "and rounds to ISO-4217 minor units (closed table "
                       "of 33 currencies, half_even). No network, no "
                       "guessing today's EUR/USD — that guess is the bug "
                       "this refuses to serve. Free.",
        "inputSchema": {"type": "object", "required": ["amount", "rate",
                                                       "to"],
                        "properties": {
                            "amount": {"type": "string"},
                            "rate": {"type": "string"},
                            "to": {"type": "string"},
                            "precision": {"type": "integer"}}}},
    {
        "name": "hash_hmac",
        "description": "RFC 2104 HMAC sign & verify over a closed algo set"
                       ". Sign a payload with a shared key; verify by "
                       "passing signature -> constant-time match. The "
                       "webhook trust primitive for agents. Free.",
        "inputSchema": {"type": "object", "required": ["message", "key"],
                        "properties": {
                            "message": {"type": "string"},
                            "key": {"type": "string"},
                            "algo": {"type": "string", "enum": [
                                "md5", "sha1", "sha224", "sha256",
                                "sha384", "sha512"], "default": "sha256"},
                            "key_kind": {"type": "string", "enum": [
                                "text", "hex", "base64"], "default": "text"},
                            "message_kind": {"type": "string", "enum": [
                                "text", "hex", "base64"], "default": "text"},
                            "signature": {"type": "string"}}}},
    {
        "name": "hash_digest",
        "description": (
            "Digests (md5/sha1/sha256/sha512/blake2b) over text, base64 or "
            "hex input. A model cannot hash and will confidently fake one - "
            "this is the call that replaces that failure. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["data"],
            "properties": {
                "data": {"type": "string"},
                "algo": {"type": "string",
                         "enum": ["md5", "sha1", "sha256", "sha512",
                                  "blake2b"], "default": "sha256"},
                "input_kind": {"type": "string",
                               "enum": ["text", "base64", "hex"],
                               "default": "text"},
            },
        },
    },
    {
        "name": "enc_base64",
        "description": (
            "base64 / base64url / hex, encode or decode, strict (garbage "
            "refused, never silently lenient), padding optional. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string"},
                "op": {"type": "string", "enum": ["encode", "decode"],
                       "default": "encode"},
                "variant": {"type": "string",
                            "enum": ["base64", "base64url", "hex"],
                            "default": "base64"},
                "padding": {"type": "boolean", "default": True},
            },
        },
    },
    {
        "name": "jwt_decode",
        "description": (
            "JWT header + claims + signature exposed, decoded only - never "
            "verified (verified=false is stated). iat/exp/nbf also as ISO. "
            "Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["token"],
            "properties": {"token": {"type": "string"}},
        },
    },
    {
        "name": "id_uuid",
        "description": (
            "Deterministic UUIDs: v5 (namespace+name), v4_seeded (seed "
            "string), v7 (explicit 'at' required - wall clock refused so "
            "replays stay byte-identical). Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["op"],
            "properties": {
                "op": {"type": "string",
                       "enum": ["v5", "v4_seeded", "v7"], "default": "v5"},
                "name": {"type": "string"},
                "namespace": {"type": "string", "default": "url",
                              "description": "url|dns|oid|x500 or UUID"},
                "seed": {"type": "string"},
                "at": {"description": "v7: ms epoch or ISO instant"},
            },
        },
    },
    {
        "name": "id_slug",
        "description": (
            "Title -> url-safe slug: NFKD transliteration, separators "
            "collapsed, optional word-boundary max_len cut. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string"},
                "sep": {"type": "string", "enum": ["-", "_"],
                        "default": "-"},
                "lower": {"type": "boolean", "default": True},
                "max_len": {"type": "integer", "default": 0,
                            "description": "0 = unlimited"},
            },
        },
    },
    {
        "name": "fingerprint",
        "description": (
            "Canonical fingerprint of JSON (keys sorted at every depth) or "
            "CSV (header-aligned records): the stable cache key. Returns "
            "sha256 + canonical text (json). Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["value"],
            "properties": {
                "value": {"description": "any JSON, or CSV text for csv"},
                "kind": {"type": "string", "enum": ["json", "csv"],
                         "default": "json"},
            },
        },
    },
    {
        "name": "validate_iban",
        "description": (
            "IBAN check: closed country table (61), per-country BBAN "
            "structure, mod-97 — plus country/bban/checksum pieces. Bad "
            "numbers arrive at 400 check_failed, never a soft 200. Paid "
            "($0.0005): money-moving trust is the tier rule."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["iban"],
            "properties": {"iban": {"type": "string"}},
        },
    },
    {
        "name": "validate_phone",
        "description": (
            "Phone -> E.164: punctuation stripped, 00/+/national forms "
            "accepted, closed dial-code table with per-country digit "
            "ranges. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["phone"],
            "properties": {
                "phone": {"type": "string"},
                "default_country": {"type": "string",
                                    "description": 'cc, e.g. "FR"'},
            },
        },
    },
    {
        "name": "validate_email",
        "description": (
            "Structural email check (closed atom set, dot rules, punycode-"
            "ready domain, alphabetic TLD) + lowercased normalized form. "
            "No DNS, no claim of existence. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["email"],
            "properties": {"email": {"type": "string"}},
        },
    },
    {
        "name": "validate_url",
        "description": (
            "URL components + canonical form: IDN->punycode, default port "
            "dropped, path normpath, userinfo password masked. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["url"],
            "properties": {"url": {"type": "string"}},
        },
    },
    {
        "name": "color_check",
        "description": (
            "Color -> hex/rgb/hsl + relative luminance, and WCAG contrast "
            "ratio + AA/AAA pass flags when 'against' is given. #767676 "
            "vs white = 4.54, the boundary everyone gets wrong. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["color"],
            "properties": {
                "color": {"type": "string",
                          "description": "#rgb | #rrggbb | rgb(r,g,b)"},
                "against": {"type": "string"},
            },
        },
    },
    {
        "name": "text_count",
        "description": (
            "The exact counts for one text in one call: chars, words, "
            "sentences, paragraphs, lines, bytes. Never let a model "
            "'estimate' a length again. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text"],
            "properties": {"text": {"type": "string"}},
        },
    },
    {
        "name": "sort_natural",
        "description": (
            "Human-order sort (file2 before file10) over strings, stable, "
            "with the exact permutation index so you can reapply it "
            "elsewhere. A model misorders lists past ~30 items — this "
            "can't. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["items"],
            "properties": {
                "items": {"type": "array", "items": {"type": "string"}},
                "reverse": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "text_case",
        "description": (
            "Case conversion both directions: snake/kebab/camel/pascal/"
            "title/upper/lower/sentence, word-boundary aware "
            "(parseHTTPResponseCode -> parse_http_response_code). Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string"},
                "op": {"type": "string",
                       "enum": ["snake", "kebab", "camel", "pascal",
                                "title", "upper", "lower", "sentence"],
                       "default": "snake"},
            },
        },
    },
    {
        "name": "text_truncate",
        "description": (
            "Truncate to N chars/words/sentences at a real boundary "
            "(cut|word|sentence strategy) with configurable ellipsis — "
            "the exact tool behind every 'summarize in 200 words' that a "
            "model overshoots. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text", "max"],
            "properties": {
                "text": {"type": "string"},
                "max": {"type": "integer"},
                "unit": {"type": "string",
                         "enum": ["chars", "words", "sentences"],
                         "default": "chars"},
                "strategy": {"type": "string",
                             "enum": ["cut", "word", "sentence"],
                             "default": "word"},
                "ellipsis": {"type": "string", "default": "…"},
            },
        },
    },
    {
        "name": "regex_test",
        "description": (
            "Run a regex against text without executing anything in your "
            "own process: test/findall (text+span)/groups (named+numbered)"
            "/replace (template with backrefs). Flags closed to imsxua; "
            "64 KB input cap. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["pattern", "text"],
            "properties": {
                "pattern": {"type": "string"},
                "text": {"type": "string"},
                "flags": {"type": "string", "default": "u"},
                "mode": {"type": "string",
                         "enum": ["test", "findall", "groups", "replace"],
                         "default": "test"},
                "template": {"type": "string"},
                "count": {"type": "integer", "default": 0},
            },
        },
    },
    {
        "name": "text_chunk",
        "description": (
            "Exact token-budget chunking with the REAL tokenizer "
            "(cl100k/o200k/o250k/p50k/gpt2), sentence/paragraph units, "
            "overlap that cannot reach the budget, char offsets, hard "
            "cuts flagged. The flagship: $0.001 per call — RAG pipelines "
            "are the heavy industry that funds the free tools."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string"},
                "budget": {"type": "integer", "default": 512},
                "overlap": {"type": "integer", "default": 0},
                "encoding": {"type": "string",
                             "enum": ["cl100k_base", "o200k_base",
                                      "o250k_base", "p50k_base", "gpt2"],
                             "default": "cl100k_base"},
                "unit": {"type": "string",
                         "enum": ["sentence", "paragraph"],
                         "default": "sentence"},
            },
        },
    },
    {
        "name": "md_render",
        "description": (
            "Closed-subset Markdown -> HTML, escape-first (raw HTML never "
            "survives), javascript:/data: urls refused, tables, fences "
            "with language class, optional NFKD heading ids. Not "
            "CommonMark — it is the contract stated here, byte-stable. "
            "Free under 32 KB, x402 above."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["markdown"],
            "properties": {
                "markdown": {"type": "string"},
                "heading_ids": {"type": "boolean", "default": False},
                "document": {"type": "boolean", "default": False,
                             "description": "wrap in a standalone "
                             "printable page (A4 print CSS — Ctrl-P "
                             "makes the PDF)"},
                "title": {"type": "string"},
            },
        },
    },
    {
        "name": "html_text",
        "description": (
            "HTML -> canonical text: invisible regions dropped, block "
            "structure as newlines, whitespace collapsed by a closed "
            "rule, entities decoded exactly once, optional link labels "
            "with hrefs (javascript:/data: refused and counted). The "
            "anti-hallucination tool for scraping agents. $0.001 per "
            "call: industrial volume funds the free half."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["html"],
            "properties": {
                "html": {"type": "string"},
                "keep_links": {"type": "boolean", "default": False},
                "max_bytes": {"type": "integer", "default": 1048576},
            },
        },
    },
    {
        "name": "color_palette",
        "description": (
            "Deterministic palettes from one seed color: complementary/"
            "analogous/triad/tetradic/split (closed hue rotations), plus an "
            "even-lightness shade ramp (2..21 steps) and optional neutral "
            "ramp. Same seed, same palette, forever. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["color"],
            "properties": {
                "color": {"type": "string"},
                "scheme": {"type": "string",
                           "enum": ["complementary", "analogous", "triad",
                                     "tetradic", "split"],
                           "default": "complementary"},
                "steps": {"type": "integer", "default": 5,
                          "description": "ramp steps, 2..21"},
                "neutral": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "eth_abi_encode",
        "description": (
            "Solidity ABI calldata encoder, closed type set (uintM/intM "
            "bytesM address bool string bytes + one-level arrays): "
            "types + values -> exact 0x calldata. No invented calldata. "
            "Capped: free under 32 KB."
        ),
        "inputSchema": {"type": "object", "required": ["types", "values"],
                        "properties": {
                            "types": {"type": "array",
                                      "items": {"type": "string"}},
                            "values": {"type": "array"}}}},
    {
        "name": "eth_abi_decode",
        "description": (
            "Decode calldata back to readable values against a type list. "
            "Blind signing dies here: see exactly what you sign. Capped."
        ),
        "inputSchema": {"type": "object", "required": ["types", "data"],
                        "properties": {
                            "types": {"type": "array",
                                      "items": {"type": "string"}},
                            "data": {"type": "string"}}}},
    {
        "name": "eth_eip712",
        "description": (
            "EIP-712 typed-data digest: domainSeparator, struct hash and "
            "the 0x1901 final digest, verified against the spec's published "
            "Mail example. Free."
        ),
        "inputSchema": {"type": "object",
                        "required": ["types", "primaryType", "domain",
                                     "message"],
                        "properties": {
                            "types": {"type": "object"},
                            "primaryType": {"type": "string"},
                            "domain": {"type": "object"},
                            "message": {"type": "object"}}}},
    {
        "name": "eth_receipt",
        "description": (
            "Receipt verifier: given event logs (already fetched) and the "
            "effects you expected (Transfer/Approval from/to/value), say "
            "match or no — no more 'probably worked'. Free."
        ),
        "inputSchema": {"type": "object", "required": ["logs", "expect"],
                        "properties": {
                            "logs": {"type": "array"},
                            "expect": {"type": "object"}}}},
    {
        "name": "eth_address",
        "description": (
            "EIP-55 address gate: validity, correct checksum form, "
            "all-lowercase/all-uppercase detection, optional allowlist "
            "membership (case-insensitive). The typo that drains a wallet "
            "dies here. Free."
        ),
        "inputSchema": {"type": "object", "required": ["address"],
                        "properties": {"address": {"type": "string"},
                                       "allowlist": {"type": "array",
                                                     "items":
                                                     {"type": "string"}}}}},
    {
        "name": "eth_selector",
        "description": (
            "Canonical function signature -> 4-byte selector via vendored "
            "pure-Python keccak256 (verified against published vectors). "
            "No more invented selectors. Free."
        ),
        "inputSchema": {"type": "object", "required": ["signature"],
                        "properties": {"signature": {"type": "string"}}}},
    {
        "name": "eth_units",
        "description": (
            "Exact wei ladder: wei/kwei/mwei/gwei/szabo/finney/ether, "
            "Decimal arithmetic, fractional-wei refused (6-vs-18 decimals "
            "mistakes cannot pass). Free."
        ),
        "inputSchema": {"type": "object", "required": ["value", "unit"],
                        "properties": {"value": {},
                                       "unit": {"type": "string",
                                                "enum": ["wei", "kwei",
                                                         "mwei", "gwei",
                                                         "szabo", "finney",
                                                         "ether"]}}}},
    {
        "name": "text_decode",
        "description": ("Mojibake repair: UTF-8-as-Latin-1 sequences "
                        "(CafÃ© -> Café) fixed only when provably safe; "
                        "reports repairs and suspicion, never guesses. "
                        "Free."),
        "inputSchema": {"type": "object", "required": ["text"],
                        "properties": {"text": {"type": "string"}}}},
    {
        "name": "num_human",
        "description": ("Human shapes for numbers: duration (3661 -> "
                        "'1h 1m 1s'), bytes (1536 -> '1.50 KiB', or decimal), "
                        "roman, ordinal. Closed rules, 1024 vs 1000 explicit. "
                        "Free."),
        "inputSchema": {"type": "object", "required": ["value", "kind"],
                        "properties": {
                            "value": {},
                            "kind": {"type": "string", "enum": ["duration",
                                     "bytes", "roman", "ordinal"]},
                            "style": {"type": "string",
                                      "enum": ["decimal", "binary"]}}}},
    {
        "name": "text_escape",
        "description": ("Escape one value for html/sql/shell/csv/json/url "
                        "dialects — the injection gate weak models type by "
                        "hand. Closed escapers per dialect. Free."),
        "inputSchema": {"type": "object", "required": ["value", "dialects"],
                        "properties": {
                            "value": {"type": "string"},
                            "dialects": {"type": "array",
                                         "items": {"type": "string",
                                                   "enum": ["html", "sql",
                                                            "shell", "csv",
                                                            "json",
                                                            "url"]}}}}},
    {
        "name": "text_normalize",
        "description": ("Unicode normalization NFC/NFD/NFKC/NFKD + accent "
                        "strip + fullwidth fold + casefold + whitespace "
                        "collapse: two names that look equal become octet "
                        "equal. Free."),
        "inputSchema": {"type": "object", "required": ["text"],
                        "properties": {
                            "text": {"type": "string"},
                            "form": {"type": "string",
                                     "enum": ["NFC", "NFD", "NFKC",
                                              "NFKD"],
                                     "default": "NFC"},
                            "strip_accents": {"type": "boolean",
                                              "default": False},
                            "casefold": {"type": "boolean",
                                         "default": False},
                            "collapse_ws": {"type": "boolean",
                                            "default": False},
                            "fullwidth": {"type": "boolean",
                                          "default": False}}}},
    {
        "name": "batch",
        "description": (
            "One tool over up to 100 payloads in a single call: the loop "
            "an agent used to walk one item at a time, with context decay "
            "and drift between steps. Per-item ok/error, aggregate sha256. "
            "Capped: free under 32 KB."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["tool", "payloads"],
            "properties": {
                "tool": {"type": "string"},
                "payloads": {"type": "array", "maxItems": 100},
                "stop_on_error": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "logic_rules",
        "description": (
            "Closed rule grammar over facts: when/require/forbid/set with "
            "and/or/not and leaf ops (eq ne gt gte lt lte in contains "
            "not_contains exists). Returns pass, per-rule trace (fired / "
            "skipped / passed / violated), violations[], errors[] naming "
            "the failing rule. Multi-step logic without drift. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["facts", "rules"],
            "properties": {
                "facts": {"type": "object"},
                "rules": {"type": "array", "maxItems": 50},
            },
        },
    },
    {
        "name": "sort_multi",
        "description": (
            "Multi-criteria stable sort of objects: by [{key, dir}], dot "
            "paths, closed type ranking (nulls first), ties keep original "
            "order. No vibes. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["rows", "by"],
            "properties": {
                "rows": {"type": "array"},
                "by": {"type": "array",
                       "items": {"type": "object",
                                 "required": ["key"]}},
            },
        },
    },
    {
        "name": "json_query",
        "description": (
            "Nested JSON access done right: $-path grammar with .key, "
            "[n] and [*] wildcards; returns every match with its exact "
            "canonical path. Reaches users[*].email where small models "
            "grab the wrong depth. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["data", "path"],
            "properties": {
                "data": {},
                "path": {"type": "string",
                         "description": "e.g. $.users[*].email"},
            },
        },
    },
    {
        "name": "check_redlines",
        "description": "The negative-constraint gate: forbidden words, "
                       "regexes, PII shapes (email/card/iban/phone/ssn), "
                       "byte budget -> clean, or the FIRST violation with "
                       "rule and offset. Instructions like 'never include "
                       "identifiers' degrade as context grows; this scan "
                       "does not. Free.",
        "inputSchema": {"type": "object", "required": ["text", "rules"],
                        "properties": {"text": {"type": "string"},
                                       "rules": {"type": "object"}}}},
    {
        "name": "check_agreement",
        "description": "Do these payloads describe the same deal? "
                       "Recursive pointer diff over N JSON values with "
                       "Decimal-tolerant scalars: agree, or every "
                       "divergence (pointer, kind, values). Two agents "
                       "that THINK they agreed is the bug; this is the "
                       "verdict. Free.",
        "inputSchema": {"type": "object", "required": ["payloads"],
                        "properties": {"payloads": {"type": "array",
                                                    "minItems": 2}}}},
    {
        "name": "intent_card",
        "description": "Human sentence -> tool choice + pre-filled form "
                       "from its real schema; what is missing becomes the "
                       "exact question to ask the human. Closed rules: "
                       "facts, enums, defaults, payload detection. Free.",
        "inputSchema": {"type": "object", "required": ["utterance"],
                        "properties": {"utterance": {"type": "string"}}}},
    {
        "name": "intent_check",
        "description": "Validate a filled intent card against the tool's "
                       "real schema before paying: ok, or the exact fields "
                       "the human must supply. Free.",
        "inputSchema": {"type": "object", "required": ["tool"],
                        "properties": {"tool": {"type": "string"},
                                       "args": {"type": "object"}}}},
    {
        "name": "extract_facts",
        "description": (
            "Deterministic fact inventory: every money amount, date, number, "
            "percent, url, email, uuid, hex id and IBAN-like token in the "
            "text, with byte offsets and a context window. Recall by "
            "construction — an LLM summarizer drops facts by chance, this "
            "cannot. Capped: free under 32 KB."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string"},
                "context_chars": {"type": "integer", "default": 30,
                                  "description": "0..200"},
                "group": {"type": "string", "enum": ["kind"],
                          "description": "kind -> deduped values per "
                                         "kind, no per-fact rows"},
            },
        },
    },
    {
        "name": "text_select",
        "description": (
            "Extractive selection without a model: score provided chunks "
            "against a query by closed coverage rules (token overlap, "
            "document-order tie-break), return top-k with matched terms. "
            "Deterministic. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["chunks", "query"],
            "properties": {
                "chunks": {"type": "array", "items": {"type": "string"}},
                "query": {"type": "string"},
                "k": {"type": "integer", "default": 3,
                      "description": "1..50"},
                "unit": {"type": "string", "enum": ["word", "char"],
                         "default": "word"},
            },
        },
    },
    {
        "name": "check_constraints",
        "description": (
            "Self-check for weak agents: text plus a closed constraint "
            "vocabulary (min/max_chars/bytes/words, max_lines, points, "
            "point_max_words, must_contain, must_not_contain, contains_date, "
            "contains_number, starts_with, ends_with, no_markdown, max_urls, "
            "https_only) -> pass/fail per constraint, first_failure and "
            "errors[] naming what to fix. Replaces self-reporting. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text", "constraints"],
            "properties": {
                "text": {"type": "string"},
                "constraints": {"type": "object"},
                "case": {"type": "string", "enum": ["fold", "exact"],
                         "default": "fold"},
            },
        },
    },
    {
        "name": "check_refs",
        "description": (
            "Anti-hallucination reference gate: every url/number/hex/uuid "
            "cited in the text must appear verbatim in the provided sources; "
            "unknown refs and unused sources are listed, never judged on "
            "meaning. Free."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["text", "sources"],
            "properties": {
                "text": {"type": "string"},
                "sources": {"type": "array", "items": {"type": "string"}},
                "kinds": {"type": "array",
                          "items": {"type": "string",
                                    "enum": ["urls", "numbers", "hex",
                                             "uuid"]}},
                "case": {"type": "string", "enum": ["fold", "exact"],
                         "default": "fold"},
            },
        },
    },]


@app.get("/mcp")
def mcp_info():
    return {
        "service": "mechacut",
        "transport": "stateless JSON-RPC 2.0 over HTTP POST",
        "tools": [t["name"] for t in MCP_TOOLS],
        "limits": f"{RATE_LIMIT} requests per minute per IP",
        "payments": payments.pricing_info(),
        "family": ("mechacut does data mechanics; storyboards, shot lists "
                   "and scene breakdowns are Moovicut, the sister product: "
                   "https://moovicut.studio"),
    }


def _rpc(result, rid):
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def _rpc_error(rid, code, message, data=None):
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": rid, "error": err}


@app.post("/mcp")
async def mcp_rpc(request: Request):
    try:
        body = await request.json()
    except Exception:
        return _rpc_error(None, -32700, "parse error")
    method = body.get("method")
    rid = body.get("id")
    if method == "initialize":
        return _rpc({"protocolVersion": "2024-11-05",
                     "capabilities": {"tools": {}},
                     "serverInfo": {"name": "mechacut", "version": "0.84.0"}}, rid)
    if method == "tools/list":
        return _rpc({"tools": MCP_TOOLS}, rid)
    if method == "tools/call":
        params = body.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        runner = TOOL_RUN.get(name)
        if runner is None:
            return _rpc_error(rid, -32602, f"unknown tool: {name}")
        result, err = runner(args)
        if err is not None:
            data = json.loads(err.body)
            return _rpc_error(rid, -32000, data.get("error", "bad_request"), data)
        return _rpc({"content": [{"type": "text",
                                  "text": json.dumps(result, sort_keys=True)}]}, rid)
    if isinstance(method, str) and method.startswith("notifications/"):
        return PlainTextResponse(status_code=202)
    return _rpc_error(rid, -32601, f"method not found: {method}")


def build_listing_text():
    """The marketplace listing, generated from live config so it CANNOT
    lie: counts from routing.TABLE, prices from payments.PRICES, URLs from
    the real surface. Copy any seller may paste and that updates itself."""
    priced = sorted(((k, int(v)) for k, v in payments.PRICES.items()),
                    key=lambda kv: kv[1])
    recipe_names = {r["name"] for r in RECIPE_SPECS}
    n_tools = sum(1 for t in routing.TABLE if t[0] not in recipe_names)
    lines = [
        "mechacut.studio — deterministic mechanical tools for AI agents",
        "%s: %d transforms + %d named recipes. Same inputs -> same bytes,"
        " or the sha256 says so." % (app.version, n_tools,
                                     len(RECIPE_SPECS)),
        "",
        "PRICING (x402 v1, USDC on Base, settled per call — no keys, no",
        "accounts, no stored data):",
        "  free  : %d endpoints, forever" % len(
            [t for t in routing.TABLE if t[1] not in payments.PRICES]),
        "  paid  : from $%.4f to $%.4f (cheapest call: %s)" % (
            priced[0][1] / 1e6, priced[-1][1] / 1e6,
            priced[0][0].replace("/api/v1/", "")),
        "  big payloads (>32 KB) auto-price on the capped routes",
        "",
        "DISCOVERY (all keyless):",
        "  GET  /agent/manifest      whole catalogue in one request",
        "  GET  /route?q=...         plain words -> ranked tools, EN/FR/PT",
        "  GET  /skillpack?pack=...  the words of one trade, ~600 tokens",
        "  GET  /integrity.json      replayable golden pins: audit us",
        "  POST /mcp                 MCP: every tool, one schema each",
        "  POST /api/v1/intent/card  human sentence -> form to fill",
            "  POST /api/v1/intent/reflect  your reading -> mirrored exact",
            "  GET  /api/v1/formula  the 12-formula catalog with sources",
            "  POST /api/v1/date/recurrence  RRULE -> dates, traps in the answer",
            "  POST /api/v1/units/shoe_size  shoe size -> exact mm + drift, never one number",
            "  POST /api/v1/net/sri          local octets -> integrity attr + style audit",
            "  POST /api/v1/date/tz_ambiguity  wall clock -> single|fold|gap, every UTC instant named",
            "  POST /api/v1/money/flight_comp  flight date + km + delay -> €250/400/600 or £220/350/520, table keyed by FLIGHT DATE",
            "  POST /api/v1/date/week          ISO week <-> date, %Y-W%V trap shown, does W53 exist?",
            "  POST /api/v1/money/baggage      does my bag pass: law by FLIGHT DATE vs gauges you supply, rotation fit",
            "  POST /api/v1/csv/excel_damage   predict Excel's silent CSV damage BEFORE the double-click, per column",
            "  POST /api/v1/money/crossover    two tariffs with fixed+unit parts: exact crossover, 'never' when one dominates",
            "  POST /api/v1/csv/excel_display  stored value + numFmt code -> what the human sees ($#,##0, scales by 1000)",
        "  POST /api/v1/check/*      the output gates: agree/redlines/refs",
        "",
        "PAYLOAD (one line, honest): mechacut.studio — %d deterministic"
        " transforms + %d recipes, free tier %d endpoints, paid calls from"
        " $%.4f USDC on Base, x402 v1. Manifest: /agent/manifest." % (
            n_tools, len(RECIPE_SPECS),
            len([t for t in routing.TABLE
                 if t[1] not in payments.PRICES]),
            priced[0][1] / 1e6),
    ]
    text = "\n".join(lines)
    return text, hashlib.sha256(text.encode()).hexdigest()


@app.get("/agent/listing.txt")
def api_agent_listing():
    body, sha = build_listing_text()
    return PlainTextResponse(
        body + "\n\nsha256(listing): %s\n" % sha,
        headers={"X-Listing-SHA": sha})


@app.get("/usage.json")
def api_usage():
    """Ephemeral settlement counters — the paid mirror of /misses.json.
    Lives in RAM only, dies with the redeploy: same doctrine as the
    misses ledger (nothing user-shaped, nothing persisted)."""
    return JSONResponse({
        "stored": False,
        "note": "in-memory since process start; a redeploy clears it",
        "settled_calls": payments.USAGE.get("settled", 0),
        "failed_settles": payments.USAGE.get("failed", 0),
        "cache_hits_saved": payments.USAGE.get("cache_hits", 0),
        "by_route": dict(sorted(payments.USAGE.get("routes", {}).items())),
    })


_INTEGRITY = Path(__file__).resolve().parent / "integrity.json"


@app.get("/integrity.json")
def api_integrity():
    """The public self-audit: every golden pin as a replayable checklist.
    Determinism is only a claim until someone else re-derives the bytes."""
    if not _INTEGRITY.exists():
        return JSONResponse(status_code=501,
                            content={"error": "integrity not built"})
    return JSONResponse(json.loads(_INTEGRITY.read_text(encoding="utf-8")))


@app.get("/misses.json")
def misses():
    """Public anonymized rejection ledger: kinds and routes, no payloads."""
    now = int(time.time())
    with _misses_lock:
        _prune_misses(now)
        total = len(_misses)
        by_kind: Dict[str, int] = {}
        by_route: Dict[str, int] = {}
        recent = []
        for ts, path, kind in reversed(_misses):
            by_kind[kind] = by_kind.get(kind, 0) + 1
            by_route[path] = by_route.get(path, 0) + 1
            if len(recent) < 20:
                recent.append({"ts": ts, "route": path, "kind": kind})
    return {
        "window_minutes": _MISS_WINDOW // 60,
        "total": total,
        "refusals": by_kind.get("payment_required", 0),
        "by_kind": by_kind,
        "by_route": by_route,
        "recent": recent,
    }


# ---------------------------------------------------------------- index

@app.get("/")
def index(request: Request):
    accept = request.headers.get("accept", "")
    if LANDING and "text/html" in accept:
        return HTMLResponse(LANDING[_pick_lang(request)])
    return {
        "service": "mechacut",
        "summary": ("Deterministic data transforms: charts, schema-gated JSON "
                    "reshaping, validation, the data-repair bundle and the "
                    "code-editing bundle (patch/diff/apply, path, glob, env). "
                    "No API key, no account, nothing stored."),
        "endpoints": {
            "/api/v1/chart": "POST records or CSV + column roles -> Vega-Lite spec and/or PNG",
            "/api/v1/reshape": "POST JSON + mapping -> reshaped JSON (outputSchema gate)",
            "/api/v1/validate": "POST payload + JSON Schema -> valid or precise errors",
            "/api/v1/json/repair": "POST broken JSON text -> parsed + repairs applied",
            "/api/v1/json/diff": "POST two JSON values -> sorted changes (JSON Pointer)",
            "/api/v1/json/patch": "POST document + RFC 6902 patch -> patched document (free < 32 KB)",
            "/api/v1/json/canonical": "POST JSON -> canonical bytes (sorted keys) + sha256",
            "/api/v1/csv/fix": "POST dirty CSV -> clean CSV + notes (free < 32 KB)",
            "/api/v1/csv/types": "POST CSV or records -> typed rows + column report (free < 32 KB)",
            "/api/v1/csv/join": "POST two tables + key -> joined rows, left wins (paid)",
            "/api/v1/table/pivot": "POST records -> pivot/unpivot with aggregation (paid)",
            "/api/v1/list/dedupe": "POST items + mode -> deduped, first-seen order kept",
            "/api/v1/format/convert": "POST text, from/to among json|yaml|toml|csv|env (free < 32 KB)",
            "/api/v1/text/patch": "POST text + edits [{find,replace,occurrences}] -> patched text (paid)",
            "/api/v1/text/diff": "POST two texts -> unified diff + stats (free < 32 KB)",
            "/api/v1/text/apply-diff": "POST text + unified diff -> patched text, strict context (paid)",
            "/api/v1/path/normalize": "POST path -> lexical POSIX normalization + parts",
            "/api/v1/glob/match": "POST pattern + paths -> deterministic match, input order",
            "/api/v1/env/interpolate": "POST template + vars -> expanded text, missing reported",
            "/api/v1/date/parse": "POST one date text -> ISO/UTC/epoch/weekday fields",
            "/api/v1/date/tz": "POST instant + IANA targets -> DST-correct conversions",
            "/api/v1/date/calc": "POST base + op -> add/business_days/diff/boundary/age",
            "/api/v1/cron/next": "POST cron + after -> next N fire times (wall clock)",
            "/api/v1/cron/humanize": "POST cron -> plain reading + field sets",
            "/api/v1/ics/generate": "POST events -> deterministic VCALENDAR (free < 32 KB)",
            "/api/v1/ics/parse": "POST VCALENDAR -> normalized events (free < 32 KB)",
            "/api/v1/num/format": "POST value + locale/style/currency -> formatted text",
            "/api/v1/num/parse": "POST human number -> canonical decimal, never guessed",
            "/api/v1/num/round": "POST value + places/mode -> exact Decimal rounding",
            "/api/v1/units/convert": "POST value + from/to -> closed-family conversion",
            "/api/v1/money/prorate": "POST amount + cycle + window -> prorated (paid)",
            "/api/v1/money/split": "POST total + participants -> cent-exact split",
            "/api/v1/number/spell": "POST amount -> words FR/EN/PT for legal mentions (free < 32 KB)",
            "/api/v1/hash/digest": "POST data + algo -> hex digest (a model cannot hash)",
            "/api/v1/hash/hmac": "POST message+key -> hmac digest; with signature -> constant-time match (free)",
            "/api/v1/id/ulid": "POST make (deterministic from seed/timestamp), parse or sort ULIDs (free)",
            "/api/v1/json/map": "POST items + closed ops -> mapped array, element-wise, in order (free)",
            "/api/v1/semver/parse": "POST version -> official semver grammar parts + stability (free)",
            "/api/v1/semver/sort": "POST versions -> semver precedence order: 10.0.0 > 2.0.0, pre < release (free)",
            "/api/v1/text/sanitize": "POST filename -> cross-OS safe name + exact warnings (free)",
            "/api/v1/file/identify": "POST base64 blob -> true type from closed magic table, or honest unknown (free)",
            "/api/v1/geo/distance": "POST two points or an ordered route -> exact great-circle metres/km (free)",
            "/api/v1/geo/geohash": "POST lat+lon -> geohash, or geohash -> centre + bounding box (free)",
            "/api/v1/integrity/verify": "POST base_url + pins (or integrity_url) -> replay N times, per-pin determinism verdict, guarded egress ($0.001)",
            "/api/v1/math/calc": "POST (expr digits) -> closed-language exact Decimal calculator: model writes, machine counts (free)",
            "/api/v1/money/discount": "POST (price steps qty currency) -> chained discounts as exact factors: 44% not 50%, order impact computed, formula returned (free)",
            "/api/v1/formula": "POST (formula args) -> the published formula, your numbers substituted, exact Fractions rendered to declared decimals — 12 rational formulas, zero constants; GET lists the closed catalog (free)",
            "/api/v1/intent/reflect": "POST (formula args as understood) -> same exact answer PLUS a reading_check: the mirror makes YOUR reading visible before arithmetic excuses it (free)",
            "/api/v1/date/recurrence": "POST (dtstart rrule max_count) -> RFC 5545 RRULE expanded to dated occurrences: closed subset, COUNT xor UNTIL, skipped invalid dates LISTED, dtstart anchor+sync declared, wall-clock per the RFC, named refusals, hard cap 500 (free)",
            "/api/v1/units/shoe_size": "POST (foot_mm | size+system, width_mm) -> shoe size in exact mm with published steps as fractions (barleycorn 127/15, Paris point 20/3), grid candidates for half AND third brand practices, cross-system drift stated exactly (1.8 mm/step, 4 EU steps != 3 US), +2 allowance named, never one confident number, brand charts declared off-contract (free)",
            "/api/v1/net/sri": "POST (bytes_b64|text | integrity_attr | url) -> W3C SRI attribute from LOCAL octets only, never fetches: ready tags + crossorigin, attr style audit (TAB-separator = CVE-2026-120423 class, sha1/md5 refused by name, length checks), URL moving-parts audit (latest/ranges), verify mode vs given octets (free)",
            "/api/v1/date/tz_ambiguity": "POST (zone, local wall clock, no offset) -> verdict single | fold | gap for DST transitions: every candidate UTC instant named with offset and abbreviation, transition minute + affected window computed from the installed IANA tzdata (never embedded, never fetched), PEP 495 fold rule stated, gap neighbours (last valid / first valid wall clocks) for schedulers, named refusals for offsets and guessed zones (free)",
            "/api/v1/money/flight_comp": "POST (regime EU|UK, flight_date, event, distance_km, delay_min|notice_days+reroute) -> EC261/UK261 compensation with the table chosen BY FLIGHT DATE: old text + Sturgeon/Nelson case-law before 2027-10-23, (EU) 2026/2202 codified rules after ('EXCEEDING three hours' strict), UK261 £220/£350/£520 with the official under-4h £260 band, intra-Union EUR 400 cap named, 50%/25 % reductions as named MAY-options, nine-month claim deadline as an exact date, refusals named, zero fetch, zero legal promises (free)",
            "/api/v1/date/week": "POST (date | iso YYYY-Www-d | year) -> ISO 8601 week round-trip: iso_week/iso_year split out of the calendar year, week bounds, W53 existence by THEOREM (53 Thursdays — zero tables), nonexistent weeks refused naming the artifact, %Y-W%V vs %G-W%V shown on the requested date, Excel/US conventions beside ISO (free)",
            "/api/v1/money/baggage": "POST (flight_date regime bag [bag_unit|weight_kg|personal_sizer|cabin_sizer|cabin_sum_limit|cabin_weight_max]) -> cabin-baggage verdict: EU law keyed by FLIGHT DATE (silent before 2027-10-23, 40x30x15 underseat safe-harbour after, NO overhead size in law), carrier gauges as SUPPLIED arguments compared PER DIMENSION with rotation allowed, the press '100 cm combined / 7 kg' reading rendered as a tested press claim never a legal rule, weight named per source, zero fetch, not legal advice (free)",
            "/api/v1/csv/excel_damage": "POST (csv locale en|eu as_of) -> what Excel silently REWRITES at open, per column with published vectors (02134->2134, 4111111111111111->4111111111111110, 1E5->100000, SEPT2/MARCH1->dates, '3-4' = March 4 in en / April 3 in eu), Microsoft's three Automatic Data Conversion toggles named, formula shapes and full-width digits flagged, column-as-Text import prescribed, unrecoverability stated; detection lot — the numFmt RENDER lives at /api/v1/csv/excel_display (free)",
            "/api/v1/money/crossover": "POST (currency a_unit_rate a_unit_per a_fixed a_fixed_per b_* [+ days_per_year usage_per_period usage_period km_per_unit exit_fee_a exit_fee_b sign_up_a sign_up_b]) -> EXACT crossover of two fixed+unit tariffs as a Fraction plus decimal, day convention NAMED (x12 for monthly, never 30-day months; x365 or 366), domination rendered as 'never' with reason, immediate-crossover when fixeds tie, costs at your usage, fees as payback months separate from the crossover, EV km only if efficiency supplied, zero fetch, no tariff advice (free)",
            "/api/v1/csv/excel_display": "POST (value format [locale]) -> what Excel DISPLAYS from the stored value under a numFmt code, the arXiv-2611.05806 divergence closed: '$#,##0,' scales by 1000 (B9: stored 1000000 shows $1,000), Microsoft symbol-table examples replayed ('#.0,,' 12200000 -> 12.2, '(000)' 12 -> (012), '0%' 0.5 -> 50%, '#.##' 8.9 -> 8.9, '0.00 \"dollars\"'), display rounding half-away-from-zero said, locale as SYMBOLS argument (de-DE renders 1.234.567,89), General/E-notation/date-codes/colours/fill/text refused BY NAME, stored value never changes (free)",
            "/api/v1/table/sql_dump": "POST (csv|rows table dialect types) -> CREATE TABLE + INSERT with types DEDUCED and DIT (type+reason+sample), dialect-exact quoting, identifiers outside closed grammar refused by name, sqlite round-trip verified (🟡 above 32 KB)",
            "/api/v1/table/scale": "POST (items factor|servings) -> recipe scaling with THREE answers per line: exact fraction, measurable amount at the class rounding step (rule named), delta — silent rounding impossible, pinch refused by name (free)",
            "/api/v1/check/format": "POST (payload formats) -> closed-set format validation for fields JSON Schema cannot describe (free)",
            "/api/v1/csv/money_columns": "POST (csv columns delimiter) -> per-column money convention PROVEN by the column's own values; ambiguous-without-proof refused with both readings (🟡)",
            "/api/v1/date/relative": "POST (phrase now tz) -> relative-date words EN/FR/PT to exact ISO, now-argument determinism, ambiguities reported (free)",
            "/api/v1/text/url_canonical": "POST (url strip_tracking sort_params drop_fragment) -> RFC 3986 §6.2.2 canonical URL, every transformation named (free)",
            "/api/v1/xml/to_json": "POST (xml force_array coerce) -> XML to JSON with rules_applied printed in the response, force_array kills the one-item bug, DTD refused (🟡)",
            "/api/v1/web/cert": "POST (pem as_of) -> X.509 lint: names, SANs, validity, deprecation flags, chain shape (🟡)",
            "/api/v1/id/checkdigit": "POST (mode check/generate/repair/scan) -> 15 published check-digit schemes: ISBN/EAN/UPC/GTIN/ISSN/ISIN/CUSIP/SEDOL/ABA/LEI/ORCID/CAS/Verhoeff/Damm, ambiguity reported (free)",
            "/api/v1/image/rightsize": "POST (data_b64 width height mode resample) -> deterministic PNG resize, integer resampling, free <32 KB (🟡)",
            "/api/v1/money/rates": "GET (+date from to amount) -> ECB official reference rates, live day or 90d archive (free)",
            "/api/v1/doc/text": "POST base64 PDF -> per-page text + verdicts (free under 32 KB, $0.001 above)",
            "/api/v1/money/amortize": "POST principal rate months -> exact annuity schedule summing to balance 0.00 (free)",
            "/api/v1/money/interest": "POST principal rate years compounds -> compound amount + EAR + the formula itself (free)",
            "/api/v1/ics/validate": "POST VCALENDAR text -> errors (MUST) + warnings (SHOULD), components counted (free)",
            "/api/v1/schedule/holidays": "POST country (+year or on) -> statutory holidays with legal basis per line (free)",
            "/api/v1/web/cache": "POST Cache-Control text (+method) -> directives classified, freshness, the one required action (free)",
            "/api/v1/gzip/roundtrip": "POST base64 payload -> deterministic gzip bytes (mtime=0) or back (free under 8 MB)",
            "/api/v1/qr/generate": "POST text (+ecl/version/scale) -> deterministic QR as SVG or raw matrix, v1-10, L M Q H (free)",
            "/api/v1/table/peek": "POST rows -> per-column type, nulls, uniques, bounds (free)",
            "/api/v1/csv/diff": "POST left right key -> added/removed/changed rows with field pointers (free)",
            "/api/v1/ssh/fingerprint": "POST public key line -> ssh-keygen-shaped SHA256+MD5 fingerprints (free)",
            "/api/v1/zip/verify": "POST base64 archive -> listing + CRC verdicts, never extracted (free under 32 MB)",
            "/api/v1/schedule/overlap": "POST intervals (+mode/window/point) -> merge, conflicts, free gaps or point verdict (free)",
            "/api/v1/cron/validate": "POST cron expr (+optional at) -> parsed fields, never-verdicts with reason, or next runs (free)",
            "/api/v1/crypto/address": "POST address (+optional chain scope) -> scheme, kind, network, checksum verdict (free)",
            "/api/v1/validate/taxid": "POST tax id value (+optional kind) -> check-digit verdict with the named published algorithm (free)",
            "/api/v1/caip/parse": "POST CAIP-2/10 value (or parts, mode=format) -> namespace, chain name, EIP-55 checksummed address (free)",
            "/api/v1/secret/scan": "POST text -> published secret formats + Luhn cards + IBAN + BIP39 checksum, positions, never echoes values (free)",
            "/api/v1/text/redact": "POST text -> masked with stable [KIND_n] tags; mapping deliberately not returned (free)",
            "/api/v1/validate/country": "POST alpha-2 -> alpha-3, numeric, currency+decimals, calling code (free)",
            "/api/v1/validate/postal": "POST code+country -> grammar verdict + canonical format (free)",
            "/api/v1/net/ip": "POST ip -> version + scope verdicts + reverse pointer (free)",
            "/api/v1/net/cidr": "POST cidr -> range math, contains?, split into subnets (free)",
            "/api/v1/file/encoding": "POST base64 -> BOM/utf-8 verdict or undetermined-with-evidence (free)",
            "/api/v1/text/punycode": "POST domain -> unicode/xn-- IDN round trip, homoglyph verdict (free)",
            "/api/v1/num/fx": "POST amount + caller-provided rate + currency -> exact Decimal math, ISO minor units (free)",
            "/api/v1/pkg/name": "POST name + kind (npm|pypi|docker) -> valid, normalized, exact errors (free)",
            "/api/v1/enc/base64": "POST text -> base64/base64url/hex, strict both ways",
            "/api/v1/jwt/decode": "POST token -> header + claims + signature, verified=false",
            "/api/v1/id/uuid": "POST op + name/seed/at -> deterministic UUID v5|v4_seeded|v7",
            "/api/v1/id/slug": "POST text -> url-safe slug",
            "/api/v1/fingerprint": "POST JSON or CSV -> canonical sha256 (cache key)",
            "/api/v1/validate/iban": "POST iban -> structure + mod-97 verdict ($0.0005)",
            "/api/v1/validate/phone": "POST phone -> E.164 + country (free)",
            "/api/v1/validate/email": "POST email -> structure + normalized (free)",
            "/api/v1/validate/url": "POST url -> components + canonical (free)",
            "/api/v1/color/check": "POST color[+against] -> WCAG verdicts (free)",
            "/api/v1/text/count": "POST text -> exact counts (chars/words/sentences/lines/bytes)",
            "/api/v1/sort/natural": "POST items -> human-order sort + permutation",
            "/api/v1/text/case": "POST text + op -> case conversion both directions",
            "/api/v1/text/truncate": "POST text + max -> boundary-exact truncation",
            "/api/v1/regex/test": "POST pattern + text -> match/spans/groups/replace",
            "/api/v1/text/chunk": "POST text + budget -> exact token chunks (tiktoken)",
            "/api/v1/md/render": "POST markdown -> safe closed-subset HTML (free < 32 KB)",
            "/api/v1/html/text": "POST html -> canonical readable text ($0.001)",
            "/api/v1/color/palette": "POST color + scheme -> palette + ramps (free)",
            "/api/v1/check/constraints": "POST text + closed constraints -> per-rule verdicts (free)",
            "/api/v1/check/refs": "POST text + sources -> unknown cited refs (free)",
            "/api/v1/extract/facts": "POST text -> every money/date/number/url/email/uuid/hexid/iban with offsets (cap 32 KB)",
            "/api/v1/text/select": "POST chunks + query -> top-k by closed coverage rules (free)",
            "/api/v1/logic/rules": "POST facts + rules -> per-rule trace and violations (free)",
            "/api/v1/sort/multi": "POST rows + keys -> stable multi-criteria order (free)",
            "/api/v1/json/query": "POST data + $-path -> every match with canonical path (free)",
            "/api/v1/batch": "POST tool + payloads[] -> every result in one call (cap 32 KB)",
            "/api/v1/recipe/invoice": "POST line items + VAT -> exact invoice + words + due date (free)",
            "/api/v1/recipe/schedule": "POST cron + start -> occurrences + ICS (free)",
            "/api/v1/fiche/shop-reste": "POST slots (total sold_morning pct_afternoon) -> the rest-after-rest chain traced, exact (free)",
            "/api/v1/fiche/partage-reste": "POST slots (total first_part second_of_rest) -> share-of-the-rest traced, fractions welcome (free)",
            "/api/v1/fiche/soldes2": "POST slots (price pct1 pct2) -> final + the naive-sum lie measured (free)",
            "/api/v1/router/plan": "POST texte -> prescribed fiche + slots + transport rule, each entry cited to a published bench line; never guesses (free)",
            "/api/v1/router/apply": "POST texte -> closed-grammar match: the server extracts verbatim slots and RUNS the fiche, zero LM calls; else named refusal + fill-in prompt (free)",
            "/api/v1/recipe/facts": "POST free text -> normalized fact inventory + money total in one call (free)",
            "/api/v1/intent/card": "POST a human sentence -> tool choice + pre-filled form or the exact missing-field question (free)",
            "/api/v1/intent/check": "POST tool + filled args -> ok or the exact fields still missing (free)",
            "/api/v1/check/agreement": "POST 2-8 payloads -> do they describe the same deal? every divergence with its pointer (free)",
            "/api/v1/check/redlines": "POST text + closed rules -> clean, or first violation of forbidden words/regex/PII shapes/budget (free)",
            "/api/v1/text/decode": "POST garbled text -> provable mojibake repair to utf-8 (free)",
            "/api/v1/num/human": "POST value + kind -> human duration/bytes/roman/ordinal (free)",
            "/api/v1/text/escape": "POST value + dialects -> escaped per closed rules (free)",
            "/api/v1/text/normalize": "POST text -> NFC/NFKC, accents, fullwidth, whitespace (free)",
            "/api/v1/eth/address": "POST address (+allowlist) -> EIP-55 verdicts (free)",
            "/api/v1/eth/selector": "POST signature -> 0x 4-byte selector (free)",
            "/api/v1/eth/units": "POST value + unit -> exact wei/gwei/ether (free)",
            "/api/v1/eth/abi-encode": "POST types + values -> exact calldata (cap 32 KB)",
            "/api/v1/eth/abi-decode": "POST calldata + types -> readable args (cap 32 KB)",
            "/api/v1/eth/eip712": "POST EIP-712 typed data -> digest (free)",
            "/api/v1/eth/receipt": "POST logs + expected -> Transfer/Approval match (free)",
            "/mcp": "stateless MCP JSON-RPC: one tool per transform",
            "/openapi.json": "OpenAPI 3.1",
            "/SKILL.md": "agent skill",
            "/SKILL-MINI.md": "one-page skill for weak models (~650 tokens)",
            "/agent/examples.json": "real request+response pairs per tool, captured at build",
            "/agent/manifest": "GET one line per tool: navigation in ~500 tokens (free)",
            "/tools/{name}.json": "GET single tool schema on demand (free)",
            "/SKILL-{pack}.md": "GET per-bundle skill pack: core|repair|code|dates|numbers|identity|checks|text|design",
            "/route": "GET ?q=task phrase -> ranked tools (closed vocabulary, free)",
            "/api/v1/recipes": "GET named pipelines: clean-table, clean-json (free)",
            "/api/v1/recipe/clean-table": "POST {csv} -> fix -> types -> dedupe in one call",
            "/api/v1/recipe/clean-json": "POST {text, style} -> repair -> canonical in one call",
            "/api/v1/pipeline": "POST {steps:[{tool,args}], $from refs} -> one chain, intermediates never leave the server",
            "/misses.json": "GET anonymized rolling rejection/refusal ledger (no payloads)",
        },
        "pricing_model": ("free tools: 30 req/min/IP keyless; capped tools: "
                          "free under 32 KB then x402 per call; priced tools: "
                          "x402 from the first call. The free tier is the "
                          "product's core loop, not a trial."),
        "limits": f"{RATE_LIMIT} requests per minute per IP; bodies up to "
                  f"{MAX_BODY_BYTES} bytes",
        "payments": payments.pricing_info(),
        "family": ("mechacut does data mechanics; storyboards, shot lists "
                   "and scene breakdowns are Moovicut, the sister product: "
                   "https://moovicut.studio"),
    }


@app.get("/SKILL.md", response_class=PlainTextResponse)
def skill_md():
    return (Path(__file__).parent / "SKILL.md").read_text()


@app.get("/agent/examples.json", response_class=PlainTextResponse)
def agent_examples():
    """Real request/response pairs captured by running the corpus at
    build time — the landing's Try-it panels fetch this lazily, so the
    page itself stays light."""
    if not _EX_PATH.exists():
        return '{"examples": {}}'
    return _EX_PATH.read_text(encoding="utf-8")
