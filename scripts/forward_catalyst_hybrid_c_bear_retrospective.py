"""Hybrid C BEAR-SIDE candidate retrospective — inverted boost direction.

Spec 008 shipped Hybrid C as bull-only. The bull-side boost INCREASES
the effective score near earnings (priced-in cases get suppressed more
aggressively when a forward catalyst is imminent).

Bear-side hypothesis (untested in Spec 008): the SAME mechanism direction
HURTS bear-side per the Spec 008 retrofit (-2.52pp at 21d window). Why?
Because earnings often RALLY (or rally-then-fade), so priced-in bear
cases that get an extra suppression bump near earnings are over-fired —
the bear case is fading on the rally, not crystallizing.

Bear-side INVERTED hypothesis (this script tests): for bear commits,
effective_bear_score = max(0, base * (1 - magnitude * boost)) — boost
DECREASES the effective score near earnings. So priced-in bear cases get
LESS suppression near earnings (because bear case is likely to fade
on rally → don't suppress it; let the bear commit play out).

Decision tree:
  - Inverted bear-side IMPROVES net Δα + cohort hit → write Spec 009
    (Hybrid C with directional asymmetry — bull-positive, bear-inverted)
  - Neutral or worse → SKIP spec; document direction is wrong;
    Spec 008's bull-only stays the recommended config
  - Mixed (improves discrim but hurts net Δα) → shadow-mode-first
    candidate per Constitution VIII v1.4.0 criterion 3 escape hatch

Zero LLM cost — reuses cached Class 3 Opus scores. Free yfinance.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402

CLASS3_CSV = Path("claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.csv")
OUT_MD = Path("claudedocs/forward-catalyst-hybrid-c-bear-retrospective-2026-05-06.md")
OUT_CSV = Path("claudedocs/forward-catalyst-hybrid-c-bear-retrospective-2026-05-06.csv")

BULLISH_RATINGS = {"Buy", "Overweight"}
BEARISH_RATINGS = {"Underweight", "Sell"}

DEFAULT_WINDOWS = (7, 14, 21)
DEFAULT_MAGNITUDES = (0.5, 1.0, 2.0)
DEFAULT_BULL_THRESHOLD = DEFAULT_CONFIG["forward_catalyst_bull_threshold"]
DEFAULT_BEAR_THRESHOLD = DEFAULT_CONFIG["forward_catalyst_bear_threshold"]


def _build_earnings_cache(tickers: list[str]) -> dict[str, list[datetime]]:
    cache: dict[str, list[datetime]] = {}
    for t in tickers:
        try:
            ed = yf.Ticker(t).earnings_dates
            if ed is None or ed.empty:
                cache[t] = []
                continue
            cache[t] = sorted(ed.index.tz_convert(None).to_pydatetime().tolist())
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] earnings_dates fetch failed for {t}: {exc}")
            cache[t] = []
    return cache


def _days_to_next_earnings(
    ticker: str,
    trade_date: str,
    cache: dict[str, list[datetime]],
) -> int | None:
    try:
        td = datetime.fromisoformat(trade_date)
    except ValueError:
        return None
    upcoming = [e for e in cache.get(ticker, []) if e >= td]
    if not upcoming:
        return None
    return (upcoming[0] - td).days


def _calendar_boost(days_to_earnings: int | None, window: int) -> float:
    if days_to_earnings is None or days_to_earnings < 0:
        return 0.0
    if days_to_earnings >= window:
        return 0.0
    return 1.0 - (days_to_earnings / window)


def _effective_bear_inverted(
    base_score: float, days_to_earnings: int | None, window: int, magnitude: float
) -> float:
    """INVERTED bear formula: effective = max(0, base * (1 - magnitude * boost)).

    Boost = 1.0 at earnings day → effective = base * (1 - magnitude).
    At magnitude=0.5: effective = base * 0.5 (HALVED near earnings).
    At magnitude=1.0: effective = base * 0 = 0 (full suppression).
    """
    boost = _calendar_boost(days_to_earnings, window)
    return max(0.0, base_score * (1.0 - magnitude * boost))


def _eval_bear_gate(
    df: pd.DataFrame,
    bear_threshold: float,
) -> dict:
    """Compute bear-side gate criteria using `eff_bear_score` column."""
    df = df.copy()
    df["fire_bear"] = (df["eff_bear_score"] > bear_threshold) & df["rating"].isin(BEARISH_RATINGS)

    cohort_b = df[df["sample_class"] == "cohort_b_bear_target"]
    bear_commits = df[df["rating"].isin(BEARISH_RATINGS)]

    bear_baseline = bear_commits["alpha_vs_spy_pct"].mean()
    bear_kept_alpha = bear_commits[~bear_commits["fire_bear"]]["alpha_vs_spy_pct"].mean()
    # For bear: HIGH α is wrong-direction; filter HELPS by removing high-α commits
    # net Δα = baseline - kept; positive = filter helps
    bear_net_dalpha = bear_baseline - bear_kept_alpha if not pd.isna(bear_kept_alpha) else 0.0

    bear_cohort_fired = cohort_b["fire_bear"].sum()
    bear_cohort_hit_rate = bear_cohort_fired / len(cohort_b) * 100 if len(cohort_b) else 0.0

    bear_fired = bear_commits[bear_commits["fire_bear"]]
    bear_fired_cohort = bear_fired[bear_fired["sample_class"] == "cohort_b_bear_target"]
    bear_fired_winner = bear_fired[bear_fired["sample_class"] == "control_bear_winner"]
    bear_fired_cohort_alpha = (
        bear_fired_cohort["alpha_vs_spy_pct"].mean()
        if not bear_fired_cohort.empty
        else float("nan")
    )
    bear_fired_winner_alpha = (
        bear_fired_winner["alpha_vs_spy_pct"].mean()
        if not bear_fired_winner.empty
        else float("nan")
    )
    bear_discrim = (
        (bear_fired_cohort_alpha - bear_fired_winner_alpha)
        if (not bear_fired_cohort.empty and not bear_fired_winner.empty)
        else float("nan")
    )

    return {
        "bear_n_fired": int(bear_commits["fire_bear"].sum()),
        "bear_baseline_alpha": bear_baseline,
        "bear_kept_alpha": bear_kept_alpha,
        "bear_net_dalpha": bear_net_dalpha,
        "bear_cohort_hit_rate": bear_cohort_hit_rate,
        "bear_discrim": bear_discrim,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bear-threshold", type=float, default=DEFAULT_BEAR_THRESHOLD)
    parser.add_argument(
        "--windows",
        default=",".join(str(w) for w in DEFAULT_WINDOWS),
    )
    parser.add_argument(
        "--magnitudes",
        default=",".join(str(m) for m in DEFAULT_MAGNITUDES),
    )
    args = parser.parse_args()

    windows = tuple(int(w) for w in args.windows.split(","))
    magnitudes = tuple(float(m) for m in args.magnitudes.split(","))

    print("# Hybrid C BEAR-SIDE retrofit — INVERTED boost direction")
    print()
    print(f"Bear threshold: {args.bear_threshold} (production-config)")
    print(f"Boost windows (cal days): {windows}")
    print(f"Boost magnitudes: {magnitudes}")
    print()
    print("Mechanism: effective_bear = max(0, base * (1 - magnitude * boost))")
    print("  → near earnings, bear score is REDUCED (less likely to fire)")
    print("  → hypothesis: earnings often rally; priced-in bear cases fade")
    print()

    if not CLASS3_CSV.exists():
        print(f"[fatal] Class 3 Opus CSV missing: {CLASS3_CSV}")
        return

    df = pd.read_csv(CLASS3_CSV)
    df = df.dropna(subset=["bull_case_priced_in", "bear_case_priced_in", "alpha_vs_spy_pct"]).copy()
    print(f"Loaded {len(df)} rows from {CLASS3_CSV}")

    print()
    print("Building earnings cache (one yfinance call per unique ticker)...")
    tickers = sorted(df["ticker"].unique().tolist())
    cache = _build_earnings_cache(tickers)
    n_with_earnings = sum(1 for t in tickers if cache.get(t))
    print(f"  {n_with_earnings} of {len(tickers)} have earnings_dates available")

    df["days_to_earnings"] = df.apply(
        lambda r: _days_to_next_earnings(r["ticker"], r["trade_date"], cache),
        axis=1,
    )

    print()

    # Class 3-alone bear baseline (no boost)
    df["eff_bear_score"] = df["bear_case_priced_in"]
    baseline = _eval_bear_gate(df, args.bear_threshold)

    print(f"## Class 3-alone bear baseline (T_bear={args.bear_threshold})")
    print()
    print(
        f"  Bear: n_fired={baseline['bear_n_fired']}, kept_α={baseline['bear_kept_alpha']:+.2f}%, "
        f"net Δα={baseline['bear_net_dalpha']:+.2f}pp, cohort hit={baseline['bear_cohort_hit_rate']:.1f}%, "
        f"discrim={baseline['bear_discrim']:+.2f}pp"
    )
    print()

    # Sweep
    print("## Hybrid C BEAR INVERTED sweep (window × magnitude)")
    print()
    print("| window | magnitude | bear n_fired | bear net Δα | bear hit% | bear discrim |")
    print("|---|---|---|---|---|---|")

    sweep_rows = []
    for w in windows:
        for m in magnitudes:
            df_h = df.copy()
            df_h["eff_bear_score"] = df_h.apply(
                lambda r, _w=w, _m=m: _effective_bear_inverted(
                    r["bear_case_priced_in"], r["days_to_earnings"], _w, _m
                ),
                axis=1,
            )
            metrics = _eval_bear_gate(df_h, args.bear_threshold)
            print(
                f"| {w}d | {m:.1f}x | {metrics['bear_n_fired']} | {metrics['bear_net_dalpha']:+.2f}pp | "
                f"{metrics['bear_cohort_hit_rate']:.1f}% | {metrics['bear_discrim']:+.2f}pp |"
            )
            sweep_rows.append({"window": w, "magnitude": m, **metrics})

    sweep_df = pd.DataFrame(sweep_rows)
    sweep_df["bear_net_improvement"] = sweep_df["bear_net_dalpha"] - baseline["bear_net_dalpha"]
    sweep_df["bear_hit_improvement"] = (
        sweep_df["bear_cohort_hit_rate"] - baseline["bear_cohort_hit_rate"]
    )
    sweep_df["bear_discrim_improvement"] = sweep_df["bear_discrim"] - baseline["bear_discrim"]

    print()
    print("## Improvement vs Class 3-alone bear baseline")
    print()
    print("| window | magnitude | bear Δα Δ | bear hit Δ | bear discrim Δ |")
    print("|---|---|---|---|---|")
    for _, r in sweep_df.iterrows():
        print(
            f"| {int(r['window'])}d | {r['magnitude']:.1f}x | "
            f"{r['bear_net_improvement']:+.2f}pp | {r['bear_hit_improvement']:+.1f}% | "
            f"{r['bear_discrim_improvement']:+.2f}pp |"
        )

    print()
    # Best by net_dalpha improvement (primary criterion for bear-side)
    best = sweep_df.loc[sweep_df["bear_net_improvement"].idxmax()]
    print(
        f"## Best bear-inverted config: window={int(best['window'])}d, magnitude={best['magnitude']:.1f}x"
    )
    print(f"  Bear net Δα change: {best['bear_net_improvement']:+.2f}pp")
    print(f"  Bear cohort hit change: {best['bear_hit_improvement']:+.1f}%")
    print(f"  Bear discrim change: {best['bear_discrim_improvement']:+.2f}pp")

    # Constitution VIII v1.4.0 forward-catalyst-class gate evaluation
    # Bear discrim must be +5pp ABSOLUTE (not delta), hit ≥60%, net Δα ≥+0.5pp
    bear_discrim_abs = best["bear_discrim"]
    bear_hit_abs = best["bear_cohort_hit_rate"]
    bear_net_abs = best["bear_net_dalpha"]
    print()
    print(
        "## Constitution VIII v1.4.0 forward-catalyst-class gate (absolute values at best config)"
    )
    print(
        f"  Discrim: {bear_discrim_abs:+.2f}pp (gate: ≥+5pp PRIMARY) {'PASS' if bear_discrim_abs >= 5 else 'FAIL'}"
    )
    print(
        f"  Cohort hit: {bear_hit_abs:.1f}% (gate: ≥60%) {'PASS' if bear_hit_abs >= 60 else 'FAIL'}"
    )
    print(
        f"  Net Δα: {bear_net_abs:+.2f}pp (gate: ≥+0.5pp OR shadow-mode-first) {'PASS' if bear_net_abs >= 0.5 else 'criteria-1+2-shadow-mode-first if 1+2 pass'}"
    )

    primary_pass = bear_discrim_abs >= 5
    cohort_pass = bear_hit_abs >= 60
    net_pass = bear_net_abs >= 0.5
    improvement_pass = best["bear_net_improvement"] > 0.5 or best["bear_hit_improvement"] > 5

    print()
    print("## Verdict")
    if primary_pass and cohort_pass and net_pass and improvement_pass:
        verdict = "PASS — invoke Spec 009 (Hybrid C bear inverted)"
    elif primary_pass and cohort_pass and improvement_pass:
        verdict = "PASS-shadow — invoke Spec 009 with shadow-mode-first condition"
    elif improvement_pass:
        verdict = "PARTIAL — improvement over Class 3 alone, but absolute gate FAILS; SKIP spec"
    else:
        verdict = "SKIP — bear-inverted does NOT improve over Class 3 baseline"
    print(f"  {verdict}")

    # Save CSV + Markdown
    sweep_df.to_csv(OUT_CSV, index=False)
    print()
    print(f"Wrote {OUT_CSV}")

    md = [
        f"# Hybrid C BEAR-SIDE retrofit — INVERTED boost — {pd.Timestamp.now().date().isoformat()}",
        "",
        "**Config source**: production (`tradingagents.default_config.DEFAULT_CONFIG`).",
        f"Bear threshold: `{args.bear_threshold}` (= spec 007 default).",
        "",
        "**Hypothesis**: For bear commits, INVERTED boost direction "
        "(`effective = max(0, base * (1 - magnitude * boost))`) — boost DECREASES the effective bear "
        "score near earnings. Rationale: earnings often rally → priced-in bear cases fade as the "
        "rally arrives. Suppressing bear commits LESS aggressively near earnings (vs Spec 008's "
        "bull-direction boost which suppresses MORE) lets bear cases play out their natural fade-pattern.",
        "",
        "**Mechanism**: `effective_bear = max(0, bear_case_priced_in * (1 - magnitude * boost))` "
        "where `boost = max(0, 1 - days_to_earnings / window)`.",
        "",
        f"**Cohort**: {len(df)} commits (cached Class 3 Opus scores + days-to-next-earnings via "
        f"yfinance for {n_with_earnings} of {len(tickers)} unique tickers).",
        "",
        "## Class 3-alone bear baseline",
        "",
        f"- Bear: n_fired={baseline['bear_n_fired']}, kept α={baseline['bear_kept_alpha']:+.2f}%, "
        f"net Δα={baseline['bear_net_dalpha']:+.2f}pp, cohort hit={baseline['bear_cohort_hit_rate']:.1f}%, "
        f"discrim={baseline['bear_discrim']:+.2f}pp",
        "",
        "## Hybrid C BEAR INVERTED sweep — improvement vs baseline",
        "",
        "| window | magnitude | bear Δα Δ | bear hit Δ | bear discrim Δ |",
        "|---|---|---|---|---|",
    ]
    for _, r in sweep_df.iterrows():
        md.append(
            f"| {int(r['window'])}d | {r['magnitude']:.1f}x | "
            f"{r['bear_net_improvement']:+.2f}pp | {r['bear_hit_improvement']:+.1f}% | "
            f"{r['bear_discrim_improvement']:+.2f}pp |"
        )

    md.extend(
        [
            "",
            f"## Best inverted config: window={int(best['window'])}d, magnitude={best['magnitude']:.1f}x",
            "",
            f"- Bear net Δα change vs baseline: {best['bear_net_improvement']:+.2f}pp",
            f"- Bear cohort hit change vs baseline: {best['bear_hit_improvement']:+.1f}%",
            f"- Bear discrim change vs baseline: {best['bear_discrim_improvement']:+.2f}pp",
            f"- Absolute bear net Δα: {bear_net_abs:+.2f}pp",
            f"- Absolute bear cohort hit: {bear_hit_abs:.1f}%",
            f"- Absolute bear discrim: {bear_discrim_abs:+.2f}pp",
            "",
            "## Constitution VIII v1.4.0 forward-catalyst-class gate",
            "",
            f"- Discrim ≥ +5pp PRIMARY: **{'PASS' if primary_pass else 'FAIL'}** ({bear_discrim_abs:+.2f}pp)",
            f"- Cohort hit rate ≥ 60%: **{'PASS' if cohort_pass else 'FAIL'}** ({bear_hit_abs:.1f}%)",
            f"- Net Δα ≥ +0.5pp OR shadow-mode-first: **{'PASS' if net_pass else 'shadow-mode-first if criteria 1+2 pass'}** ({bear_net_abs:+.2f}pp)",
            f"- Improves over Class 3 baseline: **{'YES' if improvement_pass else 'NO'}**",
            "",
            f"## Verdict — {verdict}",
            "",
            "## Reproducibility",
            "",
            "```",
            "python scripts/forward_catalyst_hybrid_c_bear_retrospective.py",
            "```",
            "",
            f"Reads cached Class 3 Opus scores from `{CLASS3_CSV}` + free yfinance fetches. Zero LLM cost.",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
