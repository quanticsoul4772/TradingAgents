"""Tests for scripts/findings_aggregate.py.

Per specs/001-experiments-scaffolding/contracts/findings_aggregate_cli.md
and contracts/analysis_md_format.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from findings_aggregate import (  # noqa: E402
    _atomic_write,
    _extract_summary,
    _render_findings,
    _scan_experiment,
    _walk_experiments,
)

pytestmark = pytest.mark.unit


# ---- _extract_summary -------------------------------------------------


def test_extract_summary_clean_case():
    md = """\
# Analysis: foo

Summary line goes here.

## Result

details
"""
    assert _extract_summary(md) == "Summary line goes here."


def test_extract_summary_with_emphasis_marker():
    md = """\
# Analysis: foo

**Summary**: When PM is blind, ratings unchanged 18 of 20 cases.

## Result
"""
    assert (
        _extract_summary(md) == "**Summary**: When PM is blind, ratings unchanged 18 of 20 cases."
    )


def test_extract_summary_multi_paragraph_takes_first():
    md = """\
# Analysis: foo

First paragraph is the summary.

Second paragraph is more detail.

## Result
"""
    assert _extract_summary(md) == "First paragraph is the summary."


def test_extract_summary_returns_none_when_no_h1():
    md = """\
Some random text.

## Result

stuff
"""
    assert _extract_summary(md) is None


def test_extract_summary_returns_none_when_only_headings():
    md = """\
# Analysis: foo

## Result

stuff
"""
    assert _extract_summary(md) is None


def test_extract_summary_empty_string():
    assert _extract_summary("") is None


def test_extract_summary_h2_only_skipped_as_h1():
    # `## ` is H2, doesn't count as H1.
    md = """\
## Analysis: foo

This is text but no H1 was found.
"""
    assert _extract_summary(md) is None


# ---- _scan_experiment / record state ----------------------------------


def test_scan_completed_experiment(tmp_path):
    exp_dir = tmp_path / "2026-05-02-001-foo"
    exp_dir.mkdir()
    (exp_dir / "ANALYSIS.md").write_text(
        "# Analysis: foo\n\nGreat finding.\n\n## Result\n",
        encoding="utf-8",
    )
    record = _scan_experiment(exp_dir)
    assert record.state == "completed"
    assert record.summary == "Great finding."
    assert record.id == "2026-05-02-001-foo"
    assert record.has_analysis is True


def test_scan_pending_analysis_when_no_md(tmp_path):
    exp_dir = tmp_path / "2026-05-02-001-foo"
    exp_dir.mkdir()
    record = _scan_experiment(exp_dir)
    assert record.state == "pending analysis"
    assert record.summary is None
    assert record.has_analysis is False


def test_scan_summary_missing_when_md_lacks_summary(tmp_path):
    exp_dir = tmp_path / "2026-05-02-001-foo"
    exp_dir.mkdir()
    (exp_dir / "ANALYSIS.md").write_text(
        "# Analysis: foo\n\n## Result\n\nstuff\n",
        encoding="utf-8",
    )
    record = _scan_experiment(exp_dir)
    assert record.state == "summary missing"
    assert record.summary is None
    assert record.has_analysis is True


# ---- _walk_experiments ------------------------------------------------


def test_walk_orders_newest_first(tmp_path):
    for name in [
        "2026-05-01-001-old",
        "2026-05-02-002-newer",
        "2026-05-02-001-newer-but-earlier-seq",
    ]:
        d = tmp_path / name
        d.mkdir()
    records = _walk_experiments(tmp_path)
    ids = [r.id for r in records]
    assert ids == [
        "2026-05-02-002-newer",
        "2026-05-02-001-newer-but-earlier-seq",
        "2026-05-01-001-old",
    ]


def test_walk_empty_dir_returns_empty_list(tmp_path):
    records = _walk_experiments(tmp_path)
    assert records == []


def test_walk_skips_malformed_dir_names(tmp_path):
    (tmp_path / "not-an-experiment").mkdir()
    (tmp_path / "2026-05-02-foo").mkdir()  # missing sequence
    (tmp_path / "tmp").mkdir()
    (tmp_path / "2026-05-02-001-real").mkdir()
    records = _walk_experiments(tmp_path)
    assert [r.id for r in records] == ["2026-05-02-001-real"]


def test_walk_skips_files(tmp_path):
    (tmp_path / "2026-05-02-001-foo").write_text("not a dir")
    (tmp_path / "2026-05-02-002-bar").mkdir()
    records = _walk_experiments(tmp_path)
    assert [r.id for r in records] == ["2026-05-02-002-bar"]


def test_walk_raises_when_dir_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        _walk_experiments(tmp_path / "nonexistent")


# ---- _render_findings -------------------------------------------------


def test_render_empty_produces_placeholder():
    out = _render_findings([])
    assert "# Findings" in out
    assert "No experiments yet." in out
    assert "Total experiments: 0" in out


def test_render_completed_quotes_summary(tmp_path):
    exp_dir = tmp_path / "2026-05-02-001-foo"
    exp_dir.mkdir()
    (exp_dir / "ANALYSIS.md").write_text(
        "# Analysis: foo\n\nThe finding.\n",
        encoding="utf-8",
    )
    records = _walk_experiments(tmp_path)
    out = _render_findings(records)
    assert "## 2026-05-02-001 — foo" in out
    assert "> The finding." in out


def test_render_pending_marker(tmp_path):
    (tmp_path / "2026-05-02-001-foo").mkdir()
    records = _walk_experiments(tmp_path)
    out = _render_findings(records)
    assert "*pending analysis*" in out


def test_render_summary_missing_marker(tmp_path):
    exp_dir = tmp_path / "2026-05-02-001-foo"
    exp_dir.mkdir()
    (exp_dir / "ANALYSIS.md").write_text("# Analysis: foo\n\n## Result\n", encoding="utf-8")
    records = _walk_experiments(tmp_path)
    out = _render_findings(records)
    assert "summary missing" in out


def test_render_includes_links(tmp_path):
    exp_dir = tmp_path / "2026-05-02-001-foo"
    exp_dir.mkdir()
    (exp_dir / "ANALYSIS.md").write_text(
        "# Analysis: foo\n\nSummary.\n",
        encoding="utf-8",
    )
    records = _walk_experiments(tmp_path)
    out = _render_findings(records)
    assert "experiments/2026-05-02-001-foo/HYPOTHESIS.md" in out
    assert "experiments/2026-05-02-001-foo/ANALYSIS.md" in out


def test_render_no_analysis_link_when_missing(tmp_path):
    (tmp_path / "2026-05-02-001-foo").mkdir()
    records = _walk_experiments(tmp_path)
    out = _render_findings(records)
    assert "experiments/2026-05-02-001-foo/HYPOTHESIS.md" in out
    assert "experiments/2026-05-02-001-foo/ANALYSIS.md" not in out


# ---- _atomic_write ----------------------------------------------------


def test_atomic_write_creates_file(tmp_path):
    path = tmp_path / "out.md"
    _atomic_write(path, "hello")
    assert path.read_text(encoding="utf-8") == "hello"


def test_atomic_write_replaces_existing(tmp_path):
    path = tmp_path / "out.md"
    path.write_text("old content", encoding="utf-8")
    _atomic_write(path, "new content")
    assert path.read_text(encoding="utf-8") == "new content"


def test_atomic_write_uses_tmp_suffix_then_renames(tmp_path):
    """The .tmp file should not exist after the write completes."""
    path = tmp_path / "out.md"
    _atomic_write(path, "data")
    tmp_file = path.with_suffix(path.suffix + ".tmp")
    assert not tmp_file.exists()
    assert path.exists()


def test_atomic_write_creates_parent_dir(tmp_path):
    path = tmp_path / "deep" / "nested" / "out.md"
    _atomic_write(path, "data")
    assert path.exists()
