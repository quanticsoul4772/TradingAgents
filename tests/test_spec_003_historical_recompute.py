"""Unit tests for spec_003_historical_recompute helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_003_historical_recompute import (  # noqa: E402
    _resolve_featurizer,
)

pytestmark = pytest.mark.unit


def test_resolve_featurizer_finds_bull_keyword_count():
    """Default featurizer must resolve."""
    fn = _resolve_featurizer("bull_keyword_count")
    assert fn is not None
    # Featurizer should be callable on a string
    val = fn("This stock is bullish bullish strong outperform")
    assert isinstance(val, (int, float))
    assert val > 0


def test_resolve_featurizer_returns_none_for_unknown():
    assert _resolve_featurizer("not_a_real_featurizer_name") is None


def test_resolve_featurizer_finds_bear_keyword_count():
    """Bear-side featurizer (alt --feature CLI option) must resolve."""
    fn = _resolve_featurizer("bear_keyword_count")
    assert fn is not None


def test_list_state_logs_handles_missing_log_base(tmp_path, monkeypatch):
    """Pointing LOG_BASE at a non-existent directory returns empty list."""
    import spec_003_historical_recompute as mod

    monkeypatch.setattr(mod, "LOG_BASE", tmp_path / "nonexistent")
    result = mod._list_state_logs(None)
    assert result == []


def test_list_state_logs_walks_proper_structure(tmp_path, monkeypatch):
    """Verify discovery walks the TICKER/TradingAgentsStrategy_logs/full_states_log_DATE.json structure."""
    import spec_003_historical_recompute as mod

    base = tmp_path / "logs"
    base.mkdir()
    for ticker in ["AAA", "BBB"]:
        log_dir = base / ticker / "TradingAgentsStrategy_logs"
        log_dir.mkdir(parents=True)
        (log_dir / "full_states_log_2026-04-17.json").write_text("{}", encoding="utf-8")
        (log_dir / "full_states_log_2026-04-24.json").write_text("{}", encoding="utf-8")
    # Add an irrelevant file that should be ignored
    (base / "AAA" / "TradingAgentsStrategy_logs" / "other.txt").write_text("x", encoding="utf-8")

    monkeypatch.setattr(mod, "LOG_BASE", base)
    result = mod._list_state_logs(None)
    # 2 tickers × 2 dates = 4 log files
    assert len(result) == 4
    tickers_seen = {t for t, _, _ in result}
    assert tickers_seen == {"AAA", "BBB"}


def test_list_state_logs_applies_ticker_filter(tmp_path, monkeypatch):
    import spec_003_historical_recompute as mod

    base = tmp_path / "logs"
    base.mkdir()
    for ticker in ["AAA", "BBB", "CCC"]:
        log_dir = base / ticker / "TradingAgentsStrategy_logs"
        log_dir.mkdir(parents=True)
        (log_dir / "full_states_log_2026-04-17.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(mod, "LOG_BASE", base)
    result = mod._list_state_logs({"AAA", "CCC"})
    assert len(result) == 2
    assert {t for t, _, _ in result} == {"AAA", "CCC"}


def test_list_state_logs_skips_dirs_without_strategy_logs(tmp_path, monkeypatch):
    """Ticker dirs without TradingAgentsStrategy_logs subdir are skipped."""
    import spec_003_historical_recompute as mod

    base = tmp_path / "logs"
    base.mkdir()
    (base / "BARE_TICKER").mkdir()
    real_log = base / "REAL" / "TradingAgentsStrategy_logs"
    real_log.mkdir(parents=True)
    (real_log / "full_states_log_2026-04-17.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(mod, "LOG_BASE", base)
    result = mod._list_state_logs(None)
    assert len(result) == 1
    assert result[0][0] == "REAL"
