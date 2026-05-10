"""TradingAgents engine — orchestrates propagates + writes progress.json + events.jsonl
for the dashboard (specs/250-dashboard-ui/).

Per spec FR-003, the engine runs in a separate subprocess from the dashboard
backend. Engine writes state to disk; dashboard reads. Read-only separation.
"""
