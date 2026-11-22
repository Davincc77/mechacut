"""Deterministic chart engine: records/CSV in, Vega-Lite spec + PNG out.

Pure functions. No LLM, no network, no storage. Same request -> same bytes.

Design choices (documented in README):
- MechaCut never reorders your data. Bars/pies aggregate (sum) per
  category in first-appearance order; lines/points keep input order.
- Numeric strings are coerced; a column is quantitative only if every
  value parses as a number.
- The PNG palette is fixed; series colors are assigned by sorted name.
"""

import csv
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PALETTE = ["#4269d3", "#efb118", "#ff725c", "#6cc5b0", "#3ca951",
           "#ff8ab7", "#a463f2", "#97bbf5", "#b27b42", "#25aae2"]
KINDS = {"bar", "line", "area", "point", "step", "histogram", "pie"}


class ChartError(Exception):
    pass


def num(v):
    """Return float(v) if v is a number or numeric string, else None."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def coerce(v):
    """CSV arrives as strings; coerce numeric-looking ones to int/float."""
    if isinstance(v, bool) or not isinstance(v, str):
        return v
    s = v.strip()
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def parse_records(data=None, csv_text=None):
    if data is not None:
        if not isinstance(data, list) or not data:
            raise ChartError("data must be a non-empty list of records")
        if not all(isinstance(r, dict) for r in data):
            raise ChartError("data rows must be objects")
        return [dict(r) for r in data]
    if csv_text:
        try:
            rows = list(csv.DictReader(io.StringIO(csv_text)))
        except csv.Error as e:
            raise ChartError(f"csv parse error: {e}")
        if not rows:
            raise ChartError("csv produced no rows (missing header?)")
        return rows
    raise ChartError("send data (list of records) or csv")


def _values(rows, kind, x, y, series):
    cols = [x]
    if kind != "histogram":
        cols.append(y)
    if series:
        cols.append(series)
    for c in cols:
        if c not in rows[0]:
            raise ChartError(f"column not found: {c}")
    out = []
    for r in rows:
        rec = {x: coerce(r.get(x))}
        if kind != "histogram":
            rec[y] = coerce(r.get(y))
        if series:
            rec[series] = coerce(r.get(series))
        out.append(rec)
    if kind == "histogram":
        for rec in out:
            if num(rec[x]) is None:
                raise ChartError(f"histogram x must be fully numeric; got {rec[x]!r}")
    return out


def _x_type(values, x):
    return "quantitative" if all(num(r[x]) is not None for r in values) else "nominal"


def _sk(v):
    """Deterministic sort key: numbers before strings."""
    n = num(v)
    return (0, n, "") if n is not None else (1, 0.0, str(v))


def _agg_sum(values, x, y, series):
    """Sum y per (x, series), preserving first-appearance order."""
    agg = {}
    for r in values:
        key = (r[x], r[series]) if series else (r[x],)
        agg[key] = agg.get(key, 0) + (num(r.get(y)) or 0.0)
    return agg


def _appearance(values, x):
    seen = []
    for r in values:
        if r[x] not in seen:
            seen.append(r[x])
    return seen


def build(kind, rows, x, y, series=None, title=None, width=640, height=400):
    """Full pipeline: rows -> (vega spec, png bytes). Raises ChartError."""
    if series and kind in ("pie", "histogram"):
        raise ChartError(f"series is not supported for kind {kind}")
    values = _values(rows, kind, x, y, series)
    vega = _build_vega(kind, values, x, y, series=series, title=title,
                       width=width, height=height)
    png = _render_png(kind, values, x, y, series=series, title=title,
                      width=width, height=height)
    return vega, png


def _build_vega(kind, values, x, y, series=None, title=None, width=640, height=400):
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "width": width,
        "height": height,
    }
    if title:
        spec["title"] = title
    spec["data"] = {"values": values}
    if kind == "histogram":
        spec["mark"] = "bar"
        spec["encoding"] = {
            "x": {"bin": True, "field": x, "type": "quantitative"},
            "y": {"aggregate": "count", "type": "quantitative"},
        }
        return spec
    if kind == "pie":
        spec["mark"] = "arc"
        spec["encoding"] = {
            "theta": {"field": y, "aggregate": "sum", "type": "quantitative"},
            "color": {"field": x, "type": "nominal", "sort": None},
        }
        return spec
    if kind == "step":
        mark = {"type": "line", "interpolate": "step-after"}
    else:
        mark = {"bar": "bar", "line": "line", "area": "area",
                "point": "point"}[kind]
    xt = _x_type(values, x)
    x_enc = {"field": x, "type": xt}
    if xt == "nominal":
        x_enc["sort"] = None  # keep the order the data arrived in
    y_enc = {"field": y, "type": "quantitative"}
    if kind == "bar":
        y_enc["aggregate"] = "sum"
    encoding = {"x": x_enc, "y": y_enc}
    if series:
        encoding["color"] = {"field": series, "type": "nominal",
                             "sort": None, "scale": {"scheme": "tableau10"}}
    spec["mark"] = mark
    try:
        nx = len({str(r.get(x)) for r in values})
        if nx > 12:
            encoding["x"].setdefault("axis", {})["labelAngle"] = -45
    except Exception:
        pass
    spec["encoding"] = encoding
    return spec


def _readable_x(ax, labels):
    """Anti-collision, server-side, versioned: above 12 categories, thin the
    ticks to <= 12 and rotate. A weak model must never guess 'labelAngle' —
    the same request still gives the same bytes, across every model."""
    n = len(labels)
    if n > 12:
        step = -(-n // 12)                      # ceil
        idx = list(range(0, n, step))
        ax.set_xticks(idx)
        ax.set_xticklabels([labels[i] for i in idx], rotation=45,
                           ha="right", fontsize=8)


def _compact_y(ax):
    """Tiny or huge magnitudes become 2.0e-04 / 1.2e+06, never
    0.000198000 — six-label clutter steals the plot width."""
    try:
        lo, hi = ax.get_ylim()
    except Exception:
        return
    top = max(abs(lo), abs(hi))
    if 0 < top < 0.01 or top >= 1e6:
        from matplotlib.ticker import FuncFormatter
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "%.1e" % v))


def _render_png(kind, values, x, y, series=None, title=None, width=640, height=400):
    fig, ax = plt.subplots(figsize=(width / 100.0, height / 100.0), dpi=100)
    try:
        ax.grid(True, color="#e8e8e8", linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        if title:
            ax.set_title(title, fontsize=12, color="#333333")
        if kind == "pie":
            agg = _agg_sum(values, x, y, series=None)
            items = [(k[0], v) for k, v in agg.items()]
            ax.pie([v for _, v in items],
                   labels=[str(k) for k, _ in items],
                   colors=[PALETTE[i % len(PALETTE)] for i in range(len(items))],
                   startangle=90, counterclock=False,
                   wedgeprops={"edgecolor": "white", "linewidth": 1})
            ax.set_aspect("equal")
        elif kind == "histogram":
            vals = [num(r[x]) for r in values]
            ax.hist(vals, bins=10, color=PALETTE[0], edgecolor="white", linewidth=0.5)
            ax.set_xlabel(x)
            ax.set_ylabel("count")
        elif kind == "bar":
            xorder = _appearance(values, x)
            agg = _agg_sum(values, x, y, series)
            if series:
                svals = sorted({k[1] for k in agg}, key=_sk)
                bw = 0.8 / len(svals)
                for si, sv in enumerate(svals):
                    hs = [agg.get((xv, sv), 0.0) for xv in xorder]
                    pos = [i - 0.4 + bw * (si + 0.5) for i in range(len(xorder))]
                    ax.bar(pos, hs, width=bw,
                           color=PALETTE[si % len(PALETTE)], label=str(sv))
                ax.legend(frameon=False, fontsize=9)
            else:
                hs = [agg.get((xv,), 0.0) for xv in xorder]
                ax.bar(range(len(xorder)), hs, color=PALETTE[0], width=0.6)
            labels = [str(v) for v in xorder]
            if len(labels) > 12:
                _readable_x(ax, labels)
            else:
                ax.set_xticks(range(len(xorder)))
                ax.set_xticklabels(labels)
            ax.set_xlabel(x)
            ax.set_ylabel(y)
            _compact_y(ax)
        else:  # line, step, area, point
            groups = {}
            for r in values:
                key = str(r[series]) if series else ""
                groups.setdefault(key, []).append(r)
            xt = _x_type(values, x)
            if xt == "nominal":
                xorder = _appearance(values, x)
                pos_of = {v: i for i, v in enumerate(xorder)}
            for gi, key in enumerate(sorted(groups, key=_sk)):
                rs = groups[key]
                if xt == "nominal":
                    pos = [pos_of[r[x]] for r in rs]
                else:
                    pos = [num(r[x]) for r in rs]
                ys = [num(r.get(y)) or 0.0 for r in rs]
                color = PALETTE[gi % len(PALETTE)]
                if kind in ("line", "step"):
                    ax.plot(pos, ys, color=color, linewidth=2,
                            drawstyle="steps-post" if kind == "step" else "default",
                            label=key if series else None)
                elif kind == "area":
                    ax.fill_between(pos, ys, color=color, alpha=0.35,
                                    label=key if series else None)
                else:  # point
                    ax.scatter(pos, ys, color=color, s=30,
                               label=key if series else None)
                if xt == "nominal":
                    labels = [str(v) for v in xorder]
                    if len(labels) > 12:
                        _readable_x(ax, labels)
                    else:
                        ax.set_xticks(range(len(xorder)))
                        ax.set_xticklabels(labels)
            if series:
                ax.legend(frameon=False, fontsize=9)
            ax.set_xlabel(x)
            ax.set_ylabel(y)
            if kind != "pie":
                _compact_y(ax)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor="white",
                    metadata={"Software": None})
        return buf.getvalue()
    finally:
        plt.close(fig)
