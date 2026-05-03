# SIGNALS — what the framework consumes + what it could

_Inventory of data signals fed to the analyst layer + suggested additions._
_Last updated 2026-05-03 (after experiments 001-007 + signal expansion commit)._

> **2026-05-03 update**: All 10 yfinance fields-available-but-unused + the 5 P1 priority additions have been wired in. Section "Available but unused" is now historical reference; section "Most useful additions" is now historical. The "Currently consumed" section reflects the expanded signal set.

This doc tracks the inputs to the framework's decision pipeline. Updated when new tools are added or when an analyst's input mix changes. For routing logic see `tradingagents/dataflows/interface.py`; for tool definitions see `tradingagents/agents/utils/*_tools.py`.

---

## Currently consumed

### Market Analyst

| Tool | Vendor | Fields / shape | Status |
|---|---|---|---|
| `get_stock_data` | yfinance | OHLCV daily, ranged | ✅ active |
| `get_indicators` | yfinance via stockstats | 11 TA indicators: close_50_sma, close_200_sma, close_10_ema, macd, macds (signal), macdh (histogram), rsi, boll (middle), boll_ub (upper), boll_lb (lower), atr, vwma | ✅ active |
| `get_vix` | yfinance (^VIX) | VIX level + N-day change + regime classifier (fear/elevated/neutral/complacency) | ✅ added 2026-05-03 |
| `get_sector_etf_strength` | yfinance (XLK/XLE/etc.) | Ticker return vs sector ETF return over trailing N days | ✅ added 2026-05-03 |
| `get_options_summary` | yfinance | Put/call OI ratio, mean IV (calls + puts), IV skew, max-OI strike | ✅ added 2026-05-03 |

### News Analyst

| Tool | Vendor | Fields / shape | Status |
|---|---|---|---|
| `get_news` | **exa** | ticker-specific news with `startPublishedDate` / `endPublishedDate` filter; full article text via `contents.text.maxCharacters=2000` | ✅ active (replaced yfinance news 2026-05-03) |
| `get_global_news` | **exa** | macro/market news, date-windowed | ✅ active |
| `get_insider_transactions` | yfinance | insider buys/sells per ticker | ✅ wired into News Analyst tool list 2026-05-03 (was previously available but unused) |

### Fundamentals Analyst

| Tool | Vendor | Fields / shape | Status |
|---|---|---|---|
| `get_fundamentals` | yfinance | 28 fields from `Ticker.info`: name, sector, industry, market cap, PE/forward PE/PEG, price-to-book, EPS/forward EPS, dividend yield, beta, 52w high/low, 50/200 day avg, revenue, gross profit, EBITDA, net income, profit/operating margins, ROE/ROA, debt-to-equity, current ratio, book value, FCF | ✅ active |
| `get_balance_sheet` | yfinance | quarterly (default) or annual balance sheet | ✅ active |
| `get_cashflow` | yfinance | quarterly cashflow statement | ✅ active |
| `get_income_statement` | yfinance | quarterly income statement | ✅ active |
| `get_recommendations` | yfinance | analyst rating history + recent upgrades/downgrades | ✅ added 2026-05-03 |
| `get_earnings_calendar` | yfinance | upcoming earnings dates + recent events | ✅ added 2026-05-03 |
| `get_short_interest` | yfinance (Ticker.info) | shortPercentOfFloat, shortRatio, sharesShort, heldPercentInsiders/Institutions | ✅ added 2026-05-03 |
| `get_institutional_holders` | yfinance | institutional + mutual fund holders | ✅ added 2026-05-03 |
| `get_corporate_actions` | yfinance | dividend + split history + ESG sustainability | ✅ added 2026-05-03 |

### Social Media Analyst

| Tool | Vendor | Fields / shape | Status |
|---|---|---|---|
| `get_news` | exa | (same news as News analyst — there is no actual sentiment source) | ❌ **degenerate** — analyst uses news as proxy for sentiment, produces redundant report |

**Sentiment-report field is empty in most state logs** because Social Media Analyst is typically excluded from `selected_analysts`. When included, it duplicates News analyst output.

---

## Available but unused (already in yfinance — no new vendor needed)

These exist in yfinance and could be wired in as new tools without external dependencies:

| Field | Likely value | Effort to wire |
|---|---|---|
| `Ticker.recommendations` | Analyst rating history + price targets — predictive at 1-3 month horizon (matches our 21d window) | Low (~30 min) |
| `Ticker.recommendations_summary` | Current consensus rating | Low |
| `Ticker.upgrades_downgrades` | Recent rating changes — highly predictive for short-term moves | Low |
| `Ticker.earnings_dates` / `calendar` | Upcoming earnings dates — knowing if earnings falls in the 21d window changes the prediction problem entirely | Low |
| `Ticker.option_chain(date)` | Put/call ratio, implied volatility, max pain | Medium (need to pick expiry) |
| `info["shortPercentOfFloat"]`, `shortRatio` | Short-interest pressure — squeeze potential | Low (already in `info` dict, just not in our render) |
| `info["heldPercentInsiders"]`, `heldPercentInstitutions` | Ownership concentration | Low |
| `Ticker.institutional_holders` | Institutional positioning + recent changes | Low |
| `Ticker.actions` | Dividend + split history | Low |
| `Ticker.sustainability` | ESG ratings | Low (probably not useful for our research) |

---

## Available with new vendor (would require new fetcher)

### Macro / regime signals

| Signal | Source | Why it'd help | Priority |
|---|---|---|---|
| VIX level + 30d change | yfinance ticker `^VIX` | Regime classifier; rising VIX during ticker drawdown = the exact mean-reversion-bull regime Q4 found UW commits failing in | **P1** |
| Sector ETF performance (XLK, XLE, etc.) | yfinance | Sector rotation context — Q4 showed bear-side anti-calibration concentrates on tickers in bull-regime sectors | **P1** |
| Treasury yields (10y, 2y, spread) | yfinance `^TNX`, `^TYX` | Macro backdrop — bond-stock correlation regime | **P2** |
| Dollar index (DXY) | yfinance `DX-Y.NYB` | International revenue exposure context | **P3** |
| Fed funds rate / FOMC calendar | FRED API | Pre/post-FOMC date awareness | **P3** |
| CPI / PCE prints + surprise vs consensus | FRED + ALFRED | Macro-shock proximity | **P3** |

### Sentiment / positioning

| Signal | Source | Why it'd help | Priority |
|---|---|---|---|
| AAII Sentiment Survey | Direct CSV from aaii.com (free) | Retail-investor sentiment — extreme readings are contrarian indicators | **P2** |
| CNN Fear & Greed Index | Scrape (no official API) | Composite sentiment — already tracked by professionals | **P2** |
| CBOE put/call ratio | CBOE direct | Market-wide hedging activity | **P3** |
| COT reports | CFTC weekly | Futures positioning by trader category — for index/commodity tickers | **P4** |
| Reddit / Twitter sentiment | Reddit API + Twitter API (paid) | Real social sentiment vs the current Social Media Analyst's degenerate "use news" approach | **P3** (if we want to actually use Social Media Analyst) |

### Earnings + analyst data

| Signal | Source | Why it'd help | Priority |
|---|---|---|---|
| Earnings surprise history | yfinance + Estimize | Pattern of beat-vs-miss informs whether next-quarter guidance is credible | **P2** |
| Earnings call transcript | Custom NLP on news vendor | Hedging intensity in call language — Opus may already capture this from news, but raw transcripts richer | **P3** |
| Analyst price target distribution | yfinance `recommendations` | Spread + median — wide spread signals analyst disagreement (similar to our framework's debate output) | **P1** |

---

## Most useful additions given current research findings

Anchored to specific findings from RESEARCH_FINDINGS.md:

1. **VIX level + 30d change** — directly addresses Q4's mean-reversion finding. The A3 filter currently uses ticker 30d momentum; adding VIX would let it distinguish stock-specific drawdowns (where mean reversion is plausible) from broad-market panic (where the bear thesis is more likely correct). **Build: 1-2h.**

2. **Sector ETF relative strength** (XLK for tech, XLE for energy, etc.) — Q4 showed UW failures concentrate on bull-regime tickers; sector context lets the framework distinguish stock-specific bear case from sector-wide selloff. **Build: 1-2h.**

3. **Earnings calendar awareness** — many of our analysis dates fall before/after earnings; the framework currently has no signal for this. A 21d window that includes earnings is fundamentally different from one that doesn't. Wiring `Ticker.earnings_dates` would let the news analyst weight upcoming-earnings differently than no-earnings windows. **Build: 30 min.**

4. **Analyst recommendations / upgrades-downgrades** — analyst consensus changes are predictive at the 1-3 month horizon, exactly our 21d window. Currently the framework reasons about analyst sentiment via news prose; raw consensus + recent changes would be lossless. **Build: 30 min.**

5. **Insider transactions actually wired into News Analyst tool list** — the tool exists (`get_insider_transactions`) but the analyst doesn't request it. One-line fix in `news_analyst.py`. **Build: 5 min.**

---

## Lower-priority / noise risk

These are tempting but probably add noise more than signal at our 21d horizon:

- ESG ratings — slow-moving, unlikely to predict 21d returns
- Mutual fund holders — quarterly cadence, lags
- Reddit / Twitter sentiment — high noise, low signal at our horizon (and expensive to wire properly)
- COT reports — most of our tickers are equities, not futures

---

## Connection to the BOTS_DESIGN architecture

The proposed bots refactor (per `docs/BOTS_DESIGN.md` + `.specify/specs/001-bots-architecture/spec.md`) replaces prose analyst reports with structured `Signal` objects. Each new data source above maps to additional fields the bots can populate:

```python
class Signal(BaseModel):
    bot_id: str
    direction: SignalDirection
    magnitude: float
    horizon_days: int
    key_facts: list[str]
    risks: list[str]
    abstain: bool
    # Future:
    macro_regime: str | None  # "risk_on" | "risk_off" | "transition"
    sector_relative_strength: float | None  # ticker / sector ETF return ratio
    earnings_in_window: bool | None
    analyst_consensus_delta: float | None  # change in consensus over last 30 days
```

The unified value function (the aggregator) can weight each Signal field independently, so adding a new data source = adding a new field + a weight, not refactoring downstream consumers.

---

## How to add a new signal source

1. Write the fetcher (`tradingagents/dataflows/<vendor>.py` or extend `y_finance.py` with the new method).
2. Add a `@tool`-decorated wrapper in the appropriate `tradingagents/agents/utils/<category>_tools.py`.
3. Register in `tradingagents/dataflows/interface.py` (`VENDOR_LIST` + `VENDOR_METHODS`).
4. Include in the analyst's `tools = [...]` list in `tradingagents/agents/analysts/<name>_analyst.py`.
5. Add unit tests under `tests/`.
6. Document the addition here.

For signals that fit the bots architecture, also extend the `Signal` schema and update `WEIGHTS` in the aggregator (per BOTS_DESIGN spec).

---

## Related artifacts

- `tradingagents/dataflows/interface.py` — vendor routing
- `tradingagents/agents/utils/*_tools.py` — tool definitions
- `tradingagents/agents/analysts/*_analyst.py` — what tools each analyst requests
- `RESEARCH_FINDINGS.md` — empirical findings motivating priorities
- `docs/BOTS_DESIGN.md` — architecture for incorporating new signals via Signal schema
- `.specify/specs/001-bots-architecture/spec.md` — formal spec
