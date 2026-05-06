"""Tests for the WC-12 `pm_sees_synthesis` config flag.

When True (default): research_plan IS in the prompt.
When False (synthesis-blind): research_plan is replaced with a withheld
marker; trader_plan, risk debate, and memory remain untouched.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tradingagents.agents.managers.portfolio_manager import create_portfolio_manager
from tradingagents.dataflows.config import set_config

pytestmark = pytest.mark.unit


def _state(research_plan="UNIQUE_RESEARCH_PLAN_TOKEN"):
    """Minimal AgentState for portfolio_manager_node."""
    return {
        "company_of_interest": "NVDA",
        "trade_date": "2026-01-30",
        "past_context": "",
        "risk_debate_state": {
            "history": "Risk debate transcript.",
            "aggressive_history": "",
            "conservative_history": "",
            "neutral_history": "",
            "judge_decision": "",
            "current_aggressive_response": "",
            "current_conservative_response": "",
            "current_neutral_response": "",
            "count": 1,
        },
        "investment_plan": research_plan,
        "trader_investment_plan": "UNIQUE_TRADER_PLAN_TOKEN",
    }


def _make_pm_with_capture():
    """Create PM node + a list that captures every prompt the LLM sees."""
    captured = []
    llm = MagicMock()

    def capture_invoke(prompt, *args, **kwargs):
        # Both structured and free-text paths route through llm.invoke eventually.
        captured.append(prompt)
        return MagicMock(content="Rating: Hold")

    llm.invoke.side_effect = capture_invoke
    # bind_structured will try llm.with_structured_output; mock that too.
    structured = MagicMock()
    structured.invoke.side_effect = capture_invoke
    llm.with_structured_output.return_value = structured

    pm_node = create_portfolio_manager(llm)
    return pm_node, captured


def test_default_includes_research_plan_in_prompt():
    """Baseline: pm_sees_synthesis defaults True; research_plan is in the prompt."""
    set_config({"pm_sees_synthesis": True})
    pm_node, captured = _make_pm_with_capture()

    pm_node(_state())

    assert len(captured) == 1
    prompt = captured[0]
    assert "UNIQUE_RESEARCH_PLAN_TOKEN" in prompt, (
        "Default behavior should include the Research Manager's plan in the prompt."
    )
    assert "withheld by experimental config" not in prompt
    # The trader plan and risk debate are still present.
    assert "UNIQUE_TRADER_PLAN_TOKEN" in prompt
    assert "Risk debate transcript." in prompt


def test_pm_sees_synthesis_false_withholds_research_plan():
    """When False, research_plan is replaced with the withheld marker."""
    set_config({"pm_sees_synthesis": False})
    pm_node, captured = _make_pm_with_capture()

    pm_node(_state())

    assert len(captured) == 1
    prompt = captured[0]
    assert "UNIQUE_RESEARCH_PLAN_TOKEN" not in prompt, (
        "Synthesis-blind mode should NOT include research_plan."
    )
    assert "withheld by experimental config" in prompt, (
        "Withheld marker must appear so the PM knows it's operating without synthesis."
    )
    # Other inputs still present.
    assert "UNIQUE_TRADER_PLAN_TOKEN" in prompt
    assert "Risk debate transcript." in prompt


def test_pm_sees_synthesis_default_is_true():
    """Restore default and verify config behavior."""
    # Reset to default state.
    from tradingagents.default_config import DEFAULT_CONFIG

    set_config(DEFAULT_CONFIG.copy())
    pm_node, captured = _make_pm_with_capture()
    pm_node(_state())

    assert "UNIQUE_RESEARCH_PLAN_TOKEN" in captured[0], (
        "DEFAULT_CONFIG should preserve the original (synthesis-visible) behavior."
    )
