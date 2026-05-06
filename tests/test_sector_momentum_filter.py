"""Unit tests for tradingagents/agents/utils/sector_momentum_filter.py.

Spec: specs/004-sector-momentum-filter/contracts/filter_function.md +
      specs/004-sector-momentum-filter/contracts/annotation_schema.md

Mocks yfinance + sector lookup so tests are fast and deterministic.
"""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from tradingagents.agents.utils.sector_momentum_filter import (
    SECTOR_ETF_MAP,
    _compute_etf_30d_return_pct,
    clear_etf_cache,
    maybe_suppress_bull_rating,
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


def _make_fetcher(frame: pd.DataFrame):
    """ETF fetcher stub returning the given frame for all calls."""

    def fetch(_etf: str, _start: str, _end: str) -> pd.DataFrame:
        return frame

    return fetch


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_etf_cache()
    yield
    clear_etf_cache()


# -- Off-mode + bullish-only + threshold validation -------------------------


@pytest.mark.unit
def test_off_mode_returns_unchanged_with_skipped_off():
    md = "**Rating**: Overweight\n\nbullish"
    out_md, ann = maybe_suppress_bull_rating(
        md,
        "WFC",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="off",
        sector_lookup=_make_lookup("Financial Services"),
    )
    assert out_md == md
    assert ann["skipped"] == "off"
    assert ann["fired"] is False


@pytest.mark.unit
def test_rating_not_bullish_skipped():
    """Hold/UW/Sell → skipped='rating_not_bullish', rating unchanged."""
    for rating in ("Hold", "Underweight", "Sell"):
        md = f"**Rating**: {rating}\n\nprose"
        out_md, ann = maybe_suppress_bull_rating(
            md,
            "WFC",
            "2026-04-03",
            threshold_pct=-5.0,
            mode="active",
            sector_lookup=_make_lookup("Financial Services"),
            etf_history_fetcher=_make_fetcher(_frame([100.0] * 35)),
        )
        assert out_md == md
        assert ann["skipped"] == "rating_not_bullish", f"failed for rating {rating}"


@pytest.mark.unit
def test_threshold_none_returns_unchanged():
    md = "**Rating**: Overweight\n\nprose"
    out_md, ann = maybe_suppress_bull_rating(
        md,
        "WFC",
        "2026-04-03",
        threshold_pct=None,
        mode="active",
        sector_lookup=_make_lookup("Financial Services"),
    )
    assert out_md == md
    assert ann["skipped"] == "off"
    assert ann["threshold_pct"] is None


@pytest.mark.unit
def test_threshold_positive_logs_warning_and_skips(caplog):
    md = "**Rating**: Overweight\n\nprose"
    with caplog.at_level("WARNING"):
        out_md, ann = maybe_suppress_bull_rating(
            md,
            "WFC",
            "2026-04-03",
            threshold_pct=5.0,  # invalid: positive
            mode="active",
            sector_lookup=_make_lookup("Financial Services"),
        )
    assert out_md == md
    assert ann["skipped"] == "invalid_threshold"
    assert any("positive" in m.lower() for m in caplog.messages)


# -- Sector lookup + ETF mapping --------------------------------------------


@pytest.mark.unit
def test_unknown_sector_skipped():
    md = "**Rating**: Overweight\n\nprose"
    out_md, ann = maybe_suppress_bull_rating(
        md,
        "MYSTERY",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="active",
        sector_lookup=_make_lookup("Unknown"),
        etf_history_fetcher=_make_fetcher(_frame([100.0] * 35)),
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

    md = "**Rating**: Overweight\n\nprose"
    with caplog.at_level("WARNING"):
        out_md, ann = maybe_suppress_bull_rating(
            md,
            "X",
            "2026-04-03",
            threshold_pct=-5.0,
            mode="active",
            sector_lookup=raising_lookup,
        )
    assert out_md == md
    assert ann["skipped"] == "unknown_sector"
    assert any("sector lookup failed" in m.lower() for m in caplog.messages)


@pytest.mark.unit
def test_no_etf_mapping_skipped():
    """A sector yfinance reports outside SECTOR_ETF_MAP → skipped."""
    md = "**Rating**: Overweight\n\nprose"
    out_md, ann = maybe_suppress_bull_rating(
        md,
        "X",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="active",
        sector_lookup=_make_lookup("ExoticSector"),
        etf_history_fetcher=_make_fetcher(_frame([100.0] * 35)),
    )
    assert out_md == md
    assert ann["skipped"] == "no_etf_mapping"
    assert ann["sector"] == "ExoticSector"
    assert ann["etf"] is None


@pytest.mark.unit
def test_missing_etf_data_skipped():
    """yfinance returns empty frame → skipped='missing_etf_data'."""
    md = "**Rating**: Overweight\n\nprose"
    out_md, ann = maybe_suppress_bull_rating(
        md,
        "WFC",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="active",
        sector_lookup=_make_lookup("Financial Services"),
        etf_history_fetcher=_make_fetcher(pd.DataFrame()),
    )
    assert out_md == md
    assert ann["skipped"] == "missing_etf_data"
    assert ann["sector"] == "Financial Services"
    assert ann["etf"] == "XLF"
    assert ann["etf_30d_return_pct"] is None


# -- Threshold-crossed firing logic -----------------------------------------


@pytest.mark.unit
def test_threshold_crossed_active_mode_downgrades():
    """ETF down -8%, threshold -5%, active mode, Overweight → downgrade to Hold."""
    # 35 closes: start 100, end 92 → -8% return on the last 31 (lookback+1)
    frame = _frame([100.0] * 4 + list(range(100, 91, -1)) * 1 + [92.0] * 22)
    # Actually simpler: deterministic -8% over a 31-row window
    closes = [100.0] * 5 + [92.0] * 30  # 35 rows; last 31 has start=100, end=92
    # Wait — last 31 of [100*5 + 92*30]: rows 4..34 = [100, 92, 92, ..., 92] → -8% return
    frame = _frame(closes)
    md = "**Rating**: Overweight\n\nbullish prose"
    out_md, ann = maybe_suppress_bull_rating(
        md,
        "WFC",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="active",
        sector_lookup=_make_lookup("Financial Services"),
        etf_history_fetcher=_make_fetcher(frame),
    )
    assert ann["fired"] is True
    assert ann["would_fire"] is True
    assert ann["post_rating"] == "Hold"
    assert ann["pre_rating"] == "Overweight"
    assert "Hold" in out_md.split("Rating")[1].split("\n")[0]
    assert "[Sector-momentum filter]" in out_md
    # Allow some tolerance — the function takes the LAST 31 rows
    assert ann["etf_30d_return_pct"] < -5.0


@pytest.mark.unit
def test_threshold_crossed_shadow_mode_no_override():
    """ETF down -8%, threshold -5%, SHADOW mode → would_fire=True, fired=False, rating unchanged."""
    closes = [100.0] * 5 + [92.0] * 30
    frame = _frame(closes)
    md = "**Rating**: Overweight\n\nbullish"
    out_md, ann = maybe_suppress_bull_rating(
        md,
        "WFC",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="shadow",
        sector_lookup=_make_lookup("Financial Services"),
        etf_history_fetcher=_make_fetcher(frame),
    )
    assert ann["would_fire"] is True
    assert ann["fired"] is False
    assert ann["pre_rating"] == "Overweight"
    assert ann["post_rating"] == "Overweight"
    assert out_md == md  # no override


@pytest.mark.unit
def test_threshold_not_crossed_no_fire():
    """ETF down -2%, threshold -5%, active mode → no fire."""
    closes = [100.0] * 5 + [98.0] * 30  # -2%
    frame = _frame(closes)
    md = "**Rating**: Overweight\n\nbullish"
    out_md, ann = maybe_suppress_bull_rating(
        md,
        "WFC",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="active",
        sector_lookup=_make_lookup("Financial Services"),
        etf_history_fetcher=_make_fetcher(frame),
    )
    assert ann["would_fire"] is False
    assert ann["fired"] is False
    assert ann["pre_rating"] == ann["post_rating"] == "Overweight"
    assert out_md == md


@pytest.mark.unit
def test_strict_less_than_boundary():
    """ETF return EXACTLY equal to threshold MUST NOT fire (strict less-than per R-3)."""
    # Engineer exact -5% return: 100 → 95
    closes = [100.0] * 5 + [95.0] * 30
    frame = _frame(closes)
    md = "**Rating**: Overweight\n\nbullish"
    out_md, ann = maybe_suppress_bull_rating(
        md,
        "WFC",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="active",
        sector_lookup=_make_lookup("Financial Services"),
        etf_history_fetcher=_make_fetcher(frame),
    )
    # Return is exactly -5%, which is NOT < -5% → must not fire
    assert ann["etf_30d_return_pct"] == pytest.approx(-5.0, abs=0.001)
    assert ann["would_fire"] is False
    assert ann["fired"] is False
    assert out_md == md


# -- Defensive paths --------------------------------------------------------


@pytest.mark.unit
def test_yfinance_fetch_raises_skipped(caplog):
    """yfinance fetch raising → caught + skipped='missing_etf_data'."""

    def raising_fetcher(_etf, _start, _end):
        raise RuntimeError("network down")

    md = "**Rating**: Overweight\n\nbullish"
    with caplog.at_level("WARNING"):
        # Use the default _etf_history wrapping; manually inject raising fetcher
        out_md, ann = maybe_suppress_bull_rating(
            md,
            "WFC",
            "2026-04-03",
            threshold_pct=-5.0,
            mode="active",
            sector_lookup=_make_lookup("Financial Services"),
            etf_history_fetcher=lambda *a, **k: pd.DataFrame(),  # simulates the LRU empty result
        )
    assert ann["skipped"] == "missing_etf_data"


@pytest.mark.unit
def test_decision_markdown_no_rating_line_defensive():
    """Markdown without a parseable rating line → defaults to 'Hold' → skipped='rating_not_bullish'."""
    md = "Just some prose, no rating line here."
    out_md, ann = maybe_suppress_bull_rating(
        md,
        "WFC",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="active",
        sector_lookup=_make_lookup("Financial Services"),
        etf_history_fetcher=_make_fetcher(_frame([100.0] * 35)),
    )
    assert ann["pre_rating"] == "Hold"
    assert ann["skipped"] == "rating_not_bullish"
    assert out_md == md


@pytest.mark.unit
def test_invalid_mode_falls_back_to_off(caplog):
    """Unknown mode value → defaults to 'off' with logged warning."""
    md = "**Rating**: Overweight\n\nbullish"
    with caplog.at_level("WARNING"):
        out_md, ann = maybe_suppress_bull_rating(
            md,
            "WFC",
            "2026-04-03",
            threshold_pct=-5.0,
            mode="bogus",  # type: ignore[arg-type]
            sector_lookup=_make_lookup("Financial Services"),
        )
    assert ann["mode"] == "off"
    assert ann["skipped"] == "off"
    assert any("unknown mode" in m.lower() for m in caplog.messages)


@pytest.mark.unit
def test_lru_cache_amortizes_repeated_etf_fetches():
    """Repeated _etf_history calls with same args hit the LRU cache."""
    fetch_calls = []

    def counting_yf_history(start=None, end=None):
        fetch_calls.append((start, end))
        return _frame([100.0] * 35, start=start or "2026-03-01")

    with patch("tradingagents.agents.utils.sector_momentum_filter.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.history = counting_yf_history
        from tradingagents.agents.utils.sector_momentum_filter import _etf_history

        _etf_history("XLF", "2026-03-01", "2026-04-03")
        _etf_history("XLF", "2026-03-01", "2026-04-03")
        _etf_history("XLF", "2026-03-01", "2026-04-03")
    # Only one underlying fetch despite three calls
    assert len(fetch_calls) == 1


# -- SECTOR_ETF_MAP coverage ------------------------------------------------


@pytest.mark.unit
def test_sector_etf_map_covers_11_sectors():
    """All 11 GICS sectors + variant keys map to the right SPDR ETFs."""
    expected = {"XLK", "XLF", "XLV", "XLE", "XLY", "XLP", "XLI", "XLC", "XLU", "XLRE", "XLB"}
    assert set(SECTOR_ETF_MAP.values()) == expected
    # Variant aliases all map to the same ETF
    assert SECTOR_ETF_MAP["Financial Services"] == SECTOR_ETF_MAP["Financials"] == "XLF"
    assert SECTOR_ETF_MAP["Consumer Cyclical"] == SECTOR_ETF_MAP["Consumer Discretionary"] == "XLY"
    assert SECTOR_ETF_MAP["Consumer Defensive"] == SECTOR_ETF_MAP["Consumer Staples"] == "XLP"
    assert SECTOR_ETF_MAP["Basic Materials"] == SECTOR_ETF_MAP["Materials"] == "XLB"


# -- _compute_etf_30d_return_pct direct tests -------------------------------


@pytest.mark.unit
def test_compute_etf_return_insufficient_history():
    """Frame with < lookback+1 rows → returns None."""
    frame = _frame([100.0] * 10)  # only 10 rows; lookback=30 needs 31
    result = _compute_etf_30d_return_pct(
        "XLF", "2026-04-03", lookback_days=30, fetcher=_make_fetcher(frame)
    )
    assert result is None


@pytest.mark.unit
def test_compute_etf_return_invalid_trade_date():
    """Malformed trade_date → returns None with warning."""
    result = _compute_etf_30d_return_pct(
        "XLF", "not-a-date", fetcher=_make_fetcher(_frame([100.0] * 35))
    )
    assert result is None


# -- US2 audit annotation tests --------------------------------------------


@pytest.mark.unit
def test_annotation_active_fires_populates_all_fields():
    """All 11 fields present + populated when active-mode firing happens."""
    closes = [100.0] * 5 + [92.0] * 30
    md = "**Rating**: Overweight\n\nbullish"
    _, ann = maybe_suppress_bull_rating(
        md,
        "WFC",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="active",
        sector_lookup=_make_lookup("Financial Services"),
        etf_history_fetcher=_make_fetcher(_frame(closes)),
    )
    expected_keys = {
        "mode",
        "sector",
        "etf",
        "etf_30d_return_pct",
        "threshold_pct",
        "lookback_days",
        "would_fire",
        "fired",
        "pre_rating",
        "post_rating",
        "skipped",
    }
    assert set(ann.keys()) == expected_keys
    assert ann["mode"] == "active"
    assert ann["sector"] == "Financial Services"
    assert ann["etf"] == "XLF"
    assert ann["etf_30d_return_pct"] < -5.0
    assert ann["threshold_pct"] == -5.0
    assert ann["lookback_days"] == 30
    assert ann["would_fire"] is True
    assert ann["fired"] is True
    assert ann["pre_rating"] == "Overweight"
    assert ann["post_rating"] == "Hold"
    assert ann["skipped"] is None


@pytest.mark.unit
def test_annotation_invariants_per_data_model():
    """Spot-check the 9 invariants from data-model.md / annotation_schema.md."""
    # Invariant 1: skipped='off' → mode='off', no data fields
    _, ann = maybe_suppress_bull_rating(
        "**Rating**: Overweight",
        "WFC",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="off",
        sector_lookup=_make_lookup("Financial Services"),
    )
    assert ann["mode"] == "off" and ann["skipped"] == "off"
    assert ann["sector"] is None and ann["etf"] is None and ann["etf_30d_return_pct"] is None
    assert ann["would_fire"] is False and ann["fired"] is False
    assert ann["pre_rating"] == ann["post_rating"]

    # Invariant 5: skipped='rating_not_bullish' → pre_rating not bullish
    _, ann = maybe_suppress_bull_rating(
        "**Rating**: Hold",
        "WFC",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="active",
        sector_lookup=_make_lookup("Financial Services"),
    )
    assert ann["skipped"] == "rating_not_bullish"
    assert ann["pre_rating"] == "Hold"
    assert ann["would_fire"] is False

    # Invariant 7: skipped is None → all populated
    closes = [100.0] * 5 + [92.0] * 30
    _, ann = maybe_suppress_bull_rating(
        "**Rating**: Overweight",
        "WFC",
        "2026-04-03",
        threshold_pct=-5.0,
        mode="active",
        sector_lookup=_make_lookup("Financial Services"),
        etf_history_fetcher=_make_fetcher(_frame(closes)),
    )
    assert ann["skipped"] is None
    assert ann["sector"] is not None
    assert ann["etf"] is not None
    assert ann["etf_30d_return_pct"] is not None
    assert ann["threshold_pct"] is not None

    # Invariant 8: fired=True ⇒ would_fire=True AND mode='active' AND post='Hold'
    assert ann["fired"] is True
    assert ann["would_fire"] is True
    assert ann["mode"] == "active"
    assert ann["post_rating"] == "Hold"


@pytest.mark.unit
def test_audit_corpus_filter_by_fired():
    """Build 6 synthetic annotations + filter by fired."""
    annotations = []
    closes_down = [100.0] * 5 + [92.0] * 30
    closes_flat = [100.0] * 35

    for setup in [
        ("active", closes_down, "Overweight"),  # fired
        ("active", closes_down, "Overweight"),  # fired
        ("shadow", closes_down, "Overweight"),  # would_fire only
        ("shadow", closes_down, "Overweight"),  # would_fire only
        ("active", closes_flat, "Overweight"),  # not-fire
        ("active", closes_flat, "Overweight"),  # not-fire
    ]:
        mode, closes, rating = setup
        _, ann = maybe_suppress_bull_rating(
            f"**Rating**: {rating}",
            "X",
            "2026-04-03",
            threshold_pct=-5.0,
            mode=mode,
            sector_lookup=_make_lookup("Financial Services"),
            etf_history_fetcher=_make_fetcher(_frame(closes)),
        )
        annotations.append(ann)

    fired = [a for a in annotations if a["fired"]]
    would_fire = [a for a in annotations if a["would_fire"] and not a["fired"]]
    none = [a for a in annotations if not a["would_fire"]]
    assert len(fired) == 2
    assert len(would_fire) == 2
    assert len(none) == 2
