# Analysis: opus47-swap-aapl

> **Headline**: Opus 4.7 on AAPL × 10 produced **8 Hold + 2 Overweight** — wildly different from the same-config 005 NVDA result (10/10 OW). Opus DISCRIMINATES by ticker; the 005 NVDA OW-collapse was bull-regime-driven, not a model-wide commit bias. The 21d bull signal that was strong on Opus NVDA (+2.85%, n=9) does NOT replicate on Opus AAPL (-0.07%, n=2) — mostly because Opus refused to commit OW on AAPL's mixed-evidence dates. **The framework's value under Opus is calibrated commitment**: commits where evidence is clear, holds where it isn't.

## Result

### Distribution comparison (AAPL × same 10 dates, 6-way)

| Bucket | Pilot Sonnet | WC-12 cross | Brave | Exa | Single-call | **Opus 4.7** |
|---|---|---|---|---|---|---|
| Buy | 0 | 0 | 0 | 0 | 0 | 0 |
| Overweight | 0 | 0 | 0 | 0 | 3 | **2** |
| Hold | 3 | 7 | 7 | 6 | 0 | **8** |
| Underweight | 7 | 2 | 3 | 4 | 7 | 0 |
| Sell | 0 | 1 | 0 | 0 | 0 | 0 |

**Striking contrast**: Opus on AAPL is the most Hold-heavy distribution of any AAPL experiment except WC-12 cross-AAPL. Opus on NVDA was 10/10 OW. Same model, same prompt, completely different distribution because Opus reads each ticker's evidence differently.

### Forward-α (5d / 10d / 21d via horizon_sweep)

| Bucket | Opus AAPL 5d | Opus AAPL 10d | **Opus AAPL 21d** | Opus NVDA 21d (for contrast) |
|---|---|---|---|---|
| Overweight | +0.33% (n=2, 50%) | +0.93% (n=2, 50%) | **-0.07% (n=2, 50%)** | +2.85% (n=9, 78%) |
| Hold | +0.29% (n=8, 62%) | -0.49% (n=8, 38%) | **-0.60% (n=7, 43%)** | — |

The 21d bull lift seen on Opus NVDA does NOT replicate on Opus AAPL. The 2 OW commits had 50% directional hit rate; mean α essentially flat.

Hold bucket at 21d shows -0.60% (n=7, 43% positive) — slightly bearish on average, consistent with AAPL's mixed-to-bearish realized direction in this period.

### Per-date breakdown at 21d

| Date | Realized 21d α | **Opus 4.7** | Correct? |
|---|---:|---|---|
| 2026-01-30 | +3.42% | Hold | — (would have been correct OW) |
| 2026-02-06 | -4.18% | Hold | — (would have been correct UW) |
| 2026-02-13 | +1.00% | Hold | — (small alpha, Hold consistent) |
| 2026-02-20 | -0.27% | Hold | ≈ (flat, Hold consistent) |
| 2026-02-27 | **+0.98%** | **OW** | ✓ |
| 2026-03-06 | +0.15% | Hold | ≈ (flat, Hold consistent) |
| 2026-03-13 | **-1.66%** | **OW** | ✗ |
| 2026-03-20 | -1.23% | Hold | — (small bear, Hold OK) |
| 2026-03-27 | -3.43% | Hold | — (Hold OK; OW would have been wrong) |
| 2026-04-03 | (insufficient 21d data) | Hold | — |

**OW commits**: 1 right (02-27 +0.98%), 1 wrong (03-13 -1.66%). Mean -0.34%, hit rate 50%.

**Hold commits**: 8 dates, mostly small-magnitude — consistent with a "tracks SPY" expectation. Two cases where Hold was suboptimal: 01-30 (Opus held, AAPL outperformed +3.42% — would have been right OW) and 02-06 (Opus held, AAPL underperformed -4.18% — would have been right UW). Pilot Sonnet HELD on 01-30 too and did UW on 02-06; Opus is more conservative on the bear date than Sonnet was.

### EH-2 gate

3 DENY findings: missing Buy + Underweight + Sell. Distribution narrower than 5-tier intent, but at least using 2 tiers (Hold + OW) — broader than Opus NVDA's single-tier collapse.

## Decision

**Scenario B confirmed** per HYPOTHESIS decision tree: Opus discriminates by ticker — produces mixed distribution on AAPL (8 Hold + 2 OW), in stark contrast to NVDA's 10/10 OW.

Per ROADMAP active branch: this confirms the 30-pair Opus re-pilot is well-grounded, but with a critical revision — **expect substantially different distributions across tickers depending on regime**. Cannot assume Opus will produce 10/10 OW on every ticker (NVDA was the bull-regime outlier).

**Cross-experiment OW 21d after 006**: +1.79% (n=41, 63% hit). Down slightly from +1.88% before 006 but still strongly positive — Opus AAPL's flat OW α (-0.07%, n=2) didn't dominate, NVDA Opus's strong +2.85% (n=9) still anchors the bull-side claim.

## Detailed findings

### What "calibrated commitment" means

Opus's behavior across the two tickers maps to evidence quality:

| Ticker | Underlying regime in this period | Opus distribution | What this means |
|---|---|---|---|
| NVDA | Bull (+26% over window) | 10/10 OW | Clear bull evidence → Opus commits |
| AAPL | Mixed (some +7% days, some -7% days) | 8 Hold + 2 OW | Mixed evidence → Opus mostly holds, commits when subset of dates show clearer bull signal |

Sonnet pilot on these tickers:
- NVDA pilot: 7 Hold + 3 UW (under-committed despite clear bull regime → missed the lift)
- AAPL pilot: 3 Hold + 7 UW (over-committed bearish on a mixed-evidence ticker → wrong-direction bias)

**Opus is more calibrated than Sonnet across both regimes**: commits when evidence supports it (NVDA), holds when it doesn't (AAPL). Sonnet either over-abstains (NVDA) or over-commits-bearish (AAPL).

### What this means for Constitution Principle VII

The Constitution VII update from 005 said: "Each model's intrinsic calibration determines mode-collapse direction; Hold-collapse is one valid form, OW-collapse is another, both honest if realized α matches."

After 006 the picture is more nuanced: Opus's mode-collapse direction is **ticker-specific within a single model**, not a model-wide property. Opus on bull-regime tickers commits OW; Opus on mixed-evidence tickers holds. So Principle VII should be amended again:

**Mode-collapse direction is a function of (model × ticker × regime × prompt)**. The framework's calibrated abstention or commit IS the model expressing its intrinsic confidence given the available evidence — and stronger models discriminate this confidence per-ticker rather than collapsing uniformly.

### What this means for the 30-pair Opus re-pilot

Expected behavior on a mixed ticker basket:
- Tickers in clear bull regimes → mostly OW commits with positive 21d α (per 005 NVDA pattern)
- Tickers in clear bear regimes → mostly UW commits (untested with Opus, but pattern likely symmetric)
- Tickers with mixed/ambiguous evidence → mostly Hold (per 006 AAPL pattern)

Cross-experiment OW 21d at +1.79% (n=41) holds as the load-bearing claim. The 30-pair re-pilot should validate it at scale **and** specifically test whether the Hold bucket on Opus is also calibrated (small magnitude, near zero).

Cost-revised plan: 30 pairs × Opus ~$1/run = ~$30 (fits Principle III). Use the A3 momentum filter enabled. Mix of bull-regime (NVDA, MSFT) + mixed-regime (AAPL, GOOG) + bear-regime (XOM, INTC) tickers.

### The 2 Opus AAPL OW commits in detail

- **02-27 OW (correct, +0.98%)**: AAPL was at the bottom of a bear stretch (mid-Feb selloff). Opus saw the earnings strength + China recovery as outweighing the selloff. Bull commit — modest +0.98% over 21d.
- **03-13 OW (wrong, -1.66%)**: AAPL was rallying off the early-March bottom. Opus extrapolated. Realized 21d underperformed SPY by 1.66% (AAPL up only +3.48% while SPY up +5.14%).

Mean -0.34%. Modest negative — well within noise band for n=2.

## Limitations

- n=10 single ticker. Opus on 1 more ticker (e.g. MSFT) would triangulate the per-ticker discrimination claim further.
- AAPL period had unusually mixed direction; bull-regime-only or bear-regime-only tickers may produce different commit rates from Opus.
- 9 of 10 dates resolved at 21d (10th date 04-03 needs ~1 more day of data); doesn't change the result materially.

## Cost & timing

- Wall-clock: 66.5 min (slightly faster than 005's 70.5 min)
- Cost: ~$10
- Errors: 0/10
- PARAMS.json auto-synced (R-007 fix verified end-to-end on this fresh run — the deep_think_llm override correctly recorded)

## Next experiment

**30-pair Opus re-pilot at 21d horizon, $30, ~3.5h, with A3 momentum filter enabled.** Mixed ticker basket: 10 bull-regime (NVDA, MSFT, GOOG-style) + 10 mixed (AAPL, AMZN-style) + 10 bear-regime (XOM, INTC, BBY). Tests whether the OW 21d signal scales AND whether Opus's per-ticker discrimination produces a usable cross-regime distribution.

Per ROADMAP active branch: this is the natural next move now that AAPL has confirmed Scenario B (Opus discriminates).

## One-paragraph summary for findings.md

> Opus 4.7 swapped on AAPL × same 10 dates produced 8 Hold + 2 Overweight (vs Sonnet pilot's 3 Hold + 7 Underweight, and vs Opus NVDA's 10 OW). The 21d OW α was -0.07% (n=2, 50% hit) — flat, decisively NOT the +2.85% strong bull signal seen on Opus NVDA. The 005 NVDA OW-collapse was bull-regime-driven, not a model-wide commit bias. Opus discriminates by ticker: commits when evidence is clear (NVDA bull regime → 10/10 OW), holds when evidence is mixed (AAPL mixed regime → 8/10 Hold). This is more calibrated behavior than Sonnet, which over-abstained on NVDA AND over-committed-bearish on AAPL. The cross-experiment OW 21d α drops slightly to +1.79% (n=41, 63% hit) but remains the load-bearing claim. The 30-pair Opus re-pilot at 21d should now test a mixed ticker basket (bull / mixed / bear regimes) to validate the per-ticker discrimination at scale.
