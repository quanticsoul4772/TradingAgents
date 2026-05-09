# Contract: `daily_signals.py --wc-10-enabled` flag

**Spec**: [../spec.md](../spec.md) (PR #140) | **Plan**: [../plan.md](../plan.md) (PR #156)

This contract defines the operator-facing flag for WC-10 production deployment via `daily_signals.py`. Activates ONLY under Spec 009 Branch A (per v2 SC-005(b) STRONG verdict + per FR-005 cohort threshold).

> **STATUS**: CONTRACT DRAFT — Branch A activation BLOCKED ON v2 verdict (~9h remaining as of contract draft). Implementation begins in Spec 009 PR #4 (MVP) per the 6-PR bundle. PR #141's `scripts/wc_10_dryrun_digest.py` is the canonical UX prototype against saved data.

---

## CLI surface

```bash
# Default behavior (no flag) — current 5-tier mode unchanged
python scripts/daily_signals.py --tickers NVDA,AAPL

# WC-10 mode enabled
python scripts/daily_signals.py --tickers NVDA,AAPL --wc-10-enabled

# Explicit no (overrides any future config-default change)
python scripts/daily_signals.py --tickers NVDA,AAPL --wc-10-disabled
```

### Flag behavior

| Flag state | `wc_10_enabled` config | `wc_10_filter_mode` config | Filter chain | Output schema |
|---|---|---|---|---|
| **Absent** (default) | `False` | (irrelevant) | All 9 filters active | 5-tier categorical |
| **`--wc-10-enabled`** | `True` | `"bypass"` | All 9 filters SKIPPED (per Spec 108 filter-bypass mode) | Continuous scalar `[-1, +1]` rendered to 4 decimals |
| **`--wc-10-disabled`** | `False` (explicit) | (irrelevant) | All 9 filters active | 5-tier categorical |

## Markdown digest output

When `--wc-10-enabled` is set, the markdown digest written to `claudedocs/daily-signals-<date>.md` adds:

### Header confidence note

Below the existing date header + universe summary line, add:

```markdown
**WC-10 mode active** — ratings rendered as continuous scalars in [-1.0, +1.0] (4 decimals).
Bin thresholds: Sell ≤ -0.6 < Underweight ≤ -0.2 < Hold ≤ +0.2 < Overweight ≤ +0.6 < Buy.
See [Constitution VII v1.5.1](../.specify/memory/constitution.md) "Schema-induced abstention is NOT calibrated abstention" + [docs/SIGNALS.md](../docs/SIGNALS.md) for caveat scope.
```

### Per-ticker rating rendering

Each ticker block in the actionable + filtered sections renders the scalar alongside the binned tier:

```markdown
### NVDA — Buy (scalar `+0.7200`)
> [Existing rationale block]
```

Format pattern matches `scripts/wc_10_dryrun_digest.py` (PR #141) which has been UX-validated against v1 pilot data on 3 sample dates.

### Side-by-side comparison (v1 vs v3 evidence)

For tickers in the empirically-validated cohort (per FR-005 — ≥6 of 8 v2 tickers passing the ≥80% commit-rate threshold), no additional annotation. For tickers OUTSIDE that cohort, append a per-ticker note:

```markdown
> ⚠️ **WC-10 not empirically validated for this ticker.** v3 caveat applies (regime-asymmetric calibration possible). Operator discretion advised.
```

The empirically-validated ticker list ships in `docs/SIGNALS.md` per FR-006.

## CSV output (`--emit-csv` interaction)

When `--emit-csv <path>` AND `--wc-10-enabled` are both set, the emitted CSV adds one column:

| Column | Type | Source | Description |
|---|---|---|---|
| `rating_scalar` | `float` in `[-1.0, +1.0]` (4 decimals) | `extract_scalar_rating()` from `tradingagents.graph.signal_processing` | The continuous-scalar rating from WC-10 mode |

When `--wc-10-disabled` (or default), the `rating_scalar` column is OMITTED entirely (not emitted as empty). Backward-compat with existing CSV consumers (paper_trade.py replay path).

When BOTH columns present:

| `rating` (5-tier binned) | `rating_scalar` | Producer/consumer relationship |
|---|---|---|
| `Buy` | `+0.6500` | Both populated; consumer can use either |
| `Overweight` | `+0.4200` | Same |
| `Hold` | `+0.0500` | Same |

## Tests required (extend `tests/test_daily_signals.py` or create `tests/test_daily_signals_wc_10.py`)

### Unit tests (target: 8-10)

- `test_default_no_wc_10_flag_unchanged` — flag absent → output identical to current production
- `test_wc_10_enabled_sets_config_correctly` — `--wc-10-enabled` → `wc_10_enabled=True` + `wc_10_filter_mode="bypass"`
- `test_wc_10_disabled_explicit_overrides_default` — `--wc-10-disabled` → forces False even if future config flips default
- `test_markdown_includes_confidence_note_when_enabled` — header note present
- `test_markdown_renders_scalar_to_4_decimals` — `+0.6200` not `+0.62` or `+0.620000`
- `test_markdown_renders_binned_tier_alongside_scalar` — both shown
- `test_csv_includes_rating_scalar_when_enabled` — column present
- `test_csv_omits_rating_scalar_when_disabled` — column NOT present (not empty)
- `test_v3_caveat_note_appears_for_non_validated_tickers` — ⚠️ block appears for tickers outside FR-005 cohort
- `test_v3_caveat_note_omitted_for_validated_tickers` — clean output for validated tickers

### Integration tests (target: 2)

- `test_paper_trade_replay_consumes_rating_scalar` — emit CSV with WC-10 mode → paper_trade.py replay handles scalar correctly (per Branch A Phase 2)
- `test_paper_trade_replay_falls_back_to_5_tier_when_no_scalar` — emit CSV without WC-10 → paper_trade.py replay uses `rating` column unchanged

## Edge cases

### Mode mismatch in CSV consumer

If a paper_trade.py replay run loads a CSV with `rating_scalar` column but the harness was started before the column existed, the harness MUST gracefully fall back to the `rating` column (not crash). Test: load v1+v2+v3 CSVs (some have scalar, some don't) — replay completes without error.

### Hold ratings under WC-10 mode

Hold under WC-10 mode is `|rating_scalar| ≤ 0.2`. Per Constitution VII v1.5.0 + WC-10 v1 pilot, this is genuine ambiguity (Mechanism A, NOT schema-induced collapse). Operators see Hold treated identically to 5-tier Hold mode — suppressed from actionable list (per existing `daily_signals.py` filter behavior) unless `--include-all` flag present.

### V3-caveat note placement

The ⚠️ note appears AFTER the existing per-ticker rationale block, NOT BEFORE the rating. Avoids cluttering the primary signal. Operators see the rating first, the caveat second (matching v3 ANALYSIS framing — caveat is a magnitude-bound, not a hard gate).

## Acceptance criteria summary

For Spec 009 Branch A activation:

- [ ] All CLI surface flags work as documented
- [ ] Markdown digest renders scalar + binned tier + confidence note + caveat per FR-006
- [ ] CSV output adds `rating_scalar` column when enabled; omits when not
- [ ] Backward-compat: paper_trade.py replay handles both schemas
- [ ] All 10 unit + 2 integration tests pass
- [ ] Smoke-tested via `daily_signals.py --tickers NVDA --wc-10-enabled --date 2026-04-15` matches `scripts/wc_10_dryrun_digest.py --date 2026-04-15` output structure (PR #141)

## Cross-references

- `specs/009-wc-10-production-deployment/spec.md` (PR #140) — Branch A user story A.1 source
- `specs/009-wc-10-production-deployment/plan.md` (PR #156) — Phase 1 implementation outline
- `scripts/wc_10_dryrun_digest.py` (PR #141) — UX prototype against saved data
- `scripts/daily_signals.py` (existing) — base implementation to extend
- `scripts/paper_trade.py` (existing) — Branch A Phase 2 consumer (extends to read `rating_scalar`)
- `tradingagents/graph/signal_processing.py` `extract_scalar_rating` — scalar extraction (Spec 108)
- `tradingagents/wc_10/bin.py` `bin_scalar_to_tier` — bin function (Spec 108)
- Constitution v1.5.1 Principle VII sub-section "Schema-induced abstention is NOT calibrated abstention" + Bear-regime validation paragraph (PR #154)
- v3 ANALYSIS.md (PR #153) — Patch D + caveat scope
- WC-10 v1 ANALYSIS.md (PR #130) — original empirical basis
