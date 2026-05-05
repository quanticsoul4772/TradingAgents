"""Artifact check for within-ticker IC candidates.

The within-ticker IC column added to scripts/evaluate_signals.py surfaced
3 candidate WITHIN-ticker predictors where the within-ticker median IC
is materially stronger than the aggregate IC suggested:

  market_report     bull_keyword_count: aggregate -0.011, within -0.489 (9/9 neg)
  investment_plan   bull_keyword_count: aggregate -0.199, within -0.295 (8/9 neg)
  investment_plan   hedge_density:      aggregate -0.145, within -0.189 (7/9 neg)

These are mirror-image candidates to the Simpson's-paradox artifacts
documented in claudedocs/featurizer-artifact-check-2026-05-04.md — instead
of "aggregate signal that disappears within ticker", these show
"within-ticker signal that the aggregate under-stated." If they survive
artifact validation (per-ticker IC stable, period-stable, permutation-
significant), they're the FIRST real within-ticker predictors in the
corpus.

For each candidate, runs:
  - Per-ticker IC + bootstrap CI on each
  - Within-ticker median IC + permutation test (shuffle alpha within
    each ticker independently — preserves between-ticker structure,
    isolates within-ticker null)
  - Per-period within-ticker breakdown (Q4'25 vs Q1'26 stability)
  - Sign-agreement test: how unusual is N-of-N unanimous direction?

Writes claudedocs/within-ticker-artifact-check-2026-05-05.md.
Zero LLM cost.
"""

from __future__ import annotations

import random
import statistics
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
    bear_keyword_count,
    bull_bear_keyword_ratio,
    bull_bigram_count,
    bull_keyword_count,
    hedge_density,
    negation_aware_sentiment_score,
    percent_mention_count,
    question_density,
    sentiment_score,
)

HORIZON_DAYS = 90
MIN_N_PER_TICKER = 5
N_PERMUTATIONS = 5000
N_BOOTSTRAPS = 5000
RANDOM_SEED = 20260505

OUT_PATH = Path("claudedocs/within-ticker-full-artifact-check-2026-05-05.md")


@dataclass(frozen=True)
class Candidate:
    signal_id: str
    name: str
    featurizer: Callable[[str], float]
    expected_within_ic: float
    expected_n_pos_neg: tuple[int, int]


CANDIDATES: list[Candidate] = [
    # Original 3 (already validated 2026-05-05 morning) — kept for re-runs
    Candidate("market_report", "bull_keyword_count", bull_keyword_count, -0.489, (0, 9)),
    Candidate("investment_plan", "bull_keyword_count", bull_keyword_count, -0.295, (1, 8)),
    Candidate("investment_plan", "hedge_density", hedge_density, -0.189, (2, 7)),
    # 8 new candidates (2026-05-05 evening) — remaining flagged candidates
    # from claudedocs/signal-evaluation-2026-05-05-within-ticker.md.
    # Mix of (a) classical Simpson's-paradox cases (aggregate sign disagrees
    # with within-ticker median sign) and (b) inverse-pattern cases (within-
    # ticker signal stronger than aggregate suggested).
    Candidate("fundamentals_report", "sentiment_score", sentiment_score, +0.166, (4, 1)),
    Candidate(
        "fundamentals_report",
        "negation_aware_sentiment_score",
        negation_aware_sentiment_score,
        +0.167,
        (5, 1),
    ),
    Candidate(
        "fundamentals_report",
        "bull_bear_keyword_ratio",
        bull_bear_keyword_ratio,
        +0.166,
        (4, 1),
    ),
    Candidate("fundamentals_report", "bear_keyword_count", bear_keyword_count, -0.014, (3, 3)),
    Candidate(
        "fundamentals_report",
        "percent_mention_count",
        percent_mention_count,
        +0.010,
        (3, 3),
    ),
    Candidate("market_report", "question_density", question_density, -0.027, (1, 3)),
    Candidate("news_report", "bull_bigram_count", bull_bigram_count, -0.269, (2, 7)),
    Candidate("investment_plan", "bear_bigram_count", bear_bigram_count, -0.262, (2, 7)),
]


def load_pairs_by_ticker(
    c: Candidate,
) -> tuple[dict[str, list[tuple[float, float, str]]], list[dict]]:
    """Pull all rows for c.signal_id, group (feature, alpha, date) tuples by ticker."""
    rows = query_all(signal_id=c.signal_id)
    by_ticker: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
    meta: list[dict] = []
    for r in rows:
        prose = r.get("value")
        if not prose or not isinstance(prose, str):
            continue
        ticker = r["ticker"]
        date = r["date"]
        feat = c.featurizer(prose)
        _, alpha, _ = fetch_returns(ticker, date, holding_days=HORIZON_DAYS)
        if alpha is None:
            continue
        by_ticker[ticker].append((feat, alpha, date))
        meta.append(
            {
                "ticker": ticker,
                "date": date,
                "feature": feat,
                "alpha": alpha,
            }
        )
    return by_ticker, meta


def per_ticker_ics(by_ticker: dict[str, list[tuple[float, float, str]]]) -> list[dict]:
    """Compute IC + bootstrap CI per ticker."""
    rng = random.Random(RANDOM_SEED)
    rows = []
    for ticker, triples in sorted(by_ticker.items()):
        if len(triples) < MIN_N_PER_TICKER:
            rows.append(
                {"ticker": ticker, "n": len(triples), "ic": None, "ci_lo": None, "ci_hi": None}
            )
            continue
        pairs = [(t[0], t[1]) for t in triples]
        ic = _spearman_ic(pairs)
        # bootstrap CI per ticker
        ics: list[float] = []
        for _ in range(N_BOOTSTRAPS):
            sample = [pairs[rng.randrange(len(pairs))] for _ in range(len(pairs))]
            b_ic = _spearman_ic(sample)
            if b_ic is not None:
                ics.append(b_ic)
        if not ics:
            ci_lo = ci_hi = None
        else:
            ics.sort()
            ci_lo = ics[int(0.025 * len(ics))]
            ci_hi = ics[int(0.975 * len(ics))]
        rows.append(
            {
                "ticker": ticker,
                "n": len(triples),
                "ic": ic,
                "ci_lo": ci_lo,
                "ci_hi": ci_hi,
            }
        )
    return rows


def within_ticker_permutation_test(
    by_ticker: dict[str, list[tuple[float, float, str]]],
    n: int,
) -> tuple[float, float, float, float]:
    """Permutation test that preserves between-ticker structure.

    Within each ticker independently, shuffle alpha labels. Then recompute
    the within-ticker median IC across tickers. How often does the shuffled
    null produce |median IC| >= |observed|?

    This is the right null for the within-ticker question — the aggregate
    permutation test would conflate between- and within-ticker variance.

    Returns (observed_median, p_two_sided, p_one_sided, observed_unanimous_count).
    """
    rng = random.Random(RANDOM_SEED + 1)

    # Observed
    observed_ics: list[float] = []
    for triples in by_ticker.values():
        if len(triples) < MIN_N_PER_TICKER:
            continue
        pairs = [(t[0], t[1]) for t in triples]
        ic = _spearman_ic(pairs)
        if ic is not None:
            observed_ics.append(ic)
    observed_median = statistics.median(observed_ics)
    observed_pos = sum(1 for ic in observed_ics if ic > 0)
    observed_neg = sum(1 for ic in observed_ics if ic < 0)
    # Unanimous direction = all same sign
    observed_unanimous = max(observed_pos, observed_neg)

    # Permutation
    extreme_two = 0
    extreme_one = 0
    extreme_unanimous = 0
    for _ in range(n):
        shuffled_ics: list[float] = []
        shuffled_signs = 0
        for triples in by_ticker.values():
            if len(triples) < MIN_N_PER_TICKER:
                continue
            feats = [t[0] for t in triples]
            alphas = [t[1] for t in triples]
            rng.shuffle(alphas)
            ic = _spearman_ic(list(zip(feats, alphas, strict=True)))
            if ic is not None:
                shuffled_ics.append(ic)
                if ic > 0:
                    shuffled_signs += 1
        if not shuffled_ics:
            continue
        med = statistics.median(shuffled_ics)
        if abs(med) >= abs(observed_median):
            extreme_two += 1
        if observed_median >= 0 and med >= observed_median:
            extreme_one += 1
        elif observed_median < 0 and med <= observed_median:
            extreme_one += 1
        # Unanimous test: count of one-sided sign agreement
        n_pos = shuffled_signs
        n_neg = len(shuffled_ics) - n_pos
        unanimous = max(n_pos, n_neg)
        if unanimous >= observed_unanimous:
            extreme_unanimous += 1

    return (
        observed_median,
        extreme_two / n,
        extreme_one / n,
        extreme_unanimous / n,
    )


def per_period_within(by_ticker: dict[str, list[tuple[float, float, str]]]) -> list[dict]:
    """Per-period within-ticker IC stability check."""

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

    # Group by (period, ticker) → list of (feat, alpha)
    by_period_ticker: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for ticker, triples in by_ticker.items():
        for feat, alpha, date in triples:
            by_period_ticker[(period(date), ticker)].append((feat, alpha))

    # For each period, compute within-ticker median IC across tickers with n>=5
    results = []
    for p in ["Q3 2025", "Q4 2025", "Q1 2026"]:
        ics = []
        n_pos = n_neg = 0
        n_tickers = 0
        for (period_label, _ticker), pairs in by_period_ticker.items():
            if period_label != p:
                continue
            if len(pairs) < MIN_N_PER_TICKER:
                continue
            ic = _spearman_ic(pairs)
            if ic is None:
                continue
            ics.append(ic)
            n_tickers += 1
            if ic > 0:
                n_pos += 1
            elif ic < 0:
                n_neg += 1
        if not ics:
            results.append({"period": p, "n_tickers": 0, "median_ic": None, "n_pos": 0, "n_neg": 0})
            continue
        results.append(
            {
                "period": p,
                "n_tickers": n_tickers,
                "median_ic": statistics.median(ics),
                "n_pos": n_pos,
                "n_neg": n_neg,
            }
        )
    return results


def render_one(
    c: Candidate,
    per_ticker: list[dict],
    perm_result: tuple[float, float, float, float],
    per_period: list[dict],
) -> list[str]:
    observed_median, p_two, p_one, p_unanimous = perm_result
    lines = []
    lines.append(f"## `{c.signal_id}` × `{c.name}`\n")
    lines.append(
        f"**Expected (from eval report)**: within-ticker median IC = {c.expected_within_ic:+.3f}, "
        f"sign agreement {c.expected_n_pos_neg[0]}+/{c.expected_n_pos_neg[1]}−.\n"
    )
    lines.append(f"**Observed**: within-ticker median IC = {observed_median:+.4f}\n")
    lines.append(
        "### Within-ticker permutation test\n\n"
        "(shuffle α independently within each ticker — preserves between-ticker structure)\n\n"
        f"- p (two-sided, |IC|): {p_two:.4f}\n"
        f"- p (one-sided, in observed direction): {p_one:.4f}\n"
        f"- p (unanimous direction agreement): {p_unanimous:.4f}\n"
    )
    lines.append("### Per-ticker IC + bootstrap CI\n")
    lines.append("| Ticker | n | IC | 95% CI | Sign |")
    lines.append("|---|---:|---:|---|---|")
    for r in per_ticker:
        if r["ic"] is None:
            lines.append(f"| {r['ticker']} | {r['n']} | — | — | n<{MIN_N_PER_TICKER} |")
            continue
        ci = f"[{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]" if r["ci_lo"] is not None else "—"
        sign = "+" if r["ic"] > 0 else ("−" if r["ic"] < 0 else "0")
        lines.append(f"| {r['ticker']} | {r['n']} | {r['ic']:+.4f} | {ci} | {sign} |")
    lines.append("")
    lines.append("### Per-period within-ticker median IC\n")
    lines.append("| Period | n tickers (n≥5) | median IC | n_pos | n_neg |")
    lines.append("|---|---:|---:|---:|---:|")
    for r in per_period:
        med = f"{r['median_ic']:+.4f}" if r["median_ic"] is not None else "—"
        lines.append(f"| {r['period']} | {r['n_tickers']} | {med} | {r['n_pos']} | {r['n_neg']} |")
    lines.append("")
    return lines


def main() -> int:
    lines: list[str] = []
    lines.append(f"# Within-ticker artifact check — {datetime.utcnow().date().isoformat()}\n")
    lines.append(
        "## Question\n\n"
        "The within-ticker IC column added to `scripts/evaluate_signals.py` surfaced 3 candidates "
        "where the within-ticker median IC was materially stronger than the aggregate IC. "
        "Most striking: `market_report bull_keyword_count` showed within-ticker IC -0.489 with "
        "9 of 9 tickers negative — unanimous direction agreement.\n\n"
        "Are these REAL within-ticker predictors, or do they fall apart under closer artifact "
        "scrutiny (per-ticker bootstrap CIs include zero, period-instability, within-ticker "
        "permutation null is reachable)?\n"
    )
    lines.append("## Method\n")
    lines.append(
        "For each candidate `(signal, feature)` pair:\n"
        "1. Pull all cached rows; compute featurizer + 90d forward α (post-buffer-fix)\n"
        f"2. Per-ticker IC + bootstrap 95% CI (n={N_BOOTSTRAPS})\n"
        f"3. **Within-ticker permutation test** (n={N_PERMUTATIONS}): shuffle α INDEPENDENTLY "
        "within each ticker, then recompute the within-ticker median IC. This preserves "
        "between-ticker structure and tests only the within-ticker null. Three p-values:\n"
        "   - two-sided: shuffled |median| ≥ |observed|\n"
        "   - one-sided: shuffled median in observed direction\n"
        "   - unanimous-direction: shuffled max(n_pos, n_neg) ≥ observed\n"
        "4. Per-period within-ticker stability (Q3'25 / Q4'25 / Q1'26)\n"
    )

    for c in CANDIDATES:
        print(f"\n[{c.signal_id} × {c.name}] loading...")
        by_ticker, meta = load_pairs_by_ticker(c)
        n_total = sum(len(v) for v in by_ticker.values())
        print(f"[{c.signal_id} × {c.name}] {len(by_ticker)} tickers, {n_total} total rows")
        if n_total < 30:
            print("  → insufficient data, skipping")
            continue

        per_ticker = per_ticker_ics(by_ticker)
        print(f"[{c.signal_id} × {c.name}] running {N_PERMUTATIONS} within-ticker permutations...")
        perm = within_ticker_permutation_test(by_ticker, N_PERMUTATIONS)
        observed_median, p_two, p_one, p_unanimous = perm
        print(
            f"  → median IC = {observed_median:+.4f}, p_two={p_two:.4f}, p_one={p_one:.4f}, p_unanimous={p_unanimous:.4f}"
        )
        per_period = per_period_within(by_ticker)
        lines.extend(render_one(c, per_ticker, perm, per_period))

    lines.append("## Verdict\n")
    lines.append("(Verdict added by hand after reviewing tables.)\n")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[out] {OUT_PATH}")
    print("\n" + "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
