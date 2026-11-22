
import vm from "node:vm";
const spec = JSON.parse(process.argv[2]);
const fns = {};
const handlers = JSON.parse(process.argv[3]); // {name: {path, args-key ignored}}
for (const name of spec.fnNames) {
  fns[name] = async (args) => {
    const r = await fetch(spec.base + "/api/v1/" + spec.routes[name], {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(args) });
    if (!r.ok) throw new Error(spec.routes[name] + " → HTTP " + r.status);
    return r.json();
  };
}
const sandbox = vm.createContext({ codemode: fns, NOTE: spec.NOTE,
  console: { log: () => {} } });
try {
  const p = new vm.Script("(" + spec.program + ")()").runInContext(sandbox);
  const result = await Promise.race([p,
    new Promise((_, rej) => setTimeout(() => rej(new Error("timeout 25s")), 25000))]);
  process.stdout.write("VMOK" + JSON.stringify({ result }));
} catch (e) {
  process.stdout.write("VMOK" + JSON.stringify({ error: String(e && e.message || e) }));
}
