"""Create a new experiment directory with templated scaffolding.

See specs/001-experiments-scaffolding/contracts/new_experiment_cli.md.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import typer
from rich.console import Console

from tradingagents.experiments.ids import next_experiment_id, validate_slug
from tradingagents.experiments.templates import (
    render_hypothesis,
    render_params_json,
    render_run_ps1,
    render_run_sh,
)

console = Console()
app = typer.Typer(add_completion=False)


def _create_experiment(
    short_name: str,
    *,
    experiments_dir: Path,
    source_idea: str | None,
    cost: float | None,
    on_date: date | None,
) -> Path:
    """Create the experiment directory and populate templates.

    Returns the created directory path. Raises ValueError on invalid input
    or FileExistsError if the directory already exists.
    """
    if not validate_slug(short_name):
        raise ValueError(
            f"Invalid short-name {short_name!r}: must be 2-40 chars, "
            "kebab-case (lowercase letters, digits, internal hyphens), "
            "no leading/trailing hyphens."
        )

    id_str = next_experiment_id(experiments_dir, short_name, date=on_date)
    exp_dir = experiments_dir / id_str

    if exp_dir.exists():
        # Belt-and-suspenders — next_experiment_id should have skipped this.
        raise FileExistsError(f"Experiment directory already exists: {exp_dir}")

    exp_dir.mkdir(parents=True, exist_ok=False)

    (exp_dir / "HYPOTHESIS.md").write_text(
        render_hypothesis(id_str, source_idea=source_idea, cost=cost),
        encoding="utf-8",
    )
    (exp_dir / "PARAMS.json").write_text(render_params_json(), encoding="utf-8")
    (exp_dir / "run.sh").write_text(render_run_sh(id_str), encoding="utf-8")
    (exp_dir / "run.ps1").write_text(render_run_ps1(id_str), encoding="utf-8")

    return exp_dir


@app.command()
def main(
    short_name: str = typer.Argument(
        ...,
        help="2-40 char kebab-case slug for the experiment (e.g. 'mr1-contradiction').",
    ),
    source_idea: str | None = typer.Option(
        None,
        "--source-idea",
        help="Reference to entry in docs/EXPERIMENT.md (e.g. 'MR-1', 'WC-12').",
    ),
    cost: float | None = typer.Option(
        None,
        "--cost",
        help="Pre-fill the cost-estimate line in HYPOTHESIS.md (USD). "
        "Leave empty for zero-cost experiments.",
    ),
    experiments_dir: Path = typer.Option(
        Path("experiments"),
        "--experiments-dir",
        help="Where to create the new experiment subdir.",
    ),
    on_date: str | None = typer.Option(
        None,
        "--date",
        help="Override the date prefix (YYYY-MM-DD; advanced/testing only).",
    ),
):
    """Scaffold a new experiment directory."""
    parsed_date: date | None = None
    if on_date is not None:
        try:
            parsed_date = datetime.strptime(on_date, "%Y-%m-%d").date()
        except ValueError as e:
            console.print(f"[red]Invalid --date {on_date!r}: {e}[/red]")
            raise typer.Exit(1) from None

    try:
        exp_dir = _create_experiment(
            short_name,
            experiments_dir=experiments_dir,
            source_idea=source_idea,
            cost=cost,
            on_date=parsed_date,
        )
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1) from None
    except FileExistsError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1) from None

    rel = exp_dir.relative_to(Path.cwd()) if exp_dir.is_absolute() else exp_dir
    console.print(f"[green]Created {rel}/[/green]")
    console.print("Next steps:")
    console.print(f"  1. Edit {rel}/HYPOTHESIS.md")
    console.print(f"  2. Edit {rel}/run.sh (or run.ps1) with the actual command")
    console.print(f"  3. Run: bash {rel}/run.sh")
    console.print(f"  4. After it completes, write {rel}/ANALYSIS.md")


if __name__ == "__main__":
    app()
