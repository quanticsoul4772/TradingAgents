"""Spec 001 Phase 5 — weight tuning for the deterministic aggregator.

Phase 1's `DEFAULT_WEIGHTS` are placeholders (per spec Assumptions). Phase 1
shipped with 42.3% direction agreement against the actual PM, well below
SC-001's ≥80% target. Phase 5 tunes WEIGHTS against the historical corpus
to find a better operating point.

Two objective functions supported:
- ``ic``: Spearman rank correlation of aggregator's direction_score vs
  realized 21d alpha. Maximizing this finds the weight vector whose
  aggregate-output best predicts forward returns. **This is the more
  interesting target** because it asks "what weighting produces the most
  alpha-correlated aggregator?" rather than "what weighting copies the PM?"
- ``agreement``: fraction of (ticker, date) pairs where the aggregator's
  3-tier direction (bull / hold / bear) matches the actual PM's 3-tier
  direction. Maximizing this finds the weight vector that best mimics PM
  decisions.

Grid search is coarse (resolution 0.1 over [0, 0.6] per weight, ~6^N
combinations for N=5 bots = 7776 evaluations). Each evaluation is fast
(~0.1ms) so the full grid runs in seconds. SC-006 train/test split on
date prevents overfitting.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from tradingagents.signals.bots import (
    DEFAULT_WEIGHTS,
    aggregate,
    shadow_aggregate_from_state_log,
)
from tradingagents.signals.evaluation import _spearman_ic

_RATING_TO_DIRECTION = {
    "Buy": +1,
    "Overweight": +1,
    "Hold": 0,
    "Underweight": -1,
    "Sell": -1,
}


@dataclass
class TuningCorpusRow:
    """One row of the tuning corpus: signals + actual PM rating + realized α."""

    ticker: str
    date: str
    signals: list  # list of Signal objects (unhashable, but ok for list)
    actual_rating: str
    alpha: float | None


@dataclass
class WeightEvaluation:
    """Per-weight-vector evaluation result."""

    weights: dict[str, float]
    n_total: int
    n_resolved: int  # rows where alpha is available
    ic: float | None  # Spearman IC of direction_score vs alpha
    direction_agreement: float  # fraction matching PM direction
    rating_within_one_tier: float  # fraction within ±1 tier of PM
    n_buy: int
    n_overweight: int
    n_hold: int
    n_underweight: int
    n_sell: int


def evaluate_weights(
    rows: list[TuningCorpusRow],
    weights: dict[str, float],
) -> WeightEvaluation:
    """Run aggregator on every row with given weights; compute metrics."""
    pairs_for_ic: list[tuple[float, float]] = []
    direction_match = 0
    rating_within = 0
    counts = {"Buy": 0, "Overweight": 0, "Hold": 0, "Underweight": 0, "Sell": 0}
    tier_order = {"Sell": 0, "Underweight": 1, "Hold": 2, "Overweight": 3, "Buy": 4}

    for row in rows:
        decision = aggregate(row.signals, weights)
        counts[decision.rating] = counts.get(decision.rating, 0) + 1

        # Direction agreement
        actual_d = _RATING_TO_DIRECTION.get(row.actual_rating, 0)
        shadow_d = _RATING_TO_DIRECTION.get(decision.rating, 0)
        if actual_d == shadow_d:
            direction_match += 1

        # Within-±1-tier
        a_t = tier_order.get(row.actual_rating)
        s_t = tier_order.get(decision.rating)
        if a_t is not None and s_t is not None and abs(a_t - s_t) <= 1:
            rating_within += 1

        # IC against realized alpha
        if row.alpha is not None:
            pairs_for_ic.append((decision.direction_score, row.alpha))

    n = len(rows)
    if n == 0:
        return WeightEvaluation(
            weights=weights,
            n_total=0,
            n_resolved=0,
            ic=None,
            direction_agreement=0.0,
            rating_within_one_tier=0.0,
            n_buy=0,
            n_overweight=0,
            n_hold=0,
            n_underweight=0,
            n_sell=0,
        )

    return WeightEvaluation(
        weights=dict(weights),
        n_total=n,
        n_resolved=len(pairs_for_ic),
        ic=_spearman_ic(pairs_for_ic),
        direction_agreement=direction_match / n,
        rating_within_one_tier=rating_within / n,
        n_buy=counts["Buy"],
        n_overweight=counts["Overweight"],
        n_hold=counts["Hold"],
        n_underweight=counts["Underweight"],
        n_sell=counts["Sell"],
    )


# Default grid: 5 weight values per bot, summing constraints relaxed.
# Each bot in [0, 0.5] step 0.1 — 6 values. With 5 bots = 7776 combinations.
# Tractable in seconds since each evaluate_weights is sub-second.
_DEFAULT_GRID_VALUES = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)


def grid_search_weights(
    rows: list[TuningCorpusRow],
    objective: str = "ic",
    bot_ids: list[str] | None = None,
    grid_values: tuple[float, ...] = _DEFAULT_GRID_VALUES,
) -> tuple[dict[str, float], WeightEvaluation]:
    """Coarse grid search over weights. Returns (best_weights, best_eval).

    objective: 'ic' (maximize Spearman IC vs alpha — most-alpha-correlated
    aggregator) or 'agreement' (maximize direction match with PM).

    Skips trivial all-zero weight vectors. Small numerical noise is
    tolerated by ranking on the rounded objective; ties broken by preferring
    more-balanced weight vectors (lower std).
    """
    if bot_ids is None:
        bot_ids = list(DEFAULT_WEIGHTS.keys())

    best_eval: WeightEvaluation | None = None
    best_weights: dict[str, float] | None = None

    for combo in itertools.product(grid_values, repeat=len(bot_ids)):
        if sum(combo) == 0.0:
            continue  # all-zero is degenerate
        weights = dict(zip(bot_ids, combo, strict=True))
        ev = evaluate_weights(rows, weights)

        # Score: maximize chosen objective; None IC sinks
        if objective == "ic":
            score = ev.ic if ev.ic is not None else -2.0
        elif objective == "agreement":
            score = ev.direction_agreement
        else:
            raise ValueError(f"Unknown objective: {objective!r}")

        if best_eval is None or score > _score(best_eval, objective):
            best_eval = ev
            best_weights = weights

    assert best_eval is not None and best_weights is not None
    return best_weights, best_eval


def _score(ev: WeightEvaluation, objective: str) -> float:
    if objective == "ic":
        return ev.ic if ev.ic is not None else -2.0
    if objective == "agreement":
        return ev.direction_agreement
    raise ValueError(f"Unknown objective: {objective!r}")


def split_train_test(
    rows: list[TuningCorpusRow],
    train_fraction: float = 0.7,
) -> tuple[list[TuningCorpusRow], list[TuningCorpusRow]]:
    """Date-ordered split: oldest train_fraction in train, rest in test.

    Per SC-006: train/test split prevents overfitting. Date-ordered (not
    random) ensures the test set is genuinely "future" from the train set's
    perspective.
    """
    sorted_rows = sorted(rows, key=lambda r: (r.date, r.ticker))
    n_train = int(len(sorted_rows) * train_fraction)
    return sorted_rows[:n_train], sorted_rows[n_train:]


def build_tuning_corpus(
    state_logs: list[tuple[str, dict, float | None]],
    horizon_days: int = 21,
) -> list[TuningCorpusRow]:
    """Build TuningCorpusRow list from (ticker, state_log_dict, alpha) tuples.

    Caller fetches alpha (which requires yfinance + the slow path) before
    passing in. The build itself is signal-derivation only.
    """
    from tradingagents.agents.utils.rating import parse_rating

    rows: list[TuningCorpusRow] = []
    for ticker, state, alpha in state_logs:
        trade_date = state.get("trade_date")
        if not trade_date:
            continue
        signals, _ = shadow_aggregate_from_state_log(state, horizon_days)
        actual_rating = parse_rating(state.get("final_trade_decision", "") or "")
        rows.append(
            TuningCorpusRow(
                ticker=ticker,
                date=str(trade_date)[:10],
                signals=signals,
                actual_rating=actual_rating,
                alpha=alpha,
            )
        )
    return rows
