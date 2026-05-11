#!/bin/sh
# dashboard_smoke.sh — Phase 5 validation gate (spec 250-dashboard-ui SC-007).
#
# Runs the engine in --dry-run mode (no LLM cost) then probes every dashboard
# route on the LOCAL container to verify end-to-end wiring before live spend.
#
# Usage:
#   ./scripts/dashboard_smoke.sh            # against localhost:8000 (run on VPS or via SSH tunnel)
#   DASHBOARD_URL=https://rawcell.duckdns.org/trading ./scripts/dashboard_smoke.sh
#
# Exit codes:
#   0 = all checks pass; 1 = any check failed.

set -eu

DASHBOARD_URL="${DASHBOARD_URL:-http://127.0.0.1:8000}"
ENGINE_PYTHON="${ENGINE_PYTHON:-python}"
TICKER="${SMOKE_TICKER:-NVDA}"

green() { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
red()   { printf '\033[1;31m✗\033[0m %s\n' "$*" >&2; }

# basic_auth credential — only required when DASHBOARD_URL is the public Caddy URL.
CURL_OPTS="-sS --max-time 10"
if [ -n "${SMOKE_BASIC_AUTH:-}" ]; then
    CURL_OPTS="${CURL_OPTS} -u ${SMOKE_BASIC_AUTH}"
fi

failures=0

check_status() {
    label=$1; url=$2; want=$3
    actual=$(curl ${CURL_OPTS} -o /dev/null -w '%{http_code}' "${url}" || echo 000)
    if [ "${actual}" = "${want}" ]; then
        green "${label}: ${url} → ${actual}"
    else
        red "${label}: ${url} → ${actual} (wanted ${want})"
        failures=$((failures + 1))
    fi
}

check_contains() {
    label=$1; url=$2; needle=$3
    body=$(curl ${CURL_OPTS} "${url}" || echo "")
    if echo "${body}" | grep -q -- "${needle}"; then
        green "${label}: ${url} contains '${needle}'"
    else
        red "${label}: ${url} missing '${needle}'"
        failures=$((failures + 1))
    fi
}

echo "==> Phase 5 smoke validation (spec 250-dashboard-ui SC-007)"
echo "    DASHBOARD_URL=${DASHBOARD_URL}"
echo

# 1. Liveness — engine + dashboard both responsive
check_status "/health"      "${DASHBOARD_URL}/health"     200

# 2. Engine dry-run — produces fake events without LLM cost (FR-008)
echo "==> Running engine in --dry-run mode (no LLM cost)..."
${ENGINE_PYTHON} -m tradingagents.engine run --ticker "${TICKER}" --dry-run >/dev/null 2>&1 || {
    red "engine dry-run failed"
    failures=$((failures + 1))
}
green "engine dry-run completed for ${TICKER}"

# 3. Schema contract — progress.json + events.jsonl readable + structured
check_status "/api/poll"    "${DASHBOARD_URL}/api/poll"   200
check_contains "/api/poll has progress" "${DASHBOARD_URL}/api/poll" '"progress"'
check_contains "/api/poll has events"   "${DASHBOARD_URL}/api/poll" '"events"'

# 4. Today summary renders the dry-run ticker
check_status "/"            "${DASHBOARD_URL}/"           200
check_contains "/ shows ticker" "${DASHBOARD_URL}/" "${TICKER}"

# 5. Live page has HTMX polling (Phase 3 FR-016)
check_status "/live"        "${DASHBOARD_URL}/live"       200
check_contains "/live has HTMX hx-get"     "${DASHBOARD_URL}/live" 'hx-get'
check_contains "/live has 3-sec trigger"   "${DASHBOARD_URL}/live" 'every 3s'

# 6. Partial route returns inner-only fragment (no base layout)
check_status "/live/partial" "${DASHBOARD_URL}/live/partial" 200

# 7. Trigger endpoint validation (FR-011) — invalid ticker rejected
echo "==> Trigger endpoint validation (FR-011 invalid-ticker rejection)..."
trigger_status=$(curl ${CURL_OPTS} -X POST -o /dev/null -w '%{http_code}' \
    "${DASHBOARD_URL}/trigger/badticker" || echo 000)
if [ "${trigger_status}" = "400" ]; then
    green "trigger /badticker → 400 (regex/watchlist rejection)"
else
    red "trigger /badticker → ${trigger_status} (wanted 400)"
    failures=$((failures + 1))
fi

# 8. Empty-state coverage — verify 404 path on missing ticker debate
check_status "/ticker/${TICKER}/1900-01-01" "${DASHBOARD_URL}/ticker/${TICKER}/1900-01-01" 404

echo
if [ ${failures} -eq 0 ]; then
    green "ALL CHECKS PASSED — dashboard ready for live run"
    exit 0
else
    red "${failures} check(s) failed — investigate before live run"
    exit 1
fi
