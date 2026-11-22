"""Bundle 29 lot 3 — ICS lint (RFC 5545).

The rules implemented are the MUST-level ones a calendar client will
actually enforce: unfolding (line folding = CRLF + horizontal whitespace),
component BEGIN/END pairing and nesting, the required properties per
component type, iana-token;PARAM=VALUE property syntax, DTSTART present
with a legal value type, DTEND same type as DTSTART (date vs
date-time) and never before it, VERSION on VCALENDAR.

Anything the spec leaves as MAY is reported as a warning, never an
error — a lint that invents rules is worse than no lint.
"""
import re

_REQ = {
    "VCALENDAR": ["VERSION", "PRODID"],
    "VEVENT": ["UID", "DTSTAMP", "DTSTART"],
    "VTODO": ["UID", "DTSTAMP"],
    "VJOURNAL": ["UID", "DTSTAMP"],
    "VALARM": ["ACTION", "TRIGGER"],
    "VTIMEZONE": ["TZID"],
    "STANDARD": ["TZOFFSETTO", "TZNAME", "DTSTART"],
    "DAYLIGHT": ["TZOFFSETTO", "TZNAME", "DTSTART"],
}
_ALLOWED_TOP = {"VCALENDAR"}
_NEST = {"VCALENDAR": {"VEVENT", "VTODO", "VJOURNAL", "VFREEBUSY",
                       "VALARM", "VTIMEZONE"},
          "VTIMEZONE": {"STANDARD", "DAYLIGHT"},
          "VEVENT": {"VALARM"},
          "VTODO": {"VALARM"},
          "VJOURNAL": {"VALARM"}}
_DATE_RE = re.compile(r"^\d{8}$")
_DT_RE = re.compile(r"^\d{8}T\d{6}(Z|[+-]\d{4})?$")
_PROP_RE = re.compile(r"^([A-Za-z0-9-]+)((;[^\s:].*)?):(.*)$", re.S)


def _unfold(text):
    lines = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        elif raw:
            lines.append(raw)
    return lines


def ics_lint(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text: non-empty VCALENDAR required")
    if len(text.encode("utf-8")) > 2 * 1024 * 1024:
        raise ValueError("ics exceeds the 2 MB lint cap")
    lines = _unfold(text)
    errors = []
    warnings = []
    stack = []
    props = []          # (component_path, NAME, value)
    counts = {}
    started = ended = 0
    # raw-line length warning uses the SOURCE lines (folding exists
    # precisely to keep them under 75 octets — RFC 5545 §3.1)
    for i, raw in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        if len(raw.encode("utf-8")) > 75:
            warnings.append({"line": i, "code": "long_physical_line",
                             "message": "physical line exceeds 75 octets "
                                        "(SHOULD be folded, §3.1)"})
    for i, line in enumerate(lines, 1):
        m2 = re.match(r"^(BEGIN|END):([A-Za-z0-9-]+)$", line)
        m = None
        if m2:
            kind, comp = m2.groups()
            comp = comp.upper()
            if kind == "BEGIN":
                started += 1
                counts[comp] = counts.get(comp, 0) + 1
                if not stack and comp not in _ALLOWED_TOP:
                    errors.append({"line": i, "code": "top_component",
                                   "message": "file must start inside "
                                              "VCALENDAR, got %s" % comp})
                elif stack and comp not in _NEST.get(stack[-1], set()):
                    errors.append({"line": i, "code": "bad_nesting",
                                   "message": "%s cannot live inside %s"
                                              % (comp, stack[-1])})
                stack.append(comp)
            else:
                ended += 1
                if not stack:
                    errors.append({"line": i, "code": "unmatched_end",
                                   "message": "END:%s without BEGIN" % comp})
                elif stack[-1] != comp:
                    errors.append({"line": i, "code": "mismatched_end",
                                   "message": "END:%s closes open %s"
                                              % (comp, stack[-1])})
                    stack.pop()
                else:
                    stack.pop()
        else:
            m = _PROP_RE.match(line)
            if not m:
                errors.append({"line": i, "code": "invalid_content_line",
                               "message": "not name[:params]value"})
                continue
            name, params, value = (m.group(1).upper(), m.group(2),
                                   m.group(4))
            if stack:
                props.append(("/".join(stack), name, value, i, params))
            else:
                errors.append({"line": i, "code": "property_outside",
                               "message": "content property outside any "
                                          "component"})
    if stack:
        for comp in stack:
            errors.append({"line": 0, "code": "unclosed_component",
                           "message": "BEGIN:%s never closed" % comp})
    if started == 0:
        errors.append({"line": 1, "code": "no_calendar",
                       "message": "no BEGIN:VCALENDAR found"})

    # required properties
    by_comp = {}
    for path, name, value, ln, params in props:
        by_comp.setdefault(path, []).append((name, value, ln, params))
    for path, plist in by_comp.items():
        comp = path.split("/")[-1]
        need = _REQ.get(comp, [])
        have = {n for n, _v, _l, _p in plist}
        for req in need:
            if req not in have:
                errors.append({"line": plist[0][2],
                               "code": "missing_required",
                               "message": "%s requires %s (RFC 5545 §3.6)"
                                          % (comp, req)})
    # value-type rules for events
    for path, plist in by_comp.items():
        if not path.endswith("VEVENT"):
            continue
        start = next((p for p in plist if p[0] == "DTSTART"), None)
        end = next((p for p in plist if p[0] == "DTEND"), None)
        if start:
            v = start[1]
            if not (_DATE_RE.match(v) or _DT_RE.match(v)):
                errors.append({"line": start[2], "code": "bad_dtstart",
                               "message": "DTSTART %r is neither DATE nor "
                                          "DATE-TIME" % v})
                continue
            if _DT_RE.match(v) and "TZID=" not in start[3].upper() \
                    and not v.endswith("Z"):
                warnings.append({"line": start[2],
                                 "code": "floating_time",
                                 "message": "DTSTART date-time without TZID "
                                            "or Z is 'floating' — legal but "
                                            "the #1 DST bug source"})
        if start and end:
            sv, ev = start[1], end[1]
            s_is_date = bool(_DATE_RE.match(sv))
            e_is_date = bool(_DATE_RE.match(ev))
            if s_is_date != e_is_date:
                errors.append({"line": end[2], "code": "dtstart_dtend_mixed",
                               "message": "all-day (DATE) event cannot have "
                                          "a DATE-TIME DTEND or vice versa"})
            elif ev < sv:
                errors.append({"line": end[2], "code": "dtend_before_start",
                               "message": "DTEND %r precedes DTSTART %r"
                                          % (ev, sv)})
    # VERSION check
    ver = [p for p in props if p[1] == "VERSION"]
    for path, name, value, ln, params in ver:
        if value != "2.0":
            errors.append({"line": ln, "code": "version",
                           "message": "VERSION must be 2.0, got %r" % value})

    sev = [e for e in errors]
    return {"valid": not sev, "errors": sev, "warnings": warnings,
            "components": counts, "content_lines": len(lines),
            "rfc": "5545 §3 (syntax), §3.6 (components)"}
