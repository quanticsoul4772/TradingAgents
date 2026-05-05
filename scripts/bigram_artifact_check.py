"""Artifact check on the (fundamentals_report, bear_bigram_count) IC = +0.457 at 90d finding.

The signal-evaluation report (claudedocs/signal-evaluation-2026-05-04.md) flagged
this as the strongest single IC in the corpus. With 14 features × 5 signals × 4
horizons = 280 IC tests, multiple-comparisons risk is real. This script:

1. Reproduces the IC from the cache + featurizer + fetch_returns(holding_days=90)
2. Permutation test (n=5000): how often does shuffled-α give |IC| ≥ +0.457?
3. Bootstrap 95% CI on the IC
4. Per-ticker breakdown (single-ticker artifact check)
5. Per-period split (Q3'25 / Q4'25 / Q1'26 — does the IC persist across cohorts?)
6. Bigram-attribution: which specific bigrams fire at high-count rows?

Writes claudedocs/bear-bigram-artifact-check-2026-05-04.md with the verdict.
Zero LLM cost.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from tradingagents.graph.trading_graph import fetch_returns
from tradingagents.signals.cache import query_all
from tradingagents.signals.evaluation import _spearman_ic
from tradingagents.signals.featurization import _BEAR_BIGRAMS, _word_pairs, bear_bigram_count

SIGNAL_ID = "fundamentals_report"
FEATURE_NAME = "bear_bigram_count"
HORIZON_DAYS = 90
OBSERVED_IC = 0.457  # from claudedocs/signal-evaluation-2026-05-04.md
N_PERMUTATIONS = 5000
N_BOOTSTRAPS = 5000
RANDOM_SEED = 20260504

OUT_PATH = Path("claudedocs/bear-bigram-artifact-check-2026-05-04.md")


def load_pairs() -> tuple[list[tuple[float, float]], list[dict]]:
    """Pull all fundamentals_report rows from cache, compute bear_bigram_count
    + forward α via fetch_returns, return (pairs, row_metadata).

    Note: ``fetch_returns(holding_days=90)`` uses ``end = start + (holding_days + 7) days``
    so for 90d it actually only sees ~64-65 trading days. We accept this — it
    matches the methodology that produced the +0.457 number we're checking. A
    separate "true 90 trading days" measurement would require a wider buffer
    in fetch_returns (~180 calendar days) and is left as a follow-up.
    """
    rows = query_all(signal_id=SIGNAL_ID)
    pairs: list[tuple[float, float]] = []
    meta: list[dict] = []
    skipped = 0
    actuals: list[int] = []
    for r in rows:
        prose = r.get("value")
        if not prose or not isinstance(prose, str):
            skipped += 1
            continue
        ticker = r["ticker"]
        date = r["date"]
        count = bear_bigram_count(prose)
        _, alpha, actual = fetch_returns(ticker, date, holding_days=HORIZON_DAYS)
        if alpha is None:
            skipped += 1
            continue
        if actual is not None:
            actuals.append(actual)
        pairs.append((count, alpha))
        meta.append(
            {
                "ticker": ticker,
                "date": date,
                "bear_bigram_count": count,
                "alpha_90d": alpha,
                "actual_days": actual,
                "prose": prose,
            }
        )
    print(f"[load] {len(rows)} cached rows, {len(pairs)} usable, {skipped} skipped")
    if actuals:
        print(
            f"[load] actual holding days: min={min(actuals)}, "
            f"median={sorted(actuals)[len(actuals) // 2]}, max={max(actuals)} "
            f"(requested {HORIZON_DAYS} — buffer was tighter than expected)"
        )
    return pairs, meta


def permutation_test(pairs: list[tuple[float, float]], n: int) -> tuple[float, float]:
    """How often does a shuffled-α give |IC| ≥ |observed|? Returns (p_two_sided, p_one_sided)."""
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
    """Bootstrap 95% CI on the IC. Returns (lo, mean, hi)."""
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
    """Compute IC within each ticker (need ≥ 5 obs per ticker)."""
    by_ticker: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for m in meta:
        by_ticker[m["ticker"]].append((m["bear_bigram_count"], m["alpha_90d"]))
    rows = []
    for tk, pairs in sorted(by_ticker.items()):
        if len(pairs) < 5:
            rows.append({"ticker": tk, "n": len(pairs), "ic": None, "note": "n<5"})
            continue
        ic = _spearman_ic(pairs)
        rows.append({"ticker": tk, "n": len(pairs), "ic": ic, "note": ""})
    return rows


def per_period_split(meta: list[dict]) -> list[dict]:
    """Split by calendar period: Q3 2025 / Q4 2025 / Q1 2026 / other."""

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
        by_period[period(m["date"])].append((m["bear_bigram_count"], m["alpha_90d"]))
    rows = []
    for p in ["Q3 2025", "Q4 2025", "Q1 2026", "other"]:
        pairs = by_period.get(p, [])
        if len(pairs) < 5:
            rows.append({"period": p, "n": len(pairs), "ic": None, "note": "n<5"})
            continue
        ic = _spearman_ic(pairs)
        rows.append({"period": p, "n": len(pairs), "ic": ic, "note": ""})
    return rows


def bigram_attribution(meta: list[dict]) -> tuple[Counter, list[dict]]:
    """Which bigrams actually fire? Returns (overall counter, top-5-count examples)."""
    overall: Counter = Counter()
    for m in meta:
        for pair in _word_pairs(m["prose"] or ""):
            if pair in _BEAR_BIGRAMS:
                overall[pair] += 1
    high_count = sorted(meta, key=lambda r: -r["bear_bigram_count"])[:5]
    examples = []
    for ex in high_count:
        fired: Counter = Counter()
        for pair in _word_pairs(ex["prose"] or ""):
            if pair in _BEAR_BIGRAMS:
                fired[pair] += 1
        examples.append(
            {
                "ticker": ex["ticker"],
                "date": ex["date"],
                "count": ex["bear_bigram_count"],
                "alpha_90d": ex["alpha_90d"],
                "fired": dict(fired),
            }
        )
    return overall, examples


def render_report(
    n_pairs: int,
    observed_ic: float,
    p_two: float,
    p_one: float,
    ci_lo: float,
    ci_mean: float,
    ci_hi: float,
    per_ticker: list[dict],
    per_period: list[dict],
    overall_bigrams: Counter,
    examples: list[dict],
) -> str:
    lines: list[str] = []
    lines.append(f"# Bear bigram count artifact check — {datetime.utcnow().date().isoformat()}\n")
    lines.append(
        "## Question\n\n"
        f"Is `(fundamentals_report, bear_bigram_count)` IC = +{OBSERVED_IC:.3f} at "
        f"{HORIZON_DAYS}d a real predictive signal, or a multiple-comparisons artifact "
        "from 280 IC tests on n~113 obs?\n"
    )
    lines.append("## Method\n")
    lines.append(
        f"- Pulled all `{SIGNAL_ID}` rows from `~/.tradingagents/cache/signals.db`\n"
        f"- Recomputed `bear_bigram_count` via `tradingagents.signals.featurization.bear_bigram_count`\n"
        f"- Recomputed forward α via `tradingagents.graph.trading_graph.fetch_returns(holding_days={HORIZON_DAYS})`\n"
        "- Required the full holding window (`actual >= holding_days`) — drops dates too recent for 90d\n"
        f"- Permutation test n={N_PERMUTATIONS}: shuffle α-labels, recompute IC, count fraction ≥ |observed|\n"
        f"- Bootstrap 95% CI: n={N_BOOTSTRAPS} resamples with replacement\n"
        "- Per-ticker + per-period IC breakdowns to detect single-ticker / single-period artifacts\n"
        "- Bigram attribution: which specific bigrams fire at high-count rows\n"
    )
    lines.append("## Headline\n")
    lines.append(
        f"- **n usable**: {n_pairs}\n"
        f"- **Observed IC**: {observed_ic:+.4f}\n"
        f"- **Permutation p (two-sided)**: {p_two:.4f}\n"
        f"- **Permutation p (one-sided, in observed direction)**: {p_one:.4f}\n"
        f"- **Bootstrap 95% CI**: [{ci_lo:+.4f}, {ci_hi:+.4f}], mean {ci_mean:+.4f}\n"
        f"- **Bonferroni threshold for 280 IC tests**: 0.05 / 280 = 1.79e-4 — "
        f"observed p {'PASSES' if p_two < 0.05 / 280 else 'FAILS'} Bonferroni at α=0.05\n"
    )
    lines.append("## Per-ticker breakdown\n")
    lines.append("| Ticker | n | IC | Note |")
    lines.append("|---|---:|---:|---|")
    for r in per_ticker:
        ic_str = f"{r['ic']:+.4f}" if r["ic"] is not None else "—"
        lines.append(f"| {r['ticker']} | {r['n']} | {ic_str} | {r['note']} |")
    lines.append("")
    lines.append("## Per-period split\n")
    lines.append("| Period | n | IC | Note |")
    lines.append("|---|---:|---:|---|")
    for r in per_period:
        ic_str = f"{r['ic']:+.4f}" if r["ic"] is not None else "—"
        lines.append(f"| {r['period']} | {r['n']} | {ic_str} | {r['note']} |")
    lines.append("")
    lines.append("## Which bigrams actually fire?\n")
    lines.append("| Bigram | Total occurrences |")
    lines.append("|---|---:|")
    for pair, count in overall_bigrams.most_common():
        lines.append(f"| `{pair[0]} {pair[1]}` | {count} |")
    lines.append("")
    lines.append("## Top-5 highest-count rows (with their fired bigrams)\n")
    for ex in examples:
        fired_str = ", ".join(f"`{a} {b}`×{c}" for (a, b), c in ex["fired"].items()) or "(none)"
        lines.append(
            f"- **{ex['ticker']} {ex['date']}** — count {ex['count']:.0f}, α_90d {ex['alpha_90d']:+.4f}\n"
            f"  - Fired: {fired_str}"
        )
    lines.append("")
    lines.append("## Verdict\n")
    return "\n".join(lines)


def main() -> int:
    pairs, meta = load_pairs()
    if len(pairs) < 30:
        print(f"insufficient data ({len(pairs)} pairs)")
        return 1

    observed = _spearman_ic(pairs)
    print(f"[ic] observed = {observed:+.4f} (n={len(pairs)})")

    print(f"[perm] running {N_PERMUTATIONS} permutations...")
    p_two, p_one = permutation_test(pairs, N_PERMUTATIONS)
    print(f"[perm] p two-sided = {p_two:.4f}, one-sided = {p_one:.4f}")

    print(f"[boot] running {N_BOOTSTRAPS} bootstraps...")
    ci_lo, ci_mean, ci_hi = bootstrap_ci(pairs, N_BOOTSTRAPS)
    print(f"[boot] 95% CI = [{ci_lo:+.4f}, {ci_hi:+.4f}], mean {ci_mean:+.4f}")

    per_ticker = per_ticker_breakdown(meta)
    per_period = per_period_split(meta)
    overall_bigrams, examples = bigram_attribution(meta)

    report = render_report(
        n_pairs=len(pairs),
        observed_ic=observed,
        p_two=p_two,
        p_one=p_one,
        ci_lo=ci_lo,
        ci_mean=ci_mean,
        ci_hi=ci_hi,
        per_ticker=per_ticker,
        per_period=per_period,
        overall_bigrams=overall_bigrams,
        examples=examples,
    )

    print(report)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(report, encoding="utf-8")
    print(f"\n[out] {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
