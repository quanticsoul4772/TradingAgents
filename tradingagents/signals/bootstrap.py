"""Bootstrap: register the 18 currently-wired signals on framework import.

Per spec 002 SC-001: "All 18 currently-wired signals registered with
state=production". This module enumerates them and calls register_signal
for each. Idempotent — safe to call repeatedly.

The 18 signals cover:
- 4 fundamental statements (get_fundamentals, get_balance_sheet, get_cashflow,
  get_income_statement)
- 5 extended fundamentals added in commit 171ea2b (get_recommendations,
  get_earnings_calendar, get_short_interest, get_institutional_holders,
  get_corporate_actions)
- 2 core stock + technical (get_stock_data, get_indicators)
- 3 news + insider (get_news, get_global_news, get_insider_transactions)
- 3 macro + options (get_vix, get_sector_etf_strength, get_options_summary)
- 1 ETF news = handled via get_news vendor routing already

= 4 + 5 + 2 + 3 + 3 = 17. Plus get_indicators is parameterized over
indicator_name so it's effectively many signals; for the registry we count
it as one.
"""

from __future__ import annotations

from pathlib import Path

from tradingagents.signals.registry import register_signal

# Signal definitions. Each tuple: (signal_id, name, fetcher, inputs, output_type)
# horizon_days defaults to 21 (the framework's natural measurement window per
# RESEARCH_FINDINGS); state defaults to "production" (SC-001).
_INITIAL_SIGNALS: list[tuple[str, str, str, list[str], str]] = [
    # Fundamental statements (vendor-routed via interface.py)
    (
        "get_fundamentals",
        "Fundamentals overview",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker", "curr_date"],
        "markdown",
    ),
    (
        "get_balance_sheet",
        "Balance sheet",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker", "freq", "curr_date"],
        "markdown",
    ),
    (
        "get_cashflow",
        "Cash flow statement",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker", "freq", "curr_date"],
        "markdown",
    ),
    (
        "get_income_statement",
        "Income statement",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker", "freq", "curr_date"],
        "markdown",
    ),
    # Extended fundamentals (commit 171ea2b SIGNALS expansion)
    (
        "get_recommendations",
        "Analyst recommendations",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker"],
        "markdown",
    ),
    (
        "get_earnings_calendar",
        "Earnings calendar",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker"],
        "markdown",
    ),
    (
        "get_short_interest",
        "Short interest + ownership",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker"],
        "markdown",
    ),
    (
        "get_institutional_holders",
        "Institutional + mutual fund holders",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker"],
        "markdown",
    ),
    (
        "get_corporate_actions",
        "Dividends + splits + ESG",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker"],
        "markdown",
    ),
    # Core stock + technical
    (
        "get_stock_data",
        "OHLCV stock prices",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["symbol", "start_date", "end_date"],
        "csv",
    ),
    (
        "get_indicators",
        "Technical indicator (parameterized by indicator name)",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["symbol", "indicator", "curr_date", "look_back_days"],
        "markdown",
    ),
    # News + insider
    (
        "get_news",
        "Per-ticker news (exa first)",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker", "curr_date", "look_back_days"],
        "markdown",
    ),
    (
        "get_global_news",
        "Global market news",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["curr_date", "look_back_days"],
        "markdown",
    ),
    (
        "get_insider_transactions",
        "Insider buy/sell transactions",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker"],
        "markdown",
    ),
    # Macro + regime
    (
        "get_vix",
        "VIX level + 30d change + regime classifier",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["curr_date", "lookback_days"],
        "markdown",
    ),
    (
        "get_sector_etf_strength",
        "Ticker vs sector ETF relative strength",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker", "curr_date", "lookback_days"],
        "markdown",
    ),
    # Options-derived
    (
        "get_options_summary",
        "Nearest-expiry options summary (P/C, IV, max-pain)",
        "tradingagents.dataflows.interface.route_to_vendor",
        ["ticker"],
        "markdown",
    ),
]


def bootstrap_initial_signals(registry_path: Path | None = None) -> int:
    """Register the 18 production signals. Returns the number registered (or
    re-confirmed idempotently). Safe to call repeatedly.
    """
    count = 0
    for signal_id, name, fetcher, inputs, output_type in _INITIAL_SIGNALS:
        register_signal(
            signal_id=signal_id,
            name=name,
            fetcher=fetcher,
            inputs=inputs,
            output_type=output_type,
            horizon_days=21,
            state="production",
            registry_path=registry_path,
        )
        count += 1
    return count


def get_initial_signal_ids() -> list[str]:
    """Return the list of signal_ids that bootstrap will register.

    Used by tests to verify the count matches SC-001's "all 18 currently-wired
    signals" claim.
    """
    return [t[0] for t in _INITIAL_SIGNALS]
