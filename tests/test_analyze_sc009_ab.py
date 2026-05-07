"""Unit tests for the SC-009 analyzer's gate-1 evaluator.

Tests the `evaluate_gate_1` helper that resolves SC-009 gate-1 status
using either the standard (boost-ON kept α minus boost-OFF kept α)
or alternative (suppressed-commits' α direction) evaluator.

Per spec 008 v0.8.0 SC-009 + the alt-gate-1 enhancement
(`scripts/analyze_sc009_ab.py`, 2026-05-07).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# scripts/ isn't a package; add it to sys.path so we can import the analyzer module
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from analyze_sc009_ab import evaluate_gate_1  # noqa: E402

pytestmark = pytest.mark.unit


# ---- Standard gate-1 path (kept-α delta) -----------------------------------


def test_standard_gate_1_pass_at_target_midpoint():
    """+3.35pp is the retrofit's exact target; should PASS."""
    result = evaluate_gate_1(net_dalpha_improvement=3.35, alt_gate_1_pass=None)
    assert result["effective"] is True
    assert result["method"] == "standard"
    assert result["status"] == "PASS"


def test_standard_gate_1_pass_at_lower_bound():
    """+2.35pp is the lower bound; should PASS (inclusive)."""
    result = evaluate_gate_1(net_dalpha_improvement=2.35, alt_gate_1_pass=None)
    assert result["effective"] is True
    assert result["status"] == "PASS"


def test_standard_gate_1_pass_at_upper_bound():
    """+4.35pp is the upper bound; should PASS (inclusive)."""
    result = evaluate_gate_1(net_dalpha_improvement=4.35, alt_gate_1_pass=None)
    assert result["effective"] is True
    assert result["status"] == "PASS"


def test_standard_gate_1_fail_below_lower_bound():
    """+2.34pp is just below lower bound; should FAIL."""
    result = evaluate_gate_1(net_dalpha_improvement=2.34, alt_gate_1_pass=None)
    assert result["effective"] is False
    assert result["method"] == "standard"
    assert result["status"] == "FAIL"


def test_standard_gate_1_fail_above_upper_bound():
    """+4.36pp is just above upper bound; should FAIL (over-improvement is suspicious)."""
    result = evaluate_gate_1(net_dalpha_improvement=4.36, alt_gate_1_pass=None)
    assert result["effective"] is False
    assert result["status"] == "FAIL"


def test_standard_gate_1_fail_negative_improvement():
    """Negative net Δα means boost HURT; should FAIL."""
    result = evaluate_gate_1(net_dalpha_improvement=-1.0, alt_gate_1_pass=None)
    assert result["effective"] is False
    assert result["status"] == "FAIL"


def test_standard_gate_1_overrides_alt_when_both_provided():
    """Standard wins when computable; alt is ignored even if PASS."""
    # Standard FAILs at -1pp; alt would PASS — standard takes precedence
    result = evaluate_gate_1(net_dalpha_improvement=-1.0, alt_gate_1_pass=True)
    assert result["effective"] is False
    assert result["method"] == "standard"


# ---- Alternative gate-1 path (suppressed-α direction) ----------------------


def test_alt_gate_1_pass_when_standard_undefined():
    """Standard undefined (100% fire rate); alt PASS → effective PASS."""
    result = evaluate_gate_1(net_dalpha_improvement=None, alt_gate_1_pass=True)
    assert result["effective"] is True
    assert result["method"] == "alternative (100%-fire-rate fallback)"
    assert result["status"] == "PASS"


def test_alt_gate_1_fail_when_standard_undefined():
    """Standard undefined; alt FAIL → effective FAIL."""
    result = evaluate_gate_1(net_dalpha_improvement=None, alt_gate_1_pass=False)
    assert result["effective"] is False
    assert result["method"] == "alternative (100%-fire-rate fallback)"
    assert result["status"] == "FAIL"


# ---- Inconclusive path ------------------------------------------------------


def test_inconclusive_when_neither_evaluator_can_decide():
    """Standard undefined + alt undefined (no suppressed α at all) → INCONCLUSIVE."""
    result = evaluate_gate_1(net_dalpha_improvement=None, alt_gate_1_pass=None)
    assert result["effective"] is False
    assert result["method"] == "neither (no fires + no suppressed α)"
    assert result["status"] == "INCONCLUSIVE"


# ---- Schema invariants ------------------------------------------------------


@pytest.mark.parametrize(
    "net_dalpha,alt_pass",
    [
        (3.35, None),
        (-1.0, None),
        (None, True),
        (None, False),
        (None, None),
    ],
)
def test_returned_dict_has_all_three_keys(net_dalpha, alt_pass):
    """Every code path returns dict with effective/method/status keys."""
    result = evaluate_gate_1(net_dalpha_improvement=net_dalpha, alt_gate_1_pass=alt_pass)
    assert set(result.keys()) == {"effective", "method", "status"}
    assert isinstance(result["effective"], bool)
    assert isinstance(result["method"], str)
    assert isinstance(result["status"], str)
    assert result["status"] in {"PASS", "FAIL", "INCONCLUSIVE"}
