"""Spec 001 Phase 3 — convergence shortcut for the bull/bear debate stage.

When 3+ analyst Signals share a direction with magnitude > 0.7, the bull/bear
debate stage is skipped (per spec FR-006). This saves the debate-round LLM
calls (typically the most expensive part of a propagate after the analysts
themselves).

This module ships the deterministic decision logic + a corpus-forecast
function. Wiring into ``conditional_logic.py`` is deferred — Phase 3.5.

The decision is testable against the existing state-log corpus by deriving
Signals from the cached analyst prose and asking "would the shortcut have
fired here?" We forecast token-savings before committing to the production
change.
"""

from __future__ import annotations

from dataclasses import dataclass

from tradingagents.signals.bots import Signal

# Default thresholds per spec FR-006.
DEFAULT_MIN_CONVERGING_SIGNALS = 3
DEFAULT_MAGNITUDE_THRESHOLD = 0.7


@dataclass
class ShortcutDecision:
    """Output of should_skip_debate — auditable decision record."""

    skip: bool
    reason: str  # human-readable explanation
    n_bullish_strong: int  # count of bots with direction>0 AND magnitude>threshold
    n_bearish_strong: int  # count of bots with direction<0 AND magnitude>threshold
    n_signals_total: int
    n_abstaining: int


def should_skip_debate(
    signals: list[Signal],
    min_converging: int = DEFAULT_MIN_CONVERGING_SIGNALS,
    magnitude_threshold: float = DEFAULT_MAGNITUDE_THRESHOLD,
) -> ShortcutDecision:
    """Decide whether to skip the bull/bear debate based on Signal convergence.

    Per FR-006: skip if ``min_converging`` or more Signals share a direction
    with magnitude > ``magnitude_threshold``. Direction is sign(Signal.direction).
    Abstaining signals don't count toward either side.

    Returns a ShortcutDecision capturing the boolean + a human-readable reason
    + the per-direction counts for audit trails.
    """
    n_total = len(signals)
    n_abstaining = sum(1 for s in signals if s.abstain or s.magnitude == 0.0)

    n_bullish_strong = 0
    n_bearish_strong = 0
    for s in signals:
        if s.abstain or s.magnitude <= magnitude_threshold:
            continue
        if s.direction > 0:
            n_bullish_strong += 1
        elif s.direction < 0:
            n_bearish_strong += 1

    if n_bullish_strong >= min_converging:
        return ShortcutDecision(
            skip=True,
            reason=(
                f"{n_bullish_strong} bots converged bullish with magnitude>{magnitude_threshold} "
                f"(threshold {min_converging})"
            ),
            n_bullish_strong=n_bullish_strong,
            n_bearish_strong=n_bearish_strong,
            n_signals_total=n_total,
            n_abstaining=n_abstaining,
        )
    if n_bearish_strong >= min_converging:
        return ShortcutDecision(
            skip=True,
            reason=(
                f"{n_bearish_strong} bots converged bearish with magnitude>{magnitude_threshold} "
                f"(threshold {min_converging})"
            ),
            n_bullish_strong=n_bullish_strong,
            n_bearish_strong=n_bearish_strong,
            n_signals_total=n_total,
            n_abstaining=n_abstaining,
        )

    return ShortcutDecision(
        skip=False,
        reason=(
            f"no convergence: {n_bullish_strong} strong-bullish + "
            f"{n_bearish_strong} strong-bearish bots (threshold {min_converging})"
        ),
        n_bullish_strong=n_bullish_strong,
        n_bearish_strong=n_bearish_strong,
        n_signals_total=n_total,
        n_abstaining=n_abstaining,
    )


@dataclass
class ShortcutCorpusReport:
    """Aggregate forecast across many state logs."""

    n_total: int
    n_would_skip: int
    n_bullish_skip: int
    n_bearish_skip: int

    @property
    def skip_rate(self) -> float:
        if self.n_total == 0:
            return 0.0
        return self.n_would_skip / self.n_total


def analyze_shortcut_corpus(
    signals_by_propagate: list[list[Signal]],
    min_converging: int = DEFAULT_MIN_CONVERGING_SIGNALS,
    magnitude_threshold: float = DEFAULT_MAGNITUDE_THRESHOLD,
) -> ShortcutCorpusReport:
    """Forecast: across ``signals_by_propagate`` (one inner list per
    historical propagate), how many would have triggered the shortcut?

    Used to estimate token-savings before wiring the shortcut into
    production. SC-004 acceptance: ≥30% reduction on shortcut-fires AND
    ≥15% overall reduction.
    """
    n_total = len(signals_by_propagate)
    n_skip = 0
    n_bull_skip = 0
    n_bear_skip = 0
    for sigs in signals_by_propagate:
        decision = should_skip_debate(sigs, min_converging, magnitude_threshold)
        if decision.skip:
            n_skip += 1
            if decision.n_bullish_strong >= decision.n_bearish_strong:
                n_bull_skip += 1
            else:
                n_bear_skip += 1
    return ShortcutCorpusReport(
        n_total=n_total,
        n_would_skip=n_skip,
        n_bullish_skip=n_bull_skip,
        n_bearish_skip=n_bear_skip,
    )
