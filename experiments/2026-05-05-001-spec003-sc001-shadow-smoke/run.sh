#!/usr/bin/env bash
# Spec 003 SC-001 shadow smoke: NVDA 2026-01-30 with contrarian_gate_mode='shadow'
set -euo pipefail
uv run --no-sync python experiments/2026-05-05-001-spec003-sc001-shadow-smoke/drive.py
