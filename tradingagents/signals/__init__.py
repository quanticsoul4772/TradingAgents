"""Signal lifecycle (spec 002) — registry + cache + future evaluation harness.

Phase 0 (this commit) ships the foundational storage layer:
- Signal registry (append-only JSONL, latest snapshot wins per signal_id)
- Per-(signal, ticker, date) SQLite cache populated transparently from
  ``route_to_vendor`` during a propagate (via ``propagate_context``)

Phase 1+ (deferred): evaluation harness, drift detector, counterfactual
tester, reweight aggregator, combinatorial discovery, LLM discovery,
regime-conditional weights.

See ``.specify/specs/002-signal-lifecycle/spec.md`` for the full spec and
``docs/SIGNAL_LIFECYCLE.md`` for the design rationale.
"""

from __future__ import annotations

from tradingagents.signals.bootstrap import (
    bootstrap_initial_signals,
    get_initial_signal_ids,
)
from tradingagents.signals.cache import (
    count_rows,
    init_cache,
    query_all,
    query_value,
    record_value,
)
from tradingagents.signals.context import (
    PropagateContext,
    get_propagate_context,
    propagate_context,
)
from tradingagents.signals.paths import (
    get_cache_path,
    get_registry_path,
    get_signals_dir,
)
from tradingagents.signals.registry import (
    VALID_STATES,
    SignalDefinition,
    StateTransition,
    get_signal,
    list_signals,
    load_registry,
    register_signal,
    transition_state,
)

__all__ = [
    "PropagateContext",
    "SignalDefinition",
    "StateTransition",
    "VALID_STATES",
    "bootstrap_initial_signals",
    "count_rows",
    "get_cache_path",
    "get_initial_signal_ids",
    "get_propagate_context",
    "get_registry_path",
    "get_signal",
    "get_signals_dir",
    "init_cache",
    "list_signals",
    "load_registry",
    "propagate_context",
    "query_all",
    "query_value",
    "record_value",
    "register_signal",
    "transition_state",
]
