"""Spec 003.5 (sector-baseline fallback) tests for ContrarianGate.

Spec: specs/003-sector-baseline-gate/

Tests cover:
  - Fallback ladder: per_ticker → sector → none
  - `gate_baseline` annotation field with 3 values
  - `n_history_per_ticker` / `n_history_sector` annotation fields
  - Mode interactions (off / shadow / active)
  - Ablation flag preservation (SC-005)
  - Boundary check at the per-ticker floor
"""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from tradingagents.signals.contrarian_gate import ContrarianGate
from tradingagents.signals.sector_baseline import SectorPool


def _gate(
    *,
    mode: str = "shadow",
    sector_fallback_enabled: bool = True,
    threshold: int = 80,
    history_floor: int = 20,
    sector_floor: int = 20,
):
    return ContrarianGate(
        config={
            "contrarian_gate_mode": mode,
            "contrarian_gate_threshold": threshold,
            "contrarian_gate_target": "hold",
            "contrarian_gate_signal": "market_report",
            "contrarian_gate_feature": "bull_keyword_count",
            "contrarian_gate_sector_fallback_enabled": sector_fallback_enabled,
            "contrarian_gate_sector_floor": sector_floor,
        },
        history_floor=history_floor,
    )


def _patch_per_ticker(values: list[float]):
    """Patch ContrarianGate._load_per_ticker_history to return the given values."""
    return patch.object(ContrarianGate, "_load_per_ticker_history", return_value=values)


def _patch_sector(values: list[float], sector: str = "Technology"):
    """Patch ContrarianGate._load_sector_pool to return a SectorPool with given values."""
    pool = SectorPool(
        sector=sector,
        before_date=date(2026, 5, 6),
        values=values,
        n=len(values),
        contributors={"NVDA": len(values)},
    )
    return patch.object(ContrarianGate, "_load_sector_pool", return_value=pool)


# -- Fallback ladder ---------------------------------------------------------


@pytest.mark.unit
def test_gate_baseline_per_ticker_when_history_thick():
    """Per-ticker N>=20 → uses per_ticker baseline; sector path NOT consulted."""
    gate = _gate()
    sector_called = []

    def spy_sector(*args, **kwargs):
        sector_called.append((args, kwargs))
        return SectorPool(sector="Technology", before_date=date(2026, 5, 6))

    with (
        _patch_per_ticker([10.0] * 25),
        patch.object(ContrarianGate, "_load_sector_pool", side_effect=spy_sector),
    ):
        ann = gate.compute_annotation("NVDA", "bullish", "Overweight", trade_date="2026-05-06")
    assert ann.gate_baseline == "per_ticker"
    assert ann.n_history_per_ticker == 25
    assert ann.n_history == 25  # backward-compat alias
    assert sector_called == []  # sector path NOT entered


@pytest.mark.unit
def test_gate_baseline_sector_when_per_ticker_thin():
    """Per-ticker N=0, sector pool N=80, current value at 92nd percentile → sector fires."""
    gate = _gate()
    # 80 sector observations all = 50; current value = 100 → 100th percentile
    with _patch_per_ticker([]), _patch_sector([50.0] * 80):
        ann = gate.compute_annotation(
            "NVDA",
            " ".join(["uptrend"] * 100),  # bull_keyword_count → 100
            "Overweight",
            trade_date="2026-05-06",
        )
    assert ann.gate_baseline == "sector"
    assert ann.n_history_per_ticker == 0
    assert ann.n_history_sector == 80
    assert ann.n_history == 80  # alias
    assert ann.would_fire is True
    assert ann.percentile == 100.0


@pytest.mark.unit
def test_gate_baseline_none_when_both_thin():
    """Per-ticker N=5, sector N=10 (both below floor) → gate_baseline=none, no fire."""
    gate = _gate()
    with _patch_per_ticker([10.0] * 5), _patch_sector([10.0] * 10):
        ann = gate.compute_annotation("NVDA", "bullish", "Overweight", trade_date="2026-05-06")
    assert ann.gate_baseline == "none"
    assert ann.n_history_per_ticker == 5
    assert ann.n_history_sector == 10
    assert ann.would_fire is None
    assert ann.percentile is None
    assert ann.gate_skipped == "insufficient_history"


@pytest.mark.unit
def test_unknown_sector_collapses_to_none():
    """Sector lookup returns "Unknown" → sector pool empty → gate_baseline=none."""
    gate = _gate()
    empty_pool = SectorPool(sector="Unknown", before_date=date(2026, 5, 6))
    with (
        _patch_per_ticker([]),
        patch.object(ContrarianGate, "_load_sector_pool", return_value=empty_pool),
    ):
        ann = gate.compute_annotation("NEW", "bullish", "Overweight", trade_date="2026-05-06")
    assert ann.gate_baseline == "none"
    assert ann.n_history_sector == 0


@pytest.mark.unit
def test_active_mode_downgrades_when_sector_baseline_fires():
    """Active mode + sector fires + Overweight → maybe_override_decision returns gate_fired=True."""
    gate = _gate(mode="active")
    with _patch_per_ticker([]), _patch_sector([50.0] * 80):
        ann = gate.compute_annotation(
            "NVDA",
            " ".join(["uptrend"] * 100),
            "Overweight",
            trade_date="2026-05-06",
        )
    assert ann.gate_baseline == "sector"
    assert ann.would_fire is True

    # Apply the override
    decision_md = "**Rating**: Overweight\n\nLooks bullish."
    modified, gate_fired = gate.maybe_override_decision(decision_md, ann)
    assert gate_fired is True
    assert "Hold" in modified.split("Rating")[1]


@pytest.mark.unit
def test_shadow_mode_annotates_but_does_not_downgrade_when_sector_fires():
    """Shadow mode + sector would-fire → annotation reflects would_fire=True but no override."""
    gate = _gate(mode="shadow")
    with _patch_per_ticker([]), _patch_sector([50.0] * 80):
        ann = gate.compute_annotation(
            "NVDA",
            " ".join(["uptrend"] * 100),
            "Overweight",
            trade_date="2026-05-06",
        )
    assert ann.would_fire is True
    decision_md = "**Rating**: Overweight\n\nLooks bullish."
    modified, gate_fired = gate.maybe_override_decision(decision_md, ann)
    assert gate_fired is False
    assert "Overweight" in modified


@pytest.mark.unit
def test_off_mode_emits_no_useful_annotation():
    """Off mode → returns mode_off skipped annotation regardless of sector path."""
    gate = _gate(mode="off")
    ann = gate.compute_annotation("NVDA", "bullish", "Overweight", trade_date="2026-05-06")
    assert ann.gate_skipped == "mode_off"


@pytest.mark.unit
def test_ablation_flag_disables_sector_fallback():
    """SC-005: sector_fallback_enabled=False → spec 003 byte-identity behavior on cold-start."""
    gate = _gate(sector_fallback_enabled=False)
    sector_called = []

    def spy_sector(*args, **kwargs):
        sector_called.append((args, kwargs))
        return SectorPool(
            sector="Technology", before_date=date(2026, 5, 6), values=[50.0] * 100, n=100
        )

    with (
        _patch_per_ticker([]),
        patch.object(ContrarianGate, "_load_sector_pool", side_effect=spy_sector),
    ):
        ann = gate.compute_annotation("NVDA", "bullish", "Overweight", trade_date="2026-05-06")
    assert ann.gate_baseline == "none"
    assert ann.n_history_sector == 0
    assert ann.would_fire is None
    assert sector_called == []  # sector path skipped entirely when flag False


@pytest.mark.unit
def test_per_ticker_floor_strict_check():
    """Boundary: per-ticker N exactly equals history_floor → uses per-ticker (>=, not >)."""
    gate = _gate(history_floor=20)
    with _patch_per_ticker([10.0] * 20), _patch_sector([99.0] * 100):
        ann = gate.compute_annotation("NVDA", "bullish", "Overweight", trade_date="2026-05-06")
    assert ann.gate_baseline == "per_ticker"
    assert ann.n_history_per_ticker == 20


@pytest.mark.unit
def test_per_ticker_just_below_floor_falls_to_sector():
    """Boundary: per-ticker N = floor-1 → falls to sector if sector qualifies."""
    gate = _gate(history_floor=20)
    with _patch_per_ticker([10.0] * 19), _patch_sector([50.0] * 80):
        ann = gate.compute_annotation(
            "NVDA",
            " ".join(["uptrend"] * 100),
            "Overweight",
            trade_date="2026-05-06",
        )
    assert ann.gate_baseline == "sector"
    assert ann.n_history_per_ticker == 19
    assert ann.n_history_sector == 80


@pytest.mark.unit
def test_no_trade_date_skips_sector_path():
    """trade_date=None (legacy callers) → sector path skipped, falls through to none."""
    gate = _gate()
    with _patch_per_ticker([]):
        ann = gate.compute_annotation("NVDA", "bullish", "Overweight", trade_date=None)
    assert ann.gate_baseline == "none"
    assert ann.gate_skipped == "insufficient_history"


# -- US2: Audit annotation fields -------------------------------------------


@pytest.mark.unit
def test_n_history_alias_matches_per_ticker_baseline():
    gate = _gate()
    with _patch_per_ticker([10.0] * 25):
        ann = gate.compute_annotation("NVDA", "bullish", "Overweight", trade_date="2026-05-06")
    assert ann.n_history == ann.n_history_per_ticker == 25


@pytest.mark.unit
def test_n_history_alias_matches_sector_baseline():
    gate = _gate()
    with _patch_per_ticker([]), _patch_sector([50.0] * 80):
        ann = gate.compute_annotation("NVDA", "bullish", "Overweight", trade_date="2026-05-06")
    assert ann.n_history == ann.n_history_sector == 80


@pytest.mark.unit
def test_annotation_contains_both_n_history_fields_always():
    """Both n_history_per_ticker and n_history_sector populated regardless of which fired."""
    gate = _gate()
    with _patch_per_ticker([10.0] * 25), _patch_sector([50.0] * 80):
        ann = gate.compute_annotation("NVDA", "bullish", "Overweight", trade_date="2026-05-06")
    d = ann.to_dict()
    assert "n_history_per_ticker" in d
    assert "n_history_sector" in d
    assert d["n_history_per_ticker"] == 25
    # n_history_sector is 0 because per-ticker fired and sector wasn't consulted
    assert d["n_history_sector"] == 0


@pytest.mark.unit
def test_audit_corpus_filter_by_baseline():
    """Quickstart Walkthrough 3 audit pattern: filter list of annotations by gate_baseline."""
    gate = _gate()
    annotations = []
    for n_pt, n_sect in [(25, 0), (25, 0), (0, 80), (0, 80), (0, 0), (5, 10)]:
        with _patch_per_ticker([10.0] * n_pt), _patch_sector([50.0] * n_sect):
            ann = gate.compute_annotation("X", "prose", "Overweight", trade_date="2026-05-06")
        annotations.append(ann.to_dict())

    per_ticker = [a for a in annotations if a["gate_baseline"] == "per_ticker"]
    sector = [a for a in annotations if a["gate_baseline"] == "sector"]
    none = [a for a in annotations if a["gate_baseline"] == "none"]
    assert len(per_ticker) == 2
    assert len(sector) == 2
    assert len(none) == 2
