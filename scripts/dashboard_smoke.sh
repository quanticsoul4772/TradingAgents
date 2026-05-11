#!/bin/sh
# dashboard_smoke.sh — Phase 5 validation gate (spec 250-dashboard-ui SC-007).
#
# Runs an ISOLATED end-to-end smoke: spawns an ephemeral uvicorn dashboard
# pointed at a temp state dir, runs the engine in --dry-run mode against the
# same temp dir, then probes every dashboard route.
#
# CRITICAL: the smoke MUST NOT touch the production state dir
# (~/.tradingagents/engine/current/). PR #266 — earlier versions did,
# leaving phantom dry-run "completed" entries in the live dashboard.
#
# The engine lock at ~/.tradingagents/engine/lock IS shared (intentional —
# blocks smoke + real engine from racing) but state writes are isolated.
#
# Usage:
#   ./scripts/dashboard_smoke.sh
#   ENGINE_PYTHON=/path/to/python ./scripts/dashboard_smoke.sh
#
# Env overrides:
#   ENGINE_PYTHON   — python that has tradingagents + uvicorn installed
#                     (default: `python`)
#   SMOKE_TICKER    — ticker for the dry-run (default: NVDA)
#   SMOKE_PORT      — port for the ephemeral uvicorn (default: 18765)
#
# Exit codes:
#   0 = all checks pass; 1 = any check failed.

set -eu

ENGINE_PYTHON="${ENGINE_PYTHON:-python}"
TICKER="${SMOKE_TICKER:-NVDA}"
PORT="${SMOKE_PORT:-18765}"

# Isolated state dir — no overlap with ~/.tradingagents/engine/current/.
STATE_DIR="$(mktemp -d -t ta-smoke-state-XXXXXX)"
mkdir -p "${STATE_DIR}/current" "${STATE_DIR}/logs" "${STATE_DIR}/paper"

DASHBOARD_URL="http://127.0.0.1:${PORT}"
UVICORN_PID=""

green() { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
red()   { printf '\033[1;31m✗\033[0m %s\n' "$*" >&2; }

cleanup() {
    if [ -n "${UVICORN_PID}" ]; then
        kill "${UVICORN_PID}" 2>/dev/null || true
        wait "${UVICORN_PID}" 2>/dev/null || true
    fi
    rm -rf "${STATE_DIR}"
}
trap cleanup EXIT INT TERM

failures=0

check_status() {
    label=$1; url=$2; want=$3
    actual=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' "${url}" || echo 000)
    if [ "${actual}" = "${want}" ]; then
        green "${label}: ${url} → ${actual}"
    else
        red "${label}: ${url} → ${actual} (wanted ${want})"
        failures=$((failures + 1))
    fi
}

check_contains() {
    label=$1; url=$2; needle=$3
    body=$(curl -sS --max-time 10 "${url}" || echo "")
    if echo "${body}" | grep -q -- "${needle}"; then
        green "${label}: ${url} contains '${needle}'"
    else
        red "${label}: ${url} missing '${needle}'"
        failures=$((failures + 1))
    fi
}

echo "==> Phase 5 smoke validation (spec 250-dashboard-ui SC-007 — isolated)"
echo "    STATE_DIR=${STATE_DIR}"
echo "    DASHBOARD_URL=${DASHBOARD_URL}"
echo

# 1. Spawn ephemeral uvicorn dashboard pointed at the temp state dir.
echo "==> Starting ephemeral dashboard on port ${PORT}..."
TA_ENGINE_DIR="${STATE_DIR}" \
TA_LOGS_DIR="${STATE_DIR}/logs" \
TA_PAPER_DIR="${STATE_DIR}/paper" \
    "${ENGINE_PYTHON}" -m uvicorn tradingagents.dashboard.app:app \
        --host 127.0.0.1 --port "${PORT}" --log-level warning \
        >/dev/null 2>&1 &
UVICORN_PID=$!

# Wait up to ~5s for the dashboard to bind the port.
i=0
while [ $i -lt 25 ]; do
    if curl -sS --max-time 1 -o /dev/null "${DASHBOARD_URL}/health" 2>/dev/null; then
        break
    fi
    sleep 0.2
    i=$((i + 1))
done
if [ $i -eq 25 ]; then
    red "ephemeral dashboard failed to start on ${DASHBOARD_URL}"
    exit 1
fi

# 2. Liveness — dashboard responsive.
check_status "/health"      "${DASHBOARD_URL}/health"     200

# 3. Engine dry-run — writes to STATE_DIR/current/, not prod (FR-008).
echo "==> Running engine in --dry-run mode (no LLM cost, isolated state)..."
"${ENGINE_PYTHON}" -m tradingagents.engine run \
    --ticker "${TICKER}" --dry-run --state-dir "${STATE_DIR}" \
    >/dev/null 2>&1 || {
    red "engine dry-run failed"
    failures=$((failures + 1))
}
green "engine dry-run completed for ${TICKER} (state in ${STATE_DIR})"

# 4. Schema contract — progress.json + events.jsonl readable + structured.
check_status "/api/poll"    "${DASHBOARD_URL}/api/poll"   200
check_contains "/api/poll has progress" "${DASHBOARD_URL}/api/poll" '"progress"'
check_contains "/api/poll has events"   "${DASHBOARD_URL}/api/poll" '"events"'

# 5. Today summary renders the dry-run ticker.
check_status "/"            "${DASHBOARD_URL}/"           200
check_contains "/ shows ticker" "${DASHBOARD_URL}/" "${TICKER}"

# 6. Live page has HTMX polling (Phase 3 FR-016).
check_status "/live"        "${DASHBOARD_URL}/live"       200
check_contains "/live has HTMX hx-get"     "${DASHBOARD_URL}/live" 'hx-get'
check_contains "/live has 3-sec trigger"   "${DASHBOARD_URL}/live" 'every 3s'

# 7. Partial route returns inner-only fragment (no base layout).
check_status "/live/partial" "${DASHBOARD_URL}/live/partial" 200

# 8. Trigger endpoint validation (FR-011) — invalid ticker rejected.
echo "==> Trigger endpoint validation (FR-011 invalid-ticker rejection)..."
trigger_status=$(curl -sS --max-time 10 -X POST -o /dev/null -w '%{http_code}' \
    "${DASHBOARD_URL}/trigger/badticker" || echo 000)
if [ "${trigger_status}" = "400" ]; then
    green "trigger /badticker → 400 (regex/watchlist rejection)"
else
    red "trigger /badticker → ${trigger_status} (wanted 400)"
    failures=$((failures + 1))
fi

# 9. Empty-state coverage — 404 path on missing ticker debate.
check_status "/ticker/${TICKER}/1900-01-01" "${DASHBOARD_URL}/ticker/${TICKER}/1900-01-01" 404

# 10. Isolation guard — production state dir was NOT touched.
PROD_PROGRESS="${HOME}/.tradingagents/engine/current/progress.json"
if [ -f "${PROD_PROGRESS}" ]; then
    # If a prod run is in flight that's fine — only fail if the dry-run leaked.
    if grep -q '"dry_run":true' "${PROD_PROGRESS}" 2>/dev/null; then
        red "isolation FAIL: prod ${PROD_PROGRESS} contains dry_run marker"
        failures=$((failures + 1))
    else
        green "isolation: prod state untouched (existing run preserved)"
    fi
else
    green "isolation: prod state dir empty (no leakage)"
fi

echo
if [ ${failures} -eq 0 ]; then
    green "ALL CHECKS PASSED — dashboard ready for live run"
    exit 0
else
    red "${failures} check(s) failed — investigate before live run"
    exit 1
fi
