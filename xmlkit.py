"""xmlkit — XML → JSON with the conversion rules PRINTED IN THE RESPONSE.

Every XML→JSON converter takes six decisions for you and almost none
say which (the industry's own words: "your XML has three books, your
JSON has one — the converter chose wrong"). This machine cannot
guarantee a correct guess, so it guarantees the opposite: the rules are
explicit, caller-adjustable where ambiguity is real, and listed in
every answer under `rules_applied`.

The v1 rules (closed, documented, stable):
  1. element            → key = tag name exactly as written
  2. attributes         → "@name" keys inside the element's object
  3. text-only element  → its text (a string; scalar replaces the object)
  4. empty element      → null
  5. text alongside attributes or children → "#text"; whitespace-only
     text next to children is dropped
  6. repeated siblings  → array in document order; force_array=[paths]
     pins a path to array even at cardinality 1 — the one-item bug
     that "works in testing with three fixtures and throws in
     production with one"
  7. namespaces         → prefixes KEPT exactly as written; no URI
     resolution, no default-namespace folding (v1, declared)
  8. comments/PIs       → dropped but COUNTED in "discarded"
  9. <!DOCTYPE          → refused by name (external entities & bombs);
     this server never parses a DTD
 10. values are strings; coerce=true converts ONLY unambiguous numbers
     (^-?(0|[1-9]\\d*)(\\.\\d+)?([eE][-+]?\\d+)?$ — leading zeros stay
     strings: 00713 is an identifier) and exact lowercase
     true/false/null.
"""
import re
from xml.parsers import expat

MAX_DEPTH = 200
NUM_RE = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][-+]?\d+)?$")


class XmlError(Exception):
    pass


def _coerce(s):
    if s == "true":
        return True
    if s == "false":
        return False
    if s == "null":
        return None
    if isinstance(s, str) and NUM_RE.match(s):
        return float(s) if any(c in s for c in ".eE") else int(s)
    return s


def _add_child(parent, tag, value, as_list):
    if as_list or tag in parent:
        cur = parent.get(tag)
        if cur is None:
            parent[tag] = [value]
        elif isinstance(cur, list):
            cur.append(value)
        else:
            parent[tag] = [cur, value]
    else:
        parent[tag] = value


def to_json(xml_text, force_array=None, coerce=False):
    if not isinstance(xml_text, str):
        try:
            xml_text = xml_text.decode("utf-8", "strict")
        except UnicodeDecodeError:
            raise XmlError("input is not valid UTF-8")
    if "<!DOCTYPE" in xml_text:
        raise XmlError("DTD refused by name — this server never parses "
                       "one (external entities, entity bombs); remove "
                       "the DOCTYPE or resolve it upstream")
    force = set(force_array or [])
    if any(not isinstance(x, str) or not x for x in force):
        raise XmlError('force_array must be a list of slash paths, '
                       'e.g. ["catalog/book"]')

    meta = {}          # id(node_dict) -> (parent_dict, tag, epath)
    holder = {"name": None, "node": None}
    counts = {"comments": 0, "processing_instructions": 0}

    p = expat.ParserCreate()
    p.buffer_text = True
    stack = []         # list of node dicts, innermost last

    def start(tag, attrs):
        if len(stack) + 1 > MAX_DEPTH:
            raise XmlError("nesting over %d deep — refusing "
                           "(structure bombs are not supported here)"
                           % MAX_DEPTH)
        parent = stack[-1] if stack else None
        epath = tag if not stack else \
            meta[id(parent)][2] + "/" + tag
        node = {}
        for a, v in attrs.items():
            node["@" + a] = _coerce(v) if coerce else v
        if holder["node"] is None:
            holder["name"], holder["node"] = tag, node
            meta[id(node)] = (None, tag, tag)   # root gets a path too
        else:
            _add_child(parent, tag, node, epath in force)
            meta[id(node)] = (parent, tag, epath)
        stack.append(node)

    def end(_tag):
        node = stack.pop()
        info = meta.pop(id(node), None)
        if info is None or info[0] is None:
            return                       # root: finalized after Parse
        parent, tag, epath = info
        text = node.pop("#text", None)
        if node:                         # attrs or child keys remain
            if text is not None and text.strip():
                node["#text"] = text
            value = node
        elif text is None or text == "" or text.strip() == "":
            value = None
        else:
            value = _coerce(text) if coerce else text
        current = parent.get(tag)
        if current is node:
            parent[tag] = value
        elif isinstance(current, list):
            for i, v in enumerate(current):
                if v is node:
                    current[i] = value
                    break

    def characters(data):
        if stack:
            node = stack[-1]
            node["#text"] = (node.get("#text") or "") + data

    def comment(_):
        counts["comments"] += 1

    def prolog(*_):
        counts["processing_instructions"] += 1

    p.StartElementHandler = start
    p.EndElementHandler = end
    p.CharacterDataHandler = characters
    p.CommentHandler = comment
    p.ProcessingInstructionHandler = prolog
    try:
        p.Parse(xml_text, True)
    except expat.ExpatError as e:
        raise XmlError("malformed XML: %s" % e)
    if holder["node"] is None:
        raise XmlError("no root element found")

    # finalize root the same way leaves finalize
    root_node = holder["node"]
    text = root_node.pop("#text", None)
    if root_node:
        if text is not None and text.strip():
            root_node["#text"] = text
        root_value = root_node
    else:
        root_value = None if not text else (
            _coerce(text) if coerce else text)

    rules = [
        "1 element=key as written",
        "2 attributes=@name",
        "3 text-only element=scalar string",
        "4 empty element=null",
        "5 mixed text=#text (whitespace-only text beside children "
        "dropped)",
        "6 repeated siblings=array"
        + ("; force_array=%s" % sorted(force) if force else ""),
        "7 namespace prefixes kept raw (no URI resolution, v1)",
        "8 comments=%d PIs=%d dropped, counted" % (
            counts["comments"], counts["processing_instructions"]),
        "9 DTD refused by name",
        "10 " + ("coerce=true: bare numbers/true/false/null only; "
                 "leading zeros stay strings"
                 if coerce else "all values stay strings"),
    ]
    out = {"json": {holder["name"]: root_value},
           "root": holder["name"], "rules_applied": rules,
           "discarded": counts}
    return out
