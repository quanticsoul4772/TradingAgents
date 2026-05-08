"""Spec 001 Phase 4 — per-bot LLM model routing.

Per spec User Story 4 / FR-007: ``config["bot_models"]: dict[str, str]``
maps bot_id → model_name. When set, the framework uses the per-bot model
instead of the framework-wide ``quick_thinking_llm`` / ``deep_thinking_llm``.
Bots without an entry use the role default (quick or deep).

Implementation:
- ``BotLLMFactory`` wraps the existing default LLM clients + the bot_models
  config. Analyst factories ask the factory for their LLM by bot_id; the
  factory returns the per-bot model when configured, default otherwise.
- LLM clients are cached per (provider, model) so we don't instantiate the
  same Anthropic client 4 times for 4 analysts on the same model.

Phase 4 is non-breaking: when ``bot_models`` is empty (default), the
factory transparently returns the framework defaults — behavior identical
to pre-Phase-4 production.
"""

from __future__ import annotations

import logging
from typing import Any

from tradingagents.default_config import TradingAgentsConfig
from tradingagents.llm_clients import create_llm_client

logger = logging.getLogger(__name__)


class BotLLMFactory:
    """Routes LLM lookups to per-bot models when ``config["bot_models"]`` is set.

    Caching: LLM clients keyed by (provider, model) so multiple bots on the
    same model share an instance. The default quick/deep LLMs (already
    constructed by TradingAgentsGraph) are reused as-is.
    """

    def __init__(
        self,
        config: dict | TradingAgentsConfig,
        default_quick_llm: Any,
        default_deep_llm: Any,
    ):
        self.config = config
        self.default_quick = default_quick_llm
        self.default_deep = default_deep_llm
        self._cache: dict[tuple[str, str], Any] = {}

    def get_llm_for_bot(self, bot_id: str, role: str = "quick") -> Any:
        """Return the LLM for this bot.

        - If ``config["bot_models"][bot_id]`` is set, build (or fetch from
          cache) a client for that model using the framework's configured
          provider.
        - Otherwise, return the role default (``default_quick`` for "quick",
          ``default_deep`` for "deep").
        """
        bot_models = self.config.get("bot_models") or {}
        model = bot_models.get(bot_id)
        if model is None:
            if role == "deep":
                return self.default_deep
            return self.default_quick
        return self._get_or_create_client(model)

    def _get_or_create_client(self, model: str) -> Any:
        """Build (or fetch from cache) the unwrapped LangChain LLM for ``model``
        using the framework's configured provider + endpoint.

        Returns the result of ``BaseLLMClient.get_llm()`` (e.g. a
        ``ChatAnthropic`` instance) — NOT the ``BaseLLMClient`` wrapper —
        so callers can invoke LangChain APIs like ``llm.bind_tools(...)``
        directly. ``TradingAgentsGraph`` follows the same convention for
        the default quick/deep LLMs (calls ``.get_llm()`` on the default
        clients before passing them in), so the factory mirrors that.
        """
        provider = self.config.get("llm_provider", "openai")
        key = (provider, model)
        if key not in self._cache:
            kwargs: dict = {}
            backend_url = self.config.get("backend_url")
            if backend_url is not None:
                kwargs["base_url"] = backend_url
            # Provider-specific thinking kwargs (mirrors TradingAgentsGraph._get_provider_kwargs)
            if provider == "google":
                level = self.config.get("google_thinking_level")
                if level:
                    kwargs["thinking_level"] = level
            elif provider == "openai":
                effort = self.config.get("openai_reasoning_effort")
                if effort:
                    kwargs["reasoning_effort"] = effort
            elif provider == "anthropic":
                effort = self.config.get("anthropic_effort")
                if effort:
                    kwargs["effort"] = effort
            self._cache[key] = create_llm_client(provider, model, **kwargs).get_llm()
            logger.info("BotLLMFactory: instantiated %s/%s for per-bot routing", provider, model)
        return self._cache[key]

    def model_for_bot(self, bot_id: str, role: str = "quick") -> str:
        """Return the model NAME this bot would use (for logging / state log)."""
        bot_models = self.config.get("bot_models") or {}
        model = bot_models.get(bot_id)
        if model is not None:
            return model
        if role == "deep":
            return self.config.get("deep_think_llm", "default_deep")
        return self.config.get("quick_think_llm", "default_quick")
