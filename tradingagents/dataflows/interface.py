# Import from vendor-specific modules
from .alpha_vantage import (
    get_balance_sheet as get_alpha_vantage_balance_sheet,
)
from .alpha_vantage import (
    get_cashflow as get_alpha_vantage_cashflow,
)
from .alpha_vantage import (
    get_fundamentals as get_alpha_vantage_fundamentals,
)
from .alpha_vantage import (
    get_global_news as get_alpha_vantage_global_news,
)
from .alpha_vantage import (
    get_income_statement as get_alpha_vantage_income_statement,
)
from .alpha_vantage import (
    get_indicator as get_alpha_vantage_indicator,
)
from .alpha_vantage import (
    get_insider_transactions as get_alpha_vantage_insider_transactions,
)
from .alpha_vantage import (
    get_news as get_alpha_vantage_news,
)
from .alpha_vantage import (
    get_stock as get_alpha_vantage_stock,
)
from .alpha_vantage_common import AlphaVantageRateLimitError

# Configuration and routing logic
from .config import get_config
from .exa_news import get_global_news_exa, get_news_exa
from .macro import get_sector_etf_strength as macro_sector_etf_strength
from .macro import get_vix as macro_vix
from .y_finance import (
    get_balance_sheet as get_yfinance_balance_sheet,
)
from .y_finance import (
    get_cashflow as get_yfinance_cashflow,
)
from .y_finance import (
    get_corporate_actions as get_yfinance_corporate_actions,
)
from .y_finance import (
    get_earnings_calendar as get_yfinance_earnings_calendar,
)
from .y_finance import (
    get_fundamentals as get_yfinance_fundamentals,
)
from .y_finance import (
    get_income_statement as get_yfinance_income_statement,
)
from .y_finance import (
    get_insider_transactions as get_yfinance_insider_transactions,
)
from .y_finance import (
    get_institutional_holders as get_yfinance_institutional_holders,
)
from .y_finance import (
    get_options_summary as get_yfinance_options_summary,
)
from .y_finance import (
    get_recommendations as get_yfinance_recommendations,
)
from .y_finance import (
    get_short_interest as get_yfinance_short_interest,
)
from .y_finance import (
    get_stock_stats_indicators_window,
    get_YFin_data_online,
)

# Tools organized by category
TOOLS_CATEGORIES = {
    "core_stock_apis": {"description": "OHLCV stock price data", "tools": ["get_stock_data"]},
    "technical_indicators": {
        "description": "Technical analysis indicators",
        "tools": ["get_indicators"],
    },
    "fundamental_data": {
        "description": "Company fundamentals",
        "tools": [
            "get_fundamentals",
            "get_balance_sheet",
            "get_cashflow",
            "get_income_statement",
            "get_recommendations",
            "get_earnings_calendar",
            "get_short_interest",
            "get_institutional_holders",
            "get_corporate_actions",
            # Insider transactions are conceptually fundamental data, not news.
            # Moved here from news_data so route_to_vendor falls back to the
            # fundamental_data category vendor (yfinance) instead of the
            # news_data vendor (exa, which has no impl for this tool).
            "get_insider_transactions",
        ],
    },
    "news_data": {
        "description": "News data",
        "tools": [
            "get_news",
            "get_global_news",
        ],
    },
    "macro_data": {
        "description": "Macro / regime signals (VIX, sector relative strength)",
        "tools": ["get_vix", "get_sector_etf_strength"],
    },
    "options_data": {
        "description": "Options-derived signals (IV, put/call, max pain)",
        "tools": ["get_options_summary"],
    },
}

VENDOR_LIST = [
    "yfinance",  # stock prices, technicals, fundamentals only (NOT news)
    "alpha_vantage",  # alternative for stock/technical/fundamentals/news
    "exa",  # ONLY supported news vendor (true historical date filter)
]

# Mapping of methods to their vendor-specific implementations
VENDOR_METHODS = {
    # core_stock_apis
    "get_stock_data": {
        "alpha_vantage": get_alpha_vantage_stock,
        "yfinance": get_YFin_data_online,
    },
    # technical_indicators
    "get_indicators": {
        "alpha_vantage": get_alpha_vantage_indicator,
        "yfinance": get_stock_stats_indicators_window,
    },
    # fundamental_data
    "get_fundamentals": {
        "alpha_vantage": get_alpha_vantage_fundamentals,
        "yfinance": get_yfinance_fundamentals,
    },
    "get_balance_sheet": {
        "alpha_vantage": get_alpha_vantage_balance_sheet,
        "yfinance": get_yfinance_balance_sheet,
    },
    "get_cashflow": {
        "alpha_vantage": get_alpha_vantage_cashflow,
        "yfinance": get_yfinance_cashflow,
    },
    "get_income_statement": {
        "alpha_vantage": get_alpha_vantage_income_statement,
        "yfinance": get_yfinance_income_statement,
    },
    # news_data — exa is the only first-party news vendor; alpha_vantage
    # remains as an alternative for users with that subscription
    "get_news": {
        "exa": get_news_exa,
        "alpha_vantage": get_alpha_vantage_news,
    },
    "get_global_news": {
        "exa": get_global_news_exa,
        "alpha_vantage": get_alpha_vantage_global_news,
    },
    "get_insider_transactions": {
        "yfinance": get_yfinance_insider_transactions,
        "alpha_vantage": get_alpha_vantage_insider_transactions,
    },
    # Extended yfinance signals (added 2026-05-03 per docs/SIGNALS.md)
    "get_recommendations": {"yfinance": get_yfinance_recommendations},
    "get_earnings_calendar": {"yfinance": get_yfinance_earnings_calendar},
    "get_options_summary": {"yfinance": get_yfinance_options_summary},
    "get_short_interest": {"yfinance": get_yfinance_short_interest},
    "get_institutional_holders": {"yfinance": get_yfinance_institutional_holders},
    "get_corporate_actions": {"yfinance": get_yfinance_corporate_actions},
    # Macro / regime signals
    "get_vix": {"yfinance": macro_vix},
    "get_sector_etf_strength": {"yfinance": macro_sector_etf_strength},
}


def get_category_for_method(method: str) -> str:
    """Get the category that contains the specified method."""
    for category, info in TOOLS_CATEGORIES.items():
        if method in info["tools"]:
            return category
    raise ValueError(f"Method '{method}' not found in any category")


def get_vendor(category: str, method: str | None = None) -> str:
    """Get the configured vendor for a data category or specific tool method.
    Tool-level configuration takes precedence over category-level.
    """
    config = get_config()

    # Check tool-level configuration first (if method provided)
    if method:
        tool_vendors = config.get("tool_vendors", {})
        if method in tool_vendors:
            return tool_vendors[method]

    # Fall back to category-level configuration
    return config.get("data_vendors", {}).get(category, "default")


def route_to_vendor(method: str, *args, **kwargs):
    """Route method calls to appropriate vendor implementation with fallback support.

    Phase 0 of spec 002: when a propagate context is set, every successful
    dispatch transparently writes the computed value to the signal cache
    keyed by the context's (ticker, trade_date). Tools called outside a
    propagate (unit tests, scripts) see no context and are not cached.
    Cache failures are logged-and-swallowed so they cannot break the pipeline.
    """
    category = get_category_for_method(method)
    vendor_config = get_vendor(category, method)
    primary_vendors = [v.strip() for v in vendor_config.split(",")]

    if method not in VENDOR_METHODS:
        raise ValueError(f"Method '{method}' not supported")

    # Build fallback chain: primary vendors first, then remaining available vendors
    all_available_vendors = list(VENDOR_METHODS[method].keys())
    fallback_vendors = primary_vendors.copy()
    for vendor in all_available_vendors:
        if vendor not in fallback_vendors:
            fallback_vendors.append(vendor)

    for vendor in fallback_vendors:
        if vendor not in VENDOR_METHODS[method]:
            continue

        vendor_impl = VENDOR_METHODS[method][vendor]
        impl_func = vendor_impl[0] if isinstance(vendor_impl, list) else vendor_impl

        try:
            result = impl_func(*args, **kwargs)
        except AlphaVantageRateLimitError:
            continue  # Only rate limits trigger fallback

        # Phase 0 cache hook: write to cache when a propagate context is set.
        # Lazy import + isolated try/except so cache I/O never breaks dispatch.
        try:
            from tradingagents.signals.cache import record_value
            from tradingagents.signals.context import get_propagate_context

            ctx = get_propagate_context()
            if ctx is not None:
                record_value(
                    signal_id=method,
                    ticker=ctx["ticker"],
                    date=ctx["trade_date"],
                    value=result,
                )
        except Exception:  # noqa: BLE001 — cache writes must never break dispatch
            import logging

            logging.getLogger(__name__).debug(
                "signals.cache write failed for %s; dispatch continues", method
            )

        return result

    raise RuntimeError(f"No available vendor for '{method}'")
