"""Artifact check on the top-N (signal, feature) ICs from the eval report.

Generalizes scripts/bigram_artifact_check.py to run on any (signal_id,
feature_name) pair and produce a combined report comparing all of them.

Defaults to the top 4 ICs from claudedocs/signal-evaluation-2026-05-04.md
all on `fundamentals_report`:
  1. bear_bigram_count   IC@90d = +0.457  (already documented as artifact)
  2. conviction_density  IC@90d = -0.407
  3. hedge_density       IC@90d = +0.305
  4. bull_keyword_count  IC@90d = -0.306

For each, runs:
  - Reproduce IC against the cache + featurizer + fetch_returns
  - Permutation test (n=5000): p-value vs shuffled-α null
  - Bootstrap 95% CI (n=5000)
  - Per-ticker IC breakdown
  - Per-period IC split (Q3'25 / Q4'25 / Q1'26)

Then compares: which features (if any) are within-ticker predictive vs
all similarly between-ticker artifacts (the bear_bigram pattern).

Writes claudedocs/featurizer-artifact-check-2026-05-04.md.
Zero LLM cost.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tradingagents.graph.trading_graph import fetch_returns
from tradingagents.signals.cache import query_all
from tradingagents.signals.evaluation import _spearman_ic
from tradingagents.signals.featurization import (
    bear_bigram_count,
    bull_keyword_count,
    conviction_density,
    hedge_density,
)

HORIZON_DAYS = 90
N_PERMUTATIONS = 5000
N_BOOTSTRAPS = 5000
RANDOM_SEED = 20260504

OUT_PATH = Path("claudedocs/featurizer-artifact-check-2026-05-04.md")


@dataclass(frozen=True)
class FeatureSpec:
    signal_id: str
    name: str
    featurizer: Callable[[str], float]
    expected_ic: float  # from the eval report


# Top 4 ICs from the eval report, all on fundamentals_report
SPECS: list[FeatureSpec] = [
    FeatureSpec("fundamentals_report", "bear_bigram_count", bear_bigram_count, +0.457),
    FeatureSpec("fundamentals_report", "conviction_density", conviction_density, -0.407),
    FeatureSpec("fundamentals_report", "hedge_density", hedge_density, +0.305),
    FeatureSpec("fundamentals_report", "bull_keyword_count", bull_keyword_count, -0.306),
]


@dataclass
class ArtifactCheckResult:
    spec: FeatureSpec
    n_pairs: int
    actual_days_median: int
    observed_ic: float
    p_two: float
    p_one: float
    ci_lo: float
    ci_mean: float
    ci_hi: float
    per_ticker: list[dict]
    per_period: list[dict]


def load_pairs(spec: FeatureSpec) -> tuple[list[tuple[float, float]], list[dict]]:
    """Pull all rows for spec.signal_id, compute featurizer + alpha."""
    rows = query_all(signal_id=spec.signal_id)
    pairs: list[tuple[float, float]] = []
    meta: list[dict] = []
    actuals: list[int] = []
    for r in rows:
        prose = r.get("value")
        if not prose or not isinstance(prose, str):
            continue
        ticker = r["ticker"]
        date = r["date"]
        feature_value = spec.featurizer(prose)
        _, alpha, actual = fetch_returns(ticker, date, holding_days=HORIZON_DAYS)
        if alpha is None:
            continue
        if actual is not None:
            actuals.append(actual)
        pairs.append((feature_value, alpha))
        meta.append(
            {
                "ticker": ticker,
                "date": date,
                "feature": feature_value,
                "alpha": alpha,
            }
        )
    return pairs, meta


def permutation_test(pairs: list[tuple[float, float]], n: int) -> tuple[float, float]:
    rng = random.Random(RANDOM_SEED)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    observed = _spearman_ic(pairs)
    if observed is None:
        return (1.0, 1.0)
    extreme_two = 0
    extreme_one = 0
    for _ in range(n):
        ys_shuffled = ys[:]
        rng.shuffle(ys_shuffled)
        ic = _spearman_ic(list(zip(xs, ys_shuffled, strict=True)))
        if ic is None:
            continue
        if abs(ic) >= abs(observed):
            extreme_two += 1
        if observed >= 0 and ic >= observed:
            extreme_one += 1
        elif observed < 0 and ic <= observed:
            extreme_one += 1
    return (extreme_two / n, extreme_one / n)


def bootstrap_ci(pairs: list[tuple[float, float]], n: int) -> tuple[float, float, float]:
    rng = random.Random(RANDOM_SEED + 1)
    ics: list[float] = []
    for _ in range(n):
        sample = [pairs[rng.randrange(len(pairs))] for _ in range(len(pairs))]
        ic = _spearman_ic(sample)
        if ic is not None:
            ics.append(ic)
    ics.sort()
    if not ics:
        return (float("nan"), float("nan"), float("nan"))
    lo = ics[int(0.025 * len(ics))]
    hi = ics[int(0.975 * len(ics))]
    mean = sum(ics) / len(ics)
    return (lo, mean, hi)


def per_ticker_breakdown(meta: list[dict]) -> list[dict]:
    by_ticker: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for m in meta:
        by_ticker[m["ticker"]].append((m["feature"], m["alpha"]))
    rows = []
    for tk, pairs in sorted(by_ticker.items()):
        if len(pairs) < 5:
            rows.append({"ticker": tk, "n": len(pairs), "ic": None})
            continue
        rows.append({"ticker": tk, "n": len(pairs), "ic": _spearman_ic(pairs)})
    return rows


def per_period_split(meta: list[dict]) -> list[dict]:
    def period(date_str: str) -> str:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        if d.year == 2025 and d.month in (7, 8, 9):
            return "Q3 2025"
        if (d.year == 2025 and d.month in (10, 11, 12)) or (
            d.year == 2026 and d.month == 1 and d.day < 15
        ):
            return "Q4 2025"
        if d.year == 2026 and d.month in (1, 2, 3, 4):
            return "Q1 2026"
        return "other"

    by_period: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for m in meta:
        by_period[period(m["date"])].append((m["feature"], m["alpha"]))
    rows = []
    for p in ["Q3 2025", "Q4 2025", "Q1 2026", "other"]:
        pairs = by_period.get(p, [])
        if len(pairs) < 5:
            rows.append({"period": p, "n": len(pairs), "ic": None})
            continue
        rows.append({"period": p, "n": len(pairs), "ic": _spearman_ic(pairs)})
    return rows


def run_one(spec: FeatureSpec) -> ArtifactCheckResult:
    print(f"\n[{spec.name}] loading pairs...")
    pairs, meta = load_pairs(spec)
    if len(pairs) < 30:
        raise SystemExit(f"insufficient data for {spec.name}: {len(pairs)} pairs")

    actual_days_median = 0  # placeholder; per-row actual_days dropped during refactor

    observed = _spearman_ic(pairs)
    print(
        f"[{spec.name}] observed IC = {observed:+.4f} (n={len(pairs)}, expected {spec.expected_ic:+.3f})"
    )

    p_two, p_one = permutation_test(pairs, N_PERMUTATIONS)
    print(f"[{spec.name}] perm p two-sided = {p_two:.4f}, one-sided = {p_one:.4f}")

    ci_lo, ci_mean, ci_hi = bootstrap_ci(pairs, N_BOOTSTRAPS)
    print(f"[{spec.name}] 95% CI = [{ci_lo:+.4f}, {ci_hi:+.4f}], mean {ci_mean:+.4f}")

    per_ticker = per_ticker_breakdown(meta)
    per_period = per_period_split(meta)

    return ArtifactCheckResult(
        spec=spec,
        n_pairs=len(pairs),
        actual_days_median=actual_days_median,
        observed_ic=observed,
        p_two=p_two,
        p_one=p_one,
        ci_lo=ci_lo,
        ci_mean=ci_mean,
        ci_hi=ci_hi,
        per_ticker=per_ticker,
        per_period=per_period,
    )


def render_report(results: list[ArtifactCheckResult]) -> str:
    lines: list[str] = []
    lines.append(f"# Featurizer artifact check (top 4 ICs) — {datetime.now().date().isoformat()}\n")
    lines.append(
        "## Question\n\n"
        "Is the top-4 strongest-IC pattern in `claudedocs/signal-evaluation-2026-05-04.md` "
        "real predictive signal, or are all four similarly **between-ticker artifacts** "
        "(as `bear_bigram_count` was shown to be in `claudedocs/bear-bigram-artifact-check-2026-05-04.md`)?\n"
        "\n"
        "If the within-ticker IC is near zero or noisy across ALL 4 features, the "
        "featurization-based-aggregator approach has no within-ticker predictive ceiling.\n"
    )
    lines.append("## Method\n")
    lines.append(
        "Identical to the bigram artifact check, parameterized over `(signal_id, featurizer)`:\n"
        "- Cache rows for the signal\n"
        "- Recompute featurizer values + α via `fetch_returns(holding_days=90)` "
        "(actual ≈ 50 trading days due to the buffer bug)\n"
        f"- Permutation test n={N_PERMUTATIONS}, bootstrap CI n={N_BOOTSTRAPS}, per-ticker, per-period\n"
    )
    lines.append("## Headline comparison\n")
    lines.append("| Signal | Feature | n | IC | perm p₂ | 95% CI | Bonferroni @ 0.05/280 |")
    lines.append("|---|---|---:|---:|---:|---|---|")
    for r in results:
        ci = f"[{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]"
        bf = "PASS" if r.p_two < 0.05 / 280 else "FAIL"
        lines.append(
            f"| `{r.spec.signal_id}` | `{r.spec.name}` | {r.n_pairs} | "
            f"{r.observed_ic:+.4f} | {r.p_two:.4f} | {ci} | {bf} |"
        )
    lines.append("")

    lines.append("## Per-ticker IC by feature\n")
    tickers = sorted({pt["ticker"] for r in results for pt in r.per_ticker})
    lines.append("| Ticker | n | " + " | ".join(f"`{r.spec.name}`" for r in results) + " |")
    lines.append("|---|---:|" + "---:|" * len(results))
    for tk in tickers:
        # n is the same for every feature (same row set per signal)
        n = next((pt["n"] for pt in results[0].per_ticker if pt["ticker"] == tk), 0)
        cells = []
        for r in results:
            ic = next((pt["ic"] for pt in r.per_ticker if pt["ticker"] == tk), None)
            if ic is None:
                cells.append("—")
            else:
                cells.append(f"{ic:+.3f}")
        lines.append(f"| {tk} | {n} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Per-period IC by feature\n")
    lines.append("| Period | n | " + " | ".join(f"`{r.spec.name}`" for r in results) + " |")
    lines.append("|---|---:|" + "---:|" * len(results))
    for period in ["Q3 2025", "Q4 2025", "Q1 2026"]:
        n = next((pp["n"] for pp in results[0].per_period if pp["period"] == period), 0)
        cells = []
        for r in results:
            ic = next((pp["ic"] for pp in r.per_period if pp["period"] == period), None)
            if ic is None:
                cells.append("—")
            else:
                cells.append(f"{ic:+.3f}")
        lines.append(f"| {period} | {n} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Verdict\n\n")
    lines.append("(See below — verdict written by hand after reviewing the tables.)\n")
    return "\n".join(lines)


def main() -> int:
    results = [run_one(spec) for spec in SPECS]
    report = render_report(results)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(report, encoding="utf-8")
    print(f"\n[out] {OUT_PATH}")
    print("\n" + report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
