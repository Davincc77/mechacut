"""moneykit — /csv/money_columns : lire une colonne de montants sans
JAMAIS deviner une valeur isolée.

La douleur d'origine (r/ClaudeAI, nov. 2026 — « Claude hallucinating
decimal points in financial CSVs », $100.50 relu $10 050,00) : un parseur
par valeur tranche l'ambigu (« 1.234 » = mille-deux-cent-trente-quatre
ou un-point-deux-cent-trente-quatre ?) au hasard du locale supposé.

Ici la convention n'est PAS supposée : elle est DÉMONTRÉE par les valeurs
non ambiguës de la même colonne.
  * une colonne qui contient « 1,234.56 » a prouvé le style US → « 1.234 »
    y vaut 1.234 (décimal), résolu ET tracé (resolved_by_column_convention)
  * une colonne qui contient « 1,234.56 » ET « 1.234,56 » est
    CONTRADICTOIRE : les deux styles y sont prouvés → chaque valeur
    ambiguë est refusée avec ses deux lectures, jamais tranchée
  * aucune preuve → ambiguïté signalée, lecture(s) listées, montant vide
Toujours : ligne, brute, décision, et pourquoi — la colonne rend un
verdict, pas des secrets.
"""
import csv
import io
import re
from decimal import Decimal

import numfmt
from numfmt import num_parse


class MoneyError(Exception):
    pass


MONEY_HINT = re.compile(r"\d")
SYMBOLS = set("$€£¥R")


def _cells_column(rows, idx):
    return [(r + 1, (row[idx] if idx < len(row) else "").strip())
            for r, row in enumerate(rows)]


def _style_of(text):
    """classify an unambiguously-parseable numeric string by the
    separator pattern that made it unambiguous."""
    if re.search(r"\d,\d{3}(\.\d)?", text) or \
            re.search(r"^[-+]?[$€£¥R]?\s*\d{1,3}(,\d{3})+", text):
        return "us"
    if re.search(r"\d\.\d{3},\d", text) or re.search(r"\d \d{3},\d", text):
        return "eu"
    return "plain"


def analyze(csv_text, columns=None, header=None, delimiter=None):
    text = (csv_text or "").lstrip("")
    if not text.strip():
        raise MoneyError("empty csv")
    if header is False and not isinstance(header, list):
        raise MoneyError("header must be a list or omitted")
    # delimiter: the caller's word, else csv.Sniffer — its test is
    # EXACTLY the right one (a real delimiter recurs consistently across
    # lines; a decimal comma does not). Sniffer failure = no consistent
    # delimiter = single-column file.
    if delimiter:
        delim = delimiter
    else:
        try:
            delim = csv.Sniffer().sniff(text[:8000],
                                        delimiters=",;\t|").delimiter
        except csv.Error:
            delim = None             # no recurring delimiter: one column
    if delim is None:
        rows = [[ln] for ln in text.splitlines() if ln.strip()]
    else:
        try:
            rows = list(csv.reader(io.StringIO(text), delimiter=delim))
        except csv.Error as e:
            raise MoneyError("csv parse error: %s" % e)

    def _rejoin(row):
        """re-merge a field split by its OWN thousands comma:
        '1' + '234.56' → '1,234.56'. Only digits-3 clusters qualify."""
        out, j, n = [], 0, len(row)
        while j < n:
            cur = row[j].strip()
            while (j + 1 < n and delim == ","
                   and re.fullmatch(r"[-+]?\d{1,3}", cur)
                   and re.match(r"^\d{3}(\D|$)", row[j + 1].strip())):
                j += 1
                cur = cur + "," + row[j].strip()
            out.append(cur)
            j += 1
        return out

    # shape choice: if rejoining thousands commas makes MORE rows agree on
    # one width than raw parsing, the file is money-shaped, not wider.
    def _mode_width(rs):
        from collections import Counter
        c = Counter(len(r) for r in rs if any(x.strip() for x in r))
        return c.most_common(1)[0] if c else (0, 0)
    body_only = rows[1:] if len(rows) > 1 else rows
    raw_w, raw_n = _mode_width(body_only)
    joined = [_rejoin(r) for r in rows]
    jn_w, jn_n = _mode_width(joined[1:] if len(joined) > 1 else joined)
    shape_note = None
    if jn_w < raw_w and jn_n > raw_n:
        rows = joined
        shape_note = ("thousands commas rejoined before parsing: the file "
                      "is %d-column with grouped numbers, not %d-column"
                      % (jn_w, raw_w))
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        raise MoneyError("no rows")
    if isinstance(header, list):
        names = header
        body = rows
    else:
        names = [c.strip() for c in rows[0]]
        body = rows[1:]
        if not names or any(not n for n in names) or \
                any(re.search(r"\d{2}|\d,\d", n) for n in names):
            # looks like data, not a header — first row stays a row
            names = ["col%d" % (i + 1) for i in range(len(rows[0]))]
            body = rows
    if columns:
        idxs = []
        for c in columns:
            if isinstance(c, int) or (isinstance(c, str) and c.isdigit()):
                i = int(c)
                if not 0 <= i < len(names):
                    raise MoneyError("column index %d out of range "
                                     "(%d columns)" % (i, len(names)))
            else:
                try:
                    i = names.index(str(c))
                except ValueError:
                    raise MoneyError("unknown column %r — available: %s"
                                     % (c, ", ".join(names)))
            idxs.append(i)
    else:
        idxs = range(len(names))
    out_cols = []
    for i in idxs:
        cells = _cells_column(body, i)
        vals = [v for _, v in cells if v != ""]
        numeric, ambiguous_rows, plain_rows = 0, [], []
        style_counter = {"us": 0, "eu": 0, "plain": 0}
        sample = []
        money_ish = 0
        for line, v in cells:
            if v == "":
                continue
            if not MONEY_HINT.search(v):
                continue
            if any(ch in SYMBOLS for ch in v):
                money_ish += 1
            try:
                r = num_parse(v, None)
                # parseable WITHOUT preference → unambiguous evidence
                st = _style_of(v)
                style_counter[st] += 1
                numeric += 1
                if len(sample) < 3:
                    sample.append({"row": line, "raw": v,
                                   "value": r["decimal_string"],
                                   "how": "unambiguous"})
            except numfmt.NumberError:
                # try both readings to expose them
                readings = {}
                for pref in ("decimal", "group"):
                    try:
                        readings[pref] = num_parse(
                            v, pref)["decimal_string"]
                    except numfmt.NumberError:
                        pass
                if not readings:
                    plain_rows.append({"row": line, "raw": v,
                                       "why": "not a number"})
                else:
                    ambiguous_rows.append({"row": line, "raw": v,
                                           "readings": readings})
        total = numeric + len(ambiguous_rows)
        if total == 0:
            continue                      # column carries no numbers
        # dominant proven style (ambiguous cells excluded from evidence)
        proven = [s for s in ("us", "eu") if style_counter[s]]
        contradictory = len(proven) > 1
        if style_counter["plain"] and not proven:
            convention = "plain"
        elif contradictory:
            convention = "CONTRADICTORY"
        else:
            convention = proven[0] if proven else "plain"
        resolved, unresolved = [], []
        for a in ambiguous_rows:
            rd = a["readings"]
            # « 1.234 » : decimal pref keeps the dot as decimal point,
            # group pref reads it as a thousands separator
            low, high = (rd.get("decimal"), rd.get("group"))
            guess = None
            if not contradictory and convention in ("us", "eu") \
                    and low is not None and high is not None:
                guess = low if convention == "us" else high
                note = ("resolved by column convention (%s style "
                        "proven by %d unambiguous values)"
                        % (convention, style_counter[convention]))
                resolved.append({**a, "value": guess, "why": note})
            else:
                why = ("column proves BOTH us and eu styles — refusing "
                       "to pick") if contradictory else \
                    ("no unambiguous style evidence in this column — "
                     "both readings kept")
                unresolved.append({**a, "why": why})
        nonempty = [v for _, v in cells if v]
        money_like = money_ish > 0 or any(
            ("." in x or "," in x) and MONEY_HINT.search(x)
            for x in nonempty)
        col = {
            "column": names[i], "index": i,
            "rows_numeric": total, "rows_empty": len(cells) - len(vals),
            "unambiguous": numeric,
            "ambiguous_total": len(ambiguous_rows),
            "ambiguous_resolved": len(resolved),
            "ambiguous_refused": len(unresolved),
            "style_convention": convention,
            "style_evidence": {k: v for k, v in style_counter.items()
                               if v},
            "looks_like_money": money_like,
            "not_numbers": plain_rows[:5],
            "resolved": resolved[:20],
            "refused": unresolved[:20],
            "samples": sample,
        }
        if resolved or unresolved:
            # the 1000× trap made visible: gap between the two readings
            worst = max(
                [abs(Decimal(r["readings"]["group"]) -
                     Decimal(r["readings"]["decimal"])) /
                 max(abs(Decimal(r["readings"]["decimal"])), Decimal("1e-9"))
                 for r in (resolved + unresolved)
                 if "group" in r["readings"] and
                 r["readings"].get("decimal")] or [0])
            col["max_reading_gap_x"] = float(round(worst, 2))
        out_cols.append(col)
    if not out_cols:
        raise MoneyError("no numeric column found — nothing to audit")
    total_amb = sum(c["ambiguous_total"] for c in out_cols)
    total_ref = sum(c["ambiguous_refused"] for c in out_cols)
    return {"columns": out_cols, "delimiter": delim,
            "header_detected": not isinstance(header, list),
            "shape_note": shape_note,
            "summary": {
                "numeric_columns": len(out_cols),
                "ambiguous_values": total_amb,
                "resolved_by_convention": sum(
                    c["ambiguous_resolved"] for c in out_cols),
                "refused_not_guessed": total_ref,
                "verdict": "clean" if total_ref == 0 else
                           "needs_human: %d value(s) refused rather than "
                           "guessed" % total_ref}}
