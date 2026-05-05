# Repro command for experiment 2026-05-04-007-phase4-bot-models-smoke
# Spec 001 Phase 4 live-propagate validation: NVDA 2026-01-30 with
# bot_models = {"market": "claude-sonnet-4-6"} override.
$ErrorActionPreference = "Stop"
& uv run --no-sync python experiments/2026-05-04-007-phase4-bot-models-smoke/drive.py
