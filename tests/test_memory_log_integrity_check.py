"""Unit tests for memory log integrity check (PR #54 followup tooling).

Tests the parse_entries + flag_inconsistencies helpers.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from memory_log_integrity_check import (  # noqa: E402
    HEADER_RE,
    flag_inconsistencies,
    parse_entries,
)

pytestmark = pytest.mark.unit


# ---- HEADER_RE regex tests --------------------------------------------------


def test_header_regex_matches_canonical_underweight_entry():
    line = "[2026-04-17 | AMD | Underweight | +24.9% | +24.4% | 5d]"
    m = HEADER_RE.match(line)
    assert m is not None
    assert m.group(1) == "2026-04-17"
    assert m.group(2) == "AMD"
    assert m.group(3) == "Underweight"
    assert m.group(4) == "+24.9"
    assert m.group(5) == "+24.4"
    assert m.group(6) == "5"


def test_header_regex_matches_negative_returns():
    line = "[2026-04-24 | INTC | Overweight | -3.20% | -2.50% | 21d]"
    m = HEADER_RE.match(line)
    assert m is not None
    assert m.group(4) == "-3.20"


def test_header_regex_does_not_match_pending_entry():
    line = "[2026-04-24 | NVDA | Hold | pending]"
    assert HEADER_RE.match(line) is None


def test_header_regex_handles_dotted_tickers():
    line = "[2026-04-17 | BRK.B | Hold | +1.00% | +0.50% | 5d]"
    m = HEADER_RE.match(line)
    assert m is not None
    assert m.group(2) == "BRK.B"


# ---- parse_entries tests ----------------------------------------------------


def test_parse_entries_returns_one_dict_per_entry():
    text = """[2026-04-17 | AMD | Underweight | +24.9% | +24.4% | 5d]

DECISION:
some prose

REFLECTION:
the call was correct because trim discipline.

<!-- ENTRY_END -->

[2026-04-24 | NVDA | Hold | pending]

DECISION:
not yet resolved
"""
    entries = parse_entries(text)
    assert len(entries) == 1  # only AMD; NVDA is pending
    assert entries[0]["ticker"] == "AMD"
    assert entries[0]["raw_return_pct"] == 24.9
    assert "trim discipline" in entries[0]["reflection_excerpt"]


def test_parse_entries_handles_empty_reflection_block():
    text = """[2026-04-17 | AAPL | Hold | +2.50% | +1.50% | 5d]

DECISION:
prose

<!-- ENTRY_END -->
"""
    entries = parse_entries(text)
    assert len(entries) == 1
    assert entries[0]["has_reflection"] is False


# ---- flag_inconsistencies tests ---------------------------------------------


def test_underweight_with_positive_return_is_flagged():
    entries = [
        {
            "line_number": 100,
            "date": "2026-04-17",
            "ticker": "AMD",
            "rating": "Underweight",
            "raw_return_pct": 24.9,
            "alpha_pct": 24.4,
            "holding_days": 5,
            "reflection_excerpt": "trim discipline validated the underweight call",
            "has_reflection": True,
        }
    ]
    suspects = flag_inconsistencies(entries)
    assert len(suspects) == 1
    assert (
        "Bearish rating (Underweight) but raw_return = +24.90% (UP)"
        in suspects[0]["suspect_reason"]
    )
    assert "validated the underweight" in suspects[0]["matched_validation_phrases"]
    assert "trim discipline" in suspects[0]["matched_validation_phrases"]


def test_overweight_with_negative_return_is_flagged():
    entries = [
        {
            "line_number": 200,
            "date": "2026-04-17",
            "ticker": "FOO",
            "rating": "Overweight",
            "raw_return_pct": -8.0,
            "alpha_pct": -7.5,
            "holding_days": 21,
            "reflection_excerpt": "the directional call was correct in retrospect",
            "has_reflection": True,
        }
    ]
    suspects = flag_inconsistencies(entries)
    assert len(suspects) == 1
    assert "Bullish rating (Overweight)" in suspects[0]["suspect_reason"]
    assert "directional call was correct" in suspects[0]["matched_validation_phrases"]


def test_hold_rating_is_never_flagged():
    """Hold has no directional expectation; never flagged."""
    entries = [
        {
            "line_number": 1,
            "date": "2026-04-17",
            "ticker": "X",
            "rating": "Hold",
            "raw_return_pct": 50.0,  # would normally be suspect
            "alpha_pct": 45.0,
            "holding_days": 5,
            "reflection_excerpt": "directional call was correct",
            "has_reflection": True,
        }
    ]
    assert flag_inconsistencies(entries) == []


def test_underweight_with_negative_return_is_not_flagged():
    """Underweight + DOWN is the EXPECTED direction; not flagged."""
    entries = [
        {
            "line_number": 1,
            "date": "2026-04-17",
            "ticker": "X",
            "rating": "Underweight",
            "raw_return_pct": -5.0,
            "alpha_pct": -4.5,
            "holding_days": 5,
            "reflection_excerpt": "trim discipline worked",
            "has_reflection": True,
        }
    ]
    assert flag_inconsistencies(entries) == []


def test_buy_with_positive_return_is_not_flagged():
    """Buy + UP is the EXPECTED direction; not flagged."""
    entries = [
        {
            "line_number": 1,
            "date": "2026-04-17",
            "ticker": "X",
            "rating": "Buy",
            "raw_return_pct": 10.0,
            "alpha_pct": 9.0,
            "holding_days": 5,
            "reflection_excerpt": "thesis confirmed",
            "has_reflection": True,
        }
    ]
    assert flag_inconsistencies(entries) == []


def test_suspect_with_no_validation_phrases_is_still_flagged():
    """Sign-mismatch alone is enough to flag, even without prose phrases."""
    entries = [
        {
            "line_number": 1,
            "date": "2026-04-17",
            "ticker": "X",
            "rating": "Underweight",
            "raw_return_pct": 5.0,
            "alpha_pct": 4.5,
            "holding_days": 5,
            "reflection_excerpt": "the underweight call did not pan out as expected",
            "has_reflection": True,
        }
    ]
    suspects = flag_inconsistencies(entries)
    assert len(suspects) == 1
    assert suspects[0]["matched_validation_phrases"] == []
