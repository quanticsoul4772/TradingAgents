"""Tests for scripts/daily_signals.py — operator-facing watchlist runner."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts/ to path so we can import daily_signals as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import daily_signals  # noqa: E402

pytestmark = pytest.mark.unit


# ---- _resolve_tickers -----------------------------------------------------


def test_resolve_tickers_comma_separated():
    assert daily_signals._resolve_tickers("AAPL,NVDA,INTC") == ["AAPL", "NVDA", "INTC"]


def test_resolve_tickers_lowercase_normalized():
    assert daily_signals._resolve_tickers("aapl,nvda") == ["AAPL", "NVDA"]


def test_resolve_tickers_strips_whitespace():
    assert daily_signals._resolve_tickers("AAPL , NVDA") == ["AAPL", "NVDA"]


def test_resolve_tickers_from_file(tmp_path):
    p = tmp_path / "watchlist.txt"
    p.write_text("# Watchlist\nAAPL\nNVDA\n  # comment\n\nINTC\n", encoding="utf-8")
    assert daily_signals._resolve_tickers(str(p)) == ["AAPL", "NVDA", "INTC"]


# ---- _resolve_date --------------------------------------------------------


def test_resolve_date_passthrough():
    assert daily_signals._resolve_date("2026-04-15") == "2026-04-15"


def test_resolve_date_default_returns_business_day(monkeypatch):
    # Monkey-patch datetime.now to return a known Saturday
    from datetime import datetime as real_dt

    import daily_signals as ds

    class _FrozenDT(real_dt):
        @classmethod
        def now(cls, tz=None):
            # 2026-05-09 is a Saturday
            return real_dt(2026, 5, 9, 12, 0, 0)

    monkeypatch.setattr(ds, "datetime", _FrozenDT)
    # Saturday → falls back to Friday 2026-05-08
    assert ds._resolve_date(None) == "2026-05-08"


# ---- _build_config --------------------------------------------------------


def test_build_config_active_gates_default():
    config = daily_signals._build_config(
        shadow_gates=False,
        a3_threshold=-5.0,
        a3_lookback=30,
        gate_threshold=80,
    )
    assert config["contrarian_gate_mode"] == "active"
    assert config["uw_momentum_filter_threshold"] == -5.0
    assert config["uw_momentum_filter_lookback_days"] == 30
    assert config["contrarian_gate_threshold"] == 80
    assert config["contrarian_gate_target"] == "hold"
    assert config["llm_provider"] == "anthropic"
    assert config["deep_think_llm"] == "claude-opus-4-7"
    assert config["quick_think_llm"] == "claude-haiku-4-5"


def test_build_config_shadow_gates():
    config = daily_signals._build_config(
        shadow_gates=True,
        a3_threshold=-5.0,
        a3_lookback=30,
        gate_threshold=80,
    )
    assert config["contrarian_gate_mode"] == "shadow"
    # A3 is still on (the shadow flag only gates spec 003)
    assert config["uw_momentum_filter_threshold"] == -5.0


# ---- _extract_rationale_excerpt ------------------------------------------


def test_extract_rationale_skips_rating_line():
    md = """**Rating**: Buy

Strong fundamentals + accelerating momentum suggest entry here.
"""
    assert "Strong fundamentals" in daily_signals._extract_rationale_excerpt(md)
    assert "Rating" not in daily_signals._extract_rationale_excerpt(md)


def test_extract_rationale_skips_gate_annotation():
    md = """**Rating**: Hold

[Spec 003 contrarian gate] Original rating Buy overridden to Hold...

Real reasoning here.
"""
    excerpt = daily_signals._extract_rationale_excerpt(md)
    assert "Real reasoning" in excerpt
    assert "Spec 003" not in excerpt


def test_extract_rationale_truncates_long_text():
    long_text = "x" * 500
    md = f"**Rating**: Buy\n\n{long_text}\n"
    excerpt = daily_signals._extract_rationale_excerpt(md, max_chars=240)
    assert len(excerpt) <= 240
    assert excerpt.endswith("…")


def test_extract_rationale_empty_input():
    assert daily_signals._extract_rationale_excerpt("") == ""
    assert daily_signals._extract_rationale_excerpt(None) == ""


# ---- _detect_gate_overrides -----------------------------------------------


def test_detect_a3_override():
    md = "Some prose\n\n**[A3 momentum filter]** Original rating Underweight overridden..."
    assert daily_signals._detect_gate_overrides(md)["a3"] is True
    assert daily_signals._detect_gate_overrides(md)["spec003"] is False


def test_detect_spec003_override():
    md = "Some prose\n\n**[Spec 003 contrarian gate]** Original rating Buy overridden..."
    assert daily_signals._detect_gate_overrides(md)["spec003"] is True
    assert daily_signals._detect_gate_overrides(md)["a3"] is False


def test_detect_no_overrides():
    md = "**Rating**: Buy\n\nReasoning."
    overrides = daily_signals._detect_gate_overrides(md)
    assert overrides["a3"] is False
    assert overrides["spec003"] is False


def test_detect_overrides_handles_none():
    overrides = daily_signals._detect_gate_overrides(None)
    assert overrides["a3"] is False
    assert overrides["spec003"] is False


# ---- _render_digest -------------------------------------------------------


def _make_row(
    ticker: str,
    rating: str,
    *,
    error: str = "",
    rationale: str = "Some reasoning.",
    a3_overrode: bool = False,
    spec003_overrode: bool = False,
    gate_skipped: str | None = None,
    gate_percentile: float | None = None,
    gate_n_history: int | None = 20,
) -> dict:
    return {
        "ticker": ticker,
        "date": "2026-04-15",
        "rating": rating,
        "error": error,
        "run_seconds": 500.0,
        "decision_markdown": f"**Rating**: {rating}\n\n{rationale}",
        "rationale": rationale,
        "gate_mode": "active",
        "gate_skipped": gate_skipped,
        "gate_feature_value": 60.0,
        "gate_percentile": gate_percentile,
        "gate_n_history": gate_n_history,
        "gate_would_fire": False,
        "gate_fired": False,
        "gate_pre_rating": rating,
        "gate_post_rating": rating,
        "a3_overrode": a3_overrode,
        "spec003_overrode": spec003_overrode,
        "gate_threshold": 80,
    }


def test_render_digest_actionable_signals_appear():
    rows = [
        _make_row("AAPL", "Buy", rationale="Strong fundamentals."),
        _make_row("NVDA", "Overweight", rationale="Solid technicals."),
    ]
    digest = daily_signals._render_digest(rows, "2026-04-15", shadow_gates=False, include_all=False)
    assert "## Actionable signals" in digest
    assert "AAPL" in digest
    assert "**Buy**" in digest
    assert "NVDA" in digest
    assert "**Overweight**" in digest


def test_render_digest_hold_suppressed_by_default():
    rows = [
        _make_row("AAPL", "Buy"),
        _make_row("MSFT", "Hold", rationale="Neutral indicators."),
    ]
    digest = daily_signals._render_digest(rows, "2026-04-15", shadow_gates=False, include_all=False)
    # Hold doesn't appear when no gate overrides + no --include-all
    assert "## Filtered" not in digest


def test_render_digest_include_all_shows_holds():
    rows = [
        _make_row("AAPL", "Buy"),
        _make_row("MSFT", "Hold"),
    ]
    digest = daily_signals._render_digest(rows, "2026-04-15", shadow_gates=False, include_all=True)
    assert "## Filtered" in digest
    assert "MSFT" in digest


def test_render_digest_gate_override_appears_in_filtered():
    rows = [
        _make_row("AAPL", "Buy"),
        _make_row("GOOGL", "Hold", spec003_overrode=True, gate_percentile=92.0),
    ]
    digest = daily_signals._render_digest(rows, "2026-04-15", shadow_gates=False, include_all=False)
    assert "## Filtered" in digest
    assert "GOOGL" in digest
    assert "Spec 003 contrarian gate overrode" in digest


def test_render_digest_a3_override_appears_in_filtered():
    rows = [
        _make_row("AAPL", "Buy"),
        _make_row("INTC", "Hold", a3_overrode=True),
    ]
    digest = daily_signals._render_digest(rows, "2026-04-15", shadow_gates=False, include_all=False)
    assert "## Filtered" in digest
    assert "INTC" in digest
    assert "A3 momentum filter overrode" in digest


def test_render_digest_no_actionable_message():
    rows = [
        _make_row("MSFT", "Hold"),
        _make_row("INTC", "Underweight"),
    ]
    digest = daily_signals._render_digest(rows, "2026-04-15", shadow_gates=False, include_all=True)
    assert "calibrated-abstention mode" in digest


def test_render_digest_errors_section():
    rows = [
        _make_row("AAPL", "Buy"),
        _make_row("FAILING", "", error="ConnectionError: timeout"),
    ]
    digest = daily_signals._render_digest(rows, "2026-04-15", shadow_gates=False, include_all=False)
    assert "## Errors" in digest
    assert "FAILING" in digest
    assert "ConnectionError" in digest


def test_render_digest_methodology_section_present():
    rows = [_make_row("AAPL", "Buy")]
    digest = daily_signals._render_digest(rows, "2026-04-15", shadow_gates=False, include_all=False)
    assert "## Methodology" in digest
    assert "21 trading days" in digest
    assert "calibrated abstention" in digest.lower()
    assert "research substrate, not investment advice" in digest


def test_render_digest_summary_counts_correct():
    rows = [
        _make_row("AAPL", "Buy"),
        _make_row("NVDA", "Overweight"),
        _make_row("MSFT", "Hold"),
        _make_row("INTC", "Hold", a3_overrode=True),
        _make_row("GOOGL", "Hold", spec003_overrode=True),
        _make_row("FAILING", "", error="oops"),
    ]
    digest = daily_signals._render_digest(rows, "2026-04-15", shadow_gates=False, include_all=True)
    assert "**Universe**: 6 tickers" in digest
    assert "**Actionable**: 2" in digest  # AAPL, NVDA
    assert (
        "**Hold (calibrated abstention)**: 3" in digest
    )  # MSFT + INTC + GOOGL (the 2 overrides land at Hold)
    assert "**Spec 003 gate overrode**: 1" in digest
    assert "**A3 filter overrode**: 1" in digest
    assert "**Errored**: 1" in digest


def test_render_digest_shadow_mode_label():
    rows = [_make_row("AAPL", "Buy")]
    digest = daily_signals._render_digest(rows, "2026-04-15", shadow_gates=True, include_all=False)
    assert "shadow (annotation only)" in digest


def test_render_digest_active_mode_label():
    rows = [_make_row("AAPL", "Buy")]
    digest = daily_signals._render_digest(rows, "2026-04-15", shadow_gates=False, include_all=False)
    assert "active (rating override)" in digest


# ---- _emit_signals_csv (Spec 002 paper-trading harness consumer) ----------


def test_emit_csv_writes_required_columns(tmp_path):
    import pandas as pd

    out = tmp_path / "signals.csv"
    rows = [
        _make_row("AAPL", "Buy"),
        _make_row("NVDA", "Overweight"),
        _make_row("INTC", "Hold"),
    ]
    for r in rows:
        r["gate_threshold"] = 80
        r["a3_threshold"] = -5.0
        r["model_deep"] = "claude-opus-4-7"
        r["model_quick"] = "claude-haiku-4-5"
    daily_signals._emit_signals_csv(rows, "2026-04-15", out)

    df = pd.read_csv(out)
    required = {"ticker", "analysis_date", "rating"}
    assert required.issubset(set(df.columns))
    assert len(df) == 3
    assert (df["analysis_date"] == "2026-04-15").all()


def test_emit_csv_includes_optional_columns_for_cross_tool_compat(tmp_path):
    out = tmp_path / "s.csv"
    row = _make_row("NVDA", "Buy")
    row["gate_threshold"] = 80
    row["a3_threshold"] = -5.0
    row["model_deep"] = "claude-opus-4-7"
    row["model_quick"] = "claude-haiku-4-5"
    daily_signals._emit_signals_csv([row], "2026-04-15", out)

    import pandas as pd

    df = pd.read_csv(out)
    for col in [
        "gate_threshold",
        "a3_threshold",
        "model_deep",
        "model_quick",
        "run_seconds",
        "error",
    ]:
        assert col in df.columns


def test_emit_csv_atomic_write_no_tmp_residue(tmp_path):
    out = tmp_path / "out.csv"
    daily_signals._emit_signals_csv([_make_row("AAPL", "Buy")], "2026-04-15", out)
    assert out.exists()
    assert not list(tmp_path.glob("*.tmp"))


def test_emit_csv_overwrites_existing_file(tmp_path):
    out = tmp_path / "out.csv"
    out.write_text("stale content\n", encoding="utf-8")
    daily_signals._emit_signals_csv([_make_row("AAPL", "Buy")], "2026-04-15", out)
    assert "stale content" not in out.read_text(encoding="utf-8")
    assert "AAPL" in out.read_text(encoding="utf-8")


def test_emit_csv_consumable_by_paper_trade(tmp_path):
    """Round-trip: emit_csv output is parseable by paper_trade's CSV reader."""
    out = tmp_path / "signals.csv"
    daily_signals._emit_signals_csv(
        [_make_row("NVDA", "Overweight"), _make_row("HD", "Hold")],
        "2026-04-15",
        out,
    )
    # Reuse paper_trade.py's _read_signals_csv via direct import
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import paper_trade  # noqa: E402

    df = paper_trade._read_signals_csv(out)
    assert {"ticker", "analysis_date", "rating"}.issubset(df.columns)
    signals = paper_trade._signals_for_date(df, __import__("datetime").date(2026, 4, 15))
    assert signals == {"NVDA": "Overweight", "HD": "Hold"}
