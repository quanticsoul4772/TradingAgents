# Contract: ANALYSIS.md format

## Required structure

```markdown
# Analysis: <experiment short name>

<one-line summary — first non-empty line after the H1>

## Result

<what the data showed>

## Decision

<what we're doing because of it>
```

## One-line summary extraction (R-001)

The aggregator extracts the **first non-empty line that follows the top-level `# ` heading and appears before any other heading**.

### Examples

**Example A — clean case**:
```markdown
# Analysis: PM-blind test

When the PM is blind to the bull/bear debate, ratings are unchanged in 18 of 20 cases — the debate adds no information.

## Result

...
```
Extracted summary: `When the PM is blind to the bull/bear debate, ratings are unchanged in 18 of 20 cases — the debate adds no information.`

**Example B — with marker emphasis (still works)**:
```markdown
# Analysis: PM-blind test

**Summary**: When the PM is blind to the bull/bear debate, ratings are unchanged in 18 of 20 cases.

## Result

...
```
Extracted summary: `**Summary**: When the PM is blind to the bull/bear debate, ratings are unchanged in 18 of 20 cases.` (markdown emphasis preserved verbatim).

**Example C — multi-paragraph above sections (still works)**:
```markdown
# Analysis: Order randomization

Analyst order has no measurable effect on PM ratings.

This finding is robust across both the original 5-ticker pilot and a 10-date repeat.

## Detailed findings

...
```
Extracted summary: `Analyst order has no measurable effect on PM ratings.` (just the first line, not the second paragraph).

**Example D — missing summary (handled gracefully)**:
```markdown
# Analysis: Foo

## Result

...
```
Extracted summary: none. Aggregator marks the entry as "summary missing".

**Example E — no H1 heading at all**:
```markdown
Some random text.

## Result

...
```
Extracted summary: none (per R-001, position requires the H1 to exist). Aggregator marks as "summary missing".

## Optional sections

These do not affect summary extraction:

- `## Detailed findings` — quantitative tables, plots references, deeper analysis
- `## Limitations` — caveats, sample size concerns, regime dependence
- `## Next experiment` — what to try next based on this result

## Anti-patterns

- **HTML comment markers** (`<!-- SUMMARY: ... -->`) — not extracted by the aggregator. Useful for the writer's own notes; ignored by tooling.
- **Frontmatter `summary:` field** — not extracted. The position rule is the contract.
- **Putting the summary inside the `## Result` section** — not extracted. The summary must precede the first second-level heading.

## Why this format

Per R-001 in `research.md`: position-based extraction requires no extra ceremony, fails gracefully, and matches what a reader would scan for anyway.
