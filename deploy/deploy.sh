#!/bin/sh
# deploy.sh — push TradingAgents source to the VPS + reload systemd units.
#
# Usage (from the local repo root):
#   ./deploy/deploy.sh
#
# Assumes:
#   - SSH alias `vps` configured in ~/.ssh/config pointing at the Hetzner box
#   - VPS path /srv/tradingagents owned by user `rawcell`
#   - systemd units already installed under /etc/systemd/system/
#   - Caddyfile snippet already merged into /srv/agent-harness/caddy/Caddyfile
#
# Customize the constants below for your VPS layout.

set -eu

VPS_HOST="${VPS_HOST:-vps}"
VPS_PATH="${VPS_PATH:-/srv/tradingagents}"
VPS_USER="${VPS_USER:-rawcell}"

echo "==> Syncing source to ${VPS_USER}@${VPS_HOST}:${VPS_PATH}"
rsync -az --delete \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='.mypy_cache' \
    --exclude='node_modules' \
    --exclude='experiments/' \
    --exclude='claudedocs/' \
    --exclude='specs/' \
    ./ "${VPS_USER}@${VPS_HOST}:${VPS_PATH}/"

echo "==> Reloading systemd"
ssh "${VPS_USER}@${VPS_HOST}" "sudo systemctl daemon-reload"

echo "==> Restarting dashboard container (if installed)"
ssh "${VPS_USER}@${VPS_HOST}" "sudo systemctl restart tradingagents-dashboard.service || echo '  (dashboard not yet installed; skipping)'"

echo "==> Reloading Caddy (picks up any Caddyfile changes)"
ssh "${VPS_USER}@${VPS_HOST}" "sudo podman exec agent-caddy caddy reload --config /etc/caddy/Caddyfile || echo '  (caddy reload failed; check container)'"

echo "==> Done. Verify with:"
echo "    ssh ${VPS_USER}@${VPS_HOST} systemctl status tradingagents-dashboard.service"
echo "    ssh ${VPS_USER}@${VPS_HOST} journalctl -u tradingagents-dashboard.service -n 30"
echo "    curl -u rawcell:\$PASS https://rawcell.duckdns.org/trading/"
