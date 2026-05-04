"""Phase C: Second-opinion check for PortfolioManager decisions.

Implements the asymmetric handling pattern from RESEARCH_FINDINGS Q5 reasoning_divergent
synthesis: agreement augments the decision with a "confirmed" annotation; disagreement
flags the decision for human review; neutral is annotated as a low-confidence agreement.
**The PM's rating is never modified by this module** — the second opinion is advisory only.

Designed to fail gracefully: any error in the second-opinion path leaves the original
PM decision intact and logs a warning. Disabled by default; opt-in via config flag
``second_opinion_enabled``.

The "second opinion" is implemented as an independent LLM call with a Bayesian-update-
style structured prompt. It is semantically equivalent to mcp-reasoning's
``reasoning_evidence`` probabilistic mode but does not require an external service.
"""

from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecondOpinionResult(BaseModel):
    """Pydantic schema for the structured-output second-opinion call."""

    posterior: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Probability that the framework's commit direction is correct given the "
            "available evidence. 0 = certainly wrong direction, 0.5 = no evidence, "
            "1 = certainly right direction."
        ),
    )
    direction: Literal["bullish", "abstain", "bearish"] = Field(
        description=(
            "The reviewer's own independent stance on the ticker over the framework's "
            "horizon, regardless of the framework's commit."
        ),
    )
    reasoning: str = Field(
        description="One paragraph explaining the posterior estimate.",
        max_length=2000,
    )
    key_evidence_for: list[str] = Field(
        default_factory=list,
        description="Bullets of evidence supporting the framework's commit.",
    )
    key_evidence_against: list[str] = Field(
        default_factory=list,
        description="Bullets of evidence contradicting the framework's commit.",
    )


def _rating_to_direction(rating: str) -> str:
    """Map the framework's 5-tier rating to a 3-tier direction for comparison."""
    rating = rating.strip().lower()
    if rating in {"buy", "overweight"}:
        return "bullish"
    if rating in {"underweight", "sell"}:
        return "bearish"
    return "abstain"


def evaluate_pm_decision(
    pm_rating: str,
    market_report: str,
    news_report: str,
    fundamentals_report: str,
    investment_plan: str,
    risk_debate_history: str,
    ticker: str,
    trade_date: str,
    llm,
) -> SecondOpinionResult | None:
    """Run the second-opinion structured call. Returns ``None`` on any failure.

    The independent reviewer sees the same evidence the PM saw (analyst reports +
    investment plan + risk debate). It does NOT see the PM's own decision text — only
    the rating string — so it cannot anchor on the PM's reasoning.
    """
    prompt = f"""You are an independent reviewer evaluating a trading framework's commit decision.

**Ticker**: {ticker}
**Trade date**: {trade_date}
**Framework's commit**: {pm_rating}

The framework operates on a 5-tier scale (Buy / Overweight / Hold / Underweight / Sell).
Buy and Overweight are bullish commits; Underweight and Sell are bearish; Hold is abstention.

Your job is to estimate the probability that the framework's commit direction is
DIRECTIONALLY CORRECT over a 21-day forward horizon (i.e., the underlying ticker will
outperform SPY if the commit is bullish, underperform if bearish, or land near SPY if
the commit is Hold).

You are NOT trying to pick the winner. You are auditing the framework's logic given the
evidence below. A posterior of 0.5 means the evidence is balanced.

---

**Market analyst report**:
{market_report or "[empty]"}

---

**News analyst report**:
{news_report or "[empty]"}

---

**Fundamentals analyst report**:
{fundamentals_report or "[empty]"}

---

**Research Manager's investment plan (bull/bear synthesis)**:
{investment_plan or "[empty]"}

---

**Risk Analysts' debate**:
{risk_debate_history or "[empty]"}

---

Output:
- ``posterior``: your probability estimate that the framework's commit direction is correct, in [0, 1]
- ``direction``: your own independent stance — 'bullish' / 'abstain' / 'bearish'
- ``reasoning``: one paragraph explaining your posterior
- ``key_evidence_for``: bullets supporting the framework's commit (may be empty)
- ``key_evidence_against``: bullets contradicting the framework's commit (may be empty)
"""

    try:
        structured_llm = llm.with_structured_output(SecondOpinionResult)
    except (NotImplementedError, AttributeError) as exc:
        logger.warning(
            "second_opinion: provider does not support structured output (%s); "
            "skipping second-opinion check",
            exc,
        )
        return None

    try:
        return structured_llm.invoke(prompt)
    except Exception as exc:
        logger.warning(
            "second_opinion: structured invocation failed (%s); skipping",
            exc,
        )
        return None


def annotate_decision(
    decision_md: str,
    opinion: SecondOpinionResult,
    pm_rating: str,
    agree_threshold: float = 0.6,
    disagree_threshold: float = 0.4,
) -> str:
    """Append an asymmetric annotation block to the PM decision markdown.

    Asymmetry follows the Q5 reasoning_divergent synthesis:
    - Agreement (direction matches AND posterior >= agree_threshold): CONFIRMED
    - Disagreement (direction differs): REVIEW FLAG (does NOT modify rating)
    - Neutral (direction matches but posterior < agree_threshold): NEUTRAL

    The PM's rating string is never altered.
    """
    pm_direction = _rating_to_direction(pm_rating)

    if pm_direction == opinion.direction:
        if opinion.posterior >= agree_threshold:
            label = "[CONFIRMED] Second opinion AGREES with PM commit direction"
            tone = "agreement"
        else:
            label = "[NEUTRAL] Second opinion agrees with direction but at low confidence"
            tone = "neutral"
    else:
        label = "[REVIEW FLAG] Second opinion DISAGREES with PM commit direction"
        tone = "disagreement"

    evidence_for = (
        "\n".join(f"  - {b}" for b in opinion.key_evidence_for)
        if opinion.key_evidence_for
        else "  - (none cited)"
    )
    evidence_against = (
        "\n".join(f"  - {b}" for b in opinion.key_evidence_against)
        if opinion.key_evidence_against
        else "  - (none cited)"
    )

    annotation = f"""

---

**[Phase C second-opinion]** {label}

- **PM rating**: {pm_rating} (direction: {pm_direction})
- **Second-opinion direction**: {opinion.direction}
- **Posterior P(framework commit directionally correct)**: {opinion.posterior:.2f}
- **Tone**: {tone}
- **Reasoning**: {opinion.reasoning}
- **Evidence supporting PM commit**:
{evidence_for}
- **Evidence contradicting PM commit**:
{evidence_against}

NOTE: This is an advisory annotation only. The PM's rating is NOT modified by this check.

---
"""
    return decision_md + annotation
