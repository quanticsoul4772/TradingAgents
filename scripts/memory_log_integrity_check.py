"""Memory log integrity check — flag reflection-prose hallucinations.

Per `claudedocs/amd-memory-log-audit-hallucination-resolution-2026-05-07-late.md`
(PR #54): the TradingMemoryLog auto-generates a REFLECTION paragraph
after each pending entry resolves. The LLM that writes the reflection
sees the realized return data but can produce prose that CONTRADICTS
the data — narrating a "successful trim" while the entry header records
a +24.9% raw return showing the trim FAILED.

This script walks any memory log file (default:
`experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/backtest_memory.md`)
and flags entries where:

1. The entry header records a CLOSED window (rating + raw_return + alpha
   + holding_days are populated, not "pending"); AND
2. The rating direction CONTRADICTS the realized return sign.

Bear-direction ratings (Underweight, Sell) expect raw_return < 0.
Bull-direction ratings (Overweight, Buy) expect raw_return > 0.
Hold has no expected direction and is excluded.

When BOTH conditions hold, the reflection is SUSPECT — operators should
read the reflection prose and verify it acknowledges the data or
identify it as hallucinated.

Usage:
    python scripts/memory_log_integrity_check.py
    python scripts/memory_log_integrity_check.py --file <path>
    python scripts/memory_log_integrity_check.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Header regex: [DATE | TICKER | RATING | RAW_RETURN | ALPHA | HOLDING_DAYS]
# Rating tier from the 5-tier scale (CLAUDE.md). Pending entries have
# different shape and are excluded.
HEADER_RE = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2})\s*\|\s*"
    r"([A-Z][A-Z0-9.\-]*)\s*\|\s*"
    r"(Buy|Overweight|Hold|Underweight|Sell)\s*\|\s*"
    r"([+\-]?\d+\.?\d*)%\s*\|\s*"
    r"([+\-]?\d+\.?\d*)%\s*\|\s*"
    r"(\d+)d\]$"
)

BULLISH_RATINGS = {"Buy", "Overweight"}
BEARISH_RATINGS = {"Underweight", "Sell"}

DEFAULT_MEMORY_FILE = Path(
    "experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/backtest_memory.md"
)


def parse_entries(memory_md: str) -> list[dict]:
    """Walk a memory log and return one dict per RESOLVED (non-pending) entry.

    Each dict has:
      - line_number (1-indexed)
      - date, ticker, rating, raw_return_pct, alpha_pct, holding_days
      - reflection_excerpt (first 600 chars after REFLECTION marker until
        ENTRY_END comment, or empty if not found)
    """
    entries = []
    lines = memory_md.split("\n")
    for i, line in enumerate(lines):
        m = HEADER_RE.match(line.strip())
        if m is None:
            continue
        date, ticker, rating, raw_str, alpha_str, days_str = m.groups()
        # Find reflection block: search forward for "REFLECTION:" marker
        # then capture text until "<!-- ENTRY_END -->" or next header.
        reflection_lines: list[str] = []
        in_reflection = False
        for j in range(i + 1, min(i + 200, len(lines))):
            ln = lines[j]
            if ln.strip() == "REFLECTION:":
                in_reflection = True
                continue
            if "<!-- ENTRY_END -->" in ln or HEADER_RE.match(ln.strip()):
                break
            if in_reflection:
                reflection_lines.append(ln)
        reflection = "\n".join(reflection_lines).strip()
        entries.append(
            {
                "line_number": i + 1,
                "date": date,
                "ticker": ticker,
                "rating": rating,
                "raw_return_pct": float(raw_str),
                "alpha_pct": float(alpha_str),
                "holding_days": int(days_str),
                "reflection_excerpt": reflection[:600],
                "has_reflection": bool(reflection),
            }
        )
    return entries


def flag_inconsistencies(entries: list[dict]) -> list[dict]:
    """Return entries where rating direction contradicts realized return sign.

    Suspect criteria:
      - Bullish rating + raw_return < 0  → trade went down despite Buy/OW
      - Bearish rating + raw_return > 0  → trade went up despite UW/Sell

    Hold ratings are excluded (no directional expectation).
    """
    suspects = []
    for e in entries:
        rating = e["rating"]
        raw = e["raw_return_pct"]
        suspect_reason = None
        if rating in BULLISH_RATINGS and raw < 0:
            suspect_reason = f"Bullish rating ({rating}) but raw_return = {raw:+.2f}% (DOWN)"
        elif rating in BEARISH_RATINGS and raw > 0:
            suspect_reason = f"Bearish rating ({rating}) but raw_return = {raw:+.2f}% (UP)"
        if suspect_reason is None:
            continue
        flagged = dict(e)
        flagged["suspect_reason"] = suspect_reason
        # Heuristic check: does the reflection contain self-validating phrases
        # despite the data refuting them?
        ref_lc = e["reflection_excerpt"].lower()
        validation_phrases = [
            "captured the inflection",
            "validated the trim",
            "validated the underweight",
            "validated the overweight",
            "directional call was correct",
            "trim discipline",
            "thesis confirmed",
            "thesis was correct",
            "proved predictive",
            "captured precisely",
        ]
        flagged["matched_validation_phrases"] = [p for p in validation_phrases if p in ref_lc]
        suspects.append(flagged)
    return suspects


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_MEMORY_FILE,
        help="Memory log file to scan (default: SC-009 backtest_memory.md)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output.",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"ERROR: {args.file} does not exist", file=sys.stderr)
        return 2

    text = args.file.read_text(encoding="utf-8")
    entries = parse_entries(text)
    suspects = flag_inconsistencies(entries)

    result = {
        "file": str(args.file),
        "total_resolved_entries": len(entries),
        "suspect_entries": len(suspects),
        "suspects": suspects,
    }

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return 1 if suspects else 0

    print("# Memory log integrity check")
    print()
    print(f"File: {args.file}")
    print(f"Resolved entries scanned: {len(entries)}")
    print(f"Suspect entries (rating direction vs return sign mismatch): {len(suspects)}")
    print()

    if not suspects:
        print("## ✓ No suspect entries")
        print()
        print("All resolved bullish ratings have raw_return >= 0;")
        print("all resolved bearish ratings have raw_return <= 0.")
        print("Reflection prose can still hallucinate on Hold ratings or on")
        print("entries where the magnitude (not sign) is the concern, but the")
        print("standard sign-mismatch heuristic finds nothing.")
        return 0

    print("## ⚠ Suspect entries")
    print()
    for s in suspects:
        print(f"### {s['ticker']} @ {s['date']} (line {s['line_number']})")
        print(f"  Rating: {s['rating']}")
        print(
            f"  Raw return: {s['raw_return_pct']:+.2f}% | "
            f"Alpha: {s['alpha_pct']:+.2f}% | "
            f"Holding: {s['holding_days']}d"
        )
        print(f"  Suspect reason: {s['suspect_reason']}")
        if s["matched_validation_phrases"]:
            print(
                f"  ⚠ Reflection contains {len(s['matched_validation_phrases'])} self-validating phrase(s):"
            )
            for p in s["matched_validation_phrases"]:
                print(f'    - "{p}"')
            print(
                "  → REFLECTION HALLUCINATION SUSPECTED. Read entry's "
                "REFLECTION paragraph and verify against the realized "
                "return data."
            )
        else:
            print(
                "  Reflection does NOT contain standard self-validating "
                "phrases — may be data-acknowledging rather than "
                "hallucinated. Read for confirmation."
            )
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
