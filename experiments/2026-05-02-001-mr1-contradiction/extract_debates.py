"""Walk ~/.tradingagents/logs/ and extract bull/bear debate pairs to JSONL.

One JSONL line per (ticker, date) pair, with the bull and bear text.
Output goes next to this script as `debates.jsonl`.

Per the experiments/<id>/ convention: this is an experiment-specific tool,
not promoted to scripts/ unless it's reused by a second experiment.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

console = Console()
app = typer.Typer(add_completion=False)


@app.command()
def main(
    logs_dir: Path = typer.Option(
        Path.home() / ".tradingagents" / "logs",
        "--logs-dir",
        help="Root of TradingAgents per-ticker state logs.",
    ),
    out: Path = typer.Option(
        Path(__file__).parent / "debates.jsonl",
        "--out",
        help="Where to write the JSONL.",
    ),
):
    """Extract (ticker, date, bull_history, bear_history) from every state log."""
    if not logs_dir.exists():
        console.print(f"[red]Logs directory not found: {logs_dir}[/red]")
        raise typer.Exit(1)

    state_files = sorted(logs_dir.glob("*/TradingAgentsStrategy_logs/full_states_log_*.json"))
    if not state_files:
        console.print(f"[red]No state logs found under {logs_dir}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Found {len(state_files)} state logs[/cyan]")

    n_ok = 0
    n_skipped = 0
    with open(out, "w", encoding="utf-8") as fout:
        for path in state_files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as e:
                console.print(f"[yellow]skip {path.name}: {e}[/yellow]")
                n_skipped += 1
                continue

            ids = data.get("investment_debate_state", {}) or {}
            bull = ids.get("bull_history", "") or ""
            bear = ids.get("bear_history", "") or ""

            if not bull.strip() or not bear.strip():
                console.print(f"[yellow]skip {path.name}: empty bull or bear history[/yellow]")
                n_skipped += 1
                continue

            row = {
                "ticker": data.get("company_of_interest", ""),
                "trade_date": data.get("trade_date", ""),
                "source_file": str(path),
                "bull_history": bull,
                "bear_history": bear,
                "bull_chars": len(bull),
                "bear_chars": len(bear),
            }
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_ok += 1

    console.print(f"\n[cyan]Done.[/cyan] {n_ok} pairs extracted, {n_skipped} skipped.")
    console.print(f"  Output: {out}")


if __name__ == "__main__":
    app()
