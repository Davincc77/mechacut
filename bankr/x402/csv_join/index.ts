// MechaCut csv_join — deterministic two-table join, left wins on overlap.
// Faithful TypeScript port of mechacut.studio /api/v1/csv/join.
// Same request -> same sha256, same row order. No pandas, no surprises.
//
// Error shape follows the MechaCut family contract:
//   400 {"error": "invalid_input", "errors": [{field, message}]}

function badRequest(errors: { field?: string; message: string }[]): Response {
  return Response.json({ error: "invalid_input", errors }, { status: 400 });
}

// canonical key: JSON with sorted object keys, compact separators —
// mirrors Python json.dumps(sort_keys=True, separators=(",", ":"))
function canon(v: unknown): string {
  if (Array.isArray(v)) return "[" + v.map(canon).join(",") + "]";
  if (v !== null && typeof v === "object") {
    const o = v as Record<string, unknown>;
    return "{" + Object.keys(o).sort()
      .map(k => JSON.stringify(k) + ":" + canon(o[k])).join(",") + "}";
  }
  return JSON.stringify(v) ?? "null";
}

async function sha256(v: unknown): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(canon(v)));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
}

function isRows(v: unknown): v is Record<string, unknown>[] {
  return Array.isArray(v) && (v.length === 0 ||
    (v[0] !== null && typeof v[0] === "object" && !Array.isArray(v[0])));
}

function pair(on: unknown): [string, string] | null {
  if (typeof on === "string") return [on, on];
  if (Array.isArray(on) && on.length === 2 &&
      on.every(x => typeof x === "string")) return [on[0] as string, on[1] as string];
  if (on !== null && typeof on === "object" && !Array.isArray(on) &&
      "left" in (on as object) && "right" in (on as object)) {
    const o = on as Record<string, unknown>;
    return [String(o.left), String(o.right)];
  }
  return null;
}

function columns(rows: Record<string, unknown>[]): string[] {
  const cols: string[] = [];
  for (const r of rows) for (const k of Object.keys(r))
    if (!cols.includes(k)) cols.push(k);
  return cols;
}

export default async function handler(req: Request): Promise<Response> {
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return badRequest([{ message: "body must be JSON" }]);
  }

  const how = (body.how as string) ?? "inner";
  if (!["inner", "left", "right", "outer"].includes(how))
    return badRequest([{ field: "how", message: "how must be inner, left, right or outer" }]);

  const p = pair(body.on);
  if (!p)
    return badRequest([{ field: "on",
      message: 'on must be "col", ["lcol", "rcol"] or {"left": ..., "right": ...}' }]);
  const [lk, rk] = p;

  const left = body.left, right = body.right;
  if (!isRows(left)) return badRequest([{ field: "left", message: "left must be a list of records" }]);
  if (!isRows(right)) return badRequest([{ field: "right", message: "right must be a list of records" }]);
  if (left.length === 0 || !(lk in left[0]))
    return badRequest([{ field: lk, message: "column not found: " + lk }]);
  if (right.length === 0 || !(rk in right[0]))
    return badRequest([{ field: rk, message: "column not found: " + rk }]);

  const rightCols = columns(right);
  const leftCols = columns(left);

  const index = new Map<string, number[]>();
  right.forEach((r, i) => {
    const k = canon(r[rk]);
    const arr = index.get(k);
    if (arr) arr.push(i); else index.set(k, [i]);
  });

  const used = new Set<number>();
  const out: Record<string, unknown>[] = [];
  let matched = 0;
  for (const l of left) {
    const hits = (lk in l ? index.get(canon(l[lk])) : undefined) ?? [];
    for (const j of hits) {
      matched++;
      used.add(j);
      out.push({ ...right[j], ...l }); // left wins on overlap
    }
    if (hits.length === 0 && (how === "left" || how === "outer")) {
      const filler: Record<string, unknown> = {};
      for (const k of rightCols) filler[k] = null;
      out.push({ ...filler, ...l });
    }
  }
  if (how === "right" || how === "outer") {
    right.forEach((r, j) => {
      if (used.has(j)) return;
      const filler: Record<string, unknown> = {};
      for (const k of leftCols) filler[k] = null;
      out.push({ ...filler, ...r });
    });
  }

  const counts = {
    left_rows: left.length,
    right_rows: right.length,
    matched,
    output_rows: out.length,
  };
  return Response.json({ output: out, counts,
    sha256: await sha256(out) });
}
