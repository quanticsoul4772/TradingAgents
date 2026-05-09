"""Dry-run digest renderer for WC-10 — operator-facing output preview without LLM cost.

Synthesizes a side-by-side daily_signals.py-style markdown digest showing what an
operator running daily_signals.py with `--wc-10-enabled` (Spec 009 Branch A)
would have seen vs the existing 5-tier baseline mode, on the same date + tickers.

Uses saved data from `experiments/2026-05-08-001-wc-10-pilot/results.csv` —
zero new LLM spend.

This is a Spec 009 ergonomics dry-run: validates the WC-10 production deployment
markdown surface BEFORE v2 + v3 verdicts trigger Branch A activation. If the
side-by-side digest reveals UX issues (confusing scalar formatting, missing
context, etc.), iterate on the renderer NOW rather than during the post-verdict
implementation push.

Usage:
    python scripts/wc_10_dryrun_digest.py [--date 2026-04-15] [--out claudedocs/...]

Output:
    Markdown to claudedocs/wc-10-dryrun-digest-<date>.md by default.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.graph.trading_graph import fetch_returns  # noqa: E402

PILOT_CSV = Path("experiments/2026-05-08-001-wc-10-pilot/results.csv")
DEFAULT_OUT_DIR = Path("claudedocs")
DEFAULT_DATE = "2026-04-15"  # mid-pilot, 21d realized α available


def _load_rows(csv_path: Path, date: str) -> dict[str, dict[str, dict]]:
    """Returns {ticker: {mode: row}} for the given date."""
    rows: dict[str, dict[str, dict]] = defaultdict(dict)
    with csv_path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["date"] != date:
                continue
            rows[row["ticker"]][row["mode"]] = row
    return rows


def _fetch_alpha(ticker: str, date: str) -> tuple[float | None, float | None, int | None]:
    raw, alpha, days = fetch_returns(ticker, date, holding_days=21)
    return raw, alpha, days


def _render_section(
    mode: str,
    label: str,
    rows: dict[str, dict[str, dict]],
    alphas: dict[str, tuple[float | None, float | None, int | None]],
) -> str:
    """Render one mode's section (WC-10 or 5-tier baseline)."""
    actionable = []
    filtered = []
    for ticker in sorted(rows.keys()):
        if mode not in rows[ticker]:
            continue
        row = rows[ticker][mode]
        rating = row["binned_tier"] if mode == "wc_10" else row["rating"]
        if rating in ("Buy", "Overweight"):
            actionable.append((ticker, row, rating))
        else:
            filtered.append((ticker, row, rating))

    parts: list[str] = [f"## {label}\n"]
    parts.append(
        f"**Actionable**: {len(actionable)}  "
        f"| **Filtered (Hold / Underweight / Sell)**: {len(filtered)}\n"
    )
    parts.append("")

    if actionable:
        parts.append("### Actionable signals (Buy / Overweight)\n")
        for ticker, row, rating in actionable:
            raw, alpha, days = alphas[ticker]
            scalar_str = ""
            if mode == "wc_10":
                scalar_str = f" (scalar `{row['rating']}`)"
            real_str = ""
            if alpha is not None and days is not None:
                real_str = f" — realized 21d α = `{alpha * 100:+.2f}%` (days={days})"
            parts.append(f"- **{ticker}** — {rating}{scalar_str}{real_str}")
        parts.append("")

    if filtered:
        parts.append("### Filtered signals (Hold / Underweight / Sell)\n")
        for ticker, row, rating in filtered:
            raw, alpha, days = alphas[ticker]
            scalar_str = ""
            if mode == "wc_10":
                scalar_str = f" (scalar `{row['rating']}`)"
            real_str = ""
            if alpha is not None and days is not None:
                real_str = f" — realized 21d α = `{alpha * 100:+.2f}%` (days={days})"
            note = ""
            if rating == "Hold":
                note = "  \n  _Hold = calibrated abstention OR schema-induced collapse (per Constitution VII v1.5.0)._"
            parts.append(f"- **{ticker}** — {rating}{scalar_str}{real_str}{note}")
        parts.append("")

    return "\n".join(parts)


def _render_compare_table(
    rows: dict[str, dict[str, dict]],
    alphas: dict[str, tuple[float | None, float | None, int | None]],
) -> str:
    """Side-by-side ticker × mode comparison."""
    lines: list[str] = ["## Side-by-side comparison\n"]
    lines.append(
        "| Ticker | WC-10 (scalar → bin) | 5-tier baseline | Decision differs? | Realized 21d α |"
    )
    lines.append("|---|---|---|---|---|")
    for ticker in sorted(rows.keys()):
        wc = rows[ticker].get("wc_10", {})
        bs = rows[ticker].get("5tier_baseline", {})
        wc_str = f"`{wc['rating']}` → {wc['binned_tier']}" if wc else "—"
        bs_str = bs.get("rating", "—") if bs else "—"
        differs = "**yes**" if (wc and bs and wc["binned_tier"] != bs["rating"]) else "no"
        raw, alpha, days = alphas[ticker]
        alpha_str = f"{alpha * 100:+.2f}% (days={days})" if alpha is not None else "—"
        lines.append(f"| {ticker} | {wc_str} | {bs_str} | {differs} | {alpha_str} |")
    lines.append("")
    return "\n".join(lines)


def _render_digest(date: str, rows: dict[str, dict[str, dict]]) -> str:
    """Top-level digest assembly."""
    # Fetch realized α once per ticker (cached by yfinance internally)
    alphas: dict[str, tuple[float | None, float | None, int | None]] = {}
    for ticker in rows:
        alphas[ticker] = _fetch_alpha(ticker, date)

    parts: list[str] = []
    parts.append(f"# WC-10 dry-run digest — {date}\n")
    parts.append(
        "_Synthesized from `experiments/2026-05-08-001-wc-10-pilot/results.csv` "
        "(WC-10 v1 pilot data, no LLM spend). Demonstrates the operator-facing "
        "markdown surface for Spec 009 Branch A (WC-10 production deployment via "
        "`daily_signals.py --wc-10-enabled`) vs the existing 5-tier baseline._\n"
    )
    parts.append(
        f"**Source**: {PILOT_CSV.as_posix()} ({len(rows)} ticker{'s' if len(rows) != 1 else ''} "
        f"on `{date}`)\n"
    )
    parts.append("")
    parts.append("---\n")

    parts.append(_render_compare_table(rows, alphas))
    parts.append("---\n")

    parts.append(
        _render_section("wc_10", "Branch A — WC-10 mode (`--wc-10-enabled`)", rows, alphas)
    )
    parts.append("---\n")

    parts.append(
        _render_section("5tier_baseline", "Existing baseline — 5-tier mode (default)", rows, alphas)
    )
    parts.append("---\n")

    parts.append("## Operator interpretation\n")
    n_total = len(rows)
    wc_actionable = sum(
        1
        for t in rows
        if "wc_10" in rows[t] and rows[t]["wc_10"]["binned_tier"] in ("Buy", "Overweight")
    )
    bs_actionable = sum(
        1
        for t in rows
        if "5tier_baseline" in rows[t]
        and rows[t]["5tier_baseline"]["rating"] in ("Buy", "Overweight")
    )
    parts.append(
        f"- WC-10 mode produced **{wc_actionable} actionable signal{'s' if wc_actionable != 1 else ''}** "
        f"of {n_total}; baseline produced **{bs_actionable} actionable**."
    )
    parts.append(
        "- Tickers where WC-10 surfaces actionable signal that baseline suppresses "
        "are the schema-induced-collapse cases per Constitution VII v1.5.0."
    )
    parts.append(
        "- Realized 21d α values (above) are the empirical check on the additional commits."
    )
    parts.append("")
    parts.append(
        "**This is dry-run output**, not investment advice. Production deployment requires "
        "v2 + v3 verdicts per Spec 009 branch selection criteria."
    )

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=DEFAULT_DATE, help="Pilot date to render (YYYY-MM-DD)")
    parser.add_argument("--out", type=Path, default=None, help="Output markdown path")
    args = parser.parse_args()

    if not PILOT_CSV.exists():
        print(f"Pilot CSV not found at {PILOT_CSV}", file=sys.stderr)
        sys.exit(1)

    rows = _load_rows(PILOT_CSV, args.date)
    if not rows:
        print(f"No rows for date {args.date} in {PILOT_CSV}", file=sys.stderr)
        sys.exit(1)

    out_path = args.out or DEFAULT_OUT_DIR / f"wc-10-dryrun-digest-{args.date}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_render_digest(args.date, rows), encoding="utf-8")

    print(f"Wrote dry-run digest to {out_path}")
    print(f"Date: {args.date}, tickers: {sorted(rows.keys())}")


if __name__ == "__main__":
    main()
