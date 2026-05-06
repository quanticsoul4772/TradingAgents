"""Daily Signals — operator-facing watchlist runner.

Runs ``propagate(ticker, date)`` over a watchlist with all empirical filters
ACTIVE by default, then renders a markdown digest filtered to actionable
21d-horizon bullish recommendations.

Filters active by default (per RESEARCH_FINDINGS):
  - Calibrated abstention (Constitution Principle VII): Hold ratings are
    correctly inert ~50-70% of the time; suppressed from actionable list
  - A3 momentum filter: UW/Sell commits on tickers in mean-reversion zone
    downgraded to Hold (claudedocs/uw-suppression-filter.md)
  - Spec 003 contrarian gate: Buy/OW commits with high analyst-prose
    bull-keyword density downgraded to Hold (4-line-evidence validated;
    claudedocs/finding4-within-bullish-subset-ic-2026-05-05.md)

Usage:
    python scripts/daily_signals.py --tickers AAPL,NVDA,INTC
    python scripts/daily_signals.py --tickers tickers.txt --date 2026-04-01
    python scripts/daily_signals.py --include-all       # show Hold/UW/Sell too
    python scripts/daily_signals.py --shadow-gates      # gates observe but don't override

Output:
    Markdown digest written to ``claudedocs/daily-signals-<YYYY-MM-DD>.md``
    by default; override with --out.

This is research substrate, not investment advice (Constitution IV).
"""

from __future__ import annotations

import re
import sys
import time
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path

import typer
from rich.console import Console

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

console = Console()
app = typer.Typer(add_completion=False, help=__doc__)


# ---- Constants -------------------------------------------------------------

ACTIONABLE_RATINGS = {"Buy", "Overweight"}
DEFAULT_OUT_DIR = Path("claudedocs")

# Default thresholds — calibrated against the existing corpus
DEFAULT_A3_THRESHOLD = -5.0  # UW/Sell suppressed when ticker down >5% in 30d
DEFAULT_A3_LOOKBACK = 30
DEFAULT_GATE_THRESHOLD = 80  # spec 003 contrarian gate percentile threshold


# ---- Helpers ---------------------------------------------------------------


def _resolve_tickers(spec: str) -> list[str]:
    """Comma-separated string OR path to a tickers file (one per line, # comments)."""
    if "," in spec or not Path(spec).exists():
        return [t.strip().upper() for t in spec.split(",") if t.strip()]
    out = []
    for line in Path(spec).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line.upper())
    return out


def _resolve_date(date_str: str | None) -> str:
    """Default to today; if today is a weekend, fall back to last Friday."""
    if date_str:
        return date_str
    today = datetime.now()
    while today.weekday() >= 5:  # Sat=5, Sun=6
        today -= timedelta(days=1)
    return today.strftime("%Y-%m-%d")


def _build_config(
    *,
    shadow_gates: bool,
    a3_threshold: float,
    a3_lookback: int,
    gate_threshold: int,
) -> dict:
    """Production-defaults config: Opus + Haiku + active gates."""
    config = deepcopy(DEFAULT_CONFIG)
    config["llm_provider"] = "anthropic"
    config["deep_think_llm"] = "claude-opus-4-7"
    config["quick_think_llm"] = "claude-haiku-4-5"
    config["max_debate_rounds"] = 1
    config["max_risk_discuss_rounds"] = 1
    config["checkpoint_enabled"] = False
    config["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "exa",
    }
    # A3 momentum filter
    config["uw_momentum_filter_threshold"] = a3_threshold
    config["uw_momentum_filter_lookback_days"] = a3_lookback
    # Spec 003 contrarian gate
    config["contrarian_gate_mode"] = "shadow" if shadow_gates else "active"
    config["contrarian_gate_threshold"] = gate_threshold
    config["contrarian_gate_target"] = "hold"
    return config


def _extract_rationale_excerpt(markdown: str, max_chars: int = 240) -> str:
    """First non-rating prose paragraph from the PM decision markdown."""
    if not markdown:
        return ""
    paragraphs = [p.strip() for p in markdown.split("\n\n") if p.strip()]
    for p in paragraphs:
        # Skip rating lines, separators, gate annotations
        if p.startswith("**Rating") or p.startswith("Rating:") or p.startswith("---"):
            continue
        if "[Spec 003 contrarian gate]" in p or "[A3 momentum filter]" in p:
            continue
        # Strip markdown emphasis markers for readability
        clean = re.sub(r"\*+", "", p).strip()
        if not clean:
            continue
        if len(clean) > max_chars:
            clean = clean[: max_chars - 1].rstrip() + "…"
        return clean
    return ""


def _detect_gate_overrides(markdown: str) -> dict[str, bool]:
    """Detect which (if any) of the empirical filters fired per the decision markdown."""
    return {
        "a3": "[A3 momentum filter]" in (markdown or ""),
        "spec003": "[Spec 003 contrarian gate]" in (markdown or ""),
    }


# ---- Per-ticker propagation -----------------------------------------------


def _run_one(ta: TradingAgentsGraph, ticker: str, date: str) -> dict:
    """Run a single propagate; capture rating + gate annotations + metadata.
    Errors are swallowed and recorded in the returned dict (never raised)."""
    t0 = time.perf_counter()
    rating = ""
    error = ""
    final_state: dict | None = None
    decision_markdown = ""
    try:
        final_state, rating_value = ta.propagate(ticker, date)
        rating = str(rating_value).strip()
        decision_markdown = (final_state or {}).get("final_trade_decision", "")
    except Exception as e:  # noqa: BLE001 — never let one ticker break the batch
        error = f"{type(e).__name__}: {e}"
    elapsed = round(time.perf_counter() - t0, 2)

    gate_block = (final_state or {}).get("contrarian_gate") or {}
    overrides = _detect_gate_overrides(decision_markdown)
    rationale = _extract_rationale_excerpt(decision_markdown)

    return {
        "ticker": ticker,
        "date": date,
        "rating": rating,
        "error": error,
        "run_seconds": elapsed,
        "decision_markdown": decision_markdown,
        "rationale": rationale,
        "gate_mode": gate_block.get("mode", ""),
        "gate_skipped": gate_block.get("gate_skipped"),
        "gate_feature_value": gate_block.get("feature_value"),
        "gate_percentile": gate_block.get("percentile"),
        "gate_n_history": gate_block.get("n_history"),
        "gate_would_fire": gate_block.get("would_fire"),
        "gate_fired": gate_block.get("gate_fired"),
        "gate_pre_rating": gate_block.get("pm_rating_pre_gate"),
        "gate_post_rating": gate_block.get("pm_rating_post_gate"),
        "a3_overrode": overrides["a3"],
        "spec003_overrode": overrides["spec003"],
    }


# ---- Markdown digest renderer ---------------------------------------------


def _render_actionable_block(row: dict) -> str:
    parts = [f"### {row['ticker']} — **{row['rating']}**"]
    if row.get("rationale"):
        parts.append(f"> {row['rationale']}")

    bullets = []
    g = row.get("gate_post_rating") or row.get("rating", "")
    pre = row.get("gate_pre_rating")
    if pre and pre != g:
        # Should not happen for actionable (gate fires only downgrade), but be defensive
        bullets.append(f"- PM call: **{pre}** → final: **{g}**")
    pct = row.get("gate_percentile")
    n_hist = row.get("gate_n_history")
    skipped = row.get("gate_skipped")
    if skipped:
        bullets.append(
            f"- Spec 003 contrarian gate: **skipped** ({skipped}; n_history={n_hist or '—'})"
        )
    elif pct is not None:
        bullets.append(
            f"- Spec 003 contrarian gate: percentile {pct:.0f} (threshold "
            f"{row.get('gate_threshold', DEFAULT_GATE_THRESHOLD)}; "
            f"n_history={n_hist or '—'}) — gate did not fire"
        )
    if bullets:
        parts.extend(bullets)
    parts.append("")
    return "\n".join(parts)


def _render_filtered_block(row: dict) -> str:
    """Filtered = Hold/UW/Sell ratings, plus active-mode-gate-suppressed bullish commits."""
    rating = row.get("rating", "")
    parts = [f"### {row['ticker']} — {rating}"]
    if row.get("a3_overrode"):
        parts.append(
            "- **A3 momentum filter overrode** the original UW/Sell rating to Hold "
            "(ticker in mean-reversion zone). See "
            "[`claudedocs/uw-suppression-filter.md`](../claudedocs/uw-suppression-filter.md)."
        )
    if row.get("spec003_overrode"):
        pct = row.get("gate_percentile")
        pct_str = f"{pct:.0f}" if pct is not None else "?"
        parts.append(
            f"- **Spec 003 contrarian gate overrode** the original Buy/OW rating to "
            f"{rating} (analyst-prose bull-keyword percentile {pct_str}). See "
            "[`claudedocs/finding4-within-bullish-subset-ic-2026-05-05.md`]"
            "(../claudedocs/finding4-within-bullish-subset-ic-2026-05-05.md)."
        )
    if row.get("rationale") and not (row.get("a3_overrode") or row.get("spec003_overrode")):
        # For unmodified Hold/UW/Sell, include a brief rationale
        parts.append(f"> {row['rationale']}")
    parts.append("")
    return "\n".join(parts)


def _render_digest(rows: list[dict], date: str, *, shadow_gates: bool, include_all: bool) -> str:
    n_total = len(rows)
    n_err = sum(1 for r in rows if r["error"])
    n_actionable = sum(
        1
        for r in rows
        if not r["error"]
        and r["rating"] in ACTIONABLE_RATINGS
        and not r.get("spec003_overrode")
        and not r.get("a3_overrode")
    )
    n_gate_overrode = sum(1 for r in rows if r.get("spec003_overrode"))
    n_a3_overrode = sum(1 for r in rows if r.get("a3_overrode"))
    n_hold = sum(1 for r in rows if not r["error"] and r["rating"] == "Hold")

    lines: list[str] = []
    lines.append(f"# Daily Signals — {date}\n")
    mode = "shadow (annotation only)" if shadow_gates else "active (rating override)"
    lines.append(
        f"**Universe**: {n_total} ticker{'s' if n_total != 1 else ''}  "
        f"| **Actionable**: {n_actionable}  "
        f"| **Hold (calibrated abstention)**: {n_hold}  "
        f"| **Spec 003 gate overrode**: {n_gate_overrode}  "
        f"| **A3 filter overrode**: {n_a3_overrode}  "
        f"| **Errored**: {n_err}\n"
    )
    lines.append(f"**Filters**: A3 momentum filter ON · Spec 003 contrarian gate ON ({mode})\n")
    lines.append("---\n")

    # Actionable section
    actionable_rows = [
        r
        for r in rows
        if not r["error"]
        and r["rating"] in ACTIONABLE_RATINGS
        and not r.get("spec003_overrode")
        and not r.get("a3_overrode")
    ]
    if actionable_rows:
        lines.append("## Actionable signals (Buy / Overweight, gates not fired)\n")
        for r in sorted(actionable_rows, key=lambda x: x["ticker"]):
            lines.append(_render_actionable_block(r))
    else:
        lines.append("## Actionable signals (Buy / Overweight, gates not fired)\n")
        lines.append(
            "_No actionable signals today. The framework is in calibrated-abstention mode._\n"
        )

    # Filtered section (Hold/UW/Sell + gate-overridden)
    if include_all or n_gate_overrode or n_a3_overrode:
        lines.append("---\n")
        lines.append("## Filtered (Hold / Underweight / Sell, or gate-suppressed)\n")
        filtered_rows = [
            r
            for r in rows
            if not r["error"]
            and (
                r["rating"] not in ACTIONABLE_RATINGS
                or r.get("spec003_overrode")
                or r.get("a3_overrode")
            )
        ]
        if filtered_rows:
            for r in sorted(filtered_rows, key=lambda x: x["ticker"]):
                lines.append(_render_filtered_block(r))
        else:
            lines.append("_(none)_\n")

    # Errors
    if n_err:
        lines.append("---\n")
        lines.append("## Errors\n")
        for r in [r for r in rows if r["error"]]:
            lines.append(f"- **{r['ticker']}**: {r['error']}")
        lines.append("")

    # Methodology footer
    lines.append("---\n")
    lines.append("## Methodology\n")
    lines.append(
        "- **Horizon**: 21 trading days. 5d horizon is at the LLM single-call calibration "
        "ceiling (no signal); 21d shows +1.23% mean α on bullish commits across n=71 "
        "cross-experiment commits (~61% hit rate). See `RESEARCH_FINDINGS.md` headline.\n"
        "- **Calibrated abstention** (Constitution VII): Hold ≈ 0% mean α at every horizon. "
        "Suppressed from the actionable list by default; the framework is correctly doing "
        "nothing 50-70% of the time.\n"
        "- **A3 momentum filter** (`tradingagents/agents/utils/momentum_filter.py`): suppresses "
        "UW/Sell commits when the ticker is down ≥5% over 30 trading days; the framework's "
        "bearish commits on already-down tickers tend to mean-revert bullishly.\n"
        "- **Spec 003 contrarian gate** (`tradingagents/signals/contrarian_gate.py`): suppresses "
        "Buy/OW commits when the market analyst's `bull_keyword_count` is in the top 20% of "
        "the prior 20-date history for that ticker; high analyst-prose density tracks recent "
        "strength which mean-reverts. Validated through 4 lines of evidence "
        "(`claudedocs/finding4-within-bullish-subset-ic-2026-05-05.md`).\n"
        "- **Period-conditional**: realized α varies across calendar periods; the +1.23% is "
        "moderate-confidence (Bayesian posterior 0.63 across 3 NVDA periods).\n"
    )
    lines.append("\n---\n")
    lines.append(
        "_This is research substrate, not investment advice. Per Constitution Principle IV: "
        "the framework's outputs are not trading recommendations._\n"
    )
    return "\n".join(lines)


# ---- CLI -------------------------------------------------------------------


@app.command()
def main(
    tickers: str = typer.Option(
        ..., "--tickers", help="Comma-separated tickers OR path to tickers file."
    ),
    date: str = typer.Option(
        None, "--date", help="ISO date (YYYY-MM-DD). Default: today (or last Friday if weekend)."
    ),
    out: Path = typer.Option(
        None, "--out", help="Markdown output path. Default: claudedocs/daily-signals-<date>.md"
    ),
    include_all: bool = typer.Option(
        False, "--include-all", help="Show Hold/UW/Sell rows alongside actionable."
    ),
    shadow_gates: bool = typer.Option(
        False,
        "--shadow-gates",
        help="Run gates in shadow mode (annotation only, no rating override).",
    ),
    a3_threshold: float = typer.Option(
        DEFAULT_A3_THRESHOLD,
        "--a3-threshold",
        help="A3 momentum filter threshold (% in lookback window).",
    ),
    a3_lookback: int = typer.Option(
        DEFAULT_A3_LOOKBACK, "--a3-lookback", help="A3 momentum filter lookback (trading days)."
    ),
    gate_threshold: int = typer.Option(
        DEFAULT_GATE_THRESHOLD,
        "--gate-threshold",
        help="Spec 003 contrarian gate percentile threshold.",
    ),
    emit_csv: Path = typer.Option(
        None,
        "--emit-csv",
        help=(
            "Optional CSV output path consumable by paper_trade.py. Schema: "
            "specs/002-paper-trading-harness/contracts/signals_csv.md. "
            "Atomically written; existing file overwritten."
        ),
    ),
):
    """Run propagate(ticker, today) over the watchlist with active gates; write digest."""
    ticker_list = _resolve_tickers(tickers)
    if not ticker_list:
        console.print("[red]No tickers resolved.[/red]")
        raise typer.Exit(1)

    resolved_date = _resolve_date(date)
    out_path = out or DEFAULT_OUT_DIR / f"daily-signals-{resolved_date}.md"

    console.print(
        f"[cyan]Daily Signals[/cyan]  date={resolved_date}  "
        f"tickers={len(ticker_list)}  "
        f"gates={'shadow' if shadow_gates else 'active'}  "
        f"output={out_path}"
    )
    console.print(
        f"[dim]Estimated cost: ${len(ticker_list) * 0.4:.2f} "
        f"({len(ticker_list)} × ~$0.40/propagate at Opus + Haiku)[/dim]"
    )

    config = _build_config(
        shadow_gates=shadow_gates,
        a3_threshold=a3_threshold,
        a3_lookback=a3_lookback,
        gate_threshold=gate_threshold,
    )
    # Per-day memory log so reruns don't pollute the user's main log
    config["memory_log_path"] = str(
        Path.home() / ".tradingagents" / "memory" / f"daily-{resolved_date}.md"
    )

    console.print("[cyan]Building graph...[/cyan]")
    ta = TradingAgentsGraph(
        selected_analysts=["market", "news", "fundamentals"],
        debug=False,
        config=config,
    )

    rows: list[dict] = []
    wall_start = time.perf_counter()
    for i, ticker in enumerate(ticker_list, 1):
        console.print(f"[cyan]({i}/{len(ticker_list)})[/cyan]  {ticker} {resolved_date}...")
        row = _run_one(ta, ticker, resolved_date)
        # Stash the configured threshold so the renderer can show it
        row["gate_threshold"] = gate_threshold
        rows.append(row)
        if row["error"]:
            console.print(f"  [red]error:[/red] {row['error']}")
        else:
            console.print(f"  → rating: [bold]{row['rating']}[/bold]  ({row['run_seconds']:.0f}s)")

    elapsed_min = (time.perf_counter() - wall_start) / 60.0
    console.print(f"\n[cyan]Done.[/cyan]  {elapsed_min:.1f} min wall-clock")

    digest = _render_digest(rows, resolved_date, shadow_gates=shadow_gates, include_all=include_all)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(digest, encoding="utf-8")
    console.print(f"[green]Digest:[/green]  {out_path}")

    if emit_csv is not None:
        _emit_signals_csv(rows, resolved_date, emit_csv)
        console.print(f"[green]CSV:[/green]     {emit_csv}")

    return 0


def _emit_signals_csv(rows: list[dict], resolved_date: str, path: Path) -> None:
    """Write a paper_trade.py-consumable signals CSV per signals_csv.md.

    Atomic write via temp-file-rename. Required columns: ticker, analysis_date,
    rating. Optional columns mirror scripts/backtest.py results.csv schema for
    cross-tool compatibility.
    """
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    fieldnames = [
        "ticker",
        "analysis_date",
        "rating",
        "gate_threshold",
        "a3_threshold",
        "model_deep",
        "model_quick",
        "run_seconds",
        "error",
    ]
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "ticker": r.get("ticker", ""),
                    "analysis_date": resolved_date,
                    "rating": r.get("rating", ""),
                    "gate_threshold": r.get("gate_threshold", ""),
                    "a3_threshold": r.get("a3_threshold", ""),
                    "model_deep": r.get("model_deep", ""),
                    "model_quick": r.get("model_quick", ""),
                    "run_seconds": f"{r.get('run_seconds', 0):.2f}" if r.get("run_seconds") else "",
                    "error": r.get("error", "") or "",
                }
            )
    tmp.replace(path)


if __name__ == "__main__":
    sys.exit(app() or 0)
