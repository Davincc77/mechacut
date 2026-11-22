// MechaCut validate_json — validate a payload against a JSON Schema
// (draft 2020-12). Gate agent output before acting on it.
// TypeScript port of mechacut.studio /api/v1/validate.

import Ajv2020 from "ajv/dist/2020.js";

export default async function handler(req: Request): Promise<Response> {
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "invalid_input", errors: [{ message: "body must be JSON" }] }, { status: 400 });
  }
  const payload = body.payload;
  const schema = body.schema;
  if (!schema || typeof schema !== "object") {
    return Response.json(
      { error: "invalid_input", errors: [{ field: "schema", message: "schema must be a JSON Schema object" }] },
      { status: 400 });
  }
  let ajv: Ajv2020;
  try {
    ajv = new Ajv2020({ allErrors: true });
  } catch (e) {
    return Response.json(
      { error: "schema_violation", errors: [{ field: "$schema", message: "invalid schema: " + (e as Error).message }], valid: false },
      { status: 400 });
  }
  let valid: boolean;
  try {
    valid = ajv.validate(schema, payload) as boolean;
  } catch (e) {
    return Response.json(
      { error: "schema_violation", errors: [{ field: "$schema", message: "invalid schema: " + (e as Error).message }], valid: false },
      { status: 400 });
  }
  if (!valid) {
    const errors = (ajv.errors || []).map(e => ({ field: e.instancePath || "/", message: e.message }));
    return Response.json({ error: "schema_violation", errors, valid: false }, { status: 400 });
  }
  return Response.json({ valid: true });
}
