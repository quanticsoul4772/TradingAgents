"""Pydantic schemas used by agents that produce structured output.

The framework's primary artifact is still prose: each agent's natural-language
reasoning is what users read in the saved markdown reports and what the
downstream agents read as context.  Structured output is layered onto the
three decision-making agents (Research Manager, Trader, Portfolio Manager)
so that:

- Their outputs follow consistent section headers across runs and providers
- Each provider's native structured-output mode is used (json_schema for
  OpenAI/xAI, response_schema for Gemini, tool-use for Anthropic)
- Schema field descriptions become the model's output instructions, freeing
  the prompt body to focus on context and the rating-scale guidance
- A render helper turns the parsed Pydantic instance back into the same
  markdown shape the rest of the system already consumes, so display,
  memory log, and saved reports keep working unchanged
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Shared rating types
# ---------------------------------------------------------------------------


class PortfolioRating(str, Enum):
    """5-tier rating used by the Research Manager and Portfolio Manager."""

    BUY = "Buy"
    OVERWEIGHT = "Overweight"
    HOLD = "Hold"
    UNDERWEIGHT = "Underweight"
    SELL = "Sell"


class TraderAction(str, Enum):
    """3-tier transaction direction used by the Trader.

    The Trader's job is to translate the Research Manager's investment plan
    into a concrete transaction proposal: should the desk execute a Buy, a
    Sell, or sit on Hold this round.  Position sizing and the nuanced
    Overweight / Underweight calls happen later at the Portfolio Manager.
    """

    BUY = "Buy"
    HOLD = "Hold"
    SELL = "Sell"


# ---------------------------------------------------------------------------
# Research Manager
# ---------------------------------------------------------------------------


class ResearchPlan(BaseModel):
    """Structured investment plan produced by the Research Manager.

    Hand-off to the Trader: the recommendation pins the directional view,
    the rationale captures which side of the bull/bear debate carried the
    argument, and the strategic actions translate that into concrete
    instructions the trader can execute against.
    """

    recommendation: PortfolioRating = Field(
        description=(
            "The investment recommendation. Exactly one of Buy / Overweight / "
            "Hold / Underweight / Sell. Reserve Hold for situations where the "
            "evidence on both sides is genuinely balanced; otherwise commit to "
            "the side with the stronger arguments."
        ),
    )
    rationale: str = Field(
        description=(
            "Conversational summary of the key points from both sides of the "
            "debate, ending with which arguments led to the recommendation. "
            "Speak naturally, as if to a teammate."
        ),
    )
    strategic_actions: str = Field(
        description=(
            "Concrete steps for the trader to implement the recommendation, "
            "including position sizing guidance consistent with the rating."
        ),
    )


def render_research_plan(plan: ResearchPlan) -> str:
    """Render a ResearchPlan to markdown for storage and the trader's prompt context."""
    return "\n".join(
        [
            f"**Recommendation**: {plan.recommendation.value}",
            "",
            f"**Rationale**: {plan.rationale}",
            "",
            f"**Strategic Actions**: {plan.strategic_actions}",
        ]
    )


class ResearchPlanV2(BaseModel):
    """MR-3 variant: rewords the field descriptions to stop framing two-sided
    evidence as Hold-leaning. Same render path. Selected by the Research
    Manager when config.research_manager_prompt_variant == 'v2'.

    Hand-off to the Trader: identical structure to ResearchPlan; only the
    field descriptions (which the LLM sees as instructions when generating
    structured output) differ.
    """

    recommendation: PortfolioRating = Field(
        description=(
            "The investment recommendation. Exactly one of Buy / Overweight / "
            "Hold / Underweight / Sell. Two-sided evidence is the NORM in "
            "stock debates and does NOT by itself warrant Hold. Reserve Hold "
            "ONLY for cases where the bull and bear arguments are quantitatively "
            "near-equal in conviction, evidence quality, and timeframe relevance. "
            "Otherwise commit to Buy / Overweight / Underweight / Sell based on "
            "which side's strongest arguments more directly bear on the next 5 "
            "trading days."
        ),
    )
    rationale: str = Field(
        description=(
            "Conversational summary that names which side's arguments more "
            "directly bear on the holding window. Acknowledge the other side's "
            "valid points, but do not let their existence pull the recommendation "
            "toward Hold. Speak naturally, as if to a teammate."
        ),
    )
    strategic_actions: str = Field(
        description=(
            "Concrete steps for the trader to implement the recommendation, "
            "including position sizing guidance consistent with the rating."
        ),
    )


def render_research_plan_v2(plan: ResearchPlanV2) -> str:
    """Render ResearchPlanV2 to the same markdown shape as the v1 variant."""
    return "\n".join(
        [
            f"**Recommendation**: {plan.recommendation.value}",
            "",
            f"**Rationale**: {plan.rationale}",
            "",
            f"**Strategic Actions**: {plan.strategic_actions}",
        ]
    )


# ---------------------------------------------------------------------------
# Trader
# ---------------------------------------------------------------------------


class TraderProposal(BaseModel):
    """Structured transaction proposal produced by the Trader.

    The trader reads the Research Manager's investment plan and the analyst
    reports, then turns them into a concrete transaction: what action to
    take, the reasoning that justifies it, and the practical levels for
    entry, stop-loss, and sizing.
    """

    action: TraderAction = Field(
        description="The transaction direction. Exactly one of Buy / Hold / Sell.",
    )
    reasoning: str = Field(
        description=(
            "The case for this action, anchored in the analysts' reports and "
            "the research plan. Two to four sentences."
        ),
    )
    entry_price: float | None = Field(
        default=None,
        description="Optional entry price target in the instrument's quote currency.",
    )
    stop_loss: float | None = Field(
        default=None,
        description="Optional stop-loss price in the instrument's quote currency.",
    )
    position_sizing: str | None = Field(
        default=None,
        description="Optional sizing guidance, e.g. '5% of portfolio'.",
    )


def render_trader_proposal(proposal: TraderProposal) -> str:
    """Render a TraderProposal to markdown.

    The trailing ``FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**`` line is
    preserved for backward compatibility with the analyst stop-signal text
    and any external code that greps for it.
    """
    parts = [
        f"**Action**: {proposal.action.value}",
        "",
        f"**Reasoning**: {proposal.reasoning}",
    ]
    if proposal.entry_price is not None:
        parts.extend(["", f"**Entry Price**: {proposal.entry_price}"])
    if proposal.stop_loss is not None:
        parts.extend(["", f"**Stop Loss**: {proposal.stop_loss}"])
    if proposal.position_sizing:
        parts.extend(["", f"**Position Sizing**: {proposal.position_sizing}"])
    parts.extend(
        [
            "",
            f"FINAL TRANSACTION PROPOSAL: **{proposal.action.value.upper()}**",
        ]
    )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Portfolio Manager
# ---------------------------------------------------------------------------


class PortfolioDecision(BaseModel):
    """Structured output produced by the Portfolio Manager.

    The model fills every field as part of its primary LLM call; no separate
    extraction pass is required. Field descriptions double as the model's
    output instructions, so the prompt body only needs to convey context and
    the rating-scale guidance.
    """

    rating: PortfolioRating | float = Field(
        description=(
            "The final position rating. When wc_10_enabled=False (default), "
            "expect exactly one of Buy / Overweight / Hold / Underweight / Sell, "
            "picked based on the analysts' debate. When wc_10_enabled=True "
            "(WC-10 Tier 2 experiment per specs/108-wc-10-continuous-scalar-rating/), "
            "expect a continuous scalar in [-1.0, +1.0]: -1=max bearish, "
            "0=balanced/Hold-equivalent, +1=max bullish; values between thresholds "
            "express partial confidence."
        ),
    )

    @field_validator("rating")
    @classmethod
    def _validate_rating_range(cls, v: PortfolioRating | float) -> PortfolioRating | float:
        """WC-10 FR-002: float ratings must be in [-1, +1]."""
        if isinstance(v, float) and not (-1.0 <= v <= 1.0):
            raise ValueError(f"Float rating must be in [-1, +1]; got {v}")
        return v

    executive_summary: str = Field(
        description=(
            "A concise action plan covering entry strategy, position sizing, "
            "key risk levels, and time horizon. Two to four sentences."
        ),
    )
    investment_thesis: str = Field(
        description=(
            "Detailed reasoning anchored in specific evidence from the analysts' "
            "debate. If prior lessons are referenced in the prompt context, "
            "incorporate them; otherwise rely solely on the current analysis."
        ),
    )
    price_target: float | None = Field(
        default=None,
        description="Optional target price in the instrument's quote currency.",
    )
    time_horizon: str | None = Field(
        default=None,
        description="Optional recommended holding period, e.g. '3-6 months'.",
    )


def render_pm_decision(decision: PortfolioDecision) -> str:
    """Render a PortfolioDecision back to the markdown shape the rest of the system expects.

    Memory log, CLI display, and saved report files all read this markdown,
    so the rendered output preserves the exact section headers (``**Rating**``,
    ``**Executive Summary**``, ``**Investment Thesis**``) that downstream
    parsers and the report writers already handle.

    WC-10 (specs/108-wc-10-continuous-scalar-rating/): when rating is a float
    (Union type allows both PortfolioRating enum AND float in [-1, +1]),
    render as a signed decimal (e.g., "+0.4567"); SignalProcessor handles
    both forms via the wc_10_enabled config branch.
    """
    if isinstance(decision.rating, float):
        rating_str = f"{decision.rating:+.4f}"
    else:
        rating_str = decision.rating.value
    parts = [
        f"**Rating**: {rating_str}",
        "",
        f"**Executive Summary**: {decision.executive_summary}",
        "",
        f"**Investment Thesis**: {decision.investment_thesis}",
    ]
    if decision.price_target is not None:
        parts.extend(["", f"**Price Target**: {decision.price_target}"])
    if decision.time_horizon:
        parts.extend(["", f"**Time Horizon**: {decision.time_horizon}"])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# BR-3 Squeak — analyst-stage structured output
# ---------------------------------------------------------------------------


class MarketAnalystSquared(BaseModel):
    """Structured output from the BR-3 Squeak market analyst.

    Per `experiments/2026-05-09-001-br3-squeak-market-analyst/HYPOTHESIS.md`,
    BR-3 tests whether the analyst-stage prose-to-structured bottleneck is
    analogous to WC-10's confirmed PM-stage bottleneck. This schema defines
    what the structured market analyst emits in place of free-form prose.
    """

    bullish_score: float = Field(
        ge=-1.0,
        le=+1.0,
        description=(
            "Continuous bullishness score in [-1.0, +1.0]. -1.0 = max bearish, "
            "0.0 = balanced, +1.0 = max bullish."
        ),
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence in the bullish_score, 0.0 (no conviction) to 1.0 (strong conviction)."
        ),
    )
    key_drivers: list[str] = Field(
        default_factory=list,
        max_length=5,
        description=(
            "Up to 5 short bullet-style drivers supporting the bullish_score (each ≤ 80 chars)."
        ),
    )
    key_risks: list[str] = Field(
        default_factory=list,
        max_length=5,
        description=(
            "Up to 5 short bullet-style risks against the bullish_score (each ≤ 80 chars)."
        ),
    )
    citations: list[str] = Field(
        default_factory=list,
        max_length=10,
        description=("Up to 10 short citation strings referencing tool outputs."),
    )


def render_market_analyst_squared(squared: MarketAnalystSquared) -> str:
    """Render structured market analyst output as a short markdown table.

    Output shape is COMPACT (table + 2 short bullet lists) so downstream
    consumers see a structured but markdown-formatted state["market_report"]
    that they can parse without code changes.
    """
    parts: list[str] = ["## Market Analyst (structured) report\n"]
    parts.append("| Field | Value |")
    parts.append("|---|---|")
    parts.append(f"| Bullish score | `{squared.bullish_score:+.3f}` |")
    parts.append(f"| Confidence | `{squared.confidence:.2f}` |")
    parts.append("")

    if squared.key_drivers:
        parts.append("**Key drivers**:")
        for d in squared.key_drivers:
            parts.append(f"- {d}")
        parts.append("")

    if squared.key_risks:
        parts.append("**Key risks**:")
        for r in squared.key_risks:
            parts.append(f"- {r}")
        parts.append("")

    if squared.citations:
        parts.append("**Tool citations**:")
        for c in squared.citations:
            parts.append(f"- {c}")
        parts.append("")

    return "\n".join(parts)
