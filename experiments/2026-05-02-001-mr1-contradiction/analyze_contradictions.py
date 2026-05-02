"""Score each bull/bear pair for actual contradiction vs parallel monologue.

Per HYPOTHESIS.md, classifies each pair into one of:
- REAL_CONTRADICTION
- PARALLEL_MONOLOGUE
- PARTIAL_OVERLAP
- STRAWMAN

Uses Anthropic structured output (claude-haiku-4-5 by default) per a fixed
rubric. Resumable: re-running skips pairs whose ticker+date appear in the
output JSONL already.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Literal

import typer
from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from rich.console import Console

load_dotenv()

console = Console()
app = typer.Typer(add_completion=False)

ClassificationLabel = Literal[
    "REAL_CONTRADICTION",
    "PARALLEL_MONOLOGUE",
    "PARTIAL_OVERLAP",
    "STRAWMAN",
]


class Classification(BaseModel):
    """Per-pair contradiction classification."""

    label: ClassificationLabel = Field(
        ...,
        description=(
            "REAL_CONTRADICTION: bull and bear identify same specific claims and "
            "reach opposite conclusions on them. "
            "PARALLEL_MONOLOGUE: bull and bear argue different topics that don't "
            "intersect; both could be true. "
            "PARTIAL_OVERLAP: some shared claims with opposite conclusions, but most "
            "of each side doesn't engage the other. "
            "STRAWMAN: one side mischaracterizes the other and rebuts the "
            "misrepresentation."
        ),
    )
    contradiction_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "0.0 = pure parallel monologue (no claims overlap), "
            "1.0 = every major bull claim is directly contradicted by a specific "
            "bear claim and vice versa."
        ),
    )
    shared_claims: list[str] = Field(
        default_factory=list,
        description=(
            "Specific claims that BOTH sides discuss (even if from different angles). "
            "Empty list = pure parallel monologue. Up to 5 entries."
        ),
    )
    bull_only_topics: list[str] = Field(
        default_factory=list,
        description="Topics only the bull addresses. Up to 3 entries.",
    )
    bear_only_topics: list[str] = Field(
        default_factory=list,
        description="Topics only the bear addresses. Up to 3 entries.",
    )
    rationale: str = Field(
        ...,
        description="One-paragraph explanation of the classification, citing specific evidence.",
    )


SYSTEM_PROMPT = """You are a debate-quality analyst. You receive a transcript of a Bull Analyst's argument and a Bear Analyst's argument about the same stock from a multi-agent trading system. Your job is to classify whether they are actually engaging with each other's claims (REAL_CONTRADICTION / PARTIAL_OVERLAP / STRAWMAN) or talking past each other (PARALLEL_MONOLOGUE).

A REAL_CONTRADICTION requires the two sides to identify the SAME specific factual claim (e.g., "P/E ratio of 32 is justified") and reach OPPOSITE conclusions on it.

PARALLEL_MONOLOGUE means the two sides discuss DIFFERENT factual claims (e.g., bull discusses Blackwell ramp, bear discusses regulatory risk) — both could be entirely true and the disagreement is on what matters, not on facts.

Be strict. Vague rhetorical opposition ("the bull is too optimistic about valuation") without specific shared factual claims counts as PARALLEL_MONOLOGUE, not REAL_CONTRADICTION.

Output the structured classification."""

USER_TEMPLATE = """Ticker: {ticker}
Date: {trade_date}

==================== BULL ANALYST ====================
{bull}

==================== BEAR ANALYST ====================
{bear}

Classify this debate."""


def _load_done_keys(out_path: Path) -> set[tuple[str, str]]:
    """Return (ticker, trade_date) pairs already classified."""
    if not out_path.exists():
        return set()
    done = set()
    with open(out_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            done.add((row.get("ticker", ""), row.get("trade_date", "")))
    return done


def _classify_one(
    client: Anthropic,
    model: str,
    ticker: str,
    trade_date: str,
    bull: str,
    bear: str,
) -> Classification:
    """Single Anthropic call returning a typed Classification."""
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        tools=[
            {
                "name": "classify_debate",
                "description": "Submit the debate classification.",
                "input_schema": Classification.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "classify_debate"},
        messages=[
            {
                "role": "user",
                "content": USER_TEMPLATE.format(
                    ticker=ticker, trade_date=trade_date, bull=bull, bear=bear
                ),
            }
        ],
    )
    # Extract the tool_use block.
    for block in response.content:
        if block.type == "tool_use" and block.name == "classify_debate":
            return Classification.model_validate(block.input)
    raise RuntimeError(
        f"No tool_use block in response for {ticker} {trade_date}: {response}"
    )


@app.command()
def main(
    in_path: Path = typer.Option(
        Path(__file__).parent / "debates.jsonl",
        "--in",
        help="Input JSONL produced by extract_debates.py",
    ),
    out: Path = typer.Option(
        Path(__file__).parent / "results.jsonl",
        "--out",
        help="Output JSONL with one classification per pair.",
    ),
    model: str = typer.Option(
        "claude-haiku-4-5",
        "--model",
        help="Anthropic model. Haiku is fine for this rubric.",
    ),
    sleep_seconds: float = typer.Option(
        0.5, "--sleep", help="Pause between calls (rate-limit cushion)."
    ),
    limit: int = typer.Option(
        0, "--limit", help="Optional cap (0 = no cap; useful for smoke tests)."
    ),
):
    """Classify every pair in `in_path` and append to `out`."""
    if not in_path.exists():
        console.print(f"[red]Input not found: {in_path}[/red]")
        raise typer.Exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]ANTHROPIC_API_KEY not set in env or .env[/red]")
        raise typer.Exit(1)

    rows: list[dict] = []
    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    done = _load_done_keys(out)
    pending = [r for r in rows if (r["ticker"], r["trade_date"]) not in done]

    if limit > 0:
        pending = pending[:limit]

    console.print(
        f"[cyan]{len(rows)} pairs total[/cyan]; "
        f"{len(done)} already classified, {len(pending)} pending"
    )
    if not pending:
        console.print("[yellow]Nothing to do.[/yellow]")
        raise typer.Exit(0)

    client = Anthropic()

    with open(out, "a", encoding="utf-8") as fout:
        for i, row in enumerate(pending, 1):
            ticker = row["ticker"]
            trade_date = row["trade_date"]
            console.print(f"\n[cyan]Run {i}/{len(pending)}[/cyan]  {ticker}  {trade_date}")
            t0 = time.perf_counter()
            try:
                cls = _classify_one(
                    client,
                    model=model,
                    ticker=ticker,
                    trade_date=trade_date,
                    bull=row["bull_history"],
                    bear=row["bear_history"],
                )
                elapsed = time.perf_counter() - t0
                out_row = {
                    "ticker": ticker,
                    "trade_date": trade_date,
                    "label": cls.label,
                    "contradiction_score": cls.contradiction_score,
                    "shared_claims": cls.shared_claims,
                    "bull_only_topics": cls.bull_only_topics,
                    "bear_only_topics": cls.bear_only_topics,
                    "rationale": cls.rationale,
                    "model": model,
                    "elapsed_seconds": round(elapsed, 2),
                    "error": "",
                }
                console.print(
                    f"  → [green]{cls.label}[/green] (score={cls.contradiction_score:.2f}, {elapsed:.1f}s)"
                )
            except Exception as e:
                out_row = {
                    "ticker": ticker,
                    "trade_date": trade_date,
                    "label": None,
                    "contradiction_score": None,
                    "shared_claims": [],
                    "bull_only_topics": [],
                    "bear_only_topics": [],
                    "rationale": "",
                    "model": model,
                    "elapsed_seconds": round(time.perf_counter() - t0, 2),
                    "error": f"{type(e).__name__}: {e}",
                }
                console.print(f"  → [red]error:[/red] {out_row['error']}")
            fout.write(json.dumps(out_row, ensure_ascii=False) + "\n")
            fout.flush()

            if i < len(pending):
                time.sleep(sleep_seconds)

    console.print(f"\n[cyan]Done.[/cyan] Output: {out}")


if __name__ == "__main__":
    app()
