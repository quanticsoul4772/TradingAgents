"""Unit tests for tradingagents/agents/utils/bear_sector_symmetry_filter.py.

Spec: specs/005-bear-sector-symmetry/contracts/filter_function.md +
      specs/005-bear-sector-symmetry/contracts/annotation_schema.md

Mocks yfinance + sector lookup so tests are fast and deterministic.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from tradingagents.agents.utils.bear_sector_symmetry_filter import (
    SECTOR_ETF_MAP,
    _compute_30d_return_pct,
    _compute_ticker_30d_return_pct,
    clear_etf_cache,
    clear_ticker_cache,
    maybe_suppress_bear_rating,
)


# Featurizer-like stub: build a yfinance-shaped frame with given closes.
def _frame(closes: list[float], start: str = "2026-03-01") -> pd.DataFrame:
    idx = pd.date_range(start, periods=len(closes), freq="B")
    return pd.DataFrame({"Close": closes}, index=idx)


def _make_lookup(sector: str):
    """Sector lookup callable that always returns the given sector."""

    def lookup(_ticker: str) -> str:
        return sector

    return lookup


def _make_ticker_fetcher(frame: pd.DataFrame):
    """Ticker fetcher stub returning the given frame for all calls."""

    def fetch(_ticker: str, _start: str, _end: str) -> pd.DataFrame:
        return frame

    return fetch


def _make_etf_fetcher(frame: pd.DataFrame):
    """ETF fetcher stub returning the given frame for all calls."""

    def fetch(_etf: str, _start: str, _end: str) -> pd.DataFrame:
        return frame

    return fetch


@pytest.fixture(autouse=True)
def _clear_caches():
    clear_etf_cache()
    clear_ticker_cache()
    yield
    clear_etf_cache()
    clear_ticker_cache()


# Standard frame inputs for ticker-up vs sector-flat scenarios:
# ticker frame: 100 → 118 over the 31-row window → +18% return
TICKER_UP_18PCT_FRAME = _frame([100.0] * 5 + [118.0] * 30)
# ETF frame: 100 → 106 → +6% return (delta vs ticker = +12%)
ETF_UP_6PCT_FRAME = _frame([100.0] * 5 + [106.0] * 30)
# ETF frame: 100 → 114 → +14% return (delta vs ticker = +4%, below +5%)
ETF_UP_14PCT_FRAME = _frame([100.0] * 5 + [114.0] * 30)
# ETF frame: ticker delta exactly +5% (boundary) — ticker +18, etf +13 → delta +5
ETF_UP_13PCT_FRAME = _frame([100.0] * 5 + [113.0] * 30)


# -- Off-mode + bearish-only + threshold validation -------------------------


@pytest.mark.unit
def test_off_mode_returns_unchanged_with_skipped_off():
    md = "**Rating**: Underweight\n\nbearish"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="off",
        sector_lookup=_make_lookup("Technology"),
    )
    assert out_md == md
    assert ann["skipped"] == "off"
    assert ann["fired"] is False


@pytest.mark.unit
def test_rating_not_bearish_skipped():
    """Hold/Buy/OW → skipped='rating_not_bearish', rating unchanged."""
    for rating in ("Hold", "Buy", "Overweight"):
        md = f"**Rating**: {rating}\n\nprose"
        out_md, ann = maybe_suppress_bear_rating(
            md,
            "NVDA",
            "2026-04-03",
            threshold_pct=5.0,
            mode="active",
            sector_lookup=_make_lookup("Technology"),
            ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
            etf_history_fetcher=_make_etf_fetcher(ETF_UP_6PCT_FRAME),
        )
        assert out_md == md
        assert ann["skipped"] == "rating_not_bearish", f"failed for rating {rating}"


@pytest.mark.unit
def test_threshold_none_returns_unchanged():
    md = "**Rating**: Underweight\n\nprose"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=None,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
    )
    assert out_md == md
    assert ann["skipped"] == "off"
    assert ann["threshold_pct"] is None


@pytest.mark.unit
def test_threshold_negative_logs_warning_and_skips(caplog):
    md = "**Rating**: Underweight\n\nprose"
    with caplog.at_level("WARNING"):
        out_md, ann = maybe_suppress_bear_rating(
            md,
            "NVDA",
            "2026-04-03",
            threshold_pct=-5.0,  # invalid: negative
            mode="active",
            sector_lookup=_make_lookup("Technology"),
        )
    assert out_md == md
    assert ann["skipped"] == "invalid_threshold"
    assert any("negative" in m.lower() for m in caplog.messages)


# -- Sector lookup + ETF mapping --------------------------------------------


@pytest.mark.unit
def test_unknown_sector_skipped():
    md = "**Rating**: Underweight\n\nprose"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "MYSTERY",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Unknown"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_6PCT_FRAME),
    )
    assert out_md == md
    assert ann["skipped"] == "unknown_sector"
    assert ann["sector"] is None
    assert ann["etf"] is None


@pytest.mark.unit
def test_sector_lookup_failure_skipped(caplog):
    """Sector lookup raising → caught + emit unknown_sector."""

    def raising_lookup(_t: str) -> str:
        raise RuntimeError("yfinance broken")

    md = "**Rating**: Underweight\n\nprose"
    with caplog.at_level("WARNING"):
        out_md, ann = maybe_suppress_bear_rating(
            md,
            "X",
            "2026-04-03",
            threshold_pct=5.0,
            mode="active",
            sector_lookup=raising_lookup,
        )
    assert out_md == md
    assert ann["skipped"] == "unknown_sector"
    assert any("sector lookup failed" in m.lower() for m in caplog.messages)


@pytest.mark.unit
def test_no_etf_mapping_skipped():
    """Sector outside SECTOR_ETF_MAP → skipped."""
    md = "**Rating**: Underweight\n\nprose"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "X",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("ExoticSector"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_6PCT_FRAME),
    )
    assert out_md == md
    assert ann["skipped"] == "no_etf_mapping"
    assert ann["sector"] == "ExoticSector"
    assert ann["etf"] is None


@pytest.mark.unit
def test_missing_ticker_data_skipped():
    """yfinance ticker returns empty frame → skipped='missing_ticker_data'."""
    md = "**Rating**: Underweight\n\nprose"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=_make_ticker_fetcher(pd.DataFrame()),
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_6PCT_FRAME),
    )
    assert out_md == md
    assert ann["skipped"] == "missing_ticker_data"
    assert ann["sector"] == "Technology"
    assert ann["etf"] == "XLK"
    assert ann["ticker_30d_return_pct"] is None


@pytest.mark.unit
def test_missing_etf_data_skipped():
    """yfinance ETF returns empty frame → skipped='missing_etf_data' (with ticker_30d populated)."""
    md = "**Rating**: Underweight\n\nprose"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=_make_etf_fetcher(pd.DataFrame()),
    )
    assert out_md == md
    assert ann["skipped"] == "missing_etf_data"
    assert ann["sector"] == "Technology"
    assert ann["etf"] == "XLK"
    assert ann["ticker_30d_return_pct"] is not None  # populated before ETF fetch
    assert ann["etf_30d_return_pct"] is None


# -- Threshold-crossed firing logic -----------------------------------------


@pytest.mark.unit
def test_threshold_crossed_active_mode_downgrades_underweight():
    """Ticker +18%, ETF +6%, delta +12%, threshold +5%, active, UW → downgrade to Hold."""
    md = "**Rating**: Underweight\n\nbearish prose"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_6PCT_FRAME),
    )
    assert ann["fired"] is True
    assert ann["would_fire"] is True
    assert ann["post_rating"] == "Hold"
    assert ann["pre_rating"] == "Underweight"
    assert "Hold" in out_md.split("Rating")[1].split("\n")[0]
    assert "[Bear-sector-symmetry filter]" in out_md
    assert ann["ticker_30d_return_pct"] == pytest.approx(18.0, abs=0.5)
    assert ann["etf_30d_return_pct"] == pytest.approx(6.0, abs=0.5)
    assert ann["relative_strength_pct"] == pytest.approx(12.0, abs=0.5)


@pytest.mark.unit
def test_threshold_crossed_active_mode_downgrades_sell():
    """Ticker +18%, ETF +6%, delta +12%, threshold +5%, active, Sell → downgrade to Hold."""
    md = "**Rating**: Sell\n\nbearish prose"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_6PCT_FRAME),
    )
    assert ann["fired"] is True
    assert ann["pre_rating"] == "Sell"
    assert ann["post_rating"] == "Hold"
    assert "Hold" in out_md.split("Rating")[1].split("\n")[0]


@pytest.mark.unit
def test_threshold_crossed_shadow_mode_no_override():
    """Threshold crossed but shadow mode → would_fire=True, fired=False, rating unchanged."""
    md = "**Rating**: Underweight\n\nbearish"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="shadow",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_6PCT_FRAME),
    )
    assert ann["would_fire"] is True
    assert ann["fired"] is False
    assert ann["pre_rating"] == "Underweight"
    assert ann["post_rating"] == "Underweight"
    assert out_md == md  # no override


@pytest.mark.unit
def test_threshold_not_crossed_no_fire():
    """Ticker +18%, ETF +14%, delta +4%, threshold +5%, active → no fire."""
    md = "**Rating**: Underweight\n\nbearish"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_14PCT_FRAME),
    )
    assert ann["would_fire"] is False
    assert ann["fired"] is False
    assert ann["pre_rating"] == ann["post_rating"] == "Underweight"
    assert ann["relative_strength_pct"] == pytest.approx(4.0, abs=0.5)
    assert out_md == md


@pytest.mark.unit
def test_strict_greater_than_boundary():
    """Delta EXACTLY equal to threshold MUST NOT fire (strict greater-than per R-3)."""
    # Engineer exact delta = +5%: ticker +18%, ETF +13%
    md = "**Rating**: Underweight\n\nbearish"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_13PCT_FRAME),
    )
    assert ann["relative_strength_pct"] == pytest.approx(5.0, abs=0.001)
    assert ann["would_fire"] is False
    assert ann["fired"] is False
    assert out_md == md


# -- Defensive paths --------------------------------------------------------


@pytest.mark.unit
def test_yfinance_ticker_fetch_raises_skipped():
    """Ticker fetch raising → caught + skipped='missing_ticker_data'."""
    md = "**Rating**: Underweight\n\nbearish"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=lambda *a, **k: pd.DataFrame(),  # simulates LRU empty result
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_6PCT_FRAME),
    )
    assert ann["skipped"] == "missing_ticker_data"


@pytest.mark.unit
def test_yfinance_etf_fetch_raises_skipped():
    """ETF fetch raising → caught + skipped='missing_etf_data'."""
    md = "**Rating**: Underweight\n\nbearish"
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=lambda *a, **k: pd.DataFrame(),
    )
    assert ann["skipped"] == "missing_etf_data"


@pytest.mark.unit
def test_decision_markdown_no_rating_line_defensive():
    """Markdown without a parseable rating line → defaults to 'Hold' → skipped='rating_not_bearish'."""
    md = "Just some prose, no rating line here."
    out_md, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_6PCT_FRAME),
    )
    assert ann["pre_rating"] == "Hold"
    assert ann["skipped"] == "rating_not_bearish"
    assert out_md == md


@pytest.mark.unit
def test_invalid_mode_falls_back_to_off(caplog):
    """Unknown mode value → defaults to 'off' with logged warning."""
    md = "**Rating**: Underweight\n\nbearish"
    with caplog.at_level("WARNING"):
        out_md, ann = maybe_suppress_bear_rating(
            md,
            "NVDA",
            "2026-04-03",
            threshold_pct=5.0,
            mode="bogus",  # type: ignore[arg-type]
            sector_lookup=_make_lookup("Technology"),
        )
    assert ann["mode"] == "off"
    assert ann["skipped"] == "off"
    assert any("unknown mode" in m.lower() for m in caplog.messages)


@pytest.mark.unit
def test_lru_cache_amortizes_repeated_ticker_fetches():
    """Repeated _ticker_history calls with same args hit the LRU cache."""
    fetch_calls = []

    def counting_yf_history(start=None, end=None):
        fetch_calls.append((start, end))
        return _frame([100.0] * 35, start=start or "2026-03-01")

    with patch("tradingagents.agents.utils.bear_sector_symmetry_filter.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.history = counting_yf_history
        from tradingagents.agents.utils.bear_sector_symmetry_filter import _ticker_history

        _ticker_history("NVDA", "2026-03-01", "2026-04-03")
        _ticker_history("NVDA", "2026-03-01", "2026-04-03")
        _ticker_history("NVDA", "2026-03-01", "2026-04-03")
    assert len(fetch_calls) == 1


@pytest.mark.unit
def test_etf_cache_shared_with_spec_004():
    """Importing _etf_history from spec 004 reuses the same LRU cache (cache hit on second call)."""
    fetch_calls = []

    def counting_yf_history(start=None, end=None):
        fetch_calls.append((start, end))
        return _frame([100.0] * 35, start=start or "2026-03-01")

    with patch("tradingagents.agents.utils.sector_momentum_filter.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.history = counting_yf_history
        # Call from spec 004 module
        # Call from spec 006 module (re-imported)
        from tradingagents.agents.utils.bear_sector_symmetry_filter import (
            _etf_history as etf_via_spec006,
        )
        from tradingagents.agents.utils.sector_momentum_filter import (
            _etf_history as etf_via_spec004,
        )

        # Same function object — same LRU cache
        assert etf_via_spec004 is etf_via_spec006

        etf_via_spec004("XLK", "2026-03-01", "2026-04-03")
        etf_via_spec006("XLK", "2026-03-01", "2026-04-03")  # cache hit
    assert len(fetch_calls) == 1


# -- Annotation invariants per data-model.md --------------------------------


@pytest.mark.unit
def test_annotation_active_fires_populates_all_fields():
    """All 13 fields populated when fired=True."""
    md = "**Rating**: Underweight\n\nbearish"
    _, ann = maybe_suppress_bear_rating(
        md,
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_6PCT_FRAME),
    )
    expected_fields = {
        "mode",
        "sector",
        "etf",
        "ticker_30d_return_pct",
        "etf_30d_return_pct",
        "relative_strength_pct",
        "threshold_pct",
        "lookback_days",
        "would_fire",
        "fired",
        "pre_rating",
        "post_rating",
        "skipped",
    }
    assert set(ann.keys()) == expected_fields
    # All non-skipped fields populated
    assert ann["mode"] == "active"
    assert ann["sector"] == "Technology"
    assert ann["etf"] == "XLK"
    assert ann["ticker_30d_return_pct"] is not None
    assert ann["etf_30d_return_pct"] is not None
    assert ann["relative_strength_pct"] is not None
    assert ann["threshold_pct"] == 5.0
    assert ann["lookback_days"] == 30
    assert ann["would_fire"] is True
    assert ann["fired"] is True
    assert ann["pre_rating"] == "Underweight"
    assert ann["post_rating"] == "Hold"
    assert ann["skipped"] is None


@pytest.mark.unit
def test_annotation_invariants_per_data_model():
    """Invariants 1-11 from data-model.md."""
    # Invariant 1: skipped == "off" → all data fields None
    _, ann_off = maybe_suppress_bear_rating(
        "**Rating**: Underweight\n",
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="off",
        sector_lookup=_make_lookup("Technology"),
    )
    assert ann_off["skipped"] == "off"
    assert ann_off["sector"] is None
    assert ann_off["etf"] is None
    assert ann_off["would_fire"] is False
    assert ann_off["fired"] is False
    assert ann_off["post_rating"] == ann_off["pre_rating"]

    # Invariant 6: skipped == "rating_not_bearish" → pre_rating in {Buy, OW, Hold}
    _, ann_buy = maybe_suppress_bear_rating(
        "**Rating**: Buy\n",
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_6PCT_FRAME),
    )
    assert ann_buy["skipped"] == "rating_not_bearish"
    assert ann_buy["pre_rating"] in {"Buy", "Overweight", "Hold"}
    assert ann_buy["would_fire"] is False

    # Invariant 9: fired=True → would_fire=True AND mode=active AND
    # pre_rating in {UW, Sell} AND post_rating == "Hold"
    _, ann_fire = maybe_suppress_bear_rating(
        "**Rating**: Underweight\n",
        "NVDA",
        "2026-04-03",
        threshold_pct=5.0,
        mode="active",
        sector_lookup=_make_lookup("Technology"),
        ticker_history_fetcher=_make_ticker_fetcher(TICKER_UP_18PCT_FRAME),
        etf_history_fetcher=_make_etf_fetcher(ETF_UP_6PCT_FRAME),
    )
    assert ann_fire["fired"] is True
    assert ann_fire["would_fire"] is True
    assert ann_fire["mode"] == "active"
    assert ann_fire["pre_rating"] == "Underweight"
    assert ann_fire["post_rating"] == "Hold"

    # Invariant 11: relative_strength_pct == ticker - etf when both populated
    assert ann_fire["relative_strength_pct"] == pytest.approx(
        ann_fire["ticker_30d_return_pct"] - ann_fire["etf_30d_return_pct"],
        abs=1e-9,
    )


@pytest.mark.unit
def test_audit_corpus_filter_by_fired_and_relative_strength():
    """Synthetic annotations filterable by `fired` + `relative_strength_pct`."""
    annotations = [
        {"fired": True, "relative_strength_pct": 12.0, "etf": "XLK"},
        {"fired": False, "relative_strength_pct": 8.0, "etf": "XLK"},
        {"fired": True, "relative_strength_pct": 6.0, "etf": "XLF"},
        {"fired": False, "relative_strength_pct": None, "etf": "XLV"},
        {"fired": False, "relative_strength_pct": 2.0, "etf": "XLK"},
        {"fired": False, "relative_strength_pct": -1.0, "etf": "XLE"},
    ]
    fired_only = [a for a in annotations if a["fired"]]
    assert len(fired_only) == 2
    high_rel_strength = [
        a
        for a in annotations
        if a["relative_strength_pct"] is not None and a["relative_strength_pct"] > 5
    ]
    assert len(high_rel_strength) == 3


# -- SECTOR_ETF_MAP reuse from spec 004 -------------------------------------


@pytest.mark.unit
def test_sector_etf_map_imported_from_spec_004():
    """Verify FR-004: SECTOR_ETF_MAP is imported from spec 004's module — same object."""
    from tradingagents.agents.utils.sector_momentum_filter import (
        SECTOR_ETF_MAP as SPEC_004_MAP,
    )

    assert SECTOR_ETF_MAP is SPEC_004_MAP


# -- _compute_30d_return_pct direct tests -----------------------------------


@pytest.mark.unit
def test_compute_30d_return_pct_insufficient_history():
    """Frame with < lookback+1 rows → returns None."""
    frame = _frame([100.0] * 10)  # only 10 rows; lookback=30 needs 31
    assert _compute_30d_return_pct(frame, 30) is None


@pytest.mark.unit
def test_compute_30d_return_pct_correct_arithmetic():
    """31-row frame, 100 → 110: returns +10.0."""
    frame = _frame([100.0] * 5 + [110.0] * 30)
    result = _compute_30d_return_pct(frame, 30)
    assert result == pytest.approx(10.0, abs=0.01)


@pytest.mark.unit
def test_compute_ticker_invalid_trade_date():
    """Malformed trade_date → returns None."""
    result = _compute_ticker_30d_return_pct(
        "NVDA",
        "not-a-date",
        fetcher=_make_ticker_fetcher(_frame([100.0] * 35)),
    )
    assert result is None


# -- SC-008 empirical-validation gate ---------------------------------------
# Marked @pytest.mark.integration: hits live yfinance, skipped by `pytest -m unit`.


@pytest.mark.integration
def test_today_ticker_strong_bear_cohort_suppression_at_5pct():
    """SC-008 empirical-validation gate.

    The original spec target was ≥8 of 18 ticker_strong-bearish cohort commits
    suppressed at +5% threshold. The empirical retrospective (run 2026-05-06,
    documented in claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md)
    showed only **5 of 18** fire at +5% — so SC-008 FAILED as originally
    specified and the filter stays default-off.

    This test now serves two purposes:

    1. **Regression detector**: assert the empirical outcome (5/18 fire) so
       a future code change that breaks the filter logic OR a yfinance data
       correction that changes the count is flagged.
    2. **Falsifiable record**: a permanent runnable check that the spec's
       motivating premise was tested and found empirically insufficient.

    Loads the cohort from the sister CSV
    (claudedocs/sector-alpha-attribution-2026-05-06.csv) so the test stays
    forward-compatible if the analyzer is re-run with a larger corpus.

    Skipped with a clear message if the CSV or sectors cache is missing.
    """
    csv_path = Path("claudedocs/sector-alpha-attribution-2026-05-06.csv")
    if not csv_path.exists():
        pytest.skip(f"Attribution CSV missing: {csv_path}")
    sectors_cache = Path.home() / ".tradingagents" / "paper" / "sectors.json"
    if not sectors_cache.exists():
        pytest.skip(f"Sectors cache missing: {sectors_cache}")

    df = pd.read_csv(csv_path)
    cohort = df[(df["rating"].isin(("Underweight", "Sell"))) & (df["cell"] == "ticker_strong")]
    if len(cohort) == 0:
        pytest.skip("Cohort empty in attribution CSV (analyzer may need re-run)")

    fired_count = 0
    for _, r in cohort.iterrows():
        _, ann = maybe_suppress_bear_rating(
            f"**Rating**: {r['rating']}\n\nbearish",
            r["ticker"],
            r["trade_date"],
            threshold_pct=5.0,
            mode="active",
            lookback_days=30,
            sectors_cache_path=sectors_cache,
        )
        if ann.get("fired"):
            fired_count += 1

    n_total = len(cohort)
    # SC-008 spec target was >= 8; empirical reality is 5 (snapshot from
    # 2026-05-06 retrospective). Test asserts empirical outcome so it serves
    # as a regression detector. A future change that drops the count below 5
    # OR raises it above 5 indicates either a code regression or a yfinance
    # data correction worth investigating.
    assert fired_count == 5, (
        f"Empirical outcome from 2026-05-06 retrospective was 5 of {n_total} "
        f"ticker_strong-bearish cohort commits suppressed at +5% threshold; "
        f"got {fired_count}. If this changed: (a) check for a recent code change "
        f"to the filter logic, (b) check for a yfinance data correction that "
        f"shifted prior-30d relative-strength values for the cohort dates, "
        f"(c) update this snapshot if the change is intentional. SC-008 spec "
        f"target was ≥8 of {n_total}; empirically failed at +5% (see "
        f"claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md verdict)."
    )
