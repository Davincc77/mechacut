// spike 002 v2 — suit le contrat officiel du README Cloudflare :
// le code du modèle est une EXPRESSION async ; l'executor reçoit (code, fns).
import vm from "node:vm";
import { t as runCode } from
  "../001-codemode-local/node_modules/@cloudflare/codemode/dist/run-code-Q3Jh6Dcu.js";

const BASE = "https://mechacut.studio";
async function call(pathSeg, args) {
  const r = await fetch(`${BASE}/api/v1/${pathSeg}`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify(args) });
  if (!r.ok) throw new Error(`${pathSeg} → HTTP ${r.status}: ${(await r.text()).slice(0,160)}`);
  return r.json();
}
const fns = {
  list_dedupe:  (a) => call("list/dedupe", a),
  hash_digest:  (a) => call("hash/digest", a),
  sort_natural: (a) => call("sort/natural", a),
};

const VmExecutor = {
  async execute(code, providersOrFns) {
    // accepte les deux formes du contrat
    let codemode = {};
    if (Array.isArray(providersOrFns))
      for (const p of providersOrFns) Object.assign(codemode, p.fns || {});
    else codemode = providersOrFns || {};
    const logs = [];
    const sandbox = vm.createContext({
      codemode,
      console: { log: (...a) => logs.push(a.map(String).join(" ")) },
    });
    try {
      // contrat : code normalisé = une expression fléchée → on l'appelle directement.
      // (le wrapper async externe renvoyait undefined dans le vm ; appel nu = OK)
      const fn = new vm.Script(`(${code})()`).runInContext(sandbox);
      const result = await Promise.race([
        fn, new Promise((_, rej) => setTimeout(() => rej(new Error("timeout 20s")), 20000))]);
      return { result, logs };
    } catch (e) {
      return { result: undefined, error: String(e && e.message || e), logs };
    }
  },
};

const modelProgram = `async () => {
  const dirty = ["b.tex","a.tex","b.tex","c-10","c-2","a.tex","d.tex"];
  const ded = await codemode.list_dedupe({ items: dirty, mode: "exact" });
  const items = ded.output;
  const hashes = [];
  for (const it of items) {
    const h = await codemode.hash_digest({ data: it, algo: "sha256" });
    hashes.push(it + " → " + h.hex.slice(0, 12));
  }
  const sorted = await codemode.sort_natural({ items });
  return { input: dirty.length, deduped: items.length,
           natural: sorted.sorted, first_hashes: hashes.slice(0, 3) };
}`;

const out = await runCode({ code: modelProgram, executor: VmExecutor, providers: fns });
console.log("BRUT:", JSON.stringify(out).slice(0, 400));

const evil = `async () => ({ process: typeof process, require: typeof require })`;
const e2 = await runCode({ code: evil, executor: VmExecutor, providers: {} });
console.log("SANDBOX:", JSON.stringify(e2));
