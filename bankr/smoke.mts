// Smoke test for the Bankr TS handlers — run: node smoke.ts (Node >= 23 strips types)
import chart from "./x402/chart_from_data/index.ts";
import reshape from "./x402/reshape_json/index.ts";
import validate from "./x402/validate_json/index.ts";

const req = (body: unknown) =>
  new Request("http://x/test", { method: "POST", body: JSON.stringify(body), headers: { "content-type": "application/json" } });

// validate: good + bad
let r = await validate(req({ payload: { age: 44 }, schema: { type: "object", required: ["age"], properties: { age: { type: "integer" } } } }));
console.log("validate ok  :", r.status, await r.text());
r = await validate(req({ payload: { age: "young" }, schema: { type: "object", required: ["age"], properties: { age: { type: "integer" } } } }));
console.log("validate bad :", r.status, await r.text());

// reshape: paths, cast, default, each
r = await reshape(req({
  input: { person: { name: "Davincc", age: "44", tags: [{ t: "a", v: "1" }, { t: "b", v: "2" }] } },
  mapping: { fields: {
    name: { path: "person.name" },
    age: { path: "person.age", cast: "int" },
    nick: { path: "person.nickname", default: "anon" },
    tags: { path: "person.tags", each: { fields: { k: { path: "t" }, v: { path: "v", cast: "int" } } } },
  } },
}));
console.log("reshape      :", r.status, await r.text());

// reshape: error shape + schema gate
r = await reshape(req({ input: { a: 1 }, mapping: { fields: { x: { path: "b.c" } } } }));
console.log("reshape err  :", r.status, await r.text());
r = await reshape(req({
  input: { a: 1 },
  mapping: { fields: { age: { path: "a", cast: "int" } } },
  outputSchema: { type: "object", required: ["age", "name"] },
}));
console.log("schema gate  :", r.status, await r.text());

// chart: spec + determinism
const chartBody = { kind: "bar", x: "month", y: "revenue", data: [{ month: "Jan", revenue: 1200 }, { month: "Feb", revenue: 1810 }] };
r = await chart(req(chartBody));
const c1 = await r.json();
console.log("chart        :", r.status, "mark:", c1.vega.mark, "sha256:", c1.sha256.slice(0, 16));
r = await chart(req(chartBody));
const c2 = await r.json();
console.log("determinism  :", c1.sha256 === c2.sha256 ? "OK" : "FAIL");

// chart: histogram + pie + error
r = await chart(req({ kind: "histogram", x: "revenue", data: chartBody.data }));
console.log("histogram    :", r.status, (await r.json()).vega.encoding.x.bin);
r = await chart(req({ kind: "pie", x: "month", y: "revenue", data: chartBody.data }));
console.log("pie          :", r.status, (await r.json()).vega.mark);
r = await chart(req({ kind: "scatter", x: "a", y: "b", data: [{ a: 1, b: 2 }] }));
console.log("bad kind     :", r.status, await r.text());
