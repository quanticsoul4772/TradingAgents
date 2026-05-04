"""Tests for tradingagents.agents.utils.second_opinion (Phase C)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from tradingagents.agents.utils.second_opinion import (
    SecondOpinionResult,
    _rating_to_direction,
    annotate_decision,
    evaluate_pm_decision,
)

pytestmark = pytest.mark.unit


# ---- _rating_to_direction --------------------------------------------------


@pytest.mark.parametrize(
    "rating,expected",
    [
        ("Buy", "bullish"),
        ("Overweight", "bullish"),
        ("buy", "bullish"),
        ("OVERWEIGHT", "bullish"),
        ("Hold", "abstain"),
        ("hold", "abstain"),
        ("Underweight", "bearish"),
        ("Sell", "bearish"),
        ("UNKNOWN", "abstain"),  # falls back to abstain
        ("", "abstain"),
    ],
)
def test_rating_to_direction(rating, expected):
    assert _rating_to_direction(rating) == expected


# ---- SecondOpinionResult schema -------------------------------------------


def test_schema_accepts_valid_fields():
    r = SecondOpinionResult(
        posterior=0.7,
        direction="bullish",
        reasoning="Evidence supports the bull case.",
        key_evidence_for=["earnings beat", "guidance raised"],
        key_evidence_against=["valuation stretched"],
    )
    assert r.posterior == 0.7
    assert r.direction == "bullish"


def test_schema_rejects_posterior_out_of_range():
    with pytest.raises(ValidationError):
        SecondOpinionResult(
            posterior=1.5,
            direction="bullish",
            reasoning="x",
        )
    with pytest.raises(ValidationError):
        SecondOpinionResult(
            posterior=-0.1,
            direction="bullish",
            reasoning="x",
        )


def test_schema_rejects_invalid_direction():
    with pytest.raises(ValidationError):
        SecondOpinionResult(
            posterior=0.5,
            direction="sideways",  # not in {bullish, abstain, bearish}
            reasoning="x",
        )


def test_schema_evidence_lists_default_empty():
    r = SecondOpinionResult(
        posterior=0.5,
        direction="abstain",
        reasoning="No strong evidence either way.",
    )
    assert r.key_evidence_for == []
    assert r.key_evidence_against == []


# ---- annotate_decision -----------------------------------------------------


def _opinion(direction: str, posterior: float) -> SecondOpinionResult:
    return SecondOpinionResult(
        posterior=posterior,
        direction=direction,  # type: ignore
        reasoning="test reasoning",
        key_evidence_for=["test evidence for"],
        key_evidence_against=["test evidence against"],
    )


def test_annotate_agreement_high_confidence():
    """Direction matches AND posterior >= agree_threshold → CONFIRMED."""
    pm_md = "**Rating: Overweight**\nDecision body."
    opinion = _opinion("bullish", 0.75)
    out = annotate_decision(pm_md, opinion, "Overweight")
    assert "[CONFIRMED]" in out
    assert "AGREES" in out
    assert "[REVIEW FLAG]" not in out
    # Original markdown is preserved
    assert "**Rating: Overweight**" in out
    # Note about non-modification
    assert "rating is not modified" in out.lower()


def test_annotate_agreement_low_confidence_is_neutral():
    """Direction matches but posterior < agree_threshold → NEUTRAL."""
    pm_md = "**Rating: Buy**\nDecision body."
    opinion = _opinion("bullish", 0.55)
    out = annotate_decision(pm_md, opinion, "Buy", agree_threshold=0.6)
    assert "[NEUTRAL]" in out
    assert "low confidence" in out
    assert "[CONFIRMED]" not in out
    assert "[REVIEW FLAG]" not in out


def test_annotate_disagreement_flags_review():
    """Direction differs → REVIEW FLAG regardless of posterior magnitude."""
    pm_md = "**Rating: Overweight**\nBull case."
    opinion = _opinion("bearish", 0.7)
    out = annotate_decision(pm_md, opinion, "Overweight")
    assert "[REVIEW FLAG]" in out
    assert "DISAGREES" in out
    assert "[CONFIRMED]" not in out


def test_annotate_disagreement_pm_bullish_opinion_abstain():
    """PM bullish, second opinion abstain — direction differs → REVIEW FLAG."""
    pm_md = "**Rating: Buy**"
    opinion = _opinion("abstain", 0.5)
    out = annotate_decision(pm_md, opinion, "Buy")
    assert "[REVIEW FLAG]" in out


def test_annotate_disagreement_pm_hold_opinion_bullish():
    """PM Hold, second opinion bullish — direction differs → REVIEW FLAG."""
    pm_md = "**Rating: Hold**"
    opinion = _opinion("bullish", 0.7)
    out = annotate_decision(pm_md, opinion, "Hold")
    assert "[REVIEW FLAG]" in out


def test_annotate_includes_posterior_value():
    pm_md = "**Rating: Overweight**"
    opinion = _opinion("bullish", 0.83)
    out = annotate_decision(pm_md, opinion, "Overweight")
    assert "0.83" in out


def test_annotate_includes_evidence_bullets():
    pm_md = "**Rating: Buy**"
    opinion = SecondOpinionResult(
        posterior=0.7,
        direction="bullish",
        reasoning="Bullish evidence is strong.",
        key_evidence_for=["earnings beat", "guidance raised"],
        key_evidence_against=["valuation high"],
    )
    out = annotate_decision(pm_md, opinion, "Buy")
    assert "earnings beat" in out
    assert "guidance raised" in out
    assert "valuation high" in out


def test_annotate_handles_empty_evidence_lists():
    pm_md = "**Rating: Hold**"
    opinion = _opinion("abstain", 0.5)
    opinion.key_evidence_for = []
    opinion.key_evidence_against = []
    out = annotate_decision(pm_md, opinion, "Hold")
    assert "(none cited)" in out


def test_annotate_pm_rating_appears_in_annotation():
    pm_md = "Body."
    opinion = _opinion("bullish", 0.7)
    out = annotate_decision(pm_md, opinion, "Overweight")
    assert "Overweight" in out


def test_annotate_pm_direction_appears_in_annotation():
    pm_md = "Body."
    opinion = _opinion("bullish", 0.7)
    out = annotate_decision(pm_md, opinion, "Overweight")
    assert "bullish" in out  # PM direction


# ---- evaluate_pm_decision (graceful degradation) ---------------------------


def test_evaluate_returns_none_when_provider_lacks_structured_output():
    """If llm.with_structured_output raises NotImplementedError, return None."""
    llm = MagicMock()
    llm.with_structured_output.side_effect = NotImplementedError("no structured")
    result = evaluate_pm_decision(
        pm_rating="Overweight",
        market_report="m",
        news_report="n",
        fundamentals_report="f",
        investment_plan="ip",
        risk_debate_history="rd",
        ticker="NVDA",
        trade_date="2026-04-01",
        llm=llm,
    )
    assert result is None


def test_evaluate_returns_none_when_provider_lacks_attribute():
    """If llm.with_structured_output raises AttributeError, return None."""
    llm = MagicMock()
    llm.with_structured_output.side_effect = AttributeError("no method")
    result = evaluate_pm_decision(
        pm_rating="Hold",
        market_report="",
        news_report="",
        fundamentals_report="",
        investment_plan="",
        risk_debate_history="",
        ticker="AAPL",
        trade_date="2026-04-01",
        llm=llm,
    )
    assert result is None


def test_evaluate_returns_none_on_invocation_failure():
    """If structured_llm.invoke raises any exception, return None."""
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.side_effect = RuntimeError("network down")
    llm.with_structured_output.return_value = structured
    result = evaluate_pm_decision(
        pm_rating="Buy",
        market_report="m",
        news_report="n",
        fundamentals_report="f",
        investment_plan="ip",
        risk_debate_history="rd",
        ticker="NVDA",
        trade_date="2026-04-01",
        llm=llm,
    )
    assert result is None


def test_evaluate_returns_result_on_success():
    """Happy path: structured_llm returns a SecondOpinionResult."""
    llm = MagicMock()
    structured = MagicMock()
    expected = SecondOpinionResult(
        posterior=0.7,
        direction="bullish",
        reasoning="Bull case is well-supported.",
        key_evidence_for=["earnings"],
        key_evidence_against=[],
    )
    structured.invoke.return_value = expected
    llm.with_structured_output.return_value = structured

    result = evaluate_pm_decision(
        pm_rating="Overweight",
        market_report="m",
        news_report="n",
        fundamentals_report="f",
        investment_plan="ip",
        risk_debate_history="rd",
        ticker="NVDA",
        trade_date="2026-04-01",
        llm=llm,
    )
    assert result is expected
    # Verify with_structured_output was called with the right schema
    llm.with_structured_output.assert_called_once_with(SecondOpinionResult)


def test_evaluate_passes_evidence_into_prompt():
    """The reports + ticker should appear in the prompt sent to the LLM."""
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = SecondOpinionResult(
        posterior=0.5,
        direction="abstain",
        reasoning="x",
    )
    llm.with_structured_output.return_value = structured

    evaluate_pm_decision(
        pm_rating="Overweight",
        market_report="MARKET_TOKEN",
        news_report="NEWS_TOKEN",
        fundamentals_report="FUND_TOKEN",
        investment_plan="IP_TOKEN",
        risk_debate_history="RD_TOKEN",
        ticker="NVDA",
        trade_date="2026-04-01",
        llm=llm,
    )
    call_args = structured.invoke.call_args
    prompt = call_args[0][0]  # first positional arg
    assert "MARKET_TOKEN" in prompt
    assert "NEWS_TOKEN" in prompt
    assert "FUND_TOKEN" in prompt
    assert "IP_TOKEN" in prompt
    assert "RD_TOKEN" in prompt
    assert "NVDA" in prompt
    assert "2026-04-01" in prompt
    assert "Overweight" in prompt
