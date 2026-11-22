// spike 001 — does @cloudflare/codemode run a sandboxed tool-chain LOCALLY,
// with a plain Node runtime, no Cloudflare account?
// Demo mirrors the mechacut profile: tools take/return JSON, typed by JSON schema.
import { createCodemodeRuntime } from "@cloudflare/codemode";

const tools = {
  fetch_records: {
    description: "Return incident log rows (stub for an HTTP fetch).",
    parameters: {
      type: "object",
      properties: { n: { type: "number", description: "how many rows" } },
      required: ["n"],
    },
    execute: async ({ n }) =>
      Array.from({ length: n }, (_, i) => ({
        id: i + 1,
        amount_usd: 100 + i * 37.5,
        status: i % 3 === 0 ? "failed" : "ok",
      })),
  },
  filter_rows: {
    description: "Keep rows where field equals value.",
    parameters: {
      type: "object",
      properties: {
        rows: { type: "array", items: { type: "object" } },
        field: { type: "string" },
        value: { type: "string" },
      },
      required: ["rows", "field", "value"],
    },
    execute: async ({ rows, field, value }) =>
      rows.filter((r) => r[field] === value),
  },
  sum_field: {
    description: "Sum a numeric field across rows.",
    parameters: {
      type: "object",
      properties: {
        rows: { type: "array", items: { type: "object" } },
        field: { type: "string" },
      },
      required: ["rows", "field"],
    },
    execute: async ({ rows, field }) =>
      rows.reduce((a, r) => a + Number(r[field] || 0), 0),
  },
};

const runtime = await createCodemodeRuntime({ tools });

// what an agent would write in ONE shot instead of 3 round-trips:
const code = `
const rows = await codemode.fetch_records({ n: 12 });
const failed = await codemode.filter_rows({ rows, field: "status", value: "failed" });
const total = await codemode.sum_field({ rows: failed, field: "amount_usd" });
const amounts = failed.map(r => r.amount_usd);
return { failed_count: failed.length, total_failed_usd: total, amounts };
`;

const result = await runtime.execute(code);
console.log("RESULTAT:", JSON.stringify(result));

// security probe: sandbox must NOT reach the outside world / process
const evil = `
let leaked = "NO";
try { leaked = String(typeof process !== "undefined"); } catch (e) {}
return { process_visible: leaked };
`;
try {
  const r2 = await runtime.execute(evil);
  console.log("SANDBOX:", JSON.stringify(r2));
} catch (e) {
  console.log("SANDBOX blocqué:", String(e).slice(0, 80));
}
console.log("TOOLS exposés:", Object.keys(tools).length,
  "| appel réseau pour la chaîne complète:", 1);
