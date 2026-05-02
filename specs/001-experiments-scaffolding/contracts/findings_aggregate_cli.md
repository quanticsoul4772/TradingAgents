# Contract: `scripts/findings_aggregate.py` CLI

## Synopsis

```bash
python scripts/findings_aggregate.py [--experiments-dir <path>] [--out <path>]
```

## Flags

| Flag | Type | Default | Description |
|---|---|---|---|
| `--experiments-dir` | path | `experiments/` | Where to walk for experiment subdirs |
| `--out` | path | `findings.md` | Where to write the aggregated index |

## Behavior

1. Walk `<experiments-dir>` for direct subdirectories matching the Experiment ID regex (`data-model.md`). Non-matching dirs are silently ignored (e.g., `.gitkeep`, accidental `tmp/`).

2. For each matching dir:
   a. Extract `experiment_id` from the dir name.
   b. Look for `ANALYSIS.md`. Three states:
      - **Missing** → mark as "pending analysis"
      - **Exists but no summary line found** → mark as "summary missing"
      - **Exists with summary** → extract the summary per R-001 (first non-empty line after `# ` heading, before any other heading)
   c. Build a record: `{id, date, sequence, slug, summary | None, summary_state, hypothesis_path, analysis_path | None}`

3. Sort records by `(date DESC, sequence DESC)` — newest first per R-002.

4. Render `findings.md` per the format in `data-model.md`:
   - Header with metadata (last updated timestamp, total count, completed count, pending count)
   - One section per experiment: `## <date>-<seq> — <slug>`, then quoted summary or italic placeholder, then links to HYPOTHESIS / ANALYSIS

5. Write atomically: write to `<out>.tmp`, then rename. Avoids leaving partial files if interrupted.

6. Print one-line summary: `Wrote findings.md (<N> experiments: <K> completed, <M> pending)`.

## Edge case handling

- **Empty `experiments/`**: produce findings.md with header + `> No experiments yet.` placeholder. Exit 0.
- **`experiments/` doesn't exist**: error message + exit 1 (deviation from "fail closed" but only situation where there's nothing meaningful to do).
- **Malformed dir names** (don't match regex): silently skip.
- **`ANALYSIS.md` is empty file**: treat as "summary missing".
- **`ANALYSIS.md` has no `# ` heading**: treat as "summary missing" (per R-001 spec — position requires the heading).
- **Filesystem permission error reading a dir**: log warning, skip that dir, continue.

## Performance contract

Per SC-005: must complete in <1 sec for 10 experiments on a developer laptop. Implementation should be I/O-bound (sequential reads); no need for parallelism at this scale.

## Tests

- `test_aggregator_emits_completed_summary` — completed experiment → quoted summary in output
- `test_aggregator_marks_missing_analysis_pending` — no ANALYSIS.md → "pending analysis" marker
- `test_aggregator_marks_missing_summary` — ANALYSIS.md exists but no summary → "summary missing" marker
- `test_aggregator_orders_newest_first` — multiple experiments → date DESC, sequence DESC
- `test_aggregator_empty_dir_produces_placeholder` — `experiments/` empty → header + placeholder, no error
- `test_aggregator_skips_malformed_dir_names` — non-conforming dir → silently ignored
- `test_aggregator_atomic_write` — interrupted run doesn't leave partial findings.md (use tmp + rename)
