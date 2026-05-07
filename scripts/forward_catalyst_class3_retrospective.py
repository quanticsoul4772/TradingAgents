"""Class 3 forward-catalyst retrospective — LLM-extracted "case priced in" feature.

Per `claudedocs/forward-catalyst-mechanism-exploration-2026-05-06.md` Class 3
recommendation. Builds an LLM-extracted feature that scores, for each propagate,
how widely the bull case + bear case are already absorbed by the market. The
hypothesis: when a thesis is already priced in, further commits in that
direction are likely to lose because the upside (or downside) is already absorbed.

Mechanism:
  - For each cohort + control commit, load the cached state log
  - Call Haiku with the 4 analyst reports + bull/bear debate
  - Receive structured JSON: {bull_case_priced_in: 0-1, bear_case_priced_in: 0-1, rationale: str}
  - For bullish commits: filter would fire when bull_case_priced_in > T_bull
  - For bearish commits: filter would fire when bear_case_priced_in > T_bear
  - Compute discrimination + cohort hit rate + net Δα

Validation gate (per design doc §5):
  1. Discrimination >= 5pp in correct direction (PRIMARY)
  2. Cohort hit rate >= 60%
  3. Net Δα >= +0.5pp OR shadow-mode-first if (3) unmeasurable

Cohorts (loaded from claudedocs/sector-alpha-attribution-2026-05-06.csv):
  A. Bullish ticker_weak (n=27): SUPPRESS Buy/OW; expect bull_case_priced_in HIGH
  B. Bearish ticker_strong (n=18): SUPPRESS UW/Sell; expect bear_case_priced_in HIGH
  Controls: 20+ bullish non-cohort + 20+ bearish non-cohort + 10 Holds (~50)

Cost: ~$0.10-0.20 in Haiku calls (~95 commits × ~3-5K tokens × $0.001/1K ≈ $0.30 ceiling).

Output:
  - claudedocs/forward-catalyst-class3-retrospective-2026-05-06.csv (per-commit features + alpha)
  - claudedocs/forward-catalyst-class3-retrospective-2026-05-06.md (verdict + tables)

Usage:
    python scripts/forward_catalyst_class3_retrospective.py
    python scripts/forward_catalyst_class3_retrospective.py --max-controls 50 --threshold 0.7
    python scripts/forward_catalyst_class3_retrospective.py --dry-run  # plans calls without invoking LLM
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

LOGS_DIR = Path.home() / ".tradingagents" / "logs"
ATTRIBUTION_CSV = Path("claudedocs/sector-alpha-attribution-2026-05-06.csv")
DEFAULT_MODEL = "claude-haiku-4-5"

# Per-model output paths so Haiku and Opus runs don't clobber each other.
_MODEL_SLUGS = {
    "claude-haiku-4-5": "",  # default: paths without slug (original Haiku run)
    "claude-opus-4-7": "-opus",
    "claude-sonnet-4-6": "-sonnet",
}


def _output_paths(model: str) -> tuple[Path, Path]:
    """Return (csv_path, md_path) for the given model. Uses a slug so different
    models write to distinct paths and don't clobber prior runs."""
    slug = _MODEL_SLUGS.get(model, f"-{model.replace('claude-', '').replace('.', '_')}")
    csv = Path(f"claudedocs/forward-catalyst-class3{slug}-retrospective-2026-05-06.csv")
    md = Path(f"claudedocs/forward-catalyst-class3{slug}-retrospective-2026-05-06.md")
    return csv, md


BULLISH_RATINGS = {"Buy", "Overweight"}
BEARISH_RATINGS = {"Underweight", "Sell"}


class CasePricedInScore(BaseModel):
    """Structured output for the Class 3 LLM-extracted feature."""

    bull_case_priced_in: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "How widely is the bull case ALREADY ACCEPTED by the market for this ticker, "
            "given the analyst evidence? 0 = no consensus / contrarian bullish setup, "
            "0.5 = mixed acceptance, 1 = thesis is universally accepted / well-known / "
            "already-priced-in. High values mean further bullish commits face limited "
            "upside because the market has already absorbed the thesis."
        ),
    )
    bear_case_priced_in: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "How widely is the bear case ALREADY ACCEPTED by the market for this ticker. "
            "Same scale as bull_case_priced_in. High values mean further bearish commits "
            "face limited downside because the bearish thesis is already absorbed."
        ),
    )
    rationale: str = Field(
        max_length=2000,
        description=(
            "One short paragraph (3-5 sentences) explaining the two scores. Reference "
            "specific evidence from the analyst reports. Do NOT pick a direction; you are "
            "scoring how priced-in each side is, not which side is right."
        ),
    )


# ---- LLM client helpers ---------------------------------------------------


def _get_anthropic_llm(model: str):
    """Build an Anthropic client for the given model. Requires ANTHROPIC_API_KEY."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Export your key or run with --dry-run to skip LLM calls."
        )
    from tradingagents.llm_clients.factory import create_llm_client

    client = create_llm_client("anthropic", model)
    return client.get_llm()


def _build_prompt(state_log: dict, ticker: str, trade_date: str) -> str:
    """Build the retrofit prompt from a cached state log."""
    market = state_log.get("market_report", "") or "[empty]"
    sentiment = state_log.get("sentiment_report", "") or "[empty]"
    news = state_log.get("news_report", "") or "[empty]"
    fundamentals = state_log.get("fundamentals_report", "") or "[empty]"
    investment_plan = state_log.get("investment_plan", "") or "[empty]"
    debate = state_log.get("investment_debate_state", {}).get("history", "") or "[empty]"

    # Truncate each report to keep total prompt under ~12K tokens (Haiku
    # has 200K context but cost scales with input; 12K is plenty).
    def _trunc(s: str, max_chars: int = 6000) -> str:
        if len(s) <= max_chars:
            return s
        return s[:max_chars] + f"\n\n[...truncated, original length {len(s)} chars]"

    return f"""You are evaluating how widely the bull case AND the bear case for a ticker are
ALREADY ACCEPTED BY THE MARKET, given the evidence collected by a multi-agent
trading framework. You are NOT picking a direction. You are scoring HOW PRICED-IN
each side's thesis is.

The empirical motivation: prior research found that backward-looking price filters
fail to discriminate cohort losers from similar-pattern winners. The hypothesis
this retrospective tests is that when a thesis (bull or bear) is already widely
absorbed by the market, further commits in that direction lose alpha because the
upside (or downside) has already been priced in.

**Ticker**: {ticker}
**Trade date**: {trade_date}

---

**Market analyst report** (price action + technicals):
{_trunc(market)}

---

**News analyst report** (recent news + sentiment):
{_trunc(news)}

---

**Sentiment / social analyst report**:
{_trunc(sentiment)}

---

**Fundamentals analyst report** (financials + business):
{_trunc(fundamentals)}

---

**Bull/bear debate history** (researcher synthesis):
{_trunc(debate, max_chars=4000)}

---

**Research Manager's investment plan** (the bridge synthesis):
{_trunc(investment_plan, max_chars=2000)}

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


def _score_with_llm(llm, state_log: dict, ticker: str, trade_date: str) -> CasePricedInScore | None:
    """Call Haiku with the structured-output schema. Returns None on failure."""
    prompt = _build_prompt(state_log, ticker, trade_date)
    try:
        structured_llm = llm.with_structured_output(CasePricedInScore)
        return structured_llm.invoke(prompt)
    except Exception as exc:
        print(f"  [warn] LLM call failed for {ticker}/{trade_date}: {exc}")
        return None


# ---- Cohort + control selection -------------------------------------------


def _load_cohort_and_controls(max_controls_per_class: int = 20) -> pd.DataFrame:
    """Load cohort + control commits from the attribution CSV.

    Cohort A (target): rating in (Buy, Overweight) AND cell == 'ticker_weak'
    Cohort B (target): rating in (Underweight, Sell) AND cell == 'ticker_strong'
    Controls: bullish + bearish non-cohort commits (sampled deterministically)
    """
    if not ATTRIBUTION_CSV.exists():
        raise FileNotFoundError(f"Attribution CSV not found: {ATTRIBUTION_CSV}")
    df = pd.read_csv(ATTRIBUTION_CSV)

    # Cohort A
    cohort_a = df[(df["rating"].isin(BULLISH_RATINGS)) & (df["cell"] == "ticker_weak")].copy()
    cohort_a["sample_class"] = "cohort_a_bull_target"

    # Cohort B
    cohort_b = df[(df["rating"].isin(BEARISH_RATINGS)) & (df["cell"] == "ticker_strong")].copy()
    cohort_b["sample_class"] = "cohort_b_bear_target"

    # Bullish controls (non-cohort: ticker_strong / sector_tide_up / sector_drag)
    bull_ctrl_pool = df[(df["rating"].isin(BULLISH_RATINGS)) & (df["cell"] != "ticker_weak")].copy()
    bull_ctrl = bull_ctrl_pool.sort_values(["ticker", "trade_date"]).head(max_controls_per_class)
    bull_ctrl["sample_class"] = "control_bull_winner"

    # Bearish controls (non-cohort: ticker_weak / sector_tide_up / sector_drag)
    bear_ctrl_pool = df[
        (df["rating"].isin(BEARISH_RATINGS)) & (df["cell"] != "ticker_strong")
    ].copy()
    bear_ctrl = bear_ctrl_pool.sort_values(["ticker", "trade_date"]).head(max_controls_per_class)
    bear_ctrl["sample_class"] = "control_bear_winner"

    # Hold baselines (smaller sample for distribution check)
    hold_pool = df[df["rating"] == "Hold"].copy()
    hold_ctrl = hold_pool.sort_values(["ticker", "trade_date"]).head(10)
    hold_ctrl["sample_class"] = "control_hold"

    out = pd.concat([cohort_a, cohort_b, bull_ctrl, bear_ctrl, hold_ctrl], ignore_index=True)
    return out


# ---- State-log loader -----------------------------------------------------


def _load_state_log(ticker: str, trade_date: str) -> dict | None:
    """Load the cached state log for a (ticker, date). Returns None if missing."""
    log_path = (
        LOGS_DIR / ticker / "TradingAgentsStrategy_logs" / f"full_states_log_{trade_date}.json"
    )
    if not log_path.exists():
        return None
    try:
        return json.loads(log_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  [warn] failed to load state log {log_path}: {exc}")
        return None


# ---- Resume support -------------------------------------------------------


def _load_resume_csv(csv_path: Path) -> pd.DataFrame | None:
    """Load the existing output CSV if present, for resume."""
    if not csv_path.exists():
        return None
    try:
        return pd.read_csv(csv_path)
    except Exception:
        return None


# ---- Validation gate analysis ---------------------------------------------


def _evaluate_gate(
    df: pd.DataFrame,
    bull_threshold: float,
    bear_threshold: float,
) -> dict:
    """Compute discrimination + cohort hit rate + net Δα at the configured thresholds.

    Filter logic:
      - Bullish commit fires when bull_case_priced_in > bull_threshold
      - Bearish commit fires when bear_case_priced_in > bear_threshold
    """
    valid = df.dropna(subset=["bull_case_priced_in", "bear_case_priced_in", "alpha_vs_spy_pct"])

    # Bullish side
    bull = valid[valid["rating"].isin(BULLISH_RATINGS)].copy()
    bull["fire"] = bull["bull_case_priced_in"] > bull_threshold
    bull_fired = bull[bull["fire"]]
    bull_kept = bull[~bull["fire"]]

    bull_baseline_alpha = bull["alpha_vs_spy_pct"].mean() if not bull.empty else float("nan")
    bull_kept_alpha = bull_kept["alpha_vs_spy_pct"].mean() if not bull_kept.empty else float("nan")
    bull_fired_alpha = (
        bull_fired["alpha_vs_spy_pct"].mean() if not bull_fired.empty else float("nan")
    )
    bull_net_dalpha = bull_kept_alpha - bull_baseline_alpha if not bull_kept.empty else 0.0

    # Bull cohort hit rate
    bull_cohort = bull[bull["sample_class"] == "cohort_a_bull_target"]
    bull_cohort_fired = bull_cohort[bull_cohort["fire"]]
    bull_cohort_hit_rate = (
        len(bull_cohort_fired) / len(bull_cohort) * 100.0 if not bull_cohort.empty else 0.0
    )

    # Bull discrimination: fired-cohort α magnitude vs fired-non-cohort α magnitude
    bull_fired_cohort = bull_fired[bull_fired["sample_class"] == "cohort_a_bull_target"]
    bull_fired_noncohort = bull_fired[bull_fired["sample_class"] == "control_bull_winner"]
    bull_fired_cohort_alpha = (
        bull_fired_cohort["alpha_vs_spy_pct"].mean()
        if not bull_fired_cohort.empty
        else float("nan")
    )
    bull_fired_noncohort_alpha = (
        bull_fired_noncohort["alpha_vs_spy_pct"].mean()
        if not bull_fired_noncohort.empty
        else float("nan")
    )
    # Discrimination: cohort fires should have NEGATIVE α (we want to suppress losers);
    # non-cohort fires should have POSITIVE α (these are the winners we'd incorrectly
    # suppress). Discrimination magnitude = noncohort_α − cohort_α; positive means
    # filter is correctly catching losers and not catching winners.
    bull_discrimination = (
        bull_fired_noncohort_alpha - bull_fired_cohort_alpha
        if (not bull_fired_cohort.empty and not bull_fired_noncohort.empty)
        else float("nan")
    )

    # Bearish side (symmetric, but for bearish commits HIGHER α means the bear
    # call was wrong; cohort fires should have HIGH α, non-cohort fires LOW α)
    bear = valid[valid["rating"].isin(BEARISH_RATINGS)].copy()
    bear["fire"] = bear["bear_case_priced_in"] > bear_threshold
    bear_fired = bear[bear["fire"]]
    bear_kept = bear[~bear["fire"]]

    bear_baseline_alpha = bear["alpha_vs_spy_pct"].mean() if not bear.empty else float("nan")
    bear_kept_alpha = bear_kept["alpha_vs_spy_pct"].mean() if not bear_kept.empty else float("nan")
    bear_fired_alpha = (
        bear_fired["alpha_vs_spy_pct"].mean() if not bear_fired.empty else float("nan")
    )
    # For BEAR: high α means the bear call was wrong; filter HELPS by removing
    # high-α (wrong-call) commits. So net Δα = baseline − kept; positive means
    # filter correctly removed wrong-direction bear commits.
    bear_net_dalpha = bear_baseline_alpha - bear_kept_alpha if not bear_kept.empty else 0.0

    bear_cohort = bear[bear["sample_class"] == "cohort_b_bear_target"]
    bear_cohort_fired = bear_cohort[bear_cohort["fire"]]
    bear_cohort_hit_rate = (
        len(bear_cohort_fired) / len(bear_cohort) * 100.0 if not bear_cohort.empty else 0.0
    )

    bear_fired_cohort = bear_fired[bear_fired["sample_class"] == "cohort_b_bear_target"]
    bear_fired_noncohort = bear_fired[bear_fired["sample_class"] == "control_bear_winner"]
    bear_fired_cohort_alpha = (
        bear_fired_cohort["alpha_vs_spy_pct"].mean()
        if not bear_fired_cohort.empty
        else float("nan")
    )
    bear_fired_noncohort_alpha = (
        bear_fired_noncohort["alpha_vs_spy_pct"].mean()
        if not bear_fired_noncohort.empty
        else float("nan")
    )
    # For BEAR cohort: high-α fires are correct (suppress wrong-direction bear).
    # Discrimination = cohort_α − noncohort_α; positive means filter catches
    # rallying cohort tickers and not catches the actually-bearish non-cohort.
    bear_discrimination = (
        bear_fired_cohort_alpha - bear_fired_noncohort_alpha
        if (not bear_fired_cohort.empty and not bear_fired_noncohort.empty)
        else float("nan")
    )

    return {
        "bull_threshold": bull_threshold,
        "bear_threshold": bear_threshold,
        "bull_n": len(bull),
        "bull_n_fired": len(bull_fired),
        "bull_baseline_alpha": bull_baseline_alpha,
        "bull_kept_alpha": bull_kept_alpha,
        "bull_fired_alpha": bull_fired_alpha,
        "bull_net_dalpha": bull_net_dalpha,
        "bull_cohort_hit_rate": bull_cohort_hit_rate,
        "bull_fired_cohort_alpha": bull_fired_cohort_alpha,
        "bull_fired_noncohort_alpha": bull_fired_noncohort_alpha,
        "bull_discrimination": bull_discrimination,
        "bear_n": len(bear),
        "bear_n_fired": len(bear_fired),
        "bear_baseline_alpha": bear_baseline_alpha,
        "bear_kept_alpha": bear_kept_alpha,
        "bear_fired_alpha": bear_fired_alpha,
        "bear_net_dalpha": bear_net_dalpha,
        "bear_cohort_hit_rate": bear_cohort_hit_rate,
        "bear_fired_cohort_alpha": bear_fired_cohort_alpha,
        "bear_fired_noncohort_alpha": bear_fired_noncohort_alpha,
        "bear_discrimination": bear_discrimination,
    }


# ---- Main -----------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-controls",
        type=int,
        default=20,
        help="Max controls per class (bull-winner / bear-winner). Default 20.",
    )
    parser.add_argument(
        "--bull-thresholds",
        default="0.5,0.6,0.7,0.8",
        help="Comma-separated thresholds for bull_case_priced_in (default: 0.5,0.6,0.7,0.8)",
    )
    parser.add_argument(
        "--bear-thresholds",
        default="0.5,0.6,0.7,0.8",
        help="Comma-separated thresholds for bear_case_priced_in (default: 0.5,0.6,0.7,0.8)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan calls without invoking LLM; useful for cost estimation",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Re-score every commit even if already in the output CSV",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=(
            f"Anthropic model to use. Default: {DEFAULT_MODEL}. Override with "
            "claude-opus-4-7 for more discriminating scoring (~10x cost)."
        ),
    )
    args = parser.parse_args()

    bull_thresholds = tuple(sorted(float(t) for t in args.bull_thresholds.split(",")))
    bear_thresholds = tuple(sorted(float(t) for t in args.bear_thresholds.split(",")))
    out_csv, out_md = _output_paths(args.model)

    print("# Class 3 forward-catalyst retrospective — LLM-extracted 'case priced in' feature")
    print()
    print(f"Model: {args.model}")
    print(f"Output CSV: {out_csv}")
    print(f"Output MD: {out_md}")
    print(f"Max controls per class: {args.max_controls}")
    print(f"Bull thresholds: {bull_thresholds}")
    print(f"Bear thresholds: {bear_thresholds}")
    print(f"Dry run: {args.dry_run}")
    print()

    print("Loading cohort + controls...")
    df = _load_cohort_and_controls(max_controls_per_class=args.max_controls)
    print(f"  Total commits to score: {len(df)}")
    print(
        f"    cohort_a (bullish ticker_weak target): {(df['sample_class'] == 'cohort_a_bull_target').sum()}"
    )
    print(
        f"    cohort_b (bearish ticker_strong target): {(df['sample_class'] == 'cohort_b_bear_target').sum()}"
    )
    print(f"    control_bull_winner: {(df['sample_class'] == 'control_bull_winner').sum()}")
    print(f"    control_bear_winner: {(df['sample_class'] == 'control_bear_winner').sum()}")
    print(f"    control_hold: {(df['sample_class'] == 'control_hold').sum()}")

    # Resume support
    resume = _load_resume_csv(out_csv) if not args.no_resume else None
    if resume is not None:
        print(f"  Resume: {len(resume)} rows already in {out_csv}")
        already_done = set(
            zip(resume["ticker"].astype(str), resume["trade_date"].astype(str), strict=False)
        )
    else:
        already_done = set()

    # Cost estimate (Haiku ~$0.002/call ceiling; Opus ~10x more)
    n_to_call = len(df) - sum(
        1 for _, r in df.iterrows() if (r["ticker"], r["trade_date"]) in already_done
    )
    cost_per_call = 0.002 if "haiku" in args.model.lower() else 0.025
    est_cost = n_to_call * cost_per_call
    print(f"  LLM calls to make: {n_to_call} (est cost ~${est_cost:.2f} at {args.model})")

    if args.dry_run:
        print()
        print("[dry-run] Skipping LLM calls. Re-run without --dry-run to score.")
        return

    if n_to_call == 0:
        print("  All rows already scored; skipping LLM calls.")
    else:
        # Initialize the configured Anthropic model
        print()
        print(f"Initializing {args.model} client...")
        llm = _get_anthropic_llm(args.model)
        print("  Ready.")

        # Build/extend the results
        results = resume.to_dict("records") if resume is not None else []
        for i, r in df.iterrows():
            key = (r["ticker"], r["trade_date"])
            if key in already_done:
                continue
            print(f"  [{i + 1}/{len(df)}] {r['ticker']} / {r['trade_date']} ({r['sample_class']})")
            state_log = _load_state_log(r["ticker"], r["trade_date"])
            if state_log is None:
                print("    [skip] state log not found")
                results.append(
                    {
                        **r.to_dict(),
                        "bull_case_priced_in": None,
                        "bear_case_priced_in": None,
                        "rationale": None,
                        "skipped": "no_state_log",
                    }
                )
                continue
            score = _score_with_llm(llm, state_log, r["ticker"], r["trade_date"])
            if score is None:
                results.append(
                    {
                        **r.to_dict(),
                        "bull_case_priced_in": None,
                        "bear_case_priced_in": None,
                        "rationale": None,
                        "skipped": "llm_failed",
                    }
                )
            else:
                results.append(
                    {
                        **r.to_dict(),
                        "bull_case_priced_in": score.bull_case_priced_in,
                        "bear_case_priced_in": score.bear_case_priced_in,
                        "rationale": score.rationale,
                        "skipped": None,
                    }
                )
            # Save after every call (success OR failure) — cheap insurance against crashes
            pd.DataFrame(results).to_csv(out_csv, index=False)

        scored = pd.DataFrame(results)
    # If resume only (no new calls), use the resume frame directly
    if resume is not None and n_to_call == 0:
        scored = resume

    print()
    print(f"  Total rows in {out_csv}: {len(scored)}")
    valid_scored = scored.dropna(subset=["bull_case_priced_in", "bear_case_priced_in"])
    print(f"  Successfully scored: {len(valid_scored)} (skipped {len(scored) - len(valid_scored)})")

    if valid_scored.empty:
        print("[fatal] no successfully-scored commits; cannot evaluate gate")
        return

    # Score distribution summary
    print()
    print("## bull_case_priced_in distribution")
    print(valid_scored["bull_case_priced_in"].describe().to_string())
    print()
    print("## bear_case_priced_in distribution")
    print(valid_scored["bear_case_priced_in"].describe().to_string())

    # Per-class mean scores
    print()
    print("## Per-sample-class mean scores")
    print()
    print("| sample_class | n | mean_bull_priced_in | mean_bear_priced_in |")
    print("|---|---|---|---|")
    for cls in sorted(valid_scored["sample_class"].unique()):
        sub = valid_scored[valid_scored["sample_class"] == cls]
        print(
            f"| {cls} | {len(sub)} | "
            f"{sub['bull_case_priced_in'].mean():.3f} | "
            f"{sub['bear_case_priced_in'].mean():.3f} |"
        )

    # Threshold sweep
    print()
    print("## Bull-side threshold sweep (filter fires when bull_case_priced_in > T)")
    print()
    print("| T_bull | n_fired | kept_α | fired_α | net_Δα | cohort_hit_rate | discrim |")
    print("|---|---|---|---|---|---|---|")
    for t in bull_thresholds:
        gate = _evaluate_gate(valid_scored, t, 1.01)  # bear threshold disabled
        print(
            f"| {t:.2f} | {gate['bull_n_fired']} | "
            f"{gate['bull_kept_alpha']:+.2f}% | {gate['bull_fired_alpha']:+.2f}% | "
            f"{gate['bull_net_dalpha']:+.2f}pp | {gate['bull_cohort_hit_rate']:.1f}% | "
            f"{gate['bull_discrimination']:+.2f}pp |"
        )

    print()
    print("## Bear-side threshold sweep (filter fires when bear_case_priced_in > T)")
    print()
    print("| T_bear | n_fired | kept_α | fired_α | net_Δα | cohort_hit_rate | discrim |")
    print("|---|---|---|---|---|---|---|")
    for t in bear_thresholds:
        gate = _evaluate_gate(valid_scored, 1.01, t)
        print(
            f"| {t:.2f} | {gate['bear_n_fired']} | "
            f"{gate['bear_kept_alpha']:+.2f}% | {gate['bear_fired_alpha']:+.2f}% | "
            f"{gate['bear_net_dalpha']:+.2f}pp | {gate['bear_cohort_hit_rate']:.1f}% | "
            f"{gate['bear_discrimination']:+.2f}pp |"
        )

    # ---- Write markdown output --------------------------------------------

    md = [
        f"# Class 3 forward-catalyst retrospective — {pd.Timestamp.now().date().isoformat()}",
        "",
        "**Hypothesis**: an LLM-extracted feature scoring how widely the bull/bear case is",
        "ALREADY ACCEPTED by the market can discriminate cohort losers (where the framework",
        "committed in the direction the market had already absorbed) from non-cohort winners",
        "(where the framework's commit aligned with under-priced movement).",
        "",
        f"**Scored**: {len(valid_scored)} commits (cohort A bullish ticker_weak + cohort B "
        f"bearish ticker_strong + bull/bear winner controls + Hold baselines)",
        f"**LLM**: {args.model}",
        f"**Cost**: ~${len(valid_scored) * cost_per_call:.2f} (per-call ceiling)",
        "",
        "## Per-sample-class mean scores",
        "",
        "If the hypothesis holds:",
        "  - cohort_a (bullish ticker_weak target) should have HIGH mean bull_case_priced_in",
        "  - cohort_b (bearish ticker_strong target) should have HIGH mean bear_case_priced_in",
        "  - control_bull_winner should have LOW mean bull_case_priced_in",
        "  - control_bear_winner should have LOW mean bear_case_priced_in",
        "",
        "| sample_class | n | mean bull_priced_in | mean bear_priced_in |",
        "|---|---|---|---|",
    ]
    for cls in sorted(valid_scored["sample_class"].unique()):
        sub = valid_scored[valid_scored["sample_class"] == cls]
        md.append(
            f"| `{cls}` | {len(sub)} | "
            f"{sub['bull_case_priced_in'].mean():.3f} | "
            f"{sub['bear_case_priced_in'].mean():.3f} |"
        )

    md.extend(
        [
            "",
            "## Bull-side threshold sweep",
            "",
            "Filter fires when `bull_case_priced_in > T_bull`. Net Δα = kept_α − baseline_α "
            "(positive means filter helped by removing losers). Discrimination = "
            "noncohort_α − cohort_α among fires (positive means filter correctly catches "
            "cohort losers and not non-cohort winners; primary gate per design doc §5).",
            "",
            "| T_bull | n_fired | kept α | fired α | net Δα | cohort hit rate | discrim |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for t in bull_thresholds:
        gate = _evaluate_gate(valid_scored, t, 1.01)
        md.append(
            f"| {t:.2f} | {gate['bull_n_fired']} | "
            f"{gate['bull_kept_alpha']:+.2f}% | {gate['bull_fired_alpha']:+.2f}% | "
            f"{gate['bull_net_dalpha']:+.2f}pp | {gate['bull_cohort_hit_rate']:.1f}% | "
            f"{gate['bull_discrimination']:+.2f}pp |"
        )

    md.extend(
        [
            "",
            "## Bear-side threshold sweep",
            "",
            "Filter fires when `bear_case_priced_in > T_bear`. For BEAR commits, HIGHER α "
            "means the bear call was wrong (ticker rallied). Filter HELPS by removing "
            "high-α commits. Net Δα = baseline_α − kept_α (positive = filter helps). "
            "Discrimination = cohort_α − noncohort_α (positive = filter catches rallying "
            "cohort tickers and not actual-loser non-cohort).",
            "",
            "| T_bear | n_fired | kept α | fired α | net Δα | cohort hit rate | discrim |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for t in bear_thresholds:
        gate = _evaluate_gate(valid_scored, 1.01, t)
        md.append(
            f"| {t:.2f} | {gate['bear_n_fired']} | "
            f"{gate['bear_kept_alpha']:+.2f}% | {gate['bear_fired_alpha']:+.2f}% | "
            f"{gate['bear_net_dalpha']:+.2f}pp | {gate['bear_cohort_hit_rate']:.1f}% | "
            f"{gate['bear_discrimination']:+.2f}pp |"
        )

    md.extend(
        [
            "",
            "## Verdict (manual fill-in after numbers)",
            "",
            "Per `claudedocs/forward-catalyst-mechanism-exploration-2026-05-06.md` §5",
            "validation methodology, the spec is permitted iff at least ONE threshold pair",
            "satisfies BOTH:",
            "",
            "  1. Discrimination ≥ +5pp in correct direction (PRIMARY gate)",
            "  2. Cohort hit rate ≥ 60%",
            "  3. Net Δα ≥ +0.5pp OR shadow-mode-first if (3) is unmeasurable",
            "",
            "Cross-side combination considered: bull-side AND bear-side both must pass for",
            "a unified spec; OR the spec can be split into bull-only and bear-only gates if",
            "one side passes and the other fails.",
            "",
            "**If passes** → invoke `/speckit.specify` for forward-catalyst spec; cite this",
            "retrospective as motivating empirical evidence.",
            "",
            "**If fails on discrimination (criterion 1)** → SKIP spec entirely; document the",
            "negative finding; consider Class 2 (options-IV) as fallback per design doc §4.",
            "",
            "**If passes 1+2 but fails 3** → spec permitted with shadow-mode-first condition",
            "(observe n≥20 propagates before active-mode flip).",
            "",
            "## Reproducibility",
            "",
            "```",
            "python scripts/forward_catalyst_class3_retrospective.py",
            "```",
            "",
            "Reads `claudedocs/sector-alpha-attribution-2026-05-06.csv` for cohort + controls;",
            "loads cached state logs from `~/.tradingagents/logs/<ticker>/...`; calls Haiku via",
            "`tradingagents.llm_clients.factory.create_llm_client`; saves per-row scores to",
            f"`{out_csv}`. Resume-on-rerun supported (only re-scores rows missing from CSV).",
            "Cost: ~$0.10-0.20 in Haiku at default ~95-commit sample.",
        ]
    )

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md), encoding="utf-8")
    print()
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
