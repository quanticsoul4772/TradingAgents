"""Spec 002 Phase 2 — counterfactual tester for signal additions/removals.

The full FR-007 envisions a deterministic aggregator (spec 001 bots
architecture) that takes signal scores → rating. With the aggregator
present, a counterfactual is "what if I added/removed signal X — how do
the aggregator's ratings change?". Spec 001 isn't built yet.

**Phase 2 MVP**: a more limited but still-useful counterfactual — given
an alternative rating function (callable returning a 5-tier rating per
(ticker, date)), compute the alpha delta vs the actual `final_trade_decision`
ratings recorded in the cache.

Use cases for the MVP:
- "What if PM had committed Hold on every UW date?" — would reduce the
  bear-side anti-calibration loss
- "What if PM had committed OW on every Hold date with positive market
  sentiment?" — would test the reverse-prose-anti-prediction insight from
  Phase 1.5
- "What if PM had been A3-filtered on a wider threshold?" — pre-A3 vs
  post-A3 alpha comparison

The MVP intentionally doesn't simulate a real aggregator — it just lets
you bring in any "alternative rating producer" as a function and compare.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from tradingagents.agents.utils.rating import parse_rating
from tradingagents.signals.evaluation import _compute_alpha

_DIRECTION_OF_RATING = {
    "Buy": +1,
    "Overweight": +1,
    "Hold": 0,
    "Underweight": -1,
    "Sell": -1,
}


@dataclass
class CounterfactualPair:
    """One row in the counterfactual report: (ticker, date, actual rating,
    alternative rating, realized alpha)."""

    ticker: str
    date: str
    actual_rating: str
    alternative_rating: str
    actual_alpha: float | None
    horizon_days: int

    @property
    def actual_alpha_contribution(self) -> float | None:
        """Alpha contribution under actual rating: + for bullish, − for
        bearish, 0 for Hold. We attribute the realized alpha to the
        committed direction (a Buy on a +5% return → +5%, a Sell on a +5%
        return → -5%)."""
        if self.actual_alpha is None:
            return None
        d = _DIRECTION_OF_RATING.get(self.actual_rating, 0)
        return d * self.actual_alpha

    @property
    def alternative_alpha_contribution(self) -> float | None:
        if self.actual_alpha is None:
            return None
        d = _DIRECTION_OF_RATING.get(self.alternative_rating, 0)
        return d * self.actual_alpha

    @property
    def alpha_delta(self) -> float | None:
        """Alternative contribution − actual contribution. Positive = the
        counterfactual would have produced better alpha; negative = worse."""
        if self.actual_alpha is None:
            return None
        a = self.actual_alpha_contribution
        c = self.alternative_alpha_contribution
        if a is None or c is None:
            return None
        return c - a


@dataclass
class CounterfactualReport:
    """Aggregate counterfactual analysis."""

    pairs: list[CounterfactualPair]
    horizon_days: int

    @property
    def n_total(self) -> int:
        return len(self.pairs)

    @property
    def n_resolved(self) -> int:
        return sum(1 for p in self.pairs if p.actual_alpha is not None)

    @property
    def n_changed(self) -> int:
        """Pairs where alternative rating differs from actual."""
        return sum(1 for p in self.pairs if p.alternative_rating != p.actual_rating)

    @property
    def mean_alpha_delta(self) -> float | None:
        deltas = [p.alpha_delta for p in self.pairs if p.alpha_delta is not None]
        if not deltas:
            return None
        return sum(deltas) / len(deltas)

    @property
    def total_alpha_delta(self) -> float | None:
        deltas = [p.alpha_delta for p in self.pairs if p.alpha_delta is not None]
        if not deltas:
            return None
        return sum(deltas)


def run_counterfactual(
    rows: list[dict],
    alternative_rating_fn: Callable[[str, str, str], str],
    horizon_days: int = 21,
    alpha_cache: dict[tuple[str, str, int], float | None] | None = None,
) -> CounterfactualReport:
    """Run a counterfactual: for every cached final_trade_decision row,
    compute the alpha contribution under the actual rating vs an
    alternative produced by ``alternative_rating_fn(ticker, date, actual_rating)``.

    The function takes the actual rating as input so callers can write
    rules like "if actual was UW, return Hold; otherwise return actual"
    (the A3-style override case).
    """
    if alpha_cache is None:
        alpha_cache = {}

    pairs: list[CounterfactualPair] = []
    for r in rows:
        actual_rating = parse_rating(r["value"] or "")
        if actual_rating not in _DIRECTION_OF_RATING:
            continue
        alternative_rating = alternative_rating_fn(r["ticker"], r["date"], actual_rating)
        # Validate alternative is a valid 5-tier rating
        if alternative_rating not in _DIRECTION_OF_RATING:
            continue

        key = (r["ticker"].upper(), r["date"], horizon_days)
        if key not in alpha_cache:
            alpha_cache[key] = _compute_alpha(r["ticker"], r["date"], horizon_days)
        alpha = alpha_cache[key]

        pairs.append(
            CounterfactualPair(
                ticker=r["ticker"],
                date=r["date"],
                actual_rating=actual_rating,
                alternative_rating=alternative_rating,
                actual_alpha=alpha,
                horizon_days=horizon_days,
            )
        )

    return CounterfactualReport(pairs=pairs, horizon_days=horizon_days)


def render_counterfactual_report(
    report: CounterfactualReport,
    description: str = "(unspecified counterfactual)",
) -> str:
    """Render a counterfactual report as markdown."""
    from datetime import datetime, timezone

    lines: list[str] = []
    lines.append("# Counterfactual Signal Report (spec 002 Phase 2)")
    lines.append("")
    lines.append(f"_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}._")
    lines.append("")
    lines.append(f"**Counterfactual**: {description}")
    lines.append(f"**Horizon**: {report.horizon_days}d")
    lines.append(f"**Total pairs**: {report.n_total}")
    lines.append(f"**Resolved (have realized alpha)**: {report.n_resolved}")
    lines.append(f"**Changed (alternative ≠ actual)**: {report.n_changed}")
    if report.mean_alpha_delta is not None:
        lines.append(f"**Mean alpha delta**: {report.mean_alpha_delta:+.3f}%")
        lines.append(f"**Total alpha delta**: {report.total_alpha_delta:+.3f}%")
    lines.append("")

    if report.n_changed:
        lines.append("## Changed pairs (alternative ≠ actual)")
        lines.append("")
        lines.append(
            "| Ticker | Date | Actual | Alternative | Realized α | "
            "Actual contrib | Alt contrib | Δ |"
        )
        lines.append("|---|---|---|---|---:|---:|---:|---:|")
        changed = [p for p in report.pairs if p.alternative_rating != p.actual_rating]
        for p in sorted(
            changed,
            key=lambda x: -(abs(x.alpha_delta) if x.alpha_delta is not None else -1),
        ):
            alpha_str = f"{p.actual_alpha:+.2f}%" if p.actual_alpha is not None else "—"
            ac_str = (
                f"{p.actual_alpha_contribution:+.2f}%"
                if p.actual_alpha_contribution is not None
                else "—"
            )
            cc_str = (
                f"{p.alternative_alpha_contribution:+.2f}%"
                if p.alternative_alpha_contribution is not None
                else "—"
            )
            d_str = f"{p.alpha_delta:+.2f}%" if p.alpha_delta is not None else "—"
            lines.append(
                f"| {p.ticker} | {p.date} | {p.actual_rating} | {p.alternative_rating} | "
                f"{alpha_str} | {ac_str} | {cc_str} | {d_str} |"
            )
        lines.append("")

    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "- **Alpha contribution** = direction(rating) × realized_alpha. "
        "Direction maps Buy/Overweight to +1, Hold to 0, Underweight/Sell to -1.\n"
        "- A bullish commit on a positive-α date contributes positively; on "
        "a negative-α date, negatively. A Hold contributes 0 by construction.\n"
        "- **Alpha delta** = alternative contribution − actual contribution. "
        "Positive delta = the counterfactual rating would have produced better "
        "alpha than the actual.\n"
        "- This MVP does NOT simulate a deterministic aggregator (spec 001). "
        "It compares the actual PM rating to whatever alternative the caller "
        "provides via a function."
    )
    lines.append("")
    return "\n".join(lines)


# -- Pre-built counterfactual rules ------------------------------------------
#
# Useful out-of-the-box counterfactuals callers can pass to run_counterfactual.


def hold_all_uw(ticker: str, date: str, actual_rating: str) -> str:
    """Counterfactual: PM had committed Hold on every UW/Sell date."""
    if actual_rating in {"Underweight", "Sell"}:
        return "Hold"
    return actual_rating


def hold_all_ow(ticker: str, date: str, actual_rating: str) -> str:
    """Counterfactual: PM had committed Hold on every Buy/Overweight date."""
    if actual_rating in {"Buy", "Overweight"}:
        return "Hold"
    return actual_rating


def invert_all_commits(ticker: str, date: str, actual_rating: str) -> str:
    """Counterfactual: PM had inverted every directional commit (Buy↔Sell, OW↔UW).
    Hold stays Hold. Tests "is the framework's commit-direction systematically
    wrong?" — a positive alpha delta on this counterfactual would confirm.
    """
    inversions = {
        "Buy": "Sell",
        "Overweight": "Underweight",
        "Hold": "Hold",
        "Underweight": "Overweight",
        "Sell": "Buy",
    }
    return inversions.get(actual_rating, actual_rating)
