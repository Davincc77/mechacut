"""Deterministic code-editing transforms (Bundle 2): patch, diff, apply,
path normalization, glob matching, env interpolation.

Pure functions. No filesystem access, no LLM, no storage. Paths are
normalized lexically — this module never touches disk.
"""

import difflib
import posixpath as _posixpath
import ntpath as _ntpath
import re


class EditError(Exception):
    pass


# ------------------------------------------------------------- text/patch

def text_patch(text, edits):
    """Apply find/replace edits in order. Each edit needs exactly one match
    by default ('occurrences': \"one\" | \"all\" | exact int) — the agent
    never guesses whether a rename landed."""
    if not isinstance(edits, list) or not edits:
        raise EditError("edits must be a non-empty array")
    cur = text
    applied = 0
    for e_idx, e in enumerate(edits):
        if not isinstance(e, dict):
            raise EditError("edits[%d]: must be an object" % e_idx)
        find = e.get("find")
        repl = e.get("replace")
        occ = e.get("occurrences", "one")
        if not isinstance(find, str) or find == "":
            raise EditError("edits[%d]: 'find' must be a non-empty string" % e_idx)
        if not isinstance(repl, str):
            raise EditError("edits[%d]: 'replace' must be a string" % e_idx)
        n = cur.count(find)
        if occ == "one":
            if n != 1:
                raise EditError("edits[%d]: found %d occurrence(s) of find, "
                                "expected exactly 1 (use \"all\" or the exact "
                                "count)" % (e_idx, n))
            cur = cur.replace(find, repl, 1)
        elif occ == "all":
            if n == 0:
                raise EditError("edits[%d]: find not found" % e_idx)
            cur = cur.replace(find, repl)
        elif isinstance(occ, int) and not isinstance(occ, bool) and occ >= 1:
            if n != occ:
                raise EditError("edits[%d]: found %d occurrence(s), expected "
                                "exactly %d" % (e_idx, n, occ))
            cur = cur.replace(find, repl, occ)
        else:
            raise EditError("edits[%d]: 'occurrences' must be \"one\", "
                            "\"all\" or an integer >= 1" % e_idx)
        applied += 1
    return cur, applied


# -------------------------------------------------------------- text/diff

def _diff_body(a, b, context):
    la = a.splitlines()
    lb = b.splitlines()
    return list(difflib.unified_diff(la, lb, fromfile="before", tofile="after",
                                     lineterm="", n=context))


def text_diff(a, b, context=3):
    """Unified line diff with fixed labels (\"before\"/\"after\") and \\n
    endings — same pair in, same diff bytes out, always."""
    lines = _diff_body(a, b, context)
    diff = "\n".join(lines) + "\n" if lines else ""
    return diff, lines


def diff_stats(lines):
    hunks = sum(1 for l in lines if l.startswith("@@"))
    added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    return hunks, added, removed


# --------------------------------------------------------- text/apply-diff

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _parse_hunks(diff):
    hunks = []
    cur = None
    for d in diff.split("\n"):
        m = _HUNK.match(d)
        if m:
            cur = {"start": int(m.group(1)), "body": []}
            hunks.append(cur)
            continue
        if cur is None:
            continue  # --- / +++ headers and preamble are ignored
        if d.startswith("+"):
            cur["body"].append(("+", d[1:]))
        elif d.startswith("-"):
            cur["body"].append(("-", d[1:]))
        elif d.startswith(" "):
            cur["body"].append((" ", d[1:]))
        elif d.startswith("\\"):
            continue  # "\ No newline at end of file": not represented
    if not hunks:
        raise EditError("no @@ hunk found in diff")
    return hunks


def text_apply_diff(text, diff):
    """Apply a unified diff strictly: every context/deletion line must match
    its documented position exactly — no fuzz, no silent reflow. Mismatches
    report the hunk number and the offending line."""
    lines = text.split("\n")
    if text.endswith("\n"):
        lines.pop()
    out = list(lines)
    delta = 0
    added = removed = 0
    hunks = _parse_hunks(diff)
    for h_idx, h in enumerate(hunks):
        i = h["start"] - 1 + delta
        if i < 0 or i > len(out):
            raise EditError("hunk %d: start line %d is outside the file "
                            "(%d lines)" % (h_idx, h["start"], len(out)))
        a0, r0 = added, removed
        for kind, ln in h["body"]:
            if kind == " ":
                if i >= len(out) or out[i] != ln:
                    found = "<EOF>" if i >= len(out) else out[i]
                    raise EditError("hunk %d: context mismatch at line %d: "
                                    "expected %r, found %r"
                                    % (h_idx, i + 1, ln[:80], found[:80]))
                i += 1
            elif kind == "-":
                if i >= len(out) or out[i] != ln:
                    found = "<EOF>" if i >= len(out) else out[i]
                    raise EditError("hunk %d: deletion mismatch at line %d: "
                                    "expected %r, found %r"
                                    % (h_idx, i + 1, ln[:80], found[:80]))
                del out[i]
                removed += 1
            else:
                out.insert(i, ln)
                added += 1
                i += 1
        delta += (added - a0) - (removed - r0)
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), \
        len(hunks), added, removed


# --------------------------------------------------------- path/normalize

def path_normalize(path, target_os="auto", case="keep"):
    """Lexical path normalization to POSIX form. Never touches the
    filesystem; `..` is resolved lexically and never climbs above the start
    of a relative path. POSIX keeps a leading `//` per spec."""
    if not isinstance(path, str) or not path.strip():
        raise EditError("path must be a non-empty string")
    if target_os not in ("auto", "posix", "windows"):
        raise EditError("target_os must be \"auto\", \"posix\" or \"windows\"")
    if case not in ("keep", "lower"):
        raise EditError("case must be \"keep\" or \"lower\"")
    p = path.strip()
    win = target_os == "windows" or (target_os == "auto" and "\\" in p)
    if target_os == "posix" or (target_os == "auto" and not win):
        p = p.replace("\\", "/")
    else:
        p = re.sub(r"\\+", "/", p)
    if case == "lower":
        p = p.lower()
    mod = _ntpath if win else _posixpath
    norm = mod.normpath(p) if p else "."
    norm = norm.replace("\\", "/")
    absolute = norm.startswith("/") or bool(_ntpath.splitdrive(norm)[0]) \
        or (win and p.startswith("/"))
    if win and p.startswith("/") and not norm.startswith("/"):
        norm = "/" + norm
    name = norm.rsplit("/", 1)[-1] if "/" in norm else norm
    if norm in ("", "."):
        name = "."
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    return {"path": norm or ".", "absolute": absolute, "name": name,
            "stem": stem, "extension": ext}


# ------------------------------------------------------------- glob/match

def _seg_match(pat_seg, seg):
    if "*" in pat_seg or "?" in pat_seg:
        rx = "^"
        for ch in pat_seg:
            if ch == "*":
                rx += "[^/]*"
            elif ch == "?":
                rx += "[^/]"
            else:
                rx += re.escape(ch)
        return re.match(rx + "$", seg) is not None
    return pat_seg == seg


def _glob_segments(psegs, ssegs):
    if not psegs:
        return not ssegs
    p0 = psegs[0]
    if p0 == "**":
        for k in range(len(ssegs) + 1):
            if _glob_segments(psegs[1:], ssegs[k:]):
                return True
        return False
    if not ssegs or not _seg_match(p0, ssegs[0]):
        return False
    return _glob_segments(psegs[1:], ssegs[1:])


def glob_match(pattern, paths):
    """Deterministic glob: `*` and `?` do not cross `/`, `**` spans any
    number of segments, `.foo` is matched explicitly (no dotfile magic),
    case-sensitive. Input order preserved."""
    if not isinstance(pattern, str) or pattern == "":
        raise EditError("pattern must be a non-empty string")
    psegs = pattern.split("/")
    absolute = pattern.startswith("/")
    matched = []
    for cand in paths:
        if not isinstance(cand, str):
            raise EditError("paths must be strings")
        csegs = cand.split("/")
        c_abs = cand.startswith("/")
        if c_abs != absolute:
            continue
        if _glob_segments(psegs, csegs):
            matched.append(cand)
    return matched


# ------------------------------------------------------- env/interpolate

_VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}"
                  r"|\$([A-Za-z_][A-Za-z0-9_]*)")


def env_interpolate(template, variables, strict=True):
    """Expand $VAR and ${VAR} / ${VAR:-default}. Strict (default): a missing
    variable is an error naming every one of them. Non-strict: missing vars
    stay literal and are reported in `missing`."""
    if not isinstance(template, str):
        raise EditError("template must be a string")
    if not isinstance(variables, dict):
        raise EditError("vars must be an object of string values")
    missing = []
    count = [0]

    def sub(m):
        name = m.group(1) or m.group(3)
        default = m.group(2)
        if name in variables:
            count[0] += 1
            return str(variables[name])
        if default is not None:
            count[0] += 1
            return default
        if name not in missing:
            missing.append(name)
        return m.group(0)

    out = _VAR.sub(sub, template)
    if strict and missing:
        raise EditError("missing variables: %s (use ${VAR:-default} or "
                        "strict=false)" % ", ".join(missing))
    return out, count[0], missing


NPM_RE = re.compile(r"^[a-z0-9][a-z0-9._~%+@!-]{0,215}$")
PYPI_RE = re.compile(r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", re.I)
DOCKER_REPO_RE = re.compile(
    r"^[a-z0-9]+(?:(?:[._]|__|-+)?[a-z0-9]+)*(?:/[a-z0-9]+"
    r"(?:(?:[._]|__|-+)?[a-z0-9]+)*)*$")
DOCKER_TAG_RE = re.compile(r"^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$")


def pkgname_op(name, kind="npm"):
    """Package-name grammar verdicts (closed rules, published grammars):
    npm (validate-npm-package-name core), PyPI (PEP 503 normalize+match),
    Docker (distribution repo/tag grammar). Agents invent uppercase npm
    names and dotted docker tags daily; this says so, precisely."""
    if not isinstance(name, str) or not name:
        raise EditError("name must be a non-empty string")
    errors = []
    normalized = name
    if kind == "npm":
        if name != name.lower():
            errors.append("npm names must be lowercase")
        if name.startswith((".", "_")):
            errors.append("cannot start with . or _")
        if len(name) > 216:
            errors.append("longer than 216 chars")
        if name.strip() != name:
            errors.append("has leading/trailing whitespace")
        if not NPM_RE.match(name.strip().lower()):
            errors.append("contains characters outside [a-z0-9._~%+@!-]")
        normalized = name.strip().lower()
    elif kind == "pypi":
        if not PYPI_RE.match(name):
            errors.append("invalid project name (PEP 503)")
        normalized = re.sub(r"[-_.]+", "-", name).lower()
    elif kind == "docker":
        ref = name
        registry = None
        if "/" in ref and "." in ref.split("/")[0]:
            registry, ref = ref.split("/", 1)
        tag = None
        digest = None
        if "@" in ref:
            ref, digest = ref.split("@", 1)
            if not re.match(r"^sha256:[0-9a-f]{64}$", digest):
                errors.append("digest must be sha256:64hex")
        if ":" in ref.rsplit("/", 1)[-1]:
            ref, tag = ref.rsplit(":", 1)
            if not DOCKER_TAG_RE.match(tag):
                errors.append("invalid tag (start alnum, [a-zA-Z0-9._-], "
                              "<=128)")
        if not DOCKER_REPO_RE.match(ref):
            errors.append("invalid repository name (lowercase path "
                          "components, [._-] separators)")
        normalized = ((registry + "/") if registry else "") + ref \
                     + (":" + tag if tag else "") \
                     + ("@" + digest if digest else "")
    else:
        raise EditError("unknown kind: %r (npm, pypi, docker)" % kind)
    return {"kind": kind, "name": name, "valid": not errors,
            "normalized": normalized, "errors": errors}
