"""Spec 008.5 SC-012 latency benchmark — closes the /speckit.analyze coverage gap.

Verifies the SC-012 latency budget for `tradingagents.agents.utils.calendar_boost`:
  - Cache-cold: dominated by yfinance HTTP; not deterministic-testable in CI.
    Documented for operator validation; skipped here.
  - Cache-warm: ≤ 5 ms p99 on the in-memory LRU lookup + boost arithmetic.
    Asserted via wall-clock timing of 100 iterations (mocked yfinance).

Marked `unit` so it runs in the default pytest-fast hook. Per-iteration cost
on a typical dev machine is ~5-50 µs, well under the 5 ms p99 budget.
"""

from __future__ import annotations

import time
from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from tradingagents.agents.utils.calendar_boost import (
    _fetch_earnings_dates,
    apply_calendar_boost,
    calendar_boost,
    days_to_next_earnings,
)

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _clear_lru_cache():
    _fetch_earnings_dates.cache_clear()
    yield
    _fetch_earnings_dates.cache_clear()


def _earnings_df(dates: list[datetime]) -> pd.DataFrame:
    if not dates:
        return pd.DataFrame()
    idx = pd.DatetimeIndex(dates).tz_localize("US/Eastern")
    return pd.DataFrame({"EPS Estimate": [None] * len(dates)}, index=idx)


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_cache_warm_latency_under_5ms_p99(mock_ticker):
    """SC-012 cache-warm: ≤ 5 ms p99 over 100 iterations after first warm-up call.

    Measures days_to_next_earnings + calendar_boost + apply_calendar_boost as
    a unit (the operational call sequence per Spec 008 integration). First
    iteration warms the LRU cache; remaining 100 hit cache.
    """
    mock_ticker.return_value.earnings_dates = _earnings_df([datetime(2026, 5, 13)])

    # Warm-up call (this is "cold" — not measured)
    days_to_next_earnings("NVDA", "2026-05-06")

    iterations = 100
    samples_ms: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        days = days_to_next_earnings("NVDA", "2026-05-06")
        boost = calendar_boost(days, window=14)
        _ = apply_calendar_boost(0.50, days, window=14, magnitude=0.5)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        samples_ms.append(elapsed_ms)
        # confirm boost branch executed (compiler-fence, also avoids unused-var warnings)
        assert 0.0 <= boost <= 1.0

    samples_ms.sort()
    p99_idx = int(0.99 * len(samples_ms))
    p99_ms = samples_ms[p99_idx]

    # Per SC-012: cache-warm budget is 5 ms p99
    assert p99_ms < 5.0, (
        f"Cache-warm latency p99 = {p99_ms:.3f} ms exceeds SC-012 budget of 5 ms. "
        f"Samples (sorted, ms): min={samples_ms[0]:.3f}, "
        f"p50={samples_ms[50]:.3f}, p99={p99_ms:.3f}, max={samples_ms[-1]:.3f}"
    )

    # yfinance.Ticker should be invoked exactly once (warm-up); 100 cache hits
    assert mock_ticker.call_count == 1, (
        f"Cache miss during warm path: yfinance.Ticker called {mock_ticker.call_count} times "
        f"(expected 1 for warm-up only)"
    )


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_cache_warm_arithmetic_only_under_1ms(mock_ticker):
    """Tighter assertion: just the boost arithmetic (no LRU lookup) under 1 ms.

    Isolates the apply_calendar_boost + calendar_boost cost from the
    days_to_next_earnings cache lookup — confirms the math is essentially free.
    """
    iterations = 1000
    t0 = time.perf_counter()
    for _ in range(iterations):
        boost = calendar_boost(7, window=14)
        _ = apply_calendar_boost(0.50, 7, window=14, magnitude=0.5)
        assert 0.0 <= boost <= 1.0
    elapsed_total_ms = (time.perf_counter() - t0) * 1000
    per_call_us = elapsed_total_ms * 1000 / iterations

    # Pure arithmetic: < 100 µs per call is generous; typically <10 µs
    assert per_call_us < 100, (
        f"Boost arithmetic per-call cost = {per_call_us:.1f} µs exceeds 100 µs ceiling. "
        f"Total elapsed = {elapsed_total_ms:.2f} ms over {iterations} iterations."
    )

    # No yfinance call should have happened — pure arithmetic test
    assert mock_ticker.call_count == 0


# Note: cache-COLD latency (≤250 ms p99 per SC-012) is dominated by yfinance
# HTTP round-trip and is not deterministic-testable in CI without network.
# Operators validate via the smoke script: scripts/smoke_spec_008.py reports
# wall-clock for the first per-process yfinance.earnings_dates fetch. Typical
# residential broadband hits 100-300 ms; the SC-012 ≤250 ms p99 budget is the
# operational expectation, not a unit-test assertion.
