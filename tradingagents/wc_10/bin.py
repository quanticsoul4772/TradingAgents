"""WC-10 bin function: continuous scalar rating → 5-tier categorical.

Pure function with deterministic mapping. Default thresholds produce
equal-width bins per spec.md.
"""

from __future__ import annotations

DEFAULT_BIN_THRESHOLDS: tuple[float, float, float, float] = (-0.6, -0.2, 0.2, 0.6)


def _validate_thresholds(thresholds: tuple[float, float, float, float]) -> None:
    """Raise ValueError if thresholds are invalid (per FR-008)."""
    if len(thresholds) != 4:
        raise ValueError(f"thresholds must be a 4-tuple; got {len(thresholds)} elements")
    for t in thresholds:
        if not (-1.0 <= t <= 1.0):
            raise ValueError(f"threshold {t} out of [-1, +1]")
    for i in range(len(thresholds) - 1):
        if thresholds[i] >= thresholds[i + 1]:
            raise ValueError(
                f"thresholds must be strictly monotonic increasing; "
                f"got {thresholds[i]} >= {thresholds[i + 1]} at index {i}"
            )


def bin_scalar_to_tier(
    rating: float,
    thresholds: tuple[float, float, float, float] | None = None,
) -> str:
    """Bin a continuous scalar rating to 5-tier categorical.

    Args:
        rating: float in [-1.0, +1.0]
        thresholds: 4-tuple of strictly-monotonic floats in [-1, +1].
            Defaults to DEFAULT_BIN_THRESHOLDS = (-0.6, -0.2, 0.2, 0.6).

    Returns:
        One of {"Buy", "Overweight", "Hold", "Underweight", "Sell"}.

    Raises:
        ValueError: if thresholds are not strictly monotonic OR out of
            [-1, +1], OR if rating is out of [-1, +1].

    Boundary semantics: ``<=`` (right-inclusive at the bin's upper boundary).
    Lower bin claims the boundary value (e.g., rating == -0.6 → "Sell",
    not "Underweight").
    """
    if thresholds is None:
        thresholds = DEFAULT_BIN_THRESHOLDS

    _validate_thresholds(thresholds)

    if not (-1.0 <= rating <= 1.0):
        raise ValueError(f"rating {rating} out of [-1, +1]")

    sell_t, uw_t, hold_t, ow_t = thresholds

    if rating <= sell_t:
        return "Sell"
    if rating <= uw_t:
        return "Underweight"
    if rating <= hold_t:
        return "Hold"
    if rating <= ow_t:
        return "Overweight"
    return "Buy"
