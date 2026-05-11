"""Engine CLI --state-dir override (PR #266 isolation fix).

Verifies that `python -m tradingagents.engine run --ticker NVDA --dry-run
--state-dir <tmp>` writes progress.json + events.jsonl to <tmp>/current/.

Regression test for the dashboard_smoke.sh pollution bug: the old smoke
wrote dry-run "completed" data to the production state dir
(~/.tradingagents/engine/current/), leaving phantom "NVDA Hold" entries
on the live dashboard with no corresponding state log.

The smoke script's runtime isolation guard ("isolation: prod state…")
covers the broader leakage property — this test pins the CLI contract.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from tradingagents.engine import lock as lock_module
from tradingagents.engine.cli import app


@pytest.fixture(autouse=True)
def isolated_lock(tmp_path, monkeypatch):
    """Redirect the engine lock to tmp so CLI invocations don't fight a real run."""
    eng_dir = tmp_path / "_lock_only"
    eng_dir.mkdir()
    monkeypatch.setattr(lock_module, "ENGINE_DIR", eng_dir)
    monkeypatch.setattr(lock_module, "LOCK_FILE", eng_dir / "lock")


def test_state_dir_override_writes_to_custom_path(tmp_path):
    """--state-dir <X> writes progress.json + events.jsonl to <X>/current/."""
    state_dir = tmp_path / "smoke_state"

    result = CliRunner().invoke(
        app,
        ["run", "--ticker", "NVDA", "--dry-run", "--state-dir", str(state_dir)],
    )

    assert result.exit_code == 0, result.stdout
    progress = state_dir / "current" / "progress.json"
    events = state_dir / "current" / "events.jsonl"
    assert progress.exists(), f"progress.json missing at {progress}"
    assert events.exists(), f"events.jsonl missing at {events}"
    assert "NVDA" in progress.read_text(encoding="utf-8")
    assert '"dry_run":true' in events.read_text(encoding="utf-8").replace(" ", "")


def test_state_dir_creates_current_subdir(tmp_path):
    """--state-dir parent doesn't need to pre-exist; runner creates current/."""
    state_dir = tmp_path / "fresh" / "nested" / "smoke_state"

    result = CliRunner().invoke(
        app,
        ["run", "--ticker", "NVDA", "--dry-run", "--state-dir", str(state_dir)],
    )

    assert result.exit_code == 0, result.stdout
    assert (state_dir / "current" / "progress.json").exists()
