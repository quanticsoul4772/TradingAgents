"""Spec 007 Forward-Catalyst-Aware Contrarian Gate.

FIRST forward-catalyst-aware filter in the framework. Invokes an LLM
(Opus default; configurable) per propagate to score how widely the
bull/bear case is already absorbed by the market, then suppresses
commits where the corresponding case is consensus-priced-in.

Empirical motivation: Class 3 Opus retrospective DECISIVELY PASSED
Constitution VIII gate on bull-side at T=0.60 (discrim +14.43pp / hit
rate 88.9% / net Δα +2.24pp on n=33 fires). Bear-side passed criteria
1+2 with shadow-mode-first condition. See:
``claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md``
and ``specs/006-forward-catalyst-gate/`` for the full design bundle.

Pattern reuse: mirrors ``tradingagents/agents/utils/second_opinion.py``
Phase C precedent for "LLM call inside PM hook with Pydantic structured
output + graceful fallback".

Read-only against analyst reports already in state. Adds one LLM call
per propagate (skipped when both modes are "off" per FR-009 / SC-006).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_BULLISH_RATINGS = {"Buy", "Overweight"}
_BEARISH_RATINGS = {"Underweight", "Sell"}
_VALID_MODES = ("off", "shadow", "active")


# ---- Pydantic structured-output schema ------------------------------------


class CasePricedInScore(BaseModel):
    """LLM-extracted scores for how widely each side's thesis is absorbed."""

    bull_case_priced_in: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "How widely is the bull case ALREADY ACCEPTED by the market for this "
            "ticker, given the analyst evidence? 0 = no consensus / contrarian "
            "bullish setup, 0.5 = mixed acceptance, 1 = thesis is universally "
            "accepted / well-known / already-priced-in. High values mean further "
            "bullish commits face limited upside."
        ),
    )
    bear_case_priced_in: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "How widely is the bear case ALREADY ACCEPTED by the market. Same "
            "scale as bull_case_priced_in. High values mean further bearish "
            "commits face limited downside."
        ),
    )
    rationale: str = Field(
        max_length=2000,
        description=(
            "One short paragraph (3-5 sentences) explaining the two scores. "
            "Reference specific evidence from the analyst reports. Do NOT pick "
            "a direction; you are scoring how priced-in each side is."
        ),
    )


# ---- Prompt builder -------------------------------------------------------


def _trunc(s: str, max_chars: int = 6000) -> str:
    """Truncate long strings; keep prompts under ~12K tokens."""
    if not s:
        return "[empty]"
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + f"\n\n[...truncated, original length {len(s)} chars]"


def _build_prompt(state: dict, ticker: str, trade_date: str) -> str:
    """Build the LLM prompt from the analyst reports + debate + investment plan."""
    market = _trunc(state.get("market_report", ""))
    sentiment = _trunc(state.get("sentiment_report", ""))
    news = _trunc(state.get("news_report", ""))
    fundamentals = _trunc(state.get("fundamentals_report", ""))
    investment_plan = _trunc(state.get("investment_plan", ""), max_chars=2000)
    debate = _trunc(
        state.get("investment_debate_state", {}).get("history", ""),
        max_chars=4000,
    )

    return f"""You are evaluating how widely the bull case AND the bear case for a ticker are
ALREADY ACCEPTED BY THE MARKET, given the evidence collected by a multi-agent
trading framework. You are NOT picking a direction. You are scoring HOW PRICED-IN
each side's thesis is.

The empirical motivation: prior research (Class 3 Opus retrospective, 2026-05-06)
established that when a thesis (bull or bear) is widely absorbed by the market,
further commits in that direction lose alpha because the upside (or downside)
has already been priced in.

**Ticker**: {ticker}
**Trade date**: {trade_date}

---

**Market analyst report** (price action + technicals):
{market}

---

**News analyst report** (recent news + sentiment):
{news}

---

**Sentiment / social analyst report**:
{sentiment}

---

**Fundamentals analyst report** (financials + business):
{fundamentals}

---

**Bull/bear debate history** (researcher synthesis):
{debate}

---

**Research Manager's investment plan** (the bridge synthesis):
{investment_plan}

---

Score, in [0, 1]:
  - bull_case_priced_in: how widely is the bull thesis ALREADY ACCEPTED?
    1.0 = "everyone knows this story; no upside surprise possible"
    0.5 = "mixed views; some absorb, some don't"
    0.0 = "contrarian / non-consensus bullish setup; significant upside surprise potential"

  - bear_case_priced_in: how widely is the bear thesis ALREADY ACCEPTED?
    Same scale as above.

These two scores are INDEPENDENT (a ticker can have both high if the market is
debating both sides loudly, or both low if the ticker is forgotten).

Provide a brief (3-5 sentence) rationale referencing specific evidence from the
analyst reports. Do NOT pick a direction; you are scoring priced-in-ness, not
correctness."""


# ---- Annotation helpers ---------------------------------------------------


def _empty_annotation(
    *,
    model: str,
    bull_mode: str,
    bear_mode: str,
    bull_threshold: float | None,
    bear_threshold: float | None,
    pre_rating: str,
    skipped: str,
    error: str | None = None,
) -> dict:
    """Build a default annotation dict for skipped/no-fire paths.

    All 16 fields per contracts/annotation_schema.md are populated; the
    caller can override any field before returning.
    """
    return {
        "model": model,
        "bull_case_priced_in": None,
        "bear_case_priced_in": None,
        "rationale": None,
        "bull_threshold": bull_threshold,
        "bear_threshold": bear_threshold,
        "bull_mode": bull_mode,
        "bear_mode": bear_mode,
        "would_fire_bull": False,
        "would_fire_bear": False,
        "fired_bull": False,
        "fired_bear": False,
        "pre_rating": pre_rating,
        "post_rating": pre_rating,
        "skipped": skipped,
        "error": error,
    }


_RATING_LINE_RE = re.compile(
    r"\*?\*?Rating\*?\*?\s*[:\-]\s*\*?\*?(Buy|Overweight|Hold|Underweight|Sell)",
    re.IGNORECASE,
)


def _parse_pre_rating(decision_markdown: str) -> str:
    """Extract the rating from the PM markdown. Defaults to 'Hold' if unparseable."""
    if not decision_markdown:
        return "Hold"
    m = _RATING_LINE_RE.search(decision_markdown)
    if m is None:
        return "Hold"
    word = m.group(1)
    return word[:1].upper() + word[1:].lower()


def _downgrade_to_hold(
    decision_markdown: str,
    pre_rating: str,
    side: str,
    annotation: dict,
) -> str:
    """Replace the rating line with Hold + append a [Forward-catalyst filter] note."""
    score_field = "bull_case_priced_in" if side == "bull" else "bear_case_priced_in"
    threshold_field = "bull_threshold" if side == "bull" else "bear_threshold"
    note = (
        "\n\n---\n\n"
        f"**[Forward-catalyst filter]** Original rating **{pre_rating}** "
        f"overridden to **Hold**. The {side} case is widely priced in "
        f"({score_field}={annotation[score_field]:.2f}, threshold "
        f"{annotation[threshold_field]:.2f}) per LLM synthesis "
        f"({annotation['model']}) over the analyst reports + debate. "
        f"Empirical pattern: when a thesis is consensus-priced-in, further "
        f"commits in that direction lose alpha because the upside (or "
        f"downside) has already been absorbed. Rationale: "
        f"{annotation['rationale']}"
        "\n\n---\n"
    )
    pattern = re.compile(
        r"(\*?\*?Rating\*?\*?\s*[:\-]\s*\*?\*?)" + re.escape(pre_rating),
        re.IGNORECASE,
    )
    modified = pattern.sub(r"\g<1>Hold", decision_markdown, count=1)
    if modified == decision_markdown:
        # Couldn't substitute; prepend note
        modified = note + decision_markdown
    else:
        modified = modified + note
    return modified


# ---- Main filter function -------------------------------------------------


def evaluate_forward_catalyst(
    decision_markdown: str,
    state: dict,
    *,
    bull_mode: Literal["off", "shadow", "active"],
    bear_mode: Literal["off", "shadow", "active"],
    bull_threshold: float,
    bear_threshold: float,
    model: str,
    max_rationale_chars: int = 2000,
    llm: Any | None = None,
    hybrid_c_calendar_boost_enabled: bool = False,
    hybrid_c_calendar_boost_window_days: int = 14,
    hybrid_c_calendar_boost_magnitude: float = 0.5,
) -> tuple[str, dict]:
    """Apply the forward-catalyst filter to a PM decision.

    Returns ``(possibly_modified_decision_markdown, annotation_dict)``.
    See ``specs/006-forward-catalyst-gate/contracts/filter_function.md``
    for the full contract.
    """
    # Normalize modes
    if bull_mode not in _VALID_MODES:
        logger.warning("forward_catalyst: unknown bull_mode %r; defaulting to 'off'", bull_mode)
        bull_mode = "off"  # type: ignore[assignment]
    if bear_mode not in _VALID_MODES:
        logger.warning("forward_catalyst: unknown bear_mode %r; defaulting to 'off'", bear_mode)
        bear_mode = "off"  # type: ignore[assignment]

    pre_rating = _parse_pre_rating(decision_markdown)

    # 1. Both-modes-off check (skip LLM call entirely; zero cost per FR-009)
    if bull_mode == "off" and bear_mode == "off":
        return decision_markdown, _empty_annotation(
            model=model,
            bull_mode="off",
            bear_mode="off",
            bull_threshold=None,
            bear_threshold=None,
            pre_rating=pre_rating,
            skipped="off",
        )

    # 2. Threshold validation per FR-005
    bull_threshold_invalid = not (0.0 <= bull_threshold <= 1.0)
    bear_threshold_invalid = not (0.0 <= bear_threshold <= 1.0)

    if bull_threshold_invalid:
        logger.warning(
            "forward_catalyst: bull_threshold=%s outside [0, 1]; bull side disabled",
            bull_threshold,
        )
        bull_mode = "off"  # type: ignore[assignment]
    if bear_threshold_invalid:
        logger.warning(
            "forward_catalyst: bear_threshold=%s outside [0, 1]; bear side disabled",
            bear_threshold,
        )
        bear_mode = "off"  # type: ignore[assignment]

    # If both sides invalidated by threshold validation, emit invalid_threshold
    if bull_mode == "off" and bear_mode == "off":
        skipped_reason = (
            "invalid_threshold" if (bull_threshold_invalid or bear_threshold_invalid) else "off"
        )
        return decision_markdown, _empty_annotation(
            model=model,
            bull_mode="off",
            bear_mode="off",
            bull_threshold=bull_threshold if not bull_threshold_invalid else None,
            bear_threshold=bear_threshold if not bear_threshold_invalid else None,
            pre_rating=pre_rating,
            skipped=skipped_reason,
        )

    # 3. Build LLM client (lazy import to avoid circular reference)
    if llm is None:
        try:
            from tradingagents.llm_clients.factory import create_llm_client

            client = create_llm_client("anthropic", model)
            llm = client.get_llm()
        except Exception as exc:  # noqa: BLE001
            logger.warning("forward_catalyst: LLM client construction failed (%s); skipping", exc)
            return decision_markdown, _empty_annotation(
                model=model,
                bull_mode=bull_mode,
                bear_mode=bear_mode,
                bull_threshold=bull_threshold if not bull_threshold_invalid else None,
                bear_threshold=bear_threshold if not bear_threshold_invalid else None,
                pre_rating=pre_rating,
                skipped="llm_failed",
                error=str(exc),
            )

    # 4. Build prompt
    ticker = state.get("company_of_interest", "<unknown>")
    trade_date = state.get("trade_date", "<unknown>")
    prompt = _build_prompt(state, ticker, trade_date)

    # 5. Structured-output call (try/except around both with_structured_output and invoke)
    try:
        structured_llm = llm.with_structured_output(CasePricedInScore)
        score = structured_llm.invoke(prompt)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "forward_catalyst: LLM call failed for %s/%s (%s)",
            ticker,
            trade_date,
            exc,
        )
        return decision_markdown, _empty_annotation(
            model=model,
            bull_mode=bull_mode,
            bear_mode=bear_mode,
            bull_threshold=bull_threshold if not bull_threshold_invalid else None,
            bear_threshold=bear_threshold if not bear_threshold_invalid else None,
            pre_rating=pre_rating,
            skipped="llm_failed",
            error=str(exc),
        )

    # 5b. Spec 008 Hybrid C calendar boost (FR-001..FR-009). When enabled,
    #     multiply bull_case_priced_in by (1 + magnitude * boost). Bull-only
    #     per FR-004; effective_bear_score equals bear_case_priced_in.
    #     Annotation fields added ONLY when boost enabled (FR-011 backward-compat).
    hybrid_c_annotation: dict | None = None
    if hybrid_c_calendar_boost_enabled:
        from tradingagents.agents.utils.calendar_boost import (
            apply_calendar_boost,
            days_to_next_earnings,
        )
        from tradingagents.agents.utils.calendar_boost import (
            calendar_boost as _calendar_boost,
        )

        days = days_to_next_earnings(ticker, trade_date)
        boost = _calendar_boost(days, hybrid_c_calendar_boost_window_days)
        effective_bull_score = apply_calendar_boost(
            score.bull_case_priced_in,
            days,
            hybrid_c_calendar_boost_window_days,
            hybrid_c_calendar_boost_magnitude,
        )
        effective_bear_score = score.bear_case_priced_in  # FR-004 bull-only
        hybrid_c_annotation = {
            "days_to_earnings": days,
            "calendar_boost": boost,
            "effective_bull_score": effective_bull_score,
            "effective_bear_score": effective_bear_score,
        }
    else:
        effective_bull_score = score.bull_case_priced_in
        effective_bear_score = score.bear_case_priced_in

    # 6. Compute would_fire flags (strict greater-than per R-3) using effective scores
    would_fire_bull = (
        effective_bull_score > bull_threshold
        and pre_rating in _BULLISH_RATINGS
        and bull_mode != "off"
    )
    would_fire_bear = (
        effective_bear_score > bear_threshold
        and pre_rating in _BEARISH_RATINGS
        and bear_mode != "off"
    )

    # 7. Build annotation with all 16 fields. Spec 008: when Hybrid C boost
    #    enabled, append 4 additional keys (days_to_earnings, calendar_boost,
    #    effective_bull_score, effective_bear_score) per FR-012. When boost
    #    disabled, dict shape stays byte-equivalent to spec 007 baseline (FR-011).
    annotation: dict[str, Any] = {
        "model": model,
        "bull_case_priced_in": score.bull_case_priced_in,
        "bear_case_priced_in": score.bear_case_priced_in,
        "rationale": score.rationale,
        "bull_threshold": bull_threshold if not bull_threshold_invalid else None,
        "bear_threshold": bear_threshold if not bear_threshold_invalid else None,
        "bull_mode": bull_mode,
        "bear_mode": bear_mode,
        "would_fire_bull": would_fire_bull,
        "would_fire_bear": would_fire_bear,
        "fired_bull": False,
        "fired_bear": False,
        "pre_rating": pre_rating,
        "post_rating": pre_rating,
        "skipped": None,
        "error": None,
    }
    if hybrid_c_annotation is not None:
        annotation.update(hybrid_c_annotation)

    # 8. Active-mode override (mutually exclusive — pre_rating can't be both bullish AND bearish)
    if would_fire_bull and bull_mode == "active":
        decision_markdown = _downgrade_to_hold(decision_markdown, pre_rating, "bull", annotation)
        annotation["fired_bull"] = True
        annotation["post_rating"] = "Hold"
    elif would_fire_bear and bear_mode == "active":
        decision_markdown = _downgrade_to_hold(decision_markdown, pre_rating, "bear", annotation)
        annotation["fired_bear"] = True
        annotation["post_rating"] = "Hold"

    return decision_markdown, annotation
