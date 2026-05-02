"""Experiment ID generation, parsing, and validation.

Format: <YYYY-MM-DD>-<NNN>-<short-name>, e.g. 2026-05-02-001-mr1-contradiction.
Validated by ID_REGEX. Sequence number auto-increments within a date by
scanning the experiments/ directory for prior IDs sharing the same date.

See specs/001-experiments-scaffolding/data-model.md for the canonical spec.
"""

from __future__ import annotations

import re
from datetime import date as _date
from datetime import datetime, timezone
from pathlib import Path

# Anchored regex per data-model.md.
ID_REGEX = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})-(\d{3})-([a-z0-9][a-z0-9-]{0,38}[a-z0-9])$"
)
SLUG_REGEX = re.compile(r"^[a-z0-9][a-z0-9-]{0,38}[a-z0-9]$")


def validate_id(id_str: str) -> bool:
    """Return True if id_str matches the canonical Experiment ID format."""
    return ID_REGEX.match(id_str) is not None


def validate_slug(slug: str) -> bool:
    """Return True if slug is a valid kebab-case short-name (1-40 chars, no edge hyphens)."""
    return SLUG_REGEX.match(slug) is not None


def parse_id(id_str: str) -> tuple[_date, int, str]:
    """Decompose a valid Experiment ID into (date, sequence_int, slug)."""
    m = ID_REGEX.match(id_str)
    if not m:
        raise ValueError(f"Not a valid experiment ID: {id_str!r}")
    yyyy, mm, dd, nnn, slug = m.groups()
    return _date(int(yyyy), int(mm), int(dd)), int(nnn), slug


def _today_utc() -> _date:
    return datetime.now(timezone.utc).date()


def next_experiment_id(experiments_dir: Path, slug: str, date: _date | None = None) -> str:
    """Compose the next free Experiment ID for `date` and `slug`.

    Scans `experiments_dir` for prior IDs sharing the same date prefix and
    returns `<date>-<NNN>-<slug>` where NNN is `max_existing + 1`, zero-padded
    to 3 digits. Returns NNN=001 when no prior IDs share the date.

    Raises ValueError if `slug` is invalid.
    """
    if not validate_slug(slug):
        raise ValueError(
            f"Invalid slug {slug!r}: must match {SLUG_REGEX.pattern} "
            "(2-40 chars, kebab-case, no leading/trailing hyphens)."
        )
    if date is None:
        date = _today_utc()
    date_prefix = date.strftime("%Y-%m-%d")

    max_seq = 0
    if experiments_dir.exists():
        for entry in experiments_dir.iterdir():
            if not entry.is_dir():
                continue
            m = ID_REGEX.match(entry.name)
            if not m:
                continue
            existing_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            if existing_date != date_prefix:
                continue
            seq = int(m.group(4))
            if seq > max_seq:
                max_seq = seq

    next_seq = max_seq + 1
    if next_seq > 999:
        raise RuntimeError(
            f"Sequence overflow for date {date_prefix}: max NNN is 999"
        )
    return f"{date_prefix}-{next_seq:03d}-{slug}"
