"""Single-call baseline: feed the framework's analyst reports to ONE Claude call.

Tests the architectural premise of the multi-agent framework: does the bull/bear
debate + research synthesis + trader + risk debate + portfolio manager pipeline
add predictive signal vs a single call on the same intermediate inputs?

For each (ticker, date) pair, this script:
  1. Loads the existing state log at ~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/
     full_states_log_<DATE>.json (produced by a prior backtest run).
  2. Extracts the three analyst reports (market, news, fundamentals).
  3. Sends them in ONE structured-output Claude call with the same 5-tier scale
     the framework's PortfolioManager uses.
  4. Writes results to a CSV in the same shape as scripts/backtest.py output,
     so scripts/analyze_backtest.py works on it without modification.

Usage:
    python scripts/single_call_baseline.py \\
        --ticker NVDA \\
        --dates 2026-01-30,2026-02-06,...,2026-04-03 \\
        --experiment-id 2026-05-03-003-single-call-baseline-nvda \\
        --out experiments/2026-05-03-003-single-call-baseline-nvda/results.csv
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path

import typer
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field
from rich.console import Console

# Path setup so we can import the project's PortfolioRating enum.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.agents.schemas import PortfolioRating  # noqa: E402

# override=True: project's .env wins over shell env (matches scripts/backtest.py).
load_dotenv(PROJECT_ROOT / ".env", override=True)

console = Console()

LOGS_BASE = Path.home() / ".tradingagents" / "logs"

CSV_HEADER = [
    "ticker",
    "analysis_date",
    "rating",
    "error",
    "run_seconds",
    "deep_model",
    "quick_model",
    "debate_rounds",
    "analysts",
    "experiment_id",
]


class BaselineDecision(BaseModel):
    """Single-call structured output. Mirrors the framework's PortfolioRating
    scale so analyze_backtest.py + check_rating_distribution.py work unmodified.
    """

    rating: PortfolioRating = Field(
        description=(
            "Final 5-tier rating: Buy / Overweight / Hold / Underweight / Sell. "
            "Reserve Hold for cases where the evidence is genuinely balanced. "
            "Commit to the side with stronger arguments otherwise."
        ),
    )
    brief_reason: str = Field(
        description="Two-sentence justification citing the strongest report evidence.",
    )


_PROMPT_TEMPLATE = """You are a portfolio manager. Three analyst reports for {ticker} as of {date} \
are below. Predict the 5-day forward direction of {ticker} relative to SPY using \
the 5-tier rating scale (Buy / Overweight / Hold / Underweight / Sell).

Output schema:
- rating: one of the 5 tiers
- brief_reason: 2 sentences citing strongest evidence

Rating-scale guidance:
- Buy: high-conviction outperform vs SPY (>2% expected 5-day alpha)
- Overweight: moderate outperform expected (~1% expected alpha)
- Hold: neutral, expect to track SPY
- Underweight: moderate underperform expected (~−1% alpha)
- Sell: high-conviction underperform (<−2% alpha)

Reserve Hold ONLY for genuinely balanced evidence. If the reports lean bullish, \
commit to Buy/Overweight; if bearish, commit to Sell/Underweight.

# Market analyst report

{market_report}

# News analyst report

{news_report}

# Fundamentals analyst report

{fundamentals_report}
"""


def load_state_log(ticker: str, date: str) -> dict:
    """Read the saved state-log JSON for the given (ticker, date)."""
    path = LOGS_BASE / ticker / "TradingAgentsStrategy_logs" / f"full_states_log_{date}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"State log not found at {path}. Run scripts/backtest.py for "
            f"{ticker} {date} first to populate it."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def call_baseline(llm: ChatAnthropic, ticker: str, date: str) -> tuple[str, float, str | None]:
    """Issue one structured-output call. Returns (rating, elapsed_sec, error)."""
    state = load_state_log(ticker, date)

    market = state.get("market_report", "")
    news = state.get("news_report", "")
    fundamentals = state.get("fundamentals_report", "")
    if not (market and news and fundamentals):
        return "", 0.0, "missing one or more analyst reports in state log"

    prompt = _PROMPT_TEMPLATE.format(
        ticker=ticker,
        date=date,
        market_report=market,
        news_report=news,
        fundamentals_report=fundamentals,
    )

    structured = llm.with_structured_output(BaselineDecision)
    t0 = time.perf_counter()
    try:
        result = structured.invoke(prompt)
    except Exception as e:
        return "", time.perf_counter() - t0, f"{type(e).__name__}: {e}"
    elapsed = time.perf_counter() - t0
    return result.rating.value, elapsed, None


def append_row(out_path: Path, row: dict) -> None:
    """Append one CSV row, writing the header on first call."""
    write_header = not out_path.exists() or out_path.stat().st_size == 0
    with open(out_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def existing_pairs(out_path: Path) -> set[tuple[str, str]]:
    """Resumability: which (ticker, date) pairs are already in the CSV."""
    if not out_path.exists():
        return set()
    pairs = set()
    with open(out_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pairs.add((row["ticker"], row["analysis_date"]))
    return pairs


app = typer.Typer(add_completion=False)


@app.command()
def main(
    ticker: str = typer.Option(..., "--ticker", help="Stock ticker (e.g. NVDA)."),
    dates: str = typer.Option(
        ...,
        "--dates",
        help="Comma-separated analysis dates (YYYY-MM-DD,YYYY-MM-DD,...).",
    ),
    out: Path = typer.Option(..., "--out", help="Output CSV path."),
    experiment_id: str = typer.Option(
        ..., "--experiment-id", help="Experiment ID for the CSV column."
    ),
    model: str = typer.Option(
        "claude-sonnet-4-6",
        "--model",
        help="Claude model. Default matches framework's deep_think_llm for fair comparison.",
    ),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompt."),
):
    """Run the single-call baseline over a list of (ticker, date) pairs."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]ANTHROPIC_API_KEY not set in env or .env[/red]")
        raise typer.Exit(1)

    date_list = [d.strip() for d in dates.split(",") if d.strip()]
    out.parent.mkdir(parents=True, exist_ok=True)
    done = existing_pairs(out)
    pending = [d for d in date_list if (ticker, d) not in done]

    console.print("[bold]Single-call baseline[/bold]")
    console.print(f"  Ticker:        {ticker}")
    console.print(f"  Dates:         {len(date_list)} ({len(pending)} pending)")
    console.print(f"  Model:         {model}")
    console.print(f"  Out:           {out}")
    console.print(f"  Experiment ID: {experiment_id}")
    console.print(f"  Est. cost:     ~${len(pending) * 0.10:.2f} (rough; ~$0.10/call)")

    if not pending:
        console.print("[green]Nothing to do — all pairs already in CSV.[/green]")
        return

    if not yes and not typer.confirm("Proceed?"):
        raise typer.Exit(0)

    llm = ChatAnthropic(model=model, temperature=0.0)
    t_start = time.perf_counter()
    n_ok = n_err = 0

    for i, date in enumerate(pending, 1):
        console.print(f"\n[bold]Run {i}/{len(pending)}[/bold]  {ticker}  {date}")
        rating, elapsed, error = call_baseline(llm, ticker, date)
        if error:
            console.print(f"  [red]error: {error}[/red]")
            n_err += 1
        else:
            console.print(f"  → rating: {rating}  ({elapsed:.1f}s)")
            n_ok += 1

        append_row(
            out,
            {
                "ticker": ticker,
                "analysis_date": date,
                "rating": rating,
                "error": error or "",
                "run_seconds": f"{elapsed:.2f}",
                "deep_model": model,
                "quick_model": "",  # n/a — single call
                "debate_rounds": 0,
                "analysts": "single-call-baseline",
                "experiment_id": experiment_id,
            },
        )

    total_min = (time.perf_counter() - t_start) / 60
    console.print(
        f"\n[bold]Done.[/bold]  {n_ok} ok, {n_err} errors, {total_min:.1f} min wall-clock"
    )
    console.print(f"  Output: {out.resolve()}")
    console.print(f"  Next:   python scripts/analyze_backtest.py {out}")


if __name__ == "__main__":
    app()
