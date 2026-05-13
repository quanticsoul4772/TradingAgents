# Deployment — TradingAgents Dashboard (Spec 250)

> Operator runbook for deploying the dashboard to the existing Hetzner VPS that already runs `agent-harness-v2`. Reuses the same Caddy + Podman Quadlet + systemd + Duck DNS infrastructure.

## What gets installed

| Component | Purpose |
|---|---|
| `tradingagents-engine-daily.service` + `.timer` | Cron-equivalent: fires the engine at 17:00 ET Mon-Fri |
| `tradingagents-trigger-poller.service` | USER unit (runs as `agent`): polls `~/.tradingagents/triggers/` for ad-hoc requests written by the dashboard, spawns engine subprocesses |
| `tradingagents-dashboard.container` | Podman Quadlet for the dashboard backend |
| Caddyfile snippet | Adds `handle_path /trading/*` to the existing site block |

## Prerequisites (already on the VPS per agent-harness-v2)

- Hetzner CPX31 (Ubuntu 24.04)
- Caddy 2.x running as a Podman Quadlet container (`agent-caddy`)
- Podman with Quadlet support
- systemd ≥ 240 (verify: `systemctl --version | head -1` — older versions silently treat the `OnCalendar=Mon..Fri 17:00 America/New_York` TZ as UTC, breaking FR-033)
- Duck DNS subdomain `rawcell.duckdns.org` resolving to the VPS
- Existing basic-auth user `rawcell` configured in the parent Caddyfile
- Existing Let's Encrypt cert managed by Caddy for `rawcell.duckdns.org`

## Setup

### 0. Verify systemd version ≥ 240 (G-12 / FR-033)

Older systemd silently treats `OnCalendar=Mon..Fri 17:00 America/New_York` as UTC, which would fire the daily timer at the wrong wall-clock time (13:00 ET in summer, 12:00 ET in winter). One-line gate that exits non-zero on older systemd:

```bash
ssh rawcell "systemctl --version | head -1 | awk '{exit (\$2 < 240)}'" \
    || { echo 'FAIL: systemd >= 240 required for timezone-aware OnCalendar'; exit 1; }
echo 'OK: systemd version satisfies FR-033'
```

If this fails, do not proceed with steps 4 (systemd units) or onward — the timer will fire at the wrong time and corrupt SC-007 cost-meter validation.

### 1. Place the source on the VPS

```bash
ssh rawcell "sudo mkdir -p /home/agent/tradingagents && sudo chown rawcell:rawcell /home/agent/tradingagents"
./deploy/deploy.sh
```

### 2. Create the Python venv

```bash
ssh rawcell
cd /home/agent/tradingagents
python3.12 -m venv .venv
.venv/bin/pip install -e .
```

### 3. Provision API keys via systemd-creds

The credstore + cred names match the existing agent-harness-v2 install:

```bash
# Skip if already present (agent-harness-v2 already provisioned anthropic-key
# and exa-key — verify with: sudo ls /etc/credstore/)
sudo systemd-creds encrypt - /etc/credstore/anthropic-key.encrypted
# paste sk-ant-...
# Ctrl-D

sudo systemd-creds encrypt - /etc/credstore/exa-key.encrypted
# paste exa key
# Ctrl-D
```

### 4a. Install the daily-timer system units

```bash
sudo cp deploy/systemd/tradingagents-engine-daily.service /etc/systemd/system/
sudo cp deploy/systemd/tradingagents-engine-daily.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tradingagents-engine-daily.timer
```

Verify:

```bash
systemctl list-timers tradingagents-engine-daily.timer
# Expect a "Next" time at the next Mon-Fri 17:00 ET
```

### 4b. Install the trigger-poller user unit

The dashboard's ad-hoc trigger UI writes request files to
`~/.tradingagents/triggers/`; a USER systemd service running as `agent`
polls that directory and spawns engine subprocesses. No root needed at
runtime — the poller spawns the engine directly via `python -m
tradingagents.engine`.

```bash
# Create + label the trigger queue dir (one-time)
sudo install -d -o agent -g agent /home/agent/.tradingagents/triggers
sudo restorecon -Rv /home/agent/.tradingagents/triggers

# Allow user services to run when no SSH session is open (one-time)
sudo loginctl enable-linger agent

# Install the unit into the agent user's systemd dir
sudo install -o agent -g agent -m 0644 \
    deploy/systemd/tradingagents-trigger-poller.service \
    /home/agent/.config/systemd/user/

# Reload + enable as the agent user (USER systemd, not system)
sudo -u agent XDG_RUNTIME_DIR=/run/user/$(id -u agent) \
    systemctl --user daemon-reload
sudo -u agent XDG_RUNTIME_DIR=/run/user/$(id -u agent) \
    systemctl --user enable --now tradingagents-trigger-poller.service
```

Verify:

```bash
sudo -u agent XDG_RUNTIME_DIR=/run/user/$(id -u agent) \
    systemctl --user status tradingagents-trigger-poller.service
# Expect: active (running)

# Tail logs:
sudo -u agent XDG_RUNTIME_DIR=/run/user/$(id -u agent) \
    journalctl --user -u tradingagents-trigger-poller -f
```

### 4c. Remove the obsolete adhoc unit (if previously installed)

```bash
sudo systemctl stop 'tradingagents-engine-adhoc@*.service' 2>/dev/null || true
sudo rm -f /etc/systemd/system/tradingagents-engine-adhoc@.service
sudo systemctl daemon-reload
```

### 5. Merge the Caddyfile snippet

Open the existing operator Caddyfile (typically `/srv/agent-harness/caddy/Caddyfile`) and add the `handle_path /trading/*` block from `deploy/Caddyfile.snippet` inside the `rawcell.duckdns.org { ... }` site block. Replace `{{ EXISTING_BCRYPT_HASH }}` with the real bcrypt hash from the existing `rawcell` user definition (use the same hash as `/v2/` and `/dashboard/`).

Reload Caddy (host-installed, not containerized — verified on this VPS):

```bash
sudo systemctl reload caddy
```

Verify the path 404s for now (dashboard not built yet):

```bash
curl -u rawcell:$PASS https://rawcell.duckdns.org/trading/
# Expect: 502 Bad Gateway (dashboard not running yet) — that's correct for Phase 4.
# After Phase 2+3 ship and the container is built, this returns the dashboard.
```

### 6. (Phase 2+3 only) Build + run the dashboard container

After Phase 2 (FastAPI backend) and Phase 3 (HTMX templates) land, the dashboard image becomes buildable:

```bash
cd /home/agent/tradingagents
podman build -t localhost/tradingagents/dashboard:latest -f deploy/Containerfile .
sudo cp deploy/quadlet/tradingagents-dashboard.container /etc/containers/systemd/
sudo systemctl daemon-reload
sudo systemctl enable --now tradingagents-dashboard.service
```

Now `https://rawcell.duckdns.org/trading/` serves the dashboard.

## Daily workflow

1. **5pm ET Mon-Fri**: `tradingagents-engine-daily.timer` fires; engine runs the watchlist (~3-4h). Cost ~$10/day.
2. **End of run**: engine writes signals.csv + spawns `paper_trade.py step` to update the live paper portfolio.
3. **You**: open `https://rawcell.duckdns.org/trading/` on your phone any time to view the dashboard (Phase 2+3).

## Manual ad-hoc fire (testing or off-schedule)

Three ways:

```bash
# 1. Full daily run via the system unit (~$10-40, 3-4h)
sudo systemctl start tradingagents-engine-daily.service

# 2. Single ticker via the dashboard's trigger UI (recommended; ~$0.40, ~10min)
#    — type ticker on https://rawcell.duckdns.org/trading/, hit Run.
#    The dashboard writes ~/.tradingagents/triggers/<TICKER>.req; the
#    trigger-poller picks it up within 2 sec and spawns the engine.

# 3. Single ticker by writing the .req file directly (bypasses dashboard auth)
echo "$(date -u +%FT%TZ)" > ~/.tradingagents/triggers/NVDA.req
```

Tail logs:

```bash
journalctl -u tradingagents-engine-daily.service -f                    # daily
sudo -u agent XDG_RUNTIME_DIR=/run/user/$(id -u agent) \
    journalctl --user -u tradingagents-trigger-poller -f               # poller
```

## Troubleshooting

- **Timer says next fire is in UTC, not ET**: systemd is < 240. Either upgrade systemd (Ubuntu 24.04 ships 255, should be fine) OR convert the OnCalendar to a UTC absolute time accounting for ET/EDT.
- **Caddy returns 502 on /trading/**: dashboard container isn't running. Check `systemctl status tradingagents-dashboard.service`. Phase 2/3 must be deployed first.
- **Engine subprocess can't read state log dir**: SELinux Z label mismatch. Verify the container's `User=1000:1000` matches the operator UID that owns `~/.tradingagents/`.
- **paper_trade.py step fails with "equity_curve dates not strictly ascending"**: there's an existing portfolio entry from a future date. Fix: prune the JSON state file to remove the future-dated entries, OR use a fresh `--portfolio-id` for a clean start.

## Cross-references

- Spec: [`specs/250-dashboard-ui/spec.md`](../specs/250-dashboard-ui/spec.md)
- Engine: [`tradingagents/engine/`](../tradingagents/engine/) (Phase 1 + 1b)
- agent-harness-v2 reference setup: see your existing VPS deployment
