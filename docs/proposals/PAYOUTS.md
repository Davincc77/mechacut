# Pay-outs — the 50/50 path (contract, proof, deployment)

State, said plainly: the contracts are WRITTEN, COMPILED,
PROVEN on a local EVM and — since 2026-11-24 — THE FACTORY IS LIVE ON
BASE: 0xFB209Eb982baA11Ff18CAF1ef22f29729DC3709a (tx
5786c8c543f37cb57969a25dbb71047063cfb0bd0b47d7eb1491956e249143d8).
Verified by direct calls, not by memory: token = Circle USDC
0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913, treasury = the core account,
payoutBps = 5000, predicted("money_tip") answers.
What is NOT done: no per-tool clone is registered yet — ensure() waits
for accepted proposals that carry a base_account, so today x402
challenges keep paying the single env address (MECHACUT_PAY_TO) and the
SKILL-KIT says exactly that. Nothing here promises
money that moves today.

## The mechanics (contract-level, contracts/splitter.sol)
- **One splitter per paid tool** — x402 settles USDC (EIP-3009) to the
  `payTo` of the challenge; the server answers `payTo` = the tool's
  splitter when `docs/proposals/splitters.json` registers one with a
  valid EIP-55 address, and falls back to the env address otherwise.
  Malformed file entries are ignored by name (`payments.splitter_note`).
- **No admin**: the clone is born with (token, treasury, payout, bps),
  all `immutable`, no owner, no withdraw, no upgrade. `flush()` is
  permissionless: whoever calls it moves payout floor(balance × bps /
  10000) to the proposer and the remainder to treasury. Funds can only
  ever go where the clone was born pointing.
- **Terms are bound to the salt**: the CREATE2 salt hashes
  (tool, payout, treasury, token, bps). `ensure("money_tip", payout)`
  with ANOTHER payout than the one the key was born with reverts
  "term mismatch with registry" — front-running a tool name with your
  own wallet is impossible by construction. `predicted()` gives the
  address before deployment, so git can pin the truth first.
- **No ETH**: the contract has no receive/fallback. ETH cannot enter,
  so nothing can be stuck or lost there.
- **50/50 is a factory constant** (`payoutBps = 5000`), the number the
  human decided on 23-11; it is not a per-call option.

## The responsibility line (the human's rule, in code)
The proposer's Base account (`base_account` at /api/v1/agent/propose)
is verified for FORMAT only — EIP-55 checksum. We do not custody, do
not check solvency, and take **no responsibility for a well-formed but
wrong address**: the split follows the bytes the proposer gave, as they
gave them. This is written in the propose response itself
(`accountability`), in SKILL-KIT.md, and enforced by the clone's
immutability.

## Deployment procedure (human, ~10 minutes, Base mainnet)
1. In YOUR terminal (never in chat): set the public treasury and run
   the deploy — the key of the gas-paying account is asked by the
   script with a MASKED PROMPT (getpass): never in shell history,
   never printed, never stored. The gas account may be a burner with
   ~$5 of ETH on Base; the contracts have NO owner, so that account
   controls nothing after paying gas.
   `export TREASURY_ADDRESS="0x…your-main-wallet" RPC_URL=https://mainnet.base.org`
2. USDC on Base is fixed: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`.
   Treasury = your payout address for the core's half.
3. `python scripts/deploy_splitter.py factory` — deploys
   SplitterFactory(token, treasury, 5000), prints its address.
4. For each paid tool with an accepted proposal whose blob carries
   `base_account`: `python scripts/deploy_splitter.py ensure <tool> <payout>`
   — or the anyone-can-calls path: the server-side design assumes YOU
   commit `docs/proposals/splitters.json` with the predicted address
   BEFORE the clone is on chain; ensure() is safe to call by anyone
   because the salt binds the terms.
5. Commit factory + per-tool addresses to `splitters.json` (path keys),
   redeploy the API, set `MECHACUT_PAY_TO` unchanged (fallback).
6. Verify a real $0.0005 call pays the clone, then `flush()` and check
   both halves — the bench does this as an e2e once live.

`scripts/deploy_splitter.py` refuses to run without the env key,
prints the address it will use, and NEVER writes the key anywhere.
