# Constitution v1.5.2 cross-reference audit — 2026-05-09

**Trigger**: reasoning_decision rank-6 (0.66 score). Verifies all docs reflect v1.5.2 (current) without stale v1.5.1 / v1.5.0 references that should have been updated.

**Cost**: $0. ~10 min wall-clock.

## Audit methodology

Grepped repo for `v1.5.0` + `v1.5.1` references, classified each:
- **CURRENT (v1.5.2)**: top-of-file pointer; should be v1.5.2
- **PRIOR-VERSION (narrative)**: documents v1.5.1 / v1.5.0 as historical predecessors; correctly preserves chain
- **EMPIRICAL-CONTEXT (load-bearing)**: cites v1.5.0 carve-out scope or v1.5.1 magnitude bound in body text; correct because it describes what THAT amendment codified
- **HISTORICAL PR / day-arc dated docs**: claudedocs entries dated by their write-time; preserve as-is

## Findings — NO STALE REFERENCES; FLOOR HOLDS

### `.specify/memory/constitution.md` (load-bearing)

- Line 5: `**Version**: 1.5.2` ✅ CURRENT
- Line 7: `**Last amended**: 2026-05-09 — added "Analyst-order scope" paragraph ... v1.5.1 → v1.5.2 (PATCH per scope-narrowing rule).` ✅ CURRENT
- Line 8: `**Prior version**: 1.5.1 — added "Bear-regime validation" paragraph ...` ✅ correct narrative chain
- Line 9: `**Prior version**: 1.5.0 — added "Schema-induced abstention is NOT calibrated abstention" sub-section ...` ✅ correct narrative chain
- Lines 162, 164: in-document body references to "v1.5.0" framing in the Bear-regime validation paragraph ✅ correct — these describe what the v1.5.0 carve-out codified (load-bearing context)

### `.specify/templates/spec-template-conditional.md` (template provenance)

- Lines 12, 191: references to "Constitution v1.5.1 patches" as pattern source (PR #144) ✅ correct historical provenance — v1.5.1 patches were the precedent for the conditional-patch pattern. v1.5.2 was a single-version amendment (not pre-scaffolded as conditional patches), so updating to "v1.5.1/v1.5.2 patches" would be inaccurate.

### `CLAUDE.md` (top-of-file load-bearing)

- Line 13 (headline finding paragraph): references to "WC-10 research arc" + "v1.5.0/v1.5.1/v1.5.2" amendment history ✅ CURRENT
- Line 17 (Principle VII evolution narrative): cites all three amendments (v1.5.0 / v1.5.1 / v1.5.2) with correct attribution ✅ CURRENT
- Line 23 (Constitution version pointer): `**Current version: v1.5.2**` + full amendment history chain ✅ CURRENT

### `CHANGELOG.md` (historical entries)

- 2026-05-09 section: extensive v1.5.x references in CONTEXT (e.g., "Constitution v1.5.1 → v1.5.2 PATCH"; "(1) genuine ambiguity (Constitution VII original); (2) schema-induced collapse (v1.5.0); (3) analyst-order-biased pooling (v1.5.2)") ✅ correct narrative
- 2026-05-08 section: "v1.4.6 → v1.5.0" amendment record ✅ correct historical entry (preserve)
- All other historical entries correctly cite their date-of-write Constitution version

### `RESEARCH_FINDINGS.md`

- WC-10 v1 pilot section: `Constitution amendment (PR #131, v1.4.3 → v1.5.0)` ✅ correct historical attribution
- WC-11 + WC-10 v2 sections: cite v1.5.2 amendment correctly
- Filter portfolio header: cites v1.5.x references in mechanism class context ✅ CURRENT

### `claudedocs/` historical entries (dated docs)

- `constitution-v1.5.1-conditional-patch-drafts-2026-05-08.md` ✅ HISTORICAL pre-scaffolded patches (correctly preserved)
- `class4-macro-filter-retrospective-2026-05-09.md` ✅ today's retrospective; correct
- `spec-012-class-4-deployment-retrospective-2026-05-09.md` ✅ correct
- `research-burst-2026-05-09.md` (PR #206) ✅ correct
- All other dated claudedocs preserve their date-of-write context

## Verdict — CLEAN PASS

**Zero stale references found.** Cross-reference structure is sound:
- v1.5.2 correctly cited as CURRENT version (header + headline + amendment-pointer locations)
- v1.5.1 + v1.5.0 correctly cited as PRIOR versions in narrative chain
- v1.5.0 carve-out scope referenced correctly in body text (load-bearing context)
- Template provenance references to v1.5.1 patches correctly historical

No edits required. The 2026-05-09 amendment landed cleanly across all load-bearing docs (CLAUDE.md preamble + headline; constitution.md header + amendment narrative; README via PR #187; CHANGELOG via PR #187; RESEARCH_FINDINGS via PR #182 + #196; ROADMAP via PR #183 + #196).

## Audit history (cumulative cleanup discipline)

| Pass | PR | Pre-scope | Post-scope | Edits |
|---|---|---|---|---:|
| Round-1 post-v1.5.1 | #142 | v1.5.0 carve-out | v1.5.1 added | 2 |
| Round-1 post-v1.5.2 + WC-10 closure | #188 | v1.5.1 | v1.5.2 + WC-10 closed | 3 |
| Round-2 post-29-PR-scale | #208 | day-arc 14-PR snapshot | day-arc 29-PR scope | 1 |
| **v1.5.2 xref audit (this PR)** | **#210** | **v1.5.2 amendment landed** | **all load-bearing docs current** | **0 (clean PASS)** |

The cleanup-pass cadence demonstrates the methodology works: surgical edits at amendment-time, audit verification at end-of-arc.

## Cost

$0 LLM. ~10 min wall-clock.

## What ships

`claudedocs/constitution-v1.5.2-xref-audit-2026-05-09.md` (audit memo only; no code or doc changes).

## Cross-references

- PR #142 (round-1 cleanup post-v1.5.1)
- PR #188 (round-1 cleanup post-v1.5.2 + WC-10 closure)
- PR #208 (round-2 cleanup post-29-PR scale)
- Constitution v1.5.2 (current; landed via PR #179)
