"""Tests for spec 003 contrarian gate (Phase 1 + Phase 2).

Covers:
- GateAnnotation dataclass shape
- ContrarianGate construction (config validation)
- compute_annotation in all 4 mode/state combinations
  (off / shadow / active × fire / no-fire)
- Per-ticker baseline (not pooled — critical for correctness)
- N<20 → gate skipped with reason
- Active-mode override changes rating only on Buy/OW
- Active-mode override does NOT change Hold/UW/Sell ratings
- Pluggable signal_id + feature
- Cache failure handling
- Backwards-compat: mode="off" returns no-op annotation, no override
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tradingagents.signals.cache import init_cache, record_value
from tradingagents.signals.contrarian_gate import (
    ContrarianGate,
    GateAnnotation,
    _percentile_of_value,
    _resolve_featurizer,
)

pytestmark = pytest.mark.unit


# ---- _percentile_of_value -------------------------------------------------


def test_percentile_empty_history():
    assert _percentile_of_value([], 5.0) == 0.0


def test_percentile_top_of_distribution():
    history = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert _percentile_of_value(history, 10.0) == 100.0


def test_percentile_bottom_of_distribution():
    history = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert _percentile_of_value(history, 0.5) == 0.0


def test_percentile_middle():
    history = [1.0, 2.0, 3.0, 4.0, 5.0]
    # current=3.0, three values <= 3.0 (1, 2, 3) → 60%
    assert _percentile_of_value(history, 3.0) == 60.0


def test_percentile_at_threshold_value():
    history = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    # current=80 → 8 of 10 are <= 80 → 80%
    assert _percentile_of_value(history, 80) == 80.0


# ---- _resolve_featurizer --------------------------------------------------


def test_resolve_featurizer_known():
    fn = _resolve_featurizer("bull_keyword_count")
    assert fn is not None
    # Sanity check the resolved featurizer is callable on prose
    assert fn("strong buy momentum") > 0


def test_resolve_featurizer_unknown():
    assert _resolve_featurizer("nonexistent_featurizer_xyz") is None


# ---- ContrarianGate construction ------------------------------------------


def test_construct_default_mode_off():
    gate = ContrarianGate(config={})
    assert gate.mode == "off"
    assert gate.threshold == 80
    assert gate.target == "hold"
    assert gate.signal_id == "market_report"
    assert gate.feature == "bull_keyword_count"


def test_construct_unknown_mode_defaults_to_off(caplog):
    gate = ContrarianGate(config={"contrarian_gate_mode": "broken_mode"})
    assert gate.mode == "off"


def test_construct_unknown_target_defaults_to_hold(caplog):
    gate = ContrarianGate(
        config={"contrarian_gate_mode": "active", "contrarian_gate_target": "broken"}
    )
    assert gate.target == "hold"


def test_construct_custom_threshold():
    gate = ContrarianGate(
        config={"contrarian_gate_mode": "active", "contrarian_gate_threshold": 90}
    )
    assert gate.threshold == 90


def test_construct_pluggable_signal_and_feature():
    gate = ContrarianGate(
        config={
            "contrarian_gate_mode": "shadow",
            "contrarian_gate_signal": "news_report",
            "contrarian_gate_feature": "bear_keyword_count",
        }
    )
    assert gate.signal_id == "news_report"
    assert gate.feature == "bear_keyword_count"


# ---- compute_annotation: mode "off" ---------------------------------------


def test_off_mode_returns_skipped_annotation():
    gate = ContrarianGate(config={})
    ann = gate.compute_annotation("NVDA", "some prose", "Overweight")
    assert ann.mode == "off"
    assert ann.gate_skipped == "mode_off"
    assert ann.feature_value is None
    assert ann.percentile is None
    assert ann.would_fire is None


# ---- compute_annotation: featurizer / cache edge cases --------------------


def test_unknown_feature_returns_skipped():
    gate = ContrarianGate(
        config={
            "contrarian_gate_mode": "shadow",
            "contrarian_gate_feature": "nonexistent_xyz",
        }
    )
    ann = gate.compute_annotation("NVDA", "prose", "Hold")
    assert ann.gate_skipped == "missing_featurizer"


def test_insufficient_history_skipped(tmp_path: Path):
    """When fewer than history_floor cached rows exist for the ticker, skip."""
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    # Seed only 5 rows for NVDA — well under default floor of 20
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="bullish strong momentum upgrade",
            cache_path=cache_path,
        )
    gate = ContrarianGate(config={"contrarian_gate_mode": "shadow"}, cache_path=cache_path)
    ann = gate.compute_annotation("NVDA", "bullish prose", "Overweight")
    assert ann.gate_skipped == "insufficient_history"
    assert ann.n_history == 5
    assert ann.feature_value is not None  # featurizer ran successfully
    assert ann.percentile is None
    assert ann.would_fire is None


def test_lower_history_floor_via_constructor(tmp_path: Path):
    """history_floor is parameterized so tests can exercise without 20+ rows."""
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value=f"{'bullish ' * (i + 1)} prose",
            cache_path=cache_path,
        )
    gate = ContrarianGate(
        config={"contrarian_gate_mode": "shadow"},
        cache_path=cache_path,
        history_floor=3,
    )
    ann = gate.compute_annotation("NVDA", "bullish bullish prose", "Overweight")
    assert ann.gate_skipped is None
    assert ann.n_history == 3
    assert ann.feature_value is not None
    assert ann.percentile is not None


# ---- compute_annotation: shadow mode with sufficient history --------------


def test_shadow_mode_high_percentile_fires_for_bullish_rating(tmp_path: Path):
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    # Seed 5 historical NVDA rows with low bull_keyword_count
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="neutral analysis observed",  # 0 bull keywords
            cache_path=cache_path,
        )
    gate = ContrarianGate(
        config={"contrarian_gate_mode": "shadow", "contrarian_gate_threshold": 80},
        cache_path=cache_path,
        history_floor=3,
    )
    # Current propagate has high bull keywords -> top of distribution
    ann = gate.compute_annotation(
        "NVDA",
        "bullish strong momentum breakout uptrend rally accelerating upgrade",
        "Overweight",
    )
    assert ann.gate_skipped is None
    assert ann.percentile == 100.0  # higher than all 5 historical values
    assert ann.would_fire is True


def test_shadow_mode_high_percentile_no_fire_for_hold(tmp_path: Path):
    """Even with high percentile, would_fire is False if PM rating is Hold."""
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="neutral",
            cache_path=cache_path,
        )
    gate = ContrarianGate(
        config={"contrarian_gate_mode": "shadow", "contrarian_gate_threshold": 80},
        cache_path=cache_path,
        history_floor=3,
    )
    ann = gate.compute_annotation("NVDA", "bullish strong momentum", "Hold")
    assert ann.percentile == 100.0
    assert ann.would_fire is False  # rating is Hold, not Buy/OW


def test_shadow_mode_low_percentile_no_fire(tmp_path: Path):
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    # Seed 5 historical NVDA rows with high bull_keyword_count
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="bullish strong momentum breakout uptrend rally accelerating upgrade",
            cache_path=cache_path,
        )
    gate = ContrarianGate(
        config={"contrarian_gate_mode": "shadow", "contrarian_gate_threshold": 80},
        cache_path=cache_path,
        history_floor=3,
    )
    # Current propagate has zero bull keywords -> bottom of distribution
    ann = gate.compute_annotation("NVDA", "neutral analysis", "Overweight")
    assert ann.percentile == 0.0
    assert ann.would_fire is False


# ---- Per-ticker baseline (not pooled) -- CRITICAL CORRECTNESS -------------


def test_per_ticker_baseline_uses_only_target_ticker(tmp_path: Path):
    """The percentile must be computed against THIS ticker's history only,
    NOT pooled across all cached tickers (which would re-introduce
    between-ticker artifacts)."""
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    # AAPL has high bull_keyword_count history
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="AAPL",
            date=f"2025-01-{i + 1:02d}",
            value="bullish strong momentum breakout uptrend",  # high
            cache_path=cache_path,
        )
    # NVDA has low bull_keyword_count history
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="neutral observation",  # 0 bull keywords
            cache_path=cache_path,
        )
    gate = ContrarianGate(
        config={"contrarian_gate_mode": "shadow"},
        cache_path=cache_path,
        history_floor=3,
    )
    # Current NVDA propagate has 1 bull keyword
    ann = gate.compute_annotation("NVDA", "bullish prose", "Overweight")
    # Compared to NVDA's history (all 0), 1 > 0 → 100th percentile
    # If pooled with AAPL's high counts, this would be much lower
    assert ann.n_history == 3
    assert ann.percentile == 100.0


# ---- maybe_override_decision: active mode ---------------------------------


def _make_decision_md(rating: str = "Overweight") -> str:
    return f"""# Trading Decision

**Rating**: {rating}

Some reasoning prose here.
"""


def test_active_mode_override_buy_to_hold(tmp_path: Path):
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="neutral",
            cache_path=cache_path,
        )
    gate = ContrarianGate(
        config={"contrarian_gate_mode": "active"},
        cache_path=cache_path,
        history_floor=3,
    )
    ann = gate.compute_annotation("NVDA", "bullish strong momentum", "Buy")
    assert ann.would_fire is True
    decision = _make_decision_md("Buy")
    modified, fired = gate.maybe_override_decision(decision, ann)
    assert fired is True
    assert "Hold" in modified
    assert "Spec 003 contrarian gate" in modified
    assert "Buy" not in modified.split("---")[0]  # not in the original section


def test_active_mode_override_overweight_to_hold(tmp_path: Path):
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="neutral",
            cache_path=cache_path,
        )
    gate = ContrarianGate(
        config={"contrarian_gate_mode": "active"},
        cache_path=cache_path,
        history_floor=3,
    )
    ann = gate.compute_annotation("NVDA", "bullish strong momentum", "Overweight")
    decision = _make_decision_md("Overweight")
    modified, fired = gate.maybe_override_decision(decision, ann)
    assert fired is True
    assert "**Rating**: Hold" in modified


def test_active_mode_underweight_target(tmp_path: Path):
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="neutral",
            cache_path=cache_path,
        )
    gate = ContrarianGate(
        config={
            "contrarian_gate_mode": "active",
            "contrarian_gate_target": "underweight",
        },
        cache_path=cache_path,
        history_floor=3,
    )
    ann = gate.compute_annotation("NVDA", "bullish strong momentum", "Buy")
    decision = _make_decision_md("Buy")
    modified, fired = gate.maybe_override_decision(decision, ann)
    assert fired is True
    assert "**Rating**: Underweight" in modified


def test_active_mode_no_override_for_hold(tmp_path: Path):
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="neutral",
            cache_path=cache_path,
        )
    gate = ContrarianGate(
        config={"contrarian_gate_mode": "active"},
        cache_path=cache_path,
        history_floor=3,
    )
    ann = gate.compute_annotation("NVDA", "bullish strong momentum", "Hold")
    decision = _make_decision_md("Hold")
    modified, fired = gate.maybe_override_decision(decision, ann)
    assert fired is False
    assert modified == decision  # unchanged


def test_active_mode_no_override_for_underweight(tmp_path: Path):
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="neutral",
            cache_path=cache_path,
        )
    gate = ContrarianGate(
        config={"contrarian_gate_mode": "active"},
        cache_path=cache_path,
        history_floor=3,
    )
    ann = gate.compute_annotation("NVDA", "bullish strong momentum", "Underweight")
    decision = _make_decision_md("Underweight")
    modified, fired = gate.maybe_override_decision(decision, ann)
    assert fired is False
    assert modified == decision


# ---- Shadow mode: never overrides -----------------------------------------


def test_shadow_mode_never_overrides(tmp_path: Path):
    """Shadow mode must NEVER modify the decision markdown — byte-identical guarantee."""
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="neutral",
            cache_path=cache_path,
        )
    gate = ContrarianGate(
        config={"contrarian_gate_mode": "shadow"},
        cache_path=cache_path,
        history_floor=3,
    )
    ann = gate.compute_annotation("NVDA", "bullish strong momentum", "Buy")
    assert ann.would_fire is True  # gate fires
    decision = _make_decision_md("Buy")
    modified, fired = gate.maybe_override_decision(decision, ann)
    assert fired is False
    assert modified == decision  # byte-identical


# ---- Off mode: never overrides --------------------------------------------


def test_off_mode_never_overrides():
    gate = ContrarianGate(config={})
    ann = GateAnnotation(
        mode="off",
        signal_id="market_report",
        feature="bull_keyword_count",
        threshold=80,
        target="hold",
        feature_value=None,
        percentile=None,
        n_history=None,
        would_fire=None,
        gate_skipped="mode_off",
    )
    decision = _make_decision_md("Buy")
    modified, fired = gate.maybe_override_decision(decision, ann)
    assert fired is False
    assert modified == decision


# ---- to_dict ---------------------------------------------------------------


def test_annotation_to_dict_complete_keys():
    ann = GateAnnotation(
        mode="active",
        signal_id="market_report",
        feature="bull_keyword_count",
        threshold=80,
        target="hold",
        feature_value=42.0,
        percentile=85.0,
        n_history=20,
        would_fire=True,
        gate_skipped=None,
    )
    d = ann.to_dict()
    assert set(d.keys()) == {
        "mode",
        "signal_id",
        "feature",
        "threshold",
        "target",
        "feature_value",
        "percentile",
        "n_history",
        "would_fire",
        "gate_skipped",
        # Spec 003.5 additions
        "gate_baseline",
        "n_history_per_ticker",
        "n_history_sector",
    }
    assert d["feature_value"] == 42.0


# ---- Pluggable source (User Story 4 / Phase 3 hook) -----------------------


def test_pluggable_signal_id_uses_different_cache_rows(tmp_path: Path):
    cache_path = tmp_path / "cache.db"
    init_cache(cache_path)
    # market_report rows have low bull_count
    for i in range(5):
        record_value(
            signal_id="market_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="neutral",
            cache_path=cache_path,
        )
    # news_report rows have high bull_count
    for i in range(5):
        record_value(
            signal_id="news_report",
            ticker="NVDA",
            date=f"2025-01-{i + 1:02d}",
            value="bullish strong momentum breakout uptrend rally",
            cache_path=cache_path,
        )
    # Gate configured for news_report — current low-bull prose should be at low percentile
    gate = ContrarianGate(
        config={
            "contrarian_gate_mode": "shadow",
            "contrarian_gate_signal": "news_report",
        },
        cache_path=cache_path,
        history_floor=3,
    )
    ann = gate.compute_annotation("NVDA", "neutral", "Overweight")
    assert ann.signal_id == "news_report"
    assert ann.percentile == 0.0  # current prose has 0 bull keywords; history all high
    assert ann.would_fire is False


# ---- Integration sanity: GateAnnotation can be merged into state log ------


def test_annotation_dict_jsonable():
    """The annotation dict must be JSON-serializable (will be written to state log)."""
    import json

    ann = GateAnnotation(
        mode="shadow",
        signal_id="market_report",
        feature="bull_keyword_count",
        threshold=80,
        target="hold",
        feature_value=42.0,
        percentile=85.0,
        n_history=20,
        would_fire=True,
        gate_skipped=None,
    )
    json.dumps(ann.to_dict())  # should not raise
