"""Paper-trading harness CLI. Spec: ``specs/002-paper-trading-harness/contracts/cli.md``.

Subcommands:
  - ``replay`` — deterministic backtest over a date range with a fixed CSV
  - ``step``   — single-trading-day idempotent update (US2)
  - ``status`` — read-only current-state inspection (US3)

The harness has zero LLM cost (FR-011, SC-008). All commands consume
pre-generated signals; signal generation is the operator's responsibility
via ``daily_signals.py``.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console

# Ensure repo root is importable when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402
from tradingagents.paper.digest import digest_filename, render_digest  # noqa: E402
from tradingagents.paper.engine import PaperTradingEngine  # noqa: E402
from tradingagents.paper.errors import PortfolioStateError  # noqa: E402
from tradingagents.paper.policy import PolicySnapshot  # noqa: E402
from tradingagents.paper.portfolio import Portfolio  # noqa: E402
from tradingagents.paper.pricing import close_on_or_before  # noqa: E402
from tradingagents.paper.state import (  # noqa: E402
    append_event,
    events_path_for,
    load_portfolio,
    save_portfolio,
    state_path_for,
)

logger = logging.getLogger(__name__)
console = Console()
app = typer.Typer(add_completion=False, help="Paper-trading harness on top of daily_signals.py")


# -- helpers -----------------------------------------------------------------


def _resolve_state_dir(override: str | None) -> Path:
    if override:
        return Path(override).expanduser()
    return Path(DEFAULT_CONFIG["paper_state_dir"]).expanduser()


def _resolve_digest_dir(override: str | None) -> Path:
    if override:
        return Path(override).expanduser()
    return Path(DEFAULT_CONFIG["paper_digest_dir"]).expanduser()


def _resolve_sectors_cache(state_dir: Path) -> Path:
    return state_dir / "sectors.json"


def _load_or_init_portfolio(
    state_path: Path,
    portfolio_id: str,
    inception_date: date,
    starting_equity: Decimal,
    policy: PolicySnapshot,
) -> Portfolio:
    if state_path.exists():
        return load_portfolio(state_path)
    return Portfolio(
        portfolio_id=portfolio_id,
        inception_date=inception_date,
        cash=starting_equity,
        starting_equity=starting_equity,
        policy_snapshot=policy,
    )


def _read_signals_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        console.print(f"[red][error][/red] signals CSV not found: {path}")
        raise typer.Exit(2)
    df = pd.read_csv(path)
    required = {"ticker", "analysis_date", "rating"}
    missing = required - set(df.columns)
    if missing:
        console.print(f"[red][error][/red] signals CSV missing required columns: {sorted(missing)}")
        raise typer.Exit(2)
    return df


def _signals_for_date(df: pd.DataFrame, target: date) -> dict[str, str]:
    target_str = target.isoformat()
    rows = df[df["analysis_date"] == target_str]
    out: dict[str, str] = {}
    for _, row in rows.iterrows():
        ticker = str(row["ticker"]).upper().strip()
        rating = row.get("rating")
        if not isinstance(rating, str) or not rating.strip():
            continue
        out[ticker] = rating.strip()  # last row wins per signals_csv.md rule 1
    return out


def _load_policy(path: Path | None) -> PolicySnapshot:
    if path is None:
        return PolicySnapshot()
    raw = json.loads(path.read_text(encoding="utf-8"))
    decimal_fields = {
        "target_per_position_pct",
        "cash_buffer_pct",
        "per_sector_cap_pct",
        "per_position_cap_pct",
        "entry_slippage_bps",
        "exit_slippage_bps",
    }
    kwargs = {k: (Decimal(v) if k in decimal_fields else v) for k, v in raw.items()}
    return PolicySnapshot(**kwargs)


def _trading_days_in_range(benchmark: str, start: date, end: date) -> list[date]:
    """Return trading days from start to end (inclusive) using benchmark price index."""
    quote_anchor = close_on_or_before(benchmark, end)
    if quote_anchor is None:
        return []
    # Use yfinance benchmark frame as the trading calendar
    import yfinance as yf

    frame = yf.Ticker(benchmark).history(
        start=start.isoformat(),
        end=(end + timedelta(days=2)).isoformat(),
    )
    if frame.empty:
        return []
    out: list[date] = []
    for ts in frame.index:
        if isinstance(ts, pd.Timestamp):
            d = ts.date()
        else:
            continue
        if start <= d <= end:
            out.append(d)
    return out


def _write_digest(
    digest_dir: Path,
    portfolio: Portfolio,
    today: date,
    step_result,
    mark_prices: dict[str, Decimal],
) -> Path:
    digest_dir.mkdir(parents=True, exist_ok=True)
    md = render_digest(portfolio, today, step_result, mark_prices)
    out = digest_dir / digest_filename(portfolio.portfolio_id, today)
    out.write_text(md, encoding="utf-8")
    return out


def _persist_step(
    portfolio: Portfolio,
    state_path: Path,
    events_path: Path,
    step_result,
    write_state: bool,
) -> None:
    if not write_state:
        return
    save_portfolio(portfolio, state_path)
    for ev in step_result.events:
        append_event(ev, events_path)


# -- replay subcommand -------------------------------------------------------


@app.command("replay")
def replay_cmd(
    signals_csv: Path = typer.Option(..., "--signals-csv", help="Input signals CSV"),
    watchlist: Path = typer.Option(..., "--watchlist", help="Newline-separated tickers"),
    start: str = typer.Option(..., "--start", help="First signal date YYYY-MM-DD"),
    end: str = typer.Option(..., "--end", help="Last signal date YYYY-MM-DD"),
    portfolio_id: str = typer.Option("default", "--portfolio-id"),
    starting_equity: str = typer.Option("100000", "--starting-equity"),
    policy: Path | None = typer.Option(None, "--policy", help="Policy JSON override"),
    digest_dir: str | None = typer.Option(None, "--digest-dir"),
    state_dir: str | None = typer.Option(None, "--state-dir"),
    no_write_state: bool = typer.Option(False, "--no-write-state", help="Dry-run; don't persist"),
    yes: bool = typer.Option(False, "--yes", help="Skip cost-confirmation prompt"),
) -> None:
    """Deterministic backtest over [start, end] using a fixed signals CSV."""
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        console.print("[red][error][/red] --end must be >= --start")
        raise typer.Exit(2)

    if not yes:
        console.print(
            "[yellow]paper_trade replay will run with 0 LLM API calls.[/yellow] "
            "Press ENTER to continue or Ctrl-C to abort."
        )
        try:
            input()
        except (EOFError, KeyboardInterrupt) as exc:
            raise typer.Exit(1) from exc

    snap = _load_policy(policy)
    state_dir_path = _resolve_state_dir(state_dir)
    digest_dir_path = _resolve_digest_dir(digest_dir)
    sectors_cache = _resolve_sectors_cache(state_dir_path)
    state_path = state_path_for(state_dir_path, portfolio_id)
    events_path = events_path_for(state_dir_path, portfolio_id)

    portfolio = _load_or_init_portfolio(
        state_path, portfolio_id, start_date, Decimal(starting_equity), snap
    )

    df = _read_signals_csv(signals_csv)

    days = _trading_days_in_range(snap.benchmark, start_date, end_date)
    if not days:
        console.print(f"[red][error][/red] no trading days in range {start} to {end}")
        raise typer.Exit(2)

    console.print(f"Processing {len(days)} trading days from {start} to {end}...")

    engine = PaperTradingEngine(portfolio, sectors_cache)
    total_entries = 0
    total_exits = 0

    for day in days:
        signals = _signals_for_date(df, day)
        result = engine.step(day, signals)
        if result.was_already_processed:
            console.print(f"  {day.isoformat()}: already processed; skipping")
            _persist_step(portfolio, state_path, events_path, result, not no_write_state)
            continue
        marks: dict[str, Decimal] = {}
        for t in portfolio.positions:
            mark = close_on_or_before(t, day)
            if mark is not None:
                marks[t] = mark[1]
        digest_path = _write_digest(digest_dir_path, portfolio, day, result, marks)
        _persist_step(portfolio, state_path, events_path, result, not no_write_state)
        total_entries += len(result.entries)
        total_exits += len(result.exits)
        console.print(
            f"  {day.isoformat()}: {len(result.entries)} entries, {len(result.exits)} exits, "
            f"{len(result.skips)} skips → {digest_path.name}"
        )

    # Final summary
    final_marks: dict[str, Decimal] = {}
    for t in portfolio.positions:
        mark = close_on_or_before(t, end_date)
        if mark is not None:
            final_marks[t] = mark[1]
    final_equity = portfolio.equity(final_marks)
    final_bench = (
        portfolio.equity_curve[-1].benchmark_equity
        if portfolio.equity_curve
        else portfolio.starting_equity
    )
    itd_return_pct = (final_equity - portfolio.starting_equity) / portfolio.starting_equity * 100
    itd_bench_pct = (final_bench - portfolio.starting_equity) / portfolio.starting_equity * 100
    itd_alpha_pct = itd_return_pct - itd_bench_pct

    console.print()
    console.print("[bold]Replay complete[/bold]")
    console.print(f"  Entries: {total_entries}, Exits: {total_exits}")
    console.print(f"  Final equity: ${final_equity:,.2f}")
    console.print(f"  ITD return: {itd_return_pct:+.2f}%")
    console.print(f"  ITD α vs {snap.benchmark}: {itd_alpha_pct:+.2f}%")


# -- step subcommand ---------------------------------------------------------


@app.command("step")
def step_cmd(
    signals_csv: Path = typer.Option(..., "--signals-csv"),
    target_date: str | None = typer.Option(None, "--date"),
    portfolio_id: str = typer.Option("default", "--portfolio-id"),
    starting_equity: str = typer.Option("100000", "--starting-equity"),
    policy: Path | None = typer.Option(None, "--policy"),
    digest_dir: str | None = typer.Option(None, "--digest-dir"),
    state_dir: str | None = typer.Option(None, "--state-dir"),
    no_write_state: bool = typer.Option(False, "--no-write-state"),
) -> None:
    """Process a single trading day. Idempotent."""
    today = date.fromisoformat(target_date) if target_date else datetime.now().date()
    snap = _load_policy(policy)
    state_dir_path = _resolve_state_dir(state_dir)
    digest_dir_path = _resolve_digest_dir(digest_dir)
    sectors_cache = _resolve_sectors_cache(state_dir_path)
    state_path = state_path_for(state_dir_path, portfolio_id)
    events_path = events_path_for(state_dir_path, portfolio_id)

    portfolio = _load_or_init_portfolio(
        state_path, portfolio_id, today, Decimal(starting_equity), snap
    )
    df = _read_signals_csv(signals_csv)
    signals = _signals_for_date(df, today)

    engine = PaperTradingEngine(portfolio, sectors_cache)
    result = engine.step(today, signals)

    if result.was_already_processed:
        # Append the skip event but DO NOT touch state file (SC-002 byte-identity)
        if not no_write_state:
            for ev in result.events:
                append_event(ev, events_path)
        console.print(f"step: {today} already processed; no state change")
        return

    marks: dict[str, Decimal] = {}
    for t in portfolio.positions:
        mark = close_on_or_before(t, today)
        if mark is not None:
            marks[t] = mark[1]
    _write_digest(digest_dir_path, portfolio, today, result, marks)
    _persist_step(portfolio, state_path, events_path, result, not no_write_state)

    final_equity = portfolio.equity(marks)
    bench = portfolio.equity_curve[-1].benchmark_equity
    alpha_pct = (final_equity - bench) / portfolio.starting_equity * 100
    console.print(
        f"step OK: D={today}, equity=${final_equity:,.2f}, "
        f"{alpha_pct:+.2f}% vs {snap.benchmark}, "
        f"opens={len(result.entries)}, closes={len(result.exits)}"
    )


# -- status subcommand -------------------------------------------------------


@app.command("status")
def status_cmd(
    portfolio_id: str = typer.Option("default", "--portfolio-id"),
    state_dir: str | None = typer.Option(None, "--state-dir"),
    mark_to_date: str | None = typer.Option(None, "--mark-to-date"),
) -> None:
    """Read-only inspection of current portfolio state."""
    state_dir_path = _resolve_state_dir(state_dir)
    state_path = state_path_for(state_dir_path, portfolio_id)
    if not state_path.exists():
        console.print(f"No portfolio found at {state_path}")
        raise typer.Exit(0)
    portfolio = load_portfolio(state_path)

    target = date.fromisoformat(mark_to_date) if mark_to_date else datetime.now().date()
    marks: dict[str, Decimal] = {}
    for t in portfolio.positions:
        mark = close_on_or_before(t, target)
        if mark is not None:
            marks[t] = mark[1]

    md = render_digest(portfolio, target, None, marks)
    console.print(md)


def main() -> None:
    try:
        app()
    except PortfolioStateError as e:
        console.print(f"[red]{e.operator_line()}[/red]")
        raise typer.Exit(3) from e


if __name__ == "__main__":
    main()
