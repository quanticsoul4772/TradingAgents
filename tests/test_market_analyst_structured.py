"""Tests for the BR-3 Squeak structured market analyst.

Per `experiments/2026-05-09-001-br3-squeak-market-analyst/HYPOTHESIS.md`.

Tests cover:
1. Pydantic schema validation (bullish_score range, list lengths)
2. Markdown rendering (compact table + bullets)
3. Module import + node creation (no LLM calls)
4. Config flag default ("prose" — backward compat)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tradingagents.agents.schemas import (
    MarketAnalystSquared,
    render_market_analyst_squared,
)

pytestmark = pytest.mark.unit


# ---- Schema validation ---------------------------------------------------


def test_squared_basic_construction():
    s = MarketAnalystSquared(bullish_score=0.5, confidence=0.8)
    assert s.bullish_score == 0.5
    assert s.confidence == 0.8
    assert s.key_drivers == []
    assert s.key_risks == []
    assert s.citations == []


def test_squared_with_drivers_and_risks():
    s = MarketAnalystSquared(
        bullish_score=-0.4,
        confidence=0.6,
        key_drivers=["RSI 38", "Sector +5%"],
        key_risks=["VIX > 25"],
        citations=["get_indicators rsi=38"],
    )
    assert len(s.key_drivers) == 2
    assert len(s.key_risks) == 1
    assert len(s.citations) == 1


def test_squared_bullish_score_clamped_to_range():
    with pytest.raises(ValidationError):
        MarketAnalystSquared(bullish_score=1.5, confidence=0.5)
    with pytest.raises(ValidationError):
        MarketAnalystSquared(bullish_score=-1.5, confidence=0.5)


def test_squared_confidence_clamped_to_unit_range():
    with pytest.raises(ValidationError):
        MarketAnalystSquared(bullish_score=0.0, confidence=1.5)
    with pytest.raises(ValidationError):
        MarketAnalystSquared(bullish_score=0.0, confidence=-0.1)


def test_squared_drivers_max_length():
    with pytest.raises(ValidationError):
        MarketAnalystSquared(
            bullish_score=0.0, confidence=0.5, key_drivers=["a", "b", "c", "d", "e", "f"]
        )


def test_squared_risks_max_length():
    with pytest.raises(ValidationError):
        MarketAnalystSquared(
            bullish_score=0.0, confidence=0.5, key_risks=["a", "b", "c", "d", "e", "f"]
        )


def test_squared_citations_max_length():
    with pytest.raises(ValidationError):
        MarketAnalystSquared(
            bullish_score=0.0,
            confidence=0.5,
            citations=[str(i) for i in range(11)],
        )


def test_squared_boundary_values_accepted():
    # ±1.0 and 0.0/1.0 endpoints should be accepted (inclusive bounds)
    s_max_bull = MarketAnalystSquared(bullish_score=1.0, confidence=1.0)
    assert s_max_bull.bullish_score == 1.0
    s_max_bear = MarketAnalystSquared(bullish_score=-1.0, confidence=0.0)
    assert s_max_bear.bullish_score == -1.0


# ---- Rendering -----------------------------------------------------------


def test_render_basic_includes_score_and_confidence():
    s = MarketAnalystSquared(bullish_score=0.62, confidence=0.85)
    out = render_market_analyst_squared(s)
    assert "Market Analyst (structured) report" in out
    assert "+0.620" in out
    assert "0.85" in out


def test_render_includes_drivers_when_present():
    s = MarketAnalystSquared(
        bullish_score=0.5,
        confidence=0.7,
        key_drivers=["RSI 38 (oversold)", "Golden cross"],
    )
    out = render_market_analyst_squared(s)
    assert "Key drivers" in out
    assert "RSI 38" in out
    assert "Golden cross" in out


def test_render_includes_risks_when_present():
    s = MarketAnalystSquared(
        bullish_score=-0.3,
        confidence=0.6,
        key_risks=["VIX > 25"],
    )
    out = render_market_analyst_squared(s)
    assert "Key risks" in out
    assert "VIX > 25" in out


def test_render_omits_empty_sections():
    s = MarketAnalystSquared(bullish_score=0.0, confidence=0.5)
    out = render_market_analyst_squared(s)
    assert "Key drivers" not in out
    assert "Key risks" not in out
    assert "Tool citations" not in out


def test_render_signed_score_format():
    s_pos = MarketAnalystSquared(bullish_score=0.6, confidence=0.5)
    s_neg = MarketAnalystSquared(bullish_score=-0.6, confidence=0.5)
    assert "+0.600" in render_market_analyst_squared(s_pos)
    assert "-0.600" in render_market_analyst_squared(s_neg)


# ---- Module import + factory creation (no LLM) ---------------------------


def test_create_market_analyst_structured_callable():
    from tradingagents.agents.analysts.market_analyst_structured import (
        create_market_analyst_structured,
    )

    # We pass None as llm — the factory just returns a closure;
    # llm is only invoked when the node is called with state, which
    # we don't do here (would require live LLM).
    node = create_market_analyst_structured(llm=None)
    assert callable(node)


# ---- Config default -----------------------------------------------------


def test_default_config_market_analyst_format_is_prose():
    """Backward compat: default unchanged from existing prose behavior."""
    from tradingagents.default_config import DEFAULT_CONFIG

    assert DEFAULT_CONFIG["market_analyst_format"] == "prose"
