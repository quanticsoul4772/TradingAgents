"""Spec 002 Phase 1.5 — feature extraction for prose signals.

Phase 1 MVP only IC-evaluated ``final_trade_decision`` (parsed 5-tier rating).
The 5 prose signals (market_report, news_report, fundamentals_report,
investment_plan, sentiment_report) reported coverage stats only because
the cache stores them as markdown blobs.

Phase 1.5 adds **per-feature** numeric extraction so the same prose signal
can produce multiple IC values (one per feature). Each (signal_id, feature)
pair becomes a separate row in the evaluation report.

MVP feature set (cheap, no LLM calls, no extra dependencies):
- ``sentiment_score`` — (bull_kw - bear_kw) / total_kw (range -1 to +1)
- ``bull_keyword_count`` — raw count of bullish keywords
- ``bear_keyword_count`` — raw count of bearish keywords
- ``hedge_density`` — hedging words per 1000 chars
- ``conviction_density`` — strong-language words per 1000 chars
- ``numeric_mention_count`` — count of $X / X% / X.X patterns
- ``value_length`` — total chars (proxy for "richness")

Featurizers are deterministic, side-effect-free, and operate on the raw
markdown stored in the cache. Adding more is a one-line registration in
``FEATURIZERS``.
"""

from __future__ import annotations

import re
from collections.abc import Callable

# Keywords sourced from common bull/bear language in the project's debate
# transcripts. Match case-insensitively on word boundaries. Order doesn't
# matter; counts are independent.
_BULL_KEYWORDS = {
    "buy",
    "buying",
    "bullish",
    "outperform",
    "outperforming",
    "overweight",
    "upgrade",
    "upside",
    "growth",
    "rally",
    "expand",
    "expanding",
    "beat",
    "beats",
    "beating",
    "raise",
    "raising",
    "raised",
    "strong",
    "strength",
    "robust",
    "momentum",
    "uptrend",
    "breakout",
    "accelerating",
    "accelerate",
    "catalyst",
    "tailwind",
    "tailwinds",
    "long",
    "accumulate",
    "add",
    "adding",
    "leadership",
    "favorable",
    "compelling",
    "attractive",
    "constructive",
    "positive",
}

_BEAR_KEYWORDS = {
    "sell",
    "selling",
    "bearish",
    "underperform",
    "underperforming",
    "underweight",
    "downgrade",
    "downside",
    "decline",
    "declining",
    "drop",
    "dropped",
    "miss",
    "missed",
    "missing",
    "cut",
    "cuts",
    "cutting",
    "lower",
    "lowered",
    "weak",
    "weakness",
    "fragile",
    "headwind",
    "headwinds",
    "downtrend",
    "breakdown",
    "deceleration",
    "decelerating",
    "risk",
    "risks",
    "risky",
    "short",
    "reduce",
    "reducing",
    "trim",
    "trimming",
    "exit",
    "avoid",
    "concern",
    "concerns",
    "concerning",
    "challenging",
    "negative",
}

_HEDGE_KEYWORDS = {
    "might",
    "may",
    "could",
    "perhaps",
    "possibly",
    "potentially",
    "uncertain",
    "unclear",
    "ambiguous",
    "mixed",
    "balanced",
    "however",
    "but",
    "although",
    "though",
    "while",
    "whereas",
    "appears",
    "seems",
    "suggests",
    "suggesting",
    "indicates",
}

_CONVICTION_KEYWORDS = {
    "strong",
    "strongly",
    "decisive",
    "decisively",
    "clear",
    "clearly",
    "definitive",
    "definitively",
    "compelling",
    "convincing",
    "must",
    "should",
    "will",
    "certainly",
    "definitely",
    "obviously",
    "robust",
    "solid",
    "firm",
    "confident",
    "high-conviction",
}

# Pattern for numeric mentions: $1.23, 1.23%, $1B, 1.5T, 100x, etc.
_NUMERIC_PATTERN = re.compile(
    r"(?:\$\d+(?:\.\d+)?[BMKT]?|\d+(?:\.\d+)?\s*%|\d+(?:\.\d+)?[xX]|\d+\.\d+)",
    re.IGNORECASE,
)


def _word_iter(text: str):
    """Lowercase word iterator on alpha-only tokens."""
    return (w.lower() for w in re.findall(r"[A-Za-z]+", text or ""))


def _count_keywords(text: str, keywords: set[str]) -> int:
    """Count words in text that appear in the keyword set."""
    return sum(1 for w in _word_iter(text) if w in keywords)


def value_length(text: str) -> float:
    """Total character length of the value. Proxy for 'richness'."""
    return float(len(text or ""))


def bull_keyword_count(text: str) -> float:
    return float(_count_keywords(text or "", _BULL_KEYWORDS))


def bear_keyword_count(text: str) -> float:
    return float(_count_keywords(text or "", _BEAR_KEYWORDS))


def sentiment_score(text: str) -> float:
    """(bull - bear) / (bull + bear). Returns 0.0 if no bull/bear words present.

    Range: -1.0 (all bearish) to +1.0 (all bullish), with 0 = balanced or
    no sentiment-bearing words.
    """
    bull = _count_keywords(text or "", _BULL_KEYWORDS)
    bear = _count_keywords(text or "", _BEAR_KEYWORDS)
    total = bull + bear
    if total == 0:
        return 0.0
    return (bull - bear) / total


def hedge_density(text: str) -> float:
    """Hedge words per 1000 chars. Returns 0.0 for empty text."""
    if not text:
        return 0.0
    n = _count_keywords(text, _HEDGE_KEYWORDS)
    return (n * 1000.0) / len(text)


def conviction_density(text: str) -> float:
    """Conviction/strong words per 1000 chars. Returns 0.0 for empty text."""
    if not text:
        return 0.0
    n = _count_keywords(text, _CONVICTION_KEYWORDS)
    return (n * 1000.0) / len(text)


def numeric_mention_count(text: str) -> float:
    """Count of $X / X% / X.X / Xx tokens in the text."""
    return float(len(_NUMERIC_PATTERN.findall(text or "")))


# Registry of feature extractors. Each entry: (feature_name, extractor_fn).
# To add a new feature: append to this list. Each (signal_id, feature_name)
# pair becomes a separately-evaluated row in the Phase 1.5 report.
FEATURIZERS: list[tuple[str, Callable[[str], float]]] = [
    ("sentiment_score", sentiment_score),
    ("bull_keyword_count", bull_keyword_count),
    ("bear_keyword_count", bear_keyword_count),
    ("hedge_density", hedge_density),
    ("conviction_density", conviction_density),
    ("numeric_mention_count", numeric_mention_count),
    ("value_length", value_length),
]


# Signals whose raw value is prose markdown — featurize these into numeric
# features for IC computation. final_trade_decision is excluded because
# Phase 1 already extracts a numeric score from its parsed rating.
PROSE_SIGNAL_IDS = frozenset(
    {
        "market_report",
        "news_report",
        "fundamentals_report",
        "sentiment_report",
        "investment_plan",
    }
)
