# Bankr x402 Cloud deployment (marketplace distribution)

The public marketplace (bankr.bot/x402/discover) lists only **Bankr-hosted**
endpoints, so mechacut ships twice: mechacut.studio stays the independent base
(full service, PNG rendering, MCP, own x402 paywall from the first call), and
this directory ports the three transforms as TypeScript handlers for Bankr's
cloud — same contract, same prices, same error shapes.

## Prices

- chart_from_data: $0.001/req — Vega-Lite spec (PNG on mechacut.studio)
- reshape_json: $0.0005/req
- validate_json: $0.0005/req

Bankr terms: first 1,000 settled requests/month fee-free, then 5% at
settlement; earnings go straight to your Bankr wallet.

## Deploy (you have a Bankr account)

```bash
bankr login                     # if not already authenticated
mkdir mechacut-x402 && cd mechacut-x402
bankr x402 init                 # scaffold; then copy over it:
cp -r <this dir>/x402/* ./x402/
cp <this dir>/bankr.x402.json .
bankr x402 deploy
```

Deploy output gives live URLs like
`https://x402.bankr.bot/0xYourWallet/chart_from_data` — payable immediately,
not yet discoverable.

## Verify before requesting marketplace discovery

```bash
bankr x402 call https://x402.bankr.bot/0xYourWallet/validate_json \
  -i   # interactive: payload + schema
bankr x402 call https://x402.bankr.bot/0xYourWallet/chart_from_data \
  -i   # interactive: kind, x, y, data…
```

Expect: `{"valid": true}` and a `sha256` + `vega` spec respectively.
Cross-check determinism: two identical calls → identical `sha256`.

## Get listed

Marketplace discovery is enabled by Bankr per endpoint — ask via the Bankr
agent chat ("please enable marketplace discovery for my chart_from_data,
reshape_json and validate_json endpoints"). The `bankr.x402.json` here is
already filled for the card: description, category `data`, tags, full schemas.

## Chat alternative (no CLI)

The Bankr agent can deploy from chat alone. Paste each handler's TypeScript
(inline) and the config values, e.g.:
"deploy an x402 endpoint called validate_json with this handler <code>,
price 0.0005, category data, tags schema, validate, json, gate".
