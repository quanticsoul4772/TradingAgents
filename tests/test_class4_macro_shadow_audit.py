"""Unit test for scripts/class4_macro_shadow_audit.py.

Covers task T013 from specs/012-class-4-macro-filter/tasks.md.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

# Load the script as a module (it's not in the package; lives under scripts/)
_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "class4_macro_shadow_audit.py"
_spec = importlib.util.spec_from_file_location("class4_macro_shadow_audit", _SCRIPT_PATH)
audit_mod = importlib.util.module_from_spec(_spec)
sys.modules["class4_macro_shadow_audit"] = audit_mod
_spec.loader.exec_module(audit_mod)

pytestmark = pytest.mark.unit


def _write_fixture_log(logs_dir: Path, ticker: str, date: str, c4_dict: dict | None) -> Path:
    """Build a state log fixture under logs_dir/<ticker>/TradingAgentsStrategy_logs/."""
    ticker_dir = logs_dir / ticker / "TradingAgentsStrategy_logs"
    ticker_dir.mkdir(parents=True, exist_ok=True)
    log_path = ticker_dir / f"full_states_log_{date}.json"
    payload = {
        "company_of_interest": ticker,
        "trade_date": date,
        "final_trade_decision": "**Rating**: Underweight",
    }
    if c4_dict is not None:
        payload["class_4_macro"] = c4_dict
    log_path.write_text(json.dumps(payload), encoding="utf-8")
    return log_path


def test_extract_fires_finds_would_fire_records(tmp_path):
    """T013: _extract_fires walks state logs + returns would-fire-bear records."""
    # Fixture: 2 fires + 1 non-fire + 1 missing class_4_macro
    _write_fixture_log(
        tmp_path,
        "AAPL",
        "2026-04-30",
        {
            "vix_snapshot": 15.42,
            "vix_threshold": 18.0,
            "bear_mode": "shadow",
            "would_fire_bear": True,
            "fired_bear": False,
            "pre_rating": "Underweight",
            "post_rating": "Underweight",
        },
    )
    _write_fixture_log(
        tmp_path,
        "MSFT",
        "2026-04-25",
        {
            "vix_snapshot": 14.80,
            "vix_threshold": 18.0,
            "bear_mode": "shadow",
            "would_fire_bear": True,
            "fired_bear": False,
            "pre_rating": "Sell",
            "post_rating": "Sell",
        },
    )
    _write_fixture_log(
        tmp_path,
        "JPM",
        "2026-04-20",
        {
            "vix_snapshot": 22.0,
            "vix_threshold": 18.0,
            "bear_mode": "shadow",
            "would_fire_bear": False,  # not a fire
            "fired_bear": False,
            "pre_rating": "Hold",
            "post_rating": "Hold",
        },
    )
    _write_fixture_log(tmp_path, "JNJ", "2026-04-15", None)  # no class_4_macro key

    fires = audit_mod._extract_fires(tmp_path)
    assert len(fires) == 2  # AAPL + MSFT only
    tickers = sorted(r["ticker"] for r in fires)
    assert tickers == ["AAPL", "MSFT"]
    # Each record has trade_date populated from filename
    for r in fires:
        assert r["trade_date"] in {"2026-04-30", "2026-04-25"}
        assert r["would_fire_bear"] is True


def test_verdict_below_n_floor_not_ready(tmp_path):
    """T013 / SC-010: n=2 fires < 30 floor → not ready for default-on flip."""
    fires = [
        {"ticker": "AAPL", "realized_alpha_pct": 5.0},
        {"ticker": "MSFT", "realized_alpha_pct": 3.0},
    ]
    verdict = audit_mod._verdict(fires)
    assert verdict["n_total"] == 2
    assert verdict["n_valid_alpha"] == 2
    assert verdict["mean_alpha_pct"] == pytest.approx(4.0)
    assert verdict["ready_for_default_on_flip"] is False
    assert "n=2 < 30" in verdict["reason"]


def test_verdict_below_alpha_floor_not_ready():
    """T013 / SC-010: 30+ fires but mean α < -1pp → not ready (mean realized α below floor)."""
    fires = [{"ticker": "X", "realized_alpha_pct": -2.0}] * 30
    verdict = audit_mod._verdict(fires)
    assert verdict["n_valid_alpha"] == 30
    assert verdict["mean_alpha_pct"] == pytest.approx(-2.0)
    assert verdict["ready_for_default_on_flip"] is False
    assert "below" in verdict["reason"] or "floor" in verdict["reason"]
