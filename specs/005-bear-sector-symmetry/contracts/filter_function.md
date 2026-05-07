# Contract: Filter Function

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Research**: [../research.md](../research.md) (R-1, R-2, R-3, R-8, R-9, R-10, R-11)

The function the PortfolioManager calls to apply the bear-sector-symmetry filter. Lives at `tradingagents/agents/utils/bear_sector_symmetry_filter.py` per R-8.

---

## Function signature

```python
def maybe_suppress_bear_rating(
    decision_markdown: str,
    ticker: str,
    trade_date: str,
    *,
    threshold_pct: float | None,
    lookback_days: int = 30,
    mode: Literal["off", "shadow", "active"] = "off",
    sectors_cache_path: Path,
    etf_history_fetcher: Callable[[str, str, str], pd.DataFrame] | None = None,
    ticker_history_fetcher: Callable[[str, str, str], pd.DataFrame] | None = None,
    sector_lookup: Callable[[str], str] | None = None,
) -> tuple[str, dict]:
    """Apply the bear-sector-symmetry filter to a PM decision.

    Returns (possibly_modified_decision_markdown, annotation_dict).
    Annotation always populated (never None) but may have `skipped` set.
    Caller is expected to merge `state["bear_sector_symmetry"] = annotation`
    and use the modified decision_markdown going forward.

    See ``specs/005-bear-sector-symmetry/contracts/annotation_schema.md``
    for the annotation dict shape.
    """
```

---

## Inputs

| Parameter | Type | Notes |
|---|---|---|
| `decision_markdown` | `str` | The PM's full markdown decision (containing the rating line). Same shape A3 + spec 003 + spec 004 receive. |
| `ticker` | `str` | The ticker for the propagate. Sector lookup keyed on this. |
| `trade_date` | `str` (ISO YYYY-MM-DD) | The signal date. Ticker + ETF history fetched for the prior `lookback_days` trading days strictly before this date. |
| `threshold_pct` | `float \| None` | Configured threshold (e.g., `+5.0`). `None` ⇒ filter disabled (returns unchanged + annotation with `skipped="off"`). Negative values rejected with logged warning + `skipped="invalid_threshold"`. |
| `lookback_days` | `int` | Trading-day lookback. Default 30 (matches A3 + spec 004 + R-9). |
| `mode` | `Literal["off", "shadow", "active"]` | Filter mode. Default `"off"`. |
| `sectors_cache_path` | `Path` | Path to the yfinance sector cache JSON (typically `<paper_state_dir>/sectors.json`). Reused via `tradingagents/paper/sectors.py::get_sector` per R-1. |
| `etf_history_fetcher` | `Callable[[str, str, str], pd.DataFrame] \| None` | Injection point for tests. When None, uses spec 004's `_etf_history` LRU-cached yfinance fetcher per R-2. Production callers pass None. |
| `ticker_history_fetcher` | `Callable[[str, str, str], pd.DataFrame] \| None` | Injection point for tests. When None, uses this module's `_ticker_history` LRU-cached yfinance fetcher per R-2. Production callers pass None. |
| `sector_lookup` | `Callable[[str], str] \| None` | Injection point for tests. When None, uses `get_sector(ticker, sectors_cache_path)`. Production callers pass None. |

---

## Output

`(decision_markdown_after_filter, annotation_dict)` per the Annotation Schema contract. The decision_markdown is unchanged unless mode="active" AND the filter fires, in which case the rating line is replaced with `"Hold"` and a `[Bear-sector-symmetry filter]` note is appended (matching A3's + spec 004's annotation pattern).

---

## Behavior

1. **Off mode**: return immediately with annotation containing `mode="off"`, `skipped="off"`, all fields default/None.
2. **Bearish-only check**: parse the rating from `decision_markdown`. If not in `{"Underweight", "Sell"}`, return immediately with `skipped="rating_not_bearish"`, `pre_rating=R`, `post_rating=R`.
3. **Threshold validation**: if `threshold_pct` is None, return immediately with `skipped="off"`. If `threshold_pct < 0`, return immediately with `skipped="invalid_threshold"` (warn).
4. **Sector lookup**: call `sector_lookup(ticker)` (or default `get_sector`). If result is `"Unknown"`, return immediately with `skipped="unknown_sector"`.
5. **ETF mapping**: look up the sector in `SECTOR_ETF_MAP` (imported from spec 004's module). If miss, return immediately with `skipped="no_etf_mapping"`.
6. **Ticker history fetch**: fetch the ticker's price frame for the prior ~lookback_days × 1.5 + 7 calendar days strictly before `trade_date` via `ticker_history_fetcher` (or default LRU-cached yfinance fetch). If empty or insufficient data, return immediately with `skipped="missing_ticker_data"`.
7. **ETF history fetch**: same as step 6 but for the sector ETF. If empty or insufficient data, return immediately with `skipped="missing_etf_data"` (with `ticker_30d_return_pct` populated).
8. **Compute prior-N-trading-day returns**: extract the ticker's prior-30d return + ETF's prior-30d return as percent (e.g., `+18.32` and `+6.40`). The math is `(close[N] - close[0]) / close[0] * 100` for each frame independently.
9. **Compute relative-strength delta**: `relative_strength_pct = ticker_30d_return_pct − etf_30d_return_pct`.
10. **Threshold check**: `would_fire = (relative_strength_pct > threshold_pct) AND (rating in BEARISH)`. Strict greater-than per R-3.
11. **Active-mode override**: if `would_fire AND mode == "active"`, replace the rating line in `decision_markdown` with "Hold" and append the annotation note. Same regex-replace pattern as A3's + spec 004's. Set `fired = True`, `post_rating = "Hold"`.
12. **Return** `(decision_markdown, annotation_dict)`.

---

## Failure modes

| Condition | Behavior |
|---|---|
| `sectors_cache_path` doesn't exist | `get_sector` populates it (Spec 002 behavior); no failure. |
| Sector lookup raises | Caught; emit `skipped="unknown_sector"` with logged warning; rating unchanged. |
| yfinance ticker fetch raises | Caught; emit `skipped="missing_ticker_data"` with logged warning; rating unchanged. |
| yfinance ETF fetch raises | Caught; emit `skipped="missing_etf_data"` with logged warning; rating unchanged. |
| `decision_markdown` parse fails (no rating line) | Treat as `pre_rating="Hold"` (defensive default); emit `skipped="rating_not_bearish"`. |
| Invalid mode value | Treat as `"off"` with logged warning. |
| Threshold < 0 | Logged warning + `skipped="invalid_threshold"` + rating unchanged. |
| A3 already suppressed UW/Sell to Hold (SC-009) | Pre-rating is now Hold; this filter no-ops via step 2 (`skipped="rating_not_bearish"`). |

The function NEVER raises into the PM pipeline (FR-010).

---

## Determinism

Per FR-011, deterministic given `(ticker, trade_date, threshold, lookback, mode)` modulo upstream yfinance data corrections. The LRU caches (R-2) do not change determinism — they just amortize repeated fetches within a process.

---

## Performance

- Expected per-evaluation: 1 sector lookup (cache hit O(1)); 1 ticker frame fetch (LRU cache hit O(1) after the first lookup of that ticker × date range in the process); 1 ETF frame fetch (LRU cache hit O(1) — likely a hit if spec 004 has already run on the same ticker/sector in the same propagate); arithmetic on small DataFrames. Total ≤500ms per propagate per plan's Performance Goals.
- For a `daily_signals.py` run on N tickers in M sectors: M ETF fetches total (one per unique sector); N ticker fetches; rest are cache hits.
- Spec 004 cache reuse: when both filters run on the same ticker (always true, since both run on every propagate), the second filter's ETF fetch is a cache hit on spec 004's first fetch.

---

## Test fixtures

- `tests/test_bear_sector_symmetry_filter.py::test_off_mode_returns_unchanged_with_skipped_off` — covers behavior step 1.
- `tests/test_bear_sector_symmetry_filter.py::test_rating_not_bearish_skipped` — Hold/Buy/OW → step 2 path.
- `tests/test_bear_sector_symmetry_filter.py::test_threshold_none_returns_unchanged` — step 3 (None case).
- `tests/test_bear_sector_symmetry_filter.py::test_threshold_negative_logs_warning_and_skips` — step 3 (<0 case).
- `tests/test_bear_sector_symmetry_filter.py::test_unknown_sector_skipped` — step 4.
- `tests/test_bear_sector_symmetry_filter.py::test_no_etf_mapping_skipped` — step 5.
- `tests/test_bear_sector_symmetry_filter.py::test_missing_ticker_data_skipped` — step 6.
- `tests/test_bear_sector_symmetry_filter.py::test_missing_etf_data_skipped` — step 7 (with ticker data populated).
- `tests/test_bear_sector_symmetry_filter.py::test_threshold_crossed_active_mode_downgrades_underweight` — step 8 + 11 happy path on Underweight.
- `tests/test_bear_sector_symmetry_filter.py::test_threshold_crossed_active_mode_downgrades_sell` — step 8 + 11 happy path on Sell.
- `tests/test_bear_sector_symmetry_filter.py::test_threshold_crossed_shadow_mode_no_override` — step 8 + 10 (would_fire) without step 11.
- `tests/test_bear_sector_symmetry_filter.py::test_threshold_not_crossed_no_fire` — step 10 negative path.
- `tests/test_bear_sector_symmetry_filter.py::test_strict_greater_than_boundary` — boundary: equality does NOT fire (R-3).
- `tests/test_bear_sector_symmetry_filter.py::test_yfinance_ticker_fetch_raises_skipped` — step 6 exception path; logged warning.
- `tests/test_bear_sector_symmetry_filter.py::test_yfinance_etf_fetch_raises_skipped` — step 7 exception path; logged warning.
- `tests/test_bear_sector_symmetry_filter.py::test_decision_markdown_no_rating_line_defensive` — defensive default for unparseable markdown.
- `tests/test_bear_sector_symmetry_filter.py::test_invalid_mode_falls_back_to_off` — defensive default.
- `tests/test_bear_sector_symmetry_filter.py::test_lru_cache_amortizes_repeated_ticker_fetches` — performance/cache test.
- `tests/test_bear_sector_symmetry_filter.py::test_relative_strength_computation_correct` — `ticker − etf` arithmetic.
- `tests/test_bear_sector_symmetry_filter.py::test_etf_cache_shared_with_spec_004` — verifies importing spec 004's `_etf_history` reuses the cache (cache hit on second call after spec 004 ran).

---

## What this function does NOT do

- Compute α (it only computes raw ticker + ETF returns + their delta; α is downstream / out-of-scope).
- Persist anything (caller integrates with state log).
- Make LLM calls (zero LLM cost per FR-006/SC-005).
- Modify the sectors cache or any other state (read-only).
- Override Buy/Overweight/Hold ratings (per FR-007 — only acts on Underweight/Sell).
- Upgrade ratings to Buy/OW (per FR-007 — suppression target is always Hold, never bullish).
- Re-implement the SECTOR_ETF_MAP (per FR-004 — imports from spec 004's module).
- Ever raise into the PM pipeline (per FR-010).
