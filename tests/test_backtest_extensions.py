"""Tests for the experiments-scaffolding extensions to scripts/backtest.py.

Per specs/001-experiments-scaffolding/contracts/backtest_extensions.md.

These tests focus on the new behaviors only (experiment_id column,
--config-override parsing, PARAMS.json auto-sync, precedence). The full
end-to-end behavior of backtest.py is exercised manually; mocking
TradingAgentsGraph here would duplicate too much without adding signal.
"""

from __future__ import annotations

import csv
import json
import logging
import sys
from pathlib import Path

import pandas as pd
import pytest

from tradingagents.experiments.overrides import apply_overrides, parse_override

# Import the script's helpers directly for unit testing.
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from backtest import (  # noqa: E402
    _NAMED_FLAG_KEYS,
    CSV_FIELDS,
    _append_row,
    _autosync_params_json,
    _ensure_header,
    _warn_override_conflicts,
)

pytestmark = pytest.mark.unit


# ---- CSV schema: experiment_id is the LAST column (R-004) -------------


def test_csv_fields_has_experiment_id_at_end():
    assert CSV_FIELDS[-1] == "experiment_id"


def test_csv_fields_unchanged_for_existing_columns():
    # Order of original columns preserved (so old readers still work).
    expected_prefix = [
        "ticker",
        "analysis_date",
        "rating",
        "error",
        "run_seconds",
        "deep_model",
        "quick_model",
        "debate_rounds",
        "analysts",
    ]
    assert CSV_FIELDS[:-1] == expected_prefix


# ---- Row writing: experiment_id stamped when set -----------------------


def test_writes_experiment_id_when_provided(tmp_path):
    out = tmp_path / "results.csv"
    _ensure_header(out)
    _append_row(
        out,
        {
            "ticker": "AAPL",
            "analysis_date": "2026-04-03",
            "rating": "Hold",
            "error": "",
            "run_seconds": 1.0,
            "deep_model": "claude-sonnet-4-6",
            "quick_model": "claude-haiku-4-5",
            "debate_rounds": 1,
            "analysts": "market,news",
            "experiment_id": "2026-05-02-001-foo",
        },
    )
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert rows[0]["experiment_id"] == "2026-05-02-001-foo"


def test_writes_empty_experiment_id_when_not_provided(tmp_path):
    out = tmp_path / "results.csv"
    _ensure_header(out)
    _append_row(
        out,
        {
            "ticker": "AAPL",
            "analysis_date": "2026-04-03",
            "rating": "Hold",
            "error": "",
            "run_seconds": 1.0,
            "deep_model": "claude-sonnet-4-6",
            "quick_model": "claude-haiku-4-5",
            "debate_rounds": 1,
            "analysts": "market,news",
            "experiment_id": "",
        },
    )
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert rows[0]["experiment_id"] == ""


# ---- --config-override coercion (delegated to overrides module) -------


def test_override_int_coercion_via_parse():
    assert parse_override("max_debate_rounds=2") == ("max_debate_rounds", 2)


def test_override_bool_coercion_via_parse():
    assert parse_override("pm_sees_debate=false") == ("pm_sees_debate", False)


def test_override_quoted_string_via_parse():
    assert parse_override('label="42"') == ("label", "42")


def test_apply_overrides_unknown_key_warns(caplog):
    config = {"known": 1}
    with caplog.at_level(logging.WARNING, logger="tradingagents.experiments.overrides"):
        out = apply_overrides(config, ["unknown=42"])
    assert out["unknown"] == 42
    assert any("unknown config key" in r.message for r in caplog.records)


# ---- Precedence warning (FR-010) --------------------------------------


def test_warn_override_conflicts_emits_for_named_flag_collision(capsys):
    # max_debate_rounds is set by --debate-rounds (named flag).
    _warn_override_conflicts(
        ["max_debate_rounds=2"],
        named_flag_set_keys={"max_debate_rounds", "max_risk_discuss_rounds"},
    )
    captured = capsys.readouterr()
    assert "overrides --debate-rounds" in captured.out


def test_warn_override_conflicts_silent_when_no_collision(capsys):
    _warn_override_conflicts(
        ["pm_sees_debate=false"],
        named_flag_set_keys={"max_debate_rounds"},
    )
    captured = capsys.readouterr()
    assert "warning" not in captured.out.lower()


def test_named_flag_keys_map_includes_expected_keys():
    # Sanity: all keys our flags set are mapped for the warning system.
    assert "max_debate_rounds" in _NAMED_FLAG_KEYS
    assert "max_risk_discuss_rounds" in _NAMED_FLAG_KEYS
    assert "llm_provider" in _NAMED_FLAG_KEYS
    assert _NAMED_FLAG_KEYS["max_debate_rounds"] == "--debate-rounds"


# ---- PARAMS.json auto-sync (R-007) ------------------------------------


def test_autosync_creates_params_when_missing(tmp_path):
    exp_dir = tmp_path / "2026-05-02-001-foo"
    exp_dir.mkdir()
    _autosync_params_json(
        "2026-05-02-001-foo",
        ["pm_sees_debate=false", "max_debate_rounds=2"],
        explicit_flags={"--debate-rounds": 1},
        experiments_root=tmp_path,
    )
    params = json.loads((exp_dir / "PARAMS.json").read_text(encoding="utf-8"))
    assert params["config_overrides"] == {
        "pm_sees_debate": False,
        "max_debate_rounds": 2,
    }
    assert params["explicit_flags"] == {"--debate-rounds": 1}


def test_autosync_populates_empty_existing_params(tmp_path):
    exp_dir = tmp_path / "2026-05-02-001-foo"
    exp_dir.mkdir()
    # Pre-existing empty PARAMS.json (as new_experiment.py would create).
    (exp_dir / "PARAMS.json").write_text(
        json.dumps(
            {
                "config_overrides": {},
                "explicit_flags": {},
                "baseline": "manual baseline note",
                "notes": "manual notes",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _autosync_params_json(
        "2026-05-02-001-foo",
        ["pm_sees_debate=false"],
        explicit_flags={},
        experiments_root=tmp_path,
    )
    params = json.loads((exp_dir / "PARAMS.json").read_text(encoding="utf-8"))
    assert params["config_overrides"] == {"pm_sees_debate": False}
    # Manual annotations preserved.
    assert params["baseline"] == "manual baseline note"
    assert params["notes"] == "manual notes"


def test_autosync_refuses_overwrite_of_nonempty_overrides(tmp_path, capsys):
    exp_dir = tmp_path / "2026-05-02-001-foo"
    exp_dir.mkdir()
    (exp_dir / "PARAMS.json").write_text(
        json.dumps(
            {
                "config_overrides": {"pre_existing_key": "manual_value"},
                "explicit_flags": {},
                "baseline": "",
                "notes": "",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _autosync_params_json(
        "2026-05-02-001-foo",
        ["new_override=42"],
        explicit_flags={},
        experiments_root=tmp_path,
    )
    params = json.loads((exp_dir / "PARAMS.json").read_text(encoding="utf-8"))
    # Manual config_overrides preserved verbatim.
    assert params["config_overrides"] == {"pre_existing_key": "manual_value"}
    captured = capsys.readouterr()
    assert "skipping auto-sync" in captured.out


def test_autosync_skips_when_experiment_dir_missing(tmp_path, capsys):
    _autosync_params_json(
        "2026-05-02-001-nonexistent",
        ["pm_sees_debate=false"],
        explicit_flags={},
        experiments_root=tmp_path,
    )
    captured = capsys.readouterr()
    assert "doesn't exist" in captured.out


def test_autosync_no_op_when_no_overrides(tmp_path):
    exp_dir = tmp_path / "2026-05-02-001-foo"
    exp_dir.mkdir()
    (exp_dir / "PARAMS.json").write_text("{}", encoding="utf-8")
    _autosync_params_json(
        "2026-05-02-001-foo",
        [],
        explicit_flags={},
        experiments_root=tmp_path,
    )
    # File unchanged.
    assert (exp_dir / "PARAMS.json").read_text(encoding="utf-8") == "{}"


def test_autosync_records_synthesized_news_vendor_override(tmp_path):
    """Per R-007 + Win #3: --news-vendor non-default should appear in PARAMS
    config_overrides as data_vendors.news_data=alpha_vantage even when the
    user didn't pass --config-override. This test exercises the synthesizer
    output that scripts/backtest.py main() now feeds into _autosync."""
    exp_dir = tmp_path / "2026-05-02-001-foo"
    exp_dir.mkdir()
    (exp_dir / "PARAMS.json").write_text("{}", encoding="utf-8")
    # main() builds the synthesized list before calling _autosync; here we
    # pass that synthesized form directly.
    _autosync_params_json(
        "2026-05-02-001-foo",
        ["data_vendors.news_data=alpha_vantage"],
        explicit_flags={"--news-vendor": "alpha_vantage"},
        experiments_root=tmp_path,
    )
    saved = json.loads((exp_dir / "PARAMS.json").read_text(encoding="utf-8"))
    assert saved["config_overrides"] == {"data_vendors.news_data": "alpha_vantage"}
    assert saved["explicit_flags"]["--news-vendor"] == "alpha_vantage"


def test_autosync_records_multiple_synthesized_overrides(tmp_path):
    """A model swap + news vendor change synthesizes two overrides."""
    exp_dir = tmp_path / "2026-05-03-005-foo"
    exp_dir.mkdir()
    (exp_dir / "PARAMS.json").write_text("{}", encoding="utf-8")
    _autosync_params_json(
        "2026-05-03-005-foo",
        ["deep_think_llm=claude-opus-4-7", "data_vendors.news_data=exa"],
        explicit_flags={
            "--deep-model": "claude-opus-4-7",
            "--news-vendor": "exa",
        },
        experiments_root=tmp_path,
    )
    saved = json.loads((exp_dir / "PARAMS.json").read_text(encoding="utf-8"))
    assert saved["config_overrides"] == {
        "deep_think_llm": "claude-opus-4-7",
        "data_vendors.news_data": "exa",
    }


# ---- Backward compat: pre-cleanup CSVs still readable -----------------


def test_old_csv_without_experiment_id_column_readable(tmp_path):
    """Pandas read_csv on an old-schema CSV should not raise; the column simply isn't there."""
    old = tmp_path / "old_pilot_results.csv"
    old.write_text(
        "ticker,analysis_date,rating,error,run_seconds,deep_model,quick_model,debate_rounds,analysts\n"
        'AAPL,2026-04-03,Hold,,180.0,claude-sonnet-4-6,claude-haiku-4-5,1,"market,news,fundamentals"\n',
        encoding="utf-8",
    )
    df = pd.read_csv(old)
    assert "experiment_id" not in df.columns
    assert df["rating"].iloc[0] == "Hold"
