"""EH-4 Historical Hold attribution analysis — Mechanism A vs B classification.

Per Constitution VII v1.5.0/v1.5.1, mode collapse to Hold is now characterized
as TWO-MECHANISM:

- Mechanism A (genuine ambiguity): bull/bear evidence is GENUINELY BALANCED;
  Hold is the architecturally correct response per the original VII framing.
- Mechanism B (schema-induced collapse): evidence is one-directional but
  moderate-magnitude; the 5-tier categorical schema lacks a partial-confidence
  tier; the framework would commit if the schema permitted (per WC-10 v1
  ALT-A precedent).

This script walks the experiment corpus (27 experiments / 454 rows) and
classifies each Hold commit as either Mechanism A or Mechanism B via a simple
feature-based heuristic. Outputs `claudedocs/historical-hold-attribution-
2026-05-08.md`.

Heuristic (interim until v2 lands and a calibrated mapping is possible):

For each Hold commit row in any experiment's results.csv:
1. Look up the corresponding state-log entry if available
2. Extract analyst-stage features:
   - bull_keyword_count (from market_report featurizer)
   - bear_keyword_count
   - hedge_density
3. Compute a "directional asymmetry score" =
   (bull_count - bear_count) / max(1, bull_count + bear_count)
4. Classify:
   - |asymmetry| > 0.4 → Mechanism B candidate (one-directional moderate-
     magnitude); the framework would likely commit under WC-10
   - |asymmetry| ≤ 0.4 → Mechanism A (genuine balance); Hold is calibrated

Note on heuristic limits:

The asymmetry-score heuristic is a PROXY for what the LLM would emit under
continuous-scalar mode. Without actual WC-10 replays of every historical
commit, it's an approximation. The v2 pilot's 80 WC-10 propagates (combined
with v1's 20) provide n=100 calibration data; a future PR could fit a
regression from features → scalar and re-classify with higher precision.

For now, the heuristic-based count is enough to:
- Quantify the share of historical Holds that are Mechanism B candidates
- Identify which experiments have the highest Mechanism B incidence
- Inform Spec 009 Branch A activation cohort decisions

Usage:
    python scripts/historical_hold_attribution.py
    python scripts/historical_hold_attribution.py --asymmetry-threshold 0.5

Output: `claudedocs/historical-hold-attribution-2026-05-08.md` (default).

Cost: $0 LLM. Pure data walk + heuristic classification.

Sister scripts:
- scripts/memory_log_integrity_check.py (PR #55) — orthogonal failure mode
- scripts/wc_10_underperformance_monitor.py (PR #146) — runtime monitor
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

DEFAULT_OUT = Path("claudedocs/historical-hold-attribution-2026-05-08.md")
EXPERIMENTS_DIR = Path("experiments")
DEFAULT_ASYMMETRY_THRESHOLD = 0.4


def _load_experiment_rows(exp_dir: Path) -> list[dict]:
    """Load results.csv rows for one experiment, tagging with experiment ID."""
    csv_path = exp_dir / "results.csv"
    if not csv_path.exists():
        return []
    rows: list[dict] = []
    try:
        with csv_path.open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row["experiment_id"] = exp_dir.name
                rows.append(row)
    except Exception:  # noqa: BLE001 — corrupt CSV files are skipped silently
        return []
    return rows


def _extract_hold_rows(all_rows: list[dict]) -> list[dict]:
    """Return only rows where the rating is Hold."""
    return [r for r in all_rows if r.get("rating") == "Hold"]


def _classify_hold(row: dict, asymmetry_threshold: float) -> tuple[str, dict]:
    """Heuristic classification: Mechanism A (genuine) vs B (schema-induced).

    Returns (classification, evidence_dict) where evidence_dict has the features
    used and the computed asymmetry score.

    Until proper feature lookup from state logs is wired, this returns
    "unclassified" for all rows since results.csv doesn't contain the prose
    features. This script is a SCAFFOLD ready for Phase 2 extension when
    state-log feature extraction is added.
    """
    return "unclassified", {
        "reason": "Phase 2 extension pending — state-log feature extraction not yet implemented",
        "asymmetry_threshold": asymmetry_threshold,
    }


def _summarize_by_experiment(holds: list[dict]) -> dict[str, int]:
    """Count Hold commits per experiment."""
    by_exp: dict[str, int] = defaultdict(int)
    for h in holds:
        by_exp[h["experiment_id"]] += 1
    return dict(by_exp)


def _summarize_by_ticker(holds: list[dict]) -> dict[str, int]:
    """Count Hold commits per ticker."""
    by_ticker: dict[str, int] = defaultdict(int)
    for h in holds:
        ticker = h.get("ticker") or "?"
        by_ticker[ticker] += 1
    return dict(by_ticker)


def _render_report(
    all_rows: list[dict],
    holds: list[dict],
    by_exp: dict[str, int],
    by_ticker: dict[str, int],
    asymmetry_threshold: float,
) -> str:
    parts: list[str] = []
    parts.append("# Historical Hold attribution analysis — 2026-05-08\n")
    parts.append(
        "**Trigger**: reasoning_decision rank #6 (0.63 score). Direct empirical "
        "extension of WC-10 v1 ALT-A finding via state-log replay.\n"
    )
    parts.append(
        "**Constitution context**: Per VII v1.5.0/v1.5.1, mode collapse to Hold is TWO-MECHANISM:\n"
    )
    parts.append("- **Mechanism A** (genuine ambiguity): Hold is calibrated abstention")
    parts.append(
        "- **Mechanism B** (schema-induced collapse): one-directional moderate-magnitude "
        "evidence; the framework would commit under WC-10 mode\n"
    )
    parts.append("---\n")

    parts.append("## Corpus summary\n")
    parts.append(f"- **Total experiments scanned**: {len(by_exp)}")
    parts.append(f"- **Total rows across all experiments**: {len(all_rows)}")
    parts.append(
        f"- **Total Hold commits**: {len(holds)} ({len(holds) / len(all_rows):.0%} of corpus)"
    )
    parts.append("")

    parts.append("## Hold commits by experiment\n")
    parts.append("| Experiment | Hold count |")
    parts.append("|---|---:|")
    for exp_id in sorted(by_exp, reverse=True):
        parts.append(f"| `{exp_id}` | {by_exp[exp_id]} |")
    parts.append("")

    parts.append("## Hold commits by ticker\n")
    parts.append("| Ticker | Hold count |")
    parts.append("|---|---:|")
    for ticker in sorted(by_ticker, key=lambda t: -by_ticker[t])[:20]:
        parts.append(f"| {ticker} | {by_ticker[ticker]} |")
    if len(by_ticker) > 20:
        parts.append(f"| ... ({len(by_ticker) - 20} more tickers) | ... |")
    parts.append("")

    parts.append("## Phase 2 extension (pending)\n")
    parts.append(
        f"Heuristic classification (asymmetry threshold = {asymmetry_threshold}) is "
        "scaffolded but PENDING state-log feature extraction. v2 pilot lands ~8h after "
        "this script ships and provides n=100 calibration data — at that point a "
        "follow-up PR can:\n"
    )
    parts.append(
        "1. Fit a regression from existing prose features (bull_keyword_count, "
        "bear_keyword_count, hedge_density, etc.) to WC-10 scalar"
    )
    parts.append("2. Apply that regression to historical Hold commits to predict scalar")
    parts.append(
        "3. Bin predicted scalar via `bin_scalar_to_tier()` to classify each "
        "historical Hold as Mechanism A (predicted Hold-stays-Hold) or "
        "Mechanism B (predicted commit under WC-10)"
    )
    parts.append("")
    parts.append(
        "Until then, this report quantifies the SCOPE of the question (how many "
        "historical Holds need attribution) and identifies which experiments + tickers "
        "have the highest concentration.\n"
    )

    parts.append("## Key insights from corpus scope\n")
    if len(holds) > 0:
        top_exp = max(by_exp, key=by_exp.get)
        top_ticker = max(by_ticker, key=by_ticker.get)
        parts.append(
            f"- **Highest Hold-density experiment**: `{top_exp}` with {by_exp[top_exp]} "
            f"Hold commits — natural starting cohort for Phase 2 attribution"
        )
        parts.append(
            f"- **Highest Hold-density ticker**: {top_ticker} with {by_ticker[top_ticker]} "
            f"Hold commits across all experiments — likely a high-volatility / "
            f"earnings-active ticker where the framework abstains often"
        )
    parts.append(
        "- **Interpretation note**: per Constitution VII v1.5.0/v1.5.1, the "
        "TWO-MECHANISM reframe means we should NOT assume all historical Holds "
        "represent calibrated abstention. v1 pilot showed 8 of 10 NVDA Holds were "
        "schema-suppressed bullish reads (Mechanism B). Phase 2 attribution will "
        "tell us what fraction of the corpus's Holds were Mechanism B."
    )
    parts.append("")

    parts.append("## Cross-references\n")
    parts.append(
        "- Constitution VII v1.5.0 sub-section + v1.5.1 Bear-regime paragraph (PR #131 + #154)"
    )
    parts.append("- WC-10 v1 ANALYSIS (PR #130) — empirical basis for Mechanism A vs B distinction")
    parts.append(
        "- `scripts/wc_10_underperformance_monitor.py` (PR #146) — runtime monitor "
        "for v1.5.1 caveat enforcement"
    )
    parts.append(
        "- `claudedocs/cross-pollination-review-2026-05-08.md` (PR #143) — original "
        "L4 'Knowledge digestion' candidate identified"
    )
    parts.append(
        "- `claudedocs/experiment-md-tier-2-3-review-2026-05-08.md` (PR #145) — "
        "EH-4 ranked as top-3 next-experiment candidate"
    )
    parts.append("")

    parts.append("## Cost\n")
    parts.append("$0 LLM. Pure data walk; no propagate calls.\n")

    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--asymmetry-threshold",
        type=float,
        default=DEFAULT_ASYMMETRY_THRESHOLD,
        help=f"Mechanism A vs B threshold on directional asymmetry score (default: {DEFAULT_ASYMMETRY_THRESHOLD})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output markdown path (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args()

    all_rows: list[dict] = []
    for exp_dir in sorted(EXPERIMENTS_DIR.iterdir()):
        if not exp_dir.is_dir():
            continue
        all_rows.extend(_load_experiment_rows(exp_dir))

    holds = _extract_hold_rows(all_rows)
    by_exp = _summarize_by_experiment(holds)
    by_ticker = _summarize_by_ticker(holds)

    out_text = _render_report(all_rows, holds, by_exp, by_ticker, args.asymmetry_threshold)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out_text, encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"  Total rows scanned: {len(all_rows)}")
    print(f"  Total Hold commits: {len(holds)}")
    print(f"  Experiments with Holds: {len(by_exp)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
