"""vm_probe — exécute un programme JS (expression async) dans node:vm avec
des bindings asynchrones exposés en `codemode.<fn>`. Retour (result, err).
node:vm = cloison de spike, pas une frontière de sécurité (cf spike 002)."""
import subprocess, json, os, tempfile

RUNNER = """
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
"""

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER_PATH = os.path.join(HERE, "runner.mjs")
with open(RUNNER_PATH, "w") as f:
    f.write(RUNNER)

ROUTES = {"extract_facts": "extract/facts",
          "list_dedupe": "list/dedupe",
          "sort_natural": "sort/natural"}


def run_vm(program, fns, extra_globals=None):
    spec = {
        "base": "https://mechacut.studio",
        "routes": ROUTES,
        "fnNames": list(ROUTES.keys()),
        "program": program,
        "NOTE": (extra_globals or {}).get("NOTE", ""),
    }
    p = subprocess.run(["node", RUNNER_PATH, json.dumps(spec), "{}"],
                       capture_output=True, text=True, timeout=60)
    out = p.stdout
    if "VMOK" not in out:
        return None, "runner failed: " + (p.stderr or out)[:200]
    d = json.loads(out[out.index("VMOK") + 4:])
    if d.get("error"):
        return None, d["error"]
    return d["result"], None
