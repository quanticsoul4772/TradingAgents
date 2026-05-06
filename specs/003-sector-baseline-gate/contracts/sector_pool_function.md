# Contract: Sector-Pool Aggregator Function

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Research**: [../research.md](../research.md) (R-1, R-2, R-3, R-4, R-7, R-10)

The internal function that aggregates `bull_keyword_count` history across same-sector tickers. Lives in the new `tradingagents/signals/sector_baseline.py` module per R-8.

---

## Function signature

```python
def aggregate_sector_pool(
    sector: str,
    before_date: date,
    *,
    sectors_cache_path: Path,
    state_logs_root: Path,
    feature_callable: Callable[[str], float],
    log_filename_pattern: str = "full_states_log_*.json",
) -> SectorPool:
    """Aggregate `feature_callable(market_report)` values across all tickers
    whose cached sector matches `sector`, strictly before `before_date`.

    Returns a `SectorPool` with `values: list[float]`, `n: int`, and
    `contributors: dict[str, int]`. Empty pool returned for `sector == "Unknown"`
    or when no same-sector state logs are found.
    """
```

---

## Inputs

| Parameter | Type | Notes |
|---|---|---|
| `sector` | `str` | The sector to aggregate over (e.g., `"Technology"`). If `"Unknown"`, returns empty pool per R-4. Empty string also returns empty pool. |
| `before_date` | `date` | Strict-prior cutoff. Pool excludes all state logs whose filename-encoded date is `>= before_date`. Per R-2: this includes same-day observations from other tickers in the same sector. |
| `sectors_cache_path` | `Path` | Path to the yfinance sector cache JSON (typically `~/.tradingagents/paper/sectors.json`). Reused via `tradingagents/paper/sectors.py::get_sector` per R-10. |
| `state_logs_root` | `Path` | Path to the per-ticker state-log root (typically `~/.tradingagents/logs/`). Each ticker has subdirectory `<TICKER>/TradingAgentsStrategy_logs/full_states_log_*.json`. |
| `feature_callable` | `Callable[[str], float]` | The featurizer to apply to `market_report` text. In production: `tradingagents.signals.featurization.bull_keyword_count`. Pluggable for tests + future feature variants per Spec 003 FR-004 pluggability. |
| `log_filename_pattern` | `str` | Glob pattern for state logs. Default matches the existing convention. |

---

## Output

```python
@dataclass(frozen=True)
class SectorPool:
    sector: str
    before_date: date
    values: list[float]                # the pooled feature values
    n: int                             # len(values); cached for convenience
    contributors: dict[str, int]       # {ticker: n_observations_from_that_ticker}
```

---

## Behavior

1. **Sector lookup**: For `sector == "Unknown"` or empty string, return `SectorPool(sector=sector, before_date=before_date, values=[], n=0, contributors={})` immediately.
2. **Discover same-sector tickers**: Iterate the `state_logs_root` directory. For each subdirectory (one per ticker the framework has propagated on), call `tradingagents/paper/sectors.py::get_sector(ticker, sectors_cache_path)`. If the returned sector matches `sector` exactly (case-sensitive), include this ticker.
3. **Scan state logs per ticker**: For each included ticker, glob `<state_logs_root>/<TICKER>/TradingAgentsStrategy_logs/<log_filename_pattern>`. For each matching file:
   - Parse the date from the filename (format: `full_states_log_YYYY-MM-DD.json`). Skip if filename doesn't match the pattern.
   - If parsed date `>= before_date`, skip (strict-prior cutoff per R-2).
   - Otherwise, read the JSON, extract `state["market_report"]`, call `feature_callable(market_report)` to compute the feature value.
   - Append the value to the pool.
   - Increment `contributors[ticker]`.
4. **Return**: `SectorPool` with the accumulated values, n, contributors.

---

## Failure modes

| Condition | Behavior |
|---|---|
| `sectors_cache_path` doesn't exist | `get_sector` populates it on first lookup (Spec 002 behavior); no failure. |
| `state_logs_root` doesn't exist | Return empty pool. |
| A specific state log file is corrupt JSON | Log a warning; skip that file; continue with others. Mirrors the resilience pattern in `scripts/contrarian_gate_retrospective.py`. |
| `feature_callable` raises on a particular `market_report` | Log a warning; skip that observation; continue. |
| `sectors_cache_path` JSON is corrupt | Underlying `get_sector` re-fetches and rebuilds (Spec 002 behavior); no failure. |
| yfinance call times out during a sector lookup | `get_sector` returns `"Unknown"`; that ticker is excluded from the pool. |

---

## Determinism

- Iteration order over the `state_logs_root` is sorted alphabetically by ticker, then sorted alphabetically by filename within each ticker. Same set of state logs → same ordered values list → same percentile.
- `contributors` dict is constructed in iteration order (insertion order; Python 3.7+ guarantee).
- The function makes no random choices and depends only on filesystem contents + the cache.

---

## Performance

- Expected: O(N_tickers_in_sector × N_state_logs_per_ticker) JSON parses + `feature_callable` invocations. At the project's scale (≤50 tickers per sector typically much fewer; ≤50 state logs per ticker), this is ≤2500 ops, well under the 200ms budget per R-3.
- No caching in v1.

---

## Test fixtures

- `tests/test_sector_baseline.py::test_empty_pool_for_unknown_sector` — sector="Unknown" returns empty pool.
- `tests/test_sector_baseline.py::test_strict_prior_cutoff_excludes_same_day_observations` — state log dated == before_date is excluded.
- `tests/test_sector_baseline.py::test_aggregates_across_multiple_same_sector_tickers` — synthetic state logs for 3 Tech tickers; pool has all values; contributors has correct counts per ticker.
- `tests/test_sector_baseline.py::test_corrupt_state_log_skipped_with_warning` — one corrupted file doesn't break the aggregation.
- `tests/test_sector_baseline.py::test_iteration_order_deterministic` — running twice on the same fixture produces identical `values` lists.
- `tests/test_sector_baseline.py::test_feature_callable_failure_skips_observation` — mock featurizer that raises on one ticker; pool excludes that observation but includes others.

---

## What this function does NOT do

- Compute percentiles. That's the caller's job (`ContrarianGate.compute_annotation`).
- Filter by minimum-diversity (≥3 distinct contributors). v1 has no diversity rule per R-7.
- Cache results. v1 recomputes per evaluation per R-3.
- Modify the sectors cache or the state logs. Read-only.
- Make LLM calls. Zero LLM cost per FR-006/SC-006.
