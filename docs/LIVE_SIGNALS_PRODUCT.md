# Live Signals Product — Operator Runbook

> ⚠️ **Simulation only — not financial advice.** Per Constitution Principle IV, this is paper trading. No real capital. Past performance of simulated trades does not predict future results.

A daily, opinionated workflow that turns the multi-agent debate framework into a continuous live signal stream. Three components glued together:

1. `scripts/daily_signals.py` — signal generator (LLM-incurring)
2. `scripts/paper_trade.py` — signal consumer (paper portfolio; $0 LLM)
3. `scripts/run_daily.py` — orchestrator that runs both end-to-end

This doc is the entry point. For component-level detail see [`docs/PAPER_TRADING.md`](PAPER_TRADING.md) and [`docs/SIGNALS.md`](SIGNALS.md).

---

## What it does

Every business day:

1. Run the framework's `propagate(ticker, today)` over a 25-name watchlist (`data/watchlists/tech_weighted.txt`)
2. Write a markdown digest filtered to **actionable bullish 21d-horizon recommendations** (Hold suppressed by default per Constitution VII; pass `--include-all` to see Hold/UW/Sell)
3. Emit a `paper_trade.py`-consumable signals CSV
4. Apply signals to a persistent paper portfolio (default `live`, $100k starting equity, 21-day holding window, 8 max positions, 10% per slot, 50% per-sector cap, 5 bps slippage, SPY benchmark)
5. Print portfolio status (cash, open positions, equity curve)

State persists in `~/.tradingagents/paper/<portfolio_id>.{json,events.jsonl}` across runs. Re-running on the same date is idempotent.

## What it does NOT do

- **No real-money trading** — Constitution IV. Paper only.
- **No intra-day signals** — propagate is once-per-day.
- **No 5-day signals** — the framework is at the LLM single-call calibration ceiling at 5d horizons (CLAUDE.md headline). 21-day window is the default.
- **No bearish actionable recommendations by default** — UW commits are regime-asymmetric per the corpus (work on bear-correct tickers; fail on bull-regime tickers). UW signals are emitted to the CSV but the digest filters them out unless `--include-all`.
- **No automatic execution** — the digest is a recommendation; the operator decides what (if anything) to do with it.

## What we learned that shaped this product

The opinionated defaults are not arbitrary. They reflect the corpus evidence accumulated across 35 experiments:

| Default | Evidence source |
|---|---|
| 21-day holding window | Headline +1.23% mean α / 61% hit at 21d (n=71); 5d at coin-flip ceiling |
| Bullish-only digest by default | Bullish commits POSITIVE AT MODERATE CONFIDENCE; bearish commits regime-asymmetric (UW on bull-regime tickers anti-calibrated) |
| Hold suppression in digest | Constitution VII: Hold ≈ 0% mean α at every horizon; calibrated abstention, not actionable |
| Tech-weighted watchlist (~60%) | SC-003 50-ticker validation: Tech +17.80% mean α on bullish picks; Financials -7.07% — signal is structurally tech-concentrated |
| 50% per-sector cap | Limits damage if multiple Tech signals concentrate; mandatory diversifier |
| Filter portfolio default-ON: A3 + Spec 003 + Spec 003.5 | Each retrospective-validated at +0.65pp / +0.70pp Δα |
| Filter portfolio default-SHADOW: Spec 007 bear + Spec X-1 + Spec 012 | Small-sample-caution per Constitution VIII v1.4.0; need 30+ live fires before flip |

## Daily workflow

```bash
# One command — runs all 3 steps, prompts for cost confirmation
python scripts/run_daily.py

# Or skip the cost prompt for cron use
python scripts/run_daily.py --yes
```

The orchestrator:
- Resolves today (or last business day if weekend)
- Estimates cost: `~$0.40 × n_tickers` (Opus + Haiku per propagate)
- Runs `daily_signals.py` → writes `claudedocs/daily-signals-<date>.md` + `~/.tradingagents/paper/live-<date>-signals.csv`
- Runs `paper_trade.py step` → applies signals, persists state
- Runs `paper_trade.py status` → prints portfolio cash + positions + equity

### Common variations

```bash
# Different watchlist
python scripts/run_daily.py --tickers data/watchlists/your_list.txt

# Different portfolio (e.g., for ablation)
python scripts/run_daily.py --portfolio-id live-shadow

# Specific historical date (for replay)
python scripts/run_daily.py --date 2026-04-15

# Re-process today's CSV without re-running signals (free)
python scripts/run_daily.py --skip-signals
```

## Cost

Default 25-ticker watchlist: **~$10/day** (Opus + Haiku × 25). Smaller watchlists scale linearly. Step 2 + 3 are $0.

Cron'd weekdays only: **~$200/month**.

## Reading the daily digest

Output at `claudedocs/daily-signals-<date>.md`. Sections:

- **Top of digest**: Buy + Overweight commits sorted by conviction. Each row: ticker / pre-rating (PM raw) / post-rating (after filter chain) / filter annotations / propagate latency / state-log path.
- **Filter audit**: when a filter fired (e.g., A3 momentum suppressed UW → Hold; Spec 003 contrarian gate downgraded OW → Hold). Filter annotations per `Constitution VIII` audit trail discipline.
- **Hold-default analysts**: tickers where the propagate landed at Hold pre-filter; suppressed unless `--include-all`.

## Reading the portfolio status

`paper_trade.py status` prints:

- Cash + open positions count + total equity
- Per-position: ticker / entry date / entry price / mark / Δ% vs entry / days held / α vs SPY
- Equity curve (last 5 entries)
- Recent events (last 10): entries / exits / skips with reason

To see the full event log: `~/.tradingagents/paper/<portfolio_id>.events.jsonl`.

## Validation against the corpus

The product reproduces the SC-003 50-ticker-bullish-bucket mean α within ±150 bps when replayed over the same dates ([SC-001 validation gate](../specs/002-paper-trading-harness/spec.md)). To verify:

```bash
python scripts/paper_trade.py replay \
    --signals-csv experiments/2026-05-05-003-signal-at-scale/results.csv \
    --watchlist data/watchlists/tech_weighted.txt \
    --start 2026-04-03 --end 2026-04-03 --yes
```

## Operational caveats

1. **Out-of-sample evidence is thin**. The +1.23% / 61% hit headline is from in-sample re-runs of the corpus. Live performance over weeks/months is the ONLY way to validate the claim. The product is the validation harness; running it accumulates the evidence.

2. **Tech concentration is structural**. Even with the 50% sector cap, a heavy-Tech watchlist will produce Tech-heavy commits. If Tech rolls over, the strategy WILL underperform. There is no current bear-side filter that catches Tech-cohort rollover (Spec 012 Class 4 macro is closest at 6 of 22 ticker_strong-bear cohort caught).

3. **Filter shadow modes are not catching anything**. Spec 007 bear + Spec X-1 + Spec 012 are all default-SHADOW pending a 30+ live-fire accumulation before flip-readiness review. Until then, bear-side suppression is A3 only.

4. **5-day window is unusable**. Do not change the 21d default to 5d expecting alpha; the corpus shows 5d is at the LLM single-call calibration ceiling.

5. **PM Hold rating + bullish prose can both be calibrated**. A propagate that returns rating=Hold with prose like "Initiate at OW, build over weeks" is intentionally consistent — the operator must trust the rating, not the prose. See `reference_pm_hold_with_bullish_prose.md`.

## Cross-references

- `docs/PAPER_TRADING.md` — paper-trade harness deep-dive
- `docs/SIGNALS.md` — what data the analyst layer consumes
- `docs/SIGNAL_LIFECYCLE.md` — Spec 002 signal-lifecycle architecture
- `RESEARCH_FINDINGS.md` — full corpus synthesis
- `CLAUDE.md` — Filter portfolio + Constitution + filter ordering
- `specs/002-paper-trading-harness/` — full spec/plan/contracts/tasks
