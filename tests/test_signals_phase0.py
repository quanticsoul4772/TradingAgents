"""Tests for the spec 002 Phase 0 signals module (registry + cache + context).

Covers:
- paths.py: env override + default behavior
- registry.py: SignalDefinition serialization, register/get/list/transition
- cache.py: init/record/query/count, idempotency, structured raw_json
- context.py: contextmanager set/reset behavior
- bootstrap.py: 17-signal initial registration, idempotency
- route_to_vendor cache hook: writes when context is set, no-op when not
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from tradingagents.signals import (
    VALID_STATES,
    SignalDefinition,
    StateTransition,
    bootstrap_initial_signals,
    count_rows,
    get_initial_signal_ids,
    get_propagate_context,
    get_signal,
    list_signals,
    load_registry,
    propagate_context,
    query_value,
    record_value,
    register_signal,
    transition_state,
)
from tradingagents.signals.paths import (
    get_cache_path,
    get_registry_path,
    get_signals_dir,
)

pytestmark = pytest.mark.unit


# ---- paths -----------------------------------------------------------------


def test_signals_dir_respects_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("TRADINGAGENTS_SIGNALS_DIR", str(tmp_path / "custom_signals"))
    out = get_signals_dir()
    assert out == tmp_path / "custom_signals"
    assert out.exists()


def test_registry_and_cache_paths_under_signals_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("TRADINGAGENTS_SIGNALS_DIR", str(tmp_path))
    assert get_registry_path() == tmp_path / "registry.jsonl"
    assert get_cache_path() == tmp_path / "cache.db"


# ---- registry: SignalDefinition serialization ------------------------------


def test_signal_definition_round_trip():
    sig = SignalDefinition(
        signal_id="get_vix",
        name="VIX",
        fetcher="tradingagents.dataflows.macro.get_vix",
        inputs=["curr_date", "lookback_days"],
        output_type="markdown",
        horizon_days=21,
        introduced="2026-05-04T20:00:00+00:00",
        state="production",
    )
    d = sig.to_dict()
    assert d["signal_id"] == "get_vix"
    assert d["state"] == "production"
    assert d["state_history"] == []
    sig2 = SignalDefinition.from_dict(d)
    assert sig2.signal_id == sig.signal_id
    assert sig2.state == sig.state
    assert sig2.inputs == sig.inputs


def test_signal_definition_rejects_invalid_state():
    with pytest.raises(ValueError, match="Invalid state"):
        SignalDefinition(
            signal_id="x",
            name="x",
            fetcher="x",
            inputs=[],
            output_type="markdown",
            horizon_days=21,
            introduced="2026-05-04T00:00:00+00:00",
            state="not-a-state",
        )


def test_state_transition_serializes():
    t = StateTransition(
        timestamp="2026-05-04T20:00:00+00:00",
        from_state="candidate",
        to_state="production",
        reason="test",
    )
    d = t.to_dict()
    assert d["from_state"] == "candidate"
    assert d["to_state"] == "production"


# ---- registry: register / get / list ---------------------------------------


def test_register_signal_writes_initial_snapshot(tmp_path):
    reg = tmp_path / "registry.jsonl"
    sig = register_signal(
        signal_id="get_test",
        name="Test signal",
        fetcher="x.y.z",
        inputs=["a"],
        registry_path=reg,
    )
    assert sig.signal_id == "get_test"
    assert sig.state == "production"
    assert len(sig.state_history) == 1
    assert sig.state_history[0].from_state is None
    assert sig.state_history[0].to_state == "production"

    # File contains exactly one JSON line
    lines = reg.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["signal_id"] == "get_test"


def test_register_signal_idempotent_when_metadata_unchanged(tmp_path):
    reg = tmp_path / "registry.jsonl"
    register_signal("s1", "Name", "x.y", ["a"], registry_path=reg)
    register_signal("s1", "Name", "x.y", ["a"], registry_path=reg)
    # Only one line written despite two calls
    lines = reg.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_register_signal_writes_new_snapshot_when_metadata_changes(tmp_path):
    reg = tmp_path / "registry.jsonl"
    register_signal("s1", "Old name", "x.y", ["a"], registry_path=reg)
    register_signal("s1", "New name", "x.y", ["a"], registry_path=reg)
    lines = reg.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    # Latest snapshot wins on load
    sig = get_signal("s1", registry_path=reg)
    assert sig is not None
    assert sig.name == "New name"


def test_list_signals_filters_by_state(tmp_path):
    reg = tmp_path / "registry.jsonl"
    register_signal("p1", "P1", "x.y", ["a"], state="production", registry_path=reg)
    register_signal("c1", "C1", "x.y", ["a"], state="candidate", registry_path=reg)
    prod = list_signals(state="production", registry_path=reg)
    cand = list_signals(state="candidate", registry_path=reg)
    assert {s.signal_id for s in prod} == {"p1"}
    assert {s.signal_id for s in cand} == {"c1"}
    assert len(list_signals(registry_path=reg)) == 2


def test_get_signal_returns_none_for_unknown(tmp_path):
    reg = tmp_path / "registry.jsonl"
    assert get_signal("nope", registry_path=reg) is None


def test_load_registry_skips_malformed_lines(tmp_path):
    reg = tmp_path / "registry.jsonl"
    # Hand-write a mix of valid + malformed lines
    register_signal("s1", "S1", "x.y", ["a"], registry_path=reg)
    with open(reg, "a", encoding="utf-8") as f:
        f.write("this is not json\n")
        f.write("{}\n")  # valid json but missing required fields
    register_signal("s2", "S2", "x.y", ["a"], registry_path=reg)
    out = load_registry(registry_path=reg)
    assert set(out.keys()) == {"s1", "s2"}


# ---- registry: state transitions -------------------------------------------


def test_transition_state_appends_event(tmp_path):
    reg = tmp_path / "registry.jsonl"
    register_signal("s1", "S1", "x.y", ["a"], state="candidate", registry_path=reg)
    sig = transition_state("s1", "experimental", "promotion criteria met", registry_path=reg)
    assert sig.state == "experimental"
    assert len(sig.state_history) == 2
    assert sig.state_history[-1].from_state == "candidate"
    assert sig.state_history[-1].to_state == "experimental"
    assert sig.state_history[-1].reason == "promotion criteria met"


def test_transition_state_idempotent_when_already_in_target(tmp_path):
    reg = tmp_path / "registry.jsonl"
    register_signal("s1", "S1", "x.y", ["a"], state="production", registry_path=reg)
    transition_state("s1", "production", "no-op", registry_path=reg)
    sig = get_signal("s1", registry_path=reg)
    assert sig is not None
    assert len(sig.state_history) == 1  # only the initial registration


def test_transition_state_raises_on_unknown_signal(tmp_path):
    reg = tmp_path / "registry.jsonl"
    with pytest.raises(KeyError, match="unknown signal"):
        transition_state("nope", "experimental", "x", registry_path=reg)


def test_transition_state_raises_on_invalid_target(tmp_path):
    reg = tmp_path / "registry.jsonl"
    register_signal("s1", "S1", "x.y", ["a"], registry_path=reg)
    with pytest.raises(ValueError, match="Invalid target state"):
        transition_state("s1", "not-a-state", "x", registry_path=reg)


def test_valid_states_constant():
    assert "production" in VALID_STATES
    assert "candidate" in VALID_STATES
    assert "experimental" in VALID_STATES
    assert "deprecated" in VALID_STATES
    assert "archived" in VALID_STATES
    assert len(VALID_STATES) == 5


# ---- cache -----------------------------------------------------------------


def test_record_and_query_value_round_trip(tmp_path):
    cache = tmp_path / "cache.db"
    record_value("get_vix", "NVDA", "2026-01-30", "VIX = 18.5", cache_path=cache)
    out = query_value("get_vix", "NVDA", "2026-01-30", cache_path=cache)
    assert out is not None
    assert out["signal_id"] == "get_vix"
    assert out["ticker"] == "NVDA"
    assert out["date"] == "2026-01-30"
    assert out["value"] == "VIX = 18.5"
    assert out["fetcher_version"] == "v1"
    assert out["computed_at"]  # set automatically


def test_record_value_overwrites_existing(tmp_path):
    cache = tmp_path / "cache.db"
    record_value("s", "T", "D", "first", cache_path=cache)
    record_value("s", "T", "D", "second", cache_path=cache)
    out = query_value("s", "T", "D", cache_path=cache)
    assert out["value"] == "second"
    assert count_rows(cache_path=cache) == 1


def test_record_value_normalizes_ticker_case(tmp_path):
    cache = tmp_path / "cache.db"
    record_value("s", "nvda", "2026-01-30", "v", cache_path=cache)
    out = query_value("s", "NVDA", "2026-01-30", cache_path=cache)
    assert out is not None  # case-normalized lookup works


def test_query_value_returns_none_when_absent(tmp_path):
    cache = tmp_path / "cache.db"
    out = query_value("missing", "T", "D", cache_path=cache)
    assert out is None


def test_count_rows_starts_zero(tmp_path):
    cache = tmp_path / "cache.db"
    assert count_rows(cache_path=cache) == 0


def test_query_all_filters_by_signal_and_ticker(tmp_path):
    cache = tmp_path / "cache.db"
    record_value("s1", "NVDA", "2026-01-30", "v", cache_path=cache)
    record_value("s1", "AAPL", "2026-01-30", "v", cache_path=cache)
    record_value("s2", "NVDA", "2026-01-30", "v", cache_path=cache)
    assert (
        len(
            query_value.__call__
            and __import__("tradingagents.signals", fromlist=["query_all"]).query_all(
                cache_path=cache
            )
        )
        == 3
    )
    from tradingagents.signals import query_all

    assert len(query_all(signal_id="s1", cache_path=cache)) == 2
    assert len(query_all(ticker="NVDA", cache_path=cache)) == 2
    assert len(query_all(signal_id="s1", ticker="NVDA", cache_path=cache)) == 1


def test_record_value_swallows_errors_quietly(tmp_path, caplog):
    """A bad cache path should not crash the caller; just warn."""
    bad_path = tmp_path / "nonexistent_dir" / "subdir" / "cache.db"
    # init_cache will mkdir the parent, but force a failure by patching.
    with patch("tradingagents.signals.cache._connect", side_effect=RuntimeError("disk full")):
        # Should not raise — caller never sees the exception
        record_value("s", "T", "D", "v", cache_path=bad_path)


# ---- context ---------------------------------------------------------------


def test_propagate_context_sets_and_resets():
    assert get_propagate_context() is None
    with propagate_context("NVDA", "2026-01-30"):
        ctx = get_propagate_context()
        assert ctx is not None
        assert ctx["ticker"] == "NVDA"
        assert ctx["trade_date"] == "2026-01-30"
    assert get_propagate_context() is None


def test_propagate_context_resets_on_exception():
    assert get_propagate_context() is None
    with pytest.raises(RuntimeError):
        with propagate_context("NVDA", "2026-01-30"):
            raise RuntimeError("boom")
    assert get_propagate_context() is None


def test_propagate_context_nested():
    """Nested contexts should restore the outer context on exit."""
    with propagate_context("NVDA", "2026-01-30"):
        outer = get_propagate_context()
        with propagate_context("AAPL", "2026-02-06"):
            inner = get_propagate_context()
            assert inner["ticker"] == "AAPL"
        # Outer is restored
        restored = get_propagate_context()
        assert restored["ticker"] == "NVDA"
        assert restored == outer


# ---- bootstrap -------------------------------------------------------------


def test_bootstrap_registers_all_initial_signals(tmp_path):
    reg = tmp_path / "registry.jsonl"
    n = bootstrap_initial_signals(registry_path=reg)
    assert n == len(get_initial_signal_ids())
    assert n >= 17  # SC-001 baseline; spec text says "18" (counts get_indicators as one)
    out = load_registry(registry_path=reg)
    assert set(out.keys()) == set(get_initial_signal_ids())
    for sig in out.values():
        assert sig.state == "production"
        assert sig.horizon_days == 21


def test_bootstrap_is_idempotent(tmp_path):
    reg = tmp_path / "registry.jsonl"
    bootstrap_initial_signals(registry_path=reg)
    line_count_first = len(reg.read_text(encoding="utf-8").splitlines())
    bootstrap_initial_signals(registry_path=reg)
    line_count_second = len(reg.read_text(encoding="utf-8").splitlines())
    assert line_count_second == line_count_first  # no new snapshots


def test_initial_signal_ids_includes_macro_and_extended_fundamentals():
    ids = set(get_initial_signal_ids())
    # Spot-check the key new signals from commit 171ea2b SIGNALS expansion
    assert "get_vix" in ids
    assert "get_sector_etf_strength" in ids
    assert "get_options_summary" in ids
    assert "get_recommendations" in ids
    assert "get_earnings_calendar" in ids
    assert "get_short_interest" in ids
    assert "get_institutional_holders" in ids
    assert "get_corporate_actions" in ids
    assert "get_news" in ids
    assert "get_global_news" in ids
    assert "get_insider_transactions" in ids
    assert "get_fundamentals" in ids
    assert "get_balance_sheet" in ids
    assert "get_cashflow" in ids
    assert "get_income_statement" in ids
    assert "get_stock_data" in ids
    assert "get_indicators" in ids


# ---- route_to_vendor cache hook --------------------------------------------


def test_route_to_vendor_writes_to_cache_when_context_is_set(tmp_path, monkeypatch):
    """Phase 0 acceptance: dispatch through route_to_vendor inside a propagate
    context writes a row to the cache. Outside a context: no write.
    """
    monkeypatch.setenv("TRADINGAGENTS_SIGNALS_DIR", str(tmp_path))
    from tradingagents.dataflows.interface import VENDOR_METHODS, route_to_vendor

    def fake_impl(*a, **kw):
        return "FAKE_VALUE"

    config = {"data_vendors": {"news_data": "exa"}, "tool_vendors": {}}
    with (
        patch("tradingagents.dataflows.interface.get_config", return_value=config),
        patch.dict(VENDOR_METHODS, {"get_news": {"exa": fake_impl}}, clear=False),
    ):
        # Outside context — no write
        result = route_to_vendor("get_news", "NVDA", "2026-01-30")
        assert result == "FAKE_VALUE"
        assert count_rows() == 0

        # Inside context — write
        with propagate_context("NVDA", "2026-01-30"):
            result = route_to_vendor("get_news", "NVDA", "2026-01-30")
        assert result == "FAKE_VALUE"
        assert count_rows() == 1
        cached = query_value("get_news", "NVDA", "2026-01-30")
        assert cached is not None
        assert cached["value"] == "FAKE_VALUE"


def test_route_to_vendor_cache_failure_does_not_break_dispatch(tmp_path, monkeypatch):
    """If the cache write raises, route_to_vendor still returns the dispatch result."""
    monkeypatch.setenv("TRADINGAGENTS_SIGNALS_DIR", str(tmp_path))
    from tradingagents.dataflows.interface import VENDOR_METHODS, route_to_vendor

    def fake_impl(*a, **kw):
        return "OK"

    config = {"data_vendors": {"news_data": "exa"}, "tool_vendors": {}}
    with (
        patch("tradingagents.dataflows.interface.get_config", return_value=config),
        patch.dict(VENDOR_METHODS, {"get_news": {"exa": fake_impl}}, clear=False),
        patch("tradingagents.signals.cache.record_value", side_effect=RuntimeError("cache broken")),
    ):
        with propagate_context("NVDA", "2026-01-30"):
            result = route_to_vendor("get_news")
        assert result == "OK"  # dispatch succeeded despite cache failure
