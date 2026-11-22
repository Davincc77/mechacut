# mechacut.studio — Cloudflare deployment

Mirrors the moovicast.studio setup.

## 1. Cloudflare zone

1. Cloudflare dashboard -> Add a domain -> `mechacut.studio` (Free plan).
2. Cloudflare shows two nameservers (e.g. `ada.ns.cloudflare.com`, `bob.ns.cloudflare.com`).
3. Porkbun -> mechacut.studio -> Nameservers -> switch to the two Cloudflare nameservers.
4. Cloudflare DNS records for the zone:
   - `A`  `@`   -> server IP   **Proxied (orange cloud)**
   - `A`  `www` -> server IP   **Proxied**
5. SSL/TLS -> mode **Full (strict)**.

## 2. Origin certificate (Cloudflare -> origin leg)

1. Cloudflare -> SSL/TLS -> Origin Server -> Create Certificate.
2. Hostnames: `mechacut.studio`, `*.mechacut.studio`. Validity: 15 years.
3. Save both PEM files on the server:

```bash
install -o caddy -g caddy -m 600 mechacut.studio.pem  /etc/caddy/certs/mechacut.studio.pem
install -o caddy -g caddy -m 600 mechacut.studio.key  /etc/caddy/certs/mechacut.studio.key
```

## 3. App + proxy on the server

```bash
tar xzf mechacut-0.2.0.tar.gz -C /opt
sudo bash /opt/mechacut/deploy/deploy.sh
# append deploy/Caddyfile.mechacut's site block to your Caddyfile,
# add the trusted_proxies global block (see comments in Caddyfile.mechacut),
sudo systemctl reload caddy
```

## 4. Verify

```bash
curl https://mechacut.studio/                 # "service": "mechacut"
curl https://mechacut.studio/openapi.json     # public contract
curl -X POST https://mechacut.studio/api/v1/validate \
  -H 'content-type: application/json' \
  -d '{"payload":{"ok":true},"schema":{"type":"object"}}'
```
