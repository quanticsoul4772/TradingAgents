# Contract: Filter Function

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Research**: [../research.md](../research.md) (R-1, R-2, R-3, R-8, R-9, R-10)

The function the PortfolioManager calls to apply the sector-momentum filter. Lives at `tradingagents/agents/utils/sector_momentum_filter.py` per R-8.

---

## Function signature

```python
def maybe_suppress_bull_rating(
    decision_markdown: str,
    ticker: str,
    trade_date: str,
    *,
    threshold_pct: float | None,
    lookback_days: int = 30,
    mode: Literal["off", "shadow", "active"] = "off",
    sectors_cache_path: Path,
    etf_history_fetcher: Callable[[str, str, str], pd.DataFrame] | None = None,
    sector_lookup: Callable[[str], str] | None = None,
) -> tuple[str, dict]:
    """Apply the sector-momentum filter to a PM decision.

    Returns (possibly_modified_decision_markdown, annotation_dict).
    Annotation always populated (never None) but may have `skipped` set.
    Caller is expected to merge `state["sector_momentum"] = annotation` and
    use the modified decision_markdown going forward.

    See ``specs/004-sector-momentum-filter/contracts/annotation_schema.md``
    for the annotation dict shape.
    """
```

---

## Inputs

| Parameter | Type | Notes |
|---|---|---|
| `decision_markdown` | `str` | The PM's full markdown decision (containing the rating line). Same shape A3 + spec 003 receive. |
| `ticker` | `str` | The ticker for the propagate. Sector lookup keyed on this. |
| `trade_date` | `str` (ISO YYYY-MM-DD) | The signal date. ETF history fetched for the prior `lookback_days` trading days strictly before this date. |
| `threshold_pct` | `float \| None` | Configured threshold (e.g., `-5.0`). `None` ⇒ filter disabled (returns unchanged + annotation with `skipped="off"`). Positive values rejected with logged warning + `skipped="invalid_threshold"`. |
| `lookback_days` | `int` | Trading-day lookback. Default 30 (matches A3 + R-9). |
| `mode` | `Literal["off", "shadow", "active"]` | Filter mode. Default `"off"`. |
| `sectors_cache_path` | `Path` | Path to the yfinance sector cache JSON (typically `<paper_state_dir>/sectors.json`). Reused via `tradingagents/paper/sectors.py::get_sector` per R-1. |
| `etf_history_fetcher` | `Callable[[str, str, str], pd.DataFrame] \| None` | Injection point for tests. When None, uses the default LRU-cached yfinance fetcher per R-2. Production callers pass None. |
| `sector_lookup` | `Callable[[str], str] \| None` | Injection point for tests. When None, uses `get_sector(ticker, sectors_cache_path)`. Production callers pass None. |

---

## Output

`(decision_markdown_after_filter, annotation_dict)` per the Annotation Schema contract. The decision_markdown is unchanged unless mode="active" AND the filter fires, in which case the rating line is replaced with `"Hold"` and a `[Sector-momentum filter]` note is appended (matching A3's annotation pattern).

---

## Behavior

1. **Off mode**: return immediately with annotation containing `mode="off"`, `skipped="off"`, all fields default/None.
2. **Bullish-only check**: parse the rating from `decision_markdown`. If not in `{"Buy", "Overweight"}`, return immediately with `skipped="rating_not_bullish"`, `pre_rating=R`, `post_rating=R`.
3. **Threshold validation**: if `threshold_pct` is None or > 0, return immediately with `skipped="off"` (None) or `skipped="invalid_threshold"` (>0; warn).
4. **Sector lookup**: call `sector_lookup(ticker)` (or default `get_sector`). If result is `"Unknown"`, return immediately with `skipped="unknown_sector"`.
5. **ETF mapping**: look up the sector in `SECTOR_ETF_MAP`. If miss, return immediately with `skipped="no_etf_mapping"`.
6. **ETF history fetch**: fetch the ETF's price frame for the prior ~lookback_days × 1.5 + 7 calendar days strictly before `trade_date` via `etf_history_fetcher` (or default LRU-cached yfinance fetch). If empty or insufficient data, return immediately with `skipped="missing_etf_data"`.
7. **Compute prior-N-trading-day return**: delegate to `tradingagents.dataflows.returns.returns_from_frames` with the ETF frame as `stock_df`, a 1-row "self benchmark" frame as `bench_df` so the function returns raw (non-α-vs-SPY) return; OR more directly: take `(close[N] - close[0]) / close[0] * 100` from the ETF frame. Use whichever is cleaner; both produce the same number. Return as percent (e.g., `-8.32`).
8. **Threshold check**: `would_fire = (etf_return_pct < threshold_pct) AND (rating in BULLISH)`. Strict less-than per R-3.
9. **Active-mode override**: if `would_fire AND mode == "active"`, replace the rating line in `decision_markdown` with "Hold" and append the annotation note. Same regex-replace pattern as A3's `momentum_filter.py:54-78`. Set `fired = True`, `post_rating = "Hold"`.
10. **Return** `(decision_markdown, annotation_dict)`.

---

## Failure modes

| Condition | Behavior |
|---|---|
| `sectors_cache_path` doesn't exist | `get_sector` populates it (Spec 002 behavior); no failure. |
| Sector lookup raises | Caught; emit `skipped="unknown_sector"` with logged warning; rating unchanged. |
| yfinance fetch raises | Caught; emit `skipped="missing_etf_data"` with logged warning; rating unchanged. |
| `decision_markdown` parse fails (no rating line) | Treat as `pre_rating="Hold"` (defensive default); emit `skipped="rating_not_bullish"`. |
| Invalid mode value | Treat as `"off"` with logged warning. |
| Threshold > 0 | Logged warning + `skipped="invalid_threshold"` + rating unchanged. |

The function NEVER raises into the PM pipeline (FR-010).

---

## Determinism

Per FR-011, deterministic given (ticker, trade_date, threshold, lookback, mode) modulo upstream yfinance data corrections. The LRU cache (R-2) does not change determinism — it just amortizes repeated fetches within a process.

---

## Performance

- Expected per-evaluation: 1 sector lookup (cache hit O(1)); 1 ETF frame fetch (LRU cache hit O(1) after the first lookup of that ETF in the process); arithmetic on a small DataFrame. Total ≤500ms per propagate per plan's Performance Goals.
- For a `daily_signals.py` run on N tickers in M sectors: M ETF fetches total (one per unique sector); rest are cache hits.

---

## Test fixtures

- `tests/test_sector_momentum_filter.py::test_off_mode_returns_unchanged_with_skipped_off` — covers behavior step 1.
- `tests/test_sector_momentum_filter.py::test_rating_not_bullish_skipped` — Hold/UW/Sell → step 2 path.
- `tests/test_sector_momentum_filter.py::test_threshold_none_returns_unchanged` — step 3 (None case).
- `tests/test_sector_momentum_filter.py::test_threshold_positive_logs_warning_and_skips` — step 3 (>0 case).
- `tests/test_sector_momentum_filter.py::test_unknown_sector_skipped` — step 4.
- `tests/test_sector_momentum_filter.py::test_no_etf_mapping_skipped` — step 5.
- `tests/test_sector_momentum_filter.py::test_missing_etf_data_skipped` — step 6.
- `tests/test_sector_momentum_filter.py::test_threshold_crossed_active_mode_downgrades` — step 7 + 9 happy path.
- `tests/test_sector_momentum_filter.py::test_threshold_crossed_shadow_mode_no_override` — step 7 + 8 (would_fire) without step 9.
- `tests/test_sector_momentum_filter.py::test_threshold_not_crossed_no_fire` — step 8 negative path.
- `tests/test_sector_momentum_filter.py::test_strict_less_than_boundary` — boundary: equality does NOT fire (R-3).
- `tests/test_sector_momentum_filter.py::test_yfinance_fetch_raises_skipped` — step 6 exception path; logged warning.
- `tests/test_sector_momentum_filter.py::test_decision_markdown_no_rating_line_defensive` — defensive default for unparseable markdown.
- `tests/test_sector_momentum_filter.py::test_invalid_mode_falls_back_to_off` — defensive default.
- `tests/test_sector_momentum_filter.py::test_lru_cache_amortizes_repeated_etf_fetches` — performance/cache test.

---

## What this function does NOT do

- Compute α (it only computes raw ETF return; α is downstream / out-of-scope).
- Persist anything (caller integrates with state log).
- Make LLM calls (zero LLM cost per FR-006/SC-005).
- Modify the sectors cache or any other state (read-only).
- Override Underweight/Sell ratings (per FR-007 — only acts on Buy/OW).
- Ever raise into the PM pipeline (per FR-010).
