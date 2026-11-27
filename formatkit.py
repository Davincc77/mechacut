"""formatkit — check/format : valider les formats QUE JSON Schema ne sait
pas dire.

La douleur (HN, nov. 2026) : « a field has a hidden schema in that only
particular strings are valid, but that restriction isn't in the JSON
schema ». Un champ type:string passe TOUJOURS `type: string` — qu'il
contienne "2026-02-30", "v1.2.3-beta..1" ou "1,234.56" censé être un
decimal-string. Les petits modèles se font avoir à chaque tour de
contexte, et l'erreur éclate trois systèmes plus loin.

Ici : payload + JSON-Schema (réutilisé tel quel via la validation
existante) + map `formats: {"$.chemin": "format"}` sur un ensemble FERMÉ
de formats, chacun cité à sa publication. Chaque violation rend
(path, value, format, why, expected_de) — la réponse est la réparation.

Formats fermés (nom → source) :
  date-iso        RFC 3339 full-date (calendrier réel : 2026-02-30 rejeté)
  datetime-iso    RFC 3339 date-time (Z ou offset obligatoires)
  time-iso        RFC 3339 full-time
  semver          grammaire officielle semver.org §2 (via micro.SEMVER_RE)
  uuid            RFC 4122 forme canonique 8-4-4-4-12
  sha256-hex      64 hexadécimaux (FIPS 180-4, la sortie)
  hex-color       #RGB ou #RRGGBB (CSS color, §4.2)
  slug            ^[a-z0-9]+(-[a-z0-9]+)*$ (fermé, déclaré)
  decimal-string  ^-?(0|[1-9]\\d*)(\\.\\d+)?$ — le "1,234.56" en chaîne
                  d'argent est ICI une violation, avec pointeur vers
                  /csv/money_columns
  e164            E.164 : + suivi de 8 à 15 chiffres
  email           syntaxe locale@domaine (domaine à point), même règle
                  que /validate/email
  url             http(s) + hôte (même garde que /validate/url)
  currency-iso    table ISO 4217 fermée du serveur
  country-iso     table ISO 3166 alpha-2 fermée du serveur
  json-pointer    RFC 6901 (vide ou segments /)
"""
import re
from datetime import datetime

import micro
import units
from checkers import check_email, check_url
from numfmt import CURRENCIES
from rules import json_query

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_TIME = re.compile(r"^\d{2}:\d{2}:\d{2}(?:\.\d+)?$")
ISO_DT = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}"
                    r"(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$")
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
                     r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                     r"[0-9a-fA-F]{12}$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DECSTR_RE = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$")
E164_RE = re.compile(r"^\+\d{8,15}$")
PTR_RE = re.compile(r"^(?:/(?:[^/~]|~[01])*)*$")


class FormatError(Exception):
    pass


def _ok_date(v):
    if not ISO_DATE.match(v or ""):
        return "expected YYYY-MM-DD (RFC 3339 full-date)", None
    try:
        datetime.strptime(v, "%Y-%m-%d")
    except ValueError:
        return "calendar day does not exist", None
    return None, None


def _ok_datetime(v):
    if not ISO_DT.match(v or ""):
        return ("expected RFC 3339 date-time with Z or ±hh:mm offset "
                "(a space instead of T is NOT RFC 3339)", None)
    try:
        datetime.fromisoformat(v.replace("Z", "+00:00").replace(
            "z", "+00:00"))
    except ValueError:
        # B11 (vague Grok 27-11, Host) : la vraie seconde intercalaire
        # 23:59:60 etait refusee sous un « calendar/zone values out of
        # range » nu — alors que la carte du contrat promet le leap
        # second. RFC 3339 l'autorise (grammar) ; POSIX ne la rend pas
        # (scale). Le FORMAT juge la grammar — le cas est NOMMEE.
        if len(v) >= 19 and v[11:19] == "23:59:60":
            return None, "leap-second"
        return "calendar/zone values out of range", None
    return None, None


def _ok_time(v):
    if not ISO_TIME.match(v or ""):
        return "expected HH:MM:SS(.frac) (RFC 3339 full-time)", None
    h, m = int(v[0:2]), int(v[3:5])
    s = int(v[6:8])
    if h > 23 or m > 59 or s > 60:      # 60 = leap second, permis
        return "hour/min/sec out of range (leap second :ss=60 ok)", None
    if s == 60:
        return None, "leap-second"  # B11 : la grammar passe, le cas se dit
    return None, None


def _ok_semver(v):
    if not (v and micro.SEMVER_RE.match(v)):
        return ("official grammar semver.org §2 — no leading v, "
                "MAJOR.MINOR.PATCH, prerelease/build rules apply", None)
    return None, None


def _mk_regex(rx, fmt, hint):
    def ok(v):
        if not isinstance(v, str) or not rx.match(v):
            return hint, None
        return None, None
    ok.__name__ = "ok_" + fmt
    return ok


CHECKS = {
    "date-iso": _ok_date,
    "datetime-iso": _ok_datetime,
    "time-iso": _ok_time,
    "semver": _ok_semver,
    "uuid": _mk_regex(UUID_RE, "uuid", "canonical 8-4-4-4-12 hex"),
    "sha256-hex": _mk_regex(SHA256_RE, "sha256-hex", "64 hex digits"),
    "hex-color": _mk_regex(COLOR_RE, "hex-color",
                           "#RGB or #RRGGBB (CSS §4.2)"),
    "slug": _mk_regex(SLUG_RE, "slug",
                      "lowercase alphanumeric words joined by single '-'"),
    "decimal-string": _mk_regex(
        DECSTR_RE, "decimal-string",
        'exact decimal as string, no leading zeros, no separators — '
        'for money inside CSVs use /api/v1/csv/money_columns'),
    "e164": _mk_regex(E164_RE, "e164", "+ then 8-15 digits"),
    "json-pointer": _mk_regex(PTR_RE, "json-pointer",
                              "'' or /segments (RFC 6901)"),
    "currency-iso": lambda v: (None, None) if (
        isinstance(v, str) and v.upper() in CURRENCIES) else (
        "ISO 4217 code from the server's closed table", None),
    "country-iso": lambda v: (None, None) if (
        isinstance(v, str) and v.upper() in units.COUNTRIES) else (
        "ISO 3166 alpha-2 from the server's closed table", None),
    "email": lambda v: (None, None) if (
        isinstance(v, str) and check_email(v)["valid"]) else (
        "local@domain.tld (same rules as /api/v1/validate/email)", None),
    "url": lambda v: (None, None) if (
        isinstance(v, str) and check_url(v)["valid"]) else (
        "http(s) URL with host (same rules as /api/v1/validate/url)",
        None),
}


def check_format(payload, formats):
    if not isinstance(formats, dict) or not formats:
        raise FormatError(
            "formats must be a non-empty map of $-path → format name")
    unknown = sorted(set(formats.values()) - set(CHECKS))
    if unknown:
        raise FormatError("unknown format(s) %s — closed set: %s"
                          % (", ".join(repr(u) for u in unknown),
                             ", ".join(sorted(CHECKS))))
    violations = []
    leap_paths = []
    checked = 0
    for path, fmt in sorted(formats.items()):
        try:
            q = json_query(payload, path)
        except Exception as e:
            raise FormatError("path %r: %s" % (path, e))
        if q["not_found"]:
            violations.append({"path": path, "format": fmt,
                               "value": None,
                               "why": "path matches nothing in payload"})
            continue
        for hit in q["results"]:
            checked += 1
            v = hit["value"]
            if not isinstance(v, str):
                violations.append({
                    "path": hit["path"], "format": fmt, "value": v,
                    "why": "%s validates STRINGS; got %s — a schema "
                           "cannot say this, which is exactly the trap"
                           % (fmt, type(v).__name__)})
                continue
            why, _note = CHECKS[fmt](v)
            if _note == "leap-second":
                leap_paths.append(hit["path"])
            if why:
                violations.append({"path": hit["path"], "format": fmt,
                                   "value": v, "why": why,
                                   "expected": fmt})
    out = {"formats_checked": checked,
           "rules": sorted("%s → %s" % kv for kv in formats.items()),
           "valid": not violations,
           "violations": violations,
           "closed_format_set": sorted(CHECKS)}
    if leap_paths:
        # B11 : la seconde valide est DITE, pas muette — RFC 3339 autorise
        # :60 ; aucune table de leap seconds n'est embarquee ici (ce
        # serait inventer le calendrier — c'est la proposition
        # utc_tt_offset_named_table qui voudrait porter cette table).
        out["leap_second_paths"] = sorted(set(leap_paths))
        out["leap_second_note"] = ("grammar-valid RFC 3339; POSIX/ISO "
                                   "civil time cannot render this instant "
                                   "— existence of the insertion is NOT "
                                   "judged here, never certified")
    return out
