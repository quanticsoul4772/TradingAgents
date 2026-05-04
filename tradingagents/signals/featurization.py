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


# -- Phase 1.5+ featurizers (added 2026-05-04 late) --------------------------
#
# Phase 1.5 unigram + density featurizers found multiple anti-correlated
# IC pairs but they're highly inter-correlated. The featurizers below add
# structurally different signal: bigrams, negation-aware sentiment, question
# density, percentage-vs-dollar mention shape. Each is one-line registration
# in FEATURIZERS. All deterministic, no extra dependencies.


# Curated bigrams. Two-word phrases carry directional information that
# single-word counts miss (e.g., "strong buy" vs "strong concern").
_BULL_BIGRAMS = {
    ("strong", "buy"),
    ("strong", "growth"),
    ("strong", "momentum"),
    ("strong", "tailwind"),
    ("high", "conviction"),
    ("high", "growth"),
    ("clear", "upside"),
    ("upgrade", "to"),  # "upgrade to Buy"
    ("raise", "guidance"),
    ("raised", "guidance"),
    ("beat", "estimates"),
    ("beat", "consensus"),
    ("expanding", "margins"),
    ("market", "leader"),
    ("competitive", "advantage"),
    ("accelerating", "growth"),
    ("price", "target"),  # often paired with raises
}

_BEAR_BIGRAMS = {
    ("downside", "risk"),
    ("downside", "risks"),
    ("guidance", "cut"),
    ("guidance", "lowered"),
    ("lowered", "guidance"),
    ("missed", "estimates"),
    ("missed", "consensus"),
    ("declining", "margins"),
    ("compressed", "margins"),
    ("competitive", "pressure"),
    ("market", "share"),  # often "losing market share"
    ("share", "loss"),
    ("regulatory", "risk"),
    ("regulatory", "risks"),
    ("execution", "risk"),
    ("downgrade", "to"),
    ("trim", "exposure"),
    ("reduce", "exposure"),
    ("decelerating", "growth"),
}

# Negation tokens that flip the polarity of the next sentiment word.
_NEGATIONS = {"not", "no", "never", "n't", "without"}


def _word_pairs(text: str):
    """Iterate (lower, lower) consecutive word pairs."""
    words = list(_word_iter(text))
    return zip(words, words[1:], strict=False)


def bull_bigram_count(text: str) -> float:
    """Count of curated bullish bigrams ('strong buy', 'high conviction', etc.)."""
    n = sum(1 for pair in _word_pairs(text or "") if pair in _BULL_BIGRAMS)
    return float(n)


def bear_bigram_count(text: str) -> float:
    """Count of curated bearish bigrams ('downside risk', 'guidance cut', etc.)."""
    n = sum(1 for pair in _word_pairs(text or "") if pair in _BEAR_BIGRAMS)
    return float(n)


def negation_aware_sentiment_score(text: str) -> float:
    """Sentiment score with simple negation handling.

    Walks the text word by word: if the previous word is in _NEGATIONS,
    flip the polarity of the current sentiment word. So "not bullish" is
    counted as -1 (bearish) instead of +1 (bullish). Conservative: only
    looks back one word.

    Returns (bull_adj - bear_adj) / (bull_adj + bear_adj) in [-1, +1], or
    0.0 if no sentiment words present.
    """
    bull = 0
    bear = 0
    prev: str | None = None
    for w in _word_iter(text or ""):
        is_bull = w in _BULL_KEYWORDS
        is_bear = w in _BEAR_KEYWORDS
        if not (is_bull or is_bear):
            prev = w
            continue
        negated = prev in _NEGATIONS
        if is_bull:
            if negated:
                bear += 1
            else:
                bull += 1
        else:  # is_bear
            if negated:
                bull += 1
            else:
                bear += 1
        prev = w
    total = bull + bear
    if total == 0:
        return 0.0
    return (bull - bear) / total


def question_density(text: str) -> float:
    """Question marks per 1000 chars. Markers of uncertainty / open questions.

    Returns 0.0 for empty text.
    """
    if not text:
        return 0.0
    n = text.count("?")
    return (n * 1000.0) / len(text)


def percent_mention_count(text: str) -> float:
    """Count of percentage tokens (e.g., '25%', '5.5%'). Subset of
    numeric_mention_count specifically for proportional figures.
    """
    return float(len(re.findall(r"\d+(?:\.\d+)?\s*%", text or "")))


def dollar_mention_count(text: str) -> float:
    """Count of dollar tokens (e.g., '$2.5B', '$100K'). Subset of
    numeric_mention_count specifically for monetary figures.
    """
    return float(len(re.findall(r"\$\d+(?:\.\d+)?[BMKT]?", text or "")))


def bull_bear_keyword_ratio(text: str) -> float:
    """Bull keywords / (bull + bear) keywords. Returns 0.5 for balanced or
    no-sentiment-words text. Range [0, 1]; high = bull-heavy.

    Different from sentiment_score in scaling: this is in [0, 1] (probability-
    style), sentiment_score is in [-1, +1] (signed).
    """
    bull = _count_keywords(text or "", _BULL_KEYWORDS)
    bear = _count_keywords(text or "", _BEAR_KEYWORDS)
    total = bull + bear
    if total == 0:
        return 0.5
    return bull / total


# Registry of feature extractors. Each entry: (feature_name, extractor_fn).
# To add a new feature: append to this list. Each (signal_id, feature_name)
# pair becomes a separately-evaluated row in the Phase 1.5 report.
FEATURIZERS: list[tuple[str, Callable[[str], float]]] = [
    # Phase 1.5 unigram + density features
    ("sentiment_score", sentiment_score),
    ("bull_keyword_count", bull_keyword_count),
    ("bear_keyword_count", bear_keyword_count),
    ("hedge_density", hedge_density),
    ("conviction_density", conviction_density),
    ("numeric_mention_count", numeric_mention_count),
    ("value_length", value_length),
    # Phase 1.5+ structural features
    ("bull_bigram_count", bull_bigram_count),
    ("bear_bigram_count", bear_bigram_count),
    ("negation_aware_sentiment_score", negation_aware_sentiment_score),
    ("question_density", question_density),
    ("percent_mention_count", percent_mention_count),
    ("dollar_mention_count", dollar_mention_count),
    ("bull_bear_keyword_ratio", bull_bear_keyword_ratio),
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
