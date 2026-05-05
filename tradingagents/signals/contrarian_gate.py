"""Spec 003 — analyst-stage contrarian gate.

Empirically motivated by RESEARCH_FINDINGS finding #4 (validated 2026-05-05):
``market_report bull_keyword_count`` anti-predicts within-ticker α at 90d
(within-ticker median IC -0.489, 8/8 non-degenerate tickers with unanimous
direction; permutation p<2e-4, passes Bonferroni for 280 tests). Mechanism
investigation (claudedocs/finding4-mechanism-2026-05-05.md): the same
feature correlates +0.47 with prior 30d α — bull keywords track recent
strength which mean-reverts.

The gate measures the current propagate's bull_keyword_count percentile
against the most recent N=20 cached values for THIS ticker, and (in
active mode) downgrades Buy/Overweight commits to Hold when the
percentile crosses a threshold.

Default: disabled (``contrarian_gate_mode = "off"``). Enable via config:

    config["contrarian_gate_mode"] = "shadow"   # measure, don't change
    config["contrarian_gate_mode"] = "active"   # measure + downgrade

The gate is structurally analogous to the A3 momentum filter
(``tradingagents/agents/utils/momentum_filter.py``). A3 suppresses bearish
UW commits when the ticker is in mean-reversion zone (price-based);
spec 003 suppresses bullish Buy/OW commits when the market analyst's
prose is in mean-reversion zone (prose-based).

Spec: ``.specify/specs/003-analyst-contrarian-gate/spec.md``
Plan: ``.specify/specs/003-analyst-contrarian-gate/plan.md``
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from tradingagents.agents.utils.rating import parse_rating
from tradingagents.signals.cache import query_all
from tradingagents.signals.featurization import FEATURIZERS

logger = logging.getLogger(__name__)

_BULLISH_RATINGS = {"Buy", "Overweight"}
_VALID_MODES = ("off", "shadow", "active")
_VALID_TARGETS = ("hold", "underweight")
_TARGET_RATING = {"hold": "Hold", "underweight": "Underweight"}


@dataclass(frozen=True)
class GateAnnotation:
    """Per-propagate gate decision + diagnostics. Always emitted into the
    state log when ``contrarian_gate_mode != "off"``."""

    mode: Literal["off", "shadow", "active"]
    signal_id: str
    feature: str
    threshold: int
    target: Literal["hold", "underweight"]

    feature_value: float | None
    percentile: float | None
    n_history: int | None
    would_fire: bool | None

    gate_skipped: (
        str | None
    )  # "mode_off" | "insufficient_history" | "missing_source_signal" | "missing_featurizer" | None

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "signal_id": self.signal_id,
            "feature": self.feature,
            "threshold": self.threshold,
            "target": self.target,
            "feature_value": self.feature_value,
            "percentile": self.percentile,
            "n_history": self.n_history,
            "would_fire": self.would_fire,
            "gate_skipped": self.gate_skipped,
        }


def _percentile_of_value(history: list[float], current: float) -> float:
    """Return the percentile rank of ``current`` against ``history``.

    Definition: 100 × (count of historical values <= current) / len(history).
    A current value greater than or equal to every historical value gets 100.
    A current value less than every historical value gets 0.
    """
    if not history:
        return 0.0
    n_at_or_below = sum(1 for x in history if x <= current)
    return (n_at_or_below / len(history)) * 100.0


def _resolve_featurizer(feature_name: str):
    """Look up a featurizer by name from FEATURIZERS. Returns None if missing."""
    for name, fn in FEATURIZERS:
        if name == feature_name:
            return fn
    return None


class ContrarianGate:
    """Per-propagate contrarian gate. Reads gate config from a config dict.

    Cache reads are read-only against ``~/.tradingagents/signals/cache.db``
    (or the path passed via ``cache_path``). Cache failures are swallowed
    per the cache.py convention — the gate emits ``gate_skipped`` rather
    than raising.
    """

    DEFAULT_THRESHOLD = 80
    DEFAULT_HISTORY_FLOOR = 20  # FR-004 amended after XLF investigation

    def __init__(
        self,
        config: dict,
        cache_path: Path | None = None,
        history_floor: int = DEFAULT_HISTORY_FLOOR,
    ) -> None:
        mode = config.get("contrarian_gate_mode", "off")
        if mode not in _VALID_MODES:
            logger.warning("contrarian_gate: unknown mode %r; defaulting to 'off'", mode)
            mode = "off"
        target = config.get("contrarian_gate_target", "hold")
        if target not in _VALID_TARGETS:
            logger.warning("contrarian_gate: unknown target %r; defaulting to 'hold'", target)
            target = "hold"

        self.mode: Literal["off", "shadow", "active"] = mode  # type: ignore[assignment]
        self.threshold: int = int(config.get("contrarian_gate_threshold", self.DEFAULT_THRESHOLD))
        self.target: Literal["hold", "underweight"] = target  # type: ignore[assignment]
        self.signal_id: str = config.get("contrarian_gate_signal", "market_report")
        self.feature: str = config.get("contrarian_gate_feature", "bull_keyword_count")
        self.cache_path = cache_path
        self.history_floor = history_floor

    # ---- Annotation computation ------------------------------------------------

    def compute_annotation(
        self,
        ticker: str,
        market_report_text: str,
        pm_rating: str,
    ) -> GateAnnotation:
        """Compute the gate annotation for THIS propagate.

        Always returns a GateAnnotation; never raises. When mode == "off",
        returns the no-op annotation (gate_skipped="mode_off").
        """
        if self.mode == "off":
            return self._skipped("mode_off", pm_rating)

        featurizer = _resolve_featurizer(self.feature)
        if featurizer is None:
            return self._skipped("missing_featurizer", pm_rating)

        # Compute the current propagate's feature value
        try:
            current_value = float(featurizer(market_report_text or ""))
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "contrarian_gate: featurizer %s failed (%s); gate skipped", self.feature, exc
            )
            return self._skipped("missing_source_signal", pm_rating)

        # Pull historical values for THIS ticker from cache (per-ticker baseline)
        history = self._load_per_ticker_history(ticker, featurizer)
        if len(history) < self.history_floor:
            return self._skipped(
                "insufficient_history",
                pm_rating,
                feature_value=current_value,
                n_history=len(history),
            )

        percentile = _percentile_of_value(history, current_value)
        threshold_crossed = percentile >= self.threshold
        # would_fire requires both threshold AND eligible bullish rating
        would_fire = threshold_crossed and (pm_rating in _BULLISH_RATINGS)

        return GateAnnotation(
            mode=self.mode,
            signal_id=self.signal_id,
            feature=self.feature,
            threshold=self.threshold,
            target=self.target,
            feature_value=current_value,
            percentile=percentile,
            n_history=len(history),
            would_fire=would_fire,
            gate_skipped=None,
        )

    # ---- Active-mode rating override -------------------------------------------

    def maybe_override_decision(
        self,
        decision_markdown: str,
        annotation: GateAnnotation,
    ) -> tuple[str, bool]:
        """In active mode + when gate fires + bullish rating, downgrade rating
        and annotate the markdown. Returns (possibly_modified_markdown, gate_fired).

        Mirrors the structure of ``maybe_suppress_bear_rating`` in the A3 module.
        """
        if annotation.mode != "active":
            return decision_markdown, False
        if not annotation.would_fire:
            return decision_markdown, False

        original_rating = parse_rating(decision_markdown, default="Hold")
        if original_rating not in _BULLISH_RATINGS:
            # Defensive: would_fire should already require this, but double-check
            return decision_markdown, False

        target_rating = _TARGET_RATING[annotation.target]
        note = (
            "\n\n---\n\n"
            f"**[Spec 003 contrarian gate]** Original rating **{original_rating}** "
            f"overridden to **{target_rating}**. The market analyst's "
            f"`{annotation.feature}` value ({annotation.feature_value:.0f}) is at "
            f"the {annotation.percentile:.0f}th percentile of the most recent "
            f"{annotation.n_history} cached values for {ticker_for_note(decision_markdown) or 'this ticker'} "
            f"(threshold {annotation.threshold}). Empirical pattern from "
            f"RESEARCH_FINDINGS finding #4: high bull-keyword-density market_report prose "
            f"anti-predicts within-ticker α at 90d (within-ticker median IC -0.489, "
            f"8/8 unanimous direction). Mechanism: the analyst's bullish prose tracks "
            f"recent strength (prior 30d IC +0.47), which mean-reverts. See "
            f"`claudedocs/within-ticker-artifact-check-2026-05-05.md` and "
            f"`claudedocs/finding4-mechanism-2026-05-05.md`.\n\n"
            "---\n"
        )

        # Replace the rating line. Same pattern as A3 momentum filter.
        pattern = re.compile(
            r"(\*?\*?Rating\*?\*?\s*[:\-]\s*\*?\*?)" + re.escape(original_rating),
            re.IGNORECASE,
        )
        modified = pattern.sub(rf"\g<1>{target_rating}", decision_markdown, count=1)
        if modified == decision_markdown:
            # Couldn't substitute; prepend note
            modified = note + decision_markdown
        else:
            modified = modified + note
        return modified, True

    # ---- Internal helpers ------------------------------------------------------

    def _skipped(
        self,
        reason: str,
        pm_rating: str,
        feature_value: float | None = None,
        n_history: int | None = None,
    ) -> GateAnnotation:
        return GateAnnotation(
            mode=self.mode,
            signal_id=self.signal_id,
            feature=self.feature,
            threshold=self.threshold,
            target=self.target,
            feature_value=feature_value,
            percentile=None,
            n_history=n_history,
            would_fire=None,
            gate_skipped=reason,
        )

    def _load_per_ticker_history(self, ticker: str, featurizer: Any) -> list[float]:
        """Pull the most recent ``history_floor * 2`` cached prose rows for
        ticker, compute the featurizer on each, return the most recent
        ``history_floor`` values (the rest are buffer in case of stale rows).

        Reading more than the floor lets us be resilient to stale/duplicated
        rows in the cache; we sort by date desc and take the top history_floor.
        """
        try:
            rows = query_all(signal_id=self.signal_id, ticker=ticker, cache_path=self.cache_path)
        except Exception as exc:  # noqa: BLE001 — cache failures must not break the propagate
            logger.warning(
                "contrarian_gate: cache query failed for %s/%s (%s); gate skipped",
                self.signal_id,
                ticker,
                exc,
            )
            return []
        if not rows:
            return []

        # Sort by date desc, take most recent history_floor entries
        rows_sorted = sorted(rows, key=lambda r: r.get("date") or "", reverse=True)[
            : self.history_floor
        ]
        values: list[float] = []
        for r in rows_sorted:
            prose = r.get("value")
            if not prose or not isinstance(prose, str):
                continue
            try:
                values.append(float(featurizer(prose)))
            except Exception:  # noqa: BLE001
                continue
        return values


def ticker_for_note(_decision_markdown: str) -> str | None:
    """Best-effort ticker extraction from the PM markdown for the override note.
    Returns None if not found; the caller falls back to "this ticker".

    Kept simple — the markdown's ticker line is in build_instrument_context's
    output earlier in the prompt; the PM doesn't always echo it. The note's
    ticker is cosmetic; not finding it doesn't break behavior.
    """
    return None
