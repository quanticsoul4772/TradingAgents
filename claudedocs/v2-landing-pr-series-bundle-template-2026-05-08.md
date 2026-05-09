# v2 landing PR series bundle template — 2026-05-08

> **STATUS**: PRE-LANDING TEMPLATE. WC-10 v2 (n=100 ticker expansion) data lands soon (~8h ETA from CLAUDE.md refresh time). When it does, follow the workflow below — all landing PRs land in ~60-90 min total (vs ~3-4h from scratch).

**Trigger**: reasoning_decision rank #4 (tied at 0.635). Sister to PR #149 (v3 landing playbook). Bundles the pre-scaffolded artifacts for v2 into a single landing playbook.

## Why v2 landing is more complex than v3

v3 was n=8 paired (16 propagates) on a single ticker. The verdict matrix was 4 simple branches (NULL/ALT-A/ALT-B/PARTIAL ALT-A). v3 landing was 3 PRs in ~40 min.

v2 is **n=80 WC-10-only** (combined with v1's n=20 → n=100 cohort). The verdict matrix is more nuanced:

- **Primary** (SC-005(b)): signed-rating × 21d-α correlation → STRONG / MODERATE / NULL
- **Secondary** (ALT-A generalization): per-ticker commit rate across 8 tickers → ≥6 of 8 ≥80% threshold passes / fails (per Spec 009 FR-005)
- **Tertiary**: per-bucket realized α generalization beyond NVDA (does v1's NVDA Buy +4.67% finding hold?)

Combined verdict drives Spec 009 Branch A/B/C selection (Branch D pre-ruled-out per v3).

## The 4-PR landing series

When v2 results.csv reaches 80 rows, the v2 landing series consists of:

| PR | Type | Estimated time | Pre-scaffolded by |
|---|---|---|---|
| **Landing PR #1** — v2 ANALYSIS.md | research | ~25 min | PR #135 (template skeleton) |
| **Landing PR #2** — Spec 009 tasks.md (per selected branch) | spec-kit | ~15 min | PR #156 plan.md + PR #158 contract |
| **Landing PR #3** — RESEARCH_FINDINGS.md update | synthesis | ~15 min | template below |
| **Landing PR #4** — ROADMAP.md update + day-end synthesis | docs | ~15 min | template below |

Total: **~70 min wall-clock** vs ~3-4h from scratch.

## Workflow (copy-paste ready)

### Step 1: Verify v2 completion + run computation snippet (5 min)

```bash
cd C:/Development/Projects/TradingAgents
wc -l experiments/2026-05-08-002-wc-10-v2-ticker-expansion/results.csv
# Should print 81 (80 data rows + header). If less, wait for completion.

# Run computation snippet (see Section A below)
```

### Step 2: Open Landing PR #1 — v2 ANALYSIS.md (25 min)

```bash
git checkout main && git pull origin main
git checkout -b 162-v2-analysis-landing
```

Then:

1. Copy `experiments/2026-05-08-002-wc-10-v2-ticker-expansion/ANALYSIS_TEMPLATE.md` → `ANALYSIS.md`
2. Run computation snippet from Section A; populate every `<TBD>` with computed values
3. Pick verdict per the verdict matrix (Section B); fill verdict prose
4. Run `scripts/wc_10_underperformance_monitor.py` against v1+v2 combined CSV (Section C); paste output as monitoring smoke-test addendum
5. Update Constitution adherence checklist + Next-steps section
6. `git add` + commit + `gh pr create`

### Step 3: Open Landing PR #2 — Spec 009 tasks.md (15 min)

Per Spec 009 plan.md (PR #156) Phase 1 (Branch A) or Branch B/C tasks.

```bash
git checkout main && git pull origin main
git checkout -b 163-spec-009-tasks-branch-X
```

1. Use `.specify/templates/tasks-template.md` as starting point
2. Copy Phase 1-4 task list from plan.md for the selected branch (A or B or C)
3. Adjust task numbering + dependency arrows
4. Mark tasks as `[ ]` (incomplete) initially; MVP PR #4 will tick them off
5. Reference contract (PR #158) + research (PR #159) + quickstart (PR #159)
6. `git add` + commit + `gh pr create`

### Step 4: Open Landing PR #3 — RESEARCH_FINDINGS.md update (15 min)

Per template in Section D below. Two updates:

1. Headline section: add v2 verdict paragraph below v3 paragraph
2. Open Questions table: mark "WC-10 v2 expansion to n≥100" + "ALT-A generalization across tickers" + "NVDA Buy bullish-amplification generalize beyond NVDA?" rows as RESOLVED

### Step 5: Open Landing PR #4 — ROADMAP.md + day-end synthesis (15 min)

Per template in Section E below. Updates:

1. ROADMAP 2026-05-08 section: append v2 landing PR numbers + verdict
2. Optional: day-end synthesis paragraph in `claudedocs/research-burst-2026-05-08.md` (analogous to existing `research-burst-2026-05-06.md` + `2026-05-07.md`)

## Section A — Ready-to-run computation snippet

```python
# Run from project root after v2 results.csv has 80 rows.
import csv
from collections import defaultdict
from tradingagents.graph.trading_graph import fetch_returns
from tradingagents.wc_10 import bin_scalar_to_tier

V1_CSV = "experiments/2026-05-08-001-wc-10-pilot/results.csv"
V2_CSV = "experiments/2026-05-08-002-wc-10-v2-ticker-expansion/results.csv"

# Combine v1 (WC-10 mode rows only) + v2 for n=100 cohort
all_wc10 = []
for path in (V1_CSV, V2_CSV):
    with open(path) as f:
        for row in csv.DictReader(f):
            if row.get("error") or row["mode"] != "wc_10":
                continue
            all_wc10.append(row)

print(f"Combined v1+v2 WC-10 cohort: n={len(all_wc10)}")

# Fetch realized α
ret_cache = {}
for r in all_wc10:
    key = (r["ticker"], r["date"])
    if key not in ret_cache:
        raw, alpha, days = fetch_returns(r["ticker"], r["date"], holding_days=21)
        ret_cache[key] = (raw, alpha, days)

# SC-005(b) — signed-rating × α correlation (PRIMARY)
import statistics
pairs = []
for r in all_wc10:
    raw, alpha, days = ret_cache[(r["ticker"], r["date"])]
    if alpha is None: continue
    pairs.append((float(r["rating"]), alpha * 100))

def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    num = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    dx = (sum((x-mx)**2 for x in xs))**0.5
    dy = (sum((y-my)**2 for y in ys))**0.5
    return num/(dx*dy) if dx*dy else 0

xs, ys = zip(*pairs)
r = pearson(xs, ys)

# Spearman
def rankify(arr):
    s = sorted(range(len(arr)), key=lambda i: arr[i])
    ranks = [0]*len(arr)
    for rank, i in enumerate(s, 1):
        ranks[i] = rank
    return ranks
rho = pearson(rankify(xs), rankify(ys))

print(f"\\nSC-005(b) Pearson r: {r:+.3f} (critical at p=0.05, n=100: ±0.197)")
print(f"SC-005(b) Spearman ρ: {rho:+.3f}")
if abs(r) > 0.30:
    print("→ STRONG (|r|>0.30) — Spec 009 Branch A activation")
elif abs(r) > 0.197:
    print("→ MODERATE (0.197<|r|<0.30) — Spec 009 Branch B activation")
else:
    print("→ NULL (|r|<0.197) — Spec 009 Branch C activation (bin-then-output ergonomic-only)")

# Per-ticker commit rate (SC-007 ALT-A generalization, SECONDARY)
print("\\nPer-ticker commit rate (FR-005 threshold: ≥80% per ticker):")
print(f"{'ticker':6s} {'n':>4s} {'committed':>10s} {'rate':>6s}")
by_ticker = defaultdict(list)
for r in all_wc10:
    by_ticker[r["ticker"]].append(abs(float(r["rating"])) > 0.2)
fr005_pass = 0
for ticker in sorted(by_ticker):
    n = len(by_ticker[ticker])
    committed = sum(by_ticker[ticker])
    rate = committed / n
    flag = " ✓" if rate >= 0.80 else " ✗"
    fr005_pass += rate >= 0.80
    print(f"{ticker:6s} {n:>4d} {committed:>10d} {rate:>5.0%}{flag}")
print(f"\\nFR-005: {fr005_pass} of 8 tickers ≥80% commit rate (≥6 required for Branch A)")

# Per-bucket mean α (TERTIARY — generalization beyond NVDA)
print("\\nPer-bucket mean α (rating-attributed; v1+v2 combined):")
print(f"{'bucket':12s} {'n':>4s} {'mean α':>8s}")
by_bucket = defaultdict(list)
for r in all_wc10:
    raw, alpha, days = ret_cache[(r["ticker"], r["date"])]
    if alpha is None: continue
    bucket = r["binned_tier"]
    if bucket in ("Buy", "Overweight"):
        by_bucket[bucket].append(alpha * 100)
    elif bucket in ("Underweight", "Sell"):
        by_bucket[bucket].append(-alpha * 100)
    else:
        by_bucket[bucket].append(0)
for bucket in ("Buy", "Overweight", "Hold", "Underweight", "Sell"):
    if bucket in by_bucket:
        rs = by_bucket[bucket]
        mean = sum(rs)/len(rs)
        print(f"{bucket:12s} {len(rs):>4d} {mean:>+7.2f}%")
```

Output:
- Combined cohort size (should be 100)
- SC-005(b) Pearson r + Spearman ρ + verdict line (STRONG/MODERATE/NULL)
- Per-ticker commit-rate breakdown (8 tickers; flag ≥80% pass)
- FR-005 pass count (≥6 required for Branch A)
- Per-bucket mean α (Buy/OW/Hold/UW/Sell)

## Section B — Verdict matrix → Spec 009 branch selection

| SC-005(b) | FR-005 (≥6 of 8 @ ≥80%) | Spec 009 Branch | Notes |
|---|---|---|---|
| STRONG (`\|r\|>0.30`) | PASS (≥6) | **A** | Operator-opt-in via daily_signals.py + paper_trade.py |
| STRONG | FAIL (<6) | **B** | Cohort too narrow for full activation; research-only |
| MODERATE (`0.197<\|r\|<0.30`) | PASS | **B** | Statistically real but small effect; research-only |
| MODERATE | FAIL | **B** | Both criteria weak; research-only |
| NULL (`\|r\|<0.197`) | PASS | **C** | Distribution shift real but magnitude carries no info; bin-then-output ergonomic-only |
| NULL | FAIL | **C** or **SKIP-with-doc** | Marginal value; consider closing Spec 009 with a SKIP-style retrospective |

Branch D pre-RULED-OUT per v3 verdict (already PARTIAL ALT-A, not full ALT-A).

## Section C — Monitoring smoke test addendum

```bash
# Combine v1+v2 WC-10 + v1 5-tier baseline into a temp paired CSV,
# then run the monitor:
python scripts/wc_10_underperformance_monitor.py \
    --csv experiments/2026-05-08-001-wc-10-pilot/results.csv \
    --alert-threshold-pp -5.0
```

(v2 alone is WC-10-only; the monitor needs paired data. v1's paired data is the canonical baseline.)

If the monitor reports cohort cumulative Δα WORSE than the v1 smoke-test result (+22.42pp), flag in Landing PR #1 ANALYSIS as a v3-caveat strengthening signal. If similar to v1 result, no additional signal — v1.5.1 caveat scope holds.

## Section D — RESEARCH_FINDINGS.md update template

Append to the WC-10 Headline section (below the existing v3 paragraph):

> **WC-10 v2 expansion (2026-05-08 / 2026-05-09; n=100 combined cohort)**: WC-10 v2 (8 tickers × 10 weekly Q1 2026 dates × WC-10 mode = 80 propagates) combined with v1 for n=100 cohort produced verdict **<STRONG / MODERATE / NULL>** on SC-005(b): Pearson r=<FILL: r>, Spearman ρ=<FILL: ρ>. FR-005 generalization: <FILL: N>/8 tickers exhibited ≥80% commit rate. Per-bucket realized α (rating-attributed): Buy n=<N> mean <+X.X>%, OW n=<N> mean <+X.X>%, Hold n=<N> mean <+X.X>%, UW n=<N> mean <+X.X>%. **Spec 009 Branch <X> activation triggered** per the verdict matrix. <Branch-specific summary sentence>.

Open Questions table — mark resolved:

> | ~~WC-10 v2 expansion to n≥100 paired propagates~~ — **RESOLVED 2026-05-08/09**, see v2 ANALYSIS.md (Landing PR #X). | (resolved) | $32 |
> | ~~Does ALT-A categorical-bottleneck pattern generalize across tickers beyond NVDA + AAPL?~~ — **RESOLVED**, FR-005 verdict <FILL: pass/fail count>. | (resolved) | $0 (subsumed) |
> | ~~Does the v1 NVDA Buy bullish-amplification generalize beyond NVDA?~~ — **RESOLVED**, per-bucket means show <generalization status>. | (resolved) | $0 (subsumed) |
> | ~~Should daily_signals.py integrate WC-10 as an opt-in mode?~~ — **RESOLVED**, Spec 009 Branch <X> activation per Landing PR #X. | (resolved) | $0+ |

## Section E — ROADMAP.md update template

Append to the existing 2026-05-08 PRs section:

> **Late 2026-05-08 (or early 2026-05-09) — WC-10 v2 landing**:
> - Landing PR #X — v2 ANALYSIS.md (verdict <STRONG / MODERATE / NULL>; FR-005 <pass/fail>; Spec 009 Branch <X> selected)
> - Landing PR #X+1 — Spec 009 tasks.md (Branch <X>)
> - Landing PR #X+2 — RESEARCH_FINDINGS update
> - Landing PR #X+3 — ROADMAP day-end synthesis

Optional: write `claudedocs/research-burst-2026-05-08.md` analogous to existing 05-06 + 05-07 retrospectives, summarizing the full 40+-PR day arc + WC-10 verdict landings.

## Estimated total wall-clock

| Phase | Time |
|---|---|
| Step 1: Verify completion + computation snippet | 5 min |
| Landing PR #1: v2 ANALYSIS.md | 25 min |
| Landing PR #2: Spec 009 tasks.md | 15 min |
| Landing PR #3: RESEARCH_FINDINGS update | 15 min |
| Landing PR #4: ROADMAP + day-end synthesis | 15 min |
| **Total** | **~75 min** |

vs ~3-4 hours if all 4 PRs were drafted from scratch. **~60% time reduction** consistent with the v3 landing series (~67% reduction from PR #149).

## Cost

$0. Codification work only. Constitution III T0.

## Cross-references

- **PR #135** — original v2 ANALYSIS_TEMPLATE.md
- **PR #149** — sister v3 landing playbook (this template extends the pattern to v2's larger verdict matrix)
- **PR #146** — `scripts/wc_10_underperformance_monitor.py` (smoke test on combined cohort)
- **PR #156** — Spec 009 plan.md (Branch A/B/C implementation)
- **PR #158** — Spec 009 contracts/daily_signals_wc_10_flag.md (flag CLI surface)
- **PR #159** — Spec 009 research.md + quickstart.md
- v1 ANALYSIS.md (n=20 baseline)
- v3 ANALYSIS.md (PR #153, PARTIAL ALT-A)
- Constitution v1.5.1 Principle VII (PR #154)

## Post-v2-landing follow-up sequencing

After v2 lands + the 4-PR landing series ships:

1. **If Branch A activates**: Spec 009 6-PR bundle continues with PR #4 MVP implementation (~4-6h wall-clock per plan.md Phase 1+2)
2. **If Branch B activates**: Spec 009 6-PR bundle continues with PR #4 docs-only update (~30 min per plan.md Branch B)
3. **If Branch C activates**: Spec 009 6-PR bundle continues with PR #4 internal-only mode addition (~1.5h per plan.md Branch C)

Day-end note: today's run will likely span both 2026-05-08 and 2026-05-09 (UTC midnight has passed). Memory entry `project_2026-05-08_record_day.md` may need a sister entry `project_2026-05-09_record_day.md` if v2 landing occurs after midnight + drives meaningful new work.
