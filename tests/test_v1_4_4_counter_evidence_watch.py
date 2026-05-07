"""Unit tests for the v1.4.4 counter-evidence watch.

Tests the `check_log` helper that classifies a single state log dict as
counter-evidence (or not) per the v1.4.4 ratification refuting criteria
(per `claudedocs/constitution-v1.4.4-draft-2026-05-07.md`).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from v1_4_4_counter_evidence_watch import check_log  # noqa: E402

pytestmark = pytest.mark.unit


def _write(tmp_path: Path, state: dict) -> Path:
    """Write a state dict as JSON to a temp file and return the path."""
    p = tmp_path / "full_states_log_2026-04-17.json"
    p.write_text(json.dumps(state), encoding="utf-8")
    return p


# ---- Negative cases (NOT counter-evidence) ---------------------------------


def test_pm_hold_is_not_counter_evidence(tmp_path):
    """PM=Hold can never be counter-evidence regardless of scores."""
    state = {
        "final_trade_decision": "**Rating**: Hold\n",
        "forward_catalyst": {"bull_case_priced_in": 0.99, "bear_case_priced_in": 0.99},
        "contrarian_gate": {"percentile": 100.0},
    }
    assert check_log(_write(tmp_path, state)) is None


def test_pm_underweight_is_not_counter_evidence(tmp_path):
    """PM=Underweight can never be counter-evidence regardless of scores."""
    state = {
        "final_trade_decision": "**Rating**: Underweight\n",
        "forward_catalyst": {"bull_case_priced_in": 0.99, "bear_case_priced_in": 0.99},
        "contrarian_gate": {"percentile": 100.0},
    }
    assert check_log(_write(tmp_path, state)) is None


def test_pm_buy_with_low_scores_is_not_counter_evidence(tmp_path):
    """PM=Buy with all scores below thresholds is fine."""
    state = {
        "final_trade_decision": "**Rating**: Buy\n",
        "forward_catalyst": {"bull_case_priced_in": 0.5, "bear_case_priced_in": 0.4},
        "contrarian_gate": {"percentile": 50.0},
    }
    assert check_log(_write(tmp_path, state)) is None


def test_no_pm_rating_is_not_counter_evidence(tmp_path):
    """Missing PM rating returns None (not classified)."""
    state = {
        "final_trade_decision": "no rating in this prose",
        "forward_catalyst": {"bull_case_priced_in": 0.95},
    }
    assert check_log(_write(tmp_path, state)) is None


def test_missing_forward_catalyst_is_not_counter_evidence(tmp_path):
    """No forward_catalyst block AND no contrarian gate → no scores → not counter."""
    state = {"final_trade_decision": "**Rating**: Buy\n"}
    assert check_log(_write(tmp_path, state)) is None


# ---- Positive cases (IS counter-evidence) ----------------------------------


def test_pm_buy_with_high_bull_score_is_counter_evidence(tmp_path):
    """PM=Buy + bull_score=0.85 should fire (≥0.80 threshold)."""
    state = {
        "final_trade_decision": "**Rating**: Buy\n",
        "forward_catalyst": {"bull_case_priced_in": 0.85, "bear_case_priced_in": 0.4},
        "contrarian_gate": {"percentile": 50.0},
    }
    result = check_log(_write(tmp_path, state))
    assert result is not None
    assert result["pm_rating"] == "Buy"
    assert any("bull_score=0.85" in r for r in result["refutations"])


def test_pm_overweight_with_high_bear_score_is_counter_evidence(tmp_path):
    """PM=Overweight + bear_score=0.65 should fire (≥0.60 threshold)."""
    state = {
        "final_trade_decision": "**Rating**: Overweight\n",
        "forward_catalyst": {"bull_case_priced_in": 0.4, "bear_case_priced_in": 0.65},
        "contrarian_gate": {"percentile": 50.0},
    }
    result = check_log(_write(tmp_path, state))
    assert result is not None
    assert result["pm_rating"] == "Overweight"
    assert any("bear_score=0.65" in r for r in result["refutations"])


def test_pm_buy_with_high_percentile_is_counter_evidence(tmp_path):
    """PM=Buy + spec_003_percentile=98 should fire (≥95.0 threshold)."""
    state = {
        "final_trade_decision": "**Rating**: Buy\n",
        "forward_catalyst": {"bull_case_priced_in": 0.5, "bear_case_priced_in": 0.4},
        "contrarian_gate": {"percentile": 98.0},
    }
    result = check_log(_write(tmp_path, state))
    assert result is not None
    assert any("percentile=98.0" in r for r in result["refutations"])


def test_multiple_refutations_recorded(tmp_path):
    """All three refutations should be listed when all three thresholds cross."""
    state = {
        "final_trade_decision": "**Rating**: Buy\n",
        "forward_catalyst": {"bull_case_priced_in": 0.85, "bear_case_priced_in": 0.65},
        "contrarian_gate": {"percentile": 98.0},
    }
    result = check_log(_write(tmp_path, state))
    assert result is not None
    assert len(result["refutations"]) == 3


# ---- Boundary cases ---------------------------------------------------------


def test_bull_score_at_exact_threshold_fires(tmp_path):
    """Threshold check is ≥, so exactly 0.80 fires."""
    state = {
        "final_trade_decision": "**Rating**: Buy\n",
        "forward_catalyst": {"bull_case_priced_in": 0.80, "bear_case_priced_in": 0.4},
        "contrarian_gate": {"percentile": 50.0},
    }
    assert check_log(_write(tmp_path, state)) is not None


def test_bull_score_just_below_threshold_does_not_fire(tmp_path):
    """0.79 should NOT fire (strict less-than)."""
    state = {
        "final_trade_decision": "**Rating**: Buy\n",
        "forward_catalyst": {"bull_case_priced_in": 0.79, "bear_case_priced_in": 0.4},
        "contrarian_gate": {"percentile": 50.0},
    }
    assert check_log(_write(tmp_path, state)) is None


# ---- Error path ------------------------------------------------------------


def test_load_error_returned_with_type_tag(tmp_path):
    """Bad JSON returns dict with counter_evidence_type=load_error."""
    p = tmp_path / "full_states_log_2026-04-17.json"
    p.write_text("not valid json {", encoding="utf-8")
    result = check_log(p)
    assert result is not None
    assert result["counter_evidence_type"] == "load_error"
    assert "error" in result
