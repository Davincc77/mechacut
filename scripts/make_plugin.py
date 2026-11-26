# -*- coding: utf-8 -*-
"""make_plugin — génère le dépôt marketplace Portable Agent Plugins v1.

Règle de la maison appliquée à nous-mêmes : le pack n'est jamais copié à
la main — il est RÉGÉNÉRÉ depuis les fichiers vivants du repo (SKILL-MINI,
SKILL-NETWORK). Une marketplace avec un skill périmé serait exactement le
mensonge de doc que l'audit externe vient de nous reprocher sur `step`.

Usage : python scripts/make_plugin.py [cible]   (défaut ~/Projets/mechacut-plugin)
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1
                            else "~/Projets/mechacut-plugin")

DESC_CORE = (
    "Deterministic exact math, dates, money, units and text mechanics "
    "for AI agents via mechacut.studio: free keyless curl calls, sha256 "
    "on every response, refusals that name field and expected. Teaches "
    "the multi-step calc protocol (one op per call, quote the returned "
    "value), the route directory (consult before acting) and the public "
    "proposal registry. No install, no daemon, no MCP required."
)
DESC_NETWORK = (
    "The mechacut network protocol for agents: propose a verified tool "
    "contract (POST /api/v1/agent/propose — ELIGIBLE / SUSPECT-DUPLICATE "
    "/ DUPLICATE-OF verdicts with evidence), track it in the public "
    "registry (/proposals, first external proposer credited 24-11), and "
    "run the three laws: a task done twice is a tool, consult before "
    "acting, verified tools evolve with their owner. Contract-as-unit: "
    "the protocol is the tool's birth certificate, not the transport."
)

PLUGIN = {
    "$schema": "https://agent-plugins.org/schemas/1.0.0/"
               "plugin.schema.json",
    "name": "mechacut",
    "version": "1.1.1",
    "description": (
        "Skills-only package (Agent Plugins v1): teaches agents the "
        "mechacut.studio surface — an ever-growing catalogue of "
        "deterministic transforms and named recipes, keyless free "
        "tier, x402 USDC on Base for paid routes, public proposal "
        "registry. One agent learns, all agents know. No plugin code, "
        "no MCP server bundled; every action is a plain HTTPS call "
        "the agent already can make — ordinary requests, no per-call "
        "harness prompt — and the skills state what leaves the "
        "machine."
    ),
    "author": {"name": "C.V.", "url": "https://github.com/Davincc77"},
    "homepage": "https://mechacut.studio",
    "repository": "https://github.com/mechacut/plugin",
    "license": "MIT",
    "keywords": ["determinism", "math", "dates", "money", "units",
                 "sha256", "x402", "registry", "tools", "skills-only"],
}

README = """# mechacut — Hermes plugin (Portable Agent Plugins v1)

Skills-only package: two instructions files, zero code, zero daemon.
An agent that installs this knows how to use mechacut.studio exactly —
and how to propose a tool the network's own verified way.

## What installs
- `skills/mechacut` — the operating contract (keyless curl tier,
  byte-stable outputs, sha256 per response, refusals that name the
  field and the expectation, the one-operation-at-a-time calc
  protocol for weak models).
- `skills/mechacut-network` — the network door: /api/v1/agent/propose
  (a CONTRACT is proposed, never code), the public registry at
  /proposals with named bench results, and the three laws.

## Disclosure (what the skills actually make an agent do)
- Plain HTTPS calls to https://mechacut.studio (GET /agent/manifest,
  GET /route?q=…, POST /api/v1/*). These are ordinary HTTPS requests:
  the harness does not prompt before each one — the skills state, up
  front, what text leaves the machine.
- Free tier: keyless, 30 requests/min, no account, nothing stored —
  an API key would contradict the product.
- Paid routes: x402 v1 (USDC on Base). The skill instructs the agent
  to ASK THE HUMAN before paying anything; a payment is a human
  decision, mechanically verified by the facilitator.
- 50/50 revenue split for accepted external proposals: the splitter
  factory is live on Base (0xFB209Eb982baA11Ff18CAF1ef22f29729DC3709a)
  and the first paid tool clone is registered and serving:
  /api/v1/chart pays 0x310852d642CcE4Dcb36C8027C79a5E0a2defCe64, with
  the first split payment confirmed on-chain 2026-11-26;
  monetization requires the proposer's own Base account (EIP-55
  format-verified, responsibility with the owner). Said here, in the
  SKILL-KIT, and on /PAYOUTS: built, proven — and now feeding.

## The one true counter
`curl https://mechacut.studio/agent/manifest` — version, counts,
tiers. The manifest IS the count: this README never bakes one, and
neither does any description above it. Bench corpus and replayable
pins: `GET /integrity.json` — audit us with your own numbers.

## Install / validate
```bash
hermes plugins validate .            # the catalog CI gate
hermes plugins install mechacut/plugin
```
"""

FRONT = """---\nname: {name}\ndescription: >-\n{desc}\nlicense: MIT\n---\n\n"""


def wrap(body_path, name, desc):
    with open(os.path.join(REPO, body_path), encoding="utf-8") as f:
        body = f.read().strip()
    d = "\n".join("  " + ln for ln in
                  __import__("textwrap").wrap(desc, 74))
    return FRONT.format(name=name, desc=d) + "\n" + body + "\n"


def main():
    for sub in ("skills/mechacut", "skills/mechacut-network"):
        os.makedirs(os.path.join(TARGET, sub), exist_ok=True)
    with open(os.path.join(TARGET, "plugin.json"), "w") as f:
        json.dump(PLUGIN, f, indent=2)
        f.write("\n")
    with open(os.path.join(TARGET, "skills", "mechacut",
                           "SKILL.md"), "w") as f:
        f.write(wrap("SKILL-MINI.md", "mechacut", DESC_CORE))
    with open(os.path.join(TARGET, "skills", "mechacut-network",
                           "SKILL.md"), "w") as f:
        f.write(wrap("SKILL-NETWORK.md", "mechacut-network",
                     DESC_NETWORK))
    with open(os.path.join(TARGET, "README.md"), "w") as f:
        f.write(README)
    lic = os.path.join(REPO, "LICENSE")
    if os.path.exists(lic):
        with open(lic) as s, open(os.path.join(TARGET, "LICENSE"),
                                  "w") as d:
            d.write(s.read())
    print("pack généré dans", TARGET)


if __name__ == "__main__":
    main()
