"""WC-10 Continuous Scalar Rating package.

Tier 2 experiment to test the categorical-bottleneck hypothesis. Replaces
the framework's 5-tier categorical PortfolioRating enum with a continuous
scalar in [-1, +1] (signed conviction magnitude). Default-OFF.

See specs/108-wc-10-continuous-scalar-rating/ for the full design bundle.
"""

from tradingagents.wc_10.bin import DEFAULT_BIN_THRESHOLDS, bin_scalar_to_tier

__all__ = ["DEFAULT_BIN_THRESHOLDS", "bin_scalar_to_tier"]
