// MechaCut reshape_json — deterministic JSON reshaping with an optional
// JSON Schema output gate. TypeScript port of mechacut.studio /api/v1/reshape.
// Same request -> same sha256. No LLM, no storage.

import Ajv2020 from "ajv/dist/2020.js";

class Missing extends Error {}

function parsePath(path: string): (string | number)[] {
  const p = path.startsWith("$.") ? path.slice(2) : path;
  const toks: (string | number)[] = [];
  const re = /\[(\d+)\]|([^.\[\]]+)/y;
  let i = 0;
  while (i < p.length) {
    re.lastIndex = i;
    const m = re.exec(p);
    if (!m) throw new Missing("invalid path syntax: " + JSON.stringify(path));
    toks.push(m[1] !== undefined ? parseInt(m[1], 10) : m[2]);
    i = re.lastIndex;
    if (i < p.length) {
      if (p[i] !== ".") throw new Missing("invalid path syntax: " + JSON.stringify(path));
      i += 1;
      if (i === p.length) throw new Missing("trailing dot in path: " + JSON.stringify(path));
    }
  }
  if (toks.length === 0) throw new Missing("invalid path: " + JSON.stringify(path));
  return toks;
}

function resolve(root: unknown, toks: (string | number)[]): unknown {
  let cur = root;
  for (const t of toks) {
    if (typeof t === "number") {
      if (!Array.isArray(cur) || t < -cur.length || t >= cur.length)
        throw new Missing("index " + t + " out of range");
      cur = cur[t];
    } else {
      if (cur === null || typeof cur !== "object" || !(t in (cur as object)))
        throw new Missing("key not found: " + t);
      cur = (cur as Record<string, unknown>)[t];
    }
  }
  return cur;
}

function castVal(v: unknown, cast: string): unknown {
  if (cast === "int") {
    const s = String(v).trim();
    const n = Number(s);
    if (!Number.isFinite(n)) throw new Error("cannot cast to int: " + JSON.stringify(v));
    return /^-?\d+$/.test(s) ? parseInt(s, 10) : Math.trunc(n);
  }
  if (cast === "float") {
    const n = Number(String(v).trim());
    if (!Number.isFinite(n)) throw new Error("cannot cast to float: " + JSON.stringify(v));
    return n;
  }
  if (cast === "str") {
    if (typeof v === "string") return v;
    if (typeof v === "object" && v !== null) return JSON.stringify(v);
    return String(v);
  }
  if (cast === "bool") {
    if (typeof v === "boolean") return v;
    const s = String(v).trim().toLowerCase();
    if (["true", "1", "yes", "y"].includes(s)) return true;
    if (["false", "0", "no", "n"].includes(s)) return false;
    throw new Error("not a bool: " + JSON.stringify(v));
  }
  if (cast === "upper") return String(v).toUpperCase();
  if (cast === "lower") return String(v).toLowerCase();
  if (cast === "strip") return String(v).trim();
  throw new Error("unknown cast: " + cast);
}

type Err = { field?: string; path?: string; message: string };
type Res = { out: Record<string, unknown>; errors: Err[]; defaults: { field: string; path: string }[] };

function apply(cur: unknown, fields: Record<string, unknown>, prefix: string): Res {
  const out: Record<string, unknown> = {};
  const errors: Err[] = [];
  const defaults: { field: string; path: string }[] = [];
  for (const [key, rawSpec] of Object.entries(fields)) {
    const fname = prefix + key;
    if (rawSpec === null || typeof rawSpec !== "object") {
      errors.push({ field: fname, message: "field spec must be an object" });
      continue;
    }
    const spec = rawSpec as Record<string, unknown>;
    if ("const" in spec) { out[key] = spec.const; continue; }
    const path = spec.path as string | undefined;
    if (!path) { errors.push({ field: fname, message: "field spec needs path or const" }); continue; }
    let toks: (string | number)[];
    try {
      toks = parsePath(path);
    } catch (e) {
      errors.push({ field: fname, path, message: (e as Error).message });
      continue;
    }
    let val: unknown;
    try {
      val = resolve(cur, toks);
    } catch (e) {
      if ("default" in spec) {
        out[key] = spec.default;
        defaults.push({ field: fname, path });
      } else if (spec.required !== false) {
        errors.push({ field: fname, path, message: "missing" });
      }
      continue;
    }
    if ("each" in spec) {
      if (!Array.isArray(val)) { errors.push({ field: fname, path, message: "each requires an array" }); continue; }
      const sub = spec.each as Record<string, unknown> | null;
      if (sub === null || typeof sub !== "object" || !sub.fields ||
          typeof sub.fields !== "object") {
        errors.push({ field: fname, message: "each must be a mapping with fields" });
        continue;
      }
      const items: unknown[] = [];
      val.forEach((item, i) => {
        const r = apply(item, sub.fields as Record<string, unknown>, fname + "[" + i + "].");
        errors.push(...r.errors);
        defaults.push(...r.defaults);
        items.push(r.out);
      });
      out[key] = items;
      continue;
    }
    if (spec.cast) {
      try {
        val = castVal(val, spec.cast as string);
      } catch (e) {
        errors.push({ field: fname, path, message: (e as Error).message });
        continue;
      }
    }
    out[key] = val;
  }
  return { out, errors, defaults };
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
    return Response.json({ error: "invalid_input", errors: [{ message: "body must be JSON" }] }, { status: 400 });
  }
  const input = body.input;
  const mapping = body.mapping as Record<string, unknown> | undefined;
  const outputSchema = body.outputSchema as Record<string, unknown> | undefined;

  if (!mapping || typeof mapping !== "object" || !mapping.fields ||
      typeof mapping.fields !== "object" || Array.isArray(mapping.fields)) {
    return Response.json(
      { error: "invalid_input", errors: [{ field: "$", message: "mapping must have a fields object" }] },
      { status: 400 });
  }

  const { out, errors, defaults } = apply(input, mapping.fields as Record<string, unknown>, "");
  if (errors.length)
    return Response.json({ error: "invalid_input", errors }, { status: 400 });

  if (outputSchema) {
    let ajv: Ajv2020;
    try {
      ajv = new Ajv2020({ allErrors: true });
    } catch (e) {
      return Response.json(
        { error: "schema_violation", errors: [{ field: "$schema", message: "invalid schema: " + (e as Error).message }], output: out },
        { status: 400 });
    }
    const valid = ajv.validate(outputSchema, out);
    if (!valid) {
      const schemaErrors = (ajv.errors ?? []).map((e: { instancePath: string; message?: string }) =>
        ({ field: e.instancePath || "/", message: e.message ?? "invalid" }));
      return Response.json({ error: "schema_violation", errors: schemaErrors, output: out }, { status: 400 });
    }
  }

  return Response.json({ output: out, sha256: await sha256(out), defaults_used: defaults });
}
