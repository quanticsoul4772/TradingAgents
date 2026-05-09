"""Spec 012 Class 4 macro filter — shadow-mode fire audit.

Walks state logs at ~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/
for state["class_4_macro"] dicts where would_fire_bear=True. Computes per-fire
realized α via tradingagents.graph.trading_graph.fetch_returns. Outputs:

1. Per-fire enumeration (ticker / date / vix_snapshot / would_fire / 21d α)
2. Cumulative would-fire count
3. Mean realized α on would-fire cohort
4. Default-on-flip-readiness verdict per Spec 012 SC-010
   (n ≥ 30 fires AND mean realized α ≥ -1pp at 21d)

Sister to scripts/run_shadow_aggregator.py (Spec 001 shadow-audit pattern).

Usage:
    python scripts/class4_macro_shadow_audit.py
    python scripts/class4_macro_shadow_audit.py --logs-dir /custom/logs
    python scripts/class4_macro_shadow_audit.py --json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.graph.trading_graph import fetch_returns  # noqa: E402
from tradingagents.signals.backfill import default_logs_dir, walk_state_logs  # noqa: E402

console = Console()
app = typer.Typer(add_completion=False)

SC_010_FIRE_FLOOR = 30
SC_010_ALPHA_FLOOR_PP = -1.0
HOLDING_DAYS = 21


def _extract_fires(logs_dir: Path) -> list[dict]:
    """Walk state logs; return list of would-fire-bear records.

    Each record: {ticker, trade_date, vix_snapshot, vix_threshold,
                  bear_mode, would_fire_bear, fired_bear, pre_rating,
                  post_rating}
    """
    fires: list[dict] = []
    for ticker, log_path in walk_state_logs(logs_dir):
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        c4 = data.get("class_4_macro")
        if not isinstance(c4, dict):
            continue
        if not c4.get("would_fire_bear"):
            continue
        # state log filename encodes the date
        trade_date = log_path.stem.replace("full_states_log_", "")
        rec = {"ticker": ticker, "trade_date": trade_date, **c4}
        fires.append(rec)
    return fires


def _enrich_with_alpha(fires: list[dict]) -> list[dict]:
    """Add realized 21d α-vs-SPY to each fire record."""
    enriched = []
    for rec in fires:
        try:
            _raw, alpha, _days = fetch_returns(
                rec["ticker"], rec["trade_date"], holding_days=HOLDING_DAYS
            )
        except Exception:
            alpha = None
        rec["realized_alpha_pct"] = (alpha * 100) if alpha is not None else None
        enriched.append(rec)
    return enriched


def _verdict(fires: list[dict]) -> dict:
    """Compute SC-010 default-on-flip-readiness verdict."""
    n_total = len(fires)
    valid = [r for r in fires if r["realized_alpha_pct"] is not None]
    n_valid = len(valid)
    if n_valid == 0:
        return {
            "n_total": n_total,
            "n_valid_alpha": 0,
            "mean_alpha_pct": None,
            "ready_for_default_on_flip": False,
            "reason": "no fires with valid forward returns yet",
        }
    mean_alpha = sum(r["realized_alpha_pct"] for r in valid) / n_valid
    sc_010_n_pass = n_valid >= SC_010_FIRE_FLOOR
    sc_010_alpha_pass = mean_alpha >= SC_010_ALPHA_FLOOR_PP
    ready = sc_010_n_pass and sc_010_alpha_pass
    if not sc_010_n_pass:
        reason = f"n={n_valid} < {SC_010_FIRE_FLOOR} required"
    elif not sc_010_alpha_pass:
        reason = f"mean α {mean_alpha:+.2f}pp < {SC_010_ALPHA_FLOOR_PP}pp floor"
    else:
        reason = f"n={n_valid} ≥ {SC_010_FIRE_FLOOR} AND mean α {mean_alpha:+.2f}pp ≥ {SC_010_ALPHA_FLOOR_PP}pp"
    return {
        "n_total": n_total,
        "n_valid_alpha": n_valid,
        "mean_alpha_pct": mean_alpha,
        "ready_for_default_on_flip": ready,
        "reason": reason,
    }


@app.command()
def main(
    logs_dir: Path = typer.Option(
        None, "--logs-dir", help="Path to logs directory (default: ~/.tradingagents/logs)."
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON instead of rich table."),
):
    """Audit Class 4 shadow-mode fires + assess SC-010 readiness."""
    if logs_dir is None:
        logs_dir = default_logs_dir()
    if not logs_dir.exists():
        console.print(f"[red]Logs dir not found: {logs_dir}[/red]")
        raise typer.Exit(1)

    fires = _extract_fires(logs_dir)
    fires = _enrich_with_alpha(fires)
    verdict = _verdict(fires)

    if as_json:
        out = {
            "fires": fires,
            "verdict": verdict,
            "sc_010_thresholds": {
                "n_fires_floor": SC_010_FIRE_FLOOR,
                "mean_alpha_floor_pp": SC_010_ALPHA_FLOOR_PP,
                "holding_days": HOLDING_DAYS,
            },
        }
        console.print_json(json.dumps(out, default=str))
        return

    if not fires:
        console.print("[yellow]No would_fire_bear instances found in state logs.[/yellow]")
        console.print(f"Searched: {logs_dir}")
        return

    table = Table(title=f"Class 4 macro shadow-mode fire audit ({len(fires)} would-fires)")
    table.add_column("Ticker")
    table.add_column("Date")
    table.add_column("VIX", justify="right")
    table.add_column("Threshold", justify="right")
    table.add_column("Pre→Post")
    table.add_column("21d α %", justify="right")
    for rec in fires:
        alpha_str = (
            f"{rec['realized_alpha_pct']:+.2f}" if rec["realized_alpha_pct"] is not None else "—"
        )
        table.add_row(
            rec["ticker"],
            rec["trade_date"],
            f"{rec.get('vix_snapshot', 0.0):.2f}" if rec.get("vix_snapshot") else "—",
            f"{rec.get('vix_threshold', 0.0):.2f}",
            f"{rec.get('pre_rating', '?')}→{rec.get('post_rating', '?')}",
            alpha_str,
        )
    console.print(table)
    console.print()
    console.print(f"[bold]SC-010 readiness verdict[/bold]: {verdict['reason']}")
    console.print(
        f"  n_total={verdict['n_total']} / n_valid_alpha={verdict['n_valid_alpha']} / "
        f"mean α={verdict['mean_alpha_pct']:+.2f}pp"
        if verdict["mean_alpha_pct"] is not None
        else f"  n_total={verdict['n_total']} / n_valid_alpha={verdict['n_valid_alpha']}"
    )
    console.print(
        f"  [{'green' if verdict['ready_for_default_on_flip'] else 'yellow'}]"
        f"Default-on flip ready: {verdict['ready_for_default_on_flip']}[/]"
    )


if __name__ == "__main__":
    app()
