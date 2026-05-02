"""Backtest harness — loop propagate() over a (ticker, date) grid.

Writes one row per run to a CSV. Resumable: re-running with the same --out
skips (ticker, date) pairs already present (errors included, to avoid
re-burning tokens on deterministic failures).

The companion analyzer (scripts/analyze_backtest.py) reads this CSV and
computes realized 5-day forward returns + alpha vs SPY per row to evaluate
whether the framework's ratings carry signal.
"""

from __future__ import annotations

import csv
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import typer
from dotenv import load_dotenv
from rich.console import Console

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.experiments.ids import validate_id
from tradingagents.experiments.overrides import apply_overrides, parse_override
from tradingagents.graph.trading_graph import TradingAgentsGraph

load_dotenv()
load_dotenv(".env.enterprise", override=False)

logger = logging.getLogger(__name__)
console = Console()
app = typer.Typer(add_completion=False)

# experiment_id at the END for backward compat with pre-cleanup CSVs (per R-004).
CSV_FIELDS = [
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

# Rough average for Anthropic Sonnet-deep + Haiku-quick + 1/1 rounds + 3 analysts.
COST_PER_RUN_USD = 0.50

FREQ_MAP = {
    "W": "W-FRI",
    "2W": "2W-FRI",
    "M": "BM",
}

# Map config-key -> the named flag that also sets it. Used to detect conflicts
# between --config-override KEY=VALUE and an explicit named flag (per FR-010).
_NAMED_FLAG_KEYS = {
    "llm_provider": "--provider",
    "deep_think_llm": "--deep-model",
    "quick_think_llm": "--quick-model",
    "anthropic_effort": "--anthropic-effort",
    "max_debate_rounds": "--debate-rounds",
    "max_risk_discuss_rounds": "--debate-rounds",
}


def _parse_csv_list(value: str) -> list[str]:
    return [s.strip() for s in value.split(",") if s.strip()]


def _load_tickers_file(path: Path) -> list[str]:
    """Read one-ticker-per-line from path; strip `#` comments and blanks."""
    tickers: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            tickers.append(line)
    return tickers


def _resolve_tickers(tickers_arg: str | None, tickers_file: Path | None) -> list[str]:
    """Resolve ticker list with priority: --tickers > --tickers-file > ./tickers.txt > fallback."""
    if tickers_arg:
        return _parse_csv_list(tickers_arg)
    if tickers_file:
        return _load_tickers_file(tickers_file)
    default_path = Path("tickers.txt")
    if default_path.exists():
        return _load_tickers_file(default_path)
    return _parse_csv_list("NVDA,AAPL,MSFT,JPM,JNJ")


def _build_grid(tickers: list[str], start: str, end: str, frequency: str) -> list[tuple[str, str]]:
    """Cross-product of tickers × dates, snapped to business days, future-trimmed."""
    pd_freq = FREQ_MAP.get(frequency, frequency)
    raw_dates = pd.date_range(start=start, end=end, freq=pd_freq)
    cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=7)
    dates = []
    for d in raw_dates:
        if d > cutoff:
            continue
        if d.weekday() >= 5:
            d = d - pd.Timedelta(days=d.weekday() - 4)
        dates.append(d.strftime("%Y-%m-%d"))
    seen = set()
    dates = [d for d in dates if not (d in seen or seen.add(d))]
    return [(t, d) for t in tickers for d in dates]


def _load_done(out_path: Path) -> set[tuple[str, str]]:
    """Return (ticker, analysis_date) pairs already present in `out_path`."""
    if not out_path.exists():
        return set()
    with open(out_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return {(row["ticker"], row["analysis_date"]) for row in reader}


def _ensure_header(out_path: Path) -> None:
    """Create the CSV with header if it doesn't exist; tolerate older schemas in place."""
    if out_path.exists():
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()


def _append_row(out_path: Path, row: dict) -> None:
    """Append `row` to `out_path`. Caller ensures header exists."""
    with open(out_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writerow(row)


def _warn_override_conflicts(overrides: list[str], named_flag_set_keys: set[str]) -> None:
    """Emit a warning per --config-override that overrides a named-flag-set key (FR-010)."""
    for spec in overrides:
        try:
            key, _value = parse_override(spec)
        except ValueError:
            continue  # bad overrides are caught later by apply_overrides
        if key in named_flag_set_keys and key in _NAMED_FLAG_KEYS:
            console.print(
                f"[yellow]warning:[/yellow] --config-override {spec} overrides "
                f"{_NAMED_FLAG_KEYS[key]} (override wins)"
            )


def _autosync_params_json(
    experiment_id: str,
    overrides: list[str],
    explicit_flags: dict[str, Any],
    experiments_root: Path = Path("experiments"),
) -> None:
    """Write effective overrides into experiments/<id>/PARAMS.json per R-007.

    No-op if the experiment dir doesn't exist or no overrides given.
    Refuses to overwrite an existing non-empty config_overrides block.
    """
    if not overrides:
        return
    exp_dir = experiments_root / experiment_id
    if not exp_dir.exists():
        console.print(
            f"[yellow]warning:[/yellow] experiments/{experiment_id}/ doesn't exist; "
            "skipping PARAMS.json auto-sync. Run scripts/new_experiment.py first."
        )
        return

    params_path = exp_dir / "PARAMS.json"
    override_dict = {parse_override(s)[0]: parse_override(s)[1] for s in overrides}

    if params_path.exists():
        try:
            existing = json.loads(params_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            console.print(
                f"[red]error:[/red] {params_path} is not valid JSON ({e}); "
                "skipping auto-sync. Fix the file by hand."
            )
            return
        if existing.get("config_overrides"):
            console.print(
                f"[yellow]warning:[/yellow] {params_path} already has non-empty "
                "config_overrides; skipping auto-sync to preserve manual annotations."
            )
            return
        existing["config_overrides"] = override_dict
        if explicit_flags and not existing.get("explicit_flags"):
            existing["explicit_flags"] = explicit_flags
        params_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    else:
        # Fresh PARAMS.json since user didn't run new_experiment.py first.
        from tradingagents.experiments.templates import render_params_json

        params = json.loads(render_params_json())
        params["config_overrides"] = override_dict
        if explicit_flags:
            params["explicit_flags"] = explicit_flags
        params_path.write_text(json.dumps(params, indent=2) + "\n", encoding="utf-8")
    console.print(f"[cyan]synced overrides into[/cyan] {params_path}")


@app.command()
def main(
    tickers: str | None = typer.Option(
        None,
        "--tickers",
        help="Comma-separated ticker symbols. Overrides --tickers-file and ./tickers.txt.",
    ),
    tickers_file: Path | None = typer.Option(
        None,
        "--tickers-file",
        help="Path to a one-ticker-per-line file (`#` comments allowed). "
        "Defaults to ./tickers.txt if present, else a built-in 5-ticker fallback.",
    ),
    start: str | None = typer.Option(
        None,
        "--start",
        help="ISO date (YYYY-MM-DD). Defaults to 90 days before --end.",
    ),
    end: str | None = typer.Option(
        None,
        "--end",
        help="ISO date (YYYY-MM-DD). Defaults to today.",
    ),
    frequency: str = typer.Option(
        "W",
        "--frequency",
        help="Cadence: W (weekly Fridays), 2W, or M (business month end).",
    ),
    out: Path = typer.Option(Path("backtest_results.csv"), "--out", help="Output CSV path."),
    max_runs: int = typer.Option(
        50, "--max-runs", help="Safety cap on the total number of propagate() calls."
    ),
    analysts: str = typer.Option(
        "market,news,fundamentals",
        "--analysts",
        help="Comma-separated subset of {market, social, news, fundamentals}.",
    ),
    debate_rounds: int = typer.Option(
        1,
        "--debate-rounds",
        help="Sets both max_debate_rounds and max_risk_discuss_rounds.",
    ),
    provider: str = typer.Option("anthropic", "--provider"),
    deep_model: str = typer.Option("claude-sonnet-4-6", "--deep-model"),
    quick_model: str = typer.Option("claude-haiku-4-5", "--quick-model"),
    anthropic_effort: str = typer.Option(
        "",
        "--anthropic-effort",
        help='"low" / "medium" / "high" — only set if your Anthropic model supports extended thinking (Opus). '
        "Sonnet/Haiku reject it. Default empty = unset.",
    ),
    sleep_seconds: float = typer.Option(
        1.0, "--sleep", help="Pause between runs (rate-limit cushion)."
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip cost-estimate confirmation."),
    experiment_id: str = typer.Option(
        "",
        "--experiment-id",
        help="Tag every output row with this Experiment ID (format: <YYYY-MM-DD>-<NNN>-<slug>). "
        "When set with --config-override, also auto-syncs overrides into experiments/<id>/PARAMS.json.",
    ),
    config_override: list[str] = typer.Option(
        [],
        "--config-override",
        help="Override a runtime config key as KEY=VALUE. Repeatable. Type-coerced "
        '(int → float → bool → null → str). Quoted strings (KEY="42") skip coercion.',
    ),
):
    """Run propagate() over a grid and append results to CSV."""
    # Validate experiment_id early so bad input fails fast.
    if experiment_id and not validate_id(experiment_id):
        console.print(
            f"[red]Invalid --experiment-id {experiment_id!r}: "
            "must match <YYYY-MM-DD>-<NNN>-<slug> format.[/red]"
        )
        raise typer.Exit(1)

    # Validate every --config-override before doing anything expensive.
    for spec in config_override:
        try:
            parse_override(spec)
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1) from None

    today = datetime.now().date()
    end_dt = datetime.strptime(end, "%Y-%m-%d").date() if end else today
    start_dt = datetime.strptime(start, "%Y-%m-%d").date() if start else end_dt - timedelta(days=90)

    ticker_list = _resolve_tickers(tickers, tickers_file)
    analyst_list = _parse_csv_list(analysts)

    grid = _build_grid(ticker_list, start_dt.isoformat(), end_dt.isoformat(), frequency)
    if not grid:
        console.print(
            "[red]Empty grid (no business days in range after the 7-day future cutoff). Exiting.[/red]"
        )
        raise typer.Exit(1)

    done = _load_done(out)
    pending = [pair for pair in grid if pair not in done]

    if not pending:
        console.print(
            f"[yellow]All {len(grid)} grid points already in {out}. Nothing to do.[/yellow]"
        )
        raise typer.Exit(0)

    truncated = False
    if len(pending) > max_runs:
        pending = pending[:max_runs]
        truncated = True

    est_cost = len(pending) * COST_PER_RUN_USD
    console.print("[cyan]Backtest plan[/cyan]")
    console.print(f"  Tickers:        {ticker_list}")
    console.print(f"  Date range:     {start_dt} → {end_dt} ({frequency})")
    console.print(f"  Analysts:       {analyst_list}")
    console.print(
        f"  Models:         deep={deep_model} quick={quick_model} effort={anthropic_effort}"
    )
    console.print(f"  Debate rounds:  {debate_rounds}/{debate_rounds}")
    console.print(f"  Output:         {out}")
    if experiment_id:
        console.print(f"  Experiment ID:  {experiment_id}")
    if config_override:
        console.print(f"  Overrides:      {config_override}")
    console.print(
        f"  Grid:           {len(grid)} pairs ({len(done)} already done, {len(pending)} pending)"
    )
    if truncated:
        console.print(f"  [yellow]Truncated to --max-runs={max_runs}[/yellow]")
    console.print(
        f"  Est. cost:      ~${est_cost:.2f} (rough; ${COST_PER_RUN_USD:.2f}/run avg for current Anthropic config)"
    )

    if not yes:
        if not typer.confirm("Proceed?"):
            raise typer.Exit(0)

    # Build the runtime config from named flags first, then apply overrides on top.
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = provider
    config["deep_think_llm"] = deep_model
    config["quick_think_llm"] = quick_model
    if anthropic_effort:
        config["anthropic_effort"] = anthropic_effort
    config["max_debate_rounds"] = debate_rounds
    config["max_risk_discuss_rounds"] = debate_rounds
    config["checkpoint_enabled"] = False
    config["memory_log_path"] = str(out.parent.resolve() / "backtest_memory.md")
    config["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "yfinance",
    }

    # Track which keys were set by named flags so we can warn on override conflicts.
    named_flag_set_keys = {
        "llm_provider",
        "deep_think_llm",
        "quick_think_llm",
        "max_debate_rounds",
        "max_risk_discuss_rounds",
    }
    if anthropic_effort:
        named_flag_set_keys.add("anthropic_effort")

    if config_override:
        _warn_override_conflicts(config_override, named_flag_set_keys)
        config = apply_overrides(config, config_override, allow_unknown=True)

    console.print("\n[cyan]Building graph...[/cyan]")
    ta = TradingAgentsGraph(
        selected_analysts=analyst_list,
        debug=False,
        config=config,
    )

    _ensure_header(out)

    n_ok = 0
    n_err = 0
    wall_start = time.perf_counter()

    for i, (ticker, analysis_date) in enumerate(pending, 1):
        console.print(f"\n[cyan]Run {i}/{len(pending)}[/cyan]  {ticker}  {analysis_date}")
        t0 = time.perf_counter()
        row = {
            "ticker": ticker,
            "analysis_date": analysis_date,
            "rating": "",
            "error": "",
            "run_seconds": 0.0,
            "deep_model": deep_model,
            "quick_model": quick_model,
            "debate_rounds": debate_rounds,
            "analysts": ",".join(analyst_list),
            "experiment_id": experiment_id,
        }
        try:
            _, rating = ta.propagate(ticker, analysis_date)
            row["rating"] = str(rating).strip()
            n_ok += 1
            console.print(f"  → rating: [green]{row['rating']}[/green]")
        except Exception as e:
            row["error"] = f"{type(e).__name__}: {e}"
            n_err += 1
            console.print(f"  → [red]error:[/red] {row['error']}")
        row["run_seconds"] = round(time.perf_counter() - t0, 2)
        _append_row(out, row)

        if i < len(pending):
            time.sleep(sleep_seconds)

    elapsed = time.perf_counter() - wall_start
    console.print(
        f"\n[cyan]Done.[/cyan]  {n_ok} ok, {n_err} errors, {elapsed / 60:.1f} min wall-clock"
    )
    console.print(f"  Output: {out.resolve()}")
    console.print(f"  Next:   python scripts/analyze_backtest.py {out}")

    # Auto-sync overrides into PARAMS.json after successful completion.
    if experiment_id and config_override:
        explicit_flags = {
            "--debate-rounds": debate_rounds,
            "--analysts": analysts,
            "--provider": provider,
            "--deep-model": deep_model,
            "--quick-model": quick_model,
        }
        if anthropic_effort:
            explicit_flags["--anthropic-effort"] = anthropic_effort
        _autosync_params_json(experiment_id, config_override, explicit_flags)


if __name__ == "__main__":
    app()
