"""TradingAgents dashboard — read-only FastAPI surface (spec 250-dashboard-ui).

Phase 2 MVP: server-rendered HTML via Jinja2. Phase 3 will add HTMX
interactivity + Tailwind via CDN.

Per FR-003: dashboard reads ~/.tradingagents/engine/current/{progress.json,events.jsonl},
~/.tradingagents/logs/<TICKER>/, ~/.tradingagents/paper/<id>.json. NEVER writes.
"""
