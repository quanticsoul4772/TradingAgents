# Deployment — TradingAgents Dashboard (Spec 250)

> Operator runbook for deploying the dashboard to the existing Hetzner VPS that already runs `agent-harness-v2`. Reuses the same Caddy + Podman Quadlet + systemd + Duck DNS infrastructure.

## What gets installed

| Component | Purpose | Phase |
|---|---|---|
| `tradingagents-engine-daily.service` + `.timer` | Cron-equivalent: fires the engine at 17:00 ET Mon-Fri | 1 (works today) |
| `tradingagents-engine-adhoc@.service` | Templated unit invoked by the dashboard's `POST /trigger/{ticker}` | 1 (works today) |
| `tradingagents-dashboard.container` | Podman Quadlet for the dashboard backend | 2 (templated; needs the dashboard image to exist) |
| Caddyfile snippet | Adds `handle_path /trading/*` to the existing site block | 4 (this PR) |

## Prerequisites (already on the VPS per agent-harness-v2)

- Hetzner CPX31 (Ubuntu 24.04)
- Caddy 2.x running as a Podman Quadlet container (`agent-caddy`)
- Podman with Quadlet support
- systemd ≥ 240 (verify: `systemctl --version | head -1` — older versions silently treat the `OnCalendar=Mon..Fri 17:00 America/New_York` TZ as UTC, breaking FR-033)
- Duck DNS subdomain `rawcell.duckdns.org` resolving to the VPS
- Existing basic-auth user `rawcell` configured in the parent Caddyfile
- Existing Let's Encrypt cert managed by Caddy for `rawcell.duckdns.org`

## Setup

### 1. Place the source on the VPS

```bash
ssh rawcell@vps "sudo mkdir -p /srv/tradingagents && sudo chown rawcell:rawcell /srv/tradingagents"
./deploy/deploy.sh
```

### 2. Create the Python venv

```bash
ssh rawcell@vps
cd /srv/tradingagents
python3.12 -m venv .venv
.venv/bin/pip install -e .
```

### 3. Provision API keys via systemd-creds

Per the agent-harness-v2 secrets pattern:

```bash
sudo systemd-creds encrypt - /etc/credstore.encrypted/anthropic-api-key
# paste sk-ant-...
# Ctrl-D

sudo systemd-creds encrypt - /etc/credstore.encrypted/exa-api-key
# paste exa key
# Ctrl-D
```

### 4. Install the systemd units

```bash
sudo cp deploy/systemd/tradingagents-engine-daily.service /etc/systemd/system/
sudo cp deploy/systemd/tradingagents-engine-daily.timer /etc/systemd/system/
sudo cp deploy/systemd/tradingagents-engine-adhoc@.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tradingagents-engine-daily.timer
```

Verify:

```bash
systemctl list-timers tradingagents-engine-daily.timer
# Expect a "Next" time at the next Mon-Fri 17:00 ET
```

### 5. Merge the Caddyfile snippet

Open the existing operator Caddyfile (typically `/srv/agent-harness/caddy/Caddyfile`) and add the `handle_path /trading/*` block from `deploy/Caddyfile.snippet` inside the `rawcell.duckdns.org { ... }` site block. Replace `{{ EXISTING_BCRYPT_HASH }}` with the real bcrypt hash from the existing `rawcell` user definition (use the same hash as `/v2/` and `/dashboard/`).

Reload Caddy:

```bash
sudo podman exec agent-caddy caddy reload --config /etc/caddy/Caddyfile
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
cd /srv/tradingagents
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

```bash
ssh rawcell@vps
sudo systemctl start tradingagents-engine-daily.service
# OR for one ticker:
sudo systemctl start tradingagents-engine-adhoc@NVDA.service
```

Tail logs:

```bash
journalctl -u tradingagents-engine-daily.service -f
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
