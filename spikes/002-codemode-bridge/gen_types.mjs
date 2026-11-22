// spike 002 — génère le SDK typé Code Mode DEPUIS les vrais schémas mechacut,
// en mesurant le coût en tokens vs charger les schémas bruts.
import { t as generateTypesFromJsonSchema } from
  "../001-codemode-local/node_modules/@cloudflare/codemode/dist/json-schema-types-D_m9tVnI.js";

const BASE = "https://mechacut.studio";
const picks = ["json_repair", "hash_digest", "text_case", "sort_natural",
               "list_dedupe", "num_round", "date_parse", "id_slug"];

const tools = {};
for (const name of picks) {
  const s = await (await fetch(`${BASE}/tools/${name}.json`)).json();
  // schéma réel : { tool, path, schema: { name, description, inputSchema } }
  const schema = s.schema?.inputSchema || null;
  tools[name] = {
    description: (s.schema?.description || s.purpose || name).slice(0, 120),
    inputSchema: schema || { type: "object", properties: {}, additionalProperties: true },
  };
  console.log("·", name, "→ inputSchema?", !!schema,
    Object.keys(tools[name].inputSchema.properties || {}).slice(0, 4).join(","));
}

const sdk = await generateTypesFromJsonSchema(tools, "mechacut");
const tokens = Math.ceil(sdk.length / 4);            // approx 4 chars/token
const rawTokens = Math.ceil(JSON.stringify(tools).length / 4);
console.log("\n=== TYPED SDK (extrait) ===");
console.log(sdk.split("\n").slice(0, 26).join("\n"));
console.log("\nSDK typé       ≈", tokens, "tokens pour", picks.length, "transforms");
console.log("Schémas bruts  ≈", rawTokens, "tokens (comparaison)");
console.log("\nProjection 72 transforms SDK ≈", Math.round(tokens / picks.length * 72), "tokens");
import { writeFileSync } from "node:fs";
writeFileSync("sdk.mjs.js", sdk);
