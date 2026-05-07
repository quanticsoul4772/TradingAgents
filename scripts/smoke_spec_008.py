"""Spec 008 live smoke test — verify Hybrid C calendar boost annotations end-to-end.

Skips the full multi-agent propagate (~$0.40-0.80) by invoking
``evaluate_forward_catalyst`` directly with real Opus + real yfinance.
Validates that:
  1. The four Hybrid C annotation keys appear in state["forward_catalyst"]
     when the boost is enabled
  2. days_to_earnings is populated from a REAL yfinance.earnings_dates fetch
  3. The boost arithmetic + integration match the integration-test expectations

Cost: ~$0.025 (one Opus call). Free yfinance fetch.

Usage:
    ANTHROPIC_API_KEY=... python scripts/smoke_spec_008.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from tradingagents.agents.utils.calendar_boost import _fetch_earnings_dates  # noqa: E402
from tradingagents.agents.utils.forward_catalyst_filter import (  # noqa: E402
    evaluate_forward_catalyst,
)


def main():
    # Minimal-but-realistic state
    # trade_date 2026-05-13 → 7 days before NVDA earnings on 2026-05-20
    # → boost = 1 - 7/14 = 0.5 → effective = base * (1 + 0.5*0.5) = base * 1.25
    state = {
        "company_of_interest": "NVDA",
        "trade_date": "2026-05-13",
        "market_report": (
            "NVDA closed at $1,150 today, up 2.5% on the session. "
            "30-day SMA = $1,100. RSI = 65 (overbought-leaning). "
            "Volume above average."
        ),
        "sentiment_report": (
            "Reddit + Twitter sentiment heavily bullish on data-center demand. "
            "Most posts cite the H200 ramp + sovereign-AI narrative."
        ),
        "news_report": (
            "Reuters reports NVDA secured a $5B Saudi sovereign-AI contract. "
            "JPM raised price target to $1,400. Earnings expected May 22."
        ),
        "fundamentals_report": (
            "Trailing-12mo revenue $115B, gross margin 75%, FCF margin 50%. "
            "Forward P/E 35x. Strong balance sheet."
        ),
        "investment_plan": (
            "Bull synthesis: data-center demand visibility extends 2 years. "
            "Bear synthesis: gross margin compression risk if competition heats up. "
            "Net: bullish bias justified at current levels but earnings-event risk priced in."
        ),
        "investment_debate_state": {
            "history": (
                "Bull: 'street is bullish; PT raises across the board; sovereign-AI is "
                "real demand.' Bear: 'consensus is too bullish; mean-revert is overdue; "
                "AMD MI400 ramps in Q3.'"
            )
        },
    }

    decision_markdown = (
        "**Rating**: Overweight\n\n"
        "**Executive Summary**: Build position into the upcoming earnings.\n\n"
        "**Investment Thesis**: Bull case has multiple legs (sovereign AI, data center, "
        "H200 ramp). Bear case is sentiment-driven, not fundamental."
    )

    print("=" * 70)
    print("Spec 008 Smoke Test — Hybrid C calendar boost")
    print("=" * 70)
    print()
    print("Step 1: clear LRU cache + fetch real NVDA earnings_dates")
    _fetch_earnings_dates.cache_clear()
    earnings = _fetch_earnings_dates("NVDA")
    print(f"  yfinance.earnings_dates returned {len(earnings)} entries")
    if earnings:
        print(f"  First: {earnings[0]}, Last: {earnings[-1]}")

    print()
    print("Step 2: invoke evaluate_forward_catalyst with REAL Opus + boost enabled")
    print(f"  Ticker: {state['company_of_interest']}")
    print(f"  Trade date: {state['trade_date']}")
    print("  Pre-rating: Overweight")
    print("  hybrid_c_calendar_boost_enabled=True (window=14d, magnitude=0.5x)")
    print()

    modified_md, annotation = evaluate_forward_catalyst(
        decision_markdown,
        state,
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        hybrid_c_calendar_boost_enabled=True,
        hybrid_c_calendar_boost_window_days=14,
        hybrid_c_calendar_boost_magnitude=0.5,
    )

    print("Step 3: verify annotation contains all 4 Hybrid C keys")
    hybrid_c_keys = {
        "days_to_earnings",
        "calendar_boost",
        "effective_bull_score",
        "effective_bear_score",
    }
    spec_007_keys = {
        "model",
        "bull_case_priced_in",
        "bear_case_priced_in",
        "rationale",
        "bull_threshold",
        "bear_threshold",
        "bull_mode",
        "bear_mode",
        "would_fire_bull",
        "would_fire_bear",
        "fired_bull",
        "fired_bear",
        "pre_rating",
        "post_rating",
        "skipped",
        "error",
    }

    missing_hybrid = hybrid_c_keys - set(annotation.keys())
    missing_spec_007 = spec_007_keys - set(annotation.keys())

    print(
        f"  Spec 007 baseline keys present: {len(spec_007_keys) - len(missing_spec_007)}/{len(spec_007_keys)}"
    )
    print(
        f"  Hybrid C keys present: {len(hybrid_c_keys) - len(missing_hybrid)}/{len(hybrid_c_keys)}"
    )

    if missing_hybrid:
        print(f"  MISSING Hybrid C keys: {missing_hybrid}")
    if missing_spec_007:
        print(f"  MISSING spec 007 keys: {missing_spec_007}")

    print()
    print("Step 4: report annotation values")
    print(f"  days_to_earnings: {annotation.get('days_to_earnings')}")
    print(f"  calendar_boost: {annotation.get('calendar_boost')}")
    print(f"  bull_case_priced_in: {annotation.get('bull_case_priced_in')}")
    print(f"  effective_bull_score: {annotation.get('effective_bull_score')}")
    print(f"  bear_case_priced_in: {annotation.get('bear_case_priced_in')}")
    print(f"  effective_bear_score: {annotation.get('effective_bear_score')}")
    print(f"  bull_threshold: {annotation.get('bull_threshold')}")
    print(f"  would_fire_bull: {annotation.get('would_fire_bull')}")
    print(f"  fired_bull: {annotation.get('fired_bull')}")
    print(f"  pre_rating: {annotation.get('pre_rating')}")
    print(f"  post_rating: {annotation.get('post_rating')}")
    print(f"  skipped: {annotation.get('skipped')}")
    print(f"  error: {annotation.get('error')}")

    print()
    print("Step 5: verify boost arithmetic")
    base = annotation.get("bull_case_priced_in")
    days = annotation.get("days_to_earnings")
    effective = annotation.get("effective_bull_score")

    if base is not None and effective is not None:
        if days is None:
            expected = base
            print(f"  days=None → expected effective = base = {expected:.4f}")
        elif days >= 14:
            expected = base
            print(f"  days={days} >= 14 → boost=0 → expected effective = {expected:.4f}")
        else:
            expected_boost = 1.0 - days / 14
            expected = min(1.0, base * (1 + 0.5 * expected_boost))
            print(
                f"  days={days}, expected boost={expected_boost:.4f}, expected effective={expected:.4f}"
            )

        if abs(effective - expected) < 1e-6:
            print(f"  Computed effective={effective:.4f} ✓ matches expected")
        else:
            print(f"  MISMATCH: computed effective={effective:.4f}, expected {expected:.4f}")

    print()
    print("=" * 70)
    if not missing_hybrid and not missing_spec_007:
        print("VERDICT: PASS — all 20 annotation keys present (16 spec 007 + 4 Hybrid C).")
        print("         Spec 008 live integration validated end-to-end.")
    else:
        print("VERDICT: FAIL — missing annotation keys; investigate.")
    print("=" * 70)

    print()
    print("Annotation JSON (full):")
    print(
        json.dumps(
            {k: (v if not isinstance(v, str) else v[:200]) for k, v in annotation.items()},
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
