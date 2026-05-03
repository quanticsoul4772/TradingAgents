from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor

@tool
def get_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 30,
) -> str:
    """
    Retrieve a single technical indicator for a given ticker symbol.
    Uses the configured technical_indicators vendor.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        indicator (str): A single technical indicator name, e.g. 'rsi', 'macd'. Call this tool once per indicator.
        curr_date (str): The current trading date you are trading on, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 30
    Returns:
        str: A formatted dataframe containing the technical indicators for the specified ticker symbol and indicator.
    """
    # LLMs sometimes pass multiple indicators as a comma-separated string;
    # split and process each individually.
    indicators = [i.strip().lower() for i in indicator.split(",") if i.strip()]
    results = []
    for ind in indicators:
        try:
            results.append(route_to_vendor("get_indicators", symbol, ind, curr_date, look_back_days))
        except ValueError as e:
            results.append(str(e))
    return "\n\n".join(results)


@tool
def get_options_summary(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Options-derived signals for the nearest expiry: put/call open-interest
    ratio, mean implied volatility (calls + puts), IV skew (puts - calls),
    max-OI strike (rough max-pain proxy). Compact summary, not full chain.

    Returns:
        str: Formatted options summary
    """
    return route_to_vendor("get_options_summary", ticker)


@tool
def get_vix(
    curr_date: Annotated[str, "current date in yyyy-mm-dd format"],
    lookback_days: Annotated[int, "Trading days to compute VIX change"] = 30,
) -> str:
    """
    Current VIX (CBOE Volatility Index) level + N-day change + regime
    classification (fear / elevated / neutral / complacency). Used as the
    macro regime context — combine with ticker-specific signals to
    distinguish stock-specific drawdowns from broad-market panic.

    Returns:
        str: VIX summary with regime label
    """
    return route_to_vendor("get_vix", curr_date, lookback_days)


@tool
def get_sector_etf_strength(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date in yyyy-mm-dd format"],
    lookback_days: Annotated[int, "Trading days to compute relative strength"] = 30,
) -> str:
    """
    Ticker performance relative to its sector's SPDR ETF (XLK / XLE /
    XLF / etc.) over the trailing N days. Distinguishes stock-specific
    moves from sector-wide moves — directly addresses the Q4 finding
    that bear-side anti-calibration concentrates on bull-regime sectors.

    Returns:
        str: Relative strength summary with interpretation
    """
    return route_to_vendor("get_sector_etf_strength", ticker, curr_date, lookback_days)