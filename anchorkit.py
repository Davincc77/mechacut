"""anchorkit — /api/v1/date/tz_anchor : une heure murale, DEUX horloges.

La classe d'erreurs mesurée en NOVEMBRE 2026, six fois le même crime :
**PraisonAI #4732/#3711** (naive `at:2026-09-02T22:30` marquée UTC → le
one-shot « fired an hour or more off ») ; **hermes-agent PR #1729**
(l'instant naïf ancré au tz SYSTÈME, relu par le tz CONFIGURÉ → « jobs
never become due ») ; **Composio #4148** (offset ET timezone passés
ensemble → événement créé décalé, JAMAIS rejeté) ; **evoila/meho
#2339** (« picker datetime and stored fire_at look different but
plausibly equivalent ») ; **nanobot #408** (champ tz présent JAMAIS LU,
croniter grainé time.time()) ; **CloseCrab** (un agent se construit sa
parade : refuser les zones DST bruyamment).

date/tz CONVERTIT un instant entre zones. date/tz_ambiguity dit si UNE
murale EXISTE dans UNE zone (single | fold | gap) — cet engine est
APPELÉ ici, jamais dupliqué. Cette route est le CONFLIT : la murale
écrite dans la zone du JOB (`meant_in`) vs l'horloge de la MACHINE qui
l'ancre naïvement (`run_in`) → chaque instant UTC candidat, sa dérive
SIGNÉE en minutes (positif = part en RETARD), et les deux wall clocks
relus de part et d'autre — le « 2 hours further out » de meho devient
un NOMBRE.

Grammaire close, contrat = les résolutions PUBLIÉES :
- l'offset dans la chaîne GAGNE, la zone ne fait que ré-afficher
  (résolution Composio #4148, mot à mot) ;
- pas de zone par défaut : les deux sont REQUISES quand le stamp est
  naïf (leçon PraisonAI : quatre niveaux de repli = quatre bugs ;
  leçon tz_ambiguity : « a model that defaults to UTC books meetings
  nobody attends ») ;
- l'`stamped_offset` optionnel rejoue le FIX piégé de PraisonAI : le
  code qui marque « l'offset en force AUJOURD'HUI » au lieu de l'offset
  de la DATE est faux d'une heure « for any date on the other side of a
  DST change » — ici l'offset fourni est comparé à l'offset de la date,
  écart nommé.
Zéro lecture d'horloge, zéro table : oracle = la base IANA du serveur
via zoneinfo, comme tz_ambiguity. Les instants rendus sont ceux que
zoneinfo calcule pour la DATE DEMANDÉE (passé et futur compris).
"""

import re
from datetime import datetime, timedelta, timezone

from dates import DateError, _fmt_off, _zone
from tzambkit import TzAmbError, _parse_local, classify

_UTC = timezone.utc

_ANCHOR_EXPECTED = {
    "stamp": "a wall clock like '2026-11-02 09:00' (naive — that is the "
             "bug class) or an absolute stamp like "
             "'2026-09-02T22:30:00Z' / '...+05:30'",
    "meant_in": "IANA zone the wall clock was WRITTEN against (the "
                "job's/config zone), e.g. Europe/Paris — never guessed",
    "run_in": "IANA zone of the MACHINE that anchors it (the server's "
              "local clock), e.g. UTC — never guessed",
    "stamped_offset": "numeric offset like '+01:00' or '-05:00': the "
                      "offset your code stamped at write time (the "
                      "PraisonAI bug) — compared against the offset IN "
                      "FORCE ON THAT DATE",
}


class AnchorError(ValueError):
    def __init__(self, field, message, expected=None):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected or _ANCHOR_EXPECTED.get(field, "")


_ABS_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?"
    r"(Z|z|[+-]\d{2}:?\d{2})$")
_EPOCH_RE = re.compile(r"^-?\d{9,11}(?:\.\d+)?$")


def _offset_tz(tok):
    """'+05:30' / 'Z' -> tzinfo (manual parse: py3.9 fromisoformat
    refuses some of these; stdlib-only determinism)."""
    if tok in ("Z", "z"):
        return _UTC
    sign = 1 if tok[0] == "+" else -1
    body = tok[1:].replace(":", "")
    return timezone(sign * timedelta(hours=int(body[:2]),
                                     minutes=int(body[2:])))


def _server_anchor(zone_name, wall):
    """WHAT THE SERVER DOES: naive.replace(tzinfo=zone) — PEP 495
    fold=0, silent. Returns (aware utc dt, applied offset, abbrev)."""
    dt = _parse_local(wall).replace(tzinfo=_zone(zone_name))
    return dt.astimezone(_UTC), dt.utcoffset(), dt.tzname()


def _drift_minutes(a_iso, b_iso):
    """(b − a) signed whole seconds; positive = b later."""
    da = datetime.fromisoformat(a_iso)
    db = datetime.fromisoformat(b_iso)
    return int((db - da).total_seconds())


def _drift_block(secs, ref_label):
    if secs == 0:
        verdict = "no drift on this stamp: both clocks anchor the same " \
                  "instant (ref: %s)" % ref_label
    else:
        verdict = "the job fires %d min %s (ref: %s)" % (
            abs(secs) // 60, "LATE" if secs > 0 else "EARLY", ref_label)
        if abs(secs) % 60:
            verdict += " + %d s" % (abs(secs) % 60)
    return {"seconds": secs,
            "minutes": secs // 60 if secs >= 0 else -((-secs) // 60),
            "sign_rule": "positive = fires LATER than intended",
            "verdict": verdict}


def _instants_of(cl):
    if cl["kind"] == "single":
        return [cl["utc"]]
    if cl["kind"] == "fold":
        return [i["utc"] for i in cl["instants"]]
    return [n["utc"] for n in cl["nearest"]]  # gap: both neighbors


def _wall_in(utc_iso, zone_name):
    return datetime.fromisoformat(utc_iso).astimezone(
        _zone(zone_name)).isoformat()


def run_anchor(args):
    stamp = args.get("stamp")
    if not isinstance(stamp, str) or not stamp.strip():
        raise AnchorError("stamp", _ANCHOR_EXPECTED["stamp"])
    stamp = stamp.strip()
    if _EPOCH_RE.match(stamp):
        raise AnchorError("stamp", "epoch numbers are ALREADY absolute "
                                   "instants — no two-clock conflict to "
                                   "analyze; read them with "
                                   "/api/v1/date/parse")

    run_zone = args.get("run_in")
    if not run_zone or not str(run_zone).strip():
        raise AnchorError("run_in", "the machine's zone is never "
                                    "guessed (nanobot #408: the tz "
                                    "field existed and was never read)")
    run_zone = str(run_zone).strip()
    try:
        _zone(run_zone)
    except DateError:
        raise AnchorError("run_in", "unknown timezone %r — an IANA "
                                    "name or UTC, never a guess"
                          % args.get("run_in"))

    meant_zone = (args.get("meant_in") or "").strip()
    if meant_zone:
        try:
            _zone(meant_zone)
        except DateError:
            raise AnchorError("meant_in", "unknown timezone %r — an "
                                          "IANA name or UTC"
                              % args.get("meant_in"))
    abs_m = _ABS_RE.match(stamp)

    if abs_m:
        # -------- absolute stamp: the Composio arbitration path
        wall = stamp[:abs_m.start(5)].replace("T", " ")
        off = _offset_tz(abs_m.group(5))
        dt = _parse_local(wall).replace(tzinfo=off)
        true_utc = dt.astimezone(_UTC)
        out = {
            "stamp": stamp, "stamp_kind": "absolute",
            "instant_utc": true_utc.isoformat(),
            "offset_wins": "resolution published in Composio #4148: an "
                           "explicit Z or numeric offset IDENTIFIES "
                           "the instant and is preserved even when a "
                           "timezone field is also supplied — the zone "
                           "only re-renders the wall clock",
        }
        if meant_zone:
            out["wall_in_meant"] = _wall_in(true_utc.isoformat(),
                                            meant_zone)
        # the misread a buggy scheduler commits: drop the offset, anchor
        # the wall clock in the RUN zone (fold=0, silently)
        mis_dt, mis_off, mis_abb = _server_anchor(run_zone, wall)
        mis_utc = mis_dt.isoformat()
        secs = _drift_minutes(true_utc.isoformat(), mis_utc)
        out["misparsed_if_offset_dropped"] = {
            "run_in": run_zone, "utc": mis_utc,
            "offset": _fmt_off(mis_off), "tz_abbrev": mis_abb,
            "drift": _drift_block(
                secs, "true instant vs the naive re-anchor"),
            "rule": "this is the shape of the bug, not the answer: the "
                    "true instant above stands; only code that STRIPS "
                    "the offset and stamps run_in wall time books this",
        }
        if args.get("stamped_offset"):
            raise AnchorError("stamped_offset", "refused with an "
                                                "absolute stamp — the "
                                                "stamp already says "
                                                "its offset; the "
                                                "stamping bug only "
                                                "exists for NAIVE "
                                                "stamps")
        out["scope_note"] = (
            "computed from the IANA tz database installed on this "
            "server via zoneinfo — no embedded table, no fetch, no "
            "clock read: the stamp IS the date, and offsets are the "
            "ones IN FORCE ON THAT DATE (the PraisonAI fix's own "
            "correction)")
        return out

    # -------- naive stamp: the two-clock conflict
    if not meant_zone:
        raise AnchorError("meant_in", "required with a naive stamp — "
                                      "one wall clock + one zone is "
                                      "date/tz_ambiguity's contract; "
                                      "this route exists for the "
                                      "conflict BETWEEN clocks")
    try:
        meant_cl = classify(meant_zone, stamp)
        run_cl = classify(run_zone, stamp)
    except (TzAmbError, DateError) as e:
        raise AnchorError("stamp", str(e))

    meant_inst = _instants_of(meant_cl)
    # the server's silent anchor = fold=0 replace (what
    # .replace(tzinfo=)/.astimezone() actually compute)
    run_dt, run_off, run_abb = _server_anchor(run_zone, stamp)
    run_utc = run_dt.isoformat()

    out = {
        "stamp": stamp, "stamp_kind": "naive",
        "meant_in": {"zone": meant_cl["zone"], "kind": meant_cl["kind"],
                     "instants": meant_inst,
                     "verdict": meant_cl["verdict"]},
        "run_in": {"zone": run_cl["zone"], "kind": run_cl["kind"],
                   "server_anchor_utc": run_utc,
                   "offset": _fmt_off(run_off), "tz_abbrev": run_abb},
        "server_anchor_rule": "what naive.replace(tzinfo=run_in) / "
                              "astimezone() silently compute: PEP 495 "
                              "fold=0 — the FIRST pass for a repeated "
                              "hour, the pre-offset reading for a "
                              "skipped hour",
    }

    if meant_cl["kind"] == "single":
        secs = _drift_minutes(meant_inst[0], run_utc)
        out["drift"] = _drift_block(secs, "the single intended instant")
        out["readback"] = {
            "intended_seen_in_run_wall": _wall_in(meant_inst[0],
                                                  run_zone),
            "server_fire_seen_in_meant_wall": _wall_in(run_utc,
                                                       meant_zone),
            "rule": "the two wall clocks the humans on each side "
                    "ACTUALLY see — meho #2339: 'different but "
                    "plausibly equivalent' stops being a feeling",
        }
    elif meant_cl["kind"] == "fold":
        out["drift"] = [
            dict(_drift_block(_drift_minutes(ins, run_utc),
                              "repeated wall clock, pass %d" % (i + 1)),
                 **{"against": "instant[%d]" % i})
            for i, ins in enumerate(meant_inst)]
    else:  # gap
        out["drift"] = _drift_block(
            _drift_minutes(meant_inst[-1], run_utc),
            "first valid wall clock AFTER the jump (the nearest)")
        out["gap_note"] = (
            "the wall clock NEVER occurs in %s: the nearest valid "
            "neighbors are %s and %s — a scheduler still anchors the "
            "impossible string to %s UTC silently"
            % (meant_cl["zone"], meant_inst[0], meant_inst[1], run_utc))

    if args.get("stamped_offset"):
        so = str(args["stamped_offset"]).strip()
        if not re.match(r"^[+-]\d{2}:?\d{2}$", so):
            raise AnchorError("stamped_offset", "expected '+HH:MM' / "
                                                "'-HHMM' — the numeric "
                                                "offset your code "
                                                "stamped")
        off_tz = _offset_tz(so)
        stamped = _parse_local(stamp).replace(tzinfo=off_tz) \
            .astimezone(_UTC)
        anchor_dt = datetime.fromisoformat(run_utc).astimezone(
            _zone(run_zone))
        secs = _drift_minutes(run_utc, stamped.isoformat())
        guard = {
            "stamped_offset": so,
            "offset_in_force_that_date": _fmt_off(anchor_dt.utcoffset()),
            "stamped_utc": stamped.isoformat(),
            "drift": _drift_block(secs, "date-correct run anchor"),
        }
        if secs == 0:
            guard["verdict"] = ("the write-time offset equals the "
                                "offset IN FORCE ON THAT DATE — this "
                                "stamp survives the bug")
        else:
            guard["verdict"] = (
                "PRAISONAI #4732 bug replayed: stamping 'the offset "
                "in force NOW' instead of the offset IN FORCE ON THAT "
                "DATE moves this instant by %d min — 'an hour wrong "
                "for any date on the other side of a DST change'"
                % (secs // 60))
        out["stamped_offset_guard"] = guard

    for key, cl in (("transition_meant", meant_cl),
                    ("transition_run", run_cl)):
        if "transition" in cl:
            out[key] = cl["transition"]
    out["scope_note"] = (
        "computed from the IANA tz database installed on this server "
        "via zoneinfo — no embedded table, no fetch, no clock read; "
        "instants for PAST and FUTURE dates are the ones tzdata "
        "encodes for that date. This route DIAGNOSES the two-clock "
        "conflict; which clock to trust stays yours — anchor at write "
        "time (store absolute) is the fix every thread above "
        "converged on")
    return out
