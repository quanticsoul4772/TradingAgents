"""Unit tests for tradingagents/agents/utils/forward_catalyst_filter.py.

Spec: specs/006-forward-catalyst-gate/contracts/filter_function.md +
      specs/006-forward-catalyst-gate/contracts/annotation_schema.md

Mocks the LLM client so tests are fast and deterministic.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tradingagents.agents.utils.forward_catalyst_filter import (
    CasePricedInScore,
    evaluate_forward_catalyst,
)


def _state(
    market: str = "market report",
    sentiment: str = "sentiment report",
    news: str = "news report",
    fundamentals: str = "fundamentals report",
    investment_plan: str = "research plan",
    debate: str = "bull/bear debate history",
    ticker: str = "NVDA",
    trade_date: str = "2026-04-03",
) -> dict:
    return {
        "company_of_interest": ticker,
        "trade_date": trade_date,
        "market_report": market,
        "sentiment_report": sentiment,
        "news_report": news,
        "fundamentals_report": fundamentals,
        "investment_plan": investment_plan,
        "investment_debate_state": {"history": debate},
    }


def _make_llm(bull: float, bear: float, rationale: str = "test rationale"):
    """Build a mocked LLM that returns a CasePricedInScore via with_structured_output."""
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = CasePricedInScore(
        bull_case_priced_in=bull, bear_case_priced_in=bear, rationale=rationale
    )
    llm.with_structured_output.return_value = structured
    return llm


def _make_failing_llm(exc: Exception):
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.side_effect = exc
    llm.with_structured_output.return_value = structured
    return llm


# -- Both-modes-off + threshold-validation paths -----------------------------


@pytest.mark.unit
def test_both_modes_off_skips_llm_call_zero_cost():
    """When both modes off, filter must NOT call the LLM (FR-009 / SC-006)."""
    md = "**Rating**: Overweight"
    llm = MagicMock()
    out_md, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="off",
        bear_mode="off",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert out_md == md
    assert ann["skipped"] == "off"
    assert ann["bull_mode"] == "off"
    assert ann["bear_mode"] == "off"
    assert ann["fired_bull"] is False
    assert ann["fired_bear"] is False
    # Critical: LLM was never invoked
    llm.with_structured_output.assert_not_called()


@pytest.mark.unit
def test_bull_threshold_invalid_warns_and_skips_bull(caplog):
    """Out-of-range bull threshold -> bull side disabled; bear continues."""
    md = "**Rating**: Underweight"
    llm = _make_llm(bull=0.78, bear=0.45)
    with caplog.at_level("WARNING"):
        _, ann = evaluate_forward_catalyst(
            md,
            _state(),
            bull_mode="active",
            bear_mode="active",
            bull_threshold=1.5,  # invalid
            bear_threshold=0.50,
            model="claude-opus-4-7",
            llm=llm,
        )
    assert ann["bull_mode"] == "off"  # disabled by validation
    assert ann["bull_threshold"] is None
    assert any("bull_threshold" in m for m in caplog.messages)


@pytest.mark.unit
def test_bear_threshold_invalid_warns_and_skips_bear(caplog):
    """Out-of-range bear threshold -> bear side disabled; bull continues."""
    md = "**Rating**: Overweight"
    llm = _make_llm(bull=0.78, bear=0.45)
    with caplog.at_level("WARNING"):
        _, ann = evaluate_forward_catalyst(
            md,
            _state(),
            bull_mode="active",
            bear_mode="active",
            bull_threshold=0.60,
            bear_threshold=-0.5,  # invalid
            model="claude-opus-4-7",
            llm=llm,
        )
    assert ann["bear_mode"] == "off"
    assert ann["bear_threshold"] is None
    assert any("bear_threshold" in m for m in caplog.messages)


@pytest.mark.unit
def test_both_thresholds_invalid_skipped_invalid_threshold():
    """Both thresholds invalid -> skipped='invalid_threshold' + no LLM call."""
    md = "**Rating**: Overweight"
    llm = MagicMock()
    _, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="active",
        bull_threshold=2.0,
        bear_threshold=-1.0,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["skipped"] == "invalid_threshold"
    assert ann["fired_bull"] is False
    assert ann["fired_bear"] is False
    llm.with_structured_output.assert_not_called()


# -- LLM-failure paths -------------------------------------------------------


@pytest.mark.unit
def test_llm_call_failure_skipped_with_error(caplog):
    """LLM exception -> skipped='llm_failed' + error populated + rating unchanged."""
    md = "**Rating**: Overweight"
    llm = _make_failing_llm(RuntimeError("network down"))
    with caplog.at_level("WARNING"):
        out_md, ann = evaluate_forward_catalyst(
            md,
            _state(),
            bull_mode="active",
            bear_mode="shadow",
            bull_threshold=0.60,
            bear_threshold=0.50,
            model="claude-opus-4-7",
            llm=llm,
        )
    assert out_md == md
    assert ann["skipped"] == "llm_failed"
    assert ann["error"] is not None
    assert "network down" in ann["error"]
    assert ann["bull_case_priced_in"] is None
    assert ann["bear_case_priced_in"] is None
    assert ann["fired_bull"] is False
    assert ann["fired_bear"] is False


@pytest.mark.unit
def test_pydantic_validation_failure_treated_as_llm_failure():
    """Mock LLM raising ValidationError -> same as LLM call exception."""
    from pydantic import ValidationError

    # Trigger a real ValidationError by trying to construct CasePricedInScore with invalid input
    try:
        CasePricedInScore(bull_case_priced_in=2.0, bear_case_priced_in=0.5, rationale="x")
    except ValidationError as exc:
        synth_exc = exc

    md = "**Rating**: Overweight"
    llm = _make_failing_llm(synth_exc)
    out_md, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["skipped"] == "llm_failed"
    assert ann["error"] is not None
    assert out_md == md


# -- Bull-side firing logic --------------------------------------------------


@pytest.mark.unit
def test_bull_active_fires_on_overweight_above_threshold():
    """Bull score above threshold + Overweight + active -> downgrade to Hold."""
    md = "**Rating**: Overweight"
    llm = _make_llm(bull=0.78, bear=0.45)
    out_md, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["fired_bull"] is True
    assert ann["would_fire_bull"] is True
    assert ann["post_rating"] == "Hold"
    assert ann["pre_rating"] == "Overweight"
    assert "Hold" in out_md.split("Rating")[1].split("\n")[0]
    assert "[Forward-catalyst filter]" in out_md


@pytest.mark.unit
def test_bull_active_fires_on_buy_above_threshold():
    """Buy variant of bull-side fire."""
    md = "**Rating**: Buy"
    llm = _make_llm(bull=0.78, bear=0.45)
    _, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["fired_bull"] is True
    assert ann["pre_rating"] == "Buy"
    assert ann["post_rating"] == "Hold"


@pytest.mark.unit
def test_bull_active_no_fire_on_overweight_below_threshold():
    """Bull score below threshold -> no fire."""
    md = "**Rating**: Overweight"
    llm = _make_llm(bull=0.55, bear=0.45)  # 0.55 < 0.60 threshold
    out_md, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["fired_bull"] is False
    assert ann["would_fire_bull"] is False
    assert ann["pre_rating"] == "Overweight"
    assert ann["post_rating"] == "Overweight"
    assert out_md == md


@pytest.mark.unit
def test_bull_active_no_fire_on_hold():
    """Hold pre-rating -> bull side no-ops (Hold is not bullish)."""
    md = "**Rating**: Hold"
    llm = _make_llm(bull=0.78, bear=0.45)
    _, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["fired_bull"] is False
    assert ann["would_fire_bull"] is False
    # The annotation is still captured; the bull score is above threshold
    assert ann["bull_case_priced_in"] == 0.78


@pytest.mark.unit
def test_bull_active_no_fire_on_underweight():
    """UW pre-rating -> bull side no-ops; bear may fire independently."""
    md = "**Rating**: Underweight"
    llm = _make_llm(bull=0.78, bear=0.45)  # bull above; bear below
    _, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="active",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["fired_bull"] is False
    assert ann["would_fire_bull"] is False
    assert ann["fired_bear"] is False  # bear score 0.45 < 0.50 threshold
    assert ann["pre_rating"] == "Underweight"


@pytest.mark.unit
def test_bull_shadow_records_would_fire_only():
    """Bull score above threshold + shadow mode -> would_fire_bull=True, fired_bull=False."""
    md = "**Rating**: Overweight"
    llm = _make_llm(bull=0.78, bear=0.45)
    out_md, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="shadow",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["would_fire_bull"] is True
    assert ann["fired_bull"] is False
    assert ann["post_rating"] == "Overweight"
    assert out_md == md


# -- Bear-side firing logic --------------------------------------------------


@pytest.mark.unit
def test_bear_active_fires_on_underweight_above_threshold():
    """Bear score above threshold + UW + active -> downgrade to Hold."""
    md = "**Rating**: Underweight"
    llm = _make_llm(bull=0.45, bear=0.65)  # bear 0.65 > 0.50 threshold
    out_md, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="active",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["fired_bear"] is True
    assert ann["would_fire_bear"] is True
    assert ann["post_rating"] == "Hold"
    assert ann["pre_rating"] == "Underweight"
    assert "[Forward-catalyst filter]" in out_md


@pytest.mark.unit
def test_bear_active_fires_on_sell_above_threshold():
    """Sell variant of bear-side fire."""
    md = "**Rating**: Sell"
    llm = _make_llm(bull=0.45, bear=0.65)
    _, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="active",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["fired_bear"] is True
    assert ann["pre_rating"] == "Sell"
    assert ann["post_rating"] == "Hold"


@pytest.mark.unit
def test_bear_shadow_records_would_fire_only_no_override():
    """Bear shadow + score above threshold -> would_fire_bear=True; rating unchanged."""
    md = "**Rating**: Underweight"
    llm = _make_llm(bull=0.45, bear=0.65)
    out_md, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["would_fire_bear"] is True
    assert ann["fired_bear"] is False
    assert ann["post_rating"] == "Underweight"
    assert out_md == md


@pytest.mark.unit
def test_bear_shadow_default_does_not_modify_rating_25_propagates():
    """SC-011: 25 propagates with bear_mode='shadow' (default) + various scores;
    assert zero rating modifications + non-zero would_fire_bear annotations."""
    rating_modifications = 0
    would_fire_count = 0
    for i in range(25):
        bear_score = 0.40 + (i % 8) * 0.05  # range 0.40..0.75
        llm = _make_llm(bull=0.50, bear=bear_score)
        md = "**Rating**: Underweight"
        out_md, ann = evaluate_forward_catalyst(
            md,
            _state(),
            bull_mode="active",
            bear_mode="shadow",
            bull_threshold=0.60,
            bear_threshold=0.50,
            model="claude-opus-4-7",
            llm=llm,
        )
        if out_md != md:
            rating_modifications += 1
        if ann["would_fire_bear"]:
            would_fire_count += 1
    # Bear-side shadow mode must NEVER modify the rating
    assert rating_modifications == 0
    # But must capture would_fire annotations when score crosses threshold
    assert would_fire_count > 0


# -- Strict-greater-than boundary --------------------------------------------


@pytest.mark.unit
def test_strict_greater_than_boundary_bull():
    """bull_case_priced_in == bull_threshold exactly -> NOT fire (strict >)."""
    md = "**Rating**: Overweight"
    llm = _make_llm(bull=0.60, bear=0.50)  # both equal threshold
    _, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="active",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["would_fire_bull"] is False
    assert ann["fired_bull"] is False


@pytest.mark.unit
def test_strict_greater_than_boundary_bear():
    """bear_case_priced_in == bear_threshold exactly -> NOT fire (strict >)."""
    md = "**Rating**: Underweight"
    llm = _make_llm(bull=0.50, bear=0.50)  # bear equals threshold
    _, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="active",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["would_fire_bear"] is False
    assert ann["fired_bear"] is False


# -- Defensive paths ---------------------------------------------------------


@pytest.mark.unit
def test_decision_markdown_no_rating_line_defensive():
    """Markdown without parseable rating -> defaults to 'Hold' -> both sides no-op."""
    md = "Just some prose, no rating line here."
    llm = _make_llm(bull=0.78, bear=0.65)
    _, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="active",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["pre_rating"] == "Hold"
    assert ann["fired_bull"] is False
    assert ann["fired_bear"] is False


@pytest.mark.unit
def test_state_missing_report_fields_empty_substituted():
    """Missing report fields -> empty string substituted; LLM call still proceeds."""
    md = "**Rating**: Overweight"
    llm = _make_llm(bull=0.78, bear=0.45)
    state = {
        "company_of_interest": "NVDA",
        "trade_date": "2026-04-03",
        # Missing all report fields
    }
    _, ann = evaluate_forward_catalyst(
        md,
        state,
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    assert ann["fired_bull"] is True  # LLM still returns scores; filter still acts


@pytest.mark.unit
def test_invalid_mode_falls_back_to_off(caplog):
    """Unknown mode value -> defaults to 'off' with logged warning."""
    md = "**Rating**: Overweight"
    llm = MagicMock()
    with caplog.at_level("WARNING"):
        _, ann = evaluate_forward_catalyst(
            md,
            _state(),
            bull_mode="bogus",  # type: ignore[arg-type]
            bear_mode="bogus",  # type: ignore[arg-type]
            bull_threshold=0.60,
            bear_threshold=0.50,
            model="claude-opus-4-7",
            llm=llm,
        )
    assert ann["bull_mode"] == "off"
    assert ann["bear_mode"] == "off"
    assert ann["skipped"] == "off"
    assert any("unknown" in m.lower() for m in caplog.messages)


# -- Annotation invariants per data-model.md ---------------------------------


@pytest.mark.unit
def test_annotation_active_fires_populates_all_16_fields():
    """All 16 fields populated when fired_bull=True."""
    md = "**Rating**: Overweight"
    llm = _make_llm(bull=0.78, bear=0.45)
    _, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    expected_fields = {
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
    assert set(ann.keys()) == expected_fields


@pytest.mark.unit
def test_annotation_off_returns_off_skipped_or_none():
    """Both modes off -> annotation with skipped='off' (or None per implementer)."""
    md = "**Rating**: Overweight"
    _, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="off",
        bear_mode="off",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=MagicMock(),
    )
    assert ann["skipped"] == "off"
    assert ann["bull_case_priced_in"] is None
    assert ann["bear_case_priced_in"] is None


@pytest.mark.unit
def test_annotation_invariant_fired_bull_implies_active_mode():
    """Invariant 5: fired_bull=True requires bull_mode=active + pre_rating bullish + post_rating Hold."""
    md = "**Rating**: Overweight"
    llm = _make_llm(bull=0.78, bear=0.45)
    _, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    if ann["fired_bull"]:
        assert ann["would_fire_bull"] is True
        assert ann["bull_mode"] == "active"
        assert ann["pre_rating"] in ("Buy", "Overweight")
        assert ann["post_rating"] == "Hold"


@pytest.mark.unit
def test_annotation_invariant_fired_bear_implies_active_mode():
    """Invariant 6: fired_bear=True requires bear_mode=active + pre_rating bearish + post_rating Hold."""
    md = "**Rating**: Underweight"
    llm = _make_llm(bull=0.45, bear=0.65)
    _, ann = evaluate_forward_catalyst(
        md,
        _state(),
        bull_mode="active",
        bear_mode="active",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
    )
    if ann["fired_bear"]:
        assert ann["would_fire_bear"] is True
        assert ann["bear_mode"] == "active"
        assert ann["pre_rating"] in ("Underweight", "Sell")
        assert ann["post_rating"] == "Hold"


@pytest.mark.unit
def test_annotation_fired_bull_and_fired_bear_mutually_exclusive():
    """Invariant 7: fired_bull AND fired_bear is impossible (pre_rating can't be both)."""
    # We test all pre-ratings; for each, at most one of fired_bull/fired_bear can be True
    for rating in ("Buy", "Overweight", "Hold", "Underweight", "Sell"):
        md = f"**Rating**: {rating}"
        llm = _make_llm(bull=0.78, bear=0.65)  # both above thresholds
        _, ann = evaluate_forward_catalyst(
            md,
            _state(),
            bull_mode="active",
            bear_mode="active",
            bull_threshold=0.60,
            bear_threshold=0.50,
            model="claude-opus-4-7",
            llm=llm,
        )
        assert not (ann["fired_bull"] and ann["fired_bear"]), (
            f"Invariant 7 violated for rating {rating}"
        )


@pytest.mark.unit
def test_audit_corpus_filter_by_fired_bull_and_score():
    """Synthetic corpus filterable by fired_bull + bull_case_priced_in."""
    annotations = [
        {"fired_bull": True, "bull_case_priced_in": 0.78, "fired_bear": False},
        {"fired_bull": False, "bull_case_priced_in": 0.50, "fired_bear": False},
        {"fired_bull": True, "bull_case_priced_in": 0.85, "fired_bear": False},
        {"fired_bull": False, "bull_case_priced_in": None, "fired_bear": False},
        {"fired_bull": False, "bull_case_priced_in": 0.65, "fired_bear": True},
        {"fired_bull": False, "bull_case_priced_in": 0.40, "fired_bear": False},
    ]
    fired_only = [a for a in annotations if a["fired_bull"]]
    assert len(fired_only) == 2
    high_bull = [
        a
        for a in annotations
        if a["bull_case_priced_in"] is not None and a["bull_case_priced_in"] > 0.7
    ]
    assert len(high_bull) == 2


# -- Model routing -----------------------------------------------------------


@pytest.mark.unit
def test_haiku_model_routing_via_factory():
    """Verify forward_catalyst_model='claude-haiku-4-5' is routed via the factory."""
    from unittest.mock import patch

    md = "**Rating**: Overweight"
    with patch("tradingagents.llm_clients.factory.create_llm_client") as mock_factory:
        mock_client = MagicMock()
        mock_client.get_llm.return_value = _make_llm(bull=0.55, bear=0.45)
        mock_factory.return_value = mock_client
        _, _ = evaluate_forward_catalyst(
            md,
            _state(),
            bull_mode="active",
            bear_mode="shadow",
            bull_threshold=0.60,
            bear_threshold=0.50,
            model="claude-haiku-4-5",
            llm=None,  # force factory invocation
        )
    mock_factory.assert_called_once_with("anthropic", "claude-haiku-4-5")


@pytest.mark.unit
def test_opus_model_routing_via_factory():
    """Verify default model claude-opus-4-7 is routed via the factory."""
    from unittest.mock import patch

    md = "**Rating**: Overweight"
    with patch("tradingagents.llm_clients.factory.create_llm_client") as mock_factory:
        mock_client = MagicMock()
        mock_client.get_llm.return_value = _make_llm(bull=0.55, bear=0.45)
        mock_factory.return_value = mock_client
        _, _ = evaluate_forward_catalyst(
            md,
            _state(),
            bull_mode="active",
            bear_mode="shadow",
            bull_threshold=0.60,
            bear_threshold=0.50,
            model="claude-opus-4-7",
            llm=None,
        )
    mock_factory.assert_called_once_with("anthropic", "claude-opus-4-7")
