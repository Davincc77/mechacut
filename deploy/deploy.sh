#!/usr/bin/env bash
# MechaCut deploy — run on the server, inside the app dir (default /opt/mechacut).
# Assumes the code is already there (git clone or scp -r from the dev box).
#   sudo bash deploy/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."
APP="$(pwd)"
echo "Deploying MechaCut from $APP"

[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python -m pytest -q

sed "s|/opt/mechacut|$APP|g" deploy/mechacut.service > /etc/systemd/system/mechacut.service
systemctl daemon-reload
systemctl enable --now mechacut
systemctl restart mechacut
sleep 1
curl -fs http://127.0.0.1:8898/ >/dev/null && echo "MechaCut is up on 127.0.0.1:8898 — now wire the proxy."
