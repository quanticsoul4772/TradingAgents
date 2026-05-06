"""CLI tests for scripts/paper_trade.py — step idempotency + status no-op.

Uses typer's CliRunner to invoke subcommands against a tmp state dir + a
hand-crafted signals CSV. yfinance calls are patched to avoid network.
"""

from __future__ import annotations

import hashlib
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import paper_trade as pt_module  # noqa: E402

from tradingagents.paper.pricing import clear_price_cache  # noqa: E402

runner = CliRunner()


def _frame(closes: list[float], start: str = "2026-04-03") -> pd.DataFrame:
    idx = pd.date_range(start, periods=len(closes), freq="B")
    return pd.DataFrame({"Close": closes}, index=idx)


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_price_cache()
    yield
    clear_price_cache()


def _patch_yfinance(monkeypatch):
    """Stub yfinance so CLI doesn't hit the network."""

    def fake_history(ticker, start, end):
        # Return a flat-price 30-day frame
        n = 30
        return _frame([100.0] * n, start=start)

    # Patch the underlying fetcher used inside pricing
    monkeypatch.setattr("tradingagents.paper.pricing._fetch_history", fake_history)

    # Patch sectors.get_sector to skip yfinance
    monkeypatch.setattr("tradingagents.paper.engine.get_sector", lambda t, p: "Technology")

    # Patch the calendar helper in paper_trade.py to return a fixed list
    def fake_calendar(benchmark, start, end):
        d = start
        out = []
        while d <= end:
            if d.weekday() < 5:
                out.append(d)
            d = d + timedelta(days=1)
        return out

    monkeypatch.setattr(pt_module, "_trading_days_in_range", fake_calendar)


def _make_csv(tmp_path: Path, rows: list[tuple[str, str, str]]) -> Path:
    """rows: list of (ticker, analysis_date, rating)."""
    p = tmp_path / "signals.csv"
    df = pd.DataFrame(rows, columns=["ticker", "analysis_date", "rating"])
    df.to_csv(p, index=False)
    return p


@pytest.mark.unit
def test_step_idempotent_byte_identical_state(monkeypatch, tmp_path):
    """SC-002: re-running step for the same date produces byte-identical state."""
    _patch_yfinance(monkeypatch)
    csv = _make_csv(tmp_path, [("NVDA", "2026-04-03", "Overweight")])
    state_dir = tmp_path / "state"
    digest_dir = tmp_path / "digests"

    # First step
    r1 = runner.invoke(
        pt_module.app,
        [
            "step",
            "--signals-csv",
            str(csv),
            "--date",
            "2026-04-03",
            "--state-dir",
            str(state_dir),
            "--digest-dir",
            str(digest_dir),
            "--portfolio-id",
            "test",
        ],
    )
    assert r1.exit_code == 0, r1.stdout
    state_file = state_dir / "test.json"
    assert state_file.exists()
    hash1 = hashlib.sha256(state_file.read_bytes()).hexdigest()

    # Second step on same date
    r2 = runner.invoke(
        pt_module.app,
        [
            "step",
            "--signals-csv",
            str(csv),
            "--date",
            "2026-04-03",
            "--state-dir",
            str(state_dir),
            "--digest-dir",
            str(digest_dir),
            "--portfolio-id",
            "test",
        ],
    )
    assert r2.exit_code == 0, r2.stdout
    hash2 = hashlib.sha256(state_file.read_bytes()).hexdigest()
    assert hash1 == hash2, "state file must be byte-identical after no-op step"


@pytest.mark.unit
def test_step_initializes_empty_portfolio_on_first_run(monkeypatch, tmp_path):
    _patch_yfinance(monkeypatch)
    csv = _make_csv(tmp_path, [])  # no signals → no entries
    state_dir = tmp_path / "state"
    digest_dir = tmp_path / "digests"

    r = runner.invoke(
        pt_module.app,
        [
            "step",
            "--signals-csv",
            str(csv),
            "--date",
            "2026-04-03",
            "--state-dir",
            str(state_dir),
            "--digest-dir",
            str(digest_dir),
            "--portfolio-id",
            "fresh",
        ],
    )
    assert r.exit_code == 0
    assert (state_dir / "fresh.json").exists()


@pytest.mark.unit
def test_status_on_missing_portfolio_exits_zero(monkeypatch, tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    r = runner.invoke(
        pt_module.app,
        ["status", "--portfolio-id", "nonexistent", "--state-dir", str(state_dir)],
    )
    assert r.exit_code == 0
    assert "No portfolio found" in r.stdout


@pytest.mark.unit
def test_status_does_not_modify_state(monkeypatch, tmp_path):
    """US3: status MUST NOT write state or events. SC: state file mtime + size unchanged."""
    _patch_yfinance(monkeypatch)
    csv = _make_csv(tmp_path, [("NVDA", "2026-04-03", "Overweight")])
    state_dir = tmp_path / "state"
    digest_dir = tmp_path / "digests"

    # Seed a portfolio via step
    runner.invoke(
        pt_module.app,
        [
            "step",
            "--signals-csv",
            str(csv),
            "--date",
            "2026-04-03",
            "--state-dir",
            str(state_dir),
            "--digest-dir",
            str(digest_dir),
            "--portfolio-id",
            "test",
        ],
    )
    state_file = state_dir / "test.json"
    events_file = state_dir / "test.events.jsonl"
    state_size_before = state_file.stat().st_size
    events_size_before = events_file.stat().st_size if events_file.exists() else 0

    # Status should not modify
    r = runner.invoke(
        pt_module.app,
        ["status", "--portfolio-id", "test", "--state-dir", str(state_dir)],
    )
    assert r.exit_code == 0
    state_size_after = state_file.stat().st_size
    events_size_after = events_file.stat().st_size if events_file.exists() else 0
    assert state_size_before == state_size_after
    assert events_size_before == events_size_after


@pytest.mark.unit
def test_step_missing_csv_exits_2(tmp_path):
    state_dir = tmp_path / "state"
    r = runner.invoke(
        pt_module.app,
        [
            "step",
            "--signals-csv",
            str(tmp_path / "nope.csv"),
            "--date",
            "2026-04-03",
            "--state-dir",
            str(state_dir),
        ],
    )
    assert r.exit_code == 2
    assert "not found" in r.stdout


@pytest.mark.unit
def test_step_csv_missing_required_columns_exits_2(tmp_path):
    bad = tmp_path / "bad.csv"
    pd.DataFrame({"ticker": ["NVDA"], "rating": ["Buy"]}).to_csv(
        bad, index=False
    )  # missing analysis_date
    state_dir = tmp_path / "state"
    r = runner.invoke(
        pt_module.app,
        [
            "step",
            "--signals-csv",
            str(bad),
            "--date",
            "2026-04-03",
            "--state-dir",
            str(state_dir),
        ],
    )
    assert r.exit_code == 2
    assert "missing required columns" in r.stdout
