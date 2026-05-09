# Quickstart: WC-10 Production Deployment (Spec 009)

**Spec**: [spec.md](spec.md) (PR #140) | **Plan**: [plan.md](plan.md) (PR #156) | **Research**: [research.md](research.md) (PR #159) | **Contract**: [contracts/daily_signals_wc_10_flag.md](contracts/daily_signals_wc_10_flag.md) (PR #158)

Operator guide for activating WC-10 production deployment via the `daily_signals.py --wc-10-enabled` flag (Branch A; v2-verdict-conditional).

> **STATUS**: PRE-ACTIVATION QUICKSTART — Branch A activation BLOCKED ON v2 verdict (~9h remaining as of quickstart draft). Steps below are operator-ready when v2 lands STRONG verdict + FR-005 cohort threshold passes.

---

## Pre-flight check

Before activating WC-10 mode for an operator workflow, verify:

1. **v2 has landed with STRONG verdict** (Pearson r ≥ 0.30 OR FR-005 ≥6 of 8 tickers @ ≥80% commit rate)
2. **Constitution v1.5.1** is on main (PR #154 merged) — confirms Bear-regime validation paragraph is in place
3. **Spec 009 MVP PR has merged** (PR #4 of the spec-kit bundle, post-v2-verdict)
4. **Empirically-validated ticker list is in `docs/SIGNALS.md`** per Spec 009 FR-006

Verify via:

```bash
# Check Constitution version
grep -E "^\*\*Version\*\*:" .specify/memory/constitution.md
# Expect: **Version**: 1.5.1 (or later)

# Check FR-005 cohort list location
grep -A 5 "WC-10 mode" docs/SIGNALS.md | head -20
```

---

## Single-ticker smoke test

Test the activation surface on one ticker before adding it to your watchlist cron:

```bash
python scripts/daily_signals.py \
    --tickers NVDA \
    --wc-10-enabled \
    --date 2026-04-15 \
    --out claudedocs/wc-10-smoke-2026-04-15.md \
    --emit-csv claudedocs/wc-10-smoke-2026-04-15.csv
```

**Expected output**:

- `claudedocs/wc-10-smoke-2026-04-15.md` — markdown digest with WC-10 confidence note in header + per-ticker scalar (4 decimals)
- `claudedocs/wc-10-smoke-2026-04-15.csv` — CSV with both `rating` (5-tier binned) AND `rating_scalar` (continuous) columns

**Verification**: structure should match `scripts/wc_10_dryrun_digest.py --date 2026-04-15` output (PR #141 dry-run renderer). The dry-run is the canonical UX prototype.

**Cost**: ~$0.40 LLM (single propagate).

---

## Multi-ticker daily workflow

Once smoke test passes, integrate into your daily watchlist:

```bash
# Add to ~/.tradingagents/watchlist.txt or pass --tickers comma-list
python scripts/daily_signals.py \
    --tickers tickers.txt \
    --wc-10-enabled \
    --emit-csv ~/.tradingagents/paper/today-wc10.csv
```

Runs propagate on each ticker (~$0.40 each) and emits:
- Markdown digest at `claudedocs/daily-signals-<today>.md`
- Signal CSV consumable by `paper_trade.py step` per Spec 002

---

## paper_trade.py integration

If you use the paper-trading harness (Spec 002), feed the WC-10 CSV directly:

```bash
python scripts/paper_trade.py step \
    --signals-csv ~/.tradingagents/paper/today-wc10.csv
```

Position-sizing uses the linear ramp `slot_size = base_slot × min(1.0, abs(rating_scalar) / 0.6)` per R-3 (Branch A Phase 2).

When `rating_scalar` column is absent (e.g., a CSV from before WC-10 activation), paper_trade.py falls back to the existing 5-tier sizing logic transparently — replay invariant preserved.

---

## Runtime monitoring (mandatory for v1.5.1 caveat enforcement)

Per Constitution v1.5.1 + Spec 009 R-8, runtime monitoring is the production enforcement of the asymmetric-calibration caveat. Wire `scripts/wc_10_underperformance_monitor.py` into nightly cron:

```bash
# Add to crontab
0 22 * * * cd /path/to/TradingAgents && python scripts/wc_10_underperformance_monitor.py \
    --csv ~/.tradingagents/paper/today-wc10.csv \
    --alert-threshold-pp -5.0 \
    > ~/.tradingagents/monitor-$(date +\%Y-\%m-\%d).log 2>&1
```

**Alert criteria** (per PR #146):
- Single-pair severe: `|delta_pp| < -5pp`
- Streak: ≥5 consecutive pairs with `delta < 0`
- Cohort cumulative: cumulative delta `< -5pp` AND `n ≥ 10`

**Exit code**: `0` = no alerts; `1` = alert triggered. Cron mailer should email operator on non-zero exit.

If alerts fire repeatedly, consider:
1. Switching to `--wc-10-disabled` for operator workflows
2. Investigating the underperformance via `claudedocs/wc-10-underperformance-investigation-<date>.md`
3. Filing a Spec 009 v2 follow-up PR to revise FR-005 cohort thresholds

---

## Troubleshooting

### "WC-10 mode active" header missing from digest

Verify `--wc-10-enabled` was passed. Default behavior is unchanged 5-tier mode.

### `rating_scalar` column missing from CSV

Verify BOTH `--wc-10-enabled` AND `--emit-csv <path>` were passed. The column is only emitted in WC-10 mode.

### paper_trade.py replay throws "unknown column 'rating_scalar'"

You're on a paper_trade.py version older than the Spec 009 MVP PR. Pull latest main + reinstall via `pip install -e .[dev]`.

### V3 caveat ⚠️ note appears for tickers I expected to be validated

Check `docs/SIGNALS.md` empirically-validated cohort list. If a ticker should be added (e.g., your operator workflow has accumulated n≥20 propagates with documented WC-10 outperformance), file a PR to update the cohort list per Spec 009 FR-005.

### Underperformance alerts firing every day

Check whether your watchlist is dominated by bear-regime tickers. v3 verdict (PARTIAL ALT-A on Q4 2025 NVDA) showed WC-10 amplifies bullish reads on falling cohorts — known caveat. Consider:
1. Diversifying watchlist to include bullish + neutral tickers
2. Switching to `--wc-10-disabled` during persistent bear regimes
3. Filing a Spec 009 v3 PR to revise FR-006 caveat scope

---

## Cost guide

| Workflow | Per-day cost | Per-month cost (~22 trading days) |
|---|---|---|
| 5-ticker daily (default) | ~$2.00 | ~$44 |
| 10-ticker daily | ~$4.00 | ~$88 |
| 20-ticker daily | ~$8.00 | ~$176 |
| Smoke test (1 ticker, ad-hoc) | ~$0.40 | n/a |

WC-10 mode adds NO marginal LLM cost vs default 5-tier mode (the schema change happens at the PM-stage output layer; propagate cost is unchanged).

Monitoring (`scripts/wc_10_underperformance_monitor.py`) is `$0` LLM cost (consumes saved CSV data + yfinance for realized α; ~50ms per ticker).

---

## Known caveats (per Constitution v1.5.1 + v3 ANALYSIS)

1. **Asymmetric calibration**: WC-10 amplifies bullish reads on bull-regime tickers (well-calibrated; NVDA Buy mean +4.67% α 21d in v1) but ALSO amplifies on falling cohorts (anti-calibrated; v3 PARTIAL ALT-A on Q4 2025 NVDA). Magnitude bound: `|delta| < 1.0pp` per v3.

2. **Bear-side specifically**: WC-10 doubles bad-direction commit count when the framework's reads are wrong (v1 AAPL UW cohort + v3 NVDA Buy on falling Q4 cohort). Operator discretion required for tickers in bear regime.

3. **Cohort scope**: FR-005 empirically-validated cohort list in `docs/SIGNALS.md` is the canonical scope. Tickers outside this list show ⚠️ V3-caveat note and apply at operator's own risk.

4. **Hold under WC-10**: `|rating_scalar| ≤ 0.2` is binned to Hold. Per Constitution VII v1.5.0/v1.5.1, this is genuine ambiguity (Mechanism A), not schema-induced collapse.

---

## Cross-references

- spec.md (PR #140) + plan.md (PR #156) + contracts/daily_signals_wc_10_flag.md (PR #158) + research.md (PR #159) — full Spec 009 bundle
- `scripts/wc_10_dryrun_digest.py` (PR #141) — UX prototype (smoke test reference)
- `scripts/wc_10_underperformance_monitor.py` (PR #146) — runtime monitor
- Constitution v1.5.1 Principle VII sub-section + Bear-regime validation paragraph (PR #154)
- WC-10 v1 ANALYSIS.md (PR #130) + v3 ANALYSIS.md (PR #153) — empirical basis
- Memory `reference_conditional_branch_spec_pattern.md` (PR #151) — pre-scaffolding pattern
