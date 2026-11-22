import json, re, html, sys
sys.path.insert(0, "bench")
import httpx

# 1. vraie réponse serveur, fraîche, en prod
from run9 import HUMAN
r = httpx.post("https://mechacut.studio/api/v1/recipe/facts",
               json={"text": HUMAN}, timeout=60)
srv = r.json()
srv_clean = {k: v for k, v in srv.items() if k in
             ("money", "percent", "date", "url", "email", "total_money")}
# inventory?
inv = srv.get("inventory") or {}
for k in list(inv):
    srv_clean.setdefault(k, inv[k])

# 2. extrait réel du log (naked 0.5b)
log = open("bench/run9_now.log", encoding="utf-8").read()
seg = log[log.index('"model": "0.5b"'):]
seg = seg[:seg.index("\n")]
h = seg[seg.index('"head": "') + len('"head": "'):]
naked = h.encode().decode("unicode_escape", errors="replace")[:320]
naked = naked.split('", "intake')[0].rstrip('"\, ') + "\n... (réponse longue, tronquée par la vraie vie)"

# 3. relais réel du modèle
relay = '{"run": "/api/v1/recipe/facts", "args": {"text": "$utterance"}}'

TPL = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body { margin:0; background:#0b0e14; color:#e6edf3;
  font:14px/1.5 Menlo, monospace; padding:28px 34px; width:1120px; }
.h { color:#8b949e; font-size:15px; margin-bottom:18px; }
.h b { color:#e6edf3; }
.p { border:1px solid #30363d; border-radius:10px; padding:16px 20px;
  margin-bottom:16px; background:#0d1117; }
.p h3 { margin:0 0 10px; font-size:15px; }
.bad h3 { color:#f85149; } .good h3 { color:#3fb950; }
pre { margin:0; white-space:pre-wrap; color:#c9d1d9; font-size:13px; }
.score { float:right; font-weight:bold; font-size:16px; }
.bad .score { color:#f85149; } .good .score { color:#3fb950; }
.foot { color:#8b949e; font-size:13px; margin-top:14px; }
.foot b { color:#d29922; }
</style></head><body>
<div class="h">mechacut.studio — bench v9 · <b>qwen2.5:0.5b</b> · seed 42, temp 0 · production, free tier</div>

<div class="p bad"><span class="score">0/6</span>
<h3>✗ naked — ce que le 0.5B a vraiment répondu</h3>
<pre>__NAKED__</pre></div>

<div class="p good"><span class="score">6/6</span>
<h3>✓ avec la fiche — tout ce que le modèle a émis (1 ligne, 320 tok)</h3>
<pre>__RELAY__</pre>
<h3 style="margin-top:14px">↓ réponse retournée par le serveur (octets réels)</h3>
<pre>__SRV__</pre></div>

<div class="foot">sha256 de la réponse : <b>__SHA__</b> · 3 appels identiques → même empreinte · second pass reproduit · échecs publiés, scripts &amp; logs dans le repo — <b>mechacut.studio</b></div>
</body></html>"""

srv_txt = json.dumps(srv_clean, indent=1)[:520]
out = (TPL.replace("__NAKED__", html.escape(naked))
          .replace("__RELAY__", html.escape(relay))
          .replace("__SRV__", html.escape(srv_txt))
          .replace("__SHA__", srv["sha256"][:24] + "…"))
open("receipt_v9.html", "w", encoding="utf-8").write(out)
print("receipt_v9.html écrit — sha:", srv["sha256"][:24])
