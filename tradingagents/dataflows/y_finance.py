from datetime import datetime
from typing import Annotated

import pandas as pd
import yfinance as yf
from dateutil.relativedelta import relativedelta

from .stockstats_utils import (
    StockstatsUtils,
    filter_financials_by_date,
    load_ohlcv,
    yf_retry,
)


def get_YFin_data_online(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
):

    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")

    # Create ticker object
    ticker = yf.Ticker(symbol.upper())

    # Fetch historical data for the specified date range
    data = yf_retry(lambda: ticker.history(start=start_date, end=end_date))

    # Check if data is empty
    if data.empty:
        return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

    # Remove timezone info from index for cleaner output
    if data.index.tz is not None:
        data.index = data.index.tz_localize(None)

    # Round numerical values to 2 decimal places for cleaner display
    numeric_columns = ["Open", "High", "Low", "Close", "Adj Close"]
    for col in numeric_columns:
        if col in data.columns:
            data[col] = data[col].round(2)

    # Convert DataFrame to CSV string
    csv_string = data.to_csv()

    # Add header information
    header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(data)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string


def get_stock_stats_indicators_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:

    best_ind_params = {
        # Moving Averages
        "close_50_sma": (
            "50 SMA: A medium-term trend indicator. "
            "Usage: Identify trend direction and serve as dynamic support/resistance. "
            "Tips: It lags price; combine with faster indicators for timely signals."
        ),
        "close_200_sma": (
            "200 SMA: A long-term trend benchmark. "
            "Usage: Confirm overall market trend and identify golden/death cross setups. "
            "Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries."
        ),
        "close_10_ema": (
            "10 EMA: A responsive short-term average. "
            "Usage: Capture quick shifts in momentum and potential entry points. "
            "Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals."
        ),
        # MACD Related
        "macd": (
            "MACD: Computes momentum via differences of EMAs. "
            "Usage: Look for crossovers and divergence as signals of trend changes. "
            "Tips: Confirm with other indicators in low-volatility or sideways markets."
        ),
        "macds": (
            "MACD Signal: An EMA smoothing of the MACD line. "
            "Usage: Use crossovers with the MACD line to trigger trades. "
            "Tips: Should be part of a broader strategy to avoid false positives."
        ),
        "macdh": (
            "MACD Histogram: Shows the gap between the MACD line and its signal. "
            "Usage: Visualize momentum strength and spot divergence early. "
            "Tips: Can be volatile; complement with additional filters in fast-moving markets."
        ),
        # Momentum Indicators
        "rsi": (
            "RSI: Measures momentum to flag overbought/oversold conditions. "
            "Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. "
            "Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis."
        ),
        # Volatility Indicators
        "boll": (
            "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. "
            "Usage: Acts as a dynamic benchmark for price movement. "
            "Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals."
        ),
        "boll_ub": (
            "Bollinger Upper Band: Typically 2 standard deviations above the middle line. "
            "Usage: Signals potential overbought conditions and breakout zones. "
            "Tips: Confirm signals with other tools; prices may ride the band in strong trends."
        ),
        "boll_lb": (
            "Bollinger Lower Band: Typically 2 standard deviations below the middle line. "
            "Usage: Indicates potential oversold conditions. "
            "Tips: Use additional analysis to avoid false reversal signals."
        ),
        "atr": (
            "ATR: Averages true range to measure volatility. "
            "Usage: Set stop-loss levels and adjust position sizes based on current market volatility. "
            "Tips: It's a reactive measure, so use it as part of a broader risk management strategy."
        ),
        # Volume-Based Indicators
        "vwma": (
            "VWMA: A moving average weighted by volume. "
            "Usage: Confirm trends by integrating price action with volume data. "
            "Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses."
        ),
        "mfi": (
            "MFI: The Money Flow Index is a momentum indicator that uses both price and volume to measure buying and selling pressure. "
            "Usage: Identify overbought (>80) or oversold (<20) conditions and confirm the strength of trends or reversals. "
            "Tips: Use alongside RSI or MACD to confirm signals; divergence between price and MFI can indicate potential reversals."
        ),
    }

    if indicator not in best_ind_params:
        raise ValueError(
            f"Indicator {indicator} is not supported. Please choose from: {list(best_ind_params.keys())}"
        )

    end_date = curr_date
    curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    before = curr_date_dt - relativedelta(days=look_back_days)

    # Optimized: Get stock data once and calculate indicators for all dates
    try:
        indicator_data = _get_stock_stats_bulk(symbol, indicator, curr_date)

        # Generate the date range we need
        current_dt = curr_date_dt
        date_values = []

        while current_dt >= before:
            date_str = current_dt.strftime("%Y-%m-%d")

            # Look up the indicator value for this date
            if date_str in indicator_data:
                indicator_value = indicator_data[date_str]
            else:
                indicator_value = "N/A: Not a trading day (weekend or holiday)"

            date_values.append((date_str, indicator_value))
            current_dt = current_dt - relativedelta(days=1)

        # Build the result string
        ind_string = ""
        for date_str, value in date_values:
            ind_string += f"{date_str}: {value}\n"

    except Exception as e:
        print(f"Error getting bulk stockstats data: {e}")
        # Fallback to original implementation if bulk method fails
        ind_string = ""
        curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        while curr_date_dt >= before:
            indicator_value = get_stockstats_indicator(
                symbol, indicator, curr_date_dt.strftime("%Y-%m-%d")
            )
            ind_string += f"{curr_date_dt.strftime('%Y-%m-%d')}: {indicator_value}\n"
            curr_date_dt = curr_date_dt - relativedelta(days=1)

    result_str = (
        f"## {indicator} values from {before.strftime('%Y-%m-%d')} to {end_date}:\n\n"
        + ind_string
        + "\n\n"
        + best_ind_params.get(indicator, "No description available.")
    )

    return result_str


def _get_stock_stats_bulk(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to calculate"],
    curr_date: Annotated[str, "current date for reference"],
) -> dict:
    """
    Optimized bulk calculation of stock stats indicators.
    Fetches data once and calculates indicator for all available dates.
    Returns dict mapping date strings to indicator values.
    """
    from stockstats import wrap

    data = load_ohlcv(symbol, curr_date)
    df = wrap(data)
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Calculate the indicator for all rows at once
    df[indicator]  # This triggers stockstats to calculate the indicator

    # Create a dictionary mapping date strings to indicator values
    result_dict = {}
    for _, row in df.iterrows():
        date_str = row["Date"]
        indicator_value = row[indicator]

        # Handle NaN/None values
        if pd.isna(indicator_value):
            result_dict[date_str] = "N/A"
        else:
            result_dict[date_str] = str(indicator_value)

    return result_dict


def get_stockstats_indicator(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
) -> str:

    curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    curr_date = curr_date_dt.strftime("%Y-%m-%d")

    try:
        indicator_value = StockstatsUtils.get_stock_stats(
            symbol,
            indicator,
            curr_date,
        )
    except Exception as e:
        print(
            f"Error getting stockstats indicator data for indicator {indicator} on {curr_date}: {e}"
        )
        return ""

    return str(indicator_value)


def get_fundamentals(
    ticker: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "current date (not used for yfinance)"] = None,
):
    """Get company fundamentals overview from yfinance."""
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        info = yf_retry(lambda: ticker_obj.info)

        if not info:
            return f"No fundamentals data found for symbol '{ticker}'"

        fields = [
            ("Name", info.get("longName")),
            ("Sector", info.get("sector")),
            ("Industry", info.get("industry")),
            ("Market Cap", info.get("marketCap")),
            ("PE Ratio (TTM)", info.get("trailingPE")),
            ("Forward PE", info.get("forwardPE")),
            ("PEG Ratio", info.get("pegRatio")),
            ("Price to Book", info.get("priceToBook")),
            ("EPS (TTM)", info.get("trailingEps")),
            ("Forward EPS", info.get("forwardEps")),
            ("Dividend Yield", info.get("dividendYield")),
            ("Beta", info.get("beta")),
            ("52 Week High", info.get("fiftyTwoWeekHigh")),
            ("52 Week Low", info.get("fiftyTwoWeekLow")),
            ("50 Day Average", info.get("fiftyDayAverage")),
            ("200 Day Average", info.get("twoHundredDayAverage")),
            ("Revenue (TTM)", info.get("totalRevenue")),
            ("Gross Profit", info.get("grossProfits")),
            ("EBITDA", info.get("ebitda")),
            ("Net Income", info.get("netIncomeToCommon")),
            ("Profit Margin", info.get("profitMargins")),
            ("Operating Margin", info.get("operatingMargins")),
            ("Return on Equity", info.get("returnOnEquity")),
            ("Return on Assets", info.get("returnOnAssets")),
            ("Debt to Equity", info.get("debtToEquity")),
            ("Current Ratio", info.get("currentRatio")),
            ("Book Value", info.get("bookValue")),
            ("Free Cash Flow", info.get("freeCashflow")),
        ]

        lines = []
        for label, value in fields:
            if value is not None:
                lines.append(f"{label}: {value}")

        header = f"# Company Fundamentals for {ticker.upper()}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + "\n".join(lines)

    except Exception as e:
        return f"Error retrieving fundamentals for {ticker}: {str(e)}"


def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
):
    """Get balance sheet data from yfinance."""
    try:
        ticker_obj = yf.Ticker(ticker.upper())

        if freq.lower() == "quarterly":
            data = yf_retry(lambda: ticker_obj.quarterly_balance_sheet)
        else:
            data = yf_retry(lambda: ticker_obj.balance_sheet)

        data = filter_financials_by_date(data, curr_date)

        if data.empty:
            return f"No balance sheet data found for symbol '{ticker}'"

        # Convert to CSV string for consistency with other functions
        csv_string = data.to_csv()

        # Add header information
        header = f"# Balance Sheet data for {ticker.upper()} ({freq})\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error retrieving balance sheet for {ticker}: {str(e)}"


def get_cashflow(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
):
    """Get cash flow data from yfinance."""
    try:
        ticker_obj = yf.Ticker(ticker.upper())

        if freq.lower() == "quarterly":
            data = yf_retry(lambda: ticker_obj.quarterly_cashflow)
        else:
            data = yf_retry(lambda: ticker_obj.cashflow)

        data = filter_financials_by_date(data, curr_date)

        if data.empty:
            return f"No cash flow data found for symbol '{ticker}'"

        # Convert to CSV string for consistency with other functions
        csv_string = data.to_csv()

        # Add header information
        header = f"# Cash Flow data for {ticker.upper()} ({freq})\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error retrieving cash flow for {ticker}: {str(e)}"


def get_income_statement(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
):
    """Get income statement data from yfinance."""
    try:
        ticker_obj = yf.Ticker(ticker.upper())

        if freq.lower() == "quarterly":
            data = yf_retry(lambda: ticker_obj.quarterly_income_stmt)
        else:
            data = yf_retry(lambda: ticker_obj.income_stmt)

        data = filter_financials_by_date(data, curr_date)

        if data.empty:
            return f"No income statement data found for symbol '{ticker}'"

        # Convert to CSV string for consistency with other functions
        csv_string = data.to_csv()

        # Add header information
        header = f"# Income Statement data for {ticker.upper()} ({freq})\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error retrieving income statement for {ticker}: {str(e)}"


def get_insider_transactions(ticker: Annotated[str, "ticker symbol of the company"]):
    """Get insider transactions data from yfinance."""
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        data = yf_retry(lambda: ticker_obj.insider_transactions)

        if data is None or data.empty:
            return f"No insider transactions data found for symbol '{ticker}'"

        # Convert to CSV string for consistency with other functions
        csv_string = data.to_csv()

        # Add header information
        header = f"# Insider Transactions data for {ticker.upper()}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error retrieving insider transactions for {ticker}: {str(e)}"


# -------------------------------------------------------------------------
# Extended yfinance signals (added 2026-05-03 per docs/SIGNALS.md)
# -------------------------------------------------------------------------


def get_recommendations(
    ticker: Annotated[str, "ticker symbol of the company"],
):
    """Wall Street analyst rating history + recent upgrades/downgrades.

    Returns up to 3 sections: current consensus (recommendations_summary),
    rating history (recommendations), recent rating changes (upgrades_downgrades).
    Highly predictive at the 1-3 month horizon — matches the framework's
    21d measurement window per RESEARCH_FINDINGS Q3.
    """
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        sections = []

        # Current consensus + raw history
        recs = yf_retry(lambda: ticker_obj.recommendations)
        if recs is not None and not recs.empty:
            sections.append("## Recommendations history\n\n" + recs.to_csv())

        # Recent upgrades/downgrades (different shape)
        try:
            upgrades = yf_retry(lambda: ticker_obj.upgrades_downgrades)
            if upgrades is not None and not upgrades.empty:
                sections.append("## Recent upgrades / downgrades\n\n" + upgrades.head(20).to_csv())
        except Exception:
            pass  # not all tickers expose upgrades_downgrades

        if not sections:
            return f"No analyst recommendations data found for symbol '{ticker}'"

        header = f"# Analyst Recommendations for {ticker.upper()}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        return header + "\n\n".join(sections)

    except Exception as e:
        return f"Error retrieving recommendations for {ticker}: {str(e)}"


def get_earnings_calendar(
    ticker: Annotated[str, "ticker symbol of the company"],
):
    """Upcoming earnings dates + earnings surprise history.

    Crucial for 21d-window analysis: a window that includes earnings is a
    fundamentally different prediction problem than one that doesn't.
    """
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        sections = []

        # Upcoming + recent earnings dates
        try:
            ed = yf_retry(lambda: ticker_obj.earnings_dates)
            if ed is not None and not ed.empty:
                sections.append("## Earnings dates (upcoming + recent)\n\n" + ed.to_csv())
        except Exception:
            pass

        # Calendar (next earnings + dividends)
        try:
            cal = yf_retry(lambda: ticker_obj.calendar)
            if cal:
                sections.append(f"## Calendar\n\n{cal}")
        except Exception:
            pass

        if not sections:
            return f"No earnings calendar data found for symbol '{ticker}'"

        header = f"# Earnings Calendar for {ticker.upper()}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        return header + "\n\n".join(sections)

    except Exception as e:
        return f"Error retrieving earnings calendar for {ticker}: {str(e)}"


def get_options_summary(
    ticker: Annotated[str, "ticker symbol of the company"],
):
    """Options-derived signals: put/call ratio, implied vol, max pain.

    Uses the nearest-expiry option chain. Heavy / volatile data — keeps
    summary compact rather than dumping full strike-by-strike chains.
    """
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        expiries = yf_retry(lambda: ticker_obj.options)
        if not expiries:
            return f"No options data found for symbol '{ticker}'"

        nearest = expiries[0]
        chain = yf_retry(lambda exp=nearest: ticker_obj.option_chain(exp))

        calls = chain.calls
        puts = chain.puts

        call_oi = calls["openInterest"].sum() if "openInterest" in calls else 0
        put_oi = puts["openInterest"].sum() if "openInterest" in puts else 0
        pc_ratio = (put_oi / call_oi) if call_oi else None

        call_iv = calls["impliedVolatility"].mean() if "impliedVolatility" in calls else None
        put_iv = puts["impliedVolatility"].mean() if "impliedVolatility" in puts else None

        # Max pain: strike where total open-interest pain (call+put combined) is minimized.
        # Approximation: strike with max combined OI is a rough proxy.
        combined_oi = calls.set_index("strike")["openInterest"].add(
            puts.set_index("strike")["openInterest"], fill_value=0
        )
        max_pain = combined_oi.idxmax() if not combined_oi.empty else None

        lines = [
            f"# Options Summary for {ticker.upper()} (expiry: {nearest})",
            f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Available expiries: {', '.join(expiries[:5])}{' …' if len(expiries) > 5 else ''}",
            f"Total open interest — calls: {int(call_oi):,}, puts: {int(put_oi):,}",
            f"Put/call open interest ratio: {pc_ratio:.3f}"
            if pc_ratio is not None
            else "Put/call ratio: n/a",
            f"Mean implied vol — calls: {call_iv:.3f}" if call_iv is not None else "Call IV: n/a",
            f"Mean implied vol — puts:  {put_iv:.3f}" if put_iv is not None else "Put IV:  n/a",
            f"IV skew (puts - calls): {(put_iv - call_iv):.3f}"
            if (put_iv is not None and call_iv is not None)
            else "IV skew: n/a",
            f"Max-OI strike (rough max-pain proxy): {max_pain}" if max_pain else "",
        ]
        return "\n".join(line for line in lines if line)

    except Exception as e:
        return f"Error retrieving options summary for {ticker}: {str(e)}"


def get_short_interest(
    ticker: Annotated[str, "ticker symbol of the company"],
):
    """Short-interest pressure + ownership concentration signals.

    All sourced from yfinance Ticker.info dict. Squeeze-potential indicator
    when high short interest + bull catalyst converge; ownership
    concentration informs liquidity / volatility expectation.

    Short-circuits on known sector ETFs (XLK / XLE / XLF / etc.) — yfinance
    Ticker.info 404s on ETFs (no fundamentals) and short-interest data
    is meaningless for index funds anyway. Same pattern as
    get_sector_etf_strength in dataflows/macro.py.
    """
    # Lazy import to avoid load-order coupling with macro.py
    from tradingagents.dataflows.macro import SECTOR_ETF

    ticker_upper = ticker.upper()
    if ticker_upper in set(SECTOR_ETF.values()):
        return (
            f"'{ticker_upper}' is a sector ETF; short-interest / ownership "
            f"signals are not meaningful for index funds (and yfinance lacks "
            f"the data). Use this on individual equities only."
        )

    try:
        ticker_obj = yf.Ticker(ticker_upper)
        info = yf_retry(lambda: ticker_obj.info)
        if not info:
            return f"No short interest / ownership data found for symbol '{ticker}'"

        fields = [
            ("Short Percent of Float", info.get("shortPercentOfFloat")),
            ("Short Ratio (days to cover)", info.get("shortRatio")),
            ("Shares Short", info.get("sharesShort")),
            ("Shares Short Prior Month", info.get("sharesShortPriorMonth")),
            ("Date Short Interest Reported", info.get("dateShortInterest")),
            ("Held Percent Insiders", info.get("heldPercentInsiders")),
            ("Held Percent Institutions", info.get("heldPercentInstitutions")),
            ("Float Shares", info.get("floatShares")),
            ("Implied Shares Outstanding", info.get("impliedSharesOutstanding")),
        ]
        lines = [f"{label}: {value}" for label, value in fields if value is not None]
        if not lines:
            return f"No short interest / ownership fields populated for '{ticker}'"

        header = f"# Short Interest + Ownership for {ticker.upper()}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        return header + "\n".join(lines)

    except Exception as e:
        return f"Error retrieving short interest for {ticker}: {str(e)}"


def get_institutional_holders(
    ticker: Annotated[str, "ticker symbol of the company"],
):
    """Top institutional + mutual-fund holders for a ticker."""
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        sections = []

        try:
            inst = yf_retry(lambda: ticker_obj.institutional_holders)
            if inst is not None and not inst.empty:
                sections.append("## Institutional holders\n\n" + inst.to_csv())
        except Exception:
            pass

        try:
            mf = yf_retry(lambda: ticker_obj.mutualfund_holders)
            if mf is not None and not mf.empty:
                sections.append("## Mutual fund holders\n\n" + mf.to_csv())
        except Exception:
            pass

        if not sections:
            return f"No institutional holders data found for symbol '{ticker}'"

        header = f"# Institutional + Mutual Fund Holders for {ticker.upper()}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        return header + "\n\n".join(sections)

    except Exception as e:
        return f"Error retrieving institutional holders for {ticker}: {str(e)}"


def get_corporate_actions(
    ticker: Annotated[str, "ticker symbol of the company"],
):
    """Dividend + split history + ESG ratings.

    Corporate actions (dividends/splits) are useful context for
    understanding price-history discontinuities. ESG ratings are included
    because they're cheap to fetch alongside, even though their
    predictive value at our 21d horizon is likely low.
    """
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        sections = []

        try:
            actions = yf_retry(lambda: ticker_obj.actions)
            if actions is not None and not actions.empty:
                sections.append(
                    "## Dividends + splits history (last 20 events)\n\n" + actions.tail(20).to_csv()
                )
        except Exception:
            pass

        try:
            esg = yf_retry(lambda: ticker_obj.sustainability)
            if esg is not None and not esg.empty:
                sections.append("## ESG sustainability ratings\n\n" + esg.to_csv())
        except Exception:
            pass

        if not sections:
            return f"No corporate actions / ESG data found for symbol '{ticker}'"

        header = f"# Corporate Actions + ESG for {ticker.upper()}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        return header + "\n\n".join(sections)

    except Exception as e:
        return f"Error retrieving corporate actions for {ticker}: {str(e)}"
