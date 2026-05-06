"""Paper-trading harness errors."""

from __future__ import annotations


class PortfolioStateError(Exception):
    """Raised when portfolio state validation, parsing, or invariant checks fail.

    Carries ``path`` (the offending file or "<in-memory>") and ``failing_invariant``
    (a short string identifying which check failed) so the CLI can render a single
    operator-friendly line instead of a stack trace.
    """

    def __init__(self, message: str, *, path: str = "<in-memory>", failing_invariant: str = ""):
        super().__init__(message)
        self.path = path
        self.failing_invariant = failing_invariant

    def operator_line(self) -> str:
        """One-line message suitable for printing to stderr."""
        bits = [f"[error] {self}"]
        if self.failing_invariant:
            bits.append(f"(invariant: {self.failing_invariant})")
        if self.path and self.path != "<in-memory>":
            bits.append(f"[path: {self.path}]")
        return " ".join(bits)
