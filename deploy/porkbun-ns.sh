#!/usr/bin/env bash
# porkbun-ns.sh — set/verify nameservers via the Porkbun API without exposing
# the key: reads /opt/data/secrets/porkbun.json (created by the OWNER via
# doctl harness-runtime exec, never via chat) and prints only the API response.
#
# Usage:
#   porkbun-ns.sh get   <domain>
#   porkbun-ns.sh set   <domain> <ns1> <ns2> [ns3] [ns4]
set -euo pipefail
KEYS=/opt/data/secrets/porkbun.json
if [ ! -f "$KEYS" ]; then
  echo "missing $KEYS — create it from your own machine with:"
  echo "  doctl harness-runtime exec <sandbox-id> -- sh -c 'umask 077; mkdir -p /opt/data/secrets && printf \"{\\\"apikey\\\":\\\"pk1_...\\\",\\\"secretapikey\\\":\\\"sk1_...\\\"}\" > /opt/data/secrets/porkbun.json'"
  exit 1
fi
cmd=$1; domain=$2; shift 2
body=$(python3 - "$domain" "$@" <<'PY'
import json, sys
keys = json.load(open("/opt/data/secrets/porkbun.json"))
cmd, domain, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
if cmd == "set":
    keys["ns"] = rest
print(json.dumps(keys))
PY
)
case "$cmd" in
  get) ep="domain/getNs/$domain" ;;
  set) ep="domain/updateNs/$domain" ;;
  *) echo "usage: porkbun-ns.sh get|set <domain> [ns...]" >&2; exit 1 ;;
esac
curl -s -X POST "https://api.porkbun.com/api/json/v3/$ep" \
  -H 'content-type: application/json' -d "$body" | python3 -c 'import json,sys; d=json.load(sys.stdin); d.pop("apikey",None); d.pop("secretapikey",None); print(json.dumps(d, indent=2))'
