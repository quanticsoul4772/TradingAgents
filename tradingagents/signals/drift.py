"""Spec 002 Phase 2 — drift detector for cached signals.

Detects two kinds of drift per signal (or signal × feature):
- **Rolling IC degradation**: IC over the most-recent N dates is materially
  worse than IC over a prior baseline window. Threshold: ≥0.05 absolute
  decline (per spec FR-006).
- **KS-statistic distribution drift**: signal-value distribution in the
  recent window differs from historical by >0.2 KS-statistic (per spec
  FR-006).

Pure computation over the existing signal cache + experiment outcomes.
No LLM cost, no new data fetching beyond the alpha lookups already done
by the evaluation harness.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from tradingagents.signals.evaluation import _compute_alpha, _spearman_ic
from tradingagents.signals.featurization import FEATURIZERS


@dataclass
class DriftReport:
    """One drift analysis result per (signal_id [, feature])."""

    signal_id: str
    feature: str | None  # None for non-prose signals (single per-signal IC)
    horizon_days: int
    n_total: int
    n_recent: int
    n_baseline: int
    ic_recent: float | None
    ic_baseline: float | None
    ic_decline: float | None  # positive = recent IC worse than baseline
    ic_decline_alert: bool
    ks_statistic: float | None  # value-distribution KS
    ks_drift_alert: bool

    def has_alert(self) -> bool:
        return self.ic_decline_alert or self.ks_drift_alert


def ks_statistic(sample_a: list[float], sample_b: list[float]) -> float | None:
    """Two-sample Kolmogorov-Smirnov statistic — max absolute distance
    between the two empirical CDFs.

    Returns None if either sample is empty. Implemented from scratch (no
    scipy dependency). KS in [0, 1]; small values = similar distributions,
    large values = different. Threshold 0.2 per spec FR-006.
    """
    if not sample_a or not sample_b:
        return None
    a_sorted = sorted(sample_a)
    b_sorted = sorted(sample_b)
    n_a = len(a_sorted)
    n_b = len(b_sorted)

    # Compute the ECDF difference at every observed value
    all_values = sorted(set(a_sorted) | set(b_sorted))
    max_diff = 0.0
    i_a = 0
    i_b = 0
    for v in all_values:
        while i_a < n_a and a_sorted[i_a] <= v:
            i_a += 1
        while i_b < n_b and b_sorted[i_b] <= v:
            i_b += 1
        cdf_a = i_a / n_a
        cdf_b = i_b / n_b
        diff = abs(cdf_a - cdf_b)
        if diff > max_diff:
            max_diff = diff
    return max_diff


def split_by_recency(
    rows: list[dict],
    n_recent: int,
) -> tuple[list[dict], list[dict]]:
    """Sort rows by date ascending; return (baseline, recent) split where
    `recent` is the last `n_recent` rows. If fewer than 2*n_recent rows,
    `baseline` may be smaller than `recent`.
    """
    sorted_rows = sorted(rows, key=lambda r: (r["date"], r["ticker"]))
    if n_recent >= len(sorted_rows):
        return [], sorted_rows
    return sorted_rows[:-n_recent], sorted_rows[-n_recent:]


def _value_to_score(
    value: str,
    feature_extractor: Callable[[str], float] | None,
) -> float | None:
    """Map a cached value to a numeric score for IC computation.

    If a feature extractor is given (Phase 1.5 prose path), call it on the
    value. Otherwise (final_trade_decision path), parse the rating.
    """
    if feature_extractor is not None:
        try:
            return feature_extractor(value or "")
        except Exception:  # noqa: BLE001
            return None
    # Default: parse the 5-tier rating from final_trade_decision
    from tradingagents.agents.utils.rating import parse_rating

    rating = parse_rating(value or "")
    score_map = {"Buy": 2.0, "Overweight": 1.0, "Hold": 0.0, "Underweight": -1.0, "Sell": -2.0}
    return score_map.get(rating)


def _ic_from_rows(
    rows: list[dict],
    horizon_days: int,
    feature_extractor: Callable[[str], float] | None,
    alpha_cache: dict[tuple[str, str, int], float | None],
) -> float | None:
    """Compute Spearman IC between value-derived score and realized alpha
    for a row subset. Returns None if too few resolved pairs.
    """
    pairs: list[tuple[float, float]] = []
    for r in rows:
        score = _value_to_score(r["value"] or "", feature_extractor)
        if score is None:
            continue
        key = (r["ticker"].upper(), r["date"], horizon_days)
        if key not in alpha_cache:
            alpha_cache[key] = _compute_alpha(r["ticker"], r["date"], horizon_days)
        alpha = alpha_cache[key]
        if alpha is None:
            continue
        pairs.append((score, float(alpha)))
    return _spearman_ic(pairs)


def analyze_drift(
    signal_id: str,
    rows: list[dict],
    horizon_days: int = 21,
    n_recent: int = 30,
    ic_decline_threshold: float = 0.05,
    ks_drift_threshold: float = 0.2,
    feature_name: str | None = None,
    feature_extractor: Callable[[str], float] | None = None,
    alpha_cache: dict[tuple[str, str, int], float | None] | None = None,
) -> DriftReport:
    """Compute a drift report for one (signal_id [, feature]) at a horizon.

    - **IC decline**: alert if (baseline IC - recent IC) >= ic_decline_threshold.
      Computed in absolute terms — a signal whose IC went from -0.20 to -0.10
      is "less anti-predictive" but the decline magnitude is still 0.10 in
      raw IC space, which the alert flags.
    - **KS drift**: alert if KS statistic between recent and baseline value
      distributions exceeds ks_drift_threshold.
    """
    if alpha_cache is None:
        alpha_cache = {}

    baseline, recent = split_by_recency(rows, n_recent)
    n_total = len(rows)

    ic_recent = _ic_from_rows(recent, horizon_days, feature_extractor, alpha_cache)
    ic_baseline = (
        _ic_from_rows(baseline, horizon_days, feature_extractor, alpha_cache) if baseline else None
    )

    ic_decline: float | None = None
    ic_decline_alert = False
    if ic_recent is not None and ic_baseline is not None:
        ic_decline = ic_baseline - ic_recent  # positive = recent worse
        ic_decline_alert = ic_decline >= ic_decline_threshold

    # KS drift on raw value scores
    baseline_scores = [
        s
        for s in (_value_to_score(r["value"] or "", feature_extractor) for r in baseline)
        if s is not None
    ]
    recent_scores = [
        s
        for s in (_value_to_score(r["value"] or "", feature_extractor) for r in recent)
        if s is not None
    ]
    ks = ks_statistic(baseline_scores, recent_scores)
    ks_drift_alert = ks is not None and ks > ks_drift_threshold

    return DriftReport(
        signal_id=signal_id,
        feature=feature_name,
        horizon_days=horizon_days,
        n_total=n_total,
        n_recent=len(recent),
        n_baseline=len(baseline),
        ic_recent=ic_recent,
        ic_baseline=ic_baseline,
        ic_decline=ic_decline,
        ic_decline_alert=ic_decline_alert,
        ks_statistic=ks,
        ks_drift_alert=ks_drift_alert,
    )


def analyze_all_signals(
    rows_by_signal: dict[str, list[dict]],
    horizon_days: int = 21,
    n_recent: int = 30,
    ic_decline_threshold: float = 0.05,
    ks_drift_threshold: float = 0.2,
) -> list[DriftReport]:
    """Run analyze_drift across every signal in the cache.

    For final_trade_decision: one report (rating-based score).
    For each prose signal in PROSE_SIGNAL_IDS: one report per featurizer.
    For all other signals (per-tool): one report (will mostly return None ICs
    since tool-level signals are uncached prose; included for completeness).
    """
    from tradingagents.signals.featurization import PROSE_SIGNAL_IDS

    reports: list[DriftReport] = []
    alpha_cache: dict[tuple[str, str, int], float | None] = {}

    for signal_id, rows in rows_by_signal.items():
        if signal_id == "final_trade_decision":
            reports.append(
                analyze_drift(
                    signal_id,
                    rows,
                    horizon_days,
                    n_recent,
                    ic_decline_threshold,
                    ks_drift_threshold,
                    alpha_cache=alpha_cache,
                )
            )
        elif signal_id in PROSE_SIGNAL_IDS:
            for feature_name, extractor in FEATURIZERS:
                reports.append(
                    analyze_drift(
                        signal_id,
                        rows,
                        horizon_days,
                        n_recent,
                        ic_decline_threshold,
                        ks_drift_threshold,
                        feature_name=feature_name,
                        feature_extractor=extractor,
                        alpha_cache=alpha_cache,
                    )
                )
        else:
            # Per-tool signals — coverage-only for now; included so the
            # report is exhaustive.
            reports.append(
                analyze_drift(
                    signal_id,
                    rows,
                    horizon_days,
                    n_recent,
                    ic_decline_threshold,
                    ks_drift_threshold,
                    alpha_cache=alpha_cache,
                )
            )
    return reports


def render_drift_report(reports: list[DriftReport], horizon_days: int) -> str:
    """Render drift analysis as markdown."""
    from datetime import datetime, timezone

    lines: list[str] = []
    lines.append("# Signal Drift Report (spec 002 Phase 2)")
    lines.append("")
    lines.append(f"_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}._")
    lines.append("")
    lines.append(
        f"Horizon: **{horizon_days}d**. "
        f"Reports: **{len(reports)}**. "
        f"Alerts: **{sum(1 for r in reports if r.has_alert())}**."
    )
    lines.append("")

    alerts = [r for r in reports if r.has_alert()]
    if alerts:
        lines.append("## Alerts")
        lines.append("")
        lines.append(
            "| Signal | Feature | n total | IC baseline | IC recent | IC decline | KS | "
            "IC alert | KS alert |"
        )
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
        for r in sorted(alerts, key=lambda x: -(x.ic_decline or 0)):
            ic_b = f"{r.ic_baseline:+.3f}" if r.ic_baseline is not None else "—"
            ic_r = f"{r.ic_recent:+.3f}" if r.ic_recent is not None else "—"
            ic_d = f"{r.ic_decline:+.3f}" if r.ic_decline is not None else "—"
            ks = f"{r.ks_statistic:.3f}" if r.ks_statistic is not None else "—"
            ic_a = "ALERT" if r.ic_decline_alert else ""
            ks_a = "ALERT" if r.ks_drift_alert else ""
            feat = r.feature or "—"
            lines.append(
                f"| `{r.signal_id}` | `{feat}` | {r.n_total} | {ic_b} | {ic_r} | "
                f"{ic_d} | {ks} | {ic_a} | {ks_a} |"
            )
        lines.append("")

    lines.append("## All reports (sorted by |IC decline| desc)")
    lines.append("")
    lines.append(
        "| Signal | Feature | n total | n recent | IC baseline | IC recent | IC decline | KS |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    sorted_all = sorted(
        reports,
        key=lambda r: -(abs(r.ic_decline) if r.ic_decline is not None else -1),
    )
    for r in sorted_all:
        ic_b = f"{r.ic_baseline:+.3f}" if r.ic_baseline is not None else "—"
        ic_r = f"{r.ic_recent:+.3f}" if r.ic_recent is not None else "—"
        ic_d = f"{r.ic_decline:+.3f}" if r.ic_decline is not None else "—"
        ks = f"{r.ks_statistic:.3f}" if r.ks_statistic is not None else "—"
        feat = r.feature or "—"
        lines.append(
            f"| `{r.signal_id}` | `{feat}` | {r.n_total} | {r.n_recent} | "
            f"{ic_b} | {ic_r} | {ic_d} | {ks} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- **IC decline** = baseline IC minus recent IC (positive = signal "
        "weakening). Alert threshold: 0.05.\n"
        "- **KS** = Kolmogorov-Smirnov statistic between recent and baseline "
        "value distributions. Alert threshold: 0.20. Range [0, 1]; small = "
        "distributions similar, large = drifted.\n"
        "- Recent window: last 30 cached rows per signal (chronological order).\n"
        "- IC computation uses the same Spearman primitive as the evaluation "
        "harness (tradingagents/signals/evaluation.py)."
    )
    lines.append("")
    return "\n".join(lines)
