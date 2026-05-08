from typing import Any, cast

import tradingagents.default_config as default_config
from tradingagents.default_config import TradingAgentsConfig

# Use default config but allow it to be overridden
_config: TradingAgentsConfig | None = None


def initialize_config() -> None:
    """Initialize the configuration with default values."""
    global _config
    if _config is None:
        _config = cast(TradingAgentsConfig, default_config.DEFAULT_CONFIG.copy())


def set_config(config: dict[str, Any] | TradingAgentsConfig) -> None:
    """Update the configuration with custom values.

    Accepts an untyped partial dict so callers can pass small overrides
    (e.g. ``{"llm_provider": "anthropic"}``) without having to construct
    a full ``TradingAgentsConfig``.
    """
    global _config
    if _config is None:
        _config = cast(TradingAgentsConfig, default_config.DEFAULT_CONFIG.copy())
    _config.update(config)  # type: ignore[typeddict-item]


def get_config() -> TradingAgentsConfig:
    """Get the current configuration."""
    if _config is None:
        initialize_config()
    assert _config is not None  # for mypy after initialize_config
    return cast(TradingAgentsConfig, _config.copy())


# Initialize with default config
initialize_config()
