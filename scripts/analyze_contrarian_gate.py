"""Spec 003 FR-008: post-hoc contrarian-gate impact analyzer.

Reads per-propagate state log JSON files (under ~/.tradingagents/logs/states/
or any --state-logs dir), extracts the `contrarian_gate` annotation block
(emitted when contrarian_gate_mode != "off"), and stratifies realized α by
`would_fire`.

Output: a markdown report at the path given by --out.

Zero LLM cost. Reuses fetch_returns for forward α.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from tradingagents.graph.trading_graph import fetch_returns
from tradingagents.signals.evaluation import _spearman_ic


def _iter_state_logs(state_logs_dir: Path):
    """Walk all .json files under state_logs_dir and yield parsed dicts."""
    for path in sorted(state_logs_dir.rglob("*.json")):
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        yield path, data


def _extract_gate_rows(state_logs_dir: Path) -> list[dict]:
    """Pull (ticker, date, gate_block, pre_rating, post_rating) tuples for all
    propagates that emitted a contrarian_gate annotation."""
    out = []
    for path, state in _iter_state_logs(state_logs_dir):
        gate = state.get("contrarian_gate")
        if not gate or not isinstance(gate, dict):
            continue
        ticker = state.get("company_of_interest") or ""
        date = str(state.get("trade_date") or "")[:10]
        if not ticker or not date:
            continue
        out.append(
            {
                "path": str(path),
                "ticker": ticker,
                "date": date,
                "mode": gate.get("mode"),
                "would_fire": gate.get("would_fire"),
                "gate_fired": gate.get("gate_fired"),
                "feature_value": gate.get("feature_value"),
                "percentile": gate.get("percentile"),
                "n_history": gate.get("n_history"),
                "gate_skipped": gate.get("gate_skipped"),
                "pre_rating": gate.get("pm_rating_pre_gate"),
                "post_rating": gate.get("pm_rating_post_gate"),
            }
        )
    return out


def _enrich_with_alpha(rows: list[dict], horizons: tuple[int, ...] = (5, 21, 90)) -> None:
    for r in rows:
        for h in horizons:
            _, alpha, _ = fetch_returns(r["ticker"], r["date"], holding_days=h)
            r[f"alpha_{h}d"] = alpha


def _summary_table_md(rows: list[dict], horizon: int) -> list[str]:
    lines = []
    fire_rows = [
        r for r in rows if r.get("would_fire") is True and r.get(f"alpha_{horizon}d") is not None
    ]
    nofire_rows = [
        r for r in rows if r.get("would_fire") is False and r.get(f"alpha_{horizon}d") is not None
    ]

    lines.append(f"### α @ {horizon}d stratified by `would_fire`\n")
    lines.append("| Bucket | n | Mean α | Median α | Hit rate |")
    lines.append("|---|---:|---:|---:|---:|")
    for label, bucket in [
        ("would_fire = True", fire_rows),
        ("would_fire = False", nofire_rows),
    ]:
        if not bucket:
            lines.append(f"| {label} | 0 | — | — | — |")
            continue
        alphas = [r[f"alpha_{horizon}d"] for r in bucket]
        mean_a = statistics.mean(alphas)
        median_a = statistics.median(alphas)
        hit = sum(1 for a in alphas if a > 0) / len(alphas)
        lines.append(
            f"| {label} | {len(bucket)} | {mean_a * 100:+.2f}% | {median_a * 100:+.2f}% | {hit:.1%} |"
        )
    lines.append("")
    return lines


def _ic_table_md(rows: list[dict], horizon: int) -> list[str]:
    """IC of would_fire (treated as +1/-1) vs forward α."""
    pairs = []
    for r in rows:
        wf = r.get("would_fire")
        a = r.get(f"alpha_{horizon}d")
        if wf is None or a is None:
            continue
        # would_fire=True (gate says "anti-bullish") → +1 (contrarian signal "on")
        # would_fire=False → -1
        pairs.append((1.0 if wf else -1.0, float(a)))
    if len(pairs) < 3:
        return [f"### IC @ {horizon}d\n\nInsufficient n ({len(pairs)} pairs).\n"]
    ic = _spearman_ic(pairs)
    return [
        f"### IC @ {horizon}d\n",
        f"- n pairs: {len(pairs)}",
        f"- Spearman IC (would_fire as +1/-1 vs α): **{ic:+.4f}**",
        "",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-logs",
        type=Path,
        required=True,
        help="Directory containing per-propagate state log JSON files",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Markdown output path",
    )
    args = parser.parse_args()

    rows = _extract_gate_rows(args.state_logs)
    print(f"[load] {len(rows)} propagates with contrarian_gate annotations")
    if not rows:
        args.out.write_text(
            "# Contrarian gate analysis — no annotated propagates found\n\n"
            f"Searched: `{args.state_logs}`\n",
            encoding="utf-8",
        )
        return 0

    print("[fetch] computing forward α at horizons 5d, 21d, 90d...")
    _enrich_with_alpha(rows)

    lines: list[str] = []
    lines.append("# Spec 003 contrarian-gate impact analysis\n")
    lines.append(
        f"Sourced from {len(rows)} propagates with `contrarian_gate` annotations "
        f"under `{args.state_logs}`.\n"
    )
    lines.append("## Coverage\n")
    n_skipped = sum(1 for r in rows if r.get("gate_skipped"))
    n_fire = sum(1 for r in rows if r.get("would_fire") is True)
    n_nofire = sum(1 for r in rows if r.get("would_fire") is False)
    n_overrode = sum(1 for r in rows if r.get("gate_fired") is True)
    by_mode: dict[str, int] = {}
    for r in rows:
        by_mode[r.get("mode", "?")] = by_mode.get(r.get("mode", "?"), 0) + 1
    lines.append(f"- Total annotated propagates: **{len(rows)}**")
    lines.append(f"- Mode distribution: {dict(sorted(by_mode.items()))}")
    lines.append(f"- Gate would_fire = True: **{n_fire}** ({n_fire / len(rows):.1%})")
    lines.append(f"- Gate would_fire = False: **{n_nofire}** ({n_nofire / len(rows):.1%})")
    lines.append(f"- Skipped (insufficient_history / missing / etc): **{n_skipped}**")
    lines.append(f"- Active-mode rating override actually applied: **{n_overrode}**")
    lines.append("")

    for horizon in (5, 21, 90):
        lines.extend(_summary_table_md(rows, horizon))
        lines.extend(_ic_table_md(rows, horizon))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[out] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
