from typing import Annotated

from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_fundamentals(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
) -> str:
    """
    Retrieve comprehensive fundamental data for a given ticker symbol.
    Uses the configured fundamental_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing comprehensive fundamental data
    """
    return route_to_vendor("get_fundamentals", ticker, curr_date)


@tool
def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"] = None,
) -> str:
    """
    Retrieve balance sheet data for a given ticker symbol.
    Uses the configured fundamental_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        freq (str): Reporting frequency: annual/quarterly (default quarterly)
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing balance sheet data
    """
    return route_to_vendor("get_balance_sheet", ticker, freq, curr_date)


@tool
def get_cashflow(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"] = None,
) -> str:
    """
    Retrieve cash flow statement data for a given ticker symbol.
    Uses the configured fundamental_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        freq (str): Reporting frequency: annual/quarterly (default quarterly)
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing cash flow statement data
    """
    return route_to_vendor("get_cashflow", ticker, freq, curr_date)


@tool
def get_income_statement(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"] = None,
) -> str:
    """
    Retrieve income statement data for a given ticker symbol.
    Uses the configured fundamental_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        freq (str): Reporting frequency: annual/quarterly (default quarterly)
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing income statement data
    """
    return route_to_vendor("get_income_statement", ticker, freq, curr_date)


@tool
def get_recommendations(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve Wall Street analyst recommendations history + recent rating
    changes for a ticker. Predictive at the 1-3 month horizon (matches
    framework's 21d measurement window). Includes:
    - Current consensus
    - Rating history
    - Recent upgrades / downgrades

    Returns:
        str: Formatted report of analyst recommendations
    """
    return route_to_vendor("get_recommendations", ticker)


@tool
def get_earnings_calendar(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve upcoming earnings dates + recent earnings event timeline for
    a ticker. Critical for 21d-window analysis: a window that includes
    earnings is a fundamentally different prediction problem than one
    that doesn't.

    Returns:
        str: Formatted earnings calendar
    """
    return route_to_vendor("get_earnings_calendar", ticker)


@tool
def get_short_interest(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve short-interest pressure (shortPercentOfFloat, shortRatio,
    shares short, days to cover) + ownership concentration (insider %,
    institutional %, float shares) for a ticker. Useful for squeeze-
    potential analysis when high short interest + bull catalyst converge.

    Returns:
        str: Formatted short interest + ownership summary
    """
    return route_to_vendor("get_short_interest", ticker)


@tool
def get_institutional_holders(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve top institutional + mutual-fund holders for a ticker.
    Concentration shifts inform liquidity / volatility expectation.

    Returns:
        str: Formatted institutional holders report
    """
    return route_to_vendor("get_institutional_holders", ticker)


@tool
def get_corporate_actions(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve dividend + split history + ESG sustainability ratings.
    Corporate actions inform price-history discontinuities; ESG is
    bundled (cheap to fetch alongside, predictive value at 21d unclear).

    Returns:
        str: Formatted corporate actions + ESG report
    """
    return route_to_vendor("get_corporate_actions", ticker)
