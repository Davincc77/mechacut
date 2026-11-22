// MechaCut chart_from_data — deterministic Vega-Lite chart from records.
// TypeScript port of mechacut.studio /api/v1/chart (spec output; PNG stays on
// mechacut.studio). Same request -> same sha256. Never reorders your data.
//
// Error shape follows the MechaCut family contract:
//   400 {"error": "invalid_input", "errors": [{field, message}]}

const KINDS = ["bar", "line", "area", "point", "step", "histogram", "pie"];

function badRequest(errors: { field?: string; message: string }[]): Response {
  return Response.json({ error: "invalid_input", errors }, { status: 400 });
}

function num(v: unknown): number | null {
  if (typeof v === "boolean") return null;
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  if (typeof v === "string") {
    const s = v.trim();
    if (s === "") return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function coerce(v: unknown): unknown {
  if (typeof v !== "string") return v;
  const s = v.trim();
  if (s === "") return s;
  if (/^-?\d+$/.test(s)) return parseInt(s, 10);
  const n = Number(s);
  return Number.isFinite(n) ? n : s;
}

function canon(v: unknown): string {
  if (Array.isArray(v)) return "[" + v.map(canon).join(",") + "]";
  if (v !== null && typeof v === "object") {
    const o = v as Record<string, unknown>;
    return "{" + Object.keys(o).sort()
      .map(k => JSON.stringify(k) + ":" + canon(o[k])).join(",") + "}";
  }
  return JSON.stringify(v);
}

async function sha256(v: unknown): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(canon(v)));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
}

export default async function handler(req: Request): Promise<Response> {
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return badRequest([{ message: "body must be JSON" }]);
  }
  const errors: { field?: string; message: string }[] = [];
  const kind = (body.kind as string) ?? "bar";
  const x = body.x as string;
  const y = body.y as string | undefined;
  const series = body.series as string | undefined;
  const title = body.title as string | undefined;
  const data = body.data as Record<string, unknown>[] | undefined;
  const csv = body.csv as string | undefined;
  const width = (body.width as number) ?? 640;
  const height = (body.height as number) ?? 400;

  if (!x) errors.push({ field: "x", message: "required" });
  if (!KINDS.includes(kind))
    errors.push({ field: "kind", message: "unknown kind, expected one of " + KINDS.join(", ") });
  if (kind !== "histogram" && !y)
    errors.push({ field: "y", message: "required unless kind is histogram" });
  if (!data && !csv)
    errors.push({ field: "data", message: "send data (records) or csv" });
  if (errors.length) return badRequest(errors);

  let rows: Record<string, unknown>[];
  if (data) {
    if (!Array.isArray(data) || data.length === 0)
      return badRequest([{ field: "data", message: "data must be a non-empty list of records" }]);
    rows = data;
  } else {
    // minimal CSV parse (quoted fields unsupported; see mechacut.studio for full RFC)
    const lines = (csv as string).trim().split(/\r?\n/);
    const header = lines[0].split(",").map(h => h.trim());
    rows = lines.slice(1).map(line => {
      const rec: Record<string, unknown> = {};
      line.split(",").forEach((cell, i) => { rec[header[i]] = cell.trim(); });
      return rec;
    });
    if (rows.length === 0)
      return badRequest([{ field: "csv", message: "csv produced no rows (missing header?)" }]);
  }

  if (series && (kind === "pie" || kind === "histogram"))
    return badRequest([{ field: "series", message: "series is not supported for kind " + kind }]);

  const cols = [x]; if (kind !== "histogram") cols.push(y as string);
  if (series) cols.push(series);
  for (const c of cols) {
    if (!(c in rows[0]))
      return badRequest([{ field: c, message: "column not found: " + c }]);
  }

  const values: Record<string, unknown>[] = rows.map(r => {
    const rec: Record<string, unknown> = { [x]: coerce(r[x]) };
    if (kind !== "histogram") rec[y as string] = coerce(r[y as string]);
    if (series) rec[series] = coerce(r[series]);
    return rec;
  });

  if (kind === "histogram" && values.some(r => num(r[x]) === null))
    return badRequest([{ field: "x", message: "histogram x must be fully numeric" }]);

  const spec: Record<string, unknown> = {
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    width, height,
  };
  if (title) spec.title = title;
  spec.data = { values };

  if (kind === "histogram") {
    spec.mark = "bar";
    spec.encoding = {
      x: { bin: true, field: x, type: "quantitative" },
      y: { aggregate: "count", type: "quantitative" },
    };
  } else if (kind === "pie") {
    spec.mark = "arc";
    spec.encoding = {
      theta: { field: y, aggregate: "sum", type: "quantitative" },
      color: { field: x, type: "nominal", sort: null },
    };
  } else {
    spec.mark = kind === "step" ? { type: "line", interpolate: "step-after" } : kind;
    const xt = values.every(r => num(r[x]) !== null) ? "quantitative" : "nominal";
    const xEnc: Record<string, unknown> = { field: x, type: xt };
    if (xt === "nominal") xEnc.sort = null; // keep the order the data arrived in
    const yEnc: Record<string, unknown> = { field: y, type: "quantitative" };
    if (kind === "bar") yEnc.aggregate = "sum";
    const encoding: Record<string, unknown> = { x: xEnc, y: yEnc };
    if (series)
      encoding.color = { field: series, type: "nominal", sort: null, scale: { scheme: "tableau10" } };
    spec.mark = kind === "step" ? { type: "line", interpolate: "step-after" } : kind;
    spec.encoding = encoding;
  }

  return Response.json({ sha256: await sha256(spec), vega: spec });
}
