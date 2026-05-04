"""Spec 001 Phase 1 — Signal schema + deterministic aggregator (shadow mode).

Phase 1 implements the foundational pieces of the bots-architecture refactor:

- ``Signal`` Pydantic schema — per-analyst structured output (bot_id,
  direction, magnitude, horizon_days, key_facts, risks, abstain).
- ``derive_signal_from_prose(bot_id, prose)`` — produces a Signal from an
  analyst's prose report by featurizing it with the Phase 1.5+ featurizers.
  Zero new LLM cost. Re-uses the cache + featurization infrastructure.
- ``aggregate(signals, weights)`` — deterministic weighted sum producing
  an ``AggregatedDecision`` (rating, confidence, direction_score, bots_used).
  Same Signal inputs always yield same rating output (FR-010).
- ``shadow_aggregate_from_state_log(state)`` — convenience wrapper that
  derives Signals from a state log's analyst reports and returns the
  aggregate decision. Used to backfill shadow-aggregate data over the
  existing corpus without new propagates (Phase 1 acceptance test).

Phase 1 is non-breaking (FR-004): the shadow aggregator runs alongside the
existing prose pipeline, never modifies production decisions. Phase 2 will
add the opt-in ``framework_mode = "bots"`` flag that routes the actual
final_trade_decision through the aggregator.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from tradingagents.signals.featurization import (
    bear_bigram_count,
    bear_keyword_count,
    bull_bigram_count,
    bull_keyword_count,
    conviction_density,
    hedge_density,
    sentiment_score,
)

# -- Signal schema ----------------------------------------------------------


class Signal(BaseModel):
    """Per-analyst structured output. Bridges 'LLM analyst' → 'deterministic
    aggregator'. Per spec 001 FR-001 / FR-009.
    """

    bot_id: str = Field(description="Analyst id: 'market', 'news', 'fundamentals', etc.")
    direction: float = Field(
        ge=-1.0,
        le=1.0,
        description="Bull/bear stance: -1 = max bearish, 0 = neutral, +1 = max bullish.",
    )
    magnitude: float = Field(
        ge=0.0,
        le=1.0,
        description="Conviction strength: 0 = abstain, 1 = max conviction.",
    )
    horizon_days: int = Field(default=21, description="Target prediction horizon.")
    key_facts: list[str] = Field(
        default_factory=list,
        description="Optional 1-3 evidence bullets supporting the direction.",
    )
    risks: list[str] = Field(
        default_factory=list,
        description="Optional 1-3 evidence bullets that contradict the direction.",
    )
    abstain: bool = Field(
        default=False,
        description="True when the analyst lacks usable evidence; aggregator weights at 0.",
    )


@dataclass
class AggregatedDecision:
    """Output of ``aggregate(signals)``. Per spec 001 Key Entities."""

    rating: str  # 5-tier: Buy / Overweight / Hold / Underweight / Sell
    confidence: float  # 0-1: combined magnitude × direction-coherence
    direction_score: float  # raw weighted-sum direction in [-1, +1]
    bots_used: list[str] = field(default_factory=list)
    abstained: list[str] = field(default_factory=list)


# -- Default per-bot weights ------------------------------------------------
#
# Per spec 001 §Assumptions: "Initial WEIGHTS (market 0.25, news 0.20,
# fundamentals 0.30, sentiment 0.10, debate 0.075 each) are placeholders;
# Phase 5 will tune."
#
# debate weights aren't used in Phase 1 (no debate-bot integration yet).
# Sentiment weight is 0.10 even though most experiments don't run the social
# analyst — when sentiment_report is missing, that weight is excluded.

DEFAULT_WEIGHTS: dict[str, float] = {
    "market_report": 0.25,
    "news_report": 0.20,
    "fundamentals_report": 0.30,
    "sentiment_report": 0.10,
    "investment_plan": 0.15,  # research-manager synthesis as a meta-bot
}


# -- Featurization-based Signal derivation ----------------------------------
#
# Phase 1 derives Signals from analyst prose (no new LLM calls). Direction
# combines unigram sentiment + bigram-count delta; magnitude scales with
# total signal density (more evidence → higher conviction).


def derive_signal_from_prose(bot_id: str, prose: str, horizon_days: int = 21) -> Signal:
    """Featurize an analyst's prose report into a Signal.

    Direction = sentiment_score blended with bigram-delta polarity.
      - sentiment_score (unigram) provides the base.
      - bull_bigram_count vs bear_bigram_count provides corroborating polarity
        — when bigrams agree with unigrams, the signal is stronger.

    Magnitude = total evidence density (sum of conviction + hedge + bigram
    + bull/bear keyword counts) clipped to [0, 1]. Reports with very little
    sentiment-bearing content abstain.

    Abstain = True when prose is effectively empty (< 50 chars) or has zero
    sentiment-bearing words.
    """
    if not prose or len(prose) < 50:
        return Signal(
            bot_id=bot_id,
            direction=0.0,
            magnitude=0.0,
            horizon_days=horizon_days,
            abstain=True,
        )

    # Polarity: combine unigram sentiment with bigram delta
    unigram_sent = sentiment_score(prose)  # [-1, +1]
    bull_bigram = bull_bigram_count(prose)
    bear_bigram = bear_bigram_count(prose)
    bigram_total = bull_bigram + bear_bigram
    if bigram_total > 0:
        bigram_polarity = (bull_bigram - bear_bigram) / bigram_total
    else:
        bigram_polarity = 0.0

    # Weighted blend: 70% unigram, 30% bigram (bigrams are sparser but
    # carry richer signal per occurrence)
    direction = 0.7 * unigram_sent + 0.3 * bigram_polarity
    direction = max(-1.0, min(1.0, direction))  # clip to [-1, +1]

    # Magnitude: density of sentiment + conviction evidence
    bull = bull_keyword_count(prose)
    bear = bear_keyword_count(prose)
    conv = conviction_density(prose)  # already per-1000-chars density
    hedg = hedge_density(prose)  # already per-1000-chars density
    # Heuristic: combine evidence counts (normalized) with conviction density
    # and a modest penalty for excessive hedging.
    keyword_density = (bull + bear + bigram_total) / max(1, len(prose) / 1000.0)
    magnitude = (
        0.4 * min(1.0, keyword_density / 20.0)  # cap density contribution at 20 kwds/1000ch
        + 0.5 * min(1.0, conv / 30.0)  # cap conviction at 30 per 1000 chars
        - 0.2 * min(1.0, hedg / 30.0)  # hedging slightly reduces magnitude
    )
    magnitude = max(0.0, min(1.0, magnitude))

    # Abstain when there's no detectable signal
    abstain = bull + bear + bigram_total == 0 or magnitude < 0.05

    return Signal(
        bot_id=bot_id,
        direction=direction,
        magnitude=magnitude,
        horizon_days=horizon_days,
        abstain=abstain,
    )


# -- Aggregator -------------------------------------------------------------


def aggregate(
    signals: list[Signal],
    weights: dict[str, float] | None = None,
) -> AggregatedDecision:
    """Deterministic weighted-sum aggregator. Same inputs → same output (FR-010).

    Computes:
      direction_score = Σ(w_i × signal_i.direction × signal_i.magnitude)
                         / Σ(w_i × signal_i.magnitude)
      confidence      = Σ(w_i × signal_i.magnitude) / Σ(w_i over non-abstaining)
      rating          = 5-tier mapping of direction_score:
                          > +0.6 → Buy
                          > +0.2 → Overweight
                          [-0.2, +0.2] → Hold
                          < -0.2 → Underweight
                          < -0.6 → Sell

    Signals with ``abstain=True`` contribute 0 weight. If all signals
    abstain or magnitude=0 across the board, returns Hold with confidence=0.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    weighted_sum_dir = 0.0  # Σ w × dir × mag
    weighted_sum_mag = 0.0  # Σ w × mag (denominator for direction_score)
    total_weight_non_abstain = 0.0  # Σ w over non-abstaining bots
    bots_used: list[str] = []
    abstained: list[str] = []

    for sig in signals:
        w = weights.get(sig.bot_id, 0.0)
        if sig.abstain or sig.magnitude == 0.0:
            abstained.append(sig.bot_id)
            continue
        weighted_sum_dir += w * sig.direction * sig.magnitude
        weighted_sum_mag += w * sig.magnitude
        total_weight_non_abstain += w
        bots_used.append(sig.bot_id)

    if weighted_sum_mag == 0.0 or total_weight_non_abstain == 0.0:
        return AggregatedDecision(
            rating="Hold",
            confidence=0.0,
            direction_score=0.0,
            bots_used=bots_used,
            abstained=abstained,
        )

    direction_score = weighted_sum_dir / weighted_sum_mag
    # Confidence: average magnitude across non-abstaining bots, weighted
    confidence = weighted_sum_mag / total_weight_non_abstain
    confidence = max(0.0, min(1.0, confidence))

    rating = _direction_to_rating(direction_score)

    return AggregatedDecision(
        rating=rating,
        confidence=confidence,
        direction_score=direction_score,
        bots_used=bots_used,
        abstained=abstained,
    )


def _direction_to_rating(direction_score: float) -> str:
    """Map continuous direction_score in [-1, +1] to 5-tier rating."""
    if direction_score > 0.6:
        return "Buy"
    if direction_score > 0.2:
        return "Overweight"
    if direction_score < -0.6:
        return "Sell"
    if direction_score < -0.2:
        return "Underweight"
    return "Hold"


# -- Shadow aggregation from state logs -------------------------------------


# Mapping of state-log field name → bot_id used in the Signal + DEFAULT_WEIGHTS.
_STATE_LOG_FIELDS_TO_BOT_ID = {
    "market_report": "market_report",
    "news_report": "news_report",
    "fundamentals_report": "fundamentals_report",
    "sentiment_report": "sentiment_report",
    "investment_plan": "investment_plan",
}


def render_aggregated_decision_markdown(
    decision: AggregatedDecision,
    signals: list[Signal],
    ticker: str,
    trade_date: str,
) -> str:
    """Render an AggregatedDecision into the markdown shape that downstream
    code (parse_rating, memory log, state log readers) expects.

    Used by Phase 2 (bots mode) to replace the LLM-produced
    final_trade_decision when ``config["framework_mode"] = "bots"``.
    The Rating: line is the load-bearing parseable token; the rest is
    audit-trail prose.
    """
    used = ", ".join(decision.bots_used) if decision.bots_used else "(none — all abstained)"
    abstained = ", ".join(decision.abstained) if decision.abstained else "(none)"

    sig_lines = []
    for s in signals:
        sig_lines.append(
            f"  - `{s.bot_id}`: direction={s.direction:+.2f}, "
            f"magnitude={s.magnitude:.2f}, abstain={s.abstain}"
        )
    sig_block = "\n".join(sig_lines) if sig_lines else "  - (no signals derived)"

    return f"""**Rating: {decision.rating}**

**Decision source**: deterministic aggregator (spec 001 Phase 2 bots mode)
**Ticker**: {ticker}
**Trade date**: {trade_date}

## Aggregator output

- **Direction score**: {decision.direction_score:+.3f} (range [-1, +1])
- **Confidence**: {decision.confidence:.3f} (range [0, 1])
- **Bots used (non-abstaining)**: {used}
- **Bots abstained**: {abstained}

## Per-bot signals

{sig_block}

## Notes

- This decision was produced by ``tradingagents.signals.bots.aggregate``,
  not by the LLM-based PortfolioManager. The aggregator is deterministic
  and reproducible from the analyst-prose state log.
- Set ``config["framework_mode"] = "prose"`` (or unset) to revert to the
  LLM-based PM pipeline.
"""


def shadow_aggregate_from_state_log(
    state: dict,
    horizon_days: int = 21,
    weights: dict[str, float] | None = None,
) -> tuple[list[Signal], AggregatedDecision]:
    """Derive Signals from a state log dict and run the aggregator.

    Returns (signals, aggregated_decision). Skips fields that are missing
    or non-string (e.g., investment_debate_state is a nested dict, not used
    here — its synthesis is captured in investment_plan).
    """
    signals: list[Signal] = []
    for field_name, bot_id in _STATE_LOG_FIELDS_TO_BOT_ID.items():
        prose = state.get(field_name)
        if not prose or not isinstance(prose, str):
            continue
        signals.append(derive_signal_from_prose(bot_id, prose, horizon_days))

    decision = aggregate(signals, weights)
    return signals, decision
